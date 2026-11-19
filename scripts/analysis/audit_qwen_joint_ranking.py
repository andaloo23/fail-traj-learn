"""Inspect joint/evidence-aux ranking sensitivity using saved scores only."""
from collections import Counter
import json
from pathlib import Path

import numpy as np

REPO=Path(__file__).resolve().parents[2]
RUN=REPO/'outputs/oopsie_distillation_local_sequential_v1'
OUT=REPO/'outputs/qwen_joint_ranking_audit_20261113_v1'


def f1(c):
    tp,fp,fn,tn=c
    return 2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None


def main():
    scores={tag:json.loads((RUN/'arm_scores'/f'{tag}.json').read_text()) for tag in ['joint','evidence_aux','binary','categories_aux']}
    rows={tag:{r['episode']:r for r in score['per_episode']} for tag,score in scores.items()}
    ids=sorted(rows['joint']);assert all(ids==sorted(r) for r in rows.values()) and len(ids)==50
    study=json.loads((REPO/'outputs/oopsie_distillation_full_v1/study.json').read_text())
    source=REPO/study['config']['source_run']
    manifest=json.loads((source/'manifest.json').read_text())
    episodes={e['id']:e for e in manifest['episodes']}
    arrays={tag:np.array([[rows[tag][eid]['metrics'][k] for k in ['tp','fp','fn','tn']] for eid in ids],dtype=np.int64) for tag in rows}
    assert all(int(a.sum())==8132 for a in arrays.values())
    positives=np.array([rows['joint'][eid]['metrics']['tp']+rows['joint'][eid]['metrics']['fn']>0 for eid in ids])
    fps=np.array([episodes[eid]['fps'] for eid in ids]);lengths=arrays['joint'].sum(1)
    masks={'all':np.ones(50,dtype=bool),'teacher_failure_episodes':positives,
        'excluding_two_1000_frame_episodes':lengths<1000}
    masks.update({lab:np.array([episodes[eid]['lab']==lab for eid in ids]) for lab in sorted({episodes[eid]['lab'] for eid in ids})})
    groups={}
    for name,mask in masks.items():
        data={}
        for tag,arr in arrays.items():
            a=arr[mask].astype(float);frames=a.sum(1)
            pooled=a.sum(0);per=[f1(c) for c in a]
            counts=dict(predicted_failure_frames=int(pooled[0]+pooled[1]),reference_failure_frames=int(pooled[0]+pooled[2]),
                pooled_frame_f1=f1(pooled),pooled_frame_agreement=float((pooled[0]+pooled[3])/pooled.sum()),
                seconds_weighted_f1=f1((a/fps[mask,None]).sum(0)),equal_episode_pooled_f1=f1((a/frames[:,None]).sum(0)),
                mean_episode_agreement=float(np.mean((a[:,0]+a[:,3])/frames)),
                mean_defined_episode_f1=float(np.mean([v for v in per if v is not None])) if any(v is not None for v in per) else None,
                episodes_with_defined_f1=sum(v is not None for v in per))
            data[tag]=counts
        groups[name]=dict(episodes=int(mask.sum()),frames=int(lengths[mask].sum()),models=data)
    wins=Counter();details=[]
    for i,eid in enumerate(ids):
        a,b=f1(arrays['joint'][i]),f1(arrays['evidence_aux'][i])
        if positives[i]:wins['joint_failure_f1_wins' if a>b else 'evidence_failure_f1_wins' if b>a else 'failure_f1_ties']+=1
        x,y=(arrays[tag][i] for tag in ['joint','evidence_aux'])
        ja=(x[0]+x[3])/x.sum();ea=(y[0]+y[3])/y.sum()
        wins['joint_agreement_wins' if ja>ea else 'evidence_agreement_wins' if ea>ja else 'agreement_ties']+=1
        details.append(dict(episode=eid,lab=episodes[eid]['lab'],frames=int(lengths[i]),reference_has_failure=bool(positives[i]),
            joint_f1=a,evidence_aux_f1=b,joint_agreement=float(ja),evidence_aux_agreement=float(ea),
            joint_tp=int(x[0]),evidence_aux_tp=int(y[0])))
    rng=np.random.default_rng(20261113);draws=rng.integers(0,50,(5000,50));distributions={}
    for tag,arr in arrays.items():
        c=arr[draws].sum(1);d=2*c[:,0]+c[:,1]+c[:,2]
        distributions[tag]=np.divide(2*c[:,0],d,out=np.full(len(d),np.nan),where=d!=0)
    diff=distributions['evidence_aux']-distributions['joint']
    result=dict(teacher_positive_episodes=int(positives.sum()),total_episodes=50,groups=groups,
        wins=dict(wins),per_episode=details,
        paired_bootstrap_evidence_minus_joint_f1_95=np.nanpercentile(diff,[2.5,97.5]).tolist(),
        bootstrap_rounds=5000,bootstrap_unit='whole episode',new_inference_calls=0,new_teacher_calls=0)
    OUT.mkdir(exist_ok=True)
    (OUT/'results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    pct=lambda v:'N/A' if v is None else f'{v*100:.2f}%'
    lines=['# Joint versus explanation-auxiliary Qwen: ranking sensitivity','',
        'Saved predictions on the same 50 OopsieData development episodes. Agreement with Sol, not human-reference accuracy. No new inference, training or teacher calls.','',
        f'Only {positives.sum()}/50 episodes have a Sol-positive failure interval.','',
        '| Scope | Episodes | Frames | Joint F1 | Explanation-aux F1 | Binary F1 | Category-aux F1 |','| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for name,g in groups.items():lines.append(f'| {name} | {g["episodes"]} | {g["frames"]} | '+ ' | '.join(pct(g['models'][tag]['pooled_frame_f1']) for tag in scores)+' |')
    lines+=['','| Weighting / metric, all 50 episodes | Joint | Explanation auxiliary |','| --- | ---: | ---: |']
    for k in ['seconds_weighted_f1','equal_episode_pooled_f1','mean_defined_episode_f1','mean_episode_agreement']:
        lines.append(f'| {k} | {pct(groups["all"]["models"]["joint"][k])} | {pct(groups["all"]["models"]["evidence_aux"][k])} |')
    lines+=['',
        'The all-episode mean-defined F1 above omits zero/zero cases and has different denominators (joint 22 episodes; explanation auxiliary 18). On the same fixed 16 teacher-positive episodes, mean per-episode F1 is '+pct(groups['teacher_failure_episodes']['models']['joint']['mean_defined_episode_f1'])+' for joint and '+pct(groups['teacher_failure_episodes']['models']['evidence_aux']['mean_defined_episode_f1'])+' for explanation auxiliary. Mean episode F1 and pooled equal-episode F1 are different calculations.','',
        'The two PRISM episodes contain 1,637/2,095 (78.14%) of the teacher-positive frames. Both labs remain part of the evaluation; lab-specific results expose different weaknesses rather than providing a reason to discard episodes.','',
        f'On the fixed set of {positives.sum()} teacher-positive episodes, per-episode failure F1 wins: joint {wins["joint_failure_f1_wins"]}, explanation auxiliary {wins["evidence_failure_f1_wins"]}, ties {wins["failure_f1_ties"]}.','',
        f'The 5,000 paired whole-episode bootstrap interval for explanation-auxiliary minus joint pooled failure F1 is [{pct(result["paired_bootstrap_evidence_minus_joint_f1_95"][0])}, {pct(result["paired_bootstrap_evidence_minus_joint_f1_95"][1])}]. This describes sampling uncertainty within the teacher-labeled development set; it does not validate the teacher.','',
        'Binary scores do not evaluate explanation grounding, category correctness, recovery, severity or resetability. A visually better model and a higher teacher-agreement model can differ. This audit checks weighting sensitivity, not independent human correctness.','',
        '| Episode | Frames | Joint F1 | Explanation-aux F1 | Joint agreement | Explanation-aux agreement |','| --- | ---: | ---: | ---: | ---: | ---: |']
    for r in details:lines.append(f'| {r["episode"]} | {r["frames"]} | {pct(r["joint_f1"])} | {pct(r["evidence_aux_f1"])} | {pct(r["joint_agreement"])} | {pct(r["evidence_aux_agreement"])} |')
    (OUT/'report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps(dict(teacher_positive_episodes=int(positives.sum()),groups=groups,wins=dict(wins),
        paired_bootstrap_evidence_minus_joint_f1_95=result['paired_bootstrap_evidence_minus_joint_f1_95']),indent=2))


if __name__=='__main__':main()
