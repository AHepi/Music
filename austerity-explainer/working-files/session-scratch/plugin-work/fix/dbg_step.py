import sys, bpy, bmesh
sys.path.insert(0,'/home/user/Music/plugins/explainer-film/kit/place-kit')
from place_kit import names, parts
from place_kit.checks import construction
for o in list(bpy.data.objects): bpy.data.objects.remove(o)
m=bpy.data.meshes.new('G'); m.from_pydata([(-8,-8,0),(8,-8,0),(8,8,0),(-8,8,0)],[],[(0,1,2,3)])
g=bpy.data.objects.new('Ground',m); bpy.context.scene.collection.objects.link(g); g[names.ROLE]='ground.earth'
def box(name,size,loc,role):
    me=bpy.data.meshes.new(name); b=bmesh.new(); bmesh.ops.create_cube(b,size=1.0)
    for v in b.verts: v.co.x*=size[0]; v.co.y*=size[1]; v.co.z*=size[2]
    b.to_mesh(me); b.free(); o=bpy.data.objects.new(name,me); bpy.context.scene.collection.objects.link(o); o.location=loc; o[names.ROLE]=role; return o
box('step 1',(0.4,1.2,0.17),(0,0,0.085),'stone.step')
box('step 2',(0.4,1.2,0.34),(0.4,0,0.17),'stone.step')
r=construction.check_construction({})
for k,v in r['objects'].items(): print(k, v['rise_m'], v['carried'], v.get('via'), v.get('seat_ground_m'))
bpy.context.view_layer.update()
print(parts.ground_under_box((-0.2,-0.6,0),(0.2,0.6,0.17)))
