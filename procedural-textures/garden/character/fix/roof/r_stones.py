"""Stones and lantern (steps 5 and 6 of the roof brief). Plain words:
 * each big rock and some pond-edge stones get ONE designed moss cap: a soft rounded pillow (2 to 4 cm thick, rolled edge, lighter top,
   darker rim) laid on the top-facing faces by ray casting a polar grid onto the stone,
 * 1 or 2 chips (a scooped corner, paler inside) and one clean dark crack on three rocks,
 * every stone gets box UVs, a soft stone normal map, warm-grey blotches and a darker, smoother wet band up to z -0.08,
 * the lantern gets 2 cracks on the post, 1 on the gallery, a chipped cap corner, and small moss blobs in the joints and on the cap."""
import math
import numpy as np
import bpy
import bmesh
from mathutils import Vector, Matrix
from r_common import *
import r_marks

RING_F = [0.0, 0.18, 0.36, 0.54, 0.7, 0.82, 0.9, 0.95, 0.985, 1.0]


def make_bvh(obj):
    """BVH of the object's mesh in WORLD space (built from world coordinates, so rays can be given in world space)"""
    from mathutils.bvhtree import BVHTree
    me = obj.data
    mw = obj.matrix_world
    co = np.empty(len(me.vertices) * 3, np.float64)
    me.vertices.foreach_get('co', co)
    co = co.reshape(-1, 3)
    M3 = np.array(mw.to_3x3())
    w = co @ M3.T + np.array(mw.translation)
    polys = [tuple(p.vertices) for p in me.polygons]
    return BVHTree.FromPolygons([tuple(v) for v in w], polys)


def surface_hit(bvh, x, y, z_from=6.0):
    """ray from above straight down; returns (point, normal) in world space or None"""
    loc, nrm, idx, dist = bvh.ray_cast(Vector((x, y, z_from)), Vector((0, 0, -1)), 20.0)
    if loc is None:
        return None
    return loc, nrm


def top_candidates(obj, z_min_frac=0.55):
    """top-facing polygon centres of the object (world space), weighted by area, only the upper part"""
    me = obj.data
    mw = obj.matrix_world
    pts, ws = [], []
    zs = [(mw @ v.co).z for v in me.vertices]
    zlo, zhi = min(zs), max(zs)
    for p in me.polygons:
        n = (mw.to_3x3() @ p.normal).normalized()
        if n.z < 0.8:
            continue
        c = mw @ p.center
        if c.z < zlo + (zhi - zlo) * z_min_frac:
            continue
        pts.append(c)
        ws.append(p.area)
    return pts, ws


def visibility_score(obj, cams, pts, ws, n_samples=40, rng=None):
    sc = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    rng = rng or np.random.default_rng(1)
    if not pts:
        return 0.0
    idx = rng.choice(len(pts), min(n_samples, len(pts)), replace=False)
    score = 0.0
    for cam in cams:
        cp = cam.matrix_world.translation
        for i in idx:
            q = pts[i] + Vector((0, 0, 0.03))
            d = q - cp
            dist = d.length
            hit = sc.ray_cast(dg, cp, d.normalized(), distance=dist - 0.03)[0]
            if not hit:
                score += ws[i] / (dist * dist)
    return score


def moss_cap_mesh(bvh, centre_xy, radius, thick, rng, name):
    """polar grid of rays; the outline follows the top-facing surface and a soft irregular shape; returns mesh or None"""
    cx, cy = centre_xy
    S = 36
    ph = rng.uniform(0, 6.28, 3)
    am = rng.uniform(0.1, 0.22, 3)
    h0 = surface_hit(bvh, cx, cy)
    if h0 is None:
        return None
    rings = []
    rmax = []
    for s in range(S):
        th = 2 * math.pi * s / S
        out = 1 + am[0] * math.sin(2 * th + ph[0]) + am[1] * math.sin(3 * th + ph[1]) + am[2] * math.sin(5 * th + ph[2])
        R = radius * out
        last_ok = 0.0
        r = 0.02
        while r <= R:
            h = surface_hit(bvh, cx + r * math.cos(th), cy + r * math.sin(th))
            if h is None or h[1].z < 0.6 or abs(h[0].z - h0[0].z) > 0.12 + 0.35 * r:
                break
            last_ok = r
            r += 0.02
        rmax.append(max(min(last_ok, R), 0.035))
    verts = []
    rim = []
    noise_ph = rng.uniform(0, 6.28, 4)
    centre = h0[0]
    verts.append(centre + Vector((0, 0, thick * 1.05)))
    rim.append(0.0)
    for k in range(1, len(RING_F)):
        f = RING_F[k]
        for s in range(S):
            th = 2 * math.pi * s / S
            r = rmax[s] * f
            h = surface_hit(bvh, cx + r * math.cos(th), cy + r * math.sin(th))
            p, n = (h if h is not None else (centre + Vector((r * math.cos(th), r * math.sin(th), 0)), Vector((0, 0, 1))))
            n = (n + Vector((0, 0, 1))).normalized()
            pillow = 1.0 + 0.22 * math.sin(7 * th + noise_ph[0] + 9 * f) * (1 - f) + 0.12 * math.sin(11 * f + noise_ph[1] + 3 * th)
            hgt = thick * pillow * max(1 - f ** 2.0, 0.0) ** 0.62 * (1 - 0.1 * f)
            embed = -0.004 if f >= 0.999 else 0.0
            verts.append(p + n * (hgt + embed))
            rim.append(f)
    faces = []
    for s in range(S):
        faces.append((0, 1 + s, 1 + (s + 1) % S))
    for k in range(1, len(RING_F) - 1):
        a0 = 1 + (k - 1) * S
        b0 = 1 + k * S
        for s in range(S):
            s2 = (s + 1) % S
            faces.append((a0 + s, b0 + s, b0 + s2, a0 + s2))
    me = new_mesh(name, verts, faces, smooth=True)
    a = me.attributes.new('g6_rim', 'FLOAT', 'POINT')
    a.data.foreach_set('value', np.array(rim, np.float32))
    cs = np.array([v.co.x for v in me.vertices])
    ctr = Vector((cx, cy, 0))
    set_uv(me, 'UVMap', lambda co, n: ((co.x - cx) / 0.6 + 0.5, (co.y - cy) / 0.6 + 0.5))
    return me


def moss_cap_material(nrm_img, name='moss cap', dark=None, lit=None, high=None, ring='#7f8a3c', nm_strength=0.5, nm_scale=1.0, lump_scale=None, lump_dark=0.5):
    """moss material read from the vertex attribute g6_rim (0 middle, 1 edge): darker rim, lighter middle, a lighter ring just inside the edge.
    FIX ROUND: colours and normal strength can be given, so the lantern gets a darker, calmer olive than the rock caps (defaults = the rock caps)."""
    m = bpy.data.materials.new(PFX + name)
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    b = N['Principled BSDF']
    at = nnew(nt, 'ShaderNodeAttribute', 'G6 rim', attribute_type='GEOMETRY', attribute_name='g6_rim')
    rim = at.outputs['Fac']
    dark = hex_lin(dark or r_marks.MOSS_DARK)
    lit = hex_lin(lit or r_marks.MOSS_LIT)
    high = hex_lin(high or r_marks.MOSS_HIGH)
    c1 = mix_rgb(nt, smoothstep_node(nt, rim, 0.72, 0.99).outputs[0], lit, dark)           # darker rim
    c2 = mix_rgb(nt, smoothstep_node(nt, rim, 0.5, 0.0).outputs[0], mix_out(c1), high)     # lighter middle, a little yellow
    # lighter top edge of the pillow: just inside the rim
    ring_m = math_node(nt, 'MULTIPLY', smoothstep_node(nt, rim, 0.45, 0.68).outputs[0], smoothstep_node(nt, rim, 0.9, 0.72).outputs[0])
    c3 = mix_rgb(nt, math_node(nt, 'MULTIPLY', ring_m.outputs[0], 0.55).outputs[0], mix_out(c2), hex_lin(ring))
    col_out = mix_out(c3)
    if lump_scale:
        # FIX ROUND: round lumps in the colour too - the moss is darker in the gaps between lumps (cells of lump_scale per metre)
        geo = nnew(nt, 'ShaderNodeNewGeometry', 'G6 geo')
        vor = nnew(nt, 'ShaderNodeTexVoronoi', 'G6 lumps', voronoi_dimensions='3D', feature='F1')
        vor.inputs['Scale'].default_value = lump_scale
        vor.inputs['Randomness'].default_value = 1.0
        L.new(geo.outputs['Position'], vor.inputs['Vector'])
        gap = smoothstep_node(nt, vor.outputs['Distance'], 0.28, 0.62)
        col_out = mix_out(mix_rgb(nt, math_node(nt, 'MULTIPLY', gap.outputs[0], lump_dark).outputs[0], col_out, dark))
    L.new(col_out, b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.92
    uv = nnew(nt, 'ShaderNodeUVMap', 'G6 UV', uv_map='UVMap')
    mp = nnew(nt, 'ShaderNodeMapping', 'G6 NM mapping')
    mp.inputs['Scale'].default_value = (nm_scale, nm_scale, nm_scale)
    L.new(uv.outputs['UV'], mp.inputs['Vector'])
    tx = nnew(nt, 'ShaderNodeTexImage', 'G6 NM image')
    tx.image = nrm_img
    tx.interpolation = 'Cubic'
    tx.extension = 'REPEAT'
    L.new(mp.outputs['Vector'], tx.inputs['Vector'])
    nm = nnew(nt, 'ShaderNodeNormalMap', 'G6 NM', space='TANGENT', uv_map='UVMap')
    nm.inputs['Strength'].default_value = nm_strength
    L.new(tx.outputs['Color'], nm.inputs['Color'])
    L.new(nm.outputs['Normal'], b.inputs['Normal'])
    return m


def ribbon_mesh(name, pts, nrms, width, lift=0.003):
    """one tapering dark ribbon along 3D points that lie on a surface (normals given)"""
    verts, faces = [], []
    n = len(pts)
    for i in range(n):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, n - 1)]
        t = (b - a).normalized()
        side = t.cross(nrms[i]).normalized()
        f = i / max(n - 1, 1)
        w = width * (0.2 + 0.8 * math.sin(math.pi * min(max(f, 0.03), 0.97)) ** 0.6)
        p = pts[i] + nrms[i] * lift
        verts.append(p + side * w * 0.5)
        verts.append(p - side * w * 0.5)
    for i in range(n - 1):
        faces.append((2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1))
    return new_mesh(name, verts, faces)


def crack_on_top(bvh, rng, start_xy, length, width=0.008, name='crack'):
    """walk over the top-facing surface from start_xy in a wandering direction, ray casting down at every 4 cm"""
    pts, nrms = [], []
    x, y = start_xy
    ang = rng.uniform(0, 6.28)
    for i in range(int(length / 0.04)):
        h = surface_hit(bvh, x, y)
        if h is None or h[1].z < 0.35:
            break
        pts.append(h[0])
        nrms.append(h[1])
        ang += rng.uniform(-0.5, 0.5)
        x += math.cos(ang) * 0.04
        y += math.sin(ang) * 0.04
    if len(pts) < 5:
        return None
    return ribbon_mesh(name, pts, nrms, width)


def chip_rock(obj, rng, n_chips=1, radius=(0.04, 0.07), depth=(0.025, 0.045)):
    """scoop 1 or 2 chips out of the stone: the vertices of a small ball around an upper edge point are pushed inward with a soft falloff;
    the chipped area is marked in the vertex attribute g6_chip (paler inside, like freshly broken stone)"""
    me = obj.data
    mw = obj.matrix_world
    co = np.array([v.co[:] for v in me.vertices])
    nm = np.array([v.normal[:] for v in me.vertices])
    wz = (co[:, 2] + mw.translation.z)
    # candidates: convex-ish vertices in the upper half that face sideways or up
    top = wz > np.percentile(wz, 55)
    cand = np.where(top & (nm[:, 2] > -0.1))[0]
    chip = np.zeros(len(co), np.float32)
    for _ in range(n_chips):
        i = rng.choice(cand)
        c = co[i]
        r = rng.uniform(*radius)
        d = rng.uniform(*depth)
        dist = np.linalg.norm(co - c, axis=1)
        w = np.clip(1 - dist / r, 0, 1)
        w = w * w * (3 - 2 * w)
        dirn = nm[i] / (np.linalg.norm(nm[i]) + 1e-9)
        co -= np.outer(w * d, dirn)
        chip = np.maximum(chip, (w > 0.25).astype(np.float32) * np.clip(w * 2, 0, 1))
    me.vertices.foreach_set('co', co.ravel())
    me.update()
    a = me.attributes.new('g6_chip', 'FLOAT', 'POINT')
    a.data.foreach_set('value', chip)
    return int((chip > 0).sum())


def add_chip_colour(mat):
    """paler inside a chip (Attribute g6_chip) - after the marks, before the Principled node"""
    nt = mat.node_tree
    bsdf = [n for n in nt.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled'][0]
    if not bsdf.inputs['Base Color'].links:
        return
    src = bsdf.inputs['Base Color'].links[0].from_socket
    at = nnew(nt, 'ShaderNodeAttribute', 'G6 chip', attribute_type='GEOMETRY', attribute_name='g6_chip')
    c = mix_rgb(nt, math_node(nt, 'MULTIPLY', at.outputs['Fac'], 0.8).outputs[0], src, hex_lin('#a89a86'))
    nt.links.new(mix_out(c), bsdf.inputs['Base Color'])


def give_stone_uv_and_mesh(obj, tile=1.0):
    """own copy of the mesh with a box UV map (1 UV unit = tile metres); the original mesh is kept and remembered"""
    import json
    if 'g6_orig' not in obj.keys():
        obj['g6_orig'] = json.dumps({'mesh': obj.data.name, 'mats': [m.name if m else None for m in obj.data.materials]})
        obj.data.use_fake_user = True
    me = obj.data.copy()
    me.name = PFX + obj.name
    obj.data = me
    mw = obj.matrix_world
    off = ((obj.location.x * 0.37) % 1.0, (obj.location.y * 0.53) % 1.0)
    fn = box_uv_fn(tile, off=off, world=mw, inside_out=signed_volume(me) < 0)
    set_uv(me, 'UVMap', fn)
    return me
