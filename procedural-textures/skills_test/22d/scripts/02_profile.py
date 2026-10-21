# What this does: prints a cross-section of the road (x and height of the vertices near y=5) for the road, gutter, kerb and pavement meshes, and the face-normal mix, so I know where the gutter edge is. Changes nothing.
import bpy, math
from collections import Counter
for name in ('street_setts', 'street_channels', 'street_kerbs', 'street_pavements', 'ground'):
    o = bpy.data.objects[name]
    me = o.data
    print('MESH', name, 'verts', len(me.vertices), 'faces', len(me.polygons), 'xrange', round(min(v.co.x for v in me.vertices), 3), round(max(v.co.x for v in me.vertices), 3),
          'yrange', round(min(v.co.y for v in me.vertices), 2), round(max(v.co.y for v in me.vertices), 2), 'matrix identity', o.matrix_world.is_identity)
    up = [p for p in me.polygons if p.normal.z > 0.9]
    print('   faces with normal up (z>0.9):', len(up), 'area', round(sum(p.area for p in up), 2), 'slopes>0.97', len([p for p in me.polygons if 0.5 < p.normal.z <= 0.97]))
    pts = sorted({(round(v.co.x, 3), round(v.co.z, 3)) for v in me.vertices if 4.5 < v.co.y < 5.5})
    print('   section near y=5 (x,z):', pts[:40])
