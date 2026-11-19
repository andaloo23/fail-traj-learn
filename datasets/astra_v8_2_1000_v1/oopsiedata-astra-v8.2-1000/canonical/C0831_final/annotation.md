# Episode: C0831

## Episode annotation

- Language task: Stack all the bowls on the table into the middle bowl.
- Success label: failure
- Outcome evidence: Frame 0 (head) shows pink, yellow, and blue bowls, with yellow the plausible middle receiving bowl. The first blue-bowl placement fails: frames 164–177 (head, right_wrist) show blue and yellow tipping apart rather than nesting. Pink is subsequently placed into yellow in frames 269–289 (head, left_wrist, right_wrist). At frame 386 (head, left_wrist, right_wrist), blue remains separately on the table, so all bowls are visibly not stacked; this is not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 164 | No |
| 164 | 178 | Yes |
| 178 | 332 | No |
| 332 | 345 | Yes |
| 345 | 387 | No |

## Failure annotations

### Failure 1

- Frames: 164-178
- Categories: manipulation
- Explanation: After successfully carrying blue toward yellow, the robot releases it off-center; frames 164–170 (head, right_wrist) show the bowls tipping against one another, and frames 171–177 show them separating instead of forming a stack. This is a failed placement following established object control.
- Recovery: Wait for the bowls to settle, reacquire blue, and center it over the upright yellow bowl before lowering and releasing; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The empty bowls tip and shift on the tabletop without visible breakage, spilling, or damage.
- Resetability: immediate
- Resetability evidence: Both bowls remain accessible on the table and settle opening-up, allowing another robotic attempt without a human reset.

### Failure 2

- Frames: 332-345
- Categories: grasp
- Explanation: Following the blue-bowl grasp closure in frames 308–318 (right_wrist), the right gripper withdraws empty starting at frame 332; frames 338–344 (head, left_wrist, right_wrist) confirm blue remains on the table while the closed gripper moves away. The completed acquisition attempt therefore failed.
- Recovery: Reopen and realign the gripper around the blue bowl’s rim, secure and verify acquisition with a small lift, then place it into the existing stack; no human intervention is needed.
- Severity: low
- Severity evidence: The missed acquisition leaves blue on the tabletop with no visible damage or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: Blue remains reachable beside the pink-and-yellow stack, so the robot can retry without environmental intervention.