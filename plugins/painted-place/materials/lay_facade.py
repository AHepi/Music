"""
What this file does:
Turns a flat stone wall into a built one, the way the street bundle "Rain on the Old Curve" built its tenements
(facades.py), but reading the place the builder made instead of one street's coordinates:

  - every big wall face the camera can see is covered in courses of individually chipped ashlar blocks, each
    block its own eight-sided silhouette and its own sandstone shade, with dark mortar showing in the joints;
  - the courses stop around every opening the builder made (windows, doors, their surrounds, steps), so the
    builder's windows end up set back in deep reveals;
  - each window gets stone jambs, a lintel above, a deep sill below with a dark drip line under it, and a sash:
    a timber frame, a centre bar and a meeting rail (two more bars on tall windows);
  - each face gets a plinth band, a first-floor band, a cornice under the eaves and heavy quoins at both ends,
    each band broken where it would cross an opening;
  - roof slabs get slate course lines;
  - a window in a plaster (rendered, limewashed) wall gets the joinery it has there: a painted timber casing round
    the opening, a sill with a dark drip line under it, and a sash with glazing bars, so a big pane reads as many
    small ones. Whatever the builder made already (its own sash bars, surround or sill) is kept and not doubled.

    import lay_facade
    report = lay_facade.lay_facades(scene, materials, role_from_name)

Only objects with the role `wall` (stone, brick) are built up; a `plaster` wall keeps its face and only its windows
are dressed. A stone wall's own material becomes mortar, so what shows
between the blocks reads as joints. Everything added is named "FACADE • ..." and can be removed with
remove_facades(). Nothing the builder made is moved or deleted. Each wall gets the property `facade_front`
(how far its new face stands in front of the old one), which the details step reads.
"""

import math
import random

import bmesh
import bpy
from mathutils import Vector

PREFIX = 'FACADE • '
BLOCK_FRONT = 0.20          # metres from the builder's wall face to the front of the ashlar
OPENING_ROLES = {'window lit', 'window dim', 'window dark', 'wood', 'trim', 'recess', 'pavement', 'earth', 'water'}
MOVE_ROLES = {'iron', 'rust', 'lamp glass', 'flame', 'paper', 'grime', 'brass', 'copper'}
WINDOW_ROLES = {'window lit', 'window dim', 'window dark'}
MAX_DISTANCE = 90.0          # faces whose centre is farther from the camera are left flat


def _role(obj, role_from_name):
    return obj.get('place_role') or role_from_name(obj.name)


def _is_added(obj):
    return obj.name.startswith(('FACADE •', 'DETAIL •', 'LAID •', 'LOOK •')) or obj.get('prototype') or '• laid' in obj.name


def oriented_faces(obj, minimum_area):
    """The vertical faces of an object: its own big vertical polygons if it is a simple box, else the sides of its oriented bounding box."""
    matrix = obj.matrix_world
    result = []
    if len(obj.data.polygons) <= 12:
        normal_matrix = matrix.to_3x3().inverted_safe().transposed()
        for polygon in obj.data.polygons:
            normal = (normal_matrix @ polygon.normal)
            normal.z = 0 if abs(normal.z) < 0.3 else normal.z
            if abs(normal.z) >= 0.3 or normal.length < 1e-6:
                continue
            normal.normalize()
            verts = [matrix @ obj.data.vertices[i].co for i in polygon.vertices]
            result.append((normal, verts))
    else:
        corners = [Vector(c) for c in obj.bound_box]
        lo = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
        hi = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
        rotation = matrix.to_3x3()
        for axis, sign in ((0, 1), (0, -1), (1, 1), (1, -1)):
            local_normal = Vector((0, 0, 0))
            local_normal[axis] = sign
            normal = (rotation @ local_normal)
            normal.z = 0
            if normal.length < 1e-6:
                continue
            normal.normalize()
            plane = hi[axis] if sign > 0 else lo[axis]
            other = 1 - axis
            verts = []
            for o in (lo[other], hi[other]):
                for z in (lo.z, hi.z):
                    p = Vector((0, 0, z))
                    p[axis] = plane
                    p[other] = o
                    verts.append(matrix @ p)
            result.append((normal, verts))
    faces = []
    for normal, verts in result:
        along = Vector((-normal.y, normal.x, 0)).normalized()
        centre = sum(verts, Vector((0, 0, 0))) / len(verts)
        us = [(v - centre).dot(along) for v in verts]
        zs = [v.z for v in verts]
        width, height = max(us) - min(us), max(zs) - min(zs)
        if width * height < minimum_area:
            continue
        origin = Vector((centre.x, centre.y, 0))
        faces.append({'object': obj.name, 'origin': origin, 'normal': normal, 'along': along,
                      'u0': min(us), 'u1': max(us), 'z0': min(zs), 'z1': max(zs)})
    return faces


def _buried(scene, depsgraph, face, roles):
    """A face pressed against another wall (a party wall between terraced houses) is not built up. Only another
    wall counts: windows, doors and pipes standing in front of a face do not bury it. Three probes, all must hit."""
    hits = 0
    for fu, fz in ((0.5, 0.5), (0.25, 0.3), (0.75, 0.7)):
        probe = (face['origin'] + face['along'] * (face['u0'] + (face['u1'] - face['u0']) * fu)
                 + Vector((0, 0, face['z0'] + (face['z1'] - face['z0']) * fz)))
        hit, location, normal, index, obj, matrix = scene.ray_cast(depsgraph, probe + face['normal'] * 0.005, face['normal'], distance=0.35)
        if hit and obj is not None and obj.name != face['object'] and roles.get(obj.name) in ('wall', 'plaster'):
            hits += 1
    return hits == 3


def _facing_camera(face, camera_spot):
    centre = face['origin'] + face['along'] * ((face['u0'] + face['u1']) / 2) + Vector((0, 0, (face['z0'] + face['z1']) / 2))
    to_camera = camera_spot - centre
    return to_camera.dot(face['normal']) > 0 and to_camera.length < MAX_DISTANCE


def openings_on(face, scene, roles, role_from_name):
    """Rectangles (u0, u1, z0, z1, role, object name) of the builder's things standing in front of the face."""
    found = []
    for obj in scene.objects:
        if obj.type != 'MESH' or obj.name == face['object'] or _is_added(obj):
            continue
        role = roles.get(obj.name)
        if role not in OPENING_ROLES:
            continue
        corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
        ds = [(c - face['origin']).dot(face['normal']) for c in corners]
        if max(ds) < -0.05 or min(ds) > 0.5:
            continue
        us = [(c - face['origin']).dot(face['along']) for c in corners]
        zs = [c.z for c in corners]
        u0, u1, z0, z1 = min(us), max(us), min(zs), max(zs)
        if u1 < face['u0'] or u0 > face['u1'] or z1 < face['z0'] or z0 > face['z1']:
            continue
        found.append((u0, u1, z0, z1, role, obj.name))
    return found


class FacadeMesh:
    """Collects vertices, faces and material indices for one wall, in the wall face's own frame (u along, d out, z up)."""

    def __init__(self, face):
        self.face = face
        self.verts, self.faces, self.materials, self.tones = [], [], [], []

    def point(self, u, d, z):
        p = self.face['origin'] + self.face['along'] * u + self.face['normal'] * d
        return (p.x, p.y, z)

    def poly(self, coords, faces, material, tone=None):
        start = len(self.verts)
        self.verts.extend(self.point(*c) for c in coords)
        self.faces.extend(tuple(start + i for i in f) for f in faces)
        self.materials.extend([material] * len(faces))
        if tone is None:      # a number per stone, so a scanned grain samples a different patch on every block
            u, d, z = coords[0]
            tone = (abs(u * 7.31 + z * 3.17 + d * 1.3) * 0.618) % 1.0
        self.tones.extend([tone] * len(faces))

    def box(self, u, d, z, w, dep, h, material):
        x, y, z0, z1 = w / 2, dep / 2, z - h / 2, z + h / 2
        self.poly([(u - x, d - y, z0), (u + x, d - y, z0), (u + x, d + y, z0), (u - x, d + y, z0),
                   (u - x, d - y, z1), (u + x, d - y, z1), (u + x, d + y, z1), (u - x, d + y, z1)],
                  [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)], material)

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
        self.poly(coords, faces, material, tone=rng.random())

    def make(self, name, material_list, collection, role='wall'):
        if not self.verts:
            return None
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(self.verts, [], self.faces)
        for material in material_list:
            mesh.materials.append(material)
        for polygon, index in zip(mesh.polygons, self.materials):
            polygon.material_index = index
        attribute = mesh.attributes.new('board_tone', 'FLOAT', 'FACE')
        attribute.data.foreach_set('value', self.tones)
        tool = bmesh.new()
        tool.from_mesh(mesh)
        bmesh.ops.recalc_face_normals(tool, faces=tool.faces)
        tool.to_mesh(mesh)
        tool.free()
        mesh.update()
        obj = bpy.data.objects.new(name, mesh)
        obj['place_role'] = role
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


def build_face(face, holes, windows, rng, index, shades, TRIM, DARK, WOOD, doors=()):
    """Ashlar, dressings and sashes for one face. Returns the FacadeMesh and the number of blocks."""
    mesh = FacadeMesh(face)
    u0, u1, z0, z1 = face['u0'], face['u1'], face['z0'], face['z1']
    width = u1 - u0
    blocks = 0
    course = 0.32 if index % 2 == 0 else 0.38
    z = z0 + 0.11
    while z < z1 - 0.14:
        h = course * rng.uniform(0.88, 1.10)
        zmid = z + h / 2
        in_course = [(a - 0.06, b + 0.06) for a, b, c, e in holes if z < e + 0.05 and z + h > c - 0.05]
        u = u0 - rng.uniform(0, 0.4)
        while u < u1:
            w = rng.uniform(0.46, 0.94)
            lo, hi = max(u, u0), min(u + w, u1)
            # a block that meets an opening is cut back to the opening's edge, so stone runs right up to every reveal
            for p, q in _free_segments(lo, hi, in_course, minimum=0.12):
                front = BLOCK_FRONT - 0.08 + rng.uniform(-0.018, 0.018)
                shade = rng.randrange(len(shades)) if rng.random() > 0.05 else TRIM
                mesh.block((p + q) / 2, front, zmid, q - p - 0.016, 0.16 + rng.uniform(-0.03, 0.02), h - 0.015, shade, rng)
                blocks += 1
            u += w
        z += h
    D = BLOCK_FRONT
    # windows: jambs, lintel, sill, drip line, sash
    for wu0, wu1, wz0, wz1, role in windows:
        ow, oh = wu1 - wu0, wz1 - wz0
        ou, oz = (wu0 + wu1) / 2, (wz0 + wz1) / 2
        if ow < 0.3 or oh < 0.3 or ow > 4 or oh > 4:
            continue
        trim_width = rng.uniform(0.105, 0.145)
        for side in (-1, 1):
            mesh.box(ou + side * (ow / 2 + 0.07), D - 0.02, oz, trim_width, 0.18, oh + 0.25, TRIM if rng.random() > 0.14 else rng.randrange(len(shades)))
        mesh.box(ou, D - 0.01, oz + oh / 2 + 0.11, ow + 0.32, 0.24, 0.16, TRIM)
        mesh.box(ou, D + 0.04, oz - oh / 2 - 0.10, ow + 0.36, 0.34, 0.14, TRIM)
        mesh.box(ou, D - 0.06, oz - oh / 2 - 0.22, ow + 0.13, 0.19, 0.11, DARK)
        glass = D - 0.10
        for side in (-1, 1):
            mesh.box(ou + side * (ow / 2 - 0.035), glass + 0.03, oz, 0.07, 0.08, oh, WOOD)
        for side in (-1, 1):
            mesh.box(ou, glass + 0.03, oz + side * (oh / 2 - 0.035), ow, 0.08, 0.07, WOOD)
        mesh.box(ou, glass + 0.04, oz, 0.034, 0.06, oh - 0.08, WOOD)
        mesh.box(ou, glass + 0.05, oz + rng.uniform(-0.09, 0.09), ow - 0.05, 0.07, 0.061, WOOD)
        if oh > 1.5:
            for dz in (-oh * 0.25, oh * 0.25):
                mesh.box(ou, glass + 0.035, oz + dz, ow - 0.07, 0.045, 0.026, WOOD)
    # doors: stone jambs and a lintel (the door itself is the builder's)
    for du0, du1, dz0, dz1, role in doors:
        ow, ou = du1 - du0, (du0 + du1) / 2
        for side in (-1, 1):
            mesh.box(ou + side * (ow / 2 + 0.11), D - 0.02, (dz0 + dz1) / 2, 0.22, 0.32, dz1 - dz0 + 0.1, TRIM)
        mesh.box(ou, D - 0.01, dz1 + 0.13, ow + 0.5, 0.30, 0.22, TRIM)
    # bands: plinth, first floor, below the cornice, cornice; broken around openings
    for zz in (z0 + 0.25, z0 + 3.25, z1 - 0.40, z1 - 0.15):
        if zz < z0 + 0.1 or zz > z1 - 0.05:
            continue
        crossing = [(a - 0.05, b + 0.05) for a, b, c, e in holes if c < zz + 0.1 and e > zz - 0.1]
        for p, q in _free_segments(u0 - 0.07, u1 + 0.07, crossing):
            mesh.box((p + q) / 2, D + 0.02, zz, q - p, 0.30, 0.13, TRIM)
            mesh.box((p + q) / 2, D - 0.04, zz - 0.10, q - p - 0.04, 0.23, 0.065, DARK)
    # quoins at both ends
    if width > 2.0:
        for edge in (-1, 1):
            u_edge = (u1 - 0.16) if edge > 0 else (u0 + 0.16)
            for q in range(int((z1 - z0) / 0.45)):
                zz = z0 + 0.225 + q * 0.45
                if any(c - 0.05 < zz < e + 0.05 and a - 0.3 < u_edge < b + 0.3 for a, b, c, e in holes):
                    continue
                if rng.random() > 0.07:
                    mesh.box(u_edge, D - 0.02, zz, (0.32 if q % 2 else 0.45) * rng.uniform(0.88, 1.08), 0.20, 0.426 * rng.uniform(0.94, 1.01), TRIM)
    return mesh, blocks


# ----------------------------------------------------------------------------------------------- windows in plaster and timber walls

def front_of(obj, face):
    """How far the front of a builder's object stands out from the wall face (metres; 0 when it is not there)."""
    if obj is None:
        return 0.0
    return max(0.0, max((obj.matrix_world @ Vector(c) - face['origin']).dot(face['normal']) for c in obj.bound_box))


def builder_joinery(found, window, window_name):
    """
    Which parts of a window's joinery the builder made already, judged from the builder's timber and stone things in
    front of the face: bars over the glass (a sash), a frame bigger than the glass all round (a surround), a thin
    piece just under the glass (a sill, or the beam a timber frame sits a window on).
    """
    wu0, wu1, wz0, wz1 = window
    width, area = wu1 - wu0, (wu1 - wu0) * (wz1 - wz0)
    kept = {'sash': False, 'surround': False, 'sill': False}
    for a, b, c, e, role, name in found:
        if name == window_name or role not in ('wood', 'trim'):
            continue
        own = (b - a) * (e - c)
        across = max(0.0, min(b, wu1) - max(a, wu0))
        overlap = across * max(0.0, min(e, wz1) - max(c, wz0))
        if overlap >= 0.6 * area and own <= 1.15 * area:
            kept['sash'] = True
        if a <= wu0 - 0.02 and b >= wu1 + 0.02 and c <= wz0 + 0.02 and e >= wz1 + 0.02 and 1.15 * area < own < 4.0 * area:
            kept['surround'] = True
        if wz0 - 0.30 <= e <= wz0 + 0.05 and e - c < 0.4 and across >= 0.6 * width:
            kept['sill'] = True
    return kept


def window_joinery(box, window, front, rng, *, casing=True, sill=True, sash=True, CASING=0, DARK=1):
    """
    Joinery for one window in the wall face's own frame (u along, d out from the face, z up). `box(u, d, z, w, depth,
    h, material)` adds one block; `front` is how far the builder's glass stands out from the face. A painted casing
    round the opening, a sill with the dark line of its drip under it, and a sash: its frame, glazing bars that cut the
    glass into panes about 0.45 m wide and 0.5 m tall, and a meeting rail when the window is a sash window's shape
    (taller than about 0.9 m and no wider than 1.6 m). Returns the number of blocks added.
    """
    wu0, wu1, wz0, wz1 = window
    ow, oh = wu1 - wu0, wz1 - wz0
    ou, oz = (wu0 + wu1) / 2, (wz0 + wz1) / 2
    proud = max(0.045, front + 0.06)            # the casing stands in front of the sash, the sash in front of the glass
    blocks = 0
    casing_width = rng.uniform(0.085, 0.115) if casing else 0.0
    if casing:
        for side in (-1, 1):
            box(ou + side * (ow / 2 + casing_width / 2), proud / 2, oz, casing_width, proud, oh, CASING)
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
        for side in (-1, 1):
            box(ou + side * (ow / 2 - bar / 2), d, oz, bar, depth, oh, CASING)
            box(ou, d, oz + side * (oh / 2 - bar / 2), ow, depth, bar, CASING)
        inner_w, inner_h = ow - 2 * bar, oh - 2 * bar
        columns = max(1, round(inner_w / 0.45))
        rows = max(1, round(inner_h / 0.5))
        sash_shape = oh > 0.9 and ow <= 1.6
        if sash_shape and rows % 2:
            rows += 1                            # an even number of panes up, so the meeting rail falls between them
        for k in range(1, columns):
            box(wu0 + bar + k * inner_w / columns, d + 0.002, oz, glazing, depth - 0.01, inner_h, CASING)
        for k in range(1, rows):
            z = wz0 + bar + k * inner_h / rows
            if sash_shape and 2 * k == rows:
                box(ou, d + 0.004, z + rng.uniform(-0.02, 0.02), inner_w, depth + 0.008, 0.05, CASING)   # the meeting rail
            else:
                box(ou, d + 0.002, z, inner_w, depth - 0.01, glazing, CASING)
        blocks += 4 + (columns - 1) + (rows - 1)
    return blocks


def dress_plaster_windows(scene, depsgraph, roles, role_from_name, camera_spot, rng, materials, collection):
    """Every window in a plaster wall the camera faces gets a casing, a sill and a sash, unless the builder made them."""
    report = {'plaster_walls_with_windows_dressed': 0, 'plaster_windows_dressed': 0,
              'builder_sashes_kept': 0, 'builder_surrounds_kept': 0, 'builder_sills_kept': 0}
    material_list = [materials['wood'], materials['dark']]
    for obj in list(scene.objects):
        if obj.type != 'MESH' or roles.get(obj.name) != 'plaster' or _is_added(obj):
            continue
        combined = None
        for face in oriented_faces(obj, minimum_area=1.5):
            if not _facing_camera(face, camera_spot) or _buried(scene, depsgraph, face, roles):
                continue
            found = openings_on(face, scene, roles, role_from_name)
            windows = [f for f in found if f[4] in WINDOW_ROLES and 0.3 <= f[1] - f[0] <= 4 and 0.3 <= f[3] - f[2] <= 4]
            if not windows:
                continue
            mesh = FacadeMesh(face)
            for wu0, wu1, wz0, wz1, role, name in windows:
                kept = builder_joinery(found, (wu0, wu1, wz0, wz1), name)
                window_joinery(mesh.box, (wu0, wu1, wz0, wz1), front_of(scene.objects.get(name), face), rng,
                               casing=not kept['surround'], sill=not kept['sill'], sash=not kept['sash'], CASING=0, DARK=1)
                report['plaster_windows_dressed'] += 1
                report['builder_sashes_kept'] += kept['sash']
                report['builder_surrounds_kept'] += kept['surround']
                report['builder_sills_kept'] += kept['sill']
            if combined is None:
                combined = mesh
            else:
                offset = len(combined.verts)
                combined.verts.extend(mesh.verts)
                combined.faces.extend(tuple(i + offset for i in f) for f in mesh.faces)
                combined.materials.extend(mesh.materials)
                combined.tones.extend(mesh.tones)
        if combined is not None and combined.verts:
            combined.make(PREFIX + obj.name + ' • window joinery', material_list, collection, role='wood')
            report['plaster_walls_with_windows_dressed'] += 1
    return report


def move_out_fixtures(face, scene, roles):
    """Pipes, brackets, wall lamps and the like fixed to the old face move out with the new, thicker face."""
    moved = 0
    for obj in scene.objects:
        if obj.type != 'MESH' or roles.get(obj.name) not in MOVE_ROLES or obj.get('moved_with_facade'):
            continue
        corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
        ds = [(c - face['origin']).dot(face['normal']) for c in corners]
        us = [(c - face['origin']).dot(face['along']) for c in corners]
        zs = [c.z for c in corners]
        if min(ds) < -0.05 or min(ds) > BLOCK_FRONT + 0.05:
            continue
        if max(us) < face['u0'] or min(us) > face['u1'] or max(zs) < face['z0'] or min(zs) > face['z1']:
            continue
        push = BLOCK_FRONT + 0.03 - min(ds)
        obj.location += face['normal'] * push
        obj['moved_with_facade'] = round(push, 3)
        moved += 1
    return moved


def roof_courses(obj, collection, slate):
    """Slate course lines on the sloping top of a roof slab."""
    matrix = obj.matrix_world
    normal_matrix = matrix.to_3x3().inverted_safe().transposed()
    best = None
    for polygon in obj.data.polygons:
        n = (normal_matrix @ polygon.normal).normalized()
        if 0.3 < n.z < 0.97:
            area = polygon.area
            if best is None or area > best[0]:
                best = (area, polygon, n)
    if best is None:
        return 0
    _, polygon, n = best
    verts = [matrix @ obj.data.vertices[i].co for i in polygon.vertices]
    if len(verts) != 4:
        return 0
    edges = [(verts[i], verts[(i + 1) % 4]) for i in range(4)]
    edges.sort(key=lambda e: abs(e[0].z - e[1].z))
    eave = min(edges[:2], key=lambda e: e[0].z + e[1].z)
    a, b = eave
    up = Vector((0, 0, 0))
    others = [v for v in verts if v not in (a, b)]
    top_mid = (others[0] + others[1]) / 2
    slope = top_mid - (a + b) / 2
    length = slope.length
    if length < 0.5:
        return 0
    step = 0.27
    count = int(length / step)
    out_verts, out_faces = [], []
    lift = n * 0.016
    along = (b - a).normalized()
    thickness = n * 0.03
    for k in range(1, count):
        base_a = a + slope * (k / count) + lift - along * 0.02
        base_b = b + slope * (k / count) + lift + along * 0.02
        down = slope.normalized() * 0.034
        quad = [base_a, base_b, base_b + down, base_a + down]
        start = len(out_verts)
        out_verts.extend([tuple(v) for v in quad] + [tuple(v + thickness) for v in quad])
        out_faces.extend([(start, start + 1, start + 2, start + 3), (start + 4, start + 7, start + 6, start + 5),
                          (start, start + 4, start + 5, start + 1), (start + 1, start + 5, start + 6, start + 2),
                          (start + 2, start + 6, start + 7, start + 3), (start + 3, start + 7, start + 4, start)])
    if not out_faces:
        return 0
    mesh = bpy.data.meshes.new(PREFIX + obj.name + ' • slate courses')
    mesh.from_pydata(out_verts, [], out_faces)
    mesh.materials.append(slate)
    mesh.update()
    lines = bpy.data.objects.new(mesh.name, mesh)
    lines['place_role'] = 'roof'
    collection.objects.link(lines)
    return count - 1


def remove_facades(scene):
    for obj in list(scene.objects):
        if obj.name.startswith(PREFIX):
            bpy.data.objects.remove(obj, do_unlink=True)
    for obj in scene.objects:
        for key in ('facade_front', 'facade_plinth'):
            if key in obj:
                del obj[key]
    collection = bpy.data.collections.get(PREFIX + 'built stonework')
    if collection is not None and not collection.objects:
        bpy.data.collections.remove(collection)


def lay_facades(scene, materials, role_from_name, seed=241105):
    """
    materials: shades (list of 12), trim, dark, wood, mortar, slate.
    """
    remove_facades(scene)
    rng = random.Random(seed)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    collection = bpy.data.collections.get(PREFIX + 'built stonework')
    if collection is None:
        collection = bpy.data.collections.new(PREFIX + 'built stonework')
        scene.collection.children.link(collection)
    camera_spot = scene.camera.matrix_world.translation if scene.camera else Vector((0, 0, 1.6))
    roles = {o.name: _role(o, role_from_name) for o in scene.objects if o.type == 'MESH' and not _is_added(o)}
    shades = materials['shades']
    material_list = shades + [materials['trim'], materials['dark'], materials['wood']]
    TRIM, DARK, WOOD = len(shades), len(shades) + 1, len(shades) + 2
    report = {'walls_built': 0, 'faces_built': 0, 'blocks': 0, 'windows_dressed': 0, 'roof_courses': 0, 'faces_skipped_hidden': 0, 'things_moved_out': 0}
    face_index = 0
    for obj in list(scene.objects):
        if obj.type != 'MESH' or roles.get(obj.name) != 'wall' or _is_added(obj):
            continue
        faces = [f for f in oriented_faces(obj, minimum_area=1.5)]
        built_any = False
        combined = None
        for face in faces:
            if not _facing_camera(face, camera_spot) or _buried(scene, depsgraph, face, roles):
                report['faces_skipped_hidden'] += 1
                continue
            found = openings_on(face, scene, roles, role_from_name)
            windows = [(a, b, c, e, role) for a, b, c, e, role, name in found if role in WINDOW_ROLES]

            def holds_a_window(a, b, c, e):
                return any(a <= (wa + wb) / 2 <= b and c <= (wc + we) / 2 <= e for wa, wb, wc, we, _ in windows)

            holes = [(a, b, c, e) for a, b, c, e, role, name in found if not (role == 'trim' and holds_a_window(a, b, c, e))]
            doors = [(a, b, c, e, role) for a, b, c, e, role, name in found
                     if role == 'wood' and e - c > 1.7 and c < face['z0'] + 0.8 and 0.6 < b - a < 2.5]
            mesh, blocks = build_face(face, holes, windows, rng, face_index, shades, TRIM, DARK, WOOD, doors)
            report['things_moved_out'] += move_out_fixtures(face, scene, roles)
            face_index += 1
            if combined is None:
                combined = mesh
            else:
                offset = len(combined.verts)
                combined.verts.extend(mesh.verts)
                combined.faces.extend(tuple(i + offset for i in f) for f in mesh.faces)
                combined.materials.extend(mesh.materials)
                combined.tones.extend(mesh.tones)
            report['faces_built'] += 1
            report['blocks'] += blocks
            report['windows_dressed'] += len(windows)
            built_any = True
        if built_any and combined is not None:
            combined.make(PREFIX + obj.name + ' • ashlar and dressings', material_list, collection)
            obj.data.materials.clear()
            obj.data.materials.append(materials['mortar'])
            obj['facade_front'] = BLOCK_FRONT
            obj['facade_plinth'] = 0.17   # the plinth band stands this far in front of the ashlar at the wall's foot
            report['walls_built'] += 1
    for obj in list(scene.objects):
        if obj.type == 'MESH' and roles.get(obj.name) == 'roof' and not _is_added(obj) and len(obj.data.polygons) <= 12:
            report['roof_courses'] += roof_courses(obj, collection, materials['slate'])
    report.update(dress_plaster_windows(scene, depsgraph, roles, role_from_name, camera_spot, rng, materials, collection))
    return report
