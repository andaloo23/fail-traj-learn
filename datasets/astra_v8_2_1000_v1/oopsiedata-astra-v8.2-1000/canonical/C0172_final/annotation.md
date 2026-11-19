# Episode: C0172

## Episode annotation

- Language task: close the drawer
- Success label: failure
- Outcome evidence: In right_shoulder_cam, the drawer is open at frame 0. The robot approaches its handle, withdraws without closing it at frames 14–21, and remains away through frame 42. A renewed approach at frames 43–52 produces some inward drawer movement at frames 53–55, but the drawer remains visibly extended at frame 60; full closure is not observed.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 14 | No |
| 14 | 43 | Yes |
| 43 | 61 | No |

## Failure annotations

### Failure 1

- Frames: 14-43
- Categories: grasp, task_not_attempted
- Explanation: In right_shoulder_cam, the fingers close near the drawer handle at frames 9–13, but the gripper subsequently moves away empty at frames 14–21 while the handle and open drawer remain in place. It then stays away from the handle with little movement through frame 42, a sustained unproductive interval rather than continued alignment at the target. The images do not establish why acquisition failed.
- Recovery: Realign with the handle or a suitable drawer-front pushing surface, establish controlled contact, and push along the drawer’s travel direction while checking closure. No human intervention is visibly required.
- Severity: low
- Severity evidence: The drawer remains open, but no damage, displaced unrelated objects, or meaningful damage risk is visible in right_shoulder_cam during frames 14–42.
- Resetability: immediate
- Resetability evidence: The drawer and handle remain accessible and essentially unchanged; another aligned attempt can begin without an environmental reset or human intervention.