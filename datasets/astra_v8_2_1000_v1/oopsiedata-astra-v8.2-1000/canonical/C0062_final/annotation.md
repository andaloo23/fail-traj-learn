# Episode: C0062

## Episode annotation

- Language task: put the animal in the purple bowl
- Success label: success but side effects
- Outcome evidence: The robot lifts the yellow toy animal and carries it to the purple bowl (frames 105–177, left, right and wrist), releases it at frames 185–193 (wrist), and withdraws, leaving it resting in the bowl (frames 217, 289 and 409, wrist; frame 499, overhead and right). After completing the task, it approaches an unrelated orange round object on the shelf and closes its fingers against it, slightly disturbing it rather than stopping (frames 409–499, wrist and left). No damage is visible.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 409 | No |
| 409 | 500 | Yes |

## Failure annotations

### Failure 1

- Frames: 409-500
- Categories: sequencing_semantic
- Explanation: After leaving the animal in the purple bowl, the robot directs its gripper toward an unrelated orange round shelf object (frames 409–465, wrist and left), closes against it (frames 473–480, wrist), and withdraws without carrying it (frames 489–499, wrist). This unnecessary wrong-object interaction does not advance the completed task and slightly disturbs the object; secure possession is not established.
- Recovery: Stop interacting with the shelf object, withdraw along a clear path, and finish after confirming the animal remains in the purple bowl; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The unrelated object remains on the shelf, the animal stays in the bowl, and no damage or meaningful damage risk is visible in frames 489–499, wrist, overhead and right.
- Resetability: immediate
- Resetability evidence: The scene remains usable and no object retrieval, repair or human reset is visibly required; the small shelf-object disturbance does not prevent another attempt.