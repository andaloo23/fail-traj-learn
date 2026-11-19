# Episode: C0782

## Episode annotation

- Language task: Pick up the stuffed animal and place it in the cardboard box.
- Success label: failure
- Outcome evidence: The stuffed animal begins beside the open box (frame 0, external and wrist). The robot visibly lifts it from the table at frames 600–606 (external), but subsequently carries it toward the right, away from the box (frames 683–695, 784–800 and 980–1000, external). At frame 1073, wrist still shows the animal at the gripper while external shows the box without the animal. Placement is not completed; this includes visibly wrong-direction transport, not merely an unconfirmed release.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 683 | No |
| 683 | 1074 | Yes |

## Failure annotations

### Failure 1

- Frames: 683-1074
- Categories: manipulation
- Explanation: After establishing control and lifting the animal (frames 600–606, external), the robot transports it increasingly rightward instead of toward the box on the left (frames 683–695, 784–800 and 893–900, external). It continues carrying it out of the external view at frames 980–1000, with wrist confirming continued retention through frame 1073. These movements and intervening holds do not advance placement in the box; no hidden cause is established.
- Recovery: Retain a secure grasp, relocate the box using the available views, and move the animal along a clear path over its opening before lowering and releasing it; no human intervention is visibly required.
- Severity: low
- Severity evidence: The animal remains held and no damage, drop or unwanted collision is visible; the observed consequence is failure to place it in the box.
- Resetability: immediate
- Resetability evidence: The box remains upright and undisturbed, and the animal remains at the gripper, so the robot can correct its transport without an environmental reset or human intervention.