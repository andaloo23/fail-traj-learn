# Episode: C0530

## Episode annotation

- Language task: Close the oven.
- Success label: failure
- Outcome evidence: In left_ego_image, the initially open door (frame 0) rises to an apparently closed position around frames 80–99, but opens again by frame 114. Subsequent lifting does not produce a lasting closure: the door lowers again during frames 218–240 and remains open at frame 336. image corroborates the repeated arm movements at the oven. This is a visibly unsuccessful closing episode, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 100 | No |
| 100 | 115 | Yes |
| 115 | 154 | No |
| 154 | 201 | Yes |
| 201 | 218 | No |
| 218 | 241 | Yes |
| 241 | 337 | Yes |

## Failure annotations

### Failure 1

- Frames: 100-115
- Categories: manipulation
- Explanation: After raising the door to an apparently closed position, the robot fails to maintain closure: left_ego_image shows the door rotating outward and downward from frame 100 until it is open at frame 114. The images establish reversed progress but do not establish whether this resulted from release, slipping, or commanded motion.
- Recovery: Reposition at the handle, raise the door fully, and verify that it stays closed before withdrawing; no human intervention is visibly required.
- Severity: low
- Severity evidence: The door reopens without visible damage, displaced contents, or damage to surrounding objects.
- Resetability: immediate
- Resetability evidence: The oven and handle remain accessible, so another closing attempt requires no environmental reset.

### Failure 2

- Frames: 154-201
- Categories: task_not_attempted
- Explanation: Following another partial lift, the robot remains nearly stationary beside the incompletely closed door for roughly four seconds; left_ego_image frames 154, 175, and 200 show no meaningful closing progress, corroborated by image.
- Recovery: Resume a controlled closing motion with suitable handle contact and verify full closure; no human intervention is visibly required.
- Severity: low
- Severity evidence: The visible consequence is delay and incomplete closure, with no observed damage.
- Resetability: immediate
- Resetability evidence: Nothing needs to be restored or cleared before continuing the attempt.

### Failure 3

- Frames: 218-241
- Categories: manipulation
- Explanation: After renewed upward movement during frames 201–217, the door again rotates downward rather than completing closure. left_ego_image frames 218, 230, and 240 show the increasing opening while the robot remains at the door; image corroborates the descending arm motion.
- Recovery: Re-establish effective handle contact, guide the door upward through its closing arc, and confirm that it remains shut before releasing; no human intervention is visibly required.
- Severity: low
- Severity evidence: Closing progress is lost, but no breakage, spill, or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: The reopened door remains accessible and the surrounding scene requires no reset.

### Failure 4

- Frames: 241-337
- Categories: task_not_attempted
- Explanation: The robot remains at the open door with only small adjustments and no meaningful closing progress for the remainder of the episode. left_ego_image frames 241, 280, 320, and 336 show the open oven, while image and wrist_image corroborate the largely unchanged robot position.
- Recovery: Reassess the handle alignment and execute a controlled upward closing motion rather than continuing to hold the same position; no human intervention is established as necessary.
- Severity: low
- Severity evidence: The task remains unfinished and time is spent without progress; no physical damage is visible.
- Resetability: immediate
- Resetability evidence: The oven remains usable and accessible, with no displaced objects or cleanup needed before retrying.
