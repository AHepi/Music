# Slate in layers - folder map and what the skeleton proved

This folder holds the pure-procedural slate recipe made of separate layers inside one Blender recipe. This note is for the people building the layers.
The skeleton (LAYOUT + four placeholder layers + COMBINE + the recipe entry point + the tests) is finished and bakes; the real COLOUR AND FADE, DAMAGE, MOSS and
OUTLINE AND SHADOW replace the placeholders, each by editing only its own file in `layers/`.

## Where things are

| path | what is in it |
|---|---|
| `interface/interface.md` | the fixed socket names and rules (READ FIRST) |
| `layers/layer_interface.py` | builds the empty layer box with the fixed sockets; `LayerBuilder` (write nodes like sums); `Control`, `resolve` |
| `layers/layout.py` | LAYOUT (finished): rows, widths, joints, chipped rounded edges, the eleven bundle numbers |
| `layers/colour_and_fade.py`, `damage.py`, `moss.py`, `outline_and_shadow.py` | PLACEHOLDERS: edit your own file only |
| `layers/combine.py` | COMBINE: stacks colour, sums height and roughness, makes the four maps |
| `recipe/slate_recipe.py` | the recipe the harness loads (`build_node_group(parameters)`); debug views; the half-tile shift |
| `recipe/settings.json` | the settings a person has chosen (only `recipe.*` for now); the full list is `recipe/controls.md` |
| `recipe/make_controls_table.py`, `recipe/controls.md` | writes / holds the one-page controls table (run again when CONTROLS change) |
| `outputs/skeleton/` | the skeleton baked at 1254 with the harness (colour, height 16-bit, normal, roughness, metallic) |
| `debug_views/` | `bundle_sheet.png` (the eleven bundle numbers as pictures), `skeleton_layers_sheet.png` + `skeleton_layers/` (every layer alone) |
| `tests/` | the tests and their results (see below) |

## Tests run on the skeleton (all with Blender 5.2.2, 2 threads, CPU Cycles)

| test | script | result |
|---|---|---|
| bakes from day one at 1254 with the harness (`--normal-reference slate`) | `lib/bake_harness.py` | 78 to 93 s for all maps (colour about 10 to 13 s, height 11 to 16 s, roughness 14 s, the harness's Bump-node normal 36 to 50 s) |
| the layout bundle as pictures | `tests/run_bundle_pictures.sh` -> `tests/bundle_sheet.png` | all eleven numbers look as documented |
| exact tiling (half-tile shift), one tile | `tests/half_tile_test.py` | colour: mean difference 0.62 of 255, 0.001 percent of dots over 40 (a wrong roll: 8.3 and 8.3 percent). Layout numbers that are smooth (edge_distance, base_height): 0.0 percent over 40 |
| exact tiling, `recipe.tiles_across` = 2 | same | colour 0.90 and 0.019 percent; and the 2 x 2 area is NOT a copy of one tile (picture against itself rolled by one base tile: mean difference 17.0, a repeat would be near 0.9) |
| 2 x 2 look | `tests/make_comparison_sheets.py` -> `tests/comparison/two_by_two.png` | no visible seam |
| layout character against the reference guide | `tests/layout_statistics.py` -> `tests/layout_stats/layout_statistics.md` | 48 slates; width median 206 dots (reference 200), log spread 0.22 (0.217); row body 150 +- 5.8 (146 +- 6.4); joint 7.55 percent of dots (7.0); band between rows 9.5 dots (8.8 to 10.6); joint between slates 3.1 (3.9) |
| independence on the skeleton | `tests/independence_test.py` -> `tests/independence/independence_table.md` | changing a layer's Amount or Seed changes nothing outside that layer's own mask (0.0 percent in every row); placeholders damage and moss are empty so they change nothing; layout seed changes slates and everything that reads them |
| timing | `tests/time_it.py` -> `tests/timing.json` | colour 13 s and height 16 s at 1254; 92 s and 87 s at 2508 dots (2 x 2 area); node count of LAYOUT 307 (457 for 2 x 2), the other boxes 9 to 14 each |

Not tested: the real layers (they do not exist yet); the reuse claim on another surface's layout (needs a second layout module that outputs the same eleven names);
EEVEE/GPU; baking at 2508 with the full harness (only colour and height were timed); the resolution check at 512 and 2508 of the look (the layout is in tile units by construction
and the half-tile test ran at 512, but a side-by-side look at 512, 1254, 2508 was not made).
