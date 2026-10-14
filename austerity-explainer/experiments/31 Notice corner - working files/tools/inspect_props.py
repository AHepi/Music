# What this does: prints the size, origin and shape of a few props, to know which way they face.
import bpy, os, sys
from mathutils import Vector
folder = sys.argv[sys.argv.index('--') + 1]
for name in ('gas-lamp-wall-bracket.glb', 'kitchen-chair.glb', 'hurricane-lantern.glb', 'notice-on-board.glb'):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.join(folder, name))
    meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    points = [o.matrix_world @ Vector(c) for o in meshes for c in o.bound_box]
    lo = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    hi = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    print('PROP', name, 'min', tuple(round(v, 3) for v in lo), 'max', tuple(round(v, 3) for v in hi))
    for o in meshes:
        b = [o.matrix_world @ Vector(c) for c in o.bound_box]
        print('   part', o.name, [m.name for m in o.data.materials][:3], 'z', round(min(p.z for p in b), 3), round(max(p.z for p in b), 3),
              'x', round(min(p.x for p in b), 3), round(max(p.x for p in b), 3), 'y', round(min(p.y for p in b), 3), round(max(p.y for p in b), 3))
