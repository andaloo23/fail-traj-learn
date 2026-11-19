# Episode: C0218

## Episode annotation

- Language task: Pick up the orange and put it into the bowl.
- Success label: failure
- Outcome evidence: The robot lifts the orange in frames 113–127, but it falls back onto the table in frames 128–130 (right_base_cam, wrist_cam). The robot subsequently reacquires it and lifts it toward the bowl in frames 218–240 (left_base_cam, right_base_cam, wrist_cam). At frame 240 the orange is still held outside/above the bowl; placement is not visible. Thus the episode includes a visibly failed retention attempt and an unfinished recovery, not confirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 128 | No |
| 128 | 140 | Yes |
| 140 | 241 | No |

## Failure annotations

### Failure 1

- Frames: 128-140
- Categories: grasp
- Explanation: After carrying the orange above the table in frames 113–127, the gripper loses retention at frame 128; frames 129–130 show the orange separated from the fingers and back on the table (right_base_cam, wrist_cam). The empty gripper continues toward the bowl through frame 139 rather than transporting the orange. Task-directed return toward the orange begins at frame 140.
- Recovery: Return to the orange, center the fingers around it, establish a secure grasp, and verify retention with a small lift before transporting it over the bowl and releasing. No human intervention is visibly necessary.
- Severity: low
- Severity evidence: The orange falls a short distance onto the tabletop and remains accessible; no damage or meaningful damage risk is visible in right_base_cam or wrist_cam at frames 129–139.
- Resetability: immediate
- Resetability evidence: The orange remains on the unobstructed tabletop beside the bowl, allowing another acquisition attempt without environmental resetting or human intervention.