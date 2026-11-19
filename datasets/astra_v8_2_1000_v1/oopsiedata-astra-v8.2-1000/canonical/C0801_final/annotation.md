# Episode: C0801

## Episode annotation

- Language task: Open the oven.
- Success label: failure
- Outcome evidence: The oven door remains closed from frame 0 through frame 345 in left_ego_image. The robot approaches the oven, but wrist_image shows repeated finger closing and reopening beside the handle from frames 174–345 without capturing it or moving the door. This is a visibly unsuccessful acquisition sequence, not merely an unconfirmed opening at the recording boundary; no damage or unrelated object displacement is visible.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 174 | No |
| 174 | 346 | Yes |

## Failure annotations

### Failure 1

- Frames: 174-346
- Categories: grasp
- Explanation: At frame 174 in wrist_image, the fingers close together beside the oven handle rather than around it. They reopen at frames 181–183 and repeat similar empty closures at frames 185, 200, 216 and subsequently through frame 345, without a successful acquisition. The unchanged closed door in left_ego_image and unchanged oven position in image corroborate that these repeated attempts do not advance opening the oven.
- Recovery: Stop repeating the same closure, reopen the fingers, and reposition so the handle lies between them before closing; verify acquisition before pulling along the door’s opening path. No human intervention is visibly required.
- Severity: low
- Severity evidence: The attempts leave the oven closed; no visible damage, displaced objects, or meaningful damage risk is established.
- Resetability: immediate
- Resetability evidence: The oven and surrounding objects remain in their original usable states, so another aligned acquisition attempt requires no environmental reset or human intervention.