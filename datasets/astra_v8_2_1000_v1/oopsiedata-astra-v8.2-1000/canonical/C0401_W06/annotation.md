# Episode: C0401_W06

## Episode annotation

- Language task: stack the bowls
- Success label: success but side effects
- Outcome evidence: Provisionally for this window, the turquoise bowl remains nested in the pale outer bowl, with overlapping rims visible in right and a stable tabletop arrangement in top at frames 1750, 1875, and 1999. However, the robot approaches, squeezes, and reorients an unrelated brown plush toy rather than leaving the completed stack alone (left, frames 1800–1999). An orange object is already inside the bowls at frame 1750; its placement is not observed here. Earlier execution is unavailable beyond the two context frames, so the previous report's earlier failure claims are not independently verified.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 1750 | 2000 | Yes |

## Failure annotations

### Failure 1

- Frames: 1750-2000
- Categories: sequencing_semantic
- Explanation: The robot directs its gripper toward the brown plush toy rather than a bowl (left and top, frames 1750–1800), closes around and compresses it (left, frames 1836–1867), then continues repositioning and reorienting it through frame 1999. Its white face becomes exposed at frame 1869 and its body turns again at frames 1996–1999 in left, confirming manipulation of an unrelated object. This does not advance bowl stacking and causes an unwanted scene change while the bowls remain nested. The wrong-target approach is already underway at the window start; its earlier onset and any continuation beyond the window are unknown.
- Recovery: Release the plush gently onto a clear tabletop area, withdraw without disturbing the bowls, and verify the nested bowls are stable before stopping; human intervention is not evidently needed.
- Severity: low
- Severity evidence: The plush is squeezed and reoriented on or near the tabletop, but no tearing, breakage, spill, or meaningful damage is visible; the bowl stack remains undisturbed in top.
- Resetability: immediate
- Resetability evidence: The plush and bowls remain accessible, with no visible damage or obstruction requiring human resetting; the robot can release the toy and withdraw directly.