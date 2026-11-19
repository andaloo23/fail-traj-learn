# Episode: C0608

## Episode annotation

- Language task: Move the banana to the pot on the right and sushi to the bowl.
- Success label: failure
- Outcome evidence: In image_primary, frame 0 shows the banana in the cream bowl, the empty metal pot on the right, and the red-and-white sushi on the table. Several banana acquisitions fail visibly. At frames 158–159 the banana begins lifting with the gripper, but transfer to the pot is not shown; the sushi remains untouched. Completion is unconfirmed, in addition to the earlier visibly failed attempts.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 49 | No |
| 49 | 53 | Yes |
| 53 | 67 | No |
| 67 | 70 | Yes |
| 70 | 92 | No |
| 92 | 96 | Yes |
| 96 | 140 | No |
| 140 | 144 | Yes |
| 144 | 160 | No |

## Failure annotations

### Failure 1

- Frames: 49-53
- Categories: grasp
- Explanation: In image_primary, after closing near the banana at frames 47–48, the gripper rises at frames 49–52 without carrying it; the banana remains in the bowl. This acquisition does not advance the transfer.
- Recovery: Reopen and reposition the fingers around the banana, then verify a secure grasp with a short lift before transferring; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The banana remains contained in the bowl, with no visible damage or meaningful damage risk.
- Resetability: immediate
- Resetability evidence: The target remains accessible in the upright bowl; another attempt requires no environmental reset.

### Failure 2

- Frames: 67-70
- Categories: grasp
- Explanation: In image_primary, the gripper closes near the banana at frames 64–66 and withdraws at frames 67–69 while the banana stays in the bowl, establishing another unsuccessful acquisition; reopening begins at frame 70.
- Recovery: Adjust the grasp position to capture the banana between the finger pads and check retention before moving toward the pot; no human intervention is visibly needed.
- Severity: low
- Severity evidence: No object leaves the bowl or shows visible damage during the failed acquisition.
- Resetability: immediate
- Resetability evidence: The bowl and banana remain available for an autonomous reattempt without resetting the scene.

### Failure 3

- Frames: 92-96
- Categories: grasp
- Explanation: In image_primary, following finger closure at frames 90–91, the gripper lifts empty at frames 92–95 while the banana remains in the bowl. The fingers reopen at frame 96.
- Recovery: Reassess the banana’s position and use a better-centered grasp, verifying possession before transport; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The visible consequence is another missed acquisition, without damage or displacement outside the bowl.
- Resetability: immediate
- Resetability evidence: No cleanup or object restoration is needed to retry.

### Failure 4

- Frames: 140-144
- Categories: grasp
- Explanation: In image_primary, the gripper closes near the banana at frames 138–139 and rises at frames 140–143 without it. The banana remains in the bowl, and reopening at frame 144 begins another attempt.
- Recovery: Reposition the fingers around a securely graspable section of the banana and confirm retention with a controlled lift before carrying it to the right-hand pot; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The failed lift leaves the banana in the bowl with no visible damage or harmful side effect.
- Resetability: immediate
- Resetability evidence: The target remains accessible and the environment remains usable without intervention.