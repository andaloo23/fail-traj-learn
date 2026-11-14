"""Build a derived, native-FPS review of preserved FLORA dense predictions."""
import hashlib
import json
from pathlib import Path
import shutil

import av


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / 'outputs/flora_oopsie_ten_completed_3533752'
SOURCE = ROOT / 'outputs/oopsiedata_ten_reference_v1'
OUT = ROOT / 'outputs/flora_oopsie_ten_review_3533752_v1'


def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def main():
    dense = RESULTS / 'flora_oopsie_ten_reference_dense_3533752'
    assert json.loads((dense / 'validation.json').read_text())['structurally_valid']
    run = json.loads((dense / 'run.json').read_text())
    rows = [json.loads(s) for s in (dense / 'dense.jsonl').read_text().splitlines() if s.strip()]
    jobs = {r['id']: r for r in map(json.loads, (SOURCE / 'dense_jobs.jsonl').read_text().splitlines())}
    provenance = {r['id']: r for r in json.loads((SOURCE / 'provenance.json').read_text())['episodes']}
    assert len(rows) == 10 and len({r['id'] for r in rows}) == 10
    (OUT / 'videos').mkdir(parents=True, exist_ok=True)
    data = []
    for row in rows:
        assert row['task'] == jobs[row['id']]['task']
        end = 0
        for s in row['segments']:
            assert s['start_frame'] == end < s['end_frame'] <= row['num_frames']
            assert row['frame_scores'][end:s['end_frame']] == [s['score']] * (s['end_frame'] - end)
            assert s['label'] == {1: 'failure', 2: 'suboptimal', 3: 'normal'}[s['score']]
            end = s['end_frame']
        assert end == row['num_frames']
        cameras = []
        by_hash = {c['sha256']: c for c in provenance[row['id']]['cameras'] if 'excluded_duplicate_of' not in c}
        for i, relative in enumerate(jobs[row['id']]['videos']):
            path = (SOURCE / relative).resolve()
            digest = sha(path)
            camera = by_hash[digest]
            assert digest in run['video_sha256'].values()
            with av.open(str(path)) as video:
                stream = video.streams.video[0]
                assert stream.codec_context.name == 'h264'
                assert abs(float(stream.average_rate) - row['fps']) < 1e-6
                count = 0
                for n, frame in enumerate(video.decode(video=0)):
                    assert abs(float(frame.time) - n / row['fps']) < 1e-5
                    count += 1
                assert count == row['num_frames']
            target = OUT / 'videos' / f'{row["id"]}_{i}.mp4'
            if not target.exists():
                shutil.copyfile(path, target)
            assert sha(target) == digest
            cameras.append(dict(name=camera['camera'], src='videos/' + target.name, sha256=digest))
        data.append({k: row[k] for k in ('id', 'task', 'fps', 'num_frames', 'segments', 'invalid_clips')} | dict(cameras=cameras))
        print(f'{row["id"]}: {len(cameras)} cameras, {row["num_frames"]} native frames, {len(row["segments"])} segments', flush=True)
    payload = json.dumps(data, ensure_ascii=True).replace('<', r'\u003c')
    template = Path(__file__).with_name('flora_ten_review_v1.html').read_text(encoding='utf-8')
    (OUT / 'index.html').write_text(template.replace('__DATA__', payload), encoding='utf-8')
    shutil.copyfile(RESULTS / 'dense_annotations_derived.md', OUT / 'annotations.md')
    (OUT / 'README.md').write_text(
        '# FLORA ten-episode video review\n\nDerived presentation of preserved job 3533752 dense annotations. '
        'The original H.264 camera videos are copied byte for byte; every native frame and original timing is retained. '
        'Only cameras supplied to the dense run are displayed. Segment end frames are exclusive. '
        'Native labels remain failure / suboptimal / normal; no binary remapping is applied. '
        'Predictions have not been human verified. Rubric outputs failed structural validation and are excluded from this dense viewer. '
        'Native result files and review notes are unchanged.\n', encoding='utf-8')
    (OUT / 'provenance.json').write_text(json.dumps(dict(
        derived=True, source_dense_sha256=sha(dense / 'dense.jsonl'),
        jobs_sha256=sha(SOURCE / 'dense_jobs.jsonl'), episodes=data), indent=2) + '\n', encoding='utf-8')
    print('http://127.0.0.1:8802/', flush=True)


if __name__ == '__main__':
    main()
