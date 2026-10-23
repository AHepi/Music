"""Forest: tree library, tree placement, undergrowth, grass scatter."""
import math, time
import numpy as np
import bpy
from mathutils import kdtree
from common import *
import layout, plants, props, assemble, terrain

LIB = {}      # name -> mesh datablock
SUN_AZ = 222.0

def road_kd():
    pts = np.concatenate([r.P[::2] for r in layout.ROADS.values()])
    kd = kdtree.KDTree(len(pts))
    for i, p in enumerate(pts):
        kd.insert((p[0], p[1], 0.0), i)
    kd.balance()
    return kd

def build_library(log=None):
    pm = assemble.plant_mats()
    bm = assemble.all_building_mats()
    for me in list(bpy.data.meshes):
        if me.name.startswith('LIB_'):
            bpy.data.meshes.remove(me)
    LIB.clear()
    t0 = time.time()
    spec = {
        # near variants
        'oak_a': plants.deciduous(101, H=13.5, spread=1.05, trunk_r=0.42, trunk_frac=0.32, elev=(0.25, 0.85), n_limbs=7),
        'oak_b': plants.deciduous(102, H=15.0, spread=1.10, trunk_r=0.46, trunk_frac=0.30, elev=(0.2, 0.8), n_limbs=8),
        'oak_c': plants.deciduous(103, H=12.0, spread=0.95, trunk_r=0.38, trunk_frac=0.34, elev=(0.3, 0.9), n_limbs=7, lean=0.03),
        'beech_a': plants.deciduous(111, H=18.0, spread=0.62, trunk_r=0.34, trunk_frac=0.45, elev=(0.6, 1.1), n_limbs=8),
        'beech_b': plants.deciduous(112, H=16.0, spread=0.68, trunk_r=0.31, trunk_frac=0.42, elev=(0.55, 1.05), n_limbs=8, lean=0.025),
        'birch_a': plants.deciduous(121, H=13.0, spread=0.52, trunk_r=0.17, trunk_frac=0.55, elev=(0.7, 1.2), n_limbs=8, birch=True, leaf_size=(0.2, 0.28), leaves_per=60),
        'birch_b': plants.deciduous(122, H=11.0, spread=0.55, trunk_r=0.15, trunk_frac=0.5, elev=(0.6, 1.2), n_limbs=7, birch=True, leaf_size=(0.2, 0.28), leaves_per=60, lean=0.04),
        'spruce_a': plants.spruce(131, H=16.0),
        'spruce_b': plants.spruce(132, H=19.0),
        'spruce_c': plants.spruce(133, H=13.0),
        'pine_a': plants.pine(141, H=18.0),
        'pine_b': plants.pine(142, H=15.0),
        'dead_a': plants.dead_tree(151, H=8.5),
        # far variants: fewer, larger leaf cards
        'oak_far': plants.deciduous(201, H=14.0, spread=1.05, trunk_r=0.42, trunk_frac=0.32, n_limbs=6, leaf_size=(0.7, 0.95), leaves_per=16, clusters=2),
        'beech_far': plants.deciduous(211, H=17.0, spread=0.65, trunk_r=0.33, trunk_frac=0.44, elev=(0.6, 1.1), n_limbs=7, leaf_size=(0.7, 0.95), leaves_per=16, clusters=2),
        'birch_far': plants.deciduous(221, H=12.0, spread=0.52, trunk_r=0.16, trunk_frac=0.52, elev=(0.7, 1.2), n_limbs=7, birch=True, leaf_size=(0.5, 0.7), leaves_per=16, clusters=2),
        'bush_a': plants.bush(301, r=1.0), 'bush_b': plants.bush(302, r=0.8, leaves=700), 'bush_c': plants.bush(303, r=1.3, leaves=1100),
        'fern_a': plants.fern(311), 'fern_b': plants.fern(312, fronds=11, length=0.9), 'fern_c': plants.fern(313, fronds=8, length=0.65),
    }
    info = {}
    for nm, mb in spec.items():
        LIB[nm] = mb.build('LIB_' + nm, pm)
        info[nm] = len(LIB[nm].polygons)
        if log is not None:
            log.append('lib %s %d %.1fs' % (nm, info[nm], time.time() - t0))
    # rocks and logs
    rng = np.random.RandomState(77)
    for i in range(4):
        LIB['rock_%d' % i] = props.boulder(rng, 0.4 + 0.25 * i).build('LIB_rock_%d' % i, bm)
    for i in range(3):
        mb = MB(); mb.rng = rng
        L = 3.5 + i
        props.log_piece(mb, (-L / 2, 0, 0.25), (L / 2, 0.3, 0.2), 0.26 - 0.03 * i, rng)
        for k in range(3):
            a = rng.uniform(0, 6.28)
            p0 = np.array([rng.uniform(-L / 3, L / 3), 0, 0.25])
            mb.tube([p0 + np.array([0, 0, 0.1]), p0 + np.array([math.cos(a) * 0.5, math.sin(a) * 0.5, 0.3])], 0.02, sides=4, mat=11, cap1=True)
        LIB['log_%d' % i] = mb.build('LIB_log_%d' % i, bm)
    stump = MB(); stump.rng = rng
    props.log_piece(stump, (0, 0, -0.1), (0, 0, 0.55), 0.3, rng)
    LIB['stump'] = stump.build('LIB_stump', bm)
    return info

# ---------------------------------------------------------------------------- placement
def candidate_points(rng, n, extent):
    return np.stack([rng.uniform(-extent, extent, n), rng.uniform(-extent, extent, n)], axis=1)

def poisson(pts, rmin, rng):
    cell = rmin.max()
    grid = {}
    keep = []
    for i in range(len(pts)):
        x, y = pts[i]
        gx, gy = int(x // cell), int(y // cell)
        ok = True
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for j in grid.get((gx + dx, gy + dy), ()):
                    d = math.hypot(x - pts[j][0], y - pts[j][1])
                    if d < 0.5 * (rmin[i] + rmin[j]):
                        ok = False
                        break
                if not ok:
                    break
            if not ok:
                break
        if ok:
            grid.setdefault((gx, gy), []).append(i)
            keep.append(i)
    return np.array(keep, dtype=int)

def place_trees(log=None, seed=2024, n_cand=26000, extent=160.0):
    assemble.ensure_layout()
    rng = np.random.RandomState(seed)
    coll = get_coll('Trees')
    for ob in list(coll.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    pts = candidate_points(rng, n_cand, extent)
    X, Y = pts[:, 0], pts[:, 1]
    r = np.hypot(X - 18.0, Y - 8.0)
    z0, clearing = layout.base_height(X, Y)
    # forest probability: thinner far away
    pf = np.where(r < 125, 1.0, np.where(r < 160, 0.55, 0.0))
    ok = (clearing < 0.35) & (rng.rand(n_cand) < pf)
    kd = road_kd()
    droad = np.array([kd.find((x, y, 0.0))[2] for x, y in pts[ok]]) if ok.any() else np.array([])
    idx = np.nonzero(ok)[0]
    good = droad > 4.6
    # near the road edge the forest is a little open, deeper in it gets denser
    idx = idx[good]
    B = layout.BUILDINGS
    for b in B:
        m = np.hypot(X[idx] - b['x'], Y[idx] - b['y']) > (max(b['W'], b['D']) * 0.5 + 8.5)
        idx = idx[m]
    # keep the camera positions and the sunlit fronts of the hero buildings clear of trees
    import cams
    for nm, d in cams.plan().items():
        if nm == 'Cam_Aerial':
            continue
        m = np.hypot(X[idx] - d['loc'][0], Y[idx] - d['loc'][1]) > 9.5
        idx = idx[m]
    sun_h = np.array([math.sin(math.radians(SUN_AZ)), math.cos(math.radians(SUN_AZ))])
    bmap = {b['name']: b for b in B}
    for nm in ('Cottage1', 'Stable', 'Cottage3', 'Cottage4'):
        b = bmap[nm]
        rel = np.stack([X[idx] - b['x'], Y[idx] - b['y']], 1)
        along = rel @ sun_h
        perp = rel @ np.array([-sun_h[1], sun_h[0]])
        m = ~((along > 2) & (along < 34) & (np.abs(perp) < 11))
        idx = idx[m]
    # species by large-scale noise: conifer patches
    cn = fbm2(X[idx] * 0.02, Y[idx] * 0.02, 3, seed=9)
    rng.shuffle(idx)
    P = pts[idx]
    rmin = 3.4 + 1.2 * rng.rand(len(idx))
    keep = poisson(P, rmin, rng)
    P = P[keep]
    cn = fbm2(P[:, 0] * 0.02, P[:, 1] * 0.02, 3, seed=9)
    rr = np.hypot(P[:, 0] - 18.0, P[:, 1] - 8.0)
    n_made = {}
    coll_objs = []
    for i, (x, y) in enumerate(P):
        u = rng.rand()
        conif = cn[i] + 0.15 * rng.randn() > 0.12
        far = rr[i] > 95
        if conif:
            nm = rng.choice(['spruce_a', 'spruce_b', 'spruce_c', 'spruce_a', 'pine_a', 'pine_b'])
        else:
            if u < 0.03:
                nm = 'dead_a'
            elif far:
                nm = rng.choice(['oak_far', 'beech_far', 'birch_far', 'oak_far', 'beech_far'])
            else:
                nm = rng.choice(['oak_a', 'oak_b', 'oak_c', 'beech_a', 'beech_b', 'birch_a', 'birch_b', 'oak_a', 'beech_a'])
        sc = float(np.clip(rng.lognormal(0.0, 0.16), 0.7, 1.4))
        z = float(layout.terrain_eval(np.array([x]), np.array([y]), do_hoof=False)['z'][0]) - 0.15
        ob = bpy.data.objects.new('Tree_%04d_%s' % (i, nm), LIB[nm])
        coll.objects.link(ob)
        ob.location = (x, y, z)
        ob.rotation_euler = (rng.normal(0, 0.025), rng.normal(0, 0.025), rng.uniform(0, 6.283))
        ob.scale = (sc, sc, sc * rng.uniform(0.92, 1.1))
        n_made[nm] = n_made.get(nm, 0) + 1
    # hand-placed village trees
    village = [(25.5, 14.5, 'oak_b', 1.1), (-24.0, -6.0, 'oak_a', 1.05), (0.5, -30.0, 'beech_a', 1.0), (50.0, -2.0, 'oak_c', 1.0), (30.0, 24.0, 'birch_a', 1.0),
               (33.0, 26.0, 'birch_b', 0.9), (-6.0, 32.0, 'oak_a', 1.0), (47.0, 20.0, 'beech_b', 1.0), (-17.5, -2.0, 'birch_b', 0.9), (4.0, 46.0, 'spruce_c', 1.0),
               (28.0, 47.0, 'oak_c', 0.9), (-31.0, 0.5, 'oak_c', 1.0), (66.0, 3.0, 'beech_a', 1.0), (2.0, -42.0, 'oak_b', 1.1)]
    for k, (x, y, nm, sc) in enumerate(village):
        z = float(layout.terrain_eval(np.array([x]), np.array([y]), do_hoof=False)['z'][0]) - 0.15
        ob = bpy.data.objects.new('VTree_%02d_%s' % (k, nm), LIB[nm])
        coll.objects.link(ob)
        ob.location = (x, y, z)
        ob.rotation_euler = (0, 0, rng.uniform(0, 6.283))
        ob.scale = (sc, sc, sc)
    if log is not None:
        log.append('trees %d %s' % (len(P), n_made))
    return {'n': len(P), 'species': n_made}

def place_undergrowth(log=None, seed=808):
    assemble.ensure_layout()
    rng = np.random.RandomState(seed)
    coll = get_coll('Undergrowth')
    for ob in list(coll.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    kd = road_kd()
    made = {'fern': 0, 'bush': 0, 'rock': 0, 'log': 0, 'stump': 0}

    def sample(n, extent, fn):
        P = candidate_points(rng, n, extent)
        z0, cl = layout.base_height(P[:, 0], P[:, 1])
        r = np.hypot(P[:, 0] - 18.0, P[:, 1] - 8.0)
        p = fn(cl, r)
        ok = rng.rand(n) < p
        P = P[ok]
        d = np.array([kd.find((x, y, 0.0))[2] for x, y in P]) if len(P) else np.array([])
        return P, d

    def put(name, mesh, x, y, scale, yaw, sink=0.02, tilt=0.0):
        z = float(layout.terrain_eval(np.array([x]), np.array([y]), do_hoof=False)['z'][0]) - sink
        ob = bpy.data.objects.new(name, mesh)
        coll.objects.link(ob)
        ob.location = (x, y, z)
        ob.rotation_euler = (rng.normal(0, tilt), rng.normal(0, tilt), yaw)
        ob.scale = (scale, scale, scale)
        return ob

    B = layout.BUILDINGS
    def clear_of_buildings(x, y, pad=3.0):
        for b in B:
            if math.hypot(x - b['x'], y - b['y']) < max(b['W'], b['D']) * 0.5 + pad:
                return False
        return True

    # ferns: forest floor, denser near the clearing edge and road verges
    P, d = sample(60000, 140, lambda cl, r: np.where(cl < 0.6, 0.05 * np.exp(-np.maximum(r - 40, 0) / 45.0) + 0.012, 0.0))
    fl = ['fern_a', 'fern_b', 'fern_c']
    for i, (x, y) in enumerate(P):
        if d[i] < 2.7 or not clear_of_buildings(x, y, 5.0):
            continue
        put('Fern_%04d' % i, LIB[fl[rng.randint(3)]], x, y, rng.uniform(0.7, 1.5), rng.uniform(0, 6.28), 0.03)
        made['fern'] += 1
    # fern patches at the road verges (inside and outside the clearing)
    for k in range(260):
        r_ = layout.ROADS['R1']
        s = rng.uniform(0, r_.L)
        x, y, tx, ty = r_.point(s)
        side = rng.choice([-1, 1])
        off = r_.half_w + rng.uniform(1.2, 4.0)
        px, py = x - ty * side * off, y + tx * side * off
        if clear_of_buildings(px, py, 4.0):
            put('VFern_%03d' % k, LIB[fl[rng.randint(3)]], px, py, rng.uniform(0.6, 1.2), rng.uniform(0, 6.28), 0.03)
            made['fern'] += 1
    # bushes
    P, d = sample(20000, 140, lambda cl, r: np.where(cl < 0.7, 0.012 * np.exp(-np.maximum(r - 40, 0) / 60.0) + 0.002, 0.0))
    bl = ['bush_a', 'bush_b', 'bush_c']
    for i, (x, y) in enumerate(P):
        if d[i] < 3.3 or not clear_of_buildings(x, y, 6.0):
            continue
        put('Bush_%03d' % i, LIB[bl[rng.randint(3)]], x, y, rng.uniform(0.8, 1.5), rng.uniform(0, 6.28), 0.05)
        made['bush'] += 1
    # a few bushes along the village hedgerows (around fences/edges of the clearing)
    for k in range(70):
        a = rng.uniform(0, 6.283)
        rr = rng.uniform(40, 62)
        x, y = 18 + rr * math.cos(a) * 1.15, 8 + rr * math.sin(a) * 0.8
        z0, cl = layout.base_height(np.array([x]), np.array([y]))
        if cl[0] > 0.8 and clear_of_buildings(x, y, 6.0) and kd.find((x, y, 0.0))[2] > 3.5:
            put('EdgeBush_%02d' % k, LIB[bl[rng.randint(3)]], x, y, rng.uniform(0.9, 1.6), rng.uniform(0, 6.28), 0.05)
            made['bush'] += 1
    # rocks, fallen logs, stumps in the forest
    P, d = sample(8000, 130, lambda cl, r: np.where(cl < 0.6, 0.006, 0.0006))
    for i, (x, y) in enumerate(P):
        if d[i] < 3.0 or not clear_of_buildings(x, y, 5.0):
            continue
        put('Rock_%03d' % i, LIB['rock_%d' % rng.randint(4)], x, y, rng.uniform(0.7, 1.6), rng.uniform(0, 6.28), 0.12, tilt=0.1)
        made['rock'] += 1
    P, d = sample(8000, 120, lambda cl, r: np.where(cl < 0.6, 0.0025, 0.0))
    for i, (x, y) in enumerate(P):
        if d[i] < 3.4 or not clear_of_buildings(x, y, 5.0):
            continue
        put('Log_%03d' % i, LIB['log_%d' % rng.randint(3)], x, y, rng.uniform(0.8, 1.2), rng.uniform(0, 6.28), 0.05, tilt=0.03)
        made['log'] += 1
    P, d = sample(8000, 120, lambda cl, r: np.where(cl < 0.7, 0.0025, 0.0))
    for i, (x, y) in enumerate(P):
        if d[i] < 3.4 or not clear_of_buildings(x, y, 5.0):
            continue
        put('Stump_%03d' % i, LIB['stump'], x, y, rng.uniform(0.8, 1.4), rng.uniform(0, 6.28), 0.05)
        made['stump'] += 1
    if log is not None:
        log.append('undergrowth %s' % made)
    return made

# ---------------------------------------------------------------------------- grass scatter
def grass_templates():
    near = [plants.grass_tuft(500 + i, blades=11, height=0.17 + 0.04 * i, spread=0.07) for i in range(4)]
    far = [plants.grass_tuft(520 + i, blades=6, height=0.32, spread=0.09, width=0.03) for i in range(3)]
    # simplified far tuft: drop to fewer rows is not needed, blades are few
    tall = [plants.grass_tuft(540 + i, blades=9, height=0.38 + 0.08 * i, spread=0.1, width=0.016) for i in range(2)]
    return near, far, tall

def scatter_grass(log=None, seed=1717, zones=()):
    """zones: list of (x, y, r, density_multiplier) high-detail areas. Returns two meshes (near, far)."""
    assemble.ensure_layout()
    rng = np.random.RandomState(seed)
    near_t, far_t, tall_t = grass_templates()
    pm = assemble.plant_mats()
    mb_near = MB(); mb_far = MB(); mb_tall = MB()
    kd = road_kd()
    B = layout.BUILDINGS

    def sample_region(xmin, xmax, ymin, ymax, dens):
        n = int((xmax - xmin) * (ymax - ymin) * dens)
        P = np.stack([rng.uniform(xmin, xmax, n), rng.uniform(ymin, ymax, n)], axis=1)
        return P

    tot = {'near': 0, 'far': 0, 'tall': 0}
    # whole clearing at low density (far tufts), full-detail zones at high density
    def evaluate(P):
        out = layout.terrain_eval(P[:, 0], P[:, 1], do_hoof=False)
        return out

    def keep_mask(out, P, kind):
        cl = out['clearing']; cov = out['cover']; cen = out['centre']; rut = out['rut']; wet = out['wet']
        grassy = np.clip(cl * 1.1, 0, 1)
        p = grassy * (1.0 - np.clip(cov * 1.4, 0, 1))
        # weeds in the horse strip, along the verges
        patch = np.clip(0.5 + 1.6 * perlin2(P[:, 0] * 0.9, P[:, 1] * 0.9, 12), 0, 1)
        p = np.maximum(p, cen * 0.55 * patch * (1 - rut) * (1 - wet))
        # taller, thicker grass near the building footprints and fence lines
        for b in B:
            d = np.hypot(P[:, 0] - b['x'], P[:, 1] - b['y']) - max(b['W'], b['D']) * 0.5
            p = np.where(d < 1.0, 0.0, p)
        return p

    def emit(P, mb, templates, scale_rng=(0.8, 1.35), pmul=1.0):
        out = evaluate(P)
        p = keep_mask(out, P, 'near') * pmul
        ok = rng.rand(len(P)) < p
        # also exclude trampled yards
        ok &= out['yard'] < 0.4
        P = P[ok]
        z = out['z'][ok]
        if len(P) == 0:
            return 0
        k = rng.randint(len(templates), size=len(P))
        for t in range(len(templates)):
            sel = k == t
            if not sel.any():
                continue
            pos = np.column_stack([P[sel], z[sel]])
            mb.add_instances(templates[t], pos, rng.uniform(0, 6.283, sel.sum()), rng.uniform(*scale_rng, sel.sum()), jitter={'rnd': 0.35}, rng=rng)
        return len(P)

    # far field: whole clearing region
    P = sample_region(-50, 85, -45, 62, 1.6)
    tot['far'] += emit(P, mb_far, far_t, (0.9, 1.5))
    # full-detail zones
    for (zx, zy, zr, dm) in zones:
        n = int(math.pi * zr * zr * 11.0 * dm)
        ang = rng.uniform(0, 6.283, n); rad = zr * np.sqrt(rng.rand(n))
        P = np.column_stack([zx + rad * np.cos(ang), zy + rad * np.sin(ang)])
        tot['near'] += emit(P, mb_near, near_t, (0.8, 1.4))
        n2 = int(math.pi * zr * zr * 0.9 * dm)
        ang = rng.uniform(0, 6.283, n2); rad = zr * np.sqrt(rng.rand(n2))
        P = np.column_stack([zx + rad * np.cos(ang), zy + rad * np.sin(ang)])
        tot['tall'] += emit(P, mb_tall, tall_t, (0.8, 1.3), 0.8)
    # tall grass and weeds hugging building bases and fence lines
    for b in B:
        n = 700
        a = rng.uniform(0, 6.283, n)
        rad = max(b['W'], b['D']) * 0.5 + rng.uniform(0.2, 2.4, n)
        cx, sn = np.cos(b['yaw']), np.sin(b['yaw'])
        lx, ly = rng.uniform(-b['W'] / 2 - 1.6, b['W'] / 2 + 1.6, n), rng.uniform(-b['D'] / 2 - 1.6, b['D'] / 2 + 1.6, n)
        inside = (np.abs(lx) < b['W'] / 2 + 0.15) & (np.abs(ly) < b['D'] / 2 + 0.15)
        P = np.column_stack([b['x'] + lx * cx - ly * sn, b['y'] + lx * sn + ly * cx])[~inside]
        tot['tall'] += emit(P, mb_tall, tall_t, (0.8, 1.4), 1.2)
    # materials: grass slot index PM['grass'] = 4 in the plant material list
    objs = []
    coll = get_coll('Grass')
    for ob in list(coll.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for nm, mb in (('GrassNear', mb_near), ('GrassFar', mb_far), ('GrassTall', mb_tall)):
        if mb.nv == 0:
            continue
        me = mb.build(nm + '_mesh', pm)
        ob = bpy.data.objects.new(nm, me)
        coll.objects.link(ob)
        objs.append((nm, len(me.polygons)))
    if log is not None:
        log.append('grass %s %s' % (tot, objs))
    return {'tufts': tot, 'objs': objs}


# ---------------------------------------------------------------------------- road debris
def scatter_road_debris(log=None, seed=4242):
    assemble.ensure_layout()
    rng = np.random.RandomState(seed)
    pm = assemble.plant_mats()
    bm = assemble.all_building_mats()
    coll = get_coll('RoadDebris')
    for ob in list(coll.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    R1, R2, R3 = layout.ROADS['R1'], layout.ROADS['R2'], layout.ROADS['R3']
    sE = layout.POINTS['sE']; sR = layout.POINTS['sR']
    # segments of road with weights: (road, s0, s1, density)
    segs = [(R1, sE - 5, sE + 60, 1.0), (R1, sR - 10, sR + 14, 1.8), (R1, 120, 215, 0.6), (R2, 0, R2.L, 0.8), (R3, 0, R3.L, 0.5), (R1, 0, 80, 0.4), (R1, 215, R1.L, 0.3)]
    # pebbles (low-poly), twigs, straw wisps, dry leaves, dung
    peb = MB(); peb.rng = rng
    peb_t = []
    for i in range(3):
        t = MB(); t.rng = rng
        seedv = int(rng.randint(1000))
        t.lathe([(0.001, 0.0), (0.7, 0.0), (1.0, 0.45), (0.75, 0.95), (0.001, 1.0)], sides=7, mat=16, smooth=True,
                wobble=lambda th, z, sv=seedv: 1.0 + 0.25 * perlin2(th * 1.3 + sv, z * 2.0))
        peb_t.append(t)
    twig_t = []
    for i in range(3):
        t = MB(); t.rng = rng
        pts = branch_path_np(rng, 4, 0.5 + 0.3 * i)
        t.tube(pts, [0.009, 0.008, 0.006, 0.005, 0.003], sides=4, mat=11, cap1=True)
        twig_t.append(t)
    dung_t = []
    for i in range(2):
        t = MB(); t.rng = rng
        seedv = int(rng.randint(1000))
        for k in range(5):
            a = rng.uniform(0, 6.28); r_ = rng.uniform(0.0, 0.07)
            sub = MB(); sub.rng = rng
            sub.lathe([(0.001, 0.0), (0.05, 0.0), (0.07, 0.03), (0.05, 0.065), (0.001, 0.08)], sides=8, mat=15, smooth=True,
                      wobble=lambda th, z, sv=seedv + k: 1.0 + 0.2 * perlin2(th * 1.5 + sv, z * 2))
            t.extend(sub, None, (r_ * math.cos(a), r_ * math.sin(a), 0.0))
        dung_t.append(t)
    mb_peb = MB(); mb_twig = MB(); mb_dung = MB(); mb_straw = MB(); mb_leaf = MB()
    n_tot = {'peb': 0, 'twig': 0, 'dung': 0, 'straw': 0, 'leaf': 0}
    from buildings import straw_litter
    for (road, s0, s1, dens) in segs:
        length = max(s1 - s0, 1.0)
        def pts(count, lat_scale=1.0):
            s = rng.uniform(s0, s1, count)
            lat = rng.normal(0, 1, count) * road.half_w * 0.45 * lat_scale
            X = np.zeros(count); Y = np.zeros(count)
            for i in range(count):
                x, y, tx, ty = road.point(s[i])
                X[i] = x - ty * lat[i]; Y[i] = y + tx * lat[i]
            return X, Y
        def zs(X, Y):
            return layout.terrain_eval(X, Y, do_hoof=False)
        n = int(length * 14 * dens)
        X, Y = pts(n)
        out = zs(X, Y)
        for t in range(3):
            sel = np.arange(n) % 3 == t
            pos = np.column_stack([X[sel], Y[sel], out['z'][sel] - 0.005])
            mb_peb.add_instances(peb_t[t], pos, rng.uniform(0, 6.28, sel.sum()), rng.uniform(0.012, 0.042, sel.sum()))
        n_tot['peb'] += n
        n = int(length * 0.7 * dens)
        X, Y = pts(n, 1.3)
        out = zs(X, Y)
        for t in range(3):
            sel = np.arange(n) % 3 == t
            pos = np.column_stack([X[sel], Y[sel], out['z'][sel] + 0.005])
            mb_twig.add_instances(twig_t[t], pos, rng.uniform(0, 6.28, sel.sum()), rng.uniform(0.8, 1.5, sel.sum()))
        n_tot['twig'] += n
        n = int(length * 0.08 * dens)
        if road.hoof and n > 0:
            X, Y = pts(n, 0.35)
            out = zs(X, Y)
            for t in range(2):
                sel = np.arange(n) % 2 == t
                pos = np.column_stack([X[sel], Y[sel], out['z'][sel] - 0.004])
                mb_dung.add_instances(dung_t[t], pos, rng.uniform(0, 6.28, sel.sum()), rng.uniform(0.8, 1.4, sel.sum()))
            n_tot['dung'] += n
        # straw wisps and dry leaves via quad generators (world coordinates)
        n = int(length * 4.0 * dens)
        X, Y = pts(n, 1.2)
        out = zs(X, Y)
        straw_litter_world(mb_straw, rng, X, Y, out['z'] + 0.008)
        n_tot['straw'] += n
        n = int(length * 5.0 * dens) if road is R1 else int(length * 2.5 * dens)
        X, Y = pts(n, 1.5)
        out = zs(X, Y)
        C = np.column_stack([X, Y, out['z'] + 0.01])
        a = rng.normal(0, 1, (n, 3)); a[:, 2] = 0
        nn = np.zeros((n, 3)); nn[:, 2] = 1
        plants.add_leaves(mb_leaf, C, a, nn, rng.uniform(0.07, 0.12, n), 0.6, plants.PM['leafdry'], rng.rand(n), np.zeros(n))
        n_tot['leaf'] += n
    out_objs = []
    for nm, mb, mats_ in (('Pebbles', mb_peb, bm), ('Twigs', mb_twig, bm), ('Dung', mb_dung, bm), ('StrawBits', mb_straw, bm), ('DryLeaves', mb_leaf, pm)):
        if mb.nv == 0:
            continue
        me = mb.build(nm + '_mesh', mats_)
        ob = bpy.data.objects.new(nm, me)
        coll.objects.link(ob)
        out_objs.append((nm, len(me.polygons)))
    if log is not None:
        log.append('debris %s %s' % (n_tot, out_objs))
    return out_objs

def branch_path_np(rng, n, length):
    pts = [np.zeros(3)]
    d = np.array([1.0, 0, 0.05])
    for i in range(n):
        d = d + rng.normal(0, 0.25, 3) * np.array([1, 1, 0.1])
        d /= np.linalg.norm(d)
        pts.append(pts[-1] + d * length / n)
    return np.array(pts)

def straw_litter_world(mb, rng, X, Y, Z, length=(0.1, 0.35)):
    n = len(X)
    ang = rng.uniform(0, math.pi, n)
    ln = rng.uniform(*length, n)
    wdt = 0.005 + 0.004 * rng.rand(n)
    d = np.stack([np.cos(ang), np.sin(ang)], axis=1)
    pn = np.stack([-d[:, 1], d[:, 0]], axis=1)
    P = np.zeros((n, 4, 3))
    for k, (a, b) in enumerate(((-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5))):
        P[:, k, 0] = X + d[:, 0] * ln * a + pn[:, 0] * wdt * b
        P[:, k, 1] = Y + d[:, 1] * ln * a + pn[:, 1] * wdt * b
        P[:, k, 2] = Z + (0.015 * rng.rand(n) if k in (1, 2) else 0.0)
    uv = np.zeros((n, 4, 2)); uv[:, 1, 0] = ln; uv[:, 2, 0] = ln; uv[:, 2, 1] = wdt; uv[:, 3, 1] = wdt
    mb.quads_hard(P, uv, 10, False)


def scatter_flowers(log=None, seed=909, zones=()):
    assemble.ensure_layout()
    rng = np.random.RandomState(seed)
    pm = assemble.plant_mats()
    tmpl = [plants.flower_tuft(600 + i, stems=3, height=0.26 + 0.04 * i) for i in range(4)]
    mb = MB()
    B = layout.BUILDINGS
    tot = 0
    for (zx, zy, zr, dm) in zones:
        n = int(math.pi * zr * zr * 1.5 * dm)
        ang = rng.uniform(0, 6.283, n); rad = zr * np.sqrt(rng.rand(n))
        P = np.column_stack([zx + rad * np.cos(ang), zy + rad * np.sin(ang)])
        out = layout.terrain_eval(P[:, 0], P[:, 1], do_hoof=False)
        # clustered: flowers come in patches
        patch = 0.5 + 0.5 * perlin2(P[:, 0] * 0.35, P[:, 1] * 0.35, 4)
        p = np.clip(out['clearing'], 0, 1) * (1 - np.clip(out['cover'] * 1.5, 0, 1)) * (patch ** 2) * 1.6
        for b in B:
            d = np.hypot(P[:, 0] - b['x'], P[:, 1] - b['y']) - max(b['W'], b['D']) * 0.5
            p = np.where(d < 1.2, 0.0, p)
        ok = (rng.rand(n) < p) & (out['yard'] < 0.3)
        P = P[ok]; z = out['z'][ok]
        k = rng.randint(len(tmpl), size=len(P))
        for t in range(len(tmpl)):
            sel = k == t
            if sel.any():
                mb.add_instances(tmpl[t], np.column_stack([P[sel], z[sel]]), rng.uniform(0, 6.28, sel.sum()), rng.uniform(0.8, 1.3, sel.sum()), jitter={'rnd': 0.0}, rng=rng)
        tot += len(P)
    coll = get_coll('Grass')
    for ob in list(coll.objects):
        if ob.name == 'Flowers':
            bpy.data.objects.remove(ob, do_unlink=True)
    if mb.nv:
        me = mb.build('Flowers_mesh', pm)
        ob = bpy.data.objects.new('Flowers', me)
        coll.objects.link(ob)
    if log is not None:
        log.append('flowers %d' % tot)
    return tot
