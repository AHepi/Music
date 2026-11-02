# Lane blockout: a place from nothing, through the plugin alone

What this file is: the record of the plugin's second test (2 November 2026). A grey-box lane of 674 named boxes and cylinders was built by `build_lane.py` with no materials and no lights, then dressed by role and lit by the look stage. It is also the test that found two faults in the plugin and fixed them.

| File | What it is |
|---|---|
| `build_lane.py` | The blockout: two unequal terraces along Y, windows and doors with surrounds, four gas lamps, puddles, a hand cart, two smoke boxes, a standing-person camera |
| `dressing-report.json` | What `apply_by_role.py` did: 673 objects dressed from their names, none unassigned; 12,279 setts and 690 flags laid |
| `round-1 - defaults, flat road.jpg` | The first picture, before setts existed in the plugin: the road a polished floor, every facade blazing |
| `round-2 - laid setts, first dials.jpg` | After the road became laid setts; exposure 0.3, window light 0.5 |
| `round-5 - final dials.jpg` | Window light 0.3, lamp light 0.6, sky light 1.6, no off-frame amber light |
| `round-1 - dials.json`, `round-5 - dials.json` | The dials of those two pictures, as `render_small.py` writes them |
| `rounds 1, 2 and 5 side by side.jpg` | The three together |

## Measures (bands in `look/The look.md`)

| Picture | Brightness | Warm : cool | Warm light covers | Time |
|---|---|---|---|---|
| Round 1 | 0.30 | 69 : 21 | 7.0 % | 159 s |
| Round 2 | 0.23 | 73 : 25 | 4.6 % | 108 s |
| Round 5 | 0.19 | 51 : 33 | 2.7 % | 109 s |
| Band | 0.14 to 0.35 | 15 to 35 : 30 to 60 | 0.4 to 3.0 % | |

Round 5 sits inside every band but the warm share. By eye it is in the family: wet setts mirroring a cobalt sky with amber pools under the lamps, haze down the lane, a dark end wall. What a judge would still list: the warm share (sandstone walls fill most of the frame from this camera; a wider lane or a lower camera shows more sky and road), every window pane the same size on a grid, the hand cart a toy, no roofs or smoke in frame (they are above it). All of those are the blockout's, not the plugin's.

## What the test found and fixed in the plugin

1. **A flat road with the cobble material reads as a polished floor** (round 1). The bundle's road was real stones; the material alone is only a sheen. Fix: `materials/lay_setts.py`, called by `apply_by_role.py` for every flat `road` and `pavement`: the bundle's eighteen unique chipped setts and eight worn flags, scattered live over the object's footprint; the flat object stays as the dark bed. 12,279 setts here, laid in a second.
2. **Every glowing window got the same light** (round 1 to 3): a floor of 40 W made a dim room shine like a lit one, and a lane with 93 glowing panes blazed. Fix: the floor is 8 W, so a dim pane gives a dim light; and three new dials in the look stage (`--lamp-light`, `--sky-light`, `--amber-reflection`) because a narrow lane with four lamps and the warm off-frame light beside the camera went amber all over.

## Round 6: the details (plugin 0.2.0, 2 November, evening)

The owner, after the blind test: "Ok. But notice the complete lack of details. I should have told you before that the pavement in the city scene was great. But the rest of geometry and the textures were terrible. The repos example had water, grime, weeds, moss, weathering. All missing." Same boxes, same camera, same dials as round 5; the dressing now also builds the walls up and lays the details (`round-6 - with facades and details.jpg`, `close look - left wall foot with facades and details.jpg`, `before and after the details.jpg`; counts in `dressing-report.json`):

- 39 walls, 60 faces laid up in about 7,000 chipped ashlar blocks; 251 windows dressed with jambs, lintels, sills, drip lines and sashes; bands, cornices and quoins; 380 slate course lines; 19 downpipes moved out with the thicker face.
- 11 puddles (placed where lamps and lit windows mirror in them), 28 runs of gutter water, about 240 damp wall feet, about 130 stains, 19 rust streaks and rusted pipes, about 530 weed tufts at wall feet and kerbs, about 80 more in sett joints, about 200 moss patches, about 900 leaves and fragments, about 5,500 pieces of coal, cinders, ash, straw and paper, 19 whitened doorsteps.
- A bug found on the way: the stones' parked pattern pieces (100 to 240 m below the street) were counted in the look stage's measure of the place, so its haze box sat underground in rounds 2 to 5. Fixed; the haze now shows.

## Not done

- No blind judge was run on these pictures (the measures and my eyes only).
- The full-size picture was not drawn.
- The hand cart, the roofs and the smoke were not looked at: they are out of frame or toys by design.

## Traps

- Round 1 looks worse than a plain render would: the look stage amplifies whatever the shapes give it. Flat road, blazing windows. That is the point of judging every round.
- The warm share of a narrow lane seen from a standing camera will sit above the band even when the light is right; read the picture before touching a dial.
