# Episode: C0060

## Episode annotation

- Language task: Move the hammer to the plate. Then, grasp the mushroom.
- Success label: success but suboptimal
- Outcome evidence: In image_primary, the gripper first closes near the hammer but lifts without it at frames 27–28. A subsequent attempt lifts the hammer at frames 40–43 and deposits it on the green plate at frames 56–60. The robot then closes around the mushroom at frames 83–84 and lifts it with the gripper at frame 85, visibly completing the ordered task after the earlier failed acquisition.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 27 | No |
| 27 | 29 | Yes |
| 29 | 86 | No |

## Failure annotations

### Failure 1

- Frames: 27-29
- Categories: grasp
- Explanation: In image_primary, after closing near the hammer at frames 25–26, the gripper rises empty at frames 27–28 while the hammer remains on the table. This establishes an unsuccessful acquisition; renewed approach begins at frame 29.
- Recovery: Reopen and realign the fingers around the hammer handle, close securely, and verify that the hammer follows a short lift before transferring it to the plate; no human intervention is needed.
- Severity: low
- Severity evidence: The hammer remains on the tabletop, with no visible damage or harmful disturbance to surrounding objects.
- Resetability: immediate
- Resetability evidence: The hammer remains accessible for another grasp, so no environmental reset or human intervention is required.