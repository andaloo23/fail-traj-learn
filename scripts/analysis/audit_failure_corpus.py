"""Read-only audit of full_* recordings, saved oracle exports and built RL arrays."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--project', type=Path, default=Path('/home/aliu/projects/fail-traj-learn'))
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    root = args.project
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'annotate'))
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'annotate' / 'bench'))
    import oracle_labels as exporter
    errors, counts, raw_eps = [], Counter(), {}
    sources, families = Counter(), {}

    def check(condition, kind, detail):
        if not condition:
            errors.append(dict(kind=kind, detail=detail))

    excl = json.loads(Path(__file__).with_name('exclusions.json').read_text())
    for d in sorted((root / 'data').glob('full_*')):
        info = json.loads((d / 'meta/info.json').read_text())
        columns = ['episode_index', 'frame_index', 'timestamp', 'index', 'action', 'observation.state',
                   'chunk.index', 'chunk.step', 'next.done', 'next.success', 'priv.sim_time']
        table = pd.concat([pd.read_parquet(f, columns=columns) for f in sorted((d/'data').rglob('*.parquet'))], ignore_index=True)
        counts['datasets'] += 1
        counts['frames'] += len(table)
        check(not table.duplicated(['episode_index', 'frame_index']).any(), 'raw_duplicate_keys', d.name)
        corrections = {int(e['episode_index']): e['action'] for e in excl.get(d.name, [])}
        for ep, df in table.groupby('episode_index', sort=True):
            ep = int(ep)
            key, label = (d.name, ep), f'{d.name}/{ep}'
            df = df.sort_values('frame_index')
            sc = json.loads((d/'sidecar'/f'episode_{ep:06d}.json').read_text())
            n, fps = len(df), float(info['fps'])
            frames = df.frame_index.to_numpy()
            action = np.stack(df.action).astype(np.float32)
            state = np.stack(df['observation.state'])
            check(sc.get('schema_version') == 3, 'schema', label)
            check(sc['length'] == n and np.array_equal(frames, np.arange(n)), 'frame_sequence', label)
            check(sc['fps'] == fps and np.allclose(df.timestamp, frames/fps, atol=1e-5), 'timestamps', label)
            check(np.isfinite(action).all() and np.isfinite(state).all(), 'nonfinite_actions_state', label)
            k = int(sc['n_action_steps'])
            starts = np.arange(0, n, k)
            check(k == 10 and np.array_equal(df['chunk.index'], frames//k) and
                  np.array_equal(df['chunk.step'], frames%k), 'chunk_bookkeeping', label)
            with np.load(d/'sidecar'/f'episode_{ep:06d}.npz') as snap:
                check(np.array_equal(snap['chunk_start_frames'], starts), 'snapshot_starts', label)
                check(len(snap['sim_states']) == len(starts) == sc['n_chunks'], 'snapshot_count', label)
                check(np.isfinite(snap['sim_states']).all() and np.isfinite(snap['init_sim_state']).all(), 'snapshot_finite', label)
            success = bool(sc['success'])
            check(bool(df['next.success'].any()) == success, 'raw_success_sidecar', label)
            check(not df['next.done'].iloc[:-1].any(), 'early_done', label)
            correction = corrections.get(ep)
            corrected = True if correction == 'relabel_success' else False if correction == 'relabel_failure' else success
            counts['episodes'] += 1
            counts['success_raw'] += success
            counts['regular_10_frame_chunks'] += len(starts)
            counts['excluded_episodes'] += correction == 'drop'
            fam = d.name.split('__t')[0]
            stat = families.setdefault(fam, Counter())
            stat['episodes'] += 1
            stat['frames'] += n
            stat['success_raw'] += success
            raw_eps[key] = dict(n=n, fps=fps, starts=starts, action=action, success=corrected,
                                excluded=correction == 'drop', global_start=int(df['index'].iloc[0]))
            sources[str(sc.get('source'))+' / '+str(sc.get('checkpoint_tag'))] += 1
        print(f'raw {d.name}: {len(table)} frames', flush=True)
    references, refstats, boundary_events, collisions = {}, Counter(), [], []
    for p in sorted((root/'bench/references').glob('*/episode_*.json')):
        ref = json.loads(p.read_text())
        key = (ref['dataset'], int(ref['episode_index']))
        references[key] = ref
        refstats['episodes'] += 1
        refstats['version_'+ref['reference_version']] += 1
        if key not in raw_eps:
            errors.append(dict(kind='reference_missing_raw', detail=str(key)))
            continue
        raw = raw_eps[key]
        check(ref['n_frames'] == raw['n'] and ref['fps'] == raw['fps'], 'reference_length_fps', str(key))
        expected = [[int(a), int(min(a+10, raw['n']))] for a in raw['starts']]
        check(ref['chunks'] == expected, 'reference_chunks', str(key))
        check(ref['success'] == raw['success'], 'reference_success', str(key))
        for cl in ref['chunk_labels']:
            check(cl['primary'] in cl['allowed'], 'primary_not_allowed', str(key))
        evs = [e for e in ref.get('events', []) if e['type'] in ('grasp', 'drop', 'release')]
        for ev in evs:
            refstats['event_'+ev['type']] += 1
            check(0 <= ev['index'] < raw['n'], 'event_bounds', str(key))
            if ev['chunk'] != ev['index']//10:
                boundary_events.append(dict(episode=list(key), type=ev['type'], frame=ev['index'],
                                            action_chunk=ev['chunk'], observed_chunk=ev['index']//10))
        byframe = Counter(e['index'] for e in evs)
        if any(v > 1 for v in byframe.values()):
            collisions.append(dict(episode=list(key), frames={str(k):v for k,v in byframe.items() if v>1}))
    exports = {}
    for path in sorted((root/'bench').glob('oracle_labels*.parquet')):
        df = pd.read_parquet(path)
        keys = ['dataset', 'episode_index', 'frame_index']
        check(not df.duplicated(keys).any(), 'export_duplicate_keys', path.name)
        stats = dict(frames=len(df), episodes=df.groupby(keys[:2]).ngroups,
                     source=df.source.value_counts().to_dict(), frame_labels=df.label.value_counts().to_dict(),
                     frame_q={str(k):int(v) for k,v in df.q.value_counts().items()},
                     events=df.event_at_frame.value_counts().to_dict())
        chunks = df.drop_duplicates(['dataset', 'episode_index', 'chunk'])
        stats['chunk_labels'] = chunks.label.value_counts().to_dict()
        stats['chunks'] = len(chunks)
        stats['episode_causes'] = df.drop_duplicates(keys[:2]).cause.fillna('null').value_counts().to_dict()
        stats['episode_failure_modes'] = df.drop_duplicates(keys[:2]).failure_mode.value_counts().to_dict()
        stats['failed_episodes_without_primary_failure_chunk'] = sum(not (g.label == 'failure_inducing').any()
            for _, g in chunks[~chunks.success].groupby(keys[:2]))
        stats['success_episodes_with_failure_chunk'] = chunks[chunks.success & (chunks.label == 'failure_inducing')].groupby(keys[:2]).ngroups
        stats['visible_equals_decisive_all_rows'] = bool(df.visible_failure_chunk.fillna(-1).equals(df.decisive_error_chunk.fillna(-1)))
        stats['recoverable_known_rows'] = int(df.recoverable_until_chunk.notna().sum())
        stats['target_events'] = df[df.event_target].event_at_frame.value_counts().to_dict()
        stats['missed_release_on_success_frames'] = int((df.event_missed_release & df.success).sum())
        stats['missing_class_known_masks'] = not any('known' in c for c in df.columns)
        mismatch, examples = Counter(), []
        for key, g in df.groupby(keys[:2], sort=False):
            key = (key[0], int(key[1]))
            if key not in references or key not in raw_eps:
                errors.append(dict(kind='export_missing_reference_or_raw', detail=str(key)))
                continue
            expected = exporter.frame_table(references[key], raw_eps[key]['global_start'])
            actual = g.sort_values('frame_index').reset_index(drop=True)
            if len(actual) != len(expected):
                errors.append(dict(kind='export_length', detail=str(key)))
                continue
            for col in expected:
                a, b = actual[col], expected[col]
                same = (a.eq(b) | (a.isna() & b.isna())).fillna(False)
                count = int((~same).sum())
                if count:
                    mismatch[col] += count
                    if len(examples) < 20:
                        examples.append(dict(episode=list(key), column=col, rows=count))
        stats['reexport_mismatched_rows_by_column'] = dict(mismatch)
        stats['reexport_mismatch_examples'] = examples
        eps = pd.read_parquet(path.with_name(path.name.replace('oracle_labels', 'oracle_episodes')))
        stats['episode_table_rows'] = len(eps)
        check(set(df.groupby(keys[:2]).size().index) == set(zip(eps.dataset, eps.episode_index)), 'episode_export_keys', path.name)
        stats['sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        exports[path.name] = stats
        print(f"export {path.name}: {stats['episodes']} episodes; reexport mismatches {dict(mismatch)}", flush=True)
    built = {}
    labels = pd.read_parquet(root/'bench/oracle_labels.parquet').set_index(['dataset', 'episode_index', 'frame_index'])
    for directory in sorted((root/'rl/datasets').glob('object_v*')):
        eps = pd.read_parquet(directory/'episodes.parquet')
        arrays = {k:np.load(directory/(k+'.npy'), mmap_mode='r') for k in
                  ('obs', 'next_obs', 'action', 'reward', 'done', 'timeout', 'ep_id', 'frame_index')}
        problems, coverage = Counter(), 0
        for row in eps.itertuples():
            key = (row.dataset, int(row.episode_index))
            ix = np.flatnonzero(arrays['ep_id'] == row.ep_id)
            raw = raw_eps[key]
            if len(ix) != raw['n']: problems['length'] += 1
            if not np.array_equal(arrays['frame_index'][ix], np.arange(len(ix))): problems['frames'] += 1
            if not np.array_equal(arrays['action'][ix], raw['action']): problems['actions'] += 1
            if raw['excluded']: problems['contains_excluded'] += 1
            if bool(row.success) != raw['success']: problems['outcome'] += 1
            if not np.array_equal(arrays['next_obs'][ix[:-1]], arrays['obs'][ix[1:]]): problems['next_obs'] += 1
            if arrays['done'][ix[:-1]].any() or not arrays['done'][ix[-1]]: problems['done'] += 1
            r = arrays['reward'][ix]
            if r[:-1].any() or r[-1] != int(row.success): problems['reward'] += 1
            index = pd.MultiIndex.from_arrays([[key[0]]*len(ix), [key[1]]*len(ix), np.arange(len(ix))])
            coverage += int(index.isin(labels.index).sum())
        finite = {name:all(np.isfinite(arrays[name][i:i+8192]).all() for i in range(0,len(arrays[name]),8192))
                  for name in ('obs', 'next_obs', 'action', 'reward')}
        built[directory.name] = dict(episodes=len(eps), frames=len(arrays['obs']), obs_dim=arrays['obs'].shape[1],
            labeled_frames=coverage, mismatched_episodes=dict(problems), finite=finite)
        print('built', directory.name, built[directory.name], flush=True)
    report = dict(created=datetime.now(timezone.utc).isoformat(), scope='all full_* recordings; existing references and exports; object_v1/v2',
        raw=dict(counts), families=families, structural_errors=errors, references=dict(refstats),
        raw_episodes_without_references=sum(k not in references for k,v in raw_eps.items() if not v['excluded']),
        annotation_action_vs_observation_chunk=dict(count=len(boundary_events), examples=boundary_events[:20]),
        reference_simultaneous_physical_events=dict(episodes=len(collisions), examples=collisions[:20]),
        exports=exports, built=built, collection_sources=dict(sources),
        limits=['No new visual semantic audit or exhaustive simulator replay in this script.',
                'Reexport comparison checks serialization against saved references, not correctness of oracle rules.',
                'No label corrections or dataset mutations performed.'])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, default=lambda x:x.item() if hasattr(x,'item') else str(x)))
    print('REPORT', args.out, 'structural errors', len(errors), flush=True)


if __name__ == '__main__':
    main()
