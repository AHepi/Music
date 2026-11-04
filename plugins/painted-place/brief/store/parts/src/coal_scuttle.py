"""
coal_scuttle: a black iron helmet-shaped coal scuttle: a round body widening to a slanted mouth (low at the front,
high at the back) with a rolled rim and a pouring lip, a foot ring, a bail handle over the top with a turned wooden
grip, and a short tilting handle at the back; coal in it. Standing, or tipped over on its side with the coal spilled
out in front. The mouth faces -Y. Foot at z = 0.

Options:
    tipped   False (default): standing; True: lying on its side, mouth towards -Y, coal spilled on the ground
    seed     the bail's angle, the coal

Where it came from: '/home/claude/build-51-chapel/dress/dress_block.py', scuttle() (line 351): a cone, a floor, a rim,
a lip box and a bail of beams; rebuilt here as one helmet body with a slanted mouth, rolled rim, foot, bail and coal.
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

PART = 'coal_scuttle'
IRON = 'IRON • soot-black lamp posts'
RUST = 'RUST • rain-aged iron'

CARD = {
    'name': PART,
    'what': 'a black iron helmet coal scuttle: slanted mouth with a rolled rim, foot ring, bail handle with a wooden grip, '
            'tilting handle at the back, coal in it; standing or tipped over with the coal spilled',
    'size_m': (0.43, 0.54, 0.49),
    'options': {
        'tipped': 'False (default): standing; True: lying on its side, mouth towards -Y, coal spilled on the ground',
        'seed': "the bail's angle, the coal (default 0)",
    },
    'materials': [IRON, RUST, 'PART • coal_scuttle: coal', 'PART • coal_scuttle: dark worn ash'],
    'source': "'/home/claude/build-51-chapel/dress/dress_block.py', scuttle() (line 351)",
    'views': 'reads from every side; the mouth and lip face -Y',
    'trap': 'tipped, the spilled coal reaches about 0.5 m in front (-Y) of the origin',
}

H_FRONT, H_BACK = 0.24, 0.40          # the mouth's height at the front and the back
R_FOOT, R_TOP = 0.15, 0.19            # the body's radius at the bottom and the mouth
WALL = 0.003


def body_rings(count=14, segments=40, inset=0.0, lip=0.035):
    """Rings of points for the body: round, widening upwards, cut by a slanted mouth; the front of the rim pulled
    out into a pouring lip. `inset` shrinks the radius (the inner wall)."""
    rings = []
    for k in range(count + 1):
        f = k / count
        ring = []
        for j in range(segments):
            a = 2 * math.pi * j / segments
            top = (H_FRONT + H_BACK) / 2 + (H_BACK - H_FRONT) / 2 * math.sin(a)
            z = f * top
            r = R_FOOT + (R_TOP - R_FOOT) * f ** 0.8 - inset
            r += 0.012 * math.sin(math.pi * f)                        # a slight belly
            r += lip * f ** 4 * max(0.0, -math.sin(a)) ** 2            # the lip at the front
            ring.append(Vector((r * math.cos(a), r * math.sin(a), z)))
        rings.append(ring)
    return rings


def build(collection, seed=0, tipped=False):
    rng = shapes.rng_for(PART, seed)
    objects = []
    grip_wood = shapes.dark_wood(PART)
    coal = shapes.coal_material(PART)

    # ------------------------------------------------------------------ body: outer and inner walls, floor, rolled rim
    body = shapes.Shape()
    outer = body_rings()
    inner = body_rings(inset=WALL)
    lift = 0.012                                       # the body stands on its foot ring
    for ring in outer + inner:
        for p in ring:
            p.z += lift
    for ring in inner:
        for p in ring:
            p.z = max(p.z, lift + 0.01)                 # the inner floor sits 1 cm up
    vo = [body._verts(r) for r in outer]
    vi = [body._verts(r) for r in inner]
    body._rings(vo, True, True, False)                 # outer wall, closed at the bottom
    body._rings(list(reversed(vi)), True, False, True)  # inner wall facing in, closed at its floor
    body._rings([vo[-1], vi[-1]], True, False, False)   # the rim's top joining outer to inner
    # the rolled rim: a rod along the mouth's edge
    rim_pts = [p + Vector((0, 0, 0)) for p in outer[-1]]
    body.sweep(rim_pts, 0.007, sides=8, closed=True)
    # the foot ring and a band low down
    body.torus((0.0, 0.0, 0.007), R_FOOT - 0.01, 0.007, segments=40, sides=8)
    # the ears for the bail, either side at the rim's height there
    ear_z = lift + (H_FRONT + H_BACK) / 2 - 0.03
    ear_r = R_FOOT + (R_TOP - R_FOOT) * 0.85 ** 0.8 + 0.012 * math.sin(math.pi * 0.85)
    for side in (-1, 1):
        body.box((side * (ear_r + 0.006), 0.0, ear_z), (0.012, 0.03, 0.05))
    # the tilting handle at the back: a wooden knob on an iron stem
    back_z = lift + H_BACK - 0.05
    back_r = R_FOOT + (R_TOP - R_FOOT) * 0.88 ** 0.8 + 0.012 * math.sin(math.pi * 0.88)
    body.cylinder((0.0, back_r - 0.01, back_z), (0.0, back_r + 0.03, back_z), 0.006, segments=8)
    objects.append(body.finish('coal_scuttle body', collection, IRON, smooth=True, sharp=40))
    knob = shapes.Shape()
    knob.lathe([(0.0, 0.0), (0.012, 0.0), (0.016, 0.02), (0.014, 0.07), (0.017, 0.08), (0.0, 0.09)], segments=14,
               matrix=shapes.to4(shapes.frame_along((0, 1, 0)), (0.0, back_r + 0.03, back_z)))
    objects.append(knob.finish('coal_scuttle tilting handle', collection, grip_wood, smooth=True, sharp=50))
    # rust where the coal scrapes: the lip's underside and the foot
    rust = shapes.Shape()
    rust.torus((0.0, 0.0, 0.004), R_FOOT - 0.006, 0.004, segments=40, sides=6)
    objects.append(rust.finish('coal_scuttle foot rust', collection, RUST, smooth=True, sharp=40))

    # ------------------------------------------------------------------ the bail: a half ring from ear to ear, leaning back
    bail_lean = math.radians(rng.uniform(20, 40))
    bail = shapes.Shape()
    pts = []
    span = ear_r + 0.012
    for k in range(25):
        a = math.pi * k / 24
        p = Vector((-span * math.cos(a), 0.0, span * 0.95 * math.sin(a)))
        p = Vector((p.x, -math.sin(bail_lean) * p.z, math.cos(bail_lean) * p.z)) * 1.0
        pts.append(p + Vector((0.0, 0.0, ear_z)))
    pts[0].x, pts[-1].x = -span, span
    bail.sweep(pts, 0.006, sides=8)
    for side in (-1, 1):
        bail.sphere((side * (span + 0.002), 0.0, ear_z), 0.009, segments=10, rings=5)
    objects.append(bail.finish('coal_scuttle bail', collection, IRON, smooth=True, sharp=50))
    grip = shapes.Shape()
    mid = pts[12]
    along = (pts[13] - pts[11]).normalized()
    grip.lathe([(0.0, -0.06), (0.011, -0.06), (0.015, -0.045), (0.014, 0.045), (0.011, 0.06), (0.0, 0.06)], segments=14,
               matrix=shapes.to4(shapes.frame_along(along), mid))
    objects.append(grip.finish('coal_scuttle grip', collection, grip_wood, smooth=True, sharp=50))

    # ------------------------------------------------------------------ coal in it
    lumps = shapes.Shape()
    fill = lift + H_FRONT - 0.05
    shapes.lumps(lumps, (0.0, 0.02, fill - 0.02), 40, 0.06, (R_TOP - 0.06, R_TOP - 0.05), rng, height=0.06)
    shapes.lumps(lumps, (0.0, 0.0, fill - 0.08), 30, 0.055, (R_TOP - 0.08, R_TOP - 0.08), rng, height=0.03)
    coal_in = lumps.finish('coal_scuttle coal', collection, coal, smooth=False)
    objects.append(coal_in)

    if tipped:
        # over onto its front: the mouth towards -Y, rolled a little onto one side, then set on the ground
        side = rng.choice((-1, 1))
        roll = Matrix.Rotation(math.radians(side * rng.uniform(18, 30)), 4, 'Y') @ Matrix.Rotation(math.radians(88), 4, 'X')
        turn = Matrix.Rotation(math.radians(rng.uniform(-15, 15)), 4, 'Z')
        for obj in objects:
            obj.matrix_world = turn @ roll @ obj.matrix_world
        bpy.context.view_layer.update()
        low = min((obj.matrix_world @ v.co).z for obj in objects if obj.name != 'coal_scuttle coal' for v in obj.data.vertices)
        for obj in objects:
            obj.matrix_world = Matrix.Translation((0.0, 0.0, -low)) @ obj.matrix_world
        shapes.bake_placement(objects)
        # the coal that has run out: a tongue of lumps from the mouth forward along the ground
        spill = shapes.Shape()
        mouth_y = -(lift + H_FRONT) - 0.02
        shapes.lumps(spill, (0.0, mouth_y - 0.12, 0.0), 45, 0.06, (0.17, 0.16), rng, height=0.05)
        shapes.lumps(spill, (0.02, mouth_y - 0.30, 0.0), 20, 0.05, (0.2, 0.12), rng, height=0.0)
        objects.append(spill.finish('coal_scuttle spilled coal', collection, coal, smooth=False))
        # the coal left in the mouth
        rest = shapes.Shape()
        shapes.lumps(rest, (0.0, mouth_y + 0.08, 0.02), 18, 0.055, (0.1, 0.06), rng, height=0.04)
        objects.append(rest.finish('coal_scuttle coal in the mouth', collection, coal, smooth=False))
    return objects
