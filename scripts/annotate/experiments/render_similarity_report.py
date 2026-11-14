"""Build a self-contained interactive report from the frozen exploration outputs."""
import csv
import hashlib
import html
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'outputs/similarity_exploration_v1'

def load(path):return json.loads(path.read_text(encoding='utf-8'))
def esc(x):return html.escape(str(x))
def fmt(x):return 'N/A' if x is None else f'{x:.3f}'
def table(headers,rows):
    return '<div class="scroll"><table><thead><tr>'+''.join('<th>'+esc(x)+'</th>' for x in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+esc(x)+'</td>' for x in row)+'</tr>' for row in rows)+'</tbody></table></div>'

def main():
    manifest=load(BASE/'corpus_manifest.json');comparison=load(BASE/'calibration_comparison.json');sem=load(BASE/'semantics/results.json')
    joint=load(BASE/'joint/summary.json');temporal=load(BASE/'temporal/summary.json')
    scale_rows=[];model_rows=[];model_data={}
    for name,folder in [('MiniLM','joint'),('BGE small','joint_bge'),('Jina small','joint_jina')]:
        js=load(BASE/folder/'summary.json');m=js['episode_macro'];model_data[name]=js['upw_pair_means']
        scale_rows.append([name,*[fmt(m[k]) for k in ['raw_cosine','shift_null_mean','shift_anchor','shift_percentile']]])
    mini=sem['metrics']['cosine']
    model_rows.append(['MiniLM',fmt(mini['proxy_by_scope']['short_template']['triplet_accuracy']),fmt(mini['proxy_by_scope']['real_paragraph']['triplet_accuracy']),fmt(mini['episode_macro_auc']['same_task']),fmt(mini['episode_macro_auc']['shift_0.5'])])
    for name,folder in [('BGE small','BAAI__bge-small-en-v1.5'),('Jina small','jinaai__jina-embeddings-v2-small-en')]:
        m=load(BASE/'alternatives'/folder/'results.json')
        model_rows.append([name,fmt(m['proxy_by_scope']['short_template']),fmt(m['proxy_by_scope']['real_paragraph']),fmt(m['heldout_episode_macro_auc']['same_task']),fmt(m['heldout_episode_macro_auc']['shift_0.5'])])
    with (BASE/'categories/summary.csv').open(encoding='utf-8') as f:cats=list(csv.DictReader(f))
    cat_rows=[[r['metric'],fmt(float(r['episode_macro_mean'])),f"{float(r['ci_low']):.3f}–{float(r['ci_high']):.3f}",r['episodes']] for r in cats]
    same=sem['calibration']['same_task_pooled']['aligned']['percentile']['mean'];different=sem['calibration']['different_task_pooled']['aligned']['percentile']['mean']
    counts=f"{manifest['records']} annotations · {manifest['episode_groups']} videos · {manifest['segments']} segments · {joint['pairs']} real annotation pairs"
    body=f'''<p class="eyebrow">Offline experiment · 4 October 2026</p><h1>Calibrating annotation agreement</h1>
<p class="lead">Use agreement above an explicit baseline, with separate timing, category, and semantic measurements. Keep raw scores visible. The strongest finding is that baseline choice matters more than swapping these three small embedding models.</p>
<p>{esc(counts)}. No human references or paid API calls. Six unavailable outputs remain in the inventory. The valid corpus contains 78 GPT and four Gemini annotations; most comparisons are between pipeline variants, not independent model families.</p>
<div class="cards"><article><strong>Timing</strong><p>Collapse adjacent exact duplicate content. Report continuous matched IoU and soft boundary similarity; preserve semantic phase distinctions.</p></article><article><strong>Categories</strong><p>Independent progress/failure positive Dice, prevalence, and kappa. Failure-type agreement only on nonempty support. Show absence explicitly.</p></article><article><strong>Semantics</strong><p>Duration-weighted cosine with an exact circular-shift baseline. Use the normalized excess as the main calibration diagnostic; percentile is auxiliary.</p></article></div>
<h2>The proposed semantic calibration</h2>
<p>For two complete annotation timelines, let <code>s = Σ overlap(i,j) × cosine(textᵢ,textⱼ) / N</code>. Every frame contributes once. Split/merge intersections are integrated rather than forced into one-to-one text matching.</p>
<p class="equation">S = (s − μ₀) / (1 − μ₀)</p>
<p><code>μ₀</code> is the mean score over all circular shifts of one annotation timeline. This preserves the descriptions and their durations while changing temporal correspondence. Zero means the shift baseline, one means identical aligned embeddings, and negative values mean below the baseline. It is a measure of time-specific semantic agreement, not a correctness probability. Do not clip negative values. Report N/A when the null has no variation or the denominator vanishes.</p>
{table(['Embedding','Raw cosine','Shift baseline μ₀','Normalized excess S','Shift percentile'],scale_rows)}
<p>These are episode-first means across all 16 videos. Normalize each pair before averaging; the table's normalized mean is not the ratio of its two aggregate means. Raw cosine ranges from 0.738 to 0.917 across models, while normalized excess is 0.270–0.296. This is evidence of reduced scale dependence on this corpus, not proof of universal comparability. Shift percentiles near 0.99 compress useful distinctions.</p>
<p>The null defines the question. A shift null tests temporal specificity. A same-task, different-video null tests similarity beyond shared task vocabulary. An unrelated-task null is much easier: in the separate held-out segment diagnostic, the same aligned pairs average percentile {same:.3f} against same-task controls versus {different:.3f} against different-task controls. Neither control is a factual negative label.</p>
<h2>What we tried</h2>
<p>{temporal['candidates']} temporal candidate/parameter combinations; binary and multilabel agreement families; 16 semantic metrics and blends; three embedding models; empirical percentiles, z scores, paraphrase anchoring and identity anchoring; and 216 composite configurations per embedding (648 total). Temporal sweeps use 574 initial controlled pairs; categories use 1,445 controlled variants. Semantic diagnostics contain {sem['pair_count']:,} directed segment/control pairs and 116 controlled triplets. Pair counts are not independent sample sizes.</p>
<h2>Temporal results</h2>
<p>Splitting each segment into two identical pieces drops raw continuous matched IoU from 1 to 0.340. Exact-content collapse restores 1 and leaves the original corpus unchanged. Collapsing only by progress/failure can erase meaningful action or object transitions, so it is a separate binary-state diagnostic.</p>
<p>A 250 ms displacement yields mean IoU 0.424 for intervals at most one second long, versus 0.889 for intervals longer than three seconds. A universal IoU cutoff therefore cannot represent a universal boundary tolerance.</p>
<p class="equation">T = 2 × max<sub>ordered matching M</sub> Σ<sub>(i,j)∈M</sub> tIoU(i,j) / (n<sub>A</sub> + n<sub>B</sub>)</p>
<p class="equation">B<sub>τ</sub> = 2 × max<sub>ordered matching M</sub> Σ<sub>(i,j)∈M</sub> exp(−|tᵢ − tⱼ|/τ) / (b<sub>A</sub> + b<sub>B</sub>)</p>
<p>Use maximum total kernel weight, not cardinality-first matching for soft kernels. Episode endpoints are excluded. A boundary-free pair carries no positive timing evidence even if a convention assigns it similarity one. In the initial positive-shift sweep, τ=1 s had no episode-average reversals; τ=0.5 s had eight of 16. A further 2,866 signed-shift, jitter, and deletion comparisons found the 1 s scale more stable for negative shifts too, but the scales tied on jitter and deletion. Report 0.5 s and 1 s together as sensitivity scales—not acceptable-error thresholds. See the temporal report's robustness appendix.</p>
<h2>Category results</h2>
<p>For each axis, p and q are positive time fractions and c is their positive intersection fraction. <code>Dice = 2c/(p+q)</code>. With <code>Pₒ = 1−p−q+2c</code> and <code>Pₑ = pq+(1−p)(1−q)</code>, <code>κ = (Pₒ−Pₑ)/(1−Pₑ)</code>. Rescaling Dice against the independent-prevalence null gives exactly κ; these are not independent signals.</p>
<p>Deleting all failures at 1% prevalence leaves accuracy at 0.990 and AC1 at 0.990, whereas Dice and kappa are zero. Removing short failure runs from 16 actual annotations preserves mean frame accuracy 0.952 but gives Dice 0.630 and event retention 0.406. Keep rare events visible.</p>
{table(['Metric','Episode mean','95% episode bootstrap','Eligible videos'],cat_rows)}
<p>Eligibility differs: failure Dice and kappa are undefined in 115/280 pairs; MCC is undefined in 150/280. Always report prevalences, missing/degenerate flags, and support. Failure-type empty/empty agreement must not dominate the result. “Unknown” is a literal type in this experiment; its eventual missing-data semantics require an explicit choice.</p>
<h2>Embedding and text-metric comparison</h2>
{table(['Embedding','Short triplets (36)','Paragraph triplets (80)','Same-task AUC (5 videos)','Half-shift AUC (8 videos)'],model_rows)}
<p>Triplet success means a controlled paraphrase scores above a controlled factual edit; it does not validate the original annotation. AUC here separates aligned pairs from controls, not correct from incorrect descriptions. Model evaluation uses the same frozen inputs. Jina is a plausible challenger, but paired episode-bootstrap intervals for its gains over MiniLM include zero for both hard controls. I would keep MiniLM as the baseline rather than switch on this pilot alone.</p>
<p>MiniLM assigns changed real paragraphs mean cosine 0.909. Long descriptions can dilute a consequential edit. Lexical-only similarity fails many short paraphrases; a keyword negation penalty reduces episode-macro half-shift AUC from 0.794 to 0.721. A hand-built field penalty improves constructed edits, but its lexicon partly encodes the probes. Keep it experimental rather than claiming general semantic calibration.</p>
<h2>Why keep the dimensions separate?</h2>
<p>On 15 common U/P/W videos, the most similar pair changes between U–P and P–W as weights change. For MiniLM, 64 of 216 configurations favor U–P and 152 favor P–W. This is a ranking of agreement between pipelines—not a ranking of annotation quality. Move the weights to inspect the tradeoff.</p>
<div class="controls"><label>Embedding <select id="model"><option>MiniLM</option><option>BGE small</option><option>Jina small</option></select></label><label>Semantic scale <select id="semantic"><option value="shift_anchor">Normalized excess</option><option value="raw_cosine">Raw cosine</option><option value="shift_percentile">Shift percentile</option></select></label></div>
<div class="controls"><label>Timing <input id="wt" type="range" min="1" max="8" value="3"></label><label>Categories <input id="wc" type="range" min="1" max="8" value="3"></label><label>Semantics <input id="ws" type="range" min="1" max="8" value="4"></label></div>
<p id="weights"></p><div id="rank"></div><p class="small">Slider weights are normalized to sum to one. This explorer uses soft boundaries at τ=0.5 s and joint-state agreement to reproduce the original composite stress test; these are illustrative inputs, not a recommended production composite.</p>
<h2>Scope and what remains unresolved</h2>
<p>These experiments support relative agreement calibration without human references. They cannot identify shared hallucinations, establish acceptable physical boundary errors, or learn the cost of missing a brief failure. All 16 videos are development data for this exploration. Episode-held-out checks protect against fitting on sibling outputs, but choosing among many candidates still needs replication on new episodes. Most tasks have too few distinct videos to fit and test task-specific cross-video baselines; the attempted task-conditioned same-task calibration fell back to pooled controls in every test case.</p>
<p>Defaults to carry forward: exact-content collapse for phase timing; continuous IoU plus a soft-boundary scale sweep; independent-axis Dice/kappa with support; and duration-weighted cosine plus the explicit shift-null effect size. Keep a same-task control diagnostic where there is enough data, and track short failures separately. Do not choose a universal acceptance threshold yet.</p>
<h2>Artifacts and reproduction</h2>
<ul><li><a href="corpus_manifest.json">Corpus inventory and provenance</a></li><li><a href="temporal/report.txt">Temporal equations and results, including robustness</a> · <a href="temporal/robustness_validation.csv">Robustness results</a> · <a href="temporal/candidate_validation.csv">Candidate sweep</a></li><li><a href="categories/REPORT.md">Category report</a> · <a href="categories/null_sensitivity.json">Null sensitivity</a></li><li><a href="semantics/REPORT.txt">Semantic report</a> · <a href="semantics/probes.json">Controlled text pairs</a></li><li><a href="calibration_comparison.json">Calibration and paired bootstrap results</a></li><li><a href="joint/pairs.json">All real pair scores</a> · <a href="joint/weight_sweep.json">Composite sweep</a></li><li><a href="run_manifest.json">Script and input hashes</a></li></ul>
<pre>.\\.venv-eval\\Scripts\\python.exe scripts/annotate/experiments/build_similarity_corpus.py
.\\.venv-eval\\Scripts\\python.exe scripts/annotate/experiments/temporal_calibration.py
.\\.venv-eval\\Scripts\\python.exe scripts/annotate/experiments/temporal_calibration.py --robustness
.\\.venv-eval\\Scripts\\python.exe scripts/annotate/experiments/category_calibration.py
.\\.venv-eval\\Scripts\\python.exe scripts/annotate/experiments/category_null_sensitivity.py
.\\.venv-eval\\Scripts\\python.exe scripts/annotate/experiments/semantic_calibration.py
.\\.venv-eval\\Scripts\\python.exe scripts/annotate/experiments/alternative_embeddings.py --model BAAI/bge-small-en-v1.5
.\\.venv-eval\\Scripts\\python.exe scripts/annotate/experiments/alternative_embeddings.py --model jinaai/jina-embeddings-v2-small-en
.\\.venv-eval\\Scripts\\python.exe scripts/annotate/experiments/joint_calibration.py --extra-vectors outputs/similarity_exploration_v1/semantics/corpus_embeddings.json
.\\.venv-eval\\Scripts\\python.exe scripts/annotate/experiments/joint_calibration.py --extra-vectors outputs/similarity_exploration_v1/alternatives/BAAI__bge-small-en-v1.5/embeddings.json --out outputs/similarity_exploration_v1/joint_bge
.\\.venv-eval\\Scripts\\python.exe scripts/annotate/experiments/joint_calibration.py --extra-vectors outputs/similarity_exploration_v1/alternatives/jinaai__jina-embeddings-v2-small-en/embeddings.json --out outputs/similarity_exploration_v1/joint_jina
.\\.venv-eval\\Scripts\\python.exe scripts/annotate/experiments/compare_calibrations.py
.\\.venv-eval\\Scripts\\python.exe scripts/annotate/experiments/render_similarity_report.py</pre>
<h2>Research informing the candidates</h2><p><a href="https://activity-net.org/challenges/2018/tasks/anet_localization.html">ActivityNet's temporal-IoU sweep</a> and <a href="https://aclanthology.org/P13-1167/">Fournier's boundary edit distance</a> informed temporal diagnostics. The exponential kernel tested here is our candidate, not Fournier's published metric. <a href="https://journals.sagepub.com/doi/abs/10.1177/001316446002000104">Cohen's agreement correction</a> motivates the prevalence baseline. <a href="https://arxiv.org/abs/1904.09675">BERTScore</a>, <a href="https://aclanthology.org/2024.findings-emnlp.436/">ALIGN-SIM</a>, and <a href="https://aclanthology.org/2022.blackboxnlp-1.20/">SemAntoNeg</a> informed semantic candidates and stress tests; we did not run BERTScore or ALIGN-SIM. The calculations and recommendations above come from the saved local experiments.</p>'''
    script='''const data=__DATA__; const ids=['model','semantic','wt','wc','ws'];
function render(){const w=['wt','wc','ws'].map(id=>Number(document.getElementById(id).value));const sum=w.reduce((a,b)=>a+b,0);const ww=w.map(x=>x/sum);const model=document.getElementById('model').value;const sem=document.getElementById('semantic').value;document.getElementById('weights').textContent=`Normalized weights: timing ${ww[0].toFixed(2)}, categories ${ww[1].toFixed(2)}, semantics ${ww[2].toFixed(2)}`;const rows=Object.entries(data[model]).map(([pair,r])=>({pair,score:ww[0]*r.boundary_soft_050+ww[1]*r.category_joint+ww[2]*r[sem]})).sort((a,b)=>b.score-a.score);document.getElementById('rank').innerHTML=rows.map(r=>`<div class="barrow"><span>${r.pair[0]}–${r.pair[1]}</span><div class="bar"><i style="width:${Math.max(0,r.score)*100}%"></i></div><b>${r.score.toFixed(3)}</b></div>`).join('');} ids.forEach(id=>document.getElementById(id).addEventListener('input',render));render();'''.replace('__DATA__',json.dumps(model_data).replace('</','<\\/'))
    style='''body{font:16px/1.6 system-ui,sans-serif;color:#172b3a;background:#f5f7f8;margin:0}main{max-width:1080px;margin:auto;padding:48px 28px 80px}h1{font-size:42px;line-height:1.1;letter-spacing:-1px}h2{font-size:24px;margin-top:44px}p{max-width:1000px}.eyebrow{font-size:13px;text-transform:uppercase;letter-spacing:2px;color:#426779}.lead{font-size:21px}.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin:28px 0}.cards article{background:white;border:1px solid #dce4e8;border-radius:12px;padding:20px}.cards strong{color:#006d77;font-size:19px}.cards p{margin-bottom:0}table{border-collapse:collapse;width:100%;font-size:14px;background:#fff}th,td{text-align:left;padding:10px 12px;border-bottom:1px solid #dce4e8}th{background:#e7eff2}td:not(:first-child){font-variant-numeric:tabular-nums}.scroll{overflow:auto}.equation{font:18px/1.7 monospace;background:#e7eff2;padding:16px;border-radius:8px}.controls{display:flex;gap:28px;flex-wrap:wrap;margin:18px 0}.controls label{display:flex;align-items:center;gap:12px}select{font:inherit;padding:6px}input{accent-color:#007f86}.barrow{display:flex;align-items:center;gap:16px;margin:14px 0}.barrow span{width:50px}.bar{height:24px;background:#e0e8eb;flex:1;border-radius:4px;overflow:hidden}.bar i{height:100%;background:#008b90;display:block}.barrow b{width:55px}.small{font-size:13px;color:#4e6573}a{color:#006f91}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#172b3a;color:#eef5f7;padding:20px;font-size:12px;border-radius:8px}code{font-size:.9em} @media(max-width:760px){.cards{grid-template-columns:1fr}h1{font-size:32px}main{padding:24px 16px}}'''
    doc='<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Similarity calibration experiments</title><style>'+style+'</style></head><body><main>'+body+'</main><script>'+script+'</script></body></html>'
    (BASE/'report.html').write_text(doc,encoding='utf-8')
    scripts=sorted((ROOT/'scripts/annotate/experiments').glob('*.py'))
    run={'corpus_sha256':manifest['corpus_sha256'],'script_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in scripts},'paid_api_calls':0,'existing_evaluator_modified':False,'artifact':'report.html'}
    (BASE/'run_manifest.json').write_text(json.dumps(run,indent=2),encoding='utf-8')
    print(BASE/'report.html')

if __name__=='__main__':main()
