"""
What this file does: builds a timber veranda (engawa) along one side of a building you name, the way Japanese inns and
houses have them: a raised floor of long boards running along the side, laid with their joints staggered on joists and
a heavy edge beam, carried on short posts that stand on flat stones; posts at the outer edge (one every 1.82 m, a ken,
by default) carrying a beam under the eave; a flat step stone (or a timber step) at the edge where you ask. The boards
are worn pale where feet go (along the middle, and in front of the step) and darker at the outer edge where rain
reaches. Each board, stone and member shows its own part of the photographed surface (the number `pp_piece`). Nothing
is placed anywhere you did not say.

From your own Blender script:

    import sys
    sys.path.insert(0, FOLDER + '/store/tools')       # FOLDER is your copy of the brief folder
    import lay_tile_roof, lay_veranda
    lay_tile_roof.lay(inn, overhang=1.1)                     # the roof first: the veranda reads the eave's height from it
    made = lay_veranda.lay(inn, side='front', depth=0.9, height=0.45, step='stone', step_at=3.0, seed=2)
    made['floor'], made['frame'], made['stones'], made['floor_height']

Sides are named by the way they face in the box's own axes: 'front' (-Y), 'back' (+Y), 'left' (-X), 'right' (+X);
distances along a side are from its left end as you stand outside facing it.

From the command line:

    python3 lay_veranda.py --help
    python3 lay_veranda.py --blend IN.blend --object Inn --side front --depth 0.9 --step stone --out OUT.blend

Options, with their defaults:
    side          'front'     the side it runs along
    depth         0.9 m       how far the floor reaches out from the wall's face (0.5 to 2.5)
    height        0.45 m      the floor's top above the building's foot (0.2 to 1.2)
    start, end    None        metres along the side where it starts and ends (None: the side's ends); a little past
                              either end (up to `depth`) wraps it past the corner's line
    posts         1.82 m      the spacing of the posts at the outer edge that carry the beam under the eave (0: no
                              posts and no beam)
    beam_height   None        the beam's top above the building's foot; None: just under the roof's rafters where
                              lay_tile_roof roofed the building (read from the box), else the box's top
    step          None        None, 'stone' (a flat step stone at the edge, where shoes are left) or 'wood' (a timber step)
    step_at       None        metres along the side to the step's middle (None: the middle of the veranda)
    seed          0           the boards' lengths and joints, each piece's part of the picture, the stones' shapes
    collection    none        where the objects go (a new collection 'lay_veranda')
    board_material   'SURFACE • old_planks_02'        (the boards: the tool lays a worn pale copy and a rain-dark copy too)
    timber_material  'SURFACE • old_planks_02'        (the posts, beams, joists; a darker copy)
    stone_material   'SURFACE • worn_rock_natural_01' (the stones under the posts and the step stone)

The result: {'floor': object, 'frame': object, 'stones': object, 'floor_height': the floor's top as a world height,
'boards': how many boards}.
"""

import argparse
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import bpy  # noqa: E402
import bmesh  # noqa: E402,F401
from mathutils import Matrix, Vector  # noqa: E402

import store  # noqa: E402

BOARD_MATERIAL = 'SURFACE • old_planks_02'
TIMBER_MATERIAL = 'SURFACE • old_planks_02'
STONE_MATERIAL = 'SURFACE • worn_rock_natural_01'
SIDE_NAMES = {'front': '-y', 'back': '+y', 'right': '+x', 'left': '-x', '-y': '-y', '+y': '+y', '-x': '-x', '+x': '+x'}
STEPS = (None, 'stone', 'wood')
BOARD_W, BOARD_T, GAP = 0.135, 0.032, 0.004
EDGE_W, EDGE_H = 0.12, 0.13          # the edge beam under the outer boards
POST = 0.12                          # the posts at the outer edge
SHORT = 0.09                         # the short posts under the floor
BEAM_W, BEAM_H = 0.13, 0.18          # the beam on the posts
RAFTER_H = 0.095                     # lay_tile_roof's rafters' depth under its boarding

TOOL = {
    'name': 'lay_veranda',
    'what': "a timber veranda (engawa) along one side of a building you name: a raised floor of long boards on joists and an edge beam, short posts on flat stones, posts at the outer edge carrying a beam under the eave, a step stone or timber step where you ask; worn pale where feet go, darker at the edge where rain reaches",
    'call': "lay_veranda.lay(inn, side='front', depth=0.9, height=0.45, step='stone', step_at=3.0, seed=2)",
    'options': {
        'side': "the side it runs along: 'front' (default), 'back', 'left' or 'right'",
        'depth': "metres the floor reaches out from the wall's face (default 0.9)",
        'height': "the floor's top above the building's foot, metres (default 0.45)",
        'start, end': "metres along the side from its left end where it starts and ends (default None: the side's ends); up to depth past either end wraps it past the corner's line",
        'posts': "the spacing of the posts at the outer edge carrying the beam under the eave, metres (default 1.82, one ken; 0 no posts and no beam)",
        'beam_height': "the beam's top above the building's foot (default None: just under the rafters of a roof lay_tile_roof laid on the building, read from the box; else the box's top)",
        'step': "None (default), 'stone' (a flat step stone at the edge, where shoes are left) or 'wood' (a timber step)",
        'step_at': "metres along the side to the step's middle (default None: the middle of the veranda)",
        'seed': "the boards' lengths and joints, each piece's part of the picture, the stones' shapes (default 0)",
        'collection': "where the objects go (default a new collection 'lay_veranda')",
        'board_material': "the boards (default '%s'; the tool lays it with a worn pale copy along the middle and a rain-dark copy at the outer edge, all turned so the grain runs along the boards)" % BOARD_MATERIAL,
        'timber_material': "posts, beams, joists, edge beam (default '%s'; a darker copy)" % TIMBER_MATERIAL,
        'stone_material': "the stones under the posts and the step stone (default '%s')" % STONE_MATERIAL,
    },
    'materials': [BOARD_MATERIAL, TIMBER_MATERIAL, STONE_MATERIAL],
    'source': "the veranda wing in '/home/claude/build-57-garden/first pass/render_final.py' (lines 769-820: deck boards, frame, red posts on pads, rafters) and the inn's ground-floor veranda (lines 1171-1186), made into a tool: boards laid along the side in staggered lengths on joists and an edge beam, short posts on flat stones, the eave posts and their beam set under a lay_tile_roof roof's rafters, a step stone, and the wear the board's photographs 10 and 11 show: pale where feet go, dark where rain reaches",
    'trap': "lay the roof first (lay_tile_roof writes the eave's height on the box, and the beam goes just under its rafters); a depth more than the roof's overhang puts the posts and the outer boards out in the rain past the eave; shoji or doors opening onto the veranda want their foot at the floor's height (height=, from the building's foot)",
}


class Build:
    def __init__(self):
        self.verts, self.faces, self.slots, self.pieces = [], [], [], []

    def block(self, corners8, slot, piece):
        """Eight corners in the order (a0 z0 o0), (a1 z0 o0), (a0 z1 o0), (a1 z1 o0), then the same at o1."""
        start = len(self.verts)
        self.verts.extend(tuple(c) for c in corners8)
        for f in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)):
            self.faces.append(tuple(start + i for i in f))
            self.slots.append(slot)
            self.pieces.append(piece)

    def make(self, name, materials, collection, frame, ground):
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(self.verts, [], self.faces)
        for material in materials:
            mesh.materials.append(material)
        mesh.polygons.foreach_set('material_index', self.slots)
        attribute = mesh.attributes.new('pp_piece', 'FLOAT', 'FACE')
        attribute.data.foreach_set('value', self.pieces)
        tool = bmesh.new()
        tool.from_mesh(mesh)
        bmesh.ops.recalc_face_normals(tool, faces=tool.faces)
        tool.to_mesh(mesh)
        tool.free()
        mesh.update()
        obj = bpy.data.objects.new(name, mesh)
        collection.objects.link(obj)
        obj.matrix_world = frame
        store.mark(obj, ground=ground)
        return obj


def _material(value):
    return store.material(value) if isinstance(value, str) else value


def _copy(material, suffix, dials):
    name = 'lay_veranda • %s %s' % (material.name.split(' • ')[-1], suffix)
    found = bpy.data.materials.get(name)
    if found is not None:
        return found
    copy = material.copy()
    copy.name = name
    weather = copy.node_tree.nodes.get('Weather') if copy.node_tree else None
    if weather is not None:
        for dial, value in dials:
            if dial in weather.inputs:
                weather.inputs[dial].default_value = value
    return copy


def _turned(material, axis):
    try:
        import lay_stone
        return lay_stone.turned_along(material, axis)
    except Exception:
        return material


def side_frame(low, high, side):
    """The side's own axes in the box's frame: its left end (seen from outside, at the foot), along, out, length."""
    name = SIDE_NAMES.get(side)
    if name is None:
        raise ValueError("side is 'front', 'back', 'left' or 'right', not %r" % (side,))
    if name == '-y':
        return Vector((low.x, low.y, low.z)), Vector((1, 0, 0)), Vector((0, -1, 0)), high.x - low.x, 'x', 'front'
    if name == '+y':
        return Vector((high.x, high.y, low.z)), Vector((-1, 0, 0)), Vector((0, 1, 0)), high.x - low.x, 'x', 'back'
    if name == '-x':
        return Vector((low.x, high.y, low.z)), Vector((0, -1, 0)), Vector((-1, 0, 0)), high.y - low.y, 'y', 'left'
    return Vector((high.x, low.y, low.z)), Vector((0, 1, 0)), Vector((1, 0, 0)), high.y - low.y, 'y', 'right'


def lay(building, side='front', depth=0.9, height=0.45, start=None, end=None, posts=1.82, beam_height=None, step=None,
        step_at=None, seed=0, collection=None, board_material=BOARD_MATERIAL, timber_material=TIMBER_MATERIAL,
        stone_material=STONE_MATERIAL):
    """Build the veranda (see the note at the top)."""
    if building is None or building.type != 'MESH':
        raise ValueError('lay_veranda needs a mesh object (the building)')
    if step not in STEPS:
        raise ValueError("step is None, 'stone' or 'wood', not %r" % (step,))
    depth, height = float(depth), float(height)
    if not 0.5 <= depth <= 2.5:
        raise ValueError('depth is 0.5 to 2.5 m, not %r' % (depth,))
    if not 0.2 <= height <= 1.2:
        raise ValueError('height is 0.2 to 1.2 m, not %r' % (height,))
    posts = float(posts or 0.0)
    if posts and not 0.9 <= posts <= 4.0:
        raise ValueError('posts is a spacing of 0.9 to 4 m (or 0 for none), not %r' % (posts,))
    bpy.context.view_layer.update()
    rng = random.Random(seed)
    location, rotation, _ = building.matrix_world.decompose()
    frame = Matrix.Translation(location) @ rotation.to_matrix().to_4x4()
    to_box = frame.inverted()
    corners = [to_box @ (building.matrix_world @ Vector(c)) for c in building.bound_box]
    low = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
    high = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
    ground = location.z + low.z
    origin, along, out, length, axis, side_name = side_frame(low, high, side)
    a_start = 0.0 if start is None else float(start)
    a_end = length if end is None else float(end)
    if not (-depth - 1e-6 <= a_start < a_end <= length + depth + 1e-6) or a_end - a_start < 0.8:
        raise ValueError('start and end lie along the side (%.2f m long, up to depth past either end), at least 0.8 m apart, not %r, %r' % (length, start, end))
    if step_at is not None and not a_start <= float(step_at) <= a_end:
        raise ValueError('step_at %r is not on the veranda (%.2f to %.2f m along the side)' % (step_at, a_start, a_end))

    def at(a, z, o):
        return origin + along * a + Vector((0, 0, z)) + out * o

    def block(build, a0, a1, z0, z1, o0, o1, slot, piece, jitter=0.0):
        pts = []
        for o in (o0, o1):
            for z in (z0, z1):
                for a in (a0, a1):
                    p = at(a, z, o)
                    if jitter:
                        p = p + Vector(((rng.random() - 0.5) * jitter, (rng.random() - 0.5) * jitter, (rng.random() - 0.5) * jitter * 0.5))
                    pts.append(p)
        build.block([pts[0], pts[1], pts[2], pts[3], pts[4], pts[5], pts[6], pts[7]], slot, piece)

    def rough_stone(a_mid, o_mid, half_a, half_o, z_top, z_bottom, piece):
        """A flat field stone: a rounded, uneven outline, its top a little domed and tipped, its edge worn round."""
        n = 14
        tip_a, tip_o = (rng.random() - 0.5) * 0.02, (rng.random() - 0.5) * 0.02
        outline = []
        for k in range(n):
            t = 2 * math.pi * (k + rng.random() * 0.3) / n
            c, s_ = math.cos(t), math.sin(t)
            r = (abs(c) ** 3 + abs(s_) ** 3) ** (-1 / 3) * rng.uniform(0.88, 1.0)
            outline.append((a_mid + half_a * r * c, o_mid + half_o * r * s_))
        def ztop(a, o, inset):
            return z_top + tip_a * (a - a_mid) / max(half_a, 0.05) + tip_o * (o - o_mid) / max(half_o, 0.05) - inset
        rings = []
        for inset, shrink in ((0.0, 0.82), (0.012, 0.93), (0.035, 1.0)):
            ring = []
            for a, o in outline:
                aa, oo = a_mid + (a - a_mid) * shrink, o_mid + (o - o_mid) * shrink
                ring.append(at(aa, ztop(aa, oo, inset) + rng.uniform(-0.004, 0.004), oo))
            rings.append(ring)
        rings.append([at(a, z_bottom, o) for a, o in outline])
        start = len(stones.verts)
        for ring in rings:
            stones.verts.extend(tuple(p) for p in ring)
        mid = at(a_mid, ztop(a_mid, o_mid, -0.006), o_mid)
        centre = len(stones.verts)
        stones.verts.append(tuple(mid))
        for k in range(n):
            j = (k + 1) % n
            stones.faces.append((centre, start + k, start + j))
            stones.slots.append(0)
            stones.pieces.append(piece)
        for r in range(len(rings) - 1):
            for k in range(n):
                j = (k + 1) % n
                a0, b0 = start + r * n + k, start + r * n + j
                stones.faces.append((a0, a0 + n, b0 + n, b0))
                stones.slots.append(0)
                stones.pieces.append(piece)
        last = start + (len(rings) - 1) * n
        stones.faces.append(tuple(last + k for k in reversed(range(n))))
        stones.slots.append(0)
        stones.pieces.append(piece)

    floor, timber, stones = Build(), Build(), Build()
    top = height
    under = top - BOARD_T
    # --- the boards: rows along the side, each row in lengths with staggered joints
    rows = max(3, int(round(depth / (BOARD_W + GAP))))
    width = depth / rows
    step_mid = (a_start + a_end) / 2 if step_at is None else float(step_at)
    count = 0
    for r in range(rows):
        o0, o1 = r * width + GAP / 2, (r + 1) * width - GAP / 2
        outer = r >= rows - 1 or (r == rows - 2 and rows >= 6)
        middle = 0.25 <= (r + 0.5) / rows <= 0.8
        a = a_start - (rng.random() * 1.2 if r % 2 else 0.0)
        # the boards in front of a step are cut there: feet wear them pale, not the whole length of the row
        cuts = [step_mid - 0.6, step_mid + 0.6] if (step is not None and r >= rows // 2) else []
        while a < a_end - 0.01:
            piece_len = rng.uniform(1.8, 3.6)
            stop = a + piece_len
            for c in cuts:
                if a + 0.05 < c < stop:
                    stop = c
                    break
            b0, b1 = max(a, a_start), min(stop, a_end)
            a = stop
            if b1 - b0 < 0.05:
                continue
            near_step = bool(cuts) and abs((b0 + b1) / 2 - step_mid) < 0.6
            if outer and not near_step:
                slot = 2                                     # rain-dark at the outer edge
            elif middle or near_step or rng.random() < 0.15:
                slot = 1                                     # worn pale where feet go
            else:
                slot = 0
            j0, j1 = b0 + (GAP / 2 if b0 > a_start else 0.0), b1 - (GAP / 2 if b1 < a_end else 0.0)
            sink = rng.uniform(-0.002, 0.002)
            block(floor, j0, j1, under + sink, top + sink, o0, o1 + (0.02 if r == rows - 1 else 0.0), slot, rng.random())
            count += 1
    # --- the frame under it: an edge beam, a ledger on the wall, joists across, short posts on stones
    edge_o0, edge_o1 = depth - 0.02 - EDGE_W, depth - 0.02
    block(timber, a_start, a_end, under - EDGE_H, under, edge_o0, edge_o1, 3, rng.random())
    block(timber, a_start, a_end, under - 0.09, under, 0.0, 0.08, 1, rng.random())
    a = a_start + 0.05
    joist_places = []
    while a < a_end:
        joist_places.append(min(a, a_end - 0.05))
        a += 0.91
    if joist_places[-1] < a_end - 0.3:
        joist_places.append(a_end - 0.05)
    for a in joist_places:
        block(timber, a - 0.03, a + 0.03, under - 0.09, under, 0.08, edge_o0, 2, rng.random())
    post_places = []
    if posts:
        n = max(1, int(round((a_end - a_start) / posts)))
        post_places = [a_start + POST / 2 + (a_end - a_start - POST) * k / n for k in range(n + 1)]
    for a in joist_places:
        if any(abs(a - p) < 0.35 for p in post_places):
            continue
        sa = a + (rng.random() - 0.5) * 0.02
        so = (edge_o0 + edge_o1) / 2
        block(timber, sa - SHORT / 2, sa + SHORT / 2, 0.08, under - EDGE_H, so - SHORT / 2, so + SHORT / 2, 0, rng.random())
        rough_stone(sa, so, 0.13, 0.13, 0.08, -0.06, rng.random())
        if depth > 1.3:
            mo = depth / 2
            block(timber, sa - SHORT / 2, sa + SHORT / 2, 0.08, under - 0.09, mo - SHORT / 2, mo + SHORT / 2, 0, rng.random())
            rough_stone(sa, mo, 0.12, 0.12, 0.08, -0.06, rng.random())
    # --- the posts at the outer edge and the beam they carry under the eave
    beam_top = None
    if posts:
        po = edge_o1 - POST / 2
        if beam_height is not None:
            beam_top = float(beam_height)
        else:
            samples = building.get('tile_roof_under')
            eaves = str(building.get('tile_roof_eaves', '')).split(',')
            if samples is not None and side_name in eaves and len(samples) >= 2:
                samples = list(samples)
                e = po + BEAM_W / 2
                i = min(int(e / 0.1), len(samples) - 2)
                f = min(1.0, max(0.0, e / 0.1 - i))
                under_z = samples[i] * (1 - f) + samples[i + 1] * f
                beam_top = under_z - RAFTER_H - 0.004 - low.z
            else:
                beam_top = high.z - low.z
        if beam_top < top + 1.0:
            raise ValueError('the beam would stand only %.2f m above the floor: give a lower height or a beam_height' % (beam_top - top))
        for a in post_places:
            rough_stone(a, po, 0.19, 0.19, 0.1, -0.06, rng.random())
            block(timber, a - POST / 2, a + POST / 2, 0.1, beam_top - BEAM_H, po - POST / 2, po + POST / 2, 0, rng.random())
        block(timber, a_start - 0.15, a_end + 0.15, beam_top - BEAM_H, beam_top, po - BEAM_W / 2, po + BEAM_W / 2, 1, rng.random())
    # --- the step
    if step == 'stone':
        sh = max(0.12, top - 0.2)
        rough_stone(step_mid, depth + 0.3, 0.5, 0.27, sh, -0.06, rng.random())
    elif step == 'wood':
        sh = top / 2
        block(timber, step_mid - 0.5, step_mid + 0.5, sh - 0.035, sh, depth + 0.0, depth + 0.3, 1, rng.random())
        for s in (-0.38, 0.38):
            block(timber, step_mid + s - 0.05, step_mid + s + 0.05, 0.05, sh - 0.035, depth + 0.05, depth + 0.25, 0, rng.random())
            rough_stone(step_mid + s, depth + 0.15, 0.11, 0.13, 0.05, -0.05, rng.random())
    if collection is None:
        collection = bpy.data.collections.new('lay_veranda')
        bpy.context.scene.collection.children.link(collection)
    boards = _material(board_material)
    worn = _copy(boards, 'worn', (('Darken', 1.3), ('Grime', 0.05), ('Wet', 0.0), ('Edge wear', 0.4)))
    rain = _copy(boards, 'rain-dark', (('Darken', 0.55), ('Grime', 0.55), ('Wet', 0.5)))
    wood = _copy(_material(timber_material), 'timber', (('Darken', 0.6), ('Grime', 0.45)))
    along_axis = axis
    across_axis = 'y' if axis == 'x' else 'x'
    floor_obj = floor.make('veranda floor', [_turned(boards, along_axis), _turned(worn, along_axis), _turned(rain, along_axis)], collection, frame, ground)
    frame_obj = timber.make('veranda frame', [wood, _turned(wood, along_axis), _turned(wood, across_axis), _turned(rain, along_axis)], collection, frame, ground)
    stones_obj = stones.make('veranda stones', [_material(stone_material)], collection, frame, ground)
    floor_obj['boards'] = count
    return {'floor': floor_obj, 'frame': frame_obj, 'stones': stones_obj, 'floor_height': ground + top, 'boards': count,
            'beam_height': None if beam_top is None else ground + beam_top}


def main(argv=None):
    argv = sys.argv[sys.argv.index('--') + 1:] if argv is None and '--' in sys.argv else (argv if argv is not None else sys.argv[1:])
    parser = argparse.ArgumentParser(description=TOOL['what'] + '. Trap: ' + TOOL['trap'] + '.')
    parser.add_argument('--blend', help='the .blend file to open')
    parser.add_argument('--object', help='the building (a box)')
    parser.add_argument('--out', help='where to save the result (.blend)')
    parser.add_argument('--side', default='front', help='default front')
    parser.add_argument('--depth', type=float, default=0.9, help='metres out from the wall; default 0.9')
    parser.add_argument('--height', type=float, default=0.45, help="the floor's top above the foot; default 0.45")
    parser.add_argument('--posts', type=float, default=1.82, help='the posts\' spacing; default 1.82 (0 none)')
    parser.add_argument('--step', choices=('stone', 'wood'), default=None, help='a step at the edge; default none')
    parser.add_argument('--step-at', type=float, default=None, help='metres along the side to the step; default the middle')
    parser.add_argument('--seed', type=int, default=0)
    args = parser.parse_args(argv)
    if not (args.blend and args.object and args.out):
        parser.error('--blend, --object and --out are needed')
    bpy.ops.wm.open_mainfile(filepath=args.blend)
    building = bpy.data.objects.get(args.object)
    if building is None:
        parser.error('no object %r in %s' % (args.object, args.blend))
    made = lay(building, side=args.side, depth=args.depth, height=args.height, posts=args.posts, step=args.step,
               step_at=args.step_at, seed=args.seed)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.out))
    print('%d boards; saved %s' % (made['boards'], args.out))


if __name__ == '__main__':
    main()
