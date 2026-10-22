import bpy, sys, json, math, numpy as np
sys.path.insert(0, '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/checker2/scripts')
OUT = sys.argv[-1]
import importlib.util
# reuse the helper classes from struct.py without running its main: copy minimal helpers
from mathutils import Vector
from mathutils.bvhtree import BVHTree
def mesh_world(ob):
    me = ob.data; n = len(me.vertices)
    co = np.empty(n * 3); me.vertices.foreach_get('co', co); co = co.reshape(n, 3)
    M = np.array(ob.matrix_world); V = co @ M[:3, :3].T + M[:3, 3]
    me.calc_loop_triangles(); nt = len(me.loop_triangles)
    T = np.empty(nt * 3, dtype=np.int64); me.loop_triangles.foreach_get('vertices', T); T = T.reshape(nt, 3)
    polys = [tuple(p.vertices) for p in me.polygons]
    return V, T, polys
def comps(V, polys):
    parent = list(range(len(V)))
    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]; a = parent[a]
        return a
    for p in polys:
        r = find(p[0])
        for v in p[1:]:
            rv = find(v)
            if rv != r: parent[rv] = r
    roots = np.array([find(i) for i in range(len(V))]); _, c = np.unique(roots, return_inverse=True); return c
class P:
    def __init__(s, obj, k, V, T):
        s.obj, s.k, s.V, s.T = obj, k, V, T; s.bmin, s.bmax = V.min(axis=0), V.max(axis=0)
        s.bvh = BVHTree.FromPolygons([tuple(v) for v in V], [tuple(t) for t in T], epsilon=0.0)
def parts(name):
    V, T, polys = mesh_world(bpy.data.objects[name]); c = comps(V, polys); tc = c[T[:, 0]]; out = []
    for k in range(c.max() + 1):
        vm = c == k; im = -np.ones(len(V), dtype=np.int64); im[vm] = np.arange(vm.sum()); out.append(P(name, k, V[vm], im[T[tc == k]]))
    return out
R = {}
planks = []
for n in ['Astra / varied planks.003', 'Astra / varied planks.004', 'Astra / varied planks.005', 'Astra / varied planks.006', 'Astra / varied planks.007']:
    planks += parts(n)
posts = parts('G6 wood / bridge posts'); bearers = parts('G6 wood / bridge bearers'); stringers = parts('Bridge stringers')
pegs = parts('G6 wood / bridge pegs'); cramps = parts('G6 wood / bridge cramps')
def touches(a, b):
    if np.any(a.bmin > b.bmax + 0.002) or np.any(b.bmin > a.bmax + 0.002): return False
    return len(a.bvh.overlap(b.bvh)) > 0
# pegs: touch (triangle overlap) any wood part?
wood = planks + posts + bearers + stringers
touch = 0; none = []
for pg in pegs:
    hit = None
    for w in wood:
        if touches(pg, w): hit = w.obj + ':' + str(w.k); break
    if hit: touch += 1
    else: none.append(pg.k)
R['pegs'] = {'n': len(pegs), 'intersect_or_touch_wood': touch, 'not_touching_ids': none}
# cramps: groups of 3 (bar + 2 heads): heads touching bar? bar touching planks?
rows = []
for g in range(0, len(cramps), 3):
    bar, h1, h2 = cramps[g], cramps[g + 1], cramps[g + 2]
    d = []
    for h in (h1, h2):
        # distance from head centre to bar surface
        c = (h.bmin + h.bmax) / 2
        r = bar.bvh.find_nearest(Vector(c), 1.0)
        d.append(round(r[3] * 1000, 1) if r[0] is not None else None)
    on_planks = sum(1 for pl in planks if touches(bar, pl))
    rows.append({'cramp': g // 3, 'bar_size_cm': np.round((bar.bmax - bar.bmin) * 100, 1).tolist(), 'head_centre_to_bar_mm': d, 'planks_touched_by_bar': on_planks, 'bar_z': [round(float(bar.bmin[2]), 3), round(float(bar.bmax[2]), 3)]})
R['cramps'] = rows
# hole areas at the turns: rays down every 2 cm within 0.52 m of the centre line near nodes (radius 0.9 m)
allV = np.vstack([p.V for p in planks]); off = 0; allT = []
for p in planks: allT.append(p.T + off); off += len(p.V)
bvh = BVHTree.FromPolygons([tuple(v) for v in allV], [tuple(t) for t in np.vstack(allT)], epsilon=0.0)
nodes = [(-5.95, 1.55), (-3.90, 0.15), (-2.00, 1.00), (-0.55, -0.60)]
def dist_to_polyline(p):
    best = 9
    for a, b in zip(nodes[:-1], nodes[1:]):
        a = np.array(a); b = np.array(b); ab = b - a; t = np.clip((p - a) @ ab / (ab @ ab), 0, 1); best = min(best, np.linalg.norm(p - (a + t * ab)))
    return best
holes = {}
for ni, nd in enumerate(nodes[1:3], start=1):
    nd = np.array(nd)
    cnt = 0; tot = 0; pts = []
    for x in np.arange(nd[0] - 0.9, nd[0] + 0.9, 0.02):
        for y in np.arange(nd[1] - 0.9, nd[1] + 0.9, 0.02):
            p = np.array([x, y])
            if np.linalg.norm(p - nd) > 0.9: continue
            if dist_to_polyline(p) > 0.52: continue
            tot += 1
            h = bvh.ray_cast(Vector((x, y, 1.0)), Vector((0, 0, -1)), 2.0)
            if h[0] is None:
                cnt += 1; pts.append((x, y))
    # discount the plank gaps: count only points whose 5x5 neighbourhood (10 cm) is mostly empty = rough open area; compute with a coarse morphological erosion
    grid = {}
    for (x, y) in pts: grid[(round(x / 0.02), round(y / 0.02))] = 1
    big = 0
    for (gx, gy) in grid:
        if all(((gx + i, gy + j) in grid) for i in range(-2, 3) for j in range(-2, 3)): big += 1
    holes['node %d (%.2f,%.2f)' % (ni, nd[0], nd[1])] = {'open_points_all_m2': round(cnt * 0.0004, 3), 'corridor_area_m2': round(tot * 0.0004, 3), 'open_area_in_blobs_wider_than_8cm_m2': round(big * 0.0004, 3)}
R['turn_holes'] = holes
json.dump(R, open(OUT, 'w'), indent=1); print('SMALL DONE', json.dumps(R)[:1500])
