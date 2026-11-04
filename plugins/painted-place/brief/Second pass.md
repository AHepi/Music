# Second pass: set dressing

What this file is: the brief for a second builder that gets a finished place (another builder's scene and script, its picture, and the kit) and one job: make it old, used and full, without changing the layout, the camera or the light. The two-pass split follows how a film crew works: one person builds and lights the set, another dresses it.

## The text

> You are dressing a place another builder made for a narrated explainer film.
>
> The owner's request, in their own words: "REQUEST"
>
> The place is built and lit: its script, SCRIPT, rebuilds it (its picture is PICTURE; the first builder's material list is MATERIALS). Keep the layout, the camera and the lights as they are. Your job is everything the first builder had no time for, and above all the near ground, the bottom third of the frame: the surfaces (worn, stained, patched, from `FOLDER/surfaces/` or your own), the wear where the world would put it, and the things the people who use this place left behind, each placed where its owner would have put it down and each big enough to be named at full size; nothing in the open road or on the path (see the traps at the bottom of FOLDER/Second pass.md). FOLDER/store/ holds ready parts, tools and materials you may use (see its Store.md); nothing in it places itself. Read FOLDER/Before you build.md first and write WORK/materials.md as your first deliverable (what you will add, line by line), then dress.
>
> The film has a look: FOLDER/The look.md, the pictures in FOLDER/reference/, and FOLDER/boards/ for the real thing. FOLDER/Traps.md lists what has gone wrong before. `python3 FOLDER/measure.py SOME.png` measures a picture against the look's bands.
>
> What you have: a work folder WORK (write everything there), Blender 5.1.2 as the `bpy` module (`python3`), 2 processors, nobody else drawing.
>
> Rules: read nothing outside FOLDER, WORK and the first builder's folder; no internet, no image generation. Your clock ends at DEADLINE by this computer's clock; use all of it: draw, measure, look at full size, fix, draw again, and do not stop before the clock unless you can say what you would change and why you will not. Draw your final at 540 x 960 as WORK/final.png; leave render_final.py (python3 render_final.py WIDTH HEIGHT SAMPLES OUT.png) that draws the dressed scene with all its finishing. End with a report in plain words: what you changed, every picture with its time and measures, what you checked and fixed, and what you did not do.

## How it is run

Copy the first builder's `render_final.py`, `final.png` and `materials.md` into a folder the second builder may read; give it the same copy of the kit, an empty work folder of its own, and 80 minutes. Save its report yourself.

## Traps

- "Keep the light" means the lamps, the sun and the haze; a dressing that adds a lantern adds its light too, and that is allowed.
- Dressing that hides the hero or crosses the frame's lines (a wire across the gun, a crate in front of the door) is wrong however good it looks.
- **Every thing goes where its owner would put it down: against a wall, by a door, on a step, beside a path. Never in the open road or on
  the path itself.** The chapel's second pass (log 51) put a wheelbarrow, a scuttle and an umbrella in the middle of the lane, and they read
  as rubbish dumped in the road; the first pass without them was the better picture.
- The first builder's puddles and their reflections, and the glossy path, are the picture's light: nothing stands between a puddle and
  the lamp it mirrors, and no smear goes over glossy ground (it kills the shine).
