# 11 Pipeline - where new layers hook into the street

What this file is: the technical study for the weathering kit (grime, cracks, stains, weeds, moss). It says what the street copy is made of, where a new layer can be put into its materials,
what the earlier layers (wetness, joints, rubbish) already give a new layer to read, which masks are still missing and how to make them from the street's own geometry, how the lockout shot file
differs, what the painter will actually see, how long a picture takes on the rented machine, and every trap the earlier builders fell into. It was written on 21 October 2026.

What I did and did not do: I read the earlier layers' code, their apply scripts and recipe notes, and opened the street copy (and, read-only, the lockout shot file and the saved Japanese courtyard scene) in
Blender with nothing saved. I wrote small study scripts (in `study/scripts/`, each with a plain note and its run line), ran one timing test on the rented machine (three Blender runs, after a first attempt that failed), and made one look-at sheet.
I did not write into the film project, `set_copy/`, `tools/`, `relief_and_rubbish/`, `painter_round_2/`, `painter_test/`, the courtyard folder or the add-on folder. No paid image calls. No git.

Words used (one word for each thing, explained once):
* **set**: the 3D street in Blender. **plate**: the one picture drawn from the set's camera, which the painter repaints. **painter**: the image model (Flux 3 edit on fal). **stage**: the film's three.js program that shines the painting back on the 3D set.
* **layer**: a small packaged recipe made of Blender's node boxes (Blender calls it a "node group") that is dropped into a material. The street has three so far: WETNESS (water), JOINTS (the gaps between the road setts) and RUBBISH (cinders, paper, mud ...).
* **Principled BSDF**: the all-purpose surface box every material of the street ends in. **plug** (Blender says "socket"): one input of a box, for example its Base Color plug or its Roughness plug.
* **hook** (or **splice**): putting a new layer in the wire between whatever feeds a plug and the plug itself.
* **mask**: a grey number for every dot of a surface, 0 = nowhere, 1 = fully. **places picture**: a small picture of the street seen from above that the rubbish builder made by measuring the real 3D shapes (distance to a wall, to a step, to a pipe foot ...).
* **family**: all the objects built the same way (for example the 28 cottage front walls). **sett**: a squared road stone. **flag**: a pavement slab. **ledge**: a shelf that sticks out of a wall (sill, step, string course, eaves).
* **painter dot**: one dot of the plate as the painter sees it. The painter is given the plate at about 0.4 to 0.5 of 1536 x 2730 (last time 810 x 1440, which is 0.53), so one painter dot is about 2.2 plate dots.
* **openness**: the share of the sky that a spot can see (1 = open field, 0 = a cellar). **EEVEE** is Blender's fast renderer (draws the plates); **Cycles** is its slow exact one.
* **brightness** (as the earlier notes use it): the finished 8-bit picture's brightness from 0 (black) to 1 (white), not light energy.

---

## 1. The short answer

1. **The way the earlier layers hook in will not do for the kit.** The JOINTS and RUBBISH code looks for "the wire that feeds the Principled box's Base Color, Roughness, Specular IOR Level, Coat Weight and Normal plugs" and fails if one plug has no wire.
   I tested it (in memory, nothing saved): it works on **0 of the 41** street materials as they are, on **15 of 45** after the wetness layer is on (the wetness layer is what wires the plugs), and on **0 of 85** materials of the lockout file.
   The street's own materials keep Roughness, Specular and Coat as plain numbers (no wire at all) and the nine window, lamp and sky materials have no Normal wire.
   A hook that takes "whatever is there, a wire or a plain number" and wires it through a group worked on **all 41** street materials, **all 85** lockout materials and **80 of 134** courtyard materials (the other 54 do not end in a Principled box: 46 are the add-on's own shader groups, 6 are glow-only, 2 put a Mix Shader after the Principled box). A do-nothing group spliced into all 41 street materials drew a picture **identical to the dot** (135 x 240, 32,400 dots, largest difference 0.0). Section 3.
2. **Where the picture's surface is** (main camera, by rays through a 90 x 160 grid): sky 30 % (never weathered), road setts 33 %, house walls 12 %, colliery brick and headframe 7 %, stone trim (steps, plinths, sills) 5 %, cast iron (pipes, gutters, lamp posts) 4 %, gutters and kerbs 2.5 %, pavement flags 2.4 %, roofs 1 %, painted woodwork 0.6 %.
   The lockout plate adds props: 8 % props and 2 % signs (the signs keep their own lettering and must be left alone). The notice-corner plate sees far more pavement (18 %). Section 2.
3. **What the earlier layers already hand over:** Wet Mask and Puddle Mask (only on the 15 materials that wear the wetness layer), a run-off mask called Streak Mask (walls only, and it works on a dry street: I drew it at wetness 0), the road's joint picture (setts only, laid every 2 m), the rubbish mask and its five parts (ground only), the places pictures (street and lockout only), the surface direction (normal z) and the object's own coordinates. Section 4.
4. **Masks the new layers need and nobody has made yet:** shade (sky openness and sun shadow), run-off lines from the real ledges and pipes, traffic and footfall lanes, wall corners and reveals, edges of kerbs and flags, cavity for walls and flags, and a general "height above the ground / how low is this spot". I prototyped two of them on the street copy: sky openness (works: 0.77 ms a dot, 21 s for 27,000 dots; the street turns out to be an even, dim canyon, road 0.40 to 0.56 open) and ledge finding (works: it finds the builder's hand numbers exactly: window sills at 0.85 m and 3.55 m above the floor, a string course at 3.1 m, the eaves course at 5.9 m, the door step; the rain pipe stands 18 cm proud of the wall at 2.0 m across the front). Section 5.
5. **What the painter will see decides the sizes.** In the main view one painter dot is 1.7 mm across the street at 3 m ahead, 2.9 mm at 5 m, 5.2 mm at 9 m, 7.6 mm at 13 m; **along** the street the same dot is 3, 9, 29 and 61 mm, because the road is seen at a grazing angle. So fine cracks and tiny weeds can only read in the first 10 m; beyond that only blotches and tone. The houses' fronts are seen from far away at a slant: 64 to 122 mm per painter dot along the wall but only 12 to 17 mm up, so **vertical run-off streaks survive and small horizontal detail does not**.
   Section 7.
6. **Dark grime on dark walls will not show.** In the wet plate 80 to 90 % of the dots on walls, stone trim, colliery brick, cast iron and the headframe are under 0.13 brightness, which is the zone the stage's own curve crushes (a painting value of 0.13 comes out 0.07, 0.08 comes out 0.02). The road (wet 0.195) and the pavement (0.20) have room to go darker; walls (0.07 to 0.09) do not, so on walls use lighter or coloured marks (lime, pale algae, rust orange) rather than black soot. Section 7.
7. **Time:** measured now on the rented RTX 4090 (shared with two other jobs): a street picture at 540 x 960 and 16 samples takes 0.2 to 1.6 s; a plate-size picture (1536 x 2730, 48 samples) 1.4 to 1.9 s; the first picture after a change costs more (shader build); the lockout file's first picture 14.7 s, then 2.6 s. One Blender run for a handful of pictures is 7 to 22 s from start to finish. On this computer the same 540 x 960 picture takes 75 to 85 s and a plate about 20 minutes. Section 8.
8. **The worst traps** (all of them in section 9): states must start with "today"; the runner skips pictures that already exist, so a stale picture on the rented machine comes back instead of the new one; EEVEE's soft-shadow noise shows as white speckle on shiny surfaces (cure: shadow rays 4, steps 16, 32 to 48 samples); steep relief far away turns into white ticks; the stage crushes darks; the old rent scripts call the old client; taking layers off in the wrong order silently switches the upper layer off (I tested it); every amount dial that was calibrated on one camera is wrong for the others.
9. **Reuse:** the slate MOSS and DAMAGE layers cannot be used as they are on a 3D surface (they read a slate "layout bundle": piece number, position on the piece, distance to the piece's edge, in tile units). What carries over is their method, their five olive moss tones (sRGB #2b2c23 to #545342, brightness 0.16 to 0.32) and lichen tans, and their rules (own seed, amount 0 means exactly nothing, no peeking). Scenario's texturing skill gives a few things as they are (a noise group that works in EEVEE, a material audit, a value report, the rule "burn the soft mask with the photo's height so growth stays in the grout") and warns that its Bevel and AO edge masks do not work in EEVEE. Section 10.

---

## 2. The street, family by family

All numbers in the "share" columns are mine: one ray through each dot of a 90 x 160 grid of each camera (about 14,400 rays, so plus or minus 0.4 points), main camera of the street copy, the lockout plate camera, the notice-corner plate camera (all in the street copy, which has no props) and the lockout file's own camera (with props). `study/out/s6_shares_*.json`.
The shares are by material, so the brick and stone of the chimneys are counted with the walls. Object counts and face counts are from my listing of the street copy (`study/out/street_listing.json`, `street_walls_trim.json`). "Built how" says what the material's nodes are; every street material is the same six boxes (section 3.1).

| family | objects (names in the file) | material and how it is built | layers on it today | share of the picture: main / lockout cam / notice cam |
|---|---|---|---|---|
| **road setts** | `street_setts` (1 object, 1,344 coarse quads of 0.28 m2; world coordinates; texture coordinates = metres / 2.0) | `street_setts`: Poly Haven square cobblestone photo, 2048 dots over 2 m (1 mm a dot), roughness 0.75 (a plain number), normal strength 1.4. Setts and joints exist only in the photo, not in the geometry | WETNESS, JOINTS, RUBBISH | 33.0 / 30.9 / 21.3 (low close view: 72) |
| **gutter channel** | `street_channels` (504 quads of 0.10 m2; the channel dips 2.5 cm below the road's edge, 2.4 m from the middle line) | `channel_stones`: sandstone blocks photo, 683 dots a metre | WETNESS (always wetter), RUBBISH | 1.3 / 1.2 / 3.9 |
| **kerb** | `street_kerbs` (one object, but **187 separate stones**, 0.17 to 1.06 m long, median 0.92 m; 4,862 faces, 4,488 edges marked sharp, custom normals; top 13 cm above the channel) | `kerb_stone`: sandstone blocks photo, 341 dots a metre | WETNESS, RUBBISH | 1.2 / 1.2 / 2.8 |
| **pavement flags** | `street_pavements` (168 big flat quads of 1.7 m2; **the flags exist only in the photo**, no flag geometry) | `pavement_flags`: grey tiles photo, 341 dots a metre (2.9 mm a dot) | WETNESS, RUBBISH (no joints layer) | 2.4 / 2.1 / **17.9** |
| **house walls, left row (brick)** | `left_row_a/b_cottage_NN_walls`, 14 objects, turned 180 degrees, sharing 2 meshes (7 users each) | `cottage_brick`: red brick photo, 1,463 dots a metre; per-layout copies `cottage_brick_door_left/right` | WETNESS (foot band, run-off streaks) | 5.9 / 1.5 / 7.9 |
| **house walls, right row (stone)** | `right_row_a/b_cottage_NN_walls`, 14 objects, not turned, sharing 2 meshes (7 users each) | `cottage_stone`: stone brick wall photo, 819 dots a metre; copies `cottage_stone_door_left/right` | WETNESS (same) | 5.4 / 9.7 / 8.4 |
| **steps, plinths, sills, lintels, string courses** | `*_trim` (28 objects, 442 faces each) and the sill faces inside the wall shell | `dressed_stone` (rock surface photo, 512 dots a metre) and `dark_dressed_stone` | WETNESS (porosity 0.8, band 0.6 m) | 4.8 + 0.4 / 4.9 + 0.4 / 4.9 + 0.8 |
| **cast iron** | `*_rainwater` (28 objects, 388 faces: the downpipe and the eaves gutter), `gas_lamp_N_post` (5), parts of the colliery buildings | `cast_iron`: rusty metal photo, metallic 0.6, roughness 0.55 (plain numbers), tint dark 0.16 | **none** | 4.1 / 4.6 / 4.9 |
| **roofs** | `*_roof` (28) | `roof_slate`: roof slates photo (683 dots a metre) and `ridge_clay` | WETNESS (slate) | 0.9 / 0.9 / 1.2 |
| **chimneys** | `*_chimney`, `*_end_chimney` (32) | `cottage_brick/stone` (the base material, not the per-layout copy), `dressed_stone`, `chimney_pot_clay`, `chimney_pot_sooted`, `plaster_dark` | WETNESS on the stone, none on the pots | 0.2 to 1.3 |
| **painted woodwork** | `*_door` (28), `*_window_ground/upper` (84), `fascia_board` in the trim | `paint_*` (grey plaster photo tinted), `brass`, `fascia_board` | **none** | 0.6 / 1.3 / 1.3 |
| **colliery buildings** | `heapstead_walls/trim`, `engine_house_walls/trim`, `second_winding_house_*`, `colliery_chimney` (70 to 110 m away) | `colliery_brick` (1,024-dot photo, 683 dots a metre), `boarded_blue/green`, trim stone | WETNESS on the brick | 5.0 / 3.7 / 2.6 |
| **headframe, wheels, ropes** | `headframe_lattice`, `winding_wheel_left/right`, `winding_ropes` | `headframe_steel`, `wheel_iron`, `wire_rope` (rusty metal, metallic 0.5 to 0.7) | **none** | 2.3 / 2.0 / 1.3 |
| **spoil heaps, yard, moor** | `spoil_heap_main/old`, `ground`, `moorland_hills_0/1` | `spoil_heap`, `colliery_yard`, `moor` | WETNESS on the yard only | 1.5 / 1.1 / 0.5 |
| **not to touch** | `sky_dome`, window glass, lamp glass, `interior_dark` (the dark doorways) | glow or very dark materials | none | sky 30 / 34 / 19 |

In the **lockout file** (main = the lockout plate camera) the picture is: sky 33.6, road 24.1, right-row stone walls 8.5, cast iron 4.4, stone trim 4.4, colliery brick 3.4, and the props: cart 1.9, brazier drum 1.6, sacks 3.4 together, notice, board and posts 2.1 (signs), wheels, coal heaps, bins, spade. Props in all: about 8 %.

Things to know about how the families are built (they change how a layer must be written):

* **The house fronts are huge flat shapes.** Each cottage wall object has only 32 faces; its front is two big n-sided faces with the window and door openings cut out (8.5 and 16 m2). So any mask that lives on the *vertices* (vertex colours, vertex curvature) is useless on the walls and on the road: the walls have no vertices where a mask could change, and the road's quads are 0.5 m wide. Masks must be pictures or made in the shader from coordinates.
* **The four wall meshes are shared.** 28 cottages use 4 meshes (brick or stone, door on the left or the right). The wetness layer already makes one copy of the wall material for each door layout and measures everything in the wall's own coordinates (the cottage floor is z = 0, y runs across the front, the wall face is at x = 0, minus x faces the street), so one wet pattern serves 7 houses. A picture made in the wall's own frame serves them too; variation between houses has to come from something per object (Blender's Object Info "Random", or the object's position).
* **The ground objects have the identity transform** (their own coordinates are the world's), so "Object" and "World" are the same on them. The street runs along +y and rises 4 degrees; its middle line is x = 0.
* **The photos are much finer than the painter.** The textures are 0.7 to 2.9 mm a dot. A painter dot is 1.2 to 40 mm in the views above. New weathering does not need detail finer than about 3 mm anywhere.
* **Shared materials.** `dressed_stone` is on 64 objects (steps, sills, chimney caps, colliery trim), `cast_iron` on 37, `colliery_brick` on 5, `roof_slate` on 31. A rule that is by material alone would weather a doorstep and a chimney cap the same way. Use geometry masks (normal direction, height above the floor, distance to a wall) as well.
* **Texture coordinates are tied to the photo.** Real-size box projection, so `uv = metres / tile_metres` (the number is kept in the material as the custom property `tile_metres`: setts 2.0, flags 3.0, brick 1.4, stone 2.5, kerb 3.0, slate 3.0 ...). Anything laid through the texture coordinates repeats every `tile_metres`: JOINTS' pictures repeat every 2 m, which is right for joints and wrong for moss or cracks (the road would show 42 copies in 84 m). Random weathering must be read from world or object position.

---

## 3. The chain: what a material looks like, what the earlier layers did to it, where a new one goes

### 3.1 The shape of the street's materials
Every textured material of the street copy is built by one function of the street builder (`textured_material` in `build_street.py`): a colour picture, a Mix box that multiplies it by a tint, a normal-map picture and a Normal Map box, all feeding one Principled box. Roughness, Metallic, Specular and Coat are plain numbers on the Principled box. There is no Mapping or Texture Coordinate box (the pictures use the mesh's own texture coordinates).
The window, lamp, lit-window and sky materials are three or four boxes (a picture into Base Color, for the glowing ones also into Emission Color, no Normal wire, emission strength 1.0 to 8): they glow, or are dark glass, and must not be weathered.
The lockout file's 44 prop-only materials come from imported glTF files: the colour picture into Base Color, a packed "ARM" picture split with a Separate Color box into Roughness (green) and Metallic (blue), a normal map; some (coal, notice paper, the brazier's coals) have plain numbers instead, and the brazier's coals are black with emission. Props share no material with the street (checked: zero in common).

### 3.2 The chain the earlier layers built
```
dry look (picture, tint, normal map)  ->  WETNESS  ->  JOINTS (road only)  ->  RUBBISH (road, flags, channel, kerb)  ->  Principled BSDF
```
Each layer takes the five values (Colour, Roughness, Specular IOR Level, Coat Weight, Normal) from the one before and hands five on; JOINTS and RUBBISH also read WETNESS's Wet Mask and Puddle Mask. WETNESS is put on 11 materials (15 with the per-layout wall copies): road, flags, channel, kerb, brick and stone walls, colliery brick, two dressed stones, slate, yard. Nothing is put on the iron, the paints, the woodwork, the headframe, the spoil heaps or the moor.

### 3.3 The hook: what failed, what worked (my tests, in memory, nothing saved)

| test | street copy (41 materials) | street copy after `aw.apply()` (45) | lockout file (85) | courtyard scene (134) |
|---|---|---|---|---|
| old hook code (looks for a wire on all 5 plugs) works on | **0** | **15** | **0** | not run |
| plugs with a wire: Roughness / Specular / Coat / Normal | 0 / 0 / 0 / 32 | 15 / 15 / 15 / 36 | 29 / 0 / 0 / 72 | - |
| new hook (wire or plain number, through a group) works on | **41** | - | **85** | **80** of 134 (54 do not end in a Principled box: 46 add-on shader groups, 6 glow-only, 2 with a Mix Shader after it) |
| constants it had to turn into nodes | 132 | - | 241 | 380 |
| picture with a do-nothing group on every material, against none | **identical** (135 x 240, 4 samples, EEVEE: 32,400 dots, largest difference 0.0) | - | not drawn | not drawn |

`study/scripts/s8_hook_test.py`, `s9_splice_test.py`, `s9b_splice_render_equal.py`. What the new hook does, in plain steps: find the Principled box that feeds the material output; for each plug (Base Color, Roughness, Specular IOR Level, Coat Weight, Normal **and Metallic**) take the socket that feeds it, or, if nothing does, make a Value or RGB box holding the plug's number (for Normal with no wire: the Geometry box's Normal); wire those into the new group and the group's outputs back into the plugs.
Add **Metallic** to the list: rust on `cast_iron` (metallic 0.6), `brass` (0.9), `headframe_steel` (0.5), `wheel_iron` (0.6) and `wire_rope` (0.7) has to lower it; JOINTS and RUBBISH never touched it. Skip materials with Emission Strength above 0 and materials in the set's "do not weather" list.
The Scenario texturing skill has the same idea (`_source`: "a socket carrying what feeds the plug, an RGB or Value box for constants"; `add_wear` inserts "between whatever feeds the Principled Base Color / Roughness / Metallic and the BSDF"), so the idea is not new; our own earlier code is what lacks it.

### 3.4 Where each kind of new layer should sit (my recommendation, with reasons)

* **Slot A, before WETNESS (on the dry colour): grime film, stains, lime and salt marks, rust tide marks, algae tint.** These are a different dry colour of the same stone; if they come before WETNESS, the water layer darkens and smooths them by its own porosity rule, so a wet street is consistent without any extra "wet look" dial. Cost: the splice is in the wire between the photo and WETNESS (the kit's chain must be able to insert anywhere, not only before the Principled box).
* **Slot B, after WETNESS and JOINTS (before RUBBISH): cracks.** A crack is a narrow, dark, dull line with a real slope, exactly the thing the JOINTS round found the water layer washes out (before JOINTS only 6 of 22 test lightings passed, the dry ones). So cracks must come after WETNESS and make themselves dull, as JOINTS does (roughness back to about 0.9, shine cut by 35 %, water film cut by 45 %, a relief the water cannot smooth).
* **Slot C, after cracks, before RUBBISH: growth (moss, weeds, lichen).** Plants lie on top of the stone and in its cracks; litter then lies on top of the plants. Growth reads Wet Mask and Puddle Mask where they exist (darker and glossier when wet, like RUBBISH's "Wet Look").
* **Materials without WETNESS** (iron, paints, woodwork, headframe, spoil): there is no slot A or B; the new layers go straight before the Principled box. Their Wet Mask input is simply 0.
* **Relief:** like RUBBISH, add the layer's height as a Bump on the incoming Normal (Bump Distance about 0.01 m). Never hand a normal map and a height to the same surface (Scenario's rule, and what the street does).

Which slots each family has today:

| family | what is on it now | slots a new layer can use |
|---|---|---|
| road setts | WETNESS, JOINTS, RUBBISH | A before WETNESS; B between JOINTS and RUBBISH; C between those two as well (growth before RUBBISH) |
| flags, gutter stones, kerb stones | WETNESS, RUBBISH | A; B and C between WETNESS and RUBBISH |
| the four wall materials (brick and stone, per door layout), the chimneys' base wall material | WETNESS | A; B and C after WETNESS (no RUBBISH on walls yet) |
| dressed stone (2), colliery brick, slate, yard | WETNESS | A; B and C after WETNESS |
| cast iron, brass, paints, fascia, headframe steel, wheel iron, wire rope, plaster, ridge clay, chimney pots, spoil heap, moor | nothing | straight before the Principled box (A, B and C are the same place); Wet Mask = 0 |
| props (lockout file) | nothing | the same, except the sign materials (leave alone) |

### 3.5 Order and repeat traps of the earlier apply scripts (found by reading, then tested)
* **Taking layers off in the wrong order silently switches the upper one off.** I put on wetness, JOINTS and RUBBISH, then removed JOINTS first: no error, but RUBBISH's Colour input lost its wire, the Principled box was fed straight from WETNESS again, and none of RUBBISH's outputs went anywhere: RUBBISH was cut out of the chain (checked by listing the wires at that moment). After `ar.remove()` the box is back to WETNESS, so a later check "is it clean?" passes while the pictures in between were wrong. The kit's chain must keep one list per material and rebuild all wires from it (add, remove, move a layer), instead of each layer remembering its own "old links".
* `aj.apply()` calls its own `remove()` first; with RUBBISH on top, calling `aj.apply()` again triggers exactly that.
* `22_render_eevee.py`: the layer is put on the first time a state other than "today" is asked for and is never taken off; asking for "today" afterwards draws the layered street with whatever state it last had. States must start with "today" (the header of the file says so).
* `aw.set_state` does not reach RUBBISH's separate 3D pieces; `ar.set_state` has to be called as well.

---

## 4. What each earlier layer already gives a new layer to read

| what | where it exists | what it holds | limits |
|---|---|---|---|
| **Wet Mask** (0..1) | output of WETNESS, on the 15 materials | how wet the dot is, puddles counted as soaked | 0 at wetness 0; only where WETNESS is on (not on iron, paints, woodwork, headframe, spoil, moor) |
| **Puddle Mask**, **Puddle Depth** | same | standing water; the depth number the puddle threshold is cut from | grounds only; calibrated on one camera (below) |
| **Streak Mask** (0..1) | same, on walls | vertical rain streaks: general ones (strength dial 0.5) plus one hanging from each window sill and the eaves (5 sources per door layout, from the builder's hand numbers) | **it is not zero on a dry street**: I drew it at wetness 0, max 1.0 and the picture shows white streaks on both rows (sheet panel 2). So a stain layer can use it as "where run-off goes" without any wetness. It is not made from the geometry |
| **Height** (after water fills puddles) | same | the photo's relief height with puddles filled | only for the materials that were given a height picture (road, flags, red brick, stone brick wall, with the wall copies) |
| **Colour, Roughness, Specular IOR Level, Coat Weight, Coat Roughness, Normal** | same | the wet look | - |
| **Joint cavity** and **halo** (0..1) | `setts/maps/sett_joints_clean.png` (red = cavity, blue = halo, green = groove profile), read by JOINTS through the road's texture coordinates | how deep in a joint a dot is, 1 cm falloff; the grid completed with the joints the dark search missed | **setts only**, repeats every 2 m, no flag or wall version. JOINTS has no output for it, so a new layer must read the picture itself |
| **Joint Shade** | JOINTS output | share of light that does not reach a joint floor | only used when Joint Shadow was above 0 when the layer was put on |
| **Rubbish Mask**, **Gutter Part**, **Wall Part**, **Corner Part**, **Props Part**, **Mud Part** | outputs of RUBBISH on the four ground materials | where litter gathers (gutter strip, wall foot, doorsteps, pipe feet, inside corners, rings round props) | ground only. Many numbers are the street's own (strip centre 2.35 m from the middle line, crown clear within 1.3 m of it, places picture covers x -4.5..4.5 and y -12..72) |
| **places pictures A and B** | `rubbish/maps/places_street_a/b.png`, `places_lockout_a/b.png`, 225 x 2100 dots, 4 cm a dot, made by `make_places_pictures.py` from the real geometry in 5 s (street) and 8 s (lockout) | A: red = distance to nearest house wall, step or plinth (0 to 1.275 m), green = distance to nearest prop, blue = catch points (doorsteps, pipe feet, post feet, inside corners). B: red = inside corners, green = doorsteps, blue = pipe and post feet | street and lockout files only; they have to be made again for any other file and whenever a prop moves; the code names the street's objects (see section 11) |
| **surface direction** | Geometry box, Normal; WETNESS turns it into "ground / wall / roof" with soft limits (ground within about 20 degrees of flat, wall steeper than about 60 degrees) | up-facing or not | roofs of 35 degrees fall in "roof" (normal z 0.82) |
| **object coordinates** | Texture Coordinate box, Object | the wall's own frame (z = 0 floor); on ground objects the same as world | the wall wet pattern uses it already |
| **height above the ground** | inside WETNESS only: z - y x 0.0699 - offset | where the wet foot band stops | not an output; the 4 degree slope is a number typed into the group |
| **distance from the camera** | Camera Data box, View Distance (JOINTS uses it to fade its relief from 5 m to 20 m) | metres | plate camera only |
| **Lowness** | an input of WETNESS, wired by the apply script from the distance to the middle line (road 0.6 to 2.1 m, pavement 2.7 to 4.4 m) | "water gathers here" | a street-specific guess, not measured from the geometry |

**Two warnings about these read-outs.** (1) Every amount dial was fitted on the main camera's road, and the numbers change with the camera: the puddle dial 0.5 gives 8 % puddle on the main camera's road, 8.4 % on the lockout camera's, **32 %** on the notice-corner camera's and 19 % on the whole street from above. A new "how much" dial has to be tied to a share of a surface in a given view, and checked on every camera. (2) The rubbish builder measured that its mask is faint in the 540 x 960 main view because the gutters are far away; it reads at plate size and in the close views.

---

## 5. Masks that are missing, and how to make each from the geometry

The method is the one `make_places_pictures.py` uses: ask Blender's own geometry (a BVH tree is a fast "what is near this point / what does this ray hit" search), write the answers into a small flat picture of the street from above (or of a wall front on), and let the shader read the picture by world or wall coordinates. Never by vertex colours (section 2).
Everything below was tried on the street copy unless it says "not tried". Timing is on this computer, one thread, Python loops.

### M1. Shade: sky openness (grounds and walls) and sun shadow
* **How:** from each dot, shoot 48 fixed rays spread over the hemisphere above the surface (cosine-weighted, 40 m long) at the real buildings and posts; openness = share that escapes. Sun shadow: one ray from each dot toward each sun lamp of the file.
* **Cost:** 0.77 ms a dot, so 27,000 dots (10 cm dots, 9 x 30 m) in 21 s. A full street picture at 4 cm (225 x 2100 = 472,500 dots) would take about 6 minutes; 8 cm dots or 24 rays make it 1.5 minutes. A wall front at 2 cm a dot (50 dots a metre: 225 x 345 = 78,000 dots) takes about a minute per wall mesh. Once per set.
* **What it shows on the street** (`study/out/s3/shade_and_ledges.json`, picture `openness_top_down.jpg`; at y = 4, 10, 24, 45 m): road middle 0.46 to 0.52, the rest of the road 0.40 to 0.56, gutters 0.40 to 0.54, pavement 0.23 to 0.50 (lowest next to the houses), the wall face 0.17 to 0.23 near the ground rising to 0.23 to 0.33 at 5 m. Steps, lamp-post feet and the nooks beside doorsteps show as dark holes (sheet panel 3). **So the street is an even, dim canyon: shade is nearly the same everywhere except in the wall foot and the nooks.** A "moss goes in the shade" rule on openness alone will therefore put moss almost uniformly along the wall foot and in the gutter, and none in the middle: that is probably right, but it is not much of a signal.
* **Sun shadow:** the file's two suns are `dusk_skylight` (toward the sun: -0.198, +0.883, +0.425; energy 0.3) and `afterglow` (0, -0.995, +0.105; energy 0.2). With the houses in place 57 % of the ground sample is in the skylight's shadow and 14 % in the afterglow's. The two house rows get a wall normal-dot-light of +0.198 / -0.198 from the skylight and 0 from the afterglow: **the street's lights hold no real "north-facing wall" signal** (they are dusk lamps and two dim sky lights, not a sun path). For moss on "the shaded side" the set's settings must **declare** a weather or shade side (a vector toward the sun, or a named row); the courtyard has a real golden-hour sun (toward the sun -0.944, -0.244, +0.223) and can read it from its lamp.
* **Not to use:** EEVEE's Ambient Occlusion node (screen-space, so it differs from Cycles, and noisy per sample; Scenario's skill measured that a threshold on live AO or Bevel averages to fractional values at the border, 17 to 18 % at any sample count) and the Bevel node (it returns the plain normal in EEVEE, so the masks go black).

### M2. Run-off lines (under sills, ledges, eaves and pipes), made from the geometry
* **What exists:** the wetness layer's Streak Mask (section 4), made from numbers typed from the street builder (`GROUND_WINDOW`, `UPPER_WINDOW`, `FACADE_LAYOUTS`, `EAVES_HEIGHT`): 5 sources per door layout (1 ground sill, 2 upper sills, 2 eaves). It exists on walls only.
* **How to find the sources from the geometry:** in the wall shell, trim, window and door objects, take every face that faces up (normal z above 0.9), has an area above 0.02 m2 and is at least 0.25 m wide, within 0.8 m in front of or 0.6 m behind the wall face. Record its height above the floor, its position across the front, its width and its depth.
  I ran it on one cottage (`right_row_a_cottage_01`; `study/out/s4_ledges.json`). It found: ground-window sill at 0.85 m (centre across 0.95 m, 1.05 m wide, sill stone 1.23 m wide, 0.30 m deep); two upper sills at 3.55 m (across -1.15 and 0.95 m); the door threshold at 0.0 m (across -1.15 m) with two steps in front (0.18 and 0.48 m out, 1.1 to 1.22 m wide, heights -0.08 and -0.26 m); lintels at 2.68 m and 2.88 m and 5.18 m; a string course at 3.1 m and an eaves course at 5.9 m, both the whole 4.48 m of the front; a fascia at 6.1 m. **The builder's hand numbers (0.85, 3.55, 6.0 m; door -1.15; ground window 0.95; upper -1.15 and 0.95) all come out of the geometry**, so the settings file does not need them.
  The cottages' trim objects are separate per cottage (442 faces each) but the wall shells are shared; I ran only one cottage and assume the others match (not checked).
* **Pipes:** in the same cottage the pipe mesh (388 faces) has a vertical run at 2.0 to 2.1 m across the front (the end where two houses meet), 17 to 19 cm in front of the wall face, from -0.77 m (below the floor, to the pavement) to 5.91 m, and the eaves gutter runs the whole width (-2.25 to +2.25 m) at 5.9 to 6.0 m. These are the things that stain the wall below them: pipe joints and brackets (not found: the mesh does not mark them), hoppers, the gutter's two ends, the downpipe's foot on the pavement.
* **How the mask is made:** one small picture per distinct wall mesh, in the wall's own frame (across the front, up from the floor), 50 dots a metre. For each ledge a streak hangs below it, as wide as the ledge plus a margin, with ragged sides, stretched downward, fading with the distance below (the `WETNESS DRIP` group already does exactly this for a (centre, half width, top, length) list: reuse it, feed it from the finder instead of the typed numbers). Pipes: a narrow streak from each joint and a wider tide below the hopper.

### M3. Traffic and footfall lanes, and the crown of the road
* **Crown:** measurable. The road is 8.0 cm above the line the channel follows at the middle line (x = 0), 6.3 cm at |x| = 1.0, 2.6 cm at 1.8, 0 at 2.2; the channel's bottom is 2.5 cm below the line at |x| = 2.4; the kerb top is 13 cm above it; the pavement rises to 14.5 cm at |x| = 3.6 m (`study/out/s7_camber_kerbs.json`; the ground rises 4 degrees along +y). A "crown" mask is just that height above the neighbouring channel; the wetness layer's "Lowness" is its opposite. Make both from the ground height picture instead of from |x|.
* **Lanes:** not in any geometry. They must come from the set's settings as lines with a width (street: wheel tracks and the middle of the road; pavement: along the wall and from each door to the kerb). The doorway empties exist (28 of them, `*_doorway`, at x = +-3.45 and y at each door) so "door to kerb" lines can be made from them. Which lines are right for a 1926 pit village is for the research step, not for the pipeline; I only say the data to build them is there.

### M4. Wall corners, reveals and the foot of the wall
* On the ground: inside corners, doorsteps and pipe and post feet are already in places picture B.
* On the walls: the fronts are flush (terraced), so "corners" are the edges of the openings (reveals, 0.12 to 0.24 m deep, found from the front face's cut-outs and the reveal faces) and the row ends and the 4 m back-lane gaps between row a and row b (the gable walls). Find vertical convex edges of the wall shell and of the openings (a face-to-face angle test on the mesh edges) and write a distance-to-corner channel into the same wall picture as M2. Not tried.
* Wall foot: height above the floor is just the object's z (floor = 0). The wetness band is already measured that way.

### M5. Edges of kerbs and flags
* **Kerb:** real geometry (187 stones, sharp edges marked). A distance-to-sharp-edge picture of the top view, made like the places pictures from the kerb mesh, gives the chipped edge and the joint every 0.92 m. Not tried.
* **Flags and setts:** no geometry; the edges are only in the photo. For the setts the joint picture exists (`sett_joints_clean.png`). For the flags nobody has made one: `make_joint_pictures.py` would need running on `large_grey_tiles_colour.jpg` (3 m tile, 341 dots a metre; how many flags the photo holds I did not count). Not tried.

### M6. Cavity and curvature
* Not from Blender's nodes in EEVEE (see M1). Not from vertex curvature either (Scenario's `curvature_attribute` depends on vertex density; "on a low poly, bake from the high instead"; the walls have 32 faces).
* **From the photos' height pictures:** `set_copy/polyhaven_maps/` already holds a displacement (height) picture for the road, the flags, the red brick and the stone brick wall. Cavity = a blurred copy of the height minus the height (the mortar joints and stone gaps are the cavities). This is what `20_make_smoothed_pictures.py` already does for the normal maps. It is tied to the photo's coordinates, like JOINTS, and it is what Price's "burn the soft mask with a contrast-stretched height picture so that growth stays in the grout" (Scenario procedure P18) needs. Not tried on the walls.
* For props and the courtyard's rocks: bake ambient occlusion in Cycles to a picture (Scenario's baking skill has `bake_high_to_low` and `curvature_from_normal`). Not tried.

### M7. Height above the ground and "how low is this spot", from the geometry
The wetness layer's wall band uses `z - y x tan(4 degrees) - offset`, and its puddle depth uses |x|. For other sets both must come from the ground: a ray from above to the ground objects gives the ground height for every dot of the ground picture (I do this for 27,000 dots in my openness test; make_places_pictures does it for 472,500 dots in 5 s). Slope = the picture's gradient; lowness = the mean height of the neighbourhood minus the dot's height. Not tried as a picture.

### M8. Distance fade
JOINTS fades its relief with the camera's View Distance (full to 5 m, 10 % at 20 m) because a steep slope far away turns into single white ticks. Every new relief (cracks, weed tufts, moss fuzz) needs the same fade, and the colour of fine detail must fade to a flat average tone with distance. The numbers (section 7) say where.

### M9. Per-object variation
Seven houses share one mesh. Use the object's Random (Object Info) or its position as a seed so that neighbouring houses differ. The rubbish layer varies "from house to house" with a slow noise along y (0.6 to 1.35 times): that is street-specific; the kit should use the object seed.

---

## 6. The lockout shot file against the street copy; cameras and sizes

| | street copy (`set_copy/street.blend`, 1.4 MB) | lockout shot file (`austerity-explainer/film-kit/assets/models/pit-village/lockout.blend`, 79.5 MB, opened read-only, never saved) |
|---|---|---|
| objects | 373 meshes, 65 empties, 33 lights, 2 cameras | the same plus 85 objects in collection `props` (53 meshes and the empty holders they hang from), 11 in `signs` (7 meshes), 22 brazier coals loose in the root collection |
| materials | 41 | 85 in use (44 more than the street's, all used by the props only, none shared with the street) |
| lights | 24 window lights (45 W, 0.5 m), 5 gas lamps (260 W, 0.12 m), 2 suns, 2 engine-house lights (400 W) | the same plus `brazier_light` 900 W, 0.25 m, at (0.95, 10.4, 2.2) |
| main camera | (0, 3, 1.89), vertical field of view 40 degrees, pitched up 6.5 degrees | moved to (-1.0, 1.2, 1.697), 44 degrees, turned 6 degrees to the right, pitched 8 degrees up. `side_camera` is unchanged. In the lockout file the name `main` is the lockout camera |
| render settings | EEVEE, 1080 x 1920, AgX "Medium High Contrast", exposure 0.6, 16 samples, ray tracing off, shadow rays 1, steps 6 | identical |
| load time | 0.8 s here | about a minute here; 3 s on the rented machine, but the first picture takes 14.7 s there (shader build of ~86 materials) |
| props | none | cart with wheels, sacks, brazier drum with fire, notice board with its notice and posts, dustbins, rusty bins, barrel, buckets, wash tub, step ladder, spade, lantern, coal heaps and lumps, iron gates, colliery name board, coal tub on a track |

* **Which objects are props:** the places-picture script decides by comparing names against `rubbish/work/objects_street.txt` (a saved list of the street copy's object names). I checked: all 53 + 7 non-street meshes in the collections `props` and `signs` are found by collection, but **22 brazier coals sit loose in the root collection**, so a collection rule alone misses them (they are glow-only and need no weathering). The kit's settings file should list "architecture" and "ground" by name pattern and treat everything else as a prop, and name the collections that are signs.
* **Signs keep their own lettering** (the film uses its own sharp copies, `lockout-signs.glb`): `notice` (material `notice-paper`), `name-board` (`colliery-board-paint`), `notice-board` (`black-boards`) must not be weathered; the posts and timber of the same collection can be.
* **Cameras** the earlier tests use (`apply_wetness_to_set.cameras()` and the rubbish runner), all vertical field of view with the plate's 1536:2730 shape unless noted:

| name | where | field of view | used for |
|---|---|---|---|
| `main` | the file's own camera (street: (0, 3, 1.9)) | 40 | the street plate; test set 540 x 960, 16 samples; plate 1536 x 2730 |
| `lockout` | (-1.0, 1.2, 1.70) | 44 | the lockout plate; test set 540 x 960; plate 1536 x 2730 |
| `notice` | (2.99, 16.35, 3.19) | 64.4 | the notice-corner plate (the corner scene; sees mostly the pavement and the right-hand gutter) |
| `close_road` | (0.5, 6.0, 1.0) looking at (0, 11, 0.45) | 38 | the low close view; test set 640 x 480, 24 samples; plate size 1920 x 1440 |
| `wall_lamp` | (1.3, 7.6, 1.05) looking at (4.0, 11.3, 0.7) | 40 | the wall foot by the first gas lamp |
| `gutter_close`, `wall_close`, `drum_close`, `doorstep_close`, `left_gutter_close` | added by the rubbish runner | 40 to 50 | 960 x 720 and 1600 x 1200 close-ups |

* **The lighting test set** (`b09_lighting_test_set.py`, 22 pictures: 3 cameras x lightings x dry / wet / heavy): A dusk lamps (the film's own lighting), B brazier glare (= A in the lockout file), C a low sun from the right with the houses' shadows switched off, D flat overhead, E a strong low light at the far end of the street shining at the camera. Dry = wetness 0, wet = 0.85 / puddles 0.5, heavy = 1.0 / 0.8. The pass line for joints was a contrast against the stone, a "seen" share, and a cap against a black net. A weathering test set should reuse the rig and the pictures, but needs its own pass line (my first suggestion: "a mark reads if it differs from the surface by at least 12 % and at least twice the surface's grain", which is the line `measure_grid_visibility.py` uses; I chose it by eye, so it is a first try).
* **The shared look of all plates** (wet recipe, section 7 of the wetness note): EEVEE, ray tracing **on**, shadow rays 4, steps 16, 32 to 64 samples, and for pictures wider than 1080 the film's own shadow-memory fix (`shadow_pool_size '1024'`, `shadow_resolution_scale = 1080 / width`). The film's own files have ray tracing off and rays 1 / steps 6.

---

## 7. What the painter will see

### 7.1 Size of things in the plate
Measured with Blender's camera maths (`study/scripts/s5_pixel_footprint.py`, `out/s5_footprint.json`): how big one plate dot is on the ground right ahead of the camera and on the right-hand cottage wall 1.5 m above the floor. A painter dot is 1 / 0.45 = 2.2 plate dots.

| main camera: distance along the street (metres ahead of the camera) | straight distance | one painter dot **across** the street | one painter dot **along** the street |
|---|---|---|---|
| 3 m (y = 6) | 3.3 m | 1.7 mm | 3.1 mm |
| 5 m (y = 8) | 5.2 m | 2.9 mm | 8.8 mm |
| 9 m (y = 12) | 9.1 m | 5.2 mm | 29 mm |
| 13 m (y = 16) | 13 m | 7.6 mm | 61 mm |
| 21 m (y = 24) | 21 m | 12 mm | 162 mm |
| 29 m (y = 32) | 29 m | 17 mm | 310 mm |
| 45 m (y = 48) | 45 m | 27 mm | 747 mm |

The lockout camera is a little worse (1.7 / 3.0 / 4.3 / 6.9 / 9.5 mm across at straight distances of 3.1 / 5.0 / 6.9 / 10.8 / 14.8 m; along 2.9 / 9.1 / 19 / 48 / 90 mm). The wall (main camera): at y = 24, 64 mm per painter dot along the wall and 12.5 mm up; at y = 32, 122 mm and 17 mm (the walls only come into the main view beyond y of about 20 m: its horizontal field is 23 degrees). The notice-corner camera (64 degrees) is the close one: its wall at y = 24 is 50 mm along and 7.6 mm up; its ground 8.5 mm across and 33 mm along at 8 m, 16.5 mm and 132 mm at 16 m.
The rows for the dot just under the camera (4,500 dots a metre) and for the camera's own position were left out: they are at the very edge of the frame.

What this means, rules of thumb for sizes (my reading, to be checked in the painter step): a mark needs about 3 painter dots across to survive, i.e. across the street **about 5 mm at 3 m ahead, 9 mm at 5 m, 16 mm at 9 m, 23 mm at 13 m, 37 mm at 21 m**; along the street 3 dots is 9 mm / 26 mm / 87 mm / 180 mm. **Direction matters as much as size.** Flat marks painted on the road are squashed along the street by 3 times at 5 m and 8 times at 13 m, so a 2 cm crack that runs *along* the street (its thin side across the street) still reads to about 9 to 13 m, while a 2 cm crack that runs *across* the street (its thin side along it) is under one painter dot already at 9 m (29 mm a dot) and gone (probably why the cross-street joints turn into ticks; not proven). Things that **stand up** (weed tufts, moss clumps with relief, litter) are seen from the side and keep the across-the-street resolution in both directions: a 10 cm tuft is about 13 painter dots tall at 13 m. So real small 3D pieces read at the middle distance where painted flat marks do not. A hairline crack is gone by 5 m; stains and moss clumps should be 20 cm and larger; tone and colour have to carry everything beyond 15 m.
The sett joints may have fallen into this already: the ticks are the joints' lit edges seen at a few dots (section 9).

### 7.2 Brightness: where dark grime can show
Measured on my fresh 540 x 960 pictures of the main camera (rented machine, today's street and the wet state 0.85 / 0.5), mean brightness of each surface and the share of its dots under 0.13 and under 0.17, sampled by the ray labels (`out/s6b_labels_main.json`; these match the wetness note's table to the third decimal):

| surface | dry today: mean / under 0.13 / under 0.17 | wet: mean / under 0.13 / under 0.17 |
|---|---|---|
| road setts | 0.130 / 50 % / 94 % | 0.196 / 6 % / 36 % |
| pavement flags | 0.174 / 25 % / 51 % | 0.196 / 3 % / 45 % |
| gutter stones, kerb | 0.121, 0.101 / 55 %, 80 % / 95 %, 97 % | 0.145, 0.157 / 29 %, 31 % / 89 %, 64 % |
| brick walls (left), stone walls (right) | 0.089, 0.091 / 87 %, 79 % / 93 %, 89 % | 0.071, 0.084 / 90 %, 81 % / 95 %, 91 % |
| dressed stone, dark dressed stone | 0.097, 0.070 / 84 %, 95 % / 95 %, 96 % | 0.091, 0.073 / 86 %, 91 % / 96 %, 98 % |
| colliery brick | 0.103 / 95 % / 97 % | 0.109 / 89 % / 97 % |
| cast iron | 0.090 / 84 % / 92 % | 0.088 / 84 % / 93 % |
| roof slate | 0.122 / 63 % / 89 % | 0.141 / 42 % / 81 % |
| headframe steel, spoil heap | 0.091, 0.053 | same |
| painted woodwork (cream paint) | 0.205 / 44 % / 62 % | 0.200 / 47 % / 62 % |

**Why it matters:** the stage's own curve crushes darks (measured by the painter-test helper: painting brightness 0.08 becomes 0.02, 0.13 becomes 0.07, 0.17 becomes 0.13, 0.24 stays 0.24, 0.5 becomes 0.59; a wet painting's road arrived at 0.75 of its painted brightness, its walls at 0.76), and the stage lost the dark sett joints. In the one painting that was made (the lockout shot), the painter's mid-wall brightness was 0.14, higher than the 0.07 to 0.09 of the main-view plate's walls, so the walls are less hopeless than the plate says; they still end up in the crushed part.
So: **dark soot or dark stains on walls, steps, iron, colliery brick and the headframe are invisible in the film; they show only on the road (wet), the pavement and the cream paint.** On the walls a mark must differ by lightness (lime, salt, pale algae, lichen) or by colour (rust orange, green) from the stone. The five olive moss tones of the slate recipe (sRGB #2b2c23 to #545342) are brightness 0.16 to 0.32, lichen tans (#645c4f, #746a5c) about 0.36 to 0.41: stage-safe. The rubbish layer's dust film (linear 0.05 dry, 0.014 wet) works only because it lies on the road and pavement.

### 7.3 What the painter did to the last plates (read-only: `painter_test/notes`, `painter_round_2/`)
* It kept the wet look when the brief said so, kept reflections and puddles where the plate had them, tamed the blown-out glare, moved nothing (line-up needed no correction), added pale brush-stroke clouds to a plain sky (it ignored "no bright clouds"), made stronger and extra lamp streaks, added a few white paint highlights on pavement edges, garbled the small print on the notice, and painted the lamp glass pale instead of amber.
* **It did not make the walls read wet**: the plate hardly showed it either. So anything on the walls that the plate shows faintly will not be rescued by the painter.
* The brief needs one more sentence for each new thing ("keep the cracks, stains, weeds and moss where image 1 has them; add no writing; nothing modern"), as the earlier briefs got one for wet joints and rubbish. Whether the painter keeps hairline cracks, drops them as noise or turns them into brush strokes is **unknown**: no repaint with weathering has been made. The second painter round (running now, in `painter_round_2/`) is fixing the rubbish pieces and the joint ticks; I found no result file there yet, only comparison pictures of the pieces and ticks before and after.
* In a moved view the stage shows the film's old dry "behind painting" wherever a prop hid the road: 71 % of the road's dots in the moved view of the first wet test. A second plate with the props taken out is needed for the behind painting: **the weathering must then be the same in both plates**, so every layer must be a pure function of position and seed (no per-picture randomness) and the scatter must not move with the props. (The second painter round is adding a wet behind painting.)

---

## 8. How long a picture takes

Measured today (21 October, around 06:10 on this computer's clock) on the rented RTX 4090, through `render_client_cached.py`, with two other jobs running on it at the time (`study/scripts/run_timing_rented.sh`, results in `study/out/rented_timing/`; the three runs took 39 s in all). The existing runner `22_render_eevee.py` drew them; every picture was checked: not black, brightness 0.17 to 0.26 (mean), i.e. real pictures.

| run | what | seconds |
|---|---|---|
| A: street copy, main camera, 540 x 960, 16 samples | today 1.1, dry 1.6 (the layer is put on), wet 0.3, heavy 0.2; Blender start to finish 9.6 s (file read 3.9 s) | **0.2 to 1.6 a picture** |
| B: street copy, main camera, plate size 1536 x 2730, 48 samples | today 1.9, wet 1.4; start to finish 7.3 s | **1.4 to 1.9 a picture** |
| C: lockout file, lockout camera, 540 x 960, 16 samples | today **14.7** (shader build of the props' materials), wet 2.6; start to finish 22 s | 2.6 after the first |

From the earlier helpers' notes (rented machine): street 540 x 960 at 16 samples 1.2 s on average; lockout 1.8 s; plate at 64 samples 3 to 6 s (the lockout wet plate 3.8 s with joints, 5.9 s with rubbish: **the rubbish layer with its 547 boxes and about 6,400 to 7,200 small pieces added about 2 s a plate**); the whole 66-picture lighting test with masks: street 73 to 87 s, lockout 45 s; a Cycles joint-measuring mask 4 to 7 s; building the rubbish layer 2 to 5 s; places pictures 5 s (street) and 8 s (lockout). Downloading a folder as one tar file 7 to 11 s (picture by picture 140 to 180 s).
On **this computer** (no card, 4 shared cores): 75 to 85 s for a 540 x 960 picture, 92 s to 6 minutes for a wet one with the shadow settings, about 20 minutes for the full-size lockout plate (7 GB of memory), the lockout file about a minute just to load. My study scripts, which do not draw: listing 2 s; ledges 1 s; 27,000 openness dots 21 s; a 135 x 240 EEVEE test picture 15 to 20 s here.

What it means for the kit: a new layer's first picture in a run costs its shader build (1.5 s in the street, 15 s with the lockout's 86 materials), later ones cost a second or two. A full test round of 66 pictures with masks is about two minutes. The rented machine ends itself after 30 idle minutes; a first call after that waits 25 s to a few minutes.

---

## 9. Traps the earlier builders fell into (and one or two I found)

**Process traps**
1. **States must start with "today"** (`22_render_eevee.py`): the layer goes on at the first non-"today" state and stays; "today" later would draw the layered street. Draw "today" first, in its own Blender run if in doubt.
2. **Stale pictures come back from the rented machine.** The runner skips a picture whose file already exists; a re-run on the rented machine only drew the missing ones, and the download brought the old (black) ones back over the new. `rent_run.py` now clears the run folder first (`--keep` to keep it). Name pictures differently per file (`lockplan_*`) when two files write to one folder.
3. **The old rent scripts call the old client.** `rent_run.py` and `remote_tools.py` in `rubbish/tools/` use `runpod/render_client.py`; the instruction now is to use only `render_client_cached.py`. Copy and fix the path in the kit.
4. **Upload every changed script or file** before using it there. The store has `set_copy`, `tools` and `maps`; it does not have `relief_and_rubbish` or any new folder.
5. **Border renders hide the EEVEE speckle** (a partial picture did less shadow work): measure whole pictures, at the size that matters.
6. **Budgets were always too small**: 18 Blender runs against about 10 (wetness round 2), 34 against 20 (rubbish), about 60 against 40 (joints and rubbish together), 27 on the rented machine against 20. Plan for double.
7. **Disk space:** while another helper unpacked a 520 MB bundle, free space dipped to 0.9 GB. There is about 2.1 GB free now, shared by three jobs.

**Picture traps**
8. **White speckle on shiny surfaces in EEVEE is soft-shadow noise,** not the relief picture, not ray tracing, not light size (five runs to find out). Cure: `shadow_ray_count` 4, `shadow_step_count` 16, 32 to 48 samples (grain 0.026 to 0.008 on the road's left third; at 16 samples still 0.0115). Cycles never showed it (it does not use shadow maps and its pictures were denoised). **Anything new that makes a surface shiny (wet streaks, glossy moss, water in cracks) can bring it back.** Scenario's lighting skill suggests rays 2 / steps 12 for finals; ours need the maxima (4 / 16).
9. **White ticks on sett corners** (rows of short bright marks in the middle distance, "hooks" in the checker's sheet): steep stone-edge slopes far away catch a lamp for one dot. Reduced, not cured, by fading the relief with distance (full to 5 m, 10 % at 20 m); the second painter round is working on it. Any new relief needs that fade from the start.
10. **The stage crushes darks** (section 7.2), so dark detail on dark surfaces is lost in the film even if the painter keeps it.
11. **Props stand dry on a wet road, sacks look as if they hover** (the plate had no contact darkening); the painter kept that. Props need their own contact grime.
12. **Blown-out glare** (about 4.5 to 4.7 % of the lockout plate's lower third over 0.97 under the brazier, later 2.8 % because the rubbish and joints made the road a little darker). Lights near new glossy marks can do it again.
13. **Calibrations belong to a camera** (section 4 warning).
14. **Honest measures:** the joint pass count was 21 of 22 with puddle and rubbish dots left out, **18 of 22 with every dot counted** (the fresh checker). Decide up front whether covered dots count.
15. **Pieces:** a few readers thought straw looked like matchsticks, coal chips like faceted gems, cinders like round pock-marks; the first rubbish look had all three. Small separate 3D pieces need many facets, ragged shapes and many sizes; 70 per m2 of lumps was the density used.
16. **Plate only:** nothing of wetness, joints or rubbish is in the `.glb` (2 cm a dot ground maps cannot hold a 1.6 cm joint), and only about 2 % of a moved view shows the glb's own surface. The audience sees the painting; weathering that is only in the plate lives or dies by the painter.

**Wiring traps**
17. The five-plug hook fails on plain numbers (section 3.3); the order trap (3.5); `show_mask` once forgot which box fed the surface the second time it was used and left black emission boxes (the "black road" pictures); `Joint Shade` changes the material's graph only when Joint Shadow is above 0 at the time the layer is put on.
18. **Hard-coded street names and numbers** in the earlier code (list in section 11).
19. **Per-file helper pictures:** the places pictures exist only for the street copy and the lockout file; moving a prop means running the script again.
20. **Names:** in the lockout file the name `main` and the name `lockout` are the same camera; the street's `main` is a different camera.

---

## 10. What can be reused

### Slate layers (`recipes/slate_layers/layers/`: moss.py, damage.py, ...)
* **As they are: no.** MOSS and DAMAGE are shader groups built with `layer_interface.make_layer_group` and read a "layout bundle" of eleven numbers per dot (piece number, position on the piece, distance to the piece's edge and to its upper edge, base height ...) and a tile coordinate in "tile units"; the street has no such pieces on the 3D surfaces. They make a flat picture of a tile that is baked from straight above.
* **What carries over, by copying:** (a) the **method**: moss where a "strength" (rules: drips, wet upper part, joints, low spots, damage) plus tall wobbly clump noise is over a threshold set by Coverage; flat painted-look clumps, tall (stretch 1.8), ragged edge, a fringe of down-pointing teeth from a noise that depends only on the sideways position, flat steps of five tones, rim lighter, shadow under the upper edge; lichen as discs and rings on jittered grids in colonies. (b) the **numbers**: moss tones #2b2c23, #35372a, #3f4032, #49493a, #545342; lichen #645c4f, #746a5c, #524c40; cluster 0.05 tile units, drip length 0.12, fringe teeth 0.009, rim opacity and core opacity for a see-through wash. (c) **the four rules** (`05 Lessons`, section 3): every random number comes from the position or piece plus the layer's own seed; Amount 0 gives exactly nothing; a layer reads only declared inputs; prove independence with a table (change a layer's seed or switch it off and count the dots that change outside its mask). The kit's layers should be held to the same four.
* **DAMAGE** paints, in order, flakes along the lower edges, pits, scratches, cracks that run from an edge (mostly downslope, thinning to a point), notches and broken lower corners; every kind sinks the surface and makes it rougher. The idea that carries over to the kerb, steps and sills is its **reach rule**: a dot is flaked when its distance to the piece's edge is smaller than "how far in flaking may reach here" times a noise, so chips are teeth along an edge with clean stretches between (the kit needs the distance-to-edge picture of M5 for it). Its flat colours: pale cream and tan flakes (#675a4a to #887b6b), near-black for the joint.
* **A possible hybrid, not tried:** bake the slate MOSS/DAMAGE tile to a picture and multiply it by a geometry mask (the picture gives the look, the mask the place). It repeats every tile length, so only for small features. The slate recipe reported moss "not useful (tried twice as soot, off)" for brick, "as rust" for wood and metal, "as puddle water" for mud, so the look is flexible but the layer is tied to its bundle.
* **Brick GRIME (`reuse_trials/brick/grime.py`, soot clouds over bricks and mortar) and wood CRACKS (`reuse_trials/wood/cracks.py`)** have the same bundle dependence. Reusable as ideas and numbers: soot cloud width 0.09 tile units, 1.8 times taller than wide, run streaks 0.012 wide and four times taller, specks 0.007 at the rim, colours #45332b and #2c221e; mortar mottle tones #8e7259, #a48669, #5e483a; cracks: cells of one lane x one stretch, at most one crack per cell, narrowing to a point at both ends, a pale lip on one side (#9c7350), crack colour #120d0b, width 0.0028 tile units (3.5 dots at 1254). (Their crack cells run along a grain; stone cracks branch and stair-step through mortar and need a different path.)
* Also reusable as they are: the cookbook's guides on shapers (Map Range, Color Ramp), pattern makers, the painted look, and `lib/recipe_tools.py` / `lib/contrib/builder.py` (seamless noise and cell helpers); `lib/bake_harness.py` (photographs a flat surface from above to get maps: the way the wet maps were made).

### Our own earlier code
* **As is:** the node-building helper class `Net` (in `wetness_layer.py`) and its extension `Builder` (in `rubbish_layer.py`: Voronoi cells, picture look-up, noise at a point); the `WETNESS DRIP` group; the picture-runner design (a JSON job list, a camera, a lighting A to E, a state, a look, a size and samples per picture; masks and measures; skip pictures that exist); the lighting rig (`b02`); `rent_run.py`'s flow (upload tools, run one Blender job, wait, fetch one tar); the measuring scripts (`22b_numbers.py` grain and black-hole numbers per surface; `measure_grid_visibility.py`).
* **To change:** every street name and number in them (section 11); the client path; the camera table; the places-picture script's regular expressions.

### Scenario's Blender skills (`/home/user/Music/.claude/skills/`, installed today by another job; MIT licence)
* **As is, usable:** `grunge_group` (Variation, Grunge and vertical Streaks noise from one vector, works in EEVEE and Cycles, coverage control); `audit_material` (colour spaces by role, bump distance, noise detail, emission strength ...) and `value_report` (albedo within 30 to 243 sRGB, roughness spread) as gates, run on small pictures (the skill says to use EEVEE, 256 pixels, 8 samples and a scratch folder on this shared computer, never the film's folder); the Price recipe for grime "mask burned by the height picture"; blend modes (Multiply for grime and mould, Screen for efflorescence and lime, Subtract on height for spalling), "chain order sets age"; the numbers table (dielectric albedo sRGB 30 to 240, Bump Distance 0.001 to 0.01, Noise Detail at most 5, brick roughness about 0.7).
* **Usable after copying a small function:** `_source` (the hook idea); GN `scatter_tree` (density x mask, a world-up slope limit, an object or collection to scatter, per-instance random value for the shader). Its mask is an attribute or a vertex group, which our coarse ground meshes do not carry, so for weeds and moss tufts it needs the picture-reading mask of `rubbish_pieces.add_scatter` instead (a Poisson-disk scatter driven by the places pictures; that code already scatters 6 kinds of pieces).
* **Not usable for the plate:** `edge_wear_group` and `add_wear`'s edge and cavity parts (Bevel and AO nodes: the skill itself says the Bevel node gives the plain normal in EEVEE, so the masks go black, and AO is stochastic); `curvature_attribute`, `mask_from_points`, `write_vertex_values` (vertex density: walls have 32 faces); `TexelMap` and `paint_stroke` (needs unique texture coordinates; the street's are repeated box projections); the GUI painting steps (no window here).
* **Where it disagrees with us:** shadow settings for EEVEE finals (rays 2, steps 12; ours 4 and 16); "specular stays 0.5" (the wet layer raises it on the road); both are fine for what each was made for.

---

## 11. Street facts that are typed into the earlier code (they must move into `sets/pit_village_street.json`)

| where | what is typed | meaning |
|---|---|---|
| `apply_wetness_to_set.py` | the `MATERIALS` table (11 material names, picture names, porosity ...); `FACADE_LAYOUTS`, `GROUND_WINDOW`, `UPPER_WINDOW`, `EAVES_HEIGHT`, `HALF_WIDTH`, `WALL_FOOT_OFFSET`; `_lowness_from_x(0.6, 2.1)` for the road and `(2.7, 4.4)` for the pavement; `SLOPE` = tan 4 degrees; `cameras()`; mesh name `cottage_shell_{material}_{layout}_walls` | which materials, which family; where ledges are (now findable); the street's width; the slope; the camera numbers |
| `wetness_layer.py` | puddle dial curve fitted on the main camera's road (0.79, 0.52, 1.25); Ground Slope default 0.0699 | calibration, slope |
| `joint_layer.py`, `apply_joints_to_set.py` | the picture path (2 m repeat), material name `street_setts` | setts only |
| `rubbish_layer.py` | `X0, X1, Y0, Y1` = -4.5, 4.5, -12, 72; gutter centre 2.35 and half width 0.15; kerb reach 0.45; crown clear 1.3 to 1.8; kerb top 2.48 to 2.72 m from the middle line; the four material names; the distance from the middle line (the absolute value of x) as "across the street", with the street centred on x = 0 and running along y; the house-to-house slow noise along y; all colours and roughnesses of coal, ash, mud, straw, paper, leaves (a **look preset**) | the street's shape, the look |
| `make_places_pictures.py` | ground object names (`street_setts`, `street_channels`, `street_kerbs`, `street_pavements`); regular expressions for walls, pipes, posts, doorways; walls and pipes only counted more than 2.7 m from the middle line, posts more than 1.6 m; grid 225 x 2100 at 4 cm; distance scale 1.275 m; ray length 0.45 m at 0.25 m height; the props rule (not in `objects_street.txt`, within 4.4 m of the middle, under 70 m along, not floating) | families, grid, props |
| `rubbish_runner.py`, `b02` | ground object names for the ground mask; lamp names `dusk_skylight`, `afterglow`; `HOUSE_PREFIXES`; the back light at (0, 66, 5.9); camera labels | test rig |

Starter values for the street's settings file, all measured above: ground objects `street_setts`, `street_channels`, `street_kerbs`, `street_pavements` (identity transform; `ground` is the yard); wall objects `*_cottage_NN_walls` (28; frame: floor z = 0, wall face x = 0, minus x toward the street; right row not turned, left row turned 180 degrees); trims `*_trim`; pipes `*_rainwater`; posts `gas_lamp_N_post` at x = +-3.03 and y = 11, 25, 39, 53, 64.5; doorways `*_doorway` empties at x = +-3.45 (28); grid x -4.5..4.5, y -12..72; ground slope 4 degrees along +y; crown 0.08 m; channel dip 0.025 m; kerb top 0.13 m; lights: toward the sun (-0.198, 0.883, 0.425) and (0, -0.995, 0.105), plus window lights and lamps as points; units metres; materials not to weather: the glow and sky ones (`window_*`, `engine_window_glow`, `lamp_glass_glow`, `sky_dome_glow`, `interior_dark`), and in the lockout the sign materials (`notice-paper`, `colliery-board-paint`, `black-boards`).

---

## 12. A quick look at the Japanese courtyard (read-only; only to check that the kit's hook is general)

Opened `astra-work/out/courtyard_final.blend` (7.9 MB) and listed it: 88 meshes, 10 curves, 7 lights, 134 materials, **Cycles, 2400 x 1600 (a landscape picture, not the street's tall one), AgX "Punchy", 64 samples**, sky texture as the world, camera at (-5.2, -5.6, 3.0), 49.6 degrees. The lights: a golden-hour sun (energy 8, toward the sun -0.944, -0.244, +0.223), a lantern point light, four hall-glow area lights, a cool sky fill.
* Of 134 materials **68 are Principled boxes with every input a plain number** (no wire at all), 14 have a colour or normal wire, **46 are the add-on's own shader groups** ("FOUNDRY / Wet Stone" for each stone and a wood group: they end in a Shader output, no Principled box on the surface), 6 are glow-only. (Two of the 82 with a Principled box, the leaves, have a Mix Shader after it, which is why my splice test skipped 54 and not 52.) So the courtyard needs the "wire or number" hook even more than the street, and needs a rule for the add-on's groups (put the new layer in front of the group's colour input if it has one, or mix the group's result with a second shader, or leave them alone). Their groups are called "Wet Stone", so they may already carry a wet look (not inspected).
* The ground "Moss and earth", the "Moss grouped bodies" (32,365 faces), the pebbles, the leaves and the maple and pine masses are already **real geometry or procedural by the add-on**; moss added by the kit must not double them.
* Many small stones have 61 to 72 faces with a Bevel modifier and a geometry-nodes modifier (the add-on's chiseling): vertex-based masks would be crude there too.
This is a 20-minute look, not a courtyard study.

---

## 13. What I tested, what I did not, what I am unsure of, and what went wrong

**Tested (by running it):** the old hook on all materials (three files); the new hook on all materials (three files); a do-nothing group on every street material gives an identical picture; the order trap; the Streak Mask on a dry street (drawn); sky openness and sun shadow on the street copy (numbers and a picture); ledge and pipe finding on one cottage; the camber and kerb geometry; the pixel footprints of three cameras; the shares of the picture by material and family for four cameras; brightness by surface in fresh pictures; timing on the rented machine (three runs, eight pictures, checked not black); the lockout file's collections and props.
**Left on the rented machine:** my timing script and its small output folder, under the same paths as here (nothing else; I removed the tar file I used to bring the pictures back; I did not touch `~/.runpod` and did not stop the machine).
**Read, not run:** all the earlier layers' code, the recipe notes, the slate and trial layers, the Scenario skills (including the code of its functions), the painter test notes.
**Not tested:** any new weathering layer (none exists yet); the painter with weathering; Cycles; the `.glb` and the stage; the ledge finder on cottages other than `right_row_a_cottage_01` and on the left row (turned 180 degrees); wall corners and reveals; kerb and flag edge pictures; cavity from the photo height pictures on walls; the slate-tile hybrid; the courtyard beyond the listing and the do-nothing hook (no courtyard picture drawn); how a layer with 500 boxes on the walls (28 houses, 4 material copies) costs in a plate (the road's RUBBISH cost about 2 s); the hook on the lockout's imported materials in a picture (only the wiring was tested).
**Unsure:**
* The openness numbers come from 48 fixed random directions per dot (not smoothed, not compared with a picture); the dots near steps and posts read 0 where the dot is inside an object.
* The footprint table is the ground right ahead of each camera's middle line (the x of the camera, or 0 for the notice camera), not an average over the picture; the elongation along the street depends on the camera's height above the ground and the 4 degree slope.
* The brightness table is from 5 x 5 dot patches at the ray-grid centres of a JPEG (quality 80) of one 540 x 960 picture per state; the shares of dots under 0.13 move with the lighting and the shadow settings.
* My "3 painter dots to survive" is a rule of thumb, not a measurement of what the painter keeps.
* Where each kind of mark belongs in a 1926 County Durham village is not in this note; that is the research step.
* The suns of the street copy are `preview` lights of the set builder; I did not check whether the film's own scene (`lockout-test.js`) lights the walls differently.
**What went wrong (all of it):**
* My first run of the sky-openness test hit the eaves and roofs instead of the pavement at |x| of 3.6 m and more (a ray from above stopped on the roof), so it first said the pavement next to the houses was 0.88 open. Found by checking a row of points (the object under x = 3.8 m was a rain gutter 7 m up). Fixed by taking the ground height from a tree of the four ground objects only (what `make_places_pictures.py` does); the numbers above are after the fix.
* My first timing script on the rented machine did nothing: the log file name held a path with slashes and `bc` is not installed there. It ended after 0.1 s with return code 0, which looked like success; I read the log tail, fixed it, and ran it again. Whoever reuses `rent_run.py` should check the log tail, not the return code.
* One facade sample of my openness test (left wall, y = 10, 1 m up) read 0.0 because the point was inside a doorstep; I left it out of the numbers.
* The picture sheet's first layout had overlapping titles and a cut-off note; fixed.

---

## 14. What I would do next (for whoever builds the kit)

1. Build the chain first, before any look: one list per material, the five plugs plus Metallic, "wire or number", add / remove / move / rebuild, a self-test that a do-nothing group gives an identical picture on every material of all three files (my test is the model), and a self-test that removing layers in any order leaves the right wires.
2. Make the geometry reader write: ground picture (height, slope, openness, sun shadow, distance to walls, steps, props, pipes, posts, kerb edges), wall picture per wall mesh (run-off lines from found ledges and pipes, reveal and corner distance, openness), all from the settings file; run it on the street and on the lockout file; time it.
3. Put the distance fade and "amount 0 = exactly nothing" and "own seed" into every layer from the first line.
4. Start with the two layers that read best at painter size: **run-off stains and tide marks on the walls** (vertical, long, lighter or coloured; mask already half there) and **growth along the gutter, the kerb foot and the wall foot** (moss and tufts; masks already there). Draw 5 pictures at 540 x 960 and 2 at plate size on the rented machine (a minute) before anything else.
5. Measure with a visibility line (mark differs by 12 % and twice the grain), per camera, with every dot counted and also with covered dots left out.
6. Ask for a repaint only after a plate shows the marks at 100 %.

---

## 15. Files

All under `proc-work/street_wet/grime_and_growth/study/` (about 3 MB). Study scripts in `scripts/` (each starts with a plain note and its run line; none saves into the street files): `s1_list_street.py` (materials, families, lights, cameras), `s2_walls_and_trim.py` (walls, trims, pipes, shared meshes), `s3_shade_and_ledges.py` and `s3b_debug_pavement.py` (openness, sun shadow, ledges), `s4_ledges_and_pipes.py`, `s5_pixel_footprint.py`, `s6_view_shares.py`, `s6b_label_grid.py`, `s7_camber_and_kerbs.py`, `s8_hook_test.py`, `s9_splice_test.py`, `s9b_splice_render_equal.py`, `s10_order_trap.py`, `s11_lockout_props.py`, `s12_streak_mask_dry.py`, `run_timing_rented.sh`, `make_sheet.py`. Results in `out/` (`street_listing.json`, `lockout_listing.json`, `courtyard_listing.json`, `street_walls_trim.json`, `s3/`, `s4_ledges.json`, `s5_footprint.json`, `s6_shares_street.json`, `s6_shares_lockout.json`, `s6b_labels_main.json`, `s7_camber_kerbs.json`, `s8_hook_*.json`, `s9_*/`, `s9b/`, `s11_lockout_props.json`, `s12/`, `rented_timing/` with eight small JPEGs of the timing run).
Picture: `proc-work/25 Street grime, cracks, stains, weeds and moss - pictures/25 Pipeline study - what the street can tell the new layers.jpg` (the main view coloured by family with shares; the run-off mask that already exists; the sky-openness map).
