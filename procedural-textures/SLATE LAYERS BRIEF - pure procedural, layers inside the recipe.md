# Slate in layers - the brief (read after PROCEDURAL_NOTES.md; where they disagree THIS FILE wins)

## What the person asked for
After seeing the first slate build (a fitted description reproducing the reference "close"): "The match is close enough. For the full procedural effect, the agent will need to keep
the colour and fading, the damage and the moss patterns on separate layers. ... Start with slate. They should be inside the recipe. Don't fit from my picture, it should be used only as a guide."

## What changes compared with the first build
1. NO FITTING. The reference is a GUIDE: look at it, measure its general character once (palette of up to 12 colours, how big the patches are, how wide the outlines are,
   what share of the surface is moss/damage, how the fade runs) and use those measurements to choose the DEFAULT SETTINGS of your layers. You must NOT copy the position, size,
   shape or colour of any individual slate or patch from the picture, must NOT trace anything, must NOT store per-element lists, and must NOT run an automatic optimiser over many
   settings to minimise a difference from the picture. Hand-tuning is the method: look, change a setting, look again. A small sweep of one or two settings against a score is fine
   to show what a setting does. The recipe's whole description is a short list of SETTINGS (tens of numbers, not hundreds, not lists of pieces): a Python dict, saved as
   settings.json (about 2 KB). `python3 -I lib/description_audit.py recipe/settings.json --limit-kilobytes 8` must pass.
2. LAYERS INSIDE THE RECIPE. One Blender recipe (a node group made by Python, for bake_harness: build_node_group(parameters), input 'Vector' = tile coordinate, outputs
   'Colour','Roughness','Metallic','Height') made of separate named sub-groups that you can see and switch off one by one in the Shader editor: 
     LAYOUT      -> the slates: rows, widths, joints, ragged edges; outputs the "layout bundle" below (and a base relief)
     COLOUR AND FADE -> each slate's base tone from a palette, per-slate variation, and the fading/streaking (weathering that runs down the slate, sun-bleached or darkened areas)
     DAMAGE      -> chips and worn edges, corner breaks, cracks, scratches, the pale lichen-tan breaks where slate has flaked
     MOSS        -> moss and lichen growth: where it gathers (drips below upper edges, along joints and in low spots, near damage), flat painted clumps, olive family + tan lichens
     OUTLINE AND SHADOW -> the dark joints, the shadow band under each slate, the bright lip
     COMBINE     -> stacks the layers in order, adds each layer's height to the base relief, makes roughness and metallic, outputs the four maps
   Each layer has its OWN controls (group inputs: amount, scale, seed, plus a few meaningful settings), its OWN random seed, its OWN mask, and writes its OWN colour, height and
   roughness. Layers are connected only through the layout bundle and through DECLARED links (for example "moss avoids fresh damage" - say so in the settings file and the guide).
   The layers are NOT separate picture files; they are separate parts inside the recipe. For the guide, make "debug views" (bake any layer's mask or colour alone through the harness) and
   show them as pictures.
3. THE LAYOUT BUNDLE (the interface every layer reads; build it once, test it, do not change it after the layers exist): outputs of the LAYOUT group:
     piece_id (float 0..1, same for all dots of one slate, random per slate), row (float, row number / rows), local_x, local_y (0..1 across and down the slate; 0,0 = top-left),
     piece_width, piece_height (in tile units), edge_distance (distance from the nearest slate edge, in tile units, 0 at the edge), top_edge_distance (distance below the slate's
     upper edge), gap_mask (1 in the black joint between slates), piece_mask (1 on slate), base_height (relief of the slates before any layer).
   Any other surface that can produce the same bundle can use the same DAMAGE, MOSS and COLOUR AND FADE layers - that is the reuse claim, and you must test it (see 8).
4. INDEPENDENCE. Prove it: bake the recipe with one layer switched off (amount 0) or one layer's seed changed, and show that ONLY that layer's contribution changed (difference
   outside that layer's mask is zero, except for the declared links - list them). Do this for every layer and show a table. Changing MOSS seed must give a new moss pattern and the
   same slates, damage and fade; changing LAYOUT seed changes the slates (and what depends on them), etc.
5. SIZES IN TILE UNITS: every width, scale and radius is a share of the tile, so the recipe gives the same look at 512, 1254 and 2508 dots. Tiling: the recipe repeats exactly
   (use the 4D tileable noise groups in lib/recipe_tools.py, whole-number layouts; prove with the half-tile-shift test). A setting `tiles_across` (1, 2, 4...) makes a bigger area of
   NEW, non-repeating content with the same look per dot (the tile-count changes the period, bake N x 1254 dots).
6. THE LOOK TARGET: the slate reference (reference/slate/colour.png, normal.png, height_as_uploaded.png) and the measured look spec (research guide "02 Research - getting a
   hand-painted stylised look.md", section 2, and recipes/slate/analysis/ findings from the first build: 8 rows of 6 slates, row body 146 dots + 10.6 dot black band, slate width median
   200 dots (log-normal), joints ~3.9 dots, 7% joint black, palette of blue-greys 23-102 brightness, olive mosses 42-74, tan lichens 87-107, black joints; outline core 10 dots + 21 dot band + lip).
   Use these as guides. The first build's generator is in recipes/slate/generator/ and its lessons in recipes/slate/"04 Lessons ...md": READ them (what worked, and its weakness: new tiles looked
   blocky and camouflage-like instead of flowing painted streaks and moss in drips). You may reuse code ideas; do not reuse anything that came from fitting the picture
   (traced descriptions, per-slate colours, fitted stamp libraries).
7. MAPS: height = sum of the layers' heights + base relief (real relief from each layer: moss slightly raised and fuzzy, chips sunk, cracks sunk, joints sunk); normal = the slope of that
   height (strength 7 as in the reference maps; check the 8-bit rule in the notes) via the harness; roughness and metallic from the layers (moss rougher, damaged rougher, fresh slate smoother).
   Compare the combined result with the reference as a GUIDE using lib/texture_compare.py ("same kind" score: aim for 0.8+ on the colour group and a look a person would accept as the same
   material) and by eye in side-by-side sheets. Report lib/pixel_compare.py numbers for transparency only; they are NOT a target now.
8. DELIVERABLES (in recipes/slate_layers/): recipe/ (the Python recipe, settings.json, a one-page "controls" table: every control, what it does, range, default), layers/ (one file per layer),
   outputs/ (baked default tile: colour, height 16-bit, normal, roughness, metallic), debug_views/ (each layer alone), tests/ (independence table + pictures, half-tile test, 2 x 2 look),
   controls_sweeps/ (for each layer, 2-3 strips showing what its main controls do), variations/ (8 tiles from 8 settings variations, e.g. seeds and sensible control changes: "more moss",
   "heavily damaged", "faded and sun-bleached", "fresh slate"), area/ (2 x 2 unique), resolution/ (512, 1254, 2508), reuse/ (the DAMAGE and MOSS layers on another surface's layout, e.g. a
   quick brick layout: show what you had to change), plus two plain-language guides: "05 Recipe - slate in layers - how it is made.md" (every Blender tool used: one plain sentence on what
   it is, which settings matter, what changing each does, with sweep pictures; the layer interface; the declared links; results tables; dead ends) and
   "05 Lessons - slate in layers - what carries over to other surfaces.md" (how to split any surface into layers, in order; what to measure first; traps; what is specific to slate).
9. HOUSE RULES as in the notes: plain Blender only (no film plugin, no Astra add-on), -t 2 renders, no git, do not edit lib/ or reference/, plain-word names and a plain note at the top of every
   file, plain language for the person (not a programmer), say what you tested and did not, record failures. Disk is tight: keep recipes/slate_layers/ under 400 MB.
