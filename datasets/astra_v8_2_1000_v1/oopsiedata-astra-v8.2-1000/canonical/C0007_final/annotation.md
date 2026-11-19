# Episode: C0007

## Episode annotation

- Language task: Pick up the pink plastic bowl and move it towards the center of the table.
- Success label: success but side effects
- Outcome evidence: In left_base_cam and right_base_cam, the robot acquires the bowl around frames 142–156 and lifts and carries it inward during frames 157–168; by frame 240 it is closer to the table center than at frame 0. Release is not shown, but the requested pickup and movement are visible. Execution includes sustained hovering at frames 60–96 and displacement of the unrelated green object during frames 195–202, visible especially in wrist_cam.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 60 | No |
| 60 | 97 | Yes |
| 97 | 195 | No |
| 195 | 203 | Yes |
| 203 | 241 | No |

## Failure annotations

### Failure 1

- Frames: 60-97
- Categories: task_not_attempted
- Explanation: After approaching and adjusting above the bowl, the empty gripper remains essentially stationary for approximately 3.7 seconds without acquiring it or advancing the task; compare frames 60, 78 and 96 in left_base_cam, right_base_cam and wrist_cam. Task-directed approach resumes at frame 97.
- Recovery: Resume alignment with the bowl rim and perform a controlled acquisition; no human intervention is visibly needed.
- Severity: low
- Severity evidence: This interval delays completion without visible damage or disturbance to the scene.
- Resetability: immediate
- Resetability evidence: The bowl remains upright and accessible, and no environmental reset is required.

### Failure 2

- Frames: 195-203
- Categories: collision
- Explanation: While the robot moves the held bowl beside the unrelated green object, that object visibly turns and shifts away during frames 195–202 in wrist_cam, with its changed position also visible in right_base_cam. This unintended disturbance does not advance the bowl-moving task; the exact contact point is partly obscured.
- Recovery: Move the bowl along a path with clearance from the green object and place it securely; restore the green object's position if required. No human intervention is necessarily needed.
- Severity: low
- Severity evidence: The green object is displaced on the tabletop but remains on it; no breakage, spilling or other damage is visible.
- Resetability: minor_reset
- Resetability evidence: Returning the displaced green object to its previous position is a straightforward minor reset; no repair or difficult retrieval is indicated.