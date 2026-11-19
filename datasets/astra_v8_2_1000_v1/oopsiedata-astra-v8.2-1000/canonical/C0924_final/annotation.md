# Episode: C0924

## Episode annotation

- Language task: stack the cups
- Success label: failure
- Outcome evidence: Initially three separate upright cups are visible in head at frame 0. The right gripper lifts one cup and brings it above another, but it falls sideways during release (head and right_wrist, frames 138–150). The left gripper subsequently lifts the rear cup, but that placement also falls beside the remaining upright cup (head and left_wrist, frames 274–285). At frame 308, head shows two cups lying separately on their sides and one upright cup, with no completed stack; these are visibly failed placements, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 138 | No |
| 138 | 159 | Yes |
| 159 | 274 | No |
| 274 | 309 | Yes |

## Failure annotations

### Failure 1

- Frames: 138-159
- Categories: manipulation
- Explanation: After successfully carrying a cup over the front upright cup, the right gripper opens and the carried cup tilts away rather than nesting (head, left_wrist and right_wrist, frames 138–144). It falls onto its side and rolls toward the front of the table (head, frames 145–158), leaving the attempted stack incomplete. At frame 159 the arms begin repositioning for another attempt.
- Recovery: Reacquire and stand the fallen cup upright, then align its base centrally over the receiving cup and lower it until securely nested before releasing; human intervention is not visibly necessary.
- Severity: low
- Severity evidence: The cup falls and rolls on the tabletop; no breakage, spilled contents or other damage is visible.
- Resetability: minor_reset
- Resetability evidence: The fallen cup needs retrieval and reorientation, a straightforward reset on the accessible tabletop without visible repair requirements.

### Failure 2

- Frames: 274-309
- Categories: manipulation
- Explanation: The left gripper carries the rear cup toward the remaining upright cup, but releases it offset to the side; it tilts and falls beside the intended receiving cup instead of nesting (head and left_wrist, frames 274–280). It rolls leftward and settles on its side (head, frames 284–300), with no subsequent recovery visible through frame 308.
- Recovery: Retrieve and upright the fallen cups, then retry with the carried cup centered over the receiving opening and supported in a nested position before opening the gripper; no human intervention is visibly required.
- Severity: low
- Severity evidence: The second cup topples on the table without visible damage or spilled contents; the receiving cup remains upright.
- Resetability: minor_reset
- Resetability evidence: This failure adds another sideways cup requiring straightforward retrieval and reorientation; no inaccessible object or damaged component is visible.