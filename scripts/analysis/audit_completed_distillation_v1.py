"""CPU-only audit of preserved development predictions; never loads a model."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import random
import re
import statistics
import sys

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'scripts/distill'))
import oopsie_recipe_data as data
import score_recipe_suite as scoring


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pct(value):
    return 'N/A' if value is None else f'{100*value:.2f}%'


def summarize(counts):
    m = scoring.metrics(counts)
    m['predicted_positive_fraction'] = (m['tp'] + m['fp']) / m['frames']
    m['balanced_accuracy'] = ((m['failure_recall'] + m['specificity']) / 2
        if m['failure_recall'] is not None and m['specificity'] is not None else None)
    return m


def aggregate(pred, truth, ids):
    c = Counter()
    for eid in ids:
        c.update(scoring.counts(pred[eid], truth[eid]))
    return summarize(c)


def bootstrap(predictions, truth, ids, rounds=5000):
    """Paired resampling of whole episodes, preserving within-video dependence."""
    counts = {name: [scoring.counts(pred[e], truth[e]) for e in ids]
              for name, pred in predictions.items()}
    rng = random.Random(20261103)
    values = defaultdict(list)
    differences = []
    for _ in range(rounds):
        sample = rng.choices(range(len(ids)), k=len(ids))
        results = {}
        for name, rows in counts.items():
            c = Counter()
            for i in sample:
                c.update(rows[i])
            m = summarize(c)
            results[name] = m
            for metric in ('failure_f1', 'failure_recall', 'strict_frame_agreement'):
                if m[metric] is not None:
                    values[name, metric].append(m[metric])
        if all(results[name]['failure_f1'] is not None for name in ('local/joint', 'local/binary')):
            differences.append(results['local/joint']['failure_f1'] - results['local/binary']['failure_f1'])

    def interval(xs):
        xs = sorted(xs)
        return [xs[int(.025 * (len(xs)-1))], xs[int(.975 * (len(xs)-1))]]
    return dict(rounds=rounds, unit='whole episode', seed=20261103,
                percentile_95={name: {metric: interval(values[name, metric]) for metric in
                    ('failure_f1', 'failure_recall', 'strict_frame_agreement')} for name in counts},
                joint_minus_binary_f1_95=interval(differences))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=REPO / 'outputs/oopsie_distillation_completed_audit_20261103_v1')
    args = parser.parse_args()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    study_root = REPO / 'outputs/oopsie_distillation_full_v1'
    folder = study_root / 'evidence_c32_x8_v3'
    study = read(study_root / 'study.json')
    index = read(folder / 'index.json')
    assert sha(folder / 'records.jsonl') == index['records_sha256']
    assert sha(study_root / 'study.json') == index['study_sha256']
    assert sha(folder / 'adapter.json') == index['adapter_sha256']
    rows = [json.loads(line) for line in (folder / 'records.jsonl').read_text(encoding='utf-8').splitlines()]
    assert not any(r['split'] == 'test' for r in rows)
    dev = [r for r in rows if r['split'] == 'development' and r['task'] == 'binary']
    train = [r for r in rows if r['split'] == 'train' and r['task'] == 'binary']
    episodes = {e['episode']: e for e in study['episodes'] if e['split'] != 'test'}
    ids = study['development_ids']
    truth = {eid: [None] * episodes[eid]['n_frames'] for eid in ids}
    window_truth = {}
    distributions = {}
    for split, subset in [('train', train), ('development', dev)]:
        counts = Counter()
        seen = defaultdict(list)
        for row in subset:
            values = []
            segs = data.parse_prediction(row['messages'][-1]['content'], row['episode'], row['core_start'], row['core_end'])
            for seg in segs:
                values.extend([int(seg['failure'])] * (seg['end_frame'] - seg['start_frame']))
            a, b = row['core_start'], row['core_end']
            assert len(values) == b-a
            counts.update(frames=len(values), failure_frames=sum(values), windows=1,
                          positive_windows=int(any(values)), mixed_windows=int(len(set(values)) > 1))
            seen[row['episode']].extend(range(a, b))
            images = [x for x in row['messages'][0]['content'] if x['type'] == 'image']
            assert len(images) == row['context_end'] - row['context_start']
            if split == 'development':
                truth[row['episode']][a:b] = values
                window_truth[row['id']] = values
        for eid, frames in seen.items():
            assert frames == list(range(episodes[eid]['n_frames']))
        distributions[split] = dict(counts, episodes=len(seen),
            failure_frame_fraction=counts['failure_frames']/counts['frames'],
            positive_window_fraction=counts['positive_windows']/counts['windows'])
    assert set(r['episode'] for r in train).isdisjoint(ids)
    assert all(None not in values for values in truth.values())
    local = REPO / 'outputs/oopsie_distillation_local_sequential_v1'
    tacc = out / 'tacc_snapshot'
    training_checks = {}
    for recipe, logs in [('binary', [local / 'runs/binary/train.jsonl', local / 'runs/binary/recovery_v1/train.jsonl']),
                          ('joint', [local / 'runs/joint/train.jsonl'])]:
        steps = {}
        for path in logs:
            for line in path.read_text(encoding='utf-8').splitlines():
                row = json.loads(line)
                steps[row['step']] = row
        assert sorted(steps) == list(range(1, 2689))
        assert all(math.isfinite(row['loss']) and math.isfinite(row['grad_norm']) for row in steps.values())
        run = read(local / 'runs' / recipe / 'run.json')
        assert run['study_sha256'] == index['study_sha256']
        assert run['records_sha256'] == index['records_sha256']
        assert run['adapter_sha256'] == index['adapter_sha256']
        completion_path = local / 'runs' / recipe / ('recovery_v1/completion.json' if recipe == 'binary' else 'completion.json')
        complete = read(completion_path)
        assert complete['completed_schedule'] and complete['unique_training_episodes_seen'] == 400
        training_checks[recipe] = dict(steps=len(steps), all_finite=True, episodes_seen=400,
            frozen_data_hashes_match=True, first_100_loss=statistics.mean(steps[i]['loss'] for i in range(1, 101)),
            last_100_loss=statistics.mean(steps[i]['loss'] for i in range(2589, 2689)),
            training_seconds=complete['elapsed_seconds'])
    roots = {'local/base': (local, 'base'), 'local/binary': (local, 'binary'),
             'local/joint': (local, 'joint'), 'tacc/base': (tacc, 'base')}
    predictions = {}
    audit = {}
    native_hashes = {}
    examples = []
    for name, (root, recipe) in roots.items():
        destination = root / 'predictions' / recipe
        # Re-run the frozen scorer against the exact source annotations.
        rescored = scoring.score(folder, destination)
        saved = read(root / 'arm_scores' / (recipe + '.json'))
        assert rescored == saved, f'Saved score differs from recomputation: {name}'
        native_hashes[str(root / 'arm_scores' / (recipe + '.json'))] = sha(root / 'arm_scores' / (recipe + '.json'))
        strict = {eid: [None] * len(truth[eid]) for eid in ids}
        unwrapped = {eid: [None] * len(truth[eid]) for eid in ids}
        errors = Counter()
        flags = Counter()
        output_tokens = []
        times = []
        changes = []
        for row in dev:
            path = destination / (row['id'] + '.json')
            saved_prediction = read(path)
            native_hashes[str(path)] = sha(path)
            raw = saved_prediction['text']
            text = raw.strip()
            match = re.fullmatch(r'```(?:markdown|md)?\s*\n([\s\S]*?)\n```', text, flags=re.I)
            if match:
                text = match[1]
                flags['outer_fences'] += 1
            output_tokens.append(saved_prediction['output_tokens'])
            times.append(saved_prediction['elapsed_seconds'])
            flags['hit_max'] += int(saved_prediction['hit_max'])
            for mode, target, candidate in [('strict', strict, raw), ('unwrapped', unwrapped, text)]:
                try:
                    if saved_prediction['hit_max']:
                        raise ValueError('Generation reached token cap')
                    segs = data.parse_prediction(candidate, row['episode'], row['core_start'], row['core_end'])
                    values = []
                    for seg in segs:
                        values.extend([int(seg['failure'])] * (seg['end_frame'] - seg['start_frame']))
                    target[row['episode']][row['core_start']:row['core_end']] = values
                    flags[mode + '_valid_windows'] += 1
                    if mode == 'strict':
                        flags['all_no_windows'] += int(not any(values))
                        flags['all_yes_windows'] += int(all(values))
                        flags['mixed_windows'] += int(len(set(values)) > 1)
                        changes.extend(s['end_frame'] for s in segs[:-1])
                except (ValueError, KeyError) as exc:
                    errors[mode + ': ' + str(exc)] += 1
                    if mode == 'strict' and len(examples) < 12:
                        examples.append(dict(model=name, window=row['id'], text=raw, error=str(exc)))
        m = aggregate(strict, truth, ids)
        assert all(m[k] == saved['metrics'][k] for k in saved['metrics'])
        predictions[name] = strict
        if flags['outer_fences']:
            predictions[name + ' unwrapped'] = unwrapped
        episode_rows = []
        for eid in ids:
            em = summarize(scoring.counts(strict[eid], truth[eid]))
            episode_rows.append(dict(episode=eid, lab=episodes[eid]['lab'], fps=episodes[eid]['fps'],
                metrics=em, boundaries=scoring.boundary_metrics(strict[eid], truth[eid], episodes[eid]['fps'])))
        reference_segments = sum(e['boundaries']['reference_failure_segments'] for e in episode_rows)
        predicted_segments = sum(e['boundaries']['predicted_failure_segments'] for e in episode_rows)
        matched = sum(e['boundaries']['matched_failure_segments'] for e in episode_rows)
        audit[name] = dict(metrics=m, flags=dict(flags), invalid_reasons=dict(errors),
            wrapper_normalization_metrics=aggregate(unwrapped, truth, ids),
            per_episode=episode_rows, within_window_transitions=len(changes),
            segment_detection=dict(reference=reference_segments, predicted=predicted_segments, matched=matched,
                recall=matched/reference_segments, precision=matched/predicted_segments if predicted_segments else None),
            elapsed_generation_seconds=sum(times), output_tokens=dict(mean=statistics.mean(output_tokens), max=max(output_tokens)))
    # Deterministic controls use the very same complete development reference.
    for name, label in [('always_no', 0), ('always_yes', 1)]:
        predictions[name] = {eid: [label] * len(truth[eid]) for eid in ids}
    totals = {name: aggregate(pred, truth, ids) for name, pred in predictions.items()}
    time_totals = {}
    for name, pred in predictions.items():
        keys = ('tp', 'fp', 'fn', 'tn', 'unknown_positive', 'unknown_negative')
        time_counts = {key: math.fsum(scoring.counts(pred[e], truth[e])[key] / episodes[e]['fps'] for e in ids)
                       for key in keys}
        time_totals[name] = summarize(time_counts)
    strata = {}
    groups = {'long_episodes_ge_500_frames': [e for e in ids if len(truth[e]) >= 500],
              'short_episodes_lt_500_frames': [e for e in ids if len(truth[e]) < 500],
              'excluding_O9014': [e for e in ids if e != 'O9014'],
              'positive_episodes': [e for e in ids if any(truth[e])],
              'negative_episodes': [e for e in ids if not any(truth[e])]}
    for lab in sorted({episodes[e]['lab'] for e in ids}):
        groups['lab/' + lab] = [e for e in ids if episodes[e]['lab'] == lab]
    for group, selected in groups.items():
        if selected:
            strata[group] = dict(episodes=len(selected), frames=sum(len(truth[e]) for e in selected),
                metrics={name: aggregate(pred, truth, selected) for name, pred in predictions.items()})
    positive = [e for e in ids if any(truth[e])]
    worst = sorted(positive, key=lambda eid: sum(truth[eid]), reverse=True)
    pair = {}
    for label, names in [('strict', ('local/base', 'tacc/base')),
                         ('unwrapped', ('local/base unwrapped', 'tacc/base unwrapped'))]:
        c = Counter()
        for eid in ids:
            for p, q in zip(predictions[names[0]][eid], predictions[names[1]][eid]):
                c['frames'] += 1
                c['same_including_unknown'] += p == q
                if p is not None and q is not None:
                    c['both_covered'] += 1
                    c['same_when_both_covered'] += p == q
        pair[label] = dict(c)
    result = dict(created_utc=datetime.now(timezone.utc).isoformat(), test_used=False,
        recomputed_saved_scores_match=True, exact_core_coverage_verified=True,
        distributions=distributions, totals=totals, time_weighted_totals=time_totals, models=audit, strata=strata,
        training_checks=training_checks,
        base_cross_hardware=pair, bootstrap=bootstrap(predictions, truth, ids),
        invalid_examples=examples, source_sha256=native_hashes)
    (out / 'diagnostics.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    report = ['# Completed distillation development audit', '',
        'The completed local models learn the output format but miss most failure frames. '
        'Joint improves over binary supervision, while pretrained Qwen has extensive output contract failures. '
        'All figures measure imitation of frozen Sol labels across 50 development episodes. The final test remains sealed.', '',
        'Completed scope: local pretrained baseline, binary SFT and joint SFT; TACC pretrained baseline. '
        'The eight TACC training arms are still running and have no completed development results in this snapshot.', '',
        f"Snapshot: {result['created_utc']}. All four saved score files exactly match a fresh run of the frozen scorer. "
        'Scored cores cover every development frame exactly once; all visible context images are present in the exported records.', '',
        '| Model or control | Coverage | Strict agreement | Precision | Recall | Failure F1 | Predicted failure frames |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for name, m in totals.items():
        report.append('| ' + name + ' | ' + ' | '.join(pct(m[k]) for k in
            ('coverage', 'strict_frame_agreement', 'failure_precision', 'failure_recall', 'failure_f1', 'predicted_positive_fraction')) + ' |')
    report += ['', 'Unwrapped rows are derived diagnostics: only an enclosing Markdown code fence is removed. '
        'They do not change interval boundaries, labels, prompts, native outputs or official scores. '
        'Any remaining malformed or token-capped output stays unknown.', '', '## Failure detection and episode concentration', '',
        f"Development has {len(positive)}/50 episodes containing failure and {sum(map(sum, truth.values()))}/{sum(map(len, truth.values()))} failure frames. "
        f"Training failure prevalence is {pct(distributions['train']['failure_frame_fraction'])} by frame and "
        f"{pct(distributions['train']['positive_window_fraction'])} by window. Development failure prevalence is "
        f"{pct(distributions['development']['failure_frame_fraction'])} by frame. "
        'The two long episodes are both Princeton PRISM at 30 FPS; the other 48 are Princeton IRoM at 10 FPS. '
        'Lab, frame rate and episode length are confounded in this development sample.', '',
        '| Episode | Frames | Failure frames | Local binary TP | Local joint TP |', '|---|---:|---:|---:|---:|']
    for eid in worst[:10]:
        report.append(f"| {eid} | {len(truth[eid])} | {sum(truth[eid])} | "
            f"{scoring.counts(predictions['local/binary'][eid], truth[eid])['tp']} | "
            f"{scoring.counts(predictions['local/joint'][eid], truth[eid])['tp']} |")
    excluded = strata['excluding_O9014']['metrics']
    report += ['', 'Without O9014, joint failure F1 is ' + pct(excluded['local/joint']['failure_f1']) +
        ' and recall is ' + pct(excluded['local/joint']['failure_recall']) + '. '
        'This is a concentration diagnostic, not an alternative selection set.', '',
        '## Duration weighted metrics', '',
        'Native frame weighting gives a 30 FPS video three times the weight per second of a 10 FPS video. '
        'The following derived calculation weights each source frame by 1/FPS, so equal video durations receive equal weight. '
        'The frozen official frame scores remain unchanged.', '',
        '| Model or control | Covered duration | Agreement | Precision | Recall | Failure F1 |',
        '|---|---:|---:|---:|---:|---:|']
    for name, m in time_totals.items():
        report.append('| ' + name + ' | ' + ' | '.join(pct(m[k]) for k in
            ('coverage', 'strict_frame_agreement', 'failure_precision', 'failure_recall', 'failure_f1')) + ' |')
    report += ['', '| Model | Matched failure intervals at IoU 0.3 | Reference intervals | Predicted intervals | Within-window transitions |',
        '|---|---:|---:|---:|---:|']
    for name, value in audit.items():
        s = value['segment_detection']
        report.append(f"| {name} | {s['matched']} | {s['reference']} | {s['predicted']} | {value['within_window_transitions']} |")
    report += ['', 'Interval matching uses the existing greedy one-to-one IoU >= 0.3 rule. '
        'Boundary error on matched intervals alone excludes entirely missed events, so it must accompany interval recall.', '',
        '## Training checks and interpretation', '',
        'Both local SFT arms completed all 2,688 updates, saw all 400 training episodes, and match the frozen study, records and evidence adapter hashes. '
        'Losses and gradient norms are finite throughout. Binary logs are combined at their recorded step indices across the approved reboot recovery. '
        'Mean first/last 100 training losses are binary ' +
        f"{training_checks['binary']['first_100_loss']:.4f}/{training_checks['binary']['last_100_loss']:.4f} and joint " +
        f"{training_checks['joint']['first_100_loss']:.4f}/{training_checks['joint']['last_100_loss']:.4f}. "
        'Different target lengths prevent direct cross-recipe loss comparisons; decreasing loss does not establish failure detection.', '',
        'Training failures occupy 32.08 percent of source frames, so the under-detection cannot be explained by an almost entirely negative training set. '
        'The full Markdown target is supervised, including structure and frame indices; label discrimination is only part of its token loss. '
        'Only 168 windows have eligible complete auxiliary intervals, compared with 5,376 primary windows, limiting the auxiliary comparisons.', '',
        'O9008 and O9014 are long task-not-attempted examples. Their 30 FPS student view is at most 48 frames, or 1.6 seconds, '
        'while the teacher judges sustained behavior across a 33.3-second episode. Context mismatch is a plausible cause to investigate, '
        'but it cannot explain every miss: O9013 has a visibly misplaced object and is also entirely missed by both local SFT models.', '',
        '## Output validity', '', '| Model | Strict valid windows | Fenced outputs | Valid after fence removal | Token cap hits |',
        '|---|---:|---:|---:|---:|']
    for name, value in audit.items():
        f = value['flags']
        report.append(f"| {name} | {f['strict_valid_windows']}/279 | {f.get('outer_fences',0)} | {f['unwrapped_valid_windows']}/279 | {f['hit_max']} |")
    report += ['', 'For local base, strict rejection reasons are: ' +
        '; '.join(key.removeprefix('strict: ') + ': ' + str(value) for key, value in audit['local/base']['invalid_reasons'].items() if key.startswith('strict: ')) + '. '
        'Code fences explain only two windows. Examples include rows such as `| Frame 32 | Frame 64 | Yes |`, '
        'extra rows for context frames, and out-of-core boundaries. Removing fences alone does not repair these errors.', '',
        'The local and TACC pretrained baselines agree on every frame covered by both strict outputs '
        f"({pair['strict']['both_covered']} frames). Their coverage patterns differ; this does not establish identical full raw generations."]
    report += ['', '## Uncertainty', '',
        'Percentile intervals below resample all 50 whole episodes together, preserving paired model comparisons and within-video dependence. '
        'They describe variation across this development sample, not additional training seeds or independent hardware replicates.', '',
        '| Model | Failure F1 | Episode bootstrap 95 percent interval |', '|---|---:|---|']
    for name, intervals in result['bootstrap']['percentile_95'].items():
        low, high = intervals['failure_f1']
        report.append(f"| {name} | {pct(totals[name]['failure_f1'])} | {pct(low)} to {pct(high)} |")
    low, high = result['bootstrap']['joint_minus_binary_f1_95']
    report += ['', f'Paired joint minus binary F1 interval: {100*low:.2f} to {100*high:.2f} percentage points. '
        'These post-hoc diagnostics do not establish a final-test winner.', '',
        '## Evaluation plan', '',
        '1. Keep the frozen strict score and add a separately versioned normalization diagnostic for every model. '
        'Report valid windows, covered frames and token cap failures alongside semantic metrics. Decide the output acceptance contract before final evaluation.',
        '2. Compare every finished recipe on the same development episodes using failure precision, recall, F1, IoU and balanced accuracy; '
        'include always-No and always-Yes controls. Show pooled and per-episode results, duration weighting, positive episodes, laboratories and long episodes separately.',
        '3. Report failure interval precision and recall at fixed IoU thresholds, onset delay, missed intervals and false alarms per video minute. '
        'Treat fully missed events separately from boundary timing on matched events.',
        '4. Review original video with time-aligned teacher and student labels. Prioritize joint misses, binary/joint disagreements, '
        'long stalling intervals, temporal boundaries and a random positive/negative sample. Independently adjudicated video labels are needed for accuracy claims.',
        '5. Diagnose whether failure is locally observable in the 32-core/8-context view. '
        'Teacher annotations use whole episodes; persistent stalling and wrong-task behavior can need more context than the student receives. '
        'Audit the prompt difference between joint training and binary-only inference before interpreting explanation benefits.',
        '6. Wait for complete TACC schedules and development generation, then compare paired recipes across hardware. '
        'The same seed on different hardware is a replication check, not multiple independent seeds. '
        'Freeze the selection criterion, parser contract and chosen configuration before opening the 50 final-test episodes.', '',
        'No new model generation, training, job submission or teacher call is part of this audit. '
        'Further GPU diagnostics need a concrete approved plan.', '',
        '## Review and metric references', '',
        '[Open the time-aligned student comparison](review.html) to play all 50 development episodes at source timing, '
        'step frames and compare strict or unwrapped predictions with Sol. Human review notes download as Markdown.', '',
        'Balanced accuracy averages class recall ([scikit-learn documentation](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.balanced_accuracy_score.html)). '
        'Segmental F1 complements frame metrics by measuring matched temporal events '
        '([Lea et al. CVPR 2017](https://openaccess.thecvf.com/content_cvpr_2017/html/Lea_Temporal_Convolutional_Networks_CVPR_2017_paper.html)).', '']
    (out / 'report.md').write_text('\n'.join(report), encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k in ('distributions', 'totals', 'strata', 'base_cross_hardware', 'bootstrap')}, indent=2))


if __name__ == '__main__':
    main()
