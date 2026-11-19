# Episode: C0265_W06

## Episode annotation

- Language task: find the cube under the green bowl
- Success label: failure
- Outcome evidence: Completion is unconfirmed in this observed window: the green bowl remains inverted and no cube is uncovered (left and top, frames 1750, 1850, 1950 and 1999). Initial sustained inactivity is followed by intermittent repositioning toward the bowl, without a visible completed grasp or lift; right also shows no acquisition. This is a provisional window outcome, not evidence of a failed grasp or abnormal termination. Earlier context beyond frames 1748–1749 is unavailable, and no subsequent execution is shown.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 1750 | 1845 | Yes |
| 1845 | 2000 | No |

## Failure annotations

### Failure 1

- Frames: 1750-1845
- Categories: task_not_attempted
- Explanation: The robot remains separated from the inverted bowl for approximately 3.2 seconds, with slight positional drift but no discernible approach, contact or uncovering action (left, right and top, frames 1750, 1800 and 1844). This sustained inactivity does not advance finding the cube. Frames 1748–1749 show the same configuration, consistent with continuity across the window boundary, but the earlier duration cannot be independently verified here. At frame 1845, repositioning begins, bringing the left gripper closer to the bowl by frame 1850 (left and top), so that preparation is excluded from the failure.
- Recovery: Resume a task-directed approach, align for a secure bowl grasp, lift the bowl clear and inspect underneath for the cube; no human intervention is visibly needed.
- Severity: low
- Severity evidence: Progress is delayed, but the bowl and surrounding scene remain undisturbed, with no visible damage or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: No environmental change needs undoing; the robot can resume the attempt without human resetting.