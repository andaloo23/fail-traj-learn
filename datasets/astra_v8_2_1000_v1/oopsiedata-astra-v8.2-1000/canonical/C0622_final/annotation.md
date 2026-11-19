# Episode: C0622

## Episode annotation

- Language task: Open the oven.
- Success label: failure
- Outcome evidence: The oven door remains closed in left_ego_image and image from frame 0 through frame 399. The gripper approaches the oven during frames 0–89, but then remains near its upper front without visibly opening it (frames 96, 180, 300 and 399, left_ego_image and wrist_image). Completion is not observed; the supported local failure is sustained stalling, not a confirmed failed grasp or pull.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 96 | No |
| 96 | 400 | Yes |

## Failure annotations

### Failure 1

- Frames: 96-400
- Categories: task_not_attempted
- Explanation: After the approach, the gripper stays essentially stationary near the oven for approximately 25 seconds without discernible progress toward opening it. Frames 96, 180, 300 and 399 in left_ego_image and wrist_image show the same gripper placement and closed door. Handle acquisition is not established, so a grasp or post-contact manipulation failure cannot be inferred.
- Recovery: Reassess the handle position, align the gripper for a secure acquisition, and open the door along its hinge path while monitoring clearance and door movement; no human intervention is visibly required.
- Severity: low
- Severity evidence: The task remains incomplete, but image and left_ego_image show no visible damage, displaced objects or other harmful consequences through frame 399.
- Resetability: immediate
- Resetability evidence: The oven remains closed and the surrounding scene is unchanged; another attempt can begin without an environmental reset or visible need for human intervention.