# What this does: finds where the glass of the wall-bracket lamp sits, to know which end meets the wall.
import bpy, os, sys
from mathutils import Vector
folder = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(folder, 'gas-lamp-wall-bracket.glb'))
o = [o for o in bpy.data.objects if o.type == 'MESH'][0]
for index, material in enumerate(o.data.materials):
    points = [o.matrix_world @ o.data.vertices[v].co for p in o.data.polygons if p.material_index == index for v in p.vertices]
    if points:
        c = sum(points, Vector()) / len(points)
        print('MAT', material.name, 'centre', tuple(round(v, 3) for v in c), 'y range', round(min(p.y for p in points), 3), round(max(p.y for p in points), 3), 'z range', round(min(p.z for p in points), 3), round(max(p.z for p in points), 3))
