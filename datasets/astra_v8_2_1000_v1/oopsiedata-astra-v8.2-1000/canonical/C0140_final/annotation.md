# Episode: C0140

## Episode annotation

- Language task: stack the bowls
- Success label: failure
- Outcome evidence: The bowls begin separate (top, frame 0) and remain separate at the end (left, right and top, frames 1980–1999). The robot places an unrelated orange, green-stemmed object into the turquoise bowl (left and right, frames 780–880), then acquires and repositions that bowl without completing a stack (right and top, frames 990–1795). Completion is unconfirmed, with no visibly failed stacking contact, drop or damage; wrong-object handling and sustained stalls are observable local failures. The recording ending does not establish abnormal termination.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 350 | Yes |
| 350 | 481 | No |
| 481 | 880 | Yes |
| 880 | 1795 | No |
| 1795 | 2000 | Yes |

## Failure annotations

### Failure 1

- Frames: 0-350
- Categories: task_not_attempted
- Explanation: The bowls and grippers remain essentially stationary without discernible stacking progress for approximately 11.6 seconds (left, right and top, frames 0, 150, 300 and 349). This is sustained inactivity rather than an ordinary brief pause. Approach movements follow (frames 350–420); the precise transition from inactivity to movement is gradual.
- Recovery: Begin a bowl-directed approach, securely acquire one bowl, and align it over the other for stacking; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The consequence is delayed task progress; no damage, spill or harmful displacement is visible.
- Resetability: immediate
- Resetability evidence: Both bowls remain upright and accessible, with no environmental reset needed before attempting the task.

### Failure 2

- Frames: 481-880
- Categories: sequencing_semantic
- Explanation: The robot repeatedly interacts with the unrelated orange, green-stemmed object rather than stacking bowls (right, frames 481–690), then visibly carries it and deposits it in the turquoise bowl (left and right, frames 750–880). The later transport clarifies this as one continuous wrong-object interaction across frame 700, not a new failure at that window boundary. Secure acquisition during the earlier contacts is uncertain, but controlled transport and placement are visible later. Bowl-directed handling follows the release.
- Recovery: Set the held bowl down if necessary, remove the orange object to a clear tabletop location, then securely grasp and align the bowls for stacking; no human intervention is visibly required.
- Severity: low
- Severity evidence: An unrelated object is relocated into a bowl, but no breakage, spill or meaningful damage risk is visible.
- Resetability: minor_reset
- Resetability evidence: Restoring the clear-bowl state requires straightforward removal of the orange object; the object and bowls remain accessible.

### Failure 3

- Frames: 1795-2000
- Categories: task_not_attempted
- Explanation: Following bowl-position adjustments, the robot holds essentially the same separated-bowl configuration for approximately 6.8 seconds without advancing stacking (right and top, frames 1795, 1830, 1920 and 1999). The left view changes gradually, but neither bowl moves into a completed stack. This supports sustained stalling, not a failed grasp or placement; the exact settling boundary is approximate and the hidden cause is unknown.
- Recovery: Securely support the turquoise bowl, clear its unrelated contents as needed, and resume transport into unobstructed stacking alignment with the pale bowl; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: This stall delays completion without visible damage, dropping or harmful collision.
- Resetability: immediate
- Resetability evidence: The stall itself introduces no additional environmental disturbance requiring reset; the robot can resume from its current configuration, with the earlier orange-object relocation accounted for separately.