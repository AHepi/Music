You are the road helper. Your scratch folder is `/home/claude/store-work/pbr56/road/`. Your clock: finish by 19:00 by this computer's clock.

1. **Setts along a line or curve,** in `lay_cobbles.py`: a new function, for example `lay_setts_along(line, width, ...)`.
   - It takes a line of points, as `lay_kerb` and `dry_wall` take theirs, with the same smoothing of a few points into a curve (read `brief/store/tools/_lines.py`; do not edit it). It also takes the road's width, and the same options as `lay_setts` (crown, missing, shades, quarries, rocked, rocked_area, holes, hole_water, patch, grit, moss, seed).
   - Setts go in courses straight across the road, square to the line, each course's joints staggered from the next.
   - On a bend the courses fan out: the setts on the inside of the bend are shorter, or their joints are wedge-shaped. Never overlapping; never a gap wider than a joint.
   - The road climbs and falls with the line's height and keeps its crown across.
   - It makes its own bed under the setts (the road lowered 12.5 cm, as `lay_setts` does), and returns the same kind of `setts` object, so joint_weeds, puddles and the wear work on it.
   - Its TOOL must say what `top_height` means on a road that climbs.
2. **Flags along the same line:** a pavement along a curve (for example `lay_flags_along(line, width, ...)`), flags in rows across the pavement, fanning the same way.
3. **Edges that line up:** a way to get the road's two edge lines (for example `road_edges(line, width)`), so that `lay_kerb` and the flags can be laid exactly along the road's edge. Check that `lay_kerb` follows them on an S-bend (it already reads curves).
4. **Photographed, piece by piece.**
   - Write `pp_piece` on every sett, flag and kerbstone (see the agreement).
   - Once `brief/store/materials/Photographed.md` names the materials and they exist, switch the defaults of lay_setts and lay_setts_along, lay_flags and lay_flags_along, and lay_kerb to those photographed materials. The old materials stay usable by name.
   - The old `lay_setts(road)` and `lay_flags(pavement)` must lay exactly the same stones in the same places as now: `tests/test_store_street_ground.py` holds a fingerprint of them. Keep it passing. If it checks the default material names, update only that expectation, and say so in your report.
   - If the materials are not ready by your last 20 minutes, keep the old defaults and say so.
5. **Tests,** in `tests/test_store_curved_road.py`:
   - On an S-bend road, every sett lies inside the road's width, none overlap, no joint is wider than asked, and the courses are square to the line within a few degrees, fanning on the bends.
   - A climbing road follows the line's height.
   - Flags along the curve pass the same checks.
   - A kerb laid along `road_edges` sits at the road's edge all the way.
   - The wear options work on a curved road, and so does joint_weeds.
   - Every piece has `pp_piece`, from 0 to 1, varied.
   - The same seed gives the same road; wrong options are refused; `--help` answers.
   - Run `tests/test_store_street_ground.py`, `tests/test_store_tools.py` and `tests/test_store_rules.py` too.
6. **Cards:** redraw `lay_cobbles` (setts on an S-bend, with flags and kerbs) and `lay_kerb` (along a curve).
