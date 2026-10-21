# Work note: the weathering kit's foundation, in plain words

*What was asked:* build the part of the weathering kit that every later helper shares (the walls helper, the ground helper, the growth helper, the integrator) and prove it on three scenes: the village street, the lockout shot file, and the Japanese courtyard. Next time the kit goes to the courtyard, no code should have to change, only two files.

*Where it is:* `kits/weathering/` (code, packs, baseline) and this folder (raw arrays the packs are built from, test results, work scripts). `README.md` in the kit is the one-page map; `HOW TO USE.md` is for builders; `masks/CONTRACT.md` lists every mask name; `masks/NOT_DONE.md` is the honest list of what is missing.

## 1. What now exists

1. **The core.** It reads a place's settings file, finds which object plays which role (road, kerb, wall, iron ...), and has one way of putting a layer into any material without touching a mesh or a material slot (the "hook"), plus one way of keeping the layers in order on a material (the "chain"). The three earlier layers (wetness, joints, rubbish) are kept as pinned copies and slot into the same chain, so taking everything off puts every material back exactly as it was. A documented do-nothing layer shows builders how to write a real one.
2. **The where-pictures.** One reader looks at the real 3D shapes and writes pictures of where things are: ground height, slope, low spots, the crown of the road, distance to walls and props, steps, edges, stone gaps, shade, dampness, foot traffic, keep-clear places, places moss and weeds may grow, and for every wall a sheet with run-off sources (found from the ledges, sills, lintels, eaves and the downpipe), shelter, corners and reveals. 40 names in all; a layer asks for any of them by name.
3. **The scale helper.** Every mark is sized in plate dots and turned into metres from the camera, so a crack is never thinner than a few dots however far away.
4. **The test rig.** Cameras and the five lights as data, the 22 lighting pictures, five close views, plates (main, lockout, notice, close road), a job writer, a picture runner that opens each scene once and draws a whole list, a remote runner that only talks to the rented machine through the cached client, and measuring scripts for the pass lines P1 to P7, self-tests, a check that the kit code names no street, courtyard or object, and sheet makers.
5. **The baseline**: the earlier layers only, drawn three times, with the numbers frozen.

## 2. What the tests say (all of it is in `test_results.json`)

* **Does an Attribute node read an object's custom property?** Yes, in EEVEE and in Cycles alike (0.5552 against 0.5554 on a test object; an object with no such property reads 0). So every per-object number (seed, role, wall sheet, per-layer amount) is a custom property, as the plan wanted.
* **The hook** works on every material that has a surface: 41 of 41 street, 85 of 85 lockout (86 materials, one with no surface), and 128 of 134 courtyard (82 plain and 46 through the adapter for the add-on's shader; the other 6 are glow-only and are left alone on purpose).
* **A do-nothing layer in slots A, B and C draws the same picture as no layer.** Street 135 x 240 and 540 x 960, lockout the same two sizes, courtyard 1200 x 800: not one dot differs by more than one step of 255 on 99 % of dots (street and lockout: none at all; courtyard: 11 dots of 960,000, the same noise two draws of the unchanged courtyard show).
* **Taking layers off in any order, or twice,** leaves every material exactly as the snapshot (all three scenes).
* **Amount 0 changes nothing; a layer alone changes only its own roles; two draws are identical** (all three scenes).
* **The five lights as data match the earlier study's own lights** (A, C, D, E on the street and the lockout: no dot over one step). A mistake I found on the way: the flat overhead light D had house shadows switched off in my first version; the earlier study left them on; fixed and tested.
* **The mask bus** hands a layer the same number the pack holds: 200 random points, worst error 0.0012 on the ground masks in all three scenes (the line is 2/255 = 0.0078) and 0.0027 on the street and lockout wall sheets. **One failure:** the courtyard's "Hall plaster" wall sheet reaches 0.065 on a few points (details in `masks/NOT_DONE.md`).
* **No Bevel, Ambient Occlusion or Pointiness node** is used anywhere in the bus or scale helper (checked on the built node groups).
* **Reuse lint:** zero hits over `apply/`, `masks/`, `harness/`.
* **The measuring scripts** pass 28 checks against made-up pictures with known answers.

## 3. Which masks passed their checks

*Street and lockout (the same ground):* ground slope 4.0 degrees; the crown 8.0 cm high, in the middle of the road (every dot within 1 m of the middle line reads 0.6 or more, every dot farther than 1.8 m reads 0, no crown on other ground); the gutters read as low (99.98 % at 0.7 or more) and the road middle reads 0; all 28 entrances found; the ledge finder found cottage 01's sills at 0.85 and 3.55, string course 3.1, eaves 5.9, lintels 2.68, 2.88 and 5.18, steps 0.18 and 0.48 out, downpipe 2.05 across and 0.153 proud (all within 5 cm); 187 kerb stones; moss, weed and lichen fields exactly 0 in the trodden lanes, on the crown and on the keep-clear places (and algae where it must be); dampness above 0.6 at wall feet and pipe feet and below 0.2 in the middle of the road; foot traffic 0.9 on the crown and 0.85 or more at every door; keep-clear 1.0 on every doorstep strip and in the middle of the road; the shaded row's fronts 0.27 shadier than the lit row's (wanted 0.2); shelter under the sills 1.0. *Courtyard:* the four exactly-zero field checks pass, the pond's shore sits where the ground crosses z = -0.12, existing growth is found (9 patches for the 7 the set names), the doorstep checks pass.

*Did not pass:* the top of a sill reads 0.125 sheltered where the plan wanted 0.1 or less; the courtyard wall sheet above; one courtyard wall has no sheet; the plan's 99 % agreement with the earlier "places" pictures is 95.8 % for wall distance on every dot (100 % on the dots the earlier picture covered; it ignored steps in the middle of the road). The dot-size table of the plan is right for across (3 %) and wrong for along beyond 15 m because the table assumed flat ground (the road leans 4 degrees); the helper agrees with the arithmetic to 1 %.

Pack sizes: street 1.2 MB, lockout 1.3 MB, courtyard 0.94 MB, plus 3.3 MB of texture-space pictures the street and lockout share (all far under the 40 MB line).

## 4. The baseline (the earlier layers only; `harness/baseline/numbers.json`)

* **Joints.** 20 of 22 pictures pass with puddle and rubbish dots left out (the plan expected 21), 18 of 22 with every dot counted (as before). The two that fail are the lockout under the brazier's glare, wet and heavy. The wet one misses its middle band by 0.005 of contrast and 0.001 of brightness; the earlier study measured it just over the line on its own draw, and my joint, puddle and rubbish masks are identical to the earlier ones, so the difference is the draw. **The plan's line "at least 21 of 22" cannot be met by the baseline itself; I suggest the integrator's line is "no picture that passes in the baseline fails".** The three repeats agree to the last digit.
* **Wet look.** Main camera, light A: wet road is 1.8 times as bright as dry (it reflects the sky and the lamps), pavement 1.19, walls 0.85; heavy rain 1.81, 0.97, 0.82. Puddles cover 7.7 % of the main camera's road when wet, 29.7 heavy (close view 2.8 % and 12.4 %, lockout 6.3 % and 42 %).
* **How dark the plates are.** Main plate: mean brightness 0.20; walls 0.077 with 79 % of wall dots under 0.10; trims 0.097 (65 %); road 0.213 (10 %); pavement 0.185 (4.6 %). Lockout plate: mean 0.24, walls 0.085 (75 %), road 0.353 (7 %). The class and distance pictures that cut every plate into surfaces and distance bands are stored small beside it.
* **Time.** A 1536 x 2730 plate at 48 samples takes **2.0 seconds** on the rented card (best of three; close plate 1.9). The first picture after putting the earlier layers on takes 2.3 to 2.5 seconds. About 6,400 (street) and 7,200 (lockout) 3D rubbish pieces are in the baseline picture; the 2,500 limit for growth pieces counts on top of that.
* **One full test-set run on the rented machine:** street file 74 pictures in 43 seconds of drawing (48 s with Blender's loading), lockout file 19 pictures in 16 seconds (18 s); with the send and the return of the pictures, 87 to 102 seconds and 62 to 64 seconds, about **2.5 to 2.8 minutes for the whole set**. The same picture drawn on this computer takes 75 to 85 seconds each.

## 5. Reuse proof on the courtyard

Settings validate; the role finder finds all 88 meshes with no object in two roles; the reader ran (ground height, the year's sun for shade with 48 sun positions, the pond's shore, the add-on's moss patches) in 17 seconds; hook plus adapter on 128 materials; the do-nothing picture at 1200 x 800 matches the plain one; every self-test passes with the courtyard look. The courtyard file was never saved.

## 6. What I changed in the two settings files, and why

Street: dropped a role alias that matched nothing; the per-object flags now name their attribute (`wk_stepped`); entrances, steps, standing iron, covers and prop roles are named as data; footfall and keep-clear shapes can say "from the entrances"; the fire role now matches the barrel stove (it matched nothing before); texture periods (brick 1.4 m, stone 2.5 m); lights: the file's own sky lights are kept when a rig switches lamps off; test set: classes, which scene each camera belongs to, a fourth plate (close road, 1920 x 1440), per-camera "harsh grid" lines for the joint test; **dampness weights raised so a wall foot reads damp (0.65) and the foot of a pipe or post too (0.80), with a new `standing_foot` term**. Courtyard: dropped a doorway role, named its entrances, the adapter's outputs are data now, the bamboo-leaf material is left alone (it glows a little), leaf masses block the sun for shade, and it expects 7 existing-growth patches.

## 7. What I am unsure about

* The courtyard wall sheets: one wall has no sheet, others only read their dominant face. Builders working on courtyard walls will see the ground-plan fallback.
* The texture cell numbers for brick, stone and flags are approximate.
* The measures for P3 (readable marks), P4 (period caps and hue), P6 (pieces and marks) have never run on a real layer; only on made-up pictures. Expect small corrections when the first builder uses them.
* The baseline joint count is 20, not 21 (above).
* The lockout under the brazier's glare is borderline for the joint test by nature (the bright glare and the rubbish cover most of the middle band).
* The rented machine was reachable throughout; no "NO CARD FREE", no machine stopped or ended; nothing in `~/.runpod` was read. The protected folders (film project, `set_copy`, `tools`, `relief_and_rubbish`, `painter_round_2`, `painter_test`, `japanese-courtyard`, the add-on folder) were not written by this work: no start-of-job hashes were taken, so this is checked by file dates (files changed there since the work began belong to the other helpers running at the same time) and by the kit code never naming those folders. The lockout and courtyard files were opened read-only and never saved. No commit, no push, no paid call.

## 8. Pictures (in `25 Street grime, cracks, stains, weeds and moss - pictures/`)

Masks: the ground pictures of the street; one wall sheet of cottage 01; the habitat fields with the traffic lanes drawn over them; the same readers on the Japanese courtyard (two names); where each thing may go (every key mask seen from the main, lockout and close cameras). Test set: the baseline close views of the five places; the 22 lighting pictures baseline contact sheet.
