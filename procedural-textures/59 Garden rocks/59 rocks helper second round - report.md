# 59 Rocks helper, second round - report

What this file is: the report, word for word, of the helper who pulled the rocks builder's hand-made rock work into the store's rocks tool (log 59; 6 November 2026, about 10:47 to 11:10). Saved by the session. Its words are in `59 rocks helper second round - text.md`.

---

**Rocks tool, second pass: what the garden builder had to make by hand is now part of the tool**

All the new options are off unless asked for, with two exceptions (the moss colour and the flat stones, points 4 and 7). Every call that worked before still works the same way, including the three private calls the garden's script makes (`_shapes`, `_sheet`, and `material` with its 8 values in the same order). A scatter that already had enough room lays exactly the same rocks as before: I checked this on a wide area.

**What I added, with the call for each**
1. **Rocks on spots you give, as particle copies:** `rocks.at_spots(spots, kind='flat', size=0.7, top=0.12, ground=yard, water=0.0, relief=0.03, seed=7)`
   - Each spot gets its own rule-made shape at its own size, and its top reaches the height `top` you give.
   - On dry ground a rock is never left floating: it is lowered into the soil, and the result's `lowered` lists those rocks.
   - Where its foot is under the `water` height you give, it stands as asked.
   - `relief` gives real bumps; it can be one number or one per spot. `facing` sets which way is up.
   - It gives back the height each top reached, so a lantern can be stood on a seat (a ray cannot find particle copies).
   - The shapes are made with the same seed numbers as the builder's `rocks_at`, so swapping it in gives the same rocks.
2. **Narrow areas:** when a size of rock comes up short, the scatter finds more places on the part of the ground the area reaches. A ring 0.5 m wide on a 30 m ground: before, 72 of 120 rocks; now 120 of 120. `area=` also takes the builder's own kind of test of one place, `keep(x, y)`, and lays the same rocks as the same area given the other way.
3. **Each rock its own amount of moss:** `moss_spread=(0.35, 1.4)` on `scatter`, `place`, `at_spots` and `material`.
4. **The moss's colour:** `moss_colour=(r, g, b)`. I made the brighter green (0.07, 0.105, 0.02) the default: in my test the old green read dark olive-grey and the new one reads as moss. The old one is still there as `rocks.MOSS_DARK`.
5. **The photograph's relief strength:** `normal_strength=` from 0 to 2. The rock sets are already at 1 as the store makes them, so the builder's "raise to 1.0" changed nothing. Only values above 1 make the relief stronger.
6. **The water line:** `water=<the water's height>`, with `water_band=0.07` for how high the wet band climbs. It gives a dark wet band above the water and darker, glossier stone below it.
7. **Flat stones:** I changed their default to `lichen_rock`. In my test the `seaside_rock` flat stone went dark grey to black in its shade, as the basin's front stone did in the garden. The lichen one stays readable and is the same stone as the boulders. River stones keep `seaside_rock`.

The material's settings now have names a script can look up: 'Moss amount', 'Moss spread', 'Water line' and 'Wet feet'. The tool's `source` says what came from the builder, with line numbers. `--help` and the command line have the new options too.

**What does not read well**
- At its default 7 cm the water line is faint in a small picture, as the builder also found; 0.15 m reads clearly. It goes by height alone, so any rock lower than the water darkens, in a pond or not.
- The `normal_strength` difference showed only with light from the side. On a rock in shade I could not see it.
- `moss_spread` shows, but only a little, in a small picture.
- Flat stones in `lichen_rock` read a little browner than the boulders. Their greyness setting is still 0.3, as the garden had it; I did not change it.

**My mistakes and fixes**
- My first test picture was too far away and too dark to judge, so I moved the camera closer and made it brighter.
- In one side-light test one rock threw its shadow on the other, so I moved the light.
- One of my new test checks looked for a setting by the wrong kind name, so it failed. I made it check by Blender's own name and it passed.
- The example in the tool's own notes asked a 0.7 m flat stone to reach 0.42 m. It cannot do that without floating, so the tool rightly lowered it. I changed the example to 0.12 m.

**Checks:** `test_store_rocks.py` passes all 10 groups of checks, including new ones for every new call and option. `test_store_tools.py` passes. In `test_store_rules.py` the rule checks pass, and the catalogue check fails until the session runs `catalogue.py`, as expected.

**Files I changed**
- `/home/claude/music/plugins/painted-place/brief/store/tools/rocks.py`
- `/home/claude/music/plugins/painted-place/brief/store/cards/tools/rocks.png` (redrawn because the look changed: flat stones now lichen granite, brighter moss, the back boulders each with their own moss)
- `/home/claude/music/plugins/painted-place/tests/test_store_rocks.py`

My scratch folder is `/home/claude/store-work/rocks59b/`. It has `notes.md`, the test pictures (`pic_a2.png`, `pic_c1.png`, `pic_b1.png`, `pic_d2.png` and their crops), `card_before_after.png`, my scripts, and copies of the three files from before my change.

**Lines for Store.md**
- In the **Rocks** paragraph, after the `scatter` sentence: "A narrow area (a pond's bank) gets as many as fit; `area=` may also be your own test of one place, `keep(x, y)`. `rocks.at_spots(spots, kind='flat', size=0.7, top=0.12, ground=ground, water=0.0, seed=7)` lays rocks with a set place as particle copies, each its own shape at its own size, its top at the height you give (never floating on dry ground; with `water=` a rock in a pond stands as asked), real bumps where you give `relief=`, and gives back the height each top reached." Change "Both wear" to "All three wear". Put `lichen_rock` for boulders and flat stones and `seaside_rock` for river stones. Add "each rock its own amount of moss with `moss_spread=(0.35, 1.4)`; `moss_colour=`; the photograph's relief with `normal_strength=` (0 to 2); a dark wet water line where they stand in a pond with `water=` (its height)."
- In Traps, replace "A narrow area holds fewer rocks than asked..." with: "An area too small to hold the rocks apart holds fewer than asked, biggest first: the tool gives back how many it placed; widen the area or give `spacing=0.6`."
- In Traps, replace "Copies made by a particle system share one shape, so only `rocks.place`..." with: "Scattered copies share their shapes, so real bumps come only on rocks laid with `rocks.at_spots(..., relief=)` or `rocks.place` (about 80,000 faces each): use them for the few big rocks near the eye."
- New trap: "A not-floating check that lowers every rock into the soil pulls a pond's rocks down to its bed (a garden builder's did). `rocks.at_spots` lowers only rocks whose foot would show; give it the water's height (`water=`), or a rock asked to stand high in a deep pond is pulled down towards the bed."
- New trap: "A scatter's area wider than the gaps an earlier pass opened fills them again: a garden builder's bank scatter put a big boulder back on the near shore the last pass had cleared so the water shows. Keep the earlier passes' clear places out of the new area (a `keep(x, y)` test can say no there)."
- New trap: "Finding a material setting by its value picks the wrong one: the rocks' moss amount and their wet feet are the same kind of setting and can hold the same number, and a builder's search for the moss amount changed the wet feet first. Find them by name: 'Moss amount', 'Moss spread', 'Water line', 'Wet feet'."
- New trap: "Flat stones in the dark smooth `seaside_rock` draw as a black patch in shade (a basin's front stone did): the rocks tool's flat stones now wear `lichen_rock` by default."
- New trap: "The rock sets' normal picture is already at full strength (1) as the store makes them; only `normal_strength=` above 1 (up to 2) makes the relief stronger."

**For the session (not mine to edit)**
- Run `catalogue.py`.
- `brief/surfaces/manifest.json` (line 747) and `brief/surfaces/Surfaces.md` still say `seaside_rock` is "for river stones and flat stepping stones": it is now for river stones only.
- The garden's own script behaves as before. Its by-hand moss colour swap now finds nothing to swap, but the moss is already that green.

I wrote this in plain words because the owner's saved preferences ask for that. Following the same saved preferences, I put a Traps section at the bottom of my `notes.md`.

---

## Traps

- This is the helper's own account; what the session checked afterwards is in the project story, log 59.
