"""Export saved development predictions as annotated videos; no model/API calls."""
import argparse
from fractions import Fraction
import hashlib
import html
import json
from pathlib import Path
import sys
import zipfile

import av
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'scripts/distill'))
import oopsie_recipe_data as data
import score_recipe_suite as scoring

SPECS = [
    dict(episode='O9014', start=224, end=584, title='Strongest sustained-failure match',
         note='Qwen starts predicting failure at 9.60 s. Sol labels the whole episode as failure; Qwen misses its beginning.'),
    dict(episode='O9008', start=676, end=924, title='Partial detection of sustained failure',
         note='This clip includes the longest correctly detected fragment. Qwen interrupts the failure timeline and misses much of the full interval.'),
    dict(episode='O9064', start=84, end=164, title='Grasp failure detected very late',
         note='Sol marks failed acquisition from 12.40 s. Qwen predicts failure only for the final 0.40 s; this is a limited detection, not a strong localization result.'),
]
SIZE = (1600, 1000)
COLORS = {True: '#a33542', False: '#226b51', None: '#566170'}


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def font(size, bold=False):
    return ImageFont.truetype('C:/Windows/Fonts/' + ('seguisb.ttf' if bold else 'segoeui.ttf'), size)


def read_prediction(run, episode):
    values = [None] * episode['n_frames']
    files = sorted((run / 'predictions/evidence_aux').glob(episode['id'] + '_*_binary.json'))
    for path in files:
        row = json.loads(path.read_text(encoding='utf-8'))
        if row['hit_max']:
            raise ValueError('Selected prediction reached token cap')
        segments = data.parse_prediction(row['text'], episode['id'], row['core_start'], row['core_end'])
        a, b = row['core_start'], row['core_end']
        if any(v is not None for v in values[a:b]):
            raise ValueError('Scored cores overlap')
        for s in segments:
            values[s['start_frame']:s['end_frame']] = [bool(s['failure'])] * (s['end_frame'] - s['start_frame'])
    if None in values:
        raise ValueError('Selected episode has missing predictions')
    return values, scoring.segments(values), files


def label_at(segments, frame):
    return next(s for s in segments if s['start_frame'] <= frame < s['end_frame'])


def draw_frame(source, episode, frame, start, end, predicted, reference, base):
    canvas = base.copy()
    draw = ImageDraw.Draw(canvas)
    fps = episode['fps']
    draw.text((24, 140), f'Source time {frame / fps:.2f} s | frame {frame} | clip {start / fps:.2f}-{end / fps:.2f} s | original speed',
              font=font(21), fill='#c5d4e5')
    item = episode['images'][frame]
    path = source / item['path']
    if sha(path) != item['sha256']:
        raise ValueError('Original model-input image changed')
    with Image.open(path) as raw:
        original = raw.convert('RGB')
        image = ImageOps.contain(original, (1552, 515), Image.Resampling.LANCZOS)
        x, y = (1600 - image.width) // 2, 190 + (515 - image.height) // 2
        canvas.paste(image, (x, y))
        for panel in item['panels']:
            px = x + round(panel['x'] * image.width / original.width)
            draw.text((px + 6, 170), panel['camera'], font=font(19, True), fill='#d8e4f1')
    for name, segments, top in [('QWEN', predicted, 728), ('SOL REFERENCE', reference, 790)]:
        s = label_at(segments, frame)
        draw.rounded_rectangle((24, top, 388, top + 48), radius=8, fill=COLORS[s['failure']])
        draw.text((40, top + 7), name + ': ' + ('FAILURE' if s['failure'] else 'NON-FAILURE'),
                  font=font(24, True), fill='white')
        draw.text((410, top + 8), f"Frames [{s['start_frame']}, {s['end_frame']}) | {s['start_frame'] / fps:.2f}-{s['end_frame'] / fps:.2f} s",
                  font=font(24), fill='#e6edf7')
    for name, segments, top in [('Qwen timeline', predicted, 878), ('Sol timeline', reference, 930)]:
        draw.text((24, top - 5), name, font=font(22), fill='#d2dfed')
        draw.rectangle((210, top, 1576, top + 21), fill=COLORS[None])
        for s in segments:
            a, b = max(start, s['start_frame']), min(end, s['end_frame'])
            if a < b:
                left = 210 + round(1366 * (a - start) / (end - start))
                right = 210 + round(1366 * (b - start) / (end - start))
                draw.rectangle((left, top, max(left, right - 1), top + 21), fill=COLORS[s['failure']])
        cursor = 210 + round(1366 * (frame - start) / (end - start))
        draw.rectangle((cursor, top - 4, cursor + 2, top + 25), fill='white')
    draw.text((24, 968), 'Red = failure | Green = non-failure | Sol is a teacher reference, not verified human ground truth.',
              font=font(20), fill='#bacbdd')
    return canvas


def render(source, out, episode, start, end, predicted, reference, title,
           recipe_label='explanation auxiliary training'):
    if out.exists():
        raise ValueError('Export already exists; refusing to overwrite')
    fps = Fraction(str(episode['fps'])).limit_denominator(1000)
    base = Image.new('RGB', SIZE, '#101722')
    draw = ImageDraw.Draw(base)
    draw.text((24, 16), episode['id'] + ' | ' + title, font=font(35, True), fill='#f1f5fb')
    draw.text((24, 65), 'Qwen2.5-VL-7B | ' + recipe_label + ' | held-out development example', font=font(23), fill='#c6b7ff')
    draw.text((24, 102), 'Task: ' + episode['task'], font=font(27), fill='#eff4fb')
    first = None
    with av.open(str(out), 'w', options={'movflags': '+faststart'}) as container:
        stream = container.add_stream('libx264', rate=fps)
        stream.width, stream.height = SIZE
        stream.pix_fmt = 'yuv420p'
        stream.options = {'crf': '18', 'preset': 'fast'}
        stream.codec_context.thread_count = 6
        for index, frame in enumerate(range(start, end)):
            canvas = draw_frame(source, episode, frame, start, end, predicted, reference, base)
            if first is None:
                first = canvas
                canvas.save(out.with_suffix('.jpg'), quality=94)
            encoded = av.VideoFrame.from_image(canvas)
            encoded.pts, encoded.time_base = index, 1 / fps
            for packet in stream.encode(encoded):
                container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)
    return verify_render(out, start, end, fps, predicted, reference)


def verify_render(out, start, end, fps, predicted, reference):
    # Verify timing and the burned-in label colors on every decoded frame.
    count = 0
    with av.open(str(out)) as container:
        for index, frame in enumerate(container.decode(video=0)):
            if abs(float(frame.pts * frame.time_base) - index / float(fps)) > 1e-5:
                raise ValueError('Encoded video timing differs from source')
            pixels = frame.to_ndarray(format='rgb24')
            for track, y in [(predicted, 750), (reference, 812)]:
                value = label_at(track, start + index)['failure']
                expected = np.array([int(COLORS[value][i:i + 2], 16) for i in (1, 3, 5)])
                if np.max(np.abs(pixels[y, 30].astype(int) - expected)) > 25:
                    raise ValueError('Burned-in label differs from saved prediction')
            count += 1
    if count != end - start:
        raise ValueError('Encoded frame count differs from selected interval')
    return dict(frames=count, fps=float(fps), duration_seconds=count / float(fps),
                sha256=sha(out), every_encoded_label_verified=True)


def timestamp(seconds):
    ms = round(seconds * 1000)
    return f'{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}'


def subtitles(path, start, end, fps, predicted, reference):
    boundaries = sorted({start, end} | {max(start, min(end, s[k])) for track in (predicted, reference)
                                       for s in track for k in ('start_frame', 'end_frame')})
    rows = []
    for index, (a, b) in enumerate(zip(boundaries, boundaries[1:]), 1):
        p, r = label_at(predicted, a), label_at(reference, a)
        rows.append(f"{index}\n{timestamp((a - start) / fps)} --> {timestamp((b - start) / fps)}\n"
                    f"Qwen: {'Failure' if p['failure'] else 'Non-failure'} | Sol reference: {'Failure' if r['failure'] else 'Non-failure'}\n"
                    f'Source frames [{a}, {b})\n')
    path.write_text('\n'.join(rows), encoding='utf-8')


def montage(clips, path):
    fps = Fraction(30)
    index = 0
    with av.open(str(path), 'w', options={'movflags': '+faststart'}) as destination:
        stream = destination.add_stream('libx264', rate=fps)
        stream.width, stream.height = SIZE
        stream.pix_fmt = 'yuv420p'
        stream.options = {'crf': '18', 'preset': 'fast'}
        stream.codec_context.thread_count = 6
        for clip_path, rate in clips:
            repeats = 30 / rate
            if repeats != int(repeats):
                raise ValueError('Montage requires an integer source-rate multiplier')
            with av.open(str(clip_path)) as source:
                for frame in source.decode(video=0):
                    pixels = frame.to_ndarray(format='rgb24')
                    for _ in range(int(repeats)):
                        converted = av.VideoFrame.from_ndarray(pixels, format='rgb24')
                        converted.pts, converted.time_base = index, 1 / fps
                        for packet in stream.encode(converted):
                            destination.mux(packet)
                        index += 1
        for packet in stream.encode():
            destination.mux(packet)
    with av.open(str(path)) as source:
        if sum(1 for _ in source.decode(video=0)) != index:
            raise ValueError('Montage frame count mismatch')
    return dict(frames=index, fps=30, duration_seconds=index / 30, sha256=sha(path))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--resume-existing', action='store_true')
    args = parser.parse_args()
    out = args.out.resolve()
    if (out / 'manifest.json').exists():
        raise ValueError('Export already complete; choose a new version')
    out.mkdir(parents=True, exist_ok=True)
    run = REPO / 'outputs/oopsie_distillation_local_sequential_v1'
    study = json.loads((REPO / 'outputs/oopsie_distillation_full_v1/study.json').read_text())
    source = REPO / study['config']['source_run']
    manifest = json.loads((source / 'manifest.json').read_text())
    episodes = {e['id']: e for e in manifest['episodes']}
    scores = {p.stem: json.loads(p.read_text()) for p in (run / 'arm_scores').glob('*.json')}
    best = max(scores, key=lambda name: scores[name]['metrics']['failure_f1'] or -1)
    if best != 'evidence_aux':
        raise ValueError('Best completed model changed; reconsider selected examples')
    score = scores[best]
    per_episode = {e['episode']: e for e in score['per_episode']}
    exports = []
    for spec in SPECS:
        eid = spec['episode']
        e = episodes[eid]
        if e['split'] != 'development' or eid not in study['development_ids']:
            raise ValueError('Examples must not access the final test set')
        values, predicted, files = read_prediction(run, e)
        native = source / 'traces' / (eid + '_sol_r01') / 'annotation.md'
        teacher = native.read_text(encoding='utf-8')
        reference = data.parse_prediction(teacher.split('## Failure annotations')[0], eid, 0, e['n_frames'])
        canonical = next(row for row in study['episodes'] if row['episode'] == eid)
        if sha(native) != canonical['annotation_sha256']:
            raise ValueError('Native Sol reference changed')
        folder = out / 'native' / eid
        folder.mkdir(parents=True, exist_ok=True)
        (folder / 'sol_annotation.md').write_bytes(native.read_bytes())
        for path in files:
            row = json.loads(path.read_text())
            (folder / (path.stem + '.md')).write_text(row['text'], encoding='utf-8', newline='')
        notes = ['# ' + eid + ': saved Qwen predictions', '', '- Derived episode timeline stitched from native Qwen window outputs.',
                 '- Start frame is inclusive; end frame is exclusive. No predictions were regenerated.', '', data.table(eid, predicted),
                 '## Interpretation', '', spec['note'], '', '## Native Sol reference', '', teacher]
        (out / (eid + '_predictions.md')).write_text('\n'.join(notes) + '\n', encoding='utf-8')
        video = out / (eid + '_annotated.mp4')
        if args.resume_existing and video.exists():
            checked = verify_render(video, spec['start'], spec['end'], Fraction(str(e['fps'])), predicted, reference)
        else:
            checked = render(source, video, e, spec['start'], spec['end'], predicted, reference, spec['title'])
        subtitles(out / (eid + '_labels.srt'), spec['start'], spec['end'], e['fps'], predicted, reference)
        exports.append(dict(spec, task=e['task'], lab=e['lab'],
            source_start_seconds=spec['start'] / e['fps'], source_end_seconds=spec['end'] / e['fps'],
            video=video.name, poster=video.with_suffix('.jpg').name, **checked,
            full_episode_metrics=per_episode[eid]['metrics'], predicted_segments=predicted, teacher_segments=reference,
            native_prediction_sources=[dict(path=str(p.relative_to(REPO)), sha256=sha(p)) for p in files],
            source_annotation_sha256=sha(native)))
        print(json.dumps(dict(exported=eid, **checked)), flush=True)
    highlights = montage([(out / e['video'], e['fps']) for e in exports], out / 'highlights.mp4')
    lines = ['# Qwen failure prediction examples', '',
        '- Model: Qwen2.5-VL-7B-Instruct, explanation auxiliary SFT (`evidence_aux`).',
        f"- Best completed local recipe by development failure F1: {score['metrics']['failure_f1']:.2%}; recall {score['metrics']['failure_recall']:.2%}; failure IoU {score['metrics']['failure_iou']:.2%}.",
        '- Three selected development examples. They are illustrations selected after inspecting scores, not a representative evaluation sample.',
        '- The strongest match is sustained inactivity. The grasp example has very late detection and is included to make the limitation visible.',
        '- Sol labels are teacher references, not independently verified human ground truth.',
        '- Videos show the exact preprocessed camera panels available to the student at native episode speed. No frame thinning.',
        '- Qwen produces binary intervals here. The explanation-auxiliary recipe does not make these binary predictions explanatory outputs.',
        '- Source times and boundaries remain in original episode coordinates. Clip subtitles use clip-local playback times.',
        '- Native outputs are preserved under native/. Companion prediction tables are derived stitched episode timelines.',
        '- No API calls, model inference, GPU training, or pipeline restart were performed for this export.', '',
        '[Play the gallery](index.html) · [Download the highlights video](highlights.mp4)', '',
        '| Episode | Clip source time | Full-episode failure F1 | Description |', '|---|---|---:|---|']
    for e in exports:
        lines.append(f"| {e['episode']} | {e['source_start_seconds']:.2f}-{e['source_end_seconds']:.2f} s | {e['full_episode_metrics']['failure_f1']:.2%} | {e['note']} |")
    (out / 'README.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    cards = []
    for e in exports:
        cards.append(f'''<section id="{e['episode']}"><h2>{e['episode']} · {html.escape(e['title'])}</h2>
<p>{html.escape(e['task'])}</p><video controls playsinline preload="metadata" poster="{e['poster']}" src="{e['video']}"></video>
<p>{html.escape(e['note'])}</p><p class="muted">Source {e['source_start_seconds']:.2f}–{e['source_end_seconds']:.2f} s · original speed · full-episode failure F1 {e['full_episode_metrics']['failure_f1']:.1%}</p>
<nav><a href="{e['video']}" download>Download MP4</a><a href="{e['episode']}_predictions.md">Full prediction timelines</a><a href="{e['episode']}_labels.srt" download>Subtitles</a></nav></section>''')
    page = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Qwen failure predictions · selected examples</title><style>
body{margin:0 auto;max-width:1300px;padding:28px 20px 60px;background:#101722;color:#edf3fb;font:17px/1.55 system-ui}
h1{font-size:31px;line-height:1.2}h2{font-size:23px}p{max-width:1050px}a{color:#c1b5ff}nav{display:flex;gap:22px;flex-wrap:wrap}
section{padding:22px;margin:24px 0;background:#192332;border:1px solid #3d5068;border-radius:12px}video{display:block;width:100%;background:#070b10;border-radius:8px}.muted{color:#b9c9dc}
</style><h1>Qwen failure predictions</h1><p>Qwen2.5-VL-7B with explanation auxiliary training. Best completed local development failure F1: <strong>58.51%</strong>.</p>
<p>These are selected examples, not a representative benchmark. Red means failure; green means non-failure. Both Qwen predictions and Sol reference labels are burned into every frame. Sol is a teacher reference, not verified human ground truth.</p>
<nav><a href="highlights.mp4" download>Download all three clips as one MP4</a><a href="README.md">Selection notes</a></nav>''' + ''.join(cards) + '</html>'
    (out / 'index.html').write_text(page, encoding='utf-8')
    artifact = dict(model='Qwen/Qwen2.5-VL-7B-Instruct', recipe=best, split='development',
        final_test_accessed=False, api_calls=0, model_inference_calls=0, training_started=False,
        source_run=str(source.relative_to(REPO)), student_run=str(run.relative_to(REPO)),
        official_score_sha256=sha(run / 'arm_scores/evidence_aux.json'), official_metrics=score['metrics'],
        examples=exports, highlights=highlights)
    (out / 'manifest.json').write_text(json.dumps(artifact, indent=2) + '\n', encoding='utf-8')
    archive = out.with_suffix('.zip')
    if archive.exists():
        raise ValueError('Archive already exists; refusing overwrite')
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted(out.rglob('*')):
            if path.is_file():
                bundle.write(path, arcname=out.name + '/' + path.relative_to(out).as_posix())
    print(json.dumps(dict(complete=True, gallery=str(out / 'index.html'), archive=str(archive), highlights=highlights)), flush=True)


if __name__ == '__main__':
    main()
