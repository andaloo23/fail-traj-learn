"""Episode-balanced comparison and bootstrap of explored semantic calibrations."""
import json
from collections import defaultdict
from pathlib import Path
import numpy as np

BASE=Path(__file__).resolve().parents[3]/'outputs/similarity_exploration_v1'
def load(path):return json.loads(path.read_text(encoding='utf-8'))
def auc(a,b):
    if not a or not b:return None
    b=np.sort(b);return float(np.mean((np.searchsorted(b,a,'left')+np.searchsorted(b,a,'right'))/(2*len(b))))
def interval(a,rng):
    a=np.asarray(a);b=rng.choice(a,(5000,len(a)),replace=True).mean(axis=1)
    return {'mean':float(a.mean()),'ci95':[float(x) for x in np.quantile(b,[.025,.975])],'episodes':len(a)}

def main():
    rng=np.random.default_rng(417);data={}
    for name,folder in [('MiniLM','joint'),('BGE small','joint_bge'),('Jina small','joint_jina')]:
        rows=load(BASE/folder/'pairs.json');eps=defaultdict(list)
        for r in rows:eps[r['episode']].append(r)
        data[name]={'summary':load(BASE/folder/'summary.json'),'episode_stats':{k:interval([np.mean([r[k] for r in rr if r[k] is not None]) for rr in eps.values()],rng) for k in ['raw_cosine','shift_null_mean','shift_anchor','shift_percentile']}}
    pairs=load(BASE/'semantics/pairs.json');eps=defaultdict(lambda:defaultdict(list))
    for p in pairs:
        if p['split']=='test':eps[p['episode']][p['kind']].append(p['scores']['cosine'])
    mini={ep:{k:auc(d['aligned'],v) for k,v in d.items() if k!='aligned'} for ep,d in eps.items()}
    differences={}
    for name,folder in [('BGE small','BAAI__bge-small-en-v1.5'),('Jina small','jinaai__jina-embeddings-v2-small-en')]:
        alt=load(BASE/'alternatives'/folder/'results.json')['heldout_episode_aucs']
        differences[name]={k:interval([alt[ep][k]-mini[ep][k] for ep in mini if ep in alt and mini[ep].get(k) is not None and alt[ep].get(k) is not None],rng) for k in ['same_task','shift_0.5','different_task']}
    result={'models':data,'paired_episode_auc_difference_from_minilm':differences,'bootstrap':'5000 paired episode resamples; exploratory intervals on small reused development cohort, no multiple-comparison correction','seed':417}
    (BASE/'calibration_comparison.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({'model_scales':{k:v['episode_stats'] for k,v in data.items()},'auc_differences':differences},indent=2))

if __name__=='__main__':main()
