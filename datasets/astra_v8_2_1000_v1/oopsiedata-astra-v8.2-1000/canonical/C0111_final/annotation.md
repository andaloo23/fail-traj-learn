# Episode: C0111

## Episode annotation

- Language task: Open the oven.
- Success label: failure
- Outcome evidence: The robot approaches the oven handle in frames 0–76 and pulls near it in frames 84–134 (left_ego_image). By frames 106–134, image shows the oven housing shifting and rotating on its support; left_ego_image still shows the glass door against the housing, without a visibly exposed opening. The observed pull displaces the appliance rather than visibly completing the task.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 103 | No |
| 103 | 135 | Yes |

## Failure annotations

### Failure 1

- Frames: 103-135
- Categories: manipulation
- Explanation: From frame 103, the pull at the handle visibly shifts the oven housing, becoming clearer in frames 106–121 (image and left_ego_image). The appliance rotates and moves relative to its support while the door remains against the housing through frame 134; the established handle interaction does not produce a visible opening.
- Recovery: Stop pulling, release the handle, and have a person reposition and stabilize the appliance before retrying a controlled pull along the door’s opening direction.
- Severity: low
- Severity evidence: The oven is displaced but remains supported on the table in frames 121–134 (image); no breakage, falling objects, or other damage is visible.
- Resetability: minor_reset
- Resetability evidence: Returning the oven to its original position and stabilizing it requires a straightforward repositioning; no repair or difficult retrieval is visibly needed.