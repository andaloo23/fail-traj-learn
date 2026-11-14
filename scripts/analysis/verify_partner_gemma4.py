"""Verify the supplied Gemma adapter on the frozen real OopsieData development split.

No training, teacher calls, or sealed-test access. Source prompts, frame windows,
camera strips and reference scoring match the existing Qwen study. Gemma uses its
native processor and the adapter's declared 70 visual soft-token budget.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import sys
import time

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'scripts/distill'))
import oopsie_common as common
import annotation_runtime as transport
import score_recipe_suite as scoring
import oopsie_recipe_data as recipe_data

RUN = REPO / 'outputs/partner_gemma4_archive_20261113_v1'
STUDY = REPO / 'outputs/oopsie_distillation_full_v1'
EVIDENCE = STUDY / 'evidence_c32_x8_v3'
MODEL = 'google/gemma-4-E4B-it'
REVISION = '4ecc2ba63bcac23ba4a767fc87025b1450f84c9c'


def now():
    return datetime.now(timezone.utc).isoformat()


def immutable(path, value):
    if path.exists():
        if common.read(path) != value:
            raise ValueError('Refusing to change frozen artifact: ' + str(path))
    else:
        common.write(path, value)


def context():
    study = common.read(STUDY / 'study.json')
    index = common.read(EVIDENCE / 'index.json')
    if common.sha(STUDY / 'study.json') != index['study_sha256'] or common.sha(EVIDENCE / 'records.jsonl') != index['records_sha256']:
        raise ValueError('Frozen validation inputs changed')
    if common.sha(EVIDENCE / 'adapter.json') != index['adapter_sha256']:
        raise ValueError('Frozen evidence adapter changed')
    source = REPO / study['config']['source_run']
    if common.sha(source / 'manifest.json') != study['source_manifest_sha256']:
        raise ValueError('Frozen source changed')
    rows = [json.loads(line) for line in (EVIDENCE / 'records.jsonl').read_text(encoding='utf-8').splitlines()]
    rows = [r for r in rows if r['split'] == 'development' and r['task'] == 'binary']
    if {r['episode'] for r in rows} != set(study['development_ids']) or len(study['development_ids']) != 50:
        raise ValueError('Expected exactly the existing 50 development episodes')
    manifest = common.read(source / 'manifest.json')
    episodes = {e['id']: e for e in manifest['episodes'] if e['id'] in study['development_ids']}
    return study, source, rows, episodes


def prepare():
    study, source, rows, episodes = context()
    archive = common.read(RUN / 'archive_verification.json')
    logs = [json.loads(line) for line in (RUN / 'received/train_log.jsonl').read_text().splitlines() if line.strip()]
    train_ids = {r['id'] for r in logs if r.get('event') == 'example'}
    old_eval = [json.loads(line) for line in (RUN / 'received/sft_v3_per_episode.jsonl').read_text().splitlines() if line.strip()]
    old_ids = {r['id'] for r in old_eval}
    confusion = Counter()
    for row in old_eval:
        p, r = row['pred_has_failure'], row['teacher_has_failure']
        confusion['tp' if p and r else 'fp' if p else 'fn' if r else 'tn'] += 1
    plan = dict(protocol='partner_gemma4_real_oopsie_development_v1', archive_sha256=archive['archive_sha256'],
        adapter_sha256=common.sha(RUN / 'received/adapter_model.safetensors'),
        adapter_config_sha256=common.sha(RUN / 'received/adapter_config.json'),
        model=MODEL, base_revision=REVISION, original_training_base_revision_known=False,
        split='development', episodes=50, episode_ids=study['development_ids'], windows=len(rows),
        total_scored_frames=sum(e['n_frames'] for e in episodes.values()),
        study_sha256=common.sha(STUDY / 'study.json'), records_sha256=index_hash(),
        source_manifest_sha256=study['source_manifest_sha256'], source_run=study['config']['source_run'],
        context_frames=8, core_frames=32, all_supplied_window_images_retained=True,
        camera_panels='Exact existing source camera strips; no synthetic camera roles or telemetry.',
        processor_max_soft_tokens=70, quantization='Original adapter loader NF4 double quantization; BF16 compute.',
        output_contract='Same binary Markdown window prompt as the Qwen study.',
        generation=dict(do_sample=False, max_new_tokens=768),
        reference='Frozen Sol V8.1; agreement is not human-ground-truth accuracy.',
        final_test_used=False, training=False, new_teacher_calls=False,
        supplied_training_unique_episode_ids=len(train_ids), supplied_eval_ids=len(old_ids),
        supplied_train_eval_overlap=sorted(train_ids & old_ids),
        current_development_id_overlap_with_supplied_training=sorted(train_ids & set(study['development_ids'])),
        supplied_old_eval_episode_confusion=dict(confusion),
        supplied_old_eval_episode_f1=2*confusion['tp']/(2*confusion['tp']+confusion['fp']+confusion['fn']),
        limitations=['The adapter was trained on the historical LIBERO-based D-series export, not real OopsieData.',
            'Matched binary-window evaluation changes the adapter training output contract (atomic JSON) and omits its synthetic robot-telemetry/events input.',
            'Gemma native visual tokenization differs from Qwen; source windows and pixels stay the same.',
            'Archive supplies per-episode scores but no raw historical predictions or pinned original base revision.'])
    immutable(RUN / 'evaluation_plan.json', plan)
    for name in ['prompt_short.py', 'model.py', 'data.py']:
        path = REPO / 'scripts/distill' / name
        dest = RUN / 'implementation' / name
        dest.parent.mkdir(exist_ok=True)
        if dest.exists():
            if dest.read_bytes() != path.read_bytes():
                raise ValueError('Loader source changed')
        else:
            dest.write_bytes(path.read_bytes())
    print(json.dumps({k: plan[k] for k in ['episodes', 'windows', 'total_scored_frames', 'supplied_training_unique_episode_ids', 'supplied_train_eval_overlap', 'supplied_old_eval_episode_confusion']}), flush=True)


def index_hash():
    return common.sha(EVIDENCE / 'records.jsonl')


def download():
    from huggingface_hub import snapshot_download
    path = snapshot_download(MODEL, revision=REVISION, allow_patterns=['*.json', '*.safetensors', '*.jinja'], max_workers=4)
    print('Pinned Gemma base downloaded: ' + path, flush=True)
    transport.atomic_json(RUN / 'model_download.json', dict(model=MODEL, revision=REVISION, snapshot=path, completed_utc=now()))


def runtime():
    import torch
    from transformers import AutoProcessor, AutoModelForImageTextToText
    from transformers.models.gemma4.modeling_gemma4 import Gemma4ForConditionalGeneration
    import peft
    import bitsandbytes
    result = dict(cuda_available=torch.cuda.is_available(), gpu=torch.cuda.get_device_name(),
        versions={name: importlib.metadata.version(name) for name in ['torch','transformers','peft','bitsandbytes','accelerate']},
        gemma4_class=Gemma4ForConditionalGeneration.__name__)
    transport.atomic_json(RUN / 'environment_check.json', result)
    print(json.dumps(result), flush=True)


def native_inputs(processor, source, row):
    from PIL import Image
    # Only the user input is copied. Stored assistant references never enter the model.
    rows = row if isinstance(row, list) else [row]
    prompts, image_batches = [], []
    for item_row in rows:
        message = item_row['messages'][0]
        if message['role'] != 'user':
            raise ValueError('Expected user-only visual input')
        images = []
        for item in message['content']:
            if item['type'] == 'image':
                with Image.open(common.inside(source, item['image'])) as image:
                    images.append(image.convert('RGB'))
        prompts.append(processor.apply_chat_template([message], tokenize=False, add_generation_prompt=True))
        image_batches.append(images)
    if isinstance(row, list):
        return processor(text=prompts, images=image_batches, padding=True, return_tensors='pt')
    return processor(text=prompts[0], images=image_batches[0], return_tensors='pt')


def batch_check():
    import torch
    from model import load_processor
    _, source, rows, _ = context()
    processor = load_processor(common.read(RUN / 'model_download.json')['snapshot'])
    processor.image_processor.max_soft_tokens = 70
    processor.tokenizer.padding_side = 'left'
    selected = rows[:2]
    separate = [native_inputs(processor, source, row) for row in selected]
    combined = native_inputs(processor, source, selected)
    image_offset = 0
    for i, single in enumerate(separate):
        mask = combined['attention_mask'][i].bool()
        assert torch.equal(combined['input_ids'][i][mask], single['input_ids'][0])
        assert torch.equal(combined['mm_token_type_ids'][i][mask],single['mm_token_type_ids'][0])
        n = single['pixel_values'].shape[0]
        assert torch.equal(combined['pixel_values'][image_offset:image_offset+n],single['pixel_values'])
        image_offset += n
    transport.atomic_json(RUN / 'batch_encoding_check.json',dict(batch_size=2,unpadded_token_ids_identical=True,
        modality_token_types_identical=True,pixel_tensors_identical=True))
    print('Batched and individual encoding have identical unpadded tokens, modality markers and image tensors.',flush=True)


def verify_loaded_adapter(model):
    from safetensors.torch import load_file
    import torch
    expected = load_file(str(RUN / 'received/adapter_model.safetensors'), device='cpu')
    actual = dict(model.named_parameters()); differences = []
    for name, value in expected.items():
        target = name.replace('.lora_A.weight', '.lora_A.default.weight').replace('.lora_B.weight', '.lora_B.default.weight')
        if target not in actual:
            raise ValueError('Saved adapter tensor was not injected: ' + name)
        loaded = actual[target].detach().cpu().float()
        if loaded.shape != value.shape or not torch.isfinite(loaded).all():
            raise ValueError('Invalid loaded adapter tensor: ' + name)
        differences.append(float((loaded-value.float()).abs().max()))
    result = dict(saved_tensors=len(expected), loaded_tensors=len(differences),
        maximum_absolute_weight_difference=max(differences), all_expected_tensors_loaded=True)
    if result['maximum_absolute_weight_difference'] != 0:
        raise ValueError('Loaded adapter values differ from the supplied safetensors')
    immutable(RUN / 'loaded_adapter_verification.json', result)
    print('Verified exact injection of all ' + str(len(expected)) + ' supplied adapter tensors.', flush=True)


def generate(tag, limit=0, gpu_embedding=False, batch_size=1):
    import torch
    import model as model_loader
    if gpu_embedding:
        # The frozen training helper offloads a 5.6-GB lookup table for long
        # training sequences. These fixed short evaluation windows fit with the
        # identical BF16 lookup weights resident on the 24-GB GPU instead.
        model_loader.offload_ple = lambda model: None
    load_model, load_processor = model_loader.load_model, model_loader.load_processor
    study, source, rows, episodes = context()
    plan = common.read(RUN / 'evaluation_plan.json')
    if (index_hash() != plan['records_sha256'] or common.sha(RUN / 'received/adapter_model.safetensors') != plan['adapter_sha256'] or
            common.sha(RUN / 'received/adapter_config.json') != plan['adapter_config_sha256']):
        raise ValueError('Evaluation input changed')
    if limit:
        rows = rows[:limit]
    folder = RUN / 'predictions' / tag; folder.mkdir(parents=True, exist_ok=True)
    pending = [r for r in rows if not (folder / (r['id'] + '.json')).exists()]
    if not pending:
        print('All requested windows already present.', flush=True); return
    download_state = common.read(RUN / 'model_download.json')
    snapshot = download_state['snapshot']
    processor = load_processor(snapshot)
    processor.image_processor.max_soft_tokens = 70
    processor.tokenizer.padding_side = 'left'
    adapter = str(RUN / 'received') if tag == 'partner' else None
    if tag not in ('partner', 'base'):
        raise ValueError('Unknown model tag')
    model = load_model(base_id=snapshot, adapter_path=adapter).eval()
    if adapter:
        verify_loaded_adapter(model)
    runtime = dict(started_utc=now(), tag=tag, gpu=torch.cuda.get_device_name(),
        executing_code_sha256=common.sha(Path(__file__)),
        versions={name: importlib.metadata.version(name) for name in ['torch','transformers','peft','bitsandbytes','accelerate']},
        base_revision=REVISION, model_class=type(model).__name__,
        per_layer_embedding_device='cuda' if gpu_embedding else 'cpu',
        batch_size=batch_size,
        allocated_gpu_gib=torch.cuda.memory_allocated()/1024**3)
    transport.atomic_json(RUN / ('runtime_' + tag + '.json'), runtime)
    print(json.dumps(runtime), flush=True)
    started = time.monotonic()
    for offset in range(0, len(pending), batch_size):
        group = pending[offset:offset + batch_size]
        for row in group:
            destination = folder / (row['id'] + '.json')
            attempt = destination.with_suffix('.attempt.json')
            if attempt.exists():
                raise ValueError('An unfinished generation attempt needs inspection: ' + row['id'])
            immutable(attempt, dict(window=row['id'], tag=tag, started_utc=now(), batch_size=len(group)))
        t0 = time.monotonic(); torch.cuda.reset_peak_memory_stats()
        batch = native_inputs(processor, source, group).to('cuda')
        batch['pixel_values'] = batch['pixel_values'].to(torch.bfloat16)
        n_prompt = int(batch['input_ids'].shape[1])
        with torch.inference_mode():
            result = model.generate(**batch, max_new_tokens=768, do_sample=False)
        eos = model.generation_config.eos_token_id
        eos = [eos] if isinstance(eos, int) else eos or []
        batch_seconds = time.monotonic()-t0
        for index, row in enumerate(group):
            token_ids = result[index, n_prompt:].tolist()
            stop = next((i+1 for i,t in enumerate(token_ids) if t in eos),len(token_ids))
            token_ids = token_ids[:stop]; n_tokens = len(token_ids)
            text = processor.tokenizer.decode(token_ids, skip_special_tokens=True)
            hit_max = n_tokens >= 768 and token_ids[-1] not in eos
            rec = dict(id=row['id'], episode=row['episode'], core_start=row['core_start'], core_end=row['core_end'],
                tag=tag, text=text, hit_max=hit_max, error=None, n_prompt_tokens=int(batch['attention_mask'][index].sum()), n_tokens=n_tokens,
                seconds=batch_seconds/len(group), batch_seconds=batch_seconds, batch_size=len(group), peak_gpu_gib=torch.cuda.max_memory_allocated()/1024**3,
                user_input_sha256=hashlib.sha256(json.dumps(row['messages'][0],sort_keys=True).encode()).hexdigest())
            try:
                if hit_max:
                    raise ValueError('Generation reached token cap')
                recipe_data.parse_prediction(text,row['episode'],row['core_start'],row['core_end'])
                rec['strict_output_valid'] = True
            except ValueError as error:
                rec['strict_output_valid'] = False; rec['parse_error'] = str(error)
            immutable(folder / (row['id'] + '.json'), rec)
            (folder / (row['id'] + '.md')).write_text(text, encoding='utf-8')
            print(f"{offset+index+1}/{len(pending)} {row['id']} tokens={n_tokens} valid={rec['strict_output_valid']} amortized_seconds={rec['seconds']:.2f}", flush=True)
        del batch, result
        state = dict(tag=tag, complete=False, windows_written=len(list(folder.glob('*_binary.json'))),
            expected_windows=279, latest=row['id'], latest_valid=rec['strict_output_valid'],
            elapsed_seconds=time.monotonic()-started, updated_utc=now())
        transport.atomic_json(RUN / ('progress_' + tag + '.json'), state)
    state['complete'] = len(list(folder.glob('*_binary.json'))) == 279
    transport.atomic_json(RUN / ('progress_' + tag + '.json'), state)


def score():
    results = {}
    for tag in ['partner', 'base']:
        folder = RUN / 'predictions' / tag
        if folder.exists():
            results[tag] = scoring.score(EVIDENCE, predictions=folder)
    existing = REPO / 'outputs/oopsie_distillation_local_sequential_v1/predictions'
    for tag in ['base', 'binary', 'joint', 'categories_aux', 'evidence_aux']:
        folder = existing / tag
        if folder.exists():
            results['existing_qwen_' + tag] = scoring.score(EVIDENCE, predictions=folder)
    transport.atomic_json(RUN / 'results.json', results)
    scoring.write_report(RUN, results)
    print(json.dumps({k:dict(episodes=v['episodes'],valid_windows=v['valid_windows'],missing_windows=v['missing_windows'],metrics=v['metrics']) for k,v in results.items()},indent=2),flush=True)


def report():
    plan = common.read(RUN / 'evaluation_plan.json')
    results = common.read(RUN / 'results.json') if (RUN / 'results.json').exists() else {}
    verified = common.read(RUN / 'archive_verification.json')
    lines = ['# Partner Gemma adapter verification', '',
        f"The supplied archive passes ZIP CRC and safetensors checks: {verified['adapter_tensors']} finite tensors, {verified['adapter_parameters']:,} adapter parameters, all 258 LoRA B matrices nonzero.", '',
        'Its supplied training logs contain 900 examples over 450 distinct D-series episodes, disjoint from its 50 archived evaluation IDs. Those D-series episodes belong to the historical LIBERO export; they are not the real OopsieData validation split.', '',
        'The archived scores recompute to TP=17, FP=0, FN=15, TN=18: 70% episode-level failure agreement, 69.39% episode-level F1. Its reported mean failure-interval IoU is 12.59%. These describe different units; episode detection does not imply accurate failure timing. Raw archived predictions are absent, so the historical per-frame scores cannot be independently recomputed from this archive.', '',
        '## Real OopsieData evaluation', '',
        'Exactly the existing 50 development episodes, 279 windows and 8,132 scored source frames. The 32-frame cores, 8-frame contexts, native camera strips, task text, binary Markdown instruction and scoring match the existing Qwen evaluation. Every scored frame is counted once. Final test remains sealed. No teacher API calls or training.', '',
        'Gemma retains the declared 70 visual soft-token processor budget and original NF4/BF16 loading. Its training used atomic JSON plus synthetic telemetry/events; this evaluation tests transfer to the existing real-video binary-window protocol. No robot state or gripper events are invented. The original base revision was not supplied; the downloaded base is pinned to `' + REVISION + '`.', '',
        '| Model | Completed windows | Valid windows | Coverage | Frame agreement | Failure precision | Failure recall | Failure F1 | Failure IoU |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    pct = lambda value: 'N/A' if value is None else f'{100*value:.2f}%'
    for tag, result in results.items():
        m = result['metrics']
        values = [m[k] for k in ['coverage','strict_frame_agreement','failure_precision','failure_recall','failure_f1','failure_iou']]
        lines.append(f"| {tag} | {result['windows']-result['missing_windows']}/{result['windows']} | {result['valid_windows']} | " + ' | '.join(pct(v) for v in values) + ' |')
    lines += ['', 'These measure agreement with frozen Sol V8.1 teacher labels, not human-ground-truth accuracy. Missing/invalid outputs remain Unknown and reduce coverage and strict agreement. Incomplete runs must not be ranked as finished.', '',
        'Input format, training data, model architecture and visual tokenization differ between Gemma and the existing Qwen students; this is a common-data transfer evaluation, not a controlled architecture comparison.', '',
        '[Frozen input prompt](prompt.md) · [Window results](results.md) · [Video reviewer](review.html)', '']
    (RUN / 'report.md').write_text('\n'.join(lines), encoding='utf-8')


def review():
    import export_qwen_development_review as viewer
    import failure_enrichment_v8_1 as enrichment
    study, source, rows, episodes = context()
    template = viewer.make_template().replace('Qwen development comparison', 'Partner Gemma development comparison')
    # Metadata-only preloading can leave HAVE_METADATA with no decoded frame
    # after rapid navigation/reloads. The reviewer must show a playable frame.
    template = template.replace("video.preload='metadata'", "video.preload='auto'")
    template = template.replace('Frozen V8.1 prompt', 'Reference teacher prompt')
    template = template.replace('Five completed Qwen variants and the Sol reference on all 50 development episodes.',
        'Partner Gemma adapter and frozen Sol reference on the same 50 real OopsieData development episodes.')
    objects = []; snapshot_hashes = {}
    for eid in study['development_ids']:
        e = episodes[eid]
        native = source / 'traces' / (eid + '_sol_r01') / 'annotation.md'
        text = native.read_text(encoding='utf-8')
        truth = enrichment.parse(text, e)
        label_dir = RUN / 'review_labels' / eid; label_dir.mkdir(parents=True, exist_ok=True)
        (label_dir / 'sol_native.md').write_bytes(native.read_bytes())
        tracks = dict(sol=[dict(repeat=1, segments=truth['segments'], failure_annotations=truth['failure_annotations'],
            native_markdown=text, markdown=f'review_labels/{eid}/sol_native.md')])
        for tag in ['partner'] + (['base'] if (RUN / 'predictions/base').exists() else []):
            values = [None] * e['n_frames']; compilation = ['# Derived compilation of saved ' + tag + ' window responses', '',
                'Each window response below is unchanged native model output. Missing/invalid intervals remain Unknown.', '']
            available = False
            for row in (r for r in rows if r['episode'] == eid):
                path = RUN / 'predictions' / tag / (row['id'] + '.json')
                if not path.exists():
                    continue
                available = True
                saved = common.read(path); snapshot_hashes[str(path.relative_to(RUN))] = common.sha(path)
                try:
                    if saved['hit_max']:
                        raise ValueError('Generation reached token cap')
                    parsed = recipe_data.parse_prediction(saved['text'], eid, row['core_start'], row['core_end'])
                    for segment in parsed:
                        values[segment['start_frame']:segment['end_frame']] = [segment['failure']] * (segment['end_frame']-segment['start_frame'])
                except ValueError:
                    pass
                compilation += [f"## Scored core [{row['core_start']}, {row['core_end']})", '', saved['text'], '']
            segments = viewer.runs(values)
            compiled = '\n'.join(compilation)
            timeline = '# Derived stitched prediction timeline\n\n' + viewer.timeline(eid, segments)
            (label_dir / (tag + '_timeline.md')).write_text(timeline, encoding='utf-8')
            tracks[tag] = [dict(repeat=1, segments=segments, native_markdown=compiled,
                markdown=f'review_labels/{eid}/{tag}_timeline.md', markdown_is_derived=True)] if available else []
        videos = []
        for index, video in enumerate(e['videos']):
            target = RUN / 'media' / eid / f'camera_{index}.mp4'; target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                os.link(source / video['url'], target)
            videos.append(dict(video, url=target.relative_to(RUN).as_posix()))
        objects.append(dict(id=eid,task=e['task'],split=e['split'],lab=e['lab'],fps=e['fps'],n_frames=e['n_frames'],
            videos=videos,teachers=tracks,source_run=source.name))
    labels = dict(sol='Sol V8.1 reference', partner='Partner Gemma adapter')
    if (RUN / 'predictions/base').exists():
        labels['base'] = 'Gemma base (no adapter)'
    data = dict(protocol='partner_gemma4_development_review_v1',
        manifest_sha256=common.sha(RUN / 'evaluation_plan.json'), review_ui_version=hashlib.sha256(template.encode()).hexdigest(),
        prompt_revision='Partner Gemma development', side_labels=labels, side_repeats={k:1 for k in labels},
        planned_responses=50*len(labels), repeats=1, episodes=objects,
        rich_prompt_description='Real OopsieData development set. Gray intervals are missing/invalid student outputs. Sol is a teacher reference, not human ground truth.')
    encoded=json.dumps(data,ensure_ascii=False).replace('<','\\u003c').replace('\u2028','\\u2028').replace('\u2029','\\u2029')
    transport.atomic_json(RUN / 'review_data.json', data)
    (RUN / 'review.html').write_text(template.replace('__DATA__', encoded), encoding='utf-8')
    (RUN / 'prompt.md').write_bytes((source / 'prompt.md').read_bytes())
    transport.atomic_json(RUN / 'review_provenance.json',dict(source_prediction_sha256=snapshot_hashes,stitched_timelines_are_derived=True))
    print('Review published for all 50 development episodes.',flush=True)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('command', choices=['prepare','download','runtime','batch_check','generate','score','report','review'])
    ap.add_argument('--tag', default='partner', choices=['partner','base'])
    ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--gpu-embedding', action='store_true')
    ap.add_argument('--batch-size', type=int, default=1)
    args = ap.parse_args()
    if args.command == 'generate':
        generate(args.tag, args.limit, args.gpu_embedding, args.batch_size)
    else:
        globals()[args.command]()
