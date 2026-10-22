import bpy
from mathutils import Vector
for o in sorted(bpy.data.objects, key=lambda o:o.name):
    if o.type!='MESH': continue
    if any(k in o.name for k in ('wall','Wall','ground','Raked','Pond water','Hills','plain','Hall roof','Shoji paper','Stone plinth','Open room','Maple leaves','Pine pads','Bamboo fence')):
        bb=[o.matrix_world@Vector(c) for c in o.bound_box]
        lo=[round(min(v[i] for v in bb),2) for i in range(3)]; hi=[round(max(v[i] for v in bb),2) for i in range(3)]
        print(f'{o.name:34s} lo={lo} hi={hi}')
