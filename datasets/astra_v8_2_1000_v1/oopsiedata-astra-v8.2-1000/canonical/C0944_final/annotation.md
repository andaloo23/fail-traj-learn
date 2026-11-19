# Episode: C0944

## Episode annotation

- Language task: pick up the bottle
- Success label: success but side effects
- Outcome evidence: In zed, the gripper approaches the bottle at frames 0–65 and retains it while moving it clear of the round tray at frames 85–105; the bottle remains held through frame 172. The tactile panel shows a sustained contact-pattern change from approximately frame 66 onward. However, zed frames 106–152 show light-colored granular contents streaming from the bottle toward the tray, with scattered contents clearly visible at frames 150–172.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 106 | No |
| 106 | 153 | Yes |
| 153 | 173 | No |

## Failure annotations

### Failure 1

- Frames: 106-153
- Categories: other
- Explanation: While the bottle remains held, light-colored granular material visibly streams from its opening in zed frames 106–152 and accumulates on the round tray, clearly visible by frames 150–153. This is an unintended spill during pickup, not a failed acquisition; the images do not establish why the contents were not secured.
- Recovery: Keep the bottle securely supported and orient its opening upward to stop further spilling, then place it safely down. Human assistance may be needed to collect and refill the spilled contents and secure the opening before another pickup.
- Severity: low
- Severity evidence: The visible consequence is dry granular material scattered onto the tray; no breakage, equipment damage, or meaningful damage risk is established.
- Resetability: minor_reset
- Resetability evidence: Collecting the material from the accessible tray and restoring the bottle contents requires a straightforward cleanup/refill; no repair or difficult retrieval is visibly necessary.