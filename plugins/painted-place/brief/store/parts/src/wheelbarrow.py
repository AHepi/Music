"""
wheelbarrow: a wooden builder's barrow of about 1900: two long ash stringers that are the handles at one end and hold
the wheel between them at the other, two legs with a cross-brace, a body of boards (a floor, flared sideboards, a
front board leaning out over the wheel, a back board), iron straps and bolt heads, and one wooden spoked wheel on an
iron tyre. The wheel is at the front (-Y); the handles reach back (+Y). Loaded with stove ash and clinker, or coal, or
nothing. Foot at z = 0 (the wheel and the legs' feet).

Options:
    loaded   'ash' (default): a heap of grey stove ash with clinker lumps; 'coal': a heap of coal; 'none': empty
    seed     the boards' shades, the wheel's turn, the heap

Where it came from: '/home/claude/build-51-chapel/dress/dress_block.py', wheelbarrow() (line 110): boxes for the
body, beams for the handles and legs, a solid disc for the wheel; rebuilt here with a real spoked wheel, a body of
single boards, and the ash and clinker it carried in that picture.
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

PART = 'wheelbarrow'
BOARDS = 'MADE • weathered boards, peeling paint'
IRON = 'IRON • soot-black lamp posts'
RUST = 'RUST • rain-aged iron'
LOADS = ('ash', 'coal', 'none')

CARD = {
    'name': PART,
    'what': "a wooden builder's barrow: one iron-tyred spoked wheel at the front (-Y), two handles back, legs, a flared body of boards; "
            "loaded with ash and clinker, coal, or nothing",
    'size_m': (0.69, 1.63, 0.85),
    'options': {
        'loaded': "'ash' (default): a heap of stove ash with clinker; 'coal': a heap of coal; 'none': empty",
        'seed': "the boards' shades, the wheel's turn, the heap (default 0)",
    },
    'materials': [BOARDS + " (reads 'board_tone')", 'SURFACE • rough_wood (wheelbarrow)', IRON, RUST,
                  'PART • wheelbarrow: stove ash', 'PART • wheelbarrow: clinker', 'PART • wheelbarrow: coal'],
    'source': "'/home/claude/build-51-chapel/dress/dress_block.py', wheelbarrow() (line 110) and the ash in it (blob 'ash in barrow')",
    'views': 'reads from every side',
    'trap': 'the handles reach 0.85 m behind the origin (+Y) and the wheel 0.77 m in front: leave it room',
}

WHEEL_R = 0.225
WHEEL_Y = -0.55
GRIP_Y = 0.85


def ash_material():
    return shapes.part_material(PART, 'stove ash', _ash)


def _ash(m, nodes, links, principled):
    """Fine grey stove ash, pale for the look but still dull: darker where it is damp, a soft lumpy bump."""
    vec = shapes.own_coordinates(nodes)
    fine = shapes.noise_fac(nodes, links, vec, 18.0, detail=5.0, roughness=0.65)
    damp = shapes.noise_fac(nodes, links, vec, 3.0, detail=3.0)
    colour = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, fine, 0.35, 0.65), (0.11, 0.11, 0.115), (0.19, 0.19, 0.195))
    colour = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, damp, 0.5, 0.65, 0.0, 0.7), colour, (0.06, 0.06, 0.065))
    links.new(colour, principled.inputs['Base Color'])
    principled.inputs['Roughness'].default_value = 0.95
    principled.inputs['Specular IOR Level'].default_value = 0.2
    links.new(shapes.bump(nodes, links, fine, 0.3, 0.004), principled.inputs['Normal'])
    m.diffuse_color = (0.15, 0.15, 0.155, 1.0)


def clinker_material():
    return shapes.part_material(PART, 'clinker', lambda m, n, l, p: _clinker(m, n, l, p))


def _clinker(m, nodes, links, principled):
    """Clinker: burnt-out coal, grey-black and pitted, duller than coal."""
    vec = shapes.own_coordinates(nodes)
    pits = shapes.noise_fac(nodes, links, vec, 60.0, detail=3.0, roughness=0.7)
    colour = shapes.mix_colour(nodes, links, shapes.map_range(nodes, links, pits, 0.4, 0.6), (0.03, 0.03, 0.032), (0.075, 0.072, 0.07))
    links.new(colour, principled.inputs['Base Color'])
    principled.inputs['Roughness'].default_value = 0.85
    links.new(shapes.bump(nodes, links, pits, 0.5, 0.004), principled.inputs['Normal'])
    m.diffuse_color = (0.05, 0.05, 0.05, 1.0)


def build(collection, seed=0, loaded='ash'):
    if loaded not in LOADS:
        raise ValueError("wheelbarrow loaded is one of %s, not %r" % (', '.join(repr(s) for s in LOADS), loaded))
    rng = shapes.rng_for(PART, seed)
    objects = []
    wood = shapes.surface_copy('rough_wood', PART, Grime=0.55, Darken=0.5, **{'Mud height': 0.3})
    boards = shapes.material(BOARDS)
    tones = [rng.uniform(0.0, 1.0) for _ in range(20)]

    def timber(name, a, b, w, h, material=None, **kw):
        obj = shapes.timber(collection, 'wheelbarrow %s' % name, a, b, w, h, material or wood, rng=rng, shift=0.4, **kw)
        objects.append(obj)
        return obj

    def board(name, a, b, w, h, k, **kw):
        return timber(name, a, b, w, h, boards, tone=tones[k % len(tones)], chamfer=0.003, **kw)

    # ------------------------------------------------------------------ stringers (the handles), legs, brace
    axle = Vector((0.0, WHEEL_Y, WHEEL_R))
    for side in (-1, 1):
        front = Vector((side * 0.075, WHEEL_Y - 0.06, WHEEL_R + 0.09))
        back = Vector((side * 0.30, GRIP_Y - 0.14, 0.56))
        timber('stringer %s' % ('left' if side < 0 else 'right'), front, back, 0.045, 0.065)
        # the grip: the stringer's end rounded, a little further back
        grip = shapes.Shape()
        grip.lathe([(0.0, 0.0), (0.02, 0.0), (0.023, 0.03), (0.021, 0.14), (0.0, 0.15)], segments=14,
                   matrix=shapes.to4(shapes.frame_along(back - front), back + (back - front).normalized() * 0.0))
        objects.append(grip.finish('wheelbarrow grip %s' % ('left' if side < 0 else 'right'), collection, wood, smooth=True, sharp=50))
        # leg: from under the stringer to the ground, a little splayed, an iron shoe at its foot
        top = front.lerp(back, 0.64) + Vector((0.0, 0.0, -0.03))
        foot = Vector((side * 0.30, top.y + 0.05, 0.0))
        timber('leg %s' % ('left' if side < 0 else 'right'), top, foot, 0.04, 0.045)
        shoe = shapes.Shape()
        shoe.box((foot.x, foot.y, 0.012), (0.05, 0.055, 0.024))
        objects.append(shoe.finish('wheelbarrow leg shoe %s' % ('left' if side < 0 else 'right'), collection, RUST, chamfer=0.003))
        # the wheel's fork: an iron strap from the stringer's front down round the axle
        fork = shapes.Shape()
        fork.box((side * 0.075, WHEEL_Y, WHEEL_R + 0.045), (0.012, 0.05, 0.095))
        fork.box((side * 0.082, WHEEL_Y, WHEEL_R), (0.012, 0.07, 0.03))
        objects.append(fork.finish('wheelbarrow fork %s' % ('left' if side < 0 else 'right'), collection, IRON, chamfer=0.002))
    # cross brace between the legs, and a stay from each leg to the stringer
    brace_y = 0.38 + 0.05
    timber('leg brace', (-0.29, brace_y + 0.02, 0.17), (0.29, brace_y + 0.02, 0.17), 0.03, 0.045)
    # cross bearers under the floor, between the stringers
    for y in (-0.30, 0.0, 0.30):
        t = (y - (WHEEL_Y - 0.06)) / ((GRIP_Y - 0.14) - (WHEEL_Y - 0.06))
        z = (WHEEL_R + 0.09) + (0.56 - (WHEEL_R + 0.09)) * t
        x = 0.075 + (0.30 - 0.075) * t
        timber('bearer %.1f' % y, (-x - 0.02, y, z + 0.055), (x + 0.02, y, z + 0.055), 0.045, 0.045)

    # ------------------------------------------------------------------ the body of boards
    floor_w = 0.40            # floor width at the middle
    y0, y1 = -0.38, 0.34      # the floor's reach, front to back
    flare = math.radians(18)
    side_h = 0.23
    # floor: four boards along Y, laid on the bearers; the floor slopes with the stringers
    board_count = 4
    bw = floor_w / board_count
    slope = (0.56 - (WHEEL_R + 0.09)) / ((GRIP_Y - 0.14) - (WHEEL_Y - 0.06))

    def z_at(y):
        """The top of the bearers (so the floor's underside) at y: the stringers' height there plus the bearer."""
        t = (y - (WHEEL_Y - 0.06)) / ((GRIP_Y - 0.14) - (WHEEL_Y - 0.06))
        return (WHEEL_R + 0.09) + (0.56 - (WHEEL_R + 0.09)) * t + 0.0775

    for k in range(board_count):
        x = -floor_w / 2 + bw * (k + 0.5)
        board('floor board %d' % (k + 1), (x, y0, z_at(y0) + 0.011), (x, y1, z_at(y1) + 0.011), bw - 0.004, 0.022, k)
    # sideboards: two boards high each side, leaning out
    for side in (-1, 1):
        up = Vector((side * math.sin(flare), 0.0, math.cos(flare)))
        base_x = side * (floor_w / 2 + 0.004)
        for k in range(2):
            h = side_h / 2
            off = up * (h * (k + 0.5) + 0.02)
            a = Vector((base_x, y0 - 0.02, z_at(y0 - 0.02))) + off
            b = Vector((base_x, y1 + 0.02, z_at(y1 + 0.02))) + off
            board('sideboard %s %d' % ('left' if side < 0 else 'right', k + 1), a, b, 0.02, h - 0.004, 6 + k + (2 if side > 0 else 0), up=up)
        # iron straps over the sideboards with bolt heads
        for y in (y0 + 0.12, y1 - 0.10):
            strap = shapes.Shape()
            lo = Vector((base_x, y, z_at(y))) + up * 0.0
            hi = Vector((base_x, y, z_at(y))) + up * (side_h + 0.03)
            strap.beam(lo + up * 0.0 + Vector((side * 0.021, 0, 0)), hi + Vector((side * 0.021, 0, 0)), 0.035, 0.004, up=Vector((side, 0, 0)))
            for t in (0.25, 0.75):
                p = lo.lerp(hi, t) + Vector((side * 0.025, 0, 0))
                strap.sphere(p, 0.008, segments=10, rings=5, squash=(0.6, 1.0, 1.0))
            objects.append(strap.finish('wheelbarrow strap %s %.1f' % ('left' if side < 0 else 'right', y), collection, RUST, smooth=True, sharp=45))
    # the front board (over the wheel), leaning well out, and the back board, leaning a little
    for (label, y, lean, k) in (('front', y0 - 0.03, -math.radians(32), 10), ('back', y1 + 0.03, math.radians(12), 11)):
        up = Vector((0.0, math.sin(lean), math.cos(lean)))
        half = floor_w / 2 + 0.03
        for j in range(2):
            h = side_h * 0.55
            off = up * (h * (j + 0.5) + 0.01)
            widen = 0.07 * (j + 0.5) / 1.0 * 1.0      # follows the sideboards' flare
            a = Vector((-half - widen, y, z_at(y))) + off
            b = Vector((half + widen, y, z_at(y))) + off
            board('%s board %d' % (label, j + 1), a, b, 0.02, h - 0.004, k + j, up=up)
    # ------------------------------------------------------------------ the wheel
    objects += shapes.spoked_wheel(collection, 'wheelbarrow wheel', axle, (1.0, 0.0, 0.0), WHEEL_R, 8, wood, IRON, rng,
                                   hub_radius=0.045, hub_length=0.12, spoke_width=0.028, felloe_depth=0.04, felloe_width=0.035, tyre=0.007)

    # ------------------------------------------------------------------ the load
    if loaded != 'none':
        heap = shapes.Shape()
        cx, cy = 0.0, (y0 + y1) / 2
        rx, ry = floor_w / 2 + 0.06, (y1 - y0) / 2 + 0.02
        top = z_at(cy) + 0.03
        if loaded == 'ash':
            # a soft mound of ash: a squashed dome, roughened, sagging at the sides where the shovel has been
            from mathutils import noise as _noise
            height = 0.14
            heap.sphere((cx, cy, top), 1.0, segments=32, rings=16, squash=(rx * 0.97, ry * 0.97, height))
            for v in heap.bm.verts:
                if v.co.z < top:
                    v.co.z = top - 0.02
                    continue
                lift = (v.co.z - top) / height
                n = _noise.noise(v.co * 7.0 + Vector((seed * 3.1, 0, 0)))
                n2 = _noise.noise(v.co * 20.0 + Vector((0, seed * 2.3, 0)))
                v.co.z += (0.035 * n + 0.008 * n2) * lift ** 0.5
            objects.append(heap.finish('wheelbarrow ash', collection, ash_material(), smooth=True, sharp=None))
            # clinker lumps lying on the ash
            clinker = shapes.Shape()
            for _ in range(18):
                a = rng.uniform(0, 2 * math.pi)
                d = math.sqrt(rng.uniform(0, 1)) * 0.75
                x, y = cx + math.cos(a) * d * rx * 0.97, cy + math.sin(a) * d * ry * 0.97
                r = rng.uniform(0.018, 0.032)
                z = top + height * math.sqrt(max(0.0, 1.0 - d * d)) + r * 0.3
                clinker.rock((x, y, z), r, rng, squash=(1.0, 1.0, 0.75), jitter=0.3)
            objects.append(clinker.finish('wheelbarrow clinker', collection, clinker_material(), smooth=False))
        else:
            shapes.lumps(heap, (cx, cy, top + 0.02), 110, 0.085, (rx * 0.9, ry * 0.92), rng, height=0.14)
            shapes.lumps(heap, (cx, cy, top + 0.12), 45, 0.075, (rx * 0.55, ry * 0.6), rng, height=0.1)
            objects.append(heap.finish('wheelbarrow coal', collection, shapes.coal_material(PART), smooth=False))
            bed = shapes.Shape()
            bed.sphere((cx, cy, top), 1.0, segments=20, rings=8, squash=(rx * 0.95, ry * 0.95, 0.16))
            objects.append(bed.finish('wheelbarrow coal bed', collection, shapes.coal_material(PART), smooth=True, sharp=None))
    return objects
