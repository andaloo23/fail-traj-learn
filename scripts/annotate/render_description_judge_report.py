"""Render a saved judge comparison with control examples and local baselines."""
import argparse
import html
import json
from pathlib import Path


def render(folder):
    data = json.loads((folder / 'comparison.json').read_text(encoding='utf-8'))
    judges = list(data['summaries'])
    rows = {}
    for row in data['pairs']:
        rows.setdefault((row['batch'], row['pair_id']), {})[row['judge']] = row
    local = {}
    for key in ('nli', 'minilm'):
        path = folder / ('local_' + key + '.json')
        if path.exists():
            values = json.loads(path.read_text(encoding='utf-8'))
            local[key] = {(r['batch'], r['pair_id']): r for r in values['pairs']}
    esc = html.escape
    parts = ['<!doctype html><html lang="en"><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width,initial-scale=1">',
        '<title>Description judge comparison</title>',
        '<style>body{font:16px/1.6 system-ui;color:#e9eef5;background:#101720;margin:0}main{max-width:1100px;margin:auto;padding:30px}h1{line-height:1.15}table{border-collapse:collapse;width:100%;font-size:14px}td,th{padding:10px;border:1px solid #405269;text-align:left}th{background:#213249}a{color:#9eceff}details{border:1px solid #405269;border-radius:6px;padding:12px;margin:12px 0}summary{cursor:pointer;font-weight:600}.muted{color:#b2c1d2}.texts{display:grid;grid-template-columns:1fr 1fr;gap:18px}.score{white-space:nowrap}.fail{color:#ffbe87}pre{white-space:pre-wrap} @media(max-width:700px){main{padding:16px}.texts{grid-template-columns:1fr}table{font-size:12px}td,th{padding:5px}}</style><main>',
        '<h1>Description judge comparison</h1>',
        '<p>Matched rubric and pairs; each pair judged in both input orders. '
        '33 real overlapping pairs and 23 authored controls. All four models use '
        'nominal medium reasoning. Provider request roles and reasoning settings '
        'are not identical. Historical Astra judgments are reused for the original pairs.</p>',
        '<p><b>Control fit measures agreement with authored expected score ranges, '
        'not video correctness.</b> A control passes only if both input orders fit '
        'its expected range. Counts are descriptive on development examples.</p>',
        '<table><tr><th>Judge</th><th>Control fit</th><th>Order disagreements</th><th>New generation estimate</th></tr>']
    attempts = [json.loads(p.read_text(encoding='utf-8')) for p in (folder / 'attempts').glob('*.json')]
    for judge in judges:
        summary = data['summaries'][judge]
        cost = sum(r.get('generation_estimate_usd', 0) for r in attempts if r['judge'] == judge)
        parts.append(f"<tr><td>{esc(summary['model'])}</td><td>{summary['controls_passed']}/{summary['controls_total']}</td>"
                     f"<td>{summary['order_disagreements']}/{summary['paired_items']}</td><td>${cost:.4f}</td></tr>")
    cost = data['cost']
    parts += ['</table>',
        f"<p>{cost['validated']}/{cost['planned']} new calls validated. Generation estimate ${cost['generation_estimate_usd']:.4f}; "
        f"separate conservative input-count allowance ${cost['preflight_allowance_usd']:.4f}. Historical baseline costs are excluded.</p>",
        '<h2>What the current rubric misses or leaves unresolved</h2>',
        '<ul><li>All judges treat an omitted brief basket bump as a minor detail (score 4); '
        'the authored target was a material omission (3). This exposes a choice about '
        'event importance: a bump with no specified consequence does not itself prove failure.</li>',
        '<li>An omitted release receives different judgments: Astra gives 3 and 5 across '
        'input order, Luna gives 5 in both orders, and Gemini gives 4 and 5. The judges '
        'can infer release from the word “places,” although it was not explicitly stated.</li>',
        '<li>A text-only judge cannot detect a shared hallucination or an event absent '
        'from both descriptions, and does not evaluate temporal localization.</li>',
        '<li>A single ordinal score mixes factual contradictions, missing claims, '
        'scope, and harmless elaboration. It is not a probability of correctness.</li></ul>',
        '<h2>Local baselines</h2><p>Directional NLI distinguishes many omissions from '
        'contradictions, but gives similar asymmetric entailment patterns to both '
        'small details and material omissions. It also flags the unrelated-description '
        'control as contradiction. Embedding cosine stays high on several '
        'meaning-changing edits. Neither baseline supplies video truth.</p>',
        '<h2>Inspect each control</h2>']
    for key, judged in rows.items():
        row = next(iter(judged.values()))
        if 'expected_min' not in row:
            continue
        parts.append(f"<details><summary>{esc(row['name'])} — authored range {row['expected_min']}–{row['expected_max']}</summary>"
                     f"<div class='texts'><p><b>A</b><br>{esc(row['left'])}</p><p><b>B</b><br>{esc(row['right'])}</p></div>"
                     '<table><tr><th>Judge</th><th>A/B</th><th>B/A</th><th>Explanation in A/B order</th></tr>')
        for judge in judges:
            r = judged.get(judge)
            if r is None:
                continue
            a, b = r['judgments']['ab'], r['judgments']['ba']
            cls = ' class="fail"' if not r['passed'] else ''
            parts.append(f"<tr{cls}><td>{esc(judge)}</td><td>{a['score']}</td><td>{b['score']}</td><td>{esc(a['explanation'])}</td></tr>")
        parts.append('</table>')
        nli = local.get('nli', {}).get(key)
        embedding = local.get('minilm', {}).get(key)
        if nli:
            parts.append(f"<p class='muted'>NLI entailment A→B {nli['forward']['entailment']:.3f}; "
                         f"B→A {nli['reverse']['entailment']:.3f}; mean contradiction {nli['mean_contradiction']:.3f}.</p>")
        if embedding:
            parts.append(f"<p class='muted'>MiniLM cosine: {embedding['cosine']:.3f}.</p>")
        parts.append('</details>')
    parts += ['<h2>Real pairs with judge disagreement</h2><p>These have no human '
              'equivalence reference. A lower score does not mean a better judge.</p>']
    for key, judged in rows.items():
        row = next(iter(judged.values()))
        if 'expected_min' in row or len({r['score'] for r in judged.values()}) == 1:
            continue
        parts.append(f"<details><summary>{esc(key[0] + '/' + key[1])}</summary><div class='texts'>"
                     f"<p><b>A</b><br>{esc(row['left'])}</p><p><b>B</b><br>{esc(row['right'])}</p></div>"
                     '<p>' + '; '.join(f"{esc(j)}: {r['judgments']['ab']['score']}/{r['judgments']['ba']['score']}"
                                      for j, r in judged.items()) + '</p></details>')
    parts += ['<h2>Next comparison</h2><p>Keep the rubric judge as a baseline. '
              'Compare it with a judge that explicitly marks matching, omitted, '
              'contradictory, and unresolved claims for operation, participant, '
              'result, and task effect. Keep directional NLI as a separate diagnostic. '
              'Decide how to weight short events and release evidence before '
              'validating on new human-reviewed pairs.</p>',
              '<p><a href="comparison.json">Full comparison JSON</a> · '
              '<a href="manifest.json">Frozen input manifest</a> · '
              '<a href="rubric.txt">Exact rubric</a></p>',
              '<p class="muted">' + esc(data['limitations']) + '</p></main></html>']
    destination = folder / 'report.html'
    destination.write_text('\n'.join(parts), encoding='utf-8')
    print(destination)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    args = parser.parse_args()
    render(args.run.resolve())
