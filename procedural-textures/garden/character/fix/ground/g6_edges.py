"""GROUND builder, step 4: where the lawn meets gravel, stones and wood.
 * Gravel kerb: its own material copy 'G6 ground / stone.rock' with a soft stone normal map (box UV, 1 m), a dark soil lip 10 to 15 cm wide on the grass
   side (own mesh), tufts and little moss pads growing from the joints, chips at the joints, 15 to 25 gravel pieces spilled onto the grass;
 * Stepping stones 0..7: soft stone normal map, a 5 mm worn dish (darker, smoother in the middle), a mud rim around the foot, a little moss at some edges;
 * Gravel rocks 0..2: soft stone normal map (moss collars and the cap come from step 3);
 * Pebbles (sources and grouped bodies): soft pebble normal map;
 * dark contact strips (soft darker bands 10 to 20 cm wide) where the grass meets rocks, the lantern base, the plinth and the bank ends of the bridge.
"""
import math
import os
import json
import numpy as np
import bpy
from g6_common import (hex_lin, lerp3, smoothstep, mesh_from_arrays, box_uv, swap_mesh, track_uv, N, link, load_image, normal_chain, unlink_input,
                       set_default, PFX, add_object)
from g6_scatter import make_points_mesh, build_instancer_group
import g6_moss
import g6_small


# ------------------------------------------------------------------------------------------------ materials
def strip_material(name, rgb, strength, opaque=False):
    """a soft dark band: vertex colour alpha is the strength (transparent where it is 0)."""
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        if n.bl_idname != 'ShaderNodeOutputMaterial':
            nt.nodes.remove(n)
    out = nt.nodes['Material Output']
    vc = nt.nodes.new('ShaderNodeVertexColor')
    vc.layer_name = 'Col'
    bs = nt.nodes.new('ShaderNodeBsdfPrincipled')
    bs.inputs['Base Color'].default_value = (*rgb, 1.0)
    bs.inputs['Roughness'].default_value = 0.95
    bs.inputs['Specular IOR Level'].default_value = 0.1
    if opaque:
        nt.links.new(vc.outputs['Color'], bs.inputs['Base Color'])
        nt.links.new(bs.outputs['BSDF'], out.inputs['Surface'])
        return mat
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    mx = nt.nodes.new('ShaderNodeMixShader')
    mul = nt.nodes.new('ShaderNodeMath')
    mul.operation = 'MULTIPLY'
    mul.inputs[1].default_value = strength
    nt.links.new(vc.outputs['Alpha'], mul.inputs[0])
    nt.links.new(mul.outputs[0], mx.inputs['Fac'])
    nt.links.new(tr.outputs['BSDF'], mx.inputs[1])
    nt.links.new(bs.outputs['BSDF'], mx.inputs[2])
    nt.links.new(mx.outputs['Shader'], out.inputs['Surface'])
    return mat


def soil_material(name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes['Principled BSDF']
    vc = nt.nodes.new('ShaderNodeVertexColor')
    vc.layer_name = 'Col'
    geo = nt.nodes.new('ShaderNodeNewGeometry')
    nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 26.0
    nz.inputs['Detail'].default_value = 3.0
    nz.inputs['Roughness'].default_value = 0.6
    nt.links.new(geo.outputs['Position'], nz.inputs['Vector'])
    mr = nt.nodes.new('ShaderNodeMapRange')
    mr.inputs['From Min'].default_value = 0.3
    mr.inputs['From Max'].default_value = 0.7
    mr.inputs['To Min'].default_value = 0.65
    mr.inputs['To Max'].default_value = 1.35
    nt.links.new(nz.outputs['Fac'], mr.inputs['Value'])
    mul = nt.nodes.new('ShaderNodeMix')
    mul.data_type = 'RGBA'
    mul.blend_type = 'MULTIPLY'
    mul.inputs[0].default_value = 1.0
    comb = nt.nodes.new('ShaderNodeCombineXYZ')
    for s in ('X', 'Y', 'Z'):
        nt.links.new(mr.outputs['Result'], comb.inputs[s])
    nt.links.new(vc.outputs['Color'], mul.inputs[6])
    nt.links.new(comb.outputs['Vector'], mul.inputs[7])
    nt.links.new(next(o for o in mul.outputs if o.enabled), bsdf.inputs['Base Color'])
    bp = nt.nodes.new('ShaderNodeBump')
    bp.inputs['Strength'].default_value = 0.45
    bp.inputs['Distance'].default_value = 0.01
    nt.links.new(nz.outputs['Fac'], bp.inputs['Height'])
    nt.links.new(bp.outputs['Normal'], bsdf.inputs['Normal'])
    bsdf.inputs['Roughness'].default_value = 0.95
    bsdf.inputs['Specular IOR Level'].default_value = 0.1
    return mat


def upgrade_stone(mat, img, strength, bump_strength, uv='UVMap', loc=(-1400, -1300), copy_ok=False):
    """soft tangent normal map from the stone picture into the material's Bump node (the node keeps a small strength)."""
    nt = mat.node_tree
    bump = nt.nodes['Bump']
    nm, mp = normal_chain(nt, 'stone', img, uv, strength, (1.0, 1.0, 1.0), loc=loc)
    link(nt, nm, 'Normal', bump, 'Normal')
    if copy_ok:
        bump.inputs['Strength'].default_value = bump_strength
    else:
        set_default(mat, 'Bump', 'Strength', bump_strength)
    return nm, bump


def add_dish(mat, radius, depth=0.55):
    """worn dish: Object-space radius -> rim height (0 in the middle bowl, 1 at the rim) added to the Bump height, and a slightly darker, smoother middle."""
    nt = mat.node_tree
    bump = nt.nodes['Bump']
    tc = N(nt, 'ShaderNodeTexCoord', 'dish coord', (-1700, -1500))
    sep = N(nt, 'ShaderNodeSeparateXYZ', 'dish sep', (-1500, -1500))
    link(nt, tc, 'Object', sep, 'Vector')
    sx = N(nt, 'ShaderNodeMath', 'dish x2', (-1300, -1450))
    sx.operation = 'POWER'
    sx.inputs[1].default_value = 2.0
    sy = N(nt, 'ShaderNodeMath', 'dish y2', (-1300, -1600))
    sy.operation = 'POWER'
    sy.inputs[1].default_value = 2.0
    link(nt, sep, 'X', sx, 0)
    link(nt, sep, 'Y', sy, 0)
    add = N(nt, 'ShaderNodeMath', 'dish r2', (-1120, -1520))
    add.operation = 'ADD'
    link(nt, sx, 0, add, 0)
    link(nt, sy, 0, add, 1)
    sq = N(nt, 'ShaderNodeMath', 'dish r', (-960, -1520))
    sq.operation = 'SQRT'
    link(nt, add, 0, sq, 0)
    mr = N(nt, 'ShaderNodeMapRange', 'dish profile', (-800, -1520))
    mr.interpolation_type = 'SMOOTHSTEP'
    mr.inputs['From Min'].default_value = 0.30 * radius
    mr.inputs['From Max'].default_value = 0.95 * radius
    mr.inputs['To Min'].default_value = 0.0
    mr.inputs['To Max'].default_value = depth
    mr.clamp = True
    link(nt, sq, 0, mr, 'Value')
    # height total = old height + dish
    old = [l for l in nt.links if l.to_node == bump and l.to_socket.name == 'Height']
    tot = N(nt, 'ShaderNodeMath', 'dish height total', (-620, -1400))
    tot.operation = 'ADD'
    if old:
        l = old[0]
        src = l.from_socket
        unlink_input(mat, 'Bump', 'Height')
        link(nt, src, tot, 0)
    link(nt, mr, 0, tot, 1)
    link(nt, tot, 0, bump, 'Height')
    # darker, smoother middle: a gentle multiply on the colour
    bsdf = nt.nodes['Principled BSDF']
    old_c = [l for l in nt.links if l.to_node == bsdf and l.to_socket.name == 'Base Color']
    if old_c:
        srcc = old_c[0].from_socket
        unlink_input(mat, 'Principled BSDF', 'Base Color')
        inv = N(nt, 'ShaderNodeMath', 'dish tint fac', (-620, -1650))
        inv.operation = 'MULTIPLY_ADD'
        inv.inputs[1].default_value = -0.5 / max(depth, 1e-3)
        inv.inputs[2].default_value = 0.5
        link(nt, mr, 0, inv, 0)
        mix = N(nt, 'ShaderNodeMix', 'dish tint', (-420, -1600))
        mix.data_type = 'RGBA'
        mix.blend_type = 'MULTIPLY'
        mix.inputs[7].default_value = (0.90, 0.89, 0.88, 1.0)
        link(nt, inv, 0, mix, 0)
        link(nt, srcc, mix, 6)
        link(nt, next(o for o in mix.outputs if o.enabled), bsdf, 'Base Color')


# ------------------------------------------------------------------------------------------------ geometry helpers
def ribbon(world, rows, closed, z_lift, colour_rows, rng=None):
    """rows: list of (P Nx2 arrays) one per row (same N); builds a quad band between consecutive rows; z follows the surface.
    colour_rows: list of RGBA per row. returns verts, faces, cols (drops quads that touch water or have no ground)."""
    nrow = len(rows)
    n = len(rows[0])
    verts, cols, ok = [], [], []
    for r in range(nrow):
        for i in range(n):
            x, y = rows[r][i]
            z, _ = world.surface(float(x), float(y))
            good = z is not None and z > -0.02
            verts.append((float(x), float(y), (z if good else 0.0) + z_lift[r]))
            cols.append(colour_rows[r])
            ok.append(good)
    faces = []
    last = n if closed else n - 1
    for r in range(nrow - 1):
        for i in range(last):
            a0, a1 = r * n + i, r * n + (i + 1) % n
            b0, b1 = (r + 1) * n + i, (r + 1) * n + (i + 1) % n
            if ok[a0] and ok[a1] and ok[b0] and ok[b1]:
                faces.append((a0, a1, b1, b0))
    return verts, faces, cols


def ring_for(world, name, bins=36):
    """smooth footprint ring of an object: returns (centre, angles, radii) with gaps filled in."""
    ol, c = g6_moss.outline_points(world, name, bins=bins)
    if not ol:
        return None
    ang = np.array([a for a, r, p in ol])
    rad = np.array([r for a, r, p in ol])
    full_a = -math.pi + 2 * math.pi * (np.arange(bins) + 0.5) / bins
    rr = np.interp(full_a, ang, rad, period=2 * math.pi)
    return c, full_a, rr


def contact_band(world, name, width, rgba_in, rgba_out, z=0.006, inner_off=0.0, bins=36, rng=None):
    ring = ring_for(world, name, bins)
    if ring is None:
        return None
    c, ang, rad = ring
    # smooth the radii a little so the band does not zigzag
    rad = (np.roll(rad, 1) + 2 * rad + np.roll(rad, -1)) / 4.0
    w = width * (rng.uniform(0.8, 1.2, len(ang)) if rng is not None else 1.0)
    P0 = np.stack([c[0] + np.cos(ang) * (rad + inner_off), c[1] + np.sin(ang) * (rad + inner_off)], axis=1)
    P1 = np.stack([c[0] + np.cos(ang) * (rad + inner_off + 0.5 * w), c[1] + np.sin(ang) * (rad + inner_off + 0.5 * w)], axis=1)
    P2 = np.stack([c[0] + np.cos(ang) * (rad + inner_off + w), c[1] + np.sin(ang) * (rad + inner_off + w)], axis=1)
    mid = tuple((a + b) * 0.5 for a, b in zip(rgba_in, rgba_out))
    return ribbon(world, [P0, P1, P2], True, [z, z, z], [rgba_in, mid, rgba_out])


def merge(parts):
    V, F, C = [], [], []
    for p in parts:
        if p is None:
            continue
        v, f, c = p
        o = len(V)
        V += v
        C += c
        F += [tuple(i + o for i in fc) for fc in f]
    return V, F, C


# ------------------------------------------------------------------------------------------------ the kerb
def kerb_blocks():
    ob = bpy.data.objects['Gravel kerb']
    me = ob.data
    n = len(me.vertices)
    parent = list(range(n))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    for e in me.edges:
        a, b = find(e.vertices[0]), find(e.vertices[1])
        if a != b:
            parent[a] = b
    co = np.zeros(n * 3, dtype=np.float32)
    me.vertices.foreach_get('co', co)
    co = co.reshape(-1, 3)
    co = co @ np.array(ob.matrix_world.to_3x3(), dtype=np.float32).T + np.array(ob.matrix_world.translation, dtype=np.float32)
    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    out = []
    for g in groups.values():
        c = co[g]
        out.append((c.min(0), c.max(0)))
    return out


def kerb_sides(blocks):
    """returns {'west': [(a, b)...], 'south': ..., 'north': ...} sorted runs (a, b along the side) and the line coordinate of the outer face."""
    sides = {'west': [], 'south': [], 'north': []}
    xs0 = min(b[0][0] for b in blocks)
    ys0 = min(b[0][1] for b in blocks)
    ys1 = max(b[1][1] for b in blocks)
    for mn, mx in blocks:
        dx, dy = mx[0] - mn[0], mx[1] - mn[1]
        if dy > dx and mn[0] < xs0 + 0.3:
            sides['west'].append((float(mn[1]), float(mx[1]), float(mn[0])))
        elif dx >= dy and mx[1] < ys0 + 0.3:
            sides['south'].append((float(mn[0]), float(mx[0]), float(mn[1])))
        elif dx >= dy and mn[1] > ys1 - 0.3:
            sides['north'].append((float(mn[0]), float(mx[0]), float(mx[1])))
    for k in sides:
        sides[k].sort()
    return sides


def outward(side):
    return {'west': (-1.0, 0.0), 'south': (0.0, -1.0), 'north': (0.0, 1.0)}[side]


def along(side):
    return {'west': (0.0, 1.0), 'south': (1.0, 0.0), 'north': (1.0, 0.0)}[side]


def point_on(side, a, line):
    return (line, a) if side == 'west' else (a, line)


def step4(ctx):
    o, world, rep = ctx['o'], ctx['world'], ctx['rep']
    rr = np.random.default_rng(o['seed'] + 41)
    maps = o['maps_dir']
    extra_tuft = []
    extra_moss = ctx.setdefault('moss_extra', [])
    chips = []
    # ------------------------------------------------ kerb material copy + normal + UV
    kerb = bpy.data.objects['Gravel kerb']
    src_mat = bpy.data.materials['GARDEN stone.rock']
    new_mat = src_mat.copy()
    new_mat.name = PFX + 'stone.rock'
    kerb['gnd_orig_mats'] = json.dumps([s.material.name if s.material else '' for s in kerb.material_slots])
    for s in kerb.material_slots:
        s.material = new_mat
    track_uv(kerb, 'UVMap')
    box_uv(kerb.data, 'UVMap', 1.0, matrix=kerb.matrix_world)
    img_stone = load_image(os.path.join(maps, 'stone_normal.png'), 'G6 stone_normal')
    upgrade_stone(new_mat, img_stone, o.get('stone_strength', 1.0), 0.30, copy_ok=True)
    # ------------------------------------------------ joints, soil lip, tufts, moss pads, chips
    blocks = kerb_blocks()
    sides = kerb_sides(blocks)
    lip_parts = []
    joints = []
    lip_len = 0.0
    for side, runs in sides.items():
        if not runs:
            continue
        line = float(np.median([r[2] for r in runs]))
        out = np.array(outward(side))
        al = np.array(along(side))
        # runs of blocks without a gap larger than 15 cm
        groups = []
        cur = [runs[0]]
        for r in runs[1:]:
            if r[0] - cur[-1][1] < 0.15:
                cur.append(r)
            else:
                groups.append(cur)
                cur = [r]
        groups.append(cur)
        for g in groups:
            a0, a1 = g[0][0] + 0.03, g[-1][1] - 0.03
            if a1 - a0 < 0.3:
                continue
            for k in range(len(g) - 1):
                joints.append((side, 0.5 * (g[k][1] + g[k + 1][0]), line))
            n = max(int((a1 - a0) / 0.12), 3)
            t = np.linspace(0.0, 1.0, n + 1)
            av = a0 + (a1 - a0) * t
            wid = rr.uniform(0.10, 0.15) * (0.55 + 0.45 * np.sin(np.pi * t) ** 0.5)
            wid = wid + rr.uniform(-0.012, 0.012, len(t))
            wid = np.maximum(wid, 0.03)
            P = [np.array(point_on(side, a, line)) for a in av]
            rows = [np.array([p + out * 0.0 for p in P]), np.array([p + out * 0.5 * w for p, w in zip(P, wid)]), np.array([p + out * w for p, w in zip(P, wid)])]
            lip_parts.append(ribbon(world, rows, False, [0.013, 0.010, 0.002], [(1, 1, 1, 1)] * 3))
            lip_len += a1 - a0
    # soil lip object
    soil_mat = soil_material(PFX + 'soil lip')
    V, F, Cc = merge(lip_parts)
    if F:
        # vertex colours: dark soil with a little variation
        cols = []
        for i in range(len(V)):
            j = rr.uniform(0.85, 1.15)
            base = hex_lin('#43362c')
            cols.append((base[0] * j * 0.8, base[1] * j * 0.8, base[2] * j * 0.8, 1.0))
        me = mesh_from_arrays(PFX + 'kerb soil lip', np.array(V, dtype=np.float32), F, cols=np.array(cols, dtype=np.float32), smooth=True)
        add_object(PFX + 'kerb soil lip', me, 'ground.earth', mats=[soil_mat])
    rep['kerb'] = dict(blocks=len(blocks), joints=len(joints), lip_length_m=round(lip_len, 2), lip_object=bool(F))
    # tufts from joints, moss pads, chips
    keep = [j for j in joints]
    rr.shuffle(keep)
    ntuft = 0
    nmoss = 0
    for (side, a, line) in keep:
        out = np.array(outward(side))
        p = np.array(point_on(side, a, line)) + out * rr.uniform(0.06, 0.16)
        if world.mask_at(p[0], p[1]) > 0.3 or not world.free(p[0], p[1], 0.03, zmin=-0.03):
            continue
        z = world.ground_z(p[0], p[1])
        r = rr.random()
        if r < 0.45 and ntuft < 16:
            extra_tuft.append((p[0], p[1], z, int(rr.choice([0, 0, 2, 13, 13, 10, 3, 1])), rr.uniform(0.55, 0.95), rr.uniform(0, 6.28)))
            ntuft += 1
        elif r < 0.62 and nmoss < 6:
            extra_moss.append((p[0], p[1], z - 0.01, int(rr.integers(0, 6)), rr.uniform(0.04, 0.07), rr.uniform(0, 6.28)))
            nmoss += 1
        if rr.random() < 0.5:
            for _ in range(int(rr.integers(1, 3))):
                q = p + out * rr.uniform(-0.05, 0.08) + np.array(along(side)) * rr.uniform(-0.1, 0.1)
                if world.free(q[0], q[1], 0.01, zmin=-0.03):
                    chips.append((q[0], q[1], world.ground_z(q[0], q[1]) + 0.004, int(rr.integers(0, 3)), rr.uniform(0.6, 1.1), rr.uniform(0, 6.28)))
    # spilled gravel on the grass: 15 to 25 pieces in clusters of 2 to 4
    nspill = 0
    tries = 0
    side_list = [s for s in sides if sides[s]]
    while nspill < 21 and tries < 400:
        tries += 1
        side = side_list[int(rr.integers(0, len(side_list)))]
        runs = sides[side]
        a = float(rr.uniform(runs[0][0] + 0.2, runs[-1][1] - 0.2))
        line = float(np.median([r[2] for r in runs]))
        out = np.array(outward(side))
        p = np.array(point_on(side, a, line)) + out * rr.uniform(0.18, 0.75)
        if not world.visible(p[0], p[1], 0.05, margin=-0.02) or world.mask_at(p[0], p[1]) > 0.35 or not world.free(p[0], p[1], 0.05, zmin=-0.03):
            continue
        for _ in range(int(rr.integers(2, 5))):
            q = p + rr.normal(0, 0.07, 2)
            if world.free(q[0], q[1], 0.01, zmin=-0.03):
                chips.append((q[0], q[1], world.ground_z(q[0], q[1]) + 0.004, int(rr.integers(0, 3)), rr.uniform(0.7, 1.7), rr.uniform(0, 6.28)))
                nspill += 1
    rep['kerb'].update(tufts_at_joints=ntuft, moss_pads_at_joints=nmoss, spilled_chips=nspill, chips_total=len(chips))
    # ------------------------------------------------ the chip sources and the chips object
    chip_mat = g6_small.vcol_material(PFX + 'chips', rough=0.8, spec=0.2)
    chip_objs = []
    for k in range(3):
        v, f, c = chip_mesh(k)
        me = mesh_from_arrays(PFX + 'chip %d' % k, v, f, cols=c, smooth=False)
        chip_objs.append(add_object(PFX + 'chip %d' % k, me, 'stone.natural', mats=[chip_mat], hide_render=True))
    if chips:
        arr = np.array(chips, dtype=np.float32)
        me = make_points_mesh(PFX + 'chip points', arr[:, :3], {'g6_pick': ('INT', arr[:, 3].astype(np.int32)), 'g6_scale': ('FLOAT', arr[:, 4]), 'g6_rot': ('FLOAT', arr[:, 5])})
        ng = build_instancer_group(PFX + 'chip instancer', chip_objs)
        ob = add_object(PFX + 'spilled gravel', me, 'stone.natural')
        ob.modifiers.new('G6 ground / chip instancer', 'NODES').node_group = ng
    if extra_tuft:
        arr = np.array(extra_tuft, dtype=np.float32)
        me = make_points_mesh(PFX + 'kerb tuft points', arr[:, :3], {'g6_pick': ('INT', arr[:, 3].astype(np.int32)), 'g6_scale': ('FLOAT', arr[:, 4]), 'g6_rot': ('FLOAT', arr[:, 5])})
        ob = add_object(PFX + 'kerb tufts', me, 'growth')
        ob.modifiers.new('G6 ground / kerb tuft instancer', 'NODES').node_group = ctx['tuft_group'] if 'tuft_group' in ctx else None
    # ------------------------------------------------ stepping stones
    stones = []
    for i in range(8):
        ob = bpy.data.objects.get('Stepping stone %d' % i)
        if ob is None:
            continue
        mat = ob.material_slots[0].material
        track_uv(ob, 'UVMap')
        box_uv(ob.data, 'UVMap', 1.0, offset=(0.137 * i + 0.31, 0.211 * i + 0.07))
        upgrade_stone(mat, img_stone, o.get('stone_strength', 1.0), 0.30)
        bb = np.array([ob.matrix_world @ __import__('mathutils').Vector(b) for b in ob.bound_box])
        radius = float(max(bb[:, 0].max() - bb[:, 0].min(), bb[:, 1].max() - bb[:, 1].min()) / 2.0)
        add_dish(mat, radius)
        stones.append(ob.name)
        # a little moss at the edge of every other stone
        if i % 2 == 0:
            ring = ring_for(world, ob.name, bins=24)
            if ring is not None:
                c, ang, rad = ring
                k = int(rr.integers(0, len(ang)))
                x, y = c[0] + math.cos(ang[k]) * (rad[k] + 0.03), c[1] + math.sin(ang[k]) * (rad[k] + 0.03)
                gz, _ = world.surface(x, y)
                if gz is not None:
                    extra_moss.append((x, y, gz - 0.012, int(rr.integers(0, 6)), rr.uniform(0.032, 0.05), rr.uniform(0, 6.28)))
    # ------------------------------------------------ gravel rocks
    for i in range(3):
        ob = bpy.data.objects.get('Gravel rock %d' % i)
        if ob is None:
            continue
        mat = ob.material_slots[0].material
        track_uv(ob, 'UVMap')
        box_uv(ob.data, 'UVMap', 1.0, offset=(0.173 * i + 0.5, 0.119 * i + 0.2))
        upgrade_stone(mat, img_stone, o.get('stone_strength', 1.0), 0.30)
    # ------------------------------------------------ pebbles: sources and grouped bodies
    img_peb = load_image(os.path.join(maps, 'pebble_normal.png'), 'G6 pebble_normal')
    for k in range(4):
        mat = bpy.data.materials['Astra / pebbles tone %d' % k]
        upgrade_stone(mat, img_peb, o.get('pebble_strength', 1.0), 0.30, loc=(-1400, -1500))
    gp = bpy.data.objects.get('Astra / pebbles grouped bodies')
    if gp is not None:
        track_uv(gp, 'UVMap')
        box_uv(gp.data, 'UVMap', 0.10, matrix=gp.matrix_world)
    for i in range(6):
        ob = bpy.data.objects.get('Life / pebble sources %d' % i)
        if ob is not None:
            track_uv(ob, 'UVMap')
            box_uv(ob.data, 'UVMap', 2.5)
    # ------------------------------------------------ contact strips
    parts = []
    names = [n for n in world.feet if n.startswith(('Rock ', 'Pond edge stone', 'Gravel rock', 'Lantern base', 'Bridge pier 0', 'Bridge pier 3'))]
    dark_in, dark_out = (0.05, 0.04, 0.035, 1.0), (0.05, 0.04, 0.035, 0.0)
    ncont = 0
    for n in names:
        w = 0.12 + 0.08 * rr.random()
        part = contact_band(world, n, w, dark_in, dark_out, z=0.007, inner_off=-0.02, rng=rr)
        if part and part[1]:
            parts.append(part)
            ncont += 1
    # mud rims around the stepping stones (on the gravel): narrower and browner
    mud = []
    for n in stones:
        part = contact_band(world, n, 0.055, (0.14, 0.10, 0.07, 1.0), (0.14, 0.10, 0.07, 0.0), z=0.012, inner_off=-0.01, rng=rr)
        if part and part[1]:
            mud.append(part)
    # plinth foot
    pb = world.bbox.get('Stone plinth')
    pl_len = 0.0
    if pb is not None:
        y_front = float(pb[0][1])
        for xa, xb in ((float(pb[0][0]) + 0.05, 1.22), (3.18, float(pb[1][0]) - 0.05)):
            n = max(int((xb - xa) / 0.15), 3)
            xs = np.linspace(xa, xb, n)
            wv = 0.12 + 0.06 * np.abs(np.sin(xs * 1.7))
            P0 = np.stack([xs, np.full(n, y_front + 0.02)], axis=1)
            P1 = np.stack([xs, y_front + 0.02 - 0.5 * wv], axis=1)
            P2 = np.stack([xs, y_front + 0.02 - wv], axis=1)
            parts.append(ribbon(world, [P0, P1, P2], False, [0.007] * 3, [dark_in, tuple((a + b) / 2 for a, b in zip(dark_in, dark_out)), dark_out]))
            pl_len += xb - xa
    strip_mat = strip_material(PFX + 'contact strip', (0.03, 0.025, 0.02), 0.62)
    V, F, Cc = merge(parts)
    if F:
        me = mesh_from_arrays(PFX + 'contact strips', np.array(V, dtype=np.float32), F, cols=np.array(Cc, dtype=np.float32))
        add_object(PFX + 'contact strips', me, 'ground.earth', mats=[strip_mat])
    V, F, Cc = merge(mud)
    if F:
        mud_mat = strip_material(PFX + 'mud rim', (0.10, 0.07, 0.05), 0.45)
        me = mesh_from_arrays(PFX + 'mud rims', np.array(V, dtype=np.float32), F, cols=np.array(Cc, dtype=np.float32))
        add_object(PFX + 'mud rims', me, 'ground.earth', mats=[mud_mat])
    rep['contact'] = dict(objects=ncont, plinth_length_m=round(pl_len, 2), stepping_stone_rims=len(mud))
    rep['stones'] = dict(stepping=len(stones), gravel_rocks=3)


def chip_mesh(k):
    """a small rounded stone: a squashed, jittered icosahedron (20 triangles), 2 to 5 cm, flat shaded (chunky, like the rocks)."""
    rng = np.random.default_rng(900 + k)
    t = (1 + 5 ** 0.5) / 2
    v = np.array([[-1, t, 0], [1, t, 0], [-1, -t, 0], [1, -t, 0], [0, -1, t], [0, 1, t], [0, -1, -t], [0, 1, -t], [t, 0, -1], [t, 0, 1], [-t, 0, -1], [-t, 0, 1]], dtype=float)
    v /= np.linalg.norm(v, axis=1)[:, None]
    f = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8), (3, 9, 4), (3, 4, 2), (3, 2, 6),
         (3, 6, 8), (3, 8, 9), (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)]
    s = [0.022, 0.017, 0.028][k]
    v = v * np.array([s, s * rng.uniform(0.7, 1.0), s * 0.5]) * rng.uniform(0.85, 1.15, (12, 1))
    v[:, 2] = np.maximum(v[:, 2], -0.004) + 0.004
    tone = [hex_lin('#8a8070', 0.8), hex_lin('#787064', 0.8), hex_lin('#9a9082', 0.8)][k]
    cols = [tuple(c * rng.uniform(0.85, 1.12) for c in tone) for _ in range(12)]
    return v.astype(np.float32), f, np.array(cols, dtype=np.float32)
