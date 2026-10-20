# 05 Lessons - slate in layers - what carries over to other surfaces

This is for the day you start a surface nobody gave you (a tiled floor, a stone wall, cedar shingles, a planked deck) and want it as one Blender
recipe made of separate layers that you can switch off, re-seed and reuse. It says how to split a surface into layers, in which order to build
them, what to measure first, which traps cost time on the slate, and what was specific to slate. The numbers are the slate's; the lessons are general.
The words (tile, dot, tile units, layer, box, bundle, mask, setting, seed, declared link, same-kind score) are explained in section 0 of
`05 Recipe - slate in layers - how it is made.md`.

## 1. How to split any surface into layers (and the order to build them in)

Think of how a painter would paint the surface, back to front, and give each kind of brush work its own box. On the slate that was (the order
below is the order to BUILD them in, suggested by the ladder further down; the slate's four layers were in fact built at the same time by four
people. The order they are PAINTED in is different: colour and fade, moss, damage, and the drawing last, on top of everything):

| order | box | the question it answers | what it reads | what it gives |
|---|---|---|---|---|
| 1 | **LAYOUT** | "which piece am I on, and where on it?" | the tile coordinate only | the **bundle** (eleven numbers per dot) and the bare relief; it paints nothing |
| 2 | **the bottom paint** (COLOUR AND FADE) | "what colour is the bare material here?" | the bundle | a colour on EVERY dot (it is the bottom of the stack) |
| 3 | **the drawing** (OUTLINE AND SHADOW) | "where are the dark lines, shadows and light edges?" | the bundle | a colour where the drawing is, a relief |
| 4 | **growth** (MOSS) | "where does something grow on top?" | the bundle (+ a declared link to damage) | colour, a little raised relief, rougher |
| 5 | **damage** (DAMAGE) | "where is material missing or broken?" | the bundle | colour, sunk relief, rougher |
| 6 | **COMBINE** | "who paints over whom, and what are the four maps?" | every layer's four outputs | colour, height, roughness, metallic |

Why this order: each step changes what the next one looks like, and the ones that buy the most come first. The "what each layer buys" ladder of the
slate (`ladder/ladder_table.md`, same-kind scores against the reference, 1254 dots, **re-run and scored after the restart**):

| what is in the picture | colour group | height group | overall |
|---|---|---|---|
| layout and joints, slates one flat colour | 0.322 | 0.371 | 0.402 |
| + colour and fade | 0.480 | 0.598 | 0.570 |
| + moss | 0.636 | 0.632 | 0.656 |
| + damage (the default tile) | 0.701 | 0.654 | 0.695 |
| the default tile WITHOUT outline and shadow | 0.567 | 0.367 | 0.539 |

So on the slate every layer earns its place, and the drawing (outline and shadow) is worth the most of all: taking it out of the finished tile costs
0.13 of the colour group and 0.29 of the height group. On a painted ("stylised") surface the dark drawing is the backbone, so build it early.
(Every line of the ladder includes OUTLINE AND SHADOW except the last one, which has it removed.)

## 2. The interface first: design the bundle once, then freeze it

The bundle is what makes the layers reusable. Write it down (names, units, ranges, which way is up) BEFORE anyone writes a layer, test it with debug
views, then do not change it. On the slate four builders worked against it at the same time, each in their own layer file; the bundle was
not changed after the layers existed.

What a good bundle has (the slate's eleven numbers are a good starting list for any "pieces with gaps" surface: bricks, tiles, planks, plates, shingles,
paving):
* a random number per piece (`piece_id`): every layer turns it into its own random numbers with its own seed (White Noise of piece_id and seed);
* where on the piece (`local_x`, `local_y`, 0..1) AND the piece's size in tile units (`piece_width`, `piece_height`), so a layer can work in real
  sizes on the piece ("a drip 0.14 tile units long") and not in stretched 0..1 units;
* distance to the piece's REAL edge (`edge_distance`, along the chipped outline) and to its upper edge (`top_edge_distance`): almost every effect
  (chips, outlines, shadows, lips, moss along edges) is "something within so far of an edge";
* the two masks (gap / piece) and a bare relief (`base_height`).

Traps of the bundle: say which way `local_y` runs (on the slate 0 = TOP of the piece while the picture's y runs UP; the interface page puts
it first in its list of "three things that are easy to get wrong");
in the gaps the piece numbers are still defined but cut off, so layers must use the masks; the bundle has no "distance to the nearest corner", so
corner effects (corner breaks, rounder bottom corners) were computed from `local_x`, `local_y` and the sizes inside each layer.

## 3. The rules that make layers truly independent (and how to prove it)

1. **Own seed**: every random number in a layer comes from (piece_id or tile coordinate) + THIS layer's seed. Then changing the moss seed gives a new
   moss pattern and the same slates, damage and fade.
2. **Amount 0 means exactly nothing**: mask, height and roughness exactly 0, not "nearly". One shared helper (`finish_layer`) guarantees it for all layers.
3. **No peeking**: a layer reads only the bundle, its own settings and its declared links. A link is one line in the reading layer's file plus a row
   in the interface page and the guide. The slate has one: MOSS reads DAMAGE's mask (moss keeps off fresh breaks, `moss.damage_avoid` 0.8).
4. **Prove it with a table**, not a promise: bake the whole recipe once as it is, then once per layer with Amount 0 and once with Seed + 1, and count
   the dots that changed OUTSIDE that layer's own mask. On the slate every one of the nine rows is exactly 0.0 % outside, and the only other layer
   whose own pattern moved is MOSS when DAMAGE changes (0.92 % and 1.57 % of the dots, all inside the damage mask: the declared link, exactly as
   declared). Table: `tests/independence_full/independence_table.md` (384 dots).

## 4. Seamless and any size: two kinds of coordinates

Every pattern in a layer belongs either to the whole surface or to one piece, and each kind has its own way to repeat exactly at the tile edge:

* **Whole surface** (big sun-bleached areas, where moss gathers, the ragged border of a shadow): seamless noise read on the tile coordinate (the
  project's 4D "donut" noise), with its scale written as "features per base tile x Tile Count". Then `recipe.tiles_across` 2 gives a 2 x 2 area of
  NEW content with the same look per dot, and the area still wraps round its own edge.
* **One piece** (streaks, drips, flakes, the shadow under a row): ordinary Noise or Voronoi read on the piece's own coordinates
  (`local_x x piece_width`, `local_y x piece_height`) with offsets from `piece_id`. A piece cut by the picture edge has the same number and coordinates
  on both sides, so it repeats exactly too, and Blender's ordinary (non-seamless) textures can be used, which are faster and offer 1D, 2D and 3D.
* Counts (rows, pieces per row, lichen grid places) must be whole numbers; every size must be in tile units.
* Prove it with the half-tile test (bake, bake again slid by half a tile, compare with the first rolled by half) and give the test a CONTROL: the
  same comparison rolled 7 dots wrong. On the slate the raw difference of the finished colour is 1.8 steps of 255 (anti-aliasing noise on one-dot
  edges), 0.34 after a 2-dot blur, against 16 for the control: seamless. (`tests/half_tile_layers/half_tile_table.md`.)

## 5. What to measure first on a new reference (once, as a guide, never slate by slate)

The brief forbids fitting, so the reference is measured ONCE for its general character and the numbers become starting values:

1. **Palette**: the brightness range of the bare material (slate: 25 to 112 of 255, median 63), its hue families (blue-grey; green-grey), and the
   families of everything on top (olive moss, tan lichen and breaks, near-black joints). Nine to twelve colours are enough for a painted surface.
2. **Shares** by a simple colour rule: on the slate reference 10.7 % olive-ish dots, 2.6 % tan, 11.2 % very dark (`integration/colour_character.py`).
   These set coverage settings and are the first thing to check on every bake.
3. **The run inside one piece**: how much lighter the bottom of a slate is than its top (slate: about 33 steps of 255), how wide the dark band under
   each row is (10 dots core + about 21 dots of shadow), the lip.
4. **Sizes**: piece sizes and their spread, joint widths, how big the flat patches are (the painted references measure 21 to 51 dots across), how tall versus wide.
5. **How the maps were made**: the slate reference height is the brightness of its colour (2.5 x (brightness - 9.5)), the normal the slope of that
   height at strength 7. Decide early whether you want real relief or the reference's colour-made height; on the slate a setting does both (section 7).

## 6. How to make it look painted, not airbrushed and not like camouflage

* **Tone steps and rounding.** Work out a tone STEP per dot as a sum of small pieces (the piece's own tone, streaks, patches, specks, big areas), then
  ROUND it and look the colour up in the palette. Rounding is what makes flat patches with hard edges; a "hardness" setting (0..1) that softens the
  rounding is a useful knob but should stay at 1.
* **Tall, not round.** Streaks, drips and patches stretched up-down (1D noise turned pointy with `1 - |2n - 1|` for tongues; Voronoi on a stretched
  coordinate for patches). Round blobs read as camouflage; that was the first slate build's main weakness.
* **Start growth at an edge.** Moss that starts at each slate's own upper edge and runs down, with strands of different lengths, reads as drips;
  free clump noise everywhere reads as camouflage (see `controls_sweeps/moss/07_clump_strength.png`).
* **Shadows in flat steps**, with a ragged lower border (the `shadow_tiers` setting: 4 flat steps; 0 = a smooth blur, which looks airbrushed).
* **Hard masks.** A layer's mask is 0 or 1 nearly everywhere; soft masks blend colours and break the painted look.
* **Patches that stop part way.** When the tall patches of COLOUR AND FADE ran the whole slate height, the slates looked like corrugated sheets of
  stripes; a new setting (`colour_and_fade.mottle_tallness`, 2.2 to 1.1) made them stop part way, like brush strokes.

## 7. Traps that cost time on the slate (and will on the next surface)

* **The same-kind score moves with the seed alone, and the default seeds were an unlucky draw.** The default settings score 0.701 on the colour
  group with the default seeds and 0.710 to 0.769 with four other seed sets (the five average 0.740). After the restart a new tuning round (14) found a pair of settings
  that lifted the default-seed score from 0.701 to 0.796, close to the brief's 0.8; on two other seed sets the same pair gained only 0.005 and 0.011.
  Before you adopt a setting because of a score, bake it on at least three seed sets. (Numbers: `integration/r14_results.json` and section 6 of the
  recipe guide.)
* **The score depends on the picture size.** The scorer enlarges every picture to 1254 dots, so a 768-dot bake is blurrier and scores lower (the
  default: 0.632 at 768, 0.701 at 1254). Compare scores only between bakes of the same size.
* **One score measure is a cliff.** The colour "feature size" measure (`colour_scale`) is where the picture's sideways self-similarity falls to one
  half; on a surface with strong rows that curve is flat, so a small change jumps it: moss coverage 0.18 to 0.22 (with the drip width 0.06 to 0.07)
  moved it from 0.29 to 0.45 and the colour group from 0.664 to 0.701. Look at the picture before you believe a jump.
* **The score and the eye can disagree.** The score preferred MORE moss (15 % olive-or-tan dots by a simple colour rule at the default; the
  reference has 10.7 % by the same rule). We kept the
  score's choice and wrote down the setting a person who prefers the reference's amount should use (`moss.coverage` 0.18).
* **Real relief versus the reference's height.** The reference height was made from the colour, so pale chips are HIGH in it, while real relief
  sinks them. A setting (`combine.tone_blend`) mixes the two: 0.4 gives a height group of 0.505, 0.7 (the default) 0.654, 1 (height from colour
  only) 0.629; the part-built stack before the setting existed (real relief only, older settings) scored 0.485. Say plainly which you chose and why.
* **Layers tuned alone do not add up.** Each builder tuned its layer against the reference; stacked, the first whole bake scored only 0.615 overall
  (colour 0.619). It took 13 hand rounds on the whole stack to reach 0.705 (colour 0.701). Plan time for the integration.
* **Parallel bakes double each other's time and the machine can restart.** Run long bakes as a chain, one after another, each writing a log and a
  `.done` file, and keep every number in a `.json` next to its pictures. After the restart on the slate the half-finished items were found from
  these files in minutes.
* **Disk.** Sixteen-bit height maps of 2508 dots are 14 MB each; a 4 x 4 area colour picture (5016 dots) is 31 MB. Keep in-between pictures as JPEG and
  delete superseded bakes once their numbers are written down (`integration/takeover/CLEAN_UP_AFTER_RESTART.md`).
* **A slow analysis can hide in a measuring script.** The area script worked out the "typical jump" of the whole picture for every column: fine at
  2508 dots, hours at 5016. Work out whole-picture numbers once.

## 8. The reuse test: the same layers on a brick wall (what had to change)

`reuse/brick_layers_recipe.py` puts the UNCHANGED files `layers/colour_and_fade.py`, `damage.py`, `moss.py`, `outline_and_shadow.py` and `combine.py`
on a different layout: a brick wall of 12 rows of 6 bricks, every second row slid by half a brick. What had to be written:

| what | size | notes |
|---|---|---|
| a brick LAYOUT that makes the same eleven bundle numbers | about 40 nodes (the slate LAYOUT has 307) | straight rows and columns, mortar 7 % of a brick sideways and 14 % up-down; `local_y` 0 at the TOP of the brick as the interface demands |
| a settings dictionary `BRICK_SETTINGS` | 53 settings | nine brick reds instead of blue-greys, shorter streaks and drips (a brick is shorter than a slate), smaller flakes, chips on all edges, mortar-grey joints, a thinner shadow, no black drips |
| lines changed in any layer file | **none** | the wiring (including the declared link moss <- damage) is copied from `recipe/slate_recipe.py` |

Result (`reuse/reuse_sheet.png`, 1254 dots, **the last four views re-run after the restart**): it bakes; it shows no seam at the wrap edge (a simple
check, `reuse/baked/brick_seam_check.json`: the jump across the edge is 0.4 and 0.1 times a normal jump, because the edge falls in the flat mortar;
the full half-tile test was NOT run on the brick); every layer lands where it should
(damage at the lower edges and corners of the bricks, moss in drips from the top of each brick, the outline in the mortar), and it reads as an old
painted brick wall. What did NOT carry over well, and why:
* The pointed tongues of COLOUR AND FADE hang from the top of every piece. On slate that is how rain runs; on brick it makes every brick look like a
  little slate. **Tested after the restart** (`reuse/settings_round_2/brick_settings_round_2.jpg`, 768 dots): `colour_and_fade.fade_direction` 0
  removes the dark-top / light-bottom trend but NOT the pointed tongue shapes, which come from the streak and mottling parts of the layer. A brick
  needs a paint layer without tongues (or a new "streak shape" setting).
* Mortar is a wide flat band, not a black gap with a shadow: OUTLINE AND SHADOW can only make it a flat colour (settings), not mortar with its own
  texture. A brick surface would want its own drawing layer, or a mortar setting in the layout's base relief.
* The brick reference has light mortar and soot that crosses bricks. The first brick settings were chosen in minutes and never tuned against the
  brick reference; the same-kind score against the brick reference is 0.19 overall (colour 0.15). One settings-only round after the restart
  (redder palette, light mortar through the outline layer's joint colours) made it read much more like a brick wall (colour group 0.154 to 0.19);
  the "soot" tried through the damp-stain setting (`stain_amount` 0.8) hardly shows, because the stain only darkens the brick paint by tone steps
  and the mortar is painted over it. **The reuse test proves the layers transfer, not that the brick looks like that reference.**

So the layers transfer when the new surface "is made of pieces with edges" and the effects are "something near an edge" or "something on a piece".
Settings carry the look a long way; the assumptions about where the weather comes from (top of a piece) are the part that is slate-specific.

## 9. What is specific to slate, and what is general

**General (reuse as it is):** the six-box split; the bundle and its rules; one seed per layer and Amount 0 = exactly nothing; declared links; tile
units and the two kinds of coordinates; tone steps + rounding + palette for a painted look; tall shapes and growth that starts at an edge; stepped
shadows; the independence table and the half-tile test with a control; the ladder; hand-tuning rounds with a side-by-side picture and the same-kind
score, judged on several seeds; chain bakes with logs and `.done` files.

**Slate only (change these numbers, or these few lines, for a new surface):** 8 rows of 6 slates of log-normal width; rounded bottom corners; chips
mostly on the lower edge; dark tongues from the top and bleached tongues from the bottom; the shadow band under each row and the pale lip at the lower
edge; moss drips from the upper edge; blue-grey, olive and tan palettes; the height made 70 % from the paint brightness.

## 10. What I would do next (honest)

* Make the tan breaks spread along MANY lower edges in small flecks (the reference) instead of gathered on a few slates (now): lower
  `damage.slate_variation` and `damage.chip_clustering`, raise `damage.chip_frequency`; not tried after the restart, because it would have meant
  re-baking every result.
* Let moss mix into the paint as a tint at its fringes (the reference's moss is partly a green cast over the streaks), not only solid clumps.
* A per-layer "direction of weather" setting (from the top, from one side, none) so the paint and moss layers fit bricks and planks without code.
* A mortar option in the drawing layer for surfaces with wide joints.
