"""r_moss.py - FIX ROUND (22 October): moss that is a designed SHAPE, not a speckle.
Plain words: the first version made roof moss as small olive speckles in the tile colour and lantern moss as one round bright blob.
Here moss is a soft cushion (a cluster of a few round lumps, 4 to 8 cm high, rolled edge, darker rim) that lies on whatever is below it:
 * cushion_mesh(): a polar grid of rays, any hit function (a BVH of one stone, or the scene's roof), optional stretch along a direction,
   so a patch can follow the cap's hip edge or hug a joint like a crescent;
 * place_roof_cushions(): cushions at the eave (lower end of the last course) and at the ridge foot and on the ridge cap, picked only
   where the hero camera sees the roof, spaced apart so each one reads as its own soft shape at 1200 px."""
import math
import numpy as np
import bpy
from mathutils import Vector
from r_common import *

RING_F = [0.0, 0.16, 0.32, 0.48, 0.64, 0.78, 0.88, 0.95, 0.985, 1.0]
ROOF_NAMES = ('Hall roof', PFX + 'pan', PFX + 'ridge course', PFX + 'eave discs', 'CT / Ceramic pan prototype')


def scene_roof_hit(x, y, z0=9.0):
    """ray straight down at (x, y); the first hit that belongs to the roof (tiles, ridge, discs) as (point, normal) or None"""
    sc = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    o = Vector((x, y, z0))
    d = Vector((0.0, 0.0, -1.0))
    for _ in range(5):
        ok, loc, nrm, idx, ob, mw = sc.ray_cast(dg, o, d)
        if not ok:
            return None
        if ob is not None and ob.name.startswith(ROOF_NAMES):
            return loc, nrm.normalized()
        o = loc + d * 0.004
    return None


class RoofSurface:
    """a BVH of the roof built from the tile shapes at their evaluated places (plus any extra objects, such as the ridge course), so a
    cushion's rays cost microseconds instead of a full scene ray cast each. hit(x, y) -> (point, normal) of the highest surface or None."""

    def __init__(self, M, plan, metas, extra_objs=()):
        from mathutils.bvhtree import BVHTree
        cache = {}
        V, P = [], []
        for k in range(len(M)):
            v = int(plan['variant'][k])
            if v not in cache:
                me = metas[v]
                co = np.empty(len(me.vertices) * 3, np.float64)
                me.vertices.foreach_get('co', co)
                cache[v] = (co.reshape(-1, 3), [tuple(p.vertices) for p in me.polygons])
            co, polys = cache[v]
            w = co @ M[k][:3, :3].T + M[k][:3, 3]
            base = len(V)
            V.extend(map(tuple, w))
            P.extend(tuple(base + i for i in p) for p in polys)
        self.trees = [BVHTree.FromPolygons(V, P)]
        from r_stones import make_bvh
        for o in extra_objs:
            self.trees.append(make_bvh(o))

    def hit(self, x, y, z0=9.0):
        best = None
        for t in self.trees:
            loc, nrm, idx, dist = t.ray_cast(Vector((x, y, z0)), Vector((0.0, 0.0, -1.0)), 20.0)
            if loc is not None and (best is None or loc.z > best[0].z):
                best = (loc, nrm.normalized() if nrm.z >= 0 else -nrm.normalized())
        return best


def _lump_field(rng, n_lumps):
    """a few soft round bumps inside the unit disc: returns f(x, y) in 0..1 (soft union), so the cushion is a cluster of lumps"""
    cs = []
    for i in range(n_lumps):
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(0.0, 0.52) if i else 0.0
        cs.append((r * math.cos(a), r * math.sin(a), rng.uniform(0.26, 0.42), rng.uniform(0.75, 1.0)))

    def f(x, y):
        s = 0.0
        for (bx, by, rho, amp) in cs:
            s += amp * math.exp(-((x - bx) ** 2 + (y - by) ** 2) / (2 * rho * rho))
        return min(s, 1.25) / 1.25
    return f


def cushion_mesh(hit_fn, centre_xy, radius, thick, rng, name, aspect=1.0, angle=0.0, S=40, lumps=4, max_dz=0.10, min_nz=0.5, uv_tile=0.5, wobble=1.0):
    """soft moss cushion. hit_fn(x, y) -> (point, normal) or None. The outline is an irregular blob of the given radius (stretched by
    'aspect' across and turned by 'angle' radians), the height is a few round lumps with a rolled edge; vertex attribute g6_rim = 0 in the
    middle, 1 at the edge (the material reads it). Returns a mesh or None."""
    cx, cy = centre_xy
    ca, sa = math.cos(angle), math.sin(angle)

    def P(u, v):
        return cx + ca * u - sa * v, cy + sa * u + ca * v
    h0 = hit_fn(cx, cy)
    if h0 is None:
        return None
    ph = rng.uniform(0, 6.28, 3)
    am = rng.uniform(0.10, 0.24, 3) * wobble          # wobble < 1: a calmer, rounder outline (lantern)
    sc_ph = rng.uniform(0, 6.28, 2)
    step = max(0.012, radius / 12.0)
    rmax = []
    for s in range(S):
        th = 2 * math.pi * s / S
        out = 1 + am[0] * math.sin(2 * th + ph[0]) + am[1] * math.sin(3 * th + ph[1]) + am[2] * math.sin(5 * th + ph[2])
        out += 0.06 * math.sin(6 * th + sc_ph[0])          # a soft scallop: the edge of a cluster of round lumps (low harmonic: no spikes)
        R = radius * out
        last_ok = 0.0
        broke = False
        r = step
        while r <= R:
            h = hit_fn(*P(r * math.cos(th), r * math.sin(th) * aspect))
            if h is None or h[1].z < min_nz or abs(h[0].z - h0[0].z) > max_dz + 0.6 * r:
                broke = True
                break
            last_ok = r
            r += step
        # a ray that was never stopped reaches the full outline radius (no stair steps of the marching step); a stopped ray ends half a step on
        rmax.append(max(min(last_ok + 0.5 * step if broke else R, R), 0.03))
    rm = np.array(rmax)
    rm = np.maximum(rm, 0.55 * float(np.median(rm)))
    rm = np.mean([np.roll(rm, i) for i in (-2, -1, 0, 1, 2)], axis=0)         # circular smoothing: a round, soft outline, no notches
    rmax = [float(v) for v in rm]
    field = _lump_field(rng, lumps)
    verts, rim = [], []
    centre = h0[0]
    nc = (h0[1] + Vector((0, 0, 1))).normalized()
    verts.append(centre + nc * (thick * (0.18 + 0.82 * field(0.0, 0.0)) * 1.05))
    rim.append(0.0)
    for k in range(1, len(RING_F)):
        f = RING_F[k]
        for s in range(S):
            th = 2 * math.pi * s / S
            r = rmax[s] * f
            x, y = P(r * math.cos(th), r * math.sin(th) * aspect)
            h = hit_fn(x, y)
            p, n = h if h is not None else (centre + Vector((x - cx, y - cy, 0)), Vector((0, 0, 1)))
            n = (n + Vector((0, 0, 1))).normalized()
            fx, fy = f * math.cos(th) * rmax[s] / max(radius, 1e-6), f * math.sin(th) * rmax[s] / max(radius, 1e-6)
            env = max(1 - f ** 2.2, 0.0) ** 0.6
            hgt = thick * (0.18 + 0.82 * field(fx, fy)) * env
            embed = -0.004 if f >= 0.999 else 0.0
            verts.append(p + n * (hgt + embed))
            rim.append(f)
    faces = []
    for s in range(S):
        faces.append((0, 1 + s, 1 + (s + 1) % S))
    for k in range(1, len(RING_F) - 1):
        a0 = 1 + (k - 1) * S
        b0 = 1 + k * S
        for s in range(S):
            s2 = (s + 1) % S
            faces.append((a0 + s, b0 + s, b0 + s2, a0 + s2))
    me = new_mesh(name, verts, faces, smooth=True)
    a = me.attributes.new('g6_rim', 'FLOAT', 'POINT')
    a.data.foreach_set('value', np.array(rim, np.float32))
    set_uv(me, 'UVMap', lambda co, n: ((co.x - cx) / uv_tile + 0.5, (co.y - cy) / uv_tile + 0.5))
    return me


def place_roof_cushions(M, plan, rng, surf, n_eave=7, n_foot=6, n_ridge=5, x_lim=(-3.9, 5.2)):
    """returns a list of (kind, name, mesh). Eave: lower half of the last course (course 7) on the south slope; ridge foot: top end of
    course 0; ridge: on the half-round cap tiles. Only where the hero camera sees the roof; spaced at least 1.2 m apart per kind."""
    from r_tiles import NB, NCRS
    bpy.context.view_layer.update()
    out = []
    vis = plan['vis_hero']
    crs = plan['crs']
    bank = plan['bank']
    var = plan['variant']
    x = M[:, 0, 3]
    used = []

    def pick(cond, n, min_d, jitter_seed):
        idx = [k for k in range(len(M)) if cond(k)]
        rr = np.random.default_rng(jitter_seed)
        rr.shuffle(idx)
        got = []
        for k in idx:
            if len(got) >= n:
                break
            p = M[k][:3, 3]
            if any(np.linalg.norm(p - M[q][:3, 3]) < min_d for q in got + used):
                continue
            got.append(k)
        return got
    eave = pick(lambda k: bank[k] == 1 and crs[k] == NCRS - 1 and vis[k] and var[k] in (0, 1, 2) and x_lim[0] < x[k] < x_lim[1], n_eave, 1.0, 71)
    used += eave
    foot = pick(lambda k: bank[k] == 1 and crs[k] <= 1 and vis[k] and var[k] in (0, 1, 2) and x_lim[0] < x[k] < x_lim[1], n_foot, 1.5, 72)
    used += foot
    n_made = 0

    def tile_xy(k, lx, ly):
        v = M[k] @ np.array([lx, ly, 0.1, 1.0])
        return float(v[0]), float(v[1])
    for kind, ks in (('eave', eave), ('foot', foot)):
        for k in ks:
            lx = rng.uniform(-0.05, 0.05)
            ly = rng.uniform(-0.20, -0.09) if kind == 'eave' else rng.uniform(0.02, 0.18)
            cx, cy = tile_xy(k, lx, ly)
            R = rng.uniform(0.18, 0.26) if kind == 'eave' else rng.uniform(0.16, 0.24)
            me = cushion_mesh(surf.hit, (cx, cy), R, rng.uniform(0.065, 0.09), rng, 'roof moss %s %d' % (kind, n_made),
                              aspect=rng.uniform(0.7, 1.0), angle=rng.uniform(-0.6, 0.6), lumps=int(rng.integers(3, 6)), uv_tile=0.4)
            if me is not None:
                out.append((kind, 'roof moss %s %d' % (kind, n_made), me, k))
                n_made += 1
    # on the ridge cap: elongated along the ridge (x), where the hero sees the top of the cap
    xs = np.linspace(-3.4, 4.5, n_ridge) + rng.uniform(-0.35, 0.35, n_ridge)
    for i, xr in enumerate(xs):
        me = cushion_mesh(surf.hit, (float(xr), 7.2), rng.uniform(0.26, 0.36), rng.uniform(0.05, 0.065), rng, 'roof moss ridge %d' % i,
                          aspect=0.42, angle=0.0, lumps=int(rng.integers(3, 5)), max_dz=0.06, min_nz=0.6, uv_tile=0.4)
        if me is not None:
            out.append(('ridge', 'roof moss ridge %d' % i, me, -1))
    return out
