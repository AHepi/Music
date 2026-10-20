# 05 Recipe - slate in layers - how it is made

This guide explains, for a person who is not a programmer, how the slate roof texture is made in Blender as ONE recipe built from separate
layers, what every part does, which settings matter and what changing them does, how well it matches the reference, and what does not work yet.
The companion guide, `05 Lessons - slate in layers - what carries over to other surfaces.md`, says what to take from this to other surfaces.

Who did what: five helpers built the layout and the four layers (each tested its own layer); a first integrator joined them, tuned the whole
stack by hand in 13 rounds and baked most of the results; the machine restarted at about 03:15 before it wrote these guides. I (the second
integrator) checked every result on disk, re-ran what the restart had cut off or never started (marked **re-run after the restart** below),
kept the first integrator's tuning (section 6 says why) and wrote the guides and `final_report.json`.

![the default tile next to the reference](integration/takeover/whole_ref_vs_default.png)

*Left: the reference (a guide only). Right: the default tile of this recipe (1254 x 1254 dots). The slates, streaks, moss and chips are all
made by Blender nodes from a list of 176 settings (49 of them tuned by hand and stored in `recipe/settings.json`); nothing is copied from the
reference slate by slate.*

## 0. Words used in this guide (one word for each thing)

| word | meaning |
|---|---|
| **tile** | the square picture that repeats (1254 x 1254 dots for the default). A **base tile** is one repeat of the pattern. |
| **dot** | one dot (pixel) of a picture. |
| **tile units** | sizes written as a share of the base tile: 1.0 = the whole tile; at 1254 dots per tile, 0.0064 = 8 dots. Every size in the recipe is in tile units, so the look is the same at any picture size. |
| **slate** | one roof slate. A **row** is a horizontal line of slates. |
| **joint** | the dark gap between two slates of a row, and the dark band between two rows. |
| **layer** | one of the boxes that paint: COLOUR AND FADE, DAMAGE, MOSS, OUTLINE AND SHADOW. LAYOUT (the slates) and COMBINE (stacking) are boxes too, but they do not paint. |
| **box** | what Blender calls a *node group*: a set of nodes packed into one node with named sockets, which you can open, look inside and switch off. |
| **bundle** | the eleven numbers LAYOUT gives every layer for every dot ("which slate am I on, and where on it"). |
| **mask** | where a layer paints: 1 = the layer's colour fully covers what is below, 0 = the layer does nothing there. |
| **setting** | one number or colour you can change, named `layer.name`, for example `moss.coverage`. It is also a knob (socket) on the layer's box in the Shader editor. All settings are listed in `recipe/controls.md`. |
| **seed** | a number that picks a different random pattern; every layer has its own. |
| **declared link** | the ONLY way one layer may look at another layer (written in the layer's file and in this guide). There is one: MOSS reads DAMAGE's mask. |
| **same-kind score** | `lib/texture_compare.py`: 0 = as different as another surface, 1 = cannot be told apart by that measure (a re-shuffled copy of the reference scores about 0.99). It has groups: colour, height, normal, tiling. |
| **dot-for-dot score** | `lib/pixel_compare.py`: compares two pictures dot by dot. It is reported for transparency only; it is NOT a target here (the slates are new slates, not the reference's slates). |

## 1. How to bake it (copy and paste)

Blender 5.2.2, command line, CPU, 2 threads. `cd` into the project folder `proc-work` first.

```
# the finished maps: colour, height (16 bit), roughness, metallic, normal (6.6 minutes at 1254 dots when it was baked, of which 3.4 minutes
# is the extra "normal_bumpnode" picture the harness also makes)
blender -b --disable-autoexec -t 2 --python lib/bake_harness.py -- recipes/slate_layers/recipe/slate_recipe.py OUT --size 1254 --normal-reference slate

# change any setting for one bake (here: more moss and a new moss pattern)
... --params '{"moss.coverage": 0.34, "moss.seed": 61}'

# one layer alone (a "debug view"): its mask, colour, height or roughness
... --params '{"debug_view": "moss.mask"}'          (also damage.colour, outline_and_shadow.height, bundle.edge_distance, bundle.piece_colour ...)

# a bigger area of NEW slates: 2 x 2 base tiles = 2508 dots
... --size 2508 --params '{"recipe.tiles_across": 2}'

# the reference-style normal map from the baked height (3 x 3 slope, strength 7, the rule the reference maps were made with)
python3 -I recipes/slate_layers/integration/make_normal.py OUT/height.png OUT/normal.png 7
```

The default tile is in `outputs/default/` (colour.png, height.png 16 bit, normal.png = strength 7 like the reference, roughness.png,
metallic.png; plus normal_harness_sobel.png = the harness's own normal with a fitted strength of 7.37, and normal_bumpnode.png).

## 2. The plan: one recipe, six boxes, eleven shared numbers

```
          Vector (where on the tile: x 0..1 left to right, y 0..1 bottom to top)
             |
          LAYOUT  ---- the bundle: eleven numbers for every dot ----+---------------+-------------+--------------------+
                                                                     |               |             |                    |
                                                             COLOUR AND FADE       MOSS  <---- DAMAGE         OUTLINE AND SHADOW
                                                                     |               | (declared link: Damage Mask)    |
                                                                     +---------------+------+------+--------------------+
                                                                                            |
                    LAYOUT's base_height -----------------------------------------------> COMBINE --> Colour, Roughness, Metallic, Height
```

Open `recipe/slate_recipe.py` in Blender (or bake it) and you see one box called SLATE; inside it the six boxes above, each of which you can open
and switch off (Amount 0). That is what "layers inside the recipe" means: the layers are not separate pictures, they are separate boxes of nodes
inside one node tree, and the pictures in `debug_views/` are made by baking one box's output alone.

**The bundle** (the fixed interface; full table in `interface/interface.md`). For every dot LAYOUT answers "which slate am I on and where on it?":

| number | what it is, with an example |
|---|---|
| `piece_id` | a random number 0..1, the same on every dot of one slate. Example: every dot of one slate carries, say, 0.4172 and every dot of its neighbour 0.8806. Layers use it to give each slate its own tone, damage and moss. |
| `row` | the row number divided by the number of rows (8 rows: 0, 0.125, ... 0.875) |
| `local_x`, `local_y` | where on the slate: 0..1 across, and 0..1 DOWN (0 = the slate's top edge). Example: the middle of a slate's lower edge is (0.5, 1). |
| `piece_width`, `piece_height` | the slate's size in tile units (median width 0.164 = 206 dots, height 0.120 = 150 dots) |
| `edge_distance` | how far in from the nearest slate edge, along the real chipped outline (tile units, 0 at the edge) |
| `top_edge_distance` | how far below the slate's upper edge |
| `gap_mask`, `piece_mask` | 1 in the joint / 1 on the slate |
| `base_height` | the bare relief: joints low (0.08), slates high (about 0.50), a rounded slope 4 dots wide along every edge |

**The rules every layer keeps** (they are what make the layers independent and the tile seamless):

1. A layer reads only the bundle, its own settings, its own seed and its declared links. It never reads another layer's picture.
2. Every layer has the same four outputs: Mask, Colour, Height (0 = no change), Roughness (0 = no change). Amount 0 makes Mask, Height and
   Roughness exactly 0 (the shared helper `finish_layer` in `layers/layer_interface.py` guarantees it).
3. Sizes are tile units. Counts (rows, slates per row) are whole numbers.
4. Anything that belongs to the whole roof (big sun-bleached areas, where moss gathers) uses the SEAMLESS noise on the tile coordinate; anything
   that belongs to one slate (streaks, drips, chips) uses the slate's own coordinates (`local_x x piece_width`, `local_y x piece_height`) with
   random offsets from `piece_id`. Both repeat exactly at the tile edge: the first because the noise is read on a donut (section 3), the second
   because a slate cut by the picture edge carries the same `piece_id` and coordinates on both sides.
5. Settings: the starting value written in the layer's own file < `recipe/settings.json` < the parameters of a bake. `settings.json` holds only
   what was tuned (49 entries, 1.7 KB; the size check `lib/description_audit.py --limit-kilobytes 8` passes with no problems).

**COMBINE** stacks the layers: colour starts as COLOUR AND FADE's colour on every dot; then, in the stack order (`recipe.stack_order`, default
`colour_and_fade, moss, damage, outline_and_shadow`), each layer's colour is laid over it by its mask. Height = base_height + the sum of every
layer's height (then partly replaced by the paint brightness, see `combine.tone_blend` in section 5). Roughness = 0.8 + the sum of every
layer's roughness. Metallic = 0.

## 3. The Blender tools used, in one plain sentence each

Everything is shader nodes, written by Python, inside one node group (1,842 nodes in all: LAYOUT 307, COLOUR AND FADE 419, DAMAGE 439,
MOSS 419, OUTLINE AND SHADOW 216, COMBINE 19, plus small helper groups; counted by `integration/count_tools.py`, list in `integration/tools_used.json`).
There is no picture, no geometry and no modifier: this shader recipe bakes in about one minute per map at 1254 dots (the research measured
geometry recipes at 1.5 to 4.5 minutes for all maps; shader recipes at 18 to 54 seconds, so this one, with about 1,840 nodes, is a slow shader recipe).

| tool (Blender's name) | what it is, in one sentence | how this recipe uses it | settings that matter |
|---|---|---|---|
| **Node group** | a box of nodes with its own named sockets, used like one node | every layer is one box; the sockets are the bundle, Seed, Amount and the layer's settings | the socket names (fixed by `interface/interface.md`) |
| **Math** node | does one sum on numbers (add, multiply, minimum, greater than, floor, modulo, power, sine ...) | 1,479 of the 1,842 nodes (80 %): distances to edges, thresholds, ramps, per-slate sizes | the operation; "Clamp" to cut the result to 0..1 |
| **Map Range** | stretches a number from one range to another (Linear), or makes a soft step between two values (Smooth Step) | turning noise (which sits between about 0.25 and 0.73) into 0..1; soft edges of masks | From Min/Max, To Min/Max, Clamp, interpolation |
| **White Noise Texture** | gives a random number that is always the same for the same input | one set of random numbers per slate (fed `piece_id` and the layer's seed) and per row (fed the row number): slate tone, slate width, how damaged, how mossy | the input you feed it (1D/2D/3D/4D); nothing else |
| **Noise Texture** | a smooth random "cloud" of values | 1D noise for the pointed paint tongues; 2D/3D noise on the slate's own coordinates for drips, wobbles, chips, moss clumps; 4D noise for seamless patterns | Scale (how many features across), Detail (how many finer layers are added), Roughness (how strong the finer layers are), and the 4th coordinate W (a different pattern for the same place) |
| **seamless noise** (the project's group `tileable_noise_group` in `lib/recipe_tools.py`) | turns x into a circle and y into another circle and reads 4D noise there, so the right edge continues into the left | big sun-bleached and damp patches, where moss gathers, the shadow's ragged border, chips of the slate edge | Scale must be "features per base tile x Tile Count" so a 2 x 2 area has the same look per dot |
| **Voronoi Texture** | cuts space into cells around random points; F1 = distance to the nearest point, Smooth F1 = the same with soft borders | COLOUR AND FADE: tall flat patches of one tone (cells stretched up-down); MOSS: flat patches of one olive tone inside a clump | Scale, Randomness, the stretch of the coordinate you feed it |
| **Mix** (colour) | lays one colour over another by a factor 0..1 (the factor is the mask) | painting the layers over each other in COMBINE; the palette lookup in COLOUR AND FADE (a chain of "if the step is above this line take the next colour") | Factor; blend mode Mix |
| **Mix** (float) | the same for plain numbers | blending two noises (upright flakes and round flakes in DAMAGE) | Factor |
| **Separate / Combine XYZ**, **Separate Color** | split a vector or colour into its numbers, or join numbers into one | reading x and y of the tile coordinate; reading the 4 random numbers White Noise gives at once | none |
| **RGB to BW** | the brightness of a colour | the tints in COLOUR AND FADE (change hue, keep brightness); `combine.tone_blend` (height from the paint brightness) | none |
| **Cycles bake** (through `lib/bake_harness.py`) | photographs one output of the recipe from straight above, one map at a time | colour (view "Standard"), height (16 bit, view "Raw"), roughness, metallic; the normal is the slope of the height | 4 samples per dot (16 gives cleaner one-dot edges, see `tests/bake_tools.py`) |

Three facts about these tools that cost time (the research guides have more):
* Blender's own Noise, Voronoi, Wave and Magic textures do NOT repeat at the tile edge. Use the seamless group, or read them on the slate's own coordinates.
* Noise Texture values sit between about 0.25 and 0.73, not 0 and 1: always stretch with Map Range before you threshold.
* Colours typed as hex (#3d444a) are sRGB; Blender's nodes work in linear colour. The layer helper converts them (`srgb_hex_to_linear`).

## 4. The layers one by one

Each part: what it does (with a concrete example first), how it is built, the settings that matter most and what changing them does, and where
the "what does this setting do" strips are. Strips in `controls_sweeps/<layer>/` were made by the layer builders at their layer's own starting
values (before integration tuning); the strips in `controls_sweeps/whole_recipe/` (**made after the restart**) show five settings on the
finished, tuned recipe.

The five whole-recipe strips (`controls_sweeps/whole_recipe/*.jpg`, 768 dots, one setting changed at a time, the same crop of about two rows; the
colour group of each picture is written over it and kept in `colour_group_of_each_picture.json`). The scores of 768-dot bakes are lower than those of
1254-dot bakes (the default scores 0.632 at 768 and 0.701 at 1254, because the scorer enlarges a smaller picture to 1254 dots and that blurs it), so
compare the numbers within one strip only:

| strip | values (default in bold) | colour group at 768 dots | what you see |
|---|---|---|---|
| `moss_coverage.jpg` | 0, 0.12, **0.22**, 0.34 | 0.52, 0.57, **0.63**, 0.67 | no moss; a few drips; drips on about one slate in three; olive slates |
| `damage_chip_amount.jpg` | 0, 0.35, **0.65**, 1.0 | 0.56, 0.57, **0.63**, 0.62 | almost clean edges (the few tan dots left are lichen); then pale-tan flakes along more and more lower edges |
| `colour_and_fade_streak_contrast.jpg` | 0, 0.7, **1.4**, 2.1 | 0.60, 0.60, **0.63**, 0.75 | smooth fade only; flat streaks in more and more contrast |
| `colour_and_fade_mottle_tallness.jpg` | 0.6, **1.1**, 2.2, 4.0 | 0.61, **0.63**, 0.64, 0.61 | a small change at this crop: the flat patches inside a slate get longer up and down as the value grows |
| `outline_and_shadow_shadow_darkness.jpg` | 0, 0.3, **0.55**, 0.8 | 0.76, 0.74, **0.63**, 0.56 | no shadow band under the rows; a light one; the default; a heavy one |

![whole recipe: streak contrast](controls_sweeps/whole_recipe/colour_and_fade_streak_contrast.jpg)

![every layer alone: mask and colour](debug_views/overview_masks_and_colours.png)

*Every layer baked alone (`debug_views/`): left its mask, right its colour; top left the layout (one random colour per slate), top right the finished tile.*

### 4.1 LAYOUT (`layers/layout.py`) - the slates, no paint

*Example (made-up but typical numbers).* Take a dot at x = 0.31, y = 0.47 of the tile: LAYOUT finds it is in row 4 (counting rows from the top, rows are 1/8 of the tile high, each
with a slightly jittered edge), the row is slid sideways by its own random amount, the dot falls in the third of six slates, which is 0.171 wide;
the dot is 0.02 below the slate's top edge and 0.013 from its nearest edge, so `local_y` is about 0.17 and `edge_distance` 0.013.

*How it is built.* (1) Rows: row edges are jittered steps of an even grid, so the next row starts exactly where this one ends and the last row ends
where the first starts again (the tile repeats). (2) Each row slides by its own random amount. (3) Six random widths per row (log-normal: a bell
number put through exp), scaled so they add up exactly to the row length; every dot of the row works out the same widths without a loop.
(4) Joints lean a little. (5) Corners are rounded (bottom corners rounder than top ones, so the joints flare into the band between rows) and the
four edges are pushed IN by seamless noise (chips only remove slate), a different noise for every slate. (6) From the four edge distances come
the bundle numbers.

| setting | default | what changing it does |
|---|---|---|
| `layout.rows_per_tile`, `layout.slates_per_row` | 8, 6 | how many rows and slates per tile (whole numbers; 6 and 4 give the "big slates" variation) |
| `layout.width_spread` | 0.26 | 0 = all slates equally wide; higher = more different widths (0.35 in the "big slates" variation; range up to 0.8) |
| `layout.row_slide` | 1 | 0 = every row starts at the same joint (a stack bond); 1 = rows slid anywhere |
| `layout.row_gap`, `layout.joint_width` | 0.005, 0.0014 | narrowest band between rows (6 dots) and between slates (1.8 dots); chips widen them |
| `layout.ragged_bottom`, `ragged_side`, `ragged_top` | 0.0055, 0.0024, 0.0022 | how deep the chips bite into each edge (7, 3, 2.8 dots) |
| `layout.corner_radius`, `corner_bottom_factor` | 0.0064, 1.5 | corner rounding (8 dots) and how much rounder the bottom corners are |
| `layout.seed` | 1 | a new roof: widths, slides, leans and chips change, nothing else |

Debug views: `debug_views/layout_slates_colour.png` (one random colour per slate) and `debug_views/skeleton_layers_sheet.png`, `debug_views/bundle_sheet.png`
(every bundle number as grey). Layout statistics (slate widths, row heights, joint share 7.5 % against the reference's 7 %): `tests/layout_stats/layout_statistics.md`.

### 4.2 COLOUR AND FADE (`layers/colour_and_fade.py`) - the bare slate paint, the bottom layer

*Example (made-up but typical numbers).* One slate rolls a base tone step of 3.4 (on a palette of nine blue-greys numbered 0 = darkest to 8 = lightest). Near its top edge a
dark tongue hangs down and takes away 1.2 steps; a tall flat patch adds 0.6; no speck; the slate sits in a sun-bleached area that adds 0.5. The
sum is 3.3, ROUNDED to 3, so the dot gets palette colour number 4 (#33393e). Rounding is what makes the paint flat: a dot is never "between" two
paints, so the picture is made of flat patches with hard edges, like a painting.

*How it is built.* The tone step is a sum: the slate's own base tone (from `piece_id`; a few slates are pushed clearly darker or lighter: the
"outliers") + pointed tongues (rows of 1D noise turned pointy with `1 - |2n - 1|`; dark tongues hang from the top edge, pale bleached tongues
reach up from the bottom edge) + mottling (tall flat patches from stretched Smooth F1 Voronoi cells) + specks + big sun-bleached and damp patches
that cross slates (seamless noise cut by thresholds) + a slow drift. The palette lookup is a chain of Mix nodes, so every palette colour stays a
live colour knob. Some slates and patches lean towards a green-grey or a warm grey (hue only, lightness kept), and a faint grain keeps flat patches
from being perfectly flat. Height follows the tone (lighter paint higher, like the reference maps); roughness: lighter rougher, darker smoother.

| setting | default (tuned) | what changing it does | strip |
|---|---|---|---|
| `colour_and_fade.tone_1` ... `tone_9` | #141719 ... #616b70 | the nine paint colours; changing them recolours the whole roof (the brick reuse test uses nine brick reds) | `tint.png` |
| `tone_centre` | 3.7 | the tone step of the average slate: lower = a darker roof | `tone_centre.png` |
| `tone_spread`, `outlier_share`, `outlier_size` | 1.0, 0.15, 1.2 | how different slates are; how many slates stand out and by how much | `tone_spread.png` |
| `fade_amount`, `fade_direction`, `fade_length` | 0.85, 1, 0.07 | how strong the tongues are; 1 = dark above and bleached below (as on the reference), -1 = the reverse; how long the longest tongue is (88 dots) | `fade_amount.png`, `fade_direction.png`, `fade_length.png` |
| `streak_width` | 0.014 (was 0.034) | width of one tongue (18 dots): narrower = finer streaks | `streak_width.png` |
| `streak_contrast` | 1.4 | how much neighbouring patches differ (0 = smooth fade only) | `streak_contrast.png` and the whole-recipe strip |
| `streak_bend` | 0.006 | slow sideways wander of the streaks (0 = ruler-straight) | `streak_bend.png` |
| `mottle_tallness` | 1.1 (added in integration; was a fixed 2.2) | how much taller than wide the flat patches are: 2.2 = patches the whole slate high (slates look like corrugated stripes), 1.1 = shorter strokes | whole-recipe strip |
| `patch_hardness` | 1 | 1 = flat patches with hard edges; 0 = the tones blend smoothly (the "airbrushed" look the brief does NOT want) | `patch_hardness.png` |
| `bleach_amount`, `stain_amount`, `patch_size` | 0.25, 0.4, 0.2 | big pale (sun) and dark (damp) areas crossing slates, and their size | `sun_bleach.png`, `damp_stain.png` |
| `tint_amount`, `tint_green_share` | 0.7, 0.8 | how far some slates lean green or warm, and which | `tint.png` |
| `amount` | 1 | 0 = every slate one flat middle tone, nothing else | `amount.png` |

The colour builder's own tests: `tests/colour_and_fade/layer_tests_table.md`; its controls page: `tests/colour_and_fade/controls_colour_and_fade.md`.

### 4.3 DAMAGE (`layers/damage.py`) - chips, cracks, the pale tan breaks

*Example (made-up but typical numbers).* Take a dot 0.012 above the lower edge of a slate. The "reach" of flaking there is 0.02 (the lower edge flakes most; sides reach only 12 % of
that, the top edge less still) times this slate's own damage level (some slates barely touched) times a seamless noise that is high here. The reach
works out to 0.018, which is more than the dot's distance to the edge (0.012), so the dot is flaked: it gets the tan break colour, it is sunk by
about 0.05 and made rougher. Two noises are blended: one stretched up-down (flakes are teeth pointing up from the edge, like the reference) and one
round (loose islands above the edge).

*Kinds of damage, in painting order*: flakes (pale cream at the edge, tan above, darker brown at the tips), pits, scratches, cracks (thin dark lines
from an edge, thinner towards the tip), notches (small dark bites), corner breaks (a lower corner gone). Every kind sinks the surface and makes it rougher.

| setting | default (tuned) | what changing it does | strip in `controls_sweeps/damage/` |
|---|---|---|---|
| `damage.chip_amount` | 0.65 | how much of the lower edges is flaked (0 = none, 1 = almost all) | `strip_1_edge_flakes.png`, whole-recipe strip |
| `chip_depth` | 0.02 | how far a flake reaches in (25 dots) | strip 1 |
| `chip_frequency` | 110 | flake teeth per tile: more = smaller teeth (110 = about 11 dots) | strip 1 |
| `chip_clustering`, `chip_breakup` | 1.0, 1.1 | flakes gathered in stretches with clean edge between; how ragged the flaked patches are | strip 1 |
| `slate_variation` | 0.7 | 0 = every slate equally damaged; 1 = some clean, some badly hurt | `strip_4_where_and_how_big.png` |
| `crack_amount`, `scratch_amount`, `pit_amount` | 0.02, 0.03, 0 | chance of a crack / scratch per slate, share of pits (turned almost off in tuning: the reference has very few) | `strip_2_cracks_scratches_pits.png` |
| `notch_amount`, `corner_break_amount` | 0.1, 0 | bites and broken corners | `strip_3_corners_notches_colours_amount.png` |
| `break_colour`, `break_colour_light`, `break_colour_dark` | #7c6f5d, #8f8d85, #5a4f43 | the tan, the pale and the dark-tan of the breaks | strip 3 |
| `sink_depth`, `roughness_gain` | 1, 1 | how deep damage is sunk, how much rougher it is | |

The damage builder's controls page with every setting: `damage_work/damage_controls.md`.

### 4.4 MOSS (`layers/moss.py`) - moss and lichen, in drips

*Example (made-up but typical numbers).* Take a dot 0.03 below a slate's upper edge, in a sideways place where this slate's drip strand is long (0.2 instead of the average 0.14):
the "drips" rule gives it 0.8 x drip preference 0.9 = 0.72; the clump noise adds 0.3; the slate is a mossy one and lies in a mossy area of the
roof, which lowers the threshold. The growth strength is above the threshold, so the dot is moss; it lies inside the clump, so it gets one of the
middle olive tones (the rim of a clump is lighter, the part right under the upper edge darker).

*How it is built.* A growth strength per dot = the RULES (where water and shade gather: drips running down from the upper edge, the upper part of
the slate, the side joints, the lower part, low damp spots read from `base_height`, and, through the declared link, damage) + a tall wobbly CLUMP
noise read on the slate's own coordinates + EDGE RAGGEDNESS noise. Moss is painted where the strength is above a threshold set by `coverage`; a very
slow seamless noise (`patchiness`) times each slate's own "how mossy am I" number (`slate_variation`) moves the threshold up in clean areas and
down on mossy slates. Clumps are tall (drip stretch 1.8), wander sideways as they run down (flow wobble), and grow downward teeth one brush-stroke
wide (fringe). Paint: five flat olive tones in tall patches (stretched Voronoi), no smooth shading. Lichen: small pale-tan discs and rings on two
jittered grids, gathered in colonies.

*Why it reads as drips and not as camouflage* (the weakness of the first slate build): clumps start at each slate's own upper edge, are taller than
wide, and their lengths change from strand to strand; the earlier build placed round blobs anywhere. Compare `controls_sweeps/moss/04_drip_length.png`
and `07_clump_strength.png` (clump strength 3 = free blobs everywhere: the camouflage look).

| setting | default (tuned) | what changing it does | strip in `controls_sweeps/moss/` |
|---|---|---|---|
| `moss.coverage` | 0.22 | how much moss: 0 = none, 0.34 = a damp roof | `01_coverage.png`, whole-recipe strip |
| `patchiness`, `slate_variation` | 0.75, 0.95 | moss gathered in a few big areas; some slates thick with moss, others clean | `02_patchiness_and_slate_variation.png` |
| `drip_preference`, `joint_preference`, `lower_preference`, `damp_preference` | 0.9, 0.15, 0.25, 0.3 | WHERE moss gathers: drips under the upper edge (strongest), along joints, low on the slate, in damp low spots | `08_where_it_gathers.png` |
| `drip_length`, `drip_width` | 0.14, 0.07 | how far drips run (175 dots) and how wide a strand is (88 dots) | `04_drip_length.png`, `05_drip_width_and_stretch.png` |
| `cluster_size`, `clump_strength`, `drip_stretch` | 0.06, 1.8, 1.8 | clump width; how much the free clump noise decides (high = blobs); how much taller than wide | `06_cluster_size.png`, `07_clump_strength.png`, `05_...` |
| `edge_raggedness`, `fringe_amount` | 0.7, 0.3 | ragged clump edges with loose flecks; downward teeth | `10_edge_raggedness.png`, `09_flow_wobble_and_fringe.png` |
| `tone_1` ... `tone_5`, `tone_centre`, `tone_spread` | #2b2c23 ... #545342, 0.7, 1.0 | the five olives; which is typical; how many one clump uses | `11_tone_centre.png`, `12_tone_spread_rim_and_shade.png` |
| `lichen_amount`, `lichen_size` | 0.15, 0.0042 | how many pale-tan lichen discs, their size (5 dots) | `13_lichen_amount.png`, `14_lichen_size_and_clustering.png` |
| `damage_avoid`, `damage_attract` | 0.8, 0 | the declared link: keep off damaged dots / grow on them (section 5) | `17_damage_avoid.png`, `17b_damage_attract.png` |
| `raise`, `roughness_gain` | 1, 1 | moss raises the surface by 0.035 and adds 0.14 roughness | `18_height.png`, `19_roughness.png` |

The moss builder's controls page: `moss_work/moss_controls.md`.

### 4.5 OUTLINE AND SHADOW (`layers/outline_and_shadow.py`) - the drawing, painted last

*Example (made-up but typical numbers).* Take a dot 0.01 below a slate's upper edge: the shadow of the slate above reaches 0.026 down here (a
little more or less where the ragged noise says so); the dot is 40 % of the way into that reach, so its depth is 0.6, which is rounded UP to the
next of four flat steps (1, 0.75, 0.5, 0.25): 0.75. The shadow colour covers the slate paint by 0.55 x 0.75 = 0.41: the paint still shows through.

Five things, laid over each other like paint: edge darkening (6 dots next to every edge), the shadow band under the row above (four flat steps with
a drip-like ragged lower border, plus a few teeth of solid black), the pale lip along the lower edge, the thin side outline, and the near-black
joints with a hand-drawn ragged edge. Relief: the shadow band is a slope out of the joint, the lip a small rim, the side outline a groove.

| setting | default (tuned) | what changing it does | strip in `controls_sweeps/outline_and_shadow/` |
|---|---|---|---|
| `outline_and_shadow.shadow_width`, `shadow_darkness` | 0.026, 0.55 | how far the shadow reaches (33 dots) and how dark it is right under the joint | `strip_2_shadow_band.png`, whole-recipe strip |
| `shadow_tiers`, `shadow_drip` | 4, 0.5 | number of flat steps (0 = smooth blur); how ragged its lower border is | strip 2 |
| `black_drips` | 0.005 | how far black teeth hang from the band (6 dots) | strip 2 |
| `lip_brightness`, `lip_width`, `lip_breakup` | 0.12, 0.003, 0.4 | the pale lower lip: strength, width (4 dots), how broken | `strip_3_lip_edges_and_amount.png` |
| `joint_colour`, `side_outline_width`, `wobble` | #0e0f11, 0.002, 0.5 | joint black; thin outline (2.5 dots); how hand-drawn the lines are | `strip_1_joints_and_outlines.png` |
| `shadow_height`, `lip_height`, `outline_height` | 0.12, 0.04, 0.05 | the relief this layer adds | `strip_4_relief_height.png` |

The outline builder's controls page: `outline_work/outline_controls.md`; its look comparisons: `controls_sweeps/outline_and_shadow/looks.png`.

### 4.6 COMBINE (`layers/combine.py`)

Stacks the colours by mask in the stack order, sums heights and roughness, and offers four settings: `combine.base_roughness` (0.8), `combine.metallic` (0),
`combine.height_gain` (1) and `combine.tone_blend` (0.7, added in integration, section 5).

## 5. The declared link, the stack order and the height choice

**The one declared link: MOSS reads DAMAGE's mask** (`moss.damage_avoid`, default 0.8; `moss.damage_attract`, default 0). Listed in
`layers/moss.py` (`DECLARED_LINKS`), in `interface/interface.md` section 5, and allowed for in the independence table.

What it really does, measured **after the restart** (`links_and_order/`, 768 dots):
* In the COLOUR picture it changes nothing with the default stack order: damage_avoid 0, 0.8 and 1 give identical colour pictures (0.00 % of dots
  differ by more than 10 steps), because DAMAGE is painted over MOSS anyway, so a break always shows its own colour. (Sheet: `links_and_order/links_sheet.jpg`, top row.)
* In the HEIGHT map it keeps moss from filling the chips: between damage_avoid 0 and 1, 0.67 % of the dots differ, every one of them on a damaged
  dot, by up to 0.044 of the height scale (moss would otherwise raise the floor of a chip). Roughness did not change by more than 0.004 anywhere
  (`links_and_order/link_height/link_measures.json`).
* Turned the other way round it is visible: with the stack order `colour_and_fade, damage, moss, outline_and_shadow` and `moss.damage_attract` 0.8,
  moss grows over the old breaks and hides them (bottom right of the sheet; 1.6 % of dots change).

So the link is honest but small. A person who wants "moss grows next to old damage" must also change the stack order; "moss right NEXT to damage
but not on it" is not possible, because the link is read dot by dot.

![the declared link and the stack order](links_and_order/links_sheet.jpg)

**The stack order** (`recipe.stack_order`) only decides who paints over whom; heights and roughness are plain sums, so they do not depend on it.
The default `colour_and_fade, moss, damage, outline_and_shadow` means: moss grows on the paint, damage breaks through moss, the drawing is last.

**The height choice** (`combine.tone_blend`, added during integration). The reference height map was made from the brightness of its colour picture
(height = 2.5 x (brightness - 9.5), research finding), so in it a pale chip is HIGH. Real relief, which every layer writes, makes a chip LOW. The
setting mixes the two: 0 = real relief only (chips sunk, moss raised, joints low); 1 = height = brightness of the finished colour (the reference's
rule); the default is 0.7. Height pictures: `links_and_order/tone_blend_sheet.jpg` (640 dots: reference, 0, 0.35, 0.7, 1). Same-kind height group
(1254 dots, measured by the first integrator's round 13 and re-scored by me before deleting the pictures): 0.4 gives 0.505, 0.7 gives 0.654, 1 gives 0.629.
**Honest note**: the brief asked for the height to be the sum of the layers' real relief. The default keeps 30 % of it; set `combine.tone_blend` 0
for pure real relief (the normal map then shows sunk chips and raised moss, and the same-kind height score drops).
Note that even at 0 the height still looks "painted": COLOUR AND FADE writes a small relief that follows its own tone (`colour_and_fade.tone_height`).

![tone blend](links_and_order/tone_blend_sheet.jpg)

## 6. How it was tuned (no fitting) and why I kept the tuning

**The method.** The reference was looked at and measured ONCE for its general character (palette range, shares of olive, tan and very dark dots,
the top-to-bottom rise inside a slate, joint and shadow widths; scripts `integration/colour_character.py`, `tests/colour_and_fade/measure_reference_character.py`,
`damage_work/measure_reference_tan.py`, `moss_work/measure_reference_moss.py`, `outline_work/measure_reference_profile.py`). After that the only
method was hand-tuning: bake the colour at 1254 dots for two or three variants (`integration/look.sh`), put a crop next to the same crop of the
reference (`integration/side_by_side.py`), score the colour group (`integration/score_colour.sh`), change one or two settings, repeat. A few small
measuring scripts answered single questions (`variance_split.py`: how much of the brightness variation is "the same along a whole row";
`sideways_bands.py`: at which sizes the paint varies sideways; `row_profile.py`: average brightness of every picture row; `low_bins.py`: power at the
largest sizes; `share_olive.py`). No optimiser, no per-slate data.

**The rounds** (reconstructed from the first integrator's round files `integration/r*_views.json`, because its notes were lost in the restart;
scores where they were recorded or where I could re-score the pictures):

| round | what was tried (the variants) | what was kept |
|---|---|---|
| 1 | all four layers at their builders' starting values | baseline: overall 0.615, colour 0.619, height 0.516, normal 0.608 |
| 2 | narrower, bent streaks (`streak_width` 0.024, `streak_bend` 0.008, `streak_contrast` 1.6); more slate-to-slate tone (`tone_spread` 0.9, outliers 15 %); fewer cracks, pits, corner breaks and bites; a lighter, narrower shadow (0.55, 0.026); moss coverage 0.3 against 0.4 | the shadow, the outliers |
| 3 | `tone_spread` 0.75; moss coverage 0.16 / 0.2 and where it gathers (drips against joints and lower part) | moss mostly in drips |
| 4 | `streak_width` 0.014 / 0.011 / 0.016, `streak_contrast` 1.4, `streak_bend` 0.006, `tone_centre` 4.0, `fade_amount` 0.85, `fade_length` | streaks 0.014 wide, contrast 1.4, bend 0.006, fade 0.85 |
| 5 | damage: no pits, no corner breaks, fewer bites (0.1), `chip_amount` 0.7, `slate_variation` 0.5; `bleach_amount` 0.35 | pits and corner breaks off, bites 0.1 |
| 6 | NEW setting `colour_and_fade.mottle_tallness` (1.0 / 0.6; was fixed at 2.2, slates looked like corrugated stripes); `streak_contrast` 1.9 | the new setting |
| 7 | `tone_centre` 3.7, `mottle_tallness` 1.1 | both |
| 8 | `tone_spread` 1.0 / 1.2 / 0.9 with drift, bleach and damp variants | `tone_spread` 1.0 |
| 9 | grain 0.12 against 0.05; `tone_spread` 0.7 against 1.0 | grain 0.05, spread 1.0 |
| 10 | shadow 0.5 dark / 0.032 wide against 0.55 / 0.026 | 0.55 / 0.026 |
| 11 | moss coverage 0.18 against 0.22 (and drip width 0.06 / 0.07); stronger green tints | coverage 0.22: colour group 0.701 against 0.664 at 0.18; the stronger tints scored 0.658 and were dropped |
| 12 | height only: `tone_height` 3.5, deeper damage, higher moss | the starting values |
| 13 | height only: NEW setting `combine.tone_blend` 0.4 / 0.7 / 1.0 | 0.7 (height group 0.505 / 0.654 / 0.629) |
| 14 (mine, after the restart) | prompted by the whole-recipe strips: `outline_and_shadow.shadow_darkness` 0.3; `colour_and_fade.streak_contrast` 2.1; both; milder both (0.4 and 1.8); then default against the milder pair on two more seed sets | nothing: see below (`integration/r14_results.json`) |

Between rounds 2 and 11 the first integrator also set, by hand, the three lightest palette colours, the flake size and breakup, the moss clump size
and edges, the lichen amount, the lip and the black drips (all in `recipe/settings.json`; `integration/settings_before_integration.json` is the start).
Every edit to a layer file is listed in `integration/CHANGES_TO_LAYER_FILES.md` (two: the two new settings above; both keep the old look at their
starting value, so nothing else moved).

**When to stop.** The last change to the colour (round 11 to 12: `damage.crack_amount` 0.03 to 0.02) changed NO dot of the colour picture (mean
difference 0.00), and rounds 12 and 13 changed only the height. By the brief's rule (stop when two further rounds each change the look by less than a
person would notice) the colour look had converged.

**Round 14 (mine) and why it changed nothing.** The whole-recipe strips (section 4, 768 dots) showed two settings that raise the colour group a lot:
a lighter shadow band and stronger streaks. At 1254 dots with the default seeds: shadow darkness 0.3 gave 0.766, streak contrast 2.1 gave 0.793,
both together 0.750, a milder pair (shadow 0.4, streak contrast 1.8) 0.796, against 0.701 for the default. That looked like the brief's 0.8 within
reach. But almost all of the gain was the feature-size measure (`colour_scale`, a cliff, see the Lessons guide), and when I baked the default and
the milder pair on two other sets of seeds the default scored 0.769 and 0.753 and the milder pair 0.780 and 0.758: a gain of 0.005 to 0.011,
smaller than what the seed alone moves. **The default seeds are simply an unlucky draw** (0.701, the lowest of five seed sets; the five average 0.740).
By eye the milder pair is at least as close to the reference (lighter shadow band, more contrasted streaks; `integration/looks/r14/crop_reference_default_r14d_r14b.png`),
so it is offered as a choice: `--params '{"outline_and_shadow.shadow_darkness": 0.4, "colour_and_fade.streak_contrast": 1.8}'`. I did not make it the
default, because that would have meant re-baking every result in this folder for a gain smaller than the seed noise.

![round 14: reference, default, milder pair, stronger streaks](integration/looks/r14/crop_reference_default_r14d_r14b.png)

**What I checked before keeping it** (after the restart): the side-by-side above and crops at 1.4 x (`integration/takeover/crop_ref_vs_default.png`);
the brightness bands (share of dots 30-50 / 50-70 / 70-90 / 90+ of 255: reference 15.9 / 40.5 / 26.9 / 5.5 %, default 17.9 / 41.4 / 25.0 / 4.7 %);
the mean colour of the olive-or-tan dots (reference 72, 72, 58; default 72, 70, 57: the same); the mean Lab colour (25.2, -1.6, -1.0 against
25.1, -1.8, -1.0). What differs, and why I did not change it:
* **More moss and tan than the reference**: by the same simple colour rule 15.1 % olive-or-tan dots against 10.7 %, and 5.3 % pale-tan against 2.6 %.
  The score prefers it (moss coverage 0.18 scored 0.664, 0.22 scores 0.701). A person who prefers the reference's amount: `moss.coverage` 0.18.
* **The tan breaks gather on a few slates** in bigger patches; on the reference small tan flecks run along almost every lower edge. Settings to try:
  lower `damage.slate_variation` and `damage.chip_clustering`, raise `damage.chip_frequency`.
* **The moss clumps are solid**; on the reference the olive is partly a cast over the streaks.
None of these is a fault of the recipe: they are taste, each has a setting, and changing the defaults now would have meant re-baking every result
in this folder (about two hours of CPU). They are listed as known gaps (section 9).

## 7. Results

### 7.1 The default tile against the reference (a guide, not a target)

Baked by the first integrator at 1254 dots through the harness (`outputs/default/`); scores read from `outputs/default/score_same_kind.json`
and `score_pixel_for_transparency.json`; I re-scored the colour picture after the restart and got the same colour group (0.701).

| same-kind measure | score | in plain words |
|---|---|---|
| **overall** | **0.705** | |
| colour group | 0.701 | the brief's aim was 0.8 or more: **not reached** |
| - colour distribution | 0.926 | the same colours in the same amounts |
| - colour spectrum | 0.609 | how much variation there is at each size |
| - colour orientation | 0.630 | which way the edges run |
| - colour scale (feature size) | 0.452 | how far the picture stays similar to itself sideways: 258 dots on ours, 64 on the reference: our rows are more alike along their length |
| - colour gradient | 0.753 | how sharp the edges are |
| height group | 0.654 | with `combine.tone_blend` 0.7 (section 5) |
| normal group | 0.671 | the normal made by the harness (strength fitted to 7.37; the reference's is 7) |
| tiling | 1.0 | seamless |

**The default seeds are an unlucky draw for this score**: the same settings with four other seed sets score 0.710 to 0.769 on the colour group
(mean of all five 0.740; section 7.3).

Mean colour (Lab): reference 25.2, -1.6, -1.0; default 25.1, -1.8, -1.0. Height follows colour with correlation 0.987 (reference 0.993).

The dot-for-dot numbers, **for transparency only** (these are new slates, so they cannot match dot for dot): colour mean difference 10.5 (Delta E),
structure (SSIM) 0.53, edge skill 0.17, height error after best fit 37.7 steps of 255, normal error 16.9 degrees; tier "none". The first slate build,
which traced the reference, reached tier "close"; this build is not meant to.

### 7.2 What each layer buys (the ladder, **finished and scored after the restart**)

`ladder/ladder_table.md`, sheet `ladder/ladder_sheet.jpg` (the same crop of every rung next to the reference). 1254 dots, same seeds.

| rung | what is in the picture | colour group | of which: feature size | height group | overall |
|---|---|---|---|---|---|
| 0 | layout and joints, every slate one flat colour | 0.322 | 0.065 | 0.371 | 0.402 |
| 1 | + colour and fade | 0.480 | 0.000 | 0.598 | 0.570 |
| 2 | + moss | 0.636 | 0.369 | 0.632 | 0.656 |
| 3 | + damage (the default tile) | 0.701 | 0.452 | 0.654 | 0.695 |
| - | the default WITHOUT outline and shadow | 0.567 | 0.489 | 0.367 | 0.539 |

(The overall here uses a normal made by `integration/score_set.py`, so rung 3 shows 0.695 instead of the harness's 0.705.) Every layer raises the
colour group; the drawing layer is worth most (without it the colour group drops by 0.13 and the height group by 0.29).

![the ladder](ladder/ladder_sheet.jpg)

### 7.3 Seeds and settings variations

Eight tiles from eight settings variations, 1254 dots each, contact sheet with each tile's settings written under it: `variations/contact_sheet.png`
(settings in `variations/variations.json`). Colour group of each against the reference:

| variation | what changed | colour group |
|---|---|---|
| v1 new seeds | five new seeds, same settings | 0.765 |
| v2 more moss | coverage 0.34, more lichen, moss on more slates | 0.760 |
| v3 heavily damaged | deep flakes on every lower edge, cracks, scratches, pits, bites, broken corners | 0.733 |
| v4 faded and sun-bleached | long fade, big bleached areas, lighter slates, little moss | 0.554 |
| v5 fresh and clean | even tone, hardly any weathering, no moss | 0.463 |
| v6 dark and wet | dark slates, big damp patches, rougher | 0.550 |
| v7 pale and old | pale warm-grey slates, flaked edges, lots of lichen | 0.544 |
| v8 big slates | 6 rows of 4 slates instead of 8 of 6 | 0.746 |

![eight variations](variations/contact_sheet.png)

The low scores of v4 to v7 are expected: they are meant to be DIFFERENT roofs from the reference (a fresh roof should not score like a mossy old one).
The seed alone moves the score. The default settings with five different sets of seeds (the default tile, v1, and three more baked after the
restart: `variations/seed_spread/seed_spread.json`, small pictures `seeds_b/c/d_colour_small.jpg`) score 0.701, 0.765, 0.769, 0.753 and 0.710:
mean 0.740, spread 0.068. The default tile has the lowest of the five. A difference of less than about 0.07 between two single bakes with
different seeds therefore says nothing.

### 7.4 Independence (every layer, Amount 0 and Seed + 1)

`tests/independence_full/independence_table.md` (384 dots; pictures `independence_sheet.png` and `<layer>_<variant>_where.png`, which show in
white where the finished picture changed). A dot counts as changed when the colour moves by more than 1 step of 255, the height by more than 0.0005 or
the roughness by more than 0.004.

| layer changed | variant | its own region (% of dots) | colour changed % | ... of which OUTSIDE its region | height changed % (outside) | roughness changed % (outside) |
|---|---|---|---|---|---|---|
| layout | Seed + 1 | 100 | 96.9 | 0.0 | 97.9 (0.0) | 92.2 (0.0) |
| colour and fade | Amount 0 | 95.0 | 74.8 | 0.0 | 93.2 (0.0) | 78.3 (0.0) |
| colour and fade | Seed + 1 | 95.0 | 76.0 | 0.0 | 93.7 (0.0) | 85.0 (0.0) |
| damage | Amount 0 | 5.3 | 4.9 | 0.0 | 5.1 (0.0) | 4.6 (0.0) |
| damage | Seed + 1 | 10.0 | 9.0 | 0.0 | 9.4 (0.0) | 8.1 (0.0) |
| moss | Amount 0 | 19.9 | 18.4 | 0.0 | 19.4 (0.0) | 19.2 (0.0) |
| moss | Seed + 1 | 39.3 | 35.9 | 0.0 | 38.2 (0.0) | 34.2 (0.0) |
| outline and shadow | Amount 0 | 37.4 | 35.9 | 0.0 | 36.9 (0.0) | 33.0 (0.0) |
| outline and shadow | Seed + 1 | 41.1 | 29.0 | 0.0 | 34.3 (0.0) | 19.4 (0.0) |

Other layers' own masks: when DAMAGE changes, the MOSS mask changes on 0.92 % (Amount 0) and 1.57 % (Seed + 1) of the dots, all inside the damage
region: that is the declared link. Every other cross entry is exactly 0. A layer's "own region" is where its mask is above 0 before or after the change
(for COLOUR AND FADE, the bottom layer, every slate dot; for LAYOUT everything).

![independence](tests/independence_full/independence_sheet.png)

### 7.5 Seamless (the half-tile test)

`tests/half_tile_layers/half_tile_table.md` (512 dots; the recipe's `shift` parameter slides everything by half a picture). Mean difference in
steps of 255; "control" = the same comparison with the picture rolled 7 dots too far, which must differ a lot.

| tiles across | picture | raw mean difference | after a 2-dot blur | control (blurred) |
|---|---|---|---|---|
| 1 | finished colour | 1.83 | 0.34 | 16.3 |
| 1 | finished height | 2.55 | 0.49 | 30.9 |
| 1 | moss mask | 2.42 | 0.74 | 37.2 |
| 1 | damage mask | 1.05 | 0.34 | 12.5 |
| 2 | finished colour | 2.81 | 0.52 | 17.9 |
| 2 | colour against itself rolled by ONE base tile (must differ: new content) | 24.3 | 16.8 | |

The raw differences are the noise of Cycles' 4 samples on one-dot edges (they vanish under a 2-dot blur); the controls are 35 to 60 times larger. The
tile and the 2 x 2 area both wrap exactly, and the 2 x 2 area is new content, not a copy.

### 7.6 A bigger area of new slates (`recipe.tiles_across`)

**2 x 2 (2508 dots)**, `area/area_2x2/` (baked by the first integrator; measures in `area_measures.json`; 522 seconds for colour and height):
* Seams: the jump across the line where a base tile would end is 0.78 (columns) and 0.58 (rows) times a normal jump between neighbouring dots;
  ordinary columns have a median of 0.96 and rows 0.74. So the base-tile lines are no different from any other line: no seam. (The reference tile
  itself has 1.7 to 2.5 at its own wrap edge.)
* Repeats: the correlation of the area with itself shifted by one base tile is 0.44 / 0.29 / 0.27 (x / y / diagonal); a real copy gives 1.0; shifts
  that are NOT a base tile give 0.45 / 0.12 / -0.07 / 0.29 (the background level of a roof with rows). Only 18 to 21 % of dots are nearly equal one
  base tile away (a copy: 100 %).
* Same look per dot: each 1254-dot quarter scores 0.701 / 0.751 / 0.705 / 0.752 on the colour group (the default tile 0.701).
* Pictures: `area_overview.png` (the area shrunk) and `new_area_against_copied_tile.jpg` (next to the default tile copied 2 x 2).

![2 x 2 area of new slates](area/area_2x2/area_overview.png)

**4 x 4 (5016 dots, colour only), baked and measured after the restart**, `area/area_4x4/` (1595 seconds, 27 minutes, on 2 threads; another bake
ran beside it for the first two minutes; the colour picture is 31 MB):
* Seams: the jump across the three base-tile lines is 1.07, 1.14 and 0.90 (columns) and 0.66, 0.72, 0.67 (rows) times a normal jump; ordinary
  columns have a median of 0.98 (90 % of them below 1.15) and ordinary rows 0.74. The base-tile lines are ordinary lines: no seam.
* Repeats: correlation with itself one base tile away 0.42 / 0.34 / 0.33 (x / y / diagonal), a real copy 1.0, shifts that are not a base tile
  0.43 / 0.13 / -0.07 / 0.29. The 0.34 straight down is the rows lining up (one base tile is exactly 8 rows), not a repeat: only 19 to 21 % of dots are
  nearly equal one base tile away (a copy: 100 %), and the 16 base tiles differ from the first by 8.3 to 9.7 brightness steps on average.
* Same look per dot: the four 1254-dot quarters of the top-left 2 x 2 score 0.768 / 0.762 / 0.717 / 0.748 on the colour group (the default tile 0.701;
  section 7.3: the seed alone moves this score by about 0.07).
* By eye (`area_overview.png`, the whole area shrunk to 1254 dots): one continuous roof, no visible repeat, no lines at the tile edges.
  `new_area_against_copied_tile.jpg` puts it next to the default tile copied 4 x 4, where the repeat is easy to see.

![4 x 4 area of new slates, shrunk](area/area_4x4/area_overview.png)

### 7.7 Resolution (the same settings at 512, 1254 and 2508 dots)

`resolution/whole_recipe/` (512 and 1254 baked by the first integrator; **2508 re-baked after the restart**, which had cut it off after the colour).

| bake | colour + height + roughness, seconds | load on the machine |
|---|---|---|
| 512 dots | 35 | about 4 (another bake running beside it) |
| 1254 dots | 179 | about 4 |
| 2508 dots | 1088 | about 4 (another bake running beside it for most of the time) |

Same look? The bigger bake shrunk to the smaller size, compared dot by dot (`resolution_differences.json`):

| bigger -> smaller | colour mean difference (of 255) | height mean difference | dots more than 40 steps apart |
|---|---|---|---|
| 2508 -> 1254 | 1.0 | 1.1 | 0.000 % colour, 0.001 % height |
| 1254 -> 512 | 1.7 | 2.4 | 0.000 %, 0.010 % |
| 2508 -> 512 | 1.6 | 2.2 | 0.001 %, 0.007 % |

The same slates, streaks, moss and chips at every size; the bigger bakes only draw edges and specks with more dots
(`same_crop_at_three_sizes.png`, `whole_tile_at_three_sizes.png`). Time grows a little faster than the number of dots (4 times the dots from
1254 to 2508 took 6 times as long, but under a shared machine; not measured on a quiet one).

Baking the same settings twice gives the same picture dot for dot: the 1254-dot resolution bake and `outputs/default` were made separately and
differ by 0 in colour, height and roughness (checked after the restart).

![the same crop at 512, 1254 and 2508 dots](resolution/whole_recipe/same_crop_at_three_sizes.png)

### 7.8 Reuse on another layout (brick)

See section 8 of the Lessons guide for what had to change (a 40-node brick layout and 53 settings; no line of any layer file) and
`reuse/reuse_sheet.png`. **After the restart** I also ran one settings-only round on the brick (`reuse/settings_round_2/`, 768 dots, colour only):
redder bricks and light mortar made it read much more like a brick wall (colour group against the brick reference 0.154 to 0.19); `fade_direction` 0
did NOT remove the slate-like pointed tongues, and soot made with the damp-stain setting hardly shows.

![the layers on a brick layout](reuse/reuse_sheet.png)

![one settings-only round on the brick](reuse/settings_round_2/brick_settings_round_2.jpg)

### 7.9 Time

Building the node tree takes about half a second. At 1254 dots one map of the full recipe takes about 60 to 70 seconds on 2 threads (colour 69 s,
height 65 s, roughness 56 s in the default bake); the layout with empty layers took 13 to 16 seconds per map (`tests/timing.json`). The four layers
cost about 50 seconds per map together. A 2 x 2 area (2508 dots, colour and height) took 522 s; the 4 x 4 area (5016 dots, colour only) 1595 s.

## 8. Tested, not tested

**Tested (ran it, numbers above):** every layer alone (debug views of mask, colour, height and roughness, `debug_views/`); the whole recipe at 512,
640, 768, 1254, 2508 and 5016 dots; Amount 0 and Seed + 1 for every layer; the half-tile test for one tile and a 2 x 2 area and for every layer's mask;
eight settings variations; the 2 x 2 area; the declared link (colour and height); the stack order changed; `combine.tone_blend` at 0, 0.35, 0.4, 0.7, 1;
the layers on a brick layout; the settings audit (1.7 KB, no problems); the controls table regenerated from the layer files (`recipe/make_controls_table.py`, identical to the
one on disk); baking the same settings twice (identical pictures).

**Not tested:** the recipe inside Blender's interactive Shader editor by a person (switching boxes off by hand; all tests were command-line bakes); EEVEE
(no graphics card here); GPU rendering; bakes on a quiet machine (every time above was measured with other bakes running); `recipe.tiles_across` 3 or
other odd numbers; any `layout.rows_per_tile` or `slates_per_row` other than 8 x 6 and 6 x 4; independence at 1254 dots (it was tested at 384);
the reuse layers on any layout other than brick, and the half-tile test or the independence table on the brick (only a simple wrap-edge check: no seam); a real 3D render of the maps on a roof (lighting, normal direction checked only by the scores).

## 9. Dead ends and known gaps (honest)

Dead ends recorded by the builders and the first integrator:
* Smooth blends of tones: they look airbrushed; flat steps (rounding to the palette) are what reads as paint (`patch_hardness` strip).
* Tall patches the whole slate high (`mottle_tallness` 2.2): slates looked like corrugated sheets of stripes.
* Free moss blobs (`clump_strength` high): camouflage, the first build's weakness.
* Stronger green tints on slates (round 11): lowered the colour group (0.658) and looked dyed.
* A smooth shadow under each row (`shadow_tiers` 0): airbrushed.
* Real relief only (`tone_blend` 0): honest, but the same-kind height score is lower because the reference height was made from the colour.

Known gaps:
* The colour group is 0.70 at the default seeds, not the 0.8 the brief aimed at; its weakest part is the feature-size measure (rows too alike along their length).
* More moss (15 % olive-or-tan dots against 10.7 %) and more, more gathered tan breaks (5.3 % against 2.6 %) than the reference; moss clumps are
  solid, the reference's moss is partly a cast over the streaks.
* The widest slate in 48 is about 1.2 times the median width; the reference has one about 2 times (layout's random widths are not heavy-tailed enough).
* No overlap of slates (a slate lying on the one below); the dark band and the shadow stand in for it.
* The declared link is read dot by dot: "moss next to damage" cannot be said, only "on" or "not on" damage.
* The height defaults to 70 % paint brightness, not the pure real relief the brief described (section 5).
* The paint layer's tongues always hang from the top of a piece (good for slate, wrong for brick).

## 10. Where everything is

See `README - folder map.md`. The numbers of this guide are collected in `final_report.json`. What I re-ran after the restart is listed in the
README and in `integration/takeover/` (the chain scripts `run_chain_d.sh` to `run_chain_h.sh` and their logs; F and G were stopped part way and finished by H, as noted at their tops).
