# What this does: lists the Geometry Nodes node names and socket names in Blender 5.2 that the board-mesh test needs. Prints only.
import bpy
tree = bpy.data.node_groups.new('probe', 'GeometryNodeTree')
for idname in ('GeometryNodeMeshLine', 'GeometryNodeMeshGrid', 'GeometryNodeMeshToPoints', 'GeometryNodeInstanceOnPoints', 'GeometryNodeRealizeInstances',
               'GeometryNodeStoreNamedAttribute', 'GeometryNodeInputNamedAttribute', 'FunctionNodeRandomValue', 'GeometryNodeInputIndex', 'GeometryNodeSetMaterial',
               'GeometryNodeJoinGeometry', 'GeometryNodeTransform', 'GeometryNodeFieldOnDomain', 'GeometryNodeInputPosition', 'ShaderNodeVectorMath', 'ShaderNodeMath',
               'GeometryNodeSetPosition', 'FunctionNodeCompare', 'GeometryNodeSwitch', 'GeometryNodeIndexSwitch', 'ShaderNodeCombineXYZ', 'ShaderNodeSeparateXYZ'):
    try:
        n = tree.nodes.new(idname)
        print(idname, 'IN', [(s.name, s.type) for s in n.inputs], 'OUT', [(s.name, s.type) for s in n.outputs])
    except Exception as e:
        print(idname, 'FAILED', e)
n = tree.nodes.new('GeometryNodeStoreNamedAttribute'); print('store props', n.data_type, n.domain, [i.identifier for i in n.bl_rna.properties['data_type'].enum_items], [i.identifier for i in n.bl_rna.properties['domain'].enum_items])
n = tree.nodes.new('FunctionNodeRandomValue'); print('random types', [i.identifier for i in n.bl_rna.properties['data_type'].enum_items])
