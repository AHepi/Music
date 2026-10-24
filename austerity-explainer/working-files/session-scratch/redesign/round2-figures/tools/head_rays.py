# What this does (scratch check): for a figure .glb, casts rays at the head from behind and the sides at
# several heights and says which material each ray meets first (hair, skin, cap, coat ...).
import math, os, sys
import bpy
from mathutils import Vector
arguments = sys.argv[sys.argv.index('--') + 1:]
folder, names = arguments[0], arguments[1:]
for name in names:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=os.path.join(folder, name + '.glb'))
    body = next(o for o in bpy.data.objects if o.type == 'MESH')
    depsgraph = bpy.context.evaluated_depsgraph_get()
    mesh = body.data
    skin_index = [i for i, m in enumerate(mesh.materials) if m.name == 'weathered skin'][0]
    # the head's middle: the skin vertices in the top 0.3 m
    top = max((body.matrix_world @ v.co).z for v in mesh.vertices)
    skin_vertices = set()
    for p in mesh.polygons:
        if p.material_index == skin_index:
            skin_vertices.update(p.vertices)
    head = [body.matrix_world @ mesh.vertices[i].co for i in skin_vertices if (body.matrix_world @ mesh.vertices[i].co).z > top - 0.30]
    centre = sum(head, Vector()) / len(head)
    print(f'== {name}: top {top:.3f}, head skin middle {tuple(round(v, 3) for v in centre)}')
    for label, direction in (('back', Vector((0, -1, 0))), ('back-left', Vector((-0.7, -0.7, 0))), ('left side', Vector((-1, 0, 0))), ('right side', Vector((1, 0, 0)))):
        row = []
        for dz in (0.10, 0.06, 0.03, 0.0, -0.03, -0.06, -0.09, -0.12, -0.15):
            target = centre + Vector((0, 0, dz))
            origin = target + direction * 1.0
            hit, location, normal, index, obj, matrix = bpy.context.scene.ray_cast(depsgraph, origin, -direction)
            row.append(f'{dz:+.2f}:{mesh.materials[mesh.polygons[index].material_index].name.split()[-1] if hit else "-"}')
        print(f'  {label:10s} ' + '  '.join(row))
