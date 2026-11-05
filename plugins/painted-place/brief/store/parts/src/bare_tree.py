"""
bare_tree: a broadleaf tree in winter (an oak, ash or elm of the hedgerows), as seen beyond a field: a trunk with a
flared, lobed foot and a slight lean, splitting at a third of its height into a few great limbs, each forking again and
again into branches that bend and taper, down to fine twigs that make the crown's edge a soft net against the sky.
Every piece is a branch: no blobs, no leaves. Wet dark bark. The trunk's foot is at the origin, z = 0.

Options:
    height   metres to the top of the crown (default 12; hedgerow trees are 8 to 20)
    seed     the whole tree: where it splits, how its limbs spread and bend, the crown's lean

Where it came from: '/home/claude/build-54-barn/first pass/render_final.py', tree() (line 765): a recursive tree of
straight six-sided cones forking in twos and threes at the same angles; rebuilt here with curved, tapering branches that
keep the thickness of their parent where they fork, branches springing all along each limb (not only at its end), a
flared foot, and fine twigs at the crown's edge.
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

PART = 'bare_tree'
BARK = 'MADE • wet bark'

CARD = {
    'name': PART,
    'what': 'a bare winter tree as seen beyond a field: trunk with a flared foot, great limbs forking again and again into curved tapering '
            'branches and fine twigs (no blobs, no leaves), wet dark bark',
    'size_m': (10.5, 8.7, 12.0),
    'options': {
        'height': 'metres to the top of the crown (default 12; hedgerow trees are 8 to 20)',
        'seed': 'the whole tree: where it splits, how its limbs spread and bend, the lean of its crown (default 0)',
    },
    'materials': [BARK],
    'source': "'/home/claude/build-54-barn/first pass/render_final.py', tree() (line 765)",
    'views': 'reads from every side; made to be seen from 30 m and more, its twigs a fine net against the sky',
    'trap': 'its twigs are a few millimetres thick: against a dark sky or in a small, low-sample render the crown thins to its big limbs; '
            'set it against the lighter sky low down',
}

SIDES = [12, 9, 7, 5, 4, 3]
STEP = [0.6, 0.5, 0.35, 0.25, 0.16, 0.1]          # metres between rings, by level (at 12 m)
WIGGLE = [0.05, 0.13, 0.2, 0.28, 0.34, 0.4]
RISE = [0.0, 0.05, 0.04, 0.07, 0.11, 0.14]        # how much each level bends towards the light (up)
LATERALS = [0, 8, 8, 7, 5, 0]                     # branches springing from an axis of each level


def build(collection, seed=0, height=12.0):
    height = barn.number('bare_tree height', height, 2.0, 40.0)
    rng = shapes.rng_for(PART, seed)
    s = height / 12.0
    shape = shapes.Shape()
    split = height * rng.uniform(0.27, 0.38)            # where the trunk breaks into limbs
    spread = height * rng.uniform(0.35, 0.42)           # the crown's half width
    lean = Vector((rng.uniform(-0.07, 0.07), rng.uniform(-0.07, 0.07), 1.0)).normalized()
    centre = Vector((lean.x * height * 0.3, lean.y * height * 0.3, (split + height) / 2.0))
    half_h = (height - split) / 2.0 * 1.08

    def inside(p):
        """How far out a point is in the crown's envelope: 1 on its skin."""
        d = p - centre
        return math.sqrt((d.x / spread) ** 2 + (d.y / spread) ** 2 + (max(d.z, -half_h * 2) / half_h) ** 2)

    def random_unit():
        while True:
            v = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1)))
            if 0.05 < v.length <= 1.0:
                return v.normalized()

    def path(start, direction, length, level):
        step = STEP[level] * s
        count = max(2, int(math.ceil(length / step)))
        pts = [Vector(start)]
        d = Vector(direction).normalized()
        for k in range(count):
            d = (d + random_unit() * WIGGLE[level] + Vector((0, 0, RISE[level]))).normalized()
            if level == 1 and k > count * 0.6:
                d = (d + Vector((0, 0, -0.04))).normalized()        # long limbs droop a little at their ends
            pts.append(pts[-1] + d * (length / count))
        return pts

    def grow(start, direction, length, radius, level):
        if radius < 0.0014 * max(1.0, s * 0.8) or level >= len(SIDES):
            return
        pts = path(start, direction, length, level)
        # keep the crown inside its envelope: a branch whose end is far outside is shortened once
        reach = inside(pts[-1])
        if level >= 2 and reach > 1.0:
            length *= max(0.35, 1.0 / reach)
            pts = path(start, direction, length, level)
        n = len(pts)
        end_r = radius * (0.32 if level >= 3 else 0.42)
        radii = [radius + (end_r - radius) * (k / (n - 1)) ** 0.9 for k in range(n)]
        if level >= 4:
            radii[-1] = radius * 0.25
        shape.sweep(pts, radius, sides=SIDES[level], radii=radii)
        lateral = LATERALS[level] if level < len(LATERALS) else 0
        if lateral == 0:
            return
        phi = rng.uniform(0, 2 * math.pi)
        for k in range(lateral):
            t = 0.22 + 0.74 * (k + rng.uniform(0.1, 0.9)) / lateral
            i = min(n - 2, int(t * (n - 1)))
            f = t * (n - 1) - i
            base = pts[i].lerp(pts[i + 1], f)
            axis = (pts[i + 1] - pts[i]).normalized()
            r_here = radii[i] + (radii[i + 1] - radii[i]) * f
            phi += math.radians(137.5 + rng.uniform(-20, 20))
            side = axis.cross(Vector((0, 0, 1)))
            if side.length < 1e-3:
                side = axis.cross(Vector((1, 0, 0)))
            side.normalize()
            side = Matrix.Rotation(phi, 3, axis) @ side
            angle = math.radians(rng.uniform(32, 62))
            child_dir = (axis * math.cos(angle) + side * math.sin(angle)).normalized()
            ratio = rng.uniform(0.5, 0.72)
            child_r = r_here * ratio
            child_len = length * rng.uniform(0.42, 0.7) * (1.0 - 0.35 * t)
            grow(base - axis * min(r_here * 0.5, 0.02), child_dir, child_len, child_r, level + 1)

    # ------------------------------------------------------------------ the trunk: a flared, lobed foot, a slight lean and bend
    r0 = 0.033 * height * rng.uniform(0.88, 1.12)
    trunk_pts = []
    trunk_r = []
    rings = 12
    bend = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), 0.0)) * 0.03 * height
    top = split * 1.12
    for k in range(rings + 1):
        t = k / rings
        z = -0.03 + top * t
        p = lean * z + bend * math.sin(math.pi * t) * 0.5
        p.z = z
        trunk_pts.append(p)
        flare = 1.0 + 0.55 * math.exp(-z / (0.35 * s)) if z > 0 else 1.55
        trunk_r.append(r0 * flare * (1.0 - 0.3 * t))
    # the foot: lobes (the roots' shoulders) round the bottom metre
    lobes = rng.randint(4, 6)
    lobe_phase = rng.uniform(0, 2 * math.pi)
    section_rings = []
    for k, (p, r) in enumerate(zip(trunk_pts, trunk_r)):
        ring = []
        z = p.z
        for j in range(16):
            a = 2 * math.pi * j / 16
            lobe = 1.0 + 0.22 * max(0.0, math.cos(lobes * a + lobe_phase)) ** 2 * math.exp(-max(z, 0.0) / (0.5 * s))
            bark = 1.0 + 0.03 * math.sin(a * 7 + z * 3.0)
            ring.append(Vector((p.x + math.cos(a) * r * lobe * bark, p.y + math.sin(a) * r * lobe * bark, z)))
        section_rings.append(shape._verts(ring))
    shape._rings(section_rings, True, True, True)
    # two or three old stubs where limbs broke off long ago
    for _ in range(rng.randint(1, 3)):
        t = rng.uniform(0.35, 0.85)
        i = int(t * rings)
        out = Vector((math.cos(rng.uniform(0, 6.3)), math.sin(rng.uniform(0, 6.3)), rng.uniform(0.2, 0.6))).normalized()
        shape.cylinder(trunk_pts[i], trunk_pts[i] + out * (trunk_r[i] + 0.25 * s), trunk_r[i] * 0.35, trunk_r[i] * 0.28, segments=7)

    # ------------------------------------------------------------------ the great limbs from the top of the trunk, then all the rest
    limbs = rng.randint(3, 5)
    r_top = trunk_r[-1]
    weights = [rng.uniform(0.7, 1.3) for _ in range(limbs)]
    total = sum(weights)
    az0 = rng.uniform(0, 2 * math.pi)
    for k in range(limbs):
        w = weights[k] / total
        r = r_top * w ** (1.0 / 2.4) * 0.95
        az = az0 + 2 * math.pi * k / limbs + rng.uniform(-0.35, 0.35)
        up = math.radians(rng.uniform(22, 48)) if k else math.radians(rng.uniform(5, 18))     # one limb carries on as a leader
        d = Vector((math.cos(az) * math.sin(up), math.sin(az) * math.sin(up), math.cos(up)))
        start = trunk_pts[-1] - Vector((0, 0, top * 0.12 * (k / limbs)))
        length = (height - split) * rng.uniform(0.62, 0.8) / max(0.75, math.cos(up))
        grow(start, d, length, r, 1)
    # the crown's top exactly at the height asked for (the twigs reach a little past the envelope)
    reach = max(v.co.z for v in shape.bm.verts)
    if reach > 0.0:
        shape.transform(Matrix.Diagonal((height / reach, height / reach, height / reach, 1.0)))
    return [shape.finish('bare_tree', collection, BARK, smooth=True, sharp=None)]
