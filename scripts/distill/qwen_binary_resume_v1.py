"""Resume a frozen binary recipe into a fresh directory, keeping its old evidence."""
from collections import Counter
import importlib.metadata
import json
import math
from pathlib import Path
import random
import time

import qwen_recipe_runner as runner


def last_entry(path):
    """A reboot may leave a partial final line; retain the last durable update."""
    result = None
    for line in Path(path).read_text(encoding='utf-8').splitlines():
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if 'step' in entry:
            result = entry
    if result is None:
        raise ValueError('No durable training updates')
    return result


def inspect_checkpoint(folder, original, updates, max_hours):
    import torch
    original = Path(original)
    spec = runner.common.read(original / 'run.json')
    study, _, _ = runner.load(folder)
    if spec['recipe'] != 'binary' or spec['init_adapter'] is not None:
        raise ValueError('This recovery supports the original binary arm only')
    expected = dict(student=runner.cfg_for(study), planned_updates=updates, max_hours=max_hours,
                    study_sha256=runner.common.sha(Path(folder).parent / 'study.json'),
                    records_sha256=runner.common.sha(Path(folder) / 'records.jsonl'),
                    adapter_sha256=runner.common.sha(Path(folder) / 'adapter.json'))
    if any(spec[k] != v for k, v in expected.items()):
        raise ValueError('Saved binary recipe differs from the approved recipe')
    versions = {n: importlib.metadata.version(n) for n in spec['versions']}
    if versions != spec['versions']:
        raise ValueError('Training runtime versions changed')
    if (original / 'completion.json').exists():
        raise ValueError('Binary training already has a completion receipt')
    # This is our own trusted, hash-checked local PyTorch checkpoint, not downloaded code.
    saved = torch.load(original / 'training_state.pt', map_location='cpu', weights_only=False)
    required = {'optimizer', 'python_rng', 'torch_rng', 'cuda_rng', 'seen', 'total_tokens', 'examples'}
    if not required.issubset(saved) or not 0 < saved['step'] < updates:
        raise ValueError('Incomplete or terminal checkpoint')
    if saved['planned_updates'] != updates or saved['records_sha256'] != expected['records_sha256']:
        raise ValueError('Checkpoint schedule or records changed')
    adapter = Path(saved['adapter']).resolve()
    if adapter != (original / f"adapter_step_{saved['step']}").resolve() or not adapter.is_dir():
        raise ValueError('Checkpoint adapter path differs from its saved step')
    states = saved['optimizer']['state']
    if not states or any(int(s['step']) != saved['step'] for s in states.values()):
        raise ValueError('Optimizer state does not match the adapter update')
    if saved['examples'] != saved['step'] * spec['primary_examples_per_update']:
        raise ValueError('Checkpoint sample position differs from the approved schedule')
    logged = last_entry(original / 'train.jsonl')
    if logged['step'] < saved['step'] or logged['elapsed_seconds'] >= max_hours * 3600:
        raise ValueError('Invalid checkpoint history or exhausted training ceiling')
    return saved, logged


def restore_training_state(model, optimizer, saved):
    """Check parameter correspondence, then restore optimizer and all saved RNGs."""
    import torch
    parameters = [p for p in model.parameters() if p.requires_grad]
    ids = [i for group in saved['optimizer']['param_groups'] for i in group['params']]
    if len(ids) != len(parameters):
        raise ValueError('Optimizer parameter count changed')
    for parameter, index in zip(parameters, ids):
        for key in ('exp_avg', 'exp_avg_sq'):
            if saved['optimizer']['state'][index][key].shape != parameter.shape:
                raise ValueError('Optimizer parameter shapes changed')
    optimizer.load_state_dict(saved['optimizer'])
    random.setstate(saved['python_rng'])
    torch.set_rng_state(saved['torch_rng'])
    torch.cuda.set_rng_state_all(saved['cuda_rng'])
    return parameters


def train(folder, original, out, updates, max_hours):
    import torch
    out = Path(out)
    if out.exists():
        raise ValueError('Recovery output exists; no automatic duplicate/retry')
    saved, logged = inspect_checkpoint(folder, original, updates, max_hours)
    study, source, rows = runner.load(folder)
    cfg = runner.cfg_for(study)
    order = runner.sample_primary([r for r in rows if r['split'] == 'train' and r['task'] == 'binary'], cfg['seed'])
    processor = runner.core.processor_for(cfg)
    random.seed(cfg['seed']); torch.manual_seed(cfg['seed']); torch.cuda.manual_seed_all(cfg['seed'])
    model = runner.core.load_model(cfg, trainable=True, adapter=Path(saved['adapter']))
    model.train()
    optimizer = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=cfg['learning_rate'])
    parameters = restore_training_state(model, optimizer, saved)
    out.mkdir(parents=True)
    runner.write_once(out / 'run.json', dict(recipe='binary', resumed_from=str(original),
        checkpoint_step=saved['step'], planned_updates=updates, max_hours=max_hours,
        previous_consumed_seconds=logged['elapsed_seconds'],
        optimizer_restored=True, python_rng_restored=True, torch_rng_restored=True,
        cuda_rng_restored=True, warm_start_optimizer_reinitialized=False, test_used=False))
    seen = Counter(saved['seen']); total_tokens = saved['total_tokens']; examples = saved['examples']
    start = time.monotonic()
    elapsed = lambda: logged['elapsed_seconds'] + time.monotonic() - start
    print(json.dumps(dict(resumed_step=saved['step'], next_step=saved['step'] + 1,
                         optimizer_restored=True, remaining_seconds=max_hours * 3600 - elapsed())), flush=True)
    with (out / 'train.jsonl').open('x', encoding='utf-8', buffering=1) as log:
        for step in range(saved['step'] + 1, updates + 1):
            optimizer.zero_grad(set_to_none=True)
            loss_sum = 0.; t = time.monotonic(); step_tokens = 0
            torch.cuda.reset_peak_memory_stats()
            for j in range(cfg['gradient_accumulation']):
                i = (step - 1) * cfg['gradient_accumulation'] + j
                row = order[i % len(order)]
                batch = runner.core.encode_train(processor, source, row, cfg['max_length'])
                n = int(batch['input_ids'].shape[1])
                batch = {k: v.to('cuda') for k, v in batch.items()}
                with torch.autocast('cuda', dtype=torch.bfloat16):
                    loss, count = runner.core.sft_loss(model, batch)
                if not torch.isfinite(loss):
                    raise ValueError('Nonfinite loss')
                weight = 1 / cfg['gradient_accumulation']
                (loss / count * weight).backward()
                loss_sum += float(loss.detach()) / count * weight
                step_tokens += n; examples += 1; seen[row['episode']] += 1
                del batch, loss
            norm = torch.nn.utils.clip_grad_norm_(parameters, 1, error_if_nonfinite=True)
            warmup = max(1, math.ceil(updates * .03))
            scale = step / warmup if step <= warmup else .1 + .9 * (1 + math.cos(math.pi * (step - warmup) / max(1, updates - warmup))) / 2
            for group in optimizer.param_groups:
                group['lr'] = cfg['learning_rate'] * scale
            optimizer.step(); torch.cuda.synchronize(); total_tokens += step_tokens
            entry = dict(step=step, loss=loss_sum, grad_norm=float(norm), step_seconds=time.monotonic() - t,
                elapsed_seconds=elapsed(), input_tokens=step_tokens,
                peak_gpu_gib=torch.cuda.max_memory_allocated() / 1024**3, unique_training_episodes_seen=len(seen))
            log.write(json.dumps(entry) + '\n'); print(json.dumps(entry), flush=True)
            if step % study['config'].get('checkpoint_every_updates', 10) == 0 or step == updates or elapsed() > max_hours * 3600:
                checkpoint = out / f'adapter_step_{step}'
                model.save_pretrained(checkpoint); processor.save_pretrained(checkpoint)
                state = dict(step=step, optimizer=optimizer.state_dict(), python_rng=random.getstate(),
                    torch_rng=torch.get_rng_state(), cuda_rng=torch.cuda.get_rng_state_all(),
                    adapter=str(checkpoint.resolve()), planned_updates=updates,
                    records_sha256=runner.common.sha(Path(folder) / 'records.jsonl'), seen=dict(seen),
                    total_tokens=total_tokens, examples=examples, elapsed_seconds=elapsed())
                temporary = out / 'training_state.tmp'
                torch.save(state, temporary); temporary.replace(out / 'training_state.pt')
            if elapsed() > max_hours * 3600:
                break
    result = dict(recipe='binary', steps=step, planned_updates=updates, completed_schedule=step == updates,
        adapter=str(checkpoint.resolve()), elapsed_seconds=elapsed(), input_tokens=total_tokens, examples=examples,
        unique_training_episodes_seen=len(seen), optimizer_resume_supported=True, optimizer_state_preserved=True,
        recovery_start_step=saved['step'], original_artifacts_preserved=True)
    runner.write_once(out / 'completion.json', result)
    return result
