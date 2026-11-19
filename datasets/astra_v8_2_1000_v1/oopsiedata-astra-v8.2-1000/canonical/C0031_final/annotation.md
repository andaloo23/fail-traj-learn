# Episode: C0031

## Episode annotation

- Language task: Put the red plastic ball into the bowl.
- Success label: failure
- Outcome evidence: The red ball starts outside the bowl at frame 0 in left_base_cam and right_base_cam. The gripper closes near the ball at frames 153–157 in wrist_cam, then opens and withdraws without it at frames 158–177. At frame 199, both base cameras and wrist_cam still show the red ball on the table outside the bowl. This is a visibly unsuccessful acquisition, not merely unconfirmed placement.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 158 | No |
| 158 | 200 | Yes |

## Failure annotations

### Failure 1

- Frames: 158-200
- Categories: grasp
- Explanation: After closing near the red ball at frames 153–157, the gripper opens at frames 158–160 in wrist_cam without securing it. It subsequently moves away empty, while left_base_cam and right_base_cam show the ball remaining on the tabletop at frames 167–199. No transport into the bowl occurs; the images do not establish the underlying cause of the failed acquisition.
- Recovery: Reposition the open gripper around the ball, adjust alignment and grasp height, close securely, and verify possession with a short lift before transporting it over the bowl and releasing. No human intervention appears necessary.
- Severity: low
- Severity evidence: The ball remains on the usable tabletop, and no damage, spill, or harmful disturbance is visible in the three camera views through frame 199.
- Resetability: immediate
- Resetability evidence: The ball and bowl remain accessible and upright in their working area; another acquisition attempt requires no environmental reset or human intervention.