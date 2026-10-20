# What this does: tests Capture Attribute (Geometry Nodes 5.2) for "remember a value from before the geometry changes": 5 cubes are instanced on 5 points; the instance
# INDEX is captured on the Instance domain BEFORE Realize Instances; after realizing, the captured value is stored as a named attribute and read back from Python.
# Expected: every vertex of cube number k carries the value k. Also tests the same with Store Named Attribute (INSTANCE domain) for comparison, and shows that a plain Index
# read AFTER realizing is the vertex index (NOT the cube number), which is why Capture/Store before Realize is needed.
# Run: blender -b --disable-autoexec -t 1 --python t09_capture_attribute.py
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy, numpy as np
import gn_tools as gt
gt.new_scene(32)
tree, g = gt.make_geometry_group('capture test', [('Geometry', 'NodeSocketGeometry', None)])
g.node('GeometryNodeMeshLine', 'line', {'Count': 5, 'Offset': (0.2, 0.0, 0.0)}, mode='OFFSET')
g.node('GeometryNodeMeshToPoints', 'points', {'Mesh': ('line', 'Mesh')})
g.node('GeometryNodeMeshCube', 'cube', {'Size': (0.1, 0.1, 0.1)})
g.node('GeometryNodeInstanceOnPoints', 'inst', {'Points': ('points', 'Points'), 'Instance': ('cube', 'Mesh')})
g.node('GeometryNodeInputIndex', 'index')
g.node('GeometryNodeCaptureAttribute', 'capture', {'Geometry': ('inst', 'Instances')}, domain='INSTANCE')
g.nodes['capture'].capture_items.new('INT', 'cube_number')
g.link('index', 'Index', 'capture', 'cube_number')
g.node('GeometryNodeStoreNamedAttribute', 'store captured', {'Geometry': ('capture', 'Geometry'), 'Name': 'from_capture', 'Value': ('capture', 'cube_number')}, data_type='INT', domain='INSTANCE')
g.node('GeometryNodeStoreNamedAttribute', 'store direct', {'Geometry': ('store captured', 'Geometry'), 'Name': 'from_store', 'Value': ('index', 'Index')}, data_type='INT', domain='INSTANCE')
g.node('GeometryNodeRealizeInstances', 'real', {'Geometry': ('store direct', 'Geometry')})
g.node('GeometryNodeStoreNamedAttribute', 'store late index', {'Geometry': ('real', 'Geometry'), 'Name': 'index_after', 'Value': ('index', 'Index')}, data_type='INT', domain='POINT')
g.link('store late index', 'Geometry', 'out', 'Geometry')
obj, _ = gt.add_geometry_object('capture', tree)
points = gt.evaluated_vertices(obj)
res = {'vertices': len(points)}
for name in ('from_capture', 'from_store', 'index_after'):
    values = gt.evaluated_attribute(obj, name)
    per_cube = [sorted(set(int(v) for v in values[(points[:, 0] > k * 0.2 - 0.1) & (points[:, 0] < k * 0.2 + 0.1)])) for k in range(5)]
    res[name + '_values_found_on_cube_0..4'] = per_cube[:5] if name != 'index_after' else [p[:3] + ['...'] if len(p) > 3 else p for p in per_cube]
json.dump(res, open(os.path.join(HERE, 'out', 't09_capture_results.json'), 'w'), indent=1)
print(json.dumps(res, indent=1))
