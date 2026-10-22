"""wood_frame.py - steps 5 and 6: hall posts (chamfer + real drying checks), hall beams (chamfer, dark end grain), eave soffit, rafter tails
(chamfer), veranda steps (chips, worn dip), gravel timber edge, shoji bars; normal maps in the owned materials.
The originals are snapshotted once (mesh 'G6 wood / orig <name>', fake user) so a second apply starts again from the original shape.
"""
import math
import numpy as np
import bpy
import bmesh
from wood_geo import MeshData, perp, unit, box_uv_for_faces, fix_winding


def post_loft(cx, cy, half, cc, z0, z1, checks, ch=0.01, step=0.15):
    """Square post, chamfered vertical edges (cc), chamfered ends (ch) and real V-grooves (drying checks).
    checks: list of dict(face 0..3 (+x,+y,-x,-y), s lateral offset, hw half width, depth, za, zb)."""
    faces_n = [np.array(v, float) for v in ((1, 0), (0, 1), (-1, 0), (0, -1))]
    zs = [z0]
    z = z0 + ch
    zs.append(z)
    while z + step < z1 - ch:
        z += step
        zs.append(z)
    zs.append(z1 - ch)
    zs.append(z1)
    V, rings = [], []
    for zi, zz in enumerate(zs):
        ends = zi in (0, len(zs) - 1)
        k = (half - ch) / half if ends else 1.0
        ring = []
        for fi in range(4):
            n = faces_n[fi]
            t = perp(n)
            smax = half - cc
            pts = [(-smax, 0.0), (smax, 0.0)]
            grooves = [c for c in checks if c['face'] == fi]
            gp = []
            for c in grooves:
                dep = 0.0
                if c['za'] < zz < c['zb'] and not ends:
                    u = (zz - c['za']) / (c['zb'] - c['za'])
                    dep = c['depth'] * math.sin(math.pi * u) ** 0.6
                gp.append((c['s'] - c['hw'] * (dep > 0), 0.0)); gp.append((c['s'], dep)); gp.append((c['s'] + c['hw'] * (dep > 0), 0.0))
            gp.sort(key=lambda p: p[0])
            seq = [pts[0]] + gp + [pts[1]]
            for s_, dep in seq:
                p = n * (half - dep) + t * s_
                V.append((cx + p[0] * k, cy + p[1] * k, zz))
                ring.append(len(V) - 1)
        rings.append(ring)
    nr = len(rings[0])
    F = []
    for r in range(len(rings) - 1):
        for i in range(nr):
            a, b = rings[r][i], rings[r][(i + 1) % nr]
            F.append((a, b, rings[r + 1][(i + 1) % nr], rings[r + 1][i]))
    F.append(tuple(reversed(rings[0])))
    F.append(tuple(rings[-1]))
    V = np.array(V)
    F = fix_winding(V, F, np.array([cx, cy, 0.5 * (z0 + z1)]))
    return V, F


def components(me):
    bm = bmesh.new()
    bm.from_mesh(me)
    seen, comps = set(), []
    for v in bm.verts:
        if v.index in seen:
            continue
        st, comp = [v], []
        while st:
            a = st.pop()
            if a.index in seen:
                continue
            seen.add(a.index)
            comp.append(a)
            for e in a.link_edges:
                st.append(e.other_vert(a))
        comps.append(np.array([c.co[:] for c in comp]))
    bm.free()
    return comps


def swap_uv(uv):
    return [[(b, a) for (a, b) in f] for f in uv]


def bevel_mesh(me, width, segments=1):
    """real chamfer on every edge of the (original) mesh with bmesh; returns the same datablock"""
    bm = bmesh.new()
    bm.from_mesh(me)
    try:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=width, offset_type='OFFSET', segments=segments, profile=0.5, affect='EDGES')
    except Exception as e:
        print('[wood_frame] bevel failed', e)
    bm.to_mesh(me)
    bm.free()
    return me


def box_uv_mesh(me, tile=1.0, swap=False, name='UVMap'):
    V = np.array([v.co[:] for v in me.vertices], float)
    F = [tuple(p.vertices) for p in me.polygons]
    uv = box_uv_for_faces(V, F, tile)
    if swap:
        uv = swap_uv(uv)
    from wood_geo import unmirror_uv
    uv = unmirror_uv(uv)
    for k in list(me.uv_layers.keys()):
        me.uv_layers.remove(me.uv_layers[k])
    uvl = me.uv_layers.new(name=name)
    uvl.data.foreach_set('uv', np.array([c for f in uv for c in f], dtype=np.float32).ravel())
    return me


def restore_original(stage, obj):
    snap = stage.original_mesh(obj)
    # copy the snapshot back into the object's own mesh (keeps the datablock and its materials)
    me = obj.data
    mats = [m for m in me.materials]
    tmp = snap.copy()
    me.clear_geometry()
    bm = bmesh.new()
    bm.from_mesh(tmp)
    bm.to_mesh(me)
    bm.free()
    bpy.data.meshes.remove(tmp)
    me.update()
    return me


def build_frame(ctx, seed, options, stage):
    import wood_mats as wm
    rng = np.random.default_rng(seed + 200)
    rep, coll, maps = ctx['rep'], ctx['coll'], ctx['maps_dir']
    mats = bpy.data.materials
    # ---------------- normal maps in the owned materials (UVs follow below)
    post_map = __import__('os').path.join(maps, 'post_timber_normal.png')
    stone_map = __import__('os').path.join(maps, 'footing_stone_normal.png')
    for mn in ('Dark timber', 'Beam timber', 'GARDEN timber.post'):
        m = mats.get(mn)
        if m:
            wm.add_normal_to_chain(m, post_map, 'UVMap', 0.8, (1 / 0.28, 1 / 0.56, 1.0))
    wm.darken_near_floor(mats['Dark timber'])
    for mn in ('Plinth stone', 'CT / Stone painterly surface.008', 'CT / Stone painterly surface.009'):
        m = mats.get(mn)
        if m:
            wm.add_normal_to_chain(m, stone_map, 'UVMap', 0.8, (1, 1, 1))
    # ---------------- hall posts
    o = bpy.data.objects['Hall posts']
    restore_original(stage, o)
    comps = components(o.data)
    md = MeshData()
    for ci, c in enumerate(sorted(comps, key=lambda a: (a[:, 1].min(), a[:, 0].min()))):
        mn, mx = c.min(0), c.max(0)
        cx, cy = 0.5 * (mn[0] + mx[0]), 0.5 * (mn[1] + mx[1])
        half = 0.5 * (mx[0] - mn[0])
        checks = []
        nck = int(rng.integers(2, 4))
        faces = list(rng.permutation(4))[:nck]
        for f in faces:
            za = float(rng.uniform(mn[2] + 0.15, mn[2] + 0.9))
            zb = float(min(za + rng.uniform(0.7, 1.4), mx[2] - 0.3))
            checks.append(dict(face=int(f), s=float(rng.uniform(-0.04, 0.04)), hw=0.0016, depth=float(rng.uniform(0.0025, 0.004)), za=za, zb=zb))
        V, F = post_loft(cx, cy, half, 0.014, mn[2], mx[2], checks)
        uv = box_uv_for_faces(V, F, 1.0)
        md.add_part(V, F, [0] * len(F), uv, {}, ci)
    stage.write_mesh(o.data, md, world_obj=o, sharp_deg=40)
    rep['changed'].append('Hall posts')
    # ---------------- hall beams (long boxes: chamfer, grain along the length, dark end grain)
    o = bpy.data.objects['Hall beams']
    restore_original(stage, o)
    bevel_mesh(o.data, 0.012)
    box_uv_mesh(o.data, 1.0, swap=True)
    mats_b = [mats['Beam timber'], ctx['planks3'][2]]
    sel = []
    for p in o.data.polygons:
        n = p.normal
        p.material_index = 1 if abs(n.x) > 0.85 else 0
        p.use_smooth = False
    o.data.materials.clear()
    for m in mats_b:
        o.data.materials.append(m)
    # end-grain faces must carry the plank end UVs: (y, z)
    rep['changed'].append('Hall beams')
    # ---------------- eave soffit: UV only
    o = bpy.data.objects['Eave soffit']
    restore_original(stage, o)
    box_uv_mesh(o.data, 1.0, swap=True)
    rep['changed'].append('Eave soffit')
    # ---------------- roof carrying frame (rafters): chamfer + UV
    o = bpy.data.objects['Roof carrying frame']
    restore_original(stage, o)
    bevel_mesh(o.data, 0.008)
    box_uv_mesh(o.data, 1.0, swap=False)
    rep['changed'].append('Roof carrying frame')
    # ---------------- gravel timber edge
    o = bpy.data.objects['Gravel timber edge']
    restore_original(stage, o)
    bevel_mesh(o.data, 0.008)
    box_uv_mesh(o.data, 1.0, swap=True)
    rep['changed'].append('Gravel timber edge')
    # ---------------- shoji bars: UV only
    o = bpy.data.objects['Shoji bars']
    restore_original(stage, o)
    box_uv_mesh(o.data, 1.0)
    rep['changed'].append('Shoji bars')
    # ---------------- veranda steps: finer mesh, rounded chips on the front edge, a 5 mm worn dip on the upper step
    for name, dip, nchip in (('Veranda step', 0.005, 3), ('Veranda step, lower', 0.003, 2)):
        o = bpy.data.objects[name]
        restore_original(stage, o)
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=5, use_grid_fill=True)
        co = np.array([v.co[:] for v in bm.verts])
        mw = np.array(o.matrix_world)
        wco = (np.c_[co, np.ones(len(co))] @ mw.T)[:, :3]
        ztop = wco[:, 2].max()
        ymin = wco[:, 1].min()
        xmin, xmax = wco[:, 0].min(), wco[:, 0].max()
        for vi, v in enumerate(bm.verts):
            x, y, z = wco[vi]
            if z > ztop - 0.004:
                depth = dip * math.exp(-(((x - 0.5 * (xmin + xmax)) / 0.55) ** 2 + ((y - (ymin + 0.28)) / 0.13) ** 2))
                v.co.z -= depth
        # chips: rounded notches on the front top edge (the edge that faces the garden, smallest y)
        for ci in range(nchip):
            cxp = float(rng.uniform(xmin + 0.25, xmax - 0.25))
            r = float(rng.uniform(0.04, 0.06))
            for vi, v in enumerate(bm.verts):
                x, y, z = wco[vi]
                d = math.hypot((x - cxp) / r, (y - ymin) / (r * 0.8))
                if d < 1.0 and z > ztop - 0.045:
                    k = (1 - d * d)
                    v.co.z -= 0.02 * k
                    v.co.y += 0.012 * k
        bm.to_mesh(o.data)
        bm.free()
        box_uv_mesh(o.data, 1.0)
        for p in o.data.polygons:
            p.use_smooth = True
        o.data.update()
        rep['changed'].append(name)
    rep['frame'] = dict(posts=len(comps))
