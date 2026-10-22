# What the masks do NOT do yet (honest list)

Written by the foundation at the end of its time. Each line says what is missing or approximate, why it matters to a builder, and what to do about it. Nothing here is hidden in a pass: where a check failed, its number is given.

## Checks that FAIL (numbers)

| what | wanted | got | what it means |
|---|---|---|---|
| `sheltered` on the top of a sill (street pack, cottage 01 sills at 0.85 and 3.55 m) | 0.1 or less | 0.125 at 3 cm above the sill (0.13 to 0.21 up to 10 cm above) | the window above shelters the sill top within the 1.2 m reach; the sill top is "mostly open", not fully. Layers should treat 0.15 as "open" |
| courtyard wall sheet "Hall plaster": bus consistency (200 random points, stored picture against what the shader draws) | at most 2/255 = 0.0078 | worst 0.0646 (`reveal`), 0.030 (`shade`), 0.028 (`sheltered`); the other two courtyard sheets and every street and lockout sheet are under 0.003 | a few points fail; the means agree (0.0133 stored, 0.0146 drawn). Probably points within one dot of a sharp edge where the drawn value is interpolated; not investigated. The ground-plan masks on the courtyard pass (0.0012) |
| `wall_dist` against the earlier places picture (street, 472,500 dots) | within 3 levels of 255 on 99 % of dots | 95.8 % on every dot; 100 % on the dots the earlier picture covered (\|x\| at least 2.7 m) | the earlier picture ignored steps and plinths in the middle of the road by construction; the new one is true everywhere. 4.2 % of dots differ, all in that middle strip |
| `vertical_foot` against the earlier places picture B | 99 % | 99.4 % on every dot, 98.8 % outside the road middle | a few dots at the edge of the post and pipe feet |
| `prop_dist` against the earlier lockout places picture | 99 % | 97.5 % on every dot, 98.4 % outside the road middle | the lockout file's props have moved a little since the earlier picture was made |
| the dot-size table of the plan (6.4) | within 3 % | `across` is within 3.03 % of the table everywhere (the table is rounded to two figures: 1.6 against 1.554 mm is 3 %) and within 1 % of exact arithmetic from the camera; `along` is within 1 % of exact arithmetic with the real surface normal but 12 to 61 % off the table beyond 15 m | the table assumed flat ground; the road leans 4 degrees toward the camera, so far dots are shorter along than the table says. Use the helper, not the table |

## Missing masks, frames and finders

* **Courtyard wall "Right wall behind hall"**: the reader could not make a sheet (`no wall face points toward the ground plan`; the pack's `stats.sheet_errors` lists it). That wall reads the ground-plan version of every mask. The set file asked for both faces of each courtyard wall (`sides: both`); the reader makes one sheet per wall and only for the dominant face. The other face reads the ground plan.
* **Roofs, chimneys, the colliery buildings' walls, iron and props** have no wall sheet by design (the set file says `kind: none`): they read the ground plan, their own height above the ground and their `wk_zmin`/`wk_zmax`. A roof-eave finder for instanced roof meshes was not written: roof edge run-off sources are only the eave courses found on the cottage wall sheets (25 sources per sheet).
* **Wall-sheet `sheltered` shows horizontal banding** (under a ledge it alternates 1.0 and 0.75 in bands about 10 cm tall) from the fixed 24-ray pattern. Blur it a little (two or three dots) inside a layer, or ask the foundation for more rays.
* **Ground-plan `drip` lines** (the footprint of raised, up-facing surfaces dropped to the ground, a soft 12 cm line) look blocky in the plan picture. Not investigated.
* **Texture-space cell numbers** (`tx_cell`) for brick, stone and flags are approximate: cells are labelled by flood-filling the cavity picture closed at the joints; a flag or brick that touches its neighbour through a gap in the cavity shares a number. Joints and cavities themselves are good (the sett joints reuse the earlier joint picture). The brick period is read from the set file (1.4 m, 2.5 m for stone), not measured from the photo.
* **Existing growth** is blurred 15 cm and kept as one density; the courtyard finds 9 separate patches at 0.5 or more where the set names 7 (a patch may split in two, never vanish).
* **`rubbish_heap`** exists only for the street and lockout packs (drawn on the rented machine from the pinned earlier rubbish layer); the courtyard has no rubbish layer, so it reads 0.
* **Acceptance checks of the mask table that are not made**: `corner` and `reveal` finding all four edges of every window and door on cottage 01; `edge_dist` at least 95 % of kerb top-edge dots under 0.05; `seam_dist` at the known x positions; `entry_rand` against the 1.4 m disc (only "one value near each door" is checked). They need positions the pack does not keep. The reader's own acceptance checks (slope, crown, lowness, entrances, ledges, steps, pipe, kerb stones) all pass, see `test_results.json`.
* **Element masks beyond one per layer** (`layer:<key>/<element>`): not built. A layer exposes one `Mask` output; the elements of the plan's period table that need their own mask (washed wall, streak pairs, tar patches, whitened steps) are listed `not_automated` in the look file's `period` table and must be counted from a builder's own feature report.
* **Sets with a bigger scene than the ground picture**: x or y outside the ground bounds returns the mask's default; the street's far end beyond 72 m is the default.

## Measures written but never run on a real layer

`measure_readable.py`, `coverage.py`, `measure_period.py` and `measure_zones.py` (the pieces and marks tests) are tested only against made-up pictures with known answers (`harness/test_measures.py`, 28 checks): no kit layer exists yet to draw. `measure_joints.py`, `measure_wet.py`, `measure_mush.py`, `measure_time.py` ran on the real baseline.

## Things that are a decision, not a gap

* The street's declared sun makes the left row's fronts the shaded side (the plan said the art lead may flip it): the shade-side check passes (shaded fronts 0.71, lit fronts 0.43, difference 0.27, wanted 0.2).
* `dampness` weights were changed in the street set so a wall foot and the foot of a pipe or post read above 0.6 (median 0.65 and 0.80), with a new term `standing_foot` (the bus mask `vertical_foot`); the road middle stays at 0.0. The courtyard's weights are unchanged.
* The lockout pack's ground plan is the street's (same ground); only the prop and fire shapes, the heap picture and the role counts differ.
