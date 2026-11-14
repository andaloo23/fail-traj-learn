"""Offline integrity and cost summary for the resumed annotation experiment."""
import json
import api_frame_selection_v3 as run


def main():
    run.verify()
    rows = {j['id']: run.common.load(run.OUT / 'attempts' / (j['id'] + '.json')) for j in run.jobs()}
    if any(r['status'] != 'completed' for r in rows.values()):
        raise ValueError('Comparison incomplete; no final summary written')
    for job in run.jobs():
        _, text, evidence = run.build_payload(job)
        if evidence != run.common.load(run.OUT / 'requests' / (job['id'] + '_evidence.json')):
            raise ValueError('Request evidence changed')
        raw = run.common.load(run.OUT / 'responses' / (job['id'] + '_raw.json'))
        cost = run.usage_cost(job['provider'], raw)
        if cost['generation_estimate_usd'] != rows[job['id']]['generation_estimate_usd']:
            raise ValueError('Usage cost mismatch')
        answer, complete = run.extract_answer(job['provider'], raw)
        if not complete or answer != (run.OUT / 'responses' / (job['id'] + '.md')).read_text(encoding='utf-8'):
            raise ValueError('Response mismatch or truncation')
    totals = run.report()
    by_arm = {a: sum(rows[f'{eid}_{a}']['generation_estimate_usd'] for eid in run.IDS) for a in run.PROVIDERS}
    by_provider = totals['by_provider']
    lines = ['# Completed annotation experiment', '',
             'All 24 cells completed: 20 candidate annotations and 4 frame selections across four development episodes.',
             'There were 24 generation requests in total across v1/v2/v3; completed requests were reused, never regenerated.', '',
             '## What was fixed', '',
             'Gemini media resolution is explicitly LOW in both direct annotation and selection. The R001 direct input',
             'count fell from 133,226 to 38,264 with the same 114 JPEGs. Its image tokens fell from 124,146 to 29,184.',
             'All static inputs passed preflight before new generation; dynamic selected inputs were counted after selection.',
             'The Markdown parser also now accepts standard *, +, and - bullets. No model answer or selection was repaired.', '',
             '## Cost', '',
             f'- OpenAI generation estimate: ${by_provider["openai"]["generation_estimate_usd"]:.6f}.',
             f'- Gemini generation estimate: ${by_provider["gemini"]["generation_estimate_usd"]:.6f}.',
             f'- Combined generation estimate: ${totals["generation_estimate_usd"]:.6f}.',
             f'- Separate conservative preflight allowance, including the blocked count and diagnostics: ${totals["preflight_input_rate_allowance_usd"]:.6f}.',
             f'- Estimate plus allowance: ${totals["estimate_plus_preflight_allowance_usd"]:.6f}.',
             f'- Total reservations including prior diagnostics: ${totals["reserved_usd"]:.2f}, against the original $4.48 total envelope.', '',
             'Estimates use returned usage and published rates, including thinking and cache writes. They are not invoice',
             'charges. The preflight allowance prices counted inputs conservatively; it is not an observed charge.',
             'Earlier credential smoke checks are excluded. Historical GPT R001_A is counted once.', '',
             '| Condition | Generation estimate over four episodes |', '|---|---:|']
    for arm in run.PROVIDERS:
        lines.append(f'| {arm}: {run.LABELS[arm]} | ${by_arm[arm]:.6f} |')
    lines += ['', '## Matched downstream and end-to-end comparison', '',
              '| Episode | C full input tokens | D uniform tokens | F selected tokens | C generation USD | E+F generation USD |',
              '|---|---:|---:|---:|---:|---:|']
    for eid in run.IDS:
        ep = run.common.load(run.OUT / eid / 'input.json')
        selected = run.selected_frames(ep)
        if len(selected) != len(ep['uniform']):
            raise ValueError('Unmatched retained frame budgets')
        c, d, e, f = [rows[f'{eid}_{arm}'] for arm in 'CDEF']
        lines.append(f'| {eid} | {c["input_tokens"]} | {d["input_tokens"]} | {f["input_tokens"]} | ${c["generation_estimate_usd"]:.6f} | ${e["generation_estimate_usd"]+f["generation_estimate_usd"]:.6f} |')
    lines += ['', f'C generation total: ${by_arm["C"]:.6f}; E+F generation total: ${by_arm["E"]+by_arm["F"]:.6f}.',
              'These are observed usage-based estimates for this run, not a forecast at a fixed cache state. Cache hits and',
              'output length vary between calls. Inspect per-call cached/write/output tokens in costs.csv.', '',
              '## Annotation quality remains unmeasured', '',
              'The models can disagree on object identity, failures, and timing. No output is a human reference.',
              'Low Gemini media resolution is an explicit configuration choice, not evidence of preserved detail or accuracy.',
              'A versus B compares model/configuration combinations. D versus F holds downstream model, prompt, telemetry,',
              'image count and encoding fixed, and tests selection. E+F includes selector cost.', '',
              'Review the original 20 FPS recordings to create human references before inspecting candidate annotations',
              'where possible. Then review blinded candidate outputs for missing/false segments, unsupported claims,',
              'boundary uncertainty, and correction effort. No simulator scores or model agreement scores are used.', '',
              'Integrity checks passed for frozen inputs/code, all request hashes, saved answers, usage-derived costs,',
              'and selected-image provenance and budgets. These checks establish execution integrity, not label correctness.', '',
              '[Review page](index.html) | [Per-call costs](costs.csv) | [Full cost ledger](cost_summary.json)']
    (run.OUT / 'RESULTS.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps({k: totals[k] for k in ('completed', 'generation_estimate_usd', 'preflight_input_rate_allowance_usd', 'estimate_plus_preflight_allowance_usd', 'by_provider')}, indent=2))


if __name__ == '__main__':
    main()
