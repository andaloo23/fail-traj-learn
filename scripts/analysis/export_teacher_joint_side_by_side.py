"""Render all development episodes side by side from preserved annotations.

The requested teacher label is a display alias; actual source-model provenance
is retained in the MP4 metadata, manifest and export notes. CPU export only.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from fractions import Fraction
from functools import lru_cache
import hashlib
import html
import json
from pathlib import Path
import sys

import av
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'scripts/distill'))
import oopsie_recipe_data as recipe
import score_recipe_suite as scoring
import export_qwen_development_review as saved

SIZE = (1920, 1080)
FPS = Fraction(30)
COLORS = {True: '#a33542', False: '#226b51'}


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


@lru_cache(maxsize=12)
def font(size, bold=False):
    return ImageFont.truetype('C:/Windows/Fonts/' + ('seguisb.ttf' if bold else 'segoeui.ttf'), size)


def at(segments, frame):
    return next(s for s in segments if s['start_frame'] <= frame < s['end_frame'])


def meta(label):
    return {'title': label + ' / Joint-trained Qwen',
            'comment': 'Teacher display alias: ' + label + '. Actual preserved teacher model: gpt-6.1-sol. '
                       'Student: Qwen2.5-VL-7B-Instruct, joint SFT. Development data; no new inference.'}


def timestamp(seconds):
    ms = round(seconds * 1000)
    return f'{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d}.{ms % 1000:03d}'


def base_canvas(e, index, teacher_label, teacher, joint):
    image = Image.new('RGB', SIZE, '#101722')
    draw = ImageDraw.Draw(image)
    draw.text((30, 14), f"Episode {index + 1} / 50  |  {e['id']}", font=font(34, True), fill='#eef4fc')
    text = 'Task: ' + e['task']
    task_font = font(29)
    if draw.textlength(text, font=task_font) > 1850:
        task_font = font(25)
    draw.text((30, 64), text, font=task_font, fill='#d4e1f1')
    for x, title, segments in [(24, teacher_label, teacher), (972, 'Joint-trained Qwen', joint)]:
        draw.rounded_rectangle((x, 134, x + 924, 1014), radius=14, fill='#192433', outline='#3a4c64', width=2)
        draw.text((x + 24, 152), title, font=font(40, True), fill='#eef3fc')
        for s in segments:
            a = x + 24 + round(876 * s['start_frame'] / e['n_frames'])
            b = x + 24 + round(876 * s['end_frame'] / e['n_frames'])
            draw.rectangle((a, 918, max(a, b - 1), 944), fill=COLORS[s['failure']])
        draw.text((x + 24, 955), '0.00 s', font=font(21), fill='#bacbdd')
        end = f"{e['n_frames'] / e['fps']:.2f} s"
        draw.text((x + 900 - draw.textlength(end, font=font(21)), 955), end, font=font(21), fill='#bacbdd')
    draw.text((1110, 1030), 'Red: failure   |   Green: non-failure', font=font(23), fill='#cfdeef')
    return image


def draw_status(base, e, frame, teacher, joint):
    canvas = base.copy()
    draw = ImageDraw.Draw(canvas)
    for x, segment in [(24, at(teacher, frame)), (972, at(joint, frame))]:
        draw.rounded_rectangle((x + 24, 218, x + 900, 276), radius=9, fill=COLORS[segment['failure']])
        draw.text((x + 44, 226), 'FAILURE' if segment['failure'] else 'NON-FAILURE', font=font(31, True), fill='white')
        draw.text((x + 24, 289),
                  f"{segment['start_frame'] / e['fps']:.2f}-{segment['end_frame'] / e['fps']:.2f} s  |  frames [{segment['start_frame']}, {segment['end_frame']})",
                  font=font(23), fill='#d4e1f0')
    return canvas


def verify(path, expected, chapters):
    """Check every presentation frame, both label colors and constant-rate timing."""
    count = 0
    chapter_index = 0
    with av.open(str(path)) as container:
        assert container.streams.video[0].width == SIZE[0]
        assert container.streams.video[0].height == SIZE[1]
        for index, frame in enumerate(container.decode(video=0)):
            if abs(float(frame.pts * frame.time_base) - index / 30) > 1e-5:
                raise ValueError('Presentation frame timing changed')
            while index >= chapters[chapter_index]['end_output_frame']:
                chapter_index += 1
            c = chapters[chapter_index]
            source_frame = (index - c['start_output_frame']) // c['repeats']
            pixels = frame.reformat(width=192, height=108, format='rgb24').to_ndarray()
            for x, track in [(88, c['teacher']), (183, c['joint'])]:
                color = COLORS[at(track, source_frame)['failure']]
                target = np.array([int(color[i:i + 2], 16) for i in (1, 3, 5)])
                if np.max(np.abs(pixels[25, x].astype(int) - target)) > 28:
                    raise ValueError('Encoded label differs from preserved prediction')
            count += 1
        duration = float(container.duration / av.time_base)
    if count != expected or abs(duration - expected / 30) > .02:
        raise ValueError('Presentation dropped frames or changed episode duration')
    return dict(encoded_frames=count, fps=30, duration_seconds=count / 30,
                every_encoded_label_checked=True, sha256=sha(path))


def render_job(job):
    source, out, e, index, teacher_label, teacher, joint = job
    source, out = Path(source), Path(out)
    path = out / 'episodes' / (e['id'] + '_side_by_side.mp4')
    if path.exists():
        raise ValueError('Episode export already exists; no overwrite')
    repeats = 30 / e['fps']
    if repeats != int(repeats):
        raise ValueError('Unexpected native rate; cannot preserve frame timing')
    repeats = int(repeats)
    if len(e['images']) != e['n_frames'] or any(x['frame'] != i for i, x in enumerate(e['images'])):
        raise ValueError('Source image timestamps are incomplete')
    panels = e['images'][0]['panels']
    if len(panels) != 3:
        raise ValueError('Presentation layout requires the three recorded cameras')
    base = base_canvas(e, index, teacher_label, teacher, joint)
    draw = ImageDraw.Draw(base)
    # Two cameras above and the third centered below, repeated on both sides.
    positions = [(24, 326), (472, 326), (248, 600)]
    for offset in (24, 972):
        for panel, (px, py) in zip(panels, positions):
            draw.text((offset + px, py), panel['camera'], font=font(20, True), fill='#c8d8ea')
    states = {}
    poster_frame = next((f for f in range(e['n_frames']) if at(teacher, f)['failure'] and at(joint, f)['failure']),
                        next((s['start_frame'] for s in teacher if s['failure']), e['n_frames'] // 2))
    encoded_count = 0
    with av.open(str(path), 'w', options={'movflags': '+faststart'}) as destination:
        destination.metadata.update(meta(teacher_label))
        stream = destination.add_stream('libx264', rate=FPS)
        stream.width, stream.height = SIZE
        stream.pix_fmt = 'yuv420p'
        stream.options = {'crf': '19', 'preset': 'veryfast'}
        stream.codec_context.thread_count = 4
        for f, item in enumerate(e['images']):
            signature = (at(teacher, f)['start_frame'], at(joint, f)['start_frame'])
            if signature not in states:
                states[signature] = draw_status(base, e, f, teacher, joint)
            canvas = states[signature].copy()
            image_path = source / item['path']
            if sha(image_path) != item['sha256']:
                raise ValueError('Source frame image changed')
            with Image.open(image_path) as raw:
                raw = raw.convert('RGB')
                for panel, (px, py) in zip(panels, positions):
                    crop = raw.crop((panel['x'], panel['y'], panel['x'] + panel['width'], panel['y'] + panel['height']))
                    crop = ImageOps.contain(crop, (428, 224), Image.Resampling.LANCZOS)
                    for offset in (24, 972):
                        canvas.paste(crop, (offset + px + (428 - crop.width) // 2, py + 29 + (224 - crop.height) // 2))
            draw = ImageDraw.Draw(canvas)
            for offset in (24, 972):
                cursor = offset + 24 + round(876 * f / e['n_frames'])
                draw.rectangle((cursor, 912, cursor + 2, 950), fill='white')
            draw.text((30, 1030), f"Source {f / e['fps']:.2f} / {e['n_frames'] / e['fps']:.2f} s  |  Frame {f} / {e['n_frames'] - 1}",
                      font=font(23), fill='#cfdeef')
            if f == poster_frame:
                canvas.save(path.with_suffix('.jpg'), quality=94)
            for _ in range(repeats):
                frame = av.VideoFrame.from_image(canvas)
                frame.pts, frame.time_base = encoded_count, Fraction(1, 30)
                for packet in stream.encode(frame):
                    destination.mux(packet)
                encoded_count += 1
        for packet in stream.encode():
            destination.mux(packet)
    chapter = dict(start_output_frame=0, end_output_frame=encoded_count, repeats=repeats,
                   teacher=teacher, joint=joint)
    checked = verify(path, encoded_count, [chapter])
    return dict(episode=e['id'], position=index + 1, task=e['task'], native_fps=e['fps'],
                source_frames=e['n_frames'], repeats=repeats, file=path.relative_to(out).as_posix(),
                poster=path.with_suffix('.jpg').relative_to(out).as_posix(), teacher=teacher, joint=joint, **checked)


def concatenate(out, records, teacher_label):
    """Join identical H.264 streams without re-encoding the rendered images."""
    path = out / 'astra_joint_all_50.mp4'
    if path.exists():
        raise ValueError('Compilation already exists')
    chapters = []
    start = 0
    with av.open(str(out / records[0]['file'])) as first:
        with av.open(str(path), 'w', options={'movflags': '+faststart'}) as destination:
            destination.metadata.update(meta(teacher_label))
            output = destination.add_stream_from_template(first.streams.video[0])
            for record in records:
                with av.open(str(out / record['file'])) as source:
                    stream = source.streams.video[0]
                    offset = Fraction(start, 30) / stream.time_base
                    if offset.denominator != 1:
                        raise ValueError('Episode boundary is not an exact packet timestamp')
                    for packet in source.demux(stream):
                        if packet.pts is None or packet.dts is None:
                            continue
                        packet.pts += int(offset)
                        packet.dts += int(offset)
                        packet.stream = output
                        destination.mux(packet)
                chapter = dict(record, start_output_frame=start,
                               end_output_frame=start + record['encoded_frames'], start_seconds=start / 30)
                chapters.append(chapter)
                start += record['encoded_frames']
    return verify(path, start, chapters), chapters


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--teacher-label', required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    if out.exists():
        raise ValueError('Choose a new version; no presentation exports are overwritten')
    study = json.loads((REPO / 'outputs/oopsie_distillation_full_v1/study.json').read_text())
    source = REPO / study['config']['source_run']
    manifest = json.loads((source / 'manifest.json').read_text())
    ids = study['development_ids']
    by_id = {e['id']: e for e in manifest['episodes']}
    if len(ids) != 50 or any(by_id[eid]['split'] != 'development' for eid in ids):
        raise ValueError('Only the 50 development episodes may be exported')
    jobs = []
    fingerprints = {}
    totals = {}
    from collections import Counter
    counts = Counter()
    out.mkdir(parents=True)
    (out / 'episodes').mkdir()
    (out / 'annotations').mkdir()
    for index, eid in enumerate(ids):
        e = by_id[eid]
        native = source / 'traces' / (eid + '_sol_r01') / 'annotation.md'
        expected = next(r['annotation_sha256'] for r in study['episodes'] if r['episode'] == eid)
        if sha(native) != expected:
            raise ValueError('Native teacher annotation changed')
        teacher_text = native.read_text(encoding='utf-8')
        teacher = recipe.parse_prediction(teacher_text.split('## Failure annotations')[0], eid, 0, e['n_frames'])
        values, joint, sources = saved.prediction(e, 'joint')
        if None in values:
            raise ValueError('Joint predictions must cover every frame')
        counts.update(scoring.counts(values, scoring.labels(teacher, e['n_frames'])))
        for s in sources:
            fingerprints[str(s['path'].relative_to(REPO))] = sha(s['path'])
        (out / 'annotations' / (eid + '_teacher_native.md')).write_bytes(native.read_bytes())
        (out / 'annotations' / (eid + '_joint_derived_timeline.md')).write_text(
            '# Derived timeline stitched from unchanged native joint-model window predictions\n\n' + saved.timeline(eid, joint), encoding='utf-8')
        jobs.append((str(source), str(out), e, index, args.teacher_label, teacher, joint))
    official = json.loads((saved.RUN / 'arm_scores/joint.json').read_text())['metrics']
    actual = scoring.metrics(counts)
    if actual != official:
        raise ValueError('Joint timelines differ from the official saved scores')
    records = []
    # Render a useful preview early; compilation order still follows the frozen split.
    jobs.sort(key=lambda j: j[2]['id'] != 'O9130')
    with ProcessPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(render_job, job) for job in jobs]
        for future in as_completed(futures):
            record = future.result()
            records.append(record)
            (out / 'progress.md').write_text(f'# Presentation export\n\nCompleted {len(records)}/50 full-episode MP4s.\n', encoding='utf-8')
            print(json.dumps(dict(completed=len(records), total=50, episode=record['episode'],
                                  seconds=record['duration_seconds'])), flush=True)
    records.sort(key=lambda r: r['position'])
    (out / 'episode_receipts.json').write_text(json.dumps(records, indent=2), encoding='utf-8')
    combined, chapters = concatenate(out, records, args.teacher_label)
    (out / 'manifest.json').write_text(json.dumps(dict(teacher_display_name=args.teacher_label,
        teacher_source_model='gpt-6.1-sol', display_name_is_alias=True,
        student_model='Qwen/Qwen2.5-VL-7B-Instruct', student_recipe='joint',
        episodes=50, split='development', final_test_accessed=False, source_predictions_sha256=fingerprints,
        official_joint_metrics=official, compilation=combined, chapters=chapters,
        new_teacher_calls=0, new_inference_calls=0, training_started=False), indent=2), encoding='utf-8')
    lines = ['# Side-by-side presentation: all 50 development episodes', '',
             f'- Left display name: **{args.teacher_label}**. This is the user-requested presentation alias for the preserved **Sol (`gpt-6.1-sol`) annotations**.',
             '- Right: **Joint-trained Qwen**, using the existing Qwen2.5-VL-7B joint-SFT predictions.',
             '- No Astra generations are substituted or claimed as the source. Original requests, teacher outputs, student predictions and review notes remain unchanged.',
             '- Both sides show the same synchronized three camera views. Only their label timelines differ.',
             '- Full episodes, native playback speed, all recorded frames. Native 10-FPS frames repeat three times in the 30-FPS presentation; native 30-FPS frames appear once.',
             '- All 50 development episodes are included in their frozen split order. The final test remains sealed.',
             '- Every encoded label and timestamp is checked in each episode MP4 and the complete compilation.',
             '- No new model calls, training, or pipeline restart.', '',
             f"Compilation duration: {timestamp(combined['duration_seconds'])}.", '',
             '## Episode chapters', '', '| Episode | Compilation start | Duration | MP4 |', '|---|---|---|---|']
    for c in chapters:
        lines.append(f"| {c['episode']} | {timestamp(c['start_seconds'])} | {c['duration_seconds']:.2f} s | [{c['episode']}]({c['file']}) |")
    (out / 'README.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    cards = ''.join(f'<li><a href="{c["file"]}">{c["episode"]}</a> · {html.escape(c["task"])} · compilation {timestamp(c["start_seconds"])}</li>' for c in chapters)
    (out / 'index.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Side-by-side presentation</title><style>body{font:17px/1.5 system-ui;background:#101722;color:#edf3fb;max-width:1500px;margin:auto;padding:24px}a{color:#c8baff}video{width:100%;background:#000}li{margin:10px 0}</style>'
        '<h1>' + html.escape(args.teacher_label) + ' / Joint-trained Qwen</h1><p>All 50 development episodes, synchronized side by side.</p>'
        '<video controls playsinline preload="metadata" src="astra_joint_all_50.mp4"></video>'
        '<p><a href="astra_joint_all_50.mp4" download>Download complete MP4</a> · <a href="README.md">Source provenance and chapter index</a></p><ol>' + cards + '</ol></html>', encoding='utf-8')
    print(json.dumps(dict(complete=True, output=str(out), compilation=combined)), flush=True)


if __name__ == '__main__':
    main()
