"""
What this file does: checks lay_stone's timber frames (frames='wood', the default): every window and door has a casing up
both sides and a head over it, every window a sill under it; no frame member overlaps a block, a band, a quoin or the
sash; every member stands in front of the block faces; the courses stop at the frames, a tight joint short of them, in
every course the frame crosses and above its head; the lying members (heads, sills) wear the frame material's picture
turned to run along them; wrong 'frames' values are refused; the same seed makes the same frames; frames='stone'
builds exactly what the tool built before the frames came (the same vertices in the same places); and 'lit' makes the
windows asked for glow in the street's lit glass.
    python3 tests/test_store_frames.py
"""
import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import check, fresh_scene  # noqa: E402

import bpy  # noqa: E402
import numpy  # noqa: E402
from mathutils import Vector  # noqa: E402

DOOR_AND_WINDOW = [('front', 'door', 0.3, 0.0, 0.9, 2.0), ('front', 'window', 1.7, 1.0, 0.8, 1.0)]
HOUSE = [('front', 'door', 1.0, 0.0, 1.0, 2.2), ('front', 'window', 3.0, 1.0, 0.9, 1.4), ('+x', 'window', 2.0, 4.2, 0.8, 1.2)]
# what lay_stone.py built before the frames came, for these two walls: vertices, faces, and the vertices' places
BEFORE = {'door and window': (2152, 1430, '9902b29a2ce8f6d10326619394d715b30cee8fab'),
          'house': (15144, 9654, 'bbaa32a92deff73cd9ed7ccda8f84cd9d0a96c1e')}


def box(name, size, location, turn=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = size
    obj.rotation_euler = (0.0, 0.0, turn)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return obj


def side_frame(wall, name):
    """The side's own frame as lay_stone uses it: its origin (the middle of the face at z = 0), along (to the right
    seen from outside), out (its normal), and its ends along it."""
    import lay_stone
    side = [s for s in lay_stone.upright_sides(wall) if s['name'] == lay_stone.SIDE_NAMES.get(name, name)][0]
    return side


def pieces(stonework, side):
    """Every piece of the stonework (one per number 'pp_piece'), with its kind (frame, stone, block, sash or door wood,
    glass, dark), its material, its number of points and its box in the side's own frame: u along, d out, z up."""
    mesh = stonework.data
    count = len(mesh.polygons)
    numbers = numpy.empty(count)
    mesh.attributes['pp_piece'].data.foreach_get('value', numbers)
    slots = numpy.empty(count, dtype=numpy.int64)
    mesh.polygons.foreach_get('material_index', slots)
    points = numpy.empty(len(mesh.vertices) * 3)
    mesh.vertices.foreach_get('co', points)
    points = points.reshape(-1, 3)
    origin = numpy.array(side['origin'])
    along, out = numpy.array(side['along']), numpy.array(side['normal'])
    names = [m.name for m in mesh.materials]
    import lay_stone
    found = {}
    for polygon in mesh.polygons:
        entry = found.setdefault(numbers[polygon.index], {'slot': slots[polygon.index], 'points': set()})
        entry['points'].update(polygon.vertices)
    result = []
    for number, entry in found.items():
        world = points[sorted(entry['points'])]
        relative = world - origin
        u, d, z = relative @ along, relative @ out, world[:, 2]
        name = names[entry['slot']]
        if name.startswith(lay_stone.FRAME_MATERIAL):
            kind = 'frame'
        elif name == lay_stone.WOOD_MATERIAL:
            kind = 'wood'
        elif name == lay_stone.GLASS_MATERIAL or name in lay_stone.LIT_MATERIALS:
            kind = 'glass'
        elif name == lay_stone.DARK_MATERIAL:
            kind = 'dark'
        else:
            kind = 'block' if len(world) == 16 else 'stone'
        result.append({'kind': kind, 'material': name, 'number': number, 'count': len(world), 'facing': abs(numpy.dot(out, (0.0, 0.0, 1.0))) < 0.5,
                       'lo': numpy.array([u.min(), d.min(), z.min()]), 'hi': numpy.array([u.max(), d.max(), z.max()])})
    return [p for p in result if p['hi'][1] > -0.05 and p['lo'][1] < 1.0]          # this side's pieces (in front of its face)


def overlap(p, q, tolerance=0.0005):
    return all(min(p['hi'][k], q['hi'][k]) - max(p['lo'][k], q['lo'][k]) > tolerance for k in range(3))


def openings_on(side, openings, name):
    import lay_stone
    found = []
    for o in lay_stone.read_openings(openings):
        if o['side'] == lay_stone.SIDE_NAMES.get(name, name):
            a = side['u0'] + o['left']
            c = side['z0'] + o['bottom']
            found.append((o['kind'], a, a + o['width'], c, c + o['height']))
    return found


def check_frames(stonework, wall, name, openings, label):
    side = side_frame(wall, name)
    every = pieces(stonework, side)
    frames = [p for p in every if p['kind'] == 'frame']
    stone = [p for p in every if p['kind'] in ('block', 'stone')]
    blocks = [p for p in every if p['kind'] == 'block' and p['lo'][1] > 0.0]          # this side's own blocks (a side round the corner reaches back to the wall)
    proudest = max(p['hi'][1] for p in blocks)
    count = 0
    for kind, a, b, c, e in openings_on(side, openings, name):
        mine = [f for f in frames if f['lo'][0] > a - 0.2 and f['hi'][0] < b + 0.2 and f['lo'][2] > c - 0.4 and f['hi'][2] < e + 0.5]
        foot = c + (0.25 if kind == 'door' else 0.01)
        left = [f for f in mine if abs(f['hi'][0] - a) < 0.001 and a - 0.13 < f['lo'][0] and f['lo'][2] <= foot and f['hi'][2] >= e - 0.001]
        right = [f for f in mine if abs(f['lo'][0] - b) < 0.001 and f['hi'][0] < b + 0.13 and f['lo'][2] <= foot and f['hi'][2] >= e - 0.001]
        head = [f for f in mine if f['lo'][2] >= e - 0.002 and f['lo'][0] < a - 0.05 and f['hi'][0] > b + 0.05]
        check(len(left) == 1 and len(right) == 1, '%s: the %s at %.2f has %d casings on its left and %d on its right' % (label, kind, a, len(left), len(right)))
        check(len(head) == 1, '%s: the %s at %.2f has %d heads over it' % (label, kind, a, len(head)))
        casing = left[0]
        check(0.06 < casing['hi'][0] - casing['lo'][0] < 0.12, '%s: a casing %.3f m wide (real joinery is 0.06 to 0.12)' % (label, casing['hi'][0] - casing['lo'][0]))
        sides = left + right
        if kind == 'window':
            sill = [f for f in mine if f['hi'][2] <= c + 0.001 and f['lo'][0] < a - 0.05 and f['hi'][0] > b + 0.05]
            check(len(sill) == 1, '%s: the window at %.2f has %d sills under it' % (label, a, len(sill)))
            check(sill[0]['hi'][1] > casing['hi'][1] + 0.02, '%s: the sill\'s nose does not stand out past the casing' % label)
            plinths = []
        else:
            plinths = [f for f in mine if f['lo'][2] < c + 0.001 and f['hi'][2] < c + 0.3 and f['hi'][1] > casing['hi'][1]]
            check(len(plinths) == 2, '%s: the door at %.2f stands on %d plinth blocks, not 2' % (label, a, len(plinths)))
        # the courses stop at the casings: in every course the frame crosses, a block ends a tight joint short of it
        rows = sorted({round((p['lo'][2] + p['hi'][2]) / 2, 3) for p in blocks if p['lo'][2] < e - 0.05 and p['hi'][2] > c + 0.3})
        for casing, outward in ((left[0], -1), (right[0], 1)):
            edge = casing['lo'][0] if outward < 0 else casing['hi'][0]
            for row in rows:
                beside = [p for p in blocks if p['lo'][2] < row < p['hi'][2] and (p['hi'][0] <= edge + 0.0005 if outward < 0 else p['lo'][0] >= edge - 0.0005)]
                if not beside:
                    continue
                gap = min((edge - p['hi'][0]) if outward < 0 else (p['lo'][0] - edge) for p in beside)
                check(-0.0005 < gap < 0.009, '%s: the course at z %.2f stops %.3f m from the %s\'s casing (a tight joint is 4 to 7 mm)' % (label, row, gap, kind))
        above = [p for p in blocks if p['lo'][0] > head[0]['lo'][0] - 0.02 and p['hi'][0] < head[0]['hi'][0] + 0.02 and p['lo'][2] > head[0]['hi'][2] - 0.001]
        if above:
            gap = min(p['lo'][2] for p in above) - head[0]['hi'][2]
            check(gap < 0.009, '%s: the stone over the %s\'s head starts %.3f m above it' % (label, kind, gap))
        count += 1
        for member in mine:
            check(member['hi'][1] > proudest + 0.012, '%s: a frame member stands %.3f m out, not in front of the block faces (%.3f)' % (label, member['hi'][1], proudest))
    for member in frames:
        for piece in stone:
            check(not overlap(member, piece), '%s: a frame member (u %.2f..%.2f, z %.2f..%.2f) overlaps a stone (u %.2f..%.2f, z %.2f..%.2f, d %.2f..%.2f)'
                  % (label, member['lo'][0], member['hi'][0], member['lo'][2], member['hi'][2], piece['lo'][0], piece['hi'][0], piece['lo'][2], piece['hi'][2], piece['lo'][1], piece['hi'][1]))
    holes = openings_on(side, openings, name)
    inside = lambda p, a, b, c, e, room: p['lo'][0] >= a - room and p['hi'][0] <= b + room and p['lo'][2] >= c - room and p['hi'][2] <= e + room
    sash = [p for p in every if p['kind'] == 'wood' and any(inside(p, a, b, c, e, 0.001) for kind, a, b, c, e in holes if kind == 'window')]
    door = [p for p in every if p['kind'] == 'wood' and any(inside(p, a, b, c, e, 0.011) for kind, a, b, c, e in holes if kind == 'door')]
    check(len(sash) >= 6 * sum(1 for h in holes if h[0] == 'window'), '%s: only %d sash members found' % (label, len(sash)))
    for member in frames:
        for piece in sash:
            check(not overlap(member, piece), '%s: a frame member (%s..%s) overlaps the sash (%s..%s)' % (label, numpy.round(member['lo'], 3), numpy.round(member['hi'], 3), numpy.round(piece['lo'], 3), numpy.round(piece['hi'], 3)))
        for piece in door:       # the door leaf's edges are let into its case a centimetre, as they were into the stone jambs
            into = min(min(member['hi'][k], piece['hi'][k]) - max(member['lo'][k], piece['lo'][k]) for k in range(3))
            check(not overlap(member, piece) or into < 0.0105, '%s: a frame member runs %.3f m into the door at u %.2f, z %.2f' % (label, into, piece['lo'][0], piece['lo'][2]))
    numbers = [f['number'] for f in frames]
    check(len(set(numbers)) == len(numbers) and all(0.0 <= n <= 1.0 for n in numbers), '%s: the frame members do not each carry their own pp_piece' % label)
    return count, len(frames), proudest


def test_frames():
    fresh_scene()
    import lay_stone
    wall = box('wall', (3.0, 0.5, 2.8), (0.0, 0.0, 1.4))
    stonework = lay_stone.lay(wall, openings=DOOR_AND_WINDOW, seed=2)
    check(stonework['frames'] == 'wood', "the default frames are %r, not 'wood'" % stonework['frames'])
    openings, members, proudest = check_frames(stonework, wall, 'front', DOOR_AND_WINDOW, 'door and window')
    check(openings == 2, 'only %d openings checked' % openings)
    print('PASS lay_stone frames: a door and a window, %d timber members: casings both sides, a head over each, a sill under the window, '
          'plinth blocks under the door\'s casings; none overlapping a stone or the sash; all in front of the block faces (%.3f m out); '
          'the courses stop a tight joint short of them' % (members, proudest))
    house = box('house', (8.0, 6.0, 7.0), (20.0, 0.0, 3.5), turn=0.4)
    stonework = lay_stone.lay(house, openings=HOUSE, seed=7)
    front = check_frames(stonework, house, 'front', HOUSE, 'house front')
    right = check_frames(stonework, house, '+x', HOUSE, 'house side')
    check(front[0] == 2 and right[0] == 1, 'the house: %d and %d openings checked' % (front[0], right[0]))
    print('PASS lay_stone frames: a turned house, a door and windows on two sides (and quoins, bands): the same, on both sides')


def test_material():
    fresh_scene()
    import lay_stone
    import store
    wall = box('wall', (3.0, 0.5, 2.8), (0.0, 0.0, 1.4))
    stonework = lay_stone.lay(wall, openings=DOOR_AND_WINDOW, seed=2)
    names = [m.name for m in stonework.data.materials]
    if lay_stone.FRAME_MATERIAL in store.names('materials'):
        check(names[-3:] == [lay_stone.FRAME_MATERIAL, lay_stone.FRAME_MATERIAL + ' • along x', lay_stone.FRAME_MATERIAL + ' • along y'], 'the frames are in %s' % names[-3:])
        for material, turned_on in zip(stonework.data.materials[-2:], ({'Y'}, {'X', 'Z'})):
            tree = material.node_tree
            along = tree.nodes.get('Along')
            check(along is not None, '%s has no quarter turn' % material.name)
            fed = {link.to_node.name for link in tree.links if link.from_node == along}
            check({'Vector Rotate', 'Normal picture'} <= fed, 'the quarter turn does not reach the picture and its normal picture (%s)' % fed)
            quarter = along.inputs[1].links[0].from_node
            for axis in 'XYZ':     # the turn each way a face can look: a quarter round on the faces that need it, none on the others
                looking = {'X': 0.0, 'Y': 0.0, 'Z': 0.0, axis: 1.0}['Y']
                turn = looking * quarter.inputs[1].default_value + quarter.inputs[2].default_value
                check(abs(turn - (1.5707963 if axis in turned_on else 0.0)) < 1e-5, '%s turns faces looking along %s by %.3f' % (material.name, axis, turn))
        check(store.material(lay_stone.FRAME_MATERIAL).node_tree.nodes.get('Along') is None, 'the store\'s own frame material was changed')
    side = side_frame(wall, 'front')
    every = pieces(stonework, side)
    slots = {}
    for polygon in stonework.data.polygons:
        slots.setdefault(polygon.material_index, 0)
    upright = [p for p in every if p['kind'] == 'frame' and (p['hi'][2] - p['lo'][2]) > (p['hi'][0] - p['lo'][0])]
    lying = [p for p in every if p['kind'] == 'frame' and (p['hi'][2] - p['lo'][2]) < (p['hi'][0] - p['lo'][0])]
    check(len(upright) == 6 and len(lying) == 3, '%d upright and %d lying members, not 6 and 3' % (len(upright), len(lying)))
    check(all(p['material'] == names[-3] for p in upright) and all(p['material'] == names[-2] for p in lying),
          'the upright members are not in the frame material and the lying ones (along x) in its turned copy')
    house = box('house', (8.0, 6.0, 7.0), (20.0, 0.0, 3.5))
    built = lay_stone.lay(house, openings=HOUSE, seed=7)
    side = [p for p in pieces(built, side_frame(house, '+x')) if p['kind'] == 'frame']
    sideways = [p for p in side if (p['hi'][2] - p['lo'][2]) < (p['hi'][0] - p['lo'][0])]
    check(len(sideways) == 2 and all(p['material'] == lay_stone.FRAME_MATERIAL + ' • along y' for p in sideways), 'the head and sill on a side along Y are not in the copy along y')
    own = lay_stone.lay(box('wall two', (3.0, 0.5, 2.8), (0.0, 10.0, 1.4)), openings=DOOR_AND_WINDOW, seed=2, frame_material=lay_stone.WOOD_MATERIAL)
    check([m.name for m in own.data.materials][-3:] == [lay_stone.WOOD_MATERIAL] * 3, 'a frame material with no picture to turn is not used as it is')
    print('PASS lay_stone frames: upright members in %r, lying ones in its copies turned a quarter round on the faces that need it (the grain along every member, on a side along X or Y); '
          'the store\'s own material unchanged; frame_material=%r used as it is' % (names[-3], lay_stone.WOOD_MATERIAL))


def fingerprint(stonework):
    points = numpy.empty(len(stonework.data.vertices) * 3)
    stonework.data.vertices.foreach_get('co', points)
    return len(stonework.data.vertices), len(stonework.data.polygons), hashlib.sha1(numpy.round(points, 6).tobytes()).hexdigest()


def test_stone_as_before():
    import lay_stone
    for label, size, location, turn, options in (('door and window', (3.0, 0.5, 2.8), (0.0, 0.0, 1.4), 0.0, dict(openings=DOOR_AND_WINDOW, seed=2)),
                                                 ('house', (8.0, 6.0, 7.0), (0.0, 0.0, 3.5), 0.4, dict(openings=HOUSE, seed=7))):
        fresh_scene()
        made = lay_stone.lay(box('wall', size, location, turn), frames='stone', **options)
        check(fingerprint(made) == BEFORE[label], "%s: frames='stone' does not build what the tool built before: %s, not %s" % (label, fingerprint(made), BEFORE[label]))
    print("PASS lay_stone frames='stone': the same vertices in the same places as before the frames came (two walls, %d and %d vertices)"
          % (BEFORE['door and window'][0], BEFORE['house'][0]))


def test_refused_and_same():
    import lay_stone
    fresh_scene()
    wall = box('wall', (3.0, 0.5, 2.8), (0.0, 0.0, 1.4))
    for wrong in ('timber', 'Wood', '', None, 1, ['wood']):
        try:
            lay_stone.lay(wall, openings=DOOR_AND_WINDOW, frames=wrong)
        except ValueError:
            continue
        check(False, 'frames=%r was accepted' % (wrong,))
    shapes = []
    for seed in (2, 2, 5):
        fresh_scene()
        made = lay_stone.lay(box('wall', (3.0, 0.5, 2.8), (0.0, 0.0, 1.4)), openings=DOOR_AND_WINDOW, seed=seed)
        frame_slots = {i for i, m in enumerate(made.data.materials) if m.name.startswith(lay_stone.FRAME_MATERIAL)}
        points = numpy.empty(len(made.data.vertices) * 3)
        made.data.vertices.foreach_get('co', points)
        points = points.reshape(-1, 3)
        used = sorted({v for p in made.data.polygons if p.material_index in frame_slots for v in p.vertices})
        shapes.append(points[used])
    check(shapes[0].shape == shapes[1].shape and numpy.array_equal(shapes[0], shapes[1]), 'the same seed made different frames')
    check(shapes[0].shape != shapes[2].shape or not numpy.allclose(shapes[0], shapes[2]), 'another seed made the very same frames')
    print("PASS lay_stone frames: frames='timber', 'Wood', '', None, 1 refused; the same seed makes the same frames, another seed others")


def test_lit():
    import lay_stone
    fresh_scene()
    wall = box('wall', (3.0, 0.5, 2.8), (0.0, 0.0, 1.4))
    dark = lay_stone.lay(wall, openings=DOOR_AND_WINDOW, seed=2)
    check(not any(m.name in lay_stone.LIT_MATERIALS for m in dark.data.materials) and dark['lit'] == '', 'a window glows without being asked')
    lit = lay_stone.lay(wall, openings=DOOR_AND_WINDOW, seed=2, lit=[1])
    glass = [p for p in pieces(lit, side_frame(wall, 'front')) if p['kind'] == 'glass']
    check(len(glass) == 1 and glass[0]['material'] in lay_stone.LIT_MATERIALS, 'lit=[1]: the window\'s glass is %s' % [p['material'] for p in glass])
    for wrong in ([0], [2], ['1'], 1.5, -0.1, 'all'):
        try:
            lay_stone.lay(wall, openings=DOOR_AND_WINDOW, lit=wrong)
        except ValueError:
            continue
        check(False, 'lit=%r was accepted' % (wrong,))
    fresh_scene()
    house = box('house', (8.0, 6.0, 7.0), (0.0, 0.0, 3.5))
    many = [('front', 'window', 0.6 + 1.2 * k, 1.0 + 3.0 * (k % 2), 0.8, 1.2) for k in range(6)]
    first = lay_stone.lay(house, openings=many, seed=4, lit=0.5)['lit']
    again = lay_stone.lay(house, openings=many, seed=4, lit=0.5)['lit']
    check(len(first.split(', ')) == 3 and first == again, 'lit=0.5 of 6 windows lit %r, then %r' % (first, again))
    check(lay_stone.lay(house, openings=many, seed=4, lit=1.0)['lit'] == '0, 1, 2, 3, 4, 5', 'lit=1.0 does not light every window')
    print("PASS lay_stone lit: no window glows unless asked; lit=[1] lights that window's glass in the street's lit glass; a door, a "
          "missing window, a share past 0 to 1 refused; lit=0.5 lights 3 of 6 windows (%s), the same with the same seed" % first)


def main():
    test_frames()
    test_lit()
    test_material()
    test_stone_as_before()
    test_refused_and_same()
    print('PASS test_store_frames')


if __name__ == '__main__':
    main()
