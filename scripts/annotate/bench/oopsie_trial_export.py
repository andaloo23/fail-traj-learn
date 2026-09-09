"""Validate/freeze two directly authored conditions and export timestep/chunk review.

Never selects semantic labels. Requires both isolated annotator outputs first.
"""
import csv
import hashlib
import html
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'outputs/oopsie_transfer_v1'
COLORS = dict(progress='#58c998',failure_inducing='#f47f79',recovery='#74b9ff',
              neutral='#a8b0bd',aftermath='#d4a56b',uncertain='#c6a0ef')

def dump(path, value):
    path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')

def write_csv(path, rows):
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def expand(episode,n):
    rows=[]
    for segment in episode['segments']:
        a,b=segment['start'],segment['end_exclusive']
        assert a==len(rows) and a<b<=n,'gap, overlap or invalid interval'
        assert segment['label'] in COLORS
        assert segment['confidence'] in ('high','medium')
        assert segment['reason']
        for f in range(a,b):
            rows.append(dict(id=episode['id'],frame=f,label=segment['label'],
                             confidence=segment['confidence'],phase=segment['phase'],reason=segment['reason'],
                             abstain=segment['label']=='uncertain',training_approved=False,
                             counterfactual_advantage=None))
    assert len(rows)==n
    assert all(0<=e['frame']<n and e['boundary_uncertainty_frames']>=0 for e in episode['events'])
    assert all(0<=f<n for f in episode['inspected_frames'])
    return rows

def main():
    manifest=json.loads((OUT/'private_manifest.json').read_text())
    previous=json.loads((ROOT/'outputs/gpt6_annotations_v1/sample.json').read_text())
    assert not {(e['dataset'],e['episode_index']) for e in manifest}&{(e['dataset'],e['episode_index']) for e in previous}
    data={}; hashes={}; frames={};stats={}
    for condition in ('a','b'):
        path=OUT/f'condition_{condition}.json'
        raw=path.read_bytes();hashes[condition]=hashlib.sha256(raw).hexdigest()
        data[condition]=json.loads(raw)
        assert [e['id'] for e in data[condition]['episodes']]==[e['id'] for e in manifest]
        rows=[]
        for ep,meta in zip(data[condition]['episodes'],manifest,strict=True):
            episode_rows=expand(ep,meta['n_frames']);frames[condition,ep['id']]=episode_rows;rows+=episode_rows
        write_csv(OUT/f'timesteps_{condition}.csv',rows)
        stats[condition]=dict(timesteps=len(rows),label_counts=dict(Counter(r['label'] for r in rows)),
                              uncertain_fraction=sum(r['abstain'] for r in rows)/len(rows),
                              segments=sum(len(e['segments']) for e in data[condition]['episodes']))
    freeze=OUT/'freeze.json'
    if freeze.exists():assert json.loads(freeze.read_text())['sha256']==hashes,'Authored results changed after freeze'
    else:dump(freeze,dict(sha256=hashes,oracle_review_started=False))
    compare=[];chunks=[];human=[]
    for meta in manifest:
        ident=meta['id'];a,b=frames['a',ident],frames['b',ident]
        compare.append(dict(id=ident,n_frames=len(a),different_labels=sum(x['label']!=y['label'] for x,y in zip(a,b)),
                            both_nonuncertain=sum(not x['abstain'] and not y['abstain'] for x,y in zip(a,b)),
                            nonuncertain_disagreements=sum(x['label']!=y['label'] and not x['abstain'] and not y['abstain'] for x,y in zip(a,b))))
        # The collector uses fixed ten-step execution chunks; boundaries verified against source afterward.
        for start in range(0,len(a),10):
            end=min(start+10,len(a))
            for condition in ('a','b'):
                counts=Counter(r['label'] for r in frames[condition,ident][start:end])
                chunks.append(dict(id=ident,condition=condition,chunk=start//10,start=start,end_exclusive=end,
                                   label=next(iter(counts)) if len(counts)==1 else 'mixed',
                                   proportions={k:v/(end-start) for k,v in counts.items()}))
        human.append(dict(id=ident,start_frame='',end_frame_exclusive='',label='',event='',event_frame='',
                          boundary_uncertainty_frames='',reason='',annotator=''))
    dump(OUT/'chunk_mixtures.json',chunks)
    if not (OUT/'human_review.csv').exists():write_csv(OUT/'human_review.csv',human)
    summary=dict(episodes=len(manifest),frames=sum(e['n_frames'] for e in manifest),conditions=stats,
                 comparison=compare,mixed_chunks={c:sum(r['condition']==c and r['label']=='mixed' for r in chunks) for c in ('a','b')},
                 human_review_completed=False,accuracy_measured=False,api_token_usage=None,
                 note='Descriptive condition differences; no oracle or human semantic labels used to score accuracy.')
    dump(OUT/'summary.json',summary)
    parts=['''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Oopsie-compatible timestep annotation trial</title><style>body{font:16px system-ui;background:#101722;color:#eef3f8;max-width:1120px;margin:35px auto;padding:0 20px}a{color:#9bd0ff}article{background:#1a2534;padding:22px;margin:22px 0;border-radius:12px}video{width:100%;max-width:900px}.track{display:flex;height:25px;margin:8px 0}.track button{border:0;min-width:1px;cursor:pointer;padding:0}.live{min-height:65px}td,th{text-align:left;padding:8px;vertical-align:top}table{width:100%;border-collapse:collapse}small{color:#bfccda}</style>
<h1>Oopsie-compatible annotation · timestep trial v1</h1>
<p><a href="oracle_comparison.html">New: Oopsie-compatible versus oracle-informed comparison</a></p>
<p>Four fresh simulated episodes. A: images + task. B: same + measured robot state and gripper commands. Separate annotation contexts; neither receives oracle states, outcomes or the other's judgments.</p>
<p>Intervals are expanded into timestep labels; event boundaries carry uncertainty. These are unvalidated candidate labels. This is an input ablation, not demonstrated real-world transfer.</p>
<p><a href="protocol.md">Protocol</a> · <a href="findings.md">Findings after oracle check</a> · <a href="summary.json">Comparison</a> · <a href="timesteps_a.csv">A timesteps</a> · <a href="timesteps_b.csv">B timesteps</a> · <a href="chunk_mixtures.json">Chunk mixtures</a> · <a href="human_review.html">Independent human review</a> · <a href="freeze.json">Frozen hashes</a></p>''']
    parts.append('<p>'+ ' · '.join(f'<span style="color:{v}">{k}</span>' for k,v in COLORS.items())+'</p>')
    for j,meta in enumerate(manifest):
        ident=meta['id'];visual=json.loads((OUT/'visual'/ident/'metadata.json').read_text())
        parts.append(f'<article><h2>{ident}: {html.escape(visual["task"])}</h2><video id="v{j}" src="visual/{ident}/raw.mp4" controls preload="metadata"></video>')
        for condition in ('a','b'):
            ep=next(e for e in data[condition]['episodes'] if e['id']==ident)
            parts.append(f'<h3>{condition.upper()}: '+('visual only' if condition=='a' else 'visual + robot telemetry')+f'</h3><p>{html.escape(ep["summary"])}</p><div class="track">')
            for s in ep['segments']:
                title=html.escape(f'{s["start"]}–{s["end_exclusive"]-1}: {s["label"]}: {s["reason"]}',quote=True)
                parts.append(f'<button style="flex:{s["end_exclusive"]-s["start"]};background:{COLORS[s["label"]]}" title="{title}" aria-label="{title}" onclick="seek({j},{s["start"]})"></button>')
            parts.append(f'</div><p class="live" id="live{condition}{j}"></p><details><summary>Reasons and boundary uncertainty</summary><table>')
            for s in ep['segments']:
                parts.append(f'<tr><td><button onclick="seek({j},{s["start"]})">{s["start"]}–{s["end_exclusive"]-1}</button></td><td>{s["label"]}<br><small>{s["confidence"]}</small></td><td>{html.escape(s["reason"])}</td></tr>')
            parts.append('</table><pre>'+html.escape(json.dumps(ep['events'],indent=2))+'</pre></details>')
        parts.append('</article>')
    payload=json.dumps(dict(a=data['a']['episodes'],b=data['b']['episodes'],manifest=manifest)).replace('<','\\u003c')
    parts.append('''<script>const d='''+payload+''';function seek(j,f){document.getElementById('v'+j).currentTime=f/d.manifest[j].fps;show(j)}function show(j){const f=Math.min(d.manifest[j].n_frames-1,Math.floor(document.getElementById('v'+j).currentTime*d.manifest[j].fps));for(const c of ['a','b']){const s=d[c][j].segments.find(s=>s.start<=f&&f<s.end_exclusive);if(s)document.getElementById('live'+c+j).textContent=`Frame ${f}: ${s.label} (${s.confidence}) — ${s.reason}`}}d.manifest.forEach((_,j)=>{document.getElementById('v'+j).addEventListener('timeupdate',()=>show(j));show(j)});</script></html>''')
    (OUT/'index.html').write_text('\n'.join(parts),encoding='utf-8')
    blind=['<!doctype html><html><meta charset="utf-8"><title>Independent human temporal review</title><h1>Human temporal review</h1><p>Review without opening the condition comparison first. Enter intervals and events in <a href="human_review.csv">the CSV template</a>. Frame bounds are zero-based, end exclusive. Labels: progress, failure_inducing, recovery, neutral, aftermath, uncertain. Record boundary uncertainty; do not infer precise boundaries from sparse evidence.</p>']
    for meta in manifest:
        ident=meta['id'];info=json.loads((OUT/'visual'/ident/'metadata.json').read_text())
        blind.append(f'<h2>{ident}: {html.escape(info["task"])}</h2><video controls width="768" src="visual/{ident}/raw.mp4"></video><p><a href="telemetry/{ident}/robot.json">Robot telemetry</a></p>')
    (OUT/'human_review.html').write_text('\n'.join(blind)+'</html>',encoding='utf-8')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
