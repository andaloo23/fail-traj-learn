# Episode: C0527

## Episode annotation

- Language task: Pick basketball and place in blue bowl.
- Success label: failure
- Outcome evidence: In exterior_cam, the basketball remains outside the bowl after unsuccessful acquisitions at frames 89–107 and 149–159. It is subsequently carried at frames 217–239 but falls from the gripper at frames 240–243 and rolls out of view by frame 250. Later empty-gripper movements toward the bowl do not deliver it; the bowl remains visibly empty at frames 505 and 599. This is a visibly failed attempt, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 89 | No |
| 89 | 108 | Yes |
| 108 | 149 | No |
| 149 | 169 | Yes |
| 169 | 240 | No |
| 240 | 257 | Yes |
| 257 | 300 | No |
| 300 | 600 | Yes |

## Failure annotations

### Failure 1

- Frames: 89-108
- Categories: grasp
- Explanation: In exterior_cam at frames 89–96, the basketball moves out from the fingers rather than being securely lifted; by frames 97–107 it rolls across the table while the gripper remains empty. The acquisition fails to advance the transfer to the bowl.
- Recovery: Track the ball until it settles, recenter the open fingers around it, and verify a secure grasp with a small lift before transporting it; no human intervention is needed.
- Severity: low
- Severity evidence: The ball remains on the tabletop, with no visible damage or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The ball is still accessible on the table and can be approached again without environmental intervention.

### Failure 2

- Frames: 149-169
- Categories: grasp
- Explanation: In exterior_cam at frames 149–153, the gripper withdraws upward without the basketball after the second acquisition attempt. Frames 154–168 show the ball still on the table beneath the empty fingers.
- Recovery: Reopen and realign the fingers around the ball, close securely, and confirm that the ball follows a short test lift; no human intervention is needed.
- Severity: low
- Severity evidence: Only acquisition is prevented; no damage or hazardous displacement is visible.
- Resetability: immediate
- Resetability evidence: The ball remains upright and reachable on the table, requiring no reset before another attempt.

### Failure 3

- Frames: 240-257
- Categories: grasp
- Explanation: After visible transport with the basketball in exterior_cam at frames 217–239, the ball separates from the fingers at frame 240, falls onto the table at frames 241–243, and rolls beyond the lower image boundary by frame 250. It is not retained or delivered to the bowl; whether it subsequently leaves the table is not visible.
- Recovery: Stop transport and locate the ball before further motion. Reacquire it only if it is safely reachable; otherwise have a person retrieve and return it after the robot is stopped.
- Severity: low
- Severity evidence: A dropped ball and interrupted transfer are visible, but no damage or concrete substantial damage risk is established; its final resting location is unseen.
- Resetability: minor_reset
- Resetability evidence: Returning the ball to a known reachable tabletop position would be a straightforward reset, although its off-camera resting location makes the exact retrieval effort uncertain.

### Failure 4

- Frames: 300-600
- Categories: sequencing_semantic
- Explanation: In exterior_cam at frames 300–350, the robot returns toward the bowl with an empty gripper rather than recovering the basketball. It continues empty-handed motions, including lowering the fingers around the bowl at frames 477–505 and contacting and shifting the bowl at frames 585–599. These actions do not accomplish the required ball transfer.
- Recovery: Stop the empty-handed placement sequence, locate and restore the basketball to a safe reachable position, then grasp it and transport it over the bowl before releasing; human retrieval is needed if the ball cannot be safely reached.
- Severity: low
- Severity evidence: The bowl is slightly displaced but remains on the table, and no damage is visible.
- Resetability: immediate
- Resetability evidence: These empty-handed actions add no substantial reset requirement; the bowl remains usable in its shifted position. Retrieval of the missing ball is a consequence of the preceding drop, not this segment.