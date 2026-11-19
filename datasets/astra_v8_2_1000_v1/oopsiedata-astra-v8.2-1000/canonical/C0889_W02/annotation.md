# Episode: C0889_W02

## Episode annotation

- Language task: Place the toys on the plate with no collisions.
- Success label: failure
- Outcome evidence: Provisionally, the task is not completed in this window: overhead_cam shows the plate remaining empty at frames 350, 420, 530 and 699, while wrist_cam shows the beige toy outside its rim. Gripper closures followed by withdrawal without transferring the toy establish unsuccessful acquisition, rather than only unconfirmed completion. No damaging collision is established. Earlier context beyond frames 348–349 and later execution are unavailable; the window ending does not establish episode termination.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 350 | 367 | No |
| 367 | 406 | Yes |
| 406 | 530 | No |
| 530 | 649 | Yes |
| 649 | 660 | No |
| 660 | 700 | Yes |

## Failure annotations

### Failure 1

- Frames: 367-406
- Categories: grasp
- Explanation: After finger closure at frames 361–365, the gripper shifts away and rotates without lifting the beige toy during frames 367–405. wrist_cam shows the toy remaining outside the plate, and overhead_cam shows no transfer onto the plate. This is an unsuccessful acquisition; reopening begins at frame 406.
- Recovery: Reopen, align the fingers around the toy rather than beside it, and verify a clear lift before transferring it over the plate; human intervention is not visibly needed.
- Severity: low
- Severity evidence: The toy remains on the tabletop, with no visible damage to it, the plate or the robot.
- Resetability: immediate
- Resetability evidence: The toy remains accessible beside the plate, allowing a corrected attempt without environmental resetting.

### Failure 2

- Frames: 530-649
- Categories: task_not_attempted
- Explanation: Following the preceding repositioning, the robot remains nearly stationary with its gripper open beside the toy for approximately eight seconds. overhead_cam and wrist_cam at frames 530, 560, 600 and 640 show no acquisition or placement progress; small adjustments do not produce a discernible advancing action. Renewed finger closure begins at frame 649.
- Recovery: Resume a deliberate, clearance-checked approach and grasp of the beige toy, then verify possession before moving toward the plate; no human intervention is visibly required.
- Severity: low
- Severity evidence: The observed consequence is delay, without visible damage or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: Stalling does not visibly alter the scene or require a person to reset anything.

### Failure 3

- Frames: 660-700
- Categories: grasp
- Explanation: Following closure at frames 649–659, the gripper rises and changes orientation at frames 660–699 without carrying the beige toy onto the plate. overhead_cam shows the withdrawing gripper and empty plate, while wrist_cam shows the toy remaining beside the rim rather than securely moving with the fingers. The unsuccessful withdrawal continues to the window edge; its continuation or subsequent recovery outside this window is unknown.
- Recovery: Stop the empty transfer, reopen and reacquire the toy with clearance from the plate rim, verifying that it rises with the fingers before proceeding; human intervention is not visibly necessary.
- Severity: low
- Severity evidence: No breakage, spill or damaging impact is visible; the consequence is another unsuccessful acquisition.
- Resetability: immediate
- Resetability evidence: The toy and plate remain usable and accessible, so a corrected attempt does not visibly require an environmental reset.