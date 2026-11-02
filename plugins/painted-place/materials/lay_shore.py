"""
What this file does:
Gives water its edges, wherever a builder put water: the sea, a lagoon, a harbour, a river, a pond.

  - Ground the water reaches is wet: a dark, glossy band along the waterline that fades inland, so the lamps and the
    sky are seen in it (as in the street's puddles).
  - The sea gets foam: a broken lace where the last wave runs up the sand, and broken lines of white water further out.
  - Above the waterline, where the tide leaves things, a wrack line: dried seaweed, sticks, husk fibre, shells, coral,
    pumice and a few modern scraps (bottle caps, rope ends, a sandal, a bottle); bleached driftwood lies along it.
  - Rocks, posts, walls and hulls standing in the water are dark and wet up to the high-water line, with a dark green
    slime band where the water stands.
  - Still water (a pond, a river, a canal) gets a mossy wet bank, leaves washed against it and leaves floating near
    it, instead of foam and wrack.
  - Things standing in sand (posts, piles, steps, a boat, rocks) have sand drifted against their feet.

Where the water meets the ground is found by looking straight down over the part of the place the camera sees, so it
works for a sloping beach, a flat one, a river bank or a pond in a garden, whatever the objects are called; only the
water's role matters (`sea`, or `water` bigger than a puddle).

    import lay_shore
    report = lay_shore.lay_shore(scene, roles, seen, materials, wet=1.0, litter=1.0, growth=1.0)

Everything added is named "DETAIL • shore ..." (lay_details.remove_details() removes it); materials copied to wet
things are named "... • wet to the tide line" and are put back by remove_shore_materials().
"""

import math
import random

import bmesh
import bpy
import numpy as np
from mathutils import Vector, noise

import survey as survey_module

PREFIX = 'DETAIL • shore '
SOFT_GROUND = {'sand', 'earth', 'weed', 'moss', 'pavement', 'road', 'grime', 'leaf'}
SHORE_GROUND = SOFT_GROUND | {'rock'}     # what a shore is made of; a deck, a boat, a roof or a palm top is not
SHORE_HEIGHT = 1.5                        # metres above the water: higher ground (a quay top, a cliff top) is not the shore
STANDS_IN_WATER = {'rock', 'wood', 'wall', 'plaster', 'trim', 'iron', 'rust', 'pavement'}
WET_SUFFIX = ' • wet to the tide line'
VIEW_LIMIT = 70.0


# ----------------------------------------------------------------------------------------------- reading the water

def _is_added(obj):
    return (obj.name.startswith(('FACADE •', 'DETAIL •', 'LAID •', 'LOOK •', 'TIMBER •')) or bool(obj.get('prototype'))
            or '• laid' in obj.name)


def water_bodies(scene, roles):
    """Flat water bigger than a puddle: [{'object', 'level', 'kind' ('sea' or 'still'), 'bounds'}]."""
    bodies = []
    for obj in scene.objects:
        if obj.type != 'MESH' or _is_added(obj):
            continue
        role = roles.get(obj.name)
        if role not in ('sea', 'water'):
            continue
        corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
        x0, x1 = min(c.x for c in corners), max(c.x for c in corners)
        y0, y1 = min(c.y for c in corners), max(c.y for c in corners)
        z0, z1 = min(c.z for c in corners), max(c.z for c in corners)
        if (role == 'water' and (x1 - x0) * (y1 - y0) < 6.0) or min(x1 - x0, y1 - y0) < 2.0 * (z1 - z0):
            continue        # a puddle, or water standing taller than it is wide (a waterfall, a tank): no shore
        bodies.append({'object': obj.name, 'level': z1, 'kind': 'sea' if role == 'sea' else 'still', 'bounds': (x0, x1, y0, y1)})
    return bodies


class ShoreGrid:
    """The ground and water straight below a grid over the part of the place the camera sees."""

    def __init__(self, seen, bodies, cell=None, margin=4.0):
        self.seen = seen
        body_names = {b['object'] for b in bodies}
        self.level_of = {b['object']: b['level'] for b in bodies}
        self.kind_of = {b['object']: b['kind'] for b in bodies}
        origin = seen.origin
        points = []
        for row in seen.grid:
            for hit in row:
                if hit is not None and (hit.location - origin).length < VIEW_LIMIT and (seen.is_ground(hit) or hit.obj in body_names):
                    points.append(hit.location)
        self.ok = bool(points)
        if not self.ok:
            return
        xs = [p.x for p in points]
        ys = [p.y for p in points]
        self.x0, self.x1 = min(xs) - margin, max(xs) + margin
        self.y0, self.y1 = min(ys) - margin, max(ys) + margin
        extent = max(self.x1 - self.x0, self.y1 - self.y0)
        self.cell = cell or max(0.15, extent / 380.0)
        self.nx = max(2, int((self.x1 - self.x0) / self.cell) + 1)
        self.ny = max(2, int((self.y1 - self.y0) / self.cell) + 1)
        top = max(max(b['level'] for b in bodies) + 8.0, origin.z + 4.0)
        self.highest_shore = max(b['level'] for b in bodies) + SHORE_HEIGHT
        self.kind = np.zeros((self.ny, self.nx), dtype=np.int8)        # 0 nothing, 1 ground, 2 water
        self.z = np.zeros((self.ny, self.nx), dtype=np.float32)
        self.role = np.empty((self.ny, self.nx), dtype=object)
        self.water_kind = np.zeros((self.ny, self.nx), dtype=np.int8)  # 1 sea, 2 still
        self.level = np.zeros((self.ny, self.nx), dtype=np.float32)
        scene, depsgraph = seen.scene, seen.depsgraph
        down = Vector((0, 0, -1))
        for j in range(self.ny):
            y = self.y0 + j * self.cell
            for i in range(self.nx):
                x = self.x0 + i * self.cell
                start = Vector((x, y, top))
                for _ in range(10):
                    hit, location, normal, index, obj, matrix = scene.ray_cast(depsgraph, start, down, distance=top + 60.0)
                    if not hit:
                        break
                    name = obj.name if obj is not None else ''
                    if name in body_names:
                        self.kind[j, i] = 2
                        self.z[j, i] = location.z
                        self.water_kind[j, i] = 1 if self.kind_of[name] == 'sea' else 2
                        self.level[j, i] = self.level_of[name]
                        break
                    role = seen.role(obj)
                    if (name.startswith(survey_module.LOOKED_THROUGH) or role not in SHORE_GROUND or normal.z < 0.6
                            or location.z > self.highest_shore):
                        start = location - Vector((0, 0, 0.0001))     # a roof, a deck, a boat, a palm top, a quay top: look below it
                        continue
                    self.kind[j, i] = 1
                    self.z[j, i] = location.z
                    self.role[j, i] = role
                    break
        water = self.kind == 2
        ground = self.kind == 1
        if not water.any() or not ground.any():
            self.ok = False         # the camera sees no place where this water meets ground
            return
        self.d_land, nearest = _distance(~water, self.cell)            # ground: metres to the nearest water
        self.d_sea, _ = _distance(~ground, self.cell)                  # water: metres to the nearest ground
        self.near_kind = self.water_kind[nearest[0], nearest[1]] if nearest is not None else np.full_like(self.water_kind, 1)
        self.near_level = self.level[nearest[0], nearest[1]] if nearest is not None else np.full_like(self.level, max(self.level_of.values()))
        gy, gx = np.gradient(self.d_sea)
        self.tangent_sea = np.stack([-gy, gx], axis=-1)
        gy, gx = np.gradient(self.d_land)
        self.tangent_land = np.stack([-gy, gx], axis=-1)

    def centre(self, i, j):
        return self.x0 + i * self.cell, self.y0 + j * self.cell

    def tangent(self, i, j, sea=True):
        t = (self.tangent_sea if sea else self.tangent_land)[j, i]
        length = math.hypot(t[0], t[1])
        if length < 1e-6:
            return 1.0, 0.0
        return t[0] / length, t[1] / length


def _distance(mask_nonzero, cell):
    """Distance (metres) from every cell to the nearest cell where mask_nonzero is False, and that cell's index."""
    try:
        from scipy import ndimage
        distance, indices = ndimage.distance_transform_edt(mask_nonzero, sampling=cell, return_indices=True)
        return distance.astype(np.float32), indices
    except ImportError:
        pass
    ny, nx = mask_nonzero.shape
    distance = np.where(mask_nonzero, np.inf, 0.0).astype(np.float32)
    iy, ix = np.indices((ny, nx))
    near_y, near_x = iy.copy(), ix.copy()
    steps = [(-1, 0, 1.0), (1, 0, 1.0), (0, -1, 1.0), (0, 1, 1.0), (-1, -1, 1.4142), (-1, 1, 1.4142), (1, -1, 1.4142), (1, 1, 1.4142)]
    for _ in range(int(40.0 / cell)):
        changed = False
        for dy, dx, cost in steps:
            shifted = np.full_like(distance, np.inf)
            sy = slice(max(dy, 0), ny + min(dy, 0))
            ty = slice(max(-dy, 0), ny + min(-dy, 0))
            sx = slice(max(dx, 0), nx + min(dx, 0))
            tx = slice(max(-dx, 0), nx + min(-dx, 0))
            shifted[ty, tx] = distance[sy, sx] + cost * cell
            better = shifted < distance
            if better.any():
                changed = True
                distance[better] = shifted[better]
                ny_shift = np.zeros_like(near_y)
                nx_shift = np.zeros_like(near_x)
                ny_shift[ty, tx] = near_y[sy, sx]
                nx_shift[ty, tx] = near_x[sy, sx]
                near_y[better] = ny_shift[better]
                near_x[better] = nx_shift[better]
        if not changed:
            break
    distance[np.isinf(distance)] = 1e6
    return distance, np.stack([near_y, near_x])


def _wander(x, y, scale, seed):
    """Smooth noise between about -1 and 1 over the ground."""
    return noise.noise(Vector((x * scale, y * scale, seed)))


def _in_view(seen, point, limit=VIEW_LIMIT):
    """In front of the camera, inside its frame (with a margin) and nearer than limit."""
    view = getattr(seen, '_view_inverse', None)
    if view is None:
        seen._view_inverse = view = seen.camera.matrix_world.inverted()
        seen._half_tan = math.tan(math.atan(18.0 / max(seen.camera.data.lens, 1.0)) * 1.3)
    local = view @ Vector(point)
    depth = -local.z
    if depth < 0.3 or depth > limit:
        return False
    return abs(local.x) < depth * seen._half_tan and abs(local.y) < depth * seen._half_tan


# ----------------------------------------------------------------------------------------------- materials

def _film_material():
    """A thin sheet of water lying on wet ground: clear where the ground is only damp, dark glass where it is soaked."""
    name = 'SHORE • wet ground film'
    material = bpy.data.materials.get(name)
    if material is not None:
        return material
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    principled = nodes.get('Principled BSDF')
    principled.inputs['Base Color'].default_value = (0.010, 0.011, 0.013, 1)
    principled.inputs['Roughness'].default_value = 0.07
    principled.inputs['IOR'].default_value = 1.33
    output = nodes.get('Material Output')
    attribute = nodes.new('ShaderNodeAttribute')
    attribute.attribute_type = 'GEOMETRY'
    attribute.attribute_name = 'wetness'
    clear = nodes.new('ShaderNodeBsdfTransparent')
    mix = nodes.new('ShaderNodeMixShader')
    scale = nodes.new('ShaderNodeMath')
    scale.operation = 'MULTIPLY'
    scale.inputs[1].default_value = 0.9
    links.new(attribute.outputs['Fac'], scale.inputs[0])
    links.new(scale.outputs[0], mix.inputs['Fac'])
    links.new(clear.outputs[0], mix.inputs[1])
    links.new(principled.outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], output.inputs['Surface'])
    material.diffuse_color = (0.02, 0.02, 0.025, 1)
    return material


def _foam_material():
    name = 'SHORE • sea foam'
    material = bpy.data.materials.get(name)
    if material is not None:
        return material
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    principled = nodes.get('Principled BSDF')
    output = nodes.get('Material Output')
    position = nodes.new('ShaderNodeNewGeometry').outputs['Position']
    bubbles = nodes.new('ShaderNodeTexNoise')
    bubbles.inputs['Scale'].default_value = 9.0
    bubbles.inputs['Detail'].default_value = 8.0
    links.new(position, bubbles.inputs['Vector'])
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[0].color = (0.22, 0.245, 0.26, 1)
    ramp.color_ramp.elements[1].color = (0.42, 0.45, 0.47, 1)
    links.new(bubbles.outputs['Fac'], ramp.inputs[0])
    links.new(ramp.outputs['Color'], principled.inputs['Base Color'])
    principled.inputs['Roughness'].default_value = 0.9
    attribute = nodes.new('ShaderNodeAttribute')
    attribute.attribute_type = 'GEOMETRY'
    attribute.attribute_name = 'foam'
    holes = nodes.new('ShaderNodeMapRange')       # foam is full of holes: where the bubbles are thin the water shows
    holes.inputs['From Min'].default_value, holes.inputs['From Max'].default_value = 0.38, 0.55
    links.new(bubbles.outputs['Fac'], holes.inputs['Value'])
    both = nodes.new('ShaderNodeMath')
    both.operation = 'MULTIPLY'
    links.new(attribute.outputs['Fac'], both.inputs[0])
    links.new(holes.outputs['Result'], both.inputs[1])
    clear = nodes.new('ShaderNodeBsdfTransparent')
    mix = nodes.new('ShaderNodeMixShader')
    links.new(both.outputs[0], mix.inputs['Fac'])
    links.new(clear.outputs[0], mix.inputs[1])
    links.new(principled.outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], output.inputs['Surface'])
    material.diffuse_color = (0.45, 0.48, 0.5, 1)
    return material


def _driftwood_material():
    name = 'SHORE • bleached driftwood'
    material = bpy.data.materials.get(name)
    if material is not None:
        return material
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    principled = nodes.get('Principled BSDF')
    coords = nodes.new('ShaderNodeTexCoord')
    mapping = nodes.new('ShaderNodeMapping')
    mapping.inputs['Scale'].default_value = (0.6, 16.0, 16.0)       # streaks run along the log (its own x)
    links.new(coords.outputs['Object'], mapping.inputs['Vector'])
    grain = nodes.new('ShaderNodeTexNoise')
    grain.inputs['Scale'].default_value = 1.0
    grain.inputs['Detail'].default_value = 7.0
    links.new(mapping.outputs['Vector'], grain.inputs['Vector'])
    ramp = nodes.new('ShaderNodeValToRGB')
    elements = ramp.color_ramp.elements
    elements[0].position, elements[0].color = 0.30, (0.07, 0.065, 0.06, 1)
    elements[1].position, elements[1].color = 0.62, (0.36, 0.35, 0.33, 1)
    extra = elements.new(0.42)
    extra.color = (0.22, 0.21, 0.195, 1)
    links.new(grain.outputs['Fac'], ramp.inputs[0])
    links.new(ramp.outputs['Color'], principled.inputs['Base Color'])
    principled.inputs['Roughness'].default_value = 0.82
    bump = nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.6
    bump.inputs['Distance'].default_value = 0.004
    links.new(grain.outputs['Fac'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], principled.inputs['Normal'])
    material.diffuse_color = (0.3, 0.29, 0.27, 1)
    return material


def _simple(name, colour, roughness, high=None, scale=50.0):
    material = bpy.data.materials.get(name)
    if material is not None:
        return material
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    principled = nodes.get('Principled BSDF')
    principled.inputs['Roughness'].default_value = roughness
    if high is None:
        principled.inputs['Base Color'].default_value = (*colour, 1)
    else:
        position = nodes.new('ShaderNodeNewGeometry').outputs['Position']
        tex = nodes.new('ShaderNodeTexNoise')
        tex.inputs['Scale'].default_value = scale
        tex.inputs['Detail'].default_value = 4.0
        links.new(position, tex.inputs['Vector'])
        ramp = nodes.new('ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].color = (*colour, 1)
        ramp.color_ramp.elements[1].color = (*high, 1)
        links.new(tex.outputs['Fac'], ramp.inputs[0])
        links.new(ramp.outputs['Color'], principled.inputs['Base Color'])
    material.diffuse_color = (*colour, 1)
    return material


def wet_to_the_tide_line(material, level, rise, sea):
    """A copy of a material that is dark and glossy below the high-water line (level + rise) and carries a dark
    green slime band where the water stands. Named by the water's level, so the same material by the sea and by a
    river gets two copies, and a moved water level gets a fresh one."""
    name = '%s%s (water at %+.2f m%s)' % (material.name, WET_SUFFIX, level, ', sea' if sea else '')
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    wet = material.copy()
    wet.name = name
    if not wet.use_nodes:
        return wet
    nodes, links = wet.node_tree.nodes, wet.node_tree.links
    position = nodes.new('ShaderNodeNewGeometry').outputs['Position']
    separate = nodes.new('ShaderNodeSeparateXYZ')
    links.new(position, separate.inputs['Vector'])
    soaked = nodes.new('ShaderNodeMapRange')
    soaked.inputs['From Min'].default_value = level + rise
    soaked.inputs['From Max'].default_value = level + rise - 0.3
    links.new(separate.outputs['Z'], soaked.inputs['Value'])
    distance = nodes.new('ShaderNodeMath')
    distance.operation = 'ABSOLUTE'
    offset = nodes.new('ShaderNodeMath')
    offset.operation = 'SUBTRACT'
    links.new(separate.outputs['Z'], offset.inputs[0])
    offset.inputs[1].default_value = level + (0.12 if sea else 0.03)
    links.new(offset.outputs[0], distance.inputs[0])
    slime = nodes.new('ShaderNodeMapRange')
    slime.inputs['From Min'].default_value = 0.22 if sea else 0.07
    slime.inputs['From Max'].default_value = 0.0
    slime.inputs['To Max'].default_value = 0.85
    links.new(distance.outputs[0], slime.inputs['Value'])
    for principled in [n for n in nodes if n.type == 'BSDF_PRINCIPLED']:
        base = principled.inputs['Base Color']
        source = base.links[0].from_socket if base.links else None
        darker = nodes.new('ShaderNodeMix')
        darker.data_type = 'RGBA'
        darker.blend_type = 'MULTIPLY'
        links.new(soaked.outputs['Result'], darker.inputs[0])
        if source is not None:
            links.new(source, darker.inputs[6])
        else:
            darker.inputs[6].default_value = base.default_value
        darker.inputs[7].default_value = (0.42, 0.42, 0.42, 1)
        green = nodes.new('ShaderNodeMix')
        green.data_type = 'RGBA'
        links.new(slime.outputs['Result'], green.inputs[0])
        links.new(darker.outputs[2], green.inputs[6])
        green.inputs[7].default_value = (0.018, 0.028, 0.012, 1)
        links.new(green.outputs[2], base)
        rough = principled.inputs['Roughness']
        rough_source = rough.links[0].from_socket if rough.links else None
        glossy = nodes.new('ShaderNodeMix')
        glossy.data_type = 'FLOAT'
        links.new(soaked.outputs['Result'], glossy.inputs[0])
        if rough_source is not None:
            links.new(rough_source, glossy.inputs[2])
        else:
            glossy.inputs[2].default_value = rough.default_value
        glossy.inputs[3].default_value = 0.14
        links.new(glossy.outputs[0], rough)
    return wet


def remove_shore_materials(scene):
    """Put back the builder's materials on things that were given wet copies: the wet copy was hung on the object
    only, so pointing its slots back at the mesh's own materials restores them (other objects sharing the mesh were
    never touched)."""
    for obj in scene.objects:
        if obj.type != 'MESH' or not obj.get('shore_wet'):
            continue
        for slot in obj.material_slots:
            if slot.link == 'OBJECT' and slot.material is not None and WET_SUFFIX in slot.material.name:
                slot.material = None
                slot.link = 'DATA'
        del obj['shore_wet']


# ----------------------------------------------------------------------------------------------- small shapes

def _blob(verts, faces, values, x, y, z, along, across, angle, rng, value=1.0, corners=11):
    """A flat ragged ellipse: centre value `value`, rim value near nothing (so it fades at its edge)."""
    start = len(verts)
    verts.append((x, y, z))
    values.append(value)
    c, s = math.cos(angle), math.sin(angle)
    phase = rng.uniform(0, math.tau)
    for k in range(corners):
        a = math.tau * k / corners
        r = 1.0 + 0.22 * math.sin(3 * a + phase) + 0.12 * math.sin(5 * a + phase * 1.7) + rng.uniform(-0.08, 0.08)
        lx, ly = math.cos(a) * along * r, math.sin(a) * across * r
        verts.append((x + lx * c - ly * s, y + lx * s + ly * c, z))
        values.append(value * rng.uniform(0.0, 0.18))
    for k in range(corners):
        faces.append((start, start + 1 + k, start + 1 + (k + 1) % corners))


def _mesh(name, verts, faces, materials, collection, role, attribute=None, values=None, slots=None, shadow=True):
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    for material in materials:
        data.materials.append(material)
    if slots is not None:
        for polygon, slot in zip(data.polygons, slots):
            polygon.material_index = slot
    if attribute is not None:
        layer = data.attributes.new(attribute, 'FLOAT', 'POINT')
        layer.data.foreach_set('value', values)
    data.update()
    obj = bpy.data.objects.new(name, data)
    obj['place_role'] = role
    obj.visible_shadow = shadow
    collection.objects.link(obj)
    return obj


def _tube(verts, faces, path, radii, sides, slots, slot):
    """A tube along a path of points with a radius at each (closed at both ends)."""
    rings = []
    for k, (p, r) in enumerate(zip(path, radii)):
        forward = (path[min(k + 1, len(path) - 1)] - path[max(k - 1, 0)]).normalized()
        side = forward.cross(Vector((0, 0, 1)))
        if side.length < 1e-4:
            side = forward.cross(Vector((0, 1, 0)))
        side.normalize()
        up = side.cross(forward).normalized()
        ring = []
        for s in range(sides):
            a = math.tau * s / sides
            ring.append(len(verts))
            verts.append(tuple(p + (side * math.cos(a) + up * math.sin(a)) * r))
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for s in range(sides):
            faces.append((a[s], a[(s + 1) % sides], b[(s + 1) % sides], b[s]))
            slots.append(slot)
    faces.append(tuple(reversed(rings[0])))
    slots.append(slot)
    faces.append(tuple(rings[-1]))
    slots.append(slot)


def _wrack_prototypes(scene):
    """What the tide leaves: seaweed, sticks, husk fibre, shells, coral, pumice (sizes written into the shapes)."""
    name = PREFIX + 'wrack prototypes'
    existing = bpy.data.collections.get(name)
    if existing is not None:
        return existing
    collection = bpy.data.collections.new(name)
    scene.collection.children.link(collection)
    weed = _simple('SHORE • dried seaweed', (0.022, 0.026, 0.012), 0.55, (0.075, 0.068, 0.028))
    stick = _simple('SHORE • grey sticks', (0.12, 0.11, 0.095), 0.8, (0.25, 0.24, 0.22))
    fibre = _simple('SHORE • husk fibre', (0.07, 0.045, 0.022), 0.9, (0.16, 0.11, 0.06), scale=120.0)
    shell = _simple('SHORE • bleached shell', (0.20, 0.185, 0.16), 0.6, (0.34, 0.32, 0.28), scale=60.0)
    coral = _simple('SHORE • coral rubble', (0.17, 0.16, 0.145), 0.9, (0.28, 0.265, 0.24), scale=80.0)
    pumice = _simple('SHORE • pumice', (0.20, 0.20, 0.19), 0.95, (0.33, 0.32, 0.30), scale=90.0)
    made = []

    def add(label, verts, faces, material, number):
        data = bpy.data.meshes.new(PREFIX + label)
        data.from_pydata(verts, [], faces)
        data.materials.append(material)
        data.update()
        obj = bpy.data.objects.new(data.name, data)
        obj.location = (0, 0, -300 - number * 1.5)
        obj['prototype'] = True
        collection.objects.link(obj)
        made.append(obj)

    number = 0
    for i in range(8):                                   # seaweed: dark ribbons lying in curls
        r = random.Random(7100 + i)
        verts, faces = [], []
        length = r.uniform(0.12, 0.45)
        width = r.uniform(0.008, 0.03)
        steps = 9
        heading = r.uniform(0, math.tau)
        x = y = 0.0
        for k in range(steps):
            heading += r.uniform(-0.7, 0.7)
            x += math.cos(heading) * length / steps
            y += math.sin(heading) * length / steps
            nx, ny = -math.sin(heading) * width, math.cos(heading) * width
            verts.extend([(x - nx, y - ny, 0.002 + r.uniform(0, 0.004)), (x + nx, y + ny, 0.002 + r.uniform(0, 0.004))])
        for k in range(steps - 1):
            faces.append((2 * k, 2 * k + 1, 2 * k + 3, 2 * k + 2))
        add('seaweed %d' % i, verts, faces, weed, number)
        number += 1
    for i in range(6):                                   # sticks: thin, bent, grey
        r = random.Random(7200 + i)
        verts, faces, slots = [], [], []
        length = r.uniform(0.08, 0.38)
        bend = r.uniform(-0.04, 0.04)
        radius = r.uniform(0.004, 0.012)
        path = [Vector(((t - 0.5) * length, bend * math.sin(t * math.pi), radius)) for t in (k / 5 for k in range(6))]
        _tube(verts, faces, path, [radius * (1 - 0.4 * k / 5) for k in range(6)], 5, slots, 0)
        add('stick %d' % i, verts, faces, stick, number)
        number += 1
    for i in range(4):                                   # husk fibre: low brown tangles
        r = random.Random(7300 + i)
        size = r.uniform(0.04, 0.10)
        count = r.randint(7, 10)
        verts = [(math.cos(math.tau * k / count) * size * r.uniform(0.5, 1.0), math.sin(math.tau * k / count) * size * r.uniform(0.5, 1.0), 0.0)
                 for k in range(count)] + [(0, 0, size * r.uniform(0.25, 0.5))]
        faces = [tuple(range(count - 1, -1, -1))] + [(k, (k + 1) % count, count) for k in range(count)]
        add('husk fibre %d' % i, verts, faces, fibre, number)
        number += 1
    for i in range(5):                                   # shells: little fans
        r = random.Random(7400 + i)
        size = r.uniform(0.012, 0.035)
        verts, faces = [(0, 0, size * 0.45)], []
        for k in range(7):
            a = -0.9 + 1.8 * k / 6
            verts.append((math.sin(a) * size, math.cos(a) * size, 0.0))
        for k in range(6):
            faces.append((0, k + 1, k + 2))
        add('shell %d' % i, verts, faces, shell, number)
        number += 1
    for i in range(4):                                   # coral and pumice: small lumps
        r = random.Random(7500 + i)
        size = r.uniform(0.02, 0.06)
        count = r.randint(5, 8)
        verts = [(math.cos(math.tau * k / count) * size * r.uniform(0.6, 1.0), math.sin(math.tau * k / count) * size * r.uniform(0.6, 1.0), 0)
                 for k in range(count)] + [(0, 0, size * r.uniform(0.4, 0.9))]
        faces = [tuple(range(count - 1, -1, -1))] + [(k, (k + 1) % count, count) for k in range(count)]
        add(('coral %d' if i < 2 else 'pumice %d') % i, verts, faces, coral if i < 2 else pumice, number)
        number += 1
    return collection


def _scrap_prototypes(scene):
    """Today's scraps in the wrack: bottle caps, rope ends, a sandal, a plastic bottle."""
    name = PREFIX + 'scrap prototypes'
    existing = bpy.data.collections.get(name)
    if existing is not None:
        return existing
    collection = bpy.data.collections.new(name)
    scene.collection.children.link(collection)
    red = _simple('SHORE • faded red plastic', (0.22, 0.04, 0.03), 0.5)
    blue = _simple('SHORE • faded blue plastic', (0.03, 0.08, 0.16), 0.5)
    pale = _simple('SHORE • clouded bottle plastic', (0.32, 0.36, 0.38), 0.25)
    rope_orange = _simple('SHORE • orange rope', (0.30, 0.10, 0.02), 0.85, (0.42, 0.16, 0.04), scale=200.0)
    rope_blue = _simple('SHORE • blue rope', (0.02, 0.06, 0.14), 0.85, (0.05, 0.12, 0.24), scale=200.0)
    black = _simple('SHORE • black rubber', (0.012, 0.012, 0.014), 0.7)

    def add(label, verts, faces, material, number):
        data = bpy.data.meshes.new(PREFIX + label)
        data.from_pydata(verts, [], faces)
        data.materials.append(material)
        data.update()
        obj = bpy.data.objects.new(data.name, data)
        obj.location = (0, 0, -340 - number * 1.5)
        obj['prototype'] = True
        collection.objects.link(obj)

    number = 0
    for material in (red, blue):                         # bottle caps
        verts, faces, slots = [], [], []
        _tube(verts, faces, [Vector((0, 0, 0.0)), Vector((0, 0, 0.012))], [0.015, 0.015], 10, slots, 0)
        add('bottle cap %d' % number, verts, faces, material, number)
        number += 1
    for k, material in enumerate((rope_orange, rope_blue)):   # rope ends
        r = random.Random(7600 + k)
        verts, faces, slots = [], [], []
        length = r.uniform(0.12, 0.3)
        path = [Vector(((t - 0.5) * length, 0.03 * math.sin(t * 4 + k), 0.008)) for t in (q / 7 for q in range(8))]
        _tube(verts, faces, path, [0.008] * 8, 6, slots, 0)
        add('rope end %d' % k, verts, faces, material, number)
        number += 1
    outline = [(-0.13, 0.0), (-0.11, 0.04), (-0.05, 0.05), (0.05, 0.045), (0.12, 0.035), (0.135, 0.0), (0.12, -0.035),
               (0.05, -0.045), (-0.05, -0.04), (-0.11, -0.035)]
    verts = [(x, y, 0.0) for x, y in outline] + [(x, y, 0.016) for x, y in outline]
    n = len(outline)
    sandal_faces = [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))] + [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
    add('sandal', verts, sandal_faces, blue, number)
    number += 1
    verts, faces, slots = [], [], []
    _tube(verts, faces, [Vector((-0.11, 0, 0.033)), Vector((0.06, 0, 0.033)), Vector((0.09, 0, 0.033)), Vector((0.12, 0, 0.033))],
          [0.033, 0.033, 0.015, 0.013], 10, slots, 0)
    add('plastic bottle', verts, faces, pale, number)
    number += 1
    verts = [(x * 0.9, y * 0.9, 0.0) for x, y in outline] + [(x * 0.9, y * 0.9, 0.012) for x, y in outline]
    add('sandal sole', verts, sandal_faces, black, number)
    return collection


def _driftwood(name, rng, length, radius, collection, material):
    """A bleached log or branch, lying along its own x: tapered, bent, knotted, with a broken branch or two."""
    verts, faces, slots = [], [], []
    steps = 10
    bend = rng.uniform(-0.12, 0.12) * length
    path, radii = [], []
    for k in range(steps):
        t = k / (steps - 1)
        path.append(Vector(((t - 0.5) * length, bend * math.sin(t * math.pi) + rng.uniform(-0.01, 0.01), 0.0)))
        r = radius * (1.0 - 0.45 * t) * (1 + 0.12 * math.sin(t * 13 + rng.uniform(0, 3)))
        radii.append(max(r, radius * 0.25))
    _tube(verts, faces, path, radii, 7, slots, 0)
    for _ in range(rng.randint(1, 3)):
        k = rng.randint(2, steps - 3)
        side = rng.choice((-1, 1))
        a = rng.uniform(0.5, 1.1) * side
        direction = Vector((math.cos(a), math.sin(a), rng.uniform(-0.1, 0.25))).normalized()
        stub = rng.uniform(0.12, 0.45) * length / 2
        start = path[k]
        _tube(verts, faces, [start, start + direction * stub * 0.5, start + direction * stub],
              [radii[k] * 0.45, radii[k] * 0.35, radii[k] * 0.2], 5, slots, 0)
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    data.materials.append(material)
    data.update()
    obj = bpy.data.objects.new(name, data)
    obj['place_role'] = 'wood'
    collection.objects.link(obj)
    return obj


def _instance(name, points, prototypes, collection, role, seed, scale=((0.6, 0.6, 0.6), (1.4, 1.4, 1.2))):
    import lay_details
    return lay_details._instance_randomly(name, points, prototypes, collection, role, seed, scale_range=scale)


# ----------------------------------------------------------------------------------------------- the layers

def wet_ground(grid, collection, rng, amount, seed=11):
    """The dark, glossy band along the waterline, as a thin film of water on the ground that fades inland."""
    if amount <= 0:
        return {'wet_ground_cells': 0}
    ny, nx = grid.kind.shape
    wet = np.zeros((ny, nx), dtype=np.float32)
    seen = grid.seen
    for j, i in zip(*np.nonzero((grid.kind == 1) & (grid.d_land <= 9.0))):
        if grid.role[j, i] not in SOFT_GROUND:
            continue
        d = float(grid.d_land[j, i])
        x, y = grid.centre(i, j)
        sea = grid.near_kind[j, i] == 1
        width = (3.0 if sea else 0.55) * amount * (0.75 + 0.35 * _wander(x, y, 0.09, seed))
        if d > width:
            continue
        level = grid.near_level[j, i]
        rise = 0.9 if sea else 0.25
        height = min(max((level + rise - grid.z[j, i]) / (rise * 0.6), 0.0), 1.0)
        patches = 0.72 + 0.28 * _wander(x, y, 0.8, seed + 3)
        wet[j, i] = (1.0 - d / width) ** 0.8 * height * patches
    keep = wet > 0.02
    near = keep.copy()
    near[1:, :] |= keep[:-1, :]
    near[:-1, :] |= keep[1:, :]
    near[:, 1:] |= keep[:, :-1]
    near[:, :-1] |= keep[:, 1:]
    near &= grid.kind == 1
    index = -np.ones((ny, nx), dtype=np.int64)
    verts, values = [], []
    # water lies flat: the film follows the beach's slope but not its ripples (a 5 x 5 average of the ground)
    ground_z = np.where(grid.kind == 1, grid.z, 0.0).astype(np.float64)
    weight = (grid.kind == 1).astype(np.float64)
    total, count = np.zeros_like(ground_z), np.zeros_like(weight)
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            total += np.roll(np.roll(ground_z, dy, axis=0), dx, axis=1)
            count += np.roll(np.roll(weight, dy, axis=0), dx, axis=1)
    smooth_z = np.where(count > 0, total / np.maximum(count, 1), ground_z)
    for j, i in zip(*np.nonzero(near)):
        x, y = grid.centre(i, j)
        if not _in_view(seen, (x, y, float(grid.z[j, i])), VIEW_LIMIT + 5):
            continue
        index[j, i] = len(verts)
        verts.append((x, y, max(float(smooth_z[j, i]), float(grid.z[j, i])) + 0.01))
        values.append(float(wet[j, i]))
    faces = []
    for j in range(ny - 1):
        for i in range(nx - 1):
            a, b, c, d = index[j, i], index[j, i + 1], index[j + 1, i + 1], index[j + 1, i]
            if min(a, b, c, d) >= 0 and max(abs(grid.z[j, i] - grid.z[j + 1, i + 1]), abs(grid.z[j, i + 1] - grid.z[j + 1, i])) < 0.25:
                faces.append((int(a), int(b), int(c), int(d)))
    if faces:
        film = _mesh(PREFIX + 'wet ground along the water', verts, faces, [_film_material()], collection, 'water', 'wetness', values, shadow=False)
        for polygon in film.data.polygons:
            polygon.use_smooth = True
    return {'wet_ground_cells': int(keep.sum())}


def foam(grid, collection, rng, amount, seed=23):
    """Sea only: a broken lace where the last wave runs up, a thin edge at the waterline, broken lines of white water
    further out, each with a fainter trail behind it."""
    if amount <= 0:
        return {'foam_patches': 0}
    verts, faces, values = [], [], []
    seen = grid.seen
    ny, nx = grid.kind.shape
    lines = (2.4, 5.6, 10.5, 17.0)
    count = 0
    cell = grid.cell
    for j, i in zip(*np.nonzero((grid.kind == 2) & (grid.water_kind == 1) & (grid.d_sea <= 22.0))):
        d = float(grid.d_sea[j, i])
        x, y = grid.centre(i, j)
        z = float(grid.level[j, i]) + 0.008
        if not _in_view(seen, (x, y, z)):
            continue
        tx, ty = grid.tangent(i, j, sea=True)
        angle = math.atan2(ty, tx)
        if d < 0.9:
            if rng.random() < (1 - d / 0.9) ** 1.4 * (0.55 + 0.45 * _wander(x, y, 1.1, seed)) * amount:
                _blob(verts, faces, values, x + rng.uniform(-cell, cell) / 2, y + rng.uniform(-cell, cell) / 2, z,
                      rng.uniform(0.06, 0.24), rng.uniform(0.04, 0.14), angle + rng.uniform(-0.6, 0.6), rng)
                count += 1
        if d <= 1.6 * cell and rng.random() < 0.45 * amount:
            _blob(verts, faces, values, x, y, z + 0.002, rng.uniform(0.2, 0.6), rng.uniform(0.02, 0.06), angle, rng, value=0.7)
            count += 1
        for k, line in enumerate(lines):
            here = line * (0.85 + 0.3 * _wander(x, y, 0.05, seed + k))
            if abs(d - here) > 0.75 * cell:
                continue
            if _wander(x, y, 0.35, seed + 10 + k) < -0.12 or rng.random() > 0.55 * amount:
                continue
            width = rng.uniform(0.07, 0.24) * (1.0 + 0.25 * k)
            _blob(verts, faces, values, x, y, z + 0.004, rng.uniform(0.5, 1.6), width, angle + rng.uniform(-0.08, 0.08), rng)
            count += 1
            if rng.random() < 0.6:
                gx = grid.tangent_sea[j, i]
                back = Vector((gx[1], -gx[0], 0))      # away from the shore: the gradient of distance-to-ground
                if back.length > 1e-6:
                    back.normalize()
                    trail = rng.uniform(0.25, 0.8)
                    _blob(verts, faces, values, x + back.x * trail, y + back.y * trail, z + 0.001, rng.uniform(0.6, 1.8),
                          rng.uniform(0.2, 0.6), angle, rng, value=0.32)
                    count += 1
        if count > 9000:
            break
    # the last wave's reach: a wandering line of thin foam up the wet sand, and lace below it
    swash = 0
    for j, i in zip(*np.nonzero((grid.kind == 1) & (grid.near_kind == 1) & (grid.d_land < 2.0))):
        if grid.role[j, i] not in SOFT_GROUND or grid.z[j, i] > grid.near_level[j, i] + 0.6:
            continue
        d = float(grid.d_land[j, i])
        x, y = grid.centre(i, j)
        # scalloped and broken: two wanders, and gaps where a third is low
        reach = 0.8 + 0.45 * _wander(x, y, 0.4, seed + 30) + 0.3 * abs(_wander(x, y, 1.4, seed + 31))
        z = float(grid.z[j, i]) + 0.016
        if not _in_view(seen, (x, y, z)):
            continue
        tx, ty = grid.tangent(i, j, sea=False)
        angle = math.atan2(ty, tx)
        if abs(d - reach) < 0.6 * cell and _wander(x, y, 0.9, seed + 32) > -0.2 and rng.random() < 0.5 * amount:
            _blob(verts, faces, values, x, y, z, rng.uniform(0.15, 0.45), rng.uniform(0.012, 0.035), angle + rng.uniform(-0.3, 0.3), rng, value=0.5)
            swash += 1
        elif d < reach and rng.random() < 0.12 * amount * (1 - d / max(reach, 0.1)):
            _blob(verts, faces, values, x + rng.uniform(-cell, cell) / 2, y + rng.uniform(-cell, cell) / 2, z,
                  rng.uniform(0.05, 0.18), rng.uniform(0.03, 0.08), angle + rng.uniform(-0.8, 0.8), rng, value=0.3)
            swash += 1
    if faces:
        _mesh(PREFIX + 'sea foam', verts, faces, [_foam_material()], collection, 'water', 'foam', values, shadow=False)
    return {'foam_patches': count, 'swash_patches': swash}


def wrack_and_driftwood(grid, collection, rng, amount, seed=37, growth=1.0, today=False):
    """The sea's tide line: debris thick along a wandering line above the wet band, thinning either side; driftwood
    along and above it near the camera. Still water instead gets leaves against the bank and floating near it."""
    seen = grid.seen
    ny, nx = grid.kind.shape
    points, scraps, logs_wanted = [], [], []
    leaf_verts, leaf_faces, leaf_slots = [], [], []
    moss_verts, moss_faces, moss_values = [], [], []
    cell = grid.cell
    area = cell * cell
    wanted = ((grid.kind == 1) & (grid.d_land <= 12.0)) | ((grid.kind == 2) & (grid.water_kind == 2) & (grid.d_sea < 1.6))
    for j, i in zip(*np.nonzero(wanted)):
        kind = grid.kind[j, i]
        x, y = grid.centre(i, j)
        if kind == 1 and grid.role[j, i] in SOFT_GROUND:
            d = float(grid.d_land[j, i])
            if d > 12.0:
                continue
            z = float(grid.z[j, i])
            if z > float(grid.near_level[j, i]) + (1.2 if grid.near_kind[j, i] == 1 else 0.4):
                continue        # the tide and the bank do not reach up there
            if not _in_view(seen, (x, y, z), 45.0):
                continue
            if grid.near_kind[j, i] == 1:
                width = 3.0 * (0.75 + 0.35 * _wander(x, y, 0.09, 11))
                line = width + 1.0 + 0.8 * _wander(x, y, 0.15, seed)
                density = 60.0 * math.exp(-0.5 * ((d - line) / 0.38) ** 2) * (0.45 + 0.55 * _wander(x, y, 0.7, seed + 1)) + 0.5
                expected = density * area * amount
                while expected > 0:
                    if rng.random() < min(expected, 1.0):
                        px, py = x + rng.uniform(-cell, cell) / 2, y + rng.uniform(-cell, cell) / 2
                        (scraps if today and rng.random() < 0.035 else points).append((px, py, z))
                    expected -= 1.0
                if abs(d - line) < 1.2 or (line < d < line + 4.0 and rng.random() < 0.12):
                    logs_wanted.append((x, y, z, i, j))
            elif d < 0.45:
                if rng.random() < 0.5 * amount:
                    start = len(leaf_verts)
                    _leaf(leaf_verts, leaf_faces, x + rng.uniform(-cell, cell) / 2, y + rng.uniform(-cell, cell) / 2, z + 0.004, rng)
                    leaf_slots.extend([0 if rng.random() < 0.6 else 1] * (len(leaf_faces) - len(leaf_slots)))
                if rng.random() < 0.55 * growth:
                    _blob(moss_verts, moss_faces, moss_values, x, y, z + 0.003, rng.uniform(0.05, 0.2), rng.uniform(0.04, 0.12),
                          rng.uniform(0, math.tau), rng)
        elif kind == 2 and grid.water_kind[j, i] == 2:
            d = float(grid.d_sea[j, i])
            if d < 1.6 and rng.random() < 0.3 * amount * (1 - d / 1.6) and _in_view(seen, (x, y, float(grid.level[j, i])), 40.0):
                _leaf(leaf_verts, leaf_faces, x + rng.uniform(-cell, cell) / 2, y + rng.uniform(-cell, cell) / 2,
                      float(grid.level[j, i]) + 0.003, rng)
                leaf_slots.extend([0 if rng.random() < 0.5 else 1] * (len(leaf_faces) - len(leaf_slots)))
    placed = []
    for collection_points, prototypes, label, seed_offset in ((points, _wrack_prototypes, 'wrack: seaweed, sticks, husk fibre, shells, coral', 0),
                                                              (scraps, _scrap_prototypes, 'wrack: caps, rope ends, a sandal, a bottle', 9)):
        grounded = []
        for px, py, pz in collection_points:
            ground = seen.ground_under(Vector((px, py, pz)), above=0.4)
            if ground is not None and abs(ground[0] - pz) < 0.3:
                grounded.append((px, py, ground[0] + 0.002))
        if grounded:
            _instance(PREFIX + label, grounded, prototypes(seen.scene), collection, 'grime', 641 + seed_offset,
                      scale=((0.8, 0.8, 0.7), (2.1, 2.1, 1.6)) if seed_offset == 0 else ((0.8, 0.8, 0.8), (1.2, 1.2, 1.2)))
        placed.append(len(grounded))
    logs = 0
    if logs_wanted and amount > 0:
        import scans
        material = scans.driftwood() or _driftwood_material()
        rng.shuffle(logs_wanted)
        chosen = []
        camera = seen.origin
        for x, y, z, i, j in logs_wanted:
            distance = math.hypot(x - camera.x, y - camera.y)
            if distance < 3.0 or distance > 32.0:
                continue
            if any(math.hypot(x - a, y - b) < 2.6 for a, b, *_ in chosen):
                continue
            chosen.append((x, y, z, i, j))
            if len(chosen) >= max(1, int(round(6 * amount))):
                break
        for k, (x, y, z, i, j) in enumerate(chosen):
            length = rng.uniform(0.7, 3.0)
            radius = rng.uniform(0.035, 0.14) * (0.6 + 0.4 * length / 3.0)
            obj = _driftwood(PREFIX + 'driftwood %d' % k, rng, length, radius, collection, material)
            scans.mark_object(obj, grain_axis=0)        # the log lies along its own x
            tx, ty = grid.tangent(i, j, sea=False)
            yaw = math.atan2(ty, tx) + rng.uniform(-0.6, 0.6)
            ends = []
            for side in (-0.5, 0.5):
                ex, ey = x + math.cos(yaw) * length * side, y + math.sin(yaw) * length * side
                ground = seen.ground_under(Vector((ex, ey, z)), above=0.6)
                ends.append(ground[0] if ground is not None else z)
            pitch = math.atan2(ends[1] - ends[0], length)
            obj.location = (x, y, (ends[0] + ends[1]) / 2 + radius * 0.55)
            obj.rotation_euler = (rng.uniform(-0.15, 0.15), -pitch, yaw)
            logs += 1
    if leaf_faces:
        import apply_by_role
        leaves = apply_by_role.append_materials(apply_by_role.DETAIL_LEAVES)
        obj = _mesh(PREFIX + 'leaves at the bank and on the water', leaf_verts, leaf_faces, [leaves[n] for n in apply_by_role.DETAIL_LEAVES],
                    collection, 'leaf', slots=leaf_slots)
    if moss_faces:
        import apply_by_role
        moss = apply_by_role.append_materials([apply_by_role.DETAIL_MATERIALS['moss']])[apply_by_role.DETAIL_MATERIALS['moss']]
        _mesh(PREFIX + 'moss along the bank', moss_verts, moss_faces, [moss], collection, 'moss')
    return {'wrack_pieces': placed[0] if placed else 0, 'modern_scraps': placed[1] if len(placed) > 1 else 0,
            'driftwood_logs': logs, 'bank_leaves': len(leaf_faces) // 4}


def _leaf(verts, faces, x, y, z, rng):
    rad = rng.uniform(0.015, 0.05)
    length = rad * rng.uniform(1.3, 2.3)
    a = rng.random() * math.tau
    dx, dy = math.cos(a), math.sin(a)
    px, py = -dy, dx
    k = len(verts)
    verts.extend([(x - dx * length, y - dy * length, z), (x + px * rad, y + py * rad, z + 0.001),
                  (x + dx * length, y + dy * length, z + 0.001), (x - px * rad, y - py * rad, z + 0.002), (x, y, z + 0.004)])
    for b in range(4):
        faces.append((k + b, k + (b + 1) % 4, k + 4))


def wet_standing_things(grid, scene, roles, bodies):
    """Rocks, posts, walls and hulls that stand in the water or at its edge: wet copies of their materials."""
    changed = 0
    if not grid.ok:
        return {'things_wet_to_the_tide_line': 0}
    water = grid.kind == 2
    for obj in scene.objects:
        if obj.type != 'MESH' or _is_added(obj) or roles.get(obj.name) not in STANDS_IN_WATER or not obj.material_slots:
            continue
        corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
        x0, x1 = min(c.x for c in corners), max(c.x for c in corners)
        y0, y1 = min(c.y for c in corners), max(c.y for c in corners)
        z0, z1 = min(c.z for c in corners), max(c.z for c in corners)
        i0 = int((x0 - 2.0 - grid.x0) / grid.cell)
        i1 = int((x1 + 2.0 - grid.x0) / grid.cell) + 1
        j0 = int((y0 - 2.0 - grid.y0) / grid.cell)
        j1 = int((y1 + 2.0 - grid.y0) / grid.cell) + 1
        i0, j0 = max(i0, 0), max(j0, 0)
        i1, j1 = min(i1, grid.nx), min(j1, grid.ny)
        if i0 >= i1 or j0 >= j1 or not water[j0:j1, i0:i1].any():
            continue
        kinds = grid.water_kind[j0:j1, i0:i1][water[j0:j1, i0:i1]]
        levels = grid.level[j0:j1, i0:i1][water[j0:j1, i0:i1]]
        sea = bool((kinds == 1).any())
        level = float(levels.max())
        rise = 0.9 if sea else 0.2
        if z0 > level + rise or z1 < level - 0.05:
            continue
        for slot in obj.material_slots:
            own = slot.material
            if own is None or WET_SUFFIX in own.name:
                continue
            slot.link = 'OBJECT'            # this object only: another object sharing the mesh, on dry land, stays dry
            slot.material = wet_to_the_tide_line(own, level, rise, sea)
        obj['shore_wet'] = True
        changed += 1
    return {'things_wet_to_the_tide_line': changed}


def _drift_along(seen, run, verts, faces, slots, materials, rng, amount):
    """One drift along one face of a standing thing: rises against it, slopes out onto the sand, tapers at both ends."""
    if len(run) < 3:
        return 0
    ground = seen.scene.objects.get(run[0].ground_obj)
    material = ground.active_material if ground is not None else None
    if material is None:
        return 0
    slot = materials.setdefault(material.name, len(materials))
    lengths = survey_module.run_length(run)
    total = lengths[-1]
    if total < 0.15:
        return 0
    object_seed = survey_module.steady_seed(run[0].obj) / 13.0
    rows = []
    for foot, t in zip(run, lengths):
        taper = min(1.0, t / 0.22, (total - t) / 0.22)
        h = (0.02 + 0.05 * (survey_module.smooth_wave(t * 3.0, object_seed) + 1) / 2) * amount * max(taper, 0.0)
        w = h * rng.uniform(3.2, 4.4) + 0.01
        top = seen.surface_point(foot, h) + foot.normal * 0.002
        middle = foot.base + foot.normal * (w * 0.42) + Vector((0, 0, h * 0.48))
        edge = foot.base + foot.normal * w - Vector((0, 0, 0.006))
        rows.append((top, middle, edge))
    for a, b in zip(rows, rows[1:]):
        start = len(verts)
        verts.extend(tuple(p) for p in a + b)
        faces.append((start, start + 3, start + 4, start + 1))
        faces.append((start + 1, start + 4, start + 5, start + 2))
        slots.extend([slot, slot])
    return 1


def sand_drifts(seen, collection, rng, amount, seed=5):
    """Sand blown and washed against the foot of everything standing in it, tapering at each end."""
    verts, faces = [], []
    runs_made = 0
    materials = {}
    slots = []
    for whole_run in seen.foot_runs(None, max_lift=0.35, limit=40.0):
        if whole_run[0].ground_role != 'sand' or len(whole_run) < 3:
            continue
        standing = seen.scene.objects.get(whole_run[0].obj)
        if standing is None or standing.dimensions.z < 0.25 or min(standing.dimensions.x, standing.dimensions.y) < 0.05:
            continue        # nets, wires, rods and boards lying flat do not hold a drift
        # a drift follows one face: break the run where the face turns sharply (a corner, or another thin part)
        pieces, piece = [], [whole_run[0]]
        for foot in whole_run[1:]:
            if foot.normal.dot(piece[-1].normal) < 0.6:
                pieces.append(piece)
                piece = []
            piece.append(foot)
        pieces.append(piece)
        for run in pieces:
            runs_made += _drift_along(seen, run, verts, faces, slots, materials, rng, amount)
    if faces:
        ordered = sorted(materials, key=materials.get)
        obj = _mesh(PREFIX + 'sand drifted against things', verts, faces, [bpy.data.materials[n] for n in ordered], collection, 'sand', slots=slots)
        tool = bmesh.new()
        tool.from_mesh(obj.data)
        bmesh.ops.recalc_face_normals(tool, faces=tool.faces)
        tool.to_mesh(obj.data)
        tool.free()
    return {'sand_drift_runs': runs_made}


# ----------------------------------------------------------------------------------------------- the one call

def lay_shore(scene, roles, seen, collection, *, wet=1.0, litter=1.0, growth=1.0, seed=88301, today=False):
    """Water edges for every sea and still water the camera sees, and sand drifts against anything standing in sand.
    Dials: wet (the wet band, foam, swash, things wet to the tide line), litter (wrack, driftwood, bank leaves, drifts),
    growth (moss along a bank); today adds today's scraps to the tide line."""
    rng = random.Random(seed)
    remove_shore_materials(scene)
    bodies = water_bodies(scene, roles)
    report = {'water_bodies': len(bodies), 'water_kinds': sorted({b['kind'] for b in bodies})}
    if seen is None or not seen.grid:
        if bodies:
            report['note'] = 'no camera to look from: water edges are dressed only where the camera sees them'
        return report
    if bodies:
        grid = ShoreGrid(seen, bodies)
        if grid.ok:
            report['grid'] = '%d x %d cells of %.2f m' % (grid.nx, grid.ny, grid.cell)
            report['water_cells_seen'] = int((grid.kind == 2).sum())
            report.update(wet_ground(grid, collection, rng, wet))
            if any(b['kind'] == 'sea' for b in bodies):
                report.update(foam(grid, collection, rng, wet))
            report.update(wrack_and_driftwood(grid, collection, rng, litter, growth=growth, today=today))
            if wet > 0:
                report.update(wet_standing_things(grid, scene, roles, bodies))
    if litter > 0:
        report.update(sand_drifts(seen, collection, rng, litter))
    return report
