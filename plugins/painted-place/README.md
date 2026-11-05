# Painted place

What this is: a small Claude plugin for building a place in Blender for the series' painted look, the way the owner approved on 3 November 2026. Version 0.7.0, 4 November 2026.

How a place is built now: one fresh builder gets the **brief kit** (`brief/`) and the owner's plain request, decides everything about the place itself (what is in it, where every thing goes, how it is lit), and the owner judges the picture. The kit carries the look; the builder's judgment does the rest. The skill `skills/make-a-painted-place/SKILL.md` says how to run it.

## What is in it

| Thing | Where | What it is |
|---|---|---|
| The brief kit | `brief/` | The words a builder gets (`Brief.md`), the look in words and numbers (`The look.md`) and in pictures (`reference/`), what went wrong for builders before (`Traps.md`), a measure tool (`measure.py`), what to do before building (`Before you build.md`), boards of real photographs per kind of place (`boards/`), a shelf of 26 photographed surfaces (`surfaces/`), the brief for a second builder that dresses a finished place (`Second pass.md`); see `brief/README.md` |
| The store | `brief/store/` | Ready parts (things to place), tools (code that makes a thing from a line, a point or an object the builder gives) and ready materials, with a card picture of each; nothing in it places itself. Since 0.8 it has farm things (a plank door, hay, a dry-stone wall along any curve, a hedge, rough stone walls, moss). Since 0.7 it has ground tools: a ground with its wetness and water, ruts (a horse and cart, a car, a lorry, a tractor), paths, footprints and potholes, stones, grass, leaves and twigs, with two worked examples in `brief/store/examples/`. Catalogue: `brief/store/Store.md` |
| The skill | `skills/make-a-painted-place/SKILL.md` | How to run a build: the board, the copy, the words, one fresh builder, its report, the owner's judgment |
| The tests | `tests/run_tests.sh` | The measure tool on the reference pictures; every material, part and tool in the store; the store's rule that nothing places itself; the catalogue up to date. Fails if any test fails |
| Records | `examples/` | Pictures and notes from the plugin's earlier versions (0.2 to 0.5), kept as a record; the code they used is retired (below) |

## Install

```
/plugin marketplace add AHepi/Music
/plugin install painted-place@ahepi-music
```

Needs Blender 5.1 or later, or the `bpy` Python module (`pip install bpy==5.1.2`), plus Python with Pillow, numpy, scipy and OpenCV for the measure and the optional finish. With only the `bpy` module, run each script as `python3 SCRIPT ARGS`.

## Try it

```
cd plugins/painted-place
sh tests/run_tests.sh                                        # every test; fails if one fails
python3 brief/store/tools/store.py --list                    # what the store holds
python3 brief/store/tools/lay_walkway.py --points "0,0,0 0.5,6,0 2,12,0.3" --out /tmp/walkway.blend
python3 brief/store/tools/card.py part bell_tent --out /tmp/cards      # a part's pictures, kept out of the store
python3 brief/measure.py brief/reference/"painting - rainy tenement street at dusk.jpg"
```

Keep your own files out of `brief/`: a builder gets a copy of it, and what is written there goes to every builder.

## What 0.7 added

The ground tools (plan 53 and the owner's decisions 71 and 72): `ground` (the sheet a place stands on, a road's camber, its wetness by height, water as sheets cut from the ground itself, rain rings), `tracks` (ruts carved along a line for a horse and cart with its hoof prints, a car, a lorry or a tractor whose tread ridges hold water; a trodden path; footprints; potholes; one age dial), `stones` (rocks, pebbles and grit), `grass` (turf, tussocks, tall weeds, kept out of ruts and water) and `litter` (fallen leaves and twigs); soil, pebble, grass and leaf materials; two worked examples, a cart track after rain and deep motor ruts in a wet field; their tests in `tests/test_store_ground.py`.

## What 0.8 added

What the barn on a farm's two builders made for themselves (log 54, decision 74), pulled into the store, and more:
eight parts (`plank_door` with strap hinges that swings open, `ladder`, `fork` as a pitch fork or a root fork with a D
handle, `skep` the woven willow basket, `mangold_heap`, `hay` stacked in a bay or heaped, `bare_tree`, `corrugated_sheet`);
tools: `dry_wall` (a dry-stone wall along any line or curve, with gateways; decision 77), `hedge` (a ragged hedge along a
line or curve), `lay_rubble` (rough stone on a wall with its doors and windows and a sloping top), `moss` (moss on the faces
of a material that look up), `clear_under` (takes scattered grass, stones and litter from under anything set down), straw
in `litter`, a hollow building in `lay_boards` so an open door shows the inside; `MADE • straw` and `MADE • hedge leaves`;
a photographed sunny sky whose sun casts the shadows (decision 76, the barn by day); every shelf surface now uses its whole
photographed set, normal picture included; a board of real barn and farmyard photographs; the builders' traps. Tests in
`tests/test_store_farm_tools.py` and the parts test.

## What 0.9 added

What the town street's three builders made for themselves (log 55, decision 79), pulled into the store: fourteen parts
(`shop_front` with a real shop behind its glass, `dormer`, `window_dressing` as blinds, nets or curtains, `boarded_window`,
`window_box` of geraniums, `sign_board` on a forged bracket, `stair_door` lit from the stair, `ash_bin`, `drain` as a cover
or a grate, `sett_stack`, `newspaper`, `chimney_stack`, `sack_barrow`, `coster_barrow`); tools: `lay_kerb` (kerbstones
along any line or curve, with channel stones), `joint_weeds` (grass and weeds in the joints, out of the wheel lines),
`lay_eaves` (a slate roof with its overhang, eaves boards, rafter ends and gutters), `downpipe` (from a gutter outlet to
the ground, with its leak stains), `weathering` (weathered copies of stone and paint); wear for the setts in `lay_cobbles`
(shades, two quarries, rocked and missing setts, a relaid patch, grit and moss in the joints), a distance, taper and
unevenness for the stains and four heavy stains that show far down a street; a third builder for the building fronts when
the owner asks for the most detail (`brief/Third pass.md`); a board of real town street photographs; the builders' traps.
Tests in `tests/test_store_street_ground.py`, `tests/test_store_street_fronts.py` and the parts test.

## What was retired, and why

Until version 0.5 the plugin built the look itself: a **dressing** (`materials/apply_by_role.py` and the `lay_*.py` files) gave every object a material by the words in its name and laid details where its own survey of the camera's view said they belonged; a **look stage** (`stage/`) lit and drew the place; a **blind judge** (`look/judge.py`, `agents/blind-judge.md`) said what to fix. The owner judged a builder given only pictures and a page against builders using the dressing, and the pictures-only builders' places were better ("Pictures only is better"): the dressing's placement logic was faulty and its objects did not make sense (decision 62). The owner then asked to keep the good parts as things to pick from: the footpath as a tool on a line, the detailed things builders had made as parts, the textures as "pick and choose" shaders (decision 65). So in 0.6:

- the brief kit moved into the plugin as `brief/`, so an install carries it;
- the good code of the dressing became the store's tools (setts and flags, lapped boards with new eaves, stonework, puddles, stone grain), working only where the builder says;
- what the test builders of log 51 had to make for themselves joined the store: a dusk sky with a box of haze, a ribbon of smoke, rail steel; the street's 45 materials, the old brass, copper and china, and the photographed timber, bark and sand joined the store's materials;
- the things builders made in their own scripts (logs 44, 46 and 50) became the store's parts, rebuilt to read from every side;
- the dressing, the look stage, the blind judge, the role list and their tests were deleted from the plugin; they stay in the repository's history (the last commit with them is the one before 0.6.0's), and decision 57 retired blind judges.

## Traps

- The store's parts and tools find the shelf and the materials by their place inside `brief/`; copy the whole folder, never the store alone.
- Every helper also reads the repository's rules file and the owner's saved preferences; keep technique out of both, or a test of the kit is spoiled.
- `examples/` shows the retired dressing at work; its commands no longer run in 0.6.
