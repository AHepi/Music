"""
maple_tree: a Japanese maple (Acer palmatum) as it grows in a garden: a low trunk with a flared foot dividing a metre up
into several stems that rise and spread, then branch in opposite pairs into nearly level, layered branches whose tips
droop; at the ends of the twigs flat sprays of leaves, each leaf a real seven-lobed, toothed maple leaf (broad lobes,
so they do not read as stars), held face up like shingles, so the crown is a stack of lacy layers with the dark
branches showing between them. Smooth grey bark from the shelf's photograph. The trunk's foot is at the origin, z = 0.

Options:
    height     metres from the ground to the top of the crown (default 4.5)
    colour     'red' (default), 'orange' or 'green': the leaves
    fullness   how full the crown is (default 1.0)
    trunk      metres of clear trunk: from the ground to where the trunk divides into its stems and the crown starts
               (default 0: where it divides of itself, 0.7 to 1 m up at the default height). Given higher, the trunk runs
               up clear to that height and the crown sits on it unchanged, so the top rises by as much: a maple that has
               had its lower limbs taken off over a path, or grown on a single stem, its crown clear of what stands
               behind it (the third garden builder had to lift the whole tree 2 m into the air, its foot out of frame)
    seed       the whole tree: its stems, branches, sprays and every leaf's shade

Where it came from: '/home/claude/build-57-garden/first pass/render_final.py': maple_outline_fine() (line 1365, the
seven toothed lobes the builder found to read as maple leaves, after narrow lobes read as stars) and leaf_the_tree()
(line 1530, leaves strewn round the points of the store's bare_tree); rebuilt here as a maple: its own low,
many-stemmed, layered frame (the bare tree is an oak of the hedgerows, tall and upright), leaves gathered into flat
sprays at the twigs' ends instead of strewn round every branch, broader lobes cut half way, veins, and the shelf's
photographed bark instead of the made wet bark.
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

PART = 'maple_tree'

COLOURS = {
    'red': [(0.0, (0.16, 0.006, 0.005)), (0.35, (0.27, 0.012, 0.008)), (0.7, (0.42, 0.035, 0.010)),
            (0.88, (0.50, 0.11, 0.015)), (0.95, (0.30, 0.10, 0.025)), (1.0, (0.13, 0.05, 0.02))],
    'orange': [(0.0, (0.30, 0.035, 0.008)), (0.3, (0.46, 0.11, 0.012)), (0.65, (0.56, 0.21, 0.02)),
               (0.88, (0.60, 0.32, 0.04)), (0.95, (0.28, 0.12, 0.03)), (1.0, (0.14, 0.06, 0.02))],
    'green': [(0.0, (0.022, 0.05, 0.010)), (0.4, (0.04, 0.085, 0.015)), (0.85, (0.075, 0.12, 0.022)),
              (0.96, (0.12, 0.13, 0.025)), (0.985, (0.30, 0.06, 0.015)), (1.0, (0.30, 0.06, 0.015))],
}

CARD = {
    'name': PART,
    'what': 'a Japanese maple: a low trunk dividing into several spreading stems, branching in pairs into layered, nearly '
            'level branches drooping at their tips; flat sprays of real seven-lobed toothed leaves at the twig ends, so the '
            'crown reads as lacy layers with dark branches between; smooth grey bark (photographed)',
    'size_m': (6.08, 5.99, 4.53),
    'options': {
        'height': 'metres from the ground to the top of the crown (default 4.5; garden maples are 2.5 to 7, the crown '
                  'about one and a third times as wide as it is tall)',
        'colour': "'red' (default): crimson and scarlet leaves, a few orange and brown; 'orange': orange and amber, some "
                  "red; 'green': summer green, a few turning red",
        'fullness': 'how full the crown is: 1 a full crown, 0.5 thin with the branches showing, 0.2 nearly bare (default '
                    '1.0; 0.1 to 1.5)',
        'trunk': 'metres of clear trunk, from the ground to where it divides into its stems and the crown starts (default 0; 0 is '
                 'where it divides of itself, about 0.7 to 1.1 m up at the default height; given higher, the trunk runs up clear to there and the '
                 'crown sits on it unchanged, so the top rises by as much: height=4.5 with trunk=2.4 starts the crown at 2.4 m, its lowest '
                 'leaves just above, the top at about 5.9 m; a value under where it divides of itself changes nothing; 0 to 8)',
        'seed': 'the whole tree: its stems, branches, sprays and every leaf (default 0)',
    },
    'materials': ['SURFACE • bark_willow_02', 'PART • maple_tree: leaves, red', 'PART • maple_tree: leaves, orange',
                  'PART • maple_tree: leaves, green'],
    'source': "'/home/claude/build-57-garden/first pass/render_final.py', maple_outline_fine() (line 1365) and "
              "leaf_the_tree() (line 1530); the trunk option from '/home/claude/build-57-garden/closer/render_final.py' "
              "(line 1710), where the builder lifted the whole tree 2 m into the air by hand to get its crown clear",
    'views': 'reads from every side; its leaves read as maple leaves from about 6 m, nearer than that each one shows its '
             'lobes and veins; from far off the crown is a soft red layered mass',
    'trap': 'the leaves are single faces, about 10 cm long: from straight below or edge-on at eye height the layers thin '
            'out, and a crown against a dark ground loses its red; set it against the sky or a lit wall, and give it light '
            'from the side; a full maple is about 6,000 leaves (340,000 points): for trees far off, fullness=0.5 halves them; '
            'its crown hangs low (from about 1 m) over whatever stands behind it: give trunk= to lift it rather than lifting the tree',
}

LEAF = 0.1           # metres from a leaf's base to its middle lobe's tip (Acer palmatum: 5 to 12 cm)
OUTLINE = plants.maple_outline()


def _number(name, value, low, high):
    return barn.number(name, value, low, high)


def _bezier(a, c, b, count):
    return [a * (1 - t) ** 2 + c * 2 * t * (1 - t) + b * t * t for t in (k / count for k in range(count + 1))]


def _lift(wood, foliage, divides, trunk, foot, lean):
    """Stretch the trunk between `foot` (its flare kept as it is) and where it divides up to `trunk`, and lift
    everything above it (stems, branches, leaves) by the difference, unchanged: the crown on a taller clear trunk. The
    taller trunk is a little thicker (a quarter more for 2 m of lift), as a tree carrying its crown higher grows it."""
    lift = trunk - divides
    stretch = (trunk - foot) / max(divides - foot, 1e-6)
    thicker = 1.0 + 0.25 * min(lift / 2.0, 1.0)
    for v in wood.bm.verts:
        z = v.co.z
        if z < divides:
            grow = 1.0 + (thicker - 1.0) * min(1.0, max(0.0, (divides - z) / 0.12))
            centre_x, centre_y = lean.x * max(z, 0.0), lean.y * max(z, 0.0)          # the trunk was built along lean * z
            v.co.x = centre_x + (v.co.x - centre_x) * grow
            v.co.y = centre_y + (v.co.y - centre_y) * grow
    for shape in (wood, foliage):
        for v in shape.bm.verts:
            z = v.co.z
            if z >= divides:
                v.co.z = z + lift
            elif z > foot:
                v.co.z = foot + (z - foot) * stretch


def build(collection, seed=0, height=4.5, colour='red', fullness=1.0, trunk=0.0):
    height = _number('maple_tree height', height, 1.5, 12.0)
    fullness = _number('maple_tree fullness', fullness, 0.05, 2.0)
    clear_trunk = _number('maple_tree trunk', trunk, 0.0, 8.0)      # (the name trunk is taken below by the trunk's points)
    if colour not in COLOURS:
        raise ValueError("maple_tree colour is 'red', 'orange' or 'green', not %r" % (colour,))
    rng = shapes.rng_for(PART, seed)
    s = height / 4.5
    wood = shapes.Shape()
    foliage = shapes.Shape()
    sprays = []                                         # (point, outward direction, size) where leaves gather

    def jitter(amount):
        return Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))) * amount

    def limb(points, r0, r1, sides):
        n = len(points)
        radii = [r0 + (r1 - r0) * (k / (n - 1)) ** 0.8 for k in range(n)]
        plants.tagged(wood, lambda: wood.sweep(points, r0, sides=sides, radii=radii), piece=rng.random())
        return radii

    # ------------------------------------------------------------------ the trunk: low, flared at its foot, leaning a little
    split = height * rng.uniform(0.15, 0.22)
    r_trunk = 0.08 * s * rng.uniform(0.9, 1.1)
    lean = Vector((rng.uniform(-0.12, 0.12), rng.uniform(-0.12, 0.12), 1.0)).normalized()
    trunk = []
    trunk_r = []
    for k in range(9):
        t = k / 8
        z = -0.03 + (split + 0.05) * t
        p = lean * z
        p.z = z
        trunk.append(p)
        trunk_r.append(r_trunk * (1.0 + 0.6 * math.exp(-max(z, 0.0) / (0.18 * s))) * (1.0 - 0.12 * t))
    plants.tagged(wood, lambda: wood.sweep(trunk, r_trunk, sides=12, radii=trunk_r), piece=rng.random())
    for v in wood.bm.verts:                                      # the foot's tilted first ring cut level just under the ground
        v.co.z = max(v.co.z, -0.03)
    top = trunk[-1]

    # ------------------------------------------------------------------ the stems, each rising then spreading towards its own part of the crown
    stems = rng.randint(3, 5)
    width = height * rng.uniform(0.64, 0.74)            # the crown's half width
    az0 = rng.uniform(0, 2 * math.pi)
    for i in range(stems):
        az = az0 + 2 * math.pi * i / stems + rng.uniform(-0.35, 0.35)
        out = Vector((math.cos(az), math.sin(az), 0.0))
        reach = width * rng.uniform(0.55, 0.85) if i else width * 0.18
        rise = height * rng.uniform(0.55, 0.76) if i else height * 0.86
        start = top - Vector((0, 0, rng.uniform(0.0, 0.15) * s)) + out * r_trunk * 0.3
        end = Vector((top.x, top.y, 0.0)) + out * reach + Vector((0, 0, rise))
        ctrl = start + Vector((0, 0, (end.z - start.z) * (0.5 if i else 0.75))) + out * reach * 0.3
        pts = _bezier(start, ctrl, end, 10)
        pts = [p + (jitter(0.06 * s) if 0 < k < len(pts) - 1 else Vector()) for k, p in enumerate(pts)]
        r_stem = r_trunk * (1.0 / stems) ** (1 / 2.4) * 0.95
        radii = limb(pts, r_stem, 0.012 * s, 8)
        # branches in opposite pairs along the stem, nearly level, drooping at their tips: the layers
        sprays.append((pts[-1], (pts[-1] - pts[-2]).normalized(), 0.3 * s))
        pairs = rng.randint(5, 7)
        for j in range(pairs):
            t = 0.25 + 0.7 * (j + rng.uniform(0.0, 0.6)) / pairs
            k = min(len(pts) - 2, int(t * (len(pts) - 1)))
            base = pts[k].lerp(pts[k + 1], t * (len(pts) - 1) - k)
            axis = (pts[k + 1] - pts[k]).normalized()
            r_here = radii[k]
            across = axis.cross(Vector((0, 0, 1)))
            if across.length < 1e-3:
                across = Vector((1, 0, 0))
            across.normalize()
            turn = Matrix.Rotation((j % 2) * math.radians(rng.uniform(50, 90)), 3, axis)
            for side in (-1, 1):
                d = (turn @ across) * side
                d = Vector((d.x, d.y, 0.0)).normalized() * 0.8 + out * 0.6
                d = Vector((d.x, d.y, 0.0)).normalized()
                length = (0.8 + 1.1 * (1.0 - t)) * s * rng.uniform(0.75, 1.15)
                if base.z + 0.2 > height * 0.95:
                    length *= 0.6
                lift = rng.uniform(0.12, 0.3)
                tip = base + d * length + Vector((0, 0, length * (lift - 0.32)))
                ctrl = base + d * length * 0.5 + Vector((0, 0, length * lift))
                bpts = _bezier(base, ctrl, tip, 6)
                bpts = [p + (jitter(0.03 * s) if 0 < m < len(bpts) - 1 else Vector()) for m, p in enumerate(bpts)]
                br = limb(bpts, max(0.006 * s, r_here * 0.42), 0.0035 * s, 6)
                # twigs in pairs along the branch's outer half, fanning in its own level plane
                twigs = rng.randint(3, 4)
                for q in range(twigs):
                    tq = 0.3 + 0.6 * (q + rng.uniform(0.0, 0.7)) / twigs
                    m = min(len(bpts) - 2, int(tq * (len(bpts) - 1)))
                    tb = bpts[m].lerp(bpts[m + 1], tq * (len(bpts) - 1) - m)
                    ax = (bpts[m + 1] - bpts[m]).normalized()
                    level_across = Vector((-ax.y, ax.x, 0.0)).normalized()
                    for sd in (-1, 1):
                        td = (ax * 0.55 + level_across * sd * 0.85)
                        td = Vector((td.x, td.y, rng.uniform(-0.1, 0.12))).normalized()
                        tl = length * rng.uniform(0.28, 0.45)
                        tt = tb + td * tl + Vector((0, 0, -tl * rng.uniform(0.05, 0.22)))
                        tpts = _bezier(tb, tb + td * tl * 0.5 + Vector((0, 0, tl * 0.08)), tt, 3)
                        limb(tpts, max(0.004 * s, br[m] * 0.6), 0.0022 * s, 4)
                        sprays.append((tt, td, tl))
                sprays.append((tip, d, length * 0.35))

    # ------------------------------------------------------------------ the leaves: flat sprays round each twig's end, face up like shingles
    for (tip, d, reach) in sprays:
        count = int(round(fullness * rng.uniform(9, 14)))
        spray_tone = rng.uniform(-0.15, 0.15)
        across = Vector((-d.y, d.x, 0.0)).normalized()
        for _ in range(count):
            back = rng.uniform(0.0, min(0.42, reach * 1.1))
            spread = rng.uniform(-1.0, 1.0) * (0.12 + back * 0.5)
            centre = tip - d * back + across * spread + Vector((0, 0, rng.uniform(-0.04, 0.03) - back * 0.06))
            along = (d * rng.uniform(0.6, 1.0) + across * (spread * 1.5 + rng.uniform(-0.5, 0.5)) + Vector((0, 0, rng.uniform(-0.35, 0.05))))
            up = Vector((rng.uniform(-0.35, 0.35), rng.uniform(-0.35, 0.35), 1.0)) + d * 0.25
            frame = plants.frame_from(along, up)
            size = LEAF * rng.uniform(0.75, 1.15) * (0.9 + 0.1 * s)
            tone = min(0.93, max(0.0, rng.random() ** 0.9 * 0.93 + spray_tone * 0.6))
            if rng.random() < 0.04:
                tone = rng.uniform(0.94, 1.0)                # an odd leaf turning early, or gone brown
            plants.leaf(foliage, centre, frame, size, OUTLINE, tone, cup=-0.12, width=rng.uniform(0.9, 1.05))

    # ------------------------------------------------------------------ the crown's top exactly at the height asked for
    reach = max(max(v.co.z for v in wood.bm.verts), max((v.co.z for v in foliage.bm.verts), default=0.0))
    k = 1.0
    if reach > 0.0:
        k = height / reach
        scale = Matrix.Diagonal((k, k, k, 1.0))
        wood.transform(scale)
        foliage.transform(scale)
    # ------------------------------------------------------------------ a taller clear trunk, if asked: the crown lifted whole
    divides = split * k                                  # where the trunk divides, after the fit
    if clear_trunk > divides + 1e-6:
        _lift(wood, foliage, divides, clear_trunk, min(0.3 * s * k, 0.5 * divides), lean)
    bark = plants.bark(PART, 'smooth bark', Scale=0.45, Normal=0.5, Darken=0.42, Wet=0.5)
    leaves = plants.leaf_material(PART, 'leaves, ' + colour, COLOURS[colour], veins='palmate', spacing=50.0,
                                  translucent=0.15, rough=0.6, coat=0.04, specular=0.05)
    made = [wood.finish('maple_tree wood', collection, bark, smooth=True, sharp=None)]
    if not foliage.empty():
        made.append(foliage.finish('maple_tree leaves', collection, leaves, smooth=False, normals=False))
    return made
