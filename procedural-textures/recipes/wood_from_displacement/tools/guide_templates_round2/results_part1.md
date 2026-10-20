### 7.1 "Same kind of surface" score against the reference wood

(`lib/texture_compare.py`: 0 = as different as another real surface, 1 = indistinguishable by those measures; other real surfaces score 0.16 to 0.50; a re-shuffled copy of the reference itself about 0.99.) The earlier wood recipe's best new tile (its seed 105) was baked again from its own description at 1254 dots for round 1 and scored with the same tool.

**Read these numbers with two cautions.** First, the new tile is made from the reference's own dots, rearranged, and the earlier recipe used nodes only: the comparison is not like for like, and the new amounts were chosen partly by looking at this score (round 1: "a compromise between score and hiding repeats"). Second, the "tiling" part of the score measures the jump across the wrap-around edge; it fell from 1.00 in round 1 to @@TILING_RANGE@@ in round 2 (MAIN seeds) because the dark band at the tile edge is no longer a uniform strip: the real gap rubble of the source (pebbles, bright lips of wood) is kept there. This is my explanation, and I checked the part that can be checked: the jump across the tile edge is no bigger than the jumps across the ordinary row boundaries inside the same tile (table below; the edge is a row boundary like the others), and the slide test (7.2) and the look at the tile corner (`sheets/seam_2x2.jpg`) and at the wrap-around strips show no seam; the uploaded map itself would score far worse (its wrap jump is 2.8 to 4.0 times a typical jump, against @@WRAP_TB@@ and @@WRAP_LR@@ here for seed 1). What I did not test is a variant with a uniform dark band at the tile edge only (round 1's way) to confirm that the rubble is the whole reason.

@@EDGE_VS_ROW_TABLE@@

@@SCORES_TABLE@@

The measures behind the scores (seed 1):

@@MEASURES_TABLE@@

Read this as: the round 2 tile (MAIN seed 1) is closer to the reference than the earlier recipe's tile on @@MEASURES_BETTER@@ of the @@MEASURES_TOTAL@@ measures (by more than 0.005), and worse on: @@MEASURES_WORSE@@. The COMPARISON colour (made from the height with palettes) is plainer than the colour map; its weakest number is colour_spectrum. The tool rewards staying close to the map's own statistics, so every thing that breaks repetition (stains, patches, tone, bending) costs score.

**Dot-for-dot numbers (for transparency only).** The new boards are not where the reference's boards are, so these are low on purpose and say nothing about quality. Two height numbers are shown: the plain error, and the error after the best brightness and contrast fit (the honesty checker pointed out that the fit collapses to a flat grey, so the second column is the same for every picture and says nothing; round 1 printed only that one):

@@PIXEL_TABLE@@

### 7.2 The pipeline adds nothing of its own, and the tile repeats exactly

@@PIPELINE_TABLE@@

The wrap-around edge of the three default tiles (a seamless tile gives about 1; the uploaded map gives 2.8 to 4.0):

@@EDGE_TABLE@@

![the tile repeated 2 x 2, and the uploaded map repeated 2 x 2](sheets/seam_2x2.jpg)

The 2 x 2 picture on the left is four copies of one default tile: I see no step at the yellow tick marks, only the tile's own row gap at the horizontal line. The uploaded map repeated the same way (right) shows a straight seam.

@@SEAM2X2_TABLE@@

(A jump of about 1 is no seam. Row boundaries jump more than a typical dot line because every row boundary is a dark band with pebbles; the horizontal tile line is itself a row boundary and jumps less than the largest of the others. The "mean difference between the four tiles" is the render noise of the 4-sample shrink: the picture is baked at 2 dots per picture dot; the shift test below scores the same picture 0.997 at one tile.)

### 7.3 Does a big area repeat? (the REPEAT test)

![before and after: the plain repeat, round 1, round 2](sheets/before_after.jpg)

![the 4 x 4 area, shrunk](sheets/area_4x4.jpg)

![full-size crops of the 4 x 4 area](sheets/area_crops.jpg)

**(a) Shift test** (how much the picture looks like itself slid sideways; 1 = identical, 0 = nothing alike). The control, the uploaded map repeated 4 x 4, is made with a whole number of dots per tile (313), so an exact repeat scores 1.0; round 1 reported 0.972 because its control was half a dot out.

@@SHIFT_TABLE@@

**(b) How much of the source map is used, and how the neighbours are chosen** (from the exact "which source dot" and "which board" pictures of the 4 x 4 area, baked at 1254 dots across with one exact dot per picture dot; round 1 baked these at 2508 dots across, so "used at least once" is NOT comparable: with fewer samples fewer source dots are hit. The average cannot be below 19 anyway: 16 tiles of dots from the 1.34 million dots of the four usable rows):

@@REUSE_TABLE@@

**(c) Near copies.** Two tests on the same pictures. The research test (the one of round 1): 40 board-sized patches (36 x 80 at 1024 dots) are searched for in the other rows, also flipped; a best match above 0.8 = "has a near copy". The look checker's test: 50 pieces of 200 x 380 dots are searched everywhere in the area, in all four ways round (as is, left-right, upside down, both); unrelated pieces of wood score a median 0.25 to 0.3 and a plain repeat 1.0. Both tests were run on the round 1 area (kept in `round1/area_4x4`) and on the round 2 area, by the same code, so the numbers compare. Two draws of 50 pieces show the noise of the test (a few points).

@@NEAR_RESEARCH_TABLE@@

@@NEAR_CHECKER_TABLE@@

**(d) Landmarks.** How often each of the twelve landmarks is shown in the 4 x 4 area (16 tiles); a landmark in a window is shown with chance 0.15 (knots) or 0.12 (others), otherwise painted out. Round 1 had no such list: every window that contained a knot showed it (24 knot boards in 16 tiles).

@@LANDMARK_TABLE@@

**(e) What each part buys** (4 x 4 areas of height at 1024 dots, 2 samples, seed 1, with parts switched off; the same two tests):

@@SWITCH_TABLE@@

@@SWITCH_READING@@
