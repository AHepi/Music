# Recipe - the ground layers (dirt, cracks, moss, iron) - how they are made

Written in plain words by the ground builder. Code: `kits/weathering/ground/`. Numbers are from the last round of drawing on the rented machine (round 7), street set.
Where something does not pass its line, it says so. The list of what is not finished is at the end.

## What there is

Four layers, each a node group that goes into the ground (and iron) materials of the set, on top of what the kit already does. They read only the kit's standard masks by name, so they work on any set. Nothing in the code names a street, a house or a lamp.

| layer (group name) | slot | what it adds |
|---|---|---|
| dirt (`WK GROUND DIRT`) | A | an even dust, a patchy dirt film, polish on the worn lanes, dried water marks, rust halos where an iron foot stands, a rust ring round a fire drum, tar patches (new, black and glossy; old, grey and matt; with pale chippings), tar splashes at the kerb foot, scrubbed doorstep strips |
| cracks (`WK GROUND CRACKS`) | B (after the wet layer and the joints layer) | fine and broken cracks in flags, tilted flags, chipped flag corners, kerb chips along the arris, open kerb joints, cracked kerb stones, scuffs, disturbed setts (tilted, sunk, missing), open sett joints |
| moss (`WK GROUND MOSS`) | C | moss ribbons in the joints (gutter side first), soft moss patches on open ground (for sets without joints), algae fans under downpipe feet, liverwort at a pipe foot, a far band along the gutter seam and wall foot where the 3D pieces have stopped |
| iron (`WK IRON`) | A, straight before the Principled BSDF on materials with no water layer | rust at the foot (chipped paint, ragged top edge), rust collars every 1.9 m with a rust run below, a dark wet streak at a pipe shoe, a rust ring at a post base, drum rust, heat scale, a soot rim and soot runs, a thin even soot on all iron |

Every layer has the amount dial. At amount 0 every effect factor is a product with the amount, so the layer gives back exactly what it was given (checked, see "What was tested").

## How an element is made (the short version)

- **Marks have a width in plate dots.** A crack, a chip or a moss ribbon is drawn at a real width (3 mm for a crack) but never narrower than the number of plate dots the painter can still keep (3.5 dots for a crack). The kit's `WK MARK WIDTH` turns metres into dots for the camera. Far away the fine detail fades to its average tone, never to clean.
- **Which dot is which stone.** The kit's pictures of the stones (joint, cavity, cell) are read by the layers' own picture nodes (the kit's own `tx` masks give one flat value per tile on setts and flags). Flags get their random numbers from a flag-sized cell of the world grid; setts from the stone's cell number.
- **Cracks** are the edges of a bent Voronoi pattern (distance to the nearest edge in metres), thinned by a slow gate so a crack is a few segments that narrow to a point. Only the chosen flags carry one; chosen flags are picked by a random number per cell and the dial for the share, with more of them near the kerb and the seams.
- **Shares** (how many flags, how much tar, how much moss) go through `thr(share, detail)`: the node group turns a share into a noise threshold from a table measured on the rented machine (the noise value above which exactly that share of a noise field lies), so a dial that says 10 percent covers about 10 percent.
- **Dull.** A crack, a chip or an open joint cuts the shine and the water film a little (narrow marks), a sunk or tilted stone cuts the clear coat much more (wide patches). This keeps the joints test from being fooled by a bright crack in a wet joint.
- **Relief.** A small height (a few mm) goes through a Bump node and is faded with distance; the `relief` dial (0 or 1) switches it.
- **Which element goes on which surface** is the set's business, not the layer's: the set's ground section (`ground_sets/<set id>.json`, key `role_dials`) gives every role a multiplier for each element dial. A multiplier of 0 for all dials of an element on every role that uses a material drops the element from the group built for that material (smaller shader). The multipliers are written on the objects as `wk_<layer>_<dial>` custom properties by a kit service (so they come back after `kit.remove()`).
- **Rings** (`rings` in the ground section): objects of the named roles (the fire drum) get a rust ring painted on the ground round their footprint, from three stored numbers per object.

## The main dials (what they do)

The sheet "25 Ground - what each main dial does" draws each of them at lowest, default and highest. In short:

- dirt: `film` (how much of the ground has the grime skin), `film_darkness`, `dust` (the even part that stays at every distance), `polish`, `water_marks`, `rust_halo`, `drum_ring`, `tar_patches`, `tar_max_share`, `tar_splash`, `scrub_strip`.
- cracks: `flag_cracks`, `flag_fine_share`, `flag_broken_share`, `flag_tilt_share`, `corner_chip_share`, `kerb_chips`, `kerb_chip_share`, `sett_disturb`, `sett_disturbed_share`, `open_joint_share`, `crack_dots`, `crack_contrast`, `near_only`, `max_contrast`, `dull`.
- moss: `joint_share`, `shade_bias`, `ribbon_dots`, `algae_fan`, `liverwort`, `far_band`, `patch_moss`, `moss_value`, `moss_lift`.
- iron: `rust_cover`, `rust_height`, `collar_rust`, `shoe_streak`, `base_ring`, `drum_rust`, `heat_scale`, `soot_halo`, `paint_keep`, `rust_bright`, `grime_dark`.

The values of the plan's Appendix A are the defaults of the kit and are listed in the look file (`presets/sooty_1926.json`), which wins over a default written by the layers. The finer dials I added (all with a range and a sentence in `dials_ground.py`) are not in the look file, so they use their own defaults. Debug: the dial `show_part` picks one named part of a layer for its Mask output (numbers in `ground_names.py`), and the views `layer:<key>` show it in plain light.

## Using it on another set

1. Write the ground section for the set (see `ground_sets/japanese_courtyard.json`, 10 lines): `role_dials` says which role gets which element (the courtyard: dirt and moss patches on gravel, earth and natural stone; no cracks and no iron, because those roles are empty there, and the self-test says "no roles" and skips them).
2. Optionally `readable` (the P3 rows), `period` (the share caps, for `measure_period_ground.py`), `dial_sheet` (the rows of the dial sheet).
3. Nothing else: `harness/layers.py` finds `ground/apply_ground.py` and calls `register(kit)`.

## What was tested (street set, rented machine, round 7) - plain numbers

Round 7 is the last full round (rounds 6 and 7 gave the same numbers except the drawing time and the algae). The files are in the work folder: `measures_r7.json` (everything below), `period_r6.json` and `period_r7.json` (the shares), `selftest_ground.json` (the self-tests).

### Sett joints (P1) - nearly met

21 of 22 lighting pictures pass with the kit's own dots left in (the frozen baseline: 20 of 22). The one that fails is the heavy-rain lockout picture (it failed before as well). 20 pass with every dot counted. With the kit's own dots left out as well, 19 pass; the line asks for the baseline's 20, so that line is NOT met (the verdict says `without_kit_equals_base: False`). The highest joint contrast next to the camera is 0.622 (limit 0.75). The 22 pictures:

| picture | near contrast / delta / seen | middle contrast / delta / seen | kit dots (share) | official | every dot | kit dots out |
|---|---|---|---|---|---|---|
| main_A_dry | 0.465 / 0.0524 / 0.999 | 0.354 / 0.041 / 0.975 | 0.361 | pass | pass | pass |
| main_A_wet | 0.534 / 0.1197 / 0.985 | 0.401 / 0.0843 / 0.906 | 0.361 | pass | pass | pass |
| main_A_heavy | 0.473 / 0.0927 / 0.977 | 0.37 / 0.0801 / 0.887 | 0.361 | pass | pass | pass |
| main_C_dry | 0.413 / 0.0567 / 0.959 | 0.313 / 0.0423 / 0.912 | 0.361 | pass | pass | pass |
| main_C_wet | 0.494 / 0.1803 / 0.99 | 0.405 / 0.1549 / 0.928 | 0.361 | pass | pass | pass |
| main_D_dry | 0.435 / 0.0716 / 0.999 | 0.338 / 0.0553 / 0.979 | 0.361 | pass | pass | pass |
| main_D_wet | 0.449 / 0.112 / 0.979 | 0.315 / 0.0737 / 0.829 | 0.361 | pass | pass | pass |
| main_E_dry | 0.398 / 0.053 / 0.915 | 0.31 / 0.0436 / 0.923 | 0.361 | pass | pass | pass |
| main_E_wet | 0.551 / 0.2502 / 0.943 | 0.402 / 0.2118 / 0.871 | 0.361 | pass | pass | pass |
| main_E_heavy | 0.514 / 0.2476 / 0.915 | 0.402 / 0.2413 / 0.88 | 0.361 | pass | pass | pass |
| close_A_dry | 0.584 / 0.0662 / 0.997 | 0.511 / 0.0578 / 0.998 | 0.297 | pass | pass | pass |
| close_A_wet | 0.622 / 0.1809 / 0.998 | 0.544 / 0.1981 / 0.998 | 0.297 | pass | pass | pass |
| close_A_heavy | 0.608 / 0.1774 / 0.998 | 0.52 / 0.1953 / 0.997 | 0.297 | pass | pass | pass |
| close_C_wet | 0.593 / 0.1784 / 0.996 | 0.518 / 0.1996 / 0.994 | 0.297 | pass | pass | pass |
| close_D_wet | 0.556 / 0.1774 / 0.997 | 0.485 / 0.1913 / 0.997 | 0.297 | pass | pass | pass |
| close_E_wet | 0.61 / 0.2125 / 0.965 | 0.535 / 0.2524 / 0.974 | 0.297 | pass | pass | pass |
| lockout_B_dry | 0.311 / 0.0654 / 0.78 | 0.092 / 0.042 / 0.38 | 0.294 | pass | pass | pass |
| lockout_B_wet | 0.407 / 0.165 / 0.841 | 0.082 / 0.0252 / 0.318 | 0.294 | pass | fail | fail |
| lockout_B_heavy | 0.3 / 0.194 / 0.69 | 0.043 / 0.0122 / 0.212 | 0.294 | FAIL | fail | fail |
| lockout_C_wet | 0.504 / 0.1028 / 0.987 | 0.298 / 0.0679 / 0.796 | 0.294 | pass | pass | pass |
| lockout_D_wet | 0.417 / 0.0876 / 0.971 | 0.205 / 0.0404 / 0.605 | 0.294 | pass | pass | pass |
| lockout_E_wet | 0.428 / 0.2029 / 0.841 | 0.108 / 0.0687 / 0.353 | 0.294 | pass | pass | fail |

### Wet look (P2) - NOT met

The road's wet-to-dry ratio is within 0.05 of the baseline in 11 of 16 pictures and outside it in 5 (for example 3.387 against 3.665 in the strongest light, 2.487 against 2.581 in the close picture). Pavement and kerb are inside. The first round had 6 road pictures outside; halving the dulling brought it to 5, and I stopped there. On top of that, the line that asks each element's own dots to be no brighter wet than dry fails for all four layers (ratios from 1.0 to 3.5, 40 lines). One more line fails that I cannot explain: the highlight share of the main picture in light C (0.0347 against the 85 to 115 percent window). Total lines failing in P2: 44.

### Readable at the painter's size (P3) - NOT met, except two rows

(Measured on each element's own part picture at the painter's scale 0.45, then 0.40: at least 60 percent of the marks GOOD, at most 15 percent LOST, at most 15 percent crushed, and the minimum number of GOOD marks.)

- All crack parts together (the foundation's row, first 15 m): main 110 marks, 26 good (24 percent), 58 lost (53 percent); lockout 124 marks, 17 good (14 percent); notice 139 marks, 75 good (54 percent), 43 lost (31 percent). FAIL on all three plates; the notice plate is the closest.
- Flag cracks (fine and broken) alone: no marks at all on the main and lockout plates (the flags in view within 15 m are too few and too small for a period share of cracks to land on them), 14 marks on the notice plate, 2 good. Tilted flags and chipped corners: none on any plate. This is what the plates can show with the period caps kept; the close views show them.
- Kerb chips, open kerb joints: passes on the notice plate (15 marks, 13 good), main 0 marks, lockout 2 marks.
- Disturbed setts and open sett joints: main 110 marks, 26 good; the soft sunk patches are the lost ones.
- Tar: passes on the notice plate (1 patch, good); main 2 marks, 1 good; lockout 2 marks, 0 good.
- Film, polish and water marks (tone only): main 680 marks, 59 good. The film and polish are broad soft tone shifts and the measure counts them as lost, so this row cannot pass by design: read it as "tone present".
- Rust halos, drum ring, scrubbed strips: 3 to 10 marks per plate, 0 to 3 good (need 4).
- Moss ribbons and algae: main 67 marks, 4 good (need 8); lockout 1 good (need 4); notice 11 good.
- Rust on iron: 0 marks on the main and lockout plates, 2 (none good) on the notice plate (need 4). The rust shows in the close views; on the plates the iron is small.

### Period caps (P4) - inside, with two exceptions

Counted on plan pictures from straight above (`period_r6.json`, 2 cm per dot):

| element | measured | cap |
|---|---|---|
| flags with fine cracks (share of flag area) | 10.4 % | 8 to 15 % |
| flags with broken cracks | 2.5 % | 2 to 4 % |
| tilted flags | 3.2 % | 3 to 6 % |
| kerb chips (share of kerb length) | 31 % | 20 to 35 % |
| setts disturbed (share of road area) | 4.9 % | 3 to 6 % |
| open sett joints (share of joint area) | 15.7 % | 10 to 20 % |
| tar (share of the road) | 0.7 % | at most 4 % |
| tar patches in the first 30 m | 2 | 1 to 3 |
| moss in kerb and gutter joints (share of joint length) | 10.6 % | 5 to 15 % |
| moss in road joints / in pavement joints (any joint length at most 15 %) | 11.7 % / 10.9 % | at most 15 % |
| liverwort patches | 1 | 0 to 2 |
| algae fans (patches on the plan picture, after the outlet reach was widened to 0.7; the pipe feet are 5 on the left, plus the lamp posts) | 4 | at every pipe outlet: NOT clearly met (see the end) |
| chipped flag corners (5 to 10 % of flags) | not measured | |

### Not one dark mush (P5) - nearly met

Main, notice and close_road plates: every line passes (plate mean ratio 0.989, 0.987, 0.976). Lockout plate: the road is 0.45 percent brighter than the baseline in the 5 to 10 m band (1.0045; the line is 0.80 to 1.00), the rest passes. Earlier rounds showed why this line is touchy: before the even dust and the soot on iron were added, rust and polish made the road and the iron 0.2 to 1.4 percent brighter in several bands.

### Zones (P6) - met

Painted moss is 0.0 percent of the crown, the lanes, the fire zone and the doorstep strips on the street and lockout pictures (limit 0.2 percent).

### Drawing time (P7) - inside the whole line on the street, one first picture over on the lockout

All four ground layers alone, last round: the street plates take 7.44 s against 5.92 s (1.26 times; the line is 1.30), the street's first picture 2.65 s against 2.26 s (1.17 times; the line is 1.5). Lockout: plates 2.73 s against 2.25 s (1.21 times), first picture 6.38 s against 2.47 s (2.6 times: over the 1.5 line; the round before it measured 2.54 s on the same picture, so the first picture swings with the machine and the shader cache; my reading is that the first picture costs about 4 s more when the shaders have to be compiled). My share was meant to be +8 percent of drawing time: it is +26 percent, which leaves the other builders only 4 percent before the whole line is crossed. No 3D pieces are added.

### Self-tests (P8)

`selftest_ground.json` (street, lockout and courtyard; the street was run again after the last code change, key `street`; the first street run is `street_round6`): each layer acts on strong dial values; at amount 0 and with the master dial at 0 the picture equals the plain one within the plan's line (at most one 8-bit step on at most 1 percent of dots; worst measured 0.03 percent of dots, biggest single difference 0.0118 on a 0 to 1 scale); alone a layer changes only the dots of its own roles; taking a layer out (in another order, twice) restores every material exactly; two draws of the same picture are the same within noise; every layer goes in and out without a crash. NOT identical in 16 bit: the renderer's own noise is of the same size (two draws of one picture differ by up to 0.0004, the layers' amount-0 difference is up to 0.012).

The courtyard (dirt and moss only; the cracks and iron layers have no roles there and the test says so): the first run failed the isolation test for the dirt layer, because a layer that carries only tonal elements gave an empty Mask. I fixed `finish_parts` (a layer with only tonal parts now reports them as its whole Mask) and repeated the run: see `selftest_ground.json`, keys `courtyard` (first run) and `courtyard_after_fix`.

## What is not finished (the honest list)

- Algae fans: with the first outlet reach (0.3) they came out empty on every plan picture; with 0.7 the plan pictures show 4 fans and 1 liverwort patch, but in the drawn pictures (a lamp post foot where a fan sits) the picture does not change (changed share 0.0000 at a threshold of 8/255): the algae colour keeps the stone's brightness and the tint is too small to show at plate or close-view size. So "algae at every pipe outlet" is placed, not seen. Not fixed.
- At close range several elements are very subtle (film, polish, the rust halo, tar on a dark wet road): the dial sheet shows it. The ones that show clearly are the moss ribbons, the flag cracks, the kerb chips, the sunk and tilted setts and all the iron.
- The preset file wins over a default written by the layers, so the tuned values I would like (more cracks near the camera, `near_only` 20 m, `polish_lift` 0, `rust_cover` 0.5) are listed in `looks_ground/sooty_1926.json` under `_proposed` and in REQUESTS.md; they need the integrator.
- The wet look (P2), the plate readability (P3) and the drawing time of the first lockout picture (P7) are open, as above. P1 without the kit's own dots is one picture short.
- The first street self-test and the round-6 numbers were taken before three small code changes (a layer with only tonal parts reports them as its Mask, the algae outlet reach, the position grid for flags); the final street self-test and round 7 were taken after all of them. The courtyard self-test ran after the first change and before the outlet reach change (a default of an extra dial that the courtyard does not use).
- Not measured: the share of flag corners with a chip (5 to 10 percent): no picture of it was made; the courtyard was not measured against the readable and drawing-time lines (it has no plate camera yet).
