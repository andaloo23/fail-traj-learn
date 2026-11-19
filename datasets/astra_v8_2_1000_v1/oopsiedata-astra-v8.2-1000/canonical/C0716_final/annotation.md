# Episode: C0716

## Episode annotation

- Language task: Place the toys on the plate with no collisions.
- Success label: success but suboptimal
- Outcome evidence: wrist_cam shows the pink toy released onto the plate at frames 182–190, the blue toy at 343–350, and the tan toy at 839–847. All three remain on the plate as the arm withdraws (overhead_cam and wrist_cam, frames 850–873; overhead_cam, frame 913). Several empty grasp attempts precede the successful tan-toy acquisition at frames 787–800. No unwanted collision or damage is clearly established.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 559 | No |
| 559 | 619 | Yes |
| 619 | 676 | No |
| 676 | 691 | Yes |
| 691 | 727 | No |
| 727 | 738 | Yes |
| 738 | 754 | No |
| 754 | 765 | Yes |
| 765 | 914 | No |

## Failure annotations

### Failure 1

- Frames: 559-619
- Categories: grasp
- Explanation: After closing beside the tan toy, the gripper withdraws empty while the toy remains on the table (wrist_cam and overhead_cam, frames 559–575). It continues to the plate and opens without delivering the toy (frames 584–618), so this transfer does not advance the task.
- Recovery: Return to the tan toy, align the fingers around its body, and verify a secure acquisition before transferring it; no human intervention is needed.
- Severity: low
- Severity evidence: The toy remains on the tabletop, with no visible damage or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The toy remains accessible and the scene needs no environmental reset.

### Failure 2

- Frames: 676-691
- Categories: grasp
- Explanation: The fingers close near the tan toy at frames 667–675, but the arm then retreats with an empty gripper while the toy stays on the table (wrist_cam and overhead_cam, frames 676–690).
- Recovery: Reopen the gripper and realign around the toy's body before closing and testing the lift; no human intervention is needed.
- Severity: low
- Severity evidence: The unsuccessful acquisition leaves the toy on the table without visible damage.
- Resetability: immediate
- Resetability evidence: Another attempt can be made directly from the resulting scene.

### Failure 3

- Frames: 727-738
- Categories: grasp
- Explanation: Following another near-toy closure, the gripper moves away empty and the tan toy remains behind (wrist_cam, frames 724–737; overhead_cam, frames 727–737), establishing another failed acquisition.
- Recovery: Adjust the grasp position so the body lies between the fingers, then confirm retention with a small lift; no human intervention is needed.
- Severity: low
- Severity evidence: Only the acquisition fails; no damage or consequential scene disruption is visible.
- Resetability: immediate
- Resetability evidence: The toy is still reachable on the tabletop, requiring no reset.

### Failure 4

- Frames: 754-765
- Categories: grasp
- Explanation: The gripper approaches the tan toy again at frames 748–753, then withdraws without it and reopens (wrist_cam, frames 754–765). overhead_cam confirms that the toy remains on the table rather than being carried toward the plate.
- Recovery: Reapproach with open fingers, surround a substantial part of the toy, and verify possession before transport; no human intervention is needed.
- Severity: low
- Severity evidence: The toy remains intact on the table; no meaningful damage risk is established.
- Resetability: immediate
- Resetability evidence: The failed attempt requires only robot repositioning, not human or environmental resetting.