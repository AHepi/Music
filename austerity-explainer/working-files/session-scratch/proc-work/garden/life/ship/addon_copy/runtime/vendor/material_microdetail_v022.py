"""Sparse material-specific native detail, v0.1.0.
No image textures. Coordinate masks are object-attached. Real V recesses are exact
Boolean modifiers with retained manifold cutters; shader checks are normal-only.
Use bounded strength and sparse target selection; not a universal weathering model.
"""
import bpy,math,random,hashlib,json,bmesh
from mathutils import Vector,Matrix
VERSION='0.2.2'
PREFIX='MD / '

def node(t,typ,name):
 n=t.nodes.new(typ);n.name=name;n.label=name;return n

def link(t,a,b):t.links.new(a,b)
def mathn(t,op,a,b=None,label=''):
 n=node(t,'ShaderNodeMath',label or op);n.operation=op
 for k,v in enumerate([a,b]):
  if v is None:continue
  if isinstance(v,(int,float)):n.inputs[k].default_value=v
  else:link(t,v,n.inputs[k])
 return n.outputs[0]
def ramp(t,fac,lo,hi,invert=False,label=''):
 n=node(t,'ShaderNodeMapRange',label);n.clamp=True;n.interpolation_type='SMOOTHSTEP';link(t,fac,n.inputs['Value']);n.inputs['From Min'].default_value=lo;n.inputs['From Max'].default_value=hi;n.inputs['To Min'].default_value=1 if invert else 0;n.inputs['To Max'].default_value=0 if invert else 1;return n.outputs['Result']
def socket(g,name,typ,io='INPUT',default=None,lo=None,hi=None):
 s=g.interface.new_socket(name=name,socket_type=typ,in_out=io)
 if default is not None:s.default_value=default
 if lo is not None:s.min_value=lo
 if hi is not None:s.max_value=hi
 return s

def validate_controls(depth,strength,stain):
 for name,value,low,high in [('Depth',depth,0,.008),('Strength',strength,0,1),('Stain',stain,0,.4)]:
  if not isinstance(value,(int,float)) or isinstance(value,bool) or not math.isfinite(value) or not low<=value<=high:raise ValueError(name+' is outside the supported range')

def check_group(*, private=False):
 name=PREFIX+'Finite grain checks v'+VERSION
 if not private and name in bpy.data.node_groups:return bpy.data.node_groups[name]
 g=bpy.data.node_groups.new(name,'ShaderNodeTree')
 socket(g,'Coordinates','NodeSocketVector');socket(g,'Pigment','NodeSocketColor');socket(g,'Normal','NodeSocketVector');socket(g,'Seed','NodeSocketFloat',default=17)
 socket(g,'Width X','NodeSocketFloat',default=.02,lo=.003,hi=.08);socket(g,'Width Y','NodeSocketFloat',default=.02,lo=.003,hi=.08)
 socket(g,'Strength','NodeSocketFloat',default=.45,lo=0,hi=1);socket(g,'Depth','NodeSocketFloat',default=.004,lo=0,hi=.008);socket(g,'Stain','NodeSocketFloat',default=.24,lo=0,hi=.4)
 socket(g,'Pigment','NodeSocketColor','OUTPUT');socket(g,'Normal','NodeSocketVector','OUTPUT');socket(g,'Check Mask','NodeSocketFloat','OUTPUT')
 i=node(g,'NodeGroupInput','Bounded microdetail controls');o=node(g,'NodeGroupOutput','Check channels');sep=node(g,'ShaderNodeSeparateXYZ','Transverse X Y / grain Z');link(g,i.outputs['Coordinates'],sep.inputs[0]);u=sep.outputs['Z']
 mask=None
 for axis in ['X','Y']:
  for j in range(2):
   r=mathn(g,'FRACT',mathn(g,'ADD',mathn(g,'MULTIPLY',i.outputs['Seed'],3.17+j*2.11+(0 if axis=='X' else 1.03)),.37+j*.41))
   center=mathn(g,'ADD',mathn(g,'MULTIPLY',r,.80),.1)
   r2=mathn(g,'FRACT',mathn(g,'ADD',mathn(g,'MULTIPLY',i.outputs['Seed'],8.31+j*.83),j*.23+(0 if axis=='X' else .41)))
   cross=mathn(g,'ADD',mathn(g,'MULTIPLY',r2,.66),.17)
   half=mathn(g,'ADD',mathn(g,'MULTIPLY',r2,.19),.13)
   t=mathn(g,'DIVIDE',mathn(g,'ABSOLUTE',mathn(g,'SUBTRACT',u,center)),half)
   taper=mathn(g,'MAXIMUM',mathn(g,'SUBTRACT',1,mathn(g,'MULTIPLY',t,t)),0)
   width=mathn(g,'ADD',mathn(g,'MULTIPLY',i.outputs['Width '+axis],taper),.00001)
   # Small grain-guided bend: U-only noise cannot turn the check across grain.
   comb=node(g,'ShaderNodeCombineXYZ','One-dimensional grain bend');link(g,u,comb.inputs['Z'])
   n=node(g,'ShaderNodeTexNoise','Low-frequency bend');n.noise_dimensions='4D';n.inputs['Scale'].default_value=9;n.inputs['Detail'].default_value=0;link(g,comb.outputs[0],n.inputs['Vector']);link(g,i.outputs['Seed'],n.inputs['W'])
   bend=mathn(g,'MULTIPLY',mathn(g,'SUBTRACT',n.outputs['Fac'],.5),mathn(g,'MULTIPLY',i.outputs['Width '+axis],2.2))
   d=mathn(g,'ABSOLUTE',mathn(g,'SUBTRACT',mathn(g,'ADD',sep.outputs[axis],bend),cross))
   line=mathn(g,'MAXIMUM',mathn(g,'SUBTRACT',1,mathn(g,'DIVIDE',d,width)),0)
   line=mathn(g,'MULTIPLY',line,ramp(g,t,.85,1,True,'Finite tapered end'))
   keep=mathn(g,'GREATER_THAN',mathn(g,'FRACT',mathn(g,'ADD',i.outputs['Seed'],j*.371+(0 if axis=='X' else .217))),.38)
   line=mathn(g,'MULTIPLY',line,keep);mask=line if mask is None else mathn(g,'MAXIMUM',mask,line)
 b=node(g,'ShaderNodeBump','Normal-only shallow checking');b.invert=True;link(g,mask,b.inputs['Height']);link(g,i.outputs['Strength'],b.inputs['Strength']);link(g,i.outputs['Depth'],b.inputs['Distance']);link(g,i.outputs['Normal'],b.inputs['Normal'])
 factor=mathn(g,'SUBTRACT',1,mathn(g,'MULTIPLY',mask,i.outputs['Stain']))
 m=node(g,'ShaderNodeMixRGB','Local stain inside checks only');m.blend_type='MULTIPLY';m.inputs[0].default_value=1;link(g,i.outputs['Pigment'],m.inputs[1]);link(g,factor,m.inputs[2]);link(g,m.outputs[0],o.inputs['Pigment']);link(g,b.outputs[0],o.inputs['Normal']);link(g,mask,o.inputs['Check Mask'])
 for k,n in enumerate(g.nodes):n.location=((k%12)*190,-(k//12)*155);n.width=170
 g.asset_mark();g.asset_data.description='Finite tapered grain-aligned check masks with bounded normal-only relief and local stain; no isotropic roughness.';return g

def noise_group():
 name=PREFIX+'Isotropic rival v'+VERSION
 if name in bpy.data.node_groups:return bpy.data.node_groups[name]
 g=bpy.data.node_groups.new(name,'ShaderNodeTree')
 for n,t,d in [('Coordinates','NodeSocketVector',None),('Pigment','NodeSocketColor',None),('Normal','NodeSocketVector',None),('Seed','NodeSocketFloat',17),('Strength','NodeSocketFloat',.45),('Depth','NodeSocketFloat',.004),('Stain','NodeSocketFloat',.24)]:socket(g,n,t,default=d)
 for n,t in [('Pigment','NodeSocketColor'),('Normal','NodeSocketVector'),('Check Mask','NodeSocketFloat')]:socket(g,n,t,'OUTPUT')
 i=node(g,'NodeGroupInput','Rival controls');o=node(g,'NodeGroupOutput','Rival channels');n=node(g,'ShaderNodeTexNoise','Isotropic fine roughness rival');n.noise_dimensions='4D';n.inputs['Scale'].default_value=35;n.inputs['Detail'].default_value=1;link(g,i.outputs['Coordinates'],n.inputs['Vector']);link(g,i.outputs['Seed'],n.inputs['W']);mask=ramp(g,n.outputs['Fac'],.60,.72,False,'Sparse roughness coverage')
 b=node(g,'ShaderNodeBump','Normal-only generic relief');b.invert=True;link(g,mask,b.inputs['Height']);link(g,i.outputs['Strength'],b.inputs['Strength']);link(g,i.outputs['Depth'],b.inputs['Distance']);link(g,i.outputs['Normal'],b.inputs['Normal']);fac=mathn(g,'SUBTRACT',1,mathn(g,'MULTIPLY',mask,i.outputs['Stain']));m=node(g,'ShaderNodeMixRGB','Comparable local contrast');m.blend_type='MULTIPLY';m.inputs[0].default_value=1;link(g,i.outputs['Pigment'],m.inputs[1]);link(g,fac,m.inputs[2]);link(g,m.outputs[0],o.inputs['Pigment']);link(g,b.outputs[0],o.inputs['Normal']);link(g,mask,o.inputs['Check Mask']);return g

def local_bounds(o):
 return [min(v.co[j] for v in o.data.vertices) for j in range(3)],[max(v.co[j] for v in o.data.vertices) for j in range(3)]
def clone_tree(g,cache):
 if g.name in cache:return cache[g.name]
 c=g.copy();c.name=PREFIX+'upstream / '+g.name;cache[g.name]=c
 for n in c.nodes:
  if n.type=='GROUP' and n.node_tree:n.node_tree=clone_tree(n.node_tree,cache)
 return c

def add_shading(o,rival=False,depth=.005,strength=.62,stain=.36,*,private_group=False):
 """Object-specific material copy. Existing broad pigment links remain upstream unchanged."""
 validate_controls(depth,strength,stain)
 if o.type!='MESH' or not o.material_slots or not o.material_slots[0].material:raise ValueError('A mesh with a bound material is required')
 lo0,hi0=local_bounds(o)
 if min(hi0[k]-lo0[k] for k in range(3))<=.000001:raise ValueError('Nonzero local extents required')
 original_link=o.material_slots[0].link;orig=o.material_slots[0].material
 if orig.get('md_material_uid'):raise ValueError('Receiver already instrumented')
 source_flag=bool(orig.use_fake_user);orig.use_fake_user=True;m=orig.copy();m.use_fake_user=False;m.name=PREFIX+o.name;cache={}
 for n in m.node_tree.nodes:
  if n.type=='GROUP' and n.node_tree:n.node_tree=clone_tree(n.node_tree,cache)
 lo,hi=local_bounds(o);dims=[hi[k]-lo[k] for k in range(3)];axis=max(range(3),key=lambda k:dims[k]);trans=[k for k in range(3) if k!=axis]
 trees=[m.node_tree]+list(cache.values());added=[]
 for t in trees:
  for bs in list(t.nodes):
   if bs.type!='BSDF_PRINCIPLED':continue
   oldcol=bs.inputs['Base Color'].links[0].from_socket if bs.inputs['Base Color'].is_linked else None
   oldnor=bs.inputs['Normal'].links[0].from_socket if bs.inputs['Normal'].is_linked else None
   g=node(t,'ShaderNodeGroup','Microdetail / isolated normal and check stain');g.node_tree=noise_group() if rival else check_group(private=private_group);g.inputs['Depth'].default_value=depth;g.inputs['Strength'].default_value=strength;g.inputs['Stain'].default_value=stain
   tc=node(t,'ShaderNodeTexCoord','Microdetail / local object coordinates');oi=node(t,'ShaderNodeObjectInfo','Microdetail / deterministic instance variation');seed=mathn(t,'ADD',mathn(t,'MULTIPLY',oi.outputs['Random'],37.73),19.17);link(t,seed,g.inputs['Seed'])
   if rival:link(t,tc.outputs['Object'],g.inputs['Coordinates'])
   else:
    sp=node(t,'ShaderNodeSeparateXYZ','Microdetail / normalized rest coordinates');link(t,tc.outputs['Generated'],sp.inputs[0]);comb=node(t,'ShaderNodeCombineXYZ','Microdetail / long-axis alignment')
    for outaxis,srcaxis in zip('XYZ',trans+[axis]):link(t,sp.outputs[srcaxis],comb.inputs[outaxis])
    link(t,comb.outputs[0],g.inputs['Coordinates']);g.inputs['Width X'].default_value=min(.06,max(.005,.0048/dims[trans[0]]));g.inputs['Width Y'].default_value=min(.06,max(.005,.0048/dims[trans[1]]))
   if oldcol:link(t,oldcol,g.inputs['Pigment'])
   else:g.inputs['Pigment'].default_value=bs.inputs['Base Color'].default_value
   if oldnor:link(t,oldnor,g.inputs['Normal'])
   else:
    geo=node(t,'ShaderNodeNewGeometry','Microdetail / original normal');link(t,geo.outputs['Normal'],g.inputs['Normal'])
   link(t,g.outputs['Pigment'],bs.inputs['Base Color']);link(t,g.outputs['Normal'],bs.inputs['Normal']);added.append(t.name)
 if not added:raise RuntimeError('No Principled shader for '+o.name)
 uid=hashlib.sha256((o.name+'|material|'+VERSION).encode()).hexdigest();m['md_material_uid']=uid;m['md_source_material']=orig;m['md_target_object']=o;m['md_original_link']=original_link;m['md_original_fake_user']=source_flag
 o.material_slots[0].link='OBJECT';o.material_slots[0].material=m
 return {'material_uid':uid,'original_fake_user':source_flag,'object':o.name,'original_material':orig.name,'original_link':original_link,'material':m.name,'grain_axis':'XYZ'[axis],'local_dimensions':dims,'shader_groups':added,'rival':rival,'depth_normal_only':depth,'strength':strength,'stain':stain}

def cutter_collection():
 c=bpy.data.collections.get(PREFIX+'retained V groove cutters')
 if not c:c=bpy.data.collections.new(PREFIX+'retained V groove cutters');bpy.context.scene.collection.children.link(c)
 return c

def make_cutter(target,name,sections,interior_factor=.68):
 """sections: center surface point, tangent, outward normal, halfwidth, cut depth.
Triangular closed volume above the surface and below it. Not an overlay."""
 vs=[];fs=[]
 for p,t,n,w,d in sections:
  p,t,n=Vector(p),Vector(t).normalized(),Vector(n).normalized();side=t.cross(n).normalized();w=max(w,.0002)
  vs.extend([tuple(p+side*w+n*.012),tuple(p-side*w+n*.012),tuple(p-n*d)])
 for j in range(len(sections)-1):
  a=j*3;b=a+3
  fs.extend([(a,b,b+1,a+1),(a+1,b+1,b+2,a+2),(a+2,b+2,b,a)])
 fs.extend([(2,1,0),tuple(range(len(vs)-3,len(vs)))])
 me=bpy.data.meshes.new(name+' mesh');me.from_pydata(vs,[],fs);me.update();bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
 c=bpy.data.objects.new(name,me);cutter_collection().objects.link(c);c.parent=target;c.matrix_parent_inverse=Matrix.Identity(4);c.matrix_basis=Matrix.Identity(4);c.hide_render=True;c.hide_set(True);c.display_type='WIRE'
 # Transfer a bounded darker version of the original substrate to actual interior faces.
 orig=target.material_slots[0].material;dark=orig.copy();dark.name=PREFIX+'recess substrate / '+target.name
 for key in list(dark.keys()):
  if key.startswith('md_'):del dark[key]
 cache={}
 for n in dark.node_tree.nodes:
  if n.type=='GROUP' and n.node_tree:n.node_tree=clone_tree(n.node_tree,cache)
 for t in [dark.node_tree]+list(cache.values()):
  for b in list(t.nodes):
   if b.type!='BSDF_PRINCIPLED':continue
   src=b.inputs['Base Color'].links[0].from_socket if b.inputs['Base Color'].is_linked else None
   mix=node(t,'ShaderNodeMixRGB','Recess / restrained substrate staining');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[2].default_value=(interior_factor,)*3+(1,)
   if src:link(t,src,mix.inputs[1])
   else:mix.inputs[1].default_value=b.inputs['Base Color'].default_value
   link(t,mix.outputs[0],b.inputs['Base Color'])
 idx=len(target.data.materials);target.data.materials.append(dark)
 for mat in target.data.materials:me.materials.append(mat)
 for poly in me.polygons:poly.material_index=idx
 mod=target.modifiers.new(PREFIX+'actual shallow V recess','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=c
 if hasattr(mod,'material_mode'):mod.material_mode='INDEX'
 c['microdetail_role']='Closed subtractive cutter; hidden from render. Recess is boolean difference, not an overlay.'
 uid=hashlib.sha256((target.name+'|'+name+'|'+VERSION).encode()).hexdigest();c['md_cutter_uid']=uid;c['md_target_object']=target;c['md_interior_material']=dark
 return {'cutter_uid':uid,'object':target.name,'cutter':c.name,'modifier':mod.name,'vertices':len(vs),'faces':len(fs),'max_depth_local':max(s[4] for s in sections),'max_half_width_local':max(s[3] for s in sections),'material_slot':idx}

def wood_cut(o,seed=1):
 r=random.Random(seed);lo,hi=local_bounds(o);dims=[hi[k]-lo[k] for k in range(3)]
 if min(dims)<.05 or max(dims)<.4:raise ValueError('Timber default cut requires transverse extent at least0.05 and length at least0.4local units')
 a=max(range(3),key=lambda k:dims[k]);others=[k for k in range(3) if k!=a]
 # For horizontal rails select a face visible from above; vertical posts face the garden.
 if a==2 and dims[2]>1.7:naxis=1;sgn=-1
 else:
  up=Vector((0,0,1));opts=[(abs((o.matrix_world.to_3x3()@Vector(tuple(1 if k==axis else 0 for k in range(3)))).dot(up)),axis) for axis in others]
  naxis=max(opts)[1];sgn=1 if (o.matrix_world.to_3x3()@Vector(tuple(1 if k==naxis else 0 for k in range(3)))).z>=0 else -1
  if abs((o.matrix_world.to_3x3()@Vector(tuple(1 if k==naxis else 0 for k in range(3)))).z)<.4:naxis=1;sgn=-1
 across=next(k for k in others if k!=naxis);face=hi[naxis] if sgn>0 else lo[naxis]
 length=min(dims[a]*.52,.78);start=lo[a]+dims[a]*r.uniform(.15,.28);cross=(lo[across]+hi[across])*.5+dims[across]*r.uniform(-.15,.15);N=7;pts=[]
 for j in range(N):
  t=j/(N-1);p=[0.,0.,0.];p[a]=start+length*t;p[across]=cross+math.sin(t*5+r.random())*.002;p[naxis]=face;pts.append(Vector(p))
 sections=[]
 for j,p in enumerate(pts):
  t=j/(N-1);tangent=pts[min(j+1,N-1)]-pts[max(0,j-1)];normal=Vector(tuple(sgn if k==naxis else 0 for k in range(3)));taper=math.sin(math.pi*t)**.7;sections.append((p,tangent,normal,.0038*taper+.0002,.006*taper+.0002))
 return make_cutter(o,PREFIX+'timber check cutter / '+o.name,sections,.66)

def stone_cut(o,seed=1):
 r=random.Random(seed);deps=bpy.context.evaluated_depsgraph_get();ev=o.evaluated_get(deps);lo,hi=local_bounds(o);sx,sy=hi[0]-lo[0],hi[1]-lo[1];angle=r.uniform(-1,1);d=Vector((math.cos(angle),math.sin(angle),0));side=Vector((-d.y,d.x,0));center=Vector(((lo[0]+hi[0])/2,(lo[1]+hi[1])/2,0));span=min(sx,sy)*.66
 pts=[]
 for j in range(7):
  t=j/6;p=center+d*((t-.5)*span)+side*(([0,.024,.040,-.012,-.025,-.008,0][j]+r.uniform(-.007,.007))*span);origin=Vector((p.x,p.y,hi[2]+2));hit,loc,n,fi=ev.ray_cast(origin,Vector((0,0,-1)))
  if hit:pts.append(loc)
 if len(pts)<4:raise RuntimeError('Insufficient stone hits '+o.name)
 sections=[]
 for j,p in enumerate(pts):
  t=j/(len(pts)-1);tan=pts[min(j+1,len(pts)-1)]-pts[max(0,j-1)];taper=math.sin(math.pi*t)**.6;sections.append((p,tan,Vector((0,0,1)),.007*taper*[.2,.65,1,.40,.77,.38,.1][j]+.0002,.022*taper*[.3,.8,1,.7,.9,.5,.2][j]+.0005))
 return make_cutter(o,PREFIX+'stone fissure cutter / '+o.name,sections,.78)

def apply(rival=False):
 if any(o.name.startswith(PREFIX) for o in bpy.context.scene.objects):raise ValueError('Already instrumented; reopen source to build a fresh variant')
 timber_prefix=('Cedar structural post','Front and back tie beam','Deep side tie beam','Bridge low rail post','Low garden bridge handrail','SOURCE / short bridge deck plank','SOURCE / veranda cedar board','Garden gate post','Gate lintel')
 targets=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.name.startswith(timber_prefix)]
 report={'version':VERSION,'rival':rival,'shading':[],'geometry':[]}
 for o in targets:report['shading'].append(add_shading(o,rival))
 stones=['Garden anchor boulder 00','Garden anchor boulder 02','Embedded shore stone 18','Embedded shore stone 21','Embedded shore stone 22','Embedded shore stone 25','Embedded shore stone 27']
 if rival:
  for name in stones:report['shading'].append(add_shading(bpy.data.objects[name],True,depth=.006,strength=.45,stain=.24))
 else:
  for i,name in enumerate(['Cedar structural post.002','Cedar structural post.004','Bridge low rail post.001','Bridge low rail post.003','Low garden bridge handrail.004','Low garden bridge handrail.005']):report['geometry'].append(wood_cut(bpy.data.objects[name],321+i))
  for i,name in enumerate(stones):report['geometry'].append(stone_cut(bpy.data.objects[name],701+i))
 if not rival:report['deck_variants']=deck_variants(report)
 return report

def remove(report):
 if report.get('deck_variants'):
  d=report['deck_variants'];bpy.data.objects[d['host']].modifiers[d['modifier']].node_group=bpy.data.node_groups[d['original_group']]
 for row in report['geometry']:
  o=bpy.data.objects[row['object']];m=o.modifiers.get(row['modifier'])
  if m:o.modifiers.remove(m)
  c=bpy.data.objects.get(row['cutter'])
  if c:bpy.data.objects.remove(c,do_unlink=True)
  # Added interior slot is always last on each targeted object.
  if len(o.data.materials)>row['material_slot']:o.data.materials.pop(index=row['material_slot'])
 for row in report['shading']:
  o=bpy.data.objects[row['object']];o.material_slots[0].material=bpy.data.materials[row['original_material']];o.material_slots[0].link=row['original_link']
 if report.get('deck_variants'):
  for name in report['deck_variants']['prototypes']:
   o=bpy.data.objects.get(name)
   if o:bpy.data.objects.remove(o,do_unlink=True)
 return True

def deck_variants(report):
 """Keep original live points, rotation, scale, and seed. Substitute 2 checked +5 intact sources."""
 source=bpy.data.objects['SOURCE / short bridge deck plank'];host=bpy.data.objects['LIVE GN / footbridge individual boards'];mod=next(m for m in host.modifiers if m.type=='NODES');old=mod.node_group;oldflag=bool(old.use_fake_user);old.use_fake_user=True;g=old.copy();g.use_fake_user=False;g.name=PREFIX+'Bridge deck / sparse end-check sources';mod.node_group=g
 guid=hashlib.sha256((host.name+'|deck|'+VERSION).encode()).hexdigest();g['md_group_uid']=guid;g['md_source_group']=old;g['md_original_fake_user']=oldflag;g['md_target_object']=host
 col=bpy.data.collections.new(PREFIX+'bridge source variants');bpy.context.scene.collection.children.link(col);protos=[]
 for j in range(7):
  o=source.copy();o.data=source.data.copy();o.name=PREFIX+f'plank prototype {j:02d}';col.objects.link(o);o.hide_render=True;o.hide_set(True);o['md_prototype_uid']=hashlib.sha256((o.name+'|prototype|'+VERSION).encode()).hexdigest();protos.append(o)
  if j not in (2,6):continue
  sign=-1 if j==2 else 1;length=.34 if j==2 else .49;cross=-.028 if j==2 else .037;lo,hi=local_bounds(o);end=lo[0] if sign<0 else hi[0];pts=[]
  for k in range(7):
   t=k/6;p=Vector((end-sign*(length*t-.018),cross+(.003*math.sin(t*4.3))*(1-t),hi[2]));pts.append(p)
  sections=[]
  for k,p in enumerate(pts):
   t=k/6;tan=pts[min(k+1,6)]-pts[max(0,k-1)];w=.0065*(1-t)**.8*(1+.18*math.sin(t*11))+.0001;depth=.012*(1-t)**.6+.0002;sections.append((p,tan,Vector((0,0,1)),w,depth))
  row=make_cutter(o,PREFIX+'deck end check cutter / '+o.name,sections,.69);report['geometry'].append(row)
 inst=next(n for n in g.nodes if n.type=='INSTANCE_ON_POINTS');join=node(g,'GeometryNodeJoinGeometry','Sparse variant source set / five intact two checked')
 for j,o in enumerate(protos):
  n=node(g,'GeometryNodeObjectInfo',f'End-check source {j}');n.inputs['Object'].default_value=o;n.inputs['As Instance'].default_value=True;n.transform_space='ORIGINAL';link(g,n.outputs['Geometry'],join.inputs['Geometry']);n.location=(-450,j*-180)
 link(g,join.outputs['Geometry'],inst.inputs['Instance']);inst.inputs['Pick Instance'].default_value=True
 idx=node(g,'FunctionNodeRandomValue','Stable sparse end-check choice');idx.data_type='INT'
 for inp in idx.inputs:
  if inp.name=='Min' and inp.bl_idname=='NodeSocketInt':inp.default_value=0
  elif inp.name=='Max' and inp.bl_idname=='NodeSocketInt':inp.default_value=6
 idx.inputs['Seed'].default_value=21439
 out=next(x for x in idx.outputs if x.bl_idname=='NodeSocketInt');link(g,out,inst.inputs['Instance Index'])
 join.location=(-170,30);idx.location=(30,-260);g.asset_mark();g.asset_data.description='Original bridge anchor points and transform randomization remain unchanged. Seven source variants, two with shallow true end checks; five intact. Seed21439.'
 return {'group_uid':guid,'original_fake_user':oldflag,'prototype_uids':[o['md_prototype_uid'] for o in protos],'host':host.name,'modifier':mod.name,'original_group':old.name,'group':g.name,'prototypes':[o.name for o in protos],'seed':21439,'checked_indices':[2,6],'intact_indices':[0,1,3,4,5],'unchanged':'Original host points, scale/rotation random nodes, seeds, transforms, plank dimensions'}

# Reopen-safe restoration. Pointer custom properties retain exact IDs; names are labels only.
def _unique(items,key,value):
 found=[x for x in items if x.get(key)==value]
 if len(found)!=1:raise ValueError('Missing or ambiguous retained identity: '+key)
 return found[0]

def remove(report):
 """Preflight all targets, then restore exact retained pointers. Refuse external edits.
Material/cutter/object/group renaming and same-name decoys cannot redirect restoration.
Original fake-user flags are restored after bindings. Private unused data is kept.
"""
 materials=[];cuts=[];protos=[];deck=None
 for row in report['shading']:
  m=_unique(bpy.data.materials,'md_material_uid',row['material_uid']);o=m.get('md_target_object');orig=m.get('md_source_material')
  if not isinstance(o,bpy.types.Object) or not isinstance(orig,bpy.types.Material):raise ValueError('Lost material target/source pointer')
  if not o.material_slots or o.material_slots[0].material!=m or o.material_slots[0].link!='OBJECT':raise ValueError('Receiver binding changed since application')
  if m['md_original_link']=='DATA' and o.data.materials[0]!=orig:raise ValueError('Original DATA slot changed')
  materials.append((m,o,orig,m['md_original_link'],bool(m['md_original_fake_user'])))
 for row in report['geometry']:
  c=_unique(bpy.data.objects,'md_cutter_uid',row['cutter_uid']);o=c.get('md_target_object');dark=c.get('md_interior_material')
  if not isinstance(o,bpy.types.Object) or c.parent!=o:raise ValueError('Cutter attachment changed')
  mods=[m for m in o.modifiers if m.type=='BOOLEAN' and m.object==c]
  if len(mods)!=1:raise ValueError('Cutter boolean missing or ambiguous')
  idx=row['material_slot']
  if len(o.data.materials)!=idx+1 or o.data.materials[idx]!=dark:raise ValueError('Recess material slots changed')
  cuts.append((o,c,mods[0],idx))
 if report.get('deck_variants'):
  d=report['deck_variants'];g=_unique(bpy.data.node_groups,'md_group_uid',d['group_uid']);host=g.get('md_target_object');old=g.get('md_source_group')
  if not isinstance(host,bpy.types.Object) or not isinstance(old,bpy.types.NodeTree):raise ValueError('Lost bridge group pointer')
  mods=[m for m in host.modifiers if m.type=='NODES' and m.node_group==g]
  if len(mods)!=1:raise ValueError('Bridge GN binding changed')
  deck=(mods[0],old,bool(g['md_original_fake_user']))
  protos=[_unique(bpy.data.objects,'md_prototype_uid',uid) for uid in d['prototype_uids']]
 # No mutations above this line.
 if deck:deck[0].node_group=deck[1]
 for o,c,m,idx in cuts:o.modifiers.remove(m);o.data.materials.pop(index=idx);bpy.data.objects.remove(c,do_unlink=True)
 flags={}
 for m,o,orig,mode,flag in materials:
  o.material_slots[0].material=orig;o.material_slots[0].link=mode
  flags[orig]=flags.get(orig,True) and flag
 for orig,flag in flags.items():orig.use_fake_user=flag
 if deck:deck[1].use_fake_user=deck[2]
 for o in protos:bpy.data.objects.remove(o,do_unlink=True)
 return {'restored_materials':len(materials),'removed_recesses':len(cuts),'restored_bridge_group':bool(deck)}
