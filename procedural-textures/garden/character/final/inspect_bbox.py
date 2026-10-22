import bpy, json
from mathutils import Vector
dg = bpy.context.evaluated_depsgraph_get()
out = {}
for n in ('Hall roof', 'Roof carrying frame', 'Hall posts', 'Eave soffit', 'Veranda step', 'Lantern base', 'Pond water', 'Maple trunk', 'Pine trunk', 'Water basin'):
    o = bpy.data.objects.get(n)
    if o is None:
        continue
    oe = o.evaluated_get(dg)
    pts = [o.matrix_world @ Vector(c) for c in oe.bound_box]
    out[n] = [[round(min(p[i] for p in pts), 2) for i in range(3)], [round(max(p[i] for p in pts), 2) for i in range(3)]]
for n in ('photo', 'veranda'):
    o = bpy.data.objects[n]
    out[n] = [list(map(lambda v: round(v, 3), o.location)), list(map(lambda v: round(v, 3), o.rotation_euler)), o.data.lens]
print('BBOX', json.dumps(out))
