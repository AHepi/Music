"""Background palette recipe 0.1.0. A tested narrow color-only operation.
No fog physics, auto-distance classification, tree creation or object-name inference.
Caller explicitly identifies every receiver, slot, layer and supported shader kind.
"""
import bpy,math
from dataclasses import dataclass

@dataclass(frozen=True)
class Receiver:
    obj: object
    slot: int
    layer: str
    kind: str  # 'emission_two_stop_wash' or 'constant_principled_wash'


def _graph(material,kind):
    if not material or not material.use_nodes:raise ValueError('A node material is required')
    nt=material.node_tree;nodes=list(nt.nodes)
    types=sorted(n.bl_idname for n in nodes)
    if kind=='emission_two_stop_wash':
        expected=sorted(['ShaderNodeOutputMaterial','ShaderNodeEmission','ShaderNodeTexCoord','ShaderNodeTexNoise','ShaderNodeValToRGB'])
        if types!=expected:raise ValueError('Unsupported emission-wash graph')
        ramp=next(n for n in nodes if n.bl_idname=='ShaderNodeValToRGB')
        if len(ramp.color_ramp.elements)!=2:raise ValueError('Exactly two ramp stops are required')
        expected_links={('ShaderNodeTexCoord','Object','ShaderNodeTexNoise','Vector'),('ShaderNodeTexNoise','Fac','ShaderNodeValToRGB','Fac'),('ShaderNodeValToRGB','Color','ShaderNodeEmission','Color'),('ShaderNodeEmission','Emission','ShaderNodeOutputMaterial','Surface')}
        actual={(l.from_node.bl_idname,l.from_socket.identifier,l.to_node.bl_idname,l.to_socket.identifier) for l in nt.links}
        if actual!=expected_links:raise ValueError('Unsupported emission-wash wiring')
        return ramp
    if kind=='constant_principled_wash':
        if types!=sorted(['ShaderNodeBsdfPrincipled','ShaderNodeOutputMaterial']):raise ValueError('Unsupported constant-Principled graph')
        shader=next(n for n in nodes if n.bl_idname=='ShaderNodeBsdfPrincipled')
        actual={(l.from_node.bl_idname,l.from_socket.identifier,l.to_node.bl_idname,l.to_socket.identifier) for l in nt.links}
        if actual!={('ShaderNodeBsdfPrincipled','BSDF','ShaderNodeOutputMaterial','Surface')}:raise ValueError('Unsupported constant-Principled wiring')
        return shader
    raise ValueError('Unsupported shader kind')


def validate(receivers,palette,ramp_factors=(.94,1.06)):
    if not receivers:raise ValueError('Explicit nonempty receiver list required')
    if len(ramp_factors)!=2 or not all(isinstance(f,(int,float)) and math.isfinite(f) and f>=0 for f in ramp_factors):raise ValueError('Two finite positive ramp factors required')
    checked=[];seen=set();source_routes={}
    for r in receivers:
        if r.obj is None or r.obj.type!='MESH' or r.obj.data.users!=1:raise ValueError('Single-user mesh receivers required')
        if not isinstance(r.slot,int) or r.slot<0 or r.slot>=len(r.obj.material_slots):raise ValueError('Invalid receiver slot')
        key=(r.obj.as_pointer(),r.slot)
        if key in seen:raise ValueError('Duplicate receiver slot')
        seen.add(key)
        col=palette.get(r.layer)
        if col is None or len(col)!=3 or not all(isinstance(v,(int,float)) and math.isfinite(v) and 0<=v<=1 for v in col):raise ValueError('Every layer needs a finite RGB color in [0,1]')
        if any(v*f>1 for v in col for f in ramp_factors):raise ValueError('Ramp color exceeds supported [0,1] range')
        m=r.obj.material_slots[r.slot].material;_graph(m,r.kind)
        # One original material may feed different layer clones, but each receiver is explicit.
        checked.append((r,m,tuple(float(x) for x in col)))
    return checked


def apply(receivers,palette,ramp_factors=(.94,1.06),label='Background palette'):
    checked=validate(receivers,palette,ramp_factors)  # All-or-nothing preflight before mutation.
    clones={};bindings=[];source_flags={m.name:m.use_fake_user for _,m,_ in checked}
    try:
        for r,source,col in checked:
            key=(source.as_pointer(),r.kind,r.layer,col)
            if key not in clones:
                source.use_fake_user=True
                m=source.copy();m.use_fake_user=False;m.name=label+' / '+source.name;clones[key]=m
                n=_graph(m,r.kind)
                if r.kind=='emission_two_stop_wash':
                    for e,f in zip(n.color_ramp.elements,ramp_factors):e.color=(*[v*f for v in col],1)
                else:
                    n.inputs['Base Color'].default_value=(*col,1)
                    n.inputs['Emission Color'].default_value=(*col,1)
            m=clones[key];bindings.append({'object':r.obj.name,'slot':r.slot,'source':source.name,'private':m.name,'link':r.obj.material_slots[r.slot].link})
            r.obj.material_slots[r.slot].material=m
    except Exception:
        for b in reversed(bindings):bpy.data.objects[b['object']].material_slots[b['slot']].material=bpy.data.materials[b['source']]
        for m in clones.values():
            if m.users==0:bpy.data.materials.remove(m)
        for name,flag in source_flags.items():bpy.data.materials[name].use_fake_user=flag
        raise
    return {'version':'0.1.0','bindings':bindings,'private_materials':[m.name for m in clones.values()],'source_fake_users':source_flags}


def restore(handle):
    """Restore exact original binding pointers. Refuse if caller edited a bound slot meanwhile."""
    if handle.get('version')!='0.1.0':raise ValueError('Unsupported handle version')
    for b in handle['bindings']:
        o=bpy.data.objects.get(b['object']);source=bpy.data.materials.get(b['source']);private=bpy.data.materials.get(b['private'])
        if o is None or source is None or private is None or b['slot']>=len(o.material_slots):raise ValueError('Restore target missing')
        slot=o.material_slots[b['slot']]
        if slot.material!=private or slot.link!=b['link']:raise ValueError('Receiver changed since application; restore refused')
    for b in handle['bindings']:bpy.data.objects[b['object']].material_slots[b['slot']].material=bpy.data.materials[b['source']]
    for name in handle['private_materials']:
        m=bpy.data.materials.get(name)
        if m and m.users==0:bpy.data.materials.remove(m)

    for name,flag in handle['source_fake_users'].items():bpy.data.materials[name].use_fake_user=flag
