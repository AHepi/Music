# 02 Research - the shader node toolbox (Blender 5.2)

What this is: a plain-language tour of every node Blender 5.2.2 gives us for making textures, grouped by what each is FOR, with what each setting
does to the picture. Everything marked TESTED was run in Blender 5.2.2 on this machine (CPU Cycles). Anything marked NOT TESTED is a
claim from the manual or a web page that I did not run. Small pictures made for this guide are in `experiments_shader_node_toolbox/pictures/`
(links below). The scripts that made them, and the raw numbers, are in `experiments_shader_node_toolbox/`.

How to read the labels
- **TESTED** = I ran it and looked at the picture or the numbers.
- **NOT TESTED** = only read, not run.
- **WEB ONLY** = a web page says it; I did not check it (or could not).
- "Tile" = the flat 1 x 1 square we bake; "u" and "v" = how far across and up the tile you are, from 0 to 1.
- "Value" = one grey number per point. "Colour" = three numbers per point.

---

## 1. The short version (read this first)

A procedural texture is a chain. Seven steps cover almost everything we need:

1. **Where am I?** Coordinates (u, v of the tile). Optionally bend or stretch them (Mapping, Vector Math, a noise added to them).
2. **Make a pattern.** A pattern maker turns coordinates into one grey value (or a random colour): Noise, Voronoi, Brick, Wave...
3. **Shape the value.** Shapers change the grey value: Map Range or Color Ramp for contrast and hard edges, Math for thresholds, Float Curve for smooth curves.
4. **Combine.** Mix (with a blend mode) or Math add/multiply to stack patterns: big blotches, small grain, cracks.
5. **Turn values into the maps we need:** a Colour (Color Ramp, Mix), a Height (grey 0..1), a Roughness, a Metallic.
6. **Surface effects:** Bump / Normal Map / Displacement make light see the height; Bevel, Ambient Occlusion and Pointiness find edges and crevices (only in real 3D).
7. **Shader:** the Principled BSDF takes colour, roughness, metallic, coat and so on and makes the final look.

The twelve facts that would have saved me the most time (each one is proved further down):

1. **Blender's random-looking patterns never tile.** Noise, Voronoi, Gabor and Magic are not the same after moving one whole tile, not even with "nice" whole-number Scale. A shop page that says they wrap at whole-number UV values is wrong. (TESTED, section 2.)
2. **Only two things tile by themselves:** the Checker, and the Brick node's mortar layout when the numbers come out whole (for example Scale 2, Brick Width 0.5, Row Height 0.25 = exactly 4 x 8 bricks). The Brick node's per-brick random COLOUR does not tile. (TESTED.)
3. **Noise sits in the middle.** Default noise only spans about 0.25..0.73. You must stretch it (Map Range From 0.3..0.7 to 0..1) before it makes contrast. More Detail makes it flatter still. (TESTED.)
4. **Normalize only affects fBM noise.** Multifractal, Ridged, Hybrid and Hetero are not limited to 0..1 at all. Ridged/Hybrid/Hetero ignore Detail until you raise Offset above 0. (TESTED.)
5. **Typing a vector into an unconnected Vector socket does nothing.** Unconnected = the object's "Generated" coordinates. Feed a real vector in. (TESTED.)
6. **The Bump node's default Distance is now 0.001 (1 mm)** - old tutorials that say "Strength 0.3" assumed a much larger default, so the same chain looks nearly flat today. (TESTED, plus release notes.)
7. **For a hard-edged height (bricks, tiles) the Bump node shows nothing at its default Filter Width 0.1.** Use Filter Width 1 to 4 to get an edge. (TESTED.)
8. **A Normal Map in OpenGL convention matches the Bump node's shading of the same height; DirectX does not.** (TESTED: 0.85 against -0.02.)
9. **Voronoi changed its pattern in Blender 5.0** (new, faster hash). A texture built in 4.5 will not look the same in 5.x. (WEB ONLY: release notes + forum; I cannot compare with an old Blender.)
10. **Python quirks:** looking a socket up by name fails when the current settings switch it off (Noise W in 3D, Mapping Location in Vector type, Voronoi Detail in N-Sphere mode). Mix-node sockets are found by the name `A` / `B` / `Result`, not by `A_Color`. (TESTED.)
11. **Shader to RGB (the toon / "painted shader" trick) gives plain white in Cycles.** It works only in EEVEE, which we cannot run here. (TESTED in Cycles.)
12. **Toolbox-only first attempts get the layout of brick, slate and wood recognisably right but miss the chunky hand-painted patches;** the real work is in hard-edged colour patches, stains that follow the layout, and height made from colour brightness. (TESTED, section 9.)

---

## 2. Claims checked: what is true, what is wrong

| Claim (where I saw it) | Verdict | Evidence |
|---|---|---|
| "Procedural nodes wrap seamlessly at whole-number UV values" (a shop page) | **FALSE** for Noise, Voronoi, Gabor, Magic, Wave, Gradient. **TRUE only** for Checker and the Brick mortar layout (when brick counts are whole). | Draw the pattern at (u, v) and at (u+1, v): the pictures differ by 0.07-0.22 on average for Noise/Voronoi/Gabor/Magic (picture spread 0.07-0.21), by 0.00 for Checker Scale 8 and for Brick mortar 4 x 8, and by 0.15 for Brick colour. TESTED (`which_patterns_wrap.json`). |
| "Noise at whole-number positions reads exactly 0.5" (Blender manual note) | **TRUE** | Scale 1, Detail 0: value 0.500 at (0,0,0), (1,2,3), (2,5,1), (-4,3,8); 0.746 at (1.5,2.5,3.5). Detail 2 also gives 0.500. TESTED. |
| "Detail 2.5 is a 50% blend of 2 and 3 octaves" (manual) | **TRUE, exactly** | Largest difference between Detail 2.5 and the average of Detail 2 and Detail 3: 0.0. TESTED. |
| "Normalize keeps noise in 0..1" (Geometry Nodes manual page) | **Only half true in the shader editor** | Normalize changes fBM only. Multifractal stays 0.2..2.0 (middle 1.0); Ridged 0..0.58; Hybrid/Hetero about -0.76..0.7 with the default Offset 0. Even normalized fBM only spans about 0.25..0.73. TESTED in the shader editor; Geometry Nodes version NOT TESTED. |
| "Unconnected Vector input = Generated coordinates" (manual) | **TRUE; and the typed value is ignored** | Typed (0.31, 0.77, 7.3) vs (0.31, 0.77, 0.1): identical picture; unconnected noise varies across the plane (std 0.089). TESTED. |
| Manual's Wave page lists profiles Sine and Saw | **Out of date:** a third, **Triangle (TRI)** exists in 5.2.2 | Drawn and looks like a triangle wave. TESTED; also listed in the Python reference. |
| Old tutorials: "Bump Strength 0.3" gives a nice rough look | **Outdated since 4.5** | Default Distance is now 0.001. With Distance 0.001 the noise bump is almost invisible; 0.03 shows a clear surface. TESTED. |
| "The Bump node makes bevel-like edges on stepped heights" (manual) | **TRUE but only with a larger Filter Width** | Brick mortar as height: Filter Width 0.1 shows nothing; 1, 2, 4 show growing edges. TESTED. |
| "The Bump node and a Normal Map are two routes to the same shading" | **TRUE if the Normal Map is OpenGL convention** | Correlation of the two renders: OpenGL 0.85, DirectX -0.02. TESTED. |
| "Shader to RGB makes toon / painterly shaders" (EEVEE tutorials, Superhive shader) | **EEVEE only** | In Cycles the output was pure white (1, 1, 1). TESTED. |
| "Pointiness finds edges" (many tutorials) | **True but depends on mesh density, and only works on real geometry** | On a bevelled cube, more simple subdivision turns bright faces mid-grey with thinner bright edge bands. TESTED; Pointiness is Cycles only per the manual (not tested in EEVEE). |
| "True displacement needs a finely subdivided mesh" (manual) | **TRUE** | Edge-on view of a plane: Bump Only = no silhouette; Displacement Only and Displacement and Bump = ragged band (needs 8 levels of simple subdivision here). TESTED. |
| `material.use_nodes = True` (every old script) | **Deprecated:** prints "'Material.use_nodes' is expected to be removed in Blender 6.0"; new materials already have a node tree | TESTED. |
| Float Curve "keeps values between 0 and 1" | **No: by default it extrapolates** | Python-made Float Curve: value at -0.5 came out -2.99. Set `mapping.extend = 'HORIZONTAL'` to clamp (then -0.5 gives 0, 1.5 gives 1). TESTED. |
| "Voronoi Normalize stretches to 0..1" | **No: it scales so the possible maximum is 1** | F1 normalized spans 0.03..0.58, F2 0.09..0.31 (un-normalized F1 0.05..1.0). Distance to Edge and N-Sphere Radius ignore it. TESTED. |

---

## 3. What changed between Blender 3.x and 5.x

| Version (release) | Change that matters for textures | Source / status |
|---|---|---|
| 3.4 (late 2022) | New **Mix** node (float, vector, colour, later rotation) replaces Mix RGB. Mix RGB still exists, shown as **Mix (Legacy)**. | 3.4 release notes (via search summary); Mix (Legacy) exists in 5.2.2: TESTED |
| 4.0 (Nov 2023) | **Principled BSDF rewritten** (Coat above emission with Tint and IOR, Sheen as microfibre on top, Specular IOR Level + Specular Tint, subsurface uses Base Color, Multiple-scattering GGX default). Glossy and Anisotropic BSDF merged. Velvet became **Sheen BSDF**. Normal Map strength fixed above 1. **Noise** got Normalize and Lacunarity. **Voronoi** got fractal Detail, Roughness, Lacunarity and Normalize. | Blender 4.0 shading release notes. Inputs seen in 5.2.2: TESTED |
| 4.1 (2024) | **Musgrave Texture merged into Noise Texture.** `Roughness = Lacunarity^(-Dimension)`; **Detail = old Detail - 1**. Musgrave modes gained Distortion and a Color output. Old files convert with identical renders. | Blender 4.1 rendering release notes. Conversion formula NOT TESTED (no old Blender here). |
| 4.3 (Nov 2024) | **Gabor Noise Texture** (oriented bands). **Metallic BSDF** node. | Blender 4.3 release notes. Gabor TESTED; Metallic BSDF NOT TESTED. |
| 4.5 (2025) | **Default Bump Distance lowered to 1 mm and Displacement Scale to 1 cm.** | Blender 4.5 release notes. Defaults in 5.2.2: Bump Distance 0.001, Displacement Scale 0.01. TESTED. |
| 5.0 (Nov 2025) | **Radial Tiling** node. **Voronoi uses a new hash: faster, but the pattern is different from before.** Shader nodes get **Repeat zones, Closures, Bundles, Menu Switch**. Point Density texture removed. "Use Nodes" removed (materials always have nodes). | Blender 5.0 rendering release notes; forum thread Sept 2026. Radial Tiling TESTED; repeat zones etc. NOT TESTED. |
| 5.1 (about early 2026) | **Raycast** shader node. **Normal Map Convention** option (OpenGL / DirectX). Join Bundle node. Vector Math rounding option. | Blender 5.1 rendering release notes. Normal Map convention TESTED; Raycast NOT TESTED. |
| 5.2 LTS (14 July 2026) | **Time** node in shaders. Principled **Thin Wall** input. Subsurface Random Walk radius re-scaled (old files become "Random Walk (Legacy)"). | Blender 5.2 rendering release notes. Thin Wall input exists: TESTED (listed); effect NOT TESTED. |
| unknown version | Wave Texture has a **Triangle** profile; Principled has a **Diffuse Roughness** input; Voronoi has a W output. | Present in 5.2.2: TESTED. Version they appeared: not checked. |

Note about the bundled manual: the manual that ships with the Blender tool server has pages for nodes the 5.2.2 shader editor does **not** have (for example Combine/Separate Cylindrical and Spherical, Mix Vector as its own node). It was written for a newer build. Always check a node exists (`list_addable_nodes.py` writes the exact list: `addable_nodes.txt`).

---

## 4. Talking to nodes from Python (pitfalls, all TESTED)

- **Name lookups skip switched-off sockets.** `node.inputs['W']` raises KeyError when Noise is 2D or 3D. Same for `Mapping.inputs['Location']` when Type is Vector or Normal, and `Voronoi.inputs['Detail']` when Feature is N-Sphere Radius. Use the position (`inputs[1]`) or loop over `node.inputs` and test `socket.enabled`.
- **Mix node:** set `data_type` first. Then `inputs['A']`, `inputs['B']`, `inputs['Factor']` and the output `'Result'` find the colour sockets. `inputs['A_Color']` (the identifier) is NOT accepted as a key. Positions in RGBA mode: Factor 0, A 6, B 7, result output 2.
- **Map Range:** float sockets are positions 0 to 5 (Value, From Min, From Max, To Min, To Max, Steps); vector versions come later. Set `interpolation_type` and `clamp` as settings.
- **Math / Vector Math:** the second and third inputs are `inputs[1]`, `inputs[2]`; many operations leave the third switched off.
- **Color Ramp:** `node.color_ramp.elements[0].position / .color`; add stops with `elements.new(position)`; `interpolation` is one of EASE, CARDINAL, LINEAR, B_SPLINE, CONSTANT; `color_mode` RGB, HSV, HSL; `hue_interpolation` NEAR, FAR, CW, CCW.
- **Float Curve / RGB Curves:** `node.mapping.curves[0].points.new(x, y)` then `node.mapping.update()`. Default `extend` is EXTRAPOLATED (see the table above).
- **`material.use_nodes = True`** still works but warns (removed in 6.0). New materials already have `node_tree`.
- **Colours typed in Python are linear.** A linear 0.214 becomes screen value 127.5 of 255 in a saved picture (0.05 gives 63, 0.5 gives 188, 1.0 gives 255). TESTED. A hex colour from a colour picker is a screen value: convert it before typing it in.
- **Dynamic sockets are the rule, not the exception:** Noise Offset and Gain exist only for Ridged, Hybrid (both) and Hetero (Offset only). Voronoi Smoothness exists only for Smooth F1, Exponent only for Minkowski. TESTED by listing which sockets are enabled.

---

## 5. Group A - the pattern makers

Each one: one sentence, then the settings, then which of our six surfaces it helps (brick, slate, wood, rusted metal, mud with puddles, gravel).

### 5.1 Coordinates (not patterns, but every pattern needs them)

- **Texture Coordinate** gives the position in different systems: Generated (0..1 across the object), UV, Object, Camera... On our flat 1 x 1 baking plane, UV and Generated are the same. An unconnected Vector input quietly uses Generated. TESTED (unconnected input varies across the plane).
- **Mapping** moves, turns and scales coordinates before a pattern sees them. See 6.9 (type table, TESTED).
- **Attribute** reads a value stored on geometry (for example one made in Geometry Nodes, section 9). TESTED in Geometry Nodes (picture g02).

### 5.2 Noise Texture - smooth, cloudy randomness (the workhorse)

**What it does:** gives a smooth random grey value for every point, built from layers (octaves) that get finer and finer.
**Example first:** Scale 5, Detail 6, Roughness 0.55, then Map Range From 0.3..0.7 to 0..1 = a cloudy mask with real contrast. Set Map Range From to 0.45..0.55 and the clouds become hard-edged blotches (picture: [s02b_map_range_window](experiments_shader_node_toolbox/pictures/s02b_map_range_window.png)).

Settings (TESTED unless said):
- **Dimensions 1D / 2D / 3D / 4D.** 1D uses only W. 2D uses Vector X and Y and ignores Z (value 0.4813 at Z = 0.1 and Z = 7.3). 3D uses Vector and ignores W (0.6399 both). 4D uses W as a fourth direction: moving W makes a new, related pattern (0.51 to 0.45), so **W is a free random "seed" and an animation dial**. Picture: [p08_noise_4d_w](experiments_shader_node_toolbox/pictures/p08_noise_4d_w.png). Higher dimensions cost more render time (manual).
- **Type: fBM, Multifractal, Ridged, Hybrid, Hetero Terrain.** (This is the old Musgrave node, merged in 4.1.) fBM: even, cloud-like. Multifractal: multiplies the octaves, so valleys are smooth and peaks rough; values are centred on 1.0 (0.2..2.0). Ridged: sharp ridges like cracks or veins; at Offset 0 its values are only 0..0.58, mostly near 0. Hybrid and Hetero: peaks and plains; with Offset 0 they run about -0.76..0.7. Picture: [p02_noise_types](experiments_shader_node_toolbox/pictures/p02_noise_types.png) (each stretched to full black-white).
- **Normalize** (checkbox): **changes fBM only.** With it on, fBM sits around 0.5 (0.25..0.73 at Detail 2); with it off it spans about -0.9..0.8. The other four types give identical numbers either way.
- **Scale:** how many noise blobs fit across 1.0. Doubling Scale halves the blob size. Picture: [p07_noise_scale](experiments_shader_node_toolbox/pictures/p07_noise_scale.png).
- **Detail:** how many layers. Detail 0 = one smooth layer; each extra layer adds finer grain. Fractions blend exactly (2.5 = half way between 2 and 3). In my 160-pixel pictures, layers beyond about Detail 6 are too small to see (on a 1254-pixel tile a few more would still show). Normalized noise gets **flatter** as Detail rises (standard deviation 0.120 at Detail 0, 0.090 at Detail 1), so re-stretch after changing Detail. Picture: [p03_noise_detail](experiments_shader_node_toolbox/pictures/p03_noise_detail.png).
- **Roughness:** how strong the fine layers are compared with the big one. 0 = only the big smooth blobs (the fine layers vanish). 1 = every layer equally strong = grainy, almost white noise. Picture: [p04_noise_roughness](experiments_shader_node_toolbox/pictures/p04_noise_roughness.png).
- **Lacunarity:** how much finer each layer is than the last (2 = each layer half as big). 1.2 makes the layers nearly the same size: smeared, wobbly shapes. 5 makes very different scales: a speckled look. Picture: [p05_noise_lacunarity](experiments_shader_node_toolbox/pictures/p05_noise_lacunarity.png).
- **Distortion:** bends the coordinates with another noise before sampling. 0.5 gives swirls, 2 to 4 gives marbled, folded streaks (good for rust drips and wood grain when stretched). Picture: [p06_noise_distortion](experiments_shader_node_toolbox/pictures/p06_noise_distortion.png).
- **Offset and Gain** (Ridged, Hybrid, Hetero only): **Offset decides whether Detail does anything.** Ridged at Offset 0: identical numbers at Detail 2 and Detail 8. At Offset 1 the range becomes 0.09..1.8 and the detail appears. Gain 2 shifts the range again (0.17..1.87). Picture: [p02b_noise_ridged_offset](experiments_shader_node_toolbox/pictures/p02b_noise_ridged_offset.png). Remap these types with Map Range; they are not 0..1.

Outputs: **Factor** (the grey value) and **Color** (three different noises). The Color red channel is exactly the Factor (correlation 1.0); green and blue are independent noises (correlations -0.09 and 0.03). So Color gives two more free random values and a free random vector (use it to bend coordinates, see 6.10).

Not seamless (section 2). Not random at whole-number positions (the 0.5 rule); on a regular grid use White Noise instead.

Helps: **everything.** Brick: stains and per-brick-ish blotches, mortar grain. Slate: moss and streak patches (stretch with Mapping). Wood: grain streaks and weathering. Metal: rust patches, paint wear. Mud: ground colour, puddle shapes (low parts of a big soft noise), grain. Gravel: soil grain, stone texture.

### 5.3 Voronoi Texture - cells (stones, cracks, tiles, dots)

**What it does:** scatters one random point per cell and tells you how far each pixel is from the nearest point(s). Distance gives bubbles or cell edges; Color gives one random colour per cell.
**Example first:** Feature "Distance to Edge" with Math "Less Than 0.05" = thin dark cracks around random cells ([p15_voronoi_edge](experiments_shader_node_toolbox/pictures/p15_voronoi_edge.png)).

Settings (TESTED):
- **Feature:** F1 (distance to the nearest point: soft bubbles), F2 (second nearest: star-like ridges), Smooth F1 (F1 blended with neighbours), **Distance to Edge** (distance to the border between cells: use for cracks and stone gaps), **N-Sphere Radius** (half the distance from a point to its nearest neighbour: one flat grey value per cell, used as a per-stone size). Picture: [p10_voronoi_features](experiments_shader_node_toolbox/pictures/p10_voronoi_features.png).
- **Outputs:** Distance; **Color** (random per cell; each channel averages about 0.45 and runs 0.01..0.97); **Position** (where the cell point is); **W** (1D/4D); **Radius** (N-Sphere only). Picture: [p10b_voronoi_features_color](experiments_shader_node_toolbox/pictures/p10b_voronoi_features_color.png).
- **Distance Metric:** Euclidean = round cells. **Manhattan** = diamond cells. **Chebychev** = square-ish cells (brick/slate/paving look). **Minkowski + Exponent** = in between (Exponent 1 = Manhattan, 2 = Euclidean, large = Chebychev; 0.5 gives a field of tiny stars and an almost white picture). Picture: [p11_voronoi_metrics](experiments_shader_node_toolbox/pictures/p11_voronoi_metrics.png).
- **Randomness:** 1 = random points, 0 = a perfect grid. Randomness 0 + F1 distance "Less Than r" = a regular row of round dots: **rivets**. Picture: [p12_voronoi_randomness](experiments_shader_node_toolbox/pictures/p12_voronoi_randomness.png).
- **Smoothness** (Smooth F1 only): 0 = hard F1 cells, 1 = blobby merge. Picture: [p13_voronoi_smoothness](experiments_shader_node_toolbox/pictures/p13_voronoi_smoothness.png).
- **Detail / Roughness / Lacunarity** (added in 4.0, not for N-Sphere Radius): layers of smaller cells. In practice Detail above 0 turns the cell field into scattered soft blobs on a mostly-white background (picture [p14_voronoi_detail](experiments_shader_node_toolbox/pictures/p14_voronoi_detail.png)); good for speckle and pebbles, not for "finer cells".
- **Normalize:** F1/F2/Smooth F1 only. It divides by the largest possible distance, so F1 falls from 0.05..1.0 to 0.03..0.58 and F2 to 0.09..0.31. It makes values smaller, not bigger.
- **Dimensions 1D to 4D:** 4D with W 0 versus 0.5 changes the picture (average difference 0.20); 1D uses only W (constant across the picture).
- **Blender 5.0 changed the pattern** (new hash). NOT TESTED against the old look.

Not seamless (section 2); the project library has a seamless version (`tileable_voronoi_group`).

Helps: **gravel** (cells = stones: Distance to Edge for the gaps, Color or Radius for the stone's own shade and size), **mud** (stones in the mud: filter cells by N-Sphere Radius), **wood** (cracks: stretch a Distance-to-Edge Voronoi along the grain with Mapping scale (0.18, 1, 1)), **slate** (Chebychev cells make chunky tiles when the Brick node is too regular), **metal** (rivets: Randomness 0), **brick** (chipped edges: warped Distance to Edge).

### 5.4 Brick Texture - rows of offset rectangles

**What it does:** draws rows of bricks with mortar between them and gives each brick a random mix of two colours. Also usable for planks, tiles, panels and slate.
**Example first (TESTED, matches the brick reference layout):** Scale 1.7, Brick Width 0.5, Row Height 0.14, Offset 0.5 gives 3.4 bricks across and about 12 rows, like the reference tile.

**Layout rule (TESTED by eye on the pictures):** bricks across = Scale / Brick Width; rows = Scale / Row Height. Whole numbers (for example Scale 2, Width 0.5, Height 0.25 = 4 x 8) make the mortar layout repeat exactly; **the random brick colour still does not repeat** (section 2).

Inputs and settings:
- **Color1 / Color2:** the two brick colours. Each brick gets its own mix of them. Setting Color1 black and Color2 white gives a per-brick random grey (32 different grey values were counted on a small picture). **Bias** -1 or +1 uses only one colour, in between favours one. Picture row 3 of [p20_brick_settings](experiments_shader_node_toolbox/pictures/p20_brick_settings.png).
- **Mortar colour, Mortar Size, Mortar Smooth:** Mortar Size is measured in the same units as brick height, so 0.1 on a 0.25-tall brick eats most of it (bricks become dashes). Mortar Smooth 0 = hard edge; 1 = bricks fade into mortar (use a little, about 0.02..0.1, for a soft edge that works with bump). Rows 1 and 2 of picture p20.
- **Offset and Offset Frequency:** Offset 0.5 is the usual half-brick shift; 0 stacks bricks in columns; Offset Frequency 3 offsets only every third row. Row 4 of p20 and [p21_brick_layout](experiments_shader_node_toolbox/pictures/p21_brick_layout.png).
- **Squash and Squash Frequency:** make every Nth row of bricks narrower or wider. Picture p21.
- **Row Height / Brick Width:** shape of one brick.
- **Outputs:** **Color** and **Factor** (1 in the mortar, 0 in the brick; with Mortar Size 0.03 at Scale 2, 33% of the tile is mortar).

What it cannot do: it gives **no brick number and no local coordinates**, so you cannot put a gradient or a light chip along each brick's top edge. Section 8 has a tested home-made brick that does.

Helps: **brick** (the layout), **slate** (Brick Width 0.17, Row Height 0.125, Offset 0.5 gives about 6 x 8 overlapping shingles, black Mortar for the dark outlines), **wood** (planks: Brick Width 1.0, Offset 0), **metal** (panels: Brick Width 0.5, Row Height 0.5, thin dark mortar for seams). The Factor also serves as a mortar-gap height.

### 5.5 Checker Texture
**What it does:** two colours in a checkerboard. Scale = number of checks across. TESTED: Scale 8 repeats exactly after one tile. Helps little with our six surfaces; useful as a layout test and for alternating panels. Picture: [p34_checker](experiments_shader_node_toolbox/pictures/p34_checker.png).

### 5.6 Gradient Texture
**What it does:** a smooth ramp from the coordinates. Types: Linear (left to right), Quadratic, Easing (smooth start and end), Diagonal, Spherical and Quadratic Sphere (bright in the middle, centred on the coordinate origin), Radial (angle around the origin). Picture: [p01_gradient_types](experiments_shader_node_toolbox/pictures/p01_gradient_types.png). **On a 0..1 tile the sphere and radial types are centred on the tile corner unless you first move the coordinates by (-0.5, -0.5, 0) with Mapping** (done in the picture). Helps: vertical fade for drips and moss (Linear along v times a noise), soft vignettes, shading each stone.

### 5.7 Magic Texture
**What it does:** a colourful interference pattern of sine waves (Depth = number of iterations, Distortion = bending). Depth 0 to 2 gives smooth woven bands; Depth 10 with Distortion 4 turns into fine grain that looks like white noise. Picture: [p30_magic](experiments_shader_node_toolbox/pictures/p30_magic.png). Rarely useful for our six surfaces; possible as a cheap smooth colour field to bend coordinates. Not seamless.

### 5.8 Wave Texture - bands and rings
**What it does:** stripes or rings from a sine, saw or triangle wave, bent by a built-in noise.
**Example first:** Bands along Y, Saw, Scale 24, Distortion 5, Detail 3 gives wavy horizontal wood grain (used in the wood demo).
Settings (TESTED, picture [p31_wave](experiments_shader_node_toolbox/pictures/p31_wave.png)): **Type** Bands or Rings; **Bands Direction** X, Y, Z, Diagonal; **Rings Direction** X, Y, Z, Spherical (Spherical = concentric rings: **knots**, once centred on the knot with Mapping); **Profile** Sine (smooth), Saw (sharp edge each period), **Triangle** (new, not in the manual); **Scale** = how many bands; **Distortion** = how much the built-in noise bends them (5 gives wavy lines, 12 with Saw gives torn, jagged edges); **Detail, Detail Scale, Detail Roughness** = the bending noise; **Phase Offset** = slides the bands (NOT TESTED). Bands along X with no Distortion do not change when you move in v (difference 0.0 after moving v by 1) but do not repeat when you move u by 1 at Scale 4 (difference 0.47); with Distortion 3 they differ both ways (0.45 and 0.16).
Helps: **wood** (grain, rings of knots), **mud** (tyre ruts: bent diagonal bands), **metal** (brushed streaks).

### 5.9 White Noise Texture
**What it does:** a different random number (0..1) for every different input, with no smoothness at all.
**Example first (TESTED):** snap the coordinates to a grid with Vector Math Snap 1/32, then White Noise: 1019 different random values over 32 x 32 = 1024 blocks (range 0.001..0.999). Picture: [p32_white_noise](experiments_shader_node_toolbox/pictures/p32_white_noise.png). This is the tool for "one random number per brick / per cell / per block"; see section 8 for a tiling version.
Pitfall from the manual (NOT TESTED): tiny number errors make different results; add an arbitrary offset, or take the absolute value, if bands appear.
Helps: per-brick, per-plank, per-stone random tints and dice rolls.

### 5.10 Gabor Texture (new in 4.3)
**What it does:** noise made of oriented ripples: bands that all run in a chosen direction, like brushed metal, wood grain, fabric or sand ripples.
Settings (TESTED, picture [p33_gabor](experiments_shader_node_toolbox/pictures/p33_gabor.png)): **2D or 3D** (2D ignores Z: 0.4479 at Z 0.1 and Z 9; 3D uses it); **Scale** (overall size); **Frequency** (how many bands across the direction; 5 gives fine hairlines); **Anisotropy** (1 = all bands parallel, 0.4 = partly scrambled, 0 = no direction at all); **Orientation** (angle in 2D: 0.785 = 45 degrees by default, 1.57 = horizontal bands; a direction vector in 3D). Outputs: **Value** (sine of the phase times the intensity, with some weak patches), **Phase** (clean stripes with no weak patches, 0..1 and wrapping round), **Intensity** (smooth blobs: where the stripes meet and break, it is near zero; multiply by it to hide the broken spots). It costs more than Noise (manual).
Helps: **wood grain** (long directional fibres), **scratched or brushed metal**, slate streaks. Not seamless.

### 5.11 Radial Tiling (new in 5.0)
**What it does:** cuts the plane into pie slices around the origin (Sides) and gives each slice its own coordinate system, so any texture you plug in repeats around a centre.
Settings (TESTED once, picture [p35_radial_tiling](experiments_shader_node_toolbox/pictures/p35_radial_tiling.png), a Checker drawn inside each slice): **Sides** (a non-whole value such as 5.5 gives one smaller odd slice), **Roundness** (0 = straight slice edges, 1 = round), **Normalize**. Outputs: Segment Coordinates, Segment ID, Segment Width, Segment Rotation.
Helps: **rivet heads** (the metal reference shows faceted round heads), **wood knots**, rosettes. Only the checker use was tested.

### 5.12 Other pattern-like nodes that exist
Image Texture, Environment Texture, Sky Texture, IES Texture (not used: no images allowed in recipes). Geometry-Nodes-only things in section 9. Point Density was removed in 5.0.

---

## 6. Group B - the shapers

### 6.1 Color Ramp - turns a grey value into a colour, and makes hard edges
**What it does:** you place colour stops along 0..1; the input value picks a colour.
Interpolation (TESTED, picture [s01_color_ramp_interpolation](experiments_shader_node_toolbox/pictures/s01_color_ramp_interpolation.png)): **Constant** = hard steps, flat colours (this IS the "painted patches" tool); **Linear** = straight blend; **Ease** = smooth blend; **Cardinal** = smooth, passes through the stops but **overshoots** (a saturated orange appeared that is not in the stops); **B-Spline** = smoothest, but **does not reach the end stops** (the first dark stop never appears).
Colour mode (TESTED, picture [s01b_color_ramp_hue](experiments_shader_node_toolbox/pictures/s01b_color_ramp_hue.png)): **RGB** blends straight (red to blue goes through a muddy grey-purple); **HSV / HSL** blends by hue, and **Hue Interpolation** picks the way round the colour wheel: Near (short way, via magenta), Far (long way: yellow, green, cyan), Clockwise, Counter-clockwise (only shown for HSV/HSL).
Helps: all six surfaces (colour palettes from the reference: brick reds 0.16..0.35 linear, slate blue-greys, wood browns, rust oranges, mud browns and blue-grey water, gravel greys with orange soil). Use Constant with 4 to 6 stops for flat painted patches.

### 6.2 Map Range - move one range onto another (the contrast and threshold tool)
**What it does:** takes values between From Min and From Max and spreads them over To Min to To Max.
**Example first:** From 0.4..0.6 to 0..1 turns cloud noise into near black-and-white. Narrowing the From window = more contrast: From 0.3..0.7 soft, 0.45..0.55 hard blotches, 0.49..0.51 almost no soft edge (picture [s02b_map_range_window](experiments_shader_node_toolbox/pictures/s02b_map_range_window.png)).
Settings (TESTED, picture [s02_map_range](experiments_shader_node_toolbox/pictures/s02_map_range.png), numbers in `map_range_numbers.json`):
- **Interpolation:** Linear; **Stepped Linear** (+ **Steps**: in the picture Steps 2 gives 3 grey levels and Steps 4 gives 5, a posterised look; the numbers at x = 0.45, 0.5, 0.55 with Steps 4 were 0.25, 0.5, 0.75); **Smooth Step**; **Smoother Step** (S-shaped, softer at both ends).
- **Clamp:** with Linear and Stepped, Clamp ON keeps the result inside To Min..To Max; Clamp OFF lets values run past (x = 0.2 gave -0.97, x = 0.8 gave 2.02 for From 0.4..0.6). **Smooth Step and Smoother Step stay inside the range whatever Clamp says.**
- **Reverse a range** by putting From Min above From Max: used for the puddle mask (everything BELOW the water level becomes 1).
- Float or Vector data type.
Helps: every surface (contrast of noises, thresholds for patches, posterised patch shading, the puddle mask).

### 6.3 Math - arithmetic on values
**What it does:** one operation on one, two or three values. Operations that matter for textures (TESTED, picture [s03_math_operations](experiments_shader_node_toolbox/pictures/s03_math_operations.png)): **Add/Subtract/Multiply** (brightness and contrast; "Clamp" checkbox limits to 0..1); **Power** (3 darkens the middle: a gamma curve); **Greater Than / Less Than** (hard threshold: black and white mask from noise); **Compare** (value within epsilon of another: a thin contour line around a noise level, here 0.5 +- 0.03); **Absolute** (after subtracting 0.5, makes ridges at the middle level); **Fraction** (repeats 0..1: contour bands); **Ping-Pong** (zig-zag); **Snap** (rounds to steps of 0.25: posterise); **Smooth Min/Max** (soft union of two shapes, with a distance); **Wrap** (loops a value into a window); **Sine/Cosine**; **Floor / Round / Ceil**; **Modulo / Floored Modulo** (used in section 8). Others exist (Logarithm, Arc functions, Sign, Minimum, Maximum...). The third input is shown only for Multiply Add, Compare, Smooth Min/Max, Wrap and a few more.
Helps: everything; the glue of a recipe.

### 6.4 Float Curve - draw a smooth curve that reshapes values
**What it does:** a curve editor: the input value goes in at the bottom, the new value comes out at the left. Picture: [s04_float_curve](experiments_shader_node_toolbox/pictures/s04_float_curve.png) (identity, S-curve, hump, steps). Use it where a Color Ramp is clumsy: smooth S-shaped contrast, or a hump that peaks at one level (a contour band). **Pitfall (TESTED):** default `extend` is EXTRAPOLATED, so values outside 0..1 shoot off (-0.5 gave -2.99); set `mapping.extend = 'HORIZONTAL'` to clamp. Python recipe: `curve = node.mapping.curves[0]; curve.points.new(0.35, 0.1); node.mapping.update()`.
Helps: shaping height profiles (rounded brick edges), wear masks.

### 6.5 RGB Curves
Curve editor for colours: a combined curve plus red, green, blue curves; `tone` is STANDARD (hue may shift) or FILMLIKE (keeps hue). Same Python as Float Curve. **NOT TESTED** visually. Helps: colour grading a finished colour map (push shadows blue, highlights warm).

### 6.6 Clamp
Limits a value between Min and Max. Type **Min Max** (if Min is above Max the result is always Max) or **Range** (swaps them). **NOT TESTED**. Often replaced by the Clamp checkboxes on Math and Map Range.

### 6.7 Mix (and Mix Legacy) - blending
**What it does:** blends two inputs A and B by a Factor (0 = A, 1 = B). Data types: Float, Vector, Colour (with blend modes), Rotation.
**Blend modes in 5.2.2 (TESTED, picture [s05_mix_blend_modes](experiments_shader_node_toolbox/pictures/s05_mix_blend_modes.png), A = bricks, B = blue-yellow noise, Factor 1):** Mix, Darken, **Multiply** (tints: the usual way to stain a base colour), Burn, Lighten, Screen, Dodge, Add, **Overlay** and **Soft Light** (add detail while keeping the base colour), Linear Light, **Difference**, Exclusion, Subtract, Divide, **Hue, Saturation, Colour, Value** (take only that part from B). Options: Clamp Factor (default on), Clamp Result (colour only).
Mix (Legacy) is the old Mix RGB. Helps: all surfaces (stain with Multiply, grime with Overlay, wet darkening, rust over paint with a mask as the Factor).

### 6.8 Invert, Hue/Saturation/Value, Brightness/Contrast, Gamma (TESTED, picture [s06_color_adjusters](experiments_shader_node_toolbox/pictures/s06_color_adjusters.png))
- **Invert Color** (Factor 1 = full negative, 0.5 = flat grey).
- **Hue/Saturation/Value:** Hue 0.5 = no change (0.3 turns the oranges to violet, 0.7 to green); Saturation 1 = no change (0 = grey, 1.6 = vivid); Value 1 = no change (0.5 = darker); Factor mixes with the original.
- **Brightness/Contrast:** Bright +-0.2 shifts, Contrast +0.5 deepens shadows and brightens highlights, -0.5 flattens.
- **Gamma:** 0.5 lifts the whole picture; 2 darkens the midtones. Gamma 0.4545 converts linear to screen brightness (used in section 8, "height from colour").
Helps: tuning a finished colour map toward the reference.

### 6.9 Mapping - move, turn, scale the coordinates
**What it does:** changes the coordinates before a pattern. Settings Type (TESTED with a point (0.2, 0.4, 0.6), Location (1,2,3), Scale 2): **Point** = scale then add location (1.4, 2.8, 4.2): use for textures; **Texture** = the inverse (-0.4, -0.8, -1.2): the pattern moves the opposite way; **Vector** = scale and rotate, location ignored (0.4, 0.8, 1.2); **Normal** = like Vector but the result is made length 1 (0.27, 0.54, 0.80): unusable for texture coordinates (gives a fan-shaped pattern). Pictures: [s07_mapping](experiments_shader_node_toolbox/pictures/s07_mapping.png), [s07b_mapping_basic](experiments_shader_node_toolbox/pictures/s07b_mapping_basic.png).
**Stretching trick (TESTED):** a LARGER scale in one direction makes MORE and SMALLER features in that direction. So Scale (1, 4, 1) on noise makes the blobs 4 times thinner up the picture (flat streaks that run left to right), and Scale (14, 1.2, 1) makes blobs very narrow across and long up and down: **vertical streaks**. This made the slate and metal drips in the demo recipes.
Helps: streaks (slate, metal, wood), rotating brick or grain, moving a pattern so two noises are different.

### 6.10 Vector Math - arithmetic on coordinates
**What it does:** the same operations as Math but on three-number vectors. Tricks (TESTED, picture [s09_vector_math_tricks](experiments_shader_node_toolbox/pictures/s09_vector_math_tricks.png)): **Snap** (pixelate the coordinates into blocks), **Fraction / Wrap** (repeat a small piece 3 x 3 times; the repeat is exactly periodic), **Floor** (flat: noise at whole numbers is a constant 0.5, which is why the picture is one flat tone), **Absolute** (mirror).
**Domain warping (TESTED, picture [s08_warp](experiments_shader_node_toolbox/pictures/s08_warp.png)):** Noise Color output, Vector Math Subtract (0.5, 0.5, 0.5), Vector Math Scale by 0.05 to 0.3, Vector Math Add the original coordinates, feed the result into the next pattern. 0.05 wobbles the lines, 0.3 tears the cells apart. Idea also used by planetset's docs and the Inigo Quilez article (concept; their numbers not checked).
Helps: bending Voronoi cracks and Brick edges so they look hand-drawn; wobbly stone outlines.

### 6.11 Vector Rotate
Turns coordinates around an axis (Axis Angle, X, Y or Z axis, Euler). Manual advice: rotate by an odd angle to avoid banding in noise at tilted planes. **NOT TESTED** (the Mapping rotation does the same and was tested).

### 6.12 Separate / Combine Color and XYZ, RGB to BW
**Separate XYZ** pulls u and v out of the coordinate (used constantly); **Combine XYZ** builds a vector (used to feed an exact test point); **Separate / Combine Color** in RGB, HSV or HSL (pulls the red channel of a Voronoi cell colour for a per-cell random number: gravel demo); **RGB to BW** gives brightness (height from colour). Tested as plumbing in every picture here. In Geometry Nodes the colour versions are Function nodes (section 9). **Squeeze Value (Legacy)** and **Mix (Legacy)** are old nodes kept for old files.

---

## 7. Group C - surface-effect nodes (light sees height, edges and crevices)

### 7.1 Bump - turns a Height into a changed surface direction (no geometry moved)
**What it does:** looks at the Height at the point and two neighbours and tilts the surface direction (normal) so light sees bumps.
Inputs (TESTED, pictures [e01_bump_strength](experiments_shader_node_toolbox/pictures/e01_bump_strength.png), [e02_bump_distance](experiments_shader_node_toolbox/pictures/e02_bump_distance.png), [e03_bump_invert](experiments_shader_node_toolbox/pictures/e03_bump_invert.png), [e04_bump_filter_width](experiments_shader_node_toolbox/pictures/e04_bump_filter_width.png)):
- **Strength** 0 = no effect, 1 = full. Fades the effect in.
- **Distance:** how tall a Height of 1.0 is, in object units. **Default 0.001 since 4.5 = almost invisible.** For a 1-unit tile try 0.02 to 0.1 (when the bake tool fitted a Bump Distance to my six demo recipes it chose 0.025 to 0.2).
- **Filter Width** (pixels): the sampling size. Default 0.1 is fine for smooth noise; **a hard-edged height such as brick mortar shows no edge until Filter Width is 1 or more** (4 gives clear bevelled edges).
- **Invert:** swaps bumps and dents. **Height:** the grey value. **Normal:** chain a second Bump after a first one (layers of detail).
- If Height is not connected the node does nothing (manual, NOT TESTED).
Helps: all six surfaces. It also gives the bake tool a normal map "the Blender way" (`normal_bumpnode.png`).

### 7.2 Displacement - really moves the surface
**What it does:** moves points along the normal by (Height - Midlevel) x Scale. Defaults: Midlevel 0.5, Scale 0.01 (1 cm since 4.5). It only does something real if **Material > Settings > Displacement** is "Displacement Only" or "Displacement and Bump" and the mesh is cut finely (here: simple subdivision level 8 on a plane). TESTED, pictures [e10_displacement_side](experiments_shader_node_toolbox/pictures/e10_displacement_side.png) and [e10_displacement_top](experiments_shader_node_toolbox/pictures/e10_displacement_top.png): seen from above all three methods look alike; seen edge-on, Bump Only has no outline while the two displacement methods show a ragged band about 0.05 to 0.06 thick (Scale 0.12 on a noise that spans about 0.25..0.75). Python: `material.displacement_method = 'BUMP' | 'DISPLACEMENT' | 'BOTH'`. Memory-hungry: manual says "Bump Only is least accurate, most memory-efficient". Helps: stones and brick that must show real silhouettes and shadows; not needed for flat baked maps.

### 7.3 Vector Displacement - moves points in any direction from a colour map. **NOT TESTED** (needs a vector map; we are not using images). Helps: overhangs only.

### 7.4 Normal Map - reads a normal map picture
Inputs: Strength (0 = off, 2.5 = strong), Color. Settings: **Space** (Tangent usual), **Convention OpenGL / DirectX** (added in 5.1), **UV Map**, Base (Original / Displaced). TESTED, picture [e05_normal_map](experiments_shader_node_toolbox/pictures/e05_normal_map.png): a normal map made from my own noise height (Sobel, OpenGL, green up) gave a render that matches the Bump node's render of the same height at correlation 0.85; the same map read as DirectX gave -0.02 (the lighting from above and below is swapped); Strength 2.5 deepens shadows. **This confirms the project's maps are OpenGL (green up) and Blender wants OpenGL.** The uploaded reference normals are DirectX: set Convention to DirectX or flip green.

### 7.5 Bevel - rounds hard edges in the shading only (Cycles only)
Inputs Radius (default 0.05), Samples (default 4; the picture used 16). Does not move geometry. TESTED, pictures [e11_bevel_shading](experiments_shader_node_toolbox/pictures/e11_bevel_shading.png) and [e11_bevel_edge_mask](experiments_shader_node_toolbox/pictures/e11_bevel_edge_mask.png). **Edge mask recipe (TESTED):** Dot Product of Bevel Normal and Geometry True Normal, then 1 - dot, times 12, clamp = white lines exactly along the edges whose width follows Radius (0.01, 0.03, 0.08 on a 0.5 cube). Used for edge wear (paint chipped on corners). **Needs real corners:** on a flat tile there are none.

### 7.6 Ambient Occlusion - how hemmed-in a point is
Inputs Color, Distance (default 1), Normal; settings Samples (16), **Inside** (finds convex instead of concave), **Only Local** (ignore other objects). TESTED, picture [e12_ao](experiments_shader_node_toolbox/pictures/e12_ao.png): ground next to cubes darkens within Distance (0.1 = thin, 1 = a wide soft shadow, the ground far from the cubes stays white); Only Local gives all white because each cube and the ground are separate objects; Inside flips it to black cube tops. Use: dirt in crevices (mud, gravel gaps, brick joints). Needs real geometry (displacement or an object), costs a lot.

### 7.7 Wireframe - lines on the mesh edges. Size 0.01 default, Pixel Size option. TESTED, picture [e15_wireframe](experiments_shader_node_toolbox/pictures/e15_wireframe.png) (size 0.05 floods a small mesh). Not useful for our surfaces except as a debugging view.

### 7.8 Geometry node (the input node, not Geometry Nodes)
Outputs Position, Normal, Tangent, True Normal, Incoming, Parametric, Backfacing, **Pointiness**, **Random Per Island**. Pointiness = a per-vertex estimate of curvature: flat 0.5, convex edges above, concave below. TESTED, picture [e13_pointiness](experiments_shader_node_toolbox/pictures/e13_pointiness.png): on a bevelled cube with Simple subdivision 0, 1, 2, 3, the cube starts nearly all bright and ends mid-grey faces with only thin bright bands at the edges. **The same shape gives different pointiness at different mesh density.** Web pages: "Pointiness measures edge angles" (blenderartists 2016), "wear is better from Bevel node" (BlenderNation 2019/2023). Cycles only (manual).

### 7.9 Layer Weight and Fresnel - how much you look along the surface
**Fresnel:** reflection amount by angle, with IOR (default 1.5). **Layer Weight:** Fresnel and Facing outputs with a Blend input (default 0.5). TESTED, picture [e14_fresnel_layer_weight](experiments_shader_node_toolbox/pictures/e14_fresnel_layer_weight.png): Fresnel IOR 1.1 is black except a rim, 1.45 grey, 3 pale; Layer Weight Fresnel Blend 0.2 dark, 0.5 mid; Facing gives a bright rim and dark centre when seen from above. Use: edge brightening on stones, sheen on wet surfaces. Little use in a flat bake.

### 7.10 Raycast (new in 5.1)
Shoots a ray through the scene and returns hit, distance, position, normal. Cycles and EEVEE. **NOT TESTED.** Could drive thickness or custom AO; expensive per the manual.

### 7.11 Other
**Light Path** (is this a camera ray?), **Object Info**, **Attribute**, **Vertex Color**, **Tangent**, **Camera Data**, **Light Falloff**: exist; not used.

---

## 8. Combining tools: tested recipes that came out of this research

### 8.1 A home-made brick that tiles AND has per-brick randomness AND local coordinates (TESTED: `t11_home_made_brick.py`)
Why: the Brick node's random colour does not repeat, and it gives no brick number.
Chain (cols = 4 whole, rows = 12 even):
1. Separate XYZ of the tile coordinate: u, v.
2. `v * rows` -> **Floor** = row number; **Fraction** = fy (0..1 up the brick).
3. `u * cols + 0.5 * (row mod 2)` (Math Multiply Add with Floored Modulo of the row by 2) -> **Floor** = column; **Fraction** = fx (0..1 along the brick).
4. Wrap the numbers: column **Floored Modulo** cols, row **Floored Modulo** rows. Combine XYZ (column, row, 0) -> **White Noise 2D** = one random number per brick.
5. Distance to the nearest brick side from fx and fy (Minimum of x and 1-x, scaled by rows/cols to match the brick shape) -> mortar where it is below 0.07.
Result: 48 different random values for 48 bricks; the colour picture is **identical after moving by one tile in u or v (difference 0.0)**; fx / fy let you draw a light chip along each brick's top edge. Picture: [r01_home_made_brick_tiled_2x2](experiments_shader_node_toolbox/pictures/r01_home_made_brick_tiled_2x2.png). Cols must be whole and rows even, otherwise the half-brick shift does not close.

### 8.2 Hard-edged painted patches
Noise (Scale 5, Detail 4) -> Map Range From 0.45..0.55 -> (Color Ramp **Constant** with 3 to 5 flat colours, or Math Greater Than 0.5 as a mask). Pictures s02b, s03. This is the mechanism behind the reference's flat colour areas; set colours from the reference palette (section 6.1).

### 8.3 Stains that run down the wall or plate
Mapping Scale (1, 0.18, 1) on a Noise (Scale 2.5, Detail 5) -> Map Range 0.55..0.75 -> Mix Multiply or Mix with a dark colour. Slate demo used Scale (14, 1.2, 1) and the metal demo Scale (10, 1, 1) and (9, 0.7, 1) for fine vertical streaks (picture z01).

### 8.4 Cracks and stone gaps
Voronoi Distance to Edge (Scale 5 to 14) -> Math Less Than 0.012..0.1 -> dark; stretch with Mapping Scale (0.18, 1, 1) for wood cracks along the grain; warp coordinates first (8.5) to look hand-drawn.

### 8.5 Domain warping (TESTED): section 6.10.

### 8.6 Rivets
Voronoi F1, Randomness 0, Scale 5 -> Math Less Than 0.09 = a regular grid of round dots; a Map Range of the Distance (0..0.09 -> 0.9..0.2) gives a dome shading.

### 8.7 Stones for gravel and mud
Voronoi F1 + Distance to Edge for the outline + Color red channel (Separate Color) through a Color Ramp **Constant** (greys, blue-grey, orange-brown) + a dice roll (green channel Greater Than 0.35) to leave some cells as soil. N-Sphere Radius > 0.36 keeps only roomy cells as stones (mud demo).

### 8.8 Height from colour brightness (TESTED; matches how the references were made)
Gamma 0.4545 (linear to screen brightness) -> RGB to BW = Height. Result on the demo recipes (texture_compare groups): brick normal group 0.33 -> 0.43; slate height group 0.03 -> 0.14, overall 0.29 -> 0.33; metal unchanged. The references' heights track colour brightness (correlation 0.96-0.99, PROCEDURAL_NOTES).

### 8.9 Edge wear with Bevel (TESTED, 7.5): Bevel Normal vs True Normal -> mask -> Mix the worn (metal) colour into the painted colour.

### 8.10 Puddles and wetness (TESTED, picture [m02_puddle_stages](experiments_shader_node_toolbox/pictures/m02_puddle_stages.png))
Built one step at a time on a tilted plane under a simple sky (one Principled BSDF, everything driven by two masks from the Height):
1. **Dry mud:** Roughness 0.9, colour ramp brown, Bump Distance 0.03 on the height.
2. **Wet rim:** `wet` = Map Range(height, From Min 0.55, From Max 0.34, To 0..1, Smooth Step): high ground 0, low ground 1. Base colour = Mix(dry colour, dry x grey 0.45 Multiply, wet). Wet ground darkens.
3. **Roughness:** Mix 0.9 -> 0.35 by `wet`, then -> 0.02 by `puddle`.
4. **Flat puddle bed:** `puddle` = Map Range(height, 0.40 -> 0.34, 0..1, Smooth Step) (water level 0.40). Feed Bump a height made with Math **Maximum(height, 0.40)** so the bed is flat while the dry ground keeps its bumps.
5. **Water colour:** Mix base colour toward blue-grey (0.12, 0.17, 0.25) by `puddle`; set the Principled **IOR to 1.33**.
6. **The old way** (a 2012 forum thread, still works): Mix Shader of the mud shader and a Glossy BSDF (Roughness 0.02, tinted) with the puddle mask as Factor. It reflects the sky strongly. Our bake wants single numbers per pixel (colour, roughness, metallic), so the one-BSDF way (steps 1-5) is easier to bake channel by channel.
Not covered: ripples, reflections of real objects, the reference's flat blue-grey patches (use step 5 with Roughness left at 0.9 for a flat painted look).

### 8.11 Whole-number layouts that really tile (TESTED, section 2): Checker and Brick mortar with whole counts; everything random needs the project's seamless groups (`tileable_noise_group`, `tileable_voronoi_group`) or a home-made hash like 8.1.

---

## 9. Group D - shader nodes: what the final look is made of

### 9.1 Principled BSDF - the one node that does most materials
Defaults in 5.2.2 (TESTED by listing): Base Color 0.8 grey, Metallic 0, Roughness 0.5, IOR 1.5, Specular IOR Level 0.5, Coat Weight 0 (Coat Roughness 0.03, Coat IOR 1.5), Subsurface Weight 0 (Radius 1, 0.2, 0.1; Scale 0.005), Sheen 0, Emission Strength 0, Thin Wall off, Diffuse Roughness 0, Distribution Multiscatter GGX, Subsurface Method Random Walk. Picture of sweeps on a sphere under a sky and a sun: [m01_principled_sweeps](experiments_shader_node_toolbox/pictures/m01_principled_sweeps.png) (TESTED).
- **Base Color:** the colour of the surface; for metals the colour of the reflection.
- **Roughness:** 0 = mirror (the sun shows as a pin dot), 0.15 small sharp glints, 0.35 soft highlight, 1 matte. Brick, slate, dry mud, gravel, old wood: 0.7 to 0.95.
- **Metallic:** 0 = non-metal (diffuse body plus faint reflection), 1 = metal (reflects the sky tinted by base colour; looks dark if there is nothing to reflect). Rusted steel: 1 on clean metal, 0 on rust (the demo made Metallic = 0.9 minus 0.9 x rust mask).
- **Specular IOR Level:** the strength of the white reflection on non-metals: 0 removes the highlight entirely, 1 doubles it. Good for matte rock, brick.
- **Coat Weight / Coat Roughness / Coat Tint / Coat IOR:** a clear glossy layer over everything: a rough base with Coat 0.25 to 1 (Coat Roughness 0.03) shows a pin-sharp highlight even at Roughness 0.9. Use for **wet** surfaces and glazed finishes (wet brick, wet stones).
- **Subsurface Weight / Radius / Scale:** light soaks in a little and comes out blurred: softens the shading; **very noisy at low sample counts** (grainy at 40 samples). Not needed for our six surfaces.
- **Emission Color / Strength:** the surface glows. Strength 0 = off. In our tools, emission is used to "photograph" one channel at a time.
- **Sheen:** dusty fuzz on top (4.0 microfibre model). Could dust the tops of stones. NOT TESTED.
- **Thin Wall, Transmission, Anisotropic, Thin Film:** NOT TESTED.
- **Normal / Coat Normal:** connect the Bump or Normal Map output here.

### 9.2 Other BSDFs
**Metallic BSDF** (4.3): metal only, with an Edge Tint or physical IOR; NOT TESTED. **Glossy BSDF** (now includes anisotropy), **Diffuse**, **Mix Shader** (blend two shaders by a factor: used in the old puddle way), **Add Shader**, **Emission** (used for baking channels), **Holdout**, **Toon BSDF**, **Translucent**, **Transparent**, **Glass**, **Refraction**, **Sheen**, **Hair**, **Volume** shaders: exist. **Shader to RGB** (turns a lit shader into a colour you can ramp): **white in Cycles**; EEVEE only.

### 9.3 Which Principled values suit which of our surfaces (starting guesses; only the puddle and Principled behaviour above was tested)
- Brick: Roughness 0.85, Specular IOR Level 0.3, Bump from the height, wet version with Coat.
- Slate: Roughness 0.55 to 0.7, Coat 0.2 for a wet-slate look.
- Wood: Roughness 0.9, Specular IOR Level 0.3.
- Rusted metal: Metallic 1 (clean) / 0 (rust), Roughness 0.45 (clean) to 0.85 (rust).
- Mud with puddles: dry 0.9, wet rim 0.35, puddle 0.02, IOR 1.33, flat blue-grey Base Color in the puddle.
- Gravel: Roughness 0.8 to 0.9; wet look with Coat on the stones.

---

## 10. The Geometry Nodes editor: texture and converter nodes

TESTED by trying to add every node (`addable_nodes.txt`, `gn_checks.json`): **the Geometry Nodes editor has 360 node types; these shader-editor texture/converter nodes are also there:** Noise, Voronoi, Brick, Checker, Gabor, Gradient, Magic, Wave, White Noise, Color Ramp, Map Range, Math, Vector Math, Clamp, Float Curve, RGB Curves, Mix, Mix (Legacy), Gamma, Vector Rotate, Separate XYZ, Combine XYZ, Radial Tiling. (Plus Blackbody, Value, Vector Curves.) **Not available there:** Invert, Hue/Saturation/Value, Brightness/Contrast, Mapping, Bump, Normal Map, Displacement, Bevel, Ambient Occlusion, Wireframe, Fresnel, Layer Weight, Geometry (input), Principled BSDF, RGB to BW, Texture Coordinate. Colour Separate/Combine exist there as Function nodes. (Geometry Nodes has its own Position, Normal, Image Texture and Rotate Vector nodes.)

What is different there (TESTED):
- **The texture's Vector input defaults to Position** (a field: one value per point, per face or per corner). Connected explicitly to Position, the stored result matched the unconnected one exactly (largest difference 0.0).
- **Noise moves real geometry:** a 129 x 129 grid, Set Position Offset Z = (noise - 0.5) x 0.2: ragged side silhouette, unlike Bump Only. Picture [g01_gn_displaced_grid](experiments_shader_node_toolbox/pictures/g01_gn_displaced_grid.png).
- **Store Named Attribute** keeps a noise as a number on each point; a material reads it with the **Attribute** node (type Geometry, name `wetness`): picture [g02_gn_attribute_in_material](experiments_shader_node_toolbox/pictures/g02_gn_attribute_in_material.png). This is how a geometry-made mask (curvature, distance to something, instance index) gets into a shader.
- **Pitfall (TESTED):** the first test rendered black: a mesh made inside Geometry Nodes has no material; add **Set Material** (and Set Shade Smooth for nicer lighting).
- The Geometry Nodes manual says noise Normalize gives 0..1 or -1..1 for all types; I did not test the Geometry Nodes version of Normalize.

---

## 11. Which node helps which surface (summary)

| Node | Brick | Slate | Wood | Rusted metal | Mud + puddles | Gravel |
|---|---|---|---|---|---|---|
| Brick Texture | layout + mortar | shingle layout, black gaps | plank layout | panel seams | - | - |
| Noise | blotches, soot, mortar grain | moss, streaks | grain streaks, weathering | rust patches, drips | ground colour, puddle shapes | soil grain, rock texture |
| Voronoi | chipped corners | chunky tiles (Chebychev) | cracks (stretched) | rivets (Randomness 0) | stones, small rocks | the stones themselves |
| Wave | - | - | grain, knots (rings) | brushed lines | tyre ruts (bent bands) | - |
| Gabor | - | streaks | fibres | scratches | - | - |
| Mapping (stretch) | vertical stains | vertical streaks | long grain | drips | rotate the ruts | - |
| Color Ramp (Constant) | flat colour patches | flat patches | flat patches | rust bands | mud/water bands | stone colours |
| Map Range / Math | hard masks | hard masks | hard masks | rust mask | puddle mask | stone/soil mask |
| Mix (Multiply, Overlay) | stains | moss | weathering | rust over paint | wet darkening | - |
| Vector Math warp | wobbly edges | wobbly edges | wavy grain | - | wavy ruts | wobbly stones |
| Bump / Normal Map | brick relief | tile relief | grain relief | panels, rivets | mud relief, flat puddle bed | stone relief |
| Bevel / AO / Pointiness | edges, joints | edges | - | edge wear | crevice dirt | gap dirt |
| Principled (Roughness, Coat, IOR) | roughness map | wet slate | roughness | metallic + roughness maps | wet look + water | wet stones |

---

## 12. How close do toolbox-only first attempts get? (TESTED)

I built six quick recipes from only the nodes above (`mini_recipes/toolbox_demo_recipes.py`), not tuned, not seamless, and compared them to the references with the project's scorer (`texture_compare.py`, 0 = different surface, 1 = same by that measure; re-shuffled reference about 0.99). Side-by-side: [z01_toolbox_demo_vs_reference](experiments_shader_node_toolbox/pictures/z01_toolbox_demo_vs_reference.png).

| Surface | overall | colour | height | normal | What looks right | What is missing |
|---|---|---|---|---|---|---|
| brick | 0.16 | 0.23 | 0.00 | 0.33 | layout, palette (colour-distribution score 0.73), mortar tan, soot | edges too clean and smooth, no chipped bricks, no hard-edged patches |
| slate | 0.29 | 0.41 | 0.03 | 0.53 | shingle layout, vertical streaks | tile edge highlights, moss patches too weak, no hand-drawn irregularity |
| wood | 0.13 | 0.25 | 0.00 | 0.05 | planks, grain direction | planks too regular, no splintered cracks, knots, rust-coloured splotches |
| metal | 0.21 | 0.15 | 0.00 | 0.43 | rust patches, rivets | straps, diagonal bars, proper rivet domes, scratches |
| mud | 0.05 | 0.06 | 0.00 | 0.17 | brown/blue-grey palette | puddles far too big, stones too many and round, no tyre-track ridges |
| gravel | 0.11 | 0.12 | 0.00 | 0.35 | polygonal stones, palette | stones too grey and large, orange soil nearly gone, no highlights on stone faces |

Why the heights score 0: the demo heights come from invented blocks; the references' heights follow the colour brightness. With "height from colour" (8.8) slate height rose to 0.14 and brick normal to 0.43. The bake times at 1254 x 1254 (CPU, 2 threads) were 18 s (brick, slate), 35 s (wood, metal), 44 s (mud), 54 s (gravel, six Voronoi nodes): Voronoi-heavy recipes cost the most.

What this says for the builders: layout nodes get you 60% of the structure; the references' look comes from (1) hard-edged flat colour patches (Color Ramp Constant, Map Range with a narrow window), (2) a handful of clearly different palette colours used in specific places, (3) outlines and chips at edges (Distance to Edge, Bevel-like masks), (4) heights made from the colour brightness.

---

## 13. Nodes that deserve their own parameter-sweep picture in the guides (and where I already made one)

1. Noise Texture: Detail, Roughness, Lacunarity, Distortion, Scale, type, Ridged Offset, 4D W (p02-p08).
2. Voronoi: Feature, Distance Metric, Randomness, Smoothness, Detail, Distance to Edge + threshold (p10-p15).
3. Brick: Mortar Size/Smooth, Bias, Offset, layout (p20, p21).
4. Wave: type/profile/distortion (p31). 5. Gabor (p33). 6. Gradient types (p01). 7. Magic (p30). 8. Radial Tiling (p35). 9. White Noise on blocks (p32).
10. Color Ramp: interpolation and hue path (s01, s01b). 11. Map Range (s02, s02b). 12. Math operations (s03). 13. Float Curve (s04). 14. Mix blend modes (s05). 15. Colour adjusters (s06). 16. Mapping types (s07). 17. Vector Math: domain warp and tiling tricks (s08, s09).
18. Bump: Strength, Distance, Filter Width, Invert (e01-e04). 19. Normal Map convention and Strength (e05). 20. Displacement method (e10). 21. Bevel edge mask (e11). 22. Ambient Occlusion (e12). 23. Pointiness vs density (e13). 24. Fresnel / Layer Weight (e14).
25. Principled BSDF: Roughness, Metallic, Coat, Specular IOR Level, Subsurface, Emission (m01). 26. Puddle build-up (m02).
Still to make for the final guides (not yet pictured): Float Curve shapes with Color Ramp comparison, Principled Anisotropy/Sheen, Wave Phase Offset, Math Compare with different epsilons, Mix Factor sweeps, per-surface "recipe before/after" strips.

---

## 14. Recipe cards (short; every one was run)

1. **Contrast a noise:** Noise (Scale 5, Detail 4-6) -> Map Range From 0.3..0.7 to 0..1. (s02b)
2. **Flat painted patches:** Noise -> Map Range From 0.45..0.55 -> Color Ramp Constant (3-5 flat colours). (s02b, s03)
3. **Vertical streaks:** Mapping Scale (14, 1.2, 1) -> Noise (Detail 6, Roughness 0.62) -> Map Range. (z01 slate and metal)
4. **Wobbly edges:** Noise Color - (0.5,0.5,0.5), x 0.05-0.3, + coordinates -> into Voronoi / Brick. (s08)
5. **Cracks:** Voronoi Distance to Edge, Scale 5-14 -> Math Less Than 0.012-0.1. (p15)
6. **Rivets:** Voronoi F1, Randomness 0, Scale 5 -> Less Than 0.09. (z01 metal)
7. **Stones:** Voronoi F1 + Distance to Edge (gaps) + cell Color red -> Color Ramp Constant + dice roll. (z01 gravel)
8. **Brick layout that matches the reference:** Brick Scale 1.7, Width 0.5, Height 0.14, Offset 0.5. Slate: Scale 1.0, Width 0.17, Height 0.125. (z01)
9. **Brick that tiles with per-brick random and local coordinates:** section 8.1. (r01)
10. **Height from colour:** Gamma 0.4545 -> RGB to BW. (section 8.8)
11. **Bump for relief:** Strength 1, Distance 0.03 (not the default 0.001), Filter Width 1-4 for hard steps. (e01, e02, e04)
12. **Normal map convention:** OpenGL for Blender; DirectX uploads need Convention DirectX or a green flip. (e05)
13. **Edge wear mask:** Bevel (Radius 0.01-0.08, Cycles) -> 1 - dot(bevel normal, true normal) x 12, clamp. (e11)
14. **Puddles:** Map Range (From low -> From high reversed) as puddle mask; darken, rough 0.9 -> 0.02, flat bed with Maximum(height, level), IOR 1.33, blue-grey colour. (m02)
15. **Real silhouette:** Displacement node + Material Displacement "Displacement Only/Both" + fine subdivision. (e10)
16. **Layouts that tile for free:** Checker or Brick mortar with whole counts; use `tileable_*` groups for noise and cells.

---

## 15. Tested here: what I ran and what happened (failures included)

Environment: Blender 5.2.2 LTS (build of 2026-09-15), command line, `-b --disable-autoexec -t 2`, CPU Cycles, 160-288 px renders; exact numbers read from 32-bit EXR renders.

| What I ran | Result |
|---|---|
| `introspect_nodes.py` | 99 shader node types created; settings, enum options, sockets, defaults saved (`nodes_shader.json`, `nodes_summary.txt`). `list_addable_nodes.py`: 118 types addable in a shader tree, 360 in a Geometry Nodes tree. |
| `t01`, `t01b` noise numbers | Normalize/range/Detail/Offset/dimension facts in sections 2 and 5.2. **Failure 1:** my first "exact point" tests all returned one value because a typed Vector is ignored; redone with Combine XYZ. |
| `t10` wrap test | **Failure 2:** my first measure (edge-jump ratio) wrongly rated a perfect Checker as a bad seam (22.7) and my first shifted version gave all zeros because the re-link silently failed. Final version builds each pattern from a shifted coordinate source: Noise/Voronoi/Gabor/Magic do not repeat; Checker and whole-count Brick mortar do. |
| `t02`, `t03` picture strips | 24 pattern pictures and 12 shaper pictures. **Failures:** KeyError on switched-off sockets (Noise W, Mapping Location, Mix `A_Color`, Voronoi Detail); labels clipped; a Map Range "Clamp OFF" tile looked the same as the clamped one (after clipping to 0..1 they differ by only 0.049), so I replaced it with a Stepped 8 tile and measured Clamp with numbers instead. |
| `t04`, `t04b` lit pictures | Bump, Normal Map, Displacement, Bevel, AO, Pointiness, Fresnel, Layer Weight, Wireframe. Bump vs Normal Map correlation 0.85 (OpenGL) and -0.02 (DirectX). **Failure:** nothing. One surprise: Bump Only shows no silhouette edge-on. |
| `t05` Principled and puddles | 30 sphere renders, 6 puddle stage renders. First framing washed out; reframed. |
| `t06`, `t09` small checks | use_nodes warning text, Float Curve extrapolation, Brick values (32 distinct), Voronoi Normalize ranges, Gabor 2D/3D, Shader to RGB white in Cycles, Mapping type numbers, Noise Color correlations, White Noise range, typed colour to saved value. |
| `t07` Geometry Nodes | Noise default Vector = Position (diff 0.0); displaced grid; stored attribute read by a material. **Failure 1:** black renders (no material on Geometry Nodes output). **Failure 2:** sun pointed up (wrong direction vector); fixed. |
| `t11` home-made brick | 48 distinct per-brick values, exactly periodic, finished picture periodic (0.0). |
| `mini_recipes` | Six recipes baked at 1254 and scored; 2 bakes failed first (KeyError on Voronoi Detail for N-Sphere), fixed and rerun. |

## 16. NOT TESTED (said plainly)

Vector Displacement; Raycast; Metallic BSDF and F82 tint; Principled Sheen, Anisotropy, Transmission, Thin Wall, Thin Film; Subsurface method differences; Sky Texture; volume nodes; Light Path; RGB Curves and Clamp and Vector Rotate visually; Wave Phase Offset; Magic as a warp field; the Musgrave to Noise conversion formula (needs an old Blender); Voronoi look before 5.0; Geometry Nodes version of Noise Normalize; adaptive subdivision and "Experimental" Cycles features; everything in EEVEE (no graphics card here); Pointiness / Bevel / AO behaviour in EEVEE; Mix Factor with Vector non-uniform mode; Repeat zones, Closures, Bundles and Menu Switch inside shaders.

---

## Sources (what I actually used)

| Title | URL | Date | What it gave |
|---|---|---|---|
| Blender 5.0: Rendering (release notes) | https://developer.blender.org/docs/release_notes/5.0/rendering/ | Blender 5.0, Nov 2025 (page itself undated) | Radial Tiling, Voronoi new hash, repeat zones/closures/bundles/menu switch in shaders, "Use Nodes" removed, Point Density removed |
| Blender 4.0: Shading & Texturing (release notes) | https://developer.blender.org/docs/release_notes/4.0/shading/ (also wiki.blender.org/release_notes/4.0/shading/) | Blender 4.0, Nov 2023 | Principled BSDF rewrite, Noise Normalize + Lacunarity, Voronoi Detail/Roughness/Lacunarity/Normalize, Sheen BSDF, Normal Map strength fix |
| Blender 4.1: Rendering (release notes) | https://developer.blender.org/docs/release_notes/4.1/rendering/ | Blender 4.1, 2024 | Musgrave merged into Noise; Roughness = Lacunarity^-Dimension; Detail - 1 |
| Blender 4.3: Rendering (release notes) | https://developer.blender.org/docs/release_notes/4.3/rendering/ | Blender 4.3, Nov 2024 | Gabor Noise texture, Metallic BSDF |
| Blender 4.5: Rendering (release notes) | https://developer.blender.org/docs/release_notes/4.5/rendering/ | Blender 4.5, 2025 | Default Bump distance 1 mm and Displacement scale 1 cm; Volume Coefficients |
| Blender 5.1 rendering release notes | https://developer.blender.org/docs/release_notes/5.1/rendering/ | Blender 5.1, early 2026 (page undated) | Raycast node, Normal Map OpenGL/DirectX convention, Vector Math rounding |
| Blender 5.2 rendering release notes; 5.2 index | https://developer.blender.org/docs/release_notes/5.2/rendering/ and https://developer.blender.org/docs/release_notes/5.2/ | Blender 5.2 LTS released 14 July 2026 | Time node, Principled Thin Wall, subsurface radius change |
| Blender Manual (bundled with the Blender tool server, read through `search_manual_docs` and the files) | local: `blender-mcp/src/mcp/blmcp/data/manual/render/shader_nodes/...` | newer than 5.2.2 (has pages for nodes 5.2.2 lacks) | Node descriptions: Noise, Voronoi, Brick, Gabor, Gradient, Magic, Wave, White Noise, Radial Tiling, Color Ramp, Map Range, Clamp, Mix, Bump, Displacement, Normal Map, Bevel, AO, Wireframe, Geometry, Layer Weight, Fresnel, Raycast, Principled, material displacement settings |
| Blender Python API reference (bundled, `get_python_api_docs`) | bpy.types.ColorRamp, CurveMapping, Material.displacement_method, ShaderNodeTexWave | for 5.2 | Color ramp modes, curve mapping API, displacement method values, Wave TRI profile |
| How to match Voronoi/procedural textures in Blender 5.0+ to previous versions (forum) | https://blenderartists.org/t/how-to-match-voronoi-procedural-textures-in-blender-5-0-to-previous-versions/1652058 | 3-4 Sept 2026 | users confirm the 5.0 Voronoi change permanently changes seed and values; no known way to restore |
| Making a procedural rusted metal material (BlenderNation Bazaar, JSAbbott) | https://bazaar.blendernation.com/listing/making-a-procedural-rusted-metal-material/ | 24 Feb 2024, Blender 4.0 | Rust chain: Noise Scale 3 / Detail 12 -> Color Ramp -> Bump (0.3 and 0.15), Mix Screen of two ramps, Metallic 1; Object coordinates |
| PlanetSet docs: Procedural Basics (canyons) | https://planetset-docs.readthedocs.io/en/latest/tutorials/canyons/ | undated | domain warping with Vector Math (noise colour - 0.5, scale, add to position) |
| Cycles puddle material shader (BlenderArtists) | https://blenderartists.org/t/cycles-puddle-material-shader-now-with-example/544715 | June 2012 | classic Diffuse + Glossy Mix Shader by a puddle mask; mask also lowers bump (concept only) |
| How to set up an Edge Wear node in Blender (BlenderNation, via Mark B. Tomlinson) | https://www.blendernation.com/2023/08/02/how-to-set-up-a-edge-wear-node-in-blender/ | 2 Aug 2023 | Bevel-based edge mask wrapped in a group with driven Samples (graph image not readable) |
| Better Edge and Cavity Masking with Cycles (BlenderNation) | https://www.blendernation.com/2019/02/10/better-edge-and-cavity-masking-with-cycles/ | 10 Feb 2019 (Blender 2.80 era) | Bevel node + AO node for edge and cavity masks (steps not shown on the page) |
| the Pointiness value, dissected (BlenderArtists) | https://blenderartists.org/t/the-pointiness-value-dissected/674328 | Aug 2016, comments to Apr 2022 | Pointiness = angle between faces at edges; depends on mesh density; flat = 0.5 |

Seen only in search summaries (not opened or not readable): Blender 3.4 release notes (Mix node) https://wiki.blender.org/release_notes/3.4/ and thread "Noticed there's now 3 mix nodes" https://blenderartists.org/t/noticed-theres-now-3-mix-nodes-now-in-blender-3-4/1427622 (late 2022); Postshade Puddle FX docs https://www.blendermarket.com/products/postshade---puddle-fx/docs (403 on fetch; product page summary only); Inigo Quilez "warp" https://iquilezles.org/articles/warp (concept of f(p + h(p))); devtalk "Merging the Musgrave Texture and Noise Texture nodes" https://devtalk.blender.org/t/merging-the-musgrave-texture-and-noise-texture-nodes/30646; BlenderNation "How to Create a Hand Painted Look in Blender" https://www.blendernation.com/2025/10/26/how-to-create-a-hand-painted-look-in-blender/ (26 Oct 2025, not read); Blender Artists "NPR Skin Shader Showcase + Breakdown" and Superhive "Oil Paint Style Shader" (both use Voronoi + Color Ramp and, for the shader, Shader to RGB, which works only in EEVEE).

---

## Files

All in `experiments_shader_node_toolbox/` (see its `README.txt`): `introspect_nodes.py`, `nodes_summary.txt`, `nodes_shader.json`, `nodes_geometry.json`, `addable_nodes.txt`, measurement scripts `t01*.py`, `t03b`, `t06`, `t07`, `t09`, `t10`, `t11` and their `.json` results, picture scripts `t02`, `t03`, `t04`, `t04b`, `t05`, helpers `probe_tools.py` and `sweeps.py`, `pictures/` (55 pictures), `mini_recipes/` (six toolbox-only recipes with scores and sheets).
