"""Terrain mesh: adaptive refinement around roads, heights and attributes from layout.terrain_eval, puddle water."""
import math, time
import numpy as np
import bpy, bmesh
from mathutils import kdtree
from common import *
import layout

HALF = 170.0
BASE_CELL = 4.0

def _combined_kd(step=2):
    pts = np.concatenate([r.P[::step] for r in layout.ROADS.values()])
    kd = kdtree.KDTree(len(pts))
    for i, p in enumerate(pts):
        kd.insert((p[0], p[1], 0.0), i)
    kd.balance()
    return kd

def road_distance_raster(res=0.5, extent=HALF + 5):
    kd = _combined_kd(2)
    n = int(2 * extent / res)
    xs = -extent + (np.arange(n) + 0.5) * res
    D = np.empty((n, n), dtype=np.float32)
    find = kd.find
    for i in range(n):
        x = xs[i]
        row = D[i]
        for j in range(n):
            row[j] = find((x, xs[j], 0.0))[2]
    return D, res, extent

def lookup(D, res, extent, X, Y):
    n = D.shape[0]
    ix = np.clip(((X + extent) / res).astype(int), 0, n - 1)
    iy = np.clip(((Y + extent) / res).astype(int), 0, n - 1)
    return D[ix, iy]

def road_distance_fast(res=1.0, extent=HALF + 5):
    """cheap raster: for the whole map only on a coarse grid; fine rings computed by dilation masks"""
    return None

def target_sizes(cx, cy, dr, db, zones):
    t = np.full(len(cx), 4.0)
    core = ((cx - 18.0) / 95.0) ** 2 + ((cy - 8.0) / 70.0) ** 2 < 1.0
    t = np.where(core, np.minimum(t, 2.0), t)
    vil = ((cx - 18.0) / 62.0) ** 2 + ((cy - 8.0) / 46.0) ** 2 < 1.0
    t = np.where(vil, np.minimum(t, 1.0), t)
    # roads
    t = np.where(dr < 14.0, np.minimum(t, 1.0), t)
    t = np.where(dr < 8.0, np.minimum(t, 0.5), t)
    t = np.where(dr < 4.6, np.minimum(t, 0.25), t)
    in_v = ((cx - 18.0) / 85.0) ** 2 + ((cy - 8.0) / 60.0) ** 2 < 1.0
    t = np.where((dr < 2.2) & in_v, np.minimum(t, 0.125), t)
    t = np.where((dr < 2.0) & (~in_v), np.minimum(t, 0.25), t)
    # buildings
    t = np.where(db < 9.0, np.minimum(t, 0.5), t)
    t = np.where(db < 3.5, np.minimum(t, 0.25), t)
    for (zx, zy, zr, zt) in zones:
        m = (cx - zx) ** 2 + (cy - zy) ** 2 < zr * zr
        t = np.where(m, np.minimum(t, zt), t)
    return t

def build_mesh(zones, name='Terrain', max_iter=9, log=None):
    t0 = time.time()
    D, res, ext = road_distance_raster(0.5, HALF + 5)
    if log is not None:
        log.append('raster %.1fs' % (time.time() - t0))
    bm = bmesh.new()
    n = int(round(2 * HALF / BASE_CELL))
    bmesh.ops.create_grid(bm, x_segments=n, y_segments=n, size=HALF)
    xs = np.array([v.co.x for v in bm.verts])
    if log is not None:
        log.append('grid extent %.2f..%.2f, nverts %d' % (xs.min(), xs.max(), len(bm.verts)))
    scale = HALF / max(abs(xs.max()), 1e-6)
    if abs(scale - 1.0) > 1e-3:
        bmesh.ops.scale(bm, vec=(scale, scale, 1.0), verts=bm.verts)
    bcent = np.array([[b['x'], b['y'], max(b['W'], b['D']) * 0.5 + 0.5] for b in layout.BUILDINGS])
    tmp = bpy.data.meshes.new('tmp_terrain_probe')
    for it in range(max_iter):
        bm.to_mesh(tmp)
        nf = len(tmp.polygons)
        cen = np.empty(nf * 3, dtype=np.float32)
        tmp.polygons.foreach_get('center', cen)
        cen = cen.reshape(-1, 3)
        area = np.empty(nf, dtype=np.float32)
        tmp.polygons.foreach_get('area', area)
        nloop = np.empty(nf, dtype=np.int32)
        tmp.polygons.foreach_get('loop_total', nloop)
        size = np.sqrt(area * np.where(nloop == 3, 2.0, 1.0))
        cx, cy = cen[:, 0].astype(float), cen[:, 1].astype(float)
        dr = lookup(D, res, ext, cx, cy).astype(float) - 0.5 * size      # conservative: nearest part of the face
        if len(bcent):
            dbs = np.sqrt((cx[:, None] - bcent[None, :, 0]) ** 2 + (cy[:, None] - bcent[None, :, 1]) ** 2) - bcent[None, :, 2]
            db = dbs.min(axis=1) - 0.5 * size
        else:
            db = np.full(nf, 99.0)
        tgt = target_sizes(cx, cy, np.maximum(dr, 0), np.maximum(db, 0), [(zx, zy, zr + 0.0, zt) for (zx, zy, zr, zt) in zones])
        split = size > tgt * 1.06
        ns = int(split.sum())
        if log is not None:
            log.append('iter %d faces %d split %d (%.1fs)' % (it, nf, ns, time.time() - t0))
        if ns == 0:
            break
        bm.faces.ensure_lookup_table()
        edges = set()
        for i in np.nonzero(split)[0]:
            for e in bm.faces[int(i)].edges:
                edges.add(e)
        bmesh.ops.subdivide_edges(bm, edges=list(edges), cuts=1, use_grid_fill=True)
    ngons = [f for f in bm.faces if len(f.verts) > 4]
    if ngons:
        bmesh.ops.triangulate(bm, faces=ngons)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    bpy.data.meshes.remove(tmp)
    return me

def vertex_cell_size(me):
    nv = len(me.vertices)
    co = np.empty(nv * 3, dtype=np.float32)
    me.vertices.foreach_get('co', co)
    co = co.reshape(-1, 3)
    ne = len(me.edges)
    ev = np.empty(ne * 2, dtype=np.int32)
    me.edges.foreach_get('vertices', ev)
    ev = ev.reshape(-1, 2)
    d = np.linalg.norm(co[ev[:, 0], :2] - co[ev[:, 1], :2], axis=1)
    acc = np.zeros(nv); cnt = np.zeros(nv)
    np.add.at(acc, ev[:, 0], d); np.add.at(acc, ev[:, 1], d)
    np.add.at(cnt, ev[:, 0], 1); np.add.at(cnt, ev[:, 1], 1)
    return acc / np.maximum(cnt, 1), co

def shape_mesh(me, log=None):
    t0 = time.time()
    cell, co = vertex_cell_size(me)
    X = co[:, 0].astype(float); Y = co[:, 1].astype(float)
    # evaluate in chunks to bound memory
    out = {}
    CH = 60000
    keys = ['z', 'clearing', 'cover', 'rut', 'wet', 'centre', 'yard', 'zbase']
    for k in keys:
        out[k] = np.zeros(len(X))
    for a in range(0, len(X), CH):
        b = min(len(X), a + CH)
        layout.CELL_CHUNK = cell[a:b]
        r = layout.terrain_eval(X[a:b], Y[a:b])
        for k in keys:
            out[k][a:b] = r[k]
        if log is not None:
            log.append('eval %d/%d (%.1fs)' % (b, len(X), time.time() - t0))
    co[:, 2] = out['z'].astype(np.float32)
    me.vertices.foreach_set('co', co.ravel())
    for nm, key in (('road', 'cover'), ('rut', 'rut'), ('wet', 'wet'), ('center', 'centre'), ('forest', None), ('yard', 'yard')):
        arr = (1.0 - out['clearing']) if key is None else out[key]
        at = me.attributes.get(nm) or me.attributes.new(name=nm, type='FLOAT', domain='POINT')
        at.data.foreach_set('value', np.clip(arr, 0, 1).astype(np.float32))
    nl = len(me.loops)
    lv = np.empty(nl, dtype=np.int32)
    me.loops.foreach_get('vertex_index', lv)
    uvl = me.uv_layers.get('UVMap') or me.uv_layers.new(name='UVMap')
    uvl.data.foreach_set('uv', co[lv][:, :2].astype(np.float32).ravel())
    me.polygons.foreach_set('use_smooth', np.ones(len(me.polygons), dtype=bool))
    me.update()
    return out

def build_puddles(terrain_me, name='Puddles'):
    """Flat water faces cut from the terrain faces that lie below each puddle's water level."""
    nv = len(terrain_me.vertices)
    co = np.empty(nv * 3, dtype=np.float32)
    terrain_me.vertices.foreach_get('co', co)
    co = co.reshape(-1, 3)
    nf = len(terrain_me.polygons)
    nloop = np.empty(nf, dtype=np.int32)
    terrain_me.polygons.foreach_get('loop_total', nloop)
    nl = len(terrain_me.loops)
    lv = np.empty(nl, dtype=np.int32)
    terrain_me.loops.foreach_get('vertex_index', lv)
    starts = np.empty(nf, dtype=np.int32)
    terrain_me.polygons.foreach_get('loop_start', starts)
    x0, y0 = co[lv[starts], 0], co[lv[starts], 1]
    mb = MB()
    infos = []
    for r in layout.ROADS.values():
        for (s0, side, Lp, ex) in r.puddles:
            g = r.gauge
            wob = r.wob(s0)
            c = side * g / 2 + wob + 0.06 * perlin2(s0 * 0.31, 1.1 * side + r.rid)
            xs, ys = [], []
            for ds in (-0.8 * Lp, 0.8 * Lp):
                x, y, tx, ty = r.point(s0 + ds)
                xs.append(x - ty * c); ys.append(y + tx * c)
            res = layout.terrain_eval(np.array(xs), np.array(ys), do_hoof=False)
            level = float(res['z'].min()) - 0.002
            x, y, tx, ty = r.point(s0)
            near = (np.abs(x0 - x) < Lp + 2.5) & (np.abs(y0 - y) < Lp + 2.5)
            made = 0
            for i in np.nonzero(near)[0]:
                vs = lv[starts[i]:starts[i] + nloop[i]]
                P = co[vs]
                if P[:, 2].min() >= level - 0.003:
                    continue
                d, l, s = r.query(np.array([P[:, 0].mean()]), np.array([P[:, 1].mean()]))
                if abs(s[0] - s0) > Lp * 0.95 or abs(l[0] - c) > 0.9:
                    continue
                Q = P.copy()
                Q[:, 2] = level
                if len(Q) == 4:
                    mb.quads_hard(Q[None], None, 0, True)
                else:
                    mb.tris_hard(Q[None], None, 0, True)
                made += 1
            infos.append((r.name, round(s0, 1), side, round(level, 3), made))
    return mb, infos
