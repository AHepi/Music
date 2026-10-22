import bpy, numpy as np
from mathutils import Vector
for n in ('Veranda step', 'Veranda step, lower', 'Stone plinth'):
    o = bpy.data.objects[n]
    V = np.array([(o.matrix_world @ Vector(c)) for c in o.bound_box])
    print(n, 'min', V.min(0).round(3), 'max', V.max(0).round(3), 'verts', len(o.data.vertices), 'mats', [s.material.name for s in o.material_slots])
dg = bpy.context.evaluated_depsgraph_get()
g = bpy.data.objects.get('Astra / Courtyard receiving ground')
ev = g.evaluated_get(dg)
for (x, y) in ((1.4, 3.9), (2.2, 3.9), (3.0, 3.9), (2.2, 3.5), (2.2, 4.2), (1.0, 4.3)):
    org = Vector((x, y, 2.0)); ok, loc, nrm, idx = ev.ray_cast(org, Vector((0, 0, -1)))
    print('ground', (x, y), loc.z if ok else None)
