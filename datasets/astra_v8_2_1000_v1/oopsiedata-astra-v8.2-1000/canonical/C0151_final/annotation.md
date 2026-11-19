# Episode: C0151

## Episode annotation

- Language task: Pick up the spoon and place it in the sink.
- Success label: failure
- Outcome evidence: The spoon remains on the counter outside the sink throughout the episode, including frames 0, 105 and 299 in right. The robot approaches its handle but withdraws empty; wrist frames 73–105 show the handle separating from the gripper rather than being carried. Subsequent hovering and small movements do not acquire or place the spoon. This is a visibly unsuccessful attempt, not merely unconfirmed completion.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 73 | No |
| 73 | 106 | Yes |
| 106 | 300 | Yes |

## Failure annotations

### Failure 1

- Frames: 73-106
- Categories: grasp
- Explanation: Following the near-handle acquisition attempt, the robot begins withdrawing at frame 73 without the spoon. In wrist frames 85–105, the handle becomes increasingly separated from the empty gripper; right confirms that the spoon stays on the counter. The attempted pickup therefore fails to advance the task.
- Recovery: Reapproach the spoon, align the fingers around its handle, close and verify possession with a small lift before transporting it over the sink; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The spoon remains on the counter, with no visible damage, spill or other harmful consequence in right frames 73–105.
- Resetability: immediate
- Resetability evidence: The spoon remains accessible in its original location and the environment requires no visible resetting before another attempt.

### Failure 2

- Frames: 106-300
- Categories: task_not_attempted
- Explanation: After the empty withdrawal, the robot hovers and makes small movements above the sink and toward the faucet rather than returning to acquire the spoon. Right frames 106, 170, 194, 241 and 299 show no progress while the spoon stays outside the sink; wrist shows the empty gripper. This sustained unproductive behavior is distinct from the preceding failed acquisition.
- Recovery: Resume the task by locating the spoon on the counter and executing a verified pickup followed by placement inside the basin; no human intervention is visibly required.
- Severity: low
- Severity evidence: The sustained inactivity and nonproductive movements leave the task incomplete, but no damage or meaningful damage risk is visible.
- Resetability: immediate
- Resetability evidence: The spoon and sink remain usable and accessible through frame 299 in right; no environmental intervention is needed to reattempt.
