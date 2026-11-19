# Episode: C0322_W04

## Episode annotation

- Language task: Place the toys on the plate with no collisions.
- Success label: failure
- Outcome evidence: Provisionally for this window, no toy is placed on the plate. overhead_cam shows the empty plate and toys outside it at frames 1050, 1185, 1280 and 1399. wrist_cam shows closure beside the beige toy at frames 1111–1121, subsequent movement without lifting the toy, and reopening at frames 1395–1399. This supports an unsuccessful acquisition, not just unconfirmed completion. No unwanted collision is clearly established. Earlier context beyond the two supplied preceding frames and later completion are unavailable.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 1050 | 1129 | No |
| 1129 | 1400 | Yes |

## Failure annotations

### Failure 1

- Frames: 1129-1400
- Categories: grasp
- Explanation: Following finger closure at frames 1111–1121, wrist_cam shows the gripper moving and changing orientation from frame 1129 onward while the beige toy remains outside the closed fingers on the tabletop, including frames 1165, 1185 and 1280. overhead_cam confirms that it remains beside the empty plate rather than being transferred. The robot continues small movements and pauses with no retained lift, then reopens at frames 1395–1399. Secure possession or a drop is not established. The failed acquisition cycle reaches the window boundary; subsequent recovery is unseen.
- Recovery: Open fully, move clear of the plate rim, and realign the fingers to enclose the beige toy's body; verify retention with a small lift before transporting it over the plate. No human intervention is visibly required.
- Severity: low
- Severity evidence: The toy remains on the tabletop and no damage, harmful displacement, or meaningful damage risk is visible in overhead_cam or wrist_cam.
- Resetability: immediate
- Resetability evidence: The toy and plate remain accessible and usable; another aligned acquisition can be attempted without an environmental or human reset.