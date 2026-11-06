# 60 Water and moss helper - report

What this file is: the report, word for word, of the helper who pulled the moss builder's hand-made work into the store: see-through water for the slab path and the puddle, moss on open shapes, ferns kept off paths, the moss's colour at dusk (log 60; 6 November 2026, about 14:34 to 14:59). Saved by the session. Its words are in `60 water and moss helper - text.md`.

---

## Report: see-through water, moss on open shapes, ferns kept off paths, moss colour at dusk

I finished at 14:59, well before 15:35. All five jobs are done. Every call the garden scripts make still works. The tests for the changed tools pass. The rules test passes its rules check and then stops at the catalogue check, as you expected, until you run catalogue.py.

### What I changed, and the call for each

**1. See-through water**

How it works: the water's own shiny surface is mixed with a clear surface that light passes straight through. These are the builder's values:
- Looking straight down, about half the stone shows through and the other half is the water's reflection.
- At a low, glancing look the reflection grows stronger.
- Each pool fades out towards its shallow edge.
- The stone under the water shows a little darker and warmer. Lamps still light it, because the light is not bent.

The calls:
- **Slab path:** `lay_slab_path.lay(line, ...)` now gives this water by default. `lay_slab_path.lay(line, ..., see_through=0)` brings back the old clear water. A water material of your own is used as it is unless you add `see_through=0.4` (or another number).
  - **Why it is the default:** the old clear water reflects only about 12% of the sky looking down. In my close test picture its pools showed as faint pale patches. The builder had already found that even 38% reflection made "pale dry patches". The new water reads as shallow water with the stone's dip and cracks visible under it. No earlier garden script uses this tool.
- **Puddle:** `puddle.make(..., see_through=0.5)`. The default stays at 0, which is the puddle exactly as before. `puddle.see_through(material, 0.5)` makes a see-through copy of any water material.
  - **Why it is only an option:** puddles on mud, roads and in ruts are muddy, not clear. The street, chapel and barn scripts and several tests rely on the old puddle. On a stone flag in my picture the old puddle was a black blot and the new one was water.

**2. Moss on an open shape**

`moss.grow(basin, ...)` now works straight on a basin that is open underneath. Before growing, it fills the shape's holes in a hidden working copy; your object is left as it was.
- The builder's basin shape now grows 0.88–1.0 square metres of moss, where it grew almost nothing before.
- A flat sheet open on all sides (like a wall top) is given some thickness instead.
- I caught one problem before it happened: a trough or pot built as a thin shell open on top would have got a "lid" of moss over its opening. Those shapes are now thickened instead, and a test checks that no moss grows over the opening.

**3. Ferns kept off paths**

There are two new options, which keep out the moss on the soil, the grass round the rocks and the ferns:
- `moss.feet(ground, rocks, ferns=3, keep_out=(x0, y0, x1, y1))`. This also takes a list of corner points, or several areas.
- `moss.feet(..., keep=lambda x, y: ...)`, where the test says yes or no for each place.

A fern then tries other sides of its rock, keeping both its middle and the reach of its fronds clear of the area. If no side works it tries a smaller fern, then the next biggest rock. What `feet` gives back now also says how many ferns found no room. Without these options it places everything exactly as before.

**4. Moss colour at dusk**

The new defaults are the builder's values: darker, more olive greens, deeper shadows between the tufts, sheen 0.3 instead of 0.8 (the tufts get 0.21) and the photograph's lumps at 0.7 instead of 0.2. There are named options on `grow`:
- `sheen=0.3` and `lumps=0.7` are the new defaults.
- `greens='olive'` is the default; `greens='bright'` gives the old greens.
- `greens='bright', sheen=0.8, lumps=0.2` brings back the old look.
- `feet(..., sheen=)` sets the sheen of the tufts on the soil.

I chose these as defaults because the film's places are at dusk, where the builder showed the old moss read as lime felt. The builder's own script still draws the same, because it sets these values itself.

I left the tuft height alone. The builder's script already makes its tufts 1.5 times taller, so changing the store's height would have made them taller again in that script.

### Pictures and cards

All my pictures are in `/home/claude/store-work/water60/`, and every one is logged in `notes.md` there.
- I redrew the **moss card** (now olive and lumpy rather than lime) and the **slab path card** (darker see-through pools with soft edges).
- The puddle card is unchanged, because the puddle's default look did not change.

### What does not read well

- **The rocks card is now out of date.** It is not one of my files. The rocks' moss is now olive by default, but the card still shows lime cushions. The moss helper's script `/home/claude/store-work/moss60/scripts/card_rocks.py -- --out FILE` can redraw it.
- On the slab path card, the far pools still show the card's back light as hard white spots when seen at a low angle.
- At eye height from 2 m, the slab pools are hard to tell from wet stone.
- All pools on a slab path share one water material, so one pool cannot keep more reflection. The builder gave the pool that reflects the lantern a boost; the store does not have that. With the puddle tool, give that one puddle a lower `see_through`.
- I have not tried the see-through puddle on mud.

### Mistakes I made, and the fixes

- **The darker shadows between tufts did not take at first.** The moss code already used the name `greens` for one of its own parts, which hid my new option. Its test caught this. I fixed it and redrew the moss card I had drawn with the fault.
- My first picture of all the changes together was too dark and too far away to judge. I redrew it closer and brighter.

### One finding that changes a trap

The builder said water that bends the light leaves the stone under it unlit. In my test that is true only when the water also casts a shadow:
- dry stone: 0.57
- under the store's clear water, which casts no shadow: 0.43, so the stone is lit
- under the same water casting shadow: 0.09, so the stone is unlit

### Files I changed

- `brief/store/tools/puddle.py`
- `brief/store/tools/lay_slab_path.py`
- `brief/store/tools/moss.py`
- `brief/store/cards/tools/moss.png`
- `brief/store/cards/tools/lay_slab_path.png`
- `tests/test_store_moss.py` (new checks for the colour defaults and old look, open basin, flat sheet, open trough, keep and keep_out)
- `tests/test_store_garden_ground.py` (new checks for the see-through water)

Tests run on the final files: `test_store_moss`, `test_store_garden_ground`, `test_store_tools` and `test_store_rocks` pass. `test_store_rules` passes its rules check (110 files), then stops at the catalogue check.

### Lines for Store.md

**Traps:**
- Water made half see-through lets less bright sky into a close view that looks down on it. The garden builder's close view, whose warm light was the hanging lantern reflected in a pool, fell under the warm-light band (0.53% to 0.28%). It came back only when that one pool kept more of its reflection and the view's exposure went from 4.4 to 4.8. Give the puddle that reflects a lamp less `see_through`, and measure the close view again.
- Water that shows the stone under it by bending the light leaves that stone unlit when the water casts a shadow, because light bent through water (caustics) is off here. In a helper's test the stone under such water drew 0.09 against 0.57 for dry stone. The store's water casts no shadow (0.43 under the same water). Give your own water `obj.visible_shadow = False`, or use `puddle.see_through`, which does not bend the light.
- Water more than about 60% see-through draws pale dry patches where a lamp lights the stone under it. Half see-through, with the stone under it darker than the dry stone round it, drew water (the garden builder).
- A fresh kit can change what an earlier script draws. The rocks' moss became real cushions by default (decision 90), so the earlier garden script drawn with a fresh kit showed bright lime cushions the owner never saw. On 6 November 2026 the cushions turned dark olive by default. Set every moss option in your script (`moss_style`; `moss.grow`'s `greens`, `sheen`, `lumps`) to keep the look you showed.
- `moss.feet` puts its ferns at a random side of the biggest rocks, and in the garden one landed on the path twice. Near a path, give `keep_out=` (the path's area) or `keep=`.

**Conventions (suggested additions):**
- In the Japanese garden line: `lay_slab_path`'s pools are half see-through by default (`see_through=0` gives the old clear water). Use `puddle.make(..., see_through=0.5)` for a puddle on stone paving.
- In the Real moss line: the cushions are dark olive, yellow-green where the light falls, with a low sheen and the photograph's lumps (`greens='olive'`, `sheen=0.3`, `lumps=0.7`). `greens='bright', sheen=0.8, lumps=0.2` is the first look, which read as lime felt at dusk. `moss.grow` also works on open shapes. `moss.feet(..., keep_out=area)` or `keep=` keeps its moss, grass and ferns off a path.

---

## Traps

- This is the helper's own account; what the session checked afterwards is in the project story, log 60.
