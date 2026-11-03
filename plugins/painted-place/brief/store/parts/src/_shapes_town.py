"""
What this file is: shape helpers shared by the town, mine and tea-room parts (gas_lamp, coal_cart, winding_tower,
ore_car, rails, barrel, tea_urn, bentwood_chair, marble_table, teapot_sign). It is not a part (its name starts with
'_', so the store does not list it).

    shape = Shape()                         gathers pieces of one object, in the part's own coordinates (metres)
    shape.box(centre, size)                 a box; shape.beam(a, b, width, height) a squared bar from a to b
    shape.cylinder(a, b, r0, r1)            a round bar or tapered cone from a to b
    shape.lathe([(r, z), ...])              a turned shape round the Z axis (an urn, a lamp base, a barrel)
    shape.sweep(points, radius)             a round rod bent along a line of points (bentwood, a rope, a wheel tyre)
    shape.prism(outline, z0, z1)            a flat outline given a thickness
    obj = shape.finish('name', collection, material)

    timber(collection, 'name', a, b, width, height, material)
        one sawn timber or plank as its own object, its own Z along the timber, so the grain of a photographed wood
        surface (laid from three sides in the object's own coordinates) runs along the timber and not across it.

Materials: `material(name)` is the store's; `surface_copy(name, part, **dials)` a copy of a SURFACE material with its
Weather dials turned for one part; `part_material(part, what, maker)` a material a part makes for itself, named
'PART • <part>: <what>', made once per file.
"""

import math
import random

import bpy
import bmesh
from mathutils import Matrix, Vector

import store

UP = Vector((0.0, 0.0, 1.0))

# the narrow-gauge track the rails part lays and the ore car runs on (metres): both parts read these numbers, so a
# car placed at the same point as a piece of track stands with its wheels on the rails
TRACK_GAUGE = 0.600            # between the inner faces of the two rail heads (two-foot mine gauge)
RAIL_HEAD = 0.044              # width of a rail head
RAIL_HEIGHT = 0.080            # foot to top of a rail
SLEEPER_TOP = 0.100            # sleepers lie on the ground, 10 cm deep
RAIL_TOP = SLEEPER_TOP + RAIL_HEIGHT          # 0.18 m: where a wheel's tread rests
RAIL_CENTRE = TRACK_GAUGE / 2 + RAIL_HEAD / 2  # 0.322 m either side of the middle


def rng_for(part, seed, salt=''):
    """The part's own random numbers: the same seed always gives the same part."""
    return random.Random('%s|%s|%s' % (part, seed, salt))


def smooth_path(points, steps=6, closed=False):
    """A smooth curve through the given points (Catmull-Rom), `steps` points per span: for bent rods, handles, scrolls."""
    pts = [Vector(p) for p in points]
    n = len(pts)
    out = []
    spans = n if closed else n - 1
    for i in range(spans):
        p0 = pts[(i - 1) % n] if (closed or i > 0) else pts[0] * 2 - pts[1]
        p1 = pts[i]
        p2 = pts[(i + 1) % n]
        p3 = pts[(i + 2) % n] if (closed or i + 2 < n) else pts[-1] * 2 - pts[-2]
        for k in range(steps):
            t = k / steps
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    if not closed:
        out.append(pts[-1])
    return out


def frame_along(direction, up=UP):
    """A rotation whose Z runs along `direction`, its X square to `up` (so a beam's faces stay level)."""
    z = Vector(direction).normalized()
    x = Vector(up).cross(z)
    if x.length < 1e-6:
        x = Vector((0.0, 1.0, 0.0)).cross(z)
        if x.length < 1e-6:
            x = Vector((1.0, 0.0, 0.0)).cross(z)
    x.normalize()
    y = z.cross(x).normalized()
    return Matrix((x, y, z)).transposed()


def to4(rotation, location=(0.0, 0.0, 0.0)):
    m = rotation.to_4x4() if rotation is not None else Matrix.Identity(4)
    m.translation = Vector(location)
    return m


class Shape:
    """One object's pieces, gathered into a bmesh. Every piece is a closed solid unless said otherwise."""

    def __init__(self):
        self.bm = bmesh.new()
        self.material_index = 0

    # ------------------------------------------------------------------ low level
    def _verts(self, points):
        return [self.bm.verts.new(Vector(p)) for p in points]

    def _face(self, verts):
        try:
            face = self.bm.faces.new(verts)
        except ValueError:
            return None
        face.material_index = self.material_index
        return face

    def poly(self, points):
        """One open face (a flat sheet with no thickness)."""
        return self._face(self._verts(points))

    def _rings(self, rings, closed_ring=True, cap_first=False, cap_last=False):
        """Join rings of vertices (equal counts, or a single vertex for a pointed end) with faces."""
        made = []
        for a, b in zip(rings[:-1], rings[1:]):
            count = max(len(a), len(b))
            last = count if closed_ring else count - 1
            for j in range(last):
                j2 = (j + 1) % count
                quad = [a[j % len(a)], a[j2 % len(a)], b[j2 % len(b)], b[j % len(b)]]
                unique = []
                for v in quad:
                    if v not in unique:
                        unique.append(v)
                if len(unique) >= 3:
                    face = self._face(unique)
                    if face is not None:
                        made.append(face)
        if cap_first and len(rings[0]) > 2:
            self._face(list(reversed(rings[0])))
        if cap_last and len(rings[-1]) > 2:
            self._face(list(rings[-1]))
        return made

    # ------------------------------------------------------------------ solids
    def box(self, centre, size, rotation=None):
        m = to4(rotation, centre) @ Matrix.Diagonal((size[0], size[1], size[2], 1.0))
        made = bmesh.ops.create_cube(self.bm, size=1.0, matrix=m)
        for v in made['verts']:
            for f in v.link_faces:
                f.material_index = self.material_index
        return made

    def beam(self, a, b, width, height, up=UP, extend=0.0):
        """A squared bar from a to b: `width` across (level), `height` the other way; `extend` adds length at both ends."""
        a, b = Vector(a), Vector(b)
        d = b - a
        if d.length < 1e-6:
            return None
        r = frame_along(d, up)
        length = d.length + 2 * extend
        return self.box((a + b) / 2, (width, height, length), r)

    def lathe(self, profile, segments=32, matrix=None, phase=0.0, flutes=0, open_ends=False):
        """A turned solid round local Z: profile is [(radius, z), ...] or [(radius, z, flute depth), ...] from one end
        to the other; a radius of 0 closes that end to a point. Flutes (grooves running up) cut each ring by its depth
        (a fraction of the radius)."""
        m = matrix if matrix is not None else Matrix.Identity(4)
        rings = []
        for entry in profile:
            r, z = entry[0], entry[1]
            depth = entry[2] if len(entry) > 2 else 0.0
            if r < 1e-7:
                rings.append(self._verts([m @ Vector((0.0, 0.0, z))]))
                continue
            ring = []
            for j in range(segments):
                t = phase + 2 * math.pi * j / segments
                rr = r
                if flutes and depth:
                    groove = (0.5 + 0.5 * math.cos(flutes * t)) ** 0.55
                    rr = r * (1.0 - depth * groove)
                ring.append(m @ Vector((rr * math.cos(t), rr * math.sin(t), z)))
            rings.append(self._verts(ring))
        cap_first = not open_ends and len(rings[0]) > 1
        cap_last = not open_ends and len(rings[-1]) > 1
        return self._rings(rings, True, cap_first, cap_last)

    def cylinder(self, a, b, r0, r1=None, segments=16, caps=True, phase=0.0):
        a, b = Vector(a), Vector(b)
        r1 = r0 if r1 is None else r1
        d = b - a
        m = to4(frame_along(d), a)
        return self.lathe([(r0, 0.0), (r1, d.length)], segments, m, phase, open_ends=not caps)

    def sphere(self, centre, radius, segments=16, rings=8, squash=(1.0, 1.0, 1.0)):
        profile = []
        for k in range(rings + 1):
            a = -math.pi / 2 + math.pi * k / rings
            profile.append((radius * math.cos(a), radius * math.sin(a)))
        m = Matrix.Translation(Vector(centre)) @ Matrix.Diagonal((squash[0], squash[1], squash[2], 1.0))
        return self.lathe(profile, segments, m)

    def sweep(self, points, radius, sides=8, closed=False, caps=True, radii=None, up=None, section=None):
        """A rod along a line of points (a polyline; give enough points for curves). `radii` gives one radius per point;
        `section` a list of (x, y) points for a shaped section instead of a circle (x across, y up)."""
        pts = [Vector(p) for p in points]
        n = len(pts)
        if n < 2:
            return None
        tangents = []
        for i in range(n):
            if closed:
                t = pts[(i + 1) % n] - pts[i - 1]
            elif i == 0:
                t = pts[1] - pts[0]
            elif i == n - 1:
                t = pts[-1] - pts[-2]
            else:
                t = (pts[i + 1] - pts[i]).normalized() + (pts[i] - pts[i - 1]).normalized()
            if t.length < 1e-9:
                t = pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]
            tangents.append(t.normalized())
        ref = Vector(up) if up is not None else (UP if abs(tangents[0].dot(UP)) < 0.95 else Vector((1, 0, 0)))
        normal = ref - tangents[0] * ref.dot(tangents[0])
        normal.normalize()
        normals = [normal]
        for i in range(1, n):
            rot = tangents[i - 1].rotation_difference(tangents[i])
            nn = rot @ normals[-1]
            nn = nn - tangents[i] * nn.dot(tangents[i])
            normals.append(nn.normalized())
        if closed:
            # spread the twist left over after going round, so the seam meets itself
            end = tangents[-1].rotation_difference(tangents[0]) @ normals[-1]
            angle = end.angle(normals[0]) if end.length > 0 else 0.0
            if end.cross(normals[0]).dot(tangents[0]) < 0:
                angle = -angle
            for i in range(n):
                q = Matrix.Rotation(angle * i / n, 3, tangents[i])
                normals[i] = q @ normals[i]
        if section is None:
            section = [(math.cos(2 * math.pi * k / sides), math.sin(2 * math.pi * k / sides)) for k in range(sides)]
            scale_section = True
        else:
            scale_section = False
        rings = []
        for i in range(n):
            t, nrm = tangents[i], normals[i]
            bi = t.cross(nrm).normalized()
            r = radii[i] if radii is not None else radius
            ring = []
            for (sx, sy) in section:
                k = r if scale_section else 1.0
                ring.append(pts[i] + bi * (sx * k) + nrm * (sy * k))
            rings.append(self._verts(ring))
        if closed:
            rings.append(rings[0])
            return self._rings(rings, True, False, False)
        return self._rings(rings, True, caps, caps)

    def torus(self, centre, radius, thickness, axis=UP, segments=32, sides=8, arc=(0.0, 2 * math.pi)):
        """A ring of round section (radius to the middle of the rod, thickness = rod radius) round `axis`."""
        r = frame_along(axis)
        full = abs(arc[1] - arc[0] - 2 * math.pi) < 1e-6
        count = segments if full else segments + 1
        pts = []
        for k in range(count):
            a = arc[0] + (arc[1] - arc[0]) * k / segments
            pts.append(Vector(centre) + r @ Vector((radius * math.cos(a), radius * math.sin(a), 0.0)))
        return self.sweep(pts, thickness, sides, closed=full, caps=not full)

    def prism(self, outline, z0, z1, matrix=None):
        """An outline [(x, y), ...] (anticlockwise seen from above) given thickness from z0 to z1, then moved by matrix."""
        m = matrix if matrix is not None else Matrix.Identity(4)
        bottom = self._verts([m @ Vector((x, y, z0)) for (x, y) in outline])
        top = self._verts([m @ Vector((x, y, z1)) for (x, y) in outline])
        bottom_face = self._face(list(reversed(bottom)))
        top_face = self._face(top)
        n = len(outline)
        sides = []
        for i in range(n):
            j = (i + 1) % n
            sides.append(self._face([bottom[i], bottom[j], top[j], top[i]]))
        return bottom_face, top_face, sides

    def frustum(self, centre_bottom, half_bottom, half_top, height, rotation=None):
        """A square-ish block narrowing (or widening) upwards: half sizes (x, y) at bottom and top."""
        m = to4(rotation, centre_bottom)
        bx, by = half_bottom
        tx, ty = half_top
        bottom = self._verts([m @ Vector(p) for p in ((-bx, -by, 0), (bx, -by, 0), (bx, by, 0), (-bx, by, 0))])
        top = self._verts([m @ Vector(p) for p in ((-tx, -ty, height), (tx, -ty, height), (tx, ty, height), (-tx, ty, height))])
        self._rings([bottom, top], True, True, True)

    def rock(self, centre, radius, rng, squash=(1.0, 1.0, 0.7), jitter=0.28, subdivisions=1, turn=None):
        """An irregular broken stone (a lump of coal, ore, ballast): a rough ball pushed in and out at random."""
        rot = Matrix.Rotation(turn if turn is not None else rng.uniform(0, 2 * math.pi), 4, 'Z') @ \
            Matrix.Rotation(rng.uniform(-0.5, 0.5), 4, 'X')
        m = Matrix.Translation(Vector(centre)) @ rot @ Matrix.Diagonal((radius * squash[0], radius * squash[1], radius * squash[2], 1.0))
        made = bmesh.ops.create_icosphere(self.bm, subdivisions=subdivisions, radius=1.0, matrix=Matrix.Identity(4))
        verts = made['verts']
        # facets: push whole groups of points along a few random planes, so it breaks like stone rather than wobbling
        for _ in range(3):
            n = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))).normalized()
            cut = rng.uniform(0.35, 0.8)
            for v in verts:
                d = v.co.dot(n)
                if d > cut:
                    v.co -= n * (d - cut)
        for v in verts:
            v.co *= 1.0 + rng.uniform(-jitter, jitter) * 0.5
            v.co = m @ v.co
        for v in verts:
            for f in v.link_faces:
                f.material_index = self.material_index
        return verts

    def chamfer_all(self, width, segments=1, angle=40.0):
        """Round off every sharp edge (sharper than `angle` degrees) by `width`."""
        edges = [e for e in self.bm.edges if len(e.link_faces) == 2 and e.calc_face_angle(0.0) > math.radians(angle)]
        if edges:
            bmesh.ops.bevel(self.bm, geom=edges, offset=width, offset_type='OFFSET', segments=segments,
                            profile=0.5, affect='EDGES', clamp_overlap=True)

    def transform(self, matrix):
        bmesh.ops.transform(self.bm, matrix=matrix, verts=self.bm.verts)

    def empty(self):
        return len(self.bm.faces) == 0

    # ------------------------------------------------------------------ out
    def finish(self, name, collection, materials=None, smooth=False, sharp=35.0, chamfer=0.0, chamfer_segments=1,
               matrix=None, shadow=True, normals=True, local=None, shift=0.0, rng=None):
        """Make the object: linked into `collection`, its materials set (one name or several, by material_index),
        smooth shading with edges sharper than `sharp` degrees kept crisp; `matrix` places the object (its mesh stays
        in its own coordinates). `local` (a 4x4 matrix) instead gives an object built in the part's coordinates its own
        frame (so a photographed surface's grain follows the frame's Z); `shift` then moves the mesh off the object's
        origin by up to that many metres, so neighbours show different parts of the photograph. Returns the object."""
        if local is not None:
            rr = rng or random.Random(name)
            offset = Vector((rr.uniform(-shift, shift), rr.uniform(-shift, shift), rr.uniform(-shift, shift)))
            inverse = local.inverted()
            for v in self.bm.verts:
                v.co = inverse @ v.co + offset
            matrix = local @ Matrix.Translation(-offset)
        if chamfer > 0:
            self.chamfer_all(chamfer, chamfer_segments)
        if normals:
            bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces[:])
        mesh = bpy.data.meshes.new(name)
        self.bm.to_mesh(mesh)
        self.bm.free()
        if smooth:
            mesh.shade_smooth()
            if sharp is not None:
                mesh.set_sharp_from_angle(angle=math.radians(sharp))
        else:
            mesh.shade_flat()
        obj = bpy.data.objects.new(name, mesh)
        collection.objects.link(obj)
        if matrix is not None:
            obj.matrix_world = matrix
        if materials is not None:
            if isinstance(materials, (str, bpy.types.Material)):
                materials = [materials]
            for m in materials:
                mesh.materials.append(material(m) if isinstance(m, str) else m)
        obj.visible_shadow = shadow
        store.mark(obj)
        return obj


# ---------------------------------------------------------------------- timbers and planks

def timber(collection, name, a, b, width, height, materials, rng=None, up=UP, extend=0.0, chamfer=0.006,
           roll=0.0, shift=0.6, sag=0.0, smooth=False, taper=1.0):
    """One sawn timber (or a plank) from a to b as its own object, its own Z along it so a photographed wood surface's
    grain runs along it. Width is level across, height the other way. The mesh sits off the object's origin by a
    random amount (`shift` metres at most) so neighbouring timbers show different parts of the photograph."""
    a, b = Vector(a), Vector(b)
    d = b - a
    length = d.length + 2 * extend
    r = frame_along(d, up)
    if roll:
        r = r @ Matrix.Rotation(roll, 3, 'Z')
    rr = rng or random.Random(name)
    offset = Vector((rr.uniform(-shift, shift), rr.uniform(-shift, shift), rr.uniform(-shift, shift)))
    shape = Shape()
    if sag:
        # a gentle bow (a plank sagging, a timber not quite straight): built in pieces along its length
        pieces = 6
        rings = []
        for k in range(pieces + 1):
            t = k / pieces
            z = -length / 2 + length * t
            dy = -sag * 4 * t * (1 - t)
            rings.append([offset + Vector((x, y + dy, z)) for (x, y) in
                          ((-width / 2, -height / 2), (width / 2, -height / 2), (width / 2, height / 2), (-width / 2, height / 2))])
        vr = [shape._verts(ring) for ring in rings]
        shape._rings(vr, True, True, True)
    elif taper != 1.0:
        # narrowing from a to b (a spoke, a shaft): full size at a, `taper` times it at b
        shape.frustum(offset + Vector((0.0, 0.0, -length / 2)), (width / 2, height / 2), (width * taper / 2, height * taper / 2), length)
    else:
        shape.box(offset, (width, height, length))
    centre = (a + b) / 2
    m = to4(r, centre - r @ offset)
    return shape.finish(name, collection, materials, smooth=smooth, chamfer=chamfer, matrix=m)


# ---------------------------------------------------------------------- materials

def material(name):
    """A store material by its name (brought in once)."""
    return store.material(name)


def surface_copy(name, part, **dials):
    """A copy of a store SURFACE material with its Weather dials turned for one part only, named
    'SURFACE • <name> (<part>)'. Dials: Wet, Grime, Mud height, Mud color, Edge wear, Bump, Darken; and 'Scale' for the
    picture size."""
    base = name if name.startswith('SURFACE • ') else 'SURFACE • ' + name
    copy_name = '%s (%s)' % (base, part)
    existing = bpy.data.materials.get(copy_name)
    if existing is not None:
        return existing
    m = store.material(base).copy()
    m.name = copy_name
    nodes = m.node_tree.nodes
    for key, value in dials.items():
        if key == 'Scale':
            nodes['Picture size'].inputs['Scale'].default_value = value
        else:
            nodes['Weather'].inputs[key].default_value = value
    return m


def part_material(part, what, maker):
    """A material a part makes itself ('PART • <part>: <what>'), made once per file. `maker(material, nodes, links,
    principled)` fills it in."""
    name = 'PART • %s: %s' % (part, what)
    existing = bpy.data.materials.get(name)
    if existing is not None:
        return existing
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nodes, links = m.node_tree.nodes, m.node_tree.links
    principled = nodes.get('Principled BSDF')
    maker(m, nodes, links, principled)
    return m


# small node helpers for part materials -------------------------------------------------------------------------

def node(nodes, kind, **inputs):
    n = nodes.new(kind)
    for key, value in inputs.items():
        if key in n.inputs:
            n.inputs[key].default_value = value
        else:
            setattr(n, key, value)
    return n


def own_coordinates(nodes):
    return nodes.new('ShaderNodeTexCoord').outputs['Object']


def noise_fac(nodes, links, vector, scale, detail=4.0, roughness=0.55, distortion=0.0):
    n = nodes.new('ShaderNodeTexNoise')
    n.inputs['Scale'].default_value = scale
    n.inputs['Detail'].default_value = detail
    n.inputs['Roughness'].default_value = roughness
    n.inputs['Distortion'].default_value = distortion
    links.new(vector, n.inputs['Vector'])
    return n.outputs['Fac']


def map_range(nodes, links, value, a0, a1, b0=0.0, b1=1.0):
    n = nodes.new('ShaderNodeMapRange')
    n.clamp = True
    links.new(value, n.inputs['Value'])
    n.inputs['From Min'].default_value = a0
    n.inputs['From Max'].default_value = a1
    n.inputs['To Min'].default_value = b0
    n.inputs['To Max'].default_value = b1
    return n.outputs['Result']


def mix_colour(nodes, links, factor, a, b, blend='MIX'):
    n = nodes.new('ShaderNodeMix')
    n.data_type = 'RGBA'
    n.blend_type = blend
    for socket, value in ((n.inputs[0], factor), (n.inputs[6], a), (n.inputs[7], b)):
        if isinstance(value, bpy.types.NodeSocket):
            links.new(value, socket)
        elif isinstance(value, (int, float)):
            socket.default_value = value
        else:
            socket.default_value = tuple(value) + ((1.0,) if len(value) == 3 else ())
    return n.outputs[2]


def bump(nodes, links, height, strength=0.2, distance=0.005, normal=None):
    n = nodes.new('ShaderNodeBump')
    n.inputs['Strength'].default_value = strength
    n.inputs['Distance'].default_value = distance
    links.new(height, n.inputs['Height'])
    if normal is not None:
        links.new(normal, n.inputs['Normal'])
    return n.outputs['Normal']


def math_node(nodes, links, operation, a, b=0.0, clamp=False):
    n = nodes.new('ShaderNodeMath')
    n.operation = operation
    n.use_clamp = clamp
    for socket, value in ((n.inputs[0], a), (n.inputs[1], b)):
        if isinstance(value, bpy.types.NodeSocket):
            links.new(value, socket)
        else:
            socket.default_value = value
    return n.outputs[0]


# ---------------------------------------------------------------------- lights

def point_light(collection, name, location, power, colour=(1.0, 0.62, 0.28), radius=0.04):
    data = bpy.data.lights.new(name, 'POINT')
    data.energy = power
    data.color = colour
    data.shadow_soft_size = radius
    obj = bpy.data.objects.new(name, data)
    collection.objects.link(obj)
    obj.matrix_world = Matrix.Translation(Vector(location))     # set the placement itself: .location is not read back until an update
    return obj


def tilt_all(objects, rx=0.0, ry=0.0, rz=0.0, pivot=(0.0, 0.0, 0.0)):
    """Lean or turn a whole part about a point (its foot): every object's placement changes, meshes stay as built."""
    p = Vector(pivot)
    m = Matrix.Translation(p) @ (Matrix.Rotation(rz, 4, 'Z') @ Matrix.Rotation(ry, 4, 'Y') @ Matrix.Rotation(rx, 4, 'X')) @ Matrix.Translation(-p)
    for obj in objects:
        obj.matrix_world = m @ obj.matrix_world
