"""Mediaeval props: barrels, crates, sacks, cart, well, haystacks, fences, woodpile, bench, skeps, garden, etc.
Every builder fills a Parts container in local coordinates (z=0 is the ground)."""
import bpy
import numpy as np
import math
from mathutils import Vector, Matrix, Euler, Quaternion
import common as C
from bparts import Parts, Wall, stone_wall, stone_lib, Strands, straw_colour, shingle_plane
import plants as PL


# ----------------------------------------------------------------------------
# containers
# ----------------------------------------------------------------------------
def barrel(P, base=(0, 0, 0), h=0.9, r=0.3, staves=18, bulge=0.16, hoops=(0.08, 0.3, 0.7, 0.92), key="plank", lid=True, tilt=None):
    rng = P.rng
    bx, by, bz = base
    nz = 8
    zs = np.linspace(0, h, nz + 1)
    rad = lambda z: r * (1 - bulge * (2 * z / h - 1) ** 2)
    gap = 0.012
    th = 0.022
    for k in range(staves):
        a0 = 2 * math.pi * k / staves + gap / r * 0.5
        a1 = 2 * math.pi * (k + 1) / staves - gap / r * 0.5
        top_off = rng.uniform(-0.006, 0.006)
        verts = []
        for z in zs:
            zz = z + (top_off if z == h else 0.0)
            ro = rad(z)
            ri = ro - th
            for a in (a0, a1):
                verts.append((bx + ro * math.cos(a), by + ro * math.sin(a), bz + zz))
            for a in (a0, a1):
                verts.append((bx + ri * math.cos(a), by + ri * math.sin(a), bz + zz))
        faces = []
        uvs = []
        sw = (a1 - a0) * r
        for j in range(nz):
            o = j * 4
            n = (j + 1) * 4
            faces.append([o + 0, o + 1, n + 1, n + 0])
            uvs.append([(zs[j], 0), (zs[j], sw), (zs[j + 1], sw), (zs[j + 1], 0)])
            faces.append([o + 3, o + 2, n + 2, n + 3])
            uvs.append([(zs[j], 0), (zs[j], sw), (zs[j + 1], sw), (zs[j + 1], 0)])
            faces.append([o + 2, o + 0, n + 0, n + 2])
            uvs.append([(zs[j], 0), (zs[j], 0.02), (zs[j + 1], 0.02), (zs[j + 1], 0)])
            faces.append([o + 1, o + 3, n + 3, n + 1])
            uvs.append([(zs[j], 0), (zs[j], 0.02), (zs[j + 1], 0.02), (zs[j + 1], 0)])
        top = nz * 4
        faces.append([top + 0, top + 1, top + 3, top + 2])
        uvs.append([(0, 0), (0.02, 0), (0.02, 0.02), (0, 0.02)])
        faces.append([2, 3, 1, 0])
        uvs.append([(0, 0), (0.02, 0), (0.02, 0.02), (0, 0.02)])
        P.add(key, np.array(verts), faces, uvs, rnd=rng.uniform())
    for hz in hoops:
        z = hz * h
        rr = rad(z) + 0.004
        pts = []
        for i in range(25):
            a = 2 * math.pi * i / 24
            pts.append((bx + rr * math.cos(a), by + rr * math.sin(a), bz + z))
        # flat band: thin tube with a tall cross-section via two stacked tubes
        P.tube("iron", pts, [0.006] * len(pts), sides=4)
        pts2 = [(p[0], p[1], p[2] + 0.02) for p in pts]
        P.tube("iron", pts2, [0.006] * len(pts2), sides=4)
    if lid:
        P.cyl(key, (bx, by, bz + h - 0.03), (bx, by, bz + h - 0.01), rad(h) - th - 0.002, sides=staves)


def crate(P, base=(0, 0, 0), size=(0.7, 0.5, 0.5), rot=0.0, key="plank", lid=True):
    rng = P.rng
    sx, sy, sz = size
    R = Euler((0, 0, rot)).to_matrix()
    o = Vector(base)

    def bx(c, s):
        P.box(key, o + R @ Vector(c), s, R, jitter=0.004)
    nb = 3
    bh = sz / nb
    for i in range(nb):
        zc = (i + 0.5) * bh
        for sgn in (-1, 1):
            bx((0, sgn * (sy / 2 - 0.01), zc), (sx - 0.02, 0.02, bh - 0.008))
            bx((sgn * (sx / 2 - 0.01), 0, zc), (0.02, sy - 0.04, bh - 0.008))
    for sx_ in (-1, 1):
        for sy_ in (-1, 1):
            bx((sx_ * (sx / 2 - 0.035), sy_ * (sy / 2 + 0.005), sz / 2), (0.05, 0.02, sz))
    bx((0, 0, 0.01), (sx - 0.03, sy - 0.03, 0.02))
    if lid:
        for k in range(4):
            yy = -sy / 2 + (k + 0.5) * sy / 4
            bx((0, yy, sz + 0.01), (sx + 0.01, sy / 4 - 0.008, 0.02))


def sack(P, base=(0, 0, 0), h=0.65, r=0.24, slump=0.3, tied=True, key="burlap"):
    rng = P.rng
    bx, by, bz = base
    nz, na = 12, 18
    seed = rng.randint(1000)
    verts = []
    for i in range(nz + 1):
        t = i / nz
        z = h * t
        # bulging bottom, narrowing neck
        prof = r * (1.0 + slump * (1 - t) ** 2) * (math.sin(math.pi * min(t * 1.15, 1.0)) ** 0.35)
        if t > 0.85:
            prof = r * 0.28 * (1 - (t - 0.85) * 2.5)
        for j in range(na):
            a = 2 * math.pi * j / na
            n = C.fbm(math.cos(a) * 1.3 + t * 2, math.sin(a) * 1.3 + seed, 2, seed)
            rr = max(prof * (1 + 0.12 * float(n)), 0.01)
            verts.append((bx + rr * math.cos(a), by + rr * math.sin(a) * 0.85, bz + z * (1 - 0.15 * slump)))
    faces = []
    for i in range(nz):
        for j in range(na):
            j2 = (j + 1) % na
            faces.append([i * na + j, i * na + j2, (i + 1) * na + j2, (i + 1) * na + j])
    faces.append(list(range(na - 1, -1, -1)))
    faces.append([nz * na + j for j in range(na)])
    P.add(key, np.array(verts), faces, None, rnd=rng.uniform())
    if tied:
        P.cyl("rope", (bx, by, bz + h * 0.83), (bx, by, bz + h * 0.87), r * 0.3, sides=10)


def bucket(P, base=(0, 0, 0), key="plank"):
    barrel(P, base, h=0.3, r=0.15, staves=12, bulge=-0.12, hoops=(0.15, 0.8), key=key, lid=False)
    bx, by, bz = base
    P.cyl(key, (bx, by, bz + 0.01), (bx, by, bz + 0.03), 0.16, sides=12)
    pts = [(bx - 0.165, by, bz + 0.26)]
    for i in range(1, 8):
        a = math.pi * i / 8
        pts.append((bx - 0.165 * math.cos(a), by, bz + 0.26 + 0.14 * math.sin(a)))
    pts.append((bx + 0.165, by, bz + 0.26))
    P.tube("iron", pts, [0.005] * len(pts), sides=4)


# ----------------------------------------------------------------------------
# wheels and the cart
# ----------------------------------------------------------------------------
def wheel(P, center, axis, radius=0.65, spokes=12, key="timber"):
    c = Vector(center)
    ax = Vector(axis).normalized()
    M = C.frame_from(ax)
    u, v = M.col[1], M.col[2]
    hub_l = 0.32
    P.cyl(key, c - ax * hub_l / 2, c + ax * hub_l / 2, 0.11, 0.1, sides=12)
    P.cyl("iron", c - ax * 0.07, c - ax * 0.05, 0.115, sides=12)
    P.cyl("iron", c + ax * 0.05, c + ax * 0.07, 0.115, sides=12)
    rf = radius - 0.06
    for k in range(spokes):
        a = 2 * math.pi * k / spokes
        d = u * math.cos(a) + v * math.sin(a)
        p0 = c + d * 0.09 + ax * (0.03 if k % 2 else -0.03)
        p1 = c + d * (rf - 0.02)
        P.tube(key, [p0, p1], [0.028, 0.02], sides=6)
    # felloes as a polygonal ring of boxes
    n = 24
    for k in range(n):
        a0 = 2 * math.pi * k / n
        a1 = 2 * math.pi * (k + 1) / n
        p0 = c + (u * math.cos(a0) + v * math.sin(a0)) * rf
        p1 = c + (u * math.cos(a1) + v * math.sin(a1)) * rf
        P.beam(key, p0, p1, 0.075, 0.08, up=(p0 + p1) * 0.5 - c, extend=0.01)
    # iron tyre
    pts = [c + (u * math.cos(2 * math.pi * k / 48) + v * math.sin(2 * math.pi * k / 48)) * (radius - 0.012) for k in range(49)]
    for off in (-0.025, 0.0, 0.025):
        P.tube("iron", [p + ax * off for p in pts], [0.012] * len(pts), sides=4, caps=False)


def cart(P, tilt_deg=16.5, key="plank"):
    """Two-wheeled farm cart; axle along X, shafts toward -Y, tipped forward so the shafts rest on the ground."""
    rng = P.rng
    R = 0.68
    # cart built with the axle at origin height R, then rotated about the axle (x) so shafts touch the ground
    parts_local = Parts(seed=rng.randint(1000))
    L = parts_local
    # wheels
    for sx in (-1, 1):
        wheel(L, (sx * 0.78, 0, 0), (1, 0, 0), radius=R)
    L.beam("timber", (-0.95, 0, 0), (0.95, 0, 0), 0.1, 0.1)
    # bed frame: side rails that continue forward as shafts
    for sx in (-1, 1):
        L.beam("timber", (sx * 0.52, 1.25, 0.2), (sx * 0.52, -1.1, 0.2), 0.09, 0.11)
        # shafts converge slightly
        L.beam("timber", (sx * 0.52, -1.1, 0.2), (sx * 0.36, -3.2, 0.24), 0.07, 0.08)
    for yy in (-1.05, -0.4, 0.3, 0.9, 1.2):
        L.beam("timber", (-0.6, yy, 0.12), (0.6, yy, 0.12), 0.08, 0.08)
    # floor planks
    for k in range(7):
        xx = -0.48 + k * 0.16
        L.beam(key, (xx, -1.1, 0.27), (xx, 1.28, 0.27), 0.15, 0.03, jitter=0.004)
    # low sides with stakes
    for sx in (-1, 1):
        for zz in (0.42, 0.62):
            L.beam(key, (sx * 0.56, -1.12, zz), (sx * 0.56, 1.28, zz), 0.025, 0.17, jitter=0.004)
        for yy in (-1.05, -0.35, 0.35, 1.2):
            L.beam("timber", (sx * 0.58, yy, 0.2), (sx * 0.58, yy, 0.8), 0.05, 0.05)
    # tail board
    L.beam(key, (-0.55, 1.29, 0.42), (0.55, 1.29, 0.42), 0.025, 0.17)
    # tip the cart forward about the axle so the shaft ends sit on the ground
    ang = math.radians(tilt_deg)
    Rm = np.array(Euler((ang, 0, 0)).to_matrix())

    def tf(v):
        return v @ Rm.T + np.array([0, 0, R])
    for k, mb in L.mb.items():
        for i, vv in enumerate(mb.verts):
            mb.verts[i] = tf(np.asarray(vv))
        tgt = P.mb[k]
        for vv, (fi0) in zip(mb.verts, range(len(mb.verts))):
            pass
        # merge into P
        base = tgt.nv
        tgt.verts.extend(mb.verts)
        tgt.faces.extend([[base + q for q in f] for f in mb.faces])
        tgt.uvs.extend(mb.uvs)
        tgt.mat.extend(mb.mat)
        tgt.frnd.extend(mb.frnd)
        for a in set(list(tgt.fattr.keys()) + list(mb.fattr.keys())):
            tgt.fattr.setdefault(a, [0.0] * (len(tgt.faces) - len(mb.faces)))
            tgt.fattr[a].extend(mb.fattr.get(a, [0.0] * len(mb.faces)))
        tgt.nv += mb.nv


# ----------------------------------------------------------------------------
# well, trough, bench, chopping block, ladder, signpost, grindstone, skeps
# ----------------------------------------------------------------------------
def stone_ring(P, r_out, r_in, z0, z1, rng=None):
    rng = rng or P.rng
    lib = stone_lib()
    rm = (r_out + r_in) / 2
    depth = r_out - r_in
    z = z0
    ci = 0
    while z < z1 - 0.05:
        h = rng.uniform(0.14, 0.24)
        if z + h > z1 - 0.06:
            h = z1 - z
        a = rng.uniform(0, 0.3)
        while a < 2 * math.pi + rng.uniform(0, 0.2) - 0.05:
            l = rng.uniform(0.25, 0.42)
            da = l / r_out
            am = a + da / 2
            v, f = lib[rng.randint(len(lib))]
            sz = np.array([(l - 0.02) / 2, depth / 2, (h - 0.02) / 2])
            vv = v * sz
            # bend the stone around the ring slightly by rotating into the tangent frame
            Rz = np.array(Euler((rng.normal(0, 0.02), rng.normal(0, 0.02), am - math.pi / 2)).to_matrix())
            vv = vv @ Rz.T + np.array([rm * math.cos(am), rm * math.sin(am), z + h / 2])
            P.add("stone", vv, f, None, rnd=rng.uniform())
            a += da
        z += h
        ci += 1
    P.cyl("mortar", (0, 0, z0), (0, 0, z1 - 0.01), r_out - 0.04, sides=24, caps=False)


def well(P):
    rng = P.rng
    stone_ring(P, 0.82, 0.52, -0.3, 0.78, rng)
    # cap stones
    n = 10
    for k in range(n):
        a = 2 * math.pi * (k + 0.5) / n
        P.box("stone", (0.67 * math.cos(a), 0.67 * math.sin(a), 0.82), (0.45, 0.34, 0.1), (0, 0, a + math.pi / 2), jitter=0.02)
    # dark shaft and water far below
    P.cyl("interior", (0, 0, -2.5), (0, 0, 0.7), 0.53, sides=24, caps=False)
    P.cyl("water", (0, 0, -1.8), (0, 0, -1.79), 0.52, sides=24)
    # posts, windlass, crank, roof
    for sx in (-1, 1):
        P.box("timber", (sx * 0.95, 0, 0.95), (0.14, 0.14, 2.3), jitter=0.01)
        P.box("timber", (sx * 0.95, 0, 0.05), (0.18, 0.5, 0.12))
    P.cyl("fresh", (-1.02, 0, 1.25), (1.02, 0, 1.25), 0.08, sides=12)
    P.cyl("rope", (-0.35, 0, 1.25), (0.35, 0, 1.25), 0.11, sides=14)
    P.beam("timber", (1.02, 0, 1.25), (1.12, 0, 1.25), 0.05, 0.05)
    P.beam("timber", (1.12, 0, 1.25), (1.12, 0.0, 0.95), 0.05, 0.05)
    P.beam("timber", (1.12, 0, 0.95), (1.25, 0, 0.95), 0.04, 0.04)
    P.tube("rope", [(0.2, -0.1, 1.2), (0.25, -0.15, 0.95), (0.42, -0.5, 0.85)], [0.012] * 3, sides=5)
    bucket(P, (0.42, -0.62, 0.86))
    # little gabled roof
    pitch = 35.0
    tn = math.tan(math.radians(pitch))
    P.beam("timber", (0, -0.0, 2.1), (0, 0.0, 2.1), 0.1, 0.1)
    P.beam("timber", (-1.15, 0, 2.15), (1.15, 0, 2.15), 0.1, 0.12)
    for sgn in (-1, 1):
        shingle_plane(P, -1.15, 1.15, sgn * 0.85, 0.0, 2.15 - 0.85 * tn * 0.3, 2.15 + 0.6 * tn * 0.5, rng=rng, expo=0.12, slen=0.34)


def trough(P, length=2.0, key="plank"):
    rng = P.rng
    w, h = 0.55, 0.42
    for sx in (-1, 1):
        P.box("stone", (sx * (length / 2 - 0.25), 0, 0.12), (0.3, 0.6, 0.3), jitter=0.03)
    z0 = 0.25
    P.box(key, (0, 0, z0 + 0.02), (length, w, 0.04))
    for sy in (-1, 1):
        P.box(key, (0, sy * (w / 2 - 0.02), z0 + h / 2), (length, 0.04, h), jitter=0.003)
    for sx in (-1, 1):
        P.box(key, (sx * (length / 2 - 0.02), 0, z0 + h / 2), (0.04, w - 0.08, h))
    P.box("water", (0, 0, z0 + h - 0.08), (length - 0.1, w - 0.1, 0.01))
    for sx in (-0.6, 0.6):
        P.box("iron", (sx, 0, z0 + h - 0.05), (0.05, w + 0.02, 0.1))


def bench(P, length=1.6, key="timber"):
    rng = P.rng
    P.log(key, (-length / 2, 0, 0.42), (length / 2, 0, 0.42), 0.15, sides=12, split=1, flip=True)
    for sx in (-1, 1):
        for sy in (-1, 1):
            P.cyl(key, (sx * (length / 2 - 0.18), sy * 0.08, 0.0), (sx * (length / 2 - 0.15), sy * 0.13, 0.4), 0.035, sides=6)


def chopping_block(P, axe=True):
    rng = P.rng
    P.log("logs", (0, 0, 0.0), (0, 0, 0.5), 0.27, sides=14, split=0)
    if axe:
        # handle stuck at an angle, iron head buried in the top
        a = Vector((0.02, 0.0, 0.47))
        b = a + Vector((0.55, 0.15, 0.32))
        P.tube("fresh", [a, b], [0.02, 0.018], sides=6)
        P.beam("iron", a + Vector((-0.06, 0, -0.03)), a + Vector((0.08, 0, 0.06)), 0.03, 0.12, up=Vector((0, 1, 0)))
    # a few split pieces lying around
    for k in range(5):
        x, y = rng.uniform(-0.9, 0.9), rng.uniform(-0.9, 0.9)
        if abs(x) < 0.4 and abs(y) < 0.4:
            continue
        a = rng.uniform(0, 2 * math.pi)
        p0 = (x, y, 0.07)
        p1 = (x + 0.42 * math.cos(a), y + 0.42 * math.sin(a), 0.07)
        P.log("logs", p0, p1, rng.uniform(0.06, 0.09), split=rng.randint(1, 3))


def woodpile(P, length=3.0, height=1.2, depth=0.45):
    rng = P.rng
    z = 0.0
    row = 0
    P.beam("timber", (-length / 2, -0.1, 0.05), (length / 2, -0.1, 0.05), 0.1, 0.1)
    P.beam("timber", (-length / 2, 0.25, 0.05), (length / 2, 0.25, 0.05), 0.1, 0.1)
    z = 0.1
    while z < height:
        y = -length / 2 + (0.07 if row % 2 else 0.0)
        rmax = 0.0
        while y < length / 2 - 0.08:
            r = rng.uniform(0.05, 0.085)
            rmax = max(rmax, r)
            x0 = -depth / 2 + rng.uniform(-0.03, 0.03)
            P.log("logs", (x0 * 0 + y, x0, z + r), (y + rng.normal(0, 0.02), x0 + depth, z + r + rng.normal(0, 0.01)), r, split=rng.randint(0, 3))
            y += 2 * r + 0.005
        z += rmax * 1.75
        row += 1
    # stakes holding the ends
    for sx in (-1, 1):
        P.box("timber", (sx * (length / 2 + 0.05), 0.08, height / 2), (0.08, 0.08, height + 0.1), jitter=0.02)


def ladder(P, length=4.0, key="fresh"):
    for sx in (-1, 1):
        P.beam(key, (sx * 0.22, 0, 0), (sx * 0.2, 0, length), 0.06, 0.05)
    n = int(length / 0.3)
    for k in range(1, n):
        z = k * length / n
        P.cyl(key, (-0.24, 0, z), (0.24, 0, z), 0.018, sides=6)


def signpost(P, arms=((25.0, "E"), (205.0, "W")), key="plank"):
    P.box("timber", (0, 0, 1.0), (0.14, 0.14, 2.2), jitter=0.01)
    for k, (ang, _) in enumerate(arms):
        a = math.radians(ang)
        z = 1.85 - k * 0.22
        d = Vector((math.cos(a), math.sin(a), 0))
        p0 = Vector((0, 0, z)) + d * 0.05
        p1 = p0 + d * 0.75
        P.beam(key, p0, p1, 0.03, 0.15, jitter=0.01)
        # pointed tip
        P.beam(key, p1, p1 + d * 0.1, 0.03, 0.08)


def skep(P, base=(0, 0, 0), h=0.45, r=0.26):
    """Coiled-straw beehive."""
    rng = P.rng
    bx, by, bz = base
    nz, na = 30, 28
    verts = []
    for i in range(nz + 1):
        t = i / nz
        prof = r * math.sqrt(max(1 - t ** 2.2, 0.0)) + 0.01
        coil = 1 + 0.04 * math.cos(t * nz * math.pi)
        for j in range(na):
            a = 2 * math.pi * j / na
            verts.append((bx + prof * coil * math.cos(a), by + prof * coil * math.sin(a), bz + h * t))
    faces = []
    for i in range(nz):
        for j in range(na):
            j2 = (j + 1) % na
            faces.append([i * na + j, i * na + j2, (i + 1) * na + j2, (i + 1) * na + j])
    faces.append([nz * na + j for j in range(na)])
    P.add("straw", np.array(verts), faces, None, rnd=rng.uniform())
    P.box("interior", (bx + r * 0.95, by, bz + 0.04), (0.06, 0.08, 0.06))


def grindstone(P):
    P.cyl("stone", (-0.07, 0, 0.75), (0.07, 0, 0.75), 0.42, sides=24)
    P.cyl("iron", (-0.35, 0, 0.75), (0.35, 0, 0.75), 0.025, sides=8)
    for sx in (-1, 1):
        P.beam("timber", (sx * 0.25, -0.5, 0.0), (sx * 0.25, 0.0, 0.78), 0.07, 0.07)
        P.beam("timber", (sx * 0.25, 0.5, 0.0), (sx * 0.25, 0.0, 0.78), 0.07, 0.07)
    P.box("plank", (0, 0, 0.42), (0.38, 0.6, 0.05))
    P.beam("timber", (0.35, 0, 0.75), (0.5, 0, 0.75), 0.04, 0.04)
    P.beam("timber", (0.5, 0, 0.75), (0.5, 0, 0.45), 0.04, 0.04)


def clay_pot(P, base=(0, 0, 0), h=0.4, r=0.18):
    rng = P.rng
    bx, by, bz = base
    prof = [(0.6, 0.0), (0.85, 0.15), (1.0, 0.4), (0.95, 0.65), (0.6, 0.85), (0.5, 0.92), (0.62, 1.0)]
    na = 20
    verts = []
    for (pr, pz) in prof:
        for j in range(na):
            a = 2 * math.pi * j / na
            verts.append((bx + r * pr * math.cos(a), by + r * pr * math.sin(a), bz + h * pz))
    # inner lip down a bit
    for j in range(na):
        a = 2 * math.pi * j / na
        verts.append((bx + r * 0.55 * math.cos(a), by + r * 0.55 * math.sin(a), bz + h * 0.8))
    faces = []
    nr = len(prof) + 1
    for i in range(nr - 1):
        for j in range(na):
            j2 = (j + 1) % na
            faces.append([i * na + j, i * na + j2, (i + 1) * na + j2, (i + 1) * na + j])
    faces.append(list(range(na - 1, -1, -1)))
    faces.append([(nr - 1) * na + j for j in range(na)])
    P.add("clay", np.array(verts), faces, None, rnd=rng.uniform())


def hitching_rail(P, length=2.6):
    for sx in (-1, 1):
        P.box("timber", (sx * length / 2, 0, 0.5), (0.16, 0.16, 1.2), jitter=0.02)
    P.log("timber", (-length / 2 - 0.15, 0, 1.0), (length / 2 + 0.15, 0, 1.03), 0.06, sides=8, split=0)


def manure_heap(P, R=1.3, H=0.7):
    rng = P.rng
    v, f = PL.rock(rng, 1.0, flat=1.0, sub=4)
    v = v / np.abs(v).max(axis=0)
    v[:, 2] = np.clip(v[:, 2], -0.05, None)
    v = v * np.array([R, R * 0.8, H])
    P.add("muck", v, f, None)


def haystack(P, st, H=3.2, R=1.7, lean=0.05):
    """Beehive haystack round a central pole, with loose straw strands."""
    rng = P.rng
    nz, na = 22, 40
    verts = []
    seed = rng.randint(1000)
    for i in range(nz + 1):
        t = i / nz
        prof = R * (1 - t ** 2.4) ** 0.55 * (1 + 0.06 * math.sin(t * math.pi)) + 0.02
        if t < 0.08:
            prof *= 0.93 + t
        for j in range(na):
            a = 2 * math.pi * j / na
            n = float(C.fbm(math.cos(a) * 2 + t * 3, math.sin(a) * 2, 3, seed))
            rr = prof * (1 + 0.07 * n)
            verts.append((rr * math.cos(a) + lean * H * t * t, rr * math.sin(a), H * t))
    faces = []
    for i in range(nz):
        for j in range(na):
            j2 = (j + 1) % na
            faces.append([i * na + j, i * na + j2, (i + 1) * na + j2, (i + 1) * na + j])
    faces.append([nz * na + j for j in range(na)])
    P.add("straw", np.array(verts), faces, None)
    P.cyl("fresh", (0, 0, -0.2), (lean * H * 0.9, 0, H + 0.7), 0.06, 0.035, sides=8)
    # strands all over, hanging down the surface
    for k in range(5000):
        t = rng.uniform(0.0, 0.97) ** 0.8
        a = rng.uniform(0, 2 * math.pi)
        prof = R * (1 - t ** 2.4) ** 0.55 * (1 + 0.06 * math.sin(t * math.pi)) + 0.02
        p = np.array([prof * math.cos(a) + lean * H * t * t, prof * math.sin(a), H * t])
        outward = np.array([math.cos(a), math.sin(a), 0.0])
        d = np.array([0, 0, -1.0]) + outward * rng.uniform(0.2, 0.7) + rng.normal(0, 0.3, 3)
        st.add(p + outward * 0.01, d, rng.uniform(0.1, 0.3), rng.uniform(0.003, 0.006), straw_colour(rng, 0.35), segs=2)
    # spilled hay round the base
    for k in range(700):
        a = rng.uniform(0, 2 * math.pi)
        r = R + rng.uniform(-0.1, 0.9) ** 2
        p = np.array([r * math.cos(a), r * math.sin(a), 0.02])
        b = rng.uniform(0, 2 * math.pi)
        st.add(p, (math.cos(b), math.sin(b), 0.05), rng.uniform(0.1, 0.3), rng.uniform(0.003, 0.006), straw_colour(rng, 0.45), segs=1)


# ----------------------------------------------------------------------------
# fences
# ----------------------------------------------------------------------------
def split_rail_fence(P, pts, post_h=1.25, rails=(0.45, 0.9), spacing=2.6, broken=0.08, ground=None):
    """Post-and-rail fence along a polyline of (x, y) local points. ground(x, y) -> z offset."""
    rng = P.rng
    ground = ground or (lambda x, y: 0.0)
    posts = []
    for i in range(len(pts) - 1):
        a = np.array(pts[i], float)
        b = np.array(pts[i + 1], float)
        L = np.linalg.norm(b - a)
        n = max(int(round(L / spacing)), 1)
        for k in range(n):
            posts.append(a + (b - a) * k / n)
    posts.append(np.array(pts[-1], float))
    tops = []
    for p in posts:
        gz = ground(p[0], p[1])
        h = post_h + rng.uniform(-0.08, 0.06)
        lean = rng.normal(0, 0.03, 2)
        P.log("timber", (p[0], p[1], gz - 0.3), (p[0] + lean[0], p[1] + lean[1], gz + h), rng.uniform(0.06, 0.08), sides=7, split=2)
        tops.append((p, gz))
    for i in range(len(posts) - 1):
        (pa, za), (pb, zb) = tops[i], tops[i + 1]
        for rz in rails:
            if rng.uniform() < broken:
                # a broken rail hanging from one post
                end = pa + (pb - pa) * rng.uniform(0.3, 0.6)
                P.log("timber", (pa[0], pa[1], za + rz), (end[0], end[1], za + rz * 0.3), 0.05, sides=7, split=1)
                continue
            sag = rng.uniform(0.0, 0.05)
            P.log("timber", (pa[0], pa[1], za + rz + rng.normal(0, 0.02)), (pb[0], pb[1], zb + rz - sag), rng.uniform(0.045, 0.06), sides=7, split=rng.randint(1, 3))


def wattle_fence(P, pts, h=0.95, stake_gap=0.42, rod_r=0.011, ground=None, gaps=()):
    """Woven hazel hurdle fence along a polyline (local coordinates)."""
    rng = P.rng
    ground = ground or (lambda x, y: 0.0)
    for i in range(len(pts) - 1):
        a = np.array(pts[i], float)
        b = np.array(pts[i + 1], float)
        L = np.linalg.norm(b - a)
        d = (b - a) / L
        n = np.array([-d[1], d[0]])
        ns = max(int(L / stake_gap), 1)
        ss = np.linspace(0, L, ns + 1)
        for s in ss:
            p = a + d * s
            gz = ground(p[0], p[1])
            hh = h + rng.uniform(0.0, 0.18)
            P.cyl("withy", (p[0], p[1], gz - 0.2), (p[0] + rng.normal(0, 0.02), p[1] + rng.normal(0, 0.02), gz + hh), rng.uniform(0.022, 0.032), rng.uniform(0.016, 0.024), sides=6)
        nrods = int(h / (rod_r * 2.2))
        for r_ in range(nrods):
            z = 0.06 + r_ * rod_r * 2.15
            if z > h - 0.02:
                break
            phase = r_ % 2
            path = []
            m = ns * 6
            for k in range(m + 1):
                s = L * k / m
                p = a + d * s
                gz = ground(p[0], p[1])
                w = math.sin(math.pi * (s / (L / ns)) + phase * math.pi) * 0.028
                path.append((p[0] + n[0] * w, p[1] + n[1] * w, gz + z + rng.normal(0, 0.002)))
            P.tube("withy", path, [rod_r * rng.uniform(0.85, 1.15)] * len(path), sides=5, caps=True)


# ----------------------------------------------------------------------------
# garden
# ----------------------------------------------------------------------------
def cabbage_geo(rng):
    geo = PL.Geo()
    outer = PL.lin((0.22, 0.32, 0.18))
    inner = PL.lin((0.42, 0.52, 0.30))
    for k in range(9):
        a = k * 2.39996
        d = Vector((math.cos(a), math.sin(a), 0.6 + 0.08 * k)).normalized()
        L = 0.17 - k * 0.008
        PL.add_leaf(geo, (0, 0, 0.02 + k * 0.006), d, (0, 0, 1), L, L * 0.95, outer * rng.uniform(0.85, 1.15), n=10, shape='oval', fold=0.05, curl=0.35)
    # head
    for k in range(10):
        a = k * 2.39996
        d = Vector((math.cos(a), math.sin(a), 1.4)).normalized()
        PL.add_leaf(geo, (0, 0, 0.05), d, (math.cos(a), math.sin(a), 0.2), 0.11, 0.12, inner * rng.uniform(0.9, 1.1), n=8, shape='oval', fold=0.1, curl=-0.4)
    return geo


def leek_geo(rng):
    geo = PL.Geo()
    col = PL.lin((0.20, 0.36, 0.22))
    for k in range(7):
        a = rng.uniform(0, 2 * math.pi)
        PL.blade(geo, rng, (0, 0, 0), rng.uniform(0.25, 0.42), 0.02, rng.uniform(0.1, 0.5), a, 0.6, 0.0, col * 0.8, col * 1.1, nseg=5)
    return geo
