# Episode: C0726

## Episode annotation

- Language task: Pick up one object from the big bowl and put it inside the small box that is empty.
- Success label: failure
- Outcome evidence: Camera right and camera top at frame 0 show an orange source container inside the bowl, distinct from the smaller empty orange destination box on the table. Cameras left and right at frames 690–720 show extraction of that source container; cameras left and top at frames 791–795 show its release onto the table. Later handling concerns the same source container, not the destination. At frames 1998–1999, cameras left and top show the container still held near the bowl and the separate destination empty. Completion is unconfirmed at the ending, with earlier visibly failed transfer attempts established; the ending alone does not establish abnormal termination.

## Timeline

| Start frame | End frame | Failure |
| --- | --- | --- |
| 0 | 325 | No |
| 325 | 367 | Yes |
| 367 | 447 | No |
| 447 | 461 | Yes |
| 461 | 791 | No |
| 791 | 797 | Yes |
| 797 | 1050 | No |
| 1050 | 1080 | Yes |
| 1080 | 1320 | No |
| 1320 | 1327 | Yes |
| 1327 | 1620 | No |
| 1620 | 2000 | Yes |

## Failure annotations

### Failure 1

- Frames: 325-367
- Categories: collision
- Explanation: While engaging the orange source container, the robot also tips the large blue bowl, visibly beginning at frame 325 and becoming pronounced at frames 330–366 in cameras right and left. This disturbs the source arrangement rather than cleanly extracting the object; the exact contact mechanism is obscured. Returning the bowl toward upright begins at frames 367–368 and is excluded.
- Recovery: Gently stabilize and lower the bowl, disengage from its rim, and realign around the source object; human assistance is needed only if safe autonomous stabilization is unavailable.
- Severity: low
- Severity evidence: The bowl tilts and its contents shift, but no breakage or spill outside the bowl is visible in cameras left and right at frames 330–366.
- Resetability: minor_reset
- Resetability evidence: The tilted bowl in cameras left and right at frames 350–366 needs straightforward local stabilization and a contents check; no repair or difficult retrieval is visibly required.

### Failure 2

- Frames: 447-461
- Categories: grasp
- Explanation: Following contact with the source container, the gripper withdraws empty while the container remains inside the bowl in cameras left, right and top at frames 447–460. This establishes unsuccessful acquisition; reorientation for another attempt follows.
- Recovery: Reopen and align around an accessible edge, establish a secure grasp, and verify retention with a small lift before transport; no human intervention is indicated.
- Severity: low
- Severity evidence: Camera right at frames 447–460 shows the container remaining supported inside the bowl, with no visible damage or spill.
- Resetability: immediate
- Resetability evidence: Cameras left and right at frames 459–461 show the bowl and source container still accessible for another attempt without environmental resetting.

### Failure 3

- Frames: 791-797
- Categories: grasp
- Explanation: The previously carried source container separates from the gripper, rotates downward, and lands on the table beside the bowl rather than inside the destination in cameras left and top at frames 791–796. Whether it slips or is prematurely released is not established. Reorientation toward recovery begins at frame 797.
- Recovery: Reacquire the container, verify retention, then transport it over the separate destination before lowering and releasing; no human assistance is visibly necessary.
- Severity: low
- Severity evidence: Cameras left and top at frames 795–798 show the container intact and accessible on the tabletop, with no visible damage or spillage.
- Resetability: immediate
- Resetability evidence: Camera top at frames 795–798 shows the container within the robot's workspace, permitting reacquisition without human resetting.

### Failure 4

- Frames: 1050-1080
- Categories: grasp
- Explanation: After reacquisition and transport at frames 930–1049, the source container is again released beside the bowl rather than into the smaller box: camera left shows the transition from a held, tilted container at frame 1049 to a separated upright container at frames 1050–1051, remaining on the table at frame 1080. Slipping versus deliberate premature release is uncertain; the precise transition from withdrawal to renewed approach is only bounded by the supplied checks.
- Recovery: Reacquire the source container and retain it until it is supported inside the intended destination; check fit first and select a smaller bowl object if necessary. No human intervention is indicated.
- Severity: low
- Severity evidence: Cameras left and top at frames 1050–1080 show the container remaining on the table without visible damage or spilled contents.
- Resetability: immediate
- Resetability evidence: Camera left at frames 1050–1080 shows the released container upright and accessible, so no environmental reset is required.

### Failure 5

- Frames: 1320-1327
- Categories: grasp
- Explanation: Following another successful acquisition, the robot again releases the source container onto the tabletop beside the bowl instead of into the destination in cameras left and top at frames 1320–1326. The container is separated from the withdrawing fingers by frame 1326. This is an off-target release, not evidence that the robot acquired the wrong object.
- Recovery: Reacquire the source container and carry it to the separate smaller box before releasing; if it cannot fit, set it down safely and select a smaller object from the bowl. No human assistance is visibly required.
- Severity: low
- Severity evidence: Cameras left and top at frames 1324–1327 show the container upright on the table, with no visible damage or harmful spill.
- Resetability: immediate
- Resetability evidence: Cameras left and top at frames 1326–1327 show the source container, bowl contents, and destination accessible without repair or manual resetting.

### Failure 6

- Frames: 1620-2000
- Categories: other
- Explanation: After reacquiring the same source container and moving it beside the bowl at frames 1500–1590, the robot begins another sustained excursion away from the destination at frame 1620. Camera top shows transport toward the far table edge through frames 1650–1800, followed by a return beside and over the bowl at frames 1830–1999 without destination placement. Camera left confirms continued retention. This repeated unproductive transport is not wrong-object handling: the carried container originated inside the bowl. The final return does not visibly establish renewed destination-directed progress.
- Recovery: Stop the repeated excursions and plan a direct, collision-free transfer to the smaller destination; check fit before lowering. If the container cannot fit, set it down safely and transfer a suitably sized bowl object instead. No human intervention is visibly necessary.
- Severity: low
- Severity evidence: Cameras left and top at frames 1620–1999 show continued retention without established damage, spill, or harmful collision; the visible consequence is prolonged failure to complete placement.
- Resetability: immediate
- Resetability evidence: Cameras left and top at frames 1998–1999 show the robot still controlling the container and the destination remaining accessible, permitting task-directed continuation without environmental repair or human reset.