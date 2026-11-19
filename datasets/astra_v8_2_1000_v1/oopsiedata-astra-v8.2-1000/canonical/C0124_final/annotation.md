# Episode: C0124

## Episode annotation

- Language task: Open the oven.
- Success label: success but suboptimal
- Outcome evidence: The oven begins closed (frame 0, image and left_ego_image). An initial partial opening at frames 147–150 is lost when the door returns closed at frame 151. After repositioning, the robot opens the door downward at frames 238–255; it remains fully open through frame 272, with the interior exposed in image and left_ego_image. No damage or displacement of unrelated objects is visible.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 150 | No |
| 150 | 152 | Yes |
| 152 | 273 | No |

## Failure annotations

### Failure 1

- Frames: 150-152
- Categories: grasp
- Explanation: After the door moves slightly outward at frames 147–149, the partial opening is lost at frames 150–151: the gripper moves away and the door returns flush with the oven rather than continuing downward (image and left_ego_image). This establishes unsuccessful retention of the handle during the opening attempt; the precise contact mechanics are obscured.
- Recovery: Reposition the gripper around the handle, establish a secure acquisition, and pull along the door’s downward opening arc while monitoring its motion; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The door returns closed without visible damage, appliance displacement, or disturbance of nearby objects.
- Resetability: immediate
- Resetability evidence: The oven remains upright and closed with its handle accessible, so another attempt requires no environmental reset or human intervention.