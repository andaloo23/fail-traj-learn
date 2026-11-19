# Episode: C0848

## Episode annotation

- Language task: Clean the table by placing the cans in the upper tray and the bowls in the tray on the right.
- Success label: failure
- Outcome evidence: In base_image, frame 0 shows two cans and two bowls outside the trays. The robot places the pink/yellow can in the upper blue tray by frames 358–367, but fails to acquire the green can on two attempts. At frame 464, the green can remains on the table and both bowls remain outside the empty right-hand red tray. Thus the observed task is incomplete, with visible failed acquisitions rather than merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 135 | No |
| 135 | 268 | Yes |
| 268 | 430 | No |
| 430 | 465 | Yes |

## Failure annotations

### Failure 1

- Frames: 135-268
- Categories: grasp
- Explanation: In base_image, frames 135–158 show the green can emerging outside the gripper after the acquisition attempt, displaced toward the bottom of the image. By frames 168–175 the gripper has moved away empty while the can remains on the table. The robot subsequently moves the empty gripper over the upper tray in frames 222–257, accomplishing no can transfer. Secure possession before the separation is not established.
- Recovery: Return to the green can, align the fingers around its visible sides, and verify a secure lift before transporting it to the upper tray; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The can remains on the tabletop, with no visible spill or newly established damage; its crushed shape was already present at frame 0.
- Resetability: immediate
- Resetability evidence: The displaced can remains accessible on the table, so another acquisition can be attempted without an environmental reset.

### Failure 2

- Frames: 430-465
- Categories: grasp
- Explanation: In base_image, frames 430–432 show the green can rotating out from the fingers and separating onto the tabletop rather than being retained. It remains near the lower image boundary through frames 445–464 while the empty gripper withdraws and travels toward the upper tray. This is a second visibly unsuccessful acquisition, not an unfinished closing motion.
- Recovery: Re-localize the displaced green can and approach with the fingers centered around it, then verify retention before transport; human intervention is not visibly required.
- Severity: low
- Severity evidence: The failed attempt displaces the can on the table without visible damage or spillage; the images do not establish that it falls off the table.
- Resetability: immediate
- Resetability evidence: The can remains visible on the tabletop and no cleanup, repair, or human repositioning is demonstrably needed before a retry.