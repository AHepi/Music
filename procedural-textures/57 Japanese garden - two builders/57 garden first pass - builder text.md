You are building one place for a narrated explainer film, alone.

The owner's request, in their own words: "Now try to do some of this. The animals are unnecessary. I'm not sure how you'll get this done though."

The owner sent these words with a picture: /home/claude/build-57-garden/kit/request/the owner's picture.png

The film has a look. The pictures in /home/claude/build-57-garden/kit/reference/ show it, /home/claude/build-57-garden/kit/The look.md describes it, and /home/claude/build-57-garden/kit/Traps.md lists what has gone wrong for builders before you. Your picture should belong with the reference pictures. `python3 /home/claude/build-57-garden/kit/measure.py PICTURE` measures a picture against the look's bands.

Before you build, read /home/claude/build-57-garden/kit/Before you build.md and the photographs in /home/claude/build-57-garden/kit/boards/japanese garden/: real pictures of the kind of place asked for. Your first deliverable is /home/claude/build-57-garden/work/materials.md: who uses this place and what they left, and every surface and thing in the picture with what it is made of, how it has aged and where its wear sits. /home/claude/build-57-garden/kit/surfaces/ is a shelf of photographed surfaces you may lay on (see its Surfaces.md), and /home/claude/build-57-garden/kit/store/ holds ready parts, tools and materials you may use (see its Store.md). Nothing in the store places itself: where things go is yours to decide.

What you have:
- A work folder: /home/claude/build-57-garden/work. Write everything there.
- Blender 5.1.2 as the Python module `bpy`: run scripts with `python3`. The computer has 2 processors and nobody else is drawing on it.

Rules:
- Read nothing outside /home/claude/build-57-garden/kit and /home/claude/build-57-garden/work. No internet, no image generation, no rented machines, no other folders on this computer.
- Your clock: your last picture must be finished by 21:47 on Thursday 05 November 2026 by this computer's clock (check with `date`). The clock ends the build, not the measures: inside every band is a floor, not the finish. Before the clock, keep going until all of these hold: every surface in your material list is laid; every thing in the frame can be named at full size; puddles have ragged edges, a wet rim and a ripple; buildings have eaves, an overhang and boards or stones in relief; nothing reads as a plain box. When they all hold and time is left, look at the picture at full size part by part and fix the weakest part, then the next.
- Your final picture is a tall frame for a vertical film. Draw it at 540 x 960, saved as /home/claude/build-57-garden/work/final.png. It may be redrawn at 1080 x 1920 with 64 samples later, so also leave a script, render_final.py, that draws your final scene with all its finishing, run as: python3 render_final.py WIDTH HEIGHT SAMPLES OUT.png
- When you finish (or at 21:47 on Thursday 05 November 2026), end with a report in plain words: what you built, how you lit and framed it, every picture you drew with how long it took, its measures, what you checked and fixed, and what you did not do. Your report is your last message.
- Keep /home/claude/build-57-garden/work/notes.md as you go: each picture with its time and measures, what you changed and what you fixed. This computer can stop without warning, and then that file is all that is left of your report.
