# Offline-RL pipeline (proposal stages 4 and 5)

Built 2026-09-09. Code: [`scripts/rl/`](../scripts/rl/). This is the closed-loop learning half of the
project: the recorded corpus becomes offline transitions, a small critic and actor train on them, and the
actor is evaluated back in LIBERO. Stage 4 (episode-level reward only) is the control; stage 5 (oracle
segments) is the method.

## 1. What the learner sees

**Observation.** A 90-dimensional state vector, `obs_v1`, defined once in
[`obs.py`](../scripts/rl/obs.py) and built two ways from the same code:

| block | width | contents |
|---|---|---|
| proprio | 27 | eef pos, eef rotation as 6D, gripper qpos/qvel, joint pos/vel |
| target | 16 | target object pos, rot6d, position relative to the end effector, distance, grasped / contact / support flags |
| goal | 14 | receptacle pos, rot6d, target-to-receptacle vector and distance, valid flag |
| distractors | 20 | the four nearest other objects, sorted by distance to the end effector: relative position, distance, contact |
| contacts | 3 | total contacts, arm contacts, gripper-static contacts (log1p) |
| fixtures | 8 | four one-DoF fixture joints and their valid flags (zero for `libero_object`) |
| time | 2 | t / max_steps and its complement |

Two decisions worth stating plainly:

- **The vector is built from `priv.*`.** The "privileged, never fed to a policy" rule in the README
  governs the *VLM annotator*, whose whole claim is that it diagnoses failures from what a camera can
  see. The learner is a different experiment: this is the standard low-dimensional state setup of
  robomimic and the LIBERO state benchmarks, and it is what the proposal means by "begin with state
  observations, add frozen image embeddings only after the state-based method works". Swapping in frozen
  visual features later means replacing the target/goal/distractor blocks behind the same interface.
- **Rotations are 6D, not quaternions.** `q` and `-q` are the same rotation, which makes a raw quaternion
  a discontinuous network input.

**Action.** The recorded 7-dim OSC action, already in `[-1, 1]`: 3 delta position, 3 delta axis-angle,
1 gripper. The gripper dimension sits exactly at the box corners, which is why the tanh-Gaussian actor
clips before `atanh`.

**Reward.** Strictly episode-level: `1.0` on the terminal transition of a successful episode, `0.0`
everywhere else. Running out of steps counts as termination, not truncation, because the step budget is
part of the task — `--bootstrap-timeout` flips that if it ever needs testing.

### The consistency guarantee

`ObsBuilder.from_columns` (offline, parquet) and `ObsBuilder.from_priv` (online, live simulator) share
one `_assemble`. [`check_obs_consistency.py`](../scripts/rl/check_obs_consistency.py) proves they agree
on real data: it restores a recorded episode from its chunk-boundary MuJoCo snapshot, replays the
recorded actions, and compares the live observation to the recorded one at every step.

```
full_shift8__t0 ep0: 30 steps  max|err|=0.00e+00
full_shift8__t0 ep1: 30 steps  max|err|=0.00e+00
OBS_CONSISTENCY_OK
```

Bit-exact. Closed-loop success is therefore measuring the same MDP the critic was fit on. Without this
check, a silent feature skew would look exactly like a bad algorithm.

## 2. The corpus

`--corpus object`: `libero_object`, 10 tasks, four initial-state perturbation levels plus the anchor.

| family | init | episodes | success |
|---|---|---|---|
| `full_anchor` | standard | 100 | 100% |
| `full_shift4` | 4 cm / 30 deg | 300 | 95% |
| `full_shift8` | 8 cm / 60 deg | 300 | 76% |
| `full_shift12` | 12 cm / 90 deg | 300 | 50% |
| `full_shift16` | 16 cm / 90 deg | 300 | 40% |
| total | | **1300** | 881 success / 419 failure, 251,229 transitions |

All ten tasks share one object set and one receptacle, so an episode differs from its neighbour only in
which object is named and where things started. `libero_goal`, `libero_10` and `libero_90` are held out
for the generalisation experiment.

Closed-loop evaluation ([`eval_env.py`](../scripts/rl/eval_env.py)) rebuilds the environment through the
same `LiberoEnv` and the same shifted-init rejection sampler the recorder used, from a **different seed
block** (`--eval-seed 90000`), so the perturbation applied to each layout is one the corpus never used.

**Two different things are being held out here, and only one of them is controlled by the seed.**
LIBERO ships a fixed list of initial states per task, and `LiberoEnv.reset` walks that list from index
zero *regardless of the seed* — the seed only drives the shift draw. So `--eval-seed` gives fresh
perturbations of the **same base layouts** the corpus recorded (ids 0..29 per task). To evaluate on base
layouts the corpus never saw, set `--init-state-offset 30` (`--eval-init-state-offset` in `train.py`).
Every evaluated episode now records its seed, `init_state_id`, shift draw, whether the rejection sampler
fell back to the unshifted layout, and a hash of the settled simulator state, so which of the two kinds
of generalisation a number describes is readable off the saved JSON rather than assumed.

Observation whitening is fit on the **training episodes only** ([`replay.py`](../scripts/rl/replay.py)),
not on the corpus statistics in `meta.json`, and the statistics actually used are what the checkpoint
stores. The results in `rl_results.md` predate that fix.

## 3. Stage 4: episode-level baselines

`bash scripts/rl/baselines.sh 100000`

| run | actor data | reward | question it answers |
|---|---|---|---|
| `bc_success` | successes only | none | how much is in the successes alone |
| `bc_all` | everything | none | does naive imitation of failures hurt |
| `bc_outcome` | everything, failures x0.1 | none | does episode-level downweighting recover it |
| `iql_terminal` | everything | terminal success | does a critic beat all of them |

The learner is small on purpose: a 3x256 MLP actor is 0.16M parameters, the twin-Q plus value critic
about 0.4M, and 100k updates take five minutes on the 3090. Results in
[`docs/rl_results.md`](rl_results.md).

## 4. Stage 5: segment-specific value and reward

Labels come from the simulator oracle at reference `r6`, never from a VLM — see
[`oracle_segmentation.md`](oracle_segmentation.md) for why. [`labels.py`](../scripts/rl/labels.py) joins
the per-frame export onto the built transitions; [`segments.py`](../scripts/rl/segments.py) turns them
into supervision.

**Caveat that must travel with every number here.** The r6 audit
([`oracle_r6_audit.md`](oracle_r6_audit.md)) found clear label disagreements in 4 of 12 inspected
episodes and explicitly says the primary labels and `q` values are not validated training supervision.
The segment results are therefore a comparison of *mechanisms* under a fixed, imperfect labeller. The
human audit of the 50 held-out episodes is still the blocking item before any claim about label quality.

### The design space

The interesting question is not "what number should a failure segment get" but **where in the algorithm
a temporal diagnosis should act at all**. An offline actor-critic offers five distinct entry points, and
each one encodes a different belief about what the label means. `SegmentHooks` exposes exactly those
five, so every idea below is a few lines against one shared IQL implementation.

```
                 label -> [reward]  -> TD target -> Q
                 label -> [done]    -> bootstrap cut
                 label -> [expectile] -> what V means at this state
                 label -> [critic loss] -> constraint on A = Q - V
                 label -> [actor weight] -> how hard to imitate
```

#### Implemented

**1. `pm1` — fixed segment reward (the straw man).**
`r_t <- r_t + c * y_t`, with `y_t = +1` progress/recovery, `-1` failure-inducing, `0` otherwise.
This is what "use a VLM to generate robot rewards" actually means, and the proposal exists to argue
against it (H3, ablation 15.2). Its weakness is visible in the formula: `c` is a free scale competing
with a terminal reward of 1, and nothing ties it to the actual value of the action. It is here to be
beaten, and it is the run to check first if the ordinal method fails to separate from it.

**2. `sign` — the ordinal advantage constraint (the proposal method, section 5.5).**
The label constrains only the *sign* of the advantage, never its magnitude:

```
L_sign    = E[ 1(y != 0) * w * softplus( -(y * A - m) / tau_A ) ]
L_neutral = E[ 1(y == 0) * w * A^2 ]
L_ann     = L_sign + lambda_0 * L_neutral,     w_t = q_t * rho_t
```

with `rho_t = exp(-|c_t - t*| / kappa)` over chunks, so an action at the decisive error is supervised
hardest and one ten chunks away barely at all. The reward stays episode-level: the VLM (here, the
oracle) is trusted to say *worse than average*, not *worth -0.4*. `seg_sign_acc` in the training log is
the fraction of supervised frames whose advantage already has the demanded sign, which is the direct
read on whether the constraint is doing anything.

**3. `expectile` — segment-conditional optimism.**
IQL's value function answers "how good could this state be under a good action", tuned by one expectile
`tau`. Segments say that question should be asked differently in different places: read productive
segments optimistically (`tau_hi = 0.9`, the good action is nearby in the data) and failure-inducing or
aftermath segments pessimistically (`tau_lo = 0.3`, do not credit this state with a recovery the data
never shows). This changes what `V` *means* per state rather than adding a term, costs one tensor, and
has no new hyperparameter beyond the two expectiles. It is the cheapest idea in the list and, for that
reason, the most interesting if it works.

**4. `decisive` — relocate the failure in time.**
Instead of a zero terminal reward when the clock runs out, put `-1` at the end of the decisive chunk
`t*` and cut bootstrapping there (optionally stop sampling the aftermath entirely,
`--seg-drop-post-decisive`). This tests H4 in the MDP itself rather than in a loss: the credit-assignment
problem disappears if the terminal is simply moved to where the error was. It is the most aggressive use
of the labels and the most sensitive to `t*` being wrong, which makes it the natural probe for the
annotation-noise experiment.

**5. `potential` — progress shaping (the control).**
`r_t <- r_t + gamma*Phi(s_{t+1}) - Phi(s_t)` with `Phi` = the share of the episode's *step budget*
already spent on productive frames, counted exclusively so `Phi(s_0) = 0`, and `Phi = 0` at the terminal
successor. Those boundary conditions make the discounted shaping sum to exactly zero on every recorded
episode, so this mode cannot re-rank episodes against each other and any gain from it is *purely* faster
credit assignment within an episode. That is what makes it the control for every other mode: if `sign`
beats terminal-only IQL by exactly as much as `potential` does, the segments are not telling the critic
anything it could not have discovered.

Be precise about the guarantee, because an earlier version of this document was not. Ng, Harada and
Russell's policy-invariance theorem requires `Phi` to be a function of the *state*. `Phi` here is a
function of the labelled prefix of the trajectory, which the 90-d observation does not contain, so the
theorem does not apply and this mode is not a proof of invariance — it is a return-preserving shaping
control, which is a weaker and checkable claim (`test_rl.py::TestPotentialShaping`). The version that
produced the results in `rl_results.md` had neither property: it divided by the realised episode length
and started from a nonzero `Phi(s_0)`, so it added `-Phi(s_0)` to every episode's return.

**6. `events` — oracle-localised physical events.**
`+1` on the frame a target grasp starts a hold of at least 8 frames, `-1` on the frame the target is
dropped, `-0.5` on a release that left the target away from the goal (any release of the target except
the one that completes a successful episode). These are the moments the oracle localises most reliably
(they come from contact geometry, not from a judgment about productivity), so this is the
highest-precision, lowest-recall use of the annotation, and it is the offline-RL "hand-designed dense
progress reward" baseline (14.3) without the hand.

The reward needs the per-frame event columns `oracle_labels.py` exports (`event_at_frame`,
`event_target`, `event_hold_frames`, `event_missed_release`) and refuses to run without them. The first
implementation keyed the *chunk's* event type against the *frame's* `held` flag and so never paid a
single grasp bonus; see [`rl_verification.md`](rl_verification.md) finding 1.

**7. `awr` — actor-side only, responsibility-graded.**
Critic untouched. `omega_t <- omega_t * f(z_t)`, with `f = 0` on aftermath, `exp(-p * w_t)` on
failure-inducing (hardest at `t*`), `1 + b * w_t` on productive. Isolates a question the other modes
confound: does the *critic* need the segments, or only the actor? If `awr` matches `sign`, the
contribution is a better imitation weighting, not better credit assignment — a much weaker claim, and
worth knowing before writing it up.

**8. `mask` — data use only.**
Drop aftermath, downweight failure-inducing and neutral. This is baseline 14.3, "successes plus
productive prefixes", done at segment resolution instead of episode prefix resolution. It is the
cheapest thing that could possibly work and the honest bar: a method that needs a new loss should beat
throwing the bad frames away.

Modes compose: `--segments sign,mask` runs both.

#### Deliberately deferred

The proposal stages these after the core method works (section 9), and so does this pipeline.

**9. Cause-matched pairwise Q ranking (proposal section 7).** `-log sigma((Q(s+,a+) - Q(s-,a-))/tau_Q)`
over pairs retrieved from comparable states in the same task phase and with the same cause. Needs a
state-similarity index over the corpus and a definition of "comparable" that does not smuggle in the
answer. The corpus is well suited to it — ten tasks x four shift levels means near-duplicate states with
opposite outcomes genuinely exist — but the retrieval is a project of its own.

**10. Cause-specific risk heads (proposal section 8).** `C_eta(s,a)` over reaching / grasp / manipulation
/ sequencing / collision, trained with multi-label BCE against the oracle cause, giving
`A_tilde = A - lambda_C * sum_c alpha_c C_c`. Needs its own network and optimiser inside the hook, and
the cause distribution in this corpus is thin outside `grasp` and `sequencing_semantic`
(reaching 12 episodes, collision 4), so it would be measuring almost nothing on `libero_object` alone.
Worth building once `libero_goal` and `libero_10` are folded in.

**11. A learned segment-value head.** Predict `P(z_t = failure_inducing | s_t)` and use it at *evaluation*
time as a runtime failure detector, not only as training supervision. This is the one idea on the list
that produces something usable outside offline RL, and it is the natural bridge to the OOPSIE validation:
the head transfers even where the actor does not.

**12. Recoverability-weighted advantage.** `recoverable_until` is still null in the export — it needs the
recovery-branching oracle described in `oracle_segmentation.md` (about 15 GPU-hours). Once it exists, the
neutral loss can be sharpened: aftermath is exactly "past `recoverable_until`", which is a physical fact
rather than a labelling convention, and the `L_neutral` term would finally have a defensible definition.

## 5. Running it

```bash
R=/mnt/c/Users/LocalPC/dev/fail-traj-learn/scripts/rl

bash $R/py.sh build_dataset.py --corpus object --tag object_v1        # parquet -> transitions
bash $R/py.sh check_obs_consistency.py --dataset full_shift8__t0      # must print OBS_CONSISTENCY_OK
bash $R/run_tests.sh                                                  # 29 CPU unit tests
bash $R/baselines.sh 100000                                           # the four stage-4 baselines
bash $R/py.sh labels.py --dataset object_v1 --labels oracle_labels_r6_object.parquet
bash $R/py.sh train.py --tag iql_sign --algo iql --segments sign --seg-use-q \
     --labels oracle_labels_r6_object.parquet
bash $R/py.sh eval_env.py --ckpt $FTL_PROJ/rl/runs/iql_sign/final.pt --family full_shift12
```

Artifacts live outside the repository, under `$FTL_PROJ/rl/`: `datasets/<tag>/` for the built
transitions, `runs/<tag>/` for `config.json`, `train_log.csv`, `final.pt` and `eval_final.json`.

| script | purpose |
|---|---|
| `common.py` | paths, corpus families, init protocols, goal-slot resolution, success corrections |
| `obs.py` | the observation spec; the single definition used offline and online |
| `build_dataset.py` | corpus parquets + sidecars -> flat transition arrays |
| `replay.py` | GPU-resident buffer, episode-level train/val split |
| `nets.py` | twin Q, value net, tanh-Gaussian and deterministic actors, observation whitening |
| `agents.py` | BC and IQL, plus the five `SegmentHooks` entry points |
| `labels.py` | oracle segment labels joined onto the built transitions |
| `segments.py` | the eight segment-supervision modes |
| `train.py` | training loop, CSV logging, periodic and final closed-loop evaluation |
| `eval_env.py` | closed-loop LIBERO evaluation of a learned actor |
| `check_obs_consistency.py` | snapshot-replay proof that offline and online observations agree |
| `test_rl.py`, `run_tests.sh` | CPU unit tests |
