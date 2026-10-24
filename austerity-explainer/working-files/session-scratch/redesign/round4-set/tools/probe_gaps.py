# What this does: the smallest distance between the meshes of pairs of things in the dressed Works (BVH trees), to
# check nothing pokes into anything (scratch, round 4).
import bpy, itertools
from mathutils.bvhtree import BVHTree
from mathutils import Vector
dg = bpy.context.evaluated_depsgraph_get()
def tree(holder_name):
    h = bpy.data.objects.get(holder_name)
    if h is None: return None
    verts, polys = [], []
    for o in [h] + list(h.children_recursive):
        if o.type != 'MESH': continue
        m = o.evaluated_get(dg).to_mesh()
        base = len(verts)
        verts += [o.matrix_world @ v.co for v in m.vertices]
        polys += [[base + i for i in p.vertices] for p in m.polygons]
        o.evaluated_get(dg).to_mesh_clear()
    return BVHTree.FromPolygons(verts, polys), verts
names = ['brazier-drum', 'man-1', 'man-2', 'man-3', 'man-4', 'man-5', 'man-6', 'man-7', 'no-1-drum-petrol', 'no-1-drum-diesel',
         'no-2-drum-petrol', 'no-2-drum-diesel', 'no-2-man-1', 'no-2-man-2', 'no-2-man-3', 'handcart', 'hurricane-lantern', 'lunch-tin']
trees = {n: tree(n) for n in names}
for a, b in itertools.combinations(names, 2):
    ta, tb = trees[a], trees[b]
    if not ta or not tb: continue
    hits = ta[0].overlap(tb[0])
    # nearest distance from a sample of b's points to a
    best = min((ta[0].find_nearest(v)[3] for v in tb[1][::7]), default=9)
    if hits or best < 0.15:
        print('GAP', a, b, 'touching faces' if hits else '', round(best, 3))
