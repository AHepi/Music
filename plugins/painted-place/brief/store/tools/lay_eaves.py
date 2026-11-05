"""
What this file does: puts a slate roof on a stone or brick building, a box you name, the way the town street's builders
roofed their tenements: the roof overhangs the walls (by the same amount on every side, or by side), with an eaves
board (the fascia) along each eave, rafter ends showing under the overhang, and a cast-iron half-round gutter on iron
brackets in front of the eaves board, with outlets where you say (a downpipe from the downpipe tool hangs under each).
The roof is pitched (two slopes up to a ridge, a gable at each end), a lean-to (one slope up to a high side) or flat
(flat-topped, a slight fall to its gutter, an eaves board all round). The walls are carried up from the box's top to
meet the roof (the gables and the wall head, in a stone material). Nothing is moved, and nothing is placed anywhere you
did not say.

From your own Blender script:

    import sys
    sys.path.insert(0, FOLDER + '/store/tools')       # FOLDER is your copy of the brief folder
    import lay_stone, lay_eaves, downpipe
    lay_stone.lay(house, sides=['front'], openings=[...])                  # first the stone (it writes how far it stands out)
    made = lay_eaves.lay(house, kind='pitched', ridge='front', overhang={'front': 0.42, 'back': 0.42, 'left': 'shared',
                         'right': 'shared'}, outlets={'front': [0.3]}, seed=2)
    made['roof'], made['eaves'], made['gutters'], made['walls']            # slates (a list: one per slope), boards, iron, stone
    downpipe.lay(house, 'front', outlet=made['outlets'][0])                # a downpipe under the outlet, its swan neck up to it

Sides are named by the way they face in the box's own axes: 'front' (-Y), 'back' (+Y), 'left' (-X), 'right' (+X) (or
'-y', '+y', '-x', '+x'). Distances along a side are from its left end as you see it standing outside facing it.

From the command line:

    python3 lay_eaves.py --help
    python3 lay_eaves.py --blend IN.blend --object House --kind pitched --ridge front --overhang 0.42 --outlet "front 0.3" --out OUT.blend

Options, with their defaults:
    kind          'pitched'   'pitched' (two slopes, a gable at each end), 'lean-to' (one slope up to `high_side`) or
                              'flat' (flat-topped, falling a little away from `high_side`)
    overhang      0.42 m      how far the roof's edge reaches past the wall's face, on every side; or by side, a dict
                              like {'front': 0.5, 'back': 0.4, 'left': 'shared', 'right': 0.1}: 'shared' is a side shared
                              with a neighbour (a party wall): the roof stops flush with the box's face there
    pitch         auto        the slope in degrees: 36 pitched, 15 lean-to, 2 flat
    ridge         'long'      a pitched roof's ridge: 'long' (along the box's longer side), 'front' (parallel to the
                              front and back) or 'side' (parallel to the left and right sides)
    high_side     'back'      the high side of a lean-to, and the side a flat roof falls away from
    face          auto        metres the wall's face stands in front of the box: on a lay_stone wall its blocks (the
                              relief it wrote, 'stone_front', plus 0.04: 0.24 m), else 0; the overhang is measured from it
    wall_head     0.25 m      how far above the box's top the roof's underside meets the wall's face (the walls are
                              carried up to it, so a lay_stone cornice under the top stays clear under the overhang)
    gutters       True        gutters on every eave (True), none (False), or a list of sides
    outlets       none        where the gutters have outlets: {'front': [0.3, 8.6]}, metres along each side
    rafters       0.6 m       the rafter ends' spacing under the overhang (0: none)
    seed          0           the rafters' small irregularities and the eaves board's shade
    collection    none        where the objects go (a new collection 'lay_eaves')
    roof_material  'MADE • slate roof'                  (the slates; each slope its own object so the courses climb it)
    boards_material 'WOOD • peeling dark painted doors' (the eaves boards, the rafter ends, the boarding under the slates)
    iron_material  'IRON • soot-black lamp posts'        (the gutters, their brackets and outlets)
    wall_material  'SURFACE • old_stone_wall_02'         (the gables and the wall head; None: no walls carried up)

The result: {'roof': [slope objects], 'eaves': object, 'gutters': object or None, 'walls': object or None, 'outlets':
[world points (x, y, z) at the foot of each outlet, in the order given]}. Every object carries obj['kind'], and the
roof's slopes obj['pitch'] and obj['overhang'] (the dict, by side, as used).
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
import bmesh  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import store  # noqa: E402
import stain  # noqa: E402

ROOF_MATERIAL = 'MADE • slate roof'
BOARDS_MATERIAL = 'WOOD • peeling dark painted doors'
IRON_MATERIAL = 'IRON • soot-black lamp posts'
WALL_MATERIAL = 'SURFACE • old_stone_wall_02'
SIDE_NAMES = {'front': '-y', 'back': '+y', 'right': '+x', 'left': '-x', '-y': '-y', '+y': '+y', '-x': '-x', '+x': '+x'}
KINDS = ('pitched', 'lean-to', 'flat')
PITCH = {'pitched': 36.0, 'lean-to': 15.0, 'flat': 2.0}
PITCH_RANGE = {'pitched': (10.0, 60.0), 'lean-to': (3.0, 45.0), 'flat': (0.0, 5.0)}
SLAB = 0.06            # the slates and boarding, through
FASCIA_H, FASCIA_T, FASCIA_IN = 0.22, 0.03, 0.04       # the eaves board's height, thickness, and how far the slates oversail it
GUTTER_R = 0.065
FILL_DEPTH = 0.35      # how far into the box the walls carried up reach

TOOL = {
    'name': 'lay_eaves',
    'what': 'puts a slate roof on a stone or brick building (a box you name): overhanging the walls on every side or by side, with an eaves board, rafter ends under the overhang and a cast-iron gutter on brackets with outlets where you say; pitched, lean-to or flat-topped; the gables and wall head carried up in stone',
    'call': "lay_eaves.lay(house, kind='pitched', ridge='front', overhang={'front': 0.42, 'back': 0.42, 'left': 'shared', 'right': 'shared'}, outlets={'front': [0.3]}, seed=2)",
    'options': {
        'kind': "'pitched' (two slopes, a gable at each end), 'lean-to' (one slope up to high_side) or 'flat' (flat-topped, a slight fall); default 'pitched'",
        'overhang': "metres the roof's edge reaches past the wall's face on every side (0.42), or by side: {'front': 0.5, 'left': 'shared', ...}; 'shared' stops the roof flush with the box's face (a party wall)",
        'pitch': 'the slope in degrees; default 36 pitched, 15 lean-to, 2 flat',
        'ridge': "a pitched roof's ridge: 'long' (along the longer side), 'front' (parallel to the front) or 'side'; default 'long'",
        'high_side': "the lean-to's high side, the side a flat roof falls away from: 'back', 'front', 'left' or 'right'; default 'back'",
        'face': "metres the wall's face stands in front of the box (default: lay_stone's blocks, 0.24 m, from the 'stone_front' it writes; else 0); the overhang is measured from it",
        'wall_head': "metres above the box's top where the roof's underside meets the wall's face (the walls carried up to it); default 0.25",
        'gutters': 'gutters on every eave (True), none (False) or a list of sides; default True',
        'outlets': "where the gutters have outlets, metres along each side: {'front': [0.3, 8.6]}; their feet come back in made['outlets']",
        'rafters': "the rafter ends' spacing under the overhang, metres (0.6; 0 none)",
        'seed': "the rafters' small irregularities; default 0",
        'collection': "where the objects go; default a new collection 'lay_eaves'",
        'roof_material': "default '%s' (each slope its own object, so the courses climb it)" % ROOF_MATERIAL,
        'boards_material': "eaves boards, rafter ends, the boarding under the slates; default '%s'" % BOARDS_MATERIAL,
        'iron_material': "gutters, brackets, outlets; default '%s'" % IRON_MATERIAL,
        'wall_material': "the gables and wall head; default '%s' (None: no walls carried up)" % WALL_MATERIAL,
    },
    'materials': [ROOF_MATERIAL, BOARDS_MATERIAL, IRON_MATERIAL, WALL_MATERIAL],
    'source': "the roof in building() in '/home/claude/build-55-street/fronts/render_final.py' (lines 365-395), made into a tool on the lines of lay_boards' eaves: it now overhangs every side you ask (the builders' only the front), its gutter is a real half-round on brackets with outlets instead of a solid rod, its rafter ends follow the slope, each slope is its own object so the slates' courses climb it, and the gables are solid",
    'trap': "lay the stone first: the eaves read the relief lay_stone writes on the box, so the overhang is measured past the blocks; ridge='long' runs the ridge along the box's longer side, so a terraced house narrower than it is deep gets a gable to the street: give ridge='front'; the eaves board and gutter hang 0.3 to 0.5 m below the wall head, partly hiding a lay_stone band near the top from below",
}


# ----------------------------------------------------------------------------------------------- small pieces

class Pieces:
    """Vertices, faces and a material slot per face, in the roof's frame."""

    def __init__(self):
        self.verts, self.faces, self.slots = [], [], []

    def prism(self, section, a0, a1, axis, section_slots, cap_slot):
        """A section of (b, z) points run along `axis` ('x' or 'y') from a0 to a1; b is the other horizontal axis."""
        start = len(self.verts)
        n = len(section)
        for a in (a0, a1):
            for b, z in section:
                self.verts.append((a, b, z) if axis == 'x' else (b, a, z))
        self.faces.append(tuple(start + i for i in reversed(range(n))))
        self.faces.append(tuple(start + n + i for i in range(n)))
        self.slots.extend([cap_slot, cap_slot])
        for i in range(n):
            j = (i + 1) % n
            self.faces.append((start + i, start + j, start + n + j, start + n + i))
            self.slots.append(section_slots[i] if isinstance(section_slots, (list, tuple)) else section_slots)

    def solid(self, corners, slot):
        """Eight corners: (x0 side: y0 top, y0 bottom, y1 top, y1 bottom), then the same at x1."""
        start = len(self.verts)
        self.verts.extend(corners)
        for f in ((0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)):
            self.faces.append(tuple(start + i for i in f))
            self.slots.append(slot)

    def tube_x(self, x0, x1, y, z, radius, slot, segments=10):
        """A round bar along x."""
        section = [(y + radius * math.cos(math.tau * k / segments), z + radius * math.sin(math.tau * k / segments)) for k in range(segments)]
        self.prism(section, x0, x1, 'x', slot, slot)

    def tube_z(self, x, y, z0, z1, radius, slot, segments=10):
        start = len(self.verts)
        for z in (z0, z1):
            for k in range(segments):
                a = math.tau * k / segments
                self.verts.append((x + radius * math.cos(a), y + radius * math.sin(a), z))
        self.faces.append(tuple(start + k for k in reversed(range(segments))))
        self.faces.append(tuple(start + segments + k for k in range(segments)))
        self.slots.extend([slot, slot])
        for k in range(segments):
            j = (k + 1) % segments
            self.faces.append((start + k, start + j, start + segments + j, start + segments + k))
            self.slots.append(slot)

    def make(self, name, materials, collection, frame, ground, to_local=None):
        mesh = bpy.data.meshes.new(name)
        verts = self.verts if to_local is None else [tuple(to_local @ Vector(v)) for v in self.verts]
        mesh.from_pydata(verts, [], self.faces)
        for material in materials:
            mesh.materials.append(material)
        for polygon, slot in zip(mesh.polygons, self.slots):
            polygon.material_index = slot
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


def _sides_dict(value, what, allow_shared=False):
    """A number for every side, or a dict by side: {'-y': ..., '+y': ..., '-x': ..., '+x': ...}."""
    if isinstance(value, dict):
        result = {name: None for name in ('-y', '+y', '-x', '+x')}
        for key, item in value.items():
            if key not in SIDE_NAMES:
                raise ValueError("%s: a side is 'front', 'back', 'left' or 'right' (or '-y', '+y', '-x', '+x'), not %r" % (what, key))
            result[SIDE_NAMES[key]] = item
        missing = [k for k, v in result.items() if v is None]
        if missing:
            raise ValueError('%s: give every side (front, back, left, right); missing %s' % (what, ', '.join(missing)))
    else:
        result = {name: value for name in ('-y', '+y', '-x', '+x')}
    for key, item in result.items():
        if allow_shared and item == 'shared':
            continue
        if isinstance(item, str) or not 0.0 <= float(item) <= 2.0:
            raise ValueError("%s is 0 to 2 m%s, not %r" % (what, " or 'shared'" if allow_shared else '', item))
        result[key] = float(item)
    return result


# ----------------------------------------------------------------------------------------------- the tool

def lay(box, kind='pitched', overhang=0.42, pitch=None, ridge='long', high_side='back', face=None, wall_head=0.25,
        gutters=True, outlets=None, rafters=0.6, seed=0, collection=None, roof_material=ROOF_MATERIAL,
        boards_material=BOARDS_MATERIAL, iron_material=IRON_MATERIAL, wall_material=WALL_MATERIAL):
    """Roof the box (see the note at the top). Returns {'roof': [objects], 'eaves': object, 'gutters': object or None,
    'walls': object or None, 'outlets': [points]}."""
    if box is None or box.type != 'MESH':
        raise ValueError('lay_eaves needs a mesh object (the building)')
    if kind not in KINDS:
        raise ValueError("kind is 'pitched', 'lean-to' or 'flat', not %r" % (kind,))
    if ridge not in ('long', 'front', 'side'):
        raise ValueError("ridge is 'long', 'front' or 'side', not %r" % (ridge,))
    if SIDE_NAMES.get(high_side) is None:
        raise ValueError("high_side is 'back', 'front', 'left' or 'right', not %r" % (high_side,))
    pitch = PITCH[kind] if pitch is None else float(pitch)
    low_pitch, high_pitch = PITCH_RANGE[kind]
    if not low_pitch <= pitch <= high_pitch:
        raise ValueError('a %s roof is pitched %g to %g degrees, not %r' % (kind, low_pitch, high_pitch, pitch))
    wall_head = float(wall_head)
    if not 0.0 <= wall_head <= 2.0:
        raise ValueError('wall_head is 0 to 2 m, not %r' % (wall_head,))
    rafters = float(rafters or 0.0)
    if rafters and not 0.25 <= rafters <= 2.0:
        raise ValueError('rafters is a spacing of 0.25 to 2 m (or 0 for none), not %r' % (rafters,))
    over = _sides_dict(overhang, 'overhang', allow_shared=True)
    bpy.context.view_layer.update()
    rng = random.Random(seed)
    face = stain_face(box, face)
    location, rotation, _ = box.matrix_world.decompose()
    box_frame = Matrix.Translation(location) @ rotation.to_matrix().to_4x4()
    to_box = box_frame.inverted()
    corners = [to_box @ (box.matrix_world @ Vector(c)) for c in box.bound_box]
    low = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
    high = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
    size_x, size_y = high.x - low.x, high.y - low.y
    # the roof's own frame: its eaves run along x, its slope climbs +y (a lean-to's and a flat roof's towards the high side)
    if kind == 'pitched':
        along_x = size_x >= size_y if ridge == 'long' else ridge == 'front'
        turn = Matrix.Identity(4) if along_x else Matrix.Rotation(math.pi / 2, 4, 'Z')
    else:
        name = SIDE_NAMES[high_side]
        turn = {'+y': Matrix.Identity(4), '-y': Matrix.Rotation(math.pi, 4, 'Z'),
                '-x': Matrix.Rotation(math.pi / 2, 4, 'Z'), '+x': Matrix.Rotation(-math.pi / 2, 4, 'Z')}[name]
    centre = (low + high) / 2
    frame = box_frame @ Matrix.Translation(Vector((centre.x, centre.y, 0.0))) @ turn
    to_roof = frame.inverted()
    # which of the box's sides is which side of the roof's frame
    roof_side = {}
    for name, direction in (('-y', (0, -1, 0)), ('+y', (0, 1, 0)), ('-x', (-1, 0, 0)), ('+x', (1, 0, 0))):
        d = turn.to_3x3().inverted() @ Vector(direction)
        roof_side[name] = ('+' if (d.x if abs(d.x) > 0.5 else d.y) > 0 else '-') + ('x' if abs(d.x) > 0.5 else 'y')
    box_side = {v: k for k, v in roof_side.items()}
    length, span = (size_x, size_y) if abs(turn[0][0]) > 0.5 else (size_y, size_x)
    top = high.z
    o = {roof_side[k]: v for k, v in over.items()}                                  # by the roof's sides
    shared = {k: v == 'shared' for k, v in o.items()}
    wall_face = {k: (0.0 if shared[k] else face) for k in o}                        # the wall's face past the box
    edge_past = {k: (0.0 if shared[k] else face + o[k]) for k in o}                 # the roof's edge past the box
    yf, yb = -span / 2 - wall_face['-y'], span / 2 + wall_face['+y']               # the walls' faces
    xl, xr = -length / 2 - wall_face['-x'], length / 2 + wall_face['+x']
    ye_f, ye_b = -span / 2 - edge_past['-y'], span / 2 + edge_past['+y']             # the roof's edges
    xe_l, xe_r = -length / 2 - edge_past['-x'], length / 2 + edge_past['+x']
    slope = math.tan(math.radians(pitch))
    lift = SLAB / math.cos(math.radians(pitch))
    seat = top + wall_head
    ridge_y = (yf + yb) / 2

    if kind == 'pitched':
        def under(y):
            return seat + ((yb - yf) / 2 - abs(y - ridge_y)) * slope
    else:
        def under(y):
            return seat + (y - yf) * slope

    roof, wall, iron = [], Pieces(), Pieces()
    boards = Pieces()
    SLATE, BOARDING = 0, 1
    # ---- the slates: one object per slope, so the slate material's courses climb each
    if kind == 'pitched':
        front, back = Pieces(), Pieces()
        front.prism([(ye_f, under(ye_f)), (ridge_y, under(ridge_y)), (ridge_y, under(ridge_y) + lift), (ye_f, under(ye_f) + lift)],
                    xe_l, xe_r, 'x', [BOARDING, SLATE, SLATE, SLATE], SLATE)
        cap = under(ridge_y) + lift
        front.prism([(ridge_y - 0.13, cap - 0.13 * slope + 0.004), (ridge_y + 0.13, cap - 0.13 * slope + 0.004), (ridge_y, cap + 0.06)],
                    xe_l - 0.01, xe_r + 0.01, 'x', SLATE, SLATE)                    # the ridge's capping
        back.prism([(ridge_y, under(ridge_y)), (ye_b, under(ye_b)), (ye_b, under(ye_b) + lift), (ridge_y, under(ridge_y) + lift)],
                   xe_l, xe_r, 'x', [BOARDING, SLATE, SLATE, SLATE], SLATE)
        slopes = [(front, Matrix.Identity(4), 'roof slope %s' % box_side['-y']), (back, Matrix.Rotation(math.pi, 4, 'Z'), 'roof slope %s' % box_side['+y'])]
        eaves_sides = ['-y', '+y']
    else:
        one = Pieces()
        one.prism([(ye_f, under(ye_f)), (ye_b, under(ye_b)), (ye_b, under(ye_b) + lift), (ye_f, under(ye_f) + lift)],
                  xe_l, xe_r, 'x', [BOARDING, SLATE, SLATE, SLATE], SLATE)
        slopes = [(one, Matrix.Identity(4), 'roof')]
        eaves_sides = ['-y', '+y'] if not shared['+y'] else ['-y']
    ground = location.z + low.z
    slate_materials = [_material(roof_material), _material(boards_material)]
    if collection is None:
        collection = bpy.data.collections.new('lay_eaves')
        bpy.context.scene.collection.children.link(collection)
    for pieces, spin, name in slopes:
        obj = pieces.make(name, slate_materials, collection, frame @ spin, ground, to_local=spin.inverted())
        obj['kind'] = kind
        obj['pitch'] = pitch
        obj['overhang'] = {box_side[k]: ('shared' if shared[k] else o[k]) for k in o}
        roof.append(obj)

    # ---- eaves boards (fascia): along the eaves; on a flat roof all round
    def out_of(side):
        return -1.0 if side[0] == '-' else 1.0

    board_sides = [s for s in eaves_sides if not shared[s] and o[s] > 0.05]
    for side in board_sides:
        y_edge = ye_f if side == '-y' else ye_b
        y_out = y_edge - out_of(side) * FASCIA_IN
        z_top = under(y_edge) + lift
        ya, yb_ = sorted((y_out, y_out - out_of(side) * FASCIA_T))
        boards.prism([(ya, z_top - FASCIA_H), (yb_, z_top - FASCIA_H), (yb_, z_top), (ya, z_top)], xe_l, xe_r, 'x', 0, 0)
    if kind == 'flat':
        for side in ('-x', '+x'):
            if shared[side] or o[side] <= 0.05:
                continue
            x_edge = xe_l if side == '-x' else xe_r
            x_out = x_edge - out_of(side) * FASCIA_IN
            xa, xb = sorted((x_out, x_out - out_of(side) * FASCIA_T))
            top_l, top_h = under(ye_f) + lift, under(ye_b) + lift
            boards.solid([(xa, ye_f, top_l), (xa, ye_f, top_l - FASCIA_H), (xa, ye_b, top_h), (xa, ye_b, top_h - FASCIA_H),
                          (xb, ye_f, top_l), (xb, ye_f, top_l - FASCIA_H), (xb, ye_b, top_h), (xb, ye_b, top_h - FASCIA_H)], 0)
    # ---- rafter ends under the overhang, from inside the wall's face out to the eaves board, following the slope
    rafter_count = 0
    if rafters:
        for side in board_sides:
            y_wall = yf if side == '-y' else yb
            y_edge = (ye_f if side == '-y' else ye_b) - out_of(side) * (FASCIA_IN + FASCIA_T)
            y_in = y_wall - out_of(side) * 0.06
            ys = sorted((y_in, y_edge))
            count = max(2, int(round((xr - xl - 0.3) / rafters)) + 1)
            for k in range(count):
                x = xl + 0.15 + (xr - xl - 0.3) * k / (count - 1) + rng.uniform(-0.02, 0.02)
                deep = 0.12 + rng.uniform(-0.01, 0.01)
                corners = []
                for xx in (x - 0.0375, x + 0.0375):
                    for y in ys:
                        corners.append((xx, y, under(y) + 0.002))
                        corners.append((xx, y, under(y) - deep))
                boards.solid(corners, 0)
                rafter_count += 1
    eaves = boards.make('eaves', [_material(boards_material)], collection, frame, ground)
    eaves['kind'] = kind
    eaves['rafters'] = rafter_count
    eaves['eaves boards'] = len(board_sides) + (2 if kind == 'flat' else 0)

    # ---- gutters: half-round cast iron on brackets, in front of each eaves board, outlets where asked
    if gutters is True:
        gutter_sides = [s for s in board_sides if kind == 'pitched' or s == '-y']    # a lean-to's or flat roof's on its low side
    elif not gutters:
        gutter_sides = []
    else:
        asked = [roof_side[SIDE_NAMES.get(s, s)] if SIDE_NAMES.get(s, s) in roof_side else None for s in gutters]
        if None in asked:
            raise ValueError("gutters is True, False or a list of sides ('front', 'back', 'left', 'right'), not %r" % (gutters,))
        wrong = [box_side[s] for s in asked if s not in board_sides]
        if wrong:
            raise ValueError('a gutter goes on an eave: %s has none on this roof (eaves: %s)' % (', '.join(wrong), ', '.join(box_side[s] for s in board_sides)))
        gutter_sides = asked
    outlet_points = []
    asked_outlets = {}
    for key, places in dict(outlets or {}).items():
        if SIDE_NAMES.get(key) is None or roof_side[SIDE_NAMES[key]] not in gutter_sides:
            raise ValueError('an outlet is on side %r, which has no gutter (gutters: %s)' % (key, ', '.join(box_side[s] for s in gutter_sides) or 'none'))
        asked_outlets[SIDE_NAMES[key]] = [float(p) for p in places]
    gutter_obj = None
    if gutter_sides:
        for side in gutter_sides:
            y_edge = ye_f if side == '-y' else ye_b
            y_board = y_edge - out_of(side) * FASCIA_IN                             # the eaves board's outer face
            yc = y_board + out_of(side) * (GUTTER_R + 0.008)
            zc = under(y_edge) + lift - 0.055
            x0, x1 = xe_l + 0.02, xe_r - 0.02
            outer = [(yc + GUTTER_R * math.cos(a), zc + GUTTER_R * math.sin(a)) for a in [math.pi + math.pi * k / 10 for k in range(11)]]
            inner = [(yc + (GUTTER_R - 0.006) * math.cos(a), zc + (GUTTER_R - 0.006) * math.sin(a)) for a in [2 * math.pi - math.pi * k / 10 for k in range(11)]]
            iron.prism(outer + inner, x0, x1, 'x', 0, 0)                                 # the half-round channel, open at the top
            bead_y = yc + out_of(side) * GUTTER_R
            iron.tube_x(x0, x1, bead_y, zc + 0.004, 0.011, 0, segments=8)              # the rolled bead on its front rim
            count = max(2, int(math.ceil((x1 - x0) / 0.9)) + 1)                      # brackets about every 0.9 m
            for k in range(count):
                x = x0 + 0.08 + (x1 - x0 - 0.16) * k / (count - 1)
                ring = [(yc + (GUTTER_R + 0.006) * math.cos(a), zc + (GUTTER_R + 0.006) * math.sin(a)) for a in [math.pi + math.pi * j / 8 for j in range(9)]]
                ring += [(yc + (GUTTER_R + 0.001) * math.cos(a), zc + (GUTTER_R + 0.001) * math.sin(a)) for a in [2 * math.pi - math.pi * j / 8 for j in range(9)]]
                iron.prism(ring, x - 0.015, x + 0.015, 'x', 0, 0)
                ya, yb_ = sorted((y_board, y_board + out_of(side) * 0.012))
                iron.solid([(x - 0.015, ya, zc + 0.03), (x - 0.015, ya, zc - 0.07), (x - 0.015, yb_, zc + 0.03), (x - 0.015, yb_, zc - 0.07),
                            (x + 0.015, ya, zc + 0.03), (x + 0.015, ya, zc - 0.07), (x + 0.015, yb_, zc + 0.03), (x + 0.015, yb_, zc - 0.07)], 0)
            for end in (x0, x1):                                                       # stop ends
                cap = [(yc + GUTTER_R * math.cos(a), zc + GUTTER_R * math.sin(a)) for a in [math.pi + math.pi * k / 10 for k in range(11)]]
                iron.prism(cap, end - 0.004, end + 0.004, 'x', 0, 0)
            for along in asked_outlets.get(box_side[side], []):
                sides_info = stain.wall_side(box, box_side[side])
                if not 0.0 <= float(along) <= sides_info['length']:
                    raise ValueError('an outlet at %r m is off the %s side (0 to %.2f m)' % (along, box_side[side], sides_info['length']))
                world = sides_info['origin'] + sides_info['along'] * float(along)
                x = (to_roof @ Vector((world.x, world.y, world.z))).x
                if not x0 + 0.06 <= x <= x1 - 0.06:
                    raise ValueError('an outlet at %r m is past the gutter\'s ends' % (along,))
                foot = zc - GUTTER_R - 0.14
                iron.tube_z(x, yc, foot, zc - GUTTER_R + 0.01, 0.042, 0)
                outlet_points.append(tuple(frame @ Vector((x, yc, foot))))
        gutter_obj = iron.make('gutters', [_material(iron_material)], collection, frame, ground)
        gutter_obj['kind'] = kind
        gutter_obj['gutters'] = len(gutter_sides)
        gutter_obj['outlets'] = len(outlet_points)

    # ---- the walls carried up from the box's top to the roof: the gables (or a lean-to's sides) and the wall head
    walls_obj = None
    if wall_material is not None:
        for side in ('-y', '+y'):                                                     # the long sides: up to the underside there
            y_wall = yf if side == '-y' else yb
            z_up = under(y_wall)
            if z_up - top < 0.01:
                continue
            ya, yb_ = sorted((y_wall, y_wall - out_of(side) * FILL_DEPTH))
            wall.prism([(ya, top), (yb_, top), (yb_, z_up), (ya, z_up)], xl + FILL_DEPTH, xr - FILL_DEPTH, 'x', 0, 0)
        for side in ('-x', '+x'):                                                     # the ends: a gable up to the slope
            x_wall = xl if side == '-x' else xr
            section = [(yf, top), (yb, top), (yb, under(yb))]
            if kind == 'pitched':
                section.append((ridge_y, under(ridge_y)))
            section.append((yf, under(yf)))
            xa, xb = sorted((x_wall, x_wall - out_of(side) * FILL_DEPTH))
            wall.prism(section, xa, xb, 'x', 0, 0)
        walls_obj = wall.make('walls carried up', [_material(wall_material)], collection, frame, ground)
        walls_obj['kind'] = kind
    return {'roof': roof, 'eaves': eaves, 'gutters': gutter_obj, 'walls': walls_obj, 'outlets': outlet_points}


def stain_face(box, face):
    """How far the wall's face stands in front of the box: `face` if given, else lay_stone's blocks, else 0."""
    if face is not None:
        face = float(face)
        if not 0.0 <= face <= 1.5:
            raise ValueError('face is 0 to 1.5 m, not %r' % (face,))
        return face
    relief = box.get('stone_front')
    return float(relief) + stain.PAST_THE_RELIEF if relief is not None else 0.0


def main(argv=None):
    argv = sys.argv[sys.argv.index('--') + 1:] if argv is None and '--' in sys.argv else (argv if argv is not None else sys.argv[1:])
    parser = argparse.ArgumentParser(description=TOOL['what'] + '. Trap: ' + TOOL['trap'] + '.')
    parser.add_argument('--blend', help='the .blend file to open')
    parser.add_argument('--object', help='the building (a box)')
    parser.add_argument('--out', help='where to save the result (.blend)')
    parser.add_argument('--kind', choices=KINDS, default='pitched', help='default pitched')
    parser.add_argument('--overhang', type=float, default=0.42, help="metres past the wall's face on every side; default 0.42")
    parser.add_argument('--shared', action='append', default=[], help='a side shared with a neighbour (repeat for more): the roof stops flush there')
    parser.add_argument('--pitch', type=float, default=None, help='degrees; default 36 pitched, 15 lean-to, 2 flat')
    parser.add_argument('--ridge', choices=('long', 'front', 'side'), default='long', help='default long')
    parser.add_argument('--high-side', default='back', help='the lean-to\'s high side; default back')
    parser.add_argument('--no-gutters', action='store_true', help='no gutters')
    parser.add_argument('--outlet', action='append', default=[], help='"side metres", e.g. "front 0.3" (repeat for more)')
    parser.add_argument('--seed', type=int, default=0)
    args = parser.parse_args(argv)
    if not (args.blend and args.object and args.out):
        parser.error('--blend, --object and --out are needed')
    bpy.ops.wm.open_mainfile(filepath=args.blend)
    box = bpy.data.objects.get(args.object)
    if box is None:
        parser.error('no object %r in %s' % (args.object, args.blend))
    overhang = {s: ('shared' if s in args.shared else args.overhang) for s in ('front', 'back', 'left', 'right')}
    outlets = {}
    for text in args.outlet:
        parts = text.split()
        if len(parts) != 2:
            parser.error('an outlet is two words: side metres (got %r)' % text)
        outlets.setdefault(parts[0], []).append(float(parts[1]))
    made = lay(box, kind=args.kind, overhang=overhang, pitch=args.pitch, ridge=args.ridge, high_side=args.high_side,
               gutters=not args.no_gutters, outlets=outlets, seed=args.seed)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.out))
    print('%s roof: %d slopes, %d rafter ends, %d outlets; saved %s' % (args.kind, len(made['roof']), made['eaves']['rafters'], len(made['outlets']), args.out))


if __name__ == '__main__':
    main()
