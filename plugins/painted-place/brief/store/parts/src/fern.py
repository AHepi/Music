"""
fern: a clump of a woodland fern (a shield fern, as grows at the foot of rocks and water basins in Japanese gardens):
fronds rising from a dark crown of old frond bases and arching out and down, the inner ones young and upright, the
outer ones older, spread low with their tips near the ground; each frond a stalk with pairs of narrow pinnae angled
towards its tip, longest a third of the way up, each pinna with rounded lobes down both sides and a midrib; two young
fronds still curled at the middle (fiddleheads). Dark glossy green, see-through where the light is behind it, the old
fronds yellowing at their tips. The crown is at the origin, z = 0.

Options:
    size     the longest fronds' length in metres (default 0.7)
    fronds   how many fronds (default 12)
    seed     each frond's turn, arch and length, every pinna's shade

Where it came from: '/home/claude/build-57-garden/first pass/render_final.py', fern() (line 1468): fronds of thirteen
points arching from one spot with a triangle for each leaflet; rebuilt here with a crown, young upright and old spread
fronds, a lance-shaped frond (pinnae longest a third of the way up, short at the foot and tip), lobed pinnae with a
midrib, the frond's face turned up, fiddleheads, and yellowing tips on the old fronds.
"""

import math
import os
import sys

from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import _shapes_chapel as shapes  # noqa: E402
import _shapes_barn as barn  # noqa: E402
import _shapes_garden_plants as plants  # noqa: E402

PART = 'fern'
GREENS = [(0.0, (0.014, 0.042, 0.010)), (0.4, (0.028, 0.075, 0.016)), (0.75, (0.05, 0.10, 0.02)),
          (0.9, (0.13, 0.12, 0.035)), (1.0, (0.12, 0.06, 0.022))]

CARD = {
    'name': PART,
    'what': 'a clump of fern for the foot of rocks and basins: fronds arching out and down from a dark crown, young ones '
            'upright in the middle, old ones spread low; each frond pairs of lobed pinnae with a midrib, longest a third '
            'of the way up; two fiddleheads; dark glossy green, old tips yellowing',
    'size_m': (1.07, 1.14, 0.43),
    'options': {
        'size': 'the longest fronds length in metres (default 0.7; 0.3 for a small fern in a joint, 1.2 for a big clump)',
        'fronds': 'how many fronds (default 12; 5 to 25)',
        'seed': 'each frond turn, arch and length, every pinna shade (default 0)',
    },
    'materials': ['PART • fern: fronds', 'PART • fern: stalks', 'PART • fern: crown'],
    'source': "'/home/claude/build-57-garden/first pass/render_final.py', fern() (line 1468)",
    'views': 'reads from every side and from above; its fronds read by their outline against a paler stone or ground',
    'trap': 'its fronds reach out about as far as they are long and their tips lie a few millimetres over the ground: '
            'on bumpy ground some tips go under it; stand its crown in the joint between rock and ground, and keep it '
            'off a dark ground, where its dark green is lost',
}


def build(collection, seed=0, size=0.7, fronds=12):
    size = barn.number('fern size', size, 0.15, 2.5)
    fronds = int(round(barn.number('fern fronds', fronds, 3, 40)))
    rng = shapes.rng_for(PART, seed)
    k = size / 0.7
    blades = shapes.Shape()
    stalks = shapes.Shape()
    crown = shapes.Shape()
    outlines = [plants.pinna_outline(lobes) for lobes in (5, 6, 7)]

    # ------------------------------------------------------------------ the crown: a dark lump of old frond bases
    crown.rock((0.0, 0.0, 0.025 * k), 0.055 * k, rng, squash=(1.0, 1.0, 0.7), jitter=0.3)
    for _ in range(6):
        a = rng.uniform(0, 2 * math.pi)
        crown.rock((math.cos(a) * 0.04 * k, math.sin(a) * 0.04 * k, 0.03 * k), 0.025 * k, rng, squash=(0.6, 0.6, 1.2))

    # ------------------------------------------------------------------ the fronds
    golden = math.radians(137.5)
    az0 = rng.uniform(0, 2 * math.pi)
    for i in range(fronds):
        young = 1.0 - i / max(1, fronds - 1)              # the first fronds are the young inner ones
        az = az0 + i * golden + rng.uniform(-0.25, 0.25)
        elev = math.radians(42 + 38 * young + rng.uniform(-6, 6))
        length = size * rng.uniform(0.72, 1.0) * (0.8 + 0.2 * (1.0 - young))
        turn = math.radians(62 + 50 * (1.0 - young) + rng.uniform(-10, 10))     # how far the frond arches over
        out = Vector((math.cos(az), math.sin(az), 0.0))
        d = Vector((out.x * math.cos(elev), out.y * math.cos(elev), math.sin(elev)))
        axis = out.cross(Vector((0, 0, 1))).normalized()      # it arches over about this level axis
        steps = 16
        p = out * 0.03 * k + Vector((0, 0, 0.04 * k))
        pts = [p.copy()]
        for _ in range(steps):
            p = p + d * (length / steps)
            p.z = max(p.z, 0.006)
            pts.append(p.copy())
            d = Matrix.Rotation(-turn / steps, 3, axis) @ d
        radii = [(0.0042 - 0.0032 * j / steps) * k for j in range(steps + 1)]
        stalks.sweep(pts, 0.004 * k, sides=5, radii=radii)
        # the pinnae, in pairs, angled towards the tip; the frond's face turned up
        pairs = rng.randint(22, 27)
        tone = rng.uniform(0.15, 0.55) + 0.25 * (1.0 - young)
        for j in range(pairs):
            t = 0.12 + 0.86 * (j + 0.5) / pairs
            f = t * steps
            m = min(steps - 1, int(f))
            at = pts[m].lerp(pts[m + 1], f - m)
            tangent = (pts[m + 1] - pts[m]).normalized()
            side = tangent.cross(Vector((0, 0, 1)))
            if side.length < 1e-4:
                side = axis.copy()
            side.normalize()
            face_up = side.cross(tangent).normalized()
            if face_up.z < 0:
                face_up = -face_up
            # a lance-shaped frond: the pinnae longest a third of the way up, short at its foot and tip
            shape_f = (t / 0.38) ** 0.6 if t < 0.38 else ((1.0 - t) / 0.62) ** 0.85
            plen = length * 0.21 * max(0.12, shape_f) * rng.uniform(0.92, 1.08)
            for sd in (-1, 1):
                ang = math.radians(rng.uniform(58, 70))
                pd = (tangent * math.cos(ang) + side * sd * math.sin(ang) - face_up * 0.18).normalized()
                frame = plants.frame_from(pd, face_up + side * sd * 0.25)
                shade = tone + rng.uniform(-0.1, 0.1) + (0.35 * max(0.0, t - 0.82) / 0.18) * (1.0 - young)
                outline = outlines[min(2, int(plen / (0.05 * k)))] if plen > 0.02 * k else outlines[0]
                plants.leaf(blades, at + side * sd * 0.002, frame, plen, outline, min(1.0, max(0.0, shade)),
                            cup=0.15, curl=0.12, width=1.6)

    # ------------------------------------------------------------------ two fiddleheads still curled at the middle
    for q in range(2):
        a = az0 + rng.uniform(0, 2 * math.pi)
        lean = Vector((math.cos(a), math.sin(a), 0.0))
        height = size * rng.uniform(0.16, 0.26)
        base = lean * 0.02 * k + Vector((0, 0, 0.04 * k))
        stem = [base + lean * (height * 0.25 * (j / 6) ** 2) + Vector((0, 0, height * j / 6)) for j in range(7)]
        top = stem[-1]
        coil = []
        for j in range(1, 22):
            ang = j / 21 * 2.6 * math.pi
            r = 0.028 * k * (1.0 - 0.75 * j / 21)
            coil.append(top + lean * r * math.sin(ang) + Vector((0, 0, r * (1.0 - math.cos(ang)) * 0.9 - 0.0)))
        path = stem + coil
        radii = [0.005 * k] * len(stem) + [0.005 * k * (1.0 - 0.6 * j / 21) for j in range(1, 22)]
        stalks.sweep(path, 0.005 * k, sides=6, radii=radii)

    return [blades.finish('fern fronds', collection, plants.leaf_material(PART, 'fronds', GREENS, veins='pinnate',
                                                                          translucent=0.2, rough=0.5, coat=0.05, vein_light=0.4, specular=0.08),
                          smooth=False, normals=False),
            stalks.finish('fern stalks', collection, plants.plain_material(PART, 'stalks', (0.05, 0.06, 0.02), rough=0.5),
                          smooth=True, sharp=None),
            crown.finish('fern crown', collection, plants.plain_material(PART, 'crown', (0.035, 0.022, 0.012), rough=0.8),
                         smooth=True, sharp=None)]
