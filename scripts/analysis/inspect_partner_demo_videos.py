"""Read-only inspection of supplied demo MP4s and D0160 source frames."""
import json
from pathlib import Path

import av
import numpy as np
from PIL import Image,ImageDraw,ImageFont

REPO=Path(__file__).resolve().parents[2]
RUN=REPO/'outputs/partner_gemma4_libero_native_20261113_v1'
OUT=RUN/'example_video_audit_D0160_v1'
FILES=['PeA1huGwwyDkOrXnu5pjQQ.mp4','tpoyLMQ_gZJEHmEsEFNNYw.mp4']
PALETTE={'reach':(66,133,244),'grasp':(251,188,5),'transport':(52,168,83),
    'release':(171,71,188),'withdraw':(0,172,193),'idle':(120,130,145),'regrasp':(255,112,67)}


def recover_bar(pictures,y,n):
    """Recover rendered bars, not raw predictions, at native-frame resolution."""
    names=list(PALETTE);colors=np.array(list(PALETTE.values()),dtype=int)
    labels=[];flags=[]
    for f in range(n):
        x=round(270+(f+.5)*970/n);votes=[];failure_votes=[]
        for picture in pictures:
            region=picture[y+8:y+36,x-1:x+2].astype(int).reshape(-1,3)
            distance=np.abs(region[:,None,:]-colors[None,:,:]).max(2)
            valid=distance.min(1)<45
            if valid.any():votes.append(int(np.bincount(distance[valid].argmin(1),minlength=len(names)).argmax()))
            top=picture[y+2:y+4,x-1:x+2].astype(int).reshape(-1,3)
            red=np.array([(255,80,80),(150,90,95)])
            red_distance=np.abs(top[:,None,:]-red[None,:,:]).max(2).min(1)
            failure_votes.append(bool(np.count_nonzero(red_distance<32)>=len(top)//2))
        labels.append(names[int(np.bincount(votes,minlength=len(names)).argmax())] if votes else 'unknown')
        flags.append(sum(failure_votes)>len(failure_votes)//2)
    segments=[]
    for f,(action,failure) in enumerate(zip(labels,flags)):
        if segments and (segments[-1]['action'],segments[-1]['failure'])==(action,failure):segments[-1]['end_frame']=f+1
        else:segments.append(dict(start_frame=f,end_frame=f+1,action=action,failure=failure))
    return labels,segments


def compare_bars():
    import hashlib
    def sha(path):
        with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
    review=json.loads((RUN/'review_data.json').read_text(encoding='utf-8'))
    episodes={e['id']:e for e in review['episodes']}
    specifications=[(FILES[0],False,[('D0160',[50,83,166]),('D0219',[249,300,332]),('D0008',[453,499,582])]),
        (FILES[1],True,[('D0185',[50,91,181]),('D0173',[249,272,362]),('D0142',[453,499,544])])]
    recovered=[]
    for name,v3,examples in specifications:
        frames_to_read={i for _,indices in examples for i in indices};pictures={}
        with av.open(str(Path('C:/Users/LocalPC/Downloads')/name)) as container:
            for i,frame in enumerate(container.decode(video=0)):
                if i in frames_to_read:pictures[i]=frame.to_ndarray(format='rgb24')
        for eid,indices in examples:
            e=episodes[eid];n=e['n_frames'];raw=json.loads((RUN/'parsed'/f'{eid}.json').read_text(encoding='utf-8'))
            truth=e['teachers']['sol'][0]['rich_segments'];tlabels=[None]*n
            for s in truth:tlabels[s['start_frame']:s['end_frame']]=[s['action']]*(s['end_frame']-s['start_frame'])
            extracted={}
            for k,y in [('teacher',435 if v3 else 425),('base',497 if v3 else 487),('sft',559 if v3 else 549)]:
                labels,segs=recover_bar([pictures[i] for i in indices],y,n)
                extracted[k]=dict(segments=segs,frame_action_agreement_vs_frozen_sol=sum(a==b for a,b in zip(labels,tlabels))/n)
            recovered.append(dict(video=name,video_version='v3' if v3 else 'earlier unversioned SFT',episode=eid,
                source_frames=n,bar_coordinates=dict(start_x=270,end_x=1240),
                recovered_from_pixels=True,rendered_boundaries_approximate=True,tracks=extracted,
                numeric_score_recovery_passes_teacher_control=extracted['teacher']['frame_action_agreement_vs_frozen_sol']==1.0,
                pixel_recovery_limitation='Failure hatching/outlines can obscure action colors. If the teacher control is below 100%, these approximate pixel estimates must not be used as reconstructed scores; use the archived native per-episode scores instead.',
                rerun_segments=raw['segments']))
    # Verify the D0160 camera pictures against the preserved source JPEG image.
    folder=OUT/Path(FILES[0]).stem;demo=np.asarray(Image.open(folder/'frame_00166.jpg').convert('RGB'))
    camera_checks=[]
    for camera,x in [('agent',40),('wrist',400)]:
        source=REPO/f'outputs/sol_v8_distillation_500/export_v1/images/D0160/0115_{camera}.jpg'
        assert source.exists()
        expected=np.asarray(Image.open(source).convert('RGB').resize((340,340),Image.Resampling.LANCZOS)).astype(float)
        actual=demo[60:400,x:x+340].astype(float)
        mad=float(np.abs(actual[40:]-expected[40:]).mean())
        camera_checks.append(dict(camera=camera,demo_frame=166,displayed_playhead=117,
            actual_sampled_source_frame=115,mean_absolute_rgb_difference_excluding_camera_caption=mad,source_sha256=sha(source)))
        assert mad<8,'Demo/source camera mismatch'
    (OUT/'recovered_demo_bars.json').write_text(json.dumps(recovered,indent=2)+'\n',encoding='utf-8')
    (OUT/'camera_checks.json').write_text(json.dumps(camera_checks,indent=2)+'\n',encoding='utf-8')
    print('Recovered timeline action agreement from MP4 pixels:')
    for r in recovered:
        print(r['video_version'],r['episode'],{k:round(v['frame_action_agreement_vs_frozen_sol'],6) for k,v in r['tracks'].items()},
            'failure_runs',[(s['start_frame'],s['end_frame']) for s in r['tracks']['sft']['segments'] if s['failure']])
    print('D0160 camera checks:',camera_checks)


def write_report():
    import hashlib
    def sha(path):
        with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
    received=REPO/'outputs/partner_gemma4_archive_20261113_v1/received'
    rows=[json.loads(line) for line in (RUN/'legacy_per_episode.jsonl').read_text().splitlines()]
    current={r['id']:r for r in rows}
    old={r['id']:r for r in (json.loads(line) for line in (received/'sft_v3_per_episode.jsonl').read_text().splitlines())}
    initial={r['id']:r for r in (json.loads(line) for line in (received/'sft_per_episode.jsonl').read_text().splitlines())}
    logs=[json.loads(line) for line in (received/'train_log.jsonl').read_text().splitlines()]
    train={r['id'] for r in logs if r.get('event')=='example'}
    review=json.loads((RUN/'review_data.json').read_text(encoding='utf-8'))
    episode=next(e for e in review['episodes'] if e['id']=='D0160')
    teacher=episode['teachers']['sol'][0]['rich_segments']
    prediction=json.loads((RUN/'parsed/D0160.json').read_text(encoding='utf-8'))['segments']
    key=lambda s:(s['start_frame'],s['end_frame'],s['action'],s['failure'])
    assert [key(s) for s in teacher]==[key(s) for s in prediction]
    assert 'D0160' not in train and len(train)==450 and current['D0160']['frame_action_acc']==1
    assert not any(s['failure'] or s['categories'] for s in prediction)
    assert prediction[-1]['review_required'] and teacher[-1]['review_required']
    # The demo's documented near() rule can credit both references without overlap.
    p=dict(start_frame=105,end_frame=135)
    qs=[dict(start_frame=80,end_frame=95),dict(start_frame=135,end_frame=140)]
    near=lambda a,b:a['start_frame']-10<=b['end_frame'] and b['start_frame']-10<=a['end_frame']
    overlap=lambda a,b:max(0,min(a['end_frame'],b['end_frame'])-max(a['start_frame'],b['start_frame']))
    assert all(near(q,p) and overlap(q,p)==0 for q in qs)
    verified=REPO/'outputs/distill/eval_verified.json'
    failure_summary=REPO/'outputs/distill/scores_failures/summary.json'
    checks=dict(episode='D0160',source_frames=150,fps=20,in_recorded_training_ids=False,recorded_training_ids=450,
        teacher_and_rerun_action_intervals_identical=True,frame_action_agreement=1.0,boundary_f1=1.0,
        predicted_failure_segments=0,teacher_failure_segments=0,release_success_unverified=True,
        original_demo_predictions_available=False,verified_failure_reference_available=verified.exists(),
        original_verified_failure_score_summary_available=failure_summary.exists(),
        near_rule_zero_overlap_many_to_one_example=dict(prediction=p,references=qs,hits=2,overlap_frames=0),
        code_sha256={str(x.relative_to(REPO)):sha(x) for x in [REPO/'scripts/distill/make_video.py',REPO/'scripts/distill/score_failures.py']})
    (OUT/'verification.json').write_text(json.dumps(checks,indent=2)+'\n',encoding='utf-8')
    lines=['# Audit of the supplied Gemma demo videos and D0160','',
        '**D0160’s action-segmentation example checks out in the new inference run.** Its four action boundaries match Sol exactly, and it is absent from the 450 recorded LoRA training IDs. This is evidence for action segmentation on a clean held-out LIBERO example. It does not measure failure localization or failure-category/explanation quality, because neither Sol nor Gemma marks a failure here.','',
        'The supplied MP4 files were read without alteration. Their hashes and extracted screenshots are saved in this audit. The D0160 camera images also match the preserved source imagery: at demo playhead 117 the renderer shows sampled source frame 115, with mean RGB differences around 2.2/255 after excluding the camera caption. This is consistent with JPEG/H.264 compression.','',
        '| D0160 action | Frames, end exclusive | Source time | Sol vs current Gemma |',
        '| --- | --- | --- | --- |']
    for s in prediction:
        lines.append(f'| {s["action"]} | [{s["start_frame"]}, {s["end_frame"]}) | {s["start_frame"]/20:.2f}–{s["end_frame"]/20:.2f} s | Exact match |')
    lines+=['',
        'The demo’s 100% and the rerun’s 100% mean **per-frame action agreement with the teacher**. They do not mean 100% failure accuracy, category accuracy, explanation correctness, or verified task completion. D0160 contains no positive failure labels, so its failure F1/IoU is undefined. The base model’s archived per-episode action agreement is 0%, consistent with the video; its original raw response is unavailable, so that base output was not independently rerun here.','',
        '**Action versus failure category:** reach, grasp, transport and release are atomic actions. The earlier audit’s finding that all 31 predicted failure categories were grasp referred only to failure=true segments across the validation set. Gemma does generate other action labels on normal segments; these are different fields.','',
        'The source frames support approach, acquisition and carriage into the basket opening. The final frames do not clearly establish separation and independent basket support. Both the saved Sol annotation and Gemma rerun correctly flag the release for review. Gemma’s specific identity claim about a white ketchup label/red cap is not clearly supported by the inspected wrist view at frame 30; matching action labels does not validate every textual claim.','',
        '[D0160 normal-speed comparison MP4](../presentation_explanations_1x_v1/episodes/D0160_explanations_1x.mp4) · [Gemma annotation](../readable/D0160.md) · [Sol annotation](../review_labels/D0160/sol.md)','',
        '## What the two supplied videos show','',
        '| File | Version shown | Selected examples | Relevant distinction |',
        '| --- | --- | --- | --- |',
        '| PeA1huGwwyDkOrXnu5pjQQ.mp4 | Earlier unversioned SFT | D0160, D0219, D0008 | Final card says failure labels were mostly masked; it explicitly says the student does not yet predict failures. Its aggregate card uses n=40. |',
        '| tpoyLMQ_gZJEHmEsEFNNYw.mp4 | v3 SFT | D0185, D0173, D0142 | Adds failure supervision, telemetry-derived gripper events and 5x failure/category weighting; reports n=50. |','',
        'The checked-in renderer hard-codes these showcase episode IDs; they are selected demonstrations, not a random audit sample. It uses sparse source JPEGs, selecting the last sampled frame at or before the playhead, and gives each episode 11 seconds of presentation time. This differs from native continuous 20 FPS playback.','',
        '| Example | Demo action agreement | Supplied archive | Our rerun |',
        '| --- | ---: | ---: | ---: |']
    for eid,version,demo in [('D0160','earlier',100),('D0219','earlier',100),('D0008','earlier',99),('D0185','v3',73),('D0173','v3',95),('D0142','v3',83)]:
        archived=initial[eid] if version=='earlier' else old[eid]
        lines.append(f'| {eid} ({version}) | {demo}% rounded | {archived["frame_action_acc"]*100:.2f}% | {current[eid]["frame_action_acc"]*100:.2f}% |')
    lines+=['',
        'D0160 and D0219 reproduce exactly; D0142 also reproduces its archived action score. D0173 and D0185 differ in the new rerun. We preserved these differences rather than replacing predictions with the demo labels. The rerun uses the supplied v3 adapter; the first video shows an earlier SFT version. The original base commit, package lock, and raw original model requests/predictions are absent, so the cause of v3 output differences cannot be isolated here. This is a reproducibility limitation, not proof that the video was fabricated.','',
        '## Failure scoring in the demo requires careful interpretation','',
        'The renderer’s failure claims use scripts/distill/score_failures.py. Its near(a,b) predicate allows intervals to be separated by up to 10 source frames (0.5 seconds at 20 FPS). Segment recall asks whether each reference has any nearby prediction; it does not enforce one-to-one matches. Category match on hits asks whether any nearby prediction shares any category with the reference; it is not exact multi-label category accuracy.','',
        'A concrete consequence using D0185’s displayed approximate long early failure span [105,135): this one prediction is near both the frozen Sol collision interval [80,95) and dropped-grasp interval [135,140), while overlapping neither under half-open intervals. It can therefore receive two caught-reference credits under that rule. The original adjudicated eval_verified.json is unavailable, so this example illustrates the implemented rule against the frozen Sol intervals rather than reconstructing the missing adjudicated labels.','',
        'That rule can explain why a caption such as caught 5/5 appears alongside an extra flag and much weaker failure-frame overlap. It does not establish five independent correctly localized failures, and the same metric should not be compared directly with strict per-frame recall or one-to-one event matching.','',
        'The v3 video also reports 38% failure segments caught and 83% category correctness when caught. These depend on outputs/distill/eval_verified.json and scores_failures/summary.json, neither of which is in the provided archive or current expected local paths. The label frame-verified does not itself establish who performed the verification or whether it was independent human review. Those figures remain unverified from the supplied materials.','',
        'The renderer additionally defines hard-coded fallback aggregate statistics and uses them if score files cannot be loaded. The values match the displayed round numbers. This does not show the fallback was used to produce these MP4s; it means a rendered score card alone is not sufficient evidence for the underlying calculation. The supplied per-episode score rows independently support several of the action/episode aggregates.','',
        'The v3 final slide itself acknowledges that the model remains below a simple telemetry rule on grasp failures and reports difficulty with wrong-object picks. The LIBERO inputs include real robot telemetry and derived gripper events; these demonstrations do not establish equivalent vision-only performance.','',
        '## Assessment','',
        'D0160 is a valid, reproducible demonstration of the adapter producing reach/grasp/transport/release labels on a clean example. The stronger claim of reliable failure understanding is not established by that example. The separate v3 failure video uses permissive event matching, selected examples, and references whose underlying adjudication artifacts were not provided. Overall action agreement approximately reproduces in our 50-episode rerun, while strict temporal failure localization remains weak.','',
        'A full authentication of the v3 failure claims would require the original raw predictions, exact model/base/software revisions, the adjudicated eval_verified.json with reviewer provenance, and the actual failure-score summary. No new model inference or training was launched for this video/source audit.','',
        '## Evidence snapshots','',
        '![D0160 action demonstration](PeA1huGwwyDkOrXnu5pjQQ/frame_00166.jpg)','',
        '![D0160 source acquisition](D0160_source/frame_065.png)','',
        '![D0160 final source observation](D0160_source/frame_149.png)','',
        '![Earlier SFT limitations card](PeA1huGwwyDkOrXnu5pjQQ/frame_00665.jpg)','',
        '![v3 results card](tpoyLMQ_gZJEHmEsEFNNYw/frame_00634.jpg)','',
        '![v3 methods and limitations card](tpoyLMQ_gZJEHmEsEFNNYw/frame_00725.jpg)','']
    (OUT/'report.md').write_text('\n'.join(lines),encoding='utf-8')
    print('D0160 source/teacher/rerun checks and demo scoring audit complete.')


def main():
    import hashlib
    OUT.mkdir(exist_ok=True);rows=[]
    for name in FILES:
        path=Path('C:/Users/LocalPC/Downloads')/name
        with path.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
        folder=OUT/path.stem;folder.mkdir(exist_ok=True)
        with av.open(str(path)) as container:
            s=container.streams.video[0]
            info=dict(name=name,sha256=digest,dimensions=[s.width,s.height],fps=str(s.average_rate),
                stream_frames=s.frames,duration_seconds=container.duration/av.time_base,metadata=dict(container.metadata),stream_metadata=dict(s.metadata))
            wanted={0,max(0,s.frames-1),*[round(i*(s.frames-1)/8) for i in range(1,8)]}
            samples=[]
            for i,frame in enumerate(container.decode(video=0)):
                if i not in wanted:continue
                output=folder/f'frame_{i:05d}.jpg';frame.to_image().save(output,quality=97)
                samples.append(dict(frame=i,seconds=float(frame.pts*frame.time_base),file=output.relative_to(OUT).as_posix()))
            info['sample_frames']=samples;rows.append(info)
    data=np.load(REPO/'outputs/sol_v8_distillation_500/source/D0160/cameras.npz')
    folder=OUT/'D0160_source';folder.mkdir(exist_ok=True)
    for f in [0,30,45,50,55,60,65,70,100,130,140,145,149]:
        image=Image.new('RGB',(512,296),'#101722');d=ImageDraw.Draw(image)
        d.text((10,5),f'D0160 source frame {f}, {f/20:.2f}s',font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',23),fill='white')
        image.paste(Image.fromarray(data['agent'][f]),(0,40));image.paste(Image.fromarray(data['wrist'][f]),(256,40))
        image.save(folder/f'frame_{f:03d}.png')
    (OUT/'video_metadata.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(rows,indent=2))
    compare_bars()
    write_report()


if __name__=='__main__':main()
