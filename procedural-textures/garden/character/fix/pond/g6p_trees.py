# POND FIX ROUND (22 October): maple lifted toward the previous final's colour with softer pad edges and windows for the branches; pine fringe shorter and chunky brush-stroke clumps, plated bark that reads.
# (copy of the builder's g6p_trees.py; every change is marked FIX)
# POND BUILDER, steps 3 and 4: the maple (layered pads on a bent trunk) and the pine (flat discs on a plated, curved trunk).
# Plain words: the maple keeps its leaf shape, size, colour ramp and leaf count, but the leaves now sit in 7 layered cloud pads with gaps in
# which the branches show; the trunk and branches are meshes with UVs and a bark normal map. The pine keeps its pads where they are (its shadow
# on the wall must not move) but each pad is a flatter disc with a needle fringe; trunk and limbs get a plated bark normal map.
# The sampling functions are pure numpy so the layout can be tried outside Blender.
import math
import json
import numpy as np
try:
    import bpy
    from mathutils import Vector
except ImportError:          # offline design
    bpy = None

# ------------------------------------------------------------------------------------------------ constants
MAPLE_BASE = np.array([-6.7, 1.3, 0.05])
MAPLE_LEAF_TOTAL = 56000
LEAF_STOPS = [(0.00, (0.17, 0.006, 0.010)), (0.16, (0.42, 0.018, 0.014)), (0.34, (0.72, 0.055, 0.016)),
              (0.55, (0.90, 0.17, 0.026)), (0.72, (0.92, 0.38, 0.045)), (0.86, (0.42, 0.46, 0.06)), (1.00, (0.20, 0.09, 0.03))]
# pads: cx, cy, cz (world), rx, ry, thickness, tilt (deg), tilt azimuth (deg), lobes
MAPLE_PADS = [
    (-5.37, 1.04, 3.65, 1.37, 1.54, 0.71, 6, 200, 6),      # 0 top crown
    (-6.78, 2.18, 3.02, 1.26, 1.10, 0.75, 8, 250, 5),      # 1 west back
    (-3.95, 2.50, 3.30, 1.10, 0.95, 0.74, 7, 120, 5),      # 2 east back, high
    (-3.78, 0.43, 2.71, 1.18, 1.46, 0.75, 10, 330, 6),     # 3 east middle (its branch shows in the hero)   FIX: tilt 7 -> 10 toward the sun
    (-4.47, 0.08, 2.45, 1.18, 0.85, 0.66, 13, 335, 5),     # 4 south, low   FIX: raised 5 cm, thinner, tilted 13 degrees toward the sun (was 9 degrees away) so it is lit
    (-6.43, 0.74, 3.28, 1.09, 0.86, 0.55, 8, 300, 5),      # 5 west
    (-4.30, 0.96, 2.78, 1.11, 1.04, 0.70, 11, 320, 5),     # 6 centre, low   FIX: tilt 6 toward the north -> 11 toward the sun
]


def rotation_to_euler(normal, spin):
    n = normal / np.linalg.norm(normal, axis=1, keepdims=True)
    a = np.where(np.abs(n[:, 2:3]) > 0.95, np.array([[1.0, 0.0, 0.0]]), np.array([[0.0, 0.0, 1.0]]))
    x = np.cross(a, n)
    x /= np.linalg.norm(x, axis=1, keepdims=True)
    y = np.cross(n, x)
    c, s = np.cos(spin)[:, None], np.sin(spin)[:, None]
    xs = x * c + y * s
    ys = -x * s + y * c
    R = np.stack([xs, ys, n], axis=2)
    sy = -R[:, 2, 0]
    ey = np.arcsin(np.clip(sy, -1, 1))
    cy = np.cos(ey)
    ex = np.where(cy > 1e-6, np.arctan2(R[:, 2, 1], R[:, 2, 2]), np.arctan2(-R[:, 1, 2], R[:, 1, 1]))
    ez = np.where(cy > 1e-6, np.arctan2(R[:, 1, 0], R[:, 0, 0]), 0.0)
    return np.stack([ex, ey, ez], axis=1)


def smooth_noise(P, seed, freq=1.0, octaves=3):
    r = np.random.default_rng(seed)
    out = np.zeros(len(P))
    amp = 1.0
    tot = 0.0
    for o in range(octaves):
        for _ in range(4):
            d = r.normal(size=3)
            d /= np.linalg.norm(d)
            out += amp * np.sin(P @ d * freq * (2.0 ** o) * 2.1 + r.uniform(0, 6.283))
            tot += amp
        amp *= 0.5
    return out / tot * 1.6


def _rot(axis, ang):
    axis = np.asarray(axis, dtype=np.float64)
    axis = axis / np.linalg.norm(axis)
    K = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    return np.eye(3) + math.sin(ang) * K + (1 - math.cos(ang)) * (K @ K)


# ------------------------------------------------------------------------------------------------ maple: leaf points of the layered pads
def pad_edge(th, lobes, phases, amp_lobe=0.14):
    return 1 + amp_lobe * np.sin(lobes * th + phases[0]) + 0.08 * np.sin(2 * th + phases[1]) + 0.05 * np.sin(3 * th + phases[2])


def _nearest_grid(Pn, Po, cell):
    """nearest old point for every new point, searched only in the 27 cells around it (grid hash); -1 where none is found"""
    lo = np.minimum(Pn.min(0), Po.min(0)) - 2 * cell
    M = np.ceil((np.maximum(Pn.max(0), Po.max(0)) + 2 * cell - lo) / cell).astype(np.int64) + 2

    def keys(P):
        c = np.floor((P - lo) / cell).astype(np.int64)
        return c, (c[:, 0] * M[1] + c[:, 1]) * M[2] + c[:, 2]
    co, ko = keys(Po)
    order = np.argsort(ko, kind='stable')
    ks = ko[order]
    cn, _ = keys(Pn)
    best = np.full(len(Pn), np.inf)
    bi = np.full(len(Pn), -1, dtype=np.int64)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                q = ((cn[:, 0] + dx) * M[1] + (cn[:, 1] + dy)) * M[2] + (cn[:, 2] + dz)
                a = np.searchsorted(ks, q, 'left'); b = np.searchsorted(ks, q, 'right')
                cnt = b - a
                for j in range(int(cnt.max()) if len(cnt) else 0):
                    sel = np.nonzero(cnt > j)[0]
                    idx = order[a[sel] + j]
                    d2 = ((Pn[sel] - Po[idx]) ** 2).sum(1)
                    better = d2 < best[sel]
                    best[sel[better]] = d2[better]; bi[sel[better]] = idx[better]
    return bi


def nearest_old(Pn, Po, cells=(0.10, 0.35, 1.2)):
    """Index of the nearest old-crown leaf for every new leaf point: grid hash with growing cells (numpy only), brute force for the last few."""
    Pn = np.asarray(Pn, dtype=np.float64); Po = np.asarray(Po, dtype=np.float64)
    bi = np.full(len(Pn), -1, dtype=np.int64)
    for cell in cells:
        todo = np.nonzero(bi < 0)[0]
        if len(todo) == 0:
            break
        bi[todo] = _nearest_grid(Pn[todo], Po, cell)
    for i in np.nonzero(bi < 0)[0]:
        bi[i] = int(np.argmin(((Po - Pn[i]) ** 2).sum(1)))
    return bi


def old_hue_field(Po, hue, cell=0.15, smooth=1):
    """Mean ramp position of the previous final's leaves on a 3D grid (cell metres), smoothed, holes filled from their neighbours. Returns (lo, cell, grid)."""
    Po = np.asarray(Po, dtype=np.float64); hue = np.asarray(hue, dtype=np.float64)
    lo = Po.min(0) - 3 * cell
    shape = np.ceil((Po.max(0) + 3 * cell - lo) / cell).astype(int) + 1
    ci = np.floor((Po - lo) / cell).astype(int)
    flat = (ci[:, 0] * shape[1] + ci[:, 1]) * shape[2] + ci[:, 2]
    n = int(shape.prod())
    sm = np.bincount(flat, weights=hue, minlength=n).reshape(shape)
    ct = np.bincount(flat, minlength=n).reshape(shape).astype(np.float64)

    def blur(a):
        for ax in range(3):
            acc = a.copy()
            for sh in (-1, 1):
                acc = acc + np.roll(a, sh, axis=ax) * 0.5
            a = acc / 2.0
        return a
    for _ in range(smooth):
        sm, ct = blur(sm), blur(ct)
    mean = np.where(ct > 1e-6, sm / np.maximum(ct, 1e-6), np.nan)
    for _ in range(6):                          # fill holes from the six neighbours
        if not np.isnan(mean).any():
            break
        acc = np.zeros_like(mean); cn = np.zeros_like(mean)
        for ax in range(3):
            for sh in (-1, 1):
                r = np.roll(mean, sh, axis=ax)
                ok = ~np.isnan(r)
                acc += np.where(ok, r, 0.0); cn += ok
        fill = np.where(cn > 0, acc / np.maximum(cn, 1), np.nan)
        mean = np.where(np.isnan(mean), fill, mean)
    mean = np.where(np.isnan(mean), float(hue.mean()), mean)
    return lo, cell, mean


def sample_field(F, P):
    lo, cell, g = F
    ci = np.clip(np.floor((np.asarray(P, dtype=np.float64) - lo) / cell).astype(int), 0, np.array(g.shape) - 1)
    return g[ci[:, 0], ci[:, 1], ci[:, 2]]


def maple_crown(seed=31, n_total=MAPLE_LEAF_TOTAL, pads=None, hue_target=None, hue_quantiles=None, wmin=0.055, wmax=0.125, share=(0.62, 0.12, 0.26), windows=None,
                fringe=0.07, tone_mean=1.10, tone_sd=0.14, hue_noise=0.09, hue_freq=1.7, bump=1.0, old=None, old_hue_blend=1.0, old_cell=0.15, old_noise=0.10, sun_bias=0.0, tail_drop=0.30, wr_scale=1.0, old_nn=False, old_tone_blend=0.0, old_normal_blend=0.0):
    """Leaf points for the layered pads. Returns dict with P, N, U (colour ramp position), T (tone), SIZE (leaf width), PAD (pad index), LAYER (0 bottom .. 1 top).
    FIX: (1) soft edges: a share `fringe` of the leaves hang below and outside the rim in loose tails, and the outline gets small scallops; (2) cloud lumps on the top
    (bigger bump, normals follow it, so every pad is lit in clumps, not as one slab); (3) leaf tone mean 1.10 (was 1.00) and fewer dark bottom leaves; (4) colour patches
    about 1.5 m across instead of whole-pad olive; (5) `windows`: view tubes toward branches: leaves in front of a branch point, as seen from the hero camera, are left out
    so the branch shows between the pads. The total stays n_total (the points are drawn a little over and thinned)."""
    rng = np.random.default_rng(seed)
    pads = pads or MAPLE_PADS
    over = 1.0 + (0.22 if windows else 0.0)
    areas = np.array([p[3] * p[4] for p in pads])
    counts = (n_total * over * areas / areas.sum()).astype(int)
    counts[0] += int(n_total * over) - counts.sum()
    out = {k: [] for k in ('P', 'N', 'U', 'T', 'SIZE', 'PAD', 'LAYER')}
    for pi, (cx, cy, cz, rx, ry, T, tilt, taz, lobes) in enumerate(pads):
        n = int(counts[pi])
        ph = rng.uniform(0, 6.3, 3)
        bph = rng.uniform(0, 6.3, 4)
        sph = rng.uniform(0, 6.3, 2)
        droop = 0.20 * (rx + ry) / 2.0
        xs, ys, rhos, ths = [], [], [], []
        got = 0
        while got < n:
            m = int(n * 1.7) + 20
            rho = np.sqrt(rng.uniform(0, 1, m)); th = rng.uniform(0, math.tau, m)
            edge = pad_edge(th, lobes, ph) + 0.045 * np.sin(11 * th + sph[0]) + 0.03 * np.sin(17 * th + sph[1])       # FIX: small scallops on the outline
            rho_e = rho / edge
            keep = (rho_e <= 1.0) & (rng.uniform(0, 1, m) < np.clip(1 - rho_e ** 4, 0, None) ** 0.5 * 0.88 + 0.12)
            sel = np.where(keep)[0][: n - got]
            xs.append(rho[sel] * np.cos(th[sel]) * rx); ys.append(rho[sel] * np.sin(th[sel]) * ry); rhos.append(rho_e[sel]); ths.append(th[sel])
            got += len(sel)
        x = np.concatenate(xs); y = np.concatenate(ys); rho = np.concatenate(rhos); th = np.concatenate(ths)
        env = np.clip(1 - rho ** 2, 0, 1)
        b0, b1, b2, b3 = bph
        bumpz = bump * (0.10 * np.sin(x * 4.6 + b0) * np.sin(y * 5.2 + b1) + 0.06 * np.sin(x * 8.3 + 2 * b1) * np.sin(y * 7.7 + b2) + 0.03 * np.sin(x * 14.0 + b3))
        gx = bump * (0.10 * 4.6 * np.cos(x * 4.6 + b0) * np.sin(y * 5.2 + b1) + 0.06 * 8.3 * np.cos(x * 8.3 + 2 * b1) * np.sin(y * 7.7 + b2) + 0.03 * 14.0 * np.cos(x * 14.0 + b3))
        gy = bump * (0.10 * 5.2 * np.sin(x * 4.6 + b0) * np.cos(y * 5.2 + b1) + 0.06 * 7.7 * np.sin(x * 8.3 + 2 * b1) * np.cos(y * 7.7 + b2))
        zt = (T * 0.5) * env ** 0.6 + bumpz * env - droop * rho ** 3
        zb = -(T * 0.5) * env ** 0.7 - 0.02 - droop * rho ** 3
        pick = rng.uniform(0, 1, len(x))
        layer = np.where(pick < share[0], 1.0, np.where(pick < share[0] + share[1], 0.0, 0.5))
        z = np.where(layer == 1.0, zt - np.abs(rng.normal(0, 0.045, len(x))), np.where(layer == 0.0, zb + np.abs(rng.normal(0, 0.04, len(x))), zb + (zt - zb) * rng.uniform(0, 1, len(x))))
        # FIX: loose tails: a share of the rim leaves hangs below the pad (ragged lower edge, no slab)
        tail = (rng.uniform(0, 1, len(x)) < fringe * 2.2) & (rho > 0.72) & (layer < 1.0) & ((cz - T * 0.5) > 2.5)          # no tails on the lowest pads (they hang over the rocks)
        z = np.where(tail, zb - rng.uniform(0.04, tail_drop, len(x)) * np.clip((rho - 0.6) / 0.4, 0, 1), z)
        # slope normals of the top surface (pad slope plus the cloud lumps); bottom leaves face down a little; interior random
        nx = (x / rx) * env * 0.5 - gx * 1.3 * env
        ny = (y / ry) * env * 0.5 - gy * 1.3 * env
        nrm = np.stack([nx, ny, np.ones_like(nx)], axis=1)
        nrm[layer == 0.0, 2] = -0.35
        wr = np.where(layer == 1.0, 0.42 + 0.22 * rho, 0.62) * wr_scale
        rnd = rng.normal(size=nrm.shape)
        nrm = nrm / np.linalg.norm(nrm, axis=1, keepdims=True) * (1 - wr[:, None]) + rnd / np.linalg.norm(rnd, axis=1, keepdims=True) * wr[:, None]
        if sun_bias:
            nrm = nrm + sun_bias * np.array([-0.75, -0.2, 0.6])[None, :]          # leaves lean toward the low west sun
        loc = np.stack([x, y, z], axis=1)
        R = _rot(np.array([-math.sin(math.radians(taz)), math.cos(math.radians(taz)), 0.0]), math.radians(tilt))
        loc = loc @ R.T
        nrm = nrm @ R.T
        world = loc + np.array([cx, cy, cz])
        low = smooth_noise(world, 5, hue_freq, 2)
        sun = np.clip(0.5 - (world[:, 0] - (MAPLE_BASE[0] + 1.7)) / 5.0, 0, 1)
        u = 0.10 + 0.26 * rho + 0.06 * sun + 0.34 * low + 0.10 * (layer - 0.5) + rng.normal(0, hue_noise, len(x))
        r = rng.uniform(0, 1, len(x))
        u = np.where((r < 0.045) & (rho > 0.55) & (layer > 0.4), rng.uniform(0.80, 0.90, len(x)), u)
        u = np.where(r > 0.955, rng.uniform(0.96, 1.0, len(x)), u)
        tone = np.clip(rng.normal(tone_mean, tone_sd, len(x)), 0.75, 1.45)
        w = np.clip(np.exp(rng.normal(math.log((wmin + wmax) / 2), 0.28, len(x))), wmin, wmax)
        for k, v in (('P', world), ('N', nrm), ('U', u), ('T', tone), ('SIZE', w), ('PAD', np.full(len(x), pi)), ('LAYER', layer)):
            out[k].append(v)
    out = {k: np.concatenate(v) for k, v in out.items()}
    if old is not None:
        # FIX: the colour pattern (and, if asked, the leaf lean) of the previous final's crown is carried over by place: every new leaf takes the ramp position of the nearest old leaf
        ob_ = float(old_hue_blend)
        if old_nn:                       # leaf by leaf: the nearest old leaf lends its ramp position, tone and lean
            idx = nearest_old(out['P'], old['P'])
            u_old = np.asarray(old['hue'], dtype=np.float64)[idx]
            if old_tone_blend > 0 and 'tone' in old:
                tb = float(old_tone_blend)
                out['T'] = (1 - tb) * out['T'] + tb * np.asarray(old['tone'], dtype=np.float64)[idx] * tone_mean
            if old_normal_blend > 0:
                nb = float(old_normal_blend)
                n_new = out['N'] / np.linalg.norm(out['N'], axis=1, keepdims=True)
                mix = (1 - nb) * n_new + nb * np.asarray(old['n'], dtype=np.float64)[idx]
                out['N'] = mix / np.linalg.norm(mix, axis=1, keepdims=True)
        else:
            F = old_hue_field(old['P'], old['hue'], cell=old_cell)
            u_old = sample_field(F, out['P'])
        out['U'] = (1 - ob_) * out['U'] + ob_ * (u_old + rng.normal(0, old_noise, len(u_old)))
    # FIX: windows toward the branches (as seen from the hero camera), then thin to exactly n_total
    n_removed = 0
    if windows:
        keep = np.ones(len(out['P']), bool)
        for (cam, pts, rad) in windows:
            cam = np.asarray(cam, dtype=np.float64)
            for pt in np.asarray(pts, dtype=np.float64):
                dvec = pt - cam
                dist = np.linalg.norm(dvec)
                dv = dvec / dist
                w_ = out['P'] - cam
                t = w_ @ dv
                perp = np.linalg.norm(w_ - t[:, None] * dv[None, :], axis=1)
                front = t < dist - 0.05
                inside = front & (perp < rad)
                edge = front & (perp >= rad) & (perp < rad * 1.45)           # a soft border: part of the leaves at the rim of the window stay
                keep &= ~(inside | (edge & (rng.uniform(0, 1, len(keep)) < (1.45 - perp / rad) * 1.1)))
        n_removed = int((~keep).sum())
        out = {k: v[keep] for k, v in out.items()}
    if len(out['P']) > n_total:
        sel = np.sort(rng.choice(len(out['P']), size=n_total, replace=False))
        out = {k: v[sel] for k, v in out.items()}
    out['n_removed_by_windows'] = n_removed
    if hue_quantiles is not None:    # keep the colour distribution of the old crown exactly: rank-map the new ramp positions onto the old quantiles (keeps the new spatial pattern)
        u = out['U']
        rank = np.argsort(np.argsort(u)) / max(1, len(u) - 1)
        out['U'] = np.interp(rank, np.linspace(0, 1, len(hue_quantiles)), hue_quantiles).astype(np.float64)
    elif hue_target is not None:       # keep the colour distribution of the old crown: match mean and spread of the ramp position
        m0, s0 = hue_target
        u = out['U']
        u = (u - u.mean()) / (u.std() + 1e-9) * s0 + m0
        out['U'] = np.clip(u, 0.0, 0.99)
    else:
        out['U'] = np.clip(out['U'], 0.0, 0.99)
    return out


# ------------------------------------------------------------------------------------------------ maple: skeleton (trunk, roots, branches)
TRUNK = [(-6.72, 1.32, -0.06, 0.36), (-6.70, 1.30, 0.10, 0.27), (-6.68, 1.26, 0.40, 0.205), (-6.60, 1.14, 0.95, 0.185), (-6.38, 1.00, 1.55, 0.155),
         (-6.00, 1.06, 2.15, 0.130), (-5.62, 1.22, 2.65, 0.105), (-5.28, 1.38, 3.05, 0.082), (-5.05, 1.45, 3.40, 0.060)]
ROOTS = [[(-6.70, 1.30, 0.22, 0.17), (-6.98, 1.52, 0.05, 0.09), (-7.35, 1.72, -0.03, 0.035)],
         [(-6.70, 1.30, 0.22, 0.17), (-6.38, 1.62, 0.03, 0.085), (-6.15, 2.02, -0.04, 0.03)],
         [(-6.70, 1.30, 0.22, 0.17), (-6.95, 0.98, 0.03, 0.08), (-7.15, 0.62, -0.04, 0.03)],
         [(-6.70, 1.30, 0.22, 0.17), (-6.35, 0.95, 0.04, 0.075), (-6.05, 0.62, -0.03, 0.028)]]
FORK_Z = [3.05, 2.50, 2.70, 1.95, 1.65, 2.20, 2.05]            # where the primary branch of pad i leaves the trunk (pad 0 is the crown: its leader leaves the trunk top)


def trunk_point(z):
    """Point on the trunk centre line at height z (control points of TRUNK, piecewise linear)."""
    t = np.array(TRUNK)
    for a, b in zip(t[:-1], t[1:]):
        if a[2] <= z <= b[2]:
            f = (z - a[2]) / (b[2] - a[2])
            return a[:3] * (1 - f) + b[:3] * f, a[3] * (1 - f) + b[3] * f
    return t[-1][:3], t[-1][3]


def maple_skeleton(pads=None, seed=7):
    """Trunk control points, root tubes and 17 branches (each a list of (x, y, z, r)): 7 primaries (one per pad), 10 forks into the gaps. World coordinates."""
    pads = pads or MAPLE_PADS
    rng = np.random.default_rng(seed)
    B = []
    ends = []
    for i, (cx, cy, cz, rx, ry, Th, tilt, taz, lobes) in enumerate(pads):
        p0, r0 = trunk_point(FORK_Z[i])
        end = np.array([cx - 0.10 * rx * math.cos(math.radians(taz)), cy - 0.10 * ry * math.sin(math.radians(taz)), cz - Th * 0.5 + 0.06])
        if i == 3 - 3:                 # pad 0 is the crown: its leader comes straight up from the trunk top
            p0, r0 = np.array(TRUNK[-2][:3]), TRUNK[-2][3]
        d = end - p0
        pts = [p0, p0 + d * 0.30 + np.array([0, 0, 0.10]), p0 + d * 0.62 + np.array([0, 0, 0.05]), end]
        rad = [0.096 * (0.6 + 0.4 * rx / 1.3), 0.074, 0.050, 0.024]
        B.append([(*p, r) for p, r in zip(pts, rad)])
        ends.append(end)
    # ten forks: leave a primary at 40 to 70 percent of its length; seven end under a pad, three are front twigs that poke out of the pads' lower front edge
    plan = [(3, 0.55, 3), (3, 0.80, 3), (1, 0.55, 1), (2, 0.50, 2), (2, 0.78, 2), (4, 0.55, 4), (5, 0.6, 5), (6, 0.55, 6), (0, 0.5, 0), (0, 0.35, 4)]
    front = {5: (3, 0.38, (0.30, -0.50, -0.06), (0.62, -1.05, -0.14)), 7: (3, 0.62, (0.18, -0.42, -0.05), (0.40, -0.92, -0.20)),
             8: (4, 0.50, (0.0, -0.45, -0.07), (-0.18, -0.95, -0.22))}
    for fi, (src, t, dst) in enumerate(plan):
        a = np.array([[q[0], q[1], q[2]] for q in B[src]])
        seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(a, axis=0), axis=1))]
        pt = np.array([np.interp(t * seg[-1], seg, a[:, k]) for k in range(3)])
        if fi in front:
            src_f, t_f, d1, d2 = front[fi]
            a = np.array([[q[0], q[1], q[2]] for q in B[src_f]])
            seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(a, axis=0), axis=1))]
            pt = np.array([np.interp(t_f * seg[-1], seg, a[:, k]) for k in range(3)])
            B.append([(*pt, 0.042), (*(pt + np.array(d1)), 0.028), (*(pt + np.array(d2)), 0.012)])
            continue
        cx, cy, cz, rx, ry, Th, tilt, taz, lobes = pads[dst]
        ang = rng.uniform(0, math.tau)
        tgt = np.array([cx + math.cos(ang) * rx * rng.uniform(0.25, 0.55), cy + math.sin(ang) * ry * rng.uniform(0.25, 0.55), cz - Th * 0.5 + rng.uniform(0.0, 0.18)])
        mid = pt * 0.5 + tgt * 0.5 + np.array([0, 0, 0.10])
        B.append([(*pt, 0.040), (*mid, 0.026), (*tgt, 0.012)])
    return TRUNK, ROOTS, B


# ------------------------------------------------------------------------------------------------ inner mass (dark lens under every pad)
def maple_inner_mass(pads=None, seed=33, windows=None):
    """One flat lumpy lens per pad (dark red-brown, a little lighter on top): returns V, F, per-face colour."""
    rng = np.random.default_rng(seed)
    pads = pads or MAPLE_PADS
    import g6p_common as C
    V0, F0 = C.icosphere(2)
    Vs, Fs, Cs, off = [], [], [], 0
    for (cx, cy, cz, rx, ry, T, tilt, taz, lobes) in pads:
        V = V0.astype(np.float64).copy()
        th = np.arctan2(V[:, 1], V[:, 0])
        edge = pad_edge(th, lobes, rng.uniform(0, 6.3, 3), 0.10)
        rad = (0.62 + rng.uniform(-0.04, 0.04, len(V))) * edge
        rho = np.hypot(V[:, 0], V[:, 1]) * rad
        V[:, 0] *= rx * rad
        V[:, 1] *= ry * rad
        V[:, 2] *= T * 0.26
        V[:, 2] -= 0.20 * (rx + ry) / 2.0 * (np.hypot(V[:, 0] / rx, V[:, 1] / ry)) ** 3 + 0.02
        R = _rot(np.array([-math.sin(math.radians(taz)), math.cos(math.radians(taz)), 0.0]), math.radians(tilt))
        V = V @ R.T + np.array([cx, cy, cz - 0.02])
        zc = V[F0].mean(axis=1)[:, 2]
        t = np.clip((zc - zc.min()) / max(1e-4, np.ptp(zc)), 0, 1)[:, None] * 0.6 + rng.uniform(0, 0.25, (len(F0), 1))
        a, b = np.array([0.12, 0.015, 0.010]), np.array([0.38, 0.05, 0.020])          # FIX: lighter inner mass (x1.5)
        Cc_ = np.concatenate([a + (b - a) * np.clip(t, 0, 1), np.ones((len(F0), 1))], axis=1)
        keepf = np.ones(len(F0), bool)
        if windows:                       # FIX: faces of the inner mass in front of a branch (seen from the hero camera) are left out, as the leaves are, so the branch shows
            cen = V[F0].mean(axis=1)
            for (cam, pts, rad) in windows:
                cam = np.asarray(cam, dtype=np.float64)
                for pt in np.asarray(pts, dtype=np.float64):
                    dvec = pt - cam
                    dist = np.linalg.norm(dvec)
                    dv = dvec / dist
                    w_ = cen - cam
                    t_ = w_ @ dv
                    perp = np.linalg.norm(w_ - t_[:, None] * dv[None, :], axis=1)
                    keepf &= ~((t_ < dist - 0.05) & (perp < rad * 1.2))
        Cs.append(Cc_[keepf])
        Vs.append(V.astype(np.float32)); Fs.append(F0[keepf] + off); off += len(V)
    return np.concatenate(Vs), np.concatenate(Fs), np.concatenate(Cs)


# ------------------------------------------------------------------------------------------------ Blender side (needs bpy)
OLD_HUE_STATS = (0.429, 0.279)            # mean and spread of the old crown's colour ramp position (measured on the starting scene)
OLD_HUE_QUANTILES = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0031, 0.0239, 0.0435, 0.0613, 0.0759, 0.0918, 0.1063, 0.1199, 0.1326, 0.1441, 0.1561, 0.1675, 0.178, 0.1882, 0.1979, 0.208, 0.217, 0.2263, 0.2352, 0.244, 0.253, 0.2612, 0.2692, 0.2777, 0.2859, 0.2937, 0.3022, 0.3096, 0.3172, 0.3249, 0.3321, 0.3392, 0.3466, 0.3542, 0.3611, 0.3685, 0.3753, 0.3827, 0.3898, 0.397, 0.4038, 0.4107, 0.4178, 0.4252, 0.4328, 0.4408, 0.4483, 0.4556, 0.4629, 0.4706, 0.4785, 0.4862, 0.494, 0.5021, 0.5103, 0.5178, 0.5258, 0.5341, 0.5425, 0.551, 0.5597, 0.569, 0.5781, 0.588, 0.5974, 0.6084, 0.6191, 0.6297, 0.6408, 0.6522, 0.6653, 0.6774, 0.6907, 0.7064, 0.7214, 0.7382, 0.7562, 0.7755, 0.7968, 0.8131, 0.8284, 0.8438, 0.8609, 0.8785, 0.8969, 0.9438, 0.9659, 0.974, 0.9823, 0.9897, 0.99, 0.99]      # its 0, 1, ... 100 percent points: the new leaves are mapped onto exactly this distribution
UNIT_LEAF_WIDTH = 1.563                    # widest of the five leaf source shapes: scale = leaf width / this


def bark_uv(U, S, n_rep, tile):
    """U 0..1 around, S metres along. n_rep whole repeats around so the seam matches; v in the same tile units (isotropic)."""
    return np.stack([U * n_rep, S / tile], axis=1)


def tube_object_data(path4, sides=10, twist=0.0, tile_m=0.6, plates=0.0, seed=0, cap_start=False, per_seg=6):
    """Mesh arrays for a branch / trunk: smooth Catmull-Rom path through (x, y, z, r) control points, round section, UV (u around, v along)."""
    import g6p_common as C
    path4 = np.asarray(path4, dtype=np.float64)
    smooth = C.catmull(path4, per_seg)
    V, F, U, S = C.tube(smooth[:, :3], smooth[:, 3], sides=sides, cap_end=True, cap_start=cap_start, twist=twist)
    if plates > 0:
        rng = np.random.default_rng(seed)
        n_rings = len(smooth)
        w = sides + 1
        ph = rng.uniform(0, 6.3, 3)
        for i in range(n_rings):
            for k in range(w):
                idx = i * w + k
                th = k / sides * math.tau
                plate = np.sin(th * 5 + ph[0] + 0.7 * np.sin(S[idx] * 3.0)) * np.sin(S[idx] * 6.0 + ph[1] + th * 2)
                c = smooth[i, :3]
                dvec = V[idx] - c
                V[idx] = c + dvec * (1.0 + plates * plate)
    circ = 2 * math.pi * float(np.mean(smooth[:, 3]))
    n_rep = max(1, int(round(circ / tile_m)))
    uvv = bark_uv(U, S, n_rep, circ / n_rep)
    return V, F, uvv


def bark_uvs_per_corner(uvv, F):
    return uvv[np.asarray(F).reshape(-1)]


def add_bark_normal(mat_name, map_path, strength, bump_cap=0.3, lift_rgb=(1.0, 1.0, 1.0), emit=0.0, plates_path=None, plates_gain=1.45):
    import g6p_common as C
    m = bpy.data.materials.get(mat_name)
    if m is None or m.node_tree is None:
        return None
    nt = m.node_tree
    bsdf0 = next(n for n in nt.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled')
    for n in list(nt.nodes):
        if n.name == 'G6 bark lift' and n.inputs[6].is_linked:               # give the colour link back before the lift node goes (second run)
            nt.links.new(n.inputs[6].links[0].from_socket, bsdf0.inputs['Base Color'])
    for n in list(nt.nodes):
        if n.name.startswith('G6 '):
            nt.nodes.remove(n)
    bump = next((n for n in nt.nodes if n.bl_idname == 'ShaderNodeBump'), None)
    bsdf = next(n for n in nt.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled')
    nm = C.normal_map_chain(nt.nodes, nt.links, map_path, 'UVMap', strength, label='G6 bark', loc=(-1400, -600))
    if bump is not None:
        bump.inputs['Strength'].default_value = min(bump.inputs['Strength'].default_value, bump_cap)
        nt.links.new(nm.outputs['Normal'], bump.inputs['Normal'])
        if not bump.outputs['Normal'].links:
            nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    else:
        nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    # a warm lift of the bark colour so branches read in the shade under the pads (colour x1.35 red, x1.25 green, x1.15 blue)
    if bsdf.inputs['Base Color'].is_linked:
        src_link = bsdf.inputs['Base Color'].links[0]
        lift = nt.nodes.new('ShaderNodeMix'); lift.data_type = 'RGBA'; lift.blend_type = 'MULTIPLY'; lift.name = lift.label = 'G6 bark lift'
        lift.inputs['Factor'].default_value = 1.0
        lift.inputs[7].default_value = (lift_rgb[0], lift_rgb[1], lift_rgb[2], 1.0)
        nt.links.new(src_link.from_socket, lift.inputs[6])
        nt.links.new(lift.outputs[2], bsdf.inputs['Base Color'])
        lift.location = (bsdf.location.x - 300, bsdf.location.y + 250)
        if emit > 0:                    # a faint self-light (as the leaves and needles have), so branches in the deep shade under the pads stay readable
            nt.links.new(lift.outputs[2], bsdf.inputs['Emission Color'])
        bsdf.inputs['Emission Strength'].default_value = emit
        if plates_path is not None:     # FIX: plate shade: dark cracks between lighter plates, drawn from the pine bark scan, mean brightness kept (gain 1/0.69)
            img = C.load_image(plates_path)
            uv = nt.nodes.new('ShaderNodeUVMap'); uv.uv_map = 'UVMap'; uv.name = uv.label = 'G6 plates UV'
            tx = nt.nodes.new('ShaderNodeTexImage'); tx.image = img; tx.interpolation = 'Cubic'; tx.extension = 'REPEAT'; tx.name = tx.label = 'G6 plates image'
            gn = nt.nodes.new('ShaderNodeVectorMath'); gn.operation = 'SCALE'; gn.inputs['Scale'].default_value = plates_gain; gn.name = gn.label = 'G6 plates gain'
            pm = nt.nodes.new('ShaderNodeMix'); pm.data_type = 'RGBA'; pm.blend_type = 'MULTIPLY'; pm.name = pm.label = 'G6 bark plates'
            pm.inputs['Factor'].default_value = 1.0
            nt.links.new(uv.outputs['UV'], tx.inputs['Vector'])
            nt.links.new(tx.outputs['Color'], gn.inputs[0])
            nt.links.new(lift.outputs[2], pm.inputs[6])
            nt.links.new(gn.outputs['Vector'], pm.inputs[7])
            nt.links.new(pm.outputs[2], bsdf.inputs['Base Color'])
            for i_, n_ in enumerate((uv, tx, gn, pm)):
                n_.location = (bsdf.location.x - 700 + i_ * 160, bsdf.location.y + 500)
    return nm


def swap_curve_for_mesh(name, V, F, uvv, mat, smooth=True):
    """Replace curve object `name` (or an earlier mesh of the same name) by a mesh object with the same name, same collections."""
    import g6p_common as C
    old = bpy.data.objects.get(name)
    cols = [c for c in old.users_collection] if old is not None else [C.collection()]
    props = {k: old[k] for k in old.keys()} if old is not None else {}
    me = C.make_mesh(name, V, F, uvs={'UVMap': bark_uvs_per_corner(uvv, F)}, smooth=smooth, materials=[mat])
    if old is not None and old.type == 'MESH':
        C.replace_mesh(old, me)
        ob = old
    else:
        if old is not None:
            C.remove_object(old)
        ob = bpy.data.objects.new(name, me)
        for c in cols:
            c.objects.link(ob)
    C.tag(ob, 'bark')
    ob['g6p_converted'] = 1
    if name.startswith('Maple'):
        ob.lightgroup = 'rest'            # the bark now carries a faint self-light, like the leaves: same light group as the other emitters
    return ob


def _old_crown(opts):
    """The previous final's crown (positions, ramp positions, leaf normals), saved in maps/maple_old_crown.npz, or None if the dial maple_old_hue_blend is 0."""
    import os
    import g6p_common as C
    if not opts.get('maple_old_hue_blend', 1.0):
        return None
    path = os.path.join(C.MAPS, 'maple_old_crown.npz')
    if not os.path.exists(path):
        return None
    d = np.load(path)
    return {'P': d['P'], 'hue': d['hue'], 'n': d['n'], 'tone': d['tone']}


def step_maple(ctx):
    import g6p_common as C
    from g6p_common import say, REP
    opts = ctx.opts
    rng = np.random.default_rng(ctx.seed + 200)
    # ---- leaves: new point cloud, same instancer (by copy), same leaf shapes
    pads_ = opts.get('maple_pads') or MAPLE_PADS
    ts_ = opts.get('maple_thick_scale', 0.82)
    if ts_ != 1.0:
        pads_ = [(cx, cy, cz, rx, ry, T * ts_, tl, tz, lb) for (cx, cy, cz, rx, ry, T, tl, tz, lb) in pads_]
    trunk, roots, B = maple_skeleton(pads_)
    # FIX: windows in the leaves toward some branches, as the hero camera sees them (the leaves in front of a branch point are left out)
    cam_ob = bpy.data.objects.get('photo')
    cam_loc = tuple(cam_ob.matrix_world.translation) if cam_ob is not None else (-5.2, -5.6, 3.0)
    windows = []
    for bi in opts.get('maple_window_branches', [3, 4]):
        sm = C.catmull(np.array(B[bi], dtype=np.float64), 10)[:, :3]
        seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(sm, axis=0), axis=1))]
        ts = np.arange(seg[-1] * opts.get('maple_window_from', 0.45), seg[-1] * 0.97, 0.10)
        pts = np.stack([np.interp(ts, seg, sm[:, k]) for k in range(3)], axis=1)
        windows.append((cam_loc, pts, opts.get('maple_window_radius', 0.11)))
    crown = maple_crown(seed=ctx.seed, pads=pads_, hue_target=OLD_HUE_STATS, hue_quantiles=OLD_HUE_QUANTILES, windows=windows if opts.get('maple_windows', True) else None,
                        tone_mean=opts.get('maple_tone_mean', 1.13), tone_sd=opts.get('maple_tone_sd', 0.14), hue_noise=opts.get('maple_hue_noise', 0.09),
                        hue_freq=opts.get('maple_hue_freq', 1.7), fringe=opts.get('maple_fringe', 0.07), bump=opts.get('maple_bump', 1.0),
                        old=_old_crown(opts), old_hue_blend=opts.get('maple_old_hue_blend', 1.0), old_cell=opts.get('maple_old_cell', 0.15), old_noise=opts.get('maple_old_noise', 0.02),
                        sun_bias=opts.get('maple_sun_bias', 0.0), tail_drop=opts.get('maple_tail_drop', 0.30), wr_scale=opts.get('maple_wr_scale', 1.0),
                        old_nn=opts.get('maple_old_nn', True), old_tone_blend=opts.get('maple_old_tone_blend', 0.0), old_normal_blend=opts.get('maple_old_normal_blend', 0.0))
    n = len(crown['P'])
    spin = rng.uniform(0, math.tau, n)
    eul = rotation_to_euler(crown['N'], spin)
    scale = crown['SIZE'] / UNIT_LEAF_WIDTH
    kind = rng.integers(0, 5, n)
    rank = rng.uniform(0, 1, n)
    ob = bpy.data.objects['Maple leaves']
    me = bpy.data.meshes.new('Maple leaves')
    me.vertices.add(n)
    me.vertices.foreach_set('co', crown['P'].astype(np.float32).ravel())
    me.update()
    for k, (typ, arr) in {'leaf_kind': ('INT', kind), 'leaf_rot': ('FLOAT_VECTOR', eul), 'leaf_scale': ('FLOAT_VECTOR', np.stack([scale] * 3, axis=1)),
                          'leaf_hue': ('FLOAT', crown['U']), 'leaf_tone': ('FLOAT', crown['T']), 'leaf_rank': ('FLOAT', rank)}.items():
        a = me.attributes.new(name=k, type=typ, domain='POINT')
        arr = np.asarray(arr)
        if typ == 'FLOAT_VECTOR':
            a.data.foreach_set('vector', arr.astype(np.float32).ravel())
        elif typ == 'INT':
            a.data.foreach_set('value', arr.astype(np.int32).ravel())
        else:
            a.data.foreach_set('value', arr.astype(np.float32).ravel())
    me.materials.append(ob.data.materials[0] if len(ob.data.materials) else bpy.data.materials['Maple leaves'])
    # FIX: a faint self-light on the leaf colour (as the bark has), so the leaves in the shade of the pads keep their red
    lm = bpy.data.materials['Maple leaves']
    pb = next((n_ for n_ in lm.node_tree.nodes if n_.bl_idname == 'ShaderNodeBsdfPrincipled'), None)
    mixn = next((n_ for n_ in lm.node_tree.nodes if n_.bl_idname == 'ShaderNodeMix'), None)
    if pb is not None and mixn is not None:
        lm.node_tree.links.new(mixn.outputs[2], pb.inputs['Emission Color'])
        pb.inputs['Emission Strength'].default_value = opts.get('maple_emit', 0.06)
    old_me = ob.data
    ob.data = me
    if old_me.users == 0:
        bpy.data.meshes.remove(old_me)
    # node group by copy
    src = bpy.data.node_groups.get('Life / maple leaf instancer')
    cp = bpy.data.node_groups.get('G6 pond / maple leaf instancer')
    # FIX: on a second run the copy is kept (removing it would clear the modifier's settings and the leaves would vanish); the copy is made only the first time
    if cp is None and src is not None:
        cp = src.copy()
        cp.name = 'G6 pond / maple leaf instancer'
        for md in ob.modifiers:
            if md.type == 'NODES':
                md.node_group = cp
    C.tag(ob, 'leaf')
    REP.changed.append('Maple leaves')
    REP.numbers['maple_leaves'] = n
    REP.numbers['maple_pads'] = len(pads_)
    REP.numbers['maple_leaves_left_out_by_windows'] = int(crown.get('n_removed_by_windows', 0))
    REP.numbers['maple_leaf_colour_ramp_mean_std'] = (round(float(crown['U'].mean()), 3), round(float(crown['U'].std()), 3))
    REP.numbers['maple_leaf_width_cm_min_median_max'] = tuple(round(float(v) * 100, 1) for v in (crown['SIZE'].min(), np.median(crown['SIZE']), crown['SIZE'].max()))
    # ---- inner mass
    V, F, Cc = maple_inner_mass(pads_, windows=windows if opts.get('maple_windows', True) else None)
    mat = bpy.data.materials['Maple inner mass']
    imesh = C.make_mesh('Maple inner mass', V, F, colors=C.face_colors_to_corners(Cc), smooth=False, materials=[mat])
    iob = bpy.data.objects['Maple inner mass']
    C.replace_mesh(iob, imesh)
    C.tag(iob, 'leaf')
    REP.changed.append('Maple inner mass')
    # ---- trunk, roots, branches as meshes with UVs
    bark = bpy.data.materials['Bark']
    parts = []
    Vt, Ft, uvt = tube_object_data(trunk, sides=14, twist=0.55, tile_m=0.7, plates=0.035, seed=3, cap_start=True)
    parts.append((Vt, Ft, uvt))
    for k, r in enumerate(roots):
        Vr, Fr, uvr = tube_object_data(r, sides=8, tile_m=0.7, plates=0.0, seed=10 + k, cap_start=False, per_seg=5)
        parts.append((Vr, Fr, uvr))
    Vs, Fs, UVs, off = [], [], [], 0
    for (Va, Fa, uva) in parts:
        Vs.append(Va); Fs.append(Fa + off); UVs.append(uva); off += len(Va)
    swap_curve_for_mesh('Maple trunk', np.concatenate(Vs), np.concatenate(Fs), np.concatenate(UVs), bark)
    REP.changed.append('Maple trunk')
    for i, name in enumerate(C.MAPLE_BRANCH_NAMES):
        Vb, Fb, uvb = tube_object_data(B[i], sides=8, tile_m=0.7, plates=0.0, seed=20 + i, per_seg=6)
        swap_curve_for_mesh(name, Vb, Fb, uvb, bark)
        REP.changed.append(name)
    add_bark_normal('Bark', C.MAPS + '/maple_bark_normal.png', opts.get('bark_strength', 0.9), lift_rgb=opts.get('bark_lift', (1.15, 0.98, 0.90)), emit=opts.get('bark_emit', 0.07))
    REP.numbers['maple_branches_meshes'] = len(C.MAPLE_BRANCH_NAMES)
    say('maple: %d leaves on %d layered pads, bent trunk with root flare (twist 0.55 rad), %d branch meshes with UVs, bark normal map' % (n, len(pads_), len(C.MAPLE_BRANCH_NAMES)))


# ------------------------------------------------------------------------------------------------ pine
PINE_PAD_RADII = [0.95, 0.85, 0.90, 0.70, 0.75]
NEEDLE_PAL = np.array([[0.010, 0.040, 0.028], [0.022, 0.070, 0.040], [0.040, 0.095, 0.050], [0.030, 0.085, 0.060], [0.055, 0.105, 0.045]])


def pine_pad_layout():
    """Pad centres and radii exactly as the starting scene (main pads: ends of limbs 0-4 + 0.10; three small satellites carried by limbs 5-7)."""
    import g6p_common as C
    anchors = [np.array(l[-1][:3]) for l in C.PINE_LIMB_PTS[:5]]
    pads = [(a + np.array([0, 0, 0.10]), PINE_PAD_RADII[i % 5] * 1.05) for i, a in enumerate(anchors)]
    sat = []
    for k, parent in zip((5, 6, 7), (0, 2, 4)):
        end = np.array(C.PINE_LIMB_PTS[k][-1][:3])
        sat.append((end + np.array([0, 0, 0.08]), pads[parent][1] * 0.5))
    return pads + sat


def pine_disc(rng, centre, radius, thick, tilt_deg, tilt_az):
    """A flat cloud disc: ragged outline, gently domed top, drooping rim, flat underside. Returns V, F, face role (0 top, 1 side, 2 under)."""
    n = 20
    ph = rng.uniform(0, 6.3, 3)
    ang = np.array([(k + rng.uniform(-0.2, 0.2)) * math.tau / n for k in range(n)])
    edge = 1 + 0.12 * np.sin(2 * ang + ph[0]) + 0.08 * np.sin(3 * ang + ph[1]) + 0.05 * np.sin(5 * ang + ph[2]) + rng.uniform(-0.05, 0.05, n)
    rings = [0.0, 0.50, 0.82, 1.0]
    V = [(0.0, 0.0, thick * 0.55)]
    for ri in (1, 2, 3):
        rr = rings[ri]
        for k in range(n):
            rad = radius * rr * edge[k]
            z = thick * (0.55 - 0.40 * rr ** 2) - (0.04 * radius * rr ** 4)
            V.append((math.cos(ang[k]) * rad, math.sin(ang[k]) * rad * 0.92, z + rng.uniform(-0.012, 0.012)))
    for k in range(n):
        rad = radius * edge[k] * 0.90
        V.append((math.cos(ang[k]) * rad, math.sin(ang[k]) * rad * 0.92, -thick * 0.30 + rng.uniform(-0.012, 0.012)))
    V.append((0.0, 0.0, -thick * 0.45))
    V = np.array(V, dtype=np.float64)
    r1, r2, r3, low, bot = 1, 1 + n, 1 + 2 * n, 1 + 3 * n, 1 + 4 * n
    F, role = [], []
    for k in range(n):
        k2 = (k + 1) % n
        F.append((0, r1 + k, r1 + k2)); role.append(0)
        F.append((r1 + k, r2 + k, r2 + k2)); role.append(0); F.append((r1 + k, r2 + k2, r1 + k2)); role.append(0)
        F.append((r2 + k, r3 + k, r3 + k2)); role.append(0); F.append((r2 + k, r3 + k2, r2 + k2)); role.append(0)
        F.append((r3 + k, low + k, low + k2)); role.append(1); F.append((r3 + k, low + k2, r3 + k2)); role.append(1)
        F.append((bot, low + k2, low + k)); role.append(2)
    R = _rot(np.array([-math.sin(math.radians(tilt_az)), math.cos(math.radians(tilt_az)), 0.0]), math.radians(tilt_deg))
    V = V @ R.T + np.asarray(centre)
    return V.astype(np.float32), np.array(F, dtype=np.int32), np.array(role)


def pine_needles(rng, V, F, role, centre, target_tris, K=5, rnd=0.30, up=0.16, len_scale=1.0, width=0.011, rim_len=1.12, tip_light=1.30):
    """Needle strokes (K broad triangles each, one brush-stroke clump) rooted over the top (radial, nearly flat), along the rim (a short drooping fringe) and under the rim.
    FIX: strokes are twice as wide (half width 1.1 cm, was 0.55 cm), the rim fringe is a quarter shorter (mean 14.6 cm, was 19.5), each stroke is darker at the root and lighter
    at the tip (one painted stroke), and the K strokes of a clump lean the same way (less random spread)."""
    pv = V[F]
    nrm = np.cross(pv[:, 1] - pv[:, 0], pv[:, 2] - pv[:, 0])
    area = np.linalg.norm(nrm, axis=1) * 0.5
    nrm = nrm / np.maximum(np.linalg.norm(nrm, axis=1, keepdims=True), 1e-9)
    w = np.where(role == 0, area, np.where(role == 1, area * 2.2, 0.0))
    ncl = int(target_tris / K)
    pick = rng.choice(len(F), size=ncl, p=w / w.sum())
    u = rng.random((ncl, 2)); flip = u.sum(axis=1) > 1; u[flip] = 1 - u[flip]
    P = pv[pick, 0] + (pv[pick, 1] - pv[pick, 0]) * u[:, :1] + (pv[pick, 2] - pv[pick, 0]) * u[:, 1:2]
    out = P - np.asarray(centre); out[:, 2] = 0
    out = out / np.maximum(np.linalg.norm(out, axis=1, keepdims=True), 1e-6)
    rim = (role[pick] == 1)[:, None]
    lean = rng.normal(size=(ncl, 3)); lean /= np.maximum(np.linalg.norm(lean, axis=1, keepdims=True), 1e-6)        # one lean per clump
    Vn = np.empty((ncl, K, 3, 3), np.float32)
    tipk = np.empty((ncl, K), np.float32)
    for k in range(K):
        rn = rng.normal(size=(ncl, 3)); rn /= np.maximum(np.linalg.norm(rn, axis=1, keepdims=True), 1e-6)
        d = out * np.where(rim, 1.0, 0.85) + np.array([0, 0, up]) * (~rim) + np.array([0, 0, -0.32]) * rim + (0.65 * lean + 0.35 * rn) * rnd
        d /= np.maximum(np.linalg.norm(d, axis=1, keepdims=True), 1e-6)
        ln = rng.uniform(0.09, 0.17, (ncl, 1)) * np.where(rim, rim_len, 1.0) * len_scale
        side = np.cross(d, np.array([0, 0, 1.0])); side /= np.maximum(np.linalg.norm(side, axis=1, keepdims=True), 1e-6)
        base = P - d * 0.01 + rng.normal(size=(ncl, 3)) * 0.009
        Vn[:, k, 0] = base + side * width
        Vn[:, k, 1] = base - side * width
        Vn[:, k, 2] = base + d * ln
    cidx = rng.integers(0, len(NEEDLE_PAL), size=ncl * K)
    tone = NEEDLE_PAL[cidx] * rng.uniform(0.75, 1.15, (ncl * K, 1))
    Cn = np.ones((ncl * K, 3, 4), np.float32)
    Cn[:, 0, :3] = tone * 0.72              # root corners darker
    Cn[:, 1, :3] = tone * 0.72
    Cn[:, 2, :3] = np.minimum(tone * tip_light, 1.0) + np.array([0.003, 0.003, 0.002])          # tip lighter and a touch warmer (not more saturated)
    return Vn.reshape(-1, 3), np.arange(ncl * K * 3, dtype=np.int32).reshape(-1, 3), Cn.reshape(-1, 4)


def step_pine(ctx):
    import g6p_common as C
    from g6p_common import say, REP
    opts = ctx.opts
    rng = np.random.default_rng(ctx.seed + 300)
    old = bpy.data.objects['Pine pads']
    n_before = len(old.data.polygons) if old.data.get('g6p_pine') is None else int(old.data['g6p_pine'])   # triangles of the starting scene (65537)
    target_total = int(opts.get('pine_needle_tris', 52000))          # FIX: fewer, broader strokes (was 64582 thin ones)
    pads = pine_pad_layout()
    areas = np.array([r * r for c, r in pads])
    Vs, Fs, Cs, off = [], [], [], 0
    body_cols = {0: ((0.014, 0.050, 0.030), (0.040, 0.100, 0.052)), 1: ((0.007, 0.022, 0.017), (0.017, 0.047, 0.028)), 2: ((0.004, 0.014, 0.010), (0.009, 0.024, 0.016))}
    tot_needle = 0
    ratios = []
    for pi, (c, r) in enumerate(pads):
        thick = opts.get('pine_thick', 0.30) * (0.92 + 0.16 * rng.uniform()) * min(1.0, 2 * r / 1.6)
        tilt = rng.uniform(4, 9)
        az = math.degrees(math.atan2(c[1] - 4.6, c[0] - 7.6)) + 90 + rng.normal(0, 10)
        V, F, role = pine_disc(rng, c, r, thick, tilt, az)
        ratios.append(float(np.ptp(V[:, 2])) / (2 * r))
        Cb = np.zeros((len(F), 4), np.float32)
        for fi, rl in enumerate(role):
            a, b = np.array(body_cols[int(rl)][0]), np.array(body_cols[int(rl)][1])
            Cb[fi, :3] = a + (b - a) * rng.uniform(0, 1); Cb[fi, 3] = 1
        Vs.append(V); Fs.append(F + off); Cs.append(np.repeat(Cb, 3, axis=0)); off += len(V)
        nt = int((target_total - 8 * len(F)) * areas[pi] / areas.sum())
        Vn, Fn, Cn = pine_needles(rng, V, F, role, c, nt, rnd=opts.get('pine_rnd', 0.50), up=opts.get('pine_up', 0.40), len_scale=opts.get('pine_len', 1.0),
                                  width=opts.get('pine_width', 0.018), rim_len=opts.get('pine_rim_len', 1.12), tip_light=opts.get('pine_tip_light', 1.30), K=int(opts.get('pine_K', 4)))
        Vs.append(Vn); Fs.append(Fn + off); Cs.append(np.repeat(Cn, 3, axis=0) if len(Cn) == len(Fn) else Cn); off += len(Vn)
        tot_needle += len(Fn)
    V = np.concatenate(Vs); F = np.concatenate(Fs)
    # per-corner colours: body faces carry one colour per face, needles one per triangle
    Ccorner = []
    for (Vx, Fx, Cx) in zip(Vs, Fs, Cs):
        pass
    mat = bpy.data.materials['Pine needles']
    Call = np.concatenate([c if len(c) == 3 * len(f) else np.repeat(c, 3, axis=0) for f, c in zip(Fs, Cs)])
    me = C.make_mesh('Pine pads', V, F, colors=Call, smooth=False, materials=[mat])
    C.replace_mesh(old, me)
    old.data['g6p_pine'] = n_before
    C.tag(old, 'leaf')
    REP.changed.append('Pine pads')
    REP.numbers['pine_pads'] = len(pads)
    REP.numbers['pine_triangles_after'] = len(F)
    REP.numbers['pine_pad_thickness_over_diameter_max'] = round(max(ratios), 3)
    # ---- trunk and limbs
    bark = bpy.data.materials['GARDEN bark.pine']
    tp = [np.array(p) for p in C.PINE_TRUNK_PTS]
    # a slightly livelier curve through the same control points
    trunk = [tuple(p) for p in C.PINE_TRUNK_PTS]
    Vt, Ft, uvt = tube_object_data(trunk, sides=20, twist=0.35, tile_m=0.75, plates=opts.get('pine_plates', 0.075), seed=5, cap_start=True, per_seg=8)   # FIX: plates 0.075 (was 0.045), 20 sides
    swap_curve_for_mesh('Pine trunk', Vt, Ft, uvt, bark)
    REP.changed.append('Pine trunk')
    for i, name in enumerate(C.PINE_LIMB_NAMES):
        pts = [list(p) for p in C.PINE_LIMB_PTS[i]]
        # thicker arms that curve up into the pad: the end tucks just under the pad centre, a middle point lifts the arm
        a, b = np.array(pts[0][:3]), np.array(pts[-1][:3])
        mid = (a + b) / 2 + np.array([0, 0, 0.07])
        ctrl = [(*a, pts[0][3] * 1.5), (*(a * 0.7 + mid * 0.3), pts[0][3] * 1.25), (*mid, pts[1][3] * 1.1), (*b, pts[-1][3] * 0.9)]
        Vl, Fl, uvl = tube_object_data(ctrl, sides=8, tile_m=0.75, plates=0.06, seed=40 + i, per_seg=6)
        swap_curve_for_mesh(name, Vl, Fl, uvl, bark)
        REP.changed.append(name)
    add_bark_normal('GARDEN bark.pine', C.MAPS + '/pine_bark_normal.png', opts.get('bark_strength', 0.9), plates_path=C.MAPS + '/pine_plates.png', plates_gain=opts.get('pine_plates_gain', 1.45))
    say('pine: %d flat discs (thickness under 25 percent of diameter) with radial needle sprays and a rim fringe (%d needle triangles, was %d), plated trunk and %d limbs as meshes with UVs, bark normal map' % (len(pads), tot_needle, n_before, len(C.PINE_LIMB_NAMES)))
