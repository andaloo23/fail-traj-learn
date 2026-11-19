# Episode: C0587

## Episode annotation

- Language task: pick up the blue peg and insert it into the green peghole
- Success label: failure
- Outcome evidence: The initial acquisition fails, leaving the blue peg on the table beside the green peghole (frames 22–25, side and wrist). The robot subsequently lifts the peg (frames 50–55, front and side), but repeatedly moves it through similar airborne poses without inserting it. At frame 248, wrist shows the peg still held while side shows the green hole empty. The observed task is incomplete, with a visible failed grasp and later unproductive motion rather than merely an occluded completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 22 | No |
| 22 | 30 | Yes |
| 30 | 155 | No |
| 155 | 249 | Yes |

## Failure annotations

### Failure 1

- Frames: 22-30
- Categories: grasp
- Explanation: At frame 22 the blue peg tips during acquisition; by frames 23–25 it has fallen beside the green holder while the gripper closes empty and withdraws (side and wrist). This establishes unsuccessful acquisition, although a secure initial hold is not established. At frame 30 the gripper begins reopening for another approach.
- Recovery: Reopen, align with the peg's new tabletop pose, and grasp securely before lifting; no human intervention is needed.
- Severity: low
- Severity evidence: The peg falls only onto the nearby tabletop; frames 24–29 in side show no visible damage or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The peg remains accessible beside the upright holder and can be reacquired without environmental intervention, as the subsequent approach demonstrates.

### Failure 2

- Frames: 155-249
- Categories: task_not_attempted
- Explanation: Beginning at frame 155, the robot reverses away from its nearer pose and continues repeated airborne motion cycles rather than advancing to insertion: comparable poses recur around frames 155, 194, and 234, and around frames 170, 209, and 248 (front and side). Wrist shows continued peg retention, while side shows the untouched empty hole. This is sustained unproductive motion, not a failed insertion contact; the underlying cause is not visible.
- Recovery: Stop the repetitive motion, locate the green opening, orient the held peg to match it, and approach along the insertion axis before lowering carefully; no human intervention is visibly required.
- Severity: low
- Severity evidence: The peg remains held, and no collision, damage, or displacement of the holder is visible during the repeated motion.
- Resetability: immediate
- Resetability evidence: The holder remains upright and accessible and the peg remains in the gripper, so a corrected approach can begin without resetting the environment.