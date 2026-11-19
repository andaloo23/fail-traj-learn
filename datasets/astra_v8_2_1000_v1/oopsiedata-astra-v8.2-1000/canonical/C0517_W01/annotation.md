# Episode: C0517_W01

## Episode annotation

- Language task: fold the shorts
- Success label: success but suboptimal
- Outcome evidence: Provisional for this window: the shorts start spread out at frame 0 (top). After an unsuccessful right-gripper acquisition, the robot repositions and acquires the fabric, lifts the near side, and brings it over the opposite side at frames 220–329 (left, right, top). Both grippers open at frames 330–338, leaving the shorts folded in half on the table through frame 349 (top; overlapping fabric edges also visible in left and right). Later episode context is not supplied, so any further intended folding or refinement is unknown.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 140 | No |
| 140 | 154 | Yes |
| 154 | 350 | No |

## Failure annotations

### Failure 1

- Frames: 140-154
- Categories: grasp
- Explanation: Following closure beside the hem at frames 128–139 (right), the right gripper moves away without carrying the fabric at frames 140–153; a gap develops between it and the shorts in top while the hem remains outside the closed fingers in right. The left gripper retains its fabric corner (left). This unsuccessful right-side acquisition delays the coordinated fold; reopening and renewed approach begin at frame 154.
- Recovery: Open and realign the right gripper around the visible hem, close on the fabric, and verify retention with a small lift before continuing the coordinated fold; no human intervention is needed.
- Severity: low
- Severity evidence: The missed acquisition only delays the fold; the shorts remain on the tabletop, with no visible damage or harmful collision in left, right, or top.
- Resetability: immediate
- Resetability evidence: The fabric remains accessible and the left corner remains controlled, so the right gripper can reattempt directly without an environmental or human reset.