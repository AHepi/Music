# What this does: small probe of the Geometry Nodes Python API in Blender 5.2.2: creates a repeat zone, capture attribute, bake node, menu sockets and prints what works.
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gn_tools as gt
tree, g = gt.make_geometry_group('probe', [('Geometry','NodeSocketGeometry',None)])
# repeat zone
rin = tree.nodes.new('GeometryNodeRepeatInput'); rout = tree.nodes.new('GeometryNodeRepeatOutput')
print('repeat pair', rin.pair_with_output(rout))
print('repeat_items', [ (i.name, i.socket_type) for i in rout.repeat_items])
print('rin inputs', [s.name for s in rin.inputs], 'rout outputs', [s.name for s in rout.outputs])
# capture attribute
cap = tree.nodes.new('GeometryNodeCaptureAttribute')
print('capture items before', len(cap.capture_items))
cap.capture_items.new('FLOAT', 'width')
print('capture inputs', [s.name for s in cap.inputs], 'outputs', [s.name for s in cap.outputs])
# bake
bk = tree.nodes.new('GeometryNodeBake')
print('bake items', len(bk.bake_items))
bk.bake_items.new('GEOMETRY','Geometry')
print('bake inputs', [s.name for s in bk.inputs], [s.name for s in bk.outputs])
# simulation
si = tree.nodes.new('GeometryNodeSimulationInput'); so = tree.nodes.new('GeometryNodeSimulationOutput')
print('sim pair', si.pair_with_output(so), [i.name for i in so.state_items])
# menu input of transform
t = tree.nodes.new('GeometryNodeTransform')
print('transform inputs', [(s.name, s.type, getattr(s,'default_value',None)) for s in t.inputs])
t.inputs['Mode'].default_value = 'Matrix'
print('mode now', t.inputs['Mode'].default_value, [ (s.name, s.enabled) for s in t.inputs])
# mix node socket picking
m = tree.nodes.new('ShaderNodeMix'); m.data_type='RGBA'
print('mix', [(s.name, s.type, s.enabled) for s in m.inputs])
# accumulate field
acc = tree.nodes.new('GeometryNodeAccumulateField')
print('acc', [(s.name, s.type) for s in acc.inputs], [(s.name, s.type) for s in acc.outputs], acc.data_type, acc.domain)
# random value
rv = tree.nodes.new('FunctionNodeRandomValue'); print('rv', rv.data_type, [(s.name,s.type,s.enabled) for s in rv.inputs])
# distribute
d = tree.nodes.new('GeometryNodeDistributePointsOnFaces'); d.distribute_method='POISSON'; print('dist', [(s.name,s.enabled) for s in d.inputs])
# convex hull, merge by distance modes
mb = tree.nodes.new('GeometryNodeMergeByDistance'); print('merge mode', mb.inputs['Mode'].default_value)
# mesh bevel
for n in ['GeometryNodeMeshBevel','GeometryNodeSubdivideMesh','GeometryNodeSubdivisionSurface','GeometryNodeDuplicateElements','GeometryNodeProximity','GeometryNodeRaycast','GeometryNodeScaleElements','GeometryNodeCurveToMesh','GeometryNodeResampleCurve','GeometryNodeMeshToCurve','GeometryNodeMeshLine','GeometryNodeConvexHull','GeometryNodeSampleIndex','GeometryNodeSampleNearest','GeometryNodeInputIndex','GeometryNodeSplitEdges','GeometryNodeSetShadeSmooth','GeometryNodeCurvePrimitiveLine','GeometryNodeInstanceOnPoints','GeometryNodeDeleteGeometry','GeometryNodeMeshBoolean','GeometryNodeMeshCube','GeometryNodeMeshIcoSphere','GeometryNodeMeshToPoints','GeometryNodeSetMaterial','GeometryNodeJoinGeometry']:
    x = tree.nodes.new(n)
    print(n, [(s.name, s.enabled) for s in x.inputs], '->', [s.name for s in x.outputs], {k: getattr(x,k) for k in ('mode','domain','distribute_method','target_element') if hasattr(x,k)})
