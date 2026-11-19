# Episode: C0194

## Episode annotation

- Language task: Put the plastic hot dog into the bowl.
- Success label: failure
- Outcome evidence: The hot dog remains on the tabletop outside the bowl from frame 0 through frame 240 in left_base_cam and right_base_cam. wrist_cam shows repeated approaches and withdrawals without visible acquisition; the final withdrawal at frames 225–240 leaves the target behind. The observed task is visibly incomplete, rather than merely hidden by an occluded placement.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 67 | No |
| 67 | 100 | Yes |
| 100 | 166 | No |
| 166 | 241 | Yes |

## Failure annotations

### Failure 1

- Frames: 67-100
- Categories: reaching
- Explanation: After approaching the hot dog, the robot backs away without reaching it at frames 67–74, then remains above the workspace through frame 99. wrist_cam shows the target receding from the open fingers; left_base_cam and right_base_cam confirm that it stays on the table. No completed grasp or contact is established.
- Recovery: Reposition the open gripper over the hot dog's center, descend until the fingers straddle it, and acquire it before transferring it to the bowl; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The unsuccessful approach leaves the objects undisturbed, with no visible damage or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The hot dog and bowl remain accessible in their original positions, so another approach requires no environmental reset.

### Failure 2

- Frames: 166-241
- Categories: reaching
- Explanation: Following another approach, the gripper moves back from the hot dog at frames 166–171, makes small back-and-forth movements without reaching it through frame 224, and withdraws farther at frames 225–240. wrist_cam shows continued separation from the target, while left_base_cam and right_base_cam show no target displacement or transfer. This is an unsuccessful pre-contact approach, not an established failed grasp.
- Recovery: Reassess the target-to-gripper alignment and make a corrected approach that places the fingers around the hot dog, then verify acquisition before lifting and placing it in the bowl; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The task remains unfinished, but no object damage, collision, or disruptive side effect is visible.
- Resetability: immediate
- Resetability evidence: The target remains on the unobstructed tabletop beside the upright bowl; no cleanup or object repositioning is required to retry.
