# Episode: C0301_W01

## Episode annotation

- Language task: Seperate the food and the toys into the two bowls.
- Success label: failure
- Outcome evidence: Provisional for this window: sorting is not completed. In overhead_cam and wrist_cam, frames 140–151 show the gripper closing near the carrot-shaped item, but frames 160–175 show it withdrawing while the food items remain on the table. It subsequently opens without depositing an item (frames 208–215). By frames 330–349, it is approaching the pink toy, with no completed acquisition yet visible. Later episode context is absent; overall completion is unconfirmed, independently of the visible failed acquisition.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 152 | No |
| 152 | 211 | Yes |
| 211 | 350 | No |

## Failure annotations

### Failure 1

- Frames: 152-211
- Categories: grasp
- Explanation: After closing near the carrot-shaped item in wrist_cam at frames 140–151, the robot begins withdrawing at frame 152 without acquiring it. Frames 160–175 in overhead_cam and wrist_cam show the gripper moving away while the carrot and adjacent food items remain on the tabletop. It continues an empty transfer toward the bowl area and opens at frames 208–210, making no sorting progress. Repositioning with the open gripper begins at frame 211; the images do not establish the underlying cause of the miss.
- Recovery: Reposition the open gripper around a clearly isolated target, descend to an appropriate grasp height, and verify that the item lifts with the gripper before transferring it to its assigned bowl; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The attempted acquisition leaves the items on the table, with no visible damage, spill, or meaningful damage risk in overhead_cam or wrist_cam.
- Resetability: immediate
- Resetability evidence: The target remains accessible on the tabletop and the bowls remain upright; another aligned grasp can be attempted without environmental resetting or human intervention.