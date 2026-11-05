# Photographed materials

What this file is: which of the store's photographed materials are meant for the town street's stones, bricks and setts, and how a tool lets each piece show its own part of the photographs (decision 80). The pictures are Poly Haven sets (CC0) on the shelf, `brief/surfaces/`, used whole: colour, roughness, normal and height, at their real size.

## Which material for which job

| job | material | photographed set (one copy covers) |
|---|---|---|
| setts | `SURFACE • dark_rock_02` | dark weathered rock, no block pattern (2.0 x 2.0 m) |
| the road bed (the grit in the setts' joints) | `SURFACE • gravel_road` | gravel road (2.0 x 2.0 m) |
| flags | `SURFACE • worn_rock_natural_01` | honey-buff weathered sandstone, no joints (2.0 x 2.0 m) |
| kerbs and dressings (lintels, sills, quoins) | `SURFACE • worn_rock_natural_01` | the same sandstone |
| ashlar blocks, projected, one part per block | `SURFACE • worn_rock_natural_01` | the same sandstone |
| bricks, old red (atlas) | `BRICK • brick_wall_02` | old red brick wall in stretcher bond (2.0 x 2.0 m); its units in `atlas/brick_wall_02.json` |
| bricks, dark sooty (atlas) | `BRICK • brick_wall_10` | dark sooty brick in stretcher bond, pale mortar (1.9 x 1.9 m); its units in `atlas/brick_wall_10.json` |
| stone blocks (atlas) | `ASHLAR • sandstone_blocks_05` | honey sandstone blocks, rough-tooled faces (3.0 x 3.0 m); its units in `atlas/sandstone_blocks_05.json` |
| mortar | `SURFACE • rough_plasterbrick_05` | grey gritty lime render, no joints (1.5 x 1.5 m) |

The street's own materials (`COBBLES • ...`, `PAVEMENT • ...`, `STONE • worn honey-grey architectural dressings`, `Hand-painted sandstone • shade NN`) stay as they were and can still be asked for by name.

## Each piece its own part: the number `pp_piece`

A tool writes a float attribute named `pp_piece`, a random number from 0 to 1 for each piece (one brick, block, sett, flag or kerbstone):
- on the faces of a mesh (domain FACE), or
- on the points that carry instanced copies, so each copy gets it.

Every `SURFACE`, `BRICK` and `ASHLAR` material reads it, from the mesh and from the instancer:
- A `SURFACE` material turns and shifts its picture for each piece, so each piece shows its own part of the photographs, and makes it a little lighter or darker.
- A `BRICK` or `ASHLAR` material makes each piece a little lighter or darker (which unit it shows is the tool's choice, through `pp_atlas`).
- Where `pp_piece` is absent, a material draws exactly as before.

Each `SURFACE` material has a node `Pieces` with two dials: `Turn` (1 any angle, 0 never turned) and `Shade` (how much lighter or darker a piece may be; 0.12 is 12 per cent either way). `Turn` is 0 on the sets whose picture has a direction (bricks, blocks, planks, bark, corrugated iron, the weaves, `cobblestone_floor_01`, `old_stone_wall_02`, `damaged_plaster`): their pieces are only shifted. The `BRICK` and `ASHLAR` materials have the same node, `Shade` 0.15.

A picture is turned about the axis its face looks along most (a sett's top turns about the upright, a block's front about the axis out of the wall), so it stays flat in the face; its normal picture is turned back by the same amount, so the relief stays lit from the right side.

## Atlases: whole bricks and blocks found in the photographs

`atlas/<set>.json` lists every whole brick or block found in a wall photograph:

    {"material": "BRICK • brick_wall_02", "set": "brick_wall_02", "picture_size_m": [2.0, 2.0],
     "units": [[u0, v0, u1, v1], ...], "kinds": ["stretcher", "header", ...]}

- u and v run from 0 to 1 over the picture, v up (Blender's way).
- A unit is a rectangle on the brick's or block's face, a little inside its edges, so no mortar shows.
- `kinds` says for each unit whether it is a stretcher (the long face) or a header (the short end); it is there only for sets that have both. Both brick sets here are stretcher bond, so their files have no `kinds`: every unit is a stretcher face (0.19 to 0.27 m long and 0.05 to 0.07 m high, inside the joints).
- The stone blocks run from 0.18 to 1.3 m long and 0.26 to 0.37 m high.
- The units were found by `src/find_atlas.py` (it can draw them over the photograph to look at: `--check FOLDER`).

A wall tool gives each unit's front face its rectangle through a UV map named `pp_atlas`, and the unit's sides thin strips at that rectangle's edges. The atlas materials read `pp_atlas` for all four pictures (the normal picture through that UV map's own directions, so a unit turned half round still has its relief lit the right way).

## How these were made, and how to check them

- The sets are on the shelf through `brief/surfaces/fetch_surfaces.py`; the materials are built by `src/build_materials.py` (`pieces_group`, `atlas_material`); the atlas files by `src/find_atlas.py`.
- `tests/test_store_photographed.py` checks it all: the names here come in with their four pictures, pieces with different numbers draw differently (instanced copies too), a mesh without `pp_piece` draws pixel for pixel as before, and every atlas unit lies inside its picture, has a brick's or block's proportions, and stands higher than the joints round it.

## Dials

All of them, `SURFACE`, `BRICK` and `ASHLAR`, have the same `Weather` node as before: `Darken`, `Wet`, `Grime`, `Mud height`, `Mud color`, `Edge wear`, `Bump`. `SURFACE` materials also keep `Picture size` and `Normal picture`.

The setts are laid dry. For a wet street like the old `COBBLES • wet basalt` one, copy `SURFACE • dark_rock_02` (`mat.copy()`) and turn its `Wet` dial up (0.6 to 0.8): darker and glossy.

## Traps

- An atlas material on a mesh without the `pp_atlas` UV map draws one blurred corner of the photograph: it needs a tool that writes `pp_atlas` (the wall tool), not a plain box.
- `pp_piece` must be a float on the faces (or on the instancing points). Put on the corners of a mesh whose pieces share corners, it blends from one piece into the next, and a piece shows a smeared mix of parts.
- Two pieces given the same `pp_piece` show the same part of the photograph: give each its own random number.
- A `SURFACE` picture is turned only about the axis its face looks along. On a sloping or rounded face the turn changes where the face crosses from one side's projection to the next: keep pieces box-shaped, with flat faces.
- The shelf's `dark_brick_wall` has no atlas: its photograph covers only 1.05 m and holds about 35 whole bricks. `BRICK • brick_wall_10` is the dark sooty brick.
- An atlas holds only the whole units found (74 old red bricks, 152 dark bricks, 21 stone blocks); a long wall shows each many times, so turn some half round and vary their shade (the wall tool does).
- `card.py material` draws a sphere and a cube, which have no `pp_atlas`: run on an atlas material it draws a useless card. The cards of the atlas materials, and of the sett and flag stones laid in pieces, are drawn by `src/photographed_cards.py` (`python3 src/photographed_cards.py` redraws them all).
