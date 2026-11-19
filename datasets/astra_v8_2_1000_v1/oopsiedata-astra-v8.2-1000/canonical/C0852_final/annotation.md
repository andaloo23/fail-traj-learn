# Episode: C0852

## Episode annotation

- Language task: pick up the bottle
- Success label: success but side effects
- Outcome evidence: In zed, the gripper approaches and closes around the bottle across frames 0–67; the bottle then stays with the gripper as the blue support surface recedes across frames 80–130, supporting successful pickup. However, pale granular contents visibly stream from the bottle toward the blue surface beginning around frame 97, leaving a substantial pile visible in frames 150–171. The tactile panel changes around acquisition but does not independently establish the lift or the contents' identity.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 97 | No |
| 97 | 151 | Yes |
| 151 | 172 | No |

## Failure annotations

### Failure 1

- Frames: 97-151
- Categories: other
- Explanation: During the pickup, pale granular material visibly exits the held bottle in zed frames 97–150 and accumulates on the blue surface. This unintended emptying is a side effect of handling the bottle, not required by the pickup task; the images do not establish the contents' identity or a hidden mechanical cause.
- Recovery: Stop the spilling motion and orient the bottle with its opening upward while maintaining a secure grasp, then place it safely on a stable surface. Human assistance is appropriate to collect the spilled material and refill or secure the bottle before another attempt.
- Severity: medium
- Severity evidence: Zed frames 144–171 show a substantial accumulation of spilled material requiring cleanup; no breakage or lasting damage is visible.
- Resetability: minor_reset
- Resetability evidence: The visible material is accessible on the blue surface and appears to require straightforward collection and bottle resetting; no repair or difficult retrieval is visibly necessary.