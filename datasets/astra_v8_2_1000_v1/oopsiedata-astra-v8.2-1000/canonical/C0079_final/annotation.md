# Episode: C0079

## Episode annotation

- Language task: Snug the pillow into the case.
- Success label: success but suboptimal
- Outcome evidence: The pillow starts separate from the case in frame 0 (ceiling, head_left, head_right). After an unsuccessful initial pickup, the robot moves it onto the case at frames 99–110 and progressively pulls the case around it. Frames 914–940 and 1009–1059 (ceiling, head_left, head_right) show the pillow seated within the case, with fabric around all sides and its white surface visible through the central opening already present in the empty case. Completion follows a failed grasp and lengthy fabric adjustments; no damage or unrelated side effects are visible.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 78 | No |
| 78 | 85 | Yes |
| 85 | 1060 | No |

## Failure annotations

### Failure 1

- Frames: 78-85
- Categories: grasp
- Explanation: After closing around the near end of the pillow at frames 74–78, the gripper withdraws empty at frames 79–84 while the pillow remains at its original location (ceiling, head_left, head_right); wrist_right also shows the fingers clear of the pillow. This completed acquisition attempt did not move or secure the target.
- Recovery: Reopen, realign around a thicker portion or accessible edge of the pillow, then close and verify retention with a short controlled lift before transfer; no human intervention is needed.
- Severity: low
- Severity evidence: The pillow remains on the tabletop, with no visible damage, fall or harmful contact.
- Resetability: immediate
- Resetability evidence: The pillow and case remain accessible in usable positions, allowing another grasp without environmental resetting or human assistance.