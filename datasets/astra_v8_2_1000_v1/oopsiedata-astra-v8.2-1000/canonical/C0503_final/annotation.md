# Episode: C0503

## Episode annotation

- Language task: Remove the fruit from the plastic bowl.
- Success label: failure
- Outcome evidence: The green and yellow fruit remain in the bowl after unsuccessful acquisitions (wrist_cam, frames 49 and 95–121). left_base_cam and right_base_cam show the gripper withdrawing without fruit at frames 89–150. The robot subsequently returns toward the bowl, but fruit is still inside at frame 240 in wrist_cam. Earlier attempts visibly fail; the final attempt remains unfinished, with no confirmed removal.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 31 | No |
| 31 | 44 | Yes |
| 44 | 81 | No |
| 81 | 152 | Yes |
| 152 | 241 | No |

## Failure annotations

### Failure 1

- Frames: 31-44
- Categories: grasp
- Explanation: After closing near the green fruit at frames 25–30, the gripper retreats without lifting it from the bowl during frames 31–43 (wrist_cam; left_base_cam and right_base_cam). The subsequent opening and view at frame 49 confirm that the fruit remains in the bowl rather than being acquired.
- Recovery: Open the fingers, realign them around the fruit with adequate clearance, and retry while verifying possession before withdrawing; human intervention is not needed.
- Severity: low
- Severity evidence: The attempt does not remove the fruit; no damage, spill, or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: The bowl remains upright and the fruit remains accessible inside it, allowing another attempt without environmental intervention.

### Failure 2

- Frames: 81-152
- Categories: grasp
- Explanation: Following another closure at frames 65–70, the robot lifts and withdraws an empty gripper starting at frame 81, leaving both fruit in the bowl (wrist_cam, frames 81–121; left_base_cam and right_base_cam, frames 89–150). It continues away empty until opening the fingers for another approach at frame 152.
- Recovery: Return with open fingers, adjust the grasp position to surround one fruit securely, and confirm that it lifts with the gripper before moving away; no human intervention is needed.
- Severity: low
- Severity evidence: The fruit remains in the upright bowl, with no visible damage or harmful displacement.
- Resetability: immediate
- Resetability evidence: No cleanup or object replacement is required; the robot can reapproach the fruit directly.