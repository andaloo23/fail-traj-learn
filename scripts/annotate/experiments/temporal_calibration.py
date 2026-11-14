"""Offline temporal similarity experiment. No reference is treated as human truth.

Run with .venv-eval/Scripts/python.exe scripts/annotate/experiments/temporal_calibration.py
"""
import csv
import hashlib
import itertools
import json
import math
import random
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean, median

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'outputs/similarity_exploration_v1/temporal'


def state(s):
    return (s.get('progress'), s.get('failure'))


def collapse(segs, exact=False):
    out = []
    for s in segs:
        keys=('progress','failure','failure_types','phase','description','failure_reason')
        same=(all(out[-1].get(k)==s.get(k) for k in keys) if exact else state(out[-1])==state(s)) if out else False
        if out and out[-1]['end'] == s['start'] and same:
            out[-1]['end'] = s['end']
        else:
            out.append(dict(s))
    return out


def matching(weights):
    """Maximum-weight ordered one-to-one matching, unlike count-first matching."""
    if not weights or not weights[0]:
        return 0.
    prev = [0.] * (len(weights[0]) + 1)
    for row in weights:
        cur = [0.]
        for j, weight in enumerate(row, 1):
            cur.append(max(prev[j], cur[-1], prev[j-1] + weight))
        prev = cur
    return prev[-1]


def iou(a, b):
    return max(0, min(a['end'], b['end']) - max(a['start'], b['start'])) / max(a['end']-a['start'], b['end']-b['start'], max(a['end'], b['end'])-min(a['start'], b['start']))


def boundary_info(segs, fps):
    return [(a['end']/fps, min(a['end']-a['start'], b['end']-b['start'])/fps)
            for a,b in zip(segs, segs[1:]) if a['end'] == b['start']]


def scores(a, b, fps):
    result = {}
    for mode in ('raw', 'collapsed', 'exact_content_collapsed'):
        aa, bb = (a,b) if mode == 'raw' else (collapse(a,mode=='exact_content_collapsed'), collapse(b,mode=='exact_content_collapsed'))
        mat = [[iou(x,y) for y in bb] for x in aa]
        denom = len(aa)+len(bb)
        result[f'{mode}/segment_soft_iou'] = 2*matching(mat)/denom if denom else 1.
        gated=[[v if state(aa[i])==state(bb[j]) else 0. for j,v in enumerate(row)] for i,row in enumerate(mat)]
        result[f'{mode}/segment_soft_iou_same_state'] = 2*matching(gated)/denom if denom else 1.
        result[f'{mode}/segment_f1_iou_0.5_same_state'] = 2*matching([[float(v>=.5) for v in row] for row in gated])/denom if denom else 1.
        for threshold in (.1,.25,.5,.75,.9):
            result[f'{mode}/segment_f1_iou_{threshold}'] = 2*matching([[float(v>=threshold) for v in row] for row in mat])/denom if denom else 1.
        ba, bc = boundary_info(aa,fps), boundary_info(bb,fps)
        den = len(ba)+len(bc)
        for kind, scales in [('absolute',(.1,.25,.5,1.)), ('relative',(.05,.1,.2,.5)), ('hybrid',(.1,.2))]:
            for scale in scales:
                ratios = []
                for x,dx in ba:
                    row=[]
                    for y,dy in bc:
                        dur = min(dx,dy)
                        tau = scale if kind == 'absolute' else scale*dur if kind == 'relative' else max(.25,scale*dur)
                        row.append(abs(x-y)/max(tau,1e-9))
                    ratios.append(row)
                for kernel in ('hard','linear','exp'):
                    weights = [[float(v<=1+1e-9) if kernel=='hard' else max(0,1-v) if kernel=='linear' else math.exp(-v) for v in row] for row in ratios]
                    result[f'{mode}/boundary_{kernel}_{kind}_{scale}'] = 2*matching(weights)/den if den else 1.
    return result


def shifted(segs, delta, n):
    out=[]
    for s in segs:
        x=dict(s)
        x['start']=max(0,min(n,s['start']+delta))
        x['end']=max(0,min(n,s['end']+delta))
        if x['end']>x['start']:out.append(x)
    return out


def split(segs):
    out=[]
    for s in segs:
        middle=(s['start']+s['end'])//2
        if middle>s['start']:
            out.extend([dict(s,end=middle),dict(s,start=middle)])
        else:out.append(dict(s))
    return out


def auc(pos, neg):
    return mean([float(a>b)+.5*float(a==b) for a in pos for b in neg]) if pos and neg else None


def write_csv(path, rows):
    if not rows:return
    with path.open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def run():
    OUT.mkdir(parents=True,exist_ok=True)
    corpus=json.loads((OUT.parent/'corpus.json').read_text(encoding='utf8'))
    if isinstance(corpus,dict):corpus=corpus.get('records',corpus.get('annotations'))
    assert corpus
    # Structural checks and score algebra checks precede corpus computation.
    for r in corpus:
        assert r['fps']>0
        for s in r['segments']:assert 0<=s['start']<s['end']<=r['n_frames']
        assert all(a['end']<=b['start'] for a,b in zip(r['segments'],r['segments'][1:]))
    toy=[dict(start=0,end=20,progress=True,failure=False),dict(start=20,end=40,progress=False,failure=True)]
    assert all(abs(v-1)<1e-9 for v in scores(toy,toy,20).values())
    assert all(abs(v-1)<1e-9 for k,v in scores(toy,split(toy),20).items() if k.startswith('collapsed/'))
    assert all(abs(v-1)<1e-9 for k,v in scores(toy,split(toy),20).items() if k.startswith('exact_content_collapsed/'))
    rev=scores(shifted(toy,2,40),toy,20);fwd=scores(toy,shifted(toy,2,40),20)
    assert all(abs(rev[k]-v)<1e-9 for k,v in fwd.items())
    byepisode=defaultdict(list)
    for r in corpus:byepisode[r['episode']].append(r)
    pairrows=[]; perturb=[]; durationrows=[]
    for episode, records in byepisode.items():
        for a,b in itertools.combinations(records,2):
            if a['n_frames']!=b['n_frames'] or a['fps']!=b['fps']:continue
            pairrows.append(dict(episode=episode,id_a=a['id'],id_b=b['id'],source_a=a['source'],source_b=b['source'],**scores(a['segments'],b['segments'],a['fps'])))
        for r in records:
            for name,target in [('identity',r['segments']),('duplicate_split',split(r['segments']))]+[(f'shift_{sec:g}s',shifted(r['segments'],round(sec*r['fps']),r['n_frames'])) for sec in (.1,.25,.5,1,2)]:
                perturb.append(dict(episode=episode,id=r['id'],source=r['source'],perturbation=name,**scores(r['segments'],target,r['fps'])))
            for s in r['segments']:
                d=(s['end']-s['start'])/r['fps']
                for shift in (.1,.25,.5,1,2):
                    # Unclipped interval isolates duration sensitivity from edge clipping.
                    v=max(0,d-shift)/(d+shift)
                    durationrows.append(dict(episode=episode,id=r['id'],duration_seconds=d,duration_bin='short_<=1s' if d<=1 else 'medium_1-3s' if d<=3 else 'long_>3s',shift_seconds=shift,iou=v))
    write_csv(OUT/'pairwise.csv',pairrows);write_csv(OUT/'perturbations.csv',perturb);write_csv(OUT/'duration_sensitivity.csv',durationrows)
    metrics=[k for k in perturb[0] if '/' in k]
    # Episode-level averaging prevents prolific sources/episodes dominating evaluation.
    ag=defaultdict(list)
    for row in perturb:ag[(row['episode'],row['perturbation'])].append(row)
    ep=[dict(episode=e,perturbation=p,**{m:mean(x[m] for x in rows) for m in metrics}) for (e,p),rows in ag.items()]
    write_csv(OUT/'episode_perturbations.csv',ep)
    validation=[]
    episodes=sorted(byepisode)
    # Hash split is stable and isolates all annotations from the same episode.
    test={e for e in episodes if int(hashlib.sha256(e.encode()).hexdigest(),16)%3==0}
    if not test or test==set(episodes):test=set(episodes[::3])
    for m in metrics:
        def vals(names,is_test):return [x[m] for x in ep if x['perturbation'] in names and (x['episode'] in test)==is_test]
        trainpos=vals(['shift_0.1s','shift_0.25s'],False);trainneg=vals(['shift_1s','shift_2s'],False)
        testpos=vals(['shift_0.1s','shift_0.25s'],True);testneg=vals(['shift_1s','shift_2s'],True)
        thresholds=sorted(set([0.,1.]+trainpos+trainneg))
        def ba(p,n,t):return .5*(mean(x>=t for x in p)+mean(x<t for x in n))
        t=max(thresholds,key=lambda t:ba(trainpos,trainneg,t))
        loeo=[];loo_thresholds=[]
        for heldout in episodes:
            p=[x[m] for x in ep if x['episode']!=heldout and x['perturbation'] in ['shift_0.1s','shift_0.25s']]
            n=[x[m] for x in ep if x['episode']!=heldout and x['perturbation'] in ['shift_1s','shift_2s']]
            tt=max(sorted(set([0.,1.]+p+n)),key=lambda tt:ba(p,n,tt))
            hp=[x[m] for x in ep if x['episode']==heldout and x['perturbation'] in ['shift_0.1s','shift_0.25s']]
            hn=[x[m] for x in ep if x['episode']==heldout and x['perturbation'] in ['shift_1s','shift_2s']]
            loeo.append(ba(hp,hn,tt));loo_thresholds.append(tt)
        values={p:mean(x[m] for x in ep if x['perturbation']==p) for p in ['identity','duplicate_split','shift_0.1s','shift_0.25s','shift_0.5s','shift_1s','shift_2s']}
        monotonic=sum(any(x>y+1e-9 for x,y in zip([next(x[m] for x in ep if x['episode']==e and x['perturbation']==p) for p in ['shift_2s','shift_1s','shift_0.5s','shift_0.25s','shift_0.1s']], [next(x[m] for x in ep if x['episode']==e and x['perturbation']==p) for p in ['shift_1s','shift_0.5s','shift_0.25s','shift_0.1s','identity']])) for e in episodes)
        validation.append(dict(metric=m,train_threshold=t,train_balanced_accuracy=ba(trainpos,trainneg,t),heldout_balanced_accuracy=ba(testpos,testneg,t),heldout_auc=auc(testpos,testneg),leave_one_episode_out_balanced_accuracy=mean(loeo),loeo_threshold_min=min(loo_thresholds),loeo_threshold_max=max(loo_thresholds),monotonic_violations_episodes=monotonic,**values))
    write_csv(OUT/'candidate_validation.csv',validation)
    grouped=defaultdict(list)
    for row in pairrows:grouped[(row['source_a'],row['source_b'],row['episode'])].append(row)
    source_ep=[dict(source_a=a,source_b=b,episode=e,**{m:mean(x[m] for x in rows) for m in metrics}) for (a,b,e),rows in grouped.items()]
    write_csv(OUT/'source_episode_pairs.csv',source_ep)
    dur=defaultdict(list)
    for row in durationrows:dur[(row['episode'],row['duration_bin'],row['shift_seconds'])].append(row['iou'])
    durgroups=defaultdict(list)
    for (e,b,s),v in dur.items():durgroups[(b,s)].append(mean(v))
    durations=[dict(duration_bin=b,shift_seconds=s,mean_episode_iou=mean(v),episodes=len(v)) for (b,s),v in sorted(durgroups.items())]
    write_csv(OUT/'duration_summary.csv',durations)
    summary=dict(records=len(corpus),episodes=len(episodes),segments=sum(len(r['segments']) for r in corpus),candidates=len(metrics),real_pairs=len(pairrows),perturbation_pairs=len(perturb),train_episodes=[e for e in episodes if e not in test],heldout_episodes=sorted(test),sanity_checks='identity, symmetry, collapsed duplicate-split invariance passed',limitations=['No metric is calibrated to factual correctness or human acceptability.','Mild/severe shift labels are experimental constructs.','Collapsed binary-state boundaries ignore meaningful within-state semantic transitions.','Timeline shifts clip edges and can delete very short intervals.','Relative and hybrid boundary scale uses the minimum of all four adjacent segment durations.'],equations={'segment_soft_iou':'2 * maximum ordered sum(tIoU) / (segment_count_A + segment_count_B)','boundary_score':'2 * maximum ordered sum(kernel(abs(tA-tB)/tau)) / (boundary_count_A + boundary_count_B)','hybrid_tau':'max(0.25 seconds, alpha * min(adjacent durations in both annotations))','kernels':'hard: 1[r<=1]; linear: max(0,1-r); exp: exp(-r)'},sources=['https://activity-net.org/challenges/2018/tasks/anet_localization.html','https://aclanthology.org/P13-1167/'])
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf8')
    print(json.dumps(summary,indent=2))
    print('Top heldout mild/severe discrimination (not correctness):')
    for x in sorted(validation,key=lambda x:x['heldout_auc'],reverse=True)[:12]:print(x['metric'],round(x['heldout_auc'],3),round(x['heldout_balanced_accuracy'],3),'split',round(x['duplicate_split'],3))


def robustness():
    corpus=json.loads((OUT.parent/'corpus.json').read_text(encoding='utf8'))
    if isinstance(corpus,dict):corpus=corpus.get('records',corpus.get('annotations'))
    rows=[]
    for r in corpus:
        original=collapse(r['segments'],exact=True)
        def add(target,family,magnitude,rep,actual_mae=None):
            assert all(s['start']<s['end'] for s in target)
            assert all(a['end']<=b['start'] for a,b in zip(target,target[1:]))
            vals={k.split('/',1)[1]:v for k,v in scores(original,target,r['fps']).items() if k.startswith('exact_content_collapsed/')}
            rows.append(dict(episode=r['episode'],id=r['id'],source=r['source'],family=family,magnitude=magnitude,rep=rep,actual_boundary_mae_seconds=actual_mae,**vals))
        for direction in (-1,1):
            for sec in (.1,.25,.5,1,2):
                add(shifted(original,round(direction*sec*r['fps']),r['n_frames']), 'negative_shift' if direction<0 else 'positive_shift',sec,0)
        # Same independently drawn boundary perturbation directions at all scales.
        # Clamp to the Voronoi cell around each original boundary, preserving order,
        # segment identity, coverage, and >=1-frame interval durations.
        starts=[original[0]['start']]+[s['end'] for s in original]
        for seed in range(5):
            rng=random.Random(int(hashlib.sha256((r['id']+str(seed)).encode()).hexdigest(),16))
            factors=[rng.uniform(-1,1) for _ in starts[1:-1]]
            for sec in (.1,.25,.5,1):
                points=[starts[0]]
                for i,factor in enumerate(factors,1):
                    lower=(starts[i-1]+starts[i])//2+1
                    upper=(starts[i]+starts[i+1])//2
                    points.append(max(lower,min(upper,starts[i]+round(factor*sec*r['fps']))))
                points.append(starts[-1])
                target=[dict(s,start=points[i],end=points[i+1]) for i,s in enumerate(original)]
                errors=[abs(a-b)/r['fps'] for a,b in zip(points[1:-1],starts[1:-1])]
                add(target,'independent_jitter',sec,seed,mean(errors) if errors else 0.)
        for i in range(len(original)-1):
            target=original[:i]+[dict(original[i],end=original[i+1]['end'])]+original[i+2:]
            add(target,'delete_one_boundary',1,i)
    write_csv(OUT/'robustness_raw.csv',rows)
    metrics=[k for k in rows[0] if k.startswith(('segment_','boundary_'))]
    groups=defaultdict(list)
    for x in rows:groups[(x['episode'],x['family'],x['magnitude'])].append(x)
    ep=[dict(episode=e,family=f,magnitude=mag,actual_boundary_mae_seconds=mean(x['actual_boundary_mae_seconds'] for x in rr) if f=='independent_jitter' else None,**{m:mean(x[m] for x in rr) for m in metrics}) for (e,f,mag),rr in groups.items()]
    write_csv(OUT/'robustness_episode.csv',ep)
    summary=[]
    episodes=sorted({r['episode'] for r in corpus})
    for family in ('positive_shift','negative_shift','independent_jitter'):
        grid=[.1,.25,.5,1] if family=='independent_jitter' else [.1,.25,.5,1,2]
        positive=[.1,.25];negative=[.5,1] if family=='independent_jitter' else [1,2]
        for m in metrics:
            rr=[x for x in ep if x['family']==family]
            violations=0
            for e in episodes:
                vals=[next(x[m] for x in rr if x['episode']==e and x['magnitude']==mag) for mag in grid]
                violations+=any(a<b-1e-9 for a,b in zip(vals,vals[1:]))
            bas=[]
            for e in episodes:
                p=[x[m] for x in rr if x['episode']!=e and x['magnitude'] in positive]
                n=[x[m] for x in rr if x['episode']!=e and x['magnitude'] in negative]
                def ba(p,n,t):return .5*(mean(x>=t for x in p)+mean(x<t for x in n))
                t=max(sorted(set([0.,1.]+p+n)),key=lambda t:ba(p,n,t))
                hp=[x[m] for x in rr if x['episode']==e and x['magnitude'] in positive]
                hn=[x[m] for x in rr if x['episode']==e and x['magnitude'] in negative]
                bas.append(ba(hp,hn,t))
            means={str(mag):mean(x[m] for x in rr if x['magnitude']==mag) if mag in grid else None for mag in [.1,.25,.5,1,2]}
            summary.append(dict(family=family,metric=m,loeo_balanced_accuracy=mean(bas),monotonic_violations_episodes=violations,**means))
    write_csv(OUT/'robustness_validation.csv',summary)
    dele=[dict(metric=m,episode_mean=mean(x[m] for x in ep if x['family']=='delete_one_boundary'),episodes=sum(x['family']=='delete_one_boundary' for x in ep)) for m in metrics]
    write_csv(OUT/'robustness_deletion_summary.csv',dele)
    print('Robustness',len(rows),'pairs;',len(episodes),'episodes;',len(metrics),'candidate scores')
    for x in summary:
        if x['metric'] in ['segment_soft_iou','boundary_exp_absolute_0.25','boundary_exp_absolute_0.5','boundary_exp_absolute_1.0']:
            print(x)
    print('Deletion',*[x for x in dele if x['metric'] in ['segment_soft_iou','boundary_exp_absolute_0.5','boundary_exp_absolute_1.0']],sep='\n')


if __name__=='__main__':
    robustness() if '--robustness' in sys.argv else run()
