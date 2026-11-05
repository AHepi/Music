You are a helper adding to a Blender plugin's store, on this machine. The owner is not a programmer: write your report in plain everyday words.

The plugin is `/home/claude/music/plugins/painted-place` (paths below start there). Its store, `brief/store/`, holds ready parts (things to place), tools (code that makes a thing from a line, a point or an object the caller gives) and materials, which fresh builders use when they build places for the owner's narrated film. Read `brief/store/Store.md` (conventions and traps), `brief/Traps.md` and `brief/Before you build.md` first. The owner's standing word (decision 84): "Please remind the builders to use PBR wherever possible. It save in space and compute."

What happened: a helper has just added a new part, `azalea`: a garden azalea clipped into a low rounded mound, built from a dense skin of single small leaves and many real five-petal flowers (`brief/store/parts/src/azalea.py`; its cards `brief/store/cards/parts/azalea - three.png`, `- close.png`, `- side.png`, `- back.png`; its maker's notes `/home/claude/store-work/closer58/plants/notes.md`). The owner saw the cards and wrote: "The bush looks incredible. But it try projecting it onto a PBR and see how it looks", and then: "Oh and use Eevee if its faster."

The reading (decision 87): bake (project) the built bush onto a simple low shape with a UV map, as a set of pictures (colour, relief as a normal picture, shine, and height), so the bush can be drawn as a few hundred faces and a few pictures instead of its thousands of leaves and flowers; draw the baked bush beside the built one, near and at garden distance; and measure what it saves in file size and drawing time.

About Eevee: the session checked it on this machine, which has no graphics card, so Eevee draws through software. Blender's starting scene at 270 x 480 took Eevee 33 to 41 seconds and Cycles (32 samples) 3.7 seconds. Time both once on your own comparison scene (the built bush and the baked bush, same view), say which is faster, and draw the rest with the faster one. Baking itself is done by Cycles.

Your job:
1. The test first (the owner is waiting for its pictures):
   - Build the azalea as builders do, `store.add_part('azalea', ...)` with its defaults (pink, in flower). Do not edit the part: it is finished.
   - Make a simple shape that hugs its outline, with a UV map, and bake the bush onto it with Cycles ("selected to active", with a cage or extrusion so the projection reaches every leaf and flower): its colour without light, a normal picture, its shine (roughness), and a height picture.
   - Give the shape a material made from the baked pictures.
   - The smooth outline of a plain shape is the likeliest give-away: try the height picture as real displacement, or another way you find, and show which reads best.
   - Draw the built bush and the baked bush side by side under the same light: close (the card's three-quarter view, 420 x 420 or wider), and as seen in a garden from 6 to 10 m away (a 540 x 960 picture, or its middle) under a dusk light of your own: a dim blue sky and a warm lantern a metre or two from the bush (the azalea's maker found its flowers go dim at dusk unless a lantern is near).
   - Measure for each: faces, the size of the saved file and of its pictures, the time to draw, and memory if you can.
   - Save each comparison picture as PNG in your scratch folder with a plain name, and write its path, time and measures into your notes as soon as it is drawn: the session sends them to the owner straight away.
2. Then put what you learned into the plugin, whichever way the test comes out (the owner's standing rule: every new technique or lesson goes into the plugin):
   - a tool `brief/store/tools/bake_to_pbr.py` that bakes a part, or any objects the caller passes, onto a simple shape the tool makes (or one the caller passes), and returns the shape with its baked material, following the store's tool conventions (a `TOOL` dict with name, what, call, options with their defaults, materials, source and trap; `--help`; importable functions that act only on what the caller passes; no tool reads the camera, surveys the scene or walks the scene's objects: `tests/test_store_rules.py` checks this);
   - its card, `brief/store/cards/tools/bake_to_pbr.png` (one 420 x 420 picture): the built and the baked bush side by side. Look at it at full size before you call it done;
   - a test, `tests/test_store_bake.py`, in the style of the others (plain PASS lines, exit code 1 on any failure);
   - if the baked azalea reads well, keep its baked pictures in your scratch folder and say in your report where they are and how big: the session decides whether the part gets a baked option;
   - in your report, a few lines for the session to add to Store.md: where the baked bush reads well and where it does not, from how far, and what it saves.

What you own: the new tool, its card, the new test, and your scratch folder `/home/claude/store-work/closer58/bake/` (the session's two small Eevee check scripts and their pictures are already there; leave them). You edit nothing else: not `Store.md`, `tests/run_tests.sh`, `tests/_common.py`, `card.py`, `catalogue.py`, `store.py`, other parts or tools, materials, `brief/The look.md`, `brief/reference/`, `brief/Traps.md` or `brief/Before you build.md`. Do not run `catalogue.py`: the session does. Read the existing tools: they show the conventions. Earlier helpers drew their cards with their own scripts (see `/home/claude/store-work/closer58/sky/scripts/` and `/home/claude/store-work/closer58/plants/scripts/`). Run your own test, `tests/test_store_tools.py` and `tests/test_store_rules.py` (its catalogue check fails until the session runs catalogue.py: expected). If your tools include the Skill tool, the skill `scenario-blender-uv-baking` covers baking a detailed object onto a simple one. The owner's pictures (`/home/claude/build-57-garden/kit/request/` and `/home/claude/build-57-garden/closer/pics/cmp_*.png`) are the owner's own: never copy them anywhere.

Working on this machine:
- Blender 5.1.2 is the Python module `bpy`: run scripts with `python3`; `import bpy` before `import bmesh`. Two processors; the session runs tests now and then. Never draw two things at once yourself.
- Keep `notes.md` in your scratch folder as you go (each picture with its time, what you changed and fixed): this machine can restart without warning, and then that file is all that is left.
- Your clock: finish by 08:15 by this computer's clock (`date`).

Your report, in plain words, as your last message: what the test showed (each picture's path with its measures), what you made (with the call to use it), what does not read well, the mistakes you made and how you fixed them, and the files you created or changed.

---

Later, from the session: "The server behind this session stopped less than a minute after you started, so nothing of yours is on disk yet (your scratch folder holds only the session's two Eevee check scripts and their pictures). Please carry out your whole job from the beginning, exactly as your first message describes. Your clock is unchanged: finish by 08:15 by this computer's clock (`date`)." And, after the first pictures: "From the session, having looked at pics/close_built_vs_baked_lit30.png at full size: the baked bush (right) shows a dark ring or swirl near the top of the dome, a little left of centre, that the built bush does not have (perhaps where the dome's one UV island has its middle, at the top pole). Please check it and fix it if it is the bake. The three pairs (close relief, flat vs relief, garden full) have been sent to the owner as they are."

## Traps

- The first paragraph to "Your report" is the helper's whole brief; the two later messages are given after it, word for word.
