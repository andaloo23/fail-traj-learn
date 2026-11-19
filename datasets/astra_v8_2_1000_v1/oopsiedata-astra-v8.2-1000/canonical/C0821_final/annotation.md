# Episode: C0821

## Episode annotation

- Language task: pick up the bottle
- Success label: success but side effects
- Outcome evidence: In zed, the gripper approaches the bottle in frames 0–66, closes around it, and carries it away from the round tray in frames 80–121 while the bottle stays fixed relative to the gripper. However, pale granular contents stream from the open neck and scatter across the tray in frames 90–138. Frames 149–157 show the bottle returned toward the tray and the fingers opening. The tactile panel changes during acquisition around frames 67–69 and release around frames 149–151.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 90 | No |
| 90 | 139 | Yes |
| 139 | 158 | No |

## Failure annotations

### Failure 1

- Frames: 90-139
- Categories: manipulation
- Explanation: While the bottle remains held, pale grains begin appearing at its open neck around frame 90 in zed, followed by a sustained stream in frames 100–127 and a growing scatter on the tray in frames 128–138. The handling spills contents rather than simply picking up and retaining the bottle; no loss of the bottle itself is visible.
- Recovery: Stop the spilling motion and orient the held bottle with its opening upward before further transport, then place it securely on a stable surface. Human assistance may be needed to collect the spilled grains and refill the bottle.
- Severity: medium
- Severity evidence: zed frames 128–157 show substantial granular spillage requiring cleanup, but no visible breakage or damage; the visible spill is largely contained by the tray.
- Resetability: minor_reset
- Resetability evidence: Collecting the grains from the accessible tray and restoring the bottle contents is a straightforward reset; no repair or difficult retrieval is visibly required.