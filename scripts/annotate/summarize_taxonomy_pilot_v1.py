"""Offline categorical model agreement. Neither model is ground truth."""
import html
import json
import statistics
import api_taxonomy_pilot_v1 as pilot
from annotation_metrics import match_ordered, boundaries, prf


def iou(a,b):
    inter=max(0,min(a[1],b[1])-max(a[0],b[0]))
    return inter/((a[1]-a[0])+(b[1]-b[0])-inter)


def overlap(a,b,threshold):
    pairs=match_ordered(a,b,lambda x,y: iou(x,y) if iou(x,y)>=threshold else None)
    return {**prf(len(pairs),len(a)-len(pairs),len(b)-len(pairs)), 'pairs':pairs}


def compare(a,b,n,fps):
    unknown={f for v in (a,b) for s in v['uncertain_intervals']
             for f in range(s['start_frame'],s['end_frame'])}
    eligible=set(range(n))-unknown
    axes={}
    for cat in ['any_failure']+sorted(pilot.CATEGORIES):
        sets=[]
        for v in (a,b):
            sets.append({f for s in v['segments'] if cat=='any_failure' or cat in s['categories']
                         for f in range(s['start_frame'],s['end_frame'])} & eligible)
        x,y=sets
        axes[cat]=prf(len(x&y),len(x-y),len(y-x))
    ba,bb=pilot.bouts(a['segments']),pilot.bouts(b['segments'])
    # Whole-event scores are withheld when failure presence is unresolved anywhere:
    # clipping events at an unknown mask would invent segment boundaries.
    events=None if unknown else {str(t):overlap(ba,bb,t) for t in (.25,.50,.75)}
    bounds=None if unknown else {str(t):boundaries(
        sorted({f for s in ba for f in s if 0<f<n}),
        sorted({f for s in bb for f in s if 0<f<n}),fps,t) for t in (.10,.25,.50)}
    return dict(eligible_fraction=len(eligible)/n, excluded_unknown_frames=len(unknown),
                duration_agreement=axes, bout_counts=[len(ba),len(bb)],
                typed_segment_counts=[len(a['segments']),len(b['segments'])],
                bout_overlap=events,bout_boundaries=bounds,
                event_score_note='Withheld if either model marks uncertain failure presence; adjudicate first.')


def main():
    manifest=pilot.verify()
    rows=[]
    unavailable=[]
    for ep in manifest['episodes']:
        paths=[pilot.OUT/(ep['id']+'_'+p+'_annotation.json') for p in pilot.MODELS]
        if not all(p.exists() for p in paths):
            unavailable.append(ep['id'])
            continue
        values=[pilot.common.load(p) for p in paths]
        for v in values: pilot.validate(v,ep)
        rows.append(dict(episode=ep['id'],**compare(*values,ep['n_frames'],ep['fps'])))
    vals=[r['duration_agreement']['any_failure']['f1'] for r in rows
          if r['duration_agreement']['any_failure']['f1'] is not None]
    report=dict(interpretation='GPT/Gemini agreement, not accuracy; precision treats Gemini as comparator only.',
                episode_macro_failure_f1=statistics.mean(vals) if vals else None,
                defined_episode_count=len(vals), available_pair_count=len(rows),planned_pair_count=4,
                unavailable_episodes=unavailable,episodes=rows,
                limitations=['Four inspected development episodes; no generalization or winner claims.',
                             'Remaining unmarked time is a provisional model negative, never a verified negative.',
                             'Semantic uncertainty inside positive segments is retained; scores are provisional.',
                             'Severity/resetability require human adjudication; no automatic quality ranking.'])
    pilot.common.write_json(pilot.OUT/'agreement.json',report)
    body=['<!doctype html><meta charset="utf-8"><title>Categorical agreement</title>',
          '<style>body{font:16px system-ui;margin:30px}td,th{padding:10px}pre{white-space:pre-wrap}</style>',
          '<h1>Categorical agreement: not accuracy</h1><p><a href="review.html">Annotations and camera evidence</a></p>',
          '<p>Unknown failure-presence intervals are excluded from duration scores. Whole-event scores are withheld on those episodes.</p>',
          '<table><tr><th>Episode</th><th>Eligible time</th><th>Failure F1</th><th>Bouts GPT/Gemini</th><th>Typed segments GPT/Gemini</th></tr>']
    for r in rows:
        f=r['duration_agreement']['any_failure']['f1']
        body.append('<tr>'+''.join('<td>'+html.escape(str(x))+'</td>' for x in
             (r['episode'],round(r['eligible_fraction'],3),round(f,3) if f is not None else 'N/A',r['bout_counts'],r['typed_segment_counts']))+'</tr>')
    body.append('</table><details><summary>Full metrics and limitations</summary><pre>'+html.escape(json.dumps(report,indent=2))+'</pre></details>')
    (pilot.OUT/'agreement.html').write_text('\n'.join(body),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('episodes','limitations')},indent=2))


if __name__=='__main__': main()
