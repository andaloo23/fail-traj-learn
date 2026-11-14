"""Measure each release episode once from its first referenced MP4's movie header.

Only MP4 headers are fetched with HTTP ranges; video frames are not downloaded.
Results are append-only and resumable. No model APIs or source annotations used.
"""
import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import hashlib
import json
from pathlib import Path
import statistics
import struct
import threading
import time
from urllib.parse import quote

import requests
from huggingface_hub import get_token


def movie_duration(read, size):
    """Walk top-level ISO BMFF boxes, then read only the mvhd timing fields."""
    def box(offset, end):
        raw = read(offset, min(16, end-offset))
        if len(raw) < 8:
            raise ValueError('Truncated MP4 box')
        length, kind = struct.unpack('>I4s', raw[:8])
        header = 8
        if length == 1:
            length, header = struct.unpack('>Q', raw[8:16])[0], 16
        elif length == 0:
            length = end-offset
        if length < header or offset+length > end:
            raise ValueError('Invalid MP4 box length')
        return kind, offset+header, offset+length

    offset = 0
    for _ in range(10000):
        if offset >= size:
            break
        kind, body, end = box(offset, size)
        if kind == b'moov':
            child = body
            while child < end:
                kind, body, child_end = box(child, end)
                if kind == b'mvhd':
                    value = read(body, min(40, child_end-body))
                    if value[0] == 0:
                        scale, duration = struct.unpack('>II', value[12:20])
                        unknown = 0xffffffff
                    elif value[0] == 1:
                        scale, duration = struct.unpack('>IQ', value[20:32])
                        unknown = 0xffffffffffffffff
                    else:
                        raise ValueError('Unknown mvhd version')
                    if scale <= 0 or duration <= 0 or duration == unknown:
                        raise ValueError('Missing positive movie duration')
                    return dict(duration_seconds=duration/scale,
                                duration_ticks=duration, timescale=scale)
                child = child_end
            raise ValueError('Movie header missing from moov')
        offset = end
    raise ValueError('MP4 moov box not found')


class RemoteHeader:
    def __init__(self, url, size, session, token):
        self.url, self.size, self.session, self.token = url, size, session, token
        self.ranges = []
        self.bytes_read = self.requests = 0

    def read(self, offset, count):
        for start, data in self.ranges:
            if start <= offset and offset+count <= start+len(data):
                return data[offset-start:offset-start+count]
        end = min(self.size-1, offset+max(count, 4096)-1)
        headers = {'Range': f'bytes={offset}-{end}'}
        if self.token:
            headers['Authorization'] = 'Bearer '+self.token
        # Distinct range query avoids caches serving a different cached range.
        url = self.url+f'?download=true&duration_range={offset}_{end}'
        with self.session.get(url, headers=headers, stream=True, timeout=(15, 45)) as r:
            r.raise_for_status()
            self.requests += 1
            if r.status_code == 206:
                content_range = r.headers.get('Content-Range', '')
                if not content_range.startswith(f'bytes {offset}-'):
                    raise ValueError('Unexpected HTTP Content-Range')
                data = r.raw.read(end-offset+1)
            elif r.status_code == 200 and offset == 0:
                data = r.raw.read(end+1)
            else:
                raise ValueError('Server did not honor nonzero byte range')
        self.bytes_read += len(data)
        self.ranges.append((offset, data))
        if len(data) < count:
            raise ValueError('Truncated HTTP range')
        return data[:count]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, default=Path('outputs/oopsie_corpus_duration_audit_v1'))
    p.add_argument('--workers', type=int, default=16)
    p.add_argument('--limit', type=int)
    args = p.parse_args()
    source = Path('outputs/oopsiedata_v0_1_access')
    info = json.loads((source/'dataset_info.json').read_text())
    with (source/'episodes.csv').open(encoding='utf-8-sig', newline='') as f:
        episodes = list(csv.DictReader(f))
    with (args.out/'manifest.csv').open(encoding='utf-8-sig', newline='') as f:
        videos = {r['release_path']: r for r in csv.DictReader(f)}
    args.out.mkdir(parents=True, exist_ok=True)
    result_path = args.out/'episode_durations.jsonl'
    results = {}
    if result_path.exists():
        for line in result_path.read_text().splitlines():
            r = json.loads(line)
            if r['revision'] != info['sha']:
                raise ValueError('Existing results use another release revision')
            if r['status'] == 'measured':
                results[r['release_path']] = r
    token = get_token()
    local = threading.local()

    def measure(e):
        video_path = json.loads(e['video_reference_paths_json'])[0]
        v = videos[video_path]
        row = dict(release_path=e['release_path'], source_repo=e['source_repo'],
                   revision=info['sha'], video_path=video_path,
                   video_sha256=v['release_sha256'],
                   camera_count=int(e['camera_count']))
        if not hasattr(local, 'session'):
            local.session = requests.Session()
            local.session.headers['User-Agent'] = 'fail-traj-learn-duration-audit/1'
        for attempt in range(4):
            try:
                url = ('https://huggingface.co/datasets/'+info['id']+'/resolve/'
                       + info['sha']+'/'+quote(video_path, safe='/'))
                reader = RemoteHeader(url, int(v['release_size_bytes']), local.session, token)
                duration = movie_duration(reader.read, reader.size)
                return dict(row, status='measured', **duration,
                            header_bytes_read=reader.bytes_read,
                            range_requests=reader.requests)
            except Exception as exc:
                # Never serialize URLs, request headers, or exception text with credentials.
                error = type(exc).__name__
                if isinstance(exc, requests.HTTPError):
                    error += ':'+str(exc.response.status_code)
                if attempt < 3:
                    time.sleep(2**attempt)
        return dict(row, status='error', error=error)

    pending = [e for e in episodes if e['release_path'] not in results]
    if args.limit:
        pending = pending[:args.limit]
    print(json.dumps(dict(total_episodes=len(episodes), already_measured=len(results),
                          pending=len(pending))), flush=True)
    started = last = time.monotonic()
    errors = []
    with result_path.open('a', encoding='utf-8', buffering=1) as out:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = [pool.submit(measure, e) for e in pending]
            for future in as_completed(futures):
                row = future.result()
                out.write(json.dumps(row)+'\n')
                if row['status'] == 'measured':
                    results[row['release_path']] = row
                else:
                    errors.append(row)
                if time.monotonic()-last >= 20:
                    print(json.dumps(dict(measured=len(results), errors=len(errors),
                                          elapsed_seconds=round(time.monotonic()-started))), flush=True)
                    last = time.monotonic()
    values = [r['duration_seconds'] for r in results.values()]
    labs = defaultdict(list)
    for r in results.values():
        labs[r['source_repo']].append(r['duration_seconds'])
    summary = dict(revision=info['sha'], expected_episodes=len(episodes),
                   measured_episodes=len(values), complete=len(values)==len(episodes),
                   method='MP4 mvhd duration from first listed camera per episode; each episode counted once',
                   mean_seconds=statistics.mean(values) if values else None,
                   median_seconds=statistics.median(values) if values else None,
                   min_seconds=min(values) if values else None,
                   max_seconds=max(values) if values else None,
                   total_seconds=sum(values), total_hours=sum(values)/3600,
                   metadata_sha256=hashlib.sha256((source/'episodes.csv').read_bytes()).hexdigest(),
                   by_source={k: dict(episodes=len(v), mean_seconds=statistics.mean(v),
                                      total_hours=sum(v)/3600) for k,v in sorted(labs.items())},
                   errors=errors)
    (args.out/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('by_source','errors')}), flush=True)
    return 0 if not errors else 1


if __name__ == '__main__':
    raise SystemExit(main())
