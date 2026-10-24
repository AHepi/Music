"""My own measures of the forest part, from the saved scene (not from the stage's own numbers). Writes evidence.json."""
import bpy, json, math, sys, numpy as np, mathutils
from mathutils import Vector
from mathutils.kdtree import KDTree
KIT='/home/user/Music/plugins/explainer-film/kit'
sys.path.insert(0, KIT+'/place-kit')
import place_kit as pk
from place_kit import parts as pkp, scene_read
from place_kit.checks import views_and_world as vw
W='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-test/work/forest'
scene=bpy.context.scene
pkp.refresh_ground()
ev={}
BUILD=[('A',-32,10,11.1,4.8),('A store',-39,10,3.0,4.8),('B',-6,9.5,6.4,4.6),('C',-26,-10.5,7.4,4.6),('D',4,-8,3.7,4.4),('stable',24,39,9.8,6.0)]
rects=[(cx-sx/2,cy-sy/2,cx+sx/2,cy+sy/2) for _,cx,cy,sx,sy in BUILD]
CL=(-50,-32,60,50); YARD=(14,24,34,36)
HIGH=[(-140,-34),(-110,-18),(-80,-6),(-45,-1.5),(-12,0.5),(20,2),(52,-2.5),(85,-10),(115,-19),(140,-33)]
LANE=[(20,2),(20.5,10),(22,18),(24,26),(24.3,34.2)]
def samples(pl,step=0.5):
    pl=np.array(pl,float); out=[]
    for a,b in zip(pl[:-1],pl[1:]):
        n=max(1,int(np.linalg.norm(b-a)/step))
        for i in range(n): out.append(a+(b-a)*i/n)
    return np.array(out)
hs, ls = samples(HIGH), samples(LANE)
# road edge KD from the real road meshes
pts=[]
for o in scene.objects:
    if o.type=='MESH' and o.get('place_role')=='ground.dirt_road':
        me=o.data; n=len(me.vertices); co=np.empty(n*3); me.vertices.foreach_get('co',co); co=co.reshape(n,3)
        m=np.array(o.matrix_world); pts.append((co@m[:3,:3].T+m[:3,3])[:,:2])
pts=np.vstack(pts); pts=pts[::2]
kd=KDTree(len(pts)); [kd.insert((float(p[0]),float(p[1]),0),i) for i,p in enumerate(pts)]; kd.balance()
def road_edge(x,y): return kd.find((x,y,0))[2]
def centre_d(x,y): return float(min(np.hypot(hs[:,0]-x,hs[:,1]-y).min(), np.hypot(ls[:,0]-x,ls[:,1]-y).min()))
def wall_d(x,y):
    return min(math.hypot(max(r[0]-x,0,x-r[2]), max(r[1]-y,0,y-r[3])) for r in rects)
def incl(x,y): return CL[0]<=x<=CL[2] and CL[1]<=y<=CL[3]
def rim_depth(x,y): return min(x-CL[0],CL[2]-x,y-CL[1],CL[3]-y)

# ---- parts of every forest object
objs=[o for o in bpy.data.objects if o.get('place_owner')=='forest' and o.type=='MESH']
ev['objects_total_forest']=len(objs)
tri_total=0; max_tris=0
trunks=[]; crowns=[]; smalls=[]; LABELS={}
for o in objs:
    me=o.data; n=len(me.vertices)
    co=np.empty(n*3); me.vertices.foreach_get('co',co); co=co.reshape(n,3); m=np.array(o.matrix_world); w=co@m[:3,:3].T+m[:3,3]
    me.calc_loop_triangles(); t=len(me.loop_triangles); tri_total+=t; max_tris=max(max_tris,t)
    labels,k=scene_read.loose_part_labels(me); LABELS[o.name]=labels
    ftri=np.empty(t*3,dtype=np.int64); me.loop_triangles.foreach_get('vertices',ftri); ftri=ftri.reshape(-1,3)
    for i in range(k):
        mask=labels==i; v=w[mask]
        rec={'obj':o.name,'role':o.get('place_role'),'lo':v.min(0),'hi':v.max(0),'v':v,'label':i}
        # signed volume
        idx=-np.ones(n,dtype=np.int64); idx[mask]=np.arange(mask.sum()); tt=ftri[labels[ftri[:,0]]==i]
        if len(tt):
            tri=v[idx[tt]]; rec['vol']=float(np.einsum('ij,ij->i',tri[:,0],np.cross(tri[:,1],tri[:,2])).sum()/6)
        if o.name.startswith('Tree') and o.get('place_role')=='tree.bark': trunks.append(rec)
        elif o.name.startswith('Tree'): crowns.append(rec)
        else: smalls.append(rec)
ev['triangles_forest']=tri_total; ev['max_mesh_triangles']=max_tris
ev['trunk_count']=len(trunks); ev['crown_pieces']=len(crowns)
ev['hero_trunk_objects']=sum(1 for o in objs if o.name.startswith('Tree hero') and o.name.endswith('trunk'))
ev['cluster_trunk_objects']=sum(1 for o in objs if o.name.startswith('Tree cluster') and o.name.endswith('trunks'))
ev['trees_per_cluster']=sorted(int(sum(1 for t in trunks if t['obj']==o.name)) for o in objs if o.name.startswith('Tree cluster') and o.name.endswith('trunks'))
ev['inside_out_pieces']=sum(1 for r in trunks+crowns+smalls if r.get('vol',1)<0)
# sizes
heights=[]; foot=[]
for t in trunks:
    z0=t['lo'][2]; cx=(t['lo'][0]+t['hi'][0])/2; cy=(t['lo'][1]+t['hi'][1])/2
    g=[pkp.ground_probe(x,y) for x,y in pkp.box_footprint_points(t['lo'],t['hi'])]
    gz=max(a[0] for a in g if a)
    t['gz']=gz; t['seat']=float(z0-gz); t['x']=cx; t['y']=cy; t['h']=float(t['hi'][2]-gz)
    # trunk across at 1.3 m height
    sel=t['v'][np.abs(t['v'][:,2]-(gz+1.3))<0.6]
    t['dia']=float(2*np.mean(np.hypot(sel[:,0]-cx,sel[:,1]-cy))) if len(sel) else None
ev['trunk_seat_error_m']={'min':float(min(t['seat'] for t in trunks)),'max':float(max(t['seat'] for t in trunks))}
ev['trunk_height_m']={'min':float(min(t['h'] for t in trunks)),'max':float(max(t['h'] for t in trunks))}
TREE={}
for ti,t in enumerate(trunks): TREE[(t['obj'],t['label'])]=ti
for c in crowns:
    cx=(c['lo'][0]+c['hi'][0])/2; cy=(c['lo'][1]+c['hi'][1])/2
    best=min(range(len(trunks)),key=lambda ti:(trunks[ti]['x']-cx)**2+(trunks[ti]['y']-cy)**2)
    TREE[(c['obj'],c['label'])]=best
POLYV={}
for o in objs:
    if o.name.startswith('Tree'):
        me=o.data; npoly=len(me.polygons); a=np.empty(npoly*3,dtype=np.int64); me.polygons.foreach_get('vertices',a); POLYV[o.name]=a.reshape(-1,3)[:,0]
# crown top (tree height) per tree: crown piece centre near trunk
tops=[]; carried=0; overlap=[]
for t in trunks:
    near=[c for c in crowns if abs((c['lo'][0]+c['hi'][0])/2-t['x'])<8 and abs((c['lo'][1]+c['hi'][1])/2-t['y'])<8 and c['lo'][2]<t['hi'][2]<c['hi'][2]+0.01 and c['hi'][2]>t['hi'][2]]
    if near:
        carried+=1
        top=max(c['hi'][2] for c in near); tops.append(top-t['gz'])
        # how far the trunk's top end lies below the top of the crown piece that holds it, and above its bottom
        best=max(min(t['hi'][2]-c['lo'][2], c['hi'][2]-t['hi'][2]) for c in near)
        overlap.append(float(best))
ev['trees_with_crown_over_trunk_top']=carried
ev['tree_total_height_m']={'min':float(min(tops)),'max':float(max(tops))} if tops else None
ev['crown_over_trunk_top_depth_m_min']=float(min(overlap)) if overlap else None
# kind split: pine = has more than 3 stacked pieces of cone... use crown names via mesh: pines have 4-6 pieces of 22 verts
# clearances
fails={'wall_lt_14':0,'in_yard':0,'clearing_road_lt_10':0,'centre_lt_2':0,'clearing_not_rim':0,'se_of_building':0,'road_edge_lt_3':0}
mins={'wall':1e9,'clearing_road_edge':1e9,'road_edge_outside':1e9,'centre':1e9}
for t in trunks:
    x,y=t['x'],t['y']
    wd=wall_d(x,y); mins['wall']=min(mins['wall'],wd)
    if wd<14: fails['wall_lt_14']+=1
    if YARD[0]<=x<=YARD[2] and YARD[1]<=y<=YARD[3]: fails['in_yard']+=1
    ed=road_edge(x,y); cd=centre_d(x,y); mins['centre']=min(mins['centre'],cd)
    if cd<2.0: fails['centre_lt_2']+=1
    if incl(x,y):
        mins['clearing_road_edge']=min(mins['clearing_road_edge'],ed)
        if ed<10: fails['clearing_road_lt_10']+=1
        if rim_depth(x,y)>9.0: fails['clearing_not_rim']+=1
    else:
        mins['road_edge_outside']=min(mins['road_edge_outside'],ed)
        if ed<3.0: fails['road_edge_lt_3']+=1
    for r in rects:
        if x>r[2] and y<r[1] and math.hypot(x-r[2],y-r[1])<32: fails['se_of_building']+=1; break
ev['trunk_clearance_failures']=fails; ev['trunk_clearance_minimums_m']=mins
# trunks in clearing
ev['trunks_inside_clearing']=sum(1 for t in trunks if incl(t['x'],t['y']))
ev['trunks_30_to_150m_of_middle']=sum(1 for t in trunks if 30<=math.hypot(t['x']-5,t['y']-9)<=150)
# smalls: roads, stable distance, seating, sizes
sm={'stumps':[], 'logs':[], 'rocks':[]}
for r in smalls:
    if r['obj'].startswith(('Stump','Log','Rock')):
        key={'Stump':'stumps','Log ':'logs','Rock':'rocks'}['Stump' if r['obj'].startswith('Stump') else 'Rock' if r['obj'].startswith('Rock') else 'Log ']
        v=r['v']; ed=min(road_edge(float(p[0]),float(p[1])) for p in v[::max(1,len(v)//60)])
        g=max(a[0] for a in [pkp.ground_probe(x,y) for x,y in pkp.box_footprint_points(r['lo'],r['hi'])] if a)
        sm[key].append({'obj':r['obj'],'height':float(r['hi'][2]-r['lo'][2]),'size':[float(r['hi'][0]-r['lo'][0]),float(r['hi'][1]-r['lo'][1])],'road_edge_m':float(ed),'seat_m':float(r['lo'][2]-g),
                        'stable_m':float(math.hypot(max(rects[-1][0]-(r['lo'][0]+r['hi'][0])/2,0,(r['lo'][0]+r['hi'][0])/2-rects[-1][2]),max(rects[-1][1]-(r['lo'][1]+r['hi'][1])/2,0,(r['lo'][1]+r['hi'][1])/2-rects[-1][3])))})
ev['small']=sm
# bushes / ferns / moss grounded
gr=[]; inclr=0
for r in smalls:
    if r['obj'].startswith(('Bush','Fern','Forest moss')):
        g=max(a[0] for a in [pkp.ground_probe(x,y) for x,y in pkp.box_footprint_points(r['lo'],r['hi'])] if a)
        gr.append(r['lo'][2]-g)
        if r['obj'].startswith(('Bush','Fern')) and incl((r['lo'][0]+r['hi'][0])/2,(r['lo'][1]+r['hi'][1])/2): inclr+=1
ev['undergrowth_pieces']=sum(1 for r in smalls if r['obj'].startswith(('Bush','Fern')))
ev['undergrowth_objects']=sum(1 for o in objs if o.name.startswith(('Bush','Fern')))
ev['undergrowth_pieces_inside_clearing']=inclr
ev['undergrowth_moss_seat_m']={'min':float(min(gr)),'max':float(max(gr))}
# sightlines
cams={c.name:c for c in scene.objects if c.type=='CAMERA'}
LEN={'View wide':70,'View road_eye':100,'View stable_close':30,'View cottage_close':40}
sd={}
for name,c in cams.items():
    loc=np.array(c.matrix_world.translation)[:2]; f3=c.matrix_world.to_3x3()@Vector((0,0,-1)); f=np.array([f3.x,f3.y]); f/=np.linalg.norm(f)
    dmin=1e9
    for r in trunks+smalls:
        p=np.array([(r['lo'][0]+r['hi'][0])/2,(r['lo'][1]+r['hi'][1])/2])-loc
        if not r['obj'].startswith(('Tree','Stump','Log','Rock')): continue
        tt=float(np.clip(p@f,0,LEN[name])); d=float(np.linalg.norm(p-f*tt)); dmin=min(dmin,d)
    sd[name]=dmin
ev['sightline_min_distance_to_a_trunk_stump_log_or_rock_m']=sd
# ---- sun: share of the ground each view sees that is shadowed (the same method as the audit, a finer grid), and by whom
dg=bpy.context.evaluated_depsgraph_get()
sun=vw.strongest_sun(scene); sd_dir=vw.toward_sun(sun)
share={}; cover={}
for name,c in cams.items():
    fr=[Vector(p) for p in c.data.view_frame(scene=scene)]
    tr,br,bl,tl=fr; cols,rows=96,64
    turn=c.matrix_world.to_3x3(); origin=c.matrix_world.translation.copy()
    sh=0; gp=0; by={}; hitsTree=0; total=0; near=0; pertree={}
    for r_ in range(rows):
        for c_ in range(cols):
            u=(c_+0.5)/cols; v=(r_+0.5)/rows
            pt=tl+(tr-tl)*u+(bl-tl)*v; d=(turn@pt).normalized()
            hit,loc,nrm,idx,ob,mat=scene.ray_cast(dg,origin,d,distance=3000)
            total+=1
            if hit and ob is not None:
                if ob.get('place_owner')=='forest' and ob.get('place_role') in ('tree.bark','plant.foliage'):
                    hitsTree+=1
                    if (loc-origin).length<40: near+=1
                    if ob.name in POLYV:
                        lab=int(LABELS[ob.name][POLYV[ob.name][idx]]); ti=TREE.get((ob.name,lab))
                        if ti is not None: pertree[ti]=pertree.get(ti,0)+1
                if (ob.get('place_role') or '').startswith('ground.'):
                    gp+=1
                    blk=vw.shadow_caster(scene,dg,loc+nrm*0.02+sd_dir*0.02,sd_dir)
                    if blk is not None:
                        sh+=1; by[blk.name]=by.get(blk.name,0)+1
    share[name]={'ground_points':gp,'shadowed':sh,'share':sh/max(gp,1),'by':sorted(by.items(),key=lambda a:-a[1])[:4]}
    top=sorted(pertree.items(),key=lambda a:-a[1])[:3]
    cover[name]={'rays_hit_forest_share':hitsTree/total,'rays_hit_forest_within_40m_share':near/total,'largest_single_tree_share':(top[0][1]/total if top else 0.0),
                 'top_trees':[{'trunk_object':trunks[ti]['obj'],'share':n/total,'at':[round(trunks[ti]['x'],1),round(trunks[ti]['y'],1)],'distance_m':round(float(np.hypot(trunks[ti]['x']-origin.x,trunks[ti]['y']-origin.y)),1)} for ti,n in top]}
ev['shadowed_share_by_view']=share; ev['forest_frame_cover_by_view']=cover
ev['sun_direction_toward']=[round(float(x),3) for x in sd_dir]
def clean(o):
    if isinstance(o,dict): return {k:clean(v) for k,v in o.items()}
    if isinstance(o,(list,tuple)): return [clean(v) for v in o]
    if isinstance(o,np.floating): return float(o)
    if isinstance(o,np.integer): return int(o)
    if isinstance(o,np.ndarray): return o.tolist()
    return o
tag=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv and len(sys.argv)>sys.argv.index('--')+1 else 'evidence'
json.dump(clean(ev),open(f'{W}/{tag}.json','w'),indent=1)
print(json.dumps(clean(ev),indent=1)[:6000])
