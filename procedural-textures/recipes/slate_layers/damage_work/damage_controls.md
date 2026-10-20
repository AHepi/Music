# DAMAGE - the controls (one page)

Each control is a setting named `damage.<control>` (in `recipe/settings.json` or passed as a parameter) and a knob on the DAMAGE box in the Shader editor.
Sizes are in TILE units (1.0 = the whole base tile; at 1254 dots per tile 0.0064 = 8 dots). "build" controls change how many nodes the box has, so they are read
when the recipe is built. The last column names the picture strip (in `controls_sweeps/damage/`) that shows what the control does. Written by
`damage_work/make_damage_controls_table.py` from `layers/damage.py`.

| setting | socket in Blender | default | low | high | what it does | strip |
|---|---|---|---|---|---|---|
| `damage.seed` | Seed | 21 | 0 | 1000 | the layer's own random seed: change it and ONLY this layer's pattern changes |  |
| `damage.amount` | Amount | 1 | 0 | 1 | overall strength of the layer: 0 switches the layer off (Mask, Height and Roughness all become 0) | strip_3_corners_notches_colours_amount.png |
| `damage.chip_amount` | Chip Amount | 0.45 | 0 | 1 | how much of the slate edges is flaked (0 = none; 0.45 = patches along about a third of the lower edges; 1 = almost all of it) | strip_1_edge_flakes.png |
| `damage.chip_depth` | Chip Depth | 0.025 | 0 | 0.08 | how far a flake reaches in from the lower edge, in tile units (0.025 = 31 dots); the sides reach less (Side Share) | strip_1_edge_flakes.png |
| `damage.chip_frequency` | Chip Frequency | 62 | 10 | 400 | how many flakes (noise features) fit across one base tile: 62 = a flake tooth about 20 dots wide (1254 / 62); more = smaller flakes | strip_1_edge_flakes.png |
| `damage.chip_clustering` | Chip Clustering | 0.8 | 0 | 3 | how strongly flakes gather into stretches of one edge with clean stretches between (0 = spread evenly along the edge; 0.8 = clusters; 3 = a few big patches) | strip_1_edge_flakes.png |
| `damage.chip_breakup` | Chip Breakup | 0.6 | 0 | 2 | how broken up the flaked patches are: 0 = solid smooth patches; 1 = ragged, with holes and loose flecks around them | strip_1_edge_flakes.png |
| `damage.side_share` | Side Share | 0.12 | 0 | 1 | how far flakes reach in along the sides, as a share of the lower edge (the top edge gets less still) | strip_4_where_and_how_big.png |
| `damage.corner_gain` | Corner Gain | 1 | 0 | 4 | extra flaking at the two lower corners (1 = twice as deep right at the corner) | strip_4_where_and_how_big.png |
| `damage.slate_variation` | Slate Variation | 0.6 | 0 | 1 | how different the slates are from each other (0 = every slate equally damaged; 1 = some nearly clean, some badly hurt) | strip_4_where_and_how_big.png |
| `damage.notch_amount` | Notch Amount | 0.3 | 0 | 1 | how many small dark bites there are in the slate edges (0 = none) | strip_3_corners_notches_colours_amount.png |
| `damage.notch_depth` | Notch Depth | 0.01 | 0 | 0.04 | deepest bite into an edge, in tile units (0.010 = 13 dots) |  |
| `damage.corner_break_amount` | Corner Break Amount | 0.08 | 0 | 1 | chance that a lower corner of a slate has broken off (only the two lower corners can break: the upper ones lie under the row above) | strip_3_corners_notches_colours_amount.png |
| `damage.corner_break_size` | Corner Break Size | 0.022 | 0 | 0.08 | size of a broken corner along each edge, in tile units (0.022 = 28 dots) |  |
| `damage.crack_amount` | Crack Amount | 0.35 | 0 | 1 | chance that a slate has a crack, per crack slot (each slate has Crack Slots slots, default 1; 0 = no cracks) | strip_2_cracks_scratches_pits.png |
| `damage.crack_length` | Crack Length | 0.07 | 0 | 0.2 | average length of a crack, in tile units (0.07 = 88 dots, about half a slate height) | strip_2_cracks_scratches_pits.png |
| `damage.crack_width` | Crack Width | 0.0028 | 0.0004 | 0.01 | width of a crack where it starts at the edge, in tile units (0.0028 = 3.5 dots); it narrows to a point | strip_2_cracks_scratches_pits.png |
| `damage.crack_across_share` | Crack Across Share | 0.25 | 0 | 1 | share of cracks that run across the slate from a side edge instead of down it (0 = all run downslope) | strip_2_cracks_scratches_pits.png |
| `damage.scratch_amount` | Scratch Amount | 0.18 | 0 | 1 | chance that a slate has a scratch, per scratch slot (each slate has Scratch Slots slots) | strip_2_cracks_scratches_pits.png |
| `damage.scratch_length` | Scratch Length | 0.03 | 0 | 0.2 | average length of a scratch, in tile units (0.03 = 38 dots) |  |
| `damage.pit_amount` | Pit Amount | 0.06 | 0 | 0.5 | share of the pit places that really hold a pit (0.06 gives about 200 pits per tile at the default Pit Low Bias) | strip_2_cracks_scratches_pits.png |
| `damage.pit_size` | Pit Size | 0.0034 | 0.0005 | 0.005 | typical pit radius in tile units (0.0034 = 4 dots) | strip_4_where_and_how_big.png |
| `damage.pit_low_bias` | Pit Low Bias | 0.6 | 0 | 1 | how much the pits gather near the lower edge of the slates (0 = evenly over the slate; 1 = only near the lower edge, like the flakes) |  |
| `damage.break_colour` | Break Colour | #7c6f5d |  |  | the tan of weathered flaked slate and the lichen on it (the middle tone of a flake) | strip_3_corners_notches_colours_amount.png |
| `damage.break_colour_light` | Break Colour Light | #8f8d85 |  |  | the pale of freshly broken slate: right at the edge of a flake, in scratches and in the rim of a bite | strip_3_corners_notches_colours_amount.png |
| `damage.break_colour_dark` | Break Colour Dark | #5a4f43 |  |  | the darker tan-brown at the far tip of a flake and in the middle of a pit | strip_3_corners_notches_colours_amount.png |
| `damage.hole_colour` | Hole Colour | #0b0c0e |  |  | the black seen where a piece is missing (corner breaks, bites) and inside cracks |  |
| `damage.sink_depth` | Sink Depth | 1 | 0 | 4 | multiplies how deep everything is sunk (1 = as tuned: a flake about -0.05, a crack -0.12, a broken corner -0.32 of the height scale) |  |
| `damage.roughness_gain` | Roughness Gain | 1 | 0 | 4 | multiplies how much rougher damaged places are (1 = flakes +0.12, cracks and pits +0.2) |  |
| `damage.crack_slots` | (build) | 1 | 0 | 6 | how many cracks a slate can have at most |  |
| `damage.scratch_slots` | (build) | 2 | 0 | 8 | how many scratches a slate can have at most |  |

Declared links: DAMAGE reads no other layer. MOSS reads DAMAGE's `Mask` through its declared link `Damage Mask` (moss may keep away from fresh damage or gather beside it).
