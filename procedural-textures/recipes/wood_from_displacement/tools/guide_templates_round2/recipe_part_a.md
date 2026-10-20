# 08 Recipe - wood from your displacement and colour maps - how it is made

**What this file is:** the full guide to the wood-from-maps recipe, written for a person who is not a programmer. It says what the recipe does with the uploaded wood maps, what every setting does, what the pictures and the measurements showed (including what failed), and what I did not test. It describes the recipe as it is after **round 2** (the round in which two independent checkers judged round 1 and I fixed what they found; the round 2 section is section 11). The companion file `08 Lessons - wood from your displacement and colour maps - what carries over to other surfaces.md` says what carries over to other surfaces. The research that came first is in `research/08 Research - making big non-repeating surfaces from one map.md`.

**Words used the same way everywhere.** A **dot** is one pixel. The **source map** is an uploaded picture (the displacement map, which is a grey height picture where brighter means higher, or the colour map) used as raw material; it is 1254 x 1254 dots. A **tile** is the default square of 1254 x 1254 dots that repeats without a seam. An **area** is a bigger picture of new content (2 x 2 tiles, 4 x 4 tiles ...). A **row** is a long strip of boards between two dark gaps; a **board** is one piece of a row between two joints; a **joint** is the dark crack where two boards meet; a **gap** is the dark line between two rows. A **window** is the piece of the source map that one board shows (where it starts, whether it is flipped, how much it is stretched). A **step** is a joint that is not one straight line: it runs down, jumps sideways along a crack in the grain, and runs down again, like the stepped joints of the source. A **half joint** is a short crack from the edge of a row that tapers to a point and hides no cut (it is only for looks). A **landmark** is a place of the source map so recognisable that a person notices when it comes back (a knot, a zigzag crack, an orange splinter, a big rust cloud). To **paint out** a landmark means to show clean grain from another place of the map where the landmark would be. A **stamp** is a small round cut-out of the source map laid on top (a stain). A **patch** is a very large soft light or dark cloud made by the recipe itself. A **seed** is a whole number that gives a new arrangement. The **MAIN version** reads the colour from the colour map; the **COMPARISON version** makes the colour from the height with palettes. A **near copy** is a part of a picture that looks almost the same as another part. A **seam** is a visible line where a picture does not continue into its own copy.

---

## 0. The result in one page

@@RESULT_PAGE@@

---

## 1. What was asked

"Maybe the wood is going to need the displacement map. But then procedurally generate more non repeating surface with it. Because it's not good." Taken to mean: the earlier wood recipes (nodes only, the picture as a guide) are not good enough, so for the wood only the uploaded displacement map may be used as source material, and Blender must arrange it procedurally into a tile that repeats and areas that do not. Then: "And the material map." Taken to mean: the uploaded colour map is also source material and is read with exactly the same arrangement as the height. The uploaded normal map is not read (a flipped board would have its slopes pointing the wrong way); the normal is made from the arranged height and compared with the uploaded normal as a check.

---

## 2. What the recipe does with the maps (the idea)

![reference | round 1 | round 2 MAIN | round 2 COMPARISON](sheets/wood_sheet.jpg)

1. **The source map is cut along its own structure.** It has five rows separated by dark gaps with small pebbles. Row 1 is only 155 dots high and is not used. The other four are cut from the middle of one gap to the middle of the next (starts at y = 189, 470, 709, 980 dots; ends at 470, 709, 980, 1254): four "row strips", each with half a gap at the top and half a gap at the bottom. Every row strip is always shown from its top gap middle to its bottom gap middle, so every row edge of the new surface lies on a real gap of the source and keeps its small dark pebbles.
2. **The new surface is laid out as rows of boards.** Five rows per tile whose heights differ by up to 20 percent (they add up to exactly one tile), the edge between two rows waves by up to 4 dots. Each row is cut into two boards per tile (the cut positions jitter by up to 40 percent of a board, so boards are 0.1 to 0.9 of a tile long), every row shifted sideways by chance.
3. **The cut between two boards is a stepped joint.** About 7 joints in 10 have one step: above the step the cut lies up to 45 dots to the left, below it up to 45 dots to the right, and a crack along the grain joins the two parts. So a joint is two half-height cracks, as in the source, not one straight line from the top of the row to the bottom.
4. **Every board shows its own window.** It takes one of the four row strips (the next board always takes a different strip, and so does the next row, see section 11), a random start along it, a random flip left-right (chance 0.5) and upside down (0.4), is stretched along the board by up to 25 percent, bent by a slow wobble (up to 12 dots along, 5 dots across) and tilted by up to 3.5 degrees, so that no two windows have the same shape. The bending dies away at the row edges so they stay on the gaps.
5. **Landmarks are painted out unless a board draws a lucky number.** Twelve landmarks of the source (3 knots, 9 other recognisable places) have a ragged round disc; inside it the recipe reads the map a second time, at another place with clean grain (found once by `tools/find_landmark_replacements.py` and stored as numbers in `recipe/settings.json`). Each board draws one random number per landmark: with 30 percent (knots) or 20 percent (the others) the board shows the landmark, otherwise it is painted out.
6. **The height map and the colour map are read at exactly the same place** (one position, built once, fed to both Image Texture nodes), also for the clean grain behind a painted-out landmark.
7. **Dark stain stamps** from the source map are laid on top at random places (two layers of stamps, each with only the dark part of the stamp painted, with a hard edge, kept 15 dots away from joints and row edges). Two **very large soft patches** (light/dark drift and dark blotches) change the look from place to place; they change the colour only, not the relief.
8. **Every cut is hidden**: a dark ragged crack of random width (1.4 to 5.8 dots across, some joints faint, some strong) with dirt and a few pebbles of different sizes where two boards meet; a dark band along every row edge that is only added where the source is not already dark (so the real gap rubble of the source stays); half joints inside many boards.
9. **Tone** changes a little per board and more per row (so neighbours in one row look alike, rows differ, and the joints show less). **Height** is the height read from the source (plus a small change linked to the tone, and the cracks). **Roughness** is made from the height and a small change per board. **Metallic** is 0.
10. **COMPARISON version:** the colour is not read from the colour map but made from the height with three palettes measured from the colour map (dull blue-grey wood, plain brown wood, orange bare wood); two slow cloud patterns choose where the orange and blue-grey patches lie. Everything else is identical to MAIN.
11. **Default tile or area from the same nodes:** with `recipe.tiles_across = 1` every random number repeats after exactly one tile; with 2, 4, 8 the random numbers keep counting up and are salted differently from the tile, so nothing repeats on purpose and the first tile of an area is not the default tile (round 1 had this wrong, see section 11). A number of things are counted per tile-wide stretch so that the amount per dot stays the same.

---

## 3. The steps inside the recipe (what you see in the Shader editor)

Open the node group **WOOD FROM MAPS**: it is divided into labelled frames (about @@NODES_TILE@@ nodes in the default tile, @@NODES_AREA@@ in an area, @@NODES_IDENTITY@@ with the arrangement switched off).

| Frame | What it does |
|---|---|
| **0 PLACE** | turns the coordinate of the picture (0 to 1) into dots on the area (one tile = 1254 dots); handles the slide test (`shift`) and crops (`window`); makes the seamless cloud helpers |
| **1 ROWS** | five rows of different heights with waving edges; finds the row of this dot, how far down in the row it is, and the row number the random numbers are made from |
| **2 BOARDS** | finds the board (random lengths, row shifted by chance), makes the stepped cut of every board end, and the random numbers of the board |
| **3 WINDOW** | chooses the source row strip, where the window starts, flips, stretch, bending and tilt, and works out the position in the source map for this dot |
| **4 LANDMARKS + READ THE MAPS** | decides for every landmark whether this board shows it; reads the height map and the colour map at that position (and at the clean place where a landmark is painted out); COMPARISON: makes the colour from the height instead |
| **5 STAINS** | two layers of stamps (one per cell of 250 dots, shifted against each other by half a cell); each paints the dark part of a stain from the source map |
| **6 JOINTS, HALF JOINTS AND ROW EDGES** | the cracks, the sideways cracks of the steps, the half joints, the row bands, with dirt, pebbles and a worn lip |
| **7 PATCHES** | the very large soft light/dark drift and dark blotches (seamless in the tile) |
| **8 COLOUR** | tone per board and per row, warmth, patches, edge shading, crack colour |
| **9 HEIGHT and ROUGHNESS** | height changes, roughness |
| **OUTPUTS** | the four outputs, or one of the debug views |

Tools: **Math** nodes (all the arithmetic), **White Noise Texture** in 4D (the hash: the same inputs give the same three random numbers; used for every random choice), **Image Texture** (reads the two maps, Linear reading, positions bounced back with Ping-Pong so a window never leaves the non-wrapping map), **Color Ramp** (used as small look-up tables of up to four numbers, and as the palettes of the COMPARISON version), **Noise Texture** and **Voronoi Texture** (bending, cracks, dirt, pebbles, patches; 4D "donut" versions in the repeating tile).

---

## 4. Every setting

Settings live in `recipe/settings.json` as `group.control`. Order of strength: the default written in the recipe file < `settings.json` < the parameters you pass (for example `--params '{"layout.boards_per_row": 3}'`). "Swept" means a picture of three values is in section 5. A setting marked (new) did not exist in round 1; (changed) means the meaning or the default changed.

| Setting | What it does | Range (default) | What changing it does |
|---|---|---|---|
| `recipe.tiles_across` | how many tiles across the picture | 1, 2, 4, 8 (1) | 1 = one tile that repeats exactly; more = an area of new boards. Bake with 1254 x that many dots, or fewer (smaller picture, same content) |
| `recipe.tile_repeats` | force the behaviour | -1 automatic, 0, 1 (-1) | 1 with `tiles_across` 2 = the default tile repeated 2 x 2 on purpose (the seam test picture); 0 with 1 = new boards everywhere |
| `recipe.seed` | a new arrangement | any whole number (1) | different boards, windows, joints, stains; seeds 1, 2, 3 are in `outputs/`. An area with seed 1 is not the tile of seed 1 (changed in round 2) |
| `layout.rows_per_tile` | rows in one tile | 4 to 6 (5) | built into the nodes. 5 gives rows of 251 dots like the source |
| `layout.row_height_variation` | how different the row heights are (changed: 0.05 before) | 0 to 0.35 (0.2) | **swept.** 0 = all rows the same height (looks like a brick wall); 0.2 = rows between 200 and 300 dots high; more = more zoom of the windows (blur or sharper) |
| `layout.boards_per_row` | boards in a row per tile (changed: 3 before) | 2, 3, 4 (2) | **swept.** 2 = long boards and few joints; 4 = many short boards (brick-like). Needs `joints.step_size` smaller than a board length times (1 - `layout.board_length_variation`). With 5, 9, ... boards two touching boards could take the same source row (the rule needs a number that is not 1 more than a multiple of 4) |
| `layout.board_length_variation` | how different the board lengths are (changed: 0.6 before) | 0 to 0.8 (0.8) | 0 = all boards equally long (brick wall); 0.8 = every cut moves by up to 40 percent of a board: boards from 0.1 to 0.9 of a tile |
| `windows.zoom` | random stretch of every window along the board (changed: 0.10 before; now along the board only, because the row strip always fills the row) | 0 to 0.3 (0.25) | more = fewer near copies, a little softer or sharper grain, knots a little oval (0.75 to 1.25 times as wide) |
| `windows.flip_left_right` | chance a board is flipped left-right | 0 to 1 (0.5) | 0 = no flips (more near copies) |
| `windows.flip_upside_down` | chance a board is turned upside down | 0 to 1 (0.4) | turns the whole window (a gap half is at both ends, so it still fits) |
| `windows.warp_along`, `windows.warp_across`, `windows.warp_size` (new) | slow bending of every window: size of the bending along the grain and across it (dots), and the length of one wave (dots) | 0 to 30, 0 to 14, 100 to 300 (12, 5, 200) | **swept.** 0 = grain stays as in the source (landmarks keep their exact shape); more = grain waves like a log's; the bending dies away at the row edges |
| `windows.tilt` (new) | the strip may be tilted by up to this many degrees | 0 to 5 (3.5) | tilts the grain lines of a board against the row |
| `windows.edge_margin` (new) | dots kept free at the ends of the source row so the bending never reads outside the map | 28 | must be larger than `windows.warp_along`; raise it with a strong bending |
| `landmarks.knot_chance` (new, replaces `windows.knot_share`) | chance that a board whose window contains a knot shows it | 0 to 1 (0.3) | **swept** (with the next setting). 0 = no knots at all; 1 = every knot that falls in a window is shown |
| `landmarks.mark_chance` (new) | the same for the 9 other landmarks (zigzag cracks, splinters, rust cloud ...) | 0 to 1 (0.2) | 0 = all painted out; 1 = all shown (the repeats the checker found) |
| `landmarks.edge_ragged` (new) | how ragged the edge of a painted-out disc is | 0 to 0.6 (0.3) | 0 = a round, visible disc; more = grain-like edge |
| `landmarks.list` (new) | the twelve landmarks: x, y, radius, shift to the clean grain, kind | list | measured once (`tools/find_landmark_replacements.py`); other maps need their own list |
| `boards.tone_variation`, `boards.row_tone_variation` | brightness change per board and per row (changed: 0.24 per board before; the row part is new) | 0 to 0.6 (0.12, 0.16) | 0.12 = plus or minus 6 percent per board, plus or minus 8 percent per row |
| `boards.warmth_variation` | warm/cool change per board | 0 to 0.3 (0.12) | red up and blue down, or the other way |
| `boards.height_shift` | height change linked to the tone | 0 to 0.3 (0.10) | brighter boards sit a little higher |
| `joints.width` | average width of a joint crack in dots (changed: 4.0 before) | 0 to 12 (3.6) | wider = more visible slits |
| `joints.width_variation` (new) | how much the width differs from joint to joint | 0 to 1 (0.6) | 0.6 = every joint between 0.4 and 1.6 times the average |
| `joints.step_share`, `joints.step_size` (new) | chance that a joint has a step, and the biggest sideways jump of a step (dots) | 0 to 1, 0 to 120 (0.7, 90) | **swept.** 0 = every joint one straight line from the top to the bottom of the row (the look of round 1: brick wall); 1 = every joint stepped. `step_size` must stay smaller than the shortest board minus a bit |
| `joints.darkness`, `joints.darkness_variation` (new) | how dark the cracks are, and how much stronger some joints are than others | 0 to 1, 0 to 1 (0.9, 0.5) | lower = faint joints that show the cut more |
| `joints.raggedness`, `joints.notches`, `joints.wobble`, `joints.wobble_length` | how much the crack edges wander and get notches, and the sideways wobble of the cut | 0 to 1 (0.8), 0 to 1 (0.6), 0 to 6 dots (2), 8 to 60 (22) | |
| `joints.edge_lip` | light worn edge next to a crack (a little higher) | 0 to 1 (0.4) | shows in the lit picture as a bevel |
| `joints.pebbles` | pebbles in the cracks (now of different sizes, in small groups) | 0 to 1 (0.45) | |
| `joints.edge_shade` | darker wood next to a joint | 0 to 1 (0.2) | |
| `joints.half_share`, `joints.half_depth`, `joints.half_run`, `joints.half_width` (new) | half joints: chance per board, depth as a part of the row height, length of the sideways run (dots), width at the edge (dots) | 0 to 1 (0.35), 0.1 to 0.6 (0.32), 20 to 120 (70), 2 to 8 (5) | 0 = no half joints |
| `gaps.band_width`, `gaps.band_variation` (changed: was `joints.gap_band_width` 4) | width of the dark band on every row edge (dots) and how much it changes along the edge | 0 to 10 (3.2), 0 to 1 (0.9) | the band is only added where the source is not already dark; hides the cut between two rows and the tile edge |
| `gaps.wobble`, `gaps.wobble_length` (new) | how far the row edges wave (dots) and the length of one wave | 0 to 8 (4), 60 to 300 (140) | 0 = dead straight row edges |
| `stains.amount` | chance per cell for a stain stamp (two layers) (changed: 0.18 before) | 0 to 1 (0.16) | more stains hide repeats but darken the picture and lower the score |
| `stains.size`, `stains.zoom` | radius of a stamp in dots, random zoom of a stamp | 40 to 120 (85), 0 to 0.4 (0.25) | |
| `stains.dark_limit`, `stains.dark_softness` (changed: 135 and 55 before) | which part of the stamp is painted (grey under 100 of 255, edge 30 wide) | 100 to 160, 20 to 80 | only the very dark blots are painted, with a crisper edge |
| `stains.keep_away`, `stains.edge_hardness` (new) | stamps stay this many dots away from joints and row edges; how hard the round edge of a stamp is | 0 to 40 (15), 0.5 to 0.95 (0.8) | 0 = stamps may cover joints (the soft smudges of round 1) |
| `masks.drift_amount`, `masks.drift_size` | very large light/dark drift: amount and clouds per tile | 0 to 0.3 (0.10), 1 to 4 (2) | colour only |
| `masks.blotch_amount`, `masks.blotch_size` | very large dark blotches | 0 to 0.5 (0.15), 3 to 8 (5) | colour only |
| `masks.darken_height` | how much of the patches also lowers the height | 0 to 1 (0) | 0 = patches are colour only (a stain film has no relief) |
| `colour.source` | where the colour comes from | `map` or `height_palette` (`map`) | `height_palette` = the COMPARISON version |
| `colour.warm_cool_amount` (new) | how much the orange and blue-grey patches of the COMPARISON colour are used | 0 to 1 (1) | 0 = the single brown palette of round 1 (flat and sepia) |
| `colour.palette`, `colour.palette_cool`, `colour.palette_mid`, `colour.palette_warm` | the palettes (height to colour) measured from the colour map | lists | used only for the COMPARISON version |
| `roughness.base`, `roughness.from_height`, `roughness.board_variation` | roughness | 0.78, 0.20, 0.04 | roughness = base + from_height x (height - 0.5) + a little per board |
| `bake.exact_dots` | ask the photograph for exact dots | 1 | when one picture dot = one source dot, uses 1 sample and a pixel filter of 0.01 so every dot is read at its own centre (the harness default would blur by about a dot) |
| `bake.shrink_samples`, `bake.shrink_filter` | samples and filter when the picture is smaller than the source | 8, 1.0 | e.g. a 4 x 4 area baked at 2508 dots; 1 and 0.01 pick one exact dot per picture dot (used for the debug pictures) |
| `debug.source_unchanged` | switch the arrangement off | 0 / 1 (0) | gives back the uploaded height (the check in section 7) |
| `source.*` | facts about the uploaded maps (file names, row strip starts and ends, stain stamp centres) | | measured, see `research/` |

Special parameters (not settings): `shift` [u, v] slides the pattern by that much of the picture (the slide test); `window` [x, y, size] bakes only a part of a big area, in tiles (for example [1.5, 2, 1] = the tile that starts one and a half tiles from the left and two from the top); `debug_view` = `boards` (a random colour per board; its Height output holds the exact board number), `rows`, `flips` (red = flipped left-right, green = upside down, blue = has a half joint), `landmarks` (which landmark is shown where: Height = number / 16, red = shown, green = painted out), `source_x` / `source_y` (exact: which dot of the source map every dot was taken from); `settings_file`.

---

## 5. Sweep pictures

All sweeps change one setting of the default tile (seed 1) and nothing else, at 512 dots, so the layout stays put and only that setting shows. Only the three that matter most are shown here; the other two are in `sheets/` (`sweep_warp.jpg`, `sweep_row_height.jpg`).

**Stepped joints (`joints.step_share` 0, 0.7, 1):** this is the change that moves the picture furthest from a brick wall.

![stepped joints](sheets/sweep_step_share.jpg)

**Boards per row (2, 3, 4):**

![boards per row](sheets/sweep_boards_per_row.jpg)

**Landmarks (all painted out, default, all shown):** with everything painted out the area has no knots and no recognisable cracks, with everything shown the checker's repeats come back (section 7.3).

![landmarks](sheets/sweep_landmarks.jpg)

What the landmarks are and what a painted-out source map looks like (left: the twelve landmarks circled; right: the map with all of them painted out; the right picture is drawn by `tools/find_landmark_replacements.py` with numpy to show what the nodes do, it is not a Blender bake):

![landmarks](sheets/landmarks.jpg)

---

## 6. How to bake

* **With the project's standard command** (this works: it was run on the final recipe, seed 1, 1254 dots, about 3.5 minutes under load; the result equals the job-driver bake):
  `blender -b --disable-autoexec -t 2 --python lib/bake_harness.py -- recipes/wood_from_displacement/recipe/wood_from_maps_recipe.py OUT_FOLDER --size 1254 --params '{"recipe.seed": 1}'`
  It writes colour.png, height.png (16-bit), roughness.png, metallic.png and normal.png (made from the height, two-neighbour slope, strength 8) and normal_bumpnode.png (a cross-check, not needed).
* **Several pictures in one Blender run:** `tools/run_jobs.py` with a jobs file (examples: `tests/jobs_r2_tiles.json`, `tests/jobs_r2_areas.json`). A job with `"full": true` is the standard bake; otherwise it lists channels. Every job builds the nodes again (about 50 seconds under load), so many small jobs in one list cost mostly build time.
* **The COMPARISON version:** add `"colour.source": "height_palette"` to the parameters; the height and normal are the same as MAIN.
* **A bigger area:** `{"recipe.tiles_across": 4}` with `--size 2508` (about 10 minutes per channel under load) or smaller. **A full-size piece of an area:** add `"window": [1.5, 1.5, 1]` and bake 1254 dots.
* **Speed:** see the table below. The round 2 recipe has about twice the nodes of round 1 and bakes about twice as slowly.

@@SPEED_TABLE@@

---

## 7. Results

@@RESULTS@@

---

## 8. Files in this folder

| Path | What it is |
|---|---|
| `recipe/wood_from_maps_recipe.py`, `recipe/wood_node_kit.py`, `recipe/settings.json` | the recipe, its helper and its settings (audited with `lib/description_audit.py`: passes). `recipe/round1/` holds the round 1 recipe for comparison |
| `outputs/main_seed1..3` | the default tile, all maps (colour, height 16-bit, roughness, metallic, normal) |
| `outputs/comparison_seed1..3` | the COMPARISON colour (the height and normal are copies of the MAIN files of the same seed) |
| `area/` | the 2 x 2 and 4 x 4 areas, the repeated tile, the crops, the exact debug pictures, the switched-off areas |
| `round1/` | the few round 1 results needed for before and after (the 4 x 4 area, the tile pictures, the round 1 score files) |
| `variations/` | the sweep pictures |
| `sheets/` | all the sheets shown in this guide (and `development/`, small pictures of the steps of round 2) |
| `scores/` | `final_scores_round2.json`, `checks_round2.json`, `repeat_tests_round2.json`, `joints_found_round2.json`, `landmarks_replacements.json`, `job_numbers_round2.json` |
| `tools/` | the job driver, the scoring, repeat and check scripts, the sheet makers, the guide filler (each starts with a plain note); `tools/measure_repeats.py`, `analyse_final.py`, `make_sheets.py` and `joint_contact_sheet.py` are the round 1 versions |
| `tests/` | job lists, logs, the earlier recipe's tile baked again for scoring |
| `research/` | the research that came first |
| `build_result_round_1.json`, `build_result_round_2.json` | the structured results of the two rounds |
| `check_look_round_1/`, `check_honesty/` | the two checkers' own folders (not mine) |

---

## 9. Dead ends, failures and weak points (in the order they happened)

**Round 1**

1. **First joints were flat black bars** (they looked drawn). Replaced by a ragged crack with dirt, pebbles and a worn lip.
2. **Rows cut from gap-top to gap-top** put wood against wood at the row boundary; the project's seam measure gave the tile a tiling score of 0.19 and then 0.0, although the half-tile slide test passed. Cutting from gap-middle to gap-middle and laying a dark band over every row boundary hid the cut: tiling score 1.0.
3. **Stain stamps from the map contained knots** (two of the first eight stamps held a knot): the knot came back as a smaller second knot in the same board. The two stamp centres were replaced.
4. **The same-kind score dropped when everything was on** (0.76 with every part against 0.85 with none, seed 1). I lowered the amounts and made the patches colour-only.
5. **Two boards per row scored lower** in round 1 (mean 0.763 against 0.800 for three boards) and repeated more (33 percent near copies against 12). Round 2 went back to two boards per row on purpose, because the look checker judged the three-board layout a brick wall (section 11 says what the numbers do now).
6. **"At most one knot per row" in a bigger area** meant one knot per 4 tiles of row, four times too few per dot.
7. **The "never the same source row as the neighbour" rule was wrong in round 1**: the fallback rows and the knot boards broke it for 19 percent of touching pairs. Round 2 removed the fallback (section 11).
8. **My first board counting in the repeat test was wrong** (dithered colour numbers); now read from the exact 16-bit picture.
9. **A rule in the research notes was mislabelled:** the uploaded normal map equals the two-neighbour slope of the uploaded height at strength 8 (0.004 against 0.03), not a 3 x 3 Sobel filter.

**Round 2**

@@ROUND2_DEAD_ENDS@@

---

## 10. Not tested, and where I am unsure

@@NOT_TESTED@@

---

## 11. Round 2: what the checkers found and what I did

@@ROUND2@@
