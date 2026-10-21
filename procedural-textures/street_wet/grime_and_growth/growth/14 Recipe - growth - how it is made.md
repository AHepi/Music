# 14 Recipe - growth - how it is made

Plain words. This is the growth builder's part of the weathering kit: small separate 3D weeds and moss cushions that stand on the ground in the plate. Code: `kits/weathering/growth/`. Pictures and numbers: `street_wet/grime_and_growth/growth/`. Written 21 October 2026.

## 1. What it is

A hidden helper object stands a few hundred small plants on the street's ground (and on the courtyard's earth and stones). They are real little 3D things: they catch the light, throw a tiny shadow and stand up, so they keep their size in the plate where a painted mark would not. They are in the plate only (not in the glb). The foundation's masks say where a plant may grow; the layer never knows which place it is in.

Nothing about the street or the courtyard is in the code. Everything that belongs to one place is in a small file of that place (`growth/growth_sets/<set id>.json`, to be moved into the set file as the key `growth`); the look (a sooty 1926 street, a mossy courtyard) is a few dial values.

## 2. The parts

| file | what it does |
|---|---|
| `species.json` | the piece library as data: ten kinds (meadow-grass, dead grass, pearlwort, dandelion, greater plantain, groundsel, chickweed, shepherd's purse, ivy-leaved toadflax, moss cushion strings), sizes by the 1926 rules, shares, colours, what each likes (damp, light, wall foot, seams) |
| `pieces.py` | builds every shape (bent blades, toothed rosette, ribbed broad leaves, stalk with lobed leaves, mat of paired leaves, spiked rosette, trailing stem, star cushion, string of lumpy cushions) in several variants each, 40 to 210 ragged faces, and the material (colour, wet look, no coat) |
| `scatter.py` | the generic engine (Geometry Nodes): which points, which plants, how big, how many |
| `local_masks.py` | two private pictures made from the foundation's pack: the wall-foot strip and the gutter-side strip; also the numbers the counting needs |
| `apply_growth.py` | the door into the kit: `register(kit)` then the same calls as any layer (`apply`, `layer_on`, `layer_off`, `set_dials`, `set_master`, `set_state`, `remove`); also `pieces(kit, visible)` and the checking view `layer:growth` |
| `dials_growth.py`, `growth_names.py` | the extra dials, and the plain tables (no Blender needed) |
| `report_growth.py`, `runner_growth.py` | write `pieces.json` (position, kind, size of every plant of a picture); the runner also draws extra cameras and the layer view |
| `selftest_growth.py`, `measure_growth.py`, `plan_growth.py`, `sheet_growth.py`, `gallery_growth.py`, `jobs_growth.py`, `run_growth.py` | the tests, the measures, the plan picture, the sheets, the piece gallery, the job lists |

## 3. How a plant gets placed (in this order)

1. **Candidate points.** A Poisson-disk set of points (no two of one kind closer than its spacing, 0.12 to 0.20 m, 0.07 m for moss) is laid on the target ground, only on faces within the pieces distance of the picture's camera and inside a cone round the camera's axis (nothing is made behind the camera or far beside the frame). The points of a face do not depend on the other faces, so a plant stands in the same place whichever camera draws the picture.
2. **Keep or drop each point.** A random number is compared with a probability made from: the site (`weed_site` for weeds, `moss_site` for cushions, plus a wall-foot strip and a gutter-side strip for weeds, each with its own gain) x what the kind likes there x the **hard gates** (keep-clear from 0.4 up, footfall from 0.6 up, road crown from 0.6 up, no ground, under water: exactly zero) x the **rubbish rule** (full density where the litter mask is under 0.45, linearly less up to 0.75, none above; moss stops between 0.30 and 0.60) x existing growth (the add-on's moss is not doubled) x the distance fade (18 m, fade 5 m).
3. **Clear of litter.** A weed is dropped if it would stand within 5 cm (in x and y) of a real 3D piece of the earlier litter layer (the set names those objects).
4. **Instances.** Each kept point picks one of the kind's variants, stands along the ground's normal blended with straight up (tufts upright, cushions along the surface), turns (free, or along the street's axis for moss strings), leans a little, and is scaled by a random size, the `piece_size` dial and a **widening that grows with distance**: never narrower than 6 plate dots (5 for moss), never more than 3 times bigger (`piece_inflate_limit`).
5. **Ceiling.** At most `max_pieces` (2,500) in one picture.

`amount` 0, `weeds_amount` 0 and `cushions_amount` 0 make every probability exactly 0: zero plants and the same picture.

## 4. How many (the share dials mean what they say)

`weed_cover`, `gutter_tuft_share`, `wall_foot_share`, `cushion_cover` and `toadflax_clumps` are **target counts for the window round the set's default camera** (distance 18 m, inside the cone). On `apply` (and when one of those dials changes) the layer lays the plants once with test gains, counts what stands in the window, and sets the gains so the counts come out at the targets: weeds = cover x ground area / mean plant footprint, split into a gutter-side part, a wall-foot part and the rest; moss likewise. If the total would pass `max_pieces` every gain is scaled down together (the zones never move). It takes under a second on the rented machine.

## 5. Colour and the wet look

The plants are lit only by the dusk lamps, and the wet road in the plate is about 0.19 bright, so a leaf has to be lifted to land at 0.30 to 0.35 (`material.albedo_gain` 8 in `species.json`; the look's `colour_gain` 1 means "as written"). Saturation is pulled back to 0.8 so the plate shows hue 78 to 111 degrees (median 96), saturation 0.47 and no bright green (saturation 0.6 and value 0.6 together: 0 dots). The wet look is a Value node in every piece material (`WET`, set by `kit.set_state`): richer, darker (the `wet_dark` dial, with a boost so the brightness falls to 0.63 to 0.90 of dry) and a little glossier (roughness 0.72 to 0.46, no coat). A damper spot (the dampness mask is stored on every plant) wets a little more.

## 6. Use

```python
from apply import kit as wk
from growth import apply_growth
k = wk.Kit.load('<set id>', scene_id='<scene id>'); bus.attach(k)      # the harness does this
apply_growth.register(k)                                                # or harness/layers.py finds it by itself
k.prepare(); k.apply(layers=['growth'])                                 # plants appear; a second call does nothing
k.set_dials('growth', weeds_amount=0.5, piece_size=1.2)                 # changes re-count if they need to
k.set_state(0.85, 0.5)                                                  # wet evening
rows = k.growth.table(camera_object)                                    # every plant of that picture
k.remove('growth')                                                      # nothing of it is left
```
On the rented machine the harness draws it as the look `solo:growth` or `kit_all`; `python3 -I growth/run_growth.py SET SCENE OUT --jobs full|times|zero|dials|spots|view` draws the growth layer's own job lists.

## 7. Using it on a new set (what the courtyard needed)

1. Say which roles are the ground the plants stand on: `apply.growth.targets` in the set file (the courtyard: earth, stepping and edge stones, gravel) and which piece sets (`moss_cushions`, `grass_edge`, `weeds`).
2. A `growth` block (today the sidecar `growth/growth_sets/<set id>.json`): the objects whose litter plants keep clear of (the street names the litter layer's host; the courtyard none), the gutter side (roles and reach; none for earth), the wall-foot reach, the axis for moss strings, the calibration camera, `align_normal` (0.8 on the courtyard's tilted stones).
3. Look extras (`growth/looks_growth/<look>.json`): the courtyard is in full light, so `colour_gain` 0.15 takes the street's lift back out.
4. A water level (`geometry.water.level_z`) keeps plants out of the pond; the pack's `above_water` does the rest.
Tested: the courtyard scene takes the layer without a crash, about 1,800 plants (almost all moss strings, 4 to 5 tufts), on earth and stones, none under water, `amount` 0 gives none.

## 8. What was tested (the numbers)

Drawn on the rented machine (1536 x 2730 plates, 48 samples; the 22 lighting pictures, five close views, plate masks), measured with the kit's own measure scripts.

* **P3 readable at painter size (0.45 / 0.40):** main plate 62.5 % GOOD, 10 % LOST, 0 crushed (62.5 % / 12.5 % at 0.40), 30 GOOD marks in the first 15 m (need 12); lockout plate 100 % GOOD (42 marks, need 6); **notice plate fails**: 51 % GOOD, 25 % LOST (need 60 and 15). Reason: that camera looks down at a lit pavement of brightness 0.39, so a plant at 0.32 has no contrast to it.
* **P4 amounts:** weed cover of the visible ground inside 18 m: main 0.68 %, notice 0.95 %, lockout 0.64 % (rule 0.5 to 2 %; over the full 18 m disc, behind the camera included, 0.27 to 0.39 %); moss cushion cover 0.9 to 1.2 %; gutter-side tufts 8.1 %, 9.5 % and 5.8 % of the gutter-side strip length (rule 3 to 8 %: two plates a little over); **wall-foot plants 0 %** (rule 2 to 5 %: see the finding below); toadflax 0 (no site). Plants on the setts: 0.76 % of the road area. Species and sizes inside the period ranges.
* **P6 zones:** 0 plants in footfall 0.6 or more, crown 0.7 or more, keep-clear 0.5 or more, on a doorstep strip or within 1 m of the fire, on all four plates (street main, notice, close road, lockout); 0 weeds within 5 cm of a litter piece (0 of 119 to 188); the habitat fields themselves are exactly 0 in the zones.
* **P7 time:** the plates cost +1 to +6 % at 300 to 1,450 plants (best of three; time per 1,000 plants 0.04 to 0.1 s); at the 2,500 ceiling about +5 to 8 %, inside the +10 % share (extrapolated from 1,450). The first picture after `apply`: +0.3 to 1.1 s. Building the scatter takes 0.5 to 1.6 s; the count about 0.3 s. (The times were drawn with an earlier brightness setting; brightness does not change the cost.)
* **P8 amount 0:** zero plants (self-test); the picture equals the plain picture to the renderer's own noise (79,550 dots one step different, 10 dots two steps; the plain picture against itself: 74,574 and 5).
* **P2 wet look:** the plants' wet over dry brightness 0.63 to 0.90 (nothing brighter when wet; moss band 0.55 to 0.85 holds in 9 of 10 pictures, lighting C wet is 0.90); the kit's own P2 lines hold on street and lockout.
* **P5 mush:** no surface class changes brightness by more than 1.4 % on any plate (the kit's M5 band test reports ratios of 1.00 as "outside 0.80 to 1.00" because it asks for a drop).
* **Self-tests** (`selftest_growth.json`, all pass on both scenes): pieces (40 to 210 faces, sizes), amount 0 and the master dial, isolation (no existing material or object changed), remove (nothing left, twice is harmless), zones, determinism, caps (a 600 ceiling is held), litter, the engine on a tilted box with a made-up mask (plants only where the mask says, standing along the normal, 0.97 or better), the courtyard.

## 9. What went wrong on the way (so the next person does not repeat it)

* A generated picture goes blank when its colour space is changed after the numbers are written: set the space first (the private strips came out empty and no plant stood anywhere).
* One big node tree takes seconds to build one node at a time (each step costs more as the tree grows: 19 s for 950 nodes). The fix is one small node group for one kind, used ten times: 1.6 s.
* Density factors in Poisson mode are read at the face corners, so a keep-clear zone would blur on big faces; the keep/drop is therefore done on the points themselves.
* The first plants were dark and thin (blades 1 dot wide, plate brightness 0.11 against a 0.18 road): 31 % GOOD. Wider blades and a lifted colour gave 62 %.
* "Within 5 cm of litter" measured by origins in x and y found weeds at the kerb foot beside litter lying on the kerb top; the clearance is now measured in x and y on the ground plan.
* Under water: plants on the flank of a stone below the pond level; fixed with a water-level gate.

## 10. Not done, not tested, unsure

* **Wall foot:** the foundation's `keepclear` is 1.0 along the whole outer half of every pavement (see REQUESTS.md); no plant may stand there, so wall-foot plants and the toadflax at damp mortar cannot be seen in the street. The wall-foot population is built and tested only on made-up scenes.
* The notice plate fails P3 (above); the gutter-side share is a little over on two plates; the moss band is missed in one lighting.
* Not tested: the painter (no paid call; **whether the painter keeps green plants green and the sizes is unknown, no plate has had green**); the plate at 0.40 beyond the measure; the sett-joint pass line P1 with the plants in (only the area share, 0.76 % of the road); the stage; the courtyard drawn with its own lighting rigs and plate camera (one 1200 x 800 picture only); the kit with all three builders' layers drawn together (it builds and removes cleanly, locally, and the plants stay at 303 with the master dial at 0 giving none; no picture); a fresh machine.
* Unsure: every amount (the studies say so too), the colour lift (8 times) is for the evening lamps only, and the cushions are drawn as strings of 2 to 4 (so about 430 strings stand for the plan's cover, not 4,000 single cushions).
