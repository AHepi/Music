# Slate in layers - folder map (read this first)

This folder holds the slate texture as ONE Blender recipe made of separate layers inside it: LAYOUT, COLOUR AND FADE, DAMAGE, MOSS, OUTLINE AND SHADOW
and COMBINE. Nothing in it is a picture of the reference: every dot is made by Blender nodes from a short list of settings (`recipe/settings.json`, 1.7 KB).
The reference picture was used only as a guide (looked at, measured once for its general character, never copied slate by slate).

The two guides to read are in this folder: `05 Recipe - slate in layers - how it is made.md` (what every layer and every Blender tool does, results tables,
dead ends) and `05 Lessons - slate in layers - what carries over to other surfaces.md` (how to split any surface into layers).

## Where things are

| folder / file | what is in it |
|---|---|
| `05 Recipe - slate in layers - how it is made.md`, `05 Lessons - slate in layers - what carries over to other surfaces.md` | the two guides |
| `final_report.json` | every number of the integration work in one file |
| `recipe/slate_recipe.py` | THE RECIPE: the file `lib/bake_harness.py` loads (`build_node_group(parameters)`); also the debug views and the half-tile shift |
| `recipe/settings.json` | the settings of the default tile (49 hand-tuned entries: numbers, colours and the stack order); everything not listed keeps the layer file's starting value |
| `recipe/controls.md` | ONE table of every control (176): layer, name, what it does, range, default |
| `layers/` | one file per layer: `layout.py`, `colour_and_fade.py`, `damage.py`, `moss.py`, `outline_and_shadow.py`, `combine.py`, and `layer_interface.py` (the fixed sockets) |
| `interface/interface.md` | the layout bundle (the eleven numbers every layer reads) and the rules of the layers |
| `outputs/default/` | the default tile baked at 1254 dots: `colour.png`, `height.png` (16 bit), `normal.png`, `roughness.png`, `metallic.png`, plus scores |
| `debug_views/` | every layer alone: its mask and its colour (1254 dots), its height and roughness change (640 dots), sheets |
| `tests/independence_full/` | the independence table and pictures (amount 0 and seed + 1 for every layer) |
| `tests/half_tile_layers/` | the half-tile shift test of the finished maps and of every layer on its own, for one tile and a 2 x 2 area |
| `controls_sweeps/` | "what does this control do" strips for every layer (made by the layer builders at each layer's own starting values); `whole_recipe/` = five strips of the finished, tuned recipe |
| `links_and_order/` | the declared link (moss avoids damage) in colour (`links_sheet.jpg`) and in height (`link_height/link_measures.json`), the stack order, and the tone-blend height pictures (`tone_blend_sheet.jpg`) |
| `ladder/` | what each layer buys: layout and joints only, + colour and fade, + moss, + damage, and without the outline (`ladder_table.md`, `ladder_sheet.jpg`) |
| `variations/` | eight tiles from eight settings variations, as a contact sheet with the settings under each tile; `seed_spread/` = the default settings with three more sets of seeds |
| `area/` | a 2 x 2 (`area_2x2/`) and a 4 x 4 (`area_4x4/`, colour only) area of new, non-repeating content, with seam and repeat measures |
| `resolution/whole_recipe/` | the same settings at 512, 1254 and 2508 dots, with the time of each bake |
| `reuse/` | the unchanged colour, damage, moss and outline layers on a BRICK layout, and what had to change (`reuse_sheet.png`); `settings_round_2/` = one settings-only round on the brick |
| `integration/` | the tuning notes: the rounds, the measuring scripts, `CHANGES_TO_LAYER_FILES.md` (every edit made to a layer file); `takeover/` = what the second integrator did after the restart (chain scripts and logs, clean-up list, numbers, `make_final_report.py`) |
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
# the reference-style normal map from the baked height (3 x 3 Sobel, strength 7)
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
