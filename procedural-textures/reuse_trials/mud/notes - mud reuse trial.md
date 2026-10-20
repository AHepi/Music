# Notes - mud reuse trial

What this file is: the plain-words report of the MUD reuse trial. The question was "how much of the tools can be used on the other textures
now?". I answered it for mud by building it: a mud tile made from the shared slate layers (taken unchanged from the frozen snapshot), with
only their settings changed, plus the new parts I could not avoid. Everything is in this folder (`reuse_trials/mud/`, 57 MB). Written on 20 October.

Words used (one word for each thing): **tile** = the square picture that repeats; **dot** = one picture dot; **layer** = one box of the recipe
(COLOUR AND FADE, MOSS and so on); **layout** = the box that tells every layer which piece of the picture each dot is on; **bundle** = the eleven
numbers the layout hands to every layer; **setting** = one named number or colour of a layer; **node** = one small step Blender works out for every
dot (a box is made of hundreds); **seed** = the number that picks one random pattern; **same-kind score** = `lib/texture_compare.py`, "is it the same
kind of surface?" from 0 to 1.

---

## 1. The short answer

**About half of the work carried over, and the half that carried over is the ground and the puddles.** No shared layer was changed (the fingerprints
of all seven files still match, and no cache folder was written into the snapshot).

| what mud needs | which box made it | how |
|---|---|---|
| the crumbly earth ground (flat painted clods, dry and wet areas) | COLOUR AND FADE | **settings only** (the whole ground) |
| the blue-grey puddles | MOSS | **settings only, with a new meaning** (water gathers in the low spots) - but it only works because the new layout hands over a bumpy bare relief with basins |
| the pieces (no bricks or slates in mud) | **new MUD LAYOUT** | ground patches about 80 dots across, plus puddle basins |
| the wheel ruts | **new RUTS layer** | no shared layer draws long winding bands |
| angular stones with a lit side | **new STONES layer** | calls the project's own stone maker (`lib/contrib/stone_tools.py`) unchanged and adds the paint |
| the layers meeting | COMBINE | **settings only** (it stacks six layers through `recipe.stack_order`) |
| the layout numbers' fixed sockets | the layer interface | **unchanged**; every new box is built with it and the bundle fed every layer without change |
| cracks, flakes, edge lines | DAMAGE and OUTLINE AND SHADOW | **no job on mud: tried, then switched off** (section 3) |

So the layered machinery really carried over (interface, COMBINE, the paint layers, the baking and scoring tools), but on mud only two of the four
paint layers found work, and the three new parts are big: 1,144 of the 2,555 nodes.

**Counted in nodes** (counted by building the finished recipe in Blender; `checks/node_counts_default.json`):
- Shared, unchanged: 1,401 nodes (55 percent). That is COLOUR AND FADE 419, MOSS 419, DAMAGE 307, OUTLINE AND SHADOW 216, COMBINE 25 and the
  seamless-noise helper 15. (DAMAGE is 307 here and not the 439 of the slate: its crack and scratch slots are build settings and I set them to 0.)
- New: 1,144 nodes (45 percent). That is MUD LAYOUT 295, RUTS 212 and STONES 637.
- The recipe's own wiring is 10 nodes, copied from the slate recipe.
- Of the 637 STONES nodes, about 498 are made by the borrowed stone maker (3 calls x 166 nodes, the count the surveyor measured for one call; I did
  not count them separately in this run) and about 139 are the paint written for this layer.
- DAMAGE (307) and OUTLINE AND SHADOW (216) are built but switched off. Counting only boxes that do something in the final tile: shared 878 (43 percent),
  new 1,144 (57 percent). If the borrowed stone maker counts as reuse: 1,899 of 2,555 (74 percent), or 68 percent of the working nodes.
- With the shared slate LAYOUT instead of MUD LAYOUT (507 nodes, tried for the look only, see 3.1) the shared share would be 1,908 of 2,767 (69 percent),
  but that layout has no basins, so there would be no puddles.

**Counted in lines of code** (comment lines and empty lines not counted; `line_counts.json`):
- Reused unchanged: 987 lines (the four paint layers, COMBINE and the interface helper; the same 987 as in the brick trial). The slate layout (171 more) is
  imported for the "slate" option but not used in the final tile.
- Borrowed unchanged: 82 lines (the whole of `stone_tools.py`; STONES uses one function in it).
- New boxes: 297 lines (mud layout 81, ruts 98, stones 92, optional height rule 26).
- Recipe wiring: 135 lines, copied from the slate recipe through the brick trial. Settings: 115 lines. Tools and tests: 547 lines.
- So of the code that makes pictures, 77 percent is reused (987 against 297 new).

**How close is it?** At the like-for-like size (1254 dots) the three seed sets score **same-kind 0.497, 0.470 and 0.555, mean 0.507** (colour group mean
0.487). The mud's own earlier small recipe, new tile 101, scored the same way, has **0.391** (colour 0.313). So on this scoring the layered tile is
**above** the earlier recipe's tile. Section 4 has the full table, including a warning about what the score can and cannot tell.

---

## 2. What was reused, and how

| part | how it was used | what it does on mud |
|---|---|---|
| layer interface (`layer_interface.py`) | unchanged | every box, old and new, is built with it; RUTS, STONES, MUD LAYOUT and the height box have exactly the shared sockets |
| COLOUR AND FADE | **settings only** | all of the earth. Nine earth browns (from the stored 16-colour mud palette). Each "clod" is one small flat cell of one brown (the shared layer's mottling cells, made short and roundish with the three "no tongues" settings from the inventory: `fade_direction` 0, `fade_length` = `streak_width` = 0.0065, `mottle_tallness` 1.3), many specks, a little grain, and big pale dry and dark wet areas that cross the patches (`bleach` and `stain`). The per-patch tone spread is nearly off (0.15), the per-patch tint is off, and the top darkening is off, because anything that changes from patch to patch shows as a cut-paper polygon |
| MOSS | **settings only, new meaning** | PUDDLES. The layer's own "damp spots" rule (moss gathers where the bare relief is low) is turned up (`damp_preference` 1.5), coverage 0.71, and everything else that makes moss (drips, joints, lower part, clump noise, fringe, patchiness) is 0. The five moss tones are five water blue-greys. The layout supplies the basins in `base_height`, so the puddle edge is the basin outline: ragged and scalloped for free. `moss.raise` is 0 |
| COMBINE | **settings only** | stacks colour_and_fade, ruts, moss, damage, stones, outline_and_shadow; `tone_blend` 1 (the height is taken from the colour, the way the reference maps were made) |
| DAMAGE | **settings only, switched off** | tried as small dark pebbles (pits), twice (section 3.2). No job on mud, `damage.amount` 0 |
| OUTLINE AND SHADOW | **settings only, switched off** | tried once, switched on (section 3.3). No job on mud, `outline_and_shadow.amount` 0 |
| LAYOUT (slate) | **settings only, tried as an alternative** | 14 rows of 14 pieces, no joints, no chips: worked for the ground, but it has no basins (section 3.1). Not used |
| `lib/contrib/stone_tools.py` | borrowed, unchanged | STONES calls `polygon_stones` three times |
| `lib/bake_harness.py`, `lib/texture_compare.py`, `make_normal.py`, `description_audit.py` | as they are | baking, scoring, the normal map at strength 9 (the mud reference's), the settings check (`settings.json` is 3.7 KB; passes the 8 KB limit) |

**Where the numbers came from** (`measure_reference_once.py`, `reference_measures.json`). I measured the reference once, as a guide only, and traced nothing:
- Colours: the earth, water and stone colours come from the stored 16-colour palette (`recipes/mud/analysis/palette_k16.json` and the palette in
  `fitted_distributions_mud.json`). One earth brown (135, 93, 67) was filled in by hand between two stored ones to make nine even steps.
- Shares of dots: earth 71 percent, stone 18 percent, water 11 percent (nearest stored palette colour, measured from the reference colour picture). I used them
  to set how many puddles and stones to aim for. I did not match them (see section 6: stones are only 8 percent).
- Earth brightness percentiles (5, 25, 50, 75, 95 percent: 36, 59, 76, 85, 117 of 255): used to place `tone_centre` and `streak_contrast`.
- The reference HEIGHT map was read once, only to fit the optional height box: height = 2.45 x (grey - 22) / 255 (the earlier recipe's own analysis found
  (grey - 20) / 108; the same line within the fit error).
- Sizes read from the stored summaries, not measured here: clods about 7 to 14 dots, ruts about 20 dots wide, puddles about 55 to 200 dots across,
  stones 830 per tile with a median of 83 dots of area. No per-stone, per-rut or per-puddle list was read.
- Then I hand-tuned over eight rounds of "look, change a few things, look again". No optimiser. I looked at a score once during tuning (round 6, a
  1254-dot bake of seed set 1: 0.413). Its weak parts (fine-detail measures) is why I made the clods finer afterwards.

---

## 3. What was new, and why

1. **MUD LAYOUT** (`mud_layout.py`, 295 nodes, 81 lines). Mud has no pieces in the picture, so the pieces are PATCHES OF GROUND: a seamless mosaic of
   irregular cells (a jittered grid of 16 x 16 points, each dot belongs to the nearest point, the 9 places around it are searched, place numbers wrap so the
   tile repeats, a slow wobble bends the borders). It hands over all eleven bundle numbers: `local_x` and `local_y` in a frame turned 12 degrees (so the clods
   lean along the ruts), `edge_distance` (distance to the patch border), no gaps (`gap_mask` 0, `piece_mask` 1), and a `base_height` made of level ground with a tiny
   lift per patch and BASINS (a slow seamless noise cut at a line; where it is above the line the ground sinks). The basins are what MOSS turns into puddles.
   - **A mistake found late (round 7):** I first made `local_x` and `local_y` run over one patch width. An irregular patch reaches farther than that from its
     point, so the numbers froze at the box edge and COLOUR AND FADE drew straight-edged blocks and "target" squares inside the patches. At 512 dots this
     looked fine; at true dot size it did not. The box is now two patch widths (`piece_width` and `piece_height` = two average patches), and the blocks are gone.
   - 3.1 **Could the shared slate LAYOUT have done it by settings?** Round 2 tried it (14 x 14 pieces, joints and chips 0, flat relief) for the look only
     (one 512-dot colour view, not scored). The ground came out about the same, because COLOUR AND FADE makes the clods; a few pieces showed as lighter
     rectangles. But the slate layout's bare relief has no basins, so MOSS has nothing to turn into puddles. So the layout had to be new, for the puddles.
2. **RUTS** (`ruts.py`, 212 nodes, 98 lines). A new paint layer with the shared sockets. Two families of straight stripes with WHOLE-number slopes (so they meet
   themselves at the tile edge), bent into S-curves by a slow seamless noise, thinning and ending where a second noise is low. Each rut has a dark band (three
   flat dark earth tones), a darker groove, a paler bank on the lit side (three flat tones) and thin blue-grey wet streaks. The band and groove sink the surface.
3. **STONES** (`stones.py`, 637 nodes, 92 lines). A new paint layer with the shared sockets. It calls `stone_tools.polygon_stones` unchanged (random five-sided
   stones, a flat face for each side, one stone per grid cell) three times: small, medium and a few big stones. It adds the paint (a stone grey from six, a lit face
   one to two greys lighter, a dark ring, a few warm tan stones) and makes the small and medium stones gather into groups: a slow noise read at the middle of
   each stone's own cell switches whole stones off in some regions. The stone maker needs plain numbers, not sockets, so this layer's seed, counts and sizes
   are "build" settings (the Seed socket on its box does nothing; the setting `stones.seed` does).
4. **MUD HEIGHT RULE** (`mud_height_rule.py`, 13 nodes, optional). A copy of the brick trial's height box with the mud numbers. See section 4: it is not needed.

### 3.2 What did not work: DAMAGE as pebbles
MOSS's lichen discs (round pebbles in colonies) and DAMAGE's pits (small round pebbles) were my first answer for stones. They looked like polka dots, not stones
(rounds 2 to 5), and lichen has a hidden rule: it only paints where `edge_distance` is over 0.003 (3.8 dots), so on a layout with small pieces it vanishes. I set
the lichen amount to 0 and tried tiny dark pits as fine speckle (round 7, view C): barely visible. DAMAGE's flakes, cracks and notches are tied to piece edges and
the lower edge of a piece, and mud has no real piece edges. So DAMAGE has no job here.

### 3.3 What did not work: OUTLINE AND SHADOW
Switched on with thin brown settings (round 2) it draws a dark net of lines round every ground patch, like cracked paving. The reference has no such lines.
The inventory said "not useful: mud has no joints" and this confirmed it. A second layout at clod size (7 to 14 dots) would give it edges to draw (and a lit lip, a shadow
band), which might make the clods look lit and shadowed like the reference. I did not try it.

---

## 4. Scores, like for like

Every row below:
- is 1254 dots;
- was scored by `lib/texture_compare.py mud` (the "same kind" score, 0 to 1);
- has its normal map made from the height by `make_normal.py` at strength 9 (the mud reference's).

All scores are in `final_scores.json` (and `final_scores_with_mud_height_rule.json`).

| tile | same-kind (overall) | colour group | height group | normal group | tiling |
|---|---|---|---|---|---|
| **trial, seed set 1** | **0.497** | **0.473** | 0.492 | 0.334 | 0.989 |
| trial, seed set 2 (every seed + 100) | 0.470 | 0.419 | 0.504 | 0.300 | 1.000 |
| trial, seed set 3 (every seed + 200) | 0.555 | 0.570 | 0.543 | 0.305 | 1.000 |
| **trial, mean of the three** | **0.507** | **0.487** | 0.513 | 0.313 | 0.996 |
| trial, mean of the three, with the optional MUD HEIGHT RULE box | 0.522 | 0.487 | 0.553 | 0.329 | 0.996 |
| **baseline: the earlier mud recipe, new tile 101, normal remade at strength 9** | **0.391** | **0.313** | 0.488 | 0.139 | 1.000 |
| the same tile as stored (its own normal map) | 0.407 | 0.313 | 0.488 | 0.247 | 1.000 |

**How to read it.**
- **The layered tile is clearly above the earlier recipe's tile on colour** (0.487 against 0.313; every seed set is higher) **and on normal** (0.313 against
  0.139), a little above on height (0.513 against 0.488; every set is at least 0.004 higher). The surveyor's figure for all eight of the
  earlier recipe's new tiles is 0.383 on average (0.353 to 0.416); I re-scored only tile 101. The baseline loses on normal when its normal is remade by the same
  tool (0.247 stored, 0.139 remade); the trial's normal is made that way too, so the like-for-like row is the 0.391 one.
- **The seed matters a lot:** overall 0.470 to 0.555, colour 0.419 to 0.570. Most of the spread is the colour "feature size" measure (0.08, 0.08 and 0.43). I looked
  at all three seed sets together while tuning (at 512 dots), so none of them is a blind test. The mean is the fair number.
- **The height box is not needed on mud.** On brick COMBINE's built-in height rule (written for slate) was clearly wrong and a new box added 0.12. On mud the box adds only
  0.015 overall (height group 0.513 to 0.553), because the mud reference's rule is close to slate's. The final tiles use COMBINE's own rule; the box stays an option.
  (The colour was copied, not re-baked, for the rule variant; by its code the box changes only the Height output.)
- **Where it is still weak** (measure by measure, mean of the three): the colour "feature size" spectrum (0.20 against the reference's full 1; the earlier tile has 0.00),
  the sharpness of colour edges (0.25), the height spectrum (0.28), the normal tilt (0.19) and normal-height agreement (0.00, same as the earlier tile: my derived
  height cannot be blurred like the reference's). Strong: colour distribution (0.78), height-colour link (0.80), normal components (0.65).
- **What the score cannot tell (the surveyor's warning).** `texture_compare` is weak at telling mud from other surfaces, so every tile was also scored against the other five
  references (the control, `control_overall_against_other_references` in `final_scores.json`):

| tile | against mud | brick | slate | wood | metal | gravel |
|---|---|---|---|---|---|---|
| trial seed set 1 | 0.497 | 0.344 | 0.239 | 0.267 | 0.283 | 0.354 |
| trial seed set 2 | 0.470 | 0.365 | 0.254 | 0.270 | 0.274 | 0.391 |
| trial seed set 3 | 0.555 | 0.365 | 0.237 | 0.281 | 0.281 | 0.363 |
| earlier recipe, tile 101 | 0.391 | 0.325 | 0.369 | 0.250 | 0.334 | 0.337 |

  The trial's mud score is 0.08 to 0.19 above its best other-surface score; the earlier tile's is only 0.02 above (its best other score is slate, 0.369). So the
  layered tile is better told apart from other surfaces. The score still says nothing about whether it looks wet or lit; for that, look at section 6.

---

## 5. Proof tests (all run and measured; files in `checks/`; the 512-dot test pictures were deleted after measuring, to keep the folder small)

- **Half-tile shift test** (512 dots; `checks_run.py` part 1, measured by `checks_analyse.py`; the picture slid by half a tile must equal the plain picture rolled by half).
  Result: **the tile repeats**.
  - Finished colour: average difference 3.7 of 255, and 0.86 percent of dots differ by more than 40; a wrongly rolled control gives 31.0 and 31.8 percent.
  - Ground patches 1.6 / 0.64 percent; bare relief 0.22 / 0; RUTS mask 0.94 / 0.89 percent; MOSS (puddle) mask 0.90 / 1.3 percent; STONES mask 1.2 / 1.8 percent
    (controls for these pictures: mean 8 to 41, share 8 to 35 percent).
  - I checked where the mask differences lie (a plain-Python look at the saved pictures): they are no denser in the 8-dot bands over the old picture edge than
    elsewhere (for example MOSS 1.65 against 1.28 percent, STONES 1.1 against 1.8), so they are scattered one-dot edge differences, not a seam.
  - With 2 tiles across: again it repeats (colour 4.6 / 0.79 percent) and the picture is NOT a copy of itself one base tile over (36.8 / 42.5 percent), so it is new
    content (the half-tile test only; I did not look at or score a 2 x 2 area of new content).
- **Seam score** in the like-for-like bakes: 0.989, 1.000 and 1.000.
- **2 x 2 repeat** (`repeat_2x2_mud.jpg`): I looked. No seam is visible. The repeat of the puddles and the big stones shows, as any one-tile repeat does.
- **Independence test** (320 dots; `checks/checks_tables.md`): each layer's Amount set to 0, and its Seed + 1, with the share of dots that changed outside that layer's own mask.
  - **Colour changed outside the layer's own mask: 0.0 percent for every layer and every row.** Seed + 1 rows were measured against the old mask together with the
    new-seed mask (the brick trial measured against the old mask only, which over-counted). With COLOUR AND FADE and the layout (they paint everywhere) the whole picture
    may change; with Seed + 1 on the layout 70 percent of the colour changes, as it should.
  - Height changed outside the mask on 0.001 to 0.013 percent of dots (RUTS, MOSS and STONES rows). I did not find the cause (it is far below one dot in a thousand; soft mask
    edges below my 0.01 mask cut-off are a likely reason, by reasoning only).
  - **DAMAGE and OUTLINE AND SHADOW are off in the final settings, so their rows are 0 and prove nothing.** MOSS changing with DAMAGE through the declared link was not tested
    (the link has no effect with Damage Avoid and Damage Attract at 0).
- **Snapshot fingerprints**: `sha256sum -c checksums.txt` reports OK for all seven files after all my runs. No cache folder is in the snapshot.

---

## 6. Does it read as mud? (honest)

**Partly. At a glance it is earthy mud: brown crumbly ground, blue-grey puddles, dark stones and winding wheel ruts. Next to the reference it is clearly weaker.**
`sheet_mud.jpg` (reference | earlier recipe | this trial; the same three enlarged; each layer's mask) and `final_seed_sets.jpg` show it.

What reads right:
- The ground (the strongest part): a flat painted mosaic of crumbly clods in the right browns, with dry pale and wet dark areas.
- Puddles with ragged, scalloped edges and two or three flat blue-grey tones; about the right share of the picture (11 to 15 percent against 11).
- Stones with an angular outline and a lit face on the upper left, in groups.
- Ruts as dark winding bands with a groove, a paler bank and blue-grey wet streaks (best seen in the close-ups in `rounds/r8/sheet.jpg`; the main sheet shows them smaller).

What is clearly weaker than the reference:
- **No lit and shadowed clods.** The reference ground looks lit from the upper left, every clod with a bright top and dark underside. Mine is a flat mosaic. COLOUR AND FADE can
  make flat patches but not a lit edge on each one, and OUTLINE AND SHADOW would need a layout with clod-size edges.
- **Ruts are narrow winding trenches, not broad parallel bands.** The reference ruts are about 20 dots of dark band plus banks and shading, in S-shaped groups; mine pinch to a
  thin line where the bend is strong (the bend squeezes the band; I did not correct the width for it).
- **Stones:** 8 percent of the dots against 18 percent in the reference, and the groups are loose. They have thick dark rims and look a little cartoon-like. There are no tiny stones.
- **Puddles** are flat: no darker middle, no ripples, a few faint polygon tone patches inside.
- **The whole tile is sparser and more even** than the reference, which is dense with stones and ruts.
- The earlier recipe's tile has bolder black stones; the layered tile is more mud-like in its ground and ruts.

---

## 7. What is missing to make it better

1. **Lit clods:** a second, small-clod layout (pieces about 7 to 14 dots) run through OUTLINE AND SHADOW with a frame turned so the shadow side is the lower right, or an "edge light" layer.
   Not tried.
2. **Ruts:** correct the band width for the bend (divide by the stripe's slope), make them run in parallel pairs, and darken the clods near them (the earlier recipe's chance table by distance from a rut).
3. **Stones:** more and smaller, gathered round the big ones (the stone maker does not hand out stone positions, so a "round the big ones" rule needs a copy of it); less thick rims.
4. **Water:** a darker middle and a lighter shallow edge; MOSS's `rim_lightening` is there but I left it on a default.
5. **Seeds:** the puddle share changed from 11 to 15 percent and the score from 0.470 to 0.555 with the seed alone. More puddle features per tile would average that out (it also makes puddles smaller).
6. **Clods along the ruts:** one global lean (12 degrees) stands in for "lie along the nearest rut".
7. **Height and normal:** a blur (the reference height has a slight blur, a shader cannot do it) would help normal-height agreement (0.00).

---

## 8. Failures (recorded as they happened)

- **Round 1:** ruts were hairline cracks (a strong bend squeezes a band); MOSS painted hundreds of small blue-grey bits because its edge-raggedness noise alone was above its threshold. Fixed in rounds 2 and 3 (coverage 0.71, `damp_preference` 1.5, raggedness 0.2).
- **Round 2:** OUTLINE AND SHADOW switched on drew a net of dark lines round every patch (section 3.3). The slate layout alternative has no basins (3.1).
- **Round 4, first start:** stopped at once with `KeyError: 'seed'` in `stones.py` (I asked the interface helper for the layer's settings without the shared Seed and Amount controls). No picture was made. Second start worked.
- **Round 5 pictures:** the three seed sets showed the same big stones, because I had left `stones.seed` out of the seed sets. Fixed.
- **Lichen discs and DAMAGE pits as stones** looked like polka dots (3.2).
- **Round 7, first start:** stopped at once (`No module named 'bake_harness'`): my copy of `window_render.py` looked one folder level too high. No picture was made. Second start worked.
- **The layout box mistake** (section 3, item 1): frozen local numbers made straight blocks inside patches; seen only at true dot size, not at 512.
- **Warm tan stones** with a dark rim looked cartoon-like (share cut from 0.08 to 0.05); stones at medium grey (tone offset 1) looked plastic, so the tone bias was lowered.
- **Tuning at 512 dots hid fine-scale flaws.** From round 7 on I used close-up windows at true dot size.
- **The final bake text in `blender_runs.log` says "round 11-prep"**: that was my label for the final bake, which is the eleventh Blender start. The twelfth was the proof checks.

---

## 9. What I did not test, and what I am unsure of

- **The plain harness command** (`blender ... lib/bake_harness.py -- mud_recipe.py OUT --size 1254 --normal-reference mud`) was not run. All bakes went through my own drivers (`run_views.py`, `final_bake.py`, `window_render.py`, `checks_run.py`), which use the harness's scene and photograph functions. The harness's own normal maps were not used.
- **Roughness and metallic** were not compared with anything (the reference has none). Metallic is 0 everywhere; roughness is COMBINE's 0.8 plus each layer's change.
- **Seeds 2 and 3 at true dot size** were only seen at 1254 reduced in the seed sheet and in 512-dot views; the close-ups were of seed set 1.
- **A 2 x 2 area of NEW content** (`recipe.tiles_across` 2): only the half-tile test was run (passes); not looked at, not scored. STONES' slow bend of its grid does not scale with the number of tiles.
- **The independence rows for DAMAGE and OUTLINE** are trivial (off). Whether the shared DAMAGE and OUTLINE still respect their masks on mud was not tested.
- **The mud height rule** was baked as height only; the colour for those scores was copied from the main set.
- **The 498 helper nodes inside STONES** are worked out from the surveyor's count of one call, not counted in this run.
- **Timings** were taken while another helper was baking: a 512-dot view 20 to 28 seconds; at 1254 dots colour 92 to 107 seconds, height 89 to 131, roughness 73 to 94, metallic 2 (about 5 minutes a set).
- **The shared slate LAYOUT alternative** was looked at once at 512 dots, not baked at 1254 and not scored.
- **Unsure:** whether the "settings only" verdict for MOSS is fair. It runs by settings, but only because the new layout supplies basins in `base_height`; with the shared layout it would make no puddles.
- **Unsure:** how much of the score gain over the earlier tile is real mud-likeness and how much is that the earlier tile has large flat shapes the fine-detail measures dislike. The control margin (section 4) says the tile is at least better told apart from other surfaces.

---

## 10. Files in this folder

- **The recipe:** `mud_recipe.py` (loaded by the harness; imports the shared layers ONLY from the snapshot and refuses to run if any came from elsewhere); `settings.json` (all mud settings, 3.7 KB); `final_sets.json` (the three seed sets); `final_bake_sets.json`.
- **New boxes:** `mud_layout.py`, `ruts.py`, `stones.py`, `mud_height_rule.py`.
- **Pictures:** `sheet_mud.jpg` (reference | earlier recipe | this trial, the same three enlarged, each layer's mask), `final_seed_sets.jpg` (the reference and the three seed sets), `repeat_2x2_mud.jpg` (the tile laid 2 x 2). `look/` holds the first look at the reference and the earlier tile and the round 6 whole tile and crop. `rounds/` holds the contact sheet of each tuning round (`sheet.jpg`, made from the views of that round, which were deleted afterwards to save space) and its log.
- **Final bakes:** `final/seeds_1`, `seeds_2`, `seeds_3`: colour, 16-bit height, roughness, metallic, normal (strength 9) and `score.json`. `final/mudrule_seeds_*` hold the height (and score) made with the optional height box. `baseline_tile_101/` holds the earlier tile (copied) and its score.
- **Scores:** `final_scores.json`, `final_scores_with_mud_height_rule.json`, `reference_measures.json`, `line_counts.json`.
- **Tests:** `checks/` (`checks_tables.md`, `half_tile_results.json`, `independence_results.json`, `node_counts_default.json`, `node_counts_with_mud_height_rule.json`, `node_counts_with_shared_slate_layout.json`, `masks/`, `run_log.txt`).
- **Tools:** `run_views.py`, `window_render.py` (a copy of the slate tool with the folder level changed and a per-job window added), `final_bake.py`, `checks_run.py`, `checks_analyse.py`, `final_scores.py`, `make_mud_sheet.py`, `seed_sets_sheet.py`, `look_sheet.py`, `look_numbers.py`, `measure_reference_once.py`, `set_values.py`, `count_lines.py`, `blender_run.sh`.
- `blender_runs.log`: every Blender start. There were **12** (the limit): 9 tuning looks (two of them stopped at once), one 1254-dot test bake, the final bake and the proof checks.

**To bake it again** (from `proc-work`):

`blender -b --disable-autoexec -t 2 --python reuse_trials/mud/final_bake.py -- reuse_trials/mud/final 1254 '{"seeds_1": {}}'`

then `python3 -I reuse_trials/mud/final_scores.py`.
