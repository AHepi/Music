# 56 Store helper for the road on a curve - report

What this file is: the report, word for word, of the helper that made the sett road, its flags and its kerbs follow any line or curve, in photographed stone (5 November 2026, 17:31 to about 18:15). Saved by the session.

---

## Road helper: report

**Where it stands:** the setts road, the flags and the kerbs now follow any line or curve. Every stone carries its own `pp_piece` number. The defaults are now the photographed materials. All my tests pass, along with the street ground, tools and rules tests. The one exception is the rules test's catalogue check, which fails until you run `catalogue.py`, as expected. The old `lay_setts(road)` and `lay_flags(pavement)` still lay exactly the same stones in the same places: the fingerprint test passes.

### What I made, and how to call it
All of it is in `lay_cobbles.py` and `lay_kerb.py`.

- **A road along a line or curve:** `lay_cobbles.lay_setts_along(line, 5.0, seed=3)`
  - The line is the road's middle. It can be a list of points, a curve object, a line-mesh object or a JSON file. A few points are smoothed into a curve, the same way `lay_kerb` does it.
  - The setts go in courses straight across the road, square to the line. Each course's joints sit at least 6 cm from the last course's joints.
  - On a bend each course becomes a wedge, so the setts on the inside are shorter. On the test S-bend they were 70% of the outside setts' length.
  - The road climbs and falls with the line's height and keeps its crown.
  - It makes its own bed 12.5 cm under the setts, and the puddle tool refuses that bed, as it does with `lay_setts`.
  - It takes every wear option `lay_setts` has. There is also `joint=`, the widest a joint may open (default 2.5 cm). Joints come out 8 mm where narrowest.
  - It returns the same kind of setts object, so `joint_weeds`, puddles and the wear all work on it.
- **The road's edges:** `left, right = lay_cobbles.road_edges(line, 5.0)`
  - Kerbs go on with `lay_kerb.lay(left, road='right')` and `lay_kerb.lay(right, road='left')`. On the S-bend the kerb stays at the road's edge all the way.
  - `road_edges(line, 5.0, beyond=0.30 + 0.9, rise=0.13)` gives the middle line for a pavement behind the kerb.
- **Flags along a line:** `lay_cobbles.lay_flags_along(middle, 1.8, seed=3)`
  - The flags go in rows across the pavement.
  - On a bend each flag is cut to a true wedge, so the joints stay even.
  - It makes its own bed under the flags.
- **`top_height` on a road that climbs:** it is only the setts' tops at the line's first point. `lay_cobbles.top_at(setts, x, y)` gives the height anywhere, for example `puddle.make(..., level=top_at(setts, x, y) + 0.002)`. The tool's notes and its trap now say this.
- **`pp_piece` on every piece:**
  - Setts, relaid setts and flags carry it on the points that carry the copies.
  - Kerbstones and channel stones carry it on their faces.
  - It comes from its own dice, so it moves no stone.
- **Defaults are photographed** (names from `Photographed.md`):
  - setts: `SURFACE • dark_rock_02`
  - road bed: `SURFACE • gravel_road`
  - flags and kerb: `SURFACE • worn_rock_natural_01`
  - The old materials still work by name.
- **A fix the materials needed:** the photographed materials laid a whole metre of picture squeezed into every copied sett and flag (the flags came out streaked). Now each stone gets a copy of its material, named `<material> • stone sized`, which shows the pictures at their real size. The store's own materials are unchanged.
- **Command line:** `python3 lay_cobbles.py --points "0,0,0 0,8,0 3.5,18,0" --width 5 --out road.blend`, or `--line "Road line"` with `--blend`.
- **Cards:**
  - `lay_cobbles`: setts round an S-bend, with kerbs and wedge flags on both sides.
  - `lay_kerb`: a kerb round a bend.
  - I looked at both at full size.

### What does not read well yet
- The kerb and the flags are the same sandstone at the same height, so from far off the kerb's top merges with the pavement. Only its face shows the edge.
- There are limits on how tight a bend can be:
  - A road's bend radius must be at least 1.33 times half its width (3.4 m for a 5 m road).
  - A pavement's bend radius must be at least its width.
  - Anything tighter is refused, and the message says the radius needed.
  - A pavement round the inside of a road's bend sits on a much tighter line than the road, so the road needs extra room there.
- Near those limits, the inside setts get short (about 5 cm). Where a straight meets a bend, a flag can sit about 3 degrees off square.
- `joint_weeds` treats each wedge flag as a rectangle. I checked 496 tufts and none grew inside a flag.
- The default 0.7% missing setts show as small dark holes from above, as they always did.

### Mistakes I made and how I fixed them
1. **A 21 cm "joint" in my first test** was one of the default missing setts. The joint check now lays with `missing=0`.
2. **My test called `puddle.make` with the wrong options** (`length`/`width` instead of `size`). Fixed.
3. **My first test S-bend was too tight** (4.5 m radius): a pavement on its inside would have been a 0.8 m corner. I made the test S-bend gentler (9.3 m) and made the tool stricter.
4. **Rectangular flags on bends** made tiny rows or opened 11–13 cm joints. I replaced them with wedge flags.
5. **Flag slivers at the pavement's edge, and rows turning too far,** opened 17–33 cm joints on tight bends. Now no edge flag is under 20 cm, each row turns at most about 9 degrees, and there is the pavement limit.
6. **Setts near the old bend limit** opened a 4.8 cm joint on the inside. I tightened the road limit.
7. **Edge setts up to 47 cm wide** came from moving joints apart. Oversize edge setts are now split in two.
8. **The photographed material was squeezed** into each stone. Fixed with the `• stone sized` copy.
9. **First card tries:** the S-line was refused as too tight, the camera was too high, and hole water drew as a white blob. Fixed by changing the line, the camera, and leaving out the hole.

### Files created or changed (in `/home/claude/music/plugins/painted-place`)
- Changed:
  - `brief/store/tools/lay_cobbles.py`
  - `brief/store/tools/lay_kerb.py`
- New: `tests/test_store_curved_road.py`
- `tests/test_store_street_ground.py`: I changed only the default-material expectation. It now accepts the store's material or its `• stone sized` copy.
- Redrawn:
  - `brief/store/cards/tools/lay_cobbles.png`
  - `brief/store/cards/tools/lay_kerb.png`
- My scratch folder is `/home/claude/store-work/pbr56/road/`. It holds `notes.md`, the card script `scripts/road_cards.py`, the look pictures in `pictures/`, and the originals in `backup/`.

### For you
- **Run `catalogue.py`.**
- **Store.md:** its "A paved street" line could mention `lay_setts_along`, `road_edges` and `lay_flags_along`. Store.md isn't mine to edit, so I left it.
- **Tell the materials helper about the squeeze:** any photographed material on Geometry Nodes copies has this problem.
  - My copy is skipped if their "Picture size" group already reads `stone_scale`.
  - If they add their own fix using a different name, the pictures would be resized twice.

I didn't use anything from memory.

---

## Traps

- This is the helper's own account. What the session checked afterwards is in the project story, log 56.
