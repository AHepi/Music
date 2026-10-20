# 06 Cookbook - start here

What this is: the front page of the procedural-texture job. It says what the job made, which guide to read for which purpose, what every word means,
and how close each of the six surfaces got, in one table. Every number on this page is copied from a file, and the file is named next to it.

---

## 1. What this job made, in one example

**Example first (slate).** We were given a hand-painted slate roof: a colour picture of 1254 x 1254 dots, with its height map and normal map. The slate
build wrote a Blender generator that reads a small file of numbers (a **description**) and draws the roof from it as thousands of flat coloured shapes,
photographed from straight above. Three descriptions of the same roof, from small to large (`recipes/slate/final_report.json`, "classes"):

* **2,762 bytes** that list only the rows, the joints and one colour per slate: the picture already has the right structure (colour SSIM 0.711), but no paint.
* **6,667 bytes** that add paint RULES (measured statistics plus a random seed): the roof now looks like the right kind of surface (same-kind score 0.725),
  but the paint is in invented places, so it does not match the reference dot for dot (tier none).
* **453,054 bytes** that write down the outline of every flat patch of the reference (a trace): it matches the reference dot for dot at tier "close"
  (colour SSIM 0.836), but it is a compressed copy, not a recipe, and it cannot make anything new.

The same generator, fed with descriptions drawn at random from the measured statistics, made **eight new roofs** (same-kind 0.722 to 0.753), a
**2508-dot roof of new content** with no seam and no repeat, and two roofs nobody gave us (**cedar shingles** and **clay fish-scale tiles**) by changing
numbers (the fish-scale tiles also needed one new setting, for their rounded bottoms).

The six builds (brick, slate, wood, metal, mud, gravel) all did the same five things, and the guides explain each one:
1. **Prove how the reference's maps were made.** All six heights are the brightness of the colour picture, lightly blurred, and all six normal maps are the
   slope of that height. So the colour picture is the whole problem (relief guide, section 3).
2. **Describe the surface as numbers, from small to large, and record what each size buys** (the "ladder"; descriptions guide, section 3).
3. **Bake with one generator per surface** and score with two tools: "is it the same KIND of surface?" and "is it the same PICTURE, dot for dot?"
   (baking and checking guide, section 7).
4. **Make new tiles, a bigger area and other picture sizes** from the same generator (descriptions guide, sections 5 and 7).
5. **Carry the generator to a surface nobody gave us** by changing numbers (descriptions guide, section 6).

Every build was then re-run by an independent **checker**, whose findings (`recipes/<surface>/verifier_answer.json`) corrected several claims. The guides
include those corrections.

What the job did NOT do: the slate in separate layers (colour and fade, damage, moss, outline) is still being built (section 4, "05"); the realistic moss and
damage test is not started (`../LATER - realistic moss and damage over the painted colour and weathering - NOT STARTED.md`).

---

## 2. The six surfaces in one picture

![The six surfaces: reference, best traced L, small S, one new tile, transfer surface](pictures/06%20Overview%20-%20all%20six%20surfaces%20-%20small.jpg)

(Full size: [06 Overview - all six surfaces.png](pictures/06%20Overview%20-%20all%20six%20surfaces.png), 1348 x 1710 dots, 3.1 MB; the copy above is
972 x 1230 dots, 295 KB.)

How to read it: one row per surface. Columns: the **reference** we were given; the **best traced L** class (the closest dot-for-dot copy within 512 KB);
the **small S** class (the description of up to 8 KB that the build made); **one new tile** from a description drawn at random; the **transfer surface**
(a surface nobody gave us). The captions give the size, the tier and the colour SSIM or the same-kind score, from each build's `final_report.json`.

How the pictures were chosen (so that no favourite was picked): the new tile is the FIRST of each build's eight (the lowest seed), not the best; the
transfer is the first picture of each build's transfer. The picture was made by `checks/overview/make_overview.py` (plain Python with cv2, from existing
pictures only); the exact files it used are listed in `checks/overview/overview_files_used.json`. Each column in short:

| column | brick | slate | wood | metal | mud | gravel |
|---|---|---|---|---|---|---|
| best traced L | `outputs/final_L` | `outputs/L_trace_fine` | `outputs/ladder_L3_trace_480kw` | `outputs/L` | `outputs/L_final_traced_ground_plus_corrections` | `outputs/L_a100_s8` |
| small S | `outputs/final_S` (fitted, not rules) | `outputs/S2_stamps_grain` | `outputs/ladder_S1_layout_paint_grain` | `outputs/S` | `outputs/S_layout_ruts_clods` | `outputs/S_v4` |
| one new tile | `variations/tile_11` | `variations/var_101` | `variations/sample_101` | `variations/seed_1` | `variations/tile_101` | `variations/out/sample_01` |
| transfer surface | `transfer/cobble_1` | `transfer/out_cedar_1` | `transfer/deck_boards_seed1` | `transfer/hull_plates` | `transfer/snow` | `transfer/out/pebbles_1254` |

(All paths inside `recipes/<surface>/`; each folder holds `colour.png`. The mud new tile is marked "112 KB (!)": mud's sampler writes every clod into the
description, so its new-tile descriptions are 112,383 to 118,421 bytes, class L by size; section 5.)

---

## 3. How to read the guides: which one, in which order, for which purpose

**If you read only one thing:** this page, then the checklist ([06 How to start a new surface - checklist](06%20How%20to%20start%20a%20new%20surface%20-%20checklist.md)).

**Reading order for a first full read** (each step builds on the one before):
1. This page (what was made, the words, the results).
2. [06 Guide - descriptions - analyse, describe, generate, compare](06%20Guide%20-%20descriptions%20-%20analyse,%20describe,%20generate,%20compare.md):
   the method worked through on slate, then all six builds side by side. Read sections 1, 2, 3.3, 4 and 5 first.
3. [06 Guide - baking and checking maps](06%20Guide%20-%20baking%20and%20checking%20maps.md), sections 1, 7 and 9: what each score means and where it lies.
   Read this before trusting any number anywhere.
4. One surface from start to finish: its "04 Recipe" and "04 Lessons" (section 4 below). Slate is the most complete worked example; brick is the
   most honest about where its own tests stop.
5. The tool guides (06) when you need a particular Blender tool.
6. The research guides (02, 03) for background: what people do on the web and what was tested before the builds started.

**By purpose:**

| I want to ... | read |
|---|---|
| start a surface nobody has done yet | the checklist, then the 04 Lessons of the most similar surface (rows of pieces: brick or slate; planks: wood; plates and bars: metal; a ground with things in it: mud; a heap of loose pieces: gravel) |
| know how close each surface got, and what "close" means | section 5 of this page; descriptions guide sections 3 and 5; baking and checking guide section 7 |
| know what a Blender node does and what its settings change | pattern makers (Noise, Voronoi, Brick, Wave ...), shapers (Map Range, Color Ramp, Math, Mix ...), seamless tiles and coordinates (Texture Coordinate, Mapping, Vector Math) |
| make height and normal maps, Bump or Displacement | relief guide |
| make a picture look hand-painted | the painted look guide |
| build real 3D shapes for a surface | geometry nodes, curves, modifiers and physics guide |
| get maps out of Blender correctly, and check them | baking and checking maps guide |
| make a tile that repeats with no seam, a bigger area, or a bigger picture | seamless tiles and coordinates guide |
| know whether an add-on or another program would help | the three 03 guides |

---

## 4. Every guide, one line each

### Research guides (02): written before the builds; what people do, and what was tested here

* [02 Research - the shader node toolbox](../research/02%20Research%20-%20the%20shader%20node%20toolbox.md): every shader node that makes textures in Blender 5.2, grouped by job, with what each setting does (tested).
* [02 Research - seamless tiles and baking](../research/02%20Research%20-%20seamless%20tiles%20and%20baking.md): how to make node textures repeat with no seam and how to save the maps correctly (the donut trick, bake routes, colour spaces, 16-bit).
* [02 Research - geometry nodes, curves, modifiers and physics for surface detail](../research/02%20Research%20-%20geometry%20nodes,%20curves,%20modifiers%20and%20physics%20for%20surface%20detail.md): building a surface out of real 3D geometry and photographing it from above.
* [02 Research - how people make each surface](../research/02%20Research%20-%20how%20people%20make%20each%20surface.md): how artists build brick, slate, wood, rusted metal, mud and gravel, what was tested here, and a verdict per surface.
* [02 Research - getting a hand-painted stylised look](../research/02%20Research%20-%20getting%20a%20hand-painted%20stylised%20look.md): tools for the painted look, and the measured "look" of each reference (palette, patch size, outline width).

### Extra tools (03): would an add-on or another program help?

* [03 Research - Ucupaint](../research/03%20Research%20-%20Ucupaint.md): a free layer-stack add-on; it works on Blender 5.2 here, but it draws the same pictures as plain nodes and its patterns are not seamless. Verdict: not needed.
* [03 Research - Material Maker](../research/03%20Research%20-%20Material%20Maker.md): a separate free program for node-built maps; it runs here, but its best brick scored 0.28 same-kind. Verdict: borrow ideas, do not use it.
* [03 Research - MCP Blender Agent](../research/03%20Research%20-%20MCP%20Blender%20Agent.md): a tool that lets an AI run Blender by ready-made commands; it cannot set node settings or Color Ramp stops. Verdict: does not help this job.

### Surface recipes and lessons (04): one pair per surface

Each **Recipe** is the full story of one build (analysis, description format, every Blender tool with its settings, every result, dead ends, checker's
corrections). Each **Lessons** file is the short "what carries over" list for the next surface.

| surface | recipe | lessons |
|---|---|---|
| brick | [04 Recipe - brick - how it is made](../recipes/brick/04%20Recipe%20-%20brick%20-%20how%20it%20is%20made.md) | [04 Lessons - brick](../recipes/brick/04%20Lessons%20-%20brick%20-%20what%20carries%20over%20to%20other%20surfaces.md) |
| slate | [04 Recipe - slate - how it is made](../recipes/slate/04%20Recipe%20-%20slate%20-%20how%20it%20is%20made.md) | [04 Lessons - slate](../recipes/slate/04%20Lessons%20-%20slate%20-%20what%20carries%20over%20to%20other%20surfaces.md) |
| wood | [04 Recipe - wood - how it is made](../recipes/wood/04%20Recipe%20-%20wood%20-%20how%20it%20is%20made.md) | [04 Lessons - wood](../recipes/wood/04%20Lessons%20-%20wood%20-%20what%20carries%20over%20to%20other%20surfaces.md) |
| metal (rusted riveted steel) | [04 Recipe - metal - how it is made](../recipes/metal/04%20Recipe%20-%20metal%20-%20how%20it%20is%20made.md) | [04 Lessons - metal](../recipes/metal/04%20Lessons%20-%20metal%20-%20what%20carries%20over%20to%20other%20surfaces.md) |
| mud | [04 Recipe - mud - how it is made](../recipes/mud/04%20Recipe%20-%20mud%20-%20how%20it%20is%20made.md) | [04 Lessons - mud](../recipes/mud/04%20Lessons%20-%20mud%20-%20what%20carries%20over%20to%20other%20surfaces.md) |
| gravel | [04 Recipe - gravel - how it is made](../recipes/gravel/04%20Recipe%20-%20gravel%20-%20how%20it%20is%20made.md) | [04 Lessons - gravel](../recipes/gravel/04%20Lessons%20-%20gravel%20-%20what%20carries%20over%20to%20other%20surfaces.md) |

(The brick and gravel builders did not write their own guides; both pairs were written afterwards from their files and their checkers' findings, and say so.)

### Slate in layers (05)

* **05: in progress, not written yet.** The slate is being rebuilt as separate layers inside one recipe (colour and fade, damage, moss, outline and shadow),
  so that each can be changed on its own. Until its guide exists, the folder map and what its first version proved are in
  [README - folder map and what the skeleton proved](../recipes/slate_layers/README%20-%20folder%20map%20and%20what%20the%20skeleton%20proved.md).
  Nothing on this page covers it.

### Tool guides (06): one Blender job each, with every build's experience

* [06 Guide - descriptions - analyse, describe, generate, compare](06%20Guide%20-%20descriptions%20-%20analyse,%20describe,%20generate,%20compare.md): the method in plain words on slate, the six ladders side by side, where "procedural" ends and "tracing" begins, new tiles, transfers, scaling.
* [06 Guide - baking and checking maps](06%20Guide%20-%20baking%20and%20checking%20maps.md): getting maps out of Blender (photograph or Bake button, view transform, 8 or 16 bits, pixel filter) and the three checking tools, their yardsticks and their 17 blind spots.
* [06 Guide - relief - height, bump, displacement and normal maps](06%20Guide%20-%20relief%20-%20height,%20bump,%20displacement%20and%20normal%20maps.md): how height and normal maps were made from the colour and how close that can get; the Bump node, Displacement, OpenGL and DirectX; real geometry against colour-made height.
* [06 Guide - seamless tiles and coordinates](06%20Guide%20-%20seamless%20tiles%20and%20coordinates.md): Texture Coordinate, Mapping, Vector Math; the donut trick; whole-number layouts; warps; the half-tile test and the seam number; bigger areas and picture sizes.
* [06 Guide - pattern makers](06%20Guide%20-%20pattern%20makers.md): Noise, Voronoi, Brick, Wave, White Noise, Gabor, Magic, Gradient, Checker and Radial Tiling: what each makes, its settings, its traps, and what the builds really used.
* [06 Guide - shapers](06%20Guide%20-%20shapers.md): Color Ramp, Map Range, Math, Float Curve, Mix, Clamp, Hue/Saturation/Value, Separate and Combine: turning a soft grey into flat painted steps.
* [06 Guide - the painted look](06%20Guide%20-%20the%20painted%20look.md): flat patches, palettes, outlines, stamps, ragged edges, the staircase, grain and filters; what did and did not give a hand-painted feel.
* [06 Guide - geometry nodes, curves, modifiers and physics](06%20Guide%20-%20geometry%20nodes,%20curves,%20modifiers%20and%20physics.md): real geometry photographed from above (Set Material, wrap copies, Instance on Points, Distribute Points, curves, modifiers, Rigid Body) and the honest verdict of all six builds.
* [06 How to start a new surface - checklist](06%20How%20to%20start%20a%20new%20surface%20-%20checklist.md): the six Lessons files merged into one ordered checklist for a surface nobody has done yet.
* [06 Check - what was checked and fixed](06%20Check%20-%20what%20was%20checked%20and%20fixed.md): an independent check of all these guides afterwards (links, numbers against the files, plain words, what was really tested, whether a newcomer can follow the checklist), with every correction it made and what is still open.
* [07 Reuse - which tools work on which surfaces](07%20Reuse%20-%20which%20tools%20work%20on%20which%20surfaces.md): how much of the layered slate tools worked on brick, wood, metal, mud and gravel (every tool against every surface, what is missing to make the toolkit general, one picture sheet per surface).
* This page, and the overview picture [06 Overview - all six surfaces](pictures/06%20Overview%20-%20all%20six%20surfaces.png).

Other files: the project notes every helper read first, [PROCEDURAL_NOTES.md](../PROCEDURAL_NOTES.md) (the job in the person's words, the tools in `lib/`,
the method); the plans not started yet, [NEXT PHASE](../NEXT%20PHASE%20-%20separate%20layers%20for%20colour%20and%20fade,%20damage,%20and%20moss%20-%20NOT%20STARTED.md)
and [LATER](../LATER%20-%20realistic%20moss%20and%20damage%20over%20the%20painted%20colour%20and%20weathering%20-%20NOT%20STARTED.md).

---

## 5. The results, honestly, in one table

**Example first (metal).** The metal build's largest description (413,452 bytes) writes down 9,155 outlines traced from the reference's own rust. Its
bake reaches tier "close": colour SSIM 0.756, colour difference 4.90. The checker showed that even tier "exact" would be reachable for the maps, so what
keeps metal from "exact" is the colour picture. Its small description of rules (6,303 bytes) does not match dot for dot (tier none), but looks like the
same kind of steel (same-kind 0.523). Eight new tiles drawn from measured ranges score 0.525 to 0.603 on the same-kind tool, and ship hull plates were made by
changing only the description (`recipes/metal/final_report.json`; `verifier_answer.json`).

The general picture: **dot-for-dot accuracy came only from tracing the reference; "the same kind of surface" came from a few kilobytes of rules.**

| surface | best class within 512 KB, and its tier | colour SSIM | colour difference | what kept it from the next tier | the small S class | new tiles: same-kind score, mean (range) | transfer surface |
|---|---|---|---|---|---|---|---|
| brick | L, 497 KB, traced: **layout** | 0.673 | 5.71 | "close": normal error 13.93 (needs 12) | S, 7.8 KB, ellipses FITTED to the reference: tier layout, SSIM 0.532, same-kind 0.365 | **0.708** (0.684 to 0.730) | grey granite cobblestones (a re-coloured brick layout; by eye) |
| slate | L fine, 442 KB, traced: **close** | 0.836 | 2.85 | "exact": SSIM 0.92, edge skill 0.85, height 6, normal 4 not met | S2, 6.5 KB, rules: tier none, SSIM 0.569, same-kind 0.725 | **0.735** (0.722 to 0.753) | cedar shingles; clay fish-scale tiles (by eye) |
| wood | L3, 462 KB, traced: **layout** | 0.725 | 4.61 | "close": edge skill 0.523 (needs 0.55), normal 15.46 | S1, 6.2 KB, rules: tier none, SSIM 0.220, same-kind 0.635 | **0.626** (0.607 to 0.665), optimistic* | silver deck boards (by eye) |
| metal | L, 404 KB, traced: **close** | 0.756 | 4.90 | "exact": the colour (SSIM, edge skill, colour difference) | S, 6.2 KB, rules: tier none, SSIM 0.479, same-kind 0.523 | **0.569** (0.525 to 0.603) | ship hull plates (by eye) |
| mud | L final, 491 KB, traced: **layout** | 0.698 | 5.0 | "close": normal error 18.59 | S, 7.2 KB, rules: tier none, SSIM 0.367, same-kind 0.267 | **0.383** (0.353 to 0.416), not proven mud-like** | snowy track (by eye) |
| gravel | L, 426 KB, traced + stamps: **layout** | 0.666 | 5.29 | "close": normal error 22.33 | S_v4, 2.3 KB, rules: tier none, SSIM 0.213, same-kind 0.362 | **0.403** (0.365 to 0.456) | pebbles on sand (by eye) |

Sources: best class and S class from each build's `final_report.json` ("classes" block; gravel "classes" list; mud "mud" block), new tiles from its
"variation" or "variations" block. Each build's checker re-baked the class rows and matched them; of the eight new tiles, each checker re-baked one to four
and matched them too (each `verifier_answer.json`, "rescored" and "variation_really_different").
Sizes are in KB of 1024 bytes, the way the project's size check counts: 497 KB = 508,878 bytes; 442 = 453,054; 462 = 473,489; 404 = 413,452; 491 = 503,014;
426 = 436,388. The size classes are: S up to 8 KB, M up to 64 KB, L up to 512 KB.

\* Wood's sampler was tuned by raising the same-kind score, so its new tiles' score is "optimistic as evidence" (`recipes/wood/verifier_answer.json`).

\** Against the mud reference, the OTHER reference pictures score 0.179 to 0.498 on the same-kind tool (gravel 0.498), so the tool cannot show that the new
mud tiles are mud-like; that rests on the eye (baking and checking guide, section 7.4; `recipes/mud/verifier_answer.json`).

**Yardsticks for the same-kind column:** against the brick reference, the five other references score 0.164 to 0.324; the brick reference slid by
(311, 517) dots scores 0.992 (baking and checking guide, section 7.4, TESTED for that guide). The other-surface level was measured only against brick and
mud: for slate, wood, metal and gravel it is NOT TESTED.

What the table says, in plain words:
1. **"Close" was reached by two surfaces, slate and metal, and only by tracing.** Brick, mud and gravel miss it only on the normal error; wood also on edge
   skill. On slate, the normal error of a completely flat normal map is 11.27 degrees, so "close" (12 or less) is easy there: only slate's L fine (9.68) is clearly
   better than flat (descriptions guide, section 3.2). "Exact" was reached by nothing.
2. **Every best class is a trace**: a vector copy of the reference that cannot make a new tile. It proves the generator can say everything the reference
   says; it is not the recipe.
3. **The small S classes are where the recipes are.** All six fit inside 8 KB. Five are rules plus measured statistics plus a seed (tier none, as expected:
   invented paint is in invented places). Brick's S is different: its 146 ellipses are fitted to the reference, which is why it reaches tier "layout".
4. **New tiles are good where the surface is elements in rows** (slate, brick: the checkers say they read as the same wall and roof, but less bold than the
   reference) **and weak where it is a busy scatter** (mud, gravel: the checkers saw "flat confetti ground", "small flat kite-shaped" stones).
   Every surface's eight new tiles are one narrow family (same palette, same layout family).
5. **Transfers were all judged by eye**: there is no reference for a surface nobody gave us, so there is no score. Each took one short script; where the
   builders counted, about 10 to 20 minutes of work, which nobody could check. Only gravel's pebbles and metal's hull plates were numbers alone; the others
   needed small additions: brick three optional sampler keys, cedar shingles a sampler option (`fitted=`), fish-scale tiles one new setting (rounded
   bottoms), snow one sampler option, deck boards sampler options and two hand-written lists (descriptions guide, section 6). Brick's cobblestones are "the brick layout re-coloured" (checker).
6. **Description size:** the rule-based descriptions are 2.3 to 7.2 KB; new-tile descriptions are 2.4 to 9.4 KB, except mud's, whose sampler writes every
   clod (112,383 to 118,421 bytes per tile). A larger set should store seeds and statistics, never shape lists (descriptions guide, section 8).

Failures and limits that matter (all recorded in the guides named):
* No description reached tier "exact"; four of six never reached "close" (above).
* The best "same kind" for new tiles is 0.735 (slate), far from the 0.99 of a re-arranged copy of a reference.
* The same-kind tool cannot tell new mud tiles from other surfaces (above), and its seam number is fooled by grain (brick's traced L went from tiling
  0.444 to 1.0 when grain was added, with no change at the seam; `recipes/brick/verifier_answer.json`).
* Real 3D geometry did not match any of these references, because their height is the brightness of the paint (brick's bright mortar is HIGH)
  (geometry guide, section 11; relief guide, section 9).
* Several builders' first claims were wrong and were corrected by the checkers: metal's map ceiling (6.7 degrees was a measuring mistake; 3.71 is right),
  gravel's half-tile numbers (measured at 512 dots, not 1254) and area time (252.6 s, not 173 s), wood's "no generator code changed" (cannot be proven),
  golden mud's tier "close" (only because its height and normal could not be measured). The guides carry the corrected numbers.

---

## 6. Words used (one meaning per word, on this page and in the checklist)

The 06 guides use the same words. A few 04 guides use other words for the same thing; where that happens it is said below.

**The pictures**
* **tile** = one square picture that is meant to be laid side by side, like a floor tile; the references and the finals are 1254 x 1254 dots.
* **dot** = one pixel of a picture. **picture size** = how many dots across (512, 1254, 2508).
* **reference** = one of the six pictures we were given (brick, slate, wood, metal, mud, gravel), each with its height map and normal map
  (plus golden mud, colour only).
* **maps** = all the pictures of one tile together: the **colour picture**, the **height map**, the **normal map**, the **roughness map** and the **metallic map**.
* **height** = how raised a place is. The **height map** shows it in grey: white = high, black = low; saved with 16 bits so that gentle slopes do not turn into steps.
* **normal map** = a blue-violet picture whose colour at each dot says which way the surface there is tilted, so that light can fall on it as if it were
  raised. Blender reads the "OpenGL" kind (green = tilted toward the top of the picture).
* **roughness** = how matt (1) or shiny (0) a place is. **metallic** = whether a place is metal (1) or not (0). The builds bake both maps, but the
  references have none, so neither was ever scored.

**The method**
* **description** = the small file of numbers (JSON) that a generator reads: element lists, palettes, settings, seeds. Never a grid of dots.
* **generator** = one Blender script per surface that turns ANY description of that surface into maps.
* **build** = one of the six surface jobs in `recipes/`; **builder** = the helper who made it; **checker** = the independent helper who re-ran it afterwards.
* **element** = one thing in a picture a person would point at: a brick, a slate, a plank, a bar, a rivet, a stone, a puddle, a rut.
  (The slate guides call an element a "piece", and so does the geometry guide for an element built as real geometry.)
* **layer** = one kind of content in a description, drawn on top of the ones before: layout, one colour per element, outline, paint or wear, stamps, grain.
* **patch** = an area of one flat colour. **palette** = the short list of colours a picture is made of.
* **stamp** = one small shape put down many times (a drip, a speck, a flake). A **made-up stamp** gets its place from a random seed (slate's paint);
  a **traced stamp** gets its place copied from the reference (gravel's specks).
* **outline** = a dark line along the edge of a patch or an element. (The brick guides call brick's outline the "ring".)
* **grain** = a tiny random lighter-or-darker change at the size of 1 to 3 dots, kept as a separate switch.
* **size classes S, M, L** = descriptions of up to 8, 64 and 512 KB (KB = 1024 bytes, as `lib/description_audit.py` counts).
* **ladder** = the table of what each layer, or each description size, bought in accuracy.
* **procedural** = rules plus measured statistics plus a seed: change the seed and you get a new, different, valid tile. **fitted** = each element of THIS
  picture written down as a few meaningful numbers. **tracing** (a **traced** description) = the outline of every flat patch of THIS picture written down: a
  compressed copy. Only procedural descriptions can make new tiles.
* **sampler** = a script that draws a NEW description at random from the statistics measured on the reference. **new tile** = a tile made from such a description.
* **recipe** is used in three ways in these guides: a "04 Recipe" file (the story of one build); a Blender node setup or generator script that makes a
  surface (baking and checking guide); and, in "a copy, not a recipe", a description that can make new tiles. The sense is always clear from the sentence.
* **area** = one picture bigger than a tile, filled with new content (here 2508 x 2508 dots, the content of 2 x 2 tiles).
* **transfer** = making a surface nobody gave us with the same generator.
* **plain Python** = a Python script run on its own, outside Blender (`python3 -I script.py`; the `-I` stops it loading stray files from the folder);
  **numpy** and **OpenCV** (`cv2`) are the libraries those scripts use for sums on pictures. **Cycles** = Blender's renderer, the part that turns a scene
  into a picture.
* **photograph** = the project's way of making maps in Blender: a camera straight above a flat 1 x 1 square that glows with one channel at a time.
  **painter route** = drawing thousands of flat coloured shapes back to front and photographing them (all six builds). **geometry route** = building real raised
  geometry and photographing its true height (tried by all six, used by none).

**Seams**
* **seamless** = when tiles are laid side by side, no line shows where one meets the next. **wrap edge** = where the last column meets the first again
  (and the last row the first row).
* **half-tile test** = bake the recipe twice, the second time with everything slid by half a tile, and compare it with the first picture rolled by half;
  a seamless recipe gives the same picture. It proves the drawing wraps; it cannot see content that does not repeat (seamless guide, section 8.1).
* **seam number** = the jump across the wrap edge divided by an ordinary jump between neighbouring dots (1.0 = no seam). The references themselves score
  1.69 to 2.49 (they have a mild seam), and the number is fooled by hard edges and by grain (seamless guide, section 8.2).

**The two scoring tools and their words**
* **same-kind score** = the overall number of `lib/texture_compare.py`: "does this look like the same KIND of surface as the reference, wherever things
  are?" 1 = the same by its measures. Yardsticks (baking and checking guide, section 7.4): the brick reference slid to a new place 0.992; other real reference
  pictures 0.16 to 0.50 (not "about 0.1", as the project notes once said); a blurred copy 0.241.
* **dot-for-dot tool** = `lib/pixel_compare.py`: "is this the same PICTURE as the reference, dot for dot?" It gives several measures and a tier; there is no
  single dot-for-dot score. Its measures:
  * **colour SSIM** (colour similarity) = how alike the light-and-dark structure of two pictures is, dot for dot; 1 = the same picture. It is high for any flat
    picture, so never judge a new tile by it.
  * **colour difference** (Delta E, the colour error) = the average colour difference between dots in the same place; about 2.3 is the smallest difference most
    people see side by side, 10 is clearly another shade.
  * **edge skill** = the share of the reference's edges that are within 2 dots of an edge of yours, with the share a wrongly placed copy gets by luck taken off;
    0 = luck, 1 = every edge in place.
  * **height error** = the average height difference in steps of 255, after the best brightness-and-contrast fix.
  * **normal error** = the average angle between your normal map and the reference's, in degrees. **flat normal** = the error of a normal map with no tilt
    at all: the "do nothing" yardstick (brick 16.72, slate 11.27, wood 24.11, metal 13.26, mud 23.5, gravel 24.46; baking and checking guide, section 7.5).
* **tier** = the dot-for-dot tool's verdict, reached when ALL its limits pass (from the top of `lib/pixel_compare.py`):

| tier | edge skill at least | colour SSIM at least | colour difference at most | height error at most | normal error at most |
|---|---|---|---|---|---|
| none | (any limit of "layout" missed) | | | | |
| layout ("the features are in the right places") | 0.30 | - | 20 | 40 | - |
| close ("a careful eye needs a side-by-side") | 0.55 | 0.60 | 10 | 20 | 12 degrees |
| exact ("practically the same picture") | 0.85 | 0.92 | 3 | 6 | 4 degrees |

* **correlation** = a number from -1 to 1 that says how closely two sets of numbers rise and fall together: 1 = exactly together, 0 = no relation,
  -1 = exactly opposite (brick's real raised bricks correlate -0.15 with the reference height: slightly opposite).
* **percentile** = the 1st percentile of a picture's brightness is the brightness that 1 % of its dots are darker than; the 99th, the one that 99 % are
  darker than (used to find a new surface's height stretch).
* **plain slope** and **Sobel slope** = two ways to make a normal map from a height: plain = right neighbour minus left neighbour (and lower minus upper),
  halved; Sobel = the same, also counting the rows (or columns) on either side at half weight, so slightly smoother.
* **derivation** = the small rule that turns a colour picture into a height map (grey brightness, a stretch or tone curve, a slight blur) and a normal map
  (the slope of that height times a whole-number strength). **derivation ceiling** = how close the derived maps get even with a perfect colour picture: 3 to
  5 steps of height and 2.7 to 4.6 degrees of normal on the six references (relief guide, section 3).
* **TESTED** = run on this machine and measured, with the file named. **NOT TESTED** = only read, or only reasoned.

---

## 7. Where the guides disagree, and which to trust

Checked for this page by reading all eight 06 guides and the twelve 04 guides side by side.

**Fixed in the guides** (small, and certain from the files or the code):
* "Another surface scores about 0.1" (in five 06 guides and five 04 Recipes): today's tool gives 0.16 to 0.50 (baking and checking guide, section 7.4).
* "The same-kind tool reads a smoothed reference height" (relief guide; slate, wood and gravel guides): since the tool was changed at 15:45 on 19 October it
  reads the 8-bit upload, like the dot-for-dot tool (`lib/texture_compare.py`). The smoothed-height scores those builds report are still real numbers; only
  the stated reason was out of date.
* "`save_array_png` writes only the red channel" (relief guide): that was an older copy; the current one writes grey into all three channels (baking and
  checking guide, section 3).
* The references' seam numbers "1.14 to 2.49" (seamless guide): 1.69 to 2.49 (re-measured for this page, section 8).
* Brick's map ceiling: 3.02 after the best fit, 3.05 before it (both in `recipes/brick/scores/ref_roundtrip/pixel.json`); the guides now say which is which.
* Metal's height-route numbers: the geometry guide quoted them before the best fit, the relief guide after it; both are now labelled.
* Brick's new-tile descriptions: 9.3 to 9.4 KB (9,523 to 9,582 bytes), not "about 9.5 KB"; and "every procedural description is class S" now notes brick's
  (just over 8 KB) and mud's (112 to 118 KB) new-tile descriptions.
* "Every tile that reaches a tier is a trace" (painted look guide): brick's S and M reach "layout" with FITTED ellipses.
* Metal's Lessons said "KB of 1024 bytes" over a table written in KB of 1000 bytes; the note now says so.

**Not changed, but read them this way:**
* **Two numbers for brick's L class.** `recipes/brick/final_report.json` holds two bakes of it: the "classes" block (SSIM 0.673, colour difference 5.71, normal
  13.93; the one the checker re-baked and matched) and the "rate_distortion" row (0.672, 5.73, 13.95). The brick guides and this page use the first; the
  descriptions guide's ladder table uses the second. They differ only in the third decimal.
* **Sizes in KB.** Most guides count 1024 bytes per KB, as the size check does; the metal and mud guides mostly count 1000 (metal's L is "413 KB" there,
  404 KB here). The byte counts are the same everywhere; trust the bytes.
* **Different words for the same thing in the 04 guides.** Each 04 guide defines its own words at its top, so each is clear on its own, but across guides the
  same-kind score is also called the "kind score" (mud) or the '"same kind" score' (slate, wood); the outline is the "ring" (brick); an element is a "piece"
  (slate); colour difference is also "Delta E" (metal); the seam number is also the "seam ratio" or "seam measure". This page and the 06 guides use one word each.
* **The research guides (02, 03) quote the project notes' "another surface about 0.1"** in places (the geometry, Material Maker and Ucupaint guides). They
  were left as written; read their same-kind scores against the yardsticks of section 5 (other real surfaces 0.16 to 0.50).

---

## 8. What was tested for this page, and what was not

TESTED for this page:
* The overview picture: `checks/overview/make_overview.py` (plain Python, `python3 -I`, numpy and cv2; no Blender), from 30 existing pictures listed in
  `checks/overview/overview_files_used.json`. Its captions were checked against the `final_report.json` files by hand.
* Every relative link on this page, in the checklist and in all 06 and 04 guides: `checks/overview/check_links.py` (it reports broken links and exits with 1 if
  there are any).
* The seam number of each reference with the project's own function (`seam_ratio` in `lib/texture_compare.py`): brick 2.22, slate 1.69, wood 2.24, metal 2.02,
  mud 2.30, gravel 2.49, golden mud 1.72 (used to correct a typo in the seamless guide).

Quoted, not re-run: every other number on this page, from the files named next to it. No Blender bake was made for this page.

NOT TESTED: whether a person new to this job can follow the reading order above (nobody has tried it yet). An independent check made afterwards read
the checklist as a newcomer would and lists what is missing (for example: the same-kind tool cannot score a new surface until its name is added to the
tool): [06 Check - what was checked and fixed](06%20Check%20-%20what%20was%20checked%20and%20fixed.md), section 5.
