# 04 Lessons - wood - what carries over to other surfaces

This file is for the day you start a surface nobody gave you (a tile floor, a leaf litter, a stone wall). It says what the wood work taught, in the order you would use it. The numbers are the wood's; the lesson is meant to hold for other surfaces. Words used: the **tile** is the 1254 x 1254 picture; the **description** is the small file the generator is driven by; a **patch** is an area of one flat colour; a **dot** is one picture dot.

## How to start a new surface (the checklist, in order)

1. **Prove how the maps were made, first (10 minutes, plain Python).** Fit three small things that turn the reference COLOUR into the reference HEIGHT and NORMAL: a brightness recipe, a straight stretch with two cut-off numbers, a blur. On the wood: brightness 0.299 R + 0.587 G + 0.114 B, height = (brightness - 12) / 116 cut at 0 and 1, blur 0.5, normal = slope of the 8-bit height times 8. This removes height and normal from your list (they follow the colour) and tells you the ceiling (4.15 steps, 4.3 degrees). Script: `analysis/derivation_ceiling.py`; it works unchanged for another surface if you change the folder name.
2. **Posterise the picture to 8, 16, 24 colours and look.** If 16 colours give a colour difference near 3, the surface is a painted label map: describe patches, do not invent shading. (Wood: 3.1.)
3. **Count the patches and their sizes before you design anything.** Cut the picture into same-colour areas and count them in classes that double. Wood: 92,000 areas; every size class from 4 to 2000 dots holds about the same share of the picture ("the same at every scale"). That one table told me the traced description would be big (hundreds of kilobytes) and the fine detail could only be INVENTED. Also measure: how long compared with tall the patches are (wood 2.7 : 1, almost all horizontal), the long dark lines (cracks, gaps, joints), the round things (knots, blobs), which tones sit on which.
4. **Find the dark line network and the round things first; they are cheap to describe and decide a lot of the picture.** Wood: five gap lines (10 waves each), 25 long cracks as centre lines with widths, 4 knots, 30 splatter clouds, pebbles: 5 KB in all.
5. **Build the generator as a painter that draws flat shapes back to front** (planks, strips, patches, cracks, ribbons, rings, blobs all become flat polygons; a mesh photographed from above). It needs no special code per surface: bricks, slates, planks, plates and stones are all "a list of flat coloured polygons in painting order".
6. **Make the maps from the finished colour picture inside the generator** (height by the straight stretch, normal from the 8-bit height). Do not paint height or normal separately; the colour is the only free part.
7. **Compare with BOTH tools and LOOK at the sheets.** "Same picture dot for dot" and "same kind of surface" disagree on purpose; they tell different things (see traps).
8. **Climb the ladder one layer at a time and write down the size of each step**: layout only; + invented paint; + grain; then traced patches at 20, 40, 60, 150, 300, 480 KB. The curve (bytes against accuracy) is the most useful result you will have.
9. **Then the sampler**: for each layer decide what is a NUMBER (counts, sizes, spreads, colours) and what is a DRAW (positions, shapes); measure the spreads on the reference; draw from them with a seed.
10. **Test transfer by changing numbers only** (palette, counts, sizes, family spreads, a few hand-written lists); write down what you had to change. Wood to deck boards: see the Recipe, section 9.

## What each layer buys (wood numbers; dot-for-dot SSIM, same-kind score)

| layer added | description size | what it fixed | what it did NOT fix |
|---|---|---|---|
| layout only (planks, gaps, 25 cracks, knots, splatter, pebbles; flat colour) | 5.2 KB | the plank structure; SSIM 0.377 | any paint; height error 40.2; kind 0.209 |
| + invented paint (zones, strips) + dry-brush grain | 6.2 KB | looks like the surface: kind 0.635 | the match dot for dot: SSIM 0.220 (the paint is not where the real paint is) |
| traced patches, coarse | 24 KB | big tones in the right places: SSIM 0.423 | edges (skill 0.111) |
| traced patches, 62 KB | 60 KB | SSIM 0.488, edge skill 0.229 | thin cracks and fine strips |
| traced patches, 150 KB | 151 KB | tier layout: SSIM 0.591, edge skill 0.361 | fine edges; normal 19.4 degrees |
| traced patches, 300 KB | 301 KB | SSIM 0.674, edge skill 0.431, height error 17.6 | normal 16.8 degrees |
| traced patches, 462 KB (the biggest class) | 462 KB | SSIM 0.725, edge skill 0.523, colour difference 4.61 | tier close (needs normal under 12 degrees: got 15.5) |

Short version: **layout buys structure, invented paint plus grain buys the look, tracing buys the match.** The jump in dot-for-dot accuracy only comes from describing the actual patches (and it costs a hundred times the bytes); the jump in "looks like it" comes from a few kilobytes of statistics.

## Traps (things that cost time here and will cost time on the next surface)

* **Do not trace by "drop the small patches".** Joining the two neighbouring patches that differ least (Ward clustering) and giving each patch its average colour is far better at the same size (SSIM 0.76 against 0.53 at 600 KB).
* **A few patches is not a small file.** 400 patches cost 139 KB because the biggest ones have huge ragged outlines. Make the outline looseness follow the thickness of the patch.
* **Do not fit paint colours with a plain table of probabilities.** It makes confetti. Colour a small patch as "the colour beneath it plus a small random change" and cover everything first with big slowly changing zones.
* **The structure score (SSIM) hardly notices fine paint.** A copy of the reference blurred by 2 dots still scores 0.62. Use colour difference, edge skill, height error, normal angle and the same-kind score together, and look.
* **The normal angle is the measure that costs most.** The reference normal map is made of features of 1 to 4 dots; the flat normal map is 24 degrees off; a 300 KB traced colour gets 16.8, a 470 KB one 15.5, an earlier test with 1.5 MB of corners 12.6. If a surface's normal is fine-grained, expect never to reach the "close" tier at 512 KB; do not chase it with random grain (random grain made the normal worse).
* **Blender's Noise texture does not tile.** Read it on the surface of a 4-D donut (the project's `tileable_noise_group`, or my `wood_shaders._donut`); give different numbers of features across and up to stretch it. Voronoi "distance to edge" on a stretched donut gives diagonal lines, not horizontal ones: use the contour lines of a stretched noise instead.
* **Shapes must be folded into the tile before shifting, and drawn again +1 and -1 tile where they touch an edge**, or the half-tile test fails.
* **Draw order is a camera trick:** each next shape a hair higher, camera above them all. With 15,000 shapes the step must be tiny (0.00002) and the camera must be above the highest shape.
* **Two comparison tools read slightly different heights** (the 8-bit upload and a smoothed copy). Score the same way every time.
* **Score noise**: the seed alone moves the same-kind score by +-0.03; do not tune to a difference under 0.05.
* **Do not wait for a job by searching for its own name** (the search finds the waiting shell). Wait on a file or a count of lines.

## What is specific to the wood and what is general

General (reuse as it is): the derivation proof; palette and patch-count tables; the painter (polygons back to front, wrap copies); height and normal from the finished colour; the merge-tracing; the outline looseness rule; the sampler idea (numbers = spreads, draws = positions); zone-plus-strips colouring; the grain node group (noise cut at two levels); the audit; the ladder; both comparison tools; the half-tile test.

Wood only: five boards with wavy gaps; strips 2.7 to 10 times longer than tall; rust clouds; knots with rings; pebbles in the gaps; the numbers in `fitted_distributions.json`. To change surface you change THESE numbers and lists (see the deck boards: no generator code changed).

## What I would do next (honest)

* Smoother, less rectangular strip shapes in the invented paint (it looks like pixelated camouflage next to the reference).
* A branching crack model from the skeleton graph (long cracks with tan chip rims).
* Tracing with shared borders (store each border once): about a third fewer bytes for the same accuracy.
* A fine-scale model for the normal map (the part that costs most).
