"""Journal the explicitly authorized short timing check, never a full sweep."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'distill'))
import corral_astra_v8_2 as transport
import qwen_backbone_timing as timing

REMOTE = '/scratch/11388/al62479/ftl-qwen-backbone-timing-v1'


def submit(root, kind, remote=REMOTE):
    plan = timing.verify(root)
    if not re.fullmatch(r'/scratch/11388/al62479/[A-Za-z0-9_/-]+', remote):
        raise ValueError('Unexpected remote workspace')
    environment = plan.get('runtime_environment', remote + '/venv')
    if not re.fullmatch(r'/scratch/11388/al62479/[A-Za-z0-9_/-]+', environment):
        raise ValueError('Unexpected runtime environment')
    folder = root / 'submissions'
    folder.mkdir(exist_ok=True)
    receipt = folder / (kind + '.json')
    if receipt.exists():
        raise ValueError('Submission previously attempted; reconcile its receipt before taking further action')
    plan_hash = timing.digest(root / 'plan.json')
    args = ['sbatch', '--parsable', '--chdir=' + remote,
            '--export=ALL,QWEN_TIMING_ROOT=' + remote + ',QWEN_TIMING_ENV=' + environment,
            '--kill-on-invalid-dep=yes', '--comment=qwen-backbone-v1-' + plan_hash[:12]]
    if kind == 'gpu':
        setup = timing.read(folder / 'setup.json')
        if setup['status'] != 'submitted' or setup['plan_sha256'] != plan_hash:
            raise ValueError('Missing matching setup submission')
        args.append('--dependency=afterok:' + setup['job_id'])
    args.append(remote + '/qwen_backbone_timing_v1_' + kind + '.sbatch')
    command = shlex.join(args)
    state = dict(kind=kind, status='submission_attempted', plan_sha256=plan_hash,
                 created_utc=datetime.now(timezone.utc).isoformat(), command=command,
                 scope='Short timing check only; no full recipe training')
    timing.save(receipt, state, True)
    try:
        result = subprocess.run(transport.SSH + [command], capture_output=True,
                                text=True, timeout=60)
    except subprocess.TimeoutExpired:
        state['status'] = 'submission_outcome_unknown_reconcile_before_retry'
        timing.save(receipt, state)
        raise
    ids = re.findall(r'^(\d+)(?:;[^\n]+)?$', result.stdout.strip(), re.MULTILINE)
    state.update(returncode=result.returncode, stdout=result.stdout, stderr=result.stderr)
    if result.returncode == 0 and len(ids) == 1:
        state.update(status='submitted', job_id=ids[0])
    else:
        state['status'] = 'submission_failed_or_ambiguous'
    timing.save(receipt, state)
    print(json.dumps(state), flush=True)
    if state['status'] != 'submitted':
        raise SystemExit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('kind', choices=['setup', 'gpu'])
    parser.add_argument('--root', type=Path, default=Path('outputs/qwen_backbone_timing_v1'))
    parser.add_argument('--remote', default=REMOTE)
    args = parser.parse_args()
    submit(args.root, args.kind, args.remote)
