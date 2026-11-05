# The tools helper's report (barn additions to the store, 5 November 2026)

What this file is: the last message of the helper that turned the barn builders' tools into store tools, saved by the session.

All seven additions are in the store, tested, and have picture cards. The curve work passed on from the owner is done: the wall follows a curve object whichever way it goes. The new test file passes, as do the store's tools and ground tests. The one failure is the rules test's catalogue check, because `Store.md` is out of date (the catalogue was left to the session as agreed). Its rule check itself passed on all 64 files, so no new tool decides where things go or looks round the scene.

## The seven additions

1. **Dry-stone wall:** `dry_wall.lay(line, height=1.25, base=0.62, top=0.42, coping=0.26, gaps=[(from, to)], ground=yard, smooth=True, seed, material, shades, core_material)`. It returns the stones, the coping and the dark core.
   - The line can be a list of points, a curve object, a line mesh or a JSON file.
   - Heights come from the ground through `ground.height_at`, or from the line's own heights if no ground is given.
   - Fixed from the builder: the coping stones are chunky, leaning in runs and tightly packed, with a taller stone now and then (no picket fence). Stone outlines are broken, stone heights vary within a course with thin stones pinned in, through-stones show on both faces, gateways get finished ends, and each stone has its own shade.
   - On the owner's request: with `smooth` (the default) a few points give a smooth curve. Each face is laid along its own length, so stones neither gap on the outside of a bend nor pile up inside. Coping stones become wedges on bends, and each face's foot follows the ground under that face, so it holds on cross slopes.
   - `smooth=False`, or a curve object's sharp points, give corners: long corner stones take turns along each face at corners of 60° or sharper.
2. **Ragged hedge:** `hedge.lay(line, height=1.6, width=1.1, gaps, ground, smooth, raggedness, amount, twigs, dry, seed, …)`.
   - Made of leafy sprays, thick at the hedge's skin, with a rounded uneven top and faces that bulge and fall back. It has holes, woody stems at a thin foot, and bare twigs.
   - The twigs out of the top are short and arching, so the outline is never spiky.
   - On a bend it is as thick on the outside as on the inside.
3. **Rubble stone face:** `lay_rubble.lay(wall, sides, openings=[(side, 'door'|'window', left, bottom, width, height)], pitch, high_side, relief=0.07, quoins, fill, seed, …)`. The name keeps it apart from `lay_stone`.
   - Rough stones lie in wandering courses with thin stones pinned in, and big squared stones at the corners (quoins).
   - Each opening gets jamb stones (long and short in turn), a lintel, a sill for windows and a dark panel.
   - The stones follow a sloping top or a lean-to (the same `pitch` and `high_side` as lay_boards), with a dark backing behind them above the box.
4. **Straw in litter:** `litter.scatter(yard, area, kinds=('straw',))`. Straw is laid only when asked; leaves and twigs come out exactly as before.
   - Strands spread over each clump's lumpy outline and lie mostly one way. They are bent ribbons, the outer ones darker, kept in the picture's dark range.
   - Clumps are pressed flat and muddy where the ground is trodden.
   - The ground is asked once per clump in Python; a Geometry Nodes step then drapes every strand onto the ground.
5. **Moss:** `moss.add(material, amount=0.8, foot=0.35, facing, scale, colour)` returns a new mossy copy and leaves the original untouched.
   - Moss grows in patches on faces that look up and climbs up from the ground under each object, not from height 0 as the builder's did.
   - It works on plain colours too, and the moss is matte and slightly raised.
6. **Clearing under a thing:** `clear_under.clear(scatterings, footprint, margin)`.
   - The footprint can be an object's outline seen from above, a function f(x, y), a rectangle or a polygon.
   - It removes only the points of the scatterings it is given. Every other point keeps its numbers, the counts are corrected, and `stones.settle` still works afterwards.
   - The builder's version walked every object in the scene and sank points 60 m down; this one does neither.
7. **Hollow lay_boards:** `lay_boards.lay(..., hollow=True, inside_material=...)`. The hut becomes a hollow shell 0.1 m thick with a floor and a ceiling, its openings cut open and its doorways left without a door leaf (windows are cut open too). Without `hollow`, it lays exactly the same boards as before (compared).

Two new made materials, `MADE • straw` and `MADE • hedge leaves`, were added in made.py; Materials.blend was rebuilt and Materials.blend1 deleted.

**Tests:** `tests/test_store_farm_tools.py`, added to `run_tests.sh`, covers all seven, plus a Bezier S-bend that turns 247° and climbs 1 in 10. Round its bends the gaps between stones average 1.5 cm on the outside and 1.3 cm on the inside, and the hedge is 0.91 times as thick on the outside as on the inside.

## What does not read well yet

- Straw close up looks a little like hair or pine needles, and on wet mud it reads dark.
- The hedge close up looks somewhat like a row of bushes; it repeats 12 spray shapes.
- On the wall card the gateway looks small in perspective.
- Corners between 20° and 60° (only with `smooth=False`) have plain meeting faces, which may show small seams.
- Moss is subtle at dusk.
- Clearing removes points for good; the same scatter call with the same seed lays them again.
- The litter and lay_boards cards were not redrawn to show straw or the hollow shell.

## Mistakes made and fixed

- Straw clumps laid flat at their middle's height were swallowed by the ground's bumps; fixed by draping each strand onto the ground.
- The wall's core ran straight past a corner and poked out through both faces; found by painting the core red, fixed by cutting the core's end on the corner's angle.
- Corner stones cut square to their own face left a wedge at a 78° corner; their ends now follow the other face.
- End stones bulged 2 cm into the gateway; they are set back.
- On a cross slope the downhill face's stones floated; each face now follows the ground under it.
- The hedge core showed as a grey slab under the card light; it is now smaller, higher, tapered and dark green.
- A hedge spray leaked into a gap near a corner, and rubble stones under a slope were forced into slivers above it; both fixed.
- A slip in the moss tool's maths code; fixed.

## Files

Created in `plugins/painted-place`: `brief/store/tools/_rough_stones.py`, `dry_wall.py`, `hedge.py`, `lay_rubble.py`, `moss.py`, `clear_under.py`; `tests/test_store_farm_tools.py`; `brief/store/cards/tools/dry_wall.png`, `hedge.png`, `lay_rubble.png`, `moss.png`, `clear_under.png`; `brief/store/cards/materials/MADE - straw.png`, `MADE - hedge leaves.png`. Changed: `brief/store/tools/litter.py`, `lay_boards.py`, `brief/store/materials/src/made.py`, `Materials.blend`, `tests/run_tests.sh`. The helper's card and preview scripts are outside the plugin, in `/home/claude/store-work/barn/farm-tools/` (`farm_cards.py` redraws the five tool cards).
