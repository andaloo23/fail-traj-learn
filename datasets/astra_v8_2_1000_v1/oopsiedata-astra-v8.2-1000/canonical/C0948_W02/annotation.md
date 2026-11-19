# Episode: C0948_W02

## Episode annotation

- Language task: find the hidden stuffed toy and put it in the bowl
- Success label: failure
- Outcome evidence: Completion is unconfirmed in this window: frames 350, 450, 550, and 699 in right and top show the green bowl remaining empty, while left and top show no discernible search, acquisition, or transfer. The robot remains essentially stationary throughout approximately 11.6 seconds. This is a provisional window outcome, with sustained inactivity rather than a visibly failed grasp; earlier context beyond frames 348–349 and later execution are unavailable.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 350 | 700 | Yes |

## Failure annotations

### Failure 1

- Frames: 350-700
- Categories: task_not_attempted
- Explanation: Across frames 350, 450, 550, 650, and 699 in left, right, and top, the grippers remain at the near edge of the workspace without discernible task-directed approach or interaction. The pink storage unit and green bowl remain unchanged, establishing sustained unproductive inactivity. Context frames 348–349 show the same pose, supporting continuity across the starting boundary independently of the prior prediction; inactivity may continue beyond frame 699, and its cause is not visible.
- Recovery: Begin a task-directed search, inspect the pink storage unit for the stuffed toy, verify its identity, then safely acquire and place it in the green bowl; no human environmental intervention is visibly needed.
- Severity: low
- Severity evidence: The visible consequence is lack of task progress; no damage, object displacement, or meaningful damage risk is observed.
- Resetability: immediate
- Resetability evidence: The environment remains unchanged and usable, so another attempt requires no physical reset or human repositioning.