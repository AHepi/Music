"""
What this file does:
Turns a flat road into a road of hand-laid stone setts, and a flat pavement into worn flagstones, the way the
street bundle "Rain on the Old Curve" did it: eighteen unique chipped stone shapes (and eight worn flags) are
scattered as live instances over the flat object's footprint, each with its own small turn, size and height,
so no two stones are alike and nothing repeats. The flat object stays underneath as the dark damp bed between
the stones. A flat plane with the cobble material alone reads as a polished floor; this is what makes it read
as a street.

Used by apply_by_role.py for every `road` and `pavement` object that is still a flat shape (two faces or fewer
on its top), unless --no-setts is given. Can also be called on its own:

    import lay_setts
    lay_setts.lay_setts_on(road_object, cobble_material, bed_material)
    lay_setts.lay_flags_on(pavement_object, pavement_material)

Numbers (stone sizes, joints, wobble) are the bundle's; only the footprint comes from the object.
"""

import random

import bpy
from mathutils import Vector

PROTOTYPE_COLLECTION = 'LAID • stone source library'


def _footprint(obj):
    """World-space x range, y range and top height of a flat object."""
    corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    xs = [c.x for c in corners]
    ys = [c.y for c in corners]
    zs = [c.z for c in corners]
    return min(xs), max(xs), min(ys), max(ys), max(zs)


def is_flat(obj):
    """A plane or a box: nothing a stone could not be laid on."""
    return obj.type == 'MESH' and len(obj.data.polygons) <= 6


def _collection(name, scene):
    collection = bpy.data.collections.get(name)
    if collection is None:
        collection = bpy.data.collections.new(name)
        scene.collection.children.link(collection)
    return collection


def _mesh_object(name, verts, faces, material, collection):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    if material:
        mesh.materials.append(material)
    return obj


def _sett_prototypes(material, collection, count=18):
    """Eighteen worn octagonal stones with rounded wet shoulders, parked far below the place."""
    made = []
    for i in range(count):
        name = 'LAID • sett source %02d' % i
        if name in bpy.data.objects:
            made.append(bpy.data.objects[name])
            continue
        rr = random.Random(802 + i)
        cut = rr.uniform(0.04, 0.11)
        outline = [(-0.5 + cut, -0.5), (0.5 - cut, -0.5), (0.5, -0.5 + cut), (0.5, 0.5 - cut),
                   (0.5 - cut, 0.5), (-0.5 + cut, 0.5), (-0.5, 0.5 - cut), (-0.5, -0.5 + cut)]
        outline = [(x + rr.uniform(-0.018, 0.018), y + rr.uniform(-0.020, 0.020)) for x, y in outline]
        ztop = rr.uniform(-0.004, 0.004)
        verts = ([(x, y, -0.075) for x, y in outline]
                 + [(x, y, ztop - 0.012) for x, y in outline]
                 + [(x * 0.91, y * 0.91, ztop + rr.uniform(-0.002, 0.002)) for x, y in outline])
        faces = ([tuple(range(7, -1, -1)), tuple(range(16, 24))]
                 + [(j, (j + 1) % 8, (j + 1) % 8 + 8, j + 8) for j in range(8)]
                 + [(j + 8, (j + 1) % 8 + 8, (j + 1) % 8 + 16, j + 16) for j in range(8)])
        obj = _mesh_object(name, verts, faces, material, collection)
        bevel = obj.modifiers.new('Rounded wet shoulders', 'BEVEL')
        bevel.width = 0.014
        bevel.segments = 3
        obj.location = (0, 0, -60 - i * 2)
        made.append(obj)
    return made


def _flag_prototypes(material, collection, count=8):
    made = []
    for i in range(count):
        name = 'LAID • flag source %d' % i
        if name in bpy.data.objects:
            made.append(bpy.data.objects[name])
            continue
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, -100 - i))
        obj = bpy.context.object
        obj.name = name
        obj.scale = (1, 1, 0.14)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        obj.data.materials.append(material)
        bevel = obj.modifiers.new('Worn softened edges', 'BEVEL')
        bevel.width = 0.03
        bevel.segments = 2
        for existing in list(obj.users_collection):
            existing.objects.unlink(obj)
        collection.objects.link(obj)
        made.append(obj)
    return made


def _scatter(name, points, scales, rotations, source_collection, target_collection, seed):
    """Points carrying their own size and turn, instanced live from the source collection by Geometry Nodes."""
    mesh = bpy.data.meshes.new(name + ' • stable point layout')
    mesh.from_pydata(points, [], [])
    mesh.update()
    for attribute, values in (('stone_scale', scales), ('stone_rotation', rotations)):
        data = mesh.attributes.new(attribute, 'FLOAT_VECTOR', 'POINT')
        for slot, value in zip(data.data, values):
            slot.vector = value
    obj = bpy.data.objects.new(name, mesh)
    target_collection.objects.link(obj)
    group = bpy.data.node_groups.new(name + ' • Geometry Nodes', 'GeometryNodeTree')
    group.interface.new_socket(name='Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    group.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    nodes, links = group.nodes, group.links
    group_in = nodes.new('NodeGroupInput')
    group_out = nodes.new('NodeGroupOutput')
    instance = nodes.new('GeometryNodeInstanceOnPoints')
    info = nodes.new('GeometryNodeCollectionInfo')
    info.inputs['Collection'].default_value = source_collection
    info.inputs['Separate Children'].default_value = True
    info.inputs['Reset Children'].default_value = True
    instance.inputs['Pick Instance'].default_value = True
    pick = nodes.new('FunctionNodeRandomValue')
    pick.data_type = 'INT'
    pick.inputs['Min'].default_value = 0
    pick.inputs['Max'].default_value = len(source_collection.objects) - 1
    pick.inputs['Seed'].default_value = seed
    links.new(group_in.outputs['Geometry'], instance.inputs['Points'])
    links.new(info.outputs['Instances'], instance.inputs['Instance'])
    links.new(pick.outputs['Value'], instance.inputs['Instance Index'])
    for attribute, socket in (('stone_scale', 'Scale'), ('stone_rotation', 'Rotation')):
        named = nodes.new('GeometryNodeInputNamedAttribute')
        named.data_type = 'FLOAT_VECTOR'
        named.inputs['Name'].default_value = attribute
        links.new(named.outputs['Attribute'], instance.inputs[socket])
    links.new(instance.outputs['Instances'], group_out.inputs['Geometry'])
    modifier = obj.modifiers.new('Live non-repeating stones', 'NODES')
    modifier.node_group = group
    return obj


def lay_setts_on(road, cobble_material, bed_material, seed=714035):
    """Lay setts over a flat road object. The road itself becomes the dark bed 7 cm lower."""
    scene = bpy.context.scene
    x0, x1, y0, y1, top = _footprint(road)
    rng = random.Random(seed)
    prototypes = _collection(PROTOTYPE_COLLECTION, scene)
    sources = bpy.data.collections.get(PROTOTYPE_COLLECTION + ' • setts')
    if sources is None:
        sources = bpy.data.collections.new(PROTOTYPE_COLLECTION + ' • setts')
        prototypes.children.link(sources)
    _sett_prototypes(cobble_material, sources)
    half_width = (x1 - x0) / 2
    centre_x = (x0 + x1) / 2
    points, scales, rotations = [], [], []
    y = y0
    while y < y1:
        depth = rng.uniform(0.125, 0.19)
        x = x0 - rng.random() * 0.22
        while x < x1:
            width = rng.uniform(0.23, 0.36)
            if x + width / 2 > x1:
                break
            px = x + width / 2 + rng.uniform(-0.012, 0.012)
            py = y + rng.uniform(-0.012, 0.012)
            # a slight crown: the middle of the road a little higher than its edges
            z = top + 0.055 + rng.uniform(-0.006, 0.006) - 0.025 * (abs(px - centre_x) / max(half_width, 0.5)) ** 1.8
            if rng.random() > 0.007:  # a few true missing setts
                points.append((px, py, z))
                scales.append((width - 0.008, depth - 0.008, 1))
                rotations.append((rng.uniform(-0.008, 0.008), rng.uniform(-0.008, 0.008), rng.uniform(-0.016, 0.016)))
            x += width
        y += depth
    target = road.users_collection[0] if road.users_collection else scene.collection
    laid = _scatter(road.name + ' • laid setts', points, scales, rotations, sources, target, 73)
    laid['place_role'] = 'road'
    road.data.materials.clear()
    road.data.materials.append(bed_material)
    road.location.z -= 0.07
    return laid, len(points)


def lay_flags_on(pavement, pavement_material, seed=714036):
    """Lay worn flagstones over a flat pavement object, in strips along its length. The object stays as the bed."""
    scene = bpy.context.scene
    x0, x1, y0, y1, top = _footprint(pavement)
    rng = random.Random(seed)
    prototypes = _collection(PROTOTYPE_COLLECTION, scene)
    sources = bpy.data.collections.get(PROTOTYPE_COLLECTION + ' • flags')
    if sources is None:
        sources = bpy.data.collections.new(PROTOTYPE_COLLECTION + ' • flags')
        prototypes.children.link(sources)
    _flag_prototypes(pavement_material, sources)
    width = x1 - x0
    strips = max(1, int(round(width / 0.7)))
    strip_width = width / strips
    points, scales, rotations = [], [], []
    for strip in range(strips):
        xx = x0 + (strip + 0.5) * strip_width
        y = y0
        while y < y1:
            depth = rng.uniform(0.53, 0.85)
            if y + depth / 2 > y1:
                break
            points.append((xx + rng.uniform(-0.02, 0.02), y + depth / 2, top + 0.005 + rng.uniform(-0.012, 0.012)))
            scales.append((strip_width - 0.02 + rng.uniform(-0.03, 0.03), depth - 0.025, 1))
            rotations.append((0, 0, rng.uniform(-0.013, 0.013)))
            y += depth
    target = pavement.users_collection[0] if pavement.users_collection else scene.collection
    laid = _scatter(pavement.name + ' • laid flags', points, scales, rotations, sources, target, 91)
    laid['place_role'] = 'pavement'
    return laid, len(points)
