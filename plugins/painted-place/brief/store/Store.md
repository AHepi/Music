# Store

What this file is: the store's catalogue. Ready **parts** (things to place), **tools** (code that makes a thing from a line, a point or an object you give it) and ready **materials** a builder may use. Nothing in the store places itself: where things go is yours to decide. Using the store is optional; anything you build yourself is just as welcome.

## How to use it, from your own Blender script

```python
import sys
sys.path.insert(0, FOLDER + '/store/tools')     # FOLDER is your copy of the brief folder
import bpy
import store

store.names('parts')                                   # what is on offer
store.names('materials')
tent = store.add_part('bell_tent', location=(2.0, 8.0, 0.0), turn=30, seed=4)   # a part where you say; returns its root
store.use_material(my_wall, 'SURFACE • old_stone_wall_02')                       # a material on your own object
import lay_walkway                                     # a tool: give it a line, it makes the thing along it
lay_walkway.lay([(0, 0, 0), (1.5, 4, 0), (2, 9, 0.2)], width=0.6, seed=2)
store.prepare_for_render(bpy.context.scene)            # once, just before drawing
```

Each tool also answers `python3 <tool>.py --help`. `python3 store.py --list` prints everything the store holds. The cards (pictures of every part and material) are in `cards/`; `cards/parts - all.jpg` and `cards/materials - all.jpg` show them all at once.

## Conventions

- Metres; Z up; ground at z = 0 under a part's foot.
- A part's origin is at its foot. Its front (a door, a muzzle, a lamp's face) faces **−Y**, which is what Blender's front view shows. Turn it with `turn` (degrees about Z, counter-clockwise seen from above).
- `add_part` puts every part in its own collection under one root (an empty); move or turn the root to move the whole part. Options a part accepts are on its row below; `seed` changes its small irregularities.
- Materials come in three kinds:
  - `SURFACE • <name>`: a photographed surface from the shelf (`surfaces/`), laid from three sides at the photograph's real size, already darkened into the look's range. Each has dials you may turn from a script: `mat.node_tree.nodes['Weather'].inputs['Wet' | 'Grime' | 'Mud height' | 'Mud color' | 'Edge wear' | 'Bump' | 'Darken']` and `mat.node_tree.nodes['Picture size'].inputs['Scale']`. Turning a dial changes every object using that material; copy the material first (`mat.copy()`) to change one thing only.
  - `MADE • <name>`: materials made in code (old brass, old copper, glazed china, weathered boards with peeling paint, wet bark, puddle water, a wet-ground film, wet mud).
  - the street's materials (setts, flags, glass, lamps, iron, moss, weeds, soot, smoke), under their own names.
- A surface material reads two numbers from each object: its real scale (`pp_scale`, so a photograph is never stretched by an unapplied scale) and the height of the ground under it (`pp_ground`, for the mud dial). `add_part` and `use_material` record both; call `store.prepare_for_render(scene)` once before drawing to refresh the scale of everything you moved or scaled since.

<!-- catalogue starts: tools/catalogue.py writes everything between these two lines from the parts', tools' and materials' own descriptions -->
<!-- catalogue ends -->

## Traps

- The surface materials are laid at the photograph's real size: an object scaled up after `use_material` shows a stretched photograph until `store.prepare_for_render` runs.
- A part's front is −Y. A part turned with `turn=180` faces +Y.
- The puddle materials need the numbers the puddle tool writes on its meshes ('shallow', 'dry'); on your own mesh without them the water is deep all over and the film wet all over.
- The pictures are found on the shelf by file name. Copy the whole brief folder, never the store alone, or the surface materials draw pink.
