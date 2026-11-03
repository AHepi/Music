"""
winding_tower: a timber mine headframe (pithead winding tower) about 15.5 m high. Four battered legs on timber
footings, tied by girts at four levels and X-braced on every face (the lowest panel of the front left open, for the
shaft), standing over the shaft mouth and its timber collar. On top, a planked deck with a handrail carries two
cast-iron sheave wheels (2.9 m across) on one axle, in bearings on A-frames; a wire rope runs over each wheel and
straight down into the shaft. Two heavy back stays lean from the bearings down towards -X, where the hoist house would
stand, braced to the tower and to each other. A ladder climbs the front face in two flights with a landing between.
Iron bolts at the joints.

The wheels turn in the XZ plane, so they are seen round from the front (-Y) and the back, edge-on from the sides.
The tower's legs stand round the origin; the back stays reach about 9.9 m out along -X.

Options:
    back_stays   True (default): the two back stays and their bracing; False: the tower alone (a plain gallows frame).
    hoist_rope   0 (default): the ropes run up the shaft and over the wheels only. A distance in metres: the ropes
                 also run from the wheel tops down towards -X to a point that far from the shaft, 2.5 m up, where a
                 hoist house's drum would be (turn the tower so its -X faces your hoist house).

Where it came from: "46 desert-mine - render_final.py" (procedural-textures/46 Pictures-only builders - three places),
headframe() (line 846): a scaled frame of square beams, bearings and spoked wheels for one camera, with the ropes
landing outside the shaft; rebuilt here at real timber sizes with the ropes into the shaft, a deck, handrails,
ladders, a landing, footings and bolts.
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
RECESS = 'RECESSES • near-black blue'

CARD = {
    'name': 'winding_tower',
    'what': 'a timber mine headframe ~15.5 m: braced legs, deck, two sheave wheels with ropes into the shaft, back stays to -X, ladder and landing',
    'size_m': (12.6, 4.7, 15.43),
    'options': {
        'back_stays': 'True (default): two back stays lean from the wheels down towards -X (about 9.9 m out); False: the tower alone',
        'hoist_rope': '0 (default): ropes over the wheels and down the shaft only; a distance in metres: ropes also run towards -X to a hoist drum that far away, 2.5 m up',
    },
    'materials': ['SURFACE • rough_wood (winding_tower)', 'SURFACE • old_planks_02 (winding_tower)', RUST, RECESS,
                  'PART • winding_tower: greased wire rope'],
    'source': '"46 desert-mine - render_final.py", headframe() (line 846); builder\'s report "46 Desert mine builder\'s report.md"',
    'views': 'reads from every side; the wheels read round from front and back, as thin discs from the sides',
    'trap': 'the origin is the shaft and tower, not the middle of the footprint: the back stays reach 9.9 m along -X',
}

TOP = 12.0                     # the top girts (the deck sits on them)
LEVELS = [0.40, 3.30, 6.30, 9.20, TOP]
BASE_HALF = (2.10, 1.80)       # leg centres at the ground
TOP_HALF = (1.00, 1.25)        # leg centres at the top
LEG = 0.30
GIRT = (0.25, 0.20)            # depth (in the face), thickness (out of it)
BRACE = (0.20, 0.13)
AXLE = Vector((-0.60, 0.0, 13.95))
WHEEL_R = 1.40                 # to the bottom of the rope groove
WHEEL_Y = 0.55
ROPE_R = 0.019


def half_at(z):
    t = z / TOP
    return (BASE_HALF[0] + (TOP_HALF[0] - BASE_HALF[0]) * t, BASE_HALF[1] + (TOP_HALF[1] - BASE_HALF[1]) * t)


def corner(sx, sy, z):
    hx, hy = half_at(z)
    return Vector((sx * hx, sy * hy, z))


def face_normal(face):
    """Outward normal of a battered face: 'front' (-Y), 'back' (+Y), 'left' (-X), 'right' (+X)."""
    dx = (TOP_HALF[0] - BASE_HALF[0]) / TOP
    dy = (TOP_HALF[1] - BASE_HALF[1]) / TOP
    if face == 'front':
        return Vector((0.0, -1.0, -dy)).normalized()
    if face == 'back':
        return Vector((0.0, 1.0, -dy)).normalized()
    if face == 'left':
        return Vector((-1.0, 0.0, -dx)).normalized()
    return Vector((1.0, 0.0, -dx)).normalized()


FACES = {  # the two corners (sx, sy) of each face, left to right seen from outside
    'front': ((-1, -1), (1, -1)),
    'right': ((1, -1), (1, 1)),
    'back': ((1, 1), (-1, 1)),
    'left': ((-1, 1), (-1, -1)),
}


def _rope(m, nodes, links, principled):
    vec = shapes.own_coordinates(nodes)
    strands = nodes.new('ShaderNodeTexWave')
    strands.wave_type = 'BANDS'
    strands.bands_direction = 'DIAGONAL'
    strands.inputs['Scale'].default_value = 60.0
    links.new(vec, strands.inputs['Vector'])
    grease = shapes.noise_fac(nodes, links, vec, 3.0, detail=4.0)
    links.new(shapes.mix_colour(nodes, links, grease, (0.016, 0.016, 0.015), (0.045, 0.036, 0.026)), principled.inputs['Base Color'])
    principled.inputs['Metallic'].default_value = 0.55
    links.new(shapes.map_range(nodes, links, grease, 0.2, 0.8, 0.32, 0.6), principled.inputs['Roughness'])
    links.new(shapes.bump(nodes, links, strands.outputs['Fac'], 0.5, 0.003), principled.inputs['Normal'])
    m.diffuse_color = (0.02, 0.02, 0.02, 1.0)


def build(collection, seed=0, back_stays=True, hoist_rope=0.0):
    rng = shapes.rng_for('winding_tower', seed)
    objects = []
    wood = shapes.surface_copy('rough_wood', 'winding_tower', Grime=0.5, Darken=0.6, **{'Mud height': 0.45})
    planks = shapes.surface_copy('old_planks_02', 'winding_tower', Grime=0.45, Darken=0.7)
    iron = shapes.Shape()           # bolts, straps, bearings, axle, wheels: one rusty iron object
    count = [0]

    def wood_piece(label, a, b, width, height, up=shapes.UP, extend=0.0, material=None, chamfer=0.012):
        count[0] += 1
        jitter = Vector((rng.uniform(-0.01, 0.01), rng.uniform(-0.01, 0.01), 0.0))
        obj = shapes.timber(collection, 'winding_tower %s %d' % (label, count[0]), Vector(a) + jitter, Vector(b) + jitter,
                            width, height, material or wood, rng=rng, up=up, extend=extend, chamfer=chamfer,
                            roll=math.radians(rng.uniform(-0.8, 0.8)))
        objects.append(obj)
        return obj

    def bolts(at, normal, along, spacing=0.09, n=2, r=0.024):
        """Bolt heads (with washers) on a timber's outer face at `at`, in a row along `along`."""
        along = Vector(along).normalized()
        for k in range(n):
            p = Vector(at) + along * spacing * (k - (n - 1) / 2)
            iron.cylinder(p - normal * 0.004, p + normal * 0.006, r * 1.5, segments=10)
            iron.cylinder(p, p + normal * 0.028, r, segments=6)

    # ------------------------------------------------------------------ footings and legs
    for sx in (-1, 1):
        for sy in (-1, 1):
            foot = corner(sx, sy, 0.0)
            for k, (lx, ly) in enumerate(((0.80, 0.34), (0.34, 0.80))):
                z = 0.10 + 0.20 * k
                wood_piece('footing', foot + Vector((-lx / 2, 0, z)) if lx > ly else foot + Vector((0, -ly / 2, z)),
                           foot + Vector((lx / 2, 0, z)) if lx > ly else foot + Vector((0, ly / 2, z)),
                           0.34 if lx > ly else 0.20, 0.20 if lx > ly else 0.34, chamfer=0.02)
            a = corner(sx, sy, 0.40)
            b = corner(sx, sy, TOP + 0.15)
            wood_piece('leg', a, b, LEG, LEG, up=(0.0, 1.0, 0.0))

    # ------------------------------------------------------------------ girts at every level, braces in every panel
    for face, ((ax, ay), (bx, by)) in FACES.items():
        n = face_normal(face)
        for z in LEVELS:
            a = corner(ax, ay, z)
            b = corner(bx, by, z)
            wood_piece('girt', a, b, GIRT[0], GIRT[1], up=n, extend=LEG / 2 - 0.02)
        for i, (z0, z1) in enumerate(zip(LEVELS[:-1], LEVELS[1:])):
            if face == 'front' and i == 0:
                continue                    # the shaft side's lowest panel stays open
            off = n * (LEG / 2 + BRACE[1] / 2)
            p00, p10 = corner(ax, ay, z0) + off, corner(bx, by, z0) + off
            p01, p11 = corner(ax, ay, z1) + off, corner(bx, by, z1) + off
            for (s, e) in ((p00, p11), (p10, p01)):
                d = (e - s).normalized()
                s2, e2 = s + d * 0.10, e - d * 0.10
                wood_piece('brace', s2, e2, BRACE[0], BRACE[1], up=n)
                for end, inward in ((s2, d), (e2, -d)):
                    bolts(end + inward * 0.22 + n * (BRACE[1] / 2), n, n.cross(d))
            mid = (p00 + p11) / 2 + n * (BRACE[1] / 2 + 0.002)
            bolts(mid, n, Vector((0, 0, 1)), n=1)

    # ------------------------------------------------------------------ the deck: planks on the top girts, handrail
    deck_z = TOP + GIRT[0] / 2
    rope_x = AXLE.x + WHEEL_R
    x = -1.22
    while x < 1.22:
        w = rng.uniform(0.20, 0.26)
        centre = x + w / 2
        if abs(centre - rope_x) > (w / 2 + 0.10):
            wood_piece('deck plank', (centre, -1.36, deck_z + 0.025), (centre, 1.36, deck_z + 0.025), w - 0.012, 0.05,
                       material=planks, chamfer=0.006)
        x += w
    rail_h = 1.0
    posts = [(-1.24, -1.40), (-0.30, -1.40), (1.24, -1.40), (-1.24, 1.40), (0.0, 1.40), (1.24, 1.40), (-1.24, 0.0), (1.24, 0.0)]
    for (px, py) in posts:
        wood_piece('rail post', (px, py, deck_z), (px, py, deck_z + rail_h + 0.05), 0.09, 0.09, chamfer=0.008)
    for h in (rail_h, rail_h * 0.5):
        z = deck_z + h
        wood_piece('handrail', (-1.24, 1.40, z), (1.24, 1.40, z), 0.08, 0.06, extend=0.05, chamfer=0.008)
        wood_piece('handrail', (-1.24, -1.40, z), (-1.24, 1.40, z), 0.08, 0.06, extend=0.05, chamfer=0.008)
        wood_piece('handrail', (1.24, -1.40, z), (1.24, 1.40, z), 0.08, 0.06, extend=0.05, chamfer=0.008)
        wood_piece('handrail', (-1.24, -1.40, z), (-0.30, -1.40, z), 0.08, 0.06, extend=0.05, chamfer=0.008)
        wood_piece('handrail', (0.62, -1.40, z), (1.24, -1.40, z), 0.08, 0.06, extend=0.05, chamfer=0.008)
    wood_piece('rail post', (0.62, -1.40, deck_z), (0.62, -1.40, deck_z + rail_h + 0.05), 0.09, 0.09, chamfer=0.008)

    # ------------------------------------------------------------------ sheave beams and A-frames carrying the bearings
    beam_top = deck_z + 0.05 + 0.30
    bearing_z = AXLE.z - 0.16
    for sy in (-1, 1):
        y = sy * 1.12
        wood_piece('sheave beam', (-1.30, y, deck_z + 0.20), (1.30, y, deck_z + 0.20), 0.30, 0.30, chamfer=0.015)
        for xl in (AXLE.x - 0.62, AXLE.x + 0.62):
            wood_piece('A-frame leg', (xl, y, beam_top - 0.05), (AXLE.x + (0.08 if xl > AXLE.x else -0.08), y, bearing_z - 0.05),
                       0.24, 0.24, up=(0.0, 1.0, 0.0))
        wood_piece('A-frame tie', (AXLE.x - 0.45, y + sy * 0.0, beam_top + 0.45), (AXLE.x + 0.45, y, beam_top + 0.45), 0.16, 0.12,
                   up=(0.0, sy, 0.0), extend=0.02)
        # the bearing: a cast block on a sole plate, with its cap and four bolts
        iron.box((AXLE.x, y, bearing_z - 0.06), (0.62, 0.30, 0.04))
        iron.box((AXLE.x, y, bearing_z + 0.04), (0.36, 0.24, 0.16))
        iron.box((AXLE.x, y, AXLE.z + 0.075), (0.30, 0.20, 0.07))
        for bx in (-0.13, 0.13):
            for by in (-0.07, 0.07):
                iron.cylinder((AXLE.x + bx, y + by, AXLE.z + 0.11), (AXLE.x + bx, y + by, AXLE.z + 0.15), 0.02, segments=6)
    iron.cylinder((AXLE.x, -1.32, AXLE.z), (AXLE.x, 1.32, AXLE.z), 0.075, segments=16)

    # ------------------------------------------------------------------ the sheave wheels: grooved rims, spokes, hubs
    wheels = shapes.Shape()
    groove = [(0.16, 0.0), (0.16, 0.05), (0.06, 0.03), (0.0, 0.0), (0.06, -0.03), (0.16, -0.05)]   # (out from groove bottom, across)
    for sy in (-1, 1):
        yw = sy * WHEEL_Y
        ring = []
        for k in range(72):
            a = 2 * math.pi * k / 72
            ring.append((AXLE.x + WHEEL_R * math.cos(a), yw, AXLE.z + WHEEL_R * math.sin(a)))
        # the rim: a section with the rope groove facing out, swept round
        section = []
        for (out, across) in groove:
            section.append((across, out))
        rim = []
        for k in range(72):
            a = 2 * math.pi * k / 72
            rim.append(Vector((AXLE.x + (WHEEL_R - 0.10) * math.cos(a), yw, AXLE.z + (WHEEL_R - 0.10) * math.sin(a))))
        # build the rim by hand: rings of the groove section round the circle
        rings = []
        for k in range(72):
            a = 2 * math.pi * k / 72
            radial = Vector((math.cos(a), 0.0, math.sin(a)))
            pts = []
            for (out, across) in ((-0.10, 0.07), (0.08, 0.07), (0.08, 0.035), (0.0, 0.012), (0.0, -0.012),
                                  (0.08, -0.035), (0.08, -0.07), (-0.10, -0.07)):
                pts.append(Vector((AXLE.x, yw + across, AXLE.z)) + radial * (WHEEL_R + out))
            rings.append(wheels._verts(pts))
        rings.append(rings[0])
        wheels._rings(rings, True, False, False)
        # an inner web ring stiffening the rim
        wheels.torus((AXLE.x, yw, AXLE.z), WHEEL_R - 0.13, 0.03, axis=(0.0, 1.0, 0.0), segments=48, sides=6)
        # hub
        wheels.cylinder((AXLE.x, yw - 0.16, AXLE.z), (AXLE.x, yw + 0.16, AXLE.z), 0.20, segments=16)
        wheels.cylinder((AXLE.x, yw - 0.19, AXLE.z), (AXLE.x, yw + 0.19, AXLE.z), 0.12, segments=12)
        # ten spokes, slightly staggered across the hub (as cast sheaves are)
        for k in range(10):
            a = 2 * math.pi * k / 10 + (0.0 if sy < 0 else 0.15)
            side = 0.06 if k % 2 else -0.06
            p0 = Vector((AXLE.x + 0.18 * math.cos(a), yw + side, AXLE.z + 0.18 * math.sin(a)))
            p1 = Vector((AXLE.x + (WHEEL_R - 0.11) * math.cos(a), yw, AXLE.z + (WHEEL_R - 0.11) * math.sin(a)))
            wheels.beam(p0, p1, 0.075, 0.045, up=(0.0, 1.0, 0.0))
    objects.append(wheels.finish('winding_tower sheave wheels', collection, RUST, smooth=True, sharp=40))

    # ------------------------------------------------------------------ ropes: up the shaft, round the groove, (to the hoist)
    rope_mat = shapes.part_material('winding_tower', 'greased wire rope', _rope)
    ropes = shapes.Shape()
    groove_r = WHEEL_R + ROPE_R + 0.002
    for sy in (-1, 1):
        yw = sy * WHEEL_Y
        if hoist_rope and hoist_rope > 0:
            hoist = Vector((-float(hoist_rope), sy * 0.45, 2.5))
            d = Vector((hoist.x - AXLE.x, hoist.z - AXLE.z))
            dist = d.length
            base = math.atan2(d.y, d.x)
            leave = base - math.acos(min(1.0, groove_r / dist))       # tangent point on the upper side
            leave = leave + 2 * math.pi if leave < 0 else leave
        else:
            leave = math.radians(112)
        arc = []
        steps = 40
        for k in range(steps + 1):
            a = leave * k / steps
            arc.append((AXLE.x + groove_r * math.cos(a), yw, AXLE.z + groove_r * math.sin(a)))
        path = [(AXLE.x + groove_r, yw, 0.05)] + list(reversed(arc))
        if hoist_rope and hoist_rope > 0:
            end = Vector(arc[-1])
            for k in range(1, 13):
                t = k / 12
                p = end.lerp(Vector((hoist.x, hoist.y, hoist.z)), t)
                p.z -= math.sin(math.pi * t) * 0.012 * float(hoist_rope)     # a slight sag
                path.append(tuple(p))
        else:
            path = path
        ropes.sweep(path, ROPE_R, sides=8)
    objects.append(ropes.finish('winding_tower ropes', collection, rope_mat, smooth=True, sharp=None))

    # ------------------------------------------------------------------ the shaft mouth: a timber collar round a dark hole
    sx0, sx1 = rope_x - 0.95, rope_x + 0.65
    sy0, sy1 = -1.10, 1.10
    for (a, b) in (((sx0 - 0.17, sy0 - 0.17), (sx1 + 0.17, sy0 - 0.17)), ((sx0 - 0.17, sy1 + 0.17), (sx1 + 0.17, sy1 + 0.17))):
        wood_piece('collar', (a[0] - 0.15, a[1], 0.17), (b[0] + 0.15, b[1], 0.17), 0.34, 0.34, chamfer=0.02)
    for xx in (sx0 - 0.17, sx1 + 0.17):
        wood_piece('collar', (xx, sy0 - 0.17, 0.17 + 0.0), (xx, sy1 + 0.17, 0.17 + 0.0), 0.30, 0.30, chamfer=0.02)
    mouth = shapes.Shape()
    mouth.box(((sx0 + sx1) / 2, 0.0, 0.03), (sx1 - sx0 + 0.04, sy1 - sy0 + 0.04, 0.02))
    # a divider timber between the two cage roads
    objects.append(mouth.finish('winding_tower shaft mouth', collection, RECESS))
    wood_piece('collar divider', (sx0, 0.0, 0.12), (sx1, 0.0, 0.12), 0.16, 0.16, chamfer=0.01)

    # ------------------------------------------------------------------ ladder up the front, in two flights, and a landing
    front = face_normal('front')

    def face_point(x, z, out):
        hx, hy = half_at(z)
        return Vector((x, -hy, z)) + front * out

    def ladder(x, z0, z1, out=0.30, extra_top=0.0):
        width = 0.46
        for sx in (-1, 1):
            a = face_point(x + sx * width / 2, z0, out)
            b = face_point(x + sx * width / 2, z1 + extra_top, out)
            wood_piece('ladder stile', a, b, 0.07, 0.10, up=front, chamfer=0.006)
        z = z0 + 0.28
        while z < z1 - 0.05:
            iron.cylinder(face_point(x - width / 2 - 0.02, z, out), face_point(x + width / 2 + 0.02, z, out), 0.016, segments=8)
            z += 0.30
        # stand-off brackets fixing the ladder to each girt it passes
        for zl in LEVELS:
            if z0 + 0.1 < zl < z1 + 0.1:
                for sx in (-1, 1):
                    p0 = face_point(x + sx * 0.23, zl, 0.0)
                    p1 = face_point(x + sx * 0.23, zl, out)
                    iron.beam(p0, p1, 0.05, 0.012, up=(0.0, 0.0, 1.0))

    land_z = LEVELS[2] + GIRT[0] / 2
    ladder(1.05, 0.0, land_z)
    ladder(0.15, land_z, deck_z + 0.05, extra_top=1.0)
    # the landing: planks on two brackets out from the girt, with a rail round its outer sides
    lx0, lx1 = -0.25, 1.45
    depth = 0.85
    for xb in (lx0 + 0.1, lx1 - 0.1):
        wood_piece('landing bearer', face_point(xb, land_z - 0.08, 0.10), face_point(xb, land_z - 0.08, depth + 0.05), 0.10, 0.16,
                   up=(0.0, 0.0, 1.0), chamfer=0.008)
        wood_piece('landing strut', face_point(xb, land_z - 1.0, 0.12), face_point(xb, land_z - 0.12, depth), 0.09, 0.09,
                   up=(1.0, 0.0, 0.0), chamfer=0.008)
    k = 0
    out = 0.12
    while out < depth:
        w = 0.17
        if not (0.26 < out < 0.42):           # leave the hole the upper flight starts through
            wood_piece('landing plank', face_point(lx0, land_z + 0.02, out + w / 2), face_point(lx1, land_z + 0.02, out + w / 2),
                       w - 0.012, 0.04, material=planks, chamfer=0.005)
        out += w
        k += 1
    for xp in (lx0, lx1):
        wood_piece('landing post', face_point(xp, land_z, depth), face_point(xp, land_z + 1.0, depth), 0.08, 0.08, chamfer=0.006)
    for h in (1.0, 0.5):
        wood_piece('landing rail', face_point(lx0, land_z + h, depth), face_point(lx1, land_z + h, depth), 0.07, 0.06,
                   up=(0.0, 0.0, 1.0), extend=0.04, chamfer=0.006)
        wood_piece('landing rail', face_point(lx1, land_z + h, depth), face_point(lx1, land_z + h, 0.05), 0.07, 0.06,
                   up=(0.0, 0.0, 1.0), extend=0.04, chamfer=0.006)

    # ------------------------------------------------------------------ back stays to -X, braced to each other and the tower
    if back_stays:
        top_x = AXLE.x - 0.12
        foot_x = -9.55
        stay = []
        for sy in (-1, 1):
            top = Vector((top_x, sy * 1.12, bearing_z - 0.10))
            foot = Vector((foot_x, sy * 1.70, 0.45))
            stay.append((top, foot))
            wood_piece('back stay', foot, top, 0.36, 0.36, up=(0.0, 1.0, 0.0))
            for k, (lx, ly) in enumerate(((1.1, 0.4), (0.4, 1.1))):
                z = 0.10 + 0.20 * k
                c = Vector((foot.x, foot.y, 0.0))
                if lx > ly:
                    wood_piece('back stay footing', c + Vector((-lx / 2, 0, z)), c + Vector((lx / 2, 0, z)), 0.40, 0.20, chamfer=0.02)
                else:
                    wood_piece('back stay footing', c + Vector((0, -ly / 2, z)), c + Vector((0, ly / 2, z)), 0.20, 0.40, chamfer=0.02)

        def on_stay(sy_index, z):
            top, foot = stay[sy_index]
            t = (z - foot.z) / (top.z - foot.z)
            return foot.lerp(top, t)

        # struts across between the two stays, X-braced, and ties back to the tower's -X legs
        heights = [2.6, 6.3, 9.2, 11.6]
        for z in heights:
            a, b = on_stay(0, z), on_stay(1, z)
            wood_piece('stay strut', a + Vector((0.0, 0.0, 0.0)), b, 0.22, 0.18, up=(1.0, 0.0, 0.0), extend=0.12)
        for z0, z1 in zip(heights[:-1], heights[1:]):
            for (p, q) in ((on_stay(0, z0), on_stay(1, z1)), (on_stay(1, z0), on_stay(0, z1))):
                n = Vector((-1.0, 0.0, 0.0))
                d = (q - p).normalized()
                wood_piece('stay brace', p + d * 0.15 + Vector((-0.27, 0, 0)), q - d * 0.15 + Vector((-0.27, 0, 0)), 0.18, 0.12,
                           up=Vector((-0.83, 0.0, 0.55)))
        for z in (3.30, 6.30, 9.20):
            for i, sy in enumerate((-1, 1)):
                a = on_stay(i, z)
                b = corner(-1, sy, z) + Vector((-0.15, 0.0, 0.0))
                b.y = a.y
                wood_piece('stay tie', a, b, 0.20, 0.16, up=(0.0, sy, 0.0), extend=0.10)
                bolts(b + Vector((-0.30, 0.0, 0.08)), Vector((0.0, 0.0, 1.0)), Vector((1.0, 0.0, 0.0)))

    objects.append(iron.finish('winding_tower ironwork', collection, RUST, smooth=True, sharp=40))
    return objects
