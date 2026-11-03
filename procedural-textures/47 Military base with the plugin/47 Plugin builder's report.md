# Plugin builder's report (military base)

What this file is: the builder's final report, returned as text and saved by the coordinating session, shortened, unchanged in substance.

Built a First World War army camp at blue hour along Y, standing camera (eye 1.65 m, 32 mm): 430 plain shapes named by role word (muddy `parade ground earth`, puddles and ruts, duckboard paths, 5 + 3 timber barrack huts with windows, shutters, doors, stovepipes, water butts; a brick headquarters with sandbags, flagpole and pennant; a gate with barrier, fence, barbed wire and sentry box; a field gun, a truck, crates, barrels, ammunition boxes; a brazier with a fire, five gas lamps, a water tower, a radio mast, an end block with one lit window).

Dressing (last run `--litter 2 --grime 1.4 --wet 0.7 --growth 1.3`): 430 objects dressed, none unassigned; 2,007 lapped boards on 30 timber walls with 24 window sashes; 3 stone walls into 1,023 ashlar blocks; 268 roof course lines; 187 weed tufts, 372 litter pieces, 1,948 rubbish pieces, 415 timber rot faces.

Last dials: 540 x 960, 32 samples, exposure 0.7, window light 1.5, lamp light 1.0, sky light 0.8, amber reflection 1.0, fire light 1.5, haze 1.0. Round 1 107 s (brightness 0.18, warm 19, cool 53, warm light 0.4 percent); round 2 129.5 s (brightness 0.22, warm 56, cool 28, warm light 0.9 percent). No glowing-glass warning.

Fix pass after round 1: raised the barrier, centre duckboard path, sandbags and boxes in the foreground, huts and camera moved closer, dressing dials raised, dials changed. Faults left in round 2: the nearest hut a big pale wall filling the left third (perhaps the off-frame amber light); warm and cool shares out of band; wire coils and brazier as black cylinders; the ground like wet shiny concrete with a dead zone at the bottom; gate and sandbags out of frame. Not fixed because the skill allows one fix pass; fix list ready (amber reflection 0, huts from y = 14, foreground clutter near the camera line, wire as lines, the brazier a bowl with a bigger flame). No close-up looks, no full size.

Redraw at full size: `cd /home/claude/plugin-military/build && python3 ../painted-place/stage/render_small.py --scene dressed.blend --out final-1080.png --width 1080 --height 1920 --samples 64 --window-light 1.5 --fire-light 1.5 --exposure 0.7 --sky-light 0.8`

Its notes for the plugin: the 32 mm tall frame is about 3 m across at 9 m; the earth role reads as a glossy mirror over large flat ground, and foreground litter and weeds are sparse and oversized; any simple iron cylinder comes out as a flat black cylinder.
