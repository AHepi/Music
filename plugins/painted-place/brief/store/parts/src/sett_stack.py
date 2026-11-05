"""
sett_stack: the road men's spare granite setts, stacked at a kerb for the corporation's cart: new setts (sharp
arrises, wet, each its own shade of grey, speckled with mica and quartz) laid in courses, each course crossed over the
one below as road men stack them so the stack stands, a gap or two in the top course where setts were taken, and a
few loose setts beside it. The stack is long along X, so it stands along a kerb that runs along X.

Options:
    layers   how many courses high (default 3; a course is about 0.135 m)
    loose    how many setts lie loose on the ground beside the stack (default 2; 0 for none)
    seed     every sett's size, shade and set, the gaps in the top course, where the loose ones lie

Where it came from: '/home/claude/build-55-street/fronts/render_final.py', the road men's spare setts (lines 1066-1086)
and their material 'new granite setts' (line 777): boxes three courses high, all laid the same way, one loose. Rebuilt
here with dressed setts (chamfered arrises, each a little out of square), the courses crossed, a made granite with
its grain, and the loose setts lying as they fell.
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
import _shapes_barn as barn  # noqa: E402
import _shapes_street_things as street  # noqa: E402

PART = 'sett_stack'
COURSE = 0.135

CARD = {
    'name': PART,
    'what': "the road men's spare granite setts stacked at a kerb: new, sharp and wet, each its own grey, the courses crossed, a gap "
            'in the top course, a few loose beside it',
    'size_m': (1.16, 0.65, 0.41),
    'options': {
        'layers': 'how many courses high (default 3; about 0.135 m a course; three or four is usual)',
        'loose': 'how many setts lie loose on the ground beside the stack (default 2; 0 for none, up to 4)',
        'seed': "every sett's size, shade and set, the gaps in the top course, where the loose ones lie (default 0)",
    },
    'materials': ['PART • sett_stack: new granite, wet'],
    'source': "'/home/claude/build-55-street/fronts/render_final.py', the road men's spare setts (lines 1066-1086) and 'new granite setts' "
              '(line 777)',
    'views': 'reads from every side; long along X',
    'trap': 'new granite is darker than the worn setts of an old road and as wet: against them the stack reads only by its sharp '
            'arrises catching light, so put a lamp or a lantern near it (the street had the road men\'s lantern on top)',
}


def _sett(shape, centre, length, width, height, turn, rng, tilt=None):
    """One dressed sett into `shape`: a box a little out of square (its corners moved a few mm), long along its own X,
    turned `turn` about Z (and `tilt`, a rotation matrix, for a fallen one) round `centre` (its middle)."""
    made = shape.box((0.0, 0.0, 0.0), (length, width, height))
    for v in made['verts']:
        v.co += Vector((rng.uniform(-0.004, 0.004), rng.uniform(-0.004, 0.004), rng.uniform(-0.003, 0.003)))
    m = Matrix.Translation(Vector(centre)) @ Matrix.Rotation(turn, 4, 'Z')
    if tilt is not None:
        m = m @ tilt
    for v in made['verts']:
        v.co = m @ v.co
    return made['verts']


def _to_ground(verts):
    """Lift or lower one sett so its lowest corner is on the ground (its corners are a few mm out of square)."""
    low = min(v.co.z for v in verts)
    for v in verts:
        v.co.z -= low


def build(collection, seed=0, layers=3, loose=2):
    layers = int(round(barn.number('sett_stack layers', layers, 1, 6)))
    loose = int(round(barn.number('sett_stack loose', loose, 0, 4)))
    rng = shapes.rng_for(PART, seed)
    stones = shapes.Shape()
    z = 0.0
    for layer in range(layers):
        top = layer == layers - 1 and layers > 1
        h_course = []
        if layer % 2 == 0:
            # three along X, two deep: setts long along X
            cells = [((i - 1) * 0.285, (j - 0.5) * 0.15, 0.0) for i in range(3) for j in range(2)]
        else:
            # crossed: six along X, one deep: setts long along Y
            cells = [((i - 2.5) * 0.146, 0.0, math.pi / 2) for i in range(6)]
        gaps = set()
        if top:
            gaps = set(rng.sample(range(len(cells)), 2 if len(cells) == 6 and layer % 2 == 0 else 3))
        for k, (x, y, turn) in enumerate(cells):
            if k in gaps:
                continue
            length, width, height = rng.uniform(0.25, 0.28), rng.uniform(0.13, 0.145), rng.uniform(0.128, 0.135)
            h_course.append(height)
            verts = _sett(stones, (x + rng.uniform(-0.008, 0.008), y + rng.uniform(-0.008, 0.008), z + height / 2), length, width, height,
                          turn + rng.uniform(-0.05, 0.05), rng)
            if layer == 0:
                _to_ground(verts)
        z += COURSE
    # loose setts on the ground, as they fell: flat, on their sides, one leant against the stack's front
    spots = [((0.36, -0.36), 0.45, None), ((-0.56, -0.12), 1.35, Matrix.Rotation(math.pi / 2, 4, 'X')),
             ((0.62, 0.02), 1.6, None), ((-0.12, -0.42), 0.15, Matrix.Rotation(math.pi / 2, 4, 'X'))]
    for k in range(loose):
        (x, y), turn, tilt = spots[k]
        length, width, height = rng.uniform(0.25, 0.28), rng.uniform(0.13, 0.145), rng.uniform(0.128, 0.135)
        up = width / 2 if tilt is not None else height / 2
        _to_ground(_sett(stones, (x + rng.uniform(-0.03, 0.03), y + rng.uniform(-0.03, 0.03), up), length, width, height,
                         turn + rng.uniform(-0.2, 0.2), rng, tilt=tilt))
    obj = stones.finish('sett_stack setts', collection, street.granite_material(PART), smooth=True, sharp=40, chamfer=0.007,
                        chamfer_segments=2)
    # the chamfer on corners a few mm out of square reaches a few mm under the ground: lift the whole stack back onto it
    low = min(v.co.z for v in obj.data.vertices)
    obj.data.transform(Matrix.Translation((0.0, 0.0, -low)))
    return [obj]
