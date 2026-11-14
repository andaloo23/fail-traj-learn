"""Freeze aligned labels from preserved native outputs; no model execution."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/distill'))
import oopsie_recipe_data as data
import score_recipe_suite as scoring


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def labels(segments, n):
    result = [None] * n
    for s in segments:
        a, b = s['start_frame'], s['end_frame']
        assert 0 <= a < b <= n and all(x is None for x in result[a:b])
        result[a:b] = [int(s['failure'])] * (b - a)
    assert None not in result
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    assert not a.out.exists()
    study_path = ROOT / 'outputs/oopsie_distillation_full_v1/study.json'
    study = json.loads(study_path.read_text())
    source = ROOT / study['config']['source_run']
    manifest = source / 'manifest.json'
    assert sha(manifest) == study['source_manifest_sha256']
    episodes = {e['id']: e for e in json.loads(manifest.read_text())['episodes']}
    canonical = {e['episode']: e for e in study['episodes']}
    presentation_path = ROOT / 'outputs/astra_joint_presentation_50_20261109_v1/manifest.json'
    presentation = json.loads(presentation_path.read_text())
    chapters = {c['episode']: c for c in presentation['chapters']}
    hashes = {str(study_path.relative_to(ROOT)): sha(study_path),
              str(manifest.relative_to(ROOT)): sha(manifest),
              str(presentation_path.relative_to(ROOT)): sha(presentation_path)}
    for name, expected in presentation['source_predictions_sha256'].items():
        path = ROOT / name
        assert sha(path) == expected, name
        hashes[name] = expected
    flora_root = ROOT / 'outputs/flora_development50_20261110_v2'
    flora_path = flora_root / 'results/dense_3572125/dense.jsonl'
    flora_rows = [json.loads(s) for s in flora_path.read_text().splitlines()]
    assert [r['id'] for r in flora_rows] == study['development_ids']
    flora = {r['id']: r for r in flora_rows}
    hashes[str(flora_path.relative_to(ROOT))] = sha(flora_path)
    flora_refs = json.loads((flora_root / 'evaluation/reference.json').read_text())['episodes']
    prepared, total = [], dict(tp=0, fp=0, fn=0, tn=0, unknown_positive=0, unknown_negative=0)
    for eid in study['development_ids']:
        e = episodes[eid]
        assert e['split'] == 'development'
        native = source / 'traces' / f'{eid}_sol_r01' / 'annotation.md'
        assert sha(native) == canonical[eid]['annotation_sha256']
        hashes[str(native.relative_to(ROOT))] = sha(native)
        teacher_segments = data.parse_prediction(native.read_text(encoding='utf-8').split('## Failure annotations')[0], eid, 0, e['n_frames'])
        teacher = labels(teacher_segments, e['n_frames'])
        assert teacher == flora_refs[eid]['frame_labels'] == labels(chapters[eid]['teacher'], e['n_frames'])
        qwen = [None] * e['n_frames']
        paths = sorted((ROOT / 'outputs/oopsie_distillation_local_sequential_v1/predictions/joint').glob(eid + '_*_binary.json'))
        for path in paths:
            raw = json.loads(path.read_text())
            assert not raw['hit_max']
            start, end = raw['core_start'], raw['core_end']
            assert all(v is None for v in qwen[start:end])
            parsed = data.parse_prediction(raw['text'], eid, start, end)
            for s in parsed:
                qwen[s['start_frame']:s['end_frame']] = [int(s['failure'])] * (s['end_frame'] - s['start_frame'])
        assert None not in qwen and qwen == labels(chapters[eid]['joint'], e['n_frames'])
        row = flora[eid]
        assert row['invalid_clips'] == 0 and all(c['valid'] for c in row['clips'])
        assert row['num_frames'] == e['n_frames'] and row['fps'] == e['fps']
        assert len(row['frame_scores']) == e['n_frames'] and set(row['frame_scores']) <= {1, 2, 3}
        for k, v in scoring.counts(qwen, teacher).items():
            total[k] += v
        prepared.append(dict(id=eid, lab=e['lab'], task=e['task'], n_frames=e['n_frames'], fps=e['fps'],
                             astra=teacher, qwen=qwen, flora_native=row['frame_scores']))
    official = json.loads((ROOT / 'outputs/oopsie_distillation_local_sequential_v1/arm_scores/joint.json').read_text())['metrics']
    assert scoring.metrics(total) == official
    assert len(prepared) == 50 and sum(e['n_frames'] for e in prepared) == 8132
    a.out.mkdir(parents=True)
    result = dict(protocol='astra_qwen_flora_pairwise_v1', teacher_display_name='Astra',
                  teacher_actual_source='gpt-6.1-sol', teacher_display_name_is_alias=True,
                  qwen_recipe='joint', flora_job=3572125, source_sha256=hashes,
                  split='development', final_test_accessed=False, new_model_calls=0,
                  native_outputs_modified=False, episodes=prepared)
    (a.out / 'aligned_labels_internal.json').write_text(json.dumps(result, indent=2) + '\n')
    print(f'Frozen {len(prepared)} episodes / 8132 frames from native outputs; all provenance hashes checked.')


if __name__ == '__main__':
    main()
