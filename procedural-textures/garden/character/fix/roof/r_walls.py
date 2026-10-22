"""Plaster walls and caps (step 4 of the roof brief). Plain words: the three long garden walls were plain 8-vertex boxes. Here each one
gets a fine grid on its garden face, 2 to 4 plaster-loss patches (real dents with an irregular outline), hairline cracks (thin dark
ribbons), drip streaks under the cap, a darker splash band, a stone footing strip, a plaster normal map and a soft blotch colour from
sw_plaster.jpg. The caps get 3 to 6 chipped tile corners, lichen specks and a green line."""
import bpy
import bmesh
import math
import numpy as np
from mathutils import Vector, Matrix
from r_common import *
import r_maps

WALLS = [  # object, garden-side outward normal, number of loss patches, number of cracks, along axis, height top z
    ('Back wall, left', (0, -1, 0), 3, 4, 0, 2.10),         # FIX ROUND: fewer cracks (was 5, 5, 8), each one bolder and longer
    ('Back wall, right', (0, -1, 0), 3, 4, 0, 2.10),
    ('Right wall behind hall', (-1, 0, 0), 4, 5, 1, 2.20),
]
FIXED_PATCHES = {'Back wall, right': [(9.1, 1.05), (7.3, 1.45)], 'Back wall, left': [(-8.0, 1.0)]}
FIXED_CRACKS = {'Back wall, right': [(8.4, 1.95), (9.8, 1.8)]}      # FIX ROUND: two bold cracks start where the hero camera looks (right of the pine)
CAPS = {'Back wall, left': 'Back wall, left cap', 'Back wall, right': 'Back wall, right cap', 'Right wall behind hall': 'Right wall behind hall cap'}


def _smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def dense_mesh(src, gn, step_vis=0.03, step_back=0.25):
    """new mesh: the garden face as a fine grid, the other long face as a coarse grid, small faces unchanged"""
    gn = Vector(gn)
    bm = bmesh.new()
    verts = {}
    def vert(co):
        key = tuple(round(c, 5) for c in co)
        v = verts.get(key)
        if v is None:
            v = bm.verts.new(co)
            verts[key] = v
        return v
    info = {}
    for p in src.polygons:
        vs = [src.vertices[i].co.copy() for i in p.vertices]
        if len(vs) != 4:
            continue
        d = p.normal.dot(gn)
        if d > 0.9 or d < -0.9:
            step = step_vis if d > 0 else step_back
            nu = max(1, int(math.ceil((vs[1] - vs[0]).length / step)))
            nv = max(1, int(math.ceil((vs[2] - vs[1]).length / step)))
            grid = {}
            for i in range(nu + 1):
                for j in range(nv + 1):
                    s, t = i / nu, j / nv
                    co = vs[0] * (1 - s) * (1 - t) + vs[1] * s * (1 - t) + vs[2] * s * t + vs[3] * (1 - s) * t
                    grid[(i, j)] = vert(co)
            for i in range(nu):
                for j in range(nv):
                    bm.faces.new([grid[(i, j)], grid[(i + 1, j)], grid[(i + 1, j + 1)], grid[(i, j + 1)]])
            if d > 0:
                info['garden_face'] = (vs, p.normal.copy())
        else:
            bm.faces.new([vert(c) for c in vs])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(PFX + 'wall')
    bm.to_mesh(me)
    bm.free()
    return me, info


def patch_shape(rng, R):
    """organic outline: harmonics 1 to 6 with decaying amplitude (a blob with bays and bulges, not a star and not a circle)"""
    ks = np.arange(1, 7)
    ph = rng.uniform(0, 6.28, len(ks))
    amp = rng.uniform(0.7, 1.0, len(ks)) * 0.30 / ks ** 0.95
    def r_of(theta):
        r = np.ones_like(theta)
        for k, p, a in zip(ks, ph, amp):
            r = r + a * np.sin(k * theta + p)
        return R * np.clip(r, 0.45, 1.7)
    return r_of


def build_wall(obj, gn, n_patch, n_crack, axis, ztop, rng, imgs):
    """returns (stats, crack ribbon mesh data, footing blocks)"""
    me_old = obj.data
    src_mats = [m for m in me_old.materials]
    me, info = dense_mesh(me_old, gn)
    swap = swap_mesh_to(obj, me)
    vs, nrm = info['garden_face']
    gnv = Vector(gn)
    # wall coordinates: s along the axis (metres), t = height
    P = np.array([v.co[:] for v in me.vertices])
    s_arr = P[:, axis]
    t_arr = P[:, 2]
    plane_d = nrm.dot(vs[0])
    on_face = np.abs(P @ np.array(nrm[:]) - plane_d) < 1e-4
    s_min, s_max = float(s_arr[on_face].min()), float(s_arr[on_face].max())
    t_min, t_max = float(t_arr[on_face].min()), float(t_arr[on_face].max())
    L = s_max - s_min
    # ---------------------------------------------------------------- loss patches (real dents)
    patches = []
    loss = np.zeros(len(P), np.float32)
    depth = np.zeros(len(P), np.float32)
    tries = 0
    fixed = list(FIXED_PATCHES.get(obj.name, []))
    while len(patches) < n_patch and tries < 200:
        tries += 1
        R = rng.uniform(0.17, 0.33)
        cs = rng.uniform(s_min + 0.5 + R, s_max - 0.5 - R)
        ct = rng.uniform(t_min + 0.55 + R, ztop - 0.35 - R)
        if fixed:
            cs, ct = fixed.pop(0)        # a few patches are placed on purpose where the hero camera looks (right of the pine)
        if any(math.hypot(cs - q['s'], ct - q['t']) < q['R'] + R + 0.5 for q in patches):
            continue
        patches.append({'s': cs, 't': ct, 'R': R, 'depth': rng.uniform(0.015, 0.025), 'fn': patch_shape(rng, R), 'asp': rng.uniform(0.7, 1.45)})
    for q in patches:
        ds, dt = (s_arr - q['s']) / q['asp'], (t_arr - q['t']) * q['asp']
        th = np.arctan2(dt, ds)
        r = q['fn'](th)
        dist = np.sqrt(ds * ds + dt * dt)
        m = _smooth(1.0, 0.0, (dist - (r - 0.012)) / 0.032) * on_face                  # 1 inside, falls to 0 over 3 cm at the edge (a clear lip)
        loss = np.maximum(loss, m.astype(np.float32))
        depth = np.maximum(depth, (m * q['depth']).astype(np.float32))
    co = np.array([v.co[:] for v in me.vertices])
    co -= np.outer(depth, np.array(nrm[:]))
    me.vertices.foreach_set('co', co.ravel())
    # ---------------------------------------------------------------- drip streaks under the cap
    streak = np.zeros(len(P), np.float32)
    streaks = []
    for _ in range(int(L / 1.1) + 2):
        cs = rng.uniform(s_min + 0.3, s_max - 0.3)
        ln = rng.uniform(0.45, 1.1)
        w = rng.uniform(0.035, 0.06)
        amp = rng.uniform(0.5, 0.9)
        streaks.append((cs, ln))
        top = ztop + 0.0
        g = np.exp(-((s_arr - cs) ** 2) / (2 * w * w)) * _smooth(0.0, 0.12, top - t_arr) * (1 - _smooth(0.55 * ln, ln, top - t_arr)) * on_face
        streak = np.maximum(streak, (amp * g).astype(np.float32))
    for nm, arr in (('g6_loss', loss), ('g6_streak', streak)):
        a = me.attributes.new(nm, 'FLOAT', 'POINT')
        a.data.foreach_set('value', arr)
    # ---------------------------------------------------------------- hairline cracks (thin dark ribbons just above the plaster)
    cracks = []
    fixed_c = list(FIXED_CRACKS.get(obj.name, []))
    for ci in range(n_crack):
        fx = fixed_c.pop(0) if fixed_c else None
        for _try in range(20):
            if fx is not None:
                s0, t0 = fx
                ang0 = rng.uniform(-2.1, -1.1)
            elif patches and rng.random() < 0.5:
                q = patches[rng.integers(len(patches))]
                ang = rng.uniform(0, 6.28)
                s0, t0 = q['s'] + np.cos(ang) * q['R'] * 1.1, q['t'] + np.sin(ang) * q['R'] * 1.1
            else:
                s0, t0 = rng.uniform(s_min + 0.3, s_max - 0.3), rng.uniform(t_min + 0.5, ztop - 0.25)
            ang = ang0 if fx is not None else (rng.uniform(-2.6, -0.5) if rng.random() < 0.75 else rng.uniform(-0.4, 0.4))
            pts = [(s0, t0)]
            n = int(rng.integers(7, 12))
            for k in range(n):
                ang += rng.choice([-1, 1]) * rng.uniform(0.25, 0.7)
                step = rng.uniform(0.05, 0.10)
                s0, t0 = s0 + math.cos(ang) * step, t0 + math.sin(ang) * step
                pts.append((s0, t0))
            ok = all(s_min + 0.1 < a < s_max - 0.1 and t_min + 0.3 < b < ztop - 0.12 for a, b in pts)
            ok = ok and not any(math.hypot(a - q['s'], b - q['t']) < q['R'] * 0.75 for a, b in pts[1:] for q in patches)
            ok = ok and not any(math.hypot(a - c[0], b - c[1]) < 0.35 for a, b in pts for cr in cracks for c in cr)         # no two cracks cross or touch
            if ok:
                cracks.append(pts)
                break
    return {'patches': [(round(q['s'], 2), round(q['t'], 2), round(q['R'], 2), round(q['depth'], 3)) for q in patches],
            'streaks': len(streaks), 'cracks': len(cracks), 's_range': (s_min, s_max), 't_range': (t_min, t_max)}, cracks, nrm, vs, axis


def swap_mesh_to(obj, me):
    import json
    if 'g6_orig' not in obj.keys():
        obj['g6_orig'] = json.dumps({'mesh': obj.data.name, 'mats': [m.name if m else None for m in obj.data.materials]})
        obj.data.use_fake_user = True
    mats = [m for m in obj.data.materials]
    obj.data = me
    me.name = PFX + obj.name
    for m in mats:
        me.materials.append(m)
    return me


def crack_ribbons(name, polylines, surf_point, normal, width=0.024, lift=0.002):
    """polylines in (s, t) wall coordinates -> one mesh of tapering ribbons. surf_point(s, t) -> Vector on the (undented) wall."""
    verts, faces = [], []
    for pts in polylines:
        base = len(verts)
        n = len(pts)
        for i, (s, t) in enumerate(pts):
            a = surf_point(*pts[max(i - 1, 0)])
            b = surf_point(*pts[min(i + 1, n - 1)])
            tang = (b - a).normalized()
            side = tang.cross(normal).normalized()
            f = i / (n - 1)
            w = width * (0.40 + 0.60 * math.sin(math.pi * min(max(f, 0.02), 0.98)) ** 0.5)
            p = surf_point(s, t) + normal * lift
            verts.append(p + side * w * 0.5)
            verts.append(p - side * w * 0.5)
        for i in range(n - 1):
            a = base + 2 * i
            faces.append((a, a + 2, a + 3, a + 1))
    return new_mesh(name, verts, faces)


def footing_blocks(name, p0, p1, normal, up, rng, thickness=0.07, height=0.25, z_bottom=-0.08, depth_off=0.0):
    """a row of chunky stone blocks along the base of the wall (garden side), each a bevelled box with a slightly rough top"""
    bm = bmesh.new()
    d = (p1 - p0)
    L = d.length
    dirv = d.normalized()
    pos = 0.0
    while pos < L - 0.15:
        ln = min(rng.uniform(0.55, 0.95), L - pos)
        h = height + rng.uniform(-0.025, 0.03)
        th = thickness + rng.uniform(-0.01, 0.02)
        a = p0 + dirv * pos
        b = p0 + dirv * (pos + ln - 0.015)
        zs = z_bottom
        verts = []
        for end in (a, b):
            for (dz, dn) in ((zs, 0.0), (zs + h, 0.0), (zs + h, th * 0.0 + th), (zs, th)):
                pass
        c = []
        for end in (a, b):
            for dz, dn in ((zs, -0.02), (zs + h * 0.92, -0.02), (zs + h, th * 0.35), (zs + h * 0.95, th), (zs, th)):
                c.append(Vector((end.x, end.y, 0)) + normal * (dn + depth_off) + Vector((0, 0, dz)))
        vv = [bm.verts.new(x) for x in c]
        k = 5
        for i in range(k - 1):
            bm.faces.new([vv[i], vv[i + 1], vv[k + i + 1], vv[k + i]])
        bm.faces.new([vv[0], vv[k + 0], vv[k + 4], vv[4]]) if False else None
        bm.faces.new([vv[k + 4], vv[k + 3], vv[k + 2], vv[k + 1], vv[k + 0]])
        bm.faces.new([vv[0], vv[1], vv[2], vv[3], vv[4]])
        bm.faces.new([vv[4], vv[k + 4], vv[k + 0], vv[0]])
        pos += ln
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for v in bm.verts:
        v.co += Vector((rng.uniform(-0.004, 0.004), rng.uniform(-0.004, 0.004), rng.uniform(-0.006, 0.006)))
    me = bpy.data.meshes.new(PFX + name)
    bm.to_mesh(me)
    bm.free()
    return me


def chip_caps(obj, rng, count):
    """3 to 6 cap tiles lose a corner: the island (connected piece) gets one slanted cut at a top corner and the hole is closed"""
    me = obj.data
    me_new = me.copy()
    me_new.name = PFX + obj.name
    if 'g6_orig' not in obj.keys():
        import json
        obj['g6_orig'] = json.dumps({'mesh': me.name, 'mats': [m.name if m else None for m in me.materials]})
        me.use_fake_user = True
    bm = bmesh.new()
    bm.from_mesh(me_new)
    seen = set()
    isl = []
    for v in bm.verts:
        if v.index in seen:
            continue
        stack, comp = [v], []
        seen.add(v.index)
        while stack:
            a = stack.pop()
            comp.append(a)
            for e in a.link_edges:
                b = e.other_vert(a)
                if b.index not in seen:
                    seen.add(b.index)
                    stack.append(b)
        isl.append(comp)
    cand = [c for c in isl if len(c) == 14]            # the small tile bodies on top of the cap board
    rng.shuffle(cand)
    chipped = 0
    for comp in cand[:count]:
        co = np.array([v.co[:] for v in comp])
        top = co[:, 2].max()
        sx = rng.choice([-1, 1])
        sy = rng.choice([-1, 1])
        cx = co[:, 0].max() if sx > 0 else co[:, 0].min()
        cy = co[:, 1].max() if sy > 0 else co[:, 1].min()
        n = Vector((sx * 0.6, sy * 0.45, 0.65)).normalized()
        corner = Vector((cx, cy, top))
        reach = rng.uniform(0.035, 0.06)
        geom = list(comp) + list({e for v in comp for e in v.link_edges}) + list({f for v in comp for f in v.link_faces})
        bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-6, plane_co=corner - n * reach, plane_no=n, clear_outer=True)
        chipped += 1
    edges = [e for e in bm.edges if e.is_boundary]
    if edges:
        bmesh.ops.holes_fill(bm, edges=edges, sides=12)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me_new)
    bm.free()
    obj.data = me_new
    return chipped


# ------------------------------------------------------------------------------------------------- materials
def build_wall_material(mat, imgs, ztop_attr='g6_ztop', cap=False):
    nt = mat.node_tree
    N, L = nt.nodes, nt.links
    bsdf = [n for n in N if n.bl_idname == 'ShaderNodeBsdfPrincipled'][0]
    wk = N['WK wallgrowth']
    bump = N['Bump']
    col = wk.outputs['Colour']
    rough_in = wk.outputs['Roughness']
    # coordinates
    tc = nnew(nt, 'ShaderNodeNewGeometry', 'G6 geo')
    sep = nnew(nt, 'ShaderNodeSeparateXYZ', 'G6 pos sep')
    L.new(tc.outputs['Position'], sep.inputs['Vector'])
    z = sep.outputs['Z']
    uv = nnew(nt, 'ShaderNodeUVMap', 'G6 UV', uv_map='UVMap')
    if not cap:
        # soft blotches from sw_plaster.jpg, mixed 40 percent (stays inside the palette)
        bl = nnew(nt, 'ShaderNodeTexImage', 'G6 blotch image')
        bl.image = imgs['blotch']
        bl.interpolation = 'Linear'
        bl.extension = 'REPEAT'
        L.new(uv.outputs['UV'], bl.inputs['Vector'])
        bfac = vmath(nt, 'SCALE', bl.outputs['Color'])
        bfac.inputs['Scale'].default_value = 2.0
        mixb = mix_rgb(nt, 0.40, (1.0, 1.0, 1.0, 1.0), bfac.outputs[0])
        col = vmath(nt, 'MULTIPLY', col, mix_out(mixb)).outputs[0]
        # splash band: darker and slightly cooler up to 0.45 m
        band = math_node(nt, 'SUBTRACT', 1.0, smoothstep_node(nt, z, 0.12, 0.5).outputs[0])
        col = mix_out(mix_rgb(nt, math_node(nt, 'MULTIPLY', band.outputs[0], 0.38).outputs[0], col, hex_lin('#5d5a52')))
        # drip streaks under the cap, plaster loss patches (brown clay), thin green line under the cap
        st = nnew(nt, 'ShaderNodeAttribute', 'G6 streak', attribute_type='GEOMETRY', attribute_name='g6_streak')
        col = mix_out(mix_rgb(nt, math_node(nt, 'MULTIPLY', st.outputs['Fac'], 0.55).outputs[0], col, hex_lin('#4a4a4c')))
        ls = nnew(nt, 'ShaderNodeAttribute', 'G6 loss', attribute_type='GEOMETRY', attribute_name='g6_loss')
        lnz = nnew(nt, 'ShaderNodeTexNoise', 'G6 loss edge noise', noise_dimensions='3D')
        lnz.inputs['Scale'].default_value = 34.0
        lnz.inputs['Detail'].default_value = 1.0
        L.new(tc.outputs['Position'], lnz.inputs['Vector'])
        lsn = math_node(nt, 'ADD', ls.outputs['Fac'], math_node(nt, 'MULTIPLY', math_node(nt, 'SUBTRACT', lnz.outputs['Fac'], 0.5).outputs[0], 0.5).outputs[0])
        cn = nnew(nt, 'ShaderNodeTexNoise', 'G6 clay colour noise', noise_dimensions='3D')
        cn.inputs['Scale'].default_value = 9.0
        L.new(tc.outputs['Position'], cn.inputs['Vector'])
        clay0 = mix_out(mix_rgb(nt, cn.outputs['Fac'], hex_lin('#7a6650'), hex_lin('#93806a')))
        clay = mix_out(mix_rgb(nt, smoothstep_node(nt, lsn.outputs[0], 0.55, 1.0).outputs[0], clay0, hex_lin('#5a4a3a')))
        col = mix_out(mix_rgb(nt, smoothstep_node(nt, lsn.outputs[0], 0.38, 0.5).outputs[0], col, clay))
        zt = nnew(nt, 'ShaderNodeAttribute', 'G6 ztop', attribute_type='OBJECT', attribute_name=ztop_attr)
        dz = math_node(nt, 'SUBTRACT', zt.outputs['Fac'], z)
        line = math_node(nt, 'MULTIPLY', smoothstep_node(nt, dz.outputs[0], 0.17, 0.05).outputs[0], smoothstep_node(nt, dz.outputs[0], -0.02, 0.02).outputs[0])
        pn = vmath(nt, 'SCALE', tc.outputs['Position'])
        pn.inputs['Scale'].default_value = 1.0
        noi = nnew(nt, 'ShaderNodeTexNoise', 'G6 green noise', noise_dimensions='3D')
        noi.inputs['Scale'].default_value = 2.1
        noi.inputs['Detail'].default_value = 2.0
        L.new(tc.outputs['Position'], noi.inputs['Vector'])
        patchy = smoothstep_node(nt, noi.outputs['Fac'], 0.46, 0.62)
        gmask = math_node(nt, 'MULTIPLY', line.outputs[0], patchy.outputs[0])
        col = mix_out(mix_rgb(nt, math_node(nt, 'MULTIPLY', gmask.outputs[0], 0.85).outputs[0], col, hex_lin('#4a4a22')))
        rmix = nnew(nt, 'ShaderNodeMix', 'G6 rough', data_type='FLOAT')
        L.new(smoothstep_node(nt, ls.outputs['Fac'], 0.1, 0.6).outputs[0], sid(rmix.inputs, 'Factor_Float'))
        L.new(rough_in, sid(rmix.inputs, 'A_Float'))
        sid(rmix.inputs, 'B_Float').default_value = 0.95
        L.new(rmix.outputs['Result'], bsdf.inputs['Roughness'])
    else:
        # caps: pale lichen specks and a patchy soft green on the top faces
        vor = nnew(nt, 'ShaderNodeTexVoronoi', 'G6 specks', voronoi_dimensions='3D', feature='F1')
        vor.inputs['Scale'].default_value = 20.0
        L.new(tc.outputs['Position'], vor.inputs['Vector'])
        noi = nnew(nt, 'ShaderNodeTexNoise', 'G6 speck zone', noise_dimensions='3D')
        noi.inputs['Scale'].default_value = 1.6
        L.new(tc.outputs['Position'], noi.inputs['Vector'])
        dots = math_node(nt, 'SUBTRACT', 1.0, smoothstep_node(nt, vor.outputs['Distance'], 0.30, 0.44).outputs[0])
        zone = smoothstep_node(nt, noi.outputs['Fac'], 0.52, 0.64)
        lich = math_node(nt, 'MULTIPLY', dots.outputs[0], zone.outputs[0])
        col = mix_out(mix_rgb(nt, math_node(nt, 'MULTIPLY', lich.outputs[0], 0.8).outputs[0], col, hex_lin('#b8a47c')))
        nrm = nnew(nt, 'ShaderNodeNewGeometry', 'G6 geo n')
        up = smoothstep_node(nt, nrm.outputs['Normal'].node.outputs['Normal'] if False else nrm.outputs['Normal'], 0.0, 1.0) if False else None
        nsep = nnew(nt, 'ShaderNodeSeparateXYZ', 'G6 n sep')
        L.new(nrm.outputs['Normal'], nsep.inputs['Vector'])
        noi2 = nnew(nt, 'ShaderNodeTexNoise', 'G6 moss zone', noise_dimensions='3D')
        noi2.inputs['Scale'].default_value = 3.0
        noi2.inputs['Detail'].default_value = 2.0
        L.new(tc.outputs['Position'], noi2.inputs['Vector'])
        topm = smoothstep_node(nt, nsep.outputs['Z'], 0.55, 0.85)
        patch = smoothstep_node(nt, noi2.outputs['Fac'], 0.5, 0.62)
        gm = math_node(nt, 'MULTIPLY', topm.outputs[0], patch.outputs[0])
        col = mix_out(mix_rgb(nt, math_node(nt, 'MULTIPLY', gm.outputs[0], 0.7).outputs[0], col, hex_lin('#4d4b22')))
    L.new(col, bsdf.inputs['Base Color'])
    # normal map: tangent space, box UV (plaster map 1 unit = 2.5 m; cap glaze map 1 unit = 1 m)
    key = 'glaze' if cap else 'plaster'
    mp = nnew(nt, 'ShaderNodeMapping', 'G6 NM mapping')
    mp.inputs['Scale'].default_value = (1.5, 1.5, 1.5) if cap else (1.0, 1.0, 1.0)
    L.new(uv.outputs['UV'], mp.inputs['Vector'])
    tx = nnew(nt, 'ShaderNodeTexImage', 'G6 NM image')
    tx.image = imgs[key]
    tx.interpolation = 'Cubic'
    tx.extension = 'REPEAT'
    L.new(mp.outputs['Vector'], tx.inputs['Vector'])
    nm = nnew(nt, 'ShaderNodeNormalMap', 'G6 NM', space='TANGENT', uv_map='UVMap')
    nm.inputs['Strength'].default_value = 1.0 if not cap else 0.8
    L.new(tx.outputs['Color'], nm.inputs['Color'])
    if not cap:
        # loss-patch rim and crack grooves feel: a soft bump from the loss mask on top of the normal map
        b2 = nnew(nt, 'ShaderNodeBump', 'G6 loss bump')
        b2.inputs['Strength'].default_value = 0.8
        b2.inputs['Distance'].default_value = 0.01
        rn = nnew(nt, 'ShaderNodeTexNoise', 'G6 clay grain', noise_dimensions='3D')
        rn.inputs['Scale'].default_value = 60.0
        rn.inputs['Detail'].default_value = 2.0
        L.new(tc.outputs['Position'], rn.inputs['Vector'])
        hh = math_node(nt, 'ADD', ls.outputs['Fac'], math_node(nt, 'MULTIPLY', math_node(nt, 'MULTIPLY', math_node(nt, 'SUBTRACT', rn.outputs['Fac'], 0.5).outputs[0], 0.35).outputs[0], ls.outputs['Fac']).outputs[0])
        L.new(hh.outputs[0], b2.inputs['Height'])
        L.new(nm.outputs['Normal'], b2.inputs['Normal'])
        L.new(b2.outputs['Normal'], bump.inputs['Normal'])
    else:
        L.new(nm.outputs['Normal'], bump.inputs['Normal'])
    bump.inputs['Strength'].default_value = 0.28
    return mat


def crack_material():
    old = bpy.data.materials.get(PFX + 'crack')
    if old is not None:
        return old          # one crack material for walls, rocks and lantern (no .001 copies)
    m = bpy.data.materials.new(PFX + 'crack')
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = hex_lin('#2e2722')
    b.inputs['Roughness'].default_value = 0.9
    return m
