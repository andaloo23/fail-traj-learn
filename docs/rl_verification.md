# RL verification — 2026-09-09

The saved numerical results are reproducible from the available artifacts. The basic
transition construction and IQL update wiring pass inspection and the checks below.
However, the event-reward implementation does not implement the described experiment,
and several interpretations in `rl_results.md` need correction before these results
can support the proposal's claims.

This audit adds a read-only verifier, `scripts/rl/verify_results.py`. It does not change
training semantics or overwrite historical checkpoints/results. Its JSON output is
saved at `outputs/rl_verification/audit.json` (generated, not tracked).

## Status of each finding

All seven findings below have been **fixed in code** and the label export regenerated.
The saved runs, checkpoints and closed-loop evaluations are untouched: nothing has been
retrained, so `rl_results.md` still reports pre-fix behaviour and says so at the top.

| # | finding | fix | affects saved results? |
|---|---|---|---|
| 1 | `events` never rewarded a grasp, penalised every release | `oracle_labels.py:event_frames` exports per-frame event timestamps, object and hold length; `segments._event_reward` keys off them and refuses an export without them | **yes** — the `events` runs must be rerun |
| 2 | potential control not policy-invariant | `segments._potential`: exclusive count so `Phi(s_0)=0`, denominator is the fixed step budget, terminal `Phi=0`; shaping now sums to 0 per episode (verified 1e-6) and the docstring states the limits of the guarantee | **yes** — the `potential` run must be rerun |
| 3 | constant-negative sign baseline misreported as 31% | `eval_critic.py` reports `const_positive_sign_agree` (0.937), `const_negative_sign_agree` (0.063), per-class rates and `adv_sign_agree_balanced`; `rl_results.md` section 2 corrected | no — narrative only |
| 4 | AUC mishandled ties | `eval_critic.auc` uses mid-ranks; verified equal to an independent pairwise AUC on all four checkpoints and 0.5 on an all-tied input | no — the four values are unchanged |
| 5 | whitening fit on the whole corpus | `replay.OfflineData.norm_mean/norm_std` fit on `train_idx` only; `train.save_checkpoint` always stores the statistics actually used | future runs only |
| 6 | evaluation provenance discarded | `train.run_eval` keeps the per-episode rows; each row records seed, `init_state_id`, shift draw, fallback flag and a settled-state hash; `--init-state-offset` addresses the base layout explicitly | future runs only |
| 7 | metric names overstated what was measured | `v_monotonicity` renamed `v_end_above_start`; `adv_decisive_margin` is now the within-episode difference averaged over episodes, with the old pooling kept as `adv_decisive_margin_pooled` | no — the paired recomputation agrees |

Regression tests for 1, 2, 4 and 5 are in `scripts/rl/test_rl.py` (`TestEventReward`,
`TestPotentialShaping`, `TestAuc`, `TestNormalisationSplit`) and for 1 in
`scripts/annotate/bench/test_oracle_labels.py`. The suites are 42 and 12 tests, both green.

## Confirmed findings, in priority order

1. **The event mode never rewards grasps on this corpus.**
   `segments.py:156` requires both a grasp event in the chunk and `held=True` at the
   *first frame* of that chunk. The label exporter repeats the event type across the
   chunk, while `held` describes the individual frame. Across 1,558 grasp chunks,
   **zero** satisfy the reward condition. All positive grasp rewards are absent.
   The same function penalizes every release, without checking whether it missed:
   **161 of 353 release penalties occur in successful episodes**. There are also 255
   drop penalties. Thus the published `events` runs tested sparse negative penalties,
   not the stated positive-grasp / negative-drop / missed-release reward.
   Preserve those runs under that description; implement event timestamps and a
   justified missed-release predicate before running the intended experiment anew.

2. **The potential control is not established as policy-invariant.**
   `segments.py:117` uses the realized episode length and retrospective labels,
   including the first frame's label, to construct the potential. It is not shown
   to be a fixed function of the learner state. With terminal potential zero, the
   discounted shaping sum telescopes to **minus the initial potential**, not zero;
   1,287 of 1,300 episodes have nonzero initial potential. That initial value depends
   on the realized trajectory length/label. The standard guarantee assumes a
   state potential; it also does not guarantee identical finite-training performance.
   See [Ng, Harada and Russell (1999)](https://ai.stanford.edu/~ang/papers/shaping-icml99.pdf).
   Consequently, the current `potential` result is not a validation of the harness
   through a proven invariant control. Use a fixed state potential and test its
   boundary conditions to establish that control.

3. **The advantage-sign baseline in the narrative uses the wrong denominator.**
   On the exact validation frames used by `eval_critic.py`, a constant-negative
   predictor scores **6.28%**, and a constant-positive predictor scores **93.72%**.
   Neutral/aftermath frames are excluded from this metric. The reported IQL 30.78%
   and sign-mode 50.14% reproduce, but the description of 31% as the constant-negative
   or chance baseline is wrong. Positive and negative per-class accuracies and their
   balanced average are needed to interpret the ordinal objective.

4. **AUC mishandles ties.** `eval_critic.py:37` assigns consecutive ranks to tied
   scores after concatenating positives first. Four identical scores with two
   positives return **0.0**, where AUC must be 0.5. Use average ranks or a tested AUC
   implementation and add tied-score cases. A separate pairwise calculation with
   half credit for ties agrees with the saved critics' AUCs: terminal 0.87315,
   events 0.89112, sign 0.17759 and decisive 0.78013. Those four values survive this bug.

5. **Validation preprocessing includes held-out observations.**
   `build_dataset.py:170` computes normalization over the entire corpus; `replay.py`
   loads those statistics before splitting episodes. Training batches exclude
   validation episodes, but the full pipeline is not strictly held out. Fit
   normalization on the training split for future runs and store it in checkpoints.
   This is feature-statistic leakage, not evidence of reward-label leakage.

6. **Evaluation provenance is insufficient for episode-level reproduction.**
   All 18 saved runs use evaluation seed 90000; seeds 1 and 2 change training and the
   validation split, not the evaluation seed block. `train.run_eval` removes the
   episode records before saving; none of the final JSONs retain them. The evaluator
   also discards rejection-sampler validity/fallback information. Retain episode
   seeds, initial-state IDs, shift validity and initial-state snapshots or hashes.
   The installed LeRobot `LiberoEnv.reset` chooses stored initial states sequentially
   from index zero, independently of `seed`. New shift draws do not establish held-out
   base initial-state IDs, and changing the seed alone does not ensure fresh standard
   initial states. Claims should distinguish these two kinds of generalization.

7. **Some metric names and conclusions overstate what was measured.**
   `v_monotonicity` only checks final V > initial V, not monotonicity at every step.
   `adv_decisive_margin` pools frames across episodes rather than computing a paired
   difference within each episode. An episode-paired recomputation gives 0.02327 for
   terminal and 0.04380 for decisive, so that particular improvement survives this
   check. Outcome AUC measures outcome separation under recorded behavior, not
   counterfactual action ranking. Single-seed sign/expectile failures at one setting
   do not establish that tuning cannot help or that their failure survives replication.

## Checks completed

- Existing CPU suite: **29 tests passed**.
- Built corpus: **251,229 transitions, 1,300 episodes, 881 successes**. All arrays
  finite; actions bounded; frame indices contiguous; next observations match the
  next frame within each episode; done exactly at episode ends; reward equals success
  on the final transition and zero elsewhere; train/validation episodes disjoint.
- Snapshot replay: `full_shift8__t0`, episodes 0 and 1, 30 steps each: **zero maximum
  absolute observation error** throughout both replays. This is a spot check, not
  proof for every task/state. The existing check's exit code tests step zero only.
- All 18 saved runs have 100,000 completed log steps and consistent evaluation
  success counts/rates. The published success-rate tables match those artifacts.
- Recomputed terminal, events, sign and decisive critic diagnostics from checkpoints.
- Compared every Q and V checkpoint tensor: `awr` and all three `mask` seeds are
  **bit-identical** to their corresponding terminal baseline critics.

| Mode | Seed 0 | Seed 1 | Seed 2 | Mean |
|---|---:|---:|---:|---:|
| events (as implemented) | 94/150 | 86/150 | 92/150 | 60.44% |
| mask | 88/150 | 83/150 | 90/150 | 58.00% |
| terminal | 78/150 | 90/150 | 86/150 | 56.44% |

The observed events–terminal mean difference is **4.00 percentage points**. Three
training seeds on the same configured evaluation block do not establish a reliable
improvement. Nor do they prove equivalence. The older document also retains stale
statements that the seed replication is still running; all six extra runs are complete.

## After the fixes

Re-running the verifier against the regenerated label export and the fixed code
(`outputs/rl_verification/audit.json`):

| quantity | before | after |
|---|---:|---:|
| grasps rewarded | 0 of 1,558 grasp chunks | **1,224** of 1,372 target grasp events (the rest are holds shorter than 8 frames) |
| release penalties | 353, of which 161 in successful episodes | **122**, of which 21 in successful episodes — those 21 are releases that were followed by a re-grasp, so they genuinely missed |
| drop penalties | 255 | **280** (target drops, localised on the drop frame) |
| episodes with nonzero initial potential | 1,287 of 1,300 | **0** |
| max abs discounted shaped return per episode | not zero | **1.06e-6** (float32 accumulation) |
| AUC of an all-tied score | 0.0 | **0.5** |
| rank AUC vs independent pairwise AUC | differ in principle | equal to 15 decimal places on all four checkpoints |
| whitening excludes validation episodes | no | **yes** |

Corrected sign-agreement table on the same validation frames (constant-positive 0.937,
constant-negative 0.063):

| run | `adv_sign_agree` | on `y=+1` | on `y=-1` | balanced |
|---|---:|---:|---:|---:|
| `iql_terminal` | 0.308 | 0.281 | 0.704 | 0.493 |
| `iql_sign` | 0.501 | 0.490 | 0.667 | **0.579** |
| `iql_decisive` | 0.319 | 0.296 | 0.658 | 0.477 |
| `iql_events` | 0.217 | 0.186 | 0.671 | 0.429 |

The ordering the narrative claimed survives on the balanced metric: `sign` is the only
mode that moves ordinal agreement above the baseline, and it is still the mode whose
outcome AUC collapses to 0.178.

## Reproduce

From the repository in the LeRobot Python environment:

```bash
python -m unittest discover -s scripts/rl -p 'test_*.py'
python -m unittest discover -s scripts/annotate/bench -p 'test_oracle_labels.py'
# the per-frame event columns finding 1 needs; regenerates bench/oracle_labels*.parquet in place
python scripts/annotate/bench/oracle_labels.py \
    --datasets full_anchor full_shift4 full_shift8 full_shift12 full_shift16 \
    --out  $FTL_PROJ/bench/oracle_labels_r6_object.parquet \
    --episodes-out $FTL_PROJ/bench/oracle_episodes_r6_object.parquet
python scripts/rl/verify_results.py --out outputs/rl_verification/audit.json
python scripts/rl/check_obs_consistency.py --dataset full_shift8__t0 --episodes 0 1 --steps 30
```

Use `FTL_PROJ` / `FTL_RL` if the artifact roots differ from the repository defaults.
This verification recomputed offline diagnostics and checked saved closed-loop counts;
it did **not** rerun the 2,700 closed-loop evaluation episodes or retrain the policies.
