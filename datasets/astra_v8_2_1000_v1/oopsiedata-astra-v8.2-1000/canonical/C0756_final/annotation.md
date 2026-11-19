# Episode: C0756

## Episode annotation

- Language task: Pick up the blue rectangle and put it on the right side of the table.
- Success label: failure
- Outcome evidence: The blue rectangle remains beside the yellow block throughout the episode, including frames 0, 150 and 240 in left_base_cam and right_base_cam. At frames 43–52, wrist_cam shows the gripper closing beside the blue rectangle without acquiring it; frames 58–74 show withdrawal empty. Later approaches and repositioning do not produce a visible pickup or placement. This is a visibly unsuccessful acquisition, not merely an unconfirmed final placement.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 43 | No |
| 43 | 53 | Yes |
| 53 | 241 | No |

## Failure annotations

### Failure 1

- Frames: 43-53
- Categories: grasp
- Explanation: In wrist_cam at frames 43–50, the fingers close offset from the blue rectangle rather than enclosing it. At frames 50–52 the rectangle remains outside the grasp; subsequent reopening and empty withdrawal at frames 53–74 confirm unsuccessful acquisition. left_base_cam and right_base_cam show the target remaining on the table.
- Recovery: Reopen the gripper, align its fingers on opposite sides of the blue rectangle, descend to a suitable grasp height, and verify acquisition with a small lift before transporting it to the right side. No human intervention is visibly needed.
- Severity: low
- Severity evidence: The attempt fails to lift the target; no damage, toppling or harmful displacement is visible in wrist_cam or the base cameras.
- Resetability: immediate
- Resetability evidence: The blue rectangle remains accessible on the tabletop, and no environmental restoration or human intervention is needed before another aligned attempt.