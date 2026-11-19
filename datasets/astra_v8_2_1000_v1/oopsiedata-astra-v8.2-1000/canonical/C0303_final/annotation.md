# Episode: C0303

## Episode annotation

- Language task: unfold the towel
- Success label: failure
- Outcome evidence: The towel begins as a compact folded rectangle at frame 0 in top and right. The robot lifts and repositions fabric at frames 540–780 and 1230–1260, then opens portions further at frames 1830–1950 in left, right and top. However, frames 1998–1999 still show substantial curled and overlapping fabric rather than a fully unfolded towel. Completion is therefore unconfirmed in the observed episode, distinct from the visibly failed grasp at frames 1137–1145. No abnormal interruption or harmful side effect is established.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 1137 | No |
| 1137 | 1146 | Yes |
| 1146 | 2000 | No |

## Failure annotations

### Failure 1

- Frames: 1137-1146
- Categories: grasp
- Explanation: Following closure near the towel edge at frames 1135–1136, the gripper withdraws empty during frames 1137–1145. Left shows the fingers separating from the fabric, right shows increasing distance from the towel, and top shows the towel remaining on the table. This is an unsuccessful acquisition, not merely unfinished finger closure. A renewed approach begins at frame 1146.
- Recovery: Reopen the gripper, align around an exposed towel edge, and verify retention with a small lift before pulling the layer outward; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The missed acquisition leaves the towel on the table without visible damage or harmful displacement of surrounding objects in left, right or top.
- Resetability: immediate
- Resetability evidence: The towel remains accessible for another grasp, with no environmental reset or human assistance required.