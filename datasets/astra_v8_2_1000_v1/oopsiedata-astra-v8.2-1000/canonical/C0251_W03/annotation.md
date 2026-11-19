# Episode: C0251_W03

## Episode annotation

- Language task: Place the toys on the plate with no collisions.
- Success label: failure
- Outcome evidence: Provisionally for this window, the pink toy is acquired and transported toward the plate at frames 700–803, but released outside it and lands on the table at frames 804–814 (overhead_cam and wrist_cam). Subsequent repositioning and grasp attempts do not visibly place it on the plate; it remains beside the plate at frame 1049. This includes a visibly failed placement, not merely unconfirmed completion. Earlier context beyond frames 698–699 and later execution are unavailable; the final acquisition attempt remains unresolved.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 700 | 804 | No |
| 804 | 820 | Yes |
| 820 | 995 | No |
| 995 | 1015 | Yes |
| 1015 | 1050 | No |

## Failure annotations

### Failure 1

- Frames: 804-820
- Categories: manipulation
- Explanation: After visibly carrying the pink toy toward the plate, the robot opens its fingers while the toy is outside the plate interior at frames 804–808 (wrist_cam). The toy falls and settles on the tabletop beside the plate at frames 809–819 (overhead_cam and wrist_cam), failing the intended placement. The visible opening supports an unsuccessful release location rather than an established accidental slip.
- Recovery: Reacquire the pink toy, lift it clear of the rim, move it fully over an available area of the plate, and lower it before releasing; no human intervention is needed.
- Severity: low
- Severity evidence: The toy lands on the tabletop and remains intact; no damage or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: The toy remains accessible beside the plate, allowing another attempt without environmental resetting.

### Failure 2

- Frames: 995-1015
- Categories: grasp
- Explanation: During closure at frames 995–1006, the fingers displace and rotate the pink toy beside the plate instead of securing it (wrist_cam). The completed closure leaves its body on the tabletop, and reopening begins at frame 1015 without acquisition; overhead_cam confirms that it remains beside the plate. This is a failed grasp, distinct from the subsequent reopening and realignment.
- Recovery: Open the fingers, reposition around the toy’s body with clearance from the plate rim, and verify a secure grasp with a small controlled lift before transporting it; no human intervention is needed.
- Severity: low
- Severity evidence: The toy is displaced locally on the tabletop, with no visible damage to it, the plate, or the robot.
- Resetability: immediate
- Resetability evidence: The displaced toy remains reachable on the table; another aligned attempt needs no human reset.