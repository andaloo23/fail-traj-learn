# Episode: C0746_W03

## Episode annotation

- Language task: Clean the table by placing the cans in the upper tray and the bowls in the tray on the right.
- Success label: failure
- Outcome evidence: In base_image, the gripper initially works beside the green can (frames 700–785), then withdraws without it and travels toward the upper tray (frames 786–900); the empty fingers and green can remaining on the table are clear by frames 822–840. At frame 1049, both cans and both bowls remain outside their destination trays. This window shows a failed acquisition, not merely unconfirmed completion. The outcome is provisional because earlier execution beyond the supplied context and later execution are unavailable.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 700 | 786 | No |
| 786 | 1050 | Yes |

## Failure annotations

### Failure 1

- Frames: 786-1050
- Categories: grasp
- Explanation: In base_image, the gripper begins withdrawing from the green can at frame 786 after the near-can acquisition motions. By frames 822–840, its fingers are visibly empty while the green can remains on the tabletop. It continues toward and over the upper tray without transporting a can (frames 850–1049), so this attempted transfer does not advance the task. No corrective return is visible within the window; this failure may continue beyond its end.
- Recovery: Return to the green can, align the fingers around its accessible body, and verify secure acquisition with a small lift before transporting it to the upper tray; no human intervention is visibly necessary.
- Severity: low
- Severity evidence: The can remains on the table and no spill, newly established damage, or meaningful damage risk is visible in base_image through frame 1049.
- Resetability: immediate
- Resetability evidence: The target remains accessible on the tabletop, so another grasp can be attempted without environmental resetting or human intervention.