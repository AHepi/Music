# Brief

What this file is: the words a builder gets, with the request, the folder and the clock filled in. Everything the builder may read is this folder. It is given a copy, never the original: the originals in the plugin's `brief/` folder stay frozen unless the owner says otherwise.

## The text

> You are building one place for a narrated explainer film, alone.
>
> The owner's request, in their own words: "REQUEST"
>
> The film has a look. The pictures in FOLDER/reference/ show it, FOLDER/The look.md describes it, and FOLDER/Traps.md lists what has gone wrong for builders before you. Your picture should belong with the reference pictures. `python3 FOLDER/measure.py PICTURE` measures a picture against the look's bands.
>
> Before you build, read FOLDER/Before you build.md and the photographs in FOLDER/boards/REQUEST/: real pictures of the kind of place asked for. Your first deliverable is WORK/materials.md: who uses this place and what they left, and every surface and thing in the picture with what it is made of, how it has aged and where its wear sits. FOLDER/surfaces/ is a shelf of photographed surfaces you may lay on (see its Surfaces.md), and FOLDER/store/ holds ready parts, tools and materials you may use (see its Store.md). Nothing in the store places itself: where things go is yours to decide.
>
> What you have:
> - A work folder: WORK. Write everything there.
> - Blender 5.1.2 as the Python module `bpy`: run scripts with `python3`. The computer has 2 processors and nobody else is drawing on it.
>
> Rules:
> - Read nothing outside FOLDER and WORK. No internet, no image generation, no rented machines, no other folders on this computer.
> - Your clock: your last picture must be finished by DEADLINE by this computer's clock (check with `date`). The clock ends the build, not the measures: inside every band is a floor, not the finish. Before the clock, keep going until all of these hold: every surface in your material list is laid; every thing in the frame can be named at full size; puddles have ragged edges, a wet rim and a ripple; buildings have eaves, an overhang and boards or stones in relief; nothing reads as a plain box. When they all hold and time is left, look at the picture at full size part by part and fix the weakest part, then the next.
> - Your final picture is a tall frame for a vertical film. Draw it at 540 x 960, saved as WORK/final.png. It may be redrawn at 1080 x 1920 with 64 samples later, so also leave a script, render_final.py, that draws your final scene with all its finishing, run as: python3 render_final.py WIDTH HEIGHT SAMPLES OUT.png
> - When you finish (or at DEADLINE), end with a report in plain words: what you built, how you lit and framed it, every picture you drew with how long it took, its measures, what you checked and fixed, and what you did not do. Your report is your last message.

## How a place is built with this

1. Copy the plugin's `brief/` folder to a fresh folder the builder may read; make an empty work folder beside it. If `boards/` has no
   board for the request, make one first (real photographs of the kind of place, public domain, with a `Board.md` saying what to look at
   in each). The store (`store/`) travels inside the copy, so the builder can use it; nothing in it places itself.
2. Fill in REQUEST (the owner's words, exactly), FOLDER, WORK and DEADLINE (100 minutes from the start: the material list and the store
   take time).
3. Start one fresh builder with the text and nothing else. Do not give it the project's notes, the plugin, or your own reasoning.
4. When it ends, save its report beside its picture; the owner judges the picture against the reference pictures.
5. For more detail, a second builder dresses the place (`Second pass.md`).
6. A picture the owner approves can join `reference/` (and `The look.md`'s table); if it sits outside a band, widen the band in `measure.py` and on the page. A fault the builder reports that the next builder would also hit goes into `Traps.md` as one line.

## Traps

- Every helper also sees the repository's rules file and the owner's saved preferences; that cannot be switched off from here. Keep both free of technique.
- A builder cannot save files whose name begins with REPORT; its report comes back as text. Save it yourself.
- Two builders given the same brief make different places. That is the method, not a fault; more reference pictures narrow it.
