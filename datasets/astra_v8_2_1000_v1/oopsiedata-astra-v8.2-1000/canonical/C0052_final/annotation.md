# Episode: C0052

## Episode annotation

- Language task: pik up one objet from the big bowl and put inside the small box that is empty
- Success label: failure
- Outcome evidence: The robot initially carries the loaded bowl rather than an individual object (right and top, frames 180-588), then extracts the spotted plush (left, right and top, frames 810-840). It repeatedly repositions that object and releases it onto the tabletop outside the boxes (for example, frames 1364-1375 and 1791-1799). At frame 1999, left, right and top show the plush still at the gripper beside the bowl, not inside a box. Thus unsuccessful transfers are visible and eventual completion remains unconfirmed; the recording ending does not establish abnormal termination. Both orange boxes appear empty in top, so the intended destination is not uniquely distinguishable, but neither receives the object.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 141 | No |
| 141 | 588 | Yes |
| 588 | 890 | No |
| 890 | 1354 | Yes |
| 1354 | 1364 | Yes |
| 1364 | 1376 | Yes |
| 1376 | 1475 | No |
| 1475 | 1485 | Yes |
| 1485 | 1499 | No |
| 1499 | 1512 | Yes |
| 1512 | 1674 | No |
| 1674 | 1684 | Yes |
| 1684 | 1791 | No |
| 1791 | 1800 | Yes |
| 1800 | 2000 | No |

## Failure annotations

### Failure 1

- Frames: 141-588
- Categories: sequencing_semantic
- Explanation: The robot displaces the bowl from frame 141 and lifts and carries the entire loaded container instead of extracting one object (left, right and top, frames 180, 300, 350, 480 and 570). This is continuous wrong-object handling across the window boundary, ending when lowering and release recovery begin around frame 588.
- Recovery: Set the bowl down stably, release its rim, and grasp an individual object inside before transporting it to an empty small box; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The contents remain contained, with no visible spill, damage or harmful impact; the consequence is an unsuccessful task detour.
- Resetability: minor_reset
- Resetability evidence: The held, displaced bowl needs straightforward lowering and release to restore a stable acquisition setup, without repair or human assistance.

### Failure 2

- Frames: 890-1354
- Categories: manipulation
- Explanation: After extracting the spotted plush, the robot repeatedly carries it away from and back toward the bowl without progressing to either box (left and top, frames 890, 960, 990, 1050, 1110, 1200, 1260, 1290 and 1350). The sustained reversals establish unproductive post-acquisition transport rather than a brief pause or failed grasp.
- Recovery: Maintain secure retention and transport the plush along a clear path over an empty small box, then lower and release it inside; no human intervention is visibly needed.
- Severity: low
- Severity evidence: Placement is delayed, but the plush remains held and no damage or loss is visible during this interval.
- Resetability: immediate
- Resetability evidence: The object is controlled and the boxes remain available, permitting placement without an environmental reset.

### Failure 3

- Frames: 1354-1364
- Categories: collision
- Explanation: As the held plush and gripper approach the bowl rim, the bowl shifts and rotates in top across frames 1354-1363; left shows the close rim interaction. This unintended displacement does not advance delivery, though the exact contacting component is obscured.
- Recovery: Withdraw clear of the bowl, reassess its position, and transport the held object along a collision-free route to the empty box; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The bowl remains upright and its contents stay inside, with no visible damage or spill.
- Resetability: immediate
- Resetability evidence: The displaced bowl remains usable and accessible; restoring its exact previous position is unnecessary.

### Failure 4

- Frames: 1364-1376
- Categories: grasp
- Explanation: The fingers open and the previously held plush separates onto the tabletop during frames 1364-1375 in left; top confirms it is outside both boxes. Retention ends before delivery, although deliberate release versus accidental loss is not established.
- Recovery: Reacquire the plush from the table, verify secure retention, and carry it into an empty small box before releasing; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The soft object lands on the tabletop without visible damage or disruption to other objects.
- Resetability: immediate
- Resetability evidence: The plush remains accessible for autonomous reacquisition without environmental resetting.

### Failure 5

- Frames: 1475-1485
- Categories: collision
- Explanation: The gripper-held plush reaches the bowl rim in left at frames 1475-1476, and top shows the bowl sliding rightward through frame 1484. The interaction displaces the source container rather than advancing placement; the precise contacting component is partly obscured.
- Recovery: Withdraw from the rim and use a clear route above the bowl to transport the securely held plush to an empty box; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The bowl stays upright with its contents contained, and no damage is visible.
- Resetability: immediate
- Resetability evidence: The bowl remains accessible and usable in its new position, so no environmental reset is required.

### Failure 6

- Frames: 1499-1512
- Categories: grasp
- Explanation: After retaining the plush through frame 1498, the gripper opens and the plush separates onto the table during frames 1499-1511 in left. Top confirms the release occurs left of the bowl, outside both boxes; whether it is deliberate or accidental is unclear.
- Recovery: Reacquire the plush around a secure body section, verify retention with a small lift, and transport it over an empty box before releasing; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The soft plush lands on the table without visible damage or disturbance to other objects.
- Resetability: immediate
- Resetability evidence: The object remains within the accessible tabletop workspace and can be reacquired without resetting the environment.

### Failure 7

- Frames: 1674-1684
- Categories: grasp
- Explanation: Following visible retention at frames 1650-1673, the fingers open at frame 1674 and the plush separates onto the tabletop beside the bowl, remaining outside both boxes through frame 1683 (left, right and top). This interrupts delivery; release intent is not established.
- Recovery: Reacquire the plush securely and move it over an empty small box before lowering and releasing it; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The plush remains on the tabletop, with no visible damage, spill or overturned container.
- Resetability: immediate
- Resetability evidence: The plush is accessible beside the bowl, allowing another acquisition attempt without environmental intervention.

### Failure 8

- Frames: 1791-1800
- Categories: grasp
- Explanation: After carrying the plush through frame 1790, the gripper opens and the plush separates onto the tabletop at frames 1791-1799 in left, right and top, outside both boxes. Retention ends before delivery; deliberate release versus accidental loss remains unclear. Repositioning for reacquisition follows from frame 1800.
- Recovery: Reacquire the plush, confirm a stable hold, and carry it over an empty box before lowering and releasing it inside; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The soft plush lands on the tabletop without visible damage or disruption to other objects.
- Resetability: immediate
- Resetability evidence: The object remains accessible beside the robot, so reacquisition requires no environmental reset or human assistance.