"""Placing the props around the village."""
import bpy
import numpy as np
import math
from mathutils import Vector, Euler
import common as C
import layout as L
import terrain as T
import props as PR
import plants as PL
from bparts import Parts, Strands, straw_colour

BEVEL = {"timber": 0.008, "plank": 0.004, "plank_dark": 0.004, "fresh": 0.003}


def bworld(bname, lx, ly):
    b = L.BUILDINGS[bname]
    c, s = math.cos(math.radians(b["rot"])), math.sin(math.radians(b["rot"]))
    return b["x"] + lx * c - ly * s, b["y"] + lx * s + ly * c, b["rot"]


class Placer:
    def __init__(self, col, mats):
        self.col = col
        self.mats = mats
        self.trees = T.ground_bvh()
        self.count = 0

    def gz(self, x, y):
        return T.ground_z(x, y, self.trees)

    def place(self, name, builder, x, y, rot=0.0, sink=0.0, z=None, tilt=None, seed=None, strands=False, zmode="center", foot=0.3):
        P = Parts(seed=seed if seed is not None else (abs(hash(name)) % 10000))
        st = Strands() if strands else None
        if strands:
            builder(P, st)
        else:
            builder(P)
        if tilt is not None:
            Rm = np.array(Euler(tilt).to_matrix())
            P.deform(list(P.mb.keys()), lambda v: v @ Rm.T)
        if z is None:
            if zmode == "min":
                zs = [self.gz(x + dx, y + dy) for dx, dy in ((0, 0), (foot, 0), (-foot, 0), (0, foot), (0, -foot))]
                z = min(zs)
            else:
                z = self.gz(x, y)
        parent = bpy.data.objects.new(name, None)
        self.col.objects.link(parent)
        parent.location = (x, y, z - sink)
        parent.rotation_euler = (0, 0, math.radians(rot))
        P.build(name, self.col, self.mats, bevel=BEVEL, parent=parent)
        if st is not None:
            st.build(name + "_strands", self.col, self.mats["strands"], parent=parent)
        self.count += 1
        return parent

    def place_world(self, name, builder, strands=False, seed=None):
        """Builder works directly in world coordinates (fences that follow the ground)."""
        P = Parts(seed=seed if seed is not None else (abs(hash(name)) % 10000))
        st = Strands() if strands else None
        if strands:
            builder(P, st)
        else:
            builder(P)
        parent = bpy.data.objects.new(name, None)
        self.col.objects.link(parent)
        P.build(name, self.col, self.mats, bevel=BEVEL, parent=parent)
        if st is not None:
            st.build(name + "_strands", self.col, self.mats["strands"], parent=parent)
        self.count += 1
        return parent


def garden_patch(pl, g, rng):
    """Tilled rows with cabbages and leeks inside a wattle fence."""
    c, s = math.cos(math.radians(g["rot"])), math.sin(math.radians(g["rot"]))
    w, d = g["w"], g["d"]
    nx, ny = int(w / 0.06) + 1, int(d / 0.06) + 1
    lx = np.linspace(-w / 2, w / 2, nx)
    ly = np.linspace(-d / 2, d / 2, ny)
    LX, LY = np.meshgrid(lx, ly, indexing='ij')
    X = g["x"] + LX * c - LY * s
    Y = g["y"] + LX * s + LY * c
    rows = 0.06 * np.maximum(np.cos(LY / 0.55 * 2 * math.pi), -0.2) + 0.01 * C.fbm(X / 0.2, Y / 0.2, 2, g["seed"])
    edge = np.minimum(np.minimum(LX + w / 2, w / 2 - LX), np.minimum(LY + d / 2, d / 2 - LY))
    rows = rows * C.smoothstep(0.0, 0.25, edge) + 0.035 * C.smoothstep(0.0, 0.15, edge) - 0.04
    Z = L.height(X, Y) + rows
    verts = np.stack([X, Y, Z], -1).reshape(-1, 3)
    idx = np.arange(nx * ny).reshape(nx, ny)
    faces = np.stack([idx[:-1, :-1].ravel(), idx[1:, :-1].ravel(), idx[1:, 1:].ravel(), idx[:-1, 1:].ravel()], 1)
    me = C.mesh_from_arrays("garden_soil_%d" % g["seed"], verts, faces, smooth=True, materials=[pl.mats["soil"]])
    ob = bpy.data.objects.new(me.name, me)
    pl.col.objects.link(ob)
    # plants on the ridges
    cab = PL.Geo()
    nrow = int(d / 0.55)
    for r in range(nrow):
        yy = -d / 2 + 0.28 + r * 0.55
        if yy > d / 2 - 0.2:
            break
        kind = 'cabbage' if r % 3 != 2 else 'leek'
        step = 0.5 if kind == 'cabbage' else 0.22
        xx = -w / 2 + 0.3
        while xx < w / 2 - 0.25:
            if rng.uniform() < 0.88:
                gx = g["x"] + xx * c - yy * s
                gy = g["y"] + xx * s + yy * c
                gz = float(L.height(gx, gy)) + 0.06 - 0.04 + 0.01
                geo = PR.cabbage_geo(rng) if kind == 'cabbage' else PR.leek_geo(rng)
                v, f, col, mi = geo.arrays()
                sc = rng.uniform(0.75, 1.15)
                ang = rng.uniform(0, 2 * math.pi)
                Rm = np.array(Euler((0, 0, ang)).to_matrix())
                v = (v * sc) @ Rm.T + np.array([gx, gy, gz])
                cab.add(v, f, [c_[:3] for c_ in col])
            xx += step * rng.uniform(0.9, 1.1)
    v, f, col, mi = cab.arrays()
    me = C.mesh_from_arrays("garden_plants_%d" % g["seed"], v, f, point_attrs={"col": col}, materials=[pl.mats["herb_mat"]])
    ob2 = bpy.data.objects.new(me.name, me)
    pl.col.objects.link(ob2)
    # wattle fence round it, with an opening on the near side
    corners = [(-w / 2 - 0.3, -d / 2 - 0.3), (w / 2 + 0.3, -d / 2 - 0.3), (w / 2 + 0.3, d / 2 + 0.3), (-w / 2 - 0.3, d / 2 + 0.3), (-w / 2 - 0.3, -d / 2 - 0.3)]
    wc = [(g["x"] + px * c - py * s, g["y"] + px * s + py * c) for px, py in corners]
    # leave a gap in the first side
    a, b = np.array(wc[0]), np.array(wc[1])
    gap0 = a + (b - a) * 0.55
    gap1 = a + (b - a) * 0.72
    segs = [[tuple(gap1), wc[1], wc[2], wc[3], wc[4], tuple(gap0)]]
    for k, sg in enumerate(segs):
        pl.place_world("wattle_garden_%d_%d" % (g["seed"], k), lambda P, sg=sg: PR.wattle_fence(P, sg, h=0.85, ground=lambda x, y: pl.gz(x, y)))


def build_props(col, mats):
    rng = np.random.RandomState(4242)
    pl = Placer(col, mats)
    out = {}
    # ---------------- stable yard and paddock ----------------
    sx, sy, srot = bworld("stable", 0, 0)
    tx, ty, _ = bworld("stable", -6.3, -3.9)
    pl.place("trough", lambda P: PR.trough(P, 2.0), tx, ty, srot + 0, zmode="min", foot=0.9)
    bx_, by_, _ = bworld("stable", -5.3, -4.35)
    pl.place("bucket_trough", lambda P: PR.bucket(P), bx_, by_, srot + 30)
    hx, hy, _ = bworld("stable", -2.1, -5.6)
    pl.place("hitching_rail", lambda P: PR.hitching_rail(P, 2.6), hx, hy, srot, zmode="min", foot=1.2)
    pl.place("cart", lambda P: PR.cart(P), 13.6, 25.0, -55.0, sink=0.02)
    mx, my, _ = bworld("stable", -6.6, 1.6)
    pl.place("manure_heap", lambda P: PR.manure_heap(P, 1.3, 0.75), mx, my, srot + 20, sink=0.15)
    lx_, ly_, _ = bworld("stable", 6.9, 0.3)
    pl.place("ladder", lambda P: PR.ladder(P, 4.6), lx_, ly_, srot + 90, tilt=(math.radians(-17), 0, 0))
    fx_, fy_, _ = bworld("stable", -2.75, -3.62)
    pl.place("pitchfork", pitchfork, fx_, fy_, srot + 10, tilt=(math.radians(-14), math.radians(4), 0))
    bx2, by2, _ = bworld("stable", 1.2, -3.7)
    pl.place("bucket_stable", lambda P: PR.bucket(P), bx2, by2, srot)
    # paddock fence with an open gap facing the yard
    pts = [(15.5, 27.0), (15.5, 42.5), (32.5, 42.5), (32.5, 23.5), (19.5, 23.5)]
    pl.place_world("paddock_fence", lambda P: PR.split_rail_fence(P, pts, ground=lambda x, y: pl.gz(x, y), broken=0.12))
    pl.place("haystack_1", lambda P, st: PR.haystack(P, st, H=3.3, R=1.75, lean=0.04), 20.0, 38.6, 30.0, strands=True, sink=0.05)
    pl.place("haystack_2", lambda P, st: PR.haystack(P, st, H=2.7, R=1.5, lean=-0.06), 25.4, 39.8, 75.0, strands=True, sink=0.05)
    pl.place("haystack_3", lambda P, st: PR.haystack(P, st, H=2.2, R=1.4, lean=0.08), 29.3, 37.2, 160.0, strands=True, sink=0.05)
    # ---------------- cottage A ----------------
    x, y, r = bworld("cottage_a", -1.0, -3.2)
    pl.place("bench_a", lambda P: PR.bench(P, 1.5), x, y, r, zmode="min")
    x, y, r = bworld("cottage_a", -4.75, -3.05)
    pl.place("butt_a", lambda P: PR.barrel(P, h=0.95, r=0.34), x, y, r)
    x, y, r = bworld("cottage_a", 5.0, 0.0)
    pl.place("woodpile_a", lambda P: PR.woodpile(P, 3.6, 1.25), x, y, r + 90, zmode="min", foot=1.0)
    x, y, r = bworld("cottage_a", -6.0, 5.2)
    pl.place("chopping_a", lambda P: PR.chopping_block(P), x, y, r + 40)
    x, y, r = bworld("cottage_a", 1.35, -3.05)
    pl.place("pots_a", lambda P: (PR.clay_pot(P, (0, 0, 0), 0.42, 0.18), PR.clay_pot(P, (0.32, 0.12, 0), 0.3, 0.13)), x, y, r)
    x, y, r = bworld("cottage_a", 3.9, 6.5)
    pl.place("skeps_a", skep_bench, x, y, r + 180, zmode="min")
    # ---------------- cottage C (trader: barrels, crates, sacks) ----------------
    x, y, r = bworld("cottage_c", 2.9, -3.15)
    pl.place("barrels_c", lambda P: (PR.barrel(P, (0, 0, 0)), PR.barrel(P, (0.66, 0.05, 0)), PR.barrel(P, (0.33, -0.55, 0), h=0.8, r=0.28)), x, y, r, zmode="min", foot=0.6)
    x, y, r = bworld("cottage_c", -2.6, -3.35)
    pl.place("crates_c", lambda P: (PR.crate(P, (0, 0, 0), (0.75, 0.55, 0.5)), PR.crate(P, (0.05, 0.02, 0.52), (0.6, 0.45, 0.4), rot=0.15), PR.crate(P, (0.85, -0.1, 0), (0.6, 0.5, 0.45), rot=-0.2)), x, y, r, zmode="min", foot=0.5)
    x, y, r = bworld("cottage_c", 1.6, -3.3)
    pl.place("sacks_c", lambda P: (PR.sack(P, (0, 0, 0)), PR.sack(P, (0.42, 0.1, 0), h=0.6), PR.sack(P, (0.2, -0.38, 0), h=0.5, slump=0.6)), x, y, r, zmode="min")
    x, y, r = bworld("cottage_c", -4.1, -2.95)
    pl.place("wheel_lean_c", lambda P: PR.wheel(P, (0, 0, 0.66), (0, 1, 0), radius=0.66), x, y, r, tilt=(math.radians(-12), 0, 0))
    x, y, r = bworld("cottage_c", 4.7, 1.2)
    pl.place("grindstone_c", lambda P: PR.grindstone(P), x, y, r + 90)
    # ---------------- cottage B ----------------
    x, y, r = bworld("cottage_b", 1.5, -2.95)
    pl.place("bench_b", lambda P: PR.bench(P, 1.3), x, y, r, zmode="min")
    x, y, r = bworld("cottage_b", -3.75, -2.6)
    pl.place("butt_b", lambda P: PR.barrel(P, h=0.85, r=0.3), x, y, r)
    x, y, r = bworld("cottage_b", 4.3, 0.2)
    pl.place("woodpile_b", lambda P: PR.woodpile(P, 2.6, 1.0), x, y, r + 90, zmode="min", foot=0.8)
    x, y, r = bworld("cottage_b", 5.0, -2.4)
    pl.place("chopping_b", lambda P: PR.chopping_block(P, axe=False), x, y, r)
    # ---------------- cottage D ----------------
    x, y, r = bworld("cottage_d", -1.6, -2.5)
    pl.place("pots_d", lambda P: (PR.clay_pot(P, (0, 0, 0), 0.36, 0.15), PR.bucket(P, (0.4, 0.05, 0))), x, y, r)
    x, y, r = bworld("cottage_d", -3.3, 1.5)
    pl.place("skeps_d", skep_bench, x, y, r + 90, zmode="min")
    # ---------------- village green, roadside ----------------
    pl.place("well", lambda P: PR.well(P), -6.8, 7.8, 15.0, zmode="min", foot=0.8)
    pl.place("signpost", lambda P: PR.signpost(P, arms=((20.0, "E"), (200.0, "W"), (280.0, "S"))), -17.2, -9.6, 0.0)
    pl.place("broken_wheel", lambda P: PR.wheel(P, (0, 0, 0.07), (0, 0, 1), radius=0.6), -41.0, -8.0, 30.0, tilt=(0.05, 0.08, 0))
    pts = [(-52.0, -11.0), (-46.0, -9.2), (-40.5, -7.6), (-35.5, -6.1)]
    pl.place_world("roadside_fence", lambda P: PR.split_rail_fence(P, pts, ground=lambda x, y: pl.gz(x, y), broken=0.2))
    pts = [(8.0, -6.8), (14.0, -5.6), (20.0, -4.6)]
    pl.place_world("roadside_fence2", lambda P: PR.split_rail_fence(P, pts, ground=lambda x, y: pl.gz(x, y), broken=0.25))
    # stone pile and a couple of hurdles by the road
    pl.place("stone_pile", stone_pile, 13.0, -8.4, 0.0, sink=0.05)
    # ---------------- gardens ----------------
    for g in L.GARDENS:
        garden_patch(pl, g, rng)
    out["props"] = pl.count
    return out


def pitchfork(P):
    P.cyl("fresh", (0, 0, 0.25), (0, 0, 1.75), 0.018, sides=6)
    for k in (-1, 0, 1):
        pts = [(k * 0.04, 0, 0.27), (k * 0.055, 0.0, 0.15), (k * 0.06, 0.02, 0.0)]
        P.tube("iron", pts, [0.006, 0.005, 0.003], sides=4)
    P.beam("iron", (-0.05, 0, 0.27), (0.05, 0, 0.27), 0.015, 0.02)


def skep_bench(P):
    P.box("plank", (0, 0, 0.45), (1.4, 0.45, 0.05))
    for sx in (-1, 1):
        P.box("timber", (sx * 0.6, 0, 0.21), (0.08, 0.35, 0.42))
    for k, xx in enumerate((-0.45, 0.0, 0.45)):
        PR.skep(P, (xx, 0, 0.475), h=0.42 + 0.03 * k, r=0.22)


def stone_pile(P):
    import plants as PL_
    rng = P.rng
    for k in range(26):
        v, f = PL_.rock(rng, rng.uniform(0.1, 0.22), flat=rng.uniform(0.5, 0.8), sub=2)
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(0, 0.7) * (1 - k / 40)
        z = 0.08 + (0.3 * (1 - r / 0.7) if k > 10 else 0.0)
        v = v + np.array([r * math.cos(a), r * math.sin(a), z])
        P.add("stone", v, f, None)
