You are the wall helper. Your scratch folder is `/home/claude/store-work/pbr56/wall/`. Your clock: finish by 19:05 by this computer's clock.

1. **A new tool, `brief/store/tools/lay_wall.py`:** `lay_wall.lay(plane, kind='brick' or 'stone', ...)`.
   - **What it covers.** One flat plane object you name: a mesh with one flat face, of any size, standing facing any direction or lying flat. Unapplied object scale and rotation are fine. It covers that plane with real bricks or stone blocks, standing out a little over a mortar back.
   - **Courses.** The courses run level: horizontal in the world when the plane stands up, along the plane's own X when it lies flat.
   - **Fitted to the plane.**
     - Whole courses from bottom to top: each course's height is adjusted a little so they come out whole.
     - The bond is kept to the edges with half bricks or closers, and blocks are cut to the edges.
     - Nothing goes outside the plane's outline.
   - **Bricks.** Real size: 215 x 102.5 x 65 mm, with 10 mm joints. The bond is a choice: at least stretcher, English and Flemish.
   - **Stone.** Dressed ashlar blocks in courses, with heights and lengths varied, thin joints, and arrises chipped like lay_stone's blocks.
   - **Wear.** Each unit is a little off true: set in or out a few millimetres, tipped a hair. Its edges are worn, and it has its own shade.
   - **Mortar.** The mortar back is the plane itself (or a copy of it), recessed behind the faces.
   - **Other outlines.** If the plane is not a rectangle (a gable's triangle), cut the units along its outline, if there is time.
2. **Photographed.**
   - Map every unit's front face into one whole photographed brick or block (the agreement's atlas): UV map `pp_atlas`, into a rectangle from `brief/store/materials/atlas/<set>.json`. Which rectangle is picked by the seed, sometimes turned half round. Map its sides into thin strips at that rectangle's edges.
   - Put `pp_piece` on every unit, and the mortar in the mortar material.
   - Until the materials helper's atlas files exist, work with your own stand-in rectangles for a shelf brick set (for example, measure a few bricks by hand in `brief/surfaces/brick_wall_02/`), so the tool works.
   - Switch to the real atlas files when they appear: check `brief/store/materials/Photographed.md` every so often. If they have not appeared by your last 25 minutes, finish with your stand-in and say so.
3. **lay_stone, the house-front tool.**
   - Switch its blocks and dressings to the photographed stone named in Photographed.md (the atlas, or the projected ashlar material), with `pp_piece` per block.
   - The old painted materials stay usable through its `shades` and `trim_material` options.
   - Its existing tests must keep passing. If one checks default material names, update only that expectation, and say so.
4. **Tests,** in `tests/test_store_wall.py`:
   - The wall covers the plane exactly: every unit inside the outline, the courses reaching within a joint of every edge, whole courses from bottom to top. Check this for planes from 1 x 1 m to 12 x 6 m; facing +X, -X, +Y and -Y; lying flat; and with unapplied scale and rotation.
   - The bond is kept. Stretcher: one course's joints sit halfway along the bricks of the next. Flemish: headers and stretchers alternate, each header centred on the stretcher below.
   - The bricks are real size, and the relief is within limits.
   - Both kinds work.
   - Every unit has `pp_piece`, and its `pp_atlas` lies inside one of its set's rectangles.
   - The same seed gives the same wall; wrong options are refused; `--help` answers.
   - Run `tests/test_store_tools.py` and `tests/test_store_rules.py` too, and any test that exercises lay_stone.
5. **Cards:** `lay_wall` (a brick wall and a stone wall side by side, one plane turned), and `lay_stone` redrawn.
