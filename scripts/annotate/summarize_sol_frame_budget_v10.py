"""Cost and descriptive agreement with V7; never treat model labels as truth."""
import json
import api_sol_frame_budget_v10 as experiment
import api_taxonomy_approach_v7 as baseline
import api_label_pilot as common


def expand(annotation,n):
    result=[None]*n
    for s in annotation['segments']:
        for f in range(s['start_frame'],s['end_frame']):
            result[f]=(s['progress'],s['failure'],tuple(sorted(s['categories'])))
    assert all(x is not None for x in result)
    return result


def events(annotation):
    # Contiguous category bouts ignore arbitrary splits with unchanged categories.
    result=[]
    for category in sorted(baseline.CATEGORIES):
        bouts=[]
        for s in annotation['segments']:
            if category not in s['categories']:continue
            if bouts and bouts[-1][1]==s['start_frame']:bouts[-1][1]=s['end_frame']
            else:bouts.append([s['start_frame'],s['end_frame']])
        result.extend((category,*b) for b in bouts)
    return result


def iou(a,b):
    if a[0]!=b[0]:return 0
    return max(0,min(a[2],b[2])-max(a[1],b[1]))/(max(a[2],b[2])-min(a[1],b[1]))


def match_events(ref,pred,threshold=.5):
    # Maximum-cardinality one-to-one matching at a fixed temporal IoU threshold.
    matched={}
    def visit(i,seen):
        for j in sorted(range(len(pred)),key=lambda j:-iou(ref[i],pred[j])):
            if j in seen or iou(ref[i],pred[j])<threshold:continue
            seen.add(j)
            if j not in matched or visit(matched[j],seen):matched[j]=i;return True
        return False
    for i in range(len(ref)):visit(i,set())
    return len(matched),[list(ref[i]) for i in range(len(ref)) if i not in matched.values()]


def main():
    m=experiment.verify();summary=experiment.report();rows=[]
    for r in summary['results']:
        ep=next(e for e in m['episodes'] if e['id']==r['episode'])
        base=common.load(baseline.OUT/f"{ep['id']}_openai_annotation.json")
        cost=common.load(baseline.OUT/'attempts'/f"{ep['id']}_openai.json")['generation_estimate_usd']
        row=dict(episode=ep['id'],arm=r['arm'],status=r['status'],pairs=len(r['seen_frames']),
            baseline_pairs=len(ep['sampled_frames']),calls=len(r['calls']),cost=r['generation_estimate_usd'],
            baseline_cost=cost,cost_ratio=r['generation_estimate_usd']/cost,requests=r['requests'])
        if r['status']=='validated':
            annotation=common.load(experiment.OUT/f"{ep['id']}_{r['arm']}_annotation.json")
            a,b=expand(base,ep['n_frames']),expand(annotation,ep['n_frames'])
            ref,pred=events(base),events(annotation);matches,unmatched=match_events(ref,pred)
            row.update(state_agreement=sum(x[:2]==y[:2] for x,y in zip(a,b))/len(a),
                category_agreement=sum(x[2]==y[2] for x,y in zip(a,b))/len(a),
                baseline_events=len(ref),predicted_events=len(pred),matched_events_at_iou05=matches,
                unmatched_baseline_events=unmatched,identity_status=annotation['identity_check']['match_status'],
                identity_description=annotation['identity_check']['manipulated_object'])
        rows.append(row)
    totals=[]
    for arm in experiment.ARMS:
        rs=[r for r in rows if r['arm']==arm];valid=[r for r in rs if r['status']=='validated']
        totals.append(dict(arm=arm,finished=len(rs),validated=len(valid),pairs=sum(r['pairs'] for r in rs),
            calls=sum(r['calls'] for r in rs),cost=sum(r['cost'] for r in rs),
            matched_events=sum(r['matched_events_at_iou05'] for r in valid),
            baseline_events=sum(r['baseline_events'] for r in valid),
            predicted_events=sum(r['predicted_events'] for r in valid),
            mean_state_agreement=sum(r['state_agreement'] for r in valid)/len(valid) if valid else None))
    common.write_json(experiment.OUT/'comparison.json',dict(note='V7 agreement, not human accuracy',arms=totals,episodes=rows))
    lines=['# Sol frame-budget experiment','',
        'Descriptive agreement with the unchanged V7 model outputs, **not ground-truth accuracy**.',
        'Matching uses one-to-one same-category temporal IoU >= 0.5 on contiguous category bouts.',
        'Multi-category failures contribute multiple bouts. No-failure episodes contribute no failure bouts.',
        'Costs include every adaptive round, excluding separately reported conservative preflight allowances.','',
        '| Arm | Valid | Camera pairs | Calls | Generation $ | Matched V7 failure bouts | Mean state agreement |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for t in totals:
        state='n/a' if t['mean_state_agreement'] is None else f"{t['mean_state_agreement']:.1%}"
        lines.append(f"| {experiment.ARMS[t['arm']]} | {t['validated']}/4 | {t['pairs']} | {t['calls']} | {t['cost']:.4f} | {t['matched_events']}/{t['baseline_events']} | {state} |")
    lines.extend(['','## Per-episode inspection',''])
    for r in rows:
        lines.extend([f"### {r['episode']} / {r['arm']}",
            f"Status: {r['status']}; {r['pairs']} pairs, {r['calls']} calls, ${r['cost']:.4f} ({r['cost_ratio']:.2f}x baseline)."])
        if r['status']=='validated':
            lines.append('Unmatched V7 category bouts: '+json.dumps(r['unmatched_baseline_events']))
            lines.append('Manipulated object: '+r['identity_description'])
        for req in r['requests']:lines.append(f"Request {req['round']}: frames {req['frames']}. {req['reason']}")
        lines.append('')
    (experiment.OUT/'RESULTS.md').write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps(totals,indent=2))


if __name__=='__main__':main()
