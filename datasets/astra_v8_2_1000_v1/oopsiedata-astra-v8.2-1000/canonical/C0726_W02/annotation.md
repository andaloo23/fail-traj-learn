# Episode: C0726_W02

## Episode annotation

- Language task: Pick up one object from the big bowl and put it inside the small box that is empty.
- Success label: failure
- Outcome evidence: Completion is unconfirmed in this window: the separate small orange box remains empty in top at frames 350 and 699. The robot initially holds the source bowl tilted, then restores it and continues attempting to acquire the orange container inside it. At frames 668–699 in left and right, that container is visibly lifted clear of the bowl, but no placement is shown. A failed acquisition is also visible earlier when the gripper withdraws without the container at frames 447–461. Earlier context beyond frames 348–349 and later execution are unavailable; this is a provisional window outcome, not a claim of final episode failure.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 350 | 367 | Yes |
| 367 | 447 | No |
| 447 | 461 | Yes |
| 461 | 700 | No |

## Failure annotations

### Failure 1

- Frames: 350-367
- Categories: collision
- Explanation: In left and right at frames 350–366, the robot remains engaged at the orange container while the large blue bowl is held markedly tilted, preventing clean extraction and disturbing the source arrangement. The visible state matches context frames 348–349, supporting continuity across the window boundary, although the original onset and exact contact mechanism are not supplied. At frame 367 the bowl begins returning toward upright, so that recovery is excluded from this failure.
- Recovery: Gently return the bowl to stable support, disengage any contact with its rim, and realign around a single object; human assistance is needed only if the bowl cannot be safely stabilized autonomously.
- Severity: low
- Severity evidence: The bowl is tilted, but left and right at frames 350–366 show no breakage or contents spilling onto the table.
- Resetability: minor_reset
- Resetability evidence: Returning the bowl upright and checking its contents is a straightforward local reset; no repair or difficult retrieval is visibly required.

### Failure 2

- Frames: 447-461
- Categories: grasp
- Explanation: After engaging the orange container at frames 400–440 in right, the gripper pulls away empty at frames 447–460 in left and top while the container remains supported inside the bowl in right. This establishes an unsuccessful acquisition rather than merely an unfinished closing motion. By frame 461 the withdrawal ends and subsequent motion reorients toward another attempt.
- Recovery: Reopen and realign the fingers around an accessible edge of the container, close securely, and verify that it follows a small test lift before transporting it to the empty box; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The object stays inside the bowl, with no visible damage, spill, or meaningful damage risk during the empty withdrawal.
- Resetability: immediate
- Resetability evidence: The bowl and container remain accessible and supported, allowing another acquisition attempt without environmental resetting.