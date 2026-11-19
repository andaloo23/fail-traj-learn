# Episode: C0968

## Episode annotation

- Language task: Open the oven.
- Success label: failure
- Outcome evidence: The oven door remains closed from frame 0 through frame 399 in left_ego_image, corroborated by image. The robot initially repositions near the oven, but then spends most of the episode hovering with only small adjustments (frames 35–399, left_ego_image and wrist_image). No door-opening motion is visible; this is an observed lack of progress with sustained stalling, rather than merely an opening action whose completion falls outside the recording.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 35 | No |
| 35 | 400 | Yes |

## Failure annotations

### Failure 1

- Frames: 35-400
- Categories: task_not_attempted
- Explanation: After the initial repositioning, the gripper remains nearly stationary near the oven for a prolonged interval (frames 35, 100, 180 and 239, left_ego_image and wrist_image). Small subsequent adjustments around frames 240–285 do not produce visible handle acquisition or door motion, and hovering continues through frame 399. The closed door in image and left_ego_image establishes that this sustained inactivity does not advance the task; no hidden cause or secure grasp is established.
- Recovery: Reassess the handle position, align the gripper for a secure acquisition, and then pull along the door's opening path while monitoring clearance and door movement. No human intervention is visibly required.
- Severity: low
- Severity evidence: The task remains incomplete, but no damage, displaced unrelated objects, or meaningful damage risk is visible through frame 399.
- Resetability: immediate
- Resetability evidence: The oven remains closed and the surrounding objects remain in place; another attempt can begin without an environmental reset or human intervention.