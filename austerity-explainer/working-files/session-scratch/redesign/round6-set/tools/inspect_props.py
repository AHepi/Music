# What this does: prints the size and parts of a few props (scratch, round 6)
import bpy, os
from mathutils import Vector
KIT = '/home/user/Music/austerity-explainer/film-kit/assets/models'
for path in ('pit-village/props/handcart.glb', 'inflation-chapter-2-newcomers/props/crate-this-way-up.glb',
             'inflation-chapter-2-newcomers/props/steel-drum-diesel.glb', 'pit-village/props/brazier-drum.glb',
             'pit-village/props/hurricane-lantern.glb'):
    full = os.path.join(KIT, path)
    if not os.path.exists(full):
        print('missing', full); continue
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=full)
    new = [o for o in bpy.data.objects if o not in before]
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in new if o.type == 'MESH' for c in o.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
    print(path, 'low', [round(v, 3) for v in lo], 'high', [round(v, 3) for v in hi])
    for o in new:
        if o.type == 'MESH':
            p = [o.matrix_world @ Vector(c) for c in o.bound_box]
            l = [round(min(q[i] for q in p), 3) for i in range(3)]; h = [round(max(q[i] for q in p), 3) for i in range(3)]
            print('   ', o.name, [m.name for m in o.data.materials], l, h)
    for o in new:
        bpy.data.objects.remove(o, do_unlink=True)
