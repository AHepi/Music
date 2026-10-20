# 06 Check - what was checked and fixed

What this is: the record of an independent check of the guides, made after they were written. The checker started at
[06 Cookbook - start here](06%20Cookbook%20-%20start%20here.md), followed it to every guide (the ten 06 files in this folder and the twelve 04 files in
`recipes/<surface>/`), and checked five things: (1) every link and picture path; (2) numbers against the files the guides name; (3) plain words;
(4) anything presented as tested that the files show was not; (5) whether a newcomer could follow the checklist and the tool guides to make a new
texture. Every correction is listed in section 6, with the old and the new words. What is still wrong is in section 7.

Words are used as in the start page, section 6. Labels: **TESTED** = run here and measured, with the file named; **NOT TESTED** = only read or reasoned.

The checker's own scripts and results are in `checks/independent_check/`:
* `check_links_independent.py`: a second link checker, written separately from `checks/overview/check_links.py`; it also finds links whose targets
  hold spaces or brackets, picture tags and reference-style links.
* `check_code_paths.py`: looks up every file name written in `code` style in the guides.
* `number_checks.py` -> `number_checks.json`: 55 numbers re-read from the files the guides name, each compared with the guide.
* `new_reference_name_test.py` -> `new_reference_name_test.json`: can the two scoring tools score a surface they have never seen? (section 5)

---

## 1. Links and pictures

**Result: no broken link or picture on any of the 24 pages** (the ten 06 files, this page, the twelve 04 files and the slate-layers README): 320 links
and pictures found by both checkers, 0 broken (TESTED, both scripts, after all the changes below). Before the changes it was 316 links on 23 pages, also
0 broken; the four new links are the three this check added to point at this page and this page's own link to the start page.

The file names written in `code` style were also looked up: all that name a real file resolve, once the guide's own short forms are read as each guide
says ("`checks/`" in the baking and checking guide = `cookbook/checks/baking_and_checking/`; "`brick/final_report.json`" = `recipes/brick/...`;
"`research/.../`" = any folder under `research/`). What does not resolve is on purpose: placeholders and naming examples (`NAME`, `seed_N`, `var_NNN.json`,
`<surface>`, `name_nor_gl.png`, `..._class_M.png`), a command (`pkill -f run_everything.sh`), a function written as file.function
(`generator/preview_tools.measure`), and three files the guides themselves say do not exist (gravel's and slate's `analysis_findings.md`, which the helpers were not allowed to write, and
`make_normal_strength_strip.py`, which wood's recipe guide says is a stale name in a script note).

The overview picture of the start page was checked too: its two files are 1348 x 1710 dots (3.1 MB) and 972 x 1230 dots (295 KB), as the page says; all
30 input pictures listed in `checks/overview/overview_files_used.json` exist; and every caption number (sizes, tiers, SSIM, same-kind scores of the first
new tile) matches the `final_report.json` files.

---

## 2. Numbers against the files

**How:** 55 numbers spread over all ten 06 files were re-read by `number_checks.py` straight from `final_report.json`, `verifier_answer.json`,
`scores/*.json` and the cookbook's own check files (all match after the fixes below; the list with both values is `number_checks.json`). About 90 more
were compared by hand while reading, among them every number of the start page's results table (section 5), every row of the descriptions guide's
ladders (section 3.2) and new-tile table (section 5), the baking guide's self-test table (7.4) and yardstick table (7.5), the relief guide's ceiling
and geometry tables (3.1, 9), the seamless guide's half-tile, area and picture-size tables (8.1, 9, 10), the geometry guide's verdict table (11), and most
numbers of the checklist, each against its Lessons, Recipe, report or checker file.

**Mismatches found, with the right value, all fixed in place:**

| guide, place | it said | the file says | file |
|---|---|---|---|
| checklist C3b; descriptions guide 3.2 (mud) | the correction layer bought "+0.03 SSIM for +50 KB, against +0.055 for +154 KB of ground patches" | in the bakes, L -> L final (+49,654 bytes) bought SSIM +0.009 (0.688 -> 0.698) and edge skill +0.041; L2 -> L (+153,816 bytes) bought SSIM +0.056 and edge skill +0.080. The quick numpy tests: +0.021 SSIM for +38.9 KB of corrections. The builder's "+0.03" matches neither | `recipes/mud/final_report.json`; mud recipe guide, section 6; `mud/builder_answer.json` |
| checklist E5 | sampled mud tiles score 0.25 to 0.38 "against gravel, brick, slate or metal" | the lowest of that range, 0.247, is against WOOD; the scores were gravel, brick, slate, metal and wood | `recipes/mud/verify/var_103/texture_vs_wood.json` and the other `tx_*` / `texture_vs_*` files |
| descriptions guide 4; seamless guide 8.2 | metal M and L seam numbers "1.34 and 1.37" | 1.33 and 1.38 (1.34 / 1.37 is the builder's earlier report) | `recipes/metal/scores/M_texture.json`, `L_texture.json` |
| baking and checking guide 5 | smoothing the height took the "normal agrees with the height" measure "from 1.0 to 0.0" | from 0.788 to 0.0 | `checks/baking_and_checking/smoothed_height_check.json` |
| baking and checking guide 7.5 | gravel's height ceiling 5.02, quoted from `final_report.json` | 5.01 (5.02 is the builder's figure for its written-out colour mix; the relief guide, which gives that mix, keeps 5.02) | `recipes/gravel/final_report.json`, derivation_ceiling |
| pattern makers 7.1 | brick L with grain 0, from `scores/rate_distortion.json`: SSIM 0.673, same-kind 0.432 | 0.672 and 0.434 in that file (0.673 and 0.432 are the other bake of L, in the "classes" block) | `recipes/brick/scores/rate_distortion.json` |
| checklist C1 | metal's layout "4.8 KB" (on a page that counts 1024 bytes per KB) | 4,840 bytes = 4.7 KB | `recipes/metal/final_report.json` |
| descriptions guide 9, item 2 | "9,383 patches (slate) can be traced into 512 KB; 92,000 (wood) or 226,197 at 24 colours (gravel) cannot" | three different counts were compared: slate's 9,383 are patches over 12 dots (442 KB traced); gravel's patches over 12 dots are 18,881 and need 1,182 KB; 226,197 is gravel's count of ALL patches; wood's 92,000 is all areas, 43,000 of them 1 to 3 dots | gravel recipe guide, appendix A9; `gravel/final_report.json`, palette_ceiling; wood recipe guide, section 4 |
| checklist A4 | metal's wrap edge jumps "2.06 times harder" (next to "seam number 1.69 to 2.49" for the references) | 2.06 is the metal builder's own measure; the project's seam number for metal is 2.02. Both now named | metal Lessons, step 2; `checks/baking_and_checking/self_tests.json` |

Numbers that looked wrong but are right: the overview's metal "4.9 KB" new tile (5,027 bytes = 4.91 KB); slate S0 SSIM given as 0.711 in one place and
the metal S0 SSIM as 0.655 in another and 0.656 in a third (0.6555 rounds either way); "18.3" for metal's 20 % geometry mix (18.25); brick's two bakes of
L (0.673 / 0.672), which the start page already explains.

---

## 3. Plain language

**Words used without a one-sentence explanation, now explained where a newcomer meets them:**
* start page, section 6 (the shared word list): **correlation**, **percentile**, **plain slope** and **Sobel slope**, **plain Python / numpy / OpenCV**,
  **Cycles**, and the three senses of **recipe**; it now also says that the geometry guide, like the slate guides, calls an element a "piece".
* checklist: **Sobel** (A1), **Lab colour system** (A8), **orthographic camera** (B1), **numpy preview** and **OpenCV preview** (B4),
  **tessellate_polygon** (B5), **gain per byte** and **wrap-padded copy** (C3b), **percentile** (G2).
* descriptions guide: "4D noise" (now "the seamless donut noise", with a pointer), "label picture", "with a smoothed height".
* pattern makers and geometry guides: **seam number** added to their word lists.

**One word for one thing.** The start page promises that the 06 guides use one word each, but "seam ratio" and "seam measure" were used for the seam
number 16 times (pattern makers 9, geometry 3, painted look 2, start page 1, checklist 1): all now "seam number". The painted look guide's "normal
jump" (meaning an ordinary jump between neighbouring dots, not a normal map) is now "ordinary jump".

**"Works" with nothing to show it ran.** Every "works" or "ran" in the 06 guides was traced to a file or a log, except one: the painted look guide said
its new soft-edge outline band "works and it is seamless". The line drawing was measured (`numbers_painted.json`), the seamlessness was not; the
sentence now says "should be seamless because it is built only from seamless noise (reasoned, NOT TESTED)".

The 04 guides were read for plain words as well. The checkers' earlier complaints (SSIM, Ward clustering, Zhang-Suen thinning, Douglas-Peucker, Hessian,
watershed, solidity, log-normal ...) have been answered: each is now explained in a sentence where it first appears. Remaining heavy spots are listed in
section 7.

---

## 4. Presented as tested, but the files show it was not

1. **Painted look guide, trap 17:** "`save_array_png` writes a one-channel array into the red channel only" was listed among the traps "all met by
   testing", but the baking and checking guide TESTED the current function and it writes grey into all three channels (`save_grey_check.log`). Now says
   that this was an older copy.
2. **Pattern makers guide, section 2, and geometry guide, section 1:** research scores (the toolbox's first attempts, 0.05 to 0.29; the geometry
   research brick wall, 0.171) were compared directly with the builds' scores. The research score files are dated 14:28 to 15:43 on 19 October, before
   the same-kind tool's height measures and yardsticks were changed at 15:45; the builds were scored afterwards. Both guides now say the comparison
   crosses tool versions and is NOT TESTED as like for like.
3. **Descriptions guide, section 8, "What is ready (TESTED in the builds)": "one script and 10 to 20 minutes of work"** per new surface. The scripts
   and bakes are real, but the minutes are the builders' own counts: the wood and gravel checkers called them "not checkable", and slate and metal
   recorded no working time. Now labelled so (also in section 1, rule 7).
4. **Checklist, "Which steps all six builds followed: ... G1"**: G1 includes "write down the time"; slate and metal did not. Now says "G1 only in part".
5. **Checklist A1:** "wood's [script] has the reference folder written into one line, which you must edit" suggested the other five scripts do not. All
   six `analysis/derivation_ceiling.py` have `REF = .../reference/<surface>` written in, and brick's and metal's also `OUT = ...` (checked by reading the
   six scripts). Fixed.

Checked and found true: all six builds' Geometry Nodes routes end with Set Material (each `builder_answer.json`, "blender_tools_used"); the harness
calls counted in the baking guide (11, 11, 17, 22 in the generators); "each checker re-baked one to four new tiles" (brick 4, metal 3, slate 2, wood,
mud and gravel 1 each); the derivation scripts exist in all six builds; both link checkers report 0 broken links.

---

## 5. Could a newcomer follow "how to start a new surface" and the tool guides to make a new texture?

**What a newcomer gets:** a clear order of work (checklist sections 0 to H), every step with an example and a number, the traps each build hit, the
yardsticks to read scores against, a command for the dot-for-dot tool, the same-kind tool and the size check (baking guide, cards 4 and 5), and in each
04 Recipe the command that bakes that build's descriptions.

**What is missing (the checklist now has a short step 0.4 for the first three):**
1. **The same-kind tool cannot score a new surface as it stands** (TESTED, `new_reference_name_test.json`): it knows only the seven names written into
   `lib/texture_compare.py` (`ALL_REFERENCES`) and its yardsticks file `lib/texture_compare_anchors.json`; a new name stops with `KeyError`. The
   dot-for-dot tool scored the same copy under a new name without trouble. Adding a surface means editing that list and rebuilding the yardsticks
   (`python3 -I lib/texture_compare.py --anchors`), which shifts every existing same-kind score a little (each yardstick is a middle value over the
   other surfaces) - NOT TESTED, and no guide said it before this check.
2. **How to set up the reference folder** (file names, the 8-bit and 16-bit heights, an OpenGL normal map) was only in `reference/README.txt`, which no
   guide linked.
3. **Which files to copy, and that new elements need new Python.** The checklist says "build one generator" but no guide says which build's files to
   copy, which lines carry the surface name, or that the part turning a description into shapes (`slate_layers.py`, `mud_layers.py` ...) is written
   for one surface's elements. A non-programmer cannot write that part from these guides: the guides explain the ideas and the Blender settings, not the
   Python. This is the biggest gap.
4. **No surface has been started from the checklist.** Every transfer changed descriptions of an existing build; nobody has copied a generator to a new
   surface or followed the checklist from step 0 (the checklist says so: NOT TESTED).
5. **The tool guides and the checklist describe two different routes.** The pattern-maker, shaper and painted-look guides are mostly about shader nodes
   (the research route); the checklist says to build a painter of flat shapes in Python, which every build did. A newcomer who follows the tool guides
   builds a shader recipe, which scored 0.05 to 0.29 in the research; the guides say so (pattern makers, section 2), but there is no worked example of a
   small painter generator to start from.
6. **Without any reference picture** (a surface invented from scratch) the method has nothing to measure; the only route is a transfer from the closest
   build, judged by eye (checklist 0.3 and G).
7. **The scripts each build used for the half-tile test differ** (brick `generator/seam_test.py`, gravel `analysis/half_tile_test.py` with the size
   fixed at 512 dots, metal `final_tests.py seam`); there is no shared one in `lib/`, and gravel's would need its size changed.

---

## 6. Every change, file by file

**06 How to start a new surface - checklist.md**
* 0.4 added: the reference folder, which tool can score a new name and which cannot (TESTED), the scripts and commands to start from, and that new
  elements need new Python (NOT TESTED as a whole).
* A1: "wood's has the reference folder written into one line" -> all six have `REF = ...`, brick and metal also `OUT = ...`; Sobel explained.
* A4: metal's 2.06 named as the builder's measure, next to the project's seam number 2.02.
* A8: the Lab colour system explained.
* B1: orthographic camera explained. B4: numpy and OpenCV previews explained. B5: `tessellate_polygon` explained.
* C1: "4.8 KB" -> "4,840 bytes = 4.7 KB".
* C3b: gain per byte and wrap-padded copy explained; the correction-layer numbers replaced (section 2).
* E5: the other references are gravel, brick, slate, metal or wood; 0.247 is against wood; the files named.
* G2: percentile explained. B3: "seam measure" -> "seam number".
* "What was tested": G1 "only in part"; a sentence on this check.

**06 Guide - descriptions - analyse, describe, generate, compare.md**
* 1, rule 6: "with a smoothed height" explained. Rule 7: the 10 to 20 minutes are the builders' own, unchecked counts.
* 3.2 metal table: "4D noise" -> "seamless donut noise", with a pointer. 3.2 mud: the correction-layer sentence replaced (section 2).
* 4: metal M and L seam numbers 1.34 / 1.37 -> 1.33 / 1.38, file named; "label picture" explained.
* 8, item 4: TESTED part (the bakes) and NOT TESTED part (the minutes) separated.
* 9, item 2: the three patch counts made comparable.

**06 Guide - baking and checking maps.md**
* 5: "from 1.0 to 0.0" -> "from 0.788 to 0.0".
* 7.5: gravel ceiling 5.02 -> 5.01, with where 5.02 comes from.

**06 Guide - seamless tiles and coordinates.md**
* 8.2, blind spot 3: metal M and L 1.34 / 1.37 -> 1.33 / 1.38, file named.

**06 Guide - pattern makers.md**
* Word list: "seam number" added. Nine "seam ratio" / "seam measure" -> "seam number".
* 2: the toolbox scores come from the earlier copy of the same-kind tool; NOT TESTED as like for like.
* 7.1: brick L grain-0 values 0.673 / 0.432 -> 0.672 / 0.434 (the cited file), with the other bake named.

**06 Guide - geometry nodes, curves, modifiers and physics.md**
* Word list: "seam number" added. Three "seam ratio" / "seam measure" -> "seam number".
* 1: the 0.171 against 0.407 comparison crosses tool versions; NOT TESTED as like for like.

**06 Guide - the painted look.md**
* 4: the soft-edge band's seamlessness marked as reasoned, NOT TESTED.
* 8: "normal jump" -> "ordinary jump"; "seam measure" -> "seam number" (also trap 13).
* 11, trap 17: the red-channel trap marked as an older copy of the function, with the test that shows the current one is fixed.

**06 Cookbook - start here.md**
* 4: this page added to the list of guides. 5: "seam measure" -> "seam number".
* 6: correlation, percentile, plain and Sobel slope, plain Python / numpy / OpenCV, Cycles and "recipe" added; "piece" note widened.
* 8: a pointer to this check's newcomer findings.

No 04 file and no file outside `cookbook/` was changed (the 04 guides already carry their checkers' corrections; their numbers were spot-checked and
matched). The relief and shapers guides needed no change.

---

## 7. Still open (not fixed here)

1. **The same-kind tool cannot score a new surface** without editing `lib/texture_compare.py` and rebuilding its yardsticks, which shifts every old
   score (section 5, item 1). That is a change to a shared tool, so it was left for the person to decide.
2. **No starting template for a new generator**, and the shape-making part needs new Python for new elements (section 5, items 3 and 5). The guides
   cannot be followed by a non-programmer to a new texture without help.
3. **Nobody has followed the checklist on a new surface** (section 5, item 4).
4. **No shared half-tile test script** in `lib/`; gravel's is fixed at 512 dots (section 5, item 7).
5. **The research guides (02, 03)** still quote "another surface about 0.1" and scores from the earlier same-kind tool; the start page says so and they
   were left as written. Any 06 sentence that compares research scores with build scores should be read with that in mind (two are now marked).
6. **Mud's builder report still says "+0.03 SSIM for +50 KB"** (`mud/builder_answer.json`); the guides no longer repeat it, but the report was not
   changed (reports are records, not guides).
7. **Heavy jargon left in the 04 Recipe files** where a newcomer reads them as reference: `bpy`, `from_pydata`, `np.roll`, "k-means", "Gaussian",
   "Hough" and code names of functions appear in the tool-by-tool sections (mostly next to a plain description, but not always). The 06 guides and the
   checklist are the plain-language route; the 04 Recipes stay the detailed record.
8. **Different ways of counting KB** remain inside the metal and mud 04 guides (1000 bytes) against 1024 elsewhere; the start page explains it and the
   byte counts agree everywhere.
9. **The overview picture and the soft-edge band strips were not re-made**; the band's seamlessness is still unmeasured.

---

## 8. What this check ran, and what it did not

TESTED for this check (plain Python, `python3 -I`; no Blender): both link checkers on all 24 pages; the code-path look-up; `number_checks.py` (55
numbers, all matching after the fixes); `new_reference_name_test.py` on a throw-away copy of `lib/` and of the brick reference (the real `lib/` and
`reference/` were not touched); the six `derivation_ceiling.py` scripts read for their `REF` lines; the sizes of the two overview pictures and the
existence of its 30 inputs.

NOT TESTED: no Blender bake was made, so no score was re-measured from a picture; numbers were checked against the files, and the files were trusted
(the builds' checkers had already re-baked them). The step 0.4 instructions were not followed through on a real new surface. Rebuilding the same-kind
yardsticks was not tried. A person new to the job has still not read the guides.
