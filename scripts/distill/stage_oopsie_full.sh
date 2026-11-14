#!/bin/bash
# Transfer only approved execution files and train/dev evidence; no credentials,
# giant native API requests, HDF5, source videos, or final-test images.
set -euo pipefail
cd /mnt/c/Users/LocalPC/dev/fail-traj-learn
task_py=/home/aliu/.venvs/ftl-oopsie-recipes-v1/bin/python
task_host=al62479@login2.ls6.tacc.utexas.edu
task_remote=/scratch/11388/al62479/ftl-oopsie-full-v1/repo
task_ssh='ssh -S /home/aliu/.ssh/tacc-flora-%C -o BatchMode=yes -o ConnectTimeout=15'
"$task_py" - <<'PY'
import sys
from pathlib import Path
sys.path.insert(0,'scripts/distill')
import oopsie_full_jobs as jobs
plan,folder=jobs.approval()
root=jobs.ROOT;repo=jobs.REPO
paths=set(plan['code_sha256'])
paths.update(str(p.relative_to(repo).as_posix()) for p in (repo/'configs').glob('*.json'))
paths.add('scripts/distill/requirements-recipes.txt')
for p in root.rglob('*'):
    if p.is_file() and p.suffix in ('.json','.jsonl','.md') and 'staging' not in p.parts:
        paths.add(str(p.relative_to(repo).as_posix()))
study=jobs.read(root/'study.json');source=repo/study['config']['source_run']
paths.update(str((source/x).relative_to(repo).as_posix()) for x in ('manifest.json','prompt.md'))
for e in study['episodes']:
    if e['split']=='test':continue
    native=source/'traces'/f"{e['episode']}_sol_r01"
    for name in ('annotation.md','response.json','attempt.json'):
        paths.add(str((native/name).relative_to(repo).as_posix()))
staging=root/'staging';staging.mkdir(exist_ok=True)
(staging/'metadata-files.nul').write_bytes(b''.join(p.encode()+b'\0' for p in sorted(paths)))
images=jobs.read(root/'image_inventory.json')['files']
(staging/'image-files.nul').write_bytes(b''.join(p['path'].encode()+b'\0' for p in sorted(images,key=lambda x:x['path'])))
print('Metadata files:',len(paths),'image files:',len(images),'image bytes:',sum(x['bytes'] for x in images),flush=True)
PY
$task_ssh "$task_host" mkdir -p "$task_remote"
if [[ ${1:-metadata} == metadata ]]; then
    rsync -rl --from0 --files-from=outputs/oopsie_distillation_full_v1/staging/metadata-files.nul --info=stats1 -e "$task_ssh" ./ "$task_host:$task_remote/"
else
    rsync -rl --from0 --files-from=outputs/oopsie_distillation_full_v1/staging/image-files.nul --info=progress2,stats1 -e "$task_ssh" ./ "$task_host:$task_remote/"
    "$task_py" - <<'PY'
import sys,json
from datetime import datetime,timezone
sys.path.insert(0,'scripts/distill')
import oopsie_full_jobs as jobs
path=jobs.ROOT/'staging/image_transfer_complete.json'
path.write_text(json.dumps(dict(rsync_exit_code=0,image_inventory_sha256=jobs.digest(jobs.ROOT/'image_inventory.json'),completed_utc=datetime.now(timezone.utc).isoformat()))+'\n')
PY
fi
