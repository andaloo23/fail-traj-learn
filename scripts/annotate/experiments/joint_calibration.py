"""Offline exact shift-null and composite sensitivity; agreement, never accuracy."""
import argparse
import hashlib
import itertools
import json
import math
import sys
from collections import defaultdict, Counter
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/annotate'))
from annotation_metrics import text_for, boundaries

BASE = ROOT / 'outputs/similarity_exploration_v1'

def load(path):
    return json.loads(path.read_text(encoding='utf-8'))

def mean(values):
    vals = [v for v in values if v is not None and math.isfinite(v)]
    return float(np.mean(vals)) if vals else None

def array(record):
    ids = np.empty(record['n_frames'], dtype=int)
    labels = np.empty((record['n_frames'], 2), dtype=bool)
    for i, seg in enumerate(record['segments']):
        ids[seg['start']:seg['end']] = i
        labels[seg['start']:seg['end']] = [seg['progress'], seg['failure']]
    return ids, labels

def soft_boundary(a,b,tau):
    # Maximum TOTAL kernel weight, not cardinality-first threshold matching.
    left = [s['start']/a['fps'] for s in a['segments'][1:]]
    right = [s['start']/b['fps'] for s in b['segments'][1:]]
    if not left and not right:
        return None
    dp=np.zeros((len(left)+1,len(right)+1))
    for i,x in enumerate(left,1):
        for j,y in enumerate(right,1):
            dp[i,j]=max(dp[i-1,j],dp[i,j-1],dp[i-1,j-1]+math.exp(-abs(x-y)/tau))
    return float(2*dp[-1,-1]/(len(left)+len(right)))

def pair(a,b,vectors):
    ia,la=array(a);ib,lb=array(b);n=a['n_frames']
    va=np.array([vectors[text_for(s)] for s in a['segments']]);vb=np.array([vectors[text_for(s)] for s in b['segments']])
    sims=np.clip(va@vb.T,-1,1)
    scores=np.empty(n)
    for shift in range(n):
        scores[shift]=np.mean(sims[ia,np.roll(ib,shift)])
    observed=float(scores[0]);null_mean=float(np.mean(scores));null_sd=float(np.std(scores))
    anchor=None if 1-null_mean<1e-8 or null_sd<1e-8 else (observed-null_mean)/(1-null_mean)
    # A degenerate null is explicitly non-informative, not a perfect percentile.
    percentile=None if null_sd<1e-8 else float(np.mean(scores<observed-1e-8)+.5*np.mean(np.abs(scores-observed)<=1e-8))
    row={'episode':a['episode'],'left':a['id'],'right':b['id'],'left_source':a['source'],'right_source':b['source'],
         'raw_cosine':observed,'shift_null_mean':null_mean,'shift_null_sd':null_sd,
         'shift_excess':observed-null_mean,'shift_anchor':anchor,
         'shift_z':None if null_sd<1e-8 else (observed-null_mean)/null_sd,'shift_percentile':percentile,
         'boundary_soft_025':soft_boundary(a,b,.25),'boundary_soft_050':soft_boundary(a,b,.5),
         'boundary_hard_025':boundaries([s['start'] for s in a['segments'][1:]],[s['start'] for s in b['segments'][1:]],a['fps'],.25)['f1'],
         'category_joint':float(np.mean(np.all(la==lb,axis=1))), 'category_binary_mean':float(np.mean(la==lb))}
    for j,axis in enumerate(('progress','failure')):
        x,y=la[:,j],lb[:,j];den=int(x.sum()+y.sum())
        row[axis+'_dice']=None if not den else float(2*np.sum(x&y)/den)
    row['axis_dice_macro']=mean([row['progress_dice'],row['failure_dice']])
    row['semantic_text_coverage']=1.
    return row

def grouped_means(rows,keys):
    groups=defaultdict(list)
    for r in rows:groups[r['episode']].append(r)
    return {k:mean([mean([r[k] for r in rr]) for rr in groups.values()]) for k in keys}

def main():
    p=argparse.ArgumentParser();p.add_argument('--extra-vectors',type=Path);p.add_argument('--out',type=Path,default=BASE/'joint');args=p.parse_args()
    corpus=load(BASE/'corpus.json');vectors={}
    for path in [ROOT/'outputs/annotation_evaluation_v1/embeddings.json',ROOT/'outputs/h_pipeline_evaluation_v1/evaluation/embeddings.json',args.extra_vectors]:
        if path and path.exists():vectors.update(load(path))
    needed={text_for(s) for r in corpus for s in r['segments']}
    missing=needed-vectors.keys()
    if missing:raise RuntimeError(f'{len(missing)} missing embedding texts; supply --extra-vectors')
    for text in needed:
        v=np.asarray(vectors[text],dtype=float);vectors[text]=(v/np.linalg.norm(v)).tolist()
    groups=defaultdict(list)
    for record in corpus:groups[record['episode']].append(record)
    rows=[pair(a,b,vectors) for records in groups.values() for a,b in itertools.combinations(records,2)]
    # Sanity: duration-weighted circular-shift mean equals dot product of episode means.
    first=corpus[0];identity=pair(first,first,vectors)
    assert abs(identity['raw_cosine']-1)<1e-6
    assert abs(identity['category_joint']-1)<1e-12
    if identity['shift_anchor'] is not None:assert abs(identity['shift_anchor']-1)<1e-5
    aa,bb=groups[rows[0]['episode']][:2];ia,_=array(aa);ib,_=array(bb)
    ma=np.mean(np.asarray([vectors[text_for(s)] for s in aa['segments']])[ia],axis=0)
    mb=np.mean(np.asarray([vectors[text_for(s)] for s in bb['segments']])[ib],axis=0)
    assert abs(float(ma@mb)-rows[0]['shift_null_mean'])<1e-9
    keys=['raw_cosine','shift_null_mean','shift_excess','shift_anchor','shift_z','shift_percentile','boundary_soft_025','boundary_soft_050','boundary_hard_025','category_joint','category_binary_mean','progress_dice','failure_dice']
    summaries=[]
    source_groups=defaultdict(list)
    for row in rows:source_groups[tuple(sorted((row['left_source'],row['right_source'])))].append(row)
    for sources,rr in sorted(source_groups.items()):
        summaries.append({'sources':sources,'episodes':len(rr),**grouped_means(rr,keys)})
    # Weight sensitivity uses only common U/P/W episodes, one triplet per video.
    triplets={}
    for eid,records in groups.items():
        chosen={r['arm']:r for r in records if r['run'] in ('windows','h_windows')}
        if all(k in chosen for k in 'UPW'):
            triplets[eid]={a+b:next(r for r in rows if {r['left'],r['right']}=={chosen[a]['id'],chosen[b]['id']}) for a,b in [('U','P'),('U','W'),('P','W')]}
    meanpairs={ab:{k:mean([rr[ab][k] for rr in triplets.values()]) for k in keys} for ab in ('UP','UW','PW')}
    sweeps=[]
    # All three axes must contribute, each between 0.1 and 0.8, weights sum to 1.
    for i in range(1,9):
        for j in range(1,10-i):
            k=10-i-j
            if k<1:continue
            weights=np.array([i,j,k])/10
            for sem in ('raw_cosine','shift_anchor','shift_percentile'):
                for cat in ('category_joint','category_binary_mean'):
                    scores={ab:float(weights@np.array([r['boundary_soft_050'],r[cat],r[sem]])) for ab,r in meanpairs.items()}
                    order=sorted(scores,key=scores.get,reverse=True)
                    sweeps.append({'weights_timing_category_semantics':weights.tolist(),'semantic':sem,'category':cat,'scores':scores,'order':order})
    out=args.out;out.mkdir(parents=True,exist_ok=True)
    report={'pairs':len(rows),'episode_count':len(groups),'episode_macro':grouped_means(rows,keys),'source_pairs':summaries,
            'common_upw_episodes':sorted(triplets),'upw_pair_means':meanpairs,'weight_configs':len(sweeps),
            'winning_pair_counts':dict(Counter(r['order'][0] for r in sweeps)),
            'ranking_counts':dict(Counter(' > '.join(r['order']) for r in sweeps)),
            'high_raw_low_specificity_examples':sorted([r for r in rows if r['raw_cosine']>.65],key=lambda r:r['shift_excess'])[:12],
            'interpretation':'Shift null retains both descriptions and durations; measures temporal specificity, not factual correctness. Composite winners are strongest agreement pairs, not best pipelines.',
            'sanity_checks':['self identity','analytic exact shift mean identity'],'paid_api_calls':0,
            'corpus_sha256':hashlib.sha256((BASE/'corpus.json').read_bytes()).hexdigest(),
            'extra_vectors_sha256':hashlib.sha256(args.extra_vectors.read_bytes()).hexdigest() if args.extra_vectors else None}
    (out/'pairs.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
    (out/'weight_sweep.json').write_text(json.dumps(sweeps,indent=2),encoding='utf-8')
    (out/'summary.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('source_pairs','high_raw_low_specificity_examples')},indent=2))

if __name__=='__main__':main()
