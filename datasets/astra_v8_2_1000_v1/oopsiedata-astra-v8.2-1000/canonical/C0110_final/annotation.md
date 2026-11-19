# Episode: C0110

## Episode annotation

- Language task: remove the blue cloth from the yellow block
- Success label: failure
- Outcome evidence: In right_shoulder_cam, the gripper approaches the blue cloth and closes at frames 0–14, but subsequently moves away without carrying it (frames 32–58). The cloth remains draped over a raised shape at frame 69; the yellow block is not directly visible. This is a visibly unsuccessful cloth-acquisition attempt, not merely an unconfirmed completion at the recording boundary.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 15 | No |
| 15 | 70 | Yes |

## Failure annotations

### Failure 1

- Frames: 15-70
- Categories: grasp
- Explanation: After closing over the cloth at frames 12–14, the gripper begins withdrawing without lifting the cloth at frames 15–16 in right_shoulder_cam. It continues moving across and away from the cloth through frames 32–57, with only slight cloth displacement and no established retention. The visibly empty gripper opens at frame 58 and remains away from the still-draped cloth through frame 69; removal is not achieved.
- Recovery: Reopen and reposition the gripper around an accessible cloth edge or fold, acquire the fabric, and verify that it lifts with the gripper before pulling it clear of the block. No human intervention is visibly required.
- Severity: low
- Severity evidence: The cloth remains on the tabletop with no visible tearing, object damage, or other harmful consequence in right_shoulder_cam through frame 69.
- Resetability: immediate
- Resetability evidence: The cloth remains accessible for another acquisition attempt; no environmental restoration or human reset is visibly necessary.