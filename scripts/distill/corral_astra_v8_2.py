"""Fresh uniform Corral sample and ten-episode Portkey Astra review pilot.

No training and no bulk labeling. Collection requires an authenticated WSL SSH
control session. Existing teacher runs are never read or modified.
"""
import argparse
import base64
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import random
import shlex
import shutil
import subprocess
import tarfile
import tempfile
import urllib.error
import urllib.request
import uuid

import oopsie_common as common
from oopsie_bulk_v8_1 import Preparation, write_once
import annotation_runtime as transport
import rich_failure_v8_2 as schema

ROOT = common.ROOT
DEFAULT = ROOT / 'outputs/corral_astra_rich_failure_v8_2_1000_v1'
INVENTORY = ROOT / 'outputs/oopsiedata_v0_1_access/episodes.csv'
VIDEOS = ROOT / 'outputs/oopsie_corpus_duration_audit_v1/manifest.csv'
PROMPT = ROOT / 'scripts/annotate/prompts/rich_failure_v8_2.md'
SSH = ['wsl', '-d', 'Ubuntu-22.04', '--', 'ssh', '-S', '/home/aliu/.ssh/tacc-flora-%C',
       '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15', 'al62479@login2.ls6.tacc.utexas.edu']


def now():
    return datetime.now(timezone.utc).isoformat()


def csv_rows(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def plan(root, corral_root, seed):
    """Uniform sample without replacement; no outcome/lab/length/old-run filters."""
    if (root / 'selection.json').exists():
        raise ValueError('Selection already frozen; use fetch/prepare, never resample')
    if not corral_root.startswith('/corral/') or '..' in PurePosixPath(corral_root).parts:
        raise ValueError('An absolute Corral release root is required')
    probe = subprocess.run(SSH + ['find ' + shlex.quote(corral_root + '/labs') +
        " -type f \\( -name '*.h5' -o -name '*.hdf5' \\) -printf '%P\\n'"], capture_output=True, timeout=300)
    if probe.returncode:
        raise RuntimeError('Corral inventory unavailable: ' + probe.stderr.decode(errors='replace')[-1200:])
    present = {'labs/' + p for p in probe.stdout.decode().splitlines()}
    videos = {r['release_path']: r for r in csv_rows(VIDEOS)}
    eligible = []; excluded = Counter()
    for row in sorted(csv_rows(INVENTORY), key=lambda e: e['release_path']):
        if row['release_path'] not in present:
            excluded['not_present_on_corral'] += 1; continue
        refs = json.loads(row['video_reference_paths_json'])
        if row['validation_status'] not in {'ok', 'corrected_video_references'} or row['all_video_references_present'] != 'True' or not refs or any(p not in videos for p in refs):
            excluded['invalid_release_metadata_or_missing_media_reference'] += 1; continue
        eligible.append(row)
    if len(eligible) < 1000:
        raise ValueError(f'Only {len(eligible)} eligible Corral episodes; verify the release root')
    seed = seed if seed is not None else random.SystemRandom().getrandbits(64)
    selected = random.Random(seed).sample(eligible, 1000)
    files = {}; episodes = []
    for i, row in enumerate(selected, 1):
        row = dict(row, id=f'C{i:04d}', lab=row['source_repo'].split('/')[-1], split='review')
        episodes.append(row)
        files[row['release_path']] = dict(sha256=row['release_file_sha256'], bytes=int(row['release_file_size_bytes']))
        for p in json.loads(row['video_reference_paths_json']):
            files[p] = dict(sha256=videos[p]['release_sha256'], bytes=int(videos[p]['release_size_bytes']))
    root.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(PROMPT, root / 'prompt.md')
    selection = dict(protocol='corral_astra_rich_failure_v8_2', created_utc=now(), seed=seed,
        source='Corral', corral_release_root=corral_root, eligible_count=len(eligible),
        sampling='Uniform random sample of 1000 distinct release episode paths without replacement. First 10 in the frozen random order form the pilot.',
        overlap_exclusions=False, outcome_labels_used=False, lab_balancing=False,
        length_or_camera_count_filter=False, technical_exclusions=dict(excluded),
        inventory_sha256=common.sha(INVENTORY), video_inventory_sha256=common.sha(VIDEOS),
        corral_hdf5_inventory_sha256=hashlib.sha256(probe.stdout).hexdigest(),
        prompt_sha256=common.sha(root / 'prompt.md'), model='gpt-6-astra', gateway='https://api.portkey.ai',
        pilot_ids=[e['id'] for e in episodes[:10]], labeling_authorized_episode_count=10,
        bulk_labeling_requires_user_review=True, episodes=episodes, files=files)
    write_once(root / 'selection.json', selection)
    (root / 'corral_hdf5_inventory.txt').write_bytes(probe.stdout)
    write_once(root / 'selection_summary.json', dict(episodes=1000, pilot=10, seed=seed,
        labs=dict(Counter(e['lab'] for e in episodes)), source_bytes=sum(f['bytes'] for f in files.values())))
    print(json.dumps(dict(selected=1000, pilot=10, seed=seed, eligible=len(eligible), source_bytes=sum(f['bytes'] for f in files.values()))), flush=True)


def verified_selection(root):
    m = common.read(root / 'selection.json')
    if common.sha(root / 'prompt.md') != m['prompt_sha256'] or len(m['episodes']) != 1000:
        raise ValueError('Changed frozen selection/prompt')
    if len({e['release_path'] for e in m['episodes']}) != 1000 or m['pilot_ids'] != [e['id'] for e in m['episodes'][:10]]:
        raise ValueError('Changed sample or pilot order')
    return m


def source_path(root, relative, meta):
    return root / 'source_files' / (meta['sha256'] + PurePosixPath(relative).suffix)


def fetch(root):
    m = verified_selection(root); missing = {}
    for relative, meta in m['files'].items():
        path = source_path(root, relative, meta)
        if not path.exists() or path.stat().st_size != meta['bytes'] or common.sha(path) != meta['sha256']:
            missing[relative] = meta
    if missing:
        (root / 'source_files').mkdir(exist_ok=True)
        command = 'tar -C ' + shlex.quote(m['corral_release_root']) + ' --null -cf - -T -'
        with tempfile.TemporaryFile() as errors, ThreadPoolExecutor(max_workers=1) as pool:
            process = subprocess.Popen(SSH + [command], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=errors)
            def send_names():
                try:
                    process.stdin.write(('\0'.join(missing) + '\0').encode()); process.stdin.close()
                except BrokenPipeError:
                    pass
            sender = pool.submit(send_names)
            try:
                with tarfile.open(fileobj=process.stdout, mode='r|') as archive:
                    for member in archive:
                        if member.name not in missing or not member.isfile():
                            raise ValueError('Unexpected archive member from Corral')
                        meta = missing[member.name]
                        if member.size != meta['bytes']:
                            raise ValueError('Corral file differs from pinned release size: ' + member.name)
                        dest = source_path(root, member.name, meta); partial = dest.with_suffix(dest.suffix + '.part')
                        with archive.extractfile(member) as inp, partial.open('wb') as out:
                            shutil.copyfileobj(inp, out, 1024 * 1024)
                        if common.sha(partial) != meta['sha256']:
                            raise ValueError('Corral bytes differ from pinned release hash: ' + member.name)
                        partial.replace(dest)
                        print('Verified Corral file: ' + member.name, flush=True)
                sender.result()
                if process.wait() != 0:
                    errors.seek(0); raise RuntimeError(errors.read().decode(errors='replace')[-1500:])
            finally:
                if process.poll() is None:
                    process.kill(); process.wait()
    for relative, meta in m['files'].items():
        path = source_path(root, relative, meta)
        if not path.exists() or path.stat().st_size != meta['bytes'] or common.sha(path) != meta['sha256']:
            raise ValueError('Incomplete collection: ' + relative)
    write_once(root / 'collection_verified.json', dict(selection_sha256=common.sha(root / 'selection.json'),
        episodes=1000, files=len(m['files']), all_source_checksums_match=True, source='Corral'))
    print('All 1000 episodes and referenced original videos collected and checksum verified.', flush=True)


class CorralPreparation(Preparation):
    def __init__(self, root, m):
        self.root = root
        self.cfg = dict(max_image_side=280)
        self.files = m['files']
        self.videos = {r['release_path']: r for r in csv_rows(VIDEOS)}

    def download(self, relative, checksum, size):
        meta = self.files[relative]; path = source_path(self.root, relative, meta)
        if meta != dict(sha256=checksum, bytes=size) or path.stat().st_size != size or common.sha(path) != checksum:
            raise ValueError('Changed Corral source')
        return path

    def episode(self, item):
        # Some releases store N actions/states and N+1 video observations. Use
        # the complete video timeline for this visual-only annotation, retaining
        # both counts explicitly. Never discard the terminal observation.
        import av
        counts = []
        for relative in json.loads(item['video_reference_paths_json']):
            meta = self.files[relative]
            path = self.download(relative, meta['sha256'], meta['bytes'])
            with av.open(str(path)) as container:
                count = container.streams.video[0].frames
                if not count:
                    count = sum(1 for _ in container.decode(video=0))
                counts.append(count)
        state_count = int(item['timestep_count'])
        if not counts or len(set(counts)) != 1 or counts[0] not in (state_count, state_count + 1):
            raise ValueError('Unresolved native camera/state frame counts: ' + item['id'])
        result = super().episode(dict(item, timestep_count=str(counts[0])))
        if result['status'] == 'prepared':
            result = dict(result, source_timestep_count=state_count,
                video_frame_count=counts[0], frame_alignment_note=(
                    'All camera videos contain one extra observation relative to robot timesteps; all video frames retained. No telemetry supplied.'
                    if counts[0] != state_count else 'Camera video and robot timestep counts match.'))
        return result


def prepare(root):
    m = verified_selection(root)
    builder = CorralPreparation(root, m)
    episodes = [builder.episode(e) for e in m['episodes'][:10]]
    failures = [e for e in episodes if e['status'] != 'prepared']
    if failures:
        raise ValueError('Pilot has technical issues; preserve sample and inspect prepared records: ' + str(failures))
    write_once(root / 'pilot_source_verified.json', dict(selection_sha256=common.sha(root / 'selection.json'),
        episodes=10, all_pilot_sources_checksum_verified=True, source='Corral'))
    write_once(root / 'manifest.json', dict(protocol=m['protocol'], annotation_schema=schema.SCHEMA,
        selection_sha256=common.sha(root / 'selection.json'), prompt_sha256=m['prompt_sha256'],
        model='gpt-6-astra', reasoning_effort='low', max_output_tokens=12000,
        evidence='all_recorded_frames_full_episode', max_camera_image_side=280,
        source_annotations_used_as_model_input=False, episodes=episodes))
    print('Prepared 10 complete episodes; all recorded frames, all distinct native camera views.', flush=True)


class Gateway:
    def __init__(self):
        values = dict(line.split('=', 1) for line in (ROOT / '.env.portkey').read_text(encoding='utf-8-sig').splitlines()
            if line.strip() and not line.startswith('#') and '=' in line)
        self.key = values.get('PORTKEY_API_KEY', '').strip()
        self.provider = values.get('PORTKEY_PROVIDER', '').strip()
        if not self.key or not __import__('re').fullmatch(r'@[A-Za-z0-9_-]+', self.provider):
            raise ValueError('Explicit Portkey key and provider alias required; no direct API fallback')

    def post(self, path, body, request_id):
        if path not in ('/v1/responses/input_tokens', '/v1/responses'):
            raise ValueError('Unexpected gateway path')
        request = urllib.request.Request('https://api.portkey.ai' + path,
            data=json.dumps(body, separators=(',', ':')).encode(), method='POST', headers={
                'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0',
                'x-portkey-api-key': self.key, 'x-portkey-provider': self.provider,
                'x-portkey-retry-count': '0', 'x-portkey-trace-id': request_id,
                'X-Client-Request-Id': request_id, 'Idempotency-Key': request_id})
        try:
            with urllib.request.urlopen(request, timeout=600) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            message = error.read().decode(errors='replace').replace(self.key, '[REDACTED]')
            raise RuntimeError(f'Portkey HTTP {error.code}: {message[:1600]}') from None
        except Exception as error:
            raise RuntimeError(type(error).__name__ + '; submission may be unknown; no automatic resend') from None


def manifest(root):
    m = common.read(root / 'manifest.json'); selection = verified_selection(root)
    if m['selection_sha256'] != common.sha(root / 'selection.json') or m['prompt_sha256'] != selection['prompt_sha256']:
        raise ValueError('Changed frozen provenance')
    if m['model'] != 'gpt-6-astra' or [e['id'] for e in m['episodes']] != selection['pilot_ids'] or m['source_annotations_used_as_model_input']:
        raise ValueError('Only the ten authorized Astra pilot episodes may be labeled')
    return m


def payload(root, m, e):
    info = (f"\n\n## Episode input\n\n- Episode: {e['id']}\n- Task: {e['task']}\n"
        f"- Source frame count: {e['n_frames']}\n- Frames per second: {e['fps']}\n"
        '- Every recorded frame is supplied. Each image contains native camera panels side by side.\n'
        '- Read panels left to right in the camera order below; black padding is not scene content.\n'
        '- Encoded frame clocks align; physical capture synchronization is not independently verified.\n\n'
        + '\n'.join(f"- {c['camera']}: {c['description']}" for c in e['cameras']))
    content = [dict(type='input_text', text=(root / 'prompt.md').read_text(encoding='utf-8') + info)]
    for image in e['images']:
        path = common.inside(root, image['path'])
        if common.sha(path) != image['sha256']:
            raise ValueError('Changed visual evidence')
        content.extend([dict(type='input_text', text=f"Frame {image['frame']} | {image['seconds']:.6f} seconds"),
            dict(type='input_image', image_url='data:image/webp;base64,' + base64.b64encode(path.read_bytes()).decode(), detail='high')])
    return dict(model=m['model'], input=[dict(role='user', content=content)],
        reasoning=dict(effort=m['reasoning_effort']), max_output_tokens=m['max_output_tokens'],
        text=dict(format=dict(type='text')), truncation='disabled', store=False)


def preflight(root):
    m = manifest(root); client = Gateway(); rows = []
    for e in m['episodes']:
        path = root / 'requests' / (e['id'] + '_astra.json')
        if path.exists():
            body = common.read(path)
        else:
            body = payload(root, m, e); write_once(path, body)
        receipt = root / 'preflight' / (e['id'] + '.json')
        if receipt.exists():
            row = common.read(receipt)
            if row['request_sha256'] != common.sha(path):
                raise ValueError('Changed request')
        else:
            count = client.post('/v1/responses/input_tokens',
                {k: body[k] for k in ('model', 'input', 'reasoning', 'text', 'truncation')}, uuid.uuid4().hex)
            tokens = count['input_tokens']
            if type(tokens) is not int or not 0 < tokens <= 1038000:
                raise ValueError('Context exceeds Astra capacity; no truncation or pilot replacement')
            multiplier = 2 if tokens > 272000 else 1
            ceiling = (tokens * 12.5 * multiplier + m['max_output_tokens'] * 50 * (1.5 if multiplier == 2 else 1)) / 1e6
            row = dict(episode=e['id'], input_tokens=tokens, request_sha256=common.sha(path), conservative_ceiling_usd=ceiling, response=count)
            write_once(receipt, row)
        rows.append(row); print(e['id'] + ': ' + str(row['input_tokens']) + ' input tokens', flush=True)
    write_once(root / 'token_preflight.json', dict(manifest_sha256=common.sha(root / 'manifest.json'), complete=True,
        requests=rows, pilot_ceiling_usd=sum(r['conservative_ceiling_usd'] for r in rows),
        pricing_source='https://developers.openai.com/api/docs/models/gpt-6-astra', pricing_checked='2026-11-12',
        rates_per_million=dict(input=10, cached=1, cache_write=12.5, output=50),
        portkey_fees_included=False))


def label(root, budget):
    m = manifest(root); pf = common.read(root / 'token_preflight.json')
    collection = common.read(root / 'collection_verified.json')
    if collection['selection_sha256'] != m['selection_sha256'] or collection['episodes'] != 1000 or not collection['all_source_checksums_match']:
        raise ValueError('Complete 1000-episode Corral collection required before pilot labeling')
    if not pf['complete'] or pf['manifest_sha256'] != common.sha(root / 'manifest.json') or pf['pilot_ceiling_usd'] > budget:
        raise ValueError('Pilot preflight incomplete, changed, or above the supplied budget')
    lock = root / 'pilot.lock'
    with lock.open('x') as stream:
        stream.write(now())
    try:
        client = Gateway()
        for e, row in zip(m['episodes'], pf['requests']):
            folder = root / 'traces' / (e['id'] + '_astra')
            if (folder / 'status.json').exists():
                continue
            if (folder / 'attempt.json').exists():
                raise ValueError('Existing uncompleted attempt; inspect before any resend: ' + e['id'])
            path = root / 'requests' / (e['id'] + '_astra.json')
            if row['episode'] != e['id'] or common.sha(path) != row['request_sha256']:
                raise ValueError('Changed frozen pilot request')
            request_id = uuid.uuid4().hex
            write_once(folder / 'attempt.json', dict(started_utc=now(), request_id=request_id, request_sha256=row['request_sha256'], gateway='Portkey'))
            try:
                raw = client.post('/v1/responses', common.read(path), request_id)
                write_once(folder / 'response.json', raw)
                text, completed = transport.extract_answer('openai', raw)
                (folder / 'annotation.md').write_text(text, encoding='utf-8')
                if not completed:
                    raise ValueError('Model response incomplete; native output preserved')
                value = schema.parse(text, e)
                write_once(folder / 'parsed.json', value)
                write_once(folder / 'status.json', dict(status='validated', usage=raw.get('usage'), model=raw.get('model'), completed_utc=now()))
                print(e['id'] + ': native Markdown validated', flush=True)
                review(root)
            except Exception as error:
                write_once(folder / 'error.json', dict(error=str(error), stopped_utc=now(), automatically_retried=False))
                raise
    finally:
        lock.unlink()


def review(root):
    m = manifest(root); episodes = []; ready = 0
    for e in m['episodes']:
        folder = root / 'traces' / (e['id'] + '_astra'); traces = []
        if (folder / 'status.json').exists():
            text = (folder / 'annotation.md').read_text(encoding='utf-8')
            value = schema.parse(text, e); ready += 1
            traces.append(dict(repeat=1, **value, native_markdown=text,
                markdown=f'traces/{folder.name}/annotation.md'))
        episodes.append(dict(id=e['id'], task=e['task'], split='review', lab=e['lab'], fps=e['fps'],
            n_frames=e['n_frames'], videos=e['videos'], teachers={'v8': traces}, source_run=root.name))
    template = Path(__file__).with_name('corral_astra_v8_2_review.html')
    data = dict(protocol=m['protocol'], prompt_revision='V8.2', manifest_sha256=common.sha(root / 'manifest.json'),
        review_ui_version=common.sha(template), repeats=1, planned_responses=10,
        side_labels={'v8': 'V8.2 - Astra'}, side_repeats={'v8': 1},
        rich_prompt_description='Fresh Corral sample; episode outcome, failure taxonomy, recovery, severity and resetability.', episodes=episodes)
    encoded = json.dumps(data, ensure_ascii=False).replace('<', '\\u003c').replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')
    transport.atomic_json(root / 'review_data.json', data)
    temp = root / 'review.html.tmp'; temp.write_text(template.read_text(encoding='utf-8').replace('__DATA__', encoded), encoding='utf-8'); temp.replace(root / 'review.html')
    lines = ['# Fresh Corral Astra pilot', '', f'{ready}/10 native Markdown annotations validated. The 990 other sampled episodes remain unlabeled.', '',
        'Review video and time-aligned failure cards at the ordinary review.html URL. Teacher labels require human review.', '',
        '| Episode | Task/outcome | Native annotation |', '| --- | --- | --- |']
    for e in episodes:
        trace = e['teachers']['v8']
        lines.append(f"| {e['id']} | {trace[0]['success_label'] if trace else 'Pending'} | " +
            (f"[Markdown]({trace[0]['markdown']})" if trace else 'Pending') + ' |')
    (root / 'report.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'Review published: {ready}/10 labels ready', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['plan', 'fetch', 'prepare', 'preflight', 'label', 'review'])
    parser.add_argument('--run', type=Path, default=DEFAULT)
    parser.add_argument('--corral-release-root')
    parser.add_argument('--seed', type=int)
    parser.add_argument('--budget-usd', type=float)
    args = parser.parse_args(); root = args.run.resolve()
    if args.command == 'plan':
        if not args.corral_release_root:
            parser.error('plan requires --corral-release-root, the verified directory containing labs/')
        plan(root, args.corral_release_root, args.seed)
    elif args.command == 'label':
        if args.budget_usd is None:
            parser.error('label requires --budget-usd')
        label(root, args.budget_usd)
    else:
        globals()[args.command](root)
