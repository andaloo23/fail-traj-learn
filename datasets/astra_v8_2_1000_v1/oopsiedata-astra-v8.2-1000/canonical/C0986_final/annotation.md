# Episode: C0986

## Episode annotation

- Language task: stack the blue block on the yellow block
- Success label: failure
- Outcome evidence: In right_shoulder_cam, the blue and yellow blocks remain separate on the table from frame 0 through frame 69. The gripper approaches and hovers above the blue block but never visibly acquires or moves it. Completion is unconfirmed; sustained hovering is visible, but no completed failed grasp or abnormal termination is established.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 10 | No |
| 10 | 29 | Yes |
| 29 | 48 | No |
| 48 | 70 | Yes |

## Failure annotations

### Failure 1

- Frames: 10-29
- Categories: task_not_attempted
- Explanation: In right_shoulder_cam, frames 10-28 show sustained hovering above the blocks with only small pose changes and no continued descent, acquisition, or object movement. This approximately four-second interval does not visibly advance stacking; approach resumes at frame 29.
- Recovery: Resume alignment and descend until the open fingers straddle the blue block, then acquire it before transferring it to the yellow block; no human intervention is visibly needed.
- Severity: low
- Severity evidence: Both blocks remain upright and unchanged, with no visible damage or harmful contact.
- Resetability: immediate
- Resetability evidence: The scene remains ready for another attempt without environmental resetting or human intervention.

### Failure 2

- Frames: 48-70
- Categories: task_not_attempted
- Explanation: In right_shoulder_cam, the gripper holds above the blue block during frames 48-56, rises away during frames 57-62, and returns to another elevated hover during frames 63-69. This sustained pause and back-and-forth movement produces no acquisition or stacking progress; both blocks remain stationary.
- Recovery: Re-align over the blue block and perform a controlled descent and grasp, verifying possession before lifting and placing it on the yellow block; no human intervention is visibly required.
- Severity: low
- Severity evidence: The visible consequence is lack of task progress; neither block nor the surrounding scene shows damage or disruption.
- Resetability: immediate
- Resetability evidence: Both blocks remain accessible in their original positions, so another attempt requires no environmental reset.
