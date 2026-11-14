"""Audit reference inputs, upstream defaults, and native dense postprocessing on CPU.

This does not certify model accuracy. Run before submitting reference GPU inference.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata as metadata
import json
from pathlib import Path
import subprocess
import sys


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def rows(path):
    return [json.loads(s) for s in path.read_text().splitlines() if s.strip()]


def parser_defaults(module, jobs):
    """Capture the real upstream argparse defaults before model/processor loading."""
    class Captured(Exception):
        pass
    result = {}
    original = module.base_parser

    def parser(*args, **kwargs):
        p = original(*args, **kwargs)
        parse = p.parse_args

        def capture(argv=None):
            result.update(vars(parse(argv)))
            raise Captured()
        p.parse_args = capture
        return p

    module.base_parser = parser
    try:
        module.main(['--jobs', str(jobs), '--output', '/unused-reference-audit.jsonl'])
    except Captured:
        pass
    finally:
        module.base_parser = original
    return {k: str(v) if isinstance(v, Path) else v for k, v in result.items()}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--inputs', type=Path, required=True)
    p.add_argument('--published', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--old-dense', type=Path)
    p.add_argument('--old-jobs', type=Path)
    p.add_argument('--verify-weights', action='store_true')
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    code = args.root/'rewarder'
    published = json.loads(args.published.read_text())
    receipt = json.loads((code/'fetch_receipt.json').read_text())
    assert receipt['repo'] == published['repo'] and receipt['revision'] == published['revision']
    assert receipt['files'] == published['code_sha256']
    for name, expected in receipt['files'].items():
        assert digest(code/name) == expected, name
    print('Published runtime code: all hashes match', flush=True)
    sys.path.insert(0, str(code))
    import av
    import numpy as np
    from packaging.requirements import Requirement
    from batch_utils import core, dense_reward, rubric_reward
    from batch_utils.engine import load_processor, render, resolve_model
    from flora_camera_mapping import map_cameras

    packages = {}
    for line in (code/'batch_utils/requirements.txt').read_text().splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        req = Requirement(line)
        version = metadata.version(req.name)
        assert req.specifier.contains(version), (line, version)
        packages[req.name] = version
    assert packages['decord'] == '0.6.0'
    import decord
    assert decord.__version__ == '0.6.0'
    check = subprocess.run([sys.executable, '-m', 'pip', 'check'], capture_output=True, text=True)
    pip_note = (check.stdout+check.stderr).strip()
    # The publisher's py3 wheel contains an internal cp36 tag. Preserve the wheel
    # unmodified and disclose the packaging warning; runtime decode is checked below.
    if check.returncode:
        assert pip_note == 'decord 0.6.0 is not supported on this platform', pip_note
    dense_defaults = parser_defaults(dense_reward, args.inputs/'dense_jobs.jsonl')
    rubric_defaults = parser_defaults(rubric_reward, args.inputs/'rubric_jobs.jsonl')
    assert dense_defaults['tensor_parallel_size'] == 1 and dense_defaults['max_num_seqs'] == 8
    assert rubric_defaults['tensor_parallel_size'] == 2 and rubric_defaults['num_samples'] == 9
    assert rubric_defaults['max_new_tokens'] == 20480 and rubric_defaults['max_model_len'] == 98304
    print('All upstream dependency requirements and parser defaults verified', flush=True)
    model = Path(resolve_model(published['repo'], published['revision'], weights=False))
    hub = json.loads((args.published.parent/'hub_metadata.json').read_text())
    supporting = []
    for item in hub['siblings']:
        name = item['rfilename']
        path = model/name
        if not path.is_file() or name.endswith('.safetensors'):
            continue
        if item.get('lfs'):
            actual = digest(path)
            expected = item['lfs']['sha256']
        else:
            raw = path.read_bytes()
            actual = hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
            expected = item['blobId']
        assert actual == expected, name
        supporting.append(name)
    assert {'config.json', 'tokenizer_config.json', 'preprocessor_config.json'} <= set(supporting)
    if args.verify_weights:
        weight_checks = []
        for item in hub['siblings']:
            if item['rfilename'].endswith('.safetensors'):
                actual = digest(model/item['rfilename'])
                assert actual == item['lfs']['sha256'], item['rfilename']
                weight_checks.append(dict(name=item['rfilename'], sha256=actual))
                print('Verified weight', item['rfilename'], flush=True)
        assert len(weight_checks) == 11
        (args.out/'weight_checksums.json').write_text(json.dumps(weight_checks, indent=2)+'\n')
    processor = load_processor(str(model))
    provenance = json.loads((args.inputs/'provenance.json').read_text())
    dense_jobs, rubric_jobs = rows(args.inputs/'dense_jobs.jsonl'), rows(args.inputs/'rubric_jobs.jsonl')
    assert [j['id'] for j in dense_jobs] == [j['id'] for j in rubric_jobs]
    reports = []
    for dense, rubric, source in zip(dense_jobs, rubric_jobs, provenance['episodes'], strict=True):
        assert dense['id'] == rubric['id'] == source['id']
        assert dense['task'] == rubric['task'] == source['task']
        assert abs(sum(max(g['points'] for g in s['grading']) for s in rubric['rubric'])-1) < 1e-6
        # Input paths are relative to the job files, never to the launch directory.
        dpaths = [(args.inputs/v).resolve() for v in dense['videos']]
        rpaths = [(args.inputs/v).resolve() for v in rubric['videos']]
        camera_by_hash = {c['sha256']: c for c in source['cameras']}
        # Locate source root using the archived path of the first selected video.
        suffix = Path(camera_by_hash[digest(rpaths[0])]['path'])
        source_root = rpaths[0]
        for _ in suffix.parts:
            source_root = source_root.parent
        mapped_d, mapped_r, descriptions = map_cameras(
            source['id'], source['cameras'], source['reviewed_camera_mapping'], source_root, args.inputs.resolve())
        assert mapped_d == dense['videos'] and mapped_r == rubric['videos'] and descriptions == rubric['cameras']
        clocks = []
        for path in dict.fromkeys(dpaths+rpaths):
            checksum = digest(path)
            assert checksum in camera_by_hash, str(path)
            source_camera = camera_by_hash[checksum]
            with av.open(str(path)) as container:
                stream = container.streams.video[0]
                clock = np.array([float(f.pts*f.time_base) for f in container.decode(stream)])
                fps = float(stream.average_rate)
            assert len(clock) == source_camera['frames']
            assert np.allclose(clock, np.arange(len(clock))/fps, atol=1e-6, rtol=0)
            clocks.append(clock)
        assert all(np.allclose(clock, clocks[0], atol=1e-6, rtol=0) for clock in clocks)
        collage = core.Collage(dpaths)
        windows = core.dense_windows(collage.num_frames, collage.fps)
        dense_inputs = []
        for window in windows:
            frames = collage.frames(window.frame_indices)
            text = render(processor, core.dense_messages(dense['task'], window), thinking=False)
            assert frames.shape[0] == 64 and frames.shape[-1] == 3
            (args.out/f"{dense['id']}_dense_clip_{window.index}_prompt.txt").write_text(text)
            dense_inputs.append(dict(index=window.index, anchor=window.anchor,
                                     frame_indices=list(window.frame_indices), real=list(window.real),
                                     shape=list(frames.shape), rgb_sha256=hashlib.sha256(frames.tobytes()).hexdigest(),
                                     prompt_sha256=hashlib.sha256(text.encode()).hexdigest()))
        collage.release()
        header = core.rubric_header(rubric['robot'], rubric['cameras'])
        prompt = core.rubric_prompt(rubric['task'], rubric['rubric'], header)
        messages = core.rubric_messages(prompt, rpaths)
        text = render(processor, messages, thinking=True, vision_ids=True)
        assert text.rstrip().endswith('<think>')
        decoded = rubric_reward.video_inputs(messages)
        assert len(decoded) == len(rpaths)
        cameras = []
        for path, (frames, info) in zip(rpaths, decoded, strict=True):
            assert frames.shape[0] <= core.RUBRIC_MAX_FRAMES
            assert info['do_sample_frames'] is False
            cameras.append(dict(path=str(path), source_sha256=digest(path),
                                shape=list(frames.shape), metadata=info,
                                decoded_sha256=hashlib.sha256(frames.tobytes()).hexdigest()))
        (args.out/f"{dense['id']}_rubric_prompt.txt").write_text(text)
        reports.append(dict(id=dense['id'], task=dense['task'], dense_videos=dense['videos'],
                            dense_inputs=dense_inputs, rubric_cameras=cameras,
                            rubric_prompt_sha256=hashlib.sha256(text.encode()).hexdigest()))
        print('All camera clocks, native dense inputs, native Decord rubric inputs passed:', dense['id'], flush=True)
    old_postprocessing = []
    if args.old_dense:
        for job, row in zip(rows(args.old_jobs), rows(args.old_dense), strict=True):
            collage = core.Collage([(args.old_jobs.parent/v).resolve() for v in job['videos']])
            windows = core.dense_windows(collage.num_frames, collage.fps)
            texts = [clip['output'] for clip in row['clips']]
            answers = [core.parse_dense(text) for text in texts]
            assert all(a.valid for a in answers)
            reconstructed = dense_reward.summarize(job, collage, windows, answers, texts, core.DENSE_TAIL_TRIM_S, True)
            assert reconstructed == row, row['id']
            old_postprocessing.append(row['id'])
    report = dict(checked_utc=datetime.now(timezone.utc).isoformat(), code=published,
                  native_code_verified=True, dependency_versions=packages,
                  pip_check_warning=pip_note if check.returncode else None,
                  supporting_snapshot_files_verified=supporting,
                  dense_defaults=dense_defaults, rubric_defaults=rubric_defaults,
                  inputs_sha256={name:digest(args.inputs/name) for name in ('dense_jobs.jsonl','rubric_jobs.jsonl','provenance.json')},
                  original_dense_native_postprocessing_reproduced=old_postprocessing,
                  media_and_prompt_preflight_passed=True, inference_performed=False,
                  episodes=reports, physical_capture_sync_independently_verified=False,
                  reference_scope='Pinned batch inference defaults, original media, explicit view mapping, researcher-defined task-specific rubric; not a benchmark replication or guarantee of label correctness')
    (args.out/'preflight.json').write_text(json.dumps(report, indent=2)+'\n')
    print('REFERENCE PREFLIGHT PASSED; no GPU inference performed', flush=True)


if __name__ == '__main__':
    main()
