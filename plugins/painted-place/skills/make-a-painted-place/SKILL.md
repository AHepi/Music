---
name: make-a-painted-place
description: Build any place (a street, a yard, a mine, a tea house, a harbour, an interior) in Blender and bring it into the series' painted blue-hour look - teal-blue shadow, amber light from lamps and windows, haze, old surfaces, a restrained brush finish - in one call, then have a blind judge say in plain words what to fix, and fix it once. Use whenever a place is to be built or drawn for the series, whatever the request says about looks, surfaces or lighting; the look stage and the dressing do that part without being told.
---

# Make a painted place

What this is: five things and a loop. Read `${CLAUDE_PLUGIN_ROOT}/look/The look.md` (one page) before building; everything else is in the tools' own help (`--help`).

## The loop

1. **Build the shapes, your way.** Plain boxes and cylinders are enough; the dressing and the light do the rest. Put the role in each object's name (`left terrace 03 wall`, `window lit`, `door wood`, `kerb stone`, `lamp post iron`, `lamp glass`, `puddle water`, `roof slate`, `chimney smoke`; the full list is `${CLAUDE_PLUGIN_ROOT}/materials/Roles.md`). Lay the place along Y, ground at Z = 0, in metres. Put the camera where a standing person would stand (eye 1.65 m, 32 mm, tall frame) looking down the place's long line so the lines meet in the upper middle; one thing of interest centred, something detailed along the bottom edge. Save it: `PLACE.blend`.
2. **Dress it:** `blender -b --python ${CLAUDE_PLUGIN_ROOT}/materials/apply_by_role.py -- --scene PLACE.blend --save-as DRESSED.blend --report dressing.json`. One call does all of this from your shapes and names, without being asked:
   - gives every object a proven material by its role;
   - lays real setts on a flat road and worn flags on a flat pavement;
   - builds every flat stone wall up into courses of chipped ashlar, stopping at your windows and doors so they sit in deep reveals, and gives each window jambs, a lintel, a sill and a sash, each wall bands, a cornice and corner stones; roof slabs get slate course lines;
   - lays the details where the place's own shape says they belong: puddles placed where a lamp or lit window will mirror in them, water in the gutters, damp at every wall's foot, soot and run-off stains, rust under iron and rusted pipes, weeds and moss at wall feet, along kerbs and in the joints between setts, the place's rubbish along gutters, wall feet and doorsteps (coal, cinders, straw and paper in a street; shells, coral and seaweed on a shore), whitened doorsteps.
   Read the report: every object should have a role; fix names for the ones in `unassigned` and run it again (running it again is safe). Dials for the details: `--wet`, `--grime`, `--growth`, `--litter` (0 none, 1 the street, 2 twice); `--no-setts`, `--no-facade`, `--no-details` switch a part off.
3. **Light it and draw it small:** `blender -b --python ${CLAUDE_PLUGIN_ROOT}/stage/render_small.py -- --scene DRESSED.blend --out round-1.png [--rain]`. About two minutes at 540 x 960 on a plain computer; seconds on a rented card. The look stage finds every glowing window and lamp and puts a real light at it, adds the sky rig and the haze, sets the colour and the finish. It writes `round-1 - dials.json` beside the picture.
4. **Measure, then judge blind.** `python3 ${CLAUDE_PLUGIN_ROOT}/look/measure.py round-1.png` says whether the picture sits inside the look's bands and names the dial if not. Then `python3 ${CLAUDE_PLUGIN_ROOT}/look/judge.py round-1.png --out judge-1` and start the `blind-judge` agent with only this sentence: "Judge the packet at judge-1." Never give the judge your report, your scene or your reasoning. Save its answer as `judge-1/verdict.md`.
5. **One fix pass.** DETAIL fixes ("too clean", "no puddles", "more weeds") change step 2's `--grime`, `--wet`, `--growth`, `--litter`. DIAL fixes change a number in step 3's command (`--exposure`, `--window-light`, `--lamp-light`, `--fire-light`, `--sky-light`, `--amber-reflection`, `--haze`, `--painterly`, `--no-haze`, `--person-camera`; the coal mine with few windows wanted window light 2.0, a narrow lane with ninety glowing panes wanted 0.3, lamp light 0.6, sky light 1.6 and no off-frame amber light); SHAPE fixes change the build script; SURFACE fixes change a role word. Make every fix in one sweep, then draw `round-2.png` once. If the judge said "no", judge round 2 the same way; if "nearly" or "yes", stop here: a third pass is where the last plugin's costs and procedure grew.
6. **Report** in plain words: the verdict, what you fixed, the measures of the last picture, the time each picture took, and what you did not do. Attach the pictures.

The full-size picture (1080 x 1920, 64 samples) is drawn once, at the end, with the same dials: `--width 1080 --height 1920 --samples 64`. Where lamps, windows or fires are lit, the picture is Cycles (the look stage sets it); on a rented card if one is set up, otherwise here.

## Worked example

`${CLAUDE_PLUGIN_ROOT}/examples/lane-blockout/` builds a grey-box lane of 674 named boxes and cylinders; the dressing gave all 673 meshes a material from their names and laid 12,279 setts on the flat road; the look stage lit it; its `What is here.md` shows the rounds and the measures. `${CLAUDE_PLUGIN_ROOT}/examples/coal-mine/` shows the look stage dropped onto a place built by someone else with its own materials: as it was, the defaults, the one fix pass (exposure 1.0, window light 2.0).

## What stays out

- No gate stops a picture. A picture that fails the measures is still drawn and still judged; the judge's words are the test.
- Do not paint surfaces in code, model trees from blobs, or stamp a painted hill band behind the place: a plain world and the haze do the distance. If the place needs a far hill, build its shape and give it the `earth` role.
- Do not model ashlar, sills, sashes, puddles, weeds, moss, grime or rubbish yourself: the dressing makes them from your plain walls, windows, kerbs and roads. Build the plain shapes, name them, and leave the old-and-used to step 2.
- Do not add your own lights unless the judge asks for a light the look stage cannot give; then say so in the report.
- The painter (an image model repainting the plate for the flatter painted look) is not part of this loop. If it is wanted, the explainer-film plugin's `paint-and-cut` skill does it from the full-size picture.

## Traps

- A lamp whose glass has no glowing material gets no light: name its glass `lamp glass`. A fire's flame is `flame` or `fire`: it gets its own low, wide light and its own dial.
- `stone` means a built wall and gets laid up in ashlar; a boulder, rock or reef is `rock`.
- Role words hide inside other names: `step`, `window` and `fire` take their role wherever they appear (`door step` is a pavement, `window frame` a dark window, `fire bucket` a flame). Read the dressing report, not your intention.
- A place laid along X instead of Y gets the stone picture smeared along its long walls; the procedural parts still work, but lay it along Y.
- The look stage replaces the sky. A sunset painted on a dome is gone; a `--keep-world` picture keeps it but loses the blue-hour sky light's colour.
- The first picture is usually too dark or too bright by one exposure step; that is what the measure is for, not a reason to change the lights.
- Measures inside every band do not mean the picture is right: balloon-shaped smoke and blob trees pass every band. Judge every round.
