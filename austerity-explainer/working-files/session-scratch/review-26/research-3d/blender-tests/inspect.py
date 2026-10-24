import bpy, os
from mathutils import Vector
MODELS = '/home/user/Music/austerity-explainer/chapter-2-inflation/pictures/models'
bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)
for name in ['factory-a.glb', 'town.glb', 'props.glb']:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(MODELS, name))
    new = [o for o in bpy.data.objects if o not in before and o.type == 'MESH']
    mins = Vector((1e9,)*3); maxs = Vector((-1e9,)*3)
    for o in new:
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c); mins = Vector(map(min, mins, w)); maxs = Vector(map(max, maxs, w))
    print('BOUNDS', name, len(new), tuple(round(v,2) for v in mins), tuple(round(v,2) for v in maxs))
    print('   names', [o.name for o in new][:12])
