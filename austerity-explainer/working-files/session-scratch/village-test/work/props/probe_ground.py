import bpy, sys, os, json
KIT='/home/user/Music/plugins/explainer-film/kit'
sys.path.insert(0, KIT+'/place-kit')
import place_kit as pk
out={}
for o in bpy.data.objects:
    if o.type=='MESH':
        bb=[o.matrix_world@__import__('mathutils').Vector(c) for c in o.bound_box]
        xs=[v.x for v in bb]; ys=[v.y for v in bb]; zs=[v.z for v in bb]
        out[o.name]=dict(role=o.get('place_role'),owner=o.get('place_owner'),verts=len(o.data.vertices),box=[min(xs),min(ys),min(zs),max(xs),max(ys),max(zs)])
    else:
        out[o.name]=dict(type=o.type)
print(json.dumps(out,indent=0)[:6000])
print('images', [i.name for i in bpy.data.images][:30])
import place_kit.wear.masks as m
mm=m.load_plan_masks()
print('masks', mm is not None)
if mm is not None:
    print('keep_clear tests', [ (x,y,pk.is_keep_clear(x,y)) for x,y in [(12.5,-5.8),(12,0.5),(20,5),(-17.5,6.0),(-32,6)]])
for x,y in [(12.5,-5.8),(-17.5,6),(-43,10.5),(-34.5,-14.5),(24,38),(-5,13.5),(4.8,-10.3)]:
    print(x,y,pk.ground_height_at(x,y))
