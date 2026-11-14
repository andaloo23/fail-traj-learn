"""Freeze compatible saved VLM outputs for offline similarity experiments.

No human reference, simulator label, annotation generation, or paid API is used.
"""
import hashlib
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/annotate'))
from review_api_experiment import parse_segments

OUT = ROOT / 'outputs/similarity_exploration_v1'
RUNS = {
    'semantic': ('frame_selection_semantic_v2', ('A', 'B', 'C', 'D', 'F')),
    'windows': ('frame_selection_windows_v1', ('U', 'P', 'W')),
    'full': ('frame_selection_full_coverage_v1', ('A', 'B', 'C', 'D', 'F')),
    'h_windows': ('h_pipeline_evaluation_v1', ('U', 'P', 'W')),
}

def load(path):
    return json.loads(path.read_text(encoding='utf-8'))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    corpus, inventory, manifests = [], [], {}
    camera_groups = defaultdict(list)
    for name, (folder, arms) in RUNS.items():
        root = ROOT / 'outputs' / folder
        manifest = load(root / 'manifest.json')
        manifests[name] = sha(root / 'manifest.json')
        for ep in manifest['episodes']:
            eid = ep['id']
            source = load(root / eid / 'input.json')
            camera_hash = source['source_sha256']['cameras.npz']
            camera_groups[camera_hash].append(eid)
            for arm in arms:
                ident = eid + '_' + arm
                answer = root / 'responses' / (ident + '.md')
                attempt_path = root / 'attempts' / (ident + '.json')
                attempt = load(attempt_path) if attempt_path.exists() else {}
                segments, warnings = parse_segments(answer.read_text(encoding='utf-8'), ep['n_frames']) if answer.exists() else ([], [])
                eligible = attempt.get('status') == 'completed' and bool(segments) and not warnings and all('progress' in s and 'failure' in s for s in segments)
                cell = {'id': name + '/' + ident, 'status': attempt.get('status', 'missing'), 'eligible': eligible,
                        'warnings': warnings, 'answer_path': str(answer.relative_to(ROOT)), 'answer_sha256': sha(answer) if answer.exists() else None}
                inventory.append(cell)
                if not eligible:
                    continue
                assert segments[0]['start'] == 0 and segments[-1]['end'] == ep['n_frames']
                assert all(a['end'] == b['start'] for a, b in zip(segments, segments[1:]))
                corpus.append({**cell, 'episode': eid, 'episode_group': camera_hash, 'source': name + '/' + arm,
                               'run': name, 'arm': arm, 'task': ep['task'], 'n_frames': ep['n_frames'], 'fps': ep['fps'],
                               'provider': attempt.get('provider'), 'model': attempt.get('returned_model'),
                               'prompt_revision': manifest['settings'].get('prompt_revision'), 'segments': segments})
    # Prevent leakage if the same source appears under different episode names.
    for record in corpus:
        record['episode_alias'] = record['episode']
        record['episode'] = min(camera_groups[record['episode_group']])
    summary = {'records': len(corpus), 'segments': sum(len(r['segments']) for r in corpus),
               'episodes': sorted({r['episode'] for r in corpus}), 'episode_groups': len({r['episode_group'] for r in corpus}),
               'tasks': dict(Counter(r['task'] for r in corpus)), 'sources': dict(Counter(r['source'] for r in corpus)),
               'models': dict(Counter(r['model'] for r in corpus)), 'unavailable': sum(not c['eligible'] for c in inventory),
               'manifest_sha256': manifests, 'inventory': inventory, 'human_references_used': False, 'paid_api_calls': 0,
               'scope': 'Only compatible explicit four-state complete partitions; older positive-only annotations are excluded, never filled as negatives.'}
    (OUT / 'corpus.json').write_text(json.dumps(corpus, indent=2), encoding='utf-8')
    summary['corpus_sha256'] = sha(OUT / 'corpus.json')
    (OUT / 'corpus_manifest.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('inventory','manifest_sha256')}, indent=2))

if __name__ == '__main__':
    main()
