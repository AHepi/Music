"""GROUND builder, step 2: the ground itself. Material 'Moss and earth' keeps its mottled olive-and-brown look and gets
 (1) WORN PATHS from a top-down mask picture (bare reddish earth with ragged grass edges, a few pebble specks),
 (2) a real soft normal map (clods, 3 m tile) in place of the scan's bump as the main relief, plus a slight footfall dish on the paths.
UV maps: 'UVMap' planar (x, y) / 3 m, 'MaskUV' (x, y) / (22, 21) with the ground's corner at 0,0 of the mask.
"""
import os
import bpy
from mathutils import Vector
from g6_common import (N, link, load_image, normal_chain, unlink_input, set_default, hex_lin, planar_uv, track_uv, PFX)

GROUND_OBJECTS = ('Astra / Courtyard receiving ground', 'Courtyard ground source')


def new_mix_color(nt, name, loc):
    n = N(nt, 'ShaderNodeMix', name, loc)
    n.data_type = 'RGBA'
    n.blend_type = 'MIX'
    n.clamp_factor = True
    return n


def new_mix_float(nt, name, loc):
    n = N(nt, 'ShaderNodeMix', name, loc)
    n.data_type = 'FLOAT'
    n.clamp_factor = True
    return n


def mixout(n):
    return next(o for o in n.outputs if o.enabled)


MIX_FAC, MIX_A_F, MIX_B_F, MIX_A_C, MIX_B_C = 0, 2, 3, 6, 7


def add_ground_uvs():
    for nm in GROUND_OBJECTS:
        ob = bpy.data.objects.get(nm)
        if ob is None:
            continue
        for lay, tile, off in (('UVMap', (3.0, 3.0), (0.0, 0.0)), ('MaskUV', (22.0, 21.0), (0.5, 8.5 / 21.0))):
            track_uv(ob, lay)
            planar_uv(ob.data, lay, tile, off, matrix=ob.matrix_world)


def upgrade_ground_material(maps_dir, opts):
    mat = bpy.data.materials['Moss and earth']
    nt = mat.node_tree
    bsdf = nt.nodes['Principled BSDF']
    gm = nt.nodes['WK groundmoss']
    img_mask = load_image(os.path.join(maps_dir, 'path_mask.png'), 'G6 path_mask', non_color=True)
    img_nrm = load_image(os.path.join(maps_dir, 'ground_normal.png'), 'G6 ground_normal', non_color=True)

    # ---- the path mask: R bare earth, G footfall dish, B pebble specks (UV = MaskUV)
    uvm = N(nt, 'ShaderNodeUVMap', 'mask UV', (-1700, -900))
    uvm.uv_map = 'MaskUV'
    tm = N(nt, 'ShaderNodeTexImage', 'path mask', (-1500, -900))
    tm.image = img_mask
    tm.interpolation = 'Linear'
    tm.extension = 'EXTEND'
    link(nt, uvm, 'UV', tm, 'Vector')
    sep = N(nt, 'ShaderNodeSeparateColor', 'mask split', (-1250, -900))
    link(nt, tm, 'Color', sep, 'Color')

    # ---- crisp, ragged edge at any distance: the 1 cm picture is bent by a fine noise and re-sharpened (no stair-steps up close)
    geo0 = N(nt, 'ShaderNodeNewGeometry', 'edge geo', (-1700, -1050))
    ez = N(nt, 'ShaderNodeTexNoise', 'edge noise', (-1500, -1050))
    ez.noise_dimensions = '3D'
    ez.inputs['Scale'].default_value = 8.0                   # FIX ROUND: a slow 12 cm wave, not 3 cm jaggies
    ez.inputs['Detail'].default_value = 1.5
    ez.inputs['Roughness'].default_value = 0.55
    link(nt, geo0, 'Position', ez, 'Vector')
    ea = N(nt, 'ShaderNodeMath', 'edge bend', (-1250, -1050))
    ea.operation = 'ADD'
    link(nt, sep, 'Red', ea, 0)
    eb = N(nt, 'ShaderNodeMath', 'edge noise centred', (-1250, -1200))
    eb.operation = 'MULTIPLY_ADD'
    eb.inputs[1].default_value = 0.30
    eb.inputs[2].default_value = -0.15
    link(nt, ez, 'Fac', eb, 0)
    link(nt, eb, 0, ea, 1)
    bare = N(nt, 'ShaderNodeMapRange', 'bare earth', (-1050, -1050))
    bare.interpolation_type = 'SMOOTHSTEP'
    bare.inputs['From Min'].default_value = 0.24             # FIX ROUND: wider, softer ramp from grass to earth
    bare.inputs['From Max'].default_value = 0.78
    link(nt, ea, 0, bare, 'Value')
    BARE = bare.outputs['Result']

    # ---- bare earth colour: reddish brown with soft blotches (darker than the raked gravel)
    geo = N(nt, 'ShaderNodeNewGeometry', 'earth geo', (-1700, -1250))
    nz = N(nt, 'ShaderNodeTexNoise', 'earth blotch', (-1500, -1250))
    nz.noise_dimensions = '3D'
    nz.inputs['Scale'].default_value = 1.7
    nz.inputs['Detail'].default_value = 2.0
    nz.inputs['Roughness'].default_value = 0.5
    link(nt, geo, 'Position', nz, 'Vector')
    ramp = N(nt, 'ShaderNodeValToRGB', 'earth ramp', (-1250, -1250))
    ramp.color_ramp.elements[0].position = 0.30
    ramp.color_ramp.elements[1].position = 0.70
    ramp.color_ramp.elements[0].color = (*opts['earth_dark'], 1.0)
    ramp.color_ramp.elements[1].color = (*opts['earth_light'], 1.0)
    link(nt, nz, 'Fac', ramp, 'Fac')
    # pebble specks: pale warm grey, only inside the bare earth
    spk = new_mix_color(nt, 'earth specks', (-1000, -1250))
    spk.inputs[MIX_B_C].default_value = (*opts['speck'], 1.0)
    link(nt, sep, 'Blue', spk, MIX_FAC)
    link(nt, ramp, 'Color', spk, MIX_A_C)

    # ---- FIX ROUND: soft modelling of the bare earth. Lighter dusty middle, darker damp rim (from the mask's own red ramp), a slow light/dark blotch
    # (about 50 cm) and a fine one (15 cm), and a lighter, compacted footfall dish (green channel).
    ctr = N(nt, 'ShaderNodeMapRange', 'earth centre tone', (-1000, -1500))
    ctr.interpolation_type = 'SMOOTHSTEP'
    ctr.inputs['From Min'].default_value = 0.40
    ctr.inputs['From Max'].default_value = 1.0
    ctr.inputs['To Min'].default_value = opts['earth_rim']
    ctr.inputs['To Max'].default_value = opts['earth_middle']
    link(nt, sep, 'Red', ctr, 'Value')
    nz_b = N(nt, 'ShaderNodeTexNoise', 'earth slow blotch', (-1500, -1450))
    nz_b.noise_dimensions = '3D'
    nz_b.inputs['Scale'].default_value = 2.2
    nz_b.inputs['Detail'].default_value = 2.0
    nz_b.inputs['Roughness'].default_value = 0.5
    link(nt, geo, 'Position', nz_b, 'Vector')
    mr_b = N(nt, 'ShaderNodeMapRange', 'earth slow range', (-1250, -1450))
    mr_b.inputs['From Min'].default_value = 0.32
    mr_b.inputs['From Max'].default_value = 0.68
    mr_b.inputs['To Min'].default_value = 1.0 - opts['earth_blotch']
    mr_b.inputs['To Max'].default_value = 1.0 + opts['earth_blotch']
    link(nt, nz_b, 'Fac', mr_b, 'Value')
    nz_f = N(nt, 'ShaderNodeTexNoise', 'earth fine blotch', (-1500, -1650))
    nz_f.noise_dimensions = '3D'
    nz_f.inputs['Scale'].default_value = 6.5
    nz_f.inputs['Detail'].default_value = 1.5
    nz_f.inputs['Roughness'].default_value = 0.5
    link(nt, geo, 'Position', nz_f, 'Vector')
    mr_f = N(nt, 'ShaderNodeMapRange', 'earth fine range', (-1250, -1650))
    mr_f.inputs['From Min'].default_value = 0.30
    mr_f.inputs['From Max'].default_value = 0.70
    mr_f.inputs['To Min'].default_value = 1.0 - opts['earth_fine']
    mr_f.inputs['To Max'].default_value = 1.0 + opts['earth_fine']
    link(nt, nz_f, 'Fac', mr_f, 'Value')
    dsh = N(nt, 'ShaderNodeMath', 'earth dish tone', (-1000, -1650))
    dsh.operation = 'MULTIPLY_ADD'
    dsh.inputs[1].default_value = opts['earth_dish_light']
    dsh.inputs[2].default_value = 1.0
    link(nt, sep, 'Green', dsh, 0)
    m1 = N(nt, 'ShaderNodeMath', 'earth tone a', (-800, -1500))
    m1.operation = 'MULTIPLY'
    link(nt, ctr, 'Result', m1, 0)
    link(nt, mr_b, 'Result', m1, 1)
    m2 = N(nt, 'ShaderNodeMath', 'earth tone b', (-640, -1550))
    m2.operation = 'MULTIPLY'
    link(nt, m1, 0, m2, 0)
    link(nt, mr_f, 'Result', m2, 1)
    m3 = N(nt, 'ShaderNodeMath', 'earth tone c', (-480, -1600))
    m3.operation = 'MULTIPLY'
    link(nt, m2, 0, m3, 0)
    link(nt, dsh, 0, m3, 1)
    wc = N(nt, 'ShaderNodeCombineXYZ', 'earth tone rgb', (-320, -1600))
    link(nt, m3, 0, wc, 'X')
    link(nt, m3, 0, wc, 'Y')
    wb = N(nt, 'ShaderNodeMath', 'earth tone blue', (-480, -1750))         # a little warmer where it is lighter (blue follows 0.93 of the others)
    wb.operation = 'MULTIPLY'
    wb.inputs[1].default_value = 0.94
    link(nt, m3, 0, wb, 0)
    link(nt, wb, 0, wc, 'Z')
    etone = new_mix_color(nt, 'earth toned', (-160, -1500))
    etone.blend_type = 'MULTIPLY'
    etone.inputs[MIX_FAC].default_value = 1.0
    link(nt, mixout(spk), etone, MIX_A_C)
    link(nt, wc, 'Vector', etone, MIX_B_C)

    # ---- FIX ROUND: gentle mottling of the lawn colour: slow olive / warm-brown blotches (about 1 m) and a finer one (about 20 cm), neutral on average
    lg = N(nt, 'ShaderNodeNewGeometry', 'lawn geo', (-1700, -1900))
    ln1 = N(nt, 'ShaderNodeTexNoise', 'lawn slow blotch', (-1500, -1900))
    ln1.noise_dimensions = '3D'
    ln1.inputs['Scale'].default_value = 1.15
    ln1.inputs['Detail'].default_value = 3.0
    ln1.inputs['Roughness'].default_value = 0.55
    link(nt, lg, 'Position', ln1, 'Vector')
    lr = N(nt, 'ShaderNodeValToRGB', 'lawn slow ramp', (-1250, -1900))
    el = lr.color_ramp.elements
    el[0].position, el[0].color = 0.30, (0.82, 0.88, 0.80, 1.0)
    el[1].position, el[1].color = 0.70, (1.14, 1.08, 0.90, 1.0)
    mid = lr.color_ramp.elements.new(0.5)
    mid.color = (1.0, 1.0, 1.0, 1.0)
    link(nt, ln1, 'Fac', lr, 'Fac')
    ln2 = N(nt, 'ShaderNodeTexNoise', 'lawn fine blotch', (-1500, -2100))
    ln2.noise_dimensions = '3D'
    ln2.inputs['Scale'].default_value = 5.0
    ln2.inputs['Detail'].default_value = 2.5
    ln2.inputs['Roughness'].default_value = 0.5
    link(nt, lg, 'Position', ln2, 'Vector')
    lm2 = N(nt, 'ShaderNodeMapRange', 'lawn fine range', (-1250, -2100))
    lm2.inputs['From Min'].default_value = 0.32
    lm2.inputs['From Max'].default_value = 0.68
    lm2.inputs['To Min'].default_value = 1.0 - opts['lawn_fine']
    lm2.inputs['To Max'].default_value = 1.0 + opts['lawn_fine']
    link(nt, ln2, 'Fac', lm2, 'Value')
    lw = N(nt, 'ShaderNodeCombineXYZ', 'lawn fine rgb', (-1000, -2100))
    for ax in ('X', 'Y', 'Z'):
        link(nt, lm2, 'Result', lw, ax)
    lmix1 = new_mix_color(nt, 'lawn mottle a', (-800, -1900))
    lmix1.blend_type = 'MULTIPLY'
    lmix1.inputs[MIX_FAC].default_value = opts['lawn_mottle']
    link(nt, gm, 'Colour', lmix1, MIX_A_C)
    link(nt, lr, 'Color', lmix1, MIX_B_C)
    lmix2 = new_mix_color(nt, 'lawn mottle b', (-600, -1900))
    lmix2.blend_type = 'MULTIPLY'
    lmix2.inputs[MIX_FAC].default_value = 1.0
    link(nt, mixout(lmix1), lmix2, MIX_A_C)
    link(nt, lw, 'Vector', lmix2, MIX_B_C)

    # ---- colour: grass colour (mottled) -> earth by the mask
    ca = new_mix_color(nt, 'path colour', (-300, -700))
    unlink_input(mat, 'Principled BSDF', 'Base Color')
    link(nt, mixout(lmix2), ca, MIX_A_C)
    link(nt, mixout(etone), ca, MIX_B_C)
    link(nt, BARE, ca, MIX_FAC)
    link(nt, mixout(ca), bsdf, 'Base Color')
    # ---- roughness: earth is matte
    cr = new_mix_float(nt, 'path roughness', (-300, -900))
    unlink_input(mat, 'Principled BSDF', 'Roughness')
    link(nt, gm, 'Roughness', cr, MIX_A_F)
    cr.inputs[MIX_B_F].default_value = 0.94
    link(nt, BARE, cr, MIX_FAC)
    link(nt, mixout(cr), bsdf, 'Roughness')

    # ---- normal: soft clods (real normal map) -> footfall dish -> the scan's bump (reduced) -> the weathering kit chain (unchanged)
    nm, mp = normal_chain(nt, 'ground', img_nrm, 'UVMap', opts['normal_strength'], (1.0, 1.0, 1.0), loc=(-1700, -300))
    # one Bump (the scan's own relief, kept near its old strength but fed by the real normal map) whose height is the scan height, flattened on
    # the paths, minus a footfall dish. Dish depth 4 mm; Bump distance 0.03 m.
    grp = nt.nodes['Group']
    bump = nt.nodes['Bump']
    flat = N(nt, 'ShaderNodeMath', 'path flatten', (-1250, -700))          # 1 - 0.75 * bare
    flat.operation = 'MULTIPLY_ADD'
    flat.inputs[1].default_value = -0.75
    flat.inputs[2].default_value = 1.0
    link(nt, BARE, flat, 0)
    sc = N(nt, 'ShaderNodeMath', 'scan height flat', (-1000, -700))
    sc.operation = 'MULTIPLY'
    link(nt, grp, 'Height', sc, 0)
    link(nt, flat, 0, sc, 1)
    dish = N(nt, 'ShaderNodeMath', 'dish term', (-1000, -850))           # - 0.14 * footfall (scaled by the bump distance)
    dish.operation = 'MULTIPLY'
    dish.inputs[1].default_value = -opts['dish_depth']
    link(nt, sep, 'Green', dish, 0)
    tot = N(nt, 'ShaderNodeMath', 'height total', (-760, -760))
    tot.operation = 'ADD'
    link(nt, sc, 0, tot, 0)
    link(nt, dish, 0, tot, 1)
    unlink_input(mat, 'Bump', 'Height')
    link(nt, tot, 0, bump, 'Height')
    link(nt, nm, 'Normal', bump, 'Normal')
    set_default(mat, 'Bump', 'Strength', opts['scan_bump'])
    return mat


def default_options():
    return dict(
        earth_dark=hex_lin('#664d3b', 0.52),        # albedo (linear); tuned on the hero picture so the path reads reddish brown and darker than the gravel
        earth_light=hex_lin('#84684d', 0.68),
        speck=hex_lin('#7e7062', 0.7),
        earth_rim=0.82, earth_middle=1.22, earth_blotch=0.13, earth_fine=0.06, earth_dish_light=0.10,
        lawn_mottle=1.0, lawn_fine=0.06,
        normal_strength=0.85,
        dish_depth=0.16,
        scan_bump=0.50,
    )


# ------------------------------------------------------------------------------------------------ FIX ROUND: a few real pebbles on the worn path
def pebble_arrays(seed, sx, sy, sz):
    """a low-poly, rounded little stone (icosphere, 42 vertices, flat shaded), flattened, lighter on top. Radius 1 (scaled by the instance)."""
    import bmesh
    import numpy as np
    from g6_common import lerp3
    rng = np.random.default_rng(seed)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    verts = []
    for v in bm.verts:
        k = 1.0 + rng.uniform(-0.05, 0.05)
        verts.append((v.co.x * sx * k, v.co.y * sy * k, v.co.z * sz * k))
    faces = [tuple(v.index for v in f.verts) for f in bm.faces]
    bm.free()
    verts = np.array(verts, dtype=np.float32)
    lo, hi = hex_lin('#38312a'), hex_lin('#645a4c')
    zmin, zmax = verts[:, 2].min(), verts[:, 2].max()
    cols = []
    j = rng.uniform(0.92, 1.08)
    for v in verts:
        t = (v[2] - zmin) / (zmax - zmin + 1e-6)
        c = lerp3(lo, hi, t ** 0.9)
        cols.append(tuple(min(1.0, x * j * rng.uniform(0.97, 1.03)) for x in c) + (1.0,))
    return verts, faces, np.array(cols, dtype=np.float32)


def path_pebbles(ctx):
    """FIX ROUND: 'a few pebbles' on the bare earth, as in the concept: 4 stone shapes, 14 small groups of 3 to 6 (2 to 6 cm radius), half sunk into the
    ground, only where the mask is fully bare and a camera can see."""
    import math
    import numpy as np
    from g6_common import mesh_from_arrays, add_object, PFX
    from g6_scatter import make_points_mesh, build_instancer_group
    from g6_small import vcol_material
    o, world, rep = ctx['o'], ctx['world'], ctx['rep']
    rng = np.random.default_rng(o['seed'] + 91)
    mat = vcol_material(PFX + 'path pebbles', rough=0.82, spec=0.2)
    srcs = []
    for k, (sx, sy, sz) in enumerate([(1.0, 0.86, 0.74), (1.0, 0.76, 0.66), (0.92, 0.92, 0.80), (1.0, 0.82, 0.60)]):
        v, f, c = pebble_arrays(700 + k, sx, sy, sz)
        me = mesh_from_arrays(PFX + 'path pebble %d' % k, v, f, cols=c, smooth=True)
        srcs.append(add_object(PFX + 'path pebble %d' % k, me, 'growth', mats=[mat], hide_render=True))
    m = world.path_mask()
    nn = m.shape[0]
    rr_, cc_ = np.where(m > 0.80)
    if len(rr_) == 0:
        rep['path_pebbles'] = dict(count=0)
        return
    pool = []
    for q in rng.permutation(len(rr_))[:6000]:
        x = -11.0 + (cc_[q] + 0.5) / nn * 22.0
        y = -8.5 + (1.0 - (rr_[q] + 0.5) / nn) * 21.0
        if world.visible(x, y, 0.05, margin=-0.02) and world.free(x, y, 0.06, zmin=-0.02):
            pool.append((x, y))
    centres = []
    for (x, y) in pool:
        if all(math.hypot(x - cx, y - cy) > 0.8 for cx, cy in centres):
            centres.append((x, y))
        if len(centres) >= 18:
            break
    X, Y, Z, K, S, RT = [], [], [], [], [], []
    for (cx, cy) in centres:
        for _ in range(int(rng.integers(4, 9))):
            a = rng.uniform(0, 6.28)
            d = 0.36 * math.sqrt(rng.uniform(0.02, 1.0))
            x, y = cx + math.cos(a) * d, cy + math.sin(a) * d
            if world.mask_at(x, y) < 0.7 or not world.free(x, y, 0.04, zmin=-0.02):
                continue
            r = 0.030 + 0.042 * rng.beta(1.3, 2.4)
            gz = world.ground_z(x, y)
            if gz is None:
                continue
            X.append(x); Y.append(y); Z.append(gz - 0.15 * r); K.append(int(rng.integers(0, 4))); S.append(r); RT.append(rng.uniform(0, 6.28))
    if not X:
        rep['path_pebbles'] = dict(count=0)
        return
    me = make_points_mesh(PFX + 'path pebble points', np.stack([X, Y, Z], axis=1), {'g6_pick': ('INT', np.array(K)), 'g6_scale': ('FLOAT', np.array(S)),
                                                                                    'g6_rot': ('FLOAT', np.array(RT))})
    ng = build_instancer_group(PFX + 'path pebble instancer', srcs)
    ob = add_object(PFX + 'path pebbles', me, 'growth')
    md = ob.modifiers.new('G6 ground / path pebble instancer', 'NODES')
    md.node_group = ng
    rep['path_pebbles'] = dict(count=len(X), groups=len(centres), radius_min=float(min(S)), radius_max=float(max(S)))
