# Episode: C0422

## Episode annotation

- Language task: Clean the table by placing the cans in the upper tray and the bowls in the tray on the right.
- Success label: success but side effects
- Outcome evidence: In base_image, both cans are in the upper blue tray by frame 213, the blue bowl is released onto the right red tray by frame 282, and the pink bowl is released onto the blue bowl by frames 373–378. Frame 423 confirms all four objects remain in their designated trays. However, the robot unintentionally displaces and rocks the pink bowl while transporting the green can (frames 68–74) and while acquiring the blue bowl (frames 225–244).

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 68 | No |
| 68 | 75 | Yes |
| 75 | 225 | No |
| 225 | 245 | Yes |
| 245 | 424 | No |

## Failure annotations

### Failure 1

- Frames: 68-75
- Categories: collision
- Explanation: In base_image frames 68–74, the green can and gripper pass against the pink bowl during the can transfer, visibly shifting and tipping the bowl rather than placing it in its destination. The robot clears the bowl and resumes transport toward the upper tray at frame 75; subsequent bowl rocking is a consequence, not continued failing action.
- Recovery: Lift the held can clear of the bowl before continuing to the upper tray, then locate the displaced bowl before its later pickup; no human intervention is needed.
- Severity: low
- Severity evidence: The pink bowl rocks and shifts on the tabletop but remains accessible; no contents, breakage, or meaningful damage are visible in base_image frames 68–100.
- Resetability: immediate
- Resetability evidence: The bowl remains on the table and settles upright, so the robot can continue from its updated position without environmental intervention.

### Failure 2

- Frames: 225-245
- Categories: collision
- Explanation: In base_image frames 225–244, while the gripper aligns with and acquires the blue bowl, the robot also disturbs the adjacent pink bowl, pushing it left and tipping it markedly by frames 240–243. This unintended contact does not advance placement of the pink bowl. At frame 245, the robot begins carrying the blue bowl clear toward the right tray.
- Recovery: Clear the neighboring bowl with the arm and gripper before lifting the blue bowl, allow the pink bowl to settle, and update its pickup position; no human intervention is needed.
- Severity: low
- Severity evidence: The pink bowl is displaced and rocks on the tabletop but does not fall off or visibly break; base_image frames 245–287 show it settling upright.
- Resetability: immediate
- Resetability evidence: The displaced bowl remains reachable on the usable tabletop, permitting another task-directed pickup without a human reset.
