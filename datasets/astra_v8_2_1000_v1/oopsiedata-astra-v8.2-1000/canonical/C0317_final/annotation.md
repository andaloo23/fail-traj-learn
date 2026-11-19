# Episode: C0317

## Episode annotation

- Language task: Pack the coffee pods onto the wooden tray.
- Success label: failure
- Outcome evidence: Two pods are placed on the tray, visible at frames 345 and 600 in overhead_cam and wrist_cam. The third acquisition fails: frames 737–750 show the gripper lifting away while the pod remains on the table. At frames 826–840, wrist_cam shows only two pods on the tray, and overhead_cam shows the remaining pod beside it. Completion is therefore visibly unachieved, not merely unconfirmed. The initial banana relocation clears the tray for packing and is consistent with useful preparation.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 734 | No |
| 734 | 879 | Yes |

## Failure annotations

### Failure 1

- Frames: 734-879
- Categories: grasp
- Explanation: During the third acquisition, the pod moves out of the closing fingers at frames 734–739 in wrist_cam; overhead_cam confirms that it remains on the tabletop as the gripper rises. The robot then travels empty to the tray and opens its fingers at frames 820–826 rather than transferring the remaining pod. It subsequently moves toward the banana through frame 878 without recovering the failed acquisition.
- Recovery: Return to the remaining pod, realign the open fingers around its body, acquire it gently, and verify that it lifts with the gripper before transporting it to the tray; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The pod remains on the usable tabletop, with no visible damage or meaningful damage risk; the consequence is incomplete packing and wasted motion.
- Resetability: immediate
- Resetability evidence: The remaining pod is still accessible beside the tray and the two placed pods remain on it, so another acquisition can be attempted without environmental resetting.