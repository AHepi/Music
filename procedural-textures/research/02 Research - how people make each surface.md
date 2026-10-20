# 02 Research - how people make each surface (brick, slate, wood, rusted metal, mud, gravel)

What this is: a plain-language guide to how Blender artists currently build six surfaces with procedural tools (shader nodes first, real geometry where people use it),
what I found on the web, and what I actually ran in Blender 5.2.2 on this machine to see whether it is true. For each surface it lists the approaches people use, which
layers make the picture look right, the traps, the hand-painted look, and an honest verdict on which approach gets closest to YOUR reference picture. Every test picture is
in `experiments_how_people_make_each_surface/pictures/`; every script and recipe is in `experiments_how_people_make_each_surface/`.

How to read the labels
- **TESTED** = I ran it in Blender 5.2.2 (CPU Cycles) and looked at the picture or the numbers.
- **NOT TESTED** = I only read it.
- **WEB ONLY** = a web page says it; I did not check it. Many tutorials are paid courses or videos: for those I could read only the title, date and a summary, not the node settings. I say so each time.
- "Tile" = the flat 1 x 1 square we bake. "u" and "v" = how far across and up the tile you are, from 0 to 1.
- "Layer" = one step that adds one kind of detail to the picture (a colour per brick, then flat patches, then soot, ...). "Mask" = a grey picture where white means "put the effect here".
- "Score" = the number from the project's scorer (`lib/texture_compare.py`): 0 = as different as another surface, 1 = the same by that measure; a re-shuffled copy of the reference itself scores about 0.99. I always also looked at the pictures.
- "Recipe" = a small Python file that builds one surface as a shader node group.

---

## 1. The short version (read this first)

The thirteen facts that would have saved me the most time (each is proved further down):

1. **Stock "tutorial" chains get you the layout and not the look.** The stock Brick Texture chain from a 2024 Blender Bazaar tutorial scored 0.065 against your brick, the same node with slate settings 0.183, planks 0.048, the Voronoi dirt chain 0.080, the noise-and-ramps rust chain 0.107 (reconstructed from incomplete step lists; see sections 5 to 9). My layered recipes scored 0.22 to 0.50 for the same six surfaces. (TESTED)
2. **The look of your references is made of hard-edged flat patches, dark outlines and a few clearly different colours, not of smooth noise.** Every recipe that came close uses Color Ramp "Constant", Map Range windows only 0.02 wide, and thin dark bands just inside every edge. (TESTED, pictures `layers_*.png`)
3. **Each surface needs its own layout idea, and the layout is the part that is easy to get wrong**: bricks = floor/fract of u x columns plus a half-brick shift on odd rows; slate = rows with a random slide and a random slate count per row; wood = boards of different heights bent with a repeating sine wave, then long thin splinter strips from a stretched Voronoi; metal = straps and braces described as numbers; mud = a diagonal coordinate bent by noise, so that bands of constant value are the ruts; gravel = one random polygon per grid cell. (TESTED)
4. **A pattern is only "seamless" if its coordinates are periodic.** Blender's own Noise and Voronoi are not. The project's trick (feed them a 4-dimensional "donut" made from sines and cosines of u and v) works for stretched patterns too (different feature counts across and up): I used it for streaks 3 across x 220 up, for ruts along a diagonal, for cells 3 x 30. (TESTED with a half-tile shift test, section 3.2)
5. **The strictest seam test is: shift the whole pattern by half a tile and compare with the picture rolled by half.** All six recipes pass (0.2 to 0.8 percent of pixels differ by more than 40/255; a wrongly rolled control differs in 1 to 35 percent). The scorer's own "seam" number gave false alarms (slate 13.9, wood 3 to 4) because a hard row boundary or a long thin line sat right on the tile edge. (TESTED)
6. **Height from colour: use the screen (sRGB) brightness of the colour.** It matches your reference height maps better than linear luminance: correlation 0.94 to 0.985 against 0.85 to 0.93. Dark stones in the colour picture are low in the height, lit faces are high. (TESTED on the reference pictures)
7. **Stones made from shrunk Voronoi cells come out as daggers and slivers.** A random polygon per grid cell (a convex polygon, each face with its own direction and radius) gives chunky faceted stones and tiles exactly. Faces per stone: 3 = shards, 4 = blocks, 5 to 8 = rounder. (TESTED, `sweep_gravel_faces_per_stone.png`)
8. **Real-geometry routes work but cost you the seamless tile.** Poisson-disk scatter keeps stones 0.0450 apart inside the tile (asked 0.045) but only 0.0104 apart across the tile edge; copies of the points one tile away make the picture repeat but still overlap at the seam. A rigid-body drop of 160 stones took 10.3 s and the walls of the tray cut the stones at the edge. (TESTED)
9. **Instanced meshes render black in Blender 5.2 unless a Set Material node gives them a material.** The material slot of the object is not enough. (TESTED)
10. **A forum claim that "Object Info > Random gives only 10 different values" is not true for instances in 5.2.2:** 196 cubes gave 196 different values (Location through White Noise gave 195, the Attribute node set to Instancer 196). (TESTED)
11. **Shader to RGB (the toon / painted trick) gives one flat colour in Cycles**, and the shader editor has no Posterize node. Use Map Range "Stepped" (N steps give N + 1 levels), Color Ramp Constant, or Math Snap. (TESTED)
12. **A single score moves by about 0.01 to 0.03 with the random seed alone and by up to 0.05 after a tiny edit** (mud 0.406 to 0.353 from one threshold). Differences under 0.05 are noise; trust the pictures first. (TESTED, section 3.3)
13. **Dynamic Paint wheel ruts can run headless, but only after you set `modifier.ui_type = 'BRUSH'` explicitly** (the operator `dpaint.type_toggle` alone left the brush a canvas); my first settings produced only 0.0009 of displacement, so I did not get a rut picture. (TESTED as far as stated; the rest NOT TESTED)

---

## 2. What your reference pictures need (what I read off them)

All six are seamless 1254 x 1254 hand-painted tiles. Common features: flat colour patches with hard edges, dark outlines, chunky shapes. Heights follow colour brightness.

| Surface | Layout | Colours (sRGB, main ones) | The details that make it look right |
|---|---|---|---|
| Brick | 4 bricks across, 12 rows, every second row shifted half a brick; mortar about 23 px | brick orange-red (159,77,45), dark red (113,61,45), soot (42,32,30), mortar tan (126,98,75) to (149,115,88) | dark outline round every brick; chipped, ragged mortar; big flat orange patches; pale spalled patches; dark soot smudges that run down across several bricks |
| Slate | 8 rows; 6 to 8 slates per row, widths 120 to 240 px, every row slid differently | dark grey-blue (58,64,65) to (78,85,85), black gaps (14,15,16), olive moss, tan lichen | thick black gap under and beside every slate; light chipped rim along the bottom edge; vertical brush-stroke colour steps; moss in the upper half of some slates |
| Wood | about 6 horizontal boards of different heights; long splintered strips inside | very dark brown (34,24,20) to (84,63,51), grey-brown (91,74,66), blue-grey, warm orange chips (140,102,75) | long dark cracks that taper; three clear round knots with rings (a fourth half hidden); round dark-brown splatter blotches; dark gaps between boards with tiny pebbles |
| Rusted metal | two vertical straps, two horizontal straps (one wraps round the tile edge), two diagonal braces, domed rivets about 42 px | plate (51,52,52) to (59,60,60) blue-grey, rust (96,61,38), bare metal (99,87,78) | dark outline and light edge line on every strap; rows of rivets; rust gathers at edges; drips; scratches; light chips |
| Mud | diagonal S-shaped ruts, blue-grey puddles with ragged edges, stones of three sizes | mud (109,73,54), (91,61,44), dark groove (42,32,30), water (106,116,121), stones dark blue-grey | dark wet groove with lighter banks; puddle rim darker; stones with a light face and a dark face; pebble clusters |
| Gravel | no layout: stones of all sizes packed on orange-brown soil | dark stones (25,24,25), (40,39,41), blue-grey (55,58,62), (76,83,86), rusty (92,65,46), (116,85,63) | about 35 percent very dark stones; faceted flat tones per face; dark outline; crumbly orange soil between |

(The colour list comes from `experiments_geometry_nodes_curves_modifiers_physics/reference_palettes.json`, the measured clusters of the references. The layout and detail columns are what I read by eye.)

---

## 3. Shared tools I built and tested for this guide

All of them are in `experiments_how_people_make_each_surface/`. They sit on top of the project's `lib/` and change nothing there.

### 3.1 `builder.py` - write a recipe as a list of sums
One short call per step (`b.mul(x, 0.5)`, `b.noise(...)`, `b.ramp(...)`); each call adds the node, wires its inputs and gives you the output. Colours are typed as hex codes ('#9f4d2d', the screen colour you see in a picture) and converted to the linear numbers Blender wants (a typed hex of #808080 is not 0.5 in Blender: 0.5 linear is screen 188). (TESTED: the six recipes are built with it.)

### 3.2 Seamless patterns, also stretched (TESTED)
`b.tnoise(scale_u, scale_v, ...)` and `b.tvoronoi(scale_u, scale_v, ...)` read the 4D noise or cells from a donut: `x = R_u cos(2 pi u)`, `y = R_u sin(2 pi u)`, `z = R_v cos(2 pi v)`, `w = R_v sin(2 pi v)` with `R = scale / (2 pi)`. **Example first:** `b.tnoise(4, 220)` makes long thin horizontal grain (4 features across the tile, 220 up it) that still wraps; `b.tnoise(34, 5, coords=(s, v))` with `s = u + v + ...` makes streaks that run along a bending diagonal rut.
**Rule:** the two numbers you feed in must each add exactly 1 when u or v grows by 1 (`u + v` does; `u * 1.5` does not).
**The half-tile shift test** (`periodicity_test.sh`): bake the recipe, then bake it again with the whole pattern slid by (0.5, 0.5); a truly periodic recipe gives the first picture rolled by half its size.

| Recipe | Mean difference (of 255) | Pixels differing by more than 40 | Same test with a wrong roll (control): mean, share |
|---|---|---|---|
| brick (128 px) | 5.4 | 0.77 % | 32.1, 25.8 % |
| slate (128 px) | 3.5 | 0.41 % | 29.0, 28.9 % |
| wood (128 px) | 5.1 | 0.24 % | 19.4, 7.5 % |
| metal (128 px) | 3.2 | 0.21 % | 11.6, 1.1 % |
| mud (192 px) | 4.7 | 0.60 % | 28.6, 25.2 % |
| gravel (192 px) | 5.4 | 0.54 % | 34.7, 34.5 % |

(The few differing pixels are anti-aliased hard edges, which land on different sample positions after the shift. Wood and metal are smooth or sparse, so their controls differ less, but the mean difference still shows the match.)

Other facts from the same tests: the baked coordinate at the tile edges is exact (u and v read back within 0.0005 of the pixel-centre values at 16 bit); Voronoi F1, F2, Smooth F1, Distance to Edge and N-Sphere Radius on the donut all show edge jumps of 0.5 to 1.5 times a normal neighbour jump (a weak test); F1 and Distance to Edge also pass the half-tile test inside the wood recipe. A tile cut that falls on a hard row boundary fools the scorer's seam number (slate: 13.9 on the first bake; shifting the rows by half a row gave 1.12). (TESTED)

### 3.3 How much can I trust one score? (TESTED, `seed_spread.sh`)
Each recipe baked with three seeds at 384 px and scored against its reference (`out/seed_spread/summary.txt`), next to the score of the same recipe at 512 px with its normal seed:

| Recipe | seed A | seed B (+100) | seed C (+200) | spread | same recipe at 512 px |
|---|---|---|---|---|---|
| brick | 0.407 | 0.434 | 0.420 | 0.027 | 0.327 |
| slate | 0.502 | 0.506 | 0.497 | 0.009 | 0.503 |
| wood | 0.455 | 0.340 | 0.347 | **0.115** | 0.325 |
| metal | 0.306 | 0.316 | 0.293 | 0.023 | 0.286 |
| mud | 0.430 | 0.407 | 0.411 | 0.023 | 0.353 |
| gravel | 0.306 | 0.289 | 0.321 | 0.032 | 0.223 |

**Meaning:** the random seed alone moves a score by 0.01 to 0.03 (wood by 0.115, because its few long cracks and knots land in different places), and the bake size matters as much: the same recipe scored 0.00 to 0.13 lower at 512 px than at 384 px (the scorer shrinks or stretches every picture to 1254, so feature sizes shift). **Only compare scores of pictures made at the same size and with the same seed, bake the final comparison at 1254, and treat differences under 0.05 as noise.** (My per-surface scores elsewhere in this guide are the 512 px, normal-seed ones.)

### 3.4 Layer-by-layer strips (TESTED)
Each recipe has a setting `stage` that shows the picture after only the first n steps: `layers_brick.png`, `layers_slate.png`, `layers_wood.png`, `layers_metal.png`, `layers_mud.png`, `layers_gravel.png` in the pictures folder. They are the best way to see what each layer adds.

### 3.5 `stone_tools.polygon_stones` - random polygons, one per grid cell (TESTED)
**What it does:** cuts the tile into a grid of `cells x cells` squares (the grid number is wrapped with a modulo, so it tiles exactly), puts at most one stone in each square, and makes the stone the part of the square where ALL of `sides` straight-edge tests are true ("distance along direction k is less than radius k"). Each direction, each radius, the offset, the size and the overall turn come from a White Noise of the cell number.
**Example first:** `polygon_stones(b, 12, seed, presence=0.12, radius_low=0.22, radius_high=0.40, sides=5)` = about 17 big five-sided stones on a 12 x 12 grid, each 0.22 to 0.40 of a cell from centre to face. A slow noise bends the grid (`warp`) so it does not read as a grid. Each flat face also gets a brightness from the direction it looks (top-left light), so one stone has a light face and a dark face for free.
**Why not Voronoi:** my first try shrank Voronoi cells; the picture `mud_first_try_voronoi_stones.png` shows dagger and sliver shapes (score 0.204). The polygon version scored 0.167 at first (stones far too big), 0.24 after I made them smaller, and 0.41 (final 0.35 after one more threshold edit) once I also added a second family of ruts and bigger puddles, so the score gain came mostly from the ruts and puddles; the stone SHAPES are what you see by eye. A flat 2D slice through 4-dimensional cells has very uneven cell sizes, which is the likely reason for the slivers (my explanation; I did not test other causes).

---

## 4. Claims checked: what is true, what is wrong, what I could not check

| Claim (where) | Verdict | Evidence |
|---|---|---|
| "Brick Texture: Noise scale ~300 into Color1/Color2 gives each brick its own colour" (Blender Bazaar bricks tutorial, 21 Jan 2024) | **Only half true.** The noise adds fine grain; the per-brick variety is the Brick node's own Color1/Color2 mix. The colours also do not repeat at whole tile steps. | Picture `stock_chains_vs_reference.png`; the non-repeat of Brick colour is from the shader-toolbox guide (TESTED there). |
| "Object Info > Random gives only 10 different values" (Blender Artists, DNorman, 1 Jun 2021) | **Not true in 5.2.2 for Geometry Nodes instances.** | 196 cubes gave 196 different values (`geo_instance_random_test.py`, facts in `out/geo_instance_random/facts.json`). TESTED |
| "Per-instance colour: use Object Info > Location through a White Noise" (same thread) | **True** (195 of 196 different values; one collision). | same test |
| A material set on the object colours every instance | **False in 5.2.2.** Instances of a mesh made inside Geometry Nodes render black unless the geometry passes through a Set Material node. | black pictures until a Set Material node was added. TESTED |
| "Poisson Disk keeps points a minimum distance apart" (Superhive scatter-rocks page; manual) | **True inside the tile, false across the tile edge.** | nearest-neighbour minimum 0.04501 for a 0.045 request; across the wrap 0.0104. TESTED |
| "Scatter a tile with ghost copies and it is seamless" (common advice) | **Periodic, yes; spacing at the seam, no** (same 0.0104). | `geo_gravel_scatter.py --ghosts` TESTED |
| "Shader to RGB makes toon / painted shaders" (EEVEE tutorials) | **EEVEE only.** One flat colour in Cycles. | `posterize_kinds.png`. TESTED |
| "Bevel node gives edge wear" (many) | **True, but only on real geometry edges;** a radius of 0.004 gives thin lines, 0.010 bolder ones. Flat painted-on straps have no edges to find. | `geo_rivets_height_and_bevel_masks.png`. TESTED |
| "Rigid bodies settle stones for gravel" (polygoniq quick tip, 1 Nov 2023) | **True,** 160 stones, 130 frames, 10.3 s here; result is cut by the tray walls so it does not tile; 3 of 160 stones escaped the tray. | `geo_physics_gravel.py`. TESTED |
| "Dynamic Paint can carve wheel ruts" (Dikko, Sardi Pax, Lester Banks) | **Runs headless, but needs `modifier.ui_type = 'BRUSH'` set by hand; I only got 0.0009 displacement.** | `geo_dynamic_paint_ruts.py`. TESTED as far as stated |
| "Pointiness does not work in Eevee" (a brick-wall product page) | I could not run Eevee here. | NOT TESTED |
| "The 'Fully procedural roof tile shader' has random Z rotation, bevel and per-tile UVs" (Blender Artists, _jb4x, 7 May 2020) | The page says so; the node tree exists only in the attached .blend. | WEB ONLY |
| "Change the seed and sawing position so every plank is unique" (Poliigon plank generator guide) | Idea only; the page 404-ed when I tried to read it again. | WEB ONLY |

---

## 5. BRICK WALL

**Plain meaning:** a wall is a grid of bricks (rows, each shifted half a brick) with mortar between; it looks right when every brick has its own colour and its own damage, the mortar is ragged, and dirt runs across several bricks.

### 5.1 Approaches found

**B1. The stock Brick Texture chain** - TESTED (reconstruction)
- Source: Blender Bazaar, "how to make a procedural bricks material", JSAbbott, 21 Jan 2024, Blender 4.0; Blender manual, Brick Texture node (the manual text bundled with 5.2).
- Chain as the page lists it: Texture Coordinate (UV) -> **Brick Texture** with Color1 `#6D3137`, Color2 `#B55B51`, Mortar `#909090`; a **Noise Texture** (Scale about 300) into two Color Ramps (white stops `#B55B51` and `#6D3137`) that feed Color1 and Color2; a second Noise through a ramp into the Mortar input; the Brick colour into a **Normal Map** (Strength 0.15) into a **Displacement** node; a **Voronoi** (Smooth F1, Scale about 3) through a Color Ramp set to **Constant** as a mask to mix "paint" in. The page also says: set the UV with Cube Projection to cure stretched sides, and turn on Node Wrangler.
- The manual's settings: Scale, **Mortar Size** (0 = no mortar), **Mortar Smooth** (blurs the brick/mortar edge, "useful with displacement"), **Bias** (-1 or 1 = only one of the two colours), **Brick Width**, **Row Height**, Offset, Frequency (2 = even/odd rows), Squash, Frequency.
- What I ran: the chain built node by node with those numbers (Scale 2, Brick Width 0.5, Row Height 0.1667 = 4 x 12 whole bricks). Score **0.065** (colour 0.086, normal 0.148). Picture: `stock_chains_vs_reference.png` (top row). Clean even rows, flat colour, no soot, no chips, no outline.
- Honest limit: the page gives no values for the ramp stop positions; I guessed them. So 0.065 is "what the listed nodes give", not the tutorial author's finished picture.

**B2. Pick the brick colour by a threshold on the per-brick number** - WEB ONLY (the idea is used in my recipe, TESTED there)
- Source: Blender Artists, "Wooden floor with Brick shader", posts 19-21 Aug 2023 (Debuk, DNorman). Each brick gets a value 0..1 from the Brick node; a **Color Ramp set to Constant with two stops** (or Math "Greater Than") turns it into a hard mask; use the mask to choose a colour or a material. Bias changes the ratio.
- Also, Blender Artists "Procedural brick shader" (jancyclops, 14 Jun 2016): per-brick random colour from a Color Ramp, bump height varied the same way; **no mortar** in the shader (mortar kept on a separate plane); Bevel modifier on each brick. A 2017 post says baking Diffuse with it gave plain white bricks (unconfirmed).

**B3. Two bricks for chipped, rounded edges** - WEB ONLY
- Source: Blender Artists, "How to procedural texture with stones tiles", 14-15 Jan 2022 (AgentTuron, RSEhlers, KAUSTIK). Two Brick nodes of identical size that differ only in Mortar Size and Smooth; the inner one made ragged with noise on its coordinates; mix with masks; one bump, or displacement on the base and bump only on the inner. A mask from a slightly shrunk Brick node combined with the bump rounds the edges; "a true dome would need displacement and Cycles". Named alternatives: Erindale's "Procedural Bricks" tutorial and Simon Thommes's Brick node (not opened).

**B4. A home-made layout with per-brick random numbers (my recipe)** - TESTED
- Chain, top to bottom (`recipes/recipe_brick.py`):
  1. `v x 12` -> Floor = row, Fraction = height inside the brick. `u x 4 + 0.5 x (row mod 2)` -> Floor = column, Fraction = position along the brick. Column and row are wrapped with Floored Modulo (4 and 12) so they repeat.
  2. **White Noise (3D) of (column, row, seed)** -> one random number per brick; four of them (tint, soot, spalling, noise seed).
  3. Distance to the nearest brick side in tile units (side distance / columns, top distance / rows, then the smaller), plus ragged-edge noise (`tnoise(70, 70)` times 0.013) -> **Map Range window only 0.0001 wide** = brick mask (hard edge); a second window 0.0045 further in = the dark outline band.
  4. Brick colour: Color Ramp **Constant** with 5 reds chosen by the brick's tint number; then flat patches from a **4D Noise read on the brick's own square** (Vector = (fx x 3, fy, 0), W = brick random x 50, Scale 1.3, Detail 4), cut with a 0.04-wide Map Range; spalled pale patches only on bricks whose number is above 0.55; soot streaks from a noise stretched up-down on the brick's square, allowed more on bricks with a high soot number.
  5. Mortar: tan Color Ramp on fine noise, lighter chips (a noise cut at 0.58 to 0.62), a darker band next to the bricks.
  6. Over everything: big soot smudges from `tnoise(6, 2.6, distortion 1.0)` cut at 0.585, drawn only on bricks; fine grain.
  7. Height = screen brightness of the colour, stretched (Map Range 0.06 to 0.55).
- Result (`compare_brick.png`, `layers_brick.png`): layout, outline, palette and per-brick variety read right at once; soot is too streaky and the mortar too even. Score **0.327** (final), 0.41 to 0.43 at 384 px with three seeds.

**B5. Real bricks with Geometry Nodes** - WEB ONLY
- Sources: Ryan King Art "Customizable Brick Wall" (product, listing 2024), 3D Tudor "Brick wall generator" (product), monsoonsheep (product). Instances of a brick mesh on a grid or along a curve; options for random rotation ("for more stylised looks"), random displacement (turns instances into real geometry, so more vertices), roundness, bevel, cement fill. One seller: "the pointiness value ... will not work in Eevee". One note says building mortar with volume-to-mesh "depended on brick size".
- My related TEST: the same instancing route for slate rows works (section 6.1 S3); I did not build a brick wall with it.

**B6. Layered node-group "bundles" and video courses** - WEB ONLY
- Brickmaker (Blender Market / Superhive docs; Blender 4.0-4.2; version 2.1): four groups in a row: **BrickTextureJT** (offset, brick size, mortar, rotation; outputs base height, mask, "barebone variation", greyscale for colour), **BrickDamage** (vertical lines, edge damage, destroy, small dots), **BrickMortar** (height, spread, noise, grains/pebbles), **BrickColor** (a set of mixed colours). Good structure to copy.
- Courses (paid, videos): Luca Rood's mossy brick wall "100 percent Blender, no third-party plugins"; Blender Guru's texturing course (a grungy brick wall; the page lists **Color Burn technique**, **wet leak patterns**, **efflorescence**, **desaturation**, **spalling**, with time stamps only). I could not read the node settings.

### 5.2 The layers that make brick look right (what each adds)
Pictures: `layers_brick.png` (1 layout only, 2 + colour per brick, 3 + flat patches, 4 + spalls and soot, 5 + mortar and outline, 6 + smudges and grain).
- **Per-brick colour** (one random number per brick through a Constant ramp): from "wallpaper" to "wall". TESTED.
- **Flat patches inside the brick** (noise on the brick's own square, narrow window): the painted-brick look. TESTED.
- **Dark outline** (a band just inside the brick edge): separates bricks and gives the hand-painted look. TESTED.
- **Ragged mortar edge** (distance plus noise, not Mortar Smooth): chips. TESTED.
- **Soot / dirt running down** (noise stretched up-down; some bricks sooty): the largest realism gain after colour. TESTED (my version still too streaky).
- **Moss, efflorescence (white salt), wet leaks:** named by the Blender Guru course and others; I did not build them. NOT TESTED.

### 5.3 Pitfalls and tricks
- Whole columns and an EVEN number of rows, or the half-brick shift does not close at the tile edge (TESTED in the shader-toolbox guide, section 8.1).
- Measure the mortar width in tile units in both directions (divide the side distance by the column count and the top distance by the row count), otherwise vertical joints come out wider than horizontal ones. TESTED (recipe).
- Read patch noise on the brick's own square `(fx x brick_aspect, fy)`, otherwise the patches stretch with the brick. TESTED.
- A per-brick seed fed into the **W** of a 4D noise gives every brick a different pattern from one node. TESTED.
- The Brick node's colour random does not repeat at whole tile steps; use your own per-brick hash if you need to tile. (TESTED in the shader-toolbox guide.)
- Brick "height" in your reference is just brightness (mortar bright, soot dark), not physical depth. If you want real depth, make a second height with mortar low. NOT TESTED as a separate map.

### 5.4 Hand-painted look
Everything hard-edged: Constant ramps, Map Range windows only 0.02 to 0.04 wide, a dark outline, flat patches, and no smooth gradients on the face of the brick. The Blender Artists answer in B2 says the same (replace "Greater Than" nodes with a two-stop Constant ramp). TESTED.

### 5.5 Which approach is closest to YOUR brick
**B4 (home-made layout, per-brick numbers).** Why: your reference has a dark outline, chunky flat patches and big smudges across several bricks, which a stock Brick node cannot give (no outline, no per-brick patches, colour limited to two blended colours). Measured: 0.327 (B4) against 0.065 (B1). By eye B4 gets layout, outline and palette; it misses the soft dark smudges and the chipped mortar. B3 (two bricks) and B6 (damage groups) would improve the edges; they are untested. Difficulty: B1 easy (about 20 nodes, one hour); B4 medium (152 nodes, of which 95 are small Math nodes, written as about 90 lines of Python; one day).

---

## 6. ROOF SLATE TILES

**Plain meaning:** a slate roof is rows of flat stones, each row slid a different amount, every slate a slightly different width, with a dark shadow gap under and beside each one.

### 6.1 Approaches found

**S1. The stock Brick node with narrow rows** - TESTED
- Source: none specific (I found no tutorial for a slate shader; the obvious home-made version is a Brick node with narrow rows, and I built that).
- What I ran: Brick Texture Scale 1.0, Brick Width 0.17, Row Height 0.125, Mortar `#0c0d0e`, two blue greys (`#2f3a42`, `#51636d`), a Noise (scale 25) into the colours. Score **0.183** (colour 0.268). Picture: `stock_chains_vs_reference.png` (second row): perfect rectangles, every row slid exactly half, one width.

**S2. A tileable slate image used as bump and colour mask** - WEB ONLY, out of date
- Source: "Blender 2.5 Materials and Textures Cookbook" (Packt, recipe "Creating a slate roof node material that repeats but with ultimate variety"; undated page, a 2.5-era book). A small tileable picture of the smallest repeat is used both as bump and as a mask for colour variation; a second recipe adds randomness to the repeat. It uses a painted picture, which this job may not use. The material steps are dated; translate them to the Principled BSDF.

**S3. Real slabs with Geometry Nodes** - TESTED (my build); sources WEB ONLY
- Sources: 3D Tudor "Blender 4 Roof Tile Procedural Geometry Node" (product; row offsets, odd/even material alternation, randomised size and placement, tiles can be bent); freckleone (NodeCrafted) "Roof Tiles Generator", Blender Artists thread 2 Jun - 6 Dec 2024 (one node for flat procedural tiles, one that distributes a custom tile mesh; a boolean per tile is slow; users asked for column offset and rotation randomness); DNorman, Blender Artists "Realistic roof tiles texture", 31 May and 1 Jun 2021 (one doubled tile instanced on a subdivided plane; object location into a White Noise gives the colour variation).
- My chain (`geo_slate_rows.py`): Mesh Grid 7 x 8 vertices -> Set Position (offset x = **Random Value with ID = floor(y x 8)**, 0 to 1/7, so every row slides by its own amount; offset z = row x 0.004 so upper rows lie over lower ones) -> Mesh to Points -> **copies one tile away in all 8 directions** (Transform + Join) so it repeats -> **Instance on Points** (Instance = a cube passed through **Set Material**; Scale = (0.84 to 0.97)/7 wide, 1.32/8 tall, 0.006 thick; Rotation = Euler to Rotation of three small random values up to 0.035 rad) -> Cycles top-down render; colour = **Object Info > Random** through a Constant ramp of blue-greys.
- Result: pictures `geo_slate_rows_colour.png` and `geo_slate_rows_height.png`. It reads as a slate roof at once (per-row slide, per-slate width, tilt, overlap). It is flat-coloured with no outline, no moss, no chips, so I did not score it; the picture still needs the same colour layers as the shader recipe. Pitfalls found: the slabs must pass through Set Material (black otherwise); the z steps cannot be periodic (one step goes the wrong way where the tile wraps).

**S4. A fully procedural roof tile shader (masks, per-tile UVs)** - WEB ONLY
- Source: Blender Artists, "Fully procedural roof tile shader", _jb4x, 7-8 May 2020, Blender 2.8. Controls: tile scale, aspect ratio, bevel on/off with thickness and height, random Z rotation, roundness (also randomised), gap between tiles (also randomised), edge noise ("not happy with"). Outputs: several masks, a height map with bevel, a UV shared by every tile, a UV unique to each tile, a tile-position output, and an example albedo using noise from the unique UV. Planned: random X rotation, moss, better edge warping. The author says the node tree is messy and gives it only as a .blend ("Procedural roof tiles - alpha.blend"). The thread says nothing about slate in particular. This "one UV per tile" output is the same idea as my `fx, fy` and per-slate random numbers.

**S5. A home-made row layout (my recipe)** - TESTED
- Chain (`recipes/recipe_slate.py`):
  1. `v x 8 + 0.5` (half a row of shift, so the tile edge cuts through slates, not through a gap) -> Floor = row, Fraction = height in the slate (0 at the bottom).
  2. **White Noise of the row number** -> the number of slates in the row (6, 7 or 8), a random slide, two random phases.
  3. `u` + slide + a **sine wave that repeats exactly 3 times across the tile** (amplitude 0.40 / (2 pi x 3)) + a second one that repeats 7 times (amplitude 0.20 / (2 pi x 7)); the sum times the slate count gives the slate number and the position across the slate. The waves squeeze and stretch the widths but are the same at u and u + 1, so it still wraps. The total wave slope (amplitude x 2 pi x repeats) must stay below 1 or the slate edges fold back.
  4. Black gap under (0.009 of the tile) and beside (0.0065) the slate, ragged by seamless noise; a light rim 0.014 above the gap, broken up by noise.
  5. Colour: a **4D Noise read on the slate's own square** stretched up-down (Vector = (fx x aspect x 9, fy x 1.5), W = per-slate random x 60), cut into 5 hard steps by a Constant ramp; the ramp chosen (dark grey or blue grey) by the slate's tint number; flat dark blotches.
  6. Moss: stretched noise window, allowed more on mossy slates and only toward the top (Map Range of fy from 0.25 to 0.9); pale lichen spots near the bottom; the rim colour.
  7. Height = screen brightness, stretched (0.02 to 0.52).
- Result (`compare_slate.png`, `layers_slate.png`): the layout reads like your slate at once. Score **0.503** (colour 0.532, height 0.313, normal 0.626), 0.50 to 0.51 at 384 px with three seeds: the best of my six.

### 6.2 Layers that make slate look right
Pictures: `layers_slate.png` (1 layout: gaps, 2 + brush strokes and tone per slate, 3 + blotches, 4 + moss, 5 + lichen and chipped rim).
- **Gap shadows** (black under and beside every slate) are the first thing the eye reads; without them it is a grey grid. TESTED.
- **Different slate count and slide per row, plus the sine squeeze:** what makes it a roof and not a brick wall. TESTED.
- **Brush-stroke colour steps** stretched up-down (hard steps): the hand-painted look. TESTED.
- **Moss at the top, lichen near the bottom edge, bare chips on the rim.** TESTED.
- **Vertical sawtooth drips** at the bottom of each stroke, and a slow blue-to-green change across the whole roof: in your reference, NOT built yet.

### 6.3 Pitfalls and tricks
- **Cut the tile through the slates, not through a gap.** With a row boundary on the tile edge the scorer's seam number was 13.9; with half a row of shift it was 1.12. (The wrap was fine both times; the number was a false alarm. TESTED.)
- Per-row randoms only work if the row number is an exact whole number and wrapped (`Floored Modulo 8`); the slate number is wrapped by the row's own count.
- Wave amplitude: my first amplitudes (0.55 and 0.30 of slope) let the slope of the squeeze fall to 0.15, so that slate came out about 6.7 times wider than average and its side gap, which I measure in the slate's own units, 6.7 times thicker (thick black bars). With 0.40 and 0.20 the slope stays above 0.4. A better fix, which I did not build, is to divide the gap by the slope. TESTED (picture and reasoning).
- Instances need Set Material, and z-stacking of rows cannot repeat. TESTED.

### 6.4 Hand-painted look
Constant ramps on stretched noise (hard colour steps in vertical strokes), thick black gaps, light broken rim, flat olive moss. The reference's slates are not blue: they are grey-green (58,64,65) with blue and olive; my first palette was too blue (visible in `compare_slate.png`).

### 6.5 Which approach is closest to YOUR slate
**S5** for the flat tile (0.503; layout, gaps and brush strokes match, palette too blue, moss too yellow). **S3** if you later want real 3D slates on a roof model: it is quick to make and shows real overlap shadows, but the pictures still need S5's colour layers. S1 is far (0.183). S4 is unknown. Difficulty: S1 easy; S3 medium (a few dozen nodes); S5 medium-hard (156 nodes).

---

## 7. AGED WOOD PLANKS

**Plain meaning:** old wood is boards laid side by side, each made of long thin splinters running the same way as the board, with dark cracks between splinters, round knots with rings, and weathered grey patches over warm brown.

### 7.1 Approaches found

**W1. The stock Brick node as planks, plus a Wave Texture for the grain** - TESTED (stock chain), sources WEB ONLY
- Sources: Blender Insight "Procedural Wooden Floor" (Blender Market / Superhive docs; compatibility listed up to 2.93): "the Brick Width input is a holdover from the brick texture inside the group and is the length of the planks", edge wear "a major factor in realism". Kyra3D "Wood Procedural Shader" (Blender Market; up to 2.93; floor shaders: chevron, herringbone, plank). A common DIY recipe (my summary of general practice; I found no readable source that spells it out) is a Brick node made into one long thin row for the boards and a Wave Texture (Bands) for the grain, through Mapping.
- What I ran: Brick Texture Scale 1, Brick Width 1, Row Height 0.2, Mortar `#150f0c`, colours `#5b3b28` and `#8a5a38`, Noise (scale 25) into the colours, a Wave Texture (Bands, direction Y, Scale 40, Distortion 6, Detail 3) multiplied dark at 45 percent. Score **0.048** (colour 0.074, normal 0.0). Picture: `stock_chains_vs_reference.png` (third row): clean brown boards with faint grain; no cracks, knots or splinters.

**W2. Wave + Voronoi with Color Ramps** - WEB ONLY
- Source: the book "Blender 3D By Example" (a wood shader: a Wave Texture for the main grain, a Voronoi for flecks, Color Ramps and Mix nodes to shape both, a Greater Than node from the first Wave to separate two grain layers, Mapping for scale, Reroutes to share one coordinate). Undated search listing.
- The Blender Bazaar "procedural concrete" tutorial (listing seen only in search results) makes cracks with Voronoi **Distance to Edge**, a smaller Scale, and a Color Ramp whose stop position sets the crack size, into Bump. Wood cracks use the same idea stretched along the grain (my W5).

**W3. Mathematics: growth rings and knots from a formula** - WEB ONLY
- Source: Blender Artists, "Semi-Pro Procedural Wood Texture" (thread, ChengHan, 4-9 Aug 2024; etn249 advising). Ported from POV-Ray code: annual rings from the distance `sqrt(x^2 + y^2 + (z/b)^2)` (like a Wave Texture), distorted by the angle round the trunk; knots made by hand with a distortion that applies only inside an angular window and equals 1.0 outside it; parameters `knot_theta_pos`, `knot_theta_range`, `knot_h_pos`, `knot_strength`, `knot_power`. Known faults: knots near angle 0 / 2 pi render wrongly; knots placed close together overlap. Shading advice: run the grey result through a Color Ramp; Principled Specular about 0.397, Roughness 0.2 to 0.5; **Bump Distance starting at 0.0004** and raised until the detail shows; an **Ambient Occlusion node** to lighten varnish on sharp edges.
- Also, Blender Artists "Procedural Wood Material", Ssendam (Lance Phan), 1 Mar 2026 (a product, USD 30; BlenderNation "Best of Blender Artists" 2026-10): nested cylindrical layers as a **3D volume texture, so no UV map**; "cutters" cut the input coordinates to make 7 floor patterns, glued wood and plywood; the node chain is not described.

**W4. All-in-one layered node groups (structure to copy)** - WEB ONLY
- Rebellious Studios "Rs Procedural Wood" (Superhive docs; Blender 4.5-5.1; USD 25): layers **board layout** (scale, length, width variation, staggering, end joints), **grain** (scale, distortion), **rings** (frequency, distortion, contrast), **knots** (density, size, variation, distortion, depth, colour variation), **gaps** (width, colour), **edge wear** (mask with width and intensity), **weathering** (scale, amount, influence), colour variation; outputs Height and Roughness; a Random seed; coordinates UV / Generated / Object / Window.
- Erindale Woodford (Gemn) "Timber", Blender Artists, 7 Aug 2019 (free): lay straight or herringbone, board length and gap width, lateral grain compression, wobbly grain, three grain value bands, tangential or quarter-sawn boards, knots, a random seed; the Pro version (Cycles only: its node count is above Eevee's limit) adds nails, medullary rays, splitting, planer ripple.
- Quantum_Anomaly, "Believable procedural wood in Cycles", 19-20 Jun 2014: vector math from another poster's approach, then a second branch with slightly varied coordinates and its own colour ramp so each floorboard differs; subtle displacement and gloss.

**W5. Splinter strips from a stretched Voronoi (my recipe)** - TESTED
- Chain (`recipes/recipe_wood.py`):
  1. **Boards of different heights:** v + two sine waves that repeat exactly 2 and 5 times (amplitudes 0.40 / (4 pi) and 0.16 / (10 pi)), times 6, Floor = board, Fraction = position across the board; gap = the first 0.0048 of each board, ragged by noise.
  2. **White Noise of the board number:** warm or grey board, tint, where the end joints are, a noise seed (about four boards in ten get one vertical joint).
  3. **Splinter strips:** `tvoronoi(3, 30, randomness 0.85)` (3 cells across the tile, 30 up), **Color output** -> red channel through a Constant ramp of 6 warm browns, or 4 greys, or 3 blue greys, chosen by the green channel plus the board's greyness.
  4. Grain: `tnoise(4, 220)` with the board's own seed, light streak window 0.57 to 0.59, dark streak 0.43 to 0.41. Weathered grey-blue patches: `tnoise(3.5, 14)` cut at 0.72 on warm boards down to 0.56 on grey boards. Thin warm orange flakes: `tnoise(5, 60)` window 0.66 to 0.675.
  5. **Cracks:** the SAME Voronoi (same seed and randomness) with feature **Distance to Edge**: dark where the distance is below 0.008 + 0.04 x a gate noise (`tnoise(5, 7)` from 0.45 to 0.7), so cracks are thick where the gate is high and fine elsewhere; a warm chip band 2.6 times wider where the gate is above 0.55.
  6. **Knots:** four fixed centres; ellipse distance (v stretched x 1.5), rings = `fract(distance x 95 + noise x 1.2)` dark below 0.28, a dark core, inside a zone of radius 0.055.
  7. Splatter: small noise blobs (window 0.60 to 0.62) allowed only inside a cloud noise (window 0.50 to 0.52). Pebbles in the gaps: `tvoronoi(110, 110)` F1 distance below 0.30.
  8. Height = screen brightness, stretched (0.02 to 0.48).
- Result (`compare_wood.png`, `layers_wood.png`): the dark splintered, blue-grey and orange look of your wood is there; the strips are too lens-shaped and regular and the orange chips are too bright. Score **0.325** at 512 px; at 384 px with three seeds 0.455, 0.340, 0.347 (the biggest swing of the six; section 3.3).
- The first version (clean boards, vertical joints, grain streaks, no strips) scored **0.082**, then 0.156 after a colour fix; adding the splinter strips raised it to 0.308 and 0.325. Lesson: your wood is mostly splinters, not boards.

### 7.2 Layers that make this wood look right
Pictures: `layers_wood.png` (1 boards and gaps, 2 + splinter strips, 3 + grain, grey patches, flakes, 4 + cracks, 5 + knots, 6 + splatter, joints, pebbles).
- **Splinter strips with a tone each** (biggest change). TESTED. **Cracks along the strip borders.** TESTED. **Grain streaks** (stretched noise, hard steps) and **grey weathered patches** on grey boards. TESTED. **Knots with rings.** TESTED. **Splatter blotches in clouds.** TESTED.
- Edge wear and varnish lightening with AO or Bevel on real geometry (W3, W4): NOT TESTED (your reference has no varnish).

### 7.3 Pitfalls and tricks
- Stretch by giving different feature counts across and up (`tnoise(4, 220)`), not by scaling the picture afterwards. TESTED.
- Cracks and strip tones must come from the same Voronoi settings, or the cracks do not follow the strips. TESTED.
- Voronoi Distance to Edge is measured in cell units, not tile units (0.008 to 0.048 above); Voronoi cells stretched to 30 rows are only 4 px thick at 128 px: look at 512 px or more.
- Knots: stay away from the tile edge (mine are not periodic by themselves; a knot crossing an edge would need a wrapped distance). A forum thread (W3) reports knots near an angle seam and overlapping knots misbehaving.
- Boards of different heights from a repeating sine of v: the slope must stay below 1 (here 0.40 + 0.16 = 0.56). TESTED.

### 7.4 Hand-painted look
Hard-edged strip tones (Constant ramps), flat orange chips along cracks, dark crack lines, flat splatter blotches. W3's advice to use a Color Ramp on the grey result is the smooth version of the same idea.

### 7.5 Which approach is closest to YOUR wood
**W5.** Why: your reference is a heap of splinters with tapering cracks and splatter, not tidy boards; the stock chain W1 reaches 0.048 because it can only make tidy boards. W3's knots and W4's layer list are good to borrow (knot parameters; gaps; edge wear), but the node chains are not published, so I cannot say how close they would get (estimate: about W1 level for boards, better for knots; NOT TESTED). Difficulty: W1 easy; W5 medium-hard (411 nodes, 304 of them small Math nodes); W3 hard (maths).

---

## 8. RUSTED, RIVETED METAL

**Plain meaning:** a dark steel plate with straps and braces laid on it, rows of domed rivets, rust that collects at the edges and runs down in drips, bare-metal chips and a few scratches.

### 8.1 Approaches found

**M1. Noise + Bump + two Color Ramps (the classic rust shader)** - TESTED (reconstruction)
- Source: Blender Bazaar, "Making a procedural rusted metal material", JSAbbott, 24 Feb 2024, Blender 4.0. Chain as listed: **Bump** (Strength 0.3) <- Color Ramp (white stop moved to 0.495 "creates the smooth areas") <- **Noise** (Scale 3, Detail 12, Texture Coordinate set to **Object**, so it does not depend on UVs); a second Bump (Strength 0.15) <- Noise (Scale 6, Detail 24); colour = Color Ramp 1 (white stop mid grey `#858585`, black stop 0.4, white 0.75) mixed with Color Ramp 2 (stops `#832912`, `#8B310B`) in a **Mix node set to Screen**; Principled **Metallic 1.0**. The page sets no Roughness and has no separate rust mask (the first noise drives both ramps); its steps 13 and 14 contradict each other about the final link.
- What I ran: those nodes with my guesses for the missing stop positions. Score **0.107** (colour 0.057, normal 0.517). Picture: `stock_chains_vs_reference.png` (bottom row): a red-pink cloud; no plate layout at all.

**M2. Mask-driven wear: Pointiness, Bevel or AO for edges, noise to break it up, a Mix Shader of clean and worn** - partly TESTED, sources WEB ONLY
- Sources: Lester Banks' summary of a Blender Buzz technique (Geometry node **Pointiness** finds edges, then mix clean and worn materials by that mask); StraySpark "procedural edge wear blender" (29 May 2026, Blender 4.2): Pointiness or a baked curvature map -> Color Ramp tightened "so only the sharpest edges read white" -> `Mix Shader(clean, worn, Fac = edge mask)` -> multiply the mask by a Noise so the wear is patchy -> cavity mask for dirt; StraySpark "procedural weathering blender geometry nodes" (12 Apr 2026): Geometry Nodes edge wear (Edge Angle above 0.3 rad about 17 degrees -> Blur Attribute -> Map Range -> Store Named Attribute "edge_wear"), gravity dirt (Normal Z -> Map Range 0.3 to 1.0 -> multiply by Noise), **Voronoi F1 rust patches** (scale about 4 -> Color Ramp -> multiply by Noise -> multiply by a moisture or cavity mask; rust roughness 0.8 to 0.95). I read that page critically: Edge Angle is a fold angle, not curvature; "world versus object space" and "vertex colour export" statements are unclear; the scale "4.0" is unitless; the promotional numbers ("15 to 20 hours") have no support.
- Blender Artists "Procedural rust streaks" (2019 posts; Secrop, pauljs75_, F.Collioud, unfa; a 2025 request for the file): Voronoi through Math **Greater Than** for round spots; a Noise into the **Z coordinate** to fade streaks downward (works best with high contrast); slope from the Z of the Normal with `tan(asin(Nz))`; crisp holes with a further Voronoi through a Color Ramp set to Constant; **drips by directionally blurring the rust patch masks with a fine Noise** (unfa, 3 Dec 2019, Blender 2.8, Eevee).
- BlenderNation: Sanctus "How to make procedural rust and blisters" (24 Apr 2021) and Erin "Procedural weathering and wear with Blender 2.83" (13 Oct 2020, "mud, rust, scratches, edge wear"): both are videos; the pages carry no node text.
- My related TEST (M3 below): the Bevel node on real straps and rivets does give a clean edge mask.

**M3. Real straps and rivets from Geometry Nodes, then Bevel for the edge wear** - TESTED (my build); sources WEB ONLY
- Sources: "Bolt Gen - Geometry Nodes Rivet/Bolt Generator" (Superhive / Gumroad, USD 5.99, Blender 4.2 to 5.0): instances a bolt along edges by spacing or one per vertex, with randomisation, optional shrinkwrap to an alignment mesh, normal blending; Blender manual Instance on Points. A Surface Effects add-on listing says its edge wear works only in Cycles because it relies on the Bevel node.
- My chain (`geo_rivets_bevel.py`): two Mesh Cubes (0.11 x 1.4 and 1.4 x 0.09, 0.012 thick) for the straps, a **UV sphere flattened to 0.6** for the rivet, **Mesh Line** (8 points) along each strap -> Mesh to Points -> Instance on Points -> Realize; every part through a Set Material node. Photograph from above in Cycles: height from Z, and an **edge-wear mask = 1 - dot(Bevel normal, true normal), times 14, clamped** (Bevel Samples 16).
- Result: `geo_rivets_height_and_bevel_masks.png`. Bevel Radius 0.004 draws thin bright lines along the strap edges and rivet bases; Radius 0.010 draws bolder ones. The whole run took about 8 s at 512 px. A shader-only painted strap has no geometry edge, so the Bevel mask finds nothing there.

**M4. A layout described by numbers (my recipe)** - TESTED
- Chain (`recipes/recipe_metal.py`):
  1. Plate colour: `tnoise(60, 6)` (60 across, 6 up = vertical streaks), 5 hard steps of blue-grey, dark blotches.
  2. **Bands as signed distances:** vertical strap = `|u - centre| - half width`; horizontal strap = `|fract(v - centre + 0.5) - 0.5| - half width` (this one wraps round the tile edge); brace = the perpendicular distance to a slanted line (cross product with the direction) with its two ends cut by the along-the-line distance. Numbers: vertical straps at u 0.0885 (half width 0.0475) and 0.583 (0.0505); horizontal at v 0.4625 (0.038) and 0.004 (0.060); braces 0.55 and 0.53 long, half width 0.036.
  3. Each band is laid on in turn: inside mask, a dark outline where the inside distance is under 0.0035, a light edge line from 0.0035 to 0.0075.
  4. **Rivets:** for each row, the distance to the nearest rivet centre from `fract((u - phase) / spacing + 0.5) - 0.5` (spacing 1/8, radius 0.017); inside the radius a dome ramp (dark bronze to light, lit from the top-left) and a dark ring. The wrapped difference makes a rivet that sits on the tile edge continue on the other side.
  5. **Wear:** rust = `tnoise(6, 6, distortion 0.5)` + 0.06 x (1 - Map Range of the distance to the nearest strap edge, 0 to 0.05), cut at 0.60 / 0.615, four flat rust steps; brown mottling; grey scuffs; **drips** = `tnoise(70, 5)` window times `tnoise(7, 3)` window; bare-metal chips with a small edge bias; two scratches = distance to a line segment (0.0012 wide).
  6. Height = screen brightness, stretched. Roughness 0.55 to 0.9 and Metallic 0.9 to 0.1 follow the rust mask (not scored: the references have no such maps).
- Result (`compare_metal.png`, `layers_metal.png`): straps, braces, rivets, outlines and scratches line up with your layout; rust is too sparse and too clean-edged (yours is mottled and pitted all over). Score **0.286**.

### 8.2 Layers that make this metal look right
Pictures: `layers_metal.png` (1 plate with brush streaks, 2 + straps and braces, 3 + rivets, 4 + brown, scuffs, rust, 5 + drips, bare-metal chips, 6 + scratches).
- **Straps with outline and edge highlight** (TESTED; the biggest gain), **domed rivets in rows** (TESTED), **rust that likes edges** (TESTED), **brown mottling and grey scuffs** (TESTED), **drips** (TESTED), **chips** (TESTED), **scratches** (TESTED). Roughness and metallic differences between rust and clean paint (TESTED as maps, not scored).

### 8.3 Pitfalls and tricks
- With the edge-bias at 0.16 and a rust cut at 0.60 the whole plate turned to rust and hid the straps (picture `metal_first_try_rust_too_heavy.png`); 0.06 and 0.60 fixed it. Judge a rust cut with the straps visible.
- Rivet rings that were not limited to the brace area showed as hollow circles outside the braces. TESTED (fixed in the recipe).
- A rivet row whose spacing does not divide 1 breaks the wrap; use 1/8, 1/10. A rivet on the tile edge needs the wrapped difference. TESTED.
- Bevel-based wear needs Cycles and real geometry; Pointiness depends on mesh density (shader-toolbox guide, TESTED there).
- Bump "Strength 0.3" in older tutorials: since 4.5 the default Distance is 0.001, so the same chain looks almost flat (shader-toolbox guide, TESTED there).

### 8.4 Hand-painted look
Rust in four flat steps, a dark outline and a light edge line on every strap, hard-edged scuffs, flat chips. Your reference rust is pitted and mottled, so a second, finer rust layer would help (not done).

### 8.5 Which approach is closest to YOUR metal
**M4** for the colour picture (0.286 against 0.107 for M1), because only an explicit layout can reproduce a one-off composition of straps and braces. **M3** is the route if you want real raised rivets and straps with true bevelled edges (and then M2's edge mask for the wear), at the price of a Cycles-only mask and a non-tiling photograph unless you add ghost copies. Difficulty: M1 easy; M4 medium-hard (552 nodes, 412 of them Math nodes: most are the band and rivet distance sums); M3 medium (a few dozen nodes plus the wear materials).

---

## 9. WET MUD WITH RUTS, STONES AND PUDDLES

**Plain meaning:** a brown mud ground cut by wheel ruts (long curved grooves with raised banks), with blue-grey water lying in the low places and stones of several sizes scattered over it.

### 9.1 Approaches found

**D1. Voronoi "Distance to Edge" dirt with a Noise overlay, puddles from Noise + Voronoi** - TESTED (reconstruction)
- Sources: Blender Bazaar, "Making a procedural dirt/water puddles material", JSAbbott, 4 Mar 2024, Blender 4.0; BlenderNation, "Make a Procedural Dirt Texture (+Puddles) in Blender 2.9", Jennifer Abbott, 24 Dec 2020 (page lists only the node names with time stamps: Voronoi, Texture Coordinate, Noise, Mix RGB, two Color Ramps, a second Noise; Voronoi + Bump for detail; Noise + Voronoi + Color Ramp + Mix RGB for puddles).
- The 2024 chain as listed: Voronoi **Distance to Edge**, Scale 3, Object coordinates -> Mix Color **Overlay** with a Noise (Scale 175, Detail 15) -> Color Ramp (white stop pulled in to cut the noise) -> second Color Ramp (`#3A251C`, `#A4764A`, `#BE8655`) -> Mix **Add** with a Noise (Scale 7.5, Detail 15) -> Principled Base Color; the first ramp also drives a **Bump**. Puddles: Noise -> Voronoi (Scale 1) -> Color Ramp (move the black stop right to widen the puddles) -> **Roughness**, and a third Mix (Overlay) into the bump input. No roughness numbers and no bump strength are given.
- What I ran: those nodes with guessed ramp positions. Score **0.080**: cracked-earth cells in tan, no ruts, no stones; the puddle mask only changes Roughness, so there is nothing blue in the colour picture. Picture: `stock_chains_vs_reference.png` (fourth row).

**D2. A puddle block (wet rim, flat water bed, low roughness)** - WEB ONLY here; tested in the shader-toolbox guide
- Sources: Blend Swap 19340 "Procedural Puddles Material" (a node group; its notes say to use a separate Mapping for the puddles and that they have "a small normal map for ripples"); Postshade "Puddle FX" (product; Eevee and Cycles; "mud to puddles"); a short free tutorial of Principled + Noise + Color Ramp with Object coordinates (listing seen in search results).
- The shader-toolbox guide (section 8.10, TESTED there) built it: wet rim from a Map Range of the height, roughness 0.9 -> 0.35 -> 0.02, a flat water bed with `Maximum(height, level)`, IOR 1.33, blue-grey colour. Our baked colour picture needs only the colour step of it.

**D3. Dynamic Paint wheel tracks** - partly TESTED
- Sources: Lester Banks' posts on "Creating Wet Tire Track With Blender's Dynamic Paint" (Sardi Pax) and tracks and splashes (Richard Shilling, Dikko); Packt chapter and Flipped Normals course (Dynamic Paint can drive displacement, image sequences, colour maps); CG Cookie forum "Dynamic Paint over a large area": use it as a bump or height map rather than true displacement, depending on camera angle.
- My attempt (`geo_dynamic_paint_ruts.py`): a plane divided 220 x 220 as canvas (type **Displace**, format Vertex, 1 to 50 frames), a cylinder wheel (radius 0.06, 0.012 below the plane) as the brush moving along x. Findings: it runs headless; **`bpy.ops.dpaint.type_toggle(type='BRUSH')` alone left the brush's `ui_type` as CANVAS and nothing happened; setting `modifier.ui_type = 'BRUSH'` as well made it work**; `dpaint.bake` finished in 0.0 s with no effect (I tried it only before the `ui_type` fix), while stepping `scene.frame_set` 1 to 50 gave the displacement. But the displacement was only 0.0006 to 0.0009 in height for Displace factor 0.03 to 0.05 (use_incremental off or on), so the height picture was flat. I stopped there: I did not find which setting scales the depth. Everything after this is NOT TESTED (depth tuning, baking, tiling: the track ends inside the tile and is not periodic).

**D4. Curves and Geometry Nodes ruts; particles** - WEB ONLY
- Sources: a render-forum reply (a spline along the tyre's contact path, extruded as a masked surface; "layered noise inside a thick line"; curved marks are the hard part); Procedural Tank Track and Track Tools (products; wheels and track pieces along a curve); BlenderNation, "Creating Tire Tracks with Particles in Blender 2.92", luwizart, 2 Jan 2021 (the page has no steps). The sibling guide's recipe (`experiments_geometry_nodes_curves_modifiers_physics/recipe_curve_ruts.py`, not mine) builds ruts as real curves with a Geometry Proximity distance profile; I did not run or judge it.

**D5. A rut coordinate bent by noise (my recipe)** - TESTED
- Chain (`recipes/recipe_mud.py`):
  1. **Rut coordinate** `s = u + v + 0.55 x (tnoise(2,2) - 0.5) + 0.045 x sin(2 pi (2u - v) + 1)`. Whole numbers added to u or v add whole numbers to s, so the bands wrap. A second family `s2 = u - v + ...` crosses it; it shows only where a gate noise allows.
  2. **Rut cross-section** `c = |fract(4 s) - 0.5|`: groove where c < 0.035 to 0.05 (dark `#2f211b`), banks 0.05 to 0.09 (lighter `#bb875f`), a thin darker wheel line.
  3. Ground: `tnoise(12, 12, distortion 0.35)` in six hard brown steps; **streaks along the ruts** = `tnoise(34, 5, coords = (s, v))`; clumps `tnoise(46, 46)`.
  4. **Puddles:** `tnoise(3.5, 3.5)` + 0.18 x (a fine jagged noise - 0.5) - 0.05 x groove, cut at 0.40 (ragged edge); a wet rim band to 0.44; water = six flat blue-grey steps from `tnoise(7, 7)` plus dark reflection patches.
  5. **Stones** (`stone_tools.polygon_stones`, section 3.5): three layers (cells across the tile / share of cells with a stone): 12 / 0.12 (big), 24 / 0.28 (medium), 52 / 0.7 times a cluster mask (pebbles); dark blue-grey tones from the stone's own number, some tan, a light face and a dark face from the direction each flat face looks, a dark outline.
  6. Height = screen brightness, stretched (0.03 to 0.50).
- Result (`compare_mud.png`, `layers_mud.png`): crossing S-shaped ruts, ragged blue puddles and faceted stones read like your tile at a glance. Too regular: parallel ruts, one big puddle, pebbles on a visible grid. Missing: the crumbly ground and the dense scatter of mid-sized stones. Score **0.353** at 512 px (0.406 one edit earlier; 0.407 to 0.430 at 384 px with three seeds; section 3.3). First attempts: Voronoi-cell stones 0.204; polygon stones with the first rut layout 0.167, 0.24, then 0.41.

### 9.2 Layers that make mud look right
Pictures: `layers_mud.png` (1 flat brown ground and streaks, 2 + ruts, 3 + puddles, 4 + pebble clusters, 5 + medium and big stones).
- **Ruts with a groove, banks and a wheel line** (TESTED; the score jumped from 0.24 to 0.41 when I added a second rut family and bigger puddles). **Puddles with ragged edges and a dark wet rim** (TESTED). **Streaks along the ruts** (TESTED). **Three sizes of stones with light and dark faces** (TESTED). **Crumbly ground texture** (in your reference; not built).

### 9.3 Pitfalls and tricks
- Rut coordinate numbers must be whole (u + v, u - v, 2u - v, u + 3v are fine). A bend noise must be periodic (`tnoise`, not the stock Noise). TESTED.
- Stretch a streak noise along the ruts by reading the noise in `(s, v)` instead of `(u, v)`: `b.tnoise(34, 5, coords=(s, v))`. The pair `(u + v, v)` is a one-to-one map of the tile, so it wraps. TESTED.
- Stones inside puddles: mine are drawn over the water (real stones stand in water too). Draw order: ground, ruts, puddles, then stones small to big.
- First stones came out 100 px wide at 512 px (20 percent of the tile): count the cells (12, 24, 52), not the radius, to control the size. TESTED.

### 9.4 Hand-painted look
Flat steps for ground and water, dark reflection patches, a dark wet rim, a lighter bank beside every groove, stones with two flat faces and a dark outline.

### 9.5 Which approach is closest to YOUR mud
**D5** (0.353) far ahead of **D1** (0.080). The ruts of your reference are many thin criss-crossing grooves with ragged banks; D4 (real curves) or more rut families in D5 would get closer. D3 is unproven here. Difficulty: D1 easy; D2 medium; D3 medium to hard (physics); D5 medium-hard (780 nodes with three stone layers; the stone layers are most of it).

---

## 10. GRAVEL / BALLAST / RUBBLE

**Plain meaning:** a ground packed with angular stones of every size, dark and blue-grey with a few rusty ones, with orange-brown soil showing in the gaps.

### 10.1 Approaches found

**G1. A shader-only rock/ground from Voronoi, ramps and bump** - WEB ONLY (page), one part TESTED
- Source: Blender Bazaar, "Procedural rocky ground material", Ryan King Art, 25 Jan 2024, Blender 4.0, free: the listing says colour and roughness come from Color Ramps and the surface from a Voronoi into bump or displacement; the steps are in a video ("Procedural Rocky Ground Material (Blender Tutorial)") that I could not read. Blender Bazaar rock shader (listing seen in search results): ramps for colour and roughness, a Voronoi into Displacement.
- My related TEST: stones made by shrinking Voronoi cells (first mud recipe) came out as daggers and slivers (`mud_first_try_voronoi_stones.png`, score 0.204 in mud).

**G2. Geometry Nodes scatter of stone instances** - TESTED (my build); sources WEB ONLY
- Sources: Superhive "Geometry Nodes Scatter Rocks - Blender 3.6+" (a Poisson Disk option "gives better control (a minimum distance) but is heavier"; a Voronoi/Noise random option; min and max scale; lower the density before switching modes to avoid crashes); Geon Scatter Rocks (Sebastien Garnier; density relative to surface area); ScatterCraft; Rock Pipeline (layered scatter with density, scale and weight maps); the Blender 2.92 Geometry Nodes release notes (a pebble scattering sample file by Simon Thommes; a BlenderNation article of 18 Dec 2020 shows the same feature); a Blender 4 geometry-nodes course lesson "Adding Low Poly Pebbles and Grass".
- My chain (`geo_gravel_scatter.py`): Mesh Grid 1 x 1 -> Distribute Points on Faces (**Poisson Disk**, Distance Min 0.045, Density Max 4000) -> **Instance on Points** (Instance = an Ico Sphere (radius 0.5, 1 subdivision) with a random offset per vertex up to 0.16 and flattened to 0.7, through Set Material; Rotation = Euler to Rotation of a random vector 0 to 6.283; Scale = random vector between (0.030, 0.026, 0.02) and (0.070, 0.060, 0.04)) -> Cycles top-down.
- Facts (`out/geo_gravel_poisson_plain/facts.json` and the ghost and random variants):

| Variant | Stones | Nearest neighbour inside the tile | Nearest neighbour across the tile edge |
|---|---|---|---|
| Poisson Disk, distance 0.045 | 308 | min 0.04501, mean 0.0495 | **0.0104** |
| Poisson Disk + copies one tile away in 8 directions | 308 in the tile (2772 incl. copies) | same | **0.0104** |
| Random distribution (500 per square) | 500 | min 0.0015 (stones overlap) | 0.0015 |

- So Poisson Disk honours the distance inside the tile but not across the seam; copies make the picture repeat but the stones still crowd at the seam. The picture `geo_gravel_scatter_variants.png` shows the three variants (colour, height, 2 x 2 tiling). The stones are too sparse (22 percent of the tile is above the ground in the Poisson picture, 30 percent in the random one) and flat-coloured: unlit emission, one colour per stone, no soil, no faces, no outline. As raw pictures they score only **0.038 to 0.055** against your gravel (and the slate rows 0.166 against your slate); to get close they need the same colour layers as the shader recipe.

**G3. Rigid-body drop** - TESTED (my build); sources WEB ONLY
- Sources: polygoniq quick tip, 1 Nov 2023 (plane with Subdivision and Displacement from a Cloud texture, applied; Rigid Body **Passive**, Shape **Mesh**, Source **Deform**; an Ico Sphere set **Active**, duplicated in Edit Mode, Separate by Loose Parts, Origin to Geometry; then **bake** the Rigid Body World; no numbers are given); Ossim (Gubin, a paid rigid-body baking add-on); a MODDB tutorial on baking normal and AO maps: to make a rock surface tileable, "fill all the opposing edges with the same models", then bake from a flipped copy; OpenGameArt "Tileable Rock Scattering" (a Geometry Nodes file on the XY plane that leaves ground displacement out; exports to glTF).
- My run (`geo_physics_gravel.py`): 160 lumpy icospheres (random size 0.04 to 0.09, random turn, dropped from random heights 0.12 up) as **Active** rigid bodies (Convex Hull, friction 0.8) into a 1 x 1 tray (a passive floor and four passive walls), 130 frames stepped with `scene.frame_set`. It took **10.3 s**; 157 of 160 stones stayed in the tray (3 escaped); the picture is `geo_physics_gravel_colour.png` (a believable heap; 42 percent of the tile is covered) but it is cut by the walls at the edge, so it does **not** tile. Score of the raw picture **0.058**.

**G4. One random polygon per grid cell in the shader (my recipe)** - TESTED
- Chain (`recipes/recipe_gravel.py`, `stone_tools.polygon_stones`, section 3.5): soil = `tnoise(26, 26)` in six hard orange-brown steps plus crumbs (`tnoise(90, 90)` windows); four stone layers drawn small to big (cells across the tile: 72, 30, 15, 8; share of cells with a stone 0.55, 0.62, 0.60, 0.55; five faces, the largest six); stone colour = eight-step Constant ramp of dark and blue-grey (the four darkest steps cover about half of the stones) from the stone's own number, a rusty brown on 45 / 12 / 10 / 10 percent of stones per layer, two flat mottling steps from a noise (windows 0.58 to 0.60 and 0.40 to 0.38), a light face (face brightness above 0.30, 20 percent toward `#bfcad4`), a dark face (below -0.30, 42 percent darker), a dark outline.
- Result (`compare_gravel.png`, `layers_gravel.png`, `sweep_gravel_faces_per_stone.png`, `sweep_gravel_stone_presence.png`): it reads as gravel on rusty soil at once and tiles (half-tile test 1.58 percent). Compared with your tile the stones are too big, too gem-like and glossy, too evenly spread; yours are smaller, blockier and packed tighter with orange crumbs between. Score **0.223** (colour 0.266, height 0.074, normal 0.474); the darker version scored 0.223, the first 0.193.
- **Setting sweeps:** faces per stone 3 = triangular shards, 4 = blocks (closest to your blocky stones), 5 to 8 = rounder; share of stones 0.4 = mostly soil, 1.4 = nearly packed.

### 10.2 Layers that make gravel look right
Pictures: `layers_gravel.png` (1 soil only, 2 + tiny stones, 3 + small stones, 4 + medium stones, 5 + large stones).
- **Several stone sizes drawn small to big** (TESTED), **mostly dark tones plus blue-grey plus a few rusty** (TESTED), **a light face and a dark face on every stone** (TESTED), **dark outlines** (TESTED), **crumbly soil between** (TESTED, still too smooth). A **stone shape with 4 faces** for your blocky stones: TESTED in the sweep, not yet used in the final recipe.

### 10.3 Pitfalls and tricks
- Instances without a Set Material node render black. TESTED.
- Poisson Disk and ghost copies do not give correct spacing across the tile edge (0.0104 against 0.045). TESTED.
- Physics gives a believable heap but walls cut it at the edge; to make it tile you would need periodic boundaries or a bigger drop cropped and repaired (the sibling seamless-tile guide covers crossfade repair). NOT TESTED here.
- Stones confined to their own grid cell keep the shader fast and periodic but leave a faint lattice; the warp (0.5 to 0.6 cell) hides most of it; stones of different layers overlapping hide the rest. TESTED (picture).
- Voronoi-cell stones: daggers. TESTED.

### 10.4 Hand-painted look
Flat tone per face (two or three tones per stone), a dark outline, mottling in two flat steps, no gradients. This is how your reference stones look.

### 10.5 Which approach is closest to YOUR gravel
**G4** (0.223, and the best-looking picture). G2 and G3 produce true 3D heaps with real shadows and silhouettes (useful for a 3D ground, and the height map is real), but as photographs they were far from your picture (0.04 to 0.06) until given the same colour layers; neither tiles without extra work. G1 is unknown (the video is not readable). Difficulty: G2 medium (a few dozen nodes); G3 medium (a script or physics setup; seconds to run); G4 medium-hard (870 nodes, 33 to 37 s per 512 px bake on 2 shared threads).

---

## 11. The hand-painted / stylised look across all six (what the sources say, what I tested)

**Plain meaning:** a hand-painted tile is made of FLAT areas of colour with hard edges and dark outlines, not of smooth gradients. In Blender that means cutting a smooth pattern into a few steps.

What the sources say (all WEB ONLY unless marked):
- Blender Artists answer in "Wooden floor with Brick shader" (DNorman, 20 Aug 2023): replace Math "Greater Than" nodes by a **Color Ramp set to Constant** with two stops.
- BlenderNation, Martin Klekner, 26 Oct 2025, "How to Create a Hand Painted Look in Blender": toon shading with **Shader to RGB + Color Ramp** (Eevee), optional texture painting, **Grease Pencil outlines**. The page has the introduction only.
- 80 Level, 18 Aug 2026, lassyla's fully procedural EEVEE shader "with no actual hand-painting": "Noise plays a big role". The article has no node details (the video and the pay-what-you-want shader do).
- Skillshare, Harry Helps, "Procedural Hand Drawn Texture" (ColorRamp, Shader to RGB, Math; Blender 3.5 or newer; listing only). BlenderNation, Levi, 21 Jan 2025: a stylised crystal shader from shader nodes with hand-drawn-looking line art and compositing (summary only).

What I tested (`posterize_kinds.png`, `posterize_steps.png`, one seamless noise, same palette):
- **Color Ramp, interpolation Constant**: N stops = N flat colours, hard edges. TESTED, used in every recipe.
- **Map Range, interpolation "Stepped"**: Steps = N gives **N + 1 levels** (2 steps gave 3 flat tones, 10 steps are nearly smooth). TESTED. There is **no Posterize node in the shader editor** (from the addable-node list in the shader-toolbox guide); the compositor has one but it cannot be used inside a material.
- **Math "Snap" (increment 0.25)** and **Math "Round"** on the value times 3: the same stepping. TESTED.
- **Map Range with a window only 0.02 wide**: a single hard mask edge (best for patches and outlines). TESTED.
- **Shader to RGB**: one flat colour in Cycles (the toon effect needs EEVEE, which I cannot run here). TESTED.

The tricks that gave the painted look in the recipes: (1) a Constant ramp on a stretched noise for strokes and strips, (2) hard windows (0.02 to 0.04 wide) for patches, (3) a dark band just inside every edge for the outline (distance to the piece edge < 0.0035 to 0.0045 of the tile), (4) a different random tone per piece (brick, slate, stone) chosen through a Constant ramp, (5) a light face and a dark face per stone from the face direction, (6) height from the colour so the relief follows the paint (section 1, fact 6).

---

## 12. Summary table: surface x approach x expected closeness x difficulty

"Closeness" = the measured score (overall, 512 px, normal seed; 0 = another surface, 0.5 = the best I reached; your own reference re-shuffled would score about 0.99) where I measured it; "est." = my guess without a test (labelled NOT TESTED). "Stock chain (reconstructed)" = built from an incomplete step list, with my guesses for the missing numbers. Eye verdicts come from the pictures.

| Surface | Approach | Expected closeness | Difficulty | Tested? |
|---|---|---|---|---|
| Brick | B1 stock Brick node + noise + Voronoi paint (Bazaar 2024) | **0.065** (clean even rows, no outline, no soot) | easy | yes (reconstructed) |
| Brick | B2 per-brick threshold mask (forum 2023) | used inside B4 | easy | idea used in B4 |
| Brick | B3 two Brick nodes for chipped edges (forum 2022) | est. 0.1 to 0.2: better edges, still no per-brick patches | medium | NOT TESTED |
| Brick | **B4 home-made layout + per-brick numbers (mine)** | **0.327** (0.41 to 0.43 at 384 px): layout, outline, palette right; soot too streaky | medium-hard | yes |
| Brick | B5 Geometry Nodes bricks (products) | est. low for colour alone; gives real depth and shadows | medium | NOT TESTED (slate analogue tested) |
| Brick | B6 damage-group bundles / video courses | est. 0.2 to 0.3 with the colour layers | n/a (paid) | NOT TESTED |
| Slate | S1 stock Brick node, narrow rows | **0.183** | easy | yes |
| Slate | S2 tile image as bump and mask (2.5-era book) | not allowed (uses a painted picture) | easy | NOT TESTED |
| Slate | S3 Geometry Nodes slabs + Object Info random | **0.166** as a raw flat photograph; reads as a roof | medium | yes |
| Slate | S4 roof-tile shader with masks and per-tile UVs (2020) | est. 0.3 to 0.4 if its masks get my colour layers | hard (file only) | NOT TESTED |
| Slate | **S5 home-made rows + sine squeeze (mine)** | **0.503** (the best of the six): layout, gaps, strokes right; palette too blue | medium-hard | yes |
| Wood | W1 stock Brick node planks + Wave grain | **0.048** | easy | yes |
| Wood | W2 Wave + Voronoi + ramps (book) | est. about W1 level | medium | NOT TESTED |
| Wood | W3 maths rings and knots (forum 2024); 3D volume wood (2026) | est. good knots and rings, but your wood is splinters | hard | NOT TESTED |
| Wood | W4 all-in-one layered groups (Rs Procedural Wood, Timber) | est. 0.1 to 0.2 (tidy boards, edge wear) | easy to use, hard to build | NOT TESTED |
| Wood | **W5 splinter strips from a stretched Voronoi (mine)** | **0.325** (0.34 to 0.455 at 384 px by seed): the splintered, dark, blue-grey look | medium-hard | yes |
| Metal | M1 noise + bump + ramps rust (Bazaar 2024) | **0.107** (a rust cloud, no layout) | easy | yes (reconstructed) |
| Metal | M2 mask-driven wear: Pointiness, AO, Bevel + noise | est. good for edges on a 3D model; no layout | medium | partly (Bevel mask only) |
| Metal | M3 real straps and rivets (Geometry Nodes) + Bevel mask | mask pictures only (no colour score); true bevelled edges | medium | yes (my build) |
| Metal | **M4 layout by numbers (mine)** | **0.286**: straps, braces, rivets, scratches right; rust too sparse | medium-hard | yes |
| Mud | D1 Voronoi Distance-to-Edge dirt + puddle roughness (Bazaar 2024) | **0.080** (cracked-earth cells, no ruts) | easy | yes (reconstructed) |
| Mud | D2 puddle block (wet rim, flat water bed) | est. good for the water part | medium | tested in the shader-toolbox guide |
| Mud | D3 Dynamic Paint wheel ruts | not obtained (0.0009 displacement) | medium-hard | partly |
| Mud | D4 curves / Geometry Nodes ruts / particles | est. good ruts; sibling recipe exists | hard | NOT TESTED here |
| Mud | **D5 bent rut coordinate + puddles + polygon stones (mine)** | **0.353** (0.41 to 0.43 at 384 px): ruts, puddles, stones read right; too regular | medium-hard | yes |
| Gravel | G1 shader rock from Voronoi + ramps (Bazaar 2024, video) | unknown; my Voronoi-cell stones gave daggers | easy | NOT TESTED (video unreadable) |
| Gravel | G2 Geometry Nodes Poisson scatter of stones | **0.038 to 0.055** as raw flat photographs (22 to 30 percent coverage); needs the colour layers | medium | yes |
| Gravel | G3 rigid-body drop | **0.058** raw (42 percent coverage); does not tile | medium | yes |
| Gravel | **G4 polygon per grid cell in the shader (mine)** | **0.223** (0.29 to 0.32 at 384 px): reads as your gravel; stones too big and glossy | medium-hard | yes |

**Advice for the builders (from the table):** start every surface from the layout idea in section 5 to 10 (not from the stock chain); copy my `layers_*.png` order (layout, colour per piece, flat patches, edges and outlines, dirt, stains); use `builder.py`, `stone_tools.polygon_stones` and the half-tile shift test; bake at 1254 for the final scores; and when you add real geometry (rivets, slate slabs, stones), pass every instanced part through a Set Material node.

---

## 13. Recipe cards (short; every number was run)

1. **Stretched seamless streaks:** `tnoise(4, 220, detail 4, roughness 0.6)` -> Map Range 0.57..0.59 (light) and 0.43..0.41 (dark) -> Mix 0.5 / 0.55. (wood grain)
2. **Ruts along a bending diagonal:** `s = u + v + 0.55 (tnoise(2,2) - 0.5) + 0.045 sin(2 pi (2u - v) + 1)`; `c = |fract(4 s) - 0.5|`; groove = Map Range(c, 0.035, 0.05) inverted; bank = Map Range(c, 0.05, 0.05) x (1 - Map Range(c, 0.09, 0.14)). (mud)
3. **Streaks along the ruts:** `tnoise(34, 5, coords = (s, v))` (coordinates must add whole numbers when u or v grows by 1).
4. **Brick layout that tiles:** columns 4 (whole), rows 12 (even); row = floor(v x 12); `u x 4 + 0.5 x (row mod 2)` -> Floor = column, Fraction = fx; wrap both with Floored Modulo.
5. **One random number per brick:** White Noise (3D) of (column, row, seed) -> Constant ramp of 5 reds; a second one x 50 into the W of a 4D Noise on `(fx x 3, fy, 0)` for patches that differ per brick.
6. **Dark outline + ragged edge:** distance to the nearest side in tile units = min(side distance / 4, top distance / 12) + 0.013 x (`tnoise(70,70)` - 0.5); brick = window 0.0001 at gap / 2 (0.00925); outline = 1 - window at gap / 2 + 0.0045.
7. **Slate rows that do not line up:** row count 8 (+0.5 row shift); per row: slate count 6..8, slide, `+ 0.40/(2 pi 3) sin(2 pi 3 u + phase) + 0.20/(2 pi 7) sin(2 pi 7 u + phase)`; gap under 0.009, beside 0.0065, rim 0.014 (tile units).
8. **Splinter strips:** `tvoronoi(3, 30, randomness 0.85)` F1 Color red -> Constant ramp of 6 browns; the same Voronoi with Distance to Edge < 0.008 + 0.04 x gate -> crack.
9. **Boards of different heights:** `v + 0.40/(4 pi) sin(4 pi v + 1.3) + 0.16/(10 pi) sin(10 pi v + 0.4)`, x 6, Floor = board (mod 6), gap = first 0.0048 of each board.
10. **Bands (straps) as signed distances:** vertical `|u - c| - w`; horizontal that wraps `|fract(v - c + 0.5) - 0.5| - w`; brace = perpendicular distance to a slanted line, ends cut by the along-the-line distance; inside = Map Range at 0; outline when the inside distance < 0.0035; light line to 0.0075.
11. **Rivet rows:** `du = (fract((u - phase) / 0.125 + 0.5) - 0.5) x 0.125`, `dv = wrapped (v - v0)`; radius 0.017; dome = ramp of the distance, lit from the top-left; ring at 0.78 to 0.80 of the radius.
12. **Rust that likes edges:** `tnoise(6,6, distortion 0.5)` + 0.06 x (1 - Map Range(distance to nearest strap edge, 0, 0.05)) -> Map Range 0.60..0.615 -> four flat rust steps.
13. **Random polygon stones:** `polygon_stones(b, cells, seed, presence, radius_low, radius_high, sides)`: gravel 72 / 30 / 15 / 8 cells; mud 12 / 24 / 52 cells; sides 4 for blocks, 5 or 6 for chunky stones.
14. **Flat painted patches from one noise:** Noise -> Map Range 0.45..0.47 (hard) -> Color Ramp Constant (3 to 5 colours); or Map Range interpolation Stepped with Steps N (N + 1 flat levels).
15. **Height from colour:** Gamma 0.4545 -> RGB to BW -> Map Range (about 0.05..0.5 -> 0..1); correlation with your height maps 0.94 to 0.985.
16. **Per-instance colour in Geometry Nodes:** pass the instanced mesh through **Set Material**, read **Object Info > Random** (unique per instance, tested 196 of 196) through a Constant ramp.
17. **Seam proof:** `periodicity_test.sh recipe.py name 128` (shifted by half = rolled by half).

---

---

## 14. Files (all under `experiments_how_people_make_each_surface/`)

- `recipes/recipe_brick.py`, `recipe_slate.py`, `recipe_wood.py`, `recipe_metal.py`, `recipe_mud.py`, `recipe_gravel.py` - the six recipes (plain note at the top of each); `recipes/six_surface_recipes.blend` - the six node groups plus six demo planes with materials; `recipes/approach_*.py` - the rebuilt stock tutorial chains; `recipes/test_*.py` - small tests.
- `builder.py` (write recipes as sums, seamless stretched noise and cells, layout helpers), `stone_tools.py` (polygon stones; the Voronoi-cell version is kept for comparison), `geo_helpers.py` and the geometry tests `geo_gravel_scatter.py`, `geo_instance_random_test.py`, `geo_slate_rows.py`, `geo_rivets_bevel.py`, `geo_physics_gravel.py`, `geo_dynamic_paint_ruts.py`.
- `bake_and_score.sh`, `periodicity_test.sh`, `seed_spread.sh`, `make_stage_strips.sh`, `make_comparison.py`, `check_seams.py`, `score_geometry_pictures.py`, `count_nodes.py`, `sweep_posterize.py`, `sweep_stone_settings.py`, `save_recipes_blend.py`, `probe_geometry_sockets.py` (socket names of the Geometry Nodes nodes in 5.2.2).
- `pictures/` - overview and comparisons (`overview_all_six.png`, `compare_*.png`), layer strips (`layers_*.png`), stock chains (`stock_chains_vs_reference.png`), geometry tests, sweeps, first tries, score sheets.
- `out/` - raw bakes, scores (`score.json`), seed spread, facts of every geometry test.

---

## 15. Tested here: what I ran and what happened (failures included)

All in Blender 5.2.2 on this machine, command line, CPU Cycles, `-t 2`, CPU shared with other helpers. Bake times at 512 px: brick 12 to 15 s, slate 11 s, metal 22 to 24 s, mud 31 to 35 s, gravel 34 to 37 s, wood 36 to 43 s (a first mud with Voronoi stones took 77 s).

1. **Six recipes, scored and compared by eye** (`recipes/recipe_*.py`, scripts `bake_and_score.sh`, `make_comparison.py`; pictures `compare_*.png`, `overview_all_six.png`, `final_*_score_sheet.png`). Overall scores at 512 px: brick 0.327, slate 0.503, wood 0.325, metal 0.286, mud 0.353, gravel 0.223.
2. **Iterations that failed or only partly worked** (kept as part of the guide): brick 0.366 -> 0.354 -> 0.338 -> 0.327 while the picture got better by eye (soot and mortar changes; the scorer is not monotonic with looks); wood first version 0.082 (clean planks), 0.156, then 0.308 and 0.325 with splinter strips; metal first version drowned in rust (0.100); mud first version with Voronoi stones 0.204, polygon stones with huge stones 0.167, then 0.24 and 0.41 (final 0.353); slate first bake seam 13.9 until the half-row shift.
3. **Stock tutorial chains rebuilt** (`recipes/approach_*.py`): 0.065, 0.183, 0.048, 0.080, 0.107. They are my reconstructions of incomplete step lists, with my guesses for ramp stops.
4. **Seamlessness:** half-tile shift test on all six recipes (section 3.2); exact coordinates at the edges; Voronoi features on the donut. The scorer's seam number false-alarmed twice (slate, wood). I chased a dark top row in the wood bake for a while: it was real crack pixels, not a bake artifact.
5. **Seed and size spread** (section 3.3).
6. **Geometry routes:** Poisson-disk scatter (three variants, facts in section 10), per-instance random values (three methods), slate rows from instances, rivets with a Bevel edge mask, rigid-body drop of 160 stones, Dynamic Paint ruts (setup works, depth not tuned). **Failures:** the first scatter and instance-random runs rendered every instance black (no Set Material); my first count of distinct random values read an 8-bit copy and gave a false 256; counting with 16-bit pictures gave 196 of 196; Dynamic Paint did nothing until `ui_type` was set to BRUSH; the first slate slabs were cubes of size 1 (too wide, a missing division by the column count).
7. **Posterize and flat-patch tricks** (section 11); **faces per stone and stone share sweeps** (section 10); **layer-by-layer strips** (`make_stage_strips.sh`).
8. **Facts about the references** (computed on the reference pictures): height versus colour brightness correlation (screen brightness 0.938, 0.985, 0.954, 0.938, 0.969, 0.978 for brick, slate, wood, metal, mud, gravel; linear luminance 0.907, 0.922, 0.896, 0.850, 0.931, 0.924); in mud and gravel, dark blue stones have mean height 0.20 and 0.27, lit blue 0.73 and 0.68, brown soil 0.48 and 0.50.
9. **Reading the web:** WebFetch returned only summaries, and many pages are paid products, videos or listings, so most node chains could not be checked; one Poliigon page returned 404; two BlenderNation pages (Sanctus, Erin) have no node text; the Bazaar rocky-ground and plank listings only link to videos.
10. **Blender's own manual and Python reference** were searched through the Blender tool server (Brick Texture, Distribute Points on Faces, Instance on Points, Bevel node, Dynamic Paint, Rigid Body, Object Info, Attribute node, Voronoi). The search for "Dynamic Paint" and "rigid body displacement" found the manual pages but nothing about wheel ruts; the manual describes Dynamic Paint only as creating colour attributes, image sequences or displacement.

---

## 16. NOT TESTED (said plainly)

- All node chains of paid products and videos: Brickmaker, Rs Procedural Wood, Timber, Blender Insight floor, the 3D Tudor and Roof Tiles Generator add-ons, BoltGen, Scatter Rocks add-ons, the Blender Guru and Luca Rood courses, lassyla's EEVEE shader, the Sanctus and Erin videos, Dikko's Dynamic Paint tutorial, the O'Reilly mud chapter and the GameDev.tv mud course.
- "Two Brick nodes for chipped corners" (B3), the 2020 roof tile shader (S4), the maths knots (W3), Voronoi rust patches and the Blender Buzz Pointiness chain as shaders (M2: only my Bevel mask was run), Geometry Nodes bricks (B5), curve ruts (D4; a sibling helper made one, I did not run it), particle tyre tracks.
- Everything EEVEE: Pointiness in Eevee, Shader to RGB toon shaders, EEVEE-only tricks (no graphics card here).
- Moss, efflorescence, wet leaks and spalling as separate effects on brick; edge wear from AO or Pointiness on a real wall; a real height map with low mortar.
- Baking my recipes at 1254 px with all maps and reading the final scores there (I used 512 px and 384 px; the final builders should bake at 1254).
- Dynamic Paint beyond "it runs and gives 0.0009"; rigid-body gravel made seamless; Geometry Nodes scatter made seamless with relaxation.
- Tiling of the geometry-route photographs (they do not repeat; only the ghost-copy variant repeats by construction).
- Whether the sine-squeeze slate or the donut Voronoi behave the same in Blender 4.x (version differences are NOT TESTED; Voronoi changed its hash in 5.0 per the shader-toolbox guide).

---

## 17. Sources (what I actually used; date = the date the page shows)

Read through WebFetch (the pages' content, as far as the tool summarised it):
1. **How to make a procedural bricks material**, JSAbbott, Blender Bazaar, 21 Jan 2024. https://bazaar.blendernation.com/listing/how-to-make-a-procedural-bricks-material/ - the stock Brick node chain, colours, noise scale 300, normal map 0.15, Voronoi paint.
2. **Making a procedural rusted metal material**, JSAbbott, Blender Bazaar, 24 Feb 2024. https://bazaar.blendernation.com/listing/making-a-procedural-rusted-metal-material/ - noise + bump + ramps rust chain.
3. **Making a procedural dirt/water puddles material**, JSAbbott, Blender Bazaar, 4 Mar 2024. https://bazaar.blendernation.com/listing/making-a-procedural-dirt-water-puddles-material/ - Voronoi Distance to Edge dirt and puddle mask chain.
4. **Procedural rocky ground material**, Ryan King Art, Blender Bazaar, 25 Jan 2024. https://bazaar.blendernation.com/listing/procedural-rocky-ground-material/ - metadata only (steps in a video).
5. **Procedural wood plank material**, Ryan King Art, Blender Bazaar, 25 Mar 2024. https://bazaar.blendernation.com/listing/procedural-wood-plank-material/ - metadata only; settings of its node group (scale, colour, variation, detail, roughness, bump).
6. **Make a Procedural Dirt Texture (+Puddles) in Blender 2.9**, Jennifer Abbott, BlenderNation, 24 Dec 2020. https://www.blendernation.com/2020/12/24/make-a-procedural-dirt-texture-puddles-in-blender-2-9/ - node list with time stamps only.
7. **procedural edge wear blender**, StraySpark, 29 May 2026. https://www.strayspark.studio/learn/tutorials/procedural-edge-wear-blender - Pointiness / curvature edge wear, Mix Shader, noise multiply (no numbers; promotional).
8. **procedural weathering blender geometry nodes**, StraySpark, 12 Apr 2026. https://www.strayspark.studio/blog/procedural-weathering-blender-geometry-nodes - Geometry Nodes edge wear, gravity dirt, Voronoi rust (I list the errors I spotted in section 8).
9. **Procedural brick shader**, jancyclops and others, Blender Artists, Jun 2016 to May 2017. https://blenderartists.org/t/procedural-brick-shader/670049 - per-brick random colour, bump variation, no mortar.
10. **Wooden floor with Brick shader**, Blender Artists, 19-21 Aug 2023. https://blenderartists.org/t/wooden-floor-with-brick-shader/1478773 - threshold mask / Constant ramp for per-brick choice.
11. **How to procedural texture with stones tiles**, Blender Artists, 14-15 Jan 2022. https://blenderartists.org/t/how-to-procedural-texture-with-stones-tiles/1354265 - two-brick method for chipped edges.
12. **Procedural rust streaks**, Blender Artists, 2019 (plus a 2025 request). https://blenderartists.org/t/procedural-rust-streaks/1152774 - Voronoi spots, noise into Z, slope, drips by directional blur.
13. **Fully procedural roof tile shader**, _jb4x, Blender Artists, 7-8 May 2020. https://blenderartists.org/t/fully-procedural-roof-tile-shader/1226380 - controls and outputs of a roof tile shader (file only).
14. **Realistic roof tiles texture**, DNorman, Blender Artists, 31 May - 1 Jun 2021. https://blenderartists.org/t/realistic-roof-tiles-texture/1306785 - instance a tile, location into White Noise for colour.
15. **Roof Tiles Generator**, freckleone (NodeCrafted), Blender Artists, 2 Jun - 6 Dec 2024. https://blenderartists.org/t/roof-tiles-generator/1532809 - Geometry Nodes roof tiles add-on; user requests (column offset, randomness).
16. **Semi-Pro Procedural Wood Texture**, ChengHan, Blender Artists, 4-9 Aug 2024. https://blenderartists.org/t/semi-pro-procedural-wood-texture/1542209 - maths rings, knot parameters, shading advice.
17. **Believable procedural wood in Cycles**, Quantum_Anomaly, Blender Artists, 19-20 Jun 2014. https://blenderartists.org/t/believable-procedural-wood-in-cycles/613323 - per-board variation by a second coordinate branch.
18. **Procedural Wood Material**, Ssendam (Lance Phan), Blender Artists, 1 Mar 2026. https://blenderartists.org/t/procedural-wood-material/1632590 - 3D volume wood, floor cutters.
19. **Timber**, Erindale Woodford (Gemn), Blender Artists, 7 Aug 2019. https://blenderartists.org/t/timber-a-realistic-procedural-pbr-wood-material-download-links-included/1173404 - feature list of a node-built wood; Eevee node limit.
20. **Rs Procedural Wood** docs, Rebellious Studios, Superhive (Blender 4.5 to 5.1; page undated). https://superhivemarket.com/products/rs-procedural-wood/docs - layer list of an all-in-one wood group.
21. **Brickmaker** docs, Superhive (Blender 4.0 to 4.2; page undated). https://superhivemarket.com/products/brickmaker/docs - four-group brick pipeline.
22. **Quick tip: rigid bodies**, polygoniq, 1 Nov 2023. https://polygoniq.com/blog/2023-11-quicktip-rigid-bodies/ - drop objects with rigid bodies, bake.
23. **Tutorial: procedural Blender shader with hand painted look**, 80 Level, 18 Aug 2026. https://80.lv/articles/tutorial-procedural-blender-shader-with-hand-painted-look - lassyla's noise-driven EEVEE shader (no node details).
24. **How to Create a Hand Painted Look in Blender**, Martin Klekner, BlenderNation, 26 Oct 2025. https://www.blendernation.com/2025/10/26/how-to-create-a-hand-painted-look-in-blender/ - Shader to RGB + Color Ramp, Grease Pencil outlines (introduction only).
25. **How to make procedural rust and blisters**, Sanctus, BlenderNation, 24 Apr 2021. https://www.blendernation.com/2021/04/24/how-to-make-procedural-rust-and-blisters/ - video; no node text.
26. **Procedural weathering and wear with Blender 2.83**, Erin, BlenderNation, 13 Oct 2020. https://www.blendernation.com/2020/10/13/procedural-weathering-and-wear-with-blender-2-83/ - video; no node text.
27. **Creating Tire Tracks with Particles in Blender 2.92**, luwizart, BlenderNation, 2 Jan 2021. https://www.blendernation.com/2021/01/02/creating-tire-tracks-with-particles-in-blender-2-92/ - no steps on the page.
28. **How to Texture in Blender - Full Course**, Blender Guru (post dated "Jul 27", year not shown). https://www.blenderguru.com/posts/how-to-texture-in-blender-full-course - topic list of the grungy brick wall (Color Burn technique, wet leaks, efflorescence, spalling), no node details.
29. **Blender 5.2 manual and Python reference bundled with the Blender tool server** (read with search_manual_docs / get_python_api_docs): Brick Texture, Voronoi, Distribute Points on Faces, Instance on Points, Bevel, Object Info, Attribute, Dynamic Paint, Rigid Body pages. No web date; matches the 5.2.2 build.

Seen only as search-result summaries or listings (I did not open the page; dates mostly not shown): Superhive "Geometry Nodes Scatter Rocks - Blender 3.6+" https://superhivemarket.com/products/geometry-nodes-scatter-rocks---blender-3 ; Geon Scatter Rocks https://sebastiengarnier.gumroad.com/l/geonscatterrocks ; Blender Insight "Procedural Wooden Floor" https://blendermarket.com/products/procedural-wooden-floor/docs ; Kyra3D "Wood Procedural Shader" https://blendermarket.com/products/wood-procedural-shader-cycles--eevee ; BoltGen https://superhivemarket.com/products/geometry-nodes-rivetbolt-generator ; 3D Tudor roof tile https://www.cubebrush.co/3d_tudor/products/ov0eya/3dt-roof-tile-blender-geometry-nodes-procedural ; Ryan King Art brick wall https://ryankingart.gumroad.com/l/brick-wall ; Packt cookbook slate recipe https://hub.packtpub.com/?p=6101 ; CG Cookie "Dynamic Paint over a large area" https://cgcookie.com/community/22244-dynamic-paint-over-a-large-area ; Lester Banks Dynamic Paint wet tyre track https://lesterbanks.com/tag/blender-dynamic-paint-waves-tutorial/ ; Blend Swap 19340 https://blendswap.com/blend/19340 ; OpenGameArt "Tileable Rock Scattering" https://opengameart.org/node/147130 ; MODDB "baking normal and ambient occlusion maps in blender" https://www.moddb.com/tutorials/baking-normal-and-ambient-occlusion-maps-in-blender ; Blender 2.92 Geometry Nodes release notes https://developer.blender.org/docs/release_notes/2.92/geometry_nodes/ ; Skillshare Harry Helps https://www.skillshare.com/en/classes/Blender-3D-Create-a-Procedural-Hand-Drawn-Texture-and-Reveal-Animation/1447452824 ; O'Reilly "3D Environment Design" mud chapter https://www.oreilly.com/library/view/3d-environment-design/9781803235851/B18697_08.xhtml ; Luca Rood "Procedural Texturing" https://blendermarket.com/products/procedural-texturing-blender ; Poliigon plank generator guide https://help.poliigon.com/en/articles/4993171-using-the-wood-plank-generator-to-create-flooring-in-blender (404 when opened).

The sibling guides in this folder (`02 Research - the shader node toolbox.md`, `02 Research - seamless tiles and baking.md`) are cited where I rely on their tested facts.
