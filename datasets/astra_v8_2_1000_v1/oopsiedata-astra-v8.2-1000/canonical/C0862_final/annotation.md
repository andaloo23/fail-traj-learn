# Episode: C0862

## Episode annotation

- Language task: press the stapler
- Success label: failure
- Outcome evidence: The stapler remains on the table without a visibly completed press. The left and right views show the hand repeatedly repositioning beside and above it rather than depressing its top (frames 57, 153, 217, 329, 353 and 449). The wrist view shows the stapler remaining separated from the hand during the large intervening movements and at frame 499. Completion is unconfirmed; the visible local failures are unsuccessful reaching/repositioning, not a demonstrated failure of the stapler mechanism.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 57 | No |
| 57 | 291 | Yes |
| 291 | 353 | No |
| 353 | 500 | Yes |

## Failure annotations

### Failure 1

- Frames: 57-291
- Categories: reaching
- Explanation: Following the initial approach, the hand moves around and away from the stapler without reaching its pressing surface. The wrist view shows the target shifting to the side at frames 65 and 129–137, then leaving the view during withdrawal at frames 201–217; left and right show it remaining untouched on the table. This extended repositioning does not produce a press and ends when renewed approach begins at frame 291.
- Recovery: Re-localize the stapler, align a suitable gripper contact surface directly above its top, and approach vertically with controlled force; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The attempt makes no visible change to the stapler or surrounding objects, and no damage or meaningful damage risk is established.
- Resetability: immediate
- Resetability evidence: The stapler remains upright and accessible on the table; another approach requires no environmental reset.

### Failure 2

- Frames: 353-500
- Categories: reaching
- Explanation: After approaching near the stapler at frames 329–348, the robot again moves away without a visible press. In wrist, separation increases from frame 353 through frames 369–401, followed by further off-target repositioning through frame 499; left and right show the stapler staying in place. No contact-driven depression is established, so this is an unsuccessful reach rather than a supported post-contact manipulation failure.
- Recovery: Stop the off-target repositioning, re-establish the stapler's top-surface location, and execute a controlled downward press from directly above it; no human intervention is visibly needed.
- Severity: low
- Severity evidence: Only task completion is prevented; no object displacement, breakage or other harmful consequence is visible.
- Resetability: immediate
- Resetability evidence: The scene remains usable and the stapler remains accessible, allowing a corrected attempt without human resetting.