# Oracle-based segmentation for training (decision 2026-09-08)

Decision: training labels for the simulation corpus come from the simulator oracle, not from a VLM. The VLM
benchmark (`docs/segmentation_benchmark.md`) showed that Qwen3-VL-8B cannot localize grasp/drop events reliably
and, even when handed the correct events, labels chunks worse than deterministic rules (oracle-conditioned
ablation: rules 8/20 dev episodes fully correct, whole-episode VLM 6/20, per-chunk VLM see the benchmark doc).
On OopsieData, labels come from human review of a stratified subset, with gripper telemetry pre-localizing
candidate events. The VLM is kept only for object identity and one-sentence descriptions of a localized moment.

## What the oracle provides today (`scripts/annotate/bench/oracle_reference.py`, reference r6)

Per episode, from `priv.*` columns only:

- per-frame held state of every object slot (both-finger contact, debounced, holds >= 8 frames, gaps <= 4 merged)
- events: grasp / drop / release with frame brackets and chunk, distinguished by the gripper command
- wrong-object contacts, arm collisions, fixture joint motion, stage frames (reached, grasped, lifted,
  transported, placed), final object state relative to the goal
- failure mode (never_reached, wrong_object, missed_grasp, drop_transport, release_miss, hold_no_release,
  stall_after_grasp, collision, other), the OOPSIE cause it implies, the decisive chunk
- per chunk: an allowed label set, a primary label and the rule that produced it

## Training label = primary label, confidence = set size

`bench/oracle_labels.py` exports one row per frame to `bench/oracle_labels.parquet`:

| column | meaning |
|---|---|
| label | the chunk's primary label (progress / failure_inducing / recovery / neutral / aftermath) |
| allowed | the allowed set; the learner may treat any member as acceptable |
| q | 1.0 if the set has one label, 0.5 for two, 0.25 for three or more, 0 for unlocalised chunks |
| decisive_error_chunk, failure_onset_chunk, visible_failure_chunk | landmarks for the t* weighting |
| recoverable_until_chunk | null until the recovery-branching oracle fills it (below) |
| cause, failure_mode, event_type_in_chunk, held, success | for cause-aware losses and analysis |

This is exactly the input the annotation loss in proposal section 5.4 expects: sign constraints on progress /
recovery (A > 0) and failure_inducing (A < 0), the neutral loss on neutral / aftermath, weights q_t times the
decay from the decisive chunk.

### r6 attempt-level credit

- Evaluate each grasp through the end of its hold across chunk boundaries. A hold that ends without ever
  becoming airborne, or drops after fewer than 8 frames, is a failed acquisition. Its ending chunk is
  failure_inducing; preceding overlapping chunks allow only failure_inducing/neutral (primary neutral).
  A final placement in a successful episode is exempt. Sustained airborne transport retains its progress credit.
- Mixed grasp/error chunks and partial failed-closure overlaps allow failure_inducing/neutral, never positive
  progress or recovery credit just because their boundaries are uncertain.
- After an error, empty-gripper approach/contact motion and unexplained movement before a later grasp are neutral.
  Recovery credit starts at an established grasp; brief failed acquisitions cannot earn it. Initial approach and
  sustained carry progress remain available.
- The hold-length cutoff uses the existing HOLD_MIN_FRAMES=8; this is a conservative rule, not a calibrated
  physical definition of successful acquisition. Event timestamps and decisive landmarks are preserved.

The q values encode rule ambiguity, not calibrated probabilities of correctness. Privileged state makes physical
events observable; it does not establish counterfactual action advantage or when failure became inevitable.
Existing r4/r5 references and training exports must be rebuilt before using these corrections; the exporter accepts
only references matching the current version.

### Frozen r6 audit

The [12-episode exploratory audit](oracle_r6_audit.md) found clear label disagreements in 4 episodes,
semantic concerns in 4, and no issue in the inspected evidence for 4. Eight cases came from the held-out failure
split and four were supplemental successes. This assistant visual/telemetry audit is not human ground truth or a
population accuracy estimate. It exposes singleton recovery/progress on failed acquisitions, inconsistent
success-only attempt filtering, and new post-decisive errors hidden by aftermath. Keep r6 frozen and do not treat
the primary labels/q values as validated training supervision. Evidence and raw videos are in
`outputs/oracle_audit_r6/index.html`; no corpus export was changed by the audit.

### Direct assistant annotation trial

The living [GPT-6 experiment record](gpt6_annotation_experiments.md) collects the direct annotation trials,
input comparisons, observed capabilities, limitations, artifact provenance and proposed next experiment.

The separate [GPT-6 direct v1 review](../outputs/gpt6_annotations_v1/index.html) contains assistant-authored
segment judgments for all 12 audit episodes, expanded to 331 chunks, with labelled videos and reasons.
It uses paired camera stills and simulator telemetry, including previously inspected audit evidence; this is
an informed reannotation, not a blind evaluation. An explicit `uncertain` label abstains on mixed chunks and
unresolved placement behavior. All counterfactual advantages remain null and training approval is false.
See the [trial protocol](../outputs/gpt6_annotations_v1/README.md). The renderer only expands authored judgments;
it does not infer labels or modify r6. Independent human evaluation remains outstanding.

### Oopsie-compatible input ablation

The [timestep trial](../outputs/oopsie_transfer_v1/index.html) compares separate visual-only and visual-plus-robot
annotation contexts on four fresh simulated episodes (833 timesteps). Both outputs were frozen before oracle
inspection. They disagree on 33.4% of timestep labels, concentrated in book insertion. Robot telemetry clarifies
commands and motion, but accuracy improvement is unproven. See the [findings](../outputs/oopsie_transfer_v1/findings.md)
for semantic disagreements, concurrent side effects, sample limitations, and the pending independent human review.

The subsequent [observed-versus-oracle comparison](../outputs/oopsie_transfer_v1/oracle_comparison.html) keeps the
observed-input B labels frozen and adds an isolated oracle-informed C pass using raw privileged arrays.
They differ on 235/833 timesteps (28.2%); 135 are neutral/aftermath, and 39 are book-insertion recovery/failure.
See the [comparison findings](../outputs/oopsie_transfer_v1/oracle_comparison_findings.md) for why this is not an
error rate and which distinctions privileged evidence resolves.

## Still to build on the oracle side

1. **Recovery-branching oracle for recoverable_until.** For a failed episode, restore the MuJoCo snapshot at chunk
   boundary c (validated by `check_snapshot_restore.py`, schema v3.2 fixture poses) and roll out the near-perfect
   MolmoAct2-LIBERO checkpoint for the remaining budget; recoverable_until = the last c at which the branch
   succeeds in >= 2 of 3 seeds. Cost: about 14 s per branch. Bisection over chunks needs about 5 branches per
   episode, so 642 failures x 5 x 3 seeds x 14 s is roughly 37 GPU-hours; sample the decisive neighbourhood only
   (c in [D-4, D+4]) to cut it to about 15 hours. Run only when the machine can be left on safely.
2. **Mechanism labels with geometry.** At the decisive frame, record the end-effector offset from the target in
   the gripper frame, the object contacted, the height and goal distance at a drop, and where a released object
   came to rest. Emit a templated sentence ("closed 3 cm left of the alphabet soup"). Needed for the qualitative
   figures and as the check for any VLM-written description.
3. **Human audit of the 50 held-out episodes.** Decisive chunk, cause, mechanism sentence, last plausibly
   recoverable chunk; 3 minutes per episode. This fixes the remaining definitional disagreements in the tail rules
   before the labels are used for training.

## What is deliberately not done

- No VLM in the training-label path. The benchmark and its scoreboards remain as the measured noise model for the
  robustness experiment (proposal H6): degrade oracle labels with the measured per-level error rates instead of
  synthetic flips.
- No per-frame labels finer than the chunk. The actor's action horizon is the chunk.
