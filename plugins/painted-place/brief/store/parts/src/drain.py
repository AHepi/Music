"""
drain: cast iron set flush in a road of about 1900, of two kinds. A round sewer cover in its square frame: the lid's
raised pattern of rings and radial ribs round a boss, two lifting holes, a dark gap round it. Or a street gully
grate in the gutter: a frame and bars over a black pit, a spine bar along the middle. The iron is rusty in the hollows
and on every side, and worn bright on the faces that stand proud, where wheels and boots go.

Its origin is the road's surface: the frame's top is 1 mm above z = 0 (the raised pattern and the bars 4 mm), the
frame and the pit go 5 cm below.

Options:
    kind     'cover' (default): a round sewer cover in a square frame; 'grate': a gully grate, long along Y
    seed     where the iron is worn and rusted, the cover's turn in its frame

Where it came from: '/home/claude/build-55-street/fronts/render_final.py', the drain grate (lines 248-254: a rust box,
nine bars, a spine, a dark box under it) and the sewer cover (lines 256-265: a rust disc, raised rings and recesses,
six ribs, a dark box), each in two store materials. Rebuilt here as one iron casting with a frame, the lid a separate
casting in it with a gap and lifting holes, the grate's bars with a pit under them, and one made iron material that
puts the wear on what stands proud and the rust in the hollows by itself.
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
import _shapes_street_things as street  # noqa: E402

PART = 'drain'
DARK = 'RECESSES • near-black blue'
KINDS = ('cover', 'grate')
PROUD = 0.003          # how far the raised pattern and the bars stand above the road (z = 0)

CARD = {
    'name': PART,
    'what': 'cast iron set flush in the road: a round sewer cover in a square frame (raised rings and ribs, lifting holes) or a '
            'gully grate over a black pit; rusty in the hollows, worn bright on the raised pattern',
    'size_m': (0.80, 0.80, 0.055),
    'options': {
        'kind': "'cover' (default): a round sewer cover, 0.62 m across, in a square frame 0.80 m a side; 'grate': a street gully "
                "grate, 0.50 m across (X) and 0.74 m long (Y), over a black pit",
        'seed': "where the iron is worn and rusted, the cover's turn in its frame (default 0)",
    },
    'materials': ['PART • drain: cast iron, rusty in the hollows, worn bright on top', DARK],
    'source': "'/home/claude/build-55-street/fronts/render_final.py', the drain grate (lines 248-254) and the sewer cover (lines 256-265)",
    'views': 'made to be seen from above and from the front at a low angle; flat things read as a line from straight across',
    'trap': 'the origin is the road surface, not the foot: the iron is flush with z = 0 (1 mm proud) and goes 5 cm below, so set the '
            "origin at the setts' tops and cut the setts (or the ground) out under it, or they cover it",
}


def _cover(iron, dark, rng):
    """A round lid in a square frame. Raised work stands PROUD above z = 0; the lid's plate is 3 mm under it."""
    half, lid_r, gap = 0.40, 0.31, 0.007
    plate = -0.003
    # the frame: a square slab with a round hole, its top at z = 0, 5 cm deep
    outline = []
    n = 48
    frame = shapes.Shape()
    for k in range(n):
        a = 2 * math.pi * k / n
        outline.append((math.cos(a), math.sin(a)))
    outer = []
    for k in range(n):
        a = 2 * math.pi * k / n
        c, s = math.cos(a), math.sin(a)
        m = max(abs(c), abs(s))
        outer.append((half * c / m, half * s / m))
    for z0, z1 in ((-0.05, 0.0),):
        top_out = frame._verts([(x, y, z1) for (x, y) in outer])
        top_in = frame._verts([((lid_r + gap) * c, (lid_r + gap) * s, z1) for (c, s) in outline])
        bot_out = frame._verts([(x, y, z0) for (x, y) in outer])
        bot_in = frame._verts([((lid_r + gap) * c, (lid_r + gap) * s, z0) for (c, s) in outline])
        frame._rings([top_in, top_out], True)
        frame._rings([top_out, bot_out], True)
        frame._rings([bot_out, bot_in], True)
        frame._rings([bot_in, top_in], True)
    # a raised bead round the hole and the frame's outer edge
    frame.torus((0, 0, -0.001), lid_r + gap + 0.012, 0.005, segments=48, sides=6)
    for (x, y, sx, sy) in ((0, half - 0.018, 2 * half - 0.03, 0.012), (0, -half + 0.018, 2 * half - 0.03, 0.012),
                           (half - 0.018, 0, 0.012, 2 * half - 0.03), (-half + 0.018, 0, 0.012, 2 * half - 0.03)):
        frame.box((x, y, -0.002), (sx, sy, 0.01))
    iron.append(frame)
    # the lid: a plate, raised rings, radial ribs, a boss; two lifting holes cut as dark slots
    lid = shapes.Shape()
    lid.lathe([(0.0, -0.045), (lid_r - 0.01, -0.045), (lid_r, -0.04), (lid_r, plate), (0.0, plate)], segments=64)
    turn = rng.uniform(0, math.pi / 4)
    rib_h = PROUD - plate
    for rr, w in ((lid_r - 0.022, 0.016), (0.205, 0.014), (0.115, 0.014)):
        lid.lathe([(rr - w / 2, plate - 0.002), (rr + w / 2, plate - 0.002), (rr + w / 2 - 0.002, PROUD), (rr - w / 2 + 0.002, PROUD),
                   (rr - w / 2, plate - 0.002)], segments=64, open_ends=True)
    for k in range(8):
        a = turn + k * math.pi / 4
        d = Vector((math.cos(a), math.sin(a), 0.0))
        for (r0, r1) in ((0.045, 0.108), (0.122, 0.198), (0.212, lid_r - 0.03)):
            lid.beam(d * r0 + Vector((0, 0, plate + rib_h / 2 - 0.001)), d * r1 + Vector((0, 0, plate + rib_h / 2 - 0.001)), 0.013, rib_h + 0.002)
    lid.lathe([(0.0, PROUD), (0.035, PROUD), (0.042, plate - 0.002), (0.0, plate - 0.002)], segments=24)
    # small raised studs in the outer ring's bays (a non-slip pattern)
    for k in range(8):
        a = turn + math.pi / 8 + k * math.pi / 4
        for rr in (0.16, 0.246):
            if rr > 0.2 and k in (0, 4):
                continue                  # the lifting holes are there
            c = Vector((math.cos(a) * rr, math.sin(a) * rr, plate + rib_h / 2 - 0.001))
            lid.box(c, (0.02, 0.02, rib_h + 0.002), Matrix.Rotation(a, 3, 'Z'))
    iron.append(lid)
    # the dark: under the gap, and in the two lifting holes
    dark.lathe([(0.0, -0.052), (lid_r + gap + 0.004, -0.052), (lid_r + gap + 0.004, -0.046), (0.0, -0.046)], segments=48)
    for sgn in (-1, 1):
        a = turn + math.pi / 8
        c = Vector((math.cos(a), math.sin(a), 0.0)) * (sgn * 0.246) + Vector((0.0, 0.0, plate + 0.0004))
        dark.box(c, (0.045, 0.014, 0.0012), Matrix.Rotation(a, 3, 'Z'))


def _grate(iron, dark, rng):
    """A rectangular gully grate: frame, bars across X, a spine along Y, a black pit under it."""
    w, l, border = 0.50, 0.74, 0.04
    frame = shapes.Shape()
    for (x, y, sx, sy) in ((0.0, l / 2 - border / 2, w, border), (0.0, -l / 2 + border / 2, w, border),
                           (w / 2 - border / 2, 0.0, border, l - 2 * border), (-w / 2 + border / 2, 0.0, border, l - 2 * border)):
        frame.box((x, y, -0.025), (sx, sy, 0.05))
    # a lip round the opening, a step down for the grate to sit in
    iron.append(frame)
    bars = shapes.Shape()
    inner_w, inner_l = w - 2 * border, l - 2 * border
    count = 9
    pitch = inner_l / count
    for i in range(count):
        y = -inner_l / 2 + pitch * (i + 0.5)
        # a bar: narrower at the bottom (a cast bar's taper), its top PROUD above the road
        bars.frustum(Vector((0.0, y, -0.04)), (inner_w / 2 + 0.004, 0.009), (inner_w / 2 + 0.004, 0.017), 0.04 + PROUD)
    bars.frustum(Vector((0.0, 0.0, -0.04)), (0.009, inner_l / 2 + 0.004), (0.016, inner_l / 2 + 0.004), 0.04 + PROUD - 0.0005)
    for sx in (-1, 1):
        bars.frustum(Vector((sx * inner_w / 4, 0.0, -0.04)), (0.006, inner_l / 2 + 0.004), (0.009, inner_l / 2 + 0.004), 0.04 - 0.003)
    iron.append(bars)
    dark.box((0.0, 0.0, -0.051), (inner_w + 0.01, inner_l + 0.01, 0.004))


def build(collection, seed=0, kind='cover'):
    if kind not in KINDS:
        raise ValueError("drain kind is 'cover' or 'grate', not %r" % (kind,))
    rng = shapes.rng_for(PART, seed)
    iron_shapes = []
    dark = shapes.Shape()
    if kind == 'cover':
        _cover(iron_shapes, dark, rng)
    else:
        _grate(iron_shapes, dark, rng)
    # everything 1 mm up, so the frame's top does not lie exactly in the road's surface (the two would flicker)
    for shape in iron_shapes + [dark]:
        shape.transform(Matrix.Translation((0.0, 0.0, 0.001)))
    material = street.worn_iron_material(PART, low=-0.0008, high=0.0035)
    objects = []
    names = ('frame', 'cover') if kind == 'cover' else ('frame', 'bars')
    for name, shape in zip(names, iron_shapes):
        objects.append(shape.finish('drain %s' % name, collection, material, smooth=False))
    objects.append(dark.finish('drain dark under', collection, DARK, smooth=False))
    return objects
