You are the materials helper. Your scratch folder is `/home/claude/store-work/pbr56/materials/`. Your clock: finish by 18:50 by this computer's clock.

Work in this order:

1. **Choose the sets** (Poly Haven, CC0; `https://api.polyhaven.com` lists them) and add them to the shelf with `brief/surfaces/fetch_surfaces.py`: colour, roughness, height and normal pictures at 2K, with the real size in the manifest. Look at each one before choosing. The town street's tenements are honey-grey sandstone, its setts dark basalt or whinstone, and its pavement sandstone flags. You need:
   - (a) For setts: a dark granite, basalt or whinstone surface with no block pattern in it.
   - (b) For flags, kerbs, dressings, and ashlar blocks projected one part per block: a buff or honey sandstone surface with no joints in it (a tooled or weathered sandstone face).
   - (c) For mortar: a lime mortar or grit.
   - (d) For brick atlases: two or three brick walls with a clear, regular bond and the mortar showing in the height picture. At least an old red brick and a dark sooty brick; the shelf already has `brick_wall_02` and `dark_brick_wall`.
   - (e) For a stone-block atlas: a dressed stone-block wall (Poly Haven has `large_sandstone_blocks_01` and `medieval_blocks_03`, among others).
2. **Write `brief/store/materials/Photographed.md`** with the names, as soon as you have decided them. The other two helpers are waiting on it.
3. **Per-piece variety in every SURFACE material, and in your new ones.**
   - Read `pp_piece` from the geometry and from the instancer.
   - Turn and shift the projected coordinates per piece, and vary the brightness slightly.
   - With the attribute absent, everything draws exactly as before. Prove it: an existing SURFACE card, or a test picture, must come out identical pixel for pixel before and after your change.
4. **Atlases.**
   - Find each whole brick or block in each atlas set's height picture (or colour picture). Leave out units cut by the picture's edge, and any that sit on mortar.
   - Write the JSON (see the agreement). Check it by drawing the found rectangles over the picture and looking at it.
   - Build an atlas material per set. It reads the UV map `pp_atlas` for colour, roughness, normal (through that UV map's tangents) and height (as bump). It varies each piece's brightness by `pp_piece`, and has the same Weather dials and the same darkening into the look as the SURFACE materials.
   - Brick atlas materials are named `BRICK • <set>`, stone-block ones `ASHLAR • <set>`. New plain surfaces stay `SURFACE • <set>`.
5. **Cards.**
   - Draw cards for the new materials.
   - An atlas material needs a test object with `pp_atlas` UVs: draw its card yourself, under the same light as the other cards, as a small panel of bricks or blocks, each mapped to a unit.
   - A plain surface's card can show several pieces with different `pp_piece` values side by side.
6. **Rebuild and test.**
   - Rebuild `Materials.blend` with `brief/store/materials/src/build_materials.py`. The street's 45 materials stay untouched.
   - Tests go in `tests/test_store_photographed.py`. They check that:
     - the new materials load by name, with all four pictures used;
     - two pieces with different `pp_piece` draw differently, and with no attribute nothing changes;
     - instanced copies differ: a point cloud with `pp_piece` instancing one cube gives copies that differ;
     - the atlas units lie inside the picture, have brick or block proportions, sit on high ground in the height picture (not on mortar), and are enough of them (40 or more per brick set).
   - Run `tests/test_store_materials.py` and `tests/test_store_tools.py` too: they must still pass.
