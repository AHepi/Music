# 38 Look stage: the street's look dropped onto the coal mine

What this file is: a map of the transfer test of 2 November 2026, which asked one question: does the look of the street bundle "Rain on the Old Curve" transfer to a place it has never seen, as code, with no numbers written for that place?

Answer: yes, for the half of the look that is light, sky, haze, colour and finish. Shapes are not touched (the mine's balloon smoke and flat hills stay as they were).

## What is here

| Folder or file | What it holds |
|---|---|
| `pictures/mine-A-as-is.png` | The coal mine drawn as it was (its own lights, sky picture and settings), 540 x 960, 32 samples, 59 s on this 2-processor machine |
| `pictures/mine-B-look.png` | The same scene and camera after one call to the look stage with its defaults, 135 s. Too dark (brightness 0.12) |
| `pictures/mine-C-look-fixed.png` | The one fix pass: exposure 1.0 instead of 0.5, window lights twice as strong, 139 s. Brightness 0.18 |
| `pictures/mine-A-vs-B.jpg`, `mine-A-B-C.jpg` | Side by side |
| `code/look_stage.py` | The look stage: `apply_look(scene)`. Everything it adds is named "LOOK • ..." and `remove_look(scene)` takes it out again |
| `code/render_mine_test.py` | Draws A and B from `mine-as-is.blend` |
| `code/render_mine_fix.py` | Draws C |
| `code/measure.py` | Brightness, warm-to-cool split and warm-light coverage of a picture (the same measures as the style bible) |
| `code/times.json` | The drawing times |

The scene file `mine-as-is.blend` (23 MB) is not here; `mine-scene/assemble_mine.py --quick --no-render --save-blend` rebuilds it in 18 s with `MINE_TEXTURES` pointing at `austerity-explainer/working-files/session-scratch/mine-work/textures_ready`. The whole test ran on Blender 5.1.2 installed as a Python module (`pip install bpy==5.1.2`), the version the street bundle was built with.

## What the look stage does (and what it refuses to do)

It adds, in one call, to any scene:

1. A real amber light at every warm glowing patch it finds by itself (a run of connected faces sharing one glowing material: a window pane, a lamp head). Lamps (by material name) get the street's gas mantle and pavement wash; windows get a point light just outside the glass, sized by the pane's area and glow. Every lamp is lit; windows nearest the camera first, up to a cap. The mine had 133 patches.
2. The street's sky rig, scaled from the place's size so the light per square metre stays the same: a broad blue light above, a far blue veil behind, a soft blue one in front of the camera, a warm off-frame reflection beside it.
3. The cloud-painted cobalt blue-hour sky as the world (the scene's own sky is remembered, not deleted).
4. A thin cool haze filling the place.
5. Cycles, AgX "Medium High Contrast", exposure as a dial.
6. The finish: fog glow, then an anisotropic Kuwahara filter mixed in at 28 percent.
7. Optional: slanted rain; the camera set like a standing person (32 mm, eye 1.65 m).

It mutes the scene's own lights (remembered, restored by `remove_look`). It never changes a shape or a material.

## The measures

| Picture | Brightness (0 black, 1 white) | Warm : cool | Warm light covers |
|---|---|---|---|
| Mine as it was (A) | 0.27 | 19 : 54 | 0.1 % |
| Mine + look, defaults (B) | 0.12 | 31 : 53 | 0.2 % |
| Mine + look, one fix pass (C) | 0.18 | 32 : 49 | 1.1 % |
| Street bundle's own render | 0.20 | 31 : 47 | 0.5 % |
| Reference painting, the pithead | 0.34 | 16 : 47 | 1.0 % |
| Reference painting, the street | 0.16 | 30 : 58 | 0.9 % |

C sits with the street render and the street painting on all three measures. By eye: blue-hour sky, amber light from the engine-house door and the village windows pooling on the yard, haze giving the village distance, the headframe a dark silhouette as in the reference pithead painting.

## Failures on the way

1. The first pass was too dark (B). Cause: the mine has fewer and smaller lights than the street, and exposure 0.5 was the street's number. The measures caught it; one dial fixed it.
2. The first rule for choosing which glowing patches get a light (the 40 biggest by area times glow) picked far village windows and left out the engine-house windows nearest the camera. Changed to: every lamp, then windows nearest the camera first.
3. `bpy.context.object` after adding the haze cube worked here under the module; it may not in every context. The street bundle relies on the same thing.

## What this does not prove

- Only one place and one camera. The Japanese courtyard, an interior and a daylight scene are untested (daylight is outside this look altogether: the look is a blue hour).
- A moving camera is untested (the Kuwahara filter and Cycles' noise clean-up could flicker between frames).
- Nothing was shown to a blind judge; the "in the family" verdict is mine plus three measures.

## Traps

- The look replaces the world. A scene whose sunset lives in a sky picture loses it (the mine did). If a place needs its sunset, the sky rig and world need a "low sun" variant that does not exist yet.
- Exposure is the street's number, not a law. Measure first, then set it; brightness 0.16 to 0.30 is the band the references sit in.
- The haze box is sized from the place's bounds with hills and sky domes (anything over 400 m across) left out. A place with a 300 m backdrop will get a haze box that large.
- Running `apply_look` twice is safe (it removes its earlier work first); saving a scene with the look applied and then applying again on the saved file also works, because every added thing carries the "LOOK • " name.
