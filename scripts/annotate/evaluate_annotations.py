"""Compare model annotations offline; accuracy requires explicitly approved human references."""
import argparse
import csv
import hashlib
import itertools
import json
import re
from pathlib import Path
from annotation_metrics import evaluate,text_for,failure_types
from review_api_experiment import parse_segments

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'outputs/annotation_evaluation_v1'
REFERENCES=ROOT/'annotations/human_reference_v1'
RUNS={'semantic':ROOT/'outputs/frame_selection_semantic_v2', 'windows':ROOT/'outputs/frame_selection_windows_v1'}
ARMS={'semantic':['A','B','C','D','F'],'windows':['U','P','W']}
PAIRS=[('semantic/A','semantic/B'),('semantic/D','semantic/F'),('windows/U','windows/P'),
       ('windows/U','windows/W'),('windows/P','windows/W'),('semantic/C','windows/W')]


def load(path):return json.loads(path.read_text(encoding='utf-8'))
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def inventory():
    cells={};episodes={};provenance={}
    for group,root in RUNS.items():
        manifest=load(root/'manifest.json');provenance[group]={'manifest_sha256':digest(root/'manifest.json'),'models':manifest['settings']['models']}
        for ep in manifest['episodes']:
            eid=ep['id'];source=load(root/eid/'input.json')
            if eid in episodes:
                assert source['source_sha256']==episodes[eid]['source_sha256'] and source['task']==episodes[eid]['task']
            episodes[eid]=source
            for arm in ARMS[group]:
                ident=eid+'_'+arm;attempt=root/'attempts'/(ident+'.json');answer=root/'responses'/(ident+'.md')
                record=load(attempt) if attempt.exists() else {};rows=[];warnings=[]
                if answer.exists():rows,warnings=parse_segments(answer.read_text(encoding='utf-8'),source['n_frames'])
                eligible=record.get('status')=='completed' and bool(rows) and not warnings and all('progress' in s for s in rows)
                cost_records=[record]
                if group=='windows' and arm in ('P','W'):
                    selector=root/'attempts'/(eid+'_'+{'P':'SP','W':'SW'}[arm]+'.json')
                    cost_records.append(load(selector) if selector.exists() else {})
                if group=='semantic' and arm=='F':
                    selector=root/'attempts'/(eid+'_E.json');cost_records.append(load(selector) if selector.exists() else {})
                known=all(r.get('generation_estimate_usd') is not None for r in cost_records)
                cells[eid+'/'+group+'/'+arm]={'episode':eid,'condition':group+'/'+arm,'status':record.get('status','not_run'),
                    'eligible':eligible,'warnings':warnings,'segments':rows,'source':str(answer),
                    'answer_sha256':digest(answer) if answer.exists() else None,
                    'pipeline_generation_estimate_usd':sum(r['generation_estimate_usd'] for r in cost_records) if known else None}
    return cells,episodes,provenance


def prepare(refs):
    cells,episodes,_=inventory();refs.mkdir(parents=True,exist_ok=True)
    for eid,ep in episodes.items():
        path=refs/(eid+'.md')
        if path.exists():continue
        path.write_text(f"""# Human reference: {eid}

- Status: draft
- Reviewer:
- Reviewed at:
- Episode: {eid}
- Source camera SHA256: {ep['source_sha256']['cameras.npz']}
- Task: {ep['task']}
- Frames: {ep['n_frames']}
- FPS: {ep['fps']}

Review the full source video independently. This file contains no model labels.
Use the current annotation scheme; cover [0, {ep['n_frames']}) without gaps/overlaps.
Add `## Segments` with one `###` heading per phase and explicit Interval, Progress,
Failure, Progress confidence, Failure confidence, Review required, Phase,
Description, Failure types, Failure reason, and Boundary reason bullets.
Resolve uncertain judgments before changing Status to approved, and fill reviewer/date.
Failure types: missed_target, lost_control, wrong_action, collision, timeout, other;
use none when Failure is no. No reference-based scores are produced while draft.
Optional Events are for human review and are not scored by this evaluator.

## Segments

Pending independent human annotation.
""",encoding='utf-8')
    print('Prepared draft references:',refs)


def reference(path,ep):
    if not path.exists():return None,'missing'
    text=path.read_text(encoding='utf-8')
    def field(name):
        m=re.search(r'(?im)^- '+re.escape(name)+r':[ \t]*(.*)$',text);return m[1].strip() if m else ''
    if field('Status').lower()!='approved':return None,'draft/unapproved'
    if not field('Reviewer') or not field('Reviewed at'):return None,'missing review provenance'
    if field('Episode')!=ep['id'] or field('Source camera SHA256')!=ep['source_sha256']['cameras.npz']:
        return None,'source/episode mismatch'
    if field('Task')!=ep['task'] or field('Frames')!=str(ep['n_frames']) or field('FPS')!=str(ep['fps']):
        return None,'task/frame metadata mismatch'
    rows,warnings=parse_segments(text,ep['n_frames'])
    if warnings or not rows:return None,'invalid reference: '+'; '.join(warnings)
    for s in rows:
        if s.get('review_required') or 'low' in (s.get('progress_confidence'),s.get('failure_confidence')):
            return None,'unresolved reference labels'
        types=failure_types(s)
        if s['failure'] and (not types or 'unknown' in types):return None,'unresolved reference failure type'
        if not s['failure'] and types:return None,'failure type on non-failure reference'
        if not text_for(s):return None,'reference description missing'
    return rows,'approved'


def run(mode,refs,output,embed):
    cells,episodes,provenance=inventory();output.mkdir(parents=True,exist_ok=True)
    references={};reference_status={}
    for eid,ep in episodes.items():references[eid],reference_status[eid]=reference(refs/(eid+'.md'),ep)
    texts={text_for(s) for c in cells.values() if c['eligible'] for s in c['segments'] if text_for(s)}
    texts.update(text_for(s) for rows in references.values() if rows for s in rows if text_for(s))
    vectors=None
    if embed:
        from build_annotation_embeddings import build
        vectors=build(texts,output)
    results=[];unavailable=[]
    if mode=='agreement':
        for eid,ep in episodes.items():
            for left,right in PAIRS:
                a,b=cells[eid+'/'+left],cells[eid+'/'+right]
                if not a['eligible'] or not b['eligible']:
                    unavailable.append({'episode':eid,'left':left,'right':right,'reason':'missing or structurally invalid output'});continue
                metrics=evaluate(a['segments'],b['segments'],ep['n_frames'],ep['fps'],vectors,require_verified=False)
                metrics['joint_label_agreement']=metrics.pop('joint_accuracy')
                for axis in metrics['axes'].values():axis['agreement']=axis.pop('accuracy')
                results.append({'episode':eid,'left':left,'right':right,'metrics':metrics})
    else:
        for cell in cells.values():
            eid=cell['episode'];ep=episodes[eid]
            if not cell['eligible'] or references[eid] is None:
                unavailable.append({'episode':eid,'condition':cell['condition'],'reason':reference_status[eid] if references[eid] is None else 'invalid/missing model output'});continue
            results.append({'episode':eid,'condition':cell['condition'],
                            'metrics':evaluate(cell['segments'],references[eid],ep['n_frames'],ep['fps'],vectors)})
    report={'code_sha256':{name:digest(Path(__file__).with_name(name)) for name in ('evaluate_annotations.py','annotation_metrics.py','build_annotation_embeddings.py','review_api_experiment.py')},'mode':mode,'warning':'Model agreement is not accuracy; models can share mistakes.' if mode=='agreement' else 'Accuracy against explicitly approved human references only.',
            'reference_status':reference_status,'provenance':provenance,
            'reference_sha256':{eid:digest(refs/(eid+'.md')) for eid in episodes if (refs/(eid+'.md')).exists()},
            'cells':cells,'results':results,'unavailable':unavailable,'paid_api_calls':0}
    (output/(mode+'.json')).write_text(json.dumps(report,indent=2),encoding='utf-8')
    compact=[]
    for row in results:
        m=row['metrics'];sem=m.get('semantic',{});bound=m['phase_boundaries'][1]
        compact.append({k:v for k,v in row.items() if k!='metrics'}|{
            'joint_label_agreement' if mode=='agreement' else 'joint_accuracy':m.get('joint_label_agreement',m.get('joint_accuracy')),
            'progress_f1':m['axes']['progress']['f1'],'failure_f1':m['axes']['failure']['f1'],
            'phase_boundary_f1_250ms':bound['f1'],'matched_boundary_mae_seconds':bound['matched_mae_seconds'],
            'description_cosine':sem.get('time_weighted_cosine')})
    if not compact and (output/(mode+'.csv')).exists():
        (output/(mode+'.csv')).unlink()
    if compact:
        with (output/(mode+'.csv')).open('w',newline='',encoding='utf-8') as f:
            writer=csv.DictWriter(f,fieldnames=list(compact[0]));writer.writeheader();writer.writerows(compact)
    lines=['# '+('Model agreement - not accuracy' if mode=='agreement' else 'Human-reference evaluation'),'',report['warning'],'',
           f'Available comparisons: {len(results)}. Unavailable: {len(unavailable)}. Paid API calls: 0.','',
           'Reference status: '+', '.join(e+': '+s for e,s in reference_status.items()),'',
           '| Episode | Comparison | Joint labels | Progress F1 | Failure F1 | Phase-boundary F1 (250ms) | Description cosine |',
           '|---|---|---:|---:|---:|---:|---:|']
    def fmt(v):return 'N/A' if v is None else f'{v:.3f}'
    for row in compact:
        label=row.get('condition') or row['left']+' vs '+row['right']
        lines.append('| '+row['episode']+' | '+label+' | '+' | '.join(fmt(row[k]) for k in (('joint_label_agreement' if mode=='agreement' else 'joint_accuracy'),'progress_f1','failure_f1','phase_boundary_f1_250ms','description_cosine'))+' |')
    lines+=['','Counts/denominators and unmatched boundaries are in the JSON. N/A is not zero. No cross-episode ranking is computed.',
            'Invalid/missing outputs remain in the inventory and unavailable list; they are not silently treated as successes.',
            'Semantic cosine is a secondary description-similarity diagnostic, not factual correctness.',
            'Start/end of episode are excluded from boundary matching. Binary-state segment scores merge adjacent identical binary labels.',
            'Fine-grained phase boundary scores retain those boundaries. No unverified simulation labels or original R model labels are used as ground truth.']
    (output/(mode+'.md')).write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'mode':mode,'comparisons':len(results),'unavailable':len(unavailable),'references':reference_status,'output':str(output)},indent=2))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['prepare','agreement','score']);p.add_argument('--references',type=Path,default=REFERENCES);p.add_argument('--output',type=Path,default=OUT);p.add_argument('--embeddings',action='store_true');args=p.parse_args()
    if args.command=='prepare':prepare(args.references)
    else:run(args.command,args.references,args.output,args.embeddings)

if __name__=='__main__':main()
