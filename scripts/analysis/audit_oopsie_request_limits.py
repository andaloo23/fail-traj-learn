"""Read-only corpus audit of the current all-frame Astra request limits.

Uses the pinned release inventory, existing prepared episodes, and MP4 headers
for episodes whose conservative token upper bound could exceed the input limit.
No inference, token-count API, source edits, or full-video downloads.
"""
import csv
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote

import av
from huggingface_hub import get_token
from PIL import Image
import requests

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/tacc'))
from audit_oopsie_durations import RemoteHeader


def video_header(read, size):
    def boxes(start, end):
        while start < end:
            raw = read(start, min(16, end-start))
            length, kind = struct.unpack('>I4s', raw[:8]); header = 8
            if length == 1:
                length = struct.unpack('>Q', raw[8:16])[0]; header = 16
            if length == 0:
                length = end-start
            if length < header or start+length > end:
                raise ValueError('Invalid MP4 box')
            yield kind, start+header, start+length
            start += length

    for kind, body, end in boxes(0, size):
        if kind != b'moov':
            continue
        for kind, track, track_end in boxes(body, end):
            if kind != b'trak':
                continue
            result = {}
            for kind, child, child_end in boxes(track, track_end):
                if kind == b'tkhd':
                    w, h = struct.unpack('>II', read(child_end-8, 8))
                    result.update(width=w >> 16, height=h >> 16)
                if kind != b'mdia':
                    continue
                for kind, media, media_end in boxes(child, child_end):
                    if kind == b'hdlr':
                        result['handler'] = read(media+8, 4)
                    if kind != b'minf':
                        continue
                    for kind, info, info_end in boxes(media, media_end):
                        if kind != b'stbl':
                            continue
                        for kind, table, table_end in boxes(info, info_end):
                            if kind in (b'stsz', b'stz2'):
                                result['frames'] = struct.unpack('>I', read(table+8, 4))[0]
            if result.get('handler') == b'vide':
                del result['handler']
                if set(result) != {'width', 'height', 'frames'} or min(result.values()) <= 0:
                    raise ValueError('Incomplete video header')
                return result
    raise ValueError('No video sample table')


def rows(path):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def main():
    inventory = ROOT / 'outputs/oopsiedata_v0_1_access/episodes.csv'
    episodes = rows(inventory)
    info = json.loads((inventory.parent/'dataset_info.json').read_text())
    videos = {v['release_path']: v for v in rows(ROOT/'outputs/oopsie_corpus_duration_audit_v1/manifest.csv')}
    run = ROOT/'outputs/corral_astra_rich_failure_v8_2_1000_batch_v2'
    prepared = {e['release_path']: e for p in (run/'prepared').glob('*.json') for e in [json.loads(p.read_text())]}
    out = ROOT/'outputs/oopsie_request_limit_audit_v1'; out.mkdir(exist_ok=True)
    # Check the sample-table reader against actual local PyAV headers.
    checks = 0
    for path in sorted((run/'source_files').glob('*.mp4'))[:33]:
        with path.open('rb') as stream:
            def read(offset, count):
                stream.seek(offset); return stream.read(count)
            measured = video_header(read, path.stat().st_size)
        with av.open(str(path)) as container:
            stream = container.streams.video[0]
            assert measured == dict(width=stream.width, height=stream.height, frames=stream.frames)
        checks += 1

    # 4,000 shared/episode tokens plus 16 tokens per frame is deliberately
    # above observed text overhead; dimensions assume every panel is 280 square.
    candidates = []
    for e in episodes:
        n, c = int(e['timestep_count']), int(e['camera_count'])
        upper_per_image = math.ceil(math.ceil(280*c/32)*9*1.2)
        if (n+1)*(upper_per_image+16)+4000 > 922000 or abs(n-1500) <= 1:
            candidates.append(e)
    cache_path = out/'candidate_video_headers.json'
    cached = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    token = get_token()
    wanted = sorted({p for e in candidates for p in json.loads(e['video_reference_paths_json'])})

    def measure(path):
        v = videos[path]
        if path in cached:
            assert cached[path]['release_sha256'] == v['release_sha256']
            return path, cached[path]
        local = run/'source_files'/(v['release_sha256']+'.mp4')
        if local.exists():
            with local.open('rb') as stream:
                def read(offset, count):
                    stream.seek(offset); return stream.read(count)
                data = video_header(read, local.stat().st_size)
            method = 'local_original_video_header'
        else:
            url = 'https://huggingface.co/datasets/'+info['id']+'/resolve/'+info['sha']+'/'+quote(path, safe='/')
            with requests.Session() as session:
                remote = RemoteHeader(url, int(v['release_size_bytes']), session, token)
                data = video_header(remote.read, remote.size)
                data['header_bytes_read'] = remote.bytes_read
            method = 'pinned_release_remote_header'
        return path, dict(data, method=method, release_sha256=v['release_sha256'])

    with ThreadPoolExecutor(max_workers=8) as pool:
        for path, data in pool.map(measure, wanted):
            cached[path] = data
            cache_path.write_text(json.dumps(cached, indent=2)+'\n')
    results = []
    for e in episodes:
        path=e['release_path']; n=int(e['timestep_count']); refs=json.loads(e['video_reference_paths_json'])
        native = prepared.get(path)
        if all(p in cached for p in refs):
            frames = {cached[p]['frames'] for p in refs}
            assert len(frames) == 1, path
            n = frames.pop(); method='measured_video_header'
            panels=[]; seen=set()
            for p in refs:
                if videos[p]['release_sha256'] in seen:
                    continue
                seen.add(videos[p]['release_sha256'])
                v=cached[p]; im=Image.new('RGB', (v['width'], v['height']))
                im.thumbnail((280,280), Image.Resampling.LANCZOS); panels.append(im.size)
        elif native:
            n=native['n_frames']; method='existing_native_preparation'
            panels=[(p['width'],p['height']) for p in native['images'][0]['panels']]
        else:
            method='release_timestep_count'; panels=None
        image_over=n>1500
        if panels:
            width=sum(w for w,h in panels); height=max(h for w,h in panels)
            image_tokens=math.ceil(math.ceil(width/32)*math.ceil(height/32)*1.2)
            # Existing token preflights show about 10 text tokens/frame.
            # Use 8..16 for an estimate range, not an API-confirmed bound.
            lower=1912+n*(image_tokens+8)
            upper=4000+n*(image_tokens+16)
        else:
            upper=4000+(n+1)*(math.ceil(math.ceil(280*int(e['camera_count'])/32)*9*1.2)+16)
            lower=None
        token_class='over' if lower is not None and lower>922000 else ('under' if upper<=922000 else 'uncertain')
        results.append(dict(release_path=path, lab=e['source_repo'].split('/')[-1],
            frames=n, frame_count_source=method, image_limit_exceeded=image_over,
            token_limit_class=token_class, input_token_lower=lower,input_token_upper=upper,
            camera_panel_sizes=panels))
    (out/'episodes.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in results))
    count=len(results); image=sum(e['image_limit_exceeded'] for e in results)
    over=[e for e in results if e['token_limit_class']=='over']
    uncertain=[e for e in results if e['token_limit_class']=='uncertain']
    both=sum(e['image_limit_exceeded'] for e in over)
    by_lab={}
    for lab in sorted({e['lab'] for e in results}):
        group=[e for e in results if e['lab']==lab]
        by_lab[lab]=dict(episodes=len(group), image_limit_exceeded=sum(e['image_limit_exceeded'] for e in group),
            token_limit_exceeded=sum(e['token_limit_class']=='over' for e in group))
    summary=dict(release_revision=info['sha'], inventory_sha256=hashlib.sha256(inventory.read_bytes()).hexdigest(),
        total_episodes=count,image_limit=1500,input_token_limit=922000,
        image_limit_exceeded=image,image_limit_percent=100*image/count,
        token_limit_estimated_exceeded=len(over),token_limit_percent=100*len(over)/count,
        both_limits_exceeded=both,either_limit_exceeded=image+len(over)-both,
        token_classification_uncertain=uncertain,token_over_episodes=over,
        local_header_reader_checks=checks, header_audited_episodes=len(candidates),
        existing_prepared_episodes=len(prepared), frame_count_source_counts={m:sum(e['frame_count_source']==m for e in results) for m in {e['frame_count_source'] for e in results}},
        token_estimate_caveat='Image patch formula plus estimated 8..16 caption tokens/frame and 1912..4000 shared/episode tokens; not full-corpus API token preflights.',
        frame_count_caveat='Unsampled episodes use release robot timesteps; native preparation observed video counts within one timestep. No unmeasured inventory count lies within one frame of image boundary.',
        by_lab=by_lab, generation_calls=0)
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    report = [
        '# OopsieData current-request limit audit', '',
        f'Population: all **{count:,} episodes** in frozen OopsieData v0.1.1 release `{info["sha"]}`.', '',
        'Current runner: rich V8.2, every native video frame, distinct camera panels side by side, '
        '280-pixel maximum side per camera, Astra high detail. These results describe the existing '
        'one-image-per-timestep format, before any contact-sheet change.', '',
        '| Limit | Episodes | Percent of entire release |',
        '|---|---:|---:|',
        f'| More than 1,500 images | {image:,} | {100*image/count:.4f}% |',
        f'| More than 922,000 input tokens (estimated) | {len(over)} | {100*len(over)/count:.4f}% |',
        f'| Either limit | {summary["either_limit_exceeded"]:,} | {100*summary["either_limit_exceeded"]/count:.4f}% |',
        f'| Neither limit | {count-summary["either_limit_exceeded"]:,} | {100*(count-summary["either_limit_exceeded"])/count:.4f}% |', '',
        f'Overlap: {both} episodes hit both limits; do not add the two counts.', '',
        '## Image-limit cases by lab', '',
        '| Lab | Affected / total episodes | Percent within lab |', '|---|---:|---:|',
    ]
    for lab, group in sorted(by_lab.items(), key=lambda item: -item[1]['image_limit_exceeded']):
        if group['image_limit_exceeded']:
            report.append(f'| {lab} | {group["image_limit_exceeded"]} / {group["episodes"]} | {100*group["image_limit_exceeded"]/group["episodes"]:.2f}% |')
    report.extend(['', '## Token-limit estimates', ''])
    for e in over:
        report.append(f'- `{e["release_path"]}`: **{e["frames"]:,} frames**, approximately '
                      f'**{e["input_token_lower"]:,}–{e["input_token_upper"]:,} input tokens**.')
    report.extend(['', '## Evidence and limits of this audit', '',
        '- The full release inventory was scanned, rather than extrapolating the 1,000-episode sample.',
        '- Existing native preparation supplies exact video counts/dimensions for 1,000 sampled episodes. '
        'Other episodes use release timestep counts. The observed native-video count difference is at most one frame.',
        '- Actual MP4 headers were inspected for all six boundary/candidate episodes, including every camera. '
        'No remaining unmeasured timestep count lies within one frame of 1,500. The header parser matched '
        'PyAV frame counts and dimensions on 33 local original videos.',
        '- A conservative 280-square-pixels-per-camera upper estimate screens the rest of the corpus '
        'for potential token overflow. Candidate dimensions are then measured from original video headers.',
        '- Token results use the documented patch formula and an estimated 8–16 text tokens per frame, '
        'with 1,912–4,000 shared/episode tokens. Existing Harvard preflights show approximately 86 total '
        'tokens/frame for 280×210 images, consistent with about 10 caption tokens/frame. These are '
        'estimates, rather than full-corpus provider token preflights.',
        '- Corral SSH authentication was unavailable during this audit. Additional headers came from '
        'the same pinned release revision on Hugging Face, identified by the existing manifest. '
        'Header-only reads do not independently verify complete remote-file SHA256 hashes.',
        '- Contact sheets change image dimensions and caption overhead, so their token counts must '
        'be estimated separately. This audit does not establish that packing will solve every case.',
        '- No model-generation or API token-count calls were made. Source files, frozen requests, '
        'teacher outputs, and the hold on the 63 episodes were preserved.', '',
        '[Image-count limit and image-token formula](https://developers.openai.com/api/docs/guides/images-vision); '
        '[Astra input limit](https://developers.openai.com/api/docs/models/gpt-6-astra).', '',
    ])
    (out/'report.md').write_text('\n'.join(report), encoding='utf-8')
    print(json.dumps(summary,indent=2))


if __name__ == '__main__':
    main()
