# Episode: C0726_W01

## Episode annotation

- Language task: Pick up one object from the big bowl and put it inside the small box that is empty.
- Success label: failure
- Outcome evidence: Completion is unconfirmed in this window, not a confirmed failed transfer: frames 0 and 200 in top and left show the bowl contents and separate empty orange box; frames 248–322 in right show the gripper engaging the orange container in the bowl, but no placement occurs. By frames 329–349 in left and right, the large bowl is also visibly tilted during the interaction. The separate box remains empty in top at frame 349. Later episode context is unavailable, so this outcome is provisional.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 325 | No |
| 325 | 350 | Yes |

## Failure annotations

### Failure 1

- Frames: 325-350
- Categories: collision
- Explanation: During the interaction with the orange container, the robot also displaces and tips the large blue bowl instead of cleanly extracting an object: the disturbance becomes apparent at frame 325 in right and top, and the bowl is markedly tilted at frames 329–349 in right and left. This unintended contact disrupts the source arrangement. The exact contact mechanism is obscured, and neither a dropped object nor a completed failed grasp is established. The disturbance remains unresolved at the window boundary and may continue beyond it.
- Recovery: Stop pulling, gently lower and stabilize the bowl on the table, then separate the gripper from the rim and align to grasp one accessible object without catching the bowl; human intervention is needed only if the robot cannot safely restore the bowl.
- Severity: low
- Severity evidence: The bowl is tilted and its contents shift, but frames 335–349 in left and right show no visible breakage or spill outside the bowl and no concrete meaningful damage risk.
- Resetability: minor_reset
- Resetability evidence: The bowl needs to be returned to a stable upright position and the contents checked before another attempt; this appears to be a straightforward local reset, with no visible need for repair or difficult retrieval.