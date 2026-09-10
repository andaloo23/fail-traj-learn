# Offline-RL results (2026-09-09)

> **Verification update, 2026-09-09.** [The audit](rl_verification.md) reproduces every saved table
> from the artifacts, and found four implementation defects plus two misstatements. The defects are now
> **fixed in the code** (`oracle_labels.py`, `segments.py`, `eval_critic.py`, `replay.py`, `eval_env.py`);
> the runs in this document were produced *before* those fixes and have **not** been rerun. So:
>
> | claim below | status |
> |---|---|
> | `events` = grasp+ / drop- / missed-release- reward | **wrong description of what ran.** No grasp ever paid out (0 of 1558 grasp chunks) and every release was charged, 161 of them in successful episodes. The runs tested an all-negative event penalty. The reward now pays 1224 grasps and charges 122 missed releases. |
> | `potential` is a policy-invariance control | **overclaimed.** The old potential depended on the realised episode length and had nonzero Phi(s_0) on 1287/1300 episodes, so it shifted every episode's return by a constant. Now it telescopes to zero exactly (see `segments._potential` for what that does and does not prove). |
> | a constant-negative critic scores 31% on `adv_sign_agree` | **wrong.** Constant-negative scores **6.28%**, constant-positive **93.72%**. Corrected in section 2 below. |
> | outcome AUC values | **unaffected.** The rank-based AUC mishandled ties, but the four checkpoint AUCs are identical under the corrected version. |
> | closed-loop success rates | **unaffected by the fixes**, but produced under corpus-wide observation whitening (validation episodes included) and without per-episode provenance. Both are fixed for future runs. |
>
> The BC-versus-IQL comparison in sections 1-2 stands. Everything about the *mechanism* of `events` and
> `potential` in section 3 needs rerunning before it means anything.

Pipeline and design: [`rl_pipeline.md`](rl_pipeline.md). Corpus: `object_v1` — `libero_object`, 10 tasks,
anchor plus shift 4/8/12/16, **1300 episodes / 251,229 transitions**, 881 success / 419 failure.
All runs: 100k updates, batch 1024, 3x256 MLPs (actor 0.16M, critic 0.47M), ~5 minutes each on the 3090.

Closed-loop evaluation: 10 tasks x 5 episodes per family, fresh initial states from seed block 90000,
so nothing here is a replay of a training layout. 50 episodes per family, 150 per run — wide confidence
intervals, roughly +-14 points on a single family cell at 50 episodes. Read the `overall` column and the
ordering, not individual task cells.

**Headline, stated up front so the tables below are not misread.** The measured spread of the *baseline*
across training seeds is 4.1 points of overall success, which is larger than the gap between the
baseline and any segment mode that improves on it. **No segment-supervision mode reliably beats a
terminal-reward critic on this corpus.** What the sweep does establish, well outside that noise, is
which mechanisms are actively harmful and why: every mode that rewrites the critic's objective loses 14
to 30 points, and the proposal's own ordinal-advantage loss is the clearest case, inverting the value
function outright.

## 0. The pipeline is sound before any numbers are read

`check_obs_consistency.py` restores a recorded episode from its chunk-boundary MuJoCo snapshot, replays
the recorded actions, and compares the live observation against the recorded one at every step:

```
full_shift8__t0 ep0: 30 steps  max|err|=0.00e+00  step0=0.00e+00
full_shift8__t0 ep1: 30 steps  max|err|=0.00e+00  step0=0.00e+00
OBS_CONSISTENCY_OK
```

Bit-exact, every feature block. The actor is evaluated on exactly the observation distribution it was
fit on, so a poor closed-loop number is a statement about the algorithm and not about a feature skew.
29 CPU unit tests cover goal-slot resolution, the rotation encoding, offline/online agreement,
permutation invariance of the distractor block, the expectile loss, both agents, and the label semantics.

## 1. Stage 4: episode-level reward only

No segment label is read anywhere in this section. Reward is 1.0 on a successful terminal transition and
0.0 everywhere else.

| run | actor data | shift4 | shift8 | shift12 | **overall** | val action MSE | val V gap |
|---|---|---|---|---|---|---|---|
| `bc_outcome` | all, failures x0.1 | 74% | 58% | 30% | **54.0%** | 0.026 | - |
| `iql_terminal` | all | 70% | **66%** | 20% | **52.0%** | 0.025 | 0.524 |
| `bc_success` | successes only | 72% | 48% | 26% | **48.7%** | 0.056 | - |
| `bc_all` | all | 66% | 36% | 12% | **38.0%** | 0.028 | - |
| *MolmoAct2 teacher* | *(generated the data)* | *95%* | *76%* | *50%* | *74%* | - | - |

Four things worth keeping.

**Naive imitation of failures is actively harmful.** `bc_all` loses 6 to 14 points against `bc_success`
at every shift level and 10.7 points overall. This is the premise of the whole project, measured on this
corpus rather than assumed: 419 failed episodes contain enough bad behaviour to drag a policy down when
cloned uniformly.

**Episode-level downweighting already recovers more than discarding.** `bc_outcome` beats `bc_success`
by 5.3 points overall and by 10 points at shift8. So **the bar for any segment method is `bc_outcome`,
not `bc_success`** — the failed episodes are useful, and a crude scalar per episode already extracts
some of that. Reporting a segment method against success-only BC would overstate it.

**A terminal-reward critic is competitive but uneven.** `iql_terminal` is the best run at shift8 (66%,
within 10 points of the teacher that generated the data) and the second worst at shift12 (20%). With 50
episodes per cell that spread is partly noise, but the overall figure sits level with `bc_outcome`.

**A 0.16M-parameter state MLP recovers 60-75% of the teacher rate.** The teacher is a fine-tuned VLA
reading two camera streams; the learner is a small MLP over object poses trained offline on that VLA
output. `bc_outcome` at 54.0% against 74.0% is a reasonable place to start measuring from.

### Two failure modes the smoke tests caught

Both would have produced plausible-looking but meaningless numbers, and both are recorded here because
they are properties of this reward structure rather than typos.

**IQL silently degenerating into BC.** With a terminal-only reward, gamma = 0.99 and episodes of about
250 steps, the reward is discounted to 0.08 by the initial state and the measured advantage spread is
`adv_std = 0.0058`. The AWR weight `exp(beta * A)` with beta = 3 is then `exp(0.017) = 1.02` for every
transition: the critic is trained, and the actor ignores it completely. Fixed by raising gamma to 0.995
and standardising the advantage by its batch spread before exponentiating (`--no-adv-normalize` restores
the old behaviour for the ablation).

**The ordinal loss inverting the value function.** Normalising `L_sign` over the *supervised* frames
rather than the batch keeps it O(1) however few frames carry a label. At `seg_lambda = 1` and 5% label
coverage this drove `v_loss` from 0.004 to 0.082 and produced `val_v_gap = -0.45` — the critic valued
failed states *above* successful ones. Both terms are now means over the whole batch, which is what
proposal 5.5 writes, so partial coverage weakens the constraint instead of being renormalised away.
`seg_lambda` defaults to 0.1 and still needs a sweep.

## 2. Critic quality of the baseline

`eval_critic.py` on the held-out validation episodes (65 episodes, 12,388 frames the trainer never
sampled), for `iql_terminal`:

| metric | value | reading |
|---|---|---|
| `outcome_auc` | 0.873 | V(s_0) predicts the episode outcome from the initial state alone |
| `outcome_auc_mid` | 0.881 | and slightly better at the midpoint |
| `v_gap` | 0.524 | successful frames are valued 0.52 above failed ones, on a [0,1] reward scale |
| `v_end_above_start` | 1.00 | V is higher at the last frame than the first in every successful episode (endpoints only — it was called `v_monotonicity`, which it never measured) |
| `adv_sign_agree` | **0.308** | the advantage sign matches the oracle segment label 31% of the time |
| `adv_sign_agree_balanced` | **0.493** | the same, averaging the two classes equally |
| `adv_decisive_margin` | +0.023 | the decisive chunk already sits below the rest of its failed episode (within-episode difference, averaged over episodes; the across-episode pooling gives the same 0.023 here) |

The critic is real: it separates outcomes strongly and its value rises along successful trajectories.

`adv_sign_agree = 0.308` is the number the segment stage exists to move. Every mean advantage is
negative (an expectile of 0.7 puts V above the average Q, so most dataset actions score below it), which
means the terminal-reward critic satisfies essentially none of the ordinal constraints of proposal 5.4 —
it has learned *which states* are bad, not *which actions* were.

**Read that number against the right baseline.** The metric is computed only on frames with `y != 0`,
and **93.72%** of those carry `y = +1` (62.8% is the share of *all* frames, the wrong denominator — an
earlier draft used it and called 0.31 "chance"). So on the actual metric a constant-positive predictor
scores **0.937** and a constant-negative one **0.063**, and 0.308 is far below both a trivial predictor
and the 0.5 of a coin flip on this skew. Per class the baseline critic gets 0.281 on `y = +1` and 0.704
on `y = -1`: it is not at chance, it is biased hard negative, which is exactly what an all-negative
advantage distribution produces. The unweighted mean of the two, **0.493**, is the number to watch when
comparing modes; the raw agreement mostly tracks how negative a mode's advantages happen to be.

`adv_decisive_margin = +0.023` says the terminal reward alone already localises something. Any claim
that decisive-error weighting helps has to beat 0.023, not 0.

## 3. Stage 5: oracle segment supervision

Labels: oracle reference `r6`, rebuilt for all 1300 episodes on 2026-09-09 (0 failures), exported to
`bench/oracle_labels_r6_object.parquet` and joined onto the transitions at **100% coverage** — all
251,229 frames, all 419 failures.

Label distribution over frames:

| | progress | recovery | neutral | failure_inducing | aftermath |
|---|---|---|---|---|---|
| successes (133,909) | 89.0% | 1.6% | 7.7% | 1.7% | - |
| failures (117,320) | **30.0%** | 1.2% | 18.9% | 7.2% | 42.7% |

That 30% is hypothesis H1 stated as a measurement: **35,140 frames of productive behaviour sit inside
episodes whose only episode-level label is "failed"**, and `bc_all` shows what happens when they are
imitated together with the 8,440 failure-inducing ones. Ambiguity is concentrated where it should be —
`q = 1` on 86.5% of success frames but only 33.6% of failure frames — and 18.4% of failures have no
localised decisive chunk at all.

> **Caveat that travels with every number in this section.** The r6 audit
> ([`oracle_r6_audit.md`](oracle_r6_audit.md)) found clear label disagreements in 4 of 12 inspected
> episodes and states that the primary labels and `q` values are **not validated training supervision**.
> What follows compares *mechanisms* under a fixed, imperfect labeller. The human audit of the 50
> held-out episodes remains the blocker before any claim about label quality, and the measured VLM error
> rates in [`segmentation_benchmark.md`](segmentation_benchmark.md) are the intended noise model for the
> robustness experiment rather than synthetic label flips.

### Results

One seed, default hyperparameters, `--seg-use-q` throughout. Baselines repeated for reference in italics.

| run | acts on | shift4 | shift8 | shift12 | **overall** | outcome AUC | V gap | adv sign agree |
|---|---|---|---|---|---|---|---|---|
| `iql_events` | reward | **96%** | 54% | **38%** | **62.7%** | **0.891** | 0.563 | 0.217 |
| `iql_awr` | actor weight | 88% | 56% | 34% | **59.3%** | 0.873 | 0.524 | 0.308 |
| `iql_mask` | actor weight | 82% | 58% | 36% | **58.7%** | 0.873 | 0.524 | 0.308 |
| *`bc_outcome`* | *actor weight* | *74%* | *58%* | *30%* | *54.0%* | - | - | - |
| *`iql_terminal`* | *(baseline)* | *70%* | *66%* | *20%* | *52.0%* | *0.873* | *0.524* | *0.308* |
| `iql_potential` | reward (control) | 74% | 52% | 26% | 50.7% | 0.807 | 0.275 | 0.335 |
| `iql_decisive` | reward + done | 70% | 50% | 26% | 48.7% | 0.780 | 0.536 | 0.319 |
| `iql_sign` | critic loss | 70% | 36% | 22% | 42.7% | **0.178** | **-1.831** | **0.501** |
| `iql_pm1` | reward | 48% | 32% | 16% | 32.0% | 0.760 | 1.686 | 0.390 |
| `iql_expectile` | value target | 40% | 26% | 12% | 26.0% | 0.520 | 2.413 | 0.279 |
| *MolmoAct2 teacher* | | *95%* | *76%* | *50%* | *74%* | - | - | - |

Critic columns are from `eval_critic.py` on the 65 held-out validation episodes. `iql_awr` and
`iql_mask` are bit-identical to `iql_terminal` on every critic metric, which is the intended check that
they touch only the actor.

### Seed replication overturns the ranking at the top of that table

`events`, `mask` and `iql_terminal` were rerun at seeds 1 and 2 (`seed_replication.sh`), 450 evaluation
episodes each:

| mode | seed 0 | seed 1 | seed 2 | **mean** | sd |
|---|---|---|---|---|---|
| `iql_events` | 62.7% | 57.3% | 61.3% | **60.4%** | 2.8 |
| `iql_mask` | 58.7% | 55.3% | 60.0% | **58.0%** | 2.4 |
| `iql_terminal` | 52.0% | 60.0% | 57.3% | **56.4%** | 4.1 |

**The 10.7-point gap between `events` and `iql_terminal` at seed 0 is 4.0 points across three seeds, and
it is not significant.** Pooling all 450 episodes per arm gives 272/450 against 254/450, a two-proportion
z of 1.22 (p about 0.22), and that test even flatters the result by treating episodes within a seed as
independent. The baseline's seed-0 draw (52.0%) was simply unlucky: its own spread across seeds is 4.1
points, larger than any of the differences between the top three modes.

So the honest reading of the top of the table is: **no segment mode reliably beats terminal-reward IQL
on this corpus at 100k steps.** `events` and `mask` are ahead on the mean and behind on nothing, which
is worth following up with more seeds and a step-count sweep, but on the present evidence the difference
is not established. The single-seed ordering that generated the first draft of this section — `events`
62.7% "beating" the baseline's 52.0% — is exactly the error that running three seeds is for.

Two things do survive replication, because they are far outside seed noise:

- **The critic-side failures are real.** `sign` (42.7%), `pm1` (32.0%) and `expectile` (26.0%) sit 14 to
  30 points below a baseline whose seed spread is 4.1. No plausible seed draw closes that.
- **The critic diagnostics are structural, not stochastic.** `iql_sign` reaching `outcome_auc` 0.178
  and `iql_expectile` reaching `q_loss` 0.95 are failures of the objective, visible in the training logs
  from the first thousand steps, not tail outcomes of an unlucky initialisation.

Everything below this line that compares the *top three* modes should be read as a hypothesis for a
larger run, not as a result. Everything about the bottom three stands.

### What this says

**Modes that reshape the critic lose; modes that leave the value function alone are at worst neutral.**
This is the one directional claim the seeds support. The bottom three (`sign`, `pm1`, `expectile`,
26.0-42.7%) all rewrite what the critic is optimising and lose 14 to 30 points, far outside the 4.1-point
seed spread of the baseline. The top three (`events`, `awr`, `mask`, means 58.0-60.4% where measured)
either add a sparse physically-grounded reward or only reweight imitation, and land level with or
slightly above a 56.4% baseline. `potential` sits at 50.7% against that 56.4%, within its noise — but
see the correction below: the potential that ran was not the invariant control it was described as, so
this row is not the harness validation it was presented as either.

**The mode that leads on the mean is the one that agrees least with the labels.** `iql_events` has the
healthiest critic of any run (outcome AUC 0.891 against 0.873) and the best mean policy, and its
advantage signs agree with the oracle segment labels **less** than the baseline does (0.217 against
0.308; balanced, 0.429 against 0.493). It never consults the productive/failure-inducing judgment at
all. The lead is not significant across seeds, but the dissociation is not a noise artefact: whatever
`events` is doing, it demonstrably is not satisfying the ordinal advantage constraint.

> **What `events` actually was in these runs.** Not "a grasp that holds, a drop, a release that misses".
> The reward keyed the chunk's event type against a per-frame `held` flag at the chunk's first frame,
> two columns on different clocks, and the conjunction was empty: **0 of 1558 grasp chunks** paid the
> +1. Every release was charged -0.5, including **161 in successful episodes**. So the winning row is a
> critic given a **sparse all-negative penalty at drops and releases** — 608 penalties, no bonuses.
> That is still an interesting result, and arguably a cleaner one (it is closer to a pure "these
> physical events are bad" signal than to a progress reward), but it is not the experiment the section
> claims. The fixed reward pays **1224** target grasps that hold, charges **280** target drops and
> **122** releases that left the object away from the goal, and lands each on the event's own frame.
> Rerunning is what would tell us whether the +1 helps, hurts, or does nothing.

**The ordinal constraint is learnable, and satisfying it destroys the critic.** `iql_sign` moves
held-out advantage-sign agreement from 0.308 to 0.501 (balanced, 0.493 to 0.579, so the gain is real and
not just a shift in how negative the advantages are) — the loss does what it is asked. It also drives
`outcome_auc` to **0.178**, far below the 0.5 of a coin flip: the critic ends up ranking failed episodes
*above* successful ones, and `v_gap` goes to -1.83. The two objectives are in direct conflict, and at
`seg_lambda = 0.1` the constraint wins. This is the central negative result of the sweep and it is a
statement about the objective, not about tuning: `L_sign` can be satisfied by lowering V on productive
states just as easily as by raising Q, and nothing in the loss prefers the second.

**Deleting the bad frames is as good as anything else here.** `iql_mask` — drop aftermath, downweight
failure-inducing to 0.1 and neutral to 0.5 — averages 58.0% over three seeds, indistinguishable from the
responsibility-graded `awr` (59.3%, one seed) and from `events` (60.4%). It is also the *steadiest* run
at the hardest level: 36 / 34 / 36% at shift12 where the baseline swings 20 / 34 / 26%. Any elaborate
segment machinery has to clear the bar set by throwing 20% of the frames away, and none of the
critic-side machinery comes close to it.

**Sparse beats dense, at the same information.** `pm1` and `events` both add a reward from the same
annotation. `pm1` spreads +-1 over every frame and collapses to 32.0%; `events` fired on about 600 of
251,229 frames (as implemented; see the correction above) and reached 62.7%. At `--seg-reward-scale 0.05` over ~250 steps with 62.8% positively
labelled frames, the `pm1` shaping term sums to roughly 7.5 against a terminal reward of 1 — the task
reward is simply drowned, and `v_gap = 1.686` shows the value function inflating to match. This is
proposal H3 with a mechanism attached, though a scale sweep would make the point properly.

**`decisive` is the one critic-side mode that is not harmful, and it sharpens t\*.** 48.7% overall
(against 52.0%) but the best shift12 result of any critic-side mode, and it doubles
`adv_decisive_margin` from 0.023 to 0.044 — the critic really does single out the decisive chunk more
sharply when the terminal is moved there. `outcome_auc` falls 0.873 to 0.780, which is the cost.

### Caveats on these numbers specifically

- **Seeds.** `events`, `mask` and `terminal` have three seeds each (see above) and their differences are
  not significant. Every other row is a **single seed** and should be assumed to carry the same 4-point
  spread — which matters for `awr` (59.3%), whose apparent edge over the baseline is entirely within it,
  and for `decisive` and `potential`, which are within it in the other direction.
- **One hyperparameter setting per mode.** `seg_lambda`, `seg_reward_scale`, the two expectiles and
  `beta` are all unswept. The `sign` and `expectile` failures are diagnosed above as structural rather
  than as tuning accidents, but that diagnosis would be firmer with a lambda sweep showing the collapse
  is monotone.
- **The labels are not validated** (see the caveat above this section). A mode that ignores the
  judgment-like labels and uses only the geometric events is exactly the mode least exposed to that
  problem, which may be part of why `events` wins.

### How to read the comparison

Three controls decide what a positive result means, and all three are in the sweep:

- **`potential`** is potential-based shaping, intended as the control that cannot change the optimal
  policy. If a mode beats `iql_terminal` by no more than `potential` does, the segments bought faster
  credit assignment, not new information. **The version that ran did not have that property**: its
  potential divided by the realised episode length and started nonzero, so the discounted shaping summed
  to `-Phi(s_0)` — a per-episode constant, correlated with the episode's own labels, added to every
  return. The fixed version telescopes to zero exactly on all 1300 episodes (`max_abs_shaped_episode_return`
  = 1e-6 in the audit JSON). Even so, Ng-Harada-Russell invariance needs Phi to be a function of the
  learner's *state*, and a potential built from retrospective labels of the trajectory prefix is not one;
  what this control now guarantees is return preservation on the offline data, not policy invariance.
- **`awr`** touches only the actor weights. If it matches `sign`, the contribution is better imitation
  weighting rather than better credit assignment — a much weaker claim than the proposal makes. It does
  not merely match it; it beats it by 17 points.
- **`mask`** just throws the bad frames away. A new loss that does not beat deleting the data has not
  earned its place.

`pm1` is the straw man of proposal 14.4 and 15.2: a fixed +-1 dense reward whose scale is a free
parameter competing with a terminal reward of 1. `sign` beats it, as H3 predicts, but both lose to the
baseline.

## 4. What this implies for the proposal

Across three seeds no segment mode beats a terminal-reward critic, and three of them lose badly. That is
a negative result for the framing of `proposal_overview.md` as it currently stands, and the specific
*way* each mode fails points at what to change.

**The ordinal advantage constraint (section 5.5) has a structural problem, not a tuning problem.**
`L_sign` asks for `sign(Q(s,a) - V(s))` to match a label. Nothing in it prefers raising `Q` on good
actions over lowering `V` on the states those actions occur in, and lowering `V` is much cheaper for the
optimiser because `V` has one input instead of two. The observed outcome — sign agreement up to 0.501,
`outcome_auc` down to 0.178 — is exactly that failure mode. Any fix has to break the symmetry: anchor
`V` with a separate term, apply the constraint to `Q` at fixed `V`, or express the constraint as a
*relative* ranking between two actions at the same state, which is what section 7 already proposes and
which does not admit the degenerate solution. That makes cause-matched pair ranking look less like an
optional extension and more like the repair for the central loss.

**The part of the annotation that is not a judgment is the part that does no harm.** `events` uses only
the oracle's physical events — as run, a penalty at drops and releases; as now implemented, that plus a
bonus at target grasps that hold — leads on the mean, and agrees with the segment labels *less* than the
baseline does. The productive / failure-inducing /
recovery taxonomy is the part the r6 audit flags as contested and the part a VLM was measured to get
wrong; the event timestamps are the part derived from contact geometry. The lead is not significant, so
this is a direction to test rather than a finding — but it is the direction with the fewest ways to be
wrong, and it is cheap to test properly with more seeds.

**Nothing is currently earning its keep in the critic.** `awr` and `mask` gain their (insignificant)
points with a provably untouched critic; every mode that changes the critic is neutral or much worse.
The proposal's novelty claim is specifically that the annotation supervises the *critic*, which then
determines the actor weights. Section 21's minimum publishable result — "ordinal advantage supervision
improves critic ranking over terminal-reward offline RL" — is **false on this corpus as implemented**:
`iql_sign` makes critic ranking dramatically worse (`outcome_auc` 0.873 to 0.178). `eval_critic.py` is
the instrument that would show a repaired version becoming true, and it should be the primary metric for
the next iteration rather than closed-loop success, which needs many seeds to move a claim.

**The corpus may also be too easy to separate the methods.** The behaviour policy is a near-expert VLA
(74% overall), 68% of episodes are successes, and success-only BC already reaches 48.7%. That leaves a
narrow band in which better use of the 419 failures can show up, and a 4-point seed spread eats most of
it. Hypothesis H1 is about the regime where "successful demonstrations are limited"; the informative
experiment is probably to subsample the successes hard (say 10-20% of them) and re-run, which widens the
gap the failures have to fill. That is a one-line change to `build_dataset.py` and it is the next thing
worth running.

**One caveat that cuts the other way.** All of this is measured with a *perfect-recall* oracle at 100%
coverage. The proposal's setting is a noisy annotator, and the modes are not equally exposed to noise:
`mask` and `awr` act on the label directly, so they degrade with it, whereas `events` depends on event
timestamps that a VLM localises poorly (`segmentation_benchmark.md`). The noise-robustness experiment
is therefore not an afterthought but the experiment that decides which of these orderings survives
contact with a real annotator.

## 5. What is not yet done

0. **Rerun `events` and `potential` against the fixed implementations** (three seeds each, ~5 min of
   training plus ~10 min of closed-loop evaluation per run). Until that happens, the `events` row is a
   result about a sparse all-negative event penalty and the `potential` row is not a control. Every
   other mode is unaffected by the fixes — none of them reads the event or potential arrays — but all of
   them were trained under corpus-wide observation whitening, so a full re-baseline is the cleaner
   option if the compute is there.
1. **Hyperparameter sweeps.** `seg_lambda` in particular (see the inversion above), plus `seg_kappa`,
   the two expectiles, and `beta`. Every number here is a single seed at one configuration.
2. **Seeds.** `events`, `mask` and `terminal` have three seeds each (complete, table above); everything
   else in the table is a single seed.
3. **`recoverable_until`** is still null — it needs the recovery-branching oracle (~15 GPU-hours,
   [`oracle_segmentation.md`](oracle_segmentation.md)). Until it exists, `aftermath` is a labelling
   convention rather than a physical fact, which is exactly the term `L_neutral` acts on.
4. **Cause-matched pair ranking and cause-specific risk heads** (proposal 7 and 8), deliberately staged
   after the core method. The cause distribution on `libero_object` alone is too thin for the risk heads
   (reaching 12 episodes, collision 4); they need `libero_goal` and `libero_10` folded in.
5. **Held-out suites.** `libero_goal`, `libero_10` and `libero_90` are recorded, labelled at r6, and
   untouched by these runs — the generalisation experiment.
6. **Frozen visual features** in place of the low-dimensional state, behind the same `ObsBuilder`
   interface. The proposal stages this after the state-based method works.
