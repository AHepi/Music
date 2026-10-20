# Notes - gravel reuse trial

What this file is: the plain-words report of the GRAVEL reuse trial. The question was "How much of the tools can be used on the other textures
now?". I answered it for gravel by building it: a gravel tile made from the shared slate layers (taken unchanged from the frozen snapshot) with only
their settings changed, plus the smallest new parts I could not avoid. Everything is in this folder (`reuse_trials/gravel/`, about 50 MB).
Written on 20 October.

Words used (one word for each thing): a **dot** is one dot (pixel) of a picture; a **node** is one small step Blender works out for every dot;
a **layer** is one box that paints one kind of thing (colour and fade, damage, ...); the **bundle** is the eleven numbers a layout hands to every
layer ("which stone am I on, how far from its edge, where on it ..."); a **mask** is a grey picture of where a layer paints (white = it paints);
the **same-kind score** is the project's tool `lib/texture_compare.py` (0 = as different as another surface, 1 = the same kind), with a **colour
group**, a **height group**, a **normal group** (the normal map is the picture that tells a game engine which way each dot of the surface faces)
and a **tiling** part; a **seed set** is one choice of random seeds for all layers (a different seed set = a different random piece of gravel).

---

## 1. The short answer

**No shared layer had to be changed, but the shared layers alone do not make gravel.** COLOUR AND FADE, DAMAGE, OUTLINE AND SHADOW, COMBINE and the
layer interface ran exactly as they are in the snapshot (the checksums of all seven files still match). Only their settings differ from slate.
But a gravel needs a layout of stones, and the soil between them needs its own paint, so four small new parts were needed:

| new part | nodes | why no shared layer could do it |
|---|---|---|
| **GRAVEL LAYOUT** (`gravel_layout.py`) | 564 | Makes the eleven bundle numbers for a heap of angular stones with soil between. The slate LAYOUT makes rows of slates and cannot make stones (by reading; I did not bake it). Mostly a copy of `lib/contrib/stone_tools.polygon_stones`, changed to hand out where the dot is on its stone, to stack three sizes of stones, to turn each grid by its own angle and to roughen the edges (section 3). |
| **SOIL** (`soil.py`), a new paint layer with the same sockets as the others | 170 | The soil lies in the GAPS. MOSS and DAMAGE only paint on a piece (they multiply by `piece_mask`), COLOUR AND FADE lies under the gap paint, and OUTLINE AND SHADOW can only paint the gap one flat colour. SOIL paints lumps, crumbs and the shadow next to each stone. |
| **FACETS** (`facets.py`), a new paint layer with the same sockets | 109 | A broken stone has flat faces; faces that look up at the light are lighter. COLOUR AND FADE paints flat patches that do not know which way a face looks, and round 1 gave flat grey blocks. |
| **GRAVEL HEIGHT RULE** (`gravel_height_rule.py`), a small box after COMBINE | 12 | Makes the height from the finished colour by the gravel reference's rule (a colour mix). COMBINE's built-in rule is slate's. It turned out to be only a small gain (section 4). |

**Counted in nodes** (the number in each box, counted by `checks_run.py` part 4; `checks/node_counts.json`, `checks/node_share.json`):
- Shared, unchanged: 1,111. That is COLOUR AND FADE 419, DAMAGE 439, OUTLINE AND SHADOW 216, COMBINE 22 and the seamless-noise helper box 15. (MOSS, 419 nodes,
  was tried and taken out of the stack, so it is not built and not counted.)
- New: 855. That is GRAVEL LAYOUT 564, SOIL 170, FACETS 109 and the height rule 12.
- The recipe's own wiring is 10 nodes, copied from the slate recipe.
- So **56 % of the nodes are shared** (57 % without the height box). Without the layout it would be 79 %: the layout is the single biggest new part,
  bigger than any shared layer. Brick was 84 % shared; the difference is the layout.

**Counted in lines of code** (comment lines not counted; `checks/line_counts.json`, from `count_lines.py`):
- Reused unchanged: 749 lines (the interface helper, COLOUR AND FADE, DAMAGE, OUTLINE AND SHADOW and COMBINE); MOSS (189) was tried and is not in the stack.
- New boxes: 295 lines (layout 130, SOIL 83, FACETS 54, height rule 28).
- Recipe wiring: 132 lines, mostly a copy of the slate recipe.
- Settings: 33 lines (103 settings).
- Tools and tests: 638 lines (scripts that bake, score, check and draw; most of them copies of the brick trial's tools with the names changed).

**How close is it?** At the like-for-like size (1254 dots) over three seed sets the trial scores **same-kind 0.622 on average** (0.589 to 0.658; colour group 0.669).
The gravel's own earlier small recipe, scored the same way, has **0.412 on average over its eight new tiles** (0.375 to 0.466; colour group 0.274) and 0.380 for its
first new tile. So the layered gravel is ahead by about 0.21 on this score. Section 4 has the full table. Whether it LOOKS better is section 6: it is a different look,
and next to the reference it is still clearly weaker.

---

## 2. What was reused, and how

| part | how it was used | what it does on gravel |
|---|---|---|
| layer interface (`layer_interface.py`) | unchanged | every box, old and new, is built with it; SOIL and FACETS have exactly the sockets of the shared layers |
| COLOUR AND FADE | **settings only** | the stones' own colours: eight measured stone colours sorted dark to light plus a ninth rust-orange one (the palette); a per-stone base tone (a bell around a dark middle, so most stones are near black); flat patches and specks inside each stone (`streak_contrast` 2, `speck_amount` 1.2); a lean towards blue-grey for most stones; **rust stones through the setting-only trick** described below; weak big patches that cross stones |
| DAMAGE | **settings only** | small dark and grey-blue chips and pits along stone edges (the break colours are set close to the stone colours so the chips are subtle). It paints about 6 % of the dots. |
| OUTLINE AND SHADOW | **settings only, used as "paint the soil flat"** | its `joint_colour` is the soil's flat base colour, painted in every gap. Its outline, shadow band, lip, drips and spill are all set to 0, because the reference stones have no dark outline. Only a faint edge darkening is left on. |
| COMBINE | **settings only** | stacks the five layers (it makes one set of inputs for every name in `recipe.stack_order`, so SOIL and FACETS needed no change there); `tone_blend` 0; base roughness 0.85 |
| MOSS | unchanged, **tried as rust, then out of the stack** | in rounds 1 to 5 it was tried as rust (orange tones, patches on stones). It gave a few orange flecks and no rusty stones (the settings are in `rounds/settings_moss_as_rust_tried.json`). It was not worth its 419 nodes, so it is not in the final stack. |
| LAYOUT (slate) | not used | it makes rows of slates. Not baked for gravel. |
| `lib/bake_harness.py`, `lib/texture_compare.py`, `make_normal.py`, `description_audit.py` | as they are | baking, scoring, the normal map at strength 10 (the gravel reference's strength), the settings check (`settings.json` is 4.3 KB, passes the 8 KB limit) |

**Rust stones by settings only.** COLOUR AND FADE paints a stone with the palette colour at its tone step. Two settings made orange stones without any new code:
the top palette colour is a rust orange, and a small share of stones (`outlier_share` 0.06) are pushed far up the steps (`outlier_size` 7), so they land on the orange.
The "warm tint" setting (a lean towards a colour of matched lightness) is also rust orange. It works, but weakly: a few stones come out orange and, under FACETS' pale paint,
some come out a dusty pink (section 6).

**How the settings were chosen.** I looked once at the reference and used the stored earlier measurements of it as a guide (section 10 lists exactly which numbers and why).
Then I hand-tuned over nine Blender runs of "look, change one or two things, look again". No optimiser, no tracing, nothing per stone.

---

## 3. What was new, and why

1. **GRAVEL LAYOUT** (564 nodes). It makes the eleven bundle numbers. How:
   - Three grids of squares, one stone per square: a **big** grid (about 100 squares, each about 127 dots wide), a **middle** one (578 squares, about 52 dots) and a **small** one (3,016 squares, about 23 dots).
   - Each stone is the part of its square where five straight-edge tests are all true (five faces with random directions and distances). Size, turn, a small off-centre shift and which squares are empty are random numbers made from the square's number, so the tile repeats.
   - A dot takes the stone of the biggest grid it lies on, so middle and small stones fill the gaps and are partly hidden behind the big ones (a heap). A stone half hidden counts the edge of the stone on top as its own edge.
   - **Each grid is turned by its own angle** (about 24, 45 and -33 degrees, written as whole-number steps so the tile still repeats exactly). Round 1 had all three grids upright and the soil gaps formed a plaid of straight lines (`rounds/round_1/sheet_a.jpg`); turning the grids removed it (`rounds/round_2/sheet_a.jpg`).
   - **Ragged edges**: a seamless noise pushes every stone edge in or out by roughly a tenth of its radius (setting 0.18). Without it the stones were clean geometric polygons (round 4: same-kind 0.472; round 6, with ragged edges and some other changes: 0.641).
   - The soil next to a stone is pushed DOWN a little over 6 dots (`base_height`); SOIL reads that dip and paints the shadow from it.
   - Stone share is about 65 % of the dots (measured on the layout's own stone mask in round 5; the reference: 68 %). The share of stone that survives "opening" with a disc is within 0.01 to 0.11 of the reference's at the five sizes tested, a little short in the middle (details in section 10).
   - Known limit: a stone cannot cross the border of its square (it would be cut flat), and the soil's "distance to a stone" only knows the stone of the dot's own square.
2. **SOIL** (170 nodes): five flat soil tones cut from one slow noise (two darker, two lighter, one pale tan, about 12 dots across), tiny dark-grey and pale-grey crumbs (about 5 dots), and two flat steps of dark brown shadow next to stones. Reads only Vector, Tile Count, `gap_mask`, `base_height`, its own Seed and settings. Amount 0 switches it off through the shared `finish_layer`. It is a cousin of the brick trial's GRIME (same "cover share" thresholds) but not the same layer: GRIME's soot and mortar mottle do not fit gravel, and the shadow part (the inventory's "part 3") is new here.
3. **FACETS** (109 nodes): three straight cut lines across every stone (random direction and place, wobbled by a fine noise so they are not ruler straight). A face that looks up is painted lighter, a face that looks down darker, each covering the stone paint only 30 %, so every stone keeps its own tone. Stones narrower than 15 dots get none. Reads only the stone's own coordinates.
4. **GRAVEL HEIGHT RULE** (12 nodes): height = (267.15 red + 91.48 green + 210.5 blue) / 255 - 17.7 (screen values of the finished colour), mixed with COMBINE's real relief at 0.9 to 0.1. Same idea as the brick trial's height box.

No shared layer was copied or changed. There is no `*_changed_for_gravel.py` file.

---

## 4. Scores, like for like

Every row below:
- is 1254 dots;
- was scored by `lib/texture_compare.py gravel` (the same-kind score, 0 to 1);
- has its normal map made from the height by `make_normal.py` at strength 10 (the gravel reference's strength).

The scores are in `final_scores.json` (the full reports, every measure, are in it too). The earlier recipe's tiles were scored by `baseline_scores.py`.

| tile | same-kind (overall) | colour group | height group | normal group | tiling |
|---|---|---|---|---|---|
| **trial, seed set 1** (the one I tuned on) | **0.658** | **0.721** | 0.567 | 0.469 | 1.000 |
| trial, seed set 2 (every seed + 100) | 0.618 | 0.655 | 0.543 | 0.462 | 1.000 |
| trial, seed set 3 (every seed + 200) | 0.589 | 0.630 | 0.495 | 0.441 | 1.000 |
| **trial, mean of the three** | **0.622** | **0.669** | 0.535 | 0.457 | 1.000 |
| trial seed set 1 with COMBINE's own height rule (no new height box) | 0.643 | 0.721 | 0.446 | 0.612 | 1.000 |
| **baseline: the gravel's earlier recipe, new tile 1** (normal remade at strength 10) | **0.380** | **0.242** | 0.407 | 0.470 | 0.974 |
| **baseline: mean of its eight new tiles** | **0.412** | **0.274** | 0.455 | 0.481 | 0.984 |

(The earlier recipe's first tile as stored, with its own normal map, scored 0.372; the eight tiles run from 0.375 to 0.466. The earlier recipe is a 2.3 KB list of rules painted by another painter, `recipes/gravel/`; its score of the same kind of tile is the fair comparison.)

**The seed matters.** The overall score goes from 0.589 to 0.658 across the three seed sets, and the colour group from 0.630 to 0.721. Within that, the feature-size measure of the colour
("colour spectrum") goes 0.528, 0.386, 0.230. I tuned on seed set 1 only, so it is the flattering number; the fair number is the mean.

**How the score grew while I tuned** (seed set 1, 1254 dots; `rounds/scores_of_the_1254_probes.json`): 0.472 (round 4, polygon stones with straight edges) -> 0.641 (round 6, ragged edges, orange top tone, patchier paint) ->
0.566 (round 7, a change that went the wrong way, see failures) -> 0.658 (round 8, final settings).

**The height rule: how much does the new box add?** One setting, `height_rule.blend`, mixes the colour rule with COMBINE's real relief (`rounds/round_6/height_blend_scores.json`, scored on the round 6 picture):
blend 0 = 0.458, 0.3 = 0.479, 0.5 = 0.506, 0.7 = 0.549, 0.8 = 0.594, 0.85 = 0.629, **0.9 = 0.641**, 0.95 = 0.629, 1 = 0.623, and COMBINE's own rule (`tone_blend` 1, the slate rule) = 0.590 there.
In the final bake the same comparison on seed set 1: new box 0.658, COMBINE's own rule 0.643 (height group 0.567 against 0.446, but normal group 0.469 against 0.612).
So **COMBINE's built-in rule is almost good enough for gravel: the new height box is a gain of 0.015 and could be left out.** (Brick needed it much more: 0.538 against 0.654.)

**What each layer adds (the ladder, `score_ladder.py`, `ladder/ladder_scores.json`, `ladder_strip.jpg`).** Seed set 1, 1254 dots; the layout is always there:

| step | same-kind | colour group |
|---|---|---|
| 1. COLOUR AND FADE only (stones everywhere, no soil) | 0.199 | 0.103 |
| 2. + OUTLINE AND SHADOW (the soil painted one flat brown) | 0.204 | 0.137 |
| 3. + DAMAGE | 0.213 | 0.154 |
| 4. + FACETS (new) | 0.329 | 0.332 |
| 5. + SOIL (new) = the finished recipe | 0.658 | 0.721 |

This is the honest answer to "how much of the shared recipe can make gravel": the shared layers (COLOUR AND FADE, OUTLINE AND SHADOW and DAMAGE, stacked by COMBINE), on a gravel layout, get to **0.21**. The two small new layers
take it to 0.66: FACETS +0.12 and SOIL +0.33. DAMAGE adds only +0.01 here. (The ladder's order matters: the flat soil of steps 2 to 4 is a big featureless area, which the score punishes hard.)

**Where the trial is still behind the reference** (seed set 1, from `compare_details.py` and the full report in `final_scores.json`):
- the feature-size curve of the height ("height spectrum" 0.18): my height has about 5 times too much detail at the finest scale (3 dots) and somewhat too little at 45 to 220 dots;
- the agreement between the normal map and the height (0.00): the reference's height was blurred 0.5 dot before its normal was made; a shader sees one dot at a time and cannot blur;
- the height's spread of values (0.43), because the reference has more very dark and very bright heights;
- the colour's feature-size curve (0.53): too much at about 380 dots across, too little at about 220 and 45.

**Where it is equal or ahead:** colour-size scale (1.00), colour orientation (0.82), colour spread (0.71), how closely the height follows the colour (0.99), the seam (1.00).

---

## 5. Proof tests (all run and measured; files in `checks/`)

- **Half-tile shift test** (512 dots; `checks_run.py` part 1, measured by `checks_analyse.py`; `checks/checks_tables.md`). It slides the picture by half a tile and checks that it equals the plain picture rolled by half. Result: **the tile repeats**.
  - Finished colour: average difference 3.9 of 255, 0.13 % of dots differ by more than 40. A wrongly rolled control gives 36 and 41 %.
  - Edge distance: 0.85 and 0.002 %. FACETS mask: 1.5 and 0.01 %.
  - Random colour per stone: 3.6 and 2.2 % (stone borders on the one-dot staircase).
  - **SOIL mask: 9.4 and 9.7 %** (control 80 and 49 %). That is a lot, so I looked where those dots lie (`seam_location_check.py`, `checks/seam_location.json`): 10.6 % in a 4-dot band along the old tile edge against 9.6 % everywhere else. They are spread over the many one-dot edges of the 2-dot crumbs (at 512 dots a crumb is 2 dots wide, so almost every dot is an edge and a rounding difference flips it). Not a seam. The same check on the finished colour: 0.17 % at the edge against 0.13 % elsewhere.
  - With 2 base tiles across: it repeats again (finished colour 5.9 and 0.24 %), and the picture is NOT a copy of itself one base tile over (37 and 40 %), so it is new content.
- **Seam score** in the like-for-like bakes: 1.00 for all three seed sets.
- **2 x 2 repeat** (`repeat_2x2_gravel.jpg`): I looked. No seam is visible. The repeat of the pale stones and the dark clusters shows, as any one-tile repeat does.
- **Independence test** (320 dots; `checks/checks_tables.md`):
  - **Amount 0**: switching a layer off changes the colour outside its own mask on 0 % of dots for COLOUR AND FADE, DAMAGE and OUTLINE, 0.001 % for SOIL and 0.097 % for FACETS.
  - The share of dots whose colour changes when a layer is switched off: COLOUR AND FADE 58 %, FACETS 46 %, SOIL 41 %, OUTLINE (the flat soil) 39 %, DAMAGE 6 %.
  - Height outside the mask is 0.02 to 1.2 % (FACETS 1.2 %). I think this is the height rule again: a colour change too small to count as a colour change (under 2 of 255) becomes a height change over the threshold 0.002, because the rule multiplies it by about 2. That explanation is by reasoning; I did not test it.
  - Roughness outside the mask for OUTLINE AND SHADOW is 20.7 % (and SOIL 2.5 %). By reading the code: OUTLINE's shadow roughness and lip roughness are written whether or not the shadow and lip are painted (I set their darkness and brightness to 0), and SOIL adds roughness to every soil dot, painted or not. It is a quirk of each layer, not a leak between layers. Roughness is not scored and I left it.
  - **Seed + 1** rows show changes outside the old mask (FACETS 2.4 %, DAMAGE 4.7 %, SOIL 2.0 %). That is expected and not a leak: they are measured against the OLD seed's mask while the new pattern lies in new places. I did not bake the new-seed masks, so these rows prove nothing either way.
  - Changing the layout seed changes 95 % of the dots, as it must.
- **Node counts**: section 1. **Snapshot fingerprints**: `sha256sum -c checksums.txt` reports OK for all seven files after all my runs; no cache folder was written into the snapshot.
- The big pictures of the half-tile and independence tests were deleted afterwards to save disk (the tables, `half_tile_results.json`, `independence_results.json` and `seam_location.json` stay). To redo them run `checks_run.py` again.

---

## 6. Does it read as gravel? (honest)

**Yes at a glance** (`sheet_gravel.jpg`, `final_seed_sets.jpg`, `repeat_2x2_gravel.jpg`): dark blue-grey and black angular stones in an orange-brown crumbly soil, a few rust-coloured stones, big and small stones mixed. All three seed sets read as gravel. Next to the earlier recipe's tile it looks more like the reference
(ragged lumpy stones, orange soil with crumbs instead of clean polygons on flat brown).

**Next to the reference, or up close, it is clearly weaker:**
- **Flat "cut-paper" stones.** The reference stones have many small, soft, ragged facets and a lit rim. Mine have a few big flat faces with hard edges, and the big stones have large plain areas.
- **Stair-step edges.** At 1254 dots the ragged outline of the big stones and of the paint patches inside them shows a one-dot staircase.
- **Soil.** It is mottled like granite, with dark specks. The reference soil is made of round orange lumps with a light top and many tiny round grey crumbs.
- **Spacing.** The stones are spread more evenly than in the reference, where they touch and gather in clusters; the three grids can still be felt as a faint regularity in the pale stones' positions.
- **Pink stones.** The rust-orange stones look dusty pink when FACETS' pale paint lies over them (seed sets 2 and 3 show them most).
- **Height.** It follows the colour the way the reference's does, so dark stones are LOW and the orange soil is HIGH: not a real relief (`maps_seeds_1.jpg`). Real relief only (blend 0) scores 0.458 against 0.641.
- **No size-linked colour.** The reference's big stones are bluer and its small ones browner; mine are not (the layout's `row` number is not read by any shared layer).

---

## 7. What is missing to make it better

1. **Softness at the dot level.** The reference was blurred a little; mine has one-dot hard edges, which is why the height has about 5 times too much detail at 3 dots and the normal-height agreement is 0. A bake at twice the size shrunk back, or 16 samples instead of 4, would soften the edges. Not tried.
2. **Soil lumps with a lit top.** Compare the lump noise with itself shifted down a few dots and paint the difference lighter. A small change to SOIL (my own file).
3. **Touching stones.** Look at the four nearest squares (or nine) instead of only the dot's own, so stones can cross square borders and the soil shadow knows its real nearest stone. About four times the layout's nodes.
4. **Facets that follow the real faces.** The layout knows each stone's face directions but the bundle has no slot to hand them out; FACETS draws its own random cuts. A twelfth bundle number (or a declared link) would do it.
5. **Rust stones that are really orange.** Keep FACETS off the orange stones, or give COLOUR AND FADE a second palette.
6. **Size-linked colour.** Let COLOUR AND FADE read `row` (a small change to a copy of the shared layer, or a setting).
7. **A size spread like the reference's** (a few very big stones, many small ones) rather than three fixed grids.
8. **Leave the height box out** unless the height group matters more than the normal group.

---

## 8. Failures (recorded as they happened)

- **Round 1: a plaid.** With three upright grids the soil gaps formed straight lines across the picture. Fixed by turning each grid.
- **MOSS as rust, four times** (rounds 1, 2, 3 and 5, with bigger clumps in round 5): only a few orange flecks; dropped.
- **Round 4: straight-edged polygon stones** looked geometric and scored 0.472. Ragged edges fixed most of that.
- **Round 7 went backwards** (0.566 against 0.641): I calmed the crumbs, grain and big patches and darkened the soil. The height lost contrast and the normal tilt score fell from 0.50 to 0.12. I went back to round 6's crumbs and grain (round 8). Lesson: the normal group is very sensitive to the strength of small edges.
- **Round 9: no paint tongues** (`fade_direction` 0) looked the same and scored 0.009 lower, so I kept round 8's settings.
- **A mean that was wrong**, found before I reported it: my first `final_scores.py` counted the COMBINE-rule set among the three seed sets. Fixed; the table above is the corrected one.
- **640-dot views scored with the compare tool are NOT like for like** (the brick trial's lesson, kept): I used 512 and 640 dots for looking only. Every score in this report is from a 1254-dot bake.
- **Disk:** the folder reached 66 MB; I deleted the big pictures of tuning rounds, scratch scores and the half-tile and independence tests to stay under 80 MB. The scripts that scored them need the pictures again if re-run.

---

## 9. What I did not test, and what I am unsure of

- **Tuned on one seed set.** The score of each round was seed set 1 only; the final seed sets 2 and 3 were never tuned on and score 0.04 to 0.07 lower.
- **Roughness and metallic** were baked and looked at (`maps_seeds_1.jpg`) but not checked against anything (the reference has none). Metallic is 0.
- **The height blend sweep** was done on the round 6 picture, not on the final tile. The best blend (0.9) was then used for the final bake. A sweep on the final tile might choose a slightly different number.
- **The soil shadow** (the dip next to each stone) was not looked at separately, so I do not know how often it is missing where a neighbouring square's stone is the nearest one.
- **The 2 x 2 area of new content** (`recipe.tiles_across` 2) passed the half-tile test, but I did not look at it or score it.
- **Other picture sizes** (512, 2508) were not baked for scoring. The sizes are in tile units, so the look should hold.
- **The shared slate LAYOUT** with gravel settings: not baked. I believe it cannot make stones.
- **MOSS** was tried with only one meaning (rust).
- **DAMAGE** paints 6 % of the dots and adds 0.009 to the score; I did not look for a better meaning for it.
- **The ladder is one order only** (and the flat soil of steps 2 to 4 makes the later steps look bigger than they are).
- **Normal map** was not tried in a 3D render.
- **Timings** were taken while another helper was baking: about 80 to 100 seconds per full-size picture, about 4.8 minutes for one set (colour, height, roughness, metallic).
- **Not done:** the LATER test (realistic moss and damage over the painted colour); it was not started.

---

## 10. Numbers taken from the reference (guide only), and why

I never traced the reference and wrote no per-stone list. The reference was used like this:
1. **Looked at by eye**, once at the start and then at the same 400 x 400 corner next to my own pictures.
2. **Stored measurements from the earlier gravel work** (`recipes/gravel/scores/measurements.json`, made by that build's own analysis; I did not repeat it):
   - the 8 stone colours and 8 soil colours (the palettes): they became the stone palette (sorted dark to light) and set the soil colours;
   - the stone share 0.678 and the "left after opening with a disc" curve at radii 8, 16, 24, 32, 48 (0.598, 0.516, 0.407, 0.322, 0.109): only to choose the grid sizes and radii (`measure_stones.py` compares my stone mask with them; mine: 0.66 share and 0.56, 0.45, 0.30, 0.28, 0.12 at 640 dots in round 5, so the middle sizes are a little short);
   - the direction of the light (lightness falls going down a big stone): only the sign of `fade_direction`.
3. **Four numbers of the height rule** (267.15, 91.48, 210.5, -17.7) from `recipes/gravel/description/S_v4.json`, "maps"/"height" (the earlier build's fit of how the reference height was made from its colour; `recipes/gravel/analysis/derivation_ceiling.py`). Why: the reference maps were made that way.
4. **A simple measure of the reference colour picture** (`measure_colours.py`, run once on it and again on my own pictures): mean stone and soil colour and the 10th, 50th and 90th brightness percentiles. It showed my first stones too light (median 64 against 48) and set `tone_centre`; the soil's mean colour (94, 65, 45) set the soil colours.
5. **The compare tool's own facts** (`compare_details.py`: how big the steps between neighbouring dots are, and how much detail sits at each feature size, for the reference and for my picture). I used them to decide by hand which of crumbs, grain, big patches and edge roughness to turn up or down. Nothing was fitted.
6. **A small sweep of one setting**: `height_rule.blend` (nine values) and `gravel_layout.ragged_edges` (0.12, 0.18, 0.25 looked at); no sweep over many settings.

Never used: `analysis/stones_found.json`, the traced descriptions.

---

## 11. Files in this folder

- **The recipe:**
  - `gravel_recipe.py`: the recipe the harness loads. It imports the shared layers ONLY from the snapshot and refuses to run if any came from elsewhere. It keeps `shift`, `debug_view`, `recipe.tiles_across`, `recipe.stack_order`, and adds `recipe.height_rule`.
  - `settings.json`: all gravel settings (4.3 KB).
- **New boxes:** `gravel_layout.py`, `soil.py`, `facets.py`, `gravel_height_rule.py`.
- **Pictures:**
  - `sheet_gravel.jpg`: reference | the earlier recipe's tile 1 | this trial's tile (seed set 1) with scores; the same enlarged at a 400 x 400 corner; then the stones (layout) and the mask of each layer.
  - `final_seed_sets.jpg`: the three final tiles side by side.
  - `repeat_2x2_gravel.jpg`: the tile laid 2 x 2.
  - `ladder_strip.jpg`: the same corner at each step of the ladder.
  - `maps_seeds_1.jpg`: colour, height, normal and roughness of seed set 1.
- **Final bakes:** `final/seeds_1`, `seeds_2`, `seeds_3`: colour, 16-bit height, roughness, metallic, normal (strength 10) and `score.json`. `final/seeds_1_combine_rule`: only the height made by COMBINE's own rule, and its `score.json`.
- **Scores:** `final_scores.json`, `baseline_scores.json`, `baseline_sample_01/` (colour and score), `ladder/ladder_scores.json`, `rounds/scores_of_the_1254_probes.json`, `rounds/round_6/height_blend_scores.json`.
- **Tests:** `checks/` (`checks_tables.md`, `half_tile_results.json`, `independence_results.json`, `seam_location.json`, `node_counts.json`, `node_share.json`, `line_counts.json`, the layer masks in `masks/`).
- **Tuning record:** `rounds/` (round 1 to 9: sheets and logs; most big pictures deleted), `look/` (the reference and the earlier tile, looked at once at the start), `blender_runs.log` (every Blender start: **12**, the most allowed).
- **Tools:** `run_views.py`, `final_bake.py`, `final_scores.py`, `checks_run.py`, `checks_analyse.py`, `seam_location_check.py`, `score_height_blends.py`, `score_probe.sh`, `score_ladder.py`, `baseline_scores.py`, `compare_details.py`, `measure_stones.py`, `measure_colours.py`, `contact_sheet.py`, `make_gravel_sheet.py`, `make_maps_sheet.py`, `seed_sets_sheet.py`, `count_lines.py`, `count_node_share.py`.
- `trial_result.json`: the short structured answer.

**To bake it again** (from `proc-work`):

`blender -b --disable-autoexec -t 2 --python reuse_trials/gravel/final_bake.py -- reuse_trials/gravel/final 1254 '{"seeds_1": {}}'`

then `python3 -I reuse_trials/gravel/final_scores.py` (it makes the normal maps and, if needed, the baseline's pictures again). The plain harness (`blender ... --python lib/bake_harness.py -- reuse_trials/gravel/gravel_recipe.py OUT --size 1254 --normal-reference gravel`) should also work, because the recipe is loaded the same way, but **I did not run it**.
