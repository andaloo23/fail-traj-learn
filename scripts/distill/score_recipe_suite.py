"""Score source timestamps once; invalid student outputs remain unknown."""
from collections import Counter
import json
from pathlib import Path
import statistics
import uuid

import oopsie_common as common
import failure_enrichment_v8_1 as enrichment
import oopsie_recipe_data as data
from oopsie_bulk_v8_1 import write_once


def labels(segments,n):
    result=[None]*n
    for s in segments:result[s['start_frame']:s['end_frame']]=[int(s['failure'])]*(s['end_frame']-s['start_frame'])
    if None in result:raise ValueError('Reference has a coverage gap')
    return result


def counts(pred,ref):
    if len(pred)!=len(ref):raise ValueError('Prediction/reference lengths differ')
    result=Counter(tp=0,fp=0,fn=0,tn=0,unknown_positive=0,unknown_negative=0)
    for p,r in zip(pred,ref):
        key='unknown_positive' if p is None and r else 'unknown_negative' if p is None else 'tp' if p and r else 'fp' if p else 'fn' if r else 'tn'
        result[key]+=1
    return dict(result)


def metrics(c):
    tp,fp,fn,tn=(c[k] for k in ['tp','fp','fn','tn']);up,un=c['unknown_positive'],c['unknown_negative']
    covered=tp+fp+fn+tn;total=covered+up+un
    return dict(c,frames=total,coverage=covered/total if total else None,
        strict_frame_agreement=(tp+tn)/total if total else None,
        covered_frame_agreement=(tp+tn)/covered if covered else None,
        failure_precision=tp/(tp+fp) if tp+fp else None,
        failure_recall=tp/(tp+fn+up) if tp+fn+up else None,
        failure_f1=2*tp/(2*tp+fp+fn+up) if 2*tp+fp+fn+up else None,
        failure_iou=tp/(tp+fp+fn+up) if tp+fp+fn+up else None,
        specificity=tn/(tn+fp+un) if tn+fp+un else None,
        invalid_frames_are_not_converted_to_nonfailure=True)


def segments(values):
    result=[]
    for i,value in enumerate(values):
        if value is None:continue
        if result and result[-1]['end_frame']==i and result[-1]['failure']==bool(value):result[-1]['end_frame']=i+1
        else:result.append(dict(start_frame=i,end_frame=i+1,failure=bool(value)))
    return result


def boundary_metrics(pred,ref,fps):
    ps=[s for s in segments(pred) if s['failure']];rs=[s for s in segments(ref) if s['failure']]
    pairs=[]
    for i,p in enumerate(ps):
        for j,r in enumerate(rs):
            intersection=max(0,min(p['end_frame'],r['end_frame'])-max(p['start_frame'],r['start_frame']))
            union=max(p['end_frame'],r['end_frame'])-min(p['start_frame'],r['start_frame'])
            if intersection/union>=.3:pairs.append((intersection/union,i,j))
    used_p=set();used_r=set();errors=[]
    for iou,i,j in sorted(pairs,reverse=True):
        if i in used_p or j in used_r:continue
        used_p.add(i);used_r.add(j)
        errors.extend([abs(ps[i]['start_frame']-rs[j]['start_frame'])/fps,abs(ps[i]['end_frame']-rs[j]['end_frame'])/fps])
    return dict(predicted_failure_segments=len(ps),reference_failure_segments=len(rs),matched_failure_segments=len(used_p),
        matched_boundary_mae_seconds=statistics.mean(errors) if errors else None,matching='Greedy descending IoU, one-to-one, threshold >= 0.3')


def score(folder,predictions=None,baseline=None):
    folder=Path(folder);study=common.read(folder.parent/'study.json');source=common.ROOT/study['config']['source_run']
    canonical={e['episode']:e for e in study['episodes']}
    m=common.read(source/'manifest.json');episodes={e['id']:e for e in m['episodes']}
    rows=[json.loads(x) for x in (folder/'records.jsonl').read_text().splitlines()]
    rows=[r for r in rows if r['split']=='development' and r['task']=='binary']
    by_episode={eid:[None]*episodes[eid]['n_frames'] for eid in study['development_ids']}
    valid=invalid=missing=0;issues=[]
    for row in rows:
        if baseline:pred=[int(baseline=='always_yes')]*(row['core_end']-row['core_start']);valid+=1
        else:
            path=Path(predictions)/(row['id']+'.json')
            if not path.exists():missing+=1;continue
            saved=common.read(path)
            try:
                if saved['hit_max']:raise ValueError('Generation reached token cap')
                parsed=data.parse_prediction(saved['text'],row['episode'],row['core_start'],row['core_end'])
                pred=[]
                for s in parsed:pred.extend([int(s['failure'])]*(s['end_frame']-s['start_frame']))
                valid+=1
            except (ValueError,KeyError) as exc:invalid+=1;issues.append(dict(window=row['id'],error=str(exc)));continue
        a,b=row['core_start'],row['core_end'];destination=by_episode[row['episode']]
        if any(x is not None for x in destination[a:b]):raise ValueError('A timestamp was scored twice')
        destination[a:b]=pred
    total=Counter();results=[]
    for eid,pred in by_episode.items():
        e=episodes[eid];native=source/'traces'/f'{eid}_sol_r01'/'annotation.md'
        if common.sha(native)!=canonical[eid]['annotation_sha256']:raise ValueError('Canonical reference changed')
        ref=labels(enrichment.parse(native.read_bytes().decode(),e)['segments'],e['n_frames'])
        c=counts(pred,ref);total.update(c)
        results.append(dict(episode=eid,metrics=metrics(c),boundaries=boundary_metrics(pred,ref,e['fps'])))
    result=dict(kind='student_teacher_agreement',split='development',test_used=False,reference='Frozen Sol V8.1 independent of student predictions',
        baseline=baseline,episodes=len(results),windows=len(rows),valid_windows=valid,invalid_windows=invalid,missing_windows=missing,
        predictions_complete=missing==0,metrics=metrics(total),mean_episode_frame_agreement=statistics.mean(x['metrics']['strict_frame_agreement'] for x in results),
        per_episode=results,invalid_outputs=issues,
        limitation='Teacher imitation, not human-reference accuracy. Overlapping context does not multiply scored frames; unseen episode context can limit the student.')
    return result


def write_report(root,results):
    lines=['# Distillation recipe development results','',
        'All results below compare student outputs to the same preserved Sol references. Final test is sealed. Invalid or missing predictions are unknown and count against strict agreement and coverage.','',
        '| Recipe | Windows returned | Coverage | Frame agreement | Failure F1 | Failure recall | Failure IoU |',
        '|---|---:|---:|---:|---:|---:|---:|']
    def pct(x):return 'N/A' if x is None else f'{100*x:.2f}%'
    for name,r in results.items():
        m=r['metrics'];lines.append(f"| {name} | {r['valid_windows']+r['invalid_windows']}/{r['windows']} | {pct(m['coverage'])} | {pct(m['strict_frame_agreement'])} | {pct(m['failure_f1'])} | {pct(m['failure_recall'])} | {pct(m['failure_iou'])} |")
    lines+=['','Incomplete runs must not be ranked as finished experiments. Recipe selection uses failure detection, output validity and compute cost together.','']
    transport_path=Path(root)/'results.md';temporary=transport_path.with_name('results.'+uuid.uuid4().hex+'.tmp');temporary.write_text('\n'.join(lines),encoding='utf-8');temporary.replace(transport_path)
