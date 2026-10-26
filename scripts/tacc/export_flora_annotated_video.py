"""Export synchronized original cameras and native FLORA segment annotations as MP4."""
import argparse
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import html
import json
from pathlib import Path

import av
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

from check_flora_results import check, check_rubric, rubric_samples_from_manifest
from review_flora_rubric import timed_cues


COLORS = {1: '#b84152', 2: '#a67525', 3: '#287552'}
SIZE = (1920, 1080)


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read_rows(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def wrap(text, font, width):
    lines, line = [], ''
    for word in text.split():
        candidate = (line+' '+word).strip()
        if line and font.getlength(candidate) > width:
            lines.append(line)
            line = word
        else:
            line = candidate
    if line:
        lines.append(line)
    return lines


def subtitle_time(seconds):
    milliseconds = round(seconds*1000)
    hours, remainder = divmod(milliseconds, 3600000)
    minutes, remainder = divmod(remainder, 60000)
    seconds, remainder = divmod(remainder, 1000)
    return f'{hours:02}:{minutes:02}:{seconds:02},{remainder:03}'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--episode', default='O003')
    parser.add_argument('--dense', type=Path, required=True)
    parser.add_argument('--dense-jobs', type=Path, required=True)
    parser.add_argument('--rubric', type=Path, required=True)
    parser.add_argument('--jobs', type=Path, required=True)
    parser.add_argument('--provenance', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    assert check(args.dense, args.dense_jobs)['structurally_valid']
    assert check_rubric(args.rubric, args.jobs, expected_samples=rubric_samples_from_manifest(args.rubric))['structurally_valid']
    dense = next(row for row in read_rows(args.dense) if row['id'] == args.episode)
    rubric = next(row for row in read_rows(args.rubric) if row['id'] == args.episode)
    job = next(row for row in read_rows(args.jobs) if row['id'] == args.episode)
    provenance = json.loads(args.provenance.read_text())
    source = next(row for row in provenance['episodes'] if row['id'] == args.episode)
    run = json.loads((args.dense.parent/'run.json').read_text())
    assert run['status'] == 'completed'
    assert run['code']['revision'] == '7de68d22c4a9decec5ddb7f86ddcaee8f82d3367'
    assert dense['task'] == job['task'] == rubric['task']
    dense_job = next(row for row in read_rows(args.dense_jobs) if row['id'] == args.episode)
    paths = [(args.dense_jobs.parent/name).resolve() for name in dense_job['videos']]
    by_hash = {c['sha256']: c for c in source['cameras'] if 'excluded_duplicate_of' not in c}
    cameras = [by_hash[digest(path)] for path in paths]
    assert len(cameras) in (1, 2, 3)
    rubric_descriptions = {digest((args.jobs.parent/name).resolve()): description
                           for name, description in zip(job['videos'], job['cameras'], strict=True)}
    camera_descriptions = [c['camera'] for c in cameras]
    for path, camera in zip(paths, cameras):
        assert digest(path) == camera['sha256']
        assert camera['frames'] == dense['num_frames']
        assert abs(camera['fps']-dense['fps']) < 1e-6
        assert camera['sha256'] in run['video_sha256'].values()
    total, fps = dense['num_frames'], Fraction(str(dense['fps']))
    duration = total/float(fps)
    segments = dense['segments']
    end = 0
    for segment in segments:
        assert segment['start_frame'] == end
        assert all(score == segment['score'] for score in dense['frame_scores'][end:segment['end_frame']])
        end = segment['end_frame']
    assert end == total
    thinking = rubric['samples'][rubric['medoid_sample']]['thinking']
    reference = run.get('reference_batch_defaults') is True
    cues = [] if reference else timed_cues(thinking, duration)
    args.out.mkdir(parents=True, exist_ok=False)
    stem = args.episode+'_annotated'
    partial = args.out/(stem+'.partial.mp4')
    output_path = args.out/(stem+'.mp4')
    font_root = Path('/usr/share/fonts/truetype/dejavu')
    regular = lambda size: ImageFont.truetype(str(font_root/'DejaVuSans.ttf'), size)
    bold = lambda size: ImageFont.truetype(str(font_root/'DejaVuSans-Bold.ttf'), size)
    fonts = {name: factory(size) for name, factory, size in [
        ('title', bold, 36), ('task', regular, 30), ('camera', bold, 25),
        ('label', bold, 37), ('score', bold, 27), ('meta', regular, 24),
        ('rationale', regular, 29), ('small', regular, 20), ('cue', regular, 23),
    ]}
    base = Image.new('RGB', SIZE, '#10151c')
    draw = ImageDraw.Draw(base)
    draw.text((32, 18), 'FLORA  /  OopsieData  /  '+args.episode, font=fonts['title'], fill='#edf2fa')
    draw.text((32, 74), job['task'], font=fonts['task'], fill='#c8d5e5')
    slots = ([(32, 148, 1856, 420)] if len(cameras) == 1 else
             [(32, 148, 918, 420), (970, 148, 918, 420)] if len(cameras) == 2 else
             [(32, 148, 760, 420), (812, 148, 528, 420), (1360, 148, 528, 420)])
    label_fonts = {}
    for label in {segment['label'].upper() for segment in segments}:
        size = 37
        while bold(size).getlength(label) > 231:
            size -= 1
        label_fonts[label] = bold(size)
    for label, (x, y, width, height) in zip(camera_descriptions, slots):
        draw.text((x, 115), label.replace('camera labeled ', '').replace('_', ' ').title(), font=fonts['camera'], fill='#bfd0e5')
        draw.rectangle((x, y, x+width-1, y+height-1), fill='#05080c')
    draw.rounded_rectangle((32, 592, 1888, 820), radius=14, fill='#192533')
    draw.rounded_rectangle((32, 836, 1888, 970), radius=12, fill='#17212d')
    draw.text((52, 847), 'EPISODE EXPLANATION' if reference else 'TIMESTAMPED EXCERPT FROM THE EPISODE EXPLANATION (APPROXIMATE ALIGNMENT)',
              font=fonts['small'], fill='#a9bdd7')
    for segment in segments:
        left = 32+round(1856*segment['start_frame']/total)
        right = 32+round(1856*segment['end_frame']/total)
        draw.rectangle((left, 994, max(left, right-1), 1014), fill=COLORS[segment['score']])
    draw.text((1100, 1032), 'Native FLORA predictions  |  Awaiting human review', font=fonts['small'], fill='#aab9cb')
    containers = [av.open(str(path)) for path in paths]
    streams = [container.streams.video[0] for container in containers]
    decoders = [iter(container.decode(stream)) for container, stream in zip(containers, streams)]
    input_audio = [len(container.streams.audio) for container in containers]
    assert not any(input_audio), 'Source audio requires an explicit preservation path'
    segment_index = 0
    checkpoints = {0, segments[1]['start_frame'] if len(segments) > 1 else 0, round(28*float(fps)), total-1}
    try:
        with av.open(str(partial), 'w', options={'movflags': '+faststart'}) as destination:
            encoded = destination.add_stream('libx264', rate=fps)
            encoded.width, encoded.height = SIZE
            encoded.pix_fmt = 'yuv420p'
            encoded.options = {'crf': '18', 'preset': 'fast'}
            encoded.codec_context.thread_count = 6
            for index in range(total):
                timestamp = index/float(fps)
                while segments[segment_index]['end_frame'] <= index:
                    segment_index += 1
                segment = segments[segment_index]
                assert segment['start_frame'] <= index < segment['end_frame']
                image = base.copy()
                draw = ImageDraw.Draw(image)
                for decoder, (x, y, width, height) in zip(decoders, slots):
                    frame = next(decoder)
                    assert abs(float(frame.pts*frame.time_base)-timestamp) < 1e-6
                    camera = Image.fromarray(frame.to_ndarray(format='rgb24'))
                    camera = ImageOps.contain(camera, (width, height), Image.Resampling.LANCZOS)
                    image.paste(camera, (x+(width-camera.width)//2, y+(height-camera.height)//2))
                color = COLORS[segment['score']]
                draw.text((52, 608), f'NATIVE SEGMENT {segment_index+1} / {len(segments)}', font=fonts['meta'], fill='#bdcce0')
                draw.text((945, 608), f'{segment["start_frame"]/float(fps):.3f}–{segment["end_frame"]/float(fps):.3f} s', font=fonts['meta'], fill='#bdcce0')
                draw.rounded_rectangle((48, 660, 315, 806), radius=12, fill=color)
                draw.text((66, 675), segment['label'].upper(), font=label_fonts[segment['label'].upper()], fill='white')
                draw.text((68, 738), f'SCORE {segment["score"]} / 3', font=fonts['score'], fill='white')
                rationale = segment['rationale'] or 'No native rationale is provided for normal spans.'
                lines = wrap(rationale, fonts['rationale'], 1500)
                assert len(lines) <= 3
                for line_index, line in enumerate(lines):
                    draw.text((350, 666+line_index*42), line, font=fonts['rationale'], fill='#edf2fa')
                active = [cue for cue in cues if cue['start_s'] <= timestamp < cue['end_s']]
                quote = '   |   '.join(cue['camera']+': '+cue['text'] for cue in active)
                if not quote:
                    quote = ('The full rubric explanation is episode-level and is saved in the companion rubric JSON. No segment timing is inferred from it.'
                             if reference else 'No explicitly timestamped passage was supplied for this interval.')
                lines = wrap(quote, fonts['cue'], 1810)
                assert len(lines) <= 3, 'Do not silently truncate the model quotation'
                for line_index, line in enumerate(lines):
                    draw.text((52, 880+line_index*28), line, font=fonts['cue'], fill='#d7e3f4')
                playhead = 32+round(1856*index/total)
                draw.rectangle((playhead, 988, playhead+3, 1020), fill='white')
                draw.text((32, 1031), f'{timestamp:05.2f} / {duration:05.2f} s    FRAME {index+1} / {total}', font=fonts['meta'], fill='#cbd9ec')
                if index in checkpoints:
                    image.save(args.out/f'preview_frame_{index:04d}.jpg', quality=92)
                frame = av.VideoFrame.from_ndarray(np.asarray(image), format='rgb24')
                frame.pts, frame.time_base = index, 1/fps
                for packet in encoded.encode(frame):
                    destination.mux(packet)
                if index % 150 == 0:
                    print(f'Rendered {index+1}/{total} frames', flush=True)
            for decoder in decoders:
                assert next(decoder, None) is None, 'A camera contains extra frames'
            for packet in encoded.encode():
                destination.mux(packet)
    finally:
        for container in containers:
            container.close()
    # Verify the actual encoded frames, including every rapid segment transition.
    checked = 0
    with av.open(str(partial)) as container:
        stream = container.streams.video[0]
        assert abs(float(stream.average_rate)-float(fps)) < 1e-6
        for index, frame in enumerate(container.decode(stream)):
            assert abs(float(frame.pts*frame.time_base)-index/float(fps)) < 1e-6
            pixel = frame.to_ndarray(format='rgb24')[790, 60].astype(int)
            expected = COLORS[dense['frame_scores'][index]].lstrip('#')
            expected = np.array([int(expected[i:i+2], 16) for i in (0, 2, 4)])
            assert np.max(np.abs(pixel-expected)) < 20, f'Encoded label mismatch at frame {index}'
            checked += 1
        assert checked == total
    partial.replace(output_path)
    (args.out/(args.episode+'_dense.json')).write_text(json.dumps(dense, indent=2)+'\n', encoding='utf-8')
    (args.out/(args.episode+'_rubric.json')).write_text(json.dumps(rubric, indent=2)+'\n', encoding='utf-8')
    subtitles = []
    for index, segment in enumerate(segments, 1):
        subtitles.append(f'{index}\n{subtitle_time(segment["start_frame"]/float(fps))} --> {subtitle_time(segment["end_frame"]/float(fps))}\n'
                         f'{segment["label"].upper()} ({segment["score"]}/3)\n'
                         f'{segment["rationale"] or "No native rationale for normal spans."}\n')
    (args.out/(args.episode+'_segments.srt')).write_text('\n'.join(subtitles), encoding='utf-8')
    manifest = dict(created_utc=datetime.now(timezone.utc).isoformat(), episode=args.episode,
                    task=job['task'], video=str(output_path), video_sha256=digest(output_path),
                    width=SIZE[0], height=SIZE[1], fps=float(fps), frames=total,
                    duration_seconds=duration, native_segments=len(segments), camera_count=len(cameras),
                    dense_sha256=digest(args.dense), rubric_sha256=digest(args.rubric),
                    source_videos=[dict(path=str(p), sha256=digest(p)) for p in paths],
                    timing='Original camera frame i and native label for frame i, at original FPS; no temporal smoothing',
                    rationale='Unmodified native dense rationale; normal spans have no native rationale',
                    episode_excerpt_timing=('No derived alignment; rubric explanation is episode-level' if reference else
                                            'Display alignment of explicit timestamps in the separate episode explanation'),
                    reference_batch_defaults=reference,
                    validation=dict(decoded_output_frames=checked, all_frame_pts_verified=True,
                                    all_encoded_label_colors_verified=True, all_camera_pts_verified=True),
                    human_verified=False, training_ready=False)
    (args.out/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    page = f'''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{args.episode} annotated video</title>
<style>body{{margin:24px auto;padding:0 20px;max-width:1440px;background:#10151c;color:#e4eaf2;font:16px/1.5 system-ui}}a{{color:#a9cbff}}video{{width:100%;background:#05080c;border-radius:10px}}h1{{font-size:25px}}.links{{display:flex;gap:24px;flex-wrap:wrap;margin:16px 0}}.muted{{color:#b0bfd2}}</style>
<h1>{args.episode} · {html.escape(job['task'])}</h1>
<video controls playsinline preload="metadata" poster="preview_frame_0000.jpg" src="{stem}.mp4"></video>
<div class="links"><a href="{stem}.mp4" download>Download annotated MP4</a>
<a href="{args.episode}_segments.srt" download>Segment subtitles</a>
<a href="{args.episode}_dense.json" download>Native annotation JSON</a></div>
<p class="muted">{duration:.2f} seconds · 1920 × 1080 · {float(fps):g} FPS · {len(cameras)} synchronized cameras · {len(segments)} native segments</p>
<p class="muted">Native FLORA labels and rationales follow each source frame. {'Full rubric reasoning is episode-level; no segment timing is inferred from it.' if reference else 'Episode-explanation excerpts use approximate written timestamps.'} Predictions await human review.</p></html>'''
    (args.out/'index.html').write_text(page, encoding='utf-8')
    print(json.dumps(dict(output=str(output_path), frames=total, segments=len(segments),
                          bytes=output_path.stat().st_size, validation='passed'), indent=2), flush=True)


if __name__ == '__main__':
    main()
