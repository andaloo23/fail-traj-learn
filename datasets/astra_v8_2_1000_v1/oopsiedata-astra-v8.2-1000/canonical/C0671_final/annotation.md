# Episode: C0671

## Episode annotation

- Language task: put the sushi in the pot
- Success label: failure
- Outcome evidence: The orange-topped, white-rice sushi remains on the table rather than entering the pot (left and wrist, frames 0–103). The gripper instead closes around the neighboring yellow waffle-cone-shaped object at frames 89–98 and begins lifting it at frames 99–103 (wrist, corroborated by left). This is a visible wrong-object attempt, not merely unconfirmed placement; no sushi transfer to the pot is observed.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 89 | No |
| 89 | 104 | Yes |

## Failure annotations

### Failure 1

- Frames: 89-104
- Categories: sequencing_semantic
- Explanation: At frame 89, the gripper closes around the yellow waffle-cone-shaped object while the orange-and-white sushi remains beside it (wrist). Through frames 99–103, the cone stays between the fingers as the arm rises and the sushi recedes in the wrist view, with the sushi still on the table in left. Acquiring this unrelated object does not advance putting the sushi in the pot.
- Recovery: Lower and release the cone safely onto the table, then align the open gripper around the orange-and-white sushi, verify acquisition, and transfer it into the pot. No human intervention is visibly necessary.
- Severity: low
- Severity evidence: The wrong object is acquired, but neither camera shows damage, a spill, or a meaningful damage hazard through frame 103.
- Resetability: immediate
- Resetability evidence: No environmental repair or human reset is indicated; the robot can set the cone down and reattempt acquisition of the accessible sushi.