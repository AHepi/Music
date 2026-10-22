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


def moss_dome(kind, seed, nr=6, ns=16, R=1.2, H=0.92):
    rng = np.random.default_rng(seed)
    p = [rng.uniform(0, 6.28) for _ in range(4)]
    a = {0: (0.05, 0.03, 0.0, 1.0, 1.0), 1: (0.24, 0.06, 0.0, 1.0, 0.95), 2: (0.12, 0.10, 0.30, 1.0, 1.0), 3: (0.34, 0.14, 0.0, 1.0, 0.9),
         4: (0.10, 0.05, 0.0, 1.08, 0.62), 5: (0.07, 0.04, 0.0, 0.92, 1.18)}[kind]
    a2, a3, kid, rs, hs = a
    verts, cols = [(0.0, 0.0, H * hs)], []
    faces = []
    rings = [i / nr for i in range(1, nr + 1)] + [1.045]
    for ri, rho in enumerate(rings):
        for j in range(ns):
            phi = 2 * math.pi * j / ns
            Rphi = R * rs * (1 + a2 * math.cos(2 * phi + p[0]) + a3 * math.cos(3 * phi + p[1]))
            if kid:
                Rphi *= 1 - kid * math.exp(-((math.atan2(math.sin(phi - p[2]), math.cos(phi - p[2]))) / 0.7) ** 2)
            lump = 1 + 0.09 * math.cos(3 * phi + p[3]) * (rho * (1 - rho) * 4) + 0.05 * math.cos(5 * phi + p[0])
            if kind == 3:
                lump *= 1 + 0.18 * math.cos(2 * phi + p[0]) * rho
            rr = min(rho, 1.0)
            z = H * hs * (1 - rr ** 2.2) ** 0.62 * lump
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
        # a warmer, lighter rim where the dome turns over (like the concept sheet)
        rim = math.sqrt(v[0] ** 2 + v[1] ** 2) / (R * rs)
        c = lerp3(c, C_WARM, 0.35 * smoothstep(0.55, 0.85, rim) * (1 - smoothstep(0.85, 1.0, rim)) * (0.4 + 0.6 * t))
        j = rng.uniform(0.9, 1.1)
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
        link(nt, next(o for o in patch.outputs if o.enabled), bsdf, 'Base Color')
        nm, mp = normal_chain(nt, 'moss', img, 'UVMap', opts['moss_strength'], (1.0, 1.0, 1.0), loc=(-1300, -300))
        link(nt, nm, 'Normal', bsdf, 'Normal')
        out.append(mat.name)
    return out


def step3(ctx):
    o, world, rep, rng = ctx['o'], ctx['world'], ctx['rep'], ctx['rng']
    opts = dict(moss_strength=0.45)
    opts.update(o.get('moss', {}))
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
    # ---- the grouped moss bodies: colour gradient + UV
    gb = bpy.data.objects.get('Astra / moss grouped bodies')
    if gb is not None:
        track_uv(gb, 'UVMap')
        box_uv(gb.data, 'UVMap', 0.09, matrix=gb.matrix_world)
        if gb.data.color_attributes.get('Col') is None:
            gb['gnd_col_added'] = 1
        set_corner_colour_from_vertex(gb.data, island_colours(gb.data))
    rep['moss_materials'] = upgrade_moss_materials(o['maps_dir'], opts)
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
        for (ang, rad, pt) in ol:
            if rr.random() < 0.48:
                continue
            for k in range(1 if rr.random() < 0.8 else 2):
                s = rr.uniform(0.05, 0.115)
                off = 0.02 + s * 1.2 * rr.uniform(0.35, 0.8)          # a cushion's edge touches the rock
                a = ang + rr.uniform(-0.12, 0.12) + (0.0 if k == 0 else rr.uniform(-0.3, 0.3))
                x = c[0] + math.cos(a) * (rad + off)
                y = c[1] + math.sin(a) * (rad + off)
                gz, on_g = world.surface(x, y)
                if gz is None or gz < -0.01 or world.mask_at(x, y) > 0.25:
                    continue
                if not world.free(x, y, 0.04, zmin=-0.01, gravel_ok=True):
                    continue
                extra.append((x, y, gz - 0.012, int(rr.integers(0, 6)), s, rr.uniform(0, 6.28)))
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
            extra.append((x, y, gz - 0.012, int(rr.integers(0, 6)), rr.uniform(0.04, 0.085), rr.uniform(0, 6.28)))
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
    srcs = [bpy.data.objects['Life / moss sources %d' % i] for i in range(6)]
    me = make_points_mesh(PFX + 'moss collar points', arr[:, :3], {'g6_pick': ('INT', arr[:, 3].astype(np.int32)), 'g6_scale': ('FLOAT', arr[:, 4]),
                                                                   'g6_rot': ('FLOAT', arr[:, 5])})
    ng = build_instancer_group(PFX + 'moss collar instancer', srcs)
    ob = add_object(PFX + 'moss collars', me, 'growth')
    m = ob.modifiers.new('G6 ground / moss collar instancer', 'NODES')
    m.node_group = ng
    ctx['rep']['moss_extra_total'] = len(extra)
