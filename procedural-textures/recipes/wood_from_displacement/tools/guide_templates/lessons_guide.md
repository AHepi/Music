# 08 Lessons - wood from your displacement and colour maps - what carries over to other surfaces

**What this file is:** a plain-words list of what the wood-from-maps job taught, for the next surface. It is written for a person who is not a programmer. It says when to use a picture as source material and when to build from nodes only, how to cut any picture into pieces and lay them out again so that a big area never repeats, and the traps that cost time. The full recipe and all numbers are in `08 Recipe - wood from your displacement and colour maps - how it is made.md`. Everything here was run on the wood only; where I guess that something carries over to other surfaces, the text says "guess".

Words used the same way everywhere: a **dot** is one pixel; the **source map** is an uploaded picture used as raw material; a **piece** is a part of the source map; a **window** is the piece one board shows; a **tile** is the default square (1254 x 1254 dots) that repeats without a seam; an **area** is a bigger picture of new content; a **seam** is a visible line where a picture does not continue into its own copy; a **near copy** is a part of a picture that looks almost the same as another part.

---

## 1. The short version

1. **A map used as source material beats nodes alone for this wood, by a wide margin**: the "same kind of surface" score of the new tile is **@@main_mean@@** on average (three seeds) against **@@earlier@@** for the best new tile of the earlier pure-node wood recipe, scored the same way. The price: the result can never be better than the map, the map's own features come back again and again in a big area, and you must have the map.
2. **The map cannot just be repeated** (it does not wrap, and every repeat shows the same knots). The method that worked: cut the map into pieces along its own structure, then let nodes choose a random piece for every board.
3. **Every cut between two pieces must be hidden by something that is made on purpose** (a dark crack, a dark band). A hidden cut costs nothing; a visible one ruins the area.
4. **Check the things a person cannot see by looking**: that the tile repeats exactly (slide test), that the pipeline adds nothing of its own (source-unchanged test), and that a big area really has the same amount of every feature per dot as one tile (count them).

---

## 2. When to use a map as source and when to build from nodes only

| Question | Map as source (this job) | Nodes only (the earlier wood recipe) |
|---|---|---|
| Look of one tile | looks like the uploaded wood because it IS the uploaded wood, re-arranged | needs a description of every feature; the best new tile looked washed out and blocky |
| "Same kind" score (0 to 1) | **@@main_mean@@** (three seeds) | **@@earlier@@** (best of 8 new tiles) |
| Big area that never repeats | the same pieces come back: each used dot of the map appears about **@@reuse_times@@** times in 16 tiles, flipped, zoomed, toned and stamped differently | new content everywhere, nothing is reused |
| Knots, big cracks | come back (only two usable knots exist in the map) | drawn fresh, but weak |
| Cost to build | about 900 nodes, no analysis beyond measuring the map | a long analysis and a generator program |
| Needs the map at bake time | yes | no |

**Rule of thumb (guess for other surfaces):** use the map as source when the person values the look of THAT picture and the surface is made of separate pieces (boards, bricks, slates) that can be re-arranged; use nodes only when the surface must be new everywhere and the map is just a guide.

---

## 3. How to cut any map into pieces (the recipe in eight steps, with the wood as the example)

**Example first.** The wood map has five rows of boards separated by dark gaps. Cut the picture from the middle of one gap to the middle of the next and you get four usable "row strips" (the top row is only 155 dots high, so it was not used). A new surface is then built row by row: every board picks one of the four strips, a random start along it, maybe flips it, and shows that window.

1. **Measure the structure** of the map: where the separators are (rows, gaps, joints), where the rare features are (knots), where the stains are, and whether the map wraps (here it does not: the jump across the left-right edge is 4 times a normal jump). Write the numbers down (`research/measurements_wood_source_map.json`).
2. **Cut along the separators, in the middle of them.** A cut in the middle of a dark gap is nearly invisible later, because both sides of any new join are dark (a dark band of the recipe's own is laid over the cut to be sure); a cut at the edge of the gap would put wood against wood.
3. **List the rare features and where they are**, so that a window can avoid them (knot-free stretches) or contain exactly one (knot boards). Keep the list short: a table of 4 rows is fine, a table of 256 is not (a long compare-and-mix table made 2115 nodes in the research and rendered black; one Color Ramp node holds a 4-column table in one node).
4. **Lay out the new surface with random numbers made from the position** (the White Noise Texture node in 4D works as a hash: the same inputs always give the same three random numbers). Row number and board number go in; start, flip, zoom, tone come out. The same node tree makes a tile that repeats (numbers repeat after one tile) and an area that does not (numbers keep counting up): one switch.
5. **Hide every cut with something made on purpose.** Here: a dark ragged crack with dirt and pebbles where two boards meet, a dark band on every row boundary, partial cracks inside boards that were joined from two. Make the crack wider than the worst mismatch of the cut.
6. **Read all maps at the same position** (build the position once, feed it to every Image Texture node). Colour, height (and anything else) then match by construction. Do not read a normal map from a re-arranged picture: a flipped piece would have its slopes pointing the wrong way. Make the normal from the arranged height at the end.
7. **Keep the "per dot" amounts the same in a tile and in an area.** Everything that is "at most one per row" needs a "per tile-wide stretch" version for areas, or a big area gets four times fewer knots per dot than one tile.
8. **Check** (section 5).

---

## 4. Traps (what went wrong here, so that nobody repeats it)

1. **Cutting the rows from gap-top to gap-top** put wood against wood at every row boundary: the project's seam measure said "seam" (score 0 for tiling) and the picture had no dark gap where the rows met. Cutting from gap-middle to gap-middle and laying a dark band over the boundary gave tiling 1.0.
2. **Stain stamps taken from the map can contain the knots.** Two of my eight stain stamps contained the biggest knot; the knot came back as a smaller second knot in the same board. Look at every stamp.
3. **"At most one knot per row" in an area is one knot per 4 tiles of row.** Found only because I counted the knots in the 4 x 4 picture.
4. **Two neighbouring boards that take the same source row show the same piece side by side, one of them mirrored** (a butterfly pattern across the joint; 2 of 25 joints in one seed). Fixed by giving every next board the next source row.
5. **Bilinear reading blurs when a window is zoomed.** A bit of zoom (10 percent) did not change the score in the one test I made (0.758 without zoom, 0.763 with); the harness's default pixel filter blurs by about one dot, so the recipe asks for a narrow filter and one sample when one picture dot = one source dot.
6. **Seamless noise and cell patterns need the "donut" trick** (4D noise or 4D cells on two circles). I used it from the start for everything that sits inside the tile (large patches, the dirt and pebbles in the cracks); plain noise would show a seam at the tile edge. I did not run the plain version, so this is a rule from the earlier work, not a failure seen here.
7. **Eight-bit debug pictures carry dither noise** (the renderer adds ±1 level of noise), so board numbers read from a colour debug picture split every board into hundreds of pieces. Read exact numbers from the 16-bit height output.
8. **Relative output paths and the folder Blender is started from:** my job list wrote into the wrong folder (the project root) once. The job driver now resolves paths against the recipe folder.
9. **The project's tools can disagree with what you see.** The "same kind" tool punished a tile whose top edge and bottom edge differ (the row structure) although the tile repeated exactly. Check the real thing (slide the picture by half a tile and compare), not only the score.
10. **A mislabelled rule in the research notes:** the uploaded normal map equals the two-neighbour slope of the uploaded height at strength 8 (0.004), NOT a 3 x 3 Sobel filter (0.03). The harness's function named `sobel_normal` is the two-neighbour rule.
11. **Stronger variation lowers the "same kind" score.** Each thing that breaks repetition (stains, large patches, tone, zoom) moves the picture away from the map's own statistics. Choose the amounts on purpose (section 5 of the recipe guide has the numbers).

---

## 5. What to check on any re-arranged map (all of these were run for the wood)

| Check | What it proves | How it was done |
|---|---|---|
| **Slide test** | the tile repeats exactly | bake the tile with the whole pattern slid by half a tile; it must equal the normal bake slid by half a tile (mean difference @@half_tile_height@@ in height) |
| **Source-unchanged test** | the pipeline (nodes, photograph, normal rule) adds nothing of its own | switch the arrangement off: height must come back (difference @@unchanged_height@@) and the normal made from it must equal the uploaded normal (@@unchanged_normal@@) |
| **Shift test on a big area** | no hidden repeat at the tile or map width | correlation of the picture with itself slid by one tile: @@shift_new@@ for the new 4 x 4 area, @@shift_plain@@ for the plain repeat |
| **Reuse count** | how much of the map is used and how often | the recipe writes "which source dot is this?" as an exact picture; count |
| **Near-copy search** | do board-sized pieces come back | the research test: 40 patches searched for in the other rows (new area: @@near_new@@ have a near copy; plain repeat: 100 percent) |
| **Look at every joint at full size** | no visible cut | a sheet with one full-size crop per joint (about 25 per tile) |
| **Count the rare features per dot** | areas and tiles have the same density | knots per tile (@@knots_per_tile@@ in the 4 x 4 area) |

---

## 6. Which parts carry over to other surfaces (guess, not tested)

* **Brick, slate and plank-like surfaces:** the row and board layout, the per-board random window, the hash from position, the crack that hides cuts, and the checks carry over almost unchanged (a brick is a board with other numbers). The slate-in-layers recipe already has a layout; a window-per-brick step could be added to it.
* **Gravel, mud, metal:** no separators to cut along. The research found that blending random shifted copies of the whole map (hex or stochastic tiling) is the method for noise-like surfaces; it was not tried in this job.
* **The checks carry over to every surface**, with or without a map.
* **What does NOT carry over:** the table of knot-free stretches and the stain stamp positions are measured on this map only. The measuring script `research/tests/measure_wood_source_map.py` shows how to get such numbers for another map.

---

## 7. Not tested, and where I am unsure

* Only the wood was tried. Everything in section 6 is a guess.
* No person has looked at the pictures for this job (the numbers and my own looking are all there is).
* The "same kind" score is a proxy: it rewards staying close to the map's own statistics, which is the opposite of what a big non-repeating area needs; read it together with the repeat tests.
* Seeds 1 to 3 only.
