"""
barrel: a wooden barrel (a cask of about 36 gallons): twenty-odd oak staves in relief, bulging at the middle and
standing proud of the heads at both ends, six iron hoops with their rivets, a head of boards at each end, and a bung
in the side at the bilge (towards -Y when standing).

Options:
    lying    False (default): standing on its end; True: lying on its side along X with the bung on top, held by two
             wooden chocks.

Where it came from: "46 desert-mine - render_final.py" (procedural-textures/46 Pictures-only builders - three places),
barrel() (line 1095): a tapered cylinder with three rings; rebuilt here with staves, chimes, heads, hoops and a bung.
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

RUST = 'RUST • rain-aged iron'

CARD = {
    'name': 'barrel',
    'what': 'a wooden barrel: oak staves in relief, six iron hoops, heads, a bung in the side; standing or lying',
    'size_m': (0.62, 0.63, 0.87),
    'options': {
        'lying': 'False (default): standing on its end, bung towards -Y; True: lying along X, bung on top, on two chocks',
    },
    'materials': ['SURFACE • rough_wood (barrel)', RUST],
    'source': '"46 desert-mine - render_final.py", barrel() (line 1095); builder\'s report "46 Desert mine builder\'s report.md"',
    'views': 'reads from every side',
    'trap': '',
}

HEIGHT = 0.86
BILGE_R = 0.305        # outside of the staves at the middle
HEAD_R = 0.255         # outside of the staves at the ends
STAVE_T = 0.024
CHIME = 0.032          # how far the staves stand past the heads


def radius_at(z):
    t = (z - HEIGHT / 2) / (HEIGHT / 2)
    return HEAD_R + (BILGE_R - HEAD_R) * (1.0 - t * t)


def build(collection, seed=0, lying=False):
    rng = shapes.rng_for('barrel', seed)
    objects = []
    wood = shapes.surface_copy('rough_wood', 'barrel', Grime=0.6, Darken=0.52, **{'Mud height': 0.10})

    # ------------------------------------------------------------------ staves: each its own piece of oak
    count = rng.choice((20, 21, 22))
    gap = 0.0035                          # the dark joint between staves, as an angle's worth of arc at the bilge
    rings_z = [HEIGHT * k / 16 for k in range(17)]
    phase = rng.uniform(0, 2 * math.pi)
    sprung = rng.randrange(count)
    staves = []
    for i in range(count):
        a0 = phase + 2 * math.pi * i / count
        a1 = phase + 2 * math.pi * (i + 1) / count
        out = 0.004 if i == sprung else rng.uniform(-0.0012, 0.0012)
        dz = rng.uniform(-0.004, 0.004)
        stave = shapes.Shape()
        rings = []
        for z in rings_z:
            zz = min(max(z + (dz if 0 < z < HEIGHT else 0.0), 0.0), HEIGHT)
            r = radius_at(z) + out
            g = gap / r
            pts = []
            for (a, rr) in ((a0 + g, r), (a1 - g, r), (a1 - g, r - STAVE_T), (a0 + g, r - STAVE_T)):
                pts.append(Vector((rr * math.cos(a), rr * math.sin(a), zz)))
            # round the outer face across the stave: a middle point pushed out
            mid = (a0 + a1) / 2
            pts.insert(1, Vector(((r + 0.0015) * math.cos(mid), (r + 0.0015) * math.sin(mid), zz)))
            rings.append(stave._verts(pts))
        stave._rings(rings, True, True, True)
        mid = (a0 + a1) / 2
        frame = shapes.to4(Matrix.Rotation(mid, 3, 'Z'), (BILGE_R * math.cos(mid), BILGE_R * math.sin(mid), HEIGHT / 2))
        staves.append(stave.finish('barrel stave %d' % (i + 1), collection, wood, smooth=True, sharp=50, local=frame,
                                   shift=0.25, rng=rng))
    objects += staves

    # ------------------------------------------------------------------ heads: boards set in just inside the chimes
    for (zc, label) in ((CHIME, 'bottom'), (HEIGHT - CHIME, 'top')):
        r = radius_at(zc) - STAVE_T + 0.004
        boards = 4
        width = 2 * r / boards
        turn = rng.uniform(0, math.pi)
        for k in range(boards):
            x0 = -r + k * width + 0.002
            x1 = -r + (k + 1) * width - 0.002
            outline = []
            steps = 8
            for j in range(steps + 1):
                x = x0 + (x1 - x0) * j / steps
                outline.append((x, -math.sqrt(max(0.0, r * r - x * x))))
            for j in range(steps + 1):
                x = x1 - (x1 - x0) * j / steps
                outline.append((x, math.sqrt(max(0.0, r * r - x * x))))
            head = shapes.Shape()
            m = Matrix.Translation((0.0, 0.0, zc)) @ Matrix.Rotation(turn, 4, 'Z')
            head.prism(outline, -0.012, 0.012, m)
            # grain across the board: its own Z along the board
            along = Matrix.Rotation(turn, 3, 'Z') @ Vector((0.0, 1.0, 0.0))
            frame = shapes.to4(shapes.frame_along(along, up=(0.0, 0.0, 1.0)), (0.0, 0.0, zc))
            objects.append(head.finish('barrel head %s %d' % (label, k + 1), collection, wood, chamfer=0.002, local=frame,
                                       shift=0.25, rng=rng))

    # ------------------------------------------------------------------ the bung, in the bung stave at the bilge
    bung_angle = -math.pi / 2 if not lying else math.pi       # lying: local -X ends up on top
    bung_dir = Vector((math.cos(bung_angle), math.sin(bung_angle), 0.0))
    bung = shapes.Shape()
    base = bung_dir * (BILGE_R - 0.01) + Vector((0.0, 0.0, HEIGHT / 2))
    bung.lathe([(0.0, 0.0), (0.026, 0.0), (0.026, 0.020), (0.030, 0.024), (0.028, 0.030), (0.0, 0.031)], segments=16,
               matrix=shapes.to4(shapes.frame_along(bung_dir), base))
    objects.append(bung.finish('barrel bung', collection, wood, smooth=True, sharp=45))

    # ------------------------------------------------------------------ hoops: chime, quarter and bilge, riveted
    iron = shapes.Shape()
    for zc, w in ((0.042, 0.040), (0.165, 0.040), (0.335, 0.046), (HEIGHT - 0.335, 0.046), (HEIGHT - 0.165, 0.040), (HEIGHT - 0.042, 0.040)):
        zc += rng.uniform(-0.006, 0.006)
        z0, z1 = zc - w / 2, zc + w / 2
        r0, r1 = radius_at(z0) + 0.0005, radius_at(z1) + 0.0005
        prof = [(r0 - 0.002, z0), (r0 + 0.0032, z0), (r1 + 0.0032, z1), (r1 - 0.002, z1)]
        iron.lathe(prof, segments=64)
        a = rng.uniform(0, 2 * math.pi)
        for da in (0.0, 0.05):
            r = (r0 + r1) / 2 + 0.0035
            p = Vector((r * math.cos(a + da), r * math.sin(a + da), zc))
            iron.sphere(p, 0.0045, segments=8, rings=4)
    objects.append(iron.finish('barrel hoops', collection, RUST, smooth=True, sharp=40))

    if lying:
        # turn the barrel onto its side along X, resting on its bilge hoops, and chock it
        lift = BILGE_R + 0.0036
        turn = Matrix.Translation((0.0, 0.0, lift)) @ Matrix.Rotation(math.pi / 2, 4, 'Y') @ Matrix.Translation((0.0, 0.0, -HEIGHT / 2))
        roll = Matrix.Translation((0.0, 0.0, lift)) @ Matrix.Rotation(math.radians(rng.uniform(-6, 6)), 4, 'X') @ Matrix.Translation((0.0, 0.0, -lift))
        for obj in objects:
            obj.matrix_world = roll @ turn @ obj.matrix_world
        for sy in (-1, 1):
            chock = shapes.Shape()
            y0 = sy * 0.20
            y1 = sy * 0.36
            outline = [(y0, 0.0), (y1, 0.0), (y1, 0.03), (y0 + sy * 0.02, 0.0 + 0.11)]
            pts = [(p[0], p[1]) for p in outline]
            m = Matrix(((0, 0, 1), (1, 0, 0), (0, 1, 0))).to_4x4()          # outline in (y, z), thickness along x
            chock.prism(pts if sy > 0 else list(reversed(pts)), -0.06, 0.06, m)
            objects.append(chock.finish('barrel chock %s' % ('front' if sy < 0 else 'back'), collection, wood, chamfer=0.004))
    else:
        # standing: a slight lean on uneven ground
        lean = math.radians(rng.uniform(0.0, 1.2))
        direction = rng.uniform(0, 2 * math.pi)
        shapes.tilt_all(objects, rx=lean * math.cos(direction), ry=lean * math.sin(direction))
        lift = Matrix.Translation((0.0, 0.0, HEAD_R * math.sin(lean)))
        for obj in objects:
            obj.matrix_world = lift @ obj.matrix_world
    return objects
