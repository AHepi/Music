"""
plank_door: a ledged and braced plank door of a barn, stable or cart shed, about 1900: upright planks of rough weathered
wood (each its own width and shade, a few rotted ragged at the foot, small gaps where they have shrunk), three cross
ledges and two diagonal braces nailed on the back (+Y), the braces rising from the hinge side as a real door's do; on
the front (-Y) long iron strap hinges with bolt heads, their eyes on pins at the hinge edge, a Suffolk thumb latch, rows
of clenched nail heads, and rust run down the planks under each strap. It is hung on its hinge edge and can stand open
by an angle, swung out towards the front as barn and stable doors open. The origin is the middle of the doorway it
closes, at the foot; the planks stop 1.2 cm above the ground.

Options:
    width    the door's width, metres (default 1.0; a cart door leaf is about 1.8)
    height   the door's height, metres (default 2.0; a cart door about 3.6)
    angle    degrees it stands open, swung out towards the front (-Y) on its hinges; negative swings it in (default 0)
    hinges   'left' (default) or 'right': the hinge edge, seen from the front
    seed     the planks' widths, shades and rot, the gaps, the rust runs

Where it came from: '/home/claude/build-54-barn/first pass/render_final.py', plank_door() (line 401): one mesh of
boxes (planks, ledges, braces, flat bars for hinges) mirrored by a negative scale for the right-hand leaf; rebuilt here
with each plank its own piece of wood, braces cut to sit on the ledges, real strap hinges with eyes and pins, a latch,
nail heads and rust runs, and no mirroring (a negative scale turns a photographed surface inside out).
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

PART = 'plank_door'
RUST = 'RUST • rain-aged iron'
NAILS = 'MADE • rusty nail heads'
STAIN = 'MADE • rust stain'
HINGES = ('left', 'right')

CARD = {
    'name': PART,
    'what': 'a ledged and braced plank door: upright weathered planks, ledges and a Z of braces on the back (+Y), long iron strap hinges, '
            'a thumb latch and nail heads on the front, rust run under the straps; hung on its hinge edge, standing open by an angle',
    'size_m': (1.06, 0.10, 2.0),
    'options': {
        'width': "the door's width, metres (default 1.0; a cart door leaf is about 1.8)",
        'height': "the door's height, metres (default 2.0; a cart door about 3.6)",
        'angle': 'degrees it stands open, swung out towards the front (-Y) on its hinges; negative swings it in (default 0)',
        'hinges': "'left' (default) or 'right': the hinge edge, seen from the front",
        'seed': "the planks' widths, shades and rot, the gaps, the rust runs (default 0)",
    },
    'materials': ['SURFACE • rough_wood (plank_door), each piece its own shade', RUST, NAILS, STAIN],
    'source': "'/home/claude/build-54-barn/first pass/render_final.py', plank_door() (line 401)",
    'views': 'reads from every side: the front (-Y) shows the planks, strap hinges and latch; the back (+Y) the ledges and braces',
    'trap': 'the origin is the middle of the doorway, not the hinge: the door swings on its hinge edge (x = -width/2 when hinges is left), '
            'so opened 90 degrees it stands a whole width out in front (-Y) of the doorway; the planks stop 1.2 cm above the ground',
}

THICK = 0.03           # the planks
LEDGE_T = 0.028        # ledges and braces, on the back
STRAP_T = 0.006
CLEAR = 0.012          # the gap under the door


def build(collection, seed=0, width=1.0, height=2.0, angle=0.0, hinges='left'):
    width = barn.number('plank_door width', width, 0.4, 4.0)
    height = barn.number('plank_door height', height, 0.6, 5.0)
    angle = barn.number('plank_door angle', angle, -180.0, 180.0)
    if hinges not in HINGES:
        raise ValueError("plank_door hinges is 'left' or 'right', not %r" % (hinges,))
    rng = shapes.rng_for(PART, seed)
    side = -1.0 if hinges == 'left' else 1.0          # the hinge edge is at x = side * width / 2
    half = width / 2.0
    front, back = -THICK / 2.0, THICK / 2.0
    wood = barn.shaded_surface('rough_wood', PART, Grime=0.6, Wet=0.15, **{'Mud height': 0.32})
    objects = []

    def x_at(u):
        """x of a point u metres in from the hinge edge."""
        return side * (half - u)

    # ------------------------------------------------------------------ the planks
    count = max(3, int(round(width / 0.15)))
    widths = [rng.uniform(0.82, 1.18) for _ in range(count)]
    scale = width / sum(widths)
    widths = [w * scale for w in widths]
    x0 = -half
    for k, w in enumerate(widths):
        gap = rng.choice((0.002, 0.003, 0.004, 0.007)) if 0 < k else 0.0
        a, b = x0 + gap / 2.0, x0 + w
        x0 += w
        rotten = rng.random() < 0.35
        plank = shapes.Shape()
        y_off = rng.uniform(-0.0006, 0.0006)
        top = height + rng.uniform(-0.004, 0.002)
        feet = [CLEAR + (rng.uniform(0.0, 0.045) if rotten else rng.uniform(0.0, 0.004)) for _ in range(2)]
        pts = [Vector((a, front + y_off, feet[0])), Vector((b, front + y_off, feet[1])), Vector((b, back + y_off, feet[1] + rng.uniform(-0.004, 0.004))),
               Vector((a, back + y_off, feet[0] + rng.uniform(-0.004, 0.004))),
               Vector((a, front + y_off, top)), Vector((b, front + y_off, top)), Vector((b, back + y_off, top)), Vector((a, back + y_off, top))]
        verts = plank._verts(pts)
        for quad in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
            plank._face([verts[i] for i in quad])
        centre = Vector(((a + b) / 2, 0.0, height / 2))
        objects.append(plank.finish('plank_door plank %d' % (k + 1), collection, wood, chamfer=0.003, local=shapes.to4(None, centre),
                                    shift=0.4, rng=rng))

    # ------------------------------------------------------------------ ledges and braces on the back
    ledge_h = 0.15 if width <= 1.3 else 0.18
    if height >= 1.4:
        ledges = [CLEAR + 0.22, (CLEAR + 0.22 + height - 0.2) / 2.0, height - 0.2]
    else:
        ledges = [CLEAR + 0.15, height - 0.15]
    y_ledge = back + LEDGE_T / 2.0
    for k, z in enumerate(ledges):
        objects.append(shapes.timber(collection, 'plank_door ledge %d' % (k + 1), (-half + 0.02, y_ledge, z), (half - 0.02, y_ledge, z),
                                     LEDGE_T, ledge_h, wood, rng=rng, chamfer=0.005, shift=0.4))
    brace_w = 0.12 if width <= 1.3 else 0.15
    braces = []
    for k in range(len(ledges) - 1):
        z_lo = ledges[k] + ledge_h / 2.0              # on top of the lower ledge, at the hinge side
        z_hi = ledges[k + 1] - ledge_h / 2.0          # under the upper ledge, at the latch side
        hw = brace_w / 2.0
        for _ in range(3):
            # half its width measured level (so its ends sit flat on the ledges), and its ends kept 3 cm inside the edges
            u_lo, u_hi = 0.03 + hw, width - 0.03 - hw
            slope = math.atan2(abs(z_hi - z_lo), max(0.05, u_hi - u_lo))
            hw = min((brace_w / 2.0) / max(math.sin(slope), 0.25), width * 0.22)
        u_lo, u_hi = 0.03 + hw, width - 0.03 - hw
        p_lo = Vector((x_at(u_lo), 0.0, z_lo))
        p_hi = Vector((x_at(u_hi), 0.0, z_hi))
        run = p_hi - p_lo
        shift_x = Vector((hw, 0.0, 0.0))
        # the brace's outline, in the door's plane; its ends cut level against the ledges
        corners = [p_lo - shift_x, p_lo + shift_x, p_hi + shift_x, p_hi - shift_x]
        brace = shapes.Shape()
        lo = brace._verts([Vector((c.x, back, c.z)) for c in corners])
        hi = brace._verts([Vector((c.x, back + LEDGE_T, c.z)) for c in corners])
        brace._rings([lo, hi], True, True, True)
        along = run.normalized()
        frame = shapes.to4(shapes.frame_along(along, up=Vector((0.0, 1.0, 0.0))), (p_lo + p_hi) / 2 + Vector((0.0, back + LEDGE_T / 2, 0.0)))
        objects.append(brace.finish('plank_door brace %d' % (k + 1), collection, wood, chamfer=0.004, local=frame, shift=0.4, rng=rng))
        braces.append((p_lo, p_hi))

    # ------------------------------------------------------------------ strap hinges on the front, their eyes on pins
    axis_x = side * (half + 0.014)
    axis_y = front - 0.011
    straps_at = [ledges[0], ledges[-1]] if height < 2.6 else ledges
    strap_len = max(0.42, 0.74 * width)
    iron = shapes.Shape()
    bolts = shapes.Shape()
    for z_s in straps_at:
        outline = []
        steps = 10
        for i in range(steps + 1):                     # top edge, from the hinge out
            u = -0.004 + (strap_len - 0.03) * i / steps
            w = 0.046 - 0.014 * (u / strap_len)
            outline.append((u, w / 2))
        for i in range(1, 8):                          # the rounded end
            a = math.pi / 2 - math.pi * i / 8
            w_end = 0.032
            outline.append((strap_len - 0.03 + 0.026 * math.cos(a), (w_end / 2 + 0.004) * math.sin(a)))
        for i in range(steps, -1, -1):                 # bottom edge, back to the hinge
            u = -0.004 + (strap_len - 0.03) * i / steps
            w = 0.046 - 0.014 * (u / strap_len)
            outline.append((u, -w / 2))
        lo = iron._verts([Vector((x_at(u), front - STRAP_T, z_s + v)) for (u, v) in outline])
        hi = iron._verts([Vector((x_at(u), front - 0.0004, z_s + v)) for (u, v) in outline])
        iron._rings([lo, hi], True, True, True)
        # the eye rolled round the pin, and the pin standing out above and below it
        iron.cylinder((axis_x, axis_y, z_s - 0.023), (axis_x, axis_y, z_s + 0.023), 0.0125, segments=14)
        iron.box(((axis_x + x_at(-0.002)) / 2, (axis_y + front - STRAP_T / 2) / 2, z_s), (abs(axis_x - x_at(-0.002)) + 0.004, 0.012, 0.044))
        iron.cylinder((axis_x, axis_y, z_s - 0.05), (axis_x, axis_y, z_s + 0.05), 0.0065, segments=10)
        for i, u in enumerate((0.07, 0.07 + (strap_len - 0.1) * 0.35, 0.07 + (strap_len - 0.1) * 0.7, strap_len - 0.03)):
            bolts.sphere((x_at(u), front - STRAP_T - 0.001, z_s), 0.0085, segments=10, rings=5, squash=(1.0, 0.45, 1.0))
    # ------------------------------------------------------------------ the Suffolk thumb latch
    u_l = width - 0.11
    x_l = x_at(u_l)
    z_l = min(1.05, 0.52 * height)
    for dz in (0.105, -0.105):                         # the two cusped plates
        plate = [(0.0, 0.04), (0.012, 0.022), (0.016, 0.0), (0.012, -0.022), (0.0, -0.04), (-0.012, -0.022), (-0.016, 0.0), (-0.012, 0.022)]
        lo = iron._verts([Vector((x_l + px, front - 0.003, z_l + dz + pz)) for (px, pz) in plate])
        hi = iron._verts([Vector((x_l + px, front - 0.0004, z_l + dz + pz)) for (px, pz) in plate])
        iron._rings([lo, hi], True, True, True)
    grip = [Vector((x_l, front - 0.003, z_l + 0.095)), Vector((x_l, front - 0.03, z_l + 0.07)), Vector((x_l, front - 0.038, z_l)),
            Vector((x_l, front - 0.03, z_l - 0.07)), Vector((x_l, front - 0.003, z_l - 0.095))]
    iron.sweep(shapes.smooth_path(grip, steps=4), 0.0065, sides=8)
    iron.box((x_l, front - 0.016, z_l + 0.15), (0.016, 0.03, 0.006), rotation=Matrix.Rotation(math.radians(-18), 3, 'X'))     # the thumb lever
    # on the back: the latch bar, pivoted towards the middle, reaching past the free edge to the keeper
    z_bar = z_l + 0.15
    bar_in = x_at(width - 0.32)
    bar_out = x_at(width + 0.03)
    iron.box(((bar_in + bar_out) / 2, back + 0.003, z_bar), (abs(bar_out - bar_in), 0.006, 0.022))
    iron.cylinder((bar_in, back, z_bar), (bar_in, back + 0.012, z_bar), 0.007, segments=8)
    iron.box((x_at(width - 0.06), back + 0.008, z_bar + 0.024), (0.014, 0.016, 0.03))          # the staple that guides it
    objects.append(iron.finish('plank_door ironwork', collection, RUST, smooth=True, sharp=40))

    # ------------------------------------------------------------------ nail heads: through each plank into the ledges and braces
    x0 = -half
    for w in widths:
        xc = x0 + w / 2
        x0 += w
        for z in ledges:
            for dx, dz in ((-0.25 * w, 0.045), (0.25 * w, -0.045)):
                bolts.sphere((xc + dx, front - 0.0015, z + dz + rng.uniform(-0.006, 0.006)), 0.0048, segments=8, rings=4, squash=(1.0, 0.5, 1.0))
        for (p_lo, p_hi) in braces:
            t = (xc - p_lo.x) / (p_hi.x - p_lo.x) if abs(p_hi.x - p_lo.x) > 1e-6 else 0.5
            if 0.02 < t < 0.98:
                bolts.sphere((xc, front - 0.0015, p_lo.z + (p_hi.z - p_lo.z) * t), 0.0048, segments=8, rings=4, squash=(1.0, 0.5, 1.0))
    objects.append(bolts.finish('plank_door bolt and nail heads', collection, NAILS, smooth=True, sharp=None))

    # ------------------------------------------------------------------ rust run down the planks under each strap
    stain = shapes.Shape()
    barn.number_layers(stain, points=('fade',))
    fade_layer = stain.bm.verts.layers.float['fade']
    for z_s in straps_at:
        top = z_s - 0.02
        cols, rows = 14, 6
        runs = [rng.uniform(0.12, 0.42) for _ in range(cols + 1)]
        grid = []
        for i in range(cols + 1):
            u = 0.02 + (strap_len - 0.02) * i / cols
            column = []
            for j in range(rows + 1):
                drop = runs[i] * j / rows
                v = stain.bm.verts.new((x_at(u), front - 0.0012, max(CLEAR + 0.01, top - drop)))
                edge = min(i, cols - i) / 2.0
                v[fade_layer] = min(1.0, j / rows + max(0.0, 1.0 - edge) * 0.6)
                column.append(v)
            grid.append(column)
        for i in range(cols):
            for j in range(rows):
                stain._face([grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]])
    objects.append(stain.finish('plank_door rust runs', collection, STAIN, smooth=True, sharp=None, shadow=False))

    # ------------------------------------------------------------------ hang it: swing the whole door on the hinge pins
    if abs(angle) > 1e-6:
        shapes.tilt_all(objects, rz=math.radians(angle) * (-1.0 if side < 0 else 1.0), pivot=(axis_x, axis_y, 0.0))
    return objects
