# 06 How to start a new surface - checklist

What this is: ONE ordered checklist for a surface nobody has done yet (a tiled floor, a stone wall, leaf litter, a beach, a rusty tank), made by
merging the six "04 Lessons" files of the builds (brick, slate, wood, metal, mud, gravel). Every step says what to do, gives an example from a build
first, then the rule, and names the build that taught it in brackets, for example (gravel). The numbers are quoted from the Lessons and Recipe files
of that build and from its checker's findings (`recipes/<surface>/verifier_answer.json`); nothing here was re-run for this page.
Words are used as in [06 Cookbook - start here](06%20Cookbook%20-%20start%20here.md), section 6 (tile, dot, description, generator, element, layer,
patch, stamp, outline, grain, size classes S / M / L, same-kind score, dot-for-dot tool, tier, derivation ceiling ...).

The six Lessons files this merges (read the one closest to your surface as well):
[brick](../recipes/brick/04%20Lessons%20-%20brick%20-%20what%20carries%20over%20to%20other%20surfaces.md),
[slate](../recipes/slate/04%20Lessons%20-%20slate%20-%20what%20carries%20over%20to%20other%20surfaces.md),
[wood](../recipes/wood/04%20Lessons%20-%20wood%20-%20what%20carries%20over%20to%20other%20surfaces.md),
[metal](../recipes/metal/04%20Lessons%20-%20metal%20-%20what%20carries%20over%20to%20other%20surfaces.md),
[mud](../recipes/mud/04%20Lessons%20-%20mud%20-%20what%20carries%20over%20to%20other%20surfaces.md),
[gravel](../recipes/gravel/04%20Lessons%20-%20gravel%20-%20what%20carries%20over%20to%20other%20surfaces.md).
The shorter ten-step version is in the descriptions guide, section 9; this one is longer because it keeps every trap.

---

## The short version

**Example first (slate, the build that went furthest).** The slate builder first proved in about an hour that the reference's height is its brightness
stretched and blurred, and its normal map the slope of that height; that took two maps off the list. Then: a 16-colour palette reproduced the picture to a
colour difference of 2.3; the layout (8 rows of 6 slates, joints found as straight dark lines) went into a 2,762-byte description that already scored colour
SSIM 0.711; paint rules measured from the reference (6,597 bytes) lifted the same-kind score to 0.707; a sampler drew eight new roofs from the same
statistics (same-kind 0.722 to 0.753); and a 90-line script turned the roof into cedar shingles by changing numbers, plus one sampler option
(`recipes/slate/final_report.json`; `verifier_answer.json`).

The checklist in one breath:
1. **Ask three questions first:** layout or heap? new tiles or a copy? is there a reference with height and normal maps? (section 0)
2. **Measure before you build:** how the maps were made and the ceiling; the yardsticks; the reference's own faults; the palette; the patch counts; the
   layout lines; the element statistics; light and shadow. (section A)
3. **Build one generator:** a painter of flat shapes, back to front, photographed from above, seamless by construction, maps made from the colour. (section B)
4. **Add layers from big to small, record the ladder after each, and keep rules and tracing apart.** (section C)
5. **Check with both tools, the yardsticks, three seam tests and your eyes.** (section D)
6. **Write the sampler, bake eight new tiles, judge the family.** (section E)
7. **Bigger areas and picture sizes by tile count and tile units.** (section F)
8. **Transfer by numbers, and write down everything you had to change.** (section G)
9. **Report so that someone else can re-run it.** (section H)

---

## 0. Three questions before anything else (five minutes, by eye)

**0.1 Does the surface have a layout, or is it a heap?** Example: a slate description of 2.7 KB with only rows and joints scores colour SSIM 0.711 dot for dot,
because a few numbers per slate put every joint in place. A plain brown square scores 0.444 against the gravel reference, and the finished made-up gravel only
0.206 (0.213 when baked in Blender), because every made-up stone sits where the reference has none (gravel; `recipes/gravel/final_report.json`,
"procedural_ladder" and "classes").
Rule: with a **layout surface** (rows, a grid, planks, plates) a few kilobytes of layout buy structure and tracing the paint buys the rest; with a **heap**
(stones, leaves, crumbs) a made-up recipe can only be judged by the same-kind score and by eye, and only tracing buys dot-for-dot accuracy, at a high price.
(gravel; slate)

**0.2 Do you want NEW tiles, or a copy of THIS picture?** Example: metal's random wear made the dot-for-dot scores worse than the layout alone (SSIM 0.655 ->
0.479) but the same-kind score much better (0.20 -> 0.52); traced patches did the opposite. Rule: rules plus measured statistics make new tiles; tracing makes
a copy. Both are useful, but **never mix them in one tile**: random wear under traced patches lowers the dot-for-dot score and adds nothing to the look.
(metal; mud)

**0.3 Is there a reference with height and normal maps?** Example: golden mud had only a colour picture, so the dot-for-dot tool skipped the height and normal
limits and its traced L reached tier "close"; with stand-in maps made from its colour it would be "layout" (mud checker). Rule: without a reference there is no
score at all (every transfer was judged by eye, most also with the half-tile test); with a colour-only reference, read every tier as "colour measures
only". (mud)

**0.4 Set up the files before step A (added by the independent check of these guides; the six builds did not need it, because their surfaces were
already set up).**
* **The reference folder.** Put the pictures in `reference/<name>/` with the names listed in `reference/README.txt`: `colour.png`,
  `height_as_uploaded.png` (the 8-bit original), `height.png` (a 16-bit copy) and `normal.png` in the OpenGL convention (green up; a DirectX upload needs
  its green channel flipped first: relief guide, section 7).
* **The dot-for-dot tool works for any such folder:** `python3 -I lib/pixel_compare.py <name> OUT_FOLDER` (TESTED by the check of these guides on a copy
  of the brick folder under a new name).
* **The same-kind tool does NOT, as it stands.** It knows only the seven names in `ALL_REFERENCES` at the top of `lib/texture_compare.py`, and it reads its
  "a different surface" yardsticks for each name from `lib/texture_compare_anchors.json`; a new name stops with `KeyError` (TESTED the same way, on a copy
  of `lib/`, without changing the real one). To score a new surface the name must be added to that list and the yardsticks rebuilt
  (`python3 -I lib/texture_compare.py --anchors`). Each yardstick is a middle value over the OTHER references, so rebuilding them changes every
  surface's same-kind scores a little: re-score the old results before comparing with them (NOT TESTED).
* **The scripts to start from.** Copy the closest build's `analysis/derivation_ceiling.py` (edit its `REF = ...` line, A1) and its `generator/` folder.
  Each 04 Recipe gives its bake command, for example slate: `blender -b --disable-autoexec -t 2 --python generator/slate_generator.py -- DESCRIPTION.json
  OUT_FOLDER --size 1254`. The scoring and audit commands are cards 4 and 5 of the baking and checking guide. The part that turns a description into
  shapes (`slate_layers.py`, `mud_layers.py` ...) is written for one surface's layers: a surface with new kinds of elements needs new Python code there.
  Nobody has yet copied a generator to a new surface; every transfer reused an existing build's generator, some with a small added option (section G)
  (NOT TESTED).

---

## A. Measure before you build (plain Python, `python3 -I`; the reference picture may be used here and only here)

**A1. Prove how the maps were made, and write down the ceiling (10 minutes to an hour).**
Example: on mud, grey brightness (0.299 red + 0.587 green + 0.114 blue), stretched from 20..128 to 0..255 and blurred half a dot, reproduces the uploaded
height to 3.32 steps of 255; the slope of that height times 9 reproduces the normal map (mud). Brick needed a 12-point tone curve, blur first (3.0 against
5.0 steps the other way round) (brick); gravel needed its own mix of red, green and blue, and its fit showed that "exact" (normal 4 degrees) was impossible
from the start: even a perfect colour gives 4.6 degrees (gravel).
Rule: fit the smallest rule that turns the reference COLOUR into its HEIGHT and NORMAL. It takes two maps off your list (they follow the colour) and it gives
the ceiling: the best any recipe can reach even with a perfect colour picture. Script to copy: each build's `analysis/derivation_ceiling.py` (all six have their
reference folder written into one line, `REF = ...`, and brick's and metal's also their output folder, `OUT = ...`: edit those lines). (all six)
Traps:
* **Measure the ceiling with the SAME rule your generator will use, through the project's scorer** (`lib/pixel_compare.py`). Slate's analysis gave 2.95 steps
  with a fine 64-slot curve; the straight line the generator uses gives 3.77 (3.03 after the best fit) (slate). Wood quoted the Sobel slope (4.3 degrees;
  "Sobel" = a slope that also counts the rows above and below at half weight, slightly smoother) while its generator uses the plain slope (right
  neighbour minus left neighbour: 4.6) (wood).
* **Make normal arrows length 1 before measuring angles.** Metal's first ceiling (6.7 degrees, "exact is impossible") came from 8-bit normals of average
  length 0.9957; made length 1 it is 3.71 degrees, and the reference colour through the generator's own rule reaches tier "exact". A wrong ceiling tells you
  to stop too early (metal).

**A2. Check what the height MEANS before you build any relief.** Example: on the brick, bright = high, so the pale mortar is HIGH and the bricks LOW, the
reverse of a real wall; real raised bricks correlated -0.15 with the reference height. Rule: find out the sign before you build geometry for height; for the
next surface, check it again (for stones in sand, the stones should be high; brick's cobblestones came out with the joints higher than the stones) (brick).
Real geometry did not match any of these six references, because all six heights are painted brightness (geometry guide, section 11).

**A3. Write down the yardsticks: what "nothing" scores.** Example: on slate a completely flat normal map is off by 11.27 degrees; most slate descriptions
scored 11.7 to 12.0, slightly WORSE than flat, and still passed the "close" limit of 12 (slate). Against the mud reference the gravel reference scores 0.498 on
the same-kind tool, more than the eight new mud tiles' average (0.383) (mud; baking and checking guide, section 7.4).
Rule: before reading any score, measure for your reference: the flat normal error, the flat height error, and what the OTHER references score on the same-kind
tool. Put them next to every number you report. (slate; mud)

**A4. Look for the reference's own faults.** Example: roll the metal picture by half a tile and look at the middle: the picture jumps 2.06 times harder across
its wrap edge than elsewhere (the metal builder's own measure; the project's seam number gives 2.02), and two rivets sit on top of each other there (metal). The brick reference's 12 courses add up to about 1223 dots, leaving a
30-dot sliver course where it was stitched (brick). Rule: a generator that traces the picture copies its faults; a layout should list what is there instead of
forcing a perfect grid. All six references have a mild seam (seam number 1.69 to 2.49). (metal; brick)

**A5. Snap the colour picture to a palette and score the snapped picture.** Example: 16 colours gave slate a colour difference of 2.3 (about "just visible")
and 24 colours 2.0 (slate); 16 gave wood 3.1 (wood); 8 colours gave gravel SSIM 0.855 and 24 gave 0.923 (gravel); 16 snapped colours gave mud SSIM 0.916 but
still a normal error of 9.8 degrees (mud); 32 colours were no better than 16 for brick (brick).
Rule: if a handful of colours repeat the whole picture, it is a map of flat patches: describe the patches, do not invent shading. The snapped picture's
score is the best any flat-patch description can do. Then ask which colours belong to what: on the brick, eight reds and oranges never occur in the mortar,
and the three darkest colours are soot and outline. Those families become the colour tables of the generator. (slate, wood, gravel, mud, brick)

**A6. Count the patches by size BEFORE choosing how to describe the surface.** Example: cut the picture into same-colour areas and count them in size
classes that double each time. On slate every class covered about the same share (5, 13, 16, 21, 21, 21 %) and the 9,383 patches over 12 dots fitted into
442 KB (slate). Wood had 92,000 areas (wood). Gravel at 24 colours had 18,881 patches over 12 dots whose outlines alone took 1,182 KB (gravel).
Rule: if the outlines of the patches over 12 dots do not fit into 512 KB, tracing cannot reach "close"; plan for a made-up recipe judged by the same-kind
score and the eye, and expect the fine detail to be invented. (slate, wood, gravel)

**A7. Find the layout from the thin dark lines, not from the colours, and look at it drawn over the reference.** Example: every brick joint is two dark
outline lines about 20 dots apart; a search for PAIRS of lines found the 12 courses and their bricks (brick). On slate "dark dots that touch are the joint
network" found 4, 7, 16, then 46 slates instead of 48, because a 1 to 3 dot break in a faint joint joins two slates; fitting straight lines, accepted only
if dark along 80 % of their length, found all 48 (slate). On metal a dark-line detector and a rotate-and-count scan found the bar edges to within a dot, and
sliding a small picture of one rivet over the tile found every rivet (metal).
Rule: the dark, high-contrast lines decide most of the edge measures (slate's joints are 7 % of the dots); find them with line tools, write them as a few
numbers per element, and draw them over the reference to LOOK. (brick, slate, metal)

**A8. When the elements do not separate by colour, use one colour number and then shape; when they touch, switch to statistics.** Example: in mud, stones and
water are grey or blue and earth is orange, so one number of the Lab colour system (a way of writing a colour as lightness plus a green-to-red number
"a" and a blue-to-yellow number "b"; here "b" below 7) marked all the "things"; then size,
raggedness and blueness split them, and a "watershed" (filling each thing from its middle, drawing a border where two pools meet) split touching stones (mud).
On gravel the stones touch and share colours: finding them one by one gave 237 merged pieces for about 1,500 stones, so the build measured shares and size
curves instead (67.8 % of the dots are stone) (gravel). Rule: palette classes are not objects; test a colour axis, then shape; go to statistics early when the
pieces touch. (mud; gravel)

**A9. Measure the elements and the paint as statistics, by AREA as well as by count.** Example: on the brick, half of all patches are 36 dots or smaller,
yet half of the picture lies in patches bigger than 511 dots; a generator that fills a surface with cells needs the area-weighted table, or it makes
camouflage confetti (brick). Measure also: the tone change inside an element (slate: 20 steps of brightness from the dark top to the pale bottom of a
slate) (slate); how far the wear reaches (metal rust: you can slide the picture 9 dots across or 13 up before it stops looking like itself) (metal); the
chance of each ground colour by distance from the nearest rut (mud); the line network at the scale where it is a valley (mud ruts: fragments at 3 dots,
the broad paths at 10) (mud); and the "clouds" (soot, rust, moss): where they gather and how big the gathering is (brick). (brick, slate, metal, mud)

**A10. Measure where the light comes from and which side of a border gets darker before you draw outlines.** Example: gravel looks outlined, but the soil
gets darker toward each stone (lightness 31.4 down to 24.6 over 8 dots) while the stone's own edge does not (20.0 to 21.2): it is a shadow on the soil,
not a dark line round the stone; the light comes from the top (gravel). Rule: an outline, a shadow band and a pale lip are three different layers; measure
which one the reference has, and its width. (gravel; the painted look guide, section 4, has the outline widths of all six)

**A11. Measure the density of fine edges.** Example: the mean brightness change between neighbouring dots was 6.8 on the mud reference against 3.6 for the
first sampled ground; the same-kind tool's sharpness measure stayed near 0 until the clods were much denser and smaller (mud). Rule: the fine edges are what
the same-kind tool watches most; measure their density on the reference and match it. (mud)

---

## B. Build the generator (once per surface)

**B1. A painter of flat shapes, drawn back to front, photographed from straight above.** Example: every build turns its description into a list of flat
coloured polygons in painting order (ground, elements, paint, specks), builds them as one flat mesh with each next shape a hair higher, and photographs it
with an orthographic camera (one with no perspective, so every dot of the picture is the same size), one channel glowing at a time (all six). Rule: bricks, slates, planks, plates and stones are all "a list of flat coloured
polygons in painting order"; the Blender part needs no change per surface. Keep the height step tiny and the camera above the top shape (wood: 0.00002 for
15,000 shapes; mud: 50,000 shapes stack one tile unit high). (all six; wood; mud)

**B2. Make height and normal from the FINISHED colour, inside the generator, with the rule from A1.** Example: wood's height is the straight stretch of its
baked colour's brightness and its normal the slope of the 8-bit height, as the reference's were made (wood). Rule: do not paint height or normal separately;
the colour is the only free part. (wood; mud; all six did this)

**B3. Make the tile repeat by construction, and read the tile size from the description everywhere.** Example: brick's generator divided by a fixed 1254,
so the 2508-dot wall came out as a quarter of itself, enlarged (brick). Shapes that ran past the tile edge broke slate's half-tile test (18 % of dots
differed) until every shape's middle was folded into the tile first (slate).
Rule: fold every shape into the tile, draw it again one tile over wherever it touches an edge ("wrap copies"), let cell seeds repeat every tile, and never
write 1254 into the code. (brick, slate, wood) Also give every slow wave or noise a length that divides the tile: brick's tone dial and edge wobble did not,
so their seamlessness rests on the seam number alone; the brick builder proposes this fix, and it was NOT TESTED.

**B4. Keep a fast preview painter, and compare it with the real Blender bake once.** Example: mud's numpy preview (a quick drawing made in plain Python, without
Blender) differed from the bake by 0.75 colour levels (mud). Metal's OpenCV preview (the same idea, drawn with the OpenCV picture library) agreed with its own measurements and hid a half-dot error for hours: a measured outline runs through the CENTRES of the outer
dots, so the generator must add half a dot and grow each outline by half a dot (edge skill 0.526 -> 0.581 after the fix) (metal). Gravel's calibration
measured 67.4 % stone on the quick drawing and 61.1 % on the Blender bake of the same description (gravel). Rule: a fast preview is for looking; measure the
real bake. (mud, metal, gravel)

**B5. Fill shapes with a method you have checked.** Example: Blender's `tessellate_polygon` (the function that fills an outline with
triangles) silently mis-filled 396 of 8,687 traced outlines (one lost 44 %
of its area); metal's own "cut into horizontal slabs" fill had no misses (metal). A strict "is this outline simple" test threw away the big patches (touching
counted as crossing): SSIM fell 0.717 -> 0.702 (metal). (metal)

---

## C. The order of layers (bake and score after each one; write the ladder down)

**C1. Layout only, then one colour per element.** Example: the brick layout alone (1.7 KB) put every brick edge in place, but scored edge skill 0.174 and
same-kind 0.127; one colour per brick (still 1.7 KB) took the colour difference from 14.31 to 12.68 and the same-kind score to 0.235 (brick). Metal's plate,
bars, edge shading, rivets and seams (4,840 bytes = 4.7 KB) reached SSIM 0.655 and edge skill 0.23 (metal). A heap has no layout: mud's and gravel's flat ground scored SSIM
0.443 and 0.444 (mud, gravel). Rule: bake the cheapest description first, score it with BOTH tools, look at the difference sheet, and fix the biggest visible
wrong thing first. (brick, metal)

**C2. Edge shading and outlines, if the surface has them.** Example: brick's dark outline ("ring") raised edge skill from 0.357 to 0.421 and the same-kind score
from 0.308 to 0.406 at 62.5 KB; drawn on top of TRACED patches it made things slightly worse, because they already hold the dark lines (brick). Metal's edge
profiles walked along each bar took edge skill from 0 to 0.15 (metal). Rule: outlines are cheap and strong on a layout surface; per-element profiles when
matching one tile, shared ones for sampling (six shared metal profiles instead of twelve: edge skill 0.221 -> 0.164). (brick, metal)

**C3a. For NEW tiles: paint or wear from measured statistics.** Example: slate's upright drip stamps, scattered from measured size classes and colour families,
took the same-kind score from 0.40 to 0.71 for 3,835 more bytes (slate); metal's wear layers on seamless noise took it from 0.20 to 0.52 (metal); gravel's five
stone size classes with shadow, rim and facets reached 0.437 in 2,364 bytes, scored on its quick drawing (0.362 when baked in Blender) (gravel). The dot-for-dot scores go DOWN, as they should (slate SSIM 0.711 -> 0.569).
Traps, each met:
* **Independent random colours make confetti.** Colour a small patch as "the colour beneath it plus a small change" and cover everything first with big slowly
  changing zones (wood); use area-weighted tables (brick); remove the top-to-bottom gradient from the measured tone spread, add a slow drift, and set the
  contrast so the brightness spread matches the reference (22 steps) (slate).
* **Change brightness only, not red, green and blue separately**: separate changes turned grey stones purple and green (gravel).
* **Measure the patch size of the wear and match it before judging the look**: metal's first wear (90 x 64 noise features) made patches of 4 to 5 dots
  against 9 to 13 in the reference, a "leopard print" (metal).
* **Set noise cuts from the noise's own values**: Blender's noise is not evenly spread, so the same cut covers 5 or 30 % depending on the settings; render the
  noise, sort the values, read off the cut for the share you want (metal).
* **Count stamps by the share that stays visible**: stamps cover each other; nudge the counts per size class until the visible share matches (8 rounds on
  slate, `analysis/calibrate_rates.py`) (slate).
* **A colour layer that covers everything hides the layers below**: a fine speckle written as a colour swallowed the rust (rust share 0.156 -> 0.010); use
  Multiply for brightness-only layers (metal).

**C3b. For a COPY of this tile: tracing, with the cheapest shapes first.** Example: on the brick, a ragged ellipse (8 numbers) beat a traced outline at every
size up to about 400 KB; tracing only the biggest patches was the worst buy of all (87.7 KB: edge skill 0.146, worse than the 7.8 KB class S) (brick).
Rules, each from a build:
* **Merge, do not drop**: joining again and again the two neighbouring patches that differ least, each with its average colour, gave SSIM 0.76 against 0.53
  for "drop the small patches" at 600 KB (wood).
* **Choose patches by gain per byte** (how much each patch improves the picture for the bytes it costs), not by size: edge skill 0.58 for 300 KB
  against 0.51 for 468 KB (metal).
* **A coarser palette is better at a fixed size** (metal: at 300 KB, 8 colours SSIM 0.738 against 0.715 with 24).
* **Trace only where the layout is wrong** (metal), and **heal the reference's seam first**: fade 14 dots at each edge to the half-shifted picture and trace
  on a wrap-padded copy (the picture with a strip of its opposite edges added all round, so a patch that crosses the edge stays one patch); the tiling score went 0.30 -> 0.79 to 0.87 at no cost (metal).
* **Make the outline looseness follow the thickness of the patch**: 400 big ragged patches cost 139 KB (wood).
* **Specks become stamps** (three numbers each): about 18,000 stamps lifted edge skill from 0.114 to 0.593 for 185 KB, while outlines 2.5 times finer reached
  only 0.242 for 120 KB (gravel).
* **Spend the last bytes on a correction layer** painted last, only where the picture is still wrong. In mud's quick (numpy) tests corrections added
  +0.021 SSIM for +38.9 KB, while more ground patches bought +0.02 to +0.04 for 150 to 450 KB (mud recipe guide, section 6). In the real bakes the step
  from "L first" to "L final" (looser ground outlines plus 113 KB of corrections, +49,654 bytes in all) bought SSIM +0.009 (0.688 -> 0.698) and edge skill
  +0.041 (0.644 -> 0.685) (`recipes/mud/final_report.json`); the builder's "+0.03 SSIM for +50 KB" matches neither (mud).
* **Say plainly that it is tracing**, with corner counts: mud's L holds 76,058 polygon corners; the audit cannot see it (mud; gravel).

**C4. Grain last, as a separate switch, and say which goal it serves.** Example: brick's traced L with grain 0.14: same-kind 0.432 -> 0.598, SSIM 0.673 ->
0.537 (brick); wood's L2: same-kind 0.459 -> 0.763, SSIM 0.674 -> 0.509 (wood); slate's faint height grain made the normal map look like the reference's
(same-kind 0.707 -> 0.725) but the dot-for-dot normal error one degree worse (slate). Rule: grain off when matching dot for dot, on for new tiles; and part of
its same-kind gain is a measuring effect (brick's tiling part went 0.444 -> 1.0 with no change at the seam). (brick, wood, slate)

**C5. Stop when the ladder flattens, and expect the normal error to move last.** Example: the reference normal maps are made of 1 to 3 dot features; wood
needed a 1.5 MB trace to reach normal 12.6 (wood); even a perfect 24-colour copy of gravel gives 10.6 degrees (gravel); invented clods made mud's normal error
worse than flat (28 against 23.5) (mud). Rule: do not chase "close" with random grain (it made the normal worse on wood); the normal error falls only as more
of the reference's real detail is written down. (wood, gravel, mud)

---

## D. Check it

**D1. Score with both tools, put the yardsticks next to the numbers, and LOOK at both sheets.** Example: a wall of flat rectangles already scores SSIM 0.518
against the full trace's 0.673 (brick); a slate roof of flat colours and black joints 0.71 against 0.84 (slate): SSIM hardly notices paint. Gravel's first
stones, 1.5 times too small, scored a hair HIGHER on the same-kind tool than the final ones (0.378 against 0.362), inside the seed noise; only the picture
could choose (gravel). Rule: judge a painted tile by colour difference, edge skill, height error, the same-kind score and your eyes together; the seed alone
moves the same-kind score by 0.03 to 0.05 (wood, mud), so do not chase smaller differences. (brick, slate, gravel, wood, mud)

**D2. Test the seam three ways, on a bake with the grain switched off.** Example: brick's half-tile test passed on its area bug, because both of its bakes had
the bug; the bug was caught by comparing the first picture column with the last (correlation 0.23, against 0.9 between neighbouring columns) (brick). Metal's
half-tile difference of 3.2 was the per-dot grain, which does not slide with the shapes (0.71 with grain 0) (metal); slate's height row read 3.28 for the same
reason (slate). Wood's first area seam read 3.71 and 3.65 ("seam!") and was 0.91 and 0.89 when each jump was compared with a normal jump in the SAME direction
(wood). Rule: (a) the half-tile test proves the wrap-round drawing; (b) the first column against the last, and the wrap jump against every ordinary line, on a
grain-free bake, catch content that does not join up; (c) your eyes on a 2 x 2 repeat and a zoom of the corner where four tiles meet. (brick, metal, slate,
wood; seamless guide, section 8)

**D3. Re-bake after the last change, and check every "why" by switching the suspect off.** Example: slate's stored S0 pictures were older than its
description (1.3 steps apart) (slate); metal's sweep strips and hull plates came from before its final generator (metal); metal's builder explained a
3.2-level difference by "rounding at colour thresholds", and the checker found the grain by switching it off (metal). Rule: compare only bakes made by the same
code (a mixed comparison gave mud a false 4.5 % alarm); a guess written down is not a fact until the suspect has been switched off. (slate, metal, mud)

---

## E. New tiles: the sampler

**E1. For each layer, decide what is a NUMBER and what is a DRAW.** Example: wood's sampler keeps counts, sizes, spreads and colours as numbers measured on the
reference and draws the positions and shapes with a seed (wood); mud's draws its ruts, stones and clods from chance tables measured relative to the ruts (mud).
Rule: numbers come from the reference; draws come from the seed; every random part needs its own seed (wood's tiles first all shared one fine-grain pattern:
pair SSIM 0.57). (wood, mud)

**E2. Write the accent colours down as lists.** Example: "low saturation = chipped spot" was right for red bricks and wrong for grey stones: the first
cobblestone tile came out with black stones (brick). Rule: write which colours are soot, chips and moss in the model file; do not let the code guess. (brick)

**E3. Calibrate counts on cheap facts, weight the big sizes, and check the real bake.** Example: gravel's calibration matched the size curve on average, but
the many small sizes hid a big miss at the big end: at a disc radius of 32 dots the reference keeps 32 % stone, the final tile 7 % (gravel). Rule: calibrate
on the quick drawing, then measure the Blender picture (gravel; mud calibrated its counts on coverage facts the same way; slate its stamp counts). Giving the
big sizes their own weight in the match is the gravel builder's proposed fix: NOT TESTED.

**E4. Bake eight new tiles, look at the contact sheet, and measure how wide the family is.** Example: brick's eight tiles are as different from each other as
from the reference (25.9 against 26.9 steps), yet all have 12 courses of 4 bricks and the same palette: one narrow family (brick). Rule: measure the same-kind
score of each, how different they are from each other and from the reference, AND what they all share. (brick; slate; metal)

**E5. Score the new tiles against the OTHER references too, and do not tune on the score you report.** Example: the sampled mud tiles scored 0.35 to 0.42 on the
same-kind tool, hardly more than they score against the other references: gravel, brick, slate, metal or wood (0.25 to 0.38; the
lowest, 0.247, is against wood; `recipes/mud/verify/var_101/tx_*.json` and `var_103/texture_vs_*.json`) (mud). Wood's sampler settings were chosen by raising the
same-kind score, so its 0.626 for new tiles is optimistic (wood). Rule: keep one judge that was not used for tuning (a fresh look, another measure, the other
references). (mud, wood)

**E6. Expect two rounds of look-and-fix, and swap parts one at a time when a new tile is worse.** Example: metal fixed the rules that made ugly layouts in two
rounds (metal). A sampled slate scored worse than the fitted one; swapping only the joints, only the colours, only the shifts changed nothing; the culprit was
one setting the export had forgotten (the slow tone drift), and the score went 0.63 to 0.70 (slate). (metal, slate)

**E7. Store seeds and statistics, never shape lists.** Example: brick's first sampler wrote every cell (1.8 MB per tile) and was replaced by cell settings plus
seeds (9 KB per tile) (brick); mud's sampler still writes every clod (112,383 to 118,421 bytes per tile, 471,580 for a 2 x 2 area) (mud). Rule: the description
must not grow with the area. (brick, mud)

---

## F. Bigger areas and other picture sizes

**F1. A bigger area is a bigger tile count, never copies.** Example: slate's 2508-dot area is ONE description of 16 rows of 12 slates instead of 8 of 6; no
seam (wrap jump 0.75 and 0.58 of a normal jump) and no repeat (strongest match between quarters 0.371; a repeated tile gives 1.0) (slate). Rule: multiply
every feature count and layout count, keep colour tables and size spreads, never multiply the position (seamless guide, section 9). (slate; all six areas passed)

**F2. Measure sizes in tile units; scale the settings counted in dots.** Example: one brick description at 1254 dots and at 2508 shrunk to 1254 gives SSIM
0.994: the same picture (brick). Rule: the normal strength, the height blur and the render's pixel filter width are counted in dots and must be scaled with the
picture size (gravel's slope stayed 0.374 / 0.367 / 0.352 at 512 / 1254 / 2508); a bigger picture makes edges crisper but adds no detail (seamless guide,
section 10). (brick, gravel, metal, mud)

---

## G. Transfer: carry the generator to a surface nobody gave you

**G1. Change numbers only, and write down every number, every added line and the time.** Example: gravel to pebbles on sand changed 21 description keys
(60 values by the checker's count) plus the height stretch; no generator code changed; about 12 minutes; a 1,992-byte description baked in 48.2 s (gravel).
Rule: a new surface of the same family is new numbers; a new piece shape is one new setting (fish-scale tiles: rounded bottoms, about 12 lines); a new
arrangement (overlapping rows, round cobbles in fan-shaped courses) is new code (slate; brick). (all six)

**G2. Re-find the height stretch for every new surface.** Example: pebbles with the gravel stretch had 62 % of the height map full white (gravel); the slate
stretch left the cedar height map all white (slate). Rule: take the 1st and the 99th percentile of the new tile's own brightness (the brightness that 1 % of
the dots are darker than, and the one that 99 % are darker than) and stretch them to about 10 and 245. (gravel, slate, mud)

**G3. Re-check what the height means on the new surface** (A2). Brick's cobblestones kept the brick's bright = high, so the sandy joints came out HIGHER than
the stones, which is backwards for paving (brick checker). (brick)

**G4. Keep proof of what you changed.** Example: brick's model file gained accent lists, smudge settings and area tables by hand, so re-running its script no
longer repeats the transfer (brick); wood's generator files were edited after its deck-board script was written, so "no generator code changed" cannot be
proven from the files (wood). Rule: keep the script that writes the new model in step with the model file, and keep a copy of the generator files from before
you start. (brick, wood)

**G5. Things outside the generator's vocabulary become hand-written lists.** Example: wood's deck boards needed their butt joints and nail heads written by
hand as two lists (wood). Rule: if you write the same kind of list twice, make it a generator option so that it becomes numbers (the wood builder's
proposal; NOT TESTED). (wood)

---

## H. Report so that someone else can re-run it

* **Quote the size a test was run at, and the run a time belongs to.** Gravel's half-tile numbers were measured at 512 dots although the report said 1254, and
  its area was quoted at 173 s, a time that belonged to another bake (the area took 252.6 s) (gravel).
* **Times on a shared machine are "about".** The same brick bake took 16 s for the builder and 28 s for the checker (brick).
* **Name files by what they hold.** Wood's traced classes are called 20k ... 480k but weigh 23.8 ... 462.4 KB (wood).
* **Keep the descriptions, and say which folders lost pictures.** Only one of brick's eight new tiles kept its height and normal maps, so the checker had to
  re-bake to re-score (brick).
* **Say which unit "KB" is.** The size check counts 1024 bytes per KB; golden mud's L (513,735 bytes) passes the "512 KB" limit only because of that (mud).
* **Label every sweep strip from the description you really use, and say its base and size.** Five gravel strips said "used" for values that were not used
  (gravel); brick's strips said "(reference)" where they meant "default" and had no gaps between squares, so the joins looked like cracks (brick); slate's
  filter-width strip at 384 dots blurs about 3.3 times more of the tile than the same setting at 1254 (slate).
* **Never stop processes by name on a shared machine.** One broad stop by script name may have stopped other builders' jobs of the same name (gravel); a
  search for words that are also in your own command finds, and stops, your own window (brick, mud); wood met the same trap when waiting for a job by its name.
* **A lesson in a builder's notes is not proven until the final tile uses it.** Gravel's notes say "draw big soil lumps first, small on top"; its final tile
  draws them the other way round, and no score compares the two (gravel).
* **Report traced descriptions as tracing, whatever the audit says,** with corner or number counts (mud: 76,058 corners; gravel: 138,857 numbers, lists kept
  just under the audit's 4,000-number limit) (mud, gravel).

---

## What was tested for this page, and what was not

This page is an editor's merge of the six Lessons files, their Recipe files and the checkers' findings. Every number is quoted from the build named in
brackets; nothing was re-run for this page, and the links on it were checked by `checks/overview/check_links.py`. The independent check of these guides
([06 Check - what was checked and fixed](06%20Check%20-%20what%20was%20checked%20and%20fixed.md)) added step 0.4 (its tool test ran on a
throw-away copy of `lib/` and of one reference), corrected numbers in C1, C3b and E5 and the script note in A1, and explained words in A1, A8, B1, B4,
B5, C3b and G2.

Which steps all six builds followed: A1, B1, B2, C1 (or its heap version), D1, E4, F1, G1 (G1 only in part: slate and metal did not write
down their working time; metal counted 6 tool calls, slate gave only bake times). Which were learned on one build only and never tried on another
(so they are one build's experience, not rules proven on several surfaces): A8 (mud's colour-axis finder), A10 (gravel's shadow measure), B5 (metal's slab
fill), and in C3b the gain per byte and the healed seam (metal) and the correction layer (mud). Three fixes are only proposals, marked NOT TESTED where they
appear: wave lengths that divide the tile (B3), extra weight for big sizes in the calibration (E3), and a generator option for hand-written lists (G5).

NOT TESTED: the whole checklist on a surface none of the six builds made. The transfers (cobblestones, cedar shingles, fish-scale tiles, deck boards, hull
plates, snow, pebbles) are the nearest test, and each of them was judged by eye only, because no reference exists for them.
