# Episode: C0365

## Episode annotation

- Language task: Clean the table by placing the cans in the upper tray and the bowls in the tray on the right.
- Success label: success but side effects
- Outcome evidence: In base_image, both cans are in the upper blue tray by frame 2000, the blue bowl is in the right red tray by frame 2700, and the pink bowl is released onto it by frame 4400. Frames 4549 and 4775 confirm the completed sorting with no task objects remaining on the exposed tabletop. However, the robot unintentionally disturbs the blue bowl while transporting the second can (frames 1610–1676), and makes two unsuccessful pink-bowl acquisitions before succeeding (frames 2985–3034 and 3555–3603).

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 1610 | No |
| 1610 | 1676 | Yes |
| 1676 | 2985 | No |
| 2985 | 3035 | Yes |
| 3035 | 3555 | No |
| 3555 | 3604 | Yes |
| 3604 | 4776 | No |

## Failure annotations

### Failure 1

- Frames: 1610-1676
- Categories: collision
- Explanation: In base_image frames 1610–1675, the blue bowl emerges tilted and displaced from beneath the withdrawing arm as the robot carries the pink/yellow can toward the upper tray. This is unintended disturbance, not a bowl transfer to the right tray. The precise contact point and any earlier onset are obscured; subsequent rocking, visible at frame 1700 after the arm clears, is a consequence rather than a continuing collision action.
- Recovery: Maintain clearance from the bowls while placing the can, let the disturbed bowl settle, then reacquire its position and transfer it to the right tray; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The bowl shifts and rocks on the tabletop, but no breakage, spill, or meaningful damage is visible in base_image frames 1610–2000.
- Resetability: immediate
- Resetability evidence: The bowl remains accessible on the table and is upright by frame 2000; no environmental restoration or human reset is required.

### Failure 2

- Frames: 2985-3035
- Categories: grasp
- Explanation: Following engagement at the pink bowl’s rim in base_image frames 2983–2984, the gripper withdraws starting at frame 2985. Frames 3000 and 3033–3034 show it moving away empty while the bowl remains on the tabletop, establishing failed acquisition; the underlying contact mechanics are not established.
- Recovery: Reapproach an accessible rim section, align and close the fingers securely, and verify acquisition with a small controlled lift before transport; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The pink bowl remains upright without visible damage or spill, and the other sorted objects remain undisturbed in base_image frames 3000–3035.
- Resetability: immediate
- Resetability evidence: The bowl remains accessible in its tabletop position, so another attempt requires no environmental reset.

### Failure 3

- Frames: 3555-3604
- Categories: grasp
- Explanation: In base_image frames 3553–3554, the gripper is engaged at the pink bowl area; from frame 3555 it withdraws without transporting the bowl. Frames 3600–3603 show the empty gripper separated from the bowl, which remains upright outside the right tray. This is a second failed acquisition, separated from the first by repositioning and a renewed approach.
- Recovery: Re-align around the pink bowl rim and verify secure retention with a small lift before moving toward the right tray; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The failed attempt leaves the bowl upright on the tabletop, with no visible damage, spill, or harmful displacement in base_image frames 3600–3604.
- Resetability: immediate
- Resetability evidence: No environmental restoration is necessary; the bowl and destination tray remain accessible for another attempt.