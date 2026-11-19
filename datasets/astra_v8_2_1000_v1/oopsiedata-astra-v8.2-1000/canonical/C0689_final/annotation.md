# Episode: C0689

## Episode annotation

- Language task: Close the oven.
- Success label: failure
- Outcome evidence: The oven door is open at frame 0 in image and left_ego_image. The robot approaches the door and positions its gripper along its outer edge during frames 30–170, with the door panel also visible close to the gripper in wrist_image. At frames 174–237, the door remains extended outward and the oven interior remains exposed in left_ego_image; sustained positioning at the door does not achieve closure. This is visibly unsuccessful closing behavior, not merely an unseen final latch.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 174 | No |
| 174 | 238 | Yes |

## Failure annotations

### Failure 1

- Frames: 174-238
- Categories: manipulation
- Explanation: After engaging and slightly repositioning the door, the robot remains at its outer edge without completing the closing rotation. Frames 174, 200, and 237 in image and left_ego_image show the door still open, while wrist_image shows the gripper maintained against the door panel with only small adjustments. This sustained post-contact behavior does not advance closure; the images do not establish why progress stops.
- Recovery: Reassess the door hinge and contact geometry, reposition the gripper to securely support the outer edge or handle, and guide the door upward along its closing arc before verifying closure. Human intervention is not visibly required; if resistance prevents motion, stop and request inspection rather than force the door.
- Severity: low
- Severity evidence: The oven remains open, but no damage, displaced unrelated objects, or concrete damage hazard is visible.
- Resetability: immediate
- Resetability evidence: The door and surrounding scene remain usable; the robot can reposition and reattempt without an environmental reset or visible need for human intervention.