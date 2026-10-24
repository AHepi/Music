import bpy, json
from mathutils import Vector
sc=bpy.context.scene
print('scene objs', len(bpy.data.objects), 'res', sc.render.resolution_x, sc.render.resolution_y, 'engine', sc.render.engine)
for o in bpy.data.objects:
    d = ''
    if o.type=='MESH':
        bb=[o.matrix_world@Vector(c) for c in o.bound_box]
        mn=[min(b[i] for b in bb) for i in range(3)]; mx=[max(b[i] for b in bb) for i in range(3)]
        d='tris=%d bounds=%s..%s'%(sum(len(p.vertices)-2 for p in o.data.polygons), [round(x,1) for x in mn],[round(x,1) for x in mx])
    elif o.type=='CAMERA':
        d='loc=%s rot=%s lens=%s clip=%s'%([round(x,2) for x in o.location],[round(x,3) for x in o.rotation_euler],o.data.lens,o.data.clip_end)
    elif o.type=='LIGHT':
        d='%s rot=%s energy=%s'%(o.data.type,[round(x,3) for x in o.rotation_euler],o.data.energy)
    print(o.name, o.type, o.get('place_role'), o.get('place_owner'), [c.name for c in o.users_collection], d)
print([c.name for c in bpy.data.collections])
