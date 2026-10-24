"""Portable native-GN scatter extracted from the courtyard's tested mechanism.
Creation validates explicit record data and finite footprint samples. Native controls
continue evaluating after save/reopen. This is not an ecology/erosion simulation.
"""
import hashlib,json,math,uuid
import bpy
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
from . import spec
from .landscape import OWNER, mesh_digest

CONTROLS={'Density':('NodeSocketFloat',1.,0.,2.),'Traffic Width':('NodeSocketFloat',1.03,0.,20.),
          'Waterline':('NodeSocketFloat',0.,-10000.,10000.),'Damp Reach':('NodeSocketFloat',.95,.01,100.),
          'Contact Influence':('NodeSocketFloat',.6,0.,1.),'Seed':('NodeSocketInt',521,0,1048576)}


def _validate(records,bank,receiver,kind,controls):
    if kind not in ('pebble','moss','tuft'):raise ValueError('Native scatter kind must be pebble, moss or tuft')
    if receiver is None or receiver.type!='MESH' or receiver.library:raise ValueError('Choose a local explicit mesh receiver')
    if bank is None or bank.library or not 1<=len(bank.objects)<=128 or any(o.type!='MESH' for o in bank.objects):raise ValueError('Source bank requires 1..128 local mesh objects')
    if any(o.parent or any(abs(o.matrix_basis[i][j]-(1 if i==j else 0))>1e-6 for i in range(4) for j in range(4)) for o in bank.objects):raise ValueError('Bank source meshes need identity transforms and no parents; encode dimensions in their geometry')
    if type(records) is not list or len(records)>20000:raise ValueError('records must be a list with at most 20000 candidates')
    for i,r in enumerate(records):
        spec.fields(r,['x','y','scale','rot','traffic','habitat','contact'],['z','id'],label='scatter record')
        for key in ['x','y']:spec.number(r[key],key,-10000,10000)
        spec.vec(r['scale'],3,'scale',.00001,10);spec.vec(r['rot'],3,'rotation',-10000,10000)
        spec.number(r['traffic'],'traffic',0,10000);spec.number(r['habitat'],'habitat',0,1);spec.number(r['contact'],'contact',0,1)
        if 'z' in r:spec.number(r['z'],'z',-10000,10000)
        if 'id' in r and (type(r['id']) is not str or not r['id']):raise ValueError('Record id must be a nonempty string')
    ids=[r.get('id',str(i)) for i,r in enumerate(records)]
    if len(set(ids))!=len(ids):raise ValueError('Record IDs must be unique')
    if set(controls)-set(CONTROLS):raise ValueError('Unknown native scatter controls: '+str(set(controls)-set(CONTROLS)))
    for key,value in controls.items():
        typ,default,lo,hi=CONTROLS[key]
        (spec.integer if typ=='NodeSocketInt' else spec.number)(value,key,lo,hi)
    return ids


def _collection(collection):
    if collection is None:return bpy.context.scene.collection
    if not isinstance(collection,bpy.types.Collection) or collection.library or collection.override_library:
        raise ValueError('Output collection must be a local editable collection in this scene')
    reachable=set();pending=[bpy.context.scene.collection]
    while pending:
        c=pending.pop()
        if c.as_pointer() in reachable:continue
        reachable.add(c.as_pointer());pending.extend(c.children)
    if collection.as_pointer() not in reachable:raise ValueError('Output collection is not linked to the current scene')
    return collection


def _bank_geometry(bank):
    bounds=[0.,0.,0.];rows=[];dg=bpy.context.evaluated_depsgraph_get()
    for original in bank.objects:
        ev=original.evaluated_get(dg);mesh=ev.to_mesh()
        try:
            if not mesh.vertices or not mesh.polygons:raise ValueError('Every source must evaluate to a nonempty mesh')
            if any(not all(math.isfinite(v) for v in p.co) for p in mesh.vertices):raise ValueError('Non-finite source geometry')
            low=min(v.co.z for v in mesh.vertices);high=max(v.co.z for v in mesh.vertices);height=high-low
            if height<1e-6 or low>height*.02+.0001 or low<-.15*height-.0001:
                raise ValueError('Source support origin must be near its bottom: min Z in [-15%, +2%] of height; normalize source geometry first')
            for axis in range(3):bounds[axis]=max(bounds[axis],max(abs(v.co[axis]) for v in mesh.vertices))
            upper=[p for p in mesh.polygons if p.center.z>low+height*.35]
            downward=[p for p in upper if p.normal.z<-.05]
            rows.append({'source':original,'evaluated_hash':mesh_digest(mesh),'upper_downward_faces':len(downward),'upper_faces':len(upper),'bottom_z':low,'height':height})
        finally:ev.to_mesh_clear()
    return bounds,rows


def _attr(mesh,name,values,typ='FLOAT'):
    a=mesh.attributes.new(name=name,type=typ,domain='POINT')
    for item,value in zip(a.data,values):
        if typ=='FLOAT_VECTOR':item.vector=value
        else:item.value=value


def _named(g,name,typ='FLOAT'):
    n=g.nodes.new('GeometryNodeInputNamedAttribute');n.data_type=typ;n.inputs['Name'].default_value=name;return n.outputs['Attribute']


def _math(g,op,a,b=None):
    n=g.nodes.new('ShaderNodeMath');n.operation=op
    for i,v in enumerate([a,b]):
        if v is None:continue
        if hasattr(v,'is_output'):g.links.new(v,n.inputs[i])
        else:n.inputs[i].default_value=v
    return n.outputs[0]


def _create_native_scatter(name,records,bank,receiver,collection,kind,*,controls=None,footprint_check=True):
    controls={} if controls is None else dict(controls)
    if 'Seed' not in controls:controls['Seed']=307 if kind=='pebble' else 521
    identities=_validate(records,bank,receiver,kind,controls)
    collection=_collection(collection);source_bounds,source_rows=_bank_geometry(bank)
    if type(footprint_check) is not bool:raise ValueError('footprint_check must be a boolean')
    dg=bpy.context.evaluated_depsgraph_get();ev=receiver.evaluated_get(dg);me=ev.to_mesh()
    try:
        if not me.vertices or not me.polygons:raise ValueError('Receiver evaluates to no surface')
        receiver_hash=mesh_digest(me);me.calc_loop_triangles();vertices=[v.co.copy() for v in me.vertices];faces=[tuple(p.vertices) for p in me.loop_triangles]
        top=max(v.z for v in vertices)+2;bottom=min(v.z for v in vertices)-2
        bvh=BVHTree.FromPolygons(vertices,faces,all_triangles=True)
    finally:ev.to_mesh_clear()
    tested=[];rejected=0;support_radii=[]
    # Finite support checks occur in receiver local space. They don't certify future modifier edits.
    for i,r in enumerate(records):
        accepted=True
        radius=math.sqrt(sum((source_bounds[k]*r['scale'][k])**2 for k in range(3)))
        if footprint_check:
            center,normal,_,_=bvh.ray_cast(Vector((r['x'],r['y'],top)),Vector((0,0,-1)),top-bottom)
            if center is None or normal.z<.50:accepted=False
            else:
                zs=[center.z];embed=.012 if kind=='pebble' else .018;tolerance=.035 if kind=='pebble' else .020
                for j in range(8):
                    a=j*math.tau/8;dx=radius*math.cos(a);dy=radius*math.sin(a)
                    p,n,_,_=bvh.ray_cast(Vector((r['x']+dx,r['y']+dy,top)),Vector((0,0,-1)),top-bottom)
                    if p is None or n.z<.50:accepted=False;break
                    plane=center.z-(normal.x*dx+normal.y*dy)/normal.z-embed
                    # A global Z spread confounds gentle slope with unsupported bank creases.
                    if plane-p.z>tolerance:accepted=False;break
                    zs.append(p.z)
                if max(zs)-min(zs)>max(radius*.9,r['scale'][2]*2.5):accepted=False
        if accepted:tested.append((r,identities[i]));support_radii.append(radius)
        else:rejected+=1
    owner=str(uuid.uuid4());mesh=bpy.data.meshes.new('Astra / '+name+' candidates')
    mesh.from_pydata([(r['x'],r['y'],top) for r,uid in tested],[],[]);mesh.update();mesh[OWNER]=owner
    host=bpy.data.objects.new(name,mesh);(collection or bpy.context.scene.collection).objects.link(host);host[OWNER]=owner
    host.parent=receiver;host.matrix_parent_inverse=Matrix.Identity(4);host.matrix_basis=Matrix.Identity(4);host['astra_kind']='native_scatter';host['astra_receiver']=receiver;host['astra_bank']=bank
    host['astra_receiver_eval_hash']=receiver_hash
    host['astra_records']=json.dumps([dict(r,id=uid) for r,uid in tested],sort_keys=True)
    host['astra_native_contract']=json.dumps({'version':spec.VERSION,'space':'receiver-local','kind':kind,'candidate_count':len(records),'retained_candidates':len(tested),'footprint_rejections':rejected,'footprint_check':footprint_check,'source_absolute_bounds':source_bounds,'footprint_policy':'Eight perimeter samples plus center; conservative evaluated source sphere bound; center tangent-plane positive support residual <= 0.035 pebble / 0.020 moss or tuft local units after embed; explicit evaluated loop triangles','source_orientation':[dict(source=r['source'].name,upper_downward_faces=r['upper_downward_faces'],upper_faces=r['upper_faces']) for r in source_rows],'limits':['Finite initial footprint samples; edited support topology needs regeneration/recheck','Native UI can bypass API bounds; audit visibly reports limits','Source bank IDs retained; do not replace bank membership without regeneration','Centre grounding follows current receiver; footprint changes are not continuously certified']},sort_keys=True)
    for nm,key,typ in [('lived_scale','scale','FLOAT_VECTOR'),('lived_rotation','rot','FLOAT_VECTOR'),('lived_traffic_distance','traffic','FLOAT'),('lived_habitat','habitat','FLOAT'),('lived_contact','contact','FLOAT')]:_attr(mesh,nm,[r[key] for r,uid in tested],typ)
    _attr(mesh,'astra_footprint_radius',support_radii)
    _attr(mesh,'astra_candidate_id',[int.from_bytes(hashlib.sha256(uid.encode()).digest()[:4],'big')%2147483647 for r,uid in tested],'INT')
    g=bpy.data.node_groups.new('Astra / '+name+' semantic scatter','GeometryNodeTree');g[OWNER]=owner
    for direction in ['INPUT','OUTPUT']:g.interface.new_socket(name='Geometry',in_out=direction,socket_type='NodeSocketGeometry')
    for label,(typ,default,lo,hi) in CONTROLS.items():
        socket=g.interface.new_socket(name=label,in_out='INPUT',socket_type=typ);socket.default_value=controls.get(label,default);socket.min_value=lo;socket.max_value=hi
    inp=g.nodes.new('NodeGroupInput');out=g.nodes.new('NodeGroupOutput');L=g.links.new
    # Attribute ray origins are invariant under downstream Set Position field evaluation.
    pos=g.nodes.new('GeometryNodeInputPosition');sep=g.nodes.new('ShaderNodeSeparateXYZ');origin=g.nodes.new('ShaderNodeCombineXYZ');L(pos.outputs[0],sep.inputs[0]);L(sep.outputs['X'],origin.inputs['X']);L(sep.outputs['Y'],origin.inputs['Y']);origin.inputs['Z'].default_value=top
    obj=g.nodes.new('GeometryNodeObjectInfo');obj.inputs['Object'].default_value=receiver;obj.transform_space='RELATIVE'
    ray=g.nodes.new('GeometryNodeRaycast');ray.data_type='FLOAT';ray.inputs['Ray Direction'].default_value=(0,0,-1);ray.inputs['Ray Length'].default_value=top-bottom;L(obj.outputs['Geometry'],ray.inputs['Target Geometry']);L(origin.outputs[0],ray.inputs['Source Position'])
    setp=g.nodes.new('GeometryNodeSetPosition');L(inp.outputs['Geometry'],setp.inputs['Geometry']);L(ray.outputs['Hit Position'],setp.inputs['Position']);setp.inputs['Offset'].default_value=(0,0,-.012 if kind=='pebble' else -.018)
    traffic=_math(g,'GREATER_THAN',_math(g,'SUBTRACT',_named(g,'lived_traffic_distance'),_named(g,'astra_footprint_radius')),inp.outputs['Traffic Width'])
    habitat=_named(g,'lived_habitat');contact=_math(g,'MULTIPLY',_named(g,'lived_contact'),inp.outputs['Contact Influence'])
    chance=_math(g,'MINIMUM',_math(g,'ADD',habitat,contact),1);chance=_math(g,'MULTIPLY',chance,inp.outputs['Density'])
    hitz=g.nodes.new('ShaderNodeSeparateXYZ');L(ray.outputs['Hit Position'],hitz.inputs[0]);dz=_math(g,'SUBTRACT',hitz.outputs['Z'],inp.outputs['Waterline']);dry=_math(g,'GREATER_THAN',dz,-.015)
    if kind!='pebble':dry=_math(g,'MULTIPLY',dry,_math(g,'LESS_THAN',dz,inp.outputs['Damp Reach']))
    ran=g.nodes.new('FunctionNodeRandomValue');ran.data_type='FLOAT';L(inp.outputs['Seed'],ran.inputs['Seed']);L(_named(g,'astra_candidate_id','INT'),ran.inputs['ID'])
    keep=_math(g,'LESS_THAN',ran.outputs['Value'],chance)
    for test in [traffic,dry,ray.outputs['Is Hit']]:keep=_math(g,'MULTIPLY',keep,test)
    source=g.nodes.new('GeometryNodeGeometryToInstance')
    # Fixed explicit object pointers keep source ordering stable across bank/object renames.
    for original in bank.objects:
        item=g.nodes.new('GeometryNodeObjectInfo');item.transform_space='ORIGINAL';item.inputs['Object'].default_value=original;item.inputs['As Instance'].default_value=False
        L(item.outputs['Geometry'],source.inputs['Geometry'])
    inst=g.nodes.new('GeometryNodeInstanceOnPoints');inst.inputs['Pick Instance'].default_value=True;L(setp.outputs[0],inst.inputs['Points']);L(keep,inst.inputs['Selection']);L(source.outputs['Instances'],inst.inputs['Instance']);L(_named(g,'lived_scale','FLOAT_VECTOR'),inst.inputs['Scale'])
    align=g.nodes.new('FunctionNodeAlignEulerToVector');align.axis='Z';L(ray.outputs['Hit Normal'],align.inputs['Vector']);L(_named(g,'lived_rotation','FLOAT_VECTOR'),align.inputs['Rotation']);L(align.outputs['Rotation'],inst.inputs['Rotation'])
    index=g.nodes.new('FunctionNodeRandomValue');index.data_type='INT';index.inputs['Min'].default_value=0;index.inputs['Max'].default_value=len(bank.objects)-1;L(inp.outputs['Seed'],index.inputs['Seed']);L(_named(g,'astra_candidate_id','INT'),index.inputs['ID']);L(index.outputs['Value'],inst.inputs['Instance Index']);L(inst.outputs[0],out.inputs[0])
    for i,n in enumerate(g.nodes):n.location=((i%6)*230,-(i//6)*190)
    mod=host.modifiers.new('Astra / Live grounded semantic scatter','NODES');mod.node_group=g
    for socket in g.interface.items_tree:
        if socket.item_type=='SOCKET' and socket.in_out=='INPUT' and socket.name in CONTROLS:mod[socket.identifier]=controls.get(socket.name,CONTROLS[socket.name][1])
    host['astra_modifier']=mod.name;host['astra_group']=g;host['astra_source_count']=len(bank.objects)
    for i,row in enumerate(source_rows):
        o=row['source'];host['astra_source_'+str(i)]=o;host['astra_source_hash_'+str(i)]=mesh_digest(o.data);host['astra_source_eval_hash_'+str(i)]=row['evaluated_hash']
    host['astra_active']=True
    return host



def create_native_scatter(name,records,bank,receiver,collection,kind,*,controls=None,footprint_check=True):
    collection=_collection(collection)
    before={family:{item.as_pointer() for item in getattr(bpy.data,family)} for family in ['objects','meshes','node_groups']}
    try:return _create_native_scatter(name,records,bank,receiver,collection,kind,controls=controls,footprint_check=footprint_check)
    except Exception:
        for family in ['objects','node_groups','meshes']:
            data=getattr(bpy.data,family)
            for item in list(data):
                if item.as_pointer() not in before[family] and item.get(OWNER):
                    if family=='objects':data.remove(item,do_unlink=True)
                    elif item.users==0:data.remove(item)
        raise


def set_controls(host,**values):
    if host is None or host.get('astra_kind')!='native_scatter':raise ValueError('Choose an Astra native scatter')
    _validate([],host.get('astra_bank'),host.get('astra_receiver'),json.loads(host['astra_native_contract'])['kind'],values)
    mod=host.modifiers.get(host['astra_modifier'])
    if mod is None or mod.type!='NODES' or mod.node_group!=host.get('astra_group'):raise ValueError('Native scatter modifier/group identity changed')
    sockets={q.name:q for q in mod.node_group.interface.items_tree if q.item_type=='SOCKET' and q.in_out=='INPUT'}
    if not set(CONTROLS)<=set(sockets):raise ValueError('Native control schema was modified; no values were changed')
    for name,value in values.items():mod[sockets[name].identifier]=value
    host.update_tag();bpy.context.view_layer.update();return audit(host)


def audit(host):
    if host is None or host.get('astra_kind')!='native_scatter':raise ValueError('Choose an Astra native scatter')
    contract=json.loads(host['astra_native_contract']);bank=host.get('astra_bank');receiver=host.get('astra_receiver');mod=host.modifiers.get(host['astra_modifier'])
    checks={'receiver_retained':receiver is not None,'source_bank_retained':bank is not None,
            'source_members_retained':bank is not None and len(bank.objects)==host['astra_source_count'] and all(host.get('astra_source_'+str(i)) in bank.objects.values() for i in range(host['astra_source_count'])),
            'native_modifier_retained':mod is not None and mod.type=='NODES' and mod.node_group==host.get('astra_group'),
            'receiver_anchor':host.parent==receiver and all(abs(host.matrix_basis[i][j]-(1 if i==j else 0))<1e-6 for i in range(4) for j in range(4)),
            'source_meshes_unchanged':all(host.get('astra_source_'+str(i)) and mesh_digest(host['astra_source_'+str(i)].data)==host['astra_source_hash_'+str(i)] for i in range(host['astra_source_count']))}
    warnings=[];values={}
    checks['initial_footprint_checked']=bool(contract['footprint_check'])
    if not contract['footprint_check']:warnings.append('Footprint checks were explicitly disabled; initial support was not tested')
    if receiver:
        ev=receiver.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
        try:checks['support_surface_matches_initial_check']=mesh_digest(mesh)==host.get('astra_receiver_eval_hash')
        finally:ev.to_mesh_clear()
        if not checks['support_surface_matches_initial_check']:warnings.append('Receiver surface changed since initial footprint checks; center grounding remains live but regenerate before claiming perimeter support')
    try:
        _,current=_bank_geometry(bank)
        current_by_id={r['source'].as_pointer():r for r in current}
        checks['source_evaluation_unchanged']=all(current_by_id.get(host['astra_source_'+str(i)].as_pointer(),{}).get('evaluated_hash')==host['astra_source_eval_hash_'+str(i)] for i in range(host['astra_source_count']))
        checks['source_transforms_identity']=all(not o.parent and all(abs(o.matrix_basis[i][j]-(1 if i==j else 0))<1e-6 for i in range(4) for j in range(4)) for o in bank.objects)
        if contract['kind']=='moss' and any(r['upper_downward_faces'] for r in current):warnings.append('Moss source has downward-facing elevated surfaces; inspect ring winding before treating dark motifs as pigment')
    except (ValueError,AttributeError,KeyError) as exc:
        checks['source_evaluation_unchanged']=False;warnings.append(str(exc))
    if checks['native_modifier_retained']:
        sockets={q.name:q for q in mod.node_group.interface.items_tree if q.item_type=='SOCKET' and q.in_out=='INPUT' and q.name in CONTROLS}
        values={name:mod.get(q.identifier,q.default_value) for name,q in sockets.items()}
        checks['complete_control_schema']=set(CONTROLS)<=set(sockets)
        try:_validate([],bank,receiver,contract['kind'],values);checks['control_ranges']=True
        except ValueError as exc:checks['control_ranges']=False;warnings.append(str(exc))
    warnings.extend(contract['limits']);warnings.append('Hero readability and current per-instance footprint support require evaluated/render inspection')
    return {'contract':contract,'checks':checks,'controls':values,'warnings':warnings,'art_acceptance':'not_determined'}
