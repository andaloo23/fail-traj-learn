"""Compare small local embedding models on the identical frozen semantic probes."""
import argparse
import hashlib
import importlib.metadata
import json
import time
from pathlib import Path
import numpy as np
from fastembed import TextEmbedding

ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'outputs/similarity_exploration_v1'

def load(path):return json.loads(path.read_text(encoding='utf-8'))

def auc(pos,neg):
    if not pos or not neg:return None
    b=np.sort(neg);a=np.array(pos)
    return float(np.mean((np.searchsorted(b,a,'left')+np.searchsorted(b,a,'right'))/(2*len(b))))

def main():
    p=argparse.ArgumentParser();p.add_argument('--model',default='BAAI/bge-small-en-v1.5');args=p.parse_args()
    out=BASE/'alternatives'/args.model.replace('/','__');out.mkdir(parents=True,exist_ok=True)
    entries=load(BASE/'semantics/entries.json');probes=load(BASE/'semantics/probes.json');pairs=load(BASE/'semantics/pairs.json')
    texts=sorted({e['text'] for e in entries}|{p[k] for p in probes for k in ('base','positive','negative')})
    started=time.monotonic()
    cache=out/'embeddings.json'
    vectors=load(cache) if cache.exists() else {}
    missing=[t for t in texts if t not in vectors]
    if missing:
        print('Loading model '+args.model,flush=True)
        model=TextEmbedding(model_name=args.model,cache_dir=str(ROOT/'outputs/evaluation_model_cache'),threads=4)
        tokenizer=model.model.tokenizer;limit=(tokenizer.truncation or {}).get('max_length',512);tokenizer.no_truncation()
        chunks=[];owners=[]
        for text in missing:
            current=[]
            for word in text.split():
                if len(tokenizer.encode(' '.join(current+[word])).ids)>limit:
                    if not current:raise ValueError('single token exceeds model context')
                    chunks.append(' '.join(current));owners.append(text);current=[word]
                else:current.append(word)
            if current:chunks.append(' '.join(current));owners.append(text)
        tokenizer.enable_truncation(max_length=limit)
        totals={};weights={}
        print(f'Embedding {len(missing)} missing texts in {len(chunks)} chunks',flush=True)
        for i,(text,chunk,v) in enumerate(zip(owners,chunks,model.embed(chunks,batch_size=32))):
            weight=len(chunk.split());totals[text]=totals.get(text,0)+v*weight;weights[text]=weights.get(text,0)+weight
            if (i+1)%128==0:print(f'Embedded {i+1}/{len(chunks)} chunks',flush=True)
        vectors.update({t:(v/np.linalg.norm(v)).tolist() for t,v in totals.items()})
        cache.write_text(json.dumps(vectors),encoding='utf-8')
        model_dir=Path(model.model._model_dir)
        manifest={'model':args.model,'texts':len(texts),'chunks':len(chunks),'token_limit':limit,'chunking':'exact token limit, word-count weighted mean, L2 normalization',
                  'fastembed_version':importlib.metadata.version('fastembed'),'onnxruntime_version':importlib.metadata.version('onnxruntime'),
                  'model_files_sha256':{str(f.relative_to(model_dir)):hashlib.sha256(f.read_bytes()).hexdigest() for f in model_dir.rglob('*') if f.is_file()},'paid_api_calls':0}
        (out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    vectors={t:np.array(v) for t,v in vectors.items()}
    dot=lambda a,b:float(vectors[a]@vectors[b])
    probe_results=[]
    for p in probes:
        pos,neg=dot(p['base'],p['positive']),dot(p['base'],p['negative'])
        probe_results.append({k:p[k] for k in ('base','positive','negative','kind','group')}|{'scope':p.get('scope','short_template'),'positive_score':pos,'negative_score':neg,'correct_proxy_order':pos>neg})
    controls={};epcontrols={}
    for pair in pairs:
        if pair['split']!='test':continue
        a,b=entries[pair['i']]['text'],entries[pair['j']]['text'];s=dot(a,b)
        controls.setdefault(pair['kind'],[]).append(s)
        epcontrols.setdefault(pair['episode'],{}).setdefault(pair['kind'],[]).append(s)
    episode_aucs={ep:{k:auc(d['aligned'],v) for k,v in d.items() if k!='aligned'} for ep,d in epcontrols.items() if 'aligned' in d}
    result={'model':args.model,'seconds':time.monotonic()-started,'proxy_triplet_accuracy':float(np.mean([r['correct_proxy_order'] for r in probe_results])),
            'proxy_by_kind':{k:float(np.mean([r['correct_proxy_order'] for r in probe_results if r['kind']==k])) for k in sorted({r['kind'] for r in probe_results})},
            'heldout_control_means':{k:float(np.mean(v)) for k,v in controls.items()},
            'heldout_control_auc':{k:auc(controls['aligned'],v) for k,v in controls.items() if k!='aligned'},
            'heldout_episode_aucs':episode_aucs,
            'heldout_episode_macro_auc':{k:float(np.mean([d[k] for d in episode_aucs.values() if d.get(k) is not None])) for k in controls if k!='aligned'},
            'proxy_by_scope':{k:float(np.mean([r['correct_proxy_order'] for r in probe_results if r['scope']==k])) for k in sorted({r['scope'] for r in probe_results})},
            'input_sha256':{name:hashlib.sha256((BASE/'semantics'/name).read_bytes()).hexdigest() for name in ('entries.json','probes.json','pairs.json')},
            'probe_count':len(probe_results),'probes':probe_results,'interpretation':'Proxy discrimination of alignment or edited text, not correctness. Same frozen probes/control pairs as MiniLM.'}
    (out/'results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('probes','heldout_episode_aucs')},indent=2),flush=True)

if __name__=='__main__':main()
