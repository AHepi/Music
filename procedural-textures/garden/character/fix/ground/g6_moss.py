"""GROUND builder, step 3: moss cushions and moss collars.
 * the six hidden moss sources 'Life / moss sources 0..5' get new soft rounded domes (round, oval, kidney, double lobe, flat, tall) with box UVs
   (1 UV unit = 0.5 m in source space) and a vertex-colour gradient: dark underside (#2a2d24) to lighter yellow-green top (#6a6a2e);
 * the four 'Astra / moss tone N' materials get a soft normal map (pillow cells) and lose the 320-cell micro bump;
 * the grouped moss bodies (static mounds) get the same colour gradient and a box UV (1 UV unit = 6 cm) so the same material fits them;
 * moss collars: low rings of small cushions at the foot of rocks, pond-edge stones on the land side, gravel rocks, the lantern base and the plinth.
"""
import math
import os
import numpy as np
import bpy
from mathutils import Vector
from g6_common import (hex_lin, lerp3, smoothstep, mesh_from_arrays, box_uv, swap_mesh, track_uv, N, link, load_image, normal_chain, unlink_input,
                       set_default, PFX, add_object, tag)
from g6_scatter import make_points_mesh

C_DARK = hex_lin('#2a2d24')
C_MID = hex_lin('#33432a')
C_LIGHT = hex_lin('#4f6130')
C_WARM = hex_lin('#586636')


def moss_dome(kind, seed, nr=6, ns=18, R=1.2, H=0.92):
    """FIX ROUND: six SOFT domes, none with a pinched crease. 0 round, 1 oval, 2 soft kidney (a shallow dent only), 3 asymmetric hump (one shoulder),
    4 low wide cushion, 5 tall small mound. The old kidney / double lobe shapes had a deep notch that repeated like a bean bag crease."""
    rng = np.random.default_rng(seed)
    p = [rng.uniform(0, 6.28) for _ in range(4)]
    a = {0: (0.02, 0.015, 0.0, 1.0, 1.0), 1: (0.17, 0.03, 0.0, 1.0, 0.92), 2: (0.09, 0.04, 0.10, 1.0, 0.96), 3: (0.20, 0.06, 0.0, 1.0, 0.98),
         4: (0.08, 0.04, 0.0, 1.10, 0.58), 5: (0.05, 0.03, 0.0, 0.88, 1.16)}[kind]
    a2, a3, kid, rs, hs = a
    verts, cols = [(0.0, 0.0, H * hs)], []
    faces = []
    rings = [i / nr for i in range(1, nr + 1)] + [1.045]
    for ri, rho in enumerate(rings):
        for j in range(ns):
            phi = 2 * math.pi * j / ns
            Rphi = R * rs * (1 + a2 * math.cos(2 * phi + p[0]) + a3 * math.cos(3 * phi + p[1]))
            if kid:
                Rphi *= 1 - kid * math.exp(-((math.atan2(math.sin(phi - p[2]), math.cos(phi - p[2]))) / 0.9) ** 2)
            lump = 1 + 0.035 * math.cos(3 * phi + p[3]) * (rho * (1 - rho) * 4) + 0.02 * math.cos(5 * phi + p[0])
            if kind == 3:
                lump *= 1 + 0.16 * math.cos(1 * phi + p[0]) * rho
            rr = min(rho, 1.0)
            z = H * hs * (1 - rr ** 2.4) ** 0.62 * lump
            if rho > 1.0:
                z = -0.07 * H
            verts.append((math.cos(phi) * Rphi * rho, math.sin(phi) * Rphi * rho, z))
    for j in range(ns):
        faces.append((0, 1 + j, 1 + (j + 1) % ns))
    for ri in range(len(rings) - 1):
        for j in range(ns):
            a0 = 1 + ri * ns + j
            a1 = 1 + ri * ns + (j + 1) % ns
            faces.append((a0, a0 + ns, a1 + ns, a1))          # counter-clockwise seen from above: normals up, like the centre fan
    verts = np.array(verts, dtype=np.float32)
    zmax = verts[:, 2].max()
    for i, v in enumerate(verts):
        t = max(v[2], 0.0) / zmax
        c = lerp3(C_DARK, C_MID, smoothstep(0.0, 0.55, t))
        c = lerp3(c, C_LIGHT, smoothstep(0.45, 1.0, t))
        rim = math.sqrt(v[0] ** 2 + v[1] ** 2) / (R * rs)
        c = lerp3(c, C_WARM, 0.35 * smoothstep(0.55, 0.85, rim) * (1 - smoothstep(0.85, 1.0, rim)) * (0.4 + 0.6 * t))
        j = rng.uniform(0.9, 1.1)
        cols.append(tuple(min(1.0, x * j) for x in c))
    return verts, faces, np.array(cols, dtype=np.float32)


def moss_pad(kind, seed, nr=5, ns=22, R=1.0, H=0.20):
    """FIX ROUND: a low, wide moss MAT with a scalloped soft edge (3 shapes). Placed between cushions, it joins them into one soft carpet: the cushions
    rise out of it. Height 20 percent of the radius, lighter top, darker rim."""
    rng = np.random.default_rng(seed + 900)
    p = [rng.uniform(0, 6.28) for _ in range(3)]
    lobes = (3, 5, 7)[kind % 3]
    amp = (0.26, 0.20, 0.16)[kind % 3]
    verts, cols, faces = [(0.0, 0.0, H)], [], []
    rings = [i / nr for i in range(1, nr + 1)] + [1.04]
    for ri, rho in enumerate(rings):
        for j in range(ns):
            phi = 2 * math.pi * j / ns
            Rphi = R * (1 + amp * math.cos(lobes * phi + p[0]) + 0.07 * math.cos((lobes + 2) * phi + p[1]))
            rr = min(rho, 1.0)
            z = H * (1 - rr ** 1.7) ** 0.75 * (1 + 0.14 * math.cos(2 * phi + p[2]) * rr)
            if rho > 1.0:
                z = -0.10 * H
            verts.append((math.cos(phi) * Rphi * rho, math.sin(phi) * Rphi * rho, z))
    for j in range(ns):
        faces.append((0, 1 + j, 1 + (j + 1) % ns))
    for ri in range(len(rings) - 1):
        for j in range(ns):
            a0 = 1 + ri * ns + j
            a1 = 1 + ri * ns + (j + 1) % ns
            faces.append((a0, a0 + ns, a1 + ns, a1))
    verts = np.array(verts, dtype=np.float32)
    for v in verts:
        t = max(v[2], 0.0) / H
        c = lerp3(C_DARK, C_MID, smoothstep(0.0, 0.5, t))
        c = lerp3(c, C_LIGHT, smoothstep(0.4, 1.0, t))
        j = rng.uniform(0.92, 1.08)
        cols.append(tuple(min(1.0, x * j) for x in c))
    return verts, faces, np.array(cols, dtype=np.float32)


def island_colours(me, zlow=None):
    """per-vertex gradient for a mesh made of separate mounds: lowest vertex of each island = dark, highest = light."""
    n = len(me.vertices)
    parent = list(range(n))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for e in me.edges:
        x, y = find(e.vertices[0]), find(e.vertices[1])
        if x != y:
            parent[x] = y
    co = np.zeros(n * 3, dtype=np.float32)
    me.vertices.foreach_get('co', co)
    co = co.reshape(-1, 3)
    roots = np.array([find(i) for i in range(n)])
    cols = np.zeros((n, 4), dtype=np.float32)
    rng = np.random.default_rng(5)
    for r in np.unique(roots):
        idx = np.where(roots == r)[0]
        z0, z1 = co[idx, 2].min(), co[idx, 2].max()
        jit = rng.uniform(0.92, 1.08)
        for i in idx:
            t = (co[i, 2] - z0) / max(z1 - z0, 0.06)
            c = lerp3(C_DARK, C_MID, smoothstep(0.0, 0.5, t))
            c = lerp3(c, C_LIGHT, smoothstep(0.4, 1.0, t))
            cols[i] = (c[0] * jit, c[1] * jit, c[2] * jit, 1.0)
    return cols


def set_corner_colour_from_vertex(me, cols, name='Col'):
    ca = me.color_attributes.get(name)
    if ca is None:
        ca = me.color_attributes.new(name, 'FLOAT_COLOR', 'POINT')
    ca.data.foreach_set('color', np.asarray(cols, dtype=np.float32).ravel())
    me.color_attributes.active_color = ca


TONES = [(1.0, 1.0, 0.93), (0.9, 1.05, 0.88), (1.08, 1.0, 0.82), (0.86, 0.98, 0.96)]


def upgrade_moss_materials(maps_dir, opts):
    img = load_image(os.path.join(maps_dir, 'moss_normal.png'), 'G6 moss_normal', non_color=True)
    out = []
    for k in range(4):
        mat = bpy.data.materials['Astra / moss tone %d' % k]
        nt = mat.node_tree
        bsdf = nt.nodes['Principled BSDF']
        unlink_input(mat, 'Principled BSDF', 'Base Color')
        unlink_input(mat, 'Principled BSDF', 'Normal')
        col = N(nt, 'ShaderNodeVertexColor', 'moss vertex colour', (-900, 300))
        col.layer_name = 'Col'
        tone = N(nt, 'ShaderNodeMix', 'moss tone', (-650, 300))
        tone.data_type = 'RGBA'
        tone.blend_type = 'MULTIPLY'
        tone.inputs[0].default_value = 1.0
        tone.inputs[7].default_value = (*TONES[k], 1.0)
        link(nt, col, 'Color', tone, 6)
        # soft patchy brightness (world space, so a 15 cm and a 50 cm cushion are patchy at the same size)
        geo = N(nt, 'ShaderNodeNewGeometry', 'moss geo', (-1100, 100))
        nz = N(nt, 'ShaderNodeTexNoise', 'moss patch', (-900, 100))
        nz.noise_dimensions = '3D'
        nz.inputs['Scale'].default_value = 11.0 + 2 * k
        nz.inputs['Detail'].default_value = 2.0
        nz.inputs['Roughness'].default_value = 0.5
        link(nt, geo, 'Position', nz, 'Vector')
        mr = N(nt, 'ShaderNodeMapRange', 'moss patch range', (-650, 100))
        mr.inputs['From Min'].default_value = 0.35
        mr.inputs['From Max'].default_value = 0.65
        mr.inputs['To Min'].default_value = 0.86
        mr.inputs['To Max'].default_value = 1.14
        link(nt, nz, 'Fac', mr, 'Value')
        comb = N(nt, 'ShaderNodeCombineXYZ', 'moss patch rgb', (-420, 100))
        for s in ('X', 'Y', 'Z'):
            link(nt, mr, 'Result', comb, s)
        patch = N(nt, 'ShaderNodeMix', 'moss patch mul', (-200, 250))
        patch.data_type = 'RGBA'
        patch.blend_type = 'MULTIPLY'
        patch.inputs[0].default_value = 1.0
        link(nt, tone, next(o for o in tone.outputs if o.enabled), patch, 6)
        link(nt, comb, 'Vector', patch, 7)
        # FIX ROUND: every cushion has its own tone (Object Info 'Random' is different for each instance): lighter and yellower, or darker and bluer
        oi = N(nt, 'ShaderNodeObjectInfo', 'moss instance info', (-420, 420))
        orng = N(nt, 'ShaderNodeMapRange', 'moss instance range', (-200, 420))
        orng.inputs['To Min'].default_value = 1.0 - opts['moss_tone']
        orng.inputs['To Max'].default_value = 1.0 + opts['moss_tone']
        link(nt, oi, 'Random', orng, 'Value')
        orb = N(nt, 'ShaderNodeMapRange', 'moss instance warm', (-200, 560))
        orb.inputs['To Min'].default_value = 1.0 - 1.25 * opts['moss_tone']
        orb.inputs['To Max'].default_value = 1.0 + 0.4 * opts['moss_tone']
        link(nt, oi, 'Random', orb, 'Value')
        ocomb = N(nt, 'ShaderNodeCombineXYZ', 'moss instance rgb', (20, 480))
        link(nt, orng, 'Result', ocomb, 'X')
        link(nt, orng, 'Result', ocomb, 'Y')
        link(nt, orb, 'Result', ocomb, 'Z')
        inst = N(nt, 'ShaderNodeMix', 'moss instance mul', (200, 300))
        inst.data_type = 'RGBA'
        inst.blend_type = 'MULTIPLY'
        inst.inputs[0].default_value = 1.0
        link(nt, next(o for o in patch.outputs if o.enabled), inst, 6)
        link(nt, ocomb, 'Vector', inst, 7)
        link(nt, next(o for o in inst.outputs if o.enabled), bsdf, 'Base Color')
        nm, mp = normal_chain(nt, 'moss', img, 'UVMap', opts['moss_strength'], (1.0, 1.0, 1.0), loc=(-1300, -300))
        link(nt, nm, 'Normal', bsdf, 'Normal')
        set_default(mat, 'Principled BSDF', 'Roughness', max(bsdf.inputs['Roughness'].default_value, 0.9))           # FIX ROUND: velvety, no gumdrop sheen
        set_default(mat, 'Principled BSDF', 'Specular IOR Level', min(bsdf.inputs['Specular IOR Level'].default_value, 0.18))
        out.append(mat.name)
    return out


DOME_W = np.array([0.30, 0.20, 0.10, 0.08, 0.16, 0.16])       # round, oval, soft kidney, hump, low cushion, tall mound


def astra_instances():
    """the cushions the original scatter makes today, read back from the evaluated scene: x, y, z, scale, rotation about z, source index."""
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ob = bpy.data.objects['Life / moss at feet and damp edges']
    rows = []
    for inst in dg.object_instances:
        par = inst.parent
        if inst.is_instance and par is not None and par.original.name == ob.name:
            m = inst.matrix_world
            t = m.translation
            sc = m.to_scale()
            rows.append((t.x, t.y, t.z, (sc.x + sc.y) / 2.0, m.to_euler().z))
    return np.array(rows, dtype=np.float64).reshape(-1, 5)


def remap_astra_moss(ctx, srcs, n_dome=6):
    """FIX ROUND (the 'bean bag' complaint): the same places as the original scatter, but
       * sizes 0.6 to 1.5 times the old one (three classes, small 40 %, normal 40 %, large 20 %), then cushions whose centre sits inside the inner 40 % of a
         bigger one are dropped (that is what made rows of identical overlapping cushions);
       * a third fewer cushions in the veranda bank (the cushions that show in the right middle of the veranda picture);
       * the pick favours round and oval domes, the shapes with a crease are rare;
       * low moss mats between touching cushions join them into one soft carpet."""
    o, world, rep = ctx['o'], ctx['world'], ctx['rep']
    rng = np.random.default_rng(o['seed'] + 41)
    rows = ctx.get('astra_rows')
    if rows is None:
        rows = astra_instances()
    rep['moss_astra_instances_read'] = int(len(rows))
    if len(rows) < 50:
        return None
    X, Y, Z, S, R = rows.T
    n0 = len(rows)
    ub = np.zeros(n0)
    vb = np.zeros(n0)
    for i in range(n0):
        u, v, d = world.view_xy('veranda', X[i], Y[i], 0.1)
        ub[i], vb[i] = u, 1.0 - v
    bank = (ub > 0.50) & (ub < 0.93) & (vb > 0.56) & (vb < 0.84)
    cls = rng.choice(3, size=n0, p=[0.40, 0.35, 0.25])
    f = np.where(cls == 0, rng.uniform(0.6, 0.8, n0), np.where(cls == 1, rng.uniform(0.9, 1.1, n0), rng.uniform(1.35, 1.75, n0)))
    S2 = np.clip(S * f, 0.04, 0.22)
    order = np.argsort(-S2)
    # the veranda bank should end up with about two thirds of what the original scatter put there: the overlap rule is tuned (bisection) to hit that
    n_bank0 = int(bank.sum())
    target = int(round(0.66 * n_bank0))

    def thin(t):
        kept = []
        kx, ky, kr = [], [], []
        for i in order:
            ok = True
            if kx:
                d = np.hypot(np.array(kx) - X[i], np.array(ky) - Y[i])
                ok = bool((d >= t * np.array(kr)).all())
            if ok:
                kept.append(i)
                kx.append(X[i]); ky.append(Y[i]); kr.append(1.1 * S2[i])
        return np.array(kept)
    lo_t, hi_t = 0.0, 0.8
    kept = thin(0.40)
    for _ in range(7):
        t = 0.5 * (lo_t + hi_t)
        kept = thin(t)
        if int(bank[kept].sum()) > target:
            lo_t = t            # too many in the bank: a stronger rule
        else:
            hi_t = t
    t_used = 0.5 * (lo_t + hi_t)
    kept = thin(t_used)
    kb = kept[bank[kept]]
    drop = set()
    if len(kb) > target:
        w = 1.0 / S2[kb]
        w = w / w.sum()
        extra = rng.choice(len(kb), size=len(kb) - target, replace=False, p=w)
        drop = set(kb[extra].tolist())
    kept = np.array([i for i in kept if i not in drop])
    kX, kY, kZ, kS, kR = X[kept], Y[kept], Z[kept], S2[kept], R[kept]
    kpick = rng.choice(n_dome, size=len(kept), p=DOME_W / DOME_W.sum())
    # big cushions are never the tall little mound, small ones are never the low wide cushion
    kpick = np.where((kS > 0.12) & (kpick == 5), 0, kpick)
    kpick = np.where((kS < 0.07) & (kpick == 4), 1, kpick)
    # ---- mats between touching cushions
    m = len(kept)
    parent = list(range(m))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for i in range(m):
        for j in range(i + 1, m):
            if math.hypot(kX[i] - kX[j], kY[i] - kY[j]) < 1.15 * 1.1 * (kS[i] + kS[j]):
                a_, b_ = find(i), find(j)
                if a_ != b_:
                    parent[a_] = b_
    groups = {}
    for i in range(m):
        groups.setdefault(find(i), []).append(i)
    px, py, pz, ps, pr, pk = [], [], [], [], [], []
    for g in groups.values():
        if len(g) < 3:
            continue
        for i in sorted(g, key=lambda q: -kS[q]):
            if rng.random() > 0.55:
                continue
            nb = sorted((q for q in g if q != i), key=lambda q: math.hypot(kX[i] - kX[q], kY[i] - kY[q]))[:1]
            if not nb:
                continue
            q = nb[0]
            wgt = kS[i] / (kS[i] + kS[q])
            x = kX[i] * wgt + kX[q] * (1 - wgt)
            y = kY[i] * wgt + kY[q] * (1 - wgt)
            gz = world.ground_z(x, y)
            if gz is None or gz < -0.02:
                continue
            sc = float(np.clip(0.90 * 1.1 * (kS[i] + kS[q]), 0.08, 0.34))
            px.append(x); py.append(y); pz.append(gz - 0.006); ps.append(sc); pr.append(rng.uniform(0, 6.28)); pk.append(n_dome + int(rng.integers(0, 3)))
    xyz = np.concatenate([np.stack([kX, kY, kZ], axis=1), np.stack([px, py, pz], axis=1).reshape(-1, 3)])
    pick = np.concatenate([kpick, np.array(pk, dtype=np.int64)]).astype(np.int32)
    scale = np.concatenate([kS, np.array(ps)]).astype(np.float32)
    rot = np.concatenate([kR, np.array(pr)]).astype(np.float32)
    nb_after = int(bank[kept].sum())
    rep['moss_remap'] = dict(overlap_rule=round(float(t_used), 3), original=int(n0), cushions_kept=int(m), mats=len(px), bank_before=n_bank0, bank_after=nb_after,
                             scale_old_min=float(S.min()), scale_old_median=float(np.median(S)), scale_new_min=float(kS.min()), scale_new_max=float(kS.max()),
                             scale_new_median=float(np.median(kS)), scale_ratio_p5_p95=float(np.percentile(kS, 95) / np.percentile(kS, 5)),
                             pick_share=[round(float((kpick == k).mean()), 3) for k in range(n_dome)])
    return xyz, pick, scale, rot


def step3(ctx):
    o, world, rep, rng = ctx['o'], ctx['world'], ctx['rep'], ctx['rng']
    opts = dict(moss_strength=0.45, moss_tone=0.16)
    opts.update(o.get('moss', {}))
    # ---- read what the original scatter makes (before anything is replaced)
    old = astra_instances()
    ctx['astra_rows'] = old
    # ---- new source domes
    stats = []
    for i in range(6):
        v, f, c = moss_dome(i, 400 + i)
        me = mesh_from_arrays(PFX + 'moss dome %d' % i, v, f, cols=c, smooth=True)
        box_uv(me, 'UVMap', 0.5)
        ob = bpy.data.objects['Life / moss sources %d' % i]
        swap_mesh(ob, me)
        stats.append(len(f))
    rep['moss_sources'] = dict(count=6, faces=stats)
    # ---- three moss mats (hidden sources, owned by this stage)
    pads = []
    for k in range(3):
        v, f, c = moss_pad(k, 500 + k)
        me = mesh_from_arrays(PFX + 'moss pad %d' % k, v, f, cols=c, smooth=True)
        box_uv(me, 'UVMap', 0.5)
        ob = add_object(PFX + 'moss pad %d' % k, me, 'growth', mats=[bpy.data.materials['Astra / moss tone %d' % (k + 1)]], hide_render=True)
        pads.append(ob)
    ctx['moss_srcs'] = [bpy.data.objects['Life / moss sources %d' % i] for i in range(6)] + pads
    # ---- the grouped moss bodies: colour gradient + UV
    gb = bpy.data.objects.get('Astra / moss grouped bodies')
    if gb is not None:
        track_uv(gb, 'UVMap')
        box_uv(gb.data, 'UVMap', 0.09, matrix=gb.matrix_world)
        if gb.data.color_attributes.get('Col') is None:
            gb['gnd_col_added'] = 1
        set_corner_colour_from_vertex(gb.data, island_colours(gb.data))
    rep['moss_materials'] = upgrade_moss_materials(o['maps_dir'], opts)
    # ---- the original scatter's cushions, varied and thinned, with mats between them
    res = remap_astra_moss(ctx, None)
    if res is not None:
        from g6_scatter import build_instancer_group
        xyz, pick, scale, rot = res
        me = make_points_mesh(PFX + 'moss points', xyz, {'g6_pick': ('INT', pick), 'g6_scale': ('FLOAT', scale), 'g6_rot': ('FLOAT', rot)})
        ng = build_instancer_group(PFX + 'moss instancer', ctx['moss_srcs'])
        ob = bpy.data.objects['Life / moss at feet and damp edges']
        swap_mesh(ob, me)
        mod = next(m for m in ob.modifiers if m.type == 'NODES')
        ob['gnd_orig_group'] = mod.node_group.name
        mod.node_group = ng
    # ---- collars
    collar_points(ctx)


def outline_points(world, name, bins=24, ground_tol=0.13):
    """points on the ground line of a rock (its footprint), as (xy list per angular bin, centre xy)."""
    cache = world.__dict__.setdefault('_ol_cache', {})
    if (name, bins, ground_tol) in cache:
        return cache[(name, bins, ground_tol)]
    res = _outline_points(world, name, bins, ground_tol)
    cache[(name, bins, ground_tol)] = res
    return res


def _outline_points(world, name, bins, ground_tol):
    co = world.feet[name]
    sel = co[(co[:, 2] < co[:, 2].min() + 1.0)]
    if len(sel) > 2500:
        sel = sel[np.random.default_rng(2).choice(len(sel), 2500, replace=False)]
    low = []
    for p in sel:
        gz, on_g = world.surface(p[0], p[1])
        if gz is not None and abs(p[2] - gz) < ground_tol:
            low.append(p)
    if len(low) < 6:
        return None, None
    low = np.array(low)
    c = low[:, :2].mean(axis=0)
    ang = np.arctan2(low[:, 1] - c[1], low[:, 0] - c[0])
    rad = np.hypot(low[:, 0] - c[0], low[:, 1] - c[1])
    out = []
    for b in range(bins):
        a0 = -math.pi + 2 * math.pi * b / bins
        m = (ang >= a0) & (ang < a0 + 2 * math.pi / bins)
        if m.any():
            k = np.argmax(rad[m])
            out.append((a0 + math.pi / bins, float(rad[m][k]), low[m][k][:2]))
    return out, c


COLLAR_NAMES = ('Rock ', 'Pond edge stone', 'Gravel rock', 'Lantern base')


def collar_points(ctx):
    """low rings of small moss cushions at rock feet. Adds to ctx['moss_extra'] and builds the object G6 ground / moss collars."""
    o, world, rep, rng = ctx['o'], ctx['world'], ctx['rep'], ctx['rng']
    extra = ctx.setdefault('moss_extra', [])
    rr = np.random.default_rng(o['seed'] + 31)
    rocks_done = []
    for name in sorted(world.feet):
        if not name.startswith(COLLAR_NAMES):
            continue
        ol, c = outline_points(world, name)
        if not ol:
            continue
        kept = 0
        phase = rr.uniform(0, 6.28)
        for bi, (ang, rad, pt) in enumerate(ol):
            if math.cos(bi * 0.95 + phase) > 0.30 or rr.random() < 0.25:          # FIX ROUND: gaps come in runs, not evenly
                continue
            for k in range(1 if rr.random() < 0.8 else 2):
                s = 0.040 + 0.14 * rr.beta(0.9, 1.9)                                   # 4 to 18 cm, mostly small, a few big
                off = 0.02 + s * 1.2 * rr.uniform(0.35, 0.8)          # a cushion's edge touches the rock
                a = ang + rr.uniform(-0.12, 0.12) + (0.0 if k == 0 else rr.uniform(-0.3, 0.3))
                x = c[0] + math.cos(a) * (rad + off)
                y = c[1] + math.sin(a) * (rad + off)
                gz, on_g = world.surface(x, y)
                if gz is None or gz < -0.01 or world.mask_at(x, y) > 0.25:
                    continue
                if not world.free(x, y, 0.04, zmin=-0.01, gravel_ok=True):
                    continue
                pk = int(rr.choice(6, p=DOME_W / DOME_W.sum()))
                if rr.random() < 0.30:
                    pk, s = 6 + int(rr.integers(0, 3)), s * 1.4                         # a low moss mat joins the cushions into one soft ring
                extra.append((x, y, gz - 0.012, pk, s, rr.uniform(0, 6.28)))
                kept += 1
        if kept >= 4:
            rocks_done.append((name, kept))
            mine = [e for e in extra[-kept:]]
            ctx.setdefault('collar_focus', {})[name] = (float(np.mean([e[0] for e in mine])), float(np.mean([e[1] for e in mine])), 0.1, float(c[0]), float(c[1]))
    # the plinth foot (long, so by line), skipping the veranda steps
    pb = world.bbox.get('Stone plinth')
    plinth_n = 0
    if pb is not None:
        y_front = float(pb[0][1])
        x0, x1 = float(pb[0][0]), float(pb[1][0])
        x = x0 + 0.2
        while x < x1 - 0.1:
            x += rr.uniform(0.35, 0.9)
            y = y_front - rr.uniform(0.08, 0.2)
            if 1.0 < x < 3.4:
                continue
            gz = world.ground_z(x, y)
            if gz is None or not world.free(x, y, 0.05, zmin=-0.01):
                continue
            extra.append((x, y, gz - 0.012, int(rr.choice(6, p=DOME_W / DOME_W.sum())), rr.uniform(0.04, 0.11), rr.uniform(0, 6.28)))
            plinth_n += 1
    # a soft moss cap on the top of one gravel rock
    cap = 0
    co = world.feet.get('Gravel rock 0')
    if co is not None:
        top = co[co[:, 2] > co[:, 2].max() - 0.06]
        cx, cy, cz = float(top[:, 0].mean()), float(top[:, 1].mean()), float(co[:, 2].max())
        extra.append((cx, cy, cz - 0.07, 4, 0.115, 1.0))
        cap = 1
    rep['moss_collars'] = dict(rocks_with_collar=len(rocks_done), rocks=[n for n, _ in rocks_done], cushions_at_rocks=int(sum(k for _, k in rocks_done)),
                               plinth_cushions=plinth_n, caps=cap)


def finalize_moss_extra(ctx):
    """one points object for every extra cushion (collars, stone edges, kerb joints) using the six moss sources."""
    extra = ctx.get('moss_extra', [])
    if not extra:
        return
    from g6_scatter import build_instancer_group
    arr = np.array(extra, dtype=np.float32)
    srcs = ctx.get('moss_srcs') or [bpy.data.objects['Life / moss sources %d' % i] for i in range(6)]
    me = make_points_mesh(PFX + 'moss collar points', arr[:, :3], {'g6_pick': ('INT', arr[:, 3].astype(np.int32)), 'g6_scale': ('FLOAT', arr[:, 4]),
                                                                   'g6_rot': ('FLOAT', arr[:, 5])})
    ng = build_instancer_group(PFX + 'moss collar instancer', srcs)
    ob = add_object(PFX + 'moss collars', me, 'growth')
    m = ob.modifiers.new('G6 ground / moss collar instancer', 'NODES')
    m.node_group = ng
    ctx['rep']['moss_extra_total'] = len(extra)
