import bpy, sys, json, math, numpy as np
sys.path.insert(0,'/home/user/Music/plugins/explainer-film/kit/place-kit')
import place_kit as pk
from place_kit import scene_read, names
out={}
objs=[o for o in bpy.data.objects if o.get('place_owner')=='cottages_north']
out['objects']={'A':sum(1 for o in objs if o.name.startswith('Cottage A')),'B':sum(1 for o in objs if o.name.startswith('Cottage B'))}
tri={'A':0,'B':0}; trib={'A':0,'B':0}
for o in objs:
    t=scene_read.triangle_count(o, evaluated=True); tag=o.name.split()[1]; tri[tag]+=t
    o.data.calc_loop_triangles(); trib[tag]+=len(o.data.loop_triangles)
out['triangles_after_modifiers']=tri; out['triangles_as_built']=trib
def world_pts(o):
    return scene_read.world_points(o, evaluated=False)
def parts_of(o):
    labels,n=scene_read.loose_part_labels(o.data)
    P=world_pts(o)
    return [P[labels==k] for k in range(n)]
g_ground={}
# footing widths and heights
for tag in 'AB':
    o=bpy.data.objects[f'Cottage {tag} footing']
    rows=[]
    for p in parts_of(o):
        lo,hi=p.min(0),p.max(0); ext=hi-lo
        rows.append({'long':round(float(max(ext[0],ext[1])),2),'width':round(float(min(ext[0],ext[1])),3),'height':round(float(ext[2]),3)})
    out[f'footing_{tag}']=rows
# steps, doors, floors
for tag in 'AB':
    st=bpy.data.objects[f'Cottage {tag} doorstep']; lo,hi=scene_read.world_bounds(st)
    gz=pk.ground_height_at((lo[0]+hi[0])/2,(lo[1]+hi[1])/2)
    out[f'doorstep_{tag}_rise']=round(float(hi[2]-gz),3)
    d=bpy.data.objects[f'Cottage {tag} door leaf']; lo,hi=scene_read.world_bounds(d)
    out[f'door_{tag}']={'height':round(float(hi[2]-lo[2]),3),'width':round(float(hi[0]-lo[0]),3),'bottom_above_step':round(float(lo[2]-(gz+out[f'doorstep_{tag}_rise'])),3)}
    f=bpy.data.objects[f'Cottage {tag} earth floor']; lo,hi=scene_read.world_bounds(f)
    gzf=pk.ground_height_at((lo[0]+hi[0])/2,(lo[1]+hi[1])/2)
    out[f'floor_{tag}_top_above_ground']=round(float(hi[2]-gzf),3)
# studs spacing on A south and north walls (centres of loose parts)
for wall in ('south','north','west','east'):
    o=bpy.data.objects[f'Cottage A {wall} wall studs']
    cs=sorted([float(p.mean(0)[0] if wall in('south','north') else p.mean(0)[1]) for p in parts_of(o)])
    # include posts
    pcs=[]
    for ob in objs:
        if ob.name.startswith('Cottage A post') and ob.get('place_role')=='timber.post':
            P=world_pts(ob); lo,hi=P.min(0),P.max(0)
            if wall=='south' and lo[1]<7.9 and (hi[1]-lo[1])<0.3: pcs.append(float((lo[0]+hi[0])/2))
            if wall=='north' and lo[1]>12.0: pcs.append(float((lo[0]+hi[0])/2))
            if wall in ('west','east') and ((lo[0]<-37.2 and wall=='west') or (hi[0]>-26.8 and wall=='east')) and ('lean-to' not in ob.name): pcs.append(float((lo[1]+hi[1])/2))
    allc=sorted(cs+pcs)
    gaps=np.diff(allc)
    out[f'stud_spacing_A_{wall}']={'count_studs':len(cs),'posts_in_line':len(pcs),'min_gap':round(float(gaps.min()),3),'max_gap':round(float(gaps.max()),3)}
# door posts and distinct posts (no two alike)
posts=[o for o in objs if o.get('place_role')=='timber.post']
sig=set()
leans=[]
for o in posts:
    P=world_pts(o); 
    sig.add(tuple(np.round(P.ravel()[:12]-P.ravel()[:3].tolist()*4,3)))
    zlo,zhi=P[:,2].min(),P[:,2].max()
    bot=P[P[:,2]<zlo+0.01].mean(0); top=P[P[:,2]>zhi-0.01].mean(0)
    leans.append(round(float(math.degrees(math.atan2(np.hypot(*(top-bot)[:2]),zhi-zlo))),2))
out['posts']={'count':len(posts),'distinct_shapes':len(sig),'lean_degrees':leans}
# ridge sag
for tag,xs_line in (('A',[-37.48,-33.85,-30.15,-26.52]),('B',[-8.58,-6.0,-3.42])):
    o=bpy.data.objects[f'Cottage {tag} ridge piece']
    out[f'ridge_{tag}_bottom_z_min_max']=None
    pts=[]
    for p in parts_of(o):
        pts.append(p)
    P=np.vstack(pts); 
    # bottom face z by x: take vertices with lowest z in each x-slice
    xs=np.unique(np.round(P[:,0],3)); zb=[]
    for x in xs:
        sel=P[np.abs(P[:,0]-x)<0.0006]; zb.append(float(sel[:,2].min()))
    zb=np.array(zb); out[f'ridge_{tag}_sag_cm']=round(float((zb.max()-zb.min())*100),1)
# chimney above ridge
th=bpy.data.objects['Cottage B thatch']; ch=bpy.data.objects['Cottage B chimney']
lo,hi=scene_read.world_bounds(th); clo,chi=scene_read.world_bounds(ch)
out['chimney_B']={'above_thatch_top_m':round(float(chi[2]-hi[2]),2),'height_m':round(float(chi[2]-clo[2]),2),'base_x':round(float(chi[0]-clo[0]),2)}
out['thatch_top_z_above_ground']={'A':round(float(scene_read.world_bounds(bpy.data.objects['Cottage A thatch'])[1][2]-pk.ground_height_at(-32,10)),2),'B':round(float(hi[2]-pk.ground_height_at(-6,9.5)),2)}
# distance to the high road centre line
road=[[-140,-34],[-110,-18],[-80,-6],[-45,-1.5],[-12,0.5],[20,2],[52,-2.5]]
def dist_to_poly(p):
    best=1e9
    for a,b in zip(road[:-1],road[1:]):
        a=np.array(a);b=np.array(b);t=np.clip(np.dot(p-a,b-a)/np.dot(b-a,b-a),0,1);best=min(best,np.linalg.norm(p-(a+t*(b-a))))
    return best
dmin=1e9
for o in objs:
    P=world_pts(o)[::3]
    for p in P[::max(1,len(P)//200)]: dmin=min(dmin,dist_to_poly(p[:2]))
out['nearest_to_high_road_centre_line_m']=round(float(dmin),2)
# bounding area of my part vs the pads
allp=np.vstack([world_pts(o)[::5] for o in objs]); out['part_bounds']={'min':np.round(allp.min(0),2).tolist(),'max':np.round(allp.max(0),2).tolist()}
# glass? lamps? shutters ajar
out['roles']=sorted(set(o.get('place_role') for o in objs))
out['glass_objects']=[o.name for o in objs if (o.get('place_role') or '').startswith('glass')]
out['lamps_in_scene']=[o.name for o in bpy.data.objects if o.type=='LIGHT']
out['cameras_in_scene']=[o.name for o in bpy.data.objects if o.type=='CAMERA']
json.dump(out,open(sys.argv[sys.argv.index('--')+1],'w'),indent=1)
print(json.dumps(out)[:3500])
