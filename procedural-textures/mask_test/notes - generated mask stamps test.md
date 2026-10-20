# Generated mask stamps test - notes (20 October 2026)

Plain note: this file is for a person who is not a programmer. It says what was tried, what it cost, what the pictures showed, and what is still unknown.
A few words first. A "mask" is a black-and-white picture that says WHERE something is painted (white = paint here). A "stamp" is one separate shape (one clump of moss,
one chip) cut out of a picture, so it can be pressed onto the surface many times, turned and resized. An "atlas" is one picture holding a grid of equal cells with one
stamp in each cell. A "layer" is one part of the slate recipe (colour and fade, damage, moss, outline) that makes its own colour, height and roughness.

## The short answer (read this first)
- The idea works as machinery: a generated picture of separate shapes can become the "where" of the moss layer and of the chipped lower edges, per slate, with random
  choice, turn, size and mirror from the layer's own seed, and the tile still repeats without a seam (proved, see section 5). The layer keeps its own colour, height and roughness.
- But in THIS test the generated shapes did not make the slate look better than the node-made masks. By the look measures the four versions are within noise of each other
  (same-kind score 0.778 node-made; 0.783 moss stamps; 0.770 chip stamps; 0.775 both), and by eye the stamp moss was smoother-edged and the stamp chips were a tidier,
  more even pale rim than the reference's lumpy chips. Section 4 says where each was better or worse and why.
- Cost: six pictures, US$0.354 by the price list (at most US$0.45 if every picture is counted at a rounded-up price). The limit was US$1.00.
- Eight Blender runs were used (budget about 12). Nothing in `lib/`, `reference/`, `recipes/` or the film repository was changed.

## 1. What was generated, and what it cost
Model: `fal-ai/flux/dev` (a text-to-image model), 1536 x 1536 dots, price US$0.025 per megapixel = US$0.059 per picture. Full ledger with prompts: `spending.md`.
Originals are in `stamps/originals/`; the sheet `sheets/generated_originals.jpg` shows every original next to the mask made from it.

| # | picture | what I asked for | what came back | usable? |
|---|---|---|---|---|
| 1 | moss A (seed 4101) | separate soft mottled moss clumps, drips, white on black | 16 round fuzzy green clumps with short drips, on black | yes, as silhouettes (round, all alike) |
| 2 | chips A (seed 4102) | separate flaked-edge chips with a flat lower side and toothed upper edge | 16 chunky cream flakes with pitted rims, on black | shape poor (blocky), not used in the comparison |
| 3 | moss B (seed 4103) | flat tall ragged moss stains with drips | 16 ink-splat shapes with drips, on a CREAM ground (not black) | yes, cleaned by "how different from the ground" |
| 4 | chips B (seed 4104) | thin long strips of chips | 16 squarish cream paper pieces (it ignored "thin strips") | shape poor, not used |
| 5 | chips C (seed 4105) | long thin strips stacked in rows | five long ragged cream strips (photographic, plaster-like) | yes, after cutting each strip into short pieces (20 stamps) |
| 6 | moss C (seed 4106) | moss hanging from a straight top edge with long drips | 16 hanging "curtains": a solid band that breaks into long thin drips, but hung on a brown rod and with a red scribble | yes, after removing the rod and the scribble by colour and shape |

Total: 6 x US$0.059 = US$0.354 exact by the price list; counted at 3 megapixels each (rounded up) US$0.45. Limit US$1.00. I stopped at six pictures. I did not read the real
account balance, so the figure is from the price list.
None of the six pictures is in the hand-painted style of the slate reference (they came out as game-style vector blobs, ink splats and photographed plaster): only their
SHAPES (silhouettes) were used, never their colours.

## 2. From pictures to stamps (cleaning and atlases)
Script: `tools/make_stamps.py` (run with `python3 -I`). Steps: find the background colour (black, or cream for sheet B); turn "how different from the background" into a soft
mask; remove specks smaller than about 60 dots; join drips and flecks to their clump by growing the mask 7 to 9 dots; cut each clump out; fit it into one cell
(moss: top edge of the clump on the top of the cell so it can hang from a slate's upper edge; chips: bottom of the piece on the bottom of the cell so it can sit on a lower edge);
soften the edge by about one dot; also store "how far inside the shape" in the green channel. Sheet C needed two extra steps: only green dots were kept (this removed
the brown rod and the red scribble) and a thin-bar filter removed what was left of the rod; the long chip strips were cut into short pieces and the cut ends faded out.

| atlas | file in `stamps/atlas/` | stamps | cell size (dots) | grid | picture size | used in the comparison? |
|---|---|---|---|---|---|---|
| moss C (hanging drips) | `moss_C_atlas.png` / `.json` | 16 | 256 x 256 | 4 x 4 | 1024 x 1024 | yes |
| moss A + B (round clumps and splats) | `moss_AB_atlas.png` | 32 | 256 x 256 | 4 x 8 | 1024 x 2048 | only at 640 dots, first trial |
| chips C (cut strips) | `chips_C_atlas.png` | 20 (4 cells empty) | 300 x 120 | 4 x 6 | 1200 x 720 | yes |
| chips A, chips B | `chips_A_atlas.png`, `chips_B_atlas.png` | 16 each | 256 x 256 | 4 x 4 | 1024 x 1024 | no (poor shapes) |
Look at them: `sheets/stamp_atlases.jpg`. Each atlas has a `.json` file next to it that says the cell size, grid and count; the recipe reads that file.

## 3. How the stamps plug into a layer
New file `slate_copy/layers/stamps.py` (the helper) and small additions in the copies of `moss.py` and `damage.py` (`slate_copy/changes_moss.diff`, `changes_damage.diff` list every change;
every other file is byte for byte the original; the copy was made at 13:12 UTC with checksums in `slate_copy/COPIED_FROM_SLATE_checksums.txt`).

A setting chooses the mask: `moss.mask_mode` and `damage.mask_mode` = `nodes` (the old node-made mask; the old picture exactly), `stamps` (the stamp mask only) or `both`
(node mask times stamp mask: a dot is painted only where both say yes).

A concrete example, moss on one slate. The slate has its own random numbers (from its piece number and the moss layer's Seed). They say, for each of four "slots":
is this slot used on this slate (a chance), where along the slate, how big, how far turned (up to 25 degrees either way), mirrored or not, and which of the 16 stamps.
- two slots hang from the slate's own upper edge (the chance follows the layer's Drip Preference),
- one sits on a side joint (follows Joint Preference),
- one sits low on the slate (follows Lower Part Preference).
Every slot's chance is also multiplied by the layer's own "big mossy areas" gate and the slate's own mossiness, so the layer's own rules still decide WHERE moss tends to be.
At every dot the layer works out where that dot lies inside each stamp (its place on the slate, minus the stamp's centre, turned, divided by the stamp's size), reads the atlas
picture there, and takes the largest value. That is the moss mask. The moss colour (five olive tones, streaks), height (+raise, fuzz) and roughness are still made by the
layer's own nodes from that mask. Chips work the same way with six slots (four along the lower edge, one at each lower corner) and use the slate's real chipped edge distance
for "height above the edge".

New controls (all in the layer, like every other control): Stamp Amount, Stamp Width, Stamp Turn, Stamp Overhang (how much hangs past the slate edge and is cut off), Stamp Edge Softness.
Settings used in the comparison (`compare/variant_settings.json`): moss C atlas, width 0.12 tile (150 dots), amount 0.85; chips C atlas, width 0.045 tile (56 dots), amount 0.8.
I chose the amounts at 640 dots so that the share of olive dots (3.8 %) and tan dots (1.07 %) matched the node-made picture (4.0 % and 1.19 %): then the comparison is about SHAPE, not amount.
Limits of this first version: only the lower-edge flakes of DAMAGE are stamped (pits, scratches, cracks, notches, corner breaks, and the side-edge flakes stay node-made); lichen discs stay node-made;
moss stamps ignore the "damp spot" rule.

## 4. The comparison at 1254 dots (same settings and seeds in all versions)
Versions (folders in `compare/`, each with `colour.png`, `height.png`, `normal.png`): 1 node-made (the copy unchanged); 2 moss from stamps; 3 chips from stamps; 4 both from stamps;
5 node mask times stamp mask for both layers (extra, one setting only, not calibrated). Bake time for colour plus height at 1254 dots with other helpers running: 309, 354, 327, 459, 477 seconds.
(The stamp versions take longer; I cannot say how much of that is the stamps and how much is other helpers baking at the same time.)

Look measures (`measure_look.py`; the reference column is the person's picture):
| picture | gradient | stripiness | olive % | tan % | moss spread | largest moss clump | brightest slate | slate spread | tilt p99 | up-down slope | side slope |
|---|---|---|---|---|---|---|---|---|---|---|---|
| reference | 5.55 | 0.827 | 6.4 | 1.00 | 6.03 | 7013 | 34.6 | 2.51 | 112.6 | 13.47 | 15.57 |
| 1 node-made | 7.54 | 0.984 | 4.0 | 1.19 | 5.63 | 8439 | 34.1 | 2.65 | 103.5 | 10.60 | 14.17 |
| 2 moss stamps | 7.40 | 0.995 | 3.8 | 1.18 | 5.45 | 5568 | 34.1 | 2.55 | 103.5 | 10.40 | 14.17 |
| 3 chip stamps | 7.54 | 0.840 | 4.1 | 1.07 | 6.39 | 8480 | 34.7 | 2.64 | 103.9 | 10.57 | 14.07 |
| 4 both stamps | 7.40 | 0.850 | 3.9 | 1.06 | 6.31 | 5568 | 34.7 | 2.54 | 103.9 | 10.37 | 14.07 |
| 5 node x stamp | 7.29 | 0.966 | 3.5 | 0.35 | 5.23 | 8340 | 34.1 | 2.61 | 102.8 | 10.38 | 14.05 |

Same-kind score against the slate reference (`lib/texture_compare.py`; 0 = as different as another surface, 1 = indistinguishable):
| version | overall | colour | height | normal | tiling |
|---|---|---|---|---|---|
| 1 node-made | 0.778 | 0.822 | 0.735 | 0.616 | 1.000 |
| 2 moss stamps | 0.783 | 0.830 | 0.739 | 0.615 | 1.000 |
| 3 chip stamps | 0.770 | 0.812 | 0.729 | 0.604 | 1.000 |
| 4 both stamps | 0.775 | 0.819 | 0.734 | 0.604 | 1.000 |
| 5 node x stamp | 0.777 | 0.814 | 0.738 | 0.624 | 1.000 |

What the numbers say, in plain words:
- The overall scores differ by at most 0.013. The slate tuners found (README, round 14) that changing only the seed moves the score by about 0.005 to 0.011, so these differences are about
  the size of ordinary seed-to-seed noise. I did not measure the seed spread myself in this test, so "no real difference" is my reading, not a proven fact.
- Stripiness (how much more upright than level the edges are): the chip stamps pull it from 0.984 down to 0.84 (reference 0.827): clearly closer. The node-made chips have many fine upright teeth; the stamp chips have a smoother, more level top edge.
- Largest moss clump: node-made is 20 % bigger than the reference, moss stamps 21 % smaller: equally far off, in opposite directions.
- Gradient (how busy the fine texture is): all versions are about 30 to 36 % busier than the reference; the stamp versions are a hair calmer. Relief numbers (tilt, slopes) did not change: moss and chips are small parts of the relief.
- Moss spread rose to 6.3 to 6.4 in versions 3 and 4 only because pale chip edges are counted as "olive" by the measure; the moss itself did not change in version 3. Treat that number with care.
- Version 5 (multiplying node mask and stamp mask) lost most of the chips (tan 0.35 %): multiplying two masks only keeps where both agree, so it needs a much higher amount on both. Not calibrated, so I do not judge it.

What I saw (looked at every sheet at 1:1 and twice size: `sheets/masks_compare.jpg` = reference | node-made | stamps, full tile and 400 x 400 crops; `sheets/masks_compare_all_versions.jpg` = all six):
- MOSS. Reference moss is grainy olive and yellow-green blotches with many tiny torn edges and speckles. Node-made moss is streaky olive washes with fine ragged brush edges. Stamp moss
  hangs neatly from the upper edge of slates and has long thin drips that the node version does not have, but the bodies are smooth-edged soft washes, there are fewer separate clumps, and the shapes
  look generic. By eye I rate the stamp moss slightly WORSE than the node-made moss, with the drips as its one plus.
- CHIPS. Reference chips are lumpy cream islands, some floating just above the lower edge. Node-made chips are a thin broken tan rim with many small teeth. Stamp chips are a broader, more even
  pale rim with a wavy upper edge: neater and closer to the reference in thickness, but too continuous (it reads like a strip of frosting), and no loose islands. A toss-up; neither is close.
- The first stamp bake had L-shaped chips climbing the side joints (see 7, failures); that is fixed in all the pictures shown here.

Why the stamps did not win: (1) the generator gave generic silhouettes (round blobs, curtains, plaster strips) with none of the torn, brush-stroke edge of the reference; (2) once a shape is
clipped by the slate and coloured by the layer's own tones, the layer's colour streaks and tone patches dominate what the eye sees; (3) 16 to 20 stamps repeated with random turn and size still look related;
(4) the node-made masks were already tuned over many rounds against this reference, the stamps were tuned for one hour. So this is a fair first look, not a final verdict on the idea.

## 5. Proofs that the stamp mode behaves (512 dots, `sheets/half_tile_test.jpg`, `work/half_tile_results.json`)
- SEAMLESS (half-tile shift test). The recipe slides the pattern by half a tile; the slid picture must equal the unslid picture rolled by half a picture. Stamps lie across the tile edge (61 separate
  moss mask pieces and 6 chip pieces touch the picture edge; 9324 and 2481 mask dots lie within 40 dots of it). Result: moss mask, chip mask and finished colour (slid by half a tile both ways, and by a quarter
  and three eighths) all agree. Plain differences exist on sharp edges because the renderer takes only 4 samples per dot with a random jiggle; the node-made control (original behaviour) shows exactly the
  same level (mean difference 0.0064 for the stamps version and 0.0065 for the control). After a gentle blur removes that jiggle: finished colour largest difference 0.033 (stamps) against 0.028 (control), 0 dots over
  the limit along the old tile edge; moss mask 0.062; chip mask 0.10, with 0 dots over the limit along the old tile edge. My first look at the raw numbers showed more differing dots along the old moss tile edge
  (7.7 % against 3.3 % elsewhere); the picture of the differences (`work/half_moss_seam.png`) showed only edge speckle on thin drips and no cut-off, and the blurred test confirmed it. That is why the blurred numbers are the ones to trust.
- INDEPENDENCE. Changing only the moss seed (31 to 32) changes 25 % of the moss mask dots and 0.0 % of the chip mask. Changing only the damage seed (21 to 22) changes 4.2 % of the chip mask dots.
- OFF SWITCH. Amount 0 gives a mask of exactly 0 for the moss stamps and the chip stamps.
- UNCHANGED COPY. With `mask_mode` at its default the copy equals the original slate recipe: 0 dots differ in colour and height at 512 dots.

## 6. What it would take to use this on other surfaces
- The stamp helper needs only what every layer already gets: the slate's own coordinates (the "layout bundle": piece number, place across, distance from the upper edge, distance from the nearest edge).
  Brick, wood planks or tiles that produce the same bundle can use `stamps.py` as it is. Steps: copy `stamps.py` beside the shared layers, add a mask mode and the five controls to the layer, say which slots
  follow which of the layer's rules (what hangs from where), calibrate the amounts so the share of area matches.
- New shapes need a new paid generation (about US$0.06 for a 1536 dot sheet at this price). A new seed only rearranges stamps. For a surface with a different look (rust blooms, mud splashes, stains) the prompt
  and the cleaning thresholds change; each new kind of sheet cost me one to three tries (six pictures gave three usable moss sheets and one usable chip sheet).
- To get shapes closer to a painted reference, the next thing to try is generating FROM the reference picture (an image-to-image model that gets a crop of the reference as input) so the brush-stroke
  edges carry over. I did not try this.
- The same machinery can drive roughness instead of colour: every layer already hands the recipe a "roughness change". A layer whose stamps are puddle and damp shapes and whose roughness change is negative
  (smoother) would be a way to make wet patches for the street-view surfaces. This is an idea only; nothing wet was tested.

## 7. Failures, dead ends and what I am unsure of
- Round "fluffy balls": the first moss prompt gave round bushes; stamps cut from round shapes read as polka dots at 640 dots (first debug bake). Fixed by trying a different prompt (moss C) and wider stamps.
- Chips B ignored "thin strips" (got squares); chips A gave chunky blocks. Both kept in `stamps/` but not used.
- Moss C came with a brown rod and a red scribble. Removed by colour and a thin-bar filter; I looked at all 16 cells of the moss C atlas at reduced size and saw no rod, but did not check them dot by dot.
- First chip stamps formed L shapes (a leg up each side joint): "height above the edge" was measured with the nearest-edge distance, which near a side joint is the side distance. Fixed by using the straight
  distance from the lower edge near the sides. Near a lower corner the real edge and the straight line can differ (the slates' bottom edges slope; I estimate by up to about 15 dots, not measured), so a corner chip can float or sink a few dots; I did not inspect corners closely.
- The raw half-tile numbers looked like a seam at first (section 5) and were not.
- Unsure: whether the overall verdict would change with better shapes, more stamps (16 to 20 is few), or a different seed set. I looked at one seed set only.
- Unsure: the true account cost (price list only).

## 8. What was NOT tested
- Other surfaces (brick, wood, metal, mud, gravel); a 2 x 2 area of new slates (`recipe.tiles_across` 2) or 2508 dots with stamps; the half-tile test at 1254 dots (done at 512 as asked).
- Roughness and normal maps of the stamp versions were not looked at (colour and height were baked; the normal was made from the height and scored).
- Any seed other than the default one; the spread of the scores over seeds.
- The `both` (multiplied) mode was baked once, uncalibrated; the multiplied mode for moss alone was seen only at 640 dots.
- Moss atlas A + B (round clumps) at full size; image-to-image generation; GPU baking; stamp sweeps (what each new control does over its range).
- Moss avoiding chips (the declared link) in stamp mode was not examined.

## 9. Where things are (folder `mask_test/`)
| item | where |
|---|---|
| this note, the money ledger | `notes - generated mask stamps test.md`, `spending.md` |
| the six originals and the cleaned masks | `stamps/originals/`, `stamps/cleaned/` |
| atlases and their size files | `stamps/atlas/` |
| the slate copy (stamp mode) | `slate_copy/` (start with `CHANGES_IN_THE_COPY.md`) |
| baked versions 1 to 5, measures, scores | `compare/` (`measures.json`, `measures_table.md`, one folder per version) |
| pictures | `sheets/masks_compare.jpg`, `sheets/masks_compare_all_versions.jpg`, `sheets/stamp_atlases.jpg`, `sheets/generated_originals.jpg`, `sheets/half_tile_test.jpg` |
| scripts | `tools/` (`make_stamps.py`, `bake_jobs.py`, `compare_variants.py`, `half_tile_check.py`, `make_stamp_sheets.py`) |
| trial bakes and checks | `work/` |
| the structured result | `result.json` |
To bake one version again: `blender -b --disable-autoexec -t 2 --python tools/bake_jobs.py -- JOBS.json` (a jobs file such as `work/jobs_finalA.json`), then `python3 -I tools/compare_variants.py`.
