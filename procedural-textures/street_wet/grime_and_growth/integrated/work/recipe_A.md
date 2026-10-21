# 15 Recipe - weathering kit - grime, cracks, stains, weeds and moss - how it is made

Written by the integrator, 21 October 2026, in plain words. This is the one note that ties the whole kit together: how to put it on and take it off, the order everything goes on in, every dial, how to switch each thing off, how to add a new set (the Japanese courtyard is next), and every number measured on the pit village street, including what does not pass. Nothing here was painted: no call to the painter was made.

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

1. **Plants and litter: a cost nobody saw.** The growth layer keeps its weeds 5 cm clear of every litter piece (a nearest-point question over all pieces). With the second round's 58,753 pieces this costs about 1.5 seconds on every plate: growth alone is +70 percent of a plate (3.65 s against 2.15 s), where its builder measured +1 to +6 percent with the first round's 6,439. Switched off (`growth.avoid_pieces_of.objects` = [] in the settings file) it costs +0.5 percent, but then 138 of 174 weeds (79 percent) stand within 5 cm of a litter piece (the line allows 3 percent) and the plant count doubles. **Decision: kept on**; a plate takes 1.5 s longer, which does not matter for a handful of stills, and no weed stands on a coal lump.
2. **Plants and puddles.** About 37 percent of the plants of the main plate stand inside puddles (38 percent of the plant dots with the first settings, 111 plants in view, 43 in a puddle; 36 percent, 32 of 88, with the final ones). Both like the low ground beside the gutter, and the plants cannot see the water layer's puddles (the puddle field is made inside the shader from a slow wobble, the ground's lowness and the relief). On wet pictures some flat green moss strings look as if they float. **Decision**: `growth.cushions_amount` 1.0 to 0.6 (the flat moss strings are the ones that read as floating; the weeds stay). This does not change the share that stands in puddles, it only makes fewer of them. **Not fixed**: the proper fix is for the water layer to hand its puddle field to the plants as a ground-plan picture. Written down as the first job of the next round.
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
    then, if the set has litter, `python3 -I masks/make_pack.py <set id> <scene id> <raw folder> --rubbish <picture>`. `python3 -I masks/check_pack.py <set id> <scene id>` checks the shade side. `masks/CONTRACT.md` lists every mask; `masks/NOT_DONE.md` lists what is missing.
16. **Smoke test** inside Blender: `aw.apply('<set id>', '<look id>')`, `w.report()` (look at `problems` and `skipped`), `w.remove()`. Then `python3 -I harness/lint_no_set_names.py` (must say 0 hits: it fails if kit code names anything from a settings file) and `harness/test_weathering_entry.py` on the rented machine.
17. **Draw and tune**: `harness/run_testset.py`, then the measuring scripts in section 9. Tune dials in the look, never kit code. A fault in a layer goes into a `REQUESTS.md` note for that layer's folder.

What each next set must decide that the street could not test: whether the kit's moss extends or matches the add-on's existing moss (`habitat.moss.extend_existing`, `growth.existing_avoid`), roof tiles that are instances (`apply.growth.realise_instances`), wall sheets for plaster walls (the courtyard has none, so `runoff` draws nothing there), its own plate camera and lighting rigs, and whether the painter keeps moss and streaks on light plaster.
