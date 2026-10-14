# What this does: prints where the street's landmarks are in 3D (chimney top, wheel axles, eaves).
import bpy
from mathutils import Vector
def box(o):
    pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return [round(min(p[i] for p in pts), 3) for i in range(3)], [round(max(p[i] for p in pts), 3) for i in range(3)]
for o in bpy.data.objects:
    n = o.name.lower()
    if o.type == 'EMPTY' and ('wheel' in n or 'chimney' in n or 'lamp_' in n):
        print('MARK', o.name, tuple(round(v, 3) for v in o.matrix_world.translation))
    if o.type == 'MESH' and ('colliery' in n or 'chimney' in n and 'cottage' not in n or 'engine' in n or 'heapstead' in n):
        print('MESH', o.name, box(o))
for o in bpy.data.objects:
    if o.type == 'MESH' and o.name.startswith('left_row_a_cottage_02'):
        print('LEFTCOT', o.name, box(o))
