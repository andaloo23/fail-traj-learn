# Episode: C0761

## Episode annotation

- Language task: Snug the pillow into the case.
- Success label: success but suboptimal
- Outcome evidence: The pillow starts separate from the case (frame 0, ceiling and head_left), is positioned over it (frames 111–190, ceiling), and is progressively tucked under the case edges (frames 350–570, head_left and head_right). By frames 794–823, ceiling and head_left show the pillow seated within the case perimeter, with its white center visible through the opening and both grippers withdrawn. Completion follows a sustained interval without visible progress.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 611 | No |
| 611 | 650 | Yes |
| 650 | 824 | No |

## Failure annotations

### Failure 1

- Frames: 611-650
- Categories: task_not_attempted
- Explanation: The robot remains essentially stationary around the partly fitted pillow for approximately four seconds, without visibly advancing the remaining adjustment; compare frames 611, 630 and 649 in ceiling, head_left and wrist_right. Task-directed gripper movement resumes at approximately frame 650; the reason for the pause is not visible.
- Recovery: Resume a controlled adjustment of the remaining loose case edge while stabilizing the pillow, then release and inspect the fit; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The visible consequence is delay; the pillow and case remain on the work surface without observed damage.
- Resetability: immediate
- Resetability evidence: The environment remains in a usable intermediate state, so adjustment can resume without an environmental reset or human intervention.