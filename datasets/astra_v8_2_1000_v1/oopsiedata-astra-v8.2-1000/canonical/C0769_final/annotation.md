# Episode: C0769

## Episode annotation

- Language task: Pick basketball and place in blue bowl.
- Success label: failure
- Outcome evidence: In exterior_cam, the robot acquires and carries the basketball (frames 76–130), but moves it around away from the blue bowl rather than placing it inside. The ball separates from the gripper onto the tabletop at frames 383–387 and is subsequently reacquired (frames 513–529). At frame 599 it remains in the gripper, outside the bowl. Placement is visibly unfinished; the episode also contains an observed loss of the ball, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 76 | No |
| 76 | 383 | Yes |
| 383 | 389 | Yes |
| 389 | 532 | No |
| 532 | 600 | Yes |

## Failure annotations

### Failure 1

- Frames: 76-383
- Categories: manipulation
- Explanation: After acquiring the basketball, the robot carries it rightward and toward the foreground, then far left, and repeatedly moves it around the foreground instead of delivering it to the bowl (exterior_cam frames 76–169, 193–281, and 301–382). This sustained, circuitous transport does not establish placement alignment; the bowl remains behind the held ball. No hidden cause or wall collision is established.
- Recovery: Retain the ball, localize the bowl, and move along a clear path to center the ball above its opening before lowering and releasing it; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The ball remains held throughout this interval, with no visible damage or meaningful damage risk established.
- Resetability: immediate
- Resetability evidence: The bowl remains upright and the ball is available in the gripper; correcting the transport requires no environmental reset.

### Failure 2

- Frames: 383-389
- Categories: grasp
- Explanation: In exterior_cam frames 383–387, the previously held basketball separates from the fingers and falls onto the foreground tabletop, well outside the blue bowl. This loses the established acquisition; whether it slipped or was released is not clear from the images.
- Recovery: Locate the settled ball, approach with the fingers aligned around it, and reacquire it before transporting it to the bowl; no human intervention is needed.
- Severity: low
- Severity evidence: The small ball lands on the tabletop without visible damage, spillage, or disruption to other objects.
- Resetability: immediate
- Resetability evidence: The ball remains accessible on the table and can be reacquired without a person resetting the scene.

### Failure 3

- Frames: 532-600
- Categories: manipulation
- Explanation: Following successful reacquisition, the robot again carries the ball toward the foreground, reverses toward the bowl, then moves forward again while continuing to hold it (exterior_cam frames 532–553, 557–577, and 582–599). These repeated excursions fail to progress to placement in the bowl.
- Recovery: Stop the repeated excursions, maintain a secure grasp, and align the ball over the bowl opening before lowering and releasing it; human intervention is not visibly required.
- Severity: low
- Severity evidence: The ball stays in the gripper and no damage or harmful contact is visible; the consequence is failure to complete placement.
- Resetability: immediate
- Resetability evidence: The ball is still held and the bowl remains usable, so the task can resume without an environmental reset.