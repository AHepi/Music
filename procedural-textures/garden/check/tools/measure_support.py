import bpy, sys, json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
out=sys.argv[sys.argv.index('--')+1]
dg=bpy.context.evaluated_depsgraph_get()
def wm(o):
    ev=o.evaluated_get(dg); me=ev.to_mesh(); mw=ev.matrix_world
    v=[mw@x.co for x in me.vertices]; p=[tuple(q.vertices) for q in me.polygons]; ev.to_mesh_clear(); return v,p
def bvh(objs):
    V=[];P=[];off=0
    for o in objs:
        v,p=wm(o); V+=v; P+=[tuple(i+off for i in q) for q in p]; off+=len(v)
    return BVHTree.FromPolygons(V,P)
R={}
names=[n for n in ('Astra / Courtyard receiving ground','Life / pond bed') if n in bpy.data.objects]
under=bvh([bpy.data.objects[n] for n in names])
R['under_surfaces_used']=names
for i in range(4):
    p=bpy.data.objects[f'Bridge pier {i}']; v,_=wm(p)
    zmin=min(c.z for c in v); low=[c for c in v if c.z<zmin+0.01]
    # first surface hit going up from deep below, and down from above, at the pier's lowest points
    cl=[]
    for c in low[:20]:
        h=under.ray_cast(Vector((c.x,c.y,c.z+3.0)),Vector((0,0,-1)),6.0)   # topmost-first hit going down from high above
        # the bed / ground surface directly below: cast down from just above the pier bottom
        h2=under.ray_cast(Vector((c.x,c.y,c.z+0.01)),Vector((0,0,-1)),3.0)
        h3=under.ray_cast(Vector((c.x,c.y,c.z-0.01)),Vector((0,0,1)),3.0)
        cl.append((round(c.z-(h2[0].z if h2[0] else -9),3), None if h3[0] is None else round(h3[0].z-c.z,3)))
    R[p.name]={'zmin':round(zmin,3),'zmax':round(max(c.z for c in v),3),'gap_down_to_surface_m(first,second)':cl[:4]}
# stringers vs planks and piers
st=bpy.data.objects['Bridge stringers']; sv,sp=wm(st)
sb=BVHTree.FromPolygons(sv,sp)
runs=[o for o in bpy.data.objects if o.name.startswith('Astra / varied planks') and o.type=='MESH']
res={}
for r in runs:
    v,p=wm(r); b=BVHTree.FromPolygons(v,p); res[r.name]=len(sb.overlap(b))
R['stringers_overlap_pairs_with_plank_runs']=res
pres={}
for i in range(4):
    v,p=wm(bpy.data.objects[f'Bridge pier {i}']); b=BVHTree.FromPolygons(v,p); pres[f'pier{i}']=len(sb.overlap(b))
R['stringers_overlap_pairs_with_piers']=pres
# water level
pw=bpy.data.objects.get('Pond water')
if pw:
    v,_=wm(pw); R['pond_water_z_range']=[round(min(c.z for c in v),3),round(max(c.z for c in v),3)]
json.dump(R,open(out,'w'),indent=1); print('SUPPORT_DONE')
