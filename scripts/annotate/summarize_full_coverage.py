"""Offline audit and human-review report for the specific-prompt rerun."""
import json
import api_frame_selection_full_coverage_v1 as run
from review_api_experiment import parse_segments


def main():
    manifest = run.verify()
    prior = run.ROOT / 'outputs/frame_selection_prompt_v2'
    records = {p.stem: run.common.load(p) for p in (run.OUT / 'attempts').glob('*.json')}
    warnings = []
    coverage = []
    for name in ('select_frames.md', 'annotate_frame_subset.md'):
        assert (run.OUT / 'prompts' / name).read_bytes() == (prior / 'prompts' / name).read_bytes()
    for episode in manifest['episodes']:
        eid = episode['id']
        assert (run.OUT / eid / 'input.json').read_bytes() == (prior / eid / 'input.json').read_bytes()
        for path in (run.OUT / eid / 'images').glob('*.jpg'):
            assert path.read_bytes() == (prior / eid / 'images' / path.name).read_bytes()
    for job in run.jobs():
        row = records.get(job['id'])
        if not row or row['status'] != 'completed':
            continue
        _, _, evidence = run.build_payload(job)
        assert evidence == run.common.load(run.OUT / 'requests' / (job['id'] + '_evidence.json'))
        raw = run.common.load(run.OUT / 'responses' / (job['id'] + '_raw.json'))
        assert run.usage_cost(job['provider'], raw)['generation_estimate_usd'] == row['generation_estimate_usd']
        answer, complete = run.extract_answer(job['provider'], raw)
        assert complete and answer == (run.OUT / 'responses' / (job['id'] + '.md')).read_text(encoding='utf-8')
        if job['arm'] != 'E':
            ep = run.common.load(run.OUT / job['episode'] / 'input.json')
            segments, errors = parse_segments(answer, ep['n_frames'])
            if not segments or any('progress' not in s for s in segments):
                errors.append('Missing full-coverage binary labels')
            coverage.append({'id': job['id'], 'segments': len(segments), 'warnings': errors,
                             'review_required_segments': sum(s.get('review_required', False) for s in segments)})
            warnings += [job['id'] + ': ' + e for e in errors]
    run.common.write_json(run.OUT / 'coverage_audit.json', coverage)
    totals = run.report()
    unknown_reserve = sum(r['reserved_usd'] for r in records.values() if r['id'] in totals['unknown_cost_requests'])
    costs = {a: sum(r.get('generation_estimate_usd') or 0 for r in records.values() if r['arm'] == a) for a in run.PROVIDERS}
    lines = ['# Full-coverage rerun: results', '',
             f'Completed **{totals["completed"]}/24 cells** on R001–R004. No model-based annotation-quality scores are computed.', '',
             'The common annotation prompt requires a complete partition with explicit progress/failure yes/no',
             'and confidence/review flags for every segment. Source images, telemetry, models, output limits,',
             'selector and subset prompts are unchanged from the specific-prompt run. No human examples are',
             'supplied. E is generated afresh, so stochastic frame selections can differ. No automatic retries.', '',
             '## This rerun: estimated generation costs (USD)', '',
             '| Condition | Completed | R001 | R002 | R003 | R004 | Total known |',
             '|---|---:|---:|---:|---:|---:|---:|']
    for arm, title in run.LABELS.items():
        cells = [records.get(f'{eid}_{arm}', {}) for eid in run.IDS]
        values = [f'${r["generation_estimate_usd"]:.6f}' if r.get('generation_estimate_usd') is not None else
                  'unknown' if r.get('generation_sent') else 'not run' for r in cells]
        lines.append(f'| {arm}: {title} | {sum(r.get("status") == "completed" for r in cells)} | ' + ' | '.join(values) + f' | ${costs[arm]:.6f} |')
    lines += ['', f'Known generation estimate: **${totals["generation_estimate_usd"]:.6f}**.',
              f'Conservative token-count allowance: **${totals["preflight_input_rate_allowance_usd"]:.6f}**.',
              f'Estimate plus allowance: **${totals["estimate_plus_preflight_allowance_usd"]:.6f}**, against the $4.16 reservation limit.',
              'Generation costs include input/cache-write, output and thinking usage. Token-count allowances are',
              'conservative bookkeeping, not observed charges. Provider invoices were not queried.',
              f'Unknown-cost requests in this rerun: {", ".join(totals["unknown_cost_requests"]) or "none"}.', '',
              f'Additional full reservation for unknown generation charges: **${unknown_reserve:.6f}**.',
              f'Known estimate + token-count allowance + unknown reservations: **${totals["estimate_plus_preflight_allowance_usd"] + unknown_reserve:.6f}**.',
              'R004_B disconnected without a response or usage record and was not retried. The unsent R004 C-F',
              'jobs were completed separately using the same frozen inputs and budget ledger.', '',
              '## Pipeline cost', '', '| Episode | C full GPT | D uniform GPT | E selector + F GPT |', '|---|---:|---:|---:|']
    for eid in run.IDS:
        values = []
        for arms in ('C', 'D', 'EF'):
            rows = [records.get(f'{eid}_{a}', {}) for a in arms]
            values.append(f'${sum(r["generation_estimate_usd"] for r in rows):.6f}' if all(r.get('generation_estimate_usd') is not None for r in rows) else 'incomplete')
        lines.append('| ' + eid + ' | ' + ' | '.join(values) + ' |')
    cumulative = totals['cumulative_with_baseline']
    lines += ['', '## Including preceding experiments', '',
              f'Known generation estimates across this and preceding experiments: ${cumulative["known_generation_estimate_usd"]:.6f}.',
              f'Combined conservative token-count allowances: ${cumulative["preflight_allowance_usd"]:.6f}.',
              f'Full reservations for requests with unknown charges: ${cumulative["unknown_full_reservations_usd"]:.2f}.',
              'The previous R003_E timeout remains unknown and is not counted as free. The current run is a new',
              'authorized experiment, not a retry or recovery of that request.', '',
              '## Review and interpretation', '',
              'Use the viewer Run selector to compare Specific prompts and Full coverage for the same episode',
              'and condition. Green/red bars reflect explicit model intervals, not human-verified labels.',
              'Review object identity, task relevance, additional physical failures and boundary uncertainty.',
              'New A–D have identical visual inputs to old A–D. New F can have different selected frames because',
              'the unchanged selector is sampled afresh. Do not attribute cross-run F differences solely to the annotation prompt.',
              'This is a development rerun on inspected episodes, one generation per cell; broader generalization',
              'and separation from model variability require fresh human-reviewed episodes and repeats.', '',
              '## Offline checks', '',
              'Verified frozen input/code hashes, exact source image and telemetry equality, all completed request',
              'hashes, saved answers and usage-derived costs, and selected-image provenance via the runner.',
              'Timeline parser warnings: ' + ('; '.join(warnings) if warnings else 'none.') , '',
              '[Review viewer](web_review/index.html) | [Per-call costs](costs.csv) | [Raw cost summary](cost_summary.json) |',
              '[Full-coverage protocol](../../docs/frame_selection_full_coverage.md)']
    (run.OUT / 'RESULTS.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps({k: totals[k] for k in ('completed', 'generation_estimate_usd', 'preflight_input_rate_allowance_usd',
          'estimate_plus_preflight_allowance_usd', 'unknown_cost_requests', 'by_provider', 'cumulative_with_baseline')}, indent=2))


if __name__ == '__main__':
    main()
