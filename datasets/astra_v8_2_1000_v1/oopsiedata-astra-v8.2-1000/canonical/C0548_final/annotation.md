# Episode: C0548

## Episode annotation

- Language task: Open the drawer.
- Success label: success but suboptimal
- Outcome evidence: The drawer starts closed (frame 0, image and left_ego_image). An initial handle-acquisition attempt does not open it, and the gripper withdraws empty (frames 180–189, wrist_image). After realignment, the robot pulls the upper drawer outward (frames 252–274, image and left_ego_image); it remains visibly open after release through frame 315. No unintended displacement of surrounding objects or damage is visible.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 117 | No |
| 117 | 210 | Yes |
| 210 | 316 | No |

## Failure annotations

### Failure 1

- Frames: 117-210
- Categories: grasp
- Explanation: Following the initial closing motion near the handle, the gripper makes small unsuccessful movements without drawing the drawer outward (frames 117–179, wrist_image and left_ego_image). It then backs away without the handle and closes empty above it (frames 180–189, wrist_image), confirming failed acquisition; the drawer remains closed. The interval ends when the fingers reopen for renewed alignment at frame 210.
- Recovery: Reopen the gripper, align both fingers around the handle with sufficient insertion depth, establish a secure grasp, and pull along the drawer’s sliding direction; no human intervention is needed.
- Severity: low
- Severity evidence: The attempt delays opening, but no damage, displaced cabinet, or harmful contact with surrounding objects is visible.
- Resetability: immediate
- Resetability evidence: The drawer and handle remain in their original usable state; the robot can realign and retry without environmental resetting or human assistance.