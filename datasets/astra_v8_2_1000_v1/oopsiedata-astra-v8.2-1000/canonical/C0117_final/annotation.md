# Episode: C0117

## Episode annotation

- Language task: Pick basketball and place in blue bowl.
- Success label: failure
- Outcome evidence: In exterior_cam, the robot repeatedly lifts the basketball but releases it onto the table outside the bowl (frames 97–104, 198–208, 341–350, and 509–515). At frame 599 the basketball remains on the tabletop, separate from the blue bowl. This is a visibly unsuccessful episode, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 97 | No |
| 97 | 105 | Yes |
| 105 | 198 | No |
| 198 | 210 | Yes |
| 210 | 341 | No |
| 341 | 358 | Yes |
| 358 | 431 | No |
| 431 | 449 | Yes |
| 449 | 509 | No |
| 509 | 516 | Yes |
| 516 | 589 | Yes |
| 589 | 600 | No |

## Failure annotations

### Failure 1

- Frames: 97-105
- Categories: grasp
- Explanation: exterior_cam frames 90–96 show the basketball held above the table; at frame 97 it separates from the opening gripper and falls onto the tabletop, outside the blue bowl, through frames 99–104. The acquired ball is not retained for placement.
- Recovery: Reacquire the ball, verify retention with a small lift, and carry it over the bowl before opening the gripper; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The ball falls onto the clear tabletop; no damage or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: The ball remains accessible on the table and the bowl remains usable; no environmental reset is needed.

### Failure 2

- Frames: 198-210
- Categories: grasp
- Explanation: After another successful lift visible in exterior_cam frames 182–197, the ball separates from the gripper at frame 198 and bounces or rolls on the table through frames 202–209, again outside the bowl.
- Recovery: Recenter the grasp on the ball and verify secure retention before transporting it to the bowl; human intervention is not visibly necessary.
- Severity: low
- Severity evidence: The visible consequence is another tabletop drop, without observed damage.
- Resetability: immediate
- Resetability evidence: Both task objects remain accessible and usable for another attempt.

### Failure 3

- Frames: 341-358
- Categories: grasp
- Explanation: exterior_cam frames 325–340 show the lifted basketball moving with the gripper. At frame 341 it separates and falls, then rolls toward the lower image boundary through frames 342–357 instead of entering the bowl. The robot begins approaching it again at frame 358.
- Recovery: Locate the ball fully before approaching, then reacquire it and maintain retention until positioned over the bowl; request human assistance only if its location cannot be safely verified.
- Severity: low
- Severity evidence: The ball visibly lands and rolls on the tabletop; no damage is established, and the image boundary does not establish a fall off the table.
- Resetability: immediate
- Resetability evidence: The ball remains partly visible at the lower boundary and is subsequently approached; no required human reset is established.

### Failure 4

- Frames: 431-449
- Categories: grasp
- Explanation: Following the approach and acquisition motion near the lower image boundary, exterior_cam frames 431–440 show the gripper lifting away empty while the orange basketball remains at the bottom of the image. This establishes a failed acquisition rather than merely unfinished finger closure.
- Recovery: Reobserve the ball and align the fingers around its center before closing and testing a small lift; no human intervention is visibly required.
- Severity: low
- Severity evidence: The attempt leaves the ball behind without visible damage or harmful contact.
- Resetability: immediate
- Resetability evidence: A new grasp can be attempted without resetting the environment.

### Failure 5

- Frames: 509-516
- Categories: grasp
- Explanation: exterior_cam frames 494–508 show the basketball held and lifted again. At frame 509 it separates from the gripper, then lands on the tabletop in frames 510–515, still well outside the blue bowl.
- Recovery: Reacquire the ball and keep the gripper closed during transport, releasing only after confirming alignment above the bowl; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The ball lands on the tabletop without visible damage to it or other objects.
- Resetability: immediate
- Resetability evidence: The ball is plainly accessible on the table, with no cleanup or repositioning intervention required.

### Failure 6

- Frames: 516-589
- Categories: task_not_attempted
- Explanation: In exterior_cam frames 516–538, the empty gripper withdraws from the basketball and moves around the bowl area; frames 539–588 show prolonged hovering and small motions without reacquiring the ball or advancing placement. The basketball remains stationary on the foreground tabletop. A renewed approach toward it begins at frame 589.
- Recovery: Stop the unproductive empty-gripper motions, locate the basketball, and perform a verified pickup followed by transport to the bowl; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The visible consequence is lost progress and time, not damage.
- Resetability: immediate
- Resetability evidence: The task objects remain available in a usable scene, so the robot can resume without an environmental reset.