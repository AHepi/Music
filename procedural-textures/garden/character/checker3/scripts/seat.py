# Are pegs and cramps really seated on / in wood? Per part: vertices inside the wood volume, nearest distance of the outside ones.
import bpy, sys, json, numpy as np
sys.path.insert(0, '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/character/checker/scripts')
from mathutils import Vector
from mathutils.bvhtree import BVHTree
OUT = sys.argv[-1]
def mesh_world(ob):
    me = ob.data; n = len(me.vertices)
    co = np.empty(n * 3); me.vertices.foreach_get('co', co); co = co.reshape(n, 3)
    M = np.array(ob.matrix_world); V = co @ M[:3, :3].T + M[:3, 3]
    me.calc_loop_triangles(); nt = len(me.loop_triangles)
    T = np.empty(nt * 3, dtype=np.int64); me.loop_triangles.foreach_get('vertices', T)
    return V, T.reshape(nt, 3), [tuple(p.vertices) for p in me.polygons]
def comps(nv, P):
    par = list(range(nv))
    def f(a):
        while par[a] != a: par[a] = par[par[a]]; a = par[a]
        return a
    for p in P:
        r = f(p[0])
        for v in p[1:]:
            rv = f(v)
            if rv != r: par[rv] = r
    roots = np.array([f(i) for i in range(nv)]); _, c = np.unique(roots, return_inverse=True); return c
# all wood on the bridge, one BVH
names = ['Astra / varied planks.003', 'Astra / varied planks.004', 'Astra / varied planks.005', 'Astra / varied planks.006', 'Astra / varied planks.007', 'Bridge stringers', 'G6 wood / bridge bearers', 'G6 wood / bridge posts']
Vs, Ts, off = [], [], 0
for n in names:
    V, T, P = mesh_world(bpy.data.objects[n]); Vs.append(V); Ts.append(T + off); off += len(V)
V = np.vstack(Vs); T = np.vstack(Ts)
bvh = BVHTree.FromPolygons([tuple(v) for v in V], [tuple(t) for t in T], epsilon=0.0)
def inside(p):
    votes = 0
    for d in ((0.0001, 0.0002, 1.0), (1.0, 0.0003, 0.0002), (0.0002, 1.0, 0.0003)):
        d = Vector(d).normalized(); pos = Vector(p); n = 0
        for _ in range(30):
            h = bvh.ray_cast(pos, d, 5.0)
            if h[0] is None: break
            n += 1; pos = h[0] + d * 1e-5
        votes += n % 2
    return votes >= 2
def classify(obname):
    Vp, Tp, Pp = mesh_world(bpy.data.objects[obname]); c = comps(len(Vp), Pp)
    rows = []
    for k in range(c.max() + 1):
        vv = Vp[c == k]
        ins = 0; dmin = 9; dsum = []
        for v in vv:
            if inside(v): ins += 1
            r = bvh.find_nearest(Vector(v), 0.1)
            d = r[3] if r[0] is not None else 9
            dmin = min(dmin, d); dsum.append(d)
        rows.append({'k': k, 'nv': len(vv), 'verts_inside_wood': ins, 'min_dist_mm': round(dmin * 1000, 2), 'bbox_min': np.round(vv.min(0), 3).tolist(), 'bbox_max': np.round(vv.max(0), 3).tolist()})
    return rows
R = {}
for ob in ('G6 wood / bridge pegs', 'G6 wood / bridge cramps'):
    rows = classify(ob)
    R[ob] = rows
    seated = [r for r in rows if r['verts_inside_wood'] > 0 or r['min_dist_mm'] <= 1.0]
    R[ob + ' summary'] = {'parts': len(rows), 'seated_(some_vertex_inside_or_within_1mm)': len(seated), 'floating': [r for r in rows if r not in seated]}
    print(ob, R[ob + ' summary']['parts'], len(seated), flush=True)
json.dump(R, open(OUT, 'w'), indent=1)
print('SEAT DONE')
