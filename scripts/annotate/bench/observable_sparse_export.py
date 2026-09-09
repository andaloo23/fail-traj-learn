"""Export authored sparse observations. Missing labels remain missing, never neutral."""
import csv
import hashlib
import html
import json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'outputs/observable_sparse_v1'
COLORS={'progress':'#58c998','failure_inducing':'#f47f79'}

def write_csv(path,rows):
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def main():
    raw=(OUT/'authored.json').read_bytes();data=json.loads(raw);digest=hashlib.sha256(raw).hexdigest()
    allrows=[];payload=[];counts=[]
    for e in data['episodes']:
        meta=json.loads((OUT/'visual'/e['id']/'metadata.json').read_text());n=meta['n_frames']
        rows=[dict(id=e['id'],frame=f,label=None,event=None,reason=None,annotation_selected=False,
                   training_approved=False,counterfactual_advantage=None) for f in range(n)]
        previous=0
        for s in e['segments']:
            assert previous<=s['start']<s['end_exclusive']<=n
            assert s['label'] in COLORS and s['confidence']=='high'
            assert set(s['evidence_frames'])<=set(e['inspected_frames'])
            previous=s['end_exclusive']
            for f in range(s['start'],s['end_exclusive']):
                rows[f].update(label=s['label'],event=s['event'],reason=s['reason'],annotation_selected=True)
        selected=sum(r['annotation_selected'] for r in rows)
        counts.append(dict(id=e['id'],frames=n,labelled=selected,unlabelled=n-selected,segments=len(e['segments'])))
        allrows+=rows;payload.append({**e,**meta})
    selected=[r for r in allrows if r['annotation_selected']]
    write_csv(OUT/'labelled_timesteps.csv',selected);write_csv(OUT/'timestep_mask.csv',allrows)
    summary=dict(version=data['version'],episodes=counts,total_frames=len(allrows),labelled_frames=len(selected),
                 unlabelled_frames=len(allrows)-len(selected),coverage=len(selected)/len(allrows),
                 label_counts=dict(Counter(r['label'] for r in selected)),authored_sha256=digest,
                 oracle_inputs_used=False,episode_outcomes_used=False,actual_oopsiedata_test=False,
                 training_approved=False,accuracy_measured=False)
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    pieces=['''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Observable-only sparse annotations</title><style>body{font:16px system-ui;background:#101722;color:#eef3f8;max-width:1100px;margin:35px auto;padding:0 20px}a{color:#9bd0ff}article{background:#1a2534;padding:22px;margin:22px 0;border-radius:12px}video{width:100%;max-width:900px}.track{height:28px;position:relative;background:#303744;margin:14px 0}.track button{position:absolute;height:28px;border:0;cursor:pointer;padding:0}.live{min-height:70px}td,th{text-align:left;padding:9px;vertical-align:top}table{border-collapse:collapse;width:100%}button{cursor:pointer}</style>
<h1>Observable-only sparse annotations · v1</h1>
<p>Fresh simulated episodes. Inputs: task, paired cameras, measured robot pose/finger positions and gripper commands. No privileged object states, contact/grasp flags, goal predicates or episode outcomes.</p>
<p>Only clear, task-relevant intervals are retained. Dark timeline regions are <strong>unlabelled</strong>, not neutral or negative. Boundary cores are conservative; no complete event coverage or exact physical onset is claimed.</p>
<p><a href="README.md">Protocol</a> · <a href="authored.json">Authored observations</a> · <a href="labelled_timesteps.csv">Labelled timesteps only</a> · <a href="timestep_mask.csv">Full timeline with selection mask</a> · <a href="summary.json">Coverage</a></p>''']
    if (OUT/'oracle_check/findings.md').exists():
        pieces.append('<p><a href="oracle_check/findings.md">Subsequent oracle check of frozen labels</a></p>')
    pieces.append(f'<p><strong>{len(selected)} / {len(allrows)} timesteps retained ({summary["coverage"]:.1%})</strong>; {len(allrows)-len(selected)} left unlabelled. Green: observed progress. Red: failed pickup.</p>')
    for j,e in enumerate(payload):
        pieces.append(f'<article><h2>{e["id"]}: {html.escape(e["task"])}</h2><p>{html.escape(e["summary"])}</p><video id="v{j}" controls preload="metadata" src="visual/{e["id"]}/raw.mp4"></video><div class="track">')
        for s in e['segments']:
            title=html.escape(f'{s["start"]}–{s["end_exclusive"]-1}: {s["event"]}',quote=True)
            pieces.append(f'<button style="left:{100*s["start"]/e["n_frames"]}%;width:{100*(s["end_exclusive"]-s["start"])/e["n_frames"]}%;background:{COLORS[s["label"]]}" title="{title}" aria-label="{title}" onclick="seek({j},{s["start"]})"></button>')
        pieces.append(f'</div><p class="live" id="l{j}"></p><table><tr><th>Frames</th><th>Observation</th><th>Evidence</th></tr>')
        for s in e['segments']:
            pieces.append(f'<tr><td><button onclick="seek({j},{s["start"]})">{s["start"]}–{s["end_exclusive"]-1}</button></td><td>{s["event"]}<br>{s["label"]}</td><td>{html.escape(s["reason"])}</td></tr>')
        pieces.append('</table></article>')
    js=json.dumps(payload).replace('<','\\u003c')
    pieces.append('''<script>const d='''+js+''';function seek(j,f){document.getElementById('v'+j).currentTime=f/d[j].fps;show(j)}function show(j){const f=Math.min(d[j].n_frames-1,Math.floor(document.getElementById('v'+j).currentTime*d[j].fps));const s=d[j].segments.find(s=>s.start<=f&&f<s.end_exclusive);document.getElementById('l'+j).textContent=s?`Frame ${f} · ${s.event} · ${s.label} — ${s.reason}`:`Frame ${f} — no annotation`; }d.forEach((_,j)=>{document.getElementById('v'+j).addEventListener('timeupdate',()=>show(j));show(j)});</script></html>''')
    (OUT/'index.html').write_text('\n'.join(pieces),encoding='utf-8')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
