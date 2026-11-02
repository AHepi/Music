# Control builder's report (tea house, no plugin)

What this file is: the control builder's final report, returned as text because the harness refused its file write; saved here by the coordinating session, unchanged in substance.

Owner's words: "A tea house."

Hand-in picture: `/home/claude/blind-test-2/control-build/final.png` (540 x 960), finished at 01:38 on this computer's clock (deadline 01:50).
Script: `/home/claude/blind-test-2/control-build/render_final.py`, run as `python3 render_final.py WIDTH HEIGHT SAMPLES OUT.png`. It is self-contained (no picture files are read). It was run from scratch for the hand-in picture. It also writes `OUT.raw.png` (the picture before finishing).

## What it built
A tea room in Britain around 1915, in an old iron-framed building, seen from the door end, standing, looking straight down the middle aisle.
- Hero: a big brass tea urn on a dark wood counter at the far end, centred, with a thin column of steam.
- Room: dark plank floor (every board a real shape with black gaps, scuffed down the middle), panelled wood low on the walls, teal paint peeling to plaster and brick, teal iron posts with rust where the paint chipped, ceiling beams with dirty roof glass between them.
- Things people use (the scale): marble-topped tables on iron feet, bentwood chairs, a tea trolley with pot and cups in the aisle, cups and pots on tables, three hanging gas lamps, six wall lamps. Brass, dark wood, steamed glass. No people, no hands, no words.
- Far wall: a big iron window, steamed over. Most panes are painted over, so the sun only gets in through 15 of 42.

## How it was lit and framed
- One main light: a low amber sun behind the far window, shining down the room toward the viewer (about 27 degrees down). It makes visible shafts in a thin haze, a window-shaped bright patch on the floor beside the trolley, and glints on the brass. The steam catches it.
- Cool light: dusk blue through the window plus a dim blue glow from the roof glass (the teal shadows).
- Small warm lights: the lamps, plus one spotlight from the counter lamp on the urn (so it is not a black shape against the window).
- Air: thin haze, so far things are lighter and bluer.
- Framing: tall 9 by 16, standing eye height (1.58 m), 30 mm lens, vanishing point about 42 percent down from the top, in the middle of the window wall. Beams and lamps lead to it. Foreground along the bottom: boards, a chair at left, the trolley, a table at right.
- Finish (in the script): paint-like smoothing that keeps built edges, glow round lamps and window, blue-black darks (warm-brown near light), amber lights, dark edge, a little grain.

## Pictures drawn (this computer's clock, all in `pics/`)
"Passes" = samples per pixel.

| Picture | Size | Passes | Time |
|---|---|---|---|
| probe_cube (machine test) | 270x480 | 16 | 2 s |
| t01 first look, no haze | 270x480 | 16 | 25 s |
| t02 haze and steam (milky) | 270x480 | 16 | 73 s |
| t03 | 180x320 | 24 | 65 s |
| t_fixed (timing test) | 90x160 | 4 | 43 s |
| t04, t05, t06 | 270x480 | 28, 24, 24 | 27 s, 49 s, 48 s |
| c01 (close check, wrong spot) | piece of 810x1440 | 48 | 91 s |
| t07 | 270x480 | 24 | 50 s |
| c02, c03, c04 (close checks of window, urn, steam) | piece of 540x960 | 40 | 45 s, 44 s, 47 s |
| t08, t09, t10, t11, t12 | 270x480 | 24 | 64 s, 50 s, 53 s, 51 s, 58 s |
| final_a (walls too orange) | 540x960 | 64 | 8 min 28 s |
| t13 | 270x480 | 24 | 43 s |
| final_b | 540x960 | 64 | 7 min 37 s |
| final_c | 540x960 | 64 | 4 min 46 s |
| final_d = the hand-in (full run of the final script) | 540x960 | 64 | 4 min 50 s |

Also: about ten tiny crash-check pictures (90x160 or 24x40, 1 to 3 s each), four unsaved timing runs, and about ten finishing-only variants (0.5 to 3 s each, no new drawing: `fin_*`, `final_c2`, `final_c3`, `crop_*`, `cmp_*`). The finishing was checked at 1080x1920 by finishing an enlarged copy (3 s). Final picture = final_c's drawing with a deeper finish; final_d is byte-for-byte the same.

## What it checked and fixed
The look.md bands (brightness 0.14 to 0.35, warm share 15 to 35 percent, cool share 30 to 60 percent, warm light coverage 0.4 to 3.0 percent): `measure.py` was not in its folder, so it wrote `measure_mine.py` and tuned it until all five reference pictures fall inside the bands. The hand-in picture measures brightness 0.223, warm 20.8, cool 37.6, warm light 1.42: all inside. A stand-in, not the real tool.

Milestones and fixes, each against The look.md:
1. "Light is rare": first haze made everything milky. Cut it from 0.045 to 0.015 and made it even all through (also much faster).
2. "Light does something to the air": the shafts were a flat glow until most panes were painted over, so the sun enters in a few places.
3. "One hero": the urn first looked like a black figure. Added the counter spotlight, made the brass partly matt, made it bigger. The first spotlight sat inside the lamp's glass ball and lit nothing.
4. The steam did not show: its box was measured from the world's centre, so its density saw nothing. Centred on its own origin. Each steam box also costs about 10 s of set-up, so quick tests leave steam out.
5. Several colour gradients (window blue and amber, floor aisle, soot on walls, low rust on iron) were silently flat because colour-ramp stops beyond 0 to 1 get squashed. Added a rescaling step. One change brought the window's blue back.
6. "Old and used": flat puddle shapes looked like black holes. Replaced with wet patches inside the floor material, plus scuffs.
7. "Two colour families": first too brown, then too blue. Raised the sun so its patches land in view, added the dim roof glow, warmed the lamps.
8. "Old and used" and "period": loud orange wall and pane blotches read as camouflage. Made them rarer and duller.
9. Checked by eye at full size: no words, no people, no hands, no balloon smoke, no flat even light.

## Weak spots it could see
The window wall reads olive-grey in the haze rather than clean teal. The urn is more copper than brass. The painterly smoothing is blotchy on walls at this size. The foreground chair is a big dark shape. The steam is thin. Wet patches are mild; no rain or puddle mirror.

## What it did not do
- It did not update the plugins (a control build may only touch its work folder). Fixes 2, 4 and 5 above are what a plugin would need to carry.
- It did not use `measure.py`, other folders, the internet or image generation.
- It did not draw the 1080x1920 version. At 64 passes expect about four times the 540x960 time (4.8 to 8.5 minutes there, depending on how busy the shared computer was).
- No exterior, rain on the glass, dust specks or daylight version. Far tables are plain.
- Older script copies `render_final_pass1.py` and `render_final_pass2.py` are left in the folder; only `render_final.py` is the final.

## Words from The look.md (its glossary)
- Cool shadow: teal-blue to slate (#0d2637, #3c4a51, #6e8c8a). Warm light: amber (#d2a76b, #dbad72). Rust-orange is the bridge.
- One dominant light: one source with a direction, always doing something to the air.
- Air between here and there: far things lighter and bluer.
- Hero subject: one thing, centred or near it. Foreground: detail along the bottom edge.
- Measured bands: the four numbers above.

## Traps it listed
- The 1080x1920 redraw at 64 passes is four times the picture area; allow more than half an hour if the computer is busy.
- Needs this Blender (5.1.2) and its names (for example the colour look "AgX - High Contrast"); another version may stop or look different.
- The finishing step needs numpy; without it only `OUT.raw.png` is written. The output folder must be writable.
- Do not run two pictures at once here; both slow down. The steam adds about 20 s of set-up to every full run.
- Its band check is a stand-in for the real `measure.py`; the real one may measure a little differently.
