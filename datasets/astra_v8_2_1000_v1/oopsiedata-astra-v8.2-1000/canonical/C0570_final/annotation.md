# Episode: C0570

## Episode annotation

- Language task: Close the oven.
- Success label: failure
- Outcome evidence: The oven door is open at frame 0 in image and left_ego_image. The arm gradually approaches the door area through frames 100–263, with wrist_image showing the nearby door rim and oven contents, but no closing rotation is visible. At frames 300 and 399 in image and left_ego_image, the door remains lowered and the oven remains open. Completion is not merely unconfirmed: the visible final state is still open, following sustained inactivity.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 264 | No |
| 264 | 400 | Yes |

## Failure annotations

### Failure 1

- Frames: 264-400
- Categories: task_not_attempted
- Explanation: After approaching the oven, the robot remains essentially stationary near the open door from frame 264 through frame 399 without visibly lifting or closing it. image and left_ego_image show the unchanged lowered door at frames 264, 300, 350 and 399; wrist_image likewise shows no meaningful further progress. This sustained stall does not advance the task. Secure acquisition of the door is not established, so a grasp or post-contact manipulation failure is not inferred.
- Recovery: Reobserve the door and handle, establish a suitable grasp or supported contact, and guide the door upward along its hinge motion while checking clearance; verify closure afterward. No human intervention is visibly required.
- Severity: low
- Severity evidence: The oven remains open, but no damage, displaced unrelated objects or concrete risk of damage is visible.
- Resetability: immediate
- Resetability evidence: The scene remains usable and the door remains accessible in its open position; the robot can reposition and reattempt without an environmental reset or human intervention.