# Episode: C0805

## Episode annotation

- Language task: push the button
- Success label: failure
- Outcome evidence: The yellow button remains on the mat while the robot moves above it without visibly reaching its surface (left, frames 0, 35, 65, 125, and 158). The fingertip overlaps the button in the wrist image at frames 125–127, but left shows separation; this projection does not establish a press. No button depression is visible before the robot withdraws, so the observed reaching behavior is unsuccessful, not a confirmed completed push.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 12 | No |
| 12 | 159 | Yes |

## Failure annotations

### Failure 1

- Frames: 12-159
- Categories: reaching
- Explanation: Beginning at frame 12, the robot moves away from its initial near-button alignment and repeatedly repositions above the workspace without descending to the button (left and wrist, frames 12–50). Further movements leave the end effector visibly separated from the button (left, frames 65–120). A later alignment brings the fingertip over the button in wrist at frames 125–127, but left still shows it above the surface; it then retreats again through frame 158 without a visible push.
- Recovery: Re-localize the button, align a suitable pressing surface directly above its center, and make a controlled downward approach followed by a press and withdrawal. No human intervention is visibly required.
- Severity: low
- Severity evidence: The button and surrounding mat remain undisturbed in left through frame 158; no collision, damage, or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: The button remains accessible in its original location, and no scene restoration or human intervention is needed before another attempt.