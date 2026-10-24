import bpy, os
bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)
out={}
def make(realize):
    bpy.ops.mesh.primitive_plane_add(size=1); g=bpy.context.active_object
    tree=bpy.data.node_groups.new('t','GeometryNodeTree')
    tree.interface.new_socket('Geometry',in_out='INPUT',socket_type='NodeSocketGeometry')
    tree.interface.new_socket('Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
    N=tree.nodes;L=tree.links; go=N.new('NodeGroupOutput'); grid=N.new('GeometryNodeMeshGrid'); cube=N.new('GeometryNodeMeshCube')
    grid.inputs['Vertices X'].default_value=4; grid.inputs['Vertices Y'].default_value=4
    iop=N.new('GeometryNodeInstanceOnPoints'); L.new(grid.outputs['Mesh'],iop.inputs['Points']); L.new(cube.outputs['Mesh'],iop.inputs['Instance'])
    last=iop.outputs['Instances']
    if realize:
        r=N.new('GeometryNodeRealizeInstances'); L.new(last,r.inputs['Geometry']); last=r.outputs['Geometry']
    L.new(last,go.inputs['Geometry'])
    g.modifiers.new('gn','NODES').node_group=tree
    return g
for realize in (False,True):
    g=make(realize); bpy.ops.object.select_all(action='DESELECT'); g.select_set(True); bpy.context.view_layer.objects.active=g
    try:
        bpy.ops.object.modifier_apply(modifier='gn'); out[f'apply_realize={realize}']=(len(g.data.polygons), len(bpy.context.scene.objects))
    except Exception as e: out[f'apply_realize={realize}']=str(e)[:200]
result=out
