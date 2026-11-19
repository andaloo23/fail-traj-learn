# Episode: C0984

## Episode annotation

- Language task: put the corn in the pot
- Success label: failure
- Outcome evidence: In right_shoulder_cam, the robot grasps and lifts the corn in frames 27–41, then carries it toward the pot in frames 42–71. At frame 72 it releases the corn outside the pot; frames 73–75 show the corn moving toward and beyond the lower image boundary while the pot remains empty. This is a visibly failed placement, not merely unconfirmed completion; the corn’s final resting location is not visible.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 72 | No |
| 72 | 76 | Yes |

## Failure annotations

### Failure 1

- Frames: 72-76
- Categories: manipulation
- Explanation: After successfully carrying the corn, the robot opens its gripper at frame 72 in right_shoulder_cam and the corn falls outside the pot. It lands on the tabletop in front of the pot at frame 73 and moves out of view by frame 75, leaving the intended container empty.
- Recovery: Locate the corn before retrying, reacquire it if safely reachable, and align it fully within the pot opening before lowering and releasing it. Human retrieval is needed if its unseen resting location is outside the robot’s safe reach.
- Severity: low
- Severity evidence: The visible consequence is a failed placement and displaced corn; no damage or meaningful damage risk is established in frames 72–75, although its final resting location is unseen.
- Resetability: minor_reset
- Resetability evidence: Retrieving and returning the displaced corn to a reachable tabletop position would allow another attempt; the final location is outside the camera view, so the exact retrieval effort and need for human assistance remain uncertain.