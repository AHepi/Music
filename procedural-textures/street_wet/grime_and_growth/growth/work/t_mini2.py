import sys, time, bpy
import numpy as np
KIT='proc-work/kits/weathering'
sys.path.insert(0,KIT); sys.dont_write_bytecode=True
from apply import kit as kit_module
from masks import bus as bus_module
from growth.scatter import GNet, S, O
from growth import pieces
k=kit_module.Kit.load('pit_village_street', scene_id='street', strict=False)
bus_module.attach(k)
pack=k.mask_pack
ent=pack.entry('GP','weed_site'); img=pack.image(ent['picture']); print('img', img.name, img.size, img.colorspace_settings.name, img.alpha_mode, ent['channel'])
def run(variant):
    tree=bpy.data.node_groups.new('mini'+variant,'GeometryNodeTree')
    tree.interface.new_socket('Geometry',in_out='INPUT',socket_type='NodeSocketGeometry')
    tree.interface.new_socket('Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
    n=GNet(tree); out=tree.nodes.new('NodeGroupOutput')
    join=n.gnode('GeometryNodeJoinGeometry')
    for name in ('street_setts','street_pavements'):
        info=n.gnode('GeometryNodeObjectInfo', transform_space='RELATIVE'); S(info,'Object').default_value=bpy.data.objects[name]; S(info,'As Instance').default_value=False
        n.link(O(info,'Geometry'), join.inputs[0])
    geo=O(join,'Geometry')
    d=n.gnode('GeometryNodeDistributePointsOnFaces', distribute_method='POISSON'); n.link(geo,S(d,'Mesh'))
    S(d,'Distance Min').default_value=0.15; S(d,'Density Max').default_value=8.0
    pts=O(d,'Points')
    px,py,pz=n.separate(n.position())
    if variant=='rand':
        rand=n.random_float(0.0,1.0,0,ident=n.index())
        drop=n.compare(rand,'GREATER_EQUAL',0.5)
    elif variant=='pos':
        drop=n.compare(py,'GREATER_EQUAL',20.0)
    elif variant=='img':
        uv=n.combine(n.math('DIVIDE', n.math('SUBTRACT', px, -4.5), 9.0), n.math('DIVIDE', n.math('SUBTRACT', py, -12.0), 84.0), 0.0)
        node=n.gnode('GeometryNodeImageTexture', interpolation='Closest', extension='CLIP')
        S(node,'Image').default_value=img
        n.link(uv,S(node,'Vector'))
        sep=n.gnode('FunctionNodeSeparateColor'); n.link(O(node,'Color'), sep.inputs[0])
        w=O(sep,'Green')
        drop=n.compare(w,'LESS_THAN',0.01)
    de=n.gnode('GeometryNodeDeleteGeometry', domain='POINT'); n.link(pts,S(de,'Geometry')); n.link(drop,S(de,'Selection'))
    n.link(O(de,'Geometry'), out.inputs[0])
    host=bpy.data.objects.new('h'+variant, bpy.data.meshes.new('hm'+variant)); bpy.context.scene.collection.objects.link(host)
    md=host.modifiers.new('g','NODES'); md.node_group=tree
    dg=bpy.context.evaluated_depsgraph_get(); dg.update()
    ev=host.evaluated_get(dg); gs=ev.evaluated_geometry()
    pc=gs.pointcloud
    print(variant, 'points', None if pc is None else len(pc.points))
for v in ('rand','pos','img'): run(v)
