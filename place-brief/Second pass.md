# Second pass: set dressing

What this file is: the brief for a second builder that gets a finished place (another builder's scene and script, its picture, and the kit) and one job: make it old, used and full, without changing the layout, the camera or the light. The two-pass split follows how a film crew works: one person builds and lights the set, another dresses it.

## The text

> You are dressing a place another builder made for a narrated explainer film.
>
> The owner's request, in their own words: "REQUEST"
>
> The place is built and lit: SCENE is the scene (its script, SCRIPT, rebuilds it; its picture is PICTURE). Keep the layout, the camera and the lights as they are. Your job is everything the first builder had no time for: the surfaces (worn, stained, patched, from `FOLDER/surfaces/` or your own), the wear where the world would put it, and the things the people who use this place left behind, each placed where its owner would have put it down. Read FOLDER/Before you build.md first and write `materials.md` as your first deliverable, then dress.
>
> The film has a look: FOLDER/The look.md, the pictures in FOLDER/reference/, and FOLDER/boards/ for the real thing. FOLDER/Traps.md lists what has gone wrong before. `python3 FOLDER/measure.py PICTURE` measures a picture against the look's bands.
>
> What you have: a work folder WORK (write everything there), Blender 5.1.2 as the `bpy` module (`python3`), 2 processors, nobody else drawing.
>
> Rules: read nothing outside FOLDER, WORK and the first builder's folder; no internet, no image generation. Your clock ends at DEADLINE by this computer's clock; use all of it: draw, measure, look at full size, fix, draw again, and do not stop before the clock unless you can say what you would change and why you will not. Draw your final at 540 x 960 as WORK/final.png; leave render_final.py (python3 render_final.py WIDTH HEIGHT SAMPLES OUT.png) that draws the dressed scene with all its finishing. End with a report in plain words: what you changed, every picture with its time and measures, what you checked and fixed, and what you did not do.

## Traps

- "Keep the light" means the lamps, the sun and the haze; a dressing that adds a lantern adds its light too, and that is allowed.
- Dressing that hides the hero or crosses the frame's lines (a wire across the gun, a crate in front of the door) is wrong however good it looks.
