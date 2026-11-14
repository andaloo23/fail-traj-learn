"""Finish only unsent R004 C-F; preserve the unknown-charge B failure."""
import api_frame_selection_full_coverage_v1 as run


def main():
    manifest = run.verify()
    failure = run.common.load(run.OUT / 'attempts/R004_B.json')
    if failure['status'] != 'stopped' or not failure.get('generation_sent'):
        raise ValueError('Expected stopped R004_B; refusing unexpected resume state')
    with (run.OUT / 'resume_remaining.lock').open('x') as lock:
        lock.write(run.common.digest(run.OUT / 'manifest.json'))
    keys = run.common.credentials()
    for job in manifest['jobs']:
        if job['id'] not in ('R004_C', 'R004_D', 'R004_E', 'R004_F'):
            continue
        path = run.OUT / 'attempts' / (job['id'] + '.json')
        record = run.common.load(path) if path.exists() else {}
        if record.get('generation_sent'):
            raise ValueError('Refusing to resend an already sent generation')
        run.execute(job, keys)
    run.report()


if __name__ == '__main__':
    main()
