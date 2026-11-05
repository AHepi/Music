"""
sign_board: a shopkeeper's hanging sign of about 1910, blank (no words, ever): a framed timber board, its field and its
moulded border painted in two colours, faded and peeling to grey wood, hanging on two S-hooks from a forged iron
bracket off the wall: a wall plate with bolt heads, a square arm ending in a curl, a diagonal stay and a scroll in the
angle between them; rust run down the wall under the wall plate. The board hangs square to the wall, so it is read by
people coming along the street.

The wall is on the +Y side: the back of the wall plate lies on y = 0. The part's origin is the foot of the wall under
the sign (z = 0 is the ground there): the bracket's arm is 3.0 m up and the board hangs 2.28 to 2.88 m up. To hang it
higher or lower, place the part higher or lower.

Options:
    width    the board's length along the arm, metres (default 0.9); the arm grows to carry it
    paint    'cream' (default), 'green', 'red' or 'black': the paint on the field of the board; a dark green border
             round cream, a cream border round the others
    seed     where the paint has peeled, the board's swing, the rust's fingers

Where it came from: '/home/claude/build-55-street/fronts/render_final.py', the dairyman's board on its iron bracket
(lines 1679-1693: a box arm, a strut, a wall plate, two boxes for the board and its border, a rust stain by the store's
stain tool) and the close's name board (lines 1694-1697). Rebuilt here with a forged bracket and scroll, S-hooks, a
framed board in peeling paint and the rust run as part of the sign.
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
import _shapes_street_shop as street  # noqa: E402

PART = 'sign_board'
PAINT_CHOICES = ('cream', 'green', 'red', 'black')
BZ = 3.0             # the arm's height
BOARD_H = 0.60
RUST_LEN = 0.70

CARD = {
    'name': PART,
    'what': 'a blank hanging sign board (no words): a framed board in two faded, peeling paints on two S-hooks from a forged iron '
            'bracket off a wall (wall side +Y), with a scroll and a curl; rust run down the wall under the bracket',
    'size_m': (0.12, 1.14, 1.28),
    'options': {
        'width': "the board's length along the arm, metres (default 0.9); the arm grows to carry it",
        'paint': "'cream' (default), 'green', 'red' or 'black': the paint on the field of the board; a dark green border round cream, a cream border round the others",
        'seed': "where the paint has peeled, the board's swing, the rust's fingers (default 0)",
    },
    'materials': [street.IRON, street.STAIN, 'PART • sign_board: <paint> paint, peeling (field and border)'],
    'source': "'/home/claude/build-55-street/fronts/render_final.py', the dairyman's sign board on its bracket (lines 1679-1693) "
              "and the close's name board (lines 1694-1697)",
    'views': 'reads from every side; drawn alone it hangs in the air, as it needs a wall behind it; the board faces along the street (X)',
    'trap': "the origin is the foot of the wall below the sign, not the sign: the board hangs 2.28 to 2.88 m up and the rust runs "
            "down the wall face (y = 0) to 1.8 m, so a wall with stonework standing proud of its face hides the rust",
    'foot_z': 1.80,      # the rust run's foot: the sign's lowest point above the part's origin (the foot of its wall)
}


def build(collection, seed=0, width=0.9, paint='cream'):
    bw = barn.number('sign_board width', width, 0.4, 2.0)
    street.choice('sign_board paint', paint, PAINT_CHOICES)
    rng = shapes.rng_for(PART, seed)
    objects = []
    arm = max(1.05, bw + 0.2)
    iron = shapes.Shape()

    # ------------------------------------------------------------------ the bracket
    iron.box((0.0, -0.006, BZ - 0.22), (0.07, 0.012, 0.6))                                   # wall plate
    for z in (BZ + 0.04, BZ - 0.22, BZ - 0.48):
        iron.lathe([(0.0, 0.0), (0.016, 0.0), (0.013, 0.006), (0.0, 0.01)], segments=10,
                   matrix=shapes.to4(shapes.frame_along((0.0, -1.0, 0.0)), (0.0, -0.012, z)))
    iron.beam((0.0, -0.012, BZ), (0.0, -arm, BZ), 0.026, 0.026)
    curl = []
    for k in range(25):
        t = k / 24
        a = math.pi / 2 - 2.1 * math.pi * t
        r = 0.06 * (1.0 - 0.7 * t)
        curl.append((0.0, -arm - 0.002 + r * math.cos(a), BZ - 0.06 + r * math.sin(a)))
    curl[0] = (0.0, -arm + 0.01, BZ)
    iron.sweep(curl, 1.0, section=[(-0.006, -0.012), (0.006, -0.012), (0.006, 0.012), (-0.006, 0.012)], up=(1.0, 0.0, 0.0))
    stay_y = -min(0.62, arm * 0.6)
    iron.beam((0.0, -0.012, BZ - 0.48), (0.0, stay_y, BZ - 0.012), 0.02, 0.02, up=(1.0, 0.0, 0.0))
    # a scroll in the angle
    flat = [(-0.004, -0.008), (0.004, -0.008), (0.004, 0.008), (-0.004, 0.008)]
    sc_r = 0.11
    cy, cz = -0.012 - sc_r - 0.01, BZ - sc_r - 0.016
    pts = []
    for k in range(57):
        t = k / 56
        a = math.radians(90) + 2 * math.pi * 1.6 * t
        r = sc_r * (1.0 - 0.82 * t)
        pts.append((0.0, cy + r * math.cos(a), cz + r * math.sin(a)))
    iron.sweep(pts, 1.0, section=flat, up=(1.0, 0.0, 0.0))
    iron.box((0.0, cy, BZ - 0.016), (0.026, 0.018, 0.018))                                   # collar where it meets the arm
    # eyes on the arm and S-hooks down to the board
    y_a, y_b = -0.15, -0.15 - bw + 0.1
    board_top = BZ - 0.12
    hooks = shapes.Shape()
    for y in (y_a, y_b):
        iron.torus((0.0, y, BZ - 0.024), 0.013, 0.004, axis=(0.0, 1.0, 0.0), segments=10, sides=5)
        s_pts = [(0.0, y, BZ - 0.035), (0.012, y, BZ - 0.05), (0.0, y, BZ - 0.068), (-0.012, y, BZ - 0.085), (0.0, y, board_top + 0.012)]
        hooks.sweep(shapes.smooth_path(s_pts, steps=4), 0.0035, sides=6)
        hooks.torus((0.0, y, board_top + 0.008), 0.009, 0.003, axis=(0.0, 1.0, 0.0), segments=8, sides=4)
    objects.append(iron.finish('sign_board bracket', collection, street.IRON, smooth=True, sharp=40))
    objects.append(hooks.finish('sign_board hooks', collection, street.IRON, smooth=True, sharp=None))

    # ------------------------------------------------------------------ the board: a field in a moulded border, hanging square to the wall
    field_paint = paint
    border_paint = 'green' if paint == 'cream' else 'cream'
    field = shapes.Shape()
    border = shapes.Shape()
    yc = (y_a + y_b) / 2
    y0, y1 = yc - bw / 2, yc + bw / 2
    z0, z1 = board_top - BOARD_H, board_top
    field.box((0.0, yc, (z0 + z1) / 2), (0.032, bw - 0.08, BOARD_H - 0.08))
    edge = 0.055
    for (cy_, cz_, sy, sz) in (((y0 + y1) / 2, z1 - edge / 2, bw, edge), ((y0 + y1) / 2, z0 + edge / 2, bw, edge),
                               (y0 + edge / 2, (z0 + z1) / 2, edge, BOARD_H - 2 * edge), (y1 - edge / 2, (z0 + z1) / 2, edge, BOARD_H - 2 * edge)):
        border.box((0.0, cy_, cz_), (0.048, sy, sz))
    border.chamfer_all(0.008)
    field_obj = field.finish('sign_board field', collection, street.painted_board(PART, '%s paint, peeling' % field_paint, field_paint), smooth=False)
    border_obj = border.finish('sign_board border', collection, street.painted_board(PART, '%s paint, peeling' % border_paint, border_paint),
                               smooth=False)
    hooks_obj = objects[-1]
    swing = math.radians(rng.uniform(-2.0, 2.0))
    shapes.tilt_all([field_obj, border_obj, hooks_obj], rx=swing, pivot=(0.0, yc, BZ - 0.035))
    shapes.bake_placement([field_obj, border_obj, hooks_obj])
    objects += [field_obj, border_obj]

    # ------------------------------------------------------------------ rust run down the wall under the plate
    stain = shapes.Shape()
    barn.number_layers(stain, points=('fade',))
    street.rust_run(stain, -0.06, 0.06, BZ - 0.5, RUST_LEN, -0.002, rng, cols=10, rows=7, full=True)
    objects.append(stain.finish('sign_board rust run', collection, street.STAIN, smooth=True, sharp=None, shadow=False))
    return objects
