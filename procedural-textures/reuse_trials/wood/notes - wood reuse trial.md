# Notes - wood reuse trial

What this file is: the plain-words report of the WOOD reuse trial. The question was "how much of the tools can be used on the other textures
now?". I answered it for wood by building it: a wall of old, weathered boards made from the shared slate layers (taken unchanged from the frozen
snapshot), with only their settings changed, plus the smallest new parts I could not avoid. Everything is in this folder
(`reuse_trials/wood/`, about 64 MB). Written on 20 October.

**Who did what.** The trial was started by an earlier helper, who was stopped part-way (the person switched the helpers to another model). It had
used 6 of the 12 Blender runs and had built the wood turn, CRACKS, KNOTS and the first tuned settings; its last scored bake (1254 dots) had
same-kind 0.437. I checked what it left (it was sound), kept it, and finished: I added the GRAIN layer, retuned, chose the height route, baked the
three final seed sets, ran the proof tests and wrote this. In total **11 of the 12 Blender runs** were used (`blender_runs.log`).

Two words used below. A **layer** is one box in the Shader editor that paints one kind of thing (colour and fade, damage, moss, outline...). The
**bundle** is the eleven numbers the layout box hands to every layer (which board am I on, where on it, how far from its edge...). A **node** is
one small step Blender works out for every dot of the picture.

---

## 1. The short answer

**Wood needs no change to any shared layer.** COLOUR AND FADE, MOSS, DAMAGE, OUTLINE AND SHADOW, COMBINE and the shared slate LAYOUT ran exactly
as they are in the snapshot (the checksums still match after all my runs). Only their settings differ from slate. Four small new parts were needed:

| new part | nodes | why no shared layer could do it |
|---|---|---|
| **WOOD TURN** (`wood_layout.py`), a box between the layout and the layers | 5 | The shared layers lay their long streaks and drips "down the piece". Wood grain runs ALONG the board. Turning the bundle a quarter makes "down" mean "along the board" for every layer, with no change to any layer. |
| **CRACKS** (`cracks.py`), a new paint layer | 95 | DAMAGE's cracks always start at a piece edge, which on a turned board is the board end. Wood splits start anywhere along the grain and taper to a point at both ends. |
| **KNOTS** (`knots.py`), a new paint layer | 78 | No shared layer makes rings. (The reference has four knots.) |
| **GRAIN** (`grain.py`), a new paint layer | 31 of its own, plus 39 borrowed | The shared layers make flat patches and specks, not long thin dry-brush streaks and hairlines. Adding this layer lifted the colour group from 0.33 to 0.64 in one step. It borrows the earlier wood build's "Wood Grain Gain" box **unchanged**. |

The shared slate LAYOUT with wood settings (5 rows, ONE board per row) made the boards: no new layout was needed, only the turn.

**How close is it?** At the like-for-like size (1254 dots), the same-kind score is **0.665, 0.657 and 0.678** for the three seed sets, **mean
0.667** (colour group 0.698). The wood's own earlier recipe, scored the same way, gives **0.606** on its first new tile (colour 0.622); its eight
new tiles had 0.607 to 0.665 as stored. So **the layered wood scores above the earlier recipe**. Two cautions, in section 4: both were tuned
against this same score tool, and I tuned on seed set 1 while looking at it.

**Counted in nodes** (see section 5 for the list):
- Shared, unchanged: **1,718** (LAYOUT 182, COLOUR AND FADE 419, MOSS 419, DAMAGE 439, OUTLINE AND SHADOW 216, COMBINE 28, the seamless-noise helper 15).
- New: **209** (WOOD TURN 5, CRACKS 95, KNOTS 78, GRAIN 31). Borrowed unchanged from the earlier wood build: 39. The recipe's own wiring: 12.
- So **86.9 % of the nodes are shared**, 10.6 % new, 2.0 % borrowed, 0.6 % wiring (1,978 in all).

**Counted in lines of code** (comment lines not counted; `code_lines.json`):
- Reused unchanged: **1,158** (the layer interface and four paint layers and COMBINE 987, plus the shared LAYOUT 171).
- New boxes: **224** (turn 27, CRACKS 74, KNOTS 64, GRAIN 59). Borrowed unchanged: 77.
- Recipe wiring 140 (mostly a copy of the brick and slate recipes), settings 150 numbers (32 lines), tools and tests 511.
- So **84 % of the box code is reused** (1,158 of 1,382).

---

## 2. What was reused, and how

| part | how it was used | what it does on wood |
|---|---|---|
| layer interface (`layer_interface.py`) | unchanged | every box, old and new, is built with it; the new layers have exactly the same sockets |
| LAYOUT | **settings only** | 5 rows of boards, ONE board per row, so each board runs right across the tile with one butt joint where the row's random slide puts it; the band between rows is the dark gap |
| COLOUR AND FADE | **settings only** (run on the turned bundle) | the boards' browns: nine tones from the reference's measured 16-colour palette, with a grey-green and a warm tint. Long flat patches along each board, some paler and darker boards, wide weathered areas |
| MOSS | **settings only, used as rust** | the "lichen discs" are coloured rust-brown and grey-blue, in clouds; the drip, joint and lower-edge preferences are all 0. This is the rust splatter. 21 % of dots are covered |
| DAMAGE | **settings only** | small chips along the long board edges (1.4 % of dots) and a few hairline cracks at board ends. It does little on wood |
| OUTLINE AND SHADOW | **settings only** | the near-black gap between boards (the "joint colour"), a thin dark side outline, slightly darkened edges; the shadow, lip and black drips are off |
| COMBINE | **settings only** | stacks the seven layers (it makes one set of inputs per name in `recipe.stack_order`, so the new layers needed no change there). Its "tone blend" is 0.8 for the height |
| `lib/bake_harness.py`, `lib/texture_compare.py`, `make_normal.py`, `description_audit.py` | as they are | baking, scoring, the normal map at strength 8, the settings check (`settings.json` is 5.7 KB, passes the 8 KB limit) |

**The settings were chosen like this.** I measured the reference once as a guide (`measure_reference_once.py`, `reference_measures.json`).
Numbers taken from the reference or from its stored analysis, and why:
- **Palette** (16 colours, `recipes/wood/analysis/palette16.json`): the nine tone colours. Why: to make the browns match.
- **Board heights and gap width** (surveyor plan: boards 281, 239, 270, 178 and 286 dots, gap 6.8 dots): 5 rows, jitter 0.15, `row_gap` (first 0.0054, then 0.0045 by eye). Why: to size the layout.
- **Strip size** (about 120 x 25 dots, `paint_model.json`): the first streak sizes. Why: first guess for the turn and the patch sizes.
- **Whole-picture shares** (very dark 7.9 %, grey-blue 6.4 %, rust-orange 12.4 %, middle grey 70, mean colour): measured once from `reference/wood/colour.png`. Why: to compare by eye and by number while tuning.
- **Height rule** (straight line from grey 12 to 128) and **normal strength 8**: used for the height-rule box, which was tried and then not used (section 3, part 5), and for the normal map.
- **Not from the reference**: the GRAIN streak numbers (45 and 420 streaks, cuts 0.58 and 0.38, gains 1.8 and 0.55, hairlines 5 and 150, 0.012 and 0.45). They are the earlier wood build's own description numbers (`recipes/wood/description/S1_layout_paint_grain.json`).
- **While tuning I also looked at the score tool's breakdown** (for example its feature-size and spectrum measures) and at the reference's feature-size curve to decide whether features were too long or too short. I never copied a position, a crack, a knot or a blot, and I ran no optimiser; each round was "look, change one or two things, look again".

---

## 3. What was new, and why

1. **WOOD TURN** (5 nodes). It hands the eleven bundle numbers on turned a quarter: new `local_x` is the old `local_y` and the reverse, board width and length swap, and `top_edge_distance` becomes the distance from the board's left end. It also has one setting, **Grain Stretch** (final value 5): it tells the layers the board is 5 times SHORTER than it is, so every pattern they draw on the board's own coordinates (paint patches, specks) comes out 5 times longer along the grain. That is how the shared layers' round patches become long streaks without touching them. It does not change anything read on the picture's own coordinate (the rust discs, the big weathered areas) or on true distances.
2. **CRACKS** (95 nodes). The board is cut across into 4 lanes and along into stretches; each cell rolls its own random numbers (does it hold a crack, where, how long, how wide); the crack wanders a little and tapers to a point at both ends, with a pale fresh-wood lip on one side. No loop over cracks, so the cost does not depend on how many there are. A crack never leaves its cell, so it never crosses a butt joint and the tile repeats.
3. **KNOTS** (78 nodes). An oval with a near-black core, rings of darker and lighter wood, and a faint halo. At most one per "place" along a board. Optional; I kept it because the reference has knots. By eye the rings are too wide and wavy (section 7).
4. **GRAIN** (31 nodes of its own, 39 borrowed, 59 lines). It borrows "Wood Grain Gain" from the earlier wood build, which makes a brightness factor (lighter streaks, darker streaks, hairlines). A paint layer cannot multiply the colour below it, so the layer turns the factor into paint: where the factor is below 1 it paints near-black with that much cover, above 1 it paints pale tan. Its Seed slides the whole pattern; it does not make new random numbers inside the borrowed box. **This was the largest single gain** (colour group 0.330 without it, 0.636 with it, same settings).
5. **Height route** (settings, not new code). COMBINE's built-in "height from brightness" rule is slate's. I tried three routes at 1254 dots on the same colour: the rule at full strength (tone blend 1.0): height group 0.309; the brick trial's HEIGHT RULE box with the wood line (copied, one name changed, `height_rule.py`): 0.371; COMBINE with tone blend 0.8 (a fifth of the real relief kept): 0.430. Tone blend 0.6 gave height 0.552 but the normal group fell to 0.356, and 0.4 was bad (0.279). **Final: tone blend 0.8.** The HEIGHT RULE box is therefore not built in the final recipe (it is only built if `recipe.height_rule` is `wood`).
6. **A soft height bake** (a bake option in `final_bake.py`, not a layer). The reference's height is a little blurred; a shader sees one dot at a time and cannot blur. Blender's own pixel filter can: the height (only) is rendered with a Gaussian filter of width 2 and 8 samples instead of the harness's width-1 box filter with 4 samples. Effect on seed set 1: height group 0.464 (sharp) to 0.556 (width 1.5) to **0.602 (width 2, final)**; overall 0.634, 0.661, **0.665**. The cost: the normal group drops a little (0.569, 0.563, 0.498), because a softer height gives a gentler normal, and the height bake takes about 190 s instead of 90 s. The brick trial did NOT do this, so wood's height and normal numbers are not strictly comparable with brick's.

No shared layer was copied or changed. There is no `*_changed_for_wood.py` file.

---

## 4. Scores, like for like

Every row below:
- is 1254 dots;
- was scored by `lib/texture_compare.py wood` (the "same kind" score, 0 to 1);
- has its normal map made from the height by `make_normal.py` at strength 8 (the wood reference's strength).

All scores are in `final_scores.json` (full per-measure reports inside; each set folder in `final/` has its own `score.json`).

| tile | same-kind (overall) | colour group | height group | normal group | tiling |
|---|---|---|---|---|---|
| **trial, seed set 1** (the one I tuned on) | **0.665** | **0.705** | 0.602 | 0.498 | 0.996 |
| trial, seed set 2 (every seed + 100) | 0.657 | 0.667 | 0.629 | 0.513 | 0.995 |
| trial, seed set 3 (every seed + 200) | 0.678 | 0.722 | 0.593 | 0.546 | 1.000 |
| **trial, mean of the three** | **0.667** | **0.698** | 0.608 | 0.519 | 0.997 |
| **baseline: the wood's earlier recipe, new tile sample_101, normal remade at strength 8** | **0.606** | **0.622** | 0.575 | 0.448 | 0.945 |
| the same tile as stored (its own normal map) | 0.619 | 0.622 | 0.575 | 0.533 | 0.945 |
| the earlier recipe's eight new tiles, as stored (surveyor's figure, `recipes/wood/variations/variation_scores.json`) | 0.607 to 0.665, mean 0.626 | 0.582 to 0.655 | | | |
| the stopped helper's last bake (round 5, seed set 1, before GRAIN) | 0.437 | 0.422 | 0.400 | 0.396 | 0.767 |

**Where the trial is behind the earlier recipe's tile** (seed set 1, `final_scores.json`): the colour feature-size curve is still off (colour
spectrum 0.30 against 0.41), and the normal agreement with the height is 0.00 for both. Everything
else is ahead, most of all the colour edge sharpness (gradient 0.65 against 0.36), the colour spread (0.81 against 0.73), the tiling (0.996
against 0.945) and the height contrast (0.97 against 0.65).

**Two cautions.**
- **The seed matters, and I tuned on seed set 1.** The colour group goes from 0.667 to 0.722 across the three sets. The fair number is the mean. Seed sets 2 and 3 were baked once, after the settings were frozen.
- **Both sides were tuned on this score.** The earlier wood tiles came from a sampler tuned against the same tool (the surveyor already said their 0.626 is optimistic), and I watched the score while hand-tuning. A score above 0.6 does not mean the picture is "as good as the reference". The reference is not a tile of this wood kind in the sense of a score of 1.
- The extras for the record (seed set 1 colour, other heights): sharp height 0.634, Gaussian 1.5 0.661, Gaussian 2 0.665.

**How the score climbed** (seed set 1; colour group is the only meaningful number for a colour-only view; `tuning_story.jpg` shows the pictures):

| step | colour group | note |
|---|---|---|
| round 5, stretch 6, no GRAIN | 0.422 | the stopped helper's last 1254 bake; features 79 dots long against the reference's 24 |
| round 6, stretch 3 | 0.577 | colour only |
| round 8, current settings without GRAIN, stretch 3 | 0.330 | the same settings as the next row, GRAIN switched off |
| round 8, with GRAIN, stretch 3 | 0.636 | |
| round 8, stretch 4 | 0.670 | |
| round 9, stretch 5 (final) | 0.705 | |
| round 9, stretch 4, more tone spread and bleach | 0.620 | worse; not used |

---

## 5. Proof tests (all run and measured; files in `checks/`)

- **Half-tile shift test** (512 dots; `checks_run.py` part 1, measured by `checks_analyse.py`): it slides the picture by half a tile and checks that it equals the plain picture rolled by half its size. Result: **the tile repeats.**
  - Finished colour: average difference 5.2 of 255, and 0.16 % of dots differ by more than 40. A wrongly rolled control gives 34.6 and 33.6 %.
  - Boards: 0.85 and 0.27 %. Edge distance: 0.5 and 0 %. CRACKS mask: 0.74 and 0.45 %. KNOTS mask: 0.28 and 0.01 %.
  - **GRAIN mask: 12.5 and 4.7 %.** This is a larger difference than the others, so I checked where it lies: it is spread evenly over the picture (12.47 away from the old picture edge, 13.45 within two dots of it; no concentration at the edge), and it all but vanishes if both pictures are blurred over 5 dots first (3.1 and 0.0 % against a control of 18.6 and 8.7 %). My explanation, by reasoning and not proven: the grain streaks are about one dot tall at 512 dots, so the renderer samples them at slightly different places in each dot when the picture is slid. I did NOT bake the grain at higher quality to prove it.
  - With 2 tiles across (`recipe.tiles_across` 2): the finished colour repeats too (7.6 and 0.45 %), and it is NOT a copy of itself one base tile over (31.3 and 27.3 %). GRAIN itself repeats once per base tile with 2 tiles, but the other layers make new content, so the whole is new.
- **Seam score** in the like-for-like bakes: 0.996, 0.995 and 1.000.
- **2 x 2 repeat** (`repeat_2x2_wood.jpg`): I looked. No seam is visible. The one-tile repeat of the rust clouds and the knots shows, as it does for any one-tile repeat.
- **Switch-off test** (320 dots; `checks/checks_tables.md`): with a layer's Amount set to 0, the colour changed outside that layer's own mask on 0.000 to 0.008 % of dots, for every layer. Height changed outside the mask on 0.00 to 0.35 % (OUTLINE AND SHADOW 0.35 %, GRAIN 0.11 %). I think the small height differences come from COMBINE's tone rule turning a colour change too small for my colour threshold into a height change above my height threshold (by reasoning; not tested). I did not run the "Seed + 1" test the brick trial ran (it proved nothing there).
- **Snapshot fingerprints**: `sha256sum -c checksums.txt` reports OK for all seven files after all my runs. No cache folder was written into the snapshot.
- **Settings check**: `description_audit.py settings.json --limit-kilobytes 8`: no problems.

**Node counts** (`checks/node_counts.json`; the walk counts each box once):

| box | nodes | kind |
|---|---|---|
| LAYOUT | 182 | shared, unchanged |
| the seamless-noise helper | 15 | shared, unchanged |
| COLOUR AND FADE | 419 | shared, unchanged |
| MOSS | 419 | shared, unchanged |
| DAMAGE | 439 | shared, unchanged |
| OUTLINE AND SHADOW | 216 | shared, unchanged |
| COMBINE | 28 | shared, unchanged (22 with five layers; 28 with seven) |
| WOOD TURN | 5 | new |
| CRACKS | 95 | new |
| KNOTS | 78 | new |
| GRAIN | 31 | new |
| Wood Grain Gain | 39 | borrowed, unchanged |
| the recipe's wiring | 12 | copied pattern |

---

## 6. Does it read as wood? (honest)

**Yes, at a glance, but it reads as a tidy, drawn wood.** `sheet_wood.jpg` and `final_seed_sets.jpg` show:
- old brown boards of different heights, running across the tile;
- a dark gap between boards with a ragged edge, and a thin dark butt joint in every board;
- long fine grain streaks and hairlines, thin cracks with pale lips;
- knots with rings;
- orange-brown and grey-blue splatter like the reference's rust.

All three final tiles read as wood. The earlier recipe's tile has no clear boards at all (only a dotted line where the gaps are), so for "looks like planks" the layered tile is clearly better; for "looks like the reference's weathered, splintered timber" neither is close.

**Next to the reference, or up close, it is clearly weaker:**
- **The boards are too regular.** Every board is a straight, even strip with a uniform black gap. The reference's boards have splintered, ragged edges with tan splinters and splits that run across the board and half-way down it.
- **A butt joint in every board.** The layout needs one end per board per tile (a board with no end would restart its own coordinates at the tile edge and show a seam). The reference has none.
- **The dark smudge clouds are missing.** The reference has large, soft, dark stains on tan wood. Mine has flat coloured patches and small rust discs. (Rust is 16 to 19 % of the dots against the reference's 12 %: a little too much.)
- **The grain looks hatched.** It is made by thresholded noise, so the streaks have a digital, repeating look. The reference's grain flows around the knots.
- **The knots are rings drawn on top.** Too wide and wavy; the grain does not bend round them.
- **The rust and the knots repeat** in the 2 x 2 picture, as any one-tile repeat does.

---

## 7. What is missing to make it better

1. **Splintered board edges.** The layout's ragged edge setting only chips inward by a few dots. A "splinter" layer, or a copy of DAMAGE with chips that run along the grain and can be long and pale, would give the tan slivers.
2. **Soft dark stains.** MOSS's flat discs cannot make a soft cloud. A "STAIN" mode (or its drip stretch and fringe settings, which I left at 0) could be tried.
3. **Grain that bends round knots.** Needs the grain to be drawn on bent coordinates; a new, bigger piece of work.
4. **Better knots.** More rings, closer together, a darker disc, and a crack across; and fewer or smaller halos.
5. **Boards without butt joints,** or joints that look real (a pale gap, a crack across the board).
6. **Colour feature sizes.** The colour spectrum score is only 0.30. I have not tried a second, finer layer of grain at a different scale.
7. **A less blunt height route.** The soft Gaussian height bake is a bake option; it should become a documented bake step (and the normal strength could rise a little to make up for it).
8. **Tune on three seed sets at once** (I tuned on one).
9. **Take DAMAGE out of the stack** if wood does not need it: its 439 nodes work out for every dot but cover 1.4 %.

---

## 8. Failures (recorded as they happened)

(First half, by the stopped helper; from its notes and logs.)
- **Run 1:** Grain Stretch was multiplied instead of divided, so the patterns came out SHORTER, the opposite of what was wanted. Fixed in round 2.
- **MOSS as rust, first tries:** the inventory's look check had found too few rust discs on wood; the helper's rounds 1 to 3 raised the coverage and the clustering by settings (I have only its sheets and logs, not the first pictures).
- **Round 5 (1254 dots):** same-kind 0.437, with a tiling score of 0.767. When I took over I looked at the wrap: a crack core lay exactly on the picture's top edge with its pale lip on the other side, which the seam measure counts as a jump. By reasoning, that is chance and not a real seam (the 2 x 2 picture of the final tile shows none); but I did not test that tile.
- **Run 6 was cut short** (the helper was stopped): only one of four planned views was baked.

(Second half, mine.)
- **Stretch 2 and 1.5 look like camouflage** (round 7, by eye): short patches with no long grain. I kept the longer stretch and added the GRAIN layer.
- **Without GRAIN the colour group was 0.330** (round 8): the long flat patches alone have no fine structure; feature sizes were wrong (colour scale 0.01, gradient 0.00).
- **Stronger grain scored worse:** 250 hairlines and stronger light streaks gave colour 0.576 against 0.636.
- **More tone spread, bleach and stain scored worse:** 0.620 against 0.670.
- **Height routes:** the wood HEIGHT RULE box 0.371 against 0.430 for tone blend 0.8 (round 8); tone blend 0.4 gave height 0.279 and normal 0.116.
- **The soft height lowers the normal group** (0.569 to 0.498 on seed set 1).
- **The grain's half-tile numbers looked bad** (12.5 and 4.7 %); I analysed them (section 5) and believe they are renderer noise, but have not proved it with a higher-quality bake.
- **Disk:** the folder reached 86 MB (over the 80 MB limit) in the middle; I deleted the tuning pictures of rounds 1 to 9 (their sheets, logs and view lists are kept) and made `tuning_story.jpg`. It is 64 MB now.
- **A scratch helper in the first half** (`set_settings.py`) failed once when I asked it to change a setting that was not yet in `settings.json`; it refuses and says so. Nothing was written.

---

## 9. What I did not test, and what I am unsure of

- **The GRAIN half-tile difference** is explained by reasoning only (section 5).
- **Roughness and metallic** were baked but not checked against anything (the reference has none). Metallic is 0; roughness is about 0.84 on average.
- **Height checks:** I looked at the height picture of seed set 1 against the reference's height by eye (gaps dark, rust patches lower, grain visible); I scored it, but did not look at the other two.
- **The 2 x 2 area of new content** (`recipe.tiles_across` 2) passed the half-tile test but I did not look at or score it.
- **GRAIN with tiles across above 1** repeats once per base tile (written in its notes); I did not look at it.
- **The WOOD HEIGHT RULE box** was baked only in the stopped helper's round 3 (640 dots, not scored) and in my round 8 height view, which was scored once.
- **Seed Plus 1 and the independence checks of the brick trial** were not repeated.
- **No second wood reference** exists, so I could not test whether the settings are over-fitted to this one reference.
- **Timings** were taken while another helper was baking at the same time: colour about 80 s, soft height about 190 s, roughness about 70 s, metallic 2 s per 1254 set (5.9 minutes for a full set).
- **Unsure:** how much of the 0.06 gain over the earlier recipe is real and how much is from tuning on the same score; the stopped helper's early rounds I did not rerun, so their small effects (for example the first tone and bleach settings) are as it left them.

---

## 10. Files in this folder

- **The recipe:**
  - `wood_recipe.py`: the recipe the harness loads. It imports the shared layers ONLY from the snapshot and refuses to run if any came from elsewhere. It keeps `shift`, `debug_view`, `recipe.tiles_across`, `recipe.stack_order` and `recipe.height_rule`.
  - `settings.json`: all wood settings (150 numbers, 5.7 KB).
  - `wood_layout.py` (WOOD TURN), `cracks.py`, `knots.py`, `grain.py`, `height_rule.py` (copy from the brick trial, not used in the final settings).
- **Pictures:**
  - `sheet_wood.jpg`: reference | earlier recipe tile | this trial; the same three enlarged (400 x 400 dots); and the boards and each layer's mask.
  - `final_seed_sets.jpg`: the three final tiles and the earlier recipe's tile.
  - `repeat_2x2_wood.jpg`: the trial's tile laid 2 x 2.
  - `tuning_story.jpg`: eight pictures from the stopped helper's round 5 to the final settings.
  - `look_*.jpg` (the first helper's looks at the reference and the earlier tile), `rounds/*_sheet*.jpg` and `rounds/r5_wrap_top_bottom.png`.
- **Final bakes:** `final/seeds_1`, `seeds_2`, `seeds_3`: colour, 16-bit height, roughness, metallic, normal (strength 8), `score.json`, `bake.json`. Also `final/extra_seeds_1_height_sharp` and `extra_seeds_1_height_gauss_1_5` (height only).
- **Scores:** `final_scores.json`, `baseline_sample_101/` (colour, height and the normal remade at strength 8).
- **Tests:** `checks/` (`checks_tables.md`, `half_tile_results.json`, `switch_off_results.json`, `node_counts.json`, the half-tile, mask and switch-off pictures), `code_lines.json`.
- **Tools:** `run_views.py`, `final_bake.py`, `checks_run.py`, `checks_analyse.py`, `final_scores.py`, `score_pair.py`, `score_views.py`, `set_settings.py`, `make_look_sheet.py`, `make_pictures.py`, `count_code.py`, `measure_reference_once.py` and `reference_measures.json`.
- `blender_runs.log`: every Blender start. There were **11**: 6 by the first helper (five tuning rounds and one cut short), then 5 mine (a tuning round at 640 dots, two at 1254, the final bake and the checks).
- `trial_result.json`: the structured result.

**To bake it again** (from `proc-work`):

`blender -b --disable-autoexec -t 2 --python reuse_trials/wood/final_bake.py -- reuse_trials/wood/final 1254 '{"seeds_1": {"_height_filter": ["GAUSSIAN", 2.0, 8]}}'`

then `python3 -I reuse_trials/wood/final_scores.py`.

The plain harness (`blender -b --disable-autoexec -t 2 --python lib/bake_harness.py -- reuse_trials/wood/wood_recipe.py OUT --size 1254 --normal-reference wood`) should also work, because it loads the recipe the same way, but **I did not run it**. It would make a sharp height (no soft filter) and the harness's own normal maps.
