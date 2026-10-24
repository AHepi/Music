"""Terrain, rutted dirt roads, footpaths, trodden yards and puddles."""
import bpy
import numpy as np
import math
from mathutils import kdtree, Vector
from mathutils.bvhtree import BVHTree
import common as C
from common import fbm, perlin, noise1, smoothstep, mesh_from_arrays
import layout as L

SHOULDER = 0.04
EDGE_DROP = 0.21
LOWER = 0.36


# ----------------------------------------------------------------------------
# lateral / longitudinal sampling
# ----------------------------------------------------------------------------
def lateral_columns(W, bands):
    pos = [0.0]
    u = 0.0
    for lim, sp in bands:
        while u + sp <= lim + 1e-9:
            u += sp
            pos.append(u)
    if pos[-1] < W - 1e-6:
        pos.append(W)
    pos = np.array(pos)
    return np.concatenate([-pos[:0:-1], pos])


def row_positions(rc, ds_fine, ds_coarse, fine_radius=50.0):
    d = np.hypot(rc.dense[:, 0] - L.VILLAGE_C[0], rc.dense[:, 1] - L.VILLAGE_C[1])
    out = [0.0]
    s = 0.0
    while s < rc.length - 1e-9:
        dd = np.interp(s, rc.s_dense, d)
        ds = ds_fine if dd < fine_radius else ds_coarse
        s = min(s + ds, rc.length)
        out.append(s)
    return np.array(out)


# ----------------------------------------------------------------------------
# hoof prints, potholes
# ----------------------------------------------------------------------------
def stamp_prints(Z, S, Uc, prints, ds_hint):
    """Z, Uc: (nr,nc) arrays, S: (nr,) row positions. prints: list of (s, u, depth, a, b, ang)."""
    for (ps, pu, dep, a, b, ang) in prints:
        r = max(a, b) * 1.6
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
        dent = -dep * np.clip(1 - rr ** 2, 0, None) ** 1.5
        # toe deeper than heel: tilt
        dent = dent * (1.0 + 0.35 * np.clip(y, -1, 1))
        rim = 0.30 * dep * np.exp(-((rr - 1.15) / 0.22) ** 2)
        Z[i0:i1, j0:j1] += dent + rim


def make_prints(rng, s0, s1, density, uc_center, half_band, depth=(0.014, 0.03)):
    n = rng.poisson(max(0.0, (s1 - s0) * density))
    out = []
    for _ in range(n):
        s = rng.uniform(s0, s1)
        u = uc_center + rng.normal(0, half_band * 0.5)
        u = float(np.clip(u, uc_center - half_band, uc_center + half_band))
        out.append((s, u, rng.uniform(*depth), rng.uniform(0.055, 0.068), rng.uniform(0.062, 0.078), rng.normal(0, 0.25)))
    return out


# ----------------------------------------------------------------------------
# Road ribbon
# ----------------------------------------------------------------------------
def road_profile(rc, S, U, J=None):
    """S (nr,), U (nc,). Returns Z offset (nr,nc) and attribute dict."""
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
    start_sink = p.get("start_sink", 0.0)
    if path:
        endfade = smoothstep(0.0, 1.4, L_ - Sg)
        E = E * (0.25 + 0.75 * endfade)
    # sunken, worn road bed with a low grassy bank at the verge
    bank_h = (0.05 + 0.045 * smoothstep(-0.4, 0.5, noise1(S / 9.0, sd + 25)))[:, None]
    if path:
        bank_h = bank_h * 0.6
    core = -bank_h + 0.025 + 0.015 * np.clip(1 - (A / E) ** 2, 0, None)
    bank = smoothstep(E - 0.55, E - 0.05, A)
    if J is not None:
        bank = bank * (1 - J)
    z = core + bank_h * bank
    z = z - EDGE_DROP * smoothstep(E - 0.05, E + 0.6, A)
    inner = 1 - smoothstep(E - 0.6, E - 0.15, A)
    z = z + (0.008 * fbm(Ug / 0.14, Sg / 0.14, 3, sd + 20) + 0.014 * fbm(Ug / 0.8, Sg / 1.3, 2, sd + 21)) * (0.35 + 0.65 * inner)
    if path:
        z = z - 0.018 * np.exp(-(Ug / (0.55 * E)) ** 2)

    rut = np.zeros_like(z)
    wander = rc.wander(S)[:, None]
    Uc = Ug - wander
    hoofband = np.zeros_like(z)
    if p["ruts"]:
        g = p["gauge"] + 0.022 * noise1(S / 13.0, sd + 30)[:, None]
        wet_zone = smoothstep(-0.35, 0.55, noise1(S / 14.0, sd + 31))[:, None]
        dry = smoothstep(-0.55, -0.05, noise1(S / 19.0, sd + 33))[:, None]
        depth = p["rut_depth"] * (0.45 + 1.0 * wet_zone) * (0.3 + 0.7 * dry)
        for k, sgn in enumerate((-1, 1)):
            # bumpy rut bottom along its length and ragged, crumbling walls
            dmod = (1.0 + 0.32 * noise1(S / 0.85, sd + 37 + k) + 0.15 * noise1(S / 0.3, sd + 60 + k))[:, None]
            width = (0.105 * (0.78 + 0.5 * smoothstep(-0.5, 0.5, noise1(S / 6.0, sd + 39 + k))))[:, None]
            crumble = 0.022 * perlin(Ug / 0.09, Sg / 0.13, sd + 38 + k) + 0.01 * perlin(Ug / 0.045, Sg / 0.06, sd + 62 + k)
            du = Uc - sgn * g
            r1 = np.exp(-((np.abs(du) + crumble) / width) ** 4)
            du2 = Uc - sgn * (g + 0.16 * noise1(S / 9.0, sd + 32 + k)[:, None])
            r2 = 0.62 * np.exp(-((np.abs(du2) + 0.6 * crumble) / (0.8 * width)) ** 2)
            du3 = Uc - sgn * (g - 0.14 + 0.06 * noise1(S / 8.0, sd + 34 + k)[:, None])
            r3 = 0.33 * np.exp(-(du3 / 0.09) ** 2)
            rr = np.maximum(np.maximum(r1, r2), r3)
            rr = rr * (1.0 + 0.12 * perlin(du / 0.04, Sg / 0.9, sd + 36 + k))
            bermh = 0.26 * (0.6 + 0.8 * smoothstep(-0.5, 0.5, perlin(Ug / 0.3, Sg / 0.8, sd + 64 + k)))
            berm = np.exp(-((np.abs(du) - width * 1.8) / 0.06) ** 2)
            z = z + depth * bermh * berm * (1 - rr)
            z = z - depth * dmod * rr
            rut = np.maximum(rut, rr * dmod)
        # hoof-churned centre strip slightly raised and lumpy
        z = z + 0.018 * np.exp(-(Uc / 0.33) ** 2)
        hoofband = np.exp(-(Uc / 0.36) ** 4)
        z = z + 0.008 * hoofband * perlin(Ug / 0.07, Sg / 0.07, sd + 66)
        # occasional passing tracks outside the main ruts
        for k, sgn in enumerate((-1, 1)):
            du4 = Uc - sgn * (g + 0.92 + 0.1 * noise1(S / 6.0, sd + 40 + k)[:, None])
            amt = np.clip(noise1(S / 10.0, sd + 42 + k)[:, None] * 2.0 + 0.1, 0, 1)
            z = z - 0.022 * amt * np.exp(-(du4 / 0.1) ** 2) * inner
        rut_norm = rut * (depth / max(p["rut_depth"], 1e-6))
    else:
        wet_zone = np.zeros((nr, 1))
        rut_norm = rut
    if start_sink > 0:
        z = z - p.get("sink_depth", 0.12) * (1 - smoothstep(0.0, start_sink, Sg))
    end_sink = p.get("end_sink", 0.0)
    if end_sink > 0:
        z = z - p.get("sink_depth", 0.12) * (1 - smoothstep(0.0, end_sink, L_ - Sg))
    edgef = smoothstep(E - 0.9, E - 0.05, A)
    return z, dict(E=E, A=A, Uc=Uc, Sg=Sg, Ug=Ug, rut=rut_norm, hoofband=hoofband, edgef=edgef, wet_zone=np.broadcast_to(wet_zone, z.shape), inner=inner)


def _seg_dist(P, poly):
    """Distance from points P (n,2) to polyline poly (m,2). Returns (dist, arclength param)."""
    A = poly[:-1]
    B = poly[1:]
    AB = B - A
    L2 = (AB ** 2).sum(1) + 1e-12
    seglen = np.sqrt(L2)
    cum = np.concatenate([[0], np.cumsum(seglen)])[:-1]
    best = np.full(len(P), 1e9)
    bests = np.zeros(len(P))
    for k in range(len(A)):
        tt = np.clip(((P - A[k]) * AB[k]).sum(1) / L2[k], 0, 1)
        proj = A[k] + tt[:, None] * AB[k]
        d = np.sqrt(((P - proj) ** 2).sum(1))
        m = d < best
        best = np.where(m, d, best)
        bests = np.where(m, cum[k] + tt * seglen[k], bests)
    return best, bests


_JUNC = None


def junctions():
    global _JUNC
    if _JUNC is not None:
        return _JUNC
    curves = L.road_curves()
    out = []
    for parent, child, turning in L.JUNCTIONS:
        pc = curves[parent]
        cc = curves[child]
        cx0, cy0, _, _ = cc.at(np.array([0.0]))
        d = np.hypot(pc.dense[:, 0] - cx0[0], pc.dense[:, 1] - cy0[0])
        sj = pc.s_dense[int(np.argmin(d))]
        cs = np.linspace(0, min(6.0, cc.length), 50)
        cxs, cys, _, _ = cc.at(cs)
        el, er = cc.edges(cs)
        turns = []
        if turning:
            jx, jy, _, _ = pc.at(np.array([sj]))
            ex, ey, _, _ = cc.at(np.array([min(6.5, cc.length)]))
            for sgn in (-1, 1):
                ax, ay, _, _ = pc.at(np.array([sj + sgn * 7.5]))
                tb = np.linspace(0, 1, 50)[:, None]
                P0 = np.array([ax[0], ay[0]])
                P1 = np.array([jx[0], jy[0]])
                P2 = np.array([ex[0], ey[0]])
                B = (1 - tb) ** 2 * P0 + 2 * (1 - tb) * tb * P1 + tb ** 2 * P2
                T_ = np.gradient(B, axis=0)
                T_ = T_ / (np.linalg.norm(T_, axis=1, keepdims=True) + 1e-12)
                N_ = np.stack([-T_[:, 1], T_[:, 0]], 1)
                g = cc.p["gauge"] or 0.72
                turns.append(dict(center=B, left=B + N_ * g, right=B - N_ * g))
        out.append(dict(parent=parent, child=child, cpts=np.stack([cxs, cys], 1), cs=cs,
                        Ec=0.5 * (el + er), turns=turns, center=np.array([cx0[0], cy0[0]])))
    _JUNC = out
    return out


def junction_flare(name, X, Y):
    """Flare factor J (0..1) on a parent road where a child road leaves it."""
    J = np.zeros(X.shape)
    for jd in junctions():
        if jd["parent"] != name:
            continue
        c = jd["center"]
        box = (np.abs(X - c[0]) < 9.0) & (np.abs(Y - c[1]) < 9.0)
        if not box.any():
            continue
        P = np.stack([X[box], Y[box]], 1)
        d, sc = _seg_dist(P, jd["cpts"])
        Ec = float(np.mean(jd["Ec"]))
        j = (1 - smoothstep(Ec * 0.45, Ec + 1.1, d)) * (1 - smoothstep(1.2, 4.2, sc))
        J[box] = np.maximum(J[box], j)
    return J


def junction_ruts(name, X, Y):
    """Extra rut depth (m) where carts turn between roads."""
    D = np.zeros(X.shape)
    for jd in junctions():
        if not jd["turns"] or name not in (jd["parent"], jd["child"]):
            continue
        c = jd["center"]
        box = (np.abs(X - c[0]) < 11.0) & (np.abs(Y - c[1]) < 11.0)
        if not box.any():
            continue
        P = np.stack([X[box], Y[box]], 1)
        acc = np.zeros(len(P))
        for tr in jd["turns"]:
            for key in ("left", "right"):
                d, sp = _seg_dist(P, tr[key])
                Ltot = np.sum(np.linalg.norm(np.diff(tr[key], axis=0), axis=1))
                fade = smoothstep(0.0, 2.5, sp) * smoothstep(0.0, 2.5, Ltot - sp)
                acc = np.maximum(acc, 0.045 * np.exp(-(d / 0.11) ** 4) * (0.35 + 0.65 * fade))
        D[box] = np.maximum(D[box], acc)
    return D


def flood(mask, seed):
    """Connected component of a boolean grid containing seed (4-neighbour)."""
    from collections import deque
    h, w = mask.shape
    out = np.zeros_like(mask, dtype=bool)
    if not mask[seed]:
        return out
    out[seed] = True
    dq = deque([seed])
    while dq:
        i, j = dq.popleft()
        for a, b in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)):
            if 0 <= a < h and 0 <= b < w and mask[a, b] and not out[a, b]:
                out[a, b] = True
                dq.append((a, b))
    return out


def build_road(name, col, materials, water_mat=None, rng_seed=0):
    rc = L.RoadCurve(name)
    p = rc.p
    W = p["width_total"]
    path = bool(p.get("path"))
    if path:
        U = lateral_columns(W, [(0.75, 0.025), (W, 0.05)])
        S = row_positions(rc, 0.03, 0.03, 1e9)
    else:
        e = p["edge"]
        U = lateral_columns(W, [(1.3, 0.03), (e + 0.2, 0.05), (W, 0.09)])
        S = row_positions(rc, 0.033, 0.12)
    nr, nc = len(S), len(U)
    cx, cy, tx, ty = rc.at(S)
    nx, ny = -ty, tx
    X = cx[:, None] + nx[:, None] * U[None, :]
    Y = cy[:, None] + ny[:, None] * U[None, :]
    H = L.height(X, Y)
    J = junction_flare(name, X, Y)
    R, at = road_profile(rc, S, U, J)
    TR = junction_ruts(name, X, Y)
    R = R - TR
    at["rut"] = np.maximum(at["rut"], TR / 0.06)
    rng = np.random.RandomState(p["seed"] + rng_seed)

    # hoof prints (horses walk the middle; a few everywhere)
    prints = []
    fine_rows = np.diff(S) < 0.05
    if p["hooves"] > 0:
        # only stamp where rows are fine (village part)
        fs = S[:-1][fine_rows]
        if len(fs):
            s0, s1 = fs.min(), fs.max()
            wv = rc.wander
            pr = make_prints(rng, s0, s1, 18.0 * p["hooves"], 0.0, 0.34, depth=(0.016, 0.034))
            pr += make_prints(rng, s0, s1, 2.5 * p["hooves"], 0.0, 1.25, depth=(0.01, 0.022))
            # convert u relative to wander-corrected centre
            prints = pr
    Z = R.copy()
    if prints:
        stamp_prints(Z, S, at["Uc"], prints, 0.033)

    # potholes (mostly in ruts) and puddles
    puddles = []
    if p["ruts"]:
        n_pot = int(rc.length / 11.0)
        for i in range(n_pot):
            s0 = rng.uniform(4.0, rc.length - 4.0)
            row = np.searchsorted(S, s0)
            if row >= nr - 2:
                continue
            fine = (S[min(row + 1, nr - 1)] - S[row]) < 0.05
            side = rng.choice([-1, 1])
            g = p["gauge"]
            kind = rng.uniform()
            if kind < 0.6:      # pothole in a wheel rut
                u0 = side * g * rng.uniform(0.85, 1.12)
                la = rng.uniform(0.3, 1.0)
                lb = rng.uniform(0.18, 0.36)
            elif kind < 0.85:   # hoof-churned hollow in the middle
                u0 = rng.uniform(-0.25, 0.25)
                la = rng.uniform(0.3, 0.7)
                lb = rng.uniform(0.25, 0.45)
            else:               # broad hollow across the track
                u0 = rng.uniform(-0.3, 0.3)
                la = rng.uniform(0.7, 1.4)
                lb = rng.uniform(0.8, 1.2)
            dep = rng.uniform(0.04, 0.08)
            i0 = np.searchsorted(S, s0 - la * 1.5)
            i1 = np.searchsorted(S, s0 + la * 1.5)
            uc = at["Uc"][i0:i1]
            dsx = (S[i0:i1, None] - s0) / la
            dux = (uc - u0) / lb
            rr = np.sqrt(dsx ** 2 + dux ** 2)
            ang = np.arctan2(dsx, dux)
            rr = rr * (1.0 + 0.22 * perlin(np.cos(ang) * 1.3 + i, np.sin(ang) * 1.3, p["seed"] + 90 + i))
            bowl = -dep * np.clip(1 - rr ** 2, 0, None) ** 1.2
            bowl += dep * 0.15 * perlin(dux * 2.0, dsx * 2.0, p["seed"] + 77 + i) * np.clip(1 - rr ** 2, 0, None)
            Z[i0:i1] += bowl
            puddles.append(dict(s0=s0, u0=u0, la=la, lb=lb, i0=i0, i1=i1, fine=fine))
        # also water in some deep rut stretches of wet zones
    Zw = H + Z
    # final vertex arrays
    verts = np.stack([X, Y, Zw], -1).reshape(-1, 3)
    idx = np.arange(nr * nc).reshape(nr, nc)
    a = idx[:-1, :-1].ravel()
    b = idx[:-1, 1:].ravel()
    c = idx[1:, 1:].ravel()
    d = idx[1:, :-1].ravel()
    # winding chosen so the normals point up (u runs to the left of the direction of travel)
    faces = np.stack([a, d, c, b], 1)
    # loop UVs: (Uc, S)
    UV = np.stack([at["Uc"], at["Sg"]], -1).reshape(-1, 2)
    loop_uv = UV[faces.ravel()]
    # wetness: rut bottoms in wet zones, plus around puddles
    wet = np.clip(at["rut"] * (0.35 + 0.65 * at["wet_zone"]), 0, 1)
    puddle_mask = np.zeros((nr, nc))
    water_meshes = []
    for k, pd in enumerate(puddles):
        i0, i1 = pd["i0"], pd["i1"]
        if i1 - i0 < 3:
            continue
        uc = at["Uc"][i0:i1]
        zz = Zw[i0:i1]
        core = (np.abs(uc - pd["u0"]) < pd["lb"] * 0.6) & (np.abs(S[i0:i1, None] - pd["s0"]) < pd["la"] * 0.6)
        if not core.any():
            continue
        zmin = zz[core].min()
        # level: fill part of the depression (rim height estimated around the core)
        ring = (np.abs(uc - pd["u0"]) < pd["lb"] * 1.3) & (np.abs(S[i0:i1, None] - pd["s0"]) < pd["la"] * 1.3) & ~core
        if not ring.any():
            continue
        zrim = np.percentile(zz[ring], 30)
        level = zmin + (zrim - zmin) * rng.uniform(0.45, 0.75)
        ci, cj = np.unravel_index(np.argmin(np.where(core, zz, 1e9)), zz.shape)
        comp = None
        for _ in range(10):
            comp = flood(zz < level, (ci, cj))
            touches = comp[0, :].any() or comp[-1, :].any() or comp[:, 0].any() or comp[:, -1].any()
            if not touches:
                break
            level = zmin + (level - zmin) * 0.7
        if comp is None or comp.sum() < 4 or touches:
            continue
        cell = comp[:-1, :-1] | comp[:-1, 1:] | comp[1:, :-1] | comp[1:, 1:]
        if cell.sum() < 4:
            continue
        ii, jj = np.where(cell)
        ii = ii + i0
        used = np.unique(np.concatenate([idx[ii, jj], idx[ii, jj + 1], idx[ii + 1, jj + 1], idx[ii + 1, jj]]))
        remap = -np.ones(nr * nc, dtype=np.int64)
        remap[used] = np.arange(len(used))
        wv = verts[used].copy()
        wv[:, 2] = level
        wf = np.stack([remap[idx[ii, jj]], remap[idx[ii + 1, jj]], remap[idx[ii + 1, jj + 1]], remap[idx[ii, jj + 1]]], 1)
        water_meshes.append((wv, wf))
        # wet halo
        halo = np.clip(1.0 - (zz - level) / 0.05, 0, 1)
        halo *= (np.abs(uc - pd["u0"]) < pd["lb"] * 2.2) & (np.abs(S[i0:i1, None] - pd["s0"]) < pd["la"] * 2.2)
        puddle_mask[i0:i1] = np.maximum(puddle_mask[i0:i1], halo)
    wet = np.maximum(wet, puddle_mask)
    # grass on the ribbon: centre strip and ragged edges
    gc = p.get("grass_center", 0.0)
    gmask = np.zeros((nr, nc))
    if p["ruts"]:
        center = np.exp(-(at["Uc"] / 0.3) ** 2) * gc
        gmask = center * smoothstep(-0.1, 0.5, fbm(at["Ug"] / 0.7, at["Sg"] / 2.5, 2, p["seed"] + 50))
    gmask = np.maximum(gmask, at["edgef"] ** 2 * 0.8 * smoothstep(-0.3, 0.4, fbm(at["Ug"] / 0.5, at["Sg"] / 1.2, 2, p["seed"] + 51)))
    gmask *= (1 - np.clip(wet * 1.5, 0, 1))
    gmask *= (1 - np.clip(at["rut"] * 3.0, 0, 1))
    pebm = (1 - 0.6 * np.clip(at["rut"], 0, 1)) * (1 - np.clip(wet, 0, 1)) * (1 - 0.6 * at["edgef"]) * smoothstep(-0.3, 0.4, fbm(at["Ug"] / 1.5, at["Sg"] / 3.0, 2, p["seed"] + 52))
    pattrs = {
        "rut": at["rut"].ravel(),
        "edgef": at["edgef"].ravel(),
        "wet": wet.ravel(),
        "gmask": gmask.ravel(),
        "hoof": at["hoofband"].ravel(),
        "pathf": np.full(nr * nc, 1.0 if path else 0.0),
        "pebm": pebm.ravel(),
    }
    me = mesh_from_arrays("road_" + name, verts, faces, loop_uv=loop_uv, point_attrs=pattrs, smooth=True, materials=materials)
    ob = C.new_object("road_" + name, me, col)
    wobs = []
    if water_meshes and water_mat is not None:
        allv = []
        allf = []
        off = 0
        for wv, wf in water_meshes:
            allv.append(wv)
            allf.append(wf + off)
            off += len(wv)
        wme = mesh_from_arrays("puddles_" + name, np.concatenate(allv), np.concatenate(allf), smooth=False, materials=[water_mat])
        wobs.append(C.new_object("puddles_" + name, wme, col))
    info = dict(rows=nr, cols=nc, verts=nr * nc, prints=len(prints), puddles=len(water_meshes), length=rc.length)
    return ob, wobs, info


# ----------------------------------------------------------------------------
# Yards (trampled dirt patches)
# ----------------------------------------------------------------------------
def yard_signed_dist(yd, X, Y):
    """Signed distance (m, + outside) to the noisy yard ellipse boundary, plus local coords."""
    c, s = math.cos(math.radians(yd["rot"])), math.sin(math.radians(yd["rot"]))
    lx = (X - yd["x"]) * c + (Y - yd["y"]) * s
    ly = -(X - yd["x"]) * s + (Y - yd["y"]) * c
    th = np.arctan2(ly / yd["ry"], lx / yd["rx"])
    rn = 1.0 + 0.16 * perlin(np.cos(th) * 1.5, np.sin(th) * 1.5, yd["seed"]) + 0.06 * perlin(np.cos(th) * 4, np.sin(th) * 4, yd["seed"] + 1)
    rho = np.sqrt((lx / yd["rx"]) ** 2 + (ly / yd["ry"]) ** 2) / rn
    rloc = np.sqrt((yd["rx"] * np.cos(th)) ** 2 + (yd["ry"] * np.sin(th)) ** 2) * rn
    return (rho - 1.0) * rloc, lx, ly


def build_yard(yd, col, materials, water_mat=None, arcs=None):
    rx, ry = yd["rx"] + 1.0, yd["ry"] + 1.0
    sp = 0.034
    lxs = np.arange(-rx, rx + 1e-6, sp)
    lys = np.arange(-ry, ry + 1e-6, sp)
    LX, LY = np.meshgrid(lxs, lys)
    c, s = math.cos(math.radians(yd["rot"])), math.sin(math.radians(yd["rot"]))
    X = yd["x"] + LX * c - LY * s
    Y = yd["y"] + LX * s + LY * c
    H = L.height(X, Y)
    t, _, _ = yard_signed_dist(yd, X, Y)
    sd = yd["seed"]
    bank_h = 0.05
    # roads entering the yard: no bank across their mouths
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
        d, _ = _seg_dist(np.stack([X[box], Y[box]], 1), poly)
        Er = rc.p["edge"]
        Jy[box] = np.maximum(Jy[box], 1 - smoothstep(Er * 0.5, Er + 0.9, d))
    z = -bank_h + 0.025 + 0.012 * np.clip(-t / 3.0, 0, 1)
    z = z + bank_h * smoothstep(-0.55, -0.05, t) * (1 - Jy)
    z = z - EDGE_DROP * smoothstep(-0.05, 0.6, t)
    inner = 1 - smoothstep(-0.6, -0.15, t)
    z = z + (0.008 * fbm(X / 0.16, Y / 0.16, 3, sd + 3) + 0.014 * fbm(X / 1.1, Y / 1.1, 2, sd + 4)) * (0.35 + 0.65 * inner)
    rng = np.random.RandomState(sd)
    rut = np.zeros_like(z)
    if arcs:
        for (ax, ay, R, depth) in arcs:
            dd = np.sqrt((X - ax) ** 2 + (Y - ay) ** 2)
            for off in (-0.74, 0.74):
                du = dd - (R + off)
                rr = np.exp(-(du / 0.1) ** 4)
                rut = np.maximum(rut, rr * depth / 0.06)
                z = z - depth * rr * inner
    # hoof prints all over (stable yard)
    if yd.get("hooves", 0) > 0:
        area = (2 * yd["rx"]) * (2 * yd["ry"])
        n = int(area * 7 * yd["hooves"])
        nr, nc = LX.shape
        for _ in range(n):
            px = rng.uniform(-yd["rx"], yd["rx"])
            py = rng.uniform(-yd["ry"], yd["ry"])
            j = int((px + rx) / sp)
            i = int((py + ry) / sp)
            i0, i1 = max(i - 5, 0), min(i + 6, nr)
            j0, j1 = max(j - 5, 0), min(j + 6, nc)
            ang = rng.uniform(0, 2 * math.pi)
            a, b = rng.uniform(0.055, 0.068), rng.uniform(0.062, 0.078)
            dx = LX[i0:i1, j0:j1] - px
            dy = LY[i0:i1, j0:j1] - py
            ca, sa = math.cos(ang), math.sin(ang)
            xx = (dx * ca - dy * sa) / a
            yy = (dx * sa + dy * ca) / b
            rr = np.sqrt(xx * xx + yy * yy)
            dep = rng.uniform(0.012, 0.028)
            z[i0:i1, j0:j1] += (-dep * np.clip(1 - rr ** 2, 0, None) ** 1.5 * (1 + 0.35 * np.clip(yy, -1, 1)) + 0.3 * dep * np.exp(-((rr - 1.15) / 0.22) ** 2)) * inner[i0:i1, j0:j1]
    # a couple of muddy hollows
    wet = np.zeros_like(z)
    water = []
    nh = 3 if yd.get("hooves", 0) > 0 else 0
    for k in range(nh):
        hx = rng.uniform(-yd["rx"] * 0.6, yd["rx"] * 0.6)
        hy = rng.uniform(-yd["ry"] * 0.6, yd["ry"] * 0.5)
        la, lb = rng.uniform(0.5, 1.1), rng.uniform(0.35, 0.7)
        dep = rng.uniform(0.035, 0.06)
        rr = np.sqrt(((LX - hx) / la) ** 2 + ((LY - hy) / lb) ** 2)
        z = z - dep * np.clip(1 - rr ** 2, 0, None) ** 1.2
        Zt = H + z
        core = rr < 0.5
        ring = (rr > 1.0) & (rr < 1.4)
        zmin = Zt[core].min()
        zrim = np.percentile(Zt[ring], 30)
        level = zmin + (zrim - zmin) * 0.55
        ci, cj = np.unravel_index(np.argmin(np.where(core, Zt, 1e9)), Zt.shape)
        comp = flood((Zt < level) & (rr < 2.5), (ci, cj))
        for _ in range(8):
            if not (comp & (rr > 2.3)).any():
                break
            level = zmin + (level - zmin) * 0.7
            comp = flood((Zt < level) & (rr < 2.5), (ci, cj))
        cell = comp[:-1, :-1] | comp[:-1, 1:] | comp[1:, :-1] | comp[1:, 1:]
        water.append((level, cell))
        wet = np.maximum(wet, np.clip(1 - (rr - 1.0) / 0.8, 0, 1))
    Z = H + z
    nr, nc = LX.shape
    # drop cells far outside (hidden under terrain)
    keep_v = t < 0.75
    idx = np.arange(nr * nc).reshape(nr, nc)
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
    gm = edgef ** 2 * 0.8 * smoothstep(-0.3, 0.4, fbm(X / 0.5, Y / 0.5, 2, sd + 51))
    gm *= (1 - np.clip(wet * 1.5, 0, 1))
    pattrs = {
        "rut": (rut.ravel()[used]).clip(0, 1),
        "edgef": edgef.ravel()[used],
        "wet": np.maximum(wet, rut * 0.5).ravel()[used],
        "gmask": gm.ravel()[used],
        "hoof": np.full(len(used), 0.6 if yd.get("hooves", 0) > 0 else 0.0),
        "pathf": np.full(len(used), 0.0 if yd.get("hooves", 0) > 0 else 1.0),
        "pebm": ((1 - np.clip(wet, 0, 1)) * (1 - 0.6 * edgef)).ravel()[used],
    }
    name = "yard_%d" % yd["seed"]
    me = mesh_from_arrays(name, verts, faces, loop_uv=loop_uv, point_attrs=pattrs, smooth=True, materials=materials)
    ob = C.new_object(name, me, col)
    wobs = []
    if water and water_mat is not None:
        allv, allf, off = [], [], 0
        for level, cell in water:
            ii, jj = np.where(cell)
            if len(ii) < 4:
                continue
            usedw = np.unique(np.concatenate([idx[ii, jj], idx[ii, jj + 1], idx[ii + 1, jj + 1], idx[ii + 1, jj]]))
            rm = -np.ones(nr * nc, dtype=np.int64)
            rm[usedw] = np.arange(len(usedw))
            wv = np.stack([X, Y, Z], -1).reshape(-1, 3)[usedw].copy()
            wv[:, 2] = level
            wf = np.stack([rm[idx[ii, jj]], rm[idx[ii, jj + 1]], rm[idx[ii + 1, jj + 1]], rm[idx[ii + 1, jj]]], 1)
            allv.append(wv)
            allf.append(wf + off)
            off += len(wv)
        if allv:
            wme = mesh_from_arrays(name + "_water", np.concatenate(allv), np.concatenate(allf), materials=[water_mat])
            wobs.append(C.new_object(name + "_water", wme, col))
    return ob, wobs


# ----------------------------------------------------------------------------
# Terrain
# ----------------------------------------------------------------------------
def road_kdtree(curves):
    pts = []
    meta = []
    for ri, (name, rc) in enumerate(curves.items()):
        ss = np.arange(0, rc.length, 0.2)
        x, y, tx, ty = rc.at(ss)
        for k in range(len(ss)):
            pts.append((x[k], y[k], 0.0))
            meta.append((name, ss[k], tx[k], ty[k]))
    kd = kdtree.KDTree(len(pts))
    for i, p in enumerate(pts):
        kd.insert(p, i)
    kd.balance()
    return kd, meta


def graded_axis(lo, hi, f0, f1, fine, coarse, grade=12.0):
    """Coordinates from lo to hi: spacing `fine` inside [f0, f1], growing to `coarse` over `grade` metres outside."""
    def sp(x):
        d = max(f0 - x, x - f1, 0.0)
        t = min(d / grade, 1.0)
        return fine + (coarse - fine) * t
    # walk outwards from f0 and f1
    xs = [f0]
    x = f0
    while x < f1 - 1e-9:
        x = min(x + fine, f1)
        xs.append(x)
    x = f1
    while x < hi - 1e-9:
        x = min(x + sp(x), hi)
        xs.append(x)
    left = []
    x = f0
    while x > lo + 1e-9:
        x = max(x - sp(x), lo)
        left.append(x)
    return np.array(left[::-1] + xs)


def build_terrain(col, materials, size=360.0, spacing=0.45):
    curves = L.road_curves()
    xs = graded_axis(-size / 2, size / 2, -64.0, 64.0, 0.22, 0.8)
    ys = graded_axis(-size / 2, size / 2, -58.0, 70.0, 0.22, 0.8)
    X, Y = np.meshgrid(xs, ys)
    ny_, nx_ = X.shape
    H = L.height(X, Y)
    fx = X.ravel()
    fy = Y.ravel()
    N = len(fx)
    lower = np.zeros(N)
    edge_t = np.full(N, 99.0)    # signed distance to nearest road edge (m, + outside)
    for name, rc in curves.items():
        ss = np.arange(0, rc.length + 0.1, 0.1)
        cx, cy, tx, ty = rc.at(ss)
        kd = kdtree.KDTree(len(ss))
        for k in range(len(ss)):
            kd.insert((cx[k], cy[k], 0.0), k)
        kd.balance()
        W = rc.p["width_total"] + 1.0
        bb = (fx > cx.min() - W) & (fx < cx.max() + W) & (fy > cy.min() - W) & (fy < cy.max() + W)
        cand = np.where(bb)[0]
        near_idx = np.empty(len(cand), dtype=np.int64)
        near_d = np.empty(len(cand))
        find = kd.find
        for m_, i in enumerate(cand):
            co, k, dist = find((fx[i], fy[i], 0.0))
            near_idx[m_] = k
            near_d[m_] = dist
        sel = near_d < W
        cand = cand[sel]
        k = near_idx[sel]
        s = ss[k]
        lat = (fx[cand] - cx[k]) * (-ty[k]) + (fy[cand] - cy[k]) * tx[k]
        # ignore points beyond the ends of the centre line
        along = (fx[cand] - cx[k]) * tx[k] + (fy[cand] - cy[k]) * ty[k]
        endok = ~(((k == 0) & (along < -0.05)) | ((k == len(ss) - 1) & (along > 0.05)))
        el, er = rc.edges(s)
        E = np.where(lat >= 0, el, er)
        if rc.p.get("path"):
            E = E * (0.25 + 0.75 * smoothstep(0.0, 1.4, rc.length - s))
        t = np.abs(lat) - E
        t = np.where(endok, t, 99.0)
        lw = LOWER * (1 - smoothstep(-0.25, 0.05, t))
        lower[cand] = np.maximum(lower[cand], lw)
        edge_t[cand] = np.minimum(edge_t[cand], t)
    # yards
    for yd in L.YARDS:
        t, _, _ = yard_signed_dist(yd, fx, fy)
        lw = LOWER * (1 - smoothstep(-0.25, 0.05, t))
        lower = np.maximum(lower, lw)
        edge_t = np.minimum(edge_t, t)
    Z = H.ravel() - lower
    verts = np.stack([fx, fy, Z], 1)
    idx = np.arange(nx_ * ny_).reshape(ny_, nx_)
    faces = np.stack([idx[:-1, :-1].ravel(), idx[:-1, 1:].ravel(), idx[1:, 1:].ravel(), idx[1:, :-1].ravel()], 1)
    forest = L.forest_mask(fx, fy)
    # building footprints
    built = np.zeros(N)
    for bname, b in list(L.BUILDINGS.items()) + [("garden%d" % i, g) for i, g in enumerate(L.GARDENS)]:
        c, s = math.cos(math.radians(b["rot"])), math.sin(math.radians(b["rot"]))
        lx = (fx - b["x"]) * c + (fy - b["y"]) * s
        ly = -(fx - b["x"]) * s + (fy - b["y"]) * c
        inside = (np.abs(lx) < b["w"] / 2 + 0.15) & (np.abs(ly) < b["d"] / 2 + 0.15)
        built = np.maximum(built, inside.astype(float))
    roadedge = 1 - smoothstep(0.0, 0.7 + 0.6 * (0.5 + 0.5 * fbm(fx / 2.0, fy / 2.0, 2, 71)), edge_t)
    grass = (1 - forest * 0.85) * smoothstep(-0.05, 0.55, edge_t) * (1 - built)
    meadow_var = smoothstep(-0.6, 0.6, fbm(fx / 9.0, fy / 9.0, 3, 61))
    pattrs = {
        "forest": forest,
        "roadedge": roadedge,
        "grass": grass,
        "built": built,
        "mvar": meadow_var,
        "edge_t": np.clip(edge_t, -5, 50),
    }
    loop_uv = np.stack([fx, fy], 1)[faces.ravel()]
    me = mesh_from_arrays("terrain", verts, faces, loop_uv=loop_uv, point_attrs=pattrs, smooth=True, materials=materials)
    ob = C.new_object("terrain", me, col)
    return ob


# ----------------------------------------------------------------------------
# Ground queries (after build)
# ----------------------------------------------------------------------------
_BVH = {}


def ground_bvh(names=None):
    names = names or [o.name for o in bpy.data.objects if o.name.startswith(("terrain", "road_", "yard_")) and o.type == 'MESH']
    key = tuple(sorted(names))
    if key in _BVH:
        return _BVH[key]
    trees = []
    for nm in names:
        ob = bpy.data.objects[nm]
        me = ob.data
        nv = len(me.vertices)
        co = np.zeros(nv * 3)
        me.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        M = np.array(ob.matrix_world)
        co = co @ M[:3, :3].T + M[:3, 3]
        nl = len(me.loops)
        lv = np.zeros(nl, dtype=np.int64)
        me.loops.foreach_get("vertex_index", lv)
        tot = np.zeros(len(me.polygons), dtype=np.int64)
        me.polygons.foreach_get("loop_total", tot)
        if np.all(tot == 4):
            polys = lv.reshape(-1, 4).tolist()
        else:
            st = np.zeros(len(me.polygons), dtype=np.int64)
            me.polygons.foreach_get("loop_start", st)
            polys = [lv[s:s + n].tolist() for s, n in zip(st, tot)]
        trees.append(BVHTree.FromPolygons(co.tolist(), polys))
    _BVH.clear()
    _BVH[key] = trees
    return trees


def ground_z(x, y, trees=None):
    trees = trees or ground_bvh()
    best = None
    for t in trees:
        hit = t.ray_cast(Vector((x, y, 500.0)), Vector((0, 0, -1)))
        if hit[0] is not None:
            z = hit[0].z
            if best is None or z > best:
                best = z
    if best is None:
        best = float(L.height(x, y))
    return best
