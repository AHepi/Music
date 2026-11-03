"""
coal_cart: a coal merchant's two-wheeled cart of about 1910, unhitched. Two big wooden wheels (twelve spokes, six
felloes, iron tyres, iron-hooped hubs) on an axle under a planked bed with painted sideboards on stakes, a tall
headboard at the front and a tailboard on chains at the back. The shafts run forward (-Y) for the horse; with no horse
they rest on two props, or on the ground. Loaded, six sacks of coal stand in the bed, open at the neck, with lumps
fallen between them.

Options:
    loaded   True (default): six sacks of coal in the bed; False: an empty bed with coal dust, lumps and one empty
             sack lying folded.
    prop     True (default): the shafts rest on two props and the bed stays level; False: the shafts' tips rest on
             the ground and the whole cart tips forward.

Where it came from: "46 townhouse - render_final.py" (procedural-textures/46 Pictures-only builders - three places),
build_cart() (line 721): a box on two wheels of bars with a heap of cubes for coal; rebuilt here as a whole cart at
real size: spoked wheels with felloes and tyres, bed, sideboards, stakes, shafts, props and sacks.
"""

import math
import os
import sys

import bpy
import mathutils
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import _shapes_town as shapes  # noqa: E402

RUST = 'RUST • rain-aged iron'

CARD = {
    'name': 'coal_cart',
    'what': 'a coal merchant\'s two-wheeled cart, unhitched: spoked wheels with iron tyres, painted sideboards, shafts to -Y on props, sacks of coal',
    'size_m': (1.99, 4.07, 1.52),
    'options': {
        'loaded': 'True (default): six sacks of coal; False: empty bed, coal dust and an empty sack',
        'prop': 'True (default): the shafts rest on two props, bed level; False: shafts on the ground, cart tipped forward',
    },
    'materials': ['SURFACE • rough_wood (coal_cart)', 'SURFACE • old_planks_02 (coal_cart)',
                  'SURFACE • distressed_painted_planks (coal_cart)', 'SURFACE • hessian_380 (coal_cart)', RUST,
                  'PART • coal_cart: coal'],
    'source': '"46 townhouse - render_final.py", build_cart() (line 721); builder\'s report "46 Townhouse builder\'s report.md"',
    'views': 'reads from every side',
    'trap': 'the shafts reach 3.06 m out in front (-Y) of the bed\'s middle: leave them room',
}

WHEEL_R = 0.60
AXLE = Vector((0.0, 0.12, 0.60))
WHEEL_X = 0.78
SILL_X = 0.51
BED_Y = 0.95
FLOOR_Z = 0.81


def _coal(m, nodes, links, principled):
    vec = shapes.own_coordinates(nodes)
    facet = nodes.new('ShaderNodeTexVoronoi')
    facet.inputs['Scale'].default_value = 30.0
    links.new(vec, facet.inputs['Vector'])
    dust = shapes.noise_fac(nodes, links, vec, 12.0, detail=4.0)
    colour = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, dust, 0.55, 0.75), (0.010, 0.010, 0.011), (0.030, 0.028, 0.026))
    links.new(colour, principled.inputs['Base Color'])
    links.new(shapes.map_range(nodes, links, dust, 0.4, 0.8, 0.22, 0.7), principled.inputs['Roughness'])
    principled.inputs['Specular IOR Level'].default_value = 0.6
    links.new(shapes.bump(nodes, links, facet.outputs['Distance'], 0.6, 0.006), principled.inputs['Normal'])
    m.diffuse_color = (0.012, 0.012, 0.012, 1.0)


def _wheel(collection, objects, side, rng, wood, tyres):
    """One wheel: hub, twelve tapered spokes, six felloes, tyre (iron into `tyres`)."""
    xc = side * WHEEL_X
    centre = Vector((xc, AXLE.y, AXLE.z))
    turn = rng.uniform(0, 2 * math.pi / 12)
    dish = 0.035                       # the rim stands a little outboard of the spokes' roots
    axis_frame = shapes.frame_along((side, 0.0, 0.0))
    # hub (nave): turned elm, grain along the axle
    hub = shapes.Shape()
    hub.lathe([(0.0, -0.17), (0.060, -0.17), (0.085, -0.155), (0.118, -0.10), (0.128, -0.035), (0.128, 0.035),
               (0.118, 0.085), (0.090, 0.140), (0.070, 0.170), (0.0, 0.170)], segments=24,
              matrix=shapes.to4(axis_frame, centre))
    objects.append(hub.finish('coal_cart hub %s' % ('left' if side < 0 else 'right'), collection, wood, smooth=True, sharp=50,
                              local=shapes.to4(axis_frame, centre), shift=0.3, rng=rng))
    for (off, r, w) in ((-0.135, 0.104, 0.012), (-0.07, 0.124, 0.010), (0.07, 0.124, 0.010), (0.135, 0.100, 0.012)):
        tyres.torus(centre + Vector((side * off, 0.0, 0.0)), r, w, axis=(1.0, 0.0, 0.0), segments=24, sides=6)
    tyres.cylinder(centre + Vector((side * 0.17, 0, 0)), centre + Vector((side * 0.205, 0, 0)), 0.055, segments=12)
    tyres.cylinder(centre + Vector((side * 0.205, 0, 0)), centre + Vector((side * 0.215, 0, 0)), 0.035, segments=8)
    # spokes
    for k in range(12):
        a = turn + 2 * math.pi * k / 12
        radial = Vector((0.0, math.cos(a), math.sin(a)))
        root = centre + radial * 0.115 + Vector((side * 0.005, 0, 0))
        tip = centre + radial * 0.53 + Vector((side * dish, 0, 0))
        objects.append(shapes.timber(collection, 'coal_cart spoke %s %d' % ('left' if side < 0 else 'right', k + 1),
                                     root, tip, 0.056, 0.036, wood, rng=rng, up=(side, 0.0, 0.0), chamfer=0.006,
                                     taper=0.78, shift=0.3))
    # felloes: six curved segments of the wooden rim, each its own piece of wood
    for k in range(6):
        a0 = turn + 2 * math.pi * k / 6 + 0.004
        a1 = turn + 2 * math.pi * (k + 1) / 6 - 0.004
        rings = []
        felloe = shapes.Shape()
        for j in range(9):
            a = a0 + (a1 - a0) * j / 8
            radial = Vector((0.0, math.cos(a), math.sin(a)))
            c = centre + Vector((side * dish, 0, 0))
            pts = [c + radial * 0.515 + Vector((-0.028, 0, 0)), c + radial * 0.515 + Vector((0.028, 0, 0)),
                   c + radial * 0.588 + Vector((0.028, 0, 0)), c + radial * 0.588 + Vector((-0.028, 0, 0))]
            rings.append(felloe._verts(pts))
        felloe._rings(rings, True, True, True)
        mid = (a0 + a1) / 2
        chord = Vector((0.0, -math.sin(mid), math.cos(mid)))
        frame = shapes.to4(shapes.frame_along(chord, up=(1.0, 0.0, 0.0)), centre + Vector((0.0, math.cos(mid), math.sin(mid))) * 0.55)
        objects.append(felloe.finish('coal_cart felloe %s %d' % ('left' if side < 0 else 'right', k + 1), collection, wood,
                                     chamfer=0.005, local=frame, shift=0.3, rng=rng))
    # the iron tyre round the felloes, with a few nail heads
    tyre_rings = []
    for j in range(73):
        a = 2 * math.pi * j / 72
        radial = Vector((0.0, math.cos(a), math.sin(a)))
        c = centre + Vector((side * dish, 0, 0))
        tyre_rings.append(tyres._verts([c + radial * 0.587 + Vector((-0.031, 0, 0)), c + radial * 0.587 + Vector((0.031, 0, 0)),
                                        c + radial * 0.601 + Vector((0.031, 0, 0)), c + radial * 0.601 + Vector((-0.031, 0, 0))]))
    tyre_rings[-1] = tyre_rings[0]
    tyres._rings(tyre_rings, True, False, False)
    for k in range(12):
        a = turn + 2 * math.pi * (k + 0.5) / 12
        radial = Vector((0.0, math.cos(a), math.sin(a)))
        tyres.cylinder(centre + Vector((side * dish, 0, 0)) + radial * 0.597, centre + Vector((side * dish, 0, 0)) + radial * 0.6025,
                       0.009, segments=6)


def _sack(shape, rng, base, height, lean):
    """A slumped sack standing open at the neck: wide where the coal's weight settles, folds gathering towards the
    neck, an uneven lip; pushed in and out at random and leaning a little."""
    r0 = rng.uniform(0.150, 0.165)
    h = height
    prof = [(0.0, 0.0), (r0 * 0.92, 0.0), (r0 * 1.16, 0.035), (r0 * 1.27, 0.11), (r0 * 1.24, h * 0.30),
            (r0 * 1.14, h * 0.58), (r0 * 1.02, h * 0.78), (r0 * 0.90, h * 0.90), (r0 * 0.94, h * 0.96),
            (r0 * 1.00, h), (r0 * 0.93, h - 0.012), (r0 * 0.82, h - 0.06)]
    turn = rng.uniform(0, math.pi)
    m = Matrix.Translation(base) @ Matrix.Rotation(turn, 4, 'Z') @ Matrix.Diagonal((1.0, 0.76, 1.0, 1.0))
    verts_before = set(shape.bm.verts)
    shape.lathe(prof, segments=28, matrix=m, open_ends=False)
    new = [v for v in shape.bm.verts if v not in verts_before]
    seed = rng.uniform(0, 100)
    phase = [rng.uniform(0, 2 * math.pi) for _ in range(3)]
    for v in new:
        local = v.co - Vector(base)
        t = max(0.0, min(1.0, local.z / h))
        angle = math.atan2(local.y, local.x)
        lump = 0.14 * mathutils.noise.noise(Vector((local.x * 5.0, local.y * 5.0, local.z * 4.0 + seed)))
        folds = (0.05 * math.sin(5 * angle + phase[0]) + 0.03 * math.sin(9 * angle + phase[1])) * t ** 1.4
        k = 1.0 + lump + folds
        lip = 0.03 * math.sin(3 * angle + phase[2]) * max(0.0, (t - 0.85) / 0.15)
        v.co = Vector(base) + Vector((local.x * k + lean[0] * local.z, local.y * k + lean[1] * local.z, local.z + lip))
    return r0, turn


def build(collection, seed=0, loaded=True, prop=True):
    rng = shapes.rng_for('coal_cart', seed)
    objects = []
    wood = shapes.surface_copy('rough_wood', 'coal_cart', Grime=0.5, Darken=0.62, **{'Mud height': 0.45})
    floor_wood = shapes.surface_copy('old_planks_02', 'coal_cart', Grime=0.7, Darken=0.55)
    paint = shapes.surface_copy('distressed_painted_planks', 'coal_cart', Grime=0.55, Darken=0.42, **{'Mud height': 0.9})
    iron = shapes.Shape()

    def piece(label, a, b, w, h, material=None, up=shapes.UP, extend=0.0, chamfer=0.006, taper=1.0, sag=0.0):
        obj = shapes.timber(collection, 'coal_cart %s' % label, a, b, w, h, material or wood, rng=rng, up=up, extend=extend,
                            chamfer=chamfer, taper=taper, sag=sag, roll=math.radians(rng.uniform(-0.6, 0.6)), shift=0.4)
        objects.append(obj)
        return obj

    # ------------------------------------------------------------------ wheels and axle
    for side in (-1, 1):
        _wheel(collection, objects, side, rng, wood, iron)
    piece('axletree', (-0.62, AXLE.y, AXLE.z + 0.005), (0.62, AXLE.y, AXLE.z + 0.005), 0.11, 0.11)
    iron.cylinder((-0.98, AXLE.y, AXLE.z), (0.98, AXLE.y, AXLE.z), 0.032, segments=12)
    for side in (-1, 1):
        # U-bolts clipping the axletree to the sills
        for dy in (-0.07, 0.07):
            iron.beam((side * SILL_X, AXLE.y + dy, AXLE.z - 0.056), (side * SILL_X, AXLE.y + dy, 0.72), 0.014, 0.014)
        iron.box((side * SILL_X, AXLE.y, AXLE.z - 0.056), (0.10, 0.18, 0.012))

    # ------------------------------------------------------------------ the frame: sills running on into the shafts
    sill_z = 0.72
    for side in (-1, 1):
        piece('sill %s' % ('left' if side < 0 else 'right'), (side * SILL_X, BED_Y, sill_z), (side * SILL_X, -BED_Y, sill_z),
              0.09, 0.12, extend=0.02)
        piece('shaft %s' % ('left' if side < 0 else 'right'), (side * SILL_X, -BED_Y + 0.05, sill_z + 0.005),
              (side * 0.37, -3.05, sill_z + 0.06), 0.085, 0.095, taper=0.72, sag=-0.03, chamfer=0.01)
        # an iron ferrule on the tip, and the tug hook for the harness
        tip = Vector((side * 0.37, -3.05, sill_z + 0.06))
        iron.cylinder(tip + Vector((0, 0.10, 0)), tip + Vector((0, -0.01, 0)), 0.036, segments=10)
        tug = Vector((side * (0.37 + (SILL_X - 0.37) * 0.45), -2.0, sill_z + 0.045))
        iron.torus(tug + Vector((side * 0.05, 0.0, 0.0)), 0.035, 0.008, axis=(0.0, 1.0, 0.0), segments=12, sides=6)
        iron.box(tug + Vector((side * 0.035, 0.0, 0.0)), (0.012, 0.05, 0.05))
    for y in (-0.80, -0.30, 0.30, 0.82):
        piece('bolster', (-0.56, y, sill_z - 0.075), (0.56, y, sill_z - 0.075), 0.07, 0.05)
    piece('breast bar', (-0.47, -1.30, sill_z + 0.01), (0.47, -1.30, sill_z + 0.01), 0.07, 0.07)

    # ------------------------------------------------------------------ the bed: floor planks, sideboards on stakes
    x = -0.53
    while x < 0.52:
        w = rng.uniform(0.19, 0.24)
        w = min(w, 0.53 - x)
        if w > 0.06:
            piece('floor plank', (x + w / 2, BED_Y, FLOOR_Z - 0.015), (x + w / 2, -BED_Y, FLOOR_Z - 0.015), w - 0.008, 0.03,
                  material=floor_wood, chamfer=0.004)
        x += w
    board_h = 0.16
    for side in (-1, 1):
        xs = side * 0.545
        for k in range(2):
            z = FLOOR_Z + 0.005 + board_h / 2 + k * (board_h + 0.008)
            piece('sideboard', (xs, -BED_Y, z), (xs, BED_Y, z), board_h, 0.026, material=paint, up=(side, 0.0, 0.0), chamfer=0.004)
        for y in (-0.86, -0.02, 0.86):
            piece('stake', (side * 0.583, y, sill_z - 0.06), (side * 0.583, y, FLOOR_Z + 2 * board_h + 0.05), 0.05, 0.045,
                  chamfer=0.006)
            # stake pocket and a strap round the boards
            iron.box((side * 0.583, y, sill_z + 0.01), (0.07, 0.07, 0.10))
            for zz in (FLOOR_Z + 0.09, FLOOR_Z + 0.26):
                iron.box((side * 0.6095, y, zz), (0.004, 0.065, 0.035))
    # headboard at the front: three boards and a rail; tailboard at the back on chains
    for k in range(3):
        z = FLOOR_Z + 0.005 + board_h / 2 + k * (board_h + 0.008)
        piece('headboard', (-0.53, -BED_Y - 0.013, z), (0.53, -BED_Y - 0.013, z), board_h, 0.026, material=paint, up=(0.0, -1.0, 0.0),
              chamfer=0.004)
    head_top = FLOOR_Z + 3 * (board_h + 0.008) + 0.02
    piece('head rail', (-0.60, -BED_Y - 0.013, head_top), (0.60, -BED_Y - 0.013, head_top), 0.055, 0.05, chamfer=0.008)
    for sx in (-1, 1):
        piece('head post', (sx * 0.55, -BED_Y - 0.01, sill_z - 0.06), (sx * 0.55, -BED_Y - 0.01, head_top + 0.02), 0.055, 0.05,
              chamfer=0.006)
    for k in range(2):
        z = FLOOR_Z + 0.005 + board_h / 2 + k * (board_h + 0.008)
        piece('tailboard', (-0.52, BED_Y + 0.013, z), (0.52, BED_Y + 0.013, z), board_h, 0.026, material=paint, up=(0.0, 1.0, 0.0),
              chamfer=0.004)
    for sx in (-1, 1):
        # corner irons and the tailboard's chains
        iron.box((sx * 0.50, BED_Y + 0.028, FLOOR_Z + 0.17), (0.08, 0.004, 0.30))
        chain = []
        for k in range(7):
            t = k / 6
            chain.append((sx * 0.565, BED_Y + 0.02 + 0.01 * math.sin(math.pi * t), FLOOR_Z + 0.33 - 0.30 * t + 0.03 * math.sin(math.pi * t)))
        for k in range(6):
            a, b = Vector(chain[k]), Vector(chain[k + 1])
            mid = (a + b) / 2
            iron.torus(mid, 0.026, 0.0045, axis=(1.0, 0.0, 0.0) if k % 2 else (0.0, 1.0, 0.0), segments=10, sides=5)
    # the props under the shafts
    if prop:
        for side in (-1, 1):
            a = Vector((side * SILL_X, -BED_Y + 0.05, sill_z + 0.005))
            b = Vector((side * 0.37, -3.05, sill_z + 0.06))
            t = (-1.75 - a.y) / (b.y - a.y)
            top = a.lerp(b, t) + Vector((0.0, 0.0, 0.03 * 4 * t * (1 - t)))     # the shaft bows up a little
            piece('prop', top, Vector((top.x * 1.02, -1.98, 0.035)), 0.055, 0.055, chamfer=0.006)
            iron.cylinder(top + Vector((-0.06, 0, 0)), top + Vector((0.06, 0, 0)), 0.012, segments=8)
            iron.box(Vector((top.x * 1.02, -1.982, 0.012)), (0.07, 0.07, 0.024))

    # ------------------------------------------------------------------ the load
    coal = shapes.part_material('coal_cart', 'coal', _coal)
    lumps = shapes.Shape()
    if loaded:
        sacking = shapes.surface_copy('hessian_380', 'coal_cart', Darken=0.12, Grime=0.9, Bump=0.9)
        sacks = shapes.Shape()
        for (sx, sy) in ((-0.27, -0.60), (0.27, -0.58), (-0.27, 0.0), (0.27, 0.02), (-0.27, 0.60), (0.27, 0.58)):
            base = Vector((sx + rng.uniform(-0.02, 0.02), sy + rng.uniform(-0.03, 0.03), FLOOR_Z + 0.002))
            height = rng.uniform(0.47, 0.60)
            lean = (rng.uniform(-0.09, 0.09), rng.uniform(-0.09, 0.09))
            r0, turn = _sack(sacks, rng, base, height, lean)
            # the coal showing at the open neck: a mound and a few lumps on it
            neck = base + Vector((lean[0] * height, lean[1] * height, height - 0.04))
            lumps.lathe([(0.0, 0.09), (r0 * 0.5, 0.06), (r0 * 0.80, 0.0), (r0 * 0.7, -0.05), (0.0, -0.06)], segments=16,
                        matrix=Matrix.Translation(neck) @ Matrix.Rotation(turn, 4, 'Z') @ Matrix.Diagonal((1.0, 0.78, 1.0, 1.0)))
            for _ in range(5):
                a = rng.uniform(0, 2 * math.pi)
                d = rng.uniform(0.0, r0 * 0.45)
                lumps.rock(neck + Vector((d * math.cos(a), d * math.sin(a) * 0.8, 0.07)), rng.uniform(0.03, 0.05), rng)
        objects.append(sacks.finish('coal_cart sacks', collection, sacking, smooth=True, sharp=None))
        loose = 14
    else:
        loose = 22
        sacking = shapes.surface_copy('hessian_380', 'coal_cart', Darken=0.12, Grime=0.9, Bump=0.9)
        empty = shapes.Shape()
        # one empty sack lying folded on the floor
        pts = []
        for k in range(7):
            t = k / 6
            pts.append((0.12 + 0.02 * math.sin(t * 5), -0.25 + 0.7 * t, FLOOR_Z + 0.012))
        empty.sweep(pts, 1.0, section=[(-0.24, -0.008), (0.24, -0.008), (0.25, 0.012), (0.10, 0.026), (-0.12, 0.022), (-0.25, 0.010)])
        objects.append(empty.finish('coal_cart empty sack', collection, sacking, smooth=True, sharp=None))
    for k in range(loose):
        x = rng.uniform(-0.48, 0.48)
        y = rng.uniform(-0.88, 0.88)
        r = rng.uniform(0.02, 0.045)
        lumps.rock((x, y, FLOOR_Z + r * 0.45), r, rng)
    objects.append(lumps.finish('coal_cart coal', collection, coal, smooth=False))
    objects.append(iron.finish('coal_cart ironwork', collection, RUST, smooth=True, sharp=40))

    # ------------------------------------------------------------------ resting: level on props, or tipped onto the shafts
    if not prop:
        tip = Vector((0.0, -3.05 - AXLE.y, 0.06 + sill_z - AXLE.z))      # the shaft tip relative to the axle (y, z)
        target = 0.045 - AXLE.z
        # angle that brings the tip down to `target` height, turning about the axle
        r = math.hypot(tip.y, tip.z)
        start = math.atan2(tip.z, tip.y)
        theta = math.pi - math.asin(max(-1.0, min(1.0, target / r))) - start
        shapes.tilt_all(objects, rx=theta, pivot=AXLE)
    return objects
