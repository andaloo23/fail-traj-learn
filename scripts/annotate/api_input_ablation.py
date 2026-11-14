"""Offline preparation and approval-gated input-reduction screen. No implicit retries."""
import argparse
import base64
from datetime import date
import html
import json
from pathlib import Path
import time

import api_label_pilot as common

ROOT = common.ROOT
OUT = ROOT / 'outputs/api_input_ablation_v3'
IDS = ('R001', 'R002', 'R003', 'R004')
ARMS = {
    'baseline': {'stride': 5, 'size': 256, 'kind': 'images', 'providers': ['openai', 'gemini']},
    'sparse': {'stride': 20, 'size': 256, 'kind': 'images', 'providers': ['openai', 'gemini']},
    'small': {'stride': 5, 'size': 128, 'kind': 'images', 'providers': ['openai', 'gemini']},
    'video': {'stride': 5, 'size': 256, 'kind': 'video', 'providers': ['gemini']},
}
MAX_INPUT = 40_000
MAX_OUTPUT = 4096
RESERVE = {'openai': 0.22, 'gemini': 0.12}
CAP = {'openai': 2.64, 'gemini': 1.92}
PROMPT_PATH = ROOT / 'scripts/annotate/prompts/progress_failure.md'


def jobs():
    return [{'id': f'{eid}_{arm}_{provider}', 'episode': eid, 'arm': arm,
             'provider': provider, 'reserved_usd': RESERVE[provider]}
            for eid in IDS for arm, spec in ARMS.items() for provider in spec['providers']]


def settings():
    return {'models': common.MODELS, 'arms': ARMS, 'ids': IDS,
            'max_input_tokens': MAX_INPUT, 'max_output_tokens': MAX_OUTPUT,
            'reasoning': 'low', 'retries': 0, 'tools': False, 'annotation_format': 'markdown',
            'provider_caps_usd': CAP, 'total_reserved_usd': 4.56,
            'price_valid_until': '2026-12-31',
            'rates_per_million': {'openai': [2, 10], 'gemini': [1, 5]}}


def file_hashes():
    return {name: common.digest(ROOT / 'scripts/annotate' / name)
            for name in ('api_input_ablation.py', 'api_label_pilot.py', 'prompts/progress_failure.md')}


def frame_indices(n, stride):
    return sorted(set(range(0, n, stride)) | {n - 1})


def episode_context(ep, spec):
    """Model-visible metadata and robot measurements as Markdown, not JSON text."""
    lines = [f'# Episode {ep["id"]}', '', f'Task: {ep["task"]}', '',
             f'Source: {ep["n_frames"]} frames at {ep["fps"]} FPS.',
             f'Visual input: {spec["kind"]}, {spec["size"]} x {spec["size"]} pixels per camera, '
             f'{20 / spec["stride"]:g} FPS requested.', '']
    if spec['kind'] == 'images':
        lines.append('Supplied image frames: ' + ', '.join(map(str, frame_indices(ep['n_frames'], spec['stride']))) + '.')
    else:
        lines.append('Two synchronized videos, external then wrist. Both start at source frame 0. '
                     'Source frame = round(seconds * 20). Provider-sampled frames are not exposed; '
                     'acknowledge timing uncertainty.')
    lines += ['', '## Ordinary robot telemetry', '',
              'Identical telemetry across conditions: 4 FPS plus the final frame. Coordinates are in meters.', '',
              '| Source frame | Seconds | End-effector XYZ | Finger positions | Gripper command |',
              '|---:|---:|---|---|---|']
    for row in ep['telemetry']:
        xyz = ', '.join(map(str, row['eef_xyz_m']))
        fingers = ', '.join(map(str, row['finger_qpos_m']))
        lines.append(f'| {row["frame"]} | {row["seconds"]} | {xyz} | {fingers} | {row["gripper_command"]} |')
    return '\n'.join(lines) + '\n'


def prepare():
    import numpy as np
    from PIL import Image
    import imageio_ffmpeg
    if OUT.exists():
        raise ValueError('Existing frozen pack; inspect instead')
    OUT.mkdir(parents=True)
    (OUT / 'prompt.md').write_bytes(PROMPT_PATH.read_bytes())
    episodes = []
    for eid in IDS:
        src = common.SOURCE / eid
        obs = common.load(src / 'observable.json')
        n = obs['n_frames']
        if obs['fps'] != 20 or not 2 <= n <= 300:
            raise ValueError('Unsupported source')
        with np.load(src / 'cameras.npz', allow_pickle=False) as arrays:
            cameras = {key: arrays[key] for key in ('agent', 'wrist')}
        if any(a.shape != (n, 256, 256, 3) or a.dtype != np.uint8 for a in cameras.values()):
            raise ValueError('Unexpected camera dimensions/type')
        epdir = OUT / eid
        epdir.mkdir()
        lookup = {r['frame']: r for r in obs['telemetry']}
        frames = frame_indices(n, 5)
        telemetry = [{'frame': f, 'seconds': f / 20,
                      'eef_xyz_m': lookup[f]['eef_xyz_m'],
                      'finger_qpos_m': lookup[f]['finger_qpos_m'],
                      'gripper_command': lookup[f]['gripper_command']} for f in frames]
        meta = {'id': eid, 'task': obs['task'], 'n_frames': n, 'fps': 20,
                'telemetry': telemetry, 'telemetry_fps': 4,
                'source_sha256': {name: common.digest(src / name) for name in ('cameras.npz', 'observable.json')}}
        common.write_json(epdir / 'input.json', meta)
        episodes.append({k: v for k, v in meta.items() if k != 'telemetry'})
        for arm, spec in ARMS.items():
            dest = epdir / arm
            dest.mkdir()
            (dest / 'context.md').write_text(episode_context(meta, spec), encoding='utf-8')
            selected = frame_indices(n, spec['stride'])
            if spec['kind'] == 'images':
                for f in selected:
                    for camera, array in cameras.items():
                        image = Image.fromarray(array[f])
                        if spec['size'] != 256:
                            image = image.resize((spec['size'], spec['size']), Image.Resampling.LANCZOS)
                        image.save(dest / f'{f:04d}_{camera}.jpg', quality=90)
            else:
                # Same two views, separate compressed videos, original source timebase.
                # Codec/decoding/sampling differ from image transport: exploratory arm.
                for camera, array in cameras.items():
                    encoder = imageio_ffmpeg.write_frames(str(dest / f'{camera}.mp4'), (256, 256),
                        fps=20, codec='libx264', pix_fmt_out='yuv420p',
                        output_params=['-crf', '18'], ffmpeg_log_level='error')
                    encoder.send(None)
                    for frame in array:
                        encoder.send(frame)
                    encoder.close()
                if sum(p.stat().st_size for p in dest.glob('*.mp4')) > 10_000_000:
                    raise ValueError('Native video exceeds inline request allowance')
    manifest = {'version': 1, 'settings': settings(), 'episodes': episodes,
                'jobs': jobs(), 'code_sha256': file_hashes(),
                'selection': 'First four development review-pack IDs; no outcomes consulted',
                'files': {p.relative_to(OUT).as_posix(): common.digest(p)
                          for p in sorted(OUT.rglob('*')) if p.is_file()}}
    common.write_json(OUT / 'manifest.json', manifest)
    preview(manifest)
    inspect()


def verify():
    m = common.load(OUT / 'manifest.json')
    if m['settings'] != json.loads(json.dumps(settings())) or m['jobs'] != jobs() or m['code_sha256'] != file_hashes():
        raise ValueError('Plan/code changed after freeze')
    for relative, expected in m['files'].items():
        p = (OUT / relative).resolve()
        if not p.is_relative_to(OUT.resolve()) or common.digest(p) != expected:
            raise ValueError('Frozen input changed')
    return m


def inspect():
    m = verify()
    print(json.dumps({'manifest_sha256': common.digest(OUT / 'manifest.json'),
                      'generation_jobs': len(m['jobs']), 'total_reserved_usd': 4.56,
                      'provider_caps_usd': CAP, 'episodes': [e['id'] for e in m['episodes']],
                      'attempts': len(list((OUT / 'attempts').glob('*.json')))}, indent=2))


def preview(m):
    parts = ['<!doctype html><meta charset="utf-8"><title>Input reduction pilot</title>',
             '<style>body{font:16px sans-serif;max-width:1200px;margin:auto} '
             'img{vertical-align:middle} table{border-collapse:collapse} td,th{padding:8px;border:1px solid #bbb}</style>',
             '<h1>Input reduction pilot — approval pending</h1><p>Four development episodes; 28 independent calls; $4.56 reserved maximum.</p>',
             '<p><a href="prompt.md">Common prompt</a> · <a href="manifest.json">Frozen manifest</a></p>',
             '<p>Telemetry stays identical at 4 Hz. Image size reduction may not reduce billed tokens. Video is an exploratory transport comparison.</p>']
    for ep in m['episodes']:
        eid = ep['id']
        parts.append(f'<h2>{eid}: {html.escape(ep["task"])}</h2>')
        parts.append('<table><tr><th>Frame</th><th>Baseline 256px / 4 Hz</th><th>Small 128px / 4 Hz</th><th>Sparse 256px / 1 Hz</th></tr>')
        for f in frame_indices(ep['n_frames'], 5):
            parts.append(f'<tr><td>{f}<br>{f/20:.2f}s</td>')
            for arm in ('baseline', 'small', 'sparse'):
                parts.append('<td>')
                if f in frame_indices(ep['n_frames'], ARMS[arm]['stride']):
                    for c in ('agent', 'wrist'):
                        parts.append(f'<img loading="lazy" src="{eid}/{arm}/{f:04d}_{c}.jpg">')
                parts.append('</td>')
            parts.append('</tr>')
        parts.append('</table><p>Native videos: external then wrist; API requested sampling 4 FPS.</p>')
        for c in ('agent', 'wrist'):
            parts.append(f'<video width="256" controls preload="none" src="{eid}/video/{c}.mp4"></video>')
    (OUT / 'index.html').write_text('\n'.join(parts), encoding='utf-8')


def payload(job):
    ep = common.load(OUT / job['episode'] / 'input.json')
    arm, provider = job['arm'], job['provider']
    spec = ARMS[arm]
    frames = frame_indices(ep['n_frames'], spec['stride'])
    text = ((OUT / 'prompt.md').read_text(encoding='utf-8') + '\n\n' +
            (OUT / ep['id'] / arm / 'context.md').read_text(encoding='utf-8'))
    if len(text.encode()) > 30_000:
        raise ValueError('Text allowance exceeded')
    def text_part(s):
        return {'type': 'input_text', 'text': s} if provider == 'openai' else {'text': s}
    parts = [text_part(text)]
    if spec['kind'] == 'images':
        for f in frames:
            parts.append(text_part(f'Source frame {f}, {f/20:.2f} seconds. External camera, then wrist camera:'))
            for camera in ('agent', 'wrist'):
                data = base64.b64encode((OUT / ep['id'] / arm / f'{f:04d}_{camera}.jpg').read_bytes()).decode()
                parts.append({'type': 'input_image', 'detail': 'high', 'image_url': 'data:image/jpeg;base64,' + data}
                             if provider == 'openai' else {'inlineData': {'mimeType': 'image/jpeg', 'data': data}})
    else:
        if provider != 'gemini':
            raise ValueError('Video arm is Gemini only')
        for camera in ('agent', 'wrist'):
            parts.append(text_part(camera + ' camera video; source FPS=20; starts at source frame 0'))
            data = base64.b64encode((OUT / ep['id'] / arm / f'{camera}.mp4').read_bytes()).decode()
            parts.append({'inlineData': {'mimeType': 'video/mp4', 'data': data}, 'videoMetadata': {'fps': 4}})
    if provider == 'openai':
        return {'model': common.MODELS[provider], 'input': [{'role': 'user', 'content': parts}],
                'reasoning': {'effort': 'low'}, 'max_output_tokens': MAX_OUTPUT,
                'store': False,
                'service_tier': 'default', 'truncation': 'disabled'}
    return {'contents': [{'role': 'user', 'parts': parts}],
            'generationConfig': {'maxOutputTokens': MAX_OUTPUT, 'thinkingConfig': {'thinkingLevel': 'low'}}}


def reserve(job):
    if job not in jobs():
        raise ValueError('Unapproved request')
    folder = OUT / 'attempts'
    folder.mkdir(exist_ok=True)
    old = [common.load(p) for p in folder.glob('*.json')]
    used = sum(r['reserved_usd'] for r in old if r['provider'] == job['provider'])
    if round(used + job['reserved_usd'], 2) > CAP[job['provider']] or len(old) >= 28:
        raise ValueError('Spending/call cap exhausted')
    path = folder / (job['id'] + '.json')
    with path.open('x', encoding='utf-8') as f:
        json.dump({**job, 'status': 'reserved', 'time': time.time()}, f)
    return path


def validate_markdown(answer):
    # This experiment evaluates prose annotations by human review, not JSON parsing.
    # Keep a minimal format check; do not silently repair or extract a second format.
    if not isinstance(answer, str) or not answer.strip():
        raise ValueError('Empty annotation')
    if answer.lstrip().startswith(('{', '[', '```')):
        raise ValueError('Expected an unfenced Markdown annotation')


def run(approval):
    m = verify()
    if approval != common.digest(OUT / 'manifest.json') or date.today() > date(2026, 12, 31):
        raise ValueError('Missing matching approval or expired price review')
    with (OUT / 'run.lock').open('x') as f:
        f.write(approval)
    keys = common.credentials()
    results = []
    for job in m['jobs']:
        record_path = reserve(job)
        record = common.load(record_path)
        provider = job['provider']
        try:
            body = payload(job)
            if provider == 'openai':
                url = 'https://api.openai.com/v1/responses'
                count_body = {k: body[k] for k in ('model', 'input', 'reasoning', 'truncation')}
                count = common.post(url + '/input_tokens', keys[provider], provider, count_body)['input_tokens']
            else:
                url = 'https://generativelanguage.googleapis.com/v1beta/models/' + common.MODELS[provider]
                count = common.post(url + ':countTokens', keys[provider], provider, {'contents': body['contents']})['totalTokens']
            record['counted_input_tokens'] = count
            common.write_json(record_path, record)
            if type(count) is not int or not 0 < count <= MAX_INPUT:
                raise ValueError('Input ceiling exceeded; generation blocked')
            raw = common.post(url if provider == 'openai' else url + ':generateContent', keys[provider], provider, body)
            clean = json.dumps(raw)
            for key in keys.values():
                clean = clean.replace(key, '[REDACTED]')
            raw = json.loads(clean)
            common.write_json(OUT / (job['id'] + '_response.json'), raw)
            if provider == 'openai':
                record['usage'] = raw.get('usage')
                if raw.get('status') != 'completed':
                    raise ValueError('Incomplete response')
                answer = ''.join(c.get('text', '') for item in raw.get('output', []) for c in item.get('content', []) if c.get('type') == 'output_text')
            else:
                record['usage'] = raw.get('usageMetadata')
                candidates = raw.get('candidates', [])
                if len(candidates) != 1 or candidates[0].get('finishReason') != 'STOP':
                    raise ValueError('Incomplete response')
                answer = ''.join(p.get('text', '') for p in candidates[0]['content']['parts'] if not p.get('thought'))
            (OUT / (job['id'] + '_annotation.md')).write_text(answer, encoding='utf-8')
            validate_markdown(answer)
            record['status'] = 'saved_for_human_review'
            results.append((job['id'], answer))
        except Exception as e:
            record['status'] = 'stopped'
            record['error_type'] = type(e).__name__
            common.write_json(record_path, record)
            raise RuntimeError('Stopped; no retry or budget release') from None
        common.write_json(record_path, record)
        print(job['id'] + ': Markdown saved for human review', flush=True)
    page = '<!doctype html><meta charset="utf-8"><title>Candidate annotations</title><h1>Input-reduction screen — human review required</h1><a href="index.html">Input comparison</a>'
    for name, value in results:
        page += '<h2><a href="' + html.escape(name) + '_annotation.md">' + html.escape(name) + '</a></h2><pre>' + html.escape(value) + '</pre>'
    (OUT / 'results.html').write_text(page, encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['prepare', 'inspect', 'run'], nargs='?', default='inspect')
    parser.add_argument('--approve-manifest-sha256', default='')
    args = parser.parse_args()
    try:
        if args.command == 'prepare': prepare()
        elif args.command == 'inspect': inspect()
        else: run(args.approve_manifest_sha256)
    except Exception as e:
        print(f'STOPPED: {type(e).__name__}. No automatic retry; inspect frozen plan/ledger.')
        raise SystemExit(1) from None


if __name__ == '__main__':
    main()
