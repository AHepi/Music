# Round 2 report: the one fix pass (bach on the beach, Samoa)

(Written by the plugin builder, a Sonnet helper at high effort, and returned as text; saved to disk by the coordinating session unchanged except for this note.)

Work folder: /home/claude/blind-test/plugin-build
Picture: round-2.png (540 x 960). Packet for the next blind judge: /home/claude/blind-test/plugin-build/judge-2. I did not judge it and did not draw a third round.

Judge's round-1 verdict was **no**, with seven fixes. The judge's file is judge-1/verdict.md.

## Each fix: what I changed

1. **DIAL, fire the one strong light, rest of the sand into blue-black shadow.** Dials changed (list below): off-frame amber light 0, window light 0.5, lamp light 0.7, sky light 1.6. Shape help: removed the verandah lamp (kept one round door lamp), so fewer amber lights. Partly done only: the dials treat every lamp and flame alike (one strength for the door lamp, the fire and the distant fale lantern), so I could not make the fire stronger than the others. The sand is still warm and bright round the fire and the left of the porch (see measures).
2. **SURFACE, dull grainy rippled sand.** Sand role changed from `ground` (damp grit with a wet coat) to `plaster` (matte, mineral flakes). Sand is now a 0.11 m grid mesh with wind ripples, a line of footprints from the steps toward the sea and a drag groove across the foreground (`beach rippled sand plaster`), over a flat `beach far sand plaster` base. The big mirror glare is gone in my sketch and in round 2 by my eye, but I did not measure it.
3. **SHAPE, line from the bottom edge to the steps and used things at the bottom.** Added a plank walk from the foot of the steps down toward the camera (14 planks, two gone, some crooked), a coiled rope, a rust bucket, a torn net (thin cords), 16 shells, a moved driftwood log, and a split log by the fire. Not done: a lantern (it would have been another full-strength amber light under the lamp dial).
4. **SURFACE, age everything.** Lower weatherboards of every wall (below 1.35 m) are separate objects named `wall foot board`, which the plugin dresses as grime; rust streaks run down the front and left walls from the eaves (`wall rust streak`, rust role); each roof side is now three sheets, the middle one a replaced darker sheet (iron role) between two rust ones; the rain tank is rust role, ribbed, with a lid, stand and pipes; three rust patches on the canoe hull. Not done: water stains, flaking paint, drifted sand in corners, a worn chair. The plugin has no such roles and I kept to role words and shapes.
5. **DIAL, haze so far things turn paler and bluer, glow round the porch and fire.** Only partly. The plugin has `--no-haze` but no haze strength dial, so I could not add haze. I raised sky light to 1.6, which lifted the palms from near-black to dark teal in round 2. No glow in the air round the porch or fire was added; I did not build my own haze volume (the skill says the haze does the distance).
6. **SHAPE, a real fire.** Rebuilt: 11 rough uneven stones (two sizes, jittered), charred broken logs (grime role), a split log, nine ember bits (rust role), five ragged flame cones leaning different ways (one flame object, so one light), and two smoke boxes above it (smoke role, a volume). Result by my eye: the flame is still a bright white-yellow spiky shape and the stones are still faceted; the smoke is not visible in the picture.
7. **SHAPE, the unnamed dark shape between the porch and the canoe.** I decided it was the water tank (dark soot-iron cylinder behind the porch) and rebuilt it as a rusty ribbed tank with lid, stand legs and pipes. By my eye in round 2 there is still a large smooth dark shape in that place (right of the porch, behind the canoe), so I cannot say the fix worked or that the tank was what the judge saw. I did not take it out.

Extras the judge named outside the seven: the power pole cut off at the right edge moved to (2.9, 16.5) and is no longer cut off; the door lamp is now a round fitting, not a box; palm fronds were rebuilt as a thin spine with 60 narrow hanging leaflets each (not a saw-toothed strip).

## Dials used (command for round 2)
`render_small.py -- --scene bach2-dressed.blend --out round-2.png --window-light 0.5 --lamp-light 0.7 --sky-light 1.6 --amber-reflection 0`
Everything else default: exposure 0.5, samples 32, painterly 0.28, haze on, no rain, no --person-camera, 540 x 960. (The dials file is `round-2 - dials.json`.) Round 1 was all defaults. Look stage found 11 glowing patches and added 18 lights (round 1: 8 and 12).

## Dressing (dressing-2.json)
96 objects dressed, `unassigned` empty. Roles: wood 36, weed 14, rust 9, iron 7, window dark 5, wall 5, grime 4, plaster 2, recess 2, window lit 2, window dim 2, lamp glass 2, smoke 2, water 1, moss 1, flame 1, leaf 1. I checked every new name's role with the plugin's own `role_from_name` before drawing.

## Measures: round 2 beside round 1
| Measure | Round 1 | Round 2 | Band |
|---|---|---|---|
| Brightness | 0.31 | 0.28 | 0.14 to 0.35 |
| Warm share | 61 % | 47 % | 15 to 35 % |
| Cool share | 33 % | 42 % | 30 to 60 % |
| Warm light coverage | 15.0 % | 12.5 % | 0.4 to 3.0 % |

Warm share and warm light coverage are still high; measure.py again says window light down and exposure down.

## Time
Round 2: 301.0 s (5 min 02 s on my clock) at 540 x 960, 32 samples, on the shared machine. Round 1 took 219.7 s. Dressing and build about 1 s each. Also one throwaway check at 270 x 480, 8 samples (`sketch-2.png`, 45 s) with the same dials, drawn before round 2 only to see that the new build was not broken; I changed nothing after it. It is not a round.

## What I tested
Ran: the rebuilt build script (build_bach.py, round-1 version kept as build_bach_round1.py), the dressing, role-word checks on the new names, one small sketch, round 2, measure.py, judge.py. All ran without error. I looked at the sketch and round 2 once to check for breakage and to write the doubts below; that is not a judgment.

## What I did not do
No judge on round 2, no third round, no full-size picture, no plugin test suite, no `--rain`, `--keep-world`, `--person-camera`. I did not try lower exposure or lower window light further (that would be a second dial pass).

## What I am unsure of (my own eye on round 2)
- The ground within reach of the fire and porch is still pale warm, so the lower half still carries the amber; the warm numbers are still well out of band.
- The big foreground items I added read oddly: the plank walk planks are very large at the bottom edge, the rope coil is a smooth octagonal ring, and the torn net looks like a starburst of lines. They may read as toys or clutter, not used things.
- The fire flame still looks like a white crystal; smoke is invisible.
- The dark smooth shape behind the porch seems to remain.
- Roof now shows a darker middle sheet, but roofs mostly read as an edge from this camera height.
- Palms are still dark silhouettes against the sky, with no extra haze.
- The haze strength could not be changed with the plugin's dials; whether that is a gap in the plugin or in how I used it I cannot tell.

## Traps (operational)
- The dials can only tune all lamps together; a fire, a door lamp and a far lantern all get the same strength.
- A flame object that is a single mesh gives one light however many tongues it has; one object per tongue would give several.
- Role names win by word order (for example `foot` after `wall` gives grime, `rust` beats `wall`); check with the dressing report.
