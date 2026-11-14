"""Independent TACC copies of the approved full-data recipes; local runs continue."""
import argparse
from datetime import datetime,timezone
import gc
import importlib.metadata
import json
from pathlib import Path
import time

import oopsie_full_jobs as frozen

ROOT=frozen.REPO/'outputs/oopsie_distillation_tacc_replicates_v2'
TRAIN=['binary','joint','categories_aux','evidence_aux','both_aux','binary_compute_control','joint_then_binary','failure_balanced']
PACKS=[['base','binary','joint'],['categories_aux','evidence_aux','both_aux'],['binary_compute_control','joint_then_binary','failure_balanced']]


def now():return datetime.now(timezone.utc).isoformat()


def save(path,value,immutable=False):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if immutable and path.exists():
        if frozen.read(path)!=value:raise ValueError('Frozen replica artifact changed: '+str(path))
        return
    if immutable:
        with path.open('x',encoding='utf-8') as out:json.dump(value,out,indent=2);out.write('\n')
    else:
        temporary=path.with_name(path.name+'.tmp');temporary.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8');temporary.replace(path)


def prepare():
    parent,folder=frozen.approval();ROOT.mkdir(parents=True,exist_ok=True)
    code=[Path(__file__),Path(__file__).with_name('requirements-tacc-replicates-v2.txt'),Path(__file__).with_name('requirements-recipes.txt'),
        frozen.REPO/'scripts/tacc/submit_tacc_replicates_v2.py']+sorted((frozen.REPO/'scripts/tacc').glob('oopsie_replicates_v2_*.sbatch'))
    plan=dict(protocol='oopsie_full_tacc_replicates_v2',parent_plan_sha256=frozen.digest(frozen.ROOT/'submission_plan.json'),
        study_sha256=parent['study_sha256'],records_sha256=parent['records_sha256'],adapter_sha256=parent['adapter_sha256'],
        data=str(folder.relative_to(frozen.REPO).as_posix()),training_episodes=400,development_episodes=50,sealed_test_episodes=50,
        recipes=['base']+TRAIN,training_recipes=TRAIN,optimizer_updates=2688,primary_examples=10752,
        train_max_hours=30,development_max_hours=1.5,baseline_max_hours=1.75,
        numpy_pin='2.3.5',runtime_root='/scratch/11388/al62479/ftl-oopsie-full-v1',
        venv='/scratch/11388/al62479/ftl-oopsie-full-v1/venv-replicates-v2',
        model_cache='/scratch/11388/al62479/ftl-oopsie-full-v1/hf/hub',
        tacc_account='IRI26045',partition='gpu-a100',packs=PACKS,packed_node_jobs=3,gpus_per_node=3,
        max_concurrent_training_jobs=8,max_concurrent_experiments=9,
        setup_hours=1,timing_hours=.5,packed_hours_per_job=32,packed_gpu_su_ceiling=288,
        this_launch_su_ceiling=288.893,prior_setup_su_ceiling=.286,cumulative_su_ceiling=289.179,authorized_su_cap=300,
        duplicate_local_experiments_authorized=True,local_run='outputs/oopsie_distillation_local_sequential_v1',
        results_are_independent=True,new_teacher_calls=0,test_used=False,automatic_requeue=False,
        execution_sha256={str(p.relative_to(frozen.REPO).as_posix()):frozen.digest(p) for p in code})
    save(ROOT/'plan.json',plan,True)
    save(ROOT/'approval.json',dict(approved=True,
        user_instruction='i think its fine to submit duplicate gpu experiments, eg the same experiments run locally we run on tacc',
        plan_sha256=frozen.digest(ROOT/'plan.json'),scope='Repair TACC setup and submit pretrained baseline plus all eight first-wave SFT recipes as independent TACC copies; local runs continue.'),True)
    (ROOT/'plan.md').write_text('''# Independent TACC distillation runs, v2

The user explicitly approved running the same experiments locally and on TACC.
Both sets continue independently; outputs, checkpoints, logs and scores remain
in separate run directories. No local job is stopped or replaced.

The TACC set contains pretrained Qwen plus binary-only, joint, category auxiliary,
explanation auxiliary, both auxiliary, extra-binary control, joint-then-binary
and failure-balanced replay. It reuses the exact same frozen study, 400 training
episodes, 50 development episodes, native-frame windows, targets, seed and
2,688-update schedule. The final 50 test episodes remain sealed. No teacher calls.

Setup uses a new isolated TACC environment with **NumPy 2.3.5** pinned; all
other direct model-runtime versions match the original recipe requirements.
This avoids the x86-64-v2 baseline introduced by NumPy 2.4, which the setup VM
does not expose. The failed environment and old logs remain preserved. The
already-downloaded pinned model cache and transferred frame evidence are reused.
Setup validates NumPy/Torch/HDF5/image interoperability, audits every input's
context length, and verifies all transferred image and reference hashes. The
GPU check then tests actual forward/backward passes before dependent jobs run.

Three complete A100 nodes each run three independent experiment processes,
one process per GPU. The array has three node jobs, up to three concurrently,
covering all eight training recipes and the baseline. Each node has a 32-hour
wall limit (up to 30 hours training per recipe plus development and overhead).
The baseline uses up to 1.75 hours within its shared node allocation. The GPU
check gets 30 minutes on A100-small, and CPU setup gets one hour on VM-small.
At 3 SUs per full-node hour, packed experiment ceiling is 3 x 32 x 3 = 288 SUs.
Requested launch ceiling: **288.893 SUs**; including conservative ceilings for
the two earlier failed setup attempts: **289.179 SUs**, within the 300-SU cap.
Time-capped runs remain incomplete and are not reported as completed copies.
No automatic requeue or retry. Scheduler dependencies cancel blocked GPU work
if setup or the runtime check fails.

NumPy source: https://numpy.org/doc/2.4/release/2.4.0-notes.html#modulate-dispatched-x86-cpu-features
Node layout and rates: https://docs.tacc.utexas.edu/hpc/lonestar6/
''',encoding='utf-8')
    print(json.dumps(dict(prepared=True,root=str(ROOT),cumulative_su_ceiling=plan['cumulative_su_ceiling'])),flush=True)


def approved():
    parent,folder=frozen.approval();plan=frozen.read(ROOT/'plan.json');a=frozen.read(ROOT/'approval.json')
    if a.get('approved') is not True or a.get('plan_sha256')!=frozen.digest(ROOT/'plan.json'):
        raise ValueError('Missing matching approval for independent TACC experiments')
    if not plan['duplicate_local_experiments_authorized']:raise ValueError('Concurrent local/TACC copies are not authorized')
    if plan['cumulative_su_ceiling']>plan['authorized_su_cap']:raise ValueError('TACC budget exceeded')
    if plan['parent_plan_sha256']!=frozen.digest(frozen.ROOT/'submission_plan.json'):raise ValueError('Canonical study plan changed')
    for rel,expected in plan['execution_sha256'].items():
        if frozen.digest(frozen.REPO/rel)!=expected:raise ValueError('Replica execution file changed: '+rel)
    return plan,folder


def verify_environment():
    import io
    import numpy as np
    import torch
    import h5py
    from PIL import Image
    plan,_=approved()
    if np.__version__!=plan['numpy_pin']:raise ValueError('Wrong NumPy build for setup VM')
    a=np.arange(12,dtype=np.float32).reshape(3,4)
    if not np.array_equal(torch.from_numpy(a).numpy(),a):raise ValueError('Torch/NumPy interoperability failed')
    memory=io.BytesIO()
    with h5py.File(memory,'w') as f:f['sample']=a
    with h5py.File(memory,'r') as f:
        if not np.array_equal(f['sample'][()],a):raise ValueError('HDF5/NumPy interoperability failed')
    if np.asarray(Image.new('RGB',(2,2))).shape!=(2,2,3):raise ValueError('Image/NumPy interoperability failed')
    return dict(versions={n:importlib.metadata.version(n) for n in ('numpy','torch','torchvision','transformers','peft','accelerate','bitsandbytes','h5py','Pillow')},
        cpu_import_and_array_checks_passed=True,cuda_available=torch.cuda.is_available())


def setup():
    import qwen_recipe_runner as runner
    plan,folder=approved();runtime=verify_environment();save(ROOT/'runtime_setup.json',runtime,True)
    audited=runner.audit(folder)
    if audited['overlength']:raise ValueError('Input context audit failed')
    s,source,rows=runner.load(folder)
    if len({r['episode'] for r in rows if r['task']=='binary' and r['split']=='train'})!=400:
        raise ValueError('Expected all 400 training episodes')
    inventory=frozen.read(frozen.ROOT/'image_inventory.json');started=time.monotonic()
    for i,item in enumerate(inventory['files']):
        path=frozen.REPO/item['path']
        if path.stat().st_size!=item['bytes'] or frozen.digest(path)!=item['sha256']:
            raise ValueError('Frame evidence changed: '+item['path'])
        if (i+1)%10000==0:print(json.dumps(dict(verified_images=i+1,total=len(inventory['files']))),flush=True)
    for e in s['episodes']:
        if e['split']=='test':continue
        native=source/'traces'/f"{e['episode']}_sol_r01"/'annotation.md'
        if frozen.digest(native)!=e['annotation_sha256']:raise ValueError('Teacher reference changed')
    save(ROOT/'setup_ready.json',dict(runtime=runtime,images=len(inventory['files']),image_bytes=inventory['bytes'],
        records_audited=len(audited['rows']),max_tokens=audited['max_tokens'],verified_utc=now(),
        plan_sha256=frozen.digest(ROOT/'plan.json'),image_verification_seconds=time.monotonic()-started,test_used=False),True)


def require_ready(name):
    value=frozen.read(ROOT/name)
    if value['plan_sha256']!=frozen.digest(ROOT/'plan.json'):raise ValueError('Readiness marker belongs to another plan')


def timing():
    import torch
    import qwen_recipe_runner as runner
    import qwen_oopsie_sft as core
    plan,folder=approved();require_ready('setup_ready.json')
    runtime=verify_environment();s,source,rows=runner.load(folder);cfg=runner.cfg_for(s);processor=core.processor_for(cfg)
    model=core.load_model(cfg,trainable=True);model.train()
    optimizer=torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],lr=cfg['learning_rate'])
    ranked=sorted(((runner.estimated_tokens(processor,source,r),r) for r in rows if r['split']=='train' and r['task']=='binary'),key=lambda x:x[0])
    results=[]
    for _,row in [ranked[len(ranked)//2],ranked[-1]]:
        optimizer.zero_grad(set_to_none=True);torch.cuda.reset_peak_memory_stats();started=time.monotonic()
        batch=core.encode_train(processor,source,row,cfg['max_length']);batch={k:v.to('cuda') for k,v in batch.items()}
        with torch.autocast('cuda',dtype=torch.bfloat16):loss,count=core.sft_loss(model,batch)
        if not torch.isfinite(loss):raise ValueError('GPU timing loss is nonfinite')
        (loss/count).backward();torch.nn.utils.clip_grad_norm_(model.parameters(),1,error_if_nonfinite=True)
        optimizer.step();torch.cuda.synchronize()
        results.append(dict(window=row['id'],seconds=time.monotonic()-started,peak_gpu_gib=torch.cuda.max_memory_allocated()/1024**3,loss=float(loss.detach())/count))
        print(json.dumps(results[-1]),flush=True);del batch,loss
    save(ROOT/'timing_ready.json',dict(plan_sha256=frozen.digest(ROOT/'plan.json'),gpu=torch.cuda.get_device_name(),
        runtime=runtime,results=results,temporary_updates_discarded=True,test_used=False),True)


def run(recipe):
    import torch
    import qwen_recipe_runner as runner
    import score_recipe_suite as scoring
    plan,folder=approved()
    if recipe not in plan['recipes']:raise ValueError('Unapproved replica recipe')
    require_ready('setup_ready.json');require_ready('timing_ready.json')
    path=ROOT/'arm_states'/(recipe+'.json')
    if path.exists():raise ValueError('Replica already attempted; refusing silent duplicate/restart')
    state=dict(recipe=recipe,status='running',started_utc=now(),plan_sha256=frozen.digest(ROOT/'plan.json'),
        independent_local_duplicate=True,site='TACC',gpu=torch.cuda.get_device_name())
    save(path,state,True)
    try:
        adapter=None
        if recipe!='base':
            result=runner.train(folder,recipe,ROOT/'runs'/recipe,updates=plan['optimizer_updates'],max_hours=plan['train_max_hours'])
            state['training']=result;adapter=Path(result['adapter']);save(path,state)
        gc.collect();torch.cuda.empty_cache()
        generated=runner.generate(folder,ROOT/'predictions'/recipe,adapter=adapter,split='development',
            max_hours=plan['baseline_max_hours'] if recipe=='base' else plan['development_max_hours'])
        score=scoring.score(folder,ROOT/'predictions'/recipe);save(ROOT/'arm_scores'/(recipe+'.json'),score,True)
        scoring.write_report(ROOT,{p.stem:frozen.read(p) for p in (ROOT/'arm_scores').glob('*.json')})
        complete=generated['complete'] and (recipe=='base' or state['training']['completed_schedule'])
        state.update(status='completed' if complete else 'time_capped',generation=generated)
    except BaseException as exc:state.update(status='failed',error=type(exc).__name__+': '+str(exc));raise
    finally:state['finished_utc']=now();save(path,state)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','check','setup','timing','run']);p.add_argument('--recipe',choices=['base']+TRAIN);a=p.parse_args()
    if a.command=='prepare':prepare()
    elif a.command=='check':approved();print('Approved independent TACC plan verified.')
    elif a.command=='setup':setup()
    elif a.command=='timing':timing()
    else:run(a.recipe)
