"""Standalone interactive result browser, plus a readable report/CSV/figure bundle."""
import argparse
import json
from pathlib import Path
import zipfile

from markdown_it import MarkdownIt


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    out = a.out
    assert not (out / 'index.html').exists()
    report = (out / 'results.md').read_text(encoding='utf-8')
    rendered = MarkdownIt('commonmark').enable('table').render(report)
    payload = (out / 'metrics_internal.json').read_text().replace('<', '\\u003c')
    template = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Astra / Qwen / FLORA — quantitative comparison</title>
<style>
:root{color-scheme:light;font-family:system-ui,sans-serif;color:#172d43;background:#f4f7fb}body{margin:0 auto;max-width:1450px;padding:30px}h1{font-size:32px;margin:0 0 12px}h2{margin-top:38px}h3{margin-top:26px}p,li{line-height:1.65}a{color:#135c96}label{font-size:14px;display:flex;flex-direction:column;gap:7px}select{font:inherit;padding:10px;background:white;border:1px solid #b0c3d4;border-radius:6px;min-width:150px}.controls{display:flex;flex-wrap:wrap;gap:20px;background:white;border:1px solid #d4dfeb;padding:20px;border-radius:10px}.note{background:#e8f0f8;border-left:4px solid #356b9d;padding:14px 18px}.scroll{overflow-x:auto;max-width:100%}table{border-collapse:collapse;width:100%;font-size:14px;background:white}th,td{text-align:left;padding:11px;border-bottom:1px solid #d8e2ed;white-space:nowrap}th{background:#e2edf6;color:#183e5e}td.num{text-align:right;font-variant-numeric:tabular-nums}.bar{height:12px;min-width:180px;background:#e6ecf1}.fill{height:100%;background:#3377a5}.downloads{margin:20px 0}img{max-width:100%;height:auto;background:white}#metric-note{min-height:30px}summary{font-size:21px;font-weight:600;cursor:pointer;padding:14px 0}button{cursor:pointer}.tag{display:inline-block;background:#e4edf5;border-radius:6px;padding:5px 9px;margin-right:8px;font-size:14px}.table-wrap{overflow-x:auto;margin:16px 0}#full-report h1{font-size:27px}#full-report table{font-size:13px}#episode-table td{font-size:13px}
</style></head><body>
<h1>Astra, joint Qwen and FLORA</h1>
<p><span class="tag">50 frozen validation episodes</span><span class="tag">8,132 source frames</span><span class="tag">679.867 seconds</span></p>
<p class="note"><strong>Agreement between labelers.</strong> Astra is the requested display name for preserved Sol (<code>gpt-6.1-sol</code>) annotations. Qwen is joint-trained Qwen2.5-VL-7B. These scores do not establish human-reference accuracy. No labels were smoothed.</p>
<div class="downloads"><a href="results.md">Full Markdown report</a> · <a href="comparison_report.zip" download>Report, figures and all CSV tables</a> · <a href="pairwise_metrics.csv" download>Pairwise CSV</a> · <a href="per_episode_metrics.csv" download>Per-episode CSV</a></div>
<div class="controls">
<label>Metric<select id="metric"></select></label>
<label>Weighting<select id="weight"><option value="frames">Each source frame</option><option value="seconds">Each elapsed second</option><option value="equal_episode">Equal episode, pooled</option></select></label>
<label>Episode group<select id="group"><option value="all">All 50 episodes</option><option value="Princeton_IRoM">Princeton_IRoM — 48 episodes</option><option value="Princeton_PRISM">Princeton_PRISM — 2 episodes</option></select></label>
<label>FLORA binary mapping<select id="mapping"><option value="Flora">Failure only (1 vs 2/3)</option><option value="FloraNonNormal">Failure + suboptimal (1/2 vs 3)</option></select></label>
</div>
<p id="metric-note"></p><div class="scroll"><table id="comparison"><thead><tr><th>Pair (A / B)</th><th id="metric-header">Score</th><th>Relative magnitude</th><th>95% episode-bootstrap interval</th></tr></thead><tbody></tbody></table></div>
<p><small>Bootstrap intervals appear for the full 50-episode pool and supported metrics. They resample complete episodes, not independent frames. Equal-episode pooled F1 differs from averaging per-episode F1; both are documented below.</small></p>
<h2>Episode detail</h2><label style="max-width:500px">Pair<select id="episode-pair"></select></label>
<p>Same selected metric, from lowest to highest. Per-episode values do not change under the weighting selector. Failure percentages below are source-frame fractions. N/A means the metric is undefined, not zero.</p>
<div class="scroll"><table id="episode-table"><thead><tr><th>Episode</th><th>Lab</th><th>Frames</th><th>A failure %</th><th>B failure %</th><th>Selected metric</th></tr></thead><tbody></tbody></table></div>
<h2>Figures</h2><img src="pairwise_overview.png" alt="Pairwise agreement, failure F1 and Cohen kappa for both FLORA mappings"><img src="weighting_and_fragmentation.png" alt="Weighting sensitivity and failure-run fragmentation">
<details><summary>Full report: definitions, alternate metrics, event timing and uncertainty</summary><article id="full-report">__REPORT__</article></details>
<script id="data" type="application/json">__DATA__</script>
<script>
const R=JSON.parse(document.getElementById('data').textContent),$=id=>document.getElementById(id);
const metrics={agreement:['Frame agreement','Fraction of matching labels, including shared non-failure. Inspect failure prevalence and the always-non-failure baseline alongside it.'],failure_f1:['Failure F1 / Dice','Symmetric overlap of the two failure masks: 2 × shared failure / sum of their failure sizes.'],failure_iou:['Failure IoU','Symmetric shared failure / union of failure. Ignores shared non-failure.'],nonfailure_f1:['Non-failure F1','Symmetric Dice overlap of the two non-failure masks.'],macro_class_f1:['Class-macro F1','Average of failure F1 and non-failure F1, giving the two classes equal importance.'],cohen_kappa:['Cohen κ','Agreement corrected for the two observed label rates. No reference labeler is needed.'],mcc:['MCC','Binary association using all four confusion cells. Undefined when either labeler has a constant margin.'],b_failure_precision_vs_a:['B failure precision vs A','Directional: among frames B calls failure, the fraction A also calls failure. A is the first labeler named.'],b_failure_recall_vs_a:['B failure recall vs A','Directional: among frames A calls failure, the fraction B also calls failure. A is the first labeler named.'],b_nonfailure_recall_vs_a:['B non-failure recall vs A','Directional: among frames A calls non-failure, the fraction B also calls non-failure.'],b_balanced_accuracy_vs_a:['B balanced accuracy vs A','Directional: average of B failure recall and B non-failure recall, treating A as the reference convention.']};
for(const [key,[name]] of Object.entries(metrics)){const o=document.createElement('option');o.value=key;o.textContent=name;$('metric').appendChild(o)}
const format=(v,key)=>v===null?'N/A':(['cohen_kappa','mcc'].includes(key)?v.toFixed(3):(100*v).toFixed(2)+'%');
function cell(row,value,number=false){const td=document.createElement('td');td.textContent=value;if(number)td.className='num';row.appendChild(td);return td}
function drawEpisodes(){const key=$('metric').value,pair=$('episode-pair').value,group=$('group').value;const body=$('episode-table').tBodies[0];body.replaceChildren();const rows=R.per_episode.filter(r=>r.pair===pair&&(group==='all'||r.lab===group)).sort((a,b)=>(a[key]??Infinity)-(b[key]??Infinity)||a.episode.localeCompare(b.episode));for(const r of rows){const tr=document.createElement('tr');cell(tr,r.episode);cell(tr,r.lab.replace('Princeton_',''));cell(tr,r.total_weight,true);cell(tr,format((r.both_failure+r.a_only_failure)/r.total_weight,'agreement'),true);cell(tr,format((r.both_failure+r.b_only_failure)/r.total_weight,'agreement'),true);cell(tr,format(r[key],key),true);body.appendChild(tr)}}
function draw(){const key=$('metric').value,weight=$('weight').value,group=$('group').value,mapping=$('mapping').value;const rows=R.pairwise.filter(r=>r.group===group&&r.weighting===weight&&(r.b==='Qwen'||r.b===mapping));$('metric-note').textContent=metrics[key][1];$('metric-header').textContent=metrics[key][0];const body=$('comparison').tBodies[0];body.replaceChildren();for(const r of rows){const tr=document.createElement('tr');tr.dataset.a=r.a;tr.dataset.b=r.b;tr.dataset.score=r[key]??'';cell(tr,r.pair);cell(tr,format(r[key],key),true);const td=document.createElement('td'),bar=document.createElement('div'),fill=document.createElement('div');bar.className='bar';fill.className='fill';fill.style.width=(r[key]===null?0:Math.min(1,Math.abs(r[key])))*100+'%';if(r[key]<0)fill.style.background='#b9594b';bar.appendChild(fill);td.appendChild(bar);tr.appendChild(td);const ci=group==='all'?R.bootstrap.find(b=>b.pair===r.pair&&b.weighting===weight&&b.metric===key):null;cell(tr,ci?format(ci.low,key)+' – '+format(ci.high,key):'—');body.appendChild(tr)}const old=$('episode-pair').value;$('episode-pair').replaceChildren();for(const r of rows){const o=document.createElement('option');o.value=r.pair;o.textContent=r.pair;$('episode-pair').appendChild(o)}if(rows.some(r=>r.pair===old))$('episode-pair').value=old;drawEpisodes()}
for(const name of ['metric','weight','group','mapping'])$(name).addEventListener('change',draw);$('episode-pair').addEventListener('change',drawEpisodes);draw();
for(const table of document.querySelectorAll('#full-report table')){const wrap=document.createElement('div');wrap.className='table-wrap';table.replaceWith(wrap);wrap.appendChild(table)}
</script></body></html>'''
    (out / 'index.html').write_text(template.replace('__REPORT__', rendered).replace('__DATA__', payload), encoding='utf-8')
    with zipfile.ZipFile(out / 'comparison_report.zip', 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(out.iterdir()):
            if path.suffix in ['.csv', '.md', '.png', '.svg', '.html']:
                archive.write(path, path.name)
    print('Created standalone interactive comparison, full readable report and CSV/figure ZIP.')


if __name__ == '__main__':
    main()
