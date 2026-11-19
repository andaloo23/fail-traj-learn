# Episode: C0600

## Episode annotation

- Language task: Pick basketball and place in blue bowl.
- Success label: failure
- Outcome evidence: In exterior_cam, the robot lifts the basketball (frames 87–116), drops it onto the table (117–124), and later reacquires it (395–408) but again drops it outside the bowl (489–500). At frame 599 the basketball remains on the tabletop and the blue bowl is empty; this is visibly unsuccessful execution, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 117 | No |
| 117 | 125 | Yes |
| 125 | 169 | No |
| 169 | 212 | Yes |
| 212 | 395 | No |
| 395 | 452 | Yes |
| 452 | 489 | No |
| 489 | 501 | Yes |
| 501 | 600 | Yes |

## Failure annotations

### Failure 1

- Frames: 117-125
- Categories: grasp
- Explanation: In exterior_cam, the previously lifted basketball separates from the fingers at frame 117 and falls and bounces on the tabletop at frames 118–124, rather than entering the blue bowl. The images establish loss of retention, but not its hidden cause.
- Recovery: Track the ball until it settles, realign the fingers around it, and verify a stable grasp before transporting it over the bowl; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The ball lands on the clear tabletop without visible damage or disturbance to other objects.
- Resetability: immediate
- Resetability evidence: The ball remains accessible on the table, allowing another attempt without environmental intervention.

### Failure 2

- Frames: 169-212
- Categories: grasp
- Explanation: In exterior_cam, the ball moves out from beneath the closing gripper at frames 169–178 and remains on the table during further unsuccessful finger movements; the gripper withdraws empty at frames 204–211, confirming failed acquisition.
- Recovery: Recenter the open fingers around the ball's current position, grasp without pushing it sideways, and verify retention with a small lift; human intervention is not required by the visible state.
- Severity: low
- Severity evidence: The unsuccessful acquisition only displaces the ball slightly on the tabletop; no damage is visible.
- Resetability: immediate
- Resetability evidence: Both target and bowl remain accessible and usable, with no reset needed before retrying.

### Failure 3

- Frames: 395-452
- Categories: manipulation
- Explanation: After establishing another grasp, the robot carries the basketball toward the right edge of exterior_cam and away from the blue bowl at frames 395–430, then continues holding it well away from the destination through frame 451. This sustained wrong-direction transport does not advance placement; a return toward the table begins at frame 452.
- Recovery: Maintain the grasp and redirect the ball along a clear path toward the blue bowl, then lower it over the opening before release; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The ball remains held during this detour, and no collision or damage is visible.
- Resetability: immediate
- Resetability evidence: The environment remains intact; the robot can correct its transport path without an environmental reset.

### Failure 4

- Frames: 489-501
- Categories: grasp
- Explanation: In exterior_cam, the basketball leaves the gripper at frame 489 while still to the right of the bowl, then bounces and rolls on the tabletop through frame 500. The second lift therefore also ends without placement.
- Recovery: Wait for the ball to settle, reacquire it with verified retention, and release only after alignment over the bowl; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The ball stays on the table and no damage or unintended object disturbance is visible.
- Resetability: immediate
- Resetability evidence: The displaced ball is still accessible for another attempt without cleanup or replacement.

### Failure 5

- Frames: 501-600
- Categories: task_not_attempted
- Explanation: Following the second drop, exterior_cam shows the empty gripper remaining elevated and making small movements away from the ball at frames 501–599, without a renewed approach or acquisition. The basketball remains outside the bowl throughout this sustained unproductive interval.
- Recovery: Resume a task-directed approach to the settled basketball, acquire it securely, and transport it to the bowl; the images do not establish a need for human intervention.
- Severity: low
- Severity evidence: The interval leaves the task unfinished but causes no visible damage or additional disturbance.
- Resetability: immediate
- Resetability evidence: The ball and bowl remain on the usable tabletop; another attempt requires no environmental reset.