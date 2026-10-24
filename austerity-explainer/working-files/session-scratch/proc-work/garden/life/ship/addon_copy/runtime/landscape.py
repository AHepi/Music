"""Portable landscape generation with explicit inputs and reversible source retention.
No scene-name lookup, global hooks, external packages, world edits, or hidden install.
Outputs are ordinary native meshes: they survive save/reopen without Python handlers.
"""
import hashlib
import json
import math
import uuid
import bpy
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
from . import spec as contract

PREFIX='Astra / '
OWNER='astra_runtime_owner'


def mesh_digest(mesh):
    payload={'v':[[round(float(c),7) for c in v.co] for v in mesh.vertices],
             'f':[list(p.vertices) for p in mesh.polygons],
             'm':[p.material_index for p in mesh.polygons]}
    return hashlib.sha256(json.dumps(payload,separators=(',',':')).encode()).hexdigest()


def ensure_source(obj):
    if obj is None or obj.type!='MESH' or not obj.data.vertices or not obj.data.polygons:
        raise ValueError('Select a nonempty mesh surface as the explicit receiver')
    if obj.library or obj.override_library or obj.data.library or obj.data.override_library:
        raise ValueError('Linked and overridden sources are not supported')
    if obj.get(OWNER) or obj.get('astra_landscape_active'):
        raise ValueError('Choose the retained source or restore its active landscape before generating again')
    if obj.modifiers or obj.data.shape_keys or obj.animation_data or obj.constraints:
        raise ValueError('Receiver must be a static height-field mesh without modifiers, shape keys or constraints')
    if len(obj.users_scene)!=1:
        raise ValueError('A receiver shared across scenes is outside this contract')
    a=obj.matrix_world.to_3x3();cols=[a.col[i] for i in range(3)];lengths=[v.length for v in cols]
    if min(lengths)<1e-5 or max(lengths)/min(lengths)>1.00001 or a.determinant()<=0 or any(abs(cols[i].dot(cols[j]))>1e-5*lengths[i]*lengths[j] for i in range(3) for j in range(i)):
        raise ValueError('Receiver needs a positive uniform-scale, nonsheared transform; apply nonuniform scale first')
    if len(obj.data.vertices)>300000:
        raise ValueError('Receiver exceeds the 300000-vertex interactive budget')
    # Reject overhangs/walls; one local XY sample per vertex is a conservative heightfield contract.
    seen=set()
    for v in obj.data.vertices:
        if not all(math.isfinite(c) for c in v.co):raise ValueError('Non-finite receiver vertex')
        key=(round(v.co.x,7),round(v.co.y,7))
        if key in seen:raise ValueError('Receiver must be an open top heightfield, without duplicate XY vertices or underside')
        seen.add(key)
    for p in obj.data.polygons:
        if p.normal.z<.25:raise ValueError('Receiver contains downward or near-vertical faces; use an upward open surface')
    return {'mesh_sha256':mesh_digest(obj.data),'world_scale':lengths[0],
            'bounds':[min(v.co.x for v in obj.data.vertices),min(v.co.y for v in obj.data.vertices),
                      max(v.co.x for v in obj.data.vertices),max(v.co.y for v in obj.data.vertices)]}



def _cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def _inside_triangle(p,tri):
    signs=[_cross(a,b,p) for a,b in zip(tri,tri[1:]+tri[:1])]
    return min(signs)>=-1e-10 or max(signs)<=1e-10

def _segments_intersect(a,b,c,d):
    if max(a[0],b[0])+1e-10<min(c[0],d[0]) or max(c[0],d[0])+1e-10<min(a[0],b[0]) or max(a[1],b[1])+1e-10<min(c[1],d[1]) or max(c[1],d[1])+1e-10<min(a[1],b[1]):return False
    return _cross(a,b,c)*_cross(a,b,d)<=1e-16 and _cross(c,d,a)*_cross(c,d,b)<=1e-16

def _triangle_capsule(tri,a,b,radius):
    if _inside_triangle(a,tri) or _inside_triangle(b,tri):return True
    if any(contract.segment_distance(p,a,b)<=radius+1e-9 for p in tri):return True
    for c,d in zip(tri,tri[1:]+tri[:1]):
        if _segments_intersect(a,b,c,d) or min(contract.segment_distance(a,c,d),contract.segment_distance(b,c,d))<=radius+1e-9:return True
    return False

def _triangle_rectangle(tri,box):
    lo,hi=box['min'],box['max'];corners=[lo,(hi[0],lo[1]),hi,(lo[0],hi[1])]
    if any(lo[0]-1e-9<=p[0]<=hi[0]+1e-9 and lo[1]-1e-9<=p[1]<=hi[1]+1e-9 for p in tri) or any(_inside_triangle(p,tri) for p in corners):return True
    return any(_segments_intersect(a,b,c,d) for a,b in zip(tri,tri[1:]+tri[:1]) for c,d in zip(corners,corners[1:]+corners[:1]))

def relief_plan(mesh,s):
    """Precompute conservative polygon protection before creating Blender IDs.
    Every original polygon touching a rectangle, swept path capsule or wet source
    triangle has ALL its vertices frozen. Any triangulation then has zero vertical
    delta throughout that polygon, including interiors missed by vertex masks.
    This may extend protection by one face; it never infers structural footprints.
    """
    mesh.calc_loop_triangles();frozen_polygons=set();water=s['water']['level']
    for triangle in mesh.loop_triangles:
        coords=[mesh.vertices[i].co for i in triangle.vertices];tri=[(p.x,p.y) for p in coords]
        hit=water is not None and min(p.z for p in coords)<=water+1e-9
        if not hit:hit=any(_triangle_rectangle(tri,r) for r in s['protected'])
        if not hit:hit=any(_triangle_capsule(tri,a,b,path['width']/2) for path in s['paths'] for a,b in zip(path['points'],path['points'][1:]))
        if hit:frozen_polygons.add(triangle.polygon_index)
    frozen={i for p in frozen_polygons for i in mesh.polygons[p].vertices}
    raw=[contract.relief(v.co.x,v.co.y,v.co.z,s) for v in mesh.vertices]
    offsets=[0. if i in frozen else d for i,d in enumerate(raw)]
    return offsets,{'policy':'Freeze every vertex of every source polygon intersecting explicit protected rectangles, swept path capsules or source water',
                    'frozen_polygons':len(frozen_polygons),'total_polygons':len(mesh.polygons),'frozen_vertices':len(frozen),
                    'conservatively_suppressed_vertices':sum(raw[i]>1e-8 for i in frozen),'protected_polygon_max_delta':max((offsets[i] for i in frozen),default=0.),
                    'interpolation_bound':'Exactly zero vertical displacement throughout every protected polygon; conservative extension up to the full intersecting source polygon'}


def material(name,color,owner,rough=.9):
    m=bpy.data.materials.new(PREFIX+name);m.use_nodes=True;m[OWNER]=owner
    m.diffuse_color=(*color,1)
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough
    return m


def make_mesh(name,vs,fs,col,owner,materials=(),indices=()):
    me=bpy.data.meshes.new(PREFIX+name+' mesh');me.from_pydata(vs,[],fs);me.update();me[OWNER]=owner
    ob=bpy.data.objects.new(PREFIX+name,me);col.objects.link(ob);ob[OWNER]=owner
    for m in materials:me.materials.append(m)
    for p,idx in zip(me.polygons,indices):p.material_index=idx
    return ob


def _cleanup(owner):
    # Only IDs created by this exact transaction are ever removed.
    for ob in list(bpy.data.objects):
        if ob.get(OWNER)==owner:bpy.data.objects.remove(ob,do_unlink=True)
    for col in list(bpy.data.collections):
        if col.get(OWNER)==owner:bpy.data.collections.remove(col)
    for family in [bpy.data.meshes,bpy.data.materials]:
        for item in list(family):
            if item.get(OWNER)==owner and item.users==0:family.remove(item)


def _sample(bvh,x,y,top,bottom):
    point,normal,_,_=bvh.ray_cast(Vector((x,y,top)),Vector((0,0,-1)),top-bottom)
    return point,normal


def _palette(kind,owner):
    colors={'pebbles':[(.21,.245,.23),(.32,.305,.25),(.11,.15,.14),(.245,.21,.16)],
            'moss':[(.035,.075,.022),(.085,.15,.04),(.15,.22,.065),(.055,.105,.03)],
            'planks':[(.19,.10,.045),(.255,.145,.07),(.31,.19,.095),(.22,.125,.052),(.35,.22,.115),(.27,.16,.075),(.21,.11,.052)]}[kind]
    return [material(kind+' tone '+str(i),c,owner) for i,c in enumerate(colors)]


def _piece(kind,x,y,radius,height,rng,bvh,top,bottom,water_level=None):
    """Every perimeter vertex is seated by a receiver query, not just the centre."""
    n=7 if kind=='pebbles' else 12
    aspect=rng.uniform(.62,.97);yaw=rng.random()*math.tau
    footprint=[]
    for i in range(n):
        a=i*math.tau/n
        lobed=(rng.uniform(.83,1.12) if kind=='pebbles' else .88+.11*math.sin(3*a+yaw)+rng.uniform(-.035,.035))
        dx=radius*math.cos(a)*lobed;dy=radius*aspect*math.sin(a)*lobed
        xx=x+dx*math.cos(yaw)-dy*math.sin(yaw);yy=y+dx*math.sin(yaw)+dy*math.cos(yaw)
        p,normal=_sample(bvh,xx,yy,top,bottom)
        if p is None or normal.z<.65 or (water_level is not None and p.z<=water_level+.008):return None
        footprint.append((xx,yy,p.z))
    zs=[p[2] for p in footprint]
    if max(zs)-min(zs)>max(radius*.8,height*2.2):return None
    centre,normal=_sample(bvh,x,y,top,bottom)
    if centre is None:return None
    vs=[];fs=[];idx=[];embed=min(.008,height*.15)
    stone_tone=rng.choice([0,0,0,2,2,3,3,1])
    # Three seated rings with a noncircular, volumetric crown.
    rings=[(1.,0),(.78,.63),(.38,.91)] if kind=='moss' else [(.78,0),(1.,.38),(.68,.84)]
    for shrink,rise in rings:
        for xx,yy,z in footprint:
            xx=x+(xx-x)*shrink;yy=y+(yy-y)*shrink
            q,nn=_sample(bvh,xx,yy,top,bottom)
            if q is None:return None
            vs.append((xx,yy,q.z-embed+height*rise))
    for ring in range(2):
        for k in range(n):
            fs.append((ring*n+k,ring*n+(k+1)%n,(ring+1)*n+(k+1)%n,(ring+1)*n+k))
            idx.append(0 if kind=='moss' and ring==0 else (1 if kind=='moss' else (stone_tone if rng.random()<.85 else max(0,stone_tone-1))))
    vs.append((x+radius*.06,y-radius*.03,centre.z+height));c=len(vs)-1
    for k in range(n):fs.append((2*n+k,2*n+(k+1)%n,c));idx.append(1 if kind=='moss' else (stone_tone if rng.random()<.85 else max(0,stone_tone-1)))
    fs.append(tuple(range(n-1,-1,-1)));idx.append(0)
    if kind=='moss':
        # Broad low leaflets are rooted in the cushion. This is not detached hair.
        for k in range(5):
            a=rng.random()*math.tau;rr=rng.uniform(.12,.57)*radius
            xx=x+rr*math.cos(a);yy=y+rr*aspect*math.sin(a);q,nn=_sample(bvh,xx,yy,top,bottom)
            if q is None:continue
            z=q.z+height*(.89-.42*rr/radius);w=radius*rng.uniform(.05,.095);h=height*rng.uniform(.15,.28)
            off=len(vs);vs.extend([(xx-w,yy,z),(xx+w,yy,z),(xx+w*.25,yy+w*.35,z+h),(xx-w*.25,yy+w*.35,z+h)])
            fs.append((off,off+1,off+2,off+3));idx.append(2 if k%3 else 3)
    return vs,fs,idx,{'center':[x,y,centre.z],'radius':radius,'height':height,
                        'perimeter_support_spread':max(zs)-min(zs),'perimeter_samples':n,'embed':embed}



def _moss_body(s,bvh,top,bottom):
    """Closed, terrain-conforming body with interpolated organic contours.
    Marching triangles clip signed habitat fields, avoiding square cell-cut borders.
    The body tapers to the receiving surface at the edge, with gravel-dominant gaps.
    """
    vs=[];fs=[];materials=[];bodies=0
    if s['moss']['density']<=0:return vs,fs,materials,bodies
    scale=s['detail_scale'];height=s['moss']['body_height']*scale
    step=max(.075,s['moss']['radius']*.45)*scale
    seedphase=contract.stable_rng(s['seed'],'moss-body-shape').random()*math.tau
    for patch in sorted(s['moss']['patches'],key=lambda p:p['id']):
        cx,cy=patch['center'];rx,ry=patch['radius'];nx=max(4,min(100,math.ceil(2*rx/step)));ny=max(4,min(100,math.ceil(2*ry/step)))
        grid={};local_vertices=[];lookup={};faces=[]
        def field(x,y):
            r2=((x-cx)/rx)**2+((y-cy)/ry)**2
            edge=.68+.13*math.sin(x*5.1+y*3.7+seedphase)+.08*math.sin(y*8.3-x*2.1-seedphase)
            p,n=_sample(bvh,x,y,top,bottom)
            if p is None or n.z<.72:return -1.,p
            level=s['water']['level'];water=1 if level is None else (p.z-level-.015)/.15
            contact=contract.zone_field(x,y,s['contacts']);shelter=contract.zone_field(x,y,s['shelter'])
            shore=0 if level is None else contract.clamp(1-(p.z-level)/s['water']['shore_reach'])
            habitat=max(shore,contact*s['moss']['contact_influence'],shelter*s['moss']['shelter_influence'])
            eligibility=patch['weight']*(.2+.8*habitat)*min(1,s['moss']['density']/13)-.18
            gravel=contract.zone_field(x,y,s['pebbles']['patches']) if s['pebbles']['density'] else 0
            return min(edge-r2,contract.clearance(x,y,s)/.3,water,eligibility,.69-gravel),p
        for j in range(ny+1):
            for i in range(nx+1):
                x=cx-rx+2*rx*i/nx;y=cy-ry+2*ry*j/ny;f,p=field(x,y);grid[(i,j)]=(x,y,f)
        def clip(poly):
            out=[]
            for a,b in zip(poly,poly[1:]+poly[:1]):
                ina=a[2]>=0;inb=b[2]>=0
                if ina:out.append(a)
                if ina!=inb:
                    t=a[2]/(a[2]-b[2]);out.append((a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1]),0.))
            return out
        def vertex(p):
            x,y,f=p;key=(round(x,7),round(y,7))
            if key in lookup:return lookup[key]
            value,hit=field(x,y)
            if hit is None:return None
            h=.003+height*.63*contract.smooth(max(0,value)/.18)
            idx=len(local_vertices);lookup[key]=idx;local_vertices.append((x,y,hit.z,h));return idx
        for j in range(ny):
            for i in range(nx):
                a=grid[(i,j)];b=grid[(i+1,j)];c=grid[(i+1,j+1)];d=grid[(i,j+1)]
                for tri in [(a,b,c),(a,c,d)]:
                    poly=clip(list(tri))
                    if len(poly)<3:continue
                    # Vertex signs alone can miss a narrow protected footprint inside a cell.
                    # Discard any clipped face intersecting it, conservatively by one body cell.
                    triangles=[[(p[0],p[1]) for p in (poly[0],poly[k],poly[k+1])] for k in range(1,len(poly)-1)]
                    if any(_triangle_rectangle(tr,r) for tr in triangles for r in s['protected']):continue
                    if any(_triangle_capsule(tr,a,b,path['width']/2) for tr in triangles for path in s['paths'] for a,b in zip(path['points'],path['points'][1:])):continue
                    ids=[vertex(p) for p in poly]
                    if None in ids or len(set(ids))<3:continue
                    # Clipping retains the input CCW winding; no flipped annuli.
                    faces.append(ids)
        if not faces:continue
        off=len(vs);N=len(local_vertices)
        vs.extend((x,y,z+h) for x,y,z,h in local_vertices);vs.extend((x,y,z-.004) for x,y,z,h in local_vertices)
        boundary={}
        for face in faces:
            ids=tuple(off+k for k in face);fs.append(ids);materials.append(1)
            fs.append(tuple(i+N for i in reversed(ids)));materials.append(0)
            for a,b in zip(ids,ids[1:]+ids[:1]):
                key=tuple(sorted((a,b)));boundary.setdefault(key,[]).append((a,b))
        for values in boundary.values():
            if len(values)==1:
                a,b=values[0];fs.append((a+N,b+N,b,a));materials.append(0)
        bodies+=1
    return vs,fs,materials,bodies


def create(source, specification, *, name='Landscape', collection=None):
    s=contract.validate(specification);pre=ensure_source(source);offsets,protection_report=relief_plan(source.data,s)
    owner=str(uuid.uuid4());col=None;old_hide=(source.hide_render,source.hide_get())
    try:
        col=bpy.data.collections.new(PREFIX+name);col[OWNER]=owner
        (collection or bpy.context.scene.collection).children.link(col)
        root=bpy.data.objects.new(PREFIX+name+' controls',None);col.objects.link(root)
        root[OWNER]=owner;root['astra_kind']='landscape';root['astra_source']=source
        root.matrix_world=source.matrix_world.copy();root.empty_display_type='PLAIN_AXES';root.empty_display_size=.3
        root['astra_spec']=json.dumps(s,sort_keys=True);root['astra_source_state']=json.dumps({'hide_render':old_hide[0],'hide_viewport':old_hide[1],**pre},sort_keys=True)
        root['astra_version']=contract.VERSION;root['astra_collection']=col;root['astra_active']=True
        ground=source.copy();ground.data=source.data.copy();ground.name=PREFIX+name+' receiving ground';col.objects.link(ground)
        ground[OWNER]=owner;ground.data[OWNER]=owner;ground.parent=root;ground.matrix_parent_inverse=Matrix.Identity(4);ground.matrix_basis=Matrix.Identity(4)
        ground.hide_render=False;ground.hide_set(False)
        for v,d in zip(ground.data.vertices,offsets):v.co.z+=d
        ground.data.update();ground['astra_role']='receiving_ground'
        if not ground.data.materials:ground.data.materials.append(material('layered earth',(.17,.115,.065),owner))
        root['astra_ground']=ground
        ground.data.calc_loop_triangles()
        bvh=BVHTree.FromPolygons([v.co.copy() for v in ground.data.vertices],[tuple(p.vertices) for p in ground.data.loop_triangles],all_triangles=True)
        top=max(v.co.z for v in ground.data.vertices)+10;bottom=min(v.co.z for v in ground.data.vertices)-10
        report={'schema':s['schema'],'version':contract.VERSION,'seed':s['seed'],'source_sha256':pre['mesh_sha256'],
                'relief_peak':max(offsets),'protection':protection_report,
                'counts':{},'rejections':{},'pieces':{},'limits':['No automatic aesthetic acceptance','Protection applies only to explicit masks','Open heightfields; no overhangs','Not ecological or structural simulation']}
        for kind in ['pebbles','moss']:
            vs=[];fs=[];indices=[];records=[];body_count=0
            if kind=='moss':vs,fs,indices,body_count=_moss_body(s,bvh,top,bottom)
            reasons={k:0 for k in ['mask','missing_surface','water','habitat','slope_or_footprint']};total=0
            for patch in sorted(s[kind]['patches'],key=lambda p:p['id']):
                area=math.pi*patch['radius'][0]*patch['radius'][1]
                count=min(6000,math.ceil(area*s[kind]['density']));total+=count
                for i in range(count):
                    identity=f"{kind}|{patch['id']}|{i}";rng=contract.stable_rng(s['seed'],identity)
                    # Correlated deposits occupy authored lobes. Candidate index remains stable at lower density.
                    a=rng.random()*math.tau;rr=math.sqrt(rng.random())
                    if kind=='pebbles':
                        # Several correlated deposits per patch, with distinct medium cobbles.
                        cr=contract.stable_rng(s['seed'],patch['id']+'|deposit:'+str(i%4))
                        ca=cr.random()*math.tau;rad=cr.uniform(.2,.65)
                        u=rad*math.cos(ca)+rng.gauss(0,.24);v=rad*math.sin(ca)+rng.gauss(0,.24)
                        rr=math.hypot(u,v)
                        if rr>1:reasons['habitat']+=1;continue
                        x=patch['center'][0]+patch['radius'][0]*u;y=patch['center'][1]+patch['radius'][1]*v
                        factor=rng.uniform(1.7,2.7) if rng.random()<.15 else rng.uniform(.5,1.10)
                    else:
                        x=patch['center'][0]+patch['radius'][0]*rr*math.cos(a);y=patch['center'][1]+patch['radius'][1]*rr*math.sin(a);factor=rng.uniform(.60,1.35)
                    radius=s[kind]['radius']*s['detail_scale']*factor
                    if contract.clearance(x,y,s)<radius*1.25:reasons['mask']+=1;continue
                    p,n=_sample(bvh,x,y,top,bottom)
                    if p is None:reasons['missing_surface']+=1;continue
                    level=s['water']['level']
                    if level is not None and p.z<=level+radius*.15:reasons['water']+=1;continue
                    contact=contract.zone_field(x,y,s['contacts']);shelter=contract.zone_field(x,y,s['shelter'])
                    shore=0 if level is None else contract.clamp(1-(p.z-level)/s['water']['shore_reach'])
                    if kind=='moss':
                        habitat=max(shore,contact*s[kind]['contact_influence'],shelter*s[kind]['shelter_influence'])
                        # Broad patch eligibility is independent of the noisy local rim.
                        chance=patch['weight']*(.20+.8*habitat)*(1-.35*rr)
                        chance*=.72+.28*math.sin(x*6+y*2)**2
                    else:chance=patch['weight']*(.92-.2*rr)
                    if rng.random()>chance:reasons['habitat']+=1;continue
                    h=(radius*rng.uniform(.45,.80) if kind=='pebbles' else s['moss']['body_height']*s['detail_scale']*rng.uniform(.78,1.24))
                    piece=_piece(kind,x,y,radius,h,rng,bvh,top,bottom,level)
                    if piece is None:reasons['slope_or_footprint']+=1;continue
                    pv,pf,pm,record=piece;off=len(vs);vs.extend(pv);fs.extend(tuple(off+k for k in f) for f in pf);indices.extend(pm)
                    record.update(identity=identity,contact=contact,shelter=shelter,shore=shore,clearance=contract.clearance(x,y,s));records.append(record)
            ob=make_mesh(kind+' grouped bodies',vs,fs,col,owner,_palette(kind,owner),indices)
            ob.parent=root;ob.matrix_parent_inverse=Matrix.Identity(4);ob.matrix_basis=Matrix.Identity(4);ob['astra_role']=kind
            root['astra_'+kind]=ob
            if kind=='moss':
                for poly in ob.data.polygons:poly.use_smooth=True
            report['counts'][kind]=len(records)
            if kind=='moss':report['counts']['moss_continuous_patches']=body_count
            report['rejections'][kind]={'candidates':total,**reasons};report['pieces'][kind]=records
        root['astra_output_hashes']=json.dumps({key:mesh_digest(root['astra_'+key].data) for key in ['ground','pebbles','moss']},sort_keys=True)
        root['astra_build_report']=json.dumps(report,sort_keys=True)
        source['astra_landscape_active']=root;source.hide_render=True;source.hide_set(True)
        bpy.context.view_layer.update()
        return root
    except Exception:
        _cleanup(owner);source.hide_render=old_hide[0];source.hide_set(old_hide[1]);raise


def get_root(obj):
    while obj and not obj.get('astra_kind'):obj=obj.parent
    if obj is None or obj.get('astra_kind') not in ('landscape','planks'):
        raise ValueError('Select generated landscape/plank controls or a generated child')
    return obj


def restore(root):
    root=get_root(root)
    if not root.get('astra_active'):raise ValueError('This generation is already restored')
    if root.get('astra_kind')=='landscape':
        source=root.get('astra_source');state=json.loads(root['astra_source_state'])
        if source is None or mesh_digest(source.data)!=state['mesh_sha256']:
            raise ValueError('Retained source missing or changed; refusing to overwrite outside edits')
        if source.get('astra_landscape_active')!=root:raise ValueError('Active source identity changed')
        source.hide_render=state['hide_render'];source.hide_set(state['hide_viewport']);del source['astra_landscape_active']
    for ob in bpy.data.objects:
        if ob.get(OWNER)==root[OWNER]:ob.hide_render=True;ob.hide_set(True)
    root['astra_active']=False
    return {'restored':True,'source_retained':True,'generated_output':'Retained hidden for inspection; no user assets deleted'}


def rebuild(root,specification):
    root=get_root(root);s=contract.validate(specification)
    if root.get('astra_kind')!='landscape' or not root.get('astra_active'):raise ValueError('Select an active landscape')
    source=root.get('astra_source');state=json.loads(root['astra_source_state'])
    if source is None or mesh_digest(source.data)!=state['mesh_sha256']:raise ValueError('Retained source missing or externally changed')
    # Validation completes before releasing old generation. Rollback restores the old visible state.
    del source['astra_landscape_active']
    try:
        ensure_source(source);new=create(source,s,name='Landscape update')
    except Exception:
        source['astra_landscape_active']=root;raise
    new['astra_source_state']=root['astra_source_state'];new.matrix_world=root.matrix_world.copy()
    for ob in bpy.data.objects:
        if ob.get(OWNER)==root[OWNER]:ob.hide_render=True;ob.hide_set(True)
    root['astra_active']=False;root['astra_superseded_by']=new
    return new


def audit(root,camera=None,scene=None):
    root=get_root(root);scene=scene or bpy.context.scene;camera=camera or scene.camera
    report={'kind':root['astra_kind'],'active':bool(root.get('astra_active')),'warnings':[],
            'checks':{},'art_acceptance':'not_determined','runtime_version':contract.VERSION}
    if root['astra_kind']=='landscape':
        build=json.loads(root['astra_build_report']);s=json.loads(root['astra_spec']);source=root.get('astra_source')
        report['counts']=build['counts'];report['relief_peak']=build['relief_peak'];report['rejections']=build['rejections']
        report['checks']['source_identity_retained']=source is not None
        expected=json.loads(root['astra_output_hashes'])
        report['checks']['generated_meshes_unchanged']=all(root.get('astra_'+key) and mesh_digest(root['astra_'+key].data)==value for key,value in expected.items())
        report['checks']['source_mesh_unchanged']=source is not None and mesh_digest(source.data)==build['source_sha256']
        report['protection']=build['protection']
        report['checks']['protected_polygon_delta_zero']=build['protection']['protected_polygon_max_delta']<1e-8
        if build['protection']['conservatively_suppressed_vertices']:report['warnings'].append('Footprint safety freezes whole intersecting source polygons; nearby relief may be suppressed. Refine the receiver to reduce the conservative margin')
        report['checks']['scatter_footprints_clear']=all(p['clearance']>=p['radius']*1.25 for rows in build['pieces'].values() for p in rows)
        if s['relief']['height'] and build['relief_peak']<s['relief']['height']*.10:report['warnings'].append('Relief is mostly masked or unsampled; inspect receiver resolution and bank placement')
        for kind in ['pebbles','moss']:
            if s[kind]['density']>0 and not build['counts'][kind]:report['warnings'].append(kind+' requested but no bodies survived the masks')
        if camera:
            from bpy_extras.object_utils import world_to_camera_view
            width=scene.render.resolution_x*scene.render.resolution_percentage/100
            height=scene.render.resolution_y*scene.render.resolution_percentage/100
            px={}
            for kind,rows in build['pieces'].items():
                spans=[];bodies=[];visible=0
                for p in rows:
                    co=Vector(p['center']);u=world_to_camera_view(scene,camera,root.matrix_world@co)
                    a=world_to_camera_view(scene,camera,root.matrix_world@(co+Vector((p['radius']*2,0,0))))
                    b=world_to_camera_view(scene,camera,root.matrix_world@(co+Vector((0,0,p['height']))))
                    if u.z>0 and 0<=u.x<=1 and 0<=u.y<=1:
                        visible+=1;spans.append(math.hypot((u.x-a.x)*width,(u.y-a.y)*height));bodies.append(math.hypot((u.x-b.x)*width,(u.y-b.y)*height))
                px[kind]={'frustum_centers':visible,'median_diameter_px':sorted(spans)[len(spans)//2] if spans else 0,'median_body_height_px':sorted(bodies)[len(bodies)//2] if bodies else 0}
                if rows and (not spans or px[kind]['median_diameter_px']<3):report['warnings'].append(kind+' has sub-3-pixel projected median diameter or is outside the camera')
                if kind=='moss' and rows and (not bodies or px[kind]['median_body_height_px']<1.5):report['warnings'].append('Moss body projects below 1.5 pixels; readability is unresolved at this camera')
            report['projection_estimates']=px
            report['warnings'].append('Projection estimates do not test occlusion, color contrast, silhouette quality or artistic acceptance; inspect actual hero and near renders')
        else:report['warnings'].append('No active camera: hero readability has not been checked')
    report['geometry_hashes']={o.get('astra_role',o.name):mesh_digest(o.data) for o in bpy.data.objects if o.get(OWNER)==root[OWNER] and o.type=='MESH'}
    if any(not v for v in report['checks'].values()):report['warnings'].append('A source/protection invariant failed; restore or inspect before continuing')
    return report


def create_planks(length=4.,width=1.3,count=14,seed=137,variation=.24,gap=.018,*,location=(0,0,0),rotation=(0,0,0),collection=None):
    contract.number(length,'length',.5,20);contract.number(width,'width',.2,4);contract.integer(count,'count',3,100)
    contract.integer(seed,'seed');contract.number(variation,'variation',0,.4);contract.number(gap,'gap',.003,.06)
    contract.vec(location,3,'location');contract.vec(rotation,3,'rotation')
    if gap*(count-1)>=length*.2:raise ValueError('Gaps occupy too much of the run')
    if (length-gap*(count-1))/count<.055:raise ValueError('Board width is below 0.055 local units')
    owner=str(uuid.uuid4())
    try:
        col=bpy.data.collections.new(PREFIX+'Planked run');col[OWNER]=owner;(collection or bpy.context.scene.collection).children.link(col)
        root=bpy.data.objects.new(PREFIX+'Planked run controls',None);col.objects.link(root);root[OWNER]=owner;root['astra_kind']='planks';root['astra_active']=True
        root.location=location;root.rotation_euler=rotation
        root['astra_spec']=json.dumps(dict(length=length,width=width,count=count,seed=seed,variation=variation,gap=gap))
        rng=contract.stable_rng(seed,'plank-widths');raw=[rng.uniform(1-variation,1+variation) for i in range(count)]
        actual=[x*(length-gap*(count-1))/sum(raw) for x in raw];cursor=-length/2;materials=_palette('planks',owner)
        vs=[];fs=[];mi=[];records=[]
        for i,w in enumerate(actual):
            r=contract.stable_rng(seed,'plank:'+str(i));a=cursor;b=cursor+w;side=width/2
            # Width varies, endpoints and top plane remain fixed. Edge silhouettes vary within clearances.
            nick=min(.022,w*.07)*variation/.24;off=len(vs);ch=r.uniform(.25,1)*nick
            outline=[(-side,a), (side-ch,a), (side,a+ch), (side,b-ch), (side-ch,b),(-side+ch,b),(-side,b-ch),(-side,a+ch)]
            for z in [-.085,0]:vs.extend((x,y,z) for x,y in outline)
            n=len(outline);faces=[tuple(off+k for k in range(n-1,-1,-1)),tuple(off+n+k for k in range(n))]
            faces+=[(off+k,off+(k+1)%n,off+n+(k+1)%n,off+n+k) for k in range(n)]
            fs.extend(faces);tone=r.randrange(len(materials));mi.extend([max(0,tone-1),tone]+[max(0,tone-1)]*n)
            records.append(dict(identity='plank:'+str(i),start=a,end=b,width=w,tone=tone));cursor=b+gap
        ob=make_mesh('varied planks',vs,fs,col,owner,materials,mi);ob.parent=root;ob.matrix_parent_inverse=Matrix.Identity(4);ob.matrix_basis=Matrix.Identity(4);ob['astra_role']='planks'
        bevel=ob.modifiers.new('Small bounded plank edge','BEVEL');bevel.width=.003;bevel.segments=1
        root['astra_build_report']=json.dumps({'boards':records,'first_endpoint':-length/2,'last_endpoint':cursor-gap,'level_top':0,'gap':gap,'length':length})
        return root
    except Exception:_cleanup(owner);raise
