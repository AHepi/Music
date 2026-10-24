import bpy
from mathutils import Vector
def bounds(o):
    pts=[o.matrix_world@Vector(c) for c in o.bound_box]
    return min(p.x for p in pts),max(p.x for p in pts),min(p.y for p in pts),max(p.y for p in pts),min(p.z for p in pts),max(p.z for p in pts)
for n in ['Step trench cheek west','Step trench cheek east','Coping near west stone 3','Coping near west stone 2','Wall near west panel 2','Wall near west panel 3','Step trench back wall','Step 1','Step 7','Step landing']:
    o=bpy.data.objects.get(n)
    if o: print(n, ['%.3f'%v for v in bounds(o)])
print([o.name for o in bpy.data.objects if o.name.startswith('Wall near west')])
