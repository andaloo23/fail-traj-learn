# Episode: C0016

## Episode annotation

- Language task: Pack the cups with a single arm.
- Success label: failure
- Outcome evidence: In base_image, the arm acquires the light-colored cup at frames 40–48 and brings it over the blue cups at frames 74–90 and 100–120, apparently attempting to consolidate them. At frames 127–134, the lifted cups tip and fall onto their sides rather than remaining securely held or packed; one blue cup remains separate on the table at frame 139. Packing is not visibly completed, and the ending shows an actual loss of control, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 127 | No |
| 127 | 140 | Yes |

## Failure annotations

### Failure 1

- Frames: 127-140
- Categories: grasp
- Explanation: In base_image at frame 127, the lifted cup assembly begins tipping out of its previously aligned position beneath the gripper. Frames 128–134 show the cups falling and settling sideways on the table, while another blue cup remains separate. This loss of retention disrupts the attempted consolidation and leaves the cups unpacked through frame 139.
- Recovery: Withdraw the gripper clear of the fallen cups, reassess their positions, and reacquire and orient them individually before resuming packing with a secure grasp; human intervention is not visibly necessary.
- Severity: low
- Severity evidence: The cups fall onto the tabletop, with no visible breakage, spill, or damage to the robot or surrounding scene.
- Resetability: minor_reset
- Resetability evidence: The fallen cups need straightforward repositioning or reorientation for another attempt; they remain accessible on the table, with no repair or difficult retrieval visibly required.