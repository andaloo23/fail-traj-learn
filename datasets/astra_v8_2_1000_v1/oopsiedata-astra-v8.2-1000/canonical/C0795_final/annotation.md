# Episode: C0795

## Episode annotation

- Language task: Move the left stuffed toy to the largest bowl.
- Success label: failure
- Outcome evidence: In image_primary, frame 0 shows the blue-and-white stuffed toy on the left and the largest, white bowl near the back center. The robot instead manipulates the pink-and-brown toy on the right (frames 14–64 and 75–90), which falls back onto the tabletop at frames 65–66 and 91–93. At frame 99, the intended left toy remains unmoved and the white bowl contains neither toy; this is a visibly task-inconsistent attempt, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 14 | No |
| 14 | 100 | Yes |

## Failure annotations

### Failure 1

- Frames: 14-100
- Categories: sequencing_semantic, grasp
- Explanation: In image_primary, the gripper begins contacting and displacing the right pink-and-brown toy at frame 14 rather than acquiring the left blue-and-white toy. It repeatedly works on that wrong object throughout the remaining episode. It withdraws empty at frames 39–40, later lifts the wrong toy at frames 58–64 before it falls onto the table at frames 65–66, and lifts it again at frames 86–90 before another fall at frames 91–93. These unsuccessful acquisitions and retention failures occur within a continuous wrong-object attempt; the intended toy remains untouched through frame 99.
- Recovery: Stop manipulating the pink-and-brown toy, leave it safely supported on the table, and acquire the left blue-and-white toy instead. Verify secure retention before transporting it over the largest white bowl and releasing it inside; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The wrong soft toy is displaced and falls onto the tabletop, but no damage or meaningful damage risk is visible in image_primary through frame 99.
- Resetability: immediate
- Resetability evidence: The intended toy and destination bowl remain accessible and usable, so the robot can immediately attempt the correct task without a human reset; restoring the unrelated toy’s exact original position is not necessary for task completion.