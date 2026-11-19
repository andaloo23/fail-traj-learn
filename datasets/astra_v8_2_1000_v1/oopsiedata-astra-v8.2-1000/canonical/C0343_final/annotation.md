# Episode: C0343

## Episode annotation

- Language task: Pack the coffee pods onto the wooden tray.
- Success label: failure
- Outcome evidence: The robot clears the banana from the tray (frames 87–200, overhead_cam and wrist_cam), then transfers three coffee pods onto it, visible after releases at frames 375, 625 and 765. The fourth acquisition fails: the pod remains on the table while the gripper withdraws empty (frames 839–855, both cameras). The robot subsequently moves over the tray and opens its empty gripper (frames 902–908, wrist_cam). At frame 1019, overhead_cam still shows three pods on the tray and one on the table; this is a visibly incomplete task following a failed attempt, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 836 | No |
| 836 | 909 | Yes |
| 909 | 1020 | No |

## Failure annotations

### Failure 1

- Frames: 836-909
- Categories: grasp
- Explanation: During closure, the fourth pod shifts out of the grasp (frames 836–839, wrist_cam). The gripper then lifts and moves away empty while the pod remains on the tabletop (frames 840–855, overhead_cam and wrist_cam). It continues to the tray and opens without delivering a pod (frames 902–908, wrist_cam), so this acquisition-and-transfer attempt does not advance packing.
- Recovery: Return to the remaining pod, realign the open fingers around its body, and verify a secure lift before transporting and releasing it onto the tray; no human intervention is needed on the visible evidence.
- Severity: low
- Severity evidence: The pod remains on the usable tabletop; no damage, spill or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: The remaining pod is accessible for another grasp, and the three packed pods can stay on the tray; no environmental reset or human assistance is required.