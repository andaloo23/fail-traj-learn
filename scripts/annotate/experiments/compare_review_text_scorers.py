"""Similarity-only scorer comparison on current review pairs and frozen probes.

No video correctness labels, generated judgments, paid APIs, or model fine-tuning.
"""
import argparse
from collections import Counter
import gc
import hashlib
import html
from importlib.metadata import version
import json
from pathlib import Path
import re
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'outputs/text_scorer_comparison_v1'
VIEW = ROOT / 'outputs/taxonomy_pilot_v1/web_review'
EMBEDDINGS = {
    'mpnet': 'sentence-transformers/all-mpnet-base-v2',
    'paraphrase_mpnet': 'sentence-transformers/paraphrase-mpnet-base-v2',
    'minilm': 'sentence-transformers/all-MiniLM-L6-v2',
    'bge_small': 'BAAI/bge-small-en-v1.5',
}
CROSS = {
    'sts_roberta_large': 'cross-encoder/stsb-roberta-large',
    'sts_distilroberta': 'cross-encoder/stsb-distilroberta-base',
}
CLASSIFIERS = {
    'paws_deberta': 'domenicrosati/deberta-v3-large-finetuned-paws-paraphrase-detector',
    'mrpc_deberta': 'mrm8488/deberta-v3-small-finetuned-mrpc',
}


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def prepare():
    OUT.mkdir(exist_ok=False)
    data = load(VIEW / 'data.json')
    rows = []
    for ep in data['episodes']:
        for run in ('v12_astra', 'v12', 'v12_astra_gemini'):
            annotations = ep['versions'][run]
            for i, a in enumerate(annotations['openai']['segments']):
                for j, b in enumerate(annotations['gemini']['segments']):
                    start, end = max(a['start_frame'], b['start_frame']), min(a['end_frame'], b['end_frame'])
                    if start < end:
                        rows.append(dict(id=f"{ep['id']}_{run}_{i+1}_{j+1}", kind='actual',
                                         episode=ep['id'], run=run, start=start, end=end,
                                         left=a['what_happened'], right=b['what_happened']))
    ep = next(e for e in data['episodes'] if e['id']=='R004')
    old = ep['versions']['v11_astra']
    rows.extend([
        dict(id='R004_old_scope_mismatch', kind='scope', left=old['openai']['segments'][0]['what_happened'], right=old['gemini']['segments'][0]['what_happened']),
        dict(id='R004_old_grouped_scope', kind='scope', left=' '.join(s['what_happened'] for s in old['openai']['segments'][:2]), right=old['gemini']['segments'][0]['what_happened']),
    ])
    # Freeze expectations BEFORE any model scoring. Only relative preferences,
    # not invented absolute semantic percentages or correctness ground truth.
    prefs = []
    specs = []
    for obj, other in [('milk carton','juice carton'), ('butter package','sauce jar'), ('red block','blue block'), ('brown bottle','white cup')]:
        specs.extend([
            ('acquisition', f'The robot grasps the {obj} and lifts it off the table.',
             f'The gripper takes hold of the {obj} and raises it clear of the table.',
             f'The robot fails to grasp the {obj}; it stays on the table.'),
            ('destination', f'The robot places the {obj} inside the basket.',
             f'The robot puts the {obj} into the basket.',
             f'The robot places the {obj} outside the basket.'),
            ('identity', f'The robot lifts the {obj} and carries it toward the basket.',
             f'The robot picks up the {obj} and transports it toward the basket.',
             f'The robot lifts the {other} and carries it toward the basket.'),
            ('order', f'The robot opens the drawer before picking up the {obj}.',
             f'After opening the drawer, the robot picks up the {obj}.',
             f'The robot picks up the {obj} before opening the drawer.'),
        ])
    specs.extend([
        ('polarity', 'The carton stays held by the gripper and is not released.', 'The gripper keeps holding the carton without letting go.', 'The carton is released and is no longer held by the gripper.'),
        ('collision', 'The basket remains stationary while the carton is lowered into it.', 'Lowering the carton into the basket does not move the basket.', 'The basket shifts and rotates while the carton is lowered into it.'),
        ('idle', 'The gripper remains clear and the milk stays in the basket. No further task improvement or independently supported failure is visible.',
         'The robot remains clear of the placed milk. The carton stays in the basket; no further task improvement or independently supported failure occurs.',
         'The robot remains clear of the milk, but the carton falls out of the basket. An independently supported placement failure occurs.'),
        ('scope', 'The robot approaches the carton, grasps it, and carries it to the basket.',
         'The robot moves toward the carton, picks it up, and transports it to the basket.',
         'The robot approaches the carton.'),
    ])
    for i, (family, base, para, changed) in enumerate(specs):
        ids = {}
        for kind, text in [('identical', base), ('paraphrase', para), ('changed', changed), ('unrelated', 'A person types a message on a laptop in another room.')]:
            ident = f'probe_{i}_{kind}'
            rows.append(dict(id=ident, kind=kind, family=family, left=base, right=text))
            ids[kind] = ident
        for lower in ('changed','unrelated'):
            prefs.append(dict(higher=ids['paraphrase'], lower=ids[lower], family=family))
    dump(OUT/'corpus.json', dict(rows=rows, preferences=prefs,
         interpretation='Author-specified similarity ordering probes, not independently human-rated benchmark labels. Changed descriptions can remain topically similar.'))
    print(f'Frozen {len(rows)} pairs, {len(prefs)} ordering checks', flush=True)


def tokens(text):
    return re.findall(r"[a-z0-9]+", text.lower())


def lexical():
    rows = load(OUT/'corpus.json')['rows']
    scores = {name: [] for name in ('token_f1', 'rouge_l', 'tfidf_cosine')}
    for r in rows:
        a,b = tokens(r['left']),tokens(r['right'])
        overlap=sum((Counter(a)&Counter(b)).values())
        scores['token_f1'].append(2*overlap/(len(a)+len(b)))
        prev=[0]*(len(b)+1)
        for x in a:
            cur=[0]
            for j,y in enumerate(b):
                cur.append(prev[j]+1 if x==y else max(prev[j+1],cur[-1]))
            prev=cur
        scores['rouge_l'].append(2*prev[-1]/(len(a)+len(b)))
    from sklearn.feature_extraction.text import TfidfVectorizer
    texts=sorted({r[k] for r in rows for k in ('left','right')})
    v=TfidfVectorizer().fit_transform(texts)
    index={t:i for i,t in enumerate(texts)}
    scores['tfidf_cosine']=[float(v[index[r['left']]].multiply(v[index[r['right']]]).sum()) for r in rows]
    for name,values in scores.items():
        dump(OUT/(name+'.json'), dict(name=name,scores=values,metadata=dict(tokenization='lowercase alphanumeric; punctuation omitted; no stopword removal')))


def revision(model):
    from huggingface_hub import try_to_load_from_cache
    path=try_to_load_from_cache(model,'config.json')
    return Path(path).parent.name if isinstance(path,str) else None


def learned(name):
    rows=load(OUT/'corpus.json')['rows']; pairs=[(r['left'],r['right']) for r in rows]
    started=time.time()
    import torch
    torch.set_num_threads(4)
    from sentence_transformers import SentenceTransformer, CrossEncoder
    if name in EMBEDDINGS:
        ident=EMBEDDINGS[name]
        model=SentenceTransformer(ident,device='cpu')
        texts=sorted({t for pair in pairs for t in pair})
        if any(len(model.tokenizer.encode(t))>model.max_seq_length for t in texts):
            raise ValueError('Text would be truncated')
        vectors=model.encode(texts,normalize_embeddings=True,show_progress_bar=True,batch_size=16)
        index={t:i for i,t in enumerate(texts)}
        values=[float(vectors[index[a]]@vectors[index[b]]) for a,b in pairs]
        meta=dict(model=ident,revision=revision(ident),metric='cosine')
    elif name in CROSS:
        ident=CROSS[name];model=CrossEncoder(ident,device='cpu')
        both=pairs+[(b,a) for a,b in pairs]
        values=model.predict(both,batch_size=8,show_progress_bar=True)
        delta=np.abs(values[:len(pairs)]-values[len(pairs):])
        values=((values[:len(pairs)]+values[len(pairs):])/2).tolist()
        meta=dict(model=ident,revision=revision(ident),metric='mean of both input orders',max_direction_difference=float(delta.max()))
    elif name in CLASSIFIERS:
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        ident=CLASSIFIERS[name]
        tokenizer=AutoTokenizer.from_pretrained(ident)
        model=AutoModelForSequenceClassification.from_pretrained(ident).eval()
        both=pairs+[(b,a) for a,b in pairs]
        probabilities=[]
        for start in range(0,len(both),8):
            batch=both[start:start+8]
            features=tokenizer([a for a,b in batch],[b for a,b in batch],padding=True,truncation=False,return_tensors='pt')
            if features['input_ids'].shape[1]>512:raise ValueError('Pair exceeds classifier context')
            with torch.no_grad():
                probabilities.extend(model(**features).logits.softmax(dim=1)[:,1].tolist())
        v=np.array(probabilities)
        values=((v[:len(pairs)]+v[len(pairs):])/2).tolist()
        meta=dict(model=ident,revision=revision(ident),metric='bidirectional mean paraphrase probability',positive_class=1,
                  id2label=model.config.id2label,max_direction_difference=float(np.abs(v[:len(pairs)]-v[len(pairs):]).max()))
    elif name in ('nli_deberta','nli_tasksource'):
        ident='cross-encoder/nli-deberta-v3-base' if name=='nli_deberta' else 'tasksource/deberta-small-long-nli'
        model=CrossEncoder(ident,device='cpu')
        from transformers import AutoConfig
        config=AutoConfig.from_pretrained(ident)
        if name=='nli_deberta':labels=['contradiction','entailment','neutral']
        else:labels=[config.id2label[i].lower() for i in range(config.num_labels)]
        entailment,contradiction=labels.index('entailment'),labels.index('contradiction')
        values=model.predict(pairs+[(b,a) for a,b in pairs],batch_size=8,show_progress_bar=True,activation_fn=torch.nn.Softmax(dim=1))
        forward,reverse=values[:len(pairs)],values[len(pairs):]
        meta=dict(model=ident,revision=revision(ident),labels=labels,metric='bidirectional mean entailment; contradiction separately',directional_probabilities=values.tolist())
        contra_name='nli_contradiction' if name=='nli_deberta' else 'tasksource_contradiction'
        dump(OUT/(contra_name+'.json'),dict(name=contra_name,scores=((forward[:,contradiction]+reverse[:,contradiction])/2).tolist(),metadata=dict(model=ident,metric='bidirectional mean contradiction; higher means more contradictory')))
        values=((forward[:,entailment]+reverse[:,entailment])/2).tolist()
    elif name=='bertscore':
        from bert_score import BERTScorer
        ident='roberta-large';model=BERTScorer(model_type=ident,lang='en',device='cpu',rescale_with_baseline=True,batch_size=8)
        _,_,rescaled=model.score([a for a,b in pairs],[b for a,b in pairs],verbose=True)
        baseline=float(model.baseline_vals[2])
        raw=(rescaled*(1-baseline)+baseline).tolist()
        meta=dict(model=ident,revision=revision(ident),hash=model.hash,baseline_f1=baseline,idf=False,num_layers=model.num_layers)
        dump(OUT/'bertscore_raw.json',dict(name='bertscore_raw',scores=raw,metadata=meta))
        values=rescaled.tolist()
    else:
        raise ValueError(name)
    if name=='nli_deberta':meta.update(model=ident,revision=revision(ident))
    meta['seconds']=round(time.time()-started,2)
    dump(OUT/(name+'.json'),dict(name=name,scores=values,metadata=meta))
    print(name+': complete',flush=True)
    del model
    gc.collect()


def report():
    corpus=load(OUT/'corpus.json');rows=corpus['rows'];index={r['id']:i for i,r in enumerate(rows)}
    results={}
    for path in OUT.glob('*.json'):
        value=load(path)
        if 'scores' in value:
            assert len(value['scores'])==len(rows)
            assert all(np.isfinite(value['scores']))
            results[value['name']]=value
    summary={}
    for name,value in results.items():
        if name.endswith('contradiction'):continue
        s=value['scores'];prefs=corpus['preferences']
        passed=[s[index[p['higher']]]>s[index[p['lower']]] for p in prefs]
        summary[name]=dict(ordering_passes=sum(passed),ordering_checks=len(prefs),
            changed_passes=sum(ok for p,ok in zip(prefs,passed) if p['lower'].endswith('changed')),
            changed_checks=sum(p['lower'].endswith('changed') for p in prefs),
            by_kind={kind:float(np.mean([s[i] for i,r in enumerate(rows) if r['kind']==kind])) for kind in ('identical','paraphrase','changed','unrelated')},
            failed_preferences=[p for p,ok in zip(prefs,passed) if not ok])
    dump(OUT/'summary.json',summary)
    dump(OUT/'manifest.json',dict(corpus_sha256=hashlib.sha256((OUT/'corpus.json').read_bytes()).hexdigest(),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),packages={p:version(p) for p in ('sentence-transformers','transformers','torch','bert-score','scikit-learn')},paid_api_calls=0))
    names=sorted(results)
    parts=['<!doctype html><meta charset="utf-8"><title>Text scorer comparison</title><style>body{font:14px system-ui;margin:25px;background:#101720;color:#e8edf5}table{border-collapse:collapse}td,th{padding:8px;border:1px solid #46546b;vertical-align:top}td.text{min-width:300px;max-width:450px}th{position:sticky;top:0;background:#253448}a{color:#a6ccff}</style>',
           '<h1>Annotation text similarity scorer comparison</h1><p>Similarity only: no video correctness judgments. Synthetic preference checks are author-defined, not an independent human benchmark. Different score scales are not comparable percentages. NLI entailment/contradiction are relations, not STS scores.</p>',
           '<p>All V12 overlapping pairs, the earlier R004 scope example, and controlled paraphrases, changed event claims, and unrelated descriptions. STS and NLI are evaluated in both directions.</p>',
           '<h2>Controlled ordering checks</h2><table><tr><th>Scorer</th><th>Paraphrase above changed claim</th><th>All checks</th><th>Mean paraphrase</th><th>Mean changed</th><th>Mean unrelated</th></tr>']
    recommendation_path=OUT/'recommendation.json'
    if recommendation_path.exists():
        recommendation=load(recommendation_path)
        parts.insert(3,'<h2>Recommendation</h2><p>'+html.escape(recommendation['recommendation'])+'</p><p>'+html.escape(recommendation['limitations'])+'</p>')
    for name,s in sorted(summary.items()):
        parts.append(f"<tr><td>{name}</td><td>{s['changed_passes']}/{s['changed_checks']}</td><td>{s['ordering_passes']}/{s['ordering_checks']}</td><td>{s['by_kind']['paraphrase']:.3f}</td><td>{s['by_kind']['changed']:.3f}</td><td>{s['by_kind']['unrelated']:.3f}</td></tr>")
    focus=['R004_v12_astra_6_8','R003_v12_astra_1_1','R002_v12_astra_3_3',
           'probe_16_paraphrase','probe_16_changed','probe_3_paraphrase','probe_3_changed',
           'R004_old_scope_mismatch','R004_old_grouped_scope']
    parts.append('</table><h2>Diagnostic examples</h2><p>R004 idle, R003 approach, R002 transport; holding/release paraphrase and reversal; action-order paraphrase and reversal; earlier R004 narrow and grouped descriptions.</p><table><tr><th>Scorer</th>'+''.join('<th>'+html.escape(n)+'</th>' for n in focus)+'</tr>')
    for name in names:
        parts.append('<tr><td>'+name+'</td>'+''.join(f"<td>{results[name]['scores'][index[n]]:.3f}</td>" for n in focus)+'</tr>')
    parts.append('</table><h2>All description pairs</h2><label>Filter pairs <input id="filter" placeholder="R004, probe, or a phrase"></label><table id="pairs"><tr><th>Pair</th><th>Left</th><th>Right</th>'+''.join('<th>'+html.escape(n)+'</th>' for n in names)+'</tr>')
    for i,r in enumerate(rows):
        parts.append('<tr><td>'+html.escape(r['id'])+'</td><td class="text">'+html.escape(r['left'])+'</td><td class="text">'+html.escape(r['right'])+'</td>'+''.join(f"<td>{results[n]['scores'][i]:.3f}</td>" for n in names)+'</tr>')
    parts.append('</table><script>document.getElementById("filter").addEventListener("input",e=>{const q=e.target.value.toLowerCase();for(const row of document.querySelectorAll("#pairs tr:not(:first-child)"))row.hidden=!row.textContent.toLowerCase().includes(q)});</script>')
    parts.append('<h2>Model and scoring provenance</h2>')
    for name,r in results.items():
        model=r['metadata'].get('model')
        link=f'<a href="https://huggingface.co/{html.escape(model)}">Model card</a>' if model else ''
        parts.append('<details><summary>'+html.escape(name)+'</summary>'+link+'<pre>'+html.escape(json.dumps(r['metadata'],indent=2)[:4000])+'</pre></details>')
    (OUT/'index.html').write_text('\n'.join(parts),encoding='utf-8')
    print(json.dumps({n:{k:v for k,v in s.items() if k!='failed_preferences'} for n,s in summary.items()},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['prepare','lexical','report',*EMBEDDINGS,*CROSS,*CLASSIFIERS,'nli_deberta','nli_tasksource','bertscore'])
    args=p.parse_args()
    if args.command in ('prepare','lexical','report'):globals()[args.command]()
    else:learned(args.command)
