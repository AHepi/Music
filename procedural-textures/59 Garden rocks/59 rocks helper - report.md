# 59 Rocks helper - report

What this file is: the report, word for word, of the helper who made the store's rocks tool at the owner's word (decision 89; 6 November 2026, about 08:27 to 09:28). Saved by the session. Its words are in `59 rocks helper - text.md`.

---

## Rocks tool: report

The new rocks tool is in the store and working. All the tests you asked for pass, except the catalogue check in `tests/test_store_rules.py`, which waits for you to run catalogue.py, as expected. I took in your notes on the first pair and redrew the new picture with the same place and light. Finished at 09:28.

### What I made
`brief/store/tools/rocks.py` makes rocks by rules. Each seed gives its own rock: a lump broken along a few flat faces, then smoothed by "weather" passes. Old rocks get many passes, so their edges are rounder. Then its surface is pitted. There are four kinds:
- **boulder:** old, weathered, set deep in the ground.
- **angular:** freshly broken, with sharp faces.
- **flat:** slabs with a level top, for stepping stones and the water's edge.
- **river:** smooth, worn by water.

```python
laid = rocks.scatter(yard, kind='boulder', count=24, sizes=(0.15, 0.9), area=(-3, -3, 3, 0), gather=0.5, moss=0.8, seed=2)
big  = rocks.place([(1.0, 2.0)], kind='boulder', size=1.4, ground=yard, moss=0.9, seed=5)
```

**`scatter()` uses Blender's particle system.** Every rock is a particle copy of one of 8 shapes per size group. Each copy is turned at random, tilted with the ground and sunk by a share of its height.
- Sizes run between the two you give, with big rocks fewer than small ones (`fall=`).
- `gather=` puts small rocks at the feet of big ones.
- The ground you pass is not changed.

**What the particle system can't do, and why:**
- **Keeping rocks apart.** Blender spreads particles at random, so they overlap. The tool picks each spot itself (inside your area, kept apart) and gives the particle system one tiny hidden face per spot, one particle each.
- **More small rocks than big ones.** Its size setting only spreads sizes evenly. So each scatter is split into size groups, one particle system each, with counts falling as size grows.
- **Real bumps.** Copies share one shape, so the same bumps would repeat. That's why big rocks near the eye come from `place()`: each is its own object, with real bumps taken from the photograph's height picture.

**Surfaces (PBR, decision 84).** The rocks wear photographed rock at its real size, within about a third: each size group's shapes are made at that group's middle size.
- Each rock shows its own part of the photograph. I checked this in a render: six copies of one shape matched each other at most 0.14, where the same picture would match close to 1.
- Feet are darker and glossier where the ground tool marked the ground wet.
- A little wet all over after rain; moss on tops when asked.
- Greyer than the photograph by default (`grey=` and `tint=` change this).

**Shelf.** I added three CC0 Poly Haven sets (2 x 2 m, four pictures each, none blank):
- `lichen_rock` for boulders
- `seaside_rock` for flat and river stones
- `rock_wall_02` for broken stone

Rebuilding Materials.blend added exactly SURFACE • lichen_rock, • seaside_rock and • rock_wall_02. Every other material came out identical, which I checked against a copy taken before.

### Example pictures
All are 540 x 960, Cycles, and inside every band.

| Picture | Time | Bright | Warm | Cool | Light |
|---|---|---|---|---|---|
| `pond_old_rocks.png` (the builders' `rock()`) | 09:00 | 0.17 | 26% | 39% | 0.8% |
| `pond_new_rocks.png` (first try) | 09:03 | 0.17 | 25% | 42% | 0.8% |
| `pond_new_rocks_second.png` (after your notes) | 09:14 | 0.18 | 24% | 42% | 0.8% |
| `pond_new_rocks_third.png` (seam fix) | 09:21 | 0.18 | 24% | 42% | 0.8% |
| **`pond_new_rocks_fourth.png` (final)** | 09:27 | 0.18 | 23% | 43% | 0.8% |

The **final pair** is `pond_old_and_new_side_by_side_fourth.png`. Earlier pairs are `..._side_by_side.png`, `_second` and `_third`. All files are in `/home/claude/store-work/rocks59/`.

**What changed after your notes:**
- **Bare edge.** The bank now gets 64 boulders asked (63 fit), 0.22 to 0.85 m, in two rows at the water's edge, closer together and set deeper.
- **Reddish boulder.** Boulders are now greyer with a slight green by default, and set deeper by default.
- **Little moss.** Moss is up to 0.95, and moss edges are softer.
- **River stones.** The ones along the gravel are now as big as the builders' stones there.

### What doesn't read well yet
- The lantern takes up the left third of the frame. It was the only way I found to get the warm-light measure into its band.
- The river stones and small broken stones hardly show at this distance.
- The wet feet are subtle.
- On a big rock, the photograph's large dark and pale patches can meet the moss cap in a visible line.
- Broken stone is crisp but its edges are softly rounded rather than razor-sharp.
- Real bumps only come on rocks set with `place()`, at about 80,000 faces each.
- A narrow area holds fewer rocks than asked, biggest first: 23 of 34 fitted in the first band until I widened it.

### Mistakes and fixes
- The ground tool moves its sheet into place, so I first dug the pond 5 m away. Fixed by using world positions.
- The ground had the ground tool's own material in its first slot, so the gravel drew as moss. Fixed by clearing the slots first.
- The card's own floor showed through the dips of my patch. Fixed by lifting the patch.
- My first light measured outside the bands (bright 0.10, warm 49%). Fixed with a bluer sky, more exposure, and the lit lantern near the eye.
- An unknown surface name crashed instead of being refused. It is now refused with the nearest names.
- A hard dark seam ran across the boulders. The store's per-piece picture turn rotates about whichever way a face looks most, which keeps changing on a round rock. Rocks now only shift their picture, never turn it, and the three projection sides blend more softly.
- Running build_materials.py made Blender rewrite `Materials.blend1` (its own backup). The previous backup from 17:50 is gone. I kept a copy of the file as it was before: `rocks59/Materials.before.blend`.

### Files
**Created:**
- `brief/store/tools/rocks.py`
- `brief/store/cards/tools/rocks.png`
- `tests/test_store_rocks.py`
- `brief/surfaces/lichen_rock/`, `seaside_rock/`, `rock_wall_02/`
- everything in `/home/claude/store-work/rocks59/` (`notes.md`, `scripts/`, pictures)

**Changed:**
- `brief/surfaces/manifest.json`: three entries
- `brief/surfaces/Surfaces.md`: three rows and one sentence
- `brief/store/materials/Materials.blend`: rebuilt, three new materials

I changed no other file and no material counts in the tests: the tests count with "at least", so nothing needed raising.

### Lines for Store.md
- **Rocks** (the owner's word, 6 November 2026): `rocks.scatter(ground, kind='boulder'|'angular'|'flat'|'river', count=, sizes=(small, big), area=)` scatters rocks made by rules over your ground with Blender's particle system: each its own shape, big ones fewer, turned, tilted with the ground, sunk in it, kept apart (`gather=` puts small ones at the feet of big ones). `rocks.place(points, size=, ground=)` sets big rocks near the eye singly, with real bumps from the photograph's height picture. Both wear the shelf's rock photographs (`lichen_rock`, `seaside_rock`, `rock_wall_02`), each rock its own part, greyer than the photograph (`grey=`, `tint=`), wet at the feet, moss on top with `moss=`.
- Trap: the rocks' particle copies are drawn only when the picture is drawn, so a ray from above cannot find them. Measure ground heights before scattering.
- Trap: a narrow area holds fewer rocks than asked, biggest first. `placed` says how many; widen the area or give `spacing=0.6`.
- Trap: a photograph turned per piece meets itself in hard seams on a round thing. The rocks only shift theirs; do the same for round things of your own.
- Trap: rock photographs under warm lamps read brown. Garden granite is grey: the rocks tool greys them by default.

---

## Traps

- This is the helper's own account; what the session checked afterwards is in the project story, log 59.
- `Materials.blend1` is Blender's own backup file and is not kept in the repository (the repository ignores it), so its loss changes nothing there.
