# 08 Lessons - wood from your displacement and colour maps - what carries over to other surfaces

**What this file is:** a plain-words list of what the wood-from-maps job taught, for the next surface. It is written for a person who is not a programmer. It says when to use a picture as source material and when to build from nodes only, how to cut any picture into pieces and lay them out again so that a big area never visibly repeats, and the traps that cost time (round 1 and round 2). The full recipe and all numbers are in `08 Recipe - wood from your displacement and colour maps - how it is made.md`. Everything here was run on the wood only; where I guess that something carries over to other surfaces, the text says "guess".

Words used the same way everywhere: a **dot** is one pixel; the **source map** is an uploaded picture used as raw material; a **piece** is a part of the source map; a **window** is the piece one board shows; a **tile** is the default square (1254 x 1254 dots) that repeats without a seam; an **area** is a bigger picture of new content; a **seam** is a visible line where a picture does not continue into its own copy; a **near copy** is a part of a picture that looks almost the same as another part; a **landmark** is a place of the source map so recognisable that a person notices when it comes back; to **paint out** a landmark is to show clean grain from another place of the map instead.

---

## 1. The short version

1. **A map used as source material beats nodes alone for this wood**: the "same kind of surface" score of the round 2 tile is **0.839** on average (three seeds) against **0.665** for the best new tile of the earlier pure-node wood recipe, scored the same way. Say next to the numbers that this is partly expected: the new tile is made from the reference's own dots. The price: the result can never be better than the map, the map's recognisable places come back in a big area unless you deal with them, and you must have the map.
2. **The map cannot just be repeated** (it does not wrap, and every repeat shows the same knots). What worked: cut the map into pieces along its own structure, then let nodes choose a random piece for every board.
3. **Every cut between two pieces must be hidden by something made on purpose, and the hiding should look like the material's own joints.** A straight dark line from the top to the bottom of a row reads as a brick wall; a stepped joint (down, sideways along the grain, down) reads as logs. Round 1 had the straight line, round 2 the step.
4. **The recognisable places matter more than the amount of reuse (my reading of the look checker's findings, not something I could measure).** The checker found its twins by recognising a knot, a hole, a zigzag crack; plain grain that comes back was not reported, although the numbers say it comes back more often. List the landmarks, paint them out by default and show each only now and then.
5. **Check the things a person cannot see by looking, and count what the notes claim**: that the tile repeats exactly (slide test), that the pipeline adds nothing of its own (source-unchanged test), that touching boards really take different source rows (count the pairs, and count them in the tile as well as in the area), that the first tile of an area is not the default tile, that no part of the picture is squeezed or magnified (measure the local scale of the reading).

---

## 2. When to use a map as source and when to build from nodes only

| Question | Map as source (this job) | Nodes only (the earlier wood recipe) |
|---|---|---|
| Look of one tile | looks like the uploaded wood because it IS the uploaded wood, re-arranged | needs a description of every feature; the best new tile looked washed out and blocky |
| "Same kind" score (0 to 1) | **0.839** (three seeds, round 2); round 1: 0.801 | **0.665** (best of 8 new tiles) |
| Big area that never visibly repeats | the same pieces come back: each used dot of the map appears about **30.7** times in 16 tiles, flipped, stretched, bent and toned differently; recognisable places are painted out and shown about 64 times in all (12 landmarks, 16 tiles) | new content everywhere, nothing is reused |
| Knots, big cracks | come back (only three knots exist in the map), now rarely and in different shapes | drawn fresh, but weak |
| Cost to build | about 1699 nodes, a measuring step for the landmarks | a long analysis and a generator program |
| Needs the map at bake time | yes | no |

**Rule of thumb (guess for other surfaces):** use the map as source when the person values the look of THAT picture and the surface is made of separate pieces (boards, bricks, slates) that can be re-arranged; use nodes only when the surface must be new everywhere and the map is just a guide.

---

## 3. How to cut any map into pieces (the recipe in ten steps, with the wood as the example)

**Example first.** The wood map has five rows of boards separated by dark gaps. Cut the picture from the middle of one gap to the middle of the next and you get four usable "row strips" (the top row is only 155 dots high, so it was not used). A new surface is then built row by row: every board picks one of the four strips, a random start along it, maybe flips it, bends it a little, and shows that window.

1. **Measure the structure** of the map: where the separators are (rows, gaps, joints), where the rare features are (knots), where the stains are, and whether the map wraps (here it does not: the jump across the left-right edge is 4 times a normal jump). Write the numbers down (`research/measurements_wood_source_map.json`).
2. **Cut along the separators, in the middle of them**, and always show a whole strip from separator to separator, so that every edge of the new surface lies on a real separator of the source (here the real gaps keep their small dark pebbles). A cut in the middle of a dark gap is nearly invisible later; a cut at the edge of the gap would put wood against wood.
3. **List the landmarks and where they are, and find clean grain to show instead.** Keep the list short (twelve here). A search for "places with no look-alike elsewhere" did not help on this painted map (every place is about equally unlike every other); choosing by eye from crops of the rows worked. For each landmark a script (`tools/find_landmark_replacements.py`) found the plain place of the map whose ring around it matches best, so the paint-out shows no step.
4. **Lay out the new surface with random numbers made from the position** (the White Noise Texture node in 4D works as a hash: the same inputs always give the same three random numbers). Row number and board number go in; start, flip, stretch, bending, tone and "shows its landmarks?" come out. The same node tree makes a tile that repeats (numbers repeat after one tile) and an area that does not (numbers keep counting up and are salted differently from the tile): one switch.
5. **Give every neighbour a different source row on purpose and count it.** The rule here: the next board takes the next of four rows, and the next row of boards steps by two, so touching boards mostly differ (1 % of touching pairs in the 4 x 4 area do not). With a wrap-around tile the rule needs an EVEN number of rows: with 5 rows the last and first row get the same value and 2 of 3 boards touching across the tile edge take the same source row (found only by counting, after the bakes). No fallback rows: a fallback that "fits any board" is what broke the rule in round 1 (19 percent of touching pairs shared a row).
6. **Hide every cut with something made on purpose, in the material's own style.** Here: a stepped dark ragged crack of random width where two boards meet, a dark band on every row edge that is only added where the source is not already dark (so the real gap rubble stays), partial wedge cracks inside boards. Make the crack wider than the worst mismatch of the cut.
7. **Read all maps at the same position** (build the position once, feed it to every Image Texture node). Colour, height (and anything else) then match by construction, also in the places where a landmark was painted out. Do not read a normal map from a re-arranged picture: a flipped piece would have its slopes pointing the wrong way. Make the normal from the arranged height at the end.
8. **Bend every window a little before reading it** (slow noise, a tilt) so that two uses of the same piece differ in shape; **let the bending die away at the edges that must stay on the separator**, but keep the shift small where it dies away (section 4, trap 12).
9. **Keep the "per dot" amounts the same in a tile and in an area.** Everything that is "at most one per row" needs a "per tile-wide stretch" version for areas.
10. **Check** (section 5).

---

## 4. Traps (what went wrong here, so that nobody repeats it)

1. **Cutting the rows from gap-top to gap-top** put wood against wood at every row boundary: the project's seam measure said "seam" and the picture had no dark gap where the rows met. Cutting from gap-middle to gap-middle and laying a dark band over the boundary fixed it.
2. **Stain stamps taken from the map can contain the knots.** Two of my eight stain stamps contained the biggest knot; the knot came back as a smaller second knot in the same board. Look at every stamp.
3. **"At most one knot per row" in an area is one knot per 4 tiles of row.** Found only because I counted the knots in the 4 x 4 picture.
4. **Two neighbouring boards that take the same source row show the same piece side by side, one of them mirrored.** Round 1 said "never"; the checker counted 19 percent of touching pairs. A written rule is a claim: count it.
5. **Straight joints and short boards read as a brick wall**, whatever the rest looks like. Fewer, longer boards, rows of different heights, joints that step, some joints faint and some strong: that moved the picture from "dry-stone wall" to "log wall" (the look checker's words for round 1, my looking at round 2; section 7.7 of the recipe guide).
6. **Boards cannot be longer than the source row.** Joining two boards into one with a partial crack (round 1) only works up to about 0.7 of a tile; a board longer than the source row would have to show the same piece twice. Do not ask for boards of 1.6 tiles from a map one tile wide.
7. **A distinctive feature repeated three times is noticed; a plain stretch repeated thirty times is not.** The "near copy" tests count both alike; the checker's finding that twins were "plainly the same knot, same hole, same rust cluster" is what led to the landmark list.
8. **A soft cross-fade makes ghosts.** The first paint-out (blending the clean grain over the landmark over a wide ring) left blurred smudges, because the source is crisply painted. A hard ragged edge with a well matched ring looks like the map's own patches.
9. **A search for clean grain can pick the same place for several landmarks, or no place at all.** The first run picked one plain patch for five landmarks and left the rust cloud pointing at the corner of the map (no valid place). Mark each chosen patch as used and check every result by looking.
10. **When the tile edge waves, the wrap needs both signs.** In the first round 2 bake the row edge at the top of the tile could be pushed up or down; I corrected only one direction, so for edges pushed up a thin strip of the wrong source row sat at the bottom edge of the tile. The slide test did not see it (the strip repeats exactly); the project's seam measure did (top-bottom jump 1.3 to 2.1 times a typical jump). Read the project's measures even when your own test passes.
11. **Eight-bit debug pictures carry dither noise**, so board numbers read from a colour debug picture split every board into hundreds of pieces. Read exact numbers from the 16-bit height output.
12. **A big sideways shift that fades out at an edge squeezes the picture there.** A tilt of up to 27 source dots, faded to zero over the last sixth of the row height, magnified the source up to 2 times near the row edges: smeared strips, in 1.6 percent of the 15-dot blocks of the tile. Found by measuring "source dots per picture dot" from the exact position pictures, after the look of the picture had made me suspicious. Cap the shift (8 dots) and measure again (0.0009 of the blocks magnified now).
13. **Relative output paths and the folder Blender is started from:** my round 1 job list wrote into the wrong folder once. The job driver now resolves paths against the recipe folder. (In round 2 a cleanup command with relative paths was started from the wrong folder; it deleted nothing only because the paths did not exist there. Use absolute paths.)
14. **The project's tools can disagree with what you see.** The "same kind" tool punishes a tile whose edge rows differ although the tile repeats exactly (round 2: tiling score 0.75 to 0.93 where round 1 had 1.0; I believe because the real gap rubble is kept at the tile edge and is no longer a uniform band, and I checked that the tile edge jumps no more than the other row boundaries of the same tile; see the recipe guide, section 7.1). Check the real thing (slide the picture by half a tile and compare), and say both numbers.
15. **A control must be exact.** The round 1 shift test control (the map repeated 4 x 4) scored 0.972 because the picture was shrunk to a tile of 313.5 dots and shifted by 313; made with whole dots it scores 1.000. A control that does not reach 1.0 makes the real result look better than it is.
16. **Tools must still run after the pictures are shrunk to save disk space.** Round 1's measuring script wanted a PNG that the shrinking script had deleted. The round 2 scripts read PNG or JPEG and keep the exact pictures.
17. **A mislabelled rule in the research notes:** the uploaded normal map equals the two-neighbour slope of the uploaded height at strength 8 (0.004), NOT a 3 x 3 Sobel filter (0.03). The harness's function named `sobel_normal` is the two-neighbour rule.
18. **Stronger variation lowers the "same kind" score.** Each thing that breaks repetition (stains, large patches, tone, stretch, bending) moves the picture away from the map's own statistics. Choose the amounts on purpose.

---

## 5. What to check on any re-arranged map (all of these were run for the wood)

| Check | What it proves | How it was done and what came out |
|---|---|---|
| **Slide test** | the tile repeats exactly | bake the tile with the whole pattern slid by half a tile; it must equal the normal bake slid by half a tile (mean difference 1e-05 in height, 0.00154 in colour) |
| **Source-unchanged test** | the pipeline (nodes, photograph, normal rule) adds nothing of its own | switch the arrangement off: height must come back (difference 3e-05) and the normal made from it must equal the uploaded normal (0.0039 / 0.0039 / 0.0041) |
| **Seam measure of the project** | no jump across the tile edge | top-bottom jump 1.08 times a typical jump, left-right 1.12 (the uploaded map: 2.76 and 3.97) |
| **Squeeze measure** | no part is magnified or smeared | local "source dots per picture dot" from the exact position pictures; share of blocks under 0.6: 0.0009 |
| **Shift test on a big area** | no hidden repeat at the tile or map width | correlation of the picture with itself slid by one tile: 0.066 for the new 4 x 4 area (background up to 0.117), 1.0 for the plain repeat |
| **Neighbour count** | the written rule "touching boards differ" is true | 1 % of touching pairs take the same source row |
| **Reuse count** | how much of the map is used and how often | the recipe writes "which source dot is this?" as an exact picture; count |
| **Near-copy search** | do pieces come back | the look checker's test: 2 % of the pieces have a twin scoring over 0.7 in the new area, 14 % in the round 1 area (same test, same size, 50 pieces each; with another draw of pieces 0 % and 18 %) |
| **Landmark count** | rare features come back rarely | 64 showings of 12 landmarks in 16 tiles (13 of them knots) |
| **Look at every joint at full size** | no visible cut | a sheet with one full-size crop per joint, found exactly from the board numbers (10 / 12 / 11 crops in the three tiles) |
| **First tile of an area** | not the default tile | correlation 0.049 (round 1: 0.76) |

---

## 6. Which parts carry over to other surfaces (guess, not tested)

* **Brick, slate and plank-like surfaces:** the row and board layout, the per-board random window, the hash from position, the stepped crack that hides cuts, the landmark paint-out and the checks carry over almost unchanged (a brick is a board with other numbers). The slate-in-layers recipe already has a layout; a window-per-brick step could be added to it.
* **Gravel, mud, metal:** no separators to cut along. The research found that blending random shifted copies of the whole map (hex or stochastic tiling) is the method for noise-like surfaces; it was not tried in this job.
* **The checks carry over to every surface**, with or without a map.
* **What does NOT carry over:** the table of row strips, the landmark list and the stain stamp positions are measured on this map only. The measuring scripts (`research/tests/measure_wood_source_map.py`, `tools/find_landmark_replacements.py`) show how to get such numbers for another map.

---

## 7. Not tested, and where I am unsure

* Only the wood was tried. Everything in section 6 is a guess.
* No person has looked at the pictures for this job (the numbers and my own looking are all there is).
* The "same kind" score is a proxy: it rewards staying close to the map's own statistics, which is the opposite of what a big non-repeating area needs; read it together with the repeat tests.
* Seeds 1 to 3 for the tiles, seed 1 for the areas.
* The landmark list was chosen by eye from the four usable rows; other recognisable places certainly remain (I saw dark slits and orange splinters come back in the crops that are not on the list).
