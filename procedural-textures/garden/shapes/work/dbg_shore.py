import sys
sys.dont_write_bytecode = True
sys.path.insert(0, 'proc-work/garden/shapes')
import bpy, bmesh, stage_shapes as S, numpy as np
from mathutils.bvhtree import BVHTree
from mathutils import Vector
ctx = S.Ctx({'look': 'painted'}); S.step_shore(ctx)
ob = bpy.data.objects['Shore stones']
bm = bmesh.new(); bm.from_mesh(ob.data); bm.verts.ensure_lookup_table()
comps = S.mesh_components(bm)
g = ctx.ground
print('components', len(comps))
for c in comps:
    zs = [v.co.z for v in c]; xs=[v.co.x for v in c]; ys=[v.co.y for v in c]
    cx, cy = np.mean(xs), np.mean(ys)
    lowest = min(c, key=lambda v: v.co.z)
    gz = g.z(lowest.co.x, lowest.co.y)
    gzc = g.z(cx, cy)
    # distance from every vertex to ground surface
    dmin = min(g.bvh.find_nearest(v.co)[3] for v in c)
    print('stone at (%.2f,%.2f) z %.3f..%.3f ground c %.3f, under lowest vertex %.3f, min vertex-to-ground dist %.3f' % (cx, cy, min(zs), max(zs), gzc, gz, dmin))
