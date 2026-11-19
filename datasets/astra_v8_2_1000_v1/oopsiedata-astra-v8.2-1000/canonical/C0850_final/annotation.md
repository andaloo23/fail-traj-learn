# Episode: C0850

## Episode annotation

- Language task: Seperate the food and the toys into the two bowls.
- Success label: failure
- Outcome evidence: wrist_cam shows the pink toy in the purple bowl at frame 270, then the carrot deposited alongside it at frames 473–480, mixing food and toys. The blue toy is eventually acquired and added to that bowl by frame 1065; this groups the toys but does not correct the misplaced carrot. overhead_cam and wrist_cam at frame 1799 show the orange fruit-shaped object and brown object still on the table, with the green bowl unused. Thus sorting is visibly incomplete and incorrect, not merely unconfirmed; repeated failed acquisitions and a temporary bowl disturbance also occur. The recording end does not establish abnormal termination.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 181 | No |
| 181 | 204 | Yes |
| 204 | 343 | No |
| 343 | 350 | Yes |
| 350 | 472 | No |
| 472 | 483 | Yes |
| 483 | 604 | No |
| 604 | 974 | Yes |
| 974 | 1231 | No |
| 1231 | 1800 | Yes |

## Failure annotations

### Failure 1

- Frames: 181-204
- Categories: collision
- Explanation: During acquisition of the pink toy, the gripper unintentionally disturbs the green bowl. overhead_cam and wrist_cam show the bowl rocking and shifting between frames 181 and 203, particularly at frame 195, before settling upright. This disturbance is not required sorting contact.
- Recovery: Clear the bowl rim and reassess its position before continuing with a collision-free approach; human intervention is not visibly needed.
- Severity: low
- Severity evidence: The empty bowl remains on the table and settles upright, with no visible breakage or spilled contents.
- Resetability: immediate
- Resetability evidence: The bowl remains usable and accessible at its updated position without cleanup or human resetting.

### Failure 2

- Frames: 343-350
- Categories: grasp
- Explanation: wrist_cam at frames 343–345 shows the brown object escaping the closing fingers; overhead_cam at frames 348–350 shows it rolling to the right while the gripper remains empty. The acquisition fails rather than transferring the object toward a bowl.
- Recovery: Locate the settled object and realign the fingers around its body before retrying, avoiding adjacent objects; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The object rolls locally on the tabletop without visible damage or a fall.
- Resetability: immediate
- Resetability evidence: The object remains accessible for another attempt without environmental repair or human resetting.

### Failure 3

- Frames: 472-483
- Categories: sequencing_semantic
- Explanation: The robot releases the carrot into the purple bowl at frames 472–480, where wrist_cam clearly shows the previously placed pink animal toy; overhead_cam confirms the transfer. Successful physical placement mixes the categories instead of separating them. Later placement of the blue toy with the pink toy does not independently constitute another sorting error; the misplaced carrot remains the unresolved error.
- Recovery: Use the purple bowl for toys and transfer the carrot into the green bowl, then place the remaining food objects there; human intervention is not visibly needed.
- Severity: low
- Severity evidence: The consequence is incorrect sorting, with the objects contained and no visible damage or meaningful damage hazard.
- Resetability: immediate
- Resetability evidence: The carrot remains accessible in an upright bowl and can be transferred directly without cleanup or a human reset.

### Failure 4

- Frames: 604-974
- Categories: grasp
- Explanation: wrist_cam shows the blue toy shifting outside the fingers at frames 604–615, followed by repeated ineffective closing and reopening cycles, including frames 690–750, 795–840, and 855–960. overhead_cam corroborates that the toy remains at the tabletop throughout these retries. This is one continuous unsuccessful acquisition sequence across frame 700, ending approximately at frame 974 as the eventual successful acquisition begins; the subsequent lift is visible at frame 1020.
- Recovery: Open and lift clear, reassess the toy's position, and align around a secure portion of its body; verify retention with a short lift before transporting it to the toy bowl. No human intervention is visibly necessary.
- Severity: low
- Severity evidence: The toy undergoes limited local displacement, but neither camera shows damage or a meaningful damage hazard.
- Resetability: immediate
- Resetability evidence: The toy remains accessible in a usable workspace, permitting a corrected attempt without cleanup, repair, or human intervention.

### Failure 5

- Frames: 1231-1800
- Categories: grasp
- Explanation: The robot repeatedly closes and reopens beside or below the orange fruit-shaped object's body without retaining it. wrist_cam shows ineffective cycles around frames 1231–1245, 1275–1290, 1350–1365, 1411–1440, 1485–1500, and 1545–1575, followed by further displacement without acquisition at frames 1620–1799; overhead_cam confirms no lift or bowl transfer. The brief pauses around frames 1400 and 1750 remain within the same repeated unsuccessful sequence, with no distinct recovery established.
- Recovery: Stop repeating the same near-edge closure, open and lift clear, and reposition the fingers on opposite sides of the object's body at an appropriate height; verify a secure short lift before transferring it to the food bowl. No human intervention is visibly required.
- Severity: low
- Severity evidence: The object is locally displaced and rotated but remains on the usable tabletop; no damage, fall, or meaningful damage hazard is visible.
- Resetability: immediate
- Resetability evidence: The target remains accessible through frame 1799, with no visible need for cleanup, repair, or human environmental resetting.