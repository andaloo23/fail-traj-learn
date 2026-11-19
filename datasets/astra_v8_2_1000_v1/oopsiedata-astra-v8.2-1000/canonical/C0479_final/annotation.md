# Episode: C0479

## Episode annotation

- Language task: Pack the cups with a single arm.
- Success label: failure
- Outcome evidence: In base_image, the arm acquires the light-colored cup and lowers it over a blue cup (frames 43–78), then moves the combined cups toward the remaining blue cup (frames 79–127). Packing is not completed: the handled cups topple sideways as the gripper closes and withdraws (frames 151–162), while another blue cup remains separate. This is a visibly unsuccessful final handling attempt, not merely unconfirmed completion; no cups are visibly placed in the box.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 151 | No |
| 151 | 163 | Yes |

## Failure annotations

### Failure 1

- Frames: 151-163
- Categories: grasp, collision
- Explanation: In base_image frame 151, the cups begin tipping during the acquisition attempt; by frame 152, the handled cups have fallen sideways and the neighboring blue cup has been displaced leftward. Frames 153–162 show the gripper withdrawing empty while the cups remain on the table, establishing unsuccessful acquisition or retention and disruptive contact with the neighboring cup.
- Recovery: Reopen and withdraw clear of the cups, then reacquire and reorient the sideways cups with a secure grasp before continuing packing. Human intervention is not clearly necessary, but a person could reset their orientation if autonomous recovery cannot be performed reliably.
- Severity: low
- Severity evidence: The cups topple and shift on the tabletop, but no breakage, spill, or other meaningful damage is visible in base_image frames 152–162.
- Resetability: minor_reset
- Resetability evidence: The sideways cups need reorientation and separation or realignment for another attempt; they remain accessible on the tabletop, so a straightforward reset appears sufficient.