# Episode: C0565

## Episode annotation

- Language task: Open the drawer.
- Success label: failure
- Outcome evidence: The robot repeatedly attempts to grasp the upper drawer handle but withdraws empty; wrist_image shows this at frames 90–94, 140–144, 190–196, 235–244, 290–294 and 342–354. The drawer remains closed in left_ego_image, including frames 0, 200 and 399. This is a visibly unsuccessful attempt, not merely unconfirmed completion; no drawer opening or unrelated object displacement is visible.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 80 | No |
| 80 | 94 | Yes |
| 94 | 120 | No |
| 120 | 144 | Yes |
| 144 | 172 | No |
| 172 | 196 | Yes |
| 196 | 224 | No |
| 224 | 244 | Yes |
| 244 | 281 | No |
| 281 | 294 | Yes |
| 294 | 335 | No |
| 335 | 354 | Yes |
| 354 | 400 | No |

## Failure annotations

### Failure 1

- Frames: 80-94
- Categories: grasp
- Explanation: In wrist_image, the fingers close beside the upper handle at frame 80 without capturing it, then withdraw empty at frames 90–93; left_ego_image shows the drawer staying closed.
- Recovery: Reopen and reposition the fingers around the handle, verify engagement, then pull along the drawer's travel direction; no human intervention is evidently needed.
- Severity: low
- Severity evidence: The missed acquisition prevents opening; no damage or displaced scene objects are visible.
- Resetability: immediate
- Resetability evidence: The drawer and handle remain in place, permitting another attempt without environmental resetting.

### Failure 2

- Frames: 120-144
- Categories: grasp
- Explanation: wrist_image shows another closure beside the handle at frames 120–121, followed by empty withdrawal at frames 132–143; the drawer does not move in left_ego_image.
- Recovery: Correct the finger position and approach depth before closing around the handle; verify capture before pulling. No human intervention is evidently needed.
- Severity: low
- Severity evidence: The attempt fails without visible damage or other consequential disturbance.
- Resetability: immediate
- Resetability evidence: No environmental change needs reversal before retrying.

### Failure 3

- Frames: 172-196
- Categories: grasp
- Explanation: The fingers close near the end of the handle at frames 172–173 in wrist_image but fail to retain it during withdrawal at frames 189–195; left_ego_image shows no opening.
- Recovery: Reopen, center the grasp on an accessible part of the handle and confirm secure engagement before pulling; no human intervention is evidently needed.
- Severity: low
- Severity evidence: Only task progress is lost; no breakage or meaningful damage risk is established by the images.
- Resetability: immediate
- Resetability evidence: The handle remains attached and the cabinet remains in its original usable state.

### Failure 4

- Frames: 224-244
- Categories: grasp
- Explanation: wrist_image shows the gripper closing without enclosing the handle at frames 224–225 and moving away empty at frames 235–243. The upper drawer stays closed in left_ego_image.
- Recovery: Adjust the grasp position rather than repeating the same near-handle closure, then verify engagement before a controlled pull; no human intervention is evidently needed.
- Severity: low
- Severity evidence: No visible damage or unintended movement accompanies the missed grasp.
- Resetability: immediate
- Resetability evidence: Another attempt requires robot repositioning only, not a scene reset.

### Failure 5

- Frames: 281-294
- Categories: grasp
- Explanation: In wrist_image, the fingers close above or beside the handle at frame 281 and retreat without it at frames 289–293; left_ego_image confirms that the drawer remains closed.
- Recovery: Re-establish the handle's position relative to both fingers and approach so the handle lies between them before closing; no human intervention is evidently needed.
- Severity: low
- Severity evidence: The unsuccessful acquisition causes no visible damage or scene disruption.
- Resetability: immediate
- Resetability evidence: The unchanged drawer is available for an immediate corrected attempt.

### Failure 6

- Frames: 335-354
- Categories: grasp
- Explanation: wrist_image shows a final closure away from the handle at frames 335–336, followed by empty withdrawal through frame 353. left_ego_image shows no drawer displacement.
- Recovery: Stop repeating the ineffective grasp position, realign around the handle and verify capture before pulling; no human intervention is visibly required.
- Severity: low
- Severity evidence: The drawer remains unopened, with no visible damage to the handle, cabinet or surrounding objects.
- Resetability: immediate
- Resetability evidence: No cleanup, repair or object replacement is visibly necessary before another attempt.