"""Derived Markdown and agreement metrics; native FLORA output is never rewritten."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

from check_flora_results import check


def metrics(c):
    tp, fp, fn, tn = (c[k] for k in ('tp', 'fp', 'fn', 'tn'))
    def div(a, b):
        return a / b if b else None
    return dict(c, frames=tp + fp + fn + tn,
                frame_agreement=div(tp + tn, tp + fp + fn + tn),
                failure_precision=div(tp, tp + fp), failure_recall=div(tp, tp + fn),
                failure_f1=div(2 * tp, 2 * tp + fp + fn), failure_iou=div(tp, tp + fp + fn),
                nonfailure_recall=div(tn, tn + fp))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--inputs', type=Path, required=True)
    p.add_argument('--run', type=Path, required=True)
    a = p.parse_args()
    source = a.run / 'dense.jsonl'
    assert check(source, a.inputs / 'dense_jobs.jsonl')['structurally_valid']
    rows = [json.loads(line) for line in source.read_text().splitlines()]
    inputs = json.loads((a.inputs / 'inputs.json').read_text())
    references = json.loads((a.inputs / 'evaluation/reference.json').read_text())
    jobs = [json.loads(s) for s in (a.inputs / 'dense_jobs.jsonl').read_text().splitlines()]
    assert [r['id'] for r in rows] == inputs['development_ids']
    sys.path.insert(0, str(a.root / 'rewarder'))
    from batch_utils import core, dense_reward
    totals = {name: Counter(tp=0, fp=0, fn=0, tn=0) for name in ['failure_only', 'non_normal']}
    reports = []
    native = Counter()
    lines = ['# FLORA: 50 development episodes', '',
             'Derived report from preserved native outputs. Reference: frozen Sol annotations '
             '(`gpt-6.1-sol`); agreement with this teacher is not human-reference accuracy. '
             'No teacher labels were supplied to FLORA. Final test remains sealed.', '',
             'Both binary mappings were declared before submission. Failure-only maps native 1 '
             'to failure; non-normal maps native 1 or 2 to failure. All raw three-class scores '
             'and rationales are retained without smoothing.', '']
    annotation_lines = ['# FLORA native segments: readable derived conversion', '',
                        'Labels and rationales come from unchanged native three-class output. '
                        'Frame intervals have exclusive ends. Model rationales are unverified.', '']
    for row, job, expected in zip(rows, jobs, inputs['episodes'], strict=True):
        assert row['num_frames'] == expected['n_frames']
        assert abs(row['fps'] - expected['fps']) < 1e-6
        collage = core.Collage([(a.inputs / v).resolve() for v in job['videos']])
        windows = core.dense_windows(collage.num_frames, collage.fps)
        texts = [clip['output'] for clip in row['clips']]
        answers = [core.parse_dense(text) for text in texts]
        reconstructed = dense_reward.summarize(job, collage, windows, answers, texts,
                                               core.DENSE_TAIL_TRIM_S, True)
        assert reconstructed == row, row['id']
        scores, clip_of_frame, _ = core.stitch_dense(windows, answers, collage.num_frames,
                                                   core.DENSE_TAIL_TRIM_S)
        ref = references['episodes'][row['id']]['frame_labels']
        assert len(ref) == len(scores)
        per_mapping = {}
        for name, failure_values in [('failure_only', {1}), ('non_normal', {1, 2})]:
            c = Counter(tp=0, fp=0, fn=0, tn=0)
            for score, label in zip(scores, ref, strict=True):
                failure = int(score) in failure_values
                c['tp' if failure and label else 'fp' if failure else 'fn' if label else 'tn'] += 1
            totals[name].update(c)
            per_mapping[name] = metrics(c)
        switches = sum(int(x != y) for x, y in zip(clip_of_frame[:-1], clip_of_frame[1:]))
        score_changes = sum(int(x != y) for x, y in zip(scores[:-1], scores[1:]))
        simultaneous = sum(int(c != d and x != y) for c, d, x, y in
                           zip(clip_of_frame[:-1], clip_of_frame[1:], scores[:-1], scores[1:]))
        diagnostics = dict(source_clip_switches=switches, native_score_changes=score_changes,
                           score_changes_at_source_switch=simultaneous,
                           segments_shorter_than_half_second=sum(
                               (s['end_frame'] - s['start_frame']) / row['fps'] < 0.5
                               for s in row['segments']))
        native.update(int(s) for s in scores)
        reports.append(dict(id=row['id'], metrics=per_mapping, stitching=diagnostics))
        annotation_lines += [f"## {row['id']}: {row['task']}", '',
                             '| Start (s) | End (s) | Frames | Native label | Model rationale |',
                             '|---:|---:|---|---|---|']
        for s in row['segments']:
            rationale = str(s.get('rationale', '')).replace('|', '\\|').replace('\n', ' ')
            annotation_lines.append(f"| {s['start_s']:.3f} | {s['end_s']:.3f} | "
                                    f"[{s['start_frame']}, {s['end_frame']}) | {s['label']} "
                                    f"({s['score']}) | {rationale} |")
        annotation_lines += ['']
    overall = {name: metrics(c) for name, c in totals.items()}
    def pct(value):
        return 'N/A' if value is None else f'{100 * value:.2f}%'
    lines += ['| Binary mapping | Agreement | Failure precision | Failure recall | Failure F1 | Failure IoU | Non-failure recall |',
              '|---|---:|---:|---:|---:|---:|---:|']
    for name, m in overall.items():
        lines.append('| ' + name + ' | ' + ' | '.join(pct(m[key]) for key in
                     ['frame_agreement', 'failure_precision', 'failure_recall', 'failure_f1',
                      'failure_iou', 'nonfailure_recall']) + ' |')
    lines += ['', f'Native frame totals: failure {native[1]}, suboptimal {native[2]}, normal {native[3]}.', '',
              '| Episode | Failure-only F1 | Non-normal F1 | Source clip switches | Score changes at source switches | Segments <0.5 s |',
              '|---|---:|---:|---:|---:|---:|']
    for r in reports:
        d = r['stitching']
        lines.append(f"| {r['id']} | {pct(r['metrics']['failure_only']['failure_f1'])} | "
                     f"{pct(r['metrics']['non_normal']['failure_f1'])} | {d['source_clip_switches']} | "
                     f"{d['score_changes_at_source_switch']} | {d['segments_shorter_than_half_second']} |")
    lines += ['', 'A source switch does not itself imply a labeling error. These counts describe '
              'the native stitching behavior; visual review is needed to judge the transitions.', '']
    result = dict(episodes=len(rows), metrics=overall, native_frame_counts=dict(native),
                  per_episode=reports, native_postprocessing_reproduced=True,
                  reference='Frozen Sol; teacher agreement, not human accuracy',
                  native_outputs_modified=False, smoothing_applied=False)
    for name, text in [('results.md', '\n'.join(lines)),
                       ('annotations_derived.md', '\n'.join(annotation_lines)),
                       ('metrics.json', json.dumps(result, indent=2) + '\n')]:
        with (a.run / name).open('x', encoding='utf-8') as stream:
            stream.write(text)
    print(f'Completed and scored {len(rows)} episodes; native outputs preserved', flush=True)


if __name__ == '__main__':
    main()
