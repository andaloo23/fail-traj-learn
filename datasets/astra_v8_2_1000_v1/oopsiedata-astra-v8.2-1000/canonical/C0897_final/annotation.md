# Episode: C0897

## Episode annotation

- Language task: Pick up the spoon and place it into the box.
- Success label: success but suboptimal
- Outcome evidence: The spoon is initially lifted in frames 60–67 (wrist_left), but falls back onto the tabletop beside the box in frames 68–75 (ceiling, wrist_left, wrist_right). The robot reacquires and lifts it in frames 103–115, then releases it inside the blue box in frames 133–137 (wrist_right). It remains in the box after the gripper withdraws through frame 157 (ceiling). Completion follows one failed retention attempt; no damage or unrelated side effects are visible.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 68 | No |
| 68 | 76 | Yes |
| 76 | 158 | No |

## Failure annotations

### Failure 1

- Frames: 68-76
- Categories: grasp
- Explanation: After the spoon is visibly lifted and carried in frames 60–67 (wrist_left), it falls away from the gripper beginning at frame 68 and settles on the tabletop outside the box by frames 70–75 (ceiling, wrist_left). The empty gripper and separated spoon are also visible in wrist_right. Loss of retention interrupts the transfer.
- Recovery: Reapproach the spoon at its new tabletop position, secure its handle, verify retention with a small lift, and carry it over the box before releasing; no human intervention is needed.
- Severity: low
- Severity evidence: The spoon lands on the tabletop beside the box without visible damage, spill, or disruption to other objects.
- Resetability: immediate
- Resetability evidence: The spoon remains accessible on the tabletop and the box remains in place; another grasp can be attempted without environmental resetting or human intervention.