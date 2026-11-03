"""
What this file does: turns a plain stone wall object you name (a box) into a built one, the street bundle's way: every
side you choose is covered in courses of ashlar blocks standing out in relief, each block its own chipped eight-sided
outline and its own sandstone shade, with dark joints between them; around the windows and doors you give it the courses
stop and the openings get stone jambs, a lintel above and, for a window, a deep sill with a dark drip line under it and a
timber sash with glazing bars set back in the reveal. Bands (plinth, cornice) and heavy quoins at the corners are on by
default; corners where two built sides meet are wrapped by quoins that alternate from side to side. The wall itself
becomes the dark mortar seen in the joints. Nothing is moved or cut and nothing is placed anywhere you did not say.

From your own Blender script:

    import sys
    sys.path.insert(0, FOLDER + '/store/tools')       # FOLDER is your copy of the brief folder
    import lay_stone
    stonework = lay_stone.lay(my_wall, openings=[
        ('front', 'door',   0.4, 0.0, 0.9, 2.0),      # side, kind, from the side's left end, from its foot, width, height (m)
        ('front', 'window', 1.8, 1.0, 0.8, 1.0),
    ], seed=2)
    import store
    store.fit_stone_pictures(bpy.context.scene)       # once, when the place is built, before drawing

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
    shades          the blocks' materials, one picked per block; default the twelve 'Hand-painted sandstone • shade NN'
    trim_material   jambs, lintels, sills, bands, quoins; default 'STONE • worn honey-grey architectural dressings'
    dark_material   drip lines and band shadows; default 'RECESSES • near-black blue'
    wood_material   sashes and doors; default 'WOOD • peeling dark painted doors'
    glass_material  window glass; default 'GLASS • sleeping navy interiors'
    mortar_material the wall becomes this, seen in the joints; default 'MORTAR • dark eroded joints' (None: leave it)
    bands           a plinth band at the foot and a cornice under the top; default True
    quoins          heavy dressed stones at the corners; default True
    fill            glass in each window and a panelled door in each door (False: leave the openings for your own); default True
    relief          how far the blocks' faces stand out from the wall face, metres; default 0.20

The blocks' faces stand 0.20 m in front of the wall's face (the jambs, sills and bands further), so pipes or lamps fixed
to the wall belong 0.2 m further out. Every block writes the number 'stone_patch' (one per stone), which the stone_grain
tool reads so each block shows its own patch of grain.
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

SHADES = ['Hand-painted sandstone • shade %02d' % i for i in range(12)]
TRIM_MATERIAL = 'STONE • worn honey-grey architectural dressings'
DARK_MATERIAL = 'RECESSES • near-black blue'
WOOD_MATERIAL = 'WOOD • peeling dark painted doors'
GLASS_MATERIAL = 'GLASS • sleeping navy interiors'
MORTAR_MATERIAL = 'MORTAR • dark eroded joints'
SIDE_NAMES = {'front': '-y', 'back': '+y', 'right': '+x', 'left': '-x'}

TOOL = {
    'name': 'lay_stone',
    'what': 'builds a plain stone wall you name into ashlar courses in relief, with jambs, lintels, sills and sashes round the openings you give',
    'call': "lay_stone.lay(wall, openings=[('front', 'window', 1.8, 1.0, 0.8, 1.0), ('front', 'door', 0.4, 0.0, 0.9, 2.0)], seed=2)",
    'options': {
        'openings': "(side, 'window' or 'door', from the side's left end, from its foot, width, height) in metres; sides '-y'/'front', '+y'/'back', '+x'/'right', '-x'/'left'",
        'seed': "the blocks' sizes, chips and shades; default 0",
        'sides': "which sides to build: 'all' or a list like ['front', '+x']; default 'all'",
        'collection': "where 'stonework' goes; default a new collection 'lay_stone'",
        'shades': "blocks' materials, one picked per block; default the twelve 'Hand-painted sandstone • shade NN'",
        'trim_material': "jambs, lintels, sills, bands, quoins; default '%s'" % TRIM_MATERIAL,
        'dark_material': "drip lines, band shadows; default '%s'" % DARK_MATERIAL,
        'wood_material': "sashes, doors; default '%s'" % WOOD_MATERIAL,
        'glass_material': "window glass; default '%s'" % GLASS_MATERIAL,
        'mortar_material': "the wall becomes this, seen in the joints; default '%s' (None leaves it)" % MORTAR_MATERIAL,
        'bands': 'a plinth band at the foot and a cornice under the top; default True',
        'quoins': 'heavy dressed stones at the corners; default True',
        'fill': 'glass in each window and a panelled door in each door; default True',
        'relief': "metres the blocks' faces stand out from the wall face; default 0.20",
    },
    'materials': SHADES + [TRIM_MATERIAL, DARK_MATERIAL, WOOD_MATERIAL, GLASS_MATERIAL, MORTAR_MATERIAL],
    'source': 'plugins/painted-place/materials/lay_facade.py: FacadeMesh, build_face, _free_segments (and oriented_faces)',
    'trap': 'the sandstone materials project one big picture over the place: call store.fit_stone_pictures(scene) once before drawing',
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
    for item in openings or ():
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
        result.append({'side': side, 'kind': kind, 'left': float(left), 'bottom': float(bottom), 'width': float(width), 'height': float(height)})
    return result


# ----------------------------------------------------------------------------------------------- the mesh

class FacadeMesh:
    """Vertices, faces, material slots and a number per stone for one wall, in each side's own frame (u along, d out,
    z up), written in world space."""

    def __init__(self):
        self.verts, self.faces, self.materials, self.patches = [], [], [], []
        self.side = None

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

    def make(self, name, material_list, collection):
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(self.verts, [], self.faces)
        for material in material_list:
            mesh.materials.append(material)
        for polygon, index in zip(mesh.polygons, self.materials):
            polygon.material_index = index
        attribute = mesh.attributes.new('stone_patch', 'FLOAT', 'FACE')
        attribute.data.foreach_set('value', self.patches)
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


def build_side(mesh, side, openings, shared, rng, index, materials, bands=True, quoins=True, fill=True, relief=0.20):
    """Ashlar, dressings, sashes and fills for one side. Returns the number of blocks."""
    SHADE_COUNT, TRIM, DARK, WOOD, GLASS = materials
    D = relief
    mesh.side = side
    u0, u1, z0, z1 = side['u0'], side['u1'], side['z0'], side['z1']
    width = u1 - u0
    holes, windows, doors = [], [], []
    for o in openings:
        a = u0 + o['left']
        b, c = a + o['width'], z0 + o['bottom']
        e = c + o['height']
        if o['kind'] == 'window':
            if not (0.3 <= b - a <= 4 and 0.3 <= e - c <= 4):
                continue
            windows.append((a, b, c, e))
            holes.append((a, b, c, e, c - 0.17, e + 0.19))           # the opening, and its dressings' bottom and top
        else:
            doors.append((a, b, c, e))
            holes.append((a, b, c, e, c, e + 0.24))
    blocks = 0
    course = 0.32 if index % 2 == 0 else 0.38
    z_end = z1 - 0.14 if bands else z1
    for z, h in _course_heights(z0, z_end, course, rng):
        zmid = z + h / 2
        cutting = [(a, b, low, high) for a, b, c, e, low, high in holes if z < e + 0.05 and z + h > c - 0.05]
        in_course = [(a - 0.06, b + 0.06) for a, b, low, high in cutting]
        u = u0 - rng.uniform(0, 0.4)
        while u < u1:
            w = rng.uniform(0.46, 0.94)
            lo, hi = max(u, u0), min(u + w, u1)
            # a block that meets an opening is cut back to the opening's edge, so stone runs right up to every reveal
            for p, q in _free_segments(lo, hi, in_course, minimum=0.12):
                front = D - 0.08 + rng.uniform(-0.018, 0.018)
                shade = rng.randrange(SHADE_COUNT) if rng.random() > 0.05 else TRIM
                mesh.block((p + q) / 2, front, zmid, q - p - 0.016, 0.16 + rng.uniform(-0.03, 0.02), h - 0.015, shade, rng)
                blocks += 1
            u += w
        # where the cut course reaches above a lintel or below a sill, stone fills the rest of the course
        for a, b, low, high in cutting:
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
    for wu0, wu1, wz0, wz1 in windows:
        ow, oh = wu1 - wu0, wz1 - wz0
        ou, oz = (wu0 + wu1) / 2, (wz0 + wz1) / 2
        trim_width = rng.uniform(0.105, 0.145)
        for s in (-1, 1):
            mesh.box(ou + s * (ow / 2 + 0.07), D - 0.02, oz, trim_width, 0.18, oh + 0.25, TRIM if rng.random() > 0.14 else rng.randrange(SHADE_COUNT))
        mesh.box(ou, D - 0.01, oz + oh / 2 + 0.11, ow + 0.32, 0.24, 0.16, TRIM)
        mesh.box(ou, D + 0.04, oz - oh / 2 - 0.10, ow + 0.36, 0.34, 0.14, TRIM)
        mesh.box(ou, D - 0.06, oz - oh / 2 - 0.22, ow + 0.13, 0.19, 0.11, DARK)
        glass = D - 0.10
        if fill:
            mesh.box(ou, glass + 0.015, oz, ow + 0.02, 0.006, oh + 0.02, GLASS)
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
    # bands: plinth and below the cornice and the cornice; broken around openings; carried round closed corners
    if bands:
        for zz in (z0 + 0.25, z1 - 0.40, z1 - 0.15):
            if zz < z0 + 0.1 or zz > z1 - 0.05:
                continue
            crossing = [(a - 0.05, b + 0.05) for a, b, c, e, low, high in holes if c < zz + 0.1 and e > zz - 0.1]
            # a closed corner: this side's band runs out to the other side's band front (right end) or starts behind it (left)
            left = u0 - (D - 0.13 if shared['left'] else 0.07)
            right = u1 + (D + 0.17 if shared['right'] else 0.07)
            for p, q in _free_segments(left, right, crossing):
                mesh.span(p, q, D + 0.02, zz, 0.30, 0.13, TRIM)
            dark_left = u0 - (D - 0.155 if shared['left'] else 0.03)
            dark_right = u1 + (D + 0.075 if shared['right'] else 0.03)
            for p, q in _free_segments(dark_left, dark_right, crossing):
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
                    for a, b, c, e, low, high in holes:      # kept whole at the corner, shortened before an opening's dressings
                        if low - 0.05 < zz < high + 0.05:
                            edge = (a - 0.24) if inward > 0 else (b + 0.24)
                            if (inner - edge) * inward > 0:
                                inner = corner + inward * max(0.12, (edge - corner) * inward)
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
                if any(c - 0.05 < zz < e + 0.05 and a - 0.3 < (outer + inner) / 2 < b + 0.3 for a, b, c, e, low, high in holes):
                    continue
                ends.append((min(outer, inner), max(outer, inner), end))
            if narrow and len(ends) == 2:
                ends = [(min(ends[0][0], ends[1][0]), max(ends[0][1], ends[1][1]), 'both')]
            for p, qq, _ in ends:
                mesh.span(p, qq, D - 0.02, zz, 0.20, zz1 - zz0, TRIM)
    return blocks


def _material(value):
    return store.material(value) if isinstance(value, str) else value


def lay(wall, openings=(), seed=0, sides='all', collection=None, shades=None, trim_material=TRIM_MATERIAL,
        dark_material=DARK_MATERIAL, wood_material=WOOD_MATERIAL, glass_material=GLASS_MATERIAL,
        mortar_material=MORTAR_MATERIAL, bands=True, quoins=True, fill=True, relief=0.20):
    """Build the wall's sides in ashlar. Returns the object 'stonework' (its counts in obj['blocks'], obj['sides'])."""
    if wall is None or wall.type != 'MESH':
        raise ValueError('lay_stone needs a mesh object (the wall)')
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
    shade_materials = [_material(m) for m in (shades or SHADES)]
    material_list = shade_materials + [_material(m) for m in (trim_material, dark_material, wood_material, glass_material)]
    slots = (len(shade_materials), len(shade_materials), len(shade_materials) + 1, len(shade_materials) + 2, len(shade_materials) + 3)
    mesh = FacadeMesh()
    blocks = 0
    for index, side in enumerate(built):
        mine = [o for o in every_opening if o['side'] == side['name']]
        blocks += build_side(mesh, side, mine, shared[id(side)], rng, index, slots, bands=bands, quoins=quoins, fill=fill, relief=relief)
    if collection is None:
        collection = bpy.data.collections.new('lay_stone')
        bpy.context.scene.collection.children.link(collection)
    stonework = mesh.make('stonework', material_list, collection)
    foot = min(s['z0'] for s in built)
    store.mark(stonework, ground=foot)
    stonework['blocks'] = blocks
    stonework['sides'] = ', '.join(s['name'] for s in built)
    stonework['openings'] = len(every_opening)
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
               fill=not args.no_fill, relief=args.relief, mortar_material=None if args.mortar_material.lower() == 'none' else args.mortar_material)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.out))
    print('%s: %d blocks on sides %s, saved %s' % (made.name, made['blocks'], made['sides'], args.out))


if __name__ == '__main__':
    main()
