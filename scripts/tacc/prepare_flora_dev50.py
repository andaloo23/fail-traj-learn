"""Freeze FLORA inference inputs from the existing development split (no labels)."""
import hashlib
import json
from pathlib import Path
import shutil

from PIL import Image, ImageDraw


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    source = Path('outputs/oopsie_rich_failure_v8_1_500_batch_v1')
    study_path = Path('outputs/oopsie_distillation_full_v1/study.json')
    out = Path('outputs/flora_development50_20261109_v1')
    study = json.loads(study_path.read_text())
    assert sha(source / 'manifest.json') == study['source_manifest_sha256']
    manifest = json.loads((source / 'manifest.json').read_text())
    indexed = {e['id']: e for e in manifest['episodes']}
    ids = study['development_ids']
    assert len(ids) == len(set(ids)) == 50
    out.mkdir(exist_ok=False)
    episodes, jobs = [], []
    for ident in ids:
        e = indexed[ident]
        assert e['split'] == 'development'
        order = (['left', 'top', 'right'] if e['lab'] == 'Princeton_PRISM'
                 else ['left_base_cam', 'wrist_cam', 'right_base_cam'])
        videos = {v['camera']: v for v in e['videos']}
        assert set(order) == set(videos)
        cameras = []
        for name in order:
            v = videos[name]
            path = source / v['url']
            assert sha(path) == v['sha256'], path
            rel = Path('media') / ident / (name + '.mp4')
            dest = out / rel
            dest.parent.mkdir(exist_ok=True, parents=True)
            shutil.copyfile(path, dest)
            cameras.append(dict(camera=name, path=rel.as_posix(), sha256=v['sha256'],
                                bytes=path.stat().st_size))
        episodes.append(dict(id=ident, task=e['task'], lab=e['lab'], n_frames=e['n_frames'],
                             fps=e['fps'], cameras=cameras))
        jobs.append(dict(id=ident, task=e['task'], videos=[c['path'] for c in cameras]))
    for page in range(5):
        canvas = Image.new('RGB', (1260, 1900), 'white')
        draw = ImageDraw.Draw(canvas)
        for row, ident in enumerate(ids[page * 10:(page + 1) * 10]):
            e = indexed[ident]
            y = row * 190
            names = [v['camera'] for v in e['videos']]
            draw.text((5, y + 3), ident + ' | source panels: ' + ', '.join(names), fill='black')
            for col, frame in enumerate([0, e['n_frames'] // 2, e['n_frames'] - 1]):
                im = Image.open(source / e['images'][frame]['path']).convert('RGB')
                im.thumbnail((415, 150))
                canvas.paste(im, (col * 420, y + 22))
                draw.text((col * 420, y + 173), f'frame {frame}', fill='black')
        canvas.save(out / f'camera_review_{page + 1}.jpg', quality=92)
    (out / 'dense_jobs.jsonl').write_text(''.join(json.dumps(j) + '\n' for j in jobs))
    metadata = dict(protocol='flora_frozen_development50_v1', dataset=manifest['repo'],
                    dataset_revision=manifest['revision'], study_sha256=sha(study_path),
                    source_manifest_sha256=sha(source / 'manifest.json'),
                    development_ids=ids, episodes=episodes, teacher_labels_in_model_input=False,
                    camera_mapping=dict(visually_reviewed=False,
                                        positions=['left', 'center', 'right'],
                                        note='Collage positions only; no inferred calibration.'))
    (out / 'inputs.json').write_text(json.dumps(metadata, indent=2) + '\n')
    print(json.dumps(dict(out=str(out), episodes=len(jobs), videos=sum(len(e['cameras']) for e in episodes),
                         frames=sum(e['n_frames'] for e in episodes),
                         bytes=sum(c['bytes'] for e in episodes for c in e['cameras']))))


if __name__ == '__main__':
    main()
