# Episode: C0091

## Episode annotation

- Language task: pick up the red block and place it in the bowl
- Success label: failure
- Outcome evidence: The robot approaches the block and moves its fingers near it in frames 40–169 (cam_2_scene, cam_3_wrist, cam_4_wrist), but no lift or transfer is visible. In frames 170–271, the robot remains essentially stationary with the block outside the bowl. Completion is unconfirmed, with a visible sustained stall rather than a confirmed failed lift. Frame 0 wrist panels show a different block/bowl arrangement from cam_2_scene and subsequent wrist frames; this isolated inconsistency does not establish completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 170 | No |
| 170 | 272 | Yes |

## Failure annotations

### Failure 1

- Frames: 170-272
- Categories: task_not_attempted
- Explanation: Following approach and finger movement, the robot remains essentially stationary beside the block for approximately five seconds through the end of the episode; frames 170, 200, 240 and 271 in cam_2_scene, cam_3_wrist and cam_4_wrist show no lifting or transport toward the bowl. This sustained lack of progress establishes stalling, but does not establish failed retention, a hardware fault or abnormal termination.
- Recovery: Reassess the block’s position relative to the fingers, reopen and realign if necessary, then acquire the block and verify a stable lift before transporting it into the bowl; no human intervention is visibly required.
- Severity: low
- Severity evidence: The block remains on the table outside the bowl, with no visible damage, spill or other harmful consequence in frames 170–271.
- Resetability: immediate
- Resetability evidence: The block and bowl remain accessible and the environment requires no visible resetting or human intervention before another attempt.
