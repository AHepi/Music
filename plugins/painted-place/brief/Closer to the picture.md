# Closer to the picture

What this file is: the brief for one more builder, used when the owner has sent a picture with the request and, seeing the place built, asks for it to come closer to that picture (decision 86). It gets the place as the last builder left it and one job: compare the owner's picture with the place, and close the biggest differences first. Unlike the dressing passes, it may change the light, the sky, the layout and the camera where the owner's picture asks for it.

## The text

> You are bringing a place other builders made for a narrated explainer film closer to a picture the owner sent.
>
> The owner's words, in order: REQUEST
>
> The place is built, lit and dressed: its script, SCRIPT, rebuilds it (its pictures are PICTURES; the builders' material lists are MATERIALS). Your job: put the owner's picture and the place's picture side by side and write WORK/differences.md first, every difference you can see, biggest first: the light and the sky (where the light comes from, its colour, the air it falls through), the big shapes and where they stand, the middle distance, the near ground, the colour of the whole. Then close the differences in that order, as many as your clock allows, drawing and comparing again after each. Keep what the earlier builders made where the owner's picture has it too; change the light, the sky, the layout or the camera only where the picture asks for it. FOLDER/store/ holds ready parts, tools and materials you may use (see its Store.md); some may be better than what the earlier builders made by hand. Nothing in the store places itself. Read FOLDER/Before you build.md first.
>
> The film has a look: FOLDER/The look.md, the pictures in FOLDER/reference/, and FOLDER/boards/ for the real thing. FOLDER/Traps.md and the traps at the bottom of FOLDER/Closer to the picture.md list what has gone wrong before. `python3 FOLDER/measure.py SOME.png` measures a picture against the look's bands; measure the owner's picture too. Your picture stays inside every band; where the owner's picture sits outside one, go as far towards it as the band allows.
>
> What you have: a work folder WORK (write everything there), Blender 5.1.2 as the `bpy` module (`python3`), 2 processors, nobody else drawing.
>
> Rules: read nothing outside FOLDER, WORK and the earlier builders' folder; no internet, no image generation. Your clock ends at DEADLINE by this computer's clock; use all of it: draw, measure, compare with the owner's picture at full size, fix, draw again, and do not stop before the clock unless you can say what you would change and why you will not. Draw your final at 540 x 960 as WORK/final.png (and any other view the earlier builders delivered, under the same name); leave render_final.py (python3 render_final.py WIDTH HEIGHT SAMPLES OUT.png) that draws the finished scene with all its finishing. End with a report in plain words: the differences you found, which you closed and how, every picture with its time and measures, and what you did not do. Keep WORK/notes.md as you go (each picture with its time and measures, what you changed and fixed): this computer can stop without warning, and then that file is all that is left of your report.

## How it is run

Copy the last builder's `render_final.py`, its pictures and every builder's `materials.md` into a folder this builder may read; give it a fresh copy of the kit (the store may have grown since the earlier builders' copy: the copy must sit at the same path, so the earlier script still finds it), the owner's pictures in the kit's `request/` folder, an empty work folder of its own, and 100 minutes. REQUEST is every message of the owner's about this place, word for word, in order, each with the picture it came with. Save its report yourself. Its picture is the one the owner judges, beside the last pass's.

## Traps

- The owner's pictures go into the builder's copy of the kit only, never into the plugin or GitHub. The builder's comparison pictures hold cuts of them: they stay in its work folder too, out of the records (the first closer pass, log 58).
- A picture warmer or bluer than the look's bands can be matched in its light, its shapes and its brightness, not past the band: say so to the owner rather than leave the band. The first closer pass measured the owner's garden at 40% warm and 12% blue, and stopped at 34% warm and 31% blue (the floor is 30%).
- Changing the light changes every surface the earlier builders judged under the old light: look again at the near ground at full size after any change of light.
- The owner's picture may show a much bigger place than the set: the first closer pass matched the garden's look but not its size, about seven times smaller than the owner's picture (the owner's words, decision 88). Measure the picture's sizes from things of known size (Traps.md) before moving anything, and say what you find.
- A refreshed kit can change what the earlier script draws: draw the earlier script once with the fresh kit, small, and compare it with its picture before changing anything.
