"""Download a queued FLORA dense run and publish validated local viewer updates."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

from check_flora_results import check


def atomic_json(path, value):
    temporary = path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')
    temporary.replace(path)


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--job-id', required=True)
    parser.add_argument('--review', type=Path, required=True)
    parser.add_argument('--jobs', type=Path, required=True)
    parser.add_argument('--record', type=Path, required=True)
    parser.add_argument('--host', default='al62479@login2.ls6.tacc.utexas.edu')
    parser.add_argument('--workspace', default='/scratch/11388/al62479/ftl-flora-oopsie-pilot-v1')
    parser.add_argument('--max-hours', type=float, default=12)
    args = parser.parse_args()
    if not args.job_id.isdigit() or not re.fullmatch(r'[a-z0-9]+@[a-z0-9.]+', args.host):
        parser.error('Invalid job ID or SSH target')
    if not re.fullmatch(r'/scratch/[A-Za-z0-9_/-]+', args.workspace):
        parser.error('Expected a scratch workspace path')
    prefix = ['wsl', '-d', 'Ubuntu-22.04', '--'] if os.name == 'nt' else []
    socket = '/home/aliu/.ssh/tacc-flora-%C'
    status_path = args.review/'dense_status.json'
    deadline = time.monotonic()+args.max_hours*3600
    record = json.loads(args.record.read_text(encoding='utf-8'))
    local_root = Path.cwd()
    output = local_root/'outputs'/('flora_oopsie_dense_'+args.job_id)

    def run(command, **kwargs):
        options = dict(stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=45)
        if os.name == 'nt':
            options['creationflags'] = subprocess.CREATE_NO_WINDOW
        return subprocess.run(prefix+command, **options, **kwargs)

    def scp(remote, target):
        local = str(target.resolve())
        if os.name == 'nt':
            local = '/mnt/'+local[0].lower()+local[2:].replace('\\', '/')
        result = run(['scp', '-r', '-o', 'ControlPath='+socket, '-o', 'BatchMode=yes',
                      args.host+':'+remote, local])
        if result.returncode:
            raise RuntimeError('Result download failed: '+result.stderr.decode(errors='replace')[-500:])

    while time.monotonic() < deadline:
        now = datetime.now(timezone.utc).isoformat()
        script = '''set -e
cd WORKSPACE
/usr/bin/python3 -S - JOB_ID <<'PY'
from pathlib import Path
import hashlib,json,subprocess,sys
job=sys.argv[1]
r=subprocess.run(['sacct','-j',job,'-X','-n','-P','--format=State,ExitCode,Elapsed'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
rows=[x.split('|') for x in r.stdout.splitlines() if x.strip()]
state=rows[0][0].strip().split()[0] if rows else 'UNKNOWN'
out=Path('outputs/flora_oopsie_dense_'+job)
record=dict(state=state,elapsed=rows[0][2] if rows else None,exit_code=rows[0][1] if rows else None)
if (out/'validation.json').is_file():record['validation']=json.loads((out/'validation.json').read_text())
if state=='COMPLETED' and (out/'dense.jsonl').is_file():record['sha256']=hashlib.sha256((out/'dense.jsonl').read_bytes()).hexdigest()
print(json.dumps(record))
PY
'''.replace('WORKSPACE', args.workspace).replace('JOB_ID', args.job_id)
        try:
            response = run(['ssh', '-S', socket, '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10',
                            args.host, 'bash', '-s'], input=script.encode())
            if response.returncode:
                raise RuntimeError('SSH status query failed')
            state = json.loads(response.stdout.decode())
            record.update(status=state['state'], updated_utc=now, elapsed=state.get('elapsed'))
            atomic_json(args.record, record)
            atomic_json(status_path, dict(state=state['state'], available=False,
                                         job_id=args.job_id, checked_utc=now))
            print(now, state['state'], flush=True)
            if state['state'] == 'COMPLETED':
                if not state.get('validation', {}).get('structurally_valid'):
                    raise ValueError('Completed run did not pass native output validation')
                output.parent.mkdir(parents=True, exist_ok=True)
                scp(args.workspace+'/outputs/'+output.name, output.parent)
                scp(args.workspace+'/outputs/oopsiedata_pilot_v1/dense_jobs.jsonl', output/'jobs.jsonl')
                report = check(output/'dense.jsonl', args.jobs)
                if not report['structurally_valid']:
                    raise ValueError(str(report['issues']))
                if digest(output/'dense.jsonl') != state['sha256']:
                    raise ValueError('Downloaded output checksum differs')
                run_manifest = json.loads((output/'run.json').read_text())
                assert run_manifest['status'] == 'completed'
                assert run_manifest['code']['revision'] == '7de68d22c4a9decec5ddb7f86ddcaee8f82d3367'
                assert digest(output/'jobs.jsonl') == run_manifest['jobs_sha256']
                parsed = lambda path: [json.loads(x) for x in path.read_text().splitlines() if x.strip()]
                assert parsed(output/'jobs.jsonl') == parsed(args.jobs)
                for remote, expected in run_manifest['video_sha256'].items():
                    assert remote.startswith(args.workspace+'/')
                    assert digest(local_root/remote[len(args.workspace)+1:]) == expected
                rows = parsed(output/'dense.jsonl')
                expected_jobs = {r['id']: r for r in parsed(args.jobs)}
                for row in rows:
                    assert row['task'] == expected_jobs[row['id']]['task']
                    end = 0
                    for segment in row['segments']:
                        assert segment['start_frame'] == end
                        assert segment['end_frame'] > end
                        assert all(x == segment['score'] for x in row['frame_scores'][end:segment['end_frame']])
                        end = segment['end_frame']
                    assert end == row['num_frames']
                atomic_json(args.review/'dense.json', rows)
                atomic_json(status_path, dict(state='COMPLETED', available=True, job_id=args.job_id,
                                             checked_utc=now, human_verified=False))
                record.update(downloaded=True, output_directory=str(output), validation=report,
                              results_sha256=state['sha256'], finished_utc=run_manifest['finished_utc'])
                atomic_json(args.record, record)
                print('Validated native segments published to viewer', flush=True)
                return
            if state['state'] in ('FAILED', 'CANCELLED', 'TIMEOUT', 'NODE_FAIL', 'OUT_OF_MEMORY'):
                return
        except (OSError, RuntimeError, subprocess.TimeoutExpired, json.JSONDecodeError) as error:
            print(now, str(error), flush=True)
            atomic_json(status_path, dict(state='RECONNECTING', available=False, job_id=args.job_id,
                                         checked_utc=now, detail=str(error)))
        except (AssertionError, ValueError) as error:
            atomic_json(status_path, dict(state='VALIDATION_FAILED', available=False,
                                         job_id=args.job_id, detail=str(error)))
            raise
        time.sleep(30)
    atomic_json(status_path, dict(state='MONITOR_STOPPED', available=False, job_id=args.job_id))


if __name__ == '__main__':
    main()
