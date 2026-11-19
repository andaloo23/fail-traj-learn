# Episode: C0850_W01

## Episode annotation

- Language task: Seperate the food and the toys into the two bowls.
- Success label: failure
- Outcome evidence: Completion is unconfirmed in this window, rather than a confirmed whole-episode failure: overhead_cam and wrist_cam show the pink toy transferred into the purple bowl at frames 259–274, but other objects remain unsorted at frame 349. The green bowl is unintentionally displaced during acquisition of the pink toy (frames 181–203), and the brown object escapes the closing gripper at frames 343–349. Later episode context is not supplied.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 181 | No |
| 181 | 204 | Yes |
| 204 | 343 | No |
| 343 | 350 | Yes |

## Failure annotations

### Failure 1

- Frames: 181-204
- Categories: collision
- Explanation: While positioning the gripper beside the pink toy, the robot displaces and rocks the green bowl rather than leaving it stable; overhead_cam shows the bowl tilting and shifting at frames 181–200, corroborated by wrist_cam at frames 190–203. This is an unintended disturbance during acquisition, not required sorting contact. The bowl settles upright and subsequent lifting of the toy advances the task.
- Recovery: Clear the bowl rim, reassess its position, and use an approach to the toy that avoids the bowl; human intervention is not visibly necessary.
- Severity: low
- Severity evidence: The empty bowl rocks and shifts but remains on the table and settles upright; neither camera shows breakage or spilled contents.
- Resetability: immediate
- Resetability evidence: The bowl remains usable and accessible, so the robot can continue using its updated position without a human reset.

### Failure 2

- Frames: 343-350
- Categories: grasp
- Explanation: The brown object moves out of the closing fingers at frames 343–344 in wrist_cam, and overhead_cam shows it rolling away to the right of the gripper through frame 349 instead of being retained. This visibly unsuccessful acquisition does not sort the object. The interval reaches the window boundary; any continuation or recovery beyond it is unseen.
- Recovery: Allow the object to settle, locate it again, and realign the fingers around its center before retrying with adequate clearance from adjacent objects; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The object rolls a short distance on the tabletop without visible damage or falling off the table.
- Resetability: immediate
- Resetability evidence: The displaced object remains visible and accessible on the table, permitting another attempt without environmental repair or human resetting.