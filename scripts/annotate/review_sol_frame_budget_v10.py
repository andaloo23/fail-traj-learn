"""Add frame-budget comparisons to the existing local viewer; no API calls."""
import shutil
import api_sol_frame_budget_v10 as experiment
import api_taxonomy_approach_v7 as baseline
import api_label_pilot as common


def extend(target,episodes,choices):
    if not (experiment.OUT/'manifest.json').exists():return None
    experiment.verify()
    summary=experiment.report()
    results={(r['episode'],r['arm']):r for r in summary['results']}
    source={ep['id']:ep for ep in common.load(experiment.OUT/'manifest.json')['episodes']}
    for arm,label in experiment.ARMS.items():
        ident='frames_'+arm
        choices.append(dict(id=ident,label='Frames - 4 Hz vs '+label,
            columns={'openai':'Sol 4 Hz (V7, unchanged)','gemini':'Sol '+label},
            heading='Sol frame reduction - '+label))
        shutil.copyfile(experiment.OUT/('adaptive_prompt.txt' if arm=='adaptive' else 'prompt.txt'),target/(ident+'_prompt.txt'))
        for ep in episodes:
            eid=ep['id'];original=source[eid]
            result=results.get((eid,arm),{})
            frames=result.get('seen_frames',experiment.sampled(original,arm))
            path=experiment.OUT/f'{eid}_{arm}_annotation.json'
            annotation=common.load(path) if path.exists() else None
            if annotation is not None:baseline.validate(annotation,{**original,'sampled_frames':frames})
            final=result.get('final_call',(result.get('calls') or [''])[-1])
            answer=experiment.OUT/f'{final}_answer.txt';raw_link=None
            if answer.exists():
                raw_link=f'{ident}_{eid}_answer.txt';shutil.copyfile(answer,target/raw_link)
            ep['versions'][ident]={'openai':ep['versions']['v7']['openai'],'gemini':annotation}
            ep['statuses'][ident]={'openai':ep['statuses']['v7']['openai'],'gemini':dict(
                status=result.get('status','pending'),error=result.get('error',''),raw_link=raw_link,display_note='')}
            base=common.load(baseline.OUT/'attempts'/f'{eid}_openai.json')
            ep.setdefault('evidence_versions',{})[ident]={
                'openai':dict(frames=original['sampled_frames'],initial_frames=original['sampled_frames'],requests=[],
                    calls=1,cost=base['generation_estimate_usd'],allowance=base.get('preflight_allowance_usd',0)),
                'gemini':dict(frames=frames,initial_frames=result.get('initial_frames',experiment.sampled(original,arm)),
                    requests=result.get('requests',[]),calls=len(result.get('calls',[])),
                    cost=result.get('generation_estimate_usd'),allowance=result.get('preflight_allowance_usd',0))}
    return 'frames_adaptive'
