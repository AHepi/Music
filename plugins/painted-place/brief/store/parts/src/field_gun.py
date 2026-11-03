"""
field_gun: a 1914-18 British 18-pounder field gun, as it stands in a muddy camp: two dished wooden wheels of
12 spokes with iron tyres (1.42 m across), the axle and axle tree, a riveted steel shield in three parts with a
sight hole and a hanging apron below, the barrel with its long spring case above and the cradle below, the breech
ring and lever, a box trail running back to the spade and trail eye, crew seats, handwheels, the sight. Olive paint
gone to rust at the edges and rivets (rust runs below them), mud thrown up the wheels and trail, lumps of mud where
the wheels and spade sit.

Options:
  elevation   the barrel's raise in degrees (default 3)
  seed        small differences: rust runs, mud lumps

About 2.0 m wide (hub to hub), 5.3 m long, 1.8 m high. The muzzle points to -Y. Foot at z = 0, centred on the origin.

Made for the store from `field_gun` (line 566) and `spoked_wheel` (line 551) in '46 military-base - render_final.py'
and `gun` in '50 second pass - render_final.py' (line 758) with its mud and rust (wheel mud, rivets with rust runs,
olive paint rusting); rebuilt at the 18-pounder's real size from the board's photographs (08: the wheels, shield,
breech, trail and spade).
"""

import math
import os
import sys

if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import _shapes_camp as sh  # noqa: E402

CARD = {
    'name': 'field_gun',
    'what': 'a 1914-18 18-pounder field gun: spoked wheels with iron tyres, shield, barrel and breech, box trail and spade',
    'size_m': (1.99, 5.28, 1.82),
    'options': {
        'elevation': "the barrel's raise in degrees (default 3)",
        'seed': 'rust runs and mud lumps (default 0)',
    },
    'materials': ['PART • field_gun: olive paint on steel, rust showing', 'PART • field_gun: olive paint on wood',
                  'SURFACE • rusty_metal_02 (field_gun)', 'IRON • soot-black lamp posts', 'RUST • rain-aged iron',
                  'SURFACE • mud_forest', 'RECESSES • near-black blue'],
    'source': "`field_gun` (line 566) and `spoked_wheel` (line 551) in '46 military-base - render_final.py'; `gun` in "
              "'50 second pass - render_final.py' (line 758) with its mud and rust; the board's photograph 08",
    'views': 'reads from every side',
    'trap': 'Its origin is the middle of its length, not the axle: the axle is 0.76 m in front of the origin (-Y).',
}

PART = 'field_gun'
R = 0.71             # wheel radius
X_WHEEL = 0.79       # the wheels' middle planes
OY = -0.76           # the axle's y (so the gun's length is centred on the origin)


def build(collection, seed=0, elevation=3.0, **_ignored):
    rnd = sh.rand(seed, PART)
    paint = sh.painted_surface(PART, 'olive paint on steel, rust showing', 'SURFACE • rusty_metal_02', (0.044, 0.053, 0.042),
                               grain=0.22, rust=0.65, mud_height=0.45, edge_wear=0.4, grime=0.6)
    paint_wood = sh.painted_surface(PART, 'olive paint on wood', 'SURFACE • rough_wood', (0.046, 0.054, 0.042),
                                    grain=0.45, mud_height=0.7, edge_wear=0.6, grime=0.6)
    tyre_iron = sh.copy_surface('SURFACE • rusty_metal_02', PART, darken=0.26, mud_height=0.55, edge_wear=0.8)

    steel = sh.Builder('field_gun carriage, shield and barrel', paint)
    wood = sh.Builder('field_gun wheels', paint_wood)
    tyres = sh.Builder('field_gun tyres', tyre_iron)
    iron = sh.Builder('field_gun breech and ironwork', 'IRON • soot-black lamp posts')
    rust = sh.Builder('field_gun rust runs', 'RUST • rain-aged iron')
    dark = sh.Builder('field_gun bore', 'RECESSES • near-black blue')
    mud = sh.Builder('field_gun mud', 'SURFACE • mud_forest', smooth=True)

    def Y(y_rel):
        return OY + y_rel

    # ---------------------------------------------------------------- wheels
    for side in (-1, 1):
        xw = side * X_WHEEL
        c = Vector((xw, Y(0.0), R))
        sh.ring_band(tyres.bm, c, (1, 0, 0), R - 0.021, R, 0.076, segments=72)
        sh.ring_band(wood.bm, c + Vector((0, 0, 0)), (1, 0, 0), 0.60, R - 0.021, 0.064, segments=72)
        hub_in, hub_out = xw - side * 0.17, xw + side * 0.1
        sh.cylinder(wood.bm, (hub_in, Y(0), R), (hub_out, Y(0), R), 0.12, segments=16)
        for xb in (hub_in + side * 0.02, hub_out - side * 0.02):
            sh.ring_band(iron.bm, (xb, Y(0), R), (1, 0, 0), 0.117, 0.13, 0.032, segments=24)
        sh.cylinder(iron.bm, (hub_out, Y(0), R), (hub_out + side * 0.07, Y(0), R), 0.082, 0.07, segments=16)
        sh.cylinder(iron.bm, (hub_out + side * 0.07, Y(0), R), (hub_out + side * 0.1, Y(0), R), 0.04, segments=6)
        spoke_x0 = xw - side * 0.06
        for k in range(12):
            a = 2 * math.pi * k / 12 + 0.13
            d = Vector((0.0, math.cos(a), math.sin(a)))
            p0 = Vector((spoke_x0, Y(0), R)) + d * 0.11
            p1 = Vector((xw, Y(0), R)) + d * 0.61
            sh.tapered_beam(wood.bm, p0, p1, 0.047, 0.062, 0.036, 0.05, up=(1, 0, 0))
        # tyre bolts through the felloe
        for k in range(12):
            a = 2 * math.pi * (k + 0.5) / 12 + 0.13
            d = Vector((0.0, math.cos(a), math.sin(a)))
            p = Vector((xw, Y(0), R)) + d * 0.645
            sh.cylinder(iron.bm, p - Vector((0.04, 0, 0)), p + Vector((0.04, 0, 0)), 0.011, segments=6)
    sh.cylinder(iron.bm, (-X_WHEEL - 0.12, Y(0), R), (X_WHEEL + 0.12, Y(0), R), 0.045, segments=12)
    sh.box(steel.bm, (-0.64, Y(-0.075), R - 0.075), (0.64, Y(0.075), R + 0.07))

    # ---------------------------------------------------------------- trail: two girders converging to the spade
    def girder(side):
        f0 = (side * 0.245, Y(0.05), 0.58, 0.88)
        f1 = (side * 0.125, Y(3.0), 0.07, 0.25)
        t = 0.014
        x0a, x0b = f0[0], f0[0] - side * t
        x1a, x1b = f1[0], f1[0] - side * t
        pts = [(x0a, f0[1], f0[2]), (x0b, f0[1], f0[2]), (x0b, f0[1], f0[3]), (x0a, f0[1], f0[3]),
               (x1a, f1[1], f1[2]), (x1b, f1[1], f1[2]), (x1b, f1[1], f1[3]), (x1a, f1[1], f1[3])]
        sh.hexahedron(steel.bm, pts)
        for za, zb in ((f0[2], f1[2]), (f0[3], f1[3])):     # flanges along the bottom and top
            off = 0.0 if za == f0[2] else -0.012
            pts = [(x0a, f0[1], za + off), (x0a - side * 0.07, f0[1], za + off), (x0a - side * 0.07, f0[1], za + off + 0.012), (x0a, f0[1], za + off + 0.012),
                   (x1a, f1[1], zb + off), (x1a - side * 0.06, f1[1], zb + off), (x1a - side * 0.06, f1[1], zb + off + 0.012), (x1a, f1[1], zb + off + 0.012)]
            sh.hexahedron(steel.bm, pts)

    for side in (-1, 1):
        girder(side)

    def trail_at(y_rel):
        f = (y_rel - 0.05) / 2.95
        return (0.245 + (0.125 - 0.245) * f, 0.58 + (0.07 - 0.58) * f, 0.88 + (0.25 - 0.88) * f)

    for y_rel in (0.95, 1.75, 2.45):
        half, zb, zt = trail_at(y_rel)
        sh.box(steel.bm, (-half + 0.012, Y(y_rel - 0.006), zb + 0.015), (half - 0.012, Y(y_rel + 0.006), zt - 0.015))
    # top plate over the back half of the trail
    h0, zb0, zt0 = trail_at(1.9)
    h1, zb1, zt1 = trail_at(3.0)
    sh.hexahedron(steel.bm, [(-h0, Y(1.9), zt0), (h0, Y(1.9), zt0), (h0, Y(1.9), zt0 + 0.01), (-h0, Y(1.9), zt0 + 0.01),
                             (-h1, Y(3.0), zt1), (h1, Y(3.0), zt1), (h1, Y(3.0), zt1 + 0.01), (-h1, Y(3.0), zt1 + 0.01)])
    # spade: a slanted blade dug in at the end, with gussets; trail eye and handles above it
    sh.hexahedron(steel.bm, [(-0.29, Y(2.98), 0.31), (0.29, Y(2.98), 0.31), (0.29, Y(2.995), 0.31), (-0.29, Y(2.995), 0.31),
                             (-0.27, Y(3.13), 0.0), (0.27, Y(3.13), 0.0), (0.27, Y(3.145), 0.0), (-0.27, Y(3.145), 0.0)])
    for side in (-1, 1):
        x = side * 0.12
        sh.extrude_polygon(steel.bm, [(2.86, 0.1), (3.0, 0.3), (3.12, 0.04)], (x - 0.006, OY, 0.0), (0, 1, 0), (0, 0, 1), (1, 0, 0), 0.012)
        sh.beam(iron.bm, (side * 0.13, Y(2.72), 0.27), (side * 0.36, Y(2.76), 0.33), 0.03, 0.03)
    sh.torus(iron.bm, (0, Y(3.16), 0.3), (0, 0, 1), 0.065, 0.019, segments=16, sides=6)
    sh.box(iron.bm, (-0.05, Y(3.0), 0.27), (0.05, Y(3.1), 0.33))

    # ---------------------------------------------------------------- saddle, cradle, barrel, spring case, breech
    el = math.radians(float(elevation))
    breech = Vector((0.0, Y(0.62), 1.06))
    direction = Vector((0.0, -math.cos(el), math.sin(el)))
    M = Matrix.Translation(breech) @ sh.frame_matrix(direction, (1, 0, 0)).to_4x4()
    sh.box(steel.bm, (-0.2, Y(-0.16), R + 0.06), (0.2, Y(0.2), 0.86))
    sh.box(steel.bm, (-0.095, -0.255, -0.02), (0.095, -0.1, 1.28), matrix=M)                      # cradle
    sh.cylinder(steel.bm, M @ Vector((-0.17, -0.17, 0.62)), M @ Vector((0.17, -0.17, 0.62)), 0.045, segments=10)   # trunnions
    barrel = [(0.112, 0.0), (0.112, 0.36), (0.098, 0.4), (0.09, 0.9), (0.08, 1.6), (0.071, 2.36), (0.078, 2.4), (0.078, 2.47), (0.072, 2.5)]
    sh.lathe(steel.bm, barrel, segments=20, matrix=M, close_bottom=True, close_top=False)
    sh.lathe(dark.bm, [(0.072, 2.5), (0.042, 2.5), (0.042, 2.3)], segments=20, matrix=M, close_bottom=False, close_top=True)
    spring = [(0.07, 0.12), (0.082, 0.16), (0.082, 1.9), (0.075, 1.96), (0.05, 1.98)]
    sh.lathe(steel.bm, spring, segments=16, centre=(0, 0.19, 0), matrix=M)
    for d in (0.35, 1.05, 1.75):
        sh.ring_band(steel.bm, M @ Vector((0, 0.19, d)), M.to_3x3() @ Vector((0, 0, 1)), 0.08, 0.092, 0.035, segments=16)
    sh.box(steel.bm, (-0.04, 0.0, 0.3), (0.04, 0.13, 0.42), matrix=M)
    sh.box(iron.bm, (-0.135, -0.135, -0.09), (0.135, 0.135, 0.2), matrix=M)                        # breech ring
    sh.box(iron.bm, (-0.1, -0.1, -0.12), (0.1, 0.1, -0.09), matrix=M)                               # breech block face
    sh.beam(iron.bm, M @ Vector((0.135, 0.02, -0.05)), M @ Vector((0.17, -0.22, -0.3)), 0.025, 0.03)    # breech lever
    sh.cylinder(iron.bm, M @ Vector((0.17, -0.22, -0.3)), M @ Vector((0.17, -0.22, -0.36)), 0.022, segments=8)

    # ---------------------------------------------------------------- shield: three plates, apron, rivets and rust runs
    lean = math.radians(7.0)

    def shield_y(z):
        return Y(-0.27) + (z - 0.3) * math.tan(lean)

    def plate(x0, x1, z0, z1, t=0.006, builder=None):
        b = builder or steel
        pts = [(x0, shield_y(z0) - t, z0), (x1, shield_y(z0) - t, z0), (x1, shield_y(z0), z0), (x0, shield_y(z0), z0),
               (x0, shield_y(z1) - t, z1), (x1, shield_y(z1) - t, z1), (x1, shield_y(z1), z1), (x0, shield_y(z1), z1)]
        sh.hexahedron(b.bm, pts)

    plate(-0.86, -0.165, 1.3, 1.82)
    plate(0.165, 0.86, 1.3, 1.82)
    plate(-0.165, 0.165, 1.44, 1.82)
    plate(-0.68, -0.165, 0.8, 1.31)
    plate(0.165, 0.68, 0.8, 1.31)
    plate(-0.6, 0.6, 0.3, 0.64)
    # folded top edge and side stiffeners (behind the plate)
    sh.hexahedron(steel.bm, [(-0.86, shield_y(1.79), 1.79), (0.86, shield_y(1.79), 1.79), (0.86, shield_y(1.79) + 0.04, 1.79), (-0.86, shield_y(1.79) + 0.04, 1.79),
                             (-0.86, shield_y(1.82), 1.82), (0.86, shield_y(1.82), 1.82), (0.86, shield_y(1.82) + 0.04, 1.82), (-0.86, shield_y(1.82) + 0.04, 1.82)])
    for x in (-0.42, 0.42):
        sh.hexahedron(steel.bm, [(x - 0.02, shield_y(0.82), 0.82), (x + 0.02, shield_y(0.82), 0.82), (x + 0.02, shield_y(0.82) + 0.035, 0.82), (x - 0.02, shield_y(0.82) + 0.035, 0.82),
                                 (x - 0.02, shield_y(1.78), 1.78), (x + 0.02, shield_y(1.78), 1.78), (x + 0.02, shield_y(1.78) + 0.035, 1.78), (x - 0.02, shield_y(1.78) + 0.035, 1.78)])
    # the sight hole, shuttered, on the left
    plate(-0.5, -0.38, 1.5, 1.63, t=0.009, builder=dark)
    plate(-0.37, -0.25, 1.49, 1.64, t=0.012)
    # rivets along the plates' edges, rust running down from some
    rivet_rows = [(-0.84, 0.84, 1.79), (-0.84, -0.19, 1.33), (0.19, 0.84, 1.33), (-0.66, -0.19, 0.83), (0.19, 0.66, 0.83), (-0.58, 0.58, 0.61), (-0.58, 0.58, 0.33)]
    for x0, x1, z in rivet_rows:
        n = max(2, int(round((x1 - x0) / 0.11)))
        for k in range(n + 1):
            x = x0 + (x1 - x0) * k / n
            y = shield_y(z) - 0.006
            sh.cylinder(steel.bm, (x, y + 0.002, z), (x, y - 0.007, z), 0.011, 0.008, segments=6)
            if rnd.random() < 0.45:
                h = rnd.uniform(0.05, 0.22)
                w = rnd.uniform(0.008, 0.02)
                z_low = max(z - h, 0.3 if z < 0.7 else 0.8 if z < 1.3 else 1.3)
                sh.hexahedron(rust.bm, [(x - w, shield_y(z_low) - 0.0075, z_low), (x + w, shield_y(z_low) - 0.0075, z_low),
                                        (x + w, shield_y(z_low) - 0.0062, z_low), (x - w, shield_y(z_low) - 0.0062, z_low),
                                        (x - w * 0.6, shield_y(z) - 0.0075, z), (x + w * 0.6, shield_y(z) - 0.0075, z),
                                        (x + w * 0.6, shield_y(z) - 0.0062, z), (x - w * 0.6, shield_y(z) - 0.0062, z)])
    for x in (-0.66, -0.19, 0.19, 0.66):
        for z in (0.88, 1.0, 1.12, 1.24):
            if abs(x) > 0.6 and z > 1.25:
                continue
            sh.cylinder(steel.bm, (x, shield_y(z) - 0.004, z), (x, shield_y(z) - 0.013, z), 0.011, 0.008, segments=6)
    # apron hangers to the axle tree
    for x in (-0.45, 0.45):
        sh.beam(steel.bm, (x, shield_y(0.62) + 0.002, 0.62), (x, Y(-0.07), R - 0.02), 0.03, 0.01)

    # ---------------------------------------------------------------- seats, handwheels, sight
    for side in (-1, 1):
        cx = side * 0.45
        sh.lathe(steel.bm, [(0.002, 0.0), (0.12, 0.012), (0.145, 0.045), (0.14, 0.05), (0.115, 0.02), (0.002, 0.01)], segments=14,
                 centre=(cx, Y(0.34), 0.96))
        sh.beam(steel.bm, (cx, Y(0.3), 0.96), (side * 0.3, Y(0.05), R + 0.05), 0.04, 0.02)
        sh.beam(steel.bm, (cx, Y(0.38), 0.96), (side * 0.4, Y(0.06), R - 0.02), 0.04, 0.02)
        wheel_c = Vector((side * 0.31, Y(0.66), 0.86))
        sh.torus(iron.bm, wheel_c, (1, 0, 0), 0.1, 0.011, segments=20, sides=5)
        for k in range(3):
            a = 2 * math.pi * k / 3
            sh.cylinder(iron.bm, wheel_c, wheel_c + Vector((0, math.cos(a), math.sin(a))) * 0.1, 0.007, segments=4)
        sh.cylinder(iron.bm, wheel_c, wheel_c + Vector((-side * 0.08, 0, 0)), 0.018, segments=8)
        sh.cylinder(iron.bm, wheel_c + Vector((0, 0.09, -0.06)), wheel_c + Vector((side * 0.06, 0.09, -0.06)), 0.009, segments=5)
    sh.box(iron.bm, (-0.27, Y(0.22), 1.3), (-0.2, Y(0.3), 1.42))
    sh.cylinder(iron.bm, (-0.235, Y(0.3), 1.39), (-0.235, Y(0.4), 1.39), 0.02, segments=8)
    sh.cylinder(iron.bm, (-0.235, Y(0.26), 1.42), (-0.235, Y(0.26), 1.46), 0.032, segments=10)

    # ---------------------------------------------------------------- mud where it sits: under the wheels, round the spade
    def lump(c, r, turn=0.0):
        m = Matrix.Translation(c) @ Matrix.Rotation(turn, 4, 'Z') @ Matrix.Diagonal((*r, 1.0))
        made_sphere = bmesh.ops.create_uvsphere(mud.bm, u_segments=12, v_segments=7, radius=1.0, matrix=m)
        for v in made_sphere['verts']:
            v.co.z = max(v.co.z, 0.0)
        flat = [f for f in {f for v in made_sphere['verts'] for f in v.link_faces} if all(v.co.z < 0.0005 for v in f.verts)]
        bmesh.ops.delete(mud.bm, geom=flat, context='FACES')

    for side in (-1, 1):
        xw = side * X_WHEEL
        for dy, sy, sz in ((-0.2, 0.22, 0.055), (0.22, 0.26, 0.06), (0.0, 0.14, 0.035)):
            lump(Vector((xw + rnd.uniform(-0.02, 0.02), Y(dy), 0.0)), (0.075 + rnd.uniform(0, 0.03), sy, sz), rnd.uniform(-0.2, 0.2))
        for k in range(3):
            lump(Vector((xw + rnd.uniform(-0.2, 0.2), Y(rnd.uniform(-0.5, 0.5)), 0.0)), (rnd.uniform(0.03, 0.06),) * 2 + (0.025,), rnd.uniform(0, 3))
    lump(Vector((0.0, Y(3.1), 0.0)), (0.42, 0.24, 0.1), 0.0)
    lump(Vector((0.16, Y(2.92), 0.0)), (0.2, 0.18, 0.07), 0.4)
    lump(Vector((-0.2, Y(3.28), 0.0)), (0.18, 0.12, 0.06), -0.3)
    for k in range(5):
        lump(Vector((rnd.uniform(-0.6, 0.6), Y(rnd.uniform(2.6, 3.5)), 0.0)), (rnd.uniform(0.03, 0.08),) * 2 + (0.03,), rnd.uniform(0, 3))

    made = []
    for builder in (steel, wood, tyres, iron, rust, dark, mud):
        obj = builder.finish(collection)
        if obj is not None:
            made.append(obj)
    return made
