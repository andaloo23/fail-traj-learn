# Episode: C0253

## Episode annotation

- Language task: pick up the red block and put it in the bowl
- Success label: failure
- Outcome evidence: In cam_2_scene, the robot approaches the red block beside the bowl during frames 30–110; cam_3_wrist shows the fingers closing around its vicinity and the block rotating during frames 114–140. From approximately frame 144 through frame 342, the robot and block remain essentially stationary outside the bowl, with no transfer or release into it visible. Completion is unconfirmed, and sustained stalling is visible; a failed acquisition or loss of possession is not established. The initial bowl-containing-block imagery in cam_3_wrist and cam_4_wrist at frame 0 conflicts with cam_2_scene and the subsequent views, so it does not establish task completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 144 | No |
| 144 | 343 | Yes |

## Failure annotations

### Failure 1

- Frames: 144-343
- Categories: task_not_attempted
- Explanation: Following the approach and finger closure, the robot stalls beside the bowl for roughly ten seconds. Frames 144, 200, 280 and 342 in cam_2_scene and cam_3_wrist show essentially unchanged gripper and block positions, with no lift or transport toward the bowl. This sustained inactivity does not advance the task; the images do not establish whether the block is securely held or why movement stopped.
- Recovery: Verify whether the block is securely grasped; if not, reopen and realign the fingers for acquisition, then lift and transfer the block into the bowl. No visible environmental condition requires human intervention.
- Severity: low
- Severity evidence: The task remains incomplete, but no damage, spill, harmful collision or concrete risk of damage is visible.
- Resetability: immediate
- Resetability evidence: The block and bowl remain accessible on the usable tabletop, with no visible cleanup or physical scene reset needed before resuming or reattempting acquisition.