"""
What this file does: clads a plain box-like timber wall or hut object you name in real lapped weatherboards, so it stops
looking like a box with a picture of planks on it ("looks like cardboard"): every side you choose gets overlapping boards
with real thickness (each lower edge standing proud and throwing a shadow line), staggered butt joints, a shade per
board, nail lines where the studs are (a few bleeding rust), corner boards wrapping each corner, and painted casings,
a drip cap and a sill round the windows and doors you give it, with a sash and glass in each window and a ledged plank
door in each door. With `eaves` it also puts a roof over the box: overhanging every side (0.35 m by default), pitched
with the ridge along the long side or a lean-to, with fascia and barge boards, rafter tails and a boarded underside that
throws its shadow on the wall; the gable (or the lean-to's sides) is boarded up to the roof. Your hut itself becomes the
dark seen between boards. Nothing is moved or cut, and nothing is placed anywhere you did not say.

From your own Blender script:

    import sys
    sys.path.insert(0, FOLDER + '/store/tools')       # FOLDER is your copy of the brief folder
    import lay_boards
    made = lay_boards.lay(my_hut, openings=[
        ('front', 'door',   1.5, 0.0, 0.9, 1.95),     # side, kind, from the side's left end, from its foot, width, height (m)
        ('front', 'window', 0.4, 0.95, 0.7, 0.7),
        ('right', 'window', 1.1, 0.95, 0.8, 0.7),
    ], eaves='pitched', seed=4)
    made['boards'], made['roof']                      # the two objects made ('roof' is None without eaves)

    Sides are named by the way they face in the hut's own axes: '-y' (or 'front'), '+y' ('back'), '+x' ('right'),
    '-x' ('left'). "From the left end" is measured along the side as you see it standing outside, facing it.

From the command line:

    python3 lay_boards.py --help
    python3 lay_boards.py --blend IN.blend --object Hut --out OUT.blend --eaves pitched --opening "front door 1.5 0 0.9 1.95"

Options:
    openings        windows and doors, as (side, 'window' or 'door', left, bottom, width, height) or dicts with those keys
    seed            the boards' lengths, shades, joints and nails; default 0
    sides           which sides to clad: 'all' (every upright side) or a list like ['front', 'right']; default 'all'
    collection      where the objects go; default a new collection 'lay_boards'
    eaves           None (no roof), 'pitched' (ridge along the long side) or 'lean-to'; default None
    overhang        how far the roof reaches past the walls on every side, metres; default 0.35
    pitch           the roof's slope in degrees; default 22 (pitched) or 10 (lean-to)
    high_side       the lean-to's high side: 'back', 'front', 'left', 'right' (or '+y', '-y', '-x', '+x'); default 'back'
    roof_material   default 'SURFACE • rusty_corrugated_iron'
    boards_material default 'MADE • weathered boards, peeling paint' (reads 'board_tone', one shade per board)
    trim_material   casings and sashes; default 'WOOD • peeling dark painted doors' (fascia, barge boards and rafters are boards)
    iron_material   nail heads, the door latch; default 'IRON • soot-black lamp posts'
    rust_material   rust streaks under nails; default 'RUST • rain-aged iron'
    glass_material  window glass; default 'GLASS • sleeping navy interiors'
    backing_material your hut becomes this, the dark between boards; default 'RECESSES • near-black blue' (None: leave it)
    nails           nail lines on the studs; default True
    fill            glass and a sash in each window, a plank door in each door (False: leave them for your own); default True

The boards stand 0.008 to 0.03 m out from the hut's faces (corner boards and casings to 0.06 m). Every face of the
boards object carries the number 'board_tone' (0..1, one value per board) that the weathered-boards material reads.
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

BOARDS_MATERIAL = 'MADE • weathered boards, peeling paint'
TRIM_MATERIAL = 'WOOD • peeling dark painted doors'
IRON_MATERIAL = 'IRON • soot-black lamp posts'
RUST_MATERIAL = 'RUST • rain-aged iron'
GLASS_MATERIAL = 'GLASS • sleeping navy interiors'
BACKING_MATERIAL = 'RECESSES • near-black blue'
ROOF_MATERIAL = 'SURFACE • rusty_corrugated_iron'
SIDE_NAMES = {'front': '-y', 'back': '+y', 'right': '+x', 'left': '-x'}
BOARD, IRON, RUST, CASING, GLASS, BACKING = range(6)

TOOL = {
    'name': 'lay_boards',
    'what': 'clads a plain timber wall or hut you name in lapped weatherboards with casings round the openings you give; eaves add an overhanging roof',
    'call': "lay_boards.lay(hut, openings=[('front', 'door', 1.5, 0.0, 0.9, 1.95)], eaves='pitched', seed=4)",
    'options': {
        'openings': "(side, 'window' or 'door', from the side's left end, from its foot, width, height) in metres; sides '-y'/'front', '+y'/'back', '+x'/'right', '-x'/'left'",
        'seed': "the boards' lengths, shades, joints and nails; default 0",
        'sides': "which sides to clad: 'all' or a list like ['front', 'right']; default 'all'",
        'collection': "where the objects go; default a new collection 'lay_boards'",
        'eaves': "None (no roof), 'pitched' (ridge along the long side) or 'lean-to'; default None",
        'overhang': 'metres the roof reaches past the walls on every side; default 0.35',
        'pitch': 'roof slope in degrees; default 22 (pitched) or 10 (lean-to)',
        'high_side': "the lean-to's high side: 'back', 'front', 'left' or 'right'; default 'back'",
        'roof_material': "default '%s'" % ROOF_MATERIAL,
        'boards_material': "default '%s' (reads 'board_tone')" % BOARDS_MATERIAL,
        'trim_material': "casings and sashes; default '%s' (fascia, barge boards, rafters use boards_material)" % TRIM_MATERIAL,
        'iron_material': "nail heads, latch; default '%s'" % IRON_MATERIAL,
        'rust_material': "rust streaks; default '%s'" % RUST_MATERIAL,
        'glass_material': "window glass; default '%s'" % GLASS_MATERIAL,
        'backing_material': "the hut becomes this, seen between boards; default '%s' (None leaves it)" % BACKING_MATERIAL,
        'nails': 'nail lines on the studs; default True',
        'fill': 'glass and sash in windows, a plank door in doors; default True',
    },
    'materials': [BOARDS_MATERIAL, TRIM_MATERIAL, IRON_MATERIAL, RUST_MATERIAL, GLASS_MATERIAL, BACKING_MATERIAL, ROOF_MATERIAL],
    'source': 'plugins/painted-place/materials/lay_timber.py: BoardMesh, lap_face, _board_tone, vary_boards; lay_facade.py: window_joinery, _free_segments, oriented_faces',
    'trap': 'the boards stand out from the hut by up to 6 cm: things fixed to the wall (lamps, pipes) belong that much further out',
}


# ----------------------------------------------------------------------------------------------- the hut's sides

def _upper_chain(points):
    """The upper outline (u, z) of a convex polygon's points, from its leftmost to its rightmost point."""
    highest = {}
    for u, z in points:
        key = round(u, 6)
        highest[key] = max(highest.get(key, -1e9), round(z, 6))
    points = sorted(highest.items())
    upper = []
    for p in reversed(points):
        while len(upper) >= 2 and ((upper[-1][0] - upper[-2][0]) * (p[1] - upper[-2][1]) - (upper[-1][1] - upper[-2][1]) * (p[0] - upper[-2][0])) <= 0:
            upper.pop()
        upper.append(p)
    return list(reversed(upper))


def _side_name(hut, normal):
    local = hut.matrix_world.inverted().to_3x3() @ normal
    axis = 0 if abs(local.x) >= abs(local.y) else 1
    return ('+' if local[axis] > 0 else '-') + 'xy'[axis]


def upright_sides(hut, narrowest=0.05):
    """The hut's upright sides: name, origin (its middle at z = 0), normal (out), along (to the right seen from outside),
    u0, u1, z0, z1 and top (the upper outline as (u, z) points: a gable's peak is kept)."""
    matrix = hut.matrix_world
    found = []
    if len(hut.data.polygons) <= 12:
        normal_matrix = matrix.to_3x3().inverted_safe().transposed()
        for polygon in hut.data.polygons:
            normal = normal_matrix @ polygon.normal
            if normal.length < 1e-9 or abs(normal.normalized().z) >= 0.3:
                continue
            normal.z = 0.0
            found.append((normal.normalized(), [matrix @ hut.data.vertices[i].co for i in polygon.vertices]))
    else:
        corners = [Vector(c) for c in hut.bound_box]
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
        sides.append({'name': _side_name(hut, normal), 'origin': Vector((centre.x, centre.y, 0.0)), 'normal': normal, 'along': along,
                      'u0': min(us), 'u1': max(us), 'z0': min(zs), 'z1': max(zs), 'top': _upper_chain(list(zip(us, zs)))})
    return sides


def _end_point(side, which):
    return (side['origin'] + side['along'] * (side['u0'] if which == 'left' else side['u1'])).to_2d()


def corners_shared(sides):
    """For each side, whether another clad side meets it at its left and right ends."""
    shared = {id(s): {'left': False, 'right': False} for s in sides}
    for a in sides:
        for b in sides:
            if a is not b and abs(a['normal'].dot(b['normal'])) < 0.3 and (_end_point(a, 'right') - _end_point(b, 'left')).length < 0.03:
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


def _top_at(top, u):
    """Height of a side's upper outline at u (outline as (u, z) points)."""
    if u <= top[0][0]:
        return top[0][1]
    for (ua, za), (ub, zb) in zip(top, top[1:]):
        if u <= ub:
            return za + (zb - za) * (u - ua) / max(ub - ua, 1e-9)
    return top[-1][1]


def _runs_below(top, z, u0, u1, step=0.02):
    """Pieces of [u0, u1] where the outline stands at least 4 cm above z."""
    runs, start = [], None
    count = max(2, int(math.ceil((u1 - u0) / step)) + 1)
    for k in range(count):
        u = u0 + (u1 - u0) * k / (count - 1)
        inside = _top_at(top, u) - z >= 0.04
        if inside and start is None:
            start = u
        if not inside and start is not None:
            runs.append((start, u))
            start = None
    if start is not None:
        runs.append((start, u1))
    return runs


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


# ----------------------------------------------------------------------------------------------- the boards mesh

class BoardMesh:
    """Vertices, faces, material slots and a shade per face, built in each side's own frame (u along, d out, z up) and
    written in the frame of the object they go in."""

    def __init__(self, to_object):
        self.to_object = to_object
        self.side = None
        self.verts, self.faces, self.slots, self.tones = [], [], [], []
        self.facing = {}          # flat faces (no inside to point away from): which way they must face

    def point(self, u, d, z):
        p = self.side['origin'] + self.side['along'] * u + self.side['normal'] * d + Vector((0.0, 0.0, z))
        return tuple(self.to_object @ p)

    def solid(self, coords, slot, tone):
        """Eight corners: back-bottom-left, back-bottom-right, front-bottom-right, front-bottom-left, then the tops."""
        start = len(self.verts)
        self.verts.extend(self.point(*c) for c in coords)
        for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
            self.faces.append(tuple(start + i for i in f))
            self.slots.append(slot)
            self.tones.append(tone)

    def box(self, u, d, z, w, dep, h, slot, tone=0.5):
        x, y = w / 2, dep / 2
        self.solid([(u - x, d - y, z - h / 2), (u + x, d - y, z - h / 2), (u + x, d + y, z - h / 2), (u - x, d + y, z - h / 2),
                    (u - x, d - y, z + h / 2), (u + x, d - y, z + h / 2), (u + x, d + y, z + h / 2), (u - x, d + y, z + h / 2)], slot, tone)

    def flat(self, points, slot, tone=0.5):
        start = len(self.verts)
        self.verts.extend(self.point(*c) for c in points)
        self.facing[len(self.faces)] = (self.to_object.to_3x3() @ self.side['normal']).normalized()
        self.faces.append(tuple(range(start, start + len(points))))
        self.slots.append(slot)
        self.tones.append(tone)

    def make(self, name, materials, collection, location_matrix):
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(self.verts, [], self.faces)
        for material in materials:
            mesh.materials.append(material)
        for polygon, slot in zip(mesh.polygons, self.slots):
            polygon.material_index = slot
        attribute = mesh.attributes.new('board_tone', 'FLOAT', 'FACE')
        attribute.data.foreach_set('value', self.tones)
        tool = bmesh.new()
        tool.from_mesh(mesh)
        tool.faces.ensure_lookup_table()
        closed = [f for f in tool.faces if f.index not in self.facing]
        bmesh.ops.recalc_face_normals(tool, faces=closed)
        tool.normal_update()
        backwards = [tool.faces[i] for i, out in self.facing.items() if tool.faces[i].normal.dot(out) < 0]
        if backwards:
            bmesh.ops.reverse_faces(tool, faces=backwards)
        tool.to_mesh(mesh)
        tool.free()
        mesh.update()
        obj = bpy.data.objects.new(name, mesh)
        collection.objects.link(obj)
        obj.matrix_world = location_matrix
        return obj


def _board_tone(rng):
    roll = rng.random()
    if roll < 0.06:
        return rng.uniform(0.93, 1.0)       # a newer board put in
    if roll < 0.11:
        return rng.uniform(0.0, 0.08)       # a rotten, near-black one
    return rng.uniform(0.18, 0.8)


def window_joinery(box, window, front, rng, *, casing=True, sill=True, sash=True, CASING=CASING, DARK=BACKING):
    """Joinery for one window in the side's own frame (u along, d out, z up). `box(u, d, z, w, depth, h, slot)` adds a
    block; `front` is how far the glass stands out from the face. A painted casing round the opening, a sill with the
    dark line of its drip under it, and a sash: its frame, glazing bars cutting the glass into panes about 0.45 m wide
    and 0.5 m tall, and a meeting rail when the window is a sash window's shape. Returns the number of blocks added."""
    wu0, wu1, wz0, wz1 = window
    ow, oh = wu1 - wu0, wz1 - wz0
    ou, oz = (wu0 + wu1) / 2, (wz0 + wz1) / 2
    proud = max(0.045, front + 0.06)
    blocks = 0
    casing_width = rng.uniform(0.085, 0.115) if casing else 0.0
    if casing:
        for s in (-1, 1):
            box(ou + s * (ow / 2 + casing_width / 2), proud / 2, oz, casing_width, proud, oh, CASING)
        head = casing_width * 1.3
        box(ou, (proud + 0.012) / 2, wz1 + head / 2, ow + 2 * casing_width + 0.04, proud + 0.012, head, CASING)
        blocks += 3
    if sill:
        sill_width = ow + 2 * casing_width + 0.10
        box(ou, (proud + 0.06) / 2, wz0 - 0.03, sill_width, proud + 0.06, 0.06, CASING)
        box(ou, 0.015, wz0 - 0.072, sill_width - 0.06, 0.03, 0.018, DARK)
        blocks += 2
    if sash:
        bar, glazing, depth = 0.05, 0.026, 0.04
        d = front + 0.002 + depth / 2
        for s in (-1, 1):
            box(ou + s * (ow / 2 - bar / 2), d, oz, bar, depth, oh, CASING)
            box(ou, d, oz + s * (oh / 2 - bar / 2), ow, depth, bar, CASING)
        inner_w, inner_h = ow - 2 * bar, oh - 2 * bar
        columns = max(1, round(inner_w / 0.45))
        rows = max(1, round(inner_h / 0.5))
        sash_shape = oh > 0.9 and ow <= 1.6
        if sash_shape and rows % 2:
            rows += 1
        for k in range(1, columns):
            box(wu0 + bar + k * inner_w / columns, d + 0.002, oz, glazing, depth - 0.01, inner_h, CASING)
        for k in range(1, rows):
            z = wz0 + bar + k * inner_h / rows
            if sash_shape and 2 * k == rows:
                box(ou, d + 0.004, z + rng.uniform(-0.02, 0.02), inner_w, depth + 0.008, 0.05, CASING)
            else:
                box(ou, d + 0.002, z, inner_w, depth - 0.01, glazing, CASING)
        blocks += 4 + (columns - 1) + (rows - 1)
    return blocks


def lap_side(mesh, side, openings, shared, rng, nails=True, fill=True):
    """Overlapping boards up one side, stopping at its openings and at its upper outline, with casings, corner boards,
    nails and the openings' fills. Returns counts."""
    mesh.side = side
    u0, u1, z0 = side['u0'], side['u1'], side['z0']
    top = side['top']
    peak = max(z for _, z in top)
    apex = [u for u, z in top if abs(z - peak) < 1e-6]
    flat_top = peak - min(z for _, z in top) < 1e-4
    apex_u = apex[len(apex) // 2] if len(top) > 2 and not flat_top else None
    counts = {'boards': 0, 'nails': 0, 'rust streaks': 0, 'windows': 0, 'doors': 0}
    windows, doors, holes = [], [], []
    for o in openings:
        a = u0 + o['left']
        b, c = a + o['width'], z0 + o['bottom']
        e = c + o['height']
        (windows if o['kind'] == 'window' else doors).append((a, b, c, e))
        holes.append((a, b, c, e))
    width = u1 - u0
    if width < 0.35:
        # a narrow end (a thin wall's edge): one upright board covers it, wrapping both corners
        z_top = min(_top_at(top, u0), _top_at(top, u1))
        lo = u0 - (0.024 if shared['left'] else 0.0)
        hi = u1 + (0.056 if shared['right'] else 0.0)
        mesh.box((lo + hi) / 2, 0.04, (z0 + z_top) / 2, hi - lo, 0.032, z_top - z0, BOARD, _board_tone(rng))
        counts['boards'] += 1
        return counts
    exposure = rng.uniform(0.165, 0.215)
    z = z0 + 0.01
    while z < peak - 0.04:
        h = min(exposure, peak - z)
        top_edge = z + h + 0.03
        in_course = [(a - 0.01, b + 0.01) for a, b, c, e in holes if z < e and z + h > c]
        u = u0 - rng.uniform(0.0, 2.4)
        while u < u1:
            length = rng.uniform(1.8, 4.2)
            lo, hi = max(u, u0), min(u + length, u1)
            u += length
            if hi - lo < 0.08:
                continue
            for run_lo, run_hi in _runs_below(top, z, lo, hi):
                pieces = _free_segments(run_lo, run_hi, in_course, 0.08)
                if apex_u is not None:      # a gable board is cut at the peak, so each half follows its own slope
                    pieces = [piece for p, q in pieces for piece in ([(p, apex_u), (apex_u, q)] if p + 0.05 < apex_u < q - 0.05 else [(p, q)])]
                for p, q in pieces:
                    p, q = p + 0.002, q - 0.002
                    tone = _board_tone(rng)
                    proud = rng.uniform(-0.003, 0.004)
                    twist = rng.uniform(-0.003, 0.003)
                    b0, b1 = 0.024 + proud, 0.024 + proud + twist      # bottom edge out from the wall, each end
                    t0, t1 = 0.008 + proud * 0.5, 0.008 + proud * 0.5 + twist * 0.5
                    top_p, top_q = min(top_edge, _top_at(top, p)), min(top_edge, _top_at(top, q))
                    if min(top_p, top_q) - z < 0.02:
                        continue
                    mesh.solid([(p, 0.002, z), (q, 0.002, z), (q, b1, z), (p, b0, z),
                                (p, 0.002, top_p), (q, 0.002, top_q), (q, t1, top_q), (p, t0, top_p)], BOARD, tone)
                    counts['boards'] += 1
                    if not nails:
                        continue
                    stud = math.ceil((p - u0) / 0.6) * 0.6 + u0
                    while stud < q - 0.03:
                        if stud > p + 0.03 and z + 0.04 < min(top_p, top_q):
                            mesh.box(stud, b0 + 0.002, z + 0.028, 0.011, 0.006, 0.011, IRON)
                            counts['nails'] += 1
                            if rng.random() < 0.16:
                                long = rng.uniform(0.05, 0.28)
                                w = rng.uniform(0.008, 0.016)
                                # the streak runs down this board's foot, then down the face of the board below it
                                below = z - long
                                mesh.flat([(stud - w * 0.3, b0 + 0.0015, z + 0.024), (stud - w / 2, b0 + 0.0015, z + 0.001),
                                           (stud + w / 2, b0 + 0.0015, z + 0.001), (stud + w * 0.3, b0 + 0.0015, z + 0.024)], RUST)
                                if below < z - 0.01 and below > z0:
                                    slope = (0.024 - 0.008) / (exposure + 0.03)
                                    near = 0.008 + slope * 0.03 + 0.0015
                                    far = 0.008 + slope * min(0.03 + long, exposure + 0.03) + 0.0015
                                    mesh.flat([(stud - w / 2, near, z - 0.001), (stud - w * 0.35, far, below),
                                               (stud + w * 0.35, far, below), (stud + w / 2, near, z - 0.001)], RUST)
                                counts['rust streaks'] += 1
                        stud += 0.6
        z += h
    # casings round windows and doors; a drip cap over each window; a sill board under it
    for wu0, wu1, wz0, wz1 in windows:
        for side_u in (wu0 - 0.045, wu1 + 0.045):
            mesh.box(side_u, 0.042, (wz0 + wz1) / 2, 0.09, 0.03, wz1 - wz0 + 0.18, CASING)
        mesh.box((wu0 + wu1) / 2, 0.042, wz1 + 0.045, wu1 - wu0 + 0.18, 0.03, 0.09, CASING)
        mesh.box((wu0 + wu1) / 2, 0.06, wz1 + 0.10, wu1 - wu0 + 0.24, 0.07, 0.025, CASING)
        mesh.box((wu0 + wu1) / 2, 0.06, wz0 - 0.03, wu1 - wu0 + 0.26, 0.09, 0.035, CASING)
        if fill:
            mesh.box((wu0 + wu1) / 2, 0.006, (wz0 + wz1) / 2, wu1 - wu0 + 0.02, 0.006, wz1 - wz0 + 0.02, GLASS)
            window_joinery(lambda u, d, zz, w, depth, hh, slot: mesh.box(u, d, zz, w, depth, hh, slot), (wu0, wu1, wz0, wz1), 0.009, rng,
                           casing=False, sill=False, sash=True)
        counts['windows'] += 1
    for du0, du1, dz0, dz1 in doors:
        for side_u in (du0 - 0.05, du1 + 0.05):
            mesh.box(side_u, 0.042, (dz0 + dz1) / 2, 0.10, 0.03, dz1 - dz0, CASING)
        mesh.box((du0 + du1) / 2, 0.042, dz1 + 0.05, du1 - du0 + 0.20, 0.03, 0.10, CASING)
        if fill:
            # a ledged and braced door of upright planks, its ledges and brace outside, an iron latch
            planks = max(3, int(round((du1 - du0) / 0.14)))
            plank = (du1 - du0) / planks
            for k in range(planks):
                pu = du0 + (k + 0.5) * plank
                mesh.box(pu, 0.018, (dz0 + dz1) / 2 + 0.005, plank - 0.005, 0.024, dz1 - dz0 - 0.01, BOARD, _board_tone(rng))
            ledges = (dz0 + 0.25, (dz0 + dz1) / 2, dz1 - 0.25)
            for lz in ledges:
                mesh.box((du0 + du1) / 2, 0.042, lz, du1 - du0 - 0.08, 0.024, 0.12, BOARD, _board_tone(rng))
            for (za, zb) in ((ledges[0] + 0.06, ledges[1] - 0.06), (ledges[1] + 0.06, ledges[2] - 0.06)):
                ua, ub = du0 + 0.07, du1 - 0.07
                rise, run = zb - za, ub - ua
                half = 0.05 * math.hypot(rise, run) / max(run, 1e-6)
                mesh.solid([(ua, 0.030, za - half), (ub, 0.030, zb - half), (ub, 0.054, zb - half), (ua, 0.054, za - half),
                            (ua, 0.030, za + half), (ub, 0.030, zb + half), (ub, 0.054, zb + half), (ua, 0.054, za + half)], BOARD, _board_tone(rng))
            mesh.box(du1 - 0.12, 0.06, dz0 + 1.0, 0.16, 0.012, 0.025, IRON)
            mesh.box(du1 - 0.06, 0.07, dz0 + 1.0, 0.03, 0.03, 0.05, IRON)
        counts['doors'] += 1
    # corner boards: wrapping each closed corner (the right one runs past it), a plain one where the wall ends free
    for end in ('left', 'right'):
        corner = u0 if end == 'left' else u1
        z_top = _top_at(top, corner)
        if shared[end]:
            lo, hi = (corner - 0.024, corner + 0.10) if end == 'left' else (corner - 0.10, corner + 0.056)
        else:
            middle = corner + (0.05 if end == 'left' else -0.05)
            if any(a - 0.1 < middle < b + 0.1 for a, b, c, e in holes):
                continue
            lo, hi = middle - 0.05, middle + 0.05
        mesh.box((lo + hi) / 2, 0.04, (z0 + z_top) / 2, hi - lo, 0.032, z_top - z0, BOARD, _board_tone(rng))
        counts['boards'] += 1
    return counts


def _backing(mesh, side, box_top):
    """Where a side reaches above the hut's own top (a gable, a lean-to's high side), a dark sheet behind its boards."""
    top = side['top']
    if max(z for _, z in top) <= box_top + 0.01:
        return 0
    us = sorted(set([side['u0'], side['u1']] + [u for u, _ in top]))
    points = [(u, 0.0, box_top) for u in us] + [(u, 0.0, max(box_top, _top_at(top, u))) for u in reversed(us)]
    mesh.flat(points, BACKING)
    return 1


# ----------------------------------------------------------------------------------------------- the roof

def _roof(hut_frame, size_x, size_y, centre, box_top, kind, overhang, pitch, high_side, rng):
    """Roof parts in a frame where the ridge (or the lean-to's slope across) runs along x: returns the roof's own frame
    matrix, its parts as (verts, faces, slots, tones), and a function giving the underside height over a point of the hut."""
    ridge_along_x = size_x >= size_y
    if kind == 'lean-to':
        name = SIDE_NAMES.get(high_side, high_side)
        if name not in ('+x', '-x', '+y', '-y'):
            raise ValueError("high_side is 'back', 'front', 'left' or 'right'")
        ridge_along_x = name in ('+y', '-y')              # the slope runs across to the high side
        flip = name in ('-y', '+x')
    else:
        flip = False
    length, span = (size_x, size_y) if ridge_along_x else (size_y, size_x)
    turn = Matrix.Identity(4) if ridge_along_x else Matrix.Rotation(math.pi / 2, 4, 'Z')
    if flip:
        turn = turn @ Matrix.Rotation(math.pi, 4, 'Z')
    frame = hut_frame @ Matrix.Translation(Vector((centre.x, centre.y, 0.0))) @ turn
    s, o, t = span / 2, overhang, 0.05
    slope = math.tan(math.radians(pitch))
    lift = t / math.cos(math.radians(pitch))
    x0, x1 = -length / 2 - o, length / 2 + o
    verts, faces, slots, tones = [], [], [], []

    def prism(section, x_low, x_high, section_slots, cap_slot, tone=0.5):
        """A section (y, z points, counter-clockwise seen from +x) run along x from x_low to x_high."""
        start = len(verts)
        n = len(section)
        verts.extend((x_low, y, z) for y, z in section)
        verts.extend((x_high, y, z) for y, z in section)
        faces.append(tuple(start + i for i in reversed(range(n))))
        faces.append(tuple(start + n + i for i in range(n)))
        slots.extend([cap_slot, cap_slot])
        tones.extend([tone, tone])
        for i in range(n):
            j = (i + 1) % n
            faces.append((start + i, start + j, start + n + j, start + n + i))
            slots.append(section_slots[i])
            tones.append(tone)

    if kind == 'pitched':
        def underside(y):
            return box_top + (s - abs(y)) * slope

        def top_surface(y):
            return underside(y) + lift
        e = s + o
        section = [(-e, underside(-e)), (0.0, underside(0.0)), (e, underside(e)), (e, top_surface(e)), (0.0, top_surface(0.0)), (-e, top_surface(-e))]
        # faces between section points: underside left, underside right, eave edge, top right, top left, eave edge
        prism(section, x0, x1, [1, 1, 2, 0, 0, 2], 2)
        eave_edges = [(-e, top_surface(-e)), (e, top_surface(e))]
        rake = [(-e, 0.0), (0.0, e)]
    else:
        def underside(y):
            return box_top + (y + s) * slope

        def top_surface(y):
            return underside(y) + lift
        e = s + o
        section = [(-e, underside(-e)), (e, underside(e)), (e, top_surface(e)), (-e, top_surface(-e))]
        prism(section, x0, x1, [1, 2, 0, 2], 2)
        eave_edges = [(-e, top_surface(-e)), (e, top_surface(e))]
        rake = [(-e, e)]
    fascia_h, fascia_t = 0.16, 0.025
    for y_edge, z_edge in eave_edges:          # fascia boards along the eaves, their top at the roof's top edge
        out = 1 if y_edge > 0 else -1
        ya, yb = (y_edge, y_edge + out * fascia_t)
        section = [(min(ya, yb), z_edge - fascia_h), (max(ya, yb), z_edge - fascia_h), (max(ya, yb), z_edge + 0.01), (min(ya, yb), z_edge + 0.01)]
        prism(section, x0 - fascia_t, x1 + fascia_t, [1, 1, 1, 1], 1, tone=_board_tone(rng))
    for x_edge in (x0 - fascia_t, x1):         # barge boards up each rake, following the slope
        for ya, yb in rake:
            start = len(verts)
            corners = []
            for xx in (x_edge, x_edge + fascia_t):
                for y in (ya, yb):
                    corners.append((xx, y, top_surface(y) + 0.01))
                    corners.append((xx, y, top_surface(y) - fascia_h))
            verts.extend(corners)
            # corners: x_low: (ya top, ya low, yb top, yb low), x_high: same
            tone = _board_tone(rng)
            for f in ((0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)):
                faces.append(tuple(start + i for i in f))
                slots.append(1)
                tones.append(tone)
    # rafter tails under the overhang along the eaves, every 0.6 m, from inside the wall line out to the fascia
    count = max(2, int(round(length / 0.6)) + 1)
    for k in range(count):
        xr = -length / 2 + 0.03 + (length - 0.06) * k / (count - 1)
        for y_wall, y_out in ((-s + 0.06, -e + fascia_t), (s - 0.06, e - fascia_t)) if kind == 'pitched' else ((-s + 0.06, -e + fascia_t), (s - 0.06, e - fascia_t)):
            section_y = sorted((y_wall, y_out))
            tone = _board_tone(rng)
            start = len(verts)
            corners = []
            for xx in (xr - 0.025, xr + 0.025):
                for y in section_y:
                    corners.append((xx, y, underside(y) + 0.002))
                    corners.append((xx, y, underside(y) - 0.10))
            verts.extend(corners)
            for f in ((0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)):
                faces.append(tuple(start + i for i in f))
                slots.append(1)
                tones.append(tone)
    to_roof = frame.inverted() @ hut_frame

    def roof_underside_over(local_point):
        p = to_roof @ Vector((local_point.x, local_point.y, 0.0))
        return underside(max(-s, min(s, p.y)))
    return frame, (verts, faces, slots, tones), roof_underside_over


# ----------------------------------------------------------------------------------------------- the tool

def _material(value):
    return store.material(value) if isinstance(value, str) else value


def lay(hut, openings=(), seed=0, sides='all', collection=None, eaves=None, overhang=0.35, pitch=None, high_side='back',
        roof_material=ROOF_MATERIAL, boards_material=BOARDS_MATERIAL, trim_material=TRIM_MATERIAL, iron_material=IRON_MATERIAL,
        rust_material=RUST_MATERIAL, glass_material=GLASS_MATERIAL, backing_material=BACKING_MATERIAL, nails=True, fill=True):
    """Clad the hut's sides in lapped boards (and, with eaves, roof it). Returns {'boards': object, 'roof': object or None}."""
    if hut is None or hut.type != 'MESH':
        raise ValueError('lay_boards needs a mesh object (the wall or hut)')
    if eaves not in (None, 'pitched', 'lean-to'):
        raise ValueError("eaves is None, 'pitched' or 'lean-to'")
    bpy.context.view_layer.update()
    rng = random.Random(seed)
    location, rotation, _ = hut.matrix_world.decompose()
    hut_frame = Matrix.Translation(location) @ rotation.to_matrix().to_4x4()
    to_frame = hut_frame.inverted()
    corners = [to_frame @ (hut.matrix_world @ Vector(c)) for c in hut.bound_box]
    low = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
    high = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
    wanted = None if sides == 'all' else {SIDE_NAMES.get(s, s) for s in sides}
    clad = [s for s in upright_sides(hut) if wanted is None or s['name'] in wanted]
    if not clad:
        raise ValueError('no upright side of %r to clad (sides=%r)' % (hut.name, sides))
    every_opening = read_openings(openings)
    known = {s['name'] for s in clad}
    for o in every_opening:
        if o['side'] not in known:
            raise ValueError('an opening is on side %r, which is not clad (clad: %s)' % (o['side'], ', '.join(sorted(known))))
    if collection is None:
        collection = bpy.data.collections.new('lay_boards')
        bpy.context.scene.collection.children.link(collection)
    box_top = location.z + high.z
    roof = None
    if eaves is not None:
        pitch = pitch if pitch is not None else (22.0 if eaves == 'pitched' else 10.0)
        centre = (low + high) / 2
        frame, parts, underside_over = _roof(hut_frame, high.x - low.x, high.y - low.y, centre, high.z, eaves, overhang, pitch, high_side, rng)
        verts, faces, slots, tones = parts
        # each side's top now follows the roof's underside (a gable, a lean-to's sides and high side)
        for side in clad:
            us = [side['u0'] + (side['u1'] - side['u0']) * k / 24 for k in range(25)]
            top = []
            for u in us:
                p = to_frame @ (side['origin'] + side['along'] * u)
                top.append((u, location.z + underside_over(p)))
            side['top'] = _upper_chain(top) if eaves == 'pitched' else top
        mesh = bpy.data.meshes.new('roof')
        mesh.from_pydata(verts, [], faces)
        for material in (_material(roof_material), _material(boards_material), _material(trim_material)):
            mesh.materials.append(material)
        for polygon, slot in zip(mesh.polygons, slots):
            polygon.material_index = slot
        attribute = mesh.attributes.new('board_tone', 'FLOAT', 'FACE')
        attribute.data.foreach_set('value', tones)
        tool = bmesh.new()
        tool.from_mesh(mesh)
        bmesh.ops.recalc_face_normals(tool, faces=tool.faces)
        tool.to_mesh(mesh)
        tool.free()
        mesh.update()
        roof = bpy.data.objects.new('roof', mesh)
        collection.objects.link(roof)
        roof.matrix_world = frame
        store.mark(roof, ground=location.z + low.z)
        roof['pitch'] = pitch
        roof['overhang'] = overhang
    shared = corners_shared(clad)
    boards_mesh = BoardMesh(to_frame)
    totals = {'boards': 0, 'nails': 0, 'rust streaks': 0, 'windows': 0, 'doors': 0, 'sides': 0, 'backing sheets': 0}
    for side in clad:
        mine = [o for o in every_opening if o['side'] == side['name']]
        counts = lap_side(boards_mesh, side, mine, shared[id(side)], rng, nails=nails, fill=fill)
        totals['backing sheets'] += _backing(boards_mesh, side, box_top)
        for key, value in counts.items():
            totals[key] += value
        totals['sides'] += 1
    materials = [_material(m) for m in (boards_material, iron_material, rust_material, trim_material, glass_material,
                                        backing_material or BACKING_MATERIAL)]
    boards = boards_mesh.make('boards', materials, collection, hut_frame)
    store.mark(boards, ground=location.z + low.z)
    for key, value in totals.items():
        boards[key] = value
    if backing_material is not None:
        store.use_material(hut, _material(backing_material), ground=location.z + low.z)
    return {'boards': boards, 'roof': roof}


def vary_boards(obj, seed=0):
    """Timber you made of many separate boards: each board (each separate piece of the mesh) its own shade, written as
    the number 'board_tone' the weathered-boards material reads. Live (a Geometry Nodes modifier), so it follows edits.
    Returns True when added (False when the object has it already or is not a mesh)."""
    name = 'lay_boards • board shades'
    if obj.type != 'MESH' or obj.modifiers.get(name) or 'board_tone' in obj.data.attributes:
        return False
    group = bpy.data.node_groups.new(name + ' • ' + obj.name, 'GeometryNodeTree')
    group.interface.new_socket(name='Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    group.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    nodes, links = group.nodes, group.links
    group_in, group_out = nodes.new('NodeGroupInput'), nodes.new('NodeGroupOutput')
    island = nodes.new('GeometryNodeInputMeshIsland')
    random_value = nodes.new('FunctionNodeRandomValue')
    random_value.data_type = 'FLOAT'
    random_value.inputs['Seed'].default_value = int(seed)
    keep = nodes.new('GeometryNodeStoreNamedAttribute')
    keep.data_type = 'FLOAT'
    keep.domain = 'FACE'
    keep.inputs['Name'].default_value = 'board_tone'
    links.new(island.outputs['Island Index'], random_value.inputs['ID'])
    links.new(group_in.outputs['Geometry'], keep.inputs['Geometry'])
    links.new(random_value.outputs['Value'], keep.inputs['Value'])
    links.new(keep.outputs['Geometry'], group_out.inputs['Geometry'])
    modifier = obj.modifiers.new(name, 'NODES')
    modifier.node_group = group
    return True


def main(argv=None):
    argv = sys.argv[sys.argv.index('--') + 1:] if argv is None and '--' in sys.argv else (argv if argv is not None else sys.argv[1:])
    parser = argparse.ArgumentParser(description=TOOL['what'] + '. Trap: ' + TOOL['trap'] + '.')
    parser.add_argument('--blend', help='the .blend file to open')
    parser.add_argument('--object', help='the wall or hut object')
    parser.add_argument('--out', help='where to save the result (.blend)')
    parser.add_argument('--opening', action='append', default=[],
                        help='"side kind left bottom width height", e.g. "front door 1.5 0 0.9 1.95" (repeat for more)')
    parser.add_argument('--seed', type=int, default=0, help="the boards' lengths, shades, joints and nails; default 0")
    parser.add_argument('--sides', default='all', help="'all' or a comma list like front,right; default all")
    parser.add_argument('--eaves', choices=['none', 'pitched', 'lean-to'], default='none', help='a roof over the box; default none')
    parser.add_argument('--overhang', type=float, default=0.35, help='metres the roof reaches past the walls; default 0.35')
    parser.add_argument('--pitch', type=float, default=None, help='roof slope, degrees; default 22 pitched, 10 lean-to')
    parser.add_argument('--high-side', default='back', help="the lean-to's high side; default back")
    parser.add_argument('--roof-material', default=ROOF_MATERIAL)
    parser.add_argument('--no-nails', action='store_true', help='no nail lines')
    parser.add_argument('--no-fill', action='store_true', help='leave the openings empty (no glass, sash or door)')
    args = parser.parse_args(argv)
    if not (args.blend and args.object and args.out):
        parser.error('--blend, --object and --out are needed to lay boards')
    openings = []
    for text in args.opening:
        parts = text.split()
        if len(parts) != 6:
            parser.error('an opening is six words: side kind left bottom width height (got %r)' % text)
        openings.append((parts[0], parts[1]) + tuple(float(p) for p in parts[2:]))
    bpy.ops.wm.open_mainfile(filepath=args.blend)
    hut = bpy.data.objects.get(args.object)
    if hut is None:
        parser.error('no object %r in %s' % (args.object, args.blend))
    made = lay(hut, openings=openings, seed=args.seed, sides='all' if args.sides == 'all' else [s.strip() for s in args.sides.split(',')],
               eaves=None if args.eaves == 'none' else args.eaves, overhang=args.overhang, pitch=args.pitch, high_side=args.high_side,
               roof_material=args.roof_material, nails=not args.no_nails, fill=not args.no_fill)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.out))
    print('boards: %d boards, %d nails on %d sides%s; saved %s' % (made['boards']['boards'], made['boards']['nails'], made['boards']['sides'],
                                                                  ', with a roof' if made['roof'] else '', args.out))


if __name__ == '__main__':
    main()
