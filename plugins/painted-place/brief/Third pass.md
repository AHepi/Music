# Third pass: the building fronts

What this file is: the brief for a third builder, used when the owner asks for the most detail (decision 79). It gets the place after the second pass and one job: the buildings' faces and the middle distance, without changing the layout, the camera, the light or the near ground the second builder dressed. In a street or a yard the fronts fill most of the frame; the first builder lays them out, the second dresses the ground, and this one finishes the fronts.

## The text

> You are giving the finishing detail to a place two other builders made for a narrated explainer film.
>
> The owner's request, in their own words: "REQUEST"
>
> The place is built, lit and dressed: its script, SCRIPT, rebuilds it (its picture is PICTURE; the builders' material lists are MATERIALS). Keep the layout, the camera, the lights and the near ground as they are. Your job is the buildings' faces and the middle distance, everything above the bottom third of the frame: every front made of what it is built of and in relief, with its joints, sills, lintels, doors, steps, gutters, downpipes and signs without words, and the wear of weather and use where the world would put it (soot above windows and under sills, damp rising at the foot, rust running under iron, paint peeling, stains under gutters and downpipes); and the things people leave on and in front of their buildings (a bucket on a step, a crate by a shop door, a curtain half drawn, a broken pane), each where its owner would have put it and each big enough to be named at full size. FOLDER/store/ holds ready parts, tools and materials you may use (see its Store.md); nothing in it places itself. Read FOLDER/Before you build.md first and write WORK/materials.md as your first deliverable (what you will add, line by line), then work.
>
> The film has a look: FOLDER/The look.md, the pictures in FOLDER/reference/, and FOLDER/boards/ for the real thing. FOLDER/Traps.md and the traps at the bottom of FOLDER/Third pass.md list what has gone wrong before. `python3 FOLDER/measure.py SOME.png` measures a picture against the look's bands.
>
> What you have: a work folder WORK (write everything there), Blender 5.1.2 as the `bpy` module (`python3`), 2 processors, nobody else drawing.
>
> Rules: read nothing outside FOLDER, WORK and the earlier builders' folder; no internet, no image generation. Your clock ends at DEADLINE by this computer's clock; use all of it: draw, measure, look at full size, fix, draw again, and do not stop before the clock unless you can say what you would change and why you will not. Draw your final at 540 x 960 as WORK/final.png; leave render_final.py (python3 render_final.py WIDTH HEIGHT SAMPLES OUT.png) that draws the finished scene with all its finishing. End with a report in plain words: what you changed, every picture with its time and measures, what you checked and fixed, and what you did not do. Keep WORK/notes.md as you go (each picture with its time and measures, what you changed and fixed): this computer can stop without warning, and then that file is all that is left of your report.

## How it is run

Copy the second builder's `render_final.py` and `final.png`, and both builders' `materials.md` (as `materials - first pass.md` and `materials - second pass.md`), into a folder the third builder may read; give it the same copy of the kit, an empty work folder of its own, and 80 minutes. Save its report yourself. Its picture is the one the owner judges, beside the second pass's.

## Traps

- "Keep the light" means the lamps, the sky and the haze; a window lit or a lamp added on a front adds its light too, and that is allowed, but the picture's brightest place stays where it was.
- Stains, damp runs and rust on a front 15 to 20 m away do not show at 540 x 960 unless they are big and strong (the barn's second builder, log 54): judge each at full size, or put the finest wear on the fronts nearest the eye.
- Nothing hides the hero or stands in a lit doorway, and nothing new goes on the near ground the second builder dressed.
- Words break the look: shop boards and signs stay blank, or too far off to read.
