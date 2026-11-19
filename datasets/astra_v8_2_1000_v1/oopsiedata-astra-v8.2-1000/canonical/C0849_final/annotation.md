# Episode: C0849

## Episode annotation

- Language task: Remove the toy potato from the bowl.
- Success label: success but side effects
- Outcome evidence: The potato initially lies inside the bowl (frame 0, wrist_cam). An initial grasp fails, leaving it in the bowl (frames 97–101, wrist_cam), before a subsequent grasp lifts it (frames 147–153, right_base_cam and wrist_cam). During withdrawal, the bowl is also dragged across the table (frames 153–177, left_base_cam and right_base_cam). The potato is ultimately released onto the tabletop outside the bowl (frames 236–240, wrist_cam and left_base_cam), completing the task despite the failed attempt and bowl displacement.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 97 | No |
| 97 | 101 | Yes |
| 101 | 153 | No |
| 153 | 178 | Yes |
| 178 | 241 | No |

## Failure annotations

### Failure 1

- Frames: 97-101
- Categories: grasp
- Explanation: After the fingers close around the potato in frames 91–96, the potato escapes the closing fingers and remains in the bowl while the gripper moves slightly upward (frames 97–100, wrist_cam and right_base_cam). This acquisition does not remove the target; reopening begins at frame 101.
- Recovery: Reopen the fingers, align them around the potato at a more secure grasp depth, and retry with a small verification lift; no human intervention is needed.
- Severity: low
- Severity evidence: The potato remains safely in the bowl, with no visible damage or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The target remains accessible in the upright bowl, so another grasp can be attempted without environmental intervention.

### Failure 2

- Frames: 153-178
- Categories: collision
- Explanation: While holding the potato near the bowl rim, the robot withdraws laterally and the bowl moves along with it across the table (frames 153–176, left_base_cam and right_base_cam). The bowl separates from the withdrawing gripper around frames 177–178; this unintended dragging disrupts the scene rather than simply removing the potato.
- Recovery: Stop lateral pulling and lift the held potato clear of the rim before continuing away; restore the bowl to its original position if needed. Human intervention is not evidently necessary.
- Severity: low
- Severity evidence: The bowl is displaced but remains on the tabletop and settles upright; no breakage, spill, or other damage is visible.
- Resetability: minor_reset
- Resetability evidence: Returning the displaced bowl to its original tabletop position is a straightforward minor reset, with no repair or difficult retrieval required.