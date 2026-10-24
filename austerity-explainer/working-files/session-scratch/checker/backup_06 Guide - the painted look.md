# 06 Guide - the painted look

What this is: a guide to making a tile look HAND-PAINTED: flat patches of paint, a short palette, dark outlines, small repeated marks, ragged edges,
a slight staircase along every edge, and a little grain. For each tool it says what it is, how the six surface builds used it, what changing its
settings does to the picture, the traps found by testing, and, at the end, what did and did not give a hand-painted feel, with the numbers.
The companion guides are "06 Guide - pattern makers.md" and "06 Guide - shapers.md" (the shader nodes themselves) and "06 Guide - geometry nodes,
curves, modifiers and physics.md" (real relief).

## How to read this guide

Words used (one word for each thing, always):
* **tile** = the square picture we make; **dot** = one pixel of it (the references are 1254 x 1254 dots). **tile units** = distances in tiles (0.01 = 12.5 dots on a 1254 tile).
* **patch** = an area of one flat colour. **palette** = the short list of colours a surface is painted with. **level** = one flat grey value.
* **cell** = a Voronoi cell: the area nearer to one scattered seed point than to any other (Blender's Voronoi Texture node makes them).
* **outline** = a dark line along the edge of a patch or a piece; **shadow band** = a wider, less dark band on one side only.
* **stamp** = one small shape placed many times (a drip, a speck, a flake). A **made-up stamp** gets its place from a random seed; a **traced stamp**
  gets its place copied from the reference.
* **warp** = pushing the position around before a pattern reads it. **staircase** = the 1-2 dot steps along a painted edge.
* **grain** = a tiny random lighter-or-darker change at the size of 1 to 3 dots.
* **filter** = a compositor node that changes a finished picture (Kuwahara, Blur and others). **mask** = a grey value from 0 (not here) to 1 (here).
* **painter route** = the main route of all six builds: flat coloured shapes stacked back to front and photographed from above. **shader route** =
  a node recipe that works out every dot's colour on its own (the research demos).
* **same-kind score** = `lib/texture_compare.py` overall (1 = the same kind of surface; a re-shuffled copy of a reference about 0.99; other real
  reference surfaces 0.16 to 0.50, not "about 0.1": baking and checking guide, section 7.4). **dot-for-dot tool** = `lib/pixel_compare.py`: colour SSIM (1 = the same light-and-dark structure), colour difference (Delta E: about
  2.3 is "just visible"), edge skill (share of the reference's edges put within 2 dots), height error, normal error.

Labels: **TESTED** = run in Blender 5.2.2 here, with the file that shows it; **NOT TESTED** = only read or reasoned; **NEW** = run for this guide.
Every number is copied from the file named next to it.

Where the facts come from: `research/02 Research - getting a hand-painted stylised look.md` ("the painted-look research"; pictures, data and scripts in
`research/experiments_hand_painted_look/`); the six builds in `recipes/<surface>/` (`04 Recipe - ...` guides, `builder_answer.json` = the builder's
report, `verifier_answer.json` = an independent checker); `research/03 Research - Material Maker.md` and `research/03 Research - Ucupaint.md` for borrowed
ideas; and a NEW test: `cookbook/checks/geometry_and_painted_strips/make_painted_strips.py` (Blender) + `finish_strips.py` (measuring), numbers in
`numbers_painted.json` in the same folder, pictures `cookbook/pictures/painted-*.jpg`.

---

## 1. The short version

Example first. The painted-look research built a painted slate roof in shader nodes, one control at a time, and scored every stage
(`research/.../pictures/c12_slate_demo_stages.png`, research section 5.1). Plain soft-coloured tiles: same-kind 0.372. Adding painted patches of the
WRONG size: 0.270 (worse). Adding ragged edges: 0.278. Adding outlines (a 10-dot dark line, a 21-dot shadow band, 6-dot gaps, a 5-dot pale lip):
**0.486**. Adding stains: 0.506. Height blurred 0.8 dots: 0.555. Drip size taken from the measurements: **0.574**. A Kuwahara filter on top: 0.534.

![the slate demo, stage by stage](pictures/painted-slate-demo-stages.jpg)

(Small copy of `c12_slate_demo_stages.png`. Top: reference, plain, + patches, + ragged edges. Bottom: + outlines, + stains, + Kuwahara, tuned.)

What "painted" means in numbers (measured on the six references, painted-look research section 2): **85 to 94 % of strong edges change colour within
2 dots**; patches are **20 to 50 dots across** (area-weighted middle size); **8 palette colours** reproduce each reference to a colour difference of
3.1 to 4.5; dark outlines are about **5 dots (brick), 12 (slate), 8 (wood), 6 (metal), 3 (stones in mud and gravel)** wide; edges have a **1 to 2 dot
staircase**; inside a patch the lightness wobbles only 3 to 6 units of 100.

The rules that would have saved the most time:
1. **Outlines are worth more than anything else** (+0.21 on the slate demo in one step). Measure their width; draw them where the layout says.
2. **Measure the patch size first.** Patches of the wrong size scored WORSE than none (0.372 -> 0.270); sizes from measurements were the biggest step
   for gravel (0.346 -> 0.394).
3. **Posterise a grey value, then colour it.** The compositor's Posterize works per colour channel and turns brown into red, olive and black.
4. **Convert hex colours to linear numbers** before typing them into Blender, or every colour comes out about 73 steps of 255 too bright.
5. **Pick colours relative to the neighbours, by area, not one patch at a time from a chance table**, or you get camouflage confetti (brick, wood).
6. **Grain is a separate switch**: it raises the same-kind score and lowers the dot-for-dot scores (brick L: same-kind 0.432 -> 0.598, SSIM 0.673 -> 0.537).
7. **Every compositor filter breaks the tile's wrap.** Wrap-pad the picture, filter, cut the middle out: seam 2.61 -> 1.05.
8. **Kuwahara does not make an already flat picture more painted** (slate demo 0.506 -> 0.482).

---

## 2. Flat patches: cells and stepped values

**What they are:** two ways to get flat colour. **Stepped values** round a smooth grey value (a noise) to a few flat levels; **cells** split the tile
into Voronoi cells and give each cell one colour.

**Example first** (TESTED, painted-look research section 4.1): seamless noise -> Map Range 0.30..0.70 to 0..1 (the noise only uses the middle, so
stretch it first) -> Map Range set to **Stepped**, Steps 3 -> Color Ramp set to **Constant** with 4 palette colours = 4 flat patches with hard edges.

![five ways to get N flat levels](../research/experiments_hand_painted_look/pictures/c01_posterise_methods_all.png)

(Rows: Color Ramp Constant, Math Floor, Math Round, Math Snap, Map Range Stepped; columns N = 2, 3, 4, 6, 8, 16.)

| Method | Setting | Levels it gives | Levels for N = 4 |
|---|---|---|---|
| Color Ramp, **Constant**, N stops | N | N | 0, 0.33, 0.67, 1 |
| Math Floor (x times N, Floor, divide by N - 1) | N | N | 0, 0.33, 0.67, 1 |
| Math Round (x times (N - 1), Round, divide) | N | N (end levels half as wide) | 0, 0.33, 0.67, 1 |
| Math **Snap**, Increment 1/N | N | N, but it rounds DOWN, so the top is 1 - 1/N | 0, 0.25, 0.5, 0.75 |
| Map Range **Stepped**, Steps N | N | **N + 1** | 0, 0.25, 0.5, 0.75, 1 |

(`research/experiments_hand_painted_look/data/c01_posterise_levels.json`; counted with 1 sample and dither 0, because anti-aliasing and the PNG
dither add in-between values.)

**Cells as patches** (TESTED, research section 4.2): seamless Voronoi (`lib/recipe_tools.tileable_voronoi_group`) -> its **Color** output (a clean
random colour per cell) -> White Noise (a different "W" for every random number you need) -> Constant Color Ramp with the palette -> a little hue and
value jitter per cell.

![Voronoi cells as paint patches](../research/experiments_hand_painted_look/pictures/c02_cells_as_paint/strip.png)

(Raw cell colours; palette per cell; + hue and value jitter; + Scale 12; + warp 0.04.)

Settings: **Scale** = cells across the tile; a first guess is **Scale = 1254 / patch width in dots** (slate 25, brick 33, wood 40, gravel 55).
**Randomness** 0 = a square grid, 0.25-0.5 = brick-like, 0.75-1 = natural patches. Patches in **layers** (research 4.6): an underpainting, then 2 or 3
layers of smaller cells (Scale x 1.8 each) that cover only part of the tile (15 to 30 % reads as stains, 50 % and more covers the underpainting).
Five layers became confetti.

**How the builds made flat patches** (all TESTED):
* **The painter route (all six builds):** every patch is a flat polygon with one palette colour, photographed with an Emission material, so every dot
  of a patch is exactly that colour. Thousands of patches bake in seconds: brick class L, 12,555 shapes in about 20 s (brick recipe guide section 7).
* **Brick's mosaic for new walls** (`recipes/brick/generator/mosaic_tools.py`, numpy): cells cut by straight lines half way between jittered seed
  points, edges bent by a wobble that is the same for both cells sharing an edge (no gaps), four cell sizes laid on top (areas 1100, 320, 90 and 45
  dots; the smaller ones kept with a chance of 0.5, 0.35 and 0.22, so they only sprinkle).

![number of cell sizes](pictures/brick-strip-number-of-cell-sizes.png)

(One cell size: stained glass; two: patches; three and four (default): the small sprinkle that makes it look painted rather than cut.)

* **Metal's wear ladder** (`recipes/metal/generator/metal_generator.py`): seamless noise -> Map Range -> Math Multiply Add -> **Color Ramp Constant**,
  with every stop placed by MEASURING the noise so each colour covers the share found on the reference (steel 0.67 against 0.63 in the reference, rust
  0.156 against 0.184, dark 0.08 against 0.096; metal recipe guide 5.3).
* **Wood's dry-brush streaks** (`recipes/wood/generator/wood_shaders.py`): stretched seamless noise -> Map Range with a nearly zero-wide window = a
  hard cut ("above 0.58 = light streak"); a softness of 0.004 gives one-dot staircases (wood recipe guide section 6).

Traps (TESTED):
* **Posterise a grey value, not a colour.** The compositor's Posterize node at Steps 4 turned a brown picture into red, olive and black blotches,
  because it steps each colour channel on its own (`research/.../pictures/c06_other_nodes.png`).
* **Never hash the Voronoi Position output for a per-cell random number**: it jumps along straight lines inside a cell (vertical-edge share 0.49
  against 0.12 for the Color output; research section 3).
* **Map Range Stepped with Steps N gives N + 1 levels; Snap rounds down.**

---

## 3. Palettes: from the reference, as a guide

**What a palette is:** the short list of colours a surface is painted with, each with the share of the tile it covers.

**Example first** (TESTED, painted-look research section 2.1): snapping every dot of the brick reference to its nearest of 8 colours leaves an average
colour difference of 4.5, for slate 3.1. The eight brick colours and their shares:

![measured palettes of the six references](../research/experiments_hand_painted_look/pictures/a03_reference_palettes.png)

![the references snapped to 4, 8, 16 and 32 colours](pictures/painted-references-in-4-8-16-32-colours.jpg)

(Small copy of `a02_posterise_reference_all.png`. At 8 colours every surface still reads as itself: bricks and mortar, slate moss, wood knot, rust,
puddles, stones.)

| Surface | Colour difference with 4 / 8 / 16 / 32 colours | Darkest 1 % | Brightest 1 % | Most colourful 1 % |
|---|---|---|---|---|
| brick | 6.3 / 4.5 / 3.5 / 2.7 | #2b201b | #b09172 | #b15329 |
| slate | 4.5 / 3.1 / 2.3 / 1.8 | #070709 | #7a7975 | #4f4d36 (olive) |
| wood | 6.0 / 4.3 / 3.1 / 2.4 | #0f0a09 | #ae8361 | #a26f4a |
| metal | 5.0 / 3.8 / 2.8 / 2.2 | #0f0b09 | #817466 | #73401f (rust) |
| mud | 6.6 / 4.4 / 3.2 / 2.4 | #0f0a09 | #a18772 | #925f3c |
| gravel | 6.3 / 4.4 / 3.3 / 2.5 | #070707 | #91897d | #815637 |

(Research section 2.1 table. The "1 %" colours are accents that averaging hides.)

**How many colours the builds used, and what they found** (TESTED):

| Build | Palette | What it found | File |
|---|---|---|---|
| brick | 16 | 32 colours gave a LOWER colour SSIM at the same number of patches (0.609 against 0.658) | brick `builder_answer.json`, dead ends |
| slate | 24 (13 blue-greys, 5 olive mosses, 3 tan lichens, the joint black, a grey-green and a neutral grey) | 16 colours: colour difference 2.3; 24: 2.0 | slate recipe guide 2B |
| metal | 8 | 8 beat 16 and 24 at the same description size | metal `builder_answer.json`, dead ends |
| mud | 16 | the reference snapped to 16 colours still scores SSIM 0.916 | mud recipe guide section 2 |
| gravel | 8 stone + 8 soil tones; 24 for tracing | 8 colours: SSIM 0.855; 24: 0.923 | gravel recipe guide 2B |

**"As a guide", not as a recipe:** the palette tells you which colours exist and how much of each; HOW the colours are put next to each other is a
separate decision, and the builds found it matters more:
* **Pick by AREA, not by count.** Brick: thousands of tiny patches overweight a table counted per patch, and the first new walls looked like camouflage;
  area-weighted tables fixed it (brick lessons).
* **Pick relative to what is around.** Wood: a plain chance table of colours gave camouflage (same-kind 0.39 to 0.45); zones of slowly changing
  colour with strips coloured "the colour beneath plus a small change" gave 0.51 to 0.63 (wood `builder_answer.json`, dead ends). Brick and mud used a
  slow "tone dial" or "zone weight" so neighbouring patches belong together:

![zone weight](../recipes/mud/guide_pictures/strip_zone_weight.png)

(Mud: zone weight 0 to 0.97. At 0 every clod picks its colour alone and the ground is confetti; near 1 whole neighbourhoods share a tone. The build used 0.6.)

* **Write down which colours are accents.** Brick's first cobblestone transfer guessed the "chip" colours from low colour saturation and turned every
  grey cobble black (brick `builder_answer.json`, dead ends). Keep explicit lists (dirt, moss, chips).
* **Jitter brightness only.** Gravel: changing red, green and blue by separate random amounts made purple and green stones; the same amount on all
  three keeps the hue (gravel recipe guide section 4, step 14).
* **Take out slow gradients before measuring tone spreads** (slate: blue patches are 20.5 steps darker in the top sixth of a slate and 13 lighter in
  the bottom sixth; slate recipe guide 2B).

Trap (TESTED): **hex colours typed straight into a Color Ramp come out 73 steps (of 255) too bright**; convert sRGB to linear first
(`lib/recipe_tools.srgb_hex_to_linear`): 0 error for all 8 brick colours (research section 4.9, `data/c11_palette_checks.json`).

---

## 4. Outlines and their measured widths

**What an outline is:** a dark line along the edge of a patch or piece. On these references it is often paired with a **shadow band** on one side.

**Example first: the widths on the references** (TESTED, painted-look research section 2.4):

| Surface | What | Width | Colour |
|---|---|---|---|
| brick | dark rim round each brick, between face and mortar | about 5 dots (the rim itself 6-8) | lightness 24 (#3a2d27 to #2b201b) |
| slate | black line under every slate, then a lighter shadow band, plus dark gaps | 12 dots at half depth: core about 10, shadow band about 21 | #0e0f11 core, #1e2022 band |
| wood | dark cracks along the planks | about 8 (3 to 14) | #1c1513 |
| metal | dark seams round plates and bars | about 6 (3 to 17) | #1f1a18 |
| mud, gravel | thin dark rim round stones, puddle shores | about 3 (1.8 to 4.6) | #171617, #242125 |

The builds measured more closely: slate black band between rows 10.6 dots (spread 0.5), joints between slates 3.9 dots (slate recipe guide 2B);
**gravel has no dark rim on the stone at all: the soil next to a stone is darker** (lightness 24.6 at 1 dot from the stone, 31.4 at 8 dots, while the
stone's own edge is 20.0 against 21.2 inside), so it is a shadow on the soil (gravel recipe guide 2B). The research's "3-dot rim" was a shadow.

**Seven ways to draw an outline, with measured widths** (TESTED, research section 4.7, straight-edge calibration in `data/c05e_width_calibration.json`):

| Route | Setting | Width measured (dots) for settings 1, 2, 3, 4, 6, 8 | Cost on a 384-dot tile (the pattern alone 1.05 s) |
|---|---|---|---|
| **from the layout** (you know where rows and pieces are) | width w | exact | free |
| **offset samples, 2** (+u, +v): mark where the patch number changes a few dots away | shift w | 1, 2, 3, 4, 6, 8 (one-sided, like a drop shadow) | 2.6 s |
| **offset samples, 4** (+-u, +-v) | shift w | 2, 4, 6, 8, 12, 16 (centred) | 4.2 s |
| **Voronoi Distance To Edge** below a threshold | (w / 2) x Scale / 1254 | 1, 2, 3, 5, 7, 9 | 2.5 s |
| **Bump node** on the patch number | Filter Width w / 2 | 1, 1, 1, 1.5, 2, 3 (thin, weak) | 2.6 s |
| compositor: Filter Sobel + threshold, then Dilate/Erode or Mask To SDF | Distance 1-4 / less than 1-4 | 5, 7, 10, 12 / 3, 6, 9, 12 | 0.2 s / 0.6 s at 1254 |
| real geometry: ambient occlusion, Bevel, Pointiness | | soft shadows, faint lines | 2 to 18 s at 512 |

![outline routes side by side](pictures/painted-outline-methods-sheet.jpg)

(Small copy of `c05_outline_methods_sheet.png`. Top four rows: cells with Distance To Edge, 2 offset samples, 4 offset samples, Bump, each at width
1, 2, 4, 8. Bottom three rows: the same routes on posterised noise: every level change draws a line, so wide offsets turn into black noise.)

**How the builds drew outlines** (TESTED):
* **Brick: a ring with a hole, drawn on top of every brick** (`recipes/brick/generator/shape_stack.py`, filled by `mathutils.geometry.tessellate_polygon`).
  Its reach was set by eye from a measured profile: 1 dot into the brick on three sides and 1.5 at the bottom; 1 dot out at the left, 0 at the top,
  1.5 at the right and 3 at the bottom (a thin line at top and left, a shadow band below and right; brick recipe guide 2B).

![brick outline ring width](pictures/brick-strip-outline-ring-width.png)

(No ring: the bricks look stuck on. x1: a hairline. x2 (default): the reference's ink line with a shadow band below. x4 and x7: a heavy cartoon outline.)
Measured on class M (brick recipe guide section 4, tool 9): the ring raised edge skill 0.357 -> 0.421, colour SSIM 0.535 -> 0.552 and the same-kind
score 0.308 -> 0.406. **On top of traced patches it made things slightly WORSE** (SSIM 0.641 -> 0.636): the traced patches already hold the dark lines.
* **Slate: the joints are part of the layout** (rows, joints with a gap and a lean, ragged edges). Layout alone already scored colour SSIM 0.711
  (slate recipe guide section 0); the joints are 7 % of the dots but decide most of the edge measures (slate lessons).
* **Gravel: a shadow on the soil plus a thin rim** under every stone (shadow 6 dots wide for a stone of radius 20; rim 0.8 dots in 0.45 x the body colour).

![shadow on the soil](../recipes/gravel/guide_pictures/strip_shadow_width.png)

(None: stones float like stickers. 6 (used): the reference's dark band. 10 and 16: the soil is buried in black.) Shadow, rim, facets and flakes
together added +0.085 to the same-kind score (0.352 -> 0.437; gravel recipe guide section 5).
* **Metal: shading along every bar edge copied from measured edge profiles** (a dark line and a bright line): colour SSIM 0.613 -> 0.649, edge skill
  0.00 -> 0.15 (metal `builder_answer.json`, layers).

**NEW test: an outline from a soft edge** (the Ucupaint "transition ramp" idea, which the Ucupaint research read about but did not get to draw an
outline, `research/03 Research - Ucupaint.md` sections 4.7 and 7). The recipe: seamless noise -> Map Range from 0.5 - softness to 0.5 + softness = a mask
m with a soft edge -> two flat patches (m above or below 0.5) -> band = 1 - |2m - 1| (1 on the edge, 0 where the mask is fully on or off) -> paint dark
where the band is above 1 - share. "Share" = how much of the soft edge is painted dark.

![outline band from a soft edge: share](pictures/painted-strip-outline-band-share.jpg)

![outline band from a soft edge: softness](pictures/painted-strip-outline-band-softness.jpg)

Measured on 512-dot renders with 1 sample (`numbers_painted.json`; width = twice the distance from the patch edge to the nearest non-line dot, minus 1;
converted to dots of a 1254 tile):

| Share (softness 0.05) | Dark share of the picture | Line width, 10 % / middle / 90 % of the edge (1254 dots) | Line dots that are islands away from any edge |
|---|---|---|---|
| 0 | 0 | no line | - |
| 0.1 | 3.5 % | 2.4 / 7.3 / 15.2 | 1.5 % |
| 0.25 | 8.8 % | 11.3 / 18.1 / 34.7 | 8.5 % |
| 0.5 | 18.8 % | 24.0 / 37.7 / 64.1 | 32.1 % |
| 1.0 | 41.4 % | 52.4 / 78.8 / 121.0 | 65.8 % |

What it says: it works and it is seamless (it is built from seamless noise), every edge dot got a line (share of edge dots with a line 1.0 at every
share above 0), and **the line is very uneven**: at share 0.1 the thickest tenth of the edge is about 6 times as wide as the thinnest tenth. The reason
(from the formula, not measured): the line covers the dots where the noise lies within softness x share of 0.5, so it is wide where the noise changes
slowly and thin where it changes fast; softness and share act the same way (the softness strip shows the same thickening by eye; not measured). From
share 0.5 up, dark islands appear far from any edge, where the noise hovers near 0.5. **Verdict:** a lively, hand-inked line for organic patches (rust,
moss, puddles) at a small share; NOT a way to hit a measured width like the brick's 5 dots. For a measured width use the layout or offset samples.
Not tested: the same band added to the height ("edge bump", Ucupaint idea 2), and this band on the builds' surfaces.

---

## 5. Stamps

**What a stamp is:** one small shape placed many times: a drip, a speck, a flake, a blob. The shape is fixed; the generator chooses where each copy
goes, how big, which way round and which colour.

**Example first** (TESTED, slate recipe guide sections 4 and 0): the slate's paint is made-up stamps: thin upright pointed drips in six size classes,
scattered from measured statistics (how much of a slate each size class covers, which colour family, how the tone changes from the top of a slate to
the bottom). Layout alone scored same-kind 0.40; layout + stamps (6.4 KB) 0.71: **the right kind of surface**. Dot for dot it was no better (colour SSIM
0.569; the checker corrected the builder's 0.60): made-up stamps are not where the real paint is.

![patch outline style](../recipes/slate/guide_pictures/strip_stamp_shape.png)

(Slate: plain spiky blobs look like spots; upright drips (used) look like paint run down a wall.)

![number of small stamps](../recipes/slate/guide_pictures/strip_small_patch_count.png)

(Slate: without tiny and small stamps the roof looks too clean; double the number and it looks sandy.)

Settings the slate build tuned: **tone noise** (how random each stamp's tone is: 0 clean layered blue-greys, 1.5 speckled camouflage, 0.4 used),
**drift** (a slow wave of lighter and darker over each slate, so neighbouring stamps belong together: 0 flat, 12 used, 40 patchwork), contrast 1.4.
Nine runs of tone noise 0.25-0.55 and drift 9-20 all scored 0.70 to 0.73: a flat plateau, so the picture, not the score, chose the values.

**Other stamps in the builds** (TESTED):
* **Brick blobs:** ragged ellipses, 8 numbers each (middle, two radii, turn, colour, raggedness, seed). Per kilobyte they beat traced outlines up to
  about 300-400 KB: at 195 KB blobs gave colour SSIM 0.592 and edge skill 0.555, traced patches 0.566 and 0.380 (brick recipe guide section 5).
* **Gravel flakes:** about 0.7 flakes per dot of stone radius on stones of radius 8 or more, 8 to 22 steps lighter or darker.

![flakes on stones](../recipes/gravel/guide_pictures/strip_flaky_patches.png)

(None: the stones are flat plastic; 0.7 (used): broken, painted; 2.2: speckled like granite.)
* **Gravel traced stamps:** tiny discs copied from the reference, 3 numbers each (x, y, radius), found as the dots where the drawn patches still
  disagreed with the palette picture. Adding about 18,000 of them to the patches over 250 dots lifted edge skill from 0.114 to 0.593 for 185 KB more,
  where making the patch outlines 2.5 times finer lifted it only to 0.242 (gravel recipe guide section 5). Stamps are the cheap way to say "many tiny specks".

Dead end (TESTED, slate `builder_answer.json`): a stamp library of 32 REAL patch outlines instead of made-up drips scored 0.692 against 0.707 and cost
2.7 KB more.

**Borrowed idea, NOT TESTED: Material Maker's Tiler and Splatter.** The same job done per dot inside a shader: cut the tile into cells, give each cell a
random offset, turn, size and brightness, and let every dot look at its neighbouring cells to see which copy of the stamp it falls in (keep the
brightest); extra outputs give each copy its own colour and its own coordinates (`research/03 Research - Material Maker.md`). It would let a shader
route scatter stamps without a list. Blender shader nodes have no loop, so the neighbouring cells would have to be written out one by one; nobody here
built it. The builds placed stamps in plain Python (painter route) or with Instance on Points (see the geometry guide, section 4).

---

## 6. Ragged edges by domain warping

**What a warp is:** adding a small noise-driven push to the position before a pattern reads it, so straight or smooth edges come out bent. Big slow
warps make shapes organic; tiny fast warps make ragged paint edges.

**Example first** (TESTED, research section 4.3): seamless Voronoi cells, with the position pushed by a seamless noise of Scale 48 by a small Amount:

![ragged paint edges](../research/experiments_hand_painted_look/pictures/c03_ragged_edges/strip.png)

(Amount 0, 0.003, 0.006, 0.01, 0.016, 0.025: clean cells; a hand-cut edge; at 0.016 and up the patches fray.)

Settings: **Amount** = roughly the largest push in tile units (0.004 is about 5 dots at the largest push); **Scale** = features of the warp noise
across the tile: 1 to 4 moves whole patches (smooth shapes), 16 to 32 at Amount 0.05 tears patches into blots, **40 to 70 at Amount 0.004 to 0.01 gives
the thin ragged edge of the references**. Two warps in a row (coarse Amount 0.012 Scale 5, then fine 0.004 Scale 70) is what the slate demo used.
Helper: `lib/contrib/hp_tools.py warp_vector_group`.

**Seamless only if the warp noise repeats** (TESTED, `data/c02_c03_periodicity.json`): after a warp with the repeating noise 0.8 to 0.95 % of dots
differed in the 2 x 2 test (one-dot edge flips, the same as with no warp); with Blender's plain Noise, 90 %.

How much it bought, honestly: in the slate demo the ragged-edge stage moved the same-kind score only from 0.270 to 0.278 (research 5.1), within the
0.01-0.03 noise of one seed. **The builds made ragged edges without a warp**, by bending polygon outlines in Python: slate edge raggedness 2.06 dots
(sides) measured on the reference; brick mosaic wobble 1.3 dots; brick blob raggedness 0.1 to 0.9 per blob.

![edge raggedness on the slate](../recipes/slate/guide_pictures/strip_edge_roughness.png)

(Slate raggedness 0 / x1 / x4: ruler-straight edges, a clean diagram; the reference's chipped look; a crumbling roof.)

---

## 7. The staircase: the 400 grid, and Cycles samples

**What the staircase is:** the references' edges are not smooth curves; they run in short straight steps of 1 to 2 dots, like a hand-placed brush on a
grid. Measured: the median straight run along a patch edge is 1 dot for brick, metal, mud and gravel and 2 dots for slate and wood
(`data/a06_stair_steps.json`).

**Example first** (TESTED, research section 4.4): before the cells read the position, round the position to a grid: Vector Math Scale x G -> Floor
-> Scale x 1/G. G = squares across the tile.

![coordinate snapped to a grid](../research/experiments_hand_painted_look/pictures/c16_coordinate_snap/strip.png)

(No snap; grid 400 (3-dot blocks); 250; 160; 100; 60 (21-dot blocks). 300 x 300 dot crops of 1254 tiles.)

Measured staircase run: no snap 1 dot; G = 400: 2; G = 250: 3; G = 100: 3 and longer on average. So **about 400 matches the references; 5-dot blocks and
bigger are blockier than the references.** **Whole numbers only:** G = 400, 250 and 100 repeat (2.7 % of dots differ in the 2 x 2 test, the same as
unsnapped); G = 250.5 gave 5.2 %.

**The builds did not use the snap.** Their edges are polygon edges, and the staircase came from the renderer: **Cycles samples** decide how an edge dot
is shared between two colours. 1 sample = a hard staircase (a dot is in or out); 16 = a clean one-dot soft edge.

![Cycles samples on a polygon edge](../recipes/slate/guide_pictures/strip_samples_zoom.png)

(Slate, 4 times zoomed: 1, 2, 4 and 16 samples.) It mattered little to the scores: on metal, 16 samples against 1 moved colour SSIM 0.717 against
0.701 and edge skill 0.528 against 0.535 (metal recipe guide 5.2, an early test). The builds used 8 or 16 samples for colour.

---

## 8. Grain

**What grain is:** a tiny random lighter-or-darker change given to every dot or to every 1-3 dot speck, on top of the flat patches.

**Example first** (TESTED, brick recipe guide section 4, tool 7): Geometry (Position) -> Vector Math Scale (x 1254) -> Floor (whole dots) -> White Noise
-> Map Range onto a range round 1 whose spread is the "amount" -> Mix (Multiply) with the patch colour. Amount 0.10 makes a typical dot 10 % lighter or
darker than its patch. Reading WHOLE-dot positions makes the grain repeat exactly across the tile edge.

![grain amount](pictures/brick-strip-grain-amount.png)

(0: flat painted patches; 0.05: a faint tooth; 0.10: clearly grainy; 0.15: close to the 0.14 of new brick walls; 0.25: sandpaper.)

![metal grain at full size](../recipes/metal/guide_pictures/strip_grain_zoom.png)

(Metal, 300 x 300 dots at full size: grain 0, 0.04, 0.08, 0.16, 0.3. The metal build uses 0.12.)

**What grain did to the scores** (TESTED):

| Build | Grain | Same-kind score | Dot-for-dot | File |
|---|---|---|---|---|
| brick, class L (traced) | 0 / 0.10 / 0.14 | 0.432 / 0.555 / 0.598 | colour SSIM 0.673 / 0.593 / 0.537 | brick recipe guide section 0 |
| brick, new tile 14 | 0.14 against 0 | 0.730 against 0.576 | | brick recipe guide section 4, tool 7 (the no-grain bake used 16 samples instead of 8) |
| slate S1 -> S2 | faint seamless noise in the HEIGHT only (2 brightness steps, 800 bumps across) | 0.707 -> 0.725 (normal part 0.51 -> 0.57) | normal error 1 degree worse | slate recipe guide section 4, tool 9 |
| wood S1 | dry-brush streaks and hair lines (the wood build calls them "grain") | 0.425 -> 0.635 | | wood recipe guide section 6 |
| wood L2 (traced) | the same | 0.459 -> 0.763 | colour SSIM 0.674 -> 0.509 | wood `builder_answer.json` |
| research gravel demo | brightness jitter 0.35 per stone + grain 0.15 | 0.394 -> 0.417 | | painted-look research 5.2 |

**The lesson, in the brick builder's words:** two goals pull in opposite directions at the finest scale. Random grain cannot be the reference's grain
dot for dot, so the dot-for-dot measures fall while the same-kind score rises. **Keep grain a separate switch and say which goal it is set for.**

Corrections found by the checkers (TESTED):
* Part of brick's L + grain gain is a measuring effect: grain makes the normal jump between neighbouring dots bigger, so the tool's seam measure falls
  from 2.11 to 1.0 and its "tiling" part rises from 0.444 to 1.0, worth about 0.04 of the 0.165 gain. The grain fixes no seam (brick `verifier_answer.json`).
* On metal, the half-tile test difference of 3.2 came from the grain (white noise read at the jittered sample positions), not from colour thresholds;
  with grain 0 it fell to 0.71 (metal `verifier_answer.json`).
* On slate, the half-tile test of the height is not meaningful with grain on: the grain stays put while the shapes slide (slate `verifier_answer.json`).

Why grain helps the look at all: the references are not perfectly flat inside a patch (3 to 6 lightness units of wobble, research 2.3). A tile of
perfectly flat palette colours has a spiky brightness histogram (one spike per colour) where the reference's is smooth (research pitfall 16; gravel
recipe guide section 5: "the soil is one flat brown with a sharp spike").

---

## 9. Kuwahara and other compositor filters, with wrap padding

**What Kuwahara is:** a compositor filter that replaces every dot with the average colour of the calmest part of its neighbourhood. Grainy colour
becomes flat patches; strong edges stay sharp. "Classic" uses square parts (blocky, fast); "Anisotropic" follows the direction of the edges (brush-like, slow).

**Example first** (TESTED, research section 4.10): flat cells covered in fine grain, 1254 dots, Kuwahara Anisotropic Size 8: the grain is flattened into
smooth blobs, the cell borders stay sharp, 5.3 s.

![Kuwahara anisotropic, Size and chained passes](pictures/painted-kuwahara-anisotropic-size.jpg)

![Kuwahara classic, Size, High Precision, chained passes](pictures/painted-kuwahara-classic-size.jpg)

(Small copies of `c06_kuwahara_aniso_size.png` and `c06_kuwahara_classic.png`; 420-dot crops. The times printed in the picture come from one run;
the times below are the research text's.)

Settings and times at 1254 dots, CPU, 2 threads:
* **Size** (in dots): Classic 1-3 changes little, 5 and up makes square-ish blocks (0.4 s at Size 8; High Precision 0.76 s, slightly cleaner).
  Anisotropic 8 and up flattens grain into brush-like blobs: 0.8 s (Size 2), 1.7 (4), 3.2 (6), 5.3 (8), 11.3 (12), 19 s (16). Each chained pass adds
  the same time again.
* **Sharpness** 0 blurs everything including edges; **1.0 keeps edges crisp** (use 1). Uniformity (0-16) and Eccentricity (0-3) changed little.
* Size is in dots, so a setting for 1254 is too small for 2048 (NOT TESTED; scale it with the picture).

**Every filter breaks the tile's wrap** (TESTED, `data/c08_compositor_seams.json`): the jump across the wrap-around edge, as a multiple of a normal
dot-to-dot jump (the source: 0.96), was 1.95 / 2.61 / 3.66 after Anisotropic Size 4 / 8 / 16 and 1.39 / 2.08 / 4.29 after Classic. The damage sits within
about 5 dots of the edge. **Fix: wrap-pad** (repeat the picture round itself, `np.pad(picture, ((m, m), (m, m), (0, 0)), mode='wrap')`, or bake a
wider area), filter, cut the middle out: **1.05** with a 96-dot margin for Size 8. Smaller margins were not tested. The compositor's own
"Extension: Repeat" did NOT fix it (seam unchanged at 2.61).

![filter seam and the wrap-padding fix](pictures/painted-filter-seam-and-wrap-padding.jpg)

(A: the plain tile filtered, a seam at the cross. B: padded, filtered, cut out: no seam. C: the compositor-only padding attempt. Small copy of
`c08_seam_fix_sheet.png`.)

The other stylising filters (TESTED, research 4.10): **Posterize** works per colour channel (wrong for a painted palette); **Pixelate** 8 dots and up
is an obvious mosaic; **Bilateral Blur** needs its Determinator socket linked to the picture itself, then Size 4-8 at Threshold 0.05 softens grain and
keeps edges (unlinked it is a plain blur); **Filter** Sobel, Prewitt, Kirsch, Laplace find edges, Box and Diamond Sharpen bring grain BACK; **Despeckle**
barely changed the grain; **Dilate/Erode** and **Mask To SDF** widen a line (section 4).

![Bilateral Blur with the Determinator linked](../research/experiments_hand_painted_look/pictures/c06_compositor/bilateral_determinator/strip.png)

**Running the compositor headless in 5.2** (TESTED; `lib/contrib/hp_tools.py run_compositor`): `scene.render.compositor_device = 'CPU'` (the default
'GPU' fails here with a libEGL error); the tree is its own data block, `scene.compositing_node_group`, ending in a Group Output (the Composite node is
gone since 5.0); every setting is an input socket, and menu sockets take the option name as text (`inputs['Type'].default_value = 'Anisotropic'`).
Filter heights in 16-bit: a Classic pass on a 16-bit height kept 23,292 distinct values, saved 8-bit only 115.

**Where it helps and where it does not:** on a grainy or noisy source it makes flat patches and keeps edges. On a picture that is already flat it
removes detail: the slate demo went 0.506 -> 0.482 (and 0.555 -> 0.534 with the height blurred). **No surface build used the compositor.** (The brick
builder smoothed the reference with a bilateral filter in plain Python before squeezing it to 16 colours, in the ANALYSIS only: 0.683 against 0.658.)

---

## 10. What did and did not give a hand-painted feel

**Did** (each TESTED, numbers from the file named):

| Change | Effect | File |
|---|---|---|
| outlines from the layout (slate demo: 10-dot core, 21-dot shadow band, 6-dot gaps, 5-dot lip) | same-kind 0.278 -> 0.486, edge density 2.5 % -> 7.0 % (reference 8.8 %) | painted-look research 5.1 |
| brick outline ring | edge skill 0.357 -> 0.421, same-kind 0.308 -> 0.406 | brick recipe guide section 4 |
| gravel shadow, rim, facets and flakes | same-kind 0.352 -> 0.437 for no extra bytes | gravel recipe guide section 5 |
| stamps from measured statistics (slate) | same-kind 0.40 -> 0.71 | slate recipe guide section 0 |
| patch sizes taken from the measurements (gravel demo) | 0.346 -> 0.394; correlation length 24 -> 7 dots (reference 8) | painted-look research 5.2 |
| drips 2 : 1 instead of 7 : 1 (slate demo) | 0.555 -> 0.574 | painted-look research 5.1 |
| colour-relative paint: zones + "colour beneath plus a change" strips (wood) | 0.39-0.45 -> 0.51-0.63 | wood `builder_answer.json` |
| area-weighted colour tables, a slow tone dial, clouds solid in the middle (brick) | ended the confetti and camouflage look (by eye) | brick `builder_answer.json`, dead ends |
| several cell sizes layered (brick mosaic) | 1 size = stained glass, 3-4 = painted sprinkle (by eye, strip in section 2) | brick recipe guide section 4 |
| grain, as a separate switch | same-kind up, dot-for-dot down (section 8) | |
| height made from the FINISHED colour, blurred 0.8 dots, normal made from it | slate demo 0.506 -> 0.555; the "normal agrees with the height slope" part 0.00 -> 0.45 | painted-look research 5.1 and section 1, fact 12 |

**Did not** (each TESTED):

| Change | What happened | File |
|---|---|---|
| painted patches of the wrong size | slate demo 0.372 -> 0.270 (worse than none) | painted-look research 5.1 |
| Kuwahara on an already flat picture | 0.506 -> 0.482 | painted-look research 5.1 |
| Posterize node on a coloured picture | red, olive and black blotches | painted-look research 4.10 |
| colours picked per patch from a chance table | camouflage (wood 0.39-0.45; brick "camouflage-like") | wood and brick `builder_answer.json` |
| independent red / green / blue jitter | purple and green stones | gravel recipe guide section 9 |
| 32 colours instead of 16 (brick) | colour SSIM 0.609 against 0.658 | brick `builder_answer.json` |
| outline ring on top of traced patches | SSIM 0.641 -> 0.636 | brick `builder_answer.json` |
| a library of 32 real patch outlines as stamps | 0.692 against 0.707 for made-up drips | slate `builder_answer.json` |
| Voronoi Distance To Edge "hair lines" on a stretched cell pattern | diagonal criss-cross lines; contour lines of stretched noise worked | wood `builder_answer.json` |
| tuning metal toward the score with large-scale tone and less grain | 0.516 -> 0.454 -> 0.410 (reverted) | metal `builder_answer.json` |
| the real-geometry colour (soft ambient-occlusion shading) | slate same-kind 0.32-0.37 against 0.71 for painted stamps | slate recipe guide section 7 |
| Gabor noise for brush strokes | low-contrast bands, not strokes, and it does not tile (45 % of dots differ) | painted-look research 4.5 |
| invented clods on the mud ground | same-kind up (0.22 with ruts only -> 0.267) but normal error 28 degrees against 23.5 for flat ground, SSIM 0.367 | mud `builder_answer.json` |

**What is still missing, honestly** (the checkers and the builders agree): the made-up tiles read as the right kind of surface but not as equally
good. Brick: "the brick faces carry a fine confetti of small cells that the reference does not have; the big flat hand-painted patches are missing"
(brick `verifier_answer.json`). Wood: "weak planks and cracks, faint knots, blocky camouflage paint" (wood `verifier_answer.json`). Gravel: stones
smaller and flatter than the reference's chunky blocks (gravel recipe guide section 5). Every tile that reaches the dot-for-dot tier "layout" or "close"
is a TRACE of the reference or a FIT to it (brick's S and M place ellipses fitted to the reference's patches), not a recipe.

![the gravel demo: earth, first stone sizes, measured sizes, + jitter and grain](pictures/painted-gravel-demo-stages.jpg)

(Small copy of `c17_gravel_demo_stages.png`: reference, earth only 0.23, first sizes 0.35, sizes from the measurements 0.39, + brightness jitter and
grain 0.42. Still clearly a Voronoi patchwork next to the reference's angular crystals.)

---

## 11. Traps (all met by testing)

1. Patches of the right kind but the wrong size score worse than none (section 1).
2. Posterize works per colour channel (section 2).
3. Hex colours must be converted to linear numbers: 73 steps too bright otherwise (section 3).
4. Voronoi Position hashed into a random number cuts straight lines through cells; use the Color output (section 2).
5. Map Range Stepped gives N + 1 levels; Snap rounds down (section 2).
6. Counting flat levels needs 1 sample and dither 0 (section 2).
7. A warp keeps the tile seamless only if the warp noise repeats (section 6).
8. Snap grids must be whole numbers (section 7).
9. Every compositor filter breaks the wrap; pad first; "Extension: Repeat" does not fix it (section 9).
10. The compositor needs `compositor_device = 'CPU'` headless; settings are sockets (section 9).
11. Bilateral Blur without its Determinator is a plain blur (section 9).
12. 8-bit heights lose the slopes: filter and save heights in 16-bit (section 9).
13. Grain makes the seam measure look better without fixing anything (section 8).
14. A soft-edge outline band is uneven and makes islands from share 0.5 up (NEW, section 4).
15. An outline ring on top of traced patches doubles the lines (section 4).
16. A "same-kind" gain bought by tuning one layer can drop elsewhere; check by eye and stop when two rounds gain nothing (metal, section 10).
17. `lib/bake_harness.save_array_png` writes a one-channel array into the red channel only; pass 3 channels (painted-look research pitfall 10).

---

## 12. Recipe cards (every line was run, except where it says NOT TESTED)

**Card 1 - Flat palette patches (shader route).** Seamless Voronoi (Scale = 1254 / patch width in dots, Randomness 0.75-1) -> Color output -> White
Noise (4D) -> Constant Color Ramp (palette converted to linear, sorted dark to light, stop length = share) -> Hue/Saturation (Hue 0.5 + (r - 0.5) x 0.04,
Value 1 + (r2 - 0.5) x 0.35). (painted-look research R1)

**Card 2 - Flat patches (painter route).** Every patch a flat polygon with one palette colour, stacked a hair apart, photographed with Emission and
the Standard view; colours by area-weighted tables, picked relative to a slow tone field; 8 to 16 samples. (all six builds)

**Card 3 - Ragged edges.** Before the pattern reads the position: a coarse warp (Scale 4-5, Amount 0.012), then a fine one (Scale 40-70, Amount
0.004-0.01), both with REPEATING noise. Or bend the polygon outline by about 2 dots (slate raggedness 2.06). (research R2; slate build)

**Card 4 - The staircase.** After the warp: Vector Math Scale x 400, Floor, Scale x 1/400 (whole number). Painter route: 1 sample gives a hard
staircase, 16 a clean one-dot edge. (research R3)

**Card 5 - Outlines with a known width.** Known layout: draw the line from the row and piece fractions (slate: core 10 dots, shadow band 21, gaps 6)
or as a ring polygon with a hole (brick: thin top and left, shadow band bottom and right). Cells: Distance To Edge below (w / 2) x Scale / 1254. Any
flat-level pattern: 2 offset samples (one-sided, exactly w) or 4 (centred, exactly 2w). Stones: a dark shadow on the ground next to the stone, about
6 dots for a stone of radius 20, plus a 0.8-dot rim. (research R6; brick, slate, gravel builds)

**Card 6 - A lively hand-inked line on organic patches (NEW).** Soft mask m (Map Range of seamless noise, softness 0.05) -> band = 1 - |2m - 1| ->
dark where band > 1 - share; share 0.1 to 0.25 (middle width 7 to 18 dots at 1254, very uneven by design). (`make_painted_strips.py`)

**Card 7 - Stamps.** Made-up: one drip or speck shape, counts per size class calibrated to the share that stays VISIBLE, tone from the colour beneath
plus a slow drift. Traced: 3 numbers per speck (x, y, radius), found where the drawn picture still disagrees with the palette picture. (slate, gravel)

**Card 8 - Grain as a switch.** Whole-dot position -> White Noise -> Map Range round 1 (spread 0.10-0.14) -> Multiply. On for new tiles, off for
dot-for-dot copies. Brightness only, never per channel. (brick, metal)

**Card 9 - Kuwahara on a grainy bake.** Wrap-pad by 96 dots, Kuwahara Anisotropic Size 8, Sharpness 1, Uniformity 4, Eccentricity 1, cut the middle
out, make the height again from the new colour. Only for grainy sources. (research R9)

**Card 10 - Maps from the finished colour.** Height = brightness of the finished colour (stretch fitted per surface), blurred about 0.5-0.8 dots with a
blur that wraps round the edge, 16-bit; normal = slope of that height at the strength fitted on the reference (brick 6, slate 7, wood 8, metal 5,
mud 9, gravel 10). (every build)

---

## 13. What was tested and what was not; files

**Tested:** everything marked TESTED, in the painted-look research's scripts (`research/experiments_hand_painted_look/scripts/`, its `hp_tools.py` is
`lib/contrib/hp_tools.py`) and in the six builds' generators (`recipes/<surface>/generator/`). The checkers re-baked the builds' classes in fresh
Blender runs and got the same scores (each `verifier_answer.json`).

**NEW for this guide** (`cookbook/checks/geometry_and_painted_strips/`): `make_painted_strips.py` (the soft-edge outline band: five shares and three
softness values at 256 dots for the strips, five shares at 512 dots with 1 sample for measuring; about 4 s of rendering), `finish_strips.py`
(measuring, white gaps, small JPG copies), numbers in `numbers_painted.json`.

**Not tested:** the 400 grid snap and Kuwahara inside any surface build (both were tested only in the research demos); Kuwahara at other resolutions
and smaller wrap-pad margins; Material Maker's Tiler, Splatter and generalised Kuwahara; Ucupaint's "edge bump"; the soft-edge band on a real build;
Convolve, Anti-Aliasing, Inpaint, Glare and Denoise as stylising filters; Grease Pencil, Freestyle and Shader to RGB outlines (Shader to RGB gives
plain white in Cycles, found by the shader-toolbox research); EEVEE (no graphics card); any result on a second seed.

**Pictures used** (small copies in `cookbook/pictures/`, made by `finish_strips.py`; originals unchanged): `painted-slate-demo-stages.jpg`
(`research/experiments_hand_painted_look/pictures/c12_slate_demo_stages.png`), `painted-references-in-4-8-16-32-colours.jpg` (`a02_posterise_reference_all.png`),
`painted-outline-methods-sheet.jpg` (`c05_outline_methods_sheet.png`), `painted-kuwahara-anisotropic-size.jpg` (`c06_kuwahara_aniso_size.png`),
`painted-kuwahara-classic-size.jpg` (`c06_kuwahara_classic.png`), `painted-filter-seam-and-wrap-padding.jpg` (`c08_seam_fix_sheet.png`),
`painted-gravel-demo-stages.jpg` (`c17_gravel_demo_stages.png`), and the NEW `painted-strip-outline-band-share.jpg` and
`painted-strip-outline-band-softness.jpg`. All other pictures are linked where they already were.
