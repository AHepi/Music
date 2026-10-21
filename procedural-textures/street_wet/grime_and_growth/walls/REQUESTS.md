# Requests from the walls builder (for the foundation's owner and the integrator)

Nothing in `apply/`, `masks/`, `harness/`, `sets/` or `presets/` was edited. Each request is the smallest change I can name, with the reason.

## A. Changes to the kit's own code (small)

1. **`Kit.materials_for(layer)` misses the copies the water layer makes.** It lists the materials of the layer's roles as they were when the set was read. The water layer's script then makes a copy of each wall material per door layout (`<material>_door_left`, `_door_right`, ...) and gives the wall objects the copies, so a layer put in after the water layer goes into originals nobody uses (my first soot picture changed the trims and chimneys but not one wall dot: walls 0.995 of the baseline). Smallest fix: in `materials_for`, also return every material whose name starts with a listed material's name (plus a suffix) and for which `chain_for` gives a chain. I did this on the kit INSTANCE in `walls/apply_walls.py` (`_patch_materials`), so nothing else changes; the ground builder will hit the same thing if the water layer copies a ground material.
2. **`remote.py` writes one shared record file (`harness/.remote_state.json`) from every helper working at the same time.** Two helpers can overwrite each other's record (the effect is only a resend). `walls/remote_walls.py` sets `remote.STATE_FILE` to a private file. A per-helper state file in `remote.py` would do the same for everyone.
3. **Runner: extra cameras.** The runner can only use cameras of the set file. `walls/runner_walls.py` wraps the kit runner and adds `extra_cameras` from the job file (face-on views of a wall). A job-file key in `harness/runner.py` would make my wrapper unnecessary.
4. **Runner views for named parts.** `layer:<key>` shows a layer's one Mask. The walls layers also have named parts (`Part Washed`, ...). `apply_walls.register` wraps `masks.debug.show_layer` so that `layer:soot.washed` works in the runner and wraps `kit.show_mask` so that `kit.show_mask('soot.washed')` works, both on the running process only. A `parts` list in the layer template would make it a standard.
5. **Unexplained, found by the self-test:** a layer that makes `Coat Weight` from a noise-driven number changes the picture at Amount 0 (up to 0.056 of full brightness on 2.9 % of dots, in the standard test with and without the earlier layers on), although the value is mathematically the same as the input. Bypassing only that one output makes the difference vanish; the same expression written as `coat x (1 + 0 x Amount)` does not change anything. `wallcracks` therefore does NOT cut the water film (the plan's "water film minus 45 percent"); it does roughness 0.9 and shine minus 35 percent only. Someone who knows EEVEE's coat closure should look at it, because the integrator will want the coat cut.

## B. Masks I would like (the walls layers worked around each)

1. **`step_top` is 1 on whole wall footprints, not only on the treads** (the ground-plan picture is dropped from every up-facing face of the step roles, and a wall face reads the picture at its own x and y). The steps layer therefore uses `step_foot` (the soft spot round an entrance) x the metres above the ground, plus `edge_dist` and `step_edge` for the pale frame. A mask `step_surface` (1 on the tread and the riser only) would make the whitening exact.
2. **`drip` is a column under a whole ledge, not a streak.** The sill-end pairs are made from the edge of that column (where `drip` is half way). A mask "distance to the nearest END of the source" (0 at an end, 1 in the middle) would give the pairs their real width and position; at the moment the width of a pair is limited to the 12 cm of the picture's soft edge.
3. **`height` reads 0 outside the ground picture** (anything beyond y 72: the colliery buildings, the tall chimney). The layers use `height_eff` (the larger of the bus height and the metres above the object's own lowest point, from `wk_zmin`). A "valid" flag with the mask would be cleaner.
4. **`sheltered` bands** (1.0 and 0.75 every 10 cm under a ledge) are flattened inside the soot layer; more rays would remove the need.
6. **The courtyard has no wall sheets** (`frame_valid` is 0 on its walls: the average over the picture is 0.04). The walls layers that need the sheet (`runoff` entirely, `wallcracks` and `soot` for their per-wall parts) therefore draw nothing or only their sheet-free parts there: on the courtyard, `runoff` draws nothing at all and its isolation self-test cannot be proven (0 dots act). Wall sheets for the plaster walls would let the runoff run under the cap tiles. I did not make a private sheet: it is the foundation's picture.
7. **`tx_cell` is approximate** (the foundation says so): spalls and chips use it, so some neighbouring bricks share a number.

## C. Look values I would like in `presets/sooty_1926.json` (walls part) and in the street set file

These are the values I measured with (private copies in `work/tuned/`; the plan's own values are given as "plan"). Why: the plan's film (0.62 on 85 to 100 percent of every wall) turns the plate walls 23 percent darker (pass line P5 asks at most 12) and the walls are already 79 percent under brightness 0.10.

| layer | dial | plan | measured | why |
|---|---|---|---|---|
| soot | `film_mult` | 0.62 | 0.60 | the film darkens; the washed patches below are lifted far above it, the plate's mean stays within 0.92 to 1.06 of the baseline |
| soot | `washed_share` | 0.20 | 0.17 | less pale area |
| soot | `washed_pale` | (new) | 0.8 | how far the washed patches are lifted toward a clean pale stone, so they read on a dark wall |
| soot | `edge_sharp` | 0.60 | 0.85 | a clearer line between washed and sheltered |
| soot | `mottle_stretch` | (new) | 3.0 | taller, more rain-like patches |
| soot | `stack_mult`, `roof_mult` | 0.35, 0.82 | 0.8, 0.8 | chimney stacks were 55 to 64 percent of base brightness at 0.5; at 0.8 they are 83 to 85 percent and no longer crushed |
| soot | `shade_wash` | (new) | 0.2 (kit default 0.6) | how much shade keeps the washed patches away; at 0.6 the shaded far terrace had hardly any washed patches and was 0.82 of base against 0.96 to 1.0 near (P5 M5); at 0.2 it is 0.90 |
| soot | `inflate_limit` | 6 | 8 | |
| runoff | `strength`, `stain_value` | 0.55, (new) | 1.0, 0.9 | pale streaks must be strong to show on the dark walls |
| runoff | `inflate_limit` | 6 | 12 | on the main camera the walls are seen almost edge-on: a streak has to be drawn many times wider than real |
| runoff | `source_share`, `pair_share` | 0.7, (new) | 0.8, 0.8 | |
| foot | `splash_strength`, `splash_pale` | 0.5, (new) | 0.9, 0.9 | a dusty brown LIGHTER than the wall, not dark mud |
| foot | `salt_bloom` | 0.03 | 0.02 | |
| wallgrowth | `moss_amount` | 0.4 | 0.05 | at 0.12 the foot of every wall and every step was a green band; at 0.05 it is a few patches |
| wallgrowth | `moss_value`, `saturation` | (new) | 0.2, 0.5 | |
| wallgrowth | `algae_amount`, `algae_strength` | 1.0, (new) | 0.6, 0.4 | |
| wallcracks | `crack_amount` | 0.3 | 0.5 | |

Set file (`apply.soot.role_dials`): the plan's `wall.trim film_mult 0.8`, `chimney film_mult 0.6` and `roof.slate film_mult 1.3` should go: the layer now has the class dials `stack_mult` and `roof_mult` for chimney stacks and roofs (it tags each object from its role's own name: `chimney`, `roof*`). For trims I measured `wall.trim: film_mult 1.4, sheltered_mult 1.75` and `wall.industrial: film_mult 1.4` (private copy `work/tuned/street_set.json`). Reason: with 1.15 and 1.5 the share of trim dots under 0.10 rose by 5.5 points on the main plate and 9.9 on the lockout plate (the line allows 3); with 1.4 and 1.75 it rises by 0.5 and 1.0. The cost: trims come out 3 to 5 percent BRIGHTER than base on average (the pale layers on trims add more than the soot takes), which is over the 1.00 top of the band-ratio line (P5 M5: 1.05 to 1.10 in the 5 to 20 m bands). Courtyard: the layers ran with `mossy_courtyard_kept` and `mossy_courtyard_neglected` exactly as they are (the plan's first guesses); nothing was tuned there.

## D. For the integrator

* Drawing time (best of three, plate 1536 x 2730, 48 samples, same machine): the six walls layers together cost **+28 to +32 percent** of a plate on the main camera (1.278 and 1.316 in two runs) and +25 percent on the lockout camera (the plan gave walls +8, all layers +30). Alone, each layer costs: soot +3.1, runoff +2.6, foot +3.6, steps +0.5, wallcracks +5.2, wallgrowth +5.7 percent; together they cost more than the sum (about +20). The first picture after putting them in takes about 28 seconds (limit 40; at most 1.5 times the baseline's first picture, which would be 7.8 seconds, is NOT met). The cost is the number of materials times about 150 nodes: soot goes into 14 to 18 materials, most of them not walls. A smaller `apply` block (only the wall and trim materials) and fewer layers on trims would help; the `fade` distance at which a layer stops drawing its fine detail is the other lever.
* Order of layers in the chain, all through `apply_walls.apply(kit)`: soot, runoff, foot, steps (slot A), wallcracks (B), wallgrowth (C).
* The look file's `readable` table asks `layer_<key>_plate_<camera>.png` to be the marks. The soot layer's Mask is the pale washed patches (the readable element), not the whole film.
