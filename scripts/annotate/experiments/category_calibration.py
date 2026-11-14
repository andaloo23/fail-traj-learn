"""Offline, symmetric category agreement exploration. No reference is treated as truth."""
import argparse
import csv
import itertools
import json
import math
import re
from collections import defaultdict
from pathlib import Path
import numpy as np


def div(a, b):
    return float(a / b) if b else None


def binary(a, b):
    tp = int(np.sum(a & b)); tn = int(np.sum(~a & ~b))
    fp = int(np.sum(a & ~b)); fn = int(np.sum(~a & b)); n = len(a)
    acc = (tp + tn) / n
    pa, pb = float(a.mean()), float(b.mean())
    pe = pa * pb + (1-pa) * (1-pb)
    p = (pa+pb)/2; ac1_pe = 2*p*(1-p)
    pos = div(2*tp, 2*tp+fp+fn); neg = div(2*tn, 2*tn+fp+fn)
    return dict(accuracy=acc, positive_dice=pos, positive_iou=div(tp,tp+fp+fn),
                macro_dice=(pos+neg)/2 if pos is not None and neg is not None else None,
                kappa=div(acc-pe,1-pe), mcc=div(tp*tn-fp*fn, math.sqrt((tp+fp)*(tp+fn)*(tn+fp)*(tn+fn))),
                ac1=div(acc-ac1_pe,1-ac1_pe), prevalence_a=pa,prevalence_b=pb,
                tp=tp,tn=tn,fp=fp,fn=fn)


def arrays(r):
    n = r['n_frames']; a = np.full((n,2),False); covered=np.zeros(n,bool)
    types=np.zeros((n,7),bool)
    labels=['missed_target','lost_control','wrong_action','collision','timeout','other','unknown']
    for s in r['segments']:
        lo,hi=int(s['start']),int(s['end'])
        a[lo:hi]=[bool(s['progress']),bool(s['failure'])]; covered[lo:hi]=True
        val=s.get('failure_types',''); val=' '.join(val) if isinstance(val,list) else str(val)
        for j,label in enumerate(labels):
            if re.search(r'\b'+label+r'\b',val):types[lo:hi,j]=True
    return a,types,covered


def metrics(a,b,ta=None,tb=None):
    out={}
    for j,axis in enumerate(['progress','failure']):
        out.update({axis+'_'+k:v for k,v in binary(a[:,j],b[:,j]).items()})
    sa=a[:,0]*2+a[:,1]; sb=b[:,0]*2+b[:,1]
    acc=float(np.mean(sa==sb)); pe=sum(float(np.mean(sa==k)*np.mean(sb==k)) for k in range(4))
    out.update(joint_accuracy=acc,joint_kappa=div(acc-pe,1-pe),axis_accuracy=float(np.mean(a==b)))
    if ta is not None:
        union=np.sum(ta|tb,axis=1); inter=np.sum(ta&tb,axis=1); eligible=union>0
        out['types_jaccard_nonempty']=float(np.mean(inter[eligible]/union[eligible])) if eligible.any() else None
        out['types_nonempty_fraction']=float(eligible.mean())
        out['types_exact_all_frames']=float(np.mean(np.all(ta==tb,axis=1)))
        pertype=[binary(ta[:,j],tb[:,j])['positive_dice'] for j in range(ta.shape[1])]
        defined=[v for v in pertype if v is not None]
        out['types_macro_positive_dice']=float(np.mean(defined)) if defined else None
        out['types_eligible_count']=len(defined)
        out['types_micro_positive_dice']=div(2*np.sum(ta&tb),np.sum(ta)+np.sum(tb))
    return out


def write_csv(path,rows):
    keys=list(dict.fromkeys(k for r in rows for k in r))
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)


def main():
    p=argparse.ArgumentParser();p.add_argument('--corpus',default='outputs/similarity_exploration_v1/corpus.json');p.add_argument('--out',default='outputs/similarity_exploration_v1/categories'); args=p.parse_args()
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
    records=json.loads(Path(args.corpus).read_text(encoding='utf-8')); records=records.get('records',[]) if isinstance(records,dict) else records
    rng=np.random.default_rng(20261004);groups=defaultdict(list); pairrows=[]; perturb=[]
    cached={r['id']:arrays(r) for r in records}
    for r in records:groups[r['episode']].append(r)
    nullkeys=['failure_positive_dice','failure_kappa','failure_mcc','failure_ac1','progress_positive_dice','joint_accuracy']
    for episode,rs in groups.items():
        for ra,rb in itertools.combinations(rs,2):
            aa,ta,ca=cached[ra['id']];bb,tb,cb=cached[rb['id']]
            n=min(len(aa),len(bb));valid=ca[:n]&cb[:n]
            if not valid.any():continue
            a,b=aa[:n][valid],bb[:n][valid]
            row=dict(episode=episode,source_a=ra['source'],source_b=rb['source'],id_a=ra['id'],id_b=rb['id'],n_frames=len(a),coverage=float(valid.mean()),**metrics(a,b,ta[:n][valid],tb[:n][valid]))
            # Preserve each timeline's prevalence and run structure, vary phase alignment.
            null=[metrics(a,np.roll(b,int(round(frac*len(b))),axis=0)) for frac in np.linspace(.05,.95,39)]
            for k in nullkeys:
                vals=[v[k] for v in null if v[k] is not None]
                if vals and row[k] is not None:
                    mu=float(np.mean(vals));row[k+'_null_mean']=mu
                    row[k+'_null_percentile']=float(np.mean(np.array(vals)<row[k])+.5*np.mean(np.array(vals)==row[k]))
                    row[k+'_null_rescaled']=div(row[k]-mu,1-mu) if 1-mu>1e-8 else None
                    sd=float(np.std(vals));row[k+'_null_sd']=sd
                    row[k+'_null_z']=div(row[k]-mu,sd) if sd>1e-8 else None
            pairrows.append(row)
    for r in records:
        a,ta,c=cached[r['id']]
        if not c.all():continue
        n=len(a)
        for frac in [0,.01,.025,.05,.1,.2,.4]:
            # Nested flips: same randomized order for monotonic perturbation severity.
            order=np.random.default_rng(77).permutation(n)
            for j,axis in enumerate(['progress','failure']):
                b=a.copy();b[order[:int(round(frac*n))],j]^=True
                perturb.append(dict(episode=r['episode'],id=r['id'],kind=axis+'_random_flip',parameter=frac,**metrics(a,b)))
        f=a[:,1]; edges=np.diff(np.r_[False,f,False].astype(int));runs=list(zip(np.where(edges==1)[0],np.where(edges==-1)[0]))
        if runs:
            lo,hi=min(runs,key=lambda x:x[1]-x[0]);b=a.copy();b[lo:hi,1]=False
            perturb.append(dict(episode=r['episode'],id=r['id'],kind='omit_shortest_failure',parameter=(hi-lo)/n,omitted_seconds=(hi-lo)/r['fps'],failure_events=len(runs),event_retention=(len(runs)-1)/len(runs),**metrics(a,b)))
        for kind in ['all_no_failure','all_failure','invert_failure']:
            b=a.copy();b[:,1]=(~f if kind=='invert_failure' else kind=='all_failure')
            perturb.append(dict(episode=r['episode'],id=r['id'],kind=kind,parameter=1,**metrics(a,b)))
    write_csv(out/'pairwise.csv',pairrows);write_csv(out/'perturbations.csv',perturb)
    # Macro by episode, then bootstrap episodes. Repeated model pairs are not independent.
    summaries=[]
    for key in nullkeys+['failure_accuracy','failure_macro_dice','joint_kappa','types_jaccard_nonempty','types_exact_all_frames','types_macro_positive_dice','types_micro_positive_dice']:
        vals=[]
        for ep in groups:
            v=[row[key] for row in pairrows if row['episode']==ep and row.get(key) is not None]
            if v:vals.append(np.mean(v))
        if vals:
            boot=rng.choice(vals,(2000,len(vals)),replace=True).mean(axis=1)
            summaries.append(dict(metric=key,episode_macro_mean=float(np.mean(vals)),ci_low=float(np.quantile(boot,.025)),ci_high=float(np.quantile(boot,.975)),episodes=len(vals)))
    write_csv(out/'summary.csv',summaries)
    synth=[]
    for prevalence in [.001,.01,.05,.1,.25,.5,.9]:
        a=np.zeros(10000,bool);a[:int(prevalence*len(a))]=True;b=np.zeros_like(a)
        synth.append(dict(prevalence=prevalence,kind='miss_all_positives',**binary(a,b)))
    write_csv(out/'prevalence_stress.csv',synth)
    print(json.dumps(dict(records=len(records),episodes=len(groups),pairs=len(pairrows),perturbations=len(perturb),out=str(out)),indent=2))


if __name__=='__main__':main()
