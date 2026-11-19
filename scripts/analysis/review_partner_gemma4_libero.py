"""Derived video review of preserved native LIBERO evaluation responses."""
import hashlib
import json
from pathlib import Path
import sys
from collections import Counter

import numpy as np

import verify_partner_gemma4_libero as job
import export_qwen_development_review as viewer

common=job.common
RUN=job.RUN


def findings(records):
    result=common.read(RUN/'results.json')
    if result['completed']!=50:return
    rows=[json.loads(line) for line in (RUN/'legacy_per_episode.jsonl').read_text().splitlines()]
    archived={r['id']:r for r in (json.loads(line) for line in (job.PRIOR/'received/sft_v3_per_episode.jsonl').read_text().splitlines())}
    assert {r['id'] for r in rows}==set(archived)
    issues=Counter();table=[];transitions=Counter()
    for r in rows:
        eid=r['id'];raw=common.read(RUN/'predictions'/f'{eid}.json');n=job.native._task_info(records[eid])['n_frames']
        value=job.legacy_module().parse_pred(raw['text']);reason=[]
        if raw.get('hit_max'):reason.append('output token limit')
        cursor=0
        for s in value.get('segments',[]) if isinstance(value,dict) else []:
            a,b=s.get('start_frame'),s.get('end_frame')
            if type(a) is not int or type(b) is not int:reason.append('boundary type');continue
            if b<=a:reason.append('zero/reversed length')
            if a<0 or b>n:reason.append('out of source bounds')
            if a!=cursor:reason.append('gap/overlap')
            cursor=b
        if cursor!=n:reason.append('does not end at source frame count')
        issues.update(set(reason))
        transitions[(archived[eid]['pred_has_failure'],r['pred_has_failure'])]+=1
        yes=lambda x:'Yes' if x else 'No'
        table.append(f'| [{eid}](review_labels/{eid}/partner.md) | {yes(r["teacher_has_failure"])} | {yes(r["pred_has_failure"])} | {yes(raw["schema_valid"])} | {yes(raw["timeline_valid"] and not raw.get("hit_max"))} | '+('; '.join(sorted(set(reason))) or 'Valid')+' |')
    actual=result['legacy_metrics'];old=result['archived_metrics'];strict=result['strict_frame_metrics']
    pct=lambda value:'N/A' if value is None else f'{100*value:.2f}%'
    lines=['# Partner Gemma on original LIBERO validation data','',
        'Completed all 50 original held-out episodes, disjoint from the 450 unique training episodes. No training or teacher calls. References are preserved gpt-6.1-sol annotations, not human ground truth.','',
        '[Open synchronized video review](review.html) · [Original prompt](prompt.md) · [Reproduction plan](plan.md)','',
        '| Metric | Partner archive | Reproduced |','| --- | ---: | ---: |']
    names={'parse_rate':'Parseable output','schema_valid_rate':'Expected fields and types','fail_acc':'Episode failure agreement',
        'fail_precision':'Episode failure precision','fail_recall':'Episode failure recall','fail_f1':'Episode failure F1',
        'frame_action_acc':'Frame action agreement','boundary_f1_tol5':'Action boundary F1 (±5 frames)',
        'failure_iou':'Mean episode temporal failure IoU','category_micro_f1':'Failure category micro F1'}
    for key,label in names.items():lines.append(f'| {label} | {100*old[key]:.2f}% | {100*actual[key]:.2f}% |')
    lines+=['',f'Strict complete, nonempty, gap-free episode timelines: **{result["strict_complete_episodes"]}/50**. After rejecting malformed whole-episode timelines, **{pct(strict["coverage"])}** of source frames have accepted predictions. Strict frame failure F1: **{pct(strict["failure_f1"])}**; failure precision **{pct(strict["failure_precision"])}**, recall **{pct(strict["failure_recall"])}**.','',
        'A strict rejection is not necessarily missing frames: an extra zero-length segment also invalidates the timeline. Invalid episodes remain Unknown in the strict score and reviewer; raw native output is preserved.','',
        'The earlier OopsieData experiment used a different dataset, windowed binary Markdown, and different auxiliary inputs. This run restores the original native LIBERO protocol. Differences between those experiments cannot isolate dataset shift from prompt/format/telemetry effects.','',
        'The original base commit and package lock were not supplied. This reproduction uses the declared base model pinned to revision '+common.read(RUN/'plan.json')['base_revision']+', the original supplied adapter (all 516 tensors loaded exactly), the original processor settings, and unchanged prompt construction. Batched and single encoding were checked for identical unpadded token IDs, modality markers, image pixels and image-position IDs. Greedy batched inference can differ numerically from single-item inference.','',
        'Archived schema validity only checked fields/types, so it does not establish complete frame coverage. Archived raw predictions were not supplied; archive coverage cannot be independently checked. Episode F1 and mean temporal failure IoU measure different things.','',
        '| Timeline issue | Episodes |','| --- | ---: |']
    lines += [f'| {key} | {value} |' for key,value in issues.most_common()]
    lines+=['','Counts can overlap across issue types.','',
        '| Episode | Reference has failure | Gemma has failure | Schema valid | Strict timeline valid | Timeline detail |',
        '| --- | --- | --- | --- | --- | --- |']+table
    (RUN/'findings.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    job.transport.atomic_json(RUN/'diagnostics.json',dict(timeline_issue_episodes=dict(issues),
        archived_to_reproduced_episode_failure=[dict(archived=a,reproduced=b,episodes=count) for (a,b),count in sorted(transitions.items())]))


def media(eid,info):
    import av
    from PIL import Image
    source=job.REPO/'outputs/sol_v8_distillation_500/source'/eid/'cameras.npz'
    videos=[];checks={}
    with np.load(source) as cameras:
        for camera in ['agent','wrist']:
            frames=cameras[camera]
            assert frames.shape==(info['n_frames'],256,256,3) and frames.dtype==np.uint8
            reference=np.asarray(Image.open(job.SOURCE/f'images/{eid}/0000_{camera}.jpg').convert('RGB'))
            delta=float(np.abs(frames[0].astype(float)-reference).mean())
            assert delta<8, f'Camera orientation/color mismatch: {eid}/{camera}: {delta}'
            path=RUN/f'media/{eid}/{camera}.mp4';path.parent.mkdir(parents=True,exist_ok=True)
            if not path.exists():
                temp=path.with_suffix('.tmp.mp4')
                with av.open(str(temp),'w') as container:
                    stream=container.add_stream('libx264',rate=int(info['fps']))
                    stream.width=256;stream.height=256;stream.pix_fmt='yuv420p'
                    stream.options={'crf':'18','preset':'fast','threads':'2'}
                    for index,array in enumerate(frames):
                        frame=av.VideoFrame.from_ndarray(array,format='rgb24');frame.pts=index
                        for packet in stream.encode(frame):container.mux(packet)
                    for packet in stream.encode():container.mux(packet)
                temp.replace(path)
            with av.open(str(path)) as container:
                stream=container.streams.video[0]
                assert stream.frames==info['n_frames'] and float(stream.average_rate)==float(info['fps'])
            videos.append(dict(camera=camera,description='Full native LIBERO frames',url=path.relative_to(RUN).as_posix()))
            checks[camera]=dict(source_first_frame_jpeg_mean_absolute_difference=delta,sha256=common.sha(path),frames=len(frames))
    return videos,dict(source_npz_sha256=common.sha(source),cameras=checks)


def converted(value):
    prefix='# Derived readable conversion\n\nConverted from preserved native JSON; not a native Markdown generation.\n\n'
    try:return prefix+job.oopsie_markdown.render(value)
    except (KeyError,TypeError,ValueError):
        lines=[prefix,'| Start frame | End frame | Failure | Action | Observed result |',
            '| --- | --- | --- | --- | --- |']
        for s in value.get('segments',[]) if isinstance(value,dict) else []:
            lines.append('| '+' | '.join(str(s.get(k,'')).replace('|','/').replace('\n',' ') for k in ['start_frame','end_frame','failure','action','observed_result'])+' |')
        return '\n'.join(lines)


def main():
    plan=common.read(RUN/'plan.json');records=job.records();objects=[];hashes={};checks={}
    template=viewer.make_template().replace('Qwen development comparison','Gemma native LIBERO comparison')
    template=template.replace("video.preload='metadata'","video.preload='auto'")
    template=template.replace("'qwen-development-'","'gemma-libero-native-'")
    template=template.replace('Five completed Qwen variants and the Sol reference on all 50 development episodes.',
        'Original LIBERO holdout: partner Gemma adapter and preserved Sol reference. Native JSON converted to readable Markdown.')
    template=template.replace('Saved window outputs (derived compilation)','Readable conversion of native JSON')
    template=template.replace('Download stitched timeline (derived)','Download readable annotation (derived)')
    template=template.replace('Frozen V8.1 prompt','Original student prompt')
    for eid in plan['episode_ids']:
        info=job.native._task_info(records[eid]);n=info['n_frames'];tracks={}
        truth=json.loads(records[eid]['messages'][1]['content'])
        label_dir=RUN/'review_labels'/eid;label_dir.mkdir(parents=True,exist_ok=True)
        predictions=RUN/'predictions'/f'{eid}.json'
        sources=[('sol',truth,None)]
        if predictions.exists():
            raw=common.read(predictions);hashes[eid]=common.sha(predictions)
            sources.append(('partner',job.legacy_module().parse_pred(raw['text']),raw))
        for name,value,raw in sources:
            invalid=None
            try:
                if raw and raw['hit_max']:raise ValueError('Token cap reached')
                labels=job.timeline(value,eid,n)
            except (ValueError,TypeError,AttributeError) as error:
                invalid=str(error);labels=[None]*n
            text=converted(value)
            if invalid:text='Strict timeline: invalid; shown as Unknown. Reason: '+invalid+'\n\n'+text
            (label_dir/f'{name}.md').write_text(text,encoding='utf-8')
            trace=dict(repeat=1,segments=viewer.runs(labels),native_markdown=text,
                markdown=f'review_labels/{eid}/{name}.md',markdown_is_derived=True)
            if not invalid and job.legacy_module().schema_ok(value):trace['rich_segments']=value['segments']
            tracks[name]=[trace]
        tracks.setdefault('partner',[])
        videos,checks[eid]=media(eid,info)
        objects.append(dict(id=eid,task=info['task'],split='original validation',lab='LIBERO object suite',
            fps=info['fps'],n_frames=n,videos=videos,teachers=tracks,source_run='sol_v8_distillation_500'))
    review=dict(protocol='partner_gemma4_libero_native_review_v1',manifest_sha256=common.sha(RUN/'plan.json'),
        review_ui_version=hashlib.sha256(template.encode()).hexdigest(),prompt_revision='Gemma native LIBERO',
        side_labels=dict(sol='Sol reference (preserved)',partner='Partner Gemma adapter'),side_repeats=dict(sol=1,partner=1),
        planned_responses=100,repeats=1,episodes=objects,
        rich_prompt_description='Exact 50 original held-out LIBERO episodes. Whole-episode native JSON, original telemetry and camera sampling. Gray = invalid timeline. Sol is a teacher reference, not human ground truth. Readable annotations are derived conversions.')
    encoded=json.dumps(review,ensure_ascii=False).replace('<','\\u003c').replace('\u2028','\\u2028').replace('\u2029','\\u2029')
    job.transport.atomic_json(RUN/'review_data.json',review)
    (RUN/'review.html').write_text(template.replace('__DATA__',encoded),encoding='utf-8')
    job.transport.atomic_json(RUN/'review_provenance.json',dict(source_prediction_sha256=hashes,media=checks,annotations_are_derived_conversions=True))
    if hashes:findings(records)
    print(f'Review ready: 50 episodes, {len(hashes)} model responses, 100 full-camera videos.',flush=True)


if __name__=='__main__':main()
