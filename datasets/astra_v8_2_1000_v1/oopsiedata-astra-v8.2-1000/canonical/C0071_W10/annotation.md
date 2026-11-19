# Episode: C0071_W10

## Episode annotation

- Language task: Clean the table by placing the cans in the upper tray and the bowls in the tray on the right.
- Success label: failure
- Outcome evidence: In base_image frames 3150, 3325, and 3499, the cans are in the upper blue tray, but both bowls remain on the tabletop and the right red tray remains empty. No discernible task-directed movement occurs during this approximately 3.5-second window. Completion is unconfirmed, rather than a new visibly failed grasp. This outcome is provisional; earlier execution beyond the two context frames and later execution are unavailable.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 3150 | 3500 | Yes |

## Failure annotations

### Failure 1

- Frames: 3150-3500
- Categories: task_not_attempted
- Explanation: Across base_image frames 3150–3499, the visible robot parts and objects remain stationary, with neither bowl approached or transferred to the empty right tray. This sustained lack of discernible task activity does not advance the unfinished task. The two preceding context frames show the same state, but the onset before this window and continuation afterward are unresolved; the prior No label does not establish that this longer stationary interval is productive. No hidden cause or abnormal termination is established.
- Recovery: Resume task-directed acquisition of a bowl, verify a secure grasp, and place it in the right tray, then repeat for the remaining bowl; no environmental human intervention is visibly needed.
- Severity: low
- Severity evidence: The visible consequence is lack of progress; base_image frames 3150 and 3499 show no displaced objects, damage, or supported damage risk.
- Resetability: immediate
- Resetability evidence: Both bowls remain upright and accessible on the tabletop, and the destination tray is empty; no physical scene reset is needed before resuming.