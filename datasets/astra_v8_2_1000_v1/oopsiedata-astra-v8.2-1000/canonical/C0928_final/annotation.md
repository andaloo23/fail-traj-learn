# Episode: C0928

## Episode annotation

- Language task: Close the oven.
- Success label: failure
- Outcome evidence: The oven door is open at frame 0 in image and left_ego_image. The robot approaches the door during frames 1–77, but then remains essentially stationary through frame 399. At frame 399, left_ego_image still shows the exposed oven interior and open door, corroborated by image; wrist_image shows the gripper beside the door edge. The oven is visibly left open, rather than completion merely being hidden or unconfirmed.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 78 | No |
| 78 | 400 | Yes |

## Failure annotations

### Failure 1

- Frames: 78-400
- Categories: task_not_attempted
- Explanation: Following the approach, the robot sustains essentially the same pose beside the open door from frame 78 through frame 399, without further closing progress. Comparisons of frames 78, 150, 250 and 399 in image, left_ego_image and wrist_image show the unchanged gripper/door arrangement and exposed interior. This extended stall does not advance the task; the images do not establish a mechanical cause or secure grasp.
- Recovery: Reassess the door edge and handle, reposition to establish controlled contact, and move the door along its hinge path toward closure while checking clearance and the final closed state. No human intervention is visibly required; if controlled motion cannot resume, request operator assistance rather than applying force blindly.
- Severity: low
- Severity evidence: The oven remains open, but no damage, displaced unrelated objects or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: The scene remains usable with the door accessible and objects undisturbed; another controlled closing attempt requires no visible environmental reset.