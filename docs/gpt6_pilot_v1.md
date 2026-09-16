# GPT-6 observable-label pilot v1

This pilot tests whether sparse GPT-6 trajectory descriptions can become fact-checked training targets without
claiming causal correctness. The fixed taxonomy is
[`scripts/annotate/bench/gpt6_taxonomy_v1.json`](../scripts/annotate/bench/gpt6_taxonomy_v1.json). The pipeline is
[`scripts/annotate/bench/gpt6_pilot.py`](../scripts/annotate/bench/gpt6_pilot.py).

## Protocol

The deterministic seed selected 30 r6 episodes: four from each of six failure-mode strata and six successes.
The annotator received anonymous IDs, task language, paired cameras, measured end-effector/finger state and the
gripper command. Episode outcome, object/contact arrays, oracle references and private identities were withheld.

GPT-6 authored 33 conservative segments. Missing intervals and missing classes mean unknown, never negative.
Segments may carry several role, physical-event, failure-family, subtype and task-stage targets. The authored JSON
was frozen at SHA-256 `a8c7b35dca38f335d1d107c9d2ba8fe2b4c822014fb00ba87212fe95e405cbcc` before privileged references were read.

After the freeze, each positive claim was classified as:

- `supported`: the hidden simulator record contains the required physical evidence;
- `contradicted`: the hidden physical facts reject the claim under the documented tolerance;
- `indeterminate`: available privileged facts do not resolve the semantic claim.

The generated `outputs/gpt6_pilot_v1/training_candidates.json` gives loss weight only to supported positive claims.
Contradicted and indeterminate claims remain present for audit but have `loss_mask: false`. The verifier does not
turn omitted GPT-6 labels into negative targets.

## First result

Across all heads, 134 claims were supported, 40 contradicted and 27 indeterminate. The useful event-level results
were:

| Claim | Supported | Contradicted |
|---|---:|---:|
| grasp acquisition | 18 | 2 |
| controlled transport | 17 | 3 |
| placement | 6 | 9 |
| wrong-object interaction | 3 | 3 |
| release | 0 | 1 |

The pilot therefore supports using verified grasp and transport positives. Raw visual placement and object-identity
claims are not reliable enough to use without privileged filtering.

Sparse selection also had poor physical-event coverage: 25/37 grasp events and 6/6 placements were covered, but
0/71 failed grasps, 0/17 drops and 0/11 releases were explicitly labelled. This cohort is a useful positive-label
pilot, not yet a balanced failure-event training set. A second observable pass should target closing attempts,
loss-of-possession transitions and releases, then be frozen and scored using the same pipeline.

## Reproduction

Run preparation with the external LeRobot environment:

```bash
python scripts/annotate/bench/gpt6_pilot.py select --n 30
bash scripts/annotate/bench/bench.sh gpt6_pilot.py prepare
# Author outputs/gpt6_pilot_v1/authored.json without reading private_manifest.json.
python scripts/annotate/bench/gpt6_pilot.py validate
python scripts/annotate/bench/gpt6_pilot.py freeze
python scripts/annotate/bench/gpt6_pilot.py verify
python -m unittest scripts.annotate.bench.test_gpt6_pilot -v
```

Generated images, private identities, authored labels and reports live under `outputs/gpt6_pilot_v1/`, which is
ignored by Git. Archive that directory with the frozen hash if the pilot is shared or used for training.
