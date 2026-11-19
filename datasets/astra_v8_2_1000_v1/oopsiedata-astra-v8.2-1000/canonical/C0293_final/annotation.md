# Episode: C0293

## Episode annotation

- Language task: stack the cubes
- Success label: failure
- Outcome evidence: The robot acquires the green cube and moves it toward the tan cube (frames 113–168, wrist and right), leaving an apparent two-cube stack after release (frames 185–200, left and right). The purple cube remains separately on the table through frame 499 (right). Thus stacking all the cubes is not visibly completed; this is partial progress, followed by an observed unproductive interval, rather than a visibly collapsed stack.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 217 | No |
| 217 | 401 | Yes |
| 401 | 500 | No |

## Failure annotations

### Failure 1

- Frames: 217-401
- Categories: task_not_attempted
- Explanation: After approaching the remaining purple cube, the empty gripper moves away from the cubes and makes an extended excursion around and above the workspace without acquiring or stacking another cube (frames 217, 249, 281, 321 and 393, left, right and wrist). The cubes remain stationary during this interval. This sustained unproductive movement does not advance the remaining stacking task; no completed failed grasp or collision is established.
- Recovery: Return to a clear approach above the purple cube, align the fingers with opposing faces, grasp and verify retention, then place it centrally on the existing stack; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The interval delays completion, but no cube falls and no damage or meaningful damage risk is visible in left or right.
- Resetability: immediate
- Resetability evidence: The cubes remain available on the tabletop and the apparent partial stack remains standing; another task-directed attempt requires no environmental reset or human intervention.