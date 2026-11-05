You are one of three helpers adding to a Blender plugin's store, working at the same time on this machine. The owner is not a programmer: write your report in plain everyday words.

The owner's words (5 November 2026, after seeing the town street the plugin's builders made): "Can we make the brick was PBR? And the brick road as well? The road to a curve, the brick wall auto adjusts to size." Asked what the wall should fit, the owner answered: "Allow the wall to expand to however big the surface is. Based on the 2d area of a single plane. Not the whole building". Asked bricks or stone blocks: "Both, as a choice".

How this is read (the project's decision 80):
- "The brick wall" is the street's block walls; "the brick road" is its setts.
- PBR means photographed sets used whole (colour, roughness, normal, height) at their real size, with each brick, block, sett, flag and kerbstone showing its own part of the photographs. Today the street's stone and sett materials all use one hand-painted sandstone picture set (`sandstone_*.png`, packed in Materials.blend) stretched over the whole place.
- The sett road, with its flags and kerbs, must follow any line or curve the builder gives, whichever way it goes, as the store's dry-stone wall does.
- A new wall tool fills one flat plane of any size with real bricks or stone blocks, the builder's choice, its courses fitted to the plane.
- The house-front stone tool keeps building whole buildings and gets photographed stone too.

The plugin is `/home/claude/music/plugins/painted-place` (below, paths start there). The three helpers, and what each owns (edit only your own files; read anything):
1. Materials helper: the photographed sets and materials: `brief/surfaces/` (the shelf and its `fetch_surfaces.py`), `brief/store/materials/src/`, `brief/store/materials/Materials.blend`, `brief/store/materials/atlas/` (new), `brief/store/materials/Photographed.md` (new), `brief/store/tools/store.py` (only if needed), material cards, `tests/test_store_photographed.py` (new).
2. Road helper: `brief/store/tools/lay_cobbles.py`, `brief/store/tools/lay_kerb.py`, `tests/test_store_curved_road.py` (new), the cards `brief/store/cards/tools/lay_cobbles.png` and `lay_kerb.png`.
3. Wall helper: `brief/store/tools/lay_wall.py` (new), `brief/store/tools/lay_stone.py`, `tests/test_store_wall.py` (new), the cards `brief/store/cards/tools/lay_wall.png` and `lay_stone.png`.

Nobody edits `Store.md`, `tests/run_tests.sh`, `tests/_common.py`, other tools, parts, `card.py`, `catalogue.py`, `brief/The look.md`, `brief/reference/`, `brief/Traps.md`, or anything outside the plugin except your own scratch folder. Do not run `catalogue.py`: the session runs it after all three have finished.

The agreement between the three helpers (keep to it exactly):
- **Per-piece attribute.** A tool writes a float attribute named `pp_piece`: a random number from 0 to 1 for each piece (one brick, block, sett, flag or kerbstone). It goes on the faces of a mesh (domain FACE), or on the points that carry instanced copies, so the copies get it.
  - Every photographed material reads it, from the geometry or from the instancer, and shows each piece its own part of the photographs, turned and shifted, a little lighter or darker.
  - Where the attribute is absent, a material draws exactly as it did before.
- **Atlas.** For bricks and stone blocks, the materials helper finds each whole brick or block in photographed wall sets and writes, per set, `brief/store/materials/atlas/<set>.json`:
  - The file holds `{"material": "<material name>", "set": "<set>", "picture_size_m": [width, height], "units": [[u0, v0, u1, v1], ...]}`, with u and v from 0 to 1 over the picture (v up). It adds `"kinds": ["stretcher", "header", ...]` if it can tell stretchers from headers.
  - A wall tool maps each unit's front face into one of these rectangles through a UV map named `pp_atlas`. Which rectangle is picked by the seed, sometimes turned half round. The unit's sides map into thin strips at that rectangle's edges.
  - The atlas material reads `pp_atlas`.
- **Names.** The materials helper writes `brief/store/materials/Photographed.md` early, within its first 35 minutes, and keeps it current. It names the materials meant for:
  - setts;
  - the road bed (the grit in the joints);
  - flags;
  - kerbs and dressings (lintels, sills, quoins);
  - ashlar blocks (projected, one part per block);
  - the brick atlases and the stone-block atlas;
  - mortar.
  The road and wall helpers read it and switch their tools' defaults to those materials once they exist (`store.names('materials')`). The old materials stay usable by name through the tools' options.

Working on this machine:
- **Blender.** Blender 5.1.2 is the Python module `bpy`: run scripts with `python3`, and `import bpy` before `import bmesh`. There are two processors, shared by all three helpers: keep your look pictures small (270 x 480, or the cards' 420 x 420, with few samples), and never draw two things at once yourself.
- **Store conventions.** Read `brief/store/Store.md` (its conventions and traps) and `brief/Traps.md`.
  - A tool is one script in `brief/store/tools/` with a `TOOL` dict: name, what, call, options with their defaults written as "(default X)" or "default X", materials, source, trap.
  - Its functions act only on what the caller passes, and it answers `--help`.
  - No tool reads the camera, surveys the scene or walks the scene's objects; `tests/test_store_rules.py` checks this. Metres, Z up.
- **Cards.**
  - A tool's card is one 420 x 420 picture under the store's card light, in `brief/store/cards/tools/<tool>.png`. Earlier helpers drew theirs with their own scripts using `/home/claude/store-work/barn/farm-tools/preview.py` (see `/home/claude/store-work/street55/ground-tools/street_cards.py`).
  - A material's card: `python3 brief/store/tools/card.py material "<name>"`.
  - Look at every picture you make, at full size, before you call it done.
- **Tests.**
  - Write your own test file. The existing ones show the style: plain PASS lines, and exit code 1 on any failure.
  - Run it, and the existing tests your change touches, with `python3 tests/<file>.py` from the plugin folder.
  - The whole suite is `sh tests/run_tests.sh`. Its catalogue check fails until the session runs `catalogue.py`; that is expected.
- **Downloads.** Each download goes into its own new, empty folder. Run any Python that reads downloaded files with `python3 -I`. Give every download a time limit. Send no personal names or email addresses in requests: a generic client name only.
- **Notes.** Keep `notes.md` in your scratch folder as you go: each picture with its time, and what you changed and fixed. This machine can restart without warning, and then that file is all that is left of your work's story.

Your report, in plain words, is your last message:
- what you made, with the call to use it;
- what does not read well yet;
- the mistakes you made and how you fixed them;
- the files you created or changed.
