"""GROUND builder, step 5: fallen maple leaves. The object 'Fallen leaves' (material 'Fallen leaves', vertex colour) is rebuilt: 60 to 100 five-lobed
maple leaves in clusters under and east of the maple plus a few windblown ones and 3 to 6 on the raked gravel court. Each leaf lies within 1 cm
of the surface under it (ray cast), slightly curled, in the maple's own colours (orange, red-brown, brown) but small. None on the deck, the bridge or
the water (the spot must be free ground above the waterline)."""
import math
import numpy as np
import bpy
from g6_common import hex_lin, lerp3, mesh_from_arrays, swap_mesh, PFX

PALETTE = [hex_lin('#cc5220'), hex_lin('#b4421a'), hex_lin('#d97a2c'), hex_lin('#9a3418'), hex_lin('#c4651f'), hex_lin('#8a3a1c')]
WEIGHTS = [0.26, 0.24, 0.16, 0.14, 0.12, 0.08]


def leaf_geometry(rng, R, yaw, curl, base, normal=(0, 0, 1)):
    """FIX ROUND: a big, simple five pointed maple star (the concept's red leaves): five lobes, each a valley - shoulder - tip - shoulder, a short stem.
    20 outline points + centre = 20 triangles; the lobe tips lift a little (curl, at most about 1 cm). Colour: dark vein centre, bright lobes."""
    n = np.array(normal, dtype=float)
    n /= np.linalg.norm(n)
    u = np.cross(n, [0.0, 1.0, 0.0])
    if np.linalg.norm(u) < 1e-3:
        u = np.array([1.0, 0.0, 0.0])
    u /= np.linalg.norm(u)
    v = np.cross(n, u)
    verts = [np.array(base) + n * 0.002]
    cols = []
    tint = PALETTE[rng.choice(len(PALETTE), p=WEIGHTS)]
    j = rng.uniform(0.9, 1.12)
    cols.append(tuple(min(1.0, c * 0.42 * j) for c in tint))
    nl = 5
    lobe = [(-0.628, 0.30, 0.0), (-0.27, 0.64, 0.4), (0.0, 1.0, 1.0), (0.27, 0.64, 0.4)]
    for k in range(nl):
        a_k = yaw + 2 * math.pi * k / nl
        sc = rng.uniform(0.9, 1.08) * (0.88 if k == 0 else 1.0)        # the lobe at the stem is a little shorter
        for (da, rr, rise) in lobe:
            a = a_k + da + rng.uniform(-0.04, 0.04)
            r = R * rr * (sc if rr > 0.5 else 1.0)
            verts.append(np.array(base) + (u * math.cos(a) + v * math.sin(a)) * r + n * (0.002 + curl * 0.010 * rise * rng.uniform(0.6, 1.2)))
            cols.append(tuple(min(1.0, c * (0.95 if rr > 0.9 else 0.72 if rr > 0.5 else 0.5) * j) for c in tint))
    # stem: a short point behind lobe 0
    a = yaw + math.pi * (1 + 1.0 / nl) - 0.0
    verts.append(np.array(base) + (u * math.cos(yaw + math.pi) + v * math.sin(yaw + math.pi)) * R * 0.62 + n * 0.0018)
    cols.append(tuple(c * 0.4 for c in tint))
    nv = 4 * nl
    faces = [(0, 1 + k, 1 + (k + 1) % nv) for k in range(nv)]
    return verts, faces, cols


def step5(ctx):
    o, world, rep = ctx['o'], ctx['world'], ctx['rep']
    rr = np.random.default_rng(o['seed'] + 77)
    maple = world.bbox.get('Maple trunk')
    mx, my = (float((maple[0][0] + maple[1][0]) / 2), float((maple[0][1] + maple[1][1]) / 2)) if maple else (-5.9, 1.2)
    # cluster centres: free, visible ground; more likely close to the maple, east of it
    cands = []
    tries = 0
    while len(cands) < 8 and tries < 9000:
        tries += 1
        x = rr.uniform(mx - 3.5, mx + 6.0)
        y = rr.uniform(my - 4.5, my + 3.5)
        if not world.visible(x, y, 0.1, margin=-0.03):
            continue
        d = math.hypot(x - mx, y - my)
        if rr.random() > math.exp(-max(d - 1.0, 0) / 3.2):
            continue
        if world.mask_at(x, y) > 0.3 or not world.free(x, y, 0.15, zmin=0.0):
            continue
        # FIX ROUND: only where a leaf is big enough to read: the lower 45 percent of the hero or the lower half of the veranda picture
        best = 0.0
        for cn in ('photo', 'veranda'):
            u_, v_, d_ = world.view_xy(cn, x, y, 0.05)
            if d_ > 0 and 0.03 < u_ < 0.97 and v_ < (0.45 if cn == 'photo' else 0.50) and v_ > 0.02:
                best = max(best, 1.0 - v_)
        if best <= 0.0:
            continue
        if all(math.hypot(x - cx, y - cy) > 1.9 for cx, cy in cands):
            cands.append((x, y))
    leaves = []
    for (cx, cy) in cands:
        n = int(rr.integers(3, 8))
        for _ in range(n):
            a = rr.uniform(0, 6.28)
            rad = abs(rr.normal(0, 0.42))
            lx, ly = cx + math.cos(a) * rad, cy + math.sin(a) * rad
            if all(math.hypot(lx - qx, ly - qy) > 0.14 for qx, qy, _ in leaves):
                leaves.append((lx, ly, False))
    # windblown ones on the lawn
    tries = 0
    k = 0
    while k < 7 and tries < 2500:
        tries += 1
        x, y = rr.uniform(mx - 3.0, mx + 7.0), rr.uniform(my - 5.0, my + 4.0)
        if world.visible(x, y, 0.1, margin=-0.03) and world.free(x, y, 0.08, zmin=0.0) and all(math.hypot(x - qx, y - qy) > 0.3 for qx, qy, _ in leaves):
            leaves.append((x, y, False))
            k += 1
    # a few on the raked gravel court (3 to 6)
    court = getattr(world, 'court', None)
    kg = 0
    tries = 0
    while court and kg < 4 and tries < 800:
        tries += 1
        x, y = rr.uniform(court[0] + 0.3, court[0] + 4.0), rr.uniform(court[2] + 0.5, court[3] - 0.5)
        if world.visible(x, y, 0.1, margin=-0.03) and world.free(x, y, 0.08, zmin=0.0, gravel_ok=True):
            leaves.append((x, y, True))
            kg += 1
    # build
    V, F, Cc = [], [], []
    placed = 0
    maxd = 0.0
    for (x, y, gravel) in leaves:
        if not gravel and (world.mask_at(x, y) > 0.5 or not world.free(x, y, 0.05, zmin=0.0)):
            continue
        z, on_g = world.surface(x, y)
        if z is None:
            continue
        R = rr.uniform(0.070, 0.100)
        v, f, c = leaf_geometry(rr, R, rr.uniform(0, 6.28), rr.uniform(0.3, 1.0), (x, y, z + rr.uniform(0.0, 0.003)))
        o_ = len(V)
        V += [tuple(p) for p in v]
        Cc += c
        F += [tuple(i + o_ for i in fc) for fc in f]
        placed += 1
        maxd = max(maxd, 0.0)
    if placed:
        me = mesh_from_arrays(PFX + 'fallen leaves', np.array(V, dtype=np.float32), F, cols=np.array(Cc, dtype=np.float32), smooth=False)
        ob = bpy.data.objects['Fallen leaves']
        swap_mesh(ob, me)
    rep['leaves'] = dict(count=placed, on_gravel=kg, clusters=len(cands), triangles=len(F))
