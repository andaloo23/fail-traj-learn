# Episode: C0055

## Episode annotation

- Language task: Stack the yellow block onto the blue one.
- Success label: failure
- Outcome evidence: The robot acquires and lifts the yellow block in frames 69–95 (wrist_cam and right_base_cam), then lowers and releases it beside the blue block rather than on top in frames 130–145. Frames 160–178 in wrist_cam clearly show the blocks separately resting on the table; left_base_cam and right_base_cam confirm that they remain unstacked through frame 213. This is a visibly unsuccessful placement, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 137 | No |
| 137 | 145 | Yes |
| 145 | 214 | No |

## Failure annotations

### Failure 1

- Frames: 137-145
- Categories: manipulation
- Explanation: After transporting the yellow block, the robot opens its fingers and leaves it on the tabletop beside the blue block in frames 137–144 (wrist_cam and right_base_cam), rather than supported on top of it. The subsequent clear views in frames 160–178 confirm the failed placement. The images do not establish a hidden cause for the placement error.
- Recovery: Reacquire the yellow block, lift it clear of the table, align it over the blue block’s top surface, and lower it onto that surface before releasing and checking stability; no human intervention is needed.
- Severity: low
- Severity evidence: The yellow block remains on the tabletop, with no visible damage or meaningful damage risk; the consequence is an incomplete stack.
- Resetability: immediate
- Resetability evidence: Both blocks remain accessible and intact on the table, so another grasp-and-place attempt requires no environmental reset or human intervention.