"""
What this file is: shared shape-making helpers for the camp parts (bell_tent, watch_tower, field_gun, hurricane_lantern,
sandbag_wall, barbed_wire_coil, barbed_wire_fence, crate, shell_box, timber_hut). Not a part itself (its name starts
with '_', so the store does not list it). Nothing here places anything: each helper adds a shape to a mesh being built.

Main pieces:
  - Builder: collects shapes into one bmesh; `finish` makes the object, gives it its material and links it.
  - Grain: a Builder whose mesh is built in a turned frame, so a photographed wood surface (laid in the object's own
    coordinates, grain running along the object's own Z on the sides) shows its grain along the timbers.
  - box, beam, hexahedron, cylinder, tube (a pipe along a line of points), torus, sagging lines.
  - copy_surface: a store SURFACE material copied for one part, with its own dials (named 'SURFACE • <name> (<part>)').
  - plain_material: a simple dark material made in a part's module (named 'PART • <part>: <what>').
  - point_light: a small light object linked into the part's collection.
"""

import math
import random

import bpy
import bmesh
from mathutils import Matrix, Vector

import store

Z = Vector((0.0, 0.0, 1.0))


# ----------------------------------------------------------------------------------------------- frames

def frame_matrix(z_axis, x_hint=None):
    """A rotation whose third column is z_axis (normalised) and whose first column lies as close as possible to x_hint."""
    z = Vector(z_axis).normalized()
    hint = Vector(x_hint) if x_hint is not None else Vector((1.0, 0.0, 0.0))
    if abs(hint.normalized().dot(z)) > 0.98:
        hint = Vector((0.0, 1.0, 0.0)) if abs(z.y) < 0.9 else Vector((1.0, 0.0, 0.0))
    y = z.cross(hint).normalized()
    x = y.cross(z).normalized()
    return Matrix((x, y, z)).transposed()


# ----------------------------------------------------------------------------------------------- shapes into a bmesh

def _verts(bm, points, matrix=None):
    if matrix is None:
        return [bm.verts.new(Vector(p)) for p in points]
    return [bm.verts.new(matrix @ Vector(p)) for p in points]


def _face(bm, verts, layer=None, value=None, material_index=0):
    try:
        face = bm.faces.new(verts)
    except ValueError:
        return None
    face.material_index = material_index
    if layer is not None:
        face[layer] = value
    return face


def hexahedron(bm, points, layer=None, value=None, matrix=None, material_index=0):
    """A closed six-sided solid from 8 points: points[0:4] one end ring, points[4:8] the other (same order).
    Normals are made to point outwards here (from the solid's own centre)."""
    v = _verts(bm, points, matrix)
    quads = ((0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0))
    centre = sum((x.co for x in v), Vector()) / 8.0
    faces = []
    for q in quads:
        f = _face(bm, [v[i] for i in q], layer, value, material_index)
        if f is None:
            continue
        f.normal_update()
        if f.normal.dot(f.calc_center_median() - centre) < 0:
            f.normal_flip()
        faces.append(f)
    return faces


def box(bm, low, high, matrix=None, layer=None, value=None, material_index=0):
    """An axis-aligned box from its low corner to its high corner (in the matrix's frame, if given)."""
    (x0, y0, z0), (x1, y1, z1) = low, high
    pts = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    return hexahedron(bm, pts, layer, value, matrix, material_index)


def centred_box(bm, centre, size, matrix=None, layer=None, value=None, material_index=0):
    c, s = Vector(centre), Vector(size) / 2.0
    return box(bm, c - s, c + s, matrix, layer, value, material_index)


def beam(bm, p0, p1, width, depth, up=None, layer=None, value=None, matrix=None, material_index=0, twist=0.0):
    """A square-cut timber from p0 to p1: `width` across (horizontal-ish), `depth` along `up` (default world Z)."""
    p0, p1 = Vector(p0), Vector(p1)
    axis = p1 - p0
    if axis.length < 1e-6:
        return []
    a = axis.normalized()
    u = Vector(up) if up is not None else Z
    if abs(u.normalized().dot(a)) > 0.98:
        u = Vector((0.0, 1.0, 0.0)) if abs(a.y) < 0.9 else Vector((1.0, 0.0, 0.0))
    x = u.cross(a).normalized()
    y = a.cross(x).normalized()
    if twist:
        x, y = x * math.cos(twist) + y * math.sin(twist), y * math.cos(twist) - x * math.sin(twist)
    hw, hd = width / 2.0, depth / 2.0
    ring = [(-hw, -hd), (hw, -hd), (hw, hd), (-hw, hd)]
    pts = [p0 + x * i + y * j for i, j in ring] + [p1 + x * i + y * j for i, j in ring]
    return hexahedron(bm, pts, layer, value, matrix, material_index)


def cylinder(bm, p0, p1, r0, r1=None, segments=12, caps=True, matrix=None, layer=None, value=None, material_index=0, phase=0.0):
    """A round rod (or a cone if r1 differs) from p0 to p1; returns (start ring, end ring) of vertices."""
    p0, p1 = Vector(p0), Vector(p1)
    r1 = r0 if r1 is None else r1
    rot = frame_matrix(p1 - p0)
    ring0, ring1 = [], []
    for k in range(segments):
        a = 2.0 * math.pi * k / segments + phase
        d = rot @ Vector((math.cos(a), math.sin(a), 0.0))
        ring0.append(p0 + d * r0)
        ring1.append(p1 + d * r1)
    v0 = _verts(bm, ring0, matrix)
    v1 = _verts(bm, ring1, matrix)
    for k in range(segments):
        k2 = (k + 1) % segments
        _face(bm, [v0[k], v0[k2], v1[k2], v1[k]], layer, value, material_index)
    if caps:
        if r0 > 1e-6:
            _face(bm, list(reversed(v0)), layer, value, material_index)
        if r1 > 1e-6:
            _face(bm, v1, layer, value, material_index)
    return v0, v1


def lathe(bm, profile, segments=16, centre=(0.0, 0.0, 0.0), close_bottom=True, close_top=True, matrix=None,
          material_index=0, layer=None, value=None):
    """A turned shape about the Z axis from a profile of (radius, z) pairs going upwards."""
    cx, cy, cz = centre
    rings = []
    for r, z in profile:
        rings.append(_verts(bm, [(cx + r * math.cos(2 * math.pi * k / segments), cy + r * math.sin(2 * math.pi * k / segments), cz + z)
                                 for k in range(segments)], matrix))
    faces = []
    for a, b in zip(rings[:-1], rings[1:]):
        for k in range(segments):
            k2 = (k + 1) % segments
            f = _face(bm, [a[k], a[k2], b[k2], b[k]], layer, value, material_index)
            if f:
                faces.append(f)
    if close_bottom and profile[0][0] > 1e-6:
        _face(bm, list(reversed(rings[0])), layer, value, material_index)
    if close_top and profile[-1][0] > 1e-6:
        _face(bm, rings[-1], layer, value, material_index)
    return rings


def torus(bm, centre, axis, major, minor, segments=24, sides=6, matrix=None, arc=2 * math.pi, layer=None, value=None, material_index=0):
    """A ring (or part of one, `arc` radians) about `axis` through `centre`."""
    rot = frame_matrix(axis)
    c = Vector(centre)
    closed = arc >= 2 * math.pi - 1e-6
    n = segments if closed else segments + 1
    rings = []
    for i in range(n):
        u = arc * i / segments
        radial = rot @ Vector((math.cos(u), math.sin(u), 0.0))
        up = rot @ Vector((0.0, 0.0, 1.0))
        ring = []
        for j in range(sides):
            v = 2 * math.pi * j / sides
            ring.append(c + radial * (major + minor * math.cos(v)) + up * (minor * math.sin(v)))
        rings.append(_verts(bm, ring, matrix))
    pairs = list(zip(rings[:-1], rings[1:])) + ([(rings[-1], rings[0])] if closed else [])
    for a, b in pairs:
        for j in range(sides):
            j2 = (j + 1) % sides
            _face(bm, [a[j], b[j], b[j2], a[j2]], layer, value, material_index)
    if not closed:
        _face(bm, list(reversed(rings[0])), layer, value, material_index)
        _face(bm, rings[-1], layer, value, material_index)


def tube(bm, points, radius, sides=6, caps=True, matrix=None, radii=None, layer=None, value=None, material_index=0, twist=0.0):
    """A round pipe along a line of points (rope, wire, a bent rod). Frames are carried along without twisting."""
    pts = [Vector(p) for p in points]
    if len(pts) < 2:
        return
    tangents = []
    for i in range(len(pts)):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, len(pts) - 1)]
        t = b - a
        tangents.append(t.normalized() if t.length > 1e-9 else Vector((0, 0, 1)))
    normal = frame_matrix(tangents[0]).col[0].xyz
    rings = []
    for i, p in enumerate(pts):
        t = tangents[i]
        normal = (normal - t * normal.dot(t))
        if normal.length < 1e-6:
            normal = frame_matrix(t).col[0].xyz
        normal.normalize()
        binormal = t.cross(normal)
        r = radius if radii is None else radii[i]
        ring = []
        for j in range(sides):
            a = 2 * math.pi * j / sides + twist * i
            ring.append(p + (normal * math.cos(a) + binormal * math.sin(a)) * r)
        rings.append(_verts(bm, ring, matrix))
    for a, b in zip(rings[:-1], rings[1:]):
        for j in range(sides):
            j2 = (j + 1) % sides
            _face(bm, [a[j], a[j2], b[j2], b[j]], layer, value, material_index)
    if caps:
        _face(bm, list(reversed(rings[0])), layer, value, material_index)
        _face(bm, rings[-1], layer, value, material_index)


def extrude_polygon(bm, outline, origin, axis_u, axis_v, axis_w, thickness, layer=None, value=None, material_index=0):
    """A flat shape (a list of (u, v) points, going round once) given thickness along axis_w: e.g. a stepped stair
    stringer. origin + u*axis_u + v*axis_v is the shape's plane; the solid runs from w = 0 to w = thickness."""
    o, au, av, aw = Vector(origin), Vector(axis_u), Vector(axis_v), Vector(axis_w)
    front = [bm.verts.new(o + au * u + av * v) for u, v in outline]
    back = [bm.verts.new(o + au * u + av * v + aw * thickness) for u, v in outline]
    faces = [_face(bm, front, layer, value, material_index), _face(bm, list(reversed(back)), layer, value, material_index)]
    n = len(outline)
    for k in range(n):
        k2 = (k + 1) % n
        faces.append(_face(bm, [front[k2], front[k], back[k], back[k2]], layer, value, material_index))
    faces = [f for f in faces if f is not None]
    bmesh.ops.recalc_face_normals(bm, faces=faces)
    return faces


def ring_band(bm, centre, axis, r_in, r_out, width, segments=48, matrix=None, layer=None, value=None, material_index=0):
    """A flat ring with a square cross-section about `axis` (a wheel's tyre or felloe)."""
    rot = frame_matrix(axis)
    c = Vector(centre)
    ax = rot.col[2].xyz
    rings = []
    for r, w in ((r_in, -width / 2), (r_out, -width / 2), (r_out, width / 2), (r_in, width / 2)):
        rings.append(_verts(bm, [c + rot @ Vector((r * math.cos(2 * math.pi * k / segments), r * math.sin(2 * math.pi * k / segments), 0.0))
                                 + ax * w for k in range(segments)], matrix))
    for a, b in zip(rings, rings[1:] + rings[:1]):
        for k in range(segments):
            k2 = (k + 1) % segments
            _face(bm, [a[k], a[k2], b[k2], b[k]], layer, value, material_index)


def tapered_beam(bm, p0, p1, w0, d0, w1, d1, up=None, matrix=None, layer=None, value=None, material_index=0):
    """A timber or rod from p0 to p1, `w0` x `d0` thick at p0 narrowing to `w1` x `d1` at p1 (a spoke)."""
    p0, p1 = Vector(p0), Vector(p1)
    a = (p1 - p0).normalized()
    u = Vector(up) if up is not None else Z
    if abs(u.normalized().dot(a)) > 0.98:
        u = Vector((0.0, 1.0, 0.0)) if abs(a.y) < 0.9 else Vector((1.0, 0.0, 0.0))
    x = u.cross(a).normalized()
    y = a.cross(x).normalized()
    ring0 = [p0 + x * i * w0 / 2 + y * j * d0 / 2 for i, j in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    ring1 = [p1 + x * i * w1 / 2 + y * j * d1 / 2 for i, j in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    return hexahedron(bm, ring0 + ring1, layer, value, matrix, material_index)


def sandbag(bm, centre, length, width, height, turn, rnd, tied=1, slump=0.0, matrix=None):
    """One filled sandbag: a soft pillow, boxy in the middle, thinner towards the ends, flattened where it rests,
    one end gathered and tied. `turn` (radians about Z); `slump` sags it over whatever is under it (metres)."""
    from mathutils import noise as _noise
    made = bmesh.ops.create_uvsphere(bm, u_segments=14, v_segments=9, radius=1.0)
    a, b, c = length / 2.0, width / 2.0, height / 2.0
    phase = Vector((rnd.uniform(0, 40), rnd.uniform(0, 40), rnd.uniform(0, 40)))
    rot = Matrix.Rotation(turn, 3, 'Z')
    tilt = Matrix.Rotation(rnd.uniform(-0.04, 0.04), 3, 'X') @ Matrix.Rotation(rnd.uniform(-0.04, 0.04), 3, 'Y')
    for v in made['verts']:
        d = v.co.copy()
        x = math.copysign(abs(d.x) ** 0.55, d.x)
        y = math.copysign(abs(d.y) ** 0.42, d.y)
        z = math.copysign(abs(d.z) ** 0.55, d.z)
        end = max(0.0, (x * tied - 0.72) / 0.28)              # the tied end, gathered
        thin = 1.0 - 0.32 * x ** 4
        y *= (1.0 - 0.55 * end ** 1.5) * (0.92 + 0.08 * thin)
        z *= thin * (1.0 - 0.5 * end ** 1.5)
        z = max(z, -0.78)                                      # pressed flat underneath
        if z > 0.6:
            z = 0.6 + (z - 0.6) * 0.35
        p = Vector((x * a * (1.0 + 0.06 * end), y * b, z * c))
        p.z -= slump * (1.0 - x * x)
        p += Vector((0, 0, 1)) * (0.014 * _noise.noise(p * 11.0 + phase)) + Vector((0, 1, 0)) * (0.01 * _noise.noise(p * 8.0 - phase))
        p += Vector((1, 0, 0)) * (0.008 * _noise.noise(p * 14.0 + phase * 0.5))
        p = rot @ (tilt @ p) + Vector(centre)
        v.co = matrix @ p if matrix is not None else p
    return made['verts']


def resample(points, step):
    """Points every `step` metres along a line of points (the last point kept)."""
    pts = [Vector(p) for p in points]
    out = [pts[0].copy()]
    next_d, acc = step, 0.0
    for a, b in zip(pts[:-1], pts[1:]):
        seg = (b - a).length
        if seg < 1e-9:
            continue
        while next_d <= acc + seg:
            out.append(a.lerp(b, (next_d - acc) / seg))
            next_d += step
        acc += seg
    if (out[-1] - pts[-1]).length > step * 0.25:
        out.append(pts[-1].copy())
    else:
        out[-1] = pts[-1].copy()
    return out


def barbed_strand(bm, points, rnd, barb_every=0.125, wire_r=0.0014, twist_pitch=0.07, barbs=True):
    """Barbed wire along a line of points: two wires twisted round each other, and every `barb_every` metres a
    four-point barb (two short wires wrapped on, their ends sticking out)."""
    line = resample(points, 0.012)
    tangents = []
    for i in range(len(line)):
        a, b = line[max(i - 1, 0)], line[min(i + 1, len(line) - 1)]
        tangents.append((b - a).normalized())
    frame_n = frame_matrix(tangents[0]).col[0].xyz
    normals = []
    for t in tangents:
        frame_n = (frame_n - t * frame_n.dot(t)).normalized()
        normals.append(frame_n.copy())
    run = 0.0
    wires = ([], [])
    for i, p in enumerate(line):
        if i:
            run += (line[i] - line[i - 1]).length
        ang = 2 * math.pi * run / twist_pitch
        n, b = normals[i], tangents[i].cross(normals[i])
        off = (n * math.cos(ang) + b * math.sin(ang)) * wire_r * 1.1
        wires[0].append(p + off)
        wires[1].append(p - off)
    for w in wires:
        tube(bm, w, wire_r, sides=4, caps=False)
    if not barbs:
        return
    total = run
    s = rnd.uniform(0.02, barb_every)
    idx, run = 0, 0.0
    while s < total - 0.02:
        while idx < len(line) - 2 and run + (line[idx + 1] - line[idx]).length < s:
            run += (line[idx + 1] - line[idx]).length
            idx += 1
        p, t = line[idx], tangents[idx]
        n, b = normals[idx], tangents[idx].cross(normals[idx])
        spin = rnd.uniform(0, math.pi)
        for k in range(2):
            a = spin + k * math.pi / 2
            d = n * math.cos(a) + b * math.sin(a)
            for sign in (-1, 1):
                tip = p + d * sign * 0.013 + t * sign * 0.006 * (1 if k else -1)
                tube(bm, [p + t * 0.002 * (k - 0.5), tip], 0.0011, sides=3, caps=True)
        s += barb_every * rnd.uniform(0.9, 1.1)


def sag_line(p0, p1, sag, count, wobble=0.0, rnd=None):
    """Points along a line from p0 to p1 hanging `sag` metres at the middle (a chain-like curve)."""
    p0, p1 = Vector(p0), Vector(p1)
    out = []
    for i in range(count + 1):
        t = i / count
        p = p0.lerp(p1, t)
        p.z -= sag * 4.0 * t * (1.0 - t)
        if wobble and rnd is not None and 0 < i < count:
            p += Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))) * wobble
        out.append(p)
    return out


def chamfer_all(bm, width, segments=1):
    """Soften every sharp edge a little (catches light on corners, as real timber does)."""
    edges = [e for e in bm.edges if len(e.link_faces) == 2 and e.calc_face_angle(0.0) > math.radians(40)]
    if edges:
        bmesh.ops.bevel(bm, geom=edges, offset=width, offset_type='OFFSET', segments=segments, profile=0.5, affect='EDGES',
                        clamp_overlap=True)


# ----------------------------------------------------------------------------------------------- objects

def finish_mesh(name, bm, collection, material=None, smooth=False, matrix=None, extra_materials=()):
    """Turn a bmesh into an object (scale 1, mesh at real size), give it its material(s), link it into `collection`."""
    mesh = bpy.data.meshes.new(name)
    bm.normal_update()
    bm.to_mesh(mesh)
    bm.free()
    if smooth:
        mesh.shade_smooth()
    obj = bpy.data.objects.new(name, mesh)
    if matrix is not None:
        obj.matrix_world = matrix
    collection.objects.link(obj)
    if material is not None:
        mat = store.material(material) if isinstance(material, str) else material
        mesh.materials.append(mat)
        for extra in extra_materials:
            mesh.materials.append(store.material(extra) if isinstance(extra, str) else extra)
        store.mark(obj)
    return obj


class Builder:
    """Shapes gathered into one mesh object. `matrix` (optional) is where the object stands; shapes are given in
    world coordinates and turned into the object's own."""

    def __init__(self, name, material, smooth=False, matrix=None, extra_materials=()):
        self.name = name
        self.material = material
        self.extra_materials = extra_materials
        self.smooth = smooth
        self.bm = bmesh.new()
        self.matrix = matrix
        self.inverse = matrix.inverted() if matrix is not None else None
        self.layers = {}

    def layer(self, name):
        if name not in self.layers:
            self.layers[name] = self.bm.faces.layers.float.new(name)
        return self.layers[name]

    def finish(self, collection):
        if len(self.bm.verts) == 0:
            self.bm.free()
            return None
        return finish_mesh(self.name, self.bm, collection, self.material, self.smooth, self.matrix, self.extra_materials)


class Grain(Builder):
    """A Builder for photographed wood: its mesh is built in a frame turned so the object's own Z runs along
    `along` (the timbers' length), so the photograph's grain runs along the timbers. `rnd` shifts where the
    photograph falls, so two Grain objects never show the same patch of wood."""

    def __init__(self, name, material, along, rnd, x_hint=None, smooth=False):
        rot = frame_matrix(along, x_hint).to_4x4()
        shift = Vector((rnd.uniform(-2.0, 2.0), rnd.uniform(-2.0, 2.0), rnd.uniform(-2.0, 2.0)))
        matrix = rot @ Matrix.Translation(-shift)
        Builder.__init__(self, name, material, smooth, matrix)


def to_local(builder, p):
    return builder.inverse @ Vector(p) if builder.inverse is not None else Vector(p)


def add_beam(builder, p0, p1, width, depth, up=None, **kw):
    """A beam given in world coordinates, into a Builder (or Grain) that may stand in a turned frame."""
    if builder.inverse is None:
        return beam(builder.bm, p0, p1, width, depth, up, **kw)
    up_world = Vector(up) if up is not None else Z
    rot_inv = builder.inverse.to_3x3()
    return beam(builder.bm, to_local(builder, p0), to_local(builder, p1), width, depth, rot_inv @ up_world, **kw)


def add_box(builder, low, high, **kw):
    """An axis-aligned (in world) box into a Builder or Grain."""
    if builder.inverse is None:
        return box(builder.bm, low, high, **kw)
    (x0, y0, z0), (x1, y1, z1) = low, high
    pts = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    return hexahedron(builder.bm, [to_local(builder, p) for p in pts], **kw)


def add_hexahedron(builder, points, **kw):
    if builder.inverse is None:
        return hexahedron(builder.bm, points, **kw)
    return hexahedron(builder.bm, [to_local(builder, p) for p in points], **kw)


def add_cylinder(builder, p0, p1, r0, r1=None, **kw):
    if builder.inverse is None:
        return cylinder(builder.bm, p0, p1, r0, r1, **kw)
    return cylinder(builder.bm, to_local(builder, p0), to_local(builder, p1), r0, r1, **kw)


# ----------------------------------------------------------------------------------------------- materials

def copy_surface(store_name, part, picture_scale=None, **dials):
    """A store SURFACE material copied for one part: 'SURFACE • <name> (<part>)', with its own dials
    (Wet, Grime, Mud height, Mud color, Edge wear, Bump, Darken) and picture size. Made once per file."""
    name = '%s (%s)' % (store_name, part)
    existing = bpy.data.materials.get(name)
    if existing is not None:
        return existing
    mat = store.material(store_name).copy()
    mat.name = name
    nodes = mat.node_tree.nodes
    if picture_scale is not None and 'Picture size' in nodes:
        nodes['Picture size'].inputs['Scale'].default_value = picture_scale
    weather = nodes.get('Weather')
    for key, value in dials.items():
        socket_name = key.replace('_', ' ').capitalize()
        if socket_name == 'Mud color':
            socket_name = 'Mud color'
        if weather is not None and socket_name in weather.inputs:
            weather.inputs[socket_name].default_value = value
    return mat


def plain_material(part, what, colour, roughness=0.7, metallic=0.0, variation=0.25, scale=6.0, bump=0.15,
                   emission=None, emission_strength=0.0):
    """A simple material made in a part's module, 'PART • <part>: <what>': a dark base colour broken up by noise
    (so it is never flat), roughness, an optional small bump."""
    name = 'PART • %s: %s' % (part, what)
    existing = bpy.data.materials.get(name)
    if existing is not None:
        return existing
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = nodes.get('Principled BSDF')
    coord = nodes.new('ShaderNodeTexCoord')
    noise = nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = scale
    noise.inputs['Detail'].default_value = 6.0
    noise.inputs['Roughness'].default_value = 0.6
    links.new(coord.outputs['Object'], noise.inputs['Vector'])
    ramp = nodes.new('ShaderNodeValToRGB')
    dark = tuple(c * (1.0 - variation) for c in colour)
    light = tuple(min(1.0, c * (1.0 + variation)) for c in colour)
    ramp.color_ramp.elements[0].position = 0.3
    ramp.color_ramp.elements[0].color = (*dark, 1.0)
    ramp.color_ramp.elements[1].position = 0.7
    ramp.color_ramp.elements[1].color = (*light, 1.0)
    links.new(noise.outputs['Fac'], ramp.inputs['Fac'])
    links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = metallic
    if bump:
        bump_node = nodes.new('ShaderNodeBump')
        bump_node.inputs['Strength'].default_value = bump
        bump_node.inputs['Distance'].default_value = 0.005
        links.new(noise.outputs['Fac'], bump_node.inputs['Height'])
        links.new(bump_node.outputs['Normal'], bsdf.inputs['Normal'])
    if emission is not None:
        bsdf.inputs['Emission Color'].default_value = (*emission, 1.0)
        bsdf.inputs['Emission Strength'].default_value = emission_strength
    mat.diffuse_color = (*colour, 1.0)
    return mat


def painted_surface(part, what, store_name, paint, grain=0.5, rust=0.0, **dials):
    """Old paint over a photographed surface, made from a store SURFACE material: the photograph's light and dark
    show through the paint (grain, dents); where `rust` > 0, the photograph's own rust shows where it is rusty.
    Keeps the store's Weather dials (mud, grime, edge wear...). Named 'PART • <part>: <what>'."""
    name = 'PART • %s: %s' % (part, what)
    existing = bpy.data.materials.get(name)
    if existing is not None:
        return existing
    source = store.material(store_name)
    darken = source.node_tree.nodes['Weather'].inputs['Darken'].default_value
    mean = 0.08 / max(darken, 0.05) ** (1 / 0.7) if darken < 0.999 else 0.06
    mat = source.copy()
    mat.name = name
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    weather = nodes['Weather']
    photo = weather.inputs['Color'].links[0].from_socket
    bw = nodes.new('ShaderNodeRGBToBW')
    links.new(photo, bw.inputs['Color'])
    factor = nodes.new('ShaderNodeMath')
    factor.operation = 'MULTIPLY_ADD'
    factor.use_clamp = False
    links.new(bw.outputs['Val'], factor.inputs[0])
    factor.inputs[1].default_value = grain / mean
    factor.inputs[2].default_value = 1.0 - grain
    tinted = nodes.new('ShaderNodeVectorMath')
    tinted.operation = 'SCALE'
    tinted.inputs[0].default_value = paint
    links.new(factor.outputs['Value'], tinted.inputs['Scale'])
    colour = tinted.outputs['Vector']
    if rust > 0.0:
        split = nodes.new('ShaderNodeSeparateColor')
        links.new(photo, split.inputs['Color'])
        redness = nodes.new('ShaderNodeMath')
        redness.operation = 'SUBTRACT'
        links.new(split.outputs['Red'], redness.inputs[0])
        links.new(split.outputs['Blue'], redness.inputs[1])
        mask = nodes.new('ShaderNodeMapRange')
        mask.clamp = True
        links.new(redness.outputs['Value'], mask.inputs['Value'])
        mask.inputs['From Min'].default_value = 0.34
        mask.inputs['From Max'].default_value = 0.55
        mask.inputs['To Max'].default_value = rust
        rusty = nodes.new('ShaderNodeVectorMath')
        rusty.operation = 'SCALE'
        rusty.inputs[0].default_value = (0.072, 0.033, 0.012)
        links.new(factor.outputs['Value'], rusty.inputs['Scale'])
        mix_node = nodes.new('ShaderNodeMix')
        mix_node.data_type = 'RGBA'
        links.new(mask.outputs['Result'], mix_node.inputs[0])
        links.new(colour, mix_node.inputs[6])
        links.new(rusty.outputs['Vector'], mix_node.inputs[7])
        colour = mix_node.outputs[2]
    links.new(colour, weather.inputs['Color'])
    weather.inputs['Darken'].default_value = 1.0
    for key, value in dials.items():
        socket_name = key.replace('_', ' ').capitalize()
        if socket_name in weather.inputs:
            weather.inputs[socket_name].default_value = value
    mat.diffuse_color = (*paint, 1.0)
    return mat


def rope_material(part):
    """Weathered hemp rope, dark and dusty: 'PART • <part>: hemp rope'."""
    return plain_material(part, 'hemp rope', (0.105, 0.085, 0.058), roughness=0.92, variation=0.3, scale=40.0, bump=0.3)


def point_light(name, collection, location, energy, colour=(1.0, 0.58, 0.26), radius=0.05):
    """A small warm point light, linked into the part's collection (store.add_part parents it with the rest)."""
    data = bpy.data.lights.new(name, 'POINT')
    data.energy = energy
    data.color = colour
    data.shadow_soft_size = radius
    obj = bpy.data.objects.new(name, data)
    obj.location = location
    collection.objects.link(obj)
    return obj


def rand(seed, salt):
    """The part's own dice: the same seed and salt always give the same numbers."""
    return random.Random((int(seed) + 1) * 1000003 + sum(ord(c) * (i + 1) for i, c in enumerate(salt)))
