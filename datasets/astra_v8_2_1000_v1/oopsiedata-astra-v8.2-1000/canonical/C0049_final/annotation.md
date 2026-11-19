# Episode: C0049

## Episode annotation

- Language task: Close the oven.
- Success label: failure
- Outcome evidence: The oven door is open initially (frame 0, image and left_ego_image). The robot approaches its handle, but spends a sustained interval nearly stationary beside the open door (frames 77–227, all three cameras). Later movements and slight door motion do not produce closure: the door still projects outward at frame 399 in image, with its inner surface visible in wrist_image. Completion is visibly absent, although the final ongoing attempt is not established as a completed failed acquisition.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 77 | No |
| 77 | 228 | Yes |
| 228 | 400 | No |

## Failure annotations

### Failure 1

- Frames: 77-228
- Categories: task_not_attempted
- Explanation: Following the approach, the gripper remains almost stationary beside the door handle for approximately 12.6 seconds without appreciable closing progress (frames 77, 120, 180 and 227, image and left_ego_image; wrist_image shows the largely unchanged finger-to-handle arrangement). This is sustained unproductive stalling rather than a brief alignment pause; the images do not establish its underlying cause or a secure grasp.
- Recovery: Reassess the handle alignment, establish a secure grasp or supported contact, and move the door along its closing arc while monitoring clearance and door motion. No human intervention is visibly required.
- Severity: low
- Severity evidence: The door remains open and task progress is delayed; no damage, displaced unrelated objects or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: The oven and surrounding objects remain in a usable state, so the robot can reposition and resume without an environmental reset or human assistance.