# Episode: C0158

## Episode annotation

- Language task: Open the drawer.
- Success label: failure
- Outcome evidence: The drawer remains closed throughout the observed episode: compare frames 0, 183, 273 and 399 in left_ego_image. wrist_image shows repeated finger closures near the silver handle followed by empty withdrawal, including frames 117–128 and 161–186. No drawer extension is visible, and the final frames show the gripper still near the cabinet rather than a completed opening.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 117 | No |
| 117 | 294 | Yes |
| 294 | 400 | Yes |

## Failure annotations

### Failure 1

- Frames: 117-294
- Categories: grasp
- Explanation: The robot repeatedly closes its fingers near the handle without securing it or moving the drawer. In wrist_image, the closure at frames 117–118 is followed by separation from the handle at frames 121–128; similar unsuccessful close-and-withdraw motions occur at frames 161–186, 214–235 and 255–274. These repetitive attempts do not establish useful handle control; left_ego_image shows the drawer remaining flush with the cabinet.
- Recovery: Withdraw slightly, realign the open fingers around the accessible middle of the handle, and verify secure engagement before pulling along the drawer's travel direction; no human intervention is visibly required.
- Severity: low
- Severity evidence: The attempts leave the drawer closed, with no visible damage or displacement of surrounding objects in image and left_ego_image.
- Resetability: immediate
- Resetability evidence: The cabinet and surrounding objects remain in place, so a corrected acquisition can be attempted without an environmental reset.

### Failure 2

- Frames: 294-400
- Categories: task_not_attempted
- Explanation: After the repeated misses, the robot remains near the cabinet with an open gripper and only small finger or pose changes, without another substantive acquisition or pull. Frames 294, 330, 370 and 399 in wrist_image and left_ego_image establish sustained lack of progress for the remainder of the episode; the recording ending alone is not evidence of abnormal termination.
- Recovery: Resume a deliberately realigned handle acquisition and verify engagement before pulling; if a reliable alignment cannot be obtained, request human assistance rather than continuing unproductive motions.
- Severity: low
- Severity evidence: This interval adds delay but shows no damage, displaced objects or other harmful consequences.
- Resetability: immediate
- Resetability evidence: No environmental change needs reversing; the robot can resume from a corrected approach without a human reset.