"""Explicit scene adapter. Portable scatter engine remains in installable plugin.
This scene's terrain has XY scale 1.4; records and source sizes are in world metres.
An identity-space live receiver proxy preserves that declared unit contract.
"""
import bpy, pathlib, json, hashlib, importlib.util, sys
from mathutils import Matrix
ROOT=pathlib.Path('/workspace/scratch/97c495355428/japanese_reconstruction')

def load_plugin():
    src=ROOT/'plugin_integration/src';name='astra_painted_workbench'
    if name not in sys.modules:
        spec=importlib.util.spec_from_file_location(name,str(src/'__init__.py'),submodule_search_locations=[str(src)])
        mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod)
    from astra_painted_workbench.runtime.native_scatter import create_native_scatter,audit
    return create_native_scatter,audit

def evaluated_world(obj):
    ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
    try:
        me.calc_loop_triangles()
        return [tuple(obj.matrix_world@v.co) for v in me.vertices],[tuple(p.vertices) for p in me.polygons],[tuple(p.vertices) for p in me.loop_triangles]
    finally:ev.to_mesh_clear()

def world_receiver(source,collection):
    me=bpy.data.meshes.new('Courtyard explicit world receiver mesh');host=bpy.data.objects.new('LIVED / World-space terrain receiving proxy',me);collection.objects.link(host)
    g=bpy.data.node_groups.new('LIVED / World-space receiver adapter','GeometryNodeTree');g.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry');out=g.nodes.new('NodeGroupOutput');info=g.nodes.new('GeometryNodeObjectInfo');info.transform_space='RELATIVE';info.inputs['Object'].default_value=source;info.inputs['As Instance'].default_value=False;g.links.new(info.outputs['Geometry'],out.inputs['Geometry']);mod=host.modifiers.new('Live original terrain in world-metre coordinates','NODES');mod.node_group=g
    host.hide_render=True;host.hide_set(True);host['astra_original_receiver']=source;host['adapter_space']='Identity host, live evaluated original geometry transformed into world-metre local coordinates.'
    bpy.context.view_layer.update();sv,sf,st=evaluated_world(source);hv,hf,ht=evaluated_world(host)
    assert len(sv)==len(hv) and sf==hf,'Proxy topology differs'
    assert st==ht,'Proxy tessellation differs from original rendered surface'
    error=max((sum((a-b)**2 for a,b in zip(x,y))**.5 for x,y in zip(sv,hv)),default=0)
    assert error<1e-6,('Proxy worldspace mismatch',error)
    proof={'source':source.name,'source_pointer_property':'astra_original_receiver','source_matrix':[list(r) for r in source.matrix_world],'proxy':host.name,'proxy_matrix':[list(r) for r in host.matrix_world],'vertices':len(hv),'polygons':len(hf),'max_world_coordinate_error_m':error,'same_evaluated_face_indices':True,'same_evaluated_loop_triangle_indices':True,'loop_triangles':len(ht)}
    host['astra_world_proxy_proof']=json.dumps(proof);return host,proof

def adopt(report):
    create,audit=load_plugin();collection=bpy.data.collections[report['new_collection']];source=bpy.data.objects['Continuous earth with sloped pond basin'];proxy,proof=world_receiver(source,collection);outputs=[]
    for kind,host_name,bank_name in [('pebble','Grouped shore and shoulder pebbles','Pebble source bank'),('moss','Connected low moss cushions','Moss cushion source bank'),('tuft','Sheltered low leafy accents','Low leafy tuft source bank')]:
        name='LIVED / '+host_name;prior=bpy.data.objects[name];prior.name=name+' / prior scene adapter';prior.hide_render=True;prior.hide_set(True)
        records=[dict(r,id=f'courtyard-{kind}-{i:05d}') for i,r in enumerate(report['scatter']['records'][kind])]
        host=create(name,records,bpy.data.collections['LIVED / '+bank_name],proxy,collection,kind,footprint_check=True)
        host['courtyard_prior_adapter']=prior;outputs.append({'host':host.name,'contract':json.loads(host['astra_native_contract']),'audit':audit(host)})
    plugin_file=ROOT/'plugin_integration/src/runtime/native_scatter.py'
    return {'implementation':'Actual installable plugin native_scatter.create_native_scatter', 'engine_sha256':hashlib.sha256(plugin_file.read_bytes()).hexdigest(),'world_receiver_proof':proof,'hosts':outputs,'scope':'Three ground scatter hosts use plugin. Terrain, dependent support, stone-skirt moss and cumulative bridge spacing remain explicit courtyard adapters with native GN.'}
