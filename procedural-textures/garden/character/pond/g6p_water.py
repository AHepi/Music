# POND BUILDER, steps 1 and 2: water, bed, pebbles, algae rim, lily pads and flowers, iris, reeds, cattails, floating leaves.
# Plain words: every piece is a designed shape in the garden's own chunky language (few big readable forms, same palette), never a photo-like layer.
import bpy
import math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
import g6p_common as C
from g6p_common import (say, REP, make_mesh, new_object, replace_mesh, tag, fresh_material, principled, hex_lin, normal_map_chain, ramp_node,
                        merge, icosphere, yaw_matrix, rot_matrix, tube, catmull, smoothstep, pond_radius, dist_to_corridor, WATER_Z)

# colours (linear RGBA) from the brief and the style note
COL_PAD_TOP = hex_lin('#7f764b')
COL_PAD_RIM = hex_lin('#4d4a2b')
COL_PETAL = hex_lin('#e8b8c0')
COL_IRIS = hex_lin('#62477d')
COL_CATTAIL = hex_lin('#5a3a28')
LEAF_STOPS = [(0.17, 0.006, 0.010), (0.42, 0.018, 0.014), (0.72, 0.055, 0.016), (0.90, 0.17, 0.026), (0.92, 0.38, 0.045)]


# ------------------------------------------------------------------------------------------------ maple leaf shape (same as the tree's leaves)
def maple_leaf_arrays(variant=0, nlobes=7):
    rng = np.random.default_rng(100 + variant * 7)
    spread = math.radians(236 if nlobes >= 7 else 190)
    angs = np.linspace(-spread / 2, spread / 2, nlobes)
    delta = angs[1] - angs[0]
    t = np.abs(angs) / (spread / 2)
    L = (1.0 - 0.40 * t ** 1.6) * (1 + rng.uniform(-0.06, 0.06, nlobes))
    seq = [(-0.32, 0.52), (-0.17, 0.78), (0.0, 1.0), (0.17, 0.78), (0.32, 0.52)]
    pts, tip = [(angs[0] - 0.5 * delta, 0.30 * L[0])], [False]
    for k in range(nlobes):
        for f, fr in seq:
            pts.append((angs[k] + (f + rng.uniform(-0.02, 0.02)) * delta, fr * L[k] * (1 + rng.uniform(-0.06, 0.06))))
            tip.append(f == 0.0)
        nxt = L[k + 1] if k + 1 < nlobes else L[k]
        pts.append((angs[k] + 0.5 * delta, 0.30 * (L[k] + nxt) / 2)); tip.append(False)
    P = np.array([(0.0, 0.0, 0.0)] + [(math.sin(a) * r, math.cos(a) * r, 0.0) for a, r in pts])
    tip = np.array([False] + tip)
    r = np.hypot(P[:, 0], P[:, 1])
    P[:, 2] = -0.16 * r ** 2 + np.where(tip, 0.035, 0.0)
    n = len(P) - 1
    F = [(0, i, i + 1) for i in range(1, n)]
    return P.astype(np.float32), np.array(F, dtype=np.int32)


def leaf_instance(variant, size, pos, yaw, tilt=(0.0, 0.0), color=(0.7, 0.05, 0.02, 1.0), z_sink=0.0):
    V, F = maple_leaf_arrays(variant)
    V = V * (size / max(1e-6, float(V[:, 0].max() - V[:, 0].min())))
    R = yaw_matrix(yaw) @ rot_matrix((1, 0, 0), tilt[0]) @ rot_matrix((0, 1, 0), tilt[1])
    V = V @ R.T + np.array(pos, dtype=np.float32)
    V[:, 2] += z_sink
    col = np.tile(np.array(color, dtype=np.float32), (len(V), 1))
    return V, F, col


# ------------------------------------------------------------------------------------------------ 1. WATER MATERIAL
WATER_RAMP = [   # (depth in metres, linear RGB): clear over the shelf, silt-green film at the rim, dark olive-teal in the middle
    (0.00, (0.46, 0.55, 0.30)), (0.03, (0.66, 0.74, 0.56)), (0.09, (0.80, 0.88, 0.78)), (0.17, (0.42, 0.52, 0.42)),
    (0.30, (0.085, 0.115, 0.100)), (0.46, (0.020, 0.030, 0.026))]


def build_water_material(opts):
    """Rebuilds material 'Pond water' (the pond builder owns it; Basin water shares it) with a normal map for the swell and the ripple rings."""
    m, nodes, links = fresh_material('Pond water')
    m.surface_render_method = 'DITHERED'
    att = nodes.new('ShaderNodeAttribute'); att.attribute_type = 'GEOMETRY'; att.attribute_name = 'depth'; att.location = (-900, 300)
    mr = nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0.0; mr.inputs['From Max'].default_value = 0.46
    mr.inputs['To Min'].default_value = 0.0; mr.inputs['To Max'].default_value = 1.0; mr.location = (-700, 300)
    links.new(att.outputs['Fac'], mr.inputs['Value'])
    stops = [(d / 0.46, (*c, 1.0)) for d, c in opts.get('water_ramp', WATER_RAMP)]
    rp = ramp_node(nodes, stops); rp.location = (-500, 300)
    links.new(mr.outputs['Result'], rp.inputs['Fac'])
    b, out = principled(nodes, links, color=(0.5, 0.5, 0.5, 1), rough=0.03, IOR=1.33, Transmission_Weight=1.0)
    b.inputs['Specular IOR Level'].default_value = 0.55
    b.inputs['Specular Tint'].default_value = opts.get('spec_tint', (0.70, 0.86, 0.78, 1.0))     # reflections lean olive-teal, not peach and not turquoise
    b.location = (150, 0); out.location = (900, 0)
    links.new(rp.outputs['Color'], b.inputs['Base Color'])
    # two normal maps (swell on UVMap, ripple rings on RippleUV), added: N = normalize(N1 + N2 - Ng)
    n1 = normal_map_chain(nodes, links, C.MAPS + '/swell_normal.png', 'UVMap', opts.get('swell_strength', 0.6), label='Swell', loc=(-1100, -300))
    n2 = normal_map_chain(nodes, links, C.MAPS + '/ripple_normal.png', 'RippleUV', opts.get('ripple_strength', 1.0), label='Ripple', loc=(-1100, -650), interpolation='Linear')
    geo = nodes.new('ShaderNodeNewGeometry'); geo.location = (-100, -500)
    add = nodes.new('ShaderNodeVectorMath'); add.operation = 'ADD'; add.location = (-150, -250)
    sub = nodes.new('ShaderNodeVectorMath'); sub.operation = 'SUBTRACT'; sub.location = (50, -250)
    nrm = nodes.new('ShaderNodeVectorMath'); nrm.operation = 'NORMALIZE'; nrm.location = (150, -250)
    links.new(n1.outputs['Normal'], add.inputs[0]); links.new(n2.outputs['Normal'], add.inputs[1])
    links.new(add.outputs['Vector'], sub.inputs[0]); links.new(geo.outputs['Normal'], sub.inputs[1])
    links.new(sub.outputs['Vector'], nrm.inputs[0])
    links.new(nrm.outputs['Vector'], b.inputs['Normal'])
    # murk: in the deep part a share of the surface is a dark olive-teal diffuse (silt in the water), so the middle reads olive-teal and not black
    murk_c = opts.get('murk_colour', (0.034, 0.050, 0.040, 1.0))
    dif = nodes.new('ShaderNodeBsdfDiffuse'); dif.inputs['Color'].default_value = murk_c; dif.inputs['Roughness'].default_value = 1.0; dif.location = (300, -150)
    mm = nodes.new('ShaderNodeMapRange'); mm.inputs['From Min'].default_value = 0.12; mm.inputs['From Max'].default_value = 0.30
    mm.inputs['To Min'].default_value = 0.0; mm.inputs['To Max'].default_value = opts.get('murk_share', 0.55); mm.clamp = True; mm.location = (-500, 100)
    links.new(att.outputs['Fac'], mm.inputs['Value'])
    mix0 = nodes.new('ShaderNodeMixShader'); mix0.location = (450, 0)
    links.new(mm.outputs['Result'], mix0.inputs['Fac'])
    links.new(b.outputs['BSDF'], mix0.inputs[1]); links.new(dif.outputs['BSDF'], mix0.inputs[2])
    # shadow rays pass through (as before)
    lp = nodes.new('ShaderNodeLightPath'); lp.location = (300, 300)
    tr = nodes.new('ShaderNodeBsdfTransparent'); tr.location = (300, 200)
    mix = nodes.new('ShaderNodeMixShader'); mix.location = (650, 0)
    links.new(lp.outputs['Is Shadow Ray'], mix.inputs['Fac'])
    links.new(mix0.outputs['Shader'], mix.inputs[1]); links.new(tr.outputs['BSDF'], mix.inputs[2])
    for l in list(out.inputs['Surface'].links):
        links.remove(l)
    links.new(mix.outputs['Shader'], out.inputs['Surface'])
    return m


def step_water(ctx):
    opts = ctx.opts
    pw = bpy.data.objects['Pond water']
    me = pw.data
    C.add_uv_by_position(me, 'UVMap', lambda P: np.stack([P[:, 0] / 3.0, P[:, 1] / 3.0], axis=1))
    C.add_uv_by_position(me, 'RippleUV', lambda P: np.stack([(P[:, 0] - C.POND_BBOX[0]) / (C.POND_BBOX[2] - C.POND_BBOX[0]),
                                                              (P[:, 1] - C.POND_BBOX[1]) / (C.POND_BBOX[3] - C.POND_BBOX[1])], axis=1))
    bw = bpy.data.objects.get('Basin water')
    if bw is not None:
        bme = bw.data
        C.add_uv_by_position(bme, 'UVMap', lambda P: np.stack([P[:, 0] / 3.0, P[:, 1] / 3.0], axis=1))
        C.add_uv_by_position(bme, 'RippleUV', lambda P: np.full((len(P), 2), 0.02, dtype=np.float32))     # a flat corner of the ripple map: no rings in the basin
    m = build_water_material(opts)
    for ob in (pw, bw):
        if ob is not None:
            tag(ob, 'water')
            if m.name not in [s.material.name for s in ob.material_slots if s.material]:
                ob.data.materials.clear(); ob.data.materials.append(m)
            REP.changed.append(ob.name)
    say('water: material "Pond water" rebuilt (clear shelf, dark olive-teal middle, swell + ripple normal maps); UV maps UVMap and RippleUV on Pond water and Basin water')


# ------------------------------------------------------------------------------------------------ bed profile helpers
class Bed:
    """Height of the thing you see on the bottom: the higher of the ground and the bed plate (after lowering). Built from numpy arrays."""

    def __init__(self, ctx, plate_V, plate_F):
        self.ground = ctx.ground
        self.plate = BVHTree.FromPolygons([tuple(v) for v in plate_V], [tuple(f) for f in plate_F])

    def z(self, x, y):
        gz = self.ground.z(x, y, default=-0.2)
        r = self.plate.ray_cast(Vector((float(x), float(y), 2.0)), Vector((0.0, 0.0, -1.0)))
        pz = r[0].z if r[0] is not None else -9.0
        return max(gz, pz)


def step_bed(ctx):
    """Plate lowered outside the bridge corridor, pebbles (instanced shapes merged into one mesh), flat stones, submerged leaves."""
    rng = np.random.default_rng(ctx.seed + 101)
    opts = ctx.opts
    bed = bpy.data.objects['Life / pond bed']
    me = bed.data
    n = len(me.vertices)
    co = np.empty(n * 3, dtype=np.float32); me.vertices.foreach_get('co', co); V = co.reshape(-1, 3).copy()
    if 'g6p_z0' not in me.attributes:
        a = me.attributes.new('g6p_z0', 'FLOAT', 'POINT')
        a.data.foreach_set('value', V[:, 2].copy())
    z0 = np.empty(n, dtype=np.float32); me.attributes['g6p_z0'].data.foreach_get('value', z0)
    gz = ctx.ground.zs(V[:, 0], V[:, 1])
    dc = np.array([dist_to_corridor(x, y) for x, y in V[:, :2]])
    w = smoothstep(1.2, 1.7, dc)
    target = np.minimum(z0, np.maximum(gz + 0.04, -0.54))
    Vn = V.copy(); Vn[:, 2] = z0 + w * (target - z0)
    me.vertices.foreach_set('co', Vn.ravel()); me.update()
    low = int((w > 0.01).sum())
    # faces of the plate, triangulated, for the height query
    F = []
    for p in me.polygons:
        vv = list(p.vertices)
        for k in range(1, len(vv) - 1):
            F.append((vv[0], vv[k], vv[k + 1]))
    F = np.array(F, dtype=np.int32)
    ctx.bed = Bed(ctx, Vn, F)
    # silt material and UVs (planar, 1 unit = 1 m)
    silt = build_silt_material(opts)
    me.materials.clear(); me.materials.append(silt)
    C.add_uv_by_position(me, 'UVMap', lambda P: np.stack([P[:, 0], P[:, 1]], axis=1))
    tag(bed, 'water')
    REP.changed.append(bed.name)
    REP.numbers['bed_plate_verts'] = n
    REP.numbers['bed_plate_verts_lowered'] = low
    REP.numbers['bed_plate_z_range'] = (round(float(Vn[:, 2].min()), 3), round(float(Vn[:, 2].max()), 3))
    REP.numbers['bed_plate_max_change_inside_corridor'] = round(float(np.abs(Vn[:, 2] - z0)[dc < 1.2].max()), 3)
    say('bed: plate lowered on %d of %d vertices (outside the 1.2 m bridge corridor), z now %.2f to %.2f' % (low, n, Vn[:, 2].min(), Vn[:, 2].max()))
    build_pebbles(ctx)
    build_bed_stones(ctx)
    build_submerged_leaves(ctx)


def build_silt_material(opts):
    m, nodes, links = fresh_material('G6 pond / silt')
    tc = nodes.new('ShaderNodeTexCoord'); tc.location = (-900, 200)
    n1 = nodes.new('ShaderNodeTexNoise'); n1.inputs['Scale'].default_value = 1.7; n1.inputs['Detail'].default_value = 2.0; n1.inputs['Roughness'].default_value = 0.5
    n1.location = (-700, 200)
    links.new(tc.outputs['Object'], n1.inputs['Vector'])
    rp = ramp_node(nodes, [(0.30, hex_lin('#2a2d24')), (0.55, hex_lin('#36331f')), (0.75, hex_lin('#423826'))]); rp.location = (-450, 200)
    links.new(n1.outputs['Fac'], rp.inputs['Fac'])
    b, out = principled(nodes, links, color=hex_lin('#36331f'), rough=0.92)
    links.new(rp.outputs['Color'], b.inputs['Base Color'])
    nm = normal_map_chain(nodes, links, C.MAPS + '/pebble_normal.png', 'UVMap', opts.get('silt_normal_strength', 0.6), label='Silt', loc=(-1100, -250))
    links.new(nm.outputs['Normal'], b.inputs['Normal'])
    b.location = (200, 0); out.location = (500, 0)
    return m


# ------------------------------------------------------------------------------------------------ pebbles, stones, leaves
PEBBLE_TINTS = ['#85787a', '#948377', '#6f6466', '#a39384', '#807c64', '#8a644f', '#625856']
PEBBLE_W = [0.28, 0.18, 0.16, 0.14, 0.10, 0.08, 0.06]


def pebble_proto(rng):
    V, F = icosphere(1)
    V = V.astype(np.float64)
    sx, sy, sz = 1.0, rng.uniform(0.70, 1.0), rng.uniform(0.46, 0.66)
    rad = 1.0 + rng.uniform(-0.12, 0.12, len(V))
    V = V * rad[:, None] * np.array([sx, sy, sz])
    V[:, 2] = np.where(V[:, 2] < -0.25 * sz, -0.25 * sz + (V[:, 2] + 0.25 * sz) * 0.4, V[:, 2])      # flat-ish bottom so it sits
    return V.astype(np.float32), F


def build_pebbles(ctx):
    rng = np.random.default_rng(ctx.seed + 102)
    opts = ctx.opts
    protos = [pebble_proto(rng) for _ in range(7)]
    target = int(opts.get('pebble_count', 760))
    attempts = int(opts.get('pebble_attempts', 9000))
    x0, y0, x1, y1 = C.POND_BBOX
    placed = []
    cell = 0.07
    grid = {}
    tries = 0
    zs = []
    cand = {'shelf': 0, 'slope': 0, 'middle': 0}
    while len(placed) < target and tries < attempts:
        tries += 1
        x, y = rng.uniform(x0 + 0.1, x1 - 0.1), rng.uniform(y0 + 0.05, y1 - 0.1)
        if pond_radius(x, y) > 0.985:
            continue
        bz = ctx.bed.z(x, y)
        if bz > -0.135 or bz < -0.60:
            continue
        d = -0.12 - bz
        cand['shelf' if d < 0.20 else ('slope' if d < 0.30 else 'middle')] += 1
        dc = dist_to_corridor(x, y)
        dens = 1.0 if d < 0.20 else float(np.interp(d, [0.20, 0.34, 0.46], [1.0, 0.05, 0.02]))
        if dc < 1.2:
            dens *= 0.55
        if rng.uniform() > dens:
            continue
        s = rng.uniform(0.020, 0.058) * (1.0 if d < 0.25 else 0.8)         # radius 2 to 5.8 cm (4 to 12 cm across)
        s = min(s, max(0.02, (-0.135 - bz) / 0.36))                          # the top stays under the water
        gi, gj = int(x / cell), int(y / cell)
        ok = True
        for di in range(-2, 3):
            for dj in range(-2, 3):
                for (px, py, ps) in grid.get((gi + di, gj + dj), ()):
                    if math.hypot(px - x, py - y) < (ps + s) * 0.92:
                        ok = False; break
                if not ok:
                    break
            if not ok:
                break
        if not ok:
            continue
        grid.setdefault((gi, gj), []).append((x, y, s))
        placed.append((x, y, s, bz, d))
    parts, nverts = [], 0
    tints = [hex_lin(h) for h in PEBBLE_TINTS]
    pw = np.array(PEBBLE_W) / np.sum(PEBBLE_W)
    for (x, y, s, bz, d) in placed:
        k = int(rng.integers(0, len(protos)))
        Vp, Fp = protos[k]
        stretch = rng.uniform(0.9, 1.35)
        Rm = yaw_matrix(rng.uniform(0, math.tau)) @ rot_matrix((1, 0, 0), rng.normal(0, 0.12)) @ rot_matrix((0, 1, 0), rng.normal(0, 0.12))
        Vq = (Vp * np.array([s * stretch, s, s])) @ Rm.T
        Vq += np.array([x, y, bz + s * 0.38 * 0.5], dtype=np.float32)
        t = np.array(tints[int(rng.choice(len(tints), p=pw))]) * rng.uniform(0.82, 1.18)
        t[3] = 1.0
        zz = (Vq[:, 2] - Vq[:, 2].min()) / max(1e-6, np.ptp(Vq[:, 2]))
        col = np.tile(t, (len(Vq), 1)) * (0.78 + 0.34 * zz)[:, None]
        col[:, 3] = 1.0
        parts.append((Vq, Fp, col))
        zs.append(Vq[:, 2].max())
    V, F, Cc = merge(parts)
    uv = C.uv_box(V, F, 1.0)
    pm = build_pebble_material(opts)
    mesh = make_mesh('Life / pond pebbles', V, F, colors=C.vcols_to_corners(Cc, F), uvs={'UVMap': uv}, smooth=True, materials=[pm])
    ob = bpy.data.objects['Life / pond pebbles']
    replace_mesh(ob, mesh)
    tag(ob, 'ground.earth')
    REP.changed.append(ob.name)
    REP.numbers['pebbles'] = len(placed)
    REP.numbers['pebble_triangles'] = len(F)
    d_all = np.array([p[4] for p in placed]); dcs = np.array([dist_to_corridor(p[0], p[1]) for p in placed])
    REP.numbers['pebbles_on_slopes_z_-0.12_to_-0.40'] = int(((d_all > 0.0) & (d_all < 0.28)).sum())
    REP.numbers['pebbles_in_middle_depth_gt_0.3'] = int((d_all > 0.3).sum())
    REP.numbers['pebble_top_z_max'] = round(float(max(zs)), 3)
    box_area = (x1 - x0 - 0.2) * (y1 - y0 - 0.15)
    for band, lo, hi in (('shelf', 0.0, 0.20), ('slope', 0.20, 0.30), ('middle', 0.30, 1.0)):
        area = cand[band] / max(1, tries) * box_area
        n_b = int(((d_all >= lo) & (d_all < hi)).sum())
        REP.numbers['pebbles_per_m2_' + band] = round(n_b / max(area, 1e-6), 1)
        REP.numbers['bed_area_m2_' + band] = round(area, 2)
    say('pebbles: %d chunky pebbles (4 to 12 cm) laid on the bed, dense on the slopes, thin in the middle (%d deeper than 0.3 m)' % (len(placed), int((d_all > 0.3).sum())))


def build_pebble_material(opts):
    m, nodes, links = fresh_material('G6 pond / pebble')
    vc = nodes.new('ShaderNodeVertexColor'); vc.layer_name = 'Col'; vc.location = (-300, 200)
    b, out = principled(nodes, links, color=hex_lin('#6e6062'), rough=0.55)
    links.new(vc.outputs['Color'], b.inputs['Base Color'])
    nm = normal_map_chain(nodes, links, C.MAPS + '/pebble_normal.png', 'UVMap', opts.get('pebble_normal_strength', 0.7), label='Pebble', loc=(-1100, -250))
    links.new(nm.outputs['Normal'], b.inputs['Normal'])
    b.location = (200, 0); out.location = (500, 0)
    return m


def flat_stone(rng, size, thick, nsides=9):
    """A flat slab: a ragged polygon, chamfered top edge, 25 to 40 cm wide, like the flat stone in sheet_pond.jpg."""
    ang = np.sort(rng.uniform(0, math.tau, nsides))
    for i in range(nsides):
        ang[i] = (i + rng.uniform(-0.25, 0.25)) * math.tau / nsides
    ex = rng.uniform(0.8, 1.0)
    rr = size * 0.5 * (1 + rng.uniform(-0.12, 0.12, nsides))
    outer = np.array([(math.cos(a) * r, math.sin(a) * r * ex) for a, r in zip(ang, rr)])
    inner = outer * 0.80
    ring = [np.c_[outer, np.full(nsides, 0.0)], np.c_[outer * 0.96, np.full(nsides, thick * 0.75)], np.c_[inner, np.full(nsides, thick)]]
    V = np.vstack(ring + [np.array([[0.0, 0.0, thick * 1.0]]), np.array([[0.0, 0.0, 0.0]])]).astype(np.float32)
    top, bot = 3 * nsides, 3 * nsides + 1
    F = []
    for k in range(nsides):
        k2 = (k + 1) % nsides
        for r in range(2):
            a, b, c, d = r * nsides + k, r * nsides + k2, (r + 1) * nsides + k2, (r + 1) * nsides + k
            F += [(a, b, c), (a, c, d)]
        F.append((2 * nsides + k, 2 * nsides + k2, top))
        F.append((bot, k2, k))
    return V, np.array(F, dtype=np.int32)


def build_bed_stones(ctx):
    rng = np.random.default_rng(ctx.seed + 103)
    cands = [(-3.15, -0.88, 0.36), (-4.55, 2.05, 0.30), (-1.75, 2.35, 0.34), (-0.95, 1.65, 0.27), (-5.0, -0.1, 0.26)]
    parts = []
    stones = []
    for (x, y, size) in cands:
        dc = dist_to_corridor(x, y)
        bz = ctx.bed.z(x, y)
        if bz > -0.16 or dc < 0.95:
            continue
        V, F = flat_stone(rng, size, rng.uniform(0.045, 0.065))
        Rm = yaw_matrix(rng.uniform(0, math.tau)) @ rot_matrix((1, 0, 0), rng.normal(0, 0.05)) @ rot_matrix((0, 1, 0), rng.normal(0, 0.05))
        V = V @ Rm.T + np.array([x, y, bz - 0.01], dtype=np.float32)
        base = np.array(hex_lin(['#8a7b6a', '#7d7064', '#8f7f6e', '#7a7468', '#86766a'][len(stones) % 5]))
        zz = (V[:, 2] - V[:, 2].min()) / max(1e-6, np.ptp(V[:, 2]))
        col = base[None, :] * (0.85 + 0.3 * zz)[:, None]; col[:, 3] = 1.0
        parts.append((V, F, col)); stones.append((x, y, size, round(dc, 2)))
    V, F, Cc = merge(parts)
    pm = bpy.data.materials['G6 pond / pebble']
    mesh = make_mesh('G6 pond / bed stones', V, F, colors=C.vcols_to_corners(Cc, F), uvs={'UVMap': C.uv_box(V, F, 1.0)}, smooth=False, materials=[pm])
    ob = new_object('G6 pond / bed stones', mesh, 'stone.natural')
    REP.created.append(ob.name)
    REP.numbers['flat_stones_under_water'] = len(stones)
    REP.numbers['flat_stone_places'] = stones
    say('bed: %d flat stones under water (25 to 40 cm)' % len(stones))


def build_submerged_leaves(ctx):
    rng = np.random.default_rng(ctx.seed + 104)
    spots = [(-3.7, -0.55), (-4.25, -0.5), (-2.9, -0.85), (-4.6, 2.15), (-1.85, 2.0), (-3.35, 2.3), (-0.85, 1.35), (-5.0, 0.4)]
    n = 0
    for i, (x, y) in enumerate(spots):
        bz = ctx.bed.z(x, y)
        if bz > -0.16:
            continue
        col = np.array([0.20, 0.045, 0.02, 1.0]) * rng.uniform(0.7, 1.3); col[3] = 1
        V, F, Cl = leaf_instance(i % 5, rng.uniform(0.06, 0.09), (x, y, bz + 0.012), rng.uniform(0, math.tau), tilt=(rng.normal(0, 0.08), rng.normal(0, 0.08)), color=tuple(col))
        mesh = make_mesh('G6 pond / submerged leaf %d' % n, V, F, colors=C.vcols_to_corners(Cl, F), smooth=False, materials=[ctx.leaf_mat])
        ob = new_object('G6 pond / submerged leaf %d' % n, mesh, 'leaf')
        REP.created.append(ob.name)
        n += 1
    REP.numbers['submerged_leaves'] = n
    say('bed: %d muted maple leaves on the bottom' % n)


# ------------------------------------------------------------------------------------------------ algae rim on the pond-edge stones
def stone_contour_rim(ob, ctx, rng):
    """Contour of the stone at the water level -> thin rolled green rim on the water side. Returns V, F, Cc or None."""
    dg = bpy.context.evaluated_depsgraph_get()
    eo = ob.evaluated_get(dg)
    me = eo.to_mesh()
    try:
        n = len(me.vertices)
        co = np.empty(n * 3, dtype=np.float32); me.vertices.foreach_get('co', co)
        P = co.reshape(-1, 3)
        mw = np.array(eo.matrix_world)
        P = P @ mw[:3, :3].T + mw[:3, 3]
        me.calc_loop_triangles()
        tri = np.empty(len(me.loop_triangles) * 3, dtype=np.int32); me.loop_triangles.foreach_get('vertices', tri)
        tri = tri.reshape(-1, 3)
    finally:
        eo.to_mesh_clear()
    z0 = WATER_Z
    zt = P[tri, 2]
    cross = (zt.min(axis=1) < z0) & (zt.max(axis=1) > z0)
    T = tri[cross]
    if len(T) == 0:
        return None
    segs, nrm = [], []
    for a, b, c in T:
        pts = []
        for i, j in ((a, b), (b, c), (c, a)):
            zi, zj = P[i, 2], P[j, 2]
            if (zi - z0) * (zj - z0) < 0:
                t = (z0 - zi) / (zj - zi)
                pts.append(P[i] + t * (P[j] - P[i]))
        if len(pts) == 2:
            nn = np.cross(P[b] - P[a], P[c] - P[a])
            h = nn[:2]
            if np.linalg.norm(h) < 1e-9 * max(1.0, np.linalg.norm(nn)) or np.linalg.norm(h) / (np.linalg.norm(nn) + 1e-12) < 0.15:
                outw = np.array(pts[0][:2]) - np.array(ob.matrix_world.translation[:2])
                nn2 = outw / (np.linalg.norm(outw) + 1e-9)
            else:
                nn2 = h / np.linalg.norm(h)
            segs.append((pts[0], pts[1])); nrm.append(nn2)
    if not segs:
        return None
    # chain segments into polylines by endpoint matching
    key = lambda p: (round(float(p[0]) * 400), round(float(p[1]) * 400))
    adj = {}
    for si, (p, q) in enumerate(segs):
        adj.setdefault(key(p), []).append((si, 0)); adj.setdefault(key(q), []).append((si, 1))
    used = [False] * len(segs)
    lines = []
    for s0 in range(len(segs)):
        if used[s0]:
            continue
        used[s0] = True
        pts = [segs[s0][0], segs[s0][1]]; nrs = [nrm[s0], nrm[s0]]
        for direction in (1, 0):
            while True:
                end = pts[-1] if direction == 1 else pts[0]
                nxt = None
                for (si, side) in adj.get(key(end), []):
                    if not used[si]:
                        nxt = (si, side); break
                if nxt is None:
                    break
                si, side = nxt; used[si] = True
                other = segs[si][1 - side]
                if direction == 1:
                    pts.append(other); nrs.append(nrm[si])
                else:
                    pts.insert(0, other); nrs.insert(0, nrm[si])
        if len(pts) >= 4:
            lines.append((np.array(pts), np.array(nrs)))
    parts = []
    width_base = ctx.rng_rim.uniform(0.030, 0.048)
    for pts, nrs in lines:
        m = len(pts)
        # smooth the outward normals along the line
        k = 3
        sm = np.array([nrs[max(0, i - k):i + k + 1].mean(axis=0) for i in range(m)])
        sm /= np.linalg.norm(sm, axis=1, keepdims=True) + 1e-9
        s_len = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
        wob = 0.70 + 0.55 * (0.5 + 0.5 * np.sin(s_len * 9.0 + rng.uniform(0, 6)) * np.sin(s_len * 3.1 + rng.uniform(0, 6)))
        w = width_base * wob
        outer_xy = pts[:, :2] + sm * w[:, None]
        gzs = np.array([ctx.ground.z(x, y, default=0.0) for x, y in outer_xy])
        inpond = np.array([pond_radius(x, y) < 1.06 for x, y in outer_xy])
        okp = (gzs < WATER_Z + 0.006) & inpond
        # runs of consecutive ok points
        i = 0
        while i < m:
            if not okp[i]:
                i += 1; continue
            j = i
            while j + 1 < m and okp[j + 1]:
                j += 1
            if j - i >= 2:
                idx = np.arange(i, j + 1)
                rows = []
                for fr, dz in ((-0.15, 0.011), (0.30, 0.0115), (0.65, 0.007), (1.00, -0.004)):
                    xy = pts[idx, :2] + sm[idx] * (w[idx] * fr)[:, None]
                    rows.append(np.c_[xy, np.full(len(idx), WATER_Z + dz)])
                # a rolled edge: the last row dips just under the surface, the first row tucks into the stone
                L = len(idx)
                V = np.vstack(rows).astype(np.float32)
                F = []
                for r in range(3):
                    for q in range(L - 1):
                        a, b, c, d = r * L + q, r * L + q + 1, (r + 1) * L + q + 1, (r + 1) * L + q
                        F += [(a, c, b), (a, d, c)]
                t = rng.uniform(0, 1, L)
                base = np.array(hex_lin('#4a5a2a')) * (1 - t)[:, None] + np.array(hex_lin('#6a6a2e')) * t[:, None]
                Cc = np.vstack([base * s for s in (0.85, 1.0, 0.9, 0.62)])
                Cc[:, 3] = 1.0
                parts.append((V, np.array(F, dtype=np.int32), Cc))
                i = j + 1
            else:
                i = j + 1
    if not parts:
        return None
    return merge(parts)


def step_rims(ctx):
    rng = np.random.default_rng(ctx.seed + 105)
    ctx.rng_rim = np.random.default_rng(ctx.seed + 106)
    mat, nodes, links = fresh_material('G6 pond / algae rim')
    vc = nodes.new('ShaderNodeVertexColor'); vc.layer_name = 'Col'; vc.location = (-300, 200)
    b, out = principled(nodes, links, color=hex_lin('#5a6430'), rough=0.72)
    links.new(vc.outputs['Color'], b.inputs['Base Color'])
    b.location = (200, 0); out.location = (500, 0)
    made, touching = [], []
    for i, nm in enumerate(C.POND_STONES):
        ob = bpy.data.objects.get(nm)
        if ob is None:
            continue
        res = stone_contour_rim(ob, ctx, rng)
        if res is None:
            continue
        V, F, Cc = res
        mesh = make_mesh('G6 pond / algae rim %d' % i, V, F, colors=C.vcols_to_corners(Cc, F), smooth=True, materials=[mat])
        o = new_object('G6 pond / algae rim %d' % i, mesh, 'growth')
        o['g6p_stone'] = nm
        REP.created.append(o.name)
        made.append((nm, len(F)))
    REP.numbers['algae_rims'] = len(made)
    REP.numbers['algae_rim_stones'] = [m[0] for m in made]
    say('algae rim: %d rims laid on pond-edge stones and rocks at the waterline (z -0.12)' % len(made))


# ------------------------------------------------------------------------------------------------ 2. PLANTS
def pad_mesh(rng, centre, radius, notch_deg, rim_lift, n_seg=22):
    """A lily pad: a disc with a 12 to 20 degree wedge cut out, slightly upturned rim, three rings, fan from the notch tip."""
    half = math.radians(notch_deg) / 2
    a0 = rng.uniform(0, math.tau)
    angs = np.linspace(half, math.tau - half, n_seg + 1) + a0
    rings = [0.0, 0.45, 0.80, 1.0]
    V = [(0.0, 0.0, 0.0)]
    for ri, rr in enumerate(rings[1:], start=1):
        for a in angs:
            ex = 1 + 0.035 * math.sin(3 * a + a0) * rr
            V.append((math.cos(a) * radius * rr * ex, math.sin(a) * radius * rr * ex, 0.0))
    V = np.array(V, dtype=np.float64)
    rho = np.hypot(V[:, 0], V[:, 1]) / radius
    V[:, 2] = rim_lift * rho ** 3 - 0.004 * (1 - rho)
    nr = n_seg + 1
    F = []
    for k in range(n_seg):
        F.append((0, 1 + k, 1 + k + 1))
    for r in range(2):
        for k in range(n_seg):
            a, b, c, d = 1 + r * nr + k, 1 + r * nr + k + 1, 1 + (r + 1) * nr + k + 1, 1 + (r + 1) * nr + k
            F += [(a, b, c), (a, c, d)]
    V += np.array([centre[0], centre[1], centre[2]])
    # colours: olive top, darker rim
    rho = np.hypot(V[:, 0] - centre[0], V[:, 1] - centre[1]) / radius
    base = np.array(COL_PAD_TOP) * rng.uniform(0.86, 1.12)
    rim = np.array(COL_PAD_RIM) * rng.uniform(0.9, 1.1)
    t = np.clip((rho - 0.62) / 0.38, 0, 1)[:, None] ** 1.5
    col = base * (1 - t) + rim * t
    col[:, 3] = 1.0
    return V.astype(np.float32), np.array(F, dtype=np.int32), col.astype(np.float32), a0


def lily_layout(ctx):
    """Pad list: (x, y, radius). The 16 centres of the starting scene are kept; extra small pads overlap some of them to make clusters."""
    cents = C.LILY_CENTRES
    rng = np.random.default_rng(ctx.seed + 110)
    pads = []
    for (x, y, r) in cents:
        pads.append((x, y, float(np.clip(r * 0.88, 0.10, 0.175)), 0))
    cluster_ids = [0, 1, 7, 5, 13, 14, 3]
    for ci in cluster_ids:
        x, y, r, _ = pads[ci]
        for k in range(2 if ci in (0, 1, 7) else 1):
            ang = rng.uniform(0, math.tau)
            rr = rng.uniform(0.060, 0.11)
            d = r * 0.85 + rr * 0.55
            pads.append((x + math.cos(ang) * d, y + math.sin(ang) * d, rr, 1))
    return pads


def petal(length, width, tilt, cup, rng):
    """One chunky petal, base at the origin, pointing +X, tilted up by `tilt`. 5 vertices, 3 triangles."""
    V = np.array([(0.0, -width * 0.20, 0.0), (0.0, width * 0.20, 0.0), (length * 0.45, -width * 0.5, cup), (length * 0.45, width * 0.5, cup), (length, 0.0, cup * 0.4)], dtype=np.float64)
    F = np.array([(0, 2, 3), (0, 3, 1), (2, 4, 3)], dtype=np.int32)
    R = rot_matrix((0, 1, 0), -tilt)
    return V @ R.T, F


def lily_flower(centre, rng, scale=1.0, bud=False):
    """A water-lily flower: 8 outer petals and 6 inner petals (pink-white, deeper pink at the tips), yellow centre. Or a closed bud."""
    parts = []
    cx, cy, cz = centre
    if bud:
        sides = 6
        rings = [(0.0, 0.0), (0.014, 0.012), (0.022, 0.035), (0.015, 0.055), (0.0, 0.075)]
        V, F, Cc = [], [], []
        for ri, (r, z) in enumerate(rings):
            for k in range(sides):
                a = k * math.tau / sides
                V.append((cx + math.cos(a) * r * scale, cy + math.sin(a) * r * scale, cz + z * scale))
        V = np.array(V)
        # collapse first and last ring to points (they are rings of radius 0)
        for ri in range(len(rings) - 1):
            for k in range(sides):
                a, b, c, d = ri * sides + k, ri * sides + (k + 1) % sides, (ri + 1) * sides + (k + 1) % sides, (ri + 1) * sides + k
                F += [(a, b, c), (a, c, d)]
        F = np.array(F, dtype=np.int32)
        t = np.clip((V[:, 2] - cz) / (0.075 * scale), 0, 1)[:, None]
        col = np.array(COL_PETAL)[None, :] * (1 - t) * 0.9 + np.array([0.80, 0.34, 0.44, 1.0])[None, :] * t
        col[:, 3] = 1.0
        return V.astype(np.float32), F, col.astype(np.float32)
    for ring, (npet, length, width, tilt, rot0) in enumerate(((8, 0.052, 0.030, 0.55, 0.0), (6, 0.040, 0.026, 0.95, 0.5))):
        for k in range(npet):
            a = (k + rot0) * math.tau / npet + rng.uniform(-0.08, 0.08)
            Vp, Fp = petal(length * scale * rng.uniform(0.92, 1.08), width * scale, tilt + rng.uniform(-0.08, 0.08), 0.004 * scale, rng)
            Vp = Vp @ yaw_matrix(a).T + np.array([cx, cy, cz + 0.004 * ring])
            # colour: white-pink at the base, pink at the tip
            tt = np.clip(np.hypot(Vp[:, 0] - cx, Vp[:, 1] - cy) / (length * scale), 0, 1)[:, None]
            col = np.array([0.93, 0.80, 0.82, 1.0])[None, :] * (1 - tt) + np.array(COL_PETAL)[None, :] * tt * 0.95 + np.array([0.0, -0.06, -0.04, 0.0])[None, :] * tt
            col[:, 3] = 1.0
            parts.append((Vp.astype(np.float32), Fp, col.astype(np.float32)))
    # yellow centre: a low cone with a rim
    ang = np.linspace(0, math.tau, 9)[:-1]
    V = np.array([(cx, cy, cz + 0.016 * scale)] + [(cx + math.cos(a) * 0.012 * scale, cy + math.sin(a) * 0.012 * scale, cz + 0.006 * scale) for a in ang])
    F = np.array([(0, 1 + k, 1 + (k + 1) % 8) for k in range(8)], dtype=np.int32)
    col = np.tile(np.array([0.90, 0.62, 0.07, 1.0]), (len(V), 1)).astype(np.float32)
    parts.append((V.astype(np.float32), F, col))
    return merge(parts)


def step_plants(ctx):
    rng = np.random.default_rng(ctx.seed + 120)
    opts = ctx.opts
    # ---- lily pads (object 'Lily pads')
    pads = lily_layout(ctx)
    parts = []
    for (x, y, r, kind) in pads:
        zc = WATER_Z + 0.006 + rng.uniform(0.0, 0.006)
        V, F, col, a0 = pad_mesh(rng, (x, y, zc), r, rng.uniform(12, 20), rng.uniform(0.010, 0.016))
        parts.append((V, F, col))
    V, F, Cc = merge(parts)
    pm, nodes, links = fresh_material('Lily pad')
    vc = nodes.new('ShaderNodeVertexColor'); vc.layer_name = 'Col'; vc.location = (-300, 100)
    b, out = principled(nodes, links, color=COL_PAD_TOP, rough=0.5)
    b.inputs['Specular IOR Level'].default_value = 0.35
    links.new(vc.outputs['Color'], b.inputs['Base Color'])
    b.location = (200, 0); out.location = (500, 0)
    mesh = make_mesh('Lily pads', V, F, colors=C.vcols_to_corners(Cc, F), smooth=False, materials=[pm])
    ob = bpy.data.objects['Lily pads']
    replace_mesh(ob, mesh)
    tag(ob, 'growth')
    REP.changed.append('Lily pads')
    REP.numbers['lily_pads'] = len(pads)
    REP.numbers['lily_pad_diameters_cm'] = (round(min(p[2] for p in pads) * 200), round(max(p[2] for p in pads) * 200))
    # ---- flowers and buds (object 'Lotus blossoms')
    f_idx = [0, 1, 13, 5]
    b_idx = [7, 3]
    parts = []
    for i in f_idx:
        x, y, r, _ = pads[i]
        parts.append(lily_flower((x + rng.uniform(-0.03, 0.03), y + rng.uniform(-0.03, 0.03), WATER_Z + 0.012), rng, scale=rng.uniform(0.95, 1.15)))
    bud_pos = []
    for i in b_idx:
        x, y, r, _ = pads[i]
        ang = rng.uniform(0, math.tau)
        pos = (x + math.cos(ang) * r * 0.55, y + math.sin(ang) * r * 0.55, WATER_Z + 0.05)
        bud_pos.append(pos)
        parts.append(lily_flower(pos, rng, scale=1.0, bud=True))
    V, F, Cc = merge(parts)
    fm, nodes, links = fresh_material('Lotus blossom')
    vc = nodes.new('ShaderNodeVertexColor'); vc.layer_name = 'Col'; vc.location = (-300, 100)
    b, out = principled(nodes, links, color=COL_PETAL, rough=0.55)
    b.inputs['Subsurface Weight'].default_value = 0.12
    links.new(vc.outputs['Color'], b.inputs['Base Color'])
    b.location = (200, 0); out.location = (500, 0)
    mesh = make_mesh('Lotus blossoms', V, F, colors=C.vcols_to_corners(Cc, F), smooth=False, materials=[fm])
    ob = bpy.data.objects['Lotus blossoms']
    replace_mesh(ob, mesh)
    tag(ob, 'growth')
    REP.changed.append('Lotus blossoms')
    REP.numbers['lily_flowers'] = len(f_idx)
    REP.numbers['lily_buds'] = len(b_idx)
    # ---- stems: from the bed to every pad and bud
    sparts = []
    stem_targets = [(p[0], p[1], WATER_Z + 0.004) for p in pads] + [(b_[0], b_[1], b_[2] - 0.02) for b_ in bud_pos]
    for (x, y, zt) in stem_targets:
        bz = ctx.bed.z(x, y)
        path = np.array([(x + rng.normal(0, 0.04), y + rng.normal(0, 0.04), bz - 0.01), (x + rng.normal(0, 0.03), y + rng.normal(0, 0.03), (bz + zt) / 2), (x, y, zt)])
        path = catmull(path, 4)
        V_, F_, U_, S_ = tube(path, np.full(len(path), 0.0055), sides=4)
        parts_c = np.tile(np.array(hex_lin('#3f4a28')), (len(V_), 1))
        sparts.append((V_, F_, parts_c.astype(np.float32)))
    V, F, Cc = merge(sparts)
    sm, nodes, links = fresh_material('Life / lily stem')
    vc = nodes.new('ShaderNodeVertexColor'); vc.layer_name = 'Col'; vc.location = (-300, 100)
    b, out = principled(nodes, links, color=hex_lin('#3f4a28'), rough=0.6)
    links.new(vc.outputs['Color'], b.inputs['Base Color'])
    b.location = (200, 0); out.location = (500, 0)
    mesh = make_mesh('Life / lily stems', V, F, colors=C.vcols_to_corners(Cc, F), smooth=True, materials=[sm])
    ob = bpy.data.objects['Life / lily stems']
    replace_mesh(ob, mesh)
    tag(ob, 'growth')
    REP.changed.append('Life / lily stems')
    say('plants: %d notched lily pads (%d to %d cm), %d flowers, %d buds, %d stems' % (len(pads), REP.numbers['lily_pad_diameters_cm'][0], REP.numbers['lily_pad_diameters_cm'][1], len(f_idx), len(b_idx), len(stem_targets)))
    build_iris(ctx)
    build_cattails_reeds(ctx)
    build_floating_leaves(ctx)


# iris clumps of the starting scene (centres found by clustering the old blades): (x, y, has_flowers)
IRIS_CLUMPS = [(-2.62, -1.02, True), (-4.30, -0.68, True), (-5.20, -0.22, False), (-5.62, 1.40, False), (-4.83, 2.28, True), (-0.97, 0.60, True), (-0.10, 1.62, False)]


def iris_blade(rng, base, height, width, bend_dir, curl):
    """One sword-shaped blade: a folded ribbon, wide at the base, pointed, curving over. 5 sections."""
    n = 6
    t = np.linspace(0, 1, n)
    d = np.array([math.cos(bend_dir), math.sin(bend_dir)])
    xy = base[None, :2] + d[None, :] * (curl * t ** 2 * height)[:, None]
    z = base[2] + height * (1 - 0.35 * curl * t ** 2) * t
    side = np.array([-d[1], d[0]])
    w = width * (1 - t ** 1.6) * 0.5
    L = np.c_[xy - side[None, :] * w[:, None], z]
    R = np.c_[xy + side[None, :] * w[:, None], z]
    M = np.c_[xy, z + 0.006 * (1 - t)]
    V = np.vstack([L, M, R])
    F = []
    for i in range(n - 1):
        F += [(i, i + 1, n + i + 1), (i, n + i + 1, n + i), (n + i, n + i + 1, 2 * n + i + 1), (n + i, 2 * n + i + 1, 2 * n + i)]
    return V.astype(np.float32), np.array(F, dtype=np.int32)


def iris_flower(centre, rng, facing):
    """Three drooping falls and three upright standards (purple), a pale signal patch on each fall. About 7 cm across."""
    cx, cy, cz = centre
    parts = []
    for k in range(3):
        a = facing + k * math.tau / 3 + rng.uniform(-0.1, 0.1)
        for (length, width, tilt, shade, sig) in ((0.040, 0.026, -0.85, 1.0, True), (0.030, 0.018, 1.15, 1.25, False)):
            ang = a if sig else a + math.tau / 6
            Vp, Fp = petal(length, width, tilt, 0.004, rng)
            Vp = Vp @ yaw_matrix(ang).T + np.array([cx, cy, cz])
            tt = np.clip(np.hypot(Vp[:, 0] - cx, Vp[:, 1] - cy) / length, 0, 1)[:, None]
            col = np.array(COL_IRIS)[None, :] * shade
            col = np.tile(col, (len(Vp), 1))
            if sig:                                                            # a small pale-yellow signal patch at the base of each fall only
                col = col + (np.array([0.80, 0.66, 0.30, 1.0]) - np.array(COL_IRIS))[None, :] * (np.clip(1 - tt * 3.4, 0, 1) ** 2 * 0.85)
            col[:, 3] = 1.0
            parts.append((Vp.astype(np.float32), Fp, col.astype(np.float32)))
    return merge(parts)


def build_iris(ctx):
    rng = np.random.default_rng(ctx.seed + 130)
    bparts, fparts = [], []
    nblades, nflowers, nclump_f = 0, 0, 0
    for (x, y, has_fl) in IRIS_CLUMPS:
        gz = ctx.ground.z(x, y, default=0.0)
        base_z = min(gz, 0.1) - 0.02
        nb = int(rng.integers(6, 11))
        for _ in range(nb):
            ang = rng.uniform(0, math.tau); rr = rng.uniform(0, 0.10)
            b = np.array([x + math.cos(ang) * rr, y + math.sin(ang) * rr, base_z])
            V, F = iris_blade(rng, b, rng.uniform(0.28, 0.52), rng.uniform(0.022, 0.034), ang + rng.normal(0, 0.5), rng.uniform(0.0, 0.35))
            bparts.append((V, F, None)); nblades += 1
        if has_fl:
            nclump_f += 1
            for _ in range(int(rng.integers(3, 6))):
                ang = rng.uniform(0, math.tau); rr = rng.uniform(0.0, 0.09)
                top = np.array([x + math.cos(ang) * rr * 1.4, y + math.sin(ang) * rr * 1.4, base_z + rng.uniform(0.48, 0.66)])
                path = catmull(np.array([(x + math.cos(ang) * rr * 0.3, y + math.sin(ang) * rr * 0.3, base_z), (x + math.cos(ang) * rr * 0.9, y + math.sin(ang) * rr * 0.9, base_z + 0.28), top]), 4)
                V, F, U, S = tube(path, np.linspace(0.006, 0.004, len(path)), sides=3)
                col = np.tile(np.array(hex_lin('#46582c')), (len(V), 1)).astype(np.float32)
                fparts.append((V, F, col))
                Vf, Ff, Cf = iris_flower(tuple(top + np.array([0, 0, 0.012])), rng, ang)
                fparts.append((Vf, Ff, Cf)); nflowers += 1
    V, F, _ = merge(bparts)
    ob = bpy.data.objects['Life / iris clumps']
    # keep the blade material (green ramp by height), new chunky blades
    old_mat = ob.data.materials[0] if len(ob.data.materials) else None
    mesh = make_mesh('Life / iris clumps', V, F, smooth=False, materials=[old_mat] if old_mat else [])
    replace_mesh(ob, mesh)
    tag(ob, 'growth')
    REP.changed.append('Life / iris clumps')
    V, F, Cc = merge(fparts)
    fm, nodes, links = fresh_material('G6 pond / iris flower')
    vc = nodes.new('ShaderNodeVertexColor'); vc.layer_name = 'Col'; vc.location = (-300, 100)
    b, out = principled(nodes, links, color=COL_IRIS, rough=0.6)
    links.new(vc.outputs['Color'], b.inputs['Base Color'])
    b.location = (200, 0); out.location = (500, 0)
    mesh = make_mesh('G6 pond / iris flowers', V, F, colors=C.vcols_to_corners(Cc, F), smooth=False, materials=[fm])
    o = new_object('G6 pond / iris flowers', mesh, 'growth')
    REP.created.append(o.name)
    REP.numbers['iris_clumps'] = len(IRIS_CLUMPS)
    REP.numbers['iris_clumps_with_flowers'] = nclump_f
    REP.numbers['iris_blades'] = nblades
    REP.numbers['iris_flower_stems'] = nflowers
    say('iris: %d clumps, %d blades, %d purple flowers on %d clumps' % (len(IRIS_CLUMPS), nblades, nflowers, nclump_f))


def build_cattails_reeds(ctx):
    rng = np.random.default_rng(ctx.seed + 140)
    mat, nodes, links = fresh_material('G6 pond / reed')
    vc = nodes.new('ShaderNodeVertexColor'); vc.layer_name = 'Col'; vc.location = (-300, 100)
    b, out = principled(nodes, links, color=hex_lin('#46582c'), rough=0.62)
    links.new(vc.outputs['Color'], b.inputs['Base Color'])
    b.location = (200, 0); out.location = (500, 0)
    parts = []
    clumps = [(-4.62, 2.62), (-0.95, 0.42)]
    heads = 0
    for (x, y) in clumps:
        gz = ctx.ground.z(x, y, default=0.0)
        bz = min(gz, 0.0) - 0.03
        for k in range(int(rng.integers(4, 6))):
            a = rng.uniform(0, math.tau); r = rng.uniform(0, 0.12)
            bx, by = x + math.cos(a) * r, y + math.sin(a) * r
            h = rng.uniform(0.85, 1.35)
            lean = rng.normal(0, 0.05)
            path = catmull(np.array([(bx, by, bz), (bx + lean * 0.4, by + lean * 0.3, bz + h * 0.5), (bx + lean, by + lean * 0.6, bz + h)]), 4)
            V, F, U, S = tube(path, np.linspace(0.008, 0.004, len(path)), sides=4)
            parts.append((V, F, np.tile(np.array(hex_lin('#4a5a2c')), (len(V), 1)).astype(np.float32)))
            # brown head: a chunky cylinder, 10 cm long, 2.6 cm wide, with a thin tip
            top = path[-1]
            hp = np.array([top + np.array([0, 0, -0.14]), top + np.array([0, 0, -0.01]), top + np.array([0, 0, 0.07])])
            Vh, Fh, Uh, Sh = tube(hp, np.array([0.014, 0.014, 0.003]), sides=6)
            parts.append((Vh, Fh, np.tile(np.array(COL_CATTAIL), (len(Vh), 1)).astype(np.float32) * rng.uniform(0.85, 1.1)))
            heads += 1
        for k in range(4):                                      # strap leaves
            a = rng.uniform(0, math.tau)
            V, F = iris_blade(rng, np.array([x + math.cos(a) * 0.06, y + math.sin(a) * 0.06, bz]), rng.uniform(0.7, 1.1), 0.03, a, rng.uniform(0.1, 0.5))
            parts.append((V, F, np.tile(np.array(hex_lin('#46582c')), (len(V), 1)).astype(np.float32)))
    reeds = [(-5.56, 1.30), (-0.12, 1.55), (-4.18, -0.74)]
    for (x, y) in reeds:
        gz = ctx.ground.z(x, y, default=0.0)
        bz = min(gz, 0.05) - 0.03
        for k in range(int(rng.integers(5, 8))):
            a = rng.uniform(0, math.tau); r = rng.uniform(0, 0.12)
            V, F = iris_blade(rng, np.array([x + math.cos(a) * r, y + math.sin(a) * r, bz]), rng.uniform(0.55, 1.05), rng.uniform(0.016, 0.026), a + rng.normal(0, 0.6), rng.uniform(0.1, 0.5))
            parts.append((V, F, np.tile(np.array(hex_lin('#5a6a34')), (len(V), 1)).astype(np.float32) * rng.uniform(0.8, 1.15)))
    V, F, Cc = merge(parts)
    mesh = make_mesh('G6 pond / cattails and reeds', V, F, colors=C.vcols_to_corners(Cc, F), smooth=False, materials=[mat])
    o = new_object('G6 pond / cattails and reeds', mesh, 'growth')
    REP.created.append(o.name)
    REP.numbers['cattail_clumps'] = len(clumps)
    REP.numbers['cattail_heads'] = heads
    REP.numbers['reed_clumps'] = len(reeds)
    say('reeds: %d cattail clumps (%d brown heads), %d reed clumps' % (len(clumps), heads, len(reeds)))


def build_floating_leaves(ctx):
    rng = np.random.default_rng(ctx.seed + 150)
    pts = [(-2.55, 2.45), (-3.0, 2.05), (-1.9, 2.55), (-4.1, 2.0), (-3.55, 1.1), (-2.35, -0.30), (-3.1, -0.45), (-1.65, 1.45), (-1.15, 1.75), (-4.5, 1.55), (-2.0, 2.1), (-0.75, 2.4), (-3.85, 2.7)]
    n = 0
    for i, (x, y) in enumerate(pts):
        half = i in (2, 7)
        stop = LEAF_STOPS[int(rng.integers(0, len(LEAF_STOPS)))]
        col = (stop[0], stop[1], stop[2], 1.0)
        V, F, Cl = leaf_instance(i % 5, rng.uniform(0.07, 0.11), (x, y, WATER_Z + 0.004), rng.uniform(0, math.tau), tilt=(rng.normal(0, 0.05), rng.normal(0, 0.05)), color=col,
                                 z_sink=-0.012 if half else 0.0)
        mesh = make_mesh('G6 pond / floating leaf %d' % n, V, F, colors=C.vcols_to_corners(Cl, F), smooth=False, materials=[ctx.leaf_mat])
        ob = new_object('G6 pond / floating leaf %d' % n, mesh, 'leaf')
        ob['g6p_half_submerged'] = int(half)
        REP.created.append(ob.name)
        n += 1
    REP.numbers['floating_leaves'] = n
    say('plants: %d red and orange maple leaves floating on the water (2 half under)' % n)


def leaf_material():
    m, nodes, links = fresh_material('G6 pond / floating leaf')
    vc = nodes.new('ShaderNodeVertexColor'); vc.layer_name = 'Col'; vc.location = (-300, 100)
    b, out = principled(nodes, links, color=(0.7, 0.05, 0.02, 1), rough=0.6)
    links.new(vc.outputs['Color'], b.inputs['Base Color'])
    tr = nodes.new('ShaderNodeBsdfTranslucent'); links.new(vc.outputs['Color'], tr.inputs['Color'])
    mix = nodes.new('ShaderNodeMixShader'); mix.inputs['Fac'].default_value = 0.4
    for l in list(out.inputs['Surface'].links):
        links.remove(l)
    links.new(b.outputs['BSDF'], mix.inputs[1]); links.new(tr.outputs['BSDF'], mix.inputs[2]); links.new(mix.outputs['Shader'], out.inputs['Surface'])
    m.use_backface_culling = False
    return m
