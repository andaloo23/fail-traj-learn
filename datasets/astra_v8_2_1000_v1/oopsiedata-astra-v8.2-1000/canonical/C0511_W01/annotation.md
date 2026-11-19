# Episode: C0511_W01

## Episode annotation

- Language task: Seperate the food and the toys into the two bowls.
- Success label: failure
- Outcome evidence: Provisional for this window: the robot places the pink plush toy in the green bowl at frames 126–130, then places the orange-shaped food item in that same bowl at frames 281–290 (overhead_cam and wrist_cam), mixing rather than separating the categories. At frame 349, other items remain on the table and the second bowl is still empty in overhead_cam. Later context is absent, so eventual completion or correction is unconfirmed; the mixed placement is a visible semantic failure.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 281 | No |
| 281 | 291 | Yes |
| 291 | 350 | No |

## Failure annotations

### Failure 1

- Frames: 281-291
- Categories: sequencing_semantic
- Explanation: At frames 281–284, wrist_cam and overhead_cam show the robot releasing the orange-shaped food item into the green bowl already containing the pink plush toy; both remain together through frame 290. The orange item has a visible green leaf/stem during acquisition (wrist_cam, frames 200–223), supporting its food identity. Acquisition and transport succeed physically, but this placement mixes the categories contrary to the task. From frame 291 onward the robot withdraws and approaches another tabletop item; the incorrect arrangement persists, but that alone does not extend the failing action.
- Recovery: Transfer the orange-shaped food item to the other bowl, retain the green bowl for toys, and continue sorting consistently; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The consequence is incorrect sorting; both objects remain contained in the intact bowl, with no visible damage or meaningful damage risk.
- Resetability: minor_reset
- Resetability evidence: Correcting the arrangement requires one straightforward transfer of the misplaced item to the other bowl, which is accessible; no repair or substantial scene reset is indicated.