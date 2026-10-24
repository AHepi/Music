"""The village buildings: four cottages and the stable."""
import bpy
import numpy as np
import math
from mathutils import Vector, Matrix, Euler
import common as C
import layout as L
from bparts import framed_gable
from bparts import Parts, Wall, framed_wall, stone_wall, thatch_gabled, thatch_ridge, thatch_hipped, shingle_plane, plank_door, window_open, chimney, Strands, thatch_fringe_gabled, thatch_fringe_hipped

BEVEL = {"timber": 0.012, "plank": 0.006, "plank_dark": 0.005, "fresh": 0.005, "shingle": 0.003, "hazel": 0.0}
SUBS = {"thatch": 0, "thatch_ridge": 1}   # pass 2: no smoothing, the eave keeps a cut edge (was a "sausage")
STRANDS = False                           # pass 2: no stray straws hanging over the walls


def site(bname):
    b = L.BUILDINGS[bname]
    c, s = math.cos(math.radians(b["rot"])), math.sin(math.radians(b["rot"]))
    hw, hd = b["w"] / 2, b["d"] / 2
    pts = [(b["x"] + c * lx - s * ly, b["y"] + s * lx + c * ly) for lx, ly in ((-hw, -hd), (hw, -hd), (hw, hd), (-hw, hd), (0, 0))]
    zs = [float(L.height(px, py)) for px, py in pts]
    return (b["x"], b["y"], float(np.mean(zs[:4])) + 0.03), b["rot"], b


def weatherboard_gable(parts, x_face, nx, y_half, z_base, tn, board=0.2, lap=0.03, rng=None):
    """Horizontal lapped boards filling a gable triangle on the plane x = x_face (outward normal nx)."""
    rng = rng or parts.rng
    z = z_base
    k = 0
    while True:
        w = y_half - (z - z_base) / tn
        if w < 0.08:
            break
        top = z + board
        w_top = max(y_half - (top - z_base) / tn, 0.0)
        # tilt: bottom edge sticks out more
        a = Vector((x_face + nx * 0.035, -w, z))
        b = Vector((x_face + nx * 0.035, w, z))
        parts.box("plank", (x_face + nx * 0.02, 0, z + board / 2), (0.025, 2 * max(w_top, 0.05) + (w - w_top), board + lap), Euler((0, math.radians(-4) * nx, 0)), rnd=rng.uniform())
        z += board - lap
        k += 1


def cottage_a(col, mats):
    """Timber-framed cottage with daub panels, a stone plinth, gabled thatch and a stone chimney."""
    (x, y, z), rot, b = site("cottage_a")
    P = Parts(seed=11)
    rng = P.rng
    Lx, Dy = 8.4, 5.2          # wall centre-line rectangle
    zb, zt = 0.35, 2.85        # sole plate bottom / wall plate top
    pitch = 50.0
    # plinth
    walls_c = [Wall((-Lx / 2, -Dy / 2), (Lx / 2, -Dy / 2), (0, -1)), Wall((Lx / 2, -Dy / 2), (Lx / 2, Dy / 2), (1, 0)),
               Wall((Lx / 2, Dy / 2), (-Lx / 2, Dy / 2), (0, 1)), Wall((-Lx / 2, Dy / 2), (-Lx / 2, -Dy / 2), (-1, 0))]
    for i, w in enumerate(walls_c):
        e = 0.21
        alt = ((e, -e), (e, -e)) if i % 2 == 0 else ((-e, e), (-e, e))
        stone_wall(P, w, -0.55, zb, 0.42, rng=rng, course=(0.13, 0.24), slen=(0.2, 0.45), alt_ext=alt, depth=0.2)
    # front wall (y = -Dy/2), posts chosen to frame a door and two windows
    front = walls_c[0]
    posts = [0.0, 1.1, 2.15, 3.2, 4.2, 5.25, 6.3, 7.35, 8.4]
    bays = [dict(rails=[1.5]), dict(window=(1.35, 2.15)), dict(rails=[1.5]), dict(rails=[1.5]), dict(door=(0.55, 2.3)),
            dict(rails=[1.5]), dict(window=(1.35, 2.15)), dict(rails=[1.5])]
    braces = [(0.1, 0.62, 1.0, 2.55), (8.3, 0.62, 7.4, 2.55)]
    framed_wall(P, front, zb, zt, posts, bays, braces=braces, plate_ext=(0.12, 0.12))
    back = walls_c[2]
    posts_b = [0.0, 1.4, 2.8, 4.2, 5.6, 7.0, 8.4]
    bays_b = [dict(rails=[1.5]), dict(rails=[1.5]), dict(window=(1.45, 2.05)), dict(rails=[1.5]), dict(rails=[1.5]), dict(rails=[1.5])]
    framed_wall(P, back, zb, zt, posts_b, bays_b, braces=[(0.1, 0.62, 1.3, 2.55), (8.3, 0.62, 7.1, 2.55)], plate_ext=(0.12, 0.12))
    for wi, w in ((1, walls_c[1]), (3, walls_c[3])):
        ps = [0.0, 1.3, 2.6, 3.9, 5.2]
        bs = [dict(rails=[1.5]), dict(rails=[1.5]), dict(window=(1.45, 2.05)) if wi == 3 else dict(rails=[1.5]), dict(rails=[1.5])]
        framed_wall(P, w, zb + 0.0, zt - 0.0, ps, bs, braces=[(0.15, 0.62, 1.2, 2.55), (5.05, 0.62, 4.0, 2.55)], plate_ext=(-0.1, -0.1), skip_end_posts=True)
    # remove duplicate corner posts: side walls drew posts at their ends too -> acceptable overlap (same box), nudge inward
    # gables: lapped weatherboards
    tn = math.tan(math.radians(pitch))
    for sx in (-1, 1):
        framed_gable(P, sx * (Lx / 2), sx, Dy / 2 + 0.1, zt, tn)
    # floor and inside darkness
    P.box("floor", (0, 0, zb + 0.05), (Lx - 0.2, Dy - 0.2, 0.1))
    P.box("interior", (0, 0, zt + 0.04), (Lx - 0.1, Dy - 0.1, 0.04))
    # door and step
    plank_door(P, front, 4.3, 5.15, 0.56, 2.29, 0.0, open_deg=38.0, hinge_left=False)
    P.box("stone", front.pt(4.72, 0.2, -0.45), (1.25, 0.55, 0.22), front.rot(), jitter=0.01)
    # windows with shutters
    for (s0, s1) in ((1.2, 2.05), (6.4, 7.25)):
        window_open(P, front, s0, s1, 1.36, 2.14, 0.065, 0.2, bars=2, shutters=True, open_deg=118)
    window_open(P, back, 2.9, 4.1, 1.46, 2.04, 0.065, 0.2, bars=3, shutters=False)
    window_open(P, walls_c[3], 2.7, 3.8, 1.46, 2.04, 0.065, 0.2, bars=2, shutters=True, open_deg=125)
    # thatch
    info = thatch_gabled(P, Lx + 0.2, Dy + 0.2, zt, pitch, oe=0.6, og=0.42, t=0.27, rng=rng)
    thatch_ridge(P, info, rng=rng)
    # chimney through the ridge near the east gable
    ztop = info["surface"](2.9, 0.25) + 0.95
    chimney(P, (2.9, 0.25), zt + 1.0, ztop, w=0.78, d=0.62, rng=rng)
    parent = bpy.data.objects.new("cottage_a", None)
    col.objects.link(parent)
    parent.location = (x, y, z)
    parent.rotation_euler = (0, 0, math.radians(rot))
    obs = P.build("cottage_a", col, mats, bevel=BEVEL, subsurf=SUBS, parent=parent)
    if STRANDS:
        st = Strands()
        thatch_fringe_gabled(st, info, rng)
        st.build("cottage_a_straw", col, mats["strands"], parent=parent)
    return parent, dict(z=z, info=dict(ridge=info["ridge_z"]))


def _place_parent(name, col, x, y, z, rot):
    parent = bpy.data.objects.new(name, None)
    col.objects.link(parent)
    parent.location = (x, y, z)
    parent.rotation_euler = (0, 0, math.radians(rot))
    return parent


def cottage_b(col, mats):
    """Fieldstone cottage with a hipped, round-cornered thatch and a stone chimney."""
    (x, y, z), rot, b = site("cottage_b")
    P = Parts(seed=22)
    rng = P.rng
    Lx, Dy, T = 6.7, 4.5, 0.5
    zt = 2.25
    walls = [Wall((-Lx / 2, -Dy / 2), (Lx / 2, -Dy / 2), (0, -1)), Wall((Lx / 2, -Dy / 2), (Lx / 2, Dy / 2), (1, 0)),
             Wall((Lx / 2, Dy / 2), (-Lx / 2, Dy / 2), (0, 1)), Wall((-Lx / 2, Dy / 2), (-Lx / 2, -Dy / 2), (-1, 0))]
    door = (2.9, 3.8, 0.05, 1.85)
    win_f = [(1.0, 1.65, 0.95, 1.6), (5.05, 5.7, 0.95, 1.6)]
    win_b = [(2.9, 3.6, 1.0, 1.55)]
    win_e = [(1.9, 2.55, 1.0, 1.55)]
    openings = {0: [door] + win_f, 1: win_e, 2: win_b, 3: []}
    e = T / 2
    for i, w in enumerate(walls):
        alt = ((e, -e), (e, -e)) if i % 2 == 0 else ((-e, e), (-e, e))
        stone_wall(P, w, -0.5, zt, T, openings=openings[i], rng=rng, course=(0.12, 0.36), slen=(0.18, 0.72), alt_ext=alt, depth=0.24)
    # lintels and sills, door, windows
    front = walls[0]
    for (s0, s1, z0, z1) in [door] + win_f:
        front.box(P, "timber", s0 - 0.2, s1 + 0.2, z1, z1 + 0.16, T / 2 - 0.2, T / 2 + 0.01, jitter=0.004)
    for (s0, s1, z0, z1) in win_f:
        front.box(P, "stone", s0 - 0.08, s1 + 0.08, z0 - 0.07, z0, T / 2 - 0.25, T / 2 + 0.05)
        window_open(P, front, s0, s1, z0, z1, T / 2, 0.3, bars=2, shutters=True, open_deg=170)
    for wi, lst in ((1, win_e), (2, win_b)):
        for (s0, s1, z0, z1) in lst:
            walls[wi].box(P, "timber", s0 - 0.2, s1 + 0.2, z1, z1 + 0.15, T / 2 - 0.2, T / 2 + 0.01)
            window_open(P, walls[wi], s0, s1, z0, z1, T / 2, 0.3, bars=2, shutters=False)
    # door jamb lining and the door, slightly open
    front.box(P, "timber", door[0] - 0.08, door[0], door[2], door[3], -T / 2, T / 2 - 0.02)
    front.box(P, "timber", door[1], door[1] + 0.08, door[2], door[3], -T / 2, T / 2 - 0.02)
    plank_door(P, front, door[0], door[1], door[2], door[3] - 0.01, T / 2 - 0.12, open_deg=12.0, hinge_left=True)
    P.box("stone", front.pt((door[0] + door[1]) / 2, -0.08, T / 2 + 0.3), (1.2, 0.6, 0.2), front.rot(), jitter=0.01)
    P.box("floor", (0, 0, 0.06), (Lx - T, Dy - T, 0.1))
    P.box("interior", (0, 0, zt - 0.02), (Lx - T + 0.02, Dy - T + 0.02, 0.04))
    info = thatch_hipped(P, Lx + T, Dy + T, zt, 48.0, oe=0.5, t=0.34, p=4.0, rng=rng)
    # chimney on the west end of the ridge
    ztop = info["ridge_z"] + 0.9
    chimney(P, (-1.6, 0.0), zt + 0.5, ztop, w=0.7, d=0.62, rng=rng)
    parent = _place_parent("cottage_b", col, x, y, z, rot)
    P.build("cottage_b", col, mats, bevel=BEVEL, subsurf=SUBS, parent=parent)
    if STRANDS:
        st = Strands()
        thatch_fringe_hipped(st, info, rng)
        st.build("cottage_b_straw", col, mats["strands"], parent=parent)
    return parent, dict(z=z, ridge=info["ridge_z"])


def cottage_d(col, mats):
    """Small wattle-and-daub hut with a low hipped thatch."""
    (x, y, z), rot, b = site("cottage_d")
    P = Parts(seed=44)
    rng = P.rng
    Lx, Dy, T = 5.2, 4.0, 0.22
    zt = 1.75
    walls = [Wall((-Lx / 2, -Dy / 2), (Lx / 2, -Dy / 2), (0, -1)), Wall((Lx / 2, -Dy / 2), (Lx / 2, Dy / 2), (1, 0)),
             Wall((Lx / 2, Dy / 2), (-Lx / 2, Dy / 2), (0, 1)), Wall((-Lx / 2, Dy / 2), (-Lx / 2, -Dy / 2), (-1, 0))]
    # low stone footing
    e = 0.17
    for i, w in enumerate(walls):
        alt = ((e, -e), (e, -e)) if i % 2 == 0 else ((-e, e), (-e, e))
        stone_wall(P, w, -0.45, 0.2, 0.34, rng=rng, course=(0.12, 0.2), slen=(0.18, 0.4), alt_ext=alt, depth=0.18,
                   openings=[(3.15, 4.05, 0.0, 0.3)] if i == 0 else [])
    # daub walls: slightly bulging thick panels between corner and door posts
    door = (3.2, 4.0)
    front = walls[0]
    for i, w in enumerate(walls):
        segs = [(0.12, w.L - 0.12)]
        if i == 0:
            segs = [(0.12, door[0] - 0.08), (door[1] + 0.08, w.L - 0.12)]
        if i == 1:
            segs = [(0.12, 1.45), (2.15, w.L - 0.12)]
        for (s0, s1) in segs:
            n = max(int((s1 - s0) / 0.5), 1)
            for k in range(n):
                a = s0 + (s1 - s0) * k / n
                bb = s0 + (s1 - s0) * (k + 1) / n
                bulge = rng.uniform(-0.012, 0.02)
                w.box(P, "daub", a - 0.005, bb + 0.005, 0.18, zt, -T / 2, T / 2 + bulge)
        if i == 0:
            w.box(P, "daub", door[0] - 0.08, door[1] + 0.08, 1.62, zt, -T / 2, T / 2)
        # corner posts
        w.box(P, "timber", -0.12, 0.12, 0.15, zt + 0.05, -0.12, 0.12, jitter=0.01)
    # window on the east wall (gap left in the daub panels, filled above and below)
    east = walls[1]
    east.box(P, "daub", 1.45, 2.15, 0.18, 0.95, -T / 2, T / 2)
    east.box(P, "daub", 1.45, 2.15, 1.42, zt, -T / 2, T / 2)
    east.box(P, "timber", 1.35, 2.25, 1.42, 1.52, -0.12, 0.14)
    window_open(P, east, 1.5, 2.1, 0.96, 1.41, T / 2, 0.22, bars=2, shutters=True, open_deg=150)
    front.box(P, "timber", door[0] - 0.09, door[0], 0.18, 1.62, -0.12, 0.13, jitter=0.006)
    front.box(P, "timber", door[1], door[1] + 0.09, 0.18, 1.62, -0.12, 0.13, jitter=0.006)
    front.box(P, "timber", door[0] - 0.15, door[1] + 0.15, 1.55, 1.66, -0.12, 0.14, jitter=0.006)
    plank_door(P, front, door[0], door[1], 0.2, 1.55, T / 2 - 0.02, open_deg=70.0, hinge_left=False)
    P.box("floor", (0, 0, 0.12), (Lx - T, Dy - T, 0.1))
    P.box("interior", (0, 0, zt), (Lx, Dy, 0.04))
    info = thatch_hipped(P, Lx + T, Dy + T, zt, 52.0, oe=0.5, t=0.32, p=3.0, rng=rng)
    parent = _place_parent("cottage_d", col, x, y, z, rot)
    P.build("cottage_d", col, mats, bevel=BEVEL, subsurf=SUBS, parent=parent)
    if STRANDS:
        st = Strands()
        thatch_fringe_hipped(st, info, rng)
        st.build("cottage_d_straw", col, mats["strands"], parent=parent)
    return parent, dict(z=z, ridge=info["ridge_z"])


def shingle_gable_roof(P, L, D, z_wp, pitch, oe, og, rng, rafters=False, battens=False, rafter_key="timber"):
    """Gabled shingle roof with ridge boards and barge boards. Returns ridge height."""
    tn = math.tan(math.radians(pitch))
    Lh = L / 2 + og
    Dh = D / 2 + oe
    z_eave = z_wp - oe * tn + 0.06
    z_ridge = z_wp + (D / 2) * tn + 0.06
    for sgn in (-1, 1):
        shingle_plane(P, -Lh, Lh, sgn * Dh, 0.0, z_eave, z_ridge, rng=rng, batten_key=("plank" if battens else None))
    # ridge boards
    for sgn in (-1, 1):
        a = Vector((-Lh - 0.05, sgn * 0.08, z_ridge + 0.035))
        b = Vector((Lh + 0.05, sgn * 0.08, z_ridge + 0.035))
        P.beam("plank", a, b, 0.22, 0.03, up=Vector((0, -sgn * math.sin(math.radians(pitch)), math.cos(math.radians(pitch)))))
    # barge boards along the verges
    for sx in (-1, 1):
        for sgn in (-1, 1):
            a = Vector((sx * (Lh + 0.02), sgn * Dh, z_eave - 0.05))
            b = Vector((sx * (Lh + 0.02), 0.0, z_ridge - 0.05))
            P.beam("plank", a, b, 0.03, 0.22, up=Vector((0, 0, 1)))
    if rafters:
        n = int(2 * Lh / 0.6)
        for k in range(n + 1):
            xx = -Lh + 0.1 + k * (2 * Lh - 0.2) / n
            for sgn in (-1, 1):
                a = Vector((xx, sgn * (Dh - 0.05), z_eave - 0.12))
                b = Vector((xx, 0.0, z_ridge - 0.12))
                P.beam(rafter_key, a, b, 0.08, 0.13, up=Vector((0, -sgn * math.sin(math.radians(pitch)), math.cos(math.radians(pitch)))))
    return z_ridge, z_eave, tn


def cottage_c(col, mats):
    """Timber-framed cottage with a shingle roof and a lean-to woodshed."""
    (x, y, z), rot, b = site("cottage_c")
    P = Parts(seed=33)
    rng = P.rng
    Lx, Dy = 7.6, 5.0
    zb, zt = 0.35, 2.75
    walls_c = [Wall((-Lx / 2, -Dy / 2), (Lx / 2, -Dy / 2), (0, -1)), Wall((Lx / 2, -Dy / 2), (Lx / 2, Dy / 2), (1, 0)),
               Wall((Lx / 2, Dy / 2), (-Lx / 2, Dy / 2), (0, 1)), Wall((-Lx / 2, Dy / 2), (-Lx / 2, -Dy / 2), (-1, 0))]
    for i, w in enumerate(walls_c):
        e = 0.21
        alt = ((e, -e), (e, -e)) if i % 2 == 0 else ((-e, e), (-e, e))
        stone_wall(P, w, -0.55, zb, 0.42, rng=rng, course=(0.13, 0.24), slen=(0.2, 0.45), alt_ext=alt, depth=0.2)
    front = walls_c[0]
    posts = [0.0, 1.25, 2.5, 3.5, 4.5, 6.3, 7.6]
    bays = [dict(rails=[1.45]), dict(window=(1.3, 2.05)), dict(rails=[1.45]), dict(door=(0.55, 2.25)), dict(rails=[0.95, 1.85]), dict(rails=[1.45])]
    framed_wall(P, front, zb, zt, posts, bays, braces=[(0.1, 0.62, 1.15, 2.45), (6.4, 2.45, 7.5, 0.62), (4.6, 0.62, 6.2, 2.45)], plate_ext=(0.12, 0.12))
    back = walls_c[2]
    framed_wall(P, back, zb, zt, [0.0, 1.9, 3.8, 5.7, 7.6], [dict(rails=[1.45]), dict(window=(1.4, 2.0)), dict(rails=[1.45]), dict(rails=[1.45])],
                braces=[(0.1, 0.62, 1.8, 2.45), (7.5, 0.62, 5.8, 2.45)], plate_ext=(0.12, 0.12))
    for wi in (1, 3):
        framed_wall(P, walls_c[wi], zb, zt, [0.0, 1.25, 2.5, 3.75, 5.0], [dict(rails=[1.45])] * 4,
                    braces=[(0.15, 0.62, 1.15, 2.45), (4.85, 0.62, 3.85, 2.45)], plate_ext=(-0.1, -0.1), skip_end_posts=True)
    tn = math.tan(math.radians(46.0))
    for sx in (-1, 1):
        framed_gable(P, sx * (Lx / 2), sx, Dy / 2 + 0.1, zt, tn)
    P.box("floor", (0, 0, zb + 0.05), (Lx - 0.2, Dy - 0.2, 0.1))
    P.box("interior", (0, 0, zt + 0.04), (Lx - 0.1, Dy - 0.1, 0.04))
    plank_door(P, front, 3.6, 4.4, 0.56, 2.24, 0.0, open_deg=0.0, hinge_left=True)
    P.box("stone", front.pt(4.0, 0.2, -0.45), (1.1, 0.5, 0.22), front.rot(), jitter=0.01)
    window_open(P, front, 1.35, 2.4, 1.31, 2.04, 0.065, 0.2, bars=3, shutters=True, open_deg=160)
    window_open(P, back, 2.0, 3.7, 1.41, 1.99, 0.065, 0.2, bars=3, shutters=False)
    zr, ze, _ = shingle_gable_roof(P, Lx + 0.2, Dy + 0.2, zt, 46.0, 0.5, 0.35, rng)
    # lean-to woodshed on the east gable
    sx0 = Lx / 2 + 0.1
    for (py_, ph) in ((-2.0, 1.95), (0.0, 1.95), (2.0, 1.95)):
        P.box("timber", (sx0 + 1.9, py_, ph / 2), (0.16, 0.16, ph + 0.2), jitter=0.01)
    P.beam("timber", (sx0 + 1.9, -2.3, 1.95), (sx0 + 1.9, 2.3, 1.95), 0.16, 0.16)
    P.beam("timber", (sx0, -2.3, 2.45), (sx0, 2.3, 2.45), 0.14, 0.14)
    lt = math.atan2(0.5, 2.0)
    for k in range(9):
        yy = -2.4 + k * 0.6
        P.beam("timber", (sx0 - 0.05, yy, 2.55), (sx0 + 2.35, yy, 1.95), 0.07, 0.11)
    # lean-to roof of overlapping boards
    nboards = 26
    for k in range(nboards):
        yy = -2.55 + k * 0.2
        P.beam("plank", (sx0 - 0.05, yy, 2.62 + (0.015 if k % 2 else 0.0)), (sx0 + 2.5, yy, 1.98 + (0.015 if k % 2 else 0.0)), 0.22, 0.025, jitter=0.01)
    # firewood stack under the lean-to
    for row in range(7):
        zz = 0.12 + row * 0.15
        for k in range(26):
            yy = -2.1 + k * 0.165 + (0.08 if row % 2 else 0.0)
            if yy > 2.1:
                continue
            xx = sx0 + 0.25 + rng.uniform(-0.02, 0.02)
            r = rng.uniform(0.055, 0.08)
            P.log("logs", (xx, yy, zz + r), (xx + rng.uniform(0.38, 0.48), yy + rng.normal(0, 0.01), zz + r + rng.normal(0, 0.01)), r, split=rng.randint(0, 3))
            P.log("logs", (xx + 0.5, yy, zz + r), (xx + 0.5 + rng.uniform(0.38, 0.48), yy, zz + r), r, split=rng.randint(0, 3))
    parent = _place_parent("cottage_c", col, x, y, z, rot)
    P.build("cottage_c", col, mats, bevel=BEVEL, subsurf=SUBS, parent=parent)
    return parent, dict(z=z, ridge=zr)


def board_wall(P, wall, s0, s1, z0, z1, d, rng, missing=0.03, battens=True, key="plank", wmin=0.17, wmax=0.3):
    """Vertical boards on the outside face (depth d) of a wall section, with battens over the joints."""
    s = s0
    while s < s1 - 0.02:
        w = min(rng.uniform(wmin, wmax), s1 - s)
        if rng.uniform() > missing:
            top = z1 - (rng.uniform(0, 0.05) if rng.uniform() < 0.2 else 0.0)
            bot = z0 + (rng.uniform(0.0, 0.12) if rng.uniform() < 0.25 else 0.0)
            wall.box(P, key, s + 0.004, s + w - 0.004, bot, top, d, d + 0.024, jitter=0.004)
        if battens and s > s0 + 0.01:
            wall.box(P, key, s - 0.03, s + 0.03, z0 + 0.02, z1 - 0.02, d + 0.024, d + 0.044, jitter=0.003)
        s += w


def stable(col, mats):
    """An empty stable: timber frame on stone pads, boarded walls, three open stalls with half doors,
    a closed tack room, hay racks and mangers, straw on the floor, shingle roof with visible rafters."""
    (x, y, z), rot, b = site("stable")
    P = Parts(seed=55)
    rng = P.rng
    X0, X1, Y0, Y1 = -5.4, 5.4, -3.2, 3.2
    zp, zt = 0.12, 2.8
    bx = [-5.4, -2.7, 0.0, 2.7, 5.4]
    # stone pads and posts
    for px in bx:
        for py in (Y0, Y1):
            P.box("stone", (px + rng.normal(0, 0.02), py + rng.normal(0, 0.02), -0.06), (0.5, 0.5, 0.36), (0, 0, rng.uniform(0, 0.4)), jitter=0.03)
            P.box("timber", (px, py, (zp + zt) / 2), (0.22, 0.22, zt - zp), jitter=0.006)
    for px in (X0, X1):
        P.box("stone", (px, 0.0, -0.06), (0.5, 0.5, 0.36), (0, 0, 0.3), jitter=0.03)
        P.box("timber", (px, 0.0, (zp + zt) / 2), (0.22, 0.22, zt - zp), jitter=0.006)
    # low rubble footing under the back and side walls, and sole plates
    back = Wall((X1, Y1), (X0, Y1), (0, 1))
    west = Wall((X0, Y1), (X0, Y0), (-1, 0))
    east = Wall((X1, Y0), (X1, Y1), (1, 0))
    front = Wall((X0, Y0), (X1, Y0), (0, -1))
    for w in (back, west, east):
        stone_wall(P, w, -0.4, 0.1, 0.3, rng=rng, course=(0.12, 0.2), slen=(0.2, 0.42), ext=(0.15, 0.15), depth=0.16)
        w.box(P, "timber", -0.1, w.L + 0.1, 0.1, 0.28, -0.1, 0.1, jitter=0.004)
        for rz in (1.0, 1.9):
            w.box(P, "timber", 0.1, w.L - 0.1, rz - 0.07, rz + 0.07, -0.08, 0.06, jitter=0.004)
    # wall plates and tie beams
    for py in (Y0, Y1):
        P.beam("timber", (X0 - 0.35, py, zt + 0.1), (X1 + 0.35, py, zt + 0.1), 0.24, 0.22)
    for px in bx:
        # tie beams sit on the wall plates and stop short of the roof slope
        P.beam("timber", (px, Y0 - 0.02, zt + 0.22), (px, Y1 + 0.02, zt + 0.22), 0.2, 0.22)
    for px in (X0, X1):
        P.beam("timber", (px, Y0, zt + 0.1), (px, Y1, zt + 0.1), 0.22, 0.22)
    # boarded walls (outer face)
    # pass 2b: a small unglazed window high in the back wall of each stall, and more boards missing, so real
    # daylight comes into the stalls from behind (pass 1 lit them with a hidden fill light; pass 2a left them black)
    wins = sorted((X1 - (bx[i] + bx[i + 1]) / 2 - 0.4, X1 - (bx[i] + bx[i + 1]) / 2 + 0.4) for i in range(3))
    zw0, zw1 = 2.04, 2.6
    s_at = 0.0
    for (wa, wb) in wins:
        board_wall(P, back, s_at, wa, 0.15, zt, 0.11, rng, missing=0.12)
        board_wall(P, back, wa, wb, 0.15, zw0, 0.11, rng, missing=0.0, battens=False)
        board_wall(P, back, wa, wb, zw1, zt, 0.11, rng, missing=0.0, battens=False)
        back.box(P, "timber", wa - 0.07, wb + 0.07, zw0 - 0.08, zw0, 0.06, 0.17, jitter=0.004)
        back.box(P, "timber", wa - 0.07, wb + 0.07, zw1, zw1 + 0.08, 0.06, 0.17, jitter=0.004)
        back.box(P, "timber", wa - 0.07, wa, zw0, zw1, 0.06, 0.165, jitter=0.003)
        back.box(P, "timber", wb, wb + 0.07, zw0, zw1, 0.06, 0.165, jitter=0.003)
        s_at = wb
    board_wall(P, back, s_at, back.L, 0.15, zt, 0.11, rng, missing=0.12)
    # limewashed lining inside the stalls' back wall (stables were limewashed), with the windows left open
    s_at = X1 - bx[3] + 0.12
    for (wa, wb) in wins:
        if wa > s_at:
            board_wall(P, back, s_at, wa, 0.15, zt - 0.02, -0.14, rng, missing=0.04, battens=False, key="lime", wmin=0.2, wmax=0.32)
        board_wall(P, back, wa, wb, 0.15, zw0, -0.14, rng, missing=0.0, battens=False, key="lime", wmin=0.2, wmax=0.32)
        board_wall(P, back, wa, wb, zw1, zt - 0.02, -0.14, rng, missing=0.0, battens=False, key="lime", wmin=0.2, wmax=0.32)
        s_at = wb
    board_wall(P, back, s_at, X1 - X0 - 0.12, 0.15, zt - 0.02, -0.14, rng, missing=0.04, battens=False, key="lime", wmin=0.2, wmax=0.32)
    board_wall(P, west, 0.0, west.L, 0.15, zt, 0.11, rng)
    board_wall(P, east, 0.0, east.L, 0.15, zt, 0.11, rng)
    # gable triangles: boards up to the roof line
    pitch = 40.0
    tn = math.tan(math.radians(pitch))
    for wl, sx in ((west, -1), (east, 1)):
        s = 0.0
        while s < wl.L - 0.02:
            w = min(rng.uniform(0.18, 0.3), wl.L - s)
            ya = (Y1 - s) if sx < 0 else (Y0 + s)
            yb = (Y1 - s - w) if sx < 0 else (Y0 + s + w)
            ha = zt + 0.24 + (3.3 - abs(ya)) * tn
            hb = zt + 0.24 + (3.3 - abs(yb)) * tn
            if (ya > 0) != (yb > 0):
                # board straddles the ridge: split it
                sm = s + abs(ya)
                hm = zt + 0.24 + 3.3 * tn
                wl.board(P, "plank", s + 0.004, sm, zt + 0.15, ha, hm, 0.11, 0.135)
                wl.board(P, "plank", sm, s + w - 0.004, zt + 0.15, hm, hb, 0.11, 0.135)
            else:
                wl.board(P, "plank", s + 0.004, s + w - 0.004, zt + 0.15, ha, hb, 0.11, 0.135)
            s += w
    # loft door and hoist beam on the east gable
    east.box(P, "plank_dark", 2.6, 3.8, zt + 0.55, zt + 1.6, 0.14, 0.17)
    east.box(P, "interior", 2.75, 3.65, zt + 0.65, zt + 1.5, 0.15, 0.175)
    P.beam("timber", (X1 - 0.5, 0.0, zt + 2.05), (X1 + 0.9, 0.0, zt + 2.05), 0.16, 0.18)
    P.cyl("iron", (X1 + 0.75, -0.06, zt + 1.86), (X1 + 0.75, 0.06, zt + 1.86), 0.08, sides=12)
    P.tube("rope", [(X1 + 0.83, 0.0, zt + 1.86), (X1 + 0.85, 0.02, zt + 0.9), (X1 + 0.8, 0.05, 0.6)], [0.012] * 3, sides=6)
    # front: three stalls with half doors, a tack room in the east bay
    for i in range(4):
        sa, sb = bx[i] - X0 + 0.11, bx[i + 1] - X0 - 0.11
        if i < 3:
            # low boarded front either side of a half door
            front.box(P, "timber", sa, sb, zt - 0.2, zt - 0.05, -0.1, 0.1)
            dw = 1.2
            dc = (sa + sb) / 2
            board_wall(P, front, sa, dc - dw / 2, 0.15, 1.3, 0.1, rng, battens=False)
            board_wall(P, front, dc + dw / 2, sb, 0.15, 1.3, 0.1, rng, battens=False)
            front.box(P, "timber", sa, sb, 1.27, 1.37, 0.05, 0.16)
            front.box(P, "timber", dc - dw / 2 - 0.08, dc - dw / 2, 0.12, 2.6, -0.06, 0.08)
            front.box(P, "timber", dc + dw / 2, dc + dw / 2 + 0.08, 0.12, 2.6, -0.06, 0.08)
            ang = [0.0, 95.0, 35.0][i]
            plank_door(P, front, dc - dw / 2 + 0.01, dc + dw / 2 - 0.01, 0.16, 1.32, 0.12, open_deg=-ang if i != 1 else -ang, hinge_left=(i != 2), key="plank")
        else:
            board_wall(P, front, sa, sb, 0.15, zt, 0.11, rng)
            front.box(P, "interior", sa + 0.6, sa + 1.4, 0.18, 1.95, 0.08, 0.1)
            plank_door(P, front, sa + 0.6, sa + 1.4, 0.18, 1.95, 0.14, open_deg=0.0, hinge_left=True, key="plank_dark")
            front.box(P, "timber", sa + 0.5, sa + 1.5, 1.95, 2.05, 0.1, 0.17)
    # tack room inner wall
    inner = Wall((bx[3], Y1), (bx[3], Y0), (-1, 0))
    board_wall(P, inner, 0.1, inner.L - 0.1, 0.1, zt, -0.02, rng, battens=False, missing=0.0)
    # stall partitions (from the back wall to y=-0.2), mangers and hay racks
    for px in bx[1:3]:
        part = Wall((px, Y1 - 0.12), (px, -0.2), (1, 0))
        for k in range(8):
            zz = 0.12 + k * 0.18
            part.box(P, "lime", 0.0, part.L, zz, zz + 0.165, -0.02, 0.02, jitter=0.004)
        P.box("timber", (px, -0.2, 1.1), (0.16, 0.16, 2.2), jitter=0.01)
        P.beam("timber", (px, -0.2, 2.1), (px, Y1 - 0.12, 2.6), 0.12, 0.14)
        P.box("timber", (px, (Y1 - 0.12 - 0.2) / 2 - 0.1, 1.62), (0.12, part.L, 0.12))
    for i in range(3):
        cx = (bx[i] + bx[i + 1]) / 2
        # manger trough
        P.box("plank", (cx, Y1 - 0.42, 0.95), (1.9, 0.05, 0.36))
        P.box("plank", (cx, Y1 - 0.28, 0.79), (1.9, 0.32, 0.04))
        for ex in (-0.95, 0.95):
            P.box("plank", (cx + ex, Y1 - 0.3, 0.92), (0.04, 0.34, 0.3))
        # slanted hay rack of round bars
        for k in range(16):
            xx = cx - 0.9 + k * 0.12
            P.cyl("fresh", (xx, Y1 - 0.12, 1.25), (xx, Y1 - 0.55, 1.95), 0.016, sides=6)
        P.beam("timber", (cx - 1.0, Y1 - 0.55, 1.97), (cx + 1.0, Y1 - 0.55, 1.97), 0.08, 0.08)
        P.beam("timber", (cx - 1.0, Y1 - 0.12, 1.23), (cx + 1.0, Y1 - 0.12, 1.23), 0.08, 0.08)
        # tie ring on the post
        P.cyl("iron", (cx + 0.6, Y1 - 0.14, 1.35), (cx + 0.6, Y1 - 0.2, 1.35), 0.04, sides=10)
    # floor: packed earth with a straw layer in the stalls
    P.box("floor", (0, 0, 0.0), (10.6, 6.2, 0.1))
    for i in range(3):
        cx = (bx[i] + bx[i + 1]) / 2
        P.box("straw", (cx, 1.55, 0.06), (2.5, 3.1, 0.06), jitter=0.01)
    # roof: shingles over rafters and battens (visible from inside)
    zr, ze, _ = shingle_gable_roof(P, X1 - X0 + 0.25, Y1 - Y0 + 0.25, zt + 0.22, pitch, 0.45, 0.4, rng, rafters=True, battens=True)
    # a sagging old ridge
    Lh = (X1 - X0) / 2 + 0.6

    def sag(v):
        f = np.clip((v[:, 2] - (zt + 0.2)) / max(zr - zt - 0.2, 0.1), 0, 1)
        v[:, 2] -= 0.08 * (1 - (v[:, 0] / Lh) ** 2) * f
        return v
    P.deform(list(P.mb.keys()), sag)
    parent = _place_parent("stable", col, x, y, z, rot)
    P.build("stable", col, mats, bevel=BEVEL, subsurf=SUBS, parent=parent)
    # loose straw strands on the stall floors, hay in the racks
    st = Strands()
    from bparts import straw_colour
    for i in range(3):
        cx = (bx[i] + bx[i + 1]) / 2
        for k in range(1400):
            p = (cx + rng.uniform(-1.3, 1.3), rng.uniform(-0.1, 3.0), 0.09 + rng.uniform(0, 0.03))
            a = rng.uniform(0, 2 * math.pi)
            st.add(p, (math.cos(a), math.sin(a), rng.uniform(-0.1, 0.15)), rng.uniform(0.08, 0.3), rng.uniform(0.003, 0.006), straw_colour(rng, 0.25), segs=1)
        for k in range(260):
            p = (cx + rng.uniform(-0.85, 0.85), Y1 - rng.uniform(0.2, 0.45), rng.uniform(1.3, 1.85))
            a = rng.uniform(0, 2 * math.pi)
            st.add(p, (math.cos(a) * 0.4, math.sin(a) * 0.4, -1.0), rng.uniform(0.1, 0.35), rng.uniform(0.003, 0.006), straw_colour(rng, 0.15), segs=2)
    # straw spilling out of the open stall door
    for k in range(500):
        p = (bx[1] + 1.35 + rng.normal(0, 0.5), Y0 - rng.uniform(-0.3, 1.2), 0.03)
        a = rng.uniform(0, 2 * math.pi)
        st.add(p, (math.cos(a), math.sin(a), 0.0), rng.uniform(0.08, 0.25), rng.uniform(0.003, 0.005), straw_colour(rng, 0.5), segs=1)
    st.build("stable_straw", col, mats["strands"], parent=parent)
    # pass 2: no hidden fill light; the low morning sun shines in under the eaves and through the gaps
    if True:
        return parent, dict(z=z, ridge=zr)
    ld = bpy.data.lights.get("stable_fill") or bpy.data.lights.new("stable_fill", 'AREA')
    ld.shape = 'RECTANGLE'
    ld.size = 7.6
    ld.size_y = 3.2
    ld.energy = 170.0
    ld.color = (1.0, 0.86, 0.68)
    lo = bpy.data.objects.new("stable_fill", ld)
    col.objects.link(lo)
    lo.parent = parent
    lo.location = (-1.3, 1.2, 2.55)
    lo.visible_camera = False
    lo.visible_glossy = False
    return parent, dict(z=z, ridge=zr)
