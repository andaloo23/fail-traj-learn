# Episode: C0750

## Episode annotation

- Language task: Open the oven.
- Success label: success but suboptimal
- Outcome evidence: The oven is initially closed (frame 0, image and left_ego_image). An initial withdrawal leaves the door closed and the gripper empty (frames 80–85, image and left_ego_image), followed by another approach. The door subsequently swings down through frames 111–132 and remains open at frame 150 (image and left_ego_image). No damage or displacement of unrelated objects is visible.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 77 | No |
| 77 | 86 | Yes |
| 86 | 151 | No |

## Failure annotations

### Failure 1

- Frames: 77-86
- Categories: grasp
- Explanation: After positioning at the oven handle, the gripper withdraws outward without carrying the handle or opening the door (frames 77–85, image and left_ego_image). By frames 82–85 it is visibly separated from the still-closed door, establishing an unsuccessful acquisition; the exact contact mechanics are unclear.
- Recovery: Return to the handle, align the fingers around it, establish a secure grasp, and pull along the door’s opening arc; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The attempt leaves the oven closed, with no visible damage or disturbance of nearby objects (frame 85, image and left_ego_image).
- Resetability: immediate
- Resetability evidence: The handle and surrounding scene remain available for another attempt without environmental resetting or human intervention.