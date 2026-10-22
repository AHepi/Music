import bpy, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

def world_mesh(ob, evaluated=False):
    if evaluated:
        dg = bpy.context.evaluated_depsgraph_get()
        eo = ob.evaluated_get(dg)
        me = eo.to_mesh()
    else:
        me = ob.data
    n = len(me.vertices)
    co = np.empty(n * 3, dtype=np.float64)
    me.vertices.foreach_get('co', co)
    co = co.reshape(n, 3)
    M = np.array(ob.matrix_world)
    V = co @ M[:3, :3].T + M[:3, 3]
    me.calc_loop_triangles()
    nt = len(me.loop_triangles)
    T = np.empty(nt * 3, dtype=np.int64)
    me.loop_triangles.foreach_get('vertices', T)
    T = T.reshape(nt, 3)
    npoly = len(me.polygons)
    P = []
    for p in me.polygons:
        P.append(tuple(p.vertices))
    return V, T, P

def components(nv, P):
    parent = np.arange(nv)
    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for poly in P:
        r = find(poly[0])
        for v in poly[1:]:
            rv = find(v)
            if rv != r:
                parent[rv] = r
    roots = np.array([find(i) for i in range(nv)])
    _, comp = np.unique(roots, return_inverse=True)
    return comp

class Parts:
    """loose parts of a list of objects, world space"""
    def __init__(self, names, label=''):
        self.items = []   # dict(obj, idx, V (verts), T (tris local idx array into V))
        for nm in names:
            ob = bpy.data.objects[nm]
            V, T, P = world_mesh(ob)
            comp = components(len(V), P)
            ncomp = comp.max() + 1 if len(V) else 0
            tcomp = comp[T[:, 0]]
            for c in range(ncomp):
                vm = comp == c
                idxmap = -np.ones(len(V), dtype=np.int64)
                idxmap[vm] = np.arange(vm.sum())
                tm = tcomp == c
                self.items.append({'obj': nm, 'idx': c, 'V': V[vm], 'T': idxmap[T[tm]]})
        for k, it in enumerate(self.items):
            it['id'] = k
            it['bmin'] = it['V'].min(axis=0)
            it['bmax'] = it['V'].max(axis=0)
        self._bvh = {}
        self._all = None
    def bvh(self, k):
        if k not in self._bvh:
            it = self.items[k]
            self._bvh[k] = BVHTree.FromPolygons([tuple(v) for v in it['V']], [tuple(t) for t in it['T']], epsilon=0.0)
        return self._bvh[k]
    def all_bvh(self):
        if self._all is None:
            Vs, Ts, lab = [], [], []
            off = 0
            for it in self.items:
                Vs.append(it['V']); Ts.append(it['T'] + off); lab += [it['id']] * len(it['T']); off += len(it['V'])
            V = np.vstack(Vs); T = np.vstack(Ts)
            self._all = (BVHTree.FromPolygons([tuple(v) for v in V], [tuple(t) for t in T], epsilon=0.0), np.array(lab))
        return self._all
