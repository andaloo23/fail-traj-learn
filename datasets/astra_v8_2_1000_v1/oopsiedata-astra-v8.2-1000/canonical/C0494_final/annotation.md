# Episode: C0494

## Episode annotation

- Language task: pack three grocery objects into a seven eleven bag
- Success label: failure
- Outcome evidence: The robot opens and stands the bag upright (aria, frames 200–430), but no grocery object is visibly packed. The purple packet is released outside the bag and lands on the table (aria and right_wrist, frames 862–872). The blue can subsequently falls and rolls off the far table edge (aria, frames 1126–1140). At frame 1450, aria shows the packet and green can still outside the bag, and right_wrist shows the empty gripper. These are visibly unsuccessful attempts, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 862 | No |
| 862 | 892 | Yes |
| 892 | 1047 | No |
| 1047 | 1063 | Yes |
| 1063 | 1126 | No |
| 1126 | 1155 | Yes |
| 1155 | 1368 | No |
| 1368 | 1451 | Yes |

## Failure annotations

### Failure 1

- Frames: 862-892
- Categories: manipulation
- Explanation: After carrying the purple packet, the robot releases it outside the bag rather than into its opening; it falls alongside the bag and rests on the tabletop (right_wrist, frames 862–866; aria, frames 864–872). The robot briefly remains above the failed placement.
- Recovery: Regrasp the packet, align it inside the visible bag opening, lower it below the rim, and release; no human intervention is needed.
- Severity: low
- Severity evidence: The packet lands on the table without visible damage or significant hazard.
- Resetability: immediate
- Resetability evidence: The packet remains accessible on the tabletop and can be picked up again without intervention.

### Failure 2

- Frames: 1047-1063
- Categories: grasp
- Explanation: During acquisition at the cans, the blue can tips onto its side instead of being secured, while the green can is displaced (aria and right_wrist, frames 1047–1057). The target is not yet retained for transport.
- Recovery: Re-align to the sideways blue can and secure a stable grasp before lifting, while leaving clearance around the green can; no human intervention is needed.
- Severity: low
- Severity evidence: The cans remain on the table; no spill or damage is visible.
- Resetability: immediate
- Resetability evidence: The sideways can is accessible for regrasping without a human reset.

### Failure 3

- Frames: 1126-1155
- Categories: grasp
- Explanation: The previously lifted blue can leaves the gripper, falls onto the table, and tumbles toward and over the far edge rather than entering the bag (aria and right_wrist, frames 1126–1139). The gripper then moves away empty.
- Recovery: Stop and locate the can; ask a person to retrieve it from below the table and inspect it before another packing attempt.
- Severity: low
- Severity evidence: A fall off the table is visible, but the landing is not shown and no damage or spill is established.
- Resetability: minor_reset
- Resetability evidence: The can must be retrieved from below or beyond the table; straightforward human retrieval appears sufficient, though its landing location is unseen.

### Failure 4

- Frames: 1368-1451
- Categories: grasp
- Explanation: The final acquisition fails to retain the green can: it tips onto its side near the gripper and remains on the table as the robot lifts away empty (aria, frames 1368–1373 and 1425–1450; right_wrist, frames 1435–1450).
- Recovery: Reapproach the sideways green can, align the fingers around its body, and verify retention with a small lift before transferring it into the bag; no human intervention is needed.
- Severity: low
- Severity evidence: The can remains on the table without visible leakage or damage.
- Resetability: immediate
- Resetability evidence: The can is still accessible on the tabletop and can be regrasped without intervention.