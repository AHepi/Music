import sys, time, bpy
import numpy as np
KIT='/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/kits/weathering'
sys.path.insert(0,KIT); sys.dont_write_bytecode=True
from growth.scatter import GNet, S, O
from growth import pieces
lib=pieces.Library(); lib.build(['grass'])
col=lib.kinds['grass']['collection']
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
    if variant=='real':
        r=n.gnode('GeometryNodeRealizeInstances'); n.link(geo,S(r,'Geometry')); geo=O(r,'Geometry')
    d=n.gnode('GeometryNodeDistributePointsOnFaces', distribute_method='POISSON'); n.link(geo,S(d,'Mesh'))
    S(d,'Distance Min').default_value=0.15; S(d,'Density Max').default_value=8.0
    inst=n.gnode('GeometryNodeInstanceOnPoints'); n.link(O(d,'Points'),S(inst,'Points'))
    info=n.gnode('GeometryNodeCollectionInfo'); S(info,'Collection').default_value=col; S(info,'Separate Children').default_value=True; S(info,'Reset Children').default_value=True
    n.link(O(info,'Instances'),S(inst,'Instance')); S(inst,'Pick Instance').default_value=True
    n.link(O(inst,'Instances'), out.inputs[0])
    host=bpy.data.objects.new('h'+variant, bpy.data.meshes.new('hm'+variant)); bpy.context.scene.collection.objects.link(host)
    md=host.modifiers.new('g','NODES'); md.node_group=tree
    dg=bpy.context.evaluated_depsgraph_get(); dg.update()
    ev=host.evaluated_get(dg); gs=ev.evaluated_geometry()
    ipc=gs.instances_pointcloud()
    print(variant, 'instances', None if ipc is None else len(ipc.points))
run('plain'); run('real')
