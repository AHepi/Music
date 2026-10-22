# the four short corner rails: what are they touching? (checker's own)
import bpy, sys, json, numpy as np
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
def parts(name):
    V, T, P = mesh_world(bpy.data.objects[name]); c = comps(len(V), P); tc = c[T[:, 0]]; out = []
    for k in range(c.max() + 1):
        vm = c == k; idx = -np.ones(len(V), dtype=np.int64); idx[vm] = np.arange(vm.sum())
        Vk = V[vm]; Tk = idx[T[tc == k]]
        out.append((name, k, Vk, Tk, BVHTree.FromPolygons([tuple(v) for v in Vk], [tuple(t) for t in Tk], epsilon=0.0)))
    return out
str_ = parts('Bridge stringers'); bear = parts('G6 wood / bridge bearers'); posts = parts('G6 wood / bridge posts')
pl = []
for n in ['Astra / varied planks.003', 'Astra / varied planks.004', 'Astra / varied planks.005', 'Astra / varied planks.006', 'Astra / varied planks.007']: pl += parts(n)
R = {}
for k in range(14, 18):
    s = str_[k]; Vs = s[2]
    row = {'bbox_min': np.round(Vs.min(0), 3).tolist(), 'bbox_max': np.round(Vs.max(0), 3).tolist(), 'touch': {}}
    for lab, group in (('stringers', str_), ('bearers', bear), ('posts', posts), ('planks', pl)):
        best = []
        for g in group:
            if g is s: continue
            if np.any(Vs.max(0) < g[2].min(0) - 0.01) or np.any(Vs.min(0) > g[2].max(0) + 0.01): continue
            ov = len(s[4].overlap(g[4]))
            # nearest distance from rail vertices
            dmin = 9
            for v in Vs[::2]:
                r = g[4].find_nearest(Vector(v), 0.05)
                if r[0] is not None: dmin = min(dmin, r[3])
            if ov > 0 or dmin < 0.01: best.append((g[0][-14:] + ':' + str(g[1]), ov, round(dmin * 1000, 1)))
        row['touch'][lab] = best[:8]
    R[str(k)] = row
    print(k, json.dumps(row), flush=True)
json.dump(R, open(OUT, 'w'), indent=1)
print('RAILS DONE')
