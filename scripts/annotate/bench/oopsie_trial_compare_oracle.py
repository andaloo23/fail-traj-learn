"""Compare frozen observed-input B with independently authored oracle-informed C."""
import csv
import hashlib
import html
import json
from collections import Counter
from pathlib import Path
from oopsie_trial_export import expand, COLORS

OUT=Path(__file__).resolve().parents[3]/'outputs/oopsie_transfer_v1'

def dump(path,obj):path.write_text(json.dumps(obj,indent=2)+'\n',encoding='utf-8')

def main():
    manifest=json.loads((OUT/'private_manifest.json').read_text())
    frozen=json.loads((OUT/'freeze.json').read_text())
    braw=(OUT/'condition_b.json').read_bytes()
    assert hashlib.sha256(braw).hexdigest()==frozen['sha256']['b']
    craw=(OUT/'condition_c.json').read_bytes()
    chash=hashlib.sha256(craw).hexdigest()
    cf=OUT/'freeze_c.json'
    if cf.exists():assert json.loads(cf.read_text())['sha256']==chash
    else:dump(cf,dict(sha256=chash,condition='oracle_informed',comparison_b_sha256=frozen['sha256']['b']))
    b,c=json.loads(braw),json.loads(craw)
    assert [e['id'] for e in b['episodes']]==[e['id'] for e in c['episodes']]==[e['id'] for e in manifest]
    totals=Counter();confusion=Counter();episode_stats=[];diffs=[];crows=[];payload=[]
    for meta,be,ce in zip(manifest,b['episodes'],c['episodes'],strict=True):
        br,cr=expand(be,meta['n_frames']),expand(ce,meta['n_frames']);crows+=cr
        counts=Counter()
        for x,y in zip(br,cr,strict=True):
            counts['frames']+=1
            counts['disagree']+=x['label']!=y['label']
            counts['b_uncertain']+=x['abstain'];counts['c_uncertain']+=y['abstain']
            counts['both_nonuncertain']+=not x['abstain'] and not y['abstain']
            counts['both_nonuncertain_disagree']+=not x['abstain'] and not y['abstain'] and x['label']!=y['label']
            counts['b_progress_c_failure']+=x['label']=='progress' and y['label']=='failure_inducing'
            confusion[x['label'],y['label']]+=1
        totals.update(counts);episode_stats.append(dict(id=meta['id'],**counts))
        boundaries=sorted({s[k] for e in (be,ce) for s in e['segments'] for k in ('start','end_exclusive')})
        intervals=[]
        for start,end in zip(boundaries,boundaries[1:]):
            x,y=br[start],cr[start]
            row=dict(id=meta['id'],start=start,end_exclusive=end,b_label=x['label'],c_label=y['label'],
                     b_reason=x['reason'],c_reason=y['reason'],different=x['label']!=y['label'])
            intervals.append(row)
            if row['different']:diffs.append(row)
        payload.append(dict(id=meta['id'],fps=meta['fps'],n_frames=meta['n_frames'],b=be,c=ce,intervals=intervals))
    summary=dict(comparison='Oopsie-compatible B vs independent oracle-informed C',totals=dict(totals),
                 disagreement_fraction=totals['disagree']/totals['frames'],episodes=episode_stats,
                 confusion=[dict(b_label=k[0],c_label=k[1],timesteps=v) for k,v in sorted(confusion.items())],
                 b_sha256=frozen['sha256']['b'],c_sha256=chash,human_accuracy_measured=False,
                 note='Disagreement with oracle-informed assistant judgments is not a human-validated error rate. B-progress/C-failure is a review candidate metric, not automatically false progress.')
    dump(OUT/'comparison_b_vs_c.json',summary);dump(OUT/'disagreements_b_vs_c.json',diffs)
    with (OUT/'timesteps_c.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(crows[0]));w.writeheader();w.writerows(crows)
    esc=html.escape
    parts=['''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Oopsie-compatible vs oracle-informed annotations</title><style>body{font:16px system-ui;background:#101722;color:#eef3f8;max-width:1120px;margin:32px auto;padding:0 20px}a{color:#9bd0ff}article{background:#1a2534;padding:22px;margin:22px 0;border-radius:12px}video{width:100%;max-width:900px}.track{display:flex;height:26px;margin:8px 0}.track button{border:0;min-width:1px;padding:0;cursor:pointer}.live{min-height:65px}td,th{text-align:left;padding:8px;vertical-align:top;border-bottom:1px solid #415063}table{width:100%;border-collapse:collapse}details{margin:15px 0}.scroll{overflow:auto;max-height:550px}</style>
<h1>Oopsie-compatible vs oracle-informed</h1>
<p>B: task, camera images, measured robot state and gripper commands. C: the same plus privileged object/contact/grasp/goal evidence. C was annotated in a separate context without seeing B. B is unchanged from the earlier trial.</p>
<p>This compares two assistant judgments. Privileged facts improve observability but do not prove every semantic label or counterfactual action value.</p>
<p><a href="oracle_comparison_findings.md">Findings</a> · <a href="comparison_b_vs_c.json">Counts</a> · <a href="disagreements_b_vs_c.json">All differences</a> · <a href="condition_c.json">Oracle-informed judgments</a> · <a href="timesteps_c.csv">C timestep CSV</a> · <a href="human_review.html">Human review</a></p>''']
    parts.append(f'<p><strong>{totals["disagree"]}/{totals["frames"]} differing timestep labels ({summary["disagreement_fraction"]:.1%})</strong>. B-progress/C-failure candidates: {totals["b_progress_c_failure"]} timesteps.</p>')
    parts.append('<p>'+' · '.join(f'<span style="color:{v}">{k}</span>' for k,v in COLORS.items())+'</p>')
    for j,p in enumerate(payload):
        task=json.loads((OUT/'visual'/p['id']/'metadata.json').read_text())['task']
        parts.append(f'<article><h2>{p["id"]}: {esc(task)}</h2><video id="v{j}" controls preload="metadata" src="visual/{p["id"]}/raw.mp4"></video>')
        for key,title in [('b','B: Oopsie-compatible inputs'),('c','C: oracle-informed')]:
            parts.append(f'<h3>{title}</h3><p>{esc(p[key]["summary"])}</p><div class="track">')
            for s in p[key]['segments']:
                label=esc(f'{s["start"]}–{s["end_exclusive"]-1}: {s["label"]}',quote=True)
                parts.append(f'<button style="flex:{s["end_exclusive"]-s["start"]};background:{COLORS[s["label"]]}" title="{label}" aria-label="{label}" onclick="seek({j},{s["start"]})"></button>')
            parts.append(f'</div><p class="live" id="{key}{j}"></p>')
        parts.append('<details><summary>All differing intervals and reasons</summary><div class="scroll"><table><tr><th>Frames</th><th>B</th><th>C</th></tr>')
        for row in p['intervals']:
            if row['different']:
                parts.append(f'<tr><td><button onclick="seek({j},{row["start"]})">{row["start"]}–{row["end_exclusive"]-1}</button></td><td>{row["b_label"]}: {esc(row["b_reason"])}</td><td>{row["c_label"]}: {esc(row["c_reason"])}</td></tr>')
        parts.append('</table></div></details></article>')
    js=json.dumps(payload).replace('<','\\u003c')
    parts.append('''<script>const d='''+js+''';function seek(j,f){document.getElementById('v'+j).currentTime=f/d[j].fps;show(j)}function show(j){const f=Math.min(d[j].n_frames-1,Math.floor(document.getElementById('v'+j).currentTime*d[j].fps));for(const k of ['b','c']){const s=d[j][k].segments.find(s=>s.start<=f&&f<s.end_exclusive);if(s)document.getElementById(k+j).textContent=`Frame ${f} · ${s.label} (${s.confidence}) — ${s.reason}`}}d.forEach((_,j)=>{document.getElementById('v'+j).addEventListener('timeupdate',()=>show(j));show(j)});</script></html>''')
    (OUT/'oracle_comparison.html').write_text('\n'.join(parts),encoding='utf-8')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
