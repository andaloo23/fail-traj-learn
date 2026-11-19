# Episode: C1000

## Episode annotation

- Language task: Put the red object into the purple plastic bowl.
- Success label: failure
- Outcome evidence: The red object remains on the tabletop outside the purple bowl throughout the episode. Frames 158–173 show the gripper approaching closely above it in right_base_cam and wrist_cam; frames 174–218 show the gripper withdrawing empty while the object stays behind. At frame 240, left_base_cam and right_base_cam still show the red object outside the bowl. This is a visibly unsuccessful acquisition, not merely an unconfirmed placement; no damage or unrelated object displacement is visible.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 174 | No |
| 174 | 241 | Yes |

## Failure annotations

### Failure 1

- Frames: 174-241
- Categories: grasp
- Explanation: Following the close approach in frames 158–173, the gripper begins moving away without the red object at frame 174. Frames 180–218 in right_base_cam and wrist_cam make the increasing separation clear while the object remains on the table. The empty withdrawal does not accomplish acquisition or transport, and no renewed acquisition occurs before frame 240. The images do not establish the underlying cause of the miss.
- Recovery: Re-localize the red object, align the open fingers around its sides at an appropriate height, and retry acquisition; verify that it lifts with the gripper before transporting it over the bowl and releasing it. No human intervention is visibly needed.
- Severity: low
- Severity evidence: The object remains on the usable tabletop, with no visible damage, spill, or disturbance of the bowl or yellow object.
- Resetability: immediate
- Resetability evidence: The red object and bowl remain accessible and in usable positions; another attempt requires no visible environmental reset or human intervention.