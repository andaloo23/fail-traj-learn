"""Exact circular shift grid sensitivity on the frozen annotation corpus."""
import json
import itertools
from pathlib import Path
from collections import defaultdict
import numpy as np
from category_calibration import arrays


def main():
    root=Path('outputs/similarity_exploration_v1');records=json.loads((root/'corpus.json').read_text())
    groups=defaultdict(list)
    for r in records:groups[r['episode']].append(r)
    rows=[]
    for ep,rs in groups.items():
        for ra,rb in itertools.combinations(rs,2):
            aa,_,ca=arrays(ra);bb,_,cb=arrays(rb);n=min(len(aa),len(bb));valid=ca[:n]&cb[:n]
            if not valid.any():continue
            a,b=aa[:n][valid,1],bb[:n][valid,1];n=len(a);den=int(a.sum()+b.sum())
            if not den:continue
            # Exact all n cyclic shifts, including zero. Counts avoid numerical tie artifacts.
            intersections=np.array([np.sum(a&np.roll(b,i)) for i in range(n)])
            scores=2*intersections/den;obs=float(scores[0]);shifts=np.arange(n)
            for exclusion in [0,.05,.10,.25]:
                mask=(shifts>=int(np.ceil(exclusion*n)))&(shifts<=int(np.floor((1-exclusion)*n)))
                vals=scores[mask];counts=intersections[mask];mu=float(vals.mean());sd=float(vals.std())
                rows.append(dict(episode=ep,id_a=ra['id'],id_b=rb['id'],exclusion=exclusion,n_shifts=len(vals),raw=obs,
                                 null_mean=mu,null_sd=sd,percentile=float(np.mean(counts<intersections[0])+.5*np.mean(counts==intersections[0])),
                                 anchor=(obs-mu)/(1-mu) if 1-mu>1e-10 else None,
                                 null_q05=float(np.quantile(vals,.05)),null_q50=float(np.quantile(vals,.5)),null_q95=float(np.quantile(vals,.95))))
            # Original 39 point grid: compare against exact shifts with same exclusion.
            idx=np.array([int(round(frac*n))%n for frac in np.linspace(.05,.95,39)])
            vals=scores[idx];counts=intersections[idx];mu=float(vals.mean())
            rows.append(dict(episode=ep,id_a=ra['id'],id_b=rb['id'],exclusion='original39',n_shifts=39,raw=obs,
                             null_mean=mu,null_sd=float(vals.std()),percentile=float(np.mean(counts<intersections[0])+.5*np.mean(counts==intersections[0])),
                             anchor=(obs-mu)/(1-mu) if 1-mu>1e-10 else None,
                             null_q05=float(np.quantile(vals,.05)),null_q50=float(np.quantile(vals,.5)),null_q95=float(np.quantile(vals,.95))))
    def emean(rs,key):
        by=defaultdict(list)
        for r in rs:
            if r.get(key) is not None:by[r['episode']].append(r[key])
        return float(np.mean([np.mean(v) for v in by.values()])) if by else None
    summary=[]
    for exclusion in [0,.05,.1,.25,'original39']:
        rs=[r for r in rows if r['exclusion']==exclusion]
        for r in rs:
            r['percentile_ge95']=float(r['percentile']>=.95);r['percentile_eq1']=float(r['percentile']==1)
            r['saturated_weak_effect']=float(r['percentile']>=.95 and r['anchor'] is not None and r['anchor']<.5)
        summary.append(dict(exclusion=exclusion,pairs=len(rs),episodes=len(set(r['episode'] for r in rs)),
                            **{k:emean(rs,k) for k in ['raw','null_mean','null_sd','percentile','anchor','null_q05','null_q50','null_q95','percentile_ge95','percentile_eq1','saturated_weak_effect']}))
    grouped=defaultdict(dict)
    for r in rows:grouped[(r['id_a'],r['id_b'])][r['exclusion']]=r
    sensitivity=[]
    for exclusion in [.05,.1,.25,'original39']:
        diffs=[]
        for v in grouped.values():
            a,b=v[0],v[exclusion]
            diffs.append(dict(episode=a['episode'],percentile_delta=b['percentile']-a['percentile'],percentile_abs_delta=abs(b['percentile']-a['percentile']),anchor_delta=b['anchor']-a['anchor'] if a['anchor'] is not None and b['anchor'] is not None else None))
        sensitivity.append(dict(exclusion=exclusion,**{k:emean(diffs,k) for k in ['percentile_delta','percentile_abs_delta','anchor_delta']}))
    result=dict(summary=summary,sensitivity_vs_all_shifts=sensitivity,rows=rows)
    (root/'categories/null_sensitivity.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(dict(summary=summary,sensitivity_vs_all_shifts=sensitivity),indent=2))


if __name__=='__main__':main()
