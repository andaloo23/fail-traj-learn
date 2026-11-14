"""Audit local scorers and independent judges without inventing human labels."""
import argparse
from collections import defaultdict
import html
import json
from pathlib import Path
import statistics

import annotation_runtime as io
from experiment_independent_judges import validate


def normalize_relation_whitespace(item, mode):
    """Canonicalize surrounding whitespace only; preserve every substantive judgment."""
    import copy
    normalized=copy.deepcopy(item);changes=[]
    targets=[]
    if mode=='scalar':targets=[('relation',normalized)]
    elif mode=='slots':targets=[('overall_relation',normalized)]+[('relation',v) for v in normalized.get('dimensions',{}).values()]
    elif mode=='facts':targets=[('relation',v) for v in normalized.get('alignments',[])]
    for key,obj in targets:
        value=obj.get(key)
        if isinstance(value,str) and value.strip()!=value:
            changes.append(dict(field=key,before=value,after=value.strip()));obj[key]=value.strip()
    return normalized,changes


def report(out):
    corpus=io.load(out/'corpus.json'); rows=corpus['pairs']; lookup={r['pair_id']:r for r in rows}
    controls=[r for r in rows if r['kind']=='control']
    local={}; summary={'corpus':{k:v for k,v in corpus.items() if k!='pairs'},'local':{},'judges':{}}
    for f in sorted(out.glob('local_*.json')):
        d=io.load(f)
        if d['corpus_sha256']!=io.digest(out/'corpus.json'): raise ValueError('Local scores belong to another corpus')
        key=f.stem.removeprefix('local_'); local[key]={r['pair_id']:r for r in d['pairs']}
        def selected(relation):return [r for r in d['pairs'] if r.get('expected_relation')==relation]
        contradictions=selected('contradiction')
        equivalent=[r for r in selected('equivalent') if r['left']!=r['right'] and not r['context']]
        selfs=[r['raw_score'] for r in d['pairs'] if r['left']==r['right']]
        stat=dict(model=d['model'],kind=d['kind'],self_raw_min=min(selfs),self_raw_max=max(selfs),
                  paraphrase_min=min(r['raw_score'] for r in equivalent),
                  contradiction_max=max(r['raw_score'] for r in contradictions),
                  contradictions_high_09=sum(r['raw_score']>=.9 for r in contradictions),contradiction_controls=len(contradictions),
                  self_ratio_above_one=sum(r['self_normalized_unclipped']>1+1e-6 for r in d['pairs'] if r['self_normalized_unclipped'] is not None),
                  worst_contradiction=max(contradictions,key=lambda r:r['raw_score'])['name'])
        if d['kind']=='nli':
            stat['contradictions_detected_both_directions_09']=sum(min(r['contradiction_ab'],r['contradiction_ba'])>=.9 for r in contradictions)
            stat['false_contradictions_09']=[r['name'] for r in d['pairs'] if r['kind']=='control' and r['expected_relation']!='contradiction' and min(r['contradiction_ab'],r['contradiction_ba'])>=.9]
        summary['local'][key]=stat
    judgments=defaultdict(dict); invalid=[];normalizations=[];cost=0
    folders=[out/'judges',*sorted(out.glob('*/judges'))]
    for folder in folders:
        manifest=io.load(folder/'manifest.json')
        if manifest['corpus_sha256']!=io.digest(out/'corpus.json'):raise ValueError('Judge corpus mismatch')
        for name,digest in manifest['files'].items():
            if io.digest(folder/name)!=digest:raise ValueError('Judge frozen input changed')
        for job in manifest['jobs']:
            attempt=folder/f"{job['name']}_attempt.json"
            if not attempt.exists():raise ValueError('Unfinished experiment')
            a=io.load(attempt)
            if a['status']=='reserved':raise ValueError('Experiment still running')
            cost+=a.get('generation_estimate_usd',0)
            path=folder/f"{job['name']}_answer.txt"
            if not path.exists():
                invalid.append(dict(job=job['name'],error=a.get('error','No answer'),pairs=job['ids']));continue
            raw=io.load(folder/f"{job['name']}_raw.json")
            _,complete=io.extract_answer('gemini',raw)
            if not complete:
                invalid.append(dict(job=job['name'],error='Incomplete generation',pairs=job['ids']));continue
            try:answer=json.loads(path.read_text(encoding='utf-8'))
            except ValueError:
                invalid.append(dict(job=job['name'],error='Invalid JSON',pairs=job['ids']));continue
            # Validate each pair independently to retain valid neighbors from a failed batch.
            items=answer.get('pairs',[]); ids=[x.get('pair_id') for x in items]
            if len(ids)!=len(job['ids']) or set(ids)!=set(job['ids']):
                invalid.append(dict(job=job['name'],error='ID coverage failure',pairs=job['ids']));continue
            for item in items:
                item,changes=normalize_relation_whitespace(item,job['mode'])
                try: item=validate({'pairs':[item]},dict(job,ids=[item['pair_id']]))[0]
                except (ValueError,KeyError,TypeError) as e:
                    invalid.append(dict(job=job['name'],error=str(e),pairs=[item.get('pair_id')]));continue
                if changes:normalizations.append(dict(job=job['name'],pair_id=item['pair_id'],changes=changes))
                key=f"{job['model']}_{job['mode']}"
                if job['order'] in judgments[key].get(item['pair_id'],{}):
                    raise ValueError('Multiple valid results for the same method, pair, and order')
                judgments[key].setdefault(item['pair_id'],{})[job['order']]=item
    for key,by_id in sorted(judgments.items()):
        def relation(x):return x.get('overall_relation',x.get('relation',x.get('computed',{}).get('relation')))
        def score(x):return x['score']/100 if 'score' in x else x['computed']['score']
        decisions=[(lookup[pid],order,x) for pid,orders in by_id.items() for order,x in orders.items()]
        control=[(r,o,x) for r,o,x in decisions if r['kind']=='control']
        disagreements=[dict(pair_id=r['pair_id'],name=r['name'],order=o,expected=r['expected_relation'],actual=relation(x),rationale=x['rationale']) for r,o,x in control if relation(x)!=r['expected_relation']]
        both=[(pid,d) for pid,d in by_id.items() if set(d)=={'ab','ba'}]
        deltas=[abs(score(d['ab'])-score(d['ba'])) for _,d in both]
        selftests=[score(x) for r,o,x in control if r['left']==r['right']]
        contradictions=[(r,o,x) for r,o,x in control if r['expected_relation']=='contradiction']
        stat=dict(control_decisions=len(control),relation_matches=len(control)-len(disagreements),disagreements=disagreements,
            explicit_contradictions_detected=sum(relation(x)=='contradiction' for r,o,x in contradictions),explicit_contradiction_decisions=len(contradictions),
            identical_perfect=sum(s==1 for s in selftests),identical_tests=len(selftests),
            equivalent_but_not_perfect=[dict(pair_id=r['pair_id'],order=o,score=score(x)) for r,o,x in decisions if relation(x)=='equivalent' and score(x)!=1],
            bidirectional_pairs=len(both),order_relation_disagreements=sum(relation(d['ab'])!=relation(d['ba']) for _,d in both),
            mean_absolute_score_delta=statistics.mean(deltas) if deltas else None,max_absolute_score_delta=max(deltas) if deltas else None,
            score_delta_over_01=[pid for (pid,d),delta in zip(both,deltas) if delta>.1+1e-9],
            real_decisions=sum(r['kind']=='real' for r,o,x in decisions),missing_pair_orders=[dict(pair_id=r['pair_id'],order=o) for r in rows for o in ('ab','ba') if o not in by_id.get(r['pair_id'],{})])
        viewer_path=out/'viewer_data.json'
        if viewer_path.exists():
            viewer=io.load(viewer_path)
            real_lookup={(r['episode'],r['left'],r['right']):by_id.get(r['pair_id'],{}) for r in rows if r['kind']=='real'}
            frames=covered=0;weighted=0.;episode_means=[]
            for ep in viewer['episodes']:
                ann=ep['versions'][viewer['default_run']];subtotal=0.;count=0
                for frame in range(ep['n_frames']):
                    if any(any(s['start_frame']<=frame<s['end_frame'] for s in ann[p].get('uncertain_intervals',[])) for p in ('openai','gemini')):continue
                    texts=[next((s['what_happened'] for s in ann[p]['segments'] if s['start_frame']<=frame<s['end_frame']),None) for p in ('openai','gemini')]
                    orders=real_lookup.get((ep['id'],*texts),{})
                    if set(orders)=={'ab','ba'}:count+=1;subtotal+=(score(orders['ab'])+score(orders['ba']))/2
                episode_means.append(dict(episode=ep['id'],scored_frames=count,total_frames=ep['n_frames'],mean_all_frames=subtotal/ep['n_frames'] if count==ep['n_frames'] else None))
                covered+=count;weighted+=subtotal;frames+=ep['n_frames']
            stat['frame_aggregation']=dict(episodes=episode_means,total_frames=frames,scored_frames=covered,
                mean_all_frames=weighted/frames if frames and covered==frames else None,
                limitation='Mean of both orders at each source frame. These method-specific agreement quantities are not calibrated accuracy or interchangeable percentages.')
        summary['judges'][key]=stat
    summary.update(generation_estimate_usd=cost,invalid_calls_or_pairs=invalid,relation_whitespace_normalizations=normalizations,
        caveats=['Authored controls test semantic behavior, not human/video accuracy.',
                'Different-product and swapped-role controls permit compatible concurrent facts; judges may assume one exclusive event. The release-paraphrase control can distinguish an active operation from its physical result. These authored expectations require adjudication; their relation disagreements are not established model errors.',
                'Local models receive text only; contextual alias controls are not a fair identical-input comparison with context-aware judges.',
                'Direct 0-100 numbers are subjective, uncalibrated rubric scores. More bins do not establish precision.',
                'Fact Dice arithmetic is explicit, but fact extraction and alignment remain model dependent and can vary with order/sampling.',
                'Dimension scoring uses nine equally weighted slots and gives partial differences zero full-equivalence credit; this is a defined diagnostic, not a universal semantic percentage.',
                'Report parsing trims surrounding relation whitespace, with each change logged. Raw responses and strict generation-time schema failure records remain unchanged.',
                'Pair comparison covers entire descriptions; boundary mismatch can cause scope differences. Do not interpret real pair mismatches as VLM errors without reviewing evidence.'])
    io.write_json(out/'results_summary.json',summary)
    payload=dict(summary=summary,corpus=rows,local=local,judges=judgments)
    io.write_json(out/'report_data.json',payload)
    template=Path(__file__).with_suffix('.html').read_text(encoding='utf-8')
    (out/'report.html').write_text(template.replace('__DATA__',json.dumps(payload).replace('<','\\u003c')),encoding='utf-8')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();report(a.out)
