# 04 Lessons - gravel - what carries over to other surfaces

This file is for the day you start a surface nobody gave you (pebbles, crushed rock, a forest floor of leaves, a beach, a heap of coal). It says what the
gravel work taught, in the order you would use it. The numbers are the gravel's; each one names the file it comes from (all paths from the gravel folder,
`recipes/gravel/`). It was written after the build from the builder's files and the checker's report (`verifier_answer.json`); the builder's own tool
refused to write it. The full recipe is `04 Recipe - gravel - how it is made.md`.

Words used: the **tile** is the 1254 x 1254 picture; a **dot** is one picture dot (pixel); the **description** is the small file the generator reads;
a **stone** is one piece of gravel the generator makes up; a **patch** is an area of one flat colour copied from the reference; a **stamp** is a tiny
round patch copied from the reference, written as three numbers (x, y, radius); the **"same kind" score** is `lib/texture_compare.py` (same kind of
surface?); the **dot-for-dot tool** is `lib/pixel_compare.py` (same picture?).

## The big lesson first: gravel is the opposite of slate

A slate roof has a fixed layout: rows and black joints. A few numbers per slate put every joint in the right place, so even a 2.7 KB slate description scores
colour SSIM 0.71 dot for dot (`../slate/04 Recipe - slate - how it is made.md`). Gravel has no layout: it is a random heap. Example: a plain brown square
scores SSIM 0.444 against the gravel reference, and the finished made-up gravel only 0.206 (0.213 when baked in Blender), because every made-up stone is somewhere the reference has none
(`final_report.json`, "procedural_ladder").

**The general rule:** before you start, ask "does this surface have a layout (rows, a grid, planks, plates), or is it a heap (stones, leaves, crumbs)?"
* **Layout surface:** a few kilobytes of layout buy dot-for-dot structure; tracing the paint buys the rest (slate reached "close" at 264 KB).
* **Heap surface:** a made-up recipe can only be judged by the "same kind" score and by eye; only tracing gives dot-for-dot accuracy, and a busy heap
  is expensive to trace (gravel's best traced copy is 426 KB and still only tier "layout").

## How to start a new surface (the checklist, in order)

1. **Prove how the maps were made, before anything else (plain Python, an hour at most).** Fit a straight mix of red, green and blue with cut-offs, a small
   blur and a normal strength that turn the reference COLOUR into the reference HEIGHT and NORMAL. For gravel: red and blue count, green hardly at all;
   blur 0.5 dots; 5.01 steps of error; normal strength 10 from the uploaded height (0.34 degrees) (`scores/derivation_ceiling_log.txt`). The fit also gives
   the **ceiling**: even a perfect colour picture would give a normal map 4.6 degrees off, so the tier "exact" (4 degrees) was impossible from the start.
   Fit the mix even when ordinary grey looks good enough: on gravel ordinary grey was nearly as good (5.08), but only the fit tells you that.
   (Script to copy: `analysis/derivation_ceiling.py`; a 30-line least-squares fitter is in `analysis/derivation_parametric.py`.)
2. **Snap the colour picture to k colours and score the snapped picture** (`analysis/palette_ceiling.py`). Gravel: 8 colours give SSIM 0.855, 24 colours
   0.923 (`scores/palette_ceiling.json`). This is the best any flat-patch description can do.
3. **Count the patches BEFORE choosing how to describe the surface.** Gravel at 24 colours has 18,881 patches over 12 dots, and their outlines take 1,182 KB
   (`scores/trace_experiment.json`); slate had 9,383 and fitted in 442 KB. If the outlines of the patches over 12 dots do not fit in 512 KB, tracing cannot
   reach "close" and you should plan for a made-up recipe judged by the "same kind" score and the eye.
4. **When the pieces touch, measure statistics instead of hunting for each piece.** Finding single stones failed (237 merged pieces for about 1,500 stones,
   `analysis/stones_found.json`). What worked (`scores/measurements.json`): the share of each kind of dot (67.8 % stone); the size curve ("how much
   survives opening with a disc of radius r", for r = 1 to 48); the colours and how the colour mix changes with size (small stones brownish grey, big
   stones blue-grey); the shadow band; the light direction; how much windows of the picture differ from each other (stone share 4.5 %, big-stone share
   7.4 %, `scores/window_spread.json`).
5. **Measure which side of a border gets darker before you draw outlines.** Gravel looks outlined, but the soil gets darker toward each stone (lightness
   31.4 down to 24.6 over 8 dots) while the stone's edge does not (20.0 to 21.2): it is a shadow on the soil, not a dark line round the stone
   (`scores/measurements.json`). Also measure where the light comes from (gravel: the top; lightness falls 0.061 per dot going down a big stone).
6. **Build the generator as a painter: flat shapes drawn back to front.** Ground; soil lumps; then the stones, smallest first so the big ones lie on top,
   each stone as shadow, rim, body, lit face, shaded face, facets, flakes. PLACE the big ones first (so small ones fill the gaps) but DRAW them last.
   The Blender part (flat faces, one emission material per picture, overhead camera, wrap copies) is the same as for slate and needs no change.
7. **Calibrate counts and spacing automatically, then check by eye, then measure the result again in Blender.** The builder's calibration
   (`analysis/calibrate_sampler.py`) drew the tile with OpenCV (about 4 s per try, the builder's figure) and nudged one number at a time until the size curve matched. Three traps
   were found (Recipe guide, Appendix A8 and A10):
   * the first calibrated tile matched the curve but its stones were 1.5 times too small by eye (redone with sizes taken from the biggest stones);
   * the match was an average over all sizes, so the many small sizes hid a big miss at the big end: at disc radius 32 the reference keeps 32 % stone,
     the final tile 7 %;
   * the quick OpenCV drawing is not the Blender picture: the same description measures 67.4 % stone drawn and 61.1 % baked.
   So: give the big sizes their own weight in the match, and measure the Blender picture, not only the quick drawing.
8. **Score with both tools, look at every sheet, and trust neither score alone** (traps below).
9. **Only then** make the sampler (new tiles), the big area, the resolutions and a transfer to a new surface.
10. **Re-find the height stretch for every new surface.** Pebbles on sand with the gravel stretch: 62 % of the height map is full white
    (`../../cookbook/pictures/gravel-strips-numbers.json`). Rule that worked: take the 1st and 99th percentile of the height mix over your own tile and
    stretch them to (nearly) the full range: the pebbles used 10 and 245 (`analysis/make_transfer_description.py`); the slate work used 0 and 255 for its
    cedar shingles (`../slate/04 Recipe - slate - how it is made.md`).

![height stretch on a new surface](../../cookbook/pictures/gravel-strip-height-stretch.jpg)

(Pebble colour; height with the gravel stretch (mostly white); height with the pebbles' own stretch.)

## What each layer buys (gravel numbers, 1254 dots)

**Made-up gravel** (`final_report.json` "procedural_ladder"; quick OpenCV drawings scored with both tools)

| layer added | description size | what it fixed | what it did NOT fix |
|---|---|---|---|
| ground colour only | 178 bytes | nothing to look at; SSIM 0.444 (the best SSIM of the whole ladder) | everything |
| + soil lumps and specks | 1,105 bytes | the crumbly soil; "same kind" 0.17 to 0.20 | no stones |
| + tiny and small stones | 1,857 bytes | "same kind" 0.247 | big stones |
| + medium and large stones | 2,186 bytes | "same kind" 0.408 | the biggest stones |
| + biggest stones (all five classes), each with shadow, rim, facets and flakes | 2,364 bytes | "same kind" 0.437 | dot for dot: SSIM 0.206, tier none |

The same five classes WITHOUT shadow, rim, facets and flakes score 0.352: that detail is worth +0.085 and costs no bytes (only values change).

**Traced gravel** (`final_report.json` class rows; baked in Blender)

| layer added | description size | what it fixed | what it did NOT fix |
|---|---|---|---|
| patches over 250 dots | 85 KB | the big stone masses in place; SSIM 0.453 | edges (skill 0.114), soil grain; looks like stained glass |
| patches over 100 dots | 204 KB | SSIM 0.513, edge skill 0.242 | fine edges |
| patches over 250 + stamps over 12 dots | 270 KB | edge skill 0.593, tier "layout" | normal error 25 degrees |
| patches over 100 + stamps over 8 dots | 426 KB | SSIM 0.666, colour difference 5.29, height error 18.5: four of five "close" limits | the normal error (22.3 degrees; "close" needs 12) |

Short version: **for a heap, statistics buy the look cheaply (2.3 KB), stamps buy the match expensively (hundreds of KB), and outlines alone buy little.**
Stamps (tiny discs at the specks' own places, three numbers each) beat finer outlines: about 18,000 stamps lifted the edge skill from 0.114 to 0.593 for
185 KB, while outlines 2.5 times finer lifted it only to 0.242 for 120 KB.

## Traps (things that cost time here and will cost time on the next surface)

* **Dot-for-dot SSIM gets WORSE as you add made-up detail.** Flat brown 0.444; with every stone 0.206. Never use SSIM (or any dot-for-dot number) to judge
  made-up content; use the "same kind" score and your eyes.
* **The dot-for-dot normal error also punishes made-up detail.** On the final tile: flat normal map 24.5 degrees, strength 5: 31.6, strength 10 (used):
  37.8, strength 20: 45.2, strength 40: 52.7 (`../../cookbook/pictures/gravel-strips-numbers.json`). Choose the strength from step 1 of the checklist,
  not from this number.

  ![normal strength](../../cookbook/pictures/gravel-strip-normal-strength.jpg)

* **The "same kind" score alone misses shapes and colour casts.** The first round S_v2 (stones 1.5 times too small) scored a hair HIGHER than the final S_v4
  (0.378 against 0.362; `final_report.json`), inside the seed noise of 0.03 to 0.05 (`builder_answer.json`). Small colour tweaks moved it 0.01 to 0.02
  (`scores/tune_texture_round1.json`). Only the picture could choose.
* **A height smoothed by 0.8 dots scores differently on the "same kind" tool.** For S_v4, a copy whose height got a 0.8-dot smoothing
  (`analysis/score_folder.py`, the "smoothed-height view") scores 0.435 against 0.362 as baked, all of it in the height part (0.402 to 0.645). The reason first
  given here, that the tool reads a smoothed reference height, is out of date: since the tool was changed at 15:45 on 19 October it reads the 8-bit upload
  (`lib/texture_compare.py`; `../../cookbook/06 Guide - baking and checking maps.md`, section 5), and smoothing a CORRECT height lowers its score (0.992 -> 0.830
  there). Report the as-baked score as the main number and say which one you quote.
* **Change brightness, not red, green and blue separately.** Separate random changes turned dark grey stones purple and green; one change applied to all
  three keeps the hue (`"jitter_mode": "brightness"`).
* **"Find the pieces by connected colour areas" fails when the pieces touch and share colours** (gravel: 237 pieces for about 1,500 stones). Go to
  statistics early.
* **Real 3D geometry does not help when the reference maps were made from the colour.** Real blocks with Geometry Nodes are quick (under 10 s) but the
  "same kind" score fell from 0.362 to 0.173, and a 50/50 hybrid height to 0.257 (`final_report.json`, "geometry_route"). The research guide's hint that
  hybrids help gravel did not hold here. Keep real geometry for a floor that must stick out in 3D.
* **A traced copy of a picture does not repeat smoothly.** The traced gravel descriptions have seam numbers 2.8 to 11.4 (1.0 = seamless): their patches were
  cut out of a picture that stops at its edge. A made-up tile passes the half-tile test (mean difference 0.78 steps at 1254 dots, checker,
  `verifier_answer.json`).
* **The audit's list limit can be dodged.** Stamps grouped by colour stay under 4,000 numbers per list (biggest 3,963, checker) and pass, although the
  description holds 138,857 numbers. Report traced descriptions as tracing, whatever the audit says.
* **Label a sweep strip from the description you really use.** Five gravel strips said "used" for values that were not used, or named the wrong layers
  (corrected copies in `../../cookbook/pictures/`). Also say at what size a strip was made: the blur that is "width 2" at 1254 dots is about "width 1" at 640.
* **Quote the size a test was run at, and the run a time belongs to.** The builder's report gave its 512-dot half-tile numbers as 1254-dot numbers, and
  gave the 2508-dot area bake 173 s, which belongs to a different, smaller bake (the area took 252.6 s, `area/out/area_2508/bake.json`).
* **Times on a shared machine are noise.** Making the same shapes took 9.1, 22.6 and 9.3 s in three runs (`resolution/resolution_report.json`); the
  checker baked the same tile in 61.3 s where the builder took 99.5 s. Compare only runs made side by side.
* **Never stop processes by name on a shared machine.** The builder's `pkill -f run_everything.sh` may have stopped other builders' scripts of the same name.
* **When you add a setting, make every layer follow it.** The light-direction setting moves the stones' lit faces but the soil lumps' lighter tops stay at
  the top (fixed in `generator/gravel_layers.py`).
* **A "lesson" in a builder's notes is not proven until the final tile uses it.** The notes say "draw big soil lumps first, small on top"; the final S_v4
  draws them the other way round and no score compares the two.

## What is specific to gravel, and what is general

General (reuse as it is): the derivation proof and its ceiling; the palette ceiling; counting patches before choosing a description; statistics plus
calibration when pieces touch; measuring shadow sides and light direction; the painter (flat shapes back to front, photographed by Blender, wrap copies);
stamps for specks; brightness-only colour changes; the height stretch from the tile's own percentiles; the half-tile test; the two scoring tools used
together with the eye.

Gravel only (change THESE numbers for a new heap surface, not the code): five size classes and their counts; corners per stone (3 = shards, 4 to 5 =
blocks, 7 to 12 = pebbles); chipping; spacing; shadow width; facets and flakes; rust share; soil lumps and specks; the colour mix per size class.

Proof that it carries over: **pebbles on sand** (`transfer/`) was made from the gravel description by changing numbers only (palettes, size classes,
corners, chipping, spacing, shadow, light, soil counts) plus the re-found height stretch; no generator code changed (checker). 1,992 bytes, baked in
48.2 s, seamless (half-tile test at 512 dots: 1.54 steps, 0 % over 40). There is no pebble reference, so it was judged by eye: it looks like a pebble beach.

![pebbles on sand](transfer/pebbles_sheet.png)

## Slate and gravel side by side

| | slate (layout surface) | gravel (heap surface) |
|---|---|---|
| best made-up description, dot for dot | 2.7 KB layout only: SSIM 0.711 | 2.3 KB: SSIM 0.213 baked (worse than a flat colour, 0.444) |
| best made-up "same kind" score | 0.73 (S2, with grain) | 0.362 as baked, 0.435 smoothed-height view |
| patches over 12 dots at 24 colours | 9,383 | 18,881 (1,182 KB of outlines) |
| tracing reached | "close" at 264 KB | "layout" at 270 and 426 KB |
| normal-map ceiling from the colour | 2.8 degrees | 4.6 degrees ("exact" impossible) |
| new surface by numbers only | cedar shingles (fish-scale tiles needed one new setting) | pebbles on sand |
| number that had to be re-found | height stretch | height stretch |

(Slate numbers from `../slate/04 Recipe - slate - how it is made.md`; gravel numbers from `final_report.json` and `scores/trace_experiment.json`.)

## What I would do next (honest; none of this was built or tested)

* **Bigger stones.** Weight the big sizes in the calibration and measure the Blender picture, not the quick drawing (the final tile keeps 7 % stone at
  disc radius 32 against 32 % in the reference).
* **Chunkier stones.** The reference stones are blocks with several faces; the made-up ones are flat kite shapes with a cartoon shadow. Try more facets
  that share edges, one face per side lit by the light direction.
* **Soil grain.** The reference soil is a grainy orange speckle; the made-up soil is one flat brown with a spike in the brightness curve. A fine seamless
  noise in the soil colour (the project's 4D noise group) is the obvious try.
* **Colour cast.** The made-up tile is a little too orange-red (average Lab 23.8, 4.1, 6.4 against 24.5, 2.5, 3.8; `scores/S_v4_texture_compare.json`).
* **A class-M made-up description** ("place the biggest stones of the reference one by one, make up the rest") needs a stone finder that works; none does yet.
* **Make the soil lumps follow the light setting.**
* **Library changes the builder asked for** (`builder_answer.json`, "changes_wanted_in_lib"): show the per-surface ceiling next to the tier limits; a flag
  that skips dot-for-dot SSIM for made-up content; let the audit accept rows of equal length; a shared "painter" tool in lib (slate and gravel each carry a
  copy of the same 150 lines); a crop option for sweep strips; a small shared least-squares fitter.
