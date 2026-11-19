# Episode: C0536

## Episode annotation

- Language task: Move the left stuffed toy to the largest bowl.
- Success label: failure
- Outcome evidence: In image_primary frame 0, the left toy is blue and white, and the largest bowl is the central white bowl. The robot instead lifts the pink toy in frames 16–20 and leaves it outside the bowl at frame 21. It later attempts to acquire the blue-and-white toy but withdraws empty in frames 70–72. At frame 90, the intended toy remains on the table and the white bowl is empty; this is visible noncompletion with failed actions, not merely an unconfirmed placement.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 6 | No |
| 6 | 22 | Yes |
| 22 | 30 | No |
| 30 | 51 | Yes |
| 51 | 70 | No |
| 70 | 72 | Yes |
| 72 | 77 | No |
| 77 | 91 | Yes |

## Failure annotations

### Failure 1

- Frames: 6-22
- Categories: sequencing_semantic
- Explanation: In image_primary frames 6–15, the gripper targets and closes around the right-hand pink toy rather than the left blue-and-white toy. It carries the pink toy in frames 16–20 and releases it beside the white bowl at frame 21, relocating the wrong object without advancing the requested transfer.
- Recovery: Leave the pink toy safely supported, identify the left blue-and-white toy, and grasp and transfer that toy into the white bowl; human intervention is not needed.
- Severity: low
- Severity evidence: The unrelated soft toy is displaced on the tabletop, but no damage or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: The intended toy and bowl remain accessible, so another task attempt needs no environmental reset.

### Failure 2

- Frames: 30-51
- Categories: task_not_attempted
- Explanation: In image_primary frames 30–43, the empty gripper remains essentially stationary above the table between the target toy and white bowl. Small back-and-forth movements in frames 44–50 do not establish an acquisition approach or move either task object, forming a sustained unproductive interval before the approach resumes at frame 51.
- Recovery: Resume a directed approach to the blue-and-white toy, align the fingers around its body, and attempt acquisition; no human intervention is visibly required.
- Severity: low
- Severity evidence: The interval delays task progress without visible damage or hazardous contact.
- Resetability: immediate
- Resetability evidence: No scene change during the stall prevents an immediate renewed attempt.

### Failure 3

- Frames: 70-72
- Categories: grasp
- Explanation: After closing around the blue-and-white toy in image_primary frames 63–69, the gripper lifts and retreats empty in frames 70–71 while the toy remains on the tabletop. This establishes a failed acquisition rather than merely an unfinished closure.
- Recovery: Reopen and realign around a substantial portion of the toy, close, and verify retention with a small lift before transporting it; human intervention is not needed.
- Severity: low
- Severity evidence: The toy remains safely on the table with no visible damage.
- Resetability: immediate
- Resetability evidence: The toy is still accessible and requires no manual repositioning for another attempt.

### Failure 4

- Frames: 77-91
- Categories: sequencing_semantic, collision
- Explanation: In image_primary frames 77–86, the gripper again descends around the pink toy instead of the left blue-and-white toy. During this interaction, the white bowl visibly shifts left and forward in frames 78–85, indicating unintended contact-driven displacement. The gripper withdraws in frames 87–90 without completing the requested transfer.
- Recovery: Lift clear of the bowl and pink toy, reassess their positions, and approach the blue-and-white toy without contacting the bowl; human intervention is not visibly necessary.
- Severity: low
- Severity evidence: The bowl and pink toy are displaced but remain upright or supported on the table; no breakage, spill, or other damage is visible.
- Resetability: immediate
- Resetability evidence: The shifted bowl remains usable and accessible, and the intended toy remains available for a new attempt without a human reset.