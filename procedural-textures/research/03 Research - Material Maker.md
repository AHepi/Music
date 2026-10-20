# 03 Research - Material Maker

Written 19 October 2026. Everything marked "ran" was run on this machine (Linux, 4 processor cores, no graphics card, Blender 5.2.2).
Everything marked "not tested" was not run, and I say so where it matters.

## In one sentence

Material Maker is a free program (a separate program, not a Blender add-on) in which you build a picture by joining boxes ("nodes") into a
network ("graph"), and which then saves the finished pictures ("maps": colour, normal, height, roughness and so on) as image files.

## Short answer for the person who asked ("do these help?" - this guide covers only Material Maker)

**Verdict: borrow ideas from it. Do not make it part of the job.**

* It is real, free, and its licence is what the chat said (MIT). I downloaded it, got it running on this machine with no graphics card, and
  made brick maps with it from a script. So the claim "can run locally without a subscription" is true.
* It did **not** get closer to the brick reference than the Blender nodes did. My best Material Maker brick scored 0.28 on texture_compare
  (the early Blender node attempts scored about 0.41), and it did not reach any dot-for-dot tier on pixel_compare. I spent about six rounds
  on it, far less than was spent on the Blender recipes, so this is "not better in a few hours", not "can never be better".
* One thing worked well and is worth copying: **a short written description of the bricks (52 bricks, 5 KB) could be put inside a
  Material Maker "Custom Shader" node, and the program then drew those exact bricks.** That brought the colour error down from 23 to 11.6 (scale
  where lower is better) and the picture similarity up from 0.40 to 0.52. The same idea works in Blender (a script reads the description).
* Its shader code is open and readable under the MIT licence, so we can copy its **methods** (seamless noise, the "tiler" that scatters
  copies of a shape, the painted-look filter, normal-from-height) and re-create them as Blender node groups.
* It is not a modelling tool at all. It makes flat pictures only.

## What Material Maker is (plain)

* A program for making textures. You draw a graph of boxes: a "Bricks" box draws a brick pattern, a "Colorize" box turns grey into colours,
  a "Blend" box lays one picture over another, a "Material" box at the end collects the finished maps.
* It is built on the Godot game engine (the downloaded program reports Godot 4.7). Each box is a few lines of shader code (the small program a
  graphics chip runs once for every dot of the picture); Material Maker joins the boxes' code into one big shader instead of making a picture
  for every box.
* The graph is saved as a plain text file ending in `.ptex` (it is JSON, so a script can write it).
* Author: Rodolphe Suescun (RodZill4) and contributors. Licence: MIT for the code (copyright line "2018-present Rodolphe Suescun and
  contributors"); the itch.io page also states "Creative Commons Zero" for the assets.
* Latest version I could find: **1.7**, uploaded 14 July 2026 (the previous one, 1.6, on 18 April 2026). The first release on Steam.
* GitHub shows about 6,000 stars and 388 forks (read from the repository page today). The code on the main branch differs from the 1.7
  release, so work continues after 1.7. I could not read GitHub's own releases page (the proxy blocks github.com pages: error 403), so the date
  comes from itch.io (upload time 14 July 2026, 07:35 UTC) and two news sites (14 and 15 July 2026).
* Blender versions: not applicable, because it is not an add-on. It talks to Blender only through image files.

## Do the chat's statements hold up?

| What the chat said | Verdict | Plain note |
|---|---|---|
| "Material Maker is excellent for procedural textures, including wear, damage, surface variation and PBR map generation." | Partly true; "excellent" is an opinion | About 320 ready-made boxes (patterns, noises, filters, dirt, scratches, crystal, edge wear helpers). It writes 8 kinds of PBR map. In my brick test it was not better than the Blender nodes. |
| "It has an MIT licence." | True | Read `LICENSE.md` in the repository and the itch.io page. |
| "Can run locally without a subscription." | True | Free download ("name your own price", minimum 0). No account was needed. I ran it. |
| (task text) "Ucupaint ... replacement for Mixar's texture-layer editor" | Not my tool to check | I know of no texture-layer editor called "Mixar"; it is probably a slip for another name (perhaps Quixel Mixer). Not verified. |
| (task text) "Material Maker for Blender" add-on | Not found | The program's own manual says the Blender export "will only generate PNG/EXR images" and suggests Blender's Node Wrangler add-on to hook them up. No Blender add-on from the author turned up in my searches. |

## What I ran here (and what happened, failures included)

1. **Download.** From the official itch.io page I took the Linux build `material_maker_1_7_linux.tar.gz`
   (99,030,904 bytes, 94 MB; SHA-256 `c8e3b6f1993540875d26fe49645c91511bba36cda0412c715bd13249f7141647`). The page offers it as "name your own
   price" with a "No thanks, just take me to the downloads" link; I used the zero-price route. It is one program file (121 MB) plus loose
   folders: `nodes/` (419 node files), `library/` (the node list), `examples/` (44 sample graphs), `doc/` (the manual), `export/`.
   Total download for the whole job was about 120 MB (the program 99 MB, plus 17.5 MB of software graphics driver, below).
2. **Reading its code before running.** The program's scripts are compiled into the program file, so I read the matching source from the
   project's public tag "1.7" (single files from raw.githubusercontent.com): how the command line works (`parse_args.gd`), how a Material box
   exports (`gen_material.gd`), and the node files in the download (they are plain JSON with the shader code inside). The network uses I found are
   a feature in the command-line code that fetches materials from the project's website when you give a name that starts `website:`, and
   window features whose script names say "share", "upload", "load from website" and "language download" (I read only the first; I used none of
   them). I removed the proxy setting for every run so the program could not reach the internet anyway.
3. **First start: crash.** With no graphics card the program says "Vulkan not found, switching to OpenGL 3" and then **crashes** (segmentation
   fault). Its shader engine needs Vulkan.
4. **Fix: a software Vulkan driver.** Ubuntu's package `mesa-vulkan-drivers` (version 25.2.8, same as the Mesa already installed, 17.5 MB, hash
   checked against the Ubuntu package list) contains "lavapipe", a Vulkan driver that runs on the processor. I unpacked it into my own folder
   (not installed on the system) and pointed the program at it. With a virtual screen (Xvfb, already on the machine) the program then ran and
   named the device "llvmpipe, CPU".
5. **Command line.** The manual says: `material_maker --export-material --target <engine> -o <folder> <files>` where the engine can be Blender,
   Godot, Unity or Unreal. It works. Details and traps are in "Quirks" below.
6. **Wrote graphs from a script** (`tools/ptex_builder.py`), exported them, and brought the maps into Blender (headless, a flat square with an
   ordinary Principled material) to check they load and look right (they do; picture below in the files list).

Time per export on this shared machine: about 40 seconds for 5 maps of 2048 x 2048 from a 30-node graph (3 s start-up, about 6 s waiting for the
files to settle, the rest drawing; a simple 5-box graph took about 12 s). A full try with scoring took about 90 s.

## The brick experiment (analyse, describe, generate, compare)

Goal: reproduce `reference/brick` (1254 x 1254) as closely as possible, then see what the scores say.

### Concrete example first: what a graph file is

This whole graph, three boxes and two wires, is the file (shortened):

```
{ "type": "graph", "nodes": [
    {"name": "Bricks",   "type": "bricks3",  "parameters": {"rows": 12, "columns": 4, "mortar": 0.19, "bevel": 0.04}},
    {"name": "Col",      "type": "colorize", "parameters": {"gradient": {"points": [ {"pos": 0, "r": 0.3, "g": 0.2, "b": 0.17}, {"pos": 1, "r": 0.74, "g": 0.38, "b": 0.23} ]}}},
    {"name": "Material", "type": "material", "parameters": {"size": 11}} ],
  "connections": [ {"from": "Bricks", "from_port": 0, "to": "Col", "to_port": 0},
                   {"from": "Col",    "from_port": 0, "to": "Material", "to_port": 0} ] }
```

The "type" is the name of a file in the program's `nodes/` folder. Port numbers of the Material box (the same box in every graph): 0 colour,
1 metallic, 2 roughness, 3 emission (glow), 4 normal, 5 occlusion (ambient shading), 6 height ("depth"), 7 opacity, 8 subsurface. Only maps
that are wired in get written. With `--target Blender` the files are:

| Port | File | Format |
|---|---|---|
| 0 colour | `NAME_albedo.png` | PNG, 2048 x 2048, has an alpha channel |
| 2 roughness | `NAME_rough.exr` | EXR (float) |
| 1 metallic | `NAME_metal.exr` | EXR |
| 4 normal | `NAME_normal.png` | PNG; I checked it points the OpenGL way (green = up), the way Blender wants it |
| 6 height | `NAME_displace.exr` | EXR, **upside down: the file holds 1 minus the height** (bricks come out dark). I measured this by comparing slopes. |
| 5 occlusion | `NAME_occlusion.exr` | EXR |
| 3 emission / 8 subsurface | `_emission.png` / `_sss.exr` | not used here |

Python's OpenCV here cannot read EXR, so I read them inside Blender (its bundled OpenImageIO) and turned them into 16-bit PNG.

### Two kinds of graph

**A. "Stock" graph: only boxes from the program's own library** (33 boxes, 15 KB file). Bricks box (12 rows, 4 across, thick mortar), a
"Fill to random grey" box (one random grey per brick, turned into red/orange/dark colours), value noise for blotches, stretched noise for sooty
streaks, a threshold on another noise for pale chips, a mortar colour with noise, a dark outline made from two Bricks boxes, then a
**generalised Kuwahara filter** (it turns noise into flat painted patches) on the whole colour; the height is the brightness of that colour and
the normal map comes from that height (this is how the reference maps were made too: height follows the colour, correlation 0.97).

**B. "Fitted" graph: the layout comes from a written description** (`analysis/fit3/brick_layout.json`, **52 bricks, 5.2 KB, 423 numbers**,
which the audit tool puts at 0.11 percent of the size of the reference picture). I measured it from the reference: the mortar is the
grey-brown, weakly coloured part; horizontal mortar lines are peaks in the row profile (12 rows), and the up-and-down joints in each row are
peaks in the column profile. For each brick: left, top, right, bottom, and its average colour. The description goes into **one Custom Shader
box** (type "shader") as constant arrays of rectangles and colours, with a few lines of shader code that find the nearest brick (checking the
tile's eight neighbours so bricks wrap round the edges). Its three outputs are: distance inside the brick, the brick's fitted colour, and a
random grey per brick. The rest of the graph is stock boxes as in A.

The shader wrote the layout correctly on the first try. Result picture: `runs/results_sheet_brick.png` (reference, stock graph, fitted layout, fitted
layout with wear) and `runs/results_sheet_brick_normals.png`.

### Scores (all against `reference/brick`, maps shrunk from 2048 to 1254 by area averaging)

How to read the columns: **texture_compare overall** 0 to 1, "is it the same kind of surface?" (a shuffled copy of the reference itself scores about
0.99, a blurred copy 0.17, another surface about 0.1). **Colour SSIM** 0 to 1, same structure dot for dot (higher is better). **Colour
error (dE)** average colour difference (lower is better; under 20 is needed for the "layout" tier). **Edge skill** 0 to 1, how many edges sit
within 2 dots of a reference edge, with luck subtracted (needs 0.30 for "layout"). **Height error** in 8-bit steps after the best brightness fix (needs 40 or less).
**Normal angle** average degrees between normals.

| Picture set | texture_compare | colour SSIM | colour dE | edge skill | height error | normal angle | tier |
|---|---|---|---|---|---|---|---|
| Stock graph, first try (round 1) | 0.139 | 0.31 | 28.4 | 0.000 | 40.0 | 28.5 | none |
| Stock, round 2 (thicker mortar, painted look, height from colour) | 0.220 | 0.34 | 26.2 | 0.002 | 39.9 | 29.4 | none |
| Stock, round 3 | 0.194 | 0.34 | 25.7 | 0.004 | 39.9 | 30.6 | none |
| Stock, round 4 (softer soot, lighter outline) | 0.272 | 0.39 | 23.4 | 0.003 | 39.9 | 26.3 | none |
| **Stock, round 5, three seeds (final)** | **0.279 / 0.279 / 0.269** | 0.40 | 22.9 to 23.4 | 0.00 to 0.01 | 39.9 | 26.1 to 26.6 | none |
| **Fitted: layout + brick colours only** | 0.223 | **0.52** | **11.6** | **0.251** | 38.3 | **23.3** | none (edge skill 0.251 is under 0.30) |
| Fitted + blotches + chips | **0.255** | 0.49 | 12.9 | 0.235 | 38.7 | 26.2 | none |
| Fitted + big soot patches too | 0.135 | 0.46 | 16.7 | 0.206 | 39.4 | 28.5 | none |

What this says, in plain words:

* Putting the real brick positions in (the 5 KB description) made the picture **much closer dot for dot** (colour error halved, edge skill
  from about 0 to 0.25) but it did **not** make it look more like "the same kind of surface" (texture_compare stayed around 0.22 to 0.26): a smooth
  fitted brick has none of the fine painted patches, and that is what texture_compare measures. Adding soot made both scores worse, because the
  fitted average colour of each brick already contains its soot, so I was counting it twice.
* Neither kind reached the "layout" tier. Fitted layout + colours misses it by one measure (edge skill 0.251 against 0.30).
* The height error stays at 38 to 40 for everything. The reference's height has fine detail (it follows every painted patch) that none of my graphs
  had.
* **Seamless:** my exports tile. At 2048, left-right / top-bottom jump ratios were 0.07 / 0.04 for the stock colour, 0.46 / 0.28 for its normal map,
  0.08 / 0.04 for its height and 0.49 / 0.00 for the fitted colour (1.0 or less = no visible seam). The reference itself measures 1.6 / 3.2 (colour), so
  a fitted description gives a seamless wall even though the reference is not.
* **Variants:** three seeds of the stock graph gave three different walls (average colour difference between them 17.5, 19.2 and 21.5 out of 255;
  between the reference and one of them 30.4), all scoring alike. The seed of each box is stored as `"seed"` in the file; the layout (rows, bricks per
  row) did not change between seeds, only the noise did.
* **What I tried that did not work:** (a) a first stock graph looked wrong because I wrote the settings of the Blend box as `amount` and
  `blend_type`; the real names are `amount1` and `blend_type1`, and **a wrong name is silently ignored** (the box just used its defaults); (b) I first
  stored seeds under `seed_int`, which is also silently ignored (three "different" seeds came out identical) - the file key is `seed`; (c) I tried to
  improve the fitted layout by moving each brick edge to the place that best covers the brick area; the overlap score rose from 0.87 to 0.91 but the
  picture got **worse** (bricks swelled over the mortar and almost touched), because the score counts the union of all bricks. I dropped it and used
  the first fit. All three are recorded so nobody repeats them.

## Quirks and limits found by testing (the part that decides "can we use it headless")

1. **It needs Vulkan.** Without a graphics card it crashes at start-up. A software driver fixes it (above), which makes it slow-ish but fine.
2. **Output size is fixed at 2048 x 2048 on the command line.** The `--size` option is read but never used (checked in the source of 1.7 and of the main
   branch, and by running `--size 1254`: still 2048). Inside the program, sizes are powers of two from 16 to 8192. So **1254 px is never produced
   natively**; I shrank 2048 to 1254 (area averaging). Because the graph does not depend on resolution, this is a faithful shrink, but it is a shrink.
3. **It does not quit by itself** after a command-line export; it sits idle forever (and also if the output folder does not exist). My script waits
   until the expected files exist and have stopped changing, then ends the program.
4. **`-t` does not work as the target option** (Godot itself uses `-t` for "always on top"). Use `--target Blender`. With `-t` the program silently
   picked a Godot export (different file names, an extra `.tres` file) and it cost me several confusing runs.
5. **It crashed at start-up now and then** (a "segmentation fault" before drawing anything). I counted 1 in 5 launches in some stretches and 0 of 14
   in another; a restart always fixed it (never more than 3 restarts in a row). I did not find the cause. The script restarts it up to 4 times.
6. **The output folder must already exist, and a relative path did not work for me.** The program starts in its own folder (its log prints it as
   "Current dir"), so a relative output path pointed at a folder that did not exist; the program then stopped working without saying anything useful
   and had to be killed. Use full paths.
7. A graph that wired a pattern box straight into the Material's height port crashed at start-up 3 times out of 3 in my early tests; routing it
   through a Colorize box worked. I cannot say whether that was the cause or a coincidence with quirk 5.
8. **Wrong setting names are silently ignored** (see above). My builder checks every name against the node's definition file and warns.
9. The "Blender" export writes the height upside down (see the table).
10. There is no scripting interface other than the graph file and the command line (no Python API). Nothing can be done to a running program.

## The node library (what is in the box), and how to think about it

The library list (`notes/node_library_list.tsv`, about 320 entries; the manual says "about 250"):

* **Pattern (26):** Bricks (running bond, English, Flemish, herringbone, basket weave, Spanish bond), Uneven Bricks 1 to 3, Skewed Bricks, Cairo,
  Custom Tiles, Weave, Random Weave, Truchet, Diagonal Weave, Beehive, Sine Wave, Arc Pavement, Scratches, Fibers, Runes, Mesh.
* **Noise (17):** Value noise, Fractional Brownian motion (13 kinds incl. Perlin, Simplex, Cellular, Voronoise, Gabor), Voronoi, Triangle Voronoi,
  Anisotropic (stretched) noise, Wavelet, Shard, White, Colour noise; composites Dirt, Crystal, Directional Noise, Clouds.
* **Transform (32):** Tiler (and Advanced), Splatter, Circle Splatter, Warp, Directional Warp, Multi Warp, Warp Dilation, Swirl, Spherize, Distort,
  Circle Map, Kaleidoscope, Mirror, Shear, Custom UV, Slope, Morphology.
* **Filter (71):** Colorize (gradient), Blend (23 modes), Adjust HSV, Tones, Normal Map (4 methods), Normal to Height, Blur (Gaussian,
  **Directional**, Slope, Fast), Edge Detect (3 kinds), Emboss, Occlusion, HBAO, Bevel, Dilate, Fill family (From Colours, To Random Grey / Colour,
  To Position, To Size, To Gradient, To Orientation), **Kuwahara (classic, anisotropic, generalised) and Symmetric Nearest Neighbour** (painted
  looks), Quantize, Palettize, Pixelize, Make Tileable, Denoiser, Colormap, Smooth Curvature.
* **Workflow (13):** map mixing for layered materials, plus ready materials Marble, Metal, Wood.
* **Miscellaneous (30):** Buffer, Iterate Buffer, **Custom Shader**, Switch, Remote (one slider driving many), Export, Variations (random per
  instance), Mesh Map (bakes curvature and similar from a model).
* **Simple (70) and 3D (62):** shapes, gradients, curves, text, and distance-field shapes for building raymarched (ray-traced in the shader) scenes.
  These make pictures, not meshes.

About the claims "wear, damage": it has Dirt, Scratches, Mesh Map and edge-style filters, but nothing that reads a mesh in the way Substance's smart
materials do inside the command-line export, and I did not test Mesh Map.

## How its key nodes are built (so we can re-create them as Blender node groups)

All of this is real code read from the download or from the 1.7 source; it is MIT-licensed, so methods may be ported if the copyright notice is kept.

* **Random numbers:** `rand(x) = fract(cos(mod(dot(x, (13.9898, 8.141)), 3.14)) * 43758.5453)`. Every random thing (per brick, per instance) is this
  hash of a position plus the box's seed.
* **Seamless value noise (the "Value Noise" box):** for each octave, take the integer cell `floor(uv*size)`, hash its four corners using
  `mod(cell, size)` (the wrap that makes it tile), blend with smoothstep, add the next octave at double `size` and weight `persistence`; divide by
  the total weight. Blender's own Noise texture is not seamless; this is a different, simple way to get a seamless one (a hash of wrapped integer
  cells), alongside the helper already in `lib/recipe_tools.py`.
* **Voronoi box:** Inigo Quilez's two-pass version: nearest point from 3 x 3 cells, then a second pass over 5 x 5 cells for the distance to the border;
  cell positions wrap with `mod(n + g + size, size)`. Outputs: cell value, border distance, and a "Fill" id.
* **Bricks box:** a pattern function returns each brick's rectangle (running bond: shift every other row by `offset`; herringbone, basket weave,
  Spanish bond are small tables of rectangles); a rounded-box distance gives the picture: `d = length(max(abs(p) - half + r, 0)) + min(max(q.x, q.y), 0) - r`,
  `value = clamp(-d / bevel, 0, 1)`, with mortar width and bevel scaled by row height. A second output is a "Fill" (rectangle) that the Fill
  companion boxes turn into random grey, random colour, position, size.
* **Tiler box (also Splatter):** divide the picture into `tx x ty` cells; for each pixel loop over the neighbouring cells (`overlap`), give each cell a random
  offset, rotation, scale and brightness from the hash, test if the pixel falls inside that instance of the input picture, keep the brightest (`max`).
  Extra outputs: a random colour per instance and each instance's own UV. This is the method behind stones, shingles, chips, leaves.
* **Normal Map box:** Sobel on the (grey) height with four methods; the classic one is the 8-neighbour Sobel scaled by `size * amount / 128`, and
  the normal is `0.5 + 0.5 * normalize(vec3(dx, dy, -1))`.
* **Edge Detect:** 8-neighbour Laplacian: `abs(8*centre - sum of the 8 neighbours) * size`.
* **Directional Blur:** a one-direction Gaussian: up to 50 steps along the angle, weights `exp(-0.5 * (i/sigma)^2)`, with sigma optionally controlled by a map.
* **Warp:** moves each pixel along the slope of a second picture (slope = difference of the height picture either side, `eps` apart); Directional Warp
  moves by an angle map and strength.
* **Colorize:** a piecewise-linear colour ramp with constant ends (like Blender's Color Ramp set to Linear); other modes: constant, smoothstep, cubic.
* **Blend:** each mode is a one-line formula, for example Normal `opacity*top + (1-opacity)*bottom`, Multiply `opacity*top*bottom + (1-opacity)*bottom`,
  Overlay and Soft Light as in Photoshop, Difference `clamp(bottom - top)`, Additive `bottom + top*opacity`. The input called "b" is the background, "l" the layer,
  "a" a mask for the layer.
* **Generalised Kuwahara (the painted look):** for each pixel, look at a square of radius `size`; split it into 8 overlapping wedge-shaped sectors
  with smooth weights; find each sector's average colour and its spread; the output is the sectors' averages weighted by `1 / (1 + (1000*spread)^(Q/2))`
  with Q = 18, so flat sectors win and edges stay sharp. Noise becomes flat painted patches with crisp borders. (Blender's compositor also has a
  Kuwahara node as far as I know; I did not test it.)

## Does it export something Blender can use directly?

* **Yes: image files only** (table above). Open them in Blender as Image Texture nodes: colour as sRGB, the others as Non-Color; the normal map goes
  through a Normal Map node, and Blender's own height (displacement) must be inverted back because of the upside-down file. I did this headless
  and rendered a square (`runs/brick_stock_v5_seed1/out/maps/blender_preview.png`): the maps loaded and the bumps lit correctly.
* **No `.blend` or material file and no Blender add-on** (manual: "will only generate PNG/EXR images ... built manually using the shader editor"). The program
  does write finished materials for Godot (`.tres`) and Unity, and a Python script for Unreal 5, but nothing like that for Blender.
* `.mmpp` is its 3D-painting project format (a model you paint on). Blender cannot read it. Not tested.

## Judged against OUR needs

| Need | Result |
|---|---|
| Pixel-accurate match of a reference from a compact fitted description | Possible only for what is described. The 5 KB brick description in a Custom Shader reproduced the layout (colour error 11.6, edge skill 0.25) but no tier was reached; fine painted detail is not in a layout description and is what the scores mostly see. Nothing here is better than doing the same in Blender with a script that reads the description. |
| Many variants and larger areas | Variants are easy (change seeds and settings; wrote 3 in minutes). Larger areas: the command line gives 2048 x 2048 and no more; for a bigger area you would raise the counts (rows, noise scales) inside that tile. Output is seamless by construction. Sizes above 2048 not tested (they need the program's window). |
| Lessons that transfer to other surfaces | Yes, mostly as methods (list below), not as the program. |
| Headless, scripted, no graphics card | Works, with six workarounds (software Vulkan driver, virtual screen, restart on crash, kill after export, long option name, full paths), about 40 s per export, 2048 only. A normal Blender bake here takes about 20 s at 1254. |
| Modelling (the coal-mine scene was built from scripts) | No help. It makes flat pictures. |

## What we could take into the job

1. **Algorithms to re-create as Blender node groups** (each was read from the real code; none re-created yet): seamless value noise from a hash of
   wrapped integer cells; the Tiler / Splatter instance scatterer with neighbour overlap and per-instance random offset, rotation, scale, brightness, colour and
   own UV (stones, gravel, shingles, chips); the Bricks pattern function with its rounded-box distance and "one id per brick" output; the generalised Kuwahara
   painted-look filter; the Sobel normal-from-height with four methods; the exact Blend formulas; Directional Blur and slope/directional Warp; two-pass Voronoi
   border distance.
2. **Workflow ideas:** (a) a graph file written by a script from a fitted description; (b) the fitted element list (rectangles, colours) carried as
   constant arrays inside one custom shader box, which is the closest thing Material Maker has to our "description" step; (c) derive the height from
   the brightness of the finished colour and the normal from that height, as the reference maps themselves were made (this lifted the "height follows colour" measure from 0
   to 0.77); (d) a per-box seed as the variation knob; (e) never trust a setting name until checked against the node's definition file.
3. **Files to keep:** the node list `notes/node_library_list.tsv`; `tools/ptex_builder.py` (writes graphs, checks names); `tools/mm_export.py`,
   `tools/finish_maps.py`, `tools/evaluate_candidate.sh` (export, convert, score in one command) if anyone wants to repeat this.
4. **Traps to remember:** quirks 1 to 10 above.

## Other free procedural-texture programs I came across (not tested)

| Name | Licence | One line |
|---|---|---|
| TextureLab | GPL (the repository's licence file is the GNU general public licence; the news article says version 3) | Free node-based texture generator, runs in an Electron app (desktop program built from web technology). |
| NodeMangler | not stated on the page I read | Free open-source node-based image editor / procedural texture maker written in Rust. |
| Armor Paint | not checked | Free 3D painting program in the same family as the ArmorPaint/Armory engine; I did not check its licence or whether it is still free. |
| Quixel Mixer | not checked (a free but closed program as far as I know) | Layered texture mixing program; the chat's "Mixar" may mean this. |
| Blender itself (Geometry Nodes, shader nodes, compositor) | GPL | What we already use. |
| Substance 3D Designer | paid | The commercial program all these try to imitate. |

## What I did not test

The program's own window (everything was command line), any size other than 2048, its 3D painting, Mesh Map, the Steam build, Windows and macOS, the
ready-made Marble / Metal / Wood materials, the Tiler / Splatter boxes in use (read only), Make Tileable, the website features, and every surface except brick (so slate, wood, metal, mud and
gravel are not tried; only my reading of how Bricks, Tiler and Voronoi are built suggests which boxes would be the starting point). I also did not test whether the GitHub
repository has newer fixes for the quirks (I could read single files from the main branch but not its commit list).

## Sources

| Title | URL | Date | What it gave |
|---|---|---|---|
| Material Maker (GitHub repository page) | https://github.com/RodZill4/material-maker | read 19 Oct 2026 | Author, MIT, about 6,000 stars and 388 forks, download links, manual link |
| Material Maker licence file | https://raw.githubusercontent.com/RodZill4/material-maker/master/LICENSE.md | read 19 Oct 2026 | "MIT License, Copyright (c) 2018-present Rodolphe Suescun and contributors" |
| Material Maker README | https://raw.githubusercontent.com/RodZill4/material-maker/master/README.md | read 19 Oct 2026 | Download places (itch.io, Steam, package managers), manual link |
| Material Maker by RodZilla (itch.io) | https://rodzilla.itch.io/material-maker | read 19 Oct 2026 | Description, code licence MIT and asset licence CC0, rating 4.9 of 5 (338 ratings), uploads 1.7 on 14 Jul 2026 and 1.6 on 18 Apr 2026, "name your own price", Linux build 94 MB |
| Material Maker 1.7 (CG Channel) | https://www.cgchannel.com/tag/material-maker-1-7/ | 14 Jul 2026 | Release date, "free alternative to Substance 3D Designer", also on Steam |
| Material Maker 1.7 Released (GameFromScratch) | https://gamefromscratch.com/material-maker-1-7-released/ | 15 Jul 2026 | 1.7 feature list, first Steam release |
| Material Maker manual: Command line arguments and Exporting Materials | https://rodzill4.github.io/material-maker/doc/ (the same pages are in the download: `doc/command_line.html`, `doc/export.html`) | version 1.7 | The command line, the Blender export being images only |
| parse_args.gd at tag 1.7 and on the main branch | https://raw.githubusercontent.com/RodZill4/material-maker/refs/tags/1.7/parse_args.gd | read 19 Oct 2026 | Command-line handling; `--size` read but unused |
| gen_material.gd at tag 1.7 | https://raw.githubusercontent.com/RodZill4/material-maker/refs/tags/1.7/addons/material_maker/engine/nodes/gen_material.gd | read 19 Oct 2026 | Export code, size limits 16 to 8192 |
| mesa-vulkan-drivers 25.2.8 (Ubuntu 24.04) | https://archive.ubuntu.com/ubuntu/pool/main/m/mesa/mesa-vulkan-drivers_25.2.8-0ubuntu0.24.04.4_amd64.deb | read 19 Oct 2026 | The "lavapipe" software Vulkan driver that made it run |
| Material Maker comments (itch.io) | https://rodzilla.itch.io/material-maker/comments?after=52 | seen in a search, 19 Oct 2026 | A user asking how to bring exports into Blender and being told to use Node Wrangler (user comments, anecdotal) |
| TextureLab, open-source procedural texture generation (GameFromScratch) | https://gamefromscratch.com/texturelab-open-source-procedural-texture-generation/ | page date not shown | TextureLab is GPLv3, Electron app |
| TextureLab licence file | https://raw.githubusercontent.com/njbrown/texturelab/master/LICENSE | read 19 Oct 2026 | GNU public licence, copyright 2019 Nicolas Brown |
| NodeMangler (itch.io) | https://danp.itch.io/nodemangler | page date not shown | Free open-source node-based image editor in Rust |
| Best free open source alternatives to Substance 3D Designer (LinuxLinks) | https://www.linuxlinks.com/best-free-open-source-alternatives-adobe-substance-3d-designer/ | page date not shown | Context for other free tools |

## Where my files are (all inside `proc-work/third-party/material_maker/`)

* `app/` the program as downloaded; `download/` the original archive; `lavapipe/` the software Vulkan driver; `run_mm.sh` starts the program (virtual screen, fake home folder, no
  internet).
* `tools/` my scripts: `ptex_builder.py` (writes graphs, checks setting names), `mm_export.py` (runs the export with restarts and a stop), `exr_to_png16.py` (runs inside Blender),
  `finish_maps.py` (2048 to 1254, normal convention check, height flip), `evaluate_candidate.sh` (export, convert, both compare tools, sheets),
  `make_brick_stock_graph.py`, `make_brick_fitted_graph.py`, `seam_ratio.py`, `side_by_side.py`, `probe_sheet.py`, `blender_preview.py`.
* `analysis/fit3/brick_layout.json` the fitted brick description (52 bricks, 5.2 KB) and `analysis/fit_brick_layout.py` (how it was measured); `analysis/refine_brick_layout.py` (the refinement that made things
  worse; kept as the recorded dead end).
* `runs/` graph files and results; the pictures to look at are `runs/results_sheet_brick.png`, `runs/results_sheet_brick_normals.png`, `runs/seeds_sheet.png` and
  `runs/brick_stock_v5_seed1/out/maps/blender_preview.png`; scores are in each run's `out/maps/score_*.json`.
* `notes/` node list, node summaries, `show_node.py` (prints any node's settings and code), extracted shader text.
