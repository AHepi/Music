# Procedural textures job - notes for every helper (read first)

## The job (in the person's words)
"Generate all textures, materials and maps using all of Blender's procedural generation tools. Use Blender's MCP and research how people
currently achieve these things. Save recipes and guides for how to use the tools, what they do, and how they change things. See how close
to the references you can make things. Use the reference maps I attached. You may use geometry nodes, curves, modifiers, or anything else."

The person is NOT a programmer. Everything you write for them must be plain everyday language: say what a tool does in one plain sentence
first, show a concrete example before the general rule, use one word for each thing (never swap synonyms), say what you tested and what you
did not, and never say something works unless you ran it. Code: full plain-word names, and a plain note at the top of every file saying what it does.
Files you create: start with a two-digit number, then plain words, e.g. "02 Research - seamless textures and baking.md" (the number is
given in your brief).

## The references (what we are trying to match) - folder: reference/
Six seamless tiles, 1254 x 1254, hand-painted / stylised look (flat painted colour patches, dark outlines, chunky shapes), each with a colour
picture, a normal map and a height ("displacement") map: brick, slate, wood, metal (rusted riveted steel), mud (ruts, stones, blue puddles),
gravel (angular blue-grey/black stones in orange-brown earth); plus mud_golden (colour only; the same mud but with warm sunset puddles).
Files per surface: colour.png, normal.png (OpenGL convention: green points UP the picture; Blender's convention), normal_as_uploaded_directx.png
(the upload; green points down), height.png (16-bit, lightly smoothed), height_as_uploaded.png (8-bit original). Look at them with the Read tool.
The maps in the upload were "derived from the base colour": height tracks the brightness of the colour (correlation 0.96-0.99) and the
normal map is a Sobel-style slope of that height.

## Tools already built (in lib/) - use them, do not rewrite them
* texture_compare.py (plain Python, run with `python3 -I`): scores a generated set against a reference. 
    `python3 -I lib/texture_compare.py brick OUT_FOLDER --json OUT_FOLDER/score.json --sheet OUT_FOLDER/sheet.png`
  OUT_FOLDER holds colour.png, normal.png, height.png. Scores run 0 (as different as a different surface) to 1 (the same by that measure);
  a re-shuffled copy of the reference itself scores about 0.99; a blurred copy about 0.17; another surface about 0.1. The sheet shows
  reference and generated side by side, a 2 x 2 tiling preview and feature-size / brightness curves. ALWAYS look at the sheet with your own
  eyes (Read the png) as well as at the numbers: a good score with an ugly picture is not a win, and a good picture with a poor score tells
  you which measure to chase.
* bake_harness.py (inside Blender): turns a recipe into pictures. A recipe is a Python file defining `build_node_group(parameters)` that returns
  a shader node group with input 'Vector' (the tile coordinate: u and v from 0 to 1) and outputs 'Colour' (colour), 'Roughness', 'Metallic',
  'Height' (0..1). `blender -b --disable-autoexec -t 2 --python lib/bake_harness.py -- RECIPE.py OUT_FOLDER --size 1254 --normal-reference brick`
  writes colour.png, height.png (16-bit), roughness.png, metallic.png, normal.png (Sobel from the height, strength fitted to the reference's
  slope spread), normal_bumpnode.png (the same made with Blender's Bump node) and bake.json. Takes about 20 seconds.
  See tests/recipe_smoke.py for the smallest recipe. For a recipe that builds real geometry (geometry nodes, curves, modifiers, physics),
  bake_harness.new_bake_scene / show_channel_material / render_to / save_array_png are the building blocks for photographing it from straight
  above (orthographic camera over a 1 x 1 square, one emitted channel at a time); write your own bake script in your recipe folder that
  ends by writing the same file names (colour.png, height.png, normal.png, roughness.png, metallic.png) into an output folder.
* recipe_tools.py (inside Blender): NodeWriter (add nodes and links by name), make_group_tree (node groups with named inputs/outputs),
  tileable_noise_group() and tileable_voronoi_group() = SEAMLESS noise and cells (Blender's own noise is NOT seamless; these sample 4D noise on a
  donut shape so the left edge continues into the right edge). Verify any new tiling trick with the seam measure: seam_ratio about 1.0 = seamless.
* sweep_tools.py + make_strip.py: render "what does this setting do" strips (see their notes at the top). Use them for the guides.

## Blender here
Blender 5.2.2 at /home/user/work/blender-app/blender-5.2.2-linux-x64/blender (headless; use `-b --disable-autoexec -t 2`; CPU Cycles only).
Blender's own tool server (MCP) is available: tools mcp__blender__* (search_manual_docs, search_api_docs, get_python_api_docs, execute_blender_code_for_cli with
proc-work/empty.blend, and execute_blender_code on the shared live server at 127.0.0.1:9876). The live server is ONE shared Blender session used by
several helpers at once: only touch datablocks whose names start with your own prefix, and prefer the *_for_cli tools or plain command-line Blender
for anything that changes state. Python in Blender has numpy and OpenImageIO but no PIL/cv2/scipy; the system python3 (use `python3 -I`) has numpy, PIL
and cv2. Web: WebSearch and WebFetch work. Blender 5.x notes: material.use_nodes still works (deprecation warning only); Musgrave is merged into
Noise Texture (noise_type); Noise and Voronoi have 1D-4D; there is a Gabor texture; Cycles only here (no GPU, EEVEE needs a graphics card).

## House rules
* Plain Blender only. Do NOT use the explainer-film plugin, the Astra add-on, anything in /home/user/Music/plugins or /home/user/Music/austerity-explainer.
  Do not touch git. Do not use any image texture of the references INSIDE a recipe (recipes must be fully procedural: nodes, geometry, curves,
  modifiers, simulation; pictures may only be used for analysing the references, never as an input to the generated textures).
* Only create files inside your own folder (given in your brief). Never edit lib/ or reference/. If you need a change in lib/, say so in your final answer.
* CPU is shared by several helpers: keep renders at -t 2, keep tests small (256-512 px) while exploring and use 1254 only for the real bakes.
* Be honest: record failures and dead ends too; they are part of the guide.


---
## REVISED SUCCESS DEFINITION (the person's clarification, after the first notes were written)
"The point is textures that can be scaled to larger sets with lessons that are transferable to other types of surfaces. Pixel accuracy isn't the end goal,
but it is required for this first step."

So the first step is: for each reference surface, a procedural recipe that can reproduce THAT reference picture, maps and all, dot for dot (as closely as
it can be made to), as proof that the method can say everything the reference says. The end goal is a METHOD: a recipe that, driven by a different
description, makes unlimited new, different, equally good tiles and larger areas, and a set of lessons (written down so they work on surfaces we have
NOT been given) about which tool does what and which layer of a recipe buys how much accuracy.

### The method: Analyse -> Describe -> Generate -> Compare (each surface)
1. ANALYSE (plain Python, `python3 -I`, numpy/cv2/PIL): look at the reference and find its structure: the layout grid, every element (brick, slate, plank,
   plate, rivet, stone, puddle, rut) with position, size, shape, rotation and colour, the colour palette, the outline darkness and width, the wear/blotch
   layers, the noise character. Pictures may be used for ANALYSIS only.
2. DESCRIBE: write a compact `description.json` (the "fitted description"): element lists, curve control points, palettes, noise settings, wear
   primitives (for example N soft blobs: position, radius, colour, strength). NEVER per-dot data: no masks, no pixel arrays, no embedded images, no lookup
   pictures. `python3 -I lib/description_audit.py description.json` enforces this (size limit 64 KB by default, no list of more than 4000 numbers, no grids)
   and reports size as a share of the reference picture. Smaller and more meaningful is better: report accuracy per kilobyte.
3. GENERATE (Blender): the recipe is a real Blender procedural setup (shader nodes, geometry nodes, curves, modifiers, physics) that READS the description
   (as node input values, as attributes on a small "parameter geometry" of points/curves built from the JSON, or as a node tree written from the JSON by
   Python) and bakes the maps with the harness. The generator itself must be generic: it must work for ANY description of the same form, not only the fitted one.
4. COMPARE: `lib/pixel_compare.py` (dot-for-dot: error in brightness steps, PSNR, SSIM, colour difference, edge skill, height error, normal angle, and a tier:
   none / layout / close / exact) AND `lib/texture_compare.py` (same-kind-of-surface scores). Make the difference sheet (`--sheet`) and LOOK at it: it
   shows exactly where the recipe is wrong; fix the biggest wrong thing first. Iterate. Record the rate-distortion curve: accuracy after each layer you
   add (layout only; + per-element colour; + wear primitives; + outlines; + fine noise) with its description size. That curve is a main result.
5. SCALE: (a) VARIATION: sample 8 new descriptions from distributions fitted to the reference's own elements (sizes, colours, spacing, wear density) and
   bake them: each must score well on texture_compare (same kind of surface) yet differ from each other and from the reference at pixel level (not copies);
   (b) AREA: bake a 2 x 2 or 4 x 4 tile area (or a bigger single picture, e.g. 2508 or 5016 px) of unique, non-repeating content from the same generator,
   and show it has no visible repeats or seams; (c) RESOLUTION: bake at 512, 1254 and 2508 px and say what changes (render time, sharpness).
6. TRANSFER: take your recipe to a surface you were NOT given (examples: brick -> paving stones or cobbles or a tiled floor; slate -> roof shingles or fish-scale
   tiles; wood -> parquet or deck boards; metal -> hull plates or corrugated sheet; mud -> snow, sand or wet clay; gravel -> pebbles or crushed rock) by
   changing only the description / a few settings, and record exactly what you had to change and how long it took. Write down the lessons in a form that would
   help someone starting a different surface (a "how to start a new surface" checklist).
7. DOCUMENT in plain language (see notes above): the recipe step by step (which tool, which settings, what it does, how changing it changes the picture, with
   small sweep pictures), the analysis method, the description format, results table (all measures, every layer), dead ends, and the transfer lessons.

### Tools added for this
* `lib/pixel_compare.py` - dot-for-dot comparison and tiers (see its first lines). Reference height for pixel comparison is `height_as_uploaded.png` (8-bit).
* `lib/description_audit.py` - makes sure a description is a description, not a picture.
* `lib/texture_compare.py` - (updated) statistical sameness; height measures now ignore overall level/contrast and add a separate contrast measure; the
  reference tiles themselves have mild seams (jump across the wrap-around edge 1.7-2.5 x a normal jump; a seamless generated tile scores about 1.0).


---
## WHAT THE FIVE RESEARCH GUIDES FOUND (use it; they are in research/, all read-ready and tested)
Read at least: the "short version" of each guide, the sections for YOUR surface, and the pitfalls. Files: "02 Research - the shader node toolbox.md",
"02 Research - seamless tiles and baking.md", "02 Research - geometry nodes, curves, modifiers and physics for surface detail.md",
"02 Research - how people make each surface.md", "02 Research - getting a hand-painted stylised look.md". (Three more, "03 Research - Ucupaint.md",
"03 Research - Material Maker.md", "03 Research - MCP Blender Agent.md", are being written by other helpers and will appear in research/ while you work; look once around
the middle of your job and take what helps.)
The facts that matter most:
1. THE MAPS ARE DERIVED FROM THE COLOUR. The reference height is (about) the sRGB brightness of the colour picture (correlation 0.94-0.985), lightly blurred (~0.8 px),
   and the reference normal map is the slope of the 8-bit height with whole-number strengths: brick 6, slate 7, wood 8, metal 5, mud 9, gravel 10 (matches to
   rounding error). So the COLOUR PICTURE is the real problem; first prove the "derivation" (fit a small tone curve + blur + strength that turns the REFERENCE
   colour into the REFERENCE height and normal; that is the ceiling for derived maps), then reproduce the colour and let height/normal follow. Where real geometry makes
   the height (bricks, rivets, ruts), blend it with the colour-brightness height (the research: 50/50 hybrids help brick, slate and gravel).
2. THE LOOK IS MEASURABLY "PAINTED": flat patches 21-51 px across, 85-94% of strong edges change within 2 px, 1-2 px staircase edges, a palette of 8 colours reproduces each surface to a mean
   colour error of only 3-4.5 (Delta E), dark outlines (brick ~5 px, slate ~12 px, wood ~8, metal ~6, stone rims ~3). So each reference colour picture is close to a label map (a
   patch id -> palette colour) plus outlines plus a little grain. Full numbers: section 2 of the painted-look guide (research/experiments_hand_painted_look/data).
3. SEAMLESS: Blender noise, Voronoi, Gabor, Magic, Wave do NOT tile; use lib tileable_noise_group / tileable_voronoi_group (4D donut), whole-number layouts, wrap copies of geometry
   (9 copies), and test with the half-tile-shift test (bake the recipe shifted by half a tile and compare with the first picture rolled by half: lib/contrib/periodicity_test.sh).
   The texture_compare seam number gives false alarms on row/crack layouts (and the references themselves have seam ratios 1.7-2.5): trust the half-tile test and a 2 x 2 look.
   Compositor filters (Kuwahara etc.) break seams unless you wrap-pad first (lib/contrib/hp_tools.py).
4. BLENDER 5.2 FACTS: Noise sits in 0.25..0.73 (stretch with Map Range); hex colours must be converted sRGB->linear (rt.srgb_hex_to_linear); Bump default Distance is 0.001 now; a Geometry Nodes
   result renders black without a Set Material node; geometry-nodes modifier inputs are modifier.properties.inputs.<Socket_id>.value then update_tag(); the compositor headless needs
   scene.render.compositor_device = 'CPU'; Shader-to-RGB and EEVEE tricks do not work here; use view transform Standard for colour and Raw for data; 16-bit for height.
5. SCORES ARE NOISY: seed alone moves texture_compare by 0.01-0.03 (wood 0.115); compare same-size same-seed bakes; bake finals at 1254; trust the picture first.
6. TIMES (CPU, 1254 px): shader recipes 18-54 s; geometry recipes 94-263 s (ambient occlusion colour is 13x slower: use it only for finals); geometry itself 1-3 s.

### Shared helper scripts (lib/contrib, read their first lines; copies of the researchers' tools, tested to import)
builder.py (write a shader recipe like a list of sums; seamless stretched noise/cells; "which brick am I on"), stone_tools.py (polygon stones, one per cell), hp_tools.py
(painted-look blocks: anisotropic seamless noise/cells, warp, outline maker, photograph with wrap padding, compositor runner), gn_tools.py (Geometry Nodes writer; photograph_geometry:
height/colour/normal from real geometry under the overhead camera), layout_tools.py (row-layout group: bricks, slates, planks, plates, with wrap copies), relax_tools.py (relax points on a
wrapping tile), periodicity_test.sh. Use: sys.path.insert(0, '<proc-work>/lib'); sys.path.insert(0, '<proc-work>/lib/contrib'). Do not edit them; copy and change in your own folder.

### Description size classes
S <= 8 KB, M <= 64 KB, L <= 512 KB (`python3 -I lib/description_audit.py file.json --limit-kilobytes 8|64|512`). Report accuracy for each class you reach: that rate-distortion table
(size -> pixel tier, SSIM, Delta E, edge skill, height and normal error) is a main result. Say plainly where the "procedural" description ends and "tracing the picture" begins.
Aim: at least 'close' on the pixel tiers at class L, as high as you can; the generic generator must also make good NEW tiles from sampled descriptions.
