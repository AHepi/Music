"""
tea_urn: a tea room's brass tea urn of about 1910 on its cast-iron stand. A turned brass body with raised bands, two
loop handles at the sides, a domed lid with a finial, a water-gauge glass, and a tap at the front (-Y): a boss and
nut, a short pipe, the valve with its turned-down spout and a T-shaped key with black grips. The body sits in a ring
on four curved iron legs over a small brass spirit burner; the legs stand on a moulded iron base on bun feet, and the
base runs forward under the tap to carry a brass drip tray.

Options: none.

Where it came from: "44 control builder - render_final.py" (procedural-textures/44 Blind test - a tea house), the
counter's urn (line 881): a lathed brass body 1.25 m high with handles, tap and gauge, standing on the counter; rebuilt
here at a real size (0.83 m), on a stand of its own with a burner and drip tray.
"""

import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import _shapes_town as shapes  # noqa: E402

BRASS = 'MADE • old brass'
IRON = 'IRON • soot-black lamp posts'

CARD = {
    'name': 'tea_urn',
    'what': 'a brass tea urn on its cast-iron stand, burner under it, tap and T-key at the front (-Y), drip tray',
    'size_m': (0.49, 0.52, 0.83),
    'options': {},
    'materials': [BRASS, IRON, 'PART • tea_urn: gauge glass'],
    'source': '"44 control builder - render_final.py", the counter urn (line 881); builder\'s report "44 Control builder\'s report.md"',
    'views': 'reads from every side',
    'trap': 'a brass urn in a dark room disappears without a light of its own on it (see Traps.md); the part brings none',
}

BODY = [
    (0.000, 0.196), (0.080, 0.196), (0.088, 0.204), (0.086, 0.214), (0.098, 0.226), (0.128, 0.246), (0.155, 0.272),
    (0.172, 0.305), (0.180, 0.345), (0.181, 0.390), (0.176, 0.440), (0.165, 0.490), (0.150, 0.540), (0.136, 0.580),
    (0.141, 0.588), (0.141, 0.598), (0.128, 0.606), (0.120, 0.628), (0.120, 0.652), (0.132, 0.658), (0.132, 0.668),
    (0.000, 0.668),
]
LID = [
    (0.000, 0.666), (0.135, 0.666), (0.137, 0.674), (0.126, 0.690), (0.104, 0.716), (0.074, 0.740), (0.042, 0.756),
    (0.026, 0.762), (0.022, 0.774), (0.034, 0.788), (0.036, 0.806), (0.026, 0.822), (0.010, 0.832), (0.000, 0.834),
]


def body_radius(z):
    for (r0, z0), (r1, z1) in zip(BODY[:-1], BODY[1:]):
        if z0 <= z <= z1 and z1 > z0:
            return r0 + (r1 - r0) * (z - z0) / (z1 - z0)
    return 0.15


def _gauge_glass(m, nodes, links, principled):
    principled.inputs['Base Color'].default_value = (0.05, 0.045, 0.035, 1.0)
    principled.inputs['Roughness'].default_value = 0.08
    principled.inputs['Transmission Weight'].default_value = 0.6
    principled.inputs['IOR'].default_value = 1.5
    m.diffuse_color = (0.05, 0.045, 0.035, 1.0)


def build(collection, seed=0):
    rng = shapes.rng_for('tea_urn', seed)
    objects = []

    # ------------------------------------------------------------------ the stand: base, feet, legs, ring (cast iron)
    stand = shapes.Shape()
    yc = -0.08
    stand.box((0.0, yc, 0.040), (0.340, 0.500, 0.022))
    stand.box((0.0, yc, 0.056), (0.316, 0.476, 0.012))
    stand.box((0.0, yc, 0.0645), (0.300, 0.460, 0.006))
    for sx in (-1, 1):
        for sy in (-0.305 + 0.0, 0.145):
            stand.lathe([(0.0, 0.0), (0.018, 0.001), (0.028, 0.012), (0.026, 0.024), (0.018, 0.030), (0.0, 0.031)], segments=14,
                        matrix=Matrix.Translation((sx * 0.140, sy, 0.0)))
    ring_z = 0.198
    stand.torus((0.0, 0.0, ring_z), 0.100, 0.011, segments=40, sides=8)
    stand.torus((0.0, 0.0, ring_z - 0.016), 0.094, 0.007, segments=40, sides=6)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        c, s = math.cos(a), math.sin(a)
        pts = []
        for j in range(13):
            t = j / 12
            r = 0.135 - 0.04 * t + 0.035 * math.sin(math.pi * t) * (1 - t)
            z = 0.066 + (ring_z - 0.066) * t
            pts.append((r * c, r * s, z))
        stand.sweep(pts, 0.009, sides=8, radii=[0.011 - 0.004 * (j / 12) for j in range(13)])
        # a small curl at each leg's foot
        curl = []
        for j in range(9):
            t = j / 8
            ang = math.pi * 1.4 * t
            rr = 0.022 * (1 - 0.5 * t)
            curl.append(((0.135 + rr * math.cos(ang)) * c, (0.135 + rr * math.cos(ang)) * s, 0.078 + rr * math.sin(ang)))
        stand.sweep(curl, 0.0055, sides=6)
    objects.append(stand.finish('tea_urn stand', collection, IRON, smooth=True, sharp=40))

    # ------------------------------------------------------------------ brass: burner, body, bands, lid, handles, tap, tray
    turn = math.radians(rng.uniform(-6, 6))
    brass = shapes.Shape()
    brass.lathe([(0.0, 0.068), (0.048, 0.068), (0.052, 0.074), (0.050, 0.112), (0.040, 0.118), (0.014, 0.120),
                 (0.012, 0.132), (0.0, 0.133)], segments=24)
    objects.append(brass.finish('tea_urn burner', collection, BRASS, smooth=True, sharp=45))

    body = shapes.Shape()
    body.lathe(BODY, segments=48)
    for z in (0.330, 0.515):
        body.torus((0.0, 0.0, z), body_radius(z) + 0.001, 0.0045, segments=48, sides=6)
    for sx in (-1, 1):
        # loop handles with round bosses where they meet the body
        top_z, low_z = 0.548, 0.430
        rt, rl = body_radius(top_z), body_radius(low_z)
        pts = shapes.smooth_path([(sx * (rt - 0.004), 0.0, top_z), (sx * (rt + 0.040), 0.0, top_z + 0.012),
                                  (sx * (rt + 0.074), 0.0, top_z - 0.010), (sx * (rt + 0.084), 0.0, top_z - 0.050),
                                  (sx * (rl + 0.058), 0.0, low_z + 0.022), (sx * (rl + 0.024), 0.0, low_z + 0.002),
                                  (sx * (rl - 0.004), 0.0, low_z)], steps=6)
        body.sweep(pts, 0.0105, sides=10)
        for (z, r) in ((top_z, rt), (low_z, rl)):
            body.cylinder((sx * (r - 0.004), 0.0, z), (sx * (r + 0.010), 0.0, z), 0.020, 0.016, segments=14)
    # the tap: boss, nut, pipe, valve, spout and key stem
    tz = 0.270
    r = body_radius(tz)
    body.cylinder((0.0, -(r - 0.006), tz), (0.0, -(r + 0.016), tz), 0.026, 0.022, segments=16)
    body.cylinder((0.0, -(r + 0.016), tz), (0.0, -(r + 0.030), tz), 0.024, segments=6)
    body.cylinder((0.0, -(r + 0.030), tz), (0.0, -0.245, tz), 0.0135, segments=14)
    vy = -0.252
    body.lathe([(0.0, 0.247), (0.017, 0.247), (0.021, 0.255), (0.021, 0.290), (0.017, 0.298), (0.010, 0.302),
                (0.010, 0.318), (0.0, 0.318)], segments=16, matrix=Matrix.Translation((0.0, vy, 0.0)))
    spout = [(0.0, vy, 0.250), (0.0, vy - 0.006, 0.236), (0.0, vy - 0.016, 0.224), (0.0, vy - 0.020, 0.214)]
    body.sweep(spout, 0.011, sides=12, radii=[0.0115, 0.0105, 0.0095, 0.009])
    # the water gauge: a glass in a brass guard, to the front right
    ga = math.radians(-55)
    gx, gy = math.cos(ga), math.sin(ga)
    gr = 0.212                          # the gauge stands this far from the urn's middle
    for (z, label) in ((0.312, 'low'), (0.522, 'high')):
        rr = body_radius(z)
        body.cylinder((gx * (rr - 0.004), gy * (rr - 0.004), z), (gx * gr, gy * gr, z), 0.007, segments=8)
        body.cylinder((gx * gr, gy * gr, z - 0.012 if label == 'low' else z + 0.012),
                      (gx * gr, gy * gr, z + 0.012 if label == 'low' else z - 0.012), 0.011, segments=10)
    for da in (-0.045, 0.045):
        px, py = math.cos(ga + da) * (gr + 0.004), math.sin(ga + da) * (gr + 0.004)
        body.cylinder((px, py, 0.324), (px, py, 0.510), 0.0028, segments=6)
    body_obj = body.finish('tea_urn body', collection, BRASS, smooth=True, sharp=48)
    objects.append(body_obj)

    lid = shapes.Shape()
    lid.lathe(LID, segments=48)
    objects.append(lid.finish('tea_urn lid', collection, BRASS, smooth=True, sharp=48))

    glass = shapes.Shape()
    glass.cylinder((gx * 0.212, gy * 0.212, 0.324), (gx * 0.212, gy * 0.212, 0.510), 0.0065, segments=10)
    gauge_obj = glass.finish('tea_urn gauge glass', collection, shapes.part_material('tea_urn', 'gauge glass', _gauge_glass), smooth=True)
    objects.append(gauge_obj)

    # the key: a stem and a cross bar with black grips
    key = shapes.Shape()
    key.cylinder((0.0, vy, 0.318), (0.0, vy, 0.334), 0.006, segments=8)
    key.cylinder((-0.022, vy, 0.338), (0.022, vy, 0.338), 0.0055, segments=8)
    key_obj = key.finish('tea_urn key', collection, BRASS, smooth=True, sharp=45)
    objects.append(key_obj)
    grips = shapes.Shape()
    for sx in (-1, 1):
        grips.lathe([(0.0, 0.0), (0.0075, 0.002), (0.0085, 0.016), (0.0065, 0.026), (0.0, 0.028)], segments=10,
                    matrix=shapes.to4(shapes.frame_along((sx, 0.0, 0.0)), (sx * 0.020, vy, 0.338)))
    grips_obj = grips.finish('tea_urn key grips', collection, IRON, smooth=True)
    objects.append(grips_obj)

    # drip tray on the base under the spout
    tray = shapes.Shape()
    tray_y, tray_z = -0.262, 0.0675
    tray.box((0.0, tray_y, tray_z + 0.002), (0.130, 0.100, 0.004))
    for (cx, cy, sx_, sy_) in ((0.0, tray_y - 0.048, 0.130, 0.004), (0.0, tray_y + 0.048, 0.130, 0.004),
                               (-0.063, tray_y, 0.004, 0.100), (0.063, tray_y, 0.004, 0.100)):
        tray.box((cx, cy, tray_z + 0.009), (sx_, sy_, 0.018))
    # a pierced grille resting inside
    for k in range(6):
        x = -0.045 + 0.018 * k
        tray.box((x, tray_y, tray_z + 0.013), (0.008, 0.088, 0.002))
    tray.box((0.0, tray_y, tray_z + 0.0115), (0.12, 0.004, 0.003))
    objects.append(tray.finish('tea_urn drip tray', collection, BRASS, smooth=False))

    # seeded: the urn sits a touch turned in its ring
    shapes.tilt_all([o for o in objects if o.name.startswith(('tea_urn body', 'tea_urn lid', 'tea_urn gauge', 'tea_urn key'))], rz=turn)
    return objects
