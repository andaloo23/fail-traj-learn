# Episode: C0170

## Episode annotation

- Language task: Stack all the bowls on the table into the middle bowl.
- Success label: failure
- Outcome evidence: Frame 0 (head) shows blue, middle pink, and orange bowls separately. The orange bowl is placed into the pink bowl by frames 133–150 (head, right_wrist). The blue-bowl placement misses and destabilizes that stack at frames 225–252 (head, left_wrist, right_wrist). At frame 383 (head), the blue bowl remains separate from the orange-in-pink stack, so the task is visibly incomplete following a failed placement, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 225 | No |
| 225 | 254 | Yes |
| 254 | 317 | No |
| 317 | 330 | Yes |
| 330 | 384 | No |

## Failure annotations

### Failure 1

- Frames: 225-254
- Categories: manipulation
- Explanation: After carrying the blue bowl toward the stack, the robot releases it off-center rather than nesting it; frames 225–234 (head, left_wrist, right_wrist) show the blue bowl beside the stack and the orange/pink pair tipping. The bowls continue rocking and separating through frame 253, defeating the placement. This follows established transport of the blue bowl at frames 194–220.
- Recovery: Wait for the bowls to settle, verify that the orange/pink stack is upright, then securely regrasp the blue bowl and lower it centrally into the stack before releasing; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The empty bowls rock and shift on the tabletop, but no breakage, spill, or meaningful damage is visible.
- Resetability: immediate
- Resetability evidence: All bowls remain accessible on the table, and the orange/pink pair settles upright; an autonomous retry needs no environmental intervention.

### Failure 2

- Frames: 317-330
- Categories: grasp
- Explanation: Following the renewed blue-bowl acquisition attempt at frames 289–316 (head, left_wrist), the left gripper lifts and withdraws empty at frames 317–329 while the blue bowl remains on the table. This establishes unsuccessful acquisition rather than an unfinished finger-closing motion.
- Recovery: Reopen the gripper, align its fingers across the blue bowl’s rim, close securely, and verify that the bowl follows a short lift before transporting it; no human intervention is needed.
- Severity: low
- Severity evidence: The failed acquisition leaves the bowl on the table without visible damage or disruption to unrelated objects.
- Resetability: immediate
- Resetability evidence: The blue bowl remains upright and reachable, allowing another grasp attempt without a human reset.