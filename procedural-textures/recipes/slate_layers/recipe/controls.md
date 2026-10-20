# Slate in layers - the controls (one page)

Every setting is a flat name `layer.control` in `recipe/settings.json` (or passed as a parameter). Order of strength: the default below (written in the
layer's own file) < settings.json < the parameters given to the bake. "socket" controls are also knobs on the layer's box in the Shader editor;
"build" controls change how many nodes a box has, so they are read when the recipe is built. Sizes are in TILE units (1.0 = the whole base tile;
at 1254 dots per tile, 0.0064 = 8 dots). Every layer also has **seed** (its own random numbers) and **amount** (0 switches the layer off).
This file is written by `recipe/make_controls_table.py` from the layer files.

## THE RECIPE ITSELF

| setting | socket in Blender | default | low | high | what it does |
|---|---|---|---|---|---|
| `recipe.tiles_across` | (build) | 1 | 1 | 64 | how many base tiles fit across the picture: 1 = one tile that repeats exactly; 2 = a 2 x 2 area of NEW content (bake 2 x 1254 dots). Whole numbers only. |
| `recipe.stack_order` | (build) | colour_and_fade,moss,damage,outline_and_shadow |  |  | which layer paints over which, bottom first (heights and roughness are plain sums, so the order only matters for colour) |

## LAYOUT

| setting | socket in Blender | default | low | high | what it does |
|---|---|---|---|---|---|
| `layout.rows_per_tile` | (build) | 8 | 1 | 64 | how many rows of slates fit in one base tile (the reference has 8) |
| `layout.slates_per_row` | (build) | 6 | 1 | 64 | how many slates sit side by side in one row of one base tile (the reference has about 6) |
| `layout.seed` | Seed | 1 | 0 | 1000 | random seed of the layout: changes the widths, slides, joints and chips, nothing else |
| `layout.row_height_jitter` | Row Height Jitter | 0.05 | 0 | 0.45 | how much the row edges wander, as a share of one row height (0.05 = rows differ by about 4 percent; 0 = all rows equal) |
| `layout.row_phase` | Row Phase | 0.5 | 0 | 1 | where the picture edge cuts through a row, as a share of a row (0.5 = through the middle, 0 = along a joint) |
| `layout.width_spread` | Width Spread | 0.26 | 0 | 0.8 | how different the slate widths are (the spread of the log-width BEFORE the widths are scaled to fill the row; 0.26 measures as about 0.22 on the finished slates, like the reference; 0 = all slates equal) |
| `layout.row_slide` | Row Slide | 1 | 0 | 1 | how far each row may be slid sideways (1 = anywhere, 0 = every row starts at the same joint, like a brick stack) |
| `layout.joint_width` | Joint Width | 0.0014 | 0 | 0.01 | narrowest dark joint between two slates of a row, in tile units (0.0014 = 1.8 dots); chips make it wider |
| `layout.row_gap` | Row Gap | 0.005 | 0 | 0.03 | narrowest dark band between two rows, in tile units (0.005 = 6.3 dots); chips make it wider (the reference band is about 10.6 dots on average) |
| `layout.row_gap_top_share` | Row Gap Top Share | 0.1 | 0 | 1 | how much of the band between rows belongs to the top of the slate below (the rest lies under the slate above) |
| `layout.corner_radius` | Corner Radius | 0.0064 | 0 | 0.05 | rounding of the slate corners, in tile units (0.0064 = 8 dots) |
| `layout.corner_top_factor` | Corner Top Factor | 0.6 | 0 | 3 | the two top corners use this share of the corner radius (the reference has sharper top corners) |
| `layout.corner_bottom_factor` | Corner Bottom Factor | 1.5 | 0 | 3 | the two bottom corners use this multiple of the corner radius (rounder bottoms make the joints flare into the band between rows) |
| `layout.corner_radius_variation` | Corner Radius Variation | 0.3 | 0 | 1 | how much the corner rounding differs from slate to slate (0 = all the same) |
| `layout.joint_lean` | Joint Lean | 0.01 | 0 | 0.05 | largest sideways lean of a joint, as sideways distance per distance down (0.01 = 1.5 dots over a slate height); it is cut down so a joint never leaves its gap |
| `layout.ragged_side` | Ragged Side | 0.0024 | 0 | 0.01 | deepest chip into the left and right edges of a slate, in tile units (0.0024 = 3 dots) |
| `layout.ragged_top` | Ragged Top | 0.0022 | 0 | 0.01 | deepest chip into the top edge of a slate, in tile units (0.0022 = 2.8 dots) |
| `layout.ragged_bottom` | Ragged Bottom | 0.0055 | 0 | 0.01 | deepest chip into the bottom edge of a slate, in tile units (0.0055 = 7 dots) |
| `layout.ragged_scale` | Ragged Scale | 100 | 4 | 400 | how many chips (noise features) fit across one base tile: 100 = a chip about 12 dots long |
| `layout.ragged_detail` | Ragged Detail | 4 | 0 | 8 | how many finer noise layers are added to the chips (0 = smooth wobble, 3 = chipped) |
| `layout.ragged_chip` | Ragged Chip | 2 | 0.5 | 4 | chip sharpness: 1 = even wobble, 2 and more = mostly straight edge with some deep chips |
| `layout.bottom_tilt` | Bottom Tilt | 0.02 | 0 | 0.1 | how much the bottom edge of each slate slopes (random direction per slate), as height difference per width; makes the rows wave a little |
| `layout.edge_softness` | Edge Softness | 0.0004 | 0 | 0.005 | width of the soft ramp of the masks at an edge, in tile units (0.0004 = half a dot); 0 = hard (render samples smooth it) |
| `layout.joint_level` | Joint Level | 0.08 | 0 | 1 | base relief height in the joints (0..1) |
| `layout.slate_level` | Slate Level | 0.5 | 0 | 1 | base relief height on the slates (0..1) |
| `layout.bevel_width` | Bevel Width | 0.0035 | 0.0001 | 0.05 | how wide the rounded slope from joint level up to slate level is, in tile units (0.0035 = 4.4 dots) |
| `layout.slate_level_jitter` | Slate Level Jitter | 0.03 | 0 | 0.3 | how much each slate's height differs from the others (plus and minus this much) |
| `layout.slate_ramp` | Slate Ramp | 0.04 | -0.3 | 0.3 | how much higher the bottom of a slate is than its top (a slate lies slanted; plus = bottom higher) |

## COLOUR AND FADE

| setting | socket in Blender | default | low | high | what it does |
|---|---|---|---|---|---|
| `colour_and_fade.seed` | Seed | 11 | 0 | 1000 | the layer's own random seed: change it and ONLY this layer's pattern changes |
| `colour_and_fade.amount` | Amount | 1 | 0 | 1 | overall strength of the layer: 0 switches the layer off (Mask, Height and Roughness all become 0) |
| `colour_and_fade.tone_1` | Tone 1 (darkest) | #141719 |  |  | palette colour number 1 of 9 (darkest to lightest blue-grey); every slate and every patch is painted with one of these nine |
| `colour_and_fade.tone_2` | Tone 2 | #1e2225 |  |  | palette colour number 2 of 9 (darkest to lightest blue-grey); every slate and every patch is painted with one of these nine |
| `colour_and_fade.tone_3` | Tone 3 | #282d32 |  |  | palette colour number 3 of 9 (darkest to lightest blue-grey); every slate and every patch is painted with one of these nine |
| `colour_and_fade.tone_4` | Tone 4 | #33393e |  |  | palette colour number 4 of 9 (darkest to lightest blue-grey); every slate and every patch is painted with one of these nine |
| `colour_and_fade.tone_5` | Tone 5 | #3d444a |  |  | palette colour number 5 of 9 (darkest to lightest blue-grey); every slate and every patch is painted with one of these nine |
| `colour_and_fade.tone_6` | Tone 6 | #475057 |  |  | palette colour number 6 of 9 (darkest to lightest blue-grey); every slate and every patch is painted with one of these nine |
| `colour_and_fade.tone_7` | Tone 7 | #525b62 |  |  | palette colour number 7 of 9 (darkest to lightest blue-grey); every slate and every patch is painted with one of these nine |
| `colour_and_fade.tone_8` | Tone 8 | #5d676d |  |  | palette colour number 8 of 9 (darkest to lightest blue-grey); every slate and every patch is painted with one of these nine |
| `colour_and_fade.tone_9` | Tone 9 (lightest) | #687278 |  |  | palette colour number 9 of 9 (darkest to lightest blue-grey); every slate and every patch is painted with one of these nine |
| `colour_and_fade.green_tint` | Green Tint | #4c5959 |  |  | a greener grey that some slates lean towards (only its hue is used; its lightness is matched to the paint it tints) |
| `colour_and_fade.warm_tint` | Warm Tint | #5d5a54 |  |  | a warmer, browner grey that a few slates lean towards (only its hue is used) |
| `colour_and_fade.tone_centre` | Tone Centre | 3.6 | 0 | 8 | the tone step of the average slate (0 = darkest palette colour, 8 = lightest; 3.6 puts the average slate on the fourth to fifth colour) |
| `colour_and_fade.tone_spread` | Tone Spread | 0.5 | 0 | 3 | how different the base tones of the slates are, in tone steps (the typical slate is within this many steps of the centre) |
| `colour_and_fade.outlier_share` | Outlier Share | 0.08 | 0 | 0.6 | share of slates that are clearly darker or lighter than the rest (they are pushed Outlier Size steps up or down) |
| `colour_and_fade.outlier_size` | Outlier Size | 1.8 | 0 | 4 | how many tone steps an outlier slate is pushed up or down |
| `colour_and_fade.tint_amount` | Tint Amount | 0.5 | 0 | 1 | how far the tinted slates lean towards the green or warm grey (0 = every slate is pure blue-grey) |
| `colour_and_fade.tint_green_share` | Tint Green Share | 0.8 | 0 | 1 | of the tinted slates, the share that lean green (the rest lean warm) |
| `colour_and_fade.patch_tint` | Patch Tint | 0.4 | 0 | 1 | how far some single paint patches lean towards the green grey (a blue slate with a few greener patches in it; 0 = patches differ only in lightness) |
| `colour_and_fade.fade_amount` | Fade Amount | 1 | 0 | 2 | strength of the weathering inside each slate (the fade down the slate and the streaks); 0 = clean flat slates, 1 = like the reference, 2 = very weathered |
| `colour_and_fade.fade_direction` | Fade Direction | 1 | -1 | 1 | which way the slate fades: 1 = dark under the slate above and bleached towards the bottom edge (the reference); -1 = the reverse (bleached above, darker below); 0 = no up-down trend, streaks only |
| `colour_and_fade.fade_length` | Fade Length | 0.07 | 0.01 | 0.4 | how far the longest paint tongue runs down (or up) the slate, in tile units (0.07 = 88 dots, over half a slate; small = short stubby drips, large = streaks all the way down) |
| `colour_and_fade.streak_width` | Streak Width | 0.034 | 0.004 | 0.1 | how wide one paint tongue / streak is, in tile units (0.034 = 43 dots) |
| `colour_and_fade.streak_contrast` | Streak Contrast | 1.15 | 0 | 3 | how strongly the patches inside a slate differ from their neighbours, as a multiple of the usual (about one tone step); 0 = no mottling, only the fade |
| `colour_and_fade.top_darkening` | Top Darkening | 0.6 | 0 | 3 | extra darkening of the first fifth of the slate, under the slate above, in tone steps (the fade keeps going darker upwards; OUTLINE AND SHADOW adds the thin shadow line) |
| `colour_and_fade.speck_amount` | Speck Amount | 0.9 | 0 | 2 | strength of the many small paint specks (a speck is a flat patch of one tone step lighter or darker, a few dots across); 0 = none |
| `colour_and_fade.speck_cover` | Speck Cover | 0.1 | 0 | 0.6 | roughly the share of each slate covered by specks |
| `colour_and_fade.speck_size` | Speck Size | 0.011 | 0.003 | 0.05 | width of a speck in tile units (0.011 = 14 dots; they are a little taller than wide) |
| `colour_and_fade.patch_hardness` | Patch Hardness | 1 | 0 | 1 | how hard the edge of each paint patch is: 1 = a clean step from one palette colour to the next (flat painted patches), 0 = the colours blend smoothly |
| `colour_and_fade.streak_bend` | Streak Bend | 0.024 | 0 | 0.05 | how far a slow wander pushes the streaks and tongues sideways and up and down, in tile units (0.024 = 30 dots); 0 = perfectly straight patch edges, more = wavy, uneven tongue widths |
| `colour_and_fade.edge_ragged` | Edge Ragged | 0.0035 | 0 | 0.02 | how far a fine wobble pushes every patch edge sideways, in tile units (0.0035 = 4 dots; 0 = smooth patch outlines) |
| `colour_and_fade.bleach_amount` | Sun Bleach Amount | 0.5 | 0 | 1 | strength of the sun-bleached patches (areas of paler paint that cross several slates); 0 = none |
| `colour_and_fade.bleach_cover` | Sun Bleach Cover | 0.22 | 0 | 0.7 | roughly the share of the picture covered by sun-bleached patches |
| `colour_and_fade.stain_amount` | Damp Stain Amount | 0.4 | 0 | 1 | strength of the damp, darker patches that cross several slates; 0 = none |
| `colour_and_fade.stain_cover` | Damp Stain Cover | 0.18 | 0 | 0.7 | roughly the share of the picture covered by damp darker patches |
| `colour_and_fade.patch_size` | Big Patch Size | 0.32 | 0.08 | 1 | size of the sun-bleach and damp patches, in tile units (0.32 = about three patches across one tile) |
| `colour_and_fade.drift_amount` | Slow Drift | 0.25 | 0 | 2 | a slow wave of lighter and darker over the whole roof, in tone steps (it makes neighbouring slates belong together) |
| `colour_and_fade.grain_amount` | Grain | 0.05 | 0 | 0.3 | a very faint fine grain inside every flat patch (a share of the paint's brightness; the reference paint is not perfectly flat); 0 = perfectly flat paint |
| `colour_and_fade.tone_height` | Tone Height | 2 | 0 | 6 | how much the relief follows the paint: the height change per unit of paint brightness (the reference height was made from its colour; 0 = no tone relief) |
| `colour_and_fade.tone_roughness` | Tone Roughness | 1 | 0 | 4 | how much lighter paint is rougher and darker paint smoother (0 = no change of roughness with tone) |

## DAMAGE

| setting | socket in Blender | default | low | high | what it does |
|---|---|---|---|---|---|
| `damage.seed` | Seed | 21 | 0 | 1000 | the layer's own random seed: change it and ONLY this layer's pattern changes |
| `damage.amount` | Amount | 1 | 0 | 1 | overall strength of the layer: 0 switches the layer off (Mask, Height and Roughness all become 0) |
| `damage.chip_amount` | Chip Amount | 0.45 | 0 | 1 | how much of the slate edges is flaked (0 = none; 0.45 = patches along about a third of the lower edges; 1 = almost all of it) |
| `damage.chip_depth` | Chip Depth | 0.025 | 0 | 0.08 | how far a flake reaches in from the lower edge, in tile units (0.025 = 31 dots); the sides reach less (Side Share) |
| `damage.chip_frequency` | Chip Frequency | 62 | 10 | 400 | how many flakes (noise features) fit across one base tile: 62 = a flake tooth about 20 dots wide (1254 / 62); more = smaller flakes |
| `damage.chip_clustering` | Chip Clustering | 0.8 | 0 | 3 | how strongly flakes gather into stretches of one edge with clean stretches between (0 = spread evenly along the edge; 0.8 = clusters; 3 = a few big patches) |
| `damage.chip_breakup` | Chip Breakup | 0.6 | 0 | 2 | how broken up the flaked patches are: 0 = solid smooth patches; 1 = ragged, with holes and loose flecks around them |
| `damage.side_share` | Side Share | 0.12 | 0 | 1 | how far flakes reach in along the sides, as a share of the lower edge (the top edge gets less still) |
| `damage.corner_gain` | Corner Gain | 1 | 0 | 4 | extra flaking at the two lower corners (1 = twice as deep right at the corner) |
| `damage.slate_variation` | Slate Variation | 0.6 | 0 | 1 | how different the slates are from each other (0 = every slate equally damaged; 1 = some nearly clean, some badly hurt) |
| `damage.notch_amount` | Notch Amount | 0.3 | 0 | 1 | how many small dark bites there are in the slate edges (0 = none) |
| `damage.notch_depth` | Notch Depth | 0.01 | 0 | 0.04 | deepest bite into an edge, in tile units (0.010 = 13 dots) |
| `damage.corner_break_amount` | Corner Break Amount | 0.08 | 0 | 1 | chance that a lower corner of a slate has broken off (only the two lower corners can break: the upper ones lie under the row above) |
| `damage.corner_break_size` | Corner Break Size | 0.022 | 0 | 0.08 | size of a broken corner along each edge, in tile units (0.022 = 28 dots) |
| `damage.crack_amount` | Crack Amount | 0.35 | 0 | 1 | chance that a slate has a crack, per crack slot (each slate has Crack Slots slots, default 1; 0 = no cracks) |
| `damage.crack_length` | Crack Length | 0.07 | 0 | 0.2 | average length of a crack, in tile units (0.07 = 88 dots, about half a slate height) |
| `damage.crack_width` | Crack Width | 0.0028 | 0.0004 | 0.01 | width of a crack where it starts at the edge, in tile units (0.0028 = 3.5 dots); it narrows to a point |
| `damage.crack_across_share` | Crack Across Share | 0.25 | 0 | 1 | share of cracks that run across the slate from a side edge instead of down it (0 = all run downslope) |
| `damage.scratch_amount` | Scratch Amount | 0.18 | 0 | 1 | chance that a slate has a scratch, per scratch slot (each slate has Scratch Slots slots) |
| `damage.scratch_length` | Scratch Length | 0.03 | 0 | 0.2 | average length of a scratch, in tile units (0.03 = 38 dots) |
| `damage.pit_amount` | Pit Amount | 0.06 | 0 | 0.5 | share of the pit places that really hold a pit (0.06 gives about 200 pits per tile at the default Pit Low Bias) |
| `damage.pit_size` | Pit Size | 0.0034 | 0.0005 | 0.005 | typical pit radius in tile units (0.0034 = 4 dots) |
| `damage.pit_low_bias` | Pit Low Bias | 0.6 | 0 | 1 | how much the pits gather near the lower edge of the slates (0 = evenly over the slate; 1 = only near the lower edge, like the flakes) |
| `damage.break_colour` | Break Colour | #7c6f5d |  |  | the tan of weathered flaked slate and the lichen on it (the middle tone of a flake) |
| `damage.break_colour_light` | Break Colour Light | #8f8d85 |  |  | the pale of freshly broken slate: right at the edge of a flake, in scratches and in the rim of a bite |
| `damage.break_colour_dark` | Break Colour Dark | #5a4f43 |  |  | the darker tan-brown at the far tip of a flake and in the middle of a pit |
| `damage.hole_colour` | Hole Colour | #0b0c0e |  |  | the black seen where a piece is missing (corner breaks, bites) and inside cracks |
| `damage.sink_depth` | Sink Depth | 1 | 0 | 4 | multiplies how deep everything is sunk (1 = as tuned: a flake about -0.05, a crack -0.12, a broken corner -0.32 of the height scale) |
| `damage.roughness_gain` | Roughness Gain | 1 | 0 | 4 | multiplies how much rougher damaged places are (1 = flakes +0.12, cracks and pits +0.2) |
| `damage.crack_slots` | (build) | 1 | 0 | 6 | how many cracks a slate can have at most |
| `damage.scratch_slots` | (build) | 2 | 0 | 8 | how many scratches a slate can have at most |

## MOSS

| setting | socket in Blender | default | low | high | what it does |
|---|---|---|---|---|---|
| `moss.seed` | Seed | 31 | 0 | 1000 | the layer's own random seed: change it and ONLY this layer's pattern changes |
| `moss.amount` | Amount | 1 | 0 | 1 | overall strength of the layer: 0 switches the layer off (Mask, Height and Roughness all become 0) |
| `moss.coverage` | Coverage | 0.22 | 0 | 1 | how much of the slate surface is moss: 0 = none, 0.22 = about 8 percent of the slate dots look olive in the finished picture (the reference has about 7.5 percent), 0.4 = about twice that, 1 = nearly everything |
| `moss.patchiness` | Patchiness | 0.5 | 0 | 1 | how much the moss gathers into a few big mossy areas with large clean areas between: 0 = spread evenly over all slates, 1 = only in the big areas |
| `moss.patch_size` | Patch Size | 0.35 | 0.1 | 1 | size of the big mossy and clean areas, in tile units (0.35 = about three areas across the tile) |
| `moss.slate_variation` | Slate Variation | 0.5 | 0 | 1 | how different the slates are from each other: 0 = every slate equally mossy, 1 = some nearly clean, some thick with moss |
| `moss.drip_preference` | Drip Preference | 0.4 | 0 | 1.5 | how strongly moss gathers just below the upper edge of a slate and runs down in drips |
| `moss.drip_length` | Drip Length | 0.12 | 0.005 | 0.25 | how far an average drip can run down a slate, in tile units (0.12 = 150 dots); single strands are shorter (down to nothing) and longer (up to twice as long) |
| `moss.drip_width` | Drip Width | 0.05 | 0.008 | 0.12 | width of one drip strand, in tile units (0.05 = 63 dots); positions between strands stay clean |
| `moss.joint_preference` | Joint Preference | 0.35 | 0 | 1.5 | how strongly moss gathers along the side joints of a slate |
| `moss.lower_preference` | Lower Part Preference | 0.55 | 0 | 1.5 | how strongly moss gathers in the lower part of a slate |
| `moss.damp_preference` | Damp Spot Preference | 0.5 | 0 | 1.5 | how strongly moss gathers where the surface sits low (slates that lie lower and the sloping rim of every slate) |
| `moss.damage_avoid` | Damage Avoid | 0.8 | 0 | 1 | how much moss keeps off fresh damage: 1 = no moss at all on a damaged dot, 0 = does not care |
| `moss.damage_attract` | Damage Attract | 0 | 0 | 1 | how much moss prefers damaged dots (old flakes): only visible when moss is stacked over damage |
| `moss.cluster_size` | Cluster Size | 0.05 | 0.01 | 0.2 | width of a moss clump, in tile units (0.05 = 63 dots) |
| `moss.clump_strength` | Clump Strength | 1.8 | 0 | 3 | how much the clump noise (instead of the rules) decides where moss is: 0 = only the rules (a band under the upper edge), 3 = free blobs everywhere |
| `moss.drip_stretch` | Drip Stretch | 1.8 | 1 | 5 | how much taller than wide the clumps are: 1 = round blobs, 1.8 = drips, 4 = long thin streaks |
| `moss.flow_wobble` | Flow Wobble | 0.012 | 0 | 0.05 | how far a drip wanders sideways as it runs down, in tile units (0.012 = 15 dots) |
| `moss.edge_raggedness` | Edge Raggedness | 0.9 | 0 | 1.5 | how ragged and broken the edge of a clump is (0 = smooth outline, 1 = very ragged with loose flecks) |
| `moss.fringe_amount` | Fringe Amount | 0.3 | 0 | 1.5 | how long the thin fringe teeth that hang down from the edges of a clump are (0 = none; 0.25 = teeth up to about 20 dots long; 1.5 = long hairs) |
| `moss.fringe_width` | Fringe Width | 0.009 | 0.002 | 0.02 | width of one fringe tooth, in tile units (0.009 = 11 dots) |
| `moss.tone_1` | Moss Tone 1 (darkest) | #2b2c23 |  |  | the darkest olive: deep shadow under the upper edge and the heart of thick moss |
| `moss.tone_2` | Moss Tone 2 | #35372a |  |  | dark olive |
| `moss.tone_3` | Moss Tone 3 | #3f4032 |  |  | middle olive |
| `moss.tone_4` | Moss Tone 4 | #49493a |  |  | light olive |
| `moss.tone_5` | Moss Tone 5 (lightest) | #545342 |  |  | yellow-green: the youngest growth at the rim of a clump |
| `moss.tone_centre` | Moss Tone Centre | 0.7 | 0 | 1 | which tone is typical: 0 = mostly the darkest olive, 1 = mostly the lightest |
| `moss.tone_spread` | Moss Tone Spread | 0.8 | 0 | 1 | how many different tones one clump uses: 0 = every clump one flat tone, 1 = the whole range |
| `moss.rim_lightening` | Rim Lightening | 0.5 | 0 | 1 | how much lighter (yellow-green) the rim of a clump is than its middle |
| `moss.top_shading` | Top Shading | 0.2 | 0 | 1 | how much darker moss is right under the upper edge of a slate (the shadow of the row above) |
| `moss.tone_patch_size` | Tone Patch Size | 0.02 | 0.006 | 0.08 | width of one flat patch of one tone inside a clump, in tile units (0.02 = 25 dots); patches are 2.7 times taller than wide at the default Drip Stretch |
| `moss.lichen_amount` | Lichen Amount | 0.35 | 0 | 1 | how many lichen discs there are (0 = none): the share of grid places that hold a disc |
| `moss.lichen_clustering` | Lichen Clustering | 0.7 | 0 | 1 | how much lichen gathers into colonies with bare slate between them: 0 = scattered evenly, 1 = only in colonies |
| `moss.lichen_size` | Lichen Size | 0.0042 | 0.001 | 0.012 | typical radius of a small lichen disc, in tile units (0.0042 = 5 dots); the few big discs and rings are about three times that |
| `moss.lichen_colour` | Lichen Colour | #645c4f |  |  | the tan of a lichen disc (a ring has this colour) |
| `moss.lichen_light` | Lichen Light | #746a5c |  |  | the paler tan of a lichen ring and of the brightest discs |
| `moss.lichen_dark` | Lichen Dark | #524c40 |  |  | the darker tan in the middle of a ring |
| `moss.raise` | Raise | 1 | 0 | 4 | multiplies how much moss and lichen raise the surface (1 = moss +0.035, lichen +0.025 of the height scale) |
| `moss.roughness_gain` | Roughness Gain | 1 | 0 | 4 | multiplies how much rougher moss and lichen are (1 = moss +0.14) |

Declared links (inputs this layer reads from another layer): `Damage Mask` from damage.Mask (DAMAGE's Mask: where the slate is damaged, so moss can avoid fresh damage or gather on old damage)

## OUTLINE AND SHADOW

| setting | socket in Blender | default | low | high | what it does |
|---|---|---|---|---|---|
| `outline_and_shadow.seed` | Seed | 41 | 0 | 1000 | the layer's own random seed: change it and ONLY this layer's pattern changes |
| `outline_and_shadow.amount` | Amount | 1 | 0 | 1 | overall strength of the layer: 0 switches the layer off (Mask, Height and Roughness all become 0) |
| `outline_and_shadow.joint_width` | Joint Width | 0.0008 | 0 | 0.006 | how far the painted black spills out of the gap BETWEEN SLATES OF A ROW into each slate, in tile units (0.0008 = 1 dot); the gap itself is the layout's Joint Width |
| `outline_and_shadow.band_width` | Band Width | 0.0004 | 0 | 0.008 | how far the painted black spills out of the band BETWEEN ROWS into the slates above and below, in tile units (0.0004 = 0.5 dot); the band itself is the layout's Row Gap |
| `outline_and_shadow.joint_colour` | Joint Colour | #0e0f11 |  |  | the near-black of the joints |
| `outline_and_shadow.side_outline_width` | Side Outline Width | 0.002 | 0 | 0.008 | width of the thin dark line just inside every slate edge, in tile units (0.0020 = 2.5 dots) |
| `outline_and_shadow.side_outline_darkness` | Side Outline Darkness | 0.6 | 0 | 1 | how strongly the outline colour covers the slate paint (0 = invisible, 1 = solid) |
| `outline_and_shadow.outline_colour` | Outline Colour | #14161a |  |  | the dark blue-black of the thin outline (a little lighter than the joint black) |
| `outline_and_shadow.shadow_width` | Shadow Width | 0.03 | 0 | 0.06 | how far the shadow of the slate above reaches down the slate below, in tile units (0.030 = 38 dots; the reference band is about 21 dots of dark plus a soft tail to 40 dots) |
| `outline_and_shadow.shadow_darkness` | Shadow Darkness | 0.7 | 0 | 1 | how strongly the shadow colour covers the slate paint right under the joint (0 = no shadow, 1 = solid black); it is weaker lower down |
| `outline_and_shadow.shadow_tiers` | Shadow Tiers | 4 | 0 | 8 | how many flat painted steps the shadow is cut into (0 = a smooth blur; 4 = four flat tones; 1 = one flat band) |
| `outline_and_shadow.shadow_drip` | Shadow Drip | 0.5 | 0 | 1 | how ragged the lower border of the shadow is, as a share of Shadow Width (0 = a straight line; 0.5 = teeth pointing down like drips; 1 = very ragged) |
| `outline_and_shadow.black_drips` | Black Drips | 0.009 | 0 | 0.03 | how far black drips hang down from the black band into the shadow, in tile units (0.009 = 11 dots at most; they are teeth of different length, most places have none; 0 = no drips) |
| `outline_and_shadow.shadow_colour` | Shadow Colour | #0f1114 |  |  | the colour of the shadow: very dark blue-grey that is laid over the slate paint |
| `outline_and_shadow.lip_offset` | Lip Offset | 0.0026 | 0 | 0.02 | how far inside the slate edge the pale lip starts, in tile units (0.0026 = 3.3 dots: between the black joint and the lip is a thin dark rim, as in the reference) |
| `outline_and_shadow.lip_width` | Lip Width | 0.003 | 0 | 0.02 | width of the pale lip along the lower edge of a slate, in tile units (0.0030 = 3.8 dots), measured from the slate edge, after Lip Offset |
| `outline_and_shadow.lip_brightness` | Lip Brightness | 0.25 | 0 | 1 | how strongly the pale colour covers the slate paint on the lip (0 = no lip, 1 = solid pale) |
| `outline_and_shadow.lip_breakup` | Lip Breakup | 0.4 | 0 | 1 | how broken the lip is (0 = one unbroken line, 1 = only short pale pieces) |
| `outline_and_shadow.lip_colour` | Lip Colour | #8c8e8b |  |  | the pale grey of the lip (the reference lip and chips measure about #6d6c67 to #7a7975 on top of the paint) |
| `outline_and_shadow.edge_darkening` | Edge Darkening | 0.3 | 0 | 1 | how strongly the slate is darkened right next to its edges (0 = not at all) |
| `outline_and_shadow.edge_darkening_width` | Edge Darkening Width | 0.0045 | 0 | 0.03 | how far from an edge the darkening reaches, in tile units (0.0045 = 5.6 dots) |
| `outline_and_shadow.wobble` | Wobble | 0.5 | 0 | 1 | how hand-drawn the lines are: every outline and joint edge gets wider and narrower by this share (0 = ruler-straight lines, 0.5 = plus or minus half) |
| `outline_and_shadow.wobble_scale` | Wobble Scale | 90 | 10 | 400 | how many wobbles fit across one base tile: 90 = a wobble about 14 dots long; more = finer |
| `outline_and_shadow.slate_variation` | Slate Variation | 0.5 | 0 | 1 | how different the slates are from each other in shadow depth, shadow reach and lip (0 = every slate drawn the same) |
| `outline_and_shadow.shadow_height` | Shadow Height | 0.12 | 0 | 0.5 | how far the slate surface is pushed down at the top edge under the joint (a slope that rises over the Shadow Width); height scale 0..1 |
| `outline_and_shadow.lip_height` | Lip Height | 0.04 | 0 | 0.3 | how much the lip is raised (height scale 0..1) |
| `outline_and_shadow.outline_height` | Outline Height | 0.05 | 0 | 0.3 | how deep the thin outline groove is (height scale 0..1) |
| `outline_and_shadow.joint_roughness` | Joint Roughness | 0.12 | -1 | 1 | how much rougher than a bare slate the black joints are (added to roughness) |
| `outline_and_shadow.shadow_roughness` | Shadow Roughness | 0.06 | -1 | 1 | how much rougher the shadow band is (dirt gathers there) |
| `outline_and_shadow.lip_roughness` | Lip Roughness | -0.15 | -1 | 1 | how much smoother the lip is (an edge worn smooth catches the light); minus = smoother |

## COMBINE

| setting | socket in Blender | default | low | high | what it does |
|---|---|---|---|---|---|
| `combine.base_roughness` | Base Roughness | 0.8 | 0 | 1 | roughness of the bare slate before any layer changes it (0 = mirror, 1 = completely matt) |
| `combine.metallic` | Metallic | 0 | 0 | 1 | metallic for the whole surface (slate: 0) |
| `combine.height_gain` | Height Gain | 1 | 0 | 10 | multiplies the layers' heights before they are added to base_height (1 = as the layers wrote them) |
