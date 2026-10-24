# lists the objects and materials of the lockout set that matter for the clip
import bpy
from mathutils import Vector
for o in bpy.data.objects:
    n = o.name.lower()
    cols = [c.name for c in o.users_collection]
    if any(k in n for k in ('brazier', 'fire', 'notice', 'name', 'board', 'post', 'flame')) or 'signs' in cols:
        if o.type == 'MESH':
            ws = [o.matrix_world @ Vector(c) for c in o.bound_box]
            lo = [min(v[i] for v in ws) for i in range(3)]; hi = [max(v[i] for v in ws) for i in range(3)]
            print(o.name, cols, [m.name for m in o.data.materials if m], 'min', [round(x, 2) for x in lo], 'max', [round(x, 2) for x in hi])
        else:
            print(o.name, o.type, cols, [round(x, 2) for x in o.matrix_world.translation])
