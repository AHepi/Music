# Checker script: does every separate piece of each wall cap touch (or overlap) the wall or another cap piece?
# A piece counts as attached if its surface intersects another piece's/the wall's surface, or if any of its vertices is
# within 2 mm of the others' surface, or any vertex of the others is within 2 mm of it.  Run:
#   blender -b --disable-autoexec FILE.blend --python measure_caps.py -- OUT.json
import bpy, sys, json, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

out_path = sys.argv[sys.argv.index('--') + 1]
dg = bpy.context.evaluated_depsgraph_get()


def evald(o):
    ev = o.evaluated_get(dg)
    me = ev.to_mesh()
    mw = ev.matrix_world
    bm = bmesh.new(); bm.from_mesh(me); ev.to_mesh_clear()
    bm.verts.ensure_lookup_table()
    return bm, mw


def pieces_of(o):
    bm, mw = evald(o)
    seen = set(); comps = []
    for v in bm.verts:
        if v.index in seen:
            continue
        st = [v]; seen.add(v.index); idx = []
        while st:
            u = st.pop(); idx.append(u.index)
            for e in u.link_edges:
                w = e.other_vert(u)
                if w.index not in seen:
                    seen.add(w.index); st.append(w)
        s = set(idx)
        verts = [mw @ bm.verts[i].co for i in idx]
        remap = {i: k for k, i in enumerate(idx)}
        polys = []
        for f in bm.faces:
            if f.verts[0].index in s:
                polys.append(tuple(remap[x.index] for x in f.verts))
        comps.append((verts, polys))
    bm.free()
    return comps


def bvh(verts, polys):
    return BVHTree.FromPolygons(verts, polys, epsilon=0.0)


R = {}
for wall in ('Back wall, left', 'Back wall, right', 'Right wall behind hall'):
    wo = bpy.data.objects[wall]; co = bpy.data.objects[wall + ' cap']
    wcomps = pieces_of(wo)
    wv = [v for c in wcomps for v in c[0]]
    wpolys = []
    off = 0
    for c in wcomps:
        wpolys += [tuple(i + off for i in p) for p in c[1]]; off += len(c[0])
    wall_top = max(v.z for v in wv)
    parts = pieces_of(co)
    nodes = [('WALL', wv, wpolys)] + [(f'piece{k}', v, p) for k, (v, p) in enumerate(parts)]
    # build bvh per node
    bv = [bvh(v, p) for (_, v, p) in nodes]
    n = len(nodes)
    adj = [[False] * n for _ in range(n)]
    mind = [[9.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            touch = False
            if bv[i].overlap(bv[j]):
                touch = True; d = 0.0
            else:
                d = 9.0
                for p in nodes[i][1][::max(1, len(nodes[i][1]) // 60)]:
                    r = bv[j].find_nearest(p)
                    if r[3] is not None: d = min(d, r[3])
                for p in nodes[j][1][::max(1, len(nodes[j][1]) // 60)]:
                    r = bv[i].find_nearest(p)
                    if r[3] is not None: d = min(d, r[3])
                touch = d < 0.002
            adj[i][j] = adj[j][i] = touch
            mind[i][j] = mind[j][i] = d
    # connected component of WALL through touches
    seen = {0}; st = [0]
    while st:
        u = st.pop()
        for v in range(n):
            if adj[u][v] and v not in seen:
                seen.add(v); st.append(v)
    floating = [nodes[i][0] for i in range(1, n) if i not in seen]
    # distance of each floating piece to the attached cluster
    fl = []
    for i in range(1, n):
        if i not in seen:
            d = min(mind[i][j] for j in seen)
            zs = [v.z for v in nodes[i][1]]
            fl.append({'piece': nodes[i][0], 'verts': len(nodes[i][1]), 'z_min': round(min(zs), 3), 'z_max': round(max(zs), 3),
                       'nearest_gap_to_attached_cm': round(d * 100, 2)})
    cz = [v.z for (_, vv, _) in nodes[1:] for v in vv]
    R[wall] = {'pieces': n - 1, 'attached_to_wall_cluster': len(seen) - 1, 'floating_pieces': len(floating),
               'floating_detail': fl[:8], 'wall_top_z': round(wall_top, 3), 'cap_zmin': round(min(cz), 3), 'cap_zmax': round(max(cz), 3)}
json.dump(R, open(out_path, 'w'), indent=1)
print('CAPS_DONE')
