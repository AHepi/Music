### 7.6 A bigger area of new slates (`recipe.tiles_across`)

**2 x 2 (2508 dots), re-baked after the look fixes** (`area/area_2x2/`; measures in `area_measures.json`, the old ones in `area_measures_before_look_fixes.json`; 1344 seconds for colour and height with the machine very busy, load average about 7 to 10, against 522 seconds before at a load of about 4;
pictures `area_overview.png` and `new_area_against_copied_tile.jpg`, old ones `..._before_look_fixes`):
* Seams: the jump across the line where a base tile would end is 0.80 (columns) and 0.51 (rows) times a normal jump between neighbouring dots (before 0.78 and 0.58); ordinary columns have a median of 0.98 and rows 0.65 (before 0.96 and 0.74). So the base-tile lines are no different from any other line: no seam.
  (The reference tile itself has 1.7 to 2.5 at its own wrap edge; the wrap-round edge of the area: 0.90 and 0.61.)
* Repeats: the correlation of the area with itself shifted by one base tile is 0.47 / 0.35 / 0.34 (x / y / diagonal) (before 0.44 / 0.29 / 0.27); a real copy gives 1.0; shifts that are NOT a base tile give 0.46 / 0.20 / -0.13 / 0.35 (the background level of a roof with rows).
  Only 23 to 27 % of dots are nearly equal one base tile away (before 18 to 21 %; a copy: 100 %). The four base tiles differ from the first by 7.0 to 8.0 brightness steps on average (before 8.2 to 9.5). The shift correlations are a little higher than before, and so is the background level (the new rows are more regular), so this is not a repeat.
* Same look per dot: each 1254-dot quarter scores 0.831 / 0.795 / 0.804 / 0.805 on the colour group (before 0.701 / 0.751 / 0.705 / 0.752; the default tile 0.822). The top-left quarter is NOT the same picture as the default tile (mean difference about 18 steps of 255); I could not explain why the old table gave the default's exact score (0.701) for it, and the old overview shows
  the same kind of difference (about 16 steps), so the old equality looks like a coincidence of the score, not a copy.
* By eye (`area_overview.png`): one continuous roof, no visible repeat, no line at the tile edges; the facet triangles (section 6b) repeat across the area as landmarks.

![2 x 2 area of new slates](area/area_2x2/area_overview.png)

**4 x 4 (5016 dots, colour only): NOT re-baked, "before the look fixes".** `area/area_4x4/` was baked from the OLD default (it would have taken about 30 to 60 minutes on this busy machine). Its numbers are still true for the old default, and only for it:
* Seams: the jump across the three base-tile lines is 1.07, 1.14 and 0.90 (columns) and 0.66, 0.72, 0.67 (rows) times a normal jump; ordinary columns have a median of 0.98 (90 % of them below 1.15) and ordinary rows 0.74. The base-tile lines are ordinary lines: no seam.
* Repeats: correlation with itself one base tile away 0.42 / 0.34 / 0.33 (x / y / diagonal), a real copy 1.0, shifts that are not a base tile 0.43 / 0.13 / -0.07 / 0.29. The 0.34 straight down is the rows lining up (one base tile is exactly 8 rows), not a repeat: only 19 to 21 % of dots are
  nearly equal one base tile away (a copy: 100 %), and the 16 base tiles differ from the first by 8.3 to 9.7 brightness steps on average.
* Same look per dot: the four 1254-dot quarters of the top-left 2 x 2 score 0.768 / 0.762 / 0.717 / 0.748 on the colour group (the old default tile 0.701).
* By eye (`area_overview.png`, the whole area shrunk to 1254 dots): one continuous roof, no visible repeat, no lines at the tile edges. (1595 seconds, 27 minutes, on 2 threads; the colour picture is 31 MB.)

![4 x 4 area of new slates, shrunk (before the look fixes)](area/area_4x4/area_overview.png)

