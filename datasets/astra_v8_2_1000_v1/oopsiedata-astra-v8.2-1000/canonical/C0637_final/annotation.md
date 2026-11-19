# Episode: C0637

## Episode annotation

- Language task: Pick basketball and place in blue bowl.
- Success label: success but suboptimal
- Outcome evidence: In exterior_cam, repeated acquisition attempts leave the basketball on the table (frames 73–80, 125–171, and 300–311). The robot eventually lifts and transports it toward the bowl (frames 337–370), lowers it inside, and opens its fingers around the ball in the bowl (frames 412–416). Completion is visible, although the gripper has not fully withdrawn.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 65 | No |
| 65 | 81 | Yes |
| 81 | 119 | No |
| 119 | 172 | Yes |
| 172 | 294 | No |
| 294 | 312 | Yes |
| 312 | 417 | No |

## Failure annotations

### Failure 1

- Frames: 65-81
- Categories: grasp
- Explanation: In exterior_cam, after closing around the basketball, the gripper rises away during frames 65–73 without retaining it; the ball remains on the tabletop beneath the open gripper through frame 80. The attempted acquisition does not advance transport to the bowl.
- Recovery: Reopen and realign the fingers around the ball, close securely, and verify retention with a small lift before transporting it; no human intervention is needed.
- Severity: low
- Severity evidence: The ball remains on the table, with no visible damage or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The ball remains accessible for another attempt without environmental resetting.

### Failure 2

- Frames: 119-172
- Categories: grasp
- Explanation: In exterior_cam, the gripper again withdraws after an acquisition attempt during frames 119–129 while the basketball remains on the table. It opens and hovers above the unacquired ball through frame 171, before descending for another attempt at frame 172.
- Recovery: Adjust the grasp position and finger spacing, descend around the ball, and verify a secure lift before moving toward the bowl; human intervention is not needed.
- Severity: low
- Severity evidence: This unsuccessful acquisition delays the task but causes no visible damage; the ball stays on the tabletop.
- Resetability: immediate
- Resetability evidence: Neither the ball nor the bowl requires repositioning for a valid retry.

### Failure 3

- Frames: 294-312
- Categories: grasp
- Explanation: In exterior_cam, the gripper rises and opens during frames 294–305, leaving the basketball on the table rather than carrying it. The separation remains visible through frame 311; renewed approach begins at frame 312.
- Recovery: Recenter the gripper around the ball and establish secure finger contact, then confirm that the ball follows a short upward motion; no human intervention is needed.
- Severity: low
- Severity evidence: The failed acquisition leaves the ball safely on the table, without visible damage or disruption to other objects.
- Resetability: immediate
- Resetability evidence: The target remains within reach and the environment is ready for another attempt without intervention.