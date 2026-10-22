"""GROUND builder, step 5: fallen maple leaves. The object 'Fallen leaves' (material 'Fallen leaves', vertex colour) is rebuilt: 60 to 100 five-lobed
maple leaves in clusters under and east of the maple plus a few windblown ones and 3 to 6 on the raked gravel court. Each leaf lies within 1 cm
of the surface under it (ray cast), slightly curled, in the maple's own colours (orange, red-brown, brown) but small. None on the deck, the bridge or
the water (the spot must be free ground above the waterline)."""
import math
import numpy as np
import bpy
from g6_common import hex_lin, lerp3, mesh_from_arrays, swap_mesh, PFX

PALETTE = [hex_lin('#b0541e'), hex_lin('#8e4220'), hex_lin('#74301a'), hex_lin('#6a4224'), hex_lin('#a07028'), hex_lin('#643020'), hex_lin('#583a22')]
WEIGHTS = [0.24, 0.2, 0.17, 0.12, 0.12, 0.08, 0.07]


def leaf_geometry(rng, R, yaw, curl, base, normal=(0, 0, 1)):
    """5 lobes, 10 outline points (tip, valley, ...), centre fan, a short stem. 12 triangles. curl lifts the lobe tips (at most ~8 mm)."""
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
    j = rng.uniform(0.85, 1.12)
    cols.append(tuple(min(1.0, c * 0.34 * j) for c in tint))
    nl = 7
    for k in range(2 * nl):
        a = yaw + 2 * math.pi * k / (2 * nl) + rng.uniform(-0.1, 0.1)
        tip = (k % 2 == 0)
        r = R * (1.0 if tip else 0.46) * rng.uniform(0.9, 1.08)
        if tip and k in (0, 5):
            r *= 0.85
        rise = curl * (0.008 if tip else 0.003) * rng.uniform(0.6, 1.2)
        verts.append(np.array(base) + (u * math.cos(a) + v * math.sin(a)) * r + n * (0.002 + rise))
        cols.append(tuple(min(1.0, c * (0.50 if tip else 0.38) * j) for c in tint))
    # stem: a point beyond lobe 0's opposite valley
    a = yaw + math.pi * (1 + 1.0 / nl)
    verts.append(np.array(base) + (u * math.cos(a) + v * math.sin(a)) * R * 0.8 + n * 0.0018)
    cols.append(tuple(c * 0.5 for c in tint))
    faces = [(0, 1 + k, 1 + (k + 1) % (2 * nl)) for k in range(2 * nl)]
    faces.append((1 + nl - 1, 1 + nl + 1, 1 + 2 * nl))     # stem triangle (the two lobes beside the back valley, and the stem point)
    return verts, faces, cols


def step5(ctx):
    o, world, rep = ctx['o'], ctx['world'], ctx['rep']
    rr = np.random.default_rng(o['seed'] + 77)
    maple = world.bbox.get('Maple trunk')
    mx, my = (float((maple[0][0] + maple[1][0]) / 2), float((maple[0][1] + maple[1][1]) / 2)) if maple else (-5.9, 1.2)
    # cluster centres: free, visible ground; more likely close to the maple, east of it
    cands = []
    tries = 0
    while len(cands) < 11 and tries < 6000:
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
        if all(math.hypot(x - cx, y - cy) > 1.6 for cx, cy in cands):
            cands.append((x, y))
    leaves = []
    for (cx, cy) in cands:
        n = int(rr.integers(5, 12))
        for _ in range(n):
            a = rr.uniform(0, 6.28)
            rad = abs(rr.normal(0, 0.30))
            leaves.append((cx + math.cos(a) * rad, cy + math.sin(a) * rad, False))
    # windblown ones on the lawn
    tries = 0
    k = 0
    while k < 9 and tries < 2500:
        tries += 1
        x, y = rr.uniform(mx - 3.0, mx + 7.0), rr.uniform(my - 5.0, my + 4.0)
        if world.visible(x, y, 0.1, margin=-0.03) and world.free(x, y, 0.08, zmin=0.0):
            leaves.append((x, y, False))
            k += 1
    # a few on the raked gravel court (3 to 6)
    court = getattr(world, 'court', None)
    kg = 0
    tries = 0
    while court and kg < 5 and tries < 800:
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
        R = rr.uniform(0.034, 0.052)
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
