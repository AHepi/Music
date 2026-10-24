# 06 Guide - baking and checking maps

What this is: a guide to getting the maps of a recipe out of Blender correctly (the photograph route, Blender's Bake button, view transform, 8 or 16 bits,
the pixel filter, the project's harness), and to checking them with the project's three checking tools: the same-kind tool, the dot-for-dot tool and the
description audit. It says what each score means, shows the tools' own pictures, and lists every blind spot that this job ran into.
Every rule is shown on an example first, with the file that holds the numbers.
Companion guides: "06 Guide - relief - height, bump, displacement and normal maps.md" (how height and normal maps are made),
"06 Guide - seamless tiles and coordinates.md" (the half-tile test and the seam number), "06 Guide - descriptions - analyse, describe, generate, compare.md"
(what the six builds made and what each description size bought).

## How to read this guide

Words used (one word for each thing, always; the same words as the other 06 guides):
* **tile** = the square picture we make. **dot** = one pixel of it. **picture size** = dots across (1254 for the references and the finals).
* **maps** = the pictures of one tile together: the **colour picture**, the **height map**, the **normal map**, the **roughness map** and the **metallic map**.
* **recipe** = a Blender node setup (or a generator script) that makes a surface. **description** = the file of numbers a build's generator reads.
* **bake** = making the maps of a recipe, by any route. **photograph** = the project's route: a camera straight above a flat 1 x 1 square that glows with
  one channel of the recipe. **the Bake button** = Blender's own Cycles Bake (Render Properties > Bake).
* **view transform** = the Blender setting (Render Properties > Color Management > View Transform) that turns Blender's internal light numbers into the
  numbers written into a picture file. **Standard**, **Raw**, **AgX** and **Filmic** are its choices.
* **8-bit** = a picture that holds 256 levels per channel ("steps of 255"); **16-bit** = 65,536 levels.
* **pixel filter** = how much of its surroundings each dot of a render averages in. **samples** = how many rays Cycles averages per dot.
* **the harness** = `lib/bake_harness.py`, the project's photograph tool.
* **the same-kind tool** = `lib/texture_compare.py`; its overall number is the **same-kind score**. **the dot-for-dot tool** = `lib/pixel_compare.py`; its verdict is
  the **tier** (none, layout, close, exact). **the audit** = `lib/description_audit.py`. **sheet** = the picture each tool draws.
* **build** = one of the six surface jobs in `recipes/` (brick, slate, wood, metal, mud, gravel). **checker** = the independent helper who re-ran a build
  afterwards (its findings are `recipes/<surface>/verifier_answer.json`). **class S / M / L** = descriptions up to 8 / 64 / 512 KB (KB = 1024 bytes, as the audit counts).
* **new tile** = a tile made from a description drawn at random from statistics measured on the reference (not a copy of the reference).

Labels: **TESTED** = run in Blender 5.2.2 or plain Python on this machine and measured; the file is named. **NOT TESTED** = only read, or only reasoned.

Where the facts come from: `research/02 Research - seamless tiles and baking.md` sections 2.1 to 2.5 (its numbers are in
`research/experiments_seamless_tiles_and_baking/out/`), the six builds' reports and checkers' findings, the code of the four `lib/` tools, and NEW tests made
for this guide in `cookbook/checks/baking_and_checking/`:
* `run_self_tests.py` -> `self_tests.json` (both measuring tools on known cases: the reference, a slid copy, a blurred copy, a flat picture, the other surfaces);
* `smoothed_height_check.py` -> `smoothed_height_check.json` (which reference height the same-kind tool reads);
* `flat_baselines.py` -> `flat_baselines.json` (the "do nothing" normal error and height error of each reference);
* `view_transform_strip.py` (Blender) + `view_transform_measure.py` -> `view_transform_numbers.json` and `pictures/baking-strip-view-transform.jpg`;
* `audit_examples.py` -> `audit_examples.json` (the audit on real and made-up descriptions);
* `harness_smoke_256/` (the harness run once on `tests/recipe_smoke.py` at 256 dots).

In tables, a short path such as `brick/verifier_answer.json` means `recipes/brick/verifier_answer.json`; "research 2.3" means section 2.3 of the research guide above;
"checks/" means `cookbook/checks/baking_and_checking/`.

---

## 1. The short version

**Example first.** Take the brick reference and slide it 311 dots down and 517 dots across, letting what falls off one edge come back on the other
(`tests/selftest_brick_rolled2`). Nothing has been added or removed: it is the same painting, moved. The two measuring tools disagree completely
(`checks/self_tests.json`):

| | same-kind score | colour SSIM (1 = same picture) | colour difference (Delta E) | edge skill | tier |
|---|---|---|---|---|---|
| the brick reference itself | 0.953 | 1.0 | 0.0 | 1.0 | exact |
| the reference slid by (311, 517) dots | **0.992** | **0.324** | **19.54** | **0.123** | **none** |

(Each measure is explained in one sentence in section 7.3.)

The same-kind tool says "the same kind of surface" (0.992, higher even than the reference itself, for a reason given in section 7.4). The dot-for-dot tool
says "nothing is in the right place" (tier none). Both are right: they answer different questions. A new tile should score high on the first and low on the
second; a copy of the reference should score high on both.

The rules that would have saved the most time:
1. **Photograph, do not use the Bake button, for a flat tile made of nodes.** Both give the same dots (colour within 0.0011, roughness within 0.00001,
   research 2.2), but the photograph needs no UV map, no image node, and lets you choose the pixel filter. All six builds photographed.
2. **View transform Standard for the colour picture, Raw for every data map.** A brand-new Blender scene uses AgX, which turned a height of 0.5 into 0.667 and
   dulled the colour of a brick recipe by 7.17 Delta E (section 4). The harness sets this for you; your own scripts must too.
3. **Height maps in 16 bits.** In 8 bits a gentle slope holds only 54 levels and its normal map breaks into terraces (section 5).
4. **Pixel filter Box 1.0 and at least 16 samples for hard painted edges.** The new-scene default (Blackman-Harris 1.5) blurs; 4 samples leave staircases
   (section 6). A Gaussian pixel filter can be used on purpose as the height blur: width = about 4 x the blur you want (slate's measurement).
5. **Check with both measuring tools and look at both sheets.** The same-kind score asks "same kind?", the tier asks "same picture?" (section 7).
6. **Know each surface's yardsticks before reading a score**: what a completely flat normal map scores (slate 11.27 degrees, wood 24.11), what other
   real surfaces score on the same-kind tool (0.16 to 0.50 in my runs, not "about 0.1"), and the best a colour-made height and normal can ever reach
   (section 7.5).
7. **Every tool has blind spots, and this job found 17 of them** (section 9). The biggest: the same-kind tool barely separates mud from other surfaces (the
   gravel reference scores 0.498 against mud, higher than the eight new mud tiles' average 0.383), and the tier limits are the same for every surface.
8. **Run the audit on every description**, but know it only counts bytes and list lengths: it cannot see that a 450 KB description is a traced copy (section 8).

---

## 2. Two routes out of Blender: photograph or the Bake button

**The photograph, in one sentence:** a flat 1 x 1 square lies under a camera that looks straight down with no perspective; the square glows with exactly one
channel of the recipe (colour, or height, or roughness ...) and no lights touch it, so every dot of the render is that channel's exact value.

**The Bake button, in one sentence:** Blender's own Cycles Bake writes what a material does at each point of an object's surface into a picture, through
the object's UV map, into an Image Texture node that you select in the material.

**Example (TESTED, research 2.2, numbers in `research/experiments_seamless_tiles_and_baking/out/bake/results.json`):** one test material (Principled BSDF with
noise colour, roughness, 40 % metal and a Bump node) was photographed and baked at 256 dots.

| want | how with the Bake button | result against the photograph |
|---|---|---|
| colour, no metal | Bake Type Diffuse, only Color ticked | mean error 0.011 |
| colour, with metal | Bake Type Diffuse | **broken: metal comes out black** (brightness 0.0069 where the photograph has 0.5917) |
| colour, any surface | send the colour into an Emission shader, Bake Type Emit ("the emission trick") | mean error 0.0011, worst 0.0078 (one 8-bit step) |
| roughness | Bake Type Roughness | mean error 0.00001 |
| normal | Bake Type Normal, Space Tangent, swizzle +X +Y +Z (OpenGL) | equals the photographed Bump-node normal within 0.00008 |
| ambient occlusion, flat square with a Bump node | Bake Type AO | **plain white** (min 1.0, max 1.0): the Bump node is invisible to it |
| metallic, height | no Bake Type exists in Blender 5.2 | use the emission trick into a Non-Color picture (NOT TESTED separately) |

![Photograph against the Bake button: Diffuse turns metal black, Emit matches, roughness in an sRGB picture comes out too bright](../research/experiments_seamless_tiles_and_baking/out/figures/fig5_bake_routes.png)

Settings of the Bake button that matter (all TESTED in research 2.2 to 2.6):
* **Samples:** the Bake button uses the scene's render samples, default 4096 in 5.2: lower them (the research used 8 to 16).
* **The pixel filter does nothing to a bake** (Blackman-Harris and Box gave the same edge error, 0.061, at 16 samples); only the sample count matters.
* **The target picture's colour space decides the numbers written:** roughness baked into an sRGB picture came out 0.7422 instead of 0.5113; colour baked into a
  Non-Color picture came out too dark (error 0.2686).
* **Margin** (default 16 dots) only matters when the UV map does not fill the picture; for a tile whose UV map covers 0..1 it changes nothing.
* **High-detail to low-detail ("Selected to Active"):** Extrusion must exceed the tallest bump (Extrusion 0, the default, left 50 % of dots flat) and Max Ray
  Distance must be 0 or larger than Extrusion plus bump (Extrusion 0.1 with Max Ray Distance 0.05 left 100 % flat).

**What the builds did:** all six photographed, with the harness's scene (`bake_harness.new_bake_scene` is called 11 times and `render_to` 11 times across the
builds' generator scripts; counted with grep). None used the Bake button. Reason: a tile is a flat square, so the photograph is simpler and faster, and only the
photograph lets the pixel filter act as a blur on purpose (section 6).

**When the Bake button is the right tool** (from research 2.2 and 2.6, NOT used in the builds): when the surface is a real 3D object with its own UV map; when
detail on a dense mesh must be moved onto a simple mesh; when you want ambient occlusion from real geometry (on a displaced surface it gave min 0.84, average 0.988).

---

## 3. How the harness works (`lib/bake_harness.py`)

**What it is, in one sentence:** a script that runs inside Blender, builds the photograph scene, photographs each channel of a recipe into its own picture, and
then makes two normal maps from the height.

**Example (TESTED for this guide, `checks/harness_smoke_256/`):**

```
blender -b --disable-autoexec -t 2 --python lib/bake_harness.py -- tests/recipe_smoke.py OUT_FOLDER --size 256 --normal-reference brick
```

It took 1.7 seconds and wrote six pictures and a note: `colour.png` (8-bit), `height.png` (**16-bit**, grey in all three channels), `roughness.png` and
`metallic.png` (8-bit; the recipe's roughness 0.7 came back as 0.70000 on average, so no colour conversion touched it), `normal.png`, `normal_bumpnode.png`,
and `bake.json`: `{"size": 256, "sobel_strength": 38.59, "bump_node_distance": 0.1508, "seconds": 1.7}`. At 1254 dots the project notes give about 20 seconds.

**A recipe** is a Python file with `build_node_group(parameters)` that returns a shader node group with input `Vector` (the tile position, u and v from 0 to 1)
and outputs `Colour`, `Roughness`, `Metallic`, `Height` (0..1). `tests/recipe_smoke.py` is the smallest one.

**The scene it builds (`new_bake_scene`), and what each setting is for** (read in the code):

| setting | value | what it does | what goes wrong without it |
|---|---|---|---|
| render engine | Cycles, CPU | the only renderer here (no graphics card, so no EEVEE) | - |
| samples | 4 | rays averaged per dot | 4 leaves staircase edges on hard shapes (section 6); the builds raised it to 8 or 16 |
| adaptive sampling, denoising | off | every dot gets the same treatment | a denoiser invents smoothing in data maps |
| max bounces | 0 | light never bounces | nothing else in the scene can leak in |
| pixel filter | Box, width 1.0 | each dot averages only its own square | the new-scene default Blackman-Harris 1.5 blurs (section 6) |
| view transform | Standard (colour) / Raw (data), Look None, exposure 0, gamma 1 | numbers written unchanged (Raw) or with the ordinary screen curve (Standard) | AgX changes every value (section 4) |
| world | black | nothing glows behind the square | - |
| the square | 1 x 1 mesh with UV 0..1 | u = x, v = y | - |
| camera | orthographic, ortho scale 1.0, 5 units above the middle, clip 0.01 to 100 | one picture dot = one tile dot, no perspective | a perspective camera bends the tile |

**How one channel is shown (`show_channel_material`):** Texture Coordinate (UV) -> the recipe group -> Emission (Strength 1) -> Material Output. A single number
(height, roughness, metallic) is sent through Combine Color into red, green and blue, so the picture is grey.

**How it saves (`render_to`):** PNG, RGB, 16-bit for the height, 8-bit for the rest; view transform Raw for data, Standard for colour.

**The two normal maps:**
* `normal.png`: the slope of the height (right neighbour minus left, lower minus upper, halved; wrapping at the edges) times a strength. With
  `--normal-reference NAME` the strength is searched until the spread of the normal map's tilts equals the reference's; without it the strength is 8.
  Caution: this matches a spread, not a look. On the smooth smoke noise it chose 38.59, far from brick's own 6 (`checks/harness_smoke_256/bake.json`). The
  function is called `sobel_normal` but it is a plain slope, the same rule the reference normal maps were made with (relief guide, section 4).
* `normal_bumpnode.png`: the same height through Blender's own Bump node with Distance = strength / picture size (here 38.59 / 256 = 0.1508).

**How the builds used it:** not as a whole. Each build wrote its own generator (a painter of flat shapes) and used the harness's building blocks: `new_bake_scene`
(11 calls), `render_to` (11), `load_png_as_array` (17) and `save_array_png` (22), then made the height and normal maps from the colour picture in numpy.

**Traps found by the builds** (each happened):
* **Camera height:** the camera sits 5 units up and sees as far as 100. A generator that stacks thousands of shapes a hair apart must keep them inside that range
  (wood asked for "a helper that puts the camera above the highest shape", `wood/builder_answer.json`; slate used steps of 0.0001 for 26,000 shapes).
* **It assumes a 1 x 1 tile of 1254 dots** in places: brick's first 2508-dot area photographed only a quarter of its description because a fixed 1254 was used in
  its own generator (`brick/builder_answer.json`); brick asked for a helper that takes the tile size in dots.
* **Grey pictures:** the relief guide reports an earlier problem where a flat (2-D) array was saved into the red channel only. The current `save_array_png` copies
  a grey array into red, green and blue: TESTED for this guide (`checks/save_grey_check.py`, `save_grey_check.log`): a 2-D grey ramp saved and read back had
  red = green = blue, largest error 0.00187 in 8 bits and 0.00001 in 16 bits.

---

## 4. View transform: Standard for colour, Raw for data, and the AgX trap

**What it is, in one sentence:** the view transform decides which numbers Blender writes into the picture file for a given internal light value; Standard
applies the ordinary screen curve, Raw writes the value unchanged, AgX and Filmic apply film-like curves that also change colours.

**Example first (TESTED for this guide, `checks/view_transform_numbers.json`):** one small brick recipe (`research/.../test_recipes/bricks_and_wave_recipe.py`),
photographed eight times at 256 dots, changing nothing but the view transform.

![One brick recipe, only the View Transform changed: top colour (Standard is right), bottom height (Raw is right)](pictures/baking-strip-view-transform.jpg)

| picture | view transform | average difference from the right picture (steps of 255) | colour difference (Delta E) | colour strength (Lab chroma; right = 28.49) |
|---|---|---|---|---|
| colour | **Standard (right)** | 0 | 0 | 28.49 |
| colour | AgX (what a new Blender scene uses) | 9.1 | 7.17 | 23.25 (duller) |
| colour | Filmic | 8.9 | 7.99 | 21.92 (duller) |
| colour | Raw | 62.8 | 26.84 | 35.61 (too dark and too strong) |
| height | **Raw (right)** | 0 | - | - |
| height | Standard | 67.8 | - | - |
| height | AgX | 59.9 | - | - |
| height | Filmic | 68.0 | - | - |

What the picture shows: AgX and Filmic keep the brick pattern but wash the red out (average red 0.73 -> 0.67 under AgX); the average brightness hardly moves
(0.565 -> 0.535), so an average alone would not have caught it. Raw makes the colour picture dark. For the height, every choice except Raw lifts the greys a lot
(average 0.346 -> 0.581 to 0.612).

The rule, measured precisely on a plain grey ramp (TESTED, research 2.1, `research/.../out/colour_space/results.json`): a photographed value of 0.5 came out as
**0.5000 with Raw**, 0.7373 with Standard, 0.6667 with AgX and 0.6961 with Filmic (8-bit; 16-bit gave 0.5000, 0.7353, 0.6651, 0.6949).

**Rules (TESTED unless marked):**
1. **Colour picture: view transform Standard.** Standard turns Blender's internal (linear) numbers back into the ordinary screen numbers. So a palette colour
   typed as ordinary 0..255 numbers must be **converted to linear first** before it goes into an Emission colour (`rt.srgb_hex_to_linear` in `lib/recipe_tools.py`);
   then Standard writes back exactly the numbers you typed (slate recipe guide, section 4 step 4; not re-measured by me).
2. **Height, roughness, metallic, normal: view transform Raw** (or save the array yourself without conversion, as `save_array_png` does).
3. **A new scene uses AgX.** Any script that does not call the harness's `new_bake_scene` must set the view transform itself, every time it renders.
4. **Pictures you load back as data** (an Image Texture node holding a height or roughness map) must be set to colour space **Non-Color**; colour pictures stay sRGB.
   The Bake button writes into the target picture's colour space (section 2).
5. **Saving:** `image.save()` of a float image writes the stored numbers whatever the colour space; `image.save_render()` applies the view transform to an sRGB
   image (0.5 became 0.2157 with Raw) but not to a Non-Color image (research 2.3 table).

---

## 5. 8 bits or 16 bits

**What it is, in one sentence:** an 8-bit picture has 256 levels per channel, which turns a gentle slope into stairs; a 16-bit picture has 65,536 levels.

**Example (TESTED, research 2.1, `research/.../out/colour_space/analysis.json`):** a ramp covering one fifth of the grey range, photographed with Raw, holds
**54 different levels in 8 bits** and 3,957 in 16 bits. Its normal map made from the 8-bit version has 53 % of dots with exactly zero sideways tilt (terraces),
against 0.9 % from 16 bits (relief guide, section 8).

![Red channel of a normal map made from an 8-bit height (left) and a 16-bit height (right)](../research/experiments_seamless_tiles_and_baking/out/figures/fig8_height_bit_depth.png)

**Rules:**
* **Height: 16-bit, Raw.** The harness does this.
* **Colour: 8-bit is enough** (all six references are 8-bit colour; every build's colour picture is 8-bit).
* **Normal maps: 8-bit is usual** (the references' are), but **an 8-bit normal is a little shorter than length 1**, so measure angles only after making each
  arrow length 1, as the dot-for-dot tool does. Metal's first "ceiling" (5.7 and 6.7 degrees) was this mistake; made length 1 it is 2.06 and 3.71 degrees
  (`metal/verifier_answer.json`; relief guide 3.3).
* **The references come in two heights:** `height_as_uploaded.png` (8-bit, the original the normal maps were made from) and `height.png` (16-bit, lightly
  smoothed). On brick they differ by **5.03 steps** after the best brightness-and-contrast fit: that is what the dot-for-dot tool reports for "the reference
  itself", because it compares the folder's `height.png` with the reference's `height_as_uploaded.png` (`checks/self_tests.json`).
* **Both measuring tools compare against the 8-bit upload.** The dot-for-dot tool always did; the same-kind tool has done so since its change at 15:45 on
  19 October (read in `lib/texture_compare.py`, `summarise`; the earlier copy `lib/texture_compare.py.bak_before_height_fix` read `height.png`). The slate
  build's note that "the two tools read different heights" (`slate/builder_answer.json`) describes the earlier copy; the relief guide (section 3.3) and the
  slate, wood and gravel guides that repeated it now say so.
  **And smoothing your height costs a lot on the same-kind tool** (TESTED for this guide, `checks/smoothed_height_check.json`): the same slid brick copy scores
  **0.992 with the 8-bit height and 0.830 with the lightly smoothed 16-bit height**; its height group falls from 0.998 to 0.524 and the "normal agrees with the
  height" measure from 1.0 to 0.0, although the normal map is the reference's own.
* Slate, mud and gravel rounded their height to 8 bits before making the normal map, on purpose, to copy how the references were made (relief guide, section 4).

---

## 6. The pixel filter and samples

**What they are, in one sentence each:** the pixel filter decides how much of its surroundings each dot of a render averages in; samples decide how many rays
are averaged per dot, which decides how smooth a hard edge looks.

**Example (TESTED, research 2.4, `research/.../out/colour_space/analysis.json`, "edge"):** a hard black-and-white diagonal edge, 64 x 64 dots; error = average
distance from the exact share of each edge dot that is black.

| setting | error on the edge dots | dots away from the edge that got blurred |
|---|---|---|
| Box 1 dot, 1 sample | 0.516 (pure black or white: jagged) | 0 |
| Box 1 dot, 4 samples (the harness) | 0.171 | 0 |
| Box 1 dot, 16 samples | 0.062 | 0 |
| Box 1 dot, 64 samples | 0.027 | 0 |
| Blackman-Harris 1.5 dots, 4 samples (the new-scene default filter) | 0.171 | **63** |
| Gaussian 1.5 dots, 64 samples | 0.029 | **259** |

![Edge quality by pixel filter and sample count](../research/experiments_seamless_tiles_and_baking/out/figures/fig6_edge_quality.png)

What it costs (TESTED, research 2.4, `research/.../out/speed/results.json`): one 1254-dot picture of detail-8 noise on 2 threads took 2.5 s at 4 samples,
8.7 s at 16 and 34.9 s at 64 (the seamless "donut" noise: 3.2, 12.1 and 46.5 s).

**How the builds used them:**
* **Colour: Box 1.0 with 8 or 16 samples** (brick 16 for its finals, metal and mud 8, slate and gravel 16; from each build's report). Slate's strip below shows
  1 sample as hard stair-steps and 16 as a clean one-dot soft edge.
* **Height: the Gaussian pixel filter as the blur.** The reference heights look like the colour brightness blurred by about half a dot. Slate measured which
  Gaussian filter width gives which blur at 1254 dots (`slate/final_report.json`, filter_width_test): width 1 and 1.5 = a 0.3-dot blur, 2 = 0.5, 3 = 0.7,
  4 = 0.9, 6 = 1.4, 8 = 1.8. **So ask for about 4 x the blur you want.** The first guess (width / 12) blurred about 3 times too much and cost about 0.06 of
  same-kind score (0.67 against 0.74; slate recipe guide, section 4). Slate, wood and gravel use this.
* **The width is counted in render dots:** at 384 dots the same width blurs about 3.3 times more of the tile than at 1254 (slate checker), so a small test
  render looks softer than the real bake.
* Metal's generator has a filter width setting whose code note says "0.01 = hard staircase edges like the painted reference; 1.0 = smooth edges"
  (`metal/generator/metal_generator.py`, line 346); its effect was NOT measured.

![Slate: samples 1, 2, 4, 16 (4 x zoom of the colour picture)](../recipes/slate/guide_pictures/strip_samples_zoom.png)

![Slate height: Cycles Gaussian filter width box, 1, 2, 4, 8 (made at 384 dots, so softer than at 1254)](../recipes/slate/guide_pictures/strip_height_filter_width.png)

---

## 7. Checking a texture set: the two measuring tools

### 7.1 Why two tools

A painted tile can be wrong in two different ways: it can be the wrong KIND of surface (the colours, sizes and sharpness are not those of brick), or the right
kind with everything in different places. The first matters for new tiles; the second matters only when you want to copy the reference. The example in section 1
(the slid copy: same-kind 0.992, tier none) is the cleanest proof that one number cannot answer both.

### 7.2 The same-kind tool (`lib/texture_compare.py`)

**What it is, in one sentence:** it answers "does this look like the same KIND of surface as the reference, wherever things are?", from 0 (as different as a
typical other reference surface) to 1 (the same by that measure).

**Run it:** `python3 -I lib/texture_compare.py brick YOUR_FOLDER --json score.json --sheet sheet.png` (YOUR_FOLDER holds `colour.png`, `normal.png`, `height.png`;
the other maps are not scored, because the references have none).

**What it measures** (read in the code; 14 measures in 4 groups; the weight is how much each counts in the overall score):

| group | measure | in plain words | weight |
|---|---|---|---|
| colour | colour_distribution | are the same colours there, in the same amounts? | 3.0 |
| colour | colour_spectrum | is the same amount of picture at each feature size (big blobs, small specks)? | 2.0 |
| colour | colour_orientation | do edges run in the same directions (upright drips, level rows)? | 1.0 |
| colour | colour_scale | how far can you move before the picture stops looking like itself, across and up? | 2.0 |
| colour | colour_gradient | are edges as sharp, and as many, as in the reference? | 1.5 |
| height | height_distribution, height_spectrum, height_gradient | the same three questions for the height map (its level and contrast are stretched away first) | 1.5 each |
| height | height_colour_link | does the height follow the colour brightness as much as in the reference? | 1.0 |
| height | height_contrast | is the relief as strong (twice or half as strong scores 0)? | 0.5 |
| normal | normal_tilt | are the surface tilts spread like the reference's? | 1.5 |
| normal | normal_components | are left-right and up-down tilts as strong, on average, as in the reference? | 1.0 |
| normal | normal_height_agreement | does the normal map follow the slope of the height map as much as in the reference? | 0.5 |
| tiling | seam | the seam number: the jump across the wrap edge divided by an ordinary jump (1.0 = none); 3 or more scores 0 | 1.5 |

**How a measure becomes a score:** the distance between your set and the reference is divided by the "different surface" distance for that reference and that
measure: the **median** distance from the reference to the other reference surfaces, that is the middle one when they are put in order (stored in
`lib/texture_compare_anchors.json`). Score = 1 minus that
share, cut at 0 and 1. Because the median is used, about half the other surfaces land above 0 on any measure, which is why whole other surfaces score 0.16 to
0.50 overall, not 0 (section 7.4).

**The sheet** (example: the slid brick copy, `pictures/checking-same-kind-sheet-slid-brick.jpg`, made by `checks/run_self_tests.py`):

![Same-kind sheet of the slid brick copy](pictures/checking-same-kind-sheet-slid-brick.jpg)

How to read it: left half, top to bottom: colour, normal map, height map, reference on the left and yours on the right. Right half: your colour laid 2 x 2 (look at
the crossing in the middle for seams and repeats), then two curves: the **feature-size curve** (how much picture there is at each size, big features on the left;
red = reference, blue = yours) and the **brightness spread** (how many dots at each brightness). When the two curves lie on top of each other, as here, only the
blue one shows. The curve labels are small and pale: read them zoomed in.

### 7.3 The dot-for-dot tool (`lib/pixel_compare.py`)

**What it is, in one sentence:** it answers "is this the same PICTURE as the reference, dot for dot?", with several measures and a tier.

**Run it:** `python3 -I lib/pixel_compare.py brick YOUR_FOLDER --json pixel.json --sheet difference.png`. It compares your `height.png` with the reference's
8-bit `height_as_uploaded.png`, and your `normal.png` with the reference's OpenGL `normal.png`.

**What it measures** (read in the code):

| measure | in plain words |
|---|---|
| colour_mae_levels, colour_psnr_db | the average colour difference per dot, in steps of 255, and the same as a "signal to noise" number (higher = closer) |
| colour_ssim | how alike the light-and-dark structure is, in 11-dot windows; 1 = the same picture. It is high for any flat picture (section 9) |
| colour_mean_delta_e, colour_p95_delta_e | the colour difference in the standard unit (about 2.3 = the smallest difference most people see side by side; 10 = clearly another shade); average, and the level that 95 % of dots stay under |
| edge_precision, edge_recall, edge_f1 (2 dots) | of the edges in your picture, how many have a reference edge within 2 dots; of the reference's edges, how many have one of yours; both together |
| edge_f1_by_luck, edge_skill_2px | painted pictures are full of edges, so a wrongly placed copy matches many by luck. The tool slides your edges by two odd amounts to measure that luck and takes it off: **edge skill** 0 = no better than luck, 1 = every edge in place |
| height_mae_levels, height_mae_best_fit_levels | the height difference in steps of 255, raw and after the best brightness-and-contrast fix (the second measures the SHAPE of the relief) |
| height_ssim, height_correlation | the same two ideas for the height map |
| normal mean, median, 95 % angle | the angle between your normal and the reference's, dot by dot, after making both length 1 |

**The tiers** (from the top of `lib/pixel_compare.py`; a tier is reached when ALL its limits pass; measures that cannot be made are skipped):

| tier | edge skill at least | colour SSIM at least | colour difference (Delta E) at most | height error after best fit at most | normal error at most |
|---|---|---|---|---|---|
| layout ("the features are in the right places") | 0.30 | - | 20 | 40 | - |
| close ("a careful eye needs a side-by-side") | 0.55 | 0.60 | 10 | 20 | 12 degrees |
| exact ("practically the same picture") | 0.85 | 0.92 | 3 | 6 | 4 degrees |

**The sheet** (example: brick class M, 63,973 bytes, tier layout: `brick/guide_pictures/difference_sheet_class_M.png`):

![Dot-for-dot sheet of brick class M](../recipes/brick/guide_pictures/difference_sheet_class_M.png)

How to read it: top left the reference, top right yours; bottom left the **difference** (bright = differs; the brightness is the difference x 4); bottom right
the **edges**: red = an edge only in the reference, green = only in yours, yellow = in both. In the brick M sheet the brick outlines are yellow (the layout is right)
and the faces are full of red specks (the reference's small paint patches that M does not hold). For comparison, the slid copy's sheet is mostly red and green,
which is what "nothing in the right place" looks like:

![Dot-for-dot sheet of the slid brick copy](pictures/checking-dot-for-dot-sheet-slid-brick.jpg)

### 7.4 What the scores mean: the self-tests

**TESTED for this guide** (`checks/self_tests.json`; all against the brick reference unless the row says mud; plain Python, the current tools):

| candidate | same-kind score (colour / height / normal / tiling group) | colour SSIM | colour difference (Delta E) | edge skill | height error after best fit | normal error (degrees) | tier |
|---|---|---|---|---|---|---|---|
| the brick reference itself | **0.953** (0.997 / 1.0 / 1.0 / 0.392) | 1.0 | 0.0 | 1.0 | 5.03 | 0.0 | exact |
| slid by (311, 517) dots | **0.992** (0.996 / 0.998 / 0.965 / 1.0) | 0.324 | 19.54 | 0.123 | 39.95 | 25.41 | none |
| blurred by about 6 dots | **0.241** (0.34 / 0.265 / 0.0 / 0.0) | 0.546 | 6.55 | 0.0 | 22.71 | 16.37 | none |
| a flat picture of the average colour | **NaN** (the tool fails; colour group 0.08) | 0.515 | 15.37 | 0.0 | 39.95 | 16.72 | none |
| the slate reference | 0.164 | 0.371 | 34.31 | 0.0 | 39.95 | 22.31 | none |
| the wood reference | 0.211 | 0.237 | 23.34 | 0.0 | 39.94 | 31.02 | none |
| the metal reference | 0.266 | 0.332 | 29.61 | 0.0 | 39.96 | 23.28 | none |
| the mud reference | 0.324 | 0.269 | 23.93 | 0.0 | 39.95 | 31.15 | none |
| the gravel reference | 0.256 | 0.254 | 31.29 | 0.0 | 39.95 | 31.87 | none |
| against MUD: brick / slate / wood / metal / **gravel** references | 0.24 / 0.179 / 0.374 / 0.195 / **0.498** | - | - | - | - | - | - |

How these copies were made: the slid copy is the reference moved by (311, 517) dots with wrap-around (`tests/selftest_brick_rolled2`; I found the amount by
matching it to the reference: mean difference 0.0 after the same roll). The blurred copy (`tests/selftest_brick_blur`) matches a Gaussian blur of 6 dots to within
0.3 steps of 255 (my estimate; its maker's note was not found).

What the rows say, in plain words:
* **A re-arranged copy of the right painting scores 0.99** on the same-kind tool and tier none on the dot-for-dot tool. That is the ideal for a new tile.
* **The reference itself scores 0.953, not 1.0**, because its own mild seam (seam number 2.22) gives its tiling group only 0.392; the slid copy moves that seam into
  the middle of the picture, so its wrap edge is clean (seam number 0.56) and it scores higher than the original.
* **Blur kills the same-kind score** (0.241): sharpness and fine detail are what the tool watches. On the dot-for-dot tool the blurred copy keeps a fair colour
  difference (6.55, it is the same picture) but edge skill 0.
* **Other real surfaces score 0.16 to 0.32 against brick, and 0.18 to 0.50 against mud.** The project notes (`PROCEDURAL_NOTES.md`, line 27) give "another
  surface about 0.1" and "a blurred copy about 0.17"; today's tool gives the numbers above. The tool's height measures were changed at 15:45 on 19 October
  (section 5); that the notes' numbers come from the earlier version is likely but NOT TESTED.
* **A flat picture scores better than a moved copy on SSIM** (0.515 against 0.324) and on the normal error (16.72 against 25.41). SSIM and the normal error
  reward "nothing" over "the right things in the wrong places".
* **The height error 39.95 means "no relation at all"** for brick: it is what a flat height gets (section 7.5).

### 7.5 Yardsticks: know each surface's numbers before you read a score

Two "do nothing" numbers (TESTED for this guide, `checks/flat_baselines.json`, measured the way the dot-for-dot tool measures) and the best a colour-made height and
normal can ever reach (the "derivation ceiling", from the builds; relief guide, section 3):

| surface | normal error of a completely flat normal map (degrees) | height error of a flat height after best fit (steps) | ceiling: height error / normal error with the reference's own colour | tier "close" reached by a build? |
|---|---|---|---|---|
| brick | 16.72 | 39.95 | 3.02 / 3.63 (3.05 before the best fit; `brick/scores/ref_roundtrip/pixel.json`, reproduced by the checker; reached tier exact) | no (best normal 13.93) |
| slate | **11.27** | 41.08 | 3.03 / 2.71 (checker) | yes, at 269,986 bytes |
| wood | 24.11 | 41.59 | 4.15 / 4.6 (plain slope; 4.3 with Sobel) | no (best normal 15.46) |
| metal | 13.26 | 32.49 | 4.93 / 3.71 (checker; reached tier exact) | yes, at 261,188 bytes |
| mud | 23.5 | 46.48 | 3.32 / 3.7 (Sobel at strength 10; 4.8 plain slope) | no (best normal 18.59) |
| gravel | 24.46 | 48.11 | 5.02 / 4.6 (Sobel at strength 12; 5.9 plain slope) | no (best normal 22.33) |

(Ceiling numbers: `recipes/<surface>/final_report.json`, derivation_ceiling, and the checkers' corrections, as collected in the relief guide, section 3.1.
Sobel = the slope rule that also counts the neighbouring rows at half weight.)

How to use it:
* **A normal error above the flat number is worse than no relief at all.** Brick S (17.66) and M (17.33) are worse than flat (16.72); slate S0 and the M classes
  (11.66 to 11.95) are worse than flat (11.27); gravel's procedural S_v4 (37.77) is far worse than flat (24.46).
* **"Close" was reached only on the two surfaces whose flat normal error is low** (slate 11.27, metal 13.26). Where a flat normal map is 23 to 24 degrees off
  (wood, mud, gravel), the 12-degree limit means halving it, and no description up to 512 KB did.
* **A height error near the flat number means no relation.** Metal's eight new tiles all scored 32.47 to 32.49 (`metal/final_report.json`): exactly the flat number.

**Noise in the scores:** the same recipe with a different random seed moves the same-kind score by 0.01 to 0.03 (project notes; wood 0.115 in one case, notes
line 129), by 0.03 to 0.05 for gravel and mud (`gravel/builder_answer.json`, `mud/builder_answer.json`). Compare same-size, same-seed bakes, and do not chase
differences smaller than that.

### 7.6 The order of checking that worked

1. Bake at 1254 dots (scores of smaller bakes are made after enlarging, so they come out lower: metal S same-kind 0.373 at 512 against 0.523 at 1254,
   `metal/final_report.json`).
2. Run both tools; write both numbers down, with the description size.
3. **Look at both sheets.** "A good score with an ugly picture is not a win, and a good picture with a poor score tells you which measure to chase" (project notes).
   The gravel builder: the same-kind score "did not see the blocky shapes or hue errors my eyes saw" (`gravel/builder_answer.json`).
4. Compare the normal error with the flat number, the same-kind score with the other-surface level, the tier with the ceiling (section 7.5).
5. Check seams with the half-tile test, not the seam number (seamless guide, section 8).

---

## 8. The description audit (`lib/description_audit.py`)

**What it is, in one sentence:** it checks that a description is a list of meaningful numbers (elements, curves, palettes, settings) and not a picture in disguise,
and reports its size.

**Example first (TESTED for this guide, `checks/audit_examples.json`):**

| file | limit | bytes | numbers | biggest list | share of a raw 1254 x 1254 colour picture | verdict |
|---|---|---|---|---|---|---|
| slate S1, layout + paint statistics (procedural) | 8 KB | 6,597 | 888 | 24 | 0.0014 | passed |
| slate L fine, traced patches | 64 KB | 453,054 | 154,230 | 9,383 | 0.096 | refused: over the size limit |
| slate L fine, traced patches | 512 KB | 453,054 | 154,230 | 9,383 | 0.096 | passed |
| made up: a 100 x 100 grid of grey values | 64 KB | 45,937 | 10,000 | 100 | 0.0097 | refused: "a grid of 100 x 100 numbers (looks like an image)" |
| made up: a flat list of 5,000 numbers | 64 KB | 22,889 | 5,000 | 5,000 | 0.0049 | refused: "more than 4000: looks like picture data" |
| made up: 100 polygon outlines of 6 to 78 numbers, the first five long | 64 KB | 11,574 | - | 100 | - | **refused (a false alarm)**: "a grid of 100 x 70 numbers" |

**What it checks** (read in the code): the file size against the limit (KB = 1024 bytes; default 64); no flat list of more than 4,000 numbers; no list of more
than 64 items whose first five items are each lists of more than 64 numbers (a "grid"); no text longer than 2,000 characters (an embedded file). It exits with 1
when it refuses.

**Run it:** `python3 -I lib/description_audit.py description.json --limit-kilobytes 8` (or 64, or 512, for classes S, M, L).

**What it does NOT check** (each found in this job):
* **It cannot see tracing.** Slate's L fine passes at 512 KB although it holds 9,383 traced patches, 9.6 % of the size of a raw picture of the reference; the checkers
  of all six builds call the L classes "vector copies" of the reference. Wood's L3 holds 85,093 corners, mud's L 76,058 (`wood/verifier_answer.json`,
  `mud/verifier_answer.json`). The builders asked for a corner count in the report (`mud/builder_answer.json`, `wood/builder_answer.json`).
* **It can be met "by the letter":** metal stored its outlines in chunks of 60 numbers and capped them at 120 corners (`metal/builder_answer.json`); gravel's stamp
  lists stay just under 4,000 numbers (3,450 and 3,963; `gravel/verifier_answer.json`).
* **False alarm on lists of outlines:** the grid rule does not check that the rows have equal length, so a list of polygons whose first five are long is called a
  picture (my last example above). Brick, slate and metal hit it and worked round it in their data (brick starts its list with a plain tile-sized rectangle; slate
  writes each patch as `[colour, [numbers]]`). All three asked for "rows of equal length" in the rule.
* **KB is 1024 bytes:** golden mud's L description is 513,735 bytes and passes the "512 KB" limit (524,288 bytes) (`mud/verifier_answer.json`).

---

## 9. Blind spots found in this job (each one happened)

**The same-kind tool**
1. **The seam number gives false alarms on row and crack layouts, and the references have their own seam.** The brick reference scores tiling 0.392 against itself
   (section 7.4); slate's new tile 106 lost 0.10 of tiling on a seam number of 1.21 (`slate/final_report.json`); metal's traced M and L read 0.837 and 0.811 although
   the half-tile test passes (`metal/final_report.json`); wood's first area numbers read 3.71 and 3.65 and were 0.91 and 0.89 when jumps were compared in the same
   direction (`wood/verifier_answer.json`). Full list and a fairer version: seamless guide, section 8.2.
2. **Grain hides seams and lifts the score:** brick's traced L went from tiling 0.444 to 1.0 and overall 0.432 to 0.598 when per-dot grain 0.14 was added, with no
   change at the seam (`brick/verifier_answer.json`). Grain also lifted wood's traced L2 from 0.459 to 0.763 while its SSIM fell from 0.674 to 0.509
   (`wood/final_report.json`, extras). **The two tools pull in opposite directions at the finest scale:** say which one a grain setting is tuned for.
3. **It barely separates mud from other surfaces** (found by the mud checker, `mud/verifier_answer.json`; confirmed for this guide): new mud tile 103 scores
   0.353 against mud and 0.306 against brick, 0.283 against gravel; mud's M class scores 0.426 against SLATE and 0.362 against mud. My run: the **gravel reference
   scores 0.498 against mud** and the wood reference 0.374 (`checks/self_tests.json`), above the eight new mud tiles' average of 0.383. Only mud's traced L was
   clearly mud-like (0.483 against mud, 0.29 against slate). So "same kind" for the new mud tiles rests on the eye, not on the tool.
4. **"Another surface" is not 0.1.** Against brick the other references score 0.164 to 0.324; against mud 0.179 to 0.498. A new tile of a seamless generator gets
   its tiling group (1.5 of the 20 weight units) for free, so its floor is higher still. Before calling a new tile "the same kind", score it against the other
   references too (only done for mud, by its checker).
5. **It fails on a perfectly flat picture** (NaN, a division by zero; my run and gravel's ladder stage 0, `gravel/final_report.json`).
6. **It punishes a smoothed height hard:** 0.992 -> 0.830 for a 0.8-dot smoothing of the same height (section 5). Slate found the normal-height agreement at 0.0
   for a normal made exactly from its own height (`slate/builder_answer.json`).
7. **Its feature-size measure is shared out over the whole picture,** so changing one layer moves the score at every size: metal's tuning of one layer made the
   score worse, 0.516 -> 0.454 -> 0.410 (`metal/builder_answer.json`).
8. **It cannot see shapes or clusters:** mud's pebble clusters "look closer by eye" but did not change the score (`mud/builder_answer.json`); gravel's blocky stones
   and wrong hues were seen only by eye.
9. **Tuning on it makes it optimistic:** wood's sampler was tuned to maximise the same-kind score, so its new tiles' 0.626 "is optimistic as evidence"
   (`wood/verifier_answer.json`).
10. **A crop of a bigger picture is not a tile:** a 1254-dot quarter of a 2508 area gets tiling 0 (mud's area quarters scored 0.29 to 0.31 overall, `mud/final_report.json`).

**The dot-for-dot tool**

11. **Missing maps raise the tier:** golden mud has no height or normal reference, so those two limits are skipped and its traced L reached "close"; the mud checker
    made a stand-in height and normal from the golden colour by the same rule and got normal 23.5 degrees and height 22.5 steps, which would be "layout"
    (`mud/verifier_answer.json`). Read any tier of a colour-only reference as "colour measures only".
12. **The same limits for every surface:** a flat normal map already meets the "close" normal limit on slate (11.27 < 12), while on wood, mud and gravel the limit
    asks for half the flat error (section 7.5). The layout tier's height limit (40) is met by a flat height on brick (39.95) and metal (32.49). Wood and gravel
    asked for limits made from each surface's own flat number or ceiling (`wood/builder_answer.json`, `gravel/builder_answer.json`).
13. **SSIM rewards flatness:** a flat picture beats any invented content (gravel's flat ground colour 0.444 against 0.213 for the procedural stones,
    `gravel/final_report.json`; my flat brick 0.515 against the slid copy's 0.324). Never judge a new tile with SSIM.
14. **The reference's own seam makes its edge rows unfair** to a seamless tile (metal asked for an option to ignore a band of dots at the edge; NOT TESTED).

**The builders' own measuring scripts** (not the shared tools, but the same lesson)

15. **Un-normalised 8-bit normals** added about 5 degrees to metal's ceiling and made "exact" look impossible; the checker's correct number reached "exact"
    (`metal/verifier_answer.json`).
16. **Numbers measured at the wrong size or with a different cut:** gravel's half-tile test was run at 512 dots while the text said 1254 (at 1254: 0.78 mean
    difference, 0 % over 40); gravel's area time 173 s belonged to another test (the area's own record says 252.6 s); mud counted dots over 8 steps where the others
    counted over 40 (`gravel/verifier_answer.json`; seamless guide 8.1).
17. **Stale pictures:** slate's S0 pictures were made before its description was last rewritten (mean colour difference 1.3 steps; `slate/verifier_answer.json`);
    metal's sweep strips were made before its final description (1.46 to 1.55 steps). Re-bake before you quote.

---

## 10. Recipe cards (every line was run, in the file named)

**Card 1 - photograph a node recipe.** `blender -b --disable-autoexec -t 2 --python lib/bake_harness.py -- RECIPE.py OUT --size 1254 --normal-reference NAME`
-> colour (8-bit, Standard), height (16-bit, Raw), roughness and metallic (8-bit, Raw), two normal maps, `bake.json`. (section 3; `checks/harness_smoke_256/`)

**Card 2 - photograph by hand (your own generator).** Orthographic camera, ortho scale 1, straight down over a 1 x 1 square; Emission (Strength 1) showing one
channel; no lights, black world, max bounces 0, no denoising; colour: Box 1.0, 16 samples, Standard, 8-bit, palette colours converted to linear first; height:
Raw, 16-bit, Gaussian filter width = 4 x the wanted blur (or Box and blur in numpy). (sections 3, 4, 6; slate generator)

**Card 3 - the Bake button, when you need it.** UV map 0..1; an Image Texture node with a new picture, selected and active, not connected; samples 8 to 16;
colour through the emission trick (Emit) into an sRGB picture; data into a Non-Color picture; normal: Tangent, +X +Y +Z (OpenGL); AO only on real geometry;
Selected to Active: Extrusion above the tallest bump, Max Ray Distance 0. (section 2; research 2.2 to 2.6)

**Card 4 - check a set.** `python3 -I lib/texture_compare.py NAME OUT --json t.json --sheet t.png` and `python3 -I lib/pixel_compare.py NAME OUT --json p.json --sheet p.png`;
look at both sheets; compare with the yardsticks (section 7.5); half-tile test for seams; for new tiles also score against the other references. (section 7)

**Card 5 - audit a description.** `python3 -I lib/description_audit.py D.json --limit-kilobytes 8` (or 64, 512); write down bytes and the share of a picture; say in
words whether the description is rules, fitted elements or traced patches (the audit cannot tell). (section 8)

---

## 11. Lessons that carry to other surfaces

1. **Decide what you are checking before you check:** "same kind" (new tiles) or "same picture" (a copy). They want different tools and pull against each other at the
   finest scale.
2. **Every measuring tool needs a self-test** with known answers: the reference itself, a moved copy, a blurred copy, a flat picture, other surfaces. Ours showed that
   two numbers in the project notes had drifted (0.17 -> 0.241, 0.1 -> 0.16 to 0.50).
3. **Measure the yardsticks of each new surface first** (flat normal, flat height, derivation ceiling, other-surface level): they say which tier is possible and which
   scores mean "nothing".
4. **Set colour management in every script that renders.** Standard for colour, Raw for data, 16-bit heights: the harness does it, a fresh scene does not.
5. **Look at the pictures.** Every blind spot in section 9 was found by someone looking, or by a second person re-running the numbers.

---

## 12. Tested for this guide, and not tested

TESTED for this guide (files in `cookbook/checks/baking_and_checking/`):
* the self-tests of both measuring tools on the brick reference, a slid copy, a blurred copy, a flat picture and the five other references, plus every reference
  against mud (`run_self_tests.py`, `self_tests.json`, `run_self_tests.log`); the two sheets of the slid copy (`pictures/checking-same-kind-sheet-slid-brick.jpg`,
  260 KB, and `pictures/checking-dot-for-dot-sheet-slid-brick.jpg`, 280 KB; the full-size PNGs were deleted to save disk);
* which reference height the same-kind tool reads, and what a smoothed height costs (`smoothed_height_check.py`, `.json`);
* the flat-map yardsticks of all six references (`flat_baselines.py`, `.json`);
* the view-transform strip in Blender 5.2.2, 8 renders at 256 dots, and its measurements (`view_transform_strip.py`, `view_transform_measure.py`,
  `view_transform_numbers.json`, `view_transform_tiles/`, `pictures/baking-strip-view-transform.jpg`, 135 KB);
* the audit on two real and three made-up descriptions (`audit_examples.py`, `audit_examples.json`, `audit_made_up/`);
* one harness run on the smoke recipe at 256 dots (`harness_smoke_256/`), and the harness's grey save (`save_grey_check.py`, `.log`);
* counts of harness calls in the builds' generators (grep).

Quoted, not re-run by me: everything from the research guide (the Bake button, colour spaces, bit depth, pixel filter, speed) and from the builds' reports and
checkers' findings, with the file named each time.

NOT TESTED: the harness at 1254 dots (the notes give about 20 seconds); the Bake button in any build; metal's filter-width-0.01 setting; whether the notes'
"0.17" and "about 0.1" came from the earlier same-kind tool; the same-kind score of slate, wood, metal or gravel new tiles against the OTHER references (done only for
mud); an edge band option for the dot-for-dot tool; any of this in EEVEE (no graphics card here).
