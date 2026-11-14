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
import urllib.error
import urllib.request

import api_label_pilot as common

ROOT = common.ROOT
OUT = ROOT / 'outputs/frame_selection_full_coverage_v1'
IDS = ('R001', 'R002', 'R003', 'R004')
MODELS = dict(common.MODELS)
PROVIDERS = {'A': 'openai', 'B': 'gemini', 'C': 'openai', 'D': 'openai', 'E': 'gemini', 'F': 'openai'}
RESERVE = {'openai': .20, 'gemini': .12}
CAP = {'openai': 3.20, 'gemini': .96}
MAX_INPUT, MAX_OUTPUT = 40_000, 4096
PROMPTS = ('progress_failure.md', 'select_frames.md', 'annotate_frame_subset.md')
LABELS = {'A': 'GPT direct', 'B': 'Gemini direct', 'C': 'GPT full / subset prompt',
          'D': 'GPT uniform subset', 'E': 'Gemini frame selector', 'F': 'GPT selected subset'}


def jobs():
    return [{'id': f'{eid}_{arm}', 'episode': eid, 'arm': arm,
             'provider': PROVIDERS[arm], 'reserved_usd': RESERVE[PROVIDERS[arm]]}
            for eid in IDS for arm in PROVIDERS]


def settings():
    return {'models': MODELS, 'max_input_tokens': MAX_INPUT, 'max_output_tokens': MAX_OUTPUT,
            'reasoning': 'low', 'gemini_media_resolution': 'MEDIA_RESOLUTION_LOW', 'image_detail': 'high', 'annotation_format': 'markdown',
            'provider_caps_usd': CAP, 'maximum_reserved_usd': 4.16, 'retries': 0,
            'prompt_revision': 'full_coverage_v1', 'transport_timeout_seconds': 600,
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
        lines += [f'Exact selection budget K: {ep["k"]} camera pairs.',
                  'Mandatory source-frame anchors: ' + ', '.join(map(str, ep['anchors'])) + '.', '']
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
            for name in ('api_frame_selection_full_coverage_v1.py', 'api_label_pilot.py')}


def prepare():
    import api_frame_selection_prompt_v2 as prior
    original = prior.verify()
    if OUT.exists():
        raise ValueError('Existing pack: do not overwrite')
    OUT.mkdir()
    for item in original['episodes']:
        eid = item['id']
        (OUT / eid / 'images').mkdir(parents=True)
        shutil.copyfile(prior.OUT / eid / 'input.json', OUT / eid / 'input.json')
        for source in (prior.OUT / eid / 'images').glob('*.jpg'):
            shutil.copyfile(source, OUT / eid / 'images' / source.name)
    (OUT / 'prompts').mkdir()
    for name in PROMPTS:
        shutil.copyfile(ROOT / 'scripts/annotate/prompts/full_coverage_v1' / name, OUT / 'prompts' / name)
    baseline = common.load(prior.OUT / 'cost_summary.json')
    baseline['unknown_full_reservations_usd'] = sum(common.load(prior.OUT / 'attempts' / (ident + '.json'))['reserved_usd'] for ident in baseline['unknown_cost_requests'])
    cumulative = baseline.get('cumulative_with_baseline', {})
    baseline['generation_estimate_usd'] = cumulative.get('known_generation_estimate_usd', baseline['generation_estimate_usd'])
    baseline['preflight_input_rate_allowance_usd'] = cumulative.get('preflight_allowance_usd', baseline['preflight_input_rate_allowance_usd'])
    baseline['unknown_cost_requests'] += cumulative.get('baseline_unknown_requests', [])
    baseline['unknown_full_reservations_usd'] += cumulative.get('unknown_full_reservations_usd', 0)
    common.write_json(OUT / 'baseline_costs.json', baseline)
    manifest = {'version': 'full_coverage_v1', 'settings': settings(), 'episodes': original['episodes'], 'jobs': jobs(),
                'revision': 'Full-coverage binary progress/failure prompt; fresh A-F calls; same visual pools, selector/subset prompts, models and generation settings.',
                'limitations': 'Development revision informed by reviewing these episodes, not a held-out validation. Only the common annotation prompt changed. E is rerun with the unchanged selector; stochastic selections may differ, so cross-run F changes are not solely an annotation-prompt effect.',
                'baseline_manifest_sha256': common.digest(prior.OUT / 'manifest.json'),
                'user_authorization': 'User requested full coverage with four progress/failure states, then explicitly asked to rerun the pipeline.',
                'code_sha256': code_hashes(),
                'files': {p.relative_to(OUT).as_posix(): common.digest(p)
                          for p in sorted(OUT.rglob('*')) if p.is_file()}}
    common.write_json(OUT / 'manifest.json', manifest)
    report()
    inspect()


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
                      'jobs': len(m['jobs']), 'max_reserved_usd': 4.16,
                      'provider_caps_usd': CAP,
                      'episodes': [{'id': e['id'], 'pairs': len(e['pool']), 'k': e['k'],
                                    'anchors': e['anchors']} for e in m['episodes']]}, indent=2))


def parse_selection(text, ep):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if lines[:2] != ['# Frame selection', '## Selected frames']:
        raise ValueError('Selection headings do not match the frozen prompt')
    if any(not re.fullmatch(r'[-*+] \d+', line) for line in lines[2:]):
        raise ValueError('Selection must contain only integer frame bullets')
    frames = [int(line[2:]) for line in lines[2:]]
    if len(frames) != ep['k'] or frames != sorted(set(frames)):
        raise ValueError('Selection must have exactly K distinct chronological frames')
    if not set(frames) <= set(ep['pool']) or not set(ep['anchors']) <= set(frames):
        raise ValueError('Selection outside pool or missing anchors')
    return frames


def freeze_selection(ep, answer):
    frames = parse_selection(answer, ep)
    folder = OUT / ep['id'] / 'selected'
    folder.mkdir()
    for f in frames:
        for camera in ('agent', 'wrist'):
            name = f'{f:04d}_{camera}.jpg'
            shutil.copyfile(OUT / ep['id'] / 'images' / name, folder / name)
    (folder / 'context.md').write_text(context(ep, frames), encoding='utf-8')
    frozen = {'frames': frames, 'selector_markdown_sha256': sha_bytes(answer.encode()),
              'files': {p.name: common.digest(p) for p in sorted(folder.iterdir()) if p.is_file()}}
    common.write_json(folder / 'freeze.json', frozen)


def selected_frames(ep):
    folder = OUT / ep['id'] / 'selected'
    frozen = common.load(folder / 'freeze.json')
    answer = (OUT / 'responses' / f'{ep["id"]}_E.md').read_text(encoding='utf-8')
    if frozen['selector_markdown_sha256'] != sha_bytes(answer.encode()) or frozen['frames'] != parse_selection(answer, ep):
        raise ValueError('Selector freeze mismatch')
    for name, expected in frozen['files'].items():
        path = (folder / name).resolve()
        if not path.is_relative_to(folder.resolve()) or common.digest(path) != expected:
            raise ValueError('Selected image/context hash changed')
        if name.endswith('.jpg') and expected != common.digest(OUT / ep['id'] / 'images' / name):
            raise ValueError('Selected image differs from original')
    return frozen['frames']


def build_payload(job):
    ep = common.load(OUT / job['episode'] / 'input.json')
    arm, provider = job['arm'], job['provider']
    frames = selected_frames(ep) if arm == 'F' else ep['uniform'] if arm == 'D' else ep['pool']
    prompts = OUT / 'prompts'
    if arm == 'E':
        prompt = (prompts / 'select_frames.md').read_text(encoding='utf-8')
    else:
        prompt = (prompts / 'progress_failure.md').read_text(encoding='utf-8')
        if arm in ('C', 'D', 'F'):
            prompt = (prompts / 'annotate_frame_subset.md').read_text(encoding='utf-8') + '\n\n' + prompt
    # Reconstruct from allowlisted metadata; never append selector prose to GPT input.
    text = prompt + '\n\n' + context(ep, frames, arm == 'E')
    if len(text.encode()) > 30_000 or len(frames) > 80:
        raise ValueError('Oversized local payload')
    parts = [{'type': 'input_text', 'text': text}] if provider == 'openai' else [{'text': text}]
    image_files = {}
    for f in frames:
        caption = f'Source frame {f}, {f / 20:.2f} seconds. External camera, then wrist camera:'
        parts.append({'type': 'input_text', 'text': caption} if provider == 'openai' else {'text': caption})
        for camera in ('agent', 'wrist'):
            folder = 'selected' if arm == 'F' else 'images'
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


def reserve(job):
    if job not in jobs():
        raise ValueError('Request not in approved matrix')
    folder = OUT / 'attempts'
    folder.mkdir(exist_ok=True)
    old = [common.load(p) for p in folder.glob('*.json')]
    if len(old) >= 24 or round(sum(r['reserved_usd'] for r in old) + job['reserved_usd'], 2) > 4.16:
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
        if job['arm'] == 'E':
            ep = common.load(OUT / job['episode'] / 'input.json')
            freeze_selection(ep, answer)
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


def report():
    records = [common.load(p) for p in sorted((OUT / 'attempts').glob('*.json'))]
    cost = sum(r.get('generation_estimate_usd') or 0 for r in records)
    history = {}  # This run's costs are separate from the previous experiment.
    preflight = sum(r.get('preflight_input_rate_allowance_usd', 0) for r in records) + history.get('preflight_input_rate_allowance_usd', 0)
    unknown = [r['id'] for r in records if r.get('generation_sent') and r.get('generation_estimate_usd') is None]
    reserved = round(sum(r['reserved_usd'] for r in records) + history.get('reserved_usd', 0), 2)
    totals = {'completed': sum(r['status'] == 'completed' for r in records), 'attempts': len(records),
              'planned_generation_calls': 24, 'generation_estimate_usd': round(cost, 8),
              'preflight_input_rate_allowance_usd': round(preflight, 8),
              'estimate_plus_preflight_allowance_usd': round(cost + preflight, 8),
              'unknown_cost_requests': unknown, 'reserved_usd': reserved, 'approved_reservation_cap_usd': 4.16,
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
             f'Completed: {totals["completed"]}/24. Attempts reserved: {len(records)}.', '',
             f'Generation estimate: **${cost:.6f}**. Additional conservative preflight allowance: **${preflight:.6f}**.',
             f'Reserved: **${reserved:.2f} / $4.16**. Requests with unknown generation charges: {len(unknown)}.', '',
             totals['cost_note'], '',
             '| Request | Condition | Status | Input | Output incl. thinking | Estimated generation USD |',
             '|---|---|---|---:|---:|---:|']
    for r in records:
        c = r.get('generation_estimate_usd')
        lines.append(f'| [{r["id"]}](responses/{r["id"]}.md) | {LABELS[r["arm"]]} | {r["status"]} | '
                     f'{r.get("input_tokens", "—")} | {r.get("output_tokens_including_thinking", "—")} | '
                     + (f'{c:.6f}' if c is not None else 'unknown/not sent') + ' |')
    lines += ['', '## Paired cost comparison', '',
              'Compare C with E+F for total pipeline cost; D and F have the same number of camera pairs.', '',
              '| Episode | C full GPT | D uniform GPT | E selector + F GPT |', '|---|---:|---:|---:|']
    by_id = {r['id']: r for r in records}
    for eid in IDS:
        values = []
        for arms in [('C',), ('D',), ('E', 'F')]:
            rows = [by_id.get(f'{eid}_{a}') for a in arms]
            values.append(f'${sum(r["generation_estimate_usd"] for r in rows):.6f}'
                          if all(r and r.get('generation_estimate_usd') is not None for r in rows) else 'pending')
        lines.append('| ' + eid + ' | ' + ' | '.join(values) + ' |')
    lines += ['', 'No annotation-quality scores are computed here. Independent human review is required.']
    (OUT / 'REPORT.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    page = ['<!doctype html><meta charset="utf-8"><title>Frame-selection experiment</title>',
            '<style>body{font:16px sans-serif;max-width:1100px;margin:auto}pre{white-space:pre-wrap}img{width:256px}</style>',
            '<h1>Frame-selection experiment</h1><p><a href="REPORT.md">Status and costs</a> · <a href="costs.csv">Per-call CSV</a></p>',
            f'<p>{totals["completed"]}/24 complete; generation estimate ${cost:.6f}; allowance reserved ${reserved:.2f}/$4.16.</p>',
            '<p>Candidate annotations require human review. Cost differences are not quality results.</p>']
    for eid in IDS:
        page.append(f'<h2>{eid}</h2>')
        for arm in ('A', 'B', 'C', 'D', 'E', 'F'):
            path = OUT / 'responses' / f'{eid}_{arm}.md'
            if path.exists():
                page.append(f'<details><summary>{arm}: {html.escape(LABELS[arm])}</summary><p><a href="responses/{eid}_{arm}.md">Markdown file</a></p><pre>{html.escape(path.read_text(encoding="utf-8"))}</pre></details>')
        epfile = OUT / eid / 'input.json'
        if epfile.exists():
            ep = common.load(epfile)
            selected = common.load(OUT / eid / 'selected/freeze.json')['frames'] if (OUT / eid / 'selected/freeze.json').exists() else []
            page.append('<details><summary>Candidate camera evidence and selections</summary>')
            for frame in ep['pool']:
                flags = (' · uniform' if frame in ep['uniform'] else '') + (' · Gemini-selected' if frame in selected else '')
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
        if not (OUT / 'attempts' / (job['id'] + '.json')).exists() and job['arm'] != 'F':
            preflight(job, keys)
    print('All static inputs fit; starting generation. Dynamic F inputs are counted after selection.', flush=True)
    for job in m['jobs']:
        if not (OUT / 'attempts' / (job['id'] + '.json')).exists() or common.load(OUT / 'attempts' / (job['id'] + '.json'))['status'] != 'completed':
            execute(job, keys)
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
