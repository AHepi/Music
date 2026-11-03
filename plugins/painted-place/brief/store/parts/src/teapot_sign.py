"""
teapot_sign: a tea room's hanging shop sign: a wrought-iron bracket out from the wall (a wall plate with three bolts, a
square top bar ending in a curl, a diagonal brace and scrolls between them) and, hanging from two eyes under it on short
chains, a copper teapot about twice life size, cast and beaten whole, its spout towards -Y and its handle towards the
wall. It is a full round teapot, so it reads from -Y and from both sides along X.

The wall is on the +Y side: the back of the wall plate lies on y = 0. The part's origin is the foot of the wall under
the sign (z = 0 is the ground there); place it on your wall's face at ground level.

Options:
    height   metres from the ground to the bracket's top bar (default 3.0); the teapot's bottom hangs about 0.6 m
             lower.

Where it came from: "44 plugin builder - build_tea_house.py" (procedural-textures/44 Blind test - a tea house), the
teapot lantern (line 254): a glowing sphere with box chains on a box bracket; rebuilt here as a forged bracket and a
copper teapot sign.
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

IRON = 'IRON • soot-black lamp posts'
COPPER = 'MADE • old copper'

CARD = {
    'name': 'teapot_sign',
    'what': 'a hanging shop sign: forged iron bracket from a wall (wall side +Y) and a copper teapot on two chains',
    'size_m': (0.40, 1.02, 0.63),
    'options': {
        'height': 'metres from the ground to the bracket\'s top bar (default 3.0); the teapot hangs about 0.6 m lower',
    },
    'materials': [IRON, COPPER],
    'source': '"44 plugin builder - build_tea_house.py", the teapot lantern (line 254); builder\'s report "44 Plugin builder\'s report.md"',
    'views': 'reads from every side; drawn alone it hangs in the air, as it needs a wall behind it',
    'trap': 'the origin is the foot of the wall below the sign, not the sign: the sign itself is 2.4 to 3.1 m up',
    'foot_z': 2.46,     # at the default height: the sign's lowest point above the part's origin (the foot of its wall)
}

BODY = [(0.0, 0.0), (0.115, 0.0), (0.126, 0.012), (0.120, 0.022), (0.152, 0.042), (0.186, 0.080), (0.202, 0.128),
        (0.198, 0.178), (0.178, 0.222), (0.150, 0.252), (0.124, 0.268), (0.122, 0.276), (0.112, 0.279), (0.0, 0.279)]
LID = [(0.0, 0.277), (0.116, 0.277), (0.114, 0.288), (0.094, 0.306), (0.058, 0.322), (0.030, 0.328), (0.020, 0.334),
       (0.031, 0.348), (0.030, 0.362), (0.016, 0.370), (0.0, 0.372)]


def _link(shape, centre, along, across, length=0.052, width=0.030, wire=0.0052):
    """One oval chain link lying in the plane of `along` and `across`."""
    along = Vector(along).normalized()
    across = Vector(across).normalized()
    pts = []
    for k in range(16):
        a = 2 * math.pi * k / 16
        straight = (length - width) / 2 * (1 if math.cos(a) >= 0 else -1)
        pts.append(Vector(centre) + along * (math.cos(a) * width / 2 + straight) + across * (math.sin(a) * width / 2))
    shape.sweep(pts, wire, sides=6, closed=True)


def build(collection, seed=0, height=3.0):
    rng = shapes.rng_for('teapot_sign', seed)
    H = float(height)
    objects = []
    iron = shapes.Shape()

    # ------------------------------------------------------------------ the bracket
    iron.box((0.0, -0.006, H - 0.21), (0.066, 0.012, 0.62))
    for z in (H + 0.06, H - 0.20, H - 0.46):
        iron.lathe([(0.0, 0.0), (0.016, 0.0), (0.014, 0.006), (0.008, 0.010), (0.0, 0.011)], segments=12,
                   matrix=shapes.to4(shapes.frame_along((0.0, -1.0, 0.0)), (0.0, -0.012, z)))
    bar_end = -0.98
    iron.beam((0.0, -0.012, H), (0.0, bar_end, H), 0.028, 0.028)
    # the curl at the bar's end, turning down and back
    curl = []
    for k in range(25):
        t = k / 24
        a = math.pi / 2 - 2.2 * math.pi * t
        r = 0.065 * (1.0 - 0.72 * t)
        curl.append((0.0, bar_end - 0.002 + r * math.cos(a) - 0.0, H - 0.065 + r * math.sin(a)))
    curl[0] = (0.0, bar_end + 0.01, H)
    iron.sweep(curl, 1.0, section=[(-0.006, -0.012), (0.006, -0.012), (0.006, 0.012), (-0.006, 0.012)], up=(1.0, 0.0, 0.0))
    # the diagonal brace
    iron.beam((0.0, -0.012, H - 0.48), (0.0, -0.64, H - 0.010), 0.022, 0.022, up=(1.0, 0.0, 0.0))
    # scrollwork in the triangle between plate, bar and brace: flat bar, curled in the bracket's plane
    flat = [(-0.004, -0.009), (0.004, -0.009), (0.004, 0.009), (-0.004, 0.009)]     # (in the plane, across)

    def spiral(centre_y, centre_z, r0, turns, start, direction=1, shrink=0.78):
        pts = []
        n = int(28 * turns)
        for k in range(n + 1):
            t = k / n
            a = start + direction * 2 * math.pi * turns * t
            r = r0 * (1.0 - shrink * t)
            pts.append((0.0, centre_y + r * math.cos(a), centre_z + r * math.sin(a)))
        return pts

    # a ring touching the plate, the bar and the brace (found from the brace's line), a spiral inside it
    d = Vector((-0.628, 0.470)).normalized()
    nrm = Vector((-d.y, d.x)) if Vector((-d.y, d.x)).y > 0 else Vector((d.y, -d.x))
    outer = (0.466 * nrm.y - 0.011) / (1.0 + nrm.x + nrm.y)
    ring_y, ring_z = -0.012 - outer, H - 0.014 - outer
    ring = [(0.0, ring_y + (outer - 0.004) * math.cos(2 * math.pi * k / 48), ring_z + (outer - 0.004) * math.sin(2 * math.pi * k / 48))
            for k in range(48)]
    iron.sweep(ring, 1.0, closed=True, section=flat, up=(1.0, 0.0, 0.0))
    iron.sweep(spiral(ring_y, ring_z, outer - 0.012, 1.55, math.radians(90), direction=1, shrink=0.86), 1.0, section=flat,
               up=(1.0, 0.0, 0.0))
    # a smaller scroll further out, between bar and brace
    gap_y = -0.45
    brace_z = H - 0.48 + (gap_y + 0.012) / -0.628 * 0.47
    small_r = (H - 0.014 - (brace_z + 0.012)) / 2
    iron.sweep(spiral(gap_y, H - 0.014 - small_r, small_r - 0.004, 1.3, math.radians(90), direction=-1), 1.0, section=flat,
               up=(1.0, 0.0, 0.0))
    # collars clasping the scrolls where they touch
    touch = Vector((ring_y, ring_z)) - nrm * outer
    for (y, z) in ((ring_y, H - 0.016), (-0.016, ring_z), (touch.x, touch.y), (gap_y, H - 0.016)):
        iron.box((0.0, y, z), (0.030, 0.018, 0.018))
    # the two eyes the chains hang from
    eye_y = (-0.36, -0.64)
    for y in eye_y:
        iron.torus((0.0, y, H - 0.032), 0.016, 0.0045, axis=(0.0, 1.0, 0.0), segments=12, sides=6)
        iron.box((0.0, y, H - 0.016), (0.012, 0.012, 0.012))

    # ------------------------------------------------------------------ chains and the teapot, swinging a little
    pot_centre_y = -0.50
    lug_z = 0.262
    chain_len = 0.20
    pot_z = H - 0.048 - chain_len - lug_z - 0.02
    chains = shapes.Shape()
    for y in eye_y:
        z = H - 0.048
        k = 0
        while z > pot_z + lug_z + 0.02:
            across = (1.0, 0.0, 0.0) if k % 2 else (0.0, 1.0, 0.0)
            _link(chains, (0.0, y, z - 0.022), (0.0, 0.0, 1.0), across)
            z -= 0.040
            k += 1
    objects.append(chains.finish('teapot_sign chains', collection, IRON, smooth=True, sharp=None))

    pot = shapes.Shape()
    base = Vector((0.0, pot_centre_y, pot_z))
    pot.lathe(BODY, segments=48, matrix=Matrix.Translation(base))
    pot.lathe(LID, segments=48, matrix=Matrix.Translation(base))
    # the spout: from low on the front, rising and opening out to a lip
    spout_path = shapes.smooth_path([base + Vector((0.0, -0.170, 0.090)), base + Vector((0.0, -0.250, 0.115)),
                                     base + Vector((0.0, -0.315, 0.175)), base + Vector((0.0, -0.355, 0.250)),
                                     base + Vector((0.0, -0.385, 0.290))], steps=5)
    n = len(spout_path)
    pot.sweep(spout_path, 0.04, sides=16, radii=[0.050 - 0.030 * (i / (n - 1)) ** 0.8 for i in range(n)])
    pot.torus(spout_path[-1], 0.021, 0.004, axis=(spout_path[-1] - spout_path[-2]), segments=16, sides=6)
    # the handle: a loop on the back, flattened oval in section
    handle = shapes.smooth_path([base + Vector((0.0, 0.165, 0.225)), base + Vector((0.0, 0.245, 0.240)),
                                 base + Vector((0.0, 0.300, 0.200)), base + Vector((0.0, 0.300, 0.120)),
                                 base + Vector((0.0, 0.245, 0.075)), base + Vector((0.0, 0.185, 0.068))], steps=6)
    pot.sweep(handle, 1.0, section=[(-0.016, -0.010), (0.016, -0.010), (0.020, 0.0), (0.016, 0.010), (-0.016, 0.010), (-0.020, 0.0)],
              up=(1.0, 0.0, 0.0))
    # lugs on the shoulder for the chains, front and back
    for dy in (eye_y[0] - pot_centre_y, eye_y[1] - pot_centre_y):
        pot.torus(base + Vector((0.0, dy, lug_z + 0.014)), 0.014, 0.0045, axis=(1.0, 0.0, 0.0), segments=12, sides=6)
        pot.box(base + Vector((0.0, dy * 0.97, lug_z - 0.002)), (0.010, 0.020, 0.012))
    pot_obj = pot.finish('teapot_sign teapot', collection, COPPER, smooth=True, sharp=50)
    objects.append(pot_obj)

    swing = math.radians(rng.uniform(-3.0, 3.0))
    shapes.tilt_all(objects, ry=swing, pivot=(0.0, -0.5, H - 0.032))
    objects.append(iron.finish('teapot_sign bracket', collection, IRON, smooth=True, sharp=40))
    return objects
