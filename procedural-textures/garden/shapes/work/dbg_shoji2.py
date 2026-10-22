import sys
sys.dont_write_bytecode = True
sys.path.insert(0, 'proc-work/garden/shapes')
import bpy, bmesh, stage_shapes as S
from mathutils.bvhtree import BVHTree
ctx = S.Ctx({'look': 'painted'}); S.repair_shoji(ctx)
ob = bpy.data.objects['Shoji bars']
bm = bmesh.new(); bm.from_mesh(ob.data); bm.verts.ensure_lookup_table()
comps = S.mesh_components(bm)
trees = []
for c in comps:
    idx = {v.index for v in c}
    fs = [f for f in bm.faces if f.verts[0].index in idx]
    vs = [v.co.copy() for v in c]; remap = {v.index: k for k, v in enumerate(c)}
    trees.append(BVHTree.FromPolygons(vs, [[remap[v.index] for v in f.verts] for f in fs]))
conn = [0]*len(comps)
for i in range(len(comps)):
    for j in range(i+1, len(comps)):
        if trees[i].overlap(trees[j]): conn[i]+=1; conn[j]+=1
iso = [i for i,c in enumerate(conn) if c==0]
print('comps', len(comps), 'isolated (no overlapping part)', len(iso))
for i in iso[:8]:
    c = comps[i]; xs=[x.co.x for x in c]; ys=[x.co.y for x in c]; zs=[x.co.z for x in c]
    print('  comp', i, 'x %.3f..%.3f y %.3f..%.3f z %.3f..%.3f' % (min(xs),max(xs),min(ys),max(ys),min(zs),max(zs)))
