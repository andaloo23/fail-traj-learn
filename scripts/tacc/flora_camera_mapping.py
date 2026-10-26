"""Explicit, reviewed camera selection for NVIDIA's positional collage interface."""
import os
from pathlib import Path


SLOTS = {1: ['single'], 2: ['left', 'right'],
         3: ['left', 'center', 'right'], 4: ['top', 'front_or_bottom', 'left', 'right']}


def map_cameras(episode_id, camera_audit, mapping, source_root, output_root):
    if not mapping.get('visually_reviewed') or not mapping.get('evidence'):
        raise ValueError(f'{episode_id}: camera mapping needs visual review and evidence')
    cameras = {c['camera']: c for c in camera_audit}
    dense = mapping['dense']
    names = [c['camera'] for c in dense]
    if [c['slot'] for c in dense] != SLOTS.get(len(dense)):
        raise ValueError(f'{episode_id}: wrong NVIDIA collage slot order')
    rubric = mapping['rubric']
    rubric_names = [c['camera'] for c in rubric]
    for mode, selected in [('dense', names), ('rubric', rubric_names)]:
        if len(selected) != len(set(selected)) or not set(selected) <= cameras.keys():
            raise ValueError(f'{episode_id}: duplicate or unknown {mode} cameras')
        if not selected:
            raise ValueError(f'{episode_id}: no {mode} cameras')
        excluded = mapping.get(mode + '_excluded', {})
        if set(selected) & excluded.keys() or set(selected) | excluded.keys() != cameras.keys():
            raise ValueError(f'{episode_id}: account for every source camera in {mode}')
        if any(not str(reason).strip() for reason in excluded.values()):
            raise ValueError(f'{episode_id}: excluded cameras need a reason')
        hashes = [cameras[name]['sha256'] for name in selected]
        if len(hashes) != len(set(hashes)):
            raise ValueError(f'{episode_id}: selected cameras have duplicate video bytes')
    if any(not c.get('description', '').strip() for c in rubric):
        raise ValueError(f'{episode_id}: rubric cameras need descriptions')

    def paths(selected):
        return [Path(os.path.relpath(source_root / cameras[name]['path'], output_root)).as_posix()
                for name in selected]

    return paths(names), paths(rubric_names), [c['description'] for c in rubric]
