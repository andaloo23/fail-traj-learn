# Episode: C0202

## Episode annotation

- Language task: put the corn in the pot
- Success label: failure
- Outcome evidence: In right_shoulder_cam, the robot lifts the corn in frames 33–40 and carries it toward the pot in frames 49–69. After release, the corn falls outside the pot in frame 70 and moves toward the foreground table edge in frames 71–74; the pot remains empty. This is a visibly failed placement, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 70 | No |
| 70 | 75 | Yes |

## Failure annotations

### Failure 1

- Frames: 70-75
- Categories: manipulation
- Explanation: Following established control and transport of the corn, the placement fails: right_shoulder_cam frame 70 shows the open gripper and corn falling outside the pot. In frames 71–74, the corn moves across the foreground tabletop rather than remaining inside the pot. The images do not establish the precise release or contact dynamics.
- Recovery: Reacquire the corn if it remains safely supported and reachable, center it within the pot opening, and lower it before releasing. If its position near the table edge prevents safe acquisition, a person should reposition it first.
- Severity: low
- Severity evidence: The corn ends outside the pot on the visible foreground tabletop, with no visible damage, spill, or disruption to other objects; falling off the table is not established.
- Resetability: immediate
- Resetability evidence: No environmental damage or required cleanup is visible, so another acquisition can be attempted without a demonstrated need for human reset; safe reachability at the partially cropped foreground position remains uncertain.