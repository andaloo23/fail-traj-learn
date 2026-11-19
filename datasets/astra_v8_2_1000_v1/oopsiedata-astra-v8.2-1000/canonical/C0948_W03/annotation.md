# Episode: C0948_W03

## Episode annotation

- Language task: find the hidden stuffed toy and put it in the bowl
- Success label: failure
- Outcome evidence: Completion is unconfirmed in this window: frames 700, 800, 900, 1000, and 1049 in right and top show the green bowl empty, while left and top show no discernible search, acquisition, or transfer. The robot remains essentially stationary for approximately 11.6 seconds, establishing sustained inactivity rather than a failed grasp. This outcome is provisional; earlier context beyond frames 698–699 and later execution are unavailable.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 700 | 1050 | Yes |

## Failure annotations

### Failure 1

- Frames: 700-1050
- Categories: task_not_attempted
- Explanation: Throughout frames 700–1049 in left, right, and top, the grippers remain near the front of the workspace without discernible task-directed interaction; the pink storage unit, bowl, and other tabletop objects remain unchanged. This sustained inactivity does not advance finding or placing the toy. Context frames 698–699 visibly show the same pose, supporting continuity across the starting boundary independently of the prior label. The inactivity may continue beyond this window; its cause is not visible.
- Recovery: Begin a task-directed search, inspect the pink storage unit and other plausible hiding locations, verify the stuffed toy's identity, then safely grasp it and place it in the bowl; no human environmental intervention is visibly needed.
- Severity: low
- Severity evidence: The observed consequence is lack of task progress, with no visible damage, displacement, or meaningful risk of damage.
- Resetability: immediate
- Resetability evidence: The workspace remains unchanged and usable; another attempt requires no visible physical reset or human repositioning.