"""
milk_churn: a steel milk churn of the conical 17-gallon kind used in Britain until the 1930s: a wide-footed body
tapering to a short neck, a mushroom lid with a loop on top, rolled bands round the body, a stout foot ring, and two
drop handles at the shoulder (either side, on X). About 0.75 m high. Worn galvanised steel, dull grey, dented, with
rust at the foot. Foot at z = 0; the maker's plate faces -Y.

Options:
    lid      True (default): the lid on; False: the lid off, leant against the foot at the front (-Y)
    seed     the dents and the handles' hang

Where it came from: '/home/claude/build-51-chapel/dress/dress_block.py', churn() (line 217): stacked cylinders in a
pale 'churn tin' and bands; rebuilt here as one turned body at real proportion, in dull galvanised steel instead of
brass or tin.
"""

import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import _shapes_chapel as shapes  # noqa: E402

PART = 'milk_churn'
RUST = 'RUST • rain-aged iron'

CARD = {
    'name': PART,
    'what': 'a conical 17-gallon steel milk churn, about 0.75 m: wide foot, tapering body, short neck, mushroom lid with a loop, '
            'rolled bands, two drop handles at the shoulder; dull dented galvanised steel',
    'size_m': (0.46, 0.47, 0.78),
    'options': {
        'lid': 'True (default): the lid on; False: the lid off, leant against the foot at the front (-Y)',
        'seed': "the dents' places and the handles' hang (default 0)",
    },
    'materials': ['PART • milk_churn: dull galvanised steel', RUST],
    'source': "'/home/claude/build-51-chapel/dress/dress_block.py', churn() (line 217)",
    'views': 'reads from every side; the handles hang on X, the plate faces -Y',
    'trap': '',
}

BODY = [(0.0, 0.0), (0.195, 0.0), (0.215, 0.012), (0.22, 0.03), (0.218, 0.10), (0.205, 0.25), (0.185, 0.40),
        (0.16, 0.50), (0.135, 0.56), (0.12, 0.59), (0.118, 0.62), (0.118, 0.66), (0.124, 0.665)]


def radius_at(z):
    for (r0, z0), (r1, z1) in zip(BODY[1:], BODY[2:]):
        if z0 <= z <= z1:
            return r0 + (r1 - r0) * (z - z0) / max(z1 - z0, 1e-6)
    return BODY[-1][0]


def build(collection, seed=0, lid=True):
    rng = shapes.rng_for(PART, seed)
    objects = []
    steel = shapes.galvanised_material(PART)
    wall = 0.0015

    # ------------------------------------------------------------------ body: outer skin, inner skin down the neck
    body = shapes.Shape()
    body.lathe(BODY, segments=48)
    inner = [(0.118 - wall, 0.665), (0.118 - wall, 0.62), (0.112, 0.59), (0.10, 0.56)]
    body.lathe(inner + [(0.0, 0.555)], segments=48, open_ends=True)
    body.lathe([(0.124, 0.665), (0.118 - wall, 0.665)], segments=48, open_ends=True)      # the neck's top edge
    # rolled bands round the body, and the shoulder bead
    for z in (0.085, 0.30, 0.50):
        body.torus((0.0, 0.0, z), radius_at(z) + 0.003, 0.007, segments=48, sides=8)
    body.torus((0.0, 0.0, 0.585), radius_at(0.585) + 0.003, 0.006, segments=48, sides=8)
    # the foot ring: a heavier rolled ring under the body
    body.torus((0.0, 0.0, 0.012), 0.205, 0.012, segments=48, sides=10)
    # the maker's plate on the front: a thin oval boss
    body.sphere((0.0, -radius_at(0.33) - 0.001, 0.33), 0.035, segments=16, rings=8, squash=(1.0, 0.08, 0.8))
    # the handle lugs at the shoulder
    lug_z = 0.515
    lug_r = radius_at(lug_z)
    for side in (-1, 1):
        body.box((side * (lug_r + 0.006), 0.0, lug_z), (0.014, 0.05, 0.04))
    body.number_all('board_tone', 0.0)
    churn = body.finish('milk_churn body', collection, steel, smooth=True, sharp=42)
    objects.append(churn)
    # rust at the foot: a thin ring low down where the water stands
    rust = shapes.Shape()
    rust.torus((0.0, 0.0, 0.004), 0.2, 0.0045, segments=48, sides=6)
    rust.lathe([(0.2155, 0.013), (0.2185, 0.04)], segments=48, open_ends=True)
    objects.append(rust.finish('milk_churn foot rust', collection, RUST, smooth=True, sharp=40))

    # ------------------------------------------------------------------ drop handles: a half ring hanging from each lug
    for side in (-1, 1):
        hang = math.radians(rng.uniform(55, 85))        # how far the handle hangs down from level
        handle = shapes.Shape()
        pts = []
        for k in range(17):
            a = math.pi * k / 16
            # a stirrup: wide at the lug, out and down
            p = Vector((0.0, -0.045 * math.cos(a), 0.0)) + Vector((math.sin(a) * 0.07, 0.0, 0.0))
            p = Matrix.Rotation(hang, 3, 'Y') @ p if side > 0 else Matrix.Rotation(-hang, 3, 'Y') @ Vector((-p.x, p.y, p.z))
            pts.append(p + Vector((side * (lug_r + 0.012), 0.0, lug_z)))
        handle.sweep(pts, 0.007, sides=8)
        for sy in (-1, 1):
            handle.sphere((side * (lug_r + 0.012), sy * 0.045, lug_z), 0.009, segments=10, rings=5)
        objects.append(handle.finish('milk_churn handle %s' % ('left' if side < 0 else 'right'), collection, steel, smooth=True, sharp=50))

    # ------------------------------------------------------------------ the lid: a mushroom with a loop
    cap = shapes.Shape()
    cap_profile = [(0.0, 0.0), (0.112, 0.0), (0.112, 0.04), (0.14, 0.045), (0.142, 0.055), (0.13, 0.075), (0.09, 0.095), (0.03, 0.105), (0.0, 0.106)]
    cap.lathe(cap_profile, segments=48)
    loop = shapes.Shape()
    loop.torus((0.0, 0.0, 0.112), 0.03, 0.006, axis=(0.0, 1.0, 0.0), segments=20, sides=8, arc=(0.0, math.pi))
    loop.cylinder((-0.03, 0.0, 0.1), (-0.03, 0.0, 0.112), 0.006, segments=8)
    loop.cylinder((0.03, 0.0, 0.1), (0.03, 0.0, 0.112), 0.006, segments=8)
    if lid:
        place = Matrix.Translation((0.0, 0.0, 0.63))
    else:
        # the lid off, leant against the foot at the front: its underside towards the churn (+Y), its dome and loop
        # facing outwards (-Y); a turn of +68 degrees about X tips the lid's top towards -Y (-68 would face it the
        # churn's way); then set down so its lowest point (the rim's edge) is on the ground
        place = Matrix.Translation((0.0, -0.25, 0.0)) @ Matrix.Rotation(math.radians(68), 4, 'X')
        lowest = min((place @ Vector((r * math.cos(a), r * math.sin(a), z))).z
                     for (r, z) in cap_profile for a in [2 * math.pi * k / 48 for k in range(48)])
        place = Matrix.Translation((0.0, 0.0, -lowest)) @ place
    objects.append(cap.finish('milk_churn lid', collection, steel, smooth=True, sharp=42, matrix=place))
    objects.append(loop.finish('milk_churn lid loop', collection, steel, smooth=True, sharp=50, matrix=place))

    # a slight lean, as it stands on setts
    lean = math.radians(rng.uniform(0.0, 1.0))
    direction = rng.uniform(0, 2 * math.pi)
    shapes.tilt_all(objects, rx=lean * math.cos(direction), ry=lean * math.sin(direction))
    return objects
