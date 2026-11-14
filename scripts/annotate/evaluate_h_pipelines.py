"""Evaluate blinded U/P/W predictions against frozen, contact-assisted human H labels."""
import csv
import json
from pathlib import Path
from statistics import mean
import api_h_pipeline_evaluation_v1 as run
from annotation_metrics import evaluate,text_for,failure_types,prf
from review_api_experiment import parse_segments
from h_reference import human_reference,legacy_projection


def main():
    manifest=run.verify();out=run.OUT/'evaluation';out.mkdir(exist_ok=True)
    records={p.stem:run.common.load(p) for p in (run.OUT/'attempts').glob('*.json')}
    audited=[]
    for job in manifest['jobs']:
        ident=job['id'];record=records.get(ident,{})
        if record.get('status')!='completed':continue
        raw=run.common.load(run.OUT/'responses'/(ident+'_raw.json'))
        answer,complete=run.extract_answer(job['provider'],raw)
        assert complete and answer==(run.OUT/'responses'/(ident+'.md')).read_text(encoding='utf-8')
        for key,value in run.usage_cost(job['provider'],raw).items():
            assert record[key]==value,(ident,key)
        _,_,evidence=run.build_payload(job)
        assert evidence==run.common.load(run.OUT/'requests'/(ident+'_evidence.json'))
        audited.append(ident)
    refs={};predictions={};texts=set();inventory=[]
    for ep in manifest['episodes']:
        eid=ep['id'];refs[eid],raw=human_reference(run.OUT,eid,ep['n_frames'])
        assert raw['task']==ep['task'] and raw['fps']==ep['fps']
        texts.update(text_for(s) for s in refs[eid] if text_for(s))
        for arm in ('U','P','W'):
            ident=eid+'_'+arm;record=records.get(ident,{})
            answer=run.OUT/'responses'/(ident+'.md');segments=[];warnings=[]
            if answer.exists():segments,warnings=parse_segments(answer.read_text(encoding='utf-8'),ep['n_frames'])
            eligible=record.get('status')=='completed' and bool(segments) and not warnings
            inventory.append({'id':ident,'status':record.get('status','not_run'),'warnings':warnings,'eligible':eligible})
            if not eligible:continue
            job=next(j for j in run.jobs() if j['id']==ident)
            _,_,evidence=run.build_payload(job)
            assert evidence==run.common.load(run.OUT/'requests'/(ident+'_evidence.json'))
            assert len(evidence['frames'])==ep['budget'] and set(ep['overview'])<=set(evidence['frames'])
            predictions[ident]=segments;texts.update(text_for(s) for s in segments if text_for(s))
    from build_annotation_embeddings import build
    vectors=build(texts,out)
    rows=[];metrics={};differences={}
    for ep in manifest['episodes']:
        eid=ep['id'];n=ep['n_frames'];fps=ep['fps'];reference=refs[eid]
        for arm in ('U','P','W'):
            ident=eid+'_'+arm
            if ident not in predictions:continue
            original=predictions[ident];pred=legacy_projection(original)
            m=evaluate(pred,reference,n,fps,vectors)
            m['legacy_class_accuracy']=m.pop('joint_accuracy')
            m['projection']='failure precedence: both -> failure; progress-only -> progress; neither -> neutral'
            m['original_both_frame_fraction']=sum(s['end']-s['start'] for s in original if s['progress'] and s['failure'])/n
            metrics[ident]=m
            cost_ids=[ident]+([eid+'_'+{'P':'SP','W':'SW'}[arm]] if arm!='U' else [])
            cost=sum(records[i]['generation_estimate_usd'] for i in cost_ids)
            row={'id':ident,'legacy_class_accuracy':m['legacy_class_accuracy'],
                 'legacy_progress_f1':m['axes']['progress']['f1'],'failure_f1':m['axes']['failure']['f1'],
                 'phase_boundary_f1_250ms':m['phase_boundaries'][1]['f1'],
                 'matched_boundary_mae_seconds':m['phase_boundaries'][1]['matched_mae_seconds'],
                 'description_cosine':m['semantic']['time_weighted_cosine'],
                 'predicted_segments':len(pred),'human_segments':len(reference),
                 'both_frame_fraction':m['original_both_frame_fraction'],'pipeline_generation_usd':cost}
            row['review_required_frame_fraction']=m['prediction_review_required_fraction']
            rows.append(row)
            issues=[]
            for i,p in enumerate(pred):
                for j,h in enumerate(reference):
                    a,b=max(p['start'],h['start']),min(p['end'],h['end'])
                    if a>=b:continue
                    pc='failure' if p['failure'] else 'progress' if p['progress'] else 'neutral'
                    label_mismatch=pc!=h['legacy_classification'];types_mismatch=failure_types(p)!=failure_types(h)
                    if label_mismatch or types_mismatch:
                        issues.append({'start':a,'end':b,'human_class':h['legacy_classification'],'predicted_legacy_class':pc,
                                       'human_types':sorted(failure_types(h)),'predicted_types':sorted(failure_types(p)),
                                       'human_text':h['description'],'prediction_text':text_for(original[i]),
                                       'label_mismatch':label_mismatch,'failure_type_mismatch':types_mismatch})
            differences[ident]=issues
            lines=[f'# {ident} versus human H', '', 'Reference uses legacy exclusive labels with recorded simulator-contact assistance.',
                   'Model both-state predictions are projected to failure for this comparison; original predictions are unchanged.', '']
            boundary=m['phase_boundaries'][1]
            lines+=['## Phase boundary differences (250 ms tolerance)', '',
                    'Unmatched model boundaries: '+str(boundary['unmatched_prediction_frames']),
                    'Unmatched human boundaries: '+str(boundary['unmatched_reference_frames']), '',
                    '| Model frame | Human frame | Signed error (seconds) |','|---:|---:|---:|']
            for match in boundary['matches']:
                lines.append(f'| {match["prediction_frame"]} | {match["reference_frame"]} | {match["signed_error_seconds"]:.3f} |')
            lines+=['','Positive timing error means the model boundary is later. Unmatched boundaries can reflect different granularity; inspect the video.','']
            for issue in issues:
                a,b=issue['start'],issue['end'];url=f'http://127.0.0.1:8766/runs/{run.OUT.name}/?episode={eid}&arm={arm}&frame={a}'
                lines += [f'## [{a}, {b}) / {a/fps:.2f}-{b/fps:.2f} s', '',
                          'Human: '+issue['human_class']+'; '+str(issue['human_types']),issue['human_text'],'',
                          'Model (legacy projection): '+issue['predicted_legacy_class']+'; '+str(issue['predicted_types']),issue['prediction_text'],'',
                          '[Review video]('+url+')','']
            if not issues:lines.append('No legacy class or failure-type disagreement. Boundary/description differences may remain.')
            (out/(ident+'_differences.md')).write_text('\n'.join(lines)+'\n',encoding='utf-8')
    paired=[eid for eid in run.IDS if all(eid+'_'+a in metrics for a in ('U','P','W'))]
    aggregate={}
    for arm in ('U','P','W'):
        ms=[metrics[eid+'_'+arm] for eid in paired]
        if not ms:continue
        counts=lambda metric:prf(*(sum(metric(m)[k] for m in ms) for k in ('tp','fp','fn')))
        aggregate[arm]={'episodes':paired,'macro_legacy_class_accuracy':mean(m['legacy_class_accuracy'] for m in ms),
                        'pooled_failure':counts(lambda m:m['axes']['failure']),
                        'pooled_phase_boundaries_250ms':counts(lambda m:m['phase_boundaries'][1]),
                        'macro_review_required_fraction':mean(m['prediction_review_required_fraction'] for m in ms),
                        'macro_description_cosine':mean(m['semantic']['time_weighted_cosine'] for m in ms)}
    payload={'reference':'User-designated H human segment labels, assisted by privileged_simulator_contacts',
             'schema_limitation':'Legacy-exclusive compatibility; no independent four-state ground truth. No event/state-array scoring.',
             'inventory':inventory,'audited_completed_calls':audited,'paired_episode_ids':paired,'paired_aggregate':aggregate,
             'metrics':metrics,'differences':differences,
             'human_freeze_sha256':run.common.digest(run.OUT/'human_reference_freeze.json'),
             'input_manifest_sha256':run.common.digest(run.OUT/'manifest.json'),
             'code_sha256':{name:run.common.digest(Path(__file__).with_name(name)) for name in ('evaluate_h_pipelines.py','annotation_metrics.py','h_reference.py')},'paid_evaluation_api_calls':0}
    run.common.write_json(out/'scores.json',payload)
    if rows:
        with (out/'scores.csv').open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    fmt=lambda x:'N/A' if x is None else f'{x:.3f}'
    lines=['# H human-reference pipeline evaluation','',payload['reference']+'.',payload['schema_limitation'],'',
           f'Valid scored annotations: {len(rows)}/36. Matched U/P/W episodes: {len(paired)}/12.',
           'Full paired cohort: '+', '.join(paired)+'.','',
           '| Condition | Legacy class accuracy (episode mean) | Failure F1 (pooled) | Phase boundary F1 +/-250ms (pooled) | Description cosine (episode mean) |',
           '|---|---:|---:|---:|---:|']
    for arm,a in aggregate.items():lines.append('| '+arm+' | '+' | '.join(fmt(v) for v in (a['macro_legacy_class_accuracy'],a['pooled_failure']['f1'],a['pooled_phase_boundaries_250ms']['f1'],a['macro_description_cosine']))+' |')
    lines+=['','These aggregate comparisons use only the same complete, structurally valid episodes in every condition.',
            'Missing/invalid outputs remain in the inventory; do not interpret the available-case scores without completion rates.',
            'Cosine similarity is not factual correctness. Human neutral labels and newer failure definitions can disagree by scheme.',
            'Provisional model labels are scored as emitted, not excluded. Review-required duration is retained in scores.csv and scores.json.',
            'H was used in historical few-shot development; this is not a wholly unseen evaluation. No H labels were sent in these requests.','',
            '## Per-episode results','', '| Call | Legacy class accuracy | Failure F1 | Boundary F1 +/-250ms | Cosine | Pipeline USD | Differences |',
            '|---|---:|---:|---:|---:|---:|---|']
    for r in rows:lines.append('| '+r['id']+' | '+' | '.join(fmt(r[k]) for k in ('legacy_class_accuracy','failure_f1','phase_boundary_f1_250ms','description_cosine','pipeline_generation_usd'))+' | [Review]('+r['id']+'_differences.md) |')
    lines+=['','## Unscored annotations','']
    for cell in inventory:
        if not cell['eligible']:lines.append('- '+cell['id']+': '+cell['status']+'; '+'; '.join(cell['warnings']))
    (out/'RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'scored':len(rows),'paired_episodes':paired,'aggregate':aggregate},indent=2))

if __name__=='__main__':main()
