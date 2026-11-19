# Episode: C0003

## Episode annotation

- Language task: Open the oven.
- Success label: failure
- Outcome evidence: The oven door is closed at frame 0 in left_ego_image. The robot approaches and aligns its gripper near the door handle through frames 100–203 in image and wrist_image, but the door remains closed through frame 320 in left_ego_image. The final prolonged near-static interaction shows no opening progress; secure handle acquisition is not established by the images.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 204 | No |
| 204 | 321 | Yes |

## Failure annotations

### Failure 1

- Frames: 204-321
- Categories: task_not_attempted
- Explanation: After approaching the handle, the robot remains in essentially the same near-door configuration with only small adjustments for approximately ten seconds, without opening the door. Compare frames 204, 240, 280 and 320 in image, left_ego_image and wrist_image. This is sustained unproductive stalling following a discernible task attempt, not evidence of a particular grasp or mechanical failure.
- Recovery: Reassess the handle position and finger placement, reposition to establish a verified handle grasp, then pull along the door's opening path while monitoring door movement; stop and request human inspection if resistance prevents opening. No human intervention is visibly required at this stage.
- Severity: low
- Severity evidence: The door remains closed, with no visible damage, displacement of unrelated objects or other harmful consequence.
- Resetability: immediate
- Resetability evidence: The oven and surrounding objects remain in their original usable state; the robot can reposition and reattempt without an environmental reset or demonstrated need for human intervention.