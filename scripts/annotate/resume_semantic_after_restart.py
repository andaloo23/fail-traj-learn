"""Continue unsent independent jobs after a transport failure; never resend a call."""
import api_frame_selection_semantic_v2 as run


def main():
    manifest = run.verify()
    with (run.OUT / 'resume_after_restart.lock').open('x') as lock:
        lock.write(run.common.digest(run.OUT / 'manifest.json'))
    keys = run.common.credentials()
    for job in manifest['jobs']:
        path = run.OUT / 'attempts' / (job['id'] + '.json')
        record = run.common.load(path) if path.exists() else {}
        if record.get('generation_sent'):
            continue
        if job['arm'] == 'F' and not (run.OUT / job['episode'] / 'selected/freeze.json').exists():
            print(job['id'] + ': blocked by unavailable selection', flush=True)
            continue
        try:
            run.execute(job, keys)
        except RuntimeError:
            failed = run.common.load(path)
            if failed.get('generation_estimate_usd') is not None or not failed.get('generation_sent'):
                raise
            if not any(t in failed.get('error', '') for t in ('TimeoutError', 'RemoteDisconnected', 'timed out')):
                raise
            print(job['id'] + ': transport failed; reservation retained; no retry', flush=True)
    run.report()


if __name__ == '__main__':
    main()
