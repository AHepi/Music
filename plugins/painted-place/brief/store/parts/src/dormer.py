"""
dormer: a slate-hung dormer of a tenement's garret, about 1900: its two cheeks and its front hung with slates, a
small two-over-two sash window between timber corner posts, its own little gabled slate roof with painted barge
boards and a finial, and lead flashings where it meets the main roof: an apron dressed over the slates in front with
a rolled edge, step flashings along the foot of each cheek, lead valleys where its roof runs into the main roof, and a
lead roll on its ridge. Lit, the window glows warm and a small hidden light in front of it lights the sill and the
lead; dark, the glass is the night's navy. It is built to stand on a main roof of the pitch you give, the cheeks' feet
and the valleys lying on that slope.

The origin is on the main roof's surface, under the middle of the dormer's front; that surface is the plane rising
towards +Y at `pitch` degrees through the origin, and the lead apron lies on it down to 0.15 m below the origin.
Front towards -Y, down the roof.

Options:
    lit      True (default): the window lit; False: dark
    pitch    the main roof's pitch, degrees (default 36; 25 to 55)
    seed     the slates' laying, the lead's weathering, the finial's lean

Where it came from: '/home/claude/build-55-street/fronts/render_final.py', Building.details(), the dormers (lines
396-418): a stone box, a slate gable as two faces, a triangle, a glass plane with four bars and a light. Rebuilt here
slate-hung, with a real sash window, its own roof meeting the main roof, and the lead that keeps the rain out.
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

PART = 'dormer'

CARD = {
    'name': PART,
    'what': "a slate-hung garret dormer: slates on its cheeks and front, a small two-over-two sash window between corner posts, its "
            "own gabled slate roof with barge boards and a finial, lead apron, step flashings, valleys and ridge roll; lit warm "
            "with a small hidden light, or dark",
    'size_m': (1.44, 2.63, 2.06),
    'options': {
        'lit': 'True (default): the window glows warm and a hidden 4 W light in front of it lights the sill and the lead; False: dark navy glass',
        'pitch': "the main roof's pitch in degrees, so the cheeks and valleys lie on it (default 36; 25 to 55)",
        'seed': "the slates' laying, the lead's weathering, the finial's lean (default 0)",
    },
    'materials': [street.SLATE, street.WOOD, street.LIT_GLASS, street.DARK_GLASS, street.RECESS, 'PART • dormer: old lead'],
    'source': "'/home/claude/build-55-street/fronts/render_final.py', Building.details(), the dormers (lines 396-418)",
    'views': 'reads from the front and both sides; from behind, its open back shows unless your roof lies under it',
    'trap': "the origin is on the roof's surface under the middle of the dormer's front, and the main roof rises towards +Y through "
            "it: give your roof's pitch, stand the origin on the slope and turn it to face down the roof; it does not cut your roof, "
            "which must lie under it (the cheeks' feet are open), and its apron reaches 0.15 m lower down the slope",
    'foot_z': -0.15,     # the apron's rolled lower edge, down the slope below the origin (the origin is on the roof under the front)
}

DROP = 0.15          # how far the apron reaches down the roof, in height, below the dormer's front
HALF = 0.55          # half the dormer's width, outside the cheeks
CHEEK = 0.06
EAVES = 1.14         # the cheeks' top, where the little roof starts
OVER = 0.08          # the little roof's overhang
WIN_W, WIN_H = 0.86, 0.86


def slab(collection, name, outline, origin, ex, ey, z0, z1, material, rng):
    """A flat piece (a slate-hung cheek, a roof slope) from an outline [(u, v), ...] in the plane through `origin`
    along ex and ey, given thickness z0..z1 along ex x ey; its own frame is (ex, ey), so the slate material's slates
    lie along ex and its courses climb ey."""
    ex, ey = Vector(ex).normalized(), Vector(ey).normalized()
    ez = ex.cross(ey).normalized()
    frame = shapes.to4(Matrix((ex, ey, ez)).transposed(), origin)
    shape = shapes.Shape()
    shape.prism(outline, z0, z1, matrix=frame)
    return shape.finish(name, collection, material, smooth=False, local=frame, shift=0.3, rng=rng)


def plate(shape, corners, up, thickness=0.003):
    """A thin flat sheet (lead) on four corner points, `thickness` along `up`."""
    up = Vector(up).normalized() * thickness
    lo = shape._verts([Vector(c) for c in corners])
    hi = shape._verts([Vector(c) + up for c in corners])
    shape._rings([lo, hi], True, True, True)


def build(collection, seed=0, lit=True, pitch=36.0):
    lit = street.flag('dormer lit', lit)
    pitch = barn.number('dormer pitch', pitch, 25.0, 55.0)
    rng = shapes.rng_for(PART, seed)
    tan_p = math.tan(math.radians(pitch))
    roof_up = Vector((0.0, -math.sin(math.radians(pitch)), math.cos(math.radians(pitch))))   # the main roof's normal

    AP = DROP / tan_p    # the apron's run down the roof, in front of the dormer

    def zr(y):
        """The main roof's surface under a point."""
        return y * tan_p

    def y_at(z):
        """Where the main roof reaches height z."""
        return z / tan_p

    objects = []
    z_foot = zr(0.0)
    sill_z = z_foot + 0.13
    ridge_z = EAVES + HALF + 0.0       # the little roof at 45 degrees, from the cheeks' outer faces
    y_cheek = y_at(EAVES)
    y_ridge = y_at(ridge_z + 0.02)
    y_eave = y_at(EAVES - OVER)
    slate = street.SLATE

    # ------------------------------------------------------------------ cheeks and front, slate-hung
    for side in (-1, 1):
        x = side * HALF
        outline = [(0.0, z_foot), (y_cheek, EAVES), (0.0, EAVES)]
        z0, z1 = (-CHEEK, 0.0) if side > 0 else (0.0, CHEEK)
        objects.append(slab(collection, 'dormer cheek %s' % ('right' if side > 0 else 'left'), outline, (x, 0.0, 0.0), (0, 1, 0), (0, 0, 1),
                            z0, z1, slate, rng))
    front = [(-HALF, z_foot), (HALF, z_foot), (HALF, sill_z), (-HALF, sill_z)]
    objects.append(slab(collection, 'dormer front under the sill', front, (0.0, 0.0, 0.0), (1, 0, 0), (0, 0, 1), 0.0, 0.03, slate, rng))
    gable = [(-HALF, EAVES), (HALF, EAVES), (0.0, EAVES + HALF)]
    objects.append(slab(collection, 'dormer gable', gable, (0.0, 0.0, 0.0), (1, 0, 0), (0, 0, 1), 0.0, 0.03, slate, rng))

    # ------------------------------------------------------------------ the little roof: two slopes running back into the main roof
    run = math.hypot(HALF + OVER, HALF + OVER)
    for side in (-1, 1):
        origin = Vector((side * (HALF + OVER), -0.10, EAVES - OVER))
        ey = Vector((-side, 0.0, 1.0))
        ex = Vector((0.0, 1.0, 0.0)) if side > 0 else Vector((0.0, -1.0, 0.0))
        back_eave = y_eave + 0.10
        back_ridge = y_ridge + 0.10
        if side > 0:
            outline = [(0.0, 0.0), (back_eave, 0.0), (back_ridge, run), (0.0, run)]
        else:
            outline = [(0.0, 0.0), (0.0, run), (-back_ridge, run), (-back_eave, 0.0)]
        objects.append(slab(collection, 'dormer roof %s' % ('right' if side > 0 else 'left'), outline, origin, ex, ey, 0.0, 0.03, slate, rng))

    # ------------------------------------------------------------------ timber: corner posts, head, barge boards, finial; the window
    wood = shapes.Shape()
    glass = shapes.Shape()
    for side in (-1, 1):
        wood.box((side * (HALF - 0.06), -0.025, (z_foot + EAVES) / 2), (0.12, 0.05, EAVES - z_foot))
    wood.box((0.0, -0.025, (sill_z + WIN_H + EAVES) / 2 + 0.0), (2 * HALF - 0.004, 0.044, EAVES - sill_z - WIN_H))
    wood.box((0.0, -0.06, EAVES - 0.02), (2 * HALF + 0.04, 0.03, 0.06))                     # a fascia under the gable
    street.sash_window(wood, glass, 0.0, -0.035, sill_z, WIN_W, WIN_H, bars=1, frame_w=0.07, depth=0.12)
    for side in (-1, 1):
        a = Vector((side * (HALF + OVER + 0.01), -0.115, EAVES - OVER - 0.02))
        b = Vector((0.0, -0.115, EAVES + HALF + 0.0))
        drop = Vector((0.0, 0.0, -0.075))
        wood.beam(a + drop * 0.5, b + drop * 0.5 + Vector((0.0, 0.0, -0.02)), 0.03, 0.15)
    wood.box((0.0, -0.115, EAVES + HALF - 0.07), (0.09, 0.034, 0.2))                         # king post where the boards meet
    lean = math.radians(rng.uniform(-3.0, 3.0))
    finial = Matrix.Translation((0.0, -0.115, EAVES + HALF - 0.08)) @ Matrix.Rotation(lean, 4, 'Y')
    wood.lathe([(0.0, 0.0), (0.03, 0.0), (0.03, 0.12), (0.045, 0.16), (0.02, 0.2), (0.03, 0.24), (0.0, 0.3)], segments=10, matrix=finial)
    objects.append(wood.finish('dormer timber', collection, street.WOOD, smooth=False))
    objects.append(glass.finish('dormer glass', collection, street.LIT_GLASS if lit else street.DARK_GLASS, smooth=False))

    # the inside, dark, so nothing shows through a gap
    inner = shapes.Shape()
    frame = Matrix(((0.0, 0.0, 1.0, -HALF + CHEEK), (1.0, 0.0, 0.0, 0.0), (0.0, 1.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0)))
    inner.prism([(0.1, zr(0.1) + 0.01), (y_cheek - 0.05, EAVES - 0.01), (0.1, EAVES - 0.01)], 0.0, 2 * (HALF - CHEEK), matrix=frame)
    objects.append(inner.finish('dormer inside', collection, street.RECESS, smooth=False))

    # ------------------------------------------------------------------ lead: apron, step flashings, valleys, ridge roll
    lead = shapes.Shape()
    w = HALF + 0.12
    plate(lead, [(-w, -AP, zr(-AP) + 0.004), (w, -AP, zr(-AP) + 0.004), (w, -0.035, zr(-0.035) + 0.004), (-w, -0.035, zr(-0.035) + 0.004)], roof_up)
    lead.box((0.0, -0.037, z_foot + 0.06), (2 * w, 0.004, 0.12))                                  # turned up the front
    lead.cylinder((-w, -AP + 0.004, -DROP + 0.008), (w, -AP + 0.004, -DROP + 0.008), 0.008, segments=8)   # its rolled lower edge
    for side in (-1, 1):
        x0 = side * HALF
        x1 = side * (HALF + 0.12)
        plate(lead, [(x0, -0.03, zr(-0.03) + 0.004), (x1, -0.03, zr(-0.03) + 0.004), (x1, y_cheek, zr(y_cheek) + 0.004),
                     (x0, y_cheek, zr(y_cheek) + 0.004)], roof_up)
        # the upstand up the cheek's foot, stepped with the courses
        steps = 6
        for k in range(steps):
            ya = -0.03 + (y_cheek + 0.03) * k / steps
            yb = -0.03 + (y_cheek + 0.03) * (k + 1) / steps
            zb = zr(ya) + 0.0
            lead.box((x0 + side * 0.003, (ya + yb) / 2, zb + 0.05), (0.004, yb - ya, max(0.06, zr(yb) - zr(ya) + 0.06)))
        # the valley where the little roof meets the main roof
        a = Vector((side * (HALF + OVER), y_eave, 0.0))
        b = Vector((0.0, y_ridge, 0.0))
        d = (b - a).normalized()
        n = Vector((d.y, -d.x, 0.0)) * 0.11
        corners = []
        for p in (a - n, a + n, b + n, b - n):
            corners.append((p.x, p.y, zr(p.y) + 0.004))
        plate(lead, corners, roof_up)
    lead.cylinder((0.0, -0.10, ridge_z + 0.02), (0.0, y_ridge, ridge_z + 0.02), 0.022, segments=10)
    objects.append(lead.finish('dormer lead', collection, street.lead(PART), smooth=True, sharp=35))

    if lit:
        objects.append(street.hidden_light(collection, 'dormer light', (0.0, -0.5, sill_z + 0.2), 4.0, radius=0.1))
    return objects
