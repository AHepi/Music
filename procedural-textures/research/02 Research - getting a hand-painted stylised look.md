# 02 Research - getting a hand-painted stylised look (Blender 5.2)

What this is: a plain-language guide to making a picture look HAND-PAINTED with Blender's procedural tools: flat patches of paint, hard edges, dark outlines,
a small set of colours, short brush streaks. It says what each tool does, which settings change what, and how close it gets to the six reference pictures.
It also gives the builders a MEASURED "look specification" for each surface (palette, patch size, outline width, edge hardness, streak direction, contrast),
worked out by running numbers on the reference pictures.
Everything marked TESTED was run in Blender 5.2.2 LTS on this machine (command line, CPU Cycles, CPU compositor). Pictures and scripts are in
`experiments_hand_painted_look/` (pictures in `pictures/`, numbers in `data/`, scripts in `scripts/`).

How to read the labels
- **TESTED** = I ran it and looked at the picture or the numbers.
- **NOT TESTED** = only read, or not tried.
- **WEB ONLY** = a web page says it; I did not check it (or could not).
- "Tile" = the flat square picture we bake (1254 x 1254 pixels for the references). "u" and "v" = how far across and up the tile you are, from 0 to 1.
- "Patch" = one area of one flat colour. "Layer" = a set of patches painted on top of another. "Outline" = a dark line around a patch.
- "Palette" = the short list of colours a surface is painted with. "Level" = one flat grey value.
- "Warp" = pushing the coordinate around before a pattern reads it. "Snap" = rounding a number to a grid. "Streak" = a long thin mark.
- Pixel sizes always mean pixels on a 1254 tile (for a 2048 tile multiply by 1.63).

---

## 1. The short version (read this first)

**What "hand-painted" means here, in numbers (measured on the six references, section 2):**
- The colour is built from flat patches with HARD edges: 85 to 94 percent of the strong edges go from one colour to the next within 2 pixels. Inside a patch the lightness wobbles only 3 to 6 units (of 100).
- The typical patch is 20 to 50 pixels across (area-weighted median), with many tiny specks of about 7 pixels.
- A short palette is enough: snapping every pixel of a reference to its nearest of 8 palette colours leaves an average colour error of only 3.1 (slate) to 4.5 (brick, wood, mud, gravel) on a scale where about 2.3 is "just visible" (a rule of thumb, not checked here) (section 2.2, picture `pictures/a02_posterise_reference_all.png`).
- Dark outlines: 5 pixels wide at the brick joints, 12 at the slate (a 10 pixel line plus a 21 pixel shadow band), 8 on wood, 6 on metal, about 3 on the stones of mud and gravel.
- Edges are ragged with a 1 to 2 pixel staircase, not blocky.
- Streaks are short: wood patches are about 2.5 times longer across than up; slate and metal drips about 1.3 to 1.6 times longer up than across.
- The height map follows the lightness of the colour (correlation 0.97 to 0.99); the reference maps were made that way.

**The twelve facts that would have saved me the most time** (each one is shown further down):

1. **Flat patches with a short palette are most of the look.** Constant colour steps and cells do it; no special shader is needed. A per-patch random number picks a colour from a Color Ramp set to Constant. (TESTED, 4.1, 4.2)
2. **Posterise a grey value, not a colour.** The compositor Posterize node works on each colour channel separately and turns a brown picture into red, olive and black. Posterise a grey number (Map Range "Stepped", or a Constant Color Ramp) and then give it colours. (TESTED, 4.1 and 4.10)
3. **Counting levels:** Map Range with Interpolation "Stepped" and Steps N gives N + 1 levels (both ends included); Math "Snap" with Increment 1/N gives N levels but the top one is only 1 - 1/N (it rounds DOWN); Floor (x times N, then divide by N - 1) and a Constant Color Ramp with N stops give N levels from 0 to 1. (TESTED, 4.1; the manual says Snap rounds down and agrees)
4. **Never hash the raw "Position" output of a Voronoi to get a random number per cell.** It seems to carry tiny rounding differences (rounding the position first cures it, which is why I think so), so the "random" number jumps along straight lines inside a cell. Use the Voronoi **Color** output (a clean per-cell hash) and feed that to a White Noise with a different "W" per random number you need. (TESTED in the seamless 4D version, 4.2)
5. **Domain warping keeps a tile seamless if the warp noise itself repeats.** Add a seamless-noise push to the coordinate, then read a seamless pattern: the 2 x 2 tiling test shows the same 1 percent of edge-pixel flips as the plain cells, against 90 percent for ordinary Noise. A fine warp (noise Scale 40 to 70, Amount 0.004 to 0.01) turns smooth cell borders into ragged paint edges. (TESTED, 4.3)
6. **Snapping the coordinate to a grid before the pattern reads it makes staircase edges.** The references have a 1 to 2 pixel staircase (median straight run 1 to 2 px); a grid of about 400 per tile (3 px blocks) gives 2 px; 5 px blocks and bigger are blockier than the references. Use whole numbers so the tile still repeats. (TESTED, 4.4)
7. **For streaks, stretched Voronoi cells with one colour each look more like paint than stretched noise.** Our own seamless streaky noise and cells take a different feature count across u and across v. The Gabor texture gives low-contrast bands and does NOT tile (45 percent of pixels differ after one tile); the Wave texture tiles only with whole cycles and no Distortion. (TESTED, 4.5)
8. **Outlines inside the shader without geometry:** sample the same patch pattern a few pixels away and mark where the patch number changes. Two samples (+u, +v) give a one-sided line of exactly w pixels (like a drop shadow); four samples (+-u, +-v) give a centred line of exactly 2w pixels; Voronoi "Distance To Edge" below a threshold gives an exact line for cell patterns; the Bump node gives only 1 to 3 pixel lines. (TESTED, 4.7, calibration table)
9. **Ambient Occlusion, Bevel and Pointiness need real geometry.** On a flat plane with a Bump node the AO result is flat (spread 0.02). On a stepped relief they give a soft shadow at the foot of each step (AO), a faint thin line (Bevel) and bright/dark edge pairs (Pointiness). They are shading tools, not outline makers. (TESTED, 4.8)
10. **The compositor in Blender 5.2 is a node group on the scene, every setting is an input socket, and headless it needs `compositor_device = 'CPU'`** (the default is 'GPU' and fails here with a libEGL error). Kuwahara anisotropic at Size 8 takes 5.3 seconds on a 1254 tile; classic takes 0.4 seconds. (TESTED, 4.10)
11. **Any compositor filter puts a seam in a tile.** After Kuwahara anisotropic Size 8 the jump across the wrap-around edge is 2.6 times a normal pixel step (size 16: 3.7; classic 16: 4.3); the source was 0.96. Fix: wrap-pad the picture first (numpy `np.pad(..., mode='wrap')` with a margin, or bake a wider area), filter, cut the middle out: 1.05. The compositor's own "Extension: Repeat" did NOT fix it. (TESTED, 4.10)
12. **Make the height from the lightness of the FINISHED colour, blur it by about 0.8 pixel, then make the normal.** On the slate demo the blur took the "normal agrees with the height slope" score from 0.00 to 0.45 and the overall score from 0.51 to 0.55 (0.57 with the patch size tuned from the spec, section 5). The Kuwahara filter did not raise the score on an already flat picture (0.51 to 0.48). (TESTED, 4.11 and 5)

**The pipeline in seven steps** (the order that worked in the slate demo):

1. **Layout** (rows, tiles, planks): put the layout in numbers (row, fraction inside the row) so outlines can be drawn from them.
2. **Patch field:** seamless Voronoi cells (stretched for streaks), one random number per cell from the Color output.
3. **Warp** the coordinate: coarse (Amount 0.012, Scale 5) for organic shapes, fine (Amount 0.004, Scale 70) for ragged edges, optionally Snap to a 400 grid.
4. **Palette:** per-patch random number into a Constant Color Ramp holding the measured palette; small Hue/Value jitter per cell.
5. **Layers:** big underpainting, then smaller patches that cover only part of the picture (coverage 0.15 to 0.5); stains with hard thresholds.
6. **Outlines and shadow bands** from the layout or from offset samples; a lip highlight above a dark line.
7. **Maps:** height = lightness of the finished colour, blurred 0.8 px; normal from that height. Optional: a Kuwahara pass if the source is grainy (padded!).

---

## 2. The look specification: what the six references measure

How I measured (script `scripts/a01_measure_references.py`, plus `a01b`, `a01c`, `a04`, `a05`, `a06`; all numbers in `data/`): the colour pictures were read as sRGB, converted to
Lab (L = lightness 0..100), and analysed with plain Python. "Colour error" is the distance in Lab between a pixel and the palette colour it is snapped to
(2.3 is the usual rule of thumb for a just-visible difference; from colour science, not checked here). The references were only READ for analysis; nothing from them goes into a recipe except these numbers.

### 2.1 Palette and contrast

Picture: `pictures/a03_reference_palettes.png` (8 colours per surface, bar width = share of the picture). The averages in a palette are a little muted, so the table
also gives the "accent" colours that averaging hides (the mean of the brightest 1 percent, the darkest 1 percent and the most colourful 1 percent of pixels).

| Surface | Lightness at the 1st / 50th / 99th percentile | Mean colourfulness | How many palette colours for an average error of 3 | Average error with 4 / 8 / 16 / 32 colours | Brightest 1% | Darkest 1% | Most colourful 1% |
|---|---|---|---|---|---|---|---|
| brick | 15 / 36 / 59 | 28 | 24 | 6.3 / 4.5 / 3.5 / 2.7 | #b09172 | #2b201b | #b15329 |
| slate | 2 / 26 / 48 | 4 | 12 | 4.5 / 3.1 / 2.3 / 1.8 | #7a7975 | #070709 | #4f4d36 (olive) |
| wood | 4 / 29 / 55 | 13 | 24 | 6.0 / 4.3 / 3.1 / 2.4 | #ae8361 | #0f0a09 | #a26f4a |
| metal | 4 / 23 / 44 | 7 | 16 | 5.0 / 3.8 / 2.8 / 2.2 | #817466 | #0f0b09 | #73401f (rust) |
| mud | 5 / 33 / 55 | 16 | 24 | 6.6 / 4.4 / 3.2 / 2.4 | #a18772 | #0f0a09 | #925f3c |
| gravel | 3 / 24 / 53 | 8 | 24 | 6.3 / 4.4 / 3.3 / 2.5 | #91897d | #070707 | #815637 |
| mud_golden | 1 / 30 / 67 | 13 | more than 64 | 7.9 / 5.6 / 4.0 / 3.0 | #c8a983 | #020202 | #c18a58 |

The 8-colour palettes (hex, share of the picture) as measured:

- **brick:** #3a2d27 9% - #513c31 12% - #633b2e 10% - #773f2e 16% - #8b442d 18% - #775e49 14% (mortar) - #a34d2d 14% - #9a7b5f 7% (mortar chips)
- **slate:** #0e0f11 8% (outline) - #1e2022 10% - #2d3133 16% - #3a3c31 7% (moss) - #3a4045 29% - #4f4e40 6% (moss) - #4a5254 21% - #6d6c67 4% (chips)
- **wood:** #1c1513 7% - #39261b 9% - #3e322e 15% - #51392b 15% - #57473f 20% - #6c4b36 12% - #715b4d 13% - #926a4d 8%
- **metal:** #1f1a18 9% - #37251d 8% - #333435 35% (steel) - #4f2c1b 7% (rust) - #3f3f3e 25% (steel) - #513e31 6% - #694125 6% (rust) - #665d54 5%
- **mud:** #242125 7% - #301f19 9% - #4d3225 16% - #6a4632 35% (earth) - #4c5058 8% (puddle) - #64544d 7% - #8f664b 10% - #6a7379 8% (puddle light)
- **gravel:** #171617 17% - #26282b 18% - #422f22 10% - #373b3f 14% - #5a3c28 14% - #4e5457 11% - #7a5940 8% - #6b6f6e 8%
- **mud_golden:** #1c1717 16% - #3f2c23 13% - #39373b 8% - #5c4233 28% - #76523b 16% - #5f6369 10% - #848380 6% - #b68d66 4%

What to do with this: put these colours into a Constant Color Ramp (section 4.9: the hex numbers must be converted to linear before they go into a ramp, or every colour comes out 73 steps too bright)
and give the ramp a random number per patch. Keep the shares: a ramp stop is as long as the colour's share.

### 2.2 How few colours? (picture `pictures/a02_posterise_reference_all.png`)

I snapped every pixel of each reference to its nearest palette colour (k-means in Lab) with 4, 8, 16 and 32 colours. At 8 colours the six surfaces still read as
themselves (brick bricks and mortar, slate moss, wood knot, rust, puddles, stones). So: aim for **8 colours plus 2 or 3 accents, in flat patches**. The darkest outline colour is its own palette entry
(slate #0e0f11, brick #2b201b).

### 2.3 Patch size, flatness, edge hardness, busyness

| Surface | Patch diameter in px (25th / 50th / 75th percentile, weighted by area) | Patch median in UV | Single specks (median px) | Share of pixels that are "flat" (5 x 5 lightness spread under 1 / under 2) | Lightness wobble inside a patch | Edge width in px (median) | Strong edges that change within 2 px | Edge density (share of pixels with a lightness jump above 8) | Typical staircase run (px) |
|---|---|---|---|---|---|---|---|---|---|
| brick | 18 / 38 / 67 | 0.031 | 6.8 | 17% / 37% | 5.8 | 1.06 | 94% | 24% | 1 |
| slate | 25 / 51 / 78 | 0.041 | 7.7 | 47% / 66% | 3.0 | 1.44 | 85% | 9% | 2 |
| wood | 14 / 31 / 54 | 0.025 | 6.7 | 5% / 18% | 6.0 | 1.19 | 89% | 34% | 2 |
| metal | 15 / 35 / 83 | 0.028 | 6.8 | 20% / 47% | 4.3 | 1.10 | 90% | 16% | 1 |
| mud | 14 / 33 / 105 | 0.026 | 6.9 | 19% / 30% | 5.1 | 1.31 | 87% | 27% | 1 |
| gravel | 12 / 23 / 42 | 0.018 | 7.4 | 18% / 33% | 4.4 | 1.33 | 88% | 23% | 1 |
| mud_golden | 12 / 21 / 38 | 0.017 | 7.0 | 11% / 21% | 6.7 | 1.17 | 90% | not measured | not measured |

"Edge width" is the size of a jump divided by its steepest slope across plus-or-minus 4 pixels: a perfect one-pixel step gives 1, a smooth ramp of 6 pixels gives 6.
"Edge density" and "staircase run" scripts: `a05_edge_density.py`, `a06_stair_steps.py`. How to use it: a first guess for the number of cells across the tile is **Scale = 1254 / patch diameter**
(slate 25, brick 33, wood 40, gravel 55) for the stain patches; edge density is the quick "is it busy enough" check (the slate demo reached 8.5 percent against the reference's 8.8, section 5).

### 2.4 Outlines

An "outline" is a dark line around a patch. The brick joints, slate tiles, wood planks and metal plates have long straight outlines; mud and gravel have thin dark rims between stones.
I measured the straight ones by averaging each row of the picture (the courses show up as dark dips), the rest with a "much darker than the surroundings" test.

| Surface | Outline | Width | Colour of the line | Notes |
|---|---|---|---|---|
| brick | dark brown rim around each brick, between brick face and mortar | about 5 px (width at half depth of the row average; the rim itself is 6-8 px) | lightness 24 (about #3a2d27-#2b201b) | 12 courses seen; a lighter mortar band sits next to it |
| slate | black line under every tile, then a lighter shadow band, plus dark gaps between tiles | 12 px at half depth (core about 10 px at lightness 2-5, shadow band about 21 px at lightness 10) | #0e0f11 core, #1e2022 shadow band | at x=250: lightness 35 body, 53 bright lip, 2-3 core (10 px), 10 shadow (11 px) |
| wood | dark crack lines along the planks | about 8 px (3 to 14) | lightness 20 (#1c1513) | long in the x direction |
| metal | dark seams around plates and bars | about 6 px (3 to 17) | lightness 15 (#1f1a18) | weaker contrast (drop 8 on average) |
| mud, gravel | thin dark rim around stones, puddle shores | about 3 px (1.8 to 4.6) | lightness 10 to 13 (#171617, #242125) | 0.4 to 1.3 percent of the picture |

### 2.5 Streaks and direction

How far you can walk along a row or down a column before the painted colour changes (pixel-weighted mean run of one palette colour) and how stretched the patches are:

| Surface | Mean run across (x) | Mean run up (y) | Up / across | Patch height / width (median, 25th-75th) | Inside tiles or panels only |
|---|---|---|---|---|---|
| brick | 22.8 | 19.6 | 0.86 | 0.78 (0.54-1.15) | |
| slate | 31.0 | 30.8 | 1.00 | 0.94 (0.61-1.41) | 1.3-1.6 (drips) |
| wood | 28.8 | 10.8 | 0.38 | 0.41 (0.27-0.59) | 0.40 (planks) |
| metal | 19.2 | 25.7 | 1.34 | 1.21 (0.84-1.74) | 1.3 (panels) |
| mud | 19.7 | 17.6 | 0.89 | 0.87 (0.64-1.17) | |
| gravel | 15.4 | 15.3 | 1.00 | 0.95 (0.71-1.27) | |

So: **wood is the only strongly directional surface (about 2.5 : 1 along x)**; slate and metal drips are only 1.3 to 1.6 : 1 tall (my first guess of 7 : 1 streaks was far too long); the others are round-ish.

### 2.6 What the height and normal maps do

| Surface | Height vs colour lightness (correlation) | Height edge width in px (median; share within 2 px) | Normal tilt angle (median / 90th / 99th percentile, degrees) | Flat normals (under 3 degrees / under 8 degrees) |
|---|---|---|---|---|
| brick | 0.974 | 1.37 (81%) | 11 / 42 / 61 | 14% / 40% |
| slate | 0.993 | 2.00 (50%) | 6 / 29 / 63 | 28% / 60% |
| wood | 0.983 | 1.37 (77%) | 20 / 50 / 67 | 5% / 20% |
| metal | 0.968 | 1.50 (75%) | 9 / 32 / 55 | 16% / 47% |
| mud | 0.987 | 1.72 (65%) | 18 / 53 / 68 | 10% / 30% |
| gravel | 0.988 | 1.89 (57%) | 19 / 55 / 70 | 7% / 26% |

Height edges are a little softer than colour edges (median equivalent width 1.4 to 2.0 px against 1.06 to 1.44), so the uploaded heights are slightly blurred (the cause is not known), and every height map stretches the full 8-bit range (levels with more than 0.05 percent of the pixels: 256 for all six).

### 2.7 Aim card for each surface (translate the numbers into settings)

- **Brick.** Palette 8 above + accents (#b09172 chips, #2b201b dark). Layout: courses of bricks with a 5 px dark rim; mortar band lighter (#775e49 / #9a7b5f). Stains: patches 18-67 px (cells across the tile: about 33), flat, hard edges, slightly wider than tall (0.8). Busy: edge density 24%. Dark soot-like stains (#3a2d27, #2b201b) that run down in drips.
- **Slate.** Palette 8 above; mostly mid blue-greys (#3a4045 29%, #4a5254 21%, #2d3133 16%). Layout: 8 courses and about 6 tiles per row. Outline: line 10 px #0e0f11 at the bottom of each tile, shadow band 21 px #1e2022 at the top of the tile below, gaps 6 px between tiles, a bright lip about 3 px wide (lightness 53, #6d6c67-#7a7975) above the line. Drips: patches 1.3-1.6 times taller than wide, 25-78 px. Olive moss (#3a3c31, #4f4e40) from the top of tiles; tan chips (#6d6c67) along the bottom edge. Flat: 47% of pixels have 5 x 5 spread under 1 - the flattest surface. Edge density 9%.
- **Wood.** Palette 8 above; planks along x with dark cracks (8 px, #1c1513); patches 14-54 px that are 2.5 times longer along x. Busiest picture (edge density 34%), least flat (5%).
- **Metal.** Steel #333435 / #3f3f3e carry 60% of the picture; rust (#4f2c1b, #694125, accent #73401f) in blotchy patches 15-83 px, runs slightly taller than wide (1.2-1.3). Seams 6 px (#1f1a18). Darkest and lowest contrast: lightness 99th percentile only 44.
- **Mud.** Earth #6a4632 35% as the base, dark ruts #301f19 / #242125, puddles blue-grey (#4c5058, #6a7379) in big soft-edged patches (up to 105 px), stones with 3 px rims. Round-ish patches (0.87).
- **Gravel.** Stones in near-black and blue-greys (#171617 17%, #26282b 18%, #373b3f, #4e5457, #6b6f6e) with brown earth (#422f22, #5a3c28, #7a5940) between; patches small (12-42 px, median 23); 3 px rims; edge density 23%.
- **mud_golden.** Same as mud with a much wider lightness range (99th percentile 67) and warm puddles #b68d66 / #c8a983; it has no height or normal map to match.

### 2.8 Converting pixels into settings (the cheat sheet)

| You want | Setting (tile 1254 px; for another size replace 1254 by that size) |
|---|---|
| cells about D px across | Voronoi Scale (cells across the tile) = 1254 / D |
| ragged paint edge of about p px | warp noise Scale 40-70, Amount about p / 1254 (0.004 is about 5 px at the largest push) |
| 1-2 px staircase | Snap grid about 400 per tile (3 px blocks); whole numbers only |
| outline of w px, one-sided | two offset samples, shift w / 1254 in u and v |
| outline of w px, centred | four offset samples, shift (w / 2) / 1254 |
| outline of w px on Voronoi cells | Distance To Edge less than 0.5 x w x Scale / 1254 (Scale = cells across) |
| outline under a row of tiles | row fraction below w / (1254 / rows) |
| streaks 1.5 : 1 tall | stretched cells: Scale U : Scale V = 1.5 : 1 (cells are long where the scale is small) |



---

## 3. How people do it today, and which claims held up

What I found on the web (sources at the end). The honest summary: there is **no single "hand-painted node" recipe**. People combine a few ideas, and most pages describe the idea without the settings.

- **Noise or Voronoi plus a hard step.** A Blender Artists answer (Renzatic, 14 Feb 2023) says paint-stroke effects come from "a lot of scratchy noise along the edges of your lines" and from stacking two colour ramps, one Constant and one B-Spline, to get both crisp and soft transitions.
- **Voronoi with fine noise on the coordinate.** The most concrete recipe I found is the "NPR skin shader" breakdown by Xeofrios (Blender Artists, 29 Sep 2023; 80.lv wrote it up on 10 Oct 2023): a Voronoi gives the stroke pattern; Smooth Voronoi was rejected because it looks bevelled; instead "blur the edges without mixing the colors" by adding very fine noise to the coordinates; several stroke layers come from ONE Voronoi with different W values, followed by a Snap (fewer snap steps = more layers); outlines come from a Fresnel/Facing factor passed through a Voronoi. I reproduced the first three ideas (sections 4.2, 4.3, 4.5 here). The Fresnel outline is for 3D objects and is not tested.
- **"Fully procedural, noise does the work".** lassyla's EEVEE shader (80.lv, 18 Aug 2026) is described as fully procedural with noise playing "a big role", but the article names no nodes; the shader is a download. WEB ONLY, no settings to check.
- **Toon shading and outlines.** The BlenderNation write-up of a tutorial by Martin Klekner (26 Oct 2025) uses Shader to RGB + Color Ramp (EEVEE) for toon shading and Grease Pencil for outlines. That is a 3D shading route, not a texture route. In Cycles, Shader to RGB gives plain white (tested by the shader-toolbox guide).
- **In other tools.** Jeff Horal's Stylized Tile Generator for Substance Designer (80.lv, 27 Aug 2018) starts from a greyscale input, shapes edges and height, strips high-frequency detail and adds Brush Strokes in the diffuse; he says there is "no magic make-it-look-stylized button". That is the same order as the pipeline in section 1.
- **Compositor.** The Kuwahara filter is the standard "painterly" post-process (Kyprianidis, Kang and Doellner, Computer Graphics Forum 28(7), 2009; Heckel, 29 Oct 2024: kernel split into sectors, each pixel takes the average of the calmest sector; the anisotropic version follows the edge direction). Blender has both versions as the Kuwahara node.

**Claims checked**

| Claim (where) | Verdict | Evidence |
|---|---|---|
| Kuwahara: Classic is blocky and fast, Anisotropic is painterly and slow (Blender manual) | **TRUE** | Pictures `pictures/c06_kuwahara_classic.png`, `c06_kuwahara_aniso_size.png`; times 0.4 s vs 5.3 s at Size 8 on 1254 px. TESTED |
| Anisotropic Kuwahara is artifact-free only at Size 4 or more, ideally 8 (devtalk, izo, 2023) | **Consistent** | Size 2 looks almost unchanged; 8 and up flattens the grain into patches. Not tested at lower sizes for artifacts. |
| The Kuwahara Size input arrived in Blender 4.1 with a High Precision option for Classic (4.1 release notes) | **TRUE for 5.2** | Size is an input socket (default 6.0); High Precision exists (0.8 s vs 0.4 s at Size 8, slightly cleaner). TESTED |
| Kuwahara "Sharpness / Uniformity / Eccentricity" tune the look (manual) | **Sharpness yes, the other two barely** | Sharpness 0 blurs the edges badly; 1 keeps them crisp. Uniformity 0 to 16 and Eccentricity 0 to 3 changed the picture only slightly on this source; run time did not change. TESTED |
| Posterize node "converts smooth gradients into sharp transitions" (manual; "useful for masks") | **TRUE but per colour channel** | Steps 4 on a brown picture gave red, olive and black blotches (`pictures/c06_other_nodes.png`); distinct colours 5 at Steps 4. Fine for masks, wrong for painted palettes. TESTED |
| Map Range "Steps = number of values allowed" (manual, vague) | **Measured:** N + 1 levels | Steps 4 gave 0, 0.25, 0.5, 0.75, 1.0. TESTED |
| Math "Snap rounds down to the nearest multiple of Increment" (manual) | **TRUE** | Snap with Increment 0.25 gave 0, 0.25, 0.5, 0.75 and never 1. TESTED |
| A manual page gives posterise as round(x x n - 0.5) / (n - 1) (search-result snippet of the Math node page) | **Not verified** | The page body could not be read; I tested round(x x (n-1)) / (n-1) instead (n levels, end levels half as wide). WEB ONLY |
| "Use the Voronoi Position output as a per-cell ID" (common practice; also what I tried first) | **FALSE in 5.2.2 (4D seamless version)** | A White Noise of Position has straight cuts inside cells (vertical-edge share 0.49 against 0.12 for the Color output); the cuts follow the lattice of the evaluation point, which points to rounding differences of one bit (rounding the position first removes them). Not tested for the plain 2D/3D Voronoi. TESTED |
| Domain-warped patterns stay seamless (my assumption; no source says it) | **TRUE only if the warp noise repeats** | Seamless warp: 0.8 percent of pixels differ after one tile; plain Blender Noise: 90 percent. TESTED |
| Gabor noise gives brush-stroke-like marks (Modo docs; 80.lv 4.3 article says "bold stylized shapes") | **Partly:** bands, not strokes; low contrast; not seamless | Gabor value output stays near 0.5 grey; 45 percent of pixels differ after one tile. TESTED (`pictures/c04_gabor_mapped_all.png`) |
| Wave texture bands wrap at whole numbers | **TRUE only for whole cycles and no Distortion** | Scale 1.5708 (5 cycles): 0.02 percent differ; Distortion 3: 83 percent; Scale 1.0: 96 percent. TESTED |
| Pointiness / Bevel / AO find edges (BlenderNation 2019, Blender Artists 2021) | **TRUE on real geometry only** | Flat plane + Bump -> AO spread 0.02; stepped relief -> soft step shadows (AO), faint lines (Bevel), edge pairs (Pointiness). Pointiness is fastest (2 s vs 17-18 s at 512 px, 24 samples). TESTED |
| Filters on a seamless tile keep it seamless (assumed) | **FALSE** | Kuwahara anisotropic Size 8: wrap jump 2.6 x a normal step (source 0.96). TESTED |
| The compositor's "Extension: Repeat" (Translate / Transform) gives a filter real neighbours (my idea after the 5.0 release notes mention Extension modes) | **FALSE in my test** | Output inside the tile identical to the plain filter (difference 0.0000001 at the edge); seam ratio unchanged 2.61. TESTED (`data/c08f_repeat_padding_verdict.json`) |
| The compositor can run headless (Blender 5.2) | **TRUE with CPU** | Default `compositor_device` is 'GPU' (Python API reference) and fails here with a libEGL error; 'CPU' works. TESTED |
| Kuwahara makes a painted picture "more painted" | **Depends on the source** | On grainy flat cells it removes the grain and keeps the cell edges (good). On the already flat slate demo it lowered the score 0.506 -> 0.482 (section 5). TESTED |
| The Composite node still ends a compositor tree (older tutorials) | **OUTDATED** | Blender 5.0 release notes: Composite node replaced by Group Output; compositing tree is its own data block (`scene.compositing_node_group`). TESTED: Group Output with an 'Image' socket works. |
| Old node names / settings as properties (`node.variation`, `node.size`) for compositor nodes (3.x/4.x tutorials) | **OUTDATED** | In 5.2 Kuwahara has no Python settings at all; Size, Type, Uniformity... are input sockets. TESTED, and confirmed by the Python API reference |

---

## 4. The tools: what each does, how to use it, what I tested

### 4.1 Flat levels (posterising a grey value)

**What it does:** turns a smooth number (0 to 1) into a few flat steps, so that a soft noise becomes patches with hard edges.

Example first: seamless noise, stretched with Map Range (From Min 0.30, From Max 0.70, Clamp on) so it uses the whole 0..1 range, then rounded to 4 levels:

`Noise (seamless) -> Map Range [From 0.30..0.70 -> 0..1, Clamp] -> Map Range [Interpolation Stepped, Steps 3] -> Color Ramp [Constant, 4 palette colours]`

Pictures: `pictures/c01_posterise_methods_all.png` (rows = method, columns = N 2, 3, 4, 6, 8, 16).

What I counted (flat levels really present; no anti-aliasing, dither off; `data/c01_posterise_levels.json`):

| Method | Setting | Levels it gives | Values for N = 4 |
|---|---|---|---|
| Color Ramp, Interpolation **Constant**, N stops at i / N | N | N | 0, 0.33, 0.67, 1 |
| Math **Floor** (x times N, Floor, divide by N - 1, Clamp) | N | N | 0, 0.33, 0.67, 1 |
| Math **Round** (x times (N - 1), Round, divide by N - 1) | N | N (end levels are half-width bins) | 0, 0.33, 0.67, 1 |
| Math **Snap** (value, Increment 1 / N) | N | N, but the top level is 1 - 1/N: it rounds DOWN | 0, 0.25, 0.5, 0.75 |
| Map Range, Interpolation **Stepped** | Steps N | **N + 1** (both ends) | 0, 0.25, 0.5, 0.75, 1 |

When to use which: a Constant Color Ramp is both the posterise AND the colouring step (put the palette in the stops, section 4.9). Map Range Stepped is the quickest way to get "N flat levels of grey" for height or masks. Snap is for snapping coordinates (4.4).
Pitfall: a flat level count taken from a picture is polluted by (a) anti-aliasing at patch edges (Cycles 4 samples gives 25, 50 and 75 percent mixes) and (b) the 8-bit **dither** Blender adds when it saves a PNG (`scene.render.dither_intensity`, default 1.0): flat areas get +-1/255 noise, so "0.33 and 0.34" both appear. Set samples to 1 and dither to 0 to count levels exactly (TESTED). The shared bake harness leaves dither on; harmless to the eye, a note for anyone who counts levels.

### 4.2 Voronoi cells as paint patches

**What it does:** splits the tile into cells; each cell gets one flat colour, like a painter's patches.

Example: 

`Seamless Voronoi [Scale 6, Randomness 1] -> Color output -> White Noise [4D, W 0] Value -> Color Ramp [Constant, palette] -> Hue/Saturation node`

Pictures: `pictures/c02_cells_all.png` (raw colour / palette / jitter / scale / warp, Randomness sweep, Scale sweep).

Settings (Voronoi, seamless 4D version from `lib/recipe_tools.py`, TESTED):
- **Scale** = number of cells across the tile (3 = a few huge patches, 24 = fine specks).
- **Randomness** 0 = a regular grid of squares; 0.25 to 0.5 = an irregular brick-like grid; 0.75 to 1 = natural patches.
- The cell's **random number** must come from the **Color** output (a clean hash). Different "W" on a White Noise gives independent random numbers (colour pick, hue, value, coverage).
- **Pitfall (TESTED):** hashing the Position output gives straight cuts through cells (section 3, `pictures/c02b_position_check/sheet.png`). Rounding the position first (Vector Math Snap 0.01) also cures it, but the Color output is simpler.
- **Per-cell jitter:** the Hue/Saturation node's Hue input is 0.5 for "no change". With Hue = 0.5 + (r - 0.5) x h and Value = 1 + (r2 - 0.5) x v: measured in the baked picture, h = 0.02 moves the hue by about plus or minus 3.6 degrees; v = 0.5 moves the brightness by about plus or minus 25 percent in linear light (the baked values moved from 0.48 to 0.60 around 0.545, about plus or minus 11 percent). Strip: `pictures/c02_cells_as_paint/strip.png`. TESTED
- Palette tool: `hp.palette_ramp()` in `scripts/hp_tools.py` fills a Constant Color Ramp from `[(hex, share), ...]`, sorted dark to light, with each stop as long as its share.

### 4.3 Domain warping (pushing the coordinate around)

**What it does:** bends a pattern by adding a noise-driven shift to the coordinate before the pattern reads it. Big slow warps make shapes organic; tiny fast warps make ragged paint edges.

Example: `Vector -> [seamless noise Color output -> Separate Color -> Red and Green, each mapped from 0.25..0.75 to -1..1, times Amount] added to u and v -> seamless Voronoi`.
Helper: `hp.warp_vector_group()` (Inputs Vector, Amount, Scale, Seed; output Vector). Pictures: `pictures/c03_warp_all.png`.

- **Amount** = roughly the largest push in tile fractions (0.05 = 5 percent of the tile = 63 px). 0.01 = hardly visible wobble; 0.06 to 0.1 = clearly organic; 0.18 = tangled.
- **Scale** = features of the warp noise across the tile. Scale 1 to 4 moves whole patches around (smooth shapes); Scale 16 to 32 at Amount 0.05 tears the patches into ragged blots; **Scale 40 to 70 at Amount 0.004 to 0.01 gives the thin ragged edge of the reference** (strip `pictures/c03_ragged_edges/strip.png`).
- Two warps in a row (coarse then fine) is what the slate demo uses.
- **Seamless?** Yes when the warp noise itself repeats (our seamless noise): after warping, the 2 x 2 test shows 0.8 to 0.95 percent of pixels that differ (one-pixel edge flips), the same as without warp; plain Blender Noise gives 90 percent. TESTED (`data/c02_c03_periodicity.json`)
- The Noise node's own **Distortion** input is a built-in warp for a single noise; the shader node toolbox guide shows it (its picture `p06_noise_distortion.png`). Not re-tested here.
- Source for the idea: the formula f(p + h(p)) (Iñigo Quilez, "Warp"; the page did not load here, formula from the search snippet, WEB ONLY) and the Planetset docs recipe (noise Color minus 0.5, scaled, added to Position, into Voronoi). The planetset recipe is the same chain; the "minus 0.5, scale" is my Map Range step.

### 4.4 Snapping the coordinate (staircase edges)

**What it does:** rounds the coordinate to a grid before the pattern reads it, so each small square of the picture reads one value and every edge becomes a staircase of squares.

Chain: `Vector (after warp) -> Vector Math Scale (x G) -> Vector Math Floor -> Vector Math Scale (x 1/G) -> Voronoi`. G = squares per tile.
Picture: `pictures/c16_coordinate_snap/strip.png` (no snap, G = 400, 250, 160, 100, 60 = blocks of 3, 5, 8, 13, 21 px).
- Measured staircase: the median straight run along the border of a patch is 1 px for brick, metal, mud, gravel and 2 px for slate and wood (`data/a06_stair_steps.json`). Snapped pictures: no snap 1, G = 400 gives 2, G = 250 gives 3, G = 100 gives 3 (and longer on average). So **G about 400 matches the references; 5 px blocks and up are blockier than the references**.
- Whole numbers only: G = 400, 250, 100 repeat (2.7 percent edge flips, same as unsnapped); G = 250.5 gave 5.2 percent. TESTED

### 4.5 Streaks and brush marks

**What it does:** makes long thin marks (drips on slate and metal, grain on wood).

All pictures: `pictures/c04_streaks_all.png`, `c04_dabs_wave_all.png`, `c04_gabor_mapped_all.png`.

| Source | How you stretch it | Seamless? (2 x 2 test: share of pixels that differ) | Notes |
|---|---|---|---|
| **Our streaky noise / cells** (`hp.anisotropic_noise_group`) | Scale U and Scale V separately (features across the tile). Long in v when Scale V is smaller than Scale U. Ratio 1, 2, 4, 8, 16 shown. | **yes** (1.3 to 2 percent: edge flips) | How: u goes round a circle of circumference Scale U, v round a circle of circumference Scale V; 4D noise or Voronoi is read from those four numbers. |
| **Stretched cells with a palette colour each** (brush "dabs") | same, with Voronoi cells | **yes** (2 percent) | Looks more like paint than stretched noise: flat patches with pointed ends. |
| **Noise through the Mapping node, Scale (8, 2, 1)** | Mapping Scale | no (91 percent) | quick look-dev only |
| **Wave texture** (Bands, Y, Sine) | Scale; Distortion bends the bands; profiles Sine / Saw / Triangle (a third profile, Triangle, exists in 5.2) | only with whole cycles (Scale 1.5708 = 5 cycles) and Distortion 0: 0.02 percent; Distortion 3: 83 percent | good for plank grain look-dev |
| **Gabor** (2D, Frequency, Anisotropy, Orientation) | Orientation (radians) sets the band direction, Anisotropy 1 = one direction, 0 = every way; Frequency = bands across the direction | no (45 percent) | low contrast (value around 0.5 grey); bands, not strokes |

Numbers to aim for: wood patches about 2.5 : 1 long along u (Scale U : Scale V about 1 : 2.5 for stretched cells; `pictures/c04_horizontal_streaks_wood/strip.png` shows 4/40, 3/60, 2/90); slate and metal drips 1.3 to 1.6 : 1 tall; everything else round. My first slate demo used 7 : 1 drips and scored lower than 2 : 1 (section 5).

### 4.6 Layers of patches ("painting in layers")

**What it does:** an underpainting of big patches, then smaller patches on top that cover only part of the picture.

Chain per layer k: `seamless cells (Scale = base x 1.8^k, Seed = 17 k) -> palette colour per cell`, then `mix(previous, this layer, cell yes/no)` where the yes/no is `(per-cell random < coverage)`. Helper script `scripts/c13_layered_dabs.py`.
Pictures: `pictures/c13_layered_dabs_all.png` (layers 1 to 5, coverage 0.15 to 0.9, stretch 0.5 to 8). Periodicity test with 4 layers: 4.3 percent of pixels differ (edge flips). TESTED.
- 3 to 4 layers is enough: 5 layers at growth 1.8 becomes confetti.
- Coverage 0.15 to 0.3 reads as stains on an underpainting (mud, brick); 0.5 and more covers the underpainting (gravel).
- This is the same idea as Xeofrios' "several Voronoi layers by changing W" (W = my Seed input).

### 4.7 Outlines (dark lines around patches)

**What it does:** draws a dark line where one patch meets another.

Seven routes, from cheapest to dearest. Straight-edge calibration (grid of square cells, no anti-aliasing, exact pixel counts; `data/c05e_width_calibration.json`):

| Route | Setting | Measured line width (px) for settings 1, 2, 3, 4, 6, 8 | Cost on a 384 px tile (pattern alone 1.05 s) |
|---|---|---|---|
| **Layout fractions** (you know where rows and tiles are: `row fraction < w / rowHeightPx`) | w | exact | free |
| **Offset samples, 2 taps** (+u, +v) | shift w px | **1, 2, 3, 4, 6, 8** (one-sided) | 2.6 s (3 pattern evaluations) |
| **Offset samples, 4 taps** (+-u, +-v) | shift w px | **2, 4, 6, 8, 12, 16** (centred, 2 w) | 4.2 s (5 evaluations) |
| **Voronoi Distance To Edge** below a threshold | threshold = (w / 2) x Scale / size | 1, 2, 3, **5, 7, 9** (about w + 1 for w of 4 and up) | 2.5 s (a second Voronoi) |
| **Bump node** on the patch number, edge = 1 - Normal Z, Filter Width = w / 2 | Filter Width | 1, 1, 1, 1.5, 2, 3 (thin, weak) | 2.6 s |
| **Compositor:** Filter Sobel + threshold, then Dilate/Erode or Mask To SDF | see 4.10 | 3 px line; widened to 5 / 7 / 10 / 12 px (Dilate Distance 1 to 4), 3 / 6 / 9 / 12 px (SDF less than 1 to 4) | 0.2 s / 0.6 s at 1254 px |
| **Real geometry:** AO, Bevel, Pointiness | see 4.8 | soft shadows, faint lines | 2 to 18 s at 512 px |

How the offset samples work: put the patch pattern in a node group with an output "Id" (a number that differs between neighbouring patches), instance it at p, p + (w, 0), p + (0, w) (and the minus versions), and mark the pixel where `|Id(p) - Id(p + d)|` is above a small value; Mix the dark colour in with that mask. It works for any flat-level pattern (cells, or posterised noise), not only cells. Pictures: sheet `pictures/c05_outline_methods_sheet.png`; folders `pictures/c05_outline_*`.
Notes: the one-sided version draws the line on one side of every border (a painted shadow edge); for a pattern with lots of tiny levels (posterised fractal noise) every level change draws a line, so wide offsets turn it into black noise (`levels_offset4_8` in the sheet).
The slate reference's line-plus-shadow is the one-sided idea twice: a 10 px core and a 21 px lighter band. In the demo they are made from the row fraction (cheapest and exact).

### 4.8 Edge darkening from real geometry (AO, Bevel, Pointiness)

**What it does:** these Cycles nodes look at the actual surface shape. They need real geometry: a flat plane with a Bump node has nothing for them to see.

Test (`scripts/c10_geometry_edge_tools.py`, picture `pictures/c10_geometry_edge_tools_sheet.png` and `_sheet2.png`): the stepped patch pattern turned into a real 256 x 256 grid with 4 height levels (step height 0.02), photographed from above, 24 samples.

| Node | What it gave | Time at 512 px |
|---|---|---|
| Ambient Occlusion, Distance 0.03 | soft dark band (about 10 px) at the foot of each step; 12 percent of pixels below 0.9; min 0.25 | 17.4 s |
| Bevel node (Radius 0.006), edge = 1 - dot(bevelled normal, real normal) | thin faint line on every step (max 0.31 before amplifying) | 18.2 s |
| Geometry > Pointiness | 0.5 on flats; brighter on convex and darker on concave edges (0.43 to 0.60); very weak | 2.1 s |
| Flat plane + Bump -> AO | flat (spread 0.02, range 0.92 to 1.0) | 16.9 s |
| Flat plane -> Pointiness | exactly 0.502 everywhere | |

Verdict: AO is a good painted shadow at step feet (and the painted slate reference does have a shadow band), but it is a soft gradient, not a hard outline, and costs 17 s per 512 px bake. Use it only when the builders have real displaced geometry for another reason (geometry nodes), and keep the layout/offset outlines for the flat tile. (The shader node toolbox guide also tests these nodes; see its pictures `e11_bevel_edge_mask.png`, `e12_ao.png`, `e13_pointiness.png` in `experiments_shader_node_toolbox/pictures/`.)

### 4.9 Palette control

**What it does:** keeps the colours to the measured list and adds small controlled variation.

- **Color Ramp options in 5.2 (TESTED):** Interpolation `EASE`, `CARDINAL`, `LINEAR`, `B_SPLINE`, `CONSTANT`; colour mode `RGB`, `HSV`, `HSL`; hue path `NEAR`, `FAR`, `CW`, `CCW`. Picture `pictures/c11_palette/ramp_modes/strip.png`: in HSV or HSL a blend from slate blue-grey to brick orange passes through purple (NEAR) or green and olive (FAR): useful for inventing a stain colour, wrong for keeping to a measured palette. Use RGB mode with Constant for painted palettes.
- **Hex trap (TESTED, the most useful number in this section):** a Color Ramp wants LINEAR colour numbers. Typing the numbers of #3a2d27 as 58/255, 45/255, 39/255 comes back 73 steps (of 255) too bright in the baked picture; converting sRGB to linear first (`hp.srgb_hex_to_linear`) comes back with 0 error for all 8 brick colours (`data/c11_palette_checks.json`).
- **Palette ordering:** sort dark to light so a smooth 0..1 number reads dark to light, and give each stop the colour's share of the picture as its length.
- **Per-cell hue and value jitter** as in 4.2; keep it small: reference patches wobble 3 to 6 lightness units inside.
- **Accents:** keep the 1 percent colours of table 2.1 (a bright chip, a rust orange) as rare small patches (coverage 0.05 to 0.1 of a top layer).

### 4.10 The compositor on baked pictures (Kuwahara and the others)

**What it does:** post-processes a finished picture. In Blender 5.2 the compositor is a node tree stored on the scene.

**How to run it headless (TESTED; `hp.run_compositor` in `scripts/hp_tools.py`):**

```
scene.render.compositor_device = 'CPU'            # the default 'GPU' needs a graphics card (libEGL error here)
scene.render.use_compositing = True
tree = bpy.data.node_groups.new('stylise', 'CompositorNodeTree')
scene.compositing_node_group = tree               # 5.x: the tree is a data block; scene.use_nodes is deprecated
tree.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
image = tree.nodes.new('CompositorNodeImage'); image.image = bpy.data.images.load(path)
kuwahara = tree.nodes.new('CompositorNodeKuwahara')
kuwahara.inputs['Type'].default_value = 'Anisotropic'     # menu sockets take the option name
kuwahara.inputs['Size'].default_value = 8.0
tree.links.new(image.outputs['Image'], kuwahara.inputs['Image'])
out = tree.nodes.new('NodeGroupOutput'); tree.links.new(kuwahara.outputs['Image'], out.inputs[0])
bpy.ops.render.render(write_still=True)           # scene resolution = picture size (my helper adds an empty camera; not tried without one)
```

For data pictures (height, masks) load the image with colour space "Non-Color", set the view transform to "Raw" and, for height, save 16-bit (`image_settings.color_depth = '16'`). A classic Kuwahara pass on a 16-bit height gave 23292 distinct values (source 25609); saved 8-bit it gave 115. TESTED

**The stylising nodes in 5.2.2 and their input sockets (TESTED, `data/b01_compositor_nodes.txt`):**

| Node | Inputs (defaults) | Menu options |
|---|---|---|
| Kuwahara | Image, Size 6.0, Type, Uniformity 4, Sharpness 1.0, Eccentricity 1.0, High Precision | Type: Classic, Anisotropic |
| Posterize | Image, Steps 8 | |
| Pixelate | Color, Size 1 (integer pixels) | |
| Filter | Image, Factor 1, Type | Soften, Box Sharpen, Diamond Sharpen, Laplace, Sobel, Prewitt, Kirsch, Shadow |
| Dilate/Erode | Mask, Size 0 (negative = erode), Type, Falloff Size, Falloff | Type: Steps, Threshold, Distance, Feather |
| Blur | Image, Size (x, y), Type, Extend Bounds, Separable | Flat, Tent, Quadratic, Cubic, Gaussian, Fast Gaussian, Catrom, Mitch |
| Bilateral Blur | Image, Determinator, Size 0, Threshold 0.1 | |
| Despeckle | Image, Factor, Color Threshold 0.5, Neighbor Threshold 0.5 | |
| Mask To SDF | Mask -> SDF (distance in pixels, negative inside), Nearest Pixel | |
| Convolve (new in 5.0) | Image, Kernel Data Type, Kernel, Normalize Kernel | |

Shader nodes such as Math, Mix, Color Ramp and Map Range can be added to a compositor tree (I used Math in the outline test). There is no separate Composite node any more.

**What the settings do (pictures `pictures/c06_*.png`, source = flat cells covered in fine grain, 1254 px, crops 420 px):**
- **Classic Size** 1 to 12: 1 to 3 changes little; 5 and up flattens the grain into **square-ish blocks**; the cell edges stay crisp. High Precision slightly cleaner (0.76 s vs 0.40 s). Chained passes make it flatter.
- **Anisotropic Size** 2 to 16: 8 and up flattens the grain into smooth brush-like blobs while the cell borders stay sharp; 16 leaves almost only flat colour. Time grows with Size: 0.8 s (2), 1.7 (4), 3.2 (6), 5.3 (8), 11.3 (12), 19 s (16); each chained pass adds the same again (x4 = 12.9 s at Size 6).
- **Sharpness** 0 blurs everything (and edges!), 0.25 to 0.5 soft, **1.0 crisp** (keep it at 1 for a painted look). **Uniformity** (0 to 16) and **Eccentricity** (0 to 3): small visible effect on this source; they did not change the run time. Manual advice for Uniformity: raise it until the picture stops changing.
- **Posterize** (per colour channel): wrong tool for a coloured picture (section 3). With the file's numbers taken as they are (`input_linear`) it gives 10 colours at Steps 4 instead of 5 and moves the picture less (mean change 0.14 vs 0.27), but it is still per channel.
- **Pixelate** Size in pixels: 1 to 4 = invisible, 8 and up = obvious mosaic. Not a painted look.
- **Bilateral Blur** (Size 4 to 16): it needs its **Determinator** socket connected to a picture that shows the edges. In my first sweep I left it unconnected (constant white) and got a plain blur. With the Determinator linked to the picture itself, Size 4 to 8 at Threshold 0.05 softens the grain and keeps the cell borders; Size 16 blurs the borders; it flattens less than Kuwahara (`pictures/c06_compositor/bilateral_determinator/strip.png`). TESTED
- **Filter:** Sobel, Prewitt, Kirsch and Laplace give edge pictures (use them to find outlines); Box/Diamond Sharpen BRING BACK the grain; Shadow is an emboss.
- **Despeckle** barely changes grain at thresholds 0.05 to 0.5.
- **Dilate/Erode** and **Mask To SDF:** see the outline table in 4.7 (widths measured).

**Run time at 1254 x 1254 (CPU, 2 threads):** Posterize 0.2 s, Pixelate 0.2 s (1.2 s at Size 32), Bilateral 0.3 s, Filter 0.3 s, Dilate 0.2 s, Mask To SDF 0.6 s, Kuwahara classic 0.4 s, anisotropic 0.8 to 19 s depending on Size.

**Seams: every filter breaks the wrap-around edge (TESTED; `pictures/c08_seams/`, `data/c08_compositor_seams.json`, `c09_compositor_details.json`)**

| Filter on the plain tile | Jump across the wrap-around edge, as a multiple of a normal pixel step (source 0.96) |
|---|---|
| Anisotropic Size 4 / 8 / 16 | 1.95 / 2.61 / 3.66 |
| Classic Size 4 / 8 / 16 | 1.39 / 2.08 / 4.29 |
| After wrap-padding the picture first (Anisotropic Size 8, margin 96 px) | **1.05** |

The damage sits within about 5 pixels of the tile edge. Fix that works: save the picture wrap-padded (`np.pad(picture, ((m, m), (m, m), (0, 0)), mode='wrap')`, or bake a wider area of the repeating pattern: `hp.photograph_padded`), filter, cut the middle tile out (`scripts/c08e_numpy_wrap_pad.py`: result equals the padded bake within 0.001). I used a margin of 96 px for Size 8 (12 x Size); smaller margins were NOT tested (the error reaches only about 5 px in, so a margin of Size is probably enough, NOT TESTED). Chained passes need the margin for each pass added up. What did NOT work: Translate/Transform with Extension "Repeat" on a bigger canvas (section 3).
Colour space: running Kuwahara on the encoded numbers (colour space "Non-Color") instead of linear light changed the picture by only 0.003 on average on this source; not worth the trouble. TESTED

**Where Kuwahara helps and where it does not (honest):** it turns grainy or noisy colour into flat patches and keeps strong edges, so it is good for a "baked noisy source" workflow. It does not create new edges, and on a picture that is already flat (the slate demo) it removed detail and lowered the score. It is also slow at the sizes that give a strong effect. The references' look is better matched by building the flat patches directly (sections 4.2 to 4.7).


### 4.11 Keeping colour, height and normal consistent

**What it does:** makes the three pictures show the same shapes, so that a painted patch edge in the colour is also a step in the height and a ridge in the normal.

What the references do (measured, section 2.6; and from the job notes: "the maps were derived from the base colour"): the height follows the lightness of the colour (correlation 0.97 to 0.99, also where that is physically odd: brick mortar is lighter than the bricks and also higher), the height edges are slightly softer than the colour edges (1.4 to 2.0 px against 1.06 to 1.44), and the normal is a Sobel-style slope of that height.
So the simplest consistent method is the one the references used: **finish the colour (with every stylising step), then make height = lightness of the colour, blur it slightly, then make the normal from the blurred height.**

Tested on the slate demo after a Kuwahara pass (`scripts/c14_kuwahara_and_consistency.py`, `data/c14_kuwahara_consistency.json`; texture_compare scores from `data/slate_demo/*/score.json`):

| Way to get the height for the stylised colour | Correlation of colour lightness with height | Overlap of the strongest 5 percent of edges (Dice) | texture_compare overall score (slate) |
|---|---|---|---|
| H1 lightness of the stylised colour (what the references did) | 1.000 (by construction) | 1.00 | 0.482 |
| H1 + blur 0.8 px, normal made from the blurred height | 0.989 | 0.88 | **0.534** |
| H2 the height the recipe made BEFORE the filter (colour stylised, height not) | 0.986 | 0.83 | 0.481 |
| H3 the same Kuwahara run separately on the height | 0.997 | 0.94 | 0.474 |

What this says: a height that was not filtered (H2) still lines up with the filtered colour well enough (edge overlap 0.83) that the score does not move. The big lever is the **blur of 0.8 px before the normal**: the "normal agrees with the height slope" score goes from 0.00 to 0.73 (and the overall score from 0.482 to 0.534). A hard-stepped height (one-pixel steps) gives a Sobel normal whose x and y parts agree with the height slope far worse than the reference's normal does. The uploaded height has edges 0.4 to 0.6 px softer than the colour's (section 2.6) and the README of the reference folder says the prepared copy was smoothed by 0.8 px, so I used 0.8 px (not fitted; other values not tried).
Also: save heights as **16-bit** (an 8-bit height through the filter had 115 distinct values against 23292 for 16-bit). TESTED

Not tested: a normal made with Blender's Bump node from the stylised height (the shared harness writes it as `normal_bumpnode.png`); a height built from a shared "structure" (patch numbers plus outline groove) instead of from the colour.

---

## 5. Putting it together: the stylising stack on a painted slate and a painted gravel

These two recipes exist only to show what each stylising control adds and to see how close plain nodes get. They are bake_harness recipes in `scripts/` (`r12_painted_slate_demo.py`, `r16_painted_gravel_demo.py`); they are NOT finished surfaces (no varying tile widths, no chipped edges). Scores come from `lib/texture_compare.py` (0 = as different as another surface, about 0.99 = a reshuffled copy of the reference itself); one random seed each, so differences of 0.02 are noise-level.

### 5.1 Slate, stage by stage (`pictures/c12_slate_demo_stages.png`)

Recipe: 8 rows of 6 tiles with a per-row shift (the layout is pushed up half a row so the wrap-around edge lies inside a row; with a row boundary on the wrap edge the texture_compare seam measure read 8.95; after the shift 0.88).

| Stage | What was added | Overall | Colour | Height | Normal | Edge density (reference 8.8%) |
|---|---|---|---|---|---|---|
| 0 | plain: one soft colour per tile + soft noise shading | 0.372 | 0.27 | 0.25 | 0.61 | 0.1% |
| 1 | + painted patches: stretched cells (Scale U 34, V 5), palette colour per cell | 0.270 | 0.25 | 0.19 | 0.13 | 2.5% |
| 2 | + ragged edges: coarse warp (Amount 0.012, Scale 5) and fine warp (0.004, Scale 70) | 0.278 | 0.25 | 0.19 | 0.17 | 2.5% |
| 3 | + outlines: 10 px core, 21 px shadow band, 6 px gaps, 5 px lip | **0.486** | 0.52 | 0.36 | 0.39 | 7.0% |
| 4 | + stains: olive patches from the top, tan chips along the bottom (hard thresholds) | 0.506 | 0.55 | 0.36 | 0.42 | 8.5% |
| 4 + smooth | same, height blurred 0.8 px and the normal remade | 0.555 | 0.55 | 0.44 | 0.58 | 8.5% |
| 4, patch size from the spec | drips U 16, V 8 (about 2 : 1 instead of 7 : 1), height blurred | **0.574** | 0.59 | 0.43 | 0.60 | 7.9% |
| 5 | + Kuwahara anisotropic Size 6 (wrap-padded), height from the new colour | 0.482 | 0.50 | 0.35 | 0.41 | 7.0% |
| 5 + smooth | same, height blurred 0.8 px | 0.534 | 0.50 | 0.42 | 0.62 | 7.0% |

Reading the table:
- **Outlines were the most valuable single control** (+0.21 overall in one step: colour spectrum 0.00 to 0.58, orientation 0.00 to 0.58, gradient 0.30 to 0.62). The slate reference has strong long horizontal lines (its horizontal correlation length is 64 px against 11 up).
- Adding painted patches alone made the score WORSE (0.37 to 0.27): the patches were the wrong size (horizontal correlation length 17 px against the reference's 64) and the normal went wrong at the same time. A control that is right in kind but wrong in size can score below no control.
- Edge density is a good sanity check: 0.1 to 2.5 percent means "not painted yet"; 8.5 percent matches the reference's 8.8.
- Tuning the drip stretch with the measured spec (2 : 1 instead of 7 : 1) helped (+0.02). Other tries: U 22 / V 9 gave 0.548; U 12 / V 5 with stronger tone steps 0.545; U 34 / V 5 0.555 (all with the 0.8 px blur).
- Kuwahara lowered the score by about 0.02 (0.506 to 0.482 unblurred, 0.555 to 0.534 blurred): the picture was already flat and its fine ragged detail is part of the reference's look.

Look at it yourself: `pictures/c12_slate_demo_stages.png` and the per-stage sheets `data/slate_demo/stage?/sheet.png`, `data/slate_demo/tune2_smooth/sheet.png`.

Honest verdict: the measured spec plus these controls get the slate to the right KIND of picture (flat patches, outlines, moss, drips, matching edge density) and a score of 0.57, but it still looks like a clean diagram next to the reference: no varying tile widths and shapes, no worn tile corners, edges not as irregular, no fine chips. Those are layout details that belong to the slate recipe itself.

### 5.2 Gravel, with stone sizes from the spec

Recipe: speckled earth (flat cells), then layers of stones. Every stone is a Voronoi cell with a dark rim (Distance To Edge, 1.5 to 4 px) and flat facet patches inside it (a second set of Chebychev cells whose seed comes from the stone's number, so every stone has its own facets). Picture of the stone idea: `pictures/c15_angular_cells_all.png` and `pictures/c15_painted_stones_crop.png`.

| Variant | What it has | Overall | Colour | Height | Normal | Edge density (reference 22.9%) |
|---|---|---|---|---|---|---|
| g0 | earth speckle only (flat cells, 48 across) | 0.235 | 0.13 | 0.17 | 0.32 | 7.5% |
| g1 | + small stones (Scale 17, covering 60%) | 0.292 | 0.17 | 0.31 | 0.31 | 13.5% |
| g2 | + big stones (Scale 6, covering 45%), facets inside every stone | 0.346 | 0.25 | 0.36 | 0.32 | 10.8% |
| g3 | the same without facets | 0.336 | 0.24 | 0.34 | 0.32 | 8.4% |
| spec | stone sizes from the measurements: earth 110 across, stones 64 / 30 / 13 across (covering 62 / 50 / 40%), rims 1.5 / 2.5 / 4 px | **0.394** | 0.35 | 0.30 | 0.42 | 25.2% |
| spec + jitter | the same plus a brightness jitter of 0.35 per stone and a fine grain of 0.15 | **0.417** | 0.37 | 0.33 | 0.47 | 24.9% |

(All with the height blurred 0.8 px; picture `pictures/c17_gravel_demo_stages.png`; sheets in `data/gravel_demo/*_smooth/sheet.png`.)

Reading the table:
- **Taking the sizes from the measurements was the biggest step** (0.346 to 0.394): the correlation length fell from 24 px to 7 (reference 8) and the edge density rose from 11% to 25% (reference 23%). With the first guessed sizes the stones were far too big.
- **Facets inside the stones** were worth only +0.01 (g2 against g3), which is within the noise of one seed.
- **Variation inside the palette helped a little** (+0.023, colour distribution score 0.48 to 0.50, height gradient 0.19 to 0.36): the sheet's brightness curve for the flat version is a row of spikes (one per palette colour) where the reference's is smooth. The reference patches wobble 3 to 6 lightness units inside (section 2.3), so "flat" means "nearly flat".
- **How close is it?** The overall character is right (dark and blue-grey stones with rims, brown earth, patch sizes, edge density), but side by side it is clearly a Voronoi patchwork: the reference stones are angular crystals with lighter facets and sharp corners, brown appears as separate grains rather than inside the stones, and there are many more tiny stones. Colour spectrum and gradient scores stay at 0. Angular cells (Chebychev, Randomness 0.6 to 0.8, `pictures/c15_angular_cells_all.png`) and a bright facet edge are the next things to try; not done.




---

## 6. Pitfalls (the things that cost me time)

1. **Posterize node on a colour picture** = red, olive and black blotches (works per channel). Posterise a grey number and colour it afterwards.
2. **Hex colours typed into a Color Ramp** come out 73 steps (of 255) too bright. Convert sRGB to linear first.
3. **Hashing the Voronoi Position output** makes straight cuts inside cells. Use the Color output.
4. **A layout boundary on the wrap-around edge** (a row boundary at v = 0 and 1) makes a seam metric such as `texture_compare`'s read 8.95 even though nothing is wrong; push the layout so the wrap edge lies inside a row (I used half a row: 0.88). The seam metric is also noisy for flat-patch pictures (a regular grid reads 0.08, one random cell picture 4.5): use the strict test instead (render 2 x 2 tiles, compare the tile at 0..1 with the one at 1..2; `hp.periodicity_check`).
5. **Any compositor filter** (Kuwahara, blur...) puts a seam in a tile. Wrap-pad first. The compositor's own Repeat extension does not do it.
6. **The compositor does not start headless** with the default `compositor_device = 'GPU'` (libEGL error). Set 'CPU'. Also: the Composite node is gone (5.0); use a Group Output and `scene.compositing_node_group`; settings are input sockets (menu sockets take the option name as text).
7. **Kuwahara Size is in pixels**, so a setting that suits 1254 px is too small for 2048 px (NOT TESTED: scale it by the resolution). Anisotropic cost grows fast with Size (5.3 s at 8, 19 s at 16 on 1254 px) and with chained passes.
8. **8-bit heights** destroy the slopes: 115 distinct values against 23292 at 16-bit after one filter. Save and filter heights as 16-bit.
9. **Hard one-pixel height steps give a bad normal map** (the normal's agreement with the height slope scored 0.00); blur the height about 0.8 px first (0.73 to 0.86).
10. **The lib function `bake_harness.save_array_png`** writes a one-channel (2-D) array into the RED channel only (green and blue stay 1.0, so a height comes out cyan, and `texture_compare` then reads a compressed height). Pass a 3-channel array. I found this when my first smoothed heights scored oddly; everything in this guide that depended on it was re-run. (`hp.save` in my helper fixes it.)
11. **Counting flat levels** needs samples = 1 and `scene.render.dither_intensity = 0`; with the defaults you see 25/50/75 percent edge mixes and +-1/255 noise.
12. **Snap grids must be whole numbers** (250 repeats, 250.5 does not quite: 5.2 versus 2.7 percent of pixels differ).
13. **Wave texture:** only repeats with whole cycles and Distortion 0; **Gabor** and **Mapping-stretched noise** never repeat.
14. **Voronoi "Minkowski" with Exponent 0.5** breaks the cells into noisy fragments (`pictures/c15_angular_cells_all.png`, row 1, fifth picture); Manhattan and Chebychev give clean angular chunks.
15. **Bilateral Blur needs its Determinator socket connected to the picture;** unconnected it is just a blur. Connected (Size 4 to 8, Threshold 0.05) it softens grain and keeps cell borders, but is weaker than Kuwahara; Size 16 blurs the borders (`pictures/c06_compositor/bilateral_determinator/strip.png`).
16. **A brightness histogram made only of flat palette colours is spiky** (8 peaks), while the reference's is smooth: the reference patches are not perfectly flat (3 to 6 lightness units of wobble inside). See the jitter test in 5.2.
17. **AO, Bevel and Pointiness do nothing on a flat plane** and cost 17 s per 512 px (AO, Bevel) in Cycles.
18. **Maps from a hard-edged pattern in Cycles** need 4 samples (anti-aliasing) for the colour but 1 sample for exact counting.

---

## 7. Recipe cards (short)

**R1 Flat palette patches.** Seamless Voronoi (Scale = 1254 / patch px, Randomness 0.75 to 1) -> Color output -> White Noise (4D) Value -> Constant Color Ramp (palette from table 2.1, converted to linear, dark to light, stop length = share) -> Hue/Saturation (Hue 0.5 + (r - 0.5) x 0.04, Value 1 + (r2 - 0.5) x 0.35). Test: 2 x 2 periodicity.

**R2 Ragged paint edges.** Before the cells read the coordinate: warp with seamless noise (Scale 40 to 70, Amount 0.004 to 0.01); add a coarse warp first (Scale 4 to 5, Amount 0.012) for organic shapes.

**R3 Staircase edges.** After the warp: Vector Math Scale x G, Floor, Scale x 1/G with G = 400 (whole number).

**R4 Drips and grain.** Seamless stretched cells (Scale U : Scale V = 1.5 : 1 to 2 : 1 for drips, 1 : 2.5 for wood grain) with one palette colour per cell; plus the warp of R2.

**R5 Layers of stains.** Underpainting cells, then 2 to 3 layers (Scale x 1.8 each, Seed + 17 per layer) that cover 15 to 50 percent of the picture (per-cell random < coverage); accent colours from the 1 percent list at coverage 0.05.

**R6 Outlines.**
- Known layout (rows, tiles): row fraction below w / rowHeight, tile fraction at the sides; a lip colour above the line; a second wider lighter band for the shadow (slate: core 10 px, shadow 21 px, gaps 6 px).
- Cells: Distance To Edge < (w / 2) x Scale / 1254.
- Any flat-level pattern: instance the pattern at p, p + (w, 0), p + (0, w) (one-sided) or the four +-(w/2) shifts (centred), mark `|Id - Id'| > 0.02`.
- Compositor from a patch-number picture: Filter Sobel, Math Greater Than 0.05, Dilate/Erode Distance k (width 3 + 2 k, about) or Mask To SDF + Math Less Than t (width about 3 x t).

**R7 Painted stones.** Stone cells (Scale 12 to 64), per stone: palette colour from its number, facet cells (Chebychev, Seed = 50 x stone number, Scale x 1.6 to 2.5) with the tone shifted per facet; dark rim: Distance To Edge < (w / 2) x Scale / 1254 where the stone is "covered"; earth speckle underneath (Scale about 110).

**R8 Maps from colour.** Height = lightness of the FINISHED colour (RGB to BW, power 1/2.2, stretch so the 99th percentile reaches 1); blur 0.8 px wrapping at the edges; 16-bit; normal = Sobel of that height, strength fitted to the reference's slope spread (the shared harness does this).

**R9 Kuwahara on a grainy bake.** Wrap-pad by 96 px, run `Kuwahara` anisotropic (Size 8, Sharpness 1, Uniformity 4, Eccentricity 1), cut the middle out; derive height from the new colour. Only worth it for noisy or grainy sources.

**R10 Measuring helpers.** `hp.periodicity_check(build, channel)` (does it repeat?), `hp.levels(array)` (how many flat levels), `a05_edge_density.py` (is it busy enough), `a06_stair_steps.py` (is the staircase too blocky).

---

## 8. Notes for the builders and for the shared tools

- `lib/bake_harness.save_array_png` fills only the red channel for a 2-D array (a cyan height, wrong scores): pass 3 channels. Suggest a fix in lib.
- `lib/bake_harness.new_bake_scene` leaves dithering on; for flat-patch recipes add `scene.render.dither_intensity = 0` (suggest in lib).
- `lib/recipe_tools.tileable_voronoi_group` outputs Position: do not hash it (use Color).
- `texture_compare`'s seam measure is inflated when a layout boundary sits on the wrap edge and noisy for flat-patch pictures; push layouts half a cell and confirm with a 2 x 2 periodicity test.
- Reusable from this folder (nothing in lib was changed): `scripts/hp_tools.py` (seamless stretched noise and cells with distance metric, warp group, palette ramp, per-cell random, outline helpers, padded photographs, compositor runner, periodicity and level checks), `scripts/r12_painted_slate_demo.py`, `scripts/r16_painted_gravel_demo.py` as worked examples.

---

## 9. Tested here: what I ran and what happened (failures included)

Everything ran in Blender 5.2.2 LTS (CPU Cycles, CPU compositor, `-t 2`), scripts in `experiments_hand_painted_look/scripts/`, outputs in `pictures/` and `data/`. Helper code: `hp_tools.py` (my own; the lib folder was not changed).

| Script | What it did | Outcome |
|---|---|---|
| `a01_measure_references.py`, `a01b`, `a01c`, `a04`, `a05`, `a06`, `a03` | measured the six references (palette, patches, outlines, edge hardness, streaks, maps, edge density, staircase) | numbers in section 2. **Failures:** my first "thin dark line" test (kernel 9) marked the whole mortar network and gave nonsense widths (replaced by a row-average dip measure and a stricter test); my first "edge rise" (10 to 90 percent over 8 px) read 6 px for edges that are about 1 px wide (replaced by jump / steepest slope over 4 px); the first streak measure for slate (autocorrelation) was dominated by the horizontal tile lines (replaced by run lengths and crops inside tiles). |
| `b00`, `b01`, `b02` | listed the compositor nodes (92 types), their sockets and menu options in 5.2.2 | table in 4.10 |
| `c00_compositor_smoke.py` | first compositor run | **crashed with a libEGL error** until `compositor_device = 'CPU'` was set; then Kuwahara, Posterize, Pixelate worked |
| `c01_posterise_methods.py` | five ways to get N flat levels | three runs: counting was first polluted by anti-aliasing, then by the PNG dither; after samples = 1 and dither 0 the counts are exact (4.1) |
| `c02_cells_palette_warp.py`, `c02b` | cells as patches, palette, jitter, warp sweeps; found the Position cut problem | first palette picture showed straight cuts inside cells; traced to hashing Position; fixed with Color output; strict periodicity test built here |
| `c04_streaks_and_brush_marks.py` | streaky noise, stretched cells, Wave, Gabor, Mapping noise | periodicity table in 4.5 |
| `c05_outlines_in_shader.py`, `c05b`, `c05c`, `c05d`, `c05e` | four shader outline routes, width calibration | first run: Distance To Edge mask all white (threshold in wrong units), then all black (a comment had swallowed a link in my script), then right; my area / centre-line width estimate was unreliable, so I calibrated on straight edges (4.7) |
| `c06_compositor_sweeps.py`, `c06b`, `c06c` | every stylising compositor node, sweeps, timings | first source (soft noise) showed almost nothing; second source (grainy cells) is the one used; Blur type list wrong at first (fixed from the error message); Bilateral Blur re-tested with the Determinator linked |
| `c08_compositor_seams.py`, `c08b`, `c08c`, `c08d`, `c08e`, `c08f` | filter seams and fixes | plain filter has a seam; padded bake and numpy wrap-pad fix it; **Translate/Transform with Repeat did not** (three attempts: zero shift and a full-tile shift changed nothing; a 96 px shift made a rolled copy that was still the plain filter) |
| `c09_compositor_details.py` | seam vs Size, colour space, Posterize spaces, compositor outlines, 16-bit height | numbers in 4.7, 4.10 |
| `c10_geometry_edge_tools.py` | AO, Bevel, Pointiness on a stepped relief and on a flat plane | table in 4.8 |
| `c11_palette_checks.py` | hex round trip, Color Ramp options, jitter strength | 4.9 |
| `c13_layered_dabs.py`, `c15_angular_cells_and_stones.py`, `c16_coordinate_snap.py` (+`c16b`) | layers, distance metrics and painted stones, coordinate snapping | 4.6, 4.4, section 5.2 |
| `r12_painted_slate_demo.py` + `run_slate_stages.sh`, `run_slate_tuning.sh`, `post_smooth_height.py`, `c14_kuwahara_and_consistency.py` | slate stack stage by stage, tuning, Kuwahara, height strategies, scoring with texture_compare | section 5.1 and 4.11. **Failures:** the first layout had a row boundary on the wrap edge (seam metric 8.95, tiling score 0, fixed by a half-row shift); my first smoothed heights were saved with the green/blue channels at 1.0 because of the `save_array_png` one-channel behaviour, so every smoothed score was wrong until I fixed `hp.save` and re-ran all of them |
| `r16_painted_gravel_demo.py` + `run_gravel_*.sh` | gravel stack, measured stone sizes, jitter and grain | section 5.2 |
| MCP tools | `search_manual_docs` (Kuwahara, Posterize, Pixelate, Mask To SDF, Dilate/Erode, Math, Map Range, Gabor, Voronoi), `get_python_api_docs` (CompositorNodeKuwahara), `search_api_docs` (compositing_node_group, compositor_device), `execute_blender_code_for_cli` on `empty.blend` (checked that the node has no Python settings, only sockets, and that the compositor device default is 'GPU') | all matched the experiments |

---

## 10. Not tested

- Kuwahara Size on other resolutions (2048, 4096); the manual says the size is in pixels, so scale it (NOT TESTED). Smaller wrap-pad margins than 96 px, margins for chained passes.
- Voronoi Position hashing in the plain (non-seamless) 2D/3D Voronoi; Smooth F1 and N-Sphere Radius features; Minkowski exponents other than 0.5, 1.5, 4.
- The Noise node's own Distortion input as a warp (the toolbox guide shows it).
- EEVEE and the GPU compositor (no graphics card here); Shader to RGB; Freestyle; Grease Pencil outlines; Fresnel/Facing outlines on 3D objects (Xeofrios' outline route).
- Compositor nodes not tried: Convolve, Anti-Aliasing, Inpaint, Glare, Denoise as stylising tools.
- AO / Bevel on higher-resolution or geometry-node displaced meshes; Pointiness in EEVEE.
- A normal made with the Bump node from the stylised height (the harness writes `normal_bumpnode.png`, I did not score it); height made from a shared structure instead of the colour.
- Hue jitter around red (hue 0 wraps) in the baked colour; larger numbers of palette colours (more than 8) in the demos.
- Texture painting, sculpting and geometry-node route to hand-painted looks (other helpers).
- mud_golden maps (the reference has none).

---

## 11. Sources

Dates are those on the page where it shows one; "no date shown" otherwise. "Search result only" = I saw only the search-result summary, not the page.

| Title | URL | Date | What it gave me |
|---|---|---|---|
| Blender 5.2 LTS Manual: Kuwahara, Posterize, Pixelate, Filter, Dilate/Erode, Mask To SDF nodes; Gabor, Voronoi, Math, Map Range (bundled copy read through the Blender MCP `search_manual_docs`) | https://docs.blender.org/manual/en/latest/compositing/types/creative/kuwahara.html (other pages in the same tree) | Blender 5.2.2 LTS, build 2026-09-15 | what each node and setting is meant to do; Snap = round down; Gabor inputs |
| Blender 5.2 Python API reference (bundled; `get_python_api_docs`, `search_api_docs`): `Scene.compositing_node_group`, `RenderSettings.compositor_device` (default 'GPU'), `CompositorNodeKuwahara` | https://docs.blender.org/api/current/ | same | how to drive the compositor from Python; why it failed headless |
| Blender 4.1: Compositor (release notes) | https://developer.blender.org/docs/release_notes/4.1/compositor/ | Blender 4.1 (no date shown) | Kuwahara Size input and High Precision (Classic) |
| Blender 5.0: Compositor (release notes) | https://developer.blender.org/docs/release_notes/5.0/compositor/ | Blender 5.0 (no date shown) | Composite node replaced by Group Output; compositing tree is a data block; new Convolve node; Extension mode options |
| Compositor new node: Kuwahara filter (devtalk thread, izo) | https://devtalk.blender.org/t/compositor-new-node-kuwahara-filter/29205 | first post 30 Apr 2023; update 26 Jun 2023 | anisotropic only artifact-free at Size 4+, ideally 8+; 4x faster but less accurate version; timings on large images |
| Realtime Compositor: Implement Anisotropic Kuwahara #110786 | https://projects.blender.org/blender/blender/pulls/110786 | 2023; search result only | the GPU implementation (said to be about 10 times faster than the CPU one) |
| Image and Video Abstraction by Anisotropic Kuwahara Filtering (Kyprianidis, Kang, Doellner), Computer Graphics Forum 28(7), pp. 1955-1963 | https://diglib.eg.org/handle/10.2312/CGF.v28i7pp1955-1963 | 2009; search result only | the method behind the anisotropic mode |
| On Crafting Painterly Shaders (Maxime Heckel) | https://blog.maximeheckel.com/posts/on-crafting-painterly-shaders | 29 Oct 2024 | classic vs generalised vs anisotropic Kuwahara, kernel size and sectors, multi-pass advice |
| NPR skin shader showcase breakdown (Xeofrios), Blender Artists | https://blenderartists.org/t/npr-skin-shader-showcase-breakdown/1485295 | 29 Sep 2023 | Voronoi strokes; fine noise on the coordinate to roughen edges without mixing colours; W layers + Snap; outline via Fresnel/Facing through a Voronoi |
| Procedural hand-painted skin shader created with Blender (80.lv) | https://80.lv/articles/procedural-hand-painted-skin-shader-created-with-blender | 10 Oct 2023 | confirms the shader is Voronoi-based (no settings) |
| Need help creating a procedural texture from an image (Renzatic's reply), Blender Artists | https://blenderartists.org/t/need-help-creating-a-procedural-texture-from-an-image/1450031 | 14 Feb 2023 | scratchy noise along line edges; Constant + B-Spline ramps stacked; toon shader |
| Tutorial: Procedural Blender Shader with Hand-Painted Look (lassyla, 80.lv) | https://80.lv/articles/tutorial-procedural-blender-shader-with-hand-painted-look | 18 Aug 2026 | an EEVEE, fully procedural example where noise does the work (no node details) |
| How to Create a Hand Painted Look in Blender (Martin Klekner, BlenderNation) | https://www.blendernation.com/2025/10/26/how-to-create-a-hand-painted-look-in-blender/ | 26 Oct 2025 | EEVEE toon route: Shader to RGB, Color Ramp, Grease Pencil outlines |
| Stylized Textures Production in Substance Designer (Jeff Horal, 80.lv) | https://80.lv/articles/stylized-textures-production-in-substance-designer | 27 Aug 2018 | greyscale first, edges and height, strip detail, brush strokes, "no magic button" |
| Check out updated Gabor noise node in Blender 4.3 (80.lv) | https://80.lv/articles/check-out-updated-gabor-noise-node-in-blender-4-3 | 21 Oct 2024 | Gabor gives interleaved bands with controllable direction |
| Using Kuwahara filter for anime style look in Blender (80.lv) | https://80.lv/articles/using-kuwahara-filter-for-anime-style-look-in-blender | 18 Nov 2025 | Kuwahara used for soft painterly renders (no settings) |
| Procedural Basics (Planetset docs): domain distortion | https://planetset-docs.readthedocs.io/en/latest/tutorials/canyons/ | no date shown | noise colour minus 0.5, scaled, added to Position, into Voronoi |
| Warp (Iñigo Quilez): f(p + h(p)) | https://iquilezles.org/articles/warp | the page did not load with the fetch tool (404); search result only | the name and formula of domain warping |
| Better Edge and Cavity Masking with Cycles (pavla, BlenderNation) | https://www.blendernation.com/2019/02/10/better-edge-and-cavity-masking-with-cycles/ | 10 Feb 2019 | pointiness, Bevel node and AO node as edge/cavity masks in Cycles |
| A better, procedural pointiness/edge detection in Cycles, Blender Artists | https://blenderartists.org/t/a-better-procedural-pointiness-edge-detection-in-cycles/1283892 | 8 Feb 2021 (reply 23 Oct 2022) | Bevel normal minus object normal as an edge mask; slower than Pointiness; Pointiness artifacts on low-poly meshes |
| Most direct way to resize with tiled/wrapped edges? (ImageMagick forum) | https://jqmagick.imagemagick.org/discourse-server/viewtopic.php?p=107153 | no date shown; search result only | the "tile 2 x 2, filter, crop the centre" idea for filtering a seamless picture |
| (inside this project) 02 Research - the shader node toolbox.md; 02 Research - seamless tiles and baking.md | same folder | 2026-10-19 | Noise/Voronoi/Bump/AO/Pointiness facts, tileable noise and Voronoi groups, seam measure |
