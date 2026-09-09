# Frozen r6 audit — 2026-09-08

**r6 is not ready to serve as trusted action-credit supervision.** A purposive 12-episode audit found clear
label disagreements in 4 episodes, unresolved semantic concerns in 4 more, and no issue in the inspected
evidence for the remaining 4. This is an exploratory assistant audit, not human ground truth or a corpus accuracy estimate.

[Open the review pack](../outputs/oracle_audit_r6/index.html), which contains unlabelled videos, clickable r6 chunk
labels, per-episode findings, and links to the camera evidence. The original r6 review and corpus exports are unchanged.

## Method and limits

- Freeze the implementation before review: SHA-256 `5a5fb5321e5e7bd01831dce1f650e526882ef458577a716326795da7d7dca9ff`.
  A source snapshot and exact sample manifest are in `outputs/oracle_audit_r6/`.
- Select two episodes each of clean success, recovered success, missed grasp, transport drop, and timeout;
  add one wrong-object case and one release miss. Selection used older reference metadata, not r6 disagreements.
- Eight failures come from the existing held-out failure split; four supplemental successes are outside both
  the dev and held-out failure splits. Exclude both episodes used for r4-r6 interactive development.
- Rebuild only these references under the audit directory. No annotation-rule or corpus-export changes.
- Inspect 24 uniformly spaced, unlabelled paired-camera observations per episode before reading r6 labels:
  288 observations across 3,286 frames / 331 chunks. Record the initial visual impressions separately.
- Compare with r6, then inspect 13 dense camera sheets and full-resolution simulator telemetry for disputed regions.
  The reviewer knew category/task/outcome metadata. This is not fully blind, continuous-video or exhaustive per-action review.

The sample covers three suites but only single-movable-target tasks. It does not establish reliability for multi-object
sequencing, fixture-only tasks, collisions, or never-reached failures. The reviewed episodes should now be treated as
development evidence, not reused as an untouched final evaluation set.

## Per-episode results

All chunk indices are zero-based. “No issue found” means no contradiction in inspected evidence, not a guarantee of correctness.

| Stratum | Episode | Result | Main evidence |
|---|---|---|---|
| Clean success | `full_anchor__t0 / 0` | No issue found | Acquisition, sustained carry, lowering into basket and success credit are coherent. |
| Clean success | `full_goals8__t1 / 4` | No issue found | Bowl acquisition and transport to stove agree with progress labels. |
| Recovered success | `full_shift16__t1 / 18` | Clear disagreement | c7 gives certain recovery to a failed acquisition; c12 discards a detected closure because of table contact. |
| Recovered success | `full_goals8__t9 / 2` | No issue found | Failed closure, sustained re-grasp, lift and rack placement are coherently represented. |
| Missed grasp | `full_shift16__t1 / 14` | Semantic concern | Six supported failed acquisitions are correctly denied positive credit; earliest-miss decisiveness and aftermath between retries remain unestablished. |
| Missed grasp | `full_shift12__t3 / 11` | Clear disagreement | New failed closures in c15–16, c21 and c26–27 are primarily aftermath. No primary failure-inducing chunk anywhere. |
| Transport drop | `full_goals8__t2 / 2` | No issue found | Lift, loss at 65–66 and subsequent empty-gripper tail agree with the annotation. |
| Transport drop | `full_l90__t74 / 7` | Semantic concern | c9–16 default to progress during constrained insertion; contact loss does not establish the causal error. |
| Timeout | `full_shift16__t2 / 10` | Semantic concern | c17–27 remain primary progress while the gripper/bottle drags the basket. |
| Timeout | `full_l90__t74 / 8` | Semantic concern | Insertion/idle sequence is real, but “progress” during manoeuvring and decisive c27 are not independently established. |
| Wrong object | `full_l90__t47 / 11` | Clear disagreement | Repeated wrong grasps become aftermath; actual grasp chunks c24 and c35 even exclude failure from their allowed sets. |
| Release miss | `full_shift8__t6 / 15` | Clear disagreement | c9 recovery and c10 progress reward a failed acquisition with one unsupported frame. Final release miss is sensible. |

The clear-disagreement count is 3/8 held-out failures and 1/4 supplemental successes. These are counts in this purposive
sample; the denominators are too small and selection too targeted to interpret as population error rates.

## Findings that justify rejecting trusted supervision

### 1. “At least eight hold frames and any airborne frame” is insufficient

In `full_shift16__t1 / 18`, the hold at frames 77–89 lasts 13 frames, but support is absent for only frame 89.
The object centre rises at most **0.48 cm** relative to frame 76 and moves **1.06 cm** in xy during the hold.
Dense images show a failed squeeze followed by another attempt. Nevertheless, c7 is `{recovery}`, **q=1**.

In `full_shift8__t6 / 15`, the hold at 99–110 lasts 12 frames, with only frame 109 airborne. c9 is `{recovery}` and
c10 is `{progress}`, both **q=1**, before the slip. This is a brief tilt/manipulation followed by failure, not the
established recovery the singleton labels claim. The later 96-frame carry is visibly different and is appropriately credited.

The physical flags are not necessarily wrong. The semantic conversion of one unsupported instant into an established
acquisition is the problem. Increasing a duration threshold alone is not a validated solution.

### 2. A table brush deletes part of a failed attempt in successful episodes

In the recovered cream-cheese example, r6 detects a failed closure at **123–130**. The success-only `is_miss` filter
rejects c12's record because it includes static contact at 123; there is no fixture contact. c12 becomes singleton
neutral, while the record starting at 130 survives and c13 allows failure/neutral. One physical attempt therefore
receives inconsistent treatment depending on which chunk slice contains the table touch.

This is separate from uncertainty about whether every action in a boundary chunk deserves negative credit: the
failure option disappears entirely in c12, despite the visual and aperture evidence of the unsuccessful closure.

### 3. Post-decisive rules erase new errors

In the BBQ-sauce episode, later closures close on nothing at 154–158, 160–165, 211–216, 262–267 and 270–272.
Dense images show active retry/manipulation, not simply a stationary consequence of the first miss. All are primarily
`aftermath` under `post_event`. Failure remains in some allowed sets, but the current exporter uses the primary label
and thus supplies neutral rather than negative supervision. A failed-attempt trajectory can contain no primary negative label.

In the wrong-object episode, the cream-cheese target never moves while the soup can is repeatedly acquired. The wrong
contact runs begin at 231 and 345, but the actual grasps begin at **249 and 357**. The code places the wrong-grasp
record only in contact-start chunks 23 and 34. Actual grasp chunks **24 and 35** become `post_recoverable`:
`{neutral, aftermath, recovery}`, excluding failure. This is a concrete boundary/label inconsistency, not just a disputed primary choice.

## Concerns requiring a clearer semantic contract

- **Active hold is not automatic progress.** In the salad-dressing timeout, the basket translates **8.33 cm** in xy
  from 170–279 while the gripper/bottle interacts with its rim. Target-to-basket xy distance decreases from **5.60 to
  2.67 cm**, yet placement is never satisfied. c17–27 are all primary progress with allowed `{progress, neutral}`.
  The evidence does not prove every action is negative; it does show why distance and motion alone cannot establish positive credit.
- **Fixture goals need geometry.** Both book episodes manoeuvre at a caddy compartment. With no movable goal slot,
  the rules use generic displacement and `pre_other` progress; they do not establish alignment with the requested compartment.
- **Decisive is not validated.** The first failed closure or start of the final idle run is observable, but neither
  proves when success became impossible. The timeout book has earlier idle periods as well. Keep these as heuristic
  landmarks until branching or an independently defined causal criterion is available.

## Recommended next work

Do not promote the existing primary labels and q values to trusted supervision. Keep r6 and this audit frozen.
First define successful acquisition in terms of sustained object control and the task state achieved, with supported
grasps, thin objects and meaningful placement explicitly accounted for. Then localize **every** new error independently
of the episode's decisive marker, use actual wrong-grasp boundaries, and make attempt filtering operate on whole attempts.
For placement/manoeuvring without goal-geometry evidence, abstain from certain positive credit.

Use these cases as regression examples when those changes are authorized, then evaluate on a new sample with independent
human labels. No rule changes were made in this audit. The regression tests establish implementation consistency, not
semantic validity; three singleton positive labels above are direct examples of why q=1 is not calibrated confidence.
