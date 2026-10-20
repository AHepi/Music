# The half-tile shift test of the finished maps and of every layer's mask, 512 dots, run again on 20 October after the look fixes (new default settings)

What this is (plain words): the recipe is baked, then baked again with the whole pattern slid by half a picture; if it repeats exactly at the tile edge, the second picture is the first one rolled by half its size.
"mean difference" is in steps of 255 (masks: of 100), the "blurred" columns first blur both pictures by 2 dots to remove the one-dot jitter of hard edges, and the "control" is the same comparison with the picture rolled 7 dots too far (it must differ a lot).
Made by `tests/half_tile_layers.py 512` (eight Blender runs). The baked pictures (about 9 MB) were deleted afterwards to save disk, so running the script again bakes them again. The old table is `half_tile_table_before_look_fixes.md`.

| tiles_across | what | mean difference (of 255) | share of dots over 10 steps % | blurred 2 dots: mean difference | blurred 2 dots: share over 10 steps % | control (rolled 7 dots wrong, blurred): mean | control: share % |
|---|---|---|---|---|---|---|---|
| 1 | finished colour | 1.645 | 1.429 | 0.31 | 0.0 | 15.01 | 54.32 |
| 1 | finished height | 2.191 | 5.081 | 0.454 | 0.0 | 29.61 | 71.35 |
| 1 | finished roughness | 1.341 | 0.892 | 0.257 | 0.0 | 10.33 | 40.16 |
| 1 | colour and fade mask | 4.041 | 19.572 | 0.982 | 0.0 | 37.64 | 79.41 |
| 1 | damage mask | 1.054 | 2.179 | 0.343 | 0.095 | 9.94 | 17.77 |
| 1 | moss mask | 1.433 | 3.998 | 0.399 | 0.002 | 29.67 | 37.86 |
| 1 | outline and shadow mask | 1.616 | 6.388 | 0.408 | 0.0 | 52.36 | 58.97 |
| 1 | piece id | 0.199 | 0.718 | 0.089 | 0.0 | 12.75 | 24.51 |
| 2 | finished colour | 2.532 | 3.532 | 0.472 | 0.0 | 17.61 | 67.88 |
| 2 | finished height | 3.82 | 10.276 | 0.71 | 0.0 | 33.99 | 80.84 |
| 2 | finished roughness | 2.106 | 2.483 | 0.383 | 0.0 | 11.96 | 49.63 |
| 2 | colour and fade mask | 7.038 | 32.076 | 1.404 | 0.01 | 35.58 | 80.16 |
| 2 | damage mask | 2.091 | 3.81 | 0.688 | 0.275 | 12.65 | 28.38 |
| 2 | moss mask | 2.746 | 7.524 | 0.755 | 0.026 | 37.5 | 52.56 |
| 2 | outline and shadow mask | 3.05 | 11.61 | 0.74 | 0.001 | 69.83 | 78.11 |
| 2 | piece id | 0.498 | 1.566 | 0.209 | 0.001 | 27.66 | 46.4 |
| 2 | colour against ITSELF rolled by one base tile (must differ a lot: new content) | 20.299 | 69.76 | 13.331 | 57.73 |  |  |
