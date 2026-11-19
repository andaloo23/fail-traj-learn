# Episode: C0430

## Episode annotation

- Language task: put the cup in the purple bowl
- Success label: failure
- Outcome evidence: The robot initially approaches the orange cup, which tips onto its side without being acquired (frames 89–104, wrist and right). A subsequent acquisition also leaves it on the table as the gripper moves away empty (frames 145–177, wrist, overhead and right). The robot then retrieves a black cup-shaped vessel from the shelf and brings it to the purple bowl (frames 305–399, wrist and right), but release and stable placement are not visible before the recording ends. Thus completion is unconfirmed, in addition to the visibly failed orange-cup attempts. Both orange and black vessels are visible; the task does not specify which cup is intended.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 89 | No |
| 89 | 105 | Yes |
| 105 | 145 | No |
| 145 | 177 | Yes |
| 177 | 400 | No |

## Failure annotations

### Failure 1

- Frames: 89-105
- Categories: grasp
- Explanation: During the attempted acquisition, the orange cup tilts and falls onto its side instead of becoming securely held (frames 89–98, wrist); it remains on the table beside the empty gripper at frame 104 in right and overhead. This does not advance placement in the bowl.
- Recovery: Reassess the cup's sideways pose and acquire it with an aligned grasp, verifying retention before lifting; human intervention is not necessary if that pose is safely graspable.
- Severity: low
- Severity evidence: The cup topples on the tabletop without visible breakage, spilled contents or damage to other objects (frames 97–104, wrist and right).
- Resetability: immediate
- Resetability evidence: The cup remains accessible on the table and can be approached in its new pose without requiring an environmental reset.

### Failure 2

- Frames: 145-177
- Categories: grasp
- Explanation: The fingers close near the sideways orange cup at frames 145–152, but reopen and move away without it at frames 153–169 in wrist. The cup remains on the table in overhead and right, while the empty gripper passes over the purple bowl and withdraws through frame 176. The completed acquisition attempt therefore fails.
- Recovery: Return to the cup, align the fingers around its body rather than beside its end, and verify a secure lift before transporting it to the bowl; no human intervention is visibly required.
- Severity: low
- Severity evidence: The attempt leaves the cup outside the bowl, with no visible damage or additional hazardous consequence (frames 153–177, overhead and right).
- Resetability: immediate
- Resetability evidence: The failed acquisition leaves the cup accessible on the tabletop, allowing another attempt without human resetting.