import bpy, sys
from mathutils import Vector
bpy.ops.wm.read_factory_settings(use_empty=True)
for f in sys.argv[sys.argv.index('--')+1:]:
    before=set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=f)
    new=[o for o in bpy.data.objects if o not in before]
    print('FILE', f)
    for o in new:
        if o.type=='MESH':
            cs=[o.matrix_world@Vector(c) for c in o.bound_box]
            lo=[min(c[i] for c in cs) for i in range(3)]; hi=[max(c[i] for c in cs) for i in range(3)]
            print('  ', o.name, o.parent.name if o.parent else None, [round(v,3) for v in lo], [round(v,3) for v in hi], [m.name for m in o.data.materials])
        else:
            print('  ', o.name, o.type)
