# Episode: C0456

## Episode annotation

- Language task: Push the Displayport cable into the cable holder on the white block.
- Success label: failure
- Outcome evidence: The cable remains on the mat rather than seated in the holder: compare frames 0, 600 and 911 in wrist and top. The robot approaches and operates its fingers around the holder without bringing the cable to it (frames 445–566, front and wrist), then withdraws empty (frames 567–600). The final views establish that insertion was not achieved, rather than merely leaving completion unconfirmed.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 9 | No |
| 9 | 400 | Yes |
| 400 | 445 | No |
| 445 | 567 | Yes |
| 567 | 607 | No |
| 607 | 912 | Yes |

## Failure annotations

### Failure 1

- Frames: 9-400
- Categories: task_not_attempted
- Explanation: The gripper lingers away from the cable, making small back-and-forth movements without acquiring it or advancing insertion; the cable and holder remain unchanged across frames 9, 100, 200, 300 and 399 in top and wrist. This is sustained unproductive behavior, not just a brief alignment pause.
- Recovery: Approach a visible cable section, position the fingers around it and establish control before moving it toward the holder; no human intervention is visibly needed.
- Severity: low
- Severity evidence: Only progress is prevented; front, top and wrist show no damage or disruptive object displacement.
- Resetability: immediate
- Resetability evidence: The cable and holder remain accessible and unchanged, so another attempt requires no environmental reset.

### Failure 2

- Frames: 445-567
- Categories: sequencing_semantic
- Explanation: The robot lowers and opens or closes its fingers around the holder instead of first bringing the cable into position (frames 445, 470, 500 and 554, front and wrist). The cable remains below and outside the holder, as also confirmed after withdrawal at frame 600 in wrist. Operating at the empty holder does not perform the requested cable insertion; possession of the cable is never established.
- Recovery: Withdraw clear of the block, acquire or otherwise control the cable, align a cable section with a holder slot and then press it into that slot; no human intervention is visibly required.
- Severity: low
- Severity evidence: No breakage, lasting deformation or meaningful damage risk is established; the visible consequence is an unsuccessful insertion sequence.
- Resetability: immediate
- Resetability evidence: The block remains upright and the cable remains on the accessible mat, with no cleanup or manual restoration visibly needed.

### Failure 3

- Frames: 607-912
- Categories: task_not_attempted
- Explanation: After withdrawing, the robot remains essentially stationary without reapproaching or moving the cable for the remainder of the episode (frames 607, 700, 800 and 911, front, top and wrist). The cable stays outside the holder throughout this sustained stall.
- Recovery: Resume with a cable-directed acquisition and alignment attempt, then verify seating after pressing the cable into the holder; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The task remains incomplete, but no additional scene disruption or damage is visible.
- Resetability: immediate
- Resetability evidence: The final scene retains an accessible cable and upright holder, permitting another attempt without resetting the environment.