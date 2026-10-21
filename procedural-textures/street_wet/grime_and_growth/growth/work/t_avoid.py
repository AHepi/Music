import sys, time, bpy, json
import numpy as np
KIT='proc-work/kits/weathering'
sys.path.insert(0,KIT); sys.dont_write_bytecode=True
from apply import kit as kit_module
from masks import bus as bus_module
from harness import legacy_stack, layers
from growth import apply_growth, scatter, runner_growth
k=kit_module.Kit.load('pit_village_street', scene_id='street', strict=False)
bus_module.attach(k)
apply_growth.register(k)
k.prepare()
stack=legacy_stack.LegacyStack(k); stack.apply(pieces=True)
print('rubbish host', bpy.data.objects.get('rubbish_scatter'))
t=time.time()
k.apply(layers=['growth'])
gs=k.growth
print('avoid objs', gs.section.get('avoid_pieces_of'), 'attached', gs.attached, round(time.time()-t,2))
rub=runner_growth.rubbish_table(); print('rubbish pieces', len(rub))
R=np.array([[r['x'],r['y']] for r in rub])
def near(rows):
    w=[r for r in rows if r['kind'].startswith('weed')]
    c=0
    for p in w:
        if np.min(np.hypot(R[:,0]-p['x'],R[:,1]-p['y']))<=0.05: c+=1
    return len(w), c
rows=gs.table(); print('avoid .05', near(rows), len(rows))
gs.engine.set_dial('avoid_m',0.0)
rows=gs.table(); print('avoid 0', near(rows), len(rows))
gs.engine.set_dial('avoid_m',0.05)
from mathutils.bvhtree import BVHTree
from mathutils import Vector
dg=bpy.context.evaluated_depsgraph_get()
verts=[];tris=[]
n=0
for inst in dg.object_instances:
    if inst.is_instance and inst.parent and inst.parent.name=='rubbish_scatter':
        me=inst.object.data
        mw=inst.matrix_world
        base=len(verts)
        verts+= [mw@v.co for v in me.vertices]
        me.calc_loop_triangles()
        tris+= [(base+t.vertices[0],base+t.vertices[1],base+t.vertices[2]) for t in me.loop_triangles]
        n+=1
print('instances',n,'verts',len(verts),'tris',len(tris))
bvh=BVHTree.FromPolygons(verts,tris)
gs.engine.set_dial('avoid_m',0.05)
rows=gs.table()
w=[r for r in rows if r['kind'].startswith('weed')]
ds=[]
for p in w:
    loc,nor,idx,dist=bvh.find_nearest(Vector((p['x'],p['y'],p['z'])))
    ds.append(dist if dist is not None else 9)
ds=np.array(ds); print('face distance of weeds: <0.05:',int((ds<0.05).sum()),'of',len(ds),'pctl',np.percentile(ds,[5,25,50]))
cnt=0
mats=[]
for inst in dg.object_instances:
    if inst.is_instance and inst.parent and inst.parent.name=='rubbish_scatter':
        mats.append((inst.matrix_world.translation.copy(), inst.object.name))
T=np.array([[m[0].x,m[0].y,m[0].z] for m in mats])
print('instance origins sample', T[:3], 'rubbish_table sample', R[:3])
for p in w:
    d=np.hypot(T[:,0]-p['x'],T[:,1]-p['y']); i=int(np.argmin(d))
    if d[i]<=0.05 and cnt<4:
        loc,nor,idx,dist=bvh.find_nearest(Vector((p['x'],p['y'],p['z'])))
        print('weed',p['x'],p['y'],p['z'],'nearest origin',T[i],mats[i][1],'xy dist',round(float(d[i]),3),'face dist',round(dist,3)); cnt+=1
