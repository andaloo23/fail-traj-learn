# Episode: C0341

## Episode annotation

- Language task: Pack the bottles onto the wooden tray.
- Success label: failure
- Outcome evidence: No bottle is packed onto the tray by frame 853 (overhead_cam). The robot first clears the banana from the tray, which is useful preparation (frames 74–180, overhead_cam and wrist_cam), but subsequently topples the blue-labelled bottle, fails to acquire bottles on two attempts, and finally releases the red bottle beside the tray, where it falls onto its side (frames 799–809, both cameras). This is visibly unsuccessful execution, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 219 | No |
| 219 | 231 | Yes |
| 231 | 263 | No |
| 263 | 364 | Yes |
| 364 | 453 | No |
| 453 | 546 | Yes |
| 546 | 799 | No |
| 799 | 815 | Yes |
| 815 | 854 | No |

## Failure annotations

### Failure 1

- Frames: 219-231
- Categories: collision
- Explanation: During the approach to the bottle cluster, the blue-labelled bottle tips and falls onto its side rather than being acquired (frames 219–230, overhead_cam and wrist_cam). The gripper's approach visibly disrupts the bottle's stable position; no secure possession is shown.
- Recovery: Withdraw enough to avoid further contact, locate the fallen bottle, and grasp it using its updated pose; human intervention is not necessary if a safe side grasp is available.
- Severity: low
- Severity evidence: The bottle falls only onto the tabletop, with no visible breakage or leakage.
- Resetability: minor_reset
- Resetability evidence: Returning to the previous upright arrangement requires a simple bottle-righting step; no repair or extensive cleanup is visibly needed.

### Failure 2

- Frames: 263-364
- Categories: grasp
- Explanation: The fingers close near the orange bottle, but it tips away and remains on the table as the gripper rises empty (frames 263–280, overhead_cam and wrist_cam). The robot then travels toward the tray and opens its empty fingers without delivering a bottle (frames 330–364, both cameras).
- Recovery: Return to the orange bottle's observed location, align around its body, and verify acquisition with a short lift before transporting it; human intervention is not required.
- Severity: low
- Severity evidence: The orange bottle is displaced and left on the tabletop; no damage or spilled contents are visible.
- Resetability: minor_reset
- Resetability evidence: A straightforward repositioning or righting of the orange bottle restores the prior arrangement; the scene remains usable.

### Failure 3

- Frames: 453-546
- Categories: grasp
- Explanation: After closing near the red bottle, the gripper withdraws without it; the red bottle remains standing beside the fallen blue bottle (frames 453–489, overhead_cam, with wrist_cam showing the empty fingers). The robot continues toward the tray and opens the empty gripper there (frames 513–546, both cameras), accomplishing no bottle transfer.
- Recovery: Reapproach the red bottle, center the fingers around a graspable portion, and confirm that the bottle rises with the gripper before moving to the tray; no human intervention is needed.
- Severity: low
- Severity evidence: This attempt produces no visible damage or additional substantial scene disturbance.
- Resetability: immediate
- Resetability evidence: The red bottle remains accessible in its standing position, so acquisition can be retried without environmental resetting.

### Failure 4

- Frames: 799-815
- Categories: manipulation
- Explanation: Following a successful red-bottle pickup and transport, the gripper opens with the bottle beside the tray rather than securely supported on it (frames 799–803, overhead_cam and wrist_cam). The bottle tips onto the tabletop and settles on its side outside the tray (frames 804–815, both cameras), so the placement fails.
- Recovery: Regrasp the fallen red bottle, position its base fully within the tray, lower until it is stably supported, and only then release; human intervention is not needed if the bottle remains safely graspable.
- Severity: low
- Severity evidence: The red bottle topples onto the table without visible breakage, leakage, or damage to nearby objects.
- Resetability: minor_reset
- Resetability evidence: Restoring an upright bottle for another placement attempt requires only a simple righting or repositioning step.