"""
clogs: a pair of Japanese wooden clogs (geta) left side by side the way a guest steps out of them: each a pale
paulownia board with rounded corners standing on two teeth (the front one under the ball of the foot, the back one under
the heel), cloth thongs (hanao) running from a hole between the toes to a hole either side, knotted under the board.
Worn as they are worn: the top darkened and pressed a little hollow where the heel, the ball of the foot and the toes
press, the teeth worn down on the slant at the back edge where the heel strikes, the board's edges rubbed.

Options:
    thongs   'red' (default): red cloth thongs; 'black': black velvet; 'indigo': indigo cotton
    pose     'pair' (default): side by side, toes to the front (-Y), as they were stepped out of; 'scattered': the
             right one turned askew and the left tipped on its side, its two teeth to the eye
    seed     how neatly they stand, the wear, the wood's grain

Where it came from: clog() in '/home/claude/build-57-garden/second pass/render_final.py' (lines 989-1016: a rounded
slab on two box teeth with a red thong in a V, 'paulownia clogs, foot-darkened'), rebuilt as a geta is made: a
photographed wood with its grain along the board, holes for the thongs, a knot at the toe, worn teeth and the marks of
the feet.
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
import _shapes_garden as garden  # noqa: E402

PART = 'clogs'
THONGS = {'red': (0.32, 0.018, 0.014), 'black': (0.012, 0.011, 0.012), 'indigo': (0.02, 0.03, 0.09)}
POSES = ('pair', 'scattered')
LENGTH, WIDTH, BOARD, TEETH = 0.232, 0.096, 0.024, 0.042
TOP = BOARD + TEETH

CARD = {
    'name': PART,
    'what': 'a pair of wooden clogs (geta): pale paulownia boards on two teeth, cloth thongs from the toe hole to either side, '
            'the tops darkened and hollowed where the feet press, the teeth worn down at the heel',
    'size_m': (0.22, 0.24, 0.10),
    'options': {
        'thongs': "'red' (default): red cloth; 'black': black velvet; 'indigo': indigo cotton",
        'pose': "'pair' (default): side by side, toes to the front (-Y); 'scattered': one turned askew, the other tipped on its side",
        'seed': 'how neatly they stand, the wear, the grain (default 0)',
    },
    'materials': ['SURFACE • rough_wood (clogs, foot-pressed)', 'SURFACE • rough_linen (clogs, tinted 0.32 0.02 0.01)'],
    'source': "clog() in '/home/claude/build-57-garden/second pass/render_final.py' (lines 989-1016)",
    'views': 'reads from every side and from above; the thongs show best from the front and above',
    'trap': 'small and low (10 cm): from eye height across a garden they read only on a step stone or a pale path, with a lamp on '
            'them; on dark wet slabs they vanish',
}


def pressed_wood():
    """The photographed weathered wood, paler (paulownia), darkened where the point number 'pressed' says (the marks
    of the feet)."""
    name = 'SURFACE • rough_wood (clogs, foot-pressed)'
    existing = bpy.data.materials.get(name)
    if existing is not None:
        return existing
    m = shapes.surface_copy('SURFACE • rough_wood', 'clogs', Darken=1.25, Grime=0.25, **{'Edge wear': 0.6})
    m.name = name
    nodes, links = m.node_tree.nodes, m.node_tree.links
    p = garden._principled(m)
    attr = nodes.new('ShaderNodeAttribute')
    attr.attribute_name = 'pressed'
    base = p.inputs['Base Color']
    source = base.links[0].from_socket if base.is_linked else tuple(base.default_value)[:3]
    amount = shapes.map_range(nodes, links, attr.outputs['Fac'], 0.04, 0.6, 0.0, 1.0)
    links.new(shapes.mix_colour(nodes, links, amount, source, (0.018, 0.011, 0.006)), base)
    rough = p.inputs['Roughness']                       # polished a little by the feet
    rsource = rough.links[0].from_socket if rough.is_linked else rough.default_value
    links.new(shapes.mix_float(nodes, links, amount, rsource, 0.38), rough)
    return m


def _outline(scale, n=40):
    """The board's outline: a rectangle with well rounded corners (a superellipse), `scale` of its full size."""
    pts = []
    for k in range(n):
        a = 2 * math.pi * k / n
        c, s = math.cos(a), math.sin(a)
        pts.append((WIDTH / 2 * scale * math.copysign(abs(c) ** 0.4, c), LENGTH / 2 * scale * math.copysign(abs(s) ** 0.4, s)))
    return pts


def _press(x, y):
    """How hard the foot presses at (x, y) on the board: heel, ball, toes."""
    def blob(cx, cy, rx, ry, k):
        d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
        return k * max(0.0, 1.0 - d) ** 1.5
    return min(1.0, max(blob(0.0, 0.068, 0.034, 0.042, 1.0), blob(0.004, -0.028, 0.04, 0.038, 0.9), blob(-0.004, -0.083, 0.036, 0.022, 0.65)))


def one_clog(rng, wood_rng):
    """One geta in its own metres: the board's middle over the origin, toes to -Y, the teeth on z = 0."""
    shape = garden.Shape()
    # the board: concentric rings on top (so the foot marks have points to sit on), a rubbed edge, a flat underside
    shape.begin()
    rings = []
    rings.append([Vector((0.0, 0.0, TOP))])
    for k, s in enumerate((0.18, 0.34, 0.5, 0.64, 0.77, 0.88, 0.96)):
        rings.append([Vector((x, y, TOP)) for (x, y) in _outline(s)])
    rings.append([Vector((x, y, TOP - 0.003)) for (x, y) in _outline(1.0)])
    rings.append([Vector((x, y, TEETH + 0.003)) for (x, y) in _outline(1.0)])
    rings.append([Vector((x, y, TEETH)) for (x, y) in _outline(0.97)])
    rings.append([Vector((0.0, 0.0, TEETH))])
    shape._rings([shape._verts(r) for r in rings], True, False, False)
    shape.end(wood_rng.random())
    layer = shape.bm.verts.layers.float.new('pressed')
    for v in shape.bm.verts:
        if v.co.z > TOP - 0.0005:
            p = _press(v.co.x, v.co.y)
            v[layer] = p
            v.co.z -= 0.0018 * p
    # the teeth: the full width of the board, narrowing a little downwards, worn on the slant at the back edge
    for cy, wear in ((-0.06, 0.003), (0.066, 0.006 + rng.uniform(0.0, 0.003))):
        shape.begin()
        t0, t1 = 0.019, 0.015
        w = WIDTH / 2 - 0.004
        low = [Vector((-w, cy - t1 / 2, wear * 0.15)), Vector((w, cy - t1 / 2, wear * 0.15)), Vector((w, cy + t1 / 2, wear)), Vector((-w, cy + t1 / 2, wear))]
        if cy < 0:
            low = [Vector((-w, cy - t1 / 2, wear)), Vector((w, cy - t1 / 2, wear)), Vector((w, cy + t1 / 2, 0.0)), Vector((-w, cy + t1 / 2, 0.0))]
        high = [Vector((-w, cy - t0 / 2, TEETH + 0.002)), Vector((w, cy - t0 / 2, TEETH + 0.002)), Vector((w, cy + t0 / 2, TEETH + 0.002)), Vector((-w, cy + t0 / 2, TEETH + 0.002))]
        shape._rings([shape._verts(low), shape._verts(high)], True, True, True)
        lowest = min(p.z for p in low)
        for v in shape.new_verts():
            v.co.z -= lowest
        shape.end(wood_rng.random())
    # the holes the thongs go through: dark pits on the top
    return shape


def thong(shape):
    """The thong: a padded cloth cord from the toe hole, knotted there, to a hole either side behind the middle."""
    front = Vector((0.0, -0.075, TOP))
    knot = front + Vector((0.0, 0.004, 0.009))
    shape.sphere(knot, 0.0075, segments=10, rings=6)
    shape.cylinder(front - Vector((0, 0, 0.004)), knot, 0.005, segments=8)
    for side in (-1, 1):
        pts = [knot, Vector((side * 0.013, -0.058, TOP + 0.02)), Vector((side * 0.031, -0.028, TOP + 0.023)),
               Vector((side * 0.041, 0.0, TOP + 0.016)), Vector((side * 0.043, 0.02, TOP + 0.005)), Vector((side * 0.043, 0.026, TOP - 0.004))]
        pts = shapes.smooth_path(pts, steps=5)
        radii = [0.0045 + 0.0012 * math.sin(math.pi * k / (len(pts) - 1)) for k in range(len(pts))]
        shape.sweep(pts, 0.006, sides=8, radii=radii)


def build(collection, seed=0, thongs='red', pose='pair'):
    if thongs not in THONGS:
        raise ValueError("thongs is one of %s, not %r" % (', '.join(repr(k) for k in THONGS), thongs))
    if pose not in POSES:
        raise ValueError("pose is one of %s, not %r" % (', '.join(repr(k) for k in POSES), pose))
    rng = shapes.rng_for(PART, seed)
    wood = pressed_wood()
    cloth = garden.tinted('SURFACE • rough_linen', 'clogs', THONGS[thongs])
    hole_mat = garden.cord((0.02, 0.014, 0.01), 'dark cord')
    made = []
    for k, side in enumerate((-1, 1)):
        name = 'left' if side < 0 else 'right'
        turn = math.radians(rng.uniform(-4.0, 4.0) + side * 2.0)
        place = Matrix.Translation((side * 0.062, rng.uniform(-0.012, 0.012), 0.0)) @ Matrix.Rotation(turn, 4, 'Z')
        if pose == 'scattered':
            if side > 0:
                place = Matrix.Translation((0.05, -0.02, 0.0)) @ Matrix.Rotation(math.radians(-38 + rng.uniform(-6, 6)), 4, 'Z')
            else:
                # tipped onto its outer long edge, the sole and its teeth turned to the front left
                place = Matrix.Translation((-0.07, 0.03, WIDTH / 2)) @ Matrix.Rotation(math.radians(-60), 4, 'Z') @ Matrix.Rotation(math.radians(-90), 4, 'Y')
        board = one_clog(rng, shapes.rng_for(PART, seed, name))
        board.transform(place)
        cord = garden.Shape()
        thong(cord)
        cord.transform(place)
        holes = garden.Shape()
        for (hx, hy) in ((0.0, -0.075), (-0.043, 0.026), (0.043, 0.026)):
            holes.cylinder((hx, hy, TOP - 0.006), (hx, hy, TOP + 0.0004), 0.0062, segments=10)
        holes.transform(place)
        shift = 0.0
        if pose == 'scattered' and side < 0:
            low = min(v.co.z for v in board.bm.verts)
            shift = -low
            for s in (board, cord, holes):
                s.transform(Matrix.Translation((0.0, 0.0, shift)))
        grain = place @ Matrix.Translation((0.0, 0.0, 0.0))
        along = (grain.to_3x3() @ Vector((0.0, 1.0, 0.0)))
        local = garden.matrix_z_along(along, grain.translation)
        made.append(board.finish('%s %s' % (PART, name), collection, wood, smooth=True, sharp=50.0, chamfer=0.002,
                                 local=local, shift=0.4, rng=shapes.rng_for(PART, seed, name + ' grain')))
        made.append(cord.finish('%s %s thong' % (PART, name), collection, cloth, smooth=True))
        made.append(holes.finish('%s %s holes' % (PART, name), collection, hole_mat, smooth=True))
    return made
