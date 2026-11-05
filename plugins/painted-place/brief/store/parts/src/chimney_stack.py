"""
chimney_stack: a town chimney stack of about 1900 on a roof ridge or a gable wall: a rubble, ashlar or brick stack,
long along X, with an oversailing course near the top, a dressed stone cope, and a row of clay chimney pots set in
mortar on the cope, each its own height and a little out of plumb. Soot from the fires has blackened it from the top
down: the pots and the cope black, the stack darkest under the cope and streaked for a metre and a half below.

Its origin is where it meets the roof: z = 0 is the ridge line (or the wall top) under the middle of the stack. Below
that its root block goes 1.0 m down, to be hidden in the roof, so the roof's two slopes meet its sides with no gap.

Options:
    pots     how many pots in the row along the top (default 5; the stack is 0.5 m long for each, plus 0.1 m)
    stone    'rubble' (default): random rubble stone; 'ashlar': dressed sandstone blocks in courses; 'brick': dark brick
    height   metres from z = 0 to the top of the cope (default 1.4)
    seed     each pot's height and lean, the soot's streaks, the blocks' lengths

Where it came from: '/home/claude/build-55-street/fronts/render_final.py', the chimney stack in building() (lines
419-431: a box of 'SURFACE • old_stone_wall_02' from 1.0 m under the ridge, two slabs of the dressings stone, five
clay cylinders), the clay (line 126) and the soot laid on the end stacks (lines 1776-1793). Rebuilt here with turned
pots (a base, a taper, a rolled rim, hollow and black inside) set in mortar flaunching, an oversailing course and a
cope, a choice of stone, and the soot in the materials themselves, heaviest at the top.
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

PART = 'chimney_stack'
STONES = ('rubble', 'ashlar', 'brick')
DRESSING = 'STONE • worn honey-grey architectural dressings'
ROOT = 1.0            # how far the stack goes down under z = 0
DEPTH = 0.85          # the stack's depth across (Y)
PITCH = 0.5           # metres of stack per pot
SOOT_REACH = 1.6      # how far down from the cope the soot reaches

CARD = {
    'name': PART,
    'what': 'a chimney stack (rubble, ashlar or brick) with an oversailing course, a stone cope and a row of clay pots set in '
            'mortar, sooted black from the top down; long along X',
    'size_m': (2.75, 1.0, 3.2),
    'foot_z': -ROOT,
    'options': {
        'pots': 'how many clay pots in the row along the top (default 5; the stack is 0.5 m long for each, plus 0.1 m)',
        'stone': "'rubble' (default): random rubble stone; 'ashlar': dressed sandstone blocks in courses; 'brick': dark brick",
        'height': 'metres from z = 0 (the ridge or wall top) to the top of the cope (default 1.4)',
        'seed': "each pot's height and lean, the soot's streaks, the blocks' lengths (default 0)",
    },
    'materials': ['SURFACE • old_stone_wall_02 (chimney_stack, sooted)', 'SURFACE • dark_brick_wall (chimney_stack, sooted)',
                  DRESSING + ' (chimney_stack, sooted)', 'PART • chimney_stack: fired clay, sooted', 'PART • chimney_stack: lime mortar, sooted'],
    'source': "'/home/claude/build-55-street/fronts/render_final.py', the chimney stack in building() (lines 419-431), the clay pots "
              "(line 126) and the soot on the end stacks (lines 1776-1793)",
    'views': 'made to be seen against the sky from the street below; reads from every side',
    'trap': 'z = 0 is the ridge (or wall top), not its lowest point: its root block goes 1.0 m below, hidden in the roof; set the origin '
            'on the ridge line (with the length along the ridge, or turned 90 degrees across it on a party wall, where a roof steeper '
            'than 36 degrees, or more than 5 pots, leaves its ends short: lower it); on a bare wall top lift it 1.0 m',
}


def _soot_of_height(top):
    """The soot on the stack at a height: black at the cope, fading out SOOT_REACH below it."""
    def soot(co):
        return max(0.0, min(1.0, (co[2] - (top - SOOT_REACH)) / SOOT_REACH)) ** 1.4
    return soot


def _block(shape, centre, size, steps):
    """A box from rings of points up its height (`steps` rings), so a point number (the soot) can change up it."""
    cx, cy, cz = centre
    sx, sy, sz = size
    rings = []
    for k in range(steps + 1):
        z = cz - sz / 2 + sz * k / steps
        rings.append(shape._verts([(cx - sx / 2, cy - sy / 2, z), (cx + sx / 2, cy - sy / 2, z), (cx + sx / 2, cy + sy / 2, z),
                                   (cx - sx / 2, cy + sy / 2, z)]))
    shape._rings(rings, True, True, True)


def _pot(shape, base, height, rng):
    """One clay chimney pot standing at `base`: a turned, tapering pot with a rolled rim and a bead near its foot,
    hollow; a little out of plumb. Writes the soot number on its points: black at the mouth, less down the pot,
    black inside."""
    r0, r1 = rng.uniform(0.125, 0.14), rng.uniform(0.1, 0.112)
    wall = 0.016
    # inside wall going up (taper parallel to the outside), the rim rolled over, outside going down
    inner = [(r0 - wall + (r1 - r0) * t, 0.02 + (height - 0.03) * t) for t in (0.0, 0.25, 0.5, 0.75, 1.0)]
    outer = []
    for t in (1.0, 0.8, 0.6, 0.4, 0.2, 0.1, 0.0):
        outer.append((r0 + (r1 - r0) * t, height * t))
    rim = [(r1 - wall + 0.002, height - 0.005), (r1 + 0.006, height), (r1 + 0.02, height - 0.012), (r1 + 0.018, height - 0.045),
           (r1 + 0.002, height - 0.055)]
    bead = [(r0 + 0.012, 0.09), (r0 + 0.012, 0.06)]
    profile = [(0.0, 0.02)] + inner + rim + [p for p in outer if p[1] < height - 0.06 and p[1] > 0.1] + [(r0 + 0.002, 0.1)] + bead + \
              [(r0, 0.05), (r0, 0.0), (0.0, 0.0)]
    lean = Matrix.Rotation(rng.uniform(-0.04, 0.04), 4, 'X') @ Matrix.Rotation(rng.uniform(-0.04, 0.04), 4, 'Y')
    m = Matrix.Translation(Vector(base)) @ lean @ Matrix.Rotation(rng.uniform(0, math.pi), 4, 'Z')
    before = set(shape.bm.verts)
    shape.lathe(profile, segments=20, matrix=m)
    made = [v for v in shape.bm.verts if v not in before]
    soot = shape.bm.verts.layers.float['soot']
    for v in made:
        local = m.inverted() @ v.co
        r = math.hypot(local.x, local.y)
        outside = r > (r0 + (r1 - r0) * max(0.0, min(1.0, local.z / height))) - wall * 0.5
        frac = max(0.0, min(1.0, local.z / height))
        v[soot] = (0.4 + 0.6 * frac ** 1.2) if outside else 1.0


def build(collection, seed=0, pots=5, stone='rubble', height=1.4):
    pots = int(round(barn.number('chimney_stack pots', pots, 1, 12)))
    height = barn.number('chimney_stack height', height, 0.5, 4.0)
    if stone not in STONES:
        raise ValueError("chimney_stack stone is one of %s, not %r" % (', '.join(repr(s) for s in STONES), stone))
    rng = shapes.rng_for(PART, seed)
    objects = []
    length = pots * PITCH + 0.1
    top = height                                       # the cope's top
    cope_h, band_h = 0.12, 0.08
    shaft_top = top - cope_h
    soot = _soot_of_height(top)

    # ------------------------------------------------------------------ the shaft
    shaft = shapes.Shape()
    barn.number_layers(shaft, points=('soot',))
    joints = None
    if stone == 'ashlar':
        joints = shapes.Shape()
        barn.number_layers(joints, points=('soot',))
        _block(joints, (0.0, 0.0, (shaft_top - ROOT) / 2), (length - 0.012, DEPTH - 0.012, shaft_top + ROOT), 24)
        course = 0.3
        z = -ROOT
        row = 0
        while z < shaft_top - 1e-4:
            h = min(course, shaft_top - z)
            # the blocks round the four faces of this course: along the front and back, then the ends between them
            for side in (-1, 1):
                x = -length / 2 + (0.0 if row % 2 == 0 else 0.25)
                first = True
                while x < length / 2 - 1e-4:
                    bl = rng.uniform(0.45, 0.75) if not (first and row % 2) else 0.25
                    first = False
                    x1 = min(length / 2, x + bl)
                    if length / 2 - x1 < 0.15:
                        x1 = length / 2
                    _block(shaft, ((x + x1) / 2, side * (DEPTH / 2 - 0.09), z + h / 2), (x1 - x - 0.006, 0.18, h - 0.006), 2)
                    x = x1
            for side in (-1, 1):
                _block(shaft, (side * (length / 2 - 0.09), 0.0, z + h / 2), (0.18, DEPTH - 0.36 - 0.006, h - 0.006), 2)
            z += course
            row += 1
        material = street.sooted(DRESSING, PART)
    else:
        _block(shaft, (0.0, 0.0, (shaft_top - ROOT) / 2), (length, DEPTH, shaft_top + ROOT), 24)
        if stone == 'rubble':
            material = street.sooted('SURFACE • old_stone_wall_02', PART, Grime=0.8)
        else:
            material = street.sooted('SURFACE • dark_brick_wall', PART, Grime=0.5)
    barn.point_numbers(shaft, shaft.bm.verts, soot=lambda v: soot(v.co))
    objects.append(shaft.finish('chimney_stack shaft', collection, material, smooth=False))
    if joints is not None:
        barn.point_numbers(joints, joints.bm.verts, soot=lambda v: soot(v.co))
        objects.append(joints.finish('chimney_stack joints', collection, street.mortar_material(PART, 'lime mortar, sooted'), smooth=False))

    # ------------------------------------------------------------------ the oversailing course and the cope
    dressing = shapes.Shape()
    barn.number_layers(dressing, points=('soot',))
    band_z = top - 0.38
    _block(dressing, (0.0, 0.0, band_z + band_h / 2), (length + 0.1, DEPTH + 0.1, band_h), 2)
    _block(dressing, (0.0, 0.0, shaft_top + cope_h / 2), (length + 0.15, DEPTH + 0.15, cope_h), 2)
    barn.point_numbers(dressing, dressing.bm.verts, soot=lambda v: 0.85 if v.co.z > band_z + band_h else soot(v.co))
    objects.append(dressing.finish('chimney_stack cope', collection, street.sooted(DRESSING, PART), smooth=False, chamfer=0.01))

    # ------------------------------------------------------------------ the pots in their flaunching
    clay = shapes.Shape()
    barn.number_layers(clay, points=('soot',))
    mortar = shapes.Shape()
    barn.number_layers(mortar, points=('soot',))
    for k in range(pots):
        x = -length / 2 + 0.05 + PITCH * (k + 0.5)
        h = rng.uniform(0.45, 0.75)
        _pot(clay, (x + rng.uniform(-0.02, 0.02), rng.uniform(-0.02, 0.02), top + 0.02), h, rng)
        mortar.lathe([(0.0, top - 0.005), (0.215, top - 0.005), (0.2, top + 0.012), (0.15, top + 0.07), (0.0, top + 0.07)], segments=18,
                     matrix=Matrix.Translation((x, 0.0, 0.0)))
    barn.point_numbers(mortar, mortar.bm.verts, soot=0.8)
    objects.append(clay.finish('chimney_stack pots', collection, street.clay_material(PART), smooth=True, sharp=50))
    objects.append(mortar.finish('chimney_stack flaunching', collection, street.mortar_material(PART), smooth=True, sharp=50))
    return objects
