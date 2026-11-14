"""Continue the timed-out v2 evidence check, preserving successful verification.

The immutable previous job log proves a contiguous verified image prefix.
Reuse is allowed only for the exact same inventory, audit, study and code.
Every newly checked chunk has a durable checkpoint. No model or training
configuration changes, and no automatic retry loop.
"""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'distill'))
import tacc_recipe_replicates_v2 as replicas
import oopsie_full_jobs as frozen
import submit_tacc_replicates_v2 as launch

ROOT=replicas.ROOT/'repairs/setup_timeout_v1'
OLD_LOG=frozen.REPO/'oopsie-rep-v2-setup-3540122.out'
OLD_LOG_SHA='3d02ee03faeaa67ffee79f6bd2c5fc77a5db50bf332d6ff6d63907ad311805af'


def now():return datetime.now(timezone.utc).isoformat()


def verified_prefix(text,total):
    seen=0
    for line in text.splitlines():
        try:value=json.loads(line)
        except ValueError:continue
        if 'verified_images' not in value:continue
        n=value['verified_images']
        if value.get('total')!=total or type(n) is not int or n!=seen+10000 or n>total:
            raise ValueError('Previous verification log is not a contiguous prefix')
        seen=n
    if not seen:raise ValueError('Previous job has no verified image prefix')
    return seen


def prepare():
    parent,_=replicas.approved()
    files=[Path(__file__),Path(__file__).with_name('oopsie_replicates_v2_continue_setup.sbatch')]
    plan=dict(parent_replica_plan_sha256=frozen.digest(replicas.ROOT/'plan.json'),
        previous_setup_job='3540122',previous_setup_log_sha256=OLD_LOG_SHA,
        inventory_sha256=frozen.digest(frozen.ROOT/'image_inventory.json'),
        audit_sha256=frozen.digest(frozen.ROOT/'evidence_c32_x8_v3/token_audit.json'),
        expected_verified_prefix=120000,total_images=174028,setup_hours=2,additional_setup_su_ceiling=.286,
        cumulative_su_ceiling=parent['cumulative_su_ceiling']+.286,authorized_su_cap=300,
        reuse_existing_environment=True,training_configuration_unchanged=True,
        execution_sha256={str(p.relative_to(frozen.REPO).as_posix()):frozen.digest(p) for p in files})
    replicas.save(ROOT/'plan.json',plan,True)
    replicas.save(ROOT/'approval.json',dict(approved=True,plan_sha256=frozen.digest(ROOT/'plan.json'),
        authorization='Existing user authorization to repair/rerun TACC setup and run matching GPU experiments alongside local experiments.',
        instructions=['if the tacc distillation setup failed we need to rerun then right',
            'i think its fine to submit duplicate gpu experiments, eg the same experiments run locally we run on tacc']),True)
    (ROOT/'plan.md').write_text('''# Continue the timed-out setup validation

Job 3540122 successfully installed NumPy 2.3.5, passed real CPU interoperability
checks, completed the 11,535-record context audit, and verified the first 120,000
images before reaching its one-hour limit. Its GPU dependents never ran.

Continue in the already-built environment with a two-hour CPU allocation.
The prior log, exact image inventory, frozen study/code and token audit are
checked by SHA256 before its contiguous verified prefix is reused. The remaining
54,028 images are checked by size and SHA256, with durable checkpoints every
500 images. Training/development reference hashes are then checked. Runtime
imports are checked again; only complete validation creates the readiness flag.

The GPU runtime check and three packed experiment jobs are restored using the
unchanged approved scripts and recipe plan. Local training continues. No teacher
calls, final-test evaluation, rebuilt environment or changed training targets.

Additional CPU ceiling: 0.286 SU. Conservative cumulative ceiling: 289.465 SUs,
within 300 SUs. This is a diagnosed continuation, not an automatic retry loop.
''',encoding='utf-8')
    print(json.dumps(dict(prepared=True,cumulative_su_ceiling=plan['cumulative_su_ceiling'])),flush=True)


def approved():
    parent,folder=replicas.approved();plan=frozen.read(ROOT/'plan.json');a=frozen.read(ROOT/'approval.json')
    if a.get('approved') is not True or a.get('plan_sha256')!=frozen.digest(ROOT/'plan.json'):raise ValueError('Repair approval mismatch')
    if plan['parent_replica_plan_sha256']!=frozen.digest(replicas.ROOT/'plan.json'):raise ValueError('Replica plan changed')
    if plan['cumulative_su_ceiling']>plan['authorized_su_cap']:raise ValueError('Budget exceeded')
    for rel,expected in plan['execution_sha256'].items():
        if frozen.digest(frozen.REPO/rel)!=expected:raise ValueError('Continuation execution file changed')
    return plan,folder


def complete():
    import qwen_recipe_runner as runner
    plan,folder=approved();runtime=replicas.verify_environment()
    inventory_path=frozen.ROOT/'image_inventory.json'
    if frozen.digest(inventory_path)!=plan['inventory_sha256']:raise ValueError('Inventory changed; verified prefix cannot be reused')
    if frozen.digest(folder/'token_audit.json')!=plan['audit_sha256']:raise ValueError('Cached completed context audit changed')
    if frozen.digest(OLD_LOG)!=plan['previous_setup_log_sha256']:raise ValueError('Prior job log changed')
    inventory=frozen.read(inventory_path);total=len(inventory['files'])
    prefix=verified_prefix(OLD_LOG.read_text(encoding='utf-8'),total)
    if prefix!=plan['expected_verified_prefix'] or total!=plan['total_images']:raise ValueError('Unexpected prior evidence coverage')
    audit=frozen.read(folder/'token_audit.json')
    if audit['overlength']:raise ValueError('Cached context audit did not pass')
    progress_path=ROOT/'progress.json';progress=dict(next_image_index=prefix,total_images=total,
        repair_plan_sha256=frozen.digest(ROOT/'plan.json'),inventory_sha256=plan['inventory_sha256'],resumed_prefix=prefix)
    if progress_path.exists():
        cached=frozen.read(progress_path)
        if any(cached[k]!=progress[k] for k in ('repair_plan_sha256','inventory_sha256','total_images','resumed_prefix')):
            raise ValueError('Checkpoint belongs to another verification')
        if not prefix<=cached['next_image_index']<=total:raise ValueError('Invalid checkpoint boundary')
        progress=cached
    replicas.save(progress_path,progress);started=time.monotonic()
    print(json.dumps(dict(resuming_at_image=progress['next_image_index'],total=total,runtime=runtime)),flush=True)
    for i in range(progress['next_image_index'],total):
        item=inventory['files'][i];path=frozen.REPO/item['path']
        if path.stat().st_size!=item['bytes'] or frozen.digest(path)!=item['sha256']:raise ValueError('Evidence changed: '+item['path'])
        if (i+1)%500==0 or i+1==total:
            progress.update(next_image_index=i+1,updated_utc=now());replicas.save(progress_path,progress)
            print(json.dumps(dict(verified_images=i+1,total=total)),flush=True)
    study,source,rows=runner.load(folder)
    for e in study['episodes']:
        if e['split']=='test':continue
        native=source/'traces'/f"{e['episode']}_sol_r01"/'annotation.md'
        if frozen.digest(native)!=e['annotation_sha256']:raise ValueError('Teacher reference changed')
    ready=dict(runtime=runtime,images=total,image_bytes=inventory['bytes'],records_audited=len(audit['rows']),
        max_tokens=audit['max_tokens'],verified_utc=now(),plan_sha256=frozen.digest(replicas.ROOT/'plan.json'),
        verification_continuation_plan_sha256=frozen.digest(ROOT/'plan.json'),verified_prefix_reused=prefix,
        additional_image_verification_seconds=time.monotonic()-started,test_used=False)
    replicas.save(replicas.ROOT/'setup_ready.json',ready,True)
    replicas.save(ROOT/'completion.json',dict(complete=True,images=total,verified_utc=now()),True)
    print(json.dumps(dict(setup_ready=True,verified_images=total)),flush=True)


def stage():
    plan,_=approved();paths=set(plan['execution_sha256'])
    for p in ROOT.rglob('*'):
        if p.is_file() and 'staging' not in p.parts:paths.add(str(p.relative_to(frozen.REPO).as_posix()))
    path=ROOT/'staging/files.nul';path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(b''.join(p.encode()+b'\0' for p in sorted(paths)))
    subprocess.run(['rsync','-rl','--from0','--files-from='+str(path),'-e',shlex.join(launch.SSH[:-1]),'./',
        launch.SSH[-1]+':'+launch.REMOTE+'/'],cwd=str(frozen.REPO),check=True)
    command='cd '+shlex.quote(launch.REMOTE)+' && /scratch/11388/al62479/ftl-flora/python/cpython-3.12.15-linux-x86_64-gnu/bin/python3.12 scripts/tacc/continue_tacc_setup_v2.py check'
    subprocess.run(launch.SSH+[command],check=True)
    replicas.save(ROOT/'staging/complete.json',dict(plan_sha256=frozen.digest(ROOT/'plan.json')),True)


def submit(kind):
    approved()
    if frozen.read(ROOT/'staging/complete.json')['plan_sha256']!=frozen.digest(ROOT/'plan.json'):raise ValueError('Repair is not staged')
    old=subprocess.run(launch.SSH+['sacct','-j','3540122,3540125,3540126','-X','-n','-P','--format=JobID,State'],capture_output=True,text=True,timeout=30,check=True)
    states=[x.split('|')[1].split()[0] for x in old.stdout.splitlines() if x.strip()]
    if len(states)!=3 or any(s not in ('TIMEOUT','CANCELLED') for s in states):raise ValueError('Prior jobs are not all terminal; inspect before replacing')
    folder=ROOT/'submissions';folder.mkdir(exist_ok=True);path=folder/(kind+'.json')
    if path.exists():raise ValueError('Continuation submission already attempted; reconcile receipt first')
    dependency=None
    if kind=='timing':dependency=frozen.read(folder/'setup.json')['job_id']
    if kind=='train':dependency=frozen.read(folder/'timing.json')['job_id']
    if kind=='setup':args=['sbatch','--parsable','--chdir='+launch.REMOTE,'--kill-on-invalid-dep=yes',launch.REMOTE+'/scripts/tacc/oopsie_replicates_v2_continue_setup.sbatch']
    else:args=launch.submission_args(kind,dependency)
    command='cd '+shlex.quote(launch.REMOTE)+' && '+shlex.join(args)
    state=dict(kind=kind,status='submission_attempted',created_utc=now(),repair_plan_sha256=frozen.digest(ROOT/'plan.json'),command=command)
    replicas.save(path,state,True)
    result=subprocess.run(launch.SSH+[command],capture_output=True,text=True,timeout=60)
    state.update(returncode=result.returncode,stdout=result.stdout.strip(),stderr=result.stderr.strip())
    ids=re.findall(r'^(\d+)(?:;[^\n]+)?$',result.stdout.strip(),re.MULTILINE)
    if result.returncode==0 and len(ids)==1:state.update(status='submitted',job_id=ids[0])
    else:state['status']='submission_failed_or_ambiguous'
    replicas.save(path,state);print(json.dumps(state),flush=True)
    if state['status']!='submitted':raise SystemExit(1)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','check','complete','stage','setup','timing','train']);a=p.parse_args()
    if a.command=='prepare':prepare()
    elif a.command=='check':approved();print('Approved checkpointed setup continuation verified.')
    elif a.command=='complete':complete()
    elif a.command=='stage':stage()
    else:submit(a.command)
