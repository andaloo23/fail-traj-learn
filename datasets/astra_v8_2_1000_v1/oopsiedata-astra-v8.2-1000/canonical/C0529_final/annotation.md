# Episode: C0529

## Episode annotation

- Language task: pick up the duckie next to the spoon and place it into the mug
- Success label: success but side effects
- Outcome evidence: The target duck is visible beside the spoon in frames 35–54 in wrist and left; after a missed acquisition, it is lifted in frames 68–70 and released into the mug in frames 76–79 (wrist, corroborated by left). However, the robot also handles an unrelated red-handled utensil in frames 22–32 and subsequently displaces the spoon in frames 89–109. Completion is visible, but includes unrelated-object manipulation and a failed grasp.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 22 | No |
| 22 | 33 | Yes |
| 33 | 55 | No |
| 55 | 60 | Yes |
| 60 | 89 | No |
| 89 | 120 | Yes |

## Failure annotations

### Failure 1

- Frames: 22-33
- Categories: sequencing_semantic
- Explanation: In wrist, the gripper closes on the red handle of an unrelated utensil in frames 22–24, carries it toward the mug in frames 27–31, and opens in frame 32; left shows the target duck remaining beside the foreground spoon. Handling this utensil does not accomplish the requested duck transfer.
- Recovery: Release the unrelated utensil safely onto the counter, then locate and grasp the duck beside the spoon; human intervention is not visibly necessary.
- Severity: low
- Severity evidence: An unrelated utensil is moved, but no breakage, spill, or other damage is visible.
- Resetability: minor_reset
- Resetability evidence: Returning the displaced utensil to its original counter position is a straightforward reset; no repair or difficult retrieval is indicated.

### Failure 2

- Frames: 55-60
- Categories: grasp
- Explanation: The fingers close beside the duck in frames 55–56 (wrist), then retract empty in frames 57–59 while the duck remains on the counter in both wrist and left. This establishes an unsuccessful acquisition rather than merely an unfinished grasp.
- Recovery: Reopen the gripper, recenter the fingers around the duck, and retry a controlled grasp with lift verification; no human intervention is needed.
- Severity: low
- Severity evidence: The duck remains accessible on the counter, with no visible damage or harmful consequence.
- Resetability: immediate
- Resetability evidence: No environmental intervention is required before another grasp attempt.

### Failure 3

- Frames: 89-120
- Categories: sequencing_semantic
- Explanation: After depositing the duck, the robot lowers to the unrelated spoon in frames 89–93 (left and wrist) and continues interacting with it through frame 119. The spoon shifts and rotates beneath the gripper, particularly across frames 102–109 in wrist. This extra manipulation does not advance the already completed task.
- Recovery: Stop manipulating the spoon and retract clear of the tableware; restore the spoon to its original position if scene restoration is required. Human intervention is not necessarily needed.
- Severity: low
- Severity evidence: The spoon is displaced on the counter, but no damage, falling object, or spill is visible.
- Resetability: minor_reset
- Resetability evidence: Restoring the spoon requires only a simple repositioning on the accessible countertop.