# What this does: checks what Accumulate Field's "Leading" and "Trailing" outputs really are (does Leading include the current element?).
import os, sys, json
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy, numpy as np
import gn_tools as gt
gt.new_scene(64)
tree, g = gt.make_geometry_group('acc test', [('Geometry','NodeSocketGeometry',None)])
g.node('GeometryNodeMeshLine', 'line', {'Count': 5, 'Offset': (1.0, 0, 0)}, mode='OFFSET')
g.node('GeometryNodeMeshToPoints', 'pts', {'Mesh': ('line', 'Mesh')})
g.node('GeometryNodeInputIndex', 'idx')
g.math('val', 'ADD', ('idx', 'Index'), 1.0)      # values 1,2,3,4,5
g.node('GeometryNodeAccumulateField', 'acc', {'Value': ('val', 0)}, data_type='FLOAT', domain='POINT')
prev = ('pts', 'Points')
for nm in ('Leading', 'Trailing', 'Total'):
    g.node('GeometryNodeStoreNamedAttribute', 's'+nm, {'Geometry': prev, 'Name': nm, 'Value': ('acc', nm)}, data_type='FLOAT', domain='POINT')
    prev = ('s'+nm, 'Geometry')
g.node('GeometryNodePointsToVertices', 'v', {'Points': prev})
g.link('v', 'Mesh', 'out', 'Geometry')
obj, m = gt.add_geometry_object('acc', tree)
print({n: gt.evaluated_attribute(obj, n).tolist() for n in ('Leading', 'Trailing', 'Total')})
