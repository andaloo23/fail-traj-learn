# GPT-6 annotation experiments: evidence, capabilities and limitations

Updated 2026-09-08. This is a living record of the direct assistant annotation experiments in this project.
It documents observed behavior on our data, not a general model capability benchmark.

**Current assessment:** GPT-6 can produce useful candidate event and segment annotations from camera evidence
and robot telemetry. Reliable autonomous training supervision has not been demonstrated. Privileged simulator
information resolves some physical ambiguity, but neither it nor higher temporal resolution resolves all
questions about task credit. No production labels were replaced by these experiments.

## What was actually run

These were direct assistant judgments in Codex, supported by local tools for camera sampling, telemetry
inspection, JSON export and review rendering. They were not a production API annotation service, a model
fine-tune, or outputs from the deterministic r6 rules. Export scripts expand authored intervals and compute
comparisons; they do not choose the semantic labels.

Separate annotation contexts were used for the input-ablation conditions, without conversation history or
access by instruction to each other's predictions. Input isolation was procedural, using folder allowlists;
it was not enforced by an operating-system sandbox. There was one run per condition, with no repeated-seed
study. Exact API model snapshot, decoding configuration and per-request token usage were not captured.

| Experiment | Evidence given to annotator | Scope | Result / artifact |
|---|---|---|---|
| Frozen r6 audit | Camera samples and simulator evidence; existing r6 predictions available | 12 purposively selected episodes | 4 clear disagreements, 4 semantic concerns, 4 with no issue found in inspected evidence; [audit report](oracle_r6_audit.md) |
| Direct v1 annotation | Camera stills, robot and privileged simulator evidence; previously seen audit | Same 12 episodes, 331 chunks, 3,286 frames | 93 uncertain chunks; [review](../outputs/gpt6_annotations_v1/index.html), [authored labels](../outputs/gpt6_annotations_v1/authored.json) |
| A: visual-only temporal pass | Task instruction and external/wrist images | 4 fresh episode identities, 833 timesteps | 20 segments, 20 uncertain timesteps; [authored A](../outputs/oopsie_transfer_v1/condition_a.json) |
| B: Oopsie-compatible temporal pass | Same as A, plus measured robot pose/finger positions and gripper commands | Same 4 episodes | 23 segments, 25 uncertain timesteps; [authored B](../outputs/oopsie_transfer_v1/condition_b.json) |
| C: oracle-informed temporal pass | Same as B, plus raw object/contact/grasp/support arrays and goal/outcome evidence | Same 4 episodes; no access to A/B judgments or r6 semantic labels | Independent evidence-rich reference; [authored C](../outputs/oopsie_transfer_v1/condition_c.json) |
| Observable sparse v1 | Task, camera samples, measured robot state and gripper commands only; no outcome or oracle inspection | 4 further fresh episodes, 992 timesteps | 8 retained segments, 292 labelled timesteps (29.4%); [review](../outputs/observable_sparse_v1/index.html) |

The direct v1 pass was explicitly **not blind**: the assistant had seen r6 and the audit. Its label counts were
106 progress, 51 failure-inducing, 31 recovery, 31 neutral, 19 aftermath and 93 uncertain. These are not accuracy
measurements. Its 178 disagreements with r6 primary labels also reflect different label semantics.

The four later episodes were selected by identity before inspecting outcomes. They turned out to contain
three simulator successes and one failure, so they are neither balanced nor representative. They are new
episodes from familiar task families, not a test on unseen tasks or real robots.

| ID | Dataset / episode | Frames | Recorded outcome revealed afterward |
|---|---|---:|---|
| E01 | `full_shift16__t1` / 1, cream cheese | 177 | Success after failed acquisition |
| E02 | `full_goals8__t2` / 1, wine bottle | 83 | Success |
| E03 | `full_l90__t74` / 1, book insertion | 400 | Failure |
| E04 | `full_shift8__t6` / 1, butter | 173 | Success with observed collateral disturbance |

## What “per timestep” means here

Annotators reasoned over attempts and authored temporal intervals, then scripts expanded the intervals to
one label per recorded timestep. They did not independently classify each frame. Initial temporal packs
sampled every five frames at 20 Hz; annotators requested denser images around selected transitions. The
12-episode pass used two sampled observations per chunk plus earlier dense audit evidence.

Consequently, complete timestep coverage is not complete visual inspection or verified one-frame precision.
Boundary uncertainty is recorded explicitly. Original ten-step chunks receive label mixtures: 5 of 85 chunks
are mixed in A and 6 in B. Finer intervals expose mixed chunks but do not automatically improve label accuracy.

## The two comparisons must not be confused

### A versus B: does ordinary robot telemetry change judgments?

Both conditions lacked privileged simulator information. They differed on **278/833 timesteps (33.4%)**;
245 differences came from E03. Among 788 timesteps where neither abstained, 222 differed (28.2%).

This was an input ablation, not an estimate of visual-only error. B is not ground truth. The comparison
demonstrated sensitivity to available evidence and semantic interpretation, but did not establish that B
is more accurate. See the [A/B review](../outputs/oopsie_transfer_v1/index.html) and
[findings](../outputs/oopsie_transfer_v1/findings.md).

### B versus C: what changes with privileged evidence?

B stayed frozen. C was authored separately and frozen before comparison. They differed on
**235/833 timesteps (28.2%)**:

| Difference | Timesteps | Interpretation |
|---|---:|---|
| B neutral / C aftermath | 135 | Stationary ending of failed book placement; largely a contextual-label distinction |
| B recovery / C failure | 39 | Book frames 186–209 and 225–239: oracle-informed pass separates renewed obstructed insertion from corrective resets |
| B progress / C failure | 6 | Cream-cheese frames 46–51: contact onset versus closing-command onset for the failed attempt |
| One condition uncertain | 49 | B abstains on 25 final book frames; C abstains on 24 butter frames with concurrent collateral disturbance |
| Other progress/failure/recovery boundary differences | 6 | Small event-boundary differences |

The six progress/failure differences are **not six proven harmful actions**: initial contact precedes closing,
and assigning it to approach versus the failed attempt is debatable. The more consequential finding is the
39 recovery/failure differences: privileged support/contact and unstable grasp evidence helps distinguish
another failed insertion from a useful-looking adjustment.

C is an oracle-informed **assistant judgment**, not a perfect oracle for semantic credit. Disagreement with C
is not automatically an error. See the [B/C review](../outputs/oopsie_transfer_v1/oracle_comparison.html),
[full findings](../outputs/oopsie_transfer_v1/oracle_comparison_findings.md), and
[numerical comparison](../outputs/oopsie_transfer_v1/comparison_b_vs_c.json).

## Capabilities supported by these observations

- **Recognizing visible attempts and mistakes.** Both nonprivileged passes identified the failed initial
  cream-cheese acquisition and retry, and collateral object tipping during butter pickup.
- **Following controlled object transport.** Both tracked useful pickup/carry sequences. All 83 wine-bottle
  timesteps received progress labels in B and C, although their phase boundaries differed.
- **Using measured state and commands.** Telemetry exposes closing/reopening commands and small robot motions
  that may be difficult to time visually. A command still does not establish object control.
- **Inspecting privileged evidence critically.** C checked raw signals: the short cream-cheese hold was supported
  throughout, and terminal grasp losses at E01 frame 175 and E04 frame 171 were obscured by debounced summaries.
- **Producing reviewable outputs.** Authored reasons, uncertain intervals, temporal boundaries, timestep CSVs,
  chunk mixtures and synchronized review timelines make disagreements inspectable.

These are demonstrated examples, not measured general precision, recall, calibration or cross-task robustness.

## Limitations and failure modes

1. **Attempted correction is conflated with recovery.** Robot movement after a mistake can be another failed
   execution. “Repositioning occurred” is more observable than “the task became easier to complete.”
2. **Mutually exclusive labels lose concurrent events.** Target acquisition and knocking over a neighboring
   object can overlap. Finer timesteps cannot eliminate this conflict.
3. **Neutral versus aftermath is underspecified.** A stationary failed ending can fit either definition,
   inflating disagreement without a difference about useful task motion.
4. **Low abstention is not reliability.** A and B abstained on only 2.4% and 3.0% of timesteps but still differed
   substantially when neither abstained. “High” and “medium” confidence were not calibrated probabilities.
5. **Success conventions are partly hidden.** The simulator can mark goal completion while an object is still
   grasped. Visible release, support, and a task predicate are distinct facts.
6. **Oracle signals need interpretation.** Short grasp flags, debouncing and contacts do not themselves provide
   ground-truth progress, causal responsibility, recoverability or counterfactual advantage.
7. **Evaluation is incomplete.** There are no independent human temporal labels, measured false-progress rate,
   event-boundary accuracy, real-world transfer score, repeated-run stability estimate or downstream training
   benefit. All exported training approvals remain false and counterfactual advantages null.
8. **Progress-only splicing has not been validated.** Removing failed/recovery intervals can create incompatible
   states at joins. These annotations do not promise a successful executable trajectory when concatenated.

## OopsieData transfer: what we know and what we have not tested

The documentation reviewed describes task instructions, camera videos, measured gripper state, joint and/or
end-effector state, executed actions, and robot/control metadata. Human outcome/descriptive annotations are
episode-level rather than our temporal credit labels. Camera calibration and field availability vary by setup.
Sources: [dataset format](https://oopsie-data.com/format/),
[robot profiles](https://oopsie-data.com/robot-profile/), [annotation workflow](https://oopsie-data.com/annotation/).

B uses a **compatible subset** of these inputs. Simulator controller-space arm commands were omitted because
their conversion to physical executed commands was not verified. No actual OopsieData episodes have been
annotated in these experiments. Compatibility of input categories is not demonstrated simulation-to-real transfer.

Even perfect oracle-assisted annotation would not establish observability from real recordings. The useful
target is reliable supervision on the observable subset, with abstention where evidence is insufficient,
rather than forcing reproduction of every privileged distinction.

## Sparse observable-only follow-up

Following the user's instruction to omit ambiguous, neutral and unimportant behavior, a direct sparse pass
used episode index 6 from the four task families above. This is a different sample from A/B/C, not another
paired comparison. The annotator inspected camera samples and ordinary robot telemetry; no oracle arrays,
predicates or recorded outcomes were examined for these episodes.

The pass retains four failed-pickup intervals (42 timesteps) and four controlled-transfer intervals
(250 timesteps). The other 700/992 timesteps have no annotation. Routine approaches, unclear insertion,
small adjustments and uncertain release boundaries are omitted. Intervals carry observable event names and
descriptive progress/failure labels; they retain conservative cores rather than claiming precise full-event
boundaries. High confidence remains an uncalibrated judgment.

The [sparse review](../outputs/observable_sparse_v1/index.html) and
[protocol](../outputs/observable_sparse_v1/README.md) link to authored observations and exports. The selected-only
CSV has 292 rows; the full alignment CSV has 992 rows with empty labels and a false selection mask on omitted
frames. Missing labels must not be interpreted as neutral/zero, negative examples, or verified safe actions.
Coverage is not accuracy. These are still simulated recordings with OopsieData-compatible inputs, not actual
OopsieData episodes. Production labels remain unchanged.

A later user-requested [oracle check](../outputs/observable_sparse_v1/oracle_check/findings.md) froze the sparse
labels before revealing simulator data. It found no physical contradiction in the eight retained segments:
all 250 transfer timesteps had target grasp/contact and were airborne, while all 42 failed-pickup timesteps
lacked a target grasp. This supports the retained event descriptions, not a 100% model accuracy claim or
per-action advantage signs. The 700 omitted timesteps and missed-event recall were not evaluated. No labels
were changed in response to the oracle check.

## Next real-data experiment proposed, not yet run

Try an event-first annotation target on actual OopsieData episodes:

1. Identify observable approach, closing attempt, object motion with gripper, slip, reopening, repositioning,
   release and stall, with evidence and boundary uncertainty.
2. Distinguish **correction attempted** from **recovery demonstrated**.
3. Represent collateral effects separately from target progress so they can overlap.
4. Derive training credit only for supported intervals; leave ambiguous adjustments unlabelled for training.
5. Obtain independent human temporal review using the same available inputs. Measure event detection,
   boundary agreement, incorrect progress on failed attempts, and usable coverage after abstention. Evaluate
   repeated model runs before attributing differences solely to input information.

The [human review page](../outputs/oopsie_transfer_v1/human_review.html) and empty CSV template already exist for
the simulated pilot, but no human judgments have been collected. The sparse follow-up above implements an
initial observable-event selection policy in simulation. The fuller concurrent-event scheme and real-data
trial remain proposals.

## Reproduction, cost and artifact status

Relevant code under `scripts/annotate/bench/`:

- `audit_r6.py`: prepares the frozen r6 audit pack.
- `render_direct_annotations.py`: expands/renders the 12-episode authored labels.
- `oopsie_trial_prepare.py`: prepares the restricted visual/robot input packs.
- `oopsie_trial_export.py`: validates/freezes A/B, exports timesteps and chunk mixtures, renders review.
- `oopsie_trial_oracle_check.py`: reveals oracle diagnostics only after the A/B hash freeze.
- `oopsie_trial_compare_oracle.py`: verifies frozen B/C and builds their comparison.
- `observable_sparse_export.py`: exports only retained observable intervals and preserves empty timestep labels.

These scripts reproduce preparation/export/comparison, **not the direct assistant's authored judgments**.
C's raw privileged input pack was prepared through an interactive Python tool call; its file hashes are saved
in `oracle_inputs_manifest.json`, but it does not yet have a dedicated reproduction command.

Per-episode token counts, API dollar cost and isolated inference latency are unavailable. Tool work, image
inspection, conversation reasoning and export development were not separately metered. Do not estimate
annotation cost by dividing total conversation usage by episode count. Future API runs should capture exact
model/settings, prompts, input manifests, response usage and timings per episode.

Validation checked coverage, frame counts, linked artifacts and frozen hashes. It did not validate semantic
correctness. Detailed checks are in each output directory's validation JSON files. `outputs/` is untracked:
the links require locally generated artifacts. Preserve those artifacts and authored JSON files separately
when sharing or archiving this tracked document.
