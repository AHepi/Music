# What this does: lists the lamp post prop's materials and where each sits, to find its glass.
import bpy, os, sys
from mathutils import Vector
folder = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(folder, 'gas-lamp-post.glb'))
for o in [o for o in bpy.data.objects if o.type == 'MESH']:
    for index, material in enumerate(o.data.materials):
        points = [o.matrix_world @ o.data.vertices[v].co for p in o.data.polygons if p.material_index == index for v in p.vertices]
        if points:
            print('MAT', o.name, material.name, 'x', round(min(p.x for p in points), 2), round(max(p.x for p in points), 2), 'y', round(min(p.y for p in points), 2), round(max(p.y for p in points), 2), 'z', round(min(p.z for p in points), 2), round(max(p.z for p in points), 2))
