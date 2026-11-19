"""Conditional category/explanation audit from frozen outputs and source cameras.

No inference, training, teacher calls, or modifications to labels. Visual ratings
are assistant observations, explicitly separate from saved Sol annotations.
"""
from collections import Counter
import json
from pathlib import Path
import textwrap

import numpy as np
from PIL import Image,ImageDraw

import export_gemma_libero_4x as style

REPO,RUN=style.REPO,style.RUN
OUT=RUN/'conditional_failure_audit_v1'


def metrics(c):
    tp,fp,fn=c
    return dict(tp=tp,fp=fp,fn=fn,precision=tp/(tp+fp) if tp+fp else None,
        recall=tp/(tp+fn) if tp+fn else None,f1=2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else None)


def overlap(a,b):return max(0,min(a['end_frame'],b['end_frame'])-max(a['start_frame'],b['start_frame']))


def finish_report(rows,stats):
    # Assistant observations after viewing all 31 two-camera contact sheets and
    # denser source-frame checks of D0173, D0185 and D0311. These assess the core
    # physical claim in context, not every product identity or exact boundaries.
    exceptions={
        'D0099_s03':('partial','The gripper engages the cylindrical can; the requested cream-cheese package remains elsewhere on the floor. Failed acquisition is plausible, but the explanation names the requested object and misses wrong-object engagement.'),
        'D0099_s06':('partial','The repeated attempt is again at the can, not the cream-cheese package. The empty withdrawal is described, but object identity and the semantic failure are missed.'),
        'D0142_s03':('partial','The gripper rises without the can. The explanation instead says a carton rises without the gripper; that object type and motion statement are not supported.'),
        'D0173_s11':('contradicted','Frames 248-276 show the can lifting and staying below the gripper. This contradicts the claim that the tool rises without the object.'),
        'D0185_s03':('contradicted','Frames 95-130 show the can rising and rotating with the gripper. The claimed failure to acquire is contradicted by this visible pickup; later failure does not make this pickup unsuccessful.'),
        'D0311_s06':('unresolved','The carton is already at the basket opening and the fingers/support are occluded. A new failed grasp, rather than placement/release adjustment, is not established by these views.'),
        'D0311_s08':('unresolved','The largely unchanged basket-opening views do not establish a new grasp failure or loss of control. The explanation is more definite than the visible evidence.'),
        'D0311_s10':('unresolved','The carton/basket interaction and later basket tilt are visible, but these views do not establish the claimed failed acquisition at frames 260-270.'),
        'D0374_s03':('partial','The approach is to the orange-juice carton, whose lettering is visible in wrist view. Empty withdrawal is plausible, but chocolate-pudding identity and the missing wrong-object category weaken the explanation.'),
        'D0410_s03':('partial','The empty upward withdrawal supports a failed acquisition. The stronger claim of losing previously established control is not established in the inspected frames.'),
    }
    notes={
        'D0138_s03':'The milk carton stays on its side as the gripper rises without stable acquisition. The core failed-pickup description is supported.',
        'D0192_s08':'The package remains below/outside the basket as the gripper withdraws empty. This supports the core failed-acquisition description, with timing shifted relative to Sol.',
        'D0264_s03':'The gripper rises while the approached object stays among the floor objects. Failed acquisition is supported; the exact ketchup identity is not independently established.',
        'D0308_s03':'The green-capped bottle remains lying on the floor during the empty withdrawal. Product identity is provisional, but the core physical description is supported.',
        'D0338_s03':'The bottle remains on the floor as the fingers withdraw. The physical description is supported; the episode is still excluded by the unchanged strict score because of its extra zero-length segment.',
    }
    ratings=[]
    for r in rows:
        rating,note=exceptions.get(r['id'],('supported',notes.get(r['id'],
            'Before/during/after views show a closure attempt followed by withdrawal without stable pickup. This supports the core failed-acquisition description; exact segment boundaries are assessed separately.')))
        ratings.append(dict(id=r['id'],episode=r['episode'],core_physical_description_rating=rating,note=note,
            source_frames=r['selected_contact_frames'],strict_timeline_valid=r['strict_timeline_valid']))
    tally=Counter(r['core_physical_description_rating'] for r in ratings)
    assert tally==Counter(supported=21,partial=5,contradicted=2,unresolved=3)
    observed=dict(reviewer='Assistant visual audit; not independent human ground truth',
        unit='Native predicted failure segment, including one in a strict-invalid episode',
        basis='Six two-camera source timestamps per prediction; additional eight-timestamp checks in three episodes',
        scope='Core physical claim in surrounding context, not full identity accuracy, exact temporal coverage, causal diagnosis, or internal reasoning faithfulness',
        category_diversity='All 31 predictions are grasp; broad taxonomy ability is not demonstrated',
        counts=dict(tally),strict_counts=dict(Counter(r['core_physical_description_rating'] for r in ratings if r['strict_timeline_valid'])),
        ratings=ratings)
    (OUT/'assistant_visual_audit.json').write_text(json.dumps(observed,indent=2)+'\n',encoding='utf-8')
    lines=['# Gemma: conditional categories and explanations','',
        'The evidence supports trying a Qwen output that includes categories and grounded descriptions. Gemma demonstrates useful descriptions of simple acquisition failures, with important limits in category diversity, identity and timing.','',
        'Audited every predicted failure in the 50-episode LIBERO rerun: **31 native segments across 16 episodes**. Thirty segments belong to strict-valid timelines; one is in D0338, whose episode remains rejected for an unrelated zero-length segment. No new inference, teacher calls or training.','',
        'I inspected the original agent/wrist source frames before, during and after all 31 predictions, plus denser checks in three episodes. These are **assistant observations**, not independent human annotations or a standardized explanation benchmark. The rating addresses the core physical description in surrounding context. It does not establish every product identity, exact failure interval, root cause or faithfulness to the model’s internal decision process.','',
        '| Core physical description | Native segments | Strict-valid subset |','| --- | ---: | ---: |']
    for key,label in [('supported','Supported'),('partial','Partly supported'),('contradicted','Contradicted by visible pickup'),('unresolved','Unresolved / insufficient visible evidence')]:
        lines.append(f'| {label} | {tally[key]} | {observed["strict_counts"].get(key,0)} |')
    lines+=['','Repeated attempts within an episode are correlated; these are not 31 independent examples. Product naming may remain unverified even when the empty-withdrawal description is supported.','',
        '| Category check against saved Sol annotations | Result |','| --- | --- |',
        '| Category labels Gemma generated | grasp: 31/31; no other category predicted |',
        '| Predicted-failure episodes where Sol also labels grasp somewhere | 15/16 (93.75%) |',
        '| Complete episode category set matches Sol | 8/16 (50.00%) |',
        '| Category micro F1 restricted to the 16 predicted-failure episodes | 75.00% |',
        '| Category micro F1 over all 50 episodes | 49.18% |',
        '| Strict-valid predicted segments overlapping a Sol failure interval | 16/30 |',
        '| Exact category set among those overlapping segments | 14/16 (87.50%) |','',
        'The 93.75% figure is coarse episode-level category precision: it permits the reference grasp event to occur at a different time. It is not explanation correctness or category correctness for every predicted interval. The 75% conditional category F1 excludes episodes where Gemma predicted no failure. Sol references are model-generated, not independent human ground truth.','',
        'Gemma produces only 12 distinct explanation strings across the 31 predictions, often repeating a template about the tool rising without the object. This can be useful grounded language, but it is a narrow behavior. In the 16 predicted-failure episodes Sol marks identity as a supported match in 10, a supported mismatch in 2, and unresolved in 4. Gemma sometimes confidently names a different-shaped object; for example D0303’s identity block describes a red carton, while the manipulated dressing object is a dark bottle.','',
        'The original detection/timing limitations remain unchanged: 50% episode failure recall, 6.94% strict frame failure recall and 11.95% strict frame failure F1. A description can fit a nearby failed attempt while its predicted interval is early, late or too short.','',
        '## Representative evidence','',
        '- Supported: D0109 and D0372 repeatedly show the gripper withdrawing without the object after attempts.',
        '- Incomplete identity/semantics: D0099 describes cream-cheese acquisition while the robot engages a can; D0374 names chocolate pudding while engaging the orange-juice carton.',
        '- Contradicted: D0173 [255,260) and D0185 [105,115) claim no acquisition, although source frames show an object lifting with the gripper.',
        '- Unresolved: D0311’s three claimed failed grasps are at the basket opening during placement/release; the available views do not establish the claimed failure mechanism.','',
        '## Implication for Qwen','',
        'This is promising evidence for learning observable failure descriptions, particularly failed acquisition. It does not yet validate broad multi-category reasoning. The existing Qwen joint recipe already trains binary labels plus categories/explanations; its saved evaluation requests use the binary output task. The next useful evaluation is its joint output on real OopsieData, separating detection/timing from detail quality. A reference-segment test would isolate categorization/description from detection errors; a predicted-segment test would measure the complete system. Include non-grasp categories, wrong-object cases and successful near-miss cases. No new Qwen evaluation or training was launched by this audit.','',
        '[All candidate annotations and source contact sheets](candidates.md) · [Normal-speed comparison video](../presentation_explanations_1x_v1/index.html) · [Original full results](../findings.md)','',
        '## Per-segment assistant notes','']
    by_id={r['id']:r for r in rows}
    for r in ratings:
        item=by_id[r['id']]
        lines += [f'### {r["id"]}: {r["core_physical_description_rating"]}','',r['note'],'',
            f'Native explanation: {item["prediction"]["what_happened"]}','',f'![Source context]({item["contact_sheet"]})','']
    for eid in ['D0173','D0185','D0311']:
        lines += [f'### {eid}: denser source-frame check','',f'![Denser source frames]({eid}_dense.jpg)','']
    (OUT/'report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')


def main():
    OUT.mkdir(exist_ok=True);(OUT/'contact_sheets').mkdir(exist_ok=True)
    review=json.loads((RUN/'review_data.json').read_text(encoding='utf-8'))
    native_references={r['id']:json.loads(r['messages'][1]['content']) for r in
        (json.loads(line) for line in (REPO/'outputs/sol_v8_distillation_500/export_v1/train.jsonl').read_text(encoding='utf-8').splitlines())}
    references={e['id']:e for e in review['episodes']}
    rows=[];episode_counts=Counter();category_counts=Counter();all_cat=Counter();hashes={};identity_status=Counter()
    for e in review['episodes']:
        eid=e['id'];path=RUN/'parsed'/f'{eid}.json';native=json.loads(path.read_text(encoding='utf-8'))
        truth=e['teachers']['sol'][0]['rich_segments'];pred=[(i,s) for i,s in enumerate(native['segments']) if s['failure']]
        raw=json.loads((RUN/'predictions'/f'{eid}.json').read_text(encoding='utf-8'))
        # The parsed audit input must equal the preserved response, not a rewrite.
        text=raw['text'];parsed=json.loads(text[text.find('{'):text.rfind('}')+1]);assert parsed==native,eid
        hashes[eid]=dict(prediction_sha256=style.sha(RUN/'predictions'/f'{eid}.json'),parsed_sha256=style.sha(path))
        truecats={c for s in truth if s['failure'] for c in s['categories']}
        predcats={c for _,s in pred for c in s['categories']}
        all_cat.update(tp=len(predcats&truecats),fp=len(predcats-truecats),fn=len(truecats-predcats))
        if not pred:continue
        identity_status.update([native_references[eid]['identity_check']['match_status']])
        episode_counts.update(tp=len(predcats&truecats),fp=len(predcats-truecats),fn=len(truecats-predcats),
            exact=predcats==truecats,episodes=1)
        with np.load(REPO/'outputs/sol_v8_distillation_500/source'/eid/'cameras.npz') as data:
            cameras={k:data[k] for k in ['agent','wrist']}
        for i,s in pred:
            key=f'{eid}_s{i+1:02d}';category_counts.update(s['categories'])
            candidates=[t for t in truth if t['failure']]
            best=max(candidates,key=lambda t:overlap(s,t),default=None)
            positive_overlap=overlap(s,best) if best else 0
            overlapping=[t for t in candidates if overlap(s,t)]
            overlapping_cats={c for t in overlapping for c in t['categories']}
            before=max(0,s['start_frame']-15);after=min(e['n_frames']-1,s['end_frame']+15)
            selected=[before,max(0,s['start_frame']-5),s['start_frame'],s['end_frame']-1,
                min(e['n_frames']-1,s['end_frame']+5),after]
            sheet=Image.new('RGB',(1536,708),'#101722');d=ImageDraw.Draw(sheet)
            d.text((16,10),f"{key}: frames [{s['start_frame']}, {s['end_frame']}) | {', '.join(s['categories'])}",font=style.font(25,True),fill='white')
            y=45
            for line in textwrap.wrap(s['what_happened'],105):
                d.text((16,y),line,font=style.font(23),fill='#d4e1f1');y+=29
            d.text((16,128),'Native frame context: before / during / after predicted failure (20 FPS)',font=style.font(21),fill='#bacbdd')
            for column,f in enumerate(selected):
                x=column*256
                d.text((x+7,163),f'Frame {f} / {f/20:.2f}s',font=style.font(21,True),fill='white')
                sheet.paste(Image.fromarray(cameras['agent'][f]),(x,194))
                sheet.paste(Image.fromarray(cameras['wrist'][f]),(x,450))
            sheet.save(OUT/'contact_sheets'/f'{key}.jpg',quality=96)
            rows.append(dict(id=key,episode=eid,segment_index=i,start_frame=s['start_frame'],end_frame=s['end_frame'],
                strict_timeline_valid=raw['timeline_valid'],prediction=s,task=e['task'],
                teacher_identity=native_references[eid]['identity_check'],prediction_identity=native['identity_check'],
                episode_teacher_categories=sorted(truecats),teacher_failure_overlap_frames=positive_overlap,
                total_teacher_failure_overlap_frames=sum(overlap(s,t) for t in candidates),
                overlapping_teacher_categories=sorted(overlapping_cats),
                category_agrees_with_overlapping_teacher=bool(overlapping) and set(s['categories'])==overlapping_cats,
                nearby_teacher_segments=[t for t in truth if t['start_frame']<after+1 and t['end_frame']>before],
                selected_contact_frames=selected,contact_sheet=f'contact_sheets/{key}.jpg'))
    strict=[r for r in rows if r['strict_timeline_valid']]
    overlap_rows=[r for r in strict if r['total_teacher_failure_overlap_frames']]
    stats=dict(predicted_failure_segments=len(rows),predicted_failure_episodes=len({r['episode'] for r in rows}),
        strict_accepted_failure_segments=len(strict),category_histogram=dict(category_counts),
        predicted_failure_frames=sum(r['end_frame']-r['start_frame'] for r in rows),
        strict_predicted_failure_frames=sum(r['end_frame']-r['start_frame'] for r in strict),
        strict_segments_with_teacher_failure_overlap=len(overlap_rows),
        strict_segments_with_exact_categories_on_overlapping_teacher=sum(r['category_agrees_with_overlapping_teacher'] for r in overlap_rows),
        category_episode_micro_all50=metrics([all_cat[k] for k in ['tp','fp','fn']]),
        category_episode_micro_on_predicted_failure_episodes=metrics([episode_counts[k] for k in ['tp','fp','fn']]),
        category_exact_set_on_predicted_failure_episodes=dict(exact=episode_counts['exact'],episodes=episode_counts['episodes']))
    stats['sol_identity_status_on_predicted_failure_episodes']=dict(identity_status)
    (OUT/'candidates.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
    (OUT/'computed_stats.json').write_text(json.dumps(stats,indent=2)+'\n',encoding='utf-8')
    (OUT/'provenance.json').write_text(json.dumps(dict(source_review_sha256=style.sha(RUN/'review_data.json'),
        source_outputs=hashes,new_inference_calls=0,new_teacher_calls=0,training_started=False),indent=2)+'\n',encoding='utf-8')
    lines=['# Gemma predicted-failure category and explanation audit','',
        'Derived from all 50 frozen LIBERO validation outputs. No new model calls or training. Sol agreement and assistant visual observations are separate; neither is independent human ground truth.','',
        'Each contact sheet shows both cameras at six source timestamps before, during and after the native predicted segment. These contextual images can support an event description without establishing the correctness of the predicted temporal boundaries.','']
    for r in rows:
        lines += [f'## {r["id"]}', '',f'- Native interval: [{r["start_frame"]}, {r["end_frame"]})',
            f'- Strict timeline valid: {r["strict_timeline_valid"]}',f'- Categories: {", ".join(r["prediction"]["categories"])}',
            f'- Explanation: {r["prediction"]["what_happened"]}',
            f'- Overlapping Sol failure frames: {r["total_teacher_failure_overlap_frames"]}',
            f'- Overlapping Sol categories: {", ".join(r["overlapping_teacher_categories"]) or "None"}',
            f'- Episode-level Sol categories: {", ".join(r["episode_teacher_categories"])}','',
            f'![Source camera context]({r["contact_sheet"]})','', 'Nearby Sol annotations:','']
        for s in r['nearby_teacher_segments']:
            lines.append(f'- [{s["start_frame"]}, {s["end_frame"]}): failure={s["failure"]}; categories={s["categories"]}; {s["what_happened"]}')
        lines.append('')
    (OUT/'candidates.md').write_text('\n'.join(lines),encoding='utf-8')
    finish_report(rows,stats)
    print(json.dumps(stats,indent=2))


if __name__=='__main__':main()
