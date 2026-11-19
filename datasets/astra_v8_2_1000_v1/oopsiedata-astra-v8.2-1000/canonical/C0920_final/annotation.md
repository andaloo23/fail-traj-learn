# Episode: C0920

## Episode annotation

- Language task: Pick basketball and place in blue bowl.
- Success label: failure
- Outcome evidence: In exterior_cam, the robot lifts the basketball (frames 85–116), but it falls onto the tabletop outside the bowl at frames 117–123. The robot reacquires it around frames 200–210, then carries it toward the foreground rather than into the blue bowl (frames 225–248). The ball disappears below the image boundary as the gripper opens around frames 249–253; its final resting location is not visible. Frames 286–290 show the blue bowl without a visible basketball. Placement is not confirmed, and the earlier drop is a visibly failed attempt.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 117 | No |
| 117 | 125 | Yes |
| 125 | 225 | No |
| 225 | 254 | Yes |
| 254 | 291 | No |

## Failure annotations

### Failure 1

- Frames: 117-125
- Categories: grasp
- Explanation: In exterior_cam, the previously held basketball separates from the gripper at frame 117 and falls and bounces on the table at frames 118–123, well outside the blue bowl. This loses the acquired object before placement; the images do not establish whether release was commanded or accidental.
- Recovery: Let the ball settle, realign the gripper, reacquire it securely, and transport it above the bowl before releasing; human intervention is not needed for the visible tabletop state.
- Severity: low
- Severity evidence: The ball lands on the clear tabletop without visible damage or disruption to other objects.
- Resetability: immediate
- Resetability evidence: The basketball remains accessible on the tabletop, so another acquisition can be attempted without environmental resetting.

### Failure 2

- Frames: 225-254
- Categories: sequencing_semantic
- Explanation: In exterior_cam, frames 225–248 show the held basketball being transported farther into the foreground, away from the blue bowl's location. Around frames 249–253, the gripper opens at the lower image boundary and the ball disappears from view instead of being placed in the bowl. Its landing location is not established.
- Recovery: Locate the basketball before further movement, then reacquire it and verify alignment above the blue bowl before release. Human assistance may be needed if the ball is outside the robot's safely reachable workspace.
- Severity: low
- Severity evidence: No damage or collision is visible; the supported consequence is an unsuccessful transfer. The ball's off-camera landing and condition remain uncertain.
- Resetability: minor_reset
- Resetability evidence: Returning the ball to a known reachable tabletop position may require a simple retrieval by a person; its final location is hidden, so the exact intervention is uncertain.