# Episode: C0915

## Episode annotation

- Language task: Close the oven.
- Success label: failure
- Outcome evidence: The oven door is open at frame 0 in left_ego_image and remains lowered at frame 163 in left_ego_image and image. The robot approaches the door, but its gripper lifts away without closing it around frames 100–105. It subsequently approaches again during frames 106–163; completion of this renewed attempt is unconfirmed, rather than visibly established as another failed acquisition.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 100 | No |
| 100 | 106 | Yes |
| 106 | 164 | No |

## Failure annotations

### Failure 1

- Frames: 100-106
- Categories: grasp
- Explanation: Following positioning at the oven door, the gripper lifts away empty during frames 100–105 in left_ego_image while the door remains lowered; image also shows the unchanged open door. This establishes unsuccessful acquisition for the closing attempt, although the precise contact or reason for the miss is not visible.
- Recovery: Reposition the gripper at the door handle or a suitable accessible edge, establish secure contact, and follow the door’s hinge motion upward to close it; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The door remains open, with no visible damage, displaced unrelated objects, or meaningful damage risk from the failed acquisition.
- Resetability: immediate
- Resetability evidence: The oven and surrounding objects remain in place, so another acquisition attempt can proceed without an environmental reset or human intervention.