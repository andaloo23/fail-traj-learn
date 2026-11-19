# Episode: C0869

## Episode annotation

- Language task: Seperate the food and the toys into the two bowls.
- Success label: failure
- Outcome evidence: wrist_cam shows both plush toys in the purple bowl by frame 553 and the orange and brown food-shaped objects in the green bowl by frame 967. The tomato-shaped object escapes the grasp at frames 660–672 and remains on the table. At frames 1043–1050, wrist_cam and overhead_cam confirm that it is still outside both bowls, so sorting is visibly incomplete following a failed acquisition, rather than merely unconfirmed.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 660 | No |
| 660 | 780 | Yes |
| 780 | 1051 | No |

## Failure annotations

### Failure 1

- Frames: 660-780
- Categories: grasp
- Explanation: After the fingers close against the tomato-shaped object at frames 650–659, wrist_cam shows it separating from the fingers and wobbling on the table at frames 660–675. overhead_cam confirms that it remains behind as the empty gripper moves away. The robot then moves over the green bowl and opens its empty fingers at frames 766–775, completing an unsuccessful transfer instead of sorting the tomato.
- Recovery: Reobserve the tomato's settled position, align the open fingers around its body, and verify secure possession with a short lift before transporting it to the green bowl; no human intervention is visibly needed.
- Severity: low
- Severity evidence: The object remains on the tabletop without visible damage, and the bowls and previously sorted objects remain usable.
- Resetability: immediate
- Resetability evidence: The tomato remains accessible on the table and can be approached again without environmental resetting or human intervention.