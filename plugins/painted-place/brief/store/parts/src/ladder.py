"""
ladder: a farm ladder of about 1900, for a hay mow or a loft: two rough rails of weathered timber (a little bowed,
chamfered by hand, narrowing towards the top), round rungs about 27 cm apart driven through them (their ends show on the
rails' outer faces), and iron tie rods with square nuts under three of the rungs. It leans back towards +Y at about 15
degrees, as a ladder is set (one out for every four up), its feet on the ground and the top of its rails resting on a
wall. The origin is the foot of that wall, straight under the ladder's top: the wall's face is the plane y = 0 and the
whole ladder stands in front of it (-Y). Foot at z = 0.

Options:
    length   metres along the rails (default 3.6)
    seed     the rails' bow and chamfers, the lean (14 to 16 degrees), each piece's shade

Where it came from: '/home/claude/build-54-barn/first pass/render_final.py', the 'hay ladder' (lines 510-519): two
square boxes for rails and eleven square bars for rungs in one mesh; rebuilt here with rough rails narrowing upwards,
round tapered rungs through them, tie rods, and its top resting on the wall.
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

PART = 'ladder'
RUST = 'RUST • rain-aged iron'

CARD = {
    'name': PART,
    'what': 'a farm ladder: two rough timber rails narrowing upwards, round rungs driven through them, iron tie rods; leaning back at 15 degrees '
            'with its top resting on a wall at +Y',
    'size_m': (0.51, 1.06, 3.47),
    'foot_z': 0.0,      # its origin is the foot of the wall it rests on, not its middle (see the trap)
    'options': {
        'length': 'metres along the rails (default 3.6)',
        'seed': "the rails' bow and chamfers, the lean (14 to 16 degrees), each piece's shade (default 0)",
    },
    'materials': ['SURFACE • rough_wood (ladder), each piece its own shade', RUST],
    'source': "'/home/claude/build-54-barn/first pass/render_final.py', the 'hay ladder' (lines 510-519)",
    'views': 'reads from every side; it needs the wall it rests on at +Y (drawn alone it leans on air)',
    'trap': 'the origin is the foot of the wall, not the ladder: the wall face is the plane y = 0 behind it and the feet stand about a quarter '
            'of its length in front (0.95 to 1.05 m at 3.6 m); put the origin on your wall face and the top rests on it at any length',
}

SPACING = 0.27          # rung to rung
W_FOOT = 0.46           # rail to rail (middle to middle) at the foot
W_TOP = 0.36            # and at the top (for 3.6 m; a longer ladder narrows the same per metre)


def build(collection, seed=0, length=3.6):
    length = barn.number('ladder length', length, 1.0, 9.0)
    rng = shapes.rng_for(PART, seed)
    lean = math.radians(15.0 + rng.uniform(-1.0, 1.0))
    wood = barn.shaded_surface('rough_wood', PART, Grime=0.55, Wet=0.1, **{'Mud height': 0.25})
    objects = []
    along = Vector((0.0, math.sin(lean), math.cos(lean)))          # up the rails
    out = Vector((0.0, math.cos(lean), -math.sin(lean)))           # square to the ladder, towards the wall
    depth_foot, depth_top = 0.074, 0.064                           # the rails, towards the wall
    thick_foot, thick_top = 0.044, 0.037                           # and across
    w_top = max(0.3, W_FOOT - (W_FOOT - W_TOP) * length / 3.6)
    # the top of the rails' back face touches the wall (y = 0)
    foot_y = -(length * math.sin(lean) + depth_top / 2 * math.cos(lean))

    def rail_centre(side, s, bow, wob):
        x = side * (W_FOOT + (w_top - W_FOOT) * s) / 2
        return Vector((x, foot_y, 0.0)) + along * (s * length) + out * (bow * 4 * s * (1 - s)) + Vector((wob * math.sin(math.pi * s * 1.5), 0, 0))

    # ------------------------------------------------------------------ the two rails
    for side in (-1, 1):
        bow = rng.uniform(-0.014, 0.014)
        wob = rng.uniform(-0.006, 0.006)
        cuts = [rng.uniform(0.003, 0.012) for _ in range(4)]
        rail = shapes.Shape()
        rings = []
        steps = 18
        for i in range(steps + 1):
            s = i / steps
            c = rail_centre(side, s, bow, wob)
            nxt = rail_centre(side, min(1.0, s + 0.01), bow, wob) - rail_centre(side, max(0.0, s - 0.01), bow, wob)
            d = nxt.normalized()
            across = Vector((1.0, 0.0, 0.0))
            across = (across - d * across.dot(d)).normalized()
            n = d.cross(across).normalized()
            if n.dot(out) < 0:
                n = -n
            half_t = (thick_foot + (thick_top - thick_foot) * s) / 2
            half_d = (depth_foot + (depth_top - depth_foot) * s) / 2
            section = []
            for k, (sx, sy) in enumerate(((1, 1), (-1, 1), (-1, -1), (1, -1))):
                cut = cuts[k] * (0.7 + 0.6 * abs(math.sin(7 * s + k)))
                section.append((sx * half_t, sy * (half_d - cut)))
                section.append((sx * (half_t - cut), sy * half_d))
            # keep the outline going one way round
            ordered = [section[0], section[1], section[3], section[2], section[4], section[5], section[7], section[6]]
            pts = [c + across * px + n * py + Vector((rng.uniform(-0.0012, 0.0012), rng.uniform(-0.0012, 0.0012), 0.0)) for (px, py) in ordered]
            if i == 0:                                   # the foot cut level, standing flat on the ground
                pts = [p - along * (p.z / along.z) for p in pts]
            rings.append(rail._verts(pts))
        rail._rings(rings, True, True, True)
        mid = rail_centre(side, 0.5, bow, wob)
        frame = shapes.to4(shapes.frame_along(along, up=out), mid)
        objects.append(rail.finish('ladder rail %s' % ('left' if side < 0 else 'right'), collection, wood, smooth=True, sharp=30,
                                   local=frame, shift=0.4, rng=rng))
        if side < 0:
            left_bow, left_wob = bow, wob
        else:
            right_bow, right_wob = bow, wob

    # ------------------------------------------------------------------ rungs, through the rails, their ends flush with the outer faces
    rungs = []
    s_len = 0.28
    while s_len < length - 0.17:
        rungs.append(s_len / length)
        s_len += SPACING
    rods = shapes.Shape()
    tie_at = {1, len(rungs) // 2, len(rungs) - 2} if len(rungs) >= 4 else {0}
    for k, s in enumerate(rungs):
        a = rail_centre(-1, s, left_bow, left_wob)
        b = rail_centre(1, s, right_bow, right_wob)
        half_t = (thick_foot + (thick_top - thick_foot) * s) / 2
        dirn = (b - a).normalized()
        a_out, b_out = a - dirn * half_t, b + dirn * half_t
        span = (b_out - a_out).length
        centre = (a_out + b_out) / 2 - out * 0.004
        frame = shapes.to4(shapes.frame_along(dirn, up=out), centre)
        rung = shapes.Shape()
        r_mid = rng.uniform(0.0165, 0.0185)
        rung.lathe([(0.0, -span / 2), (0.0128, -span / 2), (0.0132, -span / 2 + 2 * half_t), (r_mid * 0.96, -span / 4), (r_mid, 0.0),
                    (r_mid * 0.96, span / 4), (0.0132, span / 2 - 2 * half_t), (0.0128, span / 2), (0.0, span / 2)], segments=10, matrix=frame)
        objects.append(rung.finish('ladder rung %d' % (k + 1), collection, wood, smooth=True, sharp=50, local=frame, shift=0.2, rng=rng))
        if k in tie_at:
            # an iron tie rod just under the rung, square nuts on the rails' outer faces
            below = -along * 0.045
            ra, rb = a_out + below - dirn * 0.012, b_out + below + dirn * 0.012
            rods.cylinder(ra, rb, 0.0045, segments=8)
            for end, sgn in ((a_out + below, -1), (b_out + below, 1)):
                rods.box(end + dirn * (sgn * 0.004), (0.016, 0.016, 0.016), rotation=shapes.frame_along(dirn, up=out))
    objects.append(rods.finish('ladder tie rods', collection, RUST, smooth=True, sharp=40))
    return objects
