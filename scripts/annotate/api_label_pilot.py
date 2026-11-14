"""Prepare offline; run only after explicit approval of the printed manifest hash.

Fixed four-call development pilot. No retries, tools, reference scoring or training.
Uses stdlib HTTP so no SDK can silently retry a billed request.
"""
import argparse
import base64
import hashlib
import html
import json
from pathlib import Path
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'outputs/api_label_pilot_v1'
SOURCE = ROOT / 'gpt6_v3_12_episode_review_pack/episodes'
IDS = ('R001', 'R002')
MODELS = {'openai': 'gpt-6.1-sol', 'gemini': 'gemini-robotics-er-2-preview'}
MAX_INPUT = 80_000
MAX_OUTPUT = 4096
RESERVE_USD = 0.50
MAX_CALLS = 4
TAXONOMY = ['reaching', 'grasp', 'manipulation', 'sequencing_semantic',
            'collision', 'task_not_attempted', 'visible_hardware_issue', 'other']
PROMPT = '''Annotate this recorded robot episode using only the supplied evidence.
Identify progress and failure as INDEPENDENT interval labels; they may overlap.
Progress means observable advancement toward the language task, including a
productive approach or correction. Failure means an observable unsuccessful
attempt, task-inconsistent action, harmful side effect, or sustained unproductive
behavior. Lack of immediate progress alone does not establish failure. Successful
episodes can contain failures. A sensible correction can be progress before it
completes recovery. Do not infer perception/planning causes from behavior alone.

Failure types: reaching (pre-contact failure to reach; a barely missed grasp is
grasp), grasp (miss, improper grasp, slip or drop), manipulation (post-contact
failure to manipulate as intended), sequencing_semantic (wrong object/action or
order), collision, task_not_attempted (no discernible attempt, including sustained
stalling), visible_hardware_issue, other. Multiple types can coexist. A recording
ending alone is not a failure or evidence of a hardware fault.

Use separate progress and failure intervals. Merge continuous behavior within
each label; split when that behavior stops. A change of failure category alone
need not split an otherwise continuous failure interval: list applicable types.
Give a short observable description, evidence frame numbers, and uncertainty note.
Leave ambiguous intervals out of positive segments and record them in uncertain.
Do not invent recovery prescriptions, severity, resetability or terminal outcomes.
No neutral or recovery class. Omitted labels are NOT automatically negatives.

Images are chronological pairs: external camera then wrist camera, with frame
indices and telemetry preceding each pair. Source is 20 Hz, sampled every 5 frames
(4 Hz), plus the last frame. Brief events between samples may be missed. Do not
claim frame-exact boundaries; use supplied frame indices and note uncertainty.
Gripper command/finger position do not prove contact or possession. Commands at
frame t follow observation t. Do not equate a close command with a grasp.

Return ONLY one JSON object with exactly these keys:
episode_id: supplied ID
segments: array of objects with exactly:
  label: "progress" or "failure"
  start_frame: integer, inclusive, a supplied frame
  end_frame_exclusive: integer, a supplied frame or episode n_frames
  failure_types: array of allowed types (empty for progress, nonempty for failure)
  description: concise observable account
  evidence_frames: nonempty array of supplied frame indices within the interval
  uncertainty: string (empty if none)
uncertain: array of objects with exactly start_frame, end_frame_exclusive,
  labels (nonempty subset of ["progress", "failure"]), reason (nonempty string)
notes: string describing limitations of your annotation
Within each label, positive intervals must not overlap. Progress and failure may
overlap each other. Uncertain intervals for a label must not overlap positives
for that label. All intervals are half-open [start_frame,end_frame_exclusive).
Use empty arrays if no supported positive or uncertain intervals are identified.
'''


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def plan_settings():
    return {'models': MODELS, 'max_input_tokens': MAX_INPUT,
            'max_output_tokens': MAX_OUTPUT, 'max_generation_attempts': MAX_CALLS,
            'reservation_per_attempt_usd': RESERVE_USD, 'total_reserved_usd': 2.0,
            'openai_reasoning': 'low', 'gemini_thinking': 'low',
            'openai_image_detail': 'high', 'retries': 0, 'sample_stride': 5,
            'price_date': '2026-10-01', 'price_valid_until': '2026-12-31',
            'standard_input_output_usd_per_million': {'openai': [2, 10], 'gemini': [1, 5]}}


def prepare():
    import numpy as np
    from PIL import Image
    if OUT.exists():
        raise ValueError('Pilot folder already exists; use inspect. Do not overwrite frozen inputs.')
    OUT.mkdir(parents=True)
    (OUT / 'prompt.txt').write_text(PROMPT, encoding='utf-8')
    episodes = []
    for eid in IDS:
        src = SOURCE / eid
        obs = load(src / 'observable.json')
        n = obs['n_frames']
        if obs['fps'] != 20 or n < 2:
            raise ValueError('Unsupported source FPS/length')
        frames = sorted(set(range(0, n, 5)) | {n - 1})
        if len(frames) > 80:
            raise ValueError('Too many sampled frames for this fixed pilot')
        epdir = OUT / eid
        epdir.mkdir()
        telemetry = {r['frame']: r for r in obs['telemetry']}
        rows = []
        with np.load(src / 'cameras.npz', allow_pickle=False) as cameras:
            for camera in ('agent', 'wrist'):
                if cameras[camera].shape != (n, 256, 256, 3):
                    raise ValueError('Unexpected camera dimensions')
            for frame in frames:
                # Deliberate allowlist: never include outcomes, previous labels or simulator facts.
                row = {'frame': frame, 'seconds': frame / 20,
                       'eef_xyz_m': telemetry[frame]['eef_xyz_m'],
                       'finger_qpos_m': telemetry[frame]['finger_qpos_m'],
                       'gripper_command': telemetry[frame]['gripper_command']}
                rows.append(row)
                for camera in ('agent', 'wrist'):
                    Image.fromarray(cameras[camera][frame]).save(
                        epdir / f'{frame:04d}_{camera}.jpg', quality=90)
        episode = {'id': eid, 'task': obs['task'], 'n_frames': n, 'fps': 20,
                   'sampled_frames': frames, 'telemetry': rows}
        write_json(epdir / 'input.json', episode)
        episodes.append({k: episode[k] for k in ('id', 'task', 'n_frames', 'fps', 'sampled_frames')} |
                        {'source_sha256': {name: digest(src / name) for name in ('cameras.npz', 'observable.json')}})
    files = {p.relative_to(OUT).as_posix(): digest(p) for p in sorted(OUT.rglob('*')) if p.is_file()}
    manifest = {'version': 1, 'purpose': 'Development workflow pilot; no accuracy claim',
                'selection': 'First two IDs in existing review pack; no selection on outcomes',
                'settings': plan_settings(), 'episodes': episodes, 'files': files,
                'runner_sha256': digest(__file__)}
    write_json(OUT / 'manifest.json', manifest)
    render_preview(manifest)
    inspect()


def render_preview(manifest):
    parts = ['<!doctype html><meta charset="utf-8"><title>Annotation pilot inputs</title>',
             '<style>body{font:16px sans-serif;max-width:1100px;margin:auto} '
             'figure{display:inline-block;margin:8px} img{width:256px} pre{white-space:pre-wrap}</style>',
             '<h1>Progress / failure annotation pilot — prepared, not run</h1>',
             '<p>Two development episodes, sampled at 4 Hz. No reference labels or scores.</p>',
             '<p><a href="manifest.json">Frozen manifest</a> · <a href="prompt.txt">Exact prompt</a></p>']
    for ep in manifest['episodes']:
        eid = ep['id']
        parts.append(f'<h2>{eid}: {html.escape(ep["task"])}</h2>')
        parts.append(f'<p>{ep["n_frames"]} source frames; {len(ep["sampled_frames"])} sampled pairs.</p>')
        for frame in ep['sampled_frames']:
            parts.append(f'<figure><figcaption>Frame {frame} ({frame/20:.2f}s): external / wrist</figcaption>')
            for camera in ('agent', 'wrist'):
                parts.append(f'<img loading="lazy" src="{eid}/{frame:04d}_{camera}.jpg">')
            parts.append('</figure>')
    (OUT / 'index.html').write_text('\n'.join(parts), encoding='utf-8')


def verify():
    m = load(OUT / 'manifest.json')
    if m['settings'] != plan_settings() or m['runner_sha256'] != digest(__file__):
        raise ValueError('Runner/settings changed after freeze; prepare a newly reviewed experiment')
    if [ep['id'] for ep in m['episodes']] != list(IDS):
        raise ValueError('Unexpected episode list')
    for relative, expected in m['files'].items():
        p = (OUT / relative).resolve()
        if not p.is_relative_to(OUT.resolve()) or digest(p) != expected:
            raise ValueError('Frozen input integrity check failed')
    return m


def inspect():
    m = verify()
    print(json.dumps({'manifest_sha256': digest(OUT / 'manifest.json'),
                      'settings': m['settings'],
                      'episodes': [{k: v for k, v in ep.items() if k != 'sampled_frames'} |
                                   {'sampled_pairs': len(ep['sampled_frames'])} for ep in m['episodes']],
                      'requests_sent': len(list((OUT / 'attempts').glob('*.json')))}, indent=2))


def build_payload(provider, ep):
    text = (OUT / 'prompt.txt').read_text(encoding='utf-8') + '\n' + json.dumps(
        {k: ep[k] for k in ('id', 'task', 'n_frames', 'fps')})
    if len(text.encode()) > 20_000 or len(ep['sampled_frames']) > 80:
        raise ValueError('Oversized input')
    parts = [{'type': 'input_text', 'text': text}] if provider == 'openai' else [{'text': text}]
    for row in ep['telemetry']:
        caption = json.dumps(row) + '; next two images: external, wrist'
        parts.append({'type': 'input_text', 'text': caption} if provider == 'openai' else {'text': caption})
        for camera in ('agent', 'wrist'):
            data = base64.b64encode((OUT / ep['id'] / f'{row["frame"]:04d}_{camera}.jpg').read_bytes()).decode()
            parts.append({'type': 'input_image', 'detail': 'high', 'image_url': 'data:image/jpeg;base64,' + data}
                         if provider == 'openai' else {'inlineData': {'mimeType': 'image/jpeg', 'data': data}})
    if provider == 'openai':
        return {'model': MODELS[provider], 'input': [{'role': 'user', 'content': parts}],
                'reasoning': {'effort': 'low'}, 'max_output_tokens': MAX_OUTPUT,
                'text': {'format': {'type': 'json_object'}}, 'store': False,
                'service_tier': 'default', 'truncation': 'disabled'}
    return {'contents': [{'role': 'user', 'parts': parts}],
            'generationConfig': {'maxOutputTokens': MAX_OUTPUT,
                                 'thinkingConfig': {'thinkingLevel': 'low'},
                                 'responseMimeType': 'application/json'}}


def credentials():
    # Values never appear in logs, files, command-line arguments or exception text.
    values = []
    for line in (ROOT / '.env').read_text(encoding='utf-8-sig').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if line.startswith('export '):
            line = line[7:].strip()
        if '=' in line:
            line = line.split('=', 1)[1].strip()
        values.append(line.split(' #', 1)[0].strip().strip('\"\''))
    if len(values) != 2 or not all(values):
        raise ValueError('Expected two .env credentials, OpenAI then Gemini')
    return dict(zip(MODELS, values))


def post(url, key, provider, payload):
    header = {'Authorization': 'Bearer ' + key} if provider == 'openai' else {'x-goog-api-key': key}
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={'Content-Type': 'application/json', **header}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f'{provider} HTTP {e.code}; no retry, reservation retained') from None
    except Exception as e:
        raise RuntimeError(f'{provider} {type(e).__name__}; no retry, reservation retained') from None


def reserve(path, provider, eid):
    if provider not in MODELS or eid not in IDS:
        raise ValueError('Not an approved provider/episode')
    path.mkdir(exist_ok=True)
    allowed = {f'{p}_{e}.json' for p in MODELS for e in IDS}
    existing = list(path.glob('*.json'))
    if any(p.name not in allowed for p in existing) or len(existing) >= MAX_CALLS:
        raise ValueError('Pilot call budget exhausted or ledger invalid')
    slot = path / f'{provider}_{eid}.json'
    # Exclusive creation before ANY request. A timeout or crash never releases this slot.
    with slot.open('x', encoding='utf-8') as f:
        json.dump({'provider': provider, 'episode': eid, 'reserved_usd': RESERVE_USD,
                   'status': 'reserved', 'time': time.time()}, f)
    return slot


def validate(value, ep):
    if set(value) != {'episode_id', 'segments', 'uncertain', 'notes'} or value['episode_id'] != ep['id']:
        raise ValueError('Invalid annotation envelope')
    if not isinstance(value['notes'], str) or not isinstance(value['segments'], list) or not isinstance(value['uncertain'], list):
        raise ValueError('Invalid annotation types')
    starts = set(ep['sampled_frames'])
    ends = starts | {ep['n_frames']}
    intervals = {'progress': [], 'failure': []}
    for seg in value['segments']:
        if set(seg) != {'label', 'start_frame', 'end_frame_exclusive', 'failure_types', 'description', 'evidence_frames', 'uncertainty'}:
            raise ValueError('Invalid segment fields')
        label, a, b = seg['label'], seg['start_frame'], seg['end_frame_exclusive']
        if label not in intervals or type(a) is not int or type(b) is not int or a not in starts or b not in ends or a >= b:
            raise ValueError('Invalid segment bounds/label')
        ft = seg['failure_types']
        if not isinstance(ft, list) or any(x not in TAXONOMY for x in ft) or len(set(ft)) != len(ft) or bool(ft) != (label == 'failure'):
            raise ValueError('Invalid failure taxonomy')
        if not isinstance(seg['description'], str) or not seg['description'].strip() or not isinstance(seg['uncertainty'], str):
            raise ValueError('Invalid evidence description')
        evidence = seg['evidence_frames']
        if not isinstance(evidence, list) or not evidence or any(type(f) is not int or f not in starts or not a <= f < b for f in evidence):
            raise ValueError('Invalid evidence frames')
        intervals[label].append((a, b))
    for spans in intervals.values():
        spans.sort()
        if any(right[0] < left[1] for left, right in zip(spans, spans[1:])):
            raise ValueError('Positive intervals overlap within one label')
    for u in value['uncertain']:
        if set(u) != {'start_frame', 'end_frame_exclusive', 'labels', 'reason'}:
            raise ValueError('Invalid uncertainty fields')
        a, b = u['start_frame'], u['end_frame_exclusive']
        if type(a) is not int or type(b) is not int or a not in starts or b not in ends or a >= b:
            raise ValueError('Invalid uncertainty bounds')
        if not isinstance(u['labels'], list) or not u['labels'] or any(k not in intervals for k in u['labels']) or not isinstance(u['reason'], str) or not u['reason'].strip():
            raise ValueError('Invalid uncertainty labels/reason')
        if any(a < y and x < b for k in u['labels'] for x, y in intervals[k]):
            raise ValueError('Unknown and positive overlap for same label')


def run(approval):
    from datetime import date
    m = verify()
    if approval != digest(OUT / 'manifest.json'):
        raise ValueError('Explicit approval must match the exact manifest SHA256')
    if date.today() > date(2026, 12, 31):
        raise ValueError('Pricing expired; re-review budget before running')
    lock = OUT / 'run.lock'
    # Persistent lock: even an interrupted run cannot silently launch again.
    with lock.open('x') as f:
        f.write(approval)
    keys = credentials()
    results = []
    for epmeta in m['episodes']:
        ep = load(OUT / epmeta['id'] / 'input.json')
        for provider in MODELS:
            slot = reserve(OUT / 'attempts', provider, ep['id'])
            record = load(slot)
            try:
                payload = build_payload(provider, ep)
                if provider == 'openai':
                    base = 'https://api.openai.com/v1/responses'
                    count_payload = {k: payload[k] for k in ('model', 'input', 'reasoning', 'text', 'truncation')}
                    counted = post(base + '/input_tokens', keys[provider], provider, count_payload)
                    tokens = counted['input_tokens']
                else:
                    base = 'https://generativelanguage.googleapis.com/v1beta/models/' + MODELS[provider]
                    counted = post(base + ':countTokens', keys[provider], provider, {'contents': payload['contents']})
                    tokens = counted['totalTokens']
                record['counted_input_tokens'] = tokens
                write_json(slot, record)
                if type(tokens) is not int or not 0 < tokens <= MAX_INPUT:
                    raise ValueError('Input token ceiling exceeded; generation blocked')
                data = post(base if provider == 'openai' else base + ':generateContent', keys[provider], provider, payload)
                result_path = OUT / f'{provider}_{ep["id"]}_response.json'
                serialized = json.dumps(data)
                for key in keys.values():
                    serialized = serialized.replace(key, '[REDACTED]')
                data = json.loads(serialized)
                write_json(result_path, data)
                if provider == 'openai':
                    record['usage'] = data.get('usage')
                    if data.get('status') != 'completed':
                        raise ValueError('Incomplete OpenAI response; no repair/retry')
                    answer = ''.join(c.get('text', '') for item in data.get('output', []) for c in item.get('content', []) if c.get('type') == 'output_text')
                else:
                    record['usage'] = data.get('usageMetadata')
                    candidates = data.get('candidates', [])
                    if len(candidates) != 1 or candidates[0].get('finishReason') != 'STOP':
                        raise ValueError('Incomplete Gemini response; no repair/retry')
                    answer = ''.join(p.get('text', '') for p in candidates[0]['content']['parts'] if not p.get('thought'))
                annotation = json.loads(answer)
                validate(annotation, ep)
                write_json(OUT / f'{provider}_{ep["id"]}_annotation.json', annotation)
                record['status'] = 'validated'
                results.append({'provider': provider, 'episode': ep['id'], 'annotation': annotation})
            except Exception as e:
                record['status'] = 'stopped'
                record['error_type'] = type(e).__name__
                write_json(slot, record)
                raise RuntimeError(f'Pilot stopped at {provider}/{ep["id"]}; inspect saved result. No retry.') from None
            write_json(slot, record)
            print(f'{provider}/{ep["id"]}: validated', flush=True)
    report = '<!doctype html><meta charset="utf-8"><title>Pilot annotations</title><h1>Candidate annotations — human review required</h1><p><a href="index.html">Camera evidence</a></p>'
    for r in results:
        report += '<h2>' + html.escape(r['provider'] + ' / ' + r['episode']) + '</h2><pre>' + html.escape(json.dumps(r['annotation'], indent=2)) + '</pre>'
    (OUT / 'results.html').write_text(report, encoding='utf-8')
    print('Complete: four attempts maximum; no scores against simulator references.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['prepare', 'inspect', 'run'], nargs='?', default='inspect')
    parser.add_argument('--approve-manifest-sha256', default='')
    args = parser.parse_args()
    try:
        if args.command == 'prepare':
            prepare()
        elif args.command == 'inspect':
            inspect()
        else:
            run(args.approve_manifest_sha256)
    except Exception as e:
        # Never expose arbitrary exception payloads (which may originate in credentials/HTTP).
        print(f'STOPPED: {type(e).__name__}. No automatic retries. Inspect local plan/ledger.')
        raise SystemExit(1) from None


if __name__ == '__main__':
    main()
