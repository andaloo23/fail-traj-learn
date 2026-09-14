# Failure-conditioned temporal learning from robot rollouts

Status: current research direction, updated 2026-09-13. The chunk loader, causal transformer, category-query pooling, role/event heads and training CLI are implemented and smoke-tested; see [training instructions](failure_training.md). An audited real-data manifest, prospective scorer, text alignment, RL cost integration and policy-improvement results remain outstanding. The older ordinal-advantage proposal is a historical baseline.

## Research question

Can failure type and temporal localization improve a learned training signal beyond episode-outcome attention, and can that signal transfer across collecting policies, setups, and eventually embodiments?

Do not claim novelty for attention in RL, failure timestamps, or heterogeneous failure data individually. The contribution must be demonstrated through better policy outcomes and controlled transfer tests.

## Agreed contribution and end-to-end method

The proposed contribution is empirical: temporally localized failure semantics learned from heterogeneous robot rollouts provide a transferable training signal that improves a new policy. This is a potential contribution, not an established novelty claim. Demonstrate semantics, timing, and transfer separately, and compare the exact method against related work.

The primary path is:

1. Annotate progress, failure (with type), recovery, and neutral/aftermath segments in successful and failed trajectories. Preserve observed failure time separately from suspected contributing behavior.
2. Train a causal trajectory transformer on segment roles, known failure types, and temporal localization. Category embeddings condition failure-specific attention; language alignment is an optional extension. Annotations are targets, not answer-revealing inputs.
3. Reuse the representation in a prospective action-conditioned scorer: given history before execution and a proposed action chunk, predict a specified failure within a fixed future horizon. Derive targets from event timestamps and mask incomplete or unknown follow-up. No post-action observations or actual future failure description enter this scorer.
4. Freeze the scorer and evaluate its output as an auxiliary cost in RL. Task reward minus a weighted failure cost trains the critic; the actor learns from that critic. Actor weighting and candidate ranking are comparison interfaces, not replacements for the primary RL question.
5. Evaluate full-episode policy success and failure reduction, including transfer to explicitly held-out sources. Predictive accuracy alone is insufficient.

The earlier PPGuide-style attention-distillation path below is now an experimental alternative. The primary scorer is supervised by observed future events, rather than treating attention as causal blame. Prefix event recognition and prospective event prediction have different targets: the former asks what happened in a prefix, the latter asks what happens after the decision point.

Prospective risk is conditional on the recorded continuation distribution and available action coverage, not an identified counterfactual or a policy-independent physical cost. Repeated predictions can count the same anticipated event more than once. Horizon, cost accumulation, duration scaling, and penalty budget must be specified and compared with a sparse event-cost baseline before claiming useful RL shaping. The exact risk-to-cost mapping remains an implementation decision to validate.

Required evidence:

| Comparison | Claim tested |
|---|---|
| Episode outcome vs. episode-level failure classification | Added value of semantics |
| Episode-level vs. localized failure classification | Added value of timing |
| Generic localized failure vs. localized failure types | Semantics beyond localization alone |
| Same learned signal evaluated on held-out policy/setup/embodiment | Transfer of useful knowledge |

Match training data, capacity, tuning effort, and annotation budgets where feasible; report extra annotation cost explicitly. Strong transfer evidence freezes the source-trained scorer and improves a new policy with little or no target-specific failure annotation. Distinguish scorer adaptation from target-policy training, and disclose any target successes, failures, or demonstrations used.

## Starting points

- [PPGuide](https://arxiv.org/html/2603.10980v1): observation-action chunks as instances; outcome-supervised attention; a second classifier trained on inferred chunk relevance; inference-time diffusion guidance. We borrow the trajectory-to-chunk learning structure. We do not treat inferred relevance as established causal responsibility.
- [From Text to Trajectory / TTCT](https://arxiv.org/html/2412.08920v3): text-conditioned trajectory representations and attention-assisted cost assignment for safe RL. We borrow semantic conditioning and the separation between cost prediction and policy learning. A failure description is a retrospective observation, whereas a textual constraint is available beforehand; that difference must be handled explicitly.
- [SECRET](https://www.ijcai.org/proceedings/2020/0368.pdf): reward-prediction attention used for temporal credit assignment and reward shaping. Include it in related work and distinguish reward shaping from an advantage-sign constraint.
- [Adapt2Reward](https://arxiv.org/abs/2407.14872): failure-mode prompts in a language-conditioned reward model for planning and RL. Compare against this before claiming semantic failure conditioning is new.
- [DenseReward](https://arxiv.org/abs/2607.13033), July 2026 preprint: synthesized failures and recovery behavior support dense reward learning and downstream planning/RL. Compare its supervision and transfer setting against ours.
- [FailureSpot](https://arxiv.org/abs/2609.04277) and [LabRobFail](https://arxiv.org/abs/2607.23704), 2026 preprints: timestamp-level detection and semantic failure localization have precedents. Distinguish policy improvement from detection/diagnosis performance.

## What the first version learns

Learn which contextual action chunks are predictive of a specified failure, then test whether their scores are useful for policy learning. Attention is a predictive relevance mechanism, not a claim that one incremental action uniquely caused failure.

A weak grasp followed by transport may be jointly relevant. Keep contextual sequence representations and allow multiple relevant windows. Do not require attention to peak at a single timestep.

Use known failure category IDs with learned embeddings first. This implements semantic conditioning without needing a language model. Frozen text embeddings and free-text descriptions are a later ablation, not equivalent to the first version.

## Data and annotation contract

Use one sample per recorded decision chunk, initially the existing 10-frame chunks. Each token contains the pre-chunk observable representation, the complete commanded action sequence, the task representation, and elapsed duration. Preserve action order; do not average away gripper closure or motion changes. Use causal history to represent effects of preceding chunks.

Export event records separately from the per-frame arrays:
- episode key and source dataset;
- event type, observed onset/end in both frames and seconds, and annotation provenance;
- confidence/ambiguity weight, without calling agreement a calibrated probability;
- optional suspected contributing interval, explicitly separate from observed failure onset;
- per-class label-known masks;
- robot/controller, policy/checkpoint, setup, task, and chunk duration metadata where available.

Existing labels.py supplies segment roles, cause IDs, onset, decisive chunk, and physical events. Audit their meanings before conversion. In particular, a broad cause such as grasp is not synonymous with an observed drop; a decisive-error chunk is not a visible-event timestamp. Do not invent missing event labels or silently merge these clocks.

Unobserved or unannotated failure classes are unknown, not negatives. Successful episodes can contain drops followed by recovery. A neutral chunk can precede a failure and therefore is not automatically a negative future-event example.

First use the audited subset with sufficient positives and verified negatives per selected class. Expand classes only after counting coverage by source. Oracle labels are training supervision only; privileged features are excluded from the main observable model. A privileged-state experiment is a diagnostic upper bound.

## Teacher: causal history plus failure-specific attention

This is the retrospective/segment-understanding component. Add a masked segment-role classification head to the event and localization objectives below. It may initialize the primary prospective scorer or support the optional distillation experiment.

1. Encode observation-action chunks with a small causal transformer.
2. For each failure category f, use its learned query to pool contextual chunk representations.
3. Predict whether f occurred in the training window using masked binary cross-entropy. Query every class on positive and verified-negative samples, so supplying the category never supplies the answer.
4. Add an event-localization head with a separate supervised loss for audited onset/interval labels. This head predicts where the event manifests; it does not force attribution attention to that location.
5. Use full windows and prefixes, with grouped episode splits. Prefix examples have labels for events within that prefix, not the eventual episode outcome copied onto every prefix.

Initial implementation: one query per category over a shared encoder. This is failure-specific attention, not an assertion that ordinary transformer heads spontaneously specialize. Multiple pooling heads per category are a later capacity ablation.

Teacher objective: L_event + lambda_time * L_localization + lambda_role * L_role. Unknown targets and uncertain timing are masked/weighted. Attention receives gradients from prediction, never from a loss demanding agreement with a negative advantage.

Teacher inputs end at the window endpoint. A retrospective analysis window may include the visible failure. A prospective detector must instead be evaluated with inputs strictly before onset; report those as separate tasks.

## Optional PPGuide-style student: local relevance distillation

Following the two-stage idea in PPGuide, freeze the teacher and generate soft chunk relevance targets. For a verified positive event f in a window, a provisional target is its attention weight times annotation confidence. Normalize attention scores relative to window length before comparing variable-length examples, and calibrate the bounded mapping on training/validation data only. State clearly that this mapping is a heuristic.

Train a causal student from recent observable history, task, and proposed action chunk to predict the soft targets for each class. Supply class queries for all classes at inference; never supply the actual future failure label. Low attention is a weak pseudo-negative for relevance, not proof that an action is safe.

Use grouped cross-fitting when generating student targets for the policy-training corpus: each teacher fold labels episodes it did not train on. Fit preprocessing on its training fold. Keep the final test sources entirely outside teacher, student, and policy model selection.

Call the output a relevance score, not a calibrated failure probability or Q-value. Train a separate future-event predictor on actual event labels if calibrated risk is needed. Attention distillation alone does not provide it.

This student is an experimental bridge to policy learning, not proof that retrospective relevance can always be inferred locally. Report distillation quality and compare against a directly supervised local event model.

## Integration with the existing learner

Keep terminal-reward IQL as the reference critic. Do not initially force A = -attention or jointly minimize an attention-weighted advantage-sign loss: attention and value can satisfy that constraint without learning useful attribution.

Simple integration baseline: export frozen scorer outputs on recorded chunks, align them to transition rows, and use SegmentHooks.actor_weight to multiply existing positive imitation weights by exp(-lambda * score). This is a deliberately small data-use experiment; it cannot demonstrate the ability to generate missing corrective actions. Use the same scorer and score aggregation across all ablations of the control interface.

Primary RL integration, after the scorer passes held-out diagnostics: use frozen scores as an explicit failure cost through SegmentHooks.reward, with r_new = r_task - lambda * cost. This changes the objective. It is not return-preserving shaping and scores are not advantages. Fix duration scaling so chunk/frame resampling does not multiply the penalty. Keep original done/timeout semantics and do not terminate at a suspected error.

For class aggregation use a documented bounded mean over supported classes in the first experiment. Class-specific severity weights and max aggregation are later ablations. Compare matched total penalty/actor downweighting controls so benefit is not explained solely by regularization strength.

The current actor and replay are frame-based. A frozen chunk score may be broadcast for actor weighting, but that is heuristic. For chunk costs, explicitly allocate an integrated cost across its frames; do not apply the full chunk cost at every frame. A genuine chunk-action critic requires a separate change with multi-step targets and consistent online chunk execution.

Candidate reranking or diffusion/flow guidance is a later control experiment. PPGuide's diffusion guidance is not a drop-in update for this repository's small IQL actor or its collecting VLA.

## Minimal controlled experiment

Use identical observable features, source splits, policy capacity, score-to-cost mapping, and tuning budgets. Run the annotation comparisons through the same downstream interface; compare actor weighting against cost-based RL separately.

A. Terminal IQL and outcome-weighted BC.
B. PPGuide-inspired binary episode-outcome attention, with the same student and downstream integration.
C. Generic failure-event attention with timing supervision, but collapsed failure types.
D. Failure-type attention with episode-level supervision only.
E. Failure-type attention plus timing supervision: the proposed full model.
F. Direct local event prediction without attention, with matched annotation information.

C/D/E separate timing from semantics. Add label-shuffle, timing-shuffle, and uniform-attention controls after a promising first result. Do not describe B as an exact PPGuide reproduction; it uses a shared downstream integration to isolate annotation benefits.

Use at least three training seeds for the selected settings. Select score mapping and lambda on validation only. Evaluate full episodes from normal reset and report task success, per-class event incidence, and uncertainty. Use equal evaluation budgets and log base initial-state IDs and perturbations.

Offline diagnostics: per-class precision-recall metrics, timing error with a stated tolerance in seconds, calibration only for event-probability heads, and score variation across phases/sources. Classification accuracy alone is not policy improvement.

A small restored-snapshot repair study is an attribution diagnostic: replace top-scored windows versus random and recency-matched windows with equal candidate budgets, then resume the same policy. No successful sampled repair is not proof of irrecoverability.

## Transfer claims

Stage 1: held-out episodes and initial layouts in LIBERO.
Stage 2: held-out setups and collecting policies/checkpoints, with explicit source-group splits.
Stage 3: held-out embodiments using an action representation with units, reference frames, controller modes, and duration accounted for.

Current LIBERO runs cannot establish cross-embodiment transfer. OopsieData requires additional temporal annotations: its documented public schema is episode-level. A transferable visual failure detector alone does not demonstrate transferable action-conditioned cost or policy improvement.

For diverse action spaces, first distinguish visual-only failure understanding from action-conditioned scoring. Add embodiment adapters and compare against the visual-only model before attributing gains to action understanding.

## Implementation milestones

1. Export and audit an event/window manifest; report class and source coverage; lock grouped splits.
2. Add a chunk sequence loader and small failure-attention teacher; train outcome-only and semantic variants.
3. Train the prospective action-conditioned event scorer; compare supervised segment pretraining against training the scorer directly. Cross-fit soft relevance targets only for the optional distillation path.
4. Specify and test the frozen-score cost integration and matched controls; use actor weighting as a simpler baseline. Run closed-loop evaluation.
5. Test source-held-out transfer and, optionally, repair-window diagnostics before broader embodiment claims.

Implemented modules: `scripts/rl/failure_data.py`, `failure_nets.py`, `train_failure_model.py`, and `test_failure_model.py`. They reuse built observable transitions and require an explicit audited manifest. Category targets currently describe each window prefix; event targets describe onset presence within each chunk. The `last` pooling ablation retains transformer self-attention. Prospective scorer training, score export, text alignment and control integration are future work. See [data verification](failure_data_verification.md) for the existing labels' conversion requirements.

Required checks: no episode-boundary crossing, causal masks, padded/unknown-label masking, correct frame/chunk/second conversion, source split disjointness, no future labels in student inputs, frozen teacher/student during policy updates, and exact reduction to the baseline when lambda=0. A small synthetic task with two interacting windows can check learnability, but is not evidence of physical causality.

## Decision rule

Proceed to larger transfer experiments only if localized semantic supervision improves closed-loop performance or improves repair-window selection beyond binary attention and matched controls. If only event recognition improves, report that result and reconsider the control interface rather than calling attention weights responsible actions.
