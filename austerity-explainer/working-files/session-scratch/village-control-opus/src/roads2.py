"""Pass 2: rebuilt dirt roads, yards and puddles.

Changes from pass 1 (terrain.build_road / build_yard), made after the judges' notes:
- ruts braid: up to three pairs of wheel tracks that wander independently, appear and fade, with steep crumbling
  walls, squeezed-up mud lips and bumpy bottoms (no longer one pair of smooth parallel grooves);
- the bank at the verge varies from nothing to ~11 cm and its foot wanders, so the edge is not one even berm;
- wet stretches (some placed where the cameras look) have deeper, wider, churned ruts and more potholes;
- hoof prints are deeper in mud, overlap, have broken rims and mud thrown forward;
- puddle water planes reach past the flooded cells so the ground itself cuts the shoreline; each water vertex
  stores its depth so the water shader can show the mud bottom near the shore;
- new attributes for the material: 'wetzone' (damp stretch), 'ridge' (squeezed mud), 'crown' (grassy middle),
  'shore' (wet ground just above a puddle's water line).
The road edges (rc.edges) are unchanged, so the terrain built in pass 1 still fits around the roads.
"""
import bpy
import numpy as np
import math
import common as C
from common import fbm, perlin, noise1, smoothstep, mesh_from_arrays
import layout as L
import terrain as T

EDGE_DROP = T.EDGE_DROP

# art-directed wet stretches: (road, x, y, radius m) -> wet_zone forced towards 1 near these points
WET_SPOTS = [
    ("main", -34.5, -9.9, 7.0),     # eye-level view foreground
    ("main", -22.0, -7.0, 5.0),
    ("main", -1.0, -4.6, 6.5),      # road close-up
    ("main", 22.0, 7.5, 5.0),
    ("lane_n", 6.0, 13.0, 4.0),
    ("lane_s", -14.0, -22.0, 5.0),
]


# pass 2b: big puddles where carts turn and stand (junctions, the stable lane, low spots) - big enough to read
# from the aerial view as water in the road: (road, x, y, half-length m, half-width m, depth m)
BIG_PUDDLES = [
    ("main", 2.6, -3.0, 1.5, 0.95, 0.17),       # junction with the stable lane
    ("main", -17.0, -6.4, 1.7, 1.0, 0.18),      # junction with the forest road (also seen down the eye-level view)
    ("main", 24.5, 2.4, 1.2, 0.8, 0.16),
    ("main", -27.5, -8.6, 1.1, 0.7, 0.15),      # mid-distance in the eye-level view
    ("main", 44.0, 10.3, 1.3, 0.85, 0.16),
    ("lane_s", -14.2, -21.0, 1.3, 0.9, 0.16),
    ("lane_s", -6.0, -40.5, 1.1, 0.75, 0.15),
    ("lane_n", 6.6, 15.0, 1.0, 0.7, 0.15),
    ("main", 12.0, -1.4, 1.3, 0.85, 0.15),
    ("main", 33.0, 5.3, 1.0, 0.7, 0.14),
    ("main", -38.5, -11.4, 0.9, 0.6, 0.12),     # near the eye-level camera, off to one side of the ruts
    ("lane_n", 4.6, 8.0, 0.9, 0.65, 0.14),
    ("lane_s", -15.4, -14.5, 1.1, 0.75, 0.15),
    ("lane_s", -10.8, -30.0, 1.2, 0.8, 0.15),
]


def s_of_point(rc, x, y):
    d = np.hypot(rc.dense[:, 0] - x, rc.dense[:, 1] - y)
    i = int(np.argmin(d))
    return float(rc.s_dense[i]), float(d[i])


def wet_spot_field(rc, S):
    w = np.zeros(len(S))
    for (rn, x, y, rad) in WET_SPOTS:
        if rn != rc.name:
            continue
        s0, dist = s_of_point(rc, x, y)
        if dist > 4.0:
            continue
        w = np.maximum(w, 1 - smoothstep(rad * 0.45, rad, np.abs(S - s0)))
    return w


# ----------------------------------------------------------------------------
# Hoof prints
# ----------------------------------------------------------------------------
def make_prints(rng, S_lo, S_hi, density, half_band, wetf, depth_dry=(0.006, 0.014), depth_wet=(0.02, 0.045)):
    """Prints along [S_lo, S_hi]; wetf(s) gives 0..1 wetness used to pick the depth."""
    n = rng.poisson(max(0.0, (S_hi - S_lo) * density))
    out = []
    for _ in range(n):
        s = rng.uniform(S_lo, S_hi)
        u = float(np.clip(rng.normal(0, half_band * 0.5), -half_band, half_band))
        w = float(wetf(s))
        d0 = rng.uniform(*depth_dry)
        d1 = rng.uniform(*depth_wet)
        dep = d0 + (d1 - d0) * w
        a = rng.uniform(0.055, 0.07)
        b = a * rng.uniform(1.05, 1.22)
        fwd = 1.0 if rng.uniform() < 0.5 else -1.0
        out.append((s, u, dep, a, b, rng.normal(0, 0.3), fwd, rng.randint(100000)))
    return out


def stamp_prints(Z, S, Uc, prints, extra=None):
    """Deepen Z with hoof prints: bowl with the toe deeper, a broken rim and a lump of mud thrown forward."""
    for (ps, pu, dep, a, b, ang, fwd, sd) in prints:
        r = max(a, b) * 2.2
        i0 = np.searchsorted(S, ps - r)
        i1 = np.searchsorted(S, ps + r)
        if i1 <= i0:
            continue
        uc = Uc[i0:i1]
        cols = np.where(np.any(np.abs(uc - pu) < r, axis=0))[0]
        if len(cols) == 0:
            continue
        j0, j1 = cols.min(), cols.max() + 1
        ds = S[i0:i1, None] - ps
        du = Uc[i0:i1, j0:j1] - pu
        ca, sa = math.cos(ang), math.sin(ang)
        x = (du * ca - ds * sa) / a
        y = (du * sa + ds * ca) / b
        rr = np.sqrt(x * x + y * y)
        th = np.arctan2(y, x)
        # ragged outline
        rr = rr * (1.0 + 0.16 * perlin(np.cos(th) * 1.7 + sd % 97, np.sin(th) * 1.7, sd % 50))
        # a cup with steep sides and a flattish bottom, the toe deeper
        dent = -dep * np.clip(1 - rr ** 4, 0, None) ** 0.7
        dent = dent * (1.0 + 0.35 * np.clip(y * fwd, -1, 1))
        rimamp = 0.18 * dep * (0.3 + 0.7 * np.clip(0.5 + perlin(np.cos(th) * 2.3, np.sin(th) * 2.3 + sd % 31, (sd + 7) % 50), 0, 1.3))
        rim = rimamp * np.exp(-((rr - 1.1) / 0.16) ** 2)
        # a little mud pushed out in front of the toe
        yf = y * fwd
        throw = 0.22 * dep * np.exp(-((yf - 1.35) / 0.3) ** 2 - (x / 0.7) ** 2)
        Z[i0:i1, j0:j1] += dent + rim + throw
        if extra is not None:
            extra[i0:i1, j0:j1] = np.maximum(extra[i0:i1, j0:j1], np.clip(1 - rr, 0, 1))


# ----------------------------------------------------------------------------
# Road cross-section
# ----------------------------------------------------------------------------
def road_profile2(rc, S, U, J=None):
    p = rc.p
    sd = p["seed"]
    nr, nc = len(S), len(U)
    Sg = np.repeat(S[:, None], nc, 1)
    Ug = np.repeat(U[None, :], nr, 0)
    el, er = rc.edges(S)
    E = np.where(Ug >= 0, el[:, None], er[:, None])
    A = np.abs(Ug)
    path = bool(p.get("path"))
    L_ = rc.length
    if path:
        endfade = smoothstep(0.0, 1.4, L_ - Sg)
        E = E * (0.25 + 0.75 * endfade)
    # bank: from nothing to ~11 cm, its foot wandering in and out
    bank_h = (0.012 + 0.095 * smoothstep(-0.45, 0.55, noise1(S / 8.0, sd + 25)) *
              (0.55 + 0.45 * smoothstep(-0.5, 0.5, noise1(S / 2.3, sd + 26))))[:, None]
    if path:
        bank_h = bank_h * 0.6
    core = -bank_h + 0.025 + 0.015 * np.clip(1 - (A / E) ** 2, 0, None)
    foot = 0.5 + 0.32 * np.clip(fbm(Ug / 0.7, Sg / 1.1, 2, sd + 27) + 0.3, -0.4, 1.0)
    bank = smoothstep(E - foot, E - 0.05, A)
    if J is not None:
        bank = bank * (1 - J)
    z = core + bank_h * bank
    z = z - EDGE_DROP * smoothstep(E - 0.05, E + 0.6, A)
    inner = 1 - smoothstep(E - 0.6, E - 0.15, A)
    z = z + (0.009 * fbm(Ug / 0.14, Sg / 0.14, 3, sd + 20) + 0.016 * fbm(Ug / 0.8, Sg / 1.3, 2, sd + 21)) * (0.35 + 0.65 * inner)
    if path:
        z = z - 0.02 * np.exp(-(Ug / (0.55 * E)) ** 2)
    wander = rc.wander(S)[:, None]
    Uc = Ug - wander
    zeros = np.zeros_like(z)
    rut = zeros.copy()
    ridge = zeros.copy()
    hoofband = zeros.copy()
    crown = zeros.copy()
    if p["ruts"]:
        g = p["gauge"] + 0.03 * noise1(S / 13.0, sd + 30)[:, None]
        wet_zone = smoothstep(-0.35, 0.55, noise1(S / 14.0, sd + 31))
        wet_zone = np.maximum(wet_zone, wet_spot_field(rc, S))[:, None]
        dry = smoothstep(-0.55, -0.05, noise1(S / 19.0, sd + 33))[:, None]
        dry = np.maximum(dry, wet_zone)
        depth0 = p["rut_depth"] * (0.35 + 0.85 * wet_zone) * (0.35 + 0.65 * dry)
        tracks = [
            (np.zeros(nr), np.ones(nr), 1.0, 1.0),
            (0.17 + 0.10 * noise1(S / 9.0, sd + 70), smoothstep(0.0, 0.45, noise1(S / 11.0, sd + 71)), 0.65, 0.85),
            (-0.21 + 0.08 * noise1(S / 7.0, sd + 72), smoothstep(0.12, 0.55, noise1(S / 8.0, sd + 73)), 0.5, 0.75),
        ]
        dig = zeros.copy()
        lipf = zeros.copy()
        band = zeros.copy()
        for ti, (off, pres, dfac, wfac) in enumerate(tracks):
            off = off[:, None]
            pres = pres[:, None]
            for k, sgn in enumerate((-1, 1)):
                kk = ti * 2 + k
                wob = (0.035 * noise1(S / 4.5, sd + 80 + kk) + 0.012 * noise1(S / 1.3, sd + 90 + kk))[:, None]
                du = Uc - (sgn * g + off + wob)
                width = (0.07 + 0.07 * smoothstep(-0.5, 0.5, noise1(S / 6.0, sd + 39 + kk))[:, None] + 0.075 * wet_zone) * wfac
                crumble = 0.02 * perlin(Ug / 0.08, Sg / 0.12, sd + 38 + kk) + 0.01 * perlin(Ug / 0.04, Sg / 0.05, sd + 62 + kk)
                prof = np.exp(-((np.abs(du) + crumble) / width) ** 4)
                dmod = (1.0 + 0.35 * noise1(S / 0.85, sd + 37 + kk) + 0.18 * noise1(S / 0.3, sd + 60 + kk))[:, None]
                d_here = depth0 * dfac * pres * np.clip(dmod, 0.5, 1.35)
                lip = np.exp(-((np.abs(du) - width * 1.35) / (0.04 + 0.3 * width)) ** 2)
                lip = lip * (0.45 + 0.55 * np.clip(0.5 + perlin(Ug / 0.15, Sg / 0.25, sd + 64 + kk), 0, 1))
                # pass 2b: the squeezed-up mud lies in broken lumps and crumbs, not as one smooth sausage per rut
                chunk = smoothstep(-0.12, 0.22, perlin(Ug / 0.085, Sg / 0.12, sd + 140 + kk))
                lip = lip * (0.2 + 0.8 * chunk) * (1.0 + 0.45 * perlin(Ug / 0.04, Sg / 0.045, sd + 150 + kk))
                dig = np.maximum(dig, d_here * prof)
                lipf = np.maximum(lipf, 0.34 * d_here * lip)
                # pass 2b: the worn wheel band round each track (compacted, darker, no grass), wider than the rut
                # itself, so from above the road shows two soft worn bands, not two thin crisp lines
                bandw = (0.17 + 0.1 * smoothstep(-0.5, 0.5, noise1(S / 5.0, sd + 120 + kk))[:, None] + 0.06 * wet_zone) * (0.75 + 0.35 * wfac)
                bragged = 0.06 * perlin(Ug / 0.3, Sg / 0.5, sd + 130 + kk)
                band = np.maximum(band, pres * (0.55 + 0.45 * dfac) * np.exp(-((np.abs(du) + bragged) / bandw) ** 2))
                ridge = np.maximum(ridge, lip * pres * (0.4 + 0.6 * wet_zone))
        dig = dig * inner
        lipf = lipf * inner
        z = z + lipf * (1 - np.clip(dig / (0.25 * depth0 + 1e-4), 0, 1)) - dig
        rut = dig / max(p["rut_depth"], 1e-6)
        # hoof-churned middle: slightly raised, lumpy; grass grows where it is not churned
        hoofband = np.exp(-(Uc / 0.36) ** 4)
        z = z + 0.016 * np.exp(-(Uc / 0.33) ** 2)
        z = z + (0.008 + 0.01 * wet_zone) * hoofband * perlin(Ug / 0.07, Sg / 0.07, sd + 66)
        crown = np.exp(-(Uc / 0.4) ** 2)
        # occasional passing tracks outside the main ruts
        for k, sgn in enumerate((-1, 1)):
            du4 = Uc - sgn * (g + 0.92 + 0.1 * noise1(S / 6.0, sd + 40 + k)[:, None])
            amt = np.clip(noise1(S / 10.0, sd + 42 + k)[:, None] * 2.0 + 0.1, 0, 1)
            z = z - 0.022 * amt * np.exp(-(du4 / 0.1) ** 2) * inner
        wet_zone_full = np.broadcast_to(wet_zone, z.shape)
        band = band * inner
    else:
        wet_zone_full = np.zeros_like(z)
        band = np.zeros_like(z)
    start_sink = p.get("start_sink", 0.0)
    if start_sink > 0:
        z = z - p.get("sink_depth", 0.12) * (1 - smoothstep(0.0, start_sink, Sg))
    end_sink = p.get("end_sink", 0.0)
    if end_sink > 0:
        z = z - p.get("sink_depth", 0.12) * (1 - smoothstep(0.0, end_sink, L_ - Sg))
    edgef = smoothstep(E - 0.9, E - 0.05, A)
    return z, dict(E=E, A=A, Uc=Uc, Sg=Sg, Ug=Ug, rut=rut, ridge=ridge, hoofband=hoofband, crown=crown,
                   edgef=edgef, wet_zone=wet_zone_full, inner=inner, band=band)


# ----------------------------------------------------------------------------
# Puddles that the ground itself cuts
# ----------------------------------------------------------------------------
def fill_puddle(Zw, Xw, Yw, S, Uc, s0, u0, la, lb, i0, i1, rng, fill=(0.25, 0.6)):
    """Flood the depression around (s0, u0) in rows i0:i1. Returns (level, cell mask in the window) or None."""
    nr = Zw.shape[0]
    uc = Uc[i0:i1]
    zz = Zw[i0:i1]
    core = (np.abs(uc - u0) < lb * 0.6) & (np.abs(S[i0:i1, None] - s0) < la * 0.6)
    if not core.any():
        return None
    zmin = zz[core].min()
    ring = (np.abs(uc - u0) < lb * 1.3) & (np.abs(S[i0:i1, None] - s0) < la * 1.3) & ~core
    if not ring.any():
        return None
    zrim = np.percentile(zz[ring], 30)
    if zrim - zmin < 0.006:
        return None
    level = zmin + (zrim - zmin) * rng.uniform(*fill)
    ci, cj = np.unravel_index(np.argmin(np.where(core, zz, 1e9)), zz.shape)
    comp = None
    touches = True
    for _ in range(10):
        comp = T.flood(zz < level, (ci, cj))
        touches = comp[0, :].any() or comp[-1, :].any() or comp[:, 0].any() or comp[:, -1].any()
        if not touches:
            break
        level = zmin + (level - zmin) * 0.7
    if comp is None or comp.sum() < 3 or touches:
        return None
    return level, comp


def grow(mask, n):
    m = mask.copy()
    for _ in range(n):
        g = m.copy()
        g[1:] |= m[:-1]
        g[:-1] |= m[1:]
        g[:, 1:] |= m[:, :-1]
        g[:, :-1] |= m[:, 1:]
        m = g
    return m


def water_mesh_from(verts_grid, Zground, comp_full, level, idx):
    """Water quads over the flooded cells plus a two-cell margin; vertices at the water level.
    Returns (verts, faces, depth) with depth = level - ground (negative where ground is above water)."""
    big = grow(comp_full, 2)
    cell = big[:-1, :-1] | big[:-1, 1:] | big[1:, :-1] | big[1:, 1:]
    ii, jj = np.where(cell)
    if len(ii) < 3:
        return None
    used = np.unique(np.concatenate([idx[ii, jj], idx[ii, jj + 1], idx[ii + 1, jj + 1], idx[ii + 1, jj]]))
    remap = -np.ones(idx.size, dtype=np.int64)
    remap[used] = np.arange(len(used))
    wv = verts_grid.reshape(-1, 3)[used].copy()
    depth = level - Zground.reshape(-1)[used]
    wv[:, 2] = level
    wf = np.stack([remap[idx[ii, jj]], remap[idx[ii + 1, jj]], remap[idx[ii + 1, jj + 1]], remap[idx[ii, jj + 1]]], 1)
    return wv, wf, depth


# ----------------------------------------------------------------------------
# Road ribbon
# ----------------------------------------------------------------------------
def build_road_arrays(name, rng_seed=0):
    rc = L.RoadCurve(name)
    p = rc.p
    W = p["width_total"]
    path = bool(p.get("path"))
    if path:
        U = T.lateral_columns(W, [(0.75, 0.025), (W, 0.05)])
        S = T.row_positions(rc, 0.03, 0.03, 1e9)
    else:
        e = p["edge"]
        U = T.lateral_columns(W, [(1.3, 0.03), (e + 0.2, 0.05), (W, 0.09)])
        S = T.row_positions(rc, 0.033, 0.12)
    nr, nc = len(S), len(U)
    cx, cy, tx, ty = rc.at(S)
    nx, ny = -ty, tx
    X = cx[:, None] + nx[:, None] * U[None, :]
    Y = cy[:, None] + ny[:, None] * U[None, :]
    H = L.height(X, Y)
    J = T.junction_flare(name, X, Y)
    R, at = road_profile2(rc, S, U, J)
    TR = T.junction_ruts(name, X, Y)
    R = R - TR * 1.3
    at["rut"] = np.maximum(at["rut"], TR / 0.05)
    rng = np.random.RandomState(p["seed"] + 7 + rng_seed)
    wz_row = at["wet_zone"][:, 0] if at["wet_zone"].ndim == 2 else np.zeros(nr)

    def wetf(s):
        return np.interp(s, S, wz_row)
    prints = []
    printmask = np.zeros((nr, nc))
    fine_rows = np.diff(S) < 0.05
    if p["hooves"] > 0:
        fs = S[:-1][fine_rows]
        if len(fs):
            s0, s1 = fs.min(), fs.max()
            prints = make_prints(rng, s0, s1, 20.0 * p["hooves"], 0.36, wetf)
            prints += make_prints(rng, s0, s1, 3.0 * p["hooves"], 1.3, wetf)
    Z = R.copy()
    if prints:
        stamp_prints(Z, S, at["Uc"], prints, printmask)
    # potholes: more of them in wet stretches
    holes = []
    if p["ruts"]:
        n_pot = int(rc.length / 6.0)
        tries = 0
        while len(holes) < n_pot and tries < n_pot * 4:
            tries += 1
            s0 = rng.uniform(4.0, rc.length - 4.0)
            row = np.searchsorted(S, s0)
            if row >= nr - 2:
                continue
            w_here = wetf(s0)
            if rng.uniform() > 0.25 + 0.75 * w_here:
                continue
            side = rng.choice([-1, 1])
            g = p["gauge"]
            kind = rng.uniform()
            if kind < 0.45:
                u0 = side * g * rng.uniform(0.85, 1.12)
                la, lb = rng.uniform(0.3, 0.9), rng.uniform(0.16, 0.34)
            elif kind < 0.82:
                u0 = rng.uniform(-0.25, 0.25)
                la, lb = rng.uniform(0.3, 0.8), rng.uniform(0.25, 0.5)
            else:
                u0 = rng.uniform(-0.3, 0.3)
                la, lb = rng.uniform(0.8, 1.6), rng.uniform(0.8, 1.3)
            dep = rng.uniform(0.035, 0.075) * (0.7 + 0.5 * w_here)
            i0 = np.searchsorted(S, s0 - la * 1.6)
            i1 = np.searchsorted(S, s0 + la * 1.6)
            uc = at["Uc"][i0:i1]
            dsx = (S[i0:i1, None] - s0) / la
            dux = (uc - u0) / lb
            rr = np.sqrt(dsx ** 2 + dux ** 2)
            ang = np.arctan2(dsx, dux)
            k = len(holes)
            rr = rr * (1.0 + 0.25 * perlin(np.cos(ang) * 1.3 + k, np.sin(ang) * 1.3, p["seed"] + 90 + k % 40))
            bowl = -dep * np.clip(1 - rr ** 2, 0, None) ** 1.1
            bowl += dep * 0.18 * perlin(dux * 2.0, dsx * 2.0, p["seed"] + 77 + k % 40) * np.clip(1 - rr ** 2, 0, None)
            Z[i0:i1] += bowl
            holes.append(dict(s0=s0, u0=u0, la=la, lb=lb, i0=i0, i1=i1))
        # art-directed big puddles (after the random ones, so those keep their shapes)
        for kb, (rn, bx, by, la, lb, dep) in enumerate(BIG_PUDDLES):
            if rn != name:
                continue
            s0, dist = s_of_point(rc, bx, by)
            if dist > 3.0 or s0 < 3.0 or s0 > rc.length - 3.0:
                continue
            cxb, cyb, txb, tyb = rc.at(np.array([s0]))
            u_off = float((bx - cxb[0]) * (-tyb[0]) + (by - cyb[0]) * txb[0])
            u0 = u_off - float(rc.wander(np.array([s0]))[0])
            i0 = np.searchsorted(S, s0 - la * 1.7)
            i1 = np.searchsorted(S, s0 + la * 1.7)
            if i1 - i0 < 3:
                continue
            uc = at["Uc"][i0:i1]
            dsx = (S[i0:i1, None] - s0) / la
            dux = (uc - u0) / lb
            rr = np.sqrt(dsx ** 2 + dux ** 2)
            ang = np.arctan2(dsx, dux)
            k = 50 + kb
            rr = rr * (1.0 + 0.3 * perlin(np.cos(ang) * 1.5 + k, np.sin(ang) * 1.5, p["seed"] + 150 + kb)
                       + 0.1 * perlin(np.cos(ang) * 4.0 - k, np.sin(ang) * 4.0, p["seed"] + 160 + kb))
            # a broad mud hole deeper than the ruts that drain into it, so it holds a wide sheet of water
            bowl = -dep * np.clip(1 - rr ** 2, 0, None) ** 0.55
            bowl += dep * 0.12 * perlin(dux * 2.5, dsx * 2.5, p["seed"] + 170 + kb) * np.clip(1 - rr ** 2, 0, None)
            Z[i0:i1] += bowl
            holes.append(dict(s0=s0, u0=u0, la=la, lb=lb, i0=i0, i1=i1, big=True))
    Zw = H + Z
    verts_grid = np.stack([X, Y, Zw], -1)
    idx = np.arange(nr * nc).reshape(nr, nc)
    # water
    water = []
    shore = np.zeros((nr, nc))
    for pd in holes:
        i0, i1 = pd["i0"], pd["i1"]
        if i1 - i0 < 3:
            continue
        res = fill_puddle(Zw, X, Y, S, at["Uc"], pd["s0"], pd["u0"], pd["la"], pd["lb"], i0, i1, rng,
                          fill=(0.6, 0.8) if pd.get("big") else (0.25, 0.6))
        if res is None:
            continue
        level, comp = res
        comp_full = np.zeros((nr, nc), dtype=bool)
        comp_full[i0:i1] = comp
        wm = water_mesh_from(verts_grid, Zw, comp_full, level, idx)
        if wm is None:
            continue
        water.append(wm)
        hz = Zw[i0:i1] - level
        win = (np.abs(at["Uc"][i0:i1] - pd["u0"]) < pd["lb"] * 2.5) & (np.abs(S[i0:i1, None] - pd["s0"]) < pd["la"] * 2.5)
        shore[i0:i1] = np.maximum(shore[i0:i1], np.clip(1.0 - hz / 0.045, 0, 1) * win)
    # small water in the deepest wet prints and rut dips (thin film): flag for the shader only
    # wetness in the ruts comes and goes along the road (water stands in the low stretches only)
    along = 0.12 + 0.88 * smoothstep(-0.25, 0.35, fbm(at["Ug"] / 3.0, at["Sg"] / 2.2, 2, p["seed"] + 57))
    film = np.clip((at["rut"] - 0.9) * 1.5, 0, 1) * at["wet_zone"] * smoothstep(0.55, 0.9, along)
    wet = np.clip(at["rut"] * (0.25 + 0.75 * at["wet_zone"]) * along, 0, 1)
    wet = np.maximum(wet, shore)
    wet = np.maximum(wet, printmask * at["wet_zone"] * 0.9)
    # grass: patchy crown and ragged edges (not on wet or rutted ground)
    # pass 2b: a fuller grass crown (an unkept road grows grass between the wheel tracks)
    gc = min(1.0, 1.6 * p.get("grass_center", 0.0))
    gmask = np.zeros((nr, nc))
    if p["ruts"]:
        patch = smoothstep(-0.5, 0.12, fbm(at["Ug"] / 0.6, at["Sg"] / 2.2, 2, p["seed"] + 50))
        gmask = at["crown"] * gc * patch * (1 - 0.5 * at["wet_zone"])
    ragged = smoothstep(-0.35, 0.35, fbm(at["Ug"] / 0.35, at["Sg"] / 0.6, 3, p["seed"] + 51))
    edge_g = smoothstep(0.25, 0.85, at["edgef"]) * (0.35 + 0.65 * ragged)
    gmask = np.maximum(gmask, edge_g)
    # bigger bites of grass reaching in from the verge (seen from above the edge is not one clean line)
    bite = smoothstep(0.05, 0.45, fbm(at["Ug"] / 1.4, at["Sg"] / 2.6, 3, p["seed"] + 59))
    reach = 1 - smoothstep(0.0, 0.3 + 1.3 * bite, (at["E"] - at["A"]))
    gmask = np.maximum(gmask, 0.9 * reach * bite * (1 - np.clip(at["rut"] * 3, 0, 1)))
    if p["ruts"]:
        # tufts in the little-used strips between the outer ruts and the verge
        g0 = p["gauge"]
        margin = smoothstep(g0 + 0.22, g0 + 0.5, np.abs(at["Uc"])) * (1 - smoothstep(at["E"] - 0.75, at["E"] - 0.3, at["A"]))
        mpatch = smoothstep(0.1, 0.45, fbm(at["Ug"] / 0.4, at["Sg"] / 0.7, 3, p["seed"] + 58))
        gmask = np.maximum(gmask, 0.75 * margin * mpatch)
    gmask = gmask * (1 - np.clip(wet * 1.6, 0, 1)) * (1 - np.clip(at["rut"] * 2.5, 0, 1)) * (1 - 0.8 * printmask)
    gmask = gmask * (1 - 0.85 * at["band"])
    # stones: clumped, more near the verges and pushed aside out of the ruts, few in the churned middle
    clump = 0.05 + 0.95 * smoothstep(0.1, 0.5, fbm(at["Ug"] / 0.5, at["Sg"] / 0.9, 3, p["seed"] + 52))
    pebm = clump * (1 - 0.85 * np.clip(at["rut"] * 2, 0, 1)) * (1 - np.clip(wet * 1.3, 0, 1)) * (0.45 + 0.55 * smoothstep(0.1, 0.7, at["edgef"])) * (1 - 0.5 * at["hoofband"])
    pebm = pebm * (1 - 0.6 * at["band"])
    pattrs = {
        "rut": np.clip(at["rut"], 0, 1.5).ravel(),
        "edgef": at["edgef"].ravel(),
        "wet": wet.ravel(),
        "gmask": gmask.ravel(),
        "hoof": at["hoofband"].ravel(),
        "pathf": np.full(nr * nc, 1.0 if path else 0.0),
        "pebm": pebm.ravel(),
        "wetzone": np.asarray(at["wet_zone"]).ravel(),
        "ridge": at["ridge"].ravel(),
        "crown": at["crown"].ravel(),
        "shore": shore.ravel(),
        "film": film.ravel(),
        "prints": printmask.ravel(),
        "band": at["band"].ravel(),
    }
    faces = np.stack([idx[:-1, :-1].ravel(), idx[1:, :-1].ravel(), idx[1:, 1:].ravel(), idx[:-1, 1:].ravel()], 1)
    UV = np.stack([at["Uc"], at["Sg"]], -1).reshape(-1, 2)
    loop_uv = UV[faces.ravel()]
    info = dict(rows=nr, cols=nc, verts=nr * nc, prints=len(prints), holes=len(holes), puddles=len(water), length=round(rc.length, 1))
    return dict(verts=verts_grid.reshape(-1, 3), faces=faces, loop_uv=loop_uv, pattrs=pattrs, water=water, info=info,
                S=S, U=U, X=X, Y=Y, Z=Zw, idx=idx, uv_vert=UV)


def swap_mesh(ob, me):
    old = ob.data
    mats = [m for m in old.materials]
    ob.data = me
    if not me.materials:
        for m in mats:
            me.materials.append(m)
    if old.users == 0:
        bpy.data.meshes.remove(old)


def water_object(name, water, col, mat):
    ob = bpy.data.objects.get(name)
    if not water:
        if ob is not None:
            bpy.data.objects.remove(ob, do_unlink=True)
        return None
    allv, allf, alld = [], [], []
    off = 0
    for wv, wf, dep in water:
        allv.append(wv)
        allf.append(wf + off)
        alld.append(dep)
        off += len(wv)
    V = np.concatenate(allv)
    F = np.concatenate(allf)
    # pass 2b: every water face must face up. The yard grids run (y, x), so their water came out facing down and
    # rendered as flat brown patches (and as pass 1's "black hole" in the stable-yard puddle)
    a, b, c = V[F[:, 0]], V[F[:, 1]], V[F[:, 2]]
    nz = (b[:, 0] - a[:, 0]) * (c[:, 1] - a[:, 1]) - (b[:, 1] - a[:, 1]) * (c[:, 0] - a[:, 0])
    F = np.where((nz < 0)[:, None], F[:, ::-1], F)
    me = mesh_from_arrays(name, V, F, point_attrs={"wdepth": np.concatenate(alld)}, smooth=False, materials=[mat])
    if ob is None:
        ob = C.new_object(name, me, col)
    else:
        swap_mesh(ob, me)
        ob.data.materials.clear()
        ob.data.materials.append(mat)
    return ob


LAST = {}


def named_attr(nb, name):
    n = nb.node('GeometryNodeInputNamedAttribute', data_type='FLOAT')
    n.inputs['Name'].default_value = name
    return nb.out(n, 'Attribute')


def disp_group():
    """Geometry nodes: subdivide a road patch and push it up and down with the same clods, lumps and crumbs
    the road shader uses (flat x, y coordinates), masked by 'dispmask' so the patch border stays put."""
    name = "GN_mud_relief"
    ng = bpy.data.node_groups.get(name)
    if ng:
        bpy.data.node_groups.remove(ng)
    ng = bpy.data.node_groups.new(name, 'GeometryNodeTree')
    ng.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    lv = ng.interface.new_socket('Level', in_out='INPUT', socket_type='NodeSocketInt')
    lv.default_value = 2
    scs = ng.interface.new_socket('Scale', in_out='INPUT', socket_type='NodeSocketFloat')
    scs.default_value = 0.025
    ng.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    nb = C.NB(ng)
    gin = nb.node('NodeGroupInput')
    gout = nb.node('NodeGroupOutput')
    sub = nb.node('GeometryNodeSubdivideMesh')
    nb.links.new(gin.outputs[0], sub.inputs['Mesh'])
    nb.links.new(gin.outputs[1], sub.inputs['Level'])
    import materials2 as M2
    pos = nb.out(nb.node('GeometryNodeInputPosition'))
    flat = nb.vmath('MULTIPLY', pos, (1.0, 1.0, 0.0))
    A = {k: named_attr(nb, k) for k in ('hoof', 'ridge', 'prints', 'rut', 'wet', 'shore', 'film', 'wetzone', 'dispmask', 'band')}
    Wf = M2.wetness(nb, A['wet'], A['shore'], A['film'], A['prints'], A['wetzone'])
    R = M2.relief_field(nb, flat, A['hoof'], A['ridge'], A['prints'], A['rut'], Wf, band=A['band'])
    # no push on steep rut walls (it would smear them); the patch border stays where it is
    nrm = nb.out(nb.node('GeometryNodeInputNormal'))
    slope = nb.maprange(nb.sep(nrm)[2], 0.6, 0.86, 0.0, 1.0)   # pass 2b: the lips beside the ruts get relief too
    d = nb.math('MULTIPLY', nb.math('MULTIPLY', nb.math('SUBTRACT', R['h'], 0.25), nb.math('MULTIPLY', A['dispmask'], slope)), gin.outputs[2])
    off = nb.comb(0.0, 0.0, d)
    sp = nb.node('GeometryNodeSetPosition')
    nb.links.new(nb.out(sub), sp.inputs['Geometry'])
    nb.links.new(off, sp.inputs['Offset'])
    nb.links.new(nb.out(sp), gout.inputs[0])
    return ng


def patch_rows(S, s0, s1):
    i0 = int(np.searchsorted(S, s0))
    i1 = int(min(np.searchsorted(S, s1), len(S) - 1))
    return i0, i1


def rebuild_road(name, road_mat, water_mat, patches=(), patch_mat=None):
    """Rebuild a road mesh in place. patches: list of (patch_name, s0, s1): those rows become a separate object
    (sharing the border vertices exactly) that geometry nodes subdivide and displace for close views."""
    d = build_road_arrays(name)
    LAST[name] = d
    S, U = d["S"], d["U"]
    nr, nc = len(S), len(U)
    faces = d["faces"]
    keep = np.ones(len(faces), bool)
    ob = bpy.data.objects["road_" + name]
    col = ob.users_collection[0]
    made = {}
    for (pname, s0, s1) in patches:
        i0, i1 = patch_rows(S, s0, s1)
        if i1 - i0 < 4:
            continue
        fi = (np.arange(i0, i1)[:, None] * (nc - 1) + np.arange(nc - 1)[None, :]).ravel()
        keep[fi] = False
        rows = np.arange(i0, i1 + 1)
        vid = (rows[:, None] * nc + np.arange(nc)[None, :])
        pv = d["verts"][vid.ravel()]
        lidx = np.arange(len(rows) * nc).reshape(len(rows), nc)
        pf = np.stack([lidx[:-1, :-1].ravel(), lidx[1:, :-1].ravel(), lidx[1:, 1:].ravel(), lidx[:-1, 1:].ravel()], 1)
        pat = {k: v.reshape(nr, nc)[i0:i1 + 1].ravel() for k, v in d["pattrs"].items()}
        Sp = S[i0:i1 + 1]
        fade = smoothstep(0.0, 0.45, Sp - Sp[0]) * smoothstep(0.0, 0.45, Sp[-1] - Sp)
        pat["dispmask"] = np.repeat(fade[:, None], nc, 1).ravel()
        uvv = d["uv_vert"].reshape(nr, nc, 2)[i0:i1 + 1].reshape(-1, 2)
        loop_uv = uvv[pf.ravel()]
        pme = mesh_from_arrays("road_" + pname, pv, pf, loop_uv=loop_uv, point_attrs=pat, smooth=True, materials=[patch_mat or road_mat])
        pob = bpy.data.objects.get("road_" + pname)
        if pob is None:
            pob = C.new_object("road_" + pname, pme, col)
        else:
            swap_mesh(pob, pme)
            pob.data.materials.clear()
            pob.data.materials.append(patch_mat or road_mat)
        for m in list(pob.modifiers):
            pob.modifiers.remove(m)
        mod = pob.modifiers.new("relief", 'NODES')
        mod.node_group = bpy.data.node_groups.get("GN_mud_relief") or disp_group()
        made[pname] = dict(rows=int(i1 - i0), faces=int(len(pf)))
    me = mesh_from_arrays("road_" + name, d["verts"], faces[keep], loop_uv=d["loop_uv"].reshape(-1, 4, 2)[keep].reshape(-1, 2),
                          point_attrs=d["pattrs"], smooth=True, materials=[road_mat])
    swap_mesh(ob, me)
    ob.data.materials.clear()
    ob.data.materials.append(road_mat)
    water_object("puddles_" + name, d["water"], col, water_mat)
    info = dict(d["info"])
    info["patches"] = made
    return info


# ----------------------------------------------------------------------------
# Yards (trampled dirt patches)
# ----------------------------------------------------------------------------
def build_yard2(yd, road_mat, water_mat, arcs=None):
    rx, ry = yd["rx"] + 1.0, yd["ry"] + 1.0
    sp = 0.03 if yd.get("hooves", 0) > 0 else 0.034
    lxs = np.arange(-rx, rx + 1e-6, sp)
    lys = np.arange(-ry, ry + 1e-6, sp)
    LX, LY = np.meshgrid(lxs, lys)
    c, s = math.cos(math.radians(yd["rot"])), math.sin(math.radians(yd["rot"]))
    X = yd["x"] + LX * c - LY * s
    Y = yd["y"] + LX * s + LY * c
    H = L.height(X, Y)
    t, _, _ = T.yard_signed_dist(yd, X, Y)
    sd = yd["seed"]
    stable_yard = yd.get("hooves", 0) > 0
    bank_h = 0.05
    Jy = np.zeros(X.shape)
    curves = L.road_curves()
    for rn, rc in curves.items():
        if rc.p.get("path") and rn != "path_d" and rn != "path_well":
            continue
        ss = np.arange(0, rc.length, 0.25)
        cx_, cy_, _, _ = rc.at(ss)
        near = (np.abs(cx_ - yd["x"]) < yd["rx"] + 4) & (np.abs(cy_ - yd["y"]) < yd["rx"] + 4)
        if near.sum() < 2:
            continue
        poly = np.stack([cx_[near], cy_[near]], 1)
        box = (np.abs(X - yd["x"]) < rx + 1) & (np.abs(Y - yd["y"]) < rx + 1)
        d, _ = T._seg_dist(np.stack([X[box], Y[box]], 1), poly)
        Er = rc.p["edge"]
        Jy[box] = np.maximum(Jy[box], 1 - smoothstep(Er * 0.5, Er + 0.9, d))
    bank_var = bank_h * (0.3 + 0.7 * smoothstep(-0.4, 0.4, fbm(X / 1.5, Y / 1.5, 2, sd + 9)))
    z = -bank_h + 0.025 + 0.012 * np.clip(-t / 3.0, 0, 1)
    z = z + bank_var * smoothstep(-0.55, -0.05, t) * (1 - Jy)
    z = z - EDGE_DROP * smoothstep(-0.05, 0.6, t)
    inner = 1 - smoothstep(-0.6, -0.15, t)
    z = z + (0.009 * fbm(X / 0.16, Y / 0.16, 3, sd + 3) + 0.016 * fbm(X / 1.1, Y / 1.1, 2, sd + 4)) * (0.35 + 0.65 * inner)
    rng = np.random.RandomState(sd + 3)
    rut = np.zeros_like(z)
    ridge = np.zeros_like(z)
    if arcs:
        for ai, (ax, ay, R, depth) in enumerate(arcs):
            dd = np.sqrt((X - ax) ** 2 + (Y - ay) ** 2)
            th = np.arctan2(Y - ay, X - ax)
            for oi, off in enumerate((-0.74, 0.74)):
                wob = 0.04 * perlin(th * R / 3.0, 0.3 + ai + oi, sd + 20 + oi)
                du = dd - (R + off + wob)
                width = 0.09 + 0.05 * (0.5 + 0.5 * perlin(th * R / 2.0, 1.7 + oi, sd + 30 + oi))
                rr = np.exp(-(np.abs(du) / width) ** 4)
                lip = np.exp(-((np.abs(du) - width * 1.35) / 0.06) ** 2)
                rut = np.maximum(rut, rr * depth * 1.3 / 0.06)
                ridge = np.maximum(ridge, lip)
                z = z - depth * 1.3 * rr * inner + 0.35 * depth * lip * (1 - rr) * inner
    printmask = np.zeros_like(z)
    if stable_yard:
        # churned ground: hoof prints everywhere, thickest near the stalls and the trough
        area = (2 * yd["rx"]) * (2 * yd["ry"])
        n = int(area * 9 * yd["hooves"])
        nr_, nc_ = LX.shape
        # pass 2b: prints follow where horses actually walk and stand - in front of the stalls, the trough and the
        # hitching rail, and the tracks out to the lane and the paddock gate - instead of an even sprinkle of dots
        rngp = np.random.RandomState(sd + 77)

        def traffic(px, py):
            f = 0.07
            f += 0.85 * math.exp(-((py - 3.4) / 1.0) ** 2) * (1.0 - float(smoothstep(2.6, 4.2, abs(px + 1.8))))
            t = min(max((3.0 - py) / 8.0, 0.0), 1.0)
            f += 0.75 * math.exp(-((px - (-1.5 + 2.3 * t)) / 1.1) ** 2) * (1.0 if py < 3.6 else 0.0)
            f += 0.85 * math.exp(-((px + 6.8) ** 2 + (py - 3.4) ** 2) / 1.6 ** 2)
            f += 0.6 * math.exp(-((px + 2.6) ** 2 + (py - 1.9) ** 2) / 1.3 ** 2)
            if -0.5 < px < 9.0:
                f += 0.5 * math.exp(-((py - (2.5 - 1.5 * min(max(px / 8.5, 0.0), 1.0))) / 1.0) ** 2)
            return min(f, 1.0)
        placed = 0
        tries = 0
        while placed < n and tries < n * 20:
            tries += 1
            px = rngp.uniform(-yd["rx"], yd["rx"])
            py = rngp.uniform(-yd["ry"], yd["ry"])
            if rngp.uniform() > traffic(px, py):
                continue
            placed += 1
            j = int((px + rx) / sp)
            i = int((py + ry) / sp)
            i0, i1 = max(i - 7, 0), min(i + 8, nr_)
            j0, j1 = max(j - 7, 0), min(j + 8, nc_)
            ang = rng.uniform(0, 2 * math.pi)
            a = rng.uniform(0.055, 0.07)
            b = a * rng.uniform(1.05, 1.2)
            dx = LX[i0:i1, j0:j1] - px
            dy = LY[i0:i1, j0:j1] - py
            ca, sa = math.cos(ang), math.sin(ang)
            xx = (dx * ca - dy * sa) / a
            yy = (dx * sa + dy * ca) / b
            rr = np.sqrt(xx * xx + yy * yy)
            th = np.arctan2(yy, xx)
            rr = rr * (1.0 + 0.15 * np.sin(3 * th + rng.uniform(0, 6)) + 0.08 * np.sin(5 * th + rng.uniform(0, 6)))
            dep = rng.uniform(0.012, 0.035)
            rim = 0.4 * dep * (0.5 + 0.5 * np.sin(2 * th + rng.uniform(0, 6))) * np.exp(-((rr - 1.12) / 0.2) ** 2)
            throw = 0.45 * dep * np.exp(-((yy - 1.45) / 0.35) ** 2 - (xx / 0.8) ** 2)
            z[i0:i1, j0:j1] += (-dep * np.clip(1 - rr ** 2, 0, None) ** 0.9 * (1 + 0.35 * np.clip(yy, -1, 1)) + rim + throw) * inner[i0:i1, j0:j1]
            printmask[i0:i1, j0:j1] = np.maximum(printmask[i0:i1, j0:j1], np.clip(1 - rr, 0, 1))
        # a churned, lumpy layer of mud over the whole yard
        z = z + 0.012 * perlin(X / 0.07, Y / 0.07, sd + 40) * inner
    wet = np.zeros_like(z)
    if stable_yard:
        # damp, trodden mud in broad patches, wettest in front of the stalls and round the trough
        wet = 0.45 * smoothstep(-0.15, 0.4, fbm(X / 2.5, Y / 2.5, 2, sd + 60))
        wet = np.maximum(wet, 0.7 * (1 - smoothstep(0.0, 2.5, np.abs(LY - yd["ry"] * 0.85))) * smoothstep(-0.2, 0.3, fbm(X / 1.2, Y / 1.2, 2, sd + 61)))
    shore = np.zeros_like(z)
    water = []
    nh = 8 if stable_yard else 0
    idx = np.arange(z.size).reshape(z.shape)
    hollows = []
    for k in range(nh):
        hx = rng.uniform(-yd["rx"] * 0.75, yd["rx"] * 0.75)
        hy = rng.uniform(-yd["ry"] * 0.7, yd["ry"] * 0.55)
        la, lb = rng.uniform(0.45, 1.2), rng.uniform(0.3, 0.75)
        dep = rng.uniform(0.035, 0.065)
        rr = np.sqrt(((LX - hx) / la) ** 2 + ((LY - hy) / lb) ** 2)
        th = np.arctan2((LY - hy) / lb, (LX - hx) / la)
        rr = rr * (1 + 0.2 * perlin(np.cos(th) * 1.4 + k, np.sin(th) * 1.4, sd + 50 + k))
        z = z - dep * np.clip(1 - rr ** 2, 0, None) ** 1.1
        hollows.append((rr, hx, hy))
        wet = np.maximum(wet, np.clip(1 - (rr - 1.0) / 0.9, 0, 1) * 0.8)
    Z = H + z
    for (rr, hx, hy) in hollows:
        core = rr < 0.5
        ring = (rr > 1.0) & (rr < 1.4)
        if not core.any() or not ring.any():
            continue
        zmin = Z[core].min()
        zrim = np.percentile(Z[ring], 30)
        if zrim - zmin < 0.006:
            continue
        level = zmin + (zrim - zmin) * rng.uniform(0.5, 0.75)
        ci, cj = np.unravel_index(np.argmin(np.where(core, Z, 1e9)), Z.shape)
        comp = T.flood((Z < level) & (rr < 2.5), (ci, cj))
        for _ in range(8):
            if not (comp & (rr > 2.3)).any():
                break
            level = zmin + (level - zmin) * 0.7
            comp = T.flood((Z < level) & (rr < 2.5), (ci, cj))
        if comp.sum() < 3:
            continue
        wm = water_mesh_from(np.stack([X, Y, Z], -1), Z, comp, level, idx)
        if wm is not None:
            water.append(wm)
            shore = np.maximum(shore, np.clip(1.0 - (Z - level) / 0.045, 0, 1) * (rr < 2.6))
    nr, nc = LX.shape
    keep_v = t < 0.75
    cellkeep = keep_v[:-1, :-1] | keep_v[:-1, 1:] | keep_v[1:, :-1] | keep_v[1:, 1:]
    ii, jj = np.where(cellkeep)
    used = np.unique(np.concatenate([idx[ii, jj], idx[ii, jj + 1], idx[ii + 1, jj + 1], idx[ii + 1, jj]]))
    remap = -np.ones(nr * nc, dtype=np.int64)
    remap[used] = np.arange(len(used))
    verts = np.stack([X, Y, Z], -1).reshape(-1, 3)[used]
    faces = np.stack([remap[idx[ii, jj]], remap[idx[ii, jj + 1]], remap[idx[ii + 1, jj + 1]], remap[idx[ii + 1, jj]]], 1)
    UVa = np.stack([X, Y], -1).reshape(-1, 2)[used]
    loop_uv = UVa[faces.ravel()]
    edgef = smoothstep(-0.9, -0.05, t)
    ragged = smoothstep(-0.35, 0.35, fbm(X / 0.35, Y / 0.35, 3, sd + 51))
    gm = smoothstep(0.25, 0.85, edgef) * (0.35 + 0.65 * ragged)
    wetall = np.maximum(np.maximum(wet, rut * 0.6), shore)
    if stable_yard:
        wetall = np.maximum(wetall, printmask * 0.7)
    gm = gm * (1 - np.clip(wetall * 1.5, 0, 1))
    clump = smoothstep(0.05, 0.45, fbm(X / 0.5, Y / 0.5, 3, sd + 52))
    pattrs = {
        "rut": (rut.ravel()[used]).clip(0, 1.5),
        "edgef": edgef.ravel()[used],
        "wet": wetall.ravel()[used],
        "gmask": gm.ravel()[used],
        "hoof": np.full(len(used), 0.7 if stable_yard else 0.0),
        "pathf": np.full(len(used), 0.0 if stable_yard else 1.0),
        "pebm": ((1 - np.clip(wetall, 0, 1)) * (0.4 + 0.6 * edgef) * clump).ravel()[used],
        "wetzone": np.full(len(used), 0.85 if stable_yard else 0.25),
        "ridge": ridge.ravel()[used],
        "crown": np.zeros(len(used)),
        "shore": shore.ravel()[used],
        "film": np.zeros(len(used)),
        "prints": printmask.ravel()[used],
    }
    name = "yard_%d" % yd["seed"]
    me = mesh_from_arrays(name, verts, faces, loop_uv=loop_uv, point_attrs=pattrs, smooth=True, materials=[road_mat])
    ob = bpy.data.objects[name]
    swap_mesh(ob, me)
    ob.data.materials.clear()
    ob.data.materials.append(road_mat)
    water_object(name + "_water", water, ob.users_collection[0], water_mat)
    return dict(verts=len(verts), puddles=len(water))
