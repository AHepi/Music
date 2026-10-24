# Lists what the round 1 test lane holds (collections, object names), and the iron gates' parts.
import bpy, sys, os
from collections import defaultdict
by = defaultdict(list)
for o in bpy.data.objects:
    cs = ','.join(c.name for c in o.users_collection) or 'none'
    by[cs].append(f'{o.name}[{o.type}] loc={tuple(round(v,2) for v in o.location)} rotz={round(o.rotation_euler.z,2)} data={o.data.name if o.data else None}')
for cs, names in by.items():
    print('==', cs, len(names))
    for n in names[:60]:
        print('   ', n)
print('materials', sorted(m.name for m in bpy.data.materials))
print('world', bpy.context.scene.world.name if bpy.context.scene.world else None)
print('engine', bpy.context.scene.render.engine, bpy.context.scene.view_settings.exposure, bpy.context.scene.view_settings.look)
before=set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath='/home/user/Music/austerity-explainer/film-kit/assets/models/pit-village/props/iron-gates-pair.glb')
for o in bpy.data.objects:
    if o not in before:
        import mathutils
        bb=[o.matrix_world @ mathutils.Vector(c) for c in o.bound_box]
        print('GATE', o.name, o.type, o.parent.name if o.parent else None, [round(min(p[i] for p in bb),3) for i in range(3)], [round(max(p[i] for p in bb),3) for i in range(3)])
