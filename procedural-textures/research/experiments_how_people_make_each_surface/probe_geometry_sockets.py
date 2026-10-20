# What this does: lists the input and output socket names of the Geometry Nodes nodes the geometry tests use (Blender 5.2.2), so the
# test scripts use the exact names. Run: blender -b --python probe_geometry_sockets.py
import bpy
tree = bpy.data.node_groups.new('probe', 'GeometryNodeTree')
for kind, settings in [('GeometryNodeMeshGrid', {}), ('GeometryNodeDistributePointsOnFaces', {'distribute_method': 'POISSON'}), ('GeometryNodeInstanceOnPoints', {}),
                       ('GeometryNodeMeshIcoSphere', {}), ('GeometryNodeMeshCube', {}), ('FunctionNodeRandomValue', {'data_type': 'FLOAT'}),
                       ('FunctionNodeRandomValue', {'data_type': 'FLOAT_VECTOR'}), ('GeometryNodeSetPosition', {}), ('GeometryNodeRealizeInstances', {}),
                       ('GeometryNodeJoinGeometry', {}), ('GeometryNodeTransform', {}), ('GeometryNodeSetMaterial', {}), ('GeometryNodeInputIndex', {}),
                       ('GeometryNodeInputPosition', {}), ('GeometryNodeStoreNamedAttribute', {}), ('GeometryNodeInputID', {}), ('GeometryNodeMeshLine', {}),
                       ('GeometryNodeCurveToMesh', {}), ('GeometryNodeMeshToPoints', {}), ('GeometryNodeResampleCurve', {}), ('GeometryNodeCurvePrimitiveLine', {}),
                       ('GeometryNodeCurveLine', {}), ('FunctionNodeRotateEuler', {}), ('FunctionNodeAlignRotationToVector', {}), ('GeometryNodeSetMeshNormal', {}),
                       ('GeometryNodeSubdivisionSurface', {}), ('GeometryNodeCurveArc', {}), ('GeometryNodeInstanceTransform', {}), ('GeometryNodeInputNormal', {}),
                       ('GeometryNodeMergeByDistance', {}), ('GeometryNodeCaptureAttribute', {}), ('GeometryNodeSampleIndex', {})]:
    try:
        node = tree.nodes.new(kind)
        for key, value in settings.items():
            setattr(node, key, value)
        print(kind, settings, '\n   IN :', [(s.name, s.type) for s in node.inputs if s.enabled], '\n   OUT:', [s.name for s in node.outputs])
    except Exception as error:
        print(kind, 'FAILED', error)
