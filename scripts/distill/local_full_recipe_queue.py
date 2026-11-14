"""Approved sequential full-data Qwen experiments on the local Linux GPU.

Uses the original frozen study and evidence. Each phase is a fresh process so
training and evaluation models never overlap in VRAM. No automatic retry,
teacher calls, test evaluation, or reduced training subset.
"""
import argparse
from datetime import datetime,timezone
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import oopsie_full_jobs as frozen

ROOT=frozen.REPO/'outputs/oopsie_distillation_local_sequential_v1'
RECIPES=['base','binary','joint','categories_aux','evidence_aux','both_aux','binary_compute_control','joint_then_binary','failure_balanced']
CHILD=None


def now():return datetime.now(timezone.utc).isoformat()


def save(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name(path.name+'.tmp')
    temporary.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8');temporary.replace(path)


def freeze(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        if frozen.read(path)!=value:raise ValueError('Refusing to rewrite frozen local artifact: '+str(path))
    else:
        with path.open('x',encoding='utf-8') as stream:json.dump(value,stream,indent=2);stream.write('\n')


def prepare():
    parent,folder=frozen.approval()
    source=frozen.read(frozen.ROOT/'study.json')
    execution_files=[Path(__file__),Path(__file__).with_name('run_local_full_queue.sh')]
    plan=dict(protocol='oopsie_full_local_sequential_v1',parent_plan_sha256=frozen.digest(frozen.ROOT/'submission_plan.json'),
        study_sha256=parent['study_sha256'],records_sha256=parent['records_sha256'],adapter_sha256=parent['adapter_sha256'],
        source_study=str(frozen.ROOT.relative_to(frozen.REPO).as_posix()),data=str(folder.relative_to(frozen.REPO).as_posix()),
        recipes=RECIPES,training_episodes=400,development_episodes=50,sealed_test_episodes=50,
        optimizer_updates=2688,training_passes=2,primary_examples=10752,
        student=source['config']['student'],train_max_hours_per_recipe=72,evaluation_max_hours_per_recipe=6,
        hardware='NVIDIA GeForce RTX 3090 24 GB',gpu_concurrency=1,
        model_cache='/home/aliu/.cache/ftl-qwen-hub',python='/home/aliu/.venvs/ftl-oopsie-recipes-v1/bin/python',
        evidence='Unchanged native-frame windows; all 400 training episodes. No thinning or screening subset.',
        automatic_retry=False,new_teacher_calls=0,test_used=False,
        duplicate_policy='All nine first-wave arms assigned to this local queue. Do not resubmit them to TACC while locally owned; the existing TACC setup is preparation only.',
        execution_sha256={str(p.relative_to(frozen.REPO).as_posix()):frozen.digest(p) for p in execution_files})
    freeze(ROOT/'plan.json',plan)
    freeze(ROOT/'approval.json',dict(approved=True,user_instruction='ok lets also run things sequentially on thsi gpu',
        plan_sha256=frozen.digest(ROOT/'plan.json'),scope='Existing full-data first wave on the local GPU, one arm at a time; baseline first, then eight SFT arms.'))
    (ROOT/'plan.md').write_text('''# Local sequential distillation queue

Approved by the user: “ok lets also run things sequentially on thsi gpu”.

The pretrained baseline runs first, followed by binary, joint, category auxiliary,
explanation auxiliary, both auxiliary, extra-binary control, joint-then-binary and
failure-balanced replay. One GPU process runs at a time. A fresh process loads
the saved adapter for evaluation after training exits and releases its memory.

The same frozen 400 training episodes, 50 development episodes, student model,
native-frame windows, targets, seed and 2,688-update schedule are reused from the
full-data study. The final 50 test episodes remain sealed. No teacher API calls.
The balanced recipe retains its approved first-pass coverage / second-pass
balanced replay schedule. Auxiliary eligibility remains unchanged.

Each trained arm has a 72-hour training ceiling and a six-hour development
generation ceiling; completed schedules exit sooner. These ceilings allow the
slower local GPU to finish the same update schedule. A ceiling hit remains
incomplete. Checkpoints and optimizer state are preserved by the frozen trainer.
An errored phase stops the queue rather than retrying silently. No completed or
partially started experiment is overwritten or silently restarted.

All nine arms are owned by this queue; overlapping TACC GPU runs must not be
submitted without reassigning ownership. The pending TACC CPU setup can finish
independently. Its failed original GPU dependents are not active jobs.

Progress: `status.md`; controller state: `queue.json`; per-phase logs: `logs/`;
checkpoints: `runs/`; readable predictions: `predictions/`; scores: `results.md`.
Create `STOP_AFTER_CURRENT` to stop after the current recipe finishes. To release
the GPU immediately, terminate the recorded controller PID; it forwards the
termination to its child and records the interruption.
''',encoding='utf-8')
    print(json.dumps(dict(prepared=True,root=str(ROOT),recipes=len(RECIPES))),flush=True)


def approved():
    parent,folder=frozen.approval();plan=frozen.read(ROOT/'plan.json');approval=frozen.read(ROOT/'approval.json')
    if approval.get('approved') is not True or approval.get('plan_sha256')!=frozen.digest(ROOT/'plan.json'):
        raise ValueError('Local user approval does not match the frozen plan')
    if plan['parent_plan_sha256']!=frozen.digest(frozen.ROOT/'submission_plan.json'):
        raise ValueError('Canonical first-wave plan changed')
    for rel,expected in plan['execution_sha256'].items():
        if frozen.digest(frozen.REPO/rel)!=expected:raise ValueError('Local queue code changed: '+rel)
    return plan,folder


def worker(recipe,phase):
    plan,folder=approved()
    if recipe not in plan['recipes']:raise ValueError('Unapproved local arm')
    import qwen_recipe_runner as runner
    if phase=='train':
        result=runner.train(folder,recipe,ROOT/'runs'/recipe,updates=plan['optimizer_updates'],max_hours=plan['train_max_hours_per_recipe'])
    elif phase=='generate':
        adapter=None if recipe=='base' else Path(frozen.read(ROOT/'runs'/recipe/'completion.json')['adapter'])
        result=runner.generate(folder,ROOT/'predictions'/recipe,adapter=adapter,split='development',max_hours=plan['evaluation_max_hours_per_recipe'])
    else:raise ValueError('Unknown phase')
    print(json.dumps(result),flush=True)


def status(state):
    state['updated_utc']=now();save(ROOT/'queue.json',state)
    lines=['# Local distillation queue','',f"**{state['status']}** · updated {state['updated_utc']}",'',
        'RTX 3090 · one recipe at a time · 400 train / 50 development · 50 test sealed · no new teacher calls.','',
        '| Recipe | Status | Training updates | Development windows returned |','|---|---|---:|---:|']
    for name in RECIPES:
        arm=state['arms'].get(name,{})
        log=ROOT/'runs'/name/'train.jsonl';step=0
        if log.exists():
            try:step=json.loads(log.read_text(encoding='utf-8').splitlines()[-1])['step']
            except (IndexError,ValueError):pass
        returned=len(list((ROOT/'predictions'/name).glob('*_binary.json')))
        lines.append(f"| {name} | {arm.get('status','queued')} | {'—' if name=='base' else str(step)+'/2688'} | {returned}/279 |")
    if state.get('error'):lines+=['',f"Error: {state['error']}"]
    lines+=['','Training and generation logs are in `logs/`. Time-capped runs are incomplete; invalid predictions count against coverage and agreement.','']
    (ROOT/'status.md').write_text('\n'.join(lines),encoding='utf-8')


def interrupted(signum,frame):
    if CHILD is not None and CHILD.poll() is None:CHILD.terminate()
    raise InterruptedError('Local controller received signal '+str(signum))


def run_phase(recipe,phase,state):
    global CHILD
    plan,_=approved();logs=ROOT/'logs';logs.mkdir(exist_ok=True)
    hours=plan['train_max_hours_per_recipe'] if phase=='train' else plan['evaluation_max_hours_per_recipe']
    command=[sys.executable,'-u',str(Path(__file__).resolve()),'worker','--recipe',recipe,'--phase',phase]
    arm=state['arms'][recipe];arm.update(status=phase,phase_started_utc=now());status(state)
    with (logs/(recipe+'_'+phase+'.out')).open('x',encoding='utf-8') as out,(logs/(recipe+'_'+phase+'.err')).open('x',encoding='utf-8') as err:
        CHILD=subprocess.Popen(command,cwd=str(frozen.REPO),stdout=out,stderr=err)
        arm['child_pid']=CHILD.pid;status(state);started=time.monotonic()
        while CHILD.poll() is None:
            try:CHILD.wait(timeout=30)
            except subprocess.TimeoutExpired:
                status(state)
                if time.monotonic()-started>hours*3600+1800:
                    CHILD.terminate();CHILD.wait(timeout=120)
                    raise TimeoutError(recipe+' '+phase+' exceeded its wall ceiling plus checkpoint/loading allowance')
        code=CHILD.returncode;CHILD=None
    if code:raise RuntimeError(f'{recipe} {phase} exited {code}; see logs/{recipe}_{phase}.err')


def run():
    plan,folder=approved()
    lock=Path('/home/aliu/.cache/ftl-local-recipe-gpu.lock');lock.parent.mkdir(exist_ok=True)
    with lock.open('a+') as guard:
        try:fcntl.flock(guard,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise ValueError('A local recipe GPU queue is already active')
        if (ROOT/'queue.json').exists():raise ValueError('Queue already started; reconcile existing state instead of automatically restarting')
        for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,interrupted)
        state=dict(status='running',pid=os.getpid(),started_utc=now(),arms={},plan_sha256=frozen.digest(ROOT/'plan.json'))
        status(state)
        try:
            import qwen_recipe_runner as runner
            import score_recipe_suite as scoring
            s,source,rows=runner.load(folder)
            audit=frozen.read(folder/'token_audit.json')
            if audit['overlength'] or audit['adapter_sha256']!=plan['adapter_sha256']:raise ValueError('Evidence token audit failed')
            if len({r['episode'] for r in rows if r['task']=='binary' and r['split']=='train'})!=400:
                raise ValueError('The full 400 training episodes are required')
            import torch
            if not torch.cuda.is_available():raise ValueError('CUDA GPU unavailable')
            if '3090' not in torch.cuda.get_device_name():raise ValueError('Expected the approved RTX 3090')
            runtime=dict(gpu=torch.cuda.get_device_name(),python=sys.executable,torch=torch.__version__,
                cuda=torch.version.cuda,flash_compiled=torch.backends.cuda.is_flash_attention_available(),
                full_training_windows=sum(r['split']=='train' and r['task']=='binary' for r in rows),
                development_windows=sum(r['split']=='development' and r['task']=='binary' for r in rows))
            freeze(ROOT/'runtime.json',runtime);print(json.dumps(runtime),flush=True)
            # The parent only inventories CUDA; it never loads model weights.
            for recipe in plan['recipes']:
                if (ROOT/'STOP_AFTER_CURRENT').exists():state['status']='stopped_after_current';break
                state['current_recipe']=recipe;state['arms'][recipe]=dict(status='starting',started_utc=now());status(state)
                if recipe!='base':run_phase(recipe,'train',state)
                run_phase(recipe,'generate',state)
                generated=frozen.read(ROOT/'predictions'/recipe/'completion.json')
                trained=None if recipe=='base' else frozen.read(ROOT/'runs'/recipe/'completion.json')
                scored=scoring.score(folder,ROOT/'predictions'/recipe)
                freeze(ROOT/'arm_scores'/(recipe+'.json'),scored)
                scores={p.stem:frozen.read(p) for p in (ROOT/'arm_scores').glob('*.json')}
                scoring.write_report(ROOT,scores)
                complete=generated['complete'] and (recipe=='base' or trained['completed_schedule'])
                state['arms'][recipe].update(status='completed' if complete else 'time_capped',finished_utc=now(),training=trained,generation=generated)
                freeze(ROOT/'arm_states'/(recipe+'.json'),state['arms'][recipe]);status(state)
            else:state['status']='completed' if all(a['status']=='completed' for a in state['arms'].values()) else 'finished_with_incomplete_arms'
        except BaseException as exc:
            state.update(status='interrupted' if isinstance(exc,InterruptedError) else 'failed',error=type(exc).__name__+': '+str(exc))
            recipe=state.get('current_recipe')
            if recipe:state['arms'][recipe]['status']=state['status']
            if CHILD is not None and CHILD.poll() is None:
                CHILD.terminate()
                try:CHILD.wait(timeout=120)
                except subprocess.TimeoutExpired:CHILD.kill();CHILD.wait()
            raise
        finally:
            state['finished_utc']=now();status(state)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['prepare','check','run','worker'])
    p.add_argument('--recipe',choices=RECIPES);p.add_argument('--phase',choices=['train','generate']);a=p.parse_args()
    if a.command=='prepare':prepare()
    elif a.command=='check':approved();print('Approved local full-data queue verified.')
    elif a.command=='run':run()
    else:worker(a.recipe,a.phase)
