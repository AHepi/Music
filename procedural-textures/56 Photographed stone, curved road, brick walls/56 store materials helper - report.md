# 56 Store helper for the photographed materials - report

What this file is: the report, word for word, of the helper that made the photographed stone and brick materials for the store (5 November 2026, 17:31 to 18:02). Saved by the session.

---

Materials helper report (pbr56). Finished at 18:02, before the 18:50 limit. Source: decision 80 and the owner's words of 5 November 2026.

**Summary**
Each sett, flag, kerbstone, brick and block can now show its own part of a real photograph. The other two helpers' material names are ready, and the street's own 45 materials are untouched.

**What I made, and how to use it**

1. **Five new photograph sets on the shelf.** Each has colour, roughness, height and normal pictures at 2K, with its real size recorded.
   - `dark_rock_02`: setts.
   - `worn_rock_natural_01`: honey-buff sandstone for flags, kerbs, lintels, sills, quoins and projected ashlar.
   - `rough_plasterbrick_05`: mortar.
   - `sandstone_blocks_05`: stone blocks.
   - `brick_wall_10`: dark sooty brick.
   - The old red brick is the shelf's existing `brick_wall_02`. The road bed (grit in the joints) is the existing `SURFACE • gravel_road`.
   - To fetch them again: `python3 -I brief/surfaces/fetch_surfaces.py`.

2. **The names file:** `brief/store/materials/Photographed.md`.
   - It lists which material does which job: setts `SURFACE • dark_rock_02`; flags, kerbs, dressings and projected ashlar `SURFACE • worn_rock_natural_01`; mortar `SURFACE • rough_plasterbrick_05`; road bed `SURFACE • gravel_road`; bricks `BRICK • brick_wall_02` and `BRICK • brick_wall_10`; stone blocks `ASHLAR • sandstone_blocks_05`.
   - It also explains the `pp_piece` number, the `pp_atlas` layout and the dials, and ends with a traps section.
   - The first version went up at about 17:37, then I kept it current.

3. **Each piece its own part.**
   - Every SURFACE material now reads `pp_piece`, both from the mesh and from instanced copies.
   - For each piece it turns the picture within that face and shifts it, and makes the piece up to 12% lighter or darker.
   - It also turns the normal picture back by the same amount, so the bumps stay lit from the right side.
   - Pictures with a direction (bricks, planks, bark, corrugated iron and so on) are only shifted, never turned.
   - Each material has a `Pieces` node with two dials, `Turn` and `Shade`.
   - **Proof that nothing else changed:** I drew two old materials (`brick_wall_02` and `sandstone_cracks`) from the old file and from the new one, and 0 pixels differed. The test repeats this check every time it runs.

4. **Atlases: the whole bricks and blocks, found automatically.**
   - Found with `python3 brief/store/materials/src/find_atlas.py --check FOLDER`. The `--check` option draws the rectangles over the photograph so you can look at them, and I did.
   - `atlas/brick_wall_02.json`: 74 bricks.
   - `atlas/brick_wall_10.json`: 152 bricks.
   - `atlas/sandstone_blocks_05.json`: 21 blocks, 0.18 to 1.3 m long.
   - The three atlas materials read the `pp_atlas` layout for all four pictures. They have the same Weather dials and darkening as the SURFACE materials, plus per-piece shade.

5. **Rebuilt `Materials.blend`** with `python3 brief/store/materials/src/build_materials.py`. I checked the street's 45 materials node by node against the old file: no differences.

6. **Cards.** I looked at every one at full size.
   - The three atlas cards show a small brick or block panel.
   - The setts and flags cards show pieces laid side by side.
   - The other three new SURFACE cards came from `card.py`.
   - The atlas, setts and flags cards are drawn by a new script inside the plugin: `python3 brief/store/materials/src/photographed_cards.py`.

7. **Test:** `python3 tests/test_store_photographed.py` passes. It checks:
   - the named materials load with all four pictures;
   - two pieces with different numbers look different, and with no number the picture is pixel for pixel the same as before;
   - instanced copies differ (0.16 alike, against 0.98 alike when their numbers are equal);
   - turned pieces and half-turned bricks keep their bumps lit the right way;
   - the atlas units lie inside the picture, have brick or block shapes, stand higher than the mortar round them, and number 40 or more per brick set.
   - These also still pass: `test_store_materials`, `test_store_tools`, `test_store_street_ground`, `test_store_street_fronts`, `test_copy_case`.
   - `test_store_rules` fails only on the catalogue check, which is expected until you run `catalogue.py`.

**For the session**
- Add `tests/test_store_photographed.py` to `tests/run_tests.sh`. It isn't one of my files.
- Run `catalogue.py`.
- If anyone runs `card.py material all`, it will redraw the atlas cards as a useless sphere and cube. Afterwards, run `photographed_cards.py` again.

**What does not read well yet**
- The new sandstone (`worn_rock_natural_01`) is warmer and yellower than the street's old honey-grey stone. Next to the old pavement and dressing cards it looks orange-tan. I did not swap it, because the other helpers may already use that name.
- The sett stone has a few pale cracks, so some setts show a line across them. I have only seen it on cards, never in a night street. The setts are dry by default; for wet ones, copy the material and turn `Wet` up to 0.6–0.8.
- The old red bricks have chipped edges, so a few units may show a sliver of mortar at one end.
- An atlas holds only 74, 152 or 21 units, so a long wall repeats each one many times.

**Mistakes and how I fixed them**
- **Sett stone:** I first downloaded `dark_rock`, which has gold marble-like veins. I removed it and used `dark_rock_02`.
- **Block wall:** I first downloaded `medieval_blocks_03`, but its height picture is plain white. I removed it and used `sandstone_blocks_05`.
- **Dark brick:** the shelf's `dark_brick_wall` holds only about 35 whole bricks, under the 40 the tests ask for. I added `brick_wall_10` instead.
- **Atlas finder, first try:** it found only specks, because the old red brick's height picture barely shows the mortar. I rewrote it to find thin lines of mortar: first the courses, then the upright joints down each course, which must also lie lower than the brick faces either side.
- **Atlas finder, later errors:**
  - Bits of brick split at pale patches were counted as headers; dropped.
  - Narrow blocks were merged with their neighbours; fixed the spacing between joints for blocks.
  - One "brick" was really two bricks with a missed joint; units much longer than the rest are now dropped.
  - Units no higher than their surrounding mortar are now dropped.
- **Copies test:** my first measure of the instanced copies failed, though the picture showed the copies did differ. I switched to comparing how alike their patterns are.

**Files**

Changed:
- `brief/surfaces/fetch_surfaces.py`
- `brief/surfaces/manifest.json`
- `brief/surfaces/Surfaces.md`
- `brief/store/materials/src/build_materials.py`
- `brief/store/materials/Materials.blend`

Created:
- the five set folders in `brief/surfaces/`
- `brief/store/materials/Photographed.md`
- `brief/store/materials/atlas/` (3 files)
- `brief/store/materials/src/find_atlas.py`
- `brief/store/materials/src/photographed_cards.py`
- 8 cards in `brief/store/cards/materials/`: `BRICK - brick_wall_02`, `BRICK - brick_wall_10`, `ASHLAR - sandstone_blocks_05`, and `SURFACE -` `dark_rock_02`, `worn_rock_natural_01`, `rough_plasterbrick_05`, `sandstone_blocks_05`, `brick_wall_10`
- `tests/test_store_photographed.py`

Scratch folder: `/home/claude/store-work/pbr56/materials/`. It holds `notes.md`, the atlas check pictures, before and after comparison pictures, and a backup of the old `Materials.blend`.

---

## Traps

- This is the helper's own account. What the session checked afterwards is in the project story, log 56.
- The session tried to send it one more piece of work (bringing the sandstone toward the street's honey-grey) at 18:08; it could not be resumed (its record was too large to load), so the sandstone stays as photographed.
