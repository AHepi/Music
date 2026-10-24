"""Painted Fields 0.1: explicit, private Base-Color-only atlas insertion.
Blender 5.1. No install/handlers. Local-object box projection; spans are local units.
Source atlas must remain whole. Surface maps are color studies, never measured albedo.
"""
import bpy, math, json, hashlib
from dataclasses import dataclass, asdict
from pathlib import Path

VERSION='0.1.0'
ATLAS_SHA256='a8aeb046cc76f9f633e0397b7343d28cf55c4290511869eca24347d607efc2f1'
MEANS={'timber':(.07437406286506952,.045206115512307465,.026978752724687416), 'plaster':(.7247038860367877,.5919426938501364,.40570050931638313)}
@dataclass(frozen=True)
class FieldSpec:
    kind: str
    grain_axis: str='X'
    longitudinal_span: float=2.2
    transverse_span: float=.65
    seed: int=41
    strength: float=.85
    palette_mean: tuple=(.1,.06,.03)
    projection: str='LOCAL_BOX_MIRROR'
    flat: bool=False
    axis_swap: bool=False

def validate(spec):
    if not isinstance(spec,FieldSpec):raise TypeError('Use a FieldSpec')
    if spec.kind not in MEANS:raise ValueError('Only timber and plaster are implemented')
    if spec.grain_axis not in ('X','Y','Z'):raise ValueError('Declare local grain axis X, Y or Z')
    if spec.projection!='LOCAL_BOX_MIRROR':raise ValueError('Only LOCAL_BOX_MIRROR is implemented')
    for k in ('longitudinal_span','transverse_span'):
        v=getattr(spec,k)
        if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not .05<=v<=20:raise ValueError(k+' must be .05..20 local units')
    if isinstance(spec.strength,bool) or not isinstance(spec.strength,(int,float)) or not math.isfinite(spec.strength) or not 0<=spec.strength<=1:raise ValueError('Strength must be 0..1')
    if type(spec.seed) is not int or not 0<=spec.seed<=10000:raise ValueError('Seed must be an integer 0..10000')
    if len(spec.palette_mean)!=3 or any(not isinstance(v,(int,float)) or not math.isfinite(v) or not 0<=v<=1 for v in spec.palette_mean):raise ValueError('palette_mean is three finite linear RGB values 0..1')
    if type(spec.flat) is not bool or type(spec.axis_swap) is not bool:raise ValueError('Flat and axis_swap are booleans')
    return spec

def _node(t,typ,name):
    n=t.nodes.new(typ);n.name=name;n.label=name;return n

def _wire(t,source,target):
    if isinstance(source,tuple) and len(source)==2 and hasattr(source[0],'outputs'):t.links.new(source[0].outputs[source[1]],target)
    else:target.default_value=source

def _math(t,op,name,a,b=None):
    n=_node(t,'ShaderNodeMath',name);n.operation=op;_wire(t,a,n.inputs[0])
    if b is not None:_wire(t,b,n.inputs[1])
    return n,0

def _vec(t,op,name,a,b=None):
    n=_node(t,'ShaderNodeVectorMath',name);n.operation=op;_wire(t,a,n.inputs[0])
    if b is not None:_wire(t,b,n.inputs[1])
    return n,'Vector'

def _mix(t,name,f,a,b):
    n=_node(t,'ShaderNodeMixRGB',name);_wire(t,f,n.inputs[0]);_wire(t,a,n.inputs[1]);_wire(t,b,n.inputs[2]);return n,'Color'

def _socket(t,name,typ,direction='INPUT',default=None,lo=None,hi=None):
    s=t.interface.new_socket(name=name,in_out=direction,socket_type=typ)
    if default is not None:s.default_value=default
    if lo is not None:s.min_value=lo
    if hi is not None:s.max_value=hi
    return s

def build_color_group(name,spec,image):
    validate(spec)
    g=bpy.data.node_groups.new(name,'ShaderNodeTree')
    _socket(g,'Original Color','NodeSocketColor',default=(.2,.2,.2,1))
    _socket(g,'Palette Mean','NodeSocketColor',default=(*spec.palette_mean,1))
    for label,value,lo,hi in [('Strength',spec.strength,0,1),('Seed',spec.seed,0,10000),('Longitudinal Span',spec.longitudinal_span,.05,20),('Transverse Span',spec.transverse_span,.05,20),('Flat Alternative',float(spec.flat),0,1),('Swap Pattern Axes',float(spec.axis_swap),0,1)]:_socket(g,label,'NodeSocketFloat',default=value,lo=lo,hi=hi)
    _socket(g,'Color','NodeSocketColor','OUTPUT')
    inp=_node(g,'NodeGroupInput','Declared color controls');out=_node(g,'NodeGroupOutput','Color only')
    tc=_node(g,'ShaderNodeTexCoord','Object local position');sep=_node(g,'ShaderNodeSeparateXYZ','Local axes');_wire(g,(tc,'Object'),sep.inputs[0])
    geom=_node(g,'ShaderNodeNewGeometry','Unmodified geometric normal');normal=_node(g,'ShaderNodeVectorTransform','World normal to local');normal.vector_type='NORMAL';normal.convert_from='WORLD';normal.convert_to='OBJECT';_wire(g,(geom,'Normal'),normal.inputs['Vector'])
    ns=_node(g,'ShaderNodeSeparateXYZ','Local normal axes');_wire(g,(normal,'Vector'),ns.inputs[0])
    order={'X':('X','Y','Z'),'Y':('Y','X','Z'),'Z':('Z','X','Y')}[spec.grain_axis]
    coords=[(sep,a) for a in order];norms=[(ns,a) for a in order]
    weights=[_math(g,'POWER','Box face weight '+str(i),_math(g,'ABSOLUTE','Unsigned normal '+str(i),v),8) for i,v in enumerate(norms)]
    denom=_math(g,'MAXIMUM','Nonzero normal sum',_math(g,'ADD','Normal sum',_math(g,'ADD','Normal XY sum',weights[0],weights[1]),weights[2]),1e-8)
    weights=[_math(g,'DIVIDE','Normalized box weight '+str(i),v,denom) for i,v in enumerate(weights)]
    # Coordinates are mirrored within the selected inset quadrant, not across the atlas.
    phases=[_math(g,'FRACT','Seed phase '+str(i),_math(g,'MULTIPLY','Seed mixing '+str(i),(inp,'Seed'),c)) for i,c in enumerate((.61803398875,.41421356237,.73205080757))]
    inset=4/1254;u0=inset+(0 if spec.kind=='timber' else .5);v0=.5+inset;extent=.5-2*inset
    planes=[(1,2,'Transverse Span','Transverse Span'),(0,2,'Longitudinal Span','Transverse Span'),(0,1,'Longitudinal Span','Transverse Span')]
    textures=[]
    for face,(a,b,span_a,span_b) in enumerate(planes):
        # Axis transposition makes an orthogonal-grain negative; it is not a signed rotation.
        ua=_mix(g,'Axis swap U '+str(face),(inp,'Swap Pattern Axes'),coords[a],coords[b])
        vb=_mix(g,'Axis swap V '+str(face),(inp,'Swap Pattern Axes'),coords[b],coords[a])
        us=_math(g,'DIVIDE','U local span '+str(face),ua,(inp,span_a));vs=_math(g,'DIVIDE','V local span '+str(face),vb,(inp,span_b))
        us=_math(g,'PINGPONG','U mirrored repeat '+str(face),_math(g,'ADD','U seeded offset '+str(face),us,phases[face]),1)
        vs=_math(g,'PINGPONG','V mirrored repeat '+str(face),_math(g,'ADD','V seeded offset '+str(face),vs,phases[(face+1)%3]),1)
        us=_math(g,'ADD','Inset quadrant U '+str(face),_math(g,'MULTIPLY','Quadrant U extent '+str(face),us,extent),u0)
        vs=_math(g,'ADD','Inset quadrant V '+str(face),_math(g,'MULTIPLY','Quadrant V extent '+str(face),vs,extent),v0)
        uv=_node(g,'ShaderNodeCombineXYZ','Quadrant coordinates '+str(face));_wire(g,us,uv.inputs['X']);_wire(g,vs,uv.inputs['Y'])
        tex=_node(g,'ShaderNodeTexImage','Generated color study / face '+str(face));tex.image=image;tex.interpolation='Linear';tex.extension='EXTEND';_wire(g,(uv,'Vector'),tex.inputs['Vector'])
        textures.append(_vec(g,'MULTIPLY','Weighted pigment '+str(face),(tex,'Color'),weights[face]))
    combined=_vec(g,'ADD','Three local projections',_vec(g,'ADD','First two local projections',textures[0],textures[1]),textures[2])
    normalized=_vec(g,'MULTIPLY','Normalize source mean',combined,tuple(1/v for v in MEANS[spec.kind]))
    tinted=_vec(g,'MULTIPLY','Declared receiver palette',normalized,(inp,'Palette Mean'))
    selected=_mix(g,'Structured field or flat rival',(inp,'Flat Alternative'),tinted,(inp,'Palette Mean'))
    color=_mix(g,'Strength / original color',(inp,'Strength'),(inp,'Original Color'),selected)
    _wire(g,color,out.inputs['Color'])
    for i,n in enumerate(g.nodes):n.location=((i%9)*210,-(i//9)*220);n.width=190
    g['painted_fields_version']=VERSION;g['field_spec']=json.dumps(asdict(spec));g['color_study_not_measured_albedo']=True;g['source_mean_linear']=MEANS[spec.kind]
    return g

def _shader_path(material):
    if not material or not material.use_nodes:raise ValueError('A node material is required')
    outputs=[n for n in material.node_tree.nodes if n.type=='OUTPUT_MATERIAL' and n.is_active_output]
    if len(outputs)!=1:raise ValueError('Exactly one active Material Output is required')
    def walk(sock,groups):
        if len(sock.links)!=1:raise ValueError('The active shader route must be singly connected')
        src=sock.links[0].from_socket;n=src.node
        if n.type=='BSDF_PRINCIPLED':return groups,n.name
        if n.type=='GROUP':
            outs=[x for x in n.node_tree.nodes if x.type=='GROUP_OUTPUT' and x.is_active_output]
            if len(outs)!=1:raise ValueError('Exactly one active Group Output is required')
            target=next((x for x in outs[0].inputs if x.identifier==src.identifier),None)
            if target is None:target=outs[0].inputs.get(src.name)
            if target is None:raise ValueError('Cannot resolve active group shader socket')
            return walk(target,groups+[n.name])
        raise ValueError('Only a direct Principled shader through group outputs is supported; mix/add/custom shaders require explicit handling')
    return walk(outputs[0].inputs['Surface'],[])

def apply_to_receiver(obj,slot_index,spec,atlas_path):
    """Create a private OBJECT material override. Returns a JSON-safe handle.
    Validates before any receiver binding mutation. Does not edit mesh DATA slots.
    """
    validate(spec)
    if obj.type!='MESH' or type(slot_index) is not int or not 0<=slot_index<len(obj.material_slots):raise ValueError('Choose an existing mesh material slot')
    slot=obj.material_slots[slot_index];source=slot.material
    if source and source.get('painted_fields_version'):
        raise ValueError('Receiver already has Painted Fields; restore it before applying a new field')
    path,bsname=_shader_path(source)
    p=Path(atlas_path)
    if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest()!=ATLAS_SHA256:raise ValueError('Expected unchanged bundled generated pigment atlas v01')
    image=bpy.data.images.load(str(p),check_existing=True);image.colorspace_settings.name='sRGB';image.pack()
    if tuple(image.size)!=(1254,1254):raise ValueError('Atlas dimensions differ from the declared quadrant contract')
    material=source.copy();material.name='PF / '+obj.name
    tree=material.node_tree;private=[]
    for name in path:
        node=tree.nodes[name];node.node_tree=node.node_tree.copy();node.node_tree.name='PF upstream / '+obj.name+' / '+name;tree=node.node_tree;private.append(tree.name)
    bs=tree.nodes[bsname];base=bs.inputs['Base Color'];old=base.links[0].from_socket if base.is_linked else None
    color=_node(tree,'ShaderNodeGroup','PF / color-only insertion');color.node_tree=build_color_group('PF color / '+obj.name,spec,image)
    for name,value in [('Palette Mean',(*spec.palette_mean,1)),('Strength',spec.strength),('Seed',spec.seed),('Longitudinal Span',spec.longitudinal_span),('Transverse Span',spec.transverse_span),('Flat Alternative',float(spec.flat)),('Swap Pattern Axes',float(spec.axis_swap))]:color.inputs[name].default_value=value
    if old:tree.links.new(old,color.inputs['Original Color'])
    else:color.inputs['Original Color'].default_value=base.default_value
    original={'node':old.node.name,'socket':old.identifier} if old else {'default':list(base.default_value)}
    # Strength exactly zero takes the original direct link, not merely a black mix.
    if spec.strength!=0:tree.links.new(color.outputs['Color'],base)
    material['painted_fields_version']=VERSION;material['pf_handle']=json.dumps({'groups':path,'principled':bsname,'insert':'PF / color-only insertion','original':original})
    material['pf_spec']=json.dumps(asdict(spec));material['pf_source_material']=source.name
    before={'link':slot.link,'material':source.name};material['pf_original_link']=slot.link;slot.link='OBJECT';slot.material=material
    return {'object':obj.name,'slot':slot_index,'before':before,'material':material.name,'upstream_groups':private,'color_group':color.node_tree.name,'spec':asdict(spec),'original_base_color':original}

def set_controls(material,*,strength=None,flat=None,axis_swap=None,seed=None):
    """Edit only controls in this private material. Strength zero reconnects original."""
    handle=json.loads(material['pf_handle']);tree=material.node_tree
    for name in handle['groups']:tree=tree.nodes[name].node_tree
    insert=tree.nodes[handle['insert']];bs=tree.nodes[handle['principled']]
    swap_input='Swap Pattern Axes' if 'Swap Pattern Axes' in insert.inputs else 'Rotate Pattern 90'
    if strength is not None:
        if isinstance(strength,bool) or not isinstance(strength,(int,float)) or not math.isfinite(strength) or not 0<=strength<=1:raise ValueError('Strength must be 0..1')
    if seed is not None and (type(seed) is not int or not 0<=seed<=10000):raise ValueError('Seed must be integer 0..10000')
    if flat is not None and type(flat) is not bool:raise ValueError('flat must be boolean')
    if axis_swap is not None and type(axis_swap) is not bool:raise ValueError('axis_swap must be boolean')
    for name,value in [('Strength',strength),('Flat Alternative',flat),(swap_input,axis_swap),('Seed',seed)]:
        if value is not None:insert.inputs[name].default_value=float(value)
    base=bs.inputs['Base Color'];zero=insert.inputs['Strength'].default_value==0
    for link in list(base.links):tree.links.remove(link)
    if zero:
        orig=handle['original']
        if 'node' in orig:
            n=tree.nodes[orig['node']];sock=next(s for s in n.outputs if s.identifier==orig['socket']);tree.links.new(sock,base)
        else:base.default_value=orig['default']
    else:tree.links.new(insert.outputs['Color'],base)
    current={'strength':insert.inputs['Strength'].default_value,'flat':bool(insert.inputs['Flat Alternative'].default_value),'axis_swap':bool(insert.inputs[swap_input].default_value),'seed':int(insert.inputs['Seed'].default_value),'direct_bypass':zero}
    spec=json.loads(material['pf_spec']);spec.pop('rotate_90',None);spec.update({k:v for k,v in current.items() if k!='direct_bypass'});material['pf_spec']=json.dumps(spec)
    return current

def restore_receiver(obj,slot_index):
    """Restore the original source material binding recorded by apply_to_receiver.
    Private orphan IDs are retained deliberately, so cleanup never deletes user data.
    """
    slot=obj.material_slots[slot_index];m=slot.material
    if not m or 'pf_source_material' not in m:raise ValueError('Not a Painted Fields receiver')
    source=bpy.data.materials.get(m['pf_source_material'])
    if not source:raise ValueError('Original source material is unavailable')
    # Original binding mode is saved by apply_to_receiver on the private material.
    original_link=m.get('pf_original_link','OBJECT')
    if original_link=='DATA' and obj.data.materials[slot_index]!=source:raise ValueError('Mesh DATA binding changed since application; restore it explicitly rather than overwrite another edit')
    slot.material=source;slot.link=original_link
    return {'link':slot.link,'material':slot.material.name if slot.material else None}
