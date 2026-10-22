# What this does (plain words): "stage_fix" is the ONE FIX ROUND on the integrated garden (garden_real.blend / garden_painted.blend of the final step).
# It is applied to the already-saved combined scene (no earlier stage has to run again) and fixes what a viewer notices first, step by step:
#   sky      (painted)  rings round the sun are 8 to 10 sided unequal polygons, band warp is a straight-edged polyline (this folder's stage_light.py)
#   ground   (painted)  ground colour in unequal flat patches with STRAIGHT edges (Voronoi cells), gravel the same, rake lines get an ambient-shadow darkening so
#                       they read in every sun angle
#   pond     (both)     the white shards on the pond: the mirrored hall glow lamps (and optionally the screens) are no longer seen in glossy rays
#   toe      (both)     shadow lift at the very end of the compositor (black holes under the bridge): in + tint * L0 * T / (T + luminance)
#   pine     (real)     pine pads get thousands of short needle sprays (ragged, soft outline) and a duller darker body
#   plants   (real)     tuft tips green instead of pale, tuft shapes and sizes varied, moss dome mottling quieter, lichen discs reduced
#   maple    (painted)  fewer and bigger leaves (chunkier planes), same coverage
#   hedge    (both)     a clipped low hedge along the far edge of the ground, so the veranda view no longer shows a hard edge and a dark band
# Use (inside Blender, one of the saved scenes already open):  import stage_fix; stage_fix.apply({'look': 'real'})   # or 'painted'
#   options: look; steps (list, default all); pond_variant ('lamps+paper' (default) | 'lamps' | 'none'); toe = [T, L0, r, g, b] or None; seed
# Owns nothing new except objects named 'Fix / ...' (garden_owner = 'fix'); everything else it touches already existed and is listed in the report.
import bpy
import bmesh
import math
import os
import sys
import time
import random

import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
FINAL_STAGE = 'proc-work/garden/final/stage'
for _p in (FINAL_STAGE, HERE):
    if _p in sys.path:
        sys.path.remove(_p)
    sys.path.insert(0, _p)           # this folder first: its stage_light.py (painted sky) wins

OWNER = 'fix'
ALL_STEPS = ['sky', 'ground', 'pond', 'toe', 'pine', 'plants', 'maple', 'hedge']
LOG = []
CHANGED = []
CREATED = []

DEFAULTS = dict(look='real', steps=None, seed=7, pond_variant='lamps+paper', toe=[0.03, 0.014, 0.75, 1.0, 0.95],
                maple_keep=0.38, maple_grow=1.62, pine_density=700.0, hedge=True)


def say(text):
    LOG.append(text)
    print('[fix] ' + text, flush=True)


# ====================================================================================================== small helpers
def mesh_from_arrays(name, V, F, smooth=False, colors=None):
    """V (n,3), F (m,3) triangles; colors (m,4) per face -> corner colour attribute 'Col'."""
    V = np.asarray(V, dtype=np.float32)
    F = np.asarray(F, dtype=np.int32)
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(V))
    me.vertices.foreach_set('co', V.ravel())
    k = F.shape[1]
    me.polygons.add(len(F))
    me.loops.add(len(F) * k)
    me.loops.foreach_set('vertex_index', F.ravel())
    me.polygons.foreach_set('loop_start', np.arange(0, len(F) * k, k, dtype=np.int32))
    me.update(calc_edges=True)
    me.validate()
    me.polygons.foreach_set('use_smooth', np.full(len(F), bool(smooth)))
    if colors is not None:
        layer = me.color_attributes.new('Col', 'FLOAT_COLOR', 'CORNER')
        c = np.repeat(np.asarray(colors, dtype=np.float32), k, axis=0)
        layer.data.foreach_set('color', c.ravel())
    return me


def swap_mesh(ob, me, keep_materials=True):
    old = ob.data
    if keep_materials:
        for m in old.materials:
            me.materials.append(m)
    ob.data = me
    if old.users == 0:
        bpy.data.meshes.remove(old)


def ground_sampler():
    ob = bpy.data.objects['Astra / Courtyard receiving ground']
    dg = bpy.context.evaluated_depsgraph_get()
    bvh = BVHTree.FromObject(ob, dg)

    def z(x, y):
        hit = bvh.ray_cast(Vector((x, y, 12.0)), Vector((0, 0, -1)), 30.0)
        return hit[0].z if hit[0] is not None else None
    return z


def tag(ob, role='growth'):
    ob['garden_owner'] = OWNER
    ob['garden_role'] = role
    ob['garden_keep_materials'] = 1
    ob['fix_created'] = 1


def new_collection(name):
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(col)
    return col


# ====================================================================================================== 1 sky (painted)
def fix_sky(o):
    if o['look'] != 'painted':
        say('sky: realistic look keeps its smooth sky (nothing to do)')
        return
    import stage_light
    import importlib
    importlib.reload(stage_light)
    stage_light.build_world('painted', 'golden', o['seed'])
    CHANGED.append('World (painted sky: polygon rings, polyline band warp)')
    say('sky: painted world rebuilt: sun rings are 8-10 sided unequal polygons, band warp is a straight-edged polyline of the azimuth')


# ====================================================================================================== 2 ground (painted)
def passages_poly(S, scale, stops, stretch=(1.0, 1.0), offset=(0.0, 0.0), rand=1.0, label='flat passages (straight edges)'):
    """Colour in flat passages whose edges are STRAIGHT: Voronoi cells (random colour per cell, cut into steps of unequal share by a constant ramp)."""
    b = S.b
    px, py, pz = b.sep(S.pos)
    vec = b.comb(b.math('ADD', b.math('MULTIPLY', px, stretch[0]), offset[0]), b.math('ADD', b.math('MULTIPLY', py, stretch[1]), offset[1]), 0.0)
    vor = b.n('ShaderNodeTexVoronoi', label, voronoi_dimensions='2D', feature='F1', distance='EUCLIDEAN')
    b.put(vor.inputs['Vector'], vec)
    vor.inputs['Scale'].default_value = scale
    vor.inputs['Randomness'].default_value = rand
    cr, cg, cb = b.sep(vor.outputs['Color'])
    return b.ramp(cr, stops, 'CONSTANT', label)


def quiet_grain(S, color, scale=40.0, amount=0.035):
    b = S.b
    n = b.noise(S.pos, scale, detail=2.0)
    f = b.maprange(n, 0.35, 0.65, 1.0 - amount, 1.0 + amount)
    return b.vmath('SCALE', color, scale=f)


def build_painted_ground(mat):
    import surf_kit as K
    S = K.Surface(mat, 'ground')
    b = S.b
    # layer 1: broad passages (cells about 2 m, straight edges, six colours of unequal share)
    col = passages_poly(S, 0.62, [
        (0.00, (0.052, 0.088, 0.034)),      # deep moss green, shade side            (20 %)
        (0.20, (0.050, 0.098, 0.042)),      # cool green (was a grey-teal that read as a concrete slab)   (22 %)
        (0.42, (0.082, 0.122, 0.034)),      # olive, the main field                   (28 %)
        (0.70, (0.106, 0.098, 0.044)),      # warm ochre-brown where the sun lies     (10 %)
        (0.80, (0.112, 0.160, 0.050)),      # pale warm green, a lit passage          (12 %)
        (0.92, (0.150, 0.138, 0.062)),      # sun-bleached straw, a small passage      (8 %)
    ], stretch=(0.75, 1.0), offset=(3.1, 1.7), label='ground passages (straight edges)')
    # layer 2: smaller cells that only step the brightness a little (flat steps), so one passage is not one dead flat colour
    fine = passages_poly(S, 1.7, [
        (0.00, (0.88, 0.88, 0.88)), (0.30, (0.95, 0.95, 0.95)), (0.62, (1.03, 1.03, 1.03)), (0.88, (1.11, 1.11, 1.11)),
    ], stretch=(0.85, 1.0), offset=(7.7, 2.3), label='ground brightness steps (straight edges)')
    col = b.vmath('MULTIPLY', col, fine)
    col = quiet_grain(S, col, 14.0, 0.05)
    noise = b.noise(S.pos, 9.0, detail=2.0)
    S.finish(col, 0.95, noise, bump=(0.12, 0.02), spec=0.3)


def build_painted_gravel(mat, ao=True):
    import surf_kit as K
    S = K.Surface(mat, 'gravel')
    b = S.b
    col = passages_poly(S, 0.42, [
        (0.00, (0.43, 0.44, 0.44)),         # cool pale grey
        (0.28, (0.50, 0.48, 0.44)),         # neutral pale
        (0.55, (0.57, 0.545, 0.49)),        # warm lit pale
        (0.80, (0.45, 0.455, 0.435)),       # a cooler one
    ], stretch=(0.8, 1.0), offset=(1.3, 5.9), label='gravel passages (straight edges)')
    col = quiet_grain(S, col, 160.0, 0.03)
    # rake lines: the grooves are darkened by ambient shadow so the lines read at every sun angle (they faded out in the middle of the court)
    if ao:
        aon = b.n('ShaderNodeAmbientOcclusion', 'groove shadow', only_local=True, samples=8)
        aon.inputs['Distance'].default_value = 0.045
        f = b.maprange(aon.outputs['AO'], 0.45, 1.0, 0.50, 1.04)
        col = b.vmath('SCALE', col, scale=f)
    S.finish(col, 0.9, S.b.noise(S.pos, 180.0, detail=3.0), bump=(0.2, 0.003), spec=0.3)


def fix_ground(o):
    if o['look'] != 'painted':
        say('ground: realistic look keeps its scan ground (nothing to do)')
        return
    n = 0
    for name in ('Moss and earth', 'GARDEN ground.earth'):
        m = bpy.data.materials.get(name)
        if m is not None:
            build_painted_ground(m)
            m['garden_owner'] = 'fix'
            CHANGED.append('Material:' + name)
            n += 1
    g = bpy.data.materials.get('Raked gravel')
    if g is not None:
        build_painted_gravel(g, ao=o.get('gravel_ao', True))
        g['garden_owner'] = 'fix'
        CHANGED.append('Material:Raked gravel')
        n += 1
    say(f'ground: {n} painted materials rebuilt with straight-edged flat passages (ground 6 colours, gravel 4 pale ones, rake grooves darkened by ambient shadow)')


# ====================================================================================================== 3 pond: no white shards
def fix_pond(o):
    v = o['pond_variant']
    if v == 'none':
        say('pond: untouched')
        return
    names = [f'Hall glow {i}' for i in range(4)]
    if v == 'lamps+paper':
        names += ['Shoji paper']
    done = []
    for nm in names:
        ob = bpy.data.objects.get(nm)
        if ob is not None:
            ob.visible_glossy = False
            CHANGED.append(nm)
            done.append(nm)
    say(f"pond: glossy-ray visibility switched off for {done} (they still light the garden and are still seen directly; they are no longer mirrored in the water as white shards)")


# ====================================================================================================== 4 shadow lift
def add_toe(tree, sock, T, L0, tint):
    """Toe lift on a compositor socket: out = in + tint * L0 * T / (T + luminance(in)). Returns the new output socket. Node names start with 'fixtoe'."""
    bw = tree.nodes.new('CompositorNodeRGBToBW')
    bw.name = 'fixtoe luminance'
    tree.links.new(bw.inputs['Image'], sock)
    den = tree.nodes.new('ShaderNodeMath')
    den.name = 'fixtoe T + lum'
    den.operation = 'ADD'
    den.inputs[1].default_value = T
    tree.links.new(bw.outputs['Val'], den.inputs[0])
    wt = tree.nodes.new('ShaderNodeMath')
    wt.name = 'fixtoe T / (T + lum)'
    wt.operation = 'DIVIDE'
    wt.inputs[0].default_value = T
    tree.links.new(den.outputs[0], wt.inputs[1])
    sc_ = tree.nodes.new('ShaderNodeMix')
    sc_.name = 'fixtoe tint x lift'
    sc_.data_type = 'RGBA'
    sc_.blend_type = 'MULTIPLY'
    sc_.inputs['Factor'].default_value = 1.0
    tree.links.new(wt.outputs[0], sc_.inputs[6])
    sc_.inputs[7].default_value = (tint[0] * L0, tint[1] * L0, tint[2] * L0, 1.0)
    ad = tree.nodes.new('ShaderNodeMix')
    ad.name = 'fixtoe add'
    ad.data_type = 'RGBA'
    ad.blend_type = 'ADD'
    ad.inputs['Factor'].default_value = 1.0
    tree.links.new(sock, ad.inputs[6])
    tree.links.new(sc_.outputs[2], ad.inputs[7])
    return ad.outputs[2]


def fix_toe(o):
    toe = o['toe']
    tree = bpy.data.node_groups.get('GARDEN finish')
    if tree is None:
        say('toe: no GARDEN finish compositor group found, nothing done')
        return
    for n in [n for n in tree.nodes if n.name.startswith('fixtoe')]:
        tree.nodes.remove(n)
    out = next(n for n in tree.nodes if n.bl_idname == 'NodeGroupOutput')
    for l in list(out.inputs[0].links):
        tree.links.remove(l)
    # the last real node of the chain: the vignette group (else the glare, else the render layer)
    last = None
    for n in tree.nodes:
        if n.bl_idname == 'CompositorNodeGroup' and n.node_tree is not None and 'vignette' in n.node_tree.name.lower():
            last = n.outputs[0]
    if last is None:
        for n in tree.nodes:
            if n.bl_idname == 'CompositorNodeGlare':
                last = n.outputs['Image']
    if last is None:
        last = next(n for n in tree.nodes if n.bl_idname == 'CompositorNodeRLayers').outputs['Image']
    if toe:
        T, L0, r, g, b = toe
        last = add_toe(tree, last, T, L0, (r, g, b))
        say(f'toe: shadow lift added at the end of the compositor (T {T}, L0 {L0}, tint {r},{g},{b})')
    else:
        say('toe: lift switched off')
    tree.links.new(out.inputs[0], last)
    CHANGED.append('Compositor group GARDEN finish')


# ====================================================================================================== 5 pine (real)
def fix_pine(o):
    if o['look'] != 'real':
        say('pine: painted look keeps its chiselled pads (nothing to do)')
        return
    ob = bpy.data.objects.get('Pine pads')
    if ob is None:
        say('pine: no Pine pads object')
        return
    rng = np.random.default_rng(o['seed'] + 77)
    me = ob.data
    nv = len(me.vertices)
    co = np.empty(nv * 3, np.float32)
    me.vertices.foreach_get('co', co)
    co = co.reshape(-1, 3)
    loops = np.empty(len(me.loops), np.int32)
    me.loops.foreach_get('vertex_index', loops)
    if len(loops) != 3 * len(me.polygons):
        say('pine: pad mesh is not all triangles, nothing done')
        return
    tris = loops.reshape(-1, 3)
    # islands by union-find
    parent = np.arange(nv)

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for a, b_, c in tris:
        ra, rb, rc = find(a), find(b_), find(c)
        parent[rb] = ra
        parent[find(rc)] = find(ra)
    root = np.array([find(i) for i in range(nv)])
    sizes = np.bincount(root, minlength=nv)
    pad_roots = [r for r in np.unique(root) if sizes[r] >= 20]
    colattr = me.color_attributes.get('Col')
    cols = None
    if colattr is not None:
        cc = np.empty(len(me.loops) * 4, np.float32)
        colattr.data.foreach_get('color', cc)
        cols = cc.reshape(-1, 3, 4)[:, 0, :]
    keep_face = np.isin(root[tris[:, 0]], pad_roots)
    n_old_needles = int((~keep_face).sum())
    # rebuild: pad faces only (re-indexed), colour darkened a touch
    used = np.unique(tris[keep_face].ravel())
    remap = -np.ones(nv, np.int64)
    remap[used] = np.arange(len(used))
    V_pad = co[used]
    F_pad = remap[tris[keep_face]]
    C_pad = (cols[keep_face].copy() if cols is not None else np.tile([0.03, 0.09, 0.05, 1.0], (keep_face.sum(), 1)))
    C_pad[:, :3] *= 0.72
    tf = tris[keep_face]
    pn = np.cross(co[tf[:, 1]] - co[tf[:, 0]], co[tf[:, 2]] - co[tf[:, 0]])
    pn = pn / np.maximum(np.linalg.norm(pn, axis=1, keepdims=True), 1e-9)
    C_pad[pn[:, 2] < 0.55, :3] *= 0.55            # sloping sides and underside darker (they showed as a pale green slab edge)
    Vs, Fs, Cs = [V_pad], [F_pad], [C_pad]
    off = len(V_pad)
    needle_tris = 0
    needle_pal = np.array([[0.010, 0.040, 0.028], [0.022, 0.070, 0.040], [0.040, 0.095, 0.050], [0.030, 0.085, 0.060], [0.055, 0.105, 0.045]])
    for r in pad_roots:
        fm = np.where(root[tris[:, 0]] == r)[0]
        pv = co[tris[fm]]                                    # (k,3,3)
        nrm = np.cross(pv[:, 1] - pv[:, 0], pv[:, 2] - pv[:, 0])
        area = np.linalg.norm(nrm, axis=1) * 0.5
        nrm = nrm / np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-9)
        cen = co[np.unique(tris[fm].ravel())].mean(axis=0)
        w = area.copy()
        w[nrm[:, 2] < -0.55] = 0.0                            # no needles from the flat underside
        side = nrm[:, 2] < 0.55
        w[side] *= 1.6                                         # the rim carries more
        tot_area = float(w.sum())
        ncl = int(o['pine_density'] * tot_area)
        if ncl < 5:
            continue
        pick = rng.choice(len(fm), size=ncl, p=w / w.sum())
        u = rng.random((ncl, 2))
        flip = u.sum(axis=1) > 1
        u[flip] = 1 - u[flip]
        P = pv[pick, 0] + (pv[pick, 1] - pv[pick, 0]) * u[:, :1] + (pv[pick, 2] - pv[pick, 0]) * u[:, 1:2]
        N = nrm[pick]
        out = P - cen
        out[:, 2] = 0
        out = out / np.maximum(np.linalg.norm(out, axis=1, keepdims=True), 1e-6)
        K = 5
        Vn = np.empty((ncl, K, 3, 3), np.float32)
        for k in range(K):
            rnd = rng.normal(size=(ncl, 3))
            rnd /= np.maximum(np.linalg.norm(rnd, axis=1, keepdims=True), 1e-6)
            d = N * 0.50 + out * (0.55 + 0.4 * (N[:, 2:3] < 0.55)) + np.array([0, 0, 0.18]) + rnd * 0.62
            d[N[:, 2] < 0.55, 2] -= 0.22                       # rim needles droop a little
            d /= np.maximum(np.linalg.norm(d, axis=1, keepdims=True), 1e-6)
            ln = rng.uniform(0.075, 0.17, (ncl, 1))
            side_v = np.cross(d, np.array([0, 0, 1.0]))
            side_v /= np.maximum(np.linalg.norm(side_v, axis=1, keepdims=True), 1e-6)
            base = P - d * 0.01 + rng.normal(size=(ncl, 3)) * 0.008
            Vn[:, k, 0] = base + side_v * 0.0055
            Vn[:, k, 1] = base - side_v * 0.0055
            Vn[:, k, 2] = base + d * ln
        Vn = Vn.reshape(-1, 3)
        Fn = (np.arange(ncl * K * 3).reshape(-1, 3) + off).astype(np.int32)
        cidx = rng.integers(0, len(needle_pal), size=ncl * K)
        Cn = np.ones((ncl * K, 4), np.float32)
        Cn[:, :3] = needle_pal[cidx] * rng.uniform(0.7, 1.15, (ncl * K, 1))
        Vs.append(Vn)
        Fs.append(Fn)
        Cs.append(Cn)
        off += len(Vn)
        needle_tris += len(Fn)
        # a hanging skirt from the outer part of the underside, so the slab edge is not seen from below
        under = nrm[:, 2] < -0.55
        if under.any():
            fcen = pv.mean(axis=1)
            rad = np.linalg.norm((fcen - cen)[:, :2], axis=1)
            wu = np.where(under, area * (rad / max(rad.max(), 1e-6)) ** 3, 0.0)
            ns = int(0.45 * o['pine_density'] * wu.sum())
            if ns >= 5:
                pick = rng.choice(len(fm), size=ns, p=wu / wu.sum())
                u = rng.random((ns, 2))
                flip = u.sum(axis=1) > 1
                u[flip] = 1 - u[flip]
                P = pv[pick, 0] + (pv[pick, 1] - pv[pick, 0]) * u[:, :1] + (pv[pick, 2] - pv[pick, 0]) * u[:, 1:2]
                out = P - cen
                out[:, 2] = 0
                out = out / np.maximum(np.linalg.norm(out, axis=1, keepdims=True), 1e-6)
                Vk = np.empty((ns, K, 3, 3), np.float32)
                for k in range(K):
                    rnd = rng.normal(size=(ns, 3))
                    rnd /= np.maximum(np.linalg.norm(rnd, axis=1, keepdims=True), 1e-6)
                    d = np.array([0, 0, -0.85]) + out * 0.35 + rnd * 0.45
                    d /= np.maximum(np.linalg.norm(d, axis=1, keepdims=True), 1e-6)
                    ln = rng.uniform(0.07, 0.15, (ns, 1))
                    side_v = np.cross(d, np.array([0, 1.0, 0]))
                    side_v /= np.maximum(np.linalg.norm(side_v, axis=1, keepdims=True), 1e-6)
                    base = P + rng.normal(size=(ns, 3)) * 0.01
                    Vk[:, k, 0] = base + side_v * 0.0055
                    Vk[:, k, 1] = base - side_v * 0.0055
                    Vk[:, k, 2] = base + d * ln
                Vk = Vk.reshape(-1, 3)
                Fk = (np.arange(ns * K * 3).reshape(-1, 3) + off).astype(np.int32)
                Ck = np.ones((ns * K, 4), np.float32)
                Ck[:, :3] = needle_pal[rng.integers(0, 3, size=ns * K)] * rng.uniform(0.6, 0.95, (ns * K, 1))
                Vs.append(Vk)
                Fs.append(Fk)
                Cs.append(Ck)
                off += len(Vk)
                needle_tris += len(Fk)
    V = np.concatenate(Vs)
    F = np.concatenate(Fs)
    C = np.concatenate(Cs)
    new = mesh_from_arrays('Pine pads', V, F, smooth=False, colors=C)
    swap_mesh(ob, new)
    CHANGED.append('Pine pads')
    say(f'pine: {len(pad_roots)} pads kept (body colour x0.72), old needle fringe {n_old_needles} triangles replaced by {needle_tris} needle triangles in sprays of 5 (density {o["pine_density"]}/m2 of pad)')


# ====================================================================================================== 6 plants (real)
def tuft_arrays(variant, rng):
    """Four different tuft shapes (the first round had one recipe): blade count, width, height, lean and droop differ by variant."""
    spec = [dict(nb=8, w=0.062, hmin=0.50, hmax=0.85, lean=(0.10, 0.45), droop=0.10),
            dict(nb=13, w=0.072, hmin=0.65, hmax=1.05, lean=(0.25, 0.75), droop=0.22),
            dict(nb=10, w=0.058, hmin=0.80, hmax=1.25, lean=(0.05, 0.35), droop=0.05),
            dict(nb=7, w=0.085, hmin=0.45, hmax=0.80, lean=(0.35, 0.90), droop=0.30)][variant % 4]
    V, F = [], []
    for b in range(spec['nb']):
        a = rng.uniform(0, math.tau)
        lean = rng.uniform(*spec['lean'])
        h = rng.uniform(spec['hmin'], spec['hmax'])
        d = np.array([math.cos(a), math.sin(a)])
        side = np.array([-d[1], d[0]])
        segs = 3
        prev = None
        for s in range(segs + 1):
            t = s / segs
            c = d * (0.05 + lean * t ** 1.6 * h * 0.8)
            z = h * t - spec['droop'] * h * t ** 3
            ww = spec['w'] * (1 - t) ** 0.6 if s < segs else 0
            base = len(V)
            if s < segs:
                V.append((c[0] + side[0] * ww, c[1] + side[1] * ww, z))
                V.append((c[0] - side[0] * ww, c[1] - side[1] * ww, z))
            else:
                V.append((c[0], c[1], z))
            if prev is not None:
                pa, pb = prev
                if s < segs:
                    F.append((pa, pb, base + 1))
                    F.append((pa, base + 1, base))
                else:
                    F.append((pa, pb, base))
            prev = (base, base + 1)
    return np.array(V, dtype=np.float32), np.array(F, dtype=np.int32)


def fix_plants(o):
    if o['look'] != 'real':
        say('plants: painted look keeps its flat tufts and moss (nothing to do)')
        return
    rng = np.random.default_rng(o['seed'] + 91)
    # --- tuft material: tips green, a little less see-through glow
    m = bpy.data.materials.get('Life / tuft')
    if m is not None and m.node_tree:
        ramp = next((n for n in m.node_tree.nodes if n.bl_idname == 'ShaderNodeValToRGB'), None)
        if ramp is not None and len(ramp.color_ramp.elements) >= 3:
            els = ramp.color_ramp.elements
            els[1].color = (0.052, 0.105, 0.020, 1)
            els[2].color = (0.078, 0.150, 0.026, 1)
        for n in m.node_tree.nodes:
            if n.bl_idname == 'ShaderNodeMixShader':
                n.inputs['Fac'].default_value = 0.12
        CHANGED.append('Material:Life / tuft')
    # --- four different tuft shapes (the live scatter picks them at random)
    changed = 0
    for i in range(4):
        ob = bpy.data.objects.get(f'Life / tuft sources {i}')
        if ob is None:
            continue
        V, F = tuft_arrays(i, rng)
        new = mesh_from_arrays(f'Life / tuft sources {i}', V, F, smooth=False)
        swap_mesh(ob, new)
        changed += 1
    # --- sizes and tilt: the records carry scale and rotation per tuft
    host = bpy.data.objects.get('Life / tufts')
    if host is not None:
        me = host.data
        n = len(me.vertices)
        sa, ra = me.attributes.get('lived_scale'), me.attributes.get('lived_rotation')
        if sa is not None and ra is not None:
            s = np.empty(n * 3, np.float32)
            sa.data.foreach_get('vector', s)
            s = s.reshape(-1, 3)
            f = np.exp(rng.normal(0.0, 0.30, (n, 1)))
            f = np.clip(f, 0.62, 1.7)
            s2 = s * f * np.array([[1.0, 1.0, 1.0]]) * rng.uniform(0.9, 1.15, (n, 3))
            sa.data.foreach_set('vector', s2.astype(np.float32).ravel())
            r = np.empty(n * 3, np.float32)
            ra.data.foreach_get('vector', r)
            r = r.reshape(-1, 3)
            r[:, 0] = rng.uniform(-0.22, 0.22, n)
            r[:, 1] = rng.uniform(-0.22, 0.22, n)
            ra.data.foreach_set('vector', r.astype(np.float32).ravel())
            me.update()
            CHANGED.append('Life / tufts (records)')
    say(f'plants: tuft tips green, {changed} tuft shapes replaced by four different recipes, tuft sizes x0.62-1.7 and tilt +-0.22 rad varied')
    # --- moss domes: quieter mottling
    k = 0
    for i in range(4):
        mm = bpy.data.materials.get(f'Astra / moss tone {i}')
        if mm is None or mm.node_tree is None:
            continue
        ramp = next((n for n in mm.node_tree.nodes if n.bl_idname == 'ShaderNodeValToRGB'), None)
        if ramp is None or len(ramp.color_ramp.elements) < 2:
            continue
        e0, e1 = ramp.color_ramp.elements[0], ramp.color_ramp.elements[-1]
        a = np.array(e0.color[:3])
        b_ = np.array(e1.color[:3])
        e1.color = tuple(a + (b_ - a) * 0.40) + (1,)
        e0.position, e1.position = 0.22, 0.78
        for n in mm.node_tree.nodes:                    # larger, lazier mottling; the fine cell bump (the 'leopard spots') much weaker and finer
            if n.bl_idname == 'ShaderNodeTexNoise':
                n.inputs['Scale'].default_value = 4.5
            elif n.bl_idname == 'ShaderNodeTexVoronoi':
                n.inputs['Scale'].default_value = 320.0
            elif n.bl_idname == 'ShaderNodeBump':
                n.inputs['Strength'].default_value = 0.10
        k += 1
        CHANGED.append(mm.name)
    say(f'plants: {k} moss tones: colour difference between the two ramp ends cut to 40 percent, mottling scale 9 -> 4.5, cell bump strength 0.35 -> 0.10 and cells 140 -> 320 per object')
    # --- lichen: off on dressed stone (lantern, piers, steps, basin), a little left on natural stone
    nd = nn = 0
    for ob in bpy.data.objects:
        role = ob.get('garden_role')
        if ob.type != 'MESH' or role not in ('stone.dressed', 'stone.natural'):
            continue
        amount = 0.0 if role == 'stone.dressed' else 0.12
        for slot in ob.material_slots:
            mat = slot.material
            if mat is None or mat.node_tree is None:
                continue
            for n in mat.node_tree.nodes:
                if n.bl_idname == 'ShaderNodeGroup' and n.node_tree is not None and n.node_tree.name == 'WK WALL GROWTH':
                    s = n.inputs.get('Lichen Amount')
                    if s is not None:
                        s.default_value = amount
                        if role == 'stone.dressed':
                            nd += 1
                        else:
                            nn += 1
    # --- the lantern shrubs ('leopard-spotted cushions'): finer, calmer cell pattern
    sm = bpy.data.materials.get('Life / shrub')
    if sm is not None and sm.node_tree is not None:
        ramp = next((n for n in sm.node_tree.nodes if n.bl_idname == 'ShaderNodeValToRGB'), None)
        if ramp is not None and len(ramp.color_ramp.elements) >= 2:
            e0, e1 = ramp.color_ramp.elements[0], ramp.color_ramp.elements[-1]
            a = np.array(e0.color[:3])
            b_ = np.array(e1.color[:3])
            e1.color = tuple(a + (b_ - a) * 0.50) + (1,)
        for n in sm.node_tree.nodes:
            if n.bl_idname == 'ShaderNodeTexVoronoi':
                n.inputs['Scale'].default_value = 80.0
            elif n.bl_idname == 'ShaderNodeBump':
                n.inputs['Strength'].default_value = 0.25
        CHANGED.append('Material:Life / shrub')
        say('plants: shrub material (lantern shrubs and the far hedge): colour difference halved, cells 26 -> 80 per metre, bump 0.6 -> 0.25')
    say(f'plants: lichen amount 0.6 -> 0 on {nd} dressed-stone materials and -> 0.12 on {nn} natural-stone materials (moss kept)')


# ====================================================================================================== 7 maple (painted)
def fill_maple_hole(o, ob):
    """The dark eye-shaped gap in the painted canopy seen from the veranda camera (about 53 % across, 78 % up the picture): leaves are added in front of it,
    each one copying colour, kind and tilt of the nearest existing leaf, with a rank low enough to be kept by the density setting."""
    cam = bpy.data.objects.get('veranda')
    if cam is None:
        return
    sc = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    fr = [cam.matrix_world @ v for v in cam.data.view_frame(scene=sc)]       # top right, bottom right, bottom left, top left
    TR, BR, BL, TL = fr
    origin = cam.matrix_world.translation
    rng = np.random.default_rng(o['seed'] + 33)
    hits = []
    inner = bpy.data.objects.get('Maple inner mass')
    bvh = BVHTree.FromObject(inner, dg) if inner is not None else None
    me = ob.data
    n0 = len(me.vertices)
    co = np.empty(n0 * 3, np.float32)
    me.vertices.foreach_get('co', co)
    co = co.reshape(-1, 3)
    attrs = {}
    for name in ('leaf_kind', 'leaf_rot', 'leaf_scale', 'leaf_hue', 'leaf_tone', 'leaf_rank'):
        a = me.attributes[name]
        if a.data_type == 'INT':
            arr = np.empty(n0, np.int32)
            a.data.foreach_get('value', arr)
        elif a.data_type == 'FLOAT':
            arr = np.empty(n0, np.float32)
            a.data.foreach_get('value', arr)
        else:
            arr = np.empty(n0 * 3, np.float32)
            a.data.foreach_get('vector', arr)
            arr = arr.reshape(-1, 3)
        attrs[name] = arr
    # the picture position of the gap, and a few neighbours around it (the eye is long and thin)
    spots = [(0.530, 0.779), (0.552, 0.775), (0.508, 0.783), (0.575, 0.768)]
    new_pos = []
    for (u, v) in spots:
        pt = BL + (BR - BL) * u + (TL - BL) * v
        d = (pt - origin).normalized()
        hit = bvh.ray_cast(origin, d) if bvh is not None else (None,)
        if hit[0] is None:
            continue
        p = hit[0]
        hits.append(tuple(round(x, 2) for x in p))
        right = d.cross(Vector((0, 0, 1))).normalized()
        up = right.cross(d).normalized()
        for _ in range(45):
            q = p - d * rng.uniform(0.02, 0.35) + right * rng.normal(0, 0.16) + up * rng.normal(0, 0.09)
            new_pos.append(q[:])
    if not new_pos:
        say('maple: the gap was not found by the ray (nothing added)')
        return
    new_pos = np.array(new_pos, np.float32)
    nn = len(new_pos)
    d2 = ((new_pos[:, None, :] - co[None, ::7, :]) ** 2).sum(axis=2)
    near = np.argmin(d2, axis=1) * 7
    me.vertices.add(nn)
    allco = np.concatenate([co, new_pos]).astype(np.float32)
    me.vertices.foreach_set('co', allco.ravel())
    for name, arr in attrs.items():
        a = me.attributes[name]
        new = arr[near].copy()
        if name == 'leaf_rank':
            new = rng.uniform(0.0, max(0.05, o['maple_keep'] - 0.03), nn).astype(np.float32)
        full = np.concatenate([arr, new])
        if a.data_type in ('INT', 'FLOAT'):
            a.data.foreach_set('value', full.ravel())
        else:
            a.data.foreach_set('vector', full.astype(np.float32).ravel())
    me.update()
    say(f'maple: {nn} leaves added in front of the dark gap (ray hits at {hits}), copied from the nearest existing leaves')


def fix_maple(o):
    if o['look'] != 'painted':
        say('maple: realistic look keeps its fine leaves (nothing to do)')
        return
    ob = bpy.data.objects.get('Maple leaves')
    if ob is None:
        return
    me = ob.data
    n = len(me.vertices)
    sa = me.attributes.get('leaf_scale')
    s = np.empty(n * 3, np.float32)
    sa.data.foreach_get('vector', s)
    s = s.reshape(-1, 3)
    if float(s.mean()) < 0.09:          # not already grown (safe to run twice)
        s2 = s * o['maple_grow']
        sa.data.foreach_set('vector', s2.astype(np.float32).ravel())
        me.update()
    mod = next(m for m in ob.modifiers if m.type == 'NODES')
    mod.properties.inputs['Socket_2']['value'] = float(o['maple_keep'])     # Blender 5.2: node inputs live in modifier.properties.inputs[identifier]['value']
    ob.update_tag()
    CHANGED.append('Maple leaves')
    try:
        fill_maple_hole(o, ob)
    except Exception as e:
        say(f'maple: hole filling skipped ({e})')
    say(f"maple: painted leaves kept {o['maple_keep']:.0%} and grown x{o['maple_grow']} (chunkier planes, same coverage)")


# ====================================================================================================== 8 far hedge (both looks)
def fix_hedge(o):
    if not o['hedge']:
        return
    old = bpy.data.objects.get('Fix / far hedge')
    if old is not None:
        d = old.data
        bpy.data.objects.remove(old, do_unlink=True)
        if d.users == 0:
            bpy.data.meshes.remove(d)
    zf = ground_sampler()
    real = o['look'] == 'real'
    rng = np.random.default_rng(o['seed'] + 5)
    pts = []
    x_edge, y_edge = -11.0, -8.5
    # a continuous clipped hedge: along the far (west) edge, then along the south edge, about 1.3 m apart (they overlap), a metre in from the edge
    y = 8.0
    while y > y_edge + 0.8:
        pts.append((x_edge + 1.0 + rng.uniform(-0.35, 0.35), y))
        y -= rng.uniform(1.1, 1.6)
    x = x_edge + 1.4
    while x < 3.0:
        pts.append((x, y_edge + 1.0 + rng.uniform(-0.35, 0.35)))
        x += rng.uniform(1.1, 1.6)
    V, F = [], []
    off = 0
    for (x, y) in pts:
        z0 = zf(x, y)
        if z0 is None:
            continue
        w = rng.uniform(1.1, 1.7)                      # half length
        h = rng.uniform(1.0, 1.7)                      # height: tall enough to hide the dark band behind the edge from the veranda
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=3 if real else 2, radius=1.0)
        bm.verts.ensure_lookup_table()
        seed = rng.uniform(0, 100)
        for v in bm.verts:
            if real:
                jit = 0.16 * math.sin(v.co.x * 3.1 + seed) * math.cos(v.co.y * 2.7 + seed * 1.3) + 0.10 * math.sin(v.co.z * 5 + seed) + 0.05 * math.sin(v.co.x * 9 + seed * 2.1)
            else:
                jit = rng.uniform(-0.10, 0.10)
            v.co *= (1 + jit)
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -0.15], context='VERTS')
        for v in bm.verts:
            top = min(v.co.z, 0.62)                    # flatter, clipped top: a hedge, not a ball
            v.co.x *= w
            v.co.y *= w * 0.55
            v.co.z = (top + 0.15 + 0.35 * max(0.0, v.co.z - 0.62)) * h * 0.95
        bm.faces.ensure_lookup_table()
        idx = {v: i for i, v in enumerate(bm.verts)}
        Vs = np.array([tuple(v.co) for v in bm.verts]) + np.array([x, y, z0 - 0.15])
        Fs = np.array([[idx[v] for v in f.verts] for f in bm.faces if len(f.verts) == 3])
        bm.free()
        V.append(Vs)
        F.append(Fs + off)
        off += len(Vs)
    if not V:
        say('hedge: no ground found, nothing added')
        return
    V = np.concatenate(V)
    F = np.concatenate(F)
    me = mesh_from_arrays('Fix / far hedge', V, F, smooth=real)
    mat = bpy.data.materials.get('Life / shrub')
    if mat is not None and not real:
        # painted look: a lighter green copy (the shared one is nearly black in shade)
        mc = bpy.data.materials.get('Fix / hedge painted')
        if mc is None:
            mc = mat.copy()
            mc.name = 'Fix / hedge painted'
        mc['garden_owner'] = OWNER
        ramp = next((n for n in mc.node_tree.nodes if n.bl_idname == 'ShaderNodeValToRGB'), None)
        if ramp is not None:
            for e, c in zip(ramp.color_ramp.elements, [(0.048, 0.120, 0.050), (0.130, 0.260, 0.085)]):
                e.color = (c[0], c[1], c[2], 1)
        mat = mc
    if mat is not None:
        me.materials.append(mat)
    ob = bpy.data.objects.new('Fix / far hedge', me)
    new_collection('G5 fix').objects.link(ob)
    tag(ob, 'growth')
    CREATED.append(ob.name)
    say(f'hedge: {len(pts)} clipped shrubs ({len(F)} triangles) along the far west and south edges of the ground, material Life / shrub')


# ====================================================================================================== entry point
NOT_REPEATABLE = ('pine', 'plants', 'maple')
STEP_FUNCS = dict(sky=fix_sky, ground=fix_ground, pond=fix_pond, toe=fix_toe, pine=fix_pine, plants=fix_plants, maple=fix_maple, hedge=fix_hedge)


def apply(options=None):
    o = dict(DEFAULTS)
    o.update(options or {})
    if o['look'] not in ('real', 'painted'):
        raise ValueError("look must be 'real' or 'painted'")
    LOG.clear()
    CHANGED.clear()
    CREATED.clear()
    t0 = time.time()
    steps = [s for s in ALL_STEPS if (o['steps'] is None or s in o['steps'])]
    already = bpy.context.scene.get('garden_fix_applied') == o['look']
    for s in steps:
        say(f'--- step {s}')
        t = time.time()
        if already and s in NOT_REPEATABLE and not o.get('force'):
            say(f'    already applied to this scene: step {s} skipped (it multiplies colours and sizes; pass force=True to repeat it)')
            continue
        STEP_FUNCS[s](o)
        say(f'    ({time.time() - t:.1f} s)')
    bpy.context.scene['garden_fix_applied'] = o['look']
    rep = dict(look=o['look'], steps=steps, seconds=round(time.time() - t0, 1), created=sorted(CREATED), changed=sorted(set(CHANGED)), log=list(LOG))
    say(f"done in {rep['seconds']} s; created {rep['created']}; changed {len(rep['changed'])} things")
    return rep


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    print(apply({'look': argv[0] if argv else 'real'}))
