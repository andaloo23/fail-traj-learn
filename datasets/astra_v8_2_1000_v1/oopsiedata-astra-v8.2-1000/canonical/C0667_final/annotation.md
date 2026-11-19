# Episode: C0667

## Episode annotation

- Language task: Place the toys on the plate with no collisions.
- Success label: failure
- Outcome evidence: The pink and tan toys are placed on the plate by frames 140 and 240 (wrist_cam and overhead_cam), but the blue toy remains on the table after repeated unsuccessful acquisitions. At frames 1322-1334, wrist_cam shows the blue toy falling off the table onto the floor; it remains there at frame 1366 while overhead_cam shows only the other two toys on the plate. This is visible noncompletion, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 309 | No |
| 309 | 341 | Yes |
| 341 | 389 | No |
| 389 | 510 | Yes |
| 510 | 560 | No |
| 560 | 636 | Yes |
| 636 | 641 | No |
| 641 | 780 | Yes |
| 780 | 817 | No |
| 817 | 1316 | Yes |
| 1316 | 1334 | Yes |
| 1334 | 1367 | No |

## Failure annotations

### Failure 1

- Frames: 309-341
- Categories: grasp
- Explanation: Following closure near the blue toy, the gripper retreats empty while the toy stays on the table (wrist_cam, frames 309-324; overhead_cam confirms its unchanged tabletop location). The attempted acquisition does not advance placement.
- Recovery: Reopen, center the fingers around the toy's body, and verify acquisition with a short vertical lift before transporting it; no human intervention is needed.
- Severity: low
- Severity evidence: The toy remains on the tabletop with no visible damage or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The target is still accessible and no environmental resetting is required.

### Failure 2

- Frames: 389-510
- Categories: grasp
- Explanation: The second blue-toy acquisition again ends with an empty retreat (wrist_cam, frames 389-405; overhead_cam shows the blue toy remaining on the table). The robot subsequently travels to the plate and opens its empty fingers at frames 444-452, without delivering the toy.
- Recovery: Confirm that the blue toy is actually held before moving to the plate; return with open fingers and align around its body. No human intervention is needed.
- Severity: low
- Severity evidence: The unsuccessful attempt wastes motion but causes no visible damage.
- Resetability: immediate
- Resetability evidence: The blue toy remains available on the table for another attempt.

### Failure 3

- Frames: 560-636
- Categories: task_not_attempted
- Explanation: After approaching and adjusting near the blue toy, the robot remains beside it for a sustained interval without acquiring or transporting it (wrist_cam and overhead_cam, frames 560, 600 and 630).
- Recovery: Resume a centered acquisition rather than remaining beside the target; no human intervention is needed.
- Severity: low
- Severity evidence: Only task progress is prevented; no damage is visible.
- Resetability: immediate
- Resetability evidence: The scene remains usable without any object reset.

### Failure 4

- Frames: 641-780
- Categories: grasp
- Explanation: The fingers close beside the blue toy without securing it, and the robot moves away empty while the toy remains behind (wrist_cam, frames 641-665; overhead_cam). It again visits the plate and opens its fingers without adding the blue toy (wrist_cam, frames 700-724).
- Recovery: Reobserve the toy and grasp across its body, checking retention before leaving its location; no human intervention is needed.
- Severity: low
- Severity evidence: No visible damage results from this missed acquisition and empty transfer.
- Resetability: immediate
- Resetability evidence: The toy stays on the tabletop and can be reattempted without intervention.

### Failure 5

- Frames: 817-1316
- Categories: grasp
- Explanation: Acquisition becomes persistently unsuccessful: the blue toy remains outside a secure opposing-finger hold while repeated small motions displace it toward the table edge, interspersed with prolonged pauses (wrist_cam, frames 817-890, 948-998 and 1100-1247). Another closure at frames 1248-1258 is followed by separation without lifting the toy at frames 1259-1264. No blue-toy transfer occurs.
- Recovery: Stop the repeated edgeward motions, retract clear, and replan an opposing-finger grasp from a safe approach. Request human repositioning if a safe grasp cannot be made at the edge.
- Severity: low
- Severity evidence: The soft toy is displaced and progress stalls, but no damage is visible; proximity to the edge creates a fall possibility rather than evidence of damaging impact.
- Resetability: immediate
- Resetability evidence: Before the subsequent fall, the toy is still on the table; a changed grasp approach does not inherently require an environmental reset.

### Failure 6

- Frames: 1316-1334
- Categories: other
- Explanation: Continued motion beside the blue toy tips it over the table edge rather than placing it on the plate (wrist_cam, frames 1316-1322). It visibly falls and settles on the floor at frames 1323-1334. Secure possession before the fall is not established, so this is an accidental knock-off rather than a confirmed dropped grasp.
- Recovery: Stop table-edge attempts and have a person retrieve the toy after the robot is safely stationary, then reattempt from a clear tabletop position.
- Severity: low
- Severity evidence: The small soft toy falls onto an unobstructed floor area with no visible damage to it or surrounding objects.
- Resetability: minor_reset
- Resetability evidence: A person can retrieve the visible toy from the floor and return it to the table; no repair or complicated retrieval is indicated.