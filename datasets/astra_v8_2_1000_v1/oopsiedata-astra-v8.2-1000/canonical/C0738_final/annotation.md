# Episode: C0738

## Episode annotation

- Language task: Push the Displayport cable into the cable holder on the white block.
- Success label: failure
- Outcome evidence: The cable remains on the work surface rather than in the holder. The wrist view shows repeated finger closures beside the cable and empty withdrawals (frames 340–385, 462–480, 570–580, 697–707 and 801–820); front and top corroborate that the cable is not transported onto the block. At frame 862, wrist still shows the cable below and separate from the holder. Earlier acquisition attempts visibly fail; the final approach ends without confirmed acquisition or insertion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 101 | No |
| 101 | 334 | Yes |
| 334 | 436 | No |
| 436 | 462 | Yes |
| 462 | 545 | No |
| 545 | 570 | Yes |
| 570 | 657 | No |
| 657 | 697 | Yes |
| 697 | 779 | No |
| 779 | 801 | Yes |
| 801 | 863 | No |

## Failure annotations

### Failure 1

- Frames: 101-334
- Categories: grasp
- Explanation: Following the initial closure, wrist shows the cable outside the fingertips as the robot repeatedly shifts and closes near it without acquiring it (frames 101–250 and 280–334). The subsequent lift at frames 340–350 is empty; front and top show the cable remaining on the surface.
- Recovery: Open the fingers, align them on opposite sides of a reachable cable section, and verify acquisition with a small lift before transporting it; no human intervention is indicated.
- Severity: low
- Severity evidence: The failed acquisition prevents progress; no damage or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: The cable and holder remain accessible and intact, permitting another attempt without environmental intervention.

### Failure 2

- Frames: 436-462
- Categories: grasp
- Explanation: Wrist shows the fingers closing beside the cable at frames 436–445, then lifting without retaining it at frames 450–462. Front and top show no cable transport toward the holder.
- Recovery: Reopen and reposition across the cable rather than beside it, then confirm retention before lifting farther; human intervention is not needed.
- Severity: low
- Severity evidence: Only acquisition fails; no visible damage results.
- Resetability: immediate
- Resetability evidence: The cable remains on the reachable work surface, with no scene reset needed.

### Failure 3

- Frames: 545-570
- Categories: grasp
- Explanation: The fingers close near the cable in wrist at frames 545–557 but move away empty through frames 558–570. The cable stays below the gripper, also consistent with front and top.
- Recovery: Re-localize the cable section and approach with both fingertips straddling it; use a short verification lift. No human intervention is indicated.
- Severity: low
- Severity evidence: The missed acquisition produces no visible damage or harmful disturbance.
- Resetability: immediate
- Resetability evidence: Another grasp can be attempted directly in the unchanged usable workspace.

### Failure 4

- Frames: 657-697
- Categories: grasp
- Explanation: Wrist shows another closure beside the cable at frames 657–670, followed by small motions and an empty withdrawal through frames 685–697. Front and top show that the cable is still on the surface rather than carried to the block.
- Recovery: Correct the lateral fingertip alignment and verify that the cable moves with the gripper before proceeding; no human assistance is visibly required.
- Severity: low
- Severity evidence: Task progress is prevented, but damage is not observed.
- Resetability: immediate
- Resetability evidence: Neither the cable nor holder requires repositioning by a person for another attempt.

### Failure 5

- Frames: 779-801
- Categories: grasp
- Explanation: Wrist shows the fingers closing at frames 779–790 without trapping the cable, which remains outside the fingertips during the withdrawal at frames 797–801. Front and top likewise show no successful pickup.
- Recovery: Open and re-align around the visible cable, then test retention before attempting placement in the holder; human intervention is not indicated.
- Severity: low
- Severity evidence: The unsuccessful grasp causes no visible damage; its consequence is failure to advance the task.
- Resetability: immediate
- Resetability evidence: The target remains reachable on the surface and the holder remains usable, so no environmental reset is necessary.