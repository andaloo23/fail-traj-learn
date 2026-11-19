# Episode: C0412

## Episode annotation

- Language task: Move the banana to the pot on the right and sushi to the bowl.
- Success label: success but side effects
- Outcome evidence: In image_primary, the first banana acquisition fails: the gripper rises empty while the banana remains in the bowl (frames 25–30). Subsequent contact shifts the bowl and pot (frames 31–44). A retry transfers the banana into the right pot, where it remains after release (frames 89–96). The red-and-white sushi is then lifted from the table (frames 118–123), carried over the bowl, and released inside it at frame 133. Both transfers are completed, with an earlier failed grasp and unintended container displacement; no damage is visible.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 25 | No |
| 25 | 31 | Yes |
| 31 | 45 | Yes |
| 45 | 134 | No |

## Failure annotations

### Failure 1

- Frames: 25-31
- Categories: grasp
- Explanation: In image_primary frames 25–30, the closed gripper withdraws from the bowl and moves right without the banana, which remains visibly inside the bowl. This establishes failed acquisition rather than an unfinished grasp.
- Recovery: Return above the banana, adjust the grasp alignment, and verify secure acquisition with a short lift before transferring it; human intervention is not needed.
- Severity: low
- Severity evidence: The banana remains safely in the bowl, with no visible damage or meaningful damage risk from this missed acquisition.
- Resetability: immediate
- Resetability evidence: The target remains accessible in its original container, so another grasp can be attempted without environmental resetting.

### Failure 2

- Frames: 31-45
- Categories: collision
- Explanation: In image_primary frames 31–32, the empty gripper contacts the bowl edge and visibly rotates/shifts the bowl. It then moves against the pot, which shifts and rocks during frames 40–44. These unintended container contacts do not transfer the banana and disturb the scene.
- Recovery: Lift clear of the container rims, reassess their current positions, and approach the banana with adequate clearance; human intervention is not needed while both containers remain upright and accessible.
- Severity: low
- Severity evidence: Both containers remain on the table and usable; no spill, breakage, or other damage is visible.
- Resetability: immediate
- Resetability evidence: Although the containers have moved slightly, both remain upright and reachable, allowing a new attempt using their updated positions without a human reset.