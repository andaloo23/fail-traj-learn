"""Collect a completed reference run, validate it, and build separate review exports."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

from check_flora_results import check, check_rubric

COLLECTION_STATUS_PATH = None


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def atomic_json(path, value):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')
    temp.replace(path)


def main():
    global COLLECTION_STATUS_PATH
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--job-id', required=True)
    parser.add_argument('--max-hours', type=float, default=72)
    parser.add_argument('--audit-directory', type=Path, default=Path('outputs/flora_oopsie_reference_audit_v1'))
    parser.add_argument('--inputs', type=Path, default=Path('outputs/oopsiedata_reference_v2'))
    parser.add_argument('--workspace', default='/scratch/11388/al62479/ftl-flora-oopsie-pilot-v1')
    parser.add_argument('--output-tag', default='flora_oopsie_reference')
    parser.add_argument('--review-directory', type=Path)
    args = parser.parse_args()
    if not args.job_id.isdigit():
        parser.error('Job ID must be numeric')
    root = Path.cwd()
    if os.name != 'nt':
        parser.error('This collector uses the established Windows/WSL setup')
    audit = args.audit_directory.resolve()
    inputs = args.inputs.resolve()
    review = (args.review_directory.resolve() if args.review_directory else
              root/'outputs/flora_oopsie_review_3529640'/('reference_'+args.job_id))
    status = audit/'collection_status.json'
    COLLECTION_STATUS_PATH = status
    ssh = ['wsl','-d','Ubuntu-22.04','--','ssh','-S','/home/aliu/.ssh/tacc-flora-%C',
           '-o','BatchMode=yes','-o','ConnectTimeout=10','al62479@login2.ls6.tacc.utexas.edu']
    remote = args.workspace

    def run(command, **kwargs):
        return subprocess.run(command, capture_output=True, timeout=60,
                              creationflags=subprocess.CREATE_NO_WINDOW, **kwargs)

    def wsl_path(path):
        path = str(path.resolve())
        return '/mnt/'+path[0].lower()+path[2:].replace('\\','/')

    def download(path, destination, recursive=False):
        command = ['wsl','-d','Ubuntu-22.04','--','scp']+(['-r'] if recursive else [])
        command += ['-o','ControlPath=/home/aliu/.ssh/tacc-flora-%C','-o','BatchMode=yes',
                    'al62479@login2.ls6.tacc.utexas.edu:'+path,wsl_path(destination)]
        result = run(command)
        if result.returncode:
            raise RuntimeError(result.stderr.decode(errors='replace')[-500:])

    deadline = time.monotonic()+args.max_hours*3600
    while time.monotonic() < deadline:
        try:
            result = run(ssh+['sacct','-j',args.job_id,'-X','-n','-P','--format=State,ExitCode,Elapsed'])
            result.check_returncode()
            lines = [s.split('|') for s in result.stdout.decode().splitlines() if s.strip()]
            state = lines[0][0].strip().split()[0] if lines else 'UNKNOWN'
            record = dict(job_id=args.job_id,state=state,checked_utc=datetime.now(timezone.utc).isoformat(),
                          elapsed=lines[0][2] if lines else None)
            atomic_json(status, record)
            print(record['checked_utc'], state, flush=True)
            if state == 'COMPLETED':
                if lines[0][1] != '0:0':
                    raise ValueError('Completed job has a nonzero exit code')
                break
            if state in ('FAILED','CANCELLED','TIMEOUT','OUT_OF_MEMORY','NODE_FAIL','PREEMPTED'):
                raise ValueError('Reference job ended with '+state+'; no review published')
        except (subprocess.SubprocessError, OSError) as exc:
            atomic_json(status, dict(state='CONNECTION_RETRY',job_id=args.job_id,error=str(exc),
                                     checked_utc=datetime.now(timezone.utc).isoformat()))
        time.sleep(60)
    else:
        raise TimeoutError('Collector monitoring window ended; job was not cancelled')
    hardware = root/'outputs'/(args.output_tag+'_hardware_'+args.job_id+'.json')
    download(remote+'/outputs/'+hardware.name, hardware)
    h = json.loads(hardware.read_text())
    published = json.loads((audit/'hub_metadata.json').read_text())
    expected_weights = {r['rfilename']:r['lfs']['sha256'] for r in published['siblings']
                        if r['rfilename'].endswith('.safetensors')}
    assert {r['name']:r['sha256'] for r in h['weights']} == expected_weights
    assert len(h['gpus']) == 2 and all('H100' in g['name'] for g in h['gpus'])
    outputs = {}
    for mode in ('dense','rubric'):
        folder = root/'outputs'/(args.output_tag+'_'+mode+'_'+args.job_id)
        download(remote+'/outputs/'+folder.name, folder.parent, recursive=True)
        manifest = json.loads((folder/'run.json').read_text())
        assert manifest['reference_batch_defaults'] and manifest['status'] == 'completed'
        assert manifest['code']['revision'] == published['sha']
        jobs = inputs/(mode+'_jobs.jsonl')
        assert manifest['jobs_sha256'] == digest(jobs) == h['inputs_sha256'][jobs.name]
        source_hashes = {digest((jobs.parent/v).resolve()) for line in jobs.read_text().splitlines()
                         if line.strip() for v in json.loads(line)['videos']}
        assert set(manifest['video_sha256'].values()) == source_hashes
        command = manifest['command']
        for flag in ('--max-num-seqs','--tensor-parallel-size','--num-samples','--max-new-tokens',
                     '--max-model-len','--max-num-batched-tokens'):
            assert flag not in command, flag
        validation = check(folder/'dense.jsonl', jobs) if mode == 'dense' else check_rubric(folder/'rubric.jsonl', jobs, 9)
        assert validation['structurally_valid'], validation
        outputs[mode] = folder/(mode+'.jsonl')
    # Native preflight already exercised every request. Keep the reference viewer
    # and exports separate from the historical pilot, without derived time cues.
    python = '/home/aliu/projects/fail-traj-learn/lerobot/.venv/bin/python'
    def build(script, arguments):
        command = ['wsl','-d','Ubuntu-22.04','--',python,wsl_path(root/'scripts/tacc'/script)]
        for flag, value in arguments:
            command += [flag,wsl_path(value) if isinstance(value,Path) else value]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                creationflags=subprocess.CREATE_NO_WINDOW)
        print(result.stdout.decode(errors='replace'),flush=True)
        result.check_returncode()
    shared = [('--rubric',outputs['rubric']),('--jobs',inputs/'rubric_jobs.jsonl'),
              ('--provenance',inputs/'provenance.json')]
    build('review_flora_rubric.py',shared+[('--out',review)])
    dense = [json.loads(s) for s in outputs['dense'].read_text().splitlines() if s.strip()]
    atomic_json(review/'dense.json',dense)
    atomic_json(review/'dense_status.json',dict(state='COMPLETED',available=True,job_id=args.job_id))
    for episode in [json.loads(s)['id'] for s in (inputs/'dense_jobs.jsonl').read_text().splitlines() if s.strip()]:
        build('export_flora_annotated_video.py',shared+[
            ('--dense',outputs['dense']),('--dense-jobs',inputs/'dense_jobs.jsonl'),
            ('--episode',episode),('--out',review/'exports'/episode)])
    atomic_json(status,dict(state='COMPLETED',job_id=args.job_id,review=str(review),
                            url=('http://127.0.0.1:60969/'+review.relative_to(root/'outputs/flora_oopsie_review_3529640').as_posix()+'/'),
                            hardware_and_output_validation_passed=True,human_verified=False,
                            checked_utc=datetime.now(timezone.utc).isoformat()))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        if COLLECTION_STATUS_PATH is not None and COLLECTION_STATUS_PATH.parent.is_dir():
            atomic_json(COLLECTION_STATUS_PATH,dict(state='COLLECTION_FAILED',error=str(exc),
                                    checked_utc=datetime.now(timezone.utc).isoformat()))
        raise
