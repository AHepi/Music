# What this does (plain words): writes "04 Lessons - mud - what carries over to other surfaces.md" from the text below and the number files. Run after fill_guide_recipe.py. Plain Python.
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from fill_guide_part1 import *
mud = R.get('mud', {}); gold = R.get('mud_golden', {})
var = (R.get('variation') or {}).get('summary', {})
Lf = mud.get('L_final_traced_ground_plus_corrections', {}); S = mud.get('S_layout_ruts_clods', {}); M = mud.get('M_puddle_tones_stone_faces', {}); R0 = mud.get('R0_flat_ground', {})
L2 = mud.get('L2_traced_ground_2000_patches', {}); L5 = mud.get('L_traced_ground_5000_patches', {})
def row(name, r, what, notfix):
    return f"| {name} | {kb(r.get('description_bytes'))} | {f(r.get('colour_ssim'))} | {f(r.get('colour_mean_delta_e'), 2)} | {f(r.get('edge_skill_2px'))} | {f(r.get('normal_mean_angle_degrees'), 1)} | {f(r.get('texture_compare_overall'))} | {what} | {notfix} |\n"
buys = ('| layer added | size | SSIM | colour difference | edge skill | normal angle | kind score | what it fixed | what it did NOT fix |\n|---|---|---|---|---|---|---|---|---|\n'
        + row('flat ground only', R0, 'the base colour', 'everything else')
        + row('S: puddles + 16 stones + ruts + clods (numbers only)', S, 'it looks like mud (kind 0.11 to 0.26)', 'dot-for-dot match: invented clods and ruts are in the wrong places')
        + row('M: puddle tones, 590 stones with faces, ruts, clods', M, 'colour difference down to 9.7, kind 0.35', 'edges; normal angle worse than flat (clods add false slopes)')
        + row('L: traced ground 2000 patches + fine puddles and stones', L2, 'structure and edges (SSIM 0.63)', 'fine paint; normal 20 degrees')
        + row('L: traced ground 5000 patches', L5, 'SSIM 0.69, edge skill 0.64', 'normal 18.6 degrees')
        + row('L final: + corrections painted last', Lf, 'the stones and puddle edges the finders got wrong', 'tier close (normal angle over 12)'))
TEXT = f"""# 04 Lessons - mud - what carries over to other surfaces

This file is for the day you start a surface nobody gave you (snow, a muddy field, a wet beach, leaf litter, a stony stream bed). It says what the mud work taught, in the order you would use it. The numbers are the mud's; the lesson is meant to hold elsewhere. Words as in `04 Recipe - mud - how it is made.md`: **tile**, **dot**, **description**, **generator**, **layer**, **patch**, **palette**, **ladder**, **kind score**.

## How to start a new surface (the checklist, in order)

1. **Prove how the maps were made (10 minutes, plain Python).** Fit a brightness recipe, a straight stretch with two cut-off numbers, a blur, and a normal strength that turn the reference COLOUR into the reference HEIGHT and NORMAL. Mud: brightness 0.299 R + 0.587 G + 0.114 B, height = (brightness - 20) / 108 cut to 0..1, blur 0.5, normal = slope of the 8-bit height times 9 (matches to 0.35 degrees). Then the maps are not your problem; the colour is. Script: `analysis/derivation_ceiling.py` (change the folder name).
2. **Measure the ceilings before you design.** (a) Snap the reference to 16 palette colours and score it dot for dot: mud SSIM 0.916, normal 9.8 degrees. (b) Replace the ground by a blurred copy of itself at several blurs and score it (`ground_scale_test.py`): mud SSIM stays 0.49 until the blur is below 3 dots. The two tell you which layers can ever buy dot accuracy (the 1 to 3 dot detail) and which only buy the look (everything smooth).
3. **Find the "things" by a one-number colour test, not by palette entries.** In mud, stones and water are grey or blue, earth is orange: the Lab "b" number below 7 marks all of them. Set the threshold so that about a third of the picture is "not earth" (the golden mud needed 3). Fill holes, then split what you found by SHAPE: size after a big opening, solidity (area over convex-hull area), share of clearly blue dots. A watershed on the distance-to-edge picture splits touching round things.
4. **Do the few big things first, the many small things second.** 8 puddles carry the blue; 830 stones carry the dark marks. In the M description the puddles cost 9 KB, the stones 49 KB, the ruts 4.5 KB and the clod numbers 1.4 KB; in the L description the puddles 12.5 KB, the stones 88 KB, the traced ground 288 KB and the corrections 113 KB.
5. **Find the line network at the scale where it is a valley.** Ruts: at 3 dots only fragments, at 10 dots the broad paths. Follow ridges as curves (Hessian test, step along the valley, stop when it fades).
6. **Describe the rest as chances measured relative to the structure you found:** chance of each ground colour by distance from the nearest rut and side (a 2 x 10 x 9 table), patch size, shape, direction. A few numbers; the sampler draws from them.
7. **Build the generator as a painter that draws flat shapes back to front and photographs them from above.** Make height and normal from the finished colour, not separately. Keep a numpy preview painter for fast looks and compare it with the real bake once (mean difference 0.75 colour levels here).
8. **Compare with BOTH tools and LOOK at every sheet.** The pixel tool and the kind tool disagree on purpose: invented ground lowers one and raises the other.
9. **Climb the ladder one layer at a time and write down the size of each step** (table below). Then spend the last bytes on a correction layer: trace the reference only where the picture is still wrong.
10. **Sampler: for each layer decide what is a NUMBER (counts, sizes, chances, directions) and what is a DRAW (positions, shapes).** Calibrate counts with cheap facts on the quick preview before baking: share of non-earth, share of dark dots, density of fine edges.
11. **Seamless:** draw wrap copies of anything touching an edge; prove it with the half-tile test and the area autocorrelation.
12. **Transfer by changing numbers only:** palette, which entries play which part, counts, the analysis threshold. Write down what you changed and how long it took.

## What each layer buys (mud, 1254 dots, real Blender bakes)

{buys}
Short version: **layout buys structure, invented ground buys the look, tracing buys the match, corrections buy the last bit per byte.** In kilobytes: layout 7 KB, look 64 KB, match 300 to 500 KB.

## What to measure first
1. The derivation ceiling (10 minutes). 2. The palette error at 8, 16, 32 colours. 3. The share of dots that are "the other kind of thing" (here non-earth: 31 per cent). 4. The size classes of the things (here: 8 puddles, 830 stones, median stone 83 dots). 5. The scale of the line network. 6. The density of fine edges (mean gradient: reference 6.8 against 3.6 for the first sampled ground; the kind tool's gradient measure stayed at or near 0 until the clods were much denser and smaller, and it is still the weakest measure).

## Traps (each cost time here; each applies elsewhere)
* **Palette classes are not objects.** A lit stone face is blue-grey like water; a pale stone is tan like earth. Test a colour AXIS (Lab b) and then shapes.
* **A marker picture for a watershed must keep 0 for "undecided".** Adding 1 to everything made every stone one dot big and the run said "0 stones" at a minimum area of 12.
* **The scale of a ridge finder decides what it finds.** Check by overlaying the curves on the picture.
* **Smooth tone fields buy ΔE, not SSIM.** Do not spend description bytes on a smooth ground model if you want dot accuracy.
* **Invented texture and traced patches must not be mixed in one tile.** Pick one per tile: statistics for new tiles, tracing for this tile.
* **Description size is not information.** Text corners cost about 8 bytes each; the L class holds about 164,000 numbers (60,000 of them corners of traced patches), which the audit tool puts at 10.7 per cent of the size of an RGB picture of the tile. Report corner counts too, and say plainly where "description" turns into "tracing the picture".
* **The normal map is the hardest measure.** It is made of 1 to 3 dot features; invented clods make it worse than a flat normal map (28 against 23.5 degrees). Do not chase "close" with random grain.
* **The kind score moves 0.03 to 0.05 with the seed.** Compare same-size same-seed bakes, trust the picture first.
* **The reference has its own faults** (a mild seam: the kind tool reads 2.0 to 2.5 for the reference and for anything traced from it). Do not call that a failure of your seamless test; use the half-tile test.
* **Blender's Python has no OpenCV or scipy.** Do analysis and sampling in plain Python; the generator reads only the description.
* **Geometry Nodes:** an attribute called `radius` is overwritten by Mesh to Points; Vector Math "Scale" takes its number on the fourth socket; a Geometry Nodes result renders black without Set Material inside the group.
* **Draw order is a camera trick:** each next shape a hair higher, camera above them all; with 50,000 shapes the stack is 1 tile unit high.
* **Re-bake after every fix, and compare only bakes made by the same code.** My first extra seam test compared two code versions and showed a false alarm of 4.5 per cent different dots. Keep one script that re-runs everything that a change touches.
* **Score a crop of a big picture by its parts, not by the overall number.** The kind tool's tiling group is 0 for a crop that does not wrap, which dragged the area quarters down by about 0.09; I first blamed my own code (a distance grid with a fixed cell count: a real but harmless flaw I fixed on the way).
* **Name collisions in your own scripts:** score files from two surfaces had the same names; use the output folder in the file name. Do not `pkill -f` with text that is also in your own command line.

## What is specific to the mud and what is general

| General (reuse as it is) | Specific to the mud |
|---|---|
| the derivation proof; the palette and "blur ladder" ceilings | stretch 20..128, strength 9 |
| flat-shape painter: shapes back to front, wrap copies, maps from the colour | |
| one-number colour axis test + shape tests + watershed | the Lab b threshold (7; golden 3) |
| ridge following for line networks; chance tables by distance and side | rut band 20 dots wide, 34 long ruts, bank on the lit side (light from the upper left) |
| tracing by Ward merging, loose outlines, correction layer last | 5000 patches at looseness 2.6 |
| sampler = measured numbers + seeded draws; calibration by coverage facts | stone sizes (median 83 dots), puddle size (3000 to 31,600), clod size and chance table |
| two comparison tools; half-tile and area tests | |

## The transfer tests: what changed and how long
* **Snowy track (not given):** only the 16-colour palette, the names of which entries are band / groove / bank / wet / water, three scale numbers, and the height stretch (60..245). About ten minutes of thought, one call, one 40 s bake. The generator was not changed; the sampler got one small option (`maps`, the height stretch). By eye it reads as snow; weak points: rut ends fade like claws, clods too small.
* **Golden-puddle mud (colour only):** the analysis chain with the name changed and one number (threshold 3). About 6 minutes of computer time; I had to trim the M description harder (the golden has 1,085 stones). Results: S {f((gold.get('S_layout_ruts_clods') or {{}}).get('colour_ssim'))}, M {f((gold.get('M_puddle_tones_stone_faces') or {{}}).get('colour_ssim'))}, L {f((gold.get('L_final_traced_ground_plus_corrections') or {{}}).get('colour_ssim'))} SSIM; kind {f((gold.get('L_final_traced_ground_plus_corrections') or {{}}).get('texture_compare_overall'))} for the L class.

## What I would do next (honest)
1. **Whole stones instead of cut-up stones:** merge watershed pieces whose shared border is not a dark line; the biggest remaining error in the L class is the chopped big stones.
2. **Ruts as flowing bands in the sampler:** sample whole S-shaped bundles (two or three parallel curves with the same bends) instead of independent curves; the sampled tiles read as scratches.
3. **Stone clusters, fitted:** pebbles gather around big stones. The sampler now puts half of its small stones within 1 to 2.6 radii of a big one, but that rule is my guess, not a fit (the nearest-neighbour test I ran on the reference did not show strong clustering at 30 dots and above, 90 per cent against 88 per cent for a uniform scatter); fit it on the small stones only.
4. **Real-geometry stones with a stronger sun and sharper shapes** and a dark rim (an inverted hull or a bevel): the route is cheap per stone (3 numbers) but did not match the painted look.
5. **Tracing with shared borders** (store each border once): about a third fewer bytes for the same accuracy.
6. **Glossy water:** roughness 0.1 on the water tones; there is no reference for roughness, so I did not tune it.

## Changes I would like in `lib/` (I did not touch it)
* A shared **flat-shape painter** in `lib/contrib` (`build_tile_mesh`, `channel_material`, `derive_normal_from_height`): the wood and mud generators are about 90 per cent the same code.
* `merge_trace.py` and `trace_tools.py` (now only in `recipes/wood/analysis`) and the **colour-axis element finder** (`recipes/mud/analysis/element_tools.py`) as shared tools.
* `description_audit.py`: also print the number of polygon corners (a fairer size measure than JSON bytes).
* `texture_compare.py`: the `colour_gradient` and `normal_tilt` measures are 0 for anything that does not match the fine-edge density almost exactly; consider a softer scale. The `seam` measure reads 2.0 to 2.5 for anything traced from a reference that has its own mild seam.
* `pixel_compare.py`: an option to ignore a band of N dots at the picture edge, and a tier that does not require a normal map when the reference has none (it already skips missing measures; say so in the report).
"""
open(os.path.join(ROOT, '04 Lessons - mud - what carries over to other surfaces.md'), 'w').write(TEXT)
print('lessons written', len(TEXT))
