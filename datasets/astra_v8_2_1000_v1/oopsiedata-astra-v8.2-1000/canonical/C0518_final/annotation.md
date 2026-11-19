# Episode: C0518

## Episode annotation

- Language task: put the duck on a plate
- Success label: failure
- Outcome evidence: The yellow duck is on the table, separate from the plates, at frame 0 in left, overhead, right and wrist. The arm moves toward the shelving instead; wrist shows a blue-and-yellow toy car at frames 81–600. At frame 600, left, overhead and right still show the duck in its original table location and the plates empty. The task is visibly unachieved, with no observed duck acquisition or placement.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 25 | No |
| 25 | 601 | Yes |

## Failure annotations

### Failure 1

- Frames: 25-601
- Categories: task_not_attempted
- Explanation: Beginning at frame 25, the arm moves away from the duck toward the shelving rather than approaching it, as seen in wrist and right. By frames 81–105, wrist centers on an unrelated blue-and-yellow toy car in a shelf compartment. The robot then remains there with small positional adjustments through frame 600, without acquiring the duck or advancing its placement; left and overhead show the duck and plates unchanged. No possession of the car or physical malfunction is established.
- Recovery: Withdraw from the shelf with clearance, locate the yellow duck on the table, approach and grasp its body, then transfer it onto a plate and release it. No human intervention is visibly necessary.
- Severity: low
- Severity evidence: The task remains incomplete, but no object damage, displacement of the duck, or harmful collision is visible in left, right or overhead through frame 600.
- Resetability: immediate
- Resetability evidence: The duck and plates remain available in their original configuration; another task-directed attempt requires no environmental reset or human intervention.