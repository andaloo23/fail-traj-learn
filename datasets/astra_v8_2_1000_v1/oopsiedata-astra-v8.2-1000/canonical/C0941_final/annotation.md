# Episode: C0941

## Episode annotation

- Language task: Pick basketball and place in blue bowl.
- Success label: success but suboptimal
- Outcome evidence: In exterior_cam, the robot lifts the basketball at frames 70–81 but loses it onto the tabletop beside the bowl at frames 97–112. It subsequently reacquires the ball and carries it toward the bowl at frames 197–218. At frames 234–241, the ball is seated inside the blue bowl as the fingers spread around it; the gripper has not fully withdrawn. The earlier loss and reacquisition make the completion suboptimal.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 97 | No |
| 97 | 113 | Yes |
| 113 | 242 | No |

## Failure annotations

### Failure 1

- Frames: 97-113
- Categories: grasp
- Explanation: In exterior_cam, the basketball previously lifted and carried at frames 70–96 descends away from the fingers at frames 97–108 and lands on the tabletop outside the bowl by frames 109–112. This loss of retention interrupts the transfer and requires reacquisition; the images do not establish its underlying cause.
- Recovery: Track the ball until it settles, realign the open fingers around it, acquire a secure grasp, and then transfer it over the bowl before releasing; no human intervention is needed.
- Severity: low
- Severity evidence: The ball falls a short distance onto the clear tabletop and remains accessible; no damage or meaningful damage risk is visible in exterior_cam at frames 109–120.
- Resetability: immediate
- Resetability evidence: The ball remains on the usable tabletop beside the upright bowl, allowing another acquisition attempt without human resetting.