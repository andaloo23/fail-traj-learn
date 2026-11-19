# Episode: C0991

## Episode annotation

- Language task: Put the spoon in the drawer.
- Success label: success but suboptimal
- Outcome evidence: The first acquisition fails: frames 95–107 in wrist_image and left_ego_image show the gripper withdrawing while the spoon remains on the table. A second grasp succeeds, with the spoon visibly carried in frames 175–225 in left_ego_image and wrist_image. Frames 241–255 in wrist_image show its release and resting position inside the open drawer; the gripper subsequently withdraws empty through frame 269. No unintended damage or unrelated object displacement is established.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 95 | No |
| 95 | 113 | Yes |
| 113 | 270 | No |

## Failure annotations

### Failure 1

- Frames: 95-113
- Categories: grasp
- Explanation: At frame 95 in wrist_image, the spoon moves out from between the closing fingers rather than remaining secured. Through frames 100–107, left_ego_image shows the spoon on the tabletop as the gripper lifts away empty, establishing failed acquisition. The interval ends when the fingers reopen for a renewed approach at frame 113.
- Recovery: Reopen the gripper, realign the fingers around the spoon, and verify secure retention with a small lift before transporting it to the drawer; no human intervention is needed.
- Severity: low
- Severity evidence: The spoon remains accessible on the table, with no visible damage or meaningful damage risk from this failed acquisition.
- Resetability: immediate
- Resetability evidence: The robot can retry directly from the spoon’s tabletop position without environmental resetting or human intervention.