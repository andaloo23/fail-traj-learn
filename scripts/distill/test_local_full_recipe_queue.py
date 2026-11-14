"""Exercise approval, sequential execution and failures without loading a model."""
from contextlib import ExitStack
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import local_full_recipe_queue as queue
import qwen_recipe_runner as runner
import score_recipe_suite as scoring


class LocalQueueTests(unittest.TestCase):
    def fixture(self,root):
        folder=root/'evidence';folder.mkdir()
        queue.save(folder/'token_audit.json',dict(overlength=0,adapter_sha256='fixed'))
        queue.save(root/'plan.json',dict(test='not an actual experiment approval'))
        plan=dict(recipes=['base','binary'],adapter_sha256='fixed')
        rows=[dict(split='train',task='binary',episode=str(i)) for i in range(400)]
        torch=SimpleNamespace(__version__='test',version=SimpleNamespace(cuda='test'),
            cuda=SimpleNamespace(is_available=lambda:True,get_device_name=lambda:'NVIDIA GeForce RTX 3090'),
            backends=SimpleNamespace(cuda=SimpleNamespace(is_flash_attention_available=lambda:True)))
        return folder,plan,rows,torch

    def execute(self,root,phase):
        folder,plan,rows,torch=self.fixture(root)
        with ExitStack() as stack:
            stack.enter_context(patch.object(queue,'ROOT',root))
            stack.enter_context(patch.object(queue,'approved',return_value=(plan,folder)))
            stack.enter_context(patch.object(queue,'run_phase',side_effect=phase))
            stack.enter_context(patch.object(runner,'load',return_value=({},root,rows)))
            stack.enter_context(patch.object(scoring,'score',return_value={'test':'score'}))
            stack.enter_context(patch.object(scoring,'write_report'))
            stack.enter_context(patch.dict(sys.modules,{'torch':torch}))
            queue.run()

    def test_baseline_then_training_then_evaluation_without_overlap(self):
        events=[]
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            def phase(recipe,name,state):
                events.append((recipe,name))
                if name=='generate':queue.save(root/'predictions'/recipe/'completion.json',dict(complete=True))
                else:queue.save(root/'runs'/recipe/'completion.json',dict(completed_schedule=True,steps=2688))
            self.execute(root,phase)
            self.assertEqual(events,[('base','generate'),('binary','train'),('binary','generate')])
            self.assertEqual(queue.frozen.read(root/'queue.json')['status'],'completed')

    def test_failure_stops_later_gpu_arms_and_preserves_error(self):
        events=[]
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            def phase(recipe,name,state):
                events.append((recipe,name));raise RuntimeError('failed phase')
            with self.assertRaisesRegex(RuntimeError,'failed phase'):self.execute(root,phase)
            self.assertEqual(events,[('base','generate')])
            state=queue.frozen.read(root/'queue.json')
            self.assertEqual(state['status'],'failed');self.assertIn('failed phase',state['error'])

    def test_time_capped_generation_is_not_reported_as_completed_queue(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            def phase(recipe,name,state):
                if name=='generate':queue.save(root/'predictions'/recipe/'completion.json',dict(complete=False))
                else:queue.save(root/'runs'/recipe/'completion.json',dict(completed_schedule=True))
            self.execute(root,phase)
            self.assertEqual(queue.frozen.read(root/'queue.json')['status'],'finished_with_incomplete_arms')

    def test_existing_queue_cannot_be_silently_started_again(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);queue.save(root/'queue.json',dict(status='running'))
            folder,plan,_,_=self.fixture(root)
            with patch.object(queue,'ROOT',root),patch.object(queue,'approved',return_value=(plan,folder)):
                with self.assertRaisesRegex(ValueError,'already started'):queue.run()

    def test_changed_local_execution_file_invalidates_approval(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);execution=root/'queue.py';execution.write_text('original')
            parent=root/'canonical';parent.mkdir();(parent/'submission_plan.json').write_text('{}')
            plan=dict(parent_plan_sha256=queue.frozen.digest(parent/'submission_plan.json'),execution_sha256={str(execution):queue.frozen.digest(execution)})
            queue.save(root/'plan.json',plan)
            queue.save(root/'approval.json',dict(approved=True,plan_sha256=queue.frozen.digest(root/'plan.json')))
            execution.write_text('changed')
            with patch.object(queue,'ROOT',root),patch.object(queue.frozen,'ROOT',parent),patch.object(queue.frozen,'approval',return_value=({},root)):
                with self.assertRaisesRegex(ValueError,'code changed'):queue.approved()


if __name__=='__main__':unittest.main()
