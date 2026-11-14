"""Journaled, one-shot Slurm submission for the approved full-data study.

Run from WSL. A failed/ambiguous submission is never silently retried: reconcile
the named Slurm job with squeue/sacct and this journal before further action.
"""
import argparse
from datetime import datetime,timezone
import json
import subprocess
import re
import sys
from pathlib import Path

import oopsie_full_jobs as jobs

SSH=['ssh','-S','/home/aliu/.ssh/tacc-flora-%C','-o','BatchMode=yes','-o','ConnectTimeout=15','al62479@login2.ls6.tacc.utexas.edu']
REMOTE='/scratch/11388/al62479/ftl-oopsie-full-v1/repo'


def launch(kind):
    plan,folder=jobs.approval();root=jobs.ROOT/'submissions';root.mkdir(exist_ok=True)
    path=root/(kind+'.json')
    if path.exists():raise ValueError('Submission already attempted: reconcile journal before retrying '+kind)
    dependency=None
    if kind=='timing':dependency=jobs.read(root/'setup.json')['job_id']
    if kind in ('train','baseline'):dependency=jobs.read(root/'timing.json')['job_id']
    args=['sbatch','--parsable','--chdir='+REMOTE,'--kill-on-invalid-dep=yes']
    if kind=='timing':args.append('--hold')
    if dependency:args.append('--dependency=afterok:'+dependency)
    args.append(REMOTE+'/scripts/tacc/oopsie_full_'+kind+'.sbatch')
    state=dict(kind=kind,status='submission_attempted',command=args,plan_sha256=jobs.digest(jobs.ROOT/'submission_plan.json'),
        created_utc=datetime.now(timezone.utc).isoformat())
    with path.open('x',encoding='utf-8') as f:json.dump(state,f,indent=2)
    result=subprocess.run(SSH+args,capture_output=True,text=True,timeout=60)
    state.update(returncode=result.returncode,stdout=result.stdout.strip(),stderr=result.stderr.strip())
    matches=re.findall(r'^(\d+)(?:;[^\n]+)?$',result.stdout.strip(),re.MULTILINE)
    if result.returncode==0 and len(matches)==1:state.update(status='submitted',job_id=matches[0])
    else:state['status']='submission_failed_or_ambiguous'
    path.write_text(json.dumps(state,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(state),flush=True)
    if state['status']!='submitted':raise SystemExit(1)


def release_timing():
    jobs.approval();receipt=jobs.read(jobs.ROOT/'staging/image_transfer_complete.json')
    if receipt['image_inventory_sha256']!=jobs.digest(jobs.ROOT/'image_inventory.json'):
        raise ValueError('Image transfer receipt does not match this study')
    timing=jobs.read(jobs.ROOT/'submissions/timing.json')
    path=jobs.ROOT/'submissions/timing_release.json'
    if path.exists():raise ValueError('Release already attempted; reconcile Slurm state before retrying')
    state=dict(job_id=timing['job_id'],status='release_attempted',created_utc=datetime.now(timezone.utc).isoformat())
    with path.open('x',encoding='utf-8') as f:json.dump(state,f,indent=2)
    result=subprocess.run(SSH+['scontrol','release',timing['job_id']],capture_output=True,text=True,timeout=60)
    state.update(status='released' if result.returncode==0 else 'release_failed_or_ambiguous',
        returncode=result.returncode,stdout=result.stdout.strip(),stderr=result.stderr.strip())
    path.write_text(json.dumps(state,indent=2)+'\n',encoding='utf-8');print(json.dumps(state),flush=True)
    if result.returncode:raise SystemExit(1)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('kind',choices=['setup','timing','train','baseline','release-timing']);a=p.parse_args()
    release_timing() if a.kind=='release-timing' else launch(a.kind)
