"""Portable selected-receiver adapters over frozen, previously tested recipes.
Persistent ID pointers own restore; historical name-based removal is never called.
"""
import json
import math
import uuid
from pathlib import Path
import bpy
from mathutils import Vector, Matrix
from . import spec
from .landscape import OWNER, mesh_digest
from .vendor import material_microdetail_v022 as md
from .vendor import foundry_overlay as textile
from .vendor.painted_fields import painted_fields as pf


def preflight(obj,slot=0):
    if obj is None or obj.type!='MESH' or obj.library or obj.override_library or obj.data.library or obj.data.override_library:
        raise ValueError('Choose a local editable mesh receiver')
    if obj.get('astra_surface_transaction'):
        raise ValueError('Receiver already has an active surface transaction; restore before another operation')
    if obj.modifiers or obj.data.shape_keys or obj.animation_data or obj.constraints or len(obj.users_scene)!=1:
        raise ValueError('Use a static mesh without modifiers, shape keys or constraints in one scene')
    if type(slot) is not int or not 0<=slot<len(obj.material_slots) or obj.material_slots[slot].material is None:
        raise ValueError('Choose an existing nonempty material slot')
    m=obj.material_slots[slot].material
    if m.library or not m.use_nodes:raise ValueError('Receiver needs a local node material')
    pf._shader_path(m)  # validates supported active shader route before ID changes
    return m


def _begin(obj,slot,kind):
    owner=str(uuid.uuid4());keeper=bpy.data.objects.new('Astra / '+kind+' restore handle',None)
    bpy.context.scene.collection.objects.link(keeper);keeper.hide_render=True;keeper.hide_set(True)
    keeper[OWNER]=owner;keeper['astra_kind']='surface';keeper['astra_target']=obj;keeper['astra_source_mesh']=obj.data
    keeper['astra_source_hash']=mesh_digest(obj.data);keeper['astra_slot']=slot
    keeper['source_data_slot_count']=len(obj.data.materials)
    for i,m in enumerate(obj.data.materials):
        if m:keeper['source_data_material_'+str(i)]=m
    keeper['astra_slots']=json.dumps([{'index':i,'link':s.link} for i,s in enumerate(obj.material_slots)])
    for i,s in enumerate(obj.material_slots):
        if s.material:
            keeper['source_material_'+str(i)]=s.material
            keeper['source_fake_user_'+str(i)]=bool(s.material.use_fake_user)
    keeper['astra_original_modifiers']=json.dumps([m.name for m in obj.modifiers])
    mesh=obj.data.copy();mesh[OWNER]=owner;obj.data=mesh;keeper['astra_private_mesh']=mesh
    obj['astra_surface_transaction']=keeper
    return keeper


def _finish(keeper,specification,created_before):
    obj=keeper['astra_target'];keeper['astra_spec']=json.dumps(specification,sort_keys=True)
    for o in bpy.data.objects:
        if o.as_pointer() not in created_before and o!=keeper:o[OWNER]=keeper[OWNER]
    # Persistent ID pointers already retain originals. Undo vendor fake-user side effects now,
    # so concurrent receivers never capture another transaction's temporary True flag.
    for row in json.loads(keeper['astra_slots']):
        original=keeper.get('source_material_'+str(row['index']))
        if original:original.use_fake_user=bool(keeper.get('source_fake_user_'+str(row['index']),False))
    keeper['astra_source_flags_untouched']=True
    keeper['astra_private_hash']=mesh_digest(obj.data)
    for i,s in enumerate(obj.material_slots):
        if s.material:keeper['private_material_'+str(i)]=s.material
        keeper['private_link_'+str(i)]=s.link
    keeper['astra_private_slot_count']=len(obj.material_slots);keeper['astra_active']=True
    return keeper


def _restore(keeper,check=True):
    if keeper is None or keeper.get('astra_kind')!='surface':raise ValueError('No surface restore handle')
    obj=keeper.get('astra_target');original=keeper.get('astra_source_mesh');private=keeper.get('astra_private_mesh')
    if not obj or not original:raise ValueError('Persistent original receiver is unavailable')
    if check:
        if not keeper.get('astra_active'):raise ValueError('Transaction is already restored')
        if obj.data!=private:raise ValueError('Receiver mesh replaced externally; refusing to overwrite it')
        if mesh_digest(original)!=keeper['astra_source_hash']:raise ValueError('Retained original mesh changed externally')
        if len(original.materials)!=keeper['source_data_slot_count'] or any(m!=keeper.get('source_data_material_'+str(i)) for i,m in enumerate(original.materials)):raise ValueError('Retained source DATA material bindings changed externally; refusing to overwrite shared data')
        if any(m.type!='BOOLEAN' or not m.object or m.object.get(OWNER)!=keeper[OWNER] for m in obj.modifiers):raise ValueError('Outside modifiers were added or replaced; refusing to overwrite their receiver')
        if keeper.get('astra_source_flags_untouched'):
            for row in json.loads(keeper['astra_slots']):
                original_material=keeper.get('source_material_'+str(row['index']))
                if original_material and original_material.use_fake_user!=bool(keeper.get('source_fake_user_'+str(row['index']),False)):raise ValueError('Source material retention flag changed externally')
        if mesh_digest(private)!=keeper['astra_private_hash']:raise ValueError('Private mesh edited outside the transaction; keep or inspect edits before restoring')
        if len(obj.material_slots)!=keeper['astra_private_slot_count']:raise ValueError('Material slots changed externally')
        for i,s in enumerate(obj.material_slots):
            if s.material!=keeper.get('private_material_'+str(i)) or s.link!=keeper.get('private_link_'+str(i)):raise ValueError('Material binding or link mode changed externally')
    for mod in list(obj.modifiers):
        if mod.type=='BOOLEAN' and mod.object and mod.object.get(OWNER)==keeper[OWNER]:obj.modifiers.remove(mod)
    obj.data=original
    for row in json.loads(keeper['astra_slots']):
        slot=obj.material_slots[row['index']];slot.link=row['link'];slot.material=keeper.get('source_material_'+str(row['index']))
        if slot.material:slot.material.use_fake_user=bool(keeper.get('source_fake_user_'+str(row['index']),False))
    # Cutters remain retained and hidden, but their Boolean modifiers are removed.
    for o in bpy.data.objects:
        if o.get(OWNER)==keeper[OWNER]:o.hide_render=True;o.hide_set(True)
    if obj.get('astra_surface_transaction')==keeper:del obj['astra_surface_transaction']
    keeper['astra_active']=False
    return {'restored':True,'source_mesh':original.name,'identity':'Persistent ID references; names may change'}


def restore(obj):
    keeper=obj if obj and obj.get('astra_kind')=='surface' else (obj.get('astra_surface_transaction') if obj else None)
    return _restore(keeper)


def apply_pigment(obj,slot=0,kind='timber',grain_axis='X',seed=41,strength=.75,longitudinal_span=2.2,transverse_span=.65,palette_mean=(.10,.06,.03)):
    field=pf.FieldSpec(kind=kind,grain_axis=grain_axis,seed=seed,strength=strength,longitudinal_span=longitudinal_span,transverse_span=transverse_span,palette_mean=tuple(palette_mean))
    pf.validate(field);original=preflight(obj,slot)
    if original.get('painted_fields_version'):raise ValueError('Receiver already has Painted Fields; restore the earlier field first')
    path=Path(__file__).parent/'vendor'/'assets'/'generated_pigment_atlas_v01.png'
    import hashlib
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=pf.ATLAS_SHA256:raise ValueError('Bundled pigment atlas is missing or modified')
    before={o.as_pointer() for o in bpy.data.objects};keeper=_begin(obj,slot,'pigment')
    try:
        report=pf.apply_to_receiver(obj,slot,field,path,private_image=True);return _finish(keeper,{'kind':'pigment','report':report},before)
    except Exception:_restore(keeper,False);raise


def apply_textile(obj,slot=0,strength=0.):
    preflight(obj,slot);textile.validate_receiver(obj,slot,strength)
    before={o.as_pointer() for o in bpy.data.objects};keeper=_begin(obj,slot,'textile overlay')
    try:
        report=textile.apply_overlay_strength(obj,slot,strength);return _finish(keeper,{'kind':'textile','report':report},before)
    except Exception:_restore(keeper,False);raise


def _wood_check(obj,seed):
    # Local grain, independent of the object's pose/name. Source and cutter move together.
    rng=spec.stable_rng(seed,'timber-check');lo,hi=md.local_bounds(obj);dims=[b-a for a,b in zip(lo,hi)]
    axis=max(range(3),key=lambda k:dims[k]);normal_axis=2 if axis!=2 else 1
    across=next(k for k in range(3) if k not in (axis,normal_axis))
    length=min(dims[axis]*.52,.78);start=lo[axis]+dims[axis]*rng.uniform(.15,.28)
    transverse=(lo[across]+hi[across])*.5+dims[across]*rng.uniform(-.15,.15)
    pts=[]
    for j in range(7):
        t=j/6;p=Vector((0,0,0));p[axis]=start+length*t;p[across]=transverse+math.sin(t*5+rng.random())*.002;p[normal_axis]=hi[normal_axis];pts.append(p)
    sections=[]
    for j,p in enumerate(pts):
        taper=math.sin(math.pi*j/6)**.7;normal=Vector(tuple(1 if k==normal_axis else 0 for k in range(3)))
        sections.append((p,pts[min(j+1,6)]-pts[max(0,j-1)],normal,.0038*taper+.0002,.006*taper+.0002))
    return md.make_cutter(obj,'Astra / retained grain-aligned check',sections,.66)


def _ceramic_notch(obj,seed):
    # Small angular edge loss, not a timber check or all-over isotropic noise.
    r=spec.stable_rng(seed,'ceramic-edge');lo,hi=md.local_bounds(obj);dims=[b-a for a,b in zip(lo,hi)]
    axis=0 if dims[0]>=dims[1] else 1;cross=1-axis;end=hi[axis];center=(lo[cross]+hi[cross])*.5
    depth=min(.009,dims[2]*.30);w=min(.022,dims[cross]*.1);length=min(.035,dims[axis]*.1)
    pts=[]
    for j,t in enumerate([0,.25,.68,1]):
        p=Vector((0,0,0));p[axis]=end-length+length*t*1.3;p[cross]=center+r.uniform(-.1,.1)*w;p.z=hi[2]
        pts.append(p)
    sections=[]
    for j,p in enumerate(pts):
        tangent=pts[min(j+1,3)]-pts[max(0,j-1)]
        sections.append((p,tangent,Vector((0,0,1)),w*[.03,.65,1,1.05][j],depth*[.1,.65,1,1.1][j]))
    return md.make_cutter(obj,'Astra / retained ceramic edge notch',sections,.86)


def apply_detail(obj,family='timber',seed=137,depth=.004,strength=.45,stain=.24):
    if family not in ('timber','stone','ceramic'):raise ValueError('Choose timber, stone or ceramic explicitly')
    spec.integer(seed,'seed');md.validate_controls(depth,strength,stain);original=preflight(obj,0)
    if original.get('md_material_uid'):raise ValueError('Receiver already has microdetail; restore the earlier detail first')
    lo,hi=md.local_bounds(obj);dims=[b-a for a,b in zip(lo,hi)]
    if min(dims)<.05 or max(dims)<.4:raise ValueError('Detail requires extents >=0.05 and one length >=0.4 local units')
    before={o.as_pointer() for o in bpy.data.objects};keeper=_begin(obj,0,family+' detail')
    try:
        report={'family':family,'seed':seed,'geometry':[]}
        if family=='timber':
            report['shading']=md.add_shading(obj,False,depth,strength,stain,private_group=True)
            # Replace object-name-sensitive Random with the explicit seed in copied graphs.
            seen=set()
            def stable(tree):
                if tree.as_pointer() in seen:return
                seen.add(tree.as_pointer())
                for n in list(tree.nodes):
                    if n.type=='GROUP' and n.node_tree:stable(n.node_tree)
                    if n.type=='OBJECT_INFO' and n.name.startswith('Microdetail / deterministic'):
                        value=tree.nodes.new('ShaderNodeValue');value.name='Astra / explicit stable seed';value.outputs[0].default_value=spec.stable_rng(seed,'grain').random()
                        for link in list(n.outputs['Random'].links):tree.links.new(value.outputs[0],link.to_socket)
            stable(obj.material_slots[0].material.node_tree)
            report['geometry'].append(_wood_check(obj,seed))
        elif family=='stone':report['geometry'].append(md.stone_cut(obj,seed))
        else:report['geometry'].append(_ceramic_notch(obj,seed))
        for o in bpy.data.objects:
            if o.as_pointer() not in before and o!=keeper:
                o[OWNER]=keeper[OWNER]
                if o.parent==obj:
                    o['astra_anchor_target']=obj;o['astra_anchor_basis']=json.dumps([list(row) for row in o.matrix_basis])
        return _finish(keeper,{'kind':'microdetail','report':report},before)
    except Exception:
        for o in bpy.data.objects:
            if o.as_pointer() not in before and o!=keeper:o[OWNER]=keeper[OWNER]
        _restore(keeper,False);raise


def audit(obj):
    k=obj if obj and obj.get('astra_kind')=='surface' else (obj.get('astra_surface_transaction') if obj else None)
    if not k:raise ValueError('Select a receiver with an active surface transaction')
    target=k.get('astra_target');source=k.get('astra_source_mesh')
    checks={'source_retained':source is not None,'source_mesh_unchanged':source is not None and mesh_digest(source)==k['astra_source_hash'],
            'source_bindings_unchanged':source is not None and len(source.materials)==k['source_data_slot_count'] and all(m==k.get('source_data_material_'+str(i)) for i,m in enumerate(source.materials))}
    cutters=[o for o in bpy.data.objects if o.get(OWNER)==k[OWNER] and o!=k]
    checks['cutter_anchors']=all(o.parent==target and o.get('astra_anchor_target')==target and all(abs(o.matrix_basis[i][j]-(1 if i==j else 0))<1e-7 for i in range(4) for j in range(4)) for o in cutters)
    return {'checks':checks,'cutters':len(cutters),'art_acceptance':'not_determined','limits':['Static selected receivers only','Shader depth controls normal detail; real cuts use bounded material-specific dimensions','Actual Boolean intersections must be inspected in rendered and evaluated geometry']}
