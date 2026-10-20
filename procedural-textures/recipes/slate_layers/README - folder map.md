# Slate in layers - folder map (read this first)

This folder holds the slate texture as ONE Blender recipe made of separate layers inside it: LAYOUT, COLOUR AND FADE, DAMAGE, MOSS, OUTLINE AND SHADOW
and COMBINE. Nothing in it is a picture of the reference: every dot is made by Blender nodes from a list of settings (`recipe/settings.json`: 73 entries, 2.4 KB; the other 109 of the 182 controls keep the
starting values written in the layer files, so the whole description is about 6 KB, not only the 2.4 KB; corrected wording from the honesty check).
The reference picture was used only as a guide (looked at, measured once for its general character, never copied slate by slate).

**Updated 20 October after the "look fixes" (round 15).** The default tile was tuned again by hand (49 settings became 73, six new controls in two layer files) and everything that depends on the
default was baked again. Anything marked "before the look fixes" below was NOT baked again and describes the OLD default. Details: `05 Recipe ... how it is made.md`, section 6b.

The two guides to read are in this folder: `05 Recipe - slate in layers - how it is made.md` (what every layer and every Blender tool does, results tables,
dead ends) and `05 Lessons - slate in layers - what carries over to other surfaces.md` (how to split any surface into layers).

## Where things are

| folder / file | what is in it |
|---|---|
| `05 Recipe - slate in layers - how it is made.md`, `05 Lessons - slate in layers - what carries over to other surfaces.md` | the two guides |
| `final_report.json` | every number of the integration work in one file |
| `recipe/slate_recipe.py` | THE RECIPE: the file `lib/bake_harness.py` loads (`build_node_group(parameters)`); also the debug views and the half-tile shift |
| `recipe/settings.json` | the settings of the default tile (73 hand-tuned entries: 71 numbers and colours and 2 build settings, the stack order and the tile count); everything not listed keeps the layer file's starting value. `settings_before_look_fixes.json` = the old 49 |
| `recipe/controls.md` | ONE table of every control (182): layer, name, what it does, range, default |
| `layers/` | one file per layer: `layout.py`, `colour_and_fade.py`, `damage.py`, `moss.py`, `outline_and_shadow.py`, `combine.py`, and `layer_interface.py` (the fixed sockets) |
| `interface/interface.md` | the layout bundle (the eleven numbers every layer reads) and the rules of the layers |
| `outputs/default/` | the default tile baked at 1254 dots (**new default, after the look fixes**): `colour.png`, `height.png` (16 bit), `normal.png`, `roughness.png`, `metallic.png`, plus scores. `outputs/default_before_look_fixes/` = the old default, kept as it was |
| `debug_views/` | every layer alone: its mask and its colour (1254 dots), its height and roughness change (640 dots), sheets (**baked again after the look fixes**; `overview_masks_and_colours_before_look_fixes.jpg` = the old overview). The four sub-folders (`colour_and_fade/`, `damage/`, `moss/`, `outline_and_shadow/`) and the skeleton pictures are the layer builders' own old pictures and were not made again |
| `tests/independence_full/` | the independence table and pictures (amount 0 and seed + 1 for every layer), **before the look fixes** (384 dots, old default) |
| `tests/independence_changed_layers_after_look_fixes/` | the same test run again for the two layers whose files changed (MOSS and OUTLINE AND SHADOW), 512 dots, new default; table and numbers only (the pictures were deleted) |
| `tests/half_tile_layers/` | the half-tile shift test of the finished maps and of every layer on its own, for one tile and a 2 x 2 area (**run again after the look fixes**; `..._before_look_fixes` = the old table and numbers; the baked pictures were deleted to save disk, the tables and numbers are kept) |
| `tests/confirm_512_after_look_fixes/` | the new default baked at 512 dots (colour, height, roughness, metallic; the two normal maps were deleted to save disk), with `compare_512_with_1254.py` and its numbers and picture: the same look at a smaller size |
| `controls_sweeps/` | "what does this control do" strips for every layer (made by the layer builders at each layer's own starting values); `whole_recipe/` = five strips of the finished, tuned recipe **of the old default, not made again**. There are no strips for the LAYOUT layer |
| `links_and_order/` | (**old default, not made again**) the declared link (moss avoids damage) in colour (`links_sheet.jpg`) and in height (`link_height/link_measures.json`), the stack order, and the tone-blend height pictures (`tone_blend_sheet.jpg`) |
| `ladder/` | what each layer buys: layout and joints only, + colour and fade, + moss, + damage, and without the outline (`ladder_table.md` = new table, with the old one under "before the look fixes"; `ladder_sheet.jpg`; **baked again after the look fixes**) |
| `variations/` | eight tiles from eight settings variations, as a contact sheet with the settings under each tile (**baked again on the new default; v2, v4, v5 and v6 got new settings**; `variations.json` keeps the old settings and scores under "before the look fixes"; `tuning_512/` = the 17 small test bakes behind the four changes); `seed_spread/` = the default settings with three more sets of seeds (**baked again**) |
| `area/` | a 2 x 2 area (`area_2x2/`, **baked again after the look fixes**, old numbers kept as `..._before_look_fixes`) and a 4 x 4 area (`area_4x4/`, colour only, **before the look fixes: not baked again**) of new, non-repeating content, with seam and repeat measures |
| `resolution/whole_recipe/` | the same settings at 512, 1254 and 2508 dots, with the time of each bake: **before the look fixes (old default), not baked again** (its 1254 files are links to `outputs/default_before_look_fixes/`; the new 512 confirmation is in `tests/confirm_512_after_look_fixes/`) |
| `look_fixes/` | the tuner's work for the look checker's list (round 15): notes (`notes - look fixes round 15.md`, with the list "Corrections after the honesty check" at its end), settings sets, every test bake and picture, `round_1_tuner_result.json`, `round_2_tuner_result.json`, **`rebake_result.json` (what the re-baker did, with every number)**, `before_after_colour.jpg` and `before_after_lit.jpg` (in the lit picture the reference is lit without a roughness map, the two tiles with theirs: the reference set has none). `corrections_after_honesty_check/` = the two normal maps scored both ways for the old and the new tile, and the split of the colour gain (my re-measurement for the second honesty check) |
| `verify/`, `verify_look/`, `verify_look_after_fixes/` | the checkers' work: `verify/HONESTY_VERDICT.md` (are the claims true? yes, with wording errors, now corrected in the guides); `verify/after_look_fixes/HONESTY_VERDICT_AFTER_LOOK_FIXES.md` (the second honesty check, of the round-15 work: every number reproduced, eleven small wording faults, **now corrected**; its scripts and small result files are in the same folder); `verify_look/LOOK_VERDICT.md` (what looks wrong, 11 problems); `verify_look_after_fixes/round_1` and `round_2` (the look checker's two second looks) |
| `reuse/` | the unchanged colour, damage, moss and outline layers on a BRICK layout, and what had to change (`reuse_sheet.png`); `settings_round_2/` = one settings-only round on the brick. **Not baked again after the look fixes** (should be unchanged, untested) |
| `integration/` | the tuning notes: the rounds, the measuring scripts, `CHANGES_TO_LAYER_FILES.md` (every edit made to a layer file); `takeover/` = what the second integrator did after the restart (chain scripts and logs, clean-up list, numbers, `make_final_report.py`; `takeover/measured_before_clean_up.json` holds the numbers measured before the tuning-round pictures were deleted; its note about the two normal maps had them the wrong way round and is **corrected** since the second honesty check) |
| `damage_work/`, `moss_work/`, `outline_work/` | the layer builders' own working folders (kept for their notes; their bulky test bakes were removed to stay under the size limit) |

## How to bake it (copy and paste; Blender 5.2.2, CPU, 2 threads)

```
cd <proc-work>
# the finished maps (colour, height, roughness, metallic, normal)  - about 4 to 7 minutes at 1254 dots
blender -b --disable-autoexec -t 2 --python lib/bake_harness.py -- recipes/slate_layers/recipe/slate_recipe.py OUT_FOLDER --size 1254 --normal-reference slate
# one layer alone (debug view), for example the moss mask
blender -b --disable-autoexec -t 2 --python lib/bake_harness.py -- recipes/slate_layers/recipe/slate_recipe.py OUT --size 1254 --params '{"debug_view": "moss.mask"}'
# a bigger area of new slates (2 x 2 base tiles = 2508 dots)
... --size 2508 --params '{"recipe.tiles_across": 2}'
# the reference-style normal map from the baked height (3 x 3 Sobel, strength 7; "Sobel" = a standard recipe that works out how steep the picture is at each dot from the dots around it; a normal map is the picture that tells a renderer which way each dot of the surface faces)
python3 -I recipes/slate_layers/integration/make_normal.py OUT_FOLDER/height.png OUT_FOLDER/normal.png 7
```

## After the machine restart (20 October, about 03:15)

The first integrator was cut off by a restart before it wrote the guides and the report. A second integrator then checked every item on disk and
re-ran only what was missing or cut off (everything else is as the first integrator left it, and its tuning was kept):

| item | state found | what was done |
|---|---|---|
| default tile, debug views, independence table, half-tile test, variations, 2 x 2 area | complete | checked (pictures looked at, numbers read, colour group re-scored: same) |
| resolution | 2508 had only the colour | 2508 re-baked (colour, height, roughness), times and comparison written |
| reuse (brick) | only the finished wall baked | the four remaining views, the normal, the sheet and a sanity score; one more settings-only round |
| ladder | two of four rungs | the two missing rungs, scores and sheet |
| links and order | not baked | baked; the link also measured in height and roughness |
| 4 x 4 area | not started | baked and measured (the measuring script was made fast enough for 5016 dots first) |
| strips of the tuned whole recipe, seed spread | not started | added |
| tuning | 13 rounds, last two changed only the height | one more round (14, `integration/r14_results.json`): a lighter shadow and stronger streaks lift the default-seed score to 0.796 but only 0.005 to 0.011 on other seeds; settings kept |
| guides, final report | not written | written |
| folder size | 436 MB (limit 400) | superseded in-between pictures deleted or turned into JPEG; list in `integration/takeover/CLEAN_UP_AFTER_RESTART.md` |

## After the look fixes (round 15, 20 October, the re-baker)

| item | what was done | state |
|---|---|---|
| default tile | baked by the tuner at 1254 dots (colour, 16-bit height, normal at strength 7, roughness, metallic); the old one is `outputs/default_before_look_fixes/` | new |
| ladder | four rungs baked again (1254 dots), scored, table and sheet rebuilt; the old table is kept under "before the look fixes" | new |
| variations | eight tiles baked again; v2, v4, v5 and v6 got new settings (the look checker's advice tried at 512 dots first); scores and contact sheet rebuilt; old settings and scores kept in `variations.json` | new |
| seed spread | three more sets of seeds baked on the new default (with the default seeds and v1: mean 0.810, spread 0.032) | new |
| 2 x 2 area | baked again (2508 dots, colour and height) and measured again | new |
| 4 x 4 area | not baked again | before the look fixes |
| half-tile test | run again at 512 dots (eight Blender runs) | new |
| independence | run again for MOSS and OUTLINE AND SHADOW, the two layers whose files changed (512 dots); not for the other layers | new (two layers) |
| 512 bake | one 512-dot bake of all maps compared with the 1254 default shrunk | new |
| debug views | baked again (1254 dots masks and colours, 640 dots height and roughness) and the sheets rebuilt | new |
| `recipe/controls.md`, node counts | made again from the layer files (`recipe/make_controls_table.py`, `recipe/count_nodes.py`) | new |
| `final_report.json` | a new section "look fixes (round 15)"; the earlier numbers were kept | extended |
| guides | recipe guide: new section 6b, results tables with before columns, corrections from the honesty check; lessons guide: corrections and a new section 11 | updated |
| resolution, reuse (brick), control strips, links and order | not made again | before the look fixes |

Folder size: the re-baker left the folder at 454.0 MB (decimal; 432.9 MiB, which is what `du -h` prints); after the second honesty check and these corrections it is about 454.2 MB (433.2 MiB, counted as the sum of the file sizes, symbolic links as links). The limit for this round is 460 MB, so **the margin is only about 6 MB**: a person who bakes anything new here must delete its big pictures after measuring them. Pictures meant for looking are JPEG; the old ladder, variation, area and overview pictures that were overwritten are kept only as small JPEG copies named `..._before_look_fixes`.
