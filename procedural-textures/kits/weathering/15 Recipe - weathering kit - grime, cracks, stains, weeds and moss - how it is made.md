# 15 Recipe - weathering kit - grime, cracks, stains, weeds and moss - how it is made

Written by the integrator, 21 October 2026, in plain words; **section 12 and the notes marked "fix round" were added after the two checkers' findings (the same day).** This is the one note that ties the whole kit together: how to put it on and take it off, the order everything goes on in, every dial, how to switch each thing off, how to add a new set (the Japanese courtyard is next), and every number measured on the pit village street, including what does not pass. Nothing here was painted: no call to the painter was made.

Words used. A **set** is one place built in Blender (the pit village street, the Japanese courtyard). A **scene file** is one saved Blender file of a set (the street copy, the film's lockout shot file, the courtyard). A **plate** is the one picture drawn from the set's camera that the painter (the image model) repaints. A **layer** is one recipe for one kind of wear (soot, cracks, moss ...), packed as a single node group, that sits in a material between the surface's own colour and the final shader. A **mask** is a grey picture that says where something may happen (made once from the real shapes). A **dial** is one named number of a layer. The **master dial** of a layer is its `amount` (0 = the layer does nothing). A **look** is a file of dial values (a sooty 1926 coal town, a mossy temple). A **settings file** is the file that holds everything about one set.

---

## 1. What the kit is, in one page

A kit that ages painted-film sets. Fifteen parts, all drawn into the materials of the 3D set so that the plate the painter receives already has the grime, cracks, stains, weeds and moss in it:

| part | what it makes | where it lives |
|---|---|---|
| WETNESS (earlier) | water, shine, puddles | pinned copy in `integrate/legacy_round2/earlier/tools` |
| JOINTS (earlier) | dark dull joints between the road setts | `.../relief_and_rubbish/setts` |
| RUBBISH (earlier) | painted litter and 58,753 tiny 3D litter pieces (the second painter round's fixed version) | `.../relief_and_rubbish/rubbish` |
| `soot` | the old smoke crust on walls, roofs and chimneys, with rain-washed pale patches | `walls/` |
| `runoff` | pale run-off streaks under sills, ledges and downpipes | `walls/` |
| `foot` | the dusty splash band and tide-mark at the foot of a wall | `walls/` |
| `steps` | whitened and scrubbed doorsteps | `walls/` |
| `wallcracks` | stepped mining cracks, corner chips, spalls | `walls/` |
| `wallgrowth` | painted moss, algae and lichen on walls | `walls/` |
| `paint` | worn paint on doors and frames (untuned: OFF in the street) | `walls/` |
| `dirt` | ground film, polish, water marks, tar patches, rust halos, doorstep scrub | `ground/` |
| `groundcracks` | cracks in flags, chipped kerbs, disturbed setts | `ground/` |
| `groundmoss` | moss ribbons in joints, algae under downpipes, liverwort | `ground/` |
| `iron` | rust, collars, shoe streaks, the fire drum | `ground/` |
| `growth` | small separate 3D weeds and moss cushions | `growth/` |

What it never does: nothing is edited in a mesh or a material slot; nothing modern (graffiti, road lines, wheelie bins ...) exists in the look; lichen is exactly 0 in the street; no layer reads a street or courtyard name (a lint test fails the build if one does); no picture is drawn on this computer (the rented machine draws).

Folders (all under `kits/weathering/`): `apply/` the core (settings, roles, the hook that puts a layer into any material, the chain, dials), `masks/` the where-pictures and their packs, `harness/` cameras, lights, the 22-picture test set, the runner and every measuring script, `integrate/` the pinned earlier layers, `walls/` `ground/` `growth/` the three builders' layers, `sets/` one settings file per set, `presets/` one look per file, and the two top-level files `apply_weathering.py` (the one door, works for any set) and `street_weathering.py` (the street's small wrapper).

---

## 2. How to put it on and take it off

Inside Blender with a scene file open (it is only changed in memory, never saved):

```python
import sys; sys.path.insert(0, '<kit folder>')
import apply_weathering as aw
w = aw.apply('<set id>', '<look id>', state='wet')   # set id = a file in sets/, look id = a file in presets/ (or full paths)
w.set_master(0.8)                    # all the kit's layers together, 0 = nothing, 1 = as the look says
w.set_layer_master('soot', 0.5)      # one layer (any key in the table above)
w.set_master_of('rubbish', 0)        # the earlier layers too: 'wetness' (0 = dry), 'joints', 'rubbish'
w.layer_off('growth'); w.layer_on('growth')      # take a layer out of the materials and put it back
w.set_dials('soot', film_mult=0.4)   # any dial of a layer that is on
w.set_state(0.85, 0.5)               # wetness and puddles
w.camera(cam_object, plate_height=2730)   # tell the layers how big one plate dot is for this camera (before your own render)
w.report()                           # what went into which material, what was skipped, any problem
w.remove()                           # EVERYTHING off, every material exactly as it was
```

The street has a small wrapper with plain names for the groups of layers:

```python
import street_weathering as sw
sw.apply(state='wet')                            # water, joints, litter, then the kit; works on the street copy and on the lockout file
sw.set_master('walls', 0.5)                      # walls | ground | growth | earlier | all, or any layer key, or wetness | joints | rubbish
sw.remove()
```

What `apply` does, in this order: (1) read the settings file and the look, find the roles in the open scene, attach the mask pack made for this scene file; (2) register the three builders' layers and their finer dials, then check the look against them; (3) write the per-object values (`wk_seed`, `wk_role_id`, ... a number on each object so a material shared by two kinds of object stays shared) and take a snapshot of every material; (4) put on the earlier layers if the set has them (WETNESS, then JOINTS, then RUBBISH, each by its own pinned script); (5) put the kit's layers into the materials of their roles, each in its slot; (6) set the wet state. The set decides by itself whether it has earlier layers: its settings file has a `legacy` block or it has not. The courtyard has none, so `apply` puts on only the kit.

Drawing pictures (rented machine only): `python3 -I harness/run_testset.py SET LOOK OUT_ROOT --tag t1 [--layers a,b] [--today]` draws the whole test set of a look; `street_weathering.plates(out_folder)` draws the street plates before and after. Always through `harness/remote.py`, which uses only `runpod/render_client_cached.py`. States must start with `today` (the scene exactly as it is); the runner draws that first by itself.

The integrated test of the door (`harness/test_weathering_entry.py`, run on the rented machine) checks: remove gives back the scene as it was, all master dials at 0 give the picture of the earlier layers alone, two draws are identical, apply and remove twice leave the same number of nodes, each group of layers changes the picture, the earlier layers' own master dials work. Its results for the street, the lockout file and the courtyard are in section 9.

---

## 3. The order everything goes on in, and why

Every material has a chain: the surface's own colour, roughness, shine, coat, normal and metallic go through a list of stages and then into the final Principled BSDF (the shader box that draws the surface). A layer has three possible places, called slots:

| slot | what sits there | why there |
|---|---|---|
| **A** (before WETNESS) | everything that is a *different dry colour of the same stone*: soot, run-off, wall foot, steps, ground film and polish, rust, tar | water darkens by the surface's own porosity, so a wet street is consistent with no extra "wet look" dial, and white goes grey when wet |
| WETNESS | water, shine, puddles | unchanged |
| JOINTS (road only) | dark dull sett joints that survive wet light | unchanged |
| **B** (after water and joints) | cracks and chips (walls and ground) | a crack is a narrow dark line; water washes narrow dark lines out unless the crack comes after and makes itself dull |
| **C** (after B) | painted moss, algae, lichen, moss ribbons in joints | plants lie on the stone and follow the wet mask themselves |
| RUBBISH | litter | litter lies on top of plants |
| `growth` | not in the chain: separate 3D objects on a hidden helper | drawn on top of everything |

Which materials get which layer (street): road setts `dirt` - WETNESS - JOINTS - `groundcracks` - `groundmoss` - RUBBISH; flags, gutter stones, kerbs the same without JOINTS; house walls (4 per-door-layout copies the water layer makes) and dressed stone trims `soot`, `runoff`, `foot`, (`steps` on trims) - WETNESS - `wallcracks` - `wallgrowth`; colliery brick `soot`, `foot`; chimneys and the slate roof `soot` (a class value for each); cast iron, wheel iron, headframe steel, wire rope, the fire drum `iron` straight before the Principled BSDF (no water layer there); doors and window frames `paint` (OFF); the yard, moor, spoil heaps, glow, glass, sky, interior, brass, notice and sign materials get nothing. Courtyard: plaster `soot` (as a dust and algae film), `runoff`, `foot`, `wallcracks`, `wallgrowth`; natural stone through the **adapter** (the add-on's stones have no Principled box, so the kit builds one from the group's own colour, roughness and normal outputs) with `wallcracks`, `groundmoss`, `wallgrowth`; gravel and earth `dirt`, `groundmoss`; roof tile `soot`, `wallgrowth`; timber `foot`, `wallcracks`, `wallgrowth`.

### 3.1 Which earlier layers, and the second painter round

The first set of pinned copies (`integrate/legacy_pinned/earlier`, what the frozen baseline in `harness/baseline` was drawn with) has the first painter round's rubbish and joints. The second painter round finished its plate step (its numbers are in `painter_round_2/plate/plate_round2_numbers.json`) and fixed the rubbish (flatter coal lumps, more density in the gutter, curved straw, pieces that gather at the kerb and the wall foot, new defaults amount 1.4, patchiness 0.7, wall foot width 0.6) and the joints (new joint pictures, the joint relief fades earlier: far share 0.03 from 3 to 10 m). **This integration uses the second round's fixed tools** (copied by `integrate/pin_round2.py` into `integrate/legacy_round2/earlier`, hashes in `integrate/legacy_round2.json`; the only edits are the absolute paths put back to relative ones). The street's settings file says so (`legacy.pinned_root`); `WK_LEGACY_PINNED` in the environment overrides it for a one-off comparison with the first set. The difference matters: the second round's litter is 58,753 pieces (the first round's was 6,439). Every "before" picture in this work is drawn with the second round's tools, so before and after differ only by the new parts.

### 3.2 The overlaps the builders could not see, and what was decided

Each of these was found by looking at the three builders' layers drawn together. Each decision is written where it applies.

1. **Plants and litter: a cost nobody saw.** The growth layer keeps its weeds 5 cm clear of every litter piece (a nearest-point question over all pieces). With the second round's 58,753 pieces this costs about 1.5 seconds on every plate: growth alone is +70 percent of a plate (3.65 s against 2.15 s), where its builder measured +1 to +6 percent with the first round's 6,439. Switched off (`growth.avoid_pieces_of.objects` = [] in the settings file) it costs +0.5 percent, but then 138 of 174 weeds (79 percent) stand within 5 cm of a litter piece (the line allows 3 percent) and the plant count doubles. **Decision: kept on**; a plate takes 1.5 s longer, which does not matter for a handful of stills, and no weed stands on a coal lump. **Fix round: built.** The clearance is now a look-up in a baked picture (`litter_dist`, section 12.3) instead of a search over every piece; the growth layer's share of the drawing time fell from +70 percent to a few percent, and 0 of 101 weeds (street) and 0 of 60 (lockout) stand within 5 cm of a litter piece's centre.
2. **Plants and puddles.** About 37 percent of the plants of the main plate stand inside puddles (38 percent of the plant dots with the first settings, 111 plants in view, 43 in a puddle; 36 percent, 32 of 88, with the final ones). Both like the low ground beside the gutter, and the plants cannot see the water layer's puddles (the puddle field is made inside the shader from a slow wobble, the ground's lowness and the relief). On wet pictures some flat green moss strings look as if they float. **Decision**: `growth.cushions_amount` 1.0 to 0.6 (the flat moss strings are the ones that read as floating; the weeds stay). This does not change the share that stands in puddles, it only makes fewer of them. **Fix round: fixed.** The water layer's puddle picture is drawn once from above and stamped into the pack as `above_water` (0 in a puddle, section 12.3); the plants already read that mask, so no plant root now stands in a puddle (0 of 157 on the main plate), and the checkers' pixel count (green blobs whose centre is in a puddle) fell from 39 to 19 percent (the rest are leaves leaning over a puddle's edge and reflections).
3. **The keep-clear strip covered every wall foot.** The growth builder found that no plant could stand at any wall foot. The cause was in the foundation's step finder: every up-facing face of the trim within 0.9 m of a door counted as a step tread (252 of the 504 faces found were more than 3 m up: sills, lintels, eaves, roof ridges; 28 more were 2.5 to 5 m long strips along the wall base). The keep-clear strip is 0.5 m wide around "steps", so it covered the whole outer half of every pavement. Fixed in the kit (two optional keys in the set's `geometry.steps`: `max_height_m` 0.8 and `max_extent_m` 2.0; `masks/ground_plan.py` reads them, a set that says nothing is unchanged), and the street's and lockout's packs were rebuilt. Share of wall-foot dots free of the keep-clear zone: 0 percent before, 35 percent (street) and 31 percent (lockout) now; only the doorstep strips and the door-to-kerb paths stay clear.
4. **Grime darkening the joints.** The ground film (`dirt`, slot A) darkens the sett colour before the JOINTS stage draws its dark dull joints, so joint contrast could fall. Measured with everything on: 21 of 22 lighting pictures pass the joint test (the street without the new parts: 20 of 22), with every dot counted 20 (before: 18), no harsh black grid (largest joint contrast 0.62, limit 0.75). **Decision**: the order stays (film in A, joints after, cracks in B after the joints and dull). The film was lowered from 0.6 to 0.4 (also to keep the wet shine, see 7).
5. **Cracks against shine.** A crack is visible mainly because it is duller than the wet setts around it. The `dull` dial of `groundcracks` at 0.6 gave the road a better wet-to-dry ratio but made the cracks hard to see (18 good marks on the main plate against 37 at 1.0). **Decision**: dull 1.0 (cracks win; the wet road is 2 to 4 percent less shiny in the glare light).
6. **Moss and weeds under litter heaps.** The habitat fields (`moss_site`, `weed_site`) have the litter rule inside them (moss is smothered earlier than weeds) and RUBBISH sits last in the chain, so litter lies on painted moss and the 3D weeds thin out under heaps. Measured: moss, weed, lichen and algae fields are exactly 0.0 in the crown, the traffic lanes and the keep-clear strips (street and lockout), and 0 plants stand there on any plate (plates: 195, 407, 330, 253 plants).
7. **The wet look.** Layers in slot A are wetted by the water layer, which is what the plan wanted, but every kit element's brightness wet-over-dry comes out above 1.0 on roads (the whole road is 1.4 to 3.7 times brighter wet because of the lamps' reflections, so a dull mark on it is still brighter wet than dry). The plan's line "every element at most 1.0" cannot be met by a ground element in that light; the report gives each element's wet/dry divided by its surface's own wet/dry as well (1.0 or less means the mark is duller than the surface it sits on). The road's wet/dry itself stays within 0.05 of before in 7 of the 10 pictures that have a dry twin.
8. **The water layer makes copies of the wall materials** (one per door layout) after the kit has read the set, so a layer put in afterwards would go into copies nobody uses. The walls builder patches this on the kit instance in `walls/apply_walls.py`. **Decision**: left there (the ground and growth layers do not meet copies); recommended to move into `Kit.materials_for` one day.
9. **The `paint` layer is OFF in the street.** It was never tuned: even at `paint_dark` 0.93 it made doors and window frames 12 to 21 percent darker, with the share of them under plate brightness 0.10 up by 11 points (the line allows 8). In the street's `apply.paint` the roles are emptied (they are kept under `roles_when_tuned`); a layer whose block names no role goes into no material.
10. **Steps, scrub strip and entry numbers agree** by construction: the ground film's scrub strip on the flags reads the same two shares as the steps layer (whitened 0.55, scrubbed 0.35) and the same one-number-per-door (`entry_rand`).
11. **Chimneys and roofs get their own value** (`stack_mult`, `roof_mult`), not a role multiplier: a chimney stack darkened by the street's plain film was crushed (the share under plate brightness 0.10 rose by 22 to 28 points). Final values 1.15 and 1.0.

---

## 4. Every layer, what it makes, how to switch it off

For each layer: what it makes in plain words, its slot, its roles in the street, and the dials that matter. The full dial list (range, default, the street's value, the courtyard's value, what it does) is in section 8. Every layer also has the six common dials: `amount` (the master dial), `seed` (moves where random things fall), `inflate_limit` (how many times wider than real a mark may be drawn before it fades into an average tone), `fade_start` and `fade_end` (metres: the distance over which fine detail fades to the layer's average tone, never to clean), `wet_follow` (how much it follows the wet state).

**Four ways to switch a layer off, from lightest to most complete:**
1. `w.set_layer_master('soot', 0)` (or `sw.set_master('soot', 0)`): the layer stays in the materials and gives back exactly what it was given (proved for every layer: the picture is within one step of 255 on at most 1 percent of dots).
2. `w.layer_off('soot')`: takes the layer's nodes out of every chain (same picture, faster to draw); `w.layer_on('soot')` puts it back.
3. In the settings file, `apply.<layer>.roles` = [] : the layer is never put in any material (how `paint` is off in the street). Cheapest to draw.
4. `w.remove()`: everything off.

The kit's own master dial (`w.set_master(x)`) multiplies every kit layer's `amount`. The earlier layers have their own: wetness (0 = a dry street), joints (strength), rubbish (amount).

### soot (slot A; walls, trims, colliery, chimneys, roofs)
The old coal-smoke crust. A general film (0.60 of the clean colour, pulled a quarter toward grey), darker under ledges and in reveals, with rain-washed PALE patches lifted above the film (on a street where 79 percent of the wall dots are already under plate brightness 0.10 a dark mark is lost, so the pattern is made from the light side). Main dials: `film_mult`, `sheltered_mult`, `washed_share`, `washed_pale`, `shade_wash` (how much shade keeps washed patches away), `edge_sharp`, `stack_mult`, `roof_mult`.
### runoff (A; walls, trims)
Pale streaks with dark edges below sills, ledges, caps, eaves and downpipe joints; a streak at both ends of a sill; long heavy leaks under some downpipes; a rust tint at iron joints. Main dials: `strength`, `width_dots`, `source_share`, `pair_share`, `leak_share`, `stain_value`. Draws nothing on a set whose walls have no wall sheets (the courtyard's plaster).
### foot (A; walls, trims, colliery)
The dusty splash band at the foot (taller at pipe feet, a dusty brown LIGHTER than the wall), a damp tide-mark on 45 percent of houses with white salt flecks, worn mortar and flaked bricks in the lowest 0.6 m. Main dials: `splash_strength`, `splash_pale`, `tide_share`, `salt_bloom`.
### steps (A; trims; found by the step masks)
55 percent of doors have a whitened step (pale frame, pale riser), 35 percent a scrubbed one, boots grey the middle, a worn dish, chipped nosings. Main dials: `whitened_share`, `scrubbed_share`, `frame_dots`.
### wallcracks (B; walls, trims)
A few cracks, never a net: the stepped mining crack on houses the set flags, wavy cracks near corners and openings, chips at corners, spalled patches near the foot; each with a pale dust lip so it reads on a dark wall; dull. Main dials: `crack_amount`, `stepped_cracks`, `corner_chips`.
### wallgrowth (C; walls, trims)
Painted moss (flat olive, lighter than the stone), a thin green-black algae film at drips and shaded feet, lichen (0 in the street). The street's moss amount is only 0.05: at 0.12 every wall foot and step was a green band. Main dials: `moss_amount`, `algae_amount`, `lichen_amount`.
### paint (A; OFF in the street)
Worn paint on doors, window frames and boards. Built and smoke-tested only. Main dials: `paint_dark`, `flake_share`, `door_scuff`.
### dirt (A; road, flags, kerbs, gutter stones)
Ground film (darker where it is damp, near walls), polish on the worn middle of the pavement, water marks, tar patches on the road, rust halos round iron feet, the fire drum's ring, the scrubbed strip in front of doors. Per surface kind the set says which of these each surface gets (`ground.role_dials`). Main dials: `film`, `polish`, `water_marks`, `rust_halo`, `tar_patches`, `scrub_strip`.
### groundcracks (B; flags, kerbs, setts)
Fine, broken and tilted flag cracks, chipped kerb corners and runs, disturbed sett patches with open joints and the odd missing sett. Main dials: `flag_cracks`, `kerb_chips`, `sett_disturb`, `crack_dots`, `crack_contrast`, `near_only`, `dull`.
### groundmoss (C; all ground kinds)
Moss ribbons in sett, flag and kerb joints (never more than 15 percent of the joint length), algae fans under downpipe outlets, liverwort patches, a far band that takes over from the 3D plants at distance. Main dials: `joint_share`, `algae_fan`, `ribbon_dots`, `far_band`.
### iron (A, straight before the Principled BSDF; iron roles)
Rust (lowers Metallic too), collars at pipe joints, shoe streaks, the foot ring of lamp posts, the fire drum's heat scale and soot. Main dials: `rust_cover`, `rust_height`, `collar_rust`, `metallic_drop`.
### growth (separate 3D pieces; ground targets)
Ten small kinds of plant (grass, dead grass, pearlwort, dandelion, plantain, groundsel, chickweed, shepherd's purse, toadflax, moss strings) laid only in the gutter strips, at the kerb foot and now at the wall foot between doorsteps, never on the crown, the traffic lanes, the doorstep strips, within 1 m of the fire or on a litter heap, 5 to 12 cm across in the first 18 m. Main dials: `weeds_amount`, `cushions_amount`, `weed_cover`, `gutter_tuft_share`, `wall_foot_share`, `distance`, `max_pieces`.

---

## 5. The looks

`presets/sooty_1926.json` is the street's look. Values changed from the plan, and why (the plan's own values are in the dial table of the plan; every change is in `integrated/work/tune_log.md` too):

| layer | dial | plan | now | why |
|---|---|---|---|---|
| soot | `film_mult` | 0.62 | 0.60 | the plan's film turned the plate's walls 23 percent darker (the line allows 12) |
| soot | `washed_share`, `washed_pale`, `edge_sharp` | 0.20, (new), 0.60 | 0.17, 0.8, 0.85 | washed patches lifted to read on dark walls |
| soot | `stack_mult`, `roof_mult` | 0.35, 0.82 | 1.15, 1.0 | chimneys and roofs were crushed at 0.8 |
| soot | `shade_wash` | (new) | 0.2 | the shaded terrace far down the street had hardly any washed patches |
| soot role values | trims `film_mult` / `sheltered_mult`, colliery `film_mult` | 0.8 | 1.4 / 1.75, 1.65 | trims and the colliery were over-darkened |
| runoff | `strength`, `inflate_limit`, `source_share` | 0.55, 6, 0.7 | 1.0, 12, 0.8 | the walls are seen almost edge-on and very dark |
| foot | `splash_strength`, `splash_pale` | 0.5, (new) | 0.9, 0.9 | a dusty brown lighter than the wall, not dark mud |
| wallgrowth | `moss_amount` | 0.4 | 0.05 | a green band at every wall foot otherwise |
| wallcracks | `crack_amount`, `corner_chips` | 0.3, 0.4 | 0.5, 0.5 | more visible at plate size |
| dirt | `film`, `polish_lift` | 0.6, 0.05 | 0.4, 0 | joints and the wet shine (section 3.2, items 4 and 7) |
| groundcracks | `crack_dots`, `crack_contrast`, `near_only`, `site_bias` | 3.5, 0.11, 15, 0.6 | 4.5, 0.16, 20, 0.9 | the cracks were hardly visible at plate size |
| groundmoss | `ribbon_dots` | 4 | 6 | moss ribbons too thin to read |
| iron | `rust_cover` | 0.35 | 0.5 | lamp posts and pipes should rust visibly |
| growth | `cushions_amount` | 1.0 | 0.6 | section 3.2, item 2 |
| set: steps | `geometry.steps.max_height_m`, `max_extent_m` | none | 0.8, 2.0 | section 3.2, item 3 |
| *fix round* soot | `film_mult`, `washed_share`, `washed_pale`, `edge_sharp`, `grey_pull`, `pale_warm` | 0.60, 0.17, 0.8, 0.85, 0.25, (new) | 0.80, 0.07, 0.5, 0.55, 0.10, 1.0 | the pale panels and the cold grey cast on the red brick (section 12.1); the film goes back up because fewer pale patches means a darker average wall |
| *fix round* set: soot role values | trims / colliery `film_mult` | 1.4 / 1.65 | 1.2 / 1.25 | so that trims and the colliery keep about the film they had under the new 0.80 |
| *fix round* steps | `white_cream`, `white_value` | (new) | 1.0, 0.85 | whitened steps cream, not blue-white |
| *fix round* dirt | `ring_pale`, `dip_dark`, `film_max_share` | (new), (new), 0.25 | 0.0, 0.12, 0.15 | no bright arcs from the water marks; smaller film patches |
| *fix round* groundcracks | `open_joint_share`, `open_depth_mm`, `sett_disturb` | 0.14, (new), 0.7 | 0.07, 0.8, 0.35 | fewer sett cracks, no pale hairline along the joint |
| *fix round* growth | `colour_gain`, `colour_sat`, `cushions_amount`, `dead_grass_share`, `weed_cover`, `gutter_tuft_share` | 1.0, (new), 0.6, 0.15, 0.01, 0.05 | 0.55, 0.85, 0.3, 0.08, 0.02, 0.10 | plants 4 to 5 times lifted instead of 8, duller, half the flat moss strings, fewer pale dead-grass tufts, more weeds to make up for the ones kept out of puddles and off litter |
| *fix round* foot, runoff | `salt_bloom`; `width_dots`, `stain_value`, `iron_rust`, `leak_share`, `source_share`, `pair_share` | 0.02; 10, 0.9, 0.5, 0.15, 0.8, 0.8 | 0.008; 14, 1.0, 0.9, 0.3, 0.9, 1.0 | fewer white flecks at the wall foot; wider, rust-coloured run-off |

`mossy_courtyard_kept` and `mossy_courtyard_neglected` are unchanged from the plan's first guess, except that each now carries the growth layer's courtyard values (`colour_gain` 0.15, `colour_sat` 1.2, `existing_avoid` 0.7, `piece_inflate_limit` 3): the courtyard is in full light, so it takes out the lift that makes the street's plants readable under dusk lamps. Nothing was tuned on the courtyard.

A new look: copy a preset, change dial values under `layers.<layer>`. It may also carry `readable`, `period`, `forbidden`, `hue_allowed` and `green_layers` tables that the measuring scripts read.

---

## 6. Adding a new set, step by step (the next one is the Japanese courtyard; its file already exists and is the shortest real example)

A set is one settings file `sets/<set id>.json`, one or more looks in `presets/`, and a mask pack made from the scene by `masks/reader.py`. No kit code changes.

1. **Copy a settings file** (`sets/japanese_courtyard.json` is the shorter one) and change `id`, `title`, `scenes`. A scene entry: `id`, `file` (the saved .blend; never saved over), `default_camera`, `read_only: true`, and `adds_roles` for a scene with extra objects.
2. **`plate`**: size, `painter_scale`, samples. Every mark is sized in plate dots, so the plate size decides how big a crack is drawn.
3. **`roles`**: the kinds of surface. A role is `family.kind` (`wall.masonry`, `ground.gravel`, `stone.natural`, `roof.tile`, `timber.frame` ...) found by object-name regular expressions (`objects`), collections, material regular expressions (`materials`) or custom properties (`custom_props`). Every object may sit in only one role (the loader checks). Two names matter to the code: a role called `chimney...` and roles called `roof...` get their own soot class value. Everything else is just a name the rest of the file refers to.
4. **`never`**: objects and materials no layer may touch (glass, glow, sky, leaves, water). Anything that emits light is skipped automatically.
5. **`apply`**: for each layer, `roles` (which roles it goes on; [] = off) and, if needed, `role_dials` (per-role multipliers of a layer's dials, e.g. less soot on trims). `apply.growth` names `targets` (the roles plants stand on) and `piece_sets`.
6. **`geometry`**: the ground roles and the picture bounds (`geometry.ground.roles`, `bounds`, `dot_m`), the roles that are solid walls (`solids_for_wall_dist`), the step finder (`steps`: which role, `near_entrances`, `within_m`, `min_height_m`, and `max_height_m`, `max_extent_m` when trim also has sills and long courses), the wall sheets (`frames`: one picture per wall mesh), the ledges that drip (`ledges`), the entrances (`entrances.role`: an object per door; used for doorsteps and keep-clear), and `water` (level z) when there is a pond.
7. **`footfall`** (who walks where: bands, lines, polylines, rectangles, "door to the nearest kerb") and **`keep_clear`** (where no plant may stand: around doors, round a fire, on raked gravel, wherever footfall is high).
8. **`shade`** (`declared` sun side, `openness`, `year_sun` at a latitude, or a mix), **`dampness`** (weights of wall foot, drips, water, low ground, shelter), **`habitat`** (weights of the four growth fields; `lichen.enabled`).
9. **`ground`** (the ground layers' per-surface choices: `role_dials` say which element each surface kind gets; `rings`; `readable`) and **`growth`** (the plants' choices: `targets.align_normal`, `piece_sets`, `avoid_pieces_of`, `gutter_side`, `wall_foot`, `realise_targets`).
10. **`legacy`** only if the set already has earlier layers (the street's WETNESS, JOINTS, RUBBISH); a set without them has `null`.
11. **`hook`**: `adapters` for materials that are shader groups with no Principled box, and the glow rule.
12. **`cameras`, `lighting`, `test_set`**: the plate camera(s), the lighting rigs as data (rigs A to E are the street's), the list of test pictures, the joint pass line. Not needed to put the kit on, only to measure it.
13. **`looks`**: the default look and the allowed ones.
14. **Check it loads**: `python3 -I -c "from apply import settings; s = settings.load_set('<set id>'); print(settings.validate_set(s, check_files=False))"` from the kit folder. Errors (an unknown role, a regular expression that does not compile) stop everything; warnings (a pattern that matches nothing) are listed.
15. **Make the mask pack** (once per scene file, about 30 to 80 seconds; the rented machine is not needed):
    `blender -b --disable-autoexec <scene.blend> --python masks/reader.py -- <set id> <scene id> masks/packs/<set id>/<scene id> <raw folder>`
    then, if the set has litter, `python3 -I masks/make_pack.py <set id> <scene id> <raw folder> --rubbish <picture>`. **Fix round:** a set that has the earlier water layer and litter layer then draws and stamps two more pictures: `python3 -I harness/make_plan_pictures.py <set id> <scene id> <work folder>` (rented machine, about 40 s; section 12.3), so that plants stay out of puddles and off litter. `python3 -I masks/check_pack.py <set id> <scene id>` checks the shade side. `masks/CONTRACT.md` lists every mask; `masks/NOT_DONE.md` lists what is missing.
16. **Smoke test** inside Blender: `aw.apply('<set id>', '<look id>')`, `w.report()` (look at `problems` and `skipped`), `w.remove()`. Then `python3 -I harness/lint_no_set_names.py` (must say 0 hits: it fails if kit code names anything from a settings file) and `harness/test_weathering_entry.py` on the rented machine.
17. **Draw and tune**: `harness/run_testset.py`, then the measuring scripts in section 9. Tune dials in the look, never kit code. A fault in a layer goes into a `REQUESTS.md` note for that layer's folder.

What each next set must decide that the street could not test: whether the kit's moss extends or matches the add-on's existing moss (`habitat.moss.extend_existing`, `growth.existing_avoid`), roof tiles that are instances (`apply.growth.realise_instances`), wall sheets for plaster walls (the courtyard has none, so `runoff` draws nothing there), its own plate camera and lighting rigs, and whether the painter keeps moss and streaks on light plaster.

---

## 7. How it is measured (the scripts, and the pass line each one is)

All pictures are drawn on the rented machine (the street file: 74 lighting and close pictures; the lockout file: 19; plates 1536 x 2730 at 48 samples) and brought back; the measuring scripts are plain Python on those pictures. "Before" is always the earlier layers alone (the second painter round's), drawn in the same run, so nothing but the new parts differs.

| pass line | what it asks | script (in `harness/`, run by `integrated/work/measure_all.py`) |
|---|---|---|
| P1 sett joints still pass | with puddle and litter dots left out and the kit's own dots left in: at least 21 of 22 lighting pictures pass the joint test, nothing that passed before fails, no harsh black grid (joint contrast at most 0.75) | `measure_joints.py` |
| P2 the wet look is kept | wet-over-dry brightness of road, pavement and walls within 0.05 of before, puddle cover within 2 points, shine highlights within 85 to 115 percent, every kit element no brighter wet than dry | `measure_wet.py` |
| P3 readable at the painter's size | each element's marks, at the painter's 0.45 scale, at least 60 percent good, at most 15 percent lost, at most 15 percent crushed, and a minimum number of good marks | `measure_readable.py` (+ `plate_detail_check.py`) |
| P4 nothing wrong for 1926 | no forbidden thing in the look, each element's share inside its period cap, no orange or yellow or bright green outside rust and plants | `measure_period.py`, `coverage.py` |
| P5 the street is not one dark mush | against before, per surface class on each plate: M1 at most 25 percent of the class darkened by a third, M2 the share under plate brightness 0.10 rises by at most 8 points (3 on walls and trims), M3 mean brightness drops by at most 12 percent, M4 spread kept at 85 percent, M5 kit/before brightness in the 5-10, 10-20 and 20-40 m bands stays between 0.80 and 1.00 and within 0.08 band to band | `measure_mush.py` |
| P6 no plants on the crown or lanes | the growth fields are exactly 0 there, no plant stands in those zones, near the fire or on a doorstep, at most 3 percent of weeds within 5 cm of litter | `measure_zones.py` (via `integrated/work/measure_p6.py`) |
| P7 the same drawing time within +30 percent | plate time at most 1.3 times before; the first picture after putting the kit on at most 1.5 times before and never over 40 s | `measure_time.py`, `integrated/work/run_time_*.py` |
| P8 master dial 0 changes nothing, remove restores | each layer at 0 equals the input; all at 0 equals before; remove gives the scene back | `selftests.py` per builder, and `harness/test_weathering_entry.py` for the whole door |
| P9 reuse | the lint finds 0 set names in kit code; both settings files validate; the courtyard takes the same call | `lint_no_set_names.py`, `test_weathering_entry.py` on the courtyard |


## 8. Every dial (range, default, the street's value, the courtyard's value, what it does)

Generated from the dial table of the finished kit. Every layer also has the six common dials listed first. "street" is `presets/sooty_1926.json`, "courtyard" is `presets/mossy_courtyard_kept.json`. Names are Title Case on the node group (`Film Mult`).

### soot  (slot A; roles in the plan: wall.masonry, wall.trim, wall.industrial, chimney, roof.*)

| dial | range | default | street | courtyard | what it does |
|---|---|---|---|---|---|
| `amount` | 0 to 2  | 1 | 1 | 1 | Master dial of the layer. 0 = the surface is exactly as it was before the layer. 1 = normal. 2 = double. |
| `seed` | 0 to 100  | 0 | 0 | 0 | Moves where things fall; the same seed gives the same picture every time. (The kit also gives every object its own seed.) |
| `inflate_limit` | 1 to 12  | 6 | 8 | 6 | A mark may be drawn at most this many times wider than real so that it stays visible at distance; beyond that it fades into an average tone. |
| `fade_start` | 5 to 40 m | 12 | 12 | 12 | Metres from the camera where fine detail starts to give way to the average tone. |
| `fade_end` | 15 to 80 m | 40 | 40 | 40 | Metres from the camera where fine detail has fully given way to the average tone (never to "clean"). |
| `wet_follow` | 0 to 1  | 1 | 1 | 1 | How much the layer follows the Wet Mask where a wetness layer exists (darker and glossier when wet). 0 = ignores wetness. |
| `film_mult` | 0.3 to 1  | 0.8 | 0.8 | 0.97 | Colour multiplier of the general film on the clean surface (brick 0.50 to 0.65 in 1926). |
| `sheltered_mult` | 0.2 to 1  | 0.6 | 0.5 | 0.85 | Multiplier where rain cannot reach (under sills, eaves, in reveals). |
| `washed_mult` | 0.5 to 1.2  | 0.95 | 1 | 1 | Multiplier where rain washes (sill tops, the windward upper wall). |
| `washed_share` | 0 to 0.6  | 0.2 | 0.07 | 0.3 | Share of wall area that is rain-washed (15 to 25 % in 1926). |
| `floor_mult` | 0.2 to 0.8  | 0.4 | 0.3 | 0.6 | No dot may go below this multiple of its clean colour (keeps the film curve from crushing it). |
| `grey_pull` | 0 to 1  | 0.2 | 0.1 | 0.15 | How far colour is pulled toward grey (25 to 35 % in 1926). |
| `mortar_soot` | 0 to 1  | 0.3 | 0.4 | 0.1 | Extra darkening in mortar hollows (soot sits in hollows first). |
| `mottle_size` | 0.2 to 3 m | 1 | 0.9 | 1.2 | Size of the slow mottling. |
| `mottle_contrast` | 0 to 1  | 0.4 | 0.5 | 0.3 | How strong the mottling is. |
| `edge_sharp` | 0 to 1  | 0.5 | 0.55 | 0.4 | How crisp the line is between washed and sheltered (a clean line under a sill). |
| `stack_mult` | 0.2 to 1  | 0.6 | 1.15 | 1 | Multiplier on chimney stacks (blackest in a coal town). |
| `roof_mult` | 0.5 to 1  | 0.9 | 1 | 0.95 | Multiplier on roof surfaces. |
| `base_lift` | 0 to 0.5  | 0 | 0 | 0 | LAST-RESORT dial: lifts the whole wall colour so that a pattern has room above the film-black zone. Off unless the integrator proves it is needed and says so. |
| `mottle_stretch` | 1 to 4  | 2 | 3 |  | How much taller than wide the soot mottling is (soot clouds run in columns: 1.8 to 2.5). |
| `patch_min_dots` | 8 to 40 dots | 15 |  |  | Smallest soot or washed patch, in plate dots (patches of 15 dots or more survive the painter). |
| `rough_gain` | 0 to 0.3  | 0.1 |  |  | How much duller (rougher) the sooted surface becomes; soot is a dry crust. |
| `shade_wash` | 0 to 1  | 0.6 | 0.2 |  | How much shade keeps the rain-washed patches away (0 = shade makes no difference, 1 = none in full shade). |
| `washed_pale` | 0 to 1  | 0.5 | 0.5 |  | Pale-first: how much the washed patches are lifted above the surrounding film, so that they read on a dark wall (0 = only the washed_mult value). |
| `pale_warm` | 0 to 1 | 0 | 1.0 |  | Colour of the washed patches: 0 = a neutral pale stone (reads grey-blue under a night sky), 1 = a warm buff stone that keeps the warm hue of brick. (fix round) |

### runoff  (slot A; roles in the plan: wall.masonry, wall.trim (iron-sourced streaks use iron objects as sources))

| dial | range | default | street | courtyard | what it does |
|---|---|---|---|---|---|
| `amount` | 0 to 2  | 1 | 1 | 1 | Master dial of the layer. 0 = the surface is exactly as it was before the layer. 1 = normal. 2 = double. |
| `seed` | 0 to 100  | 0 | 0 | 0 | Moves where things fall; the same seed gives the same picture every time. (The kit also gives every object its own seed.) |
| `inflate_limit` | 1 to 12  | 6 | 12 | 6 | A mark may be drawn at most this many times wider than real so that it stays visible at distance; beyond that it fades into an average tone. |
| `fade_start` | 5 to 40 m | 12 | 12 | 12 | Metres from the camera where fine detail starts to give way to the average tone. |
| `fade_end` | 15 to 80 m | 40 | 40 | 40 | Metres from the camera where fine detail has fully given way to the average tone (never to "clean"). |
| `wet_follow` | 0 to 1  | 1 | 1 | 1 | How much the layer follows the Wet Mask where a wetness layer exists (darker and glossier when wet). 0 = ignores wetness. |
| `strength` | 0 to 1  | 0.4 | 1 | 0.5 | Contrast of the streaks. |
| `tone` | -1 to 1  | 0 | -0.5 | 0.7 | -1 = pale washed stripe, +1 = dark stain. 1926 sooty walls: pale stripes with dark tide-lines. Courtyard plaster: dark grey-green streaks. |
| `edge_dark` | 0 to 1  | 0.3 | 0.5 | 0.2 | Dark tide-line along the streak edges. |
| `width_dots` | 4 to 24  | 8 | 14 | 10 | Smallest streak width in plate dots (the layer widens a streak with distance up to Inflate Limit). |
| `length_mult` | 0.3 to 3  | 1 | 1 | 1.2 | Length of every streak. |
| `ragged` | 0 to 1  | 0.5 | 0.6 | 0.5 | Ragged sides and a stretched-down shape. |
| `source_share` | 0 to 1  | 0.6 | 0.9 | 0.8 | Share of sills, ledges and cap edges that carry a streak pair (60 to 80 % in 1926). |
| `leak_share` | 0 to 0.5  | 0.1 | 0.3 | 0 | Share of downpipes that leak heavily and carry a long streak. |
| `leak_length` | 0.3 to 1.5 m | 0.8 | 0.9 | 0.8 | Length of a heavy leak streak. |
| `iron_rust` | 0 to 1  | 0.3 | 0.9 | 0 | How orange (rust) a streak is when its source is an iron joint or bracket. |
| `eave_streaks` | 0 to 1  | 0.3 | 0.5 | 0.7 | Streaks hanging from eave lines, gutter ends and cap overhangs. |
| `pitch_mult` | 0.5 to 3  | 1 |  |  | Spacing of the streaks inside a run-off zone (1 = a streak about every 0.25 m). |
| `pair_share` | 0 to 1  | 0.5 | 1.0 |  | How strongly the two edges of every ledge (the sill ends) carry a streak of their own. |
| `stain_value` | 0 to 1  | 0.5 | 1.0 |  | How much brighter than its surround a pale stripe is made, 1 = the strongest allowed (pale-first on dark walls). |

### foot  (slot A; roles in the plan: wall.masonry, wall.trim, wall.industrial)

| dial | range | default | street | courtyard | what it does |
|---|---|---|---|---|---|
| `amount` | 0 to 2  | 1 | 1 | 1 | Master dial of the layer. 0 = the surface is exactly as it was before the layer. 1 = normal. 2 = double. |
| `seed` | 0 to 100  | 0 | 0 | 0 | Moves where things fall; the same seed gives the same picture every time. (The kit also gives every object its own seed.) |
| `inflate_limit` | 1 to 12  | 6 | 8 | 6 | A mark may be drawn at most this many times wider than real so that it stays visible at distance; beyond that it fades into an average tone. |
| `fade_start` | 5 to 40 m | 12 | 12 | 12 | Metres from the camera where fine detail starts to give way to the average tone. |
| `fade_end` | 15 to 80 m | 40 | 40 | 40 | Metres from the camera where fine detail has fully given way to the average tone (never to "clean"). |
| `wet_follow` | 0 to 1  | 1 | 1 | 1 | How much the layer follows the Wet Mask where a wetness layer exists (darker and glossier when wet). 0 = ignores wetness. |
| `splash_height` | 0.1 to 0.6 m | 0.25 | 0.28 | 0.3 | Height of the dirt splash band at the wall foot (15 to 35 cm in 1926). |
| `splash_strength` | 0 to 1  | 0.4 | 0.9 | 0.35 | How dark the band is at the ground line. |
| `splash_ragged` | 0 to 1  | 0.6 | 0.7 | 0.6 | Ragged top edge of splash dots and short upward fingers. |
| `finger_height` | 0 to 0.2 m | 0.08 | 0.1 | 0.1 | Height of the splash fingers above the band. |
| `pipe_foot_boost` | 0 to 2  | 1 | 1.4 | 0 | Extra heavy splash and damp where a downpipe ends. |
| `tide_share` | 0 to 1  | 0.3 | 0.45 | 0.15 | Share of house lengths that carry a damp tide-mark (older rows only). |
| `tide_height` | 0.3 to 1.3 m | 0.7 | 0.8 | 0.5 | Ragged top of the damp tide-mark. |
| `tide_strength` | 0 to 1  | 0.3 | 0.4 | 0.25 | Darkening inside the tide-mark. |
| `tide_green` | 0 to 1  | 0.2 | 0.3 | 0.4 | How green the damp zone is. |
| `salt_bloom` | 0 to 0.1  | 0.02 | 0.008 | 0.04 | Share of the band covered by white salts along its top. |
| `mortar_wear` | 0 to 1  | 0.4 | 0.5 | 0.2 | Recessed, eroded mortar in the lowest 0.6 m. |
| `spall_share` | 0 to 0.2  | 0.05 | 0.07 | 0.04 | Share of bricks or blocks with a flaked face near the foot. |
| `wear_height` | 0.2 to 0.9 m | 0.5 | 0.6 | 0.4 | How high mortar wear and spalls reach. |
| `splash_pale` | 0 to 1  | 0.5 | 0.9 |  | Pale-first: 0 = dark mud splash, 1 = pale dust splash (a dusty brown lighter than a sooted wall, so the band reads on a dark wall). |
| `band_min_dots` | 8 to 40 dots | 15 |  |  | Smallest band height in plate dots (the band is drawn taller than real when the wall is far). |
| `salt_dots` | 3 to 16 dots | 6 |  |  | Smallest salt fleck in plate dots. |

### steps  (slot A; roles in the plan: wall.trim (the steps are found by the step masks, not by object))

| dial | range | default | street | courtyard | what it does |
|---|---|---|---|---|---|
| `amount` | 0 to 2  | 1 | 1 | 1 | Master dial of the layer. 0 = the surface is exactly as it was before the layer. 1 = normal. 2 = double. |
| `seed` | 0 to 100  | 0 | 0 | 0 | Moves where things fall; the same seed gives the same picture every time. (The kit also gives every object its own seed.) |
| `inflate_limit` | 1 to 12  | 6 | 6 | 6 | A mark may be drawn at most this many times wider than real so that it stays visible at distance; beyond that it fades into an average tone. |
| `fade_start` | 5 to 40 m | 12 | 12 | 12 | Metres from the camera where fine detail starts to give way to the average tone. |
| `fade_end` | 15 to 80 m | 40 | 40 | 40 | Metres from the camera where fine detail has fully given way to the average tone (never to "clean"). |
| `wet_follow` | 0 to 1  | 1 | 1 | 1 | How much the layer follows the Wet Mask where a wetness layer exists (darker and glossier when wet). 0 = ignores wetness. |
| `whitened_share` | 0 to 1  | 0.5 | 0.55 | 0 | Share of doorsteps that are whitened or donkey-stoned (40 to 70 %; medium confidence for Durham). |
| `scrubbed_share` | 0 to 1  | 0.3 | 0.35 | 0 | Share that are only scrubbed pale. |
| `frame_m` | 0.03 to 0.12 m | 0.06 | 0.07 | 0.07 | Real width of the white frame along nosing and riser (4 to 10 cm). |
| `frame_dots` | 4 to 20  | 8 | 8 | 8 | Smallest frame width in plate dots (widened with distance up to Inflate Limit). |
| `boot_grey` | 0 to 1  | 0.3 | 0.3 | 0.3 | Boots grey the centre of the tread (30 %). |
| `dish_depth` | 0 to 0.012 m | 0.004 | 0.005 | 0.003 | Depth of the worn dish in the tread (relief, faded with distance). |
| `nosing_chips` | 0 to 1  | 0.3 | 0.3 | 0.2 | Share of steps with a chipped nosing or corner. |
| `wear_polish` | 0 to 1  | 0.4 | 0.5 | 0.2 | Polish of the worn centre. |
| `tread_pale` | 0 to 1  | 0.5 |  |  | How pale a scrubbed (not whitened) step is. |
| `chip_m` | 0.02 to 0.12 m | 0.05 |  |  | Size of a chipped nosing. |
| `riser_share` | 0 to 1  | 0.8 |  |  | How much of the whitening or scrubbing also goes on the riser and the foot of the doorway round the step. |
| `white_cream` | 0 to 1 | 0 | 1.0 |  | Colour of whitened stone: 0 = a cold near-white, 1 = a warm cream (donkey stone; a cold white reads blue-white under a night sky). (fix round) |
| `white_value` | 0.5 to 1.2 | 1 | 0.85 |  | Brightness of whitened stone against the colour chosen by white_cream (below 1 so it does not read as plastic). (fix round) |

### wallcracks  (slot B; roles in the plan: wall.masonry, wall.trim, wall.plaster)

| dial | range | default | street | courtyard | what it does |
|---|---|---|---|---|---|
| `amount` | 0 to 2  | 1 | 1 | 1 | Master dial of the layer. 0 = the surface is exactly as it was before the layer. 1 = normal. 2 = double. |
| `seed` | 0 to 100  | 0 | 0 | 0 | Moves where things fall; the same seed gives the same picture every time. (The kit also gives every object its own seed.) |
| `inflate_limit` | 1 to 12  | 6 | 8 | 6 | A mark may be drawn at most this many times wider than real so that it stays visible at distance; beyond that it fades into an average tone. |
| `fade_start` | 5 to 40 m | 12 | 12 | 12 | Metres from the camera where fine detail starts to give way to the average tone. |
| `fade_end` | 15 to 80 m | 40 | 40 | 40 | Metres from the camera where fine detail has fully given way to the average tone (never to "clean"). |
| `wet_follow` | 0 to 1  | 1 | 1 | 1 | How much the layer follows the Wet Mask where a wetness layer exists (darker and glossier when wet). 0 = ignores wetness. |
| `crack_amount` | 0 to 2  | 0.3 | 0.5 | 0.5 | How many cracks (the master Amount scales it too). |
| `crack_dots` | 2 to 8  | 3.5 | 3.5 | 3.5 | Smallest crack width in plate dots (3 dots needs contrast 0.11). |
| `crack_contrast` | 0.04 to 0.2  | 0.11 | 0.11 | 0.11 | Smallest crack contrast against the surround. |
| `stepped_cracks` | 0 to 1  | 0 | 1 | 0 | Stepped mining cracks on the houses the set file flags (1 or 2 of 28). |
| `corner_chips` | 0 to 1  | 0.3 | 0.5 | 0.5 | Chips at wall corners and opening corners. |
| `chip_cm` | 2 to 12  | 5 | 5 | 6 | Chip size in centimetres (chips of about 5 cm and bigger read). |
| `plaster_cracks` | 0 to 1  | 0 | 0 | 0.5 | Map cracks and corner cracks in plaster. |
| `spall_patches` | 0 to 1  | 0.15 | 0.2 | 0.3 | Spalled patches near the foot. |
| `near_only` | 6 to 30 m | 15 | 15 | 12 | Cracks fade out beyond this distance (the painter invents its own texture there). |
| `slope_mm` | 0 to 5  | 1.5 | 1.5 | 1.5 | Real slope of a crack edge so a lamp lights one side. |
| `dull` | 0 to 1  | 1 | 1 | 1 | Cracks are dull: roughness back to 0.9, shine cut 35 %, water film cut 45 %. |
| `chip_pale` | 0 to 1  | 0.6 |  |  | Chips show fresh, paler stone (pale-first on dark walls). |
| `step_cm` | 6 to 40 cm | 15 |  |  | Height of one step of a stepped mining crack (about two brick courses). |
| `crack_pale` | 0 to 1  | 0.5 |  |  | Pale dust lip along a crack so that it reads on a dark wall. |

### wallgrowth  (slot C; roles in the plan: wall.masonry, wall.trim, wall.plaster, roof.tile (painted moss, algae, lichen))

| dial | range | default | street | courtyard | what it does |
|---|---|---|---|---|---|
| `amount` | 0 to 2  | 1 | 1 | 1 | Master dial of the layer. 0 = the surface is exactly as it was before the layer. 1 = normal. 2 = double. |
| `seed` | 0 to 100  | 0 | 0 | 0 | Moves where things fall; the same seed gives the same picture every time. (The kit also gives every object its own seed.) |
| `inflate_limit` | 1 to 12  | 6 | 8 | 6 | A mark may be drawn at most this many times wider than real so that it stays visible at distance; beyond that it fades into an average tone. |
| `fade_start` | 5 to 40 m | 12 | 12 | 12 | Metres from the camera where fine detail starts to give way to the average tone. |
| `fade_end` | 15 to 80 m | 40 | 40 | 40 | Metres from the camera where fine detail has fully given way to the average tone (never to "clean"). |
| `wet_follow` | 0 to 1  | 1 | 1 | 1 | How much the layer follows the Wet Mask where a wetness layer exists (darker and glossier when wet). 0 = ignores wetness. |
| `moss_amount` | 0 to 2  | 0.5 | 0.05 | 1.2 | Painted moss at wall feet, drips, copings. |
| `algae_amount` | 0 to 2  | 0.8 | 0.6 | 1 | Green-black algae film at pipe outlets and shaded feet. |
| `lichen_amount` | 0 to 2  | 0 | 0 | 0.6 | Lichen. 1926 coal town: NONE (the smoke killed it). Courtyard: sparse colonies. |
| `moss_height` | 0.1 to 1 m | 0.3 | 0.35 | 0.5 | How high up a wall moss may reach from the foot. |
| `patch_dots` | 8 to 40  | 15 | 15 | 15 | Smallest moss patch width in plate dots (patches of 15 dots or more survive the painter). |
| `drip_moss` | 0 to 1  | 0.3 | 0.4 | 0.5 | Moss below run-off lines. |
| `cap_moss` | 0 to 1  | 0.3 | 0.3 | 0.6 | Moss along copings and wall caps. |
| `roof_moss` | 0 to 1  | 0 | 0 | 0.4 | Moss on roof surfaces (probably very little in 1926). |
| `tone_steps` | 3 to 6  | 5 | 5 | 4 | Number of flat painted tones in a moss patch. |
| `clump_stretch` | 1 to 3  | 1.8 | 1.8 | 1.5 | How much taller than wide a clump is (drip shape). |
| `relief` | 0 to 0.02 m | 0.005 | 0.006 | 0.008 | Height of moss relief (a bump on the incoming normal, faded with distance). |
| `lichen_dots` | 4 to 16  | 8 | 8 | 8 | Lichen disc size in plate dots. |
| `brightness_floor` | 0.12 to 0.4  | 0.25 | 0.25 | 0.25 | Lowest plate brightness of a moss patch (it must stay lighter than the stone and above the film-black zone). |
| `moss_value` | 0.1 to 1  | 0.35 | 0.2 |  | Albedo of the lightest moss tone (a number; the moss is lighter than the stone, never below brightness_floor). |
| `algae_strength` | 0 to 1  | 0.5 | 0.4 |  | How dark the green-black algae film is on its damp, shaded places. |
| `hue` | 70 to 140 deg | 100 |  |  | Hue of moss in degrees (85 to 120 survives the painter as green). |
| `saturation` | 0.3 to 0.9  | 0.55 | 0.5 |  | Saturation of moss (0.45 or more so that the painter keeps it green). |

### paint  (slot A; roles in the plan: timber.paint (doors, window frames, fascia))

| dial | range | default | street | courtyard | what it does |
|---|---|---|---|---|---|
| `amount` | 0 to 2  | 1 | 1 | 1 | Master dial of the layer. 0 = the surface is exactly as it was before the layer. 1 = normal. 2 = double. |
| `seed` | 0 to 100  | 0 | 0 | 0 | Moves where things fall; the same seed gives the same picture every time. (The kit also gives every object its own seed.) |
| `inflate_limit` | 1 to 12  | 6 | 6 | 6 | A mark may be drawn at most this many times wider than real so that it stays visible at distance; beyond that it fades into an average tone. |
| `fade_start` | 5 to 40 m | 12 | 12 | 12 | Metres from the camera where fine detail starts to give way to the average tone. |
| `fade_end` | 15 to 80 m | 40 | 40 | 40 | Metres from the camera where fine detail has fully given way to the average tone (never to "clean"). |
| `wet_follow` | 0 to 1  | 1 | 1 | 1 | How much the layer follows the Wet Mask where a wetness layer exists (darker and glossier when wet). 0 = ignores wetness. |
| `paint_dark` | 0.5 to 1  | 0.85 | 0.93 | 0.9 | General darkening of paint (0.70 to 0.85 in 1926). |
| `flake_share` | 0 to 0.5  | 0.15 | 0.2 | 0 | Share of painted area that has lost flakes. |
| `door_scuff` | 0.1 to 0.5 m | 0.25 | 0.3 | 0.25 | Height of kicked scuffs at the foot of doors (bare grey wood). |
| `latch_grease` | 0 to 1  | 0.4 | 0.4 | 0.2 | Dark hand-grease patch at the latch. |
| `gloss_loss` | 0 to 1  | 0.4 | 0.5 | 0.3 | How much the paint has lost its gloss. |
| `grain_dots` | 3 to 16 dots | 6 |  |  | Smallest flake width in plate dots. |

### dirt  (slot A; roles in the plan: ground.sett, ground.flag, ground.channel, ground.kerb (gravel and earth in other sets))

| dial | range | default | street | courtyard | what it does |
|---|---|---|---|---|---|
| `amount` | 0 to 2  | 1 | 1 | 1 | Master dial of the layer. 0 = the surface is exactly as it was before the layer. 1 = normal. 2 = double. |
| `seed` | 0 to 100  | 0 | 0 | 0 | Moves where things fall; the same seed gives the same picture every time. (The kit also gives every object its own seed.) |
| `inflate_limit` | 1 to 12  | 6 | 6 | 6 | A mark may be drawn at most this many times wider than real so that it stays visible at distance; beyond that it fades into an average tone. |
| `fade_start` | 5 to 40 m | 12 | 12 | 12 | Metres from the camera where fine detail starts to give way to the average tone. |
| `fade_end` | 15 to 80 m | 40 | 40 | 40 | Metres from the camera where fine detail has fully given way to the average tone (never to "clean"). |
| `wet_follow` | 0 to 1  | 1 | 1 | 1 | How much the layer follows the Wet Mask where a wetness layer exists (darker and glossier when wet). 0 = ignores wetness. |
| `film` | 0 to 2  | 0.5 | 0.4 | 0.4 | Broad soft film of soot and dust, 0.5 to 3 m patches. NOT ash or coal dust (the rubbish layer has those). |
| `film_scale` | 0.5 to 4 m | 1.6 | 1.6 | 1.6 | Patch size of the film. |
| `film_darkness` | 0 to 0.6  | 0.25 | 0.3 | 0.2 | Darkening of the film (at most about one third). |
| `film_max_share` | 0 to 0.5  | 0.25 | 0.15 | 0.25 | Ceiling on the share of a surface the film may darken by a third or more. |
| `film_near_walls` | 0 to 1  | 1 | 0.5 | 1 | Keeps the film off the places the rubbish layer already dirties (wall foot, gutter strip). 1 = film everywhere; 0.5 = half strength there. |
| `polish` | 0 to 1  | 0.4 | 0.5 | 0 | Traffic polish: worn lanes are lighter and smoother. |
| `polish_lift` | 0 to 0.2  | 0.05 | 0 | 0.05 | Brightness added to polished lanes. |
| `polish_rough` | 0 to 1  | 0.3 | 0.2 | 0.3 | Roughness taken off polished lanes when dry. |
| `water_marks` | 0 to 1  | 0.3 | 0.4 | 0.3 | Dried puddle rings and tide lines in low spots. |
| `rust_halo` | 0 to 1  | 0.5 | 0.7 | 0 | Rust stain on the ground round the foot of iron posts and pipes (10 to 25 cm). |
| `rust_halo_m` | 0.05 to 0.4 m | 0.18 | 0.18 | 0.18 | Reach of the rust halo. |
| `drum_ring` | 0 to 1  | 0.5 | 0.5 | 0 | Rust bleed ring on the ground at the foot of the fire drum (the ash ring is already in the rubbish layer). |
| `tar_patches` | 0 to 1  | 0.3 | 0.5 | 0 | Tar patches over lost setts: scalloped edges, speckle of chippings. |
| `tar_max_share` | 0 to 0.06  | 0.03 | 0.03 | 0 | Ceiling on tar patches as a share of road area (2 to 4 %). |
| `tar_splash` | 0 to 1  | 0.3 | 0.3 | 0 | Splashes of tar at the kerb foot. |
| `tar_gloss` | 0 to 1  | 0.6 | 0.6 | 0.6 | How glossy new tar is (near black when wet). |
| `scrub_strip` | 0 to 1  | 0 | 0.6 | 0 | Pale scrubbed strip on the flags in front of a whitened or scrubbed doorstep (reads the same door random as the steps layer). |
| `scrub_strip_m` | 0.2 to 0.8 m | 0.4 | 0.4 | 0.4 | Reach of the scrubbed strip. |
| `show_part` | 0 to 9  | 0 |  |  | Checking view only: 0 = the whole Mask output; 1 film, 2 polish, 3 water marks, 4 rust halo, 5 drum ring, 6 tar patches, 7 tar splash, 8 scrub strip. |
| `film_octaves` | 1 to 6  | 3 |  |  | How broken-up the film patches are (noise detail). |
| `dust` | 0 to 0.15  | 0.04 |  |  | A thin even dust on all ground that dulls its tone a little at every distance (the film is patchy and gives way to its average far away; this is the part that stays). |
| `ring_m` | 0.03 to 0.4 m | 0.1 |  |  | Width of the dried puddle ring. |
| `pool_scale_m` | 0.5 to 3 m | 1.3 |  |  | Size of the shallow dips the dried puddle rings sit in. |
| `drum_ring_m` | 0.03 to 0.4 m | 0.12 |  |  | Width of the rust bleed ring round the fire drum. |
| `tar_spacing_m` | 2 to 15 m | 6 |  |  | Tar patch sites lie on a loose grid of this size. |
| `tar_patch_m` | 0.3 to 1.6 m | 0.75 |  |  | Longest half-size of a tar patch (shrunk so that tar_max_share is never passed). |
| `tar_weathered` | 0 to 1  | 0.6 |  |  | Share of tar patches that are old, grey and matt (the rest are new, black and glossy). |
| `tar_chippings` | 0 to 1  | 0.5 |  |  | Strength of the pale chippings speckle on a tar patch. |
| `splash_m` | 0.1 to 0.6 m | 0.25 |  |  | Size of a tar splash at the kerb foot. |
| `scrub_whitened_share` | 0 to 1  | 0.55 |  |  | Same number as the doorstep layer's whitened_share (copied from the look when the layer is registered). |
| `scrub_scrubbed_share` | 0 to 1  | 0.35 |  |  | Same number as the doorstep layer's scrubbed_share (copied from the look when the layer is registered). |
| `scrub_lift` | 0 to 1  | 0.45 |  |  | How much paler the scrubbed strip on the flags is than the dirty flags round it. |
| `mark_dots` | 4 to 40  | 14 |  |  | Smallest width in plate dots of a stain edge or a ring (they are widened with distance up to Inflate Limit). |
| `ring_pale` | 0 to 0.8 | 0.45 | 0 |  | How much paler than the stone the tide line of a dried puddle is (0 = no pale line; at 0.45 it showed as a bright arc). (fix round) |
| `dip_dark` | 0 to 0.4 | 0.12 | 0.12 |  | How much darker the shallow dip inside a dried puddle ring is. (fix round) |

### groundcracks  (slot B; roles in the plan: ground.flag, ground.kerb, ground.sett (hard ground only))

| dial | range | default | street | courtyard | what it does |
|---|---|---|---|---|---|
| `amount` | 0 to 2  | 1 | 1 | 1 | Master dial of the layer. 0 = the surface is exactly as it was before the layer. 1 = normal. 2 = double. |
| `seed` | 0 to 100  | 0 | 0 | 0 | Moves where things fall; the same seed gives the same picture every time. (The kit also gives every object its own seed.) |
| `inflate_limit` | 1 to 12  | 6 | 6 | 6 | A mark may be drawn at most this many times wider than real so that it stays visible at distance; beyond that it fades into an average tone. |
| `fade_start` | 5 to 40 m | 12 | 12 | 12 | Metres from the camera where fine detail starts to give way to the average tone. |
| `fade_end` | 15 to 80 m | 40 | 40 | 40 | Metres from the camera where fine detail has fully given way to the average tone (never to "clean"). |
| `wet_follow` | 0 to 1  | 1 | 1 | 1 | How much the layer follows the Wet Mask where a wetness layer exists (darker and glossier when wet). 0 = ignores wetness. |
| `flag_cracks` | 0 to 2  | 1 | 1 | 0 | Amount of flag cracking. |
| `flag_fine_share` | 0.05 to 0.2  | 0.11 | 0.11 | 0 | Share of flags with a fine crack (8 to 15 %). |
| `flag_broken_share` | 0.01 to 0.06  | 0.03 | 0.03 | 0 | Share broken in two or three with a gap (2 to 4 %). |
| `flag_tilt_share` | 0.02 to 0.08  | 0.04 | 0.04 | 0 | Share tilted or sunk (3 to 6 %). |
| `tilt_lip` | 3 to 20 mm | 8 | 8 | 8 | Height of the raised edge of a tilted flag (throws a dark shadow line). |
| `corner_chip_share` | 0.03 to 0.15  | 0.07 | 0.07 | 0 | Share of flags with a chipped corner. |
| `kerb_chips` | 0 to 2  | 1 | 1 | 0 | Amount of kerb damage. |
| `kerb_chip_share` | 0.1 to 0.5  | 0.28 | 0.28 | 0 | Share of kerb length with edge chips (20 to 35 %). |
| `kerb_break_share` | 0 to 0.15  | 0.067 | 0.067 | 0 | Share of kerb stones cracked or broken (1 in 15). |
| `kerb_scuffs` | 0 to 1  | 0.3 | 0.3 | 0 | Pale wheel scuffs on kerb faces. |
| `kerb_joint_open` | 3 to 20 mm | 8 | 8 | 8 | Width of open, dark kerb joints. |
| `sett_disturb` | 0 to 2  | 0.7 | 0.35 | 0 | Amount of disturbed setts (tilted, sunk, missing, ash or tar filled). |
| `sett_disturbed_share` | 0.02 to 0.08  | 0.04 | 0.04 | 0 | Share of the sett field disturbed (3 to 6 %), gathered round seams, covers and wheel bands. |
| `open_joint_share` | 0.05 to 0.25  | 0.14 | 0.07 | 0 | Share of sett joints open and dark (10 to 20 %). |
| `missing_share` | 0 to 0.01  | 0.003 | 0.003 | 0 | Share of setts missing (dark rectangle). |
| `sunken_patch` | 0.3 to 1.5 m | 0.8 | 0.8 | 0.8 | Length of a sunken patch. |
| `crack_dots` | 2 to 8  | 3.5 | 4.5 | 3.5 | Smallest crack width in plate dots. |
| `crack_contrast` | 0.04 to 0.2  | 0.11 | 0.16 | 0.11 | Smallest crack contrast. |
| `near_only` | 8 to 30 m | 15 | 20 | 15 | Cracks fade out beyond this distance. |
| `max_contrast` | 0.4 to 0.9  | 0.75 | 0.75 | 0.75 | Guard: no harsh black grid. Sett joints may not exceed this contrast. |
| `dull` | 0 to 1  | 1 | 0.6 | 1 | Cracks are dull so the wet look cannot wash them out. |
| `show_part` | 0 to 12  | 0 |  |  | Checking view only: 0 = whole Mask; 1 flag fine cracks, 2 flag broken, 3 flag tilted, 4 flag chipped corners, 5 kerb chips, 6 kerb open joints and cracks, 7 kerb scuffs, 8 setts disturbed, 9 sett open joints; 10 and 11 the flags that were chosen for fine and for broken cracks (whole flag), 12 all sett joints (the length the open-joint share is counted against). |
| `crack_scale_m` | 0.4 to 2 m | 0.85 |  |  | Size of the pieces the crack lines run between (about one flag). |
| `crack_real_mm` | 1 to 8 mm | 3 |  |  | Real width of a fine crack, before it is drawn wider for the picture. |
| `broken_gap_mm` | 2 to 12 mm | 5 |  |  | Real width of the gap of a broken flag. |
| `site_bias` | 0 to 1  | 0.6 | 0.9 |  | How much cracks gather near the kerb, seams and covers rather than anywhere. |
| `chip_m` | 0.02 to 0.15 m | 0.05 |  |  | Size of one kerb or flag edge chip. |
| `chip_depth_mm` | 5 to 40 mm | 15 |  |  | Depth of a kerb chip. |
| `sunk_depth_mm` | 2 to 25 mm | 8 |  |  | How far a sunken sett patch lies below its neighbours. |
| `missing_depth_mm` | 10 to 60 mm | 30 |  |  | Depth of a missing sett. |
| `lip_dark` | 0 to 1  | 0.35 |  |  | Darkness of the shadow line along the raised edge of a tilted flag. |
| `relief` | 0 to 1  | 1 |  |  | Strength of the slopes (the Bump): lips of tilted stones, chip notches, crack grooves. 0 = colour and dullness only. |
| `ref_brightness` | 0.1 to 0.5  | 0.2 |  |  | Plate brightness of the surface the cracks sit on (a crack_contrast of 0.11 on 0.2 takes the plate down to 0.09). |
| `open_dark` | 0 to 0.6  | 0.22 |  |  | How much darker an open joint is than the joint round it (the joint layer already makes joints dark). |
| `open_depth_mm` | 0 to 6 mm | 3 | 0.8 |  | How deep an open sett joint is cut into the surface: a deep one catches the light and shows as a pale hairline on a wet road. (fix round) |

### groundmoss  (slot C; roles in the plan: ground.sett, ground.flag, ground.channel, ground.kerb (ground.earth, stone.natural in other sets))

| dial | range | default | street | courtyard | what it does |
|---|---|---|---|---|---|
| `amount` | 0 to 2  | 1 | 1 | 1 | Master dial of the layer. 0 = the surface is exactly as it was before the layer. 1 = normal. 2 = double. |
| `seed` | 0 to 100  | 0 | 0 | 0 | Moves where things fall; the same seed gives the same picture every time. (The kit also gives every object its own seed.) |
| `inflate_limit` | 1 to 12  | 6 | 6 | 6 | A mark may be drawn at most this many times wider than real so that it stays visible at distance; beyond that it fades into an average tone. |
| `fade_start` | 5 to 40 m | 12 | 12 | 12 | Metres from the camera where fine detail starts to give way to the average tone. |
| `fade_end` | 15 to 80 m | 40 | 40 | 40 | Metres from the camera where fine detail has fully given way to the average tone (never to "clean"). |
| `wet_follow` | 0 to 1  | 1 | 1 | 1 | How much the layer follows the Wet Mask where a wetness layer exists (darker and glossier when wet). 0 = ignores wetness. |
| `joint_share` | 0.03 to 0.3  | 0.08 | 0.1 | 0.3 | Share of joint length carrying painted moss in the best (gutter-side) strip. |
| `shade_bias` | 0 to 1  | 0.6 | 0.6 | 0.6 | How much shade favours moss over sun. |
| `ribbon_dots` | 3 to 12  | 4 | 6 | 4 | Smallest moss ribbon width in plate dots (a 1 to 3 cm joint ribbon is drawn wider near the camera). |
| `ribbon_m` | 0.01 to 0.06 m | 0.02 | 0.02 | 0.02 | Real ribbon width. |
| `broken_len` | 0.1 to 0.8 m | 0.3 | 0.3 | 0.4 | Length of a broken ribbon piece. |
| `algae_fan` | 0 to 1  | 0.6 | 0.6 | 0.3 | Dark green-black algae fan under every downpipe outlet and gully. |
| `algae_radius` | 0.3 to 1 m | 0.55 | 0.55 | 0.55 | Reach of an algae fan. |
| `liverwort` | 0 to 1  | 0 | 0.1 | 0 | The one bright green: 0 to 2 patches of 10 to 40 cm in damp shade. |
| `far_band` | 0 to 1  | 0.5 | 0.5 | 0.3 | Beyond the pieces distance: a slightly greener, darker strip along gutter and wall foot instead of single plants. |
| `far_band_m` | 0.2 to 0.8 m | 0.45 | 0.45 | 0.45 | Width of the far band. |
| `moss_value` | 0.25 to 0.5  | 0.36 | 0.36 | 0.36 | Plate brightness of dry moss (lighter than the stone; painted values under 0.12 are black on the film). |
| `show_part` | 0 to 9  | 0 |  |  | Checking view only: 0 = whole Mask; 1 joint moss, 2 patch moss, 3 algae fans, 4 liverwort, 5 far band, 6 all joints where moss could grow (the length the moss share is counted against). |
| `patch_moss` | 0 to 1  | 0.6 |  |  | Moss as soft patches on open ground (for sets with no joints, e.g. earth, gravel, stones). A set that wants moss only in joints gives the role a multiplier of 0. |
| `patch_scale_m` | 0.2 to 2 m | 0.7 |  |  | Size of a moss patch on open ground. |
| `moss_lift` | 1 to 6  | 2.2 |  |  | How much lighter than the stone beneath the dry moss is (in scene light; the painter weakens colour, so moss is made stronger than wanted). |
| `moss_rim` | 0 to 1  | 0.5 |  |  | A paler rim on the moss edge (a painted look). |
| `liverwort_m` | 0.1 to 0.6 m | 0.25 |  |  | Size of a liverwort patch. |
| `algae_dark` | 0 to 1  | 0.55 |  |  | How dark the algae film is (1 = near black-green). |
| `outlet_reach` | 0.05 to 1  | 0.7 |  |  | How close to a wall (0 touching, 1 = the set's wall reach) a standing foot must be to count as a downpipe outlet; posts stand farther out. |

### iron  (slot A; roles in the plan: iron, iron.post, iron.pipe, fire (cast iron, steel, drum, rails))

| dial | range | default | street | courtyard | what it does |
|---|---|---|---|---|---|
| `amount` | 0 to 2  | 1 | 1 | 1 | Master dial of the layer. 0 = the surface is exactly as it was before the layer. 1 = normal. 2 = double. |
| `seed` | 0 to 100  | 0 | 0 | 0 | Moves where things fall; the same seed gives the same picture every time. (The kit also gives every object its own seed.) |
| `inflate_limit` | 1 to 12  | 6 | 6 | 6 | A mark may be drawn at most this many times wider than real so that it stays visible at distance; beyond that it fades into an average tone. |
| `fade_start` | 5 to 40 m | 12 | 12 | 12 | Metres from the camera where fine detail starts to give way to the average tone. |
| `fade_end` | 15 to 80 m | 40 | 40 | 40 | Metres from the camera where fine detail has fully given way to the average tone (never to "clean"). |
| `wet_follow` | 0 to 1  | 1 | 1 | 1 | How much the layer follows the Wet Mask where a wetness layer exists (darker and glossier when wet). 0 = ignores wetness. |
| `rust_cover` | 0 to 1  | 0.3 | 0.5 | 0 | Share of the lower part of an iron object with paint chipped back to rust. |
| `rust_height` | 0.2 to 1.2 m | 0.55 | 0.55 | 0.55 | How high rust reaches from the foot of a post. |
| `chip_share` | 0.1 to 0.5  | 0.3 | 0.3 | 0.3 | Share of paint chipped in the rust zone. |
| `collar_spacing` | 1.2 to 2.5 m | 1.9 | 1.9 | 1.9 | Spacing of pipe collars and joints where rust rings sit. |
| `collar_rust` | 0 to 1  | 0.5 | 0.5 | 0 | Share of collars with rust. |
| `metallic_drop` | 0 to 1  | 0.6 | 0.6 | 0.6 | Rust lowers Metallic by up to this fraction (cast iron 0.6, steel 0.5, brass 0.9). |
| `heat_scale` | 0 to 1  | 0.3 | 0.3 | 0 | Heat-blued scale on the fire drum only. |
| `soot_halo` | 0 to 1  | 0.5 | 0.5 | 0 | Sooty halo above the drum vent holes and black rim. |
| `paint_keep` | 0 to 1  | 0.6 | 0.6 | 0.6 | Share of the original paint kept (black or dark green). |
| `rust_run` | 0.05 to 0.3 m | 0.12 | 0.12 | 0.12 | Length of rust runs below fixings. |
| `show_part` | 0 to 9  | 0 |  |  | Checking view only: 0 = whole Mask; 1 foot rust, 2 collar rings, 3 shoe streak, 4 base ring, 5 drum rust, 6 heat scale, 7 soot. |
| `streak_m` | 0.01 to 0.08 m | 0.025 |  |  | Width of a vertical rust or wet streak. |
| `rust_bright` | 1 to 3.5  | 1.7 |  |  | Brightness of rust against the iron paint it lies on (1 = as dark as the paint). |
| `grime_dark` | 0 to 0.2  | 0.06 |  |  | A thin even coat of soot on all iron: it darkens the paint a little at every distance. |
| `shoe_streak` | 0 to 1  | 0.6 |  |  | Dark wet streak at the foot (shoe) of a downpipe. |
| `shoe_height` | 0.1 to 1 m | 0.45 |  |  | How high the dark wet streak at the pipe shoe reaches. |
| `base_ring` | 0 to 1  | 0.7 |  |  | Rust ring at the base flange of a post. |
| `base_ring_m` | 0.05 to 0.3 m | 0.12 |  |  | Height of the base-flange ring. |
| `collar_m` | 0.02 to 0.15 m | 0.06 |  |  | Height of a rust ring at a collar. |
| `drum_rust` | 0 to 1  | 0.7 |  |  | Share of a drum covered by rust and old paint (60 to 80 percent). |
| `rim_soot_m` | 0.03 to 0.3 m | 0.12 |  |  | Height of the black soot rim at the top of a drum. |

### growth  (slot C; roles in the plan: ground.sett, ground.flag, ground.channel, ground.kerb (scatter targets; others by settings))

| dial | range | default | street | courtyard | what it does |
|---|---|---|---|---|---|
| `amount` | 0 to 2  | 1 | 1 | 1 | Master dial of the layer. 0 = the surface is exactly as it was before the layer. 1 = normal. 2 = double. |
| `seed` | 0 to 100  | 0 | 0 | 0 | Moves where things fall; the same seed gives the same picture every time. (The kit also gives every object its own seed.) |
| `inflate_limit` | 1 to 12  | 6 | 6 | 6 | A mark may be drawn at most this many times wider than real so that it stays visible at distance; beyond that it fades into an average tone. |
| `fade_start` | 5 to 40 m | 12 | 12 | 12 | Metres from the camera where fine detail starts to give way to the average tone. |
| `fade_end` | 15 to 80 m | 40 | 40 | 40 | Metres from the camera where fine detail has fully given way to the average tone (never to "clean"). |
| `wet_follow` | 0 to 1  | 1 | 1 | 1 | How much the layer follows the Wet Mask where a wetness layer exists (darker and glossier when wet). 0 = ignores wetness. |
| `weeds_amount` | 0 to 2  | 1 | 1 | 0.1 | Amount of weed pieces (grass tufts, rosettes). 0 = none. |
| `cushions_amount` | 0 to 2  | 1 | 0.3 | 1.5 | Amount of moss cushion pieces. 0 = none. |
| `distance` | 8 to 40 m | 18 | 18 | 25 | Pieces are laid only up to this far from the camera (the camera of the picture being drawn). |
| `distance_fade` | 2 to 10 m | 5 | 5 | 5 | Length of the fade-out at the pieces distance. |
| `piece_size` | 0.5 to 2  | 1 | 1 | 1 | Size of every piece (1 = as built to the period sizes). |
| `weed_cover` | 0 to 0.03  | 0.01 | 0.02 | 0.001 | Green cover of weeds as a share of ground area inside the pieces distance (0.5 to 2 % in 1926). |
| `gutter_tuft_share` | 0.02 to 0.1  | 0.05 | 0.1 | 0 | Share of gutter-side joint length with a visible tuft (3 to 8 %). |
| `wall_foot_share` | 0.01 to 0.08  | 0.035 | 0.035 | 0 | Share of wall-foot length with a plant (2 to 5 %). |
| `cushion_cover` | 0 to 0.03  | 0.008 | 0.008 | 0.02 | Moss cushion cover as a share of ground area inside the pieces distance. |
| `min_spacing` | 0.05 to 0.4 m | 0.15 | 0.15 | 0.15 | Nearest two pieces of one kind may be. |
| `toadflax_clumps` | 0 to 3  | 0 | 1 | 0 | Ivy-leaved toadflax trails on damp mortar: 0 to 2 clumps in the whole street. |
| `rubbish_thin_max` | 0.2 to 0.7  | 0.45 | 0.45 | 0.45 | Weeds grow at full density through rubbish thinner than this mask value. |
| `rubbish_heap_min` | 0.5 to 0.95  | 0.75 | 0.75 | 0.75 | No weeds (and no moss above 0.6) on rubbish heavier than this mask value; between the two it thins out linearly. |
| `dead_grass_share` | 0 to 0.5  | 0.15 | 0.08 | 0.15 | Share of grass tufts that are dead and straw-coloured. |
| `flower_share` | 0 to 0.3  | 0.08 | 0.08 | 0 | Share of dandelions in flower or seed-clock (a few only). |
| `max_pieces` | 500 to 6000  | 2500 | 2500 | 2500 | Hard ceiling on pieces in one picture (drawing time). |
| `wet_dark` | 0.4 to 1  | 0.7 | 0.7 | 0.7 | Colour multiple of wet pieces (richer green, darker). |
| `tilt_random` | 0 to 1  | 0.5 | 0.5 | 0.5 | How much each piece leans. |
| `piece_inflate_limit` | 1 to 6  | 3 | 3 | 3 | How many times bigger than real a plant may be drawn so that it stays at least min_dots plate dots wide at a distance (the growth layer's own, lower limit). |
| `moss_smother_from` | 0.1 to 0.6  | 0.3 |  |  | Rubbish value above which moss cushions start to thin out. |
| `moss_smother_to` | 0.3 to 0.95  | 0.6 |  |  | Rubbish value at which moss cushions have stopped. |
| `existing_avoid` | 0 to 1  | 0.8 |  | 0.7 | How much the places that already have growth (the set's existing_growth) are left alone: 0 grow on it, 1 none on it. |
| `avoid_m` | 0 to 0.3 m | 0.05 |  |  | Nearest a plant may stand to a 3D piece of the objects named in growth.avoid_pieces_of (litter). |
| `colour_gain` | 0.4 to 2.5  | 1 | 0.55 | 0.15 | Multiplies the colour of every piece (tuning the plate brightness). |
| `min_dots_scale` | 0.5 to 3  | 1 |  |  | Multiplies every kind's smallest width in plate dots (species.json min_dots: 6 for weeds, 5 for moss) that a plant is widened to at a distance (never past piece_inflate_limit). |
| `colour_sat` | 0.2 to 1.5  | 1 | 0.85 | 1.2 | Multiplies the colour saturation of every piece (1 = species.json as written). |
| `show_kind` | -1 to 20  | -1 |  |  | Checking view only: -1 all kinds, otherwise only the kind with that number. |
| `realise` | 0 to 1  | 0 |  |  | Turn the instances into plain meshes (1) or keep instances (0). |
| `cand_density_scale` | 0.3 to 3  | 1 |  |  | Multiplier of the candidate points of every kind (finer choice of places, slower). |

---

## 9. The numbers (the integrator's final settings before the fix round; the final round was `integrated/work/r5`; **the fix round's numbers are in section 12.5**)

### P1 sett joints
* With everything on: **21 of 22** lighting pictures pass (before the new parts: 20 of 22). The one that fails, `lockout_B_heavy` (the lockout in heavy rain, middle road band), failed before too. `lockout_B_wet` now passes (it failed before by 0.005). Nothing that passed before fails now.
* With every dot counted: 20 of 22 (before: 18). Highest joint contrast near the camera 0.62 (limit 0.75): no harsh black grid. Grid visible in near and middle bands: 18 of 22 (before: 18).
* **NOT met: the count with the kit's own dots left out too.** The line asks for the same as before (20); it is 18 of 22, failing `lockout_B_dry`, `lockout_B_wet`, `lockout_B_heavy`, `lockout_E_wet`. The kit's own marks cover 31 to 45 percent of the road dots (the ground film's mask is a wide soft area, not a mark), so leaving them out leaves the lockout's middle band with too few joint dots to judge. It says little about the joints themselves.

### P2 the wet look
* Road wet-over-dry within 0.05 of before in 7 of the 10 pictures that have a dry twin (10 of the 22). Out: `main_A_heavy` +0.055, `main_E_wet` -0.154, `main_E_heavy` -0.120 (light E is the brazier glare; the road is 3.7 times brighter wet there, so these are 2 to 4 percent). Pavement `close_A_heavy` +0.052. Walls are within 0.05 in all 10 (the kit makes them 0.01 to 0.04 less dark wet than before).
* Highlight share of the wet road (light C wet 0.0337, light D wet 0.0420; the line is 85 to 115 percent of 0.05 = 0.0425 to 0.0575): 2 pictures just under. Puddle cover is unchanged (the kit does not touch the water layer).
* Every kit element no brighter wet than dry: **NOT met**, 43 of 90 lines. Soot, run-off and iron come out at 0.8 to 1.15; ground film 0.83 to 1.67; cracks and moss ribbons 1.3 to 3.7. For ground elements the line cannot be met in this light (the whole road is 1.4 to 3.7 times brighter wet); divided by the surface's own wet/dry the ground film is 0.38 to 0.78 (duller than its surface, as intended), cracks 0.92 to 1.11, moss ribbons 0.59 to 1.18, soot 1.01 to 1.10, iron 0.99 to 1.06.
* The plants' wet-over-dry brightness (growth builder's measure): 0.63 to 0.90 against the moss band 0.55 to 0.85; one picture (lighting C wet) over.

### P3 readable at the painter's size (scale 0.45, inside each element's design zone)

| element (layer) | plate | marks | good | share good | lost | crushed | line |
|---|---|---|---|---|---|---|---|
| soot and dust patches | main | 152 | 51 | 34% | 43% | 10% | FAIL |
| soot and dust patches | notice | 134 | 44 | 33% | 48% | 5% | FAIL |
| run-off streaks | main | 0 | 0 | 0% | 0% | 0% | FAIL |
| run-off streaks | notice | 81 | 8 | 10% | 63% | 18% | FAIL |
| whitened or scrubbed steps | main | 0 | 0 | 0% | 0% | 0% | FAIL |
| whitened or scrubbed steps | notice | 6 | 4 | 67% | 33% | 0% | FAIL |
| rust | main | 0 | 0 | 0% | 0% | 0% | FAIL |
| rust | notice | 3 | 0 | 0% | 100% | 0% | FAIL |
| cracks in flags, kerbs, setts | main | 257 | 36 | 14% | 65% | 4% | FAIL |
| cracks in flags, kerbs, setts | notice | 240 | 110 | 46% | 34% | 6% | FAIL |
| tar patches | main | 2 | 1 | 50% | 50% | 50% | FAIL |
| tar patches | notice | 1 | 1 | 100% | 0% | 0% | pass |
| ground film, polish, water marks | main | 5 | 1 | 20% | 80% | 20% | FAIL |
| ground film, polish, water marks | notice | 3 | 1 | 33% | 67% | 67% | FAIL |
| weed tufts and moss cushions | main | 66 | 46 | 70% | 8% | 0% | pass |
| weed tufts and moss cushions | notice | 188 | 85 | 45% | 23% | 0% | FAIL |
| moss ribbons and algae fans | main | 68 | 6 | 9% | 72% | 9% | FAIL |
| moss ribbons and algae fans | notice | 57 | 13 | 23% | 60% | 7% | FAIL |
| wall-foot band and tide-mark | main | 10 | 0 | 0% | 70% | 70% | FAIL |
| soot and dust patches | lockout | 162 | 65 | 40% | 41% | 12% | FAIL |
| run-off streaks | lockout | 20 | 9 | 45% | 30% | 10% | FAIL |
| whitened or scrubbed steps | lockout | 0 | 0 | 0% | 0% | 0% | FAIL |
| rust | lockout | 0 | 0 | 0% | 0% | 0% | FAIL |
| cracks in flags, kerbs, setts | lockout | 220 | 26 | 12% | 72% | 2% | FAIL |
| tar patches | lockout | 4 | 1 | 25% | 50% | 0% | FAIL |
| ground film, polish, water marks | lockout | 7 | 1 | 14% | 71% | 0% | FAIL |
| weed tufts and moss cushions | lockout | 29 | 29 | 100% | 0% | 0% | pass |
| moss ribbons and algae fans | lockout | 11 | 1 | 9% | 64% | 0% | FAIL |

Plain reading: **only the weeds and moss cushions pass** (main 70 percent good, lockout 100 percent; the notice camera 45 percent, which looks down on a lit pavement so the plants have no contrast, fails). Everything else fails the 60 percent line: the walls are dark and seen almost edge-on, so 41 to 48 percent of the soot patches and 63 percent of the notice camera's run-off streaks are lost, and the main camera has no run-off mark and no whitened step inside the zone. Cracks gained marks when made stronger (36 good on the main plate against 28 before; 110 against 71 on the notice plate) but most marks stay faint. **Nothing was painted**: how many of these marks survive the repaint is not known.

### P4 nothing wrong for 1926
* Forbidden things: none (no graffiti, road lines, studs, bins, dishes, oil, trench patches, flower boxes, lichen; `lichen_amount` 0).
* Orange or yellow outside rust and plants, share of the changed dots (limit 0.05 percent): main 0.05, notice 0.10, close road 0.24, lockout 0.12 percent. **Over the line** (main by a hair). The brightened warm-lit brick and the dusty-pale wall foot are the likely cause; no bright green (0.0).
* Soot "on 85 to 100 percent of wall area": the measure reads the soot layer's Mask, which is the pale washed patches (14.5, 21 and 14.7 percent of the wall: the plan wants 15 to 25), not the film (which is on every wall), so the line is not a fair test of this layer; run-off streaks 1.5 to 2.8 percent of wall area (the plan wants 3 to 6): **under**.
* Not automated, not measured by anyone: washed share per house, streak pairs at sills, splash band length, whitened steps share, flag and kerb damage shares (the ground builder measured them on plan pictures: fine cracks 10.4 percent, broken 2.5, tilted 3.2, kerb chips 31, disturbed setts 4.9, open joints 15.7, tar 0.7, moss in kerb and gutter joints 10.6 percent, all inside their caps; chipped corners not counted), tar, weed cover, whitewash. A fresh person looking at eight 100 percent crops has not been done.

### P5 the street is not one dark mush
Against before, on the four plates (main, lockout, notice, close road), every surface class:
* **M1 to M4 all pass.** Darkened by a third: walls 0.12 to 0.23 of the class (limit 0.25), everything else at most 0.05. Share under plate brightness 0.10: walls and trims go DOWN (-3.4 to -6.6 and up to +1.0 points; the line allows +3), road at most +0.8, pavement, kerb, iron, roofs, chimneys, colliery within +1.3. Mean brightness: walls 0.98 to 1.05, road 0.97 to 1.00, iron 0.97, nothing under 0.966 (limit 0.88); the whole plate 0.984 to 1.003 (limit 0.92). Spread inside the class: lowest 0.91 (chimneys), road 0.93 (limit 0.85).
* **M5 is NOT met.** The upper limit of 1.00 is broken wherever the kit LIGHTENS a class (pale washed patches, pale streaks, whitened steps): walls 10 to 20 m 1.06 to 1.12, trims 1.00 to 1.76 (the close camera sees few of them), roofs and chimneys 1.0 to 1.13, road 1.01 at most. Walls differ by more than 0.08 from band to band (lockout 0.13, notice 0.16, close road 0.16). Nothing is below 0.90. This is the cost of the "pale marks on dark walls" design: the walls read at 10 to 20 m because the mid-distance wall is a little brighter than before, while the 20 to 40 m wall is 0.90 to 0.99. Fixing it means lowering `washed_pale` or `washed_share`, which would lower the soot readability that already fails.
* The `paint` layer is off (it was the only layer that failed M2 to M4).

### P6 no plants on the crown, the lanes, the doorsteps
* The moss, weed, lichen and algae fields are exactly 0.0 in the crown, the traffic lanes and the keep-clear strips (street and lockout).
* main A wet: 195 plants, in the crown / lanes / keep-clear / doorstep / within 1 m of the fire: 0 / 0 / 0 / 0 / 0; weeds within 5 cm of litter: 0 of 124.
* notice A wet: 407 plants, in the crown / lanes / keep-clear / doorstep / within 1 m of the fire: 0 / 0 / 0 / 0 / 0; weeds within 5 cm of litter: 0 of 260.
* close road A wet: 330 plants, in the crown / lanes / keep-clear / doorstep / within 1 m of the fire: 0 / 0 / 0 / 0 / 0; weeds within 5 cm of litter: 0 of 218.
* lockout B wet: 253 plants, in the crown / lanes / keep-clear / doorstep / within 1 m of the fire: 0 / 0 / 0 / 0 / 0; weeds within 5 cm of litter: 0 of 111.
* Plants standing inside puddles: 36 percent of the plants in view of the main camera (32 of 88; section 3.2, item 2). Not a pass line, but the most visible fault left.

### P7 drawing time (plate 1536 x 2730, 48 samples, best of three, the rented card shared with another job)
* Street main camera: before 2.19 s, everything on 4.52 s (**2.06 times**; limit 1.3). Lockout camera: 3.18 s against 5.58 s (**1.75 times**). NOT met.
* Per layer alone on the street plate (before = 2.15 s): iron +0 percent, steps +1, runoff +2, groundcracks +2, dirt +3, groundmoss +3, foot +4, soot +5, wallcracks +5, wallgrowth +6, **growth +70** (3.65 s: the litter clearance, section 3.2 item 1; +0.5 percent without it). The plan had walls +8, ground +8, growth +10 percent.
* First picture after putting the kit on (shader build plus the first draw): street 19.5 + 5.1 = about 25 s, lockout 20.0 + 6.3 = about 26 s (limit 40 s: met; the line of 1.5 times the before picture, about 4 s, NOT met). One lockout round measured 77 s once, while the machine was busy with two of my runs at once.
* Plants in a picture: 195 to 407 (limit 2,500).

### P8 master dial 0 and removing (the integrated test, `harness/test_weathering_entry.py`, 270 x 480 pictures on the rented machine)
* **street**: all master dials at 0 against the earlier layers alone: 0.04 percent of dots more than one step apart (largest difference 0.028 of full brightness); two draws of one state: 0.00 percent apart; after `remove()` the picture of the scene as it was: 0.00 percent apart; apply and remove twice: node counts [1067, 1067] (the same); kit node groups left behind: 0; the kit changes 39 percent of the dots; each group switched off alone changes the picture (walls 24, ground 14, growth 2.0 percent of dots).
* **lockout**: all master dials at 0 against the earlier layers alone: 0.08 percent of dots more than one step apart (largest difference 0.024 of full brightness); two draws of one state: 0.00 percent apart; after `remove()` the picture of the scene as it was: 0.00 percent apart; apply and remove twice: node counts [1349, 1349] (the same); kit node groups left behind: 0; the kit changes 31 percent of the dots; each group switched off alone changes the picture (walls 20, ground 10, growth 0.6 percent of dots).
* **courtyard**: all master dials at 0 against the earlier layers alone: 0.52 percent of dots more than one step apart (largest difference 0.090 of full brightness); two draws of one state: 0.00 percent apart; after `remove()` the picture of the scene as it was: 0.00 percent apart; apply and remove twice: node counts [1692, 1692] (the same); kit node groups left behind: 0; the kit changes 32 percent of the dots; each group switched off alone changes the picture (walls 10, ground 21, growth 1.3 percent of dots).
* The courtyard's master 0 is not exact: the add-on's stones go through an adapter box (a rebuilt Principled BSDF) and EEVEE draws it up to one step of 255 differently on about 0.5 percent of dots (a few dots up to 0.09). In Cycles the adapter is identical (the foundation measured it).
* The builders' own isolation tests (a layer alone changes only its own roles) passed on the street, the lockout file and the courtyard in their folders; runoff on the courtyard cannot be tested (it draws nothing there).

### P9 reuse
* The lint finds **0 hits** over `apply/ masks/ harness/ walls/ ground/ growth/` and the new `apply_weathering.py`. Both settings files validate (0 errors, 0 warnings for the street). The same call `aw.apply(...)` ran on the courtyard scene without a crash (12 layers registered; walls and ground layers went into 4 to 103 materials, the shader-group stones through the adapter; the growth layer is separate 3D pieces and is not counted in materials), with the two settings sections (`ground`, `growth`) moved into the set files and the courtyard looks carrying the growth layer's courtyard values.

### P10 the "behind" plate
* The lockout plate with the props hidden differs from the plate with props in 25.7 percent of the dots by more than 2 steps (the plan asked 1 percent). Before the kit it is 26.0 percent: the hidden props change the light and the glare, so this is not the kit; the line cannot be met even by the earlier layers.

### P11 hygiene
* Written: only `kits/weathering/` (the new files and the changes listed in section 11) and `street_wet/grime_and_growth/integrated/`, plus the pictures folder. Not written: the film project, `set_copy`, `street_wet/tools`, `relief_and_rubbish`, `painter_round_2`, `painter_test`, `japanese-courtyard`, the add-on folder. The lockout file and the courtyard file were only opened, never saved. No commit, no push, no paid call, no machine stopped, `~/.runpod` not touched. The integrated folder is under its 150 MB limit; free disk stayed above 0.9 GB (lowest 0.91).

---

## 10. What is not done, not tested, not sure

**Not done.**
* ~~The plants cannot see the water layer's puddles.~~ **Done in the fix round** (baked `above_water`, section 12.3).
* ~~The litter clearance of the plants costs +1.5 s a plate.~~ **Done in the fix round** (baked `litter_dist`, section 12.3).
* `paint` is untuned and off.
* The wet-over-dry line for kit elements on the road cannot be met as written; it should compare an element with its own surface.
* M5's upper limit (1.00) cannot be met by a design that lightens walls on purpose; either the line or the design has to give.
* The walls' water-film cut in `wallcracks` is not done (an unexplained difference at amount 0 when the coat is changed); the cracks cut roughness and shine only.
* `Kit.materials_for` should know the water layer's copies (the walls builder patches it on the instance).
* The courtyard has no wall sheets, no plate camera, no lighting rigs and no test set yet; `runoff` draws nothing there.

**Not tested.**
* Nothing was painted. Whether the painter keeps the green plants green, keeps a 3 to 5 dot crack, or turns the pale washed patches into plaster, is unknown (the chart plate for the Paint step was not drawn here).
* The lockout "behind" plate and the notice and close-road plates were drawn and measured, but no fresh person has looked at eight 100 percent crops and no period expert has read them.
* Cycles, heavy-rain pictures at plate size, and lighting E at plate size.
* The second courtyard look (`mossy_courtyard_neglected`), and any courtyard picture beyond the 600 x 400 test pictures.
* A fresh rented machine that has forgotten the kit.

**Not sure.**
* Whether the soot is enough, or too much, for the film: the plate's mean brightness stays within 1.1 percent of before, but the right terrace goes noticeably darker and greyer while the left row hardly changes, and the whitened steps come out cold blue-grey under the night light.
* The amounts (1926 weeds, moss, cracks) are all judgement.
* Whether a 4.5 dot crack of contrast 0.16 looks like a crack or a scratch once painted.
* Whether the ground film's pale patches read as dirt or as a smear on the wet road (the main plate's near road shows large soft pale shapes).

## 11. What the integrator changed in the kit (everything outside the three builders' folders)

* New: `apply_weathering.py` (the door), `street_weathering.py` (the street wrapper), `harness/test_weathering_entry.py`, `integrate/pin_round2.py`, `integrate/legacy_round2/` and `integrate/legacy_round2.json` (the second painter round's earlier layers), `integrate/tune_log.md`.
* `harness/legacy_stack.py`: which pinned copy is used is chosen by the set (`legacy.pinned_root`) or by `WK_LEGACY_PINNED`; the old default is unchanged.
* `harness/lint_no_set_names.py`: also scans `apply_weathering.py`.
* `masks/ground_plan.py`: the step finder reads two optional keys (`max_height_m`, `max_extent_m`); the street and lockout packs were rebuilt (`masks/packs/pit_village_street/...`; the old packs are not kept).
* `sets/pit_village_street.json`: `ground` and `growth` sections moved in from the builders' sidecar files; `legacy.pinned_root`; `geometry.steps.max_height_m` and `max_extent_m`; `apply.soot.role_dials` (trims, colliery); `apply.paint.roles` emptied.
* `sets/japanese_courtyard.json`: `ground` and `growth` sections moved in.
* `presets/sooty_1926.json`: the dial values of section 5. `presets/mossy_courtyard_*.json`: the growth layer's courtyard values.
* The builders' sidecar files (`ground/ground_sets`, `growth/growth_sets`, `ground/looks_ground`, `growth/looks_growth`) are still there and are only read when a set file has no such section.
* Nothing in `walls/`, `ground/`, `growth/` was edited by the integrator. (The fix round did edit a few lines in them: section 12.7.)


---

## 12. The fix round (after the two checkers)

Two fresh checkers looked at the integrated street (the four plates and four sheets, nothing painted) and found what a viewer would notice first. This section says what they found, what was changed for each finding (dials where possible, two small kit additions where not), what was redrawn, every number before and after, and what is still not right. The "before" is always the integrator's round r5 (`integrated/plates`); the earlier layers alone ("base") are unchanged. Nothing was painted: no call to the painter was made.

### 12.1 Finding by finding

| what a viewer sees | what was done | where it lives |
|---|---|---|
| Weeds and moss glow lime-green on the dark road, the first thing the eye lands on (median plant brightness 0.393 against 0.103 round it) | colour lift 8 times to 4.4 times (`growth.colour_gain` 0.55 of the 8 times in `species.json`), saturation x0.85, half the flat moss strings (`cushions_amount` 0.3), fewer pale dead-grass tufts (`dead_grass_share` 0.08) | look dials only |
| Plants stand in puddles in the wet state (39 percent of the plant blobs) | the earlier water layer's puddle picture (drawn once from above, in the wet state of the plates) is stamped into the pack's `above_water`; the growth layer already grows nothing where it is 0 | new picture, `masks/stamp_pack.py`, `harness/make_plan_pictures.py`, runner view `plan:puddles` |
| Hard-edged pale or blue-white panels and a cold grey cast on the left brick terrace; the red loses its warmth | washed patches 17 to 7 percent of the wall (`washed_share`), paleness 0.8 to 0.5, softer edges (`edge_sharp` 0.55), colder grey pull 0.25 to 0.10, the patches' own colour made warmer (`pale_warm` 1.0), and the film back up from 0.60 to 0.80 so the walls do not go dark mush (trims and colliery role values lowered to 1.2 and 1.25 so they keep their film) | look dials, one new dial (`soot.pale_warm`), set file role values |
| Whitened doorsteps are cold blue-white wedges | warm cream (`steps.white_cream` 1.0) a little less bright (`white_value` 0.85) | two new dials |
| Near wet road looks over-processed: film patches with bright arcs, three near-identical rings, a thin crack on nearly every sett | no pale tide line on the water marks (`dirt.ring_pale` 0, new), smaller film patches (`film_max_share` 0.15), sett disturbance halved (`sett_disturb` 0.35), open joints 14 to 7 percent and cut only 0.8 mm deep instead of 3 mm (`open_joint_share`, `groundcracks.open_depth_mm`, new): the pale hairline along a joint was the cut's slope catching the light | look dials, two new dials |
| Run-off streaks and wall-foot damp invisible at film size; the element called "stains" does not show | streaks 14 dots wide, rust-coloured under the pipe joints (`iron_rust` 0.9), more long leaks (0.3), on 90 percent of the sources; white flecks at the wall foot cut to 0.008 | look dials. **Not solved**: see 12.6 |
| The lockout plate hardly changes | left as it is (a judgement call: it already reads as grubby from the litter and the iron). If visible weather is wanted there it has to come from the walls and the gutter | nothing changed |
| Drawing time 2.1 times a plate, 70 percent of it the plants' litter clearance | the clearance is a look-up in a baked picture (`litter_dist`) | new picture, one change in `growth/scatter.py` |
| Reuse hygiene: the lint missed one-decimal numbers (the street's bounds sat in `masks/check_against_earlier.py`, a camera name in `growth/jobs_growth.py`); stale courtyard sidecar files; the round's PNGs were deleted so nothing could be re-checked | the lint now catches lists of numbers and camera names copied from a set file; both scripts read the set file instead (`legacy.places_grid`, `growth.close_camera`); the four sidecar files were moved out of the kit (to `grime_and_growth/fix/retired_sidecars`); every PNG of this round has a SHA-256 hash in `fix/keep/` and the final plates are kept as PNG | code |

### 12.2 What stayed as it was
No layer was added or removed. The master dials, the order, the roles, the packs (except the two new pictures) and every dial not listed in the table of 12.1 are unchanged; a dial added in this round has a default that gives the old behaviour (`pale_warm` 0, `white_cream` 0, `white_value` 1, `ring_pale` 0.45, `dip_dark` 0.12, `open_depth_mm` 3), so the courtyard's look, which does not name them, draws as before.

### 12.3 The two baked pictures (how to make them for a new set)
* **`above_water`** (the mask that says "water here, grow nothing"): for a pond it was always made from the set's water level. For a set with the earlier water layer's puddles, `harness/make_plan_pictures.py SET SCENE WORK_DIR` draws the puddle mask seen from above (runner view `plan:puddles`, 2 cm dots, in the wet state of the plates), `masks/stamp_pack.py` marks a dot as puddle above 0.5 (the same line the measures use), widens it by 3 cm and writes 0 there. About 18 percent of the street's ground counts as puddle. A mask that says "puddle" in a dry plate too is the price of keeping the dry and the wet plate the same plants.
* **`litter_dist`** (a new mask, picture `gp_h.png`, 2 cm dots): the distance in metres (0 to 0.25, scaled to 0 to 1) to the nearest litter piece. It is made from the litter pieces of the objects named in `growth.avoid_pieces_of` seen from above (white shapes, runner view `plan:litter`, 1 cm dots) **and the centre of every piece** (the runner writes `plan_litter_points.json`): a first version from the picture alone lost 44 percent of the pieces because thin straws and dust are narrower than a dot, and 170 of 236 weeds then stood within 5 cm of a piece's centre. With the centres added, 0 of 101. The growth layer's `avoid_m` (5 cm) dial still means what it says: a plant is not stood where `litter_dist` x 0.25 m is below it. A pack without the picture falls back to the old nearest-point search (slow, same answer).
* Both pictures are valid only for the state they were drawn in (the plates' puddle amount; the litter's amount and seed). Draw them again when those change. Stamping puddles twice only widens them: put the pack's `gp_c.png` and `manifest.json` back first to change the margin.

### 12.4 The new dials
`soot.pale_warm`, `steps.white_cream`, `steps.white_value`, `dirt.ring_pale`, `dirt.dip_dark`, `groundcracks.open_depth_mm` (rows are in section 8). The soot layer's washed patches and the run-off streaks lift their colour toward a pale target; the target of the patches can now be warm.

### 12.5 The numbers, before and after (plates 1536 x 2730, 64 samples, kit against the earlier layers alone; PNG, the checkers' own scripts re-run: `fix/work/checks.py`)

**Plants (main plate, the ground part).**

| | dry before | dry after | wet before | wet after |
|---|---|---|---|---|
| green plant dots | 9707 | 4648 | 8608 | 3873 |
| median plant brightness | 0.393 | 0.258 | 0.293 | 0.171 |
| brightness of the ring round them | 0.103 | 0.105 | 0.15 | 0.173 |
| plant over ring | 3.81 | 2.46 | 1.96 | 0.99 |
| share of plant dots over brightness 0.45 | 46 % | 7 % | 12 % | 0 % |

The plan wanted a plant brightness of 0.17 to 0.33: now 0.26 dry and 0.17 wet (before 0.39 and 0.29). The lockout plate, lit more strongly (lighting B): plants 0.45 dry and 0.318 wet (before 0.579 and 0.432); two thirds of its dry plant dots are still over 0.45, so the lockout's plants are the brightest thing left.

**Puddles.** The checkers' pixel count (green blobs of 25 dots or more whose centre is inside a puddle of the earlier water layer): main wet plate 32 of 82 (39 %) before, 8 of 42 (19 %) after; green dots inside a puddle 36 % before, 11 % after. Lockout wet plate 2 of 10 before, 1 of 9 after. The exact count from the plant list (root position against the stamped mask): **0 of 157** plants stand in a puddle on the main plate. The blobs that remain are leaves leaning over a puddle's edge (a fifth of the plants stand within 10 cm of one) and reflections of plants in the water; which of the two was not counted.

**Plant counts and clearance (P6).** Main plate 157 plants (101 weeds, 56 moss strings; before 195): in the crown / lanes / keep-clear / doorstep / within 1 m of the fire 0 / 0 / 0 / 0 / 0; weeds within 5 cm of a litter piece's centre 0 of 101. Lockout plate 120 plants (60 weeds): all zero, 0 near litter. The habitat fields are exactly 0 in the zones (street and lockout).

**Walls (main plate).** Red-to-blue ratio of the wall class, left terrace: earlier layers alone 2.021, before the fix 1.387, after 1.755; right terrace 1.502, 1.312, 1.472 (the closer to the first number, the warmer). Wall dots lifted more than 1.6 times above base (the pale panels): left 7.8 % before, 0.7 % after; right 13.5 % before, 3.1 % after.

**Not dark mush (P5, per surface class, main plate dry / wet, then lockout dry / wet).**

| class | mean brightness against base: before | after | darkened by a third: before | after | share under 0.10, base | before | after |
|---|---|---|---|---|---|---|---|
| walls (main dry) | 0.959 | 0.931 | 26.6 % | 2.8 % | 73.7 % | 71.3 % | 74.8 % |
| walls (main wet) | 0.991 | 0.95 | 17.5 % | 1.6 % | 79.3 % | 75.3 % | 79.5 % |
| trims (main dry) | 0.988 | 1.0 | 1.3 % | 0.6 % | 60.0 % | 61.4 % | 59.5 % |
| road (main dry) | 0.985 | 0.988 | 0.1 % | 0.0 % | 35.9 % | 43.3 % | 39.9 % |
| colliery (main dry) | 1.021 | 0.976 | 0.0 % | 0.0 % | 59.3 % | 56.6 % | 64.7 % |
| walls (lockout dry) | 1.017 | 0.964 | 13.9 % | 1.3 % | 67.3 % | 65.0 % | 69.1 % |
| walls (lockout wet) | 1.032 | 0.977 | 9.5 % | 0.7 % | 74.8 % | 69.5 % | 74.0 % |

Whole plate against base: main dry 0.9941 to 0.9906, main wet 0.9894 to 0.9931, lockout dry 1.0009 to 0.9974, lockout wet 1.0025 to 0.9989. The plan's lines (M1 at most 25 percent of the class darkened by a third, M2 under-0.10 share up by at most 3 points on walls and trims and 8 on the rest, M3 mean at least 0.88): all met on both plates in both states (the largest rise is the colliery's, +5.4 points on the main plate, +5.2 on the lockout; walls +1.1 and +1.8). The dry walls were over the M1 line before (26.6 percent): now 2.8 percent. M5 (distance bands) was not re-run (it fails by design, section 9).

**Joint contrast (the checkers' bands of the main plate at 540 x 960; joint over stone, puddle dots left out in the wet picture), after over base:** dry near 1.014, mid 0.993, far 0.969; wet near 1.009, mid 1.029, far 1.057 (before: 1.019, 1.001, 1.017; 1.000, 1.027, 1.093). The joints are as visible as without the kit.

**P1 sett joints (the 22 lighting pictures: street 16, lockout 6).** Official count 21 of 22 (street 16 of 16, lockout 5 of 6; the one failure, `lockout_B_heavy`, fails without the kit too); with every dot counted 19 of 22 (before the fix round 20; the three misses are `lockout_B_wet` and `lockout_B_heavy`, which fail without the kit too, and `lockout_E_wet`, which passed before); with the kit's own dots left out too **21 of 22 (before 18, the line is 20: now met)**; no harsh black grid (largest joint contrast 0.62, limit 0.75).

**P2 the wet look.** Street: 3 lines out (before the fix round 6): light E wet road wet/dry 3.6151 against 3.7119 (-0.097; was -0.154), light E heavy 3.4883 against 3.5763 (-0.088; was -0.120), light C wet highlight share 0.0361 (line 0.0425; was 0.0337). Lockout: no line out. (The per-element lines were not re-run: they need the layers' own pictures, which this round did not draw.)

**P7 drawing time (best of three, 1536 x 2730 at 48 samples, the card shared with another job).** Street: earlier layers alone 2.2 s, everything 3.05 s = **1.39 times** (before the fix round 2.06; line 1.3). Lockout: 3.24 s against 4.27 s = **1.32 times** (before 1.75). The first picture after putting the kit on: street 14.51 s look change + 16.11 s first draw, lockout 14.76 s + 4.87 s (limit 40 s: met; the 1.5 times line is not).

**P8 and the door (the integrated test, `harness/test_weathering_entry.py`, run again after the code changes).**
* **street** (0 errors): `remove()` gives the scene back (picture 0.000 percent of dots over one step apart); all master dials at 0 against the earlier layers alone 0.04 percent of dots over one step (largest 0.0275); two draws of one state 0.00 percent apart; apply and remove twice: node counts [1067, 1067]; kit leftovers 0; the kit changes 32 percent of the dots; each group off alone changes the picture (walls 20, ground 12, growth 1.1 percent of dots).
* **lockout** (0 errors): `remove()` gives the scene back (picture 0.000 percent of dots over one step apart); all master dials at 0 against the earlier layers alone 0.08 percent of dots over one step (largest 0.0235); two draws of one state 0.00 percent apart; apply and remove twice: node counts [1349, 1349]; kit leftovers 0; the kit changes 26 percent of the dots; each group off alone changes the picture (walls 17, ground 9, growth 0.4 percent of dots).
* **courtyard** (0 errors): `remove()` gives the scene back (picture 0.001 percent of dots over one step apart); all master dials at 0 against the earlier layers alone 0.52 percent of dots over one step (largest 0.0902); two draws of one state 0.00 percent apart; apply and remove twice: node counts [1822, 1822]; kit leftovers 0; the kit changes 39 percent of the dots; each group off alone changes the picture (walls 20, ground 24, growth 1.4 percent of dots).

### 12.6 What is still not right, not tested, not sure
* **The stains are still not visible at film size.** The walls are seen edge-on and are nearly black; the run-off streaks, wall-foot damp and washed patches are a few dots wide on the main plate. The streaks are wider and rustier now, but this was not measured against the painter's size (the readable-at-the-painter's-size counts, P3, were not re-run: the first checker said not to spend the round on them, and the layer pictures they need were not drawn). If "stains" must show on the walls of the main plate, the honest answers are to let the painter add them or to move the camera nearer a wall; the ground's dried puddle marks and the rust halos are the stains that do show.
* **Fewer plants** (157 in view of the main camera against 195): the puddle and litter rules keep plants out of the gutter, where the weeds liked to grow. They are small, dim tufts along the kerb foot and the gutter now. `weed_cover` and `gutter_tuft_share` are the dials to raise (the plan's own caps are 2 percent and 8 percent; the look is at 2 and 10).
* The pale dead-grass tufts are still the lightest things on the dark road; `dead_grass_share` is down to 0.08.
* The lockout's plants and the sett joints' open share (7 percent now; the plan's period line says 10 to 20 percent) were not re-checked against the period table (P4 was not re-run).
* Not run: P3 readable at the painter's size, P4 period caps, the per-layer drawing times, M5, the notice and close-road plates at full size, the heavy-rain pictures at plate size. The lamp-post rust (the checker's minor finding: a strong brick red) is unchanged: `iron.rust_bright` was tried at 1.0, 1.4, 1.7 and 3.0 and made no visible difference on the posts, so the look does not name it (the final plates were drawn with 1.4 in the look; taking it out changes nothing that could be seen).
* The whitened steps now read khaki-cream; in deep shade a few look slightly olive.
* **Nothing was painted.** The one cheap chart-plate repaint that the painted-look study asked for is still the next step: whether the painter keeps the dim green plants green, the dull terrace brick red and the cream steps cream is unknown.
* The pack's rubbish picture (`rubbish_heap`) is still the first painter round's (drawn from the earlier, smaller litter); only the new `litter_dist` comes from the second round's litter.

### 12.7 Files changed in the fix round
* Kit code: `harness/runner.py` (views `plan:puddles` and `plan:litter`, `piece_points`), `harness/class_pass.py` (a plain white override), `harness/lint_no_set_names.py` (lists of numbers and camera names), `masks/names.py` (the `litter_dist` row and the `above_water` words), `growth/scatter.py` and `growth/apply_growth.py` (the baked clearance, with the old search as the fallback), `growth/jobs_growth.py`, `masks/check_against_earlier.py` (no street numbers), `walls/steps.py`, `walls/soot.py`, `walls/walls_common.py` (`lift_to` takes a colour made in the nodes), `walls/dials_walls.py`, `ground/dirt.py`, `ground/groundcracks.py`, `ground/dials_ground.py`.
* New: `masks/stamp_pack.py`, `harness/make_plan_pictures.py`.
* Data: `presets/sooty_1926.json` (the table in section 5), `sets/pit_village_street.json` (`legacy.places_grid`, the soot role values of trims and the colliery), the street and lockout packs (`above_water`, new `gp_h.png`, `manifest.json`); `README.md`, `HOW TO USE.md`, `integrate/tune_log.md`.
* Moved out of the kit: the four sidecar files `ground/ground_sets/*.json`, `growth/growth_sets/*.json` (now in `grime_and_growth/fix/retired_sidecars`).
* Work, numbers and the originals of everything that was changed: `street_wet/grime_and_growth/fix/` (`backup/` holds the originals, `keep/` the numbers and the SHA-256 hashes of the PNGs, `plates/` the four final plates as PNG, `work/` the scripts).
