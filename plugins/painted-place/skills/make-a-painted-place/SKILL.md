---
name: make-a-painted-place
description: Build any place (a street, a yard, a camp, a mine, a chapel, an interior) in Blender for the series' painted look, the way the owner approved - one fresh builder gets the brief kit (the look page and its reference pictures, the traps, a measure tool, a board of real photographs of that kind of place, a shelf of photographed surfaces, and a store of ready parts, tools and materials it may pick from) with the owner's plain request, decides everything about the place itself, and the owner judges the picture. Use whenever a place is to be built or drawn for the series.
---

# Make a painted place

What this is: how a place is built for the series since decision 62 (3 November 2026). Not by code that dresses a scene: one fresh builder is given the brief kit in `${CLAUDE_PLUGIN_ROOT}/brief/` and the owner's request, word for word. The kit carries the look; the builder decides where every thing goes; the owner judges the picture. Read `${CLAUDE_PLUGIN_ROOT}/brief/README.md` and `${CLAUDE_PLUGIN_ROOT}/brief/Brief.md` before starting.

## Steps

1. **The board.** Look for `brief/boards/<the request>/` (a camp: `military base`; there are also `railway goods yard`, `chapel`, `barn on a farm`, `town street` and `japanese garden`). If there is none, make one first: ten to twelve public-domain photographs of that kind of place, each named `NN Short title, place, year (collection).jpg`, with a `Board.md` (each photograph and what to look at in it: what things are made of, how they are built, how they have aged and been used) and a `sources.json` (file, picture, collection, rights), as in `boards/military base/`. The Library of Congress picture search answers this machine (`https://www.loc.gov/photos/?q=...&fo=json`); Wikimedia Commons refuses it. Keep only pictures marked public domain or "no known restrictions".
2. **The copy.** Copy the whole `brief/` folder to a fresh folder the builder may read (the store travels inside it; never copy the store alone), leave out the three download scripts (`surfaces/fetch_surfaces.py`, `store/scans/fetch_scans.py`, `store/skies/fetch_skies.py`: a builder has no internet), and make an empty work folder beside it.
3. **The words.** Fill in the text in `Brief.md`: REQUEST (the owner's words, exactly), FOLDER, WORK and DEADLINE (100 minutes from the start, by the computer's clock).
4. **The builder.** Start one fresh builder (a new agent) with that text and nothing else: not the project's notes, not this skill, not your own reasoning, not the names of any techniques. One builder at a time on a 2-processor machine.
5. **Its report.** When it ends, save its report beside its picture yourself (a builder cannot write files whose names begin with REPORT). If a full-size picture is wanted, run its `render_final.py 1080 1920 64 OUT.png`.
6. **The owner judges**, against the reference pictures. No blind judges (decision 57). Send the picture beside the earlier pictures of the same place, if there are any.
7. **The second pass, always** (decision 68): a second fresh builder gets the first builder's script, picture and material list, the same kit, and 80 minutes to dress the place, above all the near ground (`brief/Second pass.md` says how). Its picture is the one the owner judges.
7a. **A third pass, when the owner asks for the most detail** (decision 79): a third fresh builder gets the second builder's script and picture and both material lists, the same kit, and 80 minutes for the buildings' faces and the middle distance (`brief/Third pass.md`). Its picture is the one the owner judges.
7b. **Closer to the owner's picture, when the owner asks** (decision 86): when the owner sent a picture with the request and asks for the place to come closer to it, one more fresh builder gets the last builder's script and pictures, every material list, a fresh copy of the kit at the same path, and 100 minutes to close the biggest differences first (`brief/Closer to the picture.md`). It may change the light, sky, layout and camera where the picture asks. Its picture is the one the owner judges.
8. **Feed the store:** whatever either builder made for itself that the store lacks (a thing, a tool, a material) is pulled into the store, checked from four sides, tested, and catalogued. Each place leaves the store bigger.

## The store

`brief/store/` holds ready parts (things to place: a bell tent, a field gun, a timber hut, a gas lamp...), tools (code that makes a thing from a line, a point or an object the builder gives: a duckboard walkway along a line, setts on a road or along any curve with its flags and kerbs, bricks or stone blocks filling any plane, a Japanese tiled roof, paper screens, a veranda, a slab path, a bamboo fence, lapped boards and eaves on a box, stonework on a wall, a puddle, stone grain, a dusk sky with a box of haze, a low golden sun with its clouds and the mist's own light, far hills that reach the height asked, a baked PBR stand-in for a detailed part, a ribbon of smoke, an optional finish) and ready materials (photographed stone and brick where each piece shows its own part of the photographs, the street's, the shelf's surfaces already darkened into the look, and a few made in code). Its catalogue is `brief/store/Store.md`. Nothing in it places itself; a builder may use it or not.

To add to the store (a new set that used a tool, part or material the store lacks; the rule in the repository's rules file):

- A part is one module in `store/parts/src/<name>.py` with a `CARD` and `build(collection, seed=0, **options)` that makes it at the origin: metres, foot at z = 0, front towards −Y. Check it from four sides (`python3 store/tools/card.py part <name> --views three,close,side,back`), then `store.save_part_file('<name>')`. In its `CARD`, write each option's default as `(default X)`, and in a choice option's text put only that option's own choices in single quotes: the parts test builds the part with every other quoted word, and reads an apostrophe as a quote mark (it tripped a helper in log 54 and again in log 55).
- A tool is one script in `store/tools/<name>.py` with a `TOOL` dict, importable functions that work only on what the caller passes, and `--help`.
- A material is added to `store/materials/src/` (`made.py` for code-made ones, `build_materials.py` for ones from the shelf's photographs); rebuild with `python3 store/materials/src/build_materials.py`, draw its card (`python3 store/tools/card.py material "<name>"`).
- Then `python3 store/tools/catalogue.py` (writes the catalogue into `Store.md` from the items' own descriptions) and the tests: `bash ${CLAUDE_PLUGIN_ROOT}/tests/run_tests.sh`, which fails if any test fails. A change is finished when the tests pass and a fresh checker (an agent that has not seen the work) has read it.

## What stays out

- No code that decides where things go: no survey of the camera's view that places litter, weeds, puddles or props, no rules by object names. A tool makes a thing where the builder says.
- No blind judge, and no image model repainting the picture, in this loop.
- `brief/The look.md` and `brief/reference/` change only when the owner says so. A picture the owner approves can join `reference/` with the owner's yes.

## Traps

- Every helper also reads the repository's rules file and the owner's saved preferences; keep both free of technique, or the test of the kit is spoiled.
- A builder stops early when the measure says "inside every band"; the brief says the bands are a floor, not the finish. If a builder still stops early, the fix goes into `brief/Traps.md`, not into the builder's request.
- The store's parts and tools find the shelf and the materials by their place inside the brief folder: a copy without `surfaces/` draws the surface materials pink.
- `import bpy` before `import bmesh` in every script run with the `bpy` module.
- A long drawing left running in the session's background is lost if the session restarts; one started as a detached process (`nohup ... &`) kept running through the restarts of logs 54 and 55. Either way, after any pause check that it is still running before saying it will arrive.
- When several helpers add parts at the same time, run the whole parts test after the last one finishes: it stops at the first part that fails (another helper's part with no part file yet), and the parts after it go unchecked.
