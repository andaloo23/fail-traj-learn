# Episode: C0857

## Episode annotation

- Language task: Seperate the food and the toys into the two bowls.
- Success label: success but side effects
- Outcome evidence: wrist_cam shows both plush toys in the purple bowl by frame 357, the carrot and brown food item in the green bowl by frame 692, and all three food items in the green bowl by frame 890. Frames 930–952 in overhead_cam and wrist_cam confirm the completed separation. During acquisition of the brown item, the gripper also disturbs and slides the green bowl (frames 593–612, overhead_cam), without spilling its contents.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 593 | No |
| 593 | 613 | Yes |
| 613 | 953 | No |

## Failure annotations

### Failure 1

- Frames: 593-613
- Categories: collision
- Explanation: While approaching and grasping the brown food item, the gripper contacts the adjacent green bowl; the bowl rocks and slides left in overhead_cam across frames 593–612. wrist_cam shows the bowl rim immediately alongside the fingers during frames 600–608. This unintended bowl displacement does not advance the sorting task, although the brown item is successfully acquired.
- Recovery: Lift clear of the bowl, update its position, and approach its interior with adequate rim clearance before placing the held food item; no human intervention is needed.
- Severity: low
- Severity evidence: The bowl remains on the table with the carrot retained, and no damage or spilled contents are visible in overhead_cam at frame 613.
- Resetability: immediate
- Resetability evidence: The displaced bowl remains upright, accessible, and usable for sorting; no environmental intervention is required before continuing.