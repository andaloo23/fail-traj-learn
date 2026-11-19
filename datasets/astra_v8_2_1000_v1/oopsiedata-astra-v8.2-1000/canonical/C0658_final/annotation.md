# Episode: C0658

## Episode annotation

- Language task: Pick up the green cup and stack it on the purple.
- Success label: failure
- Outcome evidence: The cups begin separate in top at frame 0. During acquisition, the green cup tips onto its side rather than being carried away (right_wrist and top, frames 265–307). The gripper subsequently moves away empty. At frame 749, top still shows the cups separate, with the green cup on its side; right_wrist also shows it remaining on the table. This is a visibly unsuccessful acquisition and an uncompleted stack, not merely an occluded or unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 265 | No |
| 265 | 399 | Yes |
| 399 | 464 | No |
| 464 | 750 | Yes |

## Failure annotations

### Failure 1

- Frames: 265-399
- Categories: grasp
- Explanation: In right_wrist and top, frames 265–292 show the green cup tipping onto its side during acquisition. At frames 307–328 the gripper moves away while the green cup remains on the table, establishing failed acquisition. It then moves over the purple cup and withdraws without carrying the green cup (frames 343–395), so this motion cannot produce the requested stack.
- Recovery: Reobserve the fallen green cup, acquire it securely from its new pose, and restore an upright orientation before moving it above the purple cup; human intervention is not necessarily needed.
- Severity: low
- Severity evidence: The cup falls onto the tabletop; no spill, breakage, or damage is visible in right_wrist or top.
- Resetability: minor_reset
- Resetability evidence: The green cup needs straightforward reorientation from its side for an upright retry; it remains accessible on the table and requires no repair or difficult retrieval.

### Failure 2

- Frames: 464-750
- Categories: task_not_attempted
- Explanation: Following a renewed approach toward the green cup in frames 399–463, the robot remains essentially stationary without acquiring it through approximately frame 610 (right_wrist and top). It then repeats empty movement toward the purple cup and back (frames 613–737), leaving both cups unchanged instead of recovering the fallen target.
- Recovery: Reassess the green cup's actual pose and perform a verified acquisition and reorientation before attempting transfer; no human intervention is visibly required.
- Severity: low
- Severity evidence: This interval adds delay and no task progress, but no additional object displacement or damage is visible.
- Resetability: immediate
- Resetability evidence: The stalling and empty motions create no additional environmental reset requirement; recovery can resume from the existing fallen-cup state described in Failure 1.