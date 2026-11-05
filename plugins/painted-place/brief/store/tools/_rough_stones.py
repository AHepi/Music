"""
What this file does: the rough stones the dry-stone wall and rubble tools build from, shared by both: a stone whose
corners are pushed about and whose face bulges a little (so it catches the light like a field stone, not a brick), a
plain block (a wall's dark core), each face carrying its own stone's numbers ('stone_tone', 'stone_patch'), gathered
into one mesh; and a copy of a stone material in which each stone is a little lighter or darker by its 'stone_tone'.
It decides nothing about where stones go. (A name starting with '_' keeps it out of the store's list of tools.)

    import _rough_stones
    stones = _rough_stones.StoneMesh(origin)
    stones.stone(point, along, out, (u0, u1), (bottom_left, bottom_right), (top_left, top_right), depth, rng)
    obj = stones.make('my stones', [_rough_stones.shaded(material, 0.3)], collection, bevel=0.012)
"""

import math

import bpy
import bmesh
from mathutils import Vector

UP = Vector((0.0, 0.0, 1.0))


class StoneMesh:
    """Stones gathered into one mesh, written relative to `origin` (the object's place), each face with its stone's
    material slot, 'stone_tone' (0..1, its shade) and 'stone_patch' (0..1, which patch of a grain picture it shows)."""

    def __init__(self, origin=(0.0, 0.0, 0.0)):
        self.origin = Vector(origin)
        self.verts, self.faces, self.slots, self.tones, self.patches = [], [], [], [], []
        self.labels = {}                  # whole-number labels per face (which course, which face of a wall), 0 if not given
        self.count = 0

    def _add(self, points, faces, slot, tone, patch, labels=None):
        base = len(self.verts)
        before = len(self.faces)
        self.verts.extend(tuple(Vector(p) - self.origin) for p in points)
        for face in faces:
            self.faces.append(tuple(base + i for i in face))
            self.slots.append(slot)
            self.tones.append(tone)
            self.patches.append(patch)
        for name, value in (labels or {}).items():
            column = self.labels.setdefault(name, [])
            column.extend([0] * (before - len(column)))
            column.extend([int(value)] * len(faces))
        self.count += 1

    def stone(self, point, along, out, span, bottom, top, depth, rng, slot=0, bulge=0.008, jitter=0.008, lean=0.0,
              twist=0.0, chip=0.015, tone=None, back_span=None, labels=None):
        """One rough stone. Its face looks along `out` (a unit vector, flat) and runs along `along` (unit, flat) from
        span[0] to span[1] metres from `point` (a point on the face, its z ignored); `bottom` and `top` are the world
        heights of its lower and upper edge at its left and right ends (so a stone can follow a slope). It reaches
        `depth` metres back from the face. `lean` leans its face back by that many metres per metre up (a wall's
        batter); `twist` turns it, one end that many metres further out than the other. Its outline is broken: the
        corners chipped by up to `chip`, the middles of its edges wandering, every point pushed by up to `jitter`;
        the face bulges out by about `bulge` in the middle. `back_span` gives its back's ends when they differ from its
        face's (a corner stone whose end follows the other face of a corner). `labels` are whole numbers written on its
        faces (e.g. {'stone_course': 3})."""
        along = Vector((along[0], along[1], 0.0)).normalized()
        out = Vector((out[0], out[1], 0.0)).normalized()
        base = Vector((point[0], point[1], 0.0))
        u0, u1 = span
        width = max(u1 - u0, 1e-4)
        z_middle = (bottom[0] + bottom[1] + top[0] + top[1]) / 4.0

        def at(u, z, d):
            return base + along * u + out * (d - lean * (z - z_middle) + twist * ((u - u0) / width - 0.5)) + UP * z

        front = []
        for row in range(3):
            for column in range(3):
                t = column / 2.0
                u = u0 + width * t
                z_low = bottom[0] + (bottom[1] - bottom[0]) * t
                z_high = top[0] + (top[1] - top[0]) * t
                tall = max(z_high - z_low, 1e-4)
                z = z_low + tall * row / 2.0
                corner = row in (0, 2) and column in (0, 2)
                if corner:                                   # a chipped corner: pulled in along and towards the middle
                    du = chip * rng.uniform(0.15, 1.0) * (1.0 if column == 0 else -1.0)
                    dz = min(chip * rng.uniform(0.0, 0.8), tall * 0.3) * (1.0 if row == 0 else -1.0)
                    d = bulge * rng.uniform(-0.3, 0.15)
                elif row == 1 and column == 1:               # the middle of the face
                    du = rng.uniform(-0.08, 0.08) * width
                    dz = rng.uniform(-0.08, 0.08) * tall
                    d = bulge * rng.uniform(0.7, 1.3)
                elif row == 1:                               # the middle of an end: wanders in and out
                    du = rng.uniform(-jitter, jitter) * 1.5
                    dz = rng.uniform(-0.12, 0.12) * tall
                    d = bulge * rng.uniform(0.2, 0.6)
                else:                                        # the middle of the lower or upper edge: wanders up and down
                    du = rng.uniform(-0.18, 0.18) * width
                    dz = rng.uniform(-0.04, 0.14) * tall * (1.0 if row == 0 else -1.0)
                    d = bulge * rng.uniform(0.2, 0.6)
                front.append(at(u + du, z + dz, d + rng.uniform(-jitter, jitter) * 0.4))
        inset = min(0.012, (u1 - u0) * 0.08)
        back_ends = (u0 + inset, u1 - inset) if back_span is None else back_span
        back = []
        for u, z_pair in ((back_ends[0], (bottom[0], top[0])), (back_ends[1], (bottom[1], top[1]))):
            for z in z_pair:
                back.append(at(u + rng.uniform(-jitter, jitter), z + rng.uniform(-jitter, jitter) * 0.5,
                               -depth + rng.uniform(-jitter, jitter)))
        # back: 9 left-bottom, 10 left-top, 11 right-bottom, 12 right-top; front: row-major from the bottom left
        points = front + back
        faces = [(0, 1, 4, 3), (1, 2, 5, 4), (3, 4, 7, 6), (4, 5, 8, 7),           # the face, bulging
                 (9, 11, 2, 1, 0),                                                 # underneath
                 (10, 6, 7, 8, 12),                                                # on top
                 (9, 0, 3, 6, 10),                                                 # left end
                 (11, 12, 8, 5, 2),                                                # right end
                 (9, 10, 12, 11)]                                                  # back
        self._add(points, faces, slot, rng.random() if tone is None else tone, rng.random(), labels)

    def slab(self, centre, along, across, size, rng, lean=0.0, slot=0, taper=(0.85, 0.85), rough=0.03, tone=None, wedge=0.0,
             labels=None):
        """A slab of stone standing on edge (a coping stone): `size` = (thickness along `along`, width along `across`,
        height up), its foot's middle at `centre`, leaning over towards +along by `lean` radians; its top is narrower
        by `taper` (along, across) and uneven by up to `rough` metres. `wedge` makes it thicker on its -across side and
        thinner on its +across side by that share of its thickness (so slabs round a bend close up)."""
        along = Vector((along[0], along[1], 0.0)).normalized()
        across = Vector((across[0], across[1], 0.0)).normalized()
        thickness, width, height = size
        upright = UP * math.cos(lean) + along * math.sin(lean)
        flat = along * math.cos(lean) - UP * math.sin(lean)
        points = []
        for k, (shrink_t, shrink_w) in enumerate(((1.0, 1.0), taper)):
            for i, j in ((-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5)):
                lift = height + (rng.uniform(-rough, rough * 0.6) if k else rng.uniform(-0.01, 0.0))
                points.append(Vector(centre) + flat * (i * thickness * (1.0 - wedge * j) * shrink_t + rng.uniform(-0.006, 0.006))
                              + across * (j * width * shrink_w + rng.uniform(-0.01, 0.01)) + upright * (lift if k else 0.0))
        faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        self._add(points, faces, slot, rng.random() if tone is None else tone, rng.random(), labels)

    def solid(self, points, faces, slot=0, tone=0.5):
        """Any closed solid given as points and faces (a wall's core)."""
        self._add(points, faces, slot, tone, 0.5)

    def make(self, name, materials, collection, bevel=0.0):
        """The object, its place at `origin`; its normals turned outwards; with a Bevel modifier rounding its edges
        when `bevel` is given (metres)."""
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(self.verts, [], self.faces)
        for material in materials:
            mesh.materials.append(material)
        if self.faces:
            mesh.polygons.foreach_set('material_index', self.slots)
        for number, values in (('stone_tone', self.tones), ('stone_patch', self.patches)):
            attribute = mesh.attributes.new(number, 'FLOAT', 'FACE')
            if values:
                attribute.data.foreach_set('value', values)
        for name, values in self.labels.items():
            attribute = mesh.attributes.new(name, 'INT', 'FACE')
            values = values + [0] * (len(self.faces) - len(values))
            if values:
                attribute.data.foreach_set('value', values)
        tool = bmesh.new()
        tool.from_mesh(mesh)
        bmesh.ops.recalc_face_normals(tool, faces=tool.faces[:])
        tool.to_mesh(mesh)
        tool.free()
        mesh.update()
        obj = bpy.data.objects.new(name, mesh)
        obj.location = self.origin
        collection.objects.link(obj)
        if bevel > 0:
            modifier = obj.modifiers.new('rounded edges', 'BEVEL')
            modifier.width = bevel
            modifier.segments = 2
            modifier.limit_method = 'ANGLE'
            modifier.angle_limit = math.radians(35.0)
        return obj


def shaded(material, spread=0.3):
    """A copy of a stone material in which each stone is lighter or darker by its 'stone_tone' (the face number the
    stone tools write): its colour times 1 - spread for tone 0 up to 1 + spread for tone 1. Named '<material> •
    stone by stone'; made once for a material and spread, then shared. spread 0 returns the material itself."""
    if spread <= 0:
        return material
    name = '%s • stone by stone' % material.name
    existing = bpy.data.materials.get(name)
    if existing is not None and existing.get('pp_shades_of') == material.name and abs(existing.get('pp_spread', -1) - spread) < 1e-6:
        return existing
    copy = material.copy()
    copy.name = name
    copy['pp_shades_of'] = material.name
    copy['pp_spread'] = float(spread)
    if not copy.use_nodes or copy.node_tree is None:
        return copy
    nodes, links = copy.node_tree.nodes, copy.node_tree.links
    for principled in [n for n in nodes if n.type == 'BSDF_PRINCIPLED']:
        base = principled.inputs['Base Color']
        source = base.links[0].from_socket if base.links else None
        tone = nodes.new('ShaderNodeAttribute')
        tone.attribute_type = 'GEOMETRY'
        tone.attribute_name = 'stone_tone'
        shade = nodes.new('ShaderNodeMapRange')
        shade.inputs['To Min'].default_value = 1.0 - spread
        shade.inputs['To Max'].default_value = 1.0 + spread
        links.new(tone.outputs['Fac'], shade.inputs['Value'])
        multiply = nodes.new('ShaderNodeMix')
        multiply.data_type = 'RGBA'
        multiply.blend_type = 'MULTIPLY'
        multiply.inputs[0].default_value = 1.0
        if source is not None:
            links.new(source, multiply.inputs[6])
        else:
            multiply.inputs[6].default_value = base.default_value
        links.new(shade.outputs['Result'], multiply.inputs[7])
        links.new(multiply.outputs[2], base)
    return copy
