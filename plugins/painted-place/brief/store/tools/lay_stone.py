"""
What this file does: turns a plain stone wall object you name (a box) into a built one, the street bundle's way: every
side you choose is covered in courses of ashlar blocks standing out in relief, each block its own chipped eight-sided
outline and its own sandstone shade, with dark joints between them; around the windows and doors you give it the courses
stop against a painted timber frame: a moulded casing up both sides, a head across the top with a drip cap, and under a
window a timber sill with a sloped top, a nose and a drip groove under it (a door's casing stands on plinth blocks); a
timber sash with glazing bars sits set back in each window's reveal and a panelled door in each door. Every frame member
is a little off true and worn at its edges, like old joinery, and stands a little in front of the blocks' faces.
frames='stone' gives the old stone surrounds instead: stone jambs, a lintel and, for a window, a deep stone sill with a
dark drip line under it. Bands (plinth, cornice) and heavy quoins at the corners are on by default; corners where two
built sides meet are wrapped by quoins that alternate from side to side. The wall itself becomes the dark mortar seen in
the joints. Nothing is moved or cut and nothing is placed anywhere you did not say.
The blocks and dressings are the store's photographed sandstone (Photographed.md), each block and dressing its own part
of the photographs, a little lighter or darker (it carries its own number 'pp_piece'); the old hand-painted sandstone
shades stay to hand through the options shades and trim_material. The frames are the shelf's photographed painted planks,
each member its own part of the picture with the grain running along it (the heads and sills wear a copy of the material,
'<name> • along x' or '• along y', its picture turned a quarter round on the faces that need it).

From your own Blender script:

    import sys
    sys.path.insert(0, FOLDER + '/store/tools')       # FOLDER is your copy of the brief folder
    import lay_stone
    stonework = lay_stone.lay(my_wall, openings=[
        ('front', 'door',   0.4, 0.0, 0.9, 2.0),      # side, kind, from the side's left end, from its foot, width, height (m)
        ('front', 'window', 1.8, 1.0, 0.8, 1.0),
    ], seed=2)
    import store
    store.prepare_for_render(bpy.context.scene)       # once, when the place is built, before drawing

    Sides are named by the way they face in the wall's own axes: '-y' (or 'front'), '+y' ('back'), '+x' ('right'),
    '-x' ('left'). "From the left end" is measured along the side as you see it standing outside, facing it.

From the command line:

    python3 lay_stone.py --help
    python3 lay_stone.py --blend IN.blend --object Wall --out OUT.blend --opening "front door 0.4 0 0.9 2.0" --opening "front window 1.8 1.0 0.8 1.0"

Options:
    openings        windows and doors, as (side, 'window' or 'door', left, bottom, width, height) or dicts with those keys
    seed            the blocks' sizes, chips and shades; default 0
    sides           which sides to build: 'all' (every upright side wider than 0.2 m) or a list like ['front', '+x']; default 'all'
    collection      where 'stonework' goes; default a new collection 'lay_stone'
    shades          the blocks' materials, one picked per block; default ['SURFACE • worn_rock_natural_01'] (the photographed
                    sandstone; lay_stone.SHADES are the twelve old 'Hand-painted sandstone • shade NN')
    trim_material   jambs, lintels, sills, bands, quoins; default 'SURFACE • worn_rock_natural_01' (the old one:
                    lay_stone.TRIM_MATERIAL, 'STONE • worn honey-grey architectural dressings')
    dark_material   drip lines and band shadows; default 'RECESSES • near-black blue'
    wood_material   sashes and doors; default 'WOOD • peeling dark painted doors'
    glass_material  window glass; default 'GLASS • sleeping navy interiors'
    mortar_material the wall becomes this, seen in the joints; default 'MORTAR • dark eroded joints' (None: leave it)
    bands           a plinth band at the foot and a cornice under the top; default True
    quoins          heavy dressed stones at the corners; default True
    fill            glass in each window and a panelled door in each door (False: leave the openings for your own); default True
    relief          how far the blocks' faces stand out from the wall face, metres; default 0.20
    frames          'wood' (default): a painted timber frame round every window and door (casings, a head with a drip
                    cap, a timber sill under a window); 'stone': the old stone jambs, lintels and sills (in trim_material)
    frame_material  the timber frames; default 'SURFACE • distressed_painted_planks' (blue-grey paint worn to the wood);
                    a photographed material with planks gets a copy turned a quarter round for the heads and sills
    lit             which windows glow: a list of their places in openings ([1, 3]; 0 is the first opening), or a share
                    of the windows from 0 to 1 picked by the seed (0.3); default None, all dark. The glow lights nothing
                    round it: give each lit window a small warm light of its own just outside the glass
    lit_materials   the lit glass, one picked per lit window by the seed; default ['GLASS • warm occupied interiors',
                    'GLASS • dim amber rooms']

The blocks' faces stand 0.20 m in front of the wall's face (the frames 0.25 to 0.31 m, the stone jambs, sills and bands
further), so pipes or lamps fixed to the wall belong 0.2 m further out; keep them off the frames. Every block writes the number 'stone_patch' (one per stone), which the stone_grain
tool reads so each block shows its own patch of grain, and 'pp_piece' (one per block or dressing), which the
photographed materials read so each shows its own part of the photographs; every frame member carries its own too.
A timber frame covers the wall from its casings' outer edges (about 0.08 m outside a window, 0.11 m outside a door) and
from under the sill (about 0.06 m under a window) to over the head (about 0.14 m over a window, 0.18 m over a door);
where that leaves a strip of a course too thin for a stone (under 0.07 m), the head grows a deeper board or the sill an
apron down to the course's line.
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
from mathutils import Vector  # noqa: E402

import store  # noqa: E402

SHADES = ['Hand-painted sandstone • shade %02d' % i for i in range(12)]          # the old painted shades, still to hand
TRIM_MATERIAL = 'STONE • worn honey-grey architectural dressings'                  # the old painted dressings
PHOTO_STONE = 'SURFACE • worn_rock_natural_01'           # Photographed.md: ashlar blocks (projected, one part per block) and dressings
PHOTO_SHADES = [PHOTO_STONE]
DARK_MATERIAL = 'RECESSES • near-black blue'
WOOD_MATERIAL = 'WOOD • peeling dark painted doors'
GLASS_MATERIAL = 'GLASS • sleeping navy interiors'
MORTAR_MATERIAL = 'MORTAR • dark eroded joints'
LIT_MATERIALS = ['GLASS • warm occupied interiors', 'GLASS • dim amber rooms']   # the street's lit glass, for windows asked to glow
FRAME_MATERIAL = 'SURFACE • distressed_painted_planks'  # the timber frames: painted planks, worn, the picture run along each member
FRAMES = ('wood', 'stone')
JOINT = 0.004                                            # the joint between a block and a timber frame, metres
SIDE_NAMES = {'front': '-y', 'back': '+y', 'right': '+x', 'left': '-x'}

TOOL = {
    'name': 'lay_stone',
    'what': 'builds a plain stone wall you name into ashlar courses in relief, with painted timber frames (casings, heads, sills), sashes and doors round the openings you give',
    'call': "lay_stone.lay(wall, openings=[('front', 'window', 1.8, 1.0, 0.8, 1.0), ('front', 'door', 0.4, 0.0, 0.9, 2.0)], seed=2)",
    'options': {
        'openings': "(side, 'window' or 'door', from the side's left end, from its foot, width, height) in metres; sides '-y'/'front', '+y'/'back', '+x'/'right', '-x'/'left'",
        'seed': "the blocks' sizes, chips and shades; default 0",
        'sides': "which sides to build: 'all' or a list like ['front', '+x']; default 'all'",
        'collection': "where 'stonework' goes; default a new collection 'lay_stone'",
        'shades': "blocks' materials, one picked per block; default ['%s'] (the photographed sandstone, each block its own part of the photographs); the old painted ones: lay_stone.SHADES, the twelve 'Hand-painted sandstone • shade NN'" % PHOTO_STONE,
        'trim_material': "bands, quoins (and with frames='stone' the jambs, lintels, sills); default '%s' (the old painted one: '%s')" % (PHOTO_STONE, TRIM_MATERIAL),
        'dark_material': "band shadows (and with frames='stone' the drip lines); default '%s'" % DARK_MATERIAL,
        'wood_material': "sashes, doors; default '%s'" % WOOD_MATERIAL,
        'glass_material': "window glass; default '%s'" % GLASS_MATERIAL,
        'mortar_material': "the wall becomes this, seen in the joints; default '%s' (None leaves it)" % MORTAR_MATERIAL,
        'bands': 'a plinth band at the foot and a cornice under the top; default True',
        'quoins': 'heavy dressed stones at the corners; default True',
        'fill': 'glass in each window and a panelled door in each door; default True',
        'relief': "metres the blocks' faces stand out from the wall face; default 0.20",
        'frames': "'wood' (default): a painted timber frame round every opening: a moulded casing up both sides, a head with a drip cap, a timber sill with a drip under each window, plinth blocks under a door's casings, each member a little off true and worn; 'stone': the old stone jambs, lintels and sills",
        'lit': "which windows glow: a list of their places in openings (0 is the first opening), or a share of the windows from 0 to 1 picked by the seed; default None (all dark). The glow lights nothing round it: give each lit window a small warm light just outside the glass",
        'lit_materials': "the lit windows' glass, one picked per window by the seed; default %s" % LIT_MATERIALS,
        'frame_material': "the timber frames; default '%s' (each member its own part of the picture, the grain along it: the heads and sills wear a copy, '<name> • along x' or '• along y', its picture turned a quarter round on the faces that need it)" % FRAME_MATERIAL,
    },
    'materials': [PHOTO_STONE, DARK_MATERIAL, WOOD_MATERIAL, GLASS_MATERIAL, MORTAR_MATERIAL, FRAME_MATERIAL] + LIT_MATERIALS + SHADES + [TRIM_MATERIAL],
    'source': 'plugins/painted-place/materials/lay_facade.py: FacadeMesh, build_face, _free_segments (and oriented_faces)',
    'trap': 'call store.prepare_for_render(scene) once before drawing: it records the stonework\'s real scale for the photographed sandstone (and stretches the old painted sandstone\'s one big picture over the place); the timber frames reach past the openings you give (about 0.08 m each side of a window and 0.11 m of a door, 0.14 m over a window and 0.18 m over a door, 0.06 m under a sill, up to 0.07 m more where a head or sill grows to a course\'s line) and stand up to 0.31 m out from the wall: leave that room between openings and from the wall\'s ends, and hang pipes and signs clear of them',
}


# ----------------------------------------------------------------------------------------------- the wall's sides

def _side_name(wall, normal):
    local = (wall.matrix_world.inverted().to_3x3() @ normal)
    local.z = 0.0
    axis = 0 if abs(local.x) >= abs(local.y) else 1
    return ('+' if local[axis] > 0 else '-') + 'xy'[axis]


def upright_sides(wall, narrowest=0.2):
    """The wall's upright sides, each a dict: name, origin (its middle at z = 0), normal (out), along (to the right as
    seen from outside), u0 and u1 (its ends along it, from the origin), z0 and z1. A box's own upright faces; for a
    mesh with many faces, the sides of its box."""
    matrix = wall.matrix_world
    found = []
    if len(wall.data.polygons) <= 12:
        normal_matrix = matrix.to_3x3().inverted_safe().transposed()
        for polygon in wall.data.polygons:
            normal = normal_matrix @ polygon.normal
            if normal.length < 1e-9 or abs(normal.normalized().z) >= 0.3:
                continue
            normal.z = 0.0
            found.append((normal.normalized(), [matrix @ wall.data.vertices[i].co for i in polygon.vertices]))
    else:
        corners = [Vector(c) for c in wall.bound_box]
        low = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
        high = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
        for axis, sign in ((0, 1), (0, -1), (1, 1), (1, -1)):
            local_normal = Vector((0.0, 0.0, 0.0))
            local_normal[axis] = sign
            normal = matrix.to_3x3() @ local_normal
            normal.z = 0.0
            if normal.length < 1e-9:
                continue
            plane = high[axis] if sign > 0 else low[axis]
            other = 1 - axis
            verts = []
            for o in (low[other], high[other]):
                for z in (low.z, high.z):
                    p = Vector((0.0, 0.0, z))
                    p[axis] = plane
                    p[other] = o
                    verts.append(matrix @ p)
            found.append((normal.normalized(), verts))
    sides = []
    for normal, verts in found:
        along = Vector((-normal.y, normal.x, 0.0)).normalized()
        centre = sum(verts, Vector()) / len(verts)
        us = [(v - centre).dot(along) for v in verts]
        zs = [v.z for v in verts]
        if max(us) - min(us) < narrowest:
            continue
        sides.append({'name': _side_name(wall, normal), 'origin': Vector((centre.x, centre.y, 0.0)), 'normal': normal,
                      'along': along, 'u0': min(us), 'u1': max(us), 'z0': min(zs), 'z1': max(zs)})
    return sides


def _end_point(side, which):
    u = side['u0'] if which == 'left' else side['u1']
    return (side['origin'] + side['along'] * u).to_2d()


def corners_shared(sides):
    """For each side, whether another built side meets it at its left and right ends (a closed corner)."""
    shared = {id(s): {'left': False, 'right': False} for s in sides}
    for a in sides:
        for b in sides:
            if a is b or abs(a['normal'].dot(b['normal'])) > 0.3:
                continue
            if (_end_point(a, 'right') - _end_point(b, 'left')).length < 0.03:
                shared[id(a)]['right'] = True
                shared[id(b)]['left'] = True
    return shared


def read_openings(openings):
    """Openings as dicts: side, kind, left, bottom, width, height."""
    result = []
    for number, item in enumerate(openings or ()):
        if isinstance(item, dict):
            side, kind = item['side'], item.get('kind', 'window')
            left, bottom, width, height = item['left'], item['bottom'], item['width'], item['height']
        else:
            side, kind, left, bottom, width, height = item
        side = SIDE_NAMES.get(side, side)
        if side not in ('+x', '-x', '+y', '-y'):
            raise ValueError("an opening's side is '+x', '-x', '+y', '-y' (or front, back, right, left), not %r" % (side,))
        if kind not in ('window', 'door'):
            raise ValueError("an opening's kind is 'window' or 'door', not %r" % (kind,))
        result.append({'side': side, 'kind': kind, 'left': float(left), 'bottom': float(bottom), 'width': float(width), 'height': float(height),
                       'index': number})
    return result


def lit_windows(openings, lit, seed=0, choices=2):
    """Which windows glow: {their place in the openings list: which lit glass}. lit is None (none), a list of places in
    the openings list (each must be a window), or a share of the windows from 0 to 1, picked by the seed."""
    if lit is None or lit is False:
        return {}
    windows = [o['index'] for o in openings if o['kind'] == 'window']
    pick = random.Random(seed * 6271 + 5)                 # its own stream, so nothing else changes
    if isinstance(lit, (list, tuple)):
        for number in lit:
            if isinstance(number, bool) or not isinstance(number, int) or number not in windows:
                raise ValueError('lit names windows by their place in the openings list (0 is the first; windows here: %s), not %r'
                                 % (windows, number))
        chosen = sorted(set(lit))
    elif isinstance(lit, (int, float)) and 0.0 <= float(lit) <= 1.0:
        chosen = sorted(pick.sample(windows, int(round(float(lit) * len(windows)))))
    else:
        raise ValueError('lit is a list of windows\' places in the openings list, or a share of the windows from 0 to 1, not %r' % (lit,))
    return {number: pick.randrange(choices) for number in chosen}


# ----------------------------------------------------------------------------------------------- the mesh

class FacadeMesh:
    """Vertices, faces, material slots and a number per stone for one wall, in each side's own frame (u along, d out,
    z up), written in world space."""

    def __init__(self, seed=0):
        self.verts, self.faces, self.materials, self.patches, self.pieces = [], [], [], [], []
        self.side = None
        self.piece_rng = random.Random(seed * 7919 + 13)    # its own stream, so the blocks are laid as before

    def point(self, u, d, z):
        p = self.side['origin'] + self.side['along'] * u + self.side['normal'] * d
        return (p.x, p.y, z)

    def poly(self, coords, faces, material, patch=None):
        start = len(self.verts)
        self.verts.extend(self.point(*c) for c in coords)
        self.faces.extend(tuple(start + i for i in f) for f in faces)
        self.materials.extend([material] * len(faces))
        if patch is None:      # a number per stone, so the stone grain samples a different patch on every block
            u, d, z = coords[0]
            patch = (abs(u * 7.31 + z * 3.17 + d * 1.3) * 0.618) % 1.0
        self.patches.extend([patch] * len(faces))
        self.pieces.extend([self.piece_rng.random()] * len(faces))      # one number per block or dressing

    def box(self, u, d, z, w, dep, h, material):
        x, y, z0, z1 = w / 2, dep / 2, z - h / 2, z + h / 2
        self.poly([(u - x, d - y, z0), (u + x, d - y, z0), (u + x, d + y, z0), (u - x, d + y, z0),
                   (u - x, d - y, z1), (u + x, d - y, z1), (u + x, d + y, z1), (u - x, d + y, z1)],
                  [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)], material)

    def span(self, u0, u1, d, z, dep, h, material):
        self.box((u0 + u1) / 2, d, z, u1 - u0, dep, h, material)

    def block(self, u, d, z, w, dep, h, material, rng):
        """An ashlar block with its own broken corners (the bundle's eight-sided chipped outline)."""
        cx = [rng.uniform(0.008, min(0.090, w * 0.16)) for _ in range(4)]
        cz = [rng.uniform(0.005, min(0.060, h * 0.22)) for _ in range(4)]
        outline = [(-w / 2 + cx[0], -h / 2), (w / 2 - cx[1], -h / 2), (w / 2, -h / 2 + cz[1]), (w / 2, h / 2 - cz[2]),
                   (w / 2 - cx[2], h / 2), (-w / 2 + cx[3], h / 2), (-w / 2, h / 2 - cz[3]), (-w / 2, -h / 2 + cz[0])]
        coords = []
        for side, dd in enumerate((d - dep / 2, d + dep / 2)):
            coords.extend((u + x, dd + (0.009 * math.sin(31 * u + 17 * z + 7 * i) if side else 0), z + zz) for i, (x, zz) in enumerate(outline))
        faces = [tuple(range(8)), tuple(range(15, 7, -1))] + [(i, i + 8, (i + 1) % 8 + 8, (i + 1) % 8) for i in range(8)]
        self.poly(coords, faces, material, patch=rng.random())

    def member(self, sections, material):
        """A moulded timber member: its cross-sections along its length, each the same number of (u, d, z) points going
        round its outline, joined into one closed piece with its two ends capped."""
        n, count = len(sections[0]), len(sections)
        faces = [(k * n + i, k * n + (i + 1) % n, (k + 1) * n + (i + 1) % n, (k + 1) * n + i)
                 for k in range(count - 1) for i in range(n)]
        faces += [tuple(range(n - 1, -1, -1)), tuple((count - 1) * n + i for i in range(n))]
        self.poly([p for section in sections for p in section], faces, material)

    def make(self, name, material_list, collection):
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(self.verts, [], self.faces)
        for material in material_list:
            mesh.materials.append(material)
        for polygon, index in zip(mesh.polygons, self.materials):
            polygon.material_index = index
        attribute = mesh.attributes.new('stone_patch', 'FLOAT', 'FACE')
        attribute.data.foreach_set('value', self.patches)
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
        return obj


def _free_segments(u0, u1, blocked, minimum=0.15):
    """Pieces of [u0, u1] not covered by any (a, b) in blocked."""
    pieces = [(u0, u1)]
    for a, b in sorted(blocked):
        new = []
        for p, q in pieces:
            if b <= p or a >= q:
                new.append((p, q))
                continue
            if a > p:
                new.append((p, a))
            if b < q:
                new.append((b, q))
        pieces = new
    return [(p, q) for p, q in pieces if q - p > minimum]


def _course_heights(z_start, z_end, course, rng):
    """Course heights filling [z_start, z_end] exactly (the last one stretched rather than a sliver left)."""
    heights, z = [], z_start
    while z < z_end - 0.01:
        h = course * rng.uniform(0.88, 1.10)
        if z_end - (z + h) < 0.12:
            h = z_end - z
        heights.append((z, h))
        z += h
    return heights


# ----------------------------------------------------------------------------------------------- timber frames

def _frame_zones(windows, doors, frame_rng):
    """Each opening's timber frame, sized like real joinery (each frame a little different): the casing's width, its
    head and sill, and the ground it covers on the wall: u from A to B, z from low to high. The courses stop at its edge."""
    zones = []
    for kind, found in (('window', windows), ('door', doors)):
        for a, b, c, e in found:
            if kind == 'window':
                size = {'casing': frame_rng.uniform(0.078, 0.088), 'band': 0.022, 'raise': 0.016, 'head': frame_rng.uniform(0.10, 0.115),
                        'cap': 0.034, 'cap_out': 0.03, 'sill': frame_rng.uniform(0.055, 0.065), 'nose': 0.04, 'plinth': 0.0}
            else:
                size = {'casing': frame_rng.uniform(0.10, 0.112), 'band': 0.026, 'raise': 0.018, 'head': frame_rng.uniform(0.13, 0.145),
                        'cap': 0.04, 'cap_out': 0.035, 'sill': 0.0, 'nose': 0.0, 'plinth': frame_rng.uniform(0.20, 0.23)}
            w = size['casing']
            zones.append({'kind': kind, 'a': a, 'b': b, 'c': c, 'e': e, 'A': a - w, 'B': b + w, 'size': size,
                          'low': c - size['sill'], 'high': e + size['head'] + size['cap']})
    return zones


def _snap_zones(zones, courses, thinnest=0.07):
    """Where a frame's head or sill leaves a strip of a course too thin for a stone, the frame grows to the course's
    line instead (a deeper head board, an apron under the sill), so no sliver of stone and no bare strip is left."""
    for zone in zones:
        for z, h in courses:
            if z < zone['high'] < z + h and z + h - zone['high'] < thinnest:
                zone['high'] = z + h
            if zone['kind'] == 'window' and z < zone['low'] < z + h and zone['low'] - z < thinnest:
                zone['low'] = z


def _wear(rng, size=0.0045):
    """How much an arris has been worn away along a member, as a smooth function of t (0 at one end, 1 at the other):
    it wanders between about half and all of size, with now and then a dent where something knocked it."""
    f1, f2, p1, p2 = rng.uniform(0.6, 1.6), rng.uniform(2.0, 4.0), rng.random(), rng.random()
    dent, where = (rng.uniform(1.0, 1.8) if rng.random() < 0.35 else 0.0), rng.uniform(0.1, 0.9)
    return lambda t: size * (0.72 + 0.2 * math.sin(2 * math.pi * (f1 * t + p1)) + 0.08 * math.sin(2 * math.pi * (f2 * t + p2))
                             + dent * math.exp(-((t - where) / 0.05) ** 2))


def _wood_frame(mesh, zone, D, upright, lying, rng, sections=14):
    """One opening's painted timber frame: a moulded casing up both sides (a flat face with a raised band at its outer
    edge), a head across the top butted over them with a drip cap, and under a window a timber sill with a sloped top,
    a nose and a drip groove under it (a door's casing stands on plinth blocks). Every member is a little off true and
    worn at its arrises, and only ever leans inward from its edges, so it never meets the stone or the sash."""
    s = zone['size']
    a, b, c, e = zone['a'], zone['b'], zone['c'], zone['e']
    A, B, low, high = zone['A'], zone['B'], zone['low'], zone['high']
    width, band, rise = s['casing'], s['band'], s['raise']
    face = D + 0.05                      # the casing's face, in front of the proudest block faces (about D + 0.037)
    back = -0.01                         # into the wall a little, so no gap shows behind any member
    head_face = face + rise + 0.004      # the head stands just proud of the casing's band
    foot = c + s['plinth']
    # the casings, up both sides
    for edge, out in ((a, -1), (b, 1)):
        tilt, bow, creep = rng.uniform(-0.003, 0.003), rng.uniform(-0.002, 0.002), rng.uniform(0.0, 0.003)
        worn_in, worn_out = _wear(rng), _wear(rng)
        rows = []
        for k in range(sections):
            t = k / (sections - 1)
            f = face + tilt * (2 * t - 1) + bow * math.sin(math.pi * t)
            c1, c2 = worn_in(t), worn_out(t)
            w = width - creep * (t if out > 0 else 1 - t)       # the outer edge creeps in (out of plumb), never out
            inner = width - band
            outline = [(0.0, back), (0.0, f - c1), (c1, f), (inner, f), (inner + 0.004, f + rise), (w - c2, f + rise), (w, f + rise - c2), (w, back)]
            rows.append([(edge + out * x, y, foot + (e - foot) * t) for x, y in outline])
        mesh.member(rows, upright)
        if s['plinth']:                 # a door's plinth block, a little prouder than the casing it carries
            p = face + rise + 0.008
            ch = 0.006
            outline = [(0.0, back), (0.0, p - ch), (ch, p), (width - ch - 0.002, p), (width - 0.002, p - ch), (width - 0.002, back)]
            top = [(ch, back), (ch, p - 2 * ch), (2 * ch, p - ch), (width - 0.002 - 2 * ch, p - ch), (width - 0.002 - ch, p - 2 * ch), (width - 0.002 - ch, back)]
            mesh.member([[(edge + out * x, y, z) for x, y in shape] for z, shape in ((c, outline), (foot - ch, outline), (foot, top))], upright)
    # the head, butted over the casings' tops, with a drip cap along its top
    drop, twist = rng.uniform(0.0, 0.003), rng.uniform(-0.0015, 0.0015)
    worn_under, worn_cap = _wear(rng), _wear(rng, 0.006)
    cap, out_cap = s['cap'], s['cap_out']
    top_z = high
    rows = []
    for k in range(sections):
        t = k / (sections - 1)
        f = head_face + twist * (2 * t - 1)
        c1, c3 = worn_under(t), worn_cap(t)
        crown = top_z - drop * t                                   # out of level: its top falls a little to one end
        under = crown - cap
        sash_front = D - 0.025
        outline = [(back, e), (sash_front, e), (f - c1, e), (f, e + c1),
                   (f, under), (f + out_cap - 0.007, under), (f + out_cap - 0.007, under - 0.007), (f + out_cap, under - 0.007),
                   (f + out_cap, crown - 0.012 - c3), (f + out_cap - c3, crown - 0.012), (f + 0.005, crown), (back, crown)]
        rows.append([(A + (B - A) * t, y, z) for y, z in outline])
    mesh.member(rows, lying)
    if zone['kind'] != 'window':
        return
    # the sill, under the window and the casings: sloped top, a nose, a drip groove under it; an apron below if the course asks
    tilt, sway = rng.uniform(-0.003, 0.003), rng.uniform(0.0, 0.002)
    worn_nose = _wear(rng, 0.007)
    nose_face = face + rise + s['nose']
    bottom = c - s['sill']
    rows = []
    for k in range(sections):
        t = k / (sections - 1)
        lean = t if tilt > 0 else 1 - t
        fall = 0.012 + abs(tilt) * lean                            # out of level at its front, a little
        c4 = worn_nose(t)
        nf = nose_face - sway * math.sin(math.pi * t)              # its nose bowed back a little in the middle
        lift = abs(tilt) * (1 - lean) * 0.5                        # its underside rises a little to one end (never falls)
        outline = [(back, c), (face + rise, c), (nf - c4, c - fall), (nf, c - fall - c4), (nf, bottom + lift),
                   (nf - 0.012, bottom + lift), (nf - 0.012, bottom + lift + 0.008), (nf - 0.020, bottom + lift + 0.008), (nf - 0.020, bottom + lift)]
        if low < bottom - 0.002:
            outline += [(face, bottom + lift), (face, low), (back, low)]
        else:
            outline += [(back, bottom + lift)]
        rows.append([(A + (B - A) * t, y, z) for y, z in outline])
    mesh.member(rows, lying)


def build_side(mesh, side, openings, shared, rng, index, materials, bands=True, quoins=True, fill=True, relief=0.20,
               frames='stone', frame_rng=None, lit_slots=None):
    """Ashlar, dressings, sashes and fills for one side. Returns the number of blocks."""
    SHADE_COUNT, TRIM, DARK, WOOD, GLASS = materials[:5]
    wood = frames == 'wood'
    D = relief
    mesh.side = side
    u0, u1, z0, z1 = side['u0'], side['u1'], side['z0'], side['z1']
    width = u1 - u0
    holes, windows, doors, window_numbers = [], [], [], []
    for o in openings:
        a = u0 + o['left']
        b, c = a + o['width'], z0 + o['bottom']
        e = c + o['height']
        if o['kind'] == 'window':
            if not (0.3 <= b - a <= 4 and 0.3 <= e - c <= 4):
                continue
            windows.append((a, b, c, e))
            window_numbers.append(o.get('index'))
            holes.append((a, b, c, e, c - 0.17, e + 0.19))           # the opening, and its dressings' bottom and top
        else:
            doors.append((a, b, c, e))
            holes.append((a, b, c, e, c, e + 0.24))
    blocks = 0
    course = 0.32 if index % 2 == 0 else 0.38
    z_end = z1 - 0.14 if bands else z1
    courses = _course_heights(z0, z_end, course, rng)
    zones = _frame_zones(windows, doors, frame_rng) if wood else []
    _snap_zones(zones, courses)
    for z, h in courses:
        zmid = z + h / 2
        if wood:     # the course stops at the frame's outer edge, a tight joint short of it, over the frame's whole height
            cutting = [(f['A'], f['B'], f['low'], f['high']) for f in zones if z < f['high'] - 1e-6 and z + h > f['low'] + 1e-6]
            in_course = [(a + 0.008 - JOINT, b - 0.008 + JOINT) for a, b, low, high in cutting]
        else:
            cutting = [(a, b, low, high) for a, b, c, e, low, high in holes if z < e + 0.05 and z + h > c - 0.05]
            in_course = [(a - 0.06, b + 0.06) for a, b, low, high in cutting]
        u = u0 - rng.uniform(0, 0.4)
        while u < u1:
            w = rng.uniform(0.46, 0.94)
            for a, b in (in_course if wood else ()):    # no sliver of stone (and no gap) beside a timber frame:
                if a - 0.12 < u + w < a:                 # a block that would stop just short of it runs on to it,
                    w = a - u
                elif u < b < u + w < b + 0.12:           # one that would end just past it stops at it
                    w = b - u
            lo, hi = max(u, u0), min(u + w, u1)
            # a block that meets an opening is cut back to the opening's edge, so stone runs right up to every reveal
            for p, q in _free_segments(lo, hi, in_course, minimum=0.12):
                front = D - 0.08 + rng.uniform(-0.018, 0.018)
                shade = rng.randrange(SHADE_COUNT) if rng.random() > 0.05 else TRIM
                mesh.block((p + q) / 2, front, zmid, q - p - 0.016, 0.16 + rng.uniform(-0.03, 0.02), h - 0.015, shade, rng)
                blocks += 1
            u += w
        # above a timber head or below a sill, stone fills the rest of the course, a tight joint off the timber
        for a, b, low, high in (cutting if wood else ()):
            for block_low, block_high in ((high + JOINT, z + h - 0.0075), (z + 0.0075, low - JOINT)):
                block_low, block_high = max(block_low, z + 0.0075), min(block_high, z + h - 0.0075)
                if block_high - block_low < 0.035:
                    continue
                span = b - a + 2 * JOINT - 0.016
                pieces = max(1, int(math.ceil(span / 0.9)))
                step = span / pieces
                for k in range(pieces):
                    p = a - JOINT + 0.008 + k * step
                    front = D - 0.08 + rng.uniform(-0.018, 0.018)
                    shade = rng.randrange(SHADE_COUNT)
                    mesh.block(p + step / 2, front, (block_low + block_high) / 2, step - 0.016, 0.16, block_high - block_low, shade, rng)
                    blocks += 1
        # where the cut course reaches above a lintel or below a sill, stone fills the rest of the course
        for a, b, low, high in (() if wood else cutting):
            for fill_low, fill_high in ((high, z + h), (z, low)):
                fill_low, fill_high = max(fill_low, z), min(fill_high, z + h)
                if fill_high - fill_low < 0.05:
                    continue
                pieces = max(1, int(math.ceil((b - a + 0.12) / 0.9)))
                step = (b - a + 0.12) / pieces
                for k in range(pieces):
                    p = a - 0.06 + k * step
                    front = D - 0.08 + rng.uniform(-0.018, 0.018)
                    shade = rng.randrange(SHADE_COUNT)
                    mesh.block(p + step / 2, front, (fill_low + fill_high) / 2, step - 0.016, 0.16, fill_high - fill_low - 0.015, shade, rng)
                    blocks += 1
    # windows: jambs, lintel, sill, drip line, sash (and glass)
    for number, (wu0, wu1, wz0, wz1) in zip(window_numbers, windows):
        ow, oh = wu1 - wu0, wz1 - wz0
        ou, oz = (wu0 + wu1) / 2, (wz0 + wz1) / 2
        if not wood:
            trim_width = rng.uniform(0.105, 0.145)
            for s in (-1, 1):
                mesh.box(ou + s * (ow / 2 + 0.07), D - 0.02, oz, trim_width, 0.18, oh + 0.25, TRIM if rng.random() > 0.14 else rng.randrange(SHADE_COUNT))
            mesh.box(ou, D - 0.01, oz + oh / 2 + 0.11, ow + 0.32, 0.24, 0.16, TRIM)
            mesh.box(ou, D + 0.04, oz - oh / 2 - 0.10, ow + 0.36, 0.34, 0.14, TRIM)
            mesh.box(ou, D - 0.06, oz - oh / 2 - 0.22, ow + 0.13, 0.19, 0.11, DARK)
        glass = D - 0.10
        if fill:
            mesh.box(ou, glass + 0.015, oz, ow + 0.02, 0.006, oh + 0.02, (lit_slots or {}).get(number, GLASS))
        for s in (-1, 1):
            mesh.box(ou + s * (ow / 2 - 0.035), glass + 0.03, oz, 0.07, 0.08, oh, WOOD)
        for s in (-1, 1):
            mesh.box(ou, glass + 0.03, oz + s * (oh / 2 - 0.035), ow, 0.08, 0.07, WOOD)
        mesh.box(ou, glass + 0.04, oz, 0.034, 0.06, oh - 0.08, WOOD)
        mesh.box(ou, glass + 0.05, oz + rng.uniform(-0.09, 0.09), ow - 0.05, 0.07, 0.061, WOOD)
        if oh > 1.5:
            for dz in (-oh * 0.25, oh * 0.25):
                mesh.box(ou, glass + 0.035, oz + dz, ow - 0.07, 0.045, 0.026, WOOD)
    # doors: stone jambs and a lintel; a panelled door set back in the opening
    for du0, du1, dz0, dz1 in doors:
        ow, oh, ou = du1 - du0, dz1 - dz0, (du0 + du1) / 2
        if not wood:
            for s in (-1, 1):
                mesh.box(ou + s * (ow / 2 + 0.11), D - 0.02, (dz0 + dz1) / 2, 0.22, 0.32, dz1 - dz0 + 0.1, TRIM)
            mesh.box(ou, D - 0.01, dz1 + 0.13, ow + 0.5, 0.30, 0.22, TRIM)
        if fill:
            leaf = 0.06
            mesh.box(ou, leaf, (dz0 + dz1) / 2, ow + 0.02, 0.04, oh + 0.01, WOOD)
            stile, rail = min(0.13, ow * 0.16), 0.13
            for s in (-1, 1):
                mesh.box(ou + s * (ow / 2 - stile / 2), leaf + 0.035, (dz0 + dz1) / 2, stile, 0.03, oh, WOOD)
            for rz, rh in ((dz1 - rail / 2, rail), (dz0 + oh * 0.45, 0.17), (dz0 + 0.11, 0.22)):
                mesh.box(ou, leaf + 0.035, rz, ow - 2 * stile, 0.03, rh, WOOD)
            mesh.box(ou, leaf + 0.035, (dz0 + oh * 0.45 + dz1) / 2, 0.11, 0.03, dz1 - rail - dz0 - oh * 0.45, WOOD)   # muntin
            mesh.box(ou + ow / 2 - stile - 0.05, leaf + 0.07, dz0 + 1.0, 0.035, 0.05, 0.035, DARK)                  # knob
    # timber frames: a casing up both sides and a head over every opening, a sill under every window
    lying = (materials[6] if abs(side['along'].x) >= abs(side['along'].y) else materials[7]) if wood else None
    for zone in zones:
        _wood_frame(mesh, zone, D, materials[5], lying, frame_rng)
    # bands: plinth and below the cornice and the cornice; broken around openings; carried round closed corners
    if bands:
        for zz in (z0 + 0.25, z1 - 0.40, z1 - 0.15):
            if zz < z0 + 0.1 or zz > z1 - 0.05:
                continue
            crossing = [(a - 0.05, b + 0.05) for a, b, c, e, low, high in holes if c < zz + 0.1 and e > zz - 0.1]
            dark_crossing = crossing
            if wood:     # a band stops against a timber frame it meets (and its shadow under it too)
                crossing = [(f['A'] - 0.002, f['B'] + 0.002) for f in zones if f['low'] < zz + 0.065 + JOINT and f['high'] > zz - 0.065 - JOINT]
                dark_crossing = [(f['A'] - 0.002, f['B'] + 0.002) for f in zones if f['low'] < zz - 0.0675 + JOINT and f['high'] > zz - 0.1325 - JOINT]
            # a closed corner: this side's band runs out to the other side's band front (right end) or starts behind it (left)
            left = u0 - (D - 0.13 if shared['left'] else 0.07)
            right = u1 + (D + 0.17 if shared['right'] else 0.07)
            for p, q in _free_segments(left, right, crossing):
                mesh.span(p, q, D + 0.02, zz, 0.30, 0.13, TRIM)
            dark_left = u0 - (D - 0.155 if shared['left'] else 0.03)
            dark_right = u1 + (D + 0.075 if shared['right'] else 0.03)
            for p, q in _free_segments(dark_left, dark_right, dark_crossing):
                mesh.span(p, q, D - 0.04, zz - 0.10, 0.23, 0.065, DARK)
    # quoins: free ends get the bundle's alternating quoins; closed corners are wrapped, the sides taking turns
    if quoins:
        rows = int(math.ceil((z_end - z0) / 0.45))
        narrow = width < 1.0
        for q in range(rows):
            zz0 = z0 + q * 0.45 + 0.012
            zz1 = min(zz0 + 0.426, z_end)
            if zz1 - zz0 < 0.08:
                continue
            zz = (zz0 + zz1) / 2
            ends = []
            for end in ('left', 'right'):
                corner = u0 if end == 'left' else u1
                inward = 1 if end == 'left' else -1
                if shared[end]:
                    covering = (q % 2 == 0) == (end == 'right')
                    long_side = 0.45 if covering else 0.32
                    outer = corner - inward * (D + 0.08 if covering else D - 0.12)
                    inner = corner + inward * long_side
                    for a, b, c, e, low, high in (() if wood else holes):      # kept whole at the corner, shortened before an opening's dressings
                        if low - 0.05 < zz < high + 0.05:
                            edge = (a - 0.24) if inward > 0 else (b + 0.24)
                            if (inner - edge) * inward > 0:
                                inner = corner + inward * max(0.12, (edge - corner) * inward)
                    for f in zones:                            # or a joint short of a timber frame
                        if f['low'] - JOINT < zz1 and zz0 < f['high'] + JOINT:
                            edge = (f['A'] - JOINT) if inward > 0 else (f['B'] + JOINT)
                            if (inner - edge) * inward > 0:
                                inner = corner + inward * max(0.05, (edge - corner) * inward)
                    ends.append((min(outer, inner), max(outer, inner), end))
                    continue
                elif width > 2.0:
                    long_side = (0.32 if q % 2 else 0.45) * rng.uniform(0.88, 1.08)
                    middle = corner + inward * 0.16
                    outer, inner = middle - inward * long_side / 2, middle + inward * long_side / 2
                    if rng.random() < 0.07:
                        continue
                else:
                    continue
                if not wood and any(c - 0.05 < zz < e + 0.05 and a - 0.3 < (outer + inner) / 2 < b + 0.3 for a, b, c, e, low, high in holes):
                    continue
                if any(f['low'] - JOINT < zz1 and zz0 < f['high'] + JOINT and f['A'] - JOINT < max(outer, inner) and min(outer, inner) < f['B'] + JOINT for f in zones):
                    continue
                ends.append((min(outer, inner), max(outer, inner), end))
            if narrow and len(ends) == 2:
                ends = [(min(ends[0][0], ends[1][0]), max(ends[0][1], ends[1][1]), 'both')]
            for p, qq, _ in ends:
                mesh.span(p, qq, D - 0.02, zz, 0.20, zz1 - zz0, TRIM)
    return blocks


def _material(value):
    return store.material(value) if isinstance(value, str) else value


def _in_store(name):
    try:
        return name in store.names('materials')
    except Exception:
        return False


def turned_along(material, axis='x'):
    """For a photographed material whose picture runs one way (planks), a copy for the frame's lying members (heads, sills)
    with its picture turned a quarter round where that makes the grain run along a member lying along the world's X
    (axis 'x': the faces looking along Y) or Y (axis 'y': the faces looking along X and the tops); made once and kept
    ('<name> • along x' or '• along y'). A material with no picture to turn is given back as it is."""
    nodes = material.node_tree.nodes if material.node_tree else None
    pieces = nodes.get('Pieces') if nodes else None
    if pieces is None or 'Angle' not in pieces.outputs or 'Axis' not in pieces.outputs or not pieces.outputs['Angle'].is_linked:
        return material
    name = '%s • along %s' % (material.name, axis)
    found = bpy.data.materials.get(name)
    if found is not None:
        return found
    turned = material.copy()
    turned.name = name
    tree = turned.node_tree
    pieces = tree.nodes['Pieces']
    split = tree.nodes.new('ShaderNodeSeparateXYZ')                  # which way the face looks (Pieces gives it as 1 on one axis)
    split.location = (pieces.location.x + 180, pieces.location.y - 300)
    tree.links.new(pieces.outputs['Axis'], split.inputs[0])
    quarter = tree.nodes.new('ShaderNodeMath')
    quarter.operation = 'MULTIPLY_ADD'                               # x: Y * pi/2;  y: Y * -pi/2 + pi/2
    quarter.inputs[1].default_value = math.pi / 2 if axis == 'x' else -math.pi / 2
    quarter.inputs[2].default_value = 0.0 if axis == 'x' else math.pi / 2
    quarter.location = (pieces.location.x + 360, pieces.location.y - 300)
    tree.links.new(split.outputs['Y'], quarter.inputs[0])
    along = tree.nodes.new('ShaderNodeMath')
    along.name = along.label = 'Along'
    along.operation = 'ADD'
    along.location = (pieces.location.x + 540, pieces.location.y - 220)
    targets = [link.to_socket for link in tree.links if link.from_socket == pieces.outputs['Angle']]
    tree.links.new(pieces.outputs['Angle'], along.inputs[0])
    tree.links.new(quarter.outputs[0], along.inputs[1])
    for socket in targets:
        tree.links.new(along.outputs[0], socket)
    return turned


def lay(wall, openings=(), seed=0, sides='all', collection=None, shades=None, trim_material=None,
        dark_material=DARK_MATERIAL, wood_material=WOOD_MATERIAL, glass_material=GLASS_MATERIAL,
        mortar_material=MORTAR_MATERIAL, bands=True, quoins=True, fill=True, relief=0.20,
        frames='wood', frame_material=FRAME_MATERIAL, lit=None, lit_materials=None):
    """Build the wall's sides in ashlar. Returns the object 'stonework' (its counts in obj['blocks'], obj['sides'])."""
    if wall is None or wall.type != 'MESH':
        raise ValueError('lay_stone needs a mesh object (the wall)')
    if not isinstance(frames, str) or frames not in FRAMES:
        raise ValueError("frames is 'wood' (painted timber frames round the openings) or 'stone' (stone jambs, lintels and sills), not %r" % (frames,))
    bpy.context.view_layer.update()
    rng = random.Random(seed)
    wanted = None if sides == 'all' else {SIDE_NAMES.get(s, s) for s in sides}
    built = [s for s in upright_sides(wall) if wanted is None or s['name'] in wanted]
    if not built:
        raise ValueError('no upright side of %r to build (sides=%r)' % (wall.name, sides))
    shared = corners_shared(built)
    every_opening = read_openings(openings)
    known = {s['name'] for s in built}
    for o in every_opening:
        if o['side'] not in known:
            raise ValueError('an opening is on side %r, which is not built (built: %s)' % (o['side'], ', '.join(sorted(known))))
    photographed = _in_store(PHOTO_STONE)                  # until the store holds it, the old painted sandstone
    if not shades:
        shades = PHOTO_SHADES if photographed else SHADES
    if trim_material is None:
        trim_material = PHOTO_STONE if photographed else TRIM_MATERIAL
    shade_materials = [_material(m) for m in shades]
    material_list = shade_materials + [_material(m) for m in (trim_material, dark_material, wood_material, glass_material)]
    slots = (len(shade_materials), len(shade_materials), len(shade_materials) + 1, len(shade_materials) + 2, len(shade_materials) + 3)
    if frames == 'wood':       # the frames' upright members, and their lying ones (the picture turned to run along them)
        frame = _material(frame_material)
        material_list += [frame, turned_along(frame, 'x'), turned_along(frame, 'y')]
        slots += (len(shade_materials) + 4, len(shade_materials) + 5, len(shade_materials) + 6)
    glowing = lit_windows(every_opening, lit, seed, len(lit_materials or LIT_MATERIALS))
    lit_slots = {}
    if glowing:                # the lit windows' glass, after every other material
        first = len(material_list)
        material_list += [_material(m) for m in (lit_materials or LIT_MATERIALS)]
        lit_slots = {number: first + k for number, k in glowing.items()}
    frame_rng = random.Random(seed * 104729 + 71)          # the frames' own stream: their sizes, wear and lean
    mesh = FacadeMesh(seed)
    blocks = 0
    for index, side in enumerate(built):
        mine = [o for o in every_opening if o['side'] == side['name']]
        blocks += build_side(mesh, side, mine, shared[id(side)], rng, index, slots, bands=bands, quoins=quoins, fill=fill, relief=relief,
                             frames=frames, frame_rng=frame_rng, lit_slots=lit_slots)
    if collection is None:
        collection = bpy.data.collections.new('lay_stone')
        bpy.context.scene.collection.children.link(collection)
    stonework = mesh.make('stonework', material_list, collection)
    foot = min(s['z0'] for s in built)
    store.mark(stonework, ground=foot)
    stonework['blocks'] = blocks
    stonework['sides'] = ', '.join(s['name'] for s in built)
    stonework['openings'] = len(every_opening)
    stonework['frames'] = frames
    stonework['lit'] = ', '.join(str(n) for n in sorted(glowing))
    if mortar_material is not None:
        store.use_material(wall, _material(mortar_material), ground=foot)
    wall['stone_front'] = relief
    return stonework


def main(argv=None):
    argv = sys.argv[sys.argv.index('--') + 1:] if argv is None and '--' in sys.argv else (argv if argv is not None else sys.argv[1:])
    parser = argparse.ArgumentParser(description=TOOL['what'] + '. Trap: ' + TOOL['trap'] + '.')
    parser.add_argument('--blend', help='the .blend file to open')
    parser.add_argument('--object', help='the wall object')
    parser.add_argument('--out', help='where to save the result (.blend)')
    parser.add_argument('--opening', action='append', default=[],
                        help='"side kind left bottom width height", e.g. "front window 1.8 1.0 0.8 1.0" (repeat for more)')
    parser.add_argument('--seed', type=int, default=0, help="the blocks' sizes, chips and shades; default 0")
    parser.add_argument('--sides', default='all', help="'all' or a comma list like front,+x; default all")
    parser.add_argument('--no-bands', action='store_true', help='no plinth band or cornice')
    parser.add_argument('--no-quoins', action='store_true', help='no quoins at the corners')
    parser.add_argument('--no-fill', action='store_true', help='leave the openings empty (no glass, no door)')
    parser.add_argument('--relief', type=float, default=0.20, help="metres the blocks' faces stand out from the wall; default 0.20")
    parser.add_argument('--mortar-material', default=MORTAR_MATERIAL, help="the wall's new material; 'none' leaves it")
    parser.add_argument('--frames', default='wood', choices=FRAMES,
                        help="'wood': painted timber frames round the openings (casings, a head, a sill under each window); 'stone': the old stone jambs, lintels and sills; default wood")
    parser.add_argument('--frame-material', default=FRAME_MATERIAL, help="the timber frames' material; default '%s'" % FRAME_MATERIAL)
    parser.add_argument('--lit', default=None, help="windows that glow: their places in the openings, e.g. 1,3 (0 is the first --opening), or a share like 0.3; default none")
    args = parser.parse_args(argv)
    if not (args.blend and args.object and args.out):
        parser.error('--blend, --object and --out are needed to build a wall')
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
    sides = 'all' if args.sides == 'all' else [s.strip() for s in args.sides.split(',')]
    made = lay(wall, openings=openings, seed=args.seed, sides=sides, bands=not args.no_bands, quoins=not args.no_quoins,
               fill=not args.no_fill, relief=args.relief, mortar_material=None if args.mortar_material.lower() == 'none' else args.mortar_material,
               frames=args.frames, frame_material=args.frame_material,
               lit=None if args.lit is None else (float(args.lit) if '.' in args.lit else [int(n) for n in args.lit.split(',')]))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.out))
    print('%s: %d blocks on sides %s, saved %s' % (made.name, made['blocks'], made['sides'], args.out))


if __name__ == '__main__':
    main()
