"""Approved A-F frame-selection screen with persistent reservations and cost logs."""
import argparse
import base64
import csv
from datetime import date, datetime, timezone
import hashlib
import html
import json
import math
from pathlib import Path
import re
import shutil
import time
import threading
from functools import wraps

LEDGER_LOCK = threading.RLock()
STOP = threading.Event()

def serialized(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        with LEDGER_LOCK:
            return fn(*args, **kwargs)
    return wrapped

import urllib.error
import urllib.request

import api_label_pilot as common

ROOT = common.ROOT
SOURCE = ROOT / 'outputs/preprocessing_ablation_v3/holdout_source'
OUT = ROOT / 'outputs/h_pipeline_evaluation_v1'
IDS = tuple(f'H{i:03d}' for i in range(1,13))
MODELS = dict(common.MODELS)
PROVIDERS = {'U': 'openai', 'SP': 'gemini', 'P': 'openai', 'SW': 'gemini', 'W': 'openai'}
RESERVE = {'openai': .20, 'gemini': .12}
CAP = {'openai': 7.20, 'gemini': 2.88}
MAX_INPUT, MAX_OUTPUT = 40_000, 4096
PROMPTS = ('progress_failure.md', 'select_points.md', 'select_windows.md', 'annotate_frame_subset.md')
LABELS = {'U': 'GPT uniform', 'SP': 'Gemini point selector', 'P': 'GPT selected points',
          'SW': 'Gemini window selector', 'W': 'GPT selected windows'}



def jobs():
    return [{'id': f'{eid}_{arm}', 'episode': eid, 'arm': arm,
             'provider': PROVIDERS[arm], 'reserved_usd': RESERVE[PROVIDERS[arm]]}
            for eid in IDS for arm in PROVIDERS]


def settings():
    return {'models': MODELS, 'max_input_tokens': MAX_INPUT, 'max_output_tokens': MAX_OUTPUT,
            'reasoning': 'low', 'gemini_media_resolution': 'MEDIA_RESOLUTION_LOW', 'image_detail': 'high', 'annotation_format': 'markdown',
            'provider_caps_usd': CAP, 'maximum_reserved_usd': 10.08, 'retries': 0,
            'prompt_revision': 'point_window_v1', 'transport_timeout_seconds': 600, 'episode_workers': 2,
            'price_date': '2026-10-01', 'price_expiry': '2026-12-31',
            'rates_per_million': {'openai': {'input': 2, 'cached': .1, 'cache_write': 2.5, 'output': 10},
                                  'gemini': {'input': 1, 'cached': .1, 'output': 5}}}


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def atomic_json(path, value):
    temp = path.with_suffix(path.suffix + '.tmp')
    common.write_json(temp, value)
    temp.replace(path)


def pool_and_budget(n):
    pool = sorted(set(range(0, n, 5)) | {n - 1})
    k = math.ceil(len(pool) / 4)
    uniform = [pool[math.floor(i * (len(pool) - 1) / (k - 1) + .5)] for i in range(k)]
    anchors = [uniform[i] for i in (0, (k - 1) // 3, 2 * (k - 1) // 3, k - 1)]
    return pool, k, uniform, anchors


def context(ep, frames, selector=False):
    lines = [f'# Episode {ep["id"]}', '', f'Task: {ep["task"]}', '',
             f'Source: {ep["n_frames"]} frames at {ep["fps"]} FPS.',
             'Visual input: chronological synchronized external/wrist camera pairs, 256 x 256 pixels per camera.',
             'Supplied source frames: ' + ', '.join(map(str, frames)) + '.', '']
    if selector:
        lines += ['Already retained overview frames for GPT: ' + ', '.join(map(str, ep['overview'])) + '.',
                  'These fixed overview frames need not be in your candidate images; do not infer their contents.',
                  f"Additional point count: {ep['point_count']}.",
                  f"Window count: {ep['window_count']}; each spans 10 frame steps (0.5 seconds), inclusive endpoints.",
                  f"Pairs sampled per window: {ep['pairs_per_window']}.",
                  'Allowed window starts: ' + ', '.join(map(str, ep['allowed_window_starts'])) + '.', '']
    lines += ['## Ordinary robot telemetry', '',
              'Coordinates in meters. Telemetry sampled at 4 FPS plus the final source frame.', '',
              '| Frame | Seconds | End-effector XYZ | Finger positions | Gripper command |',
              '|---:|---:|---|---|---|']
    for r in ep['telemetry']:
        lines.append(f'| {r["frame"]} | {r["seconds"]} | ' + ', '.join(map(str, r['eef_xyz_m'])) +
                     ' | ' + ', '.join(map(str, r['finger_qpos_m'])) + f' | {r["gripper_command"]} |')
    return '\n'.join(lines) + '\n'


def code_hashes():
    return {name: common.digest(ROOT / 'scripts/annotate' / name)
            for name in ('api_h_pipeline_evaluation_v1.py', 'api_label_pilot.py')}


def prepare():
    import api_frame_selection_windows_v1 as prior
    prior.verify()
    if OUT.exists(): raise ValueError('Existing pack: do not overwrite')
    OUT.mkdir()
    import numpy as np
    from PIL import Image
    episodes=[]
    for eid in IDS:
        source=SOURCE/eid
        observation=common.load(source/'observable.json')
        n=observation['n_frames'];fps=observation['fps']
        if fps!=20:raise ValueError('Expected 20 FPS')
        pool=sorted(set(range(0,n,5))|{n-1})
        telemetry=[]
        for frame in pool:
            row=observation['telemetry'][frame]
            if row['frame']!=frame:raise ValueError('Telemetry index mismatch')
            telemetry.append({'frame':frame,'seconds':round(frame/fps,3),
                              'eef_xyz_m':row['eef_xyz_m'],'finger_qpos_m':row['finger_qpos_m'],
                              'gripper_command':row['gripper_command']})
        short=n<=150
        ep={'id':eid,'task':observation['task'],'n_frames':n,'fps':fps,'pool':pool,'telemetry':telemetry,
            'budget':12 if short else 24,
            'source_sha256':{name:common.digest(source/name) for name in ('cameras.npz','observable.json')}}
        ep['uniform']=evenly(list(range(n)),ep['budget'])
        ep['overview']=evenly(ep['uniform'],4 if short else 6)
        ep['window_count']=2 if short else 3
        ep['pairs_per_window']=4 if short else 6
        ep['point_count']=ep['budget']-len(ep['overview'])
        ep['allowed_window_starts']=[f for f in pool if f+10<n]
        ep['anchors']=ep['overview'];ep['k']=ep['budget']
        folder=OUT/eid/'images';folder.mkdir(parents=True)
        with np.load(source/'cameras.npz',allow_pickle=False) as archive:
            for camera in ('agent','wrist'):
                frames=archive[camera]
                if len(frames)!=n:raise ValueError('Camera length mismatch')
                for i,frame in enumerate(frames):Image.fromarray(frame).save(folder/f'{i:04d}_{camera}.jpg',quality=90)
        common.write_json(OUT/eid/'input.json',ep);episodes.append(ep)
    (OUT/'prompts').mkdir()
    for name in PROMPTS:shutil.copyfile(prior.OUT/'prompts'/name,OUT/'prompts'/name)
    baseline=common.load(prior.OUT/'cost_summary.json');cumulative=baseline['cumulative_with_baseline']
    common.write_json(OUT/'baseline_costs.json',{
        'generation_estimate_usd':cumulative['known_generation_estimate_usd'],
        'preflight_input_rate_allowance_usd':cumulative['preflight_allowance_usd'],
        'unknown_cost_requests':baseline['unknown_cost_requests']+cumulative['baseline_unknown_requests'],
        'unknown_full_reservations_usd':cumulative['unknown_full_reservations_usd']})
    manifest={'version':'h_windows_v1','settings':settings(),'episodes':episodes,'jobs':jobs(),
              'revision':'Blinded U/P/W labeling of all twelve H episodes; same prompts and frame-selection rules.',
              'limitations':'H has exclusive legacy labels; both-axis truth unavailable. Previously used in historical few-shot development.',
              'user_authorization':'User explicitly requested the pipelines label H and evaluate against H human ground truth.',
              'code_sha256':code_hashes(),
              'files':{p.relative_to(OUT).as_posix():common.digest(p) for p in sorted(OUT.rglob('*')) if p.is_file()}}
    common.write_json(OUT/'manifest.json',manifest);report();inspect()


def verify():
    m = common.load(OUT / 'manifest.json')
    if m['settings'] != settings() or m['jobs'] != jobs() or m['code_sha256'] != code_hashes():
        raise ValueError('Frozen settings/code mismatch')
    for name, digest in m['files'].items():
        path = (OUT / name).resolve()
        if not path.is_relative_to(OUT.resolve()) or common.digest(path) != digest:
            raise ValueError('Input integrity check failed')
    return m


def inspect():
    m = verify()
    print(json.dumps({'manifest_sha256': common.digest(OUT / 'manifest.json'),
                      'jobs': len(m['jobs']), 'max_reserved_usd': 10.08,
                      'provider_caps_usd': CAP,
                      'episodes': [{'id': e['id'], 'pairs': len(e['pool']), 'k': e['k'],
                                    'anchors': e['anchors']} for e in m['episodes']]}, indent=2))


def evenly(values, k):
    return [values[math.floor(i * (len(values) - 1) / (k - 1) + .5)] for i in range(k)]


def parse_selection(text, ep, arm):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if arm == 'SP':
        if lines[:2] != ['# Frame selection', '## Selected frames']:
            raise ValueError('Invalid point headings')
        if any(not re.fullmatch(r'[-*+] \d+', line) for line in lines[2:]):
            raise ValueError('Expected integer point bullets')
        points = [int(line[2:]) for line in lines[2:]]
        if len(points) != ep['point_count'] or points != sorted(set(points)):
            raise ValueError('Wrong point count/order/uniqueness')
        if not set(points) <= set(ep['pool']) - set(ep['overview']):
            raise ValueError('Points must be candidates excluding overview')
        return sorted(ep['overview'] + points), {'points': points}
    if lines[:2] != ['# Window selection', '## Selected windows']:
        raise ValueError('Invalid window headings')
    matches = [re.fullmatch(r'[-*+] \[(\d+),\s*(\d+)\]', line) for line in lines[2:]]
    if len(matches) != ep['window_count'] or not all(matches):
        raise ValueError('Wrong window count/format')
    windows = [(int(m[1]), int(m[2])) for m in matches]
    if windows != sorted(windows) or any(a not in ep['allowed_window_starts'] or b != a + 10 for a, b in windows):
        raise ValueError('Invalid window location/span')
    if any(windows[i][1] >= windows[i+1][0] for i in range(len(windows)-1)):
        raise ValueError('Overlapping windows are rejected')
    used = set(ep['overview'])
    expanded = []
    for start, end in windows:
        chosen = []
        for target in evenly(list(range(start, end + 1)), ep['pairs_per_window']):
            available = set(range(start, end + 1)) - used
            if not available:
                raise ValueError('Window has insufficient unique frames')
            frame = min(available, key=lambda f: (abs(f-target), f))
            chosen.append(frame)
            used.add(frame)
        expanded.append(sorted(chosen))
    if len(used) != ep['budget']:
        raise ValueError('Wrong final image budget')
    return sorted(used), {'windows': windows, 'window_frames': expanded}


def freeze_selection(ep, answer, arm):
    frames, details = parse_selection(answer, ep, arm)
    folder = OUT / ep['id'] / arm
    folder.mkdir()
    frozen = {'frames': frames, **details, 'selector_markdown_sha256': sha_bytes(answer.encode()),
              'image_sha256': {f'{f:04d}_{c}.jpg': common.digest(OUT / ep['id'] / 'images' / f'{f:04d}_{c}.jpg')
                               for f in frames for c in ('agent', 'wrist')}}
    common.write_json(folder / 'freeze.json', frozen)


def selected_frames(ep, arm):
    selector = {'P': 'SP', 'W': 'SW'}[arm]
    frozen = common.load(OUT / ep['id'] / selector / 'freeze.json')
    answer = (OUT / 'responses' / f'{ep["id"]}_{selector}.md').read_text(encoding='utf-8')
    frames, _ = parse_selection(answer, ep, selector)
    if frozen['selector_markdown_sha256'] != sha_bytes(answer.encode()) or frames != frozen['frames']:
        raise ValueError('Selection freeze mismatch')
    for name, digest in frozen['image_sha256'].items():
        if common.digest(OUT / ep['id'] / 'images' / name) != digest:
            raise ValueError('Selected image changed')
    return frames


def build_payload(job):
    ep = common.load(OUT / job['episode'] / 'input.json')
    arm, provider = job['arm'], job['provider']
    frames = selected_frames(ep, arm) if arm in ('P', 'W') else ep['uniform'] if arm == 'U' else ep['pool']
    prompts = OUT / 'prompts'
    if arm in ('SP', 'SW'):
        prompt = (prompts / ('select_points.md' if arm == 'SP' else 'select_windows.md')).read_text(encoding='utf-8')
    else:
        prompt = (prompts / 'progress_failure.md').read_text(encoding='utf-8')
        if arm in ('U', 'P', 'W'):
            prompt = (prompts / 'annotate_frame_subset.md').read_text(encoding='utf-8') + '\n\n' + prompt
    # Reconstruct from allowlisted metadata; never append selector prose to GPT input.
    text = prompt + '\n\n' + context(ep, frames, arm if arm in ('SP', 'SW') else False)
    if len(text.encode()) > 30_000 or len(frames) > 80:
        raise ValueError('Oversized local payload')
    parts = [{'type': 'input_text', 'text': text}] if provider == 'openai' else [{'text': text}]
    image_files = {}
    for f in frames:
        caption = f'Source frame {f}, {f / 20:.2f} seconds. External camera, then wrist camera:'
        parts.append({'type': 'input_text', 'text': caption} if provider == 'openai' else {'text': caption})
        for camera in ('agent', 'wrist'):
            folder = 'images'
            path = OUT / ep['id'] / folder / f'{f:04d}_{camera}.jpg'
            image_files[path.relative_to(OUT).as_posix()] = common.digest(path)
            encoded = base64.b64encode(path.read_bytes()).decode()
            parts.append({'type': 'input_image', 'detail': 'high', 'image_url': 'data:image/jpeg;base64,' + encoded}
                         if provider == 'openai' else {'inlineData': {'mimeType': 'image/jpeg', 'data': encoded}})
    if provider == 'openai':
        body = {'model': MODELS[provider], 'input': [{'role': 'user', 'content': parts}],
                'reasoning': {'effort': 'low'}, 'max_output_tokens': MAX_OUTPUT,
                'store': False, 'service_tier': 'default', 'truncation': 'disabled'}
    else:
        body = {'contents': [{'role': 'user', 'parts': parts}],
                'generationConfig': {'maxOutputTokens': MAX_OUTPUT, 'thinkingConfig': {'thinkingLevel': 'low'}, 'mediaResolution': 'MEDIA_RESOLUTION_LOW'}}
    evidence = {'frames': frames, 'image_sha256': image_files, 'prompt_sha256': sha_bytes(text.encode()),
                'payload_sha256': sha_bytes(json.dumps(body, sort_keys=True).encode()),
                'payload_bytes': len(json.dumps(body).encode())}
    return body, text, evidence


@serialized
def reserve(job):
    if job not in jobs():
        raise ValueError('Request not in approved matrix')
    folder = OUT / 'attempts'
    folder.mkdir(exist_ok=True)
    old = [common.load(p) for p in folder.glob('*.json')]
    if len(old) >= 60 or round(sum(r['reserved_usd'] for r in old) + job['reserved_usd'], 2) > 10.08:
        raise ValueError('Total budget exhausted')
    subtotal = sum(r['reserved_usd'] for r in old if r['provider'] == job['provider'])
    if round(subtotal + job['reserved_usd'], 2) > CAP[job['provider']]:
        raise ValueError('Provider budget exhausted')
    path = folder / (job['id'] + '.json')
    with path.open('x', encoding='utf-8') as f:
        json.dump({**job, 'status': 'reserved', 'started_utc': datetime.now(timezone.utc).isoformat(),
                   'generation_sent': False, 'generation_estimate_usd': None}, f)
    return path


def redact(text, keys):
    for key in keys.values():
        text = text.replace(key, '[REDACTED]')
    return re.sub(r'(?<![A-Za-z0-9])(?:sk-[A-Za-z0-9_-]{24,}|AIza[A-Za-z0-9_-]{24,})', '[REDACTED]', text)


def post(url, provider, payload, keys):
    auth = {'Authorization': 'Bearer ' + keys[provider]} if provider == 'openai' else {'x-goog-api-key': keys[provider]}
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={'Content-Type': 'application/json', **auth}, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=600) as response:
            return json.load(response)
    except urllib.error.HTTPError as e:
        try:
            error = json.loads(e.read()).get('error', {})
            message = str(error.get('message', ''))
        except Exception:
            message = 'Unparseable error body'
        raise RuntimeError(redact(f'{provider} HTTP {e.code}: {message}', keys)[:800]) from None
    except Exception as e:
        raise RuntimeError(f'{provider} {type(e).__name__}; no retry') from None


def usage_cost(provider, raw):
    if provider == 'openai':
        u = raw['usage']
        inp, out = u['input_tokens'], u['output_tokens']
        details = u.get('input_tokens_details') or {}
        cached, writes = details.get('cached_tokens', 0), details.get('cache_write_tokens', 0)
        thoughts = (u.get('output_tokens_details') or {}).get('reasoning_tokens', 0)
        cost = ((inp - cached - writes) * 2 + cached * .1 + writes * 2.5 + out * 10) / 1e6
    else:
        u = raw['usageMetadata']
        inp = u['promptTokenCount']
        cached, writes, thoughts = u.get('cachedContentTokenCount', 0), 0, u.get('thoughtsTokenCount', 0)
        out = u.get('candidatesTokenCount', 0) + thoughts
        cost = ((inp - cached) + cached * .1 + out * 5) / 1e6
    if any(type(x) is not int or x < 0 for x in (inp, out, cached, writes, thoughts)) or cached + writes > inp or thoughts > out:
        raise ValueError('Unexpected usage accounting')
    return {'input_tokens': inp, 'output_tokens_including_thinking': out, 'thinking_tokens': thoughts,
            'cached_tokens': cached, 'cache_write_tokens': writes,
            'generation_estimate_usd': round(cost, 8), 'usage': u}


def extract_answer(provider, raw):
    if provider == 'openai':
        text = ''.join(c.get('text', '') for item in raw.get('output', []) for c in item.get('content', []) if c.get('type') == 'output_text')
        return text, raw.get('status') == 'completed'
    candidates = raw.get('candidates', [])
    text = ''.join(p.get('text', '') for c in candidates for p in c.get('content', {}).get('parts', []) if not p.get('thought'))
    return text, len(candidates) == 1 and candidates[0].get('finishReason') == 'STOP'


def preflight(job, keys):
    path = reserve(job)
    record = common.load(path)
    provider = job['provider']
    started = time.monotonic()
    try:
        body, text, evidence = build_payload(job)
        (OUT / 'requests').mkdir(exist_ok=True)
        (OUT / 'requests' / (job['id'] + '.md')).write_text(text, encoding='utf-8')
        common.write_json(OUT / 'requests' / (job['id'] + '_evidence.json'), evidence)
        record.update(image_count=2 * len(evidence['frames']), payload_bytes=evidence['payload_bytes'])
        print(f'{job["id"]}: preflight ({record["image_count"]} images)', flush=True)
        if provider == 'openai':
            url = 'https://api.openai.com/v1/responses/input_tokens'
            count_body = {k: body[k] for k in ('model', 'input', 'reasoning', 'truncation')}
        else:
            url = 'https://generativelanguage.googleapis.com/v1beta/models/' + MODELS[provider] + ':countTokens'
            # Include media resolution in token counting, not just generation.
            count_body = {'generateContentRequest': {'model': 'models/' + MODELS[provider], **body}}
        counted = post(url, provider, count_body, keys)
        common.write_json(OUT / 'requests' / (job['id'] + '_token_count.json'), counted)
        tokens = counted['input_tokens' if provider == 'openai' else 'totalTokens']
        if type(tokens) is not int or tokens <= 0:
            raise ValueError('Invalid token count')
        record['counted_input_tokens'] = tokens
        record['preflight_input_rate_allowance_usd'] = tokens * (2 if provider == 'openai' else 1) / 1e6
        if tokens > MAX_INPUT:
            raise ValueError('Input ceiling exceeded; generation blocked')
        worst = (tokens * (2.5 if provider == 'openai' else 1) + MAX_OUTPUT * (10 if provider == 'openai' else 5)) / 1e6
        if worst + record['preflight_input_rate_allowance_usd'] > record['reserved_usd']:
            raise ValueError('Preflight plus maximum generation exceeds reservation')
        record['maximum_generation_estimate_usd'] = worst
        record['status'] = 'preflight_completed'
        print(f'{job["id"]}: {tokens} tokens; generation bound ${worst:.6f}', flush=True)
    except Exception as e:
        record.update(status='stopped', error=redact(str(e), keys)[:800])
        raise RuntimeError(f'{job["id"]}: {record["error"]}') from None
    finally:
        record['preflight_seconds'] = round(time.monotonic() - started, 3)
        atomic_json(path, record)
        report()


def execute(job, keys):
    path = OUT / 'attempts' / (job['id'] + '.json')
    if not path.exists():
        preflight(job, keys)
    record = common.load(path)
    if record['status'] != 'preflight_completed':
        raise ValueError('Attempt already sent, failed, or not preflighted')
    provider = job['provider']
    started = time.monotonic()
    try:
        body, text, evidence = build_payload(job)
        if evidence != common.load(OUT / 'requests' / (job['id'] + '_evidence.json')):
            raise ValueError('Payload changed since preflight')
        tokens = record['counted_input_tokens']
        url = ('https://api.openai.com/v1/responses' if provider == 'openai' else
               'https://generativelanguage.googleapis.com/v1beta/models/' + MODELS[provider])
        record.update({'status': 'generation_in_flight', 'generation_sent': True})
        atomic_json(path, record)
        generation_start = time.monotonic()
        print(f'{job["id"]}: generating; {tokens} input tokens', flush=True)
        raw = post(url if provider == 'openai' else url + ':generateContent', provider, body, keys)
        raw = json.loads(redact(json.dumps(raw), keys))
        record['generation_seconds'] = round(time.monotonic() - generation_start, 3)
        (OUT / 'responses').mkdir(exist_ok=True)
        common.write_json(OUT / 'responses' / (job['id'] + '_raw.json'), raw)
        record['returned_model'] = raw.get('model', raw.get('modelVersion'))
        record['service_tier'] = raw.get('service_tier', (raw.get('usageMetadata') or {}).get('serviceTier'))
        # Account for even invalid/truncated outputs before checking answer validity.
        record.update(usage_cost(provider, raw))
        atomic_json(path, record)
        answer, complete = extract_answer(provider, raw)
        (OUT / 'responses' / (job['id'] + '.md')).write_text(answer, encoding='utf-8')
        if not complete:
            raise ValueError('Incomplete/truncated model answer; no retry')
        if not answer.strip() or answer.lstrip().startswith(('{', '[', '```')):
            raise ValueError('Expected nonempty unfenced Markdown; no repair')
        if record['input_tokens'] > MAX_INPUT or record['output_tokens_including_thinking'] > MAX_OUTPUT:
            raise ValueError('Reported usage exceeded frozen limits; halt')
        if record['generation_estimate_usd'] + record['preflight_input_rate_allowance_usd'] > record['reserved_usd']:
            raise ValueError('Reported estimate exceeded reserved allowance; halt')
        if job['arm'] in ('SP', 'SW'):
            ep = common.load(OUT / job['episode'] / 'input.json')
            freeze_selection(ep, answer, job['arm'])
        record['status'] = 'completed'
    except Exception as e:
        record['status'] = 'stopped'
        record['error'] = redact(str(e), keys)[:800]
        raise RuntimeError(f'{job["id"]}: {record["error"]}') from None
    finally:
        record['total_seconds'] = round(time.monotonic() - started + record.get('preflight_seconds', 0), 3)
        atomic_json(path, record)
        report()
    print(f'{job["id"]}: completed; generation estimate ${record["generation_estimate_usd"]:.6f}', flush=True)


@serialized
def report():
    records = [common.load(p) for p in sorted((OUT / 'attempts').glob('*.json'))]
    cost = sum(r.get('generation_estimate_usd') or 0 for r in records)
    history = {}  # This run's costs are separate from the previous experiment.
    preflight = sum(r.get('preflight_input_rate_allowance_usd', 0) for r in records) + history.get('preflight_input_rate_allowance_usd', 0)
    unknown = [r['id'] for r in records if r.get('generation_sent') and r.get('generation_estimate_usd') is None]
    reserved = round(sum(r['reserved_usd'] for r in records) + history.get('reserved_usd', 0), 2)
    totals = {'completed': sum(r['status'] == 'completed' for r in records), 'attempts': len(records),
              'planned_generation_calls': 60, 'generation_estimate_usd': round(cost, 8),
              'preflight_input_rate_allowance_usd': round(preflight, 8),
              'estimate_plus_preflight_allowance_usd': round(cost + preflight, 8),
              'unknown_cost_requests': unknown, 'reserved_usd': reserved, 'approved_reservation_cap_usd': 10.08,
              'prior_and_diagnostic_costs': history,
              'cost_note': 'Fresh prompt revision; all costs below belong to this rerun. Generation estimate from provider usage and published rates; not a billing receipt. '
                           'Preflight allowance conservatively prices counted input once more, not an observed charge. '
                           'Failed in-flight requests without usage retain their full reservation.',
              'by_provider': {p: {'generation_estimate_usd': round(sum(r.get('generation_estimate_usd') or 0 for r in records if r['provider'] == p), 8),
                                  'reserved_usd': round(sum(r['reserved_usd'] for r in records if r['provider'] == p), 2)} for p in CAP}}
    if (OUT / 'baseline_costs.json').exists():
        baseline = common.load(OUT / 'baseline_costs.json')
        totals['cumulative_with_baseline'] = {
            'known_generation_estimate_usd': round(cost + baseline['generation_estimate_usd'], 8),
            'preflight_allowance_usd': round(preflight + baseline['preflight_input_rate_allowance_usd'], 8),
            'baseline_unknown_requests': baseline['unknown_cost_requests'],
            'unknown_full_reservations_usd': round(baseline['unknown_full_reservations_usd'] + sum(r['reserved_usd'] for r in records if r['id'] in unknown), 8)}
    common.write_json(OUT / 'cost_summary.json', totals)
    columns = ['id', 'provider', 'status', 'reserved_usd', 'counted_input_tokens', 'input_tokens',
               'cached_tokens', 'cache_write_tokens', 'output_tokens_including_thinking', 'thinking_tokens',
               'generation_estimate_usd', 'preflight_input_rate_allowance_usd', 'preflight_seconds',
               'generation_seconds', 'total_seconds', 'payload_bytes', 'image_count', 'returned_model', 'error']
    with (OUT / 'costs.csv').open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(records)
    lines = ['# Frame-selection experiment status', '',
             f'Completed: {totals["completed"]}/60. Attempts reserved: {len(records)}.', '',
             f'Generation estimate: **${cost:.6f}**. Additional conservative preflight allowance: **${preflight:.6f}**.',
             f'Reserved: **${reserved:.2f} / $10.08**. Requests with unknown generation charges: {len(unknown)}.', '',
             totals['cost_note'], '',
             '| Request | Condition | Status | Input | Output incl. thinking | Estimated generation USD |',
             '|---|---|---|---:|---:|---:|']
    for r in records:
        c = r.get('generation_estimate_usd')
        lines.append(f'| [{r["id"]}](responses/{r["id"]}.md) | {LABELS[r["arm"]]} | {r["status"]} | '
                     f'{r.get("input_tokens", "â€”")} | {r.get("output_tokens_including_thinking", "â€”")} | '
                     + (f'{c:.6f}' if c is not None else 'unknown/not sent') + ' |')
    lines += ['', '## Paired cost comparison', '',
              'Compare U with SP+P and SW+W, including selector costs; GPT pair counts are equal.', '',
              '| Episode | U uniform | SP + P points | SW + W windows |', '|---|---:|---:|---:|']
    by_id = {r['id']: r for r in records}
    for eid in IDS:
        values = []
        for arms in [('U',), ('SP', 'P'), ('SW', 'W')]:
            rows = [by_id.get(f'{eid}_{a}') for a in arms]
            values.append(f'${sum(r["generation_estimate_usd"] for r in rows):.6f}'
                          if all(r and r.get('generation_estimate_usd') is not None for r in rows) else 'pending')
        lines.append('| ' + eid + ' | ' + ' | '.join(values) + ' |')
    lines += ['', 'No annotation-quality scores are computed here. Independent human review is required.']
    (OUT / 'REPORT.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    page = ['<!doctype html><meta charset="utf-8"><title>Frame-selection experiment</title>',
            '<style>body{font:16px sans-serif;max-width:1100px;margin:auto}pre{white-space:pre-wrap}img{width:256px}</style>',
            '<h1>Frame-selection experiment</h1><p><a href="REPORT.md">Status and costs</a> Â· <a href="costs.csv">Per-call CSV</a></p>',
            f'<p>{totals["completed"]}/60 complete; generation estimate ${cost:.6f}; allowance reserved ${reserved:.2f}/$10.08.</p>',
            '<p>Candidate annotations require human review. Cost differences are not quality results.</p>']
    for eid in IDS:
        page.append(f'<h2>{eid}</h2>')
        for arm in PROVIDERS:
            path = OUT / 'responses' / f'{eid}_{arm}.md'
            if path.exists():
                page.append(f'<details><summary>{arm}: {html.escape(LABELS[arm])}</summary><p><a href="responses/{eid}_{arm}.md">Markdown file</a></p><pre>{html.escape(path.read_text(encoding="utf-8"))}</pre></details>')
        epfile = OUT / eid / 'input.json'
        if epfile.exists():
            ep = common.load(epfile)
            selected = common.load(OUT / eid / 'selected/freeze.json')['frames'] if (OUT / eid / 'selected/freeze.json').exists() else []
            page.append('<details><summary>Candidate camera evidence and selections</summary>')
            for frame in ep['pool']:
                flags = (' Â· uniform' if frame in ep['uniform'] else '') + (' Â· Gemini-selected' if frame in selected else '')
                page.append(f'<p>Frame {frame} ({frame/20:.2f}s){flags}</p>')
                for camera in ('agent', 'wrist'):
                    page.append(f'<img loading="lazy" src="{eid}/images/{frame:04d}_{camera}.jpg">')
            page.append('</details>')
    (OUT / 'index.html').write_text('\n'.join(page), encoding='utf-8')
    return totals


def run(approval):
    m = verify()
    if approval != common.digest(OUT / 'manifest.json') or date.today() > date(2026, 12, 31):
        raise ValueError('Approval hash mismatch or pricing expired')
    with (OUT / 'run.lock').open('x') as f:
        f.write(approval)
    keys = common.credentials()
    for job in m['jobs']:
        if job['arm'] in ('U','SP','SW'):preflight(job,keys)
    print('Static inputs fit; two independent episode workers; no retries.',flush=True)
    def episode_work(eid):
        for job in [j for j in m['jobs'] if j['episode']==eid]:
            if STOP.is_set():return
            if job['arm'] in ('P','W'):
                selector={'P':'SP','W':'SW'}[job['arm']]
                if not (OUT/eid/selector/'freeze.json').exists():
                    print(job['id']+': blocked by selector',flush=True);continue
            try:execute(job,keys)
            except RuntimeError:
                record=common.load(OUT/'attempts'/(job['id']+'.json'))
                transport=record.get('generation_sent') and record.get('generation_estimate_usd') is None and any(t in record.get('error','') for t in ('TimeoutError','RemoteDisconnected','timed out'))
                selector_invalid=job['arm'] in ('SP','SW') and any(t in record.get('error','') for t in ('Invalid point headings','Expected integer point bullets','Wrong point count','Points must be candidates','Invalid window headings','Wrong window count','Invalid window location','Overlapping windows','Wrong final image budget'))
                if transport or selector_invalid:
                    print(job['id']+': failed; no retry; continuing independent jobs',flush=True);continue
                STOP.set();raise
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures=[executor.submit(episode_work,eid) for eid in IDS]
        for future in futures:future.result()

    print(json.dumps(report(), indent=2), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['prepare', 'inspect', 'run', 'report'])
    parser.add_argument('--approve-manifest-sha256', default='')
    args = parser.parse_args()
    try:
        if args.command == 'prepare': prepare()
        elif args.command == 'inspect': inspect()
        elif args.command == 'report': print(json.dumps(report(), indent=2))
        else: run(args.approve_manifest_sha256)
    except Exception as e:
        # Transport errors were redacted at their boundary; no key-bearing URLs are used.
        print(f'STOPPED: {e}', flush=True)
        raise SystemExit(1) from None


if __name__ == '__main__':
    main()
