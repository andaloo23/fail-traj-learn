# Oracle annotations: current contract and limitations

The simulator oracle supplies **rule-derived weak supervision** for existing RL baselines and
candidate labels for failure-representation learning. It is not a source of verified causal action
credit. The [2026-09-13 verification](failure_data_verification.md) confirms serialization and
recording consistency; the [frozen r6 semantic audit](oracle_r6_audit.md) still identifies unresolved
disagreements. VLM/assistant annotation experiments remain tools for review and descriptions;
reliable autonomous semantic supervision has not been established.

## Files and versions

- `scripts/annotate/bench/oracle_reference.py`: per-episode reference builder, currently r6.
- `$FTL_PROJ/bench/references/<dataset>/episode_XXXXXX.json`: physical events, stage/hold traces,
  episode diagnosis, per-chunk primary/allowed roles, and the rules that produced them.
- `scripts/annotate/bench/oracle_labels.py`: expands references into frame-aligned parquet labels.
- `oracle_labels.parquet`: 1,341 r6 episodes; `oracle_labels_r6_object.parquet`: 1,300 object episodes
  in the verified snapshot. The larger reference directory also includes 720 r3 and 19 r4 episodes.

Record and check reference versions before exporting. The exporter uses the current source-version
constant; invoking it on a mixed-version reference directory must not be interpreted as upgrading
those older references. Use the fresh-reference comparison in the verification guide first.

## Meaning of the exported fields

| Field | Meaning and limitation |
|---|---|
| `label` | Primary role repeated over a chunk: progress, failure_inducing, recovery, neutral, aftermath |
| `allowed` | Alternative roles admitted by the rule; not independent human votes |
| `q` | Rule-ambiguity weight: 1 for one allowed role, 0.5 for two, 0.25 for three or more, 0 for unlocalized rules |
| `cause`, `failure_mode` | Episode-level diagnosis repeated across frames; not a local cause annotation |
| `decisive_error_chunk` | Suspected decisive action chunk inferred by rules |
| `failure_onset_chunk` | First singleton failure-inducing chunk, with decisive-chunk fallback |
| `visible_failure_chunk` | Currently a copy of decisive_error_chunk, not an independently observed timestamp |
| `recoverable_until_chunk` | Unpopulated; no validated recovery boundary |
| `event_type_in_chunk` | First event assigned to the action-credit chunk |
| `event_at_frame` | Physical grasp/drop/release on its observed frame, or none |
| `event_target`, `event_hold_frames` | Target-object indicator and associated hold duration |
| `event_missed_release` | Outcome-based proxy; exempts the last target release in a successful episode |
| `held`, `success`, `source` | Frame hold state, corrected episode outcome and exporter version |

Event action credit can point to the chunk containing `last_before`, while event observation time is
`index`/`first_after`. These differ at some chunk boundaries. Keep both clocks; event localization
in the new manifest uses the observed frame. Grasp/drop/release distinctions depend on contact,
debouncing and gripper-command rules, not semantic certainty.

## Conversion for the new learner

Use the [failure-training manifest](failure_training.md), not the legacy parquet as an implicit
complete annotation contract:

1. Review segment roles and preserve uncertainty; q=0 should receive no supervision. Even q=1
   is not a calibrated probability that a label is correct.
2. Assign local `failure_types` deliberately. Broadcasting the episode cause over every segment
   would create unsupported local targets.
3. Export physical event timestamps separately from suspected contributing/decisive intervals.
4. Add explicit per-class reviewed coverage. A successful episode can contain recovered failures;
   neutral roles and missing annotations do not establish negatives.
5. Lock episode/source groups before model selection, and fit preprocessing on training data only.

The legacy `labels.py`/`segments.py` path still supports ordinal-advantage and reward baselines.
Those experiments do not establish that progress implies positive advantage, recovery succeeded,
or an aftermath action is useless. The current RL actor is frame-based; the new failure model uses
chunks. Neither receives oracle semantic labels as deployment inputs.

## Remaining annotation work

Review a seed set of local roles and observed events; correct or mask known r6 disagreement cases.
Geometry can help validate placements and contextual descriptions. Restored-snapshot repair studies
can test specific interventions, but unsuccessful sampled repairs do not prove irrecoverability,
and recoverability need not be monotonic in time. Existing fixture scenes may lack the fixed poses
needed for exact replay. Real-robot temporal annotations and access remain future work.
