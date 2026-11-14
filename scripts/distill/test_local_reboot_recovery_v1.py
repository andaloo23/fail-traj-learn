"""CPU-only recovery checks; no model weights, teacher calls or GPU benchmarks."""
from contextlib import ExitStack, nullcontext
import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

import torch

import local_full_recipe_queue as queue
import qwen_recipe_runner as runner
import qwen_binary_resume_v1 as resume
import recover_local_full_queue_v1 as recovery
import score_recipe_suite as scoring


class Input:
    def __init__(self, value):
        self.tensor = torch.tensor([[float(value), .5]])
        self.shape = self.tensor.shape

    def to(self, device):
        return self.tensor


class Processor:
    def save_pretrained(self, path):
        Path(path).mkdir(parents=True, exist_ok=True)


class Model(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.linear = torch.nn.Linear(2, 3)
        self.dropout = torch.nn.Dropout(.25)

    def forward(self, x):
        return self.dropout(self.linear(x)).tanh()

    def save_pretrained(self, path):
        Path(path).mkdir(parents=True, exist_ok=True)
        torch.save(self.state_dict(), Path(path) / 'model.pt')


def load_model(cfg, trainable=True, adapter=None):
    model = Model()
    if adapter:
        model.load_state_dict(torch.load(Path(adapter) / 'model.pt', weights_only=True))
    return model


class BinaryResumeTests(unittest.TestCase):
    def fixture(self, root):
        folder = root / 'evidence'; folder.mkdir()
        for path in (root / 'study.json', folder / 'records.jsonl', folder / 'adapter.json'):
            path.write_text('{}')
        rows = [dict(id=f'{i}_binary', episode=str(i), split='train', task='binary', has_failure=bool(i % 2), value=i + 1) for i in range(6)]
        study = dict(config=dict(student=dict(seed=42, gradient_accumulation=2, learning_rate=.01, max_length=64),
                                 checkpoint_every_updates=2, save_optimizer_state=True))
        return folder, rows, study

    def harness(self, stack, root, rows, study):
        stack.enter_context(patch.object(runner, 'load', return_value=(study, root, rows)))
        stack.enter_context(patch.object(runner.core, 'processor_for', return_value=Processor()))
        stack.enter_context(patch.object(runner.core, 'load_model', side_effect=load_model))
        stack.enter_context(patch.object(runner.core, 'encode_train', side_effect=lambda p, s, r, n: {'input_ids': Input(r['value'])}))
        stack.enter_context(patch.object(runner.core, 'sft_loss', side_effect=lambda m, b: ((m(b['input_ids']) ** 2).sum() * (.8 + random.random()), 3)))
        stack.enter_context(patch.object(runner.importlib.metadata, 'version', return_value='cpu-test'))
        stack.enter_context(patch.object(torch, 'autocast', side_effect=lambda *a, **kw: nullcontext()))
        for name in ('manual_seed_all', 'reset_peak_memory_stats', 'synchronize', 'set_rng_state_all'):
            stack.enter_context(patch.object(torch.cuda, name))
        stack.enter_context(patch.object(torch.cuda, 'max_memory_allocated', return_value=0))
        stack.enter_context(patch.object(torch.cuda, 'get_rng_state_all', side_effect=lambda: [torch.get_rng_state()]))

    def test_resumed_updates_match_uninterrupted_frozen_trainer(self):
        with tempfile.TemporaryDirectory() as d, ExitStack() as stack:
            root = Path(d); folder, rows, study = self.fixture(root)
            self.harness(stack, root, rows, study)
            complete = root / 'uninterrupted'
            runner.train(folder, 'binary', complete, updates=6, max_hours=1)
            interrupted = root / 'interrupted'
            calls = 0

            def encode(p, s, row, n):
                nonlocal calls
                calls += 1
                if calls == 5:
                    raise InterruptedError('simulated reboot after checkpoint 2')
                return {'input_ids': Input(row['value'])}

            with patch.object(runner.core, 'encode_train', side_effect=encode):
                with self.assertRaises(InterruptedError):
                    runner.train(folder, 'binary', interrupted, updates=6, max_hours=1)
            old_hash = queue.frozen.digest(interrupted / 'training_state.pt')
            resumed = root / 'resumed'
            result = resume.train(folder, interrupted, resumed, updates=6, max_hours=1)
            self.assertTrue(result['completed_schedule'])
            self.assertEqual(queue.frozen.digest(interrupted / 'training_state.pt'), old_hash)
            expected = torch.load(complete / 'adapter_step_6/model.pt', weights_only=True)
            actual = torch.load(resumed / 'adapter_step_6/model.pt', weights_only=True)
            for name in expected:
                self.assertTrue(torch.equal(expected[name], actual[name]), name)
            a = torch.load(complete / 'training_state.pt', weights_only=False)
            b = torch.load(resumed / 'training_state.pt', weights_only=False)
            for index in a['optimizer']['state']:
                for key, value in a['optimizer']['state'][index].items():
                    self.assertTrue(torch.equal(value, b['optimizer']['state'][index][key]))
            self.assertEqual((a['seen'], a['total_tokens'], a['examples']), (b['seen'], b['total_tokens'], b['examples']))
            self.assertEqual(a['python_rng'], b['python_rng'])
            self.assertTrue(torch.equal(a['torch_rng'], b['torch_rng']))
            full_log = [json.loads(x) for x in (complete / 'train.jsonl').read_text().splitlines()][2:]
            resumed_log = [json.loads(x) for x in (resumed / 'train.jsonl').read_text().splitlines()]
            self.assertEqual([(x['step'], x['loss']) for x in full_log], [(x['step'], x['loss']) for x in resumed_log])

    def test_checkpoint_rejects_changed_records(self):
        with tempfile.TemporaryDirectory() as d, ExitStack() as stack:
            root = Path(d); folder, rows, study = self.fixture(root)
            self.harness(stack, root, rows, study)
            out = root / 'original'
            with patch.object(runner.core, 'sft_loss', side_effect=RuntimeError('stop')):
                with self.assertRaises(RuntimeError):
                    runner.train(folder, 'binary', out, updates=6, max_hours=1)
            (folder / 'records.jsonl').write_text('changed')
            with self.assertRaisesRegex(ValueError, 'differs'):
                resume.inspect_checkpoint(folder, out, 6, 1)

    def test_optimizer_parameter_mismatch_is_rejected(self):
        model = Model()
        optimizer = torch.optim.AdamW(model.parameters())
        saved = {'optimizer': {'param_groups': [{'params': [0]}], 'state': {}}}
        with self.assertRaisesRegex(ValueError, 'parameter count'):
            resume.restore_training_state(model, optimizer, saved)

    def test_checkpoint_rejects_exhausted_original_time_budget(self):
        with tempfile.TemporaryDirectory() as d, ExitStack() as stack:
            root = Path(d); folder, rows, study = self.fixture(root)
            self.harness(stack, root, rows, study)
            original = root / 'original'
            runner.train(folder, 'binary', original, updates=6, max_hours=1)
            # Recreate an interrupted history with a valid earlier checkpoint.
            (original / 'completion.json').unlink()
            saved = torch.load(original / 'training_state.pt', weights_only=False)
            saved.update(step=2, adapter=str((original / 'adapter_step_2').resolve()), examples=4)
            for value in saved['optimizer']['state'].values():
                value['step'] = torch.tensor(2.)
            torch.save(saved, original / 'training_state.pt')
            (original / 'train.jsonl').write_text(json.dumps({'step': 3, 'elapsed_seconds': 3601}) + '\n')
            with self.assertRaisesRegex(ValueError, 'exhausted'):
                resume.inspect_checkpoint(folder, original, 6, 1)

    def test_partial_log_tail_uses_last_durable_update(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'log'
            path.write_text('{"step":1500,"elapsed_seconds":20}\n{"step":1501')
            self.assertEqual(resume.last_entry(path)['step'], 1500)


class ControllerTests(unittest.TestCase):
    def test_duplicate_launch_is_rejected_before_touching_queue(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); repair = root / 'repair'; repair.mkdir()
            (repair / 'launch.json').write_text('{}')
            lock = root / 'lock'
            with patch.object(recovery, 'approved', return_value=({}, root, {})), patch.object(recovery, 'RECOVERY', repair), patch.object(recovery, 'Path', side_effect=lambda p: lock if str(p).endswith('ftl-local-recipe-gpu.lock') else Path(p)):
                with self.assertRaisesRegex(ValueError, 'already attempted'):
                    recovery.run()

    def test_completed_baseline_skipped_and_future_arms_remain_sequential(self):
        with tempfile.TemporaryDirectory() as d, ExitStack() as stack:
            root = Path(d)
            state = dict(status='running', arms={'base': {'status': 'completed'}, 'binary': {'status': 'recovering'}})
            plan = dict(recipes=['base', 'binary', 'joint'])
            repair = root / 'recovery'; queue.save(repair / 'plan.json', {'checkpoint_step': 1500})
            events = []

            def phase(recipe, name, state):
                events.append((recipe, name))
                if name == 'train':
                    queue.save(root / 'runs' / recipe / 'completion.json', {'completed_schedule': True})
                else:
                    queue.save(root / 'predictions' / recipe / 'completion.json', {'complete': True})

            stack.enter_context(patch.object(recovery, 'ROOT', root))
            stack.enter_context(patch.object(recovery, 'RECOVERY', repair))
            stack.enter_context(patch.object(recovery, 'status'))
            stack.enter_context(patch.object(recovery, 'phase', side_effect=phase))
            stack.enter_context(patch.object(scoring, 'score', return_value={}))
            stack.enter_context(patch.object(scoring, 'write_report'))
            recovery.continue_recipes(state, plan, root)
            self.assertEqual(events, [('binary', 'train'), ('binary', 'generate'), ('joint', 'train'), ('joint', 'generate')])
            self.assertEqual(state['status'], 'completed')

    def test_failure_does_not_launch_a_later_arm(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); repair = root / 'recovery'
            queue.save(repair / 'plan.json', {'checkpoint_step': 1500})
            state = dict(status='running', arms={'base': {'status': 'completed'}, 'binary': {}})
            with patch.object(recovery, 'ROOT', root), patch.object(recovery, 'RECOVERY', repair), patch.object(recovery, 'status'), patch.object(recovery, 'phase', side_effect=RuntimeError('worker failed')) as phase:
                with self.assertRaises(RuntimeError):
                    recovery.continue_recipes(state, {'recipes': ['base', 'binary', 'joint']}, root)
                self.assertEqual(phase.call_count, 1)
                self.assertNotIn('joint', state['arms'])

    def test_status_handles_empty_new_training_log(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); out = root / 'resume'; out.mkdir(); (out / 'train.jsonl').touch()
            state = dict(status='running', arms={'binary': {'status': 'train', 'resumed_from_step': 1500}})
            with patch.object(recovery, 'ROOT', root), patch.object(recovery, 'TRAIN_OUT', out):
                recovery.status(state)
            self.assertIn('1500/2688', (root / 'status.md').read_text())


if __name__ == '__main__':
    unittest.main()
