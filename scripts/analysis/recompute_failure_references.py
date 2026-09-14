"""Compare saved oracle references with fresh computation; never replace annotations."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np
import pandas as pd

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS / 'annotate'))
sys.path.insert(0, str(SCRIPTS / 'annotate' / 'bench'))
from oracle_reference import build_reference  # noqa: E402
from common import corrected_success  # noqa: E402


def compare(project: Path, datasets=None):
    results = []
    directories = sorted((project / 'bench/references').iterdir())
    if datasets:
        known = {d.name for d in directories}
        missing = set(datasets) - known
        if missing:
            raise ValueError(f'unknown reference datasets: {sorted(missing)}')
        directories = [d for d in directories if d.name in datasets]
    for directory in directories:
        paths = sorted(directory.glob('episode_*.json'))
        if not paths:
            continue
        name = directory.name
        files = sorted((project / 'data' / name / 'data').rglob('*.parquet'))
        df = pd.concat([pd.read_parquet(p) for p in files], ignore_index=True)
        groups = dict(tuple(df.groupby('episode_index')))
        for path in paths:
            old = json.loads(path.read_text())
            ep = int(old['episode_index'])
            frame = groups[ep].sort_values('frame_index')
            meta = json.loads((project / 'data' / name / 'sidecar' / f'episode_{ep:06d}.json').read_text())
            cache = {}

            def col(key):
                if key not in cache:
                    cache[key] = np.stack(frame[key])
                return cache[key]

            ci = col('chunk.index').reshape(-1)
            starts = np.r_[0, np.flatnonzero(ci[1:] != ci[:-1]) + 1]
            ends = np.r_[starts[1:], len(frame)]
            # Match annotate.common.Episode without video decoding or dataset downloads.
            episode = SimpleNamespace(n=len(frame), chunks=list(zip(starts, ends)), meta=meta, col=col,
                gripper_aperture=col('observation.state')[:, 6], gripper_cmd=col('action')[:, 6],
                success=corrected_success(name, ep, meta['success']), name=name, ep=ep,
                task=meta['task_language'], fps=meta['fps'])
            fresh = build_reference(episode)
            fresh = json.loads(json.dumps(fresh, default=lambda x: x.item() if hasattr(x, 'item') else x.tolist()))
            changed = [k for k in sorted(set(old) | set(fresh)) if old.get(k) != fresh.get(k)]
            results.append(dict(dataset=name, episode_index=ep, saved_version=old['reference_version'],
                                changed_fields=changed))
        print(f'{name}: checked {len(paths)} episodes', flush=True)
    if not results:
        raise ValueError('no saved references found')
    versions = {}
    for version in sorted({x['saved_version'] for x in results}):
        rows = [x for x in results if x['saved_version'] == version]
        versions[version] = dict(episodes=len(rows), changed_episodes=sum(bool(x['changed_fields']) for x in rows),
            changed_fields=dict(Counter(k for x in rows for k in x['changed_fields'])))
    return dict(episodes=len(results), by_saved_version=versions,
                changed_examples=[x for x in results if x['changed_fields']][:30])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, default=Path('/home/aliu/projects/fail-traj-learn'))
    parser.add_argument('--datasets', nargs='+', help='Exact dataset names; defaults to all saved references')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    report = compare(args.project, args.datasets)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2))
    print(json.dumps(report['by_saved_version'], indent=2))


if __name__ == '__main__':
    main()
