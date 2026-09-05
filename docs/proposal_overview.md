# Cause-Aware Ordinal Advantage Learning from Failed Robot Trajectories

## Abstract

Real-world robot datasets increasingly contain failed and suboptimal policy rollouts, but these trajectories are usually labeled only with an episode-level outcome. Treating an entire failed trajectory as undesirable discards productive behavior before the mistake, while behavior-cloning the complete trajectory risks imitating the actions that caused the failure.

This project proposes a lightweight offline reinforcement-learning framework that uses a vision-language model to decompose failed robot trajectories into productive, failure-inducing, recovery, neutral, and post-failure segments. The VLM also identifies the likely decisive error and its cause.

Rather than asking the VLM to generate arbitrary numerical rewards, its annotations are treated as ordinal constraints on action advantage:

- Productive and recovery actions should have positive advantage.
- Failure-causing actions should have negative advantage.
- Neutral and post-failure actions should have near-zero advantage.

These constraints augment a standard offline-RL critic objective. The learned advantages are then used to train a small policy through advantage-weighted behavior cloning. Failure-cause labels additionally supervise lightweight risk models for errors such as failed reaching, unstable grasps, manipulation failures, sequencing errors, and collisions.

The method would be evaluated using closed-loop policy training in simulation and real-world annotation/value validation on OopsieData. All trainable components would be small networks operating over robot state or frozen visual features, making the project feasible on one RTX 3090 without fine-tuning a VLA.

# 1. Motivation

OopsieData collects real robot-manipulation rollouts containing successes, failures, and suboptimal behavior. Its intended uses explicitly include offline RL, reward modeling, failure prediction, and policy steering. genui{"citation":{"refs":["turn0view0","turn0view3"]}}

Each episode can contain:

- A natural-language instruction.
- Videos from one or more cameras.
- Joint, Cartesian, and gripper states.
- Absolute robot actions.
- Robot and policy metadata.
- One or more human annotations. genui{"citation":{"ref":"turn1view0"}}

The current annotation schema distinguishes:

- Clean success.
- Suboptimal success.
- Success with an unwanted side effect.
- Failure.

Failures and side effects can also be categorized as reaching, grasp, manipulation, sequencing/semantic, collision, hardware, or other, with low, medium, or catastrophic severity. These are episode-level annotations, not per-timestep labels. genui{"citation":{"refs":["turn1view0","turn1view1"]}}

That creates a credit-assignment problem.

Consider a failed pick-and-place trajectory:

1. The robot approaches the object correctly.
2. It makes contact correctly.
3. It forms an unstable grasp.
4. It lifts the object.
5. The object starts slipping.
6. The robot continues moving instead of stopping.
7. The object falls.
8. The robot moves aimlessly after recovery is impossible.

This episode contains:

- Productive behavior worth imitating.
- A decisive grasp error.
- A later failure-response error.
- Post-failure behavior that should not train the actor.

A terminal failure reward does not identify these differences. Naively behavior-cloning the trajectory reinforces all of them.

# 2. Main research question

> Can temporally localized and cause-aware VLM diagnoses of robot failures improve offline RL beyond episode-level success/failure labels?

Subquestions include:

1. Can a VLM accurately separate productive, failure-inducing, recovery, neutral, and aftermath segments?
2. Can it distinguish the decisive error from the later visible failure?
3. Does temporal annotation improve offline RL more than marking the entire episode as failed?
4. Does diagnosing why an action was bad provide useful supervision beyond classifying it as generically bad?
5. Do ordinal advantage constraints outperform manually assigned VLM rewards such as \(+1\) and \(-1\)?
6. How robust is the method to imperfect VLM annotations?

# 3. Hypotheses

### H1: Failed trajectories contain productive supervision

Productive prefixes and successful recoveries from failed trajectories will improve learning, particularly when successful demonstrations are limited.

### H2: Temporal localization improves credit assignment

Penalizing failure-inducing segments will outperform treating every action in a failed trajectory as equally undesirable.

### H3: Ordinal constraints outperform arbitrary rewards

Using annotations to supervise whether advantage should be positive or negative will be less sensitive to reward scaling than directly mapping labels to fixed numerical rewards.

### H4: Decisive-error localization matters

Supervising the critic near the action that caused the failure will work better than supervising only the later moment when failure becomes visible.

### H5: Cause information improves robustness

Cause-matched comparisons and cause-specific risk prediction will reduce corresponding failure modes better than generic failure supervision.

# 4. VLM trajectory annotation

Given a trajectory

\[
\tau=(o_0,a_0,o_1,a_1,\ldots,o_T),
\]

the VLM receives:

- The task instruction.
- Sampled video frames or clips.
- Available robot states.
- Available actions or textual action summaries.
- The episode-level outcome.

It returns structured JSON.

## Temporal labels

For each timestep or action chunk:

\[
z_t\in
\{
\text{progress},
\text{failure-inducing},
\text{recovery},
\text{neutral},
\text{aftermath}
\}.
\]

Definitions:

- **Progress:** Advances task completion.
- **Failure-inducing:** Introduces or worsens an error.
- **Recovery:** Attempts to restore feasibility or progress.
- **Neutral:** Has little meaningful effect.
- **Aftermath:** Occurs after recovery is effectively impossible.

## Temporal landmarks

The VLM separately estimates:

\[
t_{\text{onset}}
=
\text{first observable sign of degradation},
\]

\[
t^*
=
\text{likely decisive error},
\]

\[
t_{\text{visible}}
=
\text{time when failure becomes obvious}.
\]

These may be different. An unstable grasp could occur well before the object visibly slips or falls.

## Failure cause

The cause labels initially align with OopsieData:

\[
c_t\in
\{
\text{reaching},
\text{grasp},
\text{manipulation},
\text{sequencing},
\text{collision},
\text{hardware},
\text{other},
\text{unclear}
\}.
\]

The `unclear` option prevents the VLM from being forced to invent a cause.

## Example output

```json
{
  "task": "place the ball in the bowl",
  "outcome": "failure",
  "failure_symptom": "ball rolled off the table",
  "root_cause": "gripper approached off-center and pushed the ball",
  "cause": "grasp",
  "failure_onset": 28,
  "decisive_error": 25,
  "visible_failure": 34,
  "recoverable_until": 29,
  "segments": [
    {
      "start": 0,
      "end": 24,
      "label": "progress",
      "confidence": 0.94
    },
    {
      "start": 25,
      "end": 33,
      "label": "failure_inducing",
      "cause": "grasp",
      "confidence": 0.89
    },
    {
      "start": 34,
      "end": 50,
      "label": "aftermath",
      "confidence": 0.97
    }
  ]
}
```

# 5. Core offline-RL algorithm

The method uses a standard offline-RL critic objective augmented with VLM-derived advantage constraints.

## 5.1 Sparse task reward

The underlying task reward remains simple:

\[
r_t^{\text{task}}
=
\begin{cases}
1, & \text{successful terminal transition},\\
0, & \text{otherwise}.
\end{cases}
\]

Therefore, the VLM is not trusted to produce exact numerical rewards.

## 5.2 Q-function, value function, and advantage

Learn:

\[
Q_\theta(s,a)
\]

and

\[
V_\psi(s).
\]

The estimated advantage of a dataset action is:

\[
\hat A_t
=
Q_\theta(s_t,a_t)-V_\psi(s_t).
\]

A positive advantage means the action was better than the expected action from that state. A negative advantage means it was worse.

## 5.3 Standard critic learning

The TD target is:

\[
y_t
=
r_t^{\text{task}}
+
\gamma(1-d_t)V_{\bar\psi}(s_{t+1}),
\]

where \(d_t\) indicates termination.

The critic loss is:

\[
\mathcal L_Q
=
\mathbb E_D
\left[
\left(
Q_\theta(s_t,a_t)-y_t
\right)^2
\right].
\]

The value function can use IQL-style expectile regression:

\[
\mathcal L_V
=
\mathbb E_D
\left[
L_2^\tau
\left(
Q_{\bar\theta}(s_t,a_t)-V_\psi(s_t)
\right)
\right],
\]

where

\[
L_2^\tau(u)
=
\left|
\tau-\mathbb 1(u<0)
\right|u^2.
\]

## 5.4 Convert annotations into advantage constraints

Map the temporal labels to:

\[
y_t^{\text{ann}}
=
\begin{cases}
+1, & z_t\in\{\text{progress},\text{recovery}\},\\
-1, & z_t=\text{failure-inducing},\\
0, & z_t\in\{\text{neutral},\text{aftermath}\}.
\end{cases}
\]

This does not specify exactly how valuable the action was. It only specifies whether its advantage should be positive, negative, or approximately zero.

## 5.5 Ordinal advantage-sign loss

For positive and negative annotations:

\[
\mathcal L_{\text{sign}}
=
\mathbb E_D
\left[
\mathbb 1(y_t^{\text{ann}}\neq0)
w_t
\operatorname{softplus}
\left(
-\frac{
y_t^{\text{ann}}\hat A_t-m_t
}{
\tau_A
}
\right)
\right].
\]

Interpretation:

- For \(y_t^{\text{ann}}=+1\), the loss encourages \(\hat A_t>0\).
- For \(y_t^{\text{ann}}=-1\), it encourages \(\hat A_t<0\).
- \(m_t\) is a margin controlling how strong the distinction should be.
- \(\tau_A\) controls smoothness.

For neutral and aftermath actions:

\[
\mathcal L_{\text{neutral}}
=
\mathbb E_D
\left[
\mathbb 1(y_t^{\text{ann}}=0)
w_t\hat A_t^2
\right].
\]

The complete annotation loss is:

\[
\boxed{
\mathcal L_{\text{ann}}
=
\mathcal L_{\text{sign}}
+
\lambda_0\mathcal L_{\text{neutral}}
}
\]

This is the central proposed mathematical contribution.

# 6. Causal temporal responsibility

Not every action in a failure segment is equally responsible.

If the VLM predicts decisive error \(t^*\), define:

\[
\rho_t
=
\exp
\left(
-\frac{|t-t^*|}{\kappa}
\right).
\]

Let \(q_t\) be the VLM confidence. Then:

\[
w_t=q_t\rho_t.
\]

Actions near the decisive error receive strong supervision. Distant or uncertain actions receive weaker supervision.

Severity can optionally control the margin:

\[
m_{\text{catastrophic}}
>
m_{\text{medium}}
>
m_{\text{low}}.
\]

Thus, a catastrophic collision can be pushed further into negative-advantage territory than a harmless timeout.

# 7. Cause-matched action comparisons

Where possible, retrieve productive and failed actions from comparable states and the same task phase:

\[
(s^+,a^+)
\quad\text{and}\quad
(s^-,a^-).
\]

For example:

- Successful grasp versus failed grasp.
- Collision-free reach versus colliding reach.
- Correct object selection versus incorrect object selection.

If the states are sufficiently similar,

\[
\left\|
f(s^+)-f(s^-)
\right\|<\epsilon,
\]

apply the pairwise ranking loss:

\[
\mathcal L_{\text{pair}}
=
-\log\sigma
\left(
\frac{
Q_\theta(s^+,a^+)-Q_\theta(s^-,a^-)
}{
\tau_Q
}
\right).
\]

This teaches:

\[
Q(s^+,a^+)>Q(s^-,a^-).
\]

Cause labels guide which actions should be compared, giving the semantic diagnosis a direct role.

# 8. Cause-specific risk model

An optional shared risk model predicts:

\[
C_\eta(s,a)
=
\begin{bmatrix}
C_{\text{reach}}\\
C_{\text{grasp}}\\
C_{\text{manip}}\\
C_{\text{sequence}}\\
C_{\text{collision}}
\end{bmatrix}.
\]

Each output predicts the probability of a particular failure type.

Train it with multi-label binary cross-entropy:

\[
\mathcal L_{\text{cause}}
=
-\sum_c
\left[
y_{t,c}\log C_{\eta,c}(s_t,a_t)
+
(1-y_{t,c})
\log\left(1-C_{\eta,c}(s_t,a_t)\right)
\right].
\]

The risk-adjusted advantage is:

\[
\tilde A_t
=
\hat A_t
-
\lambda_C
\sum_c
\alpha_cC_{\eta,c}(s_t,a_t).
\]

This allows an action to be recognized as task-progressing but risky. For example, a fast movement might approach the goal while increasing collision risk.

# 9. Complete critic objective

The full objective is:

\[
\boxed{
\mathcal L_{\text{critic}}
=
\mathcal L_Q
+
\lambda_V\mathcal L_V
+
\lambda_{\text{ann}}\mathcal L_{\text{ann}}
+
\lambda_{\text{pair}}\mathcal L_{\text{pair}}
+
\lambda_{\text{cause}}\mathcal L_{\text{cause}}
}
\]

The initial implementation should use only:

\[
\mathcal L_Q
+
\lambda_V\mathcal L_V
+
\lambda_{\text{ann}}\mathcal L_{\text{ann}}.
\]

Pairwise ranking and cause-specific risk should be added only after the central ordinal advantage method works.

# 10. Policy improvement

Train a small actor through advantage-weighted behavior cloning:

\[
\mathcal L_\pi
=
-\mathbb E_{(s,a)\sim D}
\left[
\omega_t\log\pi_\phi(a_t\mid s_t)
\right],
\]

where:

\[
\omega_t
=
\operatorname{clip}
\left(
\exp\left(\frac{\tilde A_t}{\beta}\right),
0,
\omega_{\max}
\right).
\]

This causes:

- Productive actions to receive high imitation weights.
- Useful actions from globally failed episodes to remain usable.
- Failure-causing actions to receive low weights.
- Risky actions to be further downweighted.
- Neutral and aftermath actions to contribute little.

The VLM does not directly control the policy. It supplies semantic supervision to the critic, which determines the actor’s training weights.

# 11. Models and compute

No VLA is fine-tuned.

## VLM

The VLM is used only for offline annotation through:

- A hosted multimodal model.
- A quantized local VLM.
- An existing failure-reasoning VLM.
- Human annotations as an oracle.

## Frozen visual features

For image observations:

\[
e_t=f_{\text{frozen}}(I_t).
\]

Precompute all embeddings so the image encoder does not run during every RL update.

## Trainable components

A practical implementation could use:

- A GRU or small temporal transformer with hidden size 256.
- Two small Q-networks.
- One value network.
- One Gaussian continuous-action actor.
- One optional cause-classification head.

The trainable system can remain below approximately 10–20 million parameters, which is easily manageable on a 24 GB RTX 3090.

# 12. Dataset and evaluation strategy

The project should use two domains.

## Simulation

Use ManiSkill, robosuite, RoboCasa, or OopsieVerse if internally available.

Generate:

- Successful rollouts.
- Near-successes.
- Failed rollouts.
- Rollouts from different policy checkpoints.
- Controlled failures introduced through perturbations.
- Multiple failure causes.

Simulation enables:

- Closed-loop policy evaluation.
- Ground-truth task success.
- Ground-truth or automatically detectable failure times.
- Controlled experiments.
- Multiple random seeds.

Begin with state observations. Add frozen image embeddings only after the state-based method works.

## OopsieData

Use OopsieData for real-world validation:

- Evaluate VLM temporal segmentation against human labels.
- Evaluate cause predictions against its existing taxonomy.
- Test Q-value and action-pair ranking.
- Measure how much productive data is recovered from failed episodes.
- Test generalization across tasks, robots, policies, or labs.

The public statistics page currently shows zero released annotated episodes, so internal dataset access and usable episode counts must be confirmed before committing. genui{"citation":{"ref":"turn1view2"}}

# 13. Human-annotated reference set

Manually annotate approximately 100–300 trajectories with:

- Temporal segments.
- Failure onset.
- Decisive error.
- Visible failure.
- Failure cause.
- Severity.
- Recoverability.
- Recovery attempt.
- Recovery success.

At least 30–50 trajectories should be independently labeled by two annotators.

Measure:

- Inter-annotator agreement.
- Temporal-boundary disagreement.
- Cause agreement.
- Decisive-error agreement.
- Recoverability agreement.

This provides a realistic performance ceiling for the VLM.

# 14. Baselines

## Data-use baselines

1. Success-only behavior cloning.
2. Behavior cloning on all trajectories.
3. Behavior cloning on successful episodes plus productive failure prefixes.
4. Episode-outcome-weighted behavior cloning.
5. Fixed VLM segment weights.

## Offline-RL baselines

1. IQL with terminal success reward.
2. IQL with uniform penalties for failed episodes.
3. IQL with a hand-designed dense progress reward.
4. IQL with fixed VLM-generated labels mapped to \(+1\), \(0\), and \(-1\).
5. Ordinal advantage learning without failure causes.
6. Ordinal advantage learning without decisive-error weighting.
7. Full proposed method.
8. Human-label oracle.

## Annotation baselines

1. Episode outcome only.
2. Rule-based segmentation.
3. Generic failure classifier.
4. Zero-shot VLM prompting.
5. Structured VLM prompting.
6. VLM plus robot telemetry.
7. Human annotations.

# 15. Required ablations

## Temporal precision

Compare:

\[
\text{episode label}
\rightarrow
\text{failure segment}
\rightarrow
\text{decisive action}.
\]

## Ordinal supervision versus fixed rewards

Compare:

\[
r_t\in\{-1,0,+1\}
\]

against the proposed advantage-sign loss.

## Cause information

Compare:

- Generic failure label.
- Cause-matched pair ranking.
- Cause-specific risk heads.

## Confidence weighting

Compare:

\[
w_t=1
\]

against:

\[
w_t=q_t.
\]

## Responsibility weighting

Compare uniform weighting against:

\[
\rho_t=e^{-|t-t^*|/\kappa}.
\]

## Annotation noise

Corrupt labels and timestamps at controlled rates such as 5%, 10%, 20%, and 30%.

## Human versus VLM

Compare:

- Human labels.
- VLM labels.
- Confidence-filtered VLM labels.
- Small human seed set plus VLM pseudo-labels.

# 16. Evaluation metrics

## Annotation quality

- Segment macro-F1.
- Segment intersection-over-union.
- Cause macro-F1.
- Failure-onset localization error.
- Decisive-error localization error.
- VLM confidence calibration.

Normalized temporal error:

\[
E_{\text{time}}
=
\frac{|\hat t-t|}{T}.
\]

## Critic quality

- State-value ranking accuracy.
- Action-pair ranking accuracy.
- Correlation with simulator returns.
- Value calibration.
- Cause-specific risk classification.
- Generalization to held-out tasks and failure modes.

## Policy quality

- Task success rate.
- Return.
- Recovery success.
- Overall failure rate.
- Collision rate.
- Grasp-failure rate.
- Performance under perturbations.
- Performance as successful demonstrations become scarce.

Cause-specific improvement can be measured as:

\[
\Delta F_c
=
F_c(\pi_{\text{baseline}})
-
F_c(\pi_{\text{proposed}}).
\]

# 17. Expected contributions

The project aims to contribute:

1. A temporal and causal annotation schema for failed robot trajectories.
2. A VLM-assisted annotation pipeline.
3. An ordinal advantage-learning objective that avoids arbitrary dense reward assignment.
4. A temporal-responsibility mechanism centered on the decisive error.
5. Cause-matched Q-value ranking.
6. Optional cause-specific risk prediction.
7. A human-annotated real-robot subset of OopsieData, subject to permission.
8. A controlled simulation benchmark for policy improvement from failure data.

# 18. Novelty claim

The paper should not be framed as:

> We use a VLM to generate robot rewards.

The stronger claim is:

> Failed robot rollouts provide ordinal advantage supervision. Temporally localized VLM diagnoses identify which actions should receive positive, negative, or neutral advantage, allowing offline policy improvement without manually designed dense rewards or VLA fine-tuning.

The main conceptual pipeline is:

\[
\text{failure diagnosis}
\rightarrow
\text{advantage constraints}
\rightarrow
\text{critic learning}
\rightarrow
\text{offline policy improvement}.
\]

# 19. Risks and fallbacks

## VLM identifies symptoms instead of causes

Mitigation:

- Request symptom, onset, decisive error, and root cause separately.
- Include robot telemetry.
- Use human oracle labels.
- Allow `unclear`.
- Weight by confidence.

## VLM labels are noisy

Mitigation:

- Confidence filtering.
- Human verification.
- Soft losses rather than hard rewards.
- Noise-robustness experiments.

## OopsieData is too heterogeneous

Mitigation:

- Start with one robot/task subset.
- Normalize actions carefully.
- Use simulation for closed-loop policy evaluation.
- Treat cross-embodiment generalization as a stretch goal.

## No matching physical robot is available

Mitigation:

- Perform policy evaluation in simulation.
- Use OopsieData for annotation, critic, and action-ranking validation.
- Do not claim real-world policy improvement without real rollouts.

## Full offline RL is unstable

Fallback progression:

1. Evaluate the VLM annotations.
2. Train the critic/value model.
3. Demonstrate improved action and state ranking.
4. Train a small state-based actor in simulation.
5. Add frozen visual features.
6. Validate the critic on OopsieData.

# 20. Project stages

### Stage 1: Data and taxonomy

- Confirm OopsieData access.
- Select two or three tasks.
- Load and synchronize video, states, and actions.
- Finalize annotation definitions.
- Manually annotate a seed set.

### Stage 2: VLM annotation

- Build structured prompts.
- Compare video-only and video-plus-telemetry inputs.
- Evaluate against human annotations.
- Analyze confidence and common errors.

### Stage 3: Simulation data

- Choose three to five manipulation tasks.
- Generate successful and failed rollouts.
- Record state, action, video, and task outcomes.
- Create multiple failure modes.

### Stage 4: Baseline offline RL

- Implement success-only BC.
- Implement mixed-data BC.
- Implement terminal-reward IQL or AWR.
- Confirm closed-loop simulation evaluation.

### Stage 5: Ordinal advantage method

- Add advantage-sign supervision.
- Add temporal responsibility.
- Run main comparisons.

### Stage 6: Cause-aware extension

- Add cause-matched action comparisons.
- Add cause-specific risk heads.
- Evaluate whether semantic cause information improves performance.

### Stage 7: OopsieData validation

- Apply the VLM and critic to real trajectories.
- Evaluate temporal and cause accuracy.
- Evaluate action/value ranking.
- Test generalization where possible.

# 21. Minimum viable publishable-style result

A strong minimum result would show that:

1. VLMs can localize productive and failure-inducing segments above simple baselines.
2. Ordinal advantage supervision improves critic ranking over terminal-reward offline RL.
3. A small offline RL policy achieves higher simulation success than BC, mixed BC, and standard terminal-reward IQL.
4. The method remains effective under moderate annotation noise.
5. OopsieData experiments show that the annotation and critic behavior transfer to real robot trajectories.

The cause-specific risk model strengthens the paper, but it should not block completion of the central ordinal advantage method.

# 22. Final project summary

Failed robot trajectories should not be treated as uniformly bad episodes. Productive behavior, decisive errors, recovery attempts, and irrelevant aftermaths provide different learning signals.

The proposed method uses a VLM to reveal this structure but does not trust it to invent numerical rewards. Instead, its annotations supervise whether dataset actions should have positive, negative, or neutral advantage. These constraints augment a standard offline-RL critic, and the resulting advantages determine how strongly a small policy imitates each action.

This creates a publishable algorithmic question while remaining computationally practical:

> Can semantic failure diagnosis solve offline-RL credit assignment more effectively than terminal rewards or manually designed VLM reward mappings?

---

If you want, I can:

- Design VLM prompts for failure cause identification
- Develop evaluation strategy for VLM annotation quality
- Plan implementation of ordinal advantage learning losses
