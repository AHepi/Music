"""
coster_barrow: a costermonger's barrow of about 1900, as a street seller wheels his fruit or greens out on: a long
plank bed with low sides and a front board, on two big spoked wheels with iron tyres under its front half, two long
bearers that run on past the bed's back end as the handles, and two legs under the back of the bed. Parked, it
stands level on its wheels and its legs, the handles in the air; or, without legs, it rests tipped back on its handle
ends with its front raised. The bed is long along Y, its front (the wheel end) towards -Y, the handles towards +Y.

Options:
    rest     'legs' (default): standing level on its wheels and two legs, the handles in the air; 'handles': no legs,
             tipped back onto its handle ends, the front of the bed raised
    seed     the boards' shades and wear, the wheels' turn

Where it came from: '/home/claude/build-55-street/fronts/render_final.py', the costermonger's barrow (lines 1731-1775,
bedp() at line 1760): two wheels of short cylinder pieces with twelve rod spokes, a bed of five round rods with rod
sides, rod handles to the ground, tipped 14 degrees with its back end against the wall. Rebuilt here with a bed of
boards on bearers, low side boards, an axle tree and an iron axle, spoked wheels with felloes and iron tyres, turned
grips on the handles, and legs.
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

PART = 'coster_barrow'
BOARDS = 'MADE • weathered boards, peeling paint'
IRON = 'IRON • soot-black lamp posts'
RUST = 'RUST • rain-aged iron'
RESTS = ('legs', 'handles')

WHEEL_R = 0.48
AXLE_Y = -0.3
BED_Y0, BED_Y1 = -0.95, 0.75      # the bed's front and back ends
HANDLE_Y = 1.25                    # the handles' ends
BED_W = 0.84
BEARER_X = 0.36
BED_TOP = 0.66

CARD = {
    'name': PART,
    'what': "a costermonger's barrow: a long plank bed with low sides on two big iron-tyred spoked wheels, two handles, legs; "
            'standing level on its legs or tipped back on its handles',
    'size_m': (1.24, 2.25, 0.96),
    'options': {
        'rest': "'legs' (default): standing level on its wheels and two legs, the handles in the air; 'handles': no legs, tipped back "
                "onto its handle ends, the front of the bed raised",
        'seed': "the boards' shades and wear, the wheels' turn (default 0)",
    },
    'materials': [BOARDS + " (reads 'board_tone')", 'SURFACE • rough_wood (coster_barrow)', IRON, RUST],
    'source': "'/home/claude/build-55-street/fronts/render_final.py', the costermonger's barrow (lines 1731-1775, bedp() at line 1760)",
    'views': 'reads from every side; the wheels show best from the side (+X or -X)',
    'trap': 'it is 2.2 m long: the handles reach 1.25 m behind (+Y) the origin and the bed 0.95 m in front; backed against a wall '
            'with its handles out (as the street had it), turn it 180 degrees',
}


def build(collection, seed=0, rest='legs'):
    if rest not in RESTS:
        raise ValueError("coster_barrow rest is 'legs' or 'handles', not %r" % (rest,))
    rng = shapes.rng_for(PART, seed)
    wood = shapes.surface_copy('rough_wood', PART, Grime=0.55, Darken=0.5, **{'Mud height': 0.25})
    boards = shapes.material(BOARDS)
    tones = [rng.uniform(0.0, 1.0) for _ in range(16)]
    objects = []

    def timber(name, a, b, w, h, material=None, **kw):
        obj = shapes.timber(collection, 'coster_barrow %s' % name, a, b, w, h, material or wood, rng=rng, shift=0.4, **kw)
        objects.append(obj)
        return obj

    bearer_top = BED_TOP - 0.025
    bz = bearer_top - 0.035                     # the bearers' middle
    # ------------------------------------------------------------------ bearers running on into the handles, grips
    for side in (-1, 1):
        label = 'left' if side < 0 else 'right'
        timber('bearer %s' % label, (side * BEARER_X, BED_Y0, bz), (side * BEARER_X, HANDLE_Y - 0.15, bz), 0.05, 0.07, chamfer=0.008)
        grip = shapes.Shape()
        grip.lathe([(0.0, 0.0), (0.024, 0.0), (0.021, 0.03), (0.02, 0.13), (0.023, 0.145), (0.0, 0.15)], segments=12,
                   matrix=shapes.to4(shapes.frame_along((0.0, 1.0, 0.0)), (side * BEARER_X, HANDLE_Y - 0.15, bz)))
        objects.append(grip.finish('coster_barrow grip %s' % label, collection, wood, smooth=True, sharp=50))
    # cross bearers under the boards
    for y in (BED_Y0 + 0.06, AXLE_Y, 0.2, BED_Y1 - 0.06):
        timber('cross bearer %.2f' % y, (-BEARER_X - 0.04, y, bz), (BEARER_X + 0.04, y, bz), 0.045, 0.06)
    # ------------------------------------------------------------------ the bed: boards along Y, low sides, a front board
    count = 6
    bw = BED_W / count
    for k in range(count):
        x = -BED_W / 2 + bw * (k + 0.5)
        timber('bed board %d' % (k + 1), (x, BED_Y0, BED_TOP - 0.0125), (x, BED_Y1, BED_TOP - 0.0125), bw - 0.006, 0.025, boards,
               tone=tones[k], chamfer=0.003)
    for side in (-1, 1):
        timber('side board %s' % ('left' if side < 0 else 'right'), (side * (BED_W / 2 - 0.0125), BED_Y0 + 0.02, BED_TOP + 0.05),
               (side * (BED_W / 2 - 0.0125), BED_Y1, BED_TOP + 0.05), 0.025, 0.1, boards, tone=tones[8 + (side > 0)], chamfer=0.003,
               up=Vector((1.0, 0.0, 0.0)))
    timber('front board', (-BED_W / 2, BED_Y0 + 0.0125, BED_TOP + 0.06), (BED_W / 2, BED_Y0 + 0.0125, BED_TOP + 0.06), 0.025, 0.12,
           boards, tone=tones[10], chamfer=0.003, up=Vector((0.0, 1.0, 0.0)))
    # corner irons where the sides meet the front board
    irons = shapes.Shape()
    for side in (-1, 1):
        irons.box((side * (BED_W / 2 - 0.004), BED_Y0 + 0.06, BED_TOP + 0.05), (0.006, 0.1, 0.09))
        irons.box((side * (BED_W / 2 - 0.05), BED_Y0 - 0.002, BED_TOP + 0.06), (0.1, 0.006, 0.1))
    objects.append(irons.finish('coster_barrow corner irons', collection, RUST, smooth=False))

    # ------------------------------------------------------------------ the axle tree, the axle, the wheels
    timber('axle tree', (-BEARER_X - 0.03, AXLE_Y, (WHEEL_R + bz - 0.035) / 2), (BEARER_X + 0.03, AXLE_Y, (WHEEL_R + bz - 0.035) / 2),
           0.07, (bz - 0.035) - WHEEL_R + 0.03)
    axle = shapes.Shape()
    track = 0.53
    axle.cylinder((-track - 0.07, AXLE_Y, WHEEL_R), (track + 0.07, AXLE_Y, WHEEL_R), 0.018, segments=10)
    for side in (-1, 1):
        axle.box((side * BEARER_X, AXLE_Y, WHEEL_R + 0.02), (0.06, 0.03, 0.05))          # the clips round the axle
    objects.append(axle.finish('coster_barrow axle', collection, IRON, smooth=True, sharp=40))
    for side in (-1, 1):
        objects += shapes.spoked_wheel(collection, 'coster_barrow wheel %s' % ('left' if side < 0 else 'right'),
                                       (side * track, AXLE_Y, WHEEL_R), (1.0, 0.0, 0.0), WHEEL_R, 12, wood, IRON, rng,
                                       hub_radius=0.06, hub_length=0.15, spoke_width=0.03, felloe_depth=0.045, felloe_width=0.045, tyre=0.009)

    # ------------------------------------------------------------------ legs, or tipped back on the handles
    if rest == 'legs':
        for side in (-1, 1):
            top = Vector((side * BEARER_X, BED_Y1 - 0.2, bz - 0.035))
            foot = Vector((side * (BEARER_X + 0.03), BED_Y1 - 0.16, 0.0))
            timber('leg %s' % ('left' if side < 0 else 'right'), top + Vector((0, 0, 0.02)), foot, 0.05, 0.05, chamfer=0.006)
            shoe = shapes.Shape()
            shoe.box((foot.x, foot.y, 0.01), (0.06, 0.06, 0.02))
            objects.append(shoe.finish('coster_barrow leg shoe %s' % ('left' if side < 0 else 'right'), collection, RUST, chamfer=0.003))
    else:
        # turn the whole barrow about the axle until the grips' ends rest on the ground (the wheels stay where they are)
        end = Vector((0.0, HANDLE_Y, bz - 0.024))
        rel = end - Vector((0.0, AXLE_Y, WHEEL_R))
        radius = math.hypot(rel.y, rel.z)
        angle = math.atan2(rel.z, rel.y) - math.asin(-WHEEL_R / radius)
        shapes.tilt_all(objects, rx=-angle, pivot=(0.0, AXLE_Y, WHEEL_R))
        shapes.bake_placement(objects)
    return objects
