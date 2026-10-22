# Wall caps by touching chains: which loose cap pieces are connected (overlap or within 2 mm) to the wall through other pieces.
import bpy, json, sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
dg = bpy.context.evaluated_depsgraph_get()
def ev(o):
    e = o.evaluated_get(dg); me = e.to_mesh(); me.calc_loop_triangles()
    mw = e.matrix_world
    vs = [mw @ v.co for v in me.vertices]; ts = [tuple(t.vertices) for t in me.loop_triangles]
    e.to_mesh_clear(); return vs, ts
TOL = 0.002
res = {}
for wname, cname in (('Back wall, left', 'Back wall, left cap'), ('Back wall, right', 'Back wall, right cap'), ('Right wall behind hall', 'Right wall behind hall cap')):
    wv, wt = ev(bpy.data.objects[wname]); cv, ct = ev(bpy.data.objects[cname])
    wb = BVHTree.FromPolygons(wv, wt)
    parent = list(range(len(cv)))
    def f(x):
        while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for a, b, c in ct: parent[f(b)] = f(a); parent[f(c)] = f(a)
    comps = {}
    for t in ct: comps.setdefault(f(t[0]), []).append(t)
    keys = list(comps)
    bv = {k: BVHTree.FromPolygons(cv, comps[k]) for k in keys}
    verts = {k: [cv[i] for i in set(i for t in comps[k] for i in t)] for k in keys}
    def touch(b1, v1, b2):
        if b1.overlap(b2): return True
        for v in v1[::max(1, len(v1)//40)]:
            if b2.find_nearest(v, TOL)[0] is not None: return True
        return False
    nodes = ['WALL'] + keys
    adj = {n: set() for n in nodes}
    for k in keys:
        if touch(bv[k], verts[k], wb) or any(wb.find_nearest(v, TOL)[0] is not None for v in verts[k]):
            adj['WALL'].add(k); adj[k].add('WALL')
    for i, a in enumerate(keys):
        for b in keys[i+1:]:
            if touch(bv[a], verts[a], bv[b]) or touch(bv[b], verts[b], bv[a]):
                adj[a].add(b); adj[b].add(a)
    seen = {'WALL'}; stack = ['WALL']
    while stack:
        n = stack.pop()
        for m in adj[n]:
            if m not in seen: seen.add(m); stack.append(m)
    floating = [k for k in keys if k not in seen]
    res[cname] = {'pieces': len(keys), 'connected_to_wall': len(keys) - len(floating), 'floating': len(floating),
                  'floating_zmin': [round(min(v.z for v in verts[k]), 3) for k in floating][:6],
                  'lowest_z': round(min(v.z for k in keys for v in verts[k]), 3)}
print('CAPS2', json.dumps(res))
