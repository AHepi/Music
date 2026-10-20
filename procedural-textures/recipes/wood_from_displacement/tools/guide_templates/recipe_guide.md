# 08 Recipe - wood from your displacement and colour maps - how it is made

**What this file is:** the full guide to the wood-from-maps recipe, written for a person who is not a programmer. It says what the recipe does with the uploaded wood maps, what every setting does, what the pictures and the measurements showed (including what failed), and what I did not test. The companion file `08 Lessons - wood from your displacement and colour maps - what carries over to other surfaces.md` says what carries over to other surfaces. The research that came first is in `research/08 Research - making big non-repeating surfaces from one map.md`.

**Words used the same way everywhere.** A **dot** is one pixel. The **source map** is an uploaded picture (the displacement map, which is a grey height picture where brighter means higher, or the colour map) used as raw material; it is 1254 x 1254 dots. A **tile** is the default square of 1254 x 1254 dots that repeats without a seam. An **area** is a bigger picture of new content (2 x 2 tiles, 4 x 4 tiles ...). A **row** is a long strip of boards between two dark gaps; a **board** is one piece of a row between two joints; a **joint** is the dark crack where two boards meet; a **gap** is the dark line between two rows. A **window** is the piece of the source map that one board shows (where it starts, whether it is flipped, how much it is zoomed). A **stamp** is a small round cut-out of the source map laid on top (a stain). A **patch** is a very large soft light or dark cloud made by the recipe itself. A **seed** is a whole number that gives a new arrangement. The **MAIN version** reads the colour from the colour map; the **COMPARISON version** makes the colour from the height with a palette. A **near copy** is a part of a picture that looks almost the same as another part. A **seam** is a visible line where a picture does not continue into its own copy.

---

## 0. The result in one page

* **One recipe** (`recipe/wood_from_maps_recipe.py`, settings in `recipe/settings.json`, about @@nodes_main@@ nodes) that takes the uploaded height map and colour map as source material and arranges new boards out of them with Blender nodes only. It gives Colour, Roughness, Metallic and Height; the normal map is made from the arranged height (strength 8). No hand-made collage, no editing outside Blender.
* **A default tile** that repeats without a seam, and **bigger areas** (2, 4, 8 tiles across) of new boards that never repeat on purpose, from the same nodes: one setting (`recipe.tiles_across`).
* **Colour and relief always match**, because both maps are read at exactly the same place for every dot. Colour brightness predicts height with correlation @@corr_main@@ (the uploaded maps: @@corr_up@@).
* **Same-kind score** (the project's tool, 0 to 1) against the reference wood, three seeds: MAIN **@@main_mean@@**, COMPARISON **@@cmp_mean@@**, and the best new tile of the earlier pure-node wood recipe, scored the same way: **@@earlier@@**.
* **The tile repeats exactly**: baked with the pattern slid by half a tile it equals the normal bake slid by half a tile (mean difference @@half_tile_colour@@ in colour). The pipeline adds nothing of its own: with the arrangement switched off the height comes back to @@unchanged_height@@ and the normal made from it to @@unchanged_normal@@ of the uploaded normal.
* **A 4 x 4 area does not repeat at the tile or map width**: the picture correlates with itself shifted by one tile at @@shift_new@@ (the plain repeat of the map: @@shift_plain@@; the background of other shifts: up to @@shift_bg@@). **But the material is reused**: each used dot of the source map appears about @@reuse_times@@ times in 16 tiles, and @@near_new@@ (height) to @@near_new_colour@@ (colour brightness) of board-sized pieces have a near copy somewhere (plain repeat: 100 percent; the same test with the recipe's parts switched off: section 7.3). The two usable knots come back @@knots_4x4@@ times in 16 tiles. See section 7.
* **Joints:** every board joint of three default tiles (@@joints_total@@ crops) was looked at at full size; no cut shows. Weak points are in section 9.
* **No person has looked** at these pictures for "does it repeat?"; I did, with the measurements.

---

## 1. What was asked

"Maybe the wood is going to need the displacement map. But then procedurally generate more non repeating surface with it. Because it's not good." Taken to mean: the earlier wood recipes (nodes only, the picture as a guide) are not good enough, so for the wood only the uploaded displacement map may be used as source material, and Blender must arrange it procedurally into a tile that repeats and areas that do not. Then: "And the material map." Taken to mean: the uploaded colour map is also source material and is read with exactly the same arrangement as the height. The uploaded normal map is not read (a flipped board would have its slopes pointing the wrong way); the normal is made from the arranged height and compared with the uploaded normal as a check.

---

## 2. What the recipe does with the maps (the idea)

![reference | earlier recipe | new MAIN | new COMPARISON](sheets/wood_sheet.jpg)

1. **The source map is cut along its own structure.** It has five rows separated by dark gaps with small pebbles. Row 1 is only 155 dots high and is not used. The other four are cut from the middle of one gap to the middle of the next (starts at y = 189, 470, 709, 980 dots; lengths 281, 239, 271, 274): four "row strips", each with half a gap at the top and half a gap at the bottom.
2. **The new surface is laid out as rows of boards.** Five rows per tile of slightly different heights (they add up to exactly one tile), each row cut into three boards of random length (167 to 669 dots), every row shifted sideways by chance. Half of the neighbouring board pairs are joined into one long board.
3. **Every board shows its own window.** It takes one of the four row strips (never the same strip as its neighbour), a random start along it, a random flip left-right (chance 0.5) and upside down (0.4), a zoom of plus or minus 10 percent, a small tone and warmth change. About one board in eight shows a knot (at most one knot board per tile-wide stretch of a row); all other windows avoid the knots.
4. **The height map and the colour map are read at exactly the same place** (one position, built once, fed to both Image Texture nodes).
5. **Dark stain stamps** from the source map are laid on top at random places (two layers of stamps, each with only the dark part of the stamp painted), and two **very large soft patches** (light/dark drift and dark blotches) change the look from place to place. The patches change the colour only, not the relief.
6. **Every cut is hidden**: a dark ragged crack with dirt and pebbles and a worn light lip where two boards meet; a dark band of the same kind along every row boundary (the cut between two row strips lies in the middle of it, and so does the edge of the tile); a partial crack that starts at the top or bottom of the row inside every joined board.
7. **Height** is the height read from the source (plus a small change linked to the board's tone, the stamps, and the cracks). **Roughness** is made from the height and a small change per board. **Metallic** is 0.
8. **Default tile or area from the same nodes:** with `recipe.tiles_across = 1` every random number repeats after exactly one tile; with 2, 4, 8 the random numbers keep counting up, so nothing repeats on purpose, and a number of things are counted per tile-wide stretch so that the amount per dot stays the same.

---

## 3. The steps inside the recipe (what you see in the Shader editor)

Open the node group **WOOD FROM MAPS**: it is divided into labelled frames (about @@nodes_main@@ nodes in the default tile, @@nodes_area@@ in an area, @@nodes_identity@@ with the arrangement switched off).

| Frame | What it does |
|---|---|
| **0 PLACE** | turns the coordinate of the picture (0 to 1) into dots on the area (one tile = 1254 dots); handles the slide test (`shift`) and crops (`window`) |
| **1 ROWS** | five rows of slightly different heights; finds the row of this dot, how far down in the row it is, and the row number the random numbers are made from |
| **2 BOARDS** | finds the board (random lengths, row shifted by chance), decides whether two neighbouring boards are joined, and makes the random numbers of the board |
| **3 WINDOW** | chooses the source row strip, where the window starts (avoiding knots or containing one), flips, zoom, and works out the position in the source map for this dot |
| **4 READ THE MAPS** | reads the height map and the colour map at that position (COMPARISON: makes the colour from the height with a palette instead) |
| **5 STAINS** | two layers of stamps (one per cell of 250 dots, shifted against each other by half a cell); each paints the dark part of a stain from the source map |
| **6 JOINTS AND GAP BANDS** | the cracks, the row bands, the partial cracks inside joined boards, with dirt, pebbles and a worn lip |
| **7 PATCHES** | the very large soft light/dark drift and dark blotches (seamless in the tile) |
| **8 COLOUR** | per-board tone and warmth, patches, edge shading, crack colour |
| **9 HEIGHT and ROUGHNESS** | height changes, roughness |
| **OUTPUTS** | the four outputs, or one of the debug views |

Tools: **Math** nodes (all the arithmetic), **White Noise Texture** in 4D (the hash: the same inputs give the same three random numbers; used for every random choice), **Image Texture** (reads the two maps, Linear reading, positions bounced back with Ping-Pong so a window never leaves the non-wrapping map), **Color Ramp** (used as small look-up tables of up to four numbers, and as the 32-step palette of the COMPARISON version), **Noise Texture** and **Voronoi Texture** (cracks, dirt, pebbles, patches; 4D "donut" versions in the repeating tile).

---

## 4. Every setting

Settings live in `recipe/settings.json` as `group.control`. Order of strength: the default written in the recipe file < `settings.json` < the parameters you pass (for example `--params '{"layout.boards_per_row": 2}'`). "Swept" means a picture of three values is in section 5.

| Setting | What it does | Range (default) | What changing it does |
|---|---|---|---|
| `recipe.tiles_across` | how many tiles across the picture | 1, 2, 4, 8 (1) | 1 = one tile that repeats exactly; more = an area of new boards. Bake with 1254 x that many dots, or fewer (smaller picture, same content) |
| `recipe.tile_repeats` | force the behaviour | -1 automatic, 0, 1 (-1) | 1 with `tiles_across` 2 = the default tile repeated 2 x 2 on purpose (the seam test picture); 0 with 1 = new boards everywhere |
| `recipe.seed` | a new arrangement | any whole number (1) | different boards, windows, stains; seeds 1, 2, 3 are in `outputs/` (correlation between two seeds' heights about 0.04) |
| `layout.rows_per_tile` | rows in one tile | 4 to 6 (5) | built into the nodes. 5 gives rows of 251 dots like the source; 4 and 6 were baked once (sweep) and look right, but the windows are then scaled by 0.76 to 0.90 (4 rows) or 1.14 to 1.34 (6 rows) instead of 0.96 to 1.14, so they are softer or sharper than the source |
| `layout.row_height_variation` | how different the five row heights are | 0 to 0.2 (0.05) | more = more irregular rows but more zoom of the windows (blur) |
| `layout.boards_per_row` | boards in a row | 2, 3, 4 (3) | **swept.** 2 = long planks, fewer joints, but more near copies (33 percent of board-sized pieces against 12 percent) and a lower score; 4 = many short boards |
| `layout.board_length_variation` | how different the board lengths are | 0 to 0.8 (0.6) | 0 = all boards equally long (brick wall); 0.6 = lengths between 0.4 and 1.6 times the average |
| `layout.joined_share` | share of neighbouring pairs joined into one long board | 0 to 1 (0.5) | **swept.** 0 = every joint a full crack; 1 = every pair that fits is joined (partial crack only) |
| `layout.joined_max_length` | longest joined board, as a part of a tile | 0.3 to 0.9 (0.72) | pairs longer than this stay separate (a window cannot be longer than the source map) |
| `windows.zoom` | random zoom of every window | 0 to 0.2 (0.10) | **swept.** more = fewer near copies, a little softer detail |
| `windows.flip_left_right` | chance a board is flipped left-right | 0 to 1 (0.5) | 0 = no flips (more near copies) |
| `windows.flip_upside_down` | chance a board is turned upside down | 0 to 1 (0.4) | turns the whole window (a gap half is at both ends, so it still fits) |
| `windows.knot_share` | share of boards that show a knot | 0 to 1 (0.12) | **swept.** at most one knot board per tile-wide stretch of a row; 0 = no knots; only the two knots of rows 2 and 4 exist, so more knots = more repeats of the same two |
| `boards.tone_variation` | brightness change per board | 0 to 0.6 (0.24) | 0.24 = plus or minus 12 percent |
| `boards.warmth_variation` | warm/cool change per board | 0 to 0.3 (0.12) | red up and blue down, or the other way |
| `boards.height_shift` | height change linked to the tone | 0 to 0.3 (0.10) | brighter boards sit a little higher |
| `joints.width` | width of a joint crack in dots | 0 to 12 (4) | **swept.** wider = more visible slits; the crack must stay wider than the cut it hides (the cut is straight, the edges of the crack are ragged) |
| `joints.gap_band_width` | width of the dark band on every row boundary | 0 to 10 (4) | hides the cut between two row strips and the tile edge; 0 would show the cut |
| `joints.raggedness` | how much the crack edges wander | 0 to 1 (0.8) | |
| `joints.notches` | deeper notches in the crack edges | 0 to 1 (0.8) | |
| `joints.edge_lip` | light worn edge next to a crack (a little higher) | 0 to 1 (0.5) | shows in the lit picture as a bevel |
| `joints.pebbles` | pebbles in the cracks | 0 to 1 (0.8) | |
| `joints.edge_shade` | darker wood next to a joint | 0 to 1 (0.35) | |
| `joints.wobble_length` | length of the crack wobble in dots | 8 to 60 (22) | |
| `stains.amount` | chance per cell for a stain stamp (two layers) | 0 to 1 (0.18) | **swept.** more stains hide repeats but darken the picture and lower the score |
| `stains.size` | radius of a stamp in dots | 40 to 120 (85) | |
| `stains.zoom` | random zoom of a stamp | 0 to 0.4 (0.25) | |
| `stains.dark_limit`, `stains.dark_softness` | which part of the stamp is painted (grey under 135 of 255) | 100 to 160, 20 to 80 | only the dark stain is painted, not the wood grain inside the circle |
| `masks.drift_amount`, `masks.drift_size` | very large light/dark drift: amount and clouds per tile | 0 to 0.3 (0.10), 1 to 4 (2) | colour only |
| `masks.blotch_amount`, `masks.blotch_size` | very large dark blotches | 0 to 0.5 (0.15), 3 to 8 (5) | **swept.** colour only |
| `masks.darken_height` | how much of the patches also lowers the height | 0 to 1 (0) | 0 = patches are colour only (a stain film has no relief); 0.5 lowered the height scores in the first test |
| `colour.source` | where the colour comes from | `map` or `height_palette` (`map`) | `height_palette` = the COMPARISON version |
| `colour.palette` | the 32-step palette (height to colour) measured from the colour map | 32 pairs | used only for the COMPARISON version |
| `roughness.base`, `roughness.from_height`, `roughness.board_variation` | roughness | 0.78, 0.20, 0.04 | roughness = base + from_height x (height - 0.5) + a little per board |
| `bake.exact_dots` | ask the photograph for exact dots | 1 | when one picture dot = one source dot, uses 1 sample and a pixel filter of 0.01 so every dot is read at its own centre (the harness default would blur by about a dot) |
| `bake.shrink_samples`, `bake.shrink_filter` | samples and filter when the picture is smaller than the source | 8, 1.0 | e.g. a 4 x 4 area baked at 2508 dots |
| `debug.source_unchanged` | switch the arrangement off | 0 / 1 (0) | gives back the uploaded height (the check in section 7) |
| `source.*` | facts about the uploaded maps (file names, row strips, knot-free stretches, knot positions, stain stamp centres) | | measured, see `research/` |

Special parameters (not settings): `shift` [u, v] slides the pattern by that much of the picture (the slide test); `window` [x, y, size] bakes only a part of a big area, in tiles (for example [1.5, 2, 1] = the tile that starts one and a half tiles from the left and two from the top); `debug_view` = `boards` (a random colour per board), `rows`, `flips` (red = flipped left-right, green = upside down, blue = knot board), `source_x` / `source_y` (exact: which dot of the source map every dot was taken from); `settings_file`.

---

## 5. Sweep pictures

All sweeps change one setting of the default tile (seed 1) and nothing else, so the layout stays put and only that setting shows.

**Boards per row (2, 3, 4):** ![boards per row](sheets/sweep_boards_per_row.jpg)

**Joined pairs (0, 0.5, 1):** ![joined share](sheets/sweep_joined_share.jpg)

**Stain stamps (0, 0.18, 0.5):** ![stains](sheets/sweep_stains_amount.jpg)

Also in `sheets/`: `sweep_knot_share.jpg`, `sweep_patches.jpg` and `sweep_rows_zoom_joints.jpg` (rows per tile 4 and 6, zoom 0 and 0.2, joint width 2 and 9).

---

## 6. How to bake

* **With the project's standard command** (this works: it was run on the final recipe at 512 dots, `tests/cli_check`, and earlier for seed 1 at 1254 dots; about 100 seconds under load):
  `blender -b --disable-autoexec -t 2 --python lib/bake_harness.py -- recipes/wood_from_displacement/recipe/wood_from_maps_recipe.py OUT_FOLDER --size 1254 --params '{"recipe.seed": 1}'`
  It writes colour.png, height.png (16-bit), roughness.png, metallic.png and normal.png (made from the height, two-neighbour slope, strength 8) and normal_bumpnode.png (a cross-check, not needed).
* **Several pictures in one Blender run:** `tools/run_jobs.py` with a jobs file (examples: `tests/jobs_final_all.json`). A job with `"full": true` is the standard bake; otherwise it lists channels.
* **The COMPARISON version:** add `"colour.source": "height_palette"` to the parameters; the height and normal are the same as MAIN.
* **A bigger area:** `{"recipe.tiles_across": 4}` with `--size 2508` (about 5 minutes per channel under load) or smaller. **A full-size piece of an area:** add `"window": [1.5, 1.5, 1]` and bake 1254 dots.
* **Speed (machine under load, 2 threads):** see the table below.

@@TABLE_SPEED@@

---

## 7. Results

### 7.1 "Same kind of surface" score against the reference wood

(`lib/texture_compare.py`: 0 = as different as another real surface, 1 = indistinguishable by those measures; other real surfaces score 0.16 to 0.50; a re-shuffled copy of the reference itself about 0.99.) The earlier wood recipe's best new tile (its seed 105) was baked again from its own description at 1254 dots and scored with the same tool today.

@@TABLE_SCORES@@

The measures behind the scores (seed 1):

@@TABLE_MEASURES@@

Read this as: the new tile (MAIN seed 1) is closer to the reference than the earlier recipe's tile on @@m_better@@ of the 14 measures, equal on the seam measure, and worse on @@m_worse@@ (@@m_worse_names@@). The COMPARISON colour (made from height) is clearly plainer than the colour map (colour score @@cmp_colour@@ against @@main_colour@@; its colour spectrum is the weakest number of all). The tool rewards staying close to the map's own statistics, so every thing that breaks repetition (stains, patches, tone) costs score; section 9 lists what each cost.

**Dot-for-dot numbers (for transparency only).** The new boards are not where the reference's boards are, so these are low on purpose and say nothing about quality:

@@TABLE_PIXEL@@

### 7.2 The pipeline adds nothing of its own, and the tile repeats exactly

@@TABLE_CHECKS@@

![the tile repeated 2 x 2, and the uploaded map repeated 2 x 2](sheets/seam_2x2.jpg)

The 2 x 2 picture on the left is four copies of one default tile: no step shows at the yellow tick marks. The uploaded map repeated the same way (right) shows a straight seam.

@@TABLE_SEAM@@

### 7.3 Does a big area repeat? (the REPEAT test)

![the 4 x 4 area, shrunk](sheets/area_4x4.jpg)

![full-size crops of the 4 x 4 area across tile lines](sheets/area_crops.jpg)

**(a) Shift test** (how much the picture looks like itself slid sideways; 1 = identical, 0 = nothing alike):

@@TABLE_SHIFT@@

**(b) How much of the source map is used, and how often** (from the exact "which source dot" pictures of the 4 x 4 area):

@@TABLE_REUSE@@

**(c) Near copies** (the research test: 40 board-sized patches of 36 x 80 at 1024 dots are searched for in the other rows, also flipped; a best match above 0.8 = "has a near copy"; patches of 24 x 40 test feature-size pieces; with 40 patches, differences under about 10 points are noise):

@@TABLE_NEAR@@

With parts of the recipe switched off (4 x 4 areas of height at 1024 dots):

@@TABLE_NEAR_SWITCH@@

Reading it: the windows alone leave about a third of the board-sized pieces with a near copy; zoom, flips, tone, stains, large patches and joined boards together bring it down to about 12 percent in this 1024-dot test (20 percent for height and 30 percent for colour brightness in the test on the 2508-dot area; the numbers differ by sampling noise, since only 40 patches are drawn, and by what is looked at). Four boards per row repeat least, two boards per row (long planks) most. Feature-size pieces (a short crack pattern, a stain cluster) still come back in about half of the tests: that is what "every piece of the map is used about @@reuse_times@@ times in 16 tiles" means, and it cannot be fixed without a bigger source map.

### 7.4 Joints and the lit look

![every joint of seed 1 at full size](sheets/joints_seed1.jpg)

`sheets/joints_seed1.jpg`, `joints_seed2.jpg` and `joints_seed3.jpg` hold one full-size crop of every joint found (@@joints_total@@ crops in all; some joints are found twice, where a row band crosses them). I looked at all of them: the crack hides the cut in every one and no cut shows. What I see: some joints are very straight; a few crops show a soft dark horizontal smudge next to a joint (about 6 in 75; a stain stamp that caught a dark crack of the source, see section 9); the pebbles in the cracks are round and evenly spaced when looked at closely. The mirrored "butterfly" pattern across a joint that I saw in the first version of seed 2 is gone in the final sheets.

![reference and new, lit by a low sun](sheets/lit.jpg)

The same raking light on the reference and on the new tile: the relief of the new tile has the same character (grain, cracks, stains); the joints show as slits.

### 7.5 MAIN colour against COMPARISON colour

![three seeds, MAIN above, COMPARISON below](sheets/seeds.jpg)

Both versions use exactly the same arrangement, the same tone per board and the same patches. The colour made from the height with a 32-step palette (measured from the colour map itself, so only fair as a comparison) differs from the colour map by Delta E @@de_mean@@ on average (@@de_p95@@ at the 95th percent point; about 1 is just visible, 2 to 5 small, over 10 clearly another colour). The mean colours are almost equal. The comparison is plainer: it has no orange highlights and no blue-grey patches, because a palette cannot tell an orange area from a blue-grey one when both have the same brightness.

### 7.6 All maps of the default tile

![all maps](sheets/maps.jpg)

---

## 8. Files in this folder

| Path | What it is |
|---|---|
| `recipe/wood_from_maps_recipe.py`, `recipe/wood_node_kit.py`, `recipe/settings.json` | the recipe, its helper and its settings (audited with `lib/description_audit.py`: passes) |
| `outputs/main_seed1..3` | the default tile, all maps (colour, height 16-bit, roughness, metallic, normal) |
| `outputs/comparison_seed1..3` | the COMPARISON colour (height and normal are the same files as MAIN) |
| `area/` | the 2 x 2 and 4 x 4 areas, the repeated tile, the crops, the exact debug pictures (converted to smaller files at the end) |
| `variations/` | the sweep pictures |
| `sheets/` | all the sheets shown in this guide |
| `scores/` | `final_scores_round1.json`, `checks_round1.json`, `repeat_tests_round1.json` |
| `tools/` | the job driver, the scoring, repeat and check scripts, the sheet makers (each starts with a plain note) |
| `tests/` | job lists, logs, the earlier recipe's tile baked again for scoring |
| `research/` | the research that came first |
| `build_result_round_1.json` | the structured result of this round |

---

## 9. Dead ends, failures and weak points (in the order they happened)

1. **First joints were flat black bars** (they looked drawn). Replaced by a ragged crack with dirt, pebbles and a worn lip.
2. **Rows cut from gap-top to gap-top** put wood against wood at the row boundary; the project's seam measure gave the tile a tiling score of 0.19 and then 0.0, although the half-tile slide test passed. Cutting from gap-middle to gap-middle and laying a dark band over every row boundary hid the cut: tiling score 1.0.
3. **Stain stamps from the map contained knots** (two of the first eight stamps held a knot: one the biggest knot K2, one the partial knot K4): the knot came back as a smaller second knot in the same board. The two stamp centres were replaced.
4. **The same-kind score dropped when everything was on** (0.76 with every part against 0.85 with none, seed 1); the large patches (-0.05), the stains (-0.02) and the row-height and zoom changes together (-0.016) cost most (the switch-off sweep, `tests/sweep1_scores.json`, an earlier version of the recipe). I lowered the amounts and made the patches colour-only (they had lowered the height scores). The recipe's defaults are a compromise between the score and hiding repeats; both numbers are in this guide.
5. **Two boards per row scored lower** (mean @@b2_mean@@ against @@b3_mean@@ for three boards, three seeds, an earlier version of the settings) and repeats more (33 percent near copies against 12). Three boards per row, with half of the pairs joined, is the default.
6. **"At most one knot per row" in a bigger area** meant one knot per 4 tiles of row, four times too few per dot. Found by counting the knots in the 4 x 4 picture (24 knot boards in 16 tiles after the fix).
7. **Two neighbouring boards could take the same source row**, which shows the same piece side by side with one of them mirrored (a butterfly across the joint; 2 of 25 joints in seed 2). Fixed: every next board takes the next source row.
8. **My first board counting in the repeat test was wrong**: board numbers read from a colour debug picture are dithered, so one board became hundreds (1107 "boards" instead of about 230). Now read from the exact 16-bit picture.
9. **My job list wrote into the wrong folder once** (relative paths, started from the project folder); the files were moved. Two runs were stopped and started again after changes. About @@runs@@ Blender runs were used in all (the budget was about 25).
10. **A rule in the research notes was mislabelled:** the uploaded normal map equals the two-neighbour slope of the uploaded height at strength 8 (@@normal_rule@@), not a 3 x 3 Sobel filter.

**Weak points that remain:** soft dark smudges where a stain stamp catches a dark horizontal crack of the source (the stamp paints every grey under 135 with a soft edge; I did not test stricter settings such as `stains.dark_limit` 100 and `stains.dark_softness` 30, which should paint only the very dark blots); the joints are full-height straight cracks in most of the cases (the real joints of the map are partial and stepped; the joined boards with partial cracks are closer); a few joints are very straight; the surface still reads as a wall of boards more than as one log wall; the same two knots, the same big cracks and the same stain clusters come back (section 7.3); every tile and area is only as good as the source map; boards have a little more tone change between neighbours than the source has between rows (that is wanted, it breaks repetition).

---

## 10. Not tested, and where I am unsure

* **Nobody looked** at the pictures for "does it repeat?" except me. The near-copy numbers are the research's own measure, not a measure of what a person sees.
* **Seeds 1 to 3 only.** Other seeds will move the scores by a few points (the three seeds differ by up to @@seed_spread@@ in the same-kind score).
* **Sizes:** the 8 x 8 area was baked only at 512 dots (it runs); areas larger than that and tiles at other sizes were not tried. Bake time of the 4 x 4 area at 2508 dots is about 5 minutes per channel under load.
* **Settings not swept or not baked at all:** `joints.wobble_length`, `joints.raggedness`, `joints.notches`, `joints.edge_lip`, `joints.pebbles`, `joints.edge_shade`, `stains.size`, `stains.zoom`, `stains.dark_limit`, `stains.dark_softness`, `masks.*size`, `boards.height_shift`, `roughness.*`, `layout.joined_max_length`, `layout.board_length_variation` and the palette. Their effects in the table are what the code does, not what a sweep showed.
* **Roughness** was only looked at as a picture; the lit pictures use a constant roughness for both reference and new. The recipe's roughness map has no reference to compare with.
* **The normal map** of an arranged surface cannot be compared with anything (there is no reference for it); only the pipeline check on the unchanged source was done.
* **Other Blender versions, GPU rendering, other renderers:** not tried (Blender 5.2.2, Cycles on the CPU).
* **Use in a 3D scene** (as a material on a mesh): not tried.
* **The shared slate layers** were not used (the wood needs stains and patches from the map itself).
* **The test "LATER - realistic moss and damage ..."** was not started, as instructed.
