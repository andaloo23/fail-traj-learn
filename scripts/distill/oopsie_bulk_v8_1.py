"""Prepare an immutable, label-blind 500-episode OopsieData V8.1 collection.

All camera frames are retained. Splits are lab-disjoint and fixed before labels.
This module downloads data and prepares evidence; it makes no model calls.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict, Counter
from datetime import datetime, timezone
import csv
import hashlib
import io
import json
import os
import posixpath
from pathlib import Path
import random
import shutil
import sys
import threading
from urllib.parse import quote

import av
import h5py
import numpy as np
from PIL import Image
import requests
from huggingface_hub import get_token

import oopsie_common as common
import annotation_runtime as transport

CONFIG = common.ROOT/'configs/oopsie_rich_failure_v8_1_500_batch_v1.json'
INVENTORY = common.ROOT/'outputs/oopsiedata_v0_1_access'
VIDEO_INVENTORY = common.ROOT/'outputs/oopsie_corpus_duration_audit_v1/manifest.csv'


def write_once(path, value):
    path = Path(path)
    if path.exists():
        if common.read(path) != value:
            raise ValueError('Refusing to change frozen file: '+str(path))
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('x', encoding='utf-8') as f:
            json.dump(value, f, indent=2); f.write('\n')


def balanced_order(rows, seed):
    """Round-robin source labs; seeded shuffle within each lab, no outcomes."""
    groups = defaultdict(list)
    for row in rows:
        groups[row['source_repo']].append(row)
    rng = random.Random(seed)
    for key in sorted(groups):
        group=groups[key]
        group.sort(key=lambda e:e['release_path']); rng.shuffle(group)
    keys = sorted(groups); rng.shuffle(keys)
    result = []
    for index in range(max(map(len, groups.values()), default=0)):
        for key in keys:
            if index < len(groups[key]):
                result.append(groups[key][index])
    return result


def exclude_previous_collections(ordered, cfg, videos):
    """Continue the frozen candidate order without buying existing labels again."""
    paths, hashes, fingerprints, old_ids = set(), set(), set(), set()
    technical_paths = set(); provenance = []
    by_path = {e['release_path']:e for rows in ordered.values() for e in rows}
    for relative in cfg.get('exclude_previous_runs', []):
        previous = common.inside(common.ROOT, relative)
        selection = common.read(previous/'selection.json')
        prior_config = common.read(previous/'config.json')
        if (prior_config['revision'] != cfg['revision'] or
                prior_config['development_labs'] != cfg['development_labs'] or
                prior_config['test_labs'] != cfg['test_labs']):
            raise ValueError('Previous collection has incompatible release or held-out labs')
        for e in selection['episodes']:
            paths.add(e['release_path']); hashes.add(e['hdf5_sha256']); old_ids.add(e['id'])
            row = by_path.get(e['release_path'])
            if row is None:
                raise ValueError('Previous episode absent from unchanged candidate inventory')
            refs = json.loads(row['video_reference_paths_json'])
            fingerprints.add(tuple(sorted({videos[p]['release_sha256'] for p in refs})))
        technical_paths.update(e['release_path'] for e in selection.get('technical_exclusions', []))
        provenance.append(dict(run=relative, selection_sha256=common.sha(previous/'selection.json'),
            config_sha256=common.sha(previous/'config.json'), labeled_episodes=len(selection['episodes'])))
    result = {}; excluded = Counter()
    for split, rows in ordered.items():
        result[split] = []
        for e in rows:
            fingerprint = tuple(sorted({videos[p]['release_sha256'] for p in json.loads(e['video_reference_paths_json'])}))
            if (e['release_path'] in paths or e['release_file_sha256'] in hashes or
                    fingerprint in fingerprints or e['id'] in old_ids):
                excluded['previously_collected_episode_or_video_set'] += 1
            elif e['release_path'] in technical_paths:
                excluded['previous_technical_exclusion'] += 1
            else:
                result[split].append(e)
    return result, provenance, dict(excluded)


def plan(config=CONFIG):
    cfg = common.read(config); root = common.ROOT/cfg['out']
    root.mkdir(parents=True, exist_ok=True)
    write_once(root/'config.json', cfg)
    prompt = common.ROOT/cfg['prompt']
    if common.sha(prompt) != cfg['prompt_sha256']:
        raise ValueError('V8.1 prompt changed')
    if not (root/'prompt.md').exists(): shutil.copyfile(prompt, root/'prompt.md')
    if common.sha(root/'prompt.md') != cfg['prompt_sha256']: raise ValueError('Frozen prompt changed')
    info = common.read(INVENTORY/'dataset_info.json')
    if info['sha'] != cfg['revision']: raise ValueError('Release revision mismatch')
    with (INVENTORY/'episodes.csv').open(encoding='utf-8-sig', newline='') as f:
        episodes = list(csv.DictReader(f))
    with VIDEO_INVENTORY.open(encoding='utf-8-sig', newline='') as f:
        videos = {r['release_path']: r for r in csv.DictReader(f)}
    old = common.read(common.ROOT/'outputs/oopsiedata_twelve_v1/selection.json')
    excluded_paths = {e['release_path'] for e in old['episodes']}
    excluded_hashes = {e['release_file_sha256'] for e in old['episodes']}
    groups = defaultdict(list); exclusions = Counter(); seen = set()
    for e in episodes:
        if e['release_path'] in excluded_paths or e['release_file_sha256'] in excluded_hashes:
            exclusions['previously_reviewed_pilot'] += 1; continue
        if e['validation_status'] != 'ok' or e['all_video_references_present'] != 'True':
            exclusions['release_media_validation'] += 1; continue
        n, cameras = int(e['timestep_count']), int(e['camera_count'])
        if not 2 <= n <= cfg['max_frames'] or not 1 <= cameras <= cfg['max_cameras']:
            exclusions['whole_episode_frame_camera_limits'] += 1; continue
        refs = json.loads(e['video_reference_paths_json'])
        fingerprint = tuple(sorted({videos[p]['release_sha256'] for p in refs}))
        if fingerprint in seen:
            exclusions['duplicate_multicamera_video_set'] += 1; continue
        seen.add(fingerprint)
        lab = e['source_repo'].split('/')[-1]
        split = 'development' if lab in cfg['development_labs'] else 'test' if lab in cfg['test_labs'] else 'train'
        groups[split].append(dict(e, split=split, lab=lab))
    ordered = {}; index = 1
    for offset, split in enumerate(cfg['split_counts']):
        ordered[split] = []
        for e in balanced_order(groups[split], cfg['seed']+offset):
            ordered[split].append(dict(e, id=f'O{index:04d}')); index += 1
    previous = None
    if cfg.get('exclude_previous_runs'):
        ordered, previous, additional_exclusions = exclude_previous_collections(ordered, cfg, videos)
        exclusions.update(additional_exclusions)
    value = dict(protocol=cfg['protocol'], revision=cfg['revision'], seed=cfg['seed'],
        split_counts=cfg['split_counts'], episode_inventory_sha256=common.sha(INVENTORY/'episodes.csv'),
        video_inventory_sha256=common.sha(VIDEO_INVENTORY),
        selection='Lab-balanced round-robin, seeded within-lab shuffle; all source outcome annotations excluded. Reserve ordering frozen before labeling.',
        technical_scope='Complete episodes with 2..1500 timesteps and 1..4 cameras; all recorded timestamps retained. Technical clock/decoding failures documented, never outcome-filtered.',
        exclusions=dict(exclusions), candidates=ordered)
    if previous is not None:
        value['previous_collections'] = previous
        value['continuation'] = 'Original candidate IDs and seeded reserve order retained; previous labels and technical exclusions removed before preparation.'
    write_once(root/'selection_plan.json', value)
    print(json.dumps(dict(run=str(root), candidates={k:len(v) for k,v in ordered.items()},
                          planned=cfg['split_counts'], model_calls=0)), flush=True)
    return root, cfg, value, videos


class Preparation:
    def __init__(self, root, cfg, videos):
        self.root, self.cfg, self.videos = root, cfg, videos
        self.token = get_token(); self.local = threading.local()
        self.local_sources = {}
        for name in ('oopsiedata_pilot_v1', 'oopsiedata_ten_v1', 'oopsiedata_twelve_v1'):
            base = common.ROOT/'outputs'/name/'source'
            if base.exists():
                for p in base.rglob('*'):
                    if p.is_file(): self.local_sources[p.relative_to(base).as_posix()] = p

    def download(self, relative, checksum, size):
        dest = common.inside(self.root/'source', relative)
        # Long native Harvard paths exceed Windows path limits. Preserve bytes in
        # a content-addressed flat cache and retain their original release path.
        if len(str(dest))>235:
            dest=self.root/'source_files'/(checksum+Path(relative).suffix)
        if dest.exists():
            if dest.stat().st_size != size or common.sha(dest) != checksum:
                raise ValueError('Source checksum mismatch')
            return dest
        dest.parent.mkdir(parents=True, exist_ok=True)
        old = self.local_sources.get(relative)
        if old and common.sha(old) == checksum:
            try: os.link(old, dest)
            except OSError: shutil.copyfile(old, dest)
            return dest
        if not hasattr(self.local, 'session'):
            self.local.session = requests.Session()
        headers = {'Authorization':'Bearer '+self.token} if self.token else {}
        url = ('https://huggingface.co/datasets/'+self.cfg['repo']+'/resolve/'
               + self.cfg['revision']+'/'+quote(relative, safe='/'))
        temp = dest.with_suffix(dest.suffix+'.part')
        # Read-only source downloads may be retried; model generations never are.
        for attempt in range(3):
            try:
                with self.local.session.get(url, headers=headers, stream=True, timeout=(15,90)) as r:
                    r.raise_for_status()
                    with temp.open('wb') as f:
                        for chunk in r.iter_content(1024*1024): f.write(chunk)
                if temp.stat().st_size != size or common.sha(temp) != checksum:
                    raise ValueError('Downloaded source checksum mismatch')
                temp.replace(dest); return dest
            except requests.RequestException:
                if attempt == 2: raise ValueError('Source download failed; no credential-bearing URL recorded') from None

    def episode(self, item):
        eid = item['id']; cache = self.root/'prepared'/f'{eid}.json'
        if cache.exists(): return common.read(cache)
        try:
            hdf5 = self.download(item['release_path'], item['release_file_sha256'], int(item['release_file_size_bytes']))
            with h5py.File(hdf5, 'r') as f:
                if f.attrs['schema'] != 'oopsiedata_format_v1': raise ValueError('Unsupported native schema')
                task = f.attrs['language_instruction']
                if isinstance(task, bytes): task = task.decode()
                if not isinstance(task, str) or not task.strip(): raise ValueError('Missing native task instruction')
                refs = []
                for camera, value in f['observations/video_paths'].items():
                    native = value[()]
                    if isinstance(native, bytes): native = native.decode()
                    rel=posixpath.normpath(posixpath.join(posixpath.dirname(item['release_path']),native.replace('\\','/')))
                    if rel.startswith('../') or rel.startswith('/'):raise ValueError('Video path escape')
                    if rel not in json.loads(item['video_reference_paths_json']): raise ValueError('Video absent from release inventory')
                    refs.append((camera, rel))
            selected, duplicates, hashes = [], [], set()
            for camera, rel in refs:
                meta = self.videos[rel]; digest = meta['release_sha256']
                if digest in hashes:
                    duplicates.append(dict(camera=camera, path=rel, sha256=digest)); continue
                hashes.add(digest)
                path = self.download(rel, digest, int(meta['release_size_bytes']))
                selected.append(dict(camera=camera, description='Native camera identifier '+camera+'; no unverified geometric role assigned.',
                                     path=path, relative=rel, sha256=digest))
            containers = []
            try:
                for camera in selected:
                    container = av.open(str(camera['path'])); containers.append(container)
                    stream = container.streams.video[0]
                    camera.update(fps=float(stream.average_rate), width=stream.width, height=stream.height,
                                  frames=iter(container.decode(stream)))
                fps = selected[0]['fps']; n = int(item['timestep_count'])
                if not all(abs(c['fps']-fps)<1e-6 for c in selected): raise ValueError('Camera frame rates differ')
                images = []; folder = self.root/'images'/eid; folder.mkdir(parents=True, exist_ok=True)
                for frame_index in range(n):
                    panels, positions, x = [], [], 0
                    for camera in selected:
                        frame = next(camera['frames'], None)
                        if frame is None or frame.pts is None: raise ValueError('Missing recorded camera frame or timestamp')
                        clock = float(frame.pts*frame.time_base)
                        if abs(clock-frame_index/fps)>1e-4: raise ValueError('Native clock/state-frame mismatch')
                        image = frame.to_image().convert('RGB')
                        image.thumbnail((self.cfg['max_image_side'],)*2, Image.Resampling.LANCZOS)
                        # Match pilot per-camera JPEG95 preprocessing; retain its decoded pixels losslessly in the strip.
                        jpeg = io.BytesIO(); image.save(jpeg, format='JPEG', quality=95)
                        image = Image.open(io.BytesIO(jpeg.getvalue())).convert('RGB')
                        positions.append(dict(camera=camera['camera'], x=x, y=0, width=image.width, height=image.height))
                        panels.append(image); x += image.width
                    strip = Image.new('RGB', (x, max(p.height for p in panels)), 'black')
                    for panel, pos in zip(panels, positions): strip.paste(panel, (pos['x'],0))
                    path = folder/f'{frame_index:06d}.webp'
                    strip.save(path, format='WEBP', lossless=True, method=0)
                    if frame_index in (0,n-1):
                        with Image.open(path) as decoded:
                            if decoded.convert('RGB').tobytes()!=strip.tobytes(): raise ValueError('Lossless strip pixels differ')
                    images.append(dict(frame=frame_index, seconds=frame_index/fps, camera='all camera panels',
                        path=path.relative_to(self.root).as_posix(), sha256=common.sha(path),
                        rgb_sha256=hashlib.sha256(strip.tobytes()).hexdigest(), panels=positions, bytes=path.stat().st_size))
                if any(next(c['frames'],None) is not None for c in selected): raise ValueError('More video frames than recorded timesteps')
                result = dict(status='prepared', id=eid, release_path=item['release_path'],
                    hdf5_sha256=item['release_file_sha256'], hdf5_file=hdf5.relative_to(self.root).as_posix(),
                    lab=item['lab'], split=item['split'], task=task,
                    n_frames=n, fps=fps, duration_seconds=n/fps,
                    cameras=[dict(camera=c['camera'], description=c['description']) for c in selected],
                    videos=[dict(camera=c['camera'], description=c['description'],
                                 url=c['path'].relative_to(self.root).as_posix(), original_release_path=c['relative'],
                                 sha256=c['sha256']) for c in selected],
                    duplicate_cameras_excluded=duplicates, images=images,
                    source_annotations_used_as_model_input=False)
            finally:
                for container in containers: container.close()
        except (ValueError, av.error.FFmpegError, OSError) as exc:
            # Local errors only; no network exception URLs or credentials serialized.
            result = dict(status='technical_exclusion', id=eid, release_path=item['release_path'],
                          split=item['split'], error=str(exc)[:200] if isinstance(exc,ValueError) else type(exc).__name__)
        write_once(cache, result)
        return result


def prepare(config=CONFIG, workers=8):
    root, cfg, selection, videos = plan(config)
    if (root/'manifest.json').exists():
        print('Already frozen; preparation is not repeated.', flush=True); return
    builder = Preparation(root, cfg, videos); chosen = []; excluded = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for split, count in cfg['split_counts'].items():
            candidates = iter(selection['candidates'][split]); accepted = []
            # Keep workers occupied while yielding in deterministic candidate order.
            from collections import deque
            pending=deque()
            def refill():
                while len(pending)<min(workers*2,count-len(accepted)):
                    row=next(candidates,None)
                    if row is None:break
                    pending.append(pool.submit(builder.episode,row))
            refill()
            while len(accepted)<count:
                if not pending:raise ValueError('Insufficient technically valid candidates for '+split)
                result=pending.popleft().result()
                if result['status']=='prepared':accepted.append(result)
                else:excluded.append(result)
                refill()
                if len(accepted)%8==0 or len(accepted)==count:
                    print(json.dumps(dict(split=split, prepared=len(accepted), target=count,
                                          total_prepared=len(chosen)+len(accepted), exclusions=len(excluded))), flush=True)
            chosen.extend(accepted)
    labs = {split:{e['lab'] for e in chosen if e['split']==split} for split in cfg['split_counts']}
    assert not labs['train']&labs['development'] and not labs['train']&labs['test'] and not labs['test']&labs['development']
    write_once(root/'selection.json', dict(episodes=[{k:e[k] for k in ('id','release_path','lab','split','hdf5_sha256')} for e in chosen],
        technical_exclusions=excluded, selection_plan_sha256=common.sha(root/'selection_plan.json')))
    manifest = dict(protocol=cfg['protocol'], repo=cfg['repo'], revision=cfg['revision'], config=cfg,
        frozen_utc=datetime.now(timezone.utc).isoformat(), source_annotations_used_as_model_input=False,
        prompt_sha256=common.sha(root/'prompt.md'), selection_sha256=common.sha(root/'selection.json'),
        selection_plan_sha256=common.sha(root/'selection_plan.json'),
        preparation_code_sha256=common.sha(Path(__file__)), episodes=chosen)
    write_once(root/'manifest.json', manifest)
    print(json.dumps(dict(frozen_episodes=len(chosen), split_counts=dict(Counter(e['split'] for e in chosen)),
                          mean_seconds=sum(e['duration_seconds'] for e in chosen)/len(chosen),
                          total_hours=sum(e['duration_seconds'] for e in chosen)/3600,
                          image_bytes=sum(x['bytes'] for e in chosen for x in e['images']), model_calls=0)),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('plan','prepare'))
    parser.add_argument('--config',type=Path,default=CONFIG)
    parser.add_argument('--workers',type=int,default=8)
    args=parser.parse_args()
    if args.command=='plan':plan(args.config)
    else:prepare(args.config,args.workers)
