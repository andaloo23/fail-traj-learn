"""Versioned Astra V8.2 expansion of the reviewed, frozen Corral sample.

Retains all native video observations. Reuses the ten native pilot responses;
never regenerates them. Batch requests use explicit caching of shared text only.
Oversized episodes are held rather than silently sampled, truncated or excluded.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import statistics
import time
import urllib.error
import urllib.request
import uuid

import av
import h5py
from PIL import Image

import oopsie_common as common
import annotation_runtime as transport
import corral_astra_v8_2 as pilot
from oopsie_bulk_v8_1 import write_once
import rich_failure_v8_2 as schema

ROOT = pilot.ROOT
SOURCE = pilot.DEFAULT
DEFAULT = ROOT / 'outputs/corral_astra_rich_failure_v8_2_1000_batch_v2'
MODEL = 'gpt-6-astra'
MAX_INPUT = 922000
MAX_IMAGES = 1500
# Empirically successful JSON requests reach 71 MB; requests over 120 MB
# repeatedly failed at the gateway. This is a conservative transport policy,
# not a claimed provider specification. File-ID inputs retain exact pixels.
MAX_INLINE_REQUEST_BYTES = 75_000_000
TERMINAL = {'completed', 'failed', 'expired', 'cancelled'}


def now():
    return datetime.now(timezone.utc).isoformat()


def compact(value):
    return json.dumps(value, separators=(',', ':'), ensure_ascii=False).encode('utf-8')


def link_file(source, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        if common.sha(source) != common.sha(dest):
            raise ValueError('Different existing artifact: ' + str(dest))
        return
    os.link(source, dest)


def initialize(root, source=SOURCE, budget=800):
    selection = pilot.verified_selection(source)
    receipt = common.read(source / 'collection_verified.json')
    if receipt['selection_sha256'] != common.sha(source / 'selection.json') or not receipt['all_source_checksums_match']:
        raise ValueError('Unverified source collection')
    if root.exists():
        raise ValueError('Version already exists; resume its commands')
    root.mkdir(parents=True)
    for name in ('prompt.md', 'selection.json', 'collection_verified.json'):
        shutil.copyfile(source / name, root / name)
    # Media are immutable content-addressed originals. Hard links avoid another
    # collection and retain the URLs consumed by the established video reviewer.
    for p in (source / 'source_files').iterdir():
        link_file(p, root / 'source_files' / p.name)
    imported = []
    for e in common.read(source / 'manifest.json')['episodes']:
        eid = e['id']; folder = source / 'traces' / (eid + '_astra')
        status = common.read(folder / 'status.json')
        if status['model'] != MODEL or status['status'] != 'validated':
            raise ValueError('Pilot teacher identity or validity differs')
        schema.parse((folder / 'annotation.md').read_text(encoding='utf-8'), e)
        for image in e['images']:
            link_file(source / image['path'], root / image['path'])
        write_once(root / 'prepared' / (eid + '.json'), e)
        for p in folder.iterdir():
            if p.is_file():
                dest = root / 'traces' / folder.name / p.name
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(p, dest)
        imported.append(dict(episode=eid, source_run=source.name,
            response_sha256=common.sha(folder / 'response.json'),
            request_sha256=common.sha(source / 'requests' / (eid + '_astra.json')),
            recorded_model=status['model']))
    write_once(root / 'run_plan.json', dict(protocol='corral_astra_rich_failure_v8_2_batch_v2',
        created_utc=now(), authorization='User approved the 1000-episode dataset after reviewing the ten-episode Astra pilot.',
        source_run=str(source.resolve()), selection_sha256=common.sha(root / 'selection.json'),
        prompt_sha256=common.sha(root / 'prompt.md'), model=MODEL, budget_usd=budget,
        reasoning_effort='low', max_output_tokens=12000, max_input_tokens=MAX_INPUT,
        prompt_cache_options=dict(mode='explicit', ttl='30m'), batch_discount=0.5,
        generation_retries=0, sampling='none; every native video frame',
        imported_pilot=imported, planned_new_episode_count=990,
        source_annotations_used_as_model_input=False))
    print('Initialized same 1000-episode selection; ten reviewed pilot labels reused.', flush=True)


class FullPreparation(pilot.CorralPreparation):
    def episode(self, item):
        counts = []
        for relative in json.loads(item['video_reference_paths_json']):
            meta = self.files[relative]
            with av.open(str(self.download(relative, meta['sha256'], meta['bytes']))) as container:
                stream = container.streams.video[0]
                counts.append(stream.frames or sum(1 for _ in container.decode(video=0)))
        states = int(item['timestep_count'])
        if not counts or len(set(counts)) != 1 or abs(counts[0] - states) > 1:
            raise ValueError('Unresolved camera timelines: ' + item['id'])
        return self.decode_native(item, counts[0], states)

    def decode_native(self, item, count, states):
        eid = item['id']
        meta = self.files[item['release_path']]
        hdf5 = self.download(item['release_path'], meta['sha256'], meta['bytes'])
        refs = []
        with h5py.File(hdf5, 'r') as source:
            task = source.attrs['language_instruction']
            if isinstance(task, bytes): task = task.decode()
            for camera, value in source['observations/video_paths'].items():
                import posixpath
                native = value[()]
                if isinstance(native, bytes): native = native.decode()
                relative = posixpath.normpath(posixpath.join(posixpath.dirname(item['release_path']), native.replace('\\', '/')))
                if relative not in json.loads(item['video_reference_paths_json']):
                    raise ValueError('Unpinned video path')
                refs.append((camera, relative))
        if not isinstance(task, str) or not task.strip(): raise ValueError('Missing native task')
        selected = []; seen = set(); duplicates = []; containers = []
        try:
            for camera, relative in refs:
                meta = self.files[relative]
                if meta['sha256'] in seen:
                    duplicates.append(dict(camera=camera, path=relative, sha256=meta['sha256'])); continue
                seen.add(meta['sha256'])
                path = self.download(relative, meta['sha256'], meta['bytes'])
                container = av.open(str(path)); containers.append(container)
                stream = container.streams.video[0]
                selected.append(dict(camera=camera, relative=relative, sha256=meta['sha256'],
                    path=path, frames=iter(container.decode(video=0)), fps=float(stream.average_rate),
                    duration=float(stream.duration*stream.time_base) if stream.duration else None))
            images = []; clocks = []; previous = [-1.0] * len(selected)
            folder = self.root / 'images' / eid; folder.mkdir(parents=True, exist_ok=True)
            for index in range(count):
                panels = []; positions = []; times = []; x = 0
                for k, camera in enumerate(selected):
                    frame = next(camera['frames'], None)
                    if frame is None or frame.pts is None: raise ValueError('Missing native frame/timestamp')
                    seconds = float(frame.pts * frame.time_base)
                    if seconds <= previous[k]: raise ValueError('Non-monotonic native video clock')
                    previous[k] = seconds; times.append(seconds)
                    image = frame.to_image().convert('RGB')
                    image.thumbnail((280, 280), Image.Resampling.LANCZOS)
                    jpeg = io.BytesIO(); image.save(jpeg, format='JPEG', quality=95)
                    image = Image.open(io.BytesIO(jpeg.getvalue())).convert('RGB')
                    positions.append(dict(camera=camera['camera'], x=x, y=0, width=image.width, height=image.height))
                    panels.append(image); x += image.width
                if max(times) - min(times) > .001:
                    raise ValueError('Native camera clocks differ by more than 1ms')
                if index == 0 and abs(times[0]) > .001:
                    raise ValueError('Nonzero video timeline origin requires explicit alignment')
                strip = Image.new('RGB', (x, max(p.height for p in panels)), 'black')
                for image, pos in zip(panels, positions): strip.paste(image, (pos['x'], 0))
                path = folder / f'{index:06d}.webp'
                # An interrupted preparation may leave a prefix. Recompute it
                # deterministically and retain matching evidence unchanged.
                if path.exists():
                    with Image.open(path) as old:
                        if old.convert('RGB').tobytes() != strip.tobytes():
                            raise ValueError('Existing frame pixels differ')
                else:
                    strip.save(path, format='WEBP', lossless=True, method=0)
                images.append(dict(frame=index, seconds=times[0], camera='all camera panels',
                    path=path.relative_to(self.root).as_posix(), sha256=common.sha(path),
                    rgb_sha256=hashlib.sha256(strip.tobytes()).hexdigest(), panels=positions, bytes=path.stat().st_size))
                clocks.append(times[0])
            if any(next(c['frames'], None) is not None for c in selected): raise ValueError('Uncounted source frames')
            period = statistics.median(b-a for a,b in zip(clocks, clocks[1:])) if count > 1 else 1 / selected[0]['fps']
            return dict(status='prepared', id=eid, release_path=item['release_path'], hdf5_sha256=common.sha(hdf5),
                hdf5_file=hdf5.relative_to(self.root).as_posix(), lab=item['lab'], split='review', task=task,
                n_frames=count, source_timestep_count=states, video_frame_count=count,
                fps=selected[0]['fps'], frame_times=clocks, duration_seconds=selected[0]['duration'] or clocks[-1]+period,
                frame_alignment_note='Every native video observation retained; source presentation timestamps supplied. Robot state count is separate metadata.',
                cameras=[dict(camera=c['camera'], description='Native camera identifier '+c['camera']+'; no unverified geometric role assigned.') for c in selected],
                videos=[dict(camera=c['camera'], description='Native camera identifier '+c['camera'],
                    url=c['path'].relative_to(self.root).as_posix(), original_release_path=c['relative'], sha256=c['sha256']) for c in selected],
                duplicate_cameras_excluded=duplicates, images=images, source_annotations_used_as_model_input=False)
        finally:
            for container in containers: container.close()


_builder = None


def worker_init(root):
    global _builder
    _builder = FullPreparation(root, pilot.verified_selection(root))


def prepare_one(item):
    try:
        result = _builder.episode(item)
    except (ValueError, OSError, av.error.FFmpegError) as error:
        result = dict(id=item['id'], status='technical_issue', error=str(error))
    transport.atomic_json(_builder.root / 'prepared' / (item['id'] + '.json'), result)
    return item['id'], result['status'], result.get('n_frames', 0), result.get('error')


def prepare(root, workers=8):
    selection = pilot.verified_selection(root)
    pending = []
    for e in selection['episodes']:
        path = root / 'prepared' / (e['id'] + '.json')
        if path.exists() and common.read(path)['status'] != 'prepared':
            archive = root / 'preparation_attempts' / (e['id']+'_'+uuid.uuid4().hex+'.json')
            archive.parent.mkdir(exist_ok=True); shutil.copyfile(path, archive)
            pending.append(e)
            continue
        if not path.exists(): pending.append(e)
    with ProcessPoolExecutor(max_workers=workers, initializer=worker_init, initargs=(root,)) as pool:
        futures = [pool.submit(prepare_one, e) for e in pending]
        done = 1000 - len(pending)
        for future in as_completed(futures):
            eid, state, frames, error = future.result(); done += 1
            print(f'{done}/1000 {eid}: {state}, {frames} frames' + (': ' + str(error) if error else ''), flush=True)
    episodes = [common.read(root / 'prepared' / (e['id'] + '.json')) for e in selection['episodes']]
    failures = [dict(id=e['id'], error=e.get('error')) for e in episodes if e['status'] != 'prepared']
    transport.atomic_json(root / 'preparation_audit.json', dict(episodes=1000, failures=failures,
        retained_video_frames=sum(e.get('n_frames', 0) for e in episodes)))
    if failures:
        raise ValueError('Technical preparation failures preserved; no episode replacement: ' + str(failures))
    plan = common.read(root / 'run_plan.json')
    write_once(root / 'manifest.json', dict(protocol=plan['protocol'], annotation_schema=schema.SCHEMA,
        selection_sha256=plan['selection_sha256'], prompt_sha256=plan['prompt_sha256'],
        run_plan_sha256=common.sha(root / 'run_plan.json'), model=MODEL,
        reasoning_effort='low', max_output_tokens=12000, max_camera_image_side=280,
        source_annotations_used_as_model_input=False, episodes=episodes))


class Gateway:
    def __init__(self):
        config = pilot.Gateway()
        self.key, self.provider = config.key, config.provider

    def api(self, method, path, body=None, raw=False, content_type='application/json', request_id=None):
        import re
        if path != '/v1/responses/input_tokens' and not re.fullmatch(r'/v1/(files|batches)(/[A-Za-z0-9_-]+)?(/content)?', path):
            raise ValueError('Unexpected Portkey path')
        request_id = request_id or uuid.uuid4().hex
        headers = {'x-portkey-api-key':self.key, 'x-portkey-provider':self.provider,
            'x-portkey-retry-count':'0', 'x-portkey-trace-id':request_id,
            'X-Client-Request-Id':request_id, 'User-Agent':'Mozilla/5.0', 'Accept':'application/json'}
        data = compact(body) if isinstance(body, dict) else body
        if data is not None: headers['Content-Type'] = content_type
        if method == 'POST': headers['Idempotency-Key'] = request_id
        request = urllib.request.Request('https://api.portkey.ai'+path, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=600) as response:
                value = response.read()
            return value if raw else json.loads(value)
        except urllib.error.HTTPError as error:
            message = error.read().decode(errors='replace').replace(self.key,'[REDACTED]')
            raise RuntimeError(f'Portkey HTTP {error.code}: {message[:1600]}') from None
        except (OSError, ValueError) as error:
            raise RuntimeError(type(error).__name__+'; outcome unknown; no automatic resend') from None

    def upload(self, path, request_id, purpose='batch'):
        boundary = 'corral-'+uuid.uuid4().hex
        mime=({'webp':'image/webp','png':'image/png','jpg':'image/jpeg'}[path.suffix.lstrip('.')]
            if purpose=='vision' else 'application/jsonl')
        prefix = (f'--{boundary}\r\nContent-Disposition: form-data; name="purpose"\r\n\r\n{purpose}\r\n'
            f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{path.name}"\r\n'
            f'Content-Type: {mime}\r\n\r\n').encode()
        data = prefix+path.read_bytes()+f'\r\n--{boundary}--\r\n'.encode()
        value = self.api('POST','/v1/files',data,content_type='multipart/form-data; boundary='+boundary,request_id=request_id)
        if not value.get('id') or value.get('bytes') != path.stat().st_size:
            raise ValueError('Upload receipt does not match batch file')
        return value


def verify_plan(root):
    plan = common.read(root/'run_plan.json')
    if plan['model'] != MODEL or plan['source_annotations_used_as_model_input']:
        raise ValueError('Wrong model or source annotation leakage')
    if common.sha(root/'selection.json') != plan['selection_sha256'] or common.sha(root/'prompt.md') != plan['prompt_sha256']:
        raise ValueError('Frozen sample or prompt changed')
    return plan


def usage_cost(usage, batch_mode=True):
    details=usage.get('input_tokens_details') or {}
    cached=details.get('cached_tokens',0);writes=details.get('cache_write_tokens',0)
    tokens=usage['input_tokens'];output=usage['output_tokens']
    if min(tokens,output,cached,writes)<0 or cached+writes>tokens:
        raise ValueError('Invalid native usage accounting')
    multiplier=2 if tokens>272000 else 1
    return ((tokens-cached-writes)*10+cached+writes*12.5)*multiplier/(2e6 if batch_mode else 1e6)+output*(75 if multiplier==2 else 50)/(2e6 if batch_mode else 1e6)


def batch_ceiling(tokens, shared_tokens=4096, output_tokens=12000):
    multiplier = 2 if tokens > 272000 else 1
    # Explicit-only mode: only the shared prefix can incur 1.25x writes.
    # Assume no cache hits and conservatively overestimate its length.
    return ((tokens*10+min(tokens,shared_tokens)*2.5)*multiplier+
        output_tokens*(75 if multiplier==2 else 50))/2e6


def payload(root, episode):
    metadata = dict(model=MODEL, reasoning_effort='low', max_output_tokens=12000)
    body = pilot.payload(root, metadata, episode)
    content = body['input'][0]['content']; prompt = (root/'prompt.md').read_text(encoding='utf-8')
    if not content[0]['text'].startswith(prompt): raise ValueError('Wrong shared prompt')
    info = content[0]['text'][len(prompt):]
    content[:1] = [dict(type='input_text', text=prompt, prompt_cache_breakpoint=dict(mode='explicit')),
        dict(type='input_text', text=info)]
    body['prompt_cache_options'] = dict(mode='explicit',ttl='30m')
    return body


def frozen_request_path(root, row):
    return common.inside(root,row.get('request_path','requests/'+row['episode']+'_astra.json'))


def upload_immutable_file(root, client, path, request_id, purpose):
    """Retry immutable staging only; this endpoint cannot generate labels.

    The same idempotency key and exact file bytes are reused. All failures are
    retained; a duplicate staging file is harmless if a provider ignores the key.
    Batch creation and generation submissions are never retried here.
    """
    for attempt in range(3):
        try:return client.upload(path,request_id,purpose=purpose)
        except RuntimeError as error:
            transient=any(code in str(error) for code in ('HTTP 408','HTTP 429','HTTP 500','HTTP 502','HTTP 503','HTTP 504','URLError','Invalid file format application/octet-stream'))
            write_once(root/'upload_attempts'/(uuid.uuid4().hex+'.json'),dict(path=str(path.relative_to(root)),
                request_id=request_id,purpose=purpose,error=str(error),recorded_utc=now(),attempt=attempt+1,
                generation_submitted=False,duplicate_staging_file_possible=transient))
            if not transient or attempt==2:raise
            time.sleep(2**attempt)


def file_id_payload(root, episode, body, max_bytes=175_000_000):
    """Replace only transport bytes. Uploaded WEBPs are byte-identical evidence."""
    from concurrent.futures import ThreadPoolExecutor
    content=body['input'][0]['content']
    slots=[i for i,x in enumerate(content) if x['type']=='input_image']
    if len(slots)!=len(episode['images']):raise ValueError('Image/frame mapping differs')
    size=len(compact(body));candidates=sorted(((len(content[slot]['image_url']),i,slot) for i,slot in enumerate(slots)),reverse=True)
    chosen=[];saved=0
    for length,index,slot in candidates:
        if size-saved<max_bytes-4096:break
        chosen.append((index,slot));saved+=length-256
    def upload_one(pair):
        index,slot=pair;image=episode['images'][index];path=common.inside(root,image['path'])
        if common.sha(path)!=image['sha256']:raise ValueError('Changed upload evidence')
        receipt=root/'image_uploads'/(episode['id']+f'_{index:06d}.json')
        if receipt.exists():
            value=common.read(receipt)
            if value['image_sha256']!=image['sha256']:
                raise ValueError('Uploaded image source differs')
        else:
            value=dict(status='uploading',request_id=uuid.uuid4().hex,image_sha256=image['sha256'],image_path=image['path'])
            write_once(receipt,value)
        if value['status']!='uploaded':
            try:
                try:
                    value['response']=upload_immutable_file(root,Gateway(),path,value['request_id'],purpose='vision')
                except RuntimeError as error:
                    if 'Invalid file format application/octet-stream' not in str(error):raise
                    # Some valid lossless WEBPs fail provider MIME detection.
                    # A PNG transport copy preserves every decoded RGB pixel.
                    png=root/'transport_images'/episode['id']/(path.stem+'.png')
                    png.parent.mkdir(parents=True,exist_ok=True)
                    with Image.open(path) as source:
                        rgb=source.convert('RGB');pixels=rgb.tobytes();rgb.save(png,format='PNG',compress_level=3)
                    with Image.open(png) as decoded:
                        if decoded.convert('RGB').tobytes()!=pixels:raise ValueError('Lossless PNG pixels differ')
                    value.update(original_format_error=str(error),transport_path=png.relative_to(root).as_posix(),
                        transport_sha256=common.sha(png),transport_rgb_sha256=hashlib.sha256(pixels).hexdigest(),
                        fallback_request_id=value.get('fallback_request_id') or uuid.uuid4().hex)
                    transport.atomic_json(receipt,value)
                    value['response']=upload_immutable_file(root,Gateway(),png,value['fallback_request_id'],purpose='vision')
                value['status']='uploaded'
            except Exception as error:
                value['error']=str(error);raise
            finally:transport.atomic_json(receipt,value)
        return slot,dict(type='input_image',file_id=value['response']['id'],detail=content[slot]['detail'])
    with ThreadPoolExecutor(max_workers=4) as pool:
        for slot,image in pool.map(upload_one,chosen):content[slot]=image
    if len(compact(body))>=max_bytes:raise ValueError('File-ID request still exceeds batch transport limit')
    return body


def preflight_one(root, episode):
    verify_plan(root)
    eid = episode['id']; receipt = root/'preflight'/(eid+'.json')
    request = root/'requests'/(eid+'_astra.json')
    if receipt.exists():
        row=common.read(receipt)
        if common.sha(frozen_request_path(root,row))!=row['request_sha256']: raise ValueError('Frozen request changed')
        return row
    if len(episode['images']) > MAX_IMAGES:
        raise ValueError('Image limit; packaging choice pending: '+eid)
    if request.exists(): body=common.read(request)
    else:
        body=payload(root,episode); request.parent.mkdir(exist_ok=True)
        with request.open('xb') as f: f.write(compact(body))
    if request.stat().st_size > MAX_INLINE_REQUEST_BYTES:
        # Preserve the original inline request, and freeze a separate exact-
        # image transport variant. No prior generation request is overwritten.
        request=root/'requests'/(eid+'_astra_fileids_50mb.json')
        if request.exists():body=common.read(request)
        else:
            body=file_id_payload(root,episode,body,max_bytes=50_000_000)
            with request.open('xb') as f:f.write(compact(body))
    # The token-count endpoint accepts the visual/text input, but not the
    # generation endpoint's cache policy. Cache options remain in the frozen
    # generation request; omitting them here does not change visible tokens.
    count_body={k:body[k] for k in ('model','input','reasoning','text','truncation')}
    for attempt in range(3):
        try:
            count=Gateway().api('POST','/v1/responses/input_tokens',count_body)
            break
        except RuntimeError as error:
            transient=any(code in str(error) for code in ('HTTP 408','HTTP 429','HTTP 500','HTTP 502','HTTP 503','HTTP 504'))
            write_once(root/'preflight_attempts'/(eid+'_'+uuid.uuid4().hex+'.json'),
                dict(error=str(error),recorded_utc=now(),generation_submitted=False,transient=transient,attempt=attempt+1))
            if not transient or attempt==2:raise
            time.sleep(2**attempt)
    tokens=count['input_tokens']
    if type(tokens) is not int or not 0<tokens<=MAX_INPUT:
        raise ValueError('Context limit; no truncation: '+eid+': '+str(tokens))
    row=dict(episode=eid,input_tokens=tokens,request_path=request.relative_to(root).as_posix(),request_sha256=common.sha(request),
        prepared_sha256=common.sha(root/'prepared'/(eid+'.json')),
        request_bytes=request.stat().st_size,image_count=len(episode['images']),
        conservative_batch_ceiling_usd=batch_ceiling(tokens),response=count)
    write_once(receipt,row)
    return row


def freeze_shard(root, rows):
    folder=root/'batch_inputs'; folder.mkdir(exist_ok=True)
    # UUID names do not collide with a previously frozen batch after a restart.
    path=folder/('batch_'+uuid.uuid4().hex+'.jsonl')
    with path.open('xb') as f:
        for row in rows:
            request=frozen_request_path(root,row)
            if common.sha(request)!=row['request_sha256']: raise ValueError('Frozen request changed')
            if common.sha(root/'prepared'/(row['episode']+'.json'))!=row['prepared_sha256']:
                raise ValueError('Prepared evidence record changed')
            body=common.read(request)
            f.write(compact(dict(custom_id=row['episode']+'_astra_r01',method='POST',url='/v1/responses',body=body))+b'\n')
    shard=dict(path=path.relative_to(root).as_posix(),sha256=common.sha(path),
        bytes=path.stat().st_size,episodes=[r['episode'] for r in rows],input_tokens=sum(r['input_tokens'] for r in rows),
        conservative_batch_ceiling_usd=sum(r['conservative_batch_ceiling_usd'] for r in rows),
        endpoint='/v1/responses',completion_window='24h',model=MODEL,
        run_plan_sha256=common.sha(root/'run_plan.json'))
    write_once(root/'prepared_shards'/(path.stem+'.json'),shard)
    return shard


def freeze_available(root, assigned):
    available=[common.read(p) for p in sorted((root/'preflight').glob('*.json'))]
    group=[];size=tokens=0
    for row in available:
        if row['episode'] in assigned:continue
        if group and (size+row['request_bytes']+1024>185_000_000 or tokens+row['input_tokens']>1_000_000):
            freeze_shard(root,group);group=[];size=tokens=0
        group.append(row);size+=row['request_bytes']+1024;tokens+=row['input_tokens']
    if group:freeze_shard(root,group)


def submit_shard(root, shard, client):
    plan=verify_plan(root)
    path=root/shard['path']; stem=path.stem
    journal=root/'batch_jobs'/(stem+'.json')
    if journal.exists(): raise ValueError('Existing submission journal; no resend')
    if common.sha(path)!=shard['sha256'] or shard['run_plan_sha256']!=common.sha(root/'run_plan.json'):
        raise ValueError('Changed frozen batch')
    committed=sum(common.read(p)['shard']['conservative_batch_ceiling_usd'] for p in (root/'batch_jobs').glob('*.json'))
    if committed+shard['conservative_batch_ceiling_usd']>plan['budget_usd']:
        raise ValueError('Conservative committed cost would exceed run budget')
    state=dict(status='uploading',started_utc=now(),shard=shard,
        upload_request_id=uuid.uuid4().hex,submit_request_id=uuid.uuid4().hex)
    write_once(journal,state)
    try:
        state['upload']=upload_immutable_file(root,client,path,state['upload_request_id'],purpose='batch')
        state['status']='submitting';transport.atomic_json(journal,state)
        if (root/'STOP_REQUESTED.json').exists(): raise ValueError('Stop requested before submission')
        state['batch']=client.api('POST','/v1/batches',dict(input_file_id=state['upload']['id'],
            endpoint='/v1/responses',completion_window='24h',metadata=dict(protocol=plan['protocol'],shard=stem)),
            request_id=state['submit_request_id'])
        state['status']='submitted';state['submitted_utc']=now()
    except Exception as error:
        state.update(status='submission_unresolved',error=str(error));raise
    finally:
        transport.atomic_json(journal,state)
    print('Submitted Astra batch: '+str(len(shard['episodes']))+' episodes, '+state['batch']['id'],flush=True)


def ingest(root, state, value):
    expected={eid+'_astra_r01':eid for eid in state['shard']['episodes']}
    seen=set()
    for line in value.splitlines():
        if not line.strip(): continue
        envelope=json.loads(line);cid=envelope['custom_id']
        if cid not in expected or cid in seen: raise ValueError('Unknown/duplicate batch output ID')
        seen.add(cid);eid=expected[cid];folder=root/'traces'/(eid+'_astra')
        write_once(folder/'batch_envelope.json',envelope)
        if (folder/'status.json').exists() or (folder/'error.json').exists(): continue
        try:
            result=envelope.get('response') or {}
            if result.get('status_code')!=200 or envelope.get('error'):
                raise ValueError('Batch item rejected: '+str(envelope.get('error') or result)[:1200])
            raw=result['body'];write_once(folder/'response.json',raw)
            text,complete=transport.extract_answer('openai',raw)
            (folder/'annotation.md').write_text(text,encoding='utf-8')
            model=raw.get('model')
            if not model or not (model==MODEL or model.startswith(MODEL+'-')):
                raise ValueError('Unexpected native teacher model: '+str(model))
            if not complete: raise ValueError('Incomplete native response')
            episode=common.read(root/'prepared'/(eid+'.json'))
            parsed=schema.parse(text,episode);write_once(folder/'parsed.json',parsed)
            write_once(folder/'status.json',dict(status='validated',model=model,usage=raw.get('usage'),
                batch_id=state['batch']['id'],completed_utc=now()))
        except Exception as error:
            write_once(folder/'error.json',dict(error=str(error),automatic_resend=False,recorded_utc=now()))
            if 'Unexpected native teacher' in str(error) or any(x in str(error).lower() for x in ('billing','quota','insufficient_quota')):
                raise
    return seen


def collect(root, client):
    active_tokens=0;active=0
    for path in sorted((root/'batch_jobs').glob('*.json')):
        state=common.read(path)
        if state['status']=='collected': continue
        if 'batch' not in state: raise ValueError('Unresolved submission journal; no automatic resend: '+path.name)
        state['batch']=client.api('GET','/v1/batches/'+state['batch']['id'])
        if state['batch']['status'] not in TERMINAL:
            active_tokens+=state['shard']['input_tokens'];active+=len(state['shard']['episodes'])
        else:
            all_seen=set()
            for field in ('output_file_id','error_file_id'):
                file_id=state['batch'].get(field)
                if not file_id:continue
                dest=root/'batch_outputs'/(path.stem+'_'+field+'.jsonl');dest.parent.mkdir(exist_ok=True)
                if dest.exists():value=dest.read_bytes()
                else:
                    value=client.api('GET','/v1/files/'+file_id+'/content',raw=True)
                    with dest.open('xb') as f:f.write(value)
                all_seen|=ingest(root,state,value)
            for eid in state['shard']['episodes']:
                if eid+'_astra_r01' not in all_seen:
                    write_once(root/'traces'/(eid+'_astra')/'error.json',dict(error='No batch output returned',
                        remote_batch_status=state['batch']['status'],automatic_resend=False))
            state['status']='collected';state['collected_utc']=now()
        transport.atomic_json(path,state)
    return active,active_tokens


def catalog(root):
    path=root/'episode_catalog.json'
    if path.exists(): return common.read(path)
    import posixpath
    s=pilot.verified_selection(root);values=[]
    for e in s['episodes']:
        meta=s['files'][e['release_path']];p=pilot.source_path(root,e['release_path'],meta)
        with h5py.File(p,'r') as source:
            task=source.attrs['language_instruction']
            if isinstance(task,bytes):task=task.decode()
            videos=[]
            for camera,item in source['observations/video_paths'].items():
                rel=item[()]
                if isinstance(rel,bytes):rel=rel.decode()
                rel=posixpath.normpath(posixpath.join(posixpath.dirname(e['release_path']),rel.replace('\\','/')))
                vm=s['files'][rel];vp=pilot.source_path(root,rel,vm)
                videos.append(dict(camera=camera,description='Native camera identifier '+camera,
                    url=vp.relative_to(root).as_posix(),sha256=vm['sha256']))
            with av.open(str(root/videos[0]['url'])) as c:
                v=c.streams.video[0];fps=float(v.average_rate);frames=v.frames
        values.append(dict(id=e['id'],lab=e['lab'],split='review',task=task,fps=fps,n_frames=frames,videos=videos))
    write_once(path,values);return values


def publish(root, message=''):
    episodes=[];ready=0;errors=0
    source_manifest=common.sha(Path(common.read(root/'run_plan.json')['source_run'])/'manifest.json')
    for item in catalog(root):
        e=dict(item);eid=e['id'];p=root/'prepared'/(eid+'.json')
        if p.exists():
            prepared=common.read(p)
            if prepared['status']=='prepared':
                for key in ('fps','n_frames','videos','frame_times','duration_seconds'):
                    if key in prepared:e[key]=prepared[key]
        folder=root/'traces'/(eid+'_astra');traces=[]
        if (folder/'status.json').exists():
            value=common.read(folder/'parsed.json');text=(folder/'annotation.md').read_text(encoding='utf-8')
            traces.append(dict(repeat=1,**value,native_markdown=text,markdown=f'traces/{folder.name}/annotation.md'));ready+=1
        if (folder/'error.json').exists():errors+=1
        e.update(teachers={'v8':traces},source_run=root.name)
        if eid in {f'C{i:04d}' for i in range(1,11)}:
            e.update(source_run=SOURCE.name,source_manifest_sha256=source_manifest)
        episodes.append(e)
    template=Path(pilot.__file__).with_name('corral_astra_v8_2_review.html').read_text(encoding='utf-8')
    template=template.replace('Ten Astra pilot annotations from a fresh 1,000-episode Corral sample:',
        'Astra annotations for the frozen 1,000-episode Corral sample:')
    helper="""function frameSeconds(f){const a=current.frame_times;if(!a)return f/current.fps;if(f<a.length)return a[f];return current.duration_seconds??a.at(-1)+1/current.fps}
function frameAtSeconds(t){const a=current.frame_times;if(!a)return Math.floor(t*current.fps+0.001);let lo=0,hi=a.length;while(lo<hi){const mid=(lo+hi)>>1;if(a[mid]<=t+0.00001)lo=mid+1;else hi=mid}return Math.max(0,lo-1)}
"""
    template=template.replace("const time=f=>(f/current.fps).toFixed(2)",helper+"const time=f=>frameSeconds(f).toFixed(2)")
    template=template.replace('pendingSeek=frame/current.fps','pendingSeek=frameSeconds(frame)')
    template=template.replace('Math.floor(master.currentTime*current.fps+0.001)','frameAtSeconds(master.currentTime)')
    data=dict(protocol='corral_astra_rich_failure_v8_2_batch_v2',prompt_revision='V8.2',
        manifest_sha256=common.sha(root/'run_plan.json'),review_ui_version=hashlib.sha256(template.encode()).hexdigest(),
        repeats=1,planned_responses=1000,side_labels={'v8':'V8.2 - Astra'},side_repeats={'v8':1},
        status_message=message,rich_prompt_description='Reviewed rich V8.2 prompt; episode outcome and per-failure recovery, severity and resetability.',episodes=episodes)
    transport.atomic_json(root/'review_data.json',data)
    encoded=json.dumps(data,ensure_ascii=False).replace('<','\\u003c').replace('\u2028','\\u2028').replace('\u2029','\\u2029')
    temp=root/'review.html.tmp';temp.write_text(template.replace('__DATA__',encoded),encoding='utf-8');temp.replace(root/'review.html')
    lines=['# Astra V8.2 full dataset','',f'{ready}/1000 native Markdown annotations validated. {errors} returned items need attention.','',message,'',
        'The ten reviewed pilot responses are reused with their source provenance. No source outcome annotations are teacher inputs. Native requests and responses remain preserved.','',
        'Review video and aligned annotations at http://127.0.0.1:8809/review.html. Save human corrections as Markdown notes.','',
        '| Episode | Outcome | Native annotation |','| --- | --- | --- |']
    for e in episodes:
        trace=e['teachers']['v8']
        lines.append(f"| {e['id']} | "+(trace[0]['success_label'] if trace else 'Pending')+' | '+
            (f"[Markdown]({trace[0]['markdown']})" if trace else 'Pending')+' |')
    (root/'report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')


def export_dataset(root):
    """Operational JSONL wraps native Markdown targets; no training is launched."""
    plan=verify_plan(root);imported={r['episode']:r for r in plan['imported_pilot']}
    source_paths={e['id']:e['release_path'] for e in pilot.verified_selection(root)['episodes']}
    rows=[];models={};input_tokens=output_tokens=0;cost=0
    for episode in catalog(root):
        eid=episode['id'];folder=root/'traces'/(eid+'_astra')
        if not (folder/'status.json').exists():continue
        state=common.read(folder/'status.json');model=state['model'];models[model]=models.get(model,0)+1
        text=(folder/'annotation.md').read_text(encoding='utf-8');parsed=common.read(folder/'parsed.json')
        request=root/'requests'/(eid+'_astra.json')
        if eid in imported:
            request=Path(plan['source_run'])/'requests'/(eid+'_astra.json')
        else:
            request=frozen_request_path(root,common.read(root/'preflight'/(eid+'.json')))
        usage=state['usage'];input_tokens+=usage['input_tokens'];output_tokens+=usage['output_tokens']
        cost+=usage_cost(usage,batch_mode=eid not in imported)
        rows.append(dict(episode_id=eid,source_release_path=source_paths[eid],
            task=episode['task'],split='review',teacher_requested_model=MODEL,teacher_recorded_model=model,
            prompt_sha256=plan['prompt_sha256'],request_sha256=common.sha(request),
            response_sha256=common.sha(folder/'response.json'),native_response=str((folder/'response.json').relative_to(root)),
            annotation_markdown=str((folder/'annotation.md').relative_to(root)),assistant_target=text,
            annotation_schema=schema.SCHEMA,success_label=parsed['success_label'],
            imported_reviewed_pilot=eid in imported,human_verified=False))
    temp=root/'dataset.jsonl.tmp'
    with temp.open('wb') as f:
        for row in rows:f.write(compact(row)+b'\n')
    temp.replace(root/'dataset.jsonl')
    transport.atomic_json(root/'dataset_manifest.json',dict(updated_utc=now(),complete=len(rows)==1000,
        selected_episodes=1000,validated_native_targets=len(rows),recorded_models=models,
        input_tokens=input_tokens,output_tokens=output_tokens,estimated_total_inference_usd=cost,
        reused_pilot_targets=len(imported),new_targets=len(rows)-len(imported),
        source_selection_sha256=plan['selection_sha256'],prompt_sha256=plan['prompt_sha256'],
        human_review_status='Teacher labels require human review; imported pilot targets were shown to the user.',
        dataset_sha256=common.sha(root/'dataset.jsonl'),training_launched=False))


def pipeline(root, interval=30):
    from concurrent.futures import ThreadPoolExecutor
    plan=verify_plan(root);client=Gateway();lock=root/'queue_worker.lock'
    write_once(lock,dict(pid=os.getpid(),started_utc=now()))
    try:
        while True:
            if (root/'STOP_REQUESTED.json').exists(): raise ValueError('User stop request; no further submissions')
            try:
                active,queued_tokens=collect(root,client)
            except RuntimeError as error:
                if not any(code in str(error) for code in ('HTTP 408','HTTP 429','HTTP 500','HTTP 502','HTTP 503','HTTP 504','URLError')):
                    raise
                transport.atomic_json(root/'poll_warning.json',dict(error=str(error),recorded_utc=now(),
                    action='Read-only polling will resume; no generation submission is retried.'))
                time.sleep(interval);continue
            assigned={eid for p in (root/'prepared_shards').glob('*.json') for eid in common.read(p)['episodes']}
            freeze_available(root,assigned)
            assigned={eid for p in (root/'prepared_shards').glob('*.json') for eid in common.read(p)['episodes']}
            # Frozen but unsubmitted batches survive process restarts intact.
            for p in sorted((root/'prepared_shards').glob('*.json')):
                shard=common.read(p)
                if (root/'batch_jobs'/(Path(shard['path']).stem+'.json')).exists():continue
                if queued_tokens+shard['input_tokens']>2_500_000:break
                submit_shard(root,shard,client);queued_tokens+=shard['input_tokens'];active+=len(shard['episodes'])
            ready=[];held=[];prepared_count=0
            for item in pilot.verified_selection(root)['episodes']:
                eid=item['id'];p=root/'prepared'/(eid+'.json')
                if not p.exists():continue
                e=common.read(p)
                if e['status']!='prepared':held.append(dict(episode=eid,reason=e.get('error')));continue
                prepared_count+=1
                if (root/'traces'/(eid+'_astra')/'status.json').exists() or eid in assigned:continue
                if len(e['images'])>MAX_IMAGES:
                    held.append(dict(episode=eid,reason='Image limit; lossless packaging decision pending'));continue
                error_path=root/'preflight_errors'/(eid+'.json')
                if error_path.exists():
                    old=common.read(error_path)
                    transport_recoverable=old.get('transport_policy')!='fileids50mb_v1' and (root/'requests'/(eid+'_astra.json')).exists() and (root/'requests'/(eid+'_astra.json')).stat().st_size>MAX_INLINE_REQUEST_BYTES and not (root/'preflight'/(eid+'.json')).exists()
                    if not transport_recoverable and (old.get('rounds',0)>=3 or not any(code in old['error'] for code in ('HTTP 408','HTTP 429','HTTP 500','HTTP 502','HTTP 503','HTTP 504','Request needs file-ID transport'))):
                        held.append(dict(episode=eid,reason=old['error']));continue
                ready.append(e)
            # Bound preflight memory and leave room to collect completed jobs.
            existing_jobs=list((root/'batch_jobs').glob('*.json'))
            new_validated=max(0,len(list((root/'traces').glob('*/status.json')))-10)
            # Validate actual Batch/cache compatibility on requested episodes
            # before exposing the rest of the run to a systematic API error.
            if existing_jobs and not new_validated:
                if all(common.read(p)['status']=='collected' for p in existing_jobs):
                    raise ValueError('Initial Astra Batch returned no validated labels; inspect native outputs before more submissions')
                todo=[]
            else:
                todo=ready[:(12 if new_validated else 3)]
            if todo:
                with ThreadPoolExecutor(max_workers=3) as pool:
                    futures={pool.submit(preflight_one,root,e):e['id'] for e in todo}
                    for future in as_completed(futures):
                        eid=futures[future]
                        try:
                            row=future.result();print(eid+': preflight '+str(row['input_tokens']),flush=True)
                        except Exception as error:
                            error_path=root/'preflight_errors'/(eid+'.json')
                            old_failure=common.read(error_path) if error_path.exists() else {}
                            previous=old_failure.get('rounds',0) if old_failure.get('transport_policy')=='fileids50mb_v1' else 0
                            failure=dict(error=str(error),recorded_utc=now(),generation_submitted=False,rounds=previous+1,transport_policy='fileids50mb_v1')
                            write_once(root/'preflight_attempts'/(eid+'_'+uuid.uuid4().hex+'.json'),failure)
                            transport.atomic_json(error_path,failure)
                            if any(code in str(error) for code in ('HTTP 401','HTTP 403','Unknown parameter','billing','quota')):raise
                            print(eid+': preflight held: '+str(error),flush=True)
            freeze_available(root,assigned)
            validated=len(list((root/'traces').glob('*/status.json')))
            failed=len(list((root/'traces').glob('*/error.json')))
            state=dict(updated_utc=now(),prepared_episodes=prepared_count,validated_episodes=validated,
                returned_errors=failed,active_requests=active,queued_input_tokens=queued_tokens,
                held_episodes=held,preflight_complete=len(list((root/'preflight').glob('*.json'))),
                frozen_new_requests=sum(len(common.read(p)['episodes']) for p in (root/'prepared_shards').glob('*.json')),
                submitted_new_requests=sum(len(common.read(p)['shard']['episodes']) for p in (root/'batch_jobs').glob('*.json')),
                conservative_committed_usd=sum(common.read(p)['shard']['conservative_batch_ceiling_usd'] for p in (root/'batch_jobs').glob('*.json')),
                budget_usd=plan['budget_usd'])
            transport.atomic_json(root/'queue_status.json',state)
            message=f"{validated}/1000 validated; {active} active requests; {prepared_count}/1000 prepared; {len(held)} currently held."
            print(message,flush=True);publish(root,message);export_dataset(root)
            if validated+failed==1000: return
            time.sleep(1 if todo else interval)
    except Exception as error:
        transport.atomic_json(root/'queue_failure.json',dict(error=str(error),recorded_utc=now(),automatic_resend=False))
        publish(root,'Queue stopped: '+str(error));raise
    finally:
        lock.unlink(missing_ok=True)


def finish_preparation(root, workers=8):
    """Finish preparation after an already-running first pass, preserving errors."""
    while not (root/'preparation_audit.json').exists():
        if (root/'STOP_REQUESTED.json').exists():return
        time.sleep(10)
    prepare(root,workers)
    publish(root,'All 1000 full-video inputs prepared. Batch labeling in progress; long-episode packaging is held pending the user choice.')


def repair_transport(root):
    """Recover MIME-rejected staging inputs only; never submits generations."""
    while True:
        if (root/'STOP_REQUESTED.json').exists():return
        for path in sorted((root/'preflight_errors').glob('*.json')):
            eid=path.stem
            if (root/'preflight'/(eid+'.json')).exists():continue
            error=common.read(path)['error']
            if 'Invalid file format application/octet-stream' not in error:continue
            receipt=root/'transport_recovery'/(eid+'.json')
            if receipt.exists():continue
            try:
                row=preflight_one(root,common.read(root/'prepared'/(eid+'.json')))
                write_once(receipt,dict(status='recovered',request_sha256=row['request_sha256'],recorded_utc=now(),generation_submitted=False))
                print(eid+': exact-pixel image transport recovered',flush=True)
            except Exception as exc:
                write_once(receipt,dict(status='needs_attention',error=str(exc),recorded_utc=now(),generation_submitted=False))
                print(eid+': transport recovery needs attention: '+str(exc),flush=True)
        if (root/'dataset_manifest.json').exists() and common.read(root/'dataset_manifest.json')['complete']:return
        time.sleep(30)


def finalize_review(root):
    """Check the ordinary full reviewer after the runnable results stabilize."""
    import subprocess
    while True:
        if (root/'STOP_REQUESTED.json').exists():return
        if (root/'manifest.json').exists():
            manifest=common.read(root/'manifest.json')
            expected=[e['id'] for e in manifest['episodes'] if len(e['images'])<=MAX_IMAGES or (root/'packaging_policy.json').exists()]
            returned=all(any((root/'traces'/(eid+'_astra')/name).exists() for name in ('status.json','error.json')) for eid in expected)
            shards=list((root/'prepared_shards').glob('*.json'))
            settled=all((root/'batch_jobs'/p.name).exists() and common.read(root/'batch_jobs'/p.name)['status']=='collected' for p in shards)
            if returned and settled:break
        time.sleep(30)
    results={}
    for label,script in [('browser','check_binary_review_browser.py'),('judgments','check_corral_astra_v8_2_review.py')]:
        command=[str(ROOT/'.venv-review/Scripts/python.exe'),str(ROOT/'scripts/distill'/script),
            '--url','http://127.0.0.1:8809/review.html','--browser','C:/Program Files/Google/Chrome/Application/chrome.exe',
            '--out',str(root/(label+'_checks_stable'))]
        with (root/(label+'_stable.stdout.log')).open('w') as out,(root/(label+'_stable.stderr.log')).open('w') as err:
            result=subprocess.run(command,cwd=ROOT,stdout=out,stderr=err,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        results[label]=result.returncode
    export_dataset(root)
    transport.atomic_json(root/'stable_review_checks.json',dict(checked_utc=now(),exit_codes=results,
        all_checks_passed=all(code==0 for code in results.values()),episode_count=1000,
        covered_runnable_episode_count=len(expected),native_label_correctness_assessed=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['init', 'prepare', 'finish-preparation', 'repair-transport', 'finalize-review', 'run', 'review', 'preflight-one'])
    parser.add_argument('--run', type=Path, default=DEFAULT)
    parser.add_argument('--source', type=Path, default=SOURCE)
    parser.add_argument('--budget-usd', type=float, default=800)
    parser.add_argument('--workers', type=int, default=8)
    parser.add_argument('--episode')
    args = parser.parse_args(); root = args.run.resolve()
    if args.command == 'init':
        initialize(root, args.source.resolve(), args.budget_usd)
    elif args.command == 'prepare':
        prepare(root, args.workers)
    elif args.command == 'finish-preparation':finish_preparation(root,args.workers)
    elif args.command == 'repair-transport':repair_transport(root)
    elif args.command == 'finalize-review':finalize_review(root)
    elif args.command == 'run': pipeline(root)
    elif args.command == 'review': publish(root)
    elif args.command == 'preflight-one':
        print(json.dumps(preflight_one(root,common.read(root/'prepared'/(args.episode+'.json'))),indent=2))
