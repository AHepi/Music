"""Art-directed maintained courtyard. Native GN controls; not erosion/ecology simulation.
All baseline objects and source assets retained. Exact approved seed scene is opened by jobs.
"""
import bpy,math,random,json,pathlib
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
P='LIVED / '
R=pathlib.Path('/workspace/scratch/97c495355428/japanese_reconstruction/lived_in_study')
ROUTE=[(5.18,-10.08),(4.34,-9.10),(3.43,-8.33),(2.45,-7.49),(1.12,-6.87),(1.12,-5.7),(1.12,.9),(1.12,1.7)]
BANKS=[(-6.8,-4.9,1.65,1.8,.43),(-6.7,-1.0,2.0,1.8,.34),(5.7,-2.5,1.65,2.1,.40),(-3.4,-7.25,1.5,1.0,.28),(3.8,-7.05,1.05,1.1,.24),(-2.65,.65,2.05,.78,.37),(-4.75,-5.8,1.2,.8,.38)]
GROWTH=[(-5.9,-3.9,1.35,.7,1.0),(-5.5,-5.6,1.7,.7,1.0),(-4.4,-6.65,1.25,.65,1.0),(-2.5,-7.7,1.2,.7,.9),(-6.4,-1.2,1.8,1.2,1.0),(-3.5,.55,1.1,.6,.8),(4.9,-3.5,1.4,1.8,.9),(5.3,-.2,1.4,1.2,.8),(3.9,-6.5,.9,1.1,.7),(-1.6,.9,1.4,.35,.7)]
DEPOSITS=[(-5.1,-4.9,.7,.45),(-4.0,-6.35,.55,.65),(-2.8,-7.7,.55,.35),(-.8,-7.9,.65,.35),(2.8,-6.8,.45,.65),(4.2,-6.0,.65,.45),(5.3,-4.1,.45,.9),(5.2,-1.5,.45,.7),(-4.6,-1.1,.65,.3),(-2.6,.8,.8,.35),(3.2,.2,.65,.35),(4.6,-8.7,.6,.7),(5.8,-9.1,.55,.8)]

def clamp(x,a=0,b=1):return max(a,min(b,x))
def smooth(a,b,x):t=clamp((x-a)/(b-a));return t*t*(3-2*t)
def segdist(x,y,a,b):
 ax,ay=a;bx,by=b;u=clamp(((x-ax)*(bx-ax)+(y-ay)*(by-ay))/((bx-ax)**2+(by-ay)**2));return math.hypot(x-ax-u*(bx-ax),y-ay-u*(by-ay))
def traffic(x,y):return min(segdist(x,y,a,b) for a,b in zip(ROUTE,ROUTE[1:]))
def basin(x,y):
 xx=x/(3.65*1.4);yy=(y+2.3*1.4)/(2.65*1.4);t=math.atan2(yy,xx);r=1+.075*math.sin(3*t+.8)+.055*math.sin(5*t-1.2)+.035*math.cos(9*t);return math.sqrt(xx*xx+yy*yy)/r

def relief(x,y):
 d=basin(x,y);wet=smooth(.93,1.04,d);route=smooth(1.12,1.65,traffic(x,y));hall=1-smooth(.5,1.5,y) if abs(x)<5.7 else 1
 z=sum(h*math.exp(-((x-cx)/rx)**2-((y-cy)/ry)**2) for cx,cy,rx,ry,h in BANKS)
 # Large asymmetric shoulder shape, no global high-frequency displacement.
 z*=.90+.10*math.sin(x*2.3+y*.8)
 return z*wet*route*hall

def coll(name):
 c=bpy.data.collections.new(P+name);bpy.context.scene.collection.children.link(c);return c

def mesh(name,verts,faces,mat=None,c=None,edges=[]):
 me=bpy.data.meshes.new(P+name+' mesh');me.from_pydata(verts,edges,faces);me.update();o=bpy.data.objects.new(P+name,me);c.objects.link(o)
 if mat:me.materials.append(mat)
 return o

def attr(me,name,data,typ='FLOAT'):
 a=me.attributes.new(name=name,type=typ,domain='POINT')
 for p,v in zip(a.data,data):
  if typ=='FLOAT_VECTOR':p.vector=v
  else:p.value=v
 return a

def group(name,sockets):
 g=bpy.data.node_groups.new(P+name,'GeometryNodeTree');g.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');g.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
 for name,typ,value in sockets:
  s=g.interface.new_socket(name=name,in_out='INPUT',socket_type=typ);s.default_value=value
  if typ=='NodeSocketFloat':s.min_value=0;s.max_value=10
 i=g.nodes.new('NodeGroupInput');o=g.nodes.new('NodeGroupOutput');g.asset_mark();return g,i,o

def named(g,n,typ='FLOAT'):
 q=g.nodes.new('GeometryNodeInputNamedAttribute');q.data_type=typ;q.inputs['Name'].default_value=n;return q.outputs['Attribute']
def mathn(g,op,a,b=None):
 q=g.nodes.new('ShaderNodeMath');q.operation=op
 for k,v in enumerate([a,b]):
  if v is None:continue
  if hasattr(v,'is_output'):g.links.new(v,q.inputs[k])
  else:q.inputs[k].default_value=v
 return q.outputs[0]
def link(g,a,b):g.links.new(a,b)
def arrange(g):
 for k,n in enumerate(g.nodes):n.location=((k%6)*220,-(k//6)*190)
def setinput(mod,name,value):
 for s in mod.node_group.interface.items_tree:
  if s.item_type=='SOCKET' and s.in_out=='INPUT' and s.name==name:mod[s.identifier]=value;return
 raise KeyError(name)

def material(name,color,rough=.92):
 m=bpy.data.materials.new(P+name);linear=tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in color);m.diffuse_color=(*linear,1);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*linear,1);p.inputs['Roughness'].default_value=rough
 return m

def tintcopy(original,name,factor):
 m=original.copy();m.name=P+name;nt=m.node_tree
 groups=[n for n in nt.nodes if n.type=='GROUP' and n.inputs.get('Base')]
 if groups:
  for q in groups:
   for key in ['Base','Shadow','Highlight']:
    if q.inputs.get(key) and not q.inputs[key].is_linked:
     old=list(q.inputs[key].default_value);q.inputs[key].default_value=tuple(old[k]*factor[k] for k in range(3))+(1,)
  return m
 bs=next((n for n in nt.nodes if n.type=='BSDF_PRINCIPLED'),None)
 if bs:
  inp=bs.inputs['Base Color'];mix=nt.nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[2].default_value=(*factor,1)
  if inp.is_linked:nt.links.new(inp.links[0].from_socket,mix.inputs[1])
  else:mix.inputs[1].default_value=inp.default_value
  nt.links.new(mix.outputs[0],inp)
 return m

def terrain_setup():
 t=bpy.data.objects['Continuous earth with sloped pond basin'];t.data=t.data.copy();world=[t.matrix_world@v.co for v in t.data.vertices];data=[relief(v.x,v.y) for v in world];attr(t.data,'lived_bank_relief',data)
 # Wet-to-dry pigment transition is large-form dependent, with authored contact and traffic fields.
 damp=[clamp((1.25-basin(v.x,v.y))*2.3)+.15*math.exp(-((v.x+6)**2+(v.y+4)**2)/7) for v in world];attr(t.data,'lived_damp_soil',[clamp(v) for v in damp])
 g,i,o=group('Raised bank landform',[('Relief Height','NodeSocketFloat',1.)]);sp=g.nodes.new('GeometryNodeSetPosition');co=g.nodes.new('ShaderNodeCombineXYZ');link(g,mathn(g,'MULTIPLY',named(g,'lived_bank_relief'),i.outputs['Relief Height']),co.inputs['Z']);link(g,i.outputs['Geometry'],sp.inputs['Geometry']);link(g,co.outputs[0],sp.inputs['Offset']);link(g,sp.outputs[0],o.inputs[0]);arrange(g);mo=t.modifiers.new(P+'Live broad landform','NODES');mo.node_group=g
 old=t.data.materials[0];mat=old.copy();mat.name=P+'Layered damp earth';nt=mat.node_tree
 targets=[n.inputs['Base'] for n in nt.nodes if n.type=='GROUP' and n.inputs.get('Base')]
 targets+=[n.inputs['Base Color'] for n in nt.nodes if n.type=='BSDF_PRINCIPLED']
 for bc in targets:
  mix=nt.nodes.new('ShaderNodeMixRGB');mix.blend_type='MIX';mix.inputs[2].default_value=(.012,.022,.015,1);a=nt.nodes.new('ShaderNodeAttribute');a.attribute_name='lived_damp_soil';nt.links.new(a.outputs['Fac'],mix.inputs[0])
  if bc.is_linked:nt.links.new(bc.links[0].from_socket,mix.inputs[1])
  else:mix.inputs[1].default_value=bc.default_value
  nt.links.new(mix.outputs[0],bc)
 t.data.materials[0]=mat
 t['lived_in_semantics']='Authored bank shoulders and shallow shore tongues preserve central pond level, traffic center and inner hall support strip. Relief Height is a live amplitude control, not a simulation.'
 # Old large smooth green sheets replaced with geometry; retain for reversible audit.
 hidden=[]
 for x in bpy.context.scene.objects:
  if x.name.startswith(('Moss mat seated','Low moss pocket')):x.hide_render=True;x.hide_set(True);hidden.append(x.name)
 # Dependent receiving forms follow the same live terrain amplitude.
 moved=[]
 selected=['Garden anchor boulder 01','Garden anchor boulder 02','Embedded shore stone 09','Embedded shore stone 10','Embedded shore stone 12','Embedded shore stone 18','Embedded shore stone 19','Embedded shore stone 21','Embedded shore stone 27']
 relief_socket=next(q.identifier for q in g.interface.items_tree if q.item_type=='SOCKET' and q.name=='Relief Height')
 for x in bpy.context.scene.objects:
  if x.type!='MESH' or not (x.name in selected or x.name.startswith('Bank grass blade')):continue
  ps=[x.matrix_world@v.co for v in x.data.vertices]
  if not ps:continue
  if x.name in selected:
   cx=sum(p.x for p in ps)/len(ps);cy=sum(p.y for p in ps)/len(ps);dz=relief(cx,cy)
  else:
   p=min(ps,key=lambda v:v.z);dz=relief(p.x,p.y)
  if dz<.004:continue
  gg,ii,oo=group('Ground-following support / '+x.name,[('Relief Height','NodeSocketFloat',1.)]);tr=gg.nodes.new('GeometryNodeTransform');co=gg.nodes.new('ShaderNodeCombineXYZ');link(gg,mathn(gg,'MULTIPLY',ii.outputs['Relief Height'],dz/max(abs(x.matrix_world.to_scale().z),.001)),co.inputs['Z']);link(gg,ii.outputs['Geometry'],tr.inputs['Geometry']);link(gg,co.outputs[0],tr.inputs['Translation']);link(gg,tr.outputs[0],oo.inputs[0]);mm=x.modifiers.new(P+'Supported bank rise after accepted cuts','NODES');mm.node_group=gg
  ss=next(q.identifier for q in gg.interface.items_tree if q.item_type=='SOCKET' and q.name=='Relief Height');mm[ss]=1.
  drv=mm.driver_add('["'+ss+'"]').driver;v=drv.variables.new();v.name='relief';v.targets[0].id=t;v.targets[0].data_path='modifiers["'+mo.name+'"]["'+relief_socket+'"]';drv.expression='relief';arrange(gg);moved.append((x.name,dz))
 mo[relief_socket]=1.
 bpy.context.view_layer.update();return t,{'relief_range':[min(data),max(data)],'hidden_legacy_mats':hidden,'grass_reseated':moved}

def bvh_for(objects):
 vs=[];fs=[];dg=bpy.context.evaluated_depsgraph_get()
 for o in objects:
  e=o.evaluated_get(dg);m=e.to_mesh();off=len(vs);vs.extend(o.matrix_world@v.co for v in m.vertices);fs.extend(tuple(off+j for j in f.vertices) for f in m.polygons);e.to_mesh_clear()
 return BVHTree.FromPolygons(vs,fs)

def sample_top(bvh,x,y):
 p,n,_,_=bvh.ray_cast(Vector((x,y,6)),Vector((0,0,-1)),10);return p,n

def source_shapes(c):
 peb=bpy.data.collections.new(P+'Pebble source bank');bpy.context.scene.collection.children.link(peb)
 moss=bpy.data.collections.new(P+'Moss cushion source bank');bpy.context.scene.collection.children.link(moss)
 tuft=bpy.data.collections.new(P+'Low leafy tuft source bank');bpy.context.scene.collection.children.link(tuft)
 palette=[material('Gravel cool slate',(.36,.40,.37)),material('Gravel pale warm',(.39,.37,.29)),material('Gravel dark wet',(.105,.155,.15)),material('Gravel muted umber',(.27,.235,.17))]
 mossmat=[material('Moss deep body',(.18,.25,.16)),material('Moss olive crown',(.28,.36,.23)),material('Moss fresh small tips',(.36,.43,.27)),material('Moss shaded body',(.20,.28,.18))]
 for m in mossmat:
  nt=m.node_tree;bs=nt.nodes.get('Principled BSDF');tex=nt.nodes.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=72;tex.inputs['Detail'].default_value=2;bu=nt.nodes.new('ShaderNodeBump');bu.inputs['Distance'].default_value=.006;bu.inputs['Strength'].default_value=.32;nt.links.new(tex.outputs['Fac'],bu.inputs['Height']);nt.links.new(bu.outputs[0],bs.inputs['Normal'])
 leafmat=[material('Low ground leaf deep',(.22,.32,.21)),material('Low ground leaf face',(.34,.43,.23)),material('Low ground leaf sun',(.43,.50,.28))]
 for j in range(7):
  r=random.Random(290+j);N=7;vs=[];fs=[]
  for z,rr in [(0,.7),(.35,1),(.85,.70)]:
   for k in range(N):a=k*math.tau/N;radius=rr*r.uniform(.82,1.16);vs.append((math.cos(a)*radius,math.sin(a)*radius*(.65+.03*j),z+r.uniform(-.065,.065)))
  vs.append((.12,-.03,1.02));top=3*N
  fs.append(tuple(range(N-1,-1,-1)))
  for ring in range(2):
   for k in range(N):fs.append((ring*N+k,ring*N+(k+1)%N,(ring+1)*N+(k+1)%N,(ring+1)*N+k))
  for k in range(N):fs.append((2*N+k,2*N+(k+1)%N,top))
  lowest=min(v[2] for v in vs);vs=[(x,y,z-lowest) for x,y,z in vs]
  o=mesh('Pebble form %02d'%j,vs,fs,None,peb)
  for m in palette:o.data.materials.append(m)
  for f in o.data.polygons:f.material_index=(j+ (1 if r.random()<.13 else 0))%len(palette)
  o.hide_render=True;o.hide_set(True)
 for j in range(5):
  r=random.Random(610+j);N=21;vs=[(0,0,1.0)];fs=[];radial=[.82+.18*math.sin(3*k*math.tau/N+j)+r.uniform(-.06,.08) for k in range(N)]
  # Uneven star/lobe perimeter; low inflated growth rather than green paint.
  for ring,rr,zz in [(0,.20,.96),(1,.43,.88),(2,.67,.65),(3,.87,.31),(4,1.,.01)]:
   for k in range(N):a=k*math.tau/N;rad=rr*radial[k];vs.append((math.cos(a)*rad,math.sin(a)*rad*(.75+.07*j),zz+r.uniform(-.012,.012)))
  for k in range(N):fs.append((0,1+k,1+(k+1)%N))
  for ring in range(4):
   for k in range(N):a=1+ring*N+k;b=1+ring*N+(k+1)%N;c0=1+(ring+1)*N+(k+1)%N;d=1+(ring+1)*N+k;fs.extend([(a,c0,b),(a,d,c0)])
  o=mesh('Low lobed moss cushion %02d'%j,vs,fs,None,moss)
  for m in mossmat:o.data.materials.append(m)
  for f in o.data.polygons:f.material_index=(1 if f.center.z>.4 else 0) if r.random()<.85 else (2 if r.random()<.4 else 3)
  # Small close clustered leaflets seated into crown; silhouette not uniform fur.
  for k in range(0):
   a=r.random()*math.tau;rad=math.sqrt(r.random())*.72;x=rad*math.cos(a);y=rad*math.sin(a);z=.84-.66*rad;h=r.uniform(.07,.14);w=r.uniform(.022,.04);angle=r.random()*math.tau;u=Vector((math.cos(angle),math.sin(angle),0));base=Vector((x,y,z));off=len(vs);vs.extend([tuple(base-u*w),tuple(base+u*w),tuple(base+Vector((.02,.01,h)))]);fs.append((off,off+1,off+2))
  o.data.clear_geometry();o.data.from_pydata(vs,[],fs);o.data.update()
  for f in o.data.polygons:f.material_index=1 if f.center.z>.18 else 0;f.use_smooth=True
  o.hide_render=True;o.hide_set(True)
 for j in range(4):
  r=random.Random(911+j);vs=[];fs=[]
  for k in range(7+j):
   a=k*2.399+j;length=r.uniform(.55,1.0);w=r.uniform(.10,.19);dx,dy=math.cos(a),math.sin(a);off=len(vs);vs.extend([(0,0,0),(dx*length*.45-dy*w,dy*length*.45+dx*w,.35),(dx*length,dy*length,.22+r.random()*.3),(dx*length*.45+dy*w,dy*length*.45-dx*w,.35),(dx*length*.42,dy*length*.42,.48)]);fs.extend([(off,off+1,off+4),(off+1,off+2,off+4),(off+2,off+3,off+4),(off+3,off,off+4)])
  fs=[tuple(reversed(f)) for f in fs]
  o=mesh('Small sheltered leaf cluster %02d'%j,vs,fs,None,tuft)
  for m in leafmat:o.data.materials.append(m)
  for f in o.data.polygons:f.material_index=(f.index+j)%3
  o.hide_render=True;o.hide_set(True)
 return peb,moss,tuft

def scatter(name,records,bank,terrain,c,kind):
 host=mesh(name,[(r['x'],r['y'],4) for r in records],[],None,c)
 for nm,key,typ in [('lived_scale','scale','FLOAT_VECTOR'),('lived_rotation','rot','FLOAT_VECTOR'),('lived_traffic_distance','traffic','FLOAT'),('lived_habitat','habitat','FLOAT'),('lived_contact','contact','FLOAT')]:attr(host.data,nm,[r[key] for r in records],typ)
 g,i,o=group(name+' / semantic scatter',[('Density','NodeSocketFloat',1.),('Traffic Width','NodeSocketFloat',1.03),('Waterline','NodeSocketFloat',0.),('Damp Reach','NodeSocketFloat',.95),('Contact Influence','NodeSocketFloat',.6),('Seed','NodeSocketInt',307 if kind=='pebble' else 521)])
 pos=g.nodes.new('GeometryNodeInputPosition');oi=g.nodes.new('GeometryNodeObjectInfo');oi.inputs['Object'].default_value=terrain;oi.transform_space='RELATIVE';ray=g.nodes.new('GeometryNodeRaycast');ray.data_type='FLOAT';ray.inputs['Ray Direction'].default_value=(0,0,-1);ray.inputs['Ray Length'].default_value=10;link(g,oi.outputs['Geometry'],ray.inputs['Target Geometry']);srcsep=g.nodes.new('ShaderNodeSeparateXYZ');srcvec=g.nodes.new('ShaderNodeCombineXYZ');link(g,pos.outputs[0],srcsep.inputs[0]);link(g,srcsep.outputs['X'],srcvec.inputs['X']);link(g,srcsep.outputs['Y'],srcvec.inputs['Y']);srcvec.inputs['Z'].default_value=6;link(g,srcvec.outputs[0],ray.inputs['Source Position'])
 sp=g.nodes.new('GeometryNodeSetPosition');link(g,i.outputs['Geometry'],sp.inputs['Geometry']);link(g,ray.outputs['Hit Position'],sp.inputs['Position']);sp.inputs['Offset'].default_value=(0,0,-.012 if kind=='pebble' else -.018)
 trafficok=mathn(g,'GREATER_THAN',named(g,'lived_traffic_distance'),i.outputs['Traffic Width']);hab=named(g,'lived_habitat');contact=mathn(g,'MULTIPLY',named(g,'lived_contact'),i.outputs['Contact Influence']);prob=mathn(g,'MINIMUM',mathn(g,'ADD',hab,contact),1);prob=mathn(g,'MULTIPLY',prob,i.outputs['Density'])
 sep=g.nodes.new('ShaderNodeSeparateXYZ');link(g,ray.outputs['Hit Position'],sep.inputs[0]);dz=mathn(g,'SUBTRACT',sep.outputs['Z'],i.outputs['Waterline']);dryok=mathn(g,'GREATER_THAN',dz,-.015)
 if kind!='pebble':dryok=mathn(g,'MULTIPLY',dryok,mathn(g,'LESS_THAN',dz,i.outputs['Damp Reach']))
 ran=g.nodes.new('FunctionNodeRandomValue');ran.data_type='FLOAT';link(g,i.outputs['Seed'],ran.inputs['Seed']);keep=mathn(g,'LESS_THAN',ran.outputs['Value'],prob);keep=mathn(g,'MULTIPLY',keep,trafficok);keep=mathn(g,'MULTIPLY',keep,dryok);keep=mathn(g,'MULTIPLY',keep,ray.outputs['Is Hit'])
 info=g.nodes.new('GeometryNodeCollectionInfo');info.inputs['Collection'].default_value=bank;info.inputs['Separate Children'].default_value=True;info.inputs['Reset Children'].default_value=True
 inst=g.nodes.new('GeometryNodeInstanceOnPoints');inst.inputs['Pick Instance'].default_value=True;link(g,sp.outputs[0],inst.inputs['Points']);link(g,keep,inst.inputs['Selection']);link(g,info.outputs['Instances'],inst.inputs['Instance']);link(g,named(g,'lived_scale','FLOAT_VECTOR'),inst.inputs['Scale']);align=g.nodes.new('FunctionNodeAlignEulerToVector');align.axis='Z';link(g,ray.outputs['Hit Normal'],align.inputs['Vector']);link(g,named(g,'lived_rotation','FLOAT_VECTOR'),align.inputs['Rotation']);link(g,align.outputs['Rotation'],inst.inputs['Rotation']);index=g.nodes.new('FunctionNodeRandomValue');index.data_type='INT';index.inputs['Min'].default_value=0;index.inputs['Max'].default_value=len(bank.objects)-1;link(g,i.outputs['Seed'],index.inputs['Seed']);link(g,index.outputs['Value'],inst.inputs['Instance Index']);link(g,inst.outputs[0],o.inputs[0]);arrange(g);mod=host.modifiers.new(P+'Live planted/sorted instances','NODES');mod.node_group=g;host['lived_in_semantics']='Authored candidate sites with live traffic, waterline/damp reach, habitat/contact eligibility, density, seed and receiving-ground raycast. Not simulated growth or transport.';return host

def build_scatter(terrain,c,pc,mc,tc):
 ground=bvh_for([terrain]);stones=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.name.startswith(('Garden anchor boulder','Embedded shore stone','Embedded approach slab','Full-width bridge arrival stone','Gnarled pine / buttressed','Pine surface root')) and not 'cutter' in o.name];obstacle=bvh_for(stones)
 rng=random.Random(521);sets={'pebble':[],'moss':[],'tuft':[]};rejected=0
 def valid(x,y,r):
  p,n=sample_top(ground,x,y)
  if p is None or p.z<-.025 or n.z<.50:return None
  op,on=sample_top(obstacle,x,y)
  if op and op.z>p.z+.025:return None
  return p,n
 # Candidate density is spatially correlated: authored deposit lobes and damp ground islands.
 for kind,count in [('pebble',3200),('moss',8500),('tuft',85)]:
  for j in range(count):
   if kind=='pebble':
    cx,cy,rx,ry=DEPOSITS[j%len(DEPOSITS)];x=cx+rng.gauss(0,rx*.65);y=cy+rng.gauss(0,ry*.65);rad=rng.uniform(.025,.075) if rng.random()<.76 else rng.uniform(.085,.16);h=rad*rng.uniform(.48,.9);hab=.85
    if j%19==0:rad=rng.uniform(.15,.24);h=rad*rng.uniform(.5,.8);contact=.1
   else:
    cx,cy,rx,ry,importance=GROWTH[j%len(GROWTH)];a=rng.random()*math.tau;rr=math.sqrt(rng.random());x=cx+rx*rr*math.cos(a);y=cy+ry*rr*math.sin(a)
    # Boundary breaks in linked lobes rather than circular discs or all-over fur.
    field=.56+.24*math.sin(x*6.1+y*2.8)+.2*math.sin(y*9.3-x*.8)
    if field<.29:continue
    dep=max(math.exp(-((x-a)/rx0)**2-((y-b)/ry0)**2) for a,b,rx0,ry0 in DEPOSITS)
    if dep>.7 and j%5!=0:continue
    rad=rng.uniform(.055,.105) if kind=='moss' else rng.uniform(.08,.14);h=rng.uniform(.028,.055) if kind=='moss' else rng.uniform(.11,.18);hab=importance*(.55+.4*(1-rr));contact=.12
   td=traffic(x,y)
   if td<.96:continue
   q=valid(x,y,rad)
   if not q:rejected+=1;continue
   p,n=q
   near=obstacle.find_nearest(p);contact=clamp(1-near[3]/.55) if near[0] is not None else 0
   # Slopes get smaller, more embedded cushions; avoid unsupported large horizontal discs.
   if n.z<.88:rad*=.66
   sets[kind].append({'x':x,'y':y,'z':p.z,'scale':(rad,rad*rng.uniform(.68,1.0),h),'rot':(0,0,rng.random()*math.tau),'traffic':td,'habitat':hab,'contact':contact})
 hosts=[]
 for kind,bank in [('pebble',pc),('moss',mc),('tuft',tc)]:hosts.append(scatter({'pebble':'Grouped shore and shoulder pebbles','moss':'Connected low moss cushions','tuft':'Sheltered low leafy accents'}[kind],sets[kind],bank,terrain,c,kind))
 return {'counts_authored':{k:len(v) for k,v in sets.items()},'rejected_obstructed_or_submerged':rejected,'records':sets,'hosts':[o.name for o in hosts]}

def moss_body(terrain,c):
 ground=bvh_for([terrain]);rocks=bvh_for([o for o in bpy.context.scene.objects if o.type=='MESH' and o.name.startswith(('Garden anchor boulder','Embedded shore stone','Embedded approach slab','Full-width bridge arrival stone','Gnarled pine / buttressed','Pine surface root')) and 'cutter' not in o.name]);vs=[];fs=[];heights=[]
 # Contiguous top and perimeter sidewalls provide a genuine moss body under the fine cushions.
 for j,(cx,cy,rx,ry,strength) in enumerate(GROWTH):
  step=.12;nx=math.ceil(rx*2/step);ny=math.ceil(ry*2/step);cells={};grid={}
  for yy in range(ny+1):
   for xx in range(nx+1):
    x=cx-rx+xx*step;y=cy-ry+yy*step;r=math.sqrt(((x-cx)/rx)**2+((y-cy)/ry)**2);edge=.85+.10*math.sin(x*7+y*3)+.08*math.sin(y*5-x*4)
    dep=max(math.exp(-((x-a)/dx)**2-((y-b)/dy)**2) for a,b,dx,dy in DEPOSITS)
    if r>edge or dep>.72 or traffic(x,y)<1.16 or basin(x,y)<1.01:continue
    p,n=sample_top(ground,x,y)
    if p is None or p.z<.01 or n.z<.56:continue
    op,on=sample_top(rocks,x,y)
    if op and op.z>p.z+.018:continue
    grid[(xx,yy)]=(x,y,.008+.010*(1-r)*(.7+.3*math.sin(x*5+y*7)))
  used={};boundary={}
  for yy in range(ny):
   for xx in range(nx):
    ks=[(xx,yy),(xx+1,yy),(xx+1,yy+1),(xx,yy+1)]
    if not all(k in grid for k in ks):continue
    ids=[]
    for k in ks:
     if k not in used:
      x,y,h=grid[k];used[k]=len(vs);vs.extend([(x,y,4),(x,y,4)]);heights.extend([h,.002])
     ids.append(used[k])
    fs.extend([(ids[0],ids[1],ids[2]),(ids[0],ids[2],ids[3])])
    for a,b in zip(ids,ids[1:]+ids[:1]):
     key=tuple(sorted((a,b)))
     if key in boundary:del boundary[key]
     else:boundary[key]=(a,b)
  for a,b in boundary.values():fs.append((a,a+1,b+1,b))
 host=mesh('Connected low moss ground bodies',vs,fs,bpy.data.materials[P+'Moss deep body'],c);host.data.materials.append(bpy.data.materials[P+'Moss olive crown'])
 for f in host.data.polygons:f.material_index=0 if len(f.vertices)==4 else 1;f.use_smooth=True
 attr(host.data,'lived_moss_height',heights);g,i,o=group('Continuous moss body support',[('Cushion Height','NodeSocketFloat',1.)]);pos=g.nodes.new('GeometryNodeInputPosition');sep=g.nodes.new('ShaderNodeSeparateXYZ');co=g.nodes.new('ShaderNodeCombineXYZ');link(g,pos.outputs[0],sep.inputs[0]);link(g,sep.outputs['X'],co.inputs['X']);link(g,sep.outputs['Y'],co.inputs['Y']);co.inputs['Z'].default_value=6;oi=g.nodes.new('GeometryNodeObjectInfo');oi.inputs['Object'].default_value=terrain;oi.transform_space='RELATIVE';ray=g.nodes.new('GeometryNodeRaycast');ray.inputs['Ray Direction'].default_value=(0,0,-1);ray.inputs['Ray Length'].default_value=10;link(g,oi.outputs['Geometry'],ray.inputs['Target Geometry']);link(g,co.outputs[0],ray.inputs['Source Position']);setp=g.nodes.new('GeometryNodeSetPosition');link(g,i.outputs['Geometry'],setp.inputs['Geometry']);link(g,ray.outputs['Hit Position'],setp.inputs['Position']);h=g.nodes.new('ShaderNodeCombineXYZ');link(g,mathn(g,'MULTIPLY',named(g,'lived_moss_height'),i.outputs['Cushion Height']),h.inputs['Z']);link(g,h.outputs[0],setp.inputs['Offset']);link(g,setp.outputs[0],o.inputs[0]);mod=host.modifiers.new(P+'Live terrain-conforming moss body','NODES');mod.node_group=g;arrange(g)
 return {'host':host.name,'vertices':len(vs),'faces':len(fs),'meaning':'Continuous low irregular body following actual evaluated receiving terrain, with sparse cushions/fringe. Native height amplitude.'}

def rock_contact_growth(terrain,c,bank,terrain_report):
 ground=bvh_for([terrain]);dg=bpy.context.evaluated_depsgraph_get();rng=random.Random(179);pts=[];rot=[];sc=[];rise=[];evidence=[];shift=dict(terrain_report['grass_reseated'])
 # Select the actual lower surfaces, near receiving earth. Face interiors are support-checked.
 for target in [o for o in bpy.context.scene.objects if o.type=='MESH' and o.name.startswith(('Garden anchor boulder','Embedded shore stone'))]:
  ev=target.evaluated_get(dg);me=ev.to_mesh();me.calc_loop_triangles();normalmat=target.matrix_world.to_3x3().inverted().transposed();tb=BVHTree.FromPolygons([target.matrix_world@v.co for v in me.vertices],[list(f.vertices) for f in me.loop_triangles],all_triangles=True);dz=shift.get(target.name,0)
  for tri in me.loop_triangles:
   a,b,d=[target.matrix_world@me.vertices[k].co for k in tri.vertices];normal=(b-a).cross(d-a).normalized();area=(b-a).cross(d-a).length/2
   if area<.002 or normal.z<.03 or normal.z>.87:continue
   if normal.dot(Vector((-.25,-1,.2)).normalized())<.05:continue
   for q in range(max(1,int(area*950))):
    u=rng.random();v=rng.random()
    if u+v>1:u=1-u;v=1-v
    p=a+(b-a)*u+(d-a)*v;gh,gn=sample_top(ground,p.x,p.y)
    if gh is None or p.z-gh.z<.015 or p.z-gh.z>.19:continue
    # Patchy but contiguous sectors at contacts; not every side or upper face.
    if math.sin(p.x*4.7+p.y*2.6)+.5*math.sin(p.y*7-p.z*3)<-.2:continue
    rad=rng.uniform(.021,.041);height=rng.uniform(.008,.018);basis=normal.to_track_quat('Z','Y');uvec=basis@Vector((1,0,0));vvec=basis@Vector((0,1,0));ok=True
    for k in range(8):
     pp=p+1.15*rad*(math.cos(k*math.tau/8)*uvec+math.sin(k*math.tau/8)*vvec);support,sn,_,_=tb.ray_cast(pp+normal*.06,-normal,.14)
     if support is None or abs((pp-support).dot(normal))>.008:ok=False;break
    if not ok:continue
    pos=p-normal*.008;pts.append((pos.x,pos.y,pos.z-dz));rot.append(tuple(basis.to_euler()));sc.append((rad,rad*rng.uniform(.7,1),height));rise.append(dz);evidence.append({'target':target.name,'base':list(pos),'above_ground':p.z-gh.z,'radius':rad,'terrain_shift':dz})
  ev.to_mesh_clear()
 host=mesh('Moss grown over supported lower stone skirts',pts,[],None,c);attr(host.data,'lived_rock_moss_scale',sc,'FLOAT_VECTOR');attr(host.data,'lived_rock_moss_rotation',rot,'FLOAT_VECTOR');attr(host.data,'lived_support_rise',rise)
 g,i,o=group('Supported lower-rock moss',[('Relief Height','NodeSocketFloat',1.),('Density','NodeSocketFloat',1.)]);sp=g.nodes.new('GeometryNodeSetPosition');co=g.nodes.new('ShaderNodeCombineXYZ');link(g,mathn(g,'MULTIPLY',named(g,'lived_support_rise'),i.outputs['Relief Height']),co.inputs['Z']);link(g,i.outputs['Geometry'],sp.inputs['Geometry']);link(g,co.outputs[0],sp.inputs['Offset']);info=g.nodes.new('GeometryNodeCollectionInfo');info.inputs['Collection'].default_value=bank;info.inputs['Separate Children'].default_value=True;info.inputs['Reset Children'].default_value=True;inst=g.nodes.new('GeometryNodeInstanceOnPoints');inst.inputs['Pick Instance'].default_value=True;link(g,sp.outputs[0],inst.inputs['Points']);link(g,info.outputs['Instances'],inst.inputs['Instance']);link(g,named(g,'lived_rock_moss_scale','FLOAT_VECTOR'),inst.inputs['Scale']);link(g,named(g,'lived_rock_moss_rotation','FLOAT_VECTOR'),inst.inputs['Rotation']);rand=g.nodes.new('FunctionNodeRandomValue');rand.data_type='FLOAT';rand.inputs['Seed'].default_value=179;link(g,mathn(g,'LESS_THAN',rand.outputs['Value'],i.outputs['Density']),inst.inputs['Selection']);link(g,inst.outputs[0],o.inputs[0]);mod=host.modifiers.new(P+'Supported cushion clusters','NODES');mod.node_group=g
 terrain_mod=terrain.modifiers[P+'Live broad landform'];source_socket=next(q.identifier for q in terrain_mod.node_group.interface.items_tree if q.item_type=='SOCKET' and q.name=='Relief Height');ss=next(q.identifier for q in g.interface.items_tree if q.item_type=='SOCKET' and q.name=='Relief Height');mod[ss]=1;drv=mod.driver_add('["'+ss+'"]').driver;v=drv.variables.new();v.name='relief';v.targets[0].id=terrain;v.targets[0].data_path='modifiers["'+terrain_mod.name+'"]["'+source_socket+'"]';drv.expression='relief';arrange(g)
 return {'host':host.name,'count':len(pts),'support_records':evidence,'support_test':'Eight conservative perimeter normal-rays within0.008m of explicit evaluated target triangles at creation. Nearest-point proximity is not treated as backing.'}

def planks(c):
 old=bpy.data.objects['LIVE GN / footbridge individual boards'];old.hide_render=True;old.hide_set(True)
 # Replace uniform rhythm without moving landings, posts, girders or rail.
 rng=random.Random(903);N=21;start=-6.507;end=.531;span=end-start;gaps=[rng.uniform(.010,.021) for _ in range(N-1)];raw=[rng.uniform(.72,1.28) for _ in range(N)];widths=[w*(span-sum(gaps))/sum(raw) for w in raw];bank=bpy.data.collections.new(P+'Bridge plank profile bank');bpy.context.scene.collection.children.link(bank)
 base=bpy.data.materials['Cedar cut ends and rubbed edges'];mats=[tintcopy(base,'Cedar board tone %d'%j,(v,v*.98,v*.96)) for j,v in enumerate([.64,.78,.92,1.03,1.12,.85,.71])];side=tintcopy(base,'Cedar board end and side',(.60,.62,.64));grain=material('Dark grain and end splits',(.08,.075,.052))
 for j in range(7):
  r=random.Random(120+j);vs=[];fs=[]
  # Source dimensions 2.1m x 1 normalized width x .13m; chiseled nonidentical end profiles.
  contour=[(-1.04+r.uniform(-.04,.04),-.5),(-.5,-.5),(0,-.5),(.5,-.5),(1.04+r.uniform(-.045,.045),-.5),(1.065+r.uniform(-.02,.025),-.05),(1.04+r.uniform(-.04,.025),.5),(.5,.5),(0,.5),(-.5,.5),(-1.04+r.uniform(-.035,.035),.5),(-1.065+r.uniform(-.02,.025),.02)]
  for z in [-.065,.065]:
   for x,y in contour:vs.append((x,y,z+(.003*math.sin(x*3+j) if z>0 else 0)))
  n=len(contour);fs=[tuple(range(n-1,-1,-1)),tuple(n+k for k in range(n))]
  for k in range(n):fs.append((k,(k+1)%n,n+(k+1)%n,n+k))
  o=mesh('Hand-shaped bridge plank %02d'%j,vs,fs,None,bank);o.data.materials.append(mats[j]);o.data.materials.append(side)
  for f in o.data.polygons:f.material_index=0 if f.index==1 else 1
  b=o.modifiers.new('Readable chiseled arris','BEVEL');b.width=.012;b.segments=1;o.hide_render=True;o.hide_set(True)
 pts=[];scales=[];rot=[];y=start;records=[]
 for j,w in enumerate(widths):
  yy=y+w/2;t=(yy/1.4+4.65)/5.05;z=.32+.28*math.sin(math.pi*t);angle=rng.uniform(-.0025,.0025);twist=rng.uniform(-.004,.004);pts.append((1.12+rng.uniform(-.007,.007),yy,z));scales.append((rng.uniform(.97,1.03),w,1));rot.append((0,twist,angle));records.append({'index':j,'center':pts[-1],'width':w,'gap_after':gaps[j] if j<N-1 else None,'rotation':rot[-1]});y+=w+(gaps[j] if j<N-1 else 0)
 host=mesh('Crafted bridge deck with variable joint rhythm',pts,[],None,c);attr(host.data,'lived_plank_scale',scales,'FLOAT_VECTOR');attr(host.data,'lived_plank_rotation',rot,'FLOAT_VECTOR')
 g,i,o=group('Bounded bridge board profiles',[('Seed','NodeSocketInt',903),('Width Variation','NodeSocketFloat',1.),('Twist','NodeSocketFloat',1.)]);info=g.nodes.new('GeometryNodeCollectionInfo');info.inputs['Collection'].default_value=bank;info.inputs['Separate Children'].default_value=True;info.inputs['Reset Children'].default_value=True;ins=g.nodes.new('GeometryNodeInstanceOnPoints');ins.inputs['Pick Instance'].default_value=True;link(g,i.outputs['Geometry'],ins.inputs['Points']);link(g,info.outputs['Instances'],ins.inputs['Instance']);link(g,named(g,'lived_plank_scale','FLOAT_VECTOR'),ins.inputs['Scale']);v=g.nodes.new('ShaderNodeVectorMath');v.operation='SCALE';link(g,named(g,'lived_plank_rotation','FLOAT_VECTOR'),v.inputs[0]);link(g,i.outputs['Twist'],v.inputs['Scale']);link(g,v.outputs[0],ins.inputs['Rotation']);rand=g.nodes.new('FunctionNodeRandomValue');rand.data_type='INT';rand.inputs['Min'].default_value=0;rand.inputs['Max'].default_value=6;link(g,i.outputs['Seed'],rand.inputs['Seed']);link(g,rand.outputs['Value'],ins.inputs['Instance Index']);link(g,ins.outputs[0],o.inputs[0]);arrange(g);mod=host.modifiers.new(P+'Live board source and twist','NODES');mod.node_group=g
 # Widths follow a bounded cumulative spacing recipe so joints remain open. Remove cosmetic unused input.
 for q in list(g.interface.items_tree):
  if q.item_type=='SOCKET' and q.name=='Width Variation':g.interface.remove(q)
 host['lived_in_semantics']='Width/gap profile generated cumulatively by recipe; live seed selects seven end-profile/material variants; live Twist amplitude is bounded at design default. No support structures moved.'
 # Hall visible floor retains all top heights and support positions; restrained per-board color and narrower variation.
 hall=bpy.data.objects['LIVE GN / hall floor board variation'];hallmod=next(m for m in hall.modifiers if m.type=='NODES');oldg=hallmod.node_group;ng=oldg.copy();ng.name=P+'Hall cedar edge rhythm';hallmod.node_group=ng
 for n in ng.nodes:
  if n.bl_idname=='FunctionNodeRandomValue' and n.data_type=='FLOAT_VECTOR' and n.inputs['Max'].default_value[0]>1:
   n.inputs['Min'].default_value=(.89,.999,.985);n.inputs['Max'].default_value=(1.015,1.001,1.015)
 from bridge_support import repair_arch_pitch
 pitch_report=repair_arch_pitch(host,records)
 return {'arch_pitch':pitch_report,'host':host.name,'baseline_host':old.name,'boards':records,'width_range':[min(widths),max(widths)],'gap_range':[min(gaps),max(gaps)],'native_group':g.name,'hall_height_changes_max_m':.001}

def apply():
 c=coll('Courtyard ground and crafted details');src=coll('Hidden sources');t,ter=terrain_setup();pc,mc,tc=source_shapes(src);sc=build_scatter(t,c,pc,mc,tc);body=moss_body(t,c);contacts=rock_contact_growth(t,c,mc,ter);wood=planks(c)
 report={'version':'0.1 blockout','terrain':ter,'scatter':sc,'moss_body':body,'rock_contact_growth':contacts,'wood':wood,'new_collection':c.name,'notes':['Bank relief, masks and sizes are art-directed. No hydrology/ecology simulation.','Hall/pond/bridge structural transforms unchanged. Existing low moss sheets retained hidden.','Footprint support to be audited after blockout; center ray hits are not enough.']}
 bpy.context.scene['lived_in_pass']='Authored relief, grouped deposits, geometric moss cushions and bounded handcrafted boards. Camera/light/exposure unchanged for comparison.'
 for path in [pathlib.Path(__file__)]:
  text=bpy.data.texts.get(path.name) or bpy.data.texts.new(path.name);text.from_string(path.read_text())
 return report
