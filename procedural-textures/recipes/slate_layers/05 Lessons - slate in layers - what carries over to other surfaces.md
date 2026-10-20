# 05 Lessons - slate in layers - what carries over to other surfaces

This is for the day you start a surface nobody gave you (a tiled floor, a stone wall, cedar shingles, a planked deck) and want it as one Blender
recipe made of separate layers that you can switch off, re-seed and reuse. It says how to split a surface into layers, in which order to build
them, what to measure first, which traps cost time on the slate, and what was specific to slate. The numbers are the slate's; the lessons are general.
The words (tile, dot, tile units, layer, box, bundle, mask, setting, seed, declared link, same-kind score) are explained in section 0 of
`05 Recipe - slate in layers - how it is made.md`.

**Round 15 (20 October) added section 11 (what a look check and a second round of fixes taught) and corrected four statements that an honesty check found wrong or too strong** (marked "corrected" below):
the ladder claim, the normal-map attribution, the round-14 seed argument and the explanation of the half-tile differences. The numbers in this guide are for the NEW default tile unless a "before" or "old default" is written next to them.
A second honesty check of round 15 then found three more small faults in this guide, corrected in this version: section 6 said the shadow is "4 flat steps" (the default has 2 now), two examples in section 7 quoted old-default numbers without saying so (the 768-dot score and the moss amount), and the two measuring rules for the slate-grey spread were named wrongly in section 11.

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
slate (`ladder/ladder_table.md`, same-kind scores against the reference, 1254 dots, **made again after the look fixes**; the old numbers are in brackets):

| what is in the picture | colour group | height group | overall (harness-style normal) |
|---|---|---|---|
| layout and joints, slates one flat colour | 0.410 (0.322) | 0.441 (0.371) | 0.459 (0.402) |
| + colour and fade | 0.728 (0.480) | 0.691 (0.598) | 0.735 (0.570) |
| + moss | 0.792 (0.636) | 0.737 (0.632) | 0.774 (0.656) |
| + damage (the default tile) | 0.822 (0.701) | 0.735 (0.654) | 0.789 (0.695) |
| the default tile WITHOUT outline and shadow | 0.676 (0.567) | 0.403 (0.367) | 0.601 (0.539) |

So on the slate every layer earns its place. **(Corrected.)** The first version of this guide said "the drawing (outline and shadow) is worth the most of all". That was wrong for the colour group, and it compared two different
questions: how much a layer ADDS to a part-built picture, and how much taking it OUT of the finished picture COSTS. Added to the part-built picture, colour and fade gives +0.318 of the colour group, moss +0.064, damage +0.030; taking outline and shadow out of the finished tile costs 0.146 of the colour group and 0.332 of the
height group. The drawing layer matters most for the HEIGHT (relief) and the joints; the bottom paint matters most for the colour. On a painted ("stylised") surface the dark drawing is still the backbone of the relief, so build it early; but build the bottom paint first.
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
   declared). Table: `tests/independence_full/independence_table.md` (384 dots). **Round 15:** when a layer's FILE changes, run its row again: after six new controls were added to MOSS and OUTLINE AND SHADOW, both were
re-tested (Amount 0 and Seed + 1, 512 dots, `tests/independence_changed_layers_after_look_fixes/`) and every "outside" number was still exactly 0.0; the other layers' files had not changed, so their rows were not run again.

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
  same comparison rolled 7 dots wrong. On the slate the raw difference of the finished colour is 1.6 steps of 255 (1.8 before the look fixes), 0.31 after a 2-dot blur, against 15 for the control: seamless. (`tests/half_tile_layers/half_tile_table.md`, run again after the look fixes.)
  **(Corrected explanation.)** The first version blamed the raw difference on anti-aliasing noise only. A stricter point-sampled run by the honesty check showed that the height, all masks and the slate numbers are exact, and that the colour still differs by 1 to 2 steps on about 57 % of dots:
  that is Blender's default 8-bit dither (a little noise added when the picture is saved), not the recipe. Turn the dither off, or sample by points, when you want the test to show exact zeros.

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
* **Shadows in flat steps**, with a ragged lower border (the `shadow_tiers` setting: 2 flat steps in the default since the look fixes of round 15, 4 before them; 0 = a smooth blur, which looks airbrushed).
* **Hard masks.** A layer's mask is 0 or 1 nearly everywhere; soft masks blend colours and break the painted look. (One exception since round 15: the moss mask is deliberately half see-through at the rim of a clump, `moss.rim_opacity` 0.5, so the slate paint shows through like a thin wash; the paint inside it is still flat steps.)
* **Patches that stop part way.** When the tall patches of COLOUR AND FADE ran the whole slate height, the slates looked like corrugated sheets of
  stripes; a new setting (`colour_and_fade.mottle_tallness`, 2.2 to 1.1) made them stop part way, like brush strokes.

## 7. Traps that cost time on the slate (and will on the next surface)

* **The same-kind score differs from one set of seeds to another, and the default seeds were an unlucky draw (before the look fixes).** The old default settings scored 0.701 on the colour
  group with the default seeds and 0.710 to 0.769 with four other seed sets (the five averaged 0.740, spread 0.068). A tuning round (14) found a pair of settings
  that lifted the default-seed score from 0.701 to 0.796; on two other seed sets the same pair gained only 0.005 and 0.011. **(Corrected reasoning.)** The first version called those gains "smaller than what the seed alone moves". That mixed two things up: 0.068 is how much the score differs between DIFFERENT seed sets,
  not how much it moves when a setting changes on the SAME seeds, where the pair won every time (+0.095, +0.011, +0.005). The honest reading is "a small gain on every set, a big one on the default seeds, nearly all through one cliff measure"; keeping the old settings was a cost choice, not a statistical one.
  After the look fixes the five seed sets score 0.792 to 0.824 (mean 0.810, spread 0.032). Before you adopt a setting because of a score, bake it on at least three seed sets and look at the picture. (Numbers: `integration/r14_results.json`, section 6 and 7.3 of the recipe guide.)
* **The score depends on the picture size.** The scorer enlarges every picture to 1254 dots, so a 768-dot bake is blurrier and scores lower (the
  OLD default, before the look fixes: 0.632 at 768, 0.701 at 1254; the new default scores 0.822 at 1254 and 0.812 for its 512-dot bake, Recipe guide 7.7). Compare scores only between bakes of the same size.
* **One score measure is a cliff.** The colour "feature size" measure (`colour_scale`) is where the picture's sideways self-similarity falls to one
  half; on a surface with strong rows that curve is flat, so a small change jumps it: moss coverage 0.18 to 0.22 (with the drip width 0.06 to 0.07)
  moved it from 0.29 to 0.45 and the colour group from 0.664 to 0.701. Look at the picture before you believe a jump. **Round 15 showed it again:** the look fixes moved the colour group from 0.701 to 0.822 and the feature size measure from 0.452 to 0.899; without that measure (about three quarters of the gain, 0.094 of 0.121, is that one measure) the colour group
  went from 0.767 to 0.801 only; and raising `tone_centre` from 3.7 to 3.85 (to make the tile a little lighter) dropped the colour group from 0.755 to 0.692, all of it in that one measure. Report a score together with its biggest single part.
* **The score and the eye can disagree.** (This example is from the OLD default, before the look fixes; the numbers are not the new default's.) The old default's score preferred MORE moss (15 % olive-or-tan dots by a simple colour rule; the
  reference has 10.7 % by the same rule). We kept the
  score's choice and wrote down the setting a person who prefers the reference's amount should use (`moss.coverage` 0.18, against the old default's 0.22).
  Round 15 then changed the moss anyway, by eye: the new default has `moss.coverage` 0.30 but the moss is a soft see-through wash, and the share of slate dots that are moss is 6.5 % against 9.0 % in the reference (Recipe guide, section 6b, fix 2;
  the simple olive-or-tan rule above is not repeated for the new default in these guides). A person who wants less moss now lowers `moss.coverage` from 0.30.
* **Real relief versus the reference's height.** The reference height was made from the colour, so pale chips are HIGH in it, while real relief
  sinks them. A setting (`combine.tone_blend`) mixes the two: 0.4 gives a height group of 0.505, 0.7 (the default) 0.654, 1 (height from colour
  only) 0.629; the part-built stack before the setting existed (real relief only, older settings) scored 0.485. Say plainly which you chose and why.
* **Layers tuned alone do not add up.** Each builder tuned its layer against the reference; stacked, the first whole bake scored only 0.615 overall
  (colour 0.619). It took 13 hand rounds on the whole stack to reach 0.695 like for like (colour 0.701); the 0.705 usually quoted for that point uses a different normal-map method (corrected: the first version compared 0.615, scored with the harness's own normal map, with 0.705, scored with the strength-7 normal; the normal group itself did not improve, 0.608 to 0.604). Plan time for the integration, and compare scores only when everything but the thing you changed is measured the same way.
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

* (Done in round 15, partly) The tan breaks now spread in chunkier, less gathered flakes and the big corner L-shapes are gone; along most slates the chips are still a thin ragged fringe, not chunky cream flakes.
* (Done in round 15, partly) The moss is now a see-through wash with soft rims (`moss.rim_opacity`), as the reference's moss is partly a green cast over the streaks; the look checker found it still a little pale and combed.
* **Fix the straight-edged paint facets in the code of `colour_and_fade.py`** (bend the cell coordinates with a medium-sized noise before the Voronoi). Settings alone could not.
* A per-layer "direction of weather" setting (from the top, from one side, none) so the paint and moss layers fit bricks and planks without code.
* A mortar option in the drawing layer for surfaces with wide joints.

## 11. What a look check and a second round of fixes taught (round 15, what carries over)

On 20 October a helper who only looked (the "look checker") found eleven faults in a tile that had been tuned for many rounds and scored 0.705; a second helper fixed them by hand; the checker looked again; then everything that depended on the default settings was
baked again. What carries over to the next surface:

1. **Let someone look at the finished tile at full size, next to the reference, and under a low light, before you call it done.** The numbers had said the tile was good for rounds; the eye found rows of moss teeth, tan L-shapes at the corners, a lone crack, black drips under the rows and
   a "liquified" paint. Look at 1:1 crops, at a contrast-boosted copy (it shows flat facets), at a 3 x 3 tiling (it shows repeating landmarks) and under a raking light (it shows the relief). Keep a numbered list of faults, and keep the same list when you look again, so each fault ends as fixed, better, same or worse.
2. **Fixing one fault can make a new one, and a better measure is not a better picture.** The broader paint bands lowered the busy-ness measures and removed the ripple, and brought straight-edged flat facets that the old tile did not have. After every round, measure the old measures again (a table of about ten, before / after / reference) and look at the picture again.
3. **When three or four settings-only tries fail, write a small code change, with a new control that starts at the old behaviour.** The moss cut off in a straight line at the side joints and the opaque khaki moss could not be fixed with the existing settings; six new controls fixed them (`moss.side_clearance`, `rim_opacity`, `core_opacity`,
   `fleck_amount`, `outline_and_shadow.joint_texture`, `joint_texture_size`). Prove "no change at the starting value" (bake with the old and the new file: identical), and run the independence row for that layer again. The facets are the opposite example: they need such a change too, and it was not made, so they are still in the tile.
4. **A setting can be dead because of a wiring choice.** Raising the real relief (lip height, chip depth) changed nothing measurable because the finished height was 70 % paint brightness (`combine.tone_blend` 0.7), which scales the real relief to 30 %. On the next surface decide how the height is made BEFORE you tune the relief, and give real relief the larger share unless you must match a reference height that was made from its colour.
5. **A change to the default moves every result that depends on it, and the definitions of the variations move with it.** Eight variations were each a list of changes to the default; when the default moved (more moss, darker, different tint), v2 ("more moss", coverage 0.34 against a default that went from 0.22 to 0.30) was no longer distinct, and v6 ("dark and wet") was far too dark. After any change of default, look at every variation again; or write
   variations as multiples of the default ("twice the moss") instead of as fixed numbers. Keep a list of everything that depends on the default (here: the ladder, the variations, the seed spread, the area, the half-tile test, the debug views, the controls table, the guides) and one command for each, so the re-bake is a checklist and not a hunt.
6. **Keep "before" copies and show before and after in every table.** The old maps (`outputs/default_before_look_fixes/`), the old settings, the old tables (as "before the look fixes") and a before / after picture made the whole round checkable, and made it clear what the look checker's second look measured against. Make the "before" pictures JPEG when disk is tight.
7. **Two measuring rules for the same thing can disagree; report both.** Two measuring rules for "outlier slates" gave the spread of slate grey 5.6 (reference 5.5; the copy of the look checker's script that the tuner ran) and 6.9 (reference 5.1; the look checker's own cross-check): both agreed it was much better, they disagreed on "fixed". (The tuner's own other script measures slate lightness on another scale: 2.65 against 2.51.) A reader should see both.
8. **Moving one setting can undo another.** The paint grain lowered with the ripple vanished along with the fine grain; the moss became see-through and needed more coverage to read as moss; lifting the overall tone brought the pale outlier slates back. Change one thing, look, measure the others.
9. **A shared machine changes what a plan costs.** With another job always running (load average 7 to 10), a 2508-dot area took 22 minutes instead of 9 and a 512-dot bake three times as long. Count bakes, not minutes; run long ones in the background with a log and wait on the log; never run two of your own at once; keep a written list of which bake belongs to which result.
10. **Keep a note of what you did NOT re-make.** After the look fixes the 4 x 4 area, the resolution pictures, the brick reuse and the control strips were not baked again; each is marked "before the look fixes" in the folder map and in the guide, so nobody reads old pictures as new ones.
