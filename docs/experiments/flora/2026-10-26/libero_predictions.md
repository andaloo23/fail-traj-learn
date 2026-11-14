# Preserved FLORA predictions: derived Markdown

This is a readable conversion of historical native JSON generations, not a new
Markdown model response or a human annotation. Native scores, segment boundaries,
rationales and selected rubric reasoning are preserved. No smoothing is applied.
These outputs passed structural checks; semantic correctness remains unverified.
Consult the experiment report for camera and inference configuration limitations.

Dense labels: 1 = failure, 2 = suboptimal, 3 = normal. Rubric totals are scores
under the supplied rubric, not calibrated probabilities. Counts describe predictions.

| Episode | Task | Frames / FPS | Native segments | Segments < 0.5 s | Failure frames | Suboptimal frames | Normal frames | Rubric total |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R001 | pick up the tomato sauce and place it in the basket | 280 / 20 | 48 | 46 | 0 | 136 | 144 | not run |
| R002 | pick up the butter and place it in the basket | 150 / 20 | 1 | 0 | 0 | 0 | 150 | not run |
| R003 | pick up the orange juice and place it in the basket | 280 / 20 | 27 | 24 | 86 | 0 | 194 | not run |
| R004 | pick up the milk and place it in the basket | 280 / 20 | 45 | 43 | 0 | 48 | 232 | not run |
| R005 | pick up the salad dressing and place it in the basket | 280 / 20 | 2 | 0 | 210 | 0 | 70 | not run |
| R006 | pick up the chocolate pudding and place it in the basket | 280 / 20 | 3 | 1 | 244 | 0 | 36 | not run |
| R007 | pick up the alphabet soup and place it in the basket | 280 / 20 | 41 | 39 | 172 | 0 | 108 | not run |
| R008 | pick up the ketchup and place it in the basket | 280 / 20 | 20 | 18 | 210 | 0 | 70 | not run |
| R009 | pick up the bbq sauce and place it in the basket | 280 / 20 | 39 | 36 | 210 | 0 | 70 | not run |
| R010 | pick up the cream cheese and place it in the basket | 121 / 20 | 1 | 0 | 0 | 0 | 121 | not run |
| R011 | pick up the alphabet soup and place it in the basket | 280 / 20 | 17 | 15 | 16 | 0 | 264 | not run |
| R012 | pick up the cream cheese and place it in the basket | 280 / 20 | 65 | 62 | 104 | 0 | 176 | not run |

Times below use the native stored seconds; frame intervals are [start, end).
Duration counts use frame intervals / source FPS rather than rounded seconds.

## R001: pick up the tomato sauce and place it in the basket

| Start (s) | End (s) | Frames [start, end) | Native label | Native rationale |
| --- | --- | --- | --- | --- |
| 0.0 | 4.15 | [0, 83) | normal | (no native rationale) |
| 4.15 | 4.25 | [83, 85) | suboptimal | the left hand is jittering while placing the orange box in the basket |
| 4.25 | 4.4 | [85, 88) | normal | (no native rationale) |
| 4.4 | 4.5 | [88, 90) | suboptimal | the left hand is jittering while placing the orange box in the basket |
| 4.5 | 4.65 | [90, 93) | normal | (no native rationale) |
| 4.65 | 4.75 | [93, 95) | suboptimal | the left hand is jittering while placing the orange box in the basket |
| 4.75 | 4.9 | [95, 98) | normal | (no native rationale) |
| 4.9 | 5.0 | [98, 100) | suboptimal | the left hand is jittering while placing the orange box in the basket |
| 5.0 | 5.15 | [100, 103) | normal | (no native rationale) |
| 5.15 | 5.25 | [103, 105) | suboptimal | the left hand is jittering while placing the orange box in the basket |
| 5.25 | 5.4 | [105, 108) | normal | (no native rationale) |
| 5.4 | 5.5 | [108, 110) | suboptimal | the left hand is jittering while placing the orange box in the basket |
| 5.5 | 5.65 | [110, 113) | normal | (no native rationale) |
| 5.65 | 5.75 | [113, 115) | suboptimal | the left hand is jittering while placing the orange box in the basket |
| 5.75 | 5.9 | [115, 118) | normal | (no native rationale) |
| 5.9 | 6.0 | [118, 120) | suboptimal | the left hand is jittering while placing the orange box in the basket |
| 6.0 | 6.15 | [120, 123) | normal | (no native rationale) |
| 6.15 | 6.25 | [123, 125) | suboptimal | the left hand is jittering while placing the orange box in the basket |
| 6.25 | 6.4 | [125, 128) | normal | (no native rationale) |
| 6.4 | 6.5 | [128, 130) | suboptimal | the left hand is jittering while placing the orange box in the basket |
| 6.5 | 6.65 | [130, 133) | normal | (no native rationale) |
| 6.65 | 6.75 | [133, 135) | suboptimal | the left hand is jittering while placing the orange box in the basket |
| 6.75 | 6.9 | [135, 138) | normal | (no native rationale) |
| 6.9 | 7.0 | [138, 140) | suboptimal | the left hand is jittering while placing the orange box in the basket |
| 7.0 | 7.15 | [140, 143) | normal | (no native rationale) |
| 7.15 | 7.25 | [143, 145) | suboptimal | the left hand is jittering while placing the orange box in the basket |
| 7.25 | 7.4 | [145, 148) | normal | (no native rationale) |
| 7.4 | 7.5 | [148, 150) | suboptimal | the left hand is jittering while placing the orange box in the basket |
| 7.5 | 7.65 | [150, 153) | normal | (no native rationale) |
| 7.65 | 7.75 | [153, 155) | suboptimal | the left hand is jittering while placing the orange box in the basket |
| 7.75 | 7.9 | [155, 158) | normal | (no native rationale) |
| 7.9 | 8.0 | [158, 160) | suboptimal | the left hand is jittering while placing the orange box in the basket |
| 8.0 | 8.1 | [160, 162) | normal | (no native rationale) |
| 8.1 | 8.25 | [162, 165) | suboptimal | the left hand is jittering while placing the orange box in the basket |
| 8.25 | 8.35 | [165, 167) | normal | (no native rationale) |
| 8.35 | 8.5 | [167, 170) | suboptimal | the left hand is jittering while placing the orange box in the basket |
| 8.5 | 8.6 | [170, 172) | normal | (no native rationale) |
| 8.6 | 8.75 | [172, 175) | suboptimal | the left hand is jittering while placing the orange box in the basket |
| 8.75 | 8.85 | [175, 177) | normal | (no native rationale) |
| 8.85 | 9.0 | [177, 180) | suboptimal | the left hand is jittering while placing the orange box in the basket |
| 9.0 | 9.1 | [180, 182) | normal | (no native rationale) |
| 9.1 | 9.25 | [182, 185) | suboptimal | the left hand is jittering while placing the orange box in the basket |
| 9.25 | 9.35 | [185, 187) | normal | (no native rationale) |
| 9.35 | 9.5 | [187, 190) | suboptimal | the left hand is jittering while placing the orange box in the basket |
| 9.5 | 9.6 | [190, 192) | normal | (no native rationale) |
| 9.6 | 9.75 | [192, 195) | suboptimal | the left hand is jittering while placing the orange box in the basket |
| 9.75 | 9.85 | [195, 197) | normal | (no native rationale) |
| 9.85 | 14.0 | [197, 280) | suboptimal | the left hand is jittering while placing the orange box in the basket |

## R002: pick up the butter and place it in the basket

| Start (s) | End (s) | Frames [start, end) | Native label | Native rationale |
| --- | --- | --- | --- | --- |
| 0.0 | 7.5 | [0, 150) | normal | (no native rationale) |

## R003: pick up the orange juice and place it in the basket

| Start (s) | End (s) | Frames [start, end) | Native label | Native rationale |
| --- | --- | --- | --- | --- |
| 0.0 | 1.4 | [0, 28) | normal | (no native rationale) |
| 1.4 | 4.5 | [28, 90) | failure | the grasp is unstable |
| 4.5 | 4.65 | [90, 93) | normal | (no native rationale) |
| 4.65 | 4.75 | [93, 95) | failure | the robot did not pick up the orange juice carton |
| 4.75 | 4.9 | [95, 98) | normal | (no native rationale) |
| 4.9 | 5.0 | [98, 100) | failure | the robot did not pick up the orange juice carton |
| 5.0 | 5.15 | [100, 103) | normal | (no native rationale) |
| 5.15 | 5.25 | [103, 105) | failure | the robot did not pick up the orange juice carton |
| 5.25 | 5.4 | [105, 108) | normal | (no native rationale) |
| 5.4 | 5.5 | [108, 110) | failure | the robot did not pick up the orange juice carton |
| 5.5 | 5.65 | [110, 113) | normal | (no native rationale) |
| 5.65 | 5.75 | [113, 115) | failure | the robot did not pick up the orange juice carton |
| 5.75 | 5.9 | [115, 118) | normal | (no native rationale) |
| 5.9 | 6.0 | [118, 120) | failure | the robot did not pick up the orange juice carton |
| 6.0 | 6.15 | [120, 123) | normal | (no native rationale) |
| 6.15 | 6.25 | [123, 125) | failure | the robot did not pick up the orange juice carton |
| 6.25 | 6.4 | [125, 128) | normal | (no native rationale) |
| 6.4 | 6.5 | [128, 130) | failure | the robot did not pick up the orange juice carton |
| 6.5 | 6.65 | [130, 133) | normal | (no native rationale) |
| 6.65 | 6.75 | [133, 135) | failure | the robot did not pick up the orange juice carton |
| 6.75 | 6.9 | [135, 138) | normal | (no native rationale) |
| 6.9 | 7.0 | [138, 140) | failure | the robot did not pick up the orange juice carton |
| 7.0 | 7.15 | [140, 143) | normal | (no native rationale) |
| 7.15 | 7.25 | [143, 145) | failure | the robot did not pick up the orange juice carton |
| 7.25 | 7.4 | [145, 148) | normal | (no native rationale) |
| 7.4 | 7.5 | [148, 150) | failure | the robot did not pick up the orange juice carton |
| 7.5 | 14.0 | [150, 280) | normal | (no native rationale) |

## R004: pick up the milk and place it in the basket

| Start (s) | End (s) | Frames [start, end) | Native label | Native rationale |
| --- | --- | --- | --- | --- |
| 0.0 | 3.65 | [0, 73) | normal | (no native rationale) |
| 3.65 | 3.75 | [73, 75) | suboptimal | the milk carton is placed on the edge of the white basket with the left hand |
| 3.75 | 3.9 | [75, 78) | normal | (no native rationale) |
| 3.9 | 4.0 | [78, 80) | suboptimal | the milk carton is placed on the edge of the white basket with the left hand |
| 4.0 | 4.15 | [80, 83) | normal | (no native rationale) |
| 4.15 | 4.25 | [83, 85) | suboptimal | the milk carton is placed on the edge of the white basket with the left hand |
| 4.25 | 4.4 | [85, 88) | normal | (no native rationale) |
| 4.4 | 4.5 | [88, 90) | suboptimal | the milk carton is placed on the edge of the white basket with the left hand |
| 4.5 | 4.65 | [90, 93) | normal | (no native rationale) |
| 4.65 | 4.75 | [93, 95) | suboptimal | the milk carton is placed on the edge of the white basket with the left hand |
| 4.75 | 4.9 | [95, 98) | normal | (no native rationale) |
| 4.9 | 5.0 | [98, 100) | suboptimal | the milk carton is placed on the edge of the white basket with the left hand |
| 5.0 | 5.15 | [100, 103) | normal | (no native rationale) |
| 5.15 | 5.25 | [103, 105) | suboptimal | the milk carton is placed on the edge of the white basket with the left hand |
| 5.25 | 5.4 | [105, 108) | normal | (no native rationale) |
| 5.4 | 5.5 | [108, 110) | suboptimal | the milk carton is placed on the edge of the white basket with the left hand |
| 5.5 | 5.65 | [110, 113) | normal | (no native rationale) |
| 5.65 | 5.75 | [113, 115) | suboptimal | the milk carton is placed on the edge of the white basket with the left hand |
| 5.75 | 5.9 | [115, 118) | normal | (no native rationale) |
| 5.9 | 6.0 | [118, 120) | suboptimal | the milk carton is placed on the edge of the white basket with the left hand |
| 6.0 | 6.15 | [120, 123) | normal | (no native rationale) |
| 6.15 | 6.25 | [123, 125) | suboptimal | the milk carton is placed on the edge of the white basket with the left hand |
| 6.25 | 6.4 | [125, 128) | normal | (no native rationale) |
| 6.4 | 6.5 | [128, 130) | suboptimal | the milk carton is placed on the edge of the white basket with the left hand |
| 6.5 | 6.65 | [130, 133) | normal | (no native rationale) |
| 6.65 | 6.75 | [133, 135) | suboptimal | the milk carton is placed on the edge of the white basket with the left hand |
| 6.75 | 6.9 | [135, 138) | normal | (no native rationale) |
| 6.9 | 7.0 | [138, 140) | suboptimal | the milk carton is placed on the edge of the white basket with the left hand |
| 7.0 | 7.15 | [140, 143) | normal | (no native rationale) |
| 7.15 | 7.25 | [143, 145) | suboptimal | the milk carton is placed on the edge of the white basket with the left hand |
| 7.25 | 7.4 | [145, 148) | normal | (no native rationale) |
| 7.4 | 7.5 | [148, 150) | suboptimal | the milk carton is placed on the edge of the white basket with the left hand |
| 7.5 | 7.65 | [150, 153) | normal | (no native rationale) |
| 7.65 | 7.75 | [153, 155) | suboptimal | the milk carton is placed on the edge of the white basket with the left hand |
| 7.75 | 7.9 | [155, 158) | normal | (no native rationale) |
| 7.9 | 8.0 | [158, 160) | suboptimal | the milk carton is placed on the edge of the white basket with the left hand |
| 8.0 | 8.1 | [160, 162) | normal | (no native rationale) |
| 8.1 | 8.25 | [162, 165) | suboptimal | the milk carton is placed on the edge of the white basket with the left hand |
| 8.25 | 8.35 | [165, 167) | normal | (no native rationale) |
| 8.35 | 8.5 | [167, 170) | suboptimal | the milk carton is placed on the edge of the white basket with the left hand |
| 8.5 | 8.6 | [170, 172) | normal | (no native rationale) |
| 8.6 | 8.75 | [172, 175) | suboptimal | the milk carton is placed on the edge of the white basket with the left hand |
| 8.75 | 8.85 | [175, 177) | normal | (no native rationale) |
| 8.85 | 9.0 | [177, 180) | suboptimal | the milk carton is placed on the edge of the white basket with the left hand |
| 9.0 | 14.0 | [180, 280) | normal | (no native rationale) |

## R005: pick up the salad dressing and place it in the basket

| Start (s) | End (s) | Frames [start, end) | Native label | Native rationale |
| --- | --- | --- | --- | --- |
| 0.0 | 3.5 | [0, 70) | normal | (no native rationale) |
| 3.5 | 14.0 | [70, 280) | failure | the bottle is not placed in the basket because the bottle was not handed over |

## R006: pick up the chocolate pudding and place it in the basket

| Start (s) | End (s) | Frames [start, end) | Native label | Native rationale |
| --- | --- | --- | --- | --- |
| 0.0 | 1.4 | [0, 28) | normal | (no native rationale) |
| 1.4 | 13.6 | [28, 272) | failure | the robot was not able to grasp the chocolate pudding |
| 13.6 | 14.0 | [272, 280) | normal | (no native rationale) |

## R007: pick up the alphabet soup and place it in the basket

| Start (s) | End (s) | Frames [start, end) | Native label | Native rationale |
| --- | --- | --- | --- | --- |
| 0.0 | 2.15 | [0, 43) | normal | (no native rationale) |
| 2.15 | 2.25 | [43, 45) | failure | the grasp is unstable |
| 2.25 | 2.4 | [45, 48) | normal | (no native rationale) |
| 2.4 | 2.5 | [48, 50) | failure | the grasp is unstable |
| 2.5 | 2.65 | [50, 53) | normal | (no native rationale) |
| 2.65 | 2.75 | [53, 55) | failure | the grasp is unstable |
| 2.75 | 2.9 | [55, 58) | normal | (no native rationale) |
| 2.9 | 3.0 | [58, 60) | failure | the grasp is unstable |
| 3.0 | 3.15 | [60, 63) | normal | (no native rationale) |
| 3.15 | 3.25 | [63, 65) | failure | the grasp is unstable |
| 3.25 | 3.4 | [65, 68) | normal | (no native rationale) |
| 3.4 | 3.5 | [68, 70) | failure | the grasp is unstable |
| 3.5 | 3.65 | [70, 73) | normal | (no native rationale) |
| 3.65 | 3.75 | [73, 75) | failure | the grasp is unstable |
| 3.75 | 3.9 | [75, 78) | normal | (no native rationale) |
| 3.9 | 4.0 | [78, 80) | failure | the grasp is unstable |
| 4.0 | 4.15 | [80, 83) | normal | (no native rationale) |
| 4.15 | 4.25 | [83, 85) | failure | the grasp is unstable |
| 4.25 | 4.4 | [85, 88) | normal | (no native rationale) |
| 4.4 | 4.5 | [88, 90) | failure | the grasp is unstable |
| 4.5 | 4.65 | [90, 93) | normal | (no native rationale) |
| 4.65 | 4.75 | [93, 95) | failure | the grasp is unstable |
| 4.75 | 4.9 | [95, 98) | normal | (no native rationale) |
| 4.9 | 5.0 | [98, 100) | failure | the grasp is unstable |
| 5.0 | 5.15 | [100, 103) | normal | (no native rationale) |
| 5.15 | 5.25 | [103, 105) | failure | the grasp is unstable |
| 5.25 | 5.4 | [105, 108) | normal | (no native rationale) |
| 5.4 | 5.5 | [108, 110) | failure | the grasp is unstable |
| 5.5 | 5.65 | [110, 113) | normal | (no native rationale) |
| 5.65 | 5.75 | [113, 115) | failure | the grasp is unstable |
| 5.75 | 5.9 | [115, 118) | normal | (no native rationale) |
| 5.9 | 6.0 | [118, 120) | failure | the grasp is unstable |
| 6.0 | 6.15 | [120, 123) | normal | (no native rationale) |
| 6.15 | 6.25 | [123, 125) | failure | the grasp is unstable |
| 6.25 | 6.4 | [125, 128) | normal | (no native rationale) |
| 6.4 | 6.5 | [128, 130) | failure | the grasp is unstable |
| 6.5 | 6.65 | [130, 133) | normal | (no native rationale) |
| 6.65 | 6.75 | [133, 135) | failure | the grasp is unstable |
| 6.75 | 6.9 | [135, 138) | normal | (no native rationale) |
| 6.9 | 13.6 | [138, 272) | failure | the grasp is unstable |
| 13.6 | 14.0 | [272, 280) | normal | (no native rationale) |

## R008: pick up the ketchup and place it in the basket

| Start (s) | End (s) | Frames [start, end) | Native label | Native rationale |
| --- | --- | --- | --- | --- |
| 0.0 | 2.15 | [0, 43) | normal | (no native rationale) |
| 2.15 | 2.25 | [43, 45) | failure | the grasp is unstable |
| 2.25 | 2.4 | [45, 48) | normal | (no native rationale) |
| 2.4 | 2.5 | [48, 50) | failure | the grasp is unstable |
| 2.5 | 2.65 | [50, 53) | normal | (no native rationale) |
| 2.65 | 2.75 | [53, 55) | failure | the grasp is unstable |
| 2.75 | 2.9 | [55, 58) | normal | (no native rationale) |
| 2.9 | 3.0 | [58, 60) | failure | the grasp is unstable |
| 3.0 | 3.15 | [60, 63) | normal | (no native rationale) |
| 3.15 | 3.25 | [63, 65) | failure | the grasp is unstable |
| 3.25 | 3.4 | [65, 68) | normal | (no native rationale) |
| 3.4 | 3.5 | [68, 70) | failure | the grasp is unstable |
| 3.5 | 3.65 | [70, 73) | normal | (no native rationale) |
| 3.65 | 3.75 | [73, 75) | failure | the grasp is unstable |
| 3.75 | 3.9 | [75, 78) | normal | (no native rationale) |
| 3.9 | 4.0 | [78, 80) | failure | the grasp is unstable |
| 4.0 | 4.15 | [80, 83) | normal | (no native rationale) |
| 4.15 | 4.25 | [83, 85) | failure | the grasp is unstable |
| 4.25 | 4.4 | [85, 88) | normal | (no native rationale) |
| 4.4 | 14.0 | [88, 280) | failure | the grasp is unstable |

## R009: pick up the bbq sauce and place it in the basket

| Start (s) | End (s) | Frames [start, end) | Native label | Native rationale |
| --- | --- | --- | --- | --- |
| 0.0 | 3.65 | [0, 73) | failure | the grasp is unstable |
| 3.65 | 3.75 | [73, 75) | normal | (no native rationale) |
| 3.75 | 3.9 | [75, 78) | failure | the grasp is unstable |
| 3.9 | 4.0 | [78, 80) | normal | (no native rationale) |
| 4.0 | 4.15 | [80, 83) | failure | the grasp is unstable |
| 4.15 | 4.25 | [83, 85) | normal | (no native rationale) |
| 4.25 | 4.4 | [85, 88) | failure | the grasp is unstable |
| 4.4 | 4.5 | [88, 90) | normal | (no native rationale) |
| 4.5 | 4.65 | [90, 93) | failure | the grasp is unstable |
| 4.65 | 4.75 | [93, 95) | normal | (no native rationale) |
| 4.75 | 4.9 | [95, 98) | failure | the grasp is unstable |
| 4.9 | 5.0 | [98, 100) | normal | (no native rationale) |
| 5.0 | 5.15 | [100, 103) | failure | the grasp is unstable |
| 5.15 | 5.25 | [103, 105) | normal | (no native rationale) |
| 5.25 | 5.4 | [105, 108) | failure | the grasp is unstable |
| 5.4 | 5.5 | [108, 110) | normal | (no native rationale) |
| 5.5 | 5.65 | [110, 113) | failure | the grasp is unstable |
| 5.65 | 5.75 | [113, 115) | normal | (no native rationale) |
| 5.75 | 5.9 | [115, 118) | failure | the grasp is unstable |
| 5.9 | 6.0 | [118, 120) | normal | (no native rationale) |
| 6.0 | 6.15 | [120, 123) | failure | the grasp is unstable |
| 6.15 | 6.25 | [123, 125) | normal | (no native rationale) |
| 6.25 | 6.4 | [125, 128) | failure | the grasp is unstable |
| 6.4 | 8.1 | [128, 162) | normal | (no native rationale) |
| 8.1 | 8.25 | [162, 165) | failure | the brown bottle is misaligned with the basket |
| 8.25 | 8.35 | [165, 167) | normal | (no native rationale) |
| 8.35 | 8.5 | [167, 170) | failure | the brown bottle is misaligned with the basket |
| 8.5 | 8.6 | [170, 172) | normal | (no native rationale) |
| 8.6 | 8.75 | [172, 175) | failure | the brown bottle is misaligned with the basket |
| 8.75 | 8.85 | [175, 177) | normal | (no native rationale) |
| 8.85 | 9.0 | [177, 180) | failure | the brown bottle is misaligned with the basket |
| 9.0 | 9.1 | [180, 182) | normal | (no native rationale) |
| 9.1 | 9.25 | [182, 185) | failure | the brown bottle is misaligned with the basket |
| 9.25 | 9.35 | [185, 187) | normal | (no native rationale) |
| 9.35 | 9.5 | [187, 190) | failure | the brown bottle is misaligned with the basket |
| 9.5 | 9.6 | [190, 192) | normal | (no native rationale) |
| 9.6 | 9.75 | [192, 195) | failure | the brown bottle is misaligned with the basket |
| 9.75 | 9.85 | [195, 197) | normal | (no native rationale) |
| 9.85 | 14.0 | [197, 280) | failure | the brown bottle is misaligned with the basket |

## R010: pick up the cream cheese and place it in the basket

| Start (s) | End (s) | Frames [start, end) | Native label | Native rationale |
| --- | --- | --- | --- | --- |
| 0.0 | 6.05 | [0, 121) | normal | (no native rationale) |

## R011: pick up the alphabet soup and place it in the basket

| Start (s) | End (s) | Frames [start, end) | Native label | Native rationale |
| --- | --- | --- | --- | --- |
| 0.0 | 2.15 | [0, 43) | normal | (no native rationale) |
| 2.15 | 2.25 | [43, 45) | failure | the grasp is unstable due to misalignment of the right hand and the cylindrical can |
| 2.25 | 2.4 | [45, 48) | normal | (no native rationale) |
| 2.4 | 2.5 | [48, 50) | failure | the grasp is unstable due to misalignment of the right hand and the cylindrical can |
| 2.5 | 2.65 | [50, 53) | normal | (no native rationale) |
| 2.65 | 2.75 | [53, 55) | failure | the grasp is unstable due to misalignment of the right hand and the cylindrical can |
| 2.75 | 2.9 | [55, 58) | normal | (no native rationale) |
| 2.9 | 3.0 | [58, 60) | failure | the grasp is unstable due to misalignment of the right hand and the cylindrical can |
| 3.0 | 3.15 | [60, 63) | normal | (no native rationale) |
| 3.15 | 3.25 | [63, 65) | failure | the grasp is unstable due to misalignment of the right hand and the cylindrical can |
| 3.25 | 3.4 | [65, 68) | normal | (no native rationale) |
| 3.4 | 3.5 | [68, 70) | failure | the grasp is unstable due to misalignment of the right hand and the cylindrical can |
| 3.5 | 3.65 | [70, 73) | normal | (no native rationale) |
| 3.65 | 3.75 | [73, 75) | failure | the grasp is unstable due to misalignment of the right hand and the cylindrical can |
| 3.75 | 3.9 | [75, 78) | normal | (no native rationale) |
| 3.9 | 4.0 | [78, 80) | failure | the grasp is unstable due to misalignment of the right hand and the cylindrical can |
| 4.0 | 14.0 | [80, 280) | normal | (no native rationale) |

## R012: pick up the cream cheese and place it in the basket

| Start (s) | End (s) | Frames [start, end) | Native label | Native rationale |
| --- | --- | --- | --- | --- |
| 0.0 | 2.15 | [0, 43) | normal | (no native rationale) |
| 2.15 | 2.25 | [43, 45) | failure | due to poor grip of the right hand |
| 2.25 | 2.4 | [45, 48) | normal | (no native rationale) |
| 2.4 | 2.5 | [48, 50) | failure | due to poor grip of the right hand |
| 2.5 | 2.65 | [50, 53) | normal | (no native rationale) |
| 2.65 | 2.75 | [53, 55) | failure | due to poor grip of the right hand |
| 2.75 | 2.9 | [55, 58) | normal | (no native rationale) |
| 2.9 | 3.0 | [58, 60) | failure | due to poor grip of the right hand |
| 3.0 | 3.15 | [60, 63) | normal | (no native rationale) |
| 3.15 | 3.25 | [63, 65) | failure | due to poor grip of the right hand |
| 3.25 | 3.4 | [65, 68) | normal | (no native rationale) |
| 3.4 | 3.5 | [68, 70) | failure | due to poor grip of the right hand |
| 3.5 | 3.65 | [70, 73) | normal | (no native rationale) |
| 3.65 | 3.75 | [73, 75) | failure | due to poor grip of the right hand |
| 3.75 | 3.9 | [75, 78) | normal | (no native rationale) |
| 3.9 | 4.0 | [78, 80) | failure | due to poor grip of the right hand |
| 4.0 | 4.15 | [80, 83) | normal | (no native rationale) |
| 4.15 | 4.25 | [83, 85) | failure | due to poor grip of the right hand |
| 4.25 | 4.4 | [85, 88) | normal | (no native rationale) |
| 4.4 | 4.5 | [88, 90) | failure | due to poor grip of the right hand |
| 4.5 | 4.65 | [90, 93) | normal | (no native rationale) |
| 4.65 | 4.75 | [93, 95) | failure | due to poor grip of the right hand |
| 4.75 | 4.9 | [95, 98) | normal | (no native rationale) |
| 4.9 | 5.0 | [98, 100) | failure | due to poor grip of the right hand |
| 5.0 | 5.15 | [100, 103) | normal | (no native rationale) |
| 5.15 | 5.25 | [103, 105) | failure | due to poor grip of the right hand |
| 5.25 | 5.4 | [105, 108) | normal | (no native rationale) |
| 5.4 | 5.5 | [108, 110) | failure | due to poor grip of the right hand |
| 5.5 | 5.65 | [110, 113) | normal | (no native rationale) |
| 5.65 | 5.75 | [113, 115) | failure | due to poor grip of the right hand |
| 5.75 | 5.9 | [115, 118) | normal | (no native rationale) |
| 5.9 | 6.0 | [118, 120) | failure | due to poor grip of the right hand |
| 6.0 | 6.15 | [120, 123) | normal | (no native rationale) |
| 6.15 | 6.25 | [123, 125) | failure | due to poor grip of the right hand |
| 6.25 | 6.4 | [125, 128) | normal | (no native rationale) |
| 6.4 | 6.5 | [128, 130) | failure | due to poor grip of the right hand |
| 6.5 | 6.65 | [130, 133) | normal | (no native rationale) |
| 6.65 | 6.75 | [133, 135) | failure | due to poor grip of the right hand |
| 6.75 | 6.9 | [135, 138) | normal | (no native rationale) |
| 6.9 | 7.0 | [138, 140) | failure | due to poor grip of the right hand |
| 7.0 | 7.15 | [140, 143) | normal | (no native rationale) |
| 7.15 | 7.25 | [143, 145) | failure | due to poor grip of the right hand |
| 7.25 | 7.4 | [145, 148) | normal | (no native rationale) |
| 7.4 | 7.5 | [148, 150) | failure | due to poor grip of the right hand |
| 7.5 | 7.65 | [150, 153) | normal | (no native rationale) |
| 7.65 | 7.75 | [153, 155) | failure | due to poor grip of the right hand |
| 7.75 | 7.9 | [155, 158) | normal | (no native rationale) |
| 7.9 | 8.0 | [158, 160) | failure | due to poor grip of the right hand |
| 8.0 | 8.1 | [160, 162) | normal | (no native rationale) |
| 8.1 | 8.25 | [162, 165) | failure | due to poor grip of the right hand |
| 8.25 | 8.35 | [165, 167) | normal | (no native rationale) |
| 8.35 | 8.5 | [167, 170) | failure | due to poor grip of the right hand |
| 8.5 | 8.6 | [170, 172) | normal | (no native rationale) |
| 8.6 | 8.75 | [172, 175) | failure | due to poor grip of the right hand |
| 8.75 | 8.85 | [175, 177) | normal | (no native rationale) |
| 8.85 | 9.0 | [177, 180) | failure | due to poor grip of the right hand |
| 9.0 | 9.1 | [180, 182) | normal | (no native rationale) |
| 9.1 | 9.25 | [182, 185) | failure | due to poor grip of the right hand |
| 9.25 | 9.35 | [185, 187) | normal | (no native rationale) |
| 9.35 | 9.5 | [187, 190) | failure | due to poor grip of the right hand |
| 9.5 | 9.6 | [190, 192) | normal | (no native rationale) |
| 9.6 | 9.75 | [192, 195) | failure | due to poor grip of the right hand |
| 9.75 | 9.85 | [195, 197) | normal | (no native rationale) |
| 9.85 | 11.6 | [197, 232) | failure | due to poor grip of the right hand |
| 11.6 | 14.0 | [232, 280) | normal | (no native rationale) |

## Source integrity

| Input | SHA-256 |
| --- | --- |
| dense: dense.jsonl | `777f91e69140c0207b9ed02c5e9fb0435deab7ea107d193122f44e20b47de3d3` |
| dense_jobs: jobs.jsonl | `977391e3092865216674b16a241e5fbccbd6769133a28009f5492b3340ecad74` |
