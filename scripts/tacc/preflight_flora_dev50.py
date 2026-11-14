"""Dense-only offline preflight: pinned dependencies, cache, all media and prompts."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata as metadata
import json
from pathlib import Path
import subprocess
import sys


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--inputs', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    a.out.mkdir(parents=True, exist_ok=False)
    code = a.root / 'rewarder'
    spec = json.loads(Path(__file__).with_name('models.lock.json').read_text())['rewarder']
    published = json.loads((a.inputs / 'published_code.json').read_text())
    receipt = json.loads((code / 'fetch_receipt.json').read_text())
    assert all(receipt[k] == spec[k] == published[k] for k in ('repo', 'revision'))
    assert receipt['files'] == published['code_sha256']
    for name, expected in receipt['files'].items():
        assert sha(code / name) == expected, name
    sys.path.insert(0, str(code))
    import av
    import numpy as np
    from packaging.requirements import Requirement
    from batch_utils import core
    from batch_utils.engine import load_processor, render, resolve_model

    packages = {}
    for line in (code / 'batch_utils/requirements.txt').read_text().splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        req = Requirement(line)
        version = metadata.version(req.name)
        assert req.specifier.contains(version), (line, version)
        packages[req.name] = version
    pip = subprocess.run([sys.executable, '-m', 'pip', 'check'], capture_output=True, text=True)
    pip_note = (pip.stdout + pip.stderr).strip()
    if pip.returncode:
        # Published Decord wheel's internal tag; dense uses PyAV and never Decord.
        assert pip_note == 'decord 0.6.0 is not supported on this platform', pip_note
    model = Path(resolve_model(spec['repo'], spec['revision'], weights=False))
    hub = json.loads((a.inputs / 'hub_metadata.json').read_text())
    weight_files, supporting = [], []
    for item in hub['siblings']:
        name = item['rfilename']
        path = model / name
        if name.endswith('.safetensors'):
            assert path.is_file() and path.stat().st_size == item['lfs']['size'], name
            # Shape/header read proves each cached shard is readable without a GPU load.
            from safetensors import safe_open
            with safe_open(path, framework='numpy') as shard:
                assert list(shard.keys()), name
            weight_files.append(dict(name=name, bytes=path.stat().st_size,
                                     expected_sha256=item['lfs']['sha256']))
        elif path.is_file():
            raw = path.read_bytes()
            actual = sha(path) if item.get('lfs') else hashlib.sha1(
                b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
            expected = item['lfs']['sha256'] if item.get('lfs') else item['blobId']
            assert actual == expected, name
            supporting.append(name)
    assert len(weight_files) == 11
    assert {'config.json', 'tokenizer_config.json', 'preprocessor_config.json'} <= set(supporting)
    processor = load_processor(str(model))
    inputs = json.loads((a.inputs / 'inputs.json').read_text())
    jobs = [json.loads(s) for s in (a.inputs / 'dense_jobs.jsonl').read_text().splitlines()]
    assert [j['id'] for j in jobs] == inputs['development_ids']
    assert len(jobs) == len(set(inputs['development_ids'])) == 50
    assert inputs['camera_mapping']['visually_reviewed'] is True
    reports = []
    for job, e in zip(jobs, inputs['episodes'], strict=True):
        assert set(job) == {'id', 'task', 'videos'}
        assert job['id'] == e['id'] and job['task'] == e['task']
        assert job['videos'] == [c['path'] for c in e['cameras']]
        paths, clocks = [], []
        for camera in e['cameras']:
            path = (a.inputs / camera['path']).resolve()
            assert path.is_relative_to(a.inputs.resolve())
            assert sha(path) == camera['sha256']
            with av.open(str(path)) as container:
                stream = container.streams.video[0]
                clock = np.array([float(f.pts * f.time_base) for f in container.decode(stream)])
                fps = float(stream.average_rate)
            assert len(clock) == e['n_frames'] and abs(fps - e['fps']) < 1e-6
            assert np.allclose(clock, np.arange(len(clock)) / fps, atol=1e-6, rtol=0)
            paths.append(path)
            clocks.append(clock)
        assert all(np.array_equal(clock, clocks[0]) for clock in clocks)
        collage = core.Collage(paths)
        assert collage.num_frames == e['n_frames'] and abs(collage.fps - e['fps']) < 1e-6
        windows = core.dense_windows(collage.num_frames, collage.fps)
        collage.frames(sorted({i for w in windows for i in w.frame_indices}))
        clips = []
        for window in windows:
            frames = collage.frames(window.frame_indices)
            text = render(processor, core.dense_messages(job['task'], window), thinking=False)
            assert frames.shape[0] == 64 and frames.shape[-1] == 3
            name = f"{e['id']}_clip_{window.index}_prompt.txt"
            (a.out / name).write_text(text)
            clips.append(dict(index=window.index, shape=list(frames.shape),
                              frame_indices=list(window.frame_indices),
                              rgb_sha256=hashlib.sha256(frames.tobytes()).hexdigest(),
                              prompt_sha256=hashlib.sha256(text.encode()).hexdigest()))
        collage.release()
        reports.append(dict(id=e['id'], frames=e['n_frames'], fps=e['fps'], clips=clips))
        print(f"{job['id']}: all cameras, frame clocks, {len(clips)} native clips passed", flush=True)
    report = dict(checked_utc=datetime.now(timezone.utc).isoformat(), passed=True,
                  inference_performed=False, code=spec, packages=packages,
                  pip_check_warning=pip_note if pip.returncode else None,
                  cached_weight_size_and_headers_verified=weight_files,
                  supporting_files_hash_verified=supporting,
                  jobs_sha256=sha(a.inputs / 'dense_jobs.jsonl'),
                  inputs_sha256=sha(a.inputs / 'inputs.json'), episodes=reports)
    (a.out / 'preflight.json').write_text(json.dumps(report, indent=2) + '\n')
    print('DENSE DEVELOPMENT-50 PREFLIGHT PASSED; no inference performed', flush=True)


if __name__ == '__main__':
    main()
