"""Bounded, isolated Qwen backbone timing on frozen real OopsieData windows.

Temporary QLoRA updates are discarded. This is neither a recipe sweep nor an
accuracy experiment. Source data, native teacher outputs and old runs are read-only.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import gc
import errno
import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import re
import statistics
import shutil
import time


MODELS = {
    'reference': ('Qwen/Qwen2.5-VL-7B-Instruct', 'cc594898137f460bfe9f0759e9844b3ce807cfb5'),
    'candidate': ('Qwen/Qwen3.8-27B', '37561816e66b5b9153b1b64c10968c18c1e6f4a0'),
}
SOURCE = 'outputs/corral_astra_rich_failure_v8_2_carryforward_batch_v3'
CASES = [('C0052', 1328, 64), ('C0052', 1328, 128),
         ('C0052', 1320, 192), ('C0079', 48, 192)]


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def save(path, value, exclusive=False):
    path = Path(path)
    with path.open('x' if exclusive else 'w', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)


def targets(parsed, start, stop, *, require_details=True):
    """Keep the native event partition; explanations require wholly visible cites."""
    segments = [dict(start=max(start, s['start_frame']), end=min(stop, s['end_frame']),
                     failure=s['failure']) for s in parsed['segments']
                if s['start_frame'] < stop and s['end_frame'] > start]
    if not segments or segments[0]['start'] != start or segments[-1]['end'] != stop:
        raise ValueError('Incomplete source coverage')
    if any(a['end'] != b['start'] for a, b in zip(segments, segments[1:])):
        raise ValueError('Gap in source partition')
    details = []
    for item in parsed['failure_annotations']:
        if item['start_frame'] < start or item['end_frame'] > stop:
            continue
        # All numerical frame citations in these frozen explanations must be visible.
        cites = [int(n) for n in re.findall(r'\d+', item['explanation'])]
        if cites and all(start <= n < stop for n in cites):
            details.append(item)
    if require_details and not details:
        raise ValueError('Select a probe window with a fully visible explanation')
    base = '# Failure segments\n\n| Start frame | End frame (exclusive) | Failure |\n|---|---|---|\n'
    base += ''.join(f"| {s['start']} | {s['end']} | {'Yes' if s['failure'] else 'No'} |\n" for s in segments)
    out = {}
    for mode in ['S', 'SC', 'SE', 'SCE', 'E']:
        text = '' if mode == 'E' else base
        if mode != 'S':
            columns = ['Start frame', 'End frame (exclusive)']
            if 'C' in mode:
                columns.append('Categories')
            if 'E' in mode:
                columns.append('Explanation')
            text += '\n# Visible failure details\n\n| ' + ' | '.join(columns) + ' |\n'
            text += '|' + '|'.join(['---'] * len(columns)) + '|\n'
            for detail in details:
                row = [str(detail['start_frame']), str(detail['end_frame'])]
                if 'C' in mode:
                    row.append(', '.join(detail['categories']))
                if 'E' in mode:
                    row.append(detail['explanation'].replace('|', '/').replace('\n', ' '))
                text += '| ' + ' | '.join(row) + ' |\n'
        out[mode] = text
    return out


def prepare(root):
    import shutil
    repo = Path(__file__).resolve().parents[2]
    source = repo / SOURCE
    root.mkdir(parents=True, exist_ok=True)
    if (root / 'plan.json').exists():
        raise ValueError('Plan already exists; preserve this version')
    windows = []
    for episode, start, count in CASES:
        prepared = read(source / 'prepared' / (episode + '.json'))
        canonical = source / 'canonical' / (episode + '_final')
        response = read(canonical / 'response.json')
        if response['model'] != 'gpt-6-astra':
            raise ValueError('Unexpected actual teacher identity')
        annotation = read(canonical / 'parsed.json')
        rows = prepared['images'][start:start + count]
        if [r['frame'] for r in rows] != list(range(start, start + count)):
            raise ValueError('Frame sequence differs from requested native window')
        images = []
        for row in rows:
            destination = root / row['path']
            if not destination.exists():
                candidates = [repo / 'outputs' / name / row['path'] for name in [
                    'corral_astra_rich_failure_v8_2_carryforward_pilot_v1',
                    'corral_astra_rich_failure_v8_2_1000_batch_v2',
                    'corral_astra_rich_failure_v8_2_1000_v1']]
                original = next((p for p in candidates if p.is_file()), None)
                if original is None:
                    raise FileNotFoundError(row['path'])
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(original, destination)
            if digest(destination) != row['sha256']:
                raise ValueError('Frozen source image mismatch')
            images.append(dict(path=row['path'], frame=row['frame'], sha256=row['sha256']))
        windows.append(dict(id=f'{episode}_{start}_{count}', episode=episode, start=start,
            count=count, fps=prepared['fps'], episode_frames=prepared['n_frames'],
            task=prepared['task'], cameras=prepared['cameras'], images=images,
            targets=targets(annotation, start, start + count), actual_teacher=response['model'],
            native_response_sha256=digest(canonical / 'response.json'),
            parsed_sha256=digest(canonical / 'parsed.json')))
    for src in [Path(__file__), repo / 'scripts/distill/requirements-backbone-timing-v1.txt',
                repo / 'scripts/tacc/qwen_backbone_timing_v1_setup.sbatch',
                repo / 'scripts/tacc/qwen_backbone_timing_v1_gpu.sbatch']:
        shutil.copyfile(src, root / src.name)
    files = {str(p.relative_to(root).as_posix()): digest(p) for p in root.rglob('*') if p.is_file()}
    plan = dict(protocol='qwen_backbone_timing_v1', created_utc=datetime.now(timezone.utc).isoformat(),
        models={key: dict(model=model, revision=rev) for key, (model, rev) in MODELS.items()},
        windows=windows, files_sha256=files, training_debug_episodes=['C0052', 'C0079'],
        split_requirement='Reserve these two probe episodes for train/debug in the subsequent study.',
        recipes=['S', 'SC', 'SE', 'SCE', 'S_plus_E_aux', 'S_compute_control'],
        warmup_updates=1, timed_updates=2, max_input_tokens=32768, lora_rank=16,
        lora_alpha=32, learning_rate=1e-4, seed=20261118, max_minutes_per_model=38,
        all_frames=True, max_pixels_per_frame=313600, inference_thinking=False,
        setup_cpu_hours_ceiling=2, gpu_hours_ceiling=1.5,
        gpu_su_ceiling=2.25, setup_su_ceiling=0.286,
        temporary_updates_discarded=True, automatic_full_sweep=False,
        test_used=False, new_teacher_calls=0)
    save(root / 'plan.json', plan, True)
    print(json.dumps(dict(plan=str(root / 'plan.json'), images=len(list((root / 'images').rglob('*.webp'))))))


def verify(root):
    plan = read(root / 'plan.json')
    for name, expected in plan['files_sha256'].items():
        path = (root / name).resolve()
        if not path.is_relative_to(root.resolve()) or digest(path) != expected:
            raise ValueError('Staged hash mismatch: ' + name)
    print(json.dumps(dict(verified=True, files=len(plan['files_sha256']))), flush=True)
    return plan


def reuse_model_file(original, target):
    """Reuse cached bytes without writing to the frozen source snapshot."""
    try:
        os.link(original.resolve(), target)
    except OSError as error:
        if error.errno not in {errno.EPERM, errno.EACCES, errno.EXDEV,
                               errno.EOPNOTSUPP, errno.ENOSYS}:
            raise
        partial = target.with_name(target.name + '.copy-part')
        try:
            shutil.copyfile(original, partial)
            partial.replace(target)
        finally:
            partial.unlink(missing_ok=True)


def fetch_model(root, model, revision):
    """Bounded resumable ranges; verify every LFS weight SHA before GPU use."""
    import requests
    from huggingface_hub import HfApi
    info = HfApi().model_info(model, revision=revision, files_metadata=True, token=False)
    destination = root / 'models' / model.split('/')[-1] / revision
    destination.mkdir(parents=True, exist_ok=True)
    candidates = [f for f in info.siblings if '/' not in f.rfilename and
                  f.rfilename.endswith(('.safetensors', '.json', '.txt', '.jinja', '.model'))]

    def fetch(meta):
        target = destination / meta.rfilename
        expected = meta.lfs.sha256 if meta.lfs else None
        if target.exists():
            if target.stat().st_size != meta.size or (expected and digest(target) != expected):
                raise ValueError('Existing model file mismatch: ' + target.name)
        else:
            partial = target.with_name(target.name + '.part')
            offset = partial.stat().st_size if partial.exists() else 0
            if offset > meta.size:
                raise ValueError('Oversized partial file')
            while offset < meta.size:
                end = min(meta.size - 1, offset + 32 * 1024 * 1024 - 1)
                ranged = meta.size > 64 * 1024 * 1024
                headers = {'Range': f'bytes={offset}-{end}'} if ranged else {}
                for attempt in range(4):
                    try:
                        url = f'https://huggingface.co/{model}/resolve/{revision}/{meta.rfilename}?timing={time.time_ns()}'
                        with requests.get(url, headers=headers, timeout=(20, 90)) as response:
                            response.raise_for_status()
                            if ranged and (response.status_code != 206 or
                                not response.headers.get('Content-Range', '').startswith(f'bytes {offset}-')):
                                raise ValueError('Model download range not honored')
                            content = response.content
                        if len(content) != (end - offset + 1 if ranged else meta.size):
                            raise ValueError('Incomplete model range')
                        break
                    except (requests.RequestException, ValueError):
                        if attempt == 3:
                            raise
                        time.sleep(2 ** attempt)
                with partial.open('ab' if offset else 'wb') as stream:
                    stream.write(content)
                offset += len(content)
            if partial.stat().st_size != meta.size or (expected and digest(partial) != expected):
                raise ValueError('Downloaded model hash mismatch')
            partial.replace(target)
        record = dict(file=target.name, bytes=meta.size, sha256=digest(target), lfs_sha256=expected)
        print(json.dumps(dict(model=model, **record)), flush=True)
        return record

    # Reuse the old cache; fetch() still checks sizes and weight hashes below.
    if model == MODELS['reference'][0]:
        old = Path('/scratch/11388/al62479/ftl-oopsie-full-v1/hf/hub') / 'models--Qwen--Qwen2.5-VL-7B-Instruct/snapshots' / revision
        for meta in candidates:
            original = old / meta.rfilename
            target = destination / meta.rfilename
            if original.is_file() and not target.exists():
                reuse_model_file(original, target)
    with ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(fetch, candidates))
    save(destination / 'verified_files.json', records)
    return str(destination)


def encode(processor, root, window, mode, model_type, *, include_target=True):
    import numpy as np
    from PIL import Image
    import torch
    from transformers.video_utils import VideoMetadata
    frames = []
    for image in window['images']:
        with Image.open(root / image['path']) as source:
            frames.append(np.array(source.convert('RGB')))
    indices = [x['frame'] for x in window['images']]
    instruction = ('Explain wholly visible failure events.' if mode == 'E' else
        'Label failure segments covering every supplied frame; preserve distinct adjacent failure events.')
    fields = {'S': 'segments', 'SC': 'segments and categories', 'SE': 'segments and explanations',
              'SCE': 'segments, categories and explanations', 'E': 'explanations'}[mode]
    prompt = (f"Task: {window['task']}\n{instruction}\nOutput Markdown with {fields}. "
        f"Global native frame interval [{window['start']}, {window['start'] + window['count']}); "
        f"end indices are exclusive. Native FPS: {window['fps']}. "
        f"All {window['count']} consecutive frames and all camera panels are supplied. "
        'Do not label outside this interval. Include detailed categories/explanations only for wholly visible events. '
        'Use the headings Failure segments and Visible failure details as applicable, with frame-index tables.')
    prompt = window.get('prompt', prompt)
    messages = [dict(role='user', content=[dict(type='video', video='native frames'), dict(type='text', text=prompt)])]
    prefix = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)
    full = prefix + window['targets'][mode] + processor.tokenizer.eos_token + '\n' if include_target else prefix
    metadata = VideoMetadata(total_num_frames=window['episode_frames'], fps=window['fps'], frames_indices=indices.copy())
    # Qwen3-VL's longest_edge is a whole-video pixel budget, Qwen2.5's is per frame.
    budget = 313600 * window['count'] if model_type == 'qwen3_5' else 313600
    kwargs = dict(text=[full], videos=[np.stack(frames)], video_metadata=[metadata],
        do_sample_frames=False, fps=window['fps'], return_metadata=True,
        size=dict(shortest_edge=3136, longest_edge=budget), return_tensors='pt', device='cpu')
    if model_type == 'qwen3_5':
        kwargs.update(cap_pixels_per_frame=True, max_video_tokens=307)
    batch = processor(**kwargs)
    returned = batch.pop('video_metadata', None)
    temporal_patch = processor.video_processor.temporal_patch_size
    # Qwen's timestamp formatter may append the last frame to fill a temporal patch.
    padded_indices = indices + [indices[-1]] * (-len(indices) % temporal_patch)
    if returned is not None and list(returned[0].frames_indices) not in (indices, padded_indices):
        raise ValueError('Native frame indices were sampled or reordered')
    grid = batch['video_grid_thw'][0].tolist()
    if grid[0] != math.ceil(window['count'] / temporal_patch):
        raise ValueError('Unexpected native temporal patch count')
    patch_size = processor.video_processor.patch_size
    represented_pixels = grid[1] * grid[2] * patch_size ** 2
    native_pixels = frames[0].shape[0] * frames[0].shape[1]
    if represented_pixels < native_pixels * .82:
        raise ValueError('Processor unexpectedly downsized camera panels')
    ids = batch['input_ids'][0]
    if len(ids) > 32768:
        raise ValueError('Input exceeds declared 32768-token contract')
    if not include_target:
        return batch
    plain = processor.tokenizer(full, add_special_tokens=False, return_offsets_mapping=True)
    first = next(i for i, (a, b) in enumerate(plain['offset_mapping']) if a >= len(prefix) and b > a)
    tail = plain['input_ids'][first:]
    if ids[-len(tail):].tolist() != tail:
        raise ValueError('Assistant tokens changed during native video expansion')
    labels = torch.full_like(batch['input_ids'], -100)
    labels[0, -len(tail):] = ids[-len(tail):]
    batch['labels'] = labels
    audit = dict(case=window['id'], mode=mode, input_tokens=len(ids), target_tokens=len(tail),
        source_frames=window['count'], frame_indices=indices, grid=grid,
        represented_pixels_per_frame=represented_pixels, native_pixels_per_frame=native_pixels,
        source_fps=window['fps'], do_sample_frames=False)
    return batch, audit


def setup(root):
    plan = verify(root)
    import torch
    import transformers
    import fla
    import causal_conv1d
    from transformers import AutoProcessor
    snapshots = {key: fetch_model(root, **entry) for key, entry in plan['models'].items()}
    audits = []
    for key, snapshot in snapshots.items():
        processor = AutoProcessor.from_pretrained(snapshot, local_files_only=True)
        for window in plan['windows']:
            for mode in ['S', 'SC', 'SE', 'SCE', 'E']:
                batch, audit = encode(processor, root, window, mode, 'qwen3_5' if key == 'candidate' else 'qwen2_5_vl')
                audits.append(dict(model=key, **audit))
                del batch
    packages = ['torch', 'torchvision', 'transformers', 'numpy', 'peft', 'accelerate',
                'bitsandbytes', 'flash-linear-attention', 'causal-conv1d']
    save(root / 'setup_ready.json', dict(plan_sha256=digest(root / 'plan.json'), snapshots=snapshots,
        versions={p: importlib.metadata.version(p) for p in packages}, cpu_input_audits=audits,
        models_loaded=False, teacher_calls=0), True)
    print(json.dumps(dict(setup_complete=True, cpu_input_audits=len(audits))), flush=True)


def loss_sum(model, batch):
    import torch
    from torch.utils.checkpoint import checkpoint
    base = model.get_base_model()
    labels = batch['labels'][0]
    hidden = base.model(**{k: v for k, v in batch.items() if k != 'labels'}, use_cache=False).last_hidden_state[0]
    positions = (labels[1:] != -100).nonzero().flatten()
    selected = hidden[positions]
    targets = labels[1:][positions]
    def project(states, weight, target):
        return torch.nn.functional.cross_entropy(torch.nn.functional.linear(states, weight).float(), target, reduction='sum')
    losses = [checkpoint(project, selected[i:i + 64], base.lm_head.weight, targets[i:i + 64],
                         use_reentrant=False) for i in range(0, len(positions), 64)]
    return torch.stack(losses).sum() / len(positions)


def load_qlora(snapshot, *, require_linear_attention, adapter=None):
    import torch
    from peft import LoraConfig, PeftModel, get_peft_model, prepare_model_for_kbit_training
    from transformers import AutoModelForImageTextToText, BitsAndBytesConfig
    quantization = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type='nf4',
        bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=torch.bfloat16,
        llm_int8_skip_modules=['lm_head', 'model.visual', 'in_proj_a', 'in_proj_b'])
    model = AutoModelForImageTextToText.from_pretrained(snapshot, local_files_only=True,
        dtype=torch.bfloat16, device_map={'': 0}, attn_implementation='sdpa', quantization_config=quantization)
    model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True,
        gradient_checkpointing_kwargs={'use_reentrant': False})
    # PEFT promotes all unquantized weights to fp32. Keep norms/gates there,
    # but restore frozen large tensors and convolution weights to bf16. The
    # causal-conv1d CUDA kernel requires input and convolution weight dtypes to match.
    for name, parameter in model.named_parameters():
        if parameter.dtype == torch.float32 and any(part in name for part in
                ['.visual.', 'embed_tokens.', 'lm_head.', '.conv1d.']):
            parameter.data = parameter.data.to(torch.bfloat16)
    model.config.use_cache = False
    model.enable_input_require_grads()
    suffixes = {'q_proj', 'k_proj', 'v_proj', 'o_proj', 'gate_proj', 'up_proj', 'down_proj',
                'in_proj_qkv', 'in_proj_z', 'in_proj_a', 'in_proj_b', 'out_proj'}
    modules = [name for name, module in model.named_modules() if '.layers.' in name and
               '.visual.' not in name and name.rsplit('.', 1)[-1] in suffixes]
    if not modules or (require_linear_attention and not any('.linear_attn.in_proj_qkv' in name for name in modules)):
        raise ValueError('Missing decoder attention adapters')
    if adapter is None:
        model = get_peft_model(model, LoraConfig(r=16, lora_alpha=32, lora_dropout=.05,
            target_modules=modules, bias='none', task_type='CAUSAL_LM'))
    else:
        model = PeftModel.from_pretrained(model, adapter, is_trainable=True)
    if any(p.requires_grad for name, p in model.named_parameters() if '.visual.' in name):
        raise ValueError('Vision tower must remain frozen')
    return model, modules


def gpu(root, key):
    import os
    import signal
    import torch
    from transformers import AutoProcessor, set_seed
    ready = read(root / 'setup_ready.json')
    plan = verify(root)
    if ready['plan_sha256'] != digest(root / 'plan.json'):
        raise ValueError('Setup was completed for another plan')
    result_path = root / (key + '_result.json')
    if result_path.exists():
        raise ValueError('A timing result already exists; do not duplicate this run')
    if not torch.cuda.is_available():
        raise ValueError('GPU job has no CUDA device')
    device = torch.cuda.get_device_properties(0)
    if 'A100' not in device.name or device.total_memory < 39 * 1024 ** 3:
        raise ValueError('Timing requires the requested A100 40GB')
    set_seed(plan['seed'])
    deadline = time.monotonic() + plan['max_minutes_per_model'] * 60
    stop = [False]
    signal.signal(signal.SIGUSR1, lambda *_: stop.__setitem__(0, True))
    result = dict(model_key=key, model=plan['models'][key], gpu=device.name,
        gpu_memory_gib=device.total_memory / 1024 ** 3, slurm_job=os.environ.get('SLURM_JOB_ID'),
        plan_sha256=digest(root / 'plan.json'), measurements=[], failures=[],
        temporary_updates_discarded=True, accuracy_evaluated=False, complete=False)
    save(result_path, result, True)
    snapshot = ready['snapshots'][key]
    processor = AutoProcessor.from_pretrained(snapshot, local_files_only=True)
    started = time.monotonic()
    model, modules = load_qlora(snapshot, require_linear_attention=key == 'candidate')
    result.update(model_load_seconds=time.monotonic() - started, lora_target_modules=modules,
        trainable_parameters=sum(p.numel() for p in model.parameters() if p.requires_grad))
    if key == 'candidate':
        import fla.ops.gated_delta_rule
        import causal_conv1d
        result['optimized_linear_attention_packages_imported'] = True
    optimizer = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=1e-4)
    representative = None
    for window in plan['windows']:
        if stop[0] or time.monotonic() > deadline:
            break
        for mode in ['S', 'SC', 'SE', 'SCE', 'S_plus_E_aux']:
            if stop[0] or time.monotonic() > deadline:
                break
            try:
                model.train()
                t = time.monotonic()
                encoded, audit = encode(processor, root, window, 'S' if mode == 'S_plus_E_aux' else mode,
                    'qwen3_5' if key == 'candidate' else 'qwen2_5_vl')
                batch = {k: v.to('cuda') if hasattr(v, 'to') else v for k, v in encoded.items()}
                aux = None
                if mode == 'S_plus_E_aux':
                    aux_encoded, _ = encode(processor, root, window, 'E', 'qwen3_5' if key == 'candidate' else 'qwen2_5_vl')
                    aux = {k: v.to('cuda') if hasattr(v, 'to') else v for k, v in aux_encoded.items()}
                preprocess_seconds = time.monotonic() - t
                times = []
                for update in range(plan['warmup_updates'] + plan['timed_updates']):
                    if stop[0] or time.monotonic() > deadline:
                        break
                    optimizer.zero_grad(set_to_none=True)
                    torch.cuda.reset_peak_memory_stats()
                    torch.cuda.synchronize()
                    t = time.monotonic()
                    with torch.autocast('cuda', dtype=torch.bfloat16):
                        loss = loss_sum(model, batch)
                    if not torch.isfinite(loss):
                        raise ValueError('Nonfinite primary loss')
                    loss.backward()
                    if aux is not None:
                        with torch.autocast('cuda', dtype=torch.bfloat16):
                            extra = loss_sum(model, aux) * .3
                        if not torch.isfinite(extra):
                            raise ValueError('Nonfinite auxiliary loss')
                        extra.backward()
                    grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), 1.)
                    if not torch.isfinite(grad_norm):
                        raise ValueError('Nonfinite adapter gradients')
                    optimizer.step()
                    torch.cuda.synchronize()
                    elapsed = time.monotonic() - t
                    entry = dict(case=window['id'], recipe=mode, update=update,
                        warmup=update < plan['warmup_updates'], step_seconds=elapsed,
                        loss=float(loss.detach()), grad_norm=float(grad_norm),
                        peak_allocated_gib=torch.cuda.max_memory_allocated() / 1024 ** 3,
                        peak_reserved_gib=torch.cuda.max_memory_reserved() / 1024 ** 3,
                        input_tokens=audit['input_tokens'], supervised_tokens=audit['target_tokens'],
                        preprocessing_seconds=preprocess_seconds, source_frames=window['count'])
                    result['measurements'].append(entry)
                    save(result_path, result)
                    print(json.dumps(entry), flush=True)
                    if not entry['warmup']:
                        times.append(elapsed)
                if representative is None and times:
                    representative = (window, batch)
                if representative is None or representative[1] is not batch:
                    del batch
                del encoded
                if aux is not None:
                    del aux, aux_encoded
            except torch.cuda.OutOfMemoryError as exc:
                result['failures'].append(dict(case=window['id'], recipe=mode,
                    error='CUDAOutOfMemory',detail=str(exc)[:500]))
                # Return a useful limit report without retrying the failing shape.
                optimizer.zero_grad(set_to_none=True)
                batch = aux = encoded = aux_encoded = loss = extra = None
                gc.collect()
                torch.cuda.empty_cache()
                save(result_path, result)
                break
    if representative is not None and not stop[0] and time.monotonic() < deadline:
        model.eval()
        window, batch = representative
        with torch.no_grad(), torch.autocast('cuda', dtype=torch.bfloat16):
            expected_loss = float(loss_sum(model, batch))
        adapter = root / (key + '_temporary_adapter')
        model.save_pretrained(adapter, safe_serialization=True)
        # Replace trained tensors with checkpoint values and verify the exact loss.
        from peft import set_peft_model_state_dict
        from safetensors.torch import load_file
        weights = load_file(str(adapter / 'adapter_model.safetensors'))
        with torch.no_grad():
            for name, parameter in model.named_parameters():
                if 'lora_' in name:
                    parameter.zero_()
        set_peft_model_state_dict(model, weights)
        with torch.no_grad(), torch.autocast('cuda', dtype=torch.bfloat16):
            reloaded_loss = float(loss_sum(model, batch))
        if abs(expected_loss - reloaded_loss) > 1e-4:
            raise ValueError('Adapter save/reload changed deterministic loss')
        result['adapter_reload'] = dict(passed=True, before=expected_loss, after=reloaded_loss,
            note='Adapter tensors restored into the same pinned, frozen base; not a fresh-process base reload.')
        prompt_batch = {k: v for k, v in batch.items() if k != 'labels'}
        first_target = int((batch['labels'][0] != -100).nonzero()[0])
        prompt_batch['input_ids'] = prompt_batch['input_ids'][:, :first_target]
        prompt_batch['attention_mask'] = prompt_batch['attention_mask'][:, :first_target]
        with torch.no_grad():
            generated = model.generate(**prompt_batch, max_new_tokens=96, do_sample=False, use_cache=True)
        decoded = processor.tokenizer.decode(generated[0, first_target:], skip_special_tokens=True)
        result['generation_smoke'] = dict(text=decoded, generated_tokens=generated.shape[1] - first_target,
            accuracy_evaluated=False, schema_quality_not_established=True)
    result['complete'] = not stop[0] and time.monotonic() <= deadline
    result['wall_seconds'] = plan['max_minutes_per_model'] * 60 - max(0, deadline - time.monotonic())
    result['time_budget_reached'] = not result['complete']
    result['compute_control_timing'] = 'Same S step cost; total updates depend on the later frozen matching budget.'
    save(result_path, result)


def report(root):
    results = {key: read(root / (key + '_result.json')) for key in MODELS}
    grouped = {}
    for key, result in results.items():
        for row in result['measurements']:
            if not row['warmup']:
                grouped.setdefault((key, row['case'], row['recipe']), []).append(row['step_seconds'])
    ratios = []
    for key, case, recipe in grouped:
        if key == 'candidate' and ('reference', case, recipe) in grouped:
            a = statistics.median(grouped[(key, case, recipe)])
            b = statistics.median(grouped[('reference', case, recipe)])
            ratios.append(dict(case=case, recipe=recipe, candidate_seconds=a, reference_seconds=b,
                               candidate_to_reference_ratio=a / b))
    save(root / 'comparison.json', dict(results=results, comparisons=ratios,
        new_teacher_calls=0, full_sweep_submitted=False, training_accuracy_claimed=False))
    print(json.dumps(dict(comparisons=ratios, complete=True)), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['prepare', 'verify', 'setup', 'gpu', 'report'])
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--model', choices=list(MODELS))
    args = parser.parse_args()
    if args.command == 'gpu':
        gpu(args.root, args.model)
    else:
        globals()[args.command](args.root)
