# Episode: C0679

## Episode annotation

- Language task: place the coffee bag in the blue basket
- Success label: failure
- Outcome evidence: The robot approaches and closes its gripper on the coffee bag in frames 0–67 (right, wrist), then raises it slightly outside the basket. Beans visibly spill onto the table in frames 128–144 (right). By frames 185–193 (left, right, wrist), the bag is back on the table and the gripper opens; the blue basket remains empty. Placement is not completed, and the episode includes a visible spill rather than merely an unconfirmed outcome.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 128 | No |
| 128 | 185 | Yes |
| 185 | 194 | No |

## Failure annotations

### Failure 1

- Frames: 128-185
- Categories: manipulation
- Explanation: While the gripper holds the raised coffee bag outside the basket, beans begin appearing beneath it at frame 128 and accumulate across frames 130–144 (right); individual beans are also visible in wrist. The robot continues holding the bag in this position through frame 184 instead of containing the contents or transferring it into the basket. The opening or damage responsible for the leak is not clearly visible.
- Recovery: Set the bag down gently in a stable orientation that prevents further spilling, then request human assistance to collect the beans and inspect or secure the bag opening before retrying the transfer.
- Severity: medium
- Severity evidence: Beans visibly spill across the tabletop, requiring cleanup; no damage to the robot, basket, or table is visible, and whether the bag itself is torn is uncertain.
- Resetability: minor_reset
- Resetability evidence: Collecting the spilled beans and checking or securing the bag is a straightforward reset requiring human assistance; no major environmental repair is visibly necessary.