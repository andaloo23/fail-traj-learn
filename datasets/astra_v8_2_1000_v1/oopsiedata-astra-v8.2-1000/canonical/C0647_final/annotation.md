# Episode: C0647

## Episode annotation

- Language task: close the drawer
- Success label: failure
- Outcome evidence: In right_shoulder_cam, the drawer is open at frame 0 and remains extended with its interior visible at frame 48. The gripper approaches and repositions near the handle, but no drawer-closing movement is visible. Completion is not confirmed; sustained unproductive hovering is visible, but failed acquisition or established handle control cannot be confirmed.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 20 | No |
| 20 | 41 | Yes |
| 41 | 49 | No |

## Failure annotations

### Failure 1

- Frames: 20-41
- Categories: task_not_attempted
- Explanation: In right_shoulder_cam, frames 20–40 show sustained hovering near the drawer handle with only small pose adjustments, including a shift at frames 30–31. The drawer stays extended throughout, with no visible progress toward closure. This interval is sustained stalling rather than a confirmed failed grasp; more substantial repositioning resumes at frame 41.
- Recovery: Reassess alignment with the drawer front or handle, establish suitable contact, and apply a controlled inward push while checking that the drawer slides closed; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The drawer remains open, but no damage, displaced unrelated objects, or meaningful damage risk is visible in right_shoulder_cam frames 20–40.
- Resetability: immediate
- Resetability evidence: The drawer and surrounding scene remain in a usable state, so another closing attempt can proceed without an environmental reset.