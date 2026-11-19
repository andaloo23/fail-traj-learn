# Episode: C0775

## Episode annotation

- Language task: Open the oven.
- Success label: failure
- Outcome evidence: The oven door remains closed in left_ego_image at frames 0, 100, 150 and 212. The robot repositions near the oven, holds nearly the same pose for a sustained interval, and resumes moving toward its front around frames 146–156 (image and left_ego_image). No opening is visible by frame 212; completion is unconfirmed, and the final near-door positioning does not establish a failed grasp or pull.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 40 | No |
| 40 | 146 | Yes |
| 146 | 213 | No |

## Failure annotations

### Failure 1

- Frames: 40-146
- Categories: task_not_attempted
- Explanation: Across frames 40–145, image and left_ego_image show the gripper remaining in essentially the same position near the oven’s upper front, while the door stays closed; wrist_image likewise shows no substantial task-directed progress. This sustained interval of roughly nine seconds is unproductive stalling, rather than a brief alignment pause. The images do not establish a mechanical or planning cause.
- Recovery: Resume deliberate alignment with the oven handle, establish a secure grasp, and pull along the door’s opening path while checking clearance and door motion; no human intervention is visibly required.
- Severity: low
- Severity evidence: The observed consequence is delay without opening the oven; no damage, displaced objects or meaningful damage risk is visible during this interval.
- Resetability: immediate
- Resetability evidence: The oven and surrounding objects remain in place, so another opening attempt requires no environmental reset or human intervention.