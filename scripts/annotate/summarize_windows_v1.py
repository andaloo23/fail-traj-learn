"""Offline provenance, budget and annotation-structure audit; no API calls."""
import json
import re
import api_frame_selection_windows_v1 as run
from review_api_experiment import parse_segments


def main():
    manifest = run.verify()
    prior = run.ROOT / 'outputs/frame_selection_semantic_v2'
    for name in ('progress_failure.md', 'annotate_frame_subset.md'):
        assert (run.OUT/'prompts'/name).read_bytes() == (prior/'prompts'/name).read_bytes()
    rows = {p.stem: run.common.load(p) for p in (run.OUT/'attempts').glob('*.json')}
    audits = []
    for ep in manifest['episodes']:
        eid = ep['id']
        old = run.common.load(prior/eid/'input.json')
        assert ep['pool'] == old['pool'] and ep['telemetry'] == old['telemetry']
        assert run.common.digest(run.common.SOURCE/eid/'cameras.npz') == ep['source_sha256']['cameras.npz']
        for f in ep['pool']:
            for camera in ('agent','wrist'):
                name=f'{f:04d}_{camera}.jpg'
                assert (run.OUT/eid/'images'/name).read_bytes() == (prior/eid/'images'/name).read_bytes()
        texts = []
        for job in [j for j in run.jobs() if j['episode']==eid]:
            row=rows.get(job['id'],{})
            if row.get('status')!='completed':continue
            body,text,evidence=run.build_payload(job)
            assert evidence == run.common.load(run.OUT/'requests'/(job['id']+'_evidence.json'))
            raw=run.common.load(run.OUT/'responses'/(job['id']+'_raw.json'))
            assert run.usage_cost(job['provider'],raw)['generation_estimate_usd']==row['generation_estimate_usd']
            answer,complete=run.extract_answer(job['provider'],raw)
            assert complete and answer==(run.OUT/'responses'/(job['id']+'.md')).read_text(encoding='utf-8')
            if job['provider']=='gemini':
                assert evidence['frames']==ep['pool']
                continue
            assert len(evidence['frames'])==ep['budget'] and len(set(evidence['frames']))==ep['budget']
            assert set(ep['overview'])<=set(evidence['frames'])
            texts.append(re.sub(r'Supplied source frames: .*?\.', 'Supplied source frames: [varies].', text))
            segments,warnings=parse_segments(answer,ep['n_frames'])
            for segment in segments:
                for field in ('phase','failure_types','failure_reason','boundary_reason'):
                    if not segment.get(field):warnings.append('Missing '+field+': '+segment['title'])
            audits.append({'id':job['id'],'pairs':len(evidence['frames']),'segments':len(segments),'warnings':warnings})
        assert len(set(texts))<=1, 'GPT text differs beyond supplied frame indices'
    run.common.write_json(run.OUT/'coverage_audit.json',audits)
    totals=run.report()
    unknown=sum(r['reserved_usd'] for r in rows.values() if r['id'] in totals['unknown_cost_requests'])
    lines=['# Points versus windows: results','',f'Completed {totals["completed"]}/20 calls. No annotation-quality scores are computed.','',
           f'Known generation estimate: ${totals["generation_estimate_usd"]:.6f}.',
           f'Conservative token-count allowance: ${totals["preflight_input_rate_allowance_usd"]:.6f}.',
           f'Unknown-charge reservations: ${unknown:.6f}.',
           f'Total conservative tracked exposure: ${totals["estimate_plus_preflight_allowance_usd"]+unknown:.6f} against $3.36.','',
           '## Pipeline costs (generation estimates)','',
           '| Episode | U uniform | SP + P points | SW + W windows |','|---|---:|---:|---:|']
    for eid in run.IDS:
        values=[]
        for arms in (('U',),('SP','P'),('SW','W')):
            rs=[rows.get(eid+'_'+a,{}) for a in arms]
            values.append(f'${sum(r["generation_estimate_usd"] for r in rs):.6f}' if all(r.get('generation_estimate_usd') is not None for r in rs) else 'incomplete/unknown')
        lines.append('| '+eid+' | '+' | '.join(values)+' |')
    lines+=['','## Annotation structure','','| Call | Camera pairs | Segments | Warnings |','|---|---:|---:|---|']
    for a in audits:lines.append(f'| {a["id"]} | {a["pairs"]} | {a["segments"]} | {"; ".join(a["warnings"]) or "none"} |')
    lines+=['','## Selected evidence','']
    for ep in manifest['episodes']:
        lines += [f'### {ep["id"]}', '', 'Overview: '+str(ep['overview'])]
        for selector in ('SP','SW'):
            p=run.OUT/ep['id']/selector/'freeze.json'
            if p.exists():
                selection=run.common.load(p)
                lines+=['',selector+': '+str(selection.get('windows',selection.get('points'))),
                        'GPT frames: '+str(selection['frames'])]
    lines+=['','## Limitations and checks','',
            'One sample per condition on previously inspected development episodes. More segments are not evidence of better annotation.',
            'Human review should separately judge identity evidence, before/after coverage of transitions, persistent failures, and GPT boundary/reason correctness.',
            'Windows also introduce denser source frames unavailable in the Gemini overview; this tests evidence allocation as a whole.',
            'Verified original candidate bytes, camera hashes, identical telemetry, equal GPT image budgets and common overview inclusion,',
            'identical GPT prompt/context except frame indices, frozen request payloads, selector expansions and usage-derived costs.',
            'Prices are estimates from recorded usage; token-count allowances are conservative, not observed invoice charges.','',
            '[Protocol](../../docs/frame_selection_windows_v1.md) | [Per-call costs](costs.csv) | [Viewer](web_review/index.html)']
    for r in rows.values():
        if r['status']=='stopped':lines+=['',r['id']+': '+r.get('error','stopped')]
    (run.OUT/'RESULTS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'completed':totals['completed'],'generation':totals['generation_estimate_usd'],'conservative_total':round(totals['estimate_plus_preflight_allowance_usd']+unknown,8),'audits':audits},indent=2))

if __name__=='__main__':main()
