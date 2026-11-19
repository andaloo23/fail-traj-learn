# Episode: C0929

## Episode annotation

- Language task: Pick green block and place on cardboard.
- Success label: failure
- Outcome evidence: In exterior_cam, the block starts on the bare table beside the cardboard (frame 0), remains behind during early empty withdrawals (frames 51–69 and 159–174), and later falls from the gripper onto the bare table (frames 475–482). The robot subsequently reacquires it and moves toward the cardboard (frames 577–599), but a completed release and stable placement are not visible. Final completion is unconfirmed, separately from the visibly unsuccessful earlier attempts.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 51 | No |
| 51 | 70 | Yes |
| 70 | 159 | No |
| 159 | 175 | Yes |
| 175 | 305 | No |
| 305 | 320 | Yes |
| 320 | 475 | No |
| 475 | 483 | Yes |
| 483 | 600 | No |

## Failure annotations

### Failure 1

- Frames: 51-70
- Categories: grasp
- Explanation: After closing near the block, the gripper lifts away empty while the green block remains on the table in exterior_cam, frames 51–69; the acquisition did not succeed.
- Recovery: Reopen, align the fingers around the block at its actual tabletop position, and verify retention with a short lift before transport; no human intervention is needed.
- Severity: low
- Severity evidence: The block remains on the usable tabletop, with no visible damage or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: Neither the block nor the cardboard requires environmental resetting before another attempt.

### Failure 2

- Frames: 159-175
- Categories: grasp
- Explanation: Following another near-block closing motion, the gripper withdraws upward without the block; exterior_cam frames 159–174 show the target remaining on the table rather than following the gripper.
- Recovery: Adjust the grasp position and finger orientation, descend around the block, and confirm a secure acquisition before withdrawing; human intervention is not required.
- Severity: low
- Severity evidence: The failed acquisition prevents progress but produces no visible damage.
- Resetability: immediate
- Resetability evidence: The target remains accessible on the table for an autonomous retry.

### Failure 3

- Frames: 305-320
- Categories: grasp
- Explanation: The gripper withdraws from another acquisition attempt while the green block remains separately visible on the tabletop in exterior_cam, frames 305–319; it has not secured the target.
- Recovery: Locate the block's slightly changed position, reopen and realign the gripper, and retry with a verified short lift; no human intervention is needed.
- Severity: low
- Severity evidence: Only a small tabletop displacement and unsuccessful acquisition are visible; no damage is established.
- Resetability: immediate
- Resetability evidence: The block remains reachable and the scene is still valid for another attempt without resetting.

### Failure 4

- Frames: 475-483
- Categories: grasp
- Explanation: After the green block has moved with the gripper, it separates and falls onto the bare table in exterior_cam frames 475–482, away from the cardboard. Whether this resulted from slipping or opening is not established, but retention through placement failed.
- Recovery: Reacquire the block from its new tabletop position, verify a secure hold, and transport it over the cardboard before lowering and releasing; no human intervention is needed.
- Severity: low
- Severity evidence: The block falls a short distance onto the clear tabletop and remains there; no damage or consequential collision is visible.
- Resetability: immediate
- Resetability evidence: The fallen block remains accessible on the work surface, so another attempt does not require a human reset.