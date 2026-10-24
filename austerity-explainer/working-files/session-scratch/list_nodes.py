import bpy
names = [n for n in dir(bpy.types) if 'SeparateColor' in n or 'CombineColor' in n or 'ImageTexture' in n or 'EulerToRotation' in n or 'RandomValue' in n or 'DistributePoints' in n or 'InstanceOnPoints' in n or 'CollectionInfo' in n or 'ObjectInfo' in n or 'AlignEuler' in n or 'AlignRotation' in n or 'RotateInstances' in n or 'SubdivideMesh' in n or 'SeparateGeometry' in n or 'InputNamedAttribute' in n or 'SetPosition' in n]
print('NODES', names)
t = bpy.data.node_groups.new('t', 'GeometryNodeTree')
for idname in ('FunctionNodeSeparateColor', 'ShaderNodeSeparateColor', 'FunctionNodeCombineColor', 'GeometryNodeImageTexture', 'FunctionNodeEulerToRotation', 'FunctionNodeRandomValue', 'GeometryNodeDistributePointsOnFaces', 'GeometryNodeInstanceOnPoints', 'GeometryNodeCollectionInfo', 'GeometryNodeObjectInfo', 'GeometryNodeSubdivideMesh', 'GeometryNodeSeparateGeometry', 'GeometryNodeInputNamedAttribute', 'GeometryNodeSetPosition', 'FunctionNodeCompare', 'FunctionNodeBooleanMath', 'GeometryNodeInputPosition', 'GeometryNodeInputNormal', 'ShaderNodeMath', 'ShaderNodeVectorMath', 'ShaderNodeSeparateXYZ', 'ShaderNodeCombineXYZ'):
    try:
        n = t.nodes.new(idname)
        print('OK ', idname, [s.name + ':' + s.type for s in n.inputs][:12])
    except Exception as e:
        print('NO ', idname, str(e)[:80])
