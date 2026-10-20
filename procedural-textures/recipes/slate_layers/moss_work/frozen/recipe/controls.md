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
| `colour_and_fade.tone_a` | Slate Tone A | #3a4045 |  |  | first palette colour (blue-grey, about 29 percent of the reference) |
| `colour_and_fade.tone_b` | Slate Tone B | #4a5254 |  |  | second palette colour (lighter blue-grey); also the tone every slate gets when Amount is 0 |
| `colour_and_fade.tone_c` | Slate Tone C | #2d3133 |  |  | third palette colour (dark blue-grey) |

## DAMAGE

| setting | socket in Blender | default | low | high | what it does |
|---|---|---|---|---|---|
| `damage.seed` | Seed | 21 | 0 | 1000 | the layer's own random seed: change it and ONLY this layer's pattern changes |
| `damage.amount` | Amount | 1 | 0 | 1 | overall strength of the layer: 0 switches the layer off (Mask, Height and Roughness all become 0) |
| `damage.break_colour` | Break Colour | #8a7d6b |  |  | the pale tan colour of freshly broken slate and lichen on it |

## MOSS

| setting | socket in Blender | default | low | high | what it does |
|---|---|---|---|---|---|
| `moss.seed` | Seed | 31 | 0 | 1000 | the layer's own random seed: change it and ONLY this layer's pattern changes |
| `moss.amount` | Amount | 1 | 0 | 1 | overall strength of the layer: 0 switches the layer off (Mask, Height and Roughness all become 0) |
| `moss.moss_colour` | Moss Colour | #4f4e40 |  |  | the olive colour of the moss |

Declared links (inputs this layer reads from another layer): `Damage Mask` from damage.Mask (DAMAGE's Mask: where the slate is damaged, so moss can avoid fresh damage or gather near it)

## OUTLINE AND SHADOW

| setting | socket in Blender | default | low | high | what it does |
|---|---|---|---|---|---|
| `outline_and_shadow.seed` | Seed | 41 | 0 | 1000 | the layer's own random seed: change it and ONLY this layer's pattern changes |
| `outline_and_shadow.amount` | Amount | 1 | 0 | 1 | overall strength of the layer: 0 switches the layer off (Mask, Height and Roughness all become 0) |
| `outline_and_shadow.joint_colour` | Joint Colour | #0e0f11 |  |  | the near-black of the joints (the reference joint colour) |
| `outline_and_shadow.joint_roughness` | Joint Roughness | 0.12 | -1 | 1 | how much rougher than a bare slate the joint is (added to roughness where the joint is) |

## COMBINE

| setting | socket in Blender | default | low | high | what it does |
|---|---|---|---|---|---|
| `combine.base_roughness` | Base Roughness | 0.8 | 0 | 1 | roughness of the bare slate before any layer changes it (0 = mirror, 1 = completely matt) |
| `combine.metallic` | Metallic | 0 | 0 | 1 | metallic for the whole surface (slate: 0) |
| `combine.height_gain` | Height Gain | 1 | 0 | 10 | multiplies the layers' heights before they are added to base_height (1 = as the layers wrote them) |
