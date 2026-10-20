# MOSS layer - the controls (one page)

Every control is a setting named `moss.<name>` (in `recipe/settings.json` or passed to the bake, for example `--params '{"moss.coverage": 0.5}'`) and also a knob
on the MOSS box in the Shader editor (its "socket" name is in the second column). Order of strength: the default below (written in `layers/moss.py`)
< settings.json < the parameters given to the bake. Sizes are in TILE units (1.0 = the whole base tile; at 1254 dots per tile, 0.0064 = 8 dots).
`moss.amount` is the layer's off-switch and an overall dimmer: 0 = nothing at all (mask, height and roughness exactly 0); between 0 and 1 it scales **coverage and lichen amount**
(so the paint stays crisp, only the amount of moss changes). This file is written by `moss_work/make_moss_controls_table.py` from `layers/moss.py`.

## How much, and where in the big picture

| setting | socket in Blender | default | range | what it does |
|---|---|---|---|---|
| `moss.coverage` | Coverage | 0.22 | 0 to 1 | how much of the slate surface is moss: 0 = none, 0.22 = about 8 percent of the slate dots look olive in the finished picture (the reference has about 7.5 percent), 0.4 = about twice that, 1 = nearly everything |
| `moss.patchiness` | Patchiness | 0.5 | 0 to 1 | how much the moss gathers into a few big mossy areas with large clean areas between: 0 = spread evenly over all slates, 1 = only in the big areas |
| `moss.patch_size` | Patch Size | 0.35 | 0.1 to 1 | size of the big mossy and clean areas, in tile units (0.35 = about three areas across the tile) |
| `moss.slate_variation` | Slate Variation | 0.5 | 0 to 1 | how different the slates are from each other: 0 = every slate equally mossy, 1 = some nearly clean, some thick with moss |
| `moss.seed` | Seed | 31 | 0 to 1000 | the layer's own random seed: change it and ONLY this layer's pattern changes |
| `moss.amount` | Amount | 1 | 0 to 1 | overall strength of the layer: 0 switches the layer off (Mask, Height and Roughness all become 0) |

## Where it likes to grow (each is a preference; 0 = does not care)

| setting | socket in Blender | default | range | what it does |
|---|---|---|---|---|
| `moss.drip_preference` | Drip Preference | 0.4 | 0 to 1.5 | how strongly moss gathers just below the upper edge of a slate and runs down in drips |
| `moss.drip_length` | Drip Length | 0.12 | 0.005 to 0.25 | how far an average drip can run down a slate, in tile units (0.12 = 150 dots); single strands are shorter (down to nothing) and longer (up to twice as long) |
| `moss.drip_width` | Drip Width | 0.05 | 0.008 to 0.12 | width of one drip strand, in tile units (0.05 = 63 dots); positions between strands stay clean |
| `moss.joint_preference` | Joint Preference | 0.35 | 0 to 1.5 | how strongly moss gathers along the side joints of a slate |
| `moss.lower_preference` | Lower Part Preference | 0.55 | 0 to 1.5 | how strongly moss gathers in the lower part of a slate |
| `moss.damp_preference` | Damp Spot Preference | 0.5 | 0 to 1.5 | how strongly moss gathers where the surface sits low (slates that lie lower and the sloping rim of every slate) |
| `moss.damage_avoid` | Damage Avoid | 0.8 | 0 to 1 | how much moss keeps off fresh damage: 1 = no moss at all on a damaged dot, 0 = does not care |
| `moss.damage_attract` | Damage Attract | 0 | 0 to 1 | how much moss prefers damaged dots (old flakes): only visible when moss is stacked over damage |

## The shape of the clumps

| setting | socket in Blender | default | range | what it does |
|---|---|---|---|---|
| `moss.cluster_size` | Cluster Size | 0.05 | 0.01 to 0.2 | width of a moss clump, in tile units (0.05 = 63 dots) |
| `moss.clump_strength` | Clump Strength | 1.8 | 0 to 3 | how much the clump noise (instead of the rules) decides where moss is: 0 = only the rules (a band under the upper edge), 3 = free blobs everywhere |
| `moss.drip_stretch` | Drip Stretch | 1.8 | 1 to 5 | how much taller than wide the clumps are: 1 = round blobs, 1.8 = drips, 4 = long thin streaks |
| `moss.flow_wobble` | Flow Wobble | 0.012 | 0 to 0.05 | how far a drip wanders sideways as it runs down, in tile units (0.012 = 15 dots) |
| `moss.edge_raggedness` | Edge Raggedness | 0.9 | 0 to 1.5 | how ragged and broken the edge of a clump is (0 = smooth outline, 1 = very ragged with loose flecks) |
| `moss.fringe_amount` | Fringe Amount | 0.3 | 0 to 1.5 | how long the thin fringe teeth that hang down from the edges of a clump are (0 = none; 0.25 = teeth up to about 20 dots long; 1.5 = long hairs) |
| `moss.fringe_width` | Fringe Width | 0.009 | 0.002 to 0.02 | width of one fringe tooth, in tile units (0.009 = 11 dots) |

## The olive colours and how they are used

| setting | socket in Blender | default | range | what it does |
|---|---|---|---|---|
| `moss.tone_1` | Moss Tone 1 (darkest) | #2b2c23 | (a colour) | the darkest olive: deep shadow under the upper edge and the heart of thick moss |
| `moss.tone_2` | Moss Tone 2 | #35372a | (a colour) | dark olive |
| `moss.tone_3` | Moss Tone 3 | #3f4032 | (a colour) | middle olive |
| `moss.tone_4` | Moss Tone 4 | #49493a | (a colour) | light olive |
| `moss.tone_5` | Moss Tone 5 (lightest) | #545342 | (a colour) | yellow-green: the youngest growth at the rim of a clump |
| `moss.tone_centre` | Moss Tone Centre | 0.7 | 0 to 1 | which tone is typical: 0 = mostly the darkest olive, 1 = mostly the lightest |
| `moss.tone_spread` | Moss Tone Spread | 0.8 | 0 to 1 | how many different tones one clump uses: 0 = every clump one flat tone, 1 = the whole range |
| `moss.rim_lightening` | Rim Lightening | 0.5 | 0 to 1 | how much lighter (yellow-green) the rim of a clump is than its middle |
| `moss.top_shading` | Top Shading | 0.2 | 0 to 1 | how much darker moss is right under the upper edge of a slate (the shadow of the row above) |
| `moss.tone_patch_size` | Tone Patch Size | 0.02 | 0.006 to 0.08 | width of one flat patch of one tone inside a clump, in tile units (0.02 = 25 dots); patches are 2.7 times taller than wide at the default Drip Stretch |

## Lichen (small round discs and rings)

| setting | socket in Blender | default | range | what it does |
|---|---|---|---|---|
| `moss.lichen_amount` | Lichen Amount | 0.35 | 0 to 1 | how many lichen discs there are (0 = none): the share of grid places that hold a disc |
| `moss.lichen_clustering` | Lichen Clustering | 0.7 | 0 to 1 | how much lichen gathers into colonies with bare slate between them: 0 = scattered evenly, 1 = only in colonies |
| `moss.lichen_size` | Lichen Size | 0.0042 | 0.001 to 0.012 | typical radius of a small lichen disc, in tile units (0.0042 = 5 dots); the few big discs and rings are about three times that |
| `moss.lichen_colour` | Lichen Colour | #645c4f | (a colour) | the tan of a lichen disc (a ring has this colour) |
| `moss.lichen_light` | Lichen Light | #746a5c | (a colour) | the paler tan of a lichen ring and of the brightest discs |
| `moss.lichen_dark` | Lichen Dark | #524c40 | (a colour) | the darker tan in the middle of a ring |

## Relief and roughness

| setting | socket in Blender | default | range | what it does |
|---|---|---|---|---|
| `moss.raise` | Raise | 1 | 0 to 4 | multiplies how much moss and lichen raise the surface (1 = moss +0.035, lichen +0.025 of the height scale) |
| `moss.roughness_gain` | Roughness Gain | 1 | 0 to 4 | multiplies how much rougher moss and lichen are (1 = moss +0.14) |

## The declared link (an input MOSS reads from another layer)

| socket | comes from | what it means |
|---|---|---|
| `Damage Mask` | damage layer, output `Mask` | DAMAGE's Mask: where the slate is damaged, so moss can avoid fresh damage or gather on old damage |
