# A change the owner asks for

What this file is: the brief for one more builder when the owner, seeing a finished place, asks for one particular change (decision 89: "The next thing to work on is the rocks..."). It gets the place as the last builder left it and one job: make the change the owner asked for as well as it can be made, wherever it applies, and keep everything else as it is.

## The text

> You are changing a place other builders made for a narrated explainer film, at the owner's word.
>
> The owner's words, in order: REQUEST
>
> The place is built, lit and dressed: its script, SCRIPT, rebuilds it (its pictures are PICTURES; the builders' material lists are MATERIALS). Your job is the change in the owner's last words: make it as well as it can be made, across the whole place wherever it applies, and keep everything else as it is (the layout, the camera, the light) unless the change cannot be made without moving it. FOLDER/store/ holds ready parts, tools and materials you may use (see its Store.md); some may make the change better than anything the earlier builders made by hand. Nothing in the store places itself. Read FOLDER/Before you build.md first, then write WORK/change.md before changing anything: what the owner asked for, where it shows in the place, and how you will make it.
>
> The film has a look: FOLDER/The look.md, the pictures in FOLDER/reference/, and FOLDER/boards/ for the real thing. FOLDER/Traps.md and the traps at the bottom of FOLDER/A change the owner asks for.md list what has gone wrong before. `python3 FOLDER/measure.py SOME.png` measures a picture against the look's bands; your picture stays inside every band.
>
> What you have: a work folder WORK (write everything there), Blender 5.1.2 as the `bpy` module (`python3`), 2 processors, nobody else drawing.
>
> Rules: read nothing outside FOLDER, WORK and the earlier builders' folder; no internet, no image generation. Your clock ends at DEADLINE by this computer's clock; use all of it: draw, measure, look at full size beside the earlier picture, fix, draw again, and do not stop before the clock unless you can say what you would change and why you will not. Draw your final at 540 x 960 as WORK/final.png (and any other view the earlier builders delivered, under the same name); leave render_final.py (python3 render_final.py WIDTH HEIGHT SAMPLES OUT.png) that draws the changed scene with all its finishing. End with a report in plain words: what you changed and how, every picture with its time and measures, what you checked and fixed, and what you did not do. Keep WORK/notes.md as you go (each picture with its time and measures, what you changed and fixed): this computer can stop without warning, and then that file is all that is left of your report.

## How it is run

Copy the last builder's `render_final.py`, its pictures and every builder's `materials.md` into a folder this builder may read; give it a fresh copy of the kit at the same path as the earlier builders' copy (the store may have grown since; the earlier script must still find it), any pictures the owner sent about this place in the kit's `request/` folder, an empty work folder of its own, and 80 minutes. REQUEST is every message of the owner's about this place, word for word, in order. Save its report yourself. Its picture is the one the owner judges, beside the last pass's.

## Traps

- A change asked for one kind of thing applies wherever that thing shows in the place (every rock, not only the few nearest the eye), and to nothing else.
- A refreshed kit can change what the earlier script draws: draw the earlier script once with the fresh kit, small, and compare it with its picture before changing anything.
- The owner's pictures go into the builder's copy of the kit only, never into the plugin or GitHub.
