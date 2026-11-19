# Episode: C0489

## Episode annotation

- Language task: Clean the table by placing the cans in the upper tray and the bowls in the tray on the right.
- Success label: success but side effects
- Outcome evidence: In base_image, both cans are in the upper blue tray by frame 404, and both bowls are stacked in the right red tray by frames 673–745. Completion is visible. The first green-can acquisition fails, with the gripper withdrawing empty at frames 121–139. Incidental bowl displacement also occurs during the other can acquisition and the blue-bowl acquisition.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 121 | No |
| 121 | 140 | Yes |
| 140 | 289 | No |
| 289 | 303 | Yes |
| 303 | 476 | No |
| 476 | 481 | Yes |
| 481 | 746 | No |

## Failure annotations

### Failure 1

- Frames: 121-140
- Categories: grasp
- Explanation: In base_image frames 121–139, the gripper withdraws toward the upper tray without the green can, which remains on the table after the closing attempt. This establishes failed acquisition; renewed alignment begins at frame 140.
- Recovery: Reopen and realign around the green can, then verify retention with a small lift before transferring it; no human intervention is needed.
- Severity: low
- Severity evidence: The can remains on the tabletop, with no visible spill or new damage attributable to the missed acquisition.
- Resetability: immediate
- Resetability evidence: The target remains accessible for another grasp without environmental resetting.

### Failure 2

- Frames: 289-303
- Categories: collision
- Explanation: In base_image frames 289–302, the gripper and red/yellow can move against the adjacent blue bowl, shifting the bowl down and right during can acquisition. This is incidental displacement rather than placement of the bowl in its assigned tray.
- Recovery: Clear the bowl before continuing the can lift, using a grasp and lifting path that avoid neighboring objects; no human intervention is needed.
- Severity: low
- Severity evidence: The blue bowl shifts slightly but stays upright on the table; no damage or spill is visible.
- Resetability: immediate
- Resetability evidence: Both objects remain accessible, and the task can continue from their changed positions without a human reset.

### Failure 3

- Frames: 476-481
- Categories: collision
- Explanation: In base_image frames 476–480, the blue bowl being acquired presses into the neighboring pink bowl, displacing it downward. The pink bowl is not being intentionally transferred at this point; the blue bowl begins lifting clear at frame 481.
- Recovery: Lift the blue bowl clear of its neighbor before translating it, and reacquire the pink bowl’s updated position for its later transfer; no human intervention is needed.
- Severity: low
- Severity evidence: The pink bowl remains upright and on the table after the small displacement, with no visible damage or spill.
- Resetability: immediate
- Resetability evidence: The shifted pink bowl remains reachable and requires no environmental intervention before continuing.
