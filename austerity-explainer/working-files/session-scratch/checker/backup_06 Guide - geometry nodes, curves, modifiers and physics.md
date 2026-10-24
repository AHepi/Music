# 06 Guide - geometry nodes, curves, modifiers and physics

What this is: a guide to the Blender 5.2 tools that build REAL geometry for a surface (raised bricks, tilted slates, ruts, cracks, rivets, piles of
stones) and to the "photo booth" that turns that geometry into the colour, height and normal pictures of a tile. For each tool it says what it is,
what it did in this job, what changing its settings does, the traps found by testing, and how it compared with the flat "painter" route that all six
surface builds finally used. It ends with the honest verdict of every builder and short recipe cards.
The companion guides are "06 Guide - pattern makers.md" and "06 Guide - shapers.md" (shader nodes) and "06 Guide - the painted look.md".

## How to read this guide

Words used (one word for each thing, always):
* **tile** = the square picture we make; **dot** = one pixel of it. The references are 1254 x 1254 dots.
* **tile units** = distances measured in tiles: the whole tile is 1 x 1, so 0.01 is one hundredth of the tile (12.5 dots on a 1254 tile).
* **geometry** = a real 3D surface made of points, edges and faces. **Geometry Nodes** = Blender's node editor that makes and changes geometry.
  A **node group** is a saved bundle of nodes.
* **point** = a position with no size. **piece** = one brick, slate, plank, stone, bar or rivet built as geometry.
* **copy** = a wrap copy: the same piece again, shifted by one whole tile left, right, up or down.
* **curve** = a line through points that Blender can resample, bend and sweep a shape along.
* **photo booth** = the overhead camera that photographs geometry straight down, one picture per channel (section 2).
* **height picture**, **colour picture**, **normal picture** = the three pictures of a tile (white = high in a height picture).
* **seam** = a visible jump where the right edge of a tile meets the left edge of the next one.
* **painter route** = the main route of all six surface builds: thousands of FLAT coloured shapes stacked back to front and photographed from
  above, with the height made from the brightness of the finished colour. **geometry route** = real raised geometry photographed for its true height.
  (The painter route is geometry too, flat pieces; this guide is about the tools that make real relief.)
* **same-kind score** = `lib/texture_compare.py` overall (1 = the same kind of surface; a re-shuffled copy of a reference scores about 0.99, other real
  reference surfaces 0.16 to 0.50, not "about 0.1": baking and checking guide, section 7.4). **dot-for-dot tool** = `lib/pixel_compare.py` (colour SSIM, colour difference, edge skill, height error, normal error).

Labels: **TESTED** = run in Blender 5.2.2 on this machine, with the file that shows it; **NOT TESTED** = only read or reasoned; **NEW** = run for this
guide. Every number is copied from the file named next to it.

Where the facts come from: `research/02 Research - geometry nodes, curves, modifiers and physics for surface detail.md` (scripts and pictures in
`research/experiments_geometry_nodes_curves_modifiers_physics/`, called "the geometry research" below); the six builds in `recipes/<surface>/`
(`04 Recipe - <surface> - how it is made.md`, `builder_answer.json` = the builder's report, `verifier_answer.json` = an independent checker's findings);
`research/03 Research - Material Maker.md` and `research/03 Research - Ucupaint.md` for borrowed ideas; and NEW tests made for this guide:
`cookbook/checks/geometry_and_painted_strips/make_geometry_strips.py` (numbers in `numbers_geometry.json` in the same folder; joined and shrunk by
`finish_strips.py`; pictures `cookbook/pictures/geometry-*.jpg`).

---

## 1. The short version

Example first. The geometry research built a brick wall tile like this: a row-layout node group places 48 bricks (12 rows of 4), each brick is a box
with a random length, a mortar sheet goes underneath, noise roughens both, and one overhead camera takes the height, colour and normal pictures.
It took 110.5 seconds at 1254 x 1254 dots and nothing in it is a picture (geometry research, section 9 table). Its same-kind score against the brick
reference was 0.171. The brick builder later reached 0.407 with flat painted shapes and a height made from the colour (brick recipe guide, section 7).
That gap is the main lesson of this guide: **real geometry gives true relief, but the six reference height maps are not true relief; they are the
brightness of the colour picture.** So geometry lost every comparison against these references, and it remains the right tool when a surface must
really stick out in 3D.

The rules that would have saved the most time:
1. **End every Geometry Nodes group with a Set Material node.** A material put on the object does not reach geometry the group built: the picture
   came out black (NEW: mean brightness 0.0003 against 0.3253, section 8).
2. **Photograph with an orthographic camera and save the height as 16-bit.** Error 0.0000076 of the height range in 16-bit, one step in 255 in 8-bit
   (section 2).
3. **Geometry does not wrap by itself.** Make 9 copies of every piece (shifted by -1, 0, +1 tile in x and y) and use noise that repeats. Seam measure
   without and with copies: brick 10.37 -> 0.62, slate 40.19 -> 0.27 (section 3).
4. **Distribute Points with Poisson Disk keeps points apart inside the tile only.** Across the tile edge two points sat 0.0048 apart where 0.064 was
   asked. Relaxing the points 40 times in a Repeat zone fixed it: no point too close (NEW strip, section 5).
5. **Store per-piece numbers BEFORE Realize Instances.** After realizing, the plain Index is the vertex number, not the piece number (section 4).
6. **A curve swept with no profile is only edges.** Edges are perfect for measuring "distance to the curve" (grooves, ruts, cracks) and invisible to the
   camera (NEW strip, section 6).
7. **Mesh Bevel on edges needs its four offsets set**; each defaults to 0.1 tile units and a first try exploded the height range (section 9).
8. **Cut holes with ONE cutter and the Manifold or Float solver.** 144 holes: 12.7 s with 144 Boolean modifiers, 0.19 s with one cutter and Manifold
   (section 9).
9. **Rigid Body piles do not wrap.** 69 stone pairs pushed into each other across the tile edge; moving the pile half a tile and settling again twice
   brought it to 14 (section 10).
10. **Ambient occlusion gives free dark crevices but makes the colour picture about 13 times slower** (brick: 6.8 s without, 87 s with, section 2).

---

## 2. The photo booth: photographing geometry from above

**What it is:** a camera that looks straight down at the 1 x 1 tile with no perspective, plus a material that makes the surface glow with exactly one
number (its height, its colour, or its slope), so every dot of the picture is that number.

**Example first** (TESTED, geometry research section 2.2, `t01_zdepth_routes.py`): a staircase of four flat steps at heights 0, 0.02, 0.05 and 0.10
was drawn six ways and compared with the truth:

| Route | How | Biggest error (0..1 scale) |
|---|---|---|
| Emission of Geometry > Position > Z, 8-bit PNG | the classic forum answer | 0.0039 (one step of 255) |
| the same, **16-bit PNG** | `color_depth = '16'` | 0.0000076 |
| Camera Data > View Z Depth into the Emission, 16-bit | height = 5 - depth | 0.0000076 |
| Cycles Depth pass, 32-bit EXR | height = 5 - Depth.Z | 0.0000019 |
| Cycles Position pass, 32-bit EXR | read Position.Z | 0.000000015 |
| Emission of Position Z saved as a 32-bit EXR | the "Combined" pass | 0.000000015 |

So a 16-bit PNG is as exact as you will need, and 8-bit shows steps on smooth slopes.

**The setup** (TESTED; `lib/bake_harness.py new_bake_scene` and `lib/contrib/gn_tools.py photograph_geometry`): orthographic camera
(`ortho_scale = 1.0`) at (0.5, 0.5, 5) looking down; Cycles with 4 samples, pixel filter Box width 1, no bounces, black world; view transform
Standard for colour and Raw for data. Cycles is used because this machine has no graphics card, so EEVEE cannot run (NOT TESTED).
* **Height:** Emission of Position Z through a Map Range from the lowest to the highest Z (clamped). `gn_tools.z_range()` reads them from the
  evaluated mesh; `z_percentiles=(0.0, 99.99)` ignores a stray point (a stone still in the air).
* **Colour:** store the colour on the geometry (Store Named Attribute, type Color, name `piece_colour`) and show it with an Attribute node into the
  Emission: flat colour with no lighting.
* **Normal:** either the slope of the 16-bit height (a Sobel filter, `lib/bake_harness.sobel_normal`) or the TRUE surface normal (Emission of
  Geometry > Normal x 0.5 + 0.5; set the mesh Shade Smooth first or every facet is flat). Which wins depends on the surface: the true normal scored
  0.49 against 0.29 for slate and 0.00 against 0.27 for brick on the normal part of the same-kind score (geometry research, section 9). Try both.
* **Extras only real geometry can give:** an Ambient Occlusion node multiplied into the colour darkens crevices (Distance 0.02-0.03, 16 samples);
  Geometry > Pointiness through Map Range 0.5..0.62 lightens sharp edges ("worn paint"). Ambient occlusion made the brick colour picture 13 times
  slower: 6.8 s without, 87 s with, at 1254 dots (geometry research, sections 2.4 and 11). The strips show both:

![ambient occlusion strength](../research/experiments_geometry_nodes_curves_modifiers_physics/out/strips/ambient_occlusion_colour.png)

(Ambient occlusion strength 0 / 0.5 / 1.0, distance 0.03: the mortar and the foot of every brick get darker; at 1.0 the mortar is nearly black.)

![edge wear](../research/experiments_geometry_nodes_curves_modifiers_physics/out/strips/edge_wear_colour.png)

(Edge wear from Pointiness 0 / 0.5 / 1.0: faint on bricks because their bevels are small; it shows clearly on rivet edges, geometry research section 10.)

**All seven research geometry recipes, photographed** (reference colour | geometry colour | reference height | geometry height | reference normal |
geometry normal; one row per recipe; small copy of `research/.../out/overview_all_recipes.png`):

![all geometry recipes next to the references](pictures/geometry-overview-all-recipes.jpg)

Look at the height columns: the reference heights are speckled grey copies of the colour picture; the geometry heights are clean blocks. That is the
whole story of section 11 in one picture.

**What the photo booth cannot do:** anything under an overhang is invisible (correct for a height picture); roughness and metallic must be stored as
numbers and shown the same way (NOT TESTED in the research beyond colour; the builds did it on flat pieces).

---

## 3. Making geometry wrap, and row layouts

**What wrap copies are:** every piece is made 9 times, shifted by -1, 0 and +1 tile in x and in y; copies that cannot touch the tile are deleted; the
camera crops to the tile. A brick that leaves the right edge at x = 1.02 then also appears at x = 0.02.

**Measured** (TESTED, geometry research section 3.1, `t07_wrap_tests.py`; seam ratio about 1.0 or less = seamless):

| What | without the rule | with the rule |
|---|---|---|
| brick wall, wrap copies | 10.37 | 0.62 |
| slate roof, wrap copies | 40.19 | 0.27 |
| mud ruts: curves closed on the tile + copies | 6.08 | 0.67 |
| a plane bumped by noise: plain Noise vs repeating "donut" noise | 18.41 | 0.87 |

![wrap test, every picture slid by half a tile](pictures/geometry-wrap-test-sheet.jpg)

(Each picture slid by half a tile, so a seam would show as a cross in the middle. The "nowrap" pictures have cut-off bricks and slates and a broken
rut; the wrapped ones do not. Small copy of `research/.../out/t07_wrap_sheet.png`.)

The other wrap rules (followed in every geometry recipe; not separately A/B tested): give every piece a number that its copies share (`piece_id`)
and seed every random value with it, or a copy looks different from its original; look up the ground height at the WRAPPED position for anything
dropped onto it; close every curve on the tile (section 6).
The painter builds used the same idea on flat shapes, with one more step: **fold each shape's middle into the tile before copying it** (layouts run past
the edge). The slate builder forgot this once and the half-tile test showed 18 % of dots different (slate `builder_answer.json`, dead ends).

**The row layout** (TESTED, geometry research section 4, `lib/contrib/layout_tools.py row_layout_group`): one node group that gives one point per brick,
slate or plank, with its width, height, row and a shared `piece_id`. Example: Rows 12, Per row 4, Width jitter 0.2, Gap 0.022 makes 12 rows of 4 bricks,
and every row adds up to exactly 1.0 wide, so every row repeats. The chain: Mesh Line -> Mesh to Points (one point per piece) -> row = Floor(index / per
row) -> Random Value weight per piece -> **Accumulate Field** (Group ID = row) -> start = Trailing / Total, width = weight / Total -> row shift -> Wrap
-> Set Position -> Store Named Attribute -> Duplicate Elements (Amount 9) for the copies -> delete copies outside the tile.

![width jitter](../research/experiments_geometry_nodes_curves_modifiers_physics/out/strips/width_jitter_colour.png)

(Width jitter 0 / 0.2 / 0.5: equal bricks; mixed; lengths from half to one and a half of the average.)

![row shift](../research/experiments_geometry_nodes_curves_modifiers_physics/out/strips/row_shift_colour.png)

(Row shift randomness 0 / 0.8 / 1.0: tidy half-brick bond; every row starts somewhere else, like the reference.)

Traps (TESTED):
* **Accumulate Field: "Leading" INCLUDES the current piece; "Trailing" is the total before it.** Weights 1, 2, 3, 4, 5 gave Leading 1, 3, 6, 10, 15
  and Trailing 0, 1, 3, 6, 10. Using Leading for the start made bricks overlap or leave gaps (geometry research, section 15, row 4).
* **Duplicate Elements Amount 9 gives 9 in total** (the original is not extra), and it keeps the point's attributes, which is what lets copies share
  `piece_id`. An attribute stored AFTER the copies gives every copy its own number.
* The slate build's geometry test reused this idea on the builder's own fitted layout: 63 points (48 slates plus their copies), each with width,
  height and tone (slate recipe guide, section 7).

---

## 4. Instance on Points and Realize Instances

**What they are:** Instance on Points puts a cheap copy of one shape on every point (an "instance"); Realize Instances turns those cheap copies into
real geometry that later nodes can bend and colour.

**Example first** (TESTED, brick build `generator/gn_blobs_route.py`, brick recipe guide sections 4 and 7): the 1,818 paint blobs of the brick's
class M description became one point each (centre, two radii, turn, colour, seed stored on the point) -> **Mesh Circle** (28 corners, filled) ->
**Instance on Points** (Scale = the two radii, Rotation = the turn, read with Named Attribute nodes) -> **Realize Instances** -> Set Position (corners
pushed by a 4D noise for a ragged edge) -> Store Named Attribute (colour) -> Set Material. The nodes took 0.11 s; the picture scored the same as the
numpy painter (colour SSIM 0.554 against 0.552, edge skill 0.434 against 0.421).

What each build placed with it (all TESTED; times from the files named):

| Build | Shape instanced | Points | Time | File |
|---|---|---|---|---|
| brick | filled Mesh Circle (28 corners), one per blob | 1,818 | 0.11 s for the nodes | brick recipe guide, section 7 |
| wood | 12-sided circle, one per splatter blob | 458 | 11.6 s whole route, against 15.3 s for polygons | `recipes/wood/outputs/geometry_route/geometry_route_report.json` |
| metal | 8-sided Mesh Cone, one per rivet | 50 (with copies) | 1.28 s whole scene | `recipes/metal/outputs/geometry_route/geometry_route.json` |
| gravel | a 4-, 5- or 6-sided Mesh Cylinder with a shrunk top (Pick Instance) | 2,921 (2,832 stones + copies) | 0.66 s to build | gravel recipe guide, section 7 |
| mud | a low-poly ball bent by noise, one per stone | 590 stones | 8.4 s, against 3.4 s for polygons | `recipes/mud/outputs/geometry_route/report.json` |
| research gravel | Pick Instance among 8 convex-hull shapes | 2,150 stones | 1-3 s of geometry (3.33 s in the timing table) | geometry research, sections 5.7 and 9 |

Settings that matter:
* **Pick Instance** on + **Instance Index** = a random whole number chooses among several shapes joined with Geometry to Instance.
* **Scale** multiplies the shape. A thin plate scaled unevenly and then bevelled gets bevels of unequal width, so **bevel AFTER Realize**.
* **Realize Instances** is where memory and time go. Thousands of instances of a 40-face shape were fine; thousands of finely subdivided shapes were not.

Traps (TESTED):
* **Store per-piece numbers BEFORE Realize Instances.** In `t09_capture_attribute.py` 5 cubes were instanced; the instance number was stored
  (Store Named Attribute, domain Instance) and captured (Capture Attribute) before realizing, and after realizing every vertex of cube k held k. A plain
  Index read AFTER realizing gave the vertex number (0-7 for cube 0, 8-15 for cube 1), useless for per-piece colours.
* **An attribute called `radius` is overwritten by Mesh to Points**, which has its own Radius input (mud recipe guide, section 8).
* Vector Math "Scale" takes its number on the fourth socket (mud recipe guide, section 8).
* A point cloud cannot be read as a mesh: add Points to Vertices when you want to look at the points from Python (geometry research, section 8.1).

**A cousin worth knowing (NOT TESTED):** Material Maker's "Tiler" and "Splatter" boxes do the same job inside a shader, with no geometry: the tile is
cut into cells, each cell gets a random offset, turn, size and brightness, and every dot checks the neighbouring cells to see if it falls inside one of
the copies (`research/03 Research - Material Maker.md`, "How its key nodes are built"). It was read, not run; section 5 of "06 Guide - the painted
look.md" says what our builds did instead.

---

## 5. Distribute Points, and relaxing points in a Repeat zone

**What they are:** Distribute Points on Faces scatters points over a surface (Random, or Poisson Disk = never closer than Distance Min). A **Repeat
zone** runs the nodes inside it again and again; used here to push points that are too close apart, a little each time ("relaxing").

**Example first (NEW strip, `make_geometry_strips.py`, numbers in `numbers_geometry.json`).** 220 points, each needing room of radius 0.032 (so two
points should be at least 0.064 apart). A disc is drawn round every point; a **red** disc has a neighbour closer than 0.9 x 0.064, measured the
wrap-around way. Every picture is slid by half a tile, so the tile's own edge is the thin blue cross in the middle.

![spacing points: Poisson Disk, then relaxing](pictures/geometry-strip-relax-steps.jpg)

| Method (seed 3) | Points | Smallest distance (wrap-around) | Share of points too close | Time to evaluate |
|---|---|---|---|---|
| Poisson Disk, Distance Min 0.064 | 161 (220 asked) | 0.0048 | 0.174 | 0.003 s |
| random, not relaxed | 220 | 0.0067 | 0.923 | 0.002 s |
| random, relaxed 5 times | 220 | 0.0315 | 0.736 | 0.036 s |
| random, relaxed 15 times | 220 | 0.0482 | 0.35 | 0.075 s |
| random, relaxed 40 times | 220 | 0.0604 | 0.0 | 0.149 s |

What the strip shows: **Poisson Disk is perfect inside the tile, and every red disc it has sits on the blue cross**: it knows nothing about the other
side of the tile edge. It also gave only 161 of the 220 points asked for (the room needed caps the number). Relaxing fixes both problems; 40 steps left
no point too close. These are the same numbers the geometry research measured (its `out/t06_relax/results.json`: 0.0048, 0.0315, 0.0482, 0.0604),
so the test repeats exactly.

**One relaxing step, in node order** (TESTED, `lib/contrib/relax_tools.py`; geometry research section 6.2):
1. Store Named Attribute `central = True` on the points.
2. Nine Transform Geometry copies (shifted -1, 0, +1 in x and y); the eight shifted copies get `central = False`.
3. **Index of Nearest** (Position) = the nearest OTHER point, which may be a copy on the other side of the tile edge.
4. **Sample Index** reads that neighbour's position and its `radius`.
5. away = position - neighbour; overlap = (own radius + neighbour radius) x Tightness - distance; push = 0.45 x overlap (never negative); Set Position
   moves the point by push along away.
6. Delete the copies; **Wrap** x and y back into 0..1, so a point pushed over the edge comes back on the other side.

Settings: **Iterations** (40 to 60 was plenty for 220 to 1,100 points); **Tightness** (1.0 = circles may just touch; the research gravel used 0.95
because angular stones fill their circle poorly). Python: pair the Repeat Input and Output nodes first (`repeat_in.pair_with_output(repeat_out)`),
then link into them.
* A **Simulation zone** built the same way and stepped one frame at a time gave the same result to within 0.0016 (geometry research section 6.2).
* The **Bake node** freezes a slow stage: after baking, changing Iterations 40 -> 2 moved the points by 0.0 (before baking: up to 0.0316). It needs a
  saved .blend file and an active object (geometry research section 6.3). Not needed by any build.
* Known weakness: only the single nearest neighbour is pushed per step, so crowded points need more steps.
* Where it was used: the research gravel "nodes only" recipe (2,150 stones, 60 iterations, Tightness 0.95). The gravel BUILD placed its stones in plain
  Python instead, refusing a stone closer than "spacing" x the two radii, measured across the tile edge too (gravel recipe guide, section 4, step 13).

---

## 6. Curves: ruts, cracks, grain, bars and rivets

**What a curve is here:** a line through points that Geometry Nodes can resample (put evenly spaced points on it), bend (Set Position), and sweep a
cross-section along (**Curve to Mesh**). Two ways to use one for a surface: (a) measure every ground point's **distance to the curve** (Geometry
Proximity) and dig or raise the ground by that distance = a groove, rut or crack; (b) **sweep** a shape along it = a raised ridge, bar or rope.

**Example first (NEW strips, `make_geometry_strips.py`).** Three wavy curves, each made by Curve Line (from x = 0 to x = 1) -> **Resample Curve**
(Mode "Count", 240 points) -> **Set Position** (y moved by a whole-number slope of 0, +1 or -1 times x, plus a sine wave with a whole number of waves,
so each curve ends where it started on the tile) -> **Curve to Mesh** with no profile (= plain edges) -> 9 copies -> **Geometry Proximity** (target:
Edges) measured from every vertex of a 257 x 257 Grid -> **Map Range** from distance 0..half-width to height -0.01..0 = a V-shaped groove.

![groove width from curves](pictures/geometry-strip-groove-width.jpg)

The setting is the groove's half-width in tile units: 0.005, 0.01, 0.02, 0.04 (on a 1254 tile 6.3, 12.5, 25.1 and 50.2 dots, `numbers_geometry.json`).
A narrow half-width draws a crack; a wide one a soft wheel rut. Every groove crosses the tile edge and comes back on the other side. Each square took
about 1 s to build and photograph at 256 dots.

![Curve to Mesh profile radius](pictures/geometry-strip-curve-ridge-radius.jpg)

The same curves swept with a **Curve Circle** profile (8 sides) of radius 0, 0.003, 0.006, 0.012 and 0.024 tile units, height picture from 0 to 0.024.
**The first square is black: with no profile, Curve to Mesh makes only edges, and edges have no surface for the camera to see.** With a profile the
ridge stands as high as the circle's radius (highest point 0.003, 0.006, 0.012, 0.024, `numbers_geometry.json`).

**What curves did in this job:**

| Surface | Curve use | Settings | Status, file |
|---|---|---|---|
| mud ruts | 3 tracks, each a PAIR of curves 0.075 apart (wheel gauge); Proximity -> **Float Curve** rut profile with points (0, 0.02), (0.18, 0.05), (0.40, 0.30), (0.52, 0.52), (0.68, 0.92), (0.85, 0.62), (1.0, 0.5) -> Map Range to -0.014..+0.007 (a groove 0.014 tile units deep with a bank 0.007 high) | slope -1 / -1 / +1, whole waves, wobble by repeating noise of x | TESTED, geometry research 5.4, `recipe_curve_ruts.py`, 132 s at 1254 |
| wood cracks | 14 random curves -> Proximity (Edges) -> Map Range 0..0.0045 to -0.014..0 = a V groove; the same distance makes the colour dark | | TESTED, geometry research 5.6 |
| wood grain ridges | bundles of 9 wiggly curves on every plank -> Curve to Mesh with a Curve Circle of Resolution 3 (a triangle), radius 0.0016 | **sweep AFTER scaling to the plank**, or the profile is stretched | TESTED, geometry research 5.6 |
| wood knots | 3 points -> Proximity (Points) -> rings fading outward | | TESTED, geometry research 5.6 |
| metal straps and braces | Curve Line along each bar -> **Quadrilateral** profile -> Curve to Mesh = a real bar; one group used 21 times | | TESTED, metal recipe guide 5.5, whole scene 1.28 s |
| metal rivets | Curve Line along a strap -> Resample Curve (Count 9 on a full strap, 4 on a brace) -> Curve to Points -> Instance on Points (Mesh Cone) | a 9-point resample puts a rivet at each end, so two halves meet across the tile edge | TESTED, geometry research 5.5 |
| wood build cracks | Blender **curve OBJECTS** (not nodes): poly curve, bevel on, every point's radius = half the crack width, so the crack tapers by itself | 200 cracks | TESTED, `recipes/wood/outputs/geometry_route/geometry_route_report.json`: same picture as polygons (mean difference 0.134 brightness steps, 0.1 % of dots over 40), 11.6 s against 15.3 s |
| mud build ruts | curve objects with a bevel depth (seen from above, a ribbon twice the bevel depth wide) | | TESTED, mud recipe guide section 8: 3.2 s against 4.6 s for polygon ribbons, equal picture, but one width and one colour per curve |

![wood: polygon painter and geometry route](../recipes/wood/outputs/geometry_route/compare_crop.png)

(Wood build, the same description drawn twice: left the numpy polygons, right curve objects for the cracks and Geometry Nodes circles for the blobs.
The only visible difference is that the node blobs are perfect circles.)

Traps (TESTED):
* **Closed curves only:** a slope that is not a whole number, or a part-wave, leaves the right edge at one height and enters the left edge at another
  (the rut seam test, section 3).
* **Resample Curve's Mode is an input socket in 5.x** (`inputs['Mode'] = 'Count'`); `mode='COUNT'` as a Python setting fails. The same is true of
  Transform Geometry's Mode and Mesh Bevel's Affect (geometry research, section 11, item 5).
* **Geometry Proximity distance is 3D:** feed a flat sample position (z = 0) when the target is flat, or the depth you dig changes the distance.
* **Float Curve extrapolates outside 0..1** unless `mapping.extend = 'HORIZONTAL'` (geometry research section 8.1; another helper measured -2.99).
* **Curve objects do not scale to thousands:** one Blender object per crack (200 in the wood test) would not work for 3,000 traced patches, and a curve
  has one width and one colour (wood and mud recipe guides).

---

## 7. Set Position

**What it is:** a node that moves points: to a new place (Position) or by an amount (Offset), only where its Selection is true.

**Example first** (TESTED, geometry research recipe 1, `recipe_brick_layout.py`): every brick vertex above the brick base moves sideways by up to 0.0026
tile units, driven by a repeating noise whose Seed is 7.3 x the brick's `piece_id` (so a copy across the tile edge moves the same way) = a ragged brick
outline. A second Set Position lifts faces that point up by fine noise (0.002) plus a hard-edged "patch" noise (0.004; Map Range 0.40..0.60 makes
painted-looking blobs).

Other uses that were run:
* slate lower edges: vertices below -0.30 in slate-local height pushed up the slate by chip noise x 0.012 = a ragged chipped edge (geometry research 5.2);
* stones resting on bumpy ground: **Raycast** straight down from z = 1 at the WRAPPED x and y, then Set Position z = hit height (geometry research 5.4;
  no hit gives position (0, 0, 0), so look up at the wrapped place or delete the miss);
* the brick blobs of section 4: every corner pushed in or out by a 4D noise, the blob's seed as the 4th number, a lump about every 6 dots;
* the mud build's stones: every corner of a low-poly ball pushed by noise so each ball becomes a lump (mud recipe guide section 8).

Traps (TESTED):
* **Blender's Noise does not repeat across the tile edge.** Use `gn_tools.tileable_noise_geo_group()` (the 4D "donut" trick): seam 18.41 with plain
  Noise, 0.87 with the repeating one (section 3).
* **Set Position can only move points that exist.** On a coarse mesh the noise moves only a few corners:

![Subdivide level](../research/experiments_geometry_nodes_curves_modifiers_physics/out/strips/subdivide_level_normals.png)

(Subdivide Mesh level 0 / 2 / 4 before the noise, normal picture: smooth and slightly wavy; gentle roughness; fine grain on every face, with 16 times
the vertices of level 2.)

---

## 8. Set Material, and the black picture

**What it is:** a node that gives the geometry passing through it a material.

**Example first (NEW, `make_geometry_strips.py`, `numbers_geometry.json`, "set_material").** The same coloured ridges, built by a Geometry Nodes group,
photographed twice with the same colour material:

![the black-picture trap](pictures/geometry-trap-set-material.jpg)

| How the material was given | Mean brightness of the picture (0..1) | Materials on the evaluated geometry |
|---|---|---|
| put on the object's own material slot, no Set Material node | 0.0003 (black) | one empty slot |
| Set Material as the last node of the group | 0.3253 | the colour material |

**The rule:** a material on the object does not reach geometry that a Geometry Nodes group built from nothing. End every group with Set Material.
The photo booth (`gn_tools.finish_with_material_slot` and `render_with`) names that node `show material` and swaps its material for each picture
(height, colour, normal). The geometry research met it first (its first brick picture was pure black); the brick builder (`builder_answer.json`) and
the metal recipe guide (section 5.5) wrote it down; all six builds' Geometry Nodes trees end with Set Material (`builder_answer.json`
"blender_tools_used" of each).

---

## 9. Modifiers: Displace, Bevel, Boolean, Subdivision and others

**What a modifier is:** a ready-made step stacked on an object (in the Modifiers panel) that changes its geometry without changing the original.
Geometry Nodes has a node for most of them; the recipes used the nodes.

**Example first** (TESTED, geometry research section 8.2, `t05_modifier_gallery.py`): twelve modifiers, each photographed from above as a height
picture (white = high). Small copy of `out/t05_modifiers_sheet.png`:

![modifiers seen from above](pictures/geometry-modifiers-from-above.jpg)

| Modifier | Settings used | What it does to a height picture |
|---|---|---|
| **Displace** (Clouds texture) | noise scale 0.22, depth 3, Strength 0.10, Mid Level 0.5 | cloudy relief; mid-grey = unchanged. Needs a dense grid (0.017 s for 16,641 vertices) |
| **Subdivision Surface** | levels 0 / 2 / 3 | a box becomes a rounded pebble; 2 and 3 look alike here |
| **Bevel** | width 0 / 0.02 (1 segment) / 0.04 (4 segments) | chamfers, then round shoulders; shows more in the normal picture than in the height |
| **Boolean** Difference / Union | 4 cylinders / 4 spheres | clean round holes / domed bolts |
| **Remesh** | Voxel 0.02 / Blocks | even and smooth / stepped, block-like |
| **Array + Weld** | count 5; Weld 0.001 | same picture; Weld merged shared vertices 40 -> 24 |
| **Wave** | height 0.12 at frame 8 | ripples; with width 0.12 and narrowness 1.5 only 0.002 high (almost invisible) |
| **Solidify** | thickness 0.04 | a sheet gets a thickness; from above only the edges change |
| **Array** with a z offset | count 4, z 0.015 | a row of bricks; a staircase |
| **Cast** | Sphere 0 / 0.5 / 1 | a block turns into a pebble |
| **Simple Deform** | Bend 70, Twist 80, Taper 0.8 | arched, twisted, tapered planks |

**Bevel, in Geometry Nodes (Mesh Bevel).** Example: the research brick wall used offsets of 0.0035 with 2 segments on the sharp edges only (Edge Angle
above 0.6, so the grid edges inside a face are not bevelled).

![bevel offset](../research/experiments_geometry_nodes_curves_modifiers_physics/out/strips/bevel_offset_normals.png)

(Mesh Bevel offset 0.0003 / 0.0035 / 0.008, normal picture: a hairline; a clear thin highlight round every brick; a wide soft band, pillowy bricks.)
**Trap (TESTED):** for edges, set the four inputs Start Left, Start Right, End Left and End Right Offset. Each defaults to 0.1 tile units; the single
"Offset" input is for vertex bevels only. A first try with the defaults blew the height range out to -0.09..0.09 (geometry research section 15, row 4).

**Subdivision.** Subdivide Mesh (no smoothing) multiplies the faces by 4 per level. Level 5 on bevelled bricks gave 3.5 million vertices and a 98 s run at
only 512 dots; level 3 gave 270,000 (geometry research section 11). Use the lowest level that lets Set Position draw the detail you need (strip in section 7).

**Boolean, and the speed of its solvers** (TESTED twice, geometry research section 8.3, `t08_boolean_speed.py`, 1 thread; the two runs agreed within
25 %; raw numbers in `out/t08_boolean_speed.json`). Cutting N round holes in a plate:

| Holes | N Boolean modifiers (Exact) | one cutter holding all N (Exact) | one cutter, Float solver | one cutter, Manifold solver | Geometry Nodes Mesh Boolean (Float) |
|---|---|---|---|---|---|
| 4 | 0.09 s | 0.05 s | 0.003 s | 0.26 s (first call) | 0.003 s |
| 16 | 0.38 s | 0.23 s | 0.012 s | 0.013 s | 0.012 s |
| 64 | 3.1 s | 0.97 s | 0.09 s | 0.05 s | 0.09 s |
| 144 | **12.7 s** | 2.5 s | 0.47 s | **0.19 s** | 0.44 s |

All give the same vertex count. Rule: one cutter, and Manifold (needs closed, well-formed meshes) or Float (when the cutters do not overlap each other);
Exact only when you need it. The 0.26 s first Manifold call looks like a set-up cost. (The research file also still holds the first run's table below
this one: 15.0 s for 144 modifiers; same conclusion.) No build used Boolean (a search of the six `generator/` folders finds no Boolean).

**Solidify and Bevel on real brick slabs** (TESTED, brick recipe guide section 4, tool 12): every brick face of the class M description became a slab
0.02 thick with its top edges rounded by 4 dots (3 segments). **Trap:** the faces pointed DOWN (the picture's y runs down, Blender's up), so the slabs
grew downwards and the height picture came out black; thickness +0.02 with offset -1 fixed it. The result is in section 11.

Not used in any texture recipe (gallery only, NOT TESTED further): Remesh, Weld, Wave, Cast, Simple Deform, Boolean.

---

## 10. Rigid Body settling, and why it does not wrap

**What it is:** Blender's physics drops real objects (here stones) onto a floor; they bounce, slide and come to rest leaning on each other.

**Example first** (TESTED, geometry research section 7, `recipe_gravel_rigidbody.py`): 834 stones (34 big, 140 medium, 360 small, 300 tiny) dropped
for 190 frames, then two more rounds of 90 frames; 19-21 s of physics per round; 262.5 s for the whole script at 1254 dots, of which about 60 s was
physics and about 85 s the colour picture with ambient occlusion. The pile is the "mine: gravel (rigid body)" row of the overview picture in section 2.
Same-kind score 0.145 (geometry research section 9).

The settings that mattered (all from the run):
1. **Scale the world 10 times up** (tile = 10 x 10 units, big stones 0.9-1.35). The 5.2 manual: "It is best to avoid small objects ... at least 20 cm in
   diameter." Running at 1 x scale was NOT TESTED.
2. Floor Passive, box shape, friction 1.0. Stones Active, **Convex Hull** shape, uniform scale only, Margin 0.002, friction 0.9, bounciness 0.05,
   mass = size cubed x 2.5, angular damping 0.4, **linear damping 0.7** (it caps the falling speed).
3. Rigid Body World: Solver Iterations 30, Substeps 10.
4. Step it from Python: `scene.frame_set(f)` frame by frame, then read `obj.matrix_world`. A falling cube reached z = 0.306 at frame 10 against the
   free-fall formula's 0.31, so stepping from Python is physically right.

**Why it does not wrap, and what was tried** (TESTED, geometry research section 7.2):

| Idea | Result |
|---|---|
| none (just photograph the middle tile) | **69 stone pairs** pushed into each other across the tile edge (45 deeply) |
| "ghost" copies: 8 moving copies of every stone that follow it each step | only 4 overlaps left, BUT stones squeezed between a ghost and the floor fell through it (5 ended below the floor), some rested 4-5.5 units up on ghosts, and physics took 79-85 s per round instead of 20 s. Not recommended. |
| **move the pile half a tile (wrapping round) and settle again**, twice | 69 -> 29 -> 14 overlapping pairs (deep ones 45 -> 15 -> 7), about 20 s per round. A 4th round was not tried. |

Why the third works: stones that overlapped across the old edge now sit in the middle, where physics pushes them apart for real.
Fragile things: fast or tiny stones and anything squeezed by a moving body tunnel through the floor; more substeps (30) and solver iterations (60)
did NOT help in the ghost version; a lower start height or linear damping 0.7 did.

**The node-only alternative** (TESTED, geometry research recipe 7, `recipe_gravel_scatter_gn.py`): relax 2,150 stone positions in a Repeat zone
(section 5) instead of dropping them: about 1 s of geometry instead of minutes, and it wraps; stones never lean on each other. Same-kind 0.184
against 0.145 for the dropped pile. **No surface build used physics** (gravel `builder_answer.json`: "Not used: ... rigid-body physics").
Particles, Cloth, Dynamic Paint, Fluids and the 5.2 hair and cloth physics: NOT TESTED.

---

## 11. The honest verdict: what every builder's geometry route gave

Every builder's report has a "geometry_route_verdict": all six tried real geometry and compared it with their painter route on the same
description. The numbers:

| Build | What was built as real geometry | Time, geometry against painter | Result against the painter route (same description) | Verdict, in the builder's words (shortened) |
|---|---|---|---|---|
| brick | (a) bricks as slabs (Solidify + Bevel), true height; (b) the 1,818 paint blobs by Geometry Nodes | (b) 0.11 s for the nodes | (a) height: correlation with the reference -0.15 (slab only) and 0.16 (half slab, half colour) against 0.69 for the colour-made height; same-kind 0.262 / 0.296 against 0.407. (b) same picture: SSIM 0.554 / 0.552 | slabs worse here because the reference height is brightness (mortar high); node blobs a valid alternative, not used (brick recipe guide section 7) |
| slate | the whole roof: Instance on Points of tilted thin boxes, Mesh Bevel, Subdivide, Set Position, ambient occlusion | 88 s against 28 s (colour with ambient occlusion alone 76 s) | colour SSIM 0.679 against 0.711 (layout only); same-kind 0.32-0.37 against 0.71 with painted stamps; height error 33.8 (true), 34.9 (half and half) | true overlap, shadow and tilt for free; colour is soft blobs; use it on a real 3D roof (slate recipe guide section 7) |
| wood | cracks as curve objects (tapering by point radius), blobs by Geometry Nodes | 11.6 s against 15.3 s | the same picture: mean difference 0.134 steps, 0.1 % of dots over 40 | taper is one setting and scatter is one node tree, but one object per crack does not scale; real relief not tested (wood recipe guide section 10) |
| metal | 21 bars (Curve Line + Quadrilateral + Curve to Mesh) and 50 rivet cones, true height and normal | 1.28 s against 14-45 s | height correlation 0.07 with the reference; with the class L colour: height error before the best fit 32.4 (geometry) against 17.1 (made from colour); mixing in 20 / 40 / 60 % geometry: 18.3 / 20.8 / 24.2 (after the best fit, as the relief guide quotes them: 32.39 against 16.62; 16.69 / 16.87 / 17.46; `metal/final_report.json`, height_routes_L) | derive the maps from the colour to match this reference; geometry when real raised parts are wanted (metal recipe guide section 8) |
| mud | stones by Geometry Nodes (bent balls, sun-lit facets); ruts as curve objects | stones 8.4 s against 3.4 s; ruts 3.2 s against 4.6 s | stones: low-poly rocks without the painted stones' strong light and dark faces and dark rim; ruts: equal picture. Height from geometry not tried | good for a stone scatter that should look 3D; flat polygons better for a painted look (mud recipe guide section 8) |
| gravel | 2,832 stones as short columns with shrunk tops (Instance on Points, Pick Instance) | about 9 s against 65-100 s | same-kind 0.173 (geometry alone), 0.203 (painter colour + geometry height), 0.257 (50/50 height) against 0.362 (painter) | lowers the score for a colour-made reference; keep it for a gravel floor that must stick out in 3D (gravel recipe guide section 7) |

![slate: reference, painter, real geometry](../recipes/slate/guide_pictures/geometry_vs_painter.png)

(Slate. Left: reference colour and height. Middle: painter route. Right: real geometry. The real slates overlap, tilt and cast soft shadows, and their
height is a smooth ramp; the reference height follows the paint.)

![gravel: painter route and real geometry](../recipes/gravel/guide_pictures/geometry_route_compare.png)

(Gravel. Top: painter colour, geometry block colour, geometry true height, 50/50 height. Bottom: the painter's normal, the normal from the true height,
the half-and-half normal.)

![mud stones: reference, flat polygons, Geometry Nodes rocks](../recipes/mud/outputs/geometry_route/stones_crop_ref_polygons_geometry.png)

(Mud stones. Left: reference; middle: flat polygons; right: Geometry Nodes rocks lit by a sun lamp.)

**What it adds up to:**
1. **The geometry research's hint "50/50 hybrid heights help brick, slate and gravel" did NOT hold in the builds.** It was measured on the research's
   own geometry tiles; on the builders' descriptions the half-and-half height was worse or no better for brick (0.296 against 0.407), slate
   (height error 34.9 against 33.8) and gravel (0.257 against 0.362), and slightly worse for metal (height error 18.3 at 20 % against 17.1).
2. **The reason is a fact about the upload, not a weakness of geometry:** each reference height map is the brightness of its colour picture
   (correlation 0.968 to 0.993, painted-look research section 2.6). On the brick, mortar is BRIGHT and therefore HIGH; a real wall is the other way round.
3. **Geometry is fast to build.** Metal 1.28 s, gravel about 9 s, the brick blobs 0.11 s, against tens of seconds for the painter. The slow part is
   ambient occlusion in the colour picture, not the geometry.
4. **Use real geometry for:** a texture that will displace a real 3D surface, real overlap and shadow (a 3D roof), true normals of rivet domes,
   placing thousands of things with one node tree (Instance on Points), and layouts. **Use the painter route for:** copying a painted reference.
5. A real-geometry SHAPE with the painted COLOUR on top was suggested by the slate builder and never built (slate recipe guide section 7). NOT TESTED.

---

## 12. Traps (all met by testing)

1. Black picture: no Set Material at the end of the group (section 8; NEW numbers 0.0003 against 0.3253).
2. Mesh Bevel's four edge offsets default to 0.1 (section 9).
3. Accumulate Field: Leading includes the current piece, Trailing does not (section 3).
4. A Geometry Nodes modifier's inputs are set as `modifier.properties.inputs.Socket_1.value = 5` followed by `object.update_tag()`; the old
   `modifier["Socket_1"] = 5` fails, and without `update_tag()` headless Blender showed the old result (geometry research section 1, item 8).
5. Several nodes take menu INPUT sockets now: Resample Curve Mode, Transform Geometry Mode, Mesh Bevel Affect, Merge by Distance Mode (section 6).
6. A Repeat or Simulation zone must be paired before you link into it (section 5).
7. Per-piece values must be stored before Realize Instances (section 4).
8. Plain Noise and Voronoi do not repeat across the tile edge; use the donut groups (section 3).
9. Poisson Disk ignores the other side of the tile edge and caps the count (section 5; NEW strip).
10. Curve to Mesh with no profile is invisible to the camera (section 6; NEW strip).
11. Float Curve extrapolates unless `extend = 'HORIZONTAL'` (section 6).
12. Solidify grows along the face normal: faces that point down make slabs that grow down (section 9).
13. Python handles go stale after `save_as_mainfile`; fetch the object and modifier again (geometry research section 11).
14. EXR in 5.2: set `media_type = 'MULTI_LAYER_IMAGE'` first, then `file_format = 'OPEN_EXR_MULTILAYER'`; read every part of the file (section 2).
15. In Geometry Nodes the colour node is `FunctionNodeCombineColor`, not `ShaderNodeCombineColor` (geometry research section 11).
16. Rigid Body: tiny or fast stones tunnel through the floor; scale the world up and use linear damping 0.7 (section 10).
17. The seam measure can read 1.63 on a seamless brick tile because brick edges sit near the edge; always look at the half-tile-slid picture too
   (geometry research section 3.1).

---

## 13. Recipe cards (every line was run)

**Card 1 - Photograph geometry from above.** Orthographic camera, ortho_scale 1, at (0.5, 0.5, 5); Cycles 4 samples, Box filter width 1; Emission of
(Position Z - lowest) / (highest - lowest), clamped; Raw view; 16-bit PNG. Colour = Attribute `piece_colour` into Emission (+ ambient occlusion 0.8,
distance 0.03, for dark crevices; 13 times slower). Normal = Sobel of the height, or Emission of Normal x 0.5 + 0.5 on a Shade Smooth mesh: score both.
End the group with Set Material and swap its material per picture. (`lib/contrib/gn_tools.photograph_geometry`)

**Card 2 - Make anything wrap.** 9 copies shifted -1, 0, +1 in x and y; delete copies that cannot reach the tile; one shared `piece_id` for every
random value; repeating (donut) noise; curves with whole-number slope and whole waves; look heights up at the wrapped place. Check with the
half-tile-slid picture.

**Card 3 - Rows of bricks, slates or planks.** Mesh Line -> Mesh to Points -> row = Floor(index / per row) -> Random Value weight -> Accumulate Field
(Trailing / Total) -> row shift -> Wrap -> Duplicate Elements x 9 -> Instance on Points (a Cube) -> Realize -> Mesh Bevel (4 offsets, sharp edges
only) -> Subdivide level 3 -> Set Position with repeating noise. Slates: height factor 1.32 and a tilt of -atan2(lift, height).
(`lib/contrib/layout_tools.py`, research `recipe_brick_layout.py`, `recipe_slate_layout.py`)

**Card 4 - Stones that never overlap, and wrap.** Points with a `radius` attribute -> Repeat zone with the relaxing step (9 copies, Index of Nearest,
push by 0.45 x overlap, delete copies, Wrap) x 40 to 60 -> Instance on Points (Pick Instance among convex-hull shapes) -> Realize -> facet colours.
(`lib/contrib/relax_tools.py`; NEW strip `pictures/geometry-strip-relax-steps.jpg`)

**Card 5 - A groove, rut or crack.** Curve Line -> Resample Curve (Count) -> Set Position (whole-number slope + whole waves) -> Curve to Mesh (no
profile) -> 9 copies -> Geometry Proximity (Edges) from a dense Grid (sample z = 0) -> Map Range distance 0..half-width to depth..0 (a V), or a Float
Curve with extend Horizontal (a rut with banks) -> Set Position z. (NEW strip `pictures/geometry-strip-groove-width.jpg`)

**Card 6 - A ridge, bar or rope.** The same curves -> Curve to Mesh with a Curve Circle (round ridge; Resolution 3 = triangle grain ridge) or a
Quadrilateral (flat bar) -> 9 copies. Sweep after scaling. (NEW strip `pictures/geometry-strip-curve-ridge-radius.jpg`)

**Card 7 - Rivets along a bar.** Curve Line along the bar -> Resample Curve (Count 9 for a full-length strap) -> Curve to Points -> Instance on
Points (8-sided Mesh Cone, Radius Bottom 0.021, Top 0.004, Depth 0.016) -> Realize -> Set Material.

**Card 8 - Holes.** One cutter object holding every cylinder; Boolean Difference with the Manifold or Float solver (or Mesh Boolean in Geometry Nodes).

**Card 9 - A settled pile (only if it must lean).** Rigid Body, world 10 times up, Convex Hull, margin 0.002, friction 0.9, linear damping 0.7, 30
solver iterations; step with `frame_set`; read `matrix_world`; move the pile half a tile and settle again, twice; count the leftover overlaps.

---

## 14. What was tested and what was not; files

**Tested** (in Blender 5.2.2 here): everything marked TESTED above, in the geometry research's scripts (`research/experiments_geometry_nodes_curves_modifiers_physics/*.py`)
and the builds' geometry routes (`recipes/brick/generator/gn_blobs_route.py`, `recipes/slate/generator/geometry_route_slabs.py`,
`recipes/wood/generator/geometry_route.py`, `recipes/metal/generator/metal_geometry_route.py`, `recipes/mud/generator/geometry_route.py`,
`recipes/gravel/generator/geometry_route.py`). The checkers re-ran the metal, mud and slate routes and found the same numbers (metal correlation 0.072;
mud 1,090 flat shapes and 7,080 node vertices; slate: "all rows match the stored scores", `verifier_answer.json` of each). The mud checker found the
builder's words "smooth round lumps" wrong: the render shows low-poly rocks with flat facets; the conclusion stands.

**NEW for this guide** (`cookbook/checks/geometry_and_painted_strips/`): `make_geometry_strips.py` (relaxing strip, groove-width strip, ridge strip,
Set Material test; 10.1 s in all, `numbers_geometry.json`), `finish_strips.py` (white gaps between squares, small JPG copies). The relaxing numbers
repeat the research's exactly.

**Not tested:** EEVEE and GPU rendering (no graphics card); Cycles' own Bake from a Geometry Nodes object; Rigid Body at real scale and a 4th settling
round; Particles, Cloth, Dynamic Paint, Fluids and the 5.2 hair and cloth physics; Remesh, Weld, Wave, Cast and Simple Deform inside a recipe; Material
Maker's Tiler and Splatter; a real-geometry shape with painted colour on top; whether any of the numbers hold on another seed (every result is one seed).

**Pictures used** (small copies in `cookbook/pictures/`, made by `finish_strips.py` from the named originals; the originals are unchanged):
`geometry-overview-all-recipes.jpg` (from `research/.../out/overview_all_recipes.png`), `geometry-wrap-test-sheet.jpg` (`out/t07_wrap_sheet.png`),
`geometry-modifiers-from-above.jpg` (`out/t05_modifiers_sheet.png`), and the NEW `geometry-strip-relax-steps.jpg`, `geometry-strip-groove-width.jpg`,
`geometry-strip-curve-ridge-radius.jpg`, `geometry-trap-set-material.jpg`.
