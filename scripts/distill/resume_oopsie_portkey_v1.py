"""Continue only never-submitted Sol requests through the explicit Portkey key.

The original run stays frozen. File references are re-uploaded to the new
provider; image bytes, prompt, model and decoding settings stay unchanged.
No generation request is automatically retried, including an ambiguous submit.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid

import oopsie_common as common
import oopsie_bulk_batch as bulk
import annotation_runtime as transport

SOURCE = common.ROOT / 'outputs/oopsie_rich_failure_v8_1_additional_500_batch_v2'
DEST = common.ROOT / 'outputs/oopsie_rich_failure_v8_1_additional_500_portkey_v3'


def now():
    return datetime.now(timezone.utc).isoformat()


class Portkey:
    """An explicit gateway transport: never reads or falls back to OPENAI_API_KEY."""
    def __init__(self, secret=None):
        path = secret or common.ROOT / '.env.portkey'
        values = dict(line.split('=', 1) for line in path.read_text(encoding='utf-8').splitlines()
                      if line.strip() and not line.startswith('#') and '=' in line)
        self.key = values.get('PORTKEY_API_KEY', '').strip()
        self.provider = values.get('PORTKEY_PROVIDER', '').strip()
        if not self.key or not re.fullmatch(r'@[A-Za-z0-9_-]+', self.provider):
            raise ValueError('Explicit PORTKEY_API_KEY and provider alias required in .env.portkey')
        self.fingerprint = hashlib.sha256(self.key.encode()).hexdigest()[:12]

    def api(self, method, path, body=None, content_type='application/json', raw=False, request_id=None):
        if not re.fullmatch(r'/v1/(files|batches)(/[A-Za-z0-9_-]+)?(/content)?', path):
            raise ValueError('Unexpected gateway path')
        headers = {'x-portkey-api-key': self.key, 'x-portkey-provider': self.provider,
                   'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'}
        data = json.dumps(body).encode() if isinstance(body, dict) else body
        if data is not None:
            headers['Content-Type'] = content_type
        if request_id:
            headers.update({'X-Client-Request-Id': request_id, 'Idempotency-Key': request_id})
        request = urllib.request.Request('https://api.portkey.ai' + path, data=data,
                                         headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=600) as response:
                data = response.read()
            return data if raw else json.loads(data)
        except urllib.error.HTTPError as error:
            message = error.read().decode('utf-8', errors='replace').replace(self.key, '[REDACTED]')
            raise RuntimeError(f'Portkey HTTP {error.code}: {message[:1800]}') from None
        except (OSError, ValueError) as error:
            raise RuntimeError(f'Portkey {type(error).__name__}; outcome may be unknown; no resend') from None

    def upload(self, path, purpose):
        boundary = 'portkey-' + uuid.uuid4().hex
        mime = 'image/webp' if purpose == 'vision' else 'application/jsonl'
        prefix = (f'--{boundary}\r\nContent-Disposition: form-data; name="purpose"\r\n\r\n{purpose}\r\n'
                  f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{path.name}"\r\n'
                  f'Content-Type: {mime}\r\n\r\n').encode()
        body = prefix + path.read_bytes() + f'\r\n--{boundary}--\r\n'.encode()
        result = self.api('POST', '/v1/files', body, 'multipart/form-data; boundary=' + boundary)
        if not result.get('id') or result.get('bytes') != path.stat().st_size:
            raise ValueError('Unexpected uploaded file receipt')
        return result


def pending_shards(source, manifest):
    """Existing journals include successful, rejected and uncertain submissions."""
    return [s for s in manifest['shards']
            if not (source / 'batch_jobs' / (Path(s['path']).stem + '.json')).exists()]


def prepare(source, dest, client):
    m = bulk.verify(source)
    bm = common.read(source / 'batch_manifest.json')
    pf = common.read(source / 'token_preflight.json')
    if (bm['manifest_sha256'] != common.sha(source / 'manifest.json') or
            bm['preflight_sha256'] != common.sha(source / 'token_preflight.json') or not pf['complete']):
        raise ValueError('Frozen preflight provenance changed')
    if (source / 'queue_worker.lock').exists():
        raise ValueError('Source queue has a lock; refuse concurrent continuation')
    if dest.exists():
        raise ValueError('Continuation already exists; use run/status, never prepare it again')
    shards = pending_shards(source, bm)
    rows = {r['episode']: r for r in pf['requests']}
    request_hashes = {}
    for s in shards:
        if common.sha(source / s['path']) != s['sha256']:
            raise ValueError('Frozen source shard changed')
        for cid in s['custom_ids']:
            eid = cid.removesuffix('_sol_r01')
            path = source / 'requests' / (eid + '_sol.json')
            if common.sha(path) != rows[eid]['request_sha256']:
                raise ValueError('Frozen source request changed')
            request_hashes[eid] = rows[eid]['request_sha256']
    # Budget includes every already billed response, even parser-invalid responses.
    spent = sum(common.read(p).get('generation_estimate_usd', 0)
                for p in (source / 'traces').glob('*/attempt.json'))
    remaining_ceiling = sum(s['cost_ceiling_usd'] for s in shards)
    if spent + remaining_ceiling > m['config']['budget_usd'] or m['config']['budget_usd'] != 75:
        raise ValueError('Continuation exceeds the existing $75 generation authorization')
    plan = dict(protocol='oopsie_sol_portkey_continuation_v1', run_id=uuid.uuid4().hex,
                created_utc=now(), source=str(source), source_manifest_sha256=common.sha(source / 'manifest.json'),
                source_batch_manifest_sha256=common.sha(source / 'batch_manifest.json'),
                source_preflight_sha256=common.sha(source / 'token_preflight.json'),
                provider=client.provider, credential_fingerprint_sha256_prefix=client.fingerprint,
                model='gpt-6.1-sol', endpoint='/v1/responses', completion_window='24h',
                planned_new_requests=len(request_hashes), preserved_source_responses=len(list((source / 'traces').glob('*/attempt.json'))),
                source_spend_estimate_usd=spent, continuation_cost_ceiling_usd=remaining_ceiling,
                combined_cost_ceiling_usd=spent + remaining_ceiling, budget_usd=75,
                max_enqueued_input_tokens=bm['max_enqueued_input_tokens'], generation_retries=0,
                requests=request_hashes, shards=shards,
                selection='Only shards without any prior submission journal; excludes all failed and ambiguous submissions.')
    dest.mkdir(parents=True)
    for name in ('manifest.json', 'config.json', 'selection.json', 'selection_plan.json', 'prompt.md'):
        shutil.copyfile(source / name, dest / name)
    for name in ('requests', 'batch_inputs', 'batch_jobs', 'batch_outputs', 'image_uploads', 'prepared_shards'):
        (dest / name).mkdir()
    shutil.copytree(source / 'traces', dest / 'traces')
    if (source / 'reviews').exists():
        shutil.copytree(source / 'reviews', dest / 'reviews')
    # Read-only media assets share bytes on disk; no source files are moved or edited.
    for e in m['episodes']:
        for video in e['videos']:
            relative = video.get('path', video.get('url'))
            path = dest / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists():
                os.link(source / relative, path)
    bulk.write_once(dest / 'continuation_plan.json', plan)
    lines = ['# Sol collection continuation through Portkey', '',
             f'- New requests: {len(request_hashes)} never-submitted episodes; existing outputs remain preserved.',
             '- Teacher: gpt-6.1-sol, low reasoning, unchanged V8.1 prompt and complete camera/frame evidence.',
             '- Transport: explicit Portkey key and provider; no fallback to the old OpenAI key.',
             '- Previously rejected or uncertain requests are excluded from this continuation.',
             '- Existing provider-specific image references are replaced with uploads of the exact same image bytes.',
             f'- Previous generation estimate: ${spent:.6f}. Remaining Batch ceiling: ${remaining_ceiling:.6f}.',
             f'- Combined ceiling: ${spent + remaining_ceiling:.6f}, within the original $75 authorization.',
             '- Frozen source manifests, requests, teacher responses and review notes are preserved.',
             '- No student training is submitted.']
    (dest / 'plan.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    publish(dest, m, plan, 'Prepared; Portkey queue has not submitted any batches yet.')
    return plan


def remap_images(body, episode, upload_image):
    slots = [x for x in body['input'][0]['content'] if x.get('type') == 'input_image']
    if len(slots) != len(episode['images']):
        raise ValueError('Image/frame coverage changed')
    for slot, image in zip(slots, episode['images']):
        if 'file_id' in slot:
            slot['file_id'] = upload_image(image)
    return body


def prepare_shard(source, dest, plan, shard, episodes, client):
    stem = Path(shard['path']).stem
    receipt = dest / 'prepared_shards' / (stem + '.json')
    target = dest / shard['path']
    if receipt.exists():
        ready = common.read(receipt)
        if common.sha(target) != ready['sha256']:
            raise ValueError('Prepared Portkey batch changed')
        return ready
    def upload_image(image):
        path = common.inside(source, image['path'])
        if common.sha(path) != image['sha256']:
            raise ValueError('Original image bytes changed')
        receipt = dest / 'image_uploads' / (image['sha256'] + '.json')
        if receipt.exists():
            saved = common.read(receipt)
        else:
            saved = dict(image_sha256=image['sha256'], provider=client.provider,
                         response=client.upload(path, 'vision'))
            bulk.write_once(receipt, saved)
        if saved['image_sha256'] != image['sha256'] or saved['provider'] != client.provider:
            raise ValueError('Image upload provenance changed')
        return saved['response']['id']
    temp = target.with_suffix('.jsonl.preparing')
    if temp.exists() or target.exists():
        raise ValueError('Interrupted shard preparation needs inspection; no overwrite')
    with temp.open('xb') as stream:
        for cid in shard['custom_ids']:
            eid = cid.removesuffix('_sol_r01')
            old = source / 'requests' / (eid + '_sol.json')
            if common.sha(old) != plan['requests'][eid]:
                raise ValueError('Source request changed')
            body = common.read(old)
            if body['model'] != 'gpt-6.1-sol':
                raise ValueError('Wrong teacher model')
            remap_images(body, episodes[eid], upload_image)
            data = bulk.compact(body)
            path = dest / 'requests' / old.name
            with path.open('xb') as output:
                output.write(data)
            stream.write(b'{"custom_id":' + bulk.compact(cid) +
                         b',"method":"POST","url":"/v1/responses","body":' + data + b'}\n')
    temp.replace(target)
    ready = dict(path=shard['path'], sha256=common.sha(target), bytes=target.stat().st_size,
                 custom_ids=shard['custom_ids'], input_tokens=shard['input_tokens'],
                 cost_ceiling_usd=shard['cost_ceiling_usd'])
    bulk.write_once(receipt, ready)
    return ready


def submit(dest, plan, shard, client):
    stem = Path(shard['path']).stem
    path = dest / 'batch_jobs' / (stem + '.json')
    if path.exists():
        raise ValueError('Prior submission journal exists; no resend')
    if common.sha(dest / shard['path']) != shard['sha256']:
        raise ValueError('Prepared Portkey batch changed')
    upload_path = dest / 'batch_jobs' / (stem + '_upload.json')
    if upload_path.exists():
        uploaded = common.read(upload_path)
    else:
        uploaded = client.upload(dest / shard['path'], 'batch')
        bulk.write_once(upload_path, uploaded)
    state = dict(status='submitting', input_file_id=uploaded['id'], run_id=plan['run_id'],
                 custom_ids=shard['custom_ids'], request_id=str(uuid.uuid4()),
                 provider=client.provider, started_utc=now())
    bulk.write_once(path, state)
    try:
        state['batch'] = client.api('POST', '/v1/batches',
            dict(input_file_id=uploaded['id'], endpoint='/v1/responses', completion_window='24h',
                 metadata=dict(run_id=plan['run_id'], shard=stem, protocol=plan['protocol'])),
            request_id=state['request_id'])
        state['status'] = 'submitted'
    except Exception as error:
        state.update(status='submission_unresolved', error=str(error))
        raise
    finally:
        transport.atomic_json(path, state)
    print(json.dumps(dict(submitted=stem, requests=len(shard['custom_ids']),
                          batch_id=state['batch']['id'], gateway='Portkey')), flush=True)


def collect(dest, m, plan, client):
    active = complete = tokens = 0
    for shard in plan['shards']:
        path = dest / 'batch_jobs' / (Path(shard['path']).stem + '.json')
        if not path.exists():
            continue
        state = common.read(path)
        if not state.get('batch'):
            raise ValueError('Uncertain submission; no automatic resend')
        remote = state['batch']
        if remote['status'] not in bulk.TERMINAL:
            remote = client.api('GET', '/v1/batches/' + remote['id'])
            state['batch'] = remote
            transport.atomic_json(path, state)
        if remote['status'] not in bulk.TERMINAL:
            active += len(shard['custom_ids'])
            tokens += shard['input_tokens']
            continue
        for role in ('output', 'error'):
            fid = remote.get(role + '_file_id')
            if fid:
                output = dest / 'batch_outputs' / (path.stem + '_' + role + '.jsonl')
                if not output.exists():
                    data = client.api('GET', '/v1/files/' + fid + '/content', raw=True)
                    with output.open('xb') as stream:
                        stream.write(data)
                bulk.ingest(dest, m, shard, output.read_bytes())
                if role == 'error' and any(code in output.read_bytes() for code in
                        (b'credit_balance_exhausted', b'billing_hard_limit_reached', b'insufficient_quota')):
                    raise ValueError('Portkey returned a billing/quota rejection; preserve outputs and stop submissions')
        if remote['status'] != 'completed':
            raise ValueError('A Portkey batch failed; no further submissions or generation retries')
        complete += len(shard['custom_ids'])
    return active, complete, tokens


def publish(dest, m, plan, message, **counts):
    state = dict(message=message, updated_utc=now(), controller_pid=os.getpid(),
                 transport='Portkey', planned_new_requests=plan['planned_new_requests'], **counts)
    transport.atomic_json(dest / 'queue_status.json', state)
    bulk.publish(dest, m, state)
    summary = common.read(dest / 'collection_summary.json')
    lines = ['# Sol collection through Portkey', '', message, '',
             f"- Updated (UTC): {state['updated_utc']}",
             f"- Validated labels: {summary['validated']}/500; preserved invalid/stopped responses: {len(summary['invalid'])}.",
             f"- New requests planned: {plan['planned_new_requests']}; active: {counts.get('active_requests', 0)}; newly returned: {counts.get('completed_new_requests', 0)}.",
             '- Teacher: gpt-6.1-sol. Gateway: api.portkey.ai. No direct OpenAI credential fallback.',
             f"- Combined generation ceiling: ${plan['combined_cost_ceiling_usd']:.6f}, within the original $75 authorization.",
             '- Rejected and uncertain source submissions remain excluded; no automatic generation retries.',
             '', '[Video and time-aligned annotations](http://127.0.0.1:8802/review.html) · [Continuation plan](plan.md)']
    (dest / 'status.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps(state), flush=True)


def run(dest, client, interval=30):
    if (dest / 'STOP_REQUESTED.json').exists():
        raise ValueError('Stopped at user request; explicit authorization is required before resuming')
    plan = common.read(dest / 'continuation_plan.json')
    source = Path(plan['source'])
    if client.provider != plan['provider'] or client.fingerprint != plan['credential_fingerprint_sha256_prefix']:
        raise ValueError('Portkey credential/provider differs from frozen continuation plan')
    for filename, key in [('manifest.json', 'source_manifest_sha256'),
                          ('batch_manifest.json', 'source_batch_manifest_sha256'),
                          ('token_preflight.json', 'source_preflight_sha256')]:
        if common.sha(source / filename) != plan[key]:
            raise ValueError('Frozen source provenance changed')
    m = bulk.verify(source)
    episodes = {e['id']: e for e in m['episodes']}
    lock = dest / 'queue_worker.lock'
    with lock.open('x', encoding='utf-8') as stream:
        json.dump(dict(pid=os.getpid(), started_utc=now()), stream)
    try:
        while True:
            if (dest / 'STOP_REQUESTED.json').exists():
                raise ValueError('Stopped at user request; no further submissions')
            active, complete, tokens = collect(dest, m, plan, client)
            submitted_one = False
            pending = []
            for s in plan['shards']:
                path = dest / 'batch_jobs' / (Path(s['path']).stem + '.json')
                if not path.exists():
                    pending.append(s)
            if pending and tokens + pending[0]['input_tokens'] <= plan['max_enqueued_input_tokens']:
                shard = pending[0]
                if (source / 'queue_worker.lock').exists() or (source / 'batch_jobs' / (Path(shard['path']).stem + '.json')).exists():
                    raise ValueError('Source queue or journal appeared; refuse duplicate submission')
                publish(dest, m, plan, 'Uploading unchanged evidence and preparing the next Portkey batch.',
                        active_requests=active, completed_new_requests=complete,
                        queued_locally=sum(len(s['custom_ids']) for s in pending))
                prepared = prepare_shard(source, dest, plan, shard, episodes, client)
                if (dest / 'STOP_REQUESTED.json').exists():
                    raise ValueError('Stopped at user request before batch submission')
                submit(dest, plan, prepared, client)
                active += len(shard['custom_ids'])
                pending.pop(0)
                submitted_one = True
            message = f"Portkey Sol collection running: {active} active; {sum(len(s['custom_ids']) for s in pending)} queued; {complete} new responses returned."
            if not pending and not active:
                message = 'Portkey continuation complete; original failed/uncertain requests remain preserved and excluded.'
            publish(dest, m, plan, message, active_requests=active, completed_new_requests=complete,
                    queued_locally=sum(len(s['custom_ids']) for s in pending))
            if not pending and not active:
                # Existing viewer is reused. Check all available episodes and
                # repeats on its ordinary URL after the last label arrivals.
                command = [str(common.ROOT / '.venv-review/Scripts/python.exe'),
                           str(common.ROOT / 'scripts/distill/check_binary_review_browser.py'),
                           '--url', 'http://127.0.0.1:8802/review.html',
                           '--browser', 'C:/Program Files/Google/Chrome/Application/chrome.exe',
                           '--out', str(dest / 'browser_checks')]
                with (dest / 'browser.stdout.log').open('w') as out, (dest / 'browser.stderr.log').open('w') as err:
                    checked = subprocess.run(command, cwd=common.ROOT, stdout=out, stderr=err,
                                             creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                transport.atomic_json(dest / 'browser_status.json', dict(returncode=checked.returncode,
                    all_available_episodes_and_repeats_checked=checked.returncode == 0))
                return
            if not submitted_one:
                time.sleep(interval)
    except Exception as error:
        transport.atomic_json(dest / 'queue_failure.json', dict(message=str(error), updated_utc=now()))
        publish(dest, m, plan, 'Stopped; no automatic resend. ' + str(error))
        raise
    finally:
        lock.unlink(missing_ok=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('prepare', 'run'))
    parser.add_argument('--source', type=Path, default=SOURCE)
    parser.add_argument('--run', type=Path, default=DEST)
    args = parser.parse_args()
    client = Portkey()
    if args.command == 'prepare':
        prepare(args.source.resolve(), args.run.resolve(), client)
    else:
        run(args.run.resolve(), client)
