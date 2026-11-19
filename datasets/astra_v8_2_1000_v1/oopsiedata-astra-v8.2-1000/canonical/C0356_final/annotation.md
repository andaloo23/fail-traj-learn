# Episode: C0356

## Episode annotation

- Language task: Pick up the yellow object in the bowl and put it next to the dark green fruit.
- Success label: failure
- Outcome evidence: The yellow object remains in the bowl throughout the episode, including frame 71 in right_base_cam and wrist_cam; no placement beside the dark green fruit occurs. The gripper approaches the bowl and then withdraws empty twice (frames 16–27 and 54–71, left_base_cam and wrist_cam), supporting visibly unsuccessful acquisition attempts rather than merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 20 | No |
| 20 | 27 | Yes |
| 27 | 58 | No |
| 58 | 72 | Yes |

## Failure annotations

### Failure 1

- Frames: 20-27
- Categories: grasp
- Explanation: Following the approach to the bowl at frames 16–19, the gripper lifts away empty during frames 20–26 in left_base_cam; wrist_cam shows the yellow object remaining inside the bowl. This withdrawal establishes a missed acquisition, without evidence of possession or dropping.
- Recovery: Reposition the open gripper directly around the yellow object, descend with clearance from the bowl, and verify acquisition before lifting; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The object remains in the upright bowl, with no visible damage or disruption to the surrounding scene.
- Resetability: immediate
- Resetability evidence: The bowl and target remain available in their original arrangement, so another acquisition attempt requires no environmental reset.

### Failure 2

- Frames: 58-72
- Categories: grasp
- Explanation: After another approach toward the bowl at frames 51–57, the gripper moves away empty during frames 58–71 in left_base_cam and right_base_cam. The yellow object remains in the bowl, also visible in wrist_cam, so the renewed attempt does not acquire or transfer it.
- Recovery: Return above the bowl, correct the gripper alignment around the yellow object, and confirm a secure grasp before transporting it beside the dark green fruit; no human intervention is visibly required.
- Severity: low
- Severity evidence: Only acquisition is prevented; the supplied views show no overturned objects, damage, or other harmful consequences.
- Resetability: immediate
- Resetability evidence: The target is still accessible in the upright bowl and the destination fruit remains on the table, allowing a retry without resetting the scene.