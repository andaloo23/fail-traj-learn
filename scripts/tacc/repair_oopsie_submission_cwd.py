"""Replace diagnosed failed submissions, keeping the approved frozen payloads.

The original SSH submission ran sbatch from HOME. Its --chdir option did not
change SLURM_SUBMIT_DIR, which the frozen scripts cd into. Submit from the repo
directory explicitly. This is a one-shot repair, not an automatic retry loop.
"""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'distill'))
import oopsie_full_jobs as jobs

SSH=['ssh','-S','/home/aliu/.ssh/tacc-flora-%C','-o','BatchMode=yes','-o','ConnectTimeout=15','al62479@login2.ls6.tacc.utexas.edu']
REMOTE='/scratch/11388/al62479/ftl-oopsie-full-v1/repo'


def launch(kind):
    plan,_=jobs.approval()
    receipt=jobs.read(jobs.ROOT/'staging/image_transfer_complete.json')
    if receipt['rsync_exit_code']!=0 or receipt['image_inventory_sha256']!=jobs.digest(jobs.ROOT/'image_inventory.json'):
        raise ValueError('Evidence transfer must be complete')
    # Do not duplicate any live first-wave work. Original jobs must be terminal.
    old=subprocess.run(SSH+['sacct','-j','3539432,3539433,3539434,3539435','-X','-n','-P','--format=JobID,State,Elapsed,ExitCode'],capture_output=True,text=True,timeout=30,check=True)
    lines=[x for x in old.stdout.splitlines() if x.strip()]
    if len(lines)!=4 or any(x.split('|')[1].split()[0] not in ('FAILED','CANCELLED') for x in lines):
        raise ValueError('Original job states changed; inspect before replacing')
    root=jobs.ROOT/'submissions/cwd_repair_v1';root.mkdir(exist_ok=True)
    path=root/(kind+'.json')
    if path.exists():raise ValueError('Repair already attempted; reconcile receipt before retrying')
    dependency=None
    if kind=='timing':dependency=jobs.read(root/'setup.json')['job_id']
    if kind in ('train','baseline'):dependency=jobs.read(root/'timing.json')['job_id']
    args=['sbatch','--parsable','--chdir='+REMOTE,'--kill-on-invalid-dep=yes']
    if dependency:args.append('--dependency=afterok:'+dependency)
    args.append(REMOTE+'/scripts/tacc/oopsie_full_'+kind+'.sbatch')
    # Both the actual sbatch submission cwd and WorkDir now point to the repo.
    command='cd '+shlex.quote(REMOTE)+' && '+shlex.join(args)
    state=dict(kind=kind,status='submission_attempted',plan_sha256=jobs.digest(jobs.ROOT/'submission_plan.json'),
        diagnosis='Original setup cd used SLURM_SUBMIT_DIR=HOME; corrected sbatch submission cwd. Frozen execution code/data unchanged.',
        original_jobs=old.stdout.strip(),ssh_command=command,created_utc=datetime.now(timezone.utc).isoformat(),
        approved_su_cap=300,first_wave_requested_su_ceiling=plan['tacc_su_ceiling'],original_setup_runtime_seconds=3,
        original_gpu_jobs_ran=False)
    with path.open('x',encoding='utf-8') as f:json.dump(state,f,indent=2)
    result=subprocess.run(SSH+[command],capture_output=True,text=True,timeout=60)
    state.update(returncode=result.returncode,stdout=result.stdout.strip(),stderr=result.stderr.strip())
    ids=re.findall(r'^(\d+)(?:;[^\n]+)?$',result.stdout.strip(),re.MULTILINE)
    if result.returncode==0 and len(ids)==1:state.update(status='submitted',job_id=ids[0])
    else:state['status']='submission_failed_or_ambiguous'
    path.write_text(json.dumps(state,indent=2)+'\n',encoding='utf-8');print(json.dumps(state),flush=True)
    if state['status']!='submitted':raise SystemExit(1)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('kind',choices=['setup','timing','train','baseline']);a=p.parse_args();launch(a.kind)
