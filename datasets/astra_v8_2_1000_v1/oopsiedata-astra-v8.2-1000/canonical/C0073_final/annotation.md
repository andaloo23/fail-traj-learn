# Episode: C0073

## Episode annotation

- Language task: Move the left stuffed toy to the largest bowl.
- Success label: failure
- Outcome evidence: In image_primary frame 0, the left toy is blue and white, and the largest bowl is the central white bowl. The robot instead repeatedly handles the pink toy on the right (frames 12–22, 41–48, and 60–71). At frame 90, the blue-and-white toy remains in its original tabletop position and the white bowl remains empty. This is visible wrong-object behavior, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 8 | No |
| 8 | 24 | Yes |
| 24 | 38 | No |
| 38 | 91 | Yes |

## Failure annotations

### Failure 1

- Frames: 8-24
- Categories: sequencing_semantic, grasp
- Explanation: In image_primary frames 8–19, the gripper approaches and closes around the right pink toy rather than the left blue-and-white toy. It briefly lifts the pink toy in frames 20–21, but the toy falls back onto the table by frame 22 as the gripper withdraws empty. Both the wrong-object selection and failed retention are visible.
- Recovery: Leave the pink toy safely on the table, identify the left blue-and-white toy, and align the gripper around its body before lifting toward the white bowl; no human intervention is needed.
- Severity: low
- Severity evidence: The soft toy falls a short distance onto the tabletop; no damage or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: The intended toy and bowl remain accessible and unchanged, so another task attempt requires no environmental reset.

### Failure 2

- Frames: 38-91
- Categories: sequencing_semantic, grasp
- Explanation: After moving toward the left toy in image_primary frames 24–37, the robot returns to the pink toy at frame 38 and repeatedly manipulates that wrong object. A lift in frame 47 ends with the toy back on the table and the gripper empty at frame 48. The robot subsequently carries it toward the white bowl in frames 61–70, releases it outside the bowl at frame 71, and approaches it again through frame 90. The requested blue-and-white toy remains untouched throughout.
- Recovery: Stop retrying the pink toy, withdraw clear of both toys, and grasp the blue-and-white toy on the left; carry it over the white bowl and release only when positioned inside its opening. No human intervention is visibly required.
- Severity: low
- Severity evidence: The unintended toy is displaced and dropped onto the tabletop, but no damage, spill, or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: Both toys remain reachable on the table and the largest bowl remains usable; the intended task can be reattempted without human resetting.