import bpy, sys, json
from mathutils import Vector
out={}
for o in bpy.data.objects:
    ow=o.get('place_owner')
    if o.type!='MESH' or ow in (None,'ground_and_roads','forest'): continue
    bb=[o.matrix_world@Vector(c) for c in o.bound_box]
    xs=[v.x for v in bb]; ys=[v.y for v in bb]; zs=[v.z for v in bb]
    out[o.name]=dict(owner=ow,role=o.get('place_role'),box=[round(min(xs),2),round(min(ys),2),round(min(zs),2),round(max(xs),2),round(max(ys),2),round(max(zs),2)])
json.dump(out,open(sys.argv[-1],'w'),indent=0)
print(len(out))
