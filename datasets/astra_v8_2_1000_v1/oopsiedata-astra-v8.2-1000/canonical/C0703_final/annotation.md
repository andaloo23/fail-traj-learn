# Episode: C0703

## Episode annotation

- Language task: Open the drawer.
- Success label: success but suboptimal
- Outcome evidence: The drawer is visibly pulled outward in frames 195–213 and remains open through frame 239 in image and left_ego_image. Before that success, the gripper closes without acquiring the handle and retreats while the drawer stays shut (frames 94–137, wrist_image and left_ego_image), then reopens and approaches again. No damage or disturbance of unrelated tabletop objects is visible.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 93 | No |
| 93 | 138 | Yes |
| 138 | 240 | No |

## Failure annotations

### Failure 1

- Frames: 93-138
- Categories: grasp
- Explanation: In frames 93–96, wrist_image shows the fingers closing beside the drawer handle rather than securely around it. The gripper subsequently withdraws empty in frames 117–137 while the drawer remains closed in image and left_ego_image, establishing a failed acquisition rather than merely an unfinished grasp. Reopening for another approach begins at frame 138.
- Recovery: Reopen the gripper, align the fingers around the handle, establish a secure grasp, and pull along the drawer’s travel direction; no human intervention is needed.
- Severity: low
- Severity evidence: The failed grasp delays opening, but no damage, displaced unrelated objects, or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: The drawer and surrounding scene remain in place, allowing another grasp attempt without environmental resetting or human intervention.