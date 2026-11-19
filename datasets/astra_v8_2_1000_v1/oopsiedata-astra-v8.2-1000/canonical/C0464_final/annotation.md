# Episode: C0464

## Episode annotation

- Language task: Open the drawer.
- Success label: failure
- Outcome evidence: The drawer remains closed throughout the observed episode. In wrist_image, repeated finger closures occur beside rather than securely around the silver handle, followed by empty withdrawals (frames 73–98, 143–164, 175–184, 211–224, 251–264 and 313–334). In left_ego_image, the drawer fronts remain flush at frames 0, 164, 264 and 399; image also shows the robot withdrawing without opening the drawer. These are visibly unsuccessful acquisitions, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 73 | No |
| 73 | 98 | Yes |
| 98 | 143 | No |
| 143 | 164 | Yes |
| 164 | 175 | No |
| 175 | 184 | Yes |
| 184 | 211 | No |
| 211 | 224 | Yes |
| 224 | 251 | No |
| 251 | 264 | Yes |
| 264 | 313 | No |
| 313 | 334 | Yes |
| 334 | 400 | No |

## Failure annotations

### Failure 1

- Frames: 73-98
- Categories: grasp
- Explanation: In wrist_image at frame 73, the fingers have closed beside the handle without enclosing it. The gripper subsequently withdraws empty at frames 89–97 while the drawer stays closed in left_ego_image.
- Recovery: Reopen the fingers, align them around the protruding handle, and verify acquisition before pulling along the drawer travel direction; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The attempt does not open the drawer; no damage or displacement of unrelated objects is visible.
- Resetability: immediate
- Resetability evidence: The drawer and handle remain in place, allowing another attempt without environmental resetting.

### Failure 2

- Frames: 143-164
- Categories: grasp
- Explanation: Following a renewed approach, wrist_image shows another completed closure offset from the handle at frames 143–148, followed by an empty withdrawal at frames 159–163. left_ego_image shows no drawer opening.
- Recovery: Reposition the open gripper so the handle lies between the fingers, then confirm a secure grasp before pulling; human intervention is not required by the visible state.
- Severity: low
- Severity evidence: Only unsuccessful acquisition is established; no visible damage results.
- Resetability: immediate
- Resetability evidence: No objects require replacement or repositioning before another attempt.

### Failure 3

- Frames: 175-184
- Categories: grasp
- Explanation: In wrist_image at frames 175–178, the fingers close next to the silver handle and then move away empty at frames 179–183. The drawer remains flush in left_ego_image.
- Recovery: Correct the lateral and depth alignment around the handle rather than repeating the offset closure; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The missed acquisition prevents progress but produces no visible damage or harmful side effect.
- Resetability: immediate
- Resetability evidence: The unchanged drawer remains available for an immediate reattempt.

### Failure 4

- Frames: 211-224
- Categories: grasp
- Explanation: wrist_image shows closed fingers beside the handle at frames 211–217, followed by separation from the handle without drawer movement at frames 218–223. left_ego_image confirms the drawer stays closed.
- Recovery: Open and realign the fingers around the handle, checking engagement before attempting an outward pull; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: No meaningful damage or scene disruption is visible.
- Resetability: immediate
- Resetability evidence: The failed grasp leaves the environment unchanged and requires no reset.

### Failure 5

- Frames: 251-264
- Categories: grasp
- Explanation: The renewed closure at frames 251–257 in wrist_image again fails to capture the handle. At frames 258–263 the gripper withdraws empty, while left_ego_image shows the drawer remaining closed.
- Recovery: Use the visible handle position to correct the grasp pose and verify capture before pulling; human assistance is not visibly required.
- Severity: low
- Severity evidence: The consequence is another unsuccessful attempt, with no visible damage.
- Resetability: immediate
- Resetability evidence: The handle and drawer retain their original usable positions.

### Failure 6

- Frames: 313-334
- Categories: grasp
- Explanation: In wrist_image at frames 313–318, the fingers finish closing away from the handle, which remains outside the grasp. The robot then retreats empty through frame 333; left_ego_image shows no opening of the drawer.
- Recovery: Return with an open gripper and a corrected handle-centered pose, verify engagement, and pull straight outward; no human intervention is established as necessary.
- Severity: low
- Severity evidence: The task remains incomplete, but no damage, tipping or disturbance of nearby objects is visible.
- Resetability: immediate
- Resetability evidence: The drawer remains closed and intact, so another attempt needs no environmental intervention.