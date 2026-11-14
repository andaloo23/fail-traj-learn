"""Full 400/50/50 frozen distillation study; no new teacher calls."""
import argparse
from collections import Counter
from datetime import datetime,timezone
import json
from pathlib import Path

import oopsie_common as common
import oopsie_recipe_data as data
import binary_segments_v9 as binary
import failure_enrichment_v8_1 as enrichment
from oopsie_bulk_v8_1 import write_once

ROOT=common.ROOT/'outputs/oopsie_distillation_full_v1'
CONFIG=common.ROOT/'configs/oopsie_distillation_full_v1.json'
TRAIN=['binary','joint','categories_aux','evidence_aux','both_aux','binary_compute_control','joint_then_binary','failure_balanced']


def native_value(source,e):
    folder=source/'traces'/f"{e['id']}_sol_r01"
    state=common.read(folder/'attempt.json')
    for name in ('annotation','response'):
        p=folder/('annotation.md' if name=='annotation' else 'response.json')
        if common.sha(p)!=state[name+'_sha256']:raise ValueError('Native teacher hash mismatch: '+e['id'])
    text=(folder/'annotation.md').read_text(encoding='utf-8')
    segments=binary.parse(text.split('## Failure annotations',1)[0],e)
    try:return enrichment.parse(text,e),None
    except ValueError as exc:
        return dict(episode_id=e['id'],segments=segments,failure_annotations=[]),str(exc)


def prepare():
    cfg=common.read(CONFIG);source=common.ROOT/cfg['source_run'];m=common.read(source/'manifest.json')
    if m['config']['teachers']!={'sol':'gpt-6.1-sol'}:raise ValueError('Sol-only corpus required')
    ROOT.mkdir(parents=True,exist_ok=True);episodes=[];values={}
    for e in m['episodes']:
        value,error=native_value(source,e);values[e['id']]=(value,error)
        folder=source/'traces'/f"{e['id']}_sol_r01"
        episodes.append(dict(episode=e['id'],split=e['split'],lab=e['lab'],n_frames=e['n_frames'],fps=e['fps'],
            annotation_sha256=common.sha(folder/'annotation.md'),response_sha256=common.sha(folder/'response.json'),
            binary_valid=True,auxiliary_valid=error is None,auxiliary_error=error,
            has_failure=any(x['failure'] for x in value['segments'])))
    counts=Counter(e['split'] for e in episodes)
    if counts!={'train':400,'development':50,'test':50}:raise ValueError('Unexpected split')
    study=dict(protocol=cfg['protocol'],config=cfg,source_manifest_sha256=common.sha(source/'manifest.json'),
        source_prompt_sha256=common.sha(source/'prompt.md'),episodes=episodes,
        training_order=[e['episode'] for e in episodes if e['split']=='train'],
        development_ids=[e['episode'] for e in episodes if e['split']=='development'],
        sealed_test_ids=[e['episode'] for e in episodes if e['split']=='test'],
        recipes={k:data.RECIPES[k] for k in ['base']+TRAIN},test_evaluation_enabled=False,
        new_teacher_calls_authorized_by_controller=False)
    write_once(ROOT/'study.json',study)
    folder=ROOT/'evidence_c32_x8_v3';folder.mkdir(exist_ok=True)
    adapter=dict(version='full_timestamp_overlapping_windows_v3',core_frames=32,context_frames=8,
        all_frames_retained=True,cameras='all native nonduplicate panels',student=cfg['student'],
        auxiliary_policy='Only fully visible intervals with valid native citations. Six training episodes use binary-only supervision in every arm; no fabricated None evidence.',
        limitation='Windows do not provide distant episode context; native teacher saw entire episodes.')
    write_once(folder/'adapter.json',adapter)
    output=folder/'records.jsonl';metadata=[];counts=Counter();files={}
    if output.exists():raise ValueError('Full-data export is frozen; do not overwrite it')
    with output.open('x',encoding='utf-8') as f:
        for e in m['episodes']:
            if e['split']=='test':continue
            value,error=values[e['id']]
            for image in e['images']:
                path=(source/image['path']).relative_to(common.ROOT).as_posix()
                files[path]=dict(path=path,bytes=image['bytes'],sha256=image['sha256'])
            for w in data.windows(e['n_frames'],32,8):
                tasks=['binary','joint'] if e['split']=='train' else ['binary']
                if error is None and e['split']=='train' and data.supported_details(value,w):
                    tasks+=['categories_aux','evidence_aux','both_aux']
                for task in tasks:
                    # Bad auxiliary fields do not invalidate valid primary labels,
                    # and never become a fabricated negative auxiliary target.
                    r=data.record(source,e,value,w,'binary' if error and task=='joint' else task)
                    if error and task=='joint':
                        r['id']=r['id'].removesuffix('_binary')+'_joint';r['task']='joint'
                        r['auxiliary_omitted_reason']=error
                    f.write(json.dumps(r,separators=(',',':'))+'\n');counts[e['split']+'_'+task]+=1
                    metadata.append({k:r[k] for k in ('id','episode','split','task','core_start','core_end','context_start','context_end','has_failure','eligible_aux_annotations')})
    if counts['train_binary']!=5376 or counts['development_binary']!=279:raise ValueError('Unexpected full-data window count')
    index=dict(protocol=cfg['protocol'],study_sha256=common.sha(ROOT/'study.json'),
        adapter_sha256=common.sha(folder/'adapter.json'),records_sha256=common.sha(output),counts=dict(counts),
        records=metadata,sealed_test_exported=False)
    write_once(folder/'index.json',index)
    write_once(ROOT/'image_inventory.json',dict(files=list(files.values()),bytes=sum(v['bytes'] for v in files.values()),test_images_staged=False))
    write_once(ROOT/'selected_adapter.json',dict(folder=folder.name,
        selection_basis='Predeclared shared 32-core/8-context adapter selected by training-only local memory benchmark; same evidence for all arms',
        benchmark_source='outputs/oopsie_distillation_recipes_v1/gpu_benchmark.json'))
    print(json.dumps(dict(root=str(ROOT),counts=dict(counts),image_files=len(files),image_bytes=sum(v['bytes'] for v in files.values()))),flush=True)


def freeze_plan():
    study=common.read(ROOT/'study.json');folder=ROOT/'evidence_c32_x8_v3';index=common.read(folder/'index.json')
    # Bind execution code as well as the data to the approved launch receipt.
    scripts=sorted(common.ROOT.glob('scripts/**/*.py'))+sorted(common.ROOT.glob('scripts/tacc/oopsie_full_*.sbatch'))
    code={str(p.relative_to(common.ROOT).as_posix()):common.sha(p) for p in scripts}
    plan=dict(protocol='oopsie_full_first_wave_jobs_v1',study_sha256=common.sha(ROOT/'study.json'),
        selected_adapter=folder.name,adapter_sha256=common.sha(folder/'adapter.json'),records_sha256=index['records_sha256'],
        code_sha256=code,training_episodes=400,development_episodes=50,sealed_test_episodes=50,
        final_test_used=False,new_teacher_calls=0,training_recipes=TRAIN,baseline='base',optimizer_updates=2688,
        primary_examples=10752,primary_windows_per_pass=5376,epochs=2,
        balanced_arm_schedule='One complete pass over all 400 episodes, then equal Yes/No window replay for the second-pass example budget',
        train_max_hours=22,development_max_hours=1.5,training_job_hours=24,
        training_gpu_su_ceiling=288,baseline_gpu_hours=2,baseline_gpu_su_ceiling=3,
        timing_gpu_hours=.5,timing_gpu_su_ceiling=.75,setup_cpu_hours=1,setup_cpu_su_ceiling=.143,
        tacc_su_ceiling=291.893,authorized_tacc_su_cap=300,tacc_account='IRI26045',
        partition='gpu-a100-small',parallel_training_jobs=3,automatic_requeue=False,
        automatic_closed_loop_runs=False,code_changes_require_revalidation=True)
    write_once(ROOT/'submission_plan.json',plan)
    write_once(ROOT/'submission_approval.json',dict(approved=True,
        user_instruction='ok i think this is a good start. lets submit the jobs.',
        scope='Full-data first wave: pretrained baseline plus eight SFT recipes; no teacher calls or final-test evaluation; <=300 TACC SUs.',
        plan_sha256=common.sha(ROOT/'submission_plan.json')))
    text='''# Full-data distillation first wave

Approved for submission by the user: “ok i think this is a good start. lets submit the jobs.”

400 training episodes, 50 development episodes, 50 sealed test episodes. Sol teacher outputs are reused; no new API calls. All arms start from the same pinned Qwen2.5-VL-7B model and share the same overlapping windows, retaining every source timestamp and camera panel.

| Recipe | Training supervision |
|---|---|
| Pretrained baseline | No training; evaluate Qwen directly. |
| Binary | Failure / non-failure Markdown timelines only. |
| Joint | Binary timelines plus visible categories and explanations in the same answer. |
| Category auxiliary | Binary timelines plus a separate category task. |
| Explanation auxiliary | Binary timelines plus a separate grounded explanation task. |
| Both auxiliary | Binary timelines plus a separate category-and-explanation task. |
| Extra-binary control | Extra binary examples with the same extra visual windows as auxiliary supervision. |
| Joint then binary | First pass joint targets; second pass binary targets. |
| Failure-balanced replay | First pass covers every training window; second-pass budget balances failure/non-failure windows. |

Ordinary SFT arms have two complete passes: 5,376 windows per pass, 10,752 primary examples, 2,688 updates with four primary examples per update. The balanced arm uses the same update budget with the sampling difference above. Auxiliary arms add one auxiliary example per update at weight 0.3; extra-binary control matches their visual exposure. Six episodes have invalid auxiliary citations: their valid binary targets remain in all arms, while their auxiliary text is omitted. Only fully visible, grounded intervals are used for auxiliary tasks. These are visible teacher explanations, not hidden reasoning traces.

Eight A100-small training jobs, at most three concurrent, each limited to 24 hours (22 hours training and 1.5 hours development generation, with loading/checkpoint overhead). The pretrained baseline gets two hours, training-only timing gets 30 minutes, and CPU setup gets one hour. Combined requested ceiling: **291.893 SUs**, below the 300-SU cap. Time-capped runs remain incomplete, with checkpoints preserved; no automatic requeue or duplicate retry.

Development reports include output validity, frame coverage/agreement, failure precision/recall/F1 and boundary errors. Agreement is imitation of Sol, not human-reference accuracy. Final test remains sealed. Feedback-loop experiments follow after checkpoints and drafts exist; they are not submitted in this wave.
'''
    (ROOT/'submission_plan.md').write_text(text,encoding='utf-8')
    print(json.dumps(dict(plan_sha256=common.sha(ROOT/'submission_plan.json'),approved=True,su_ceiling=plan['tacc_su_ceiling'])),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','freeze-plan']);a=p.parse_args()
    prepare() if a.command=='prepare' else freeze_plan()
