"""Validate downloaded OopsieData episodes and build label-blind FLORA inputs.

Run in an environment with h5py, numpy and PyAV. Original MP4s are used without
transcoding. Source annotations are archived separately and never enter jobs.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import av
import h5py
import numpy as np

from flora_camera_mapping import map_cameras


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def plain(value):
    if isinstance(value, bytes):
        return value.decode('utf-8')
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pilot', type=Path, required=True)
    parser.add_argument('--inventory', type=Path, required=True)
    parser.add_argument('--camera-map', type=Path, required=True,
                        help='Reviewed camera roles; alphabetical HDF5 order is never a geometry mapping')
    parser.add_argument('--out', type=Path, help='Fresh output directory; sources stay in --pilot')
    parser.add_argument('--rubrics', type=Path, help='Optional task-specific rubric JSON keyed by episode ID')
    args = parser.parse_args()
    pilot = args.pilot.resolve()
    output = args.out.resolve() if args.out else pilot
    if any((output/name).exists() for name in ('rubric_jobs.jsonl', 'dense_jobs.jsonl', 'provenance.json')):
        raise ValueError('Refusing to overwrite prior inference inputs; choose a fresh --out directory')
    camera_map = json.loads(args.camera_map.read_text(encoding='utf-8'))
    task_rubrics = json.loads(args.rubrics.read_text(encoding='utf-8')) if args.rubrics else None
    selection = json.loads((pilot/'selection.json').read_text())
    inventory = json.loads(args.inventory.read_text())
    if selection['revision'] != inventory['sha'] or selection['repo'] != inventory['id']:
        raise ValueError('Selection and repository inventory differ')
    files = {row['rfilename']: row for row in inventory['siblings']}
    rubric = [{
        'action': 'Fulfill the supplied task instruction. Consider visible task progress, unsuccessful attempts, recovery, handling quality, and the final state. Judge only visible evidence; do not assume completion beyond the video.',
        'grading': [
            {'label': 'No meaningful progress toward the requested task is visible.', 'points': 0.0},
            {'label': 'A relevant attempt is visible, but little progress is made and the final objective is not achieved.', 'points': 0.25},
            {'label': 'Substantial progress is visible, but the final objective is not achieved.', 'points': 0.5},
            {'label': 'The requested task is achieved, with visible retries, recovery, or materially imprecise or inefficient handling.', 'points': 0.75},
            {'label': 'The requested task is achieved cleanly, with appropriate and reasonably efficient handling.', 'points': 1.0},
        ],
    }]
    jobs, dense_jobs, provenance, annotations = [], [], [], {}
    for index, episode in enumerate(selection['episodes'], 1):
        episode_id = f'O{index:03d}'
        path = pilot/'source'/episode['release_path']
        if digest(path) != episode['release_file_sha256']:
            raise ValueError(f'HDF5 checksum mismatch: {path}')
        with h5py.File(path, 'r') as handle:
            if handle.attrs['schema'] != 'oopsiedata_format_v1':
                raise ValueError(f'Unsupported schema: {path}')
            task = plain(handle.attrs['language_instruction'])
            if not isinstance(task, str) or not task.strip():
                raise ValueError(f'Missing task instruction: {path}')
            profile = json.loads(plain(handle.attrs['robot_profile']))
            videos, cameras, camera_audit, seen = [], [], [], {}
            reference_pts = None
            for name, dataset in handle['observations/video_paths'].items():
                video = (path.parent/plain(dataset[()])).resolve(strict=True)
                if not video.is_relative_to(pilot/'source'):
                    raise ValueError('Video path escapes downloaded source tree')
                release_path = video.relative_to(pilot/'source').as_posix()
                if release_path not in json.loads(episode['video_reference_paths_json']):
                    raise ValueError('HDF5 video is absent from the release episode manifest')
                checksum = digest(video)
                if checksum != files[release_path]['lfs']['sha256']:
                    raise ValueError(f'Video checksum mismatch: {release_path}')
                with av.open(str(video)) as container:
                    stream = container.streams.video[0]
                    pts = np.array([float(frame.pts*frame.time_base) for frame in container.decode(stream)])
                    fps = float(stream.average_rate)
                    width, height = stream.width, stream.height
                if len(pts) != int(episode['timestep_count']):
                    raise ValueError(f'Frame/state count mismatch: {release_path}')
                if len(pts) < 2 or not np.allclose(pts, np.arange(len(pts))/fps, rtol=0, atol=1e-6):
                    raise ValueError(f'Nonuniform or offset video clock: {release_path}')
                if reference_pts is not None and not np.allclose(pts, reference_pts, rtol=0, atol=1e-6):
                    raise ValueError(f'Camera timelines differ: {release_path}')
                reference_pts = pts
                audit = dict(camera=name, path=release_path, sha256=checksum,
                             frames=len(pts), fps=fps, width=width, height=height,
                             first_pts_seconds=float(pts[0]), last_pts_seconds=float(pts[-1]))
                if checksum in seen:
                    audit['excluded_duplicate_of'] = seen[checksum]
                else:
                    seen[checksum] = name
                    videos.append(video.relative_to(pilot).as_posix())
                    # Use recorded identifiers without inventing camera geometry.
                    cameras.append('camera labeled '+name)
                camera_audit.append(audit)
            if not videos:
                raise ValueError('Episode has no usable videos')
            dense_videos, videos, cameras = map_cameras(
                episode_id, camera_audit, camera_map['episodes'][episode_id], pilot/'source', output)
            robot = ('bimanual' if profile.get('is_biarm') else 'single-arm')
            robot += ' real-world robot '+str(profile.get('robot_name', 'unspecified'))
            jobs.append(dict(id=episode_id, task=task, videos=videos, robot=robot,
                             cameras=cameras, rubric=task_rubrics[episode_id] if task_rubrics else rubric))
            dense_jobs.append(dict(id=episode_id, task=task, videos=dense_videos))
            source_annotations = {}
            def archive(name, obj):
                item = {'attrs': {key: plain(value) for key, value in obj.attrs.items()}}
                if isinstance(obj, h5py.Dataset):
                    item['value'] = plain(obj[()])
                source_annotations[name] = item
            handle['episode_annotations'].visititems(archive)
            annotations[episode_id] = source_annotations
            provenance.append(dict(id=episode_id, release_path=episode['release_path'],
                                   hdf5_sha256=digest(path), task=task,
                                   robot_profile=profile, cameras=camera_audit,
                                   reviewed_camera_mapping=camera_map['episodes'][episode_id],
                                   video_clock_check='matching zero-based constant-rate PTS; physical capture synchronization not independently verified'))
    output.mkdir(parents=True, exist_ok=True)
    (output/'rubric_jobs.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in jobs), encoding='utf-8')
    (output/'dense_jobs.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in dense_jobs), encoding='utf-8')
    report = dict(created_utc=datetime.now(timezone.utc).isoformat(),
                  repo=selection['repo'], revision=selection['revision'],
                  selection_method=selection['selection_method'], episodes=provenance,
                  rubric_origin=('Researcher-defined task-specific steps; not an NVIDIA benchmark rubric' if task_rubrics
                                 else 'Researcher-defined generic criterion, not an NVIDIA benchmark rubric'),
                  camera_map_sha256=digest(args.camera_map),
                  rubrics_sha256=digest(args.rubrics) if args.rubrics else None,
                  source_annotations_used_as_model_input=False,
                  human_verified=False, training_ready=False)
    (output/'provenance.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    (output/'source_annotations.json').write_text(json.dumps(annotations, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(episodes=len(jobs), unique_video_inputs=sum(len(j['videos']) for j in jobs),
                          output=str(output), validation='passed'), indent=2))


if __name__ == '__main__':
    main()
