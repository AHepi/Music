# Japanese courtyard - project story

## The goal

Use the Astra Painted Workbench add-on you uploaded (version 0.2.0) to build a quick Japanese-style courtyard in Blender, then take a photo of it. Then check whether your newer upload (version 0.2.1) changes anything.

## Where things stand

- **Done:** a courtyard is built and photographed at golden hour: a wooden hall with glowing paper screens under a tiled roof, a pond with a zigzag wooden bridge and lily pads, rocks, a stone lantern, a red maple, a pruned pine, raked gravel, and hazy hills behind.
- **The photo:** "01 Japanese courtyard - golden hour photo.png" (2400 x 1600 pixels).
- **One thing to know:** your add-on says it was tested on Blender 5.1.x and only declares support up to 5.2.0. The Blender on this computer is 5.2.2. One part of the add-on (the roof and stone builders) stopped working there, so I added a small workaround in my own script. Nothing inside your add-on was changed.
- **Version 0.2.1 (your second upload):** the courtyard comes out exactly the same: zero different dots in the picture, and the same 89 objects and 214,689 corner points. What 0.2.1 adds is a safety net for the panel's buttons: if a button fails halfway, 0.2.0 leaves half-built objects behind, and 0.2.1 clears them away completely. I tested that through the real plank and roof buttons.
- **Not checked:** I have not tested the add-on's panel as a person would use it (clicking in the Blender window). I only pressed its plank and roof buttons from a script, and called its built-in functions for the rest. I did not use its live scatter tool, its "pigment" painting or its "detail" tool; they were not needed for a quick scene.

## How the pieces fit

| Piece | What it does | What it hands on |
|---|---|---|
| Your add-on (unpacked, untouched) | Makes the ceramic roof, the seated stones, the wooden planks, and the moss and pebble ground cover | Roof, stones, planks, terrain with moss and pebbles |
| `astra_loader.py` | Loads the add-on straight from its folder, and holds the small Blender 5.2 workaround | The add-on's functions, ready to call |
| `build_courtyard.py` | Builds the whole scene in order: ground and pond, hall, walls, stones, bridge, lantern, trees, lights, camera, then takes the photo | The Blender file and the photo |
| `rollback_test.py` | Presses the add-on's plank and roof buttons while forcing a failure near the end, and counts what is left behind in Blender, for either version | A short report: what each version left behind |
| The photo | The finished picture | What you see |

Re-making it: `blender -b --disable-autoexec --python build_courtyard.py -- ADD-ON_FOLDER OUT_NAME`. Building the scene takes about 10 seconds; taking the full-size photo takes about 13 minutes on this computer.

## Word list

- **Add-on:** extra tools added to Blender.
- **Blender:** the free 3D program.
- **Render / take a photo:** the computer works out what the camera would see, one tiny dot at a time.
- **Golden hour:** the hour before sunset, when the light is low, warm and long-shadowed.
- **Hall (with veranda):** the long wooden building; the veranda is the wooden floor along its front, under the roof's overhang (a Japanese engawa).
- **Shoji:** sliding screens of paper on a wooden grid; here they glow warm as if lit from inside.
- **Stone lantern:** the stacked stone lamp by the pond (a tōrō).
- **Raked gravel:** pale gravel with combed lines and rings around the rocks.
- **Workaround ("shim"):** a few lines that make an old tool work with a newer Blender, without editing the tool.
- **Moss and pebbles:** ground cover the add-on grows along the pond's edge and around the rocks.
- **Safety net (rollback):** if a button fails partway, the add-on puts everything back the way it was before you pressed it, instead of leaving half-built objects.
- **Fingerprint:** a short code worked out from the exact shape of everything in the scene. Two scenes with the same fingerprint are identical.

## Log (added to, never rewritten)

1. **Opened the upload safely.** Unpacked it into its own folder and read its guide first. Searched all its code for anything risky (reaching the internet, starting other programs, deleting files): found nothing. Opened its parts library with Blender's automatic scripts switched off: it holds a ceramic roof, a seated stone and some surface materials.
2. **First test failed (a version difference).** The add-on could not set the roof's size. Cause: Blender 5.2 moved where those settings live, and the add-on was written for 5.1. Fix: a small workaround in my own script. Result: roof, stone and planks all worked.
3. **Stone rules.** The add-on refuses stones thinner than 0.2 m or more than six times longer than thick. Two of my stones broke the rule (a low step and the lantern's thin gallery); I made them thicker.
4. **Sky settings renamed.** Blender 5.2 renamed one sky setting; I used the new name.
5. **First picture: washed out.** Far too bright and hazy, and a huge green sheet floated at the top. That was my own "hill" shape, lit like cloth. Replaced it with three flat hazy ridgelines.
6. **Second picture: the pond hid itself.** Seen from a low camera, the pond was mostly behind the bridge and the rocks, so it looked like dark ground. Made the pond bigger, moved the hall back a metre, raised the camera, added lily pads and a few lotus flowers.
7. **Slow build (7 minutes).** My way of making thousands of leaves got slower as it went. Rewrote it with a faster method: the build now takes about 10 seconds.
8. **The maple looked like popcorn.** Chunky balls. Replaced them with thousands of flat five-pointed leaves over a dark core. It reads as a maple now.
9. **The sun did nothing (two causes).** (a) The hall is about 4 metres tall, so a low sun behind it throws a shadow some 25 metres long, covering the whole garden. (b) My hazy hills were blocking the sun too. Fixes: the sun now comes low from the left, the hills no longer cast shadows, and I removed the left garden wall, which would also have blocked it.
10. **Haze test dropped.** A thin golden haze made soft beams but turned the picture dim and killed the sky's glow. Left out.
11. **"White shapes" beside the bridge were not a fault.** I hid objects one group at a time to find them: they are the pond's mirror reflection of the glowing paper screens. I softened them by roughening the water slightly and dimming the screens a little.
12. **Final photo** taken at 2400 x 1600 pixels (180 samples, 13 minutes 21 seconds).
13. **Compared add-on 0.2.1 with 0.2.0.** Unpacked 0.2.1 into its own folder and read its notes first. Compared the files: every part my courtyard script uses (roof, stones, planks, ground, materials) is identical; the differences are the version number, the panel's buttons, and one new file that adds the safety net. Built the courtyard with both versions (small preview): the scene fingerprint matched exactly (89 objects, 214,689 corner points, 236,044 faces) and 0 of 345,600 dots in the pictures differed. Then pressed the real plank and roof buttons with a failure forced near the end: 0.2.0 left behind 2 objects, 1 shape and 7 materials for planks, and 2 objects, 2 shapes, 3 materials and 5 geometry recipes for the roof; 0.2.1 left nothing. The forced error still shows as an error in both (correct: the safety net cleans up, it does not hide the problem). Normal button presses worked the same in both. Not tested: stone, ground, scatter and detail buttons, the panel's Undo/Redo inside the Blender window, Blender 5.1, a full-size photo with 0.2.1.

## Next step

A second photo from the veranda, looking out over the pond (about 15 minutes). Other ideas for later: a different time of day (blue evening with the lantern lit, or morning mist), or more details (a bamboo water spout, a tea house, fish in the pond).
