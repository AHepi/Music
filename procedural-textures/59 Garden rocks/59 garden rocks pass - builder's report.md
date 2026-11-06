# 59 The Japanese garden's rocks - builder's report

What this file is: the report, word for word, of the fresh builder who redid every rock in the garden at the owner's word (decision 89; 6 November 2026, 09:30 to 10:39), from the plugin and the owner's words alone, with the brief `A change the owner asks for.md`. Saved by the session. Its words are in `59 garden rocks pass - builder text.md`. Its comparison pictures (`pics/cmp*.png` in its work folder) hold no picture of the owner's, but they are crops beside the earlier pictures and stay on this machine.

---

I worked from the kit's "A change the owner asks for.md", "Before you build.md" and "The look.md".

The owner's last words were: "The next thing to work on is the rocks. They need to be procedurally generated in a particle system. And better textured". Both parts are done. Every rock in the garden is now made by rules and placed by Blender's particle system, and every rock wears a photographed stone surface. Both pictures stay inside every band of the look. The layout, the camera, the lights and everything that isn't a rock are as the earlier builders left them.

**What I changed and how**
- **Before:** every rock was a hand-placed ball of noise, about 80 of them, all in one smooth material smothered in bright moss. In the pictures they read as soft green pillows.
- **Rule-made rocks:** I used the store's rocks tool. Each rock is a lump of stone broken along a few faces, its edges rounded by weather and its skin pitted, and each has its own shape.
- **The pond's bank and the channel under the bridge:** the tool scatters 120 old boulders from 16 cm to 1.1 m across along the waterline, with the small ones gathered at the feet of the big ones. It keeps the earlier gaps: the stepping-stone edge, under the bridge and the open near shore.
- **Rocks with a set place:** the stone lantern's seat and mound, four single boulders, the rock by the basin, two flat stones in the near water, the basin's front stone and 18 pads under the veranda posts. Each is still a particle copy of its own rule-made shape. Each sits where the earlier rock stood, as big and as high. The lantern's seat is a flat-topped stone with its top right at the lantern's foot.
- **Small rocks:** 14 small ones scattered round the foot of the stone basin.
- **Texture:** every rock wears the shelf's photographed lichen rock (colour, roughness, relief and height pictures, so PBR as the owner asked). The stone is greyed, the feet where they meet wet soil are darker and shinier, and the tops carry moss in the earlier builders' brighter green, a different amount on each rock. A dark wet band runs 7 cm above the pond's water. The four rocks nearest the eye have 3 cm of real bumps from the height picture.
- **The stone basin:** it keeps its carved shape and now wears the same stone and moss.
- **The earlier noise balls** are still in the file but hidden. That keeps the stone lantern and the leaves the earlier builders set on them exactly where they were.

**Pictures** (the limits are: brightness 0.14–0.35, warm share 15–36%, cool share 30–60%, warm light 0.4–4.5%)

| Picture | Time | Bright | Warm | Cool | Light |
|---|---|---|---|---|---|
| Earlier final | – | 0.23 | 34% | 31% | 4.1% |
| Earlier close view | – | 0.21 | 35% | 31% | 0.5% |
| 00 earlier script with the fresh kit, small | 09:31 | 0.23 | 34% | 29% | 4.3% |
| 01 first try, small | 09:37 | 0.22 | 34% | 32% | 4.4% |
| 02 | 09:40 | 0.22 | 34% | 33% | 4.1% |
| 03 close view | 09:44 | 0.21 | 34% | 32% | 0.5% |
| 04 | 09:47 | 0.22 | 34% | 32% | 4.1% |
| 05 close view | 09:50 | 0.21 | 34% | 32% | 0.5% |
| 06 | 09:53 | 0.22 | 34% | 32% | 4.1% |
| Final A | 09:57 | 0.22 | 34% | 32% | 4.1% |
| Close view A | 10:01 | 0.21 | 34% | 32% | 0.5% |
| 07 test, wetter rocks | 10:03 | 0.22 | 34% | 32% | 4.1% |
| 08 test, wet band at the water | 10:06 | 0.22 | 34% | 32% | 4.1% |
| Final B | 10:10 | 0.22 | 34% | 32% | 4.1% |
| Close view B | 10:14 | 0.21 | 34% | 32% | 0.5% |
| 09 test, moss differs per rock | 10:18 | 0.22 | 34% | 32% | 4.1% |
| Final C | 10:22 | 0.22 | 34% | 33% | 4.1% |
| Close view C | 10:25 | 0.21 | 34% | 32% | 0.5% |
| **final.png** | 10:29 | 0.22 | 34% | 33% | 4.1% |
| **closeup.png** | 10:33 | 0.21 | 34% | 32% | 0.5% |

Every picture is inside every band except 00. That one was the earlier script drawn small with few samples (cool share 29%); the earlier final itself measures inside.

**What I checked and fixed**
- **Fresh kit:** I drew the earlier script small with the fresh kit first. It drew the same place as its picture.
- **Rocks sank:** a check meant to stop rocks floating on land pulled the pond's rocks down to its bottom, and the lantern was left floating. Now that check only applies on land.
- **Near water hidden:** the scatter put a big boulder in the corner by the first stepping stone, hiding the water the last pass had opened up. I kept that corner clear.
- **Bank rocks too small:** most were too small to see from the camera. I made them bigger and laid 120.
- **Black patch:** the tool's flat stones come in a dark smooth sea rock, and the basin's front stone drew as a black patch in the shade. All rocks now use the lichen rock.
- **Moss too dull:** it read grey-olive, so I brightened it.
- **Wrong setting:** my first try at varying the moss changed the setting for the dark wet feet by mistake. I stopped it before it drew anything and fixed it.
- **Thin moss on the basin:** varying the moss per rock also thinned the basin's moss, so the basin is left out of that.
- **Wetter rocks:** I tested making the rocks wetter all over. It made no visible difference, so I didn't keep it.
- **Looking:** I looked at every full-size picture zoomed beside the earlier one (pond, basin, veranda foot, close view). The veranda, path, light and everything else are unchanged.

**What I did not do, and why**
- **Small rocks by the basin:** one shows in the close view as a small dark stone; the other 13 are hidden behind the basin. Moving them would crowd the path's edge, and with 16 minutes left I couldn't test it and draw both finals again.
- **Stepping stones and path slabs:** left as they were. They are the path, which the owner's second picture was about, not the rocks.
- **Size and lantern height:** I didn't make the rocks bigger or the lantern's mound taller like the owner's picture. The layout and the lantern's height stay, and the owner accepted the smaller scale.
- **The plugin:** not updated. The project's notes file says every new set must update the plugin, but the plugin is outside the folders I was allowed to touch. Two things it could take from this pass: rocks placed one by one on chosen spots with a particle system, and the lichen rock for flat stones that sit in shade. That's for you to decide.

**Files** (all in /home/claude/build-57-garden/rocks)
- final.png
- closeup.png
- render_final.py (`python3 render_final.py WIDTH HEIGHT SAMPLES OUT.png`, add `--closeup` for the close view)
- change.md
- materials - rocks pass.md
- notes.md (every picture, change and fix)
- pics/ (every test picture, the side-by-side comparisons, and the scripts that drew finals A, B and C)

**For the project's Lessons file** (mistakes that had to be fixed):
- The not-floating check sank the pond's rocks.
- The scatter's area was wider than the earlier gaps and filled the opened shore.
- The tool's default flat-stone surface drew black in shade.
- Matching a setting by its value picked the wrong one.

From memory, I wrote this in plain words and named the guiding documents at the start, as the user prefers. Nothing in memory asked for anything outside this task.

---

## Traps

- This is the builder's own account; what the session checked afterwards is in the project story, log 59.
