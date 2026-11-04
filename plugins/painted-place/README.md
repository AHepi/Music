# Painted place

What this is: a small Claude plugin for building a place in Blender for the series' painted look, the way the owner approved on 3 November 2026. Version 0.6.0, 4 November 2026.

How a place is built now: one fresh builder gets the **brief kit** (`brief/`) and the owner's plain request, decides everything about the place itself (what is in it, where every thing goes, how it is lit), and the owner judges the picture. The kit carries the look; the builder's judgment does the rest. The skill `skills/make-a-painted-place/SKILL.md` says how to run it.

## What is in it

| Thing | Where | What it is |
|---|---|---|
| The brief kit | `brief/` | The words a builder gets (`Brief.md`), the look in words and numbers (`The look.md`) and in pictures (`reference/`), what went wrong for builders before (`Traps.md`), a measure tool (`measure.py`), what to do before building (`Before you build.md`), boards of real photographs per kind of place (`boards/`), a shelf of 23 photographed surfaces (`surfaces/`), the brief for a second builder that dresses a finished place (`Second pass.md`); see `brief/README.md` |
| The store | `brief/store/` | Ready parts (things to place), tools (code that makes a thing from a line, a point or an object the builder gives) and ready materials, with a card picture of each; nothing in it places itself. Catalogue: `brief/store/Store.md` |
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
