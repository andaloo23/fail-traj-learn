# Episode: C0719

## Episode annotation

- Language task: Put the orange into the purple container.
- Success label: failure
- Outcome evidence: The robot approaches the orange and closes its fingers around it at frames 104–110 (wrist_cam), but opens again and withdraws without lifting it at frames 116–138 (wrist_cam, right_base_cam). At frame 166, the orange remains on the tabletop outside the purple container (left_base_cam, right_base_cam). This is a visibly unsuccessful acquisition, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 116 | No |
| 116 | 139 | Yes |
| 139 | 167 | No |

## Failure annotations

### Failure 1

- Frames: 116-139
- Categories: grasp
- Explanation: After closing around the orange at frames 104–110, the fingers reopen starting at frame 116 and the gripper moves away empty through frame 138 while the orange remains on the tabletop (wrist_cam, left_base_cam, right_base_cam). The acquisition therefore fails; the images do not establish a secure hold or a subsequent drop.
- Recovery: Reposition the open gripper over the orange, align the fingers on opposing sides, close securely, and verify retention with a small lift before transporting it over the container; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The orange remains on the usable tabletop, with no visible damage or harmful disturbance to the container or nearby object (frames 138–139, left_base_cam and right_base_cam).
- Resetability: immediate
- Resetability evidence: The orange and container remain accessible and upright in the workspace; another acquisition attempt requires no environmental reset or human intervention.