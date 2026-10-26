"""Render preserved native FLORA outputs as derived Markdown, without inference."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from check_flora_results import check, check_rubric, rubric_samples_from_manifest


def rows(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def cell(value):
    return str(value).replace('|', '\\|').replace('\n', ' ')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dense', type=Path, required=True)
    parser.add_argument('--dense-jobs', type=Path, required=True)
    parser.add_argument('--rubric', type=Path)
    parser.add_argument('--rubric-jobs', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if bool(args.rubric) != bool(args.rubric_jobs):
        parser.error('--rubric and --rubric-jobs must be supplied together')
    if args.out.exists():
        parser.error('Choose a new --out; preserved reports are not overwritten')
    report = check(args.dense, args.dense_jobs)
    if not report['structurally_valid']:
        raise ValueError(report['issues'])
    rubric = {}
    if args.rubric:
        report = check_rubric(args.rubric, args.rubric_jobs, rubric_samples_from_manifest(args.rubric))
        if not report['structurally_valid']:
            raise ValueError(report['issues'])
        rubric = {row['id']: row for row in rows(args.rubric)}
    dense = rows(args.dense)
    lines = [
        '# Preserved FLORA predictions: derived Markdown', '',
        'This is a readable conversion of historical native JSON generations, not a new',
        'Markdown model response or a human annotation. Native scores, segment boundaries,',
        'rationales and selected rubric reasoning are preserved. No smoothing is applied.',
        'These outputs passed structural checks; semantic correctness remains unverified.',
        'Consult the experiment report for camera and inference configuration limitations.', '',
        'Dense labels: 1 = failure, 2 = suboptimal, 3 = normal. Rubric totals are scores',
        'under the supplied rubric, not calibrated probabilities. Counts describe predictions.', '',
        '| Episode | Task | Frames / FPS | Native segments | Segments < 0.5 s | Failure frames | Suboptimal frames | Normal frames | Rubric total |',
        '| --- | --- | --- | --- | --- | --- | --- | --- | --- |',
    ]
    for row in dense:
        counts = Counter(row['frame_scores'])
        short = sum((s['end_frame'] - s['start_frame']) / row['fps'] < .5 for s in row['segments'])
        lines.append('| ' + ' | '.join(map(cell, [row['id'], row['task'],
            f"{row['num_frames']} / {row['fps']:g}", len(row['segments']), short,
            counts[1], counts[2], counts[3], rubric.get(row['id'], {}).get('total', 'not run')])) + ' |')
    lines += ['', 'Times below use the native stored seconds; frame intervals are [start, end).',
              'Duration counts use frame intervals / source FPS rather than rounded seconds.', '']
    for row in dense:
        lines += [f"## {row['id']}: {row['task']}", '',
                  '| Start (s) | End (s) | Frames [start, end) | Native label | Native rationale |',
                  '| --- | --- | --- | --- | --- |']
        for segment in row['segments']:
            values = [segment['start_s'], segment['end_s'],
                      f"[{segment['start_frame']}, {segment['end_frame']})",
                      segment['label'], segment['rationale'] or '(no native rationale)']
            lines.append('| ' + ' | '.join(map(cell, values)) + ' |')
        if row['id'] in rubric:
            result = rubric[row['id']]
            selected = result['samples'][result['medoid_sample']]
            lines += ['', '### Separate episode-level rubric output', '',
                      f"Selected scores: {result['scores']}; total: {result['total']}.", '',
                      'The following text is the selected native model reasoning. Its claims and',
                      'written timestamps are unverified; they are not extra dense annotations.', '',
                      selected['thinking'], '', selected['answer'], '']
        lines.append('')
    lines += ['## Source integrity', '', '| Input | SHA-256 |', '| --- | --- |']
    for name in ('dense', 'dense_jobs', 'rubric', 'rubric_jobs'):
        path = getattr(args, name)
        if path:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            lines.append(f'| {name}: {path.name} | `{digest}` |')
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write('\n'.join(lines) + '\n')
    print(f'Wrote derived Markdown: {args.out}')


if __name__ == '__main__':
    main()
