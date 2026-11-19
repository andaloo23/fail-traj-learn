# Episode: C0949

## Episode annotation

- Language task: Pick up NIST rod and insert into corresponding hole on the NIST board.
- Success label: failure
- Outcome evidence: In side frames 0–12, the robot approaches the upright rod. In side and wrist frames 14–17, the rod tips and ends up lying on the board rather than securely acquired. The robot subsequently approaches the fallen rod in frames 18–26, but no completed pickup or insertion is visible. The initial acquisition visibly fails; completion of the subsequent attempt remains unconfirmed.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 14 | No |
| 14 | 18 | Yes |
| 18 | 27 | No |

## Failure annotations

### Failure 1

- Frames: 14-18
- Categories: grasp
- Explanation: During acquisition, the rod visibly tilts between the fingers in wrist frame 14, then falls onto the board in side frames 16–17. By frame 17, it lies separately from the gripper, establishing unsuccessful acquisition or retention rather than a completed pickup; secure possession before the fall is not established.
- Recovery: Reposition the open gripper around the fallen rod, acquire it securely, and then align it with the corresponding hole before insertion. No human intervention is visibly required.
- Severity: low
- Severity evidence: The rod falls onto the board and remains accessible in side frames 17–26; no damage or consequential disturbance to other objects is visible.
- Resetability: immediate
- Resetability evidence: The fallen rod remains on the accessible board surface, allowing another acquisition attempt without a necessary human or environmental reset.