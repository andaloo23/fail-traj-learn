"""Stage and journal one-shot submissions of the independent TACC recipe set."""
import argparse
from datetime import datetime,timezone
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'distill'))
import tacc_recipe_replicates_v2 as replicas
import oopsie_full_jobs as frozen

SSH=['ssh','-S','/home/aliu/.ssh/tacc-flora-%C','-o','BatchMode=yes','-o','ConnectTimeout=15','al62479@login2.ls6.tacc.utexas.edu']
REMOTE='/scratch/11388/al62479/ftl-oopsie-full-v1/repo'


def submission_args(kind,dependency=None):
    args=['sbatch','--parsable','--chdir='+REMOTE,'--kill-on-invalid-dep=yes']
    if dependency:args.append('--dependency=afterok:'+str(dependency))
    args.append(REMOTE+'/scripts/tacc/oopsie_replicates_v2_'+kind+'.sbatch')
    return args


def stage():
    plan,_=replicas.approved();paths=set(plan['execution_sha256'])
    for p in replicas.ROOT.rglob('*'):
        if p.is_file() and 'staging' not in p.parts:paths.add(str(p.relative_to(frozen.REPO).as_posix()))
    staging=replicas.ROOT/'staging';staging.mkdir(exist_ok=True)
    manifest=staging/'files.nul';manifest.write_bytes(b''.join(p.encode()+b'\0' for p in sorted(paths)))
    command=['rsync','-rl','--from0','--files-from='+str(manifest),'--info=stats1','-e',shlex.join(SSH[:-1]),
        './',SSH[-1]+':'+REMOTE+'/']
    subprocess.run(command,cwd=str(frozen.REPO),check=True)
    # Check the exact frozen plan remotely with stdlib only, before submission.
    check='cd '+shlex.quote(REMOTE)+' && /scratch/11388/al62479/ftl-flora/python/cpython-3.12.15-linux-x86_64-gnu/bin/python3.12 scripts/distill/tacc_recipe_replicates_v2.py check'
    subprocess.run(SSH+[check],check=True)
    replicas.save(staging/'complete.json',dict(staged_utc=datetime.now(timezone.utc).isoformat(),plan_sha256=frozen.digest(replicas.ROOT/'plan.json')),True)


def submit(kind):
    plan,_=replicas.approved()
    staged=frozen.read(replicas.ROOT/'staging/complete.json')
    if staged['plan_sha256']!=frozen.digest(replicas.ROOT/'plan.json'):raise ValueError('This plan has not been staged')
    folder=replicas.ROOT/'submissions';folder.mkdir(exist_ok=True);path=folder/(kind+'.json')
    if path.exists():raise ValueError('Replica submission already attempted; reconcile receipt before retrying')
    dependency=None
    if kind=='timing':dependency=frozen.read(folder/'setup.json')['job_id']
    if kind=='train':dependency=frozen.read(folder/'timing.json')['job_id']
    args=submission_args(kind,dependency)
    command='cd '+shlex.quote(REMOTE)+' && '+shlex.join(args)
    state=dict(kind=kind,status='submission_attempted',created_utc=datetime.now(timezone.utc).isoformat(),
        plan_sha256=frozen.digest(replicas.ROOT/'plan.json'),command=command,duplicate_local_experiments_authorized=True)
    replicas.save(path,state,True)
    result=subprocess.run(SSH+[command],capture_output=True,text=True,timeout=60)
    state.update(returncode=result.returncode,stdout=result.stdout.strip(),stderr=result.stderr.strip())
    ids=re.findall(r'^(\d+)(?:;[^\n]+)?$',result.stdout.strip(),re.MULTILINE)
    if result.returncode==0 and len(ids)==1:state.update(status='submitted',job_id=ids[0])
    else:state['status']='submission_failed_or_ambiguous'
    replicas.save(path,state);print(json.dumps(state),flush=True)
    if state['status']!='submitted':raise SystemExit(1)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['stage','setup','timing','train']);a=p.parse_args()
    stage() if a.command=='stage' else submit(a.command)
