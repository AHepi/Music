# Recipe - the wall layers (soot, run-off, wall foot, doorsteps, wall cracks, wall growth, worn paint) - how they are made

Written in plain words by the walls builder. Code: `kits/weathering/walls/`. Numbers come from the last full round of drawing on the rented machine (round f8, street set and lockout file, plates 1536 x 2730), plus the self-tests of the final code. Where something does not pass its line, it says so. The list of what is not finished, not tested and not sure is at the end. Look values I changed are in `REQUESTS.md` (this folder), never in the kit's own `presets/` or `sets/`.

## What there is

Seven layers, each a node group that goes into the wall, trim, chimney and roof materials of the set through the kit's hook and chain (nothing here splices a material by hand). They read only the kit's standard masks by name (listed at the top of each file), so they work on any set; no file names a street, a house or a lamp (the kit's lint says zero hits in `walls/`).

| layer (group) | slot | status | what it adds |
|---|---|---|---|
| soot (`WK SOOT`) | A | done, works | the old coal-smoke crust: a general film, blackest under ledges and in reveals, pale rain-washed patches, more soot in the mortar hollows, a drier surface; chimney stacks and roofs get their own film |
| runoff (`WK RUNOFF`) | A | done, works on the street, draws nothing on the courtyard | pale washed streaks with dark edges below sills, ledges, caps, eaves and downpipe joints; a streak at both ends of a sill; long heavy leaks under the joints of some downpipes; rust tint at iron joints |
| foot (`WK FOOT`) | A | done, works | the dusty splash band at the foot of a wall (taller at pipe feet), the damp tide-mark on some houses with white salts along its top, worn mortar and flaked bricks in the lowest 0.6 m |
| steps (`WK STEPS`) | A | done, works | doorsteps: 55 percent of the doors have a whitened step (pale frame along the nosing, pale riser), 35 percent a scrubbed one, boots grey the middle, a worn dish, polish, chipped nosings |
| wallcracks (`WK WALL CRACKS`) | B (after the water layer and joints, dull) | partly: works, hard to see at plate size, the water-film cut is NOT done | a stepped mining crack on the houses the set flags, a few wavy cracks near corners and openings, chips at corners, spalled patches near the foot, map cracks on plaster |
| wallgrowth (`WK WALL GROWTH`) | C | partly: works on the courtyard, almost invisible on the street at the look's amount | painted moss, a thin green-black algae film, lichen (off in the street) |
| paint (`WK PAINT`) | A | built and smoke-tested only, NOT tuned and NOT measured (the COULD) | worn paint on doors, window frames and boards: darker old paint, pale bare-wood flakes, scuffs at the foot, a grease patch at latch height, lost gloss |

Not built, as told: limewash, bird lime, the roof soot fan.

Every layer has the amount dial; at amount 0 each effect is a product with the amount, so the layer gives back what it was given (see the numbers under "Master dial 0").

## How it is made (the short version)

- **Pale first.** 79 percent of the plate's wall dots are under brightness 0.10 and the film crushes anything under painted 0.10 to 0.12. A dark mark on a dark wall is simply lost, and a darker wall is mush. So the pattern is made of the light side: pale washed patches, pale streaks, a dusty-pale splash band, white salts, whitened steps, pale dust along a crack, moss lighter than the stone. The dark soot never goes below `floor_mult` of the clean colour. The helper `lift_to` (in `walls_common.py`) lifts a colour toward a pale stone colour wherever it is darker than that.
- **Marks have a width in plate dots.** Every width goes through the kit's `WK MARK WIDTH`: a streak is never narrower than `width_dots` plate dots (measured ALONG the wall, so a wall seen from the side gets wider streaks), a soot patch never smaller than 15 dots, a crack never under 3.5 dots, a splash band never lower than 15 dots. Far away the fine detail fades to the layer's average tone, never to clean.
- **Walls are slanted in the view.** Vertical marks (streaks, the washed patches stretched taller than wide, the stepped crack going up) survive; small horizontal detail does not. The mottling is stretched 3 times taller than wide (`mottle_stretch`).
- **Where the wall sheet applies.** The foundation makes a "wall sheet" picture for each house (sheltered, drip, corner, height, and the flag `frame_valid`). The layers use sheet masks only where `frame_valid` says a sheet applies; gables, chimneys, roofs and big plain buildings get the film and mottling only.
- **Height where the picture has none.** `height` reads 0 outside the ground picture (the colliery buildings, the tall chimney). The layers use `height_eff`: the larger of the bus height and the metres above the object's own lowest point (`wk_zmin`, written by the kit).
- **One random number per house.** From the object's own seed (`wk_seed`): which houses carry a tide-mark, a leak, a stepped crack, a whitened step. Nothing is drawn per camera: the amounts are shares of the wall in the world, checked on three cameras.
- **Object class.** `apply_walls` writes `wk_walls_class` on every object from its role's own name (0 wall, 1 chimney stack, 2 roof), so soot can give stacks and roofs their own film (`stack_mult`, `roof_mult`). The set's `role_dials` give per-role multipliers (for example `wall.trim`).
- **Wet.** The soot, run-off, foot, steps and paint layers sit in slot A, before the water layer, so water wets them (white goes grey when wet). Cracks (B) and growth (C) come after and read the wet and puddle masks (growth goes darker and greener when wet).
- **Part views.** Each layer has named parts (`soot.washed`, `runoff.streaks`, `foot.band`, ...). `apply_walls.show_mask(kit, 'soot.washed')` or `kit.show_mask('soot.washed')` shows one in plain light; the runner view `layer:soot.washed` does too; `layer:soot` shows the layer's own Mask (for soot: the pale washed patches, the readable element).
- **The water layer makes copies.** After the kit reads the set, the water layer makes a copy of each wall material per door layout and gives the wall objects the copies. `Kit.materials_for` does not list the copies, so a layer put in afterwards went into materials nobody used (my first soot picture changed no wall dot). `apply_walls` patches this on the kit INSTANCE only (REQUESTS.md A1).

## The layers, one by one

### soot
Film: 0.60 of the clean colour on every wall (plan 0.62) with the colour pulled 25 percent toward grey; under ledges and in reveals it is `sheltered_mult` (0.5 x the role's multiplier), with a crisp line where the shelter ends (`edge_sharp` 0.85). Rain-washed patches (`washed_share` 17 percent of the wall) are LIFTED above the film, up to a clean pale stone (`washed_pale` 0.8) so that they read. Mortar hollows carry more soot (`mortar_soot`). Rough surface and less shine where the film is dark. Chimney stacks `stack_mult` 0.8, roofs `roof_mult` 0.8.
New in the last round: `shade_wash` (0.2 in the street look, kit default 0.6). It says how much shade keeps the washed patches away. At 0.6 the shaded terrace far down the street got almost no washed patches and came out at 0.82 of base brightness while the near walls were at 0.96 to 1.0 (distance continuity, P5 M5); at 0.2 the far band is at 0.90.

### runoff
Streaks run in columns below each source (the `drip` mask); the streak pitch is 3.4 times the width from `width_dots`; each streak has its own length (0.5 to 1.3 times `length_mult` x 0.7 m); `source_share` 0.8 of the sources carry a streak; `pair_share` the two ends of every ledge; `leak_share` 15 percent of the downpipes get a long heavy leak. A streak on a sooty wall is a PALE stripe (`tone` -0.5) with dark tide-lines along its edges (`edge_dark`); on pale plaster (`tone` +0.7) it is a dark grey-green stain. `inflate_limit` 12: on the main camera the walls are seen almost edge-on and a streak has to be drawn up to 12 times wider than real to be 8 to 15 dots.

### foot
A splash band 0.28 m tall (never under 15 dots), darkest at the ground line, with a ragged top and fingers 10 cm tall; heavier at pipe and post feet (`pipe_foot_boost` 1.4). `splash_pale` 0.9 makes it a dusty brown LIGHTER than the wall (0 would be dark mud: it is crushed). Tide-mark on 45 percent of the houses, rising 0.8 m, slightly darker and greener inside, with white salt flecks along its top (`salt_bloom` 0.02, never under 6 dots). Worn mortar (`mortar_wear`, a small relief) and 7 percent flaked bricks in the lowest 0.6 m.

### steps
`step_top` is 1 on whole wall footprints (the ground plan is dropped on every up-facing face of the step roles), so it cannot find the tread. The layer uses `step_foot` (the soft spot round an entrance) times the metres above the ground (0.02 to 0.6 m), plus `edge_dist` and `step_edge` for the pale frame (7 cm, never under 8 dots). Per door (one random number per entrance): `whitened_share` 0.55 whitened, `scrubbed_share` 0.35 scrubbed, the rest plain. Boots grey the middle; a worn dish 5 mm (`dish_depth`); polish; chipped nosings. The whitened stone is the palest thing in a row of dark houses on purpose. In the night light it comes out cold blue-grey (see "Not sure").

### wallcracks
A few cracks, never a net. The stepped mining crack is built in the object's own frame (flag `wk_stepped`, `step_cm` 15, about seven steps at 45 degrees, wider at the top). Corner and opening cracks are wavy lines of noise cut thin, gated per house (`crack_amount`). Chips and spalls use `tx_cell`. Every crack has a pale dust lip (`crack_pale`) because a dark line on a dark wall is crushed. DULL: roughness back to 0.9 and shine minus 35 percent. The plan's "water film minus 45 percent" is NOT done (see tried and dropped).

### wallgrowth
Painted moss: flat olive tones, clumps taller than wide with a lighter rim, lighter than the stone and above `brightness_floor`, saturation 0.5, hue 100. Where: low on the wall, under run-off lines, on tops and caps. Algae: a thin dark green-black film at drips and shaded feet. Lichen: pale discs with rings, `lichen_amount` 0 in the street (the smoke killed it) and on in the courtyard looks. The look's `moss_amount` is only 0.05: at 0.12 the foot of every wall and every step was a green band.

### paint
Built small (87 nodes). Only the standard kit tests were run on it (master dial, isolation, node count). I did not tune it or measure it on the plates.

## The main dials (what they do)

The sheet `25 walls - what each main dial does.jpg` draws the main ones at three values on one house seen square-on. In short (plan Appendix A names; the finer dials I added are in `dials_walls.py`, each with a range and a sentence):

- soot: `film_mult`, `sheltered_mult`, `washed_mult`, `washed_share`, `floor_mult`, `grey_pull`, `mortar_soot`, `mottle_size`, `mottle_contrast`, `edge_sharp`, `stack_mult`, `roof_mult`, `base_lift`. Finer: `mottle_stretch`, `patch_min_dots`, `rough_gain`, `washed_pale`, `shade_wash`.
- runoff: `strength`, `tone`, `edge_dark`, `width_dots`, `length_mult`, `ragged`, `source_share`, `leak_share`, `leak_length`, `iron_rust`, `eave_streaks`. Finer: `pitch_mult`, `pair_share`, `stain_value`.
- foot: `splash_height`, `splash_strength`, `splash_ragged`, `finger_height`, `pipe_foot_boost`, `tide_share`, `tide_height`, `tide_strength`, `tide_green`, `salt_bloom`, `mortar_wear`, `spall_share`, `wear_height`. Finer: `splash_pale`, `band_min_dots`, `salt_dots`.
- steps: `whitened_share`, `scrubbed_share`, `frame_m`, `frame_dots`, `boot_grey`, `dish_depth`, `nosing_chips`, `wear_polish`. Finer: `tread_pale`, `chip_m`, `riser_share`.
- wallcracks: `crack_amount`, `crack_dots`, `crack_contrast`, `stepped_cracks`, `corner_chips`, `chip_cm`, `spall_patches`, `plaster_cracks`, `dull`, `slope_mm`. Finer: `chip_pale`, `step_cm`, `crack_pale`.
- wallgrowth: `moss_amount`, `algae_amount`, `lichen_amount`, `moss_height`, `patch_dots`, `drip_moss`, `cap_moss`, `roof_moss`, `tone_steps`, `clump_stretch`, `relief`, `lichen_dots`, `brightness_floor`. Finer: `moss_value`, `algae_strength`, `hue`, `saturation`.
- paint: `paint_dark`, `flake_share`, `door_scuff`, `latch_grease`, `gloss_loss`. Finer: `grain_dots`.
- every layer: `amount` (the master dial), `seed`, `inflate_limit`, `fade_start`, `fade_end`, `wet_follow`.

Values that differ from the plan are in `REQUESTS.md` section C with the reason (the plan's film of 0.62 over 85 to 100 percent of every wall turned the plate walls 23 percent darker).

## How to use it

```
from walls import apply_walls
apply_walls.register(kit)                      # the harness does this by itself
apply_walls.apply(kit, look='sooty_1926')      # every walls layer that has a role in the set
apply_walls.set_dials(kit, 'soot', film_mult=0.8)
apply_walls.show_mask(kit, 'soot.washed')      # one part; 'layer:soot' = the layer's own Mask
apply_walls.remove(kit)                        # everything out, materials restored
```

Self-test (Blender side, one scene per call): `blender -b --disable-autoexec SCENE.blend --python walls/selftest_walls.py -- SET SCENE OUT CONFIG.json` (writes `selftest_walls.json`). Sheet: `walls/sheet_walls.py` (Blender side, for scenes without lighting rigs) plus the Pillow montage helpers in the same file. On the rented machine: `walls/remote_walls.py` (its own record file, so helpers working at the same time do not overwrite each other) and `walls/runner_walls.py` (the kit runner plus extra cameras named in the job file).

## Using it on another set (the Japanese courtyard)

1. The set's `apply` block says which roles get which layer (the courtyard's already does: soot, runoff, foot, wallcracks, wallgrowth on `wall.plaster` and `stone.dressed`; steps and paint have no role there, and the self-test says "no role in this set" and skips them).
2. The look: `mossy_courtyard_kept` or `mossy_courtyard_neglected`, exactly as they are (the plan's first guesses; nothing tuned).
3. Nothing else: `harness/layers.py` finds `walls/apply_walls.py` and calls `register(kit)`.

What the courtyard test showed (sheet `25 Walls - the same layers on the courtyard plaster wall (reuse test).jpg`): soot gives the plaster a faint dirty mottle, foot a dusty band, wallgrowth a moss ribbon along the wall foot, wallcracks fine map cracks in the neglected look. **Run-off draws nothing there**: the courtyard has no wall sheets (`frame_valid` is 0 on its walls) and the layer uses the sheet's `drip` pictures only where a sheet applies. Wall sheets for the plaster walls are asked for in REQUESTS.md B6.

## What was tested (numbers)

### P5, the street not turned into mush (round f8, against the baseline plates; main, notice and lockout)

Whole plate brightness against base: 0.998, 0.999, 1.001 (the line allows a drop of 8 percent).

| class and plate | M1 darkened by a third | M2 share under 0.10, points | M3 mean ratio | M4 spread ratio | M5 bands 5-10 / 10-20 / 20-40 m |
|---|---|---|---|---|---|
| walls, main | 0.203 | -3.8 | 0.992 | 1.85 | - / - / 0.993 |
| walls, notice | 0.230 | -3.5 | 0.981 | 1.65 | 0.977 / 1.063 / 0.905 |
| walls, lockout | 0.116 | -5.0 | 1.034 | 1.54 | - / 1.117 / 0.986 |
| trims, main | 0.003 | +0.5 | 0.989 | 1.14 | - / 0.999 / 1.004 |
| trims, notice | 0.005 | -4.7 | 1.055 | 1.04 | 1.050 / 1.091 / 1.003 |
| trims, lockout | 0.001 | +1.0 | 1.030 | 1.25 | - / 1.098 / 1.002 |
| roofs, main | 0 | +4.2 | 0.973 | 1.06 | - / 0.961 / 0.973 |
| roofs, notice | 0 | +11.2 | 0.951 | 1.10 | 0.899 / 0.957 / 0.968 |
| roofs, lockout | 0 | +6.0 | 0.942 | 1.04 | - / 0.925 / 0.952 |

Reading it. M1, M2 (walls and trims), M3 and M4 are met. **M5 is NOT met in places:** the line asks every band ratio between 0.80 and 1.00 and at most 0.08 apart. Over the top: walls notice 10-20 m 1.063, walls lockout 10-20 m 1.117, trims notice 1.050 and 1.091, trims lockout 1.098 (the pale layers add more than the soot takes away at 10 to 20 m). Too far apart: walls notice (1.063 against 0.905, 0.158), walls lockout (0.131), trims notice (1.091 against 1.003, 0.088), trims lockout (0.096). Nothing is under 0.80. The roofs have no M2 line in the plan (only road, pavement, walls, trims); their share under 0.10 rises 4 to 11 points, reported. The chimney stacks and the colliery buildings are my own extra classes (not in the plan's list): stacks are at 0.83 to 0.85 of base (a drop of 15 to 17 percent, over the 12 the line gives to a class), colliery at 0.94, share under 0.10 up 11 to 15 points.

How it got here (the tuning that mattered): the plan's film darkened plate walls by 23 percent. With the pale-first changes the walls sit at 0.98 to 1.03. Trims: soot on trims at `film_mult` 1.15 / `sheltered_mult` 1.5 pushed 5.5 points (main) and 9.9 points (lockout) more trim dots under 0.10; at 1.4 and 1.75 it is +0.5 and +1.0, at the price of trims 3 to 5 percent brighter than base.

### P3, readable at painter size (scale 0.45, inside the design zone)

The line: at least 60 percent of marks GOOD, at most 15 percent LOST, at most 15 percent crushed. None of the elements meets it, except part of two small samples.

| element | plate | marks | GOOD | LOST | crushed |
|---|---|---|---|---|---|
| soot (the pale washed patches) | main | 152 | 34 % | 45 % | 10 % |
| soot | notice | 134 | 34 % | 48 % | 6 % |
| soot | lockout | 162 | 40 % | 41 % | 12 % |
| runoff | main | 0 | - | - | - |
| runoff | notice | 81 | 10 % | 63 % | 19 % |
| runoff | lockout | 20 | 45 % | 30 % | 10 % |
| foot | main / notice / lockout | 10 / 25 / 15 | 0 / 16 / 0 % | 70 / 72 / 67 % | 70 / 60 / 60 % |
| steps | notice | 6 | 67 % | 33 % | 0 % |
| wallcracks | main / notice / lockout | 29 / 78 / 79 | 0 / 9 / 9 % | 66 / 47 / 66 % | 3 / 3 / 0 % |
| wallgrowth | all | 0 | no marks at the look's amount | | |

Why: the walls are seen almost edge-on and are very dark (79 percent under 0.10), so a streak or a crack that is right in the world is a few dots wide with little contrast. The main camera shows no run-off mark inside the zone at all. A bigger `washed_pale` or `strength` would probably raise the GOOD share a little (the dial sheet shows the look; I did not measure P3 at other values) but also brightens the walls over base; I did not go further.

### P7, drawing time (best of three, same card, plate 1536 x 2730, 48 samples)

| | base | six walls layers | ratio |
|---|---|---|---|
| main (P7 run) | 1.93 s | 2.54 s | 1.316 |
| main (per-layer run, a second measurement) | 1.94 s | 2.48 s | 1.278 |
| lockout | 2.27 s | 2.84 s | 1.251 |

The line: all kit layers together at most 1.30, and the walls' own share +8 percent. The walls layers alone use +25 to +32 percent: **not met** (the share) and on the line (the total). Alone each costs (main): soot +3.1, runoff +2.6, foot +3.6, steps +0.5, wallcracks +5.2, wallgrowth +5.7 percent; together more than the sum. First picture after applying: 28.6 s (main) and 27.7 s (lockout); under 40 s, but the line also asks at most 1.5 times the base's first picture (5.2 s, so 7.8 s): **not met**. The cost is the number of materials times about 150 nodes (soot goes into 14 to 18 materials, most of them not walls). Levers for the integrator: a smaller `apply` block (only the wall and trim materials) and `fade_end` closer.

### P8, master dial 0 and isolation (the kit's self-tests on the final code)

- **Isolation** (a layer alone acts only on its roles): passed for every layer on the street, on the lockout file and on the courtyard, 0 dots acting outside the roles in every case, except `runoff` on the courtyard (nothing acts there at all, so the test cannot pass; no dot acted outside the roles either).
- **Amount 0, one layer at a time**: the kit's test line (at most 1 percent of dots changed by more than one step of 255) is met by every layer on every scene (0.00 to 0.12 percent). But the picture is NOT always bit-for-bit the same. On the street with the earlier layers on, soot, run-off, foot, wallcracks and wallgrowth at amount 0 change 0.8 to 3.2 percent of the dots, by at most 0.023 of full brightness (about 6 steps of 255); steps 0.9 percent, at most 0.014. The paint layer is identical. On the lockout file (no earlier layers) the changes are at most 0.0005 on at most 0.4 percent of dots; on the courtyard at most 0.00125 on at most 5.8 percent (below half a step). I do not know the cause (REQUESTS.md A5 describes the same kind of difference).
- **Master dial 0 with all layers in** (`set_master(0)`): street 0.7 percent of dots changed, 0.025 percent by more than one step, largest 0.0149; steps layer alone 1.4 percent, largest 0.0149; lockout 0.5 percent, largest 0.0003; courtyard 9 percent of dots, largest 0.0035 (under one step). All pass the kit's line; none is bit-identical.
- **Two draws of the same picture** (determinism): identical on the street and the lockout file with all layers; on the courtyard and the steps test the two draws differ by at most 0.0018 on at most 0.08 percent of dots (not over one step).
- **Reuse test** (every layer in and out, materials restored exactly): passed on all three scenes, with no wiring problems.
- **Node counts** (limit about 150): soot 126, run-off 146, foot 140, steps 100, paint 87, wallgrowth 152, wallcracks 172 (over the guide by 22). Noise or Voronoi nodes: 1 to 3 each. No Bevel, AO or Pointiness node in any.

### P2, the wet look (wall part, main and lockout, wet against dry mean brightness)

| | base | with the layers | difference |
|---|---|---|---|
| walls, main | 0.848 | 0.875 | +0.028 |
| trims, main | 0.946 | 0.948 | +0.002 |
| walls, lockout | 0.883 | 0.895 | +0.012 |
| trims, lockout | 0.933 | 0.923 | -0.010 |

The line: within 0.05 of base. Met on these two plates. I did not measure the other wet and heavy pictures of the 22, nor each element's own wet/dry ratio (at most 1.0).

## Tried and dropped

- **A dark soot film on every wall at 0.62** (the plan). It turned the walls 23 percent darker and most of them was crushed under 0.10; the pale-first version replaced it.
- **The water-film (coat) cut in wallcracks.** A Coat Weight made from noise changed the picture at amount 0 (up to 0.056 of full brightness on 2.9 percent of dots) although it is mathematically the same number; writing the same expression as `coat x (1 + 0 x Amount)` changed nothing. I do not understand it, so the cut is left out (roughness and shine only). REQUESTS.md A5.
- **Splash dots above the foot band**: they read as dirt specks and were crushed.
- **Moss at 0.12 and above**: a green band along every wall and every step. Cut to 0.05; hence almost no moss on the street plates.
- **Washed patches on the engine house and other plain buildings**: they looked like camouflage. The washed weight is cut where there is no wall sheet, and `wall.industrial` gets `film_mult` 1.4.
- **Using `step_top` for the steps**: it is 1 on whole wall footprints (REQUESTS.md B1).
- **Shade fully keeping the rain-washed patches away** (`shade_wash` 0.6): the shaded far terrace came out darker than the near walls; now 0.2.
- **Chimney stacks at 0.5** (plan 0.35): 55 to 64 percent of base brightness and crushed; now 0.8.

## What was not tested

- No picture was run through the painter (no paid image call). How much of the pale patches, streaks and cracks the painter keeps is unknown.
- Not measured: the period caps (P4: soot share, streak share of the wall, sill pairs, leaks, splash on 70 to 90 percent of wall length, steps 40 to 70 percent), the hue check on changed dots, P6 for the wall moss with the kit's tool, P10 (the behind plate), the wall-moss part of P1.
- P2 only on the main and lockout wet and dry pictures, not the 22.
- The courtyard ran only small tests (300 x 200 and 900 x 600 pictures) with the unchanged courtyard looks.
- The paint layer: node count, master dial and isolation only; not looked at on a plate close view after the last round; not measured.
- Lighting E and the heavy-rain pictures; Cycles.
- The first picture after applying in the courtyard scene; drawing time on the courtyard.

## What I am unsure about

- **How much.** On the dark plates the soot film at 0.60 plus pale patches gives a mean about equal to the baseline: the walls get a visible pattern but not a darker street. The left terrace's red brick goes dark grey-brown in the plates (see `25 walls - before and after.jpg`). Whether that is "grimy enough" for the film is the person's call; the dial sheet shows `film_mult` 1.0, 0.6, 0.4.
- **Which colour.** Whitened steps come out cold blue-grey in the night light (the stone's albedo is pale; the light is blue sky). The splash band is a dusty brown lighter than the wall; on some walls it reads as a pale band rather than mud.
- **Whether the painter keeps it.** Run-off, wall foot and cracks are mostly lost at painter size by my measure; if the painter ignores marks that small they can only be seen in the plates. Soot patches and whitened steps are the elements most likely to survive.
- **Pale washed patches on a single house seen square-on** look like large pale blotches (the first sheet picture). On the plates at 6 to 40 m they read as rain-washed wall. A fresh checker should look at eight 100 percent crops.
- **The cause of the small Amount-0 differences** on the street with the earlier layers on, and of the unexplained coat difference.
- **Whether trims should get any soot** at all: at the measured values they are slightly brighter than base.
