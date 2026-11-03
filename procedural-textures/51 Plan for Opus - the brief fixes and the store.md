# 51 Plan for Opus: the brief fixes and the store

What this file is: the plan a worker session (Opus) follows, written by the planning session (Fable) on 3 November 2026 after the owner judged the two-pass military base (log 50). The owner's words that set this plan: "It looks so much better. But it isn't there just yet. The water looks like a cutout mirror, the walk way is littered with items I can't identify. House to the left of the tower looks like cardboard. There are also a ton of things I would add if we are to keep the plugin: The footpath could be turned into a tool or modified that automatically generates on a spline: it has really great details. There a ton of detailed assets, already created, that can be turned into some kind of tool as well. There are a tone of textures that can be added as "pick and choose" shaders." Then: "can you create the plan for Opus to follow. Your the brains, Opus is the worker."

Read this whole file before doing anything. Then read, in this order: `austerity-explainer/project-notes/Decisions.md` (items 45 to 64 at least), `Procedural textures - project story.md` (logs 44 to 50), `49 Research - how environment artists make a place old, used and full.md`, and `place-brief/README.md`. Everything below assumes you have.

## The idea in three sentences

The way a place is built is the brief kit (`place-brief/`): a look page, reference pictures, a traps page, a measure tool, a board of real photographs, a shelf of surfaces, and a fresh builder with a clock. What failed before was a plugin that decided where things go (the dressing); what the research and the last test showed works is a builder that decides placement itself. So the plugin is kept, but turned into a **store**: parts, tools and ready materials a builder picks from and places itself, with no placement rules in it.

## Where things are

- Repository: `AHepi/Music`, branch `ccr-e7298c9b-n19qkt`, clone at `/home/claude/music` (sparse checkout; use `git add --sparse` for paths outside it). Latest commit at the time of writing: `fe7014d`.
- The kit: `place-brief/` (top level of the repository). Its `Brief.md` says how a place is built with it.
- The old plugin: `plugins/painted-place/` (version 0.5.0). Its dressing (`materials/apply_by_role.py` and the `lay_*.py` files), look stage (`stage/`), judge (`look/judge.py`) and skill loop are what is being retired; some of its code becomes tools (below).
- The builders' scripts, where the parts come from (each `render_final.py` builds a whole scene in code; the parts are functions inside):
  - `procedural-textures/46 Pictures-only builders - three places/46 townhouse - render_final.py` (brick terraces, gas lamps, a coal cart, cobbles laid one by one, puddles)
  - `.../46 desert-mine - render_final.py` (winding tower, engine house, ore cars on rails, a smoke ribbon, haze inside materials, a tone-and-grade finish)
  - `.../46 military-base - render_final.py` (field gun, bell tents, barrack huts, watch tower, sandbags, duckboards, barbed wire, rifle stack, telegraph poles)
  - `procedural-textures/50 Military base from the kit with board, shelf and material list/50 first pass - render_final.py` and `50 second pass - render_final.py` (duckboards with wear and nails, lanterns, tents, tower, a gun with mud and rust, the things people left)
  - `procedural-textures/44 Blind test - a tea house/44 control builder - render_final.py` (a tea room inside: urn, marble tables, bentwood chairs, trolley, a sunbeam through steamed glass)
  - `procedural-textures/44 Blind test - a tea house/44 plugin builder - build_tea_house.py` (a jettied half-timbered tea house, a teapot sign)
- The owner's records: `austerity-explainer/project-notes/Decisions.md`, `Lessons.md`, `Status.md`; the story `procedural-textures/Procedural textures - project story.md` (log entries are numbered and added to, never rewritten).

## Standing rules (from the owner; do not bend them)

- Plain everyday words to the owner; one word for each thing. In this plan: **kit** (the brief folder), **shelf** (photographed surfaces), **store** (parts, tools and ready materials), **part** (a thing to place), **tool** (code that makes a thing from a line or a shape the builder gives), **material** (a ready-to-apply Blender material; the owner also says "shader").
- Decision 45: a test build gets only the kit and the owner's plain request. Never name techniques in a builder's request or in the repository's rules file (`CLAUDE.md`), because every helper reads it.
- Decision 49: no login keys, tokens or machine ids in the repository; never put the owner's email or name into requests to outside websites.
- Decision 57: no blind judges. The owner judges finished pictures.
- Decision 62: the kit carries the look; no placement code is added anywhere.
- Authority documents stay frozen: `place-brief/The look.md` and `place-brief/reference/` change only when the owner says (a new reference picture joins only with the owner's approval).
- Every document gets a Traps section at the bottom. Lessons are failures only (a thing that broke and had to be fixed); Traps are operational.
- Every change to the plugin is checked by its tests and by a fresh checker (an agent that has not seen the work being made), before it is called finished.
- Record as you go: a numbered story log entry (the next is 51), a decision entry with the owner's exact words when the owner decides something, lessons for every failure, status at the end; a numbered folder `procedural-textures/51 ...` for what this plan produces; commit and push to the branch, ending each commit message with the attribution lines your own session gives you.
- Builders are fresh Sonnet agents, one at a time on the 2-processor machine, with a clock; they read nothing outside the folders they are given. Save their reports yourself (they cannot write files named REPORT).

## Step 1: fix the brief (about an hour)

Edit `place-brief/Traps.md`: add these lines, in the owner's sense, as traps (operational, one line each):

- Puddles drawn as flat glossy discs read as cutout mirrors. A puddle needs a ragged edge, a dark wet halo of ground round it, mud showing through at the shallow edge, and a faint ripple that breaks the reflection.
- Any thing in the picture that cannot be named at the final size is noise: take it out or make it bigger. Litter on a walkway is the usual case.
- A building drawn as a box with a plank picture on it reads as cardboard. It needs eaves with a roof overhang and its shadow, board relief or lapped boards, a door, a stove pipe or chimney, and corner boards.
- The measure tool's bands are a floor, not the finish: "inside every band" says the colour and light are not wrong; it says nothing about detail. (Three builders stopped early because of it: logs 48 and 50.)

Edit `place-brief/Brief.md` (the text builders get) so "finished" is spelled out: the clock ends the build; before the clock, finished means every surface in the material list is laid, every prop can be named at full size, puddles have edges, buildings have eaves, and nothing in the frame reads as a plain box. Keep the text short; it is read by a builder in a hurry.

Add one line to `place-brief/Brief.md` under "How a place is built": the store at `place-brief/store/` (step 2) is offered to the builder as a folder it may use; nothing in the store places itself.

## Step 2: build the store (most of a day; do it in batches and commit each)

Make `place-brief/store/` with three folders and one catalogue:

```
store/
  Store.md            the catalogue: one row per item, a card picture, one line of what it is, how to use it
  parts/              Blender files, one per part, real scale in metres, origin at the foot, +Y forward, named plainly
  tools/              Python scripts: give them a line or an object, get a thing back; every one answers --help
  materials/          one Blender file holding the ready materials, plus a card picture per material
  cards/              the card pictures (a 3/4 view and a close view for parts; a lit sphere and cube for materials)
```

**Batch A, the walkway tool** (the owner's first ask). `tools/lay_walkway.py`: input a curve object or a list of points in a JSON file, plus width (default 0.6 m), board length and gap, runner height, sag, wear amount, mud at the ends; output mesh objects (boards, runners, nails) following the line, each board its own tilt and shade, the middle worn paler, mud lumps only at the ends and only if asked. Take the boards' look from the 50 first- and second-pass scripts (the worn strip, the wet films, the nails with rust runs). Test: a straight line, a curve, a line that climbs a slope; render each from the builder's camera height and from the side; count that every board touches its runners.

**Batch B, tools from the old plugin's good parts.** These exist as functions; make each a tool that works on one object the builder names, with `--help`, and no survey or role words:
- `tools/lay_cobbles.py` from `plugins/painted-place/materials/lay_setts.py` (`lay_setts_on`, `lay_flags_on`): setts on a flat road object, flags on a flat pavement object. The owner called the street's setts great; keep them exactly.
- `tools/lay_boards.py` from `materials/lay_timber.py` (`lay_boards`, `lap_face`, and the eaves/casing logic in `lay_facade.py` `window_joinery`): lapped boards, casings, corner boards and nail lines on a plain timber wall the builder names; add eaves and a roof overhang option, because that is what the cardboard hut lacked.
- `tools/lay_stone.py` from `materials/lay_facade.py` (`build_face`): ashlar courses, jambs, lintels, sills and sashes on a plain stone wall.
- `tools/puddle.py` from `materials/lay_details.py` (`puddles`) and `materials/lay_shore.py` (`wet_ground`): a puddle film with a transparent shallow edge, a dark wet halo on the ground round it, a ripple; placed where the builder says (a point and a size), never by survey.
- `tools/stone_grain.py` from `materials/scans.py` (`add_stone_grain`): real stone grain over a stone material.
Keep `survey.py` only if a tool needs it; the camera survey must not place anything.

**Batch C, parts from the builders' scripts.** Pull each out as a function, run it into an empty scene, give it the shelf's surfaces where the script used code colours, save as `parts/<name>.blend`, render its two cards. First batch, in this order: bell tent (50 first pass), watch tower (50), field gun (46 military base and 50 second pass, with the mud and rust), hurricane lantern (50), gas lamp (46 townhouse), coal cart (46 townhouse), sandbag wall (46/50), barbed wire coil and fence (46/50), crate, barrel and shell box (50), winding tower and ore car (46 desert mine), brass tea urn and bentwood chair (44 control), teapot sign (44 plugin). Each part is checked by eye from the side and close up before it is accepted; a part that only reads from one angle is reworked or left out, and the catalogue says so.

**Batch D, ready materials.** `materials/Materials.blend`: the 23 shelf surfaces as Blender materials with box projection, real scale from `surfaces/manifest.json`, and the colour darkened into the look's range (`measure.py` on the card says whether); plus the made ones: old brass, old copper, glazed china (`plugins/painted-place/materials/brass_copper_china.py`), wet mud, the puddle film, weathered boards with peeling paint (`lay_timber.boards_material`), chimney smoke. Every material gets a card: a sphere and a cube under one amber light and blue fill. A builder appends a material by name; `Store.md` lists the names.

**Batch E, the finish.** The desert mine builder's tone-and-grade finish (orange never turns white, blue-black darks, warm bloom) and the 50 builder's finish are the two best; put one in `tools/finish.py` that takes a raw render and writes the finished picture, with dials, and say in `Store.md` that it is optional.

**The catalogue.** `Store.md`: for each item, the card, one line of what it is, the command or the file, the real size, where it came from (which builder, which log), and a one-line trap if it has one. No instruction anywhere about where to put things.

**The old plugin.** `plugins/painted-place/` becomes a thin plugin that points at the kit and the store: its skill says "build a place with the brief kit; the store is available"; its README says what was retired and why (decisions 62 and 65), and that the retired code stays in the repository's history. Delete the dressing, look stage, judge and the old tests from the plugin folder once their good parts are in the store; keep `look/The look.md`, `look/measure.py` and `look/reference/` only as copies of the kit's or, better, move the kit into the plugin as `plugins/painted-place/brief/` so an install carries it. Ask the owner before moving the kit (it changes paths everywhere); until then, leave it at `place-brief/`.

## Step 3: test it (about two hours of machine time)

The military base again, one fresh builder, the brief kit with the store, the usual clock (100 minutes), no blind judge, saved to `procedural-textures/51 .../`. Then, if time allows, a second place that was not used to build the store (a railway goods yard, or a chapel: ask the owner which). Send the owner the picture beside the folder-50 one and the pictures-only one. The owner judges.

## Step 4: checks and records

- Tests: `plugins/painted-place/tests/run_tests.sh` rewritten for the store: each tool runs on a small scene and makes what it says (count the boards, the setts, the puddle's faces); each part file opens and has its named objects at real scale; each material appends by name. The runner fails on a failing test (lesson 168).
- A fresh checker reads the store (not the builder's picture): wrong scales, parts that read from one angle only, tools that place things on their own, materials too bright for the look, documents that disagree with the code.
- Records: story log 51 (what was built, what the test showed, failures, not done); decision 65 with the owner's words above; lessons for every failure; status; `51 What is here.md` in the folder; commit and push.

## What not to do

- No placement rules: no survey that decides where litter, weeds, puddles or props go. A tool makes a thing where the builder says.
- No new techniques named in a builder's request. The builder gets the brief text and the folder.
- No blind judges. No image-model paint-over.
- Do not touch `The look.md` or `reference/` without the owner.
- Do not retire the old code before its good parts are in the store and tested.

## Time budget

Step 1 about an hour; step 2 batches A and B about three hours, C about four, D about two, E about one; step 3 two hours of machine time; step 4 two hours. If it does not all fit, stop after batches A, B and D, test, and report; C and E can follow.

## Traps

- The builders' scripts build everything in world coordinates for one camera; a part pulled out keeps that camera's bias (one side detailed, the back bare). Render the side and back cards before accepting it.
- The shelf's colour pictures are daylight-bright; a material that is not darkened will measure outside the warm band on its card.
- `import bpy` before `import bmesh` in every script run with the `bpy` module.
- A long drawing left running in the background is lost if the machine restarts; run finals one at a time in the foreground, or check they are still running before promising them.
- Wikimedia Commons refuses this machine's requests; the Library of Congress answers (`sources.json` in `boards/military base/` shows how the board was made).
- Sonnet builders stop early when the measure tool says "inside every band"; step 1's fix is for that, and the test in step 3 is also a test of the fix.
