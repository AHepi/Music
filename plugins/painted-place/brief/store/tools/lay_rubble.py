"""
What this file does: covers the sides you choose of a plain wall or building object you name (a box) in rubble
stonework: rough field stones of every size in uneven, wandering courses, standing out from the face in relief with
dark joints between them, small thin stones pinned in where a stone is short of its course, big squared quoin stones at
the corners. Round each door and window you give it the courses stop: the opening gets its own jamb stones, long and
short in turn up each side, a long lintel stone over it and, for a window, a sill stone under it, and a dark panel in
the opening so it reads as a hole into the dark. The stones follow the side's top: a box's flat top, a sloping top the
object has, or a lean-to's slope you give (pitch and high side, as lay_boards' lean-to roof takes them), and where the
slope rises above the box a dark backing fills behind the stones. The wall itself becomes the mortar seen in the
joints. (For dressed, squared sandstone in level courses use lay_stone; this tool lays rough rubble.) Nothing is
moved or cut, and nothing is placed anywhere you did not say.

From your own script:

    import sys; sys.path.insert(0, FOLDER + '/store/tools')
    import lay_rubble
    made = lay_rubble.lay(cow_house, sides=['left', 'front'], openings=[
        ('left', 'door', 4.4, 0.0, 1.2, 1.9),          # side, kind, from the side's left end, from its foot, width, height (m)
        ('left', 'window', 8.1, 1.05, 0.7, 0.6),
    ], pitch=12, high_side='right', seed=21)
    made['stones'], made['backing'], made['recesses']

    Sides are named by the way they face in the object's own axes: '-y' (or 'front'), '+y' ('back'), '+x' ('right'),
    '-x' ('left'). "From the left end" is measured along the side as you see it standing outside, facing it.

From the command line:

    python3 lay_rubble.py --help
    python3 lay_rubble.py --blend IN.blend --object "cow house" --sides left,front --opening "left door 4.4 0 1.2 1.9" --pitch 12 --high-side right --out OUT.blend

Options, with their defaults:
    sides           'all' (every upright side) or a list like ['front', 'left']
    openings        doors and windows: (side, 'door' or 'window', left, bottom, width, height) or dicts with those keys
    pitch           none     a lean-to's slope in degrees: the sides' tops rise towards high_side (none: the object's own top)
    high_side       'back'   the lean-to's high side: 'back', 'front', 'left', 'right' (or '+y', '-y', '-x', '+x')
    relief          0.07 m   how far the stones stand out from the wall's face (each stone half to all of it)
    quoins          True     big squared stones at the corners, long and short in turn
    fill            True     a dark panel in each opening (False: leave the wall's face showing for your own door)
    seed            0        the same seed lays the same stones
    material        'SURFACE • old_stone_wall_02'   the rubble stones; each its own shade of it (shades)
    shades          0.3      how much lighter or darker one stone is than the next; 0 uses your material as it is
    dressing_material none   jambs, lintels, sills and quoins (none: the rubble's own material)
    mortar_material 'MORTAR • dark eroded joints'  the wall becomes this, seen in the joints (None: leave it)
    recess_material 'RECESSES • near-black blue'   the panels in the openings
    collection      none     where the objects go (a new collection 'lay_rubble')

What it makes: 'rubble stones' (obj['stones'] counts them; the dressings use its second material slot), 'rubble
backing' (only where a slope rises above the object) and 'rubble recesses' (with fill). Every stone face carries
'stone_tone' and 'stone_patch'. A Bevel modifier rounds the stones' edges.
"""

import argparse
import math
import os
import random
import sys

import bpy
from mathutils import Matrix, Vector

TOOLS = os.path.dirname(os.path.abspath(__file__))
if TOOLS not in sys.path:
    sys.path.insert(0, TOOLS)
import store  # noqa: E402
import lay_boards  # noqa: E402
import _rough_stones  # noqa: E402

STONE = 'SURFACE • old_stone_wall_02'
MORTAR = 'MORTAR • dark eroded joints'
RECESS = 'RECESSES • near-black blue'
SIDE_NAMES = {'front': '-y', 'back': '+y', 'right': '+x', 'left': '-x'}
JAMB_ZONE = 0.38          # metres beside an opening given to its jamb stones (and the stones packed round them)
QUOIN_ZONE = 0.5          # metres at a corner given to its quoins
UP = Vector((0.0, 0.0, 1.0))

TOOL = {
    'name': 'lay_rubble',
    'what': 'covers the sides of a plain wall or building you name in rough rubble stonework in relief (uneven courses, '
            'pinned stones, quoins), with jamb stones, a lintel and a sill round the openings you give; follows a '
            'sloping or lean-to top. Not the dressed sandstone of lay_stone',
    'call': "lay_rubble.lay(cow_house, sides=['left', 'front'], openings=[('left', 'door', 4.4, 0.0, 1.2, 1.9)], pitch=12, high_side='right', seed=21)",
    'options': {
        'sides': "'all' or a list like ['front', 'left']; sides '-y'/'front', '+y'/'back', '+x'/'right', '-x'/'left' ('all')",
        'openings': "(side, 'door' or 'window', from the side's left end, from its foot, width, height) in metres",
        'pitch, high_side': "a lean-to's slope in degrees and its high side, as lay_boards' lean-to takes them (none: the object's own top)",
        'relief': 'how far the stones stand out from the face (0.07 m)',
        'quoins': 'big squared stones at the corners (True)',
        'fill': 'a dark panel in each opening (True; False leaves the face for your own door)',
        'seed': 'the same seed lays the same stones (0)',
        'material': "the rubble ('%s'), each stone its own shade (shades 0.3)" % STONE,
        'dressing_material': "jambs, lintels, sills, quoins (none: the rubble's own)",
        'mortar_material': "the wall becomes this, seen in the joints ('%s'; None leaves it)" % MORTAR,
        'recess_material': "the panels in the openings ('%s')" % RECESS,
        'collection': "where the objects go (a new collection 'lay_rubble')",
    },
    'materials': [STONE, MORTAR, RECESS],
    'source': "`rubble_face` in the barn builder's '54 barn first pass - render_final.py' (line 581), made into a tool with "
              "jamb stones, lintels, sills, quoins and pinned stones",
    'trap': 'the stones stand up to `relief` (7 cm) out from the wall: a door or frame you add belongs that far out, and a '
            'lean-to roof over it should overhang at least that much more',
}


# ------------------------------------------------------------------------------------------------ the sides' tops

def _lean_to_tops(wall, sides, pitch, high_side):
    """Each side's top as (u, z) points when a lean-to's slope rises towards `high_side` from the object's top."""
    name = SIDE_NAMES.get(high_side, high_side)
    if name not in ('+x', '-x', '+y', '-y'):
        raise ValueError("high_side is 'back', 'front', 'left' or 'right' (or '+y', '-y', '+x', '-x'), not %r" % (high_side,))
    location, rotation, _ = wall.matrix_world.decompose()
    frame = Matrix.Translation(location) @ rotation.to_matrix().to_4x4()
    to_frame = frame.inverted()
    corners = [to_frame @ (wall.matrix_world @ Vector(c)) for c in wall.bound_box]
    low = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
    high = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
    slope = math.tan(math.radians(pitch))
    box_top = location.z + high.z
    for side in sides:
        top = []
        for k in range(25):
            u = side['u0'] + (side['u1'] - side['u0']) * k / 24
            local = to_frame @ (side['origin'] + side['along'] * u)
            rise = {'+y': local.y - low.y, '-y': high.y - local.y, '+x': local.x - low.x, '-x': high.x - local.x}[name]
            top.append((u, box_top + max(rise, 0.0) * slope))
        side['top'] = top
    return box_top


# ------------------------------------------------------------------------------------------------ one side

class _Face:
    """Stones on one side, in its own frame: u along it (to the right seen from outside), d out from its face, z up."""

    def __init__(self, mesh, side, rng, relief):
        self.mesh, self.side, self.rng, self.relief = mesh, side, rng, relief
        self.base = side['origin'] + side['normal'] * 0.0

    def top(self, u):
        return lay_boards._top_at(self.side['top'], u)

    def rubble(self, a, b, bottom, top, slot=0, proud=None, square=False):
        """A rubble stone from a to b along, its lower and upper edges given as (left, right) heights; clipped under
        the side's top. Returns False when there was no room."""
        rng = self.rng
        top = (min(top[0], self.top(a) - 0.008), min(top[1], self.top(b) - 0.008))
        if b - a < 0.04 or max(top[0] - bottom[0], top[1] - bottom[1]) < 0.035:
            return False
        room_a, room_b = top[0] - bottom[0], top[1] - bottom[1]
        if min(room_a, room_b) < 0.02:              # under a slope one end has no room: shorten the stone to where it fits
            t = (0.02 - room_a) / (room_b - room_a)
            cut = a + (b - a) * t
            at_cut = lambda pair: pair[0] + (pair[1] - pair[0]) * t
            if room_a < room_b:
                a, bottom, top = cut, (at_cut(bottom), bottom[1]), (at_cut(top), top[1])
            else:
                b, bottom, top = cut, (bottom[0], at_cut(bottom)), (top[0], at_cut(top))
            if b - a < 0.06:
                return False
        proud = self.relief * rng.uniform(0.5, 1.0) if proud is None else proud
        middle = (a + b) / 2.0
        point = self.side['origin'] + self.side['along'] * middle + self.side['normal'] * proud
        tall = min(top[0] - bottom[0], top[1] - bottom[1])
        self.mesh.stone(point, self.side['along'], self.side['normal'], (a - middle, b - middle), bottom, top, proud + 0.02, rng,
                        slot=slot, bulge=rng.uniform(0.004, 0.009) if square else rng.uniform(0.006, 0.016),
                        jitter=0.005 if square else 0.009, twist=rng.uniform(-0.01, 0.01),
                        chip=min(0.012 if square else 0.04, tall * 0.35))
        return True

    def fill(self, a, b, low, high, slot=0):
        """Rubble packed into a rectangle (a, b) x (low, high): one row of stones 0.2 to 0.5 m long."""
        if b - a < 0.05 or high - low < 0.035:
            return 0
        made, u = 0, a
        while u < b - 0.03:
            w = self.rng.uniform(0.2, 0.5)
            end = b if b - (u + w) < 0.12 else u + w
            gap = self.rng.uniform(0.008, 0.016)
            if self.rubble(u + gap / 2.0, end - gap / 2.0, (low + 0.004, low + 0.004), (high - 0.006, high - 0.006), slot=slot):
                made += 1
            u = end
        return made


def _build_side(mesh, side, openings, shared, rng, relief, quoins, recesses):
    """Rubble, dressings and quoins on one side. Returns the number of stones."""
    face = _Face(mesh, side, rng, relief)
    u0, u1, z0 = side['u0'], side['u1'], side['z0']
    peak = max(z for _, z in side['top'])
    count_before = mesh.count
    zones = []                                           # (a, b, low, high): kept for dressings, not for the courses
    dressings = []
    for o in openings:
        a = u0 + o['left']
        b, c = a + o['width'], z0 + o['bottom']
        e = c + o['height']
        lintel = rng.uniform(0.18, 0.22)
        low = c - 0.1 if o['kind'] == 'window' else c
        zones.append((a - JAMB_ZONE, b + JAMB_ZONE, low, e + lintel))
        dressings.append((o['kind'], a, b, c, e, lintel))
        if recesses is not None:
            recesses.append([side['origin'] + side['along'] * u + side['normal'] * 0.003 + UP * z for u, z in ((a, c), (b, c), (b, e), (a, e))])
    if quoins:
        for end in ('left', 'right'):
            a, b = (u0, u0 + QUOIN_ZONE) if end == 'left' else (u1 - QUOIN_ZONE, u1)
            if u1 - u0 > 2.2 * QUOIN_ZONE:
                zones.append((a, b, z0 - 0.05, peak + 1.0))
    # the courses: uneven, each course's foot wandering a little along the wall
    courses, z = [], z0 - 0.02
    while z < peak - 0.03:
        share = max(0.0, z - z0) / max(peak - z0, 1e-6)
        h = rng.uniform(0.16, 0.24) if not courses else (0.17 - 0.06 * share) * rng.uniform(0.75, 1.3)
        courses.append((z, h, rng.uniform(0.008, 0.022), rng.uniform(1.4, 3.0), rng.uniform(0.0, 2.0 * math.pi)))
        z += h
    courses.append((z, 0.0, 0.0, 1.0, 0.0))

    def wander(k, u):
        zk, _, amplitude, period, phase = courses[k]
        return zk + (amplitude * math.sin(2.0 * math.pi * u / period + phase) if 0 < k < len(courses) - 1 else 0.0)

    joints_below = []
    for k in range(len(courses) - 1):
        zk, h = courses[k][0], courses[k][1]
        blocked = [(a, b) for a, b, low, high in zones if zk + 0.02 < high and zk + h - 0.02 > low]
        free = lay_boards._free_segments(u0, u1, blocked, minimum=0.05)
        joints = []
        for p, q in free:
            u = p
            while u < q - 1e-6:
                w = rng.uniform(0.16, 0.55)
                joint = u + w
                for below in joints_below:
                    if abs(joint - below) < 0.06:
                        joint = below + (0.07 if rng.random() < 0.5 or joint - u < 0.16 else -0.07)
                        break
                if q - joint < 0.1:
                    joint = q
                joint = min(max(joint, u + 0.08), q) if q - u > 0.08 else q
                gap = rng.uniform(0.01, 0.022)
                a, b = u + gap / 2.0, joint - gap / 2.0
                bottom = (wander(k, a) + 0.004, wander(k, b) + 0.004)
                room = (wander(k + 1, a) - 0.012, wander(k + 1, b) - 0.012)
                short = rng.random() < 0.3
                top = (room[0] - (room[0] - bottom[0]) * rng.uniform(0.2, 0.4), room[1] - (room[1] - bottom[1]) * rng.uniform(0.2, 0.4)) if short else room
                face.rubble(a, b, bottom, top)
                if short and min(room[0] - top[0], room[1] - top[1]) > 0.025:      # a thin stone pinned in over it
                    length = (b - a) * rng.uniform(0.45, 0.85)
                    start = a + rng.uniform(0.0, (b - a) - length)
                    face.rubble(start, start + length, (top[0] + 0.004, top[1] + 0.004), room, proud=relief * rng.uniform(0.35, 0.6))
                joints.append(joint)
                u = joint
        # where a course runs over or under an opening's dressings, rubble fills the rest of the course there
        for a, b, low, high in zones:
            if not (zk + 0.02 < high and zk + h - 0.02 > low):
                continue
            if high < zk + h - 0.035 and high > zk - 0.01:
                face.fill(a, b, max(high, zk) + 0.006, zk + h - 0.01)
            if low > zk + 0.035 and low < zk + h + 0.01:
                face.fill(a, b, zk + 0.004, min(low, zk + h) - 0.006)
        joints_below = joints
    # each opening's dressings: jambs long and short in turn, a lintel, a sill; rubble packed round them in the zone
    for kind, a, b, c, e, lintel in dressings:
        z = c
        row = 0
        while z < e - 0.04:
            h = min(rng.uniform(0.2, 0.3), e - z)
            if e - (z + h) < 0.12:
                h = e - z
            for side_sign, edge in ((-1, a), (1, b)):
                reach = (0.34 if (row % 2 == 0) == (side_sign < 0) else 0.21) * rng.uniform(0.92, 1.08)
                inner, outer = (edge - reach, edge) if side_sign < 0 else (edge, edge + reach)
                face.rubble(inner + 0.006, outer - 0.006, (z + 0.005, z + 0.005), (z + h - 0.008, z + h - 0.008), slot=1,
                            proud=relief + 0.012, square=True)
                if side_sign < 0:
                    face.fill(a - JAMB_ZONE + 0.006, inner - 0.006, z + 0.005, z + h - 0.008)
                else:
                    face.fill(outer + 0.006, b + JAMB_ZONE - 0.006, z + 0.005, z + h - 0.008)
            z += h
            row += 1
        reach = 0.2 if b - a < 1.6 else 0.3
        face.rubble(a - reach, b + reach, (e + 0.006, e + 0.006), (e + lintel - 0.006, e + lintel - 0.006), slot=1,
                    proud=relief + 0.012, square=True)
        face.fill(a - JAMB_ZONE + 0.006, a - reach - 0.008, e + 0.006, e + lintel - 0.006)
        face.fill(b + reach + 0.008, b + JAMB_ZONE - 0.006, e + 0.006, e + lintel - 0.006)
        if kind == 'window':
            face.rubble(a - 0.09, b + 0.09, (c - 0.095, c - 0.095), (c - 0.008, c - 0.008), slot=1, proud=relief + 0.04, square=True)
            face.fill(a - JAMB_ZONE + 0.006, a - 0.1, c - 0.095, c - 0.008)
            face.fill(b + 0.1, b + JAMB_ZONE - 0.006, c - 0.095, c - 0.008)
    # quoins: long and short in turn up each corner, wrapping a corner another built side shares
    if quoins and u1 - u0 > 2.2 * QUOIN_ZONE:
        for end in ('left', 'right'):
            corner = u0 if end == 'left' else u1
            inward = 1.0 if end == 'left' else -1.0
            z, row = z0 - 0.02, 0
            while z < max(face.top(corner), face.top(corner + inward * QUOIN_ZONE)) - 0.05:
                h = rng.uniform(0.24, 0.32)
                long_row = (row % 2 == 0) == (end == 'left')
                reach = (0.46 if long_row else 0.28) * rng.uniform(0.94, 1.06)
                past = (relief + 0.012) if shared[end] and long_row else 0.0
                outer = corner - inward * past
                inner = corner + inward * reach
                a, b = min(outer, inner), max(outer, inner)
                face.rubble(a + 0.005, b - 0.005, (z + 0.005, z + 0.005), (z + h - 0.008, z + h - 0.008), slot=1,
                            proud=relief + 0.012, square=True)
                rest = (inner + inward * 0.008, corner + inward * QUOIN_ZONE)
                face.fill(min(rest), max(rest), z + 0.005, z + h - 0.008)
                z += h
                row += 1
    return mesh.count - count_before


def _backing(side, box_top):
    """Where a side's top rises above the object's own top, a flat sheet in the face behind the stones."""
    top = side['top']
    if max(z for _, z in top) <= box_top + 0.01:
        return None
    us = sorted(set([side['u0'], side['u1']] + [u for u, _ in top]))
    corners = [(u, box_top - 0.02) for u in us] + [(u, max(box_top, lay_boards._top_at(top, u))) for u in reversed(us)]
    return [side['origin'] + side['along'] * u + side['normal'] * 0.002 + UP * z for u, z in corners]


def _flat_object(name, polygons, material, collection, ground):
    verts, faces = [], []
    for polygon in polygons:
        start = len(verts)
        verts.extend(tuple(p) for p in polygon)
        faces.append(tuple(range(start, start + len(polygon))))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    store.use_material(obj, material, ground=ground)
    return obj


def _material(value):
    return store.material(value) if isinstance(value, str) else value


def lay(wall, sides='all', openings=(), pitch=None, high_side='back', relief=0.07, quoins=True, fill=True, seed=0,
        material=STONE, shades=0.3, dressing_material=None, mortar_material=MORTAR, recess_material=RECESS, collection=None):
    """Cover the wall's sides in rubble; returns {'stones': object, 'backing': object or None, 'recesses': object or
    None} (see the note at the top)."""
    if wall is None or getattr(wall, 'type', None) != 'MESH':
        raise ValueError('lay_rubble needs a mesh object (the wall or building)')
    relief = float(relief)
    if not 0.01 <= relief <= 0.3:
        raise ValueError('relief is 0.01 to 0.3 m, not %r' % (relief,))
    if pitch is not None and not 0.0 < float(pitch) < 60.0:
        raise ValueError('pitch is a lean-to\'s slope, more than 0 and under 60 degrees (or None), not %r' % (pitch,))
    if not 0.0 <= float(shades) <= 0.9:
        raise ValueError('shades is 0 to 0.9, not %r' % (shades,))
    bpy.context.view_layer.update()
    rng = random.Random(seed)
    if sides != 'all':
        if isinstance(sides, str):
            sides = [sides]
        unknown = [s for s in sides if SIDE_NAMES.get(s, s) not in ('+x', '-x', '+y', '-y')]
        if unknown:
            raise ValueError("sides are 'all' or a list of 'front', 'back', 'left', 'right' (or '-y', '+y', '-x', '+x'), not %r" % (unknown,))
    wanted = None if sides == 'all' else {SIDE_NAMES.get(s, s) for s in sides}
    built = [s for s in lay_boards.upright_sides(wall, narrowest=0.2) if wanted is None or s['name'] in wanted]
    if not built:
        raise ValueError('no upright side of %r to cover (sides=%r)' % (wall.name, sides))
    location, rotation, _ = wall.matrix_world.decompose()
    box_top = max(s['z1'] for s in built)
    if pitch is not None:
        box_top = _lean_to_tops(wall, built, float(pitch), high_side)
    every_opening = lay_boards.read_openings(openings)
    known = {s['name'] for s in built}
    for o in every_opening:
        if o['side'] not in known:
            raise ValueError('an opening is on side %r, which is not covered (covered: %s)' % (o['side'], ', '.join(sorted(known))))
        side = next(s for s in built if s['name'] == o['side'])
        span = side['u1'] - side['u0']
        top = min(lay_boards._top_at(side['top'], side['u0'] + o['left']), lay_boards._top_at(side['top'], side['u0'] + o['left'] + o['width']))
        if o['left'] < 0 or o['left'] + o['width'] > span + 1e-6 or o['bottom'] < 0 or side['z0'] + o['bottom'] + o['height'] > top - 0.1 + 1e-6:
            raise ValueError('the %s at %.2f m on side %s (%.2f x %.2f m from %.2f m up) does not fit inside that side (%.2f m long, %.2f m to its top there)'
                             % (o['kind'], o['left'], o['side'], o['width'], o['height'], o['bottom'], span, top - side['z0']))
        if o['width'] < 0.2 or o['height'] < 0.2:
            raise ValueError('an opening is at least 0.2 x 0.2 m, not %.2f x %.2f' % (o['width'], o['height']))
    shared = lay_boards.corners_shared(built)
    foot = min(s['z0'] for s in built)
    mesh = _rough_stones.StoneMesh(Vector((location.x, location.y, foot)))
    recesses = [] if fill else None
    backings = []
    stones = 0
    for side in built:
        mine = [o for o in every_opening if o['side'] == side['name']]
        stones += _build_side(mesh, side, mine, shared[id(side)], rng, relief, quoins, recesses)
        sheet = _backing(side, box_top)
        if sheet is not None:
            backings.append(sheet)
    if collection is None:
        collection = bpy.data.collections.new('lay_rubble')
        bpy.context.scene.collection.children.link(collection)
    rubble = _rough_stones.shaded(_material(material), float(shades))
    dressing = _rough_stones.shaded(_material(dressing_material), float(shades) * 0.6) if dressing_material is not None else rubble
    made = {'stones': mesh.make('rubble stones', [rubble, dressing], collection, bevel=0.01)}
    store.mark(made['stones'], ground=foot)
    made['stones']['stones'] = stones
    made['stones']['sides'] = ', '.join(s['name'] for s in built)
    made['stones']['openings'] = len(every_opening)
    mortar = _material(mortar_material) if mortar_material is not None else None
    made['backing'] = _flat_object('rubble backing', backings, mortar or _material(MORTAR), collection, foot) if backings else None
    made['recesses'] = _flat_object('rubble recesses', recesses, _material(recess_material), collection, foot) if recesses else None
    if mortar is not None:
        store.use_material(wall, mortar, ground=foot)
    for side in built:
        made['stones']['top %s' % side['name']] = [z for _, z in side['top']]
    bpy.context.view_layer.update()
    return made


def main(argv=None):
    argv = sys.argv[sys.argv.index('--') + 1:] if argv is None and '--' in sys.argv else (argv if argv is not None else sys.argv[1:])
    parser = argparse.ArgumentParser(description=TOOL['what'] + '. Trap: ' + TOOL['trap'] + '.')
    parser.add_argument('--blend', help='the .blend file to open')
    parser.add_argument('--object', help='the wall or building object')
    parser.add_argument('--out', help='where to save the result (.blend)')
    parser.add_argument('--sides', default='all', help="'all' or a comma list like left,front; default all")
    parser.add_argument('--opening', action='append', default=[], help='"side kind left bottom width height", e.g. "left door 4.4 0 1.2 1.9" (repeat for more)')
    parser.add_argument('--pitch', type=float, default=None, help="a lean-to's slope in degrees (default: the object's own top)")
    parser.add_argument('--high-side', default='back', help="the lean-to's high side; default back")
    parser.add_argument('--relief', type=float, default=0.07, help='how far the stones stand out, metres; default 0.07')
    parser.add_argument('--no-quoins', action='store_true', help='no quoin stones at the corners')
    parser.add_argument('--no-fill', action='store_true', help='no dark panels in the openings')
    parser.add_argument('--seed', type=int, default=0, help='the same seed lays the same stones; default 0')
    args = parser.parse_args(argv)
    if not (args.blend and args.object and args.out):
        parser.error('--blend, --object and --out are needed to lay rubble')
    openings = []
    for text in args.opening:
        parts = text.split()
        if len(parts) != 6:
            parser.error('an opening is six words: side kind left bottom width height (got %r)' % text)
        openings.append((parts[0], parts[1]) + tuple(float(p) for p in parts[2:]))
    bpy.ops.wm.open_mainfile(filepath=args.blend)
    wall = bpy.data.objects.get(args.object)
    if wall is None:
        parser.error('no object %r in %s' % (args.object, args.blend))
    made = lay(wall, sides='all' if args.sides == 'all' else [s.strip() for s in args.sides.split(',')], openings=openings,
               pitch=args.pitch, high_side=args.high_side, relief=args.relief, quoins=not args.no_quoins, fill=not args.no_fill, seed=args.seed)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.out))
    print('%d rubble stones on sides %s; saved %s' % (made['stones']['stones'], made['stones']['sides'], args.out))


if __name__ == '__main__':
    main()
