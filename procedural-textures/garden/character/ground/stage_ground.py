"""GROUND builder stage (22 October character round). apply(options) works on the OPEN starting scene, is idempotent (it first removes what an
earlier run made and restores what that run changed) and touches only what the ground builder owns.

Plain words: it gives the lawn character. Grass tufts of twelve shapes in clumps with seed heads, a few small flowers and twigs (step 1); the
ground material with worn bare-earth paths and a real soft normal map (step 2); moss cushions and moss collars at rock feet (step 3); the
edges where lawn meets gravel kerb, stepping stones and plinth (step 4); fallen maple leaves (step 5); a slight tone variation of the dark
hedges (step 6).

options: steps (list, default all), maps_dir, seed, cameras (bool: add 'G6 ground cam n'), verbose.
"""
import os
import sys
import json
import time
import math

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import bpy  # noqa: E402
import numpy as np  # noqa: E402
import g6_common as C  # noqa: E402
from g6_common import PFX, inventory, cleanup  # noqa: E402

DEFAULTS = dict(steps=[1, 2, 3, 4, 5, 6], maps_dir=os.path.join(HERE, 'maps'), seed=7, cameras=True, verbose=True, tuft_budget_tris=60000,
                target_tufts=1150)


def log(o, *a):
    if o.get('verbose'):
        print('G6', *a, flush=True)


def apply(options=None):
    import importlib
    o = dict(DEFAULTS)
    o.update(options or {})
    T0 = time.time()
    for mod in ('g6_common', 'g6_world', 'g6_scatter', 'g6_tufts', 'g6_small', 'g6_ground', 'g6_moss', 'g6_edges', 'g6_leaves', 'g6_hedge'):
        try:
            importlib.reload(sys.modules[mod]) if mod in sys.modules else importlib.import_module(mod)
        except ImportError:
            pass
    before = inventory()
    cleanup()
    rep = dict(steps=o['steps'], seed=o['seed'])
    from g6_world import World
    world = World(o['maps_dir'], verbose=o['verbose'])
    rep['obstacle_objects'] = world.n_obstacle_objects
    feats = world.feature_points()
    fields = {k: world.dist_field(feats[k]) for k in ('rock', 'water', 'kerb', 'pathedge', 'plinth')}
    log(o, 'feature points', {k: len(v) for k, v in feats.items()}, 'in %.1fs' % (time.time() - T0))
    ctx = dict(o=o, world=world, feats=feats, fields=fields, rep=rep, rng=np.random.default_rng(o['seed']))
    steps = o['steps']
    if 2 in steps:
        import g6_ground
        g6_ground.add_ground_uvs()
        opts = g6_ground.default_options()
        opts.update(o.get('ground', {}))
        g6_ground.upgrade_ground_material(o['maps_dir'], opts)
        rep['ground'] = 'material Moss and earth upgraded; UVMap + MaskUV written'
    if 1 in steps:
        step1_grass(ctx)
    if 3 in steps:
        import g6_moss
        g6_moss.step3(ctx)
    if 4 in steps:
        import g6_edges
        g6_edges.step4(ctx)
    if 5 in steps:
        import g6_leaves
        g6_leaves.step5(ctx)
    if 6 in steps:
        import g6_hedge
        g6_hedge.step6(ctx)
    if 3 in steps or 4 in steps:
        import g6_moss
        g6_moss.finalize_moss_extra(ctx)
    if o.get('cameras'):
        make_cameras(ctx)
    if o.get('lineup'):
        make_lineup(ctx)
    changed = sorted(ob.name for ob in bpy.data.objects if not C.is_mine(ob) and any(ob.get(k) is not None for k in ('gnd_orig_mesh', 'gnd_uv_added', 'gnd_orig_mats', 'gnd_orig_group', 'gnd_col_added')))
    rep['objects_changed'] = changed
    rep['materials_changed'] = sorted(m.name for m in bpy.data.materials if m.get('gnd_rec') is not None)
    after = inventory()
    rep['objects_created'] = sorted(set(after['objects']) - set(before['objects']))
    rep['objects_removed'] = sorted(set(before['objects']) - set(after['objects']))
    rep['materials_created'] = sorted(set(after['materials']) - set(before['materials']))
    rep['node_groups_created'] = sorted(set(after['node_groups']) - set(before['node_groups']))
    rep['seconds'] = round(time.time() - T0, 1)
    log(o, 'done in', rep['seconds'], 's; created', len(rep['objects_created']), 'objects:', ', '.join(rep['objects_created'][:6]), '...; changed', len(rep['objects_changed']), 'owned objects and', len(rep['materials_changed']), 'owned materials; deleted: none')
    return rep


# ---------------------------------------------------------------------------------------------- step 1
def step1_grass(ctx):
    import g6_tufts as T
    import g6_small as S
    from g6_scatter import make_points_mesh, build_instancer_group
    o, world, rep, rng = ctx['o'], ctx['world'], ctx['rep'], ctx['rng']
    mat = S.tuft_material(PFX + 'tuft')
    src = T.build_sources(mat)
    cl = T.lawn_clumps(world, ctx['fields'], rng, target_tufts=o['target_tufts'], verbose=o['verbose'])
    tris_of = np.array([s['tris'] for s in src])
    # thin to the triangle budget (the old tufts: 31 440 triangles; the limit is twice that)
    n = len(cl['x'])
    total = tris_of[cl['pick']].sum()
    keep = np.ones(n, bool)
    if total > o['tuft_budget_tris']:
        order = rng.permutation(n)
        run = total
        for i in order:
            if run <= o['tuft_budget_tris']:
                break
            keep[i] = False
            run -= tris_of[cl['pick'][i]]
    for k in cl:
        cl[k] = cl[k][keep]
    n = len(cl['x'])
    total = int(tris_of[cl['pick']].sum())
    verts_of = np.array([s['verts'] for s in src])
    xyz = np.stack([cl['x'], cl['y'], cl['z']], axis=1)
    me = make_points_mesh(PFX + 'tuft points', xyz, {'g6_pick': ('INT', cl['pick']), 'g6_scale': ('FLOAT', cl['scale']), 'g6_rot': ('FLOAT', cl['rot'])})
    ng = build_instancer_group(PFX + 'tuft instancer', [s['obj'] for s in src])
    ctx['tuft_group'] = ng
    ctx['tuft_src'] = src
    ob = bpy.data.objects['Life / tufts']
    C.swap_mesh(ob, me)
    mod = next(m for m in ob.modifiers if m.type == 'NODES')
    ob['gnd_orig_group'] = mod.node_group.name
    mod.node_group = ng
    ob['g6_role_note'] = 'tuft field: points carry g6_pick / g6_scale / g6_rot'
    # statistics for the report and for acceptance test 17
    pick = cl['pick']
    seed_share = float(np.isin([src[p]['key'] for p in pick], T.SEED_HEAD_KEYS).mean())
    straw_share = float(np.isin([src[p]['tint'] for p in pick], T.STRAW_TIP).mean())
    red_share = float(np.array([src[p]['tint'] == 'red' for p in pick]).mean())
    heights = np.array([src[p]['height'] for p in pick]) * cl['scale']
    rep['tufts'] = dict(count=int(n), triangles=int(total), vertices=int(verts_of[pick].sum()), shapes=len(set(s['key'] for s in src)),
                        sources=len(src), scale_min=float(cl['scale'].min()), scale_max=float(cl['scale'].max()),
                        scale_ratio=float(cl['scale'].max() / cl['scale'].min()), seed_head_share=round(seed_share, 3),
                        straw_share=round(straw_share, 3), red_share=round(red_share, 3), height_min_m=round(float(heights.min()), 3),
                        height_max_m=round(float(heights.max()), 3), height_p5_m=round(float(np.percentile(heights, 5)), 3),
                        height_p95_m=round(float(np.percentile(heights, 95)), 3))
    seedp = []
    xs_, ys_ = world.grid()
    for i in range(n):
        if src[cl['pick'][i]]['key'] in T.SEED_HEAD_KEYS:
            ii = int(np.clip((cl['x'][i] + 10.0) / 0.1, 0, len(xs_) - 1)); jj = int(np.clip((cl['y'][i] + 8.0) / 0.1, 0, len(ys_) - 1))
            seedp.append((float(ctx['fields']['rock'][jj, ii]), float(cl['x'][i]), float(cl['y'][i]), float(cl['z'][i]), src[cl['pick'][i]]['key'], float(cl['scale'][i])))
    ctx['seed_pts'] = sorted(seedp)
    # flowers (20 to 60) and twigs (10 to 15)
    flowers_and_twigs(ctx, cl, mat)
    log(o, 'tufts', rep['tufts'])


def flowers_and_twigs(ctx, cl, tuft_mat):
    import g6_small as S
    from g6_tufts import Mesh
    from g6_common import mesh_from_arrays, add_object
    o, world, rep = ctx['o'], ctx['world'], ctx['rep']
    rng = np.random.default_rng(o['seed'] + 5)
    vmat = S.vcol_material(PFX + 'small things', rough=0.72, spec=0.22)
    # flower spots: one or two in each of these screen regions (hero lower right, veranda foreground, near the stones), free, visible, off the path
    regions = [('photo', 0.55, 1.0, 0.62, 0.95), ('photo', 0.55, 1.0, 0.62, 0.95), ('veranda', 0.0, 0.55, 0.62, 0.97), ('veranda', 0.3, 0.9, 0.55, 0.9),
               ('photo', 0.25, 0.65, 0.6, 0.85), ('photo', 0.05, 0.5, 0.65, 0.95)]
    pool = []
    for i in range(len(cl['x'])):
        x, y = float(cl['x'][i]), float(cl['y'][i])
        if world.mask_at(x, y) > 0.05 or not world.free(x, y, 0.25, zmin=-0.02):
            continue
        pool.append((x, y))
    for _ in range(900):
        x, y = float(rng.uniform(-8.5, 6.0)), float(rng.uniform(-7.0, 5.0))
        if world.visible(x, y, 0.1, margin=-0.02) and world.mask_at(x, y) < 0.05 and world.free(x, y, 0.25, zmin=0.0):
            pool.append((x, y))
    spots = []
    rng.shuffle(pool)
    for (cam, u0, u1, v0, v1) in regions:
        for (x, y) in pool:
            u, v, d = world.view_xy(cam, x, y)
            v = 1.0 - v                                      # picture row from the top
            if d > 0 and u0 < u < u1 and v0 < v < v1 and all((x - sx) ** 2 + (y - sy) ** 2 > 1.5 ** 2 for sx, sy, _ in spots):
                spots.append((x, y, cam))
                break
    m = Mesh()
    nfl = 0
    for k, (sx, sy, nm) in enumerate(spots):
        n = int(rng.integers(5, 10))
        az0 = rng.uniform(0, math.pi)
        d = np.array([math.cos(az0), math.sin(az0)])
        white = (k % 2 == 0)
        for j in range(n):
            t = (j / max(n - 1, 1) - 0.5) * rng.uniform(0.5, 0.9)
            x = sx + d[0] * t + rng.uniform(-0.06, 0.06)
            y = sy + d[1] * t + rng.uniform(-0.06, 0.06)
            if world.mask_at(x, y) > 0.1 or not world.free(x, y, 0.03, zmin=-0.02):
                continue
            z = world.ground_z(x, y)
            S.add_flower(m, (x, y, z - 0.004), rng, white=(white if rng.random() < 0.85 else not white), az=rng.uniform(0, 6.28))
            nfl += 1
    if nfl:
        v, f, c = m.arrays()
        me = mesh_from_arrays(PFX + 'flowers', v, f, cols=c)
        ob = add_object(PFX + 'flowers', me, 'growth', mats=[vmat])
        ob['g6_flower_count'] = nfl
    rep['flowers'] = dict(count=nfl, spots=len(spots))
    # twigs
    mt = Mesh()
    ntw = 0
    tries = 0
    while ntw < 13 and tries < 900:
        tries += 1
        i = int(rng.integers(0, len(cl['x'])))
        x = float(cl['x'][i]) + rng.uniform(-0.5, 0.5)
        y = float(cl['y'][i]) + rng.uniform(-0.5, 0.5)
        if not world.visible(x, y, 0.1, margin=-0.04) or world.mask_at(x, y) > 0.55 or not world.free(x, y, 0.2, zmin=-0.02):
            continue
        z = world.ground_z(x, y)
        S.add_twig(mt, (x, y, z), rng.uniform(0, math.pi), rng.uniform(0.26, 0.5), rng, lambda a, b: (world.ground_z(a, b) or 0.0))
        ntw += 1
    if ntw:
        v, f, c = mt.arrays()
        me = mesh_from_arrays(PFX + 'twigs', v, f, cols=c)
        ob = add_object(PFX + 'twigs', me, 'growth', mats=[vmat])
        ob['g6_twig_count'] = ntw
    rep['twigs'] = dict(count=ntw)


def look_at(ob, target):
    from mathutils import Vector
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def new_cam(name, loc, target, lens, clip_start=0.05):
    from mathutils import Vector
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = 36.0
    cd.clip_start = clip_start
    ob = bpy.data.objects.new(name, cd)
    C.get_collection().objects.link(ob)
    C.tag(ob, 'glow')            # role label only; a test camera
    ob['garden_role'] = 'camera'
    ob.location = Vector(loc)
    look_at(ob, target)
    return ob


def clear_view(world, p, target):
    """True when nothing solid stands between the camera spot and the target."""
    from mathutils import Vector
    d = Vector(target) - Vector(p)
    L = d.length
    if L < 1e-3:
        return False
    if world.near_hedge(p, 1.0):
        return False
    h = world.obs.ray_cast(Vector(p), d.normalized(), L - 0.1)
    return h[0] is None


def make_cameras(ctx):
    """test cameras 'G6 ground cam n' (the frozen hero / veranda cameras are not touched).
    1 a 3 x 2 m patch of lawn from 45 degrees; 2 a low view of a clump with seed heads near a rock; 3 the worn path; 4 the kerb join; 5 a moss collar."""
    world, rep = ctx['world'], ctx['rep']
    from mathutils import Vector
    made = []
    # 1 lawn patch (3 x 2 m) from 45 degrees above, 50 mm: distance so that about 3 m fits
    c1 = Vector((0.15, -2.9, 0.0))
    made.append(new_cam('G6 ground cam 1', (c1.x - 2.6, c1.y - 2.6, 3.2), c1, 50))
    # 2 a clump with seed heads near a rock: 1.4 m away, 0.45 m above the ground, 50 mm. prefers the chunky spike kind, tall and visible
    inbox = lambda p: -3.2 < p[1] < 2.6 and -3.6 < p[2] < 2.8          # the lit lawn between the pond, the lantern and the court
    sp = [p for p in (ctx.get('seed_pts') or []) if inbox(p) and p[4] == 'seed_spike' and p[5] >= 0.85 and world.visible(p[1], p[2], 0.2, margin=-0.05)] or \
        [p for p in (ctx.get('seed_pts') or []) if inbox(p)] or ctx.get('seed_pts') or []
    t2 = None
    for d, x, y, z, key, scl in sp:
        if d < 1.2:
            for ang in (-2.4, -0.8, 0.8, 2.4, 3.9, 5.5, 0.0, 3.14):
                p = Vector((x + math.cos(ang) * 1.5, y + math.sin(ang) * 1.5, 0.45))
                if world.free(p.x, p.y, 0.1, zmin=-0.02) and clear_view(world, p, (x, y, z + 0.30)):
                    t2 = (p, Vector((x, y, z + 0.30)))
                    break
        if t2:
            break
    if t2 is not None:
        made.append(new_cam('G6 ground cam 2', t2[0], t2[1], 50))
    # 3 the worn path along the desire line / stepping stones
    made.append(new_cam('G6 ground cam 3', (-0.9, -6.2, 1.0), (0.45, -4.0, 0.0), 32))
    # 4 the kerb join and spilled gravel: the first joint with a tuft
    kt = bpy.data.objects.get(PFX + 'kerb tufts')
    if kt is not None and len(kt.data.vertices):
        v = kt.data.vertices[min(3, len(kt.data.vertices) - 1)].co
        made.append(new_cam('G6 ground cam 4', (v.x - 0.9, v.y - 0.9, 0.7), (v.x, v.y, 0.04), 40))
    # 5 a moss collar at a rock foot: aim at the middle of one rock's collar cushions from a free spot 1.2 to 2 m away (several azimuths tried)
    focus = ctx.get('collar_focus', {})
    order = sorted(focus, key=lambda n: (0 if n == 'Gravel rock 0' else 1 if n.startswith('Rock ') else 2, n))
    done = False
    for pick in order:
        fx, fy, fz, rx, ry = focus[pick]
        ctr = Vector((fx, fy, 0.10))
        base = math.atan2(fy - ry, fx - rx)
        for dist in (2.2, 1.8, 2.6, 1.4):
            for da in (0.0, 0.5, -0.5, 1.0, -1.0, 1.6, -1.6, 2.4, -2.4, 3.1):
                p = Vector((fx + math.cos(base + da) * dist, fy + math.sin(base + da) * dist, 0.55))
                if world.free(p.x, p.y, 0.1, zmin=-0.02, gravel_ok=True) and clear_view(world, p, (fx, fy, 0.22)):
                    made.append(new_cam('G6 ground cam 5', p, Vector((fx, fy, 0.22)), 35))
                    done = True
                    break
            if done:
                break
        if done:
            break
    rep['cameras'] = [m.name for m in made]


def make_lineup(ctx):
    """TEST ONLY (option lineup=True): every tuft shape in two rows, three moss domes, on a plain olive-brown floor off to the side of the garden
    (the sun is a directional light, so the light is the same), with a camera 'G6 ground cam lineup'. Removed again by cleanup()."""
    import g6_tufts as T
    from g6_common import add_object, mesh_from_arrays
    src = ctx.get('tuft_src') or []
    ox, oy = 40.0, 0.0
    verts = [(ox - 4, oy - 3, 0.0), (ox + 4, oy - 3, 0.0), (ox + 4, oy + 3, 0.0), (ox - 4, oy + 3, 0.0)]
    me = mesh_from_arrays(PFX + 'lineup floor', verts, [(0, 1, 2, 3)])
    mat = bpy.data.materials.new(PFX + 'lineup floor')
    mat.use_nodes = True
    bs = mat.node_tree.nodes['Principled BSDF']
    bs.inputs['Base Color'].default_value = (0.115, 0.100, 0.058, 1.0)
    bs.inputs['Roughness'].default_value = 0.92
    add_object(PFX + 'lineup floor', me, 'ground.earth', mats=[mat])
    n = 0
    for i, s in enumerate(src):
        row, col = divmod(i, 8)
        x, y = ox - 1.82 + col * 0.52, oy + 0.30 - row * 0.55
        ob = bpy.data.objects.new(PFX + 'lineup tuft %02d' % i, s['obj'].data)
        C.get_collection().objects.link(ob)
        C.tag(ob, 'growth')
        ob.location = (x, y, 0.0)
        ob.rotation_euler = (0, 0, 0.7 * i)
        n += 1
    for k in range(3):
        mo = bpy.data.objects['Life / moss sources %d' % (k * 2)]
        ob = bpy.data.objects.new(PFX + 'lineup moss %d' % k, mo.data)
        C.get_collection().objects.link(ob)
        C.tag(ob, 'growth')
        ob.scale = (0.10 + 0.035 * k,) * 3
        ob.location = (ox - 1.0 + k * 1.0, oy - 1.15, 0.0)
    ld = bpy.data.lights.new(PFX + 'lineup light', 'SUN')
    ld.energy = 3.0
    ld.color = (1.0, 0.92, 0.82)
    lo = bpy.data.objects.new(PFX + 'lineup light', ld)
    C.get_collection().objects.link(lo)
    C.tag(lo, 'glow')
    lo.rotation_euler = (math.radians(52), 0, math.radians(-25))
    new_cam('G6 ground cam lineup', (ox, oy - 3.3, 0.85), (ox, oy - 0.25, 0.20), 30)
    ctx['rep']['lineup'] = n
