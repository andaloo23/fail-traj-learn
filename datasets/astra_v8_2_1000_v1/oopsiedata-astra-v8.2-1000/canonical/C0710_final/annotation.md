# Episode: C0710

## Episode annotation

- Language task: Pick up the stuffed animal and place it in the cardboard box.
- Success label: failure
- Outcome evidence: The stuffed animal remains on the table outside the box throughout the observed episode (external, frames 0, 545, 934 and 1073). The gripper closes near the animal and withdraws empty in frames 915–934 (external and wrist), establishing a failed acquisition. It subsequently approaches again, but no successful pickup or placement is visible before frame 1073; the final attempt's completion is unconfirmed.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 918 | No |
| 918 | 1013 | Yes |
| 1013 | 1074 | No |

## Failure annotations

### Failure 1

- Frames: 918-1013
- Categories: grasp
- Explanation: After closing near the stuffed animal in frames 915–917, the gripper withdraws without it in frames 918–934; external shows the animal remaining on the table, while wrist shows increasing separation from the closed fingers. The robot then remains at the withdrawn pose through frame 1012 without advancing the transfer. No possession or drop is established.
- Recovery: Reopen the gripper, realign the fingers around a sufficiently substantial part of the animal, descend carefully, and verify retention with a small lift before moving toward the box; no human intervention is visibly required.
- Severity: low
- Severity evidence: The acquisition fails, but the animal and box remain on the table with no visible damage or harmful displacement (external, frame 934).
- Resetability: immediate
- Resetability evidence: The target remains accessible in its original table location, so another approach can be attempted without environmental resetting or human intervention.