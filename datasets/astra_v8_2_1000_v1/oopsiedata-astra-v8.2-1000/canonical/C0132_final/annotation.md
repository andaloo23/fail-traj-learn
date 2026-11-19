# Episode: C0132

## Episode annotation

- Language task: Pick up the stuffed animal and place it in the box.
- Success label: failure
- Outcome evidence: In external and wrist, the stuffed animal remains on the table outside the box from frame 0 through frame 1273. The robot approaches and adjusts near the animal (frames 338–743), but no possession or lift is visible; it subsequently withdraws empty (frames 825–943) and never places the animal in the box. Completion is visibly absent, rather than merely hidden by the final camera view; a completed failed grasp is not established.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 825 | No |
| 825 | 1274 | Yes |

## Failure annotations

### Failure 1

- Frames: 825-1274
- Categories: task_not_attempted
- Explanation: After approaching the animal, the robot moves away without it in external and wrist (frames 825–943), then remains away with only small further adjustments and prolonged inactivity through frame 1273. The animal stays on the table and no renewed acquisition or placement attempt occurs. This sustained unproductive withdrawal does not advance the task; the images do not establish a completed grasp attempt or a hidden cause.
- Recovery: Re-localize the animal, align the open fingers around a graspable portion of its body, acquire it, and verify retention with a small lift before transporting it over the box and releasing it. No human intervention is visibly required.
- Severity: low
- Severity evidence: The task remains unfinished, but neither camera shows damage, displaced unrelated objects, or a concrete risk of damage.
- Resetability: immediate
- Resetability evidence: The animal remains accessible on the tabletop and the box remains upright and available; no environmental resetting or human intervention is needed for another attempt.