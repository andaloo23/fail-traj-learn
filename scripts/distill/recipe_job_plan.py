"""Concrete first-wave jobs; execution requires a separately recorded approval."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path

import oopsie_common as common
import annotation_runtime as transport
import oopsie_recipe_data as data
import qwen_recipe_runner as runner
import score_recipe_suite as scoring
from oopsie_bulk_v8_1 import write_once

ROOT=common.ROOT/common.read(data.CONFIG)['out']
LOCAL=['binary','base','failure_balanced']
TACC=['joint','categories_aux','evidence_aux','both_aux','binary_compute_control','joint_then_binary']


def plan(root):
    study=common.read(root/'study.json');selection=common.read(root/'selected_adapter.json')
    adapter=root/selection['folder'];index=common.read(adapter/'index.json')
    value=dict(protocol='oopsie_distillation_first_wave_jobs_v1',study_sha256=common.sha(root/'study.json'),
        selected_adapter=selection['folder'],adapter_sha256=common.sha(adapter/'adapter.json'),
        records_sha256=index['records_sha256'],training_episodes=50,development_episodes=50,
        final_test_used=False,new_teacher_calls=0,optimizer_updates=40,seed=study['config']['student']['seed'],
        local_jobs=LOCAL,tacc_gpu_jobs=TACC,tacc_setup_jobs=1,tacc_parallel_gpu_jobs=2,
        tacc_partition='gpu-a100-small',tacc_account='IRI26045',tacc_gpu_wall_hours_per_job=2,
        tacc_gpu_charge_su_per_hour=1.5,tacc_gpu_su_ceiling=18,
        tacc_setup_partition='vm-small',tacc_setup_wall_hours=1,tacc_setup_su_ceiling=.143,
        local_wall_hours_ceiling=6,train_wall_hours_per_job=1.25,development_wall_hours_per_job=.6,
        approval_required=True,automatic_closed_loop_runs=False,
        later_branches=['Qwen self-review inference','Fixed-reference error replay with a matched continuation control',
                        'Qwen self-revision distillation','Sol-assisted review and correction distillation',
                        'Preference/reward methods after valid draft/preference/reward artifacts exist'])
    write_once(root/'submission_plan.json',value)
    labels=dict(binary='Binary labels only',base='Pretrained Qwen, no training',failure_balanced='Binary labels with failure-balanced sampling',
        joint='Joint binary labels + visible categories/explanations',categories_aux='Binary task + category auxiliary task',
        evidence_aux='Binary task + explanation auxiliary task',both_aux='Binary task + both auxiliary targets',
        binary_compute_control='Extra binary examples matching auxiliary visual exposure',joint_then_binary='Joint supervision, followed by binary-only supervision')
    lines=['# First-wave distillation jobs for approval','',
        '**Prepared, not submitted.** The local memory/speed benchmark was explicitly resumed by the user; training/submission still requires confirmation.','',
        'All recipes use the same pinned Qwen2.5-VL-7B model, the same 50 training episodes, all 50 development episodes, and the same binary references. This is a bounded screening sweep, not full training on all 394 usable training episodes.','',
        f"The shared evidence adapter is `{selection['folder']}`. It retains every frame across overlapping windows, scores each timestamp once, and preserves the native camera panels. Windowed inputs cannot provide distant episode context. Final test stays sealed.",'',
        '| Run | Recipe | Where | Maximum runtime |','|---|---|---|---|']
    for name in LOCAL:lines.append(f"| {name} | {labels[name]} | Local Linux / 3090 | 2 hours |")
    for name in TACC:lines.append(f"| {name} | {labels[name]} | TACC A100-small | 2 hours |")
    lines+=['','## Limits and interpretation','',
        '- Eight SFT recipes: 40 optimizer updates each, one fixed seed. Pretrained Qwen and always-No/always-Yes controls provide baselines.',
        '- Each trained arm gets at most 1.25 hours for training and 0.6 hours for development generation; model loading and reporting fit within the 2-hour job.',
        '- Six TACC GPU jobs run at most two at a time. GPU ceiling: **18 SUs**. One CPU setup job adds at most **0.143 SU**. No GPU job is submitted before setup and local benchmark readiness.',
        '- The three local runs have a combined maximum of **6 hours**. New teacher API calls: **zero**.',
        '- Auxiliary tasks use only teacher evidence wholly visible in the student context. Limited eligible auxiliary coverage is reported; no unseen observations are supplied as grounded targets.',
        '- Equal primary-example exposure is maintained across ordinary SFT arms. The auxiliary-compute control gets the same extra visual windows as auxiliary training.',
        '- Time-capped or incomplete runs remain marked incomplete and are not ranked as completed comparisons.',
        '- Development scores report frame agreement, failure precision/recall/F1, IoU, boundary error, output validity, coverage and compute. Agreement with Sol is not human-reference accuracy.','',
        '## Later feedback experiments','',
        'The first binary checkpoint provides drafts for Qwen self-review and training-error replay. New Sol-assisted review, correction distillation, preference training and reward training need their own concrete input/budget plans after those drafts exist. They are not automatically launched under this first-wave plan.','',
        'Once the screening comparison is informative, finalists can expand to 200 and then 394 training episodes and additional seeds. That expansion is not submitted automatically.','',
        'Confirmation of this exact plan will be recorded separately before any training or cluster submission.','']
    (root/'submission_plan.md').write_text('\n'.join(lines),encoding='utf-8')
    return value


def require_approval(root):
    if (root/'submission_plan_superseded.json').exists():
        raise ValueError('The 50-episode screening plan is superseded; a full-data plan and matching user approval are required')
    path=root/'submission_approval.json'
    if not path.exists():raise ValueError('User confirmation is required before training/submission; see submission_plan.md')
    approval=common.read(path)
    if approval.get('approved') is not True or approval.get('plan_sha256')!=common.sha(root/'submission_plan.json'):
        raise ValueError('Approval does not match the concrete frozen job plan')
    return common.read(root/'submission_plan.json')


def run_arm(root,recipe):
    spec=require_approval(root)
    if recipe not in spec['local_jobs']+spec['tacc_gpu_jobs']:raise ValueError('Recipe outside approved first wave')
    folder=root/spec['selected_adapter']
    if common.sha(folder/'adapter.json')!=spec['adapter_sha256'] or common.sha(folder/'records.jsonl')!=spec['records_sha256']:
        raise ValueError('Approved evidence changed')
    states=root/'arm_states';states.mkdir(exist_ok=True);state_path=states/(recipe+'.json')
    if state_path.exists():raise ValueError('Prior arm exists; inspect its state instead of automatically duplicating a run')
    state=dict(recipe=recipe,status='running',started_utc=datetime.now(timezone.utc).isoformat(),plan_sha256=common.sha(root/'submission_plan.json'))
    write_once(state_path,state)
    try:
        adapter=None
        if recipe!='base':
            result=runner.train(folder,recipe,root/'runs'/recipe,updates=spec['optimizer_updates'],max_hours=spec['train_wall_hours_per_job'])
            adapter=Path(result['adapter']);state['training']=result
        generated=runner.generate(folder,root/'predictions'/recipe,adapter=adapter,split='development',max_hours=spec['development_wall_hours_per_job'] if recipe!='base' else 1.8)
        scored=scoring.score(folder,root/'predictions'/recipe)
        write_once(root/'arm_scores'/(recipe+'.json'),scored)
        scores={p.stem:common.read(p) for p in (root/'arm_scores').glob('*.json')}
        scoring.write_report(root,scores)
        state.update(status='completed' if generated['complete'] and (recipe=='base' or state['training']['completed_schedule']) else 'time_capped',generation=generated)
    except Exception as exc:
        state.update(status='failed',error=type(exc).__name__+': '+str(exc));raise
    finally:
        state['finished_utc']=datetime.now(timezone.utc).isoformat();transport.atomic_json(state_path,state)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['plan','run-arm','check-approval'])
    p.add_argument('--study',type=Path,default=ROOT);p.add_argument('--recipe')
    a=p.parse_args()
    if a.command=='plan':print(json.dumps(plan(a.study)),flush=True)
    elif a.command=='check-approval':require_approval(a.study);print('Approved exact plan verified.')
    else:run_arm(a.study,a.recipe)
