"""Pairwise frame, duration, episode, event and boundary agreement from frozen labels."""
import argparse
from collections import Counter
import csv
import hashlib
import html
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import linear_sum_assignment

DISPLAY = {'Astra': 'Astra', 'Qwen': 'Joint Qwen', 'Flora': 'FLORA: failure only',
           'FloraNonNormal': 'FLORA: failure + suboptimal'}
PAIRS = [('Astra', 'Qwen'), ('Astra', 'Flora'), ('Qwen', 'Flora'),
         ('Astra', 'FloraNonNormal'), ('Qwen', 'FloraNonNormal')]
WEIGHTS = ['frames', 'seconds', 'equal_episode']


def divide(a, b):
    return float(a / b) if b else None


def clean(value):
    if isinstance(value, dict):
        return {k: clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(v) for v in value]
    if isinstance(value, np.generic):
        return clean(value.item())
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def metrics(c):
    # A is the left/reference convention, B is the right/comparison convention.
    both, b_only, a_only, neither = map(float, c)
    n = both + b_only + a_only + neither
    p_a, p_b = (both + a_only) / n, (both + b_only) / n
    observed = (both + neither) / n
    chance = p_a * p_b + (1 - p_a) * (1 - p_b)
    f1 = divide(2 * both, 2 * both + a_only + b_only)
    nf1 = divide(2 * neither, 2 * neither + a_only + b_only)
    recall, nonrecall = divide(both, both + a_only), divide(neither, neither + b_only)
    fiou = divide(both, both + a_only + b_only)
    niou = divide(neither, neither + a_only + b_only)
    return dict(both_failure=both, b_only_failure=b_only, a_only_failure=a_only, both_nonfailure=neither,
                total_weight=n, agreement=observed, disagreement=1 - observed,
                failure_f1=f1, failure_iou=fiou, nonfailure_f1=nf1, nonfailure_iou=niou,
                macro_class_f1=(f1 + nf1) / 2 if f1 is not None and nf1 is not None else None,
                mean_iou=(fiou + niou) / 2 if fiou is not None and niou is not None else None,
                cohen_kappa=divide(observed - chance, 1 - chance),
                mcc=divide(both * neither - a_only * b_only,
                           np.sqrt((both + b_only) * (both + a_only) * (neither + b_only) * (neither + a_only))),
                b_failure_precision_vs_a=divide(both, both + b_only), b_failure_recall_vs_a=recall,
                b_nonfailure_recall_vs_a=nonrecall,
                b_balanced_accuracy_vs_a=(recall + nonrecall) / 2 if recall is not None and nonrecall is not None else None)


def confusion(a, b):
    return np.array([np.sum(a & b), np.sum(~a & b), np.sum(a & ~b), np.sum(~a & ~b)], dtype=float)


def segments(values):
    padded = np.r_[False, values, False].astype(int)
    return list(zip(np.flatnonzero(np.diff(padded) == 1), np.flatnonzero(np.diff(padded) == -1)))


def optimal_matches(quality, threshold):
    if quality.size == 0:
        return []
    valid = quality >= threshold
    # A match-count advantage dominates every possible total IoU tie-break.
    utility = np.where(valid, min(quality.shape) + 1 + quality, 0)
    aa, bb = linear_sum_assignment(-utility)
    return [(int(a), int(b)) for a, b in zip(aa, bb) if valid[a, b]]


def event_metrics(episodes, left, right, threshold):
    n_a = n_b = matched = 0
    errors, onset, offset, cover_a, cover_b = [], [], [], [], []
    for e in episodes:
        a, b = segments(e['tracks'][left]), segments(e['tracks'][right])
        n_a += len(a)
        n_b += len(b)
        iou = np.zeros((len(a), len(b)))
        for i, (s, t) in enumerate(a):
            for j, (u, v) in enumerate(b):
                iou[i, j] = max(0, min(t, v) - max(s, u)) / (max(t, v) - min(s, u))
        for i, (s, t) in enumerate(a):
            cover_a.append(((t - s) / e['fps'], float(iou[i].max()) if b else 0.))
        for j, (s, t) in enumerate(b):
            cover_b.append(((t - s) / e['fps'], float(iou[:, j].max()) if a else 0.))
        pairs = optimal_matches(iou, threshold)
        matched += len(pairs)
        for i, j in pairs:
            start_error, end_error = (b[j][0] - a[i][0]) / e['fps'], (b[j][1] - a[i][1]) / e['fps']
            onset.append(start_error)
            offset.append(end_error)
            errors.extend([abs(start_error), abs(end_error)])
    def cover(rows, duration):
        return divide(sum((s if duration else 1) * v for s, v in rows), sum(s if duration else 1 for s, v in rows))
    return dict(a_failure_segments=n_a, b_failure_segments=n_b, matched_segments=matched,
                segment_precision_b_vs_a=divide(matched, n_b), segment_recall_b_vs_a=divide(matched, n_a),
                segment_f1=divide(2 * matched, n_a + n_b),
                matched_boundary_mae_seconds=float(np.mean(errors)) if errors else None,
                matched_boundary_median_abs_seconds=float(np.median(errors)) if errors else None,
                matched_onset_signed_mean_seconds=float(np.mean(onset)) if onset else None,
                matched_offset_signed_mean_seconds=float(np.mean(offset)) if offset else None,
                a_mean_best_segment_iou=cover(cover_a, False), b_mean_best_segment_iou=cover(cover_b, False),
                a_duration_weighted_best_iou=cover(cover_a, True), b_duration_weighted_best_iou=cover(cover_b, True))


def boundary_metrics(episodes, left, right, tolerance, direction):
    n_a = n_b = matched = 0
    for e in episodes:
        a = (np.flatnonzero(np.diff(e['tracks'][left].astype(int)) == direction) + 1) / e['fps']
        b = (np.flatnonzero(np.diff(e['tracks'][right].astype(int)) == direction) + 1) / e['fps']
        n_a += len(a)
        n_b += len(b)
        distance = np.abs(a[:, None] - b[None, :])
        # quality >= 0 selects only eligible boundaries; negative distances break ties.
        utility = np.where(distance <= tolerance + 1e-9, 1 - distance / (tolerance + 1e-9), -1.)
        matched += len(optimal_matches(utility, 0))
    return dict(a_boundaries=n_a, b_boundaries=n_b, matched_boundaries=matched,
                precision_b_vs_a=divide(matched, n_b), recall_b_vs_a=divide(matched, n_a),
                boundary_f1=divide(2 * matched, n_a + n_b))


def csv_write(path, rows):
    keys = list(dict.fromkeys(k for row in rows for k in row))
    with path.open('x', newline='', encoding='utf-8-sig') as stream:
        writer = csv.DictWriter(stream, fieldnames=keys)
        writer.writeheader()
        writer.writerows(clean(rows))


def pct(value):
    return 'N/A' if value is None else f'{100 * value:.2f}%'


def num(value):
    return 'N/A' if value is None else f'{value:.3f}'


def md_table(headers, rows):
    return ['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join(['---'] * len(headers)) + ' |'] + [
        '| ' + ' | '.join(map(str, row)) + ' |' for row in rows]


def build_report(out, episodes, pairwise, per_episode, summaries, events, boundaries, patterns, triples, boot):
    lines = ['# Astra, joint Qwen and FLORA: quantitative agreement', '',
             'Same frozen 50 development episodes, 8,132 native source frames, 679.867 seconds. '
             'No model calls, retraining, smoothing or final-test access. “Astra” is the user-requested display alias '
             'for preserved **Sol (`gpt-6.1-sol`)** annotations. Qwen means the **joint-trained Qwen2.5-VL-7B** run; '
             'FLORA means the native outputs from TACC job 3572125.', '',
             '**These quantify agreement between labelers, not accuracy against human ground truth.** '
             'Qwen was trained with the same teacher family, so these are not three independent human raters.', '',
             'FLORA failure-only maps **1 → failure; 2/3 → non-failure**. FLORA failure + suboptimal maps '
             '**1/2 → failure; 3 → non-failure**. Both mappings are shown; native three-class outputs are preserved.', '',
             '## 1. How much does each pair agree?', '',
             'Source-frame weighting, matching earlier reports. Agreement, F1, IoU, κ and MCC below are symmetric. '
             'Failure F1 is the Dice overlap of the two failure masks. No reference is needed for these columns.', '']
    full = [r for r in pairwise if r['group'] == 'all' and r['weighting'] == 'frames']
    lines += md_table(['Pair', 'Agreement', 'Failure F1', 'Failure IoU', 'Non-failure F1', 'Class-macro F1', 'Cohen κ', 'MCC'], [
        [r['pair'], pct(r['agreement']), pct(r['failure_f1']), pct(r['failure_iou']), pct(r['nonfailure_f1']),
         pct(r['macro_class_f1']), num(r['cohen_kappa']), num(r['mcc'])] for r in full])
    lines += ['', '![Pairwise agreement and overlap](pairwise_overview.png)', '',
              'κ corrects agreement for the two observed failure rates. MCC measures binary association and includes all four '
              'confusion cells. Both are 1 for perfect agreement, around 0 for no association under their respective definitions, '
              'and can be negative. Neither establishes correctness.', '',
              '## 2. Precision and recall, choosing a reference convention', '',
              'A is the left labeler named in each pair; B is the right. Precision = fraction of B’s failure frames also '
              'called failure by A. Recall = fraction of A’s failure frames also called failure by B. '
              'Swapping A and B swaps failure precision and recall; F1 and IoU stay unchanged.', '']
    lines += md_table(['A → B', 'B failure precision', 'B failure recall', 'B non-failure recall', 'B balanced accuracy'], [
        [r['pair'], pct(r['b_failure_precision_vs_a']), pct(r['b_failure_recall_vs_a']),
         pct(r['b_nonfailure_recall_vs_a']), pct(r['b_balanced_accuracy_vs_a'])] for r in full])
    lines += ['', '## 3. Weighting changes the question', '',
              '- **Frames:** each recorded frame counts equally. Higher-FPS and longer episodes receive more weight.',
              '- **Seconds:** each frame has weight 1/FPS; each second of video counts equally.',
              '- **Equal episode, pooled:** each frame has weight 1/episode-frame-count. Each episode contributes total weight 1, '
              'then metrics are calculated from the pooled weighted confusion matrix.',
              '- **Mean episode F1:** separately calculate F1 in each episode, then average the defined values. Episodes where '
              'both labelers predict no failure have undefined failure F1 and are omitted, with the denominator shown. '
              'This differs from equal-episode pooled F1.', '']
    lines += md_table(['Pair', 'Frame agreement', 'Seconds agreement', 'Equal-episode agreement',
                       'Frame failure F1', 'Seconds failure F1', 'Equal-episode pooled F1', 'Mean episode F1 (N)'], [
        [row['pair']] + [pct(next(r for r in pairwise if r['pair'] == row['pair'] and r['group'] == 'all' and r['weighting'] == w)['agreement']) for w in WEIGHTS] +
        [pct(next(r for r in pairwise if r['pair'] == row['pair'] and r['group'] == 'all' and r['weighting'] == w)['failure_f1']) for w in WEIGHTS] +
        [pct(float(np.mean(vals))) + f' ({len(vals)}/50)' if vals else 'N/A (0/50)']
        for row in full for vals in [[r['failure_f1'] for r in per_episode if r['pair'] == row['pair'] and r['failure_f1'] is not None]]])
    lines += ['', '### Lab and duration breakdown', '']
    lines += md_table(['Lab', 'Episodes', 'Frames', 'Frame share', 'Seconds', 'Time share'], [
        [lab, len(es), sum(e['n_frames'] for e in es), pct(sum(e['n_frames'] for e in es)/8132),
         f"{sum(e['n_frames']/e['fps'] for e in es):.3f}", pct(sum(e['n_frames']/e['fps'] for e in es)/sum(e['n_frames']/e['fps'] for e in episodes))]
        for lab in sorted({e['lab'] for e in episodes}) for es in [[e for e in episodes if e['lab'] == lab]]])
    lines += ['', 'The two PRISM episodes contribute 24.6% of frames but only 9.8% of elapsed video time. '
              'Averaging by frame therefore gives this pair of episodes appreciable influence.', '']
    lines += md_table(['Lab', 'Pair', 'Agreement', 'Failure F1', 'Failure IoU'], [
        [r['group'], r['pair'], pct(r['agreement']), pct(r['failure_f1']), pct(r['failure_iou'])]
        for r in pairwise if r['group'] != 'all' and r['weighting'] == 'frames'])
    lines += ['', '![Weighting and fragmentation](weighting_and_fragmentation.png)', '',
              '## 4. Failure rates, episode presence and fragmentation', '']
    lines += md_table(['Labeler / mapping', 'Failure frames', 'Failure frame %', 'Failure time %', 'Mean episode failure %',
                       'Episodes with failure', 'Failure runs', 'Median run (s)', 'Runs <0.5 s', 'Label switches/min'], [
        [r['labeler'], r['failure_frames'], pct(r['failure_frame_fraction']), pct(r['failure_time_fraction']),
         pct(r['mean_episode_failure_fraction']), r['episodes_with_failure'], r['failure_runs'], num(r['median_failure_run_seconds']),
         f"{r['short_failure_runs']} ({pct(r['short_failure_run_fraction'])})", num(r['switches_per_minute'])] for r in summaries])
    lines += ['', 'A failure run is one contiguous binary failure interval after the declared FLORA mapping; adjacent failure '
              'and suboptimal spans merge only in the failure+suboptimal mapping. No filtering or smoothing is applied. '
              'Transitions per minute use all binary label changes divided by total native duration. '
              'Fragmentation describes temporal behavior, not semantic correctness.', '',
              '## 5. Do they identify the same failure events?', '',
              'One-to-one matches between contiguous failure intervals. A pair qualifies when temporal IoU ≥ the threshold. '
              'Matching maximizes the number of matches, then total IoU. Counts are pooled across episodes; intervals never '
              'match across episodes. Event precision = matches / B runs; recall = matches / A runs. '
              'Event F1 penalizes splitting one event into many predicted runs.', '']
    lines += md_table(['Pair', 'IoU threshold', 'A runs', 'B runs', 'Matches', 'Event precision', 'Event recall', 'Event F1', 'Matched boundary MAE (s)'], [
        [r['pair'], r['iou_threshold'], r['a_failure_segments'], r['b_failure_segments'], r['matched_segments'],
         pct(r['segment_precision_b_vs_a']), pct(r['segment_recall_b_vs_a']), pct(r['segment_f1']), num(r['matched_boundary_mae_seconds'])]
        for r in events if r['group'] == 'all'])
    lines += ['', 'Boundary MAE averages absolute onset and offset differences **only for matched events**. '
              'Its match count must be read alongside the error: an apparently small MAE can come from matching very few events. '
              'CSV also includes signed onset/offset differences (positive means B is later), and directional best-segment IoU '
              'averaged uniformly or weighted by segment duration, with no one-to-one restriction for those coverage measures.', '',
              '## 6. Do failure starts and ends align?', '',
              'Onsets and offsets are matched separately, one-to-one, within 0.25, 0.5 or 1.0 seconds. '
              'Failure already active at episode start and failure continuing through episode end are censored: '
              'those artificial edge boundaries are excluded. This tests timing independently of whole-event IoU.', '']
    lines += md_table(['Pair', 'Tolerance (s)', 'Onset F1', 'Offset F1', 'Onset matches / A,B', 'Offset matches / A,B'], [
        [r['pair'], r['tolerance_seconds'], pct(r['boundary_f1']), pct(off['boundary_f1']),
         f"{r['matched_boundaries']} / {r['a_boundaries']},{r['b_boundaries']}",
         f"{off['matched_boundaries']} / {off['a_boundaries']},{off['b_boundaries']}"]
        for r in boundaries if r['boundary'] == 'onset' and r['group'] == 'all'
        for off in [next(x for x in boundaries if x['pair'] == r['pair'] and x['tolerance_seconds'] == r['tolerance_seconds'] and x['boundary'] == 'offset' and x['group'] == 'all')]])
    lines += ['', '## 7. Three-way agreement', '',
              'The three raters here are Astra, joint Qwen and one FLORA mapping at a time. '
              'Unanimity includes both all-failure and all-non-failure. Three-way failure Jaccard = frames all three call '
              'failure / frames at least one calls failure. Fleiss κ is descriptive for these correlated, heterogeneous labelers.', '']
    lines += md_table(['FLORA mapping', 'Weighting', 'Unanimous', 'All failure', 'All non-failure', '3-way failure Jaccard', 'Fleiss κ'], [
        [r['flora_mapping'], r['weighting'], pct(r['unanimous']), pct(r['all_failure']), pct(r['all_nonfailure']),
         pct(r['failure_jaccard']), num(r['fleiss_kappa'])] for r in triples])
    lines += ['', 'All eight vote patterns and their frame, time and equal-episode shares are in `three_way_patterns.csv`. '
              'This identifies which labeler is the lone dissenter; majority agreement is not treated as truth.', '',
              '## 8. Episode-presence agreement', '',
              'An episode is positive if the labeler marks at least one failure frame. '
              'This discards duration and timing; a single-frame failure makes the whole episode positive.', '']
    lines += md_table(['Pair', 'Episode agreement', 'Failure-episode F1', 'Both positive', 'B only positive', 'A only positive', 'Both negative'], [
        [r['pair'], pct(m['agreement']), pct(m['failure_f1']), int(m['both_failure']), int(m['b_only_failure']), int(m['a_only_failure']), int(m['both_nonfailure'])]
        for r in full for m in [metrics(sum((confusion(np.array([e['tracks'][r['a']].any()]), np.array([e['tracks'][r['b']].any()])) for e in episodes), np.zeros(4))) ]])
    lines += ['', '## 9. Trivial baselines against Astra', '',
              'These help interpret whether a metric rewards a degenerate labeling policy. Source-frame weighting.', '']
    baseline = []
    for value, label in [(False, 'Always non-failure'), (True, 'Always failure')]:
        c = sum((confusion(e['tracks']['Astra'], np.full(e['n_frames'], value, dtype=bool)) for e in episodes), np.zeros(4))
        m = metrics(c)
        baseline.append([label, pct(m['agreement']), pct(m['b_failure_precision_vs_a']), pct(m['b_failure_recall_vs_a']), pct(m['failure_f1']), pct(m['b_balanced_accuracy_vs_a'])])
    lines += md_table(['Policy', 'Agreement', 'Failure precision', 'Failure recall', 'Failure F1', 'Balanced accuracy'], baseline)
    lines += ['', '## 10. Sampling uncertainty', '',
              '95% percentile bootstrap intervals, 2,000 whole-episode resamples with replacement, seed 20261112. '
              'Frames within an episode are kept together. Intervals describe variation across the observed episode pool; '
              'they do not account for teacher error, training randomness, or provide a human-accuracy confidence interval. '
              'Only two PRISM episodes are present, so subgroup generalization is particularly limited.', '']
    lines += md_table(['Pair', 'Metric', 'Value', '95% episode-bootstrap interval'], [
        [r['pair'], r['metric'], num(r['estimate']) if r['metric'] == 'cohen_kappa' else pct(r['estimate']),
         f"{num(r['low'])}–{num(r['high'])}" if r['metric'] == 'cohen_kappa' else f"{pct(r['low'])}–{pct(r['high'])}"]
        for r in boot if r['weighting'] == 'frames'])
    lines += ['', 'Full intervals for all three weightings are in `bootstrap_intervals.csv`.', '',
              '## Metric menu', '',
              '| Question | Metrics to inspect | Limitation |', '|---|---|---|',
              '| How often are labels identical? | Agreement, with failure rate and trivial baseline | Non-failure frames can dominate |',
              '| Do the same moments get called failure? | Failure F1 / Dice and failure IoU | Ignores correct non-failure moments |',
              '| Is agreement higher than expected from label rates? | Cohen κ, MCC | Sensitive to prevalence; no correctness guarantee |',
              '| How conservative is one labeler relative to another? | Directional precision, failure recall, non-failure recall, balanced accuracy | Requires a named reference convention |',
              '| Are all episodes represented comparably? | Seconds-weighted, equal-episode pooled, mean-episode F1, lab breakdown | Different weightings answer different questions |',
              '| Are failure events matched without excessive splitting? | Event F1 at IoU 0.1/0.3/0.5, failure-run counts | Sensitive to segmentation and threshold |',
              '| Are event transitions timed similarly? | Onset/offset F1 at tolerances, matched-event boundary error | Boundary error alone ignores unmatched events |',
              '| Do all three labelers agree? | Unanimity, vote patterns, three-way failure Jaccard | Majority agreement is not ground truth |', '',
              '## Calculation and audit details', '',
              'The entire native timeline is scored, not frames sampled from the 4x MP4. Each source frame is scored once. '
              'No overlapping inference window is counted twice. All 50 episodes have complete labels from every source. '
              'No unknown frames are imputed. Undefined divisions (e.g. F1 when both failure sets are empty, κ for identical '
              'constant labels, MCC with a constant margin) are N/A, not silently set to 0 or 1. '
              'Mean-episode metrics disclose their number of defined episodes. Percentages in CSV are stored as fractions.', '',
              'Frame F1, precision and recall against Astra reproduce the existing Qwen and FLORA reports. '
              'Event matching here uses maximum-cardinality matching with an IoU tie-break, rather than the older Qwen '
              'script’s greedy IoU matching; event metrics are therefore a new, consistently recomputed comparison.', '',
              'Files: `pairwise_metrics.csv`, `per_episode_metrics.csv`, `model_summary.csv`, `segment_metrics.csv`, '
              '`boundary_metrics.csv`, `three_way_patterns.csv`, `three_way_summary.csv`, `bootstrap_intervals.csv`. '
              'Provenance hashes and normalized labels are internal audit artifacts.', '']
    (out / 'results.md').write_text('\n'.join(lines), encoding='utf-8')


def plots(out, pairwise, summaries):
    fig, axes = plt.subplots(2, 3, figsize=(13, 8), constrained_layout=True)
    for row, flora in enumerate(['Flora', 'FloraNonNormal']):
        names = ['Astra', 'Qwen', flora]
        for col, (key, title, cmap, lower) in enumerate([
            ('agreement', 'Frame agreement', 'Blues', 0), ('failure_f1', 'Failure F1 / Dice', 'YlGnBu', 0),
            ('cohen_kappa', 'Cohen κ', 'RdYlGn', -1)]):
            matrix = np.eye(3)
            for i in range(3):
                for j in range(i + 1, 3):
                    r = next(r for r in pairwise if r['group'] == 'all' and r['weighting'] == 'frames' and {r['a'], r['b']} == {names[i], names[j]})
                    matrix[i, j] = matrix[j, i] = r[key]
            ax = axes[row, col]
            ax.imshow(matrix, vmin=lower, vmax=1, cmap=cmap)
            labels = ['Astra', 'Joint Qwen', 'FLORA (1)' if flora == 'Flora' else 'FLORA (1+2)']
            ax.set_xticks(range(3), labels, rotation=25, ha='right')
            ax.set_yticks(range(3), labels)
            ax.set_title(title)
            for (i, j), value in np.ndenumerate(matrix):
                ax.text(j, i, f'{value:.3f}' if key == 'cohen_kappa' else f'{100*value:.1f}%', ha='center', va='center',
                        color='white' if key != 'cohen_kappa' and value > .65 else 'black', fontsize=12)
    fig.suptitle('Same 50 episodes • 8,132 source frames • symmetric pairwise agreement\n'
                 'FLORA (1): failure only; FLORA (1+2): failure + suboptimal', fontsize=14)
    for ext in ['png', 'svg']:
        fig.savefig(out / ('pairwise_overview.' + ext), dpi=180)
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), constrained_layout=True)
    x = np.arange(3)
    for i, label in enumerate(['Qwen', 'Flora', 'FloraNonNormal']):
        ys = [100 * next(r for r in pairwise if r['a'] == 'Astra' and r['b'] == label and r['group'] == 'all' and r['weighting'] == w)['failure_f1'] for w in WEIGHTS]
        bars = axes[0].bar(x + (i - 1)*.25, ys, .24, label=DISPLAY[label])
        axes[0].bar_label(bars, fmt='%.1f', fontsize=9)
    axes[0].set_xticks(x, ['Frames', 'Seconds', 'Equal episode\n(pooled)'])
    axes[0].set_ylim(0, 100)
    axes[0].set_ylabel('Failure F1 vs Astra (%)')
    axes[0].set_title('Weighting sensitivity')
    axes[0].legend(fontsize=8)
    y = np.arange(len(summaries))
    short = [s['short_failure_runs'] for s in summaries]
    long = [s['failure_runs'] - s['short_failure_runs'] for s in summaries]
    axes[1].barh(y, long, label='≥0.5 s', color='#36856c')
    axes[1].barh(y, short, left=long, label='<0.5 s', color='#c57b33')
    axes[1].set_yticks(y, [r['labeler'].replace(': ', ':\n') for r in summaries])
    for i, r in enumerate(summaries):
        axes[1].text(r['failure_runs'] + 2, i, str(r['failure_runs']), va='center')
    axes[1].set_xlim(0, max(r['failure_runs'] for r in summaries) * 1.17)
    axes[1].set_xlabel('Contiguous failure runs across 50 episodes')
    axes[1].set_title('Temporal fragmentation (no smoothing)')
    axes[1].legend(fontsize=9)
    for ext in ['png', 'svg']:
        fig.savefig(out / ('weighting_and_fragmentation.' + ext), dpi=180)
    plt.close(fig)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    out = a.out
    assert not (out / 'results.md').exists(), 'Choose a new result version'
    inputs = json.loads((out / 'aligned_labels_internal.json').read_text())
    episodes = inputs['episodes']
    for e in episodes:
        e['tracks'] = dict(Astra=np.array(e['astra'], dtype=bool), Qwen=np.array(e['qwen'], dtype=bool),
                           Flora=np.array(e['flora_native']) == 1, FloraNonNormal=np.array(e['flora_native']) <= 2)
    groups = {'all': episodes} | {lab: [e for e in episodes if e['lab'] == lab] for lab in sorted({e['lab'] for e in episodes})}
    pairwise, per_episode, events, boundaries, summaries, patterns, triples, boot = [], [], [], [], [], [], [], []
    rng = np.random.default_rng(20261112)
    draws = rng.integers(0, len(episodes), (2000, len(episodes)))
    for left, right in PAIRS:
        pair = DISPLAY[left] + ' / ' + DISPLAY[right]
        counts = np.array([confusion(e['tracks'][left], e['tracks'][right]) for e in episodes])
        for e, c in zip(episodes, counts):
            per_episode.append(dict(pair=pair, a=left, b=right, episode=e['id'], lab=e['lab'], **metrics(c)))
        for group, es in groups.items():
            cc = np.array([confusion(e['tracks'][left], e['tracks'][right]) for e in es])
            for weight in WEIGHTS:
                factors = np.array([1 if weight == 'frames' else 1/e['fps'] if weight == 'seconds' else 1/e['n_frames'] for e in es])
                values = metrics(np.sum(cc * factors[:, None], axis=0))
                pairwise.append(dict(pair=pair, a=left, b=right, group=group, weighting=weight, **values))
                if group == 'all':
                    samples = np.sum((cc * factors[:, None])[draws], axis=1)
                    bm = [metrics(c) for c in samples]
                    for key in ['agreement', 'failure_f1', 'failure_iou', 'cohen_kappa']:
                        vals = [r[key] for r in bm if r[key] is not None]
                        low, high = np.quantile(vals, [.025, .975])
                        boot.append(dict(pair=pair, weighting=weight, metric=key, estimate=values[key], low=low,
                                         high=high, defined_resamples=len(vals), resamples=2000, seed=20261112))
            for threshold in [.1, .3, .5]:
                events.append(dict(pair=pair, group=group, iou_threshold=threshold, **event_metrics(es, left, right, threshold)))
            for tolerance in [.25, .5, 1.]:
                for direction, name in [(1, 'onset'), (-1, 'offset')]:
                    boundaries.append(dict(pair=pair, group=group, tolerance_seconds=tolerance, boundary=name,
                                           **boundary_metrics(es, left, right, tolerance, direction)))
    total_seconds = sum(e['n_frames']/e['fps'] for e in episodes)
    for label in DISPLAY:
        runs = [(b - a)/e['fps'] for e in episodes for a, b in segments(e['tracks'][label])]
        positive = sum(int(e['tracks'][label].sum()) for e in episodes)
        summaries.append(dict(labeler=DISPLAY[label], failure_frames=positive, failure_frame_fraction=positive/8132,
                              failure_time_fraction=sum(e['tracks'][label].sum()/e['fps'] for e in episodes)/total_seconds,
                              mean_episode_failure_fraction=float(np.mean([e['tracks'][label].mean() for e in episodes])),
                              episodes_with_failure=sum(int(e['tracks'][label].any()) for e in episodes),
                              failure_runs=len(runs), median_failure_run_seconds=float(np.median(runs)) if runs else None,
                              short_failure_runs=sum(t < .5 for t in runs), short_failure_run_fraction=divide(sum(t < .5 for t in runs), len(runs)),
                              switches_per_minute=sum(np.count_nonzero(np.diff(e['tracks'][label])) for e in episodes)/total_seconds*60))
    for flora in ['Flora', 'FloraNonNormal']:
        for weight in WEIGHTS:
            tally = np.zeros(8)
            for e in episodes:
                bits = e['tracks']['Astra'].astype(int)*4 + e['tracks']['Qwen'].astype(int)*2 + e['tracks'][flora].astype(int)
                factor = 1 if weight == 'frames' else 1/e['fps'] if weight == 'seconds' else 1/e['n_frames']
                tally += np.bincount(bits, minlength=8) * factor
            shares = tally/tally.sum()
            for value in range(8):
                patterns.append(dict(flora_mapping=DISPLAY[flora], weighting=weight, astra=(value >> 2)&1,
                                     qwen=(value >> 1)&1, flora=value&1, weight=tally[value], fraction=shares[value]))
            p_fail = sum(shares[i] * i.bit_count()/3 for i in range(8))
            observed = sum(shares[i] * (1 if i in [0, 7] else 1/3) for i in range(8))
            expected = p_fail**2+(1-p_fail)**2
            triples.append(dict(flora_mapping=DISPLAY[flora], weighting=weight,
                                unanimous=shares[0]+shares[7], all_failure=shares[7], all_nonfailure=shares[0],
                                failure_jaccard=divide(shares[7], 1-shares[0]), fleiss_kappa=divide(observed-expected, 1-expected)))
    # Independently reproduce published confusion counts before writing comparisons.
    expected = {('Astra', 'Qwen'): [453, 59, 1642, 5978], ('Astra', 'Flora'): [1629, 1039, 466, 4998],
                ('Astra', 'FloraNonNormal'): [1706, 1672, 389, 4365]}
    for pair, c in expected.items():
        actual = next(r for r in pairwise if (r['a'], r['b']) == pair and r['weighting'] == 'frames' and r['group'] == 'all')
        assert all(actual[k] == v for k, v in zip(['both_failure', 'b_only_failure', 'a_only_failure', 'both_nonfailure'], c))
    for name, rows in [('pairwise_metrics', pairwise), ('per_episode_metrics', per_episode), ('model_summary', summaries),
                       ('segment_metrics', events), ('boundary_metrics', boundaries), ('three_way_patterns', patterns),
                       ('three_way_summary', triples), ('bootstrap_intervals', boot)]:
        csv_write(out / (name + '.csv'), rows)
    result = dict(episodes=50, frames=8132, seconds=total_seconds, pairwise=pairwise, per_episode=per_episode,
                  model_summary=summaries, segments=events, boundaries=boundaries, three_way=triples,
                  bootstrap=boot, source_labels_sha256=hashlib.sha256((out/'aligned_labels_internal.json').read_bytes()).hexdigest())
    (out/'metrics_internal.json').write_text(json.dumps(clean(result), indent=2, allow_nan=False)+'\n')
    plots(out, pairwise, summaries)
    build_report(out, episodes, pairwise, per_episode, summaries, events, boundaries, patterns, triples, boot)
    print('Completed: five pairwise comparisons, three weightings, two labs, event/boundary metrics, bootstrap intervals, CSVs and figures.')
    for row in pairwise:
        if row['group'] == 'all' and row['weighting'] == 'frames':
            print(row['pair'], 'agreement', pct(row['agreement']), 'F1', pct(row['failure_f1']), 'kappa', num(row['cohen_kappa']))


if __name__ == '__main__':
    main()
