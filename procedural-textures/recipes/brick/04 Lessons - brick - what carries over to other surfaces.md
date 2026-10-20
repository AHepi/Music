# 04 Lessons - brick - what carries over to other surfaces

This file is for the day you start a surface nobody gave you (a tiled floor, a stone wall, a pavement, a field of pebbles). It says what the brick work
taught, in the order you would use it. The numbers are the brick's (from `final_report.json`, `scores/` and the checker's `verifier_answer.json`; the full
story is in "04 Recipe - brick - how it is made.md"); the lessons are meant for other surfaces. Like the recipe, this file was written from the builder's
and the checker's files after the brick work was finished.

Words used (the same as in the recipe): the **tile** is the 1254 x 1254 picture; a **dot** is one dot of it; the **description** is the small file of
numbers the generator reads; a **patch** is an area of one flat colour; a **blob** is a patch written as a ragged ellipse (8 numbers); a **traced patch** is
the outline of a real patch of the reference; a **cell** is a patch the generator cuts out by itself; a **course** is a row of bricks; the **ring** is the
dark outline round each piece; **grain** is a tiny random lighter-or-darker change given to every single dot; the **same-kind score** is the
texture_compare overall score (1 = the same kind of surface).

## How to start a new surface (the checklist, in order)

1. **Prove how the maps were made, before anything else (plain Python, the first thing you do).**
   Example from the brick: grey brightness of the colour (0.299 red + 0.587 green + 0.114 blue), blurred 0.7 dots, looked up on a 12-point tone curve,
   gives the reference height to within 3.0 steps of 255; the slope of that height times 6 gives the normal map. Fed with the reference's own colour, this
   rule reaches the tier "exact" (height error 3.02, normal error 3.63 degrees, `scores/ref_roundtrip/pixel.json`).
   The general rule: fit the smallest recipe that turns the reference COLOUR into the reference HEIGHT and NORMAL (`analysis/derivation_ceiling.py` is a
   starting point). It takes two maps off your list, and it gives you the ceiling: the best any recipe can reach even with a perfect colour picture.
   **While you are there, check what the height MEANS.** On the brick, bright = high, so the mortar is HIGH and the bricks are LOW: the reverse of a real
   wall. Real raised bricks correlated -0.15 with that height. Find this out before you build any real geometry for height.

2. **Squeeze the colour picture to a palette and look at which colour belongs to what.**
   16 colours (k-means in the Lab colour space, after a light bilateral smoothing that keeps edges) were enough for the brick; 32 were not better.
   Then ask: which colours occur only on the pieces, only in the gaps, only in the dirt? On the brick, eight reds and oranges never occur in the mortar,
   and the three darkest colours are soot and ring. Those families become the colour tables of your generator.

3. **Find the layout from the thin dark lines, not from colour, and look at it drawn over the reference.**
   Example: every brick joint is two dark ring lines about 20 dots apart; a black top-hat filter plus a search for PAIRS of lines found the 12 courses and
   their bricks. Draw the rectangles over the reference and LOOK (`analysis/layout_overlay.png`).
   Then check whether the reference really repeats: the brick reference does not (12 courses add up to about 1223 dots; a 30-dot sliver course and a mild
   seam are left where it was stitched). Let the description list what is there instead of forcing a perfect grid.

4. **Measure the pieces and the paint as statistics, by AREA as well as by count.**
   Sizes and spreads of pieces and gaps, the base colour of each piece, the patches per size band (doubling sizes), how stretched and tilted, how ragged,
   and which colours. On the brick, half of all patches are 36 dots or smaller, yet half of the picture lies in patches bigger than 511 dots
   (`analysis/element_stats.json`). A generator that fills a surface with cells needs the AREA-weighted colour table; a count-weighted one gives
   camouflage. Also measure the "clouds" (soot, spalls, moss, rust): where they gather and how big the gathering is.

5. **Bake the cheapest descriptions first and score them with BOTH tools, then look at the difference sheet.**
   Layout only (1.7 KB) and "+ one colour per piece" (still 1.7 KB). On the brick, layout alone already put every brick edge in place (the rectangles
   are yellow in the difference sheet) but scored only 0.174 on edge skill and 0.127 on the same-kind score. Fix the biggest visible wrong thing first.

6. **Add paint from big to small and write down the ladder (size against accuracy).** Try cheap shapes before tracing: on the brick a ragged ellipse
   (8 numbers) beat a traced outline at every size up to about 400 KB; tracing only the biggest patches was the worst buy of all (87.7 KB: edge skill
   0.146, worse than the 7.8 KB class S). Stop where the curve flattens.

7. **Add the ring (the dark outline) if the surface has one.** On the brick it raised edge skill from 0.357 to 0.421 and the same-kind score from 0.308 to
   0.406 at 62.5 KB; drawn on top of TRACED patches it made things slightly worse (they already contain the dark lines).

8. **Add grain last, as a separate switch, and say which goal it serves.** Grain lowers the dot-for-dot colour measures and raises the same-kind score
   (class L: SSIM 0.673 -> 0.537, colour difference 5.71 -> 6.37, same-kind 0.432 -> 0.598 with grain 0.14; a sampled tile: 0.576 without grain, 0.730 with it). Keep it off when
   matching the reference dot for dot, on when making new tiles.

9. **Write the sampler from the measured statistics, and write the accent colours down explicitly.** Which colours are the soot, the chips, the moss:
   write them as lists in the model file. Do not let the code guess them from colour saturation: on the cobblestones the guess turned every grey stone
   into "spall" colour and the first tile came out with black stones.

10. **Make the tile repeat by construction, read the tile size from the description, and test the repeat THREE ways.**
    By construction: pieces that add up to the tile, anything crossing an edge drawn again one tile over, cell seeds that repeat every tile, and every slow
    wave or noise with a length that divides the tile (the brick's tone dial and wobble do NOT, see the traps). Then test:
    (a) the half-tile test (`generator/seam_test.py`): proves the wrap-round DRAWING works;
    (b) the first picture column against the last, and a band test on a grain-free bake (`../../cookbook/checks/brick_seam_without_grain/seam_check.py`):
        catches content that does not join up and a wrong tile size;
    (c) your eyes on a 2 x 2 repeat and a zoom of the corner where four tiles meet.
    Each one catches faults the others miss (see the traps).

11. **Bake at least eight new tiles before you believe the generator is general, and look at how wide the family is.** Measure the same-kind score of
    each, how different they are from each other (brick: as different from each other as from the reference, 25.9 against 26.9 steps), and also look for
    what they ALL share: the brick's eight tiles all have 12 courses of 4 bricks and the same palette, so they are one narrow family.

12. **Carry the recipe to a new surface by changing numbers only, and keep a record.** Write down every number you changed, every line of code you had to
    add, how long it took, and what went wrong. Keep the script that writes the new model in step with the model file you actually used (see the traps).
    And re-check the meaning of the height for the new surface (step 1): for stones in sand, the stones should be high.

## What each layer buys (brick numbers; 1254 dots; `final_report.json`, `scores/rate_distortion.json`)

| layer added | description size | what it fixed | what it did NOT fix |
|---|---|---|---|
| layout only (rounded rectangles, one colour, thin border) | 1.7 KB | every brick edge in the right place | colour (difference 14.3), height error 38, same-kind 0.127 |
| + one colour per brick | 1.7 KB | colour difference 14.3 -> 12.7, same-kind 0.127 -> 0.235 | the paint |
| + 146 fitted blobs + ring (class S) | 7.8 KB | the first pixel tier ("layout": edge skill 0.306), same-kind 0.365 | small patches, mortar texture |
| + 1,818 blobs (class M) | 62.5 KB | colour difference 7.93, height error 25.0 | edges (0.421) |
| + up to 11,406 blobs | 367 KB | SSIM 0.626, edge skill 0.624, height error 19.3 | normal error (15.4) |
| traced patches instead, 12 dots and more (class L) | 497 KB | SSIM 0.673, colour difference 5.71, edge skill 0.656, height error 15.35: four of the five "close" rules | normal error 13.93 (needs 12); it is a copy, not a procedure |
| + grain 0.14 | + 1 number | same-kind 0.432 -> 0.598 | lowers SSIM to 0.537; part of the gain is a measuring effect (see traps) |
| the derivation rule | 0.3 KB | height and normal for free | nothing it can fix: errors in the colour go straight into the maps |
| a sampler (statistics + seeds) | 6.3 KB model, 9.3 KB per tile | unlimited new tiles, same-kind 0.684 to 0.730 | the reference's big flat hand-painted patches; family is narrow |

Short version: **layout buys the edges, a palette buys the colour, fitted blobs buy the "layout" tier cheaply, tracing buys the last bit of match, and
grain buys "looks like the same kind of surface".** The dot-for-dot score is decided by tens of thousands of tiny details: even a perfect 16-colour
flat-patch copy needs 197,504 patches to reach SSIM 0.945 (`analysis/posterise_ceiling.json`).

## Traps (things that cost time on the brick and will cost time on the next surface)

* **The half-tile test proves the drawing, not the content.** It slides finished shapes, so both of its pictures always hold the same shapes. It could not
  see the area bug (both bakes had it), it cannot see a slow tone wave that does not repeat every tile, and it cannot be run on traced descriptions.
  What caught the area bug: the first picture column correlated 0.23 with the last, against 0.9 between neighbouring columns.
* **A fixed tile size in the code breaks every bigger area silently.** The generator divided by 1254; the 2508-dot wall came out as a quarter of itself,
  enlarged. Read the tile size from the description everywhere.
* **Grain fools the seam measure and the same-kind score.** Grain makes ordinary dot-to-dot jumps bigger, so a seam looks smaller: class L's seam measure
  went from 2.11 to 1.0 with grain, its "tiling" part from 0.444 to 1.0, although the picture's seam did not change. That alone is about 0.04 of the
  overall score. Measure seams on a grain-free bake.
* **SSIM hardly notices paint.** A wall of flat rectangles already scores 0.518; the full trace 0.673. Judge a painted texture by colour difference, edge
  skill, height error, the same-kind score and your eyes together.
* **The two scorers pull against each other at the finest scale.** Dot-for-dot rewards clean flat patches; same-kind rewards dot-level noise. Report both,
  and say which one a setting is tuned for.
* **Counting patches by number makes confetti.** Thousands of tiny patches outnumber the big ones; tables weighted by count give a camouflage look. Use
  area-weighted tables for cells that fill a surface, count-weighted only for scattered blobs.
* **Guessing roles from colour breaks on the next palette.** "Low saturation = spall" was right for red bricks and wrong for grey stones (black stones).
  Write the roles down.
* **Height can be upside down compared with the real object.** Here the mortar is high because the height is brightness. Real slabs with Solidify and
  Bevel gave height error 39 against 25 for the colour-derived height. Check the sign before building geometry.
* **The project's size check has a false alarm** on lists of long polygons ("looks like a picture"). The brick work-round: start the traced list with the
  tile-sized ground square. (Suggested lib change: call it a grid only when the rows have equal length.)
* **A model file edited by hand drifts away from the script that made it.** The cobble model gained accent lists, smudge settings and area tables by hand;
  `transfer/make_cobble_model.py` still writes the old version, so "re-run the script" does NOT repeat the transfer. Either edit the script and re-run it,
  or say in the script's first lines that the stored file is the true one.
* **Sweep strips must say what their base is.** The brick strips used a coarser, grain-free base (cells twice the default area, 384 dots, 4 samples), and
  were labelled "(reference)" where they meant "default". Label the default as "default", say which defaults were measured and which chosen by eye, keep a
  gap between the squares (without one, the joins looked like cracks in the bricks), and do not stretch the squares.
* **Deleting pictures to save disk breaks re-checking.** Only one of the eight new tiles kept its height and normal maps; the checker had to re-bake to
  re-score. Keep the descriptions (they are small) and write down which folders are incomplete.
* **Times on a shared machine are not stable.** The same bake took 16 s for the builder and 28 s for the checker. Quote times as "about".
* **Tool handling that cost time:** `python3 -I` ignores the script's own folder (add it to `sys.path`); Geometry Nodes output renders black without a Set
  Material node in Blender 5.2; Solidify grows along the face direction, and faces built with the picture's y running down point down;
  `pkill -f PATTERN` also kills your own shell when the pattern is in your own command line.

## What is specific to the brick, and what is general

General (reuse as it is): the derivation proof and its ceiling; the palette families; finding the layout from thin dark lines; area-weighted patch
statistics; the painter's stack of flat shapes photographed from straight above (one mesh, a tiny height step per shape, Emission, an orthographic camera);
tessellate_polygon for shapes with holes; the ring; grain as a separate switch; the ladder of description sizes; a sampler with explicit accent lists;
periodic by construction with the tile size read from the description; the three seam tests; the two scorers used together.

Brick only: running-bond courses of 4 bricks with random widths; two colour families (brick reds, mortar greys) plus soot; rounded rectangles with a ring
that is thin at the top and left and a shadow band at the bottom and right; spalls; soot clouds running down several bricks. To change surface you change
THESE numbers, not the code. The cobblestone test showed where that stops: a re-coloured wall of the same family is "new numbers" (20 minutes); real
cobbles (round or irregular stones, fan-shaped courses) would need a new piece shape and a new layout, which is new code.

## What I would do next (honest)

* Make the content provably seamless: give the tone dial and the edge wobble wavelengths that divide the tile, then the half-tile test plus periodic
  content is a proof instead of a strong hint.
* Widen the family of new walls: draw the number of courses and bricks per course, add other bonds, and add a layer of big flat hand-painted patches drawn
  from the area-weighted statistics (the reference's most visible feature that the sampler lacks); smear the soot instead of speckling it.
* Real cobblestones: polygon stones (the shared `lib/contrib/stone_tools.py` makes one stone per cell), irregular courses, and a height with stones high.
* Fix `transfer/make_cobble_model.py` so it writes the model that was used (accents, smudge settings, area tables).
* The normal error is the last "close" rule missed (13.93 against 12): describe the dot-level detail as a noise matched to the reference's feature sizes,
  then measure whether it helps dot for dot or only the same-kind score.
* Move the cell cutter into Geometry Nodes (the blob test showed Geometry Nodes builds 1,818 patches in 0.11 s with the same picture), so the whole wall
  lives in Blender nodes.
