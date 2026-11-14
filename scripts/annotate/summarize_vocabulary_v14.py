"""Describe vocabulary ablation differences without treating higher agreement as success."""
import html
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[2]
VIEW = ROOT / 'outputs/taxonomy_pilot_v1/web_review'
OUT = ROOT / 'outputs/taxonomy_vocabulary_v14'


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def stats(annotation):
    segments = annotation['segments']
    texts = [s['what_happened'] for s in segments]
    pattern = r'\b(?:approach\w*|acqui\w*|transport\w*|position\w*|plac\w*|releas\w*|reposition\w*|recover\w*|idl\w*)\b'
    return dict(segments=len(segments),
                segments_with_preferred_term=sum(bool(re.search(pattern,t,re.I)) for t in texts),
                words=sum(len(re.findall(r'\b\w+\b',t)) for t in texts))


def compare(a,b,n,scores):
    agreement, text = 0,0.0
    for x in a['segments']:
        for y in b['segments']:
            overlap=max(0,min(x['end_frame'],y['end_frame'])-max(x['start_frame'],y['start_frame']))
            if not overlap:continue
            if x['progress']==y['progress'] and x['failure']==y['failure'] and set(x['categories'])==set(y['categories']):
                agreement+=overlap
            text+=overlap*scores[x['what_happened'],y['what_happened']]
    return dict(frame_agreement=agreement/n,text_similarity=text/n)


def main():
    data=load(VIEW/'data.json');score_data=load(VIEW/'text_similarity.json')
    assert score_data['model']=='cross-encoder/stsb-distilroberta-base'
    scores={(p['left'],p['right']):p['score'] for p in score_data['pairs']}
    model_rows=[];pair_rows=[]
    for ep in data['episodes']:
        n=ep['n_frames']
        for model,run,provider in [('sol','','openai'),('astra','_astra','gemini'),('gemini','','gemini')]:
            old=ep['versions']['v13'+run][provider];new=ep['versions']['v14'+run][provider]
            if old is None or new is None:raise ValueError('Missing displayed annotation')
            model_rows.append(dict(episode=ep['id'],model=model,before=stats(old),after=stats(new),
                                   before_after=compare(old,new,n,scores)))
        for label,suffix in [('Sol / Astra','_astra'),('Sol / Gemini',''),('Astra / Gemini','_astra_gemini')]:
            old=ep['versions']['v13'+suffix];new=ep['versions']['v14'+suffix]
            pair_rows.append(dict(episode=ep['id'],pair=label,
                                  before=compare(old['openai'],old['gemini'],n,scores),
                                  after=compare(new['openai'],new['gemini'],n,scores)))
    result=dict(models=model_rows,pairs=pair_rows,text_scorer=score_data['model'],
                limitation='One sample per model/episode/condition. Prompt effects and generation variability are not separated. Higher lexical or text agreement alone does not establish better semantic comparability.')
    (OUT/'comparison.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    parts=['<!doctype html><meta charset="utf-8"><title>Vocabulary guidance comparison</title><style>body{font:15px system-ui;background:#101720;color:#e8edf5;margin:25px}table{border-collapse:collapse}td,th{padding:9px;border:1px solid #46546b}a{color:#a6ccff}</style>',
           '<h1>V14 vocabulary guidance versus V13</h1><p>'+html.escape(result['limitation'])+'</p>',
           '<p>Same images, telemetry, models, generation settings, and schema. V14 expands participant vocabulary and adds adjacent-segment merging guidance. Preferred-term counts measure lexical compliance, not preserved meaning. Text scores use the same symmetric STS DistilRoBERTa scorer throughout.</p>',
           '<h2>Each model before / after</h2><table><tr><th>Episode</th><th>Model</th><th>Segments V13 / V14</th><th>Segments with preferred term V13 / V14</th><th>Words V13 / V14</th><th>Frame agreement</th><th>Text similarity</th></tr>']
    for r in model_rows:
        a,b=r['before'],r['after'];c=r['before_after']
        link='../?run=v14_before_after_'+r['model']+'&episode='+r['episode']
        parts.append(f'<tr><td>{r["episode"]}</td><td><a href="{link}">{r["model"]}</a></td><td>{a["segments"]} / {b["segments"]}</td><td>{a["segments_with_preferred_term"]} / {b["segments_with_preferred_term"]}</td><td>{a["words"]} / {b["words"]}</td><td>{c["frame_agreement"]:.1%}</td><td>{c["text_similarity"]:.3f}</td></tr>')
    parts.append('</table><h2>Between-model agreement</h2><table><tr><th>Episode</th><th>Pair</th><th>Frame agreement V13 / V14</th><th>Text similarity V13 / V14</th></tr>')
    for r in pair_rows:
        a,b=r['before'],r['after']
        parts.append(f'<tr><td>{r["episode"]}</td><td>{r["pair"]}</td><td>{a["frame_agreement"]:.1%} / {b["frame_agreement"]:.1%}</td><td>{a["text_similarity"]:.3f} / {b["text_similarity"]:.3f}</td></tr>')
    parts.append('</table>')
    (OUT/'comparison.html').write_text('\n'.join(parts),encoding='utf-8')
    destination=VIEW/'vocabulary_v14_comparison';destination.mkdir(exist_ok=True)
    shutil.copyfile(OUT/'comparison.html',destination/'index.html')
    shutil.copyfile(OUT/'comparison.json',destination/'comparison.json')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
