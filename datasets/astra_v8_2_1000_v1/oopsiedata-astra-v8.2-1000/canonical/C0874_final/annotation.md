# Episode: C0874

## Episode annotation

- Language task: Clean the table by placing the cans in the upper tray and the bowls in the tray on the right.
- Success label: failure
- Outcome evidence: In base_image, both cans are in the upper blue tray by frame 900, and the blue bowl is in the right red tray by frame 1200. Three attempts to acquire the pink bowl instead produce empty movements toward the right tray, visible at frames 1398, 1748, and 2098. At frame 2193 the pink bowl remains on the table, establishing visibly incomplete execution rather than merely unconfirmed placement. No abnormal termination or damage is established.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 1293 | No |
| 1293 | 1501 | Yes |
| 1501 | 1640 | No |
| 1640 | 1900 | Yes |
| 1900 | 1984 | No |
| 1984 | 2194 | Yes |

## Failure annotations

### Failure 1

- Frames: 1293-1501
- Categories: grasp
- Explanation: In base_image, frames 1293–1300 show the fingers closing beside the pink bowl rather than securing its rim. By frames 1398–1401 the gripper has moved empty to the right tray while the bowl remains on the table; it subsequently opens there by frame 1500. This empty transport and release sequence continues the failed acquisition across the window boundary. Return toward the bowl is visible by frame 1600; the exact recovery transition between frames 1500 and 1600 is uncertain, and frame 1501 is used as the interval boundary.
- Recovery: Return to the pink bowl, adjust the grasp position so the fingers capture its rim, and verify possession with a small lift before transporting it; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The pink bowl remains upright on the table, with no visible damage, spill, or harmful displacement in base_image through frame 1600.
- Resetability: immediate
- Resetability evidence: The bowl remains accessible for another attempt; no environmental reset or human intervention is needed.

### Failure 2

- Frames: 1640-1900
- Categories: grasp
- Explanation: In base_image, frames 1640–1641 show another closure beside the pink bowl, and frames 1700–1751 show the gripper departing empty and reaching the right tray while the bowl stays behind. The empty placement sequence continues over the tray at frame 1800, rather than ending at the window boundary. Withdrawal for another approach is visible at frame 1900; the exact transition between frames 1800 and 1900 is uncertain.
- Recovery: Reposition the open gripper across the bowl rim rather than repeating the same offset closure, then confirm a secure lift before moving toward the tray; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The attempt leaves the pink bowl upright and unmoved, with no visible damage or harmful collision in base_image through frame 1900.
- Resetability: immediate
- Resetability evidence: The missed bowl remains available on the table, so another attempt requires no scene resetting.

### Failure 3

- Frames: 1984-2194
- Categories: grasp
- Explanation: In base_image, frames 1984–2000 show a third closure beside the pink bowl without acquisition. Frames 2098–2101 show the empty gripper over the right tray while the pink bowl remains on the table, followed by opening there at frames 2192–2193. This is one continuous failed acquisition and empty placement sequence through the episode end, not a separate failure caused by the recording ending.
- Recovery: Return to the bowl with an adjusted rim grasp and verify retention before transport; if acquisition cannot be verified, stop the transfer and reassess alignment. No human intervention is visibly required.
- Severity: low
- Severity evidence: At frame 2193 in base_image, the bowl remains upright and the scene remains usable; no damage, spill, or concrete damage risk is visible.
- Resetability: immediate
- Resetability evidence: The pink bowl remains accessible in its table location, permitting another acquisition attempt without environmental intervention.