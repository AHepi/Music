# 04 Lessons - slate - what carries over to other surfaces

This file is for the day you start a surface nobody gave you (a tile floor, a stone wall, a field of leaves). It says what the slate work taught,
in the order you would use it. The numbers quoted are the slate's; the lesson is the same for other surfaces. Words used: the **tile** is the
1254 x 1254 picture; the **description** is the small file the generator is driven by; a **patch** is an area of one flat colour in a picture;
a **stamp** is a patch the generator makes up; the **joint** is the dark line between two pieces; a **dot** is one picture dot (pixel);
a **piece** is one slate, shingle or scale; **KB** is 1024 bytes (the unit of the project's size check). The measures (SSIM, colour difference, edge skill,
height error, normal error, tiers, "same kind" score) are explained in plain words in section 0 of the recipe guide, under "How to read the columns".

## How to start a new surface (the checklist, in order)

1. **Prove how the maps were made, before anything else (10 minutes, plain Python).**
   Fit three small things that turn the reference COLOUR into the reference HEIGHT and NORMAL: which brightness recipe, a straight stretch with
   cut-offs, a blur. For the slate: height = 2.5 x (brightness - 9.5), cut off at 0 and 255, blur 0.5 dots; normal = slope of the 8-bit height, strength 7.
   Measure the ceiling with the SAME rule your generator will use and with the project's own scorer (`lib/pixel_compare.py`): on the slate the analysis script's
   2.95 steps came from a finer 64-slot lookup curve; the straight line actually used gives 3.77 steps (3.03 after the best brightness-and-contrast fix).
   This takes the height and the normal off your list: they become automatic once the colour is right. It also gives you the ceiling: the best
   height error (about 3 steps of 255) and normal error (about 2.8 degrees) any recipe could reach even with a perfect colour picture.
   (Script: `analysis/derivation_ceiling.py`.) Try this first on every surface: it cost one hour on slate and saved days.
2. **Snap the colour picture to a palette and look at it.** 16 colours gave a mean colour difference of 2.3 (about "just visible"), 24 gave 2.0. If a
   handful of colours repeat the whole picture, the picture is a map of flat patches and your job is to describe the patches, not to invent shading.
3. **Find the layout first: it is where the dark, high-contrast lines are.** Black joints are 7 % of the slate dots yet they decide most of the edge
   measures. Find the rows, the pieces in each row, the joint widths and leans, the edge raggedness; write them as a few numbers per piece.
4. **Measure the patches by size class.** Cut the picture into same-colour areas and count them in size classes that double each time. On the slate
   every class covered about the same share of the area (5, 13, 16, 21, 21, 21 %): the paint is "the same at every scale". Also measure: how tall
   versus wide the patches are, which colour families they use, and how tone changes from the top of a piece to the bottom (on slate: a dark
   shadow band at the top, a pale lip at the bottom: 20 steps of brightness from top to bottom).
5. **Build the generator as a painter that draws flat shapes back to front** (see the recipe): first the dark ground, then the pieces, then the paint.
   Everything a surface needs (bricks, plates, planks, stones) is "a list of flat coloured polygons in painting order".
6. **Compare with BOTH tools and look at the sheets.** One tool says "is it the same picture dot for dot", the other "is it the same kind of
   surface". They disagree on purpose: see the traps below.
7. **Climb the ladder one layer at a time and write down the size of each step** (layout, + paint statistics, + traced big patches, + traced fine
   patches). The curve of accuracy against description size is the most useful result you will have.
8. **Only then make the sampler** (new tiles from the measured spreads), check each new tile with the "same kind" score, and measure how different the
   tiles are from each other and from the reference.
9. **Test a new surface by changing numbers only** (palette, counts, sizes, family lists). If you must change code, write down exactly what and how long it took.
   On the slate work: cedar shingles needed numbers only in the Blender generator (a short script, a bake of 25 s), but they did use a new sampler option
   (`fitted=`, to read another set of numbers) and the preview painter's height stretch; fish-scale pieces needed one new setting (round lower corners, 12 lines).
   One number must be re-found for every new surface: the **height stretch**. With no reference height, stretch the 1st to the 99th percentile of the picture's own brightness
   (on the slate this gives 9 and 114, the fitted values are 9.5 and 111.5; skipping it left the cedar height map all white).

## What each layer buys (slate numbers; 1254 dots; "close" = the pixel tier the project calls close)

| layer added | description size | what it fixed | what it did NOT fix |
|---|---|---|---|
| layout only (rows, joints, ragged outlines, one flat colour per slate) | 2.7 KB | all the structure: the picture reads as a roof; colour SSIM 0.71 | any paint; height error 35 steps; edges 0.29 |
| + paint stamps from measured statistics | 6.4 KB | looks like the right surface: "same kind" score 0.40 to 0.71 | dot-for-dot match (it is invented paint: SSIM 0.569, lower than layout only) |
| + a faint seamless grain (optional) | 6.5 KB | the normal map looks like the reference's: "same kind" normal score 0.51 to 0.57, overall 0.707 to 0.725 | dot-for-dot: normal error 1 degree worse (random grain is not the reference's) |
| traced outlines + biggest patches (16 colours) | 60 KB | tone of every slate and big streak in the right place: colour difference 8.1 to 5.7, height error 35 to 23 | the edge measure (0.44) and anything under about 500 dots |
| + patches over 100 dots | 147 KB | edge measure 0.54, colour difference 4.0, height error 16 (one hair under the "close" edge limit 0.55) | fine edges |
| + medium patches | 264 KB | tier "close": edges 0.67, height error 12 | faint grain, 1-dot edge placement; the normal map (11.0 degrees, hardly better than a flat one at 11.3) |
| + fine patches | 442 KB | colour difference 2.85, edges 0.74, normal 9.7 degrees | tier "exact" (needs colour SSIM 0.92; we get 0.84) |

Short version: **layout buys structure, statistics buy the look, tracing buys the match.** The jump in dot-for-dot accuracy only comes from
describing the actual patches; the jump in "looks right" comes much earlier and costs a hundredth of the bytes.

## Traps (things that cost time here and will cost time on the next surface)

* **The picture-structure measure (SSIM) hardly notices paint.** A slate roof with flat colours and black joints already scores 0.71; the fully traced one
  0.84. The black joints decide it. Do not use SSIM alone to judge a painted texture; use colour difference, the edge measure, the height error and the
  "same kind" score together, and look.
* **Know which reference height each comparison tool reads.** The dot-for-dot tool compares with the 8-bit upload. This guide first said the "same kind" tool
  compares with a copy smoothed 0.8 dots; that was true of the tool before it was changed at 15:45 on 19 October, and today it reads the 8-bit upload too
  (read in `lib/texture_compare.py`; `cookbook/06 Guide - baking and checking maps.md`, section 5). The slate's "smoothed-height view" scores
  (`analysis/score_folder.py`) are still real numbers (S2: 0.725 as baked, 0.724 smoothed), but smoothing is no longer the way to match the tool: on a correct
  height it lowers the score (0.992 -> 0.830 in the baking guide's test). Score the height as baked, and say so.
* **A thin joint breaks "find the pieces by connected areas".** A 2-dot break in a black line joined slates into 4, then 16, then 46 areas instead of 48.
  Fix: find long thin dark lines with a tall thin kernel, fit a straight line through each, accept a line only if it is dark along 80 % of its length.
* **Coordinates must be folded into the tile before sliding or copying.** Layouts that run past the tile edge broke the half-tile test (18 % of dots
  differed) until every shape's middle was brought into the tile first. Draw each shape again shifted by plus and minus one tile wherever it touches an edge.
* **Counting stamps one by one over-covers the surface**, because stamps are drawn on top of each other. Draw them with a different number per size class,
  measure the share that stays visible, and nudge the counts until it matches the reference (`analysis/calibrate_rates.py`, 8 rounds).
* **Independent random tones make confetti.** The measured spread of patch tones includes the top-to-bottom gradient; remove it before using the spread, add a slow
  smooth drift on top, and set the overall contrast so the standard deviation of brightness matches the reference (22 steps).
* **When a sampled tile scores worse than the fitted one, swap the parts one at a time.** Swapping only the joints, only the colours, only the shifts changed
  nothing; the culprit was one missing setting (the smooth tone drift) that the export had forgotten. Score went 0.63 to 0.70.
* **Blender's Gaussian pixel filter is not the blur you think.** Filter width 2 blurs like a 0.5-dot Gaussian; 4 like 0.9; 6 like 1.4 (not width / 12).
  Measure it once (`generator/test_filter_width.py`). The width is counted in picture dots, so a sweep strip baked at 384 dots blurs about 3.3 times more of the
  tile than the same width at 1254 dots: bake the strip at the real size if it is meant to show softness.
* **Row-by-row separation (a pile of "same-looking" pieces) is where the generator is NOT general:** overlapping pieces (fish-scale pieces, shingles with a visible lap) need an overlap option; mine draws a black gap
  where a real roof shows the next row's piece.
* **Put the "do nothing" yardstick next to every number.** On the slate a completely flat normal map is off by 11.3 degrees; most descriptions scored 11.7 to 12.0,
  slightly WORSE than flat, and still passed the "close" limit of 12. Without the yardstick in the table nobody would notice.
* **Re-bake and re-score after the last change to a description, and say which sampler version made each file.** The independent checker found the stored S0
  pictures older than the S0 description, and the area and sample_1 to 4 descriptions made by an earlier sampler (no grain). The numbers still held, but only a re-bake proved it.
* **A test that slides the tile is not fair to anything that stays fixed in place.** With the grain on, the half-tile test's height part differed by 3.28 steps (the grain does
  not slide with the shapes); the colour part is the one to trust.
* **The project's description audit has a false alarm:** a list of patches whose first five entries are long looks "like an image". Write each patch as
  `[colour, [numbers]]` (a short row) and it passes. (Suggested change in lib: ask for rows of EQUAL length before calling it a grid.)

## What is specific to the slate, and what is general

General (reuse as it is): the derivation proof; the palette idea; polygons drawn back to front in Blender (flat meshes under an overhead camera);
wrap copies; Cycles pixel filter as a blur; maps made from the colour picture inside the recipe; the audit; the ladder; the sampler idea (draw new
numbers from the measured spreads); the calibration of stamp counts and contrast; the two comparison tools used together.

Slate only: rows of 6 pieces of log-normal width; joints 4 dots wide; the shadow band at the top and pale lip at the bottom; upright "drip" stamps; moss
and lichen shares per slate. To change surface you change THESE numbers, not the code (see the transfer test: cedar shingles needed only a new palette,
counts, sizes and family lists, plus the sampler's `fitted=` option and a new height stretch).

## What I would do next (honest)

* Describe the faint grain (75 % of neighbouring dots differ by half a step) with a seamless fine noise: probably what separates "close" from "exact".
* Tried and not worth it: stamping a library of 32 REAL patch outlines instead of made-up upright drips ("same kind" 0.692 against 0.707, 2.7 KB more). What would help instead: long-range tone differences between neighbouring slates.
* Edge raggedness from real chipped outlines (the layout makes random ones: the layout-only picture scores 0.29 on edges because its ragged edges are not where the
  real ones are).
* Replace my numpy outline maker by a Geometry Nodes one (Fillet Curve, Resample Curve, Set Position with noise, Fill Curve) so the whole layout lives in Blender nodes.

## Checked independently

An independent checker re-ran the slate work from the files (`verifier_answer.json`; its pictures and scores are in `verify/`).
* Confirmed: every re-baked picture identical to the builder's; every class's tier and scores in the table above; the generator never opens the reference; every claimed size class passes the size check.
* Confirmed: the derivation ceiling of about 3 steps and 2.8 degrees (straight-line rule: 3.03 steps after best fit, 2.71 degrees; `verify/scores/ceiling_pixel.json`).
* Confirmed: the eight sampled tiles are new and different (mean "same kind" 0.735), but they look clearly weaker than the reference (blocky "camouflage", little pale chipping or moss).
* Corrected: layout + stamps scores colour SSIM 0.569, not 0.60.
* Corrected: sizes in KB of 1024 bytes: grain step 6.5 KB (not 6.6), traced coarse 60 KB (not 61).
* Corrected: the 2.95-step ceiling was for a 64-slot lookup curve, not the straight line (step 1 of the checklist).
* Corrected: cedar shingles were "numbers only" for the Blender generator, not for the whole pipeline (sampler `fitted=` option, preview painter's height stretch).
* Corrected: side edge raggedness is 2.06 dots, not 1.6 (in the recipe guide).
* Added: the flat-normal yardstick, the stale-file trap and the half-tile grain trap (Traps above).
