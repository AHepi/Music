### 7.5 Seamless (the half-tile test, **re-run after the look fixes**)

`tests/half_tile_layers/half_tile_table.md` (512 dots; the recipe's `shift` parameter slides everything by half a picture; the old table is `half_tile_table_before_look_fixes.md` and `.json`). Mean difference in
steps of 255; "control" = the same comparison with the picture rolled 7 dots too far, which must differ a lot. **Eight Blender runs, on the NEW default settings.**

| tiles across | picture | raw mean difference (before) | after a 2-dot blur (before) | control (blurred) |
|---|---|---|---|---|
| 1 | finished colour | 1.65 (1.83) | 0.31 (0.34) | 15.0 |
| 1 | finished height | 2.19 (2.55) | 0.45 (0.49) | 29.6 |
| 1 | moss mask | 1.43 (2.42) | 0.40 (0.74) | 29.7 |
| 1 | damage mask | 1.05 (1.05) | 0.34 (0.34) | 9.9 |
| 1 | outline and shadow mask | 1.62 (1.54) | 0.41 (0.37) | 52.4 |
| 2 | finished colour | 2.53 (2.81) | 0.47 (0.52) | 17.6 |
| 2 | finished height | 3.82 (4.24) | 0.71 (0.76) | 34.0 |
| 2 | colour against itself rolled by ONE base tile (must differ: new content) | 20.3 (24.3) | 13.3 (16.8) | |

(All sixteen rows are in the table file: finished roughness, the colour-and-fade mask and the slate numbers too, for one tile and for the 2 x 2 area.) The blurred differences are 18 to 95 times smaller than the controls. The one-tile picture and the 2 x 2 area both wrap exactly, and the 2 x 2 area is new content, not a copy. Nothing got worse; the moss mask became closer to exact, probably because the moss clumps are smaller and softer.

Where the raw difference comes from (corrected: the first version blamed only Cycles' 4-sample anti-aliasing). A stricter point-sampled run by the honesty check (`verify/`, 1 sample, 0.01 filter) showed that height, all four masks and the slate numbers are EXACT
(at most 0.03 % of dots differ, at isolated boundary dots) and that the colour still differs by 1 to 2 steps on about 57 % of dots: that is Blender's default 8-bit dither (noise added when the picture is saved), not the recipe. So the seamless conclusion is stronger than the raw
table shows. The point-sampled run was not repeated for the new default.

