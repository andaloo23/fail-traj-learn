# Episode: C0393

## Episode annotation

- Language task: Put the spoon in the drawer.
- Success label: failure
- Outcome evidence: The robot acquires and lifts the wooden spoon (frames 70–100, image and wrist_image), then carries it toward the open drawer. At frames 198–203, image and wrist_image show the spoon leaving the gripper and falling outside the drawer. It rests on the tabletop at frames 206–207 in image and left_ego_image, establishing a visibly failed placement rather than merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 198 | No |
| 198 | 208 | Yes |

## Failure annotations

### Failure 1

- Frames: 198-208
- Categories: manipulation
- Explanation: After successfully transporting the spoon, the robot releases it without placing it inside the drawer. The spoon begins leaving the gripper at frame 198 in wrist_image, falls outside the drawer at frames 199–203 in image, and settles on the table by frames 206–207 in image and left_ego_image. The visible placement fails; the images do not establish a hidden cause.
- Recovery: Reacquire the spoon from the tabletop, align it fully within the open drawer, lower it into the drawer, and release only after confirming clearance and support; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The spoon falls onto the tabletop and remains accessible, with no visible damage or disturbance to other objects.
- Resetability: immediate
- Resetability evidence: The spoon is on the usable tabletop and the drawer remains open, allowing another acquisition and placement attempt without environmental intervention.