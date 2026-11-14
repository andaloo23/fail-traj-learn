"""Review all saved development predictions and export additional video examples.

Runs on CPU with preserved outputs; no teacher calls, inference or training.
Unknown baseline outputs stay unknown. The final test remains sealed.
"""
from collections import Counter
import hashlib
import html
import json
import os
from pathlib import Path
import sys
import zipfile

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'scripts/distill'))
import oopsie_recipe_data as data
import score_recipe_suite as scoring
import failure_enrichment_v8_1 as enrichment
import export_qwen_failure_examples as clips

OUT = REPO / 'outputs/qwen_development_results_20261109_v2'
RUN = REPO / 'outputs/oopsie_distillation_local_sequential_v1'
MODELS = {
    'evidence_aux': 'Qwen · explanation auxiliary',
    'joint': 'Qwen · joint training',
    'binary': 'Qwen · binary only',
    'categories_aux': 'Qwen · category auxiliary',
    'base': 'Qwen · pretrained baseline',
}
EXAMPLES = [
    ('O9130', 'joint', 85, 143, 'Failed grasp detected by joint Qwen', 'Joint Qwen closely matches the final failed-acquisition interval; the explanation-auxiliary model misses it.'),
    ('O9013', 'categories_aux', 32, 134, 'Object placed outside the bowl', 'The category-auxiliary model detects a short portion of the placement failure; most of the Sol interval is missed.'),
    ('O9129', 'joint', 60, 139, 'Collision during placement', 'The joint model partly overlaps the collision but its predicted boundaries include false-positive frames.'),
    ('O9083', 'joint', 92, 140, 'Missed grasp with late detection', 'The joint model detects only a short part of the failed withdrawal.'),
    ('O9163', 'joint', 80, 134, 'Ball remains after grasp attempt', 'A brief joint-model detection overlaps the missed grasp; other predicted failure frames disagree with Sol.'),
    ('O9191', 'evidence_aux', 88, 129, 'Very late ball-grasp detection', 'The explanation-auxiliary model labels only the final frame as failure.'),
    ('O9023', 'evidence_aux', 58, 148, 'Bowl acquisition missed by Qwen', 'The explanation-auxiliary model predicts non-failure throughout this Sol-labeled failed grasp.'),
    ('O9079', 'evidence_aux', 24, 86, 'Failure prediction disagrees with Sol', 'Qwen predicts failure near the end, while Sol labels the entire episode non-failure. Human review must judge the disagreement.'),
    ('O9116', 'evidence_aux', 96, 177, 'Another failure disagreement', 'Qwen predicts failure during the final withdrawal; Sol reports no failure. This illustrates a disagreement, not a verified false alarm.'),
]


def runs(values):
    result = []
    for frame, value in enumerate(values):
        if result and result[-1]['failure'] == value:
            result[-1]['end_frame'] = frame + 1
        else:
            result.append(dict(start_frame=frame, end_frame=frame + 1, failure=value))
    return result


def prediction(episode, model):
    values = [None] * episode['n_frames']
    seen = [False] * episode['n_frames']
    sources = []
    for path in sorted((RUN / 'predictions' / model).glob(episode['id'] + '_*_binary.json')):
        row = json.loads(path.read_text(encoding='utf-8'))
        a, b = row['core_start'], row['core_end']
        if any(seen[a:b]):
            raise ValueError('Duplicate scored core')
        seen[a:b] = [True] * (b - a)
        reason = None
        try:
            if row['hit_max']:
                raise ValueError('Generation reached token cap')
            parsed = data.parse_prediction(row['text'], episode['id'], a, b)
            for s in parsed:
                values[s['start_frame']:s['end_frame']] = [bool(s['failure'])] * (s['end_frame'] - s['start_frame'])
        except ValueError as error:
            reason = str(error)
        sources.append(dict(path=path, row=row, invalid_reason=reason))
    if not all(seen):
        raise ValueError('Saved development generation is incomplete')
    return values, runs(values), sources


def timeline(eid, segments):
    return '# Episode: ' + eid + '\n\n| Start frame | End frame | Failure |\n| --- | --- | --- |\n' + ''.join(
        f"| {s['start_frame']} | {s['end_frame']} | {'Unknown' if s['failure'] is None else 'Yes' if s['failure'] else 'No'} |\n"
        for s in segments)


def make_template():
    text = (REPO / 'scripts/distill/oopsie_bulk_review.html').read_text(encoding='utf-8')
    replacements = [
        ("document.title=revision+' Sol labels';document.querySelector('h1').textContent=revision+' · Sol annotations';",
         "document.title='Qwen development comparison';document.querySelector('h1').textContent='Qwen development comparison';"),
        ("const data=__DATA__, $=id=>document.getElementById(id), storageKey='binary-v9-'+data.manifest_sha256;",
         "const data=__DATA__, $=id=>document.getElementById(id), storageKey='qwen-development-'+data.manifest_sha256;\n"
         "const labelText=s=>s.failure===null?'Unknown':s.failure?'Failure':'Non-failure';\n"
         "const labelClass=s=>s.failure===null?'unknown':s.failure?'failure':'nonfailure';"),
        ("label.textContent=segment.failure?'Failure':'Non-failure';label.className='current-label '+(segment.failure?'failure':'nonfailure');",
         "label.textContent=labelText(segment);label.className='current-label '+labelClass(segment);"),
        ("el('button',s.failure?'Failure':'Non-failure',s.failure?'fail':'')",
         "el('button',labelText(s),s.failure===null?'unknown':s.failure?'fail':'')"),
        ("button.title=(s.failure?'Failure':'Non-failure')+' · '", "button.title=labelText(s)+' · '"),
        ("el('td',s.failure?'Failure':'Non-failure',s.failure?'failure':'nonfailure')", "el('td',labelText(s),labelClass(s))"),
        ("...['v8','v9'].flatMap", "...Object.keys(current.teachers).flatMap"),
        ("    $('videos').replaceChildren();\n    videos=[];",
         "    for(const video of videos){video.onloadedmetadata=null;video.onerror=null;video.onended=null;video.pause();video.removeAttribute('src');video.load();}\n"
         "    $('videos').replaceChildren();\n    videos=[];"),
        ("summary=el('summary','Complete native Markdown')", "summary=el('summary',value.markdown_is_derived?'Saved window outputs (derived compilation)':'Complete native Markdown')"),
        ("const link=el('a','Download native Markdown','download')", "const link=el('a',value.markdown_is_derived?'Download stitched timeline (derived)':'Download native Markdown','download')"),
        ("result='# Sol V8.1 episode review", "result='# Qwen development comparison review"),
        ("'sol-v8-1-review.md'", "'qwen-development-review.md'"),
    ]
    for old, new in replacements:
        if text.count(old) != 1:
            raise ValueError('Expected one template anchor: ' + old)
        text = text.replace(old, new)
    text = text.replace('One V8.1 Sol annotation per episode: failure labels, taxonomy and visible explanations.',
                        'Five completed Qwen variants and the Sol reference on all 50 development episodes.')
    text = text.replace('aria-label="Sol failure annotation"', 'aria-label="Qwen model predictions and Sol reference"')
    text = text.replace('</style>', '#teachers{display:grid;grid-template-columns:repeat(auto-fit,minmax(440px,1fr));gap:16px}.teacher{margin:0}.unknown{color:#bcc7d4}.timeline button.unknown{background:#606c7e}.teacher table{font-size:14px}pre{overflow-wrap:anywhere}@media(max-width:700px){#teachers{grid-template-columns:1fr}}</style>')
    return text


def build_review(out):
    study = json.loads((REPO / 'outputs/oopsie_distillation_full_v1/study.json').read_text())
    source = REPO / study['config']['source_run']
    manifest = json.loads((source / 'manifest.json').read_text())
    ids = set(study['development_ids'])
    episodes = [e for e in manifest['episodes'] if e['id'] in ids]
    if len(episodes) != 50 or any(e['split'] != 'development' for e in episodes):
        raise ValueError('Expected exactly 50 development episodes; final test stays sealed')
    first = [s[0] for s in EXAMPLES] + ['O9014', 'O9008', 'O9064']
    order = {eid: i for i, eid in enumerate(first)}
    episodes.sort(key=lambda e: (order.get(e['id'], 1000), e['id']))
    official = {m: json.loads((RUN / 'arm_scores' / (m + '.json')).read_text()) for m in MODELS}
    totals = {m: Counter() for m in MODELS}
    hashes = {}
    objects = []
    cached = {}
    for e in episodes:
        eid = e['id']
        native = source / 'traces' / (eid + '_sol_r01') / 'annotation.md'
        teacher = native.read_text(encoding='utf-8')
        canonical = next(r for r in study['episodes'] if r['episode'] == eid)
        if clips.sha(native) != canonical['annotation_sha256']:
            raise ValueError('Sol reference changed')
        value = enrichment.parse(teacher, e)
        reference = value['segments']
        target = out / 'labels' / eid
        target.mkdir(parents=True)
        (target / 'sol_native.md').write_bytes(native.read_bytes())
        tracks = {'sol': [dict(repeat=1, segments=reference, failure_annotations=value['failure_annotations'],
                              native_markdown=teacher, markdown=f'labels/{eid}/sol_native.md')]}
        for model in MODELS:
            values, segments, sources = prediction(e, model)
            totals[model].update(scoring.counts(values, scoring.labels(reference, e['n_frames'])))
            compilation = [f'# {eid}: preserved {MODELS[model]} window outputs', '',
                           'This is a derived compilation. Each quoted window response is the unchanged saved model output.', '']
            for record in sources:
                row = record['row']
                name = record['path'].stem + '.md'
                folder = target / model
                folder.mkdir(exist_ok=True)
                (folder / name).write_text(row['text'], encoding='utf-8', newline='')
                hashes[str(record['path'].relative_to(REPO))] = clips.sha(record['path'])
                compilation.extend([f"## Source core [{row['core_start']}, {row['core_end']})", '',
                                    'Strict output: ' + ('invalid; shown as Unknown' if record['invalid_reason'] else 'valid'), '', row['text'], ''])
            stitched = timeline(eid, segments)
            (target / (model + '_timeline.md')).write_text('# Derived stitched prediction timeline\n\n' + stitched, encoding='utf-8')
            (target / (model + '_window_outputs.md')).write_text('\n'.join(compilation), encoding='utf-8')
            tracks[model] = [dict(repeat=1, segments=segments, native_markdown='\n'.join(compilation),
                                  markdown=f'labels/{eid}/{model}_timeline.md', markdown_is_derived=True)]
            cached[(eid, model)] = (segments, reference)
        videos = []
        for index, v in enumerate(e['videos']):
            relative = f"media/{eid}/camera_{index}.mp4"
            path = out / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            os.link(source / v['url'], path)
            videos.append(dict(v, url=relative))
        objects.append(dict(id=eid, task=e['task'], split=e['split'], lab=e['lab'], fps=e['fps'],
                            n_frames=e['n_frames'], videos=videos, teachers=tracks, source_run=source.name))
    for model in MODELS:
        actual = scoring.metrics(totals[model])
        for key, expected in official[model]['metrics'].items():
            found = actual[key]
            if isinstance(expected, float):
                if abs(expected - found) > 1e-12:
                    raise ValueError('Derived predictions disagree with official score: ' + model + '/' + key)
            elif found != expected:
                raise ValueError('Derived prediction counts disagree with official score')
    template = make_template()
    fingerprint = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()
    review = dict(protocol='all_completed_qwen_development_review_v2', manifest_sha256=fingerprint,
        review_ui_version=hashlib.sha256(template.encode()).hexdigest(), prompt_revision='Qwen development',
        side_labels=dict(sol='Sol · teacher reference', **MODELS), side_repeats={m: 1 for m in ['sol'] + list(MODELS)},
        planned_responses=len(objects) * 6, episodes=objects, repeats=1,
        status_message='All 50 development episodes; five completed Qwen variants. Gray = unknown/invalid baseline output.',
        rich_prompt_description='Compare synchronized native videos and saved predictions. Sol is a teacher reference, not human ground truth. Native baseline format failures remain Unknown.')
    encoded = json.dumps(review, ensure_ascii=False).replace('<', '\\u003c').replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')
    (out / 'review.html').write_text(template.replace('__DATA__', encoded), encoding='utf-8')
    (out / 'review_data.json').write_text(json.dumps(review, ensure_ascii=False), encoding='utf-8')
    (out / 'review_template.html').write_text(template, encoding='utf-8')
    (out / 'prompt.md').write_bytes((source / 'prompt.md').read_bytes())
    (out / 'provenance.json').write_text(json.dumps(dict(source_run=str(source.relative_to(REPO)),
        episodes=50, model_tracks=300, source_prediction_sha256=hashes, final_test_accessed=False,
        api_calls=0, inference_calls=0, training_started=False, official_metrics_reproduced=True), indent=2), encoding='utf-8')
    report = ['# Completed Qwen development results', '',
              '- Every one of the 50 development episodes is available with all five completed Qwen variants and Sol.',
              '- Labels are visible by default. Optional blind review applies across episodes and reloads.',
              '- Gray baseline intervals are invalid/unknown outputs; they are never relabeled as non-failure.',
              '- All frame counts and metrics exactly reproduce the existing official development scores.',
              '- Final test remains sealed. No API calls, model inference, training or pipeline restart.', '',
              (RUN / 'results.md').read_text(encoding='utf-8')]
    (out / 'report.md').write_text('\n'.join(report), encoding='utf-8')
    return source, {e['id']: e for e in episodes}, official, cached


def build_clips(out, source, episodes, scores, cache):
    folder = out / 'clips'
    folder.mkdir()
    items = []
    for eid, model, start, end, title, note in EXAMPLES:
        e = episodes[eid]
        predicted, reference = cache[(eid, model)]
        if any(s['failure'] is None for s in predicted):
            raise ValueError('Burned-in examples require valid selected-model predictions')
        name = f'{eid}_{model}.mp4'
        info = clips.render(source, folder / name, e, start, end, predicted, reference, title,
                            recipe_label=MODELS[model].replace('Qwen · ', ''))
        clips.subtitles(folder / name.replace('.mp4', '.srt'), start, end, e['fps'], predicted, reference)
        metric = next(r['metrics'] for r in scores[model]['per_episode'] if r['episode'] == eid)
        item = dict(episode=eid, model=model, model_name=MODELS[model], title=title, note=note, task=e['task'],
                    file='clips/' + name, poster='clips/' + name.replace('.mp4', '.jpg'),
                    start_frame=start, end_frame=end, source_start_seconds=start / e['fps'],
                    source_end_seconds=end / e['fps'], full_episode_metrics=metric, **info)
        items.append(item)
        print(json.dumps(dict(exported=eid, recipe=model, frames=info['frames'])), flush=True)
    highlights = clips.montage([(out / i['file'], i['fps']) for i in items], out / 'more_examples.mp4')
    (out / 'clip_manifest.json').write_text(json.dumps(dict(examples=items, highlights=highlights), indent=2), encoding='utf-8')
    return items


def index(out, examples):
    cards = []
    for e in examples:
        cards.append(f'''<section id="{e['episode']}"><h2>{e['episode']} · {html.escape(e['title'])}</h2>
<p><strong>{html.escape(e['model_name'])}</strong> · {html.escape(e['task'])}</p>
<video controls playsinline preload="metadata" src="{e['file']}" poster="{e['poster']}"></video>
<p>{html.escape(e['note'])}</p><p>Source {e['source_start_seconds']:.2f}–{e['source_end_seconds']:.2f} s · full-episode failure F1 {e['full_episode_metrics']['failure_f1']:.1%}</p>
<nav><a href="{e['file']}" download>Download clip</a><a href="review.html?episode={e['episode']}">Compare every model on the full episode</a></nav></section>''')
    template = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>More Qwen results</title>
<style>body{background:#101722;color:#eff4fb;font:17px/1.5 system-ui;max-width:1300px;margin:auto;padding:26px 20px}h1{font-size:33px}h2{font-size:23px}a{color:#c5b7ff}nav{display:flex;gap:24px;flex-wrap:wrap}section{padding:22px;margin:24px 0;border:1px solid #3f536e;border-radius:12px;background:#192332}video{width:100%;display:block;background:#05080c}strong{color:#e1d8ff}</style>
<h1>More Qwen results</h1><p><strong>All 50 development episodes, five completed Qwen variants, and Sol.</strong> Review whole episodes or play nine additional exported examples below.</p>
<p>The explanation-auxiliary model is best in aggregate; a different model can be stronger on an individual episode. Each clip names the model actually shown. Examples include grasp failures, placement errors, collisions, missed failures and disagreements. Sol is a teacher reference, not verified human ground truth.</p>
<nav><a href="review.html">Open the full 50-episode comparison</a><a href="more_examples.mp4" download>Download nine examples as one MP4</a><a href="report.md">Metrics and scope</a></nav>'''
    (out / 'index.html').write_text(template + ''.join(cards) + '</html>', encoding='utf-8')


def main():
    if OUT.exists():
        raise ValueError('Choose a new version; do not overwrite an existing review')
    OUT.mkdir()
    source, episodes, scores, cache = build_review(OUT)
    print(json.dumps(dict(review_ready=True, episodes=50, tracks=300)), flush=True)
    examples = build_clips(OUT, source, episodes, scores, cache)
    index(OUT, examples)
    print(json.dumps(dict(complete=True, output=str(OUT), clips=len(examples))), flush=True)


if __name__ == '__main__':
    main()
