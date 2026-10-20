# 00 Inventory - which tools fit which surface

What this file is: the answer to "how much of the tools can be used on the other textures now?". It lists every tool built so far (the shared tools,
the cookbook, the per-surface builds and the slate made of separate layers), says in one plain sentence what each does, and says for brick, wood,
metal, mud and gravel whether it works **as is**, needs **settings only**, **needs a new layout**, **needs a new layer**, **needs code changes**, or is
**not useful**, with the evidence. Then it gives one concrete TRIAL PLAN per surface (how to make the layout bundle, which layers to run with which kind
of settings, what small new layer is truly needed, what to measure once from the reference as a guide, and the BASELINE to compare with like for like).
Written by the reuse surveyor on 20 October. Reading plus five small checks (section 3); no trial was baked. Nothing outside `reuse_trials/` was changed.

---

## 1. The short answer

**The layered machinery carries over; the layouts mostly do not.** On every one of the five surfaces the same core runs with no change to its code:
the layer helper and its fixed interface, the four paint layers (COLOUR AND FADE, DAMAGE, MOSS, OUTLINE AND SHADOW), COMBINE, the baking tool and the
"same kind" score. What changes from surface to surface is the LAYOUT (the box that says "which piece am I on, and where on it") and one or two small
new layers for things no shared layer can paint.

| surface | the layout bundle | shared layers | small new layers truly needed | how much is new code |
|---|---|---|---|---|
| **brick** | the slate LAYOUT with brick settings (12 rows of 4), or the earlier quick brick layout with 4 not 6 bricks per course | all four, settings only | **GRIME** (soot that crosses bricks AND mortar; mottled mortar) | one small layer (about 40 to 60 nodes) |
| **wood** | the slate LAYOUT with board settings (5 rows of 1) plus a **10-node "turn"** so the layers' up-down runs ALONG the grain (proved by eye today) | all four, settings only, except cracks | **CRACKS** that start anywhere along the grain (DAMAGE's cracks start only at a piece edge); KNOTS and GRAIN only if needed | the turn plus one small layer |
| **metal** | **new**: bars and plate panels, creases as the gaps (about 100 to 150 nodes) | all four, settings only, with new meanings (MOSS = rust, DAMAGE = chipped paint) | **RIVETS**; EDGE LIGHT (the bright upper-left edge) only if the first round shows it is missing | a new layout and one or two layers |
| **mud** | **new**: no pieces in the picture, so the pieces are the small flat earth **clods** (a seamless cell layout, no gaps) | COLOUR AND FADE settings only; MOSS as puddle water (unsure); DAMAGE maybe; OUTLINE off | **RUTS**; STONES (borrowing `lib/contrib/stone_tools.py` unchanged); PUDDLES only if MOSS-as-water fails | a new layout and two or three layers: the most new code |
| **gravel** | **new**: pieces = stones (a copy of `lib/contrib/stone_tools.polygon_stones` that also hands out each stone's coordinates and size), gap = soil | COLOUR AND FADE, DAMAGE, OUTLINE settings only; MOSS off or a few rust spots | **GRIME** (the soil texture and its shadow next to stones); FACETS only if needed | a new layout (mostly a copy) and one shared layer |

How much of the tool list fits each surface (counted by `inventory_checks/count_verdicts.py` from the 52 rows of section 4; "fits" = as is or settings only):

| | brick | wood | metal | mud | gravel |
|---|---|---|---|---|---|
| as is | 28 | 29 | 28 | 29 | 28 |
| settings only | 6 | 5 | 5 | 4 | 5 |
| needs a new layout | 0 | 0 | 1 | 1 | 1 |
| needs a new layer | 0 | 0 | 0 | 0 | 0 |
| needs code changes | 8 | 9 | 7 | 7 | 8 |
| not useful | 10 | 9 | 11 | 11 | 10 |
| **fits now (as is or settings only)** | **34 of 52** | **34 of 52** | **33 of 52** | **33 of 52** | **33 of 52** |

The counts treat a reading guide and a paint layer alike, so read them as "how much of the shelf is usable", not as "how close the trial will look".
The useful measure for the look is the first table: on every surface the paint layers and COMBINE run by settings alone (two exceptions: DAMAGE's cracks
do not suit wood, and mud has no joints for OUTLINE AND SHADOW to draw); what is new is one layout (metal, mud, gravel) and one or two small layers.

(The "needs a new layer" row is 0 because the new layers are not tools on the list: they are the missing pieces, named in the table above.
"Needs code changes" is mostly small: copying the slate recipe and its tests and changing the recipe path and the layer names.
"Not useful" is mostly the per-surface painter generators, tracing tools and Geometry Nodes helpers: a different route from the layered recipe, and the
generators are what each trial is compared WITH.)

Five things found today that the trials need to know (evidence in section 3):
1. The frozen snapshot of the shared layers builds in Blender from `reuse_trials/shared_layers_snapshot/layers` with no change (all six boxes).
2. **Turning the bundle a quarter makes the shared paint run along wood grain**, with no layer change (look check sheet).
3. **On brick, three settings remove the pointed "slate tongues"** (`fade_direction` 0, `fade_length` = `streak_width`, `mottle_tallness` 1). The 05
   Lessons guide (section 8) concluded that brick needs a new paint layer or a new "streak shape" setting, because pointed shapes stayed with
   `fade_direction` 0. Reading the code and the look check say otherwise: `fade_direction` 0 does remove the tongues (they are multiplied by it); the
   shapes that stayed are the mottling patches, whose height follows `fade_length` and whose width follows `streak_width` (in that test 0.06 tall against
   0.024 wide, 2.5 times taller). With `fade_length` equal to `streak_width` they come out round. No new layer or setting is needed for that.
4. **MOSS and DAMAGE only paint on pieces** (both multiply by `piece_mask`), and COLOUR AND FADE is always under the gap paint. So anything that must
   cross the gaps (brick soot over mortar, soil between stones) needs a whole-surface layer: that is the one shared new layer, GRIME.
5. **Trap:** importing the snapshot writes a Python cache folder (`__pycache__`) INTO the snapshot unless the trial sets `sys.dont_write_bytecode = True`
   before the import. It happened in my first check; I deleted the folder I had made and the checksums of all seven files still match.

---

## 2. Words used (one word for each thing)

* **tile**: the square picture that repeats; **dot**: one picture dot; **tile units**: sizes as a share of the tile (at 1254 dots, 0.008 = 10 dots).
* **piece**: one brick, board, plate, bar, clod or stone; **gap**: the mortar, joint, crease or soil between pieces.
* **layer**: one box of the recipe with its own settings, seed and mask (for example MOSS). **LAYOUT**: the box that makes the pieces.
* **bundle**: the eleven numbers LAYOUT hands to every layer for every dot (which piece, where on it, how far from its edge, gap or piece, bare relief).
* **turn**: handing the bundle over rotated a quarter, so that "down the piece" means "along the board".
* **setting**: one named number or colour of a layer, like `moss.coverage`. **seed**: the number that picks one random pattern.
* **same-kind score**: `lib/texture_compare.py`, "is it the same kind of surface?" from 0 to 1, with four groups: colour, height, normal, tiling.
  The **colour group** is the part that does not depend on how the height map was made.
* **painter generator**: the first builds' way of making a surface: thousands of flat coloured shapes photographed from above, driven by a description file.
* **baseline**: the surface's own earlier small recipe and its new tiles, which a trial must be compared with.

---

## 3. What I checked for this inventory (today), and what each check showed

All in `reuse_trials/inventory_checks/` (each file says at the top what it does). One Blender run at a time, `-t 2`.

| check | what it did | result |
|---|---|---|
| snapshot fingerprints | `sha256sum -c checksums.txt` before and after my runs | all seven layer files OK both times |
| `build_check.py` (7 s) | imports the frozen layers from the snapshot; builds every box with default settings; builds `lib/contrib/stone_tools.polygon_stones` inside an empty layout box; builds the wood build's "Wood Grain Gain" group | all six boxes build (LAYOUT 307 nodes, COLOUR AND FADE 419, DAMAGE 439, MOSS 419, OUTLINE AND SHADOW 216, COMBINE 19); MOSS has the one declared link "Damage Mask"; `polygon_stones` builds (166 nodes) and gives mask, outline, face, three random numbers, inside distance, but NOT the stone's own coordinates or size; the wood grain group builds unchanged (39 nodes, Vector in, Gain out). Result file `build_check.json` |
| the cache-folder trap | the first import wrote `__pycache__` into the snapshot's `layers` folder | deleted it (it was mine; the folder had only the seven `.py` files before); every later run sets `sys.dont_write_bytecode = True` first; checksums still OK |
| `range_clamp_check.py` (5 s) | builds the frozen LAYOUT with `joint_width` 0.016, above its listed highest value 0.01 | the value is KEPT as given, both on the box and on a copy of the box in a recipe. So a brick mortar of 20 dots can be set through the slate LAYOUT's settings. Not checked in a bake whether the picture uses it in full. Result `range_clamp_check.json` |
| `look_check_recipe.py` + `look_check_run.py` (68 s for six 512-dot colour views) | the frozen layers on a quick board layout (plain and turned) and on a brick layout of 12 courses of 4 | picture `look_check/look_check_sheet.jpg` (and a 2 x zoom, `zoom_wood_and_brick_all_layers.jpg`). Wood: plain bundle = upright streaks (wrong); turned bundle = long flat patches along the boards (right). Brick: the earlier settings give pointed patches; the three settings above give round flat patches. In "all layers": rust-coloured lichen discs appear on the wood but far too few; the only crack seen starts at a board end; brick moss reads teal on red (its olive tones were never changed) |
| re-scoring the baselines (7 to 8 s each) | `python3 -I lib/texture_compare.py SURFACE recipes/SURFACE/variations/FIRST_TILE` | the five overall scores equal the stored ones to the last digit; the group scores are in each plan below. Files `baseline_scores/*.json` |
| reading | which bundle numbers each shared layer reads (a text search of the frozen files) | nobody reads `row`; `gap_mask` is read only by OUTLINE AND SHADOW; `top_edge_distance` only by MOSS and OUTLINE; `base_height` by MOSS (damp spots) and COMBINE. MOSS and DAMAGE multiply their mask by `piece_mask` |

---

## 4. Every tool, what it does, and whether it fits each surface

Verdicts: **as is** (use it unchanged), **settings only** (unchanged code, new numbers), **needs a new layout**, **needs a new layer**,
**needs code changes** (a copy with a few lines changed, never an edit of the original), **not useful** (for the layered trials).
"Not tried" means the verdict comes from reading, not from a bake.

### 4A. Shared tools in `lib/`

| tool | what it does | brick | wood | metal | mud | gravel | evidence |
|---|---|---|---|---|---|---|---|
| `lib/bake_harness.py` | Turns any recipe into flat colour, height, roughness, metallic and normal pictures by photographing a square from straight above. | **as is** | **as is** | **as is** | **as is** | **as is** | Ran today (look check); the slate layers and the brick reuse were baked through it. Slate layers at 1254 dots: about 3 minutes for colour, height and roughness. |
| `lib/recipe_tools.py` | Small helpers to add and link nodes and make node groups, plus seamless noise and seamless cells. | **as is** | **as is** | **as is** | **as is** | **as is** | Every shared layer sits on it; build check today. |
| `lib/texture_compare.py` (+ its anchors file) | The "same kind of surface?" score and its four groups, with a side-by-side sheet. | **as is** | **as is**. The old wood new tiles were tuned on it, so their score is optimistic | **as is** | **as is**, but weak on mud: also score against the other five references as a control | **as is**. Quote the as-baked number | Re-scored the five first new tiles today: identical to the stored numbers. |
| `lib/pixel_compare.py` | The "same picture, dot for dot?" measures and tiers. | **as is**, only to show a new tile is not a copy | **as is**, the same | **as is**, the same | **as is**, the same | **as is**, the same | Every made-up tile of all six builds is tier "none" (final reports), by design. |
| `lib/description_audit.py` | Checks that a description file is a short list of numbers, not a picture in disguise. | **as is**, on the trial's settings file | **as is**, the same | **as is**, the same | **as is**, the same | **as is**, the same | Reading: a layered recipe has no description, only a settings file of plain numbers and colours (slate's is 1.7 KB). Not run today. |
| `lib/sweep_tools.py` + `lib/make_strip.py` | Bakes small squares of one setting at several values and joins them into a labelled strip. | **as is**, with a one-line function that builds the trial recipe with one setting changed | **as is**, the same | **as is**, the same | **as is**, the same | **as is**, the same | Reading only (35 + 31 lines): it needs a group with a Vector input, which every layered recipe has. Not run today. |

### 4B. Helpers in `lib/contrib/`

| tool | what it does | brick | wood | metal | mud | gravel | evidence |
|---|---|---|---|---|---|---|---|
| `builder.py` | "Write nodes like a list of sums": add, multiply, map range, ramps, seamless noise and cells, a brick-grid helper. | **as is** | **as is** | **as is** | **as is** | **as is** | The layer helper is built on it; build check today. |
| `stone_tools.py` | Seamless random stones: one faceted polygon stone per grid cell (`polygon_stones`) or Voronoi stones (`stone_layer`), with mask, facet brightness and random numbers. | **not useful** | **not useful** | **not useful** | **as is**, inside a new STONES layer (mask and facet brightness are enough) | **needs code changes**: a copy that also returns each stone's centre coordinates and size, so a LAYOUT can make `local_x`, `local_y` and piece sizes | Build check today: builds inside an empty layout box made by the layer helper (166 nodes); the outputs it gives are listed in section 3. |
| `hp_tools.py` | Painted-look helpers: streaky seamless noise and cells, warped coordinates, palette ramps, padded photographs, a periodicity check. | **as is**, building blocks for GRIME (streaky soot) | **as is**, building blocks if a CRACKS or GRAIN layer is written | **as is**, streaky noise if MOSS drips are not enough for rust streaks | **as is**, warp and streaky noise inside RUTS | **as is**, inside GRIME for the soil | Reading only; not run today. |
| `layout_tools.py` | A Geometry Nodes group that places one point per brick, slate, plank or plate on a wrapping tile. | **not useful** | **not useful** | **not useful** | **not useful** | **not useful** | The layers need eleven numbers for every dot, not a cloud of points. |
| `relax_tools.py` | A Geometry Nodes group that pushes overlapping points apart on a wrapping tile. | **not useful** | **not useful** | **not useful** | **not useful** | **not useful** | Only for a real-geometry route; on gravel that route lowered the same-kind score from 0.362 to 0.173 (gravel final report, "geometry_route"). |
| `gn_tools.py` | Helpers to build Geometry Nodes groups and photograph real geometry from above. | **not useful** | **not useful** | **not useful** | **not useful** | **not useful** | The layered route is shader nodes only; all six builds found real geometry did not help when the reference maps were made from the colour. |
| `periodicity_test.sh` | The half-tile test: bakes a recipe, bakes it again slid by half a tile, compares, with a wrong-roll control. | **as is** | **as is** | **as is** | **as is** | **as is** | Reading; the slate layers' own `tests/half_tile_layers.py` is the fuller version (below). |

### 4C. The slate made of separate layers (`recipes/slate_layers/`; the trials import the layer files from the frozen snapshot)

| tool | what it does | brick | wood | metal | mud | gravel | evidence |
|---|---|---|---|---|---|---|---|
| `interface/interface.md` | The fixed contract: the eleven bundle numbers, the four outputs of every layer, sizes in tile units, seamless rules, declared links, setting names. | **as is** | **as is**, with the bundle turned (`local_y` along the grain) | **as is** (pieces = bars and panels) | **as is** (pieces = clods) | **as is** (pieces = stones, gap = soil) | The brick reuse ran on it unchanged; look check today; no shared layer reads `row`. |
| `layers/layer_interface.py` | Makes the empty layer box with the fixed sockets, and the helper for sums, seamless noise, per-piece random numbers and the Amount-0 off switch. | **as is** | **as is** | **as is** | **as is** | **as is** | Build check today, from the snapshot. |
| `layers/layout.py` (the slate LAYOUT) | Makes rows of pieces with random widths, leaning joints, rounded and chipped edges, and hands out the bundle. | **settings only**: 12 rows of 4, joint 0.016, row gap 0.0148 (not baked yet) | **settings only**: 5 rows of 1 piece, plus the 10-node turn in the recipe (not baked yet) | **needs a new layout** | **needs a new layout** | **needs a new layout** | Range check today: values above a control's listed range are kept. |
| `layers/colour_and_fade.py` | The bottom paint: a tone per piece, tongues and tall mottling patches on the piece's own coordinates, specks, big bleached and damp patches across pieces, palette rounding for flat paint. | **settings only**: the three tongue-removing settings (look check) | **settings only**, on the turned bundle (look check) | **settings only**: steel blue-greys, patches 1.45 times taller than wide (not tried) | **settings only**: one earth tone per clod plus dry and wet areas (not tried) | **settings only**: one tone per stone; `fade_direction` -1 = lit from the top (not tried) | Look check sheet; reading the code. |
| `layers/damage.py` | Flakes along edges (mostly the lower edge and corners), pits, scratches, cracks from an edge, bites, broken corners; sinks the relief. | **settings only**: pale sandy chips at edges and corners (brick reuse, look check) | **needs code changes**: its cracks always start at a piece edge (on turned boards: at the board end, look check), wood cracks start anywhere along the grain; or a new CRACKS layer. Chips: settings only | **settings only**: chipped paint at bar edges in bare-steel colours, rust pits, two long scratches (not tried) | **settings only**: dark crumbly rims on clod edges (not tried, unsure) | **settings only**: pale flakes at stone edges, pits as rust spots (not tried) | Look check zoom; reading. Confined to pieces. |
| `layers/moss.py` | Growth: flat clumps gathered by rules (drips from the upper edge, joints, lower part, low spots, a big patch gate) and round lichen discs in colonies; can avoid or seek damage. | **settings only**: little or none (the brick reference shows no moss); if kept, change its olive tones (teal on red in the look check) | **settings only**: moss off; lichen discs in rust browns = the rust splatter (look check: they appear, too few) | **settings only**, as RUST: drips down from upper edges, along bar edges, clumped by panel, `damage_attract` = rust in chipped paint (not tried) | **settings only, unsure**: as puddle WATER (rules off, big gate on), lichen discs as small stones; may need a new PUDDLES layer | **settings only**: off, or a few rust spots | Reading: confined to pieces; its clump noise is read on piece coordinates. |
| `layers/outline_and_shadow.py` | The drawing: dark gaps, thin side outline, stepped shadow band under each piece's upper edge, pale lip on its lower edge, edge darkening; small relief. | **settings only**: gap = mortar colour, thin dark ring, the lip used as a DARK lower rim; the mortar stays flat (texture comes from GRIME) | **settings only**: dark gaps, thin outline, no shadow band, no lip (look check) | **settings only** for half: creases and the shadow under horizontal bars; the bright upper-left edge and the shadow right of vertical bars need EDGE LIGHT | **not useful**: mud has no joints (Amount 0, or a 1-dot crack between clods) | **settings only**: gap colour = soil base colour, thin rim, no shadow band, no lip (stones have no dark outline) | Brick reuse sheet; look check; reading: the shadow and lip belong to each piece's own upper and lower edge. |
| `layers/combine.py` | Stacks the layers (colour over colour by mask), adds heights and roughness, one metallic number, mixes height with paint brightness (`tone_blend`). | **as is** (any layer names in `recipe.stack_order`) | **as is** | **as is** for colour, height and roughness; steel-versus-rust metallic per dot would need a code change (not scored: the reference has no metallic map) | **as is** | **as is** | Reading: it makes inputs for every name in the stack order. |
| `recipe/slate_recipe.py` | Wires LAYOUT, the layers, the declared links and COMBINE; settings order; debug views; half-tile shift; `tiles_across`. | **needs code changes**: copy it, swap the LAYOUT, add new layers | **needs code changes**, the same plus the turn | **needs code changes**, the same | **needs code changes**, the same | **needs code changes**, the same | The brick reuse recipe and my look check recipe are both copies of its wiring. |
| `recipe/make_controls_table.py` | Writes the one-page controls table from the layer files. | **needs code changes** (the trial's layer list) | **needs code changes** | **needs code changes** | **needs code changes** | **needs code changes** | Reading. |
| `tests/half_tile_test.py`, `tests/half_tile_layers.py` | Prove the recipe and every layer repeat exactly at the tile edge (half-tile slide, wrong-roll control, 2 x 2 area). | **needs code changes**: the RECIPE line and the layer names; the trial recipe must keep the `shift`, `debug_view` and `recipe.tiles_across` parameters | **needs code changes**, the same | **needs code changes**, the same | **needs code changes**, the same | **needs code changes**, the same | Reading: `RECIPE = ... slate_recipe.py` is written in each file. |
| `tests/independence_full.py` | Proves the layers are independent (Amount 0 and Seed + 1 per layer; nothing may change outside the layer's own mask except declared links). | **needs code changes** (RECIPE line, layer list) | **needs code changes** | **needs code changes** | **needs code changes** | **needs code changes** | Reading. |
| `tests/bake_tools.py` | Bakes many single views (colour and exact height) of any recipe in one Blender run. | **as is** | **as is** | **as is** | **as is** | **as is** | The brick reuse bakes used it. |
| `tests/layout_statistics.py` | Measures the slate layout (counts, widths, gap share) next to the reference's numbers. | **needs code changes** (courses, bricks per course, mortar share) | **needs code changes** (board heights, gap width) | **needs code changes** (bars, panels) | **needs code changes** (clod sizes) | **needs code changes** (stone sizes, stone share) | Reading. |
| `integration/colour_character.py` | Measures the shares of olive, tan and very dark dots of a slate picture (to set coverage settings by hand). | **needs code changes** (soot, mortar) | **needs code changes** (cracks, rust) | **needs code changes** (rust, dark stains) | **needs code changes** (water, stones) | **needs code changes** (soil, stone) | Reading: the colour rules are slate's. |
| `integration/make_normal.py` | Normal map from a 16-bit height with a whole-number slope strength, wrapping at the edges. | **as is** (strength 6) | **as is** (8) | **as is** (5) | **as is** (9) | **as is** (10) | Strengths from each build's proof of how its maps were made. |
| `ladder/make_ladder_table.py` | Scores the "what each layer adds" bakes and draws one sheet. | **needs code changes** (reference name, rungs) | **needs code changes** | **needs code changes** | **needs code changes** | **needs code changes** | Reading. |
| `controls_sweeps/` (slate strips) | Pictures of what each setting of each layer does (on slate). | **as is** for reading what a setting does | **as is**, the same | **as is**, the same | **as is**, the same | **as is**, the same | 40-odd strips on disk; new strips for a surface need the sweep tools above. |
| `reuse/brick_layers_recipe.py` + `reuse/settings_round_2/` | The earlier test: the same layers on a quick brick layout (40 nodes, 53 settings), plus one settings-only round. | **needs code changes**, tiny: the starting point; `columns` 4 is already a parameter, the two mortar shares are constants to turn into settings; then round 2 "b1" plus the three paint settings | **needs code changes**: a template for a board layout (the look check made one) | **not useful**, except as a wiring template | **not useful**, the same | **not useful**, the same | Its score against the brick reference: 0.194 overall, colour 0.152 (`reuse/score_against_brick/score.json`). |
| `05 Recipe` and `05 Lessons - slate in layers` | How the layered slate was made, the order to build, the traps. | **as is** (but see finding 3: the tongue remark is corrected here) | **as is** | **as is** | **as is** | **as is** | Reading. |

### 4D. The per-surface builds (`recipes/<surface>/`)

| tool | what it does | brick | wood | metal | mud | gravel | evidence |
|---|---|---|---|---|---|---|---|
| the painter generators (`generator/*_generator.py` and their layer files) | Draw a surface as thousands of flat coloured shapes from a description file and photograph them. | **not useful**: a different route; it is the BASELINE | **not useful**, the same | **not useful**, the same | **not useful**, the same | **not useful**, the same | Reading; their new tiles are the baselines in section 5. |
| the proof of how the maps were made (`analysis/derivation_ceiling.py` and the 04 guides) | Shows each reference's height is the brightness of its colour (curve or straight stretch, small blur) and its normal the slope at a whole-number strength. | **settings only**: `combine.tone_blend` and normal strength 6 | **settings only** (8) | **settings only** (5) | **settings only** (9) | **settings only** (10) | Final reports, "derivation_ceiling". |
| measured summary numbers (palettes, shares, sizes, spreads; files listed in each plan) | Numbers measured once on each reference as a whole. | **as is**: read once as a guide | **as is**, the same | **as is**, the same | **as is**, the same | **as is**, the same | They are general character, not positions of single things. |
| per-element lists and traced descriptions (`layout_clean.json`, `rivets_found.json`, `cracks_fitted.json`, `ruts_*.json`, `stones_found.json`, the M and L descriptions) | Positions and outlines of single bricks, rivets, cracks, ruts, stones and patches of the reference. | **not useful**: using them would be tracing, which the trials must not do | **not useful**, the same | **not useful**, the same | **not useful**, the same | **not useful**, the same | House rules. |
| tracing tools (wood `merge_trace.py`, `trace_tools.py`; metal and gravel trace scripts) | Cut a reference picture into flat patches and write their outlines. | **not useful** | **not useful** | **not useful** | **not useful** | **not useful** | Tracing is forbidden for the trials. |
| the samplers (`sample_description.py`, `sampler.py`) | Write new painter descriptions from measured ranges and a seed. | **not useful**: they write painter descriptions (their measured ranges are the useful part, row above) | **not useful** | **not useful** | **not useful** | **not useful** | Reading. |
| wood `generator/wood_shaders.py` ("Wood Grain Gain") | A seamless group of thin dry-brush streaks and hair-thin lines (Vector in, a brightness factor out). | **not useful** | **as is**, inside a new GRAIN layer, only if the turned colour layer's patches are not enough | **not useful** | **not useful** | **not useful** | Build check today: builds unchanged, 39 nodes. |
| the `04 Recipe` and `04 Lessons` guides and the checkers' answers | Each build's full story, measured numbers, traps, corrections. | **as is** (reading) | **as is** | **as is** | **as is** | **as is** | Read for this inventory. |

### 4E. The cookbook (`cookbook/`)

| tool | what it does | brick | wood | metal | mud | gravel | evidence |
|---|---|---|---|---|---|---|---|
| `06 Cookbook - start here` | Front page: words, which guide for what, the results table. | **as is** (reading) | **as is** | **as is** | **as is** | **as is** | It still says the 05 slate guides are not written; they are now. |
| `06 Guide - baking and checking maps` | Getting maps out of Blender, what each score means, 17 blind spots. | **as is** | **as is** | **as is** | **as is** | **as is** | Read before trusting any number. |
| `06 Guide - descriptions - analyse, describe, generate, compare` | The fit-and-trace method, the ladders, tracing against procedural. | **as is**, only its "measure first" and "ladder" parts | **as is**, the same | **as is**, the same | **as is**, the same | **as is**, the same | The trials do not fit descriptions. |
| `06 Guide - geometry nodes, curves, modifiers and physics` | Real geometry photographed from above. | **not useful** | **not useful** | **not useful** | **not useful** | **not useful** | The layered route is shader nodes. |
| `06 Guide - pattern makers` | Noise, Voronoi, Wave, White Noise and others: what each makes, settings, traps. | **as is** (for GRIME) | **as is** (for CRACKS) | **as is** (for RIVETS) | **as is** (for RUTS) | **as is** (for GRIME) | Reading. |
| `06 Guide - relief - height, bump, displacement and normal maps` | How height and normal were made from colour; real relief against colour-made height. | **as is** | **as is** | **as is** | **as is** | **as is** | Decides `tone_blend`. |
| `06 Guide - seamless tiles and coordinates` | The donut trick, whole-number layouts, the half-tile test. | **as is** | **as is** | **as is** | **as is** | **as is** | Every new layer and layout must follow it. |
| `06 Guide - shapers` | Map Range, Color Ramp, Math, Mix: turning soft greys into flat painted steps. | **as is** | **as is** | **as is** | **as is** | **as is** | Reading. |
| `06 Guide - the painted look` | Flat patches, palettes, outline widths, ragged edges, grain. | **as is** | **as is** | **as is** | **as is** | **as is** | Reading. |
| `06 How to start a new surface - checklist` | The six Lessons merged into one ordered checklist. | **as is**, sections 0 and A (measure first); B to G are the painter route | **as is**, the same | **as is**, the same | **as is**, the same | **as is**, the same | It mentions the layered bundle once. |
| `06 Check - what was checked and fixed` | The independent check of the cookbook. | **as is** (reading) | **as is** | **as is** | **as is** | **as is** | Reading. |

---

## 5. The trial plans, one per surface

### 5.0 Rules every trial follows (the same for all five)

1. **Own folder**: `reuse_trials/<surface>/`. Copy what you need into it; never edit the originals, `lib/`, `reference/` or the snapshot.
2. **Imports**: put `reuse_trials/shared_layers_snapshot/layers` first on `sys.path` and set `sys.dont_write_bytecode = True` BEFORE the import
   (otherwise a cache folder appears inside the snapshot). Check `sha256sum -c checksums.txt` (run inside the snapshot folder) at the end.
3. **Recipe**: a copy of `recipes/slate_layers/recipe/slate_recipe.py`'s wiring with the surface's LAYOUT, keeping the `shift`, `debug_view` and
   `recipe.tiles_across` parameters, so copies of the half-tile and independence tests run with one line changed. New layers follow the interface
   (bundle in; Mask, Colour, Height, Roughness out; own seed; Amount 0 = exactly nothing; `finish_layer`). COMBINE takes any layer names in `recipe.stack_order`.
4. **Settings by hand**, measured guesses from the reference as a guide (palette, shares, sizes, measured ONCE); hand rounds of "look, change one or two
   settings, look again"; never an automatic optimiser, never per-piece lists.
5. **Bakes**: tune with colour-only views at 512 to 768 dots (about 10 to 20 seconds per view, look check); the like-for-like bake at 1254 dots with all maps
   (`blender -b --disable-autoexec -t 2 --python lib/bake_harness.py -- RECIPE.py OUT --size 1254 --normal-reference SURFACE`; about 3 to 5 minutes, so run it in
   the background and wait on its log). One Blender at a time. Check `df -h /` first; keep looking-pictures as JPEG; delete superseded bakes.
6. **Like-for-like score**: `python3 -I lib/texture_compare.py SURFACE OUT`. Report the overall score AND the colour group next to the baseline tile below.
   The colour group is the fair part: the baseline tiles made their height from their colour with the reference's own rule, a layered recipe from its
   relief mixed with paint brightness. For the fairest height and normal groups set `combine.tone_blend` to 1 (height = brightness of the finished
   colour, the reference's way) and say so; also report your chosen value. Bake at least **three seed sets** (change every layer's seed): the seed alone moves
   the score by 0.03 to 0.07 (slate layers: 0.701 to 0.769 colour group over five seed sets). Compare only bakes of the same size.
7. **Prove it**: the half-tile test and the independence test (copied, one line changed), and the "what each layer adds" ladder. Write down failures.

### 5.1 One new layer that four surfaces can share: GRIME

No shared layer can paint across the gaps: MOSS and DAMAGE stop at `piece_mask`, and COLOUR AND FADE is under the gap paint. Brick needs soot that
runs over bricks AND mortar and a mottled mortar; gravel needs a textured soil; metal and mud may want dark stains over everything. One small layer, written
once in `reuse_trials/new_layers/grime.py`, would serve all four:
* reads only `Vector`, `Tile Count`, `gap_mask`, `piece_mask`, `base_height` (so it is independent of every other layer);
* part 1, **clouds**: seamless noise stretched up-down (a setting for how much taller than wide), cut into two or three flat dark tones by thresholds set
  from a cover share (the way COLOUR AND FADE turns a share into a threshold), painted anywhere;
* part 2, **gap mottle**: fine seamless noise cut into three flat tones, painted only where `gap_mask` is 1 (mortar, soil);
* part 3, **low-spot darkening** (for gravel): darker where `base_height` is low inside the gap (the stone layout makes the soil low next to stones);
* stacked last (above OUTLINE AND SHADOW). About 40 to 60 nodes. Use `hp_tools` streaky noise or `LayerBuilder.tileable_noise`.

### 5.2 BRICK

**Start from** `recipes/slate_layers/reuse/brick_layers_recipe.py` and `reuse/settings_round_2/views.json` (b1: redder bricks, light mortar). Copy both into
`reuse_trials/brick/`.

**What the reference shows, and which layer makes it**

| visible feature (from the brick 04 guides) | layer | settings or new |
|---|---|---|
| running courses: 12 courses, about 4 bricks each, lengths that vary (pitch 313.5 dots, spread 59), course pitch 101.9 dots | LAYOUT | settings (or the quick layout with 2 constants changed) |
| wide pale mortar, 22.1 % of the tile (head joints 20.4 dots, bed joints 18.6 dots), pale greys and browns with dark dirt | OUTLINE AND SHADOW (flat mortar colour) + GRIME part 2 (mottle) | settings + **new** |
| big flat patches of reds and oranges on each brick (half the picture lies in patches over 511 dots); a few pale and dark bricks | COLOUR AND FADE | settings: the three tongue-removing settings, outlier bricks |
| soot: dark clouds running down over several bricks and the mortar (21.6 % of dots are dark, with the ring and dark bricks) | GRIME part 1 (clouds, taller than wide) | **new** |
| spalls: pale broken patches at brick edges and corners | DAMAGE (flakes, broken corners, bites in pale sandy colours) | settings |
| ring: thin dark line at the top and left of each brick, a shadow band at the bottom and right | OUTLINE AND SHADOW: side outline; the lip turned into a DARK lower rim (`lip_colour` dark brown) | settings (the right-hand shadow is not available) |
| moss | MOSS | off or almost off (none seen in the reference); change its olive tones if kept |
| height = brightness (mortar HIGH, bricks low), normal strength 6 | COMBINE `tone_blend` 0.7 to 1 | settings |

**The layout bundle.** Two ways; try A first (no new code), keep B as the fall-back.
* A: the slate LAYOUT with settings: `rows_per_tile` 12, `slates_per_row` 4, `width_spread` about 0.2, `row_slide` 1, `joint_width` 0.016 (20 dots),
  `row_gap` 0.0148 (18.6 dots), `row_gap_top_share` 0.5, `corner_radius` 0.007 (9 dots), corner factors 1, `joint_lean` 0, the three `ragged_*` about 0.001
  to 0.002, `bottom_tilt` small, `slate_ramp` 0. (Values above a control's listed range are kept; checked.) Gives random brick lengths and chipped edges.
* B: the reuse quick layout with 4 columns (not 6) and mortar shares 0.065 sideways and 0.18 up-down (two constants: make them settings in the copy).

| bundle number | brick meaning |
|---|---|
| `piece_id` | one random number per brick |
| `row` | course number / 12 (no shared layer reads it) |
| `local_x`, `local_y` | across the brick 0 to 1; down the brick 0 (top) to 1 (bottom) |
| `piece_width`, `piece_height` | brick length (about 0.23 tile units, varying) and face height (about 0.066 = 83 dots) |
| `edge_distance`, `top_edge_distance` | distance in from the nearest brick edge; distance below the brick's upper edge |
| `gap_mask`, `piece_mask` | 1 in the mortar (about 22 %); 1 on the brick |
| `base_height` | mortar low, brick high (real relief); `tone_blend` then makes the mortar high in the height map, as in the reference |

**New layer truly needed:** GRIME (5.1), for soot and mortar mottle. Nothing else.

**Measure once (guide; summary numbers already measured, files to read):** `recipes/brick/analysis/palette_k16.npy` (16 colours: 8 reds and oranges that
never occur in the mortar, mortar greys and browns, soot darks), `analysis/element_stats.json` (patch sizes by area), `generator/sampler_model_brick.json`
(per-class brick tones, soot and spall numbers; some chosen by eye, it says so). Measure two new numbers once: the share of soot-dark dots outside the ring
and how big a soot cloud is (how far you can slide the dark mask before it stops matching itself). Never read `analysis/layout_clean.json` (single bricks).

**Baseline (like for like).** The brick's own small description class S (7.8 KB) is fitted to the reference, not rules (same-kind 0.365); the fair
baseline is the brick sampler's new tiles (9.5 KB descriptions of rules plus measured statistics): **same-kind 0.708 on average (0.684 to 0.730, 8 tiles)**.
First new tile: `recipes/brick/variations/tile_11/colour.png`, re-scored today: overall 0.725, **colour 0.750**, height 0.704, normal 0.566.
The earlier layered brick: overall 0.194, colour 0.152 (1254 dots, first settings); round 2's 0.154 to 0.19 were 768-dot bakes enlarged, NOT like for like.
Expect a big gap at first: the brick new tiles carry dot-level grain, which the brick lessons say lifts the same-kind score by itself.

**Steps.** (1) Copy, switch to 4 bricks per course (layout A or B), b1 settings plus the three paint settings; 768-dot colour views; look. (2) Soot and
mortar: write GRIME, stack it last; look. (3) Hand rounds on palette, chips, ring; colour-only 768 dots. (4) 1254-dot full bake, three seed sets, score;
half-tile and independence tests. **Unsure:** whether the slate LAYOUT's joint spill and chips look right at 20-dot mortar; whether the lip-as-dark-rim trick
reads as a shadow.

### 5.3 WOOD

**What the reference shows, and which layer makes it**

| visible feature (wood 04 guides) | layer | settings or new |
|---|---|---|
| five horizontal boards of different heights (281, 239, 270, 178, 286 dots), full width | LAYOUT (slate, settings) + the turn | settings + a 10-node turn |
| dark wavy gaps between boards (6.8 dots, wobble 3.6 dots) with small grey pebbles in them | OUTLINE AND SHADOW (dark gaps; shadow band and lip off) | settings; pebbles left out in round 1 |
| long thin strips along the grain (68 % of the picture is strips 24 to 96 dots long), zones about 120 x 25 dots; browns, tans, grey-blue | COLOUR AND FADE on the turned bundle | settings (look check: works) |
| fine dry-brush streaks and hair-thin lines | COLOUR AND FADE specks (stretched along) first | settings; GRAIN layer (borrowing "Wood Grain Gain" unchanged) only if needed |
| long dark cracks along the grain (very dark dots 6.4 %, median 47 dots long, 2.9 dots wide, 37 % along the gaps) | DAMAGE cracks start only at a piece edge | **new CRACKS layer** (or a code change in a copy of DAMAGE: "start anywhere") |
| four knots with rings (half-sizes 30 to 64 dots) | none | KNOTS layer, optional (round 2) |
| rust splatter: 513 small blobs (radius about 3 dots) in 70 clouds about 42 x 35 dots | MOSS lichen discs in rust browns, clustered | settings (look check: discs appear, need more and bigger colonies) |
| chipped board edges | DAMAGE flakes on the long edges (`side_share` high) | settings |
| height = straight stretch of brightness (12 to 128), normal strength 8 | COMBINE `tone_blend` high | settings |

**The layout bundle (turned).** The slate LAYOUT with `rows_per_tile` 5, `slates_per_row` 1, `row_gap` 0.0054 (6.8 dots), `row_height_jitter` about 0.25
(boards differ by up to a quarter), `joint_width` small (the butt joint), corners and chips small, `width_spread` 0. Then a **turn** in the recipe (about 10
nodes): new `local_x` = old `local_y`; new `local_y` = old `local_x`; `piece_width` and `piece_height` swapped; new `top_edge_distance` = old `local_x` x old
`piece_width` (distance from the board's left end). The other numbers pass through.

| bundle number | wood meaning (turned) |
|---|---|
| `piece_id` | one random number per board length |
| `row` | board number / 5 |
| `local_x` | across the board, 0 at its top to 1 at its bottom |
| `local_y` | ALONG the board, 0 at its left end to 1 at its right end |
| `piece_width`, `piece_height` | board height (0.14 to 0.23 tile units); board length (about 1 tile) |
| `edge_distance`, `top_edge_distance` | distance in from the nearest edge; distance from the left end |
| `gap_mask`, `piece_mask`, `base_height` | the dark gaps (and butt joint); the board; gaps low, boards high |

**A limit to know:** every board needs at least one end per tile. A piece that spans the whole tile would have its own coordinates restart at the tile edge,
which shows as a seam in every pattern read on the piece. The reference has no butt joints; the trial will have one per board per tile (staggered by the
row slide). Say so in the results.

**New layer truly needed:** CRACKS (long thin dark lines that start anywhere inside a board and run along the grain, narrowing to a point; some along the
gaps). About 40 nodes, reading the turned bundle and its own seed. KNOTS and GRAIN only if round 1 shows they are missed.

**Measure once:** `recipes/wood/analysis/palette16.json` (16 colours; the look check used 9 picked from the S1 description's palette), `paint_model.json`
(zones and strip classes), `wood_measurements.json`, the board heights and gap widths above, crack and splatter summaries above. Never copy the crack lines or
knot places in `S1_layout_paint_grain.json` or `cracks_fitted.json`.

**Baseline.** Wood S1 (6.2 KB: invented paint, but its 5 board gaps, 20 crack lines, 25 rust-splatter clouds and 4 knots are written from the
reference; counted in the file today): same-kind 0.635. New tiles from the wood sampler: **0.626 on average (0.607 to 0.665)**, optimistic because
the sampler was tuned on this score. First new tile: `recipes/wood/variations/sample_101/colour.png`, re-scored today: overall 0.619, **colour 0.622**,
height 0.575, normal 0.533.

**Steps.** (1) Copy the look check's board recipe into `reuse_trials/wood/`, replace its quick layout by the slate LAYOUT plus the turn; 768-dot views. (2)
Palette, strips, rust colonies by hand. (3) CRACKS. (4) Full bake, three seed sets, tests. **Unsure:** whether the slate LAYOUT works with one piece per
row (`slates_per_row` 1 was not tried; if not, keep the look check's quick board layout, which did work); whether its straight rows look like wavy board
gaps; whether the specks give enough fine grain.

### 5.4 METAL (rusted riveted steel)

**What the reference shows, and which layer makes it**

| visible feature (metal 04 guides) | layer | settings or new (meaning re-used) |
|---|---|---|
| bare steel plate in five blue-grey tones (steel 63 % of the picture) | COLOUR AND FADE | settings |
| straps: 2 upright (about 136 dots wide) and 2 lying (100 to 163 dots) on the plate; 2 diagonal braces (about 100 dots, 44 to 54 degrees) | LAYOUT | **new layout** (braces in round 2) |
| plate seams (thin dark lines) and the dark crease along every bar edge | LAYOUT gaps + OUTLINE AND SHADOW | new layout + settings |
| bar edge drawing: upper and left edges: short shadow, dark crease, bright line; lower and right edges: long soft shadow (about 20 dots), very dark crease | OUTLINE AND SHADOW shadow band under the upper edge (= the shadow below a lying bar) | settings for that half; the bright upper-left line and the shadow right of upright bars need **EDGE LIGHT** (round 2) |
| rivets: 33, radius 19.5 dots, faceted domes (4 rings x 8 slices), 170 to 290 dots apart along bars and at crossings | none | **new RIVETS layer** |
| rust blooms: 18 % rust plus 9 % dusty rust and pale bare metal, patches about 9 dots wide and 13 tall, gathered at bar edges and under rivets, clumped by panel | **MOSS as RUST** (growth that gathers where water runs and sits): joints = bar edges, patch gate = clumped by panel, `damage_attract` = rust in chipped paint, lichen discs = small rust spots | settings |
| rust streaks: long thin streaks running down from rivets and edges | MOSS drips from the upper edge (long, thin, fringe) | settings; from rivets only with a rivet halo (see "unsure") |
| chipped paint and bare-metal flecks, pits, two long light scratches | **DAMAGE as chipped paint** | settings |
| dark stains (10 %) over plate and bars | COLOUR AND FADE damp patches (read on the whole picture, so they cross pieces) or GRIME | settings, GRIME if too weak |
| fine speckle | COLOUR AND FADE specks and grain | settings |
| height = brightness through a steep curve, normal strength 5 | COMBINE `tone_blend` | settings |

**The layout bundle (new METAL LAYOUT, about 100 to 150 nodes).** Pieces are bar segments and plate panels. Upright bars are cut where they pass under
a lying bar, so no piece spans the whole tile (its coordinates would restart at the tile edge). Strap count is a build setting; positions are evenly spread
with seeded jitter; widths and crease width are settings.

| bundle number | metal meaning |
|---|---|
| `piece_id` | one random number per bar segment or panel |
| `row` | panel row (unused by the shared layers) |
| `local_x`, `local_y` | across and down the bar segment or panel, 0 at its left and top edge |
| `piece_width`, `piece_height` | the segment's or panel's size in tile units |
| `edge_distance`, `top_edge_distance` | distance in from the bar's or panel's nearest edge; below its upper edge |
| `gap_mask`, `piece_mask` | the dark crease lines (2 to 3 dots) along every bar edge and the plate seams; everything else |
| `base_height` | bars higher (about 0.62) than the plate (0.45), creases low; new layers (RIVETS, EDGE LIGHT) can tell bar from plate by this level |

**New layer truly needed:** RIVETS. Discs along each bar's centre line (`local_x` 0.5) at a spacing setting, only where `base_height` says "bar"; each disc
shaded in 8 slices x 4 rings from a light direction (upper left); dome height; rust-brown rim colour. About 50 to 80 nodes. EDGE LIGHT only if the
first round shows the missing bright edge. (An option to try, written down as a change of meaning: wire max(damage mask, rivet halo) into MOSS's
"Damage Mask" socket in the trial recipe, so rust also gathers round rivets. The interface allows only declared links, so this must be recorded.)

**Measure once:** `recipes/metal/analysis/palette_k8.json` and `palette_k12.json`, the wear shares and patch sizes in the 04 Recipe (section 3.3),
`analysis/edge_profiles.json` (widths of shadow, crease, bright line), `description/sampler_model.json` (strap counts and widths, rivet spacing ranges, every
number with a note). Never `analysis/rivets_found.json`.

**Baseline.** Metal S (6.3 KB: the reference's own layout plus procedural wear): same-kind 0.523. New tiles from the metal sampler: **0.569 on average (0.525
to 0.603)**. First new tile: `recipes/metal/variations/seed_1/colour.png`, re-scored today: overall 0.578, **colour 0.540**, height 0.608, normal 0.431.

**Steps.** (1) METAL LAYOUT with straps only; bundle debug views (`bundle.piece_colour`, `bundle.edge_distance`). (2) The four layers by settings, 768-dot
views. (3) RIVETS. (4) Rust and chips by hand. (5) Full bake, three seed sets, tests. (6) Braces and EDGE LIGHT if time allows. **Unsure:** whether MOSS's
drips (made for moss) look like rust streaks; whether the shadow band OUTLINE draws on the upper edge of every piece looks wrong on the bars themselves
(a bar's upper edge lies above the plate, so it should get a bright line, not a shadow); metallic stays one number.

### 5.5 MUD

**What the reference shows, and which layer makes it**

| visible feature (mud 04 guides) | layer | settings or new |
|---|---|---|
| orange-brown earth, 69 % of the picture, made of tiny flat clods (median 39 dots of area, 1.9 times longer than wide, lying along the ruts), 9 earth tones | LAYOUT (pieces = clods) + COLOUR AND FADE (one tone per clod, specks, dry and wet areas from the big patches) | **new layout** + settings |
| wheel ruts: 34 long dark bands about 20 dots wide (brightness 21 against 30 to 33), lighter banks on the lit side, grooves, wet streaks; 2 or 3 directions, S-shaped | none | **new RUTS layer** |
| puddles: 8 big blue-grey water areas (3,000 to 31,600 dots of area), two water tones, scalloped edges | MOSS as WATER: clump noise and the edge rules off, the big seamless patch gate and the low spots (`damp_preference` on a low `base_height`) on, tones = water blue-greys | settings, **unsure**; PUDDLES layer if it fails |
| stones: 830, median 83 dots of area (biggest 10,500), dark, angular, lit faces from the upper left, gathered round big stones | small ones: MOSS lichen discs in stone greys (round, not angular); bigger ones: a STONES layer using `stone_tools.polygon_stones` unchanged | settings + **new STONES** |
| crumbly fine edges (the reference has twice the fine-edge density of the first sampled ground) | DAMAGE flakes on clod edges in dark brown | settings, unsure |
| height = straight stretch of brightness (20 to 128), normal strength 9 | COMBINE `tone_blend` high | settings |

**What to do with no pieces.** One piece for the whole tile does not work: its own coordinates would restart at the tile edge (a seam in every pattern
read on piece coordinates) and it would get one random number for everything. Make the pieces the **clods**: a seamless cell layout (a jittered grid of
points, each dot belongs to its nearest point; point indices wrapped so the tile repeats; cells stretched along the main rut direction by a setting). No
gaps, so OUTLINE AND SHADOW has nothing to draw (Amount 0, or a 1-dot dark crack between clods). Try two cell sizes (the clod size, about 0.006 tile units,
and a "ground patch" of about 0.04 with COLOUR AND FADE's specks making the clods inside) and keep the better by eye. About 150 to 250 nodes (each dot looks
at the 3 x 3 neighbouring grid cells).

| bundle number | mud meaning |
|---|---|
| `piece_id` | one random number per clod |
| `row` | 0 (unused) |
| `local_x`, `local_y` | where in the clod's box, 0.5 at its point, 0 at the left and top |
| `piece_width`, `piece_height` | the cell size (stretched along the rut direction) |
| `edge_distance` | distance to the nearest cell border |
| `top_edge_distance` | distance below the clod's upper border (approximately `local_y` x `piece_height`) |
| `gap_mask`, `piece_mask` | 0 and 1 everywhere (no gaps), or a 1-dot crack |
| `base_height` | a gentle seamless relief: low basins where puddles collect (MOSS-as-water reads it), lower along the ruts if RUTS also writes height |

**New layers truly needed:** RUTS (bands made from seamless noise in 2 or 3 directions, wobbling, with a dark band, a lighter bank on the lit side, a groove,
wet streaks; sunk height; about 60 to 100 nodes; can borrow `hp_tools` warp and streaky noise). STONES (borrow `polygon_stones` unchanged, mask and facet
brightness are enough; about 30 nodes of colour on top). PUDDLES only if MOSS-as-water shows the clod mosaic at its edges.

**Measure once:** `recipes/mud/analysis/palette_k16.json` (earth browns from (46,29,24) to (156,112,82), water (86,94,104) and (107,119,126), stone greys),
the shares above (non-earth 31 %), `generator/fitted_distributions_mud.json` and `analysis/sampler_stats_mud.json` (summaries: stone size list summary,
puddle sizes, clod chance table by distance from a rut). Never `ruts_main_mud.json` or the element files (single ruts and stones).

**Baseline.** Mud S (7.4 KB: rules plus layout numbers): same-kind 0.267. New tiles from the mud sampler: **0.383 on average (0.353 to 0.416)**, but from
112 to 118 KB descriptions (the sampler writes every clod: size class L, not small), and the score does NOT tell these tiles from other surfaces (they
score 0.25 to 0.38 against the other references). First new tile: `recipes/mud/variations/tile_101/colour.png`, re-scored today: overall 0.407, **colour
0.313**, height 0.488, normal 0.247. The mud trial must also score against the other five references (the control) and be judged by eye.

**Steps.** (1) CELL LAYOUT, debug views. (2) COLOUR AND FADE as earth. (3) RUTS. (4) MOSS as water; PUDDLES if needed. (5) STONES. (6) Full bake, three seed
sets, control scores, tests. **Unsure:** this is the surface with the most new code and the weakest score evidence; mud may be better served by its own
layers than by the shared ones.

### 5.6 GRAVEL

**What the reference shows, and which layer makes it**

| visible feature (gravel 04 guides) | layer | settings or new |
|---|---|---|
| a heap of touching stones, 67.8 % stone; five sizes (half the picture is stone at least 16 dots in radius, a third at least 32) | LAYOUT (pieces = stones, 2 or 3 sizes stacked, big ones win) | **new layout** (mostly a copy of `polygon_stones`) |
| stones in 8 colours from near black (19,19,19) to pale blue-grey (111,117,116); big stones bluer, small ones browner | COLOUR AND FADE (one tone per stone, tints blue-grey and brownish grey) | settings (size-linked colour only through the layout's per-size seeds) |
| light from the top: lightness falls 0.061 per dot going down a big stone | COLOUR AND FADE `fade_direction` -1 (bleached above, darker below), `fade_length` about a stone | settings |
| orange-brown crumbly soil between stones (32 %, 8 soil colours, lumps and specks) | OUTLINE AND SHADOW gap colour = soil base + GRIME gap mottle | settings + **new (shared GRIME)** |
| soil shadow next to stones (soil lightness 31.4 down to 24.6 over 8 dots); NO dark outline on the stones | GRIME low-spot darkening from `base_height` (the layout makes the soil low next to stones) | **new (GRIME part 3)** |
| facets, rim, flakes, a few rust spots | DAMAGE (pale flakes at edges, pits as rust spots); OUTLINE thin side line as the rim; facets: FACETS layer only if needed | settings |
| height = a fitted mix of red and blue, normal strength 10 | COMBINE `tone_blend` | settings |

**The layout bundle (new STONE LAYOUT).** A copy of `lib/contrib/stone_tools.polygon_stones` in `reuse_trials/gravel/` that also returns each stone's
centre offset and radius (they are worked out inside but not returned: build check). Two or three grid sizes (for example 12, 30 and 70 cells across) for
big, middle and small stones; a dot takes the biggest stone it is on.

| bundle number | gravel meaning |
|---|---|
| `piece_id` | one random number per stone |
| `row` | the size class (0, 0.5, 1; unused by the shared layers) |
| `local_x`, `local_y` | across and down the stone, from its centre offset divided by twice its radius, plus 0.5 (0 = top) |
| `piece_width`, `piece_height` | twice the radius, in tile units |
| `edge_distance` | minus the inside distance, in tile units, on the stone |
| `top_edge_distance` | distance below the stone's upper edge (approximately `local_y` x `piece_height`) |
| `gap_mask`, `piece_mask` | the soil; the stone |
| `base_height` | stones high with a dome; soil low right next to a stone, rising over about 8 dots (this carries the shadow; only inside the stone's own grid cell, see "unsure") |

**New layer truly needed:** GRIME (5.1) for the soil and its shadow. FACETS (flat faces lit from the top, sectors by angle from the stone centre) only if the
stones look too flat; the same idea as RIVETS' slices, so write it once if both are needed.

**Measure once:** `recipes/gravel/scores/measurements.json` (stone share, size curve, colours per size, border lightness profile, light),
`scores/window_spread.json` (how much windows differ), `description/S_v4.json` (class counts and radii of the procedural recipe: rules, not positions).
Never `analysis/stones_found.json` or the traced descriptions.

**Baseline.** Gravel S_v4 (2.3 KB, rules): same-kind 0.362 as baked (0.435 in the smoothed-height view; quote as-baked). New tiles from the gravel sampler:
**0.403 on average as baked (0.365 to 0.456)**. First new tile: `recipes/gravel/variations/out/sample_01/colour.png`, re-scored today: overall 0.372,
**colour 0.242**, height 0.407, normal 0.415.

**Steps.** (1) STONE LAYOUT copy with coordinates; debug views. (2) COLOUR AND FADE stones; OUTLINE as soil base. (3) GRIME. (4) DAMAGE flakes. (5) Full
bake, three seed sets, tests. **Unsure:** one stone per grid cell can look like a grid (the warp helps); stones cannot overlap cell borders, so the biggest
stones are limited to about half a cell; the soil "distance to a stone" from `polygon_stones` is only to the stone of the dot's own cell.

---

## 6. Suggested order

1. **Brick** (closest to what was already proven; settings plus GRIME). 2. **Wood** (the turn is proven by eye; one layer). 3. **Gravel** (the layout is
mostly a copy; reuses GRIME). 4. **Metal** (new layout and RIVETS). 5. **Mud** (most new code, weakest score evidence).

---

## 7. What I did not test, and what I am unsure of

* **No trial was baked or scored.** Every "settings only (not tried)" is from reading the code and the 04 guides. The two look checks are 512-dot colour
  views with settings chosen in minutes; they show direction and shape only, not quality, and were not scored.
* The slate LAYOUT with brick and wood settings was built but NOT baked (only the range check). Whether its joints, chips and corners look right at
  20-dot mortar or as board gaps is open.
* Whether the renderer uses an out-of-range setting in full was not checked in a bake (Blender keeps the value; checked).
* MOSS as puddle water (mud) and MOSS drips as rust streaks (metal) are the least certain meanings; DAMAGE as crumbly clod rims (mud) too.
* The baseline numbers are the earlier builds' (re-scored today: identical). The brick and wood baselines are high because their new tiles carry dot-level
  grain and, for wood, a sampler tuned on that score; a layered trial below them is not automatically a failure. Judge by eye as well.
* `hp_tools.py`, `sweep_tools.py`, `description_audit.py` and the test scripts were judged by reading only.
* Time estimates (3 to 5 minutes for a 1254-dot full bake) come from the slate layers' resolution test (about 3 minutes for colour, height and roughness
  at load 4) and today's look check; the trial layouts may be slower (the metal and stone layouts have more nodes per dot).

---

## 8. Files made for this inventory (all in `reuse_trials/`)

* `00 Inventory - which tools fit which surface.md`: this file.
* `inventory_checks/build_check.py` and `build_check.json`: builds every frozen layer box, `polygon_stones` in a layout box, and the wood grain group.
* `inventory_checks/range_clamp_check.py` and `range_clamp_check.json`: settings above a control's range are kept.
* `inventory_checks/look_check_recipe.py`, `look_check_run.py`, `make_look_sheet.py`, folder `look_check/` (six 512-dot colour pictures, `timing.json`,
  `look_check_sheet.jpg`, `zoom_wood_and_brick_all_layers.jpg`): the wood turn and brick tongue checks.
* `inventory_checks/baseline_scores/*_first_new_tile.json`: today's re-scores of the five first new tiles.
* `inventory_checks/count_verdicts.py`: counts the verdicts of the tables in section 4 (the counts table in section 1 comes from it).
