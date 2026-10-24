import sys
sys.dont_write_bytecode = True
sys.path.insert(0, '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/shapes')
import bpy, bmesh, stage_shapes as S
from mathutils.bvhtree import BVHTree
from mathutils import Vector
ctx = S.Ctx({'look': 'painted'}); S.repair_shoji(ctx)
ob = bpy.data.objects['Shoji bars']
bm = bmesh.new(); bm.from_mesh(ob.data); bm.faces.ensure_lookup_table()
comps = S.mesh_components(bm)
owner = {}
for ci, c in enumerate(comps):
    for v in c: owner[v.index] = ci
coords = [v.co.copy() for v in bm.verts]; polys = [[v.index for v in f.verts] for f in bm.faces]
tree = BVHTree.FromPolygons(coords, polys)
eps = 0.001; hits = {}
for f in bm.faces:
    c = f.calc_center_median(); i = owner[f.verts[0].index]
    for loc, hn, idx, _ in tree.find_nearest_range(c, eps):
        j = owner[bm.faces[idx].verts[0].index]
        if j != i and abs(f.normal.dot(hn)) > 0.999 and ((c - loc) - (c - loc).dot(hn) * hn).length < eps * 0.01 and f.normal.dot(hn) > 0:
            hits.setdefault(tuple(sorted((i, j))), []).append((tuple(round(x, 3) for x in c), tuple(round(x, 2) for x in f.normal)))
print('pairs', len(hits), 'faces', sum(len(v) for v in hits.values()))
for k, v in list(hits.items())[:6]:
    for ci in k:
        xs=[x.co.x for x in comps[ci]]; ys=[x.co.y for x in comps[ci]]; zs=[x.co.z for x in comps[ci]]
        print('  comp', ci, 'x %.3f..%.3f y %.3f..%.3f z %.3f..%.3f' % (min(xs),max(xs),min(ys),max(ys),min(zs),max(zs)))
    print('   at', v[:2])
