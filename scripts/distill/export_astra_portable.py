"""Export existing Astra labels and optional original videos for another computer.

Uses only Python's standard library. Never submits requests or changes the run.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import tarfile
import zipfile


REPO = Path(__file__).resolve().parents[2]
DEFAULT = REPO / 'outputs/corral_astra_rich_failure_v8_2_carryforward_batch_v3'


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def export(run, destination, include_videos=False):
    run = run.resolve()
    if destination.exists():
        raise ValueError(f'Choose a new destination; already exists: {destination}')
    rows = [json.loads(line) for line in (run / 'dataset.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()]
    ids = [row['episode_id'] for row in rows]
    catalog = read(run / 'catalog.json')
    if not read(run / 'dataset_manifest.json')['complete'] or len(set(ids)) != len(rows):
        raise ValueError('Expected a complete dataset with unique episode IDs')
    if set(ids) != {item['id'] for item in catalog}:
        raise ValueError('Labels and episode catalog do not match')
    for row in rows:
        folder = run / 'canonical' / (row['episode_id'] + '_final')
        if row['native_response'] != f'canonical/{row["episode_id"]}_final/response.json':
            raise ValueError(f'Unexpected response path: {row["episode_id"]}')
        response = folder / 'response.json'
        if sha(response) != row['response_sha256']:
            raise ValueError(f'Changed native response: {row["episode_id"]}')
        if read(response)['model'] != row['teacher_recorded_model']:
            raise ValueError(f'Teacher identity mismatch: {row["episode_id"]}')
        if (folder / 'annotation.md').read_text(encoding='utf-8') != row['assistant_target']:
            raise ValueError(f'Changed annotation: {row["episode_id"]}')

    # Explicit allowlist: no environment files, credentials, or request-image payloads.
    names = ['dataset.jsonl', 'dataset_manifest.json', 'catalog.json', 'selection.json',
             'run_plan.json', 'plan_identity.json', 'recipe.json', 'prompt.md',
             'window_prompt.md', 'reconciliation_prompt.md', 'report.md',
             'review.html', 'review_data.json', 'completion.json', 'all_frames_recipe_audit.json']
    files = {name: run / name for name in names if (run / name).is_file()}
    for path in sorted((run / 'canonical').glob('*/*')):
        if path.is_file() and path.name in ('annotation.md', 'response.json', 'parsed.json', 'status.json'):
            files[path.relative_to(run).as_posix()] = path
    for path in sorted((run / 'reviews').glob('*.md')):
        files[path.relative_to(run).as_posix()] = path
    for name in ['scripts/distill/serve_oopsie_review.py', 'scripts/tacc/serve_flora_review.py']:
        files[name] = REPO / name

    videos = {}
    for item in catalog:
        for video in item['videos']:
            name = video['url']
            if not name.startswith('source_files/') or len(Path(name).parts) != 2:
                raise ValueError(f'Nonportable video path: {name}')
            if name in videos and videos[name] != video['sha256']:
                raise ValueError(f'Conflicting video hashes: {name}')
            videos[name] = video['sha256']
    if include_videos:
        for name, digest in videos.items():
            if sha(run / name) != digest:
                raise ValueError(f'Video checksum mismatch: {name}')

    destination.mkdir(parents=True)
    prefix = 'oopsiedata-astra-v8.2-1000'
    metadata = dict(exported_utc=datetime.now(timezone.utc).isoformat(), source_run=run.name,
                    episodes=len(rows), recorded_models=dict(Counter(r['teacher_recorded_model'] for r in rows)),
                    human_verified=sum(bool(r['human_verified']) for r in rows),
                    unique_original_videos=len(videos), videos_in_separate_archive=include_videos,
                    files={name: sha(path) for name, path in sorted(files.items())},
                    video_sha256=dict(sorted(videos.items())))
    readme = f'''# Portable Astra labels

{len(rows)} real OopsieData episodes with rich V8.2 Markdown labels.
Native teacher identity is preserved in dataset.jsonl and canonical/*/response.json.
Only {metadata['human_verified']} dataset rows are marked human_verified; schema validation is not human adjudication.

Read report.md for the episode index and canonical/C0001_final/annotation.md for an example.
dataset.jsonl contains the assistant targets. catalog.json and selection.json map labels to source episodes and cameras.
The canonical folder includes final native outputs and intermediate carry-forward outputs.
Prompt and recipe snapshots are included. This is a portable label/review export, not a full frozen-request or training-data archive.
Original collection artifacts remain on the source computer. Model-input images and native HDF5 files are excluded.

## On your Mac

Extract {prefix}-labels.zip. If you also have {prefix}-videos.tar,
extract both archives into the same parent directory. They share the {prefix}/ folder.

```sh
unzip {prefix}-labels.zip
tar -xf {prefix}-videos.tar  # Only when transferring videos too
cd {prefix}
python3 scripts/distill/serve_oopsie_review.py --directory . --port 8814
```

Open http://127.0.0.1:8814/review.html for video playback and time-aligned labels.
Video playback requires the separate videos archive. Reading Markdown labels requires no server.
The server supports seeking and saves new Markdown notes under reviews/.

Verify transferred archives from their parent directory with:

```sh
shasum -a 256 -c SHA256SUMS
```

EXPORT_MANIFEST.json records SHA-256 checksums of exported files and original videos.
Historical provenance may mention source-computer paths; review media and native responses use relative paths.
'''
    labels = destination / f'{prefix}-labels.zip'
    with zipfile.ZipFile(labels, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name, path in sorted(files.items()):
            archive.write(path, f'{prefix}/{name}')
        archive.writestr(f'{prefix}/README.md', readme)
        archive.writestr(f'{prefix}/EXPORT_MANIFEST.json', json.dumps(metadata, indent=2) + '\n')
    archives = [labels]
    if include_videos:
        media = destination / f'{prefix}-videos.tar'
        with tarfile.open(media, 'x', format=tarfile.PAX_FORMAT, dereference=True) as archive:
            for name in sorted(videos):
                # Dereference Windows hardlinks so extraction never depends on the source machine.
                archive.add(run / name, arcname=f'{prefix}/{name}', recursive=False)
        archives.append(media)
    (destination / 'SHA256SUMS').write_text(''.join(f'{sha(path)}  {path.name}\n' for path in archives), encoding='utf-8')
    for path in archives:
        print(f'{path}: {path.stat().st_size:,} bytes')
    print(f'Validated {len(rows)} labels; recorded models: {metadata["recorded_models"]}')
    return archives


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, default=DEFAULT)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--include-videos', action='store_true')
    args = parser.parse_args()
    export(args.run, args.out, args.include_videos)
