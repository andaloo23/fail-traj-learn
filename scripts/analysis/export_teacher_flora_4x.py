"""All 50 development episodes at 4x: preserved teacher versus native FLORA.

CPU-only presentation export. No model calls, smoothing, or label edits.
"""
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from fractions import Fraction
import html
import json
from pathlib import Path
import sys

import av
import numpy as np
from PIL import Image, ImageDraw, ImageOps

import export_teacher_joint_side_by_side as original

REPO = Path(__file__).resolve().parents[2]
SIZE = original.SIZE
FPS = Fraction(30)
COLORS = {1: '#a33542', 2: '#a56b14', 3: '#226b51'}
NAMES = {1: 'FAILURE', 2: 'SUBOPTIMAL', 3: 'NORMAL'}
font, sha, at = original.font, original.sha, original.at


def metadata():
    return dict(title='Astra / FLORA | all 50 validation episodes | Sped up 4x',
                comment='Astra is the user-requested display alias for preserved gpt-6.1-sol annotations. '
                        'FLORA: nvidia/Flora-Rewarder revision 7de68d22c4a9decec5ddb7f86ddcaee8f82d3367, '
                        'TACC job 3572125. Native failure/suboptimal/normal labels, no smoothing. '
                        'Binary failure-only comparison maps score 1 to failure, scores 2/3 to non-failure. '
                        'Exactly the same 50 frozen development episodes as the Qwen presentation. '
                        'Playback speed: 4x. No new inference or teacher calls.')


def canvas_base(e, position, teacher, flora):
    canvas = Image.new('RGB', SIZE, '#101722')
    d = ImageDraw.Draw(canvas)
    d.text((30, 14), f"Episode {position + 1} / 50  |  {e['id']}", font=font(34, True), fill='#eef4fc')
    task = 'Task: ' + e['task']
    task_font = font(29) if d.textlength(task, font=font(29)) < 1850 else font(25)
    d.text((30, 64), task, font=task_font, fill='#d4e1f1')
    for x, title, track in [(24, 'Astra', teacher), (972, 'FLORA', flora)]:
        d.rounded_rectangle((x, 134, x + 924, 1014), radius=14, fill='#192433', outline='#3a4c64', width=2)
        d.text((x + 24, 152), title, font=font(40, True), fill='#eef3fc')
        note = 'Failure / non-failure' if x == 24 else 'Native 3-class labels; binary comparison shown below'
        d.text((x + 24, 198), note, font=font(20), fill='#bacbdd')
        for s in track:
            a = x + 24 + round(876 * s['start_frame'] / e['n_frames'])
            b = x + 24 + round(876 * s['end_frame'] / e['n_frames'])
            color = COLORS[s['score']] if x == 972 else original.COLORS[s['failure']]
            d.rectangle((a, 918, max(a, b - 1), 944), fill=color)
        d.text((x + 24, 955), '0.00 s', font=font(21), fill='#bacbdd')
        end = f"{e['n_frames'] / e['fps']:.2f} s"
        d.text((x + 900 - d.textlength(end, font=font(21)), 955), end, font=font(21), fill='#bacbdd')
    banner = 'Sped up 4\u00d7'
    width = d.textlength(banner, font=font(40, True))
    d.rounded_rectangle((1920 - width - 70, 10, 1890, 81), radius=10, fill='#34435f')
    d.text((1920 - width - 50, 20), banner, font=font(40, True), fill='white')
    d.text((1000, 1030), 'Red: failure  |  Amber: suboptimal  |  Green: normal / non-failure',
           font=font(21), fill='#cfdeef')
    return canvas


def status(base, e, teacher, flora):
    canvas = base.copy()
    d = ImageDraw.Draw(canvas)
    for x, s in [(24, teacher), (972, flora)]:
        color = original.COLORS[s['failure']] if x == 24 else COLORS[s['score']]
        label = ('FAILURE' if s['failure'] else 'NON-FAILURE') if x == 24 else NAMES[s['score']]
        if x == 972:
            label += '  |  binary: ' + ('FAILURE' if s['score'] == 1 else 'NON-FAILURE')
        d.rounded_rectangle((x + 24, 229, x + 900, 283), radius=9, fill=color)
        d.text((x + 44, 234), label, font=font(29, True), fill='white')
        d.text((x + 24, 294),
               f"{s['start_frame'] / e['fps']:.2f}-{s['end_frame'] / e['fps']:.2f} s  |  frames [{s['start_frame']}, {s['end_frame']})",
               font=font(23), fill='#d4e1f0')
    return canvas


def verify(path, expected_frames, chapters):
    count = 0
    chapter_index = 0
    with av.open(str(path)) as container:
        stream = container.streams.video[0]
        assert (stream.width, stream.height) == SIZE and stream.average_rate == FPS
        for index, frame in enumerate(container.decode(video=0)):
            assert abs(float(frame.pts * frame.time_base) - index / 30) < 1e-5
            while index >= chapters[chapter_index]['end_output_frame']:
                chapter_index += 1
            chapter = chapters[chapter_index]
            local = index - chapter['start_output_frame']
            f = chapter['selected_source_frames'][local]
            pixels = frame.reformat(width=192, height=108, format='rgb24').to_ndarray()
            for x, color in [(88, original.COLORS[at(chapter['teacher'], f)['failure']]),
                             (183, COLORS[at(chapter['flora'], f)['score']])]:
                target = np.array([int(color[i:i + 2], 16) for i in (1, 3, 5)])
                assert np.max(np.abs(pixels[25, x].astype(int) - target)) <= 30, (index, f, color)
            # At 10% resolution the 40px glyphs are antialiased into ~4px text.
            # Its light pixels stay above 120; the banner background is <100.
            assert np.count_nonzero(np.all(pixels[1:9, 159:189] > 120, axis=2)) > 10, 'Missing speed label'
            count += 1
        duration = container.duration / av.time_base
    assert count == expected_frames and abs(duration - count / 30) < .02
    return dict(encoded_frames=count, fps=30, duration_seconds=duration,
                dimensions=list(SIZE), every_encoded_label_and_timestamp_checked=True,
                every_encoded_speed_banner_checked=True, sha256=sha(path))


def render(job):
    source, out, e, position, teacher, flora, selected, reuse = job
    source, out = Path(source), Path(out)
    path = out / 'episodes' / (e['id'] + '_4x.mp4')
    chapter = dict(episode=e['id'], position=position + 1, task=e['task'], teacher=teacher,
                   flora=flora, selected_source_frames=selected, start_output_frame=0,
                   end_output_frame=len(selected), file=path.relative_to(out).as_posix())
    if path.exists():
        assert reuse, 'Episode export already exists; no overwrite'
        chapter.update(verify(path, len(selected), [chapter]))
        return chapter
    base = canvas_base(e, position, teacher, flora)
    d = ImageDraw.Draw(base)
    positions = [(24, 332), (472, 332), (248, 606)]
    panels = e['images'][0]['panels']
    assert len(panels) == 3
    for offset in (24, 972):
        for panel, (x, y) in zip(panels, positions):
            d.text((offset + x, y), panel['camera'], font=font(20, True), fill='#c8d8ea')
    signature, cached = None, None
    with av.open(str(path), 'w', options={'movflags': '+faststart'}) as dest:
        dest.metadata.update(metadata())
        stream = dest.add_stream('libx264', rate=FPS)
        stream.width, stream.height = SIZE
        stream.pix_fmt = 'yuv420p'
        stream.options = {'crf': '18', 'preset': 'veryfast'}
        stream.codec_context.thread_count = 4
        for index, f in enumerate(selected):
            t, p = at(teacher, f), at(flora, f)
            key = (t['start_frame'], p['start_frame'])
            if key != signature:
                cached = status(base, e, t, p)
                signature = key
            canvas = cached.copy()
            item = e['images'][f]
            image = source / item['path']
            assert item['frame'] == f and sha(image) == item['sha256']
            with Image.open(image) as raw:
                raw = raw.convert('RGB')
                for panel, (x, y) in zip(panels, positions):
                    crop = raw.crop((panel['x'], panel['y'], panel['x'] + panel['width'], panel['y'] + panel['height']))
                    crop = ImageOps.contain(crop, (428, 224), Image.Resampling.LANCZOS)
                    for offset in (24, 972):
                        canvas.paste(crop, (offset + x + (428 - crop.width) // 2, y + 29 + (224 - crop.height) // 2))
            d = ImageDraw.Draw(canvas)
            for offset in (24, 972):
                cursor = offset + 24 + round(876 * f / e['n_frames'])
                d.rectangle((cursor, 912, cursor + 2, 950), fill='white')
            d.text((30, 1030), f"Source {f / e['fps']:.2f} / {e['n_frames'] / e['fps']:.2f} s  |  Frame {f} / {e['n_frames'] - 1}",
                   font=font(23), fill='#cfdeef')
            if index == len(selected) // 2:
                canvas.save(path.with_suffix('.jpg'), quality=95)
            frame = av.VideoFrame.from_image(canvas)
            frame.pts, frame.time_base = index, Fraction(1, 30)
            for packet in stream.encode(frame):
                dest.mux(packet)
        for packet in stream.encode():
            dest.mux(packet)
    chapter.update(verify(path, len(selected), [chapter]))
    return chapter


def concatenate(out, chapters):
    path = out / 'astra_flora_all_50_4x.mp4'
    assert not path.exists()
    start = 0
    with av.open(str(out / chapters[0]['file'])) as first:
        with av.open(str(path), 'w', options={'movflags': '+faststart'}) as dest:
            dest.metadata.update(metadata())
            output = dest.add_stream_from_template(first.streams.video[0])
            for c in chapters:
                with av.open(str(out / c['file'])) as source:
                    stream = source.streams.video[0]
                    offset = Fraction(start, 30) / stream.time_base
                    assert offset.denominator == 1
                    for packet in source.demux(stream):
                        if packet.pts is None or packet.dts is None:
                            continue
                        packet.pts += int(offset)
                        packet.dts += int(offset)
                        packet.stream = output
                        dest.mux(packet)
                c.update(start_output_frame=start, end_output_frame=start + c['encoded_frames'],
                         start_seconds=start / 30)
                start += c['encoded_frames']
    return verify(path, start, chapters)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--reuse-rendered', action='store_true', help='Verify existing episode MP4s without overwriting them')
    a = p.parse_args()
    out = a.out.resolve()
    assert not out.exists() or a.reuse_rendered, 'Choose a new version; no presentation artifacts are overwritten'
    assert not (out / 'manifest.json').exists() and not (out / 'astra_flora_all_50_4x.mp4').exists(), 'Completed presentation already exists'
    study = json.loads((REPO / 'outputs/oopsie_distillation_full_v1/study.json').read_text())
    source = REPO / study['config']['source_run']
    manifest_path = source / 'manifest.json'
    assert sha(manifest_path) == study['source_manifest_sha256']
    episodes = {e['id']: e for e in json.loads(manifest_path.read_text())['episodes']}
    run = REPO / 'outputs/flora_development50_20261110_v2'
    dense = run / 'results/dense_3572125/dense.jsonl'
    flora_rows = [json.loads(line) for line in dense.read_text().splitlines()]
    ids = study['development_ids']
    assert len(ids) == 50 and [r['id'] for r in flora_rows] == ids
    references = json.loads((run / 'evaluation/reference.json').read_text())['episodes']
    canonical = {r['episode']: r['annotation_sha256'] for r in study['episodes']}
    out.mkdir(exist_ok=a.reuse_rendered)
    (out / 'episodes').mkdir(exist_ok=a.reuse_rendered)
    (out / 'annotations').mkdir(exist_ok=a.reuse_rendered)
    jobs, hashes = [], {}
    source_position = 0
    for position, (eid, row) in enumerate(zip(ids, flora_rows, strict=True)):
        e = episodes[eid]
        assert e['split'] == 'development' and row['num_frames'] == e['n_frames']
        assert row['fps'] == e['fps'] and row['invalid_clips'] == 0 and all(c['valid'] for c in row['clips'])
        native = source / 'traces' / (eid + '_sol_r01') / 'annotation.md'
        assert sha(native) == canonical[eid]
        hashes[eid] = sha(native)
        teacher = original.recipe.parse_prediction(native.read_text(encoding='utf-8').split('## Failure annotations')[0],
                                                   eid, 0, e['n_frames'])
        assert original.scoring.labels(teacher, e['n_frames']) == references[eid]['frame_labels']
        values = []
        for s in row['segments']:
            assert s['start_frame'] == len(values)
            values.extend([s['score']] * (s['end_frame'] - s['start_frame']))
        assert values == row['frame_scores'] and len(values) == e['n_frames']
        repeats = 30 / e['fps']
        assert repeats == int(repeats)
        repeats = int(repeats)
        native_count = e['n_frames'] * repeats
        first = source_position + (-source_position % 4)
        selected = [(i - source_position) // repeats for i in range(first, source_position + native_count, 4)]
        assert selected and len(e['images']) == e['n_frames']
        source_position += native_count
        copied = out / 'annotations' / (eid + '_teacher_native.md')
        if copied.exists():
            assert copied.read_bytes() == native.read_bytes(), 'Preserved teacher copy changed'
        else:
            copied.write_bytes(native.read_bytes())
        jobs.append((str(source), str(out), e, position, teacher, row['segments'], selected, a.reuse_rendered))
    records = []
    with ProcessPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(render, job) for job in jobs]
        for future in as_completed(futures):
            records.append(future.result())
            print(f"Rendered and verified {len(records)}/50: {records[-1]['episode']}", flush=True)
            (out / 'progress.md').write_text(f'# FLORA presentation export\n\nRendered and verified {len(records)}/50 episodes.\n')
    records.sort(key=lambda r: r['position'])
    checked = concatenate(out, records)
    assert checked['encoded_frames'] == (source_position + 3) // 4 == 5099
    prior = json.loads((REPO / 'outputs/astra_joint_presentation_50_20261109_v1/speed_4x_manifest.json').read_text())
    assert prior['encoded_frames'] == checked['encoded_frames']
    assert abs(prior['duration_seconds'] - checked['duration_seconds']) < .001
    result = dict(episodes=50, split='development', teacher_display_name='Astra',
                  teacher_source_model='gpt-6.1-sol', teacher_display_name_is_alias=True,
                  flora_model='nvidia/Flora-Rewarder', flora_job=3572125, flora_native_sha256=sha(dense),
                  teacher_native_sha256=hashes, source_manifest_sha256=sha(manifest_path),
                  speed_multiplier=4, visible_speed_label='Sped up 4\u00d7',
                  frame_selection='Every fourth global 30 FPS presentation frame, starting at frame zero; same as Qwen 4x MP4',
                  flora_native_three_class_labels=True, binary_display_mapping='Failure only: 1 vs 2/3',
                  smoothing_applied=False, native_outputs_modified=False,
                  new_teacher_calls=0, new_inference_calls=0, final_test_accessed=False,
                  compilation=checked, chapters=records)
    (out / 'manifest.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    lines = ['# Astra / FLORA: all 50 validation episodes at 4x', '',
             'One MP4, same frozen episode order and exactly the same frame selection, duration and '
             '1920x1080 / 30 FPS presentation format as the joint-Qwen 4x export.', '',
             'Left: Astra, the requested display alias for preserved Sol (`gpt-6.1-sol`) annotations. '
             'Right: FLORA native failure (red), suboptimal (amber), normal (green), with the failure-only '
             'binary mapping also shown. Both panels show identical synchronized source cameras.', '',
             'Derived presentation of preserved outputs; no inference, new labeling, smoothing or native-output edits. '
             'The visible speed banner reads Sped up 4\u00d7. At 4x/30 FPS, brief source spans can fall between displayed '
             'frames, as in the Qwen export. Full native segments remain in the source report.', '',
             f"Duration: {checked['duration_seconds']:.3f} seconds. All 5,099 encoded frames were decoded to check "
             'timestamps, both label colors, the speed banner, and all 50 chapter boundaries.', '',
             '| Episode | Presentation start | Episode MP4 |', '|---|---|---|']
    for c in records:
        lines.append(f"| {c['episode']} | {original.timestamp(c['start_seconds'])} | [{c['episode']}]({c['file']}) |")
    (out / 'README.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    links = ''.join(f'<li><button onclick="v.currentTime={c["start_seconds"]};v.play()">{c["episode"]}</button> '
                    f'{html.escape(c["task"])}</li>' for c in records)
    (out / 'index.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1"><title>Astra / FLORA, 4x</title>'
        '<style>body{font:17px/1.5 system-ui;background:#101722;color:#edf3fb;max-width:1500px;margin:auto;padding:24px}'
        'a{color:#c8baff}video{width:100%;background:#000}li{margin:9px 0}button{cursor:pointer;padding:6px}</style>'
        '<h1>Astra / FLORA — all 50 validation episodes, 4×</h1>'
        '<video id="v" controls playsinline preload="metadata" src="astra_flora_all_50_4x.mp4"></video>'
        '<p><a href="astra_flora_all_50_4x.mp4" download>Download single MP4</a> · '
        '<a href="README.md">Export notes and provenance</a></p><ol>' + links + '</ol></html>', encoding='utf-8')
    print(json.dumps(dict(complete=True, output=str(out), compilation=checked)), flush=True)


if __name__ == '__main__':
    main()
