# 56 Store helper for the wall on a plane - report

What this file is: the report, word for word, of the helper that made the new wall tool (bricks or stone blocks filling one flat plane) and switched the house-front tool to photographed stone (5 November 2026, 17:31 to 18:16). Saved by the session.

---

**Wall helper report.** I finished at 18:16 by this computer's clock; the deadline was 19:05.

## What I made

**1. A new wall tool, `lay_wall`.** It covers one flat plane with real bricks or stone blocks. The plane can be any size, standing facing any way or lying flat, with its scale and turn left unapplied.
```
import lay_wall
lay_wall.lay(my_plane, kind='brick', bond='flemish', seed=2)
lay_wall.lay(my_plane, kind='stone', seed=5)
```
- **Courses:** they run level. When the plane lies flat they run along the plane's own X. They come out whole from bottom to top, and the bricks or blocks stop half a joint from every edge.
- **Bricks:** real size (215 x 102.5 x 65 mm, 10 mm joints). Bonds: stretcher, English, Flemish and header. The bond is kept at both edges with half bricks and closers. The cut bricks go near the middle of the wall, where bricklayers put them, and each course places its cuts so they overlap the joints of the course below.
- **Stone:** coursed blocks with heights and lengths varied, 5 mm joints, and corners now and then knocked off like lay_stone's blocks.
- **Wear:** every brick or block sits a few millimetres in or out, is tipped a hair, and has worn edges.
- **Photographed look:**
  - Each brick or block shows one whole photographed brick or block from the store's atlas (UV map `pp_atlas`). The seed picks which one, and it is sometimes turned half round; its sides show thin strips from that brick's edges.
  - Every brick or block carries its own `pp_piece` number.
  - The defaults are the materials helper's `BRICK • brick_wall_02`, `ASHLAR • sandstone_blocks_05` and `SURFACE • rough_plasterbrick_05` for the mortar. The plane itself becomes the mortar.
  - My own stand-in rectangles were needed only for the first ten minutes. They stay in the tool as a fallback in case the atlas files go missing.
- **Other outlines:** a gable's triangle cuts the units along its slopes. A hole in the plane, such as a window left out of the mesh, stays open. An L-shaped plane works.
- **Other options:**
  - `atlas`: for example `'brick_wall_10'`.
  - `material` and `mortar_material`.
  - `course`: stone course height.
  - `relief`, `wear`.
  - `flip`: lays the units on the other side of the plane.
- Wrong options are refused, and the tool answers `--help`.

**2. `lay_stone` switched to the photographed stone.** Its blocks and dressings now default to `SURFACE • worn_rock_natural_01`, the projected ashlar named in `Photographed.md`. Each block and dressing carries its own `pp_piece`. The old painted stone still works by name: `shades=lay_stone.SHADES, trim_material=lay_stone.TRIM_MATERIAL`. With the old materials, the blocks land exactly where they did before. All the existing lay_stone tests pass without changes; none checked material names.

**3. Tests: `tests/test_store_wall.py`, 27 PASS lines.** They cover:
- planes from 1 x 1 m to 12 x 6 m, facing +X, -X, +Y and -Y, lying flat, and turned within themselves, all with scale and turn unapplied;
- every unit inside the outline, the courses within a joint of every edge, and whole courses;
- the bonds:
  - stretcher joints halfway along the brick above;
  - Flemish headers centred on the stretcher below;
  - English courses alternating;
  - both edges matching;
- real brick sizes, and the relief within limits;
- the gable, the hole, and both kinds;
- `pp_piece` on every unit, and `pp_atlas` inside one atlas rectangle;
- the same seed giving the same wall, wrong options refused, and `--help`.

`test_store_tools`, `test_store_street_fronts` and `test_store_materials` pass. `test_store_rules` passes except its catalogue check, which is expected until you run `catalogue.py`. The whole suite shows only that one failure.

**4. Cards.** `lay_wall` shows a Flemish brick wall beside a stone wall turned towards the eye. The `lay_stone` card is redrawn in the photographed sandstone. I looked at both at full size.

## What does not read well yet
- **Holes:** over and under a window hole, and under a step in an outline, a brick piece thinner than 2 cm (4 cm for stone) is left out. Up to 3 cm of mortar shows there; a lintel or sill would cover it.
- **Corners:** where two planes meet at a building's corner, the bricks do not wrap round it. Each plane's bricks stop at its own edge.
- **Long stone blocks:** stone blocks longer than the atlas's photographed blocks show the photograph enlarged, up to about 1.8 times.
- **lay_stone's dressings:** they are now the same sandstone as its walling. They stand apart from the walling only by their relief and joints, not by colour.
- **Wrong side:** if the plane's face looks the wrong way, the units come out behind it. `flip=True` fixes this, and the tool's trap line says so.
- **Cards may go stale:** the cards show the materials as they were at 18:15. If the materials helper changes them, redraw with `python3 /home/claude/store-work/pbr56/wall/scripts/cards.py -- lay_wall OUT.png 24` (or `lay_stone`).

## Mistakes I made and how I fixed them
- **Stone looked like pillows:** the first stone blocks had corner chips too big for their 2 cm relief. I made the chips small, with only now and then a big one.
- **Gable built on the back:** in one of my test pictures I made the gable's face look the wrong way, so the bricks stood behind it. I fixed my script, then added `flip`.
- **Header bond end gap:** header bond left an 11 mm end joint where a joint fell across the edge. The last brick now reaches the edge.
- **Shared `pp_piece`:** two of 5,760 bricks got the same `pp_piece`, because Blender stores the number with less precision and repeats happen on big walls. Each unit now gets its own number, spread evenly over 0 to 1 and shuffled.
- **Missing course under a window:** a window's foot lying exactly on a course line was misread by a tiny rounding error, and a whole course under the window went missing. Corners that close to a course line now count as on it.
- **Wrong test check:** my first lay_stone `pp_piece` check grouped faces wrongly and failed when nothing was wrong. It now checks that each block's faces share one number.
- **Seam in the middle:** the cut bricks first stacked into a straight seam in the middle of the wall. Each course now picks where its cuts go.

## Files
Created:
- `/home/claude/music/plugins/painted-place/brief/store/tools/lay_wall.py`
- `/home/claude/music/plugins/painted-place/tests/test_store_wall.py`
- `/home/claude/music/plugins/painted-place/brief/store/cards/tools/lay_wall.png`

Changed:
- `/home/claude/music/plugins/painted-place/brief/store/tools/lay_stone.py`
- `/home/claude/music/plugins/painted-place/brief/store/cards/tools/lay_stone.png`

My scratch folder `/home/claude/store-work/pbr56/wall/` holds `notes.md`, the scripts that drew the pictures and cards, every picture, and copies of the earlier versions.

## For the session
- `tests/run_tests.sh` does not list `tests/test_store_wall.py`. I was not allowed to edit the runner, so please add it.
- Then run `catalogue.py`.

---

## Traps

- This is the helper's own account. What the session checked afterwards is in the project story, log 56.
