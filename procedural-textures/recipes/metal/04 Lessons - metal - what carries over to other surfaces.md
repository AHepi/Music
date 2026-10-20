# 04 Lessons - metal - what carries over to other surfaces

What this is: what I learned while making the metal tile that should help with a surface nobody has given us yet (a ship's hull, brick paving, a painted door, a rusty tank).
Everything here was measured in this folder; the numbers come from `recipes/metal/` (see `04 Recipe - metal - how it is made.md` for the details and the pictures).
Same words as in the recipe: dot, bar, patch, description, generator, layer, tier. The measures (SSIM, Delta E, edge skill, height error, normal angle, "same kind" score) are explained in plain words at the top of the recipe guide. An independent checker re-ran this work; the last section lists what it confirmed and what was corrected.

---

## 1. How to start a new surface (the checklist, in order)

1. **Find the ceiling first.** Fit the small rule (grey -> blur -> tone curve, i.e. a table of which grey becomes which height; slope with a whole-number strength) that turns the reference COLOUR into its height and normal. Write down the error it leaves: for metal 4.93 height levels and 3.71 degrees of normal angle. That error is the best any colour picture can do through derived maps, and it tells you which tier is reachable (metal: even "exact", whose limits are 6 levels and 4 degrees). **Measure it with the project's own scorer (`lib/pixel_compare.py`), feeding the reference colour through your generator's own rule.** My first ceiling (6.7 degrees, "never exact") was wrong: my script compared with the reference's normal arrows as stored in the 8-bit picture without making them length 1 first (their length is 0.9957 on average), which alone adds about 5 degrees. The independent checker found it by running the reference colour through `generator/derive_maps.py` and scoring it: tier "exact" (`verify/ceiling/pixel.json`). A wrong ceiling tells you to stop too early.
2. **Look for the reference's own faults.** Roll the picture by half a tile and look at the seam in the middle. Metal has a mild seam (the picture jumps 2.06 times harder across the wrap edge) and two rivets sit on top of each other there. A generator that traces the picture copies the fault.
3. **Sort what you see into three kinds:** (a) things placed by a rule or a number (bars, rivets, seam lines: layout), (b) shading that repeats along every edge (edge profiles), (c) a fine random mottle (wear). In metal the layout (bar faces 30 per cent, bar edge strips 22 per cent, rivets 6.5 per cent of the tile; the bare plate 42 per cent) is 58 per cent of the area, but most of the strong edges that the comparison counts are in (c): the layout alone reaches edge skill 0.23.
4. **Measure the layout by numbers, not by eye.** Dark-line detector + a rotate-and-count scan found bar edges to within a dot; template matching found every rivet; the middle (median) colour across an edge, walked along the whole bar and using only the less rusty half of the samples, gave clean edge profiles. One script each: 6 bars, 33 rivets, 3 seams.
5. **Describe the layout and look at the first picture early** (a fast OpenCV preview, then the real Blender bake). If the structure is wrong, nothing else matters. The first layout picture (5 KB) already had SSIM 0.65.
6. **Measure the wear's statistics:** shares of each colour class, how far a patch reaches across and up (the "autocorrelation length": how far you can slide the picture before it stops looking like itself; metal rust 9 dots across, 13 up), how uneven it is between windows. Put them in a table next to the generated picture's (`analysis/wear_stats.py`) and tune until the rows match. Do not tune by looking only at the score (the score is noisy; see the traps).
7. **Pick the wear strategy for the job:** statistics for NEW tiles (procedural noise layers with calibrated thresholds), tracing for THIS tile (patches). They are different layers with different jobs: never mix them in one tile (random wear underneath traced patches lowers the dot-for-dot score and adds nothing to the look).
8. **Make the tracing cost-aware** (section 3): choose patches by "gain per byte" (how much each patch improves the picture for the bytes it costs), not by size. Metal: 0.58 edge skill for 300 KB this way, against 0.51 for 468 KB by size.
9. **Test seamlessness properly:** bake shifted by half a tile and compare with the first bake rolled by half a tile; then look at a 2 x 2 tiling. If the difference is bigger than the edge smoothing explains (metal S: 3.2 levels against 0.4 to 0.6 for the shape-only classes), switch off the part you suspect and test again: the grain was the cause (0.71 with grain 0), not the reason I first guessed.
10. **Write the random description generator** (`sample_description.py`) from ranges measured on the reference, bake 8 tiles, look at the contact sheet and measure how different they are from the reference and from each other. Fix the rules that make ugly layouts (it took two rounds here).
11. **Transfer test on a surface you were not given** by changing only the description (section 6), and re-bake the transfer picture after every later generator fix (the stored hull picture predates the grain fix).

---

## 2. What each layer buys (accuracy against description size, metal)

Real Blender bakes, 1254 dots, 8 samples, dot-for-dot against the reference (`scores/*_pixel.json`, `final_report.json`). "Edge skill" = share of strong edges placed within 2 dots (0 = luck, 1 = all). Normal angle in degrees. Sizes in KB of 1000 bytes, rounded; the 16, 32, 64, 128 and 256 KB rows are named after the size they were cut to (their files are 16,091 to 261,188 bytes), and the size check counts 1024 bytes per KB (L, 413,452 bytes, is 404 KB in its units; exact bytes in `cookbook/06 Guide - descriptions - analyse, describe, generate, compare.md`, section 3.2).

| Layer added | Description size | Tier | SSIM | Delta E | Edge skill | Height error | Normal angle | Same-kind score |
|---|---|---|---|---|---|---|---|---|
| plate + bar faces (flat) | 3.6 KB | none | 0.613 | 9.75 | 0.00 | 32.3 | 13.3 | 0.16 |
| + edge shading (profiles) | 4.1 KB | none | 0.649 | 8.88 | 0.15 | 28.1 | 12.8 | 0.17 |
| + rivets + seam lines (= S0, the layout) | 4.8 KB | none | 0.655 | 8.60 | 0.23 | 26.8 | 12.7 | 0.20 |
| layout + 88 traced patches | 16 KB | none (edge 0.297, just under 0.30) | 0.666 | 7.75 | 0.30 | 25.1 | 12.6 | 0.23 |
| layout + 275 patches | 32 KB | layout | 0.675 | 7.12 | 0.35 | 24.0 | 12.4 | 0.25 |
| M: layout + 841 patches | 64 KB | layout | 0.692 | 6.44 | 0.42 | 22.3 | 12.1 | 0.30 |
| layout + 2273 patches | 128 KB | layout | 0.713 | 5.77 | 0.48 | 20.3 | 11.6 | 0.35 |
| layout + 5392 patches | 256 KB | **close** | 0.740 | 5.14 | 0.55 | 17.9 | 11.0 | 0.44 |
| L: layout + 9155 patches | 413 KB | **close** | 0.756 | 4.90 | 0.58 | 16.6 | 10.6 | 0.50 |
| S: layout + procedural wear (not traced) | 6.3 KB | none | 0.479 | 12.18 | 0.15 | 31.5 | 16.1 | **0.52** |

How to read it:
* Layout is the cheapest accuracy: 5 KB buys most of the structure (flat bar faces to rivets: SSIM 0.61 to 0.66, edge skill 0 to 0.23).
* Each doubling of traced bytes buys about +0.01 to +0.03 SSIM and about +0.05 to +0.07 edge skill; it never saturates below the 512 KB limit. The tracing is **not** a description: it is a coded copy of this tile's rust.
* Procedural wear does the opposite of tracing: dot-for-dot scores get WORSE than layout alone (SSIM 0.655 -> 0.479, because random rust sits in the wrong places) but "same kind of surface" gets much better (0.20 -> 0.52). The two measures want different layers. That is the point of having two comparison tools.
* The height and normal errors follow the colour error closely (they are derived from it). The floor is 4.93 levels and 3.71 degrees (corrected from 5.0 and 6.7). So for L (16.6 levels, 10.6 degrees) the gap to "exact" is the COLOUR, not the rule that makes the maps.

---

## 3. Lessons about tracing a picture into patches (general, any painted surface)

(The comparisons in this section were made with the fast OpenCV preview, before the half-dot fix of section 4, and with a 300 KB budget; I did not repeat every comparison with real Blender bakes; the real bakes of the budget series in section 2 rise in the same order, with absolute numbers 0.01 to 0.05 lower than the preview's.)

* **Rank by gain per byte.** I first kept every patch above an area limit: 6280 patches / 468 KB gave edge skill 0.51. Ranking every candidate by (colour error removed, with dots near strong edges counted three times) / (bytes it costs) and keeping the best until the budget is used gave edge skill 0.58 with 6843 patches / 300 KB.
* **A coarser palette is better at a fixed size.** Same budget (300 KB): 8 colours: SSIM 0.738 / edge 0.578; 12 colours: 0.732 / 0.575; 16 colours: 0.729 / 0.579; 24 colours: 0.715 / 0.514. More colours cut every area into more, smaller patches that do not pay for themselves.
* **Only trace the difference from the layout.** A patch is made only where the reference's palette colour differs from what the layout already paints. The layout shows through everywhere else, so edges, rivets and shading are not stored twice.
* **Trace on a healed copy when the reference has a seam.** Fade 14 dots at each edge to the half-tile-shifted picture, then trace on a copy padded by wrap-around so a patch that crosses the edge is one patch. Cost: SSIM 0.680 -> 0.679 (nothing); gain: the tiling score 0.30 -> 0.79 to 0.87.
* **Outlines through dot centres need growing by half a dot** (next section).

---

## 4. Traps (each one cost me time; each applies to any surface built from shapes)

1. **The half-dot trap.** A measured outline runs through the CENTRES of the outer dots. A renderer that fills exact areas fills only half of each outer dot, and "dot i" is the span i to i+1, not the number i. Both mistakes together shifted and eroded every traced patch: edge skill 0.526 instead of 0.581, SSIM 0.716 instead of 0.759. Fix: description coordinates are dot numbers; the generator adds 0.5 and grows each outline by 0.5. A fast OpenCV preview that draws "boundary dots included" hid the problem for hours because it agreed with the measurement. **Always compare the preview with the real render once** (mean difference 2.6 colour levels was the warning).
2. **Blender's `tessellate_polygon` silently mis-fills hard outlines** (396 of 8687 traced outlines, the biggest ones; one lost 44 per cent of its area). My own slab method (cut into horizontal slabs, pair the edges left to right) fills every outline that does not cross itself, including ones that touch themselves at a corner.
3. **A strict "is this outline simple" test threw away the big patches** (touching counted as crossing): SSIM fell 0.717 -> 0.702. Only proper crossings need to be refused.
4. **Averaging edge profiles over similar bars loses the sharp lines.** Six shared profiles instead of twelve per-bar ones: edge skill 0.221 -> 0.164. Use per-bar profiles when matching one tile; shared ones for sampling.
5. **A "cover everything" ramp hides earlier layers.** A fine speckle layer written as a colour layer swallowed the rust (rust share 0.156 -> 0.010). Brightness-only layers must use Multiply (128 = no change).
6. **Texture scores are noisy and can be gamed by fine grain.** Adding a large-scale tone layer and turning grain down made "same kind" 0.516 -> 0.454 -> 0.410 even though the pictures looked fine: the spectrum measure is normalised by total energy, so a change at one size moves every other size. I went back to the best setting. Look at the spectrum difference per size (`analysis/spectrum_diff.py`) before changing a layer.
7. **The first procedural wear was far too fine** (90 x 64 noise features across the tile: patches 4 to 5 dots wide against 9 to 13 in the reference, a "leopard print"). Measure patch size and match it before judging the look.
8. **Calibrate noise thresholds from the noise itself.** Blender's noise values are not evenly spread; the same threshold covers 5 or 30 per cent depending on the settings. Render the noise value, sort the values and read off the value below which the wanted share lies ("quantiles"), and set the thresholds from the shares you want.
9. **Time:** each noise layer costs render time. 5 layers + grain: colour render 20 to 60 seconds at 1254 dots (the layout and traced patches alone: 4 to 12 seconds).
10. **Check every "why" by switching the suspect off.** I explained the 3.2-level half-tile difference of S by rounding at colour thresholds; the checker set the grain to 0 and the difference fell to 0.71, so the grain was the cause. I also wrote that the variation tiles mixed grain versions (they did not: all were baked after the fix) and that the long scratches were not reproduced (the upper-right one is partly there in L). Each was a guess written down as a fact.

---

## 5. What is specific to metal and what is general

| General (use it on any surface) | Specific to this metal |
|---|---|
| derivation ceiling first; look at the reference's seam | straps, braces and rivets as bars with edge profiles |
| layout as numbers, rotate-and-count scan, template matching (sliding a picture of one object over the tile) for repeated objects | the lit upper-left / shaded lower-right edge profiles |
| wear = steps of a colour ramp on seamless stretched noise, thresholds calibrated from the noise values (quantiles) | rust gathering at edges and under rivets (edge attraction number) |
| stack of flat shapes photographed from above; slab fill; half-dot rule | 8-facet rivet dome picture (rings x slices) |
| tracing by gain per byte on a coarse palette, healed seam | the vertical stretch (1.45 x) of the rust |
| sampler = ranges measured on the reference + rules that stop ugly layouts | brace only in roomy near-square panels |
| two comparison tools because they want different things | geometry route does not match this reference's height |

---

## 6. The transfer test (hull plates, no code changed)

Surface not given: painted ship's hull plates (rows of overlapping steel plates, vertical joints that change place from row to row, small close rivets on every edge, rust streaks running down from the rivets).
* Changed: ONLY the description, written by `transfer/make_hull_plates.py` (43 lines): 6 wide horizontal bars instead of straps; 3 thin joint bars per row, shifted by half a plate every second row; two rows of small rivets along each plate (the same rivet picture, radius 7.5 instead of 19.5); the same six shared edge profiles; new plate colours (blue-green paint); the same three wear layers with new colours, long vertical streaks (130 x 14 noise features instead of 44 x 30), rust share about 12 per cent instead of 18, rust attracted harder to rivets.
* Changed in the generator: nothing for the transfer. Thresholds were set by the same calibration script (1 call). The stored hull picture was baked before the generator's grain fix (20:57 against 21:08); re-baked with today's generator it differs by 2.94 levels on average, 0 per cent of dots by more than 40. The checker ran the half-tile test on it (the builder had not): 2.52 levels, 0 per cent over 40: seamless.
* Time: about 6 tool calls from "what is a hull plate" to the picture (the description script took 1 call, calibration 20 seconds, the bake 80 seconds at 1254 dots with 19 074 shapes and all maps). Picture: `guide_pictures/transfer_hull_plates.png`.
* Judged by eye only (there is no reference for it, so no score). What looks right: the stepped plate rows with shadow under each lap, the rivet rows, the joints, rust streaks from the rivets. What looks wrong: the paint tone noise is wavy (30 x 8 features: too smooth), the rust is too sparse, rivets look too brown near the laps.

---

## 7. If I had one more day

1. Add the two long scratches (thin light lines) and the reference's drip streaks to the procedural wear (the one thing the variation tiles clearly lack: long vertical drips under rivets and edges). The traced L class already has the upper-right scratch as broken pieces; S0, S, M and the sampled tiles have neither.
2. Fit the strap edge profile in the description as a small formula (shadow length, crease depth, line brightness) instead of tables, so sampled tiles get per-bar variety.
3. Re-test hard (1 sample) against smooth (8 samples) edges after the half-dot fix: the earlier test was made before the fix.
4. A second pass of patch selection after the first set is painted (the gains change once big patches are down).
5. Ask for in `lib/`: a `pixel_compare` option to ignore a band of N dots at the picture edge (the reference's seam makes the border rows unfair), and a texture_compare measure that is not normalised by total energy.

---

## 8. Checked independently

An independent checker re-ran the metal work from the files (`verifier_answer.json`; its bakes and scores are in `verify/`).
* Confirmed: every number in the table of section 2, from fresh Blender bakes of S0, S, M and L scored with both tools.
* Confirmed: the generator never reads the reference; every claimed description passes the size check; the variations and the area are new pictures, re-made identically.
* Confirmed: the height ceiling of about 5 levels; the half-tile tests pass (L 0.56, S-type tile 3.2, hull plates 2.52 levels; 0 per cent over 40).
* Corrected: the normal ceiling is 3.71 degrees, not 6.7, and tier "exact" IS reachable through derived maps; only the colour keeps L from it (step 1, section 2).
* Corrected: the cause of the 3.2-level half-tile difference is the per-dot grain (trap 10, step 9).
* Corrected: the variation tiles were all baked after the grain fix; the upper-right scratch is partly present in L (trap 10, section 7).
* Corrected: the tracing in M and L is a traced copy of this tile's rust (the recipe's first section now says so too).
* Corrected: the hull picture predates the grain fix; it is still seamless (section 6).
* Plain words added for autocorrelation length, gain per byte, quantiles and template matching.
