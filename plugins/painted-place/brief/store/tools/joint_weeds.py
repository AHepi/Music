"""
What this file does: grows sparse tufts of grass and small weeds (flat rosettes of broad leaves, a dandelion or a
plantain) out of the joints between setts or flags that lay_cobbles laid, within an area you give: each tuft rooted in
a joint, its blades fanned along the joint's line, more often where joints cross; none in the wheel lines you give.
Nothing here chooses where weeds go: the stones, the area and the wheel lines are yours.

From your own script:

    import sys; sys.path.insert(0, FOLDER + '/store/tools')
    import lay_cobbles, joint_weeds
    setts = lay_cobbles.lay_setts(road, seed=3, grit=True)
    made = joint_weeds.grow(setts, area=(2.6, -9, 3.45, 30), wheel_lines=[[(1.2, -9), (1.2, 30)], [(-0.3, -9), (-0.3, 30)]], seed=4)
    made['grass'], made['weeds']                     # obj['tufts'] counts each

    python3 joint_weeds.py --help
    python3 joint_weeds.py --blend IN.blend --stones setts --area 2.6 -9 3.45 30 --out OUT.blend

Options, with their defaults:
    stones          what lay_cobbles.lay_setts or lay_flags returned (the 'setts' or 'flags' object), or a list of them
    area            where weeds may grow: None (every joint of the stones), a rectangle (x0, y0, x1, y1), a polygon
                    [(x, y), ...], or a function of an (n, 2) array of points giving weights 0 to 1 (None)
    amount          1.0      about 1.2 tufts per square metre of the area; 0.5 thinner, up to 5
    kinds           ('grass', 'weeds')   grass: narrow blades 7 to 24 cm; weeds: flat rosettes of broad leaves 10 to 22 cm across
    wheel_lines     none     lines [(x, y), ...] (or curve objects) along which wheels run: no tuft within wheel_width/2 of one
    wheel_width     0.4 m    how wide a band each wheel line keeps clear
    seed            0        the same seed grows the same weeds
    material        'Weed • rain olive'     the grass blades
    leaf_material   'Weed • dark ivy'       the weeds' leaves
    collection      none     where the objects go (a new collection 'joint_weeds')

What it makes: 'joint grass' and 'joint weeds': a point per tuft (its root, in a joint, just under the stones' tops)
carrying its size, turn and shape ('stone_scale', 'stone_rotation', 'stone_shape'), with live copies of a dozen tuft
shapes on them (Geometry Nodes); obj['tufts'] is the count.
"""

import argparse
import math
import os
import random
import sys

import bpy
import bmesh
import numpy
from mathutils import Euler, Vector

TOOLS = os.path.dirname(os.path.abspath(__file__))
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)
import store  # noqa: E402
import _lines  # noqa: E402
import lay_cobbles  # noqa: E402
import stones as stones_tool  # noqa: E402

BLADES = 'Weed • rain olive'
LEAVES = 'Weed • dark ivy'
KINDS = ('grass', 'weeds')
DENSITY = 1.2               # tufts per square metre of the area at amount 1
SHAPES = 12

TOOL = {
    'name': 'joint_weeds',
    'what': 'sparse tufts of grass and small flat weeds growing out of the joints of the setts or flags lay_cobbles laid, '
            'within an area you give, keeping out of the wheel lines you give',
    'call': "joint_weeds.grow(setts, area=(2.6, -9, 3.45, 30), wheel_lines=[[(1.2, -9), (1.2, 30)]], amount=1.0, seed=4)",
    'options': {
        'stones': "what lay_cobbles.lay_setts or lay_flags returned, or a list of them (required)",
        'area': 'None (every joint), a rectangle (x0, y0, x1, y1), a polygon [(x, y), ...], or a function of an (n, 2) array of points giving weights 0..1 (None)',
        'amount': 'about 1.2 tufts per square metre at 1; 0 to 5 (1.0)',
        'kinds': "'grass' (narrow blades 7 to 24 cm), 'weeds' (flat rosettes of broad leaves 10 to 22 cm across) (both)",
        'wheel_lines, wheel_width': 'lines [(x, y), ...] or curve objects along which wheels run, and the band each keeps clear (none, 0.4 m)',
        'seed': 'the same seed grows the same weeds (0)',
        'material, leaf_material': "the blades ('%s'), the weeds' leaves ('%s')" % (BLADES, LEAVES),
        'collection': "where the objects go (a new collection 'joint_weeds')",
    },
    'materials': [BLADES, LEAVES],
    'source': "`tuft` in the town street builder's '55 street - render_final.py' (line 635; tufts of thin cones stood at "
              "points the builder typed), made into a tool: the tufts now find the joints from the stones themselves, "
              "fan along them, cross-joints first, and keep out of wheel lines",
    'trap': 'give stones laid by lay_cobbles (their points carry the size and turn each tuft reads to find the joints); '
            'weeds grow where wheels and feet do not go: by the kerb, round a lamp post or a step, rarely in the middle '
            'of a road, so give a narrow area',
}


# ------------------------------------------------------------------------------------------------ the tuft shapes

def _blade(bm, root, heading, lean, length, width, droop, rows=4):
    out = Vector((math.cos(heading), math.sin(heading), 0.0))
    side = Vector((-out.y, out.x, 0.0))
    ring = []
    for row in range(rows + 1):
        t = row / rows
        centre = root + (out * (math.sin(lean) * t + droop * t * t) + Vector((0.0, 0.0, math.cos(lean) * t - droop * t * t * 0.5))) * length
        half = 0.5 * width * (1.0 - t) ** 0.8 + 0.0004
        ring.append((bm.verts.new(centre - side * half), bm.verts.new(centre + side * half)))
    for (a, b), (c, d) in zip(ring[:-1], ring[1:]):
        bm.faces.new((a, b, d, c))


def _grass_mesh(name, index):
    """A tuft 1 m tall: narrow blades rising from a short line of roots along X (the joint's line), fanning out."""
    pick = random.Random(6100 + 37 * index)
    bm = bmesh.new()
    for _ in range(pick.randint(14, 24)):
        root = Vector((pick.uniform(-0.3, 0.3), pick.uniform(-0.025, 0.025), 0.0))
        heading = pick.choice((0.5, -0.5)) * math.pi + pick.gauss(0.0, 0.8)
        _blade(bm, root, heading, math.radians(pick.uniform(8.0, 50.0)), pick.uniform(0.45, 1.0), pick.uniform(0.045, 0.08),
               pick.uniform(0.05, 0.35))
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    return mesh


def _rosette_mesh(name, index):
    """A flat weed 1 m across: broad leaves in a rosette lying out from the root, their tips lifting a little."""
    pick = random.Random(6900 + 41 * index)
    bm = bmesh.new()
    count = pick.randint(5, 9)
    for k in range(count):
        heading = math.tau * k / count + pick.uniform(-0.3, 0.3)
        out = Vector((math.cos(heading), math.sin(heading), 0.0))
        side = Vector((-out.y, out.x, 0.0))
        length = pick.uniform(0.32, 0.5)
        width = length * pick.uniform(0.28, 0.45)
        lift = pick.uniform(0.05, 0.3)
        rows = []
        for row in range(5):
            t = row / 4
            centre = out * (length * t) + Vector((0.0, 0.0, 0.02 + lift * length * t * t))
            half = width * 0.5 * math.sin(math.pi * min(t * 1.15, 1.0)) ** 0.8 + 0.004
            rows.append((bm.verts.new(centre - side * half), bm.verts.new(centre), bm.verts.new(centre + side * half)))
        for (a, b, c), (d, e, f) in zip(rows[:-1], rows[1:]):
            bm.faces.new((a, b, e, d))
            bm.faces.new((b, c, f, e))
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    return mesh


def _shapes(kind, material, collection):
    shapes = lay_cobbles._shapes_collection('joint %s • %s' % (kind, material.name), collection)
    for index in range(len(shapes.objects), SHAPES):
        name = 'joint %s %02d' % (kind, index)
        mesh = (_grass_mesh if kind == 'grass' else _rosette_mesh)(name, index)
        mesh.materials.append(material)
        shapes.objects.link(bpy.data.objects.new(name, mesh))
    return shapes


# ------------------------------------------------------------------------------------------------ the joints

def joints_of(stones):
    """Every laid stone's middle (n, 3), half sizes (n, 2) and turn about Z (n,), from what lay_cobbles returned."""
    if isinstance(stones, bpy.types.Object):
        stones = [stones]
    middles, halves, turns = [], [], []
    for obj in stones:
        if not isinstance(obj, bpy.types.Object) or obj.type != 'MESH':
            raise ValueError('stones are what lay_cobbles.lay_setts or lay_flags returned (a mesh object of points), not %r' % (obj,))
        mesh = obj.data
        scale, rotation = mesh.attributes.get('stone_scale'), mesh.attributes.get('stone_rotation')
        if scale is None or rotation is None:
            raise ValueError('%s carries no stone_scale or stone_rotation: give the setts or flags lay_cobbles laid' % obj.name)
        count = len(mesh.vertices)
        co = numpy.zeros(count * 3)
        mesh.vertices.foreach_get('co', co)
        co = co.reshape(-1, 3)
        matrix = numpy.array(obj.matrix_world)
        middles.append(co @ matrix[:3, :3].T + matrix[:3, 3])
        sizes = numpy.zeros(count * 3)
        scale.data.foreach_get('vector', sizes)
        halves.append(sizes.reshape(-1, 3)[:, :2] / 2.0 + 0.004)        # the stone's own half size and half a joint
        euler = numpy.zeros(count * 3)
        rotation.data.foreach_get('vector', euler)
        euler = euler.reshape(-1, 3)
        world_turn = math.atan2(matrix[1, 0], matrix[0, 0])
        turns.append(numpy.array([Euler(e).to_matrix().to_euler('ZXY').z for e in euler]) + world_turn)
    return numpy.concatenate(middles), numpy.concatenate(halves), numpy.concatenate(turns)


def covered(places, middles, halves, turns, inset=0.0):
    """For each place (n, 2): does a stone stand there (more than `inset` inside its footprint, joint left out)?"""
    from scipy.spatial import cKDTree
    result = numpy.zeros(len(places), dtype=bool)
    if not len(places) or not len(middles):
        return result
    for index, near in enumerate(cKDTree(middles[:, :2]).query_ball_point(places, r=0.6)):
        if not near:
            continue
        near = numpy.array(near)
        dx, dy = places[index, 0] - middles[near, 0], places[index, 1] - middles[near, 1]
        c, s = numpy.cos(turns[near]), numpy.sin(turns[near])
        lx, ly = c * dx + s * dy, -s * dx + c * dy
        result[index] = bool(((numpy.abs(lx) < halves[near, 0] - 0.004 - inset) & (numpy.abs(ly) < halves[near, 1] - 0.004 - inset)).any())
    return result


def grow(stones, area=None, amount=1.0, kinds=KINDS, wheel_lines=(), wheel_width=0.4, seed=0, material=BLADES,
         leaf_material=LEAVES, collection=None):
    """Grow tufts in the stones' joints within the area (see the note at the top). Returns {'grass': obj, 'weeds': obj},
    the kinds asked for."""
    kinds = (kinds,) if isinstance(kinds, str) else tuple(kinds)
    unknown = [k for k in kinds if k not in KINDS]
    if unknown or not kinds:
        raise ValueError('kinds are %s, not %r' % (', '.join(KINDS), kinds))
    amount, wheel_width = float(amount), float(wheel_width)
    if not 0.0 <= amount <= 5.0:
        raise ValueError('amount is 0 to 5 (1 about 1.2 tufts a square metre), not %r' % (amount,))
    if not 0.0 <= wheel_width <= 3.0:
        raise ValueError('wheel_width is 0 to 3 m, not %r' % (wheel_width,))
    middles, halves, turns = joints_of(stones)
    weigh, _box = stones_tool._area(area)
    rng = random.Random(seed)
    # the places a tuft may root: the joint beyond each stone's far side and far end, and its far corner (where joints cross)
    candidates = []
    for i in range(len(middles)):
        c, s = math.cos(turns[i]), math.sin(turns[i])
        hx, hy = halves[i]
        for kind_of_place in ('side', 'end', 'corner'):
            if kind_of_place == 'side':
                local, heading = (hx, rng.uniform(-hy, hy) * 0.85), turns[i] + math.pi / 2
            elif kind_of_place == 'end':
                local, heading = (rng.uniform(-hx, hx) * 0.85, hy), turns[i]
            else:
                local, heading = (hx, hy), turns[i] + rng.choice((0.0, math.pi / 2))
            x = middles[i, 0] + c * local[0] - s * local[1]
            y = middles[i, 1] + s * local[0] + c * local[1]
            candidates.append((x, y, middles[i, 2], heading, 2.5 if kind_of_place == 'corner' else 1.0))
    places = numpy.array([(p[0], p[1]) for p in candidates]) if candidates else numpy.zeros((0, 2))
    keep = weigh(places) > 0.5 if len(places) else numpy.zeros(0, dtype=bool)
    keep &= ~covered(places, middles, halves, turns, inset=0.006)    # a neighbour laid off true may close a joint
    for line in (wheel_lines or ()):
        points = [Vector((p[0], p[1], 0.0)) for p in _lines.line_points(line)]
        path = _lines.Path(points)
        fine = _lines.Path([path.at(d) for d in numpy.linspace(0.0, path.total, int(path.total / 0.02) + 2)])
        _along, across, _ahead = fine.project(places) if len(places) else (None, numpy.zeros(0), None)
        keep &= numpy.abs(across) > wheel_width / 2
    # how much ground the area holds: the stones whose middles lie in it, each its own footprint
    in_area = weigh(middles[:, :2]) > 0.5 if len(middles) else numpy.zeros(0, dtype=bool)
    ground = float((4.0 * halves[in_area, 0] * halves[in_area, 1]).sum())
    wanted = ground * DENSITY * amount
    chosen = [i for i in range(len(candidates)) if keep[i]]
    target = collection
    if target is None:
        target = bpy.data.collections.new('joint_weeds')
        bpy.context.scene.collection.children.link(target)
    made = {}
    pick = numpy.random.default_rng([seed, 55])
    share = {'grass': 0.7, 'weeds': 0.3} if len(kinds) == 2 else {kinds[0]: 1.0}
    taken = set()
    for kind in KINDS:
        if kind not in kinds:
            continue
        count = min(int(round(wanted * share[kind])), max(0, len(chosen) - len(taken)))
        free = [i for i in chosen if i not in taken]
        free_weights = numpy.array([candidates[i][4] for i in free], dtype=float)
        order = pick.choice(len(free), size=count, replace=False, p=free_weights / free_weights.sum()) if count else []
        points, scales, rotations, shapes_index = [], [], [], []
        for k in order:
            index = free[int(k)]
            taken.add(index)
            x, y, z, heading, _w = candidates[index]
            size = (rng.uniform(0.07, 0.24) if kind == 'grass' else rng.uniform(0.1, 0.22))
            points.append((x, y, z - (0.012 if kind == 'grass' else 0.016)))
            scales.append((size, size, size))
            rotations.append((rng.uniform(-0.12, 0.12), rng.uniform(-0.12, 0.12), heading + (rng.uniform(-0.25, 0.25) if kind == 'grass' else rng.uniform(0, math.tau))))
            shapes_index.append(rng.randrange(SHAPES))
        wanted_material = material if kind == 'grass' else leaf_material
        shapes = _shapes(kind, store.material(wanted_material) if isinstance(wanted_material, str) else wanted_material, target)
        obj = lay_cobbles._laid_stones('joint ' + kind, points, scales, rotations, shapes_index, shapes, target)
        obj['tufts'] = len(points)
        store.mark(obj)
        made[kind] = obj
    return made


# ------------------------------------------------------------------------------------------------ command line

def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    parser = argparse.ArgumentParser(description=TOOL['what'] + ' (see the note at the top of joint_weeds.py). Trap: ' + TOOL['trap'] + '.')
    parser.add_argument('--blend', help='the .blend file holding the laid setts or flags')
    parser.add_argument('--stones', default='setts', help="the laid stones' object name; default 'setts'")
    parser.add_argument('--area', type=float, nargs=4, metavar=('X0', 'Y0', 'X1', 'Y1'), help='a rectangle to grow in (default: every joint)')
    parser.add_argument('--amount', type=float, default=1.0, help='about 1.2 tufts a square metre at 1; default 1')
    parser.add_argument('--kinds', nargs='+', default=list(KINDS), help='grass, weeds; default both')
    parser.add_argument('--seed', type=int, default=0, help='the same seed grows the same weeds; default 0')
    parser.add_argument('--out', help='save the result here')
    args = parser.parse_args(argv)
    if not args.blend:
        parser.error('give --blend (a file with the setts or flags lay_cobbles laid)')
    bpy.ops.wm.open_mainfile(filepath=args.blend)
    laid = bpy.data.objects.get(args.stones)
    if laid is None:
        parser.error('no object %r in the file' % args.stones)
    made = grow(laid, area=tuple(args.area) if args.area else None, amount=args.amount, kinds=args.kinds, seed=args.seed)
    print('grew', ', '.join('%s: %d tufts' % (name, obj['tufts']) for name, obj in made.items()))
    if args.out:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.out))
        print('saved', args.out)
    else:
        print('note: nothing was saved; give --out FILE.blend')


if __name__ == '__main__':
    main()
