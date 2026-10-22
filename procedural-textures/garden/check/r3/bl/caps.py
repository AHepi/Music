# Wall caps: for every loose piece of each cap, the vertical gap between its lowest points and what could carry it
# (wall top surface, or another cap piece below it). Negative = sunk into the wall. Reads only.
import bpy, json, sys
from mathutils import Vector
from mathutils.bvhtree import BVHTree
dg = bpy.context.evaluated_depsgraph_get()
def ev(o):
    e = o.evaluated_get(dg); me = e.to_mesh(); me.calc_loop_triangles()
    mw = e.matrix_world
    vs = [mw @ v.co for v in me.vertices]; ts = [tuple(t.vertices) for t in me.loop_triangles]
    e.to_mesh_clear(); return vs, ts
res = {}
for wname, cname in (('Back wall, left', 'Back wall, left cap'), ('Back wall, right', 'Back wall, right cap'), ('Right wall behind hall', 'Right wall behind hall cap')):
    wv, wt = ev(bpy.data.objects[wname]); cv, ct = ev(bpy.data.objects[cname])
    wtop = max(v.z for v in wv); wb = BVHTree.FromPolygons(wv, wt)
    parent = list(range(len(cv)))
    def f(x):
        while parent[x] != x: parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for a, b, c in ct: parent[f(b)] = f(a); parent[f(c)] = f(a)
    comps = {}
    for i in set(i for t in ct for i in t): comps.setdefault(f(i), []).append(i)
    pieces = []
    for cid, idx in comps.items():
        pts = [cv[i] for i in idx]; zmin = min(p.z for p in pts)
        idxset = set(idx)
        lowtris = [t for t in ct if t[0] in idxset and all(cv[i].z <= zmin + 0.004 for i in t)]
        low = [ (cv[t[0]] + cv[t[1]] + cv[t[2]]) / 3 for t in lowtris ] or [p for p in pts if p.z <= zmin + 0.004]
        others = [t for t in ct if f(t[0]) != cid]
        ob = BVHTree.FromPolygons(cv, others) if others else None
        best = None
        for p in low[:60]:
            c = []
            h = wb.ray_cast(p + Vector((0, 0, 0.001)), Vector((0, 0, -1)), 3.0)
            if h[0] is not None and h[0].z > wtop - 0.02: c.append(p.z - h[0].z)
            u = wb.ray_cast(p, Vector((0, 0, 1)), 0.08)
            if u[0] is not None and u[0].z >= wtop - 0.001: c.append(-(u[0].z - p.z))
            if ob is not None:
                h2 = ob.ray_cast(p + Vector((0, 0, 0.001)), Vector((0, 0, -1)), 3.0)
                if h2[0] is not None: c.append(p.z - h2[0].z)
            if c:
                m = min(c, key=abs) if False else min(c)
                best = m if best is None else min(best, m)
        pieces.append((round(zmin, 3), None if best is None else round(best * 1000, 1)))
    sup = [g for z, g in pieces if g is not None and g <= 3]
    floating = [(z, g) for z, g in pieces if g is None or g > 3]
    res[cname] = {'wall_top': round(wtop, 3), 'pieces': len(pieces), 'supported_within_3mm_or_sunk': len(sup), 'floating': len(floating),
                  'floating_detail': floating[:8], 'lowest_piece_z': min(z for z, g in pieces)}
print('CAPS', json.dumps(res))
json.dump(res, open(sys.argv[sys.argv.index('--') + 1], 'w'), indent=1)
