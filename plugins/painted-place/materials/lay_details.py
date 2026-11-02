"""
What this file does:
Puts the small, old, wet things onto a dressed place: puddles on the road and water in the gutters, damp and
soot on the walls' feet and run-off stains on their faces, rust streaks under iron, moss patches, weed tufts,
fallen leaves and litter along gutters and wall feet, and fallen stone flakes. These are the systems of the
street bundle "Rain on the Old Curve" (wear.py, street_life.py) with every position taken from the place
itself instead of from that street: where a wall meets the ground, where a kerb meets the road, where an iron
pipe comes down. Shapes are not touched; materials are not touched; everything added is named "DETAIL • ..."
and can be removed again with remove_details().

    import lay_details
    report = lay_details.lay_details(bpy.context.scene, materials, wet=1.0, grime=1.0, growth=1.0, litter=1.0)

The amounts scale how much of each kind there is (0 = none, 1 = as the street). Materials come from the
street bundle (materials/Materials.blend); apply_details.py appends them and calls this.
"""

import math
import random

import bpy
from mathutils import Vector

PREFIX = 'DETAIL • '
LOOK_AWAY_LIMIT = 70.0  # metres from the camera beyond which nothing small is placed


# ----------------------------------------------------------------------------------------------- reading the place

def role_of(obj, role_from_name):
    if obj.get('place_role'):
        return obj['place_role']
    return role_from_name(obj.name)


def is_added(obj):
    """Things this plugin added (laid stones, details, facades, the look) and parked prototypes are not part of the place."""
    return (obj.name.startswith(('FACADE •', 'DETAIL •', 'LAID •', 'LOOK •')) or '• laid' in obj.name
            or bool(obj.get('prototype')))


def wall_faces(scene, roles, camera_spot):
    """Big vertical faces the camera can see, of stone walls and of timber walls (a thin, tall, long wood object).
    Each face carries `front`: how far its visible surface stands in front of the face (laid ashlar is thick)."""
    import lay_facade
    faces = []
    for obj in scene.objects:
        if obj.type != 'MESH' or is_added(obj):
            continue
        role = roles.get(obj.name)
        if role == 'wood':
            size = sorted(obj.dimensions)
            if not (obj.dimensions.z > 1.2 and size[-1] > 1.5 and min(obj.dimensions.x, obj.dimensions.y) < 0.8):
                continue
        elif role not in ('wall', 'plaster'):
            continue
        for face in lay_facade.oriented_faces(obj, minimum_area=1.5):
            centre = face['origin'] + face['along'] * ((face['u0'] + face['u1']) / 2) + Vector((0, 0, (face['z0'] + face['z1']) / 2))
            if (camera_spot - centre).dot(face['normal']) <= 0:
                continue
            face['front'] = float(obj.get('facade_front', 0.0))
            face['plinth'] = float(obj.get('facade_plinth', 0.0))
            face['stone'] = role in ('wall', 'plaster')
            face['centre'] = centre
            faces.append(face)
    return faces


def ground_probe(scene):
    """ground_z(x, y, from_z): the height of the surface something would rest on, found by a ray straight down.
    Laid stones and flags count (rays hit instances); details, glass, smoke and steep faces do not."""
    depsgraph = bpy.context.evaluated_depsgraph_get()
    skip_words = ('DETAIL •', 'LOOK •', 'FACADE •')

    def ground_z(x, y, from_z):
        origin = Vector((x, y, from_z))
        for _ in range(6):
            hit, location, normal, index, obj, matrix = scene.ray_cast(depsgraph, origin, Vector((0, 0, -1)), distance=50.0)
            if not hit:
                return None
            name = obj.name if obj is not None else ''
            role = obj.get('place_role', '') if obj is not None else ''
            if name.startswith(skip_words) or role in ('smoke', 'window lit', 'window dim', 'window dark', 'lamp glass', 'flame') or normal.z < 0.6:
                origin = location - Vector((0, 0, 0.002))
                continue
            return location.z
        return None
    return ground_z


def kerb_lines(scene, roles, road_centre, ground_z):
    """Long low trim objects are kerbs: (start, end, toward-road direction, kerb top, gutter height) along the edge nearest the road."""
    lines = []
    for obj in scene.objects:
        if obj.type != 'MESH' or is_added(obj) or roles.get(obj.name) != 'trim':
            continue
        size = obj.dimensions
        if max(size.x, size.y) < 4.0 or size.z > 0.4:
            continue
        corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
        top = max(c.z for c in corners)
        x0, x1 = min(c.x for c in corners), max(c.x for c in corners)
        y0, y1 = min(c.y for c in corners), max(c.y for c in corners)
        if size.y >= size.x:
            toward = 1 if road_centre.x > (x0 + x1) / 2 else -1
            edge_x = x1 if toward > 0 else x0
            start, end, direction = Vector((edge_x, y0, top)), Vector((edge_x, y1, top)), Vector((toward, 0, 0))
        else:
            toward = 1 if road_centre.y > (y0 + y1) / 2 else -1
            edge_y = y1 if toward > 0 else y0
            start, end, direction = Vector((x0, edge_y, top)), Vector((x1, edge_y, top)), Vector((0, toward, 0))
        middle = (start + end) / 2 + direction * 0.08
        gutter = ground_z(middle.x, middle.y, top + 0.3)
        if gutter is None or gutter > top - 0.02:
            gutter = top - 0.16
        lines.append((start, end, direction, top, gutter))
    return lines


def road_footprints(scene, roles):
    """(x0, x1, y0, y1, top z, has_setts) for every road object (laid setts lie on their bed)."""
    roads = []
    laid = [o.name for o in scene.objects if '• laid setts' in o.name]
    for obj in scene.objects:
        if obj.type != 'MESH' or is_added(obj) or roles.get(obj.name) != 'road':
            continue
        corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
        has_setts = any(name.startswith(obj.name) for name in laid)
        top = max(c.z for c in corners) + (0.07 if has_setts else 0.0)
        roads.append((min(c.x for c in corners), max(c.x for c in corners), min(c.y for c in corners), max(c.y for c in corners), top, has_setts))
    return roads


def iron_feet(scene, roles):
    """Lowest point of every iron object that stands up (pipes, posts): (foot point, height)."""
    feet = []
    for obj in scene.objects:
        if obj.type != 'MESH' or is_added(obj) or roles.get(obj.name) not in ('iron', 'rust'):
            continue
        size = obj.dimensions
        if size.z < 0.8 or max(size.x, size.y) > 0.6:
            continue
        corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
        foot = Vector((sum(c.x for c in corners) / 8, sum(c.y for c in corners) / 8, min(c.z for c in corners)))
        feet.append((foot, size.z))
    return feet


# ----------------------------------------------------------------------------------------------- making things

def _collection(scene):
    collection = bpy.data.collections.get(PREFIX + 'details')
    if collection is None:
        collection = bpy.data.collections.new(PREFIX + 'details')
        scene.collection.children.link(collection)
    return collection


def _mesh_object(name, verts, faces, material, collection, role):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    if material is not None:
        mesh.materials.append(material)
    obj = bpy.data.objects.new(name, mesh)
    obj['place_role'] = role
    collection.objects.link(obj)
    return obj


def _instance_randomly(name, points, prototypes, collection, role, seed, scale_range=((0.55, 0.55, 0.55), (1.35, 1.35, 1.15))):
    """Points instanced live from a collection of prototypes with random pick, size and turn (the bundle's way)."""
    obj = _mesh_object(name, points, [], None, collection, role)
    group = bpy.data.node_groups.new(name + ' • Geometry Nodes', 'GeometryNodeTree')
    group.interface.new_socket(name='Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    group.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    nodes, links = group.nodes, group.links
    group_in = nodes.new('NodeGroupInput')
    group_out = nodes.new('NodeGroupOutput')
    instance = nodes.new('GeometryNodeInstanceOnPoints')
    info = nodes.new('GeometryNodeCollectionInfo')
    info.inputs['Collection'].default_value = prototypes
    info.inputs['Separate Children'].default_value = True
    info.inputs['Reset Children'].default_value = True
    instance.inputs['Pick Instance'].default_value = True
    pick = nodes.new('FunctionNodeRandomValue')
    pick.data_type = 'INT'
    pick.inputs['Min'].default_value = 0
    pick.inputs['Max'].default_value = len(prototypes.objects) - 1
    pick.inputs['Seed'].default_value = seed
    scale = nodes.new('FunctionNodeRandomValue')
    scale.data_type = 'FLOAT_VECTOR'
    scale.inputs['Min'].default_value = scale_range[0]
    scale.inputs['Max'].default_value = scale_range[1]
    scale.inputs['Seed'].default_value = seed + 1
    rotation = nodes.new('FunctionNodeRandomValue')
    rotation.data_type = 'FLOAT_VECTOR'
    rotation.inputs['Min'].default_value = (-0.08, -0.08, 0)
    rotation.inputs['Max'].default_value = (0.08, 0.08, math.tau)
    rotation.inputs['Seed'].default_value = seed + 2
    links.new(group_in.outputs['Geometry'], instance.inputs['Points'])
    links.new(info.outputs['Instances'], instance.inputs['Instance'])
    links.new(pick.outputs['Value'], instance.inputs['Instance Index'])
    links.new(scale.outputs['Value'], instance.inputs['Scale'])
    links.new(rotation.outputs['Value'], instance.inputs['Rotation'])
    links.new(instance.outputs['Instances'], group_out.inputs['Geometry'])
    modifier = obj.modifiers.new('Live varied pieces', 'NODES')
    modifier.node_group = group
    return obj


def _weed_prototypes(scene, greens, rng, collection_name=PREFIX + 'weed prototypes', count=12):
    """Twelve tufts of bent tapering blades, parked far below the place (the bundle's leaf sources)."""
    existing = bpy.data.collections.get(collection_name)
    if existing is not None:
        return existing
    prototypes = bpy.data.collections.new(collection_name)
    scene.collection.children.link(prototypes)
    for i in range(count):
        verts, faces, indices = [], [], []
        for _ in range(rng.randint(5, 13)):
            a = rng.random() * math.tau
            h = rng.uniform(0.08, 0.32)
            lean = rng.uniform(0.012, 0.14)
            w = rng.uniform(0.006, 0.020)
            start = len(verts)
            for k in range(5):
                t = k / 4
                off = lean * t * t
                wid = w * (1 - t) * 0.5
                verts.extend([(math.cos(a) * off - math.sin(a) * wid, math.sin(a) * off + math.cos(a) * wid, h * t),
                              (math.cos(a) * off + math.sin(a) * wid, math.sin(a) * off - math.cos(a) * wid, h * t)])
            for k in range(4):
                faces.append((start + 2 * k, start + 2 * k + 1, start + 2 * k + 3, start + 2 * k + 2))
                indices.append(rng.randrange(len(greens)))
        mesh = bpy.data.meshes.new(PREFIX + 'weed tuft %02d' % i)
        mesh.from_pydata(verts, [], faces)
        mesh.update()
        for green in greens:
            mesh.materials.append(green)
        for polygon, index in zip(mesh.polygons, indices):
            polygon.material_index = index
        obj = bpy.data.objects.new(PREFIX + 'weed tuft %02d' % i, mesh)
        obj['prototype'] = True
        obj.location = (0, 0, -150 - i)
        prototypes.objects.link(obj)
    return prototypes


def _flake_prototype(scene, stone, collection):
    name = PREFIX + 'stone flake source'
    if name in bpy.data.objects:
        return bpy.data.objects[name]
    obj = _mesh_object(name, [(-0.52, -0.4, 0), (0.45, -0.34, 0), (0.58, 0.18, 0.02), (0.06, 0.49, 0), (-0.45, 0.27, 0.04), (-0.12, -0.08, 0.24)],
                       [(0, 4, 3, 2, 1), (0, 1, 5), (1, 2, 5), (2, 3, 5), (3, 4, 5), (4, 0, 5)], stone, collection, 'trim')
    obj.location = (0, 0, -180)
    obj['prototype'] = True
    return obj


def _patch(verts, faces, centre, rx, ry, z, rng, lift=0.002):
    """A ragged flat blob of 9 to 16 corners around a centre; faces fan from the centre."""
    start = len(verts)
    verts.append((centre[0], centre[1], z))
    count = rng.randint(9, 16)
    for k in range(count):
        a = math.tau * k / count
        r = rng.uniform(0.55, 1.3)
        verts.append((centre[0] + math.cos(a) * rx * r, centre[1] + math.sin(a) * ry * r, z + rng.uniform(0, lift)))
    for k in range(count):
        faces.append((start, start + 1 + k, start + 1 + (k + 1) % count))


def _simple_material(name, colour, roughness, high=None, scale=40.0):
    material = bpy.data.materials.get(name)
    if material is not None:
        return material
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    principled = material.node_tree.nodes.get('Principled BSDF')
    principled.inputs['Roughness'].default_value = roughness
    if high is None:
        principled.inputs['Base Color'].default_value = (*colour, 1)
    else:
        nodes, links = material.node_tree.nodes, material.node_tree.links
        geometry = nodes.new('ShaderNodeNewGeometry')
        noise = nodes.new('ShaderNodeTexNoise')
        noise.inputs['Scale'].default_value = scale
        noise.inputs['Detail'].default_value = 3
        ramp = nodes.new('ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].color = (*colour, 1)
        ramp.color_ramp.elements[1].color = (*high, 1)
        links.new(geometry.outputs['Position'], noise.inputs['Vector'])
        links.new(noise.outputs['Fac'], ramp.inputs[0])
        links.new(ramp.outputs['Color'], principled.inputs['Base Color'])
    material.diffuse_color = (*colour, 1)
    return material


def _rubbish_prototypes(scene, rng, paper):
    """Sixteen coal, cinder and ash lumps, four bits of wet straw, one paper scrap: the street's small rubbish (mostly dark)."""
    name = PREFIX + 'rubbish prototypes'
    existing = bpy.data.collections.get(name)
    if existing is not None:
        return existing
    collection = bpy.data.collections.new(name)
    scene.collection.children.link(collection)
    coal = _simple_material(PREFIX + 'coal and cinders', (0.012, 0.012, 0.014), 0.45, (0.05, 0.045, 0.042))
    ash = _simple_material(PREFIX + 'ash, grit and mud', (0.045, 0.040, 0.034), 0.92, (0.12, 0.105, 0.085))
    straw = _simple_material(PREFIX + 'wet straw', (0.10, 0.075, 0.030), 0.7, (0.22, 0.17, 0.07))
    made = 0
    for i in range(16):
        r = random.Random(4100 + i)
        count = r.randint(6, 9)
        verts = []
        size = 0.04 if i < 12 else 0.06  # metres; written into the shape itself, because instancing resets an object's own scale
        for k in range(count):
            a = math.tau * k / count + r.uniform(-0.3, 0.3)
            rad = r.uniform(0.6, 1.0)
            verts.append((math.cos(a) * rad * size, math.sin(a) * rad * r.uniform(0.6, 1.0) * size, r.uniform(0.0, 0.15) * size))
        verts.append((r.uniform(-0.2, 0.2) * size, r.uniform(-0.2, 0.2) * size, r.uniform(0.35, 0.7) * size))
        top = len(verts) - 1
        faces = [tuple(range(count - 1, -1, -1))] + [(k, (k + 1) % count, top) for k in range(count)]
        mesh = bpy.data.meshes.new(PREFIX + 'lump %02d' % i)
        mesh.from_pydata(verts, [], faces)
        mesh.materials.append(coal if i < 10 else ash)
        obj = bpy.data.objects.new(mesh.name, mesh)
        obj.location = (0, 0, -190 - i)
        obj['prototype'] = True
        collection.objects.link(obj)
        made += 1
    for i in range(4):
        r = random.Random(4200 + i)
        verts, faces = [], []
        length, bend = r.uniform(0.06, 0.14), r.uniform(-0.03, 0.03)
        for k in range(6):
            t = k / 5
            x, y = (t - 0.5) * length, bend * math.sin(t * math.pi)
            verts.extend([(x, y - 0.0025, 0.002), (x, y + 0.0025, 0.002)])
        for k in range(5):
            faces.append((2 * k, 2 * k + 1, 2 * k + 3, 2 * k + 2))
        mesh = bpy.data.meshes.new(PREFIX + 'straw %d' % i)
        mesh.from_pydata(verts, [], faces)
        mesh.materials.append(straw)
        obj = bpy.data.objects.new(mesh.name, mesh)
        obj.location = (0, 0, -200 - i)
        obj['prototype'] = True
        collection.objects.link(obj)
    for i in range(1):
        r = random.Random(4300 + i)
        w, h = r.uniform(0.04, 0.09), r.uniform(0.03, 0.07)
        verts = [(-w / 2 + r.uniform(0, 0.01), -h / 2, 0.001), (w / 2, -h / 2 + r.uniform(0, 0.01), 0.002),
                 (w / 2 - r.uniform(0, 0.015), h / 2, 0.004), (-w / 2, h / 2 - r.uniform(0, 0.012), 0.001)]
        mesh = bpy.data.meshes.new(PREFIX + 'paper scrap %d' % i)
        mesh.from_pydata(verts, [], [(0, 1, 2, 3)])
        mesh.materials.append(paper)
        obj = bpy.data.objects.new(mesh.name, mesh)
        obj.location = (0, 0, -210 - i)
        obj['prototype'] = True
        collection.objects.link(obj)
    return collection


def _shore_prototypes(scene, rng):
    """Shells, coral bits and seaweed: a shore's small things."""
    name = PREFIX + 'shore prototypes'
    existing = bpy.data.collections.get(name)
    if existing is not None:
        return existing
    collection = bpy.data.collections.new(name)
    scene.collection.children.link(collection)
    shell = _simple_material(PREFIX + 'bleached shell', (0.55, 0.50, 0.43), 0.6, (0.75, 0.70, 0.62), scale=60.0)
    coral = _simple_material(PREFIX + 'coral rubble', (0.48, 0.45, 0.40), 0.9, (0.66, 0.62, 0.55), scale=80.0)
    weed = _simple_material(PREFIX + 'dried seaweed', (0.03, 0.035, 0.015), 0.6, (0.09, 0.08, 0.03))
    for i in range(6):
        r = random.Random(4400 + i)
        size = r.uniform(0.012, 0.03)
        verts, faces = [(0, 0, size * 0.5)], []
        for k in range(7):
            a = -0.9 + 1.8 * k / 6
            verts.append((math.sin(a) * size, math.cos(a) * size, 0.0))
        for k in range(6):
            faces.append((0, k + 1, k + 2))
        mesh = bpy.data.meshes.new(PREFIX + 'shell %d' % i)
        mesh.from_pydata(verts, [], faces)
        mesh.materials.append(shell)
        obj = bpy.data.objects.new(mesh.name, mesh)
        obj.location = (0, 0, -220 - i)
        obj['prototype'] = True
        collection.objects.link(obj)
    for i in range(6):
        r = random.Random(4500 + i)
        size = r.uniform(0.02, 0.05)
        count = r.randint(5, 8)
        verts = [(math.cos(math.tau * k / count) * size * r.uniform(0.6, 1.0), math.sin(math.tau * k / count) * size * r.uniform(0.6, 1.0), 0)
                 for k in range(count)] + [(0, 0, size * r.uniform(0.4, 0.9))]
        faces = [tuple(range(count - 1, -1, -1))] + [(k, (k + 1) % count, count) for k in range(count)]
        mesh = bpy.data.meshes.new(PREFIX + 'coral bit %d' % i)
        mesh.from_pydata(verts, [], faces)
        mesh.materials.append(coral)
        obj = bpy.data.objects.new(mesh.name, mesh)
        obj.location = (0, 0, -230 - i)
        obj['prototype'] = True
        collection.objects.link(obj)
    for i in range(4):
        r = random.Random(4600 + i)
        verts, faces = [], []
        length = r.uniform(0.15, 0.4)
        for k in range(8):
            tt = k / 7
            x, y = (tt - 0.5) * length, 0.04 * math.sin(tt * 5 + i)
            verts.extend([(x, y - 0.012, 0.003), (x, y + 0.012, 0.003)])
        for k in range(7):
            faces.append((2 * k, 2 * k + 1, 2 * k + 3, 2 * k + 2))
        mesh = bpy.data.meshes.new(PREFIX + 'seaweed %d' % i)
        mesh.from_pydata(verts, [], faces)
        mesh.materials.append(weed)
        obj = bpy.data.objects.new(mesh.name, mesh)
        obj.location = (0, 0, -240 - i)
        obj['prototype'] = True
        collection.objects.link(obj)
    return collection


def _in_view(point, camera, limit):
    """In front of the camera, inside its frame (with a margin) and nearer than limit."""
    if camera is None:
        return True
    local = camera.matrix_world.inverted() @ Vector(point)
    depth = -local.z
    if depth < 0.5 or depth > limit:
        return False
    half = math.atan(18.0 / max(camera.data.lens, 1.0)) * 1.25
    return abs(local.x) < depth * math.tan(half) and abs(local.y) < depth * math.tan(half)


def _near_camera(point, camera_spot):
    return (Vector(point) - camera_spot).length < LOOK_AWAY_LIMIT


# ----------------------------------------------------------------------------------------------- the layers

def _foot_point(face, u, out):
    """A point in front of a face's visible surface, at along-position u, `out` metres out."""
    return face['origin'] + face['along'] * u + face['normal'] * (face['front'] + out)


def _ground_point(face, u, out):
    """A point on the ground in front of a face's foot: in front of its plinth, if it has one."""
    return face['origin'] + face['along'] * u + face['normal'] * (face['front'] + face.get('plinth', 0.0) + out)


def light_spots(scene, roles):
    """Centres of the things that will shine: lamp glass, flames and lit windows."""
    spots = []
    for obj in scene.objects:
        if obj.type != 'MESH' or is_added(obj) or roles.get(obj.name) not in ('lamp glass', 'flame', 'window lit'):
            continue
        corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
        spots.append(sum(corners, Vector((0, 0, 0))) / 8)
    return spots


def mirror_points(camera, spots, ground_height, rng, limit=26.0):
    """Where on the ground a puddle must lie for the camera to see each light mirrored in it (a set dresser's trick):
    on the line from the camera to the light's mirror image below the ground."""
    if camera is None:
        return []
    c = camera.matrix_world.translation
    points = []
    for spot in spots:
        mirror = Vector((spot.x, spot.y, 2 * ground_height - spot.z))
        if c.z - mirror.z <= 1e-6:
            continue
        t = (c.z - ground_height) / (c.z - mirror.z)
        p = c + (mirror - c) * t
        if 3.0 < (p - c).length < limit and _in_view(p, camera, limit):
            points.append(Vector((p.x + rng.uniform(-0.25, 0.25), p.y + rng.uniform(-0.25, 0.25), ground_height)))
    return points


def puddles(scene, roads, kerbs, water, collection, rng, amount, camera_spot, roles=None):
    """Rain films on the road (level, so high stones stand out of them), placed first where a lamp or a lit window will be
    seen mirrored in them, then a few more at random; and interrupted runs of water in the gutters."""
    verts, faces = [], []
    count = 0
    camera = scene.camera
    spots = light_spots(scene, roles or {})
    for x0, x1, y0, y1, top, has_setts in roads:
        half = max((x1 - x0) / 2, 0.5)
        cx = (x0 + x1) / 2
        wanted = [p for p in mirror_points(camera, spots, top + 0.05, rng) if x0 + 0.5 < p.x < x1 - 0.5 and y0 + 0.5 < p.y < y1 - 0.5]
        rng.shuffle(wanted)
        kept = []
        for p in wanted:
            if all((p - q).length > 1.6 for q in kept):
                kept.append(p)
        kept = kept[:max(1, int(6 * amount))]
        extra = int(amount * (y1 - y0) / 14.0)
        places = [(p.x, p.y) for p in kept] + [(rng.uniform(x0 + 0.6, x1 - 0.6), rng.uniform(y0 + 1, y1 - 1)) for _ in range(extra)]
        for x, y in places:
            if not _near_camera((x, y, top), camera_spot):
                continue
            rx, ry = rng.uniform(0.6, 1.3), rng.uniform(0.3, 0.6)
            crown = 0.025 * (abs(x - cx) / half) ** 1.8 if has_setts else 0.0
            level = top + (0.055 + 0.005 - crown if has_setts else 0.012)
            phases = [rng.uniform(0, math.tau) for _ in range(3)]
            first = len(verts)
            verts.append((x, y, level))
            n = 48
            for j in range(n):
                a = math.tau * j / n
                r = 1 + 0.13 * math.sin(3 * a + phases[0]) + 0.075 * math.sin(7 * a + phases[1]) + 0.035 * math.sin(13 * a + phases[2])
                verts.append((x + rx * math.cos(a) * r, y + ry * math.sin(a) * r, level))
            for j in range(n):
                faces.append((first, first + 1 + j, first + 1 + (j + 1) % n))
            count += 1
    runs = 0
    for start_point, end_point, toward, top, gutter in kerbs:
        line = end_point - start_point
        length = line.length
        if length < 1:
            continue
        direction = line.normalized()
        t = 0.0
        while t < length:
            t += rng.uniform(0.4, 4.0)
            run = rng.uniform(1.3, 4.8) * amount
            if t + run > length or run < 0.5:
                break
            a = start_point + direction * t
            b = start_point + direction * (t + run)
            if _near_camera(a, camera_spot):
                width = rng.uniform(0.07, 0.18)
                z = gutter + 0.009
                first = len(verts)
                steps = 10
                for k in range(steps + 1):
                    point = a + (b - a) * (k / steps)
                    wobble = rng.uniform(-0.015, 0.015)
                    verts.append((point.x + toward.x * 0.005, point.y + toward.y * 0.005, z))
                    verts.append((point.x + toward.x * (0.005 + width + wobble), point.y + toward.y * (0.005 + width + wobble), z))
                for k in range(steps):
                    q = first + 2 * k
                    faces.append((q, q + 1, q + 3, q + 2))
                runs += 1
            t += run
    if faces:
        _mesh_object(PREFIX + 'puddles and gutter water', verts, faces, water, collection, 'water')
    return {'puddles': count, 'gutter_runs': runs}


def wall_damp_and_soot(scene, faces_list, grime, soot, collection, rng, amount, camera_spot, ground_z):
    """Damp at every wall's foot, starting where the ground really meets it, and soot or run-off stains higher up."""
    foot_verts, foot_faces = [], []
    stain_verts, stain_faces = [], []
    feet = stains = 0
    for face in faces_list:
        if not _near_camera(face['centre'], camera_spot):
            continue
        n, along = face['normal'], face['along']
        out = 0.012
        u = face['u0'] + rng.uniform(0, 0.4)
        while u < face['u1']:
            w = min(rng.uniform(0.3, 1.4) * amount, face['u1'] - u)
            if w < 0.05:
                break
            middle = _ground_point(face, u + w / 2, 0.05)
            base = ground_z(middle.x, middle.y, face['z0'] + 0.6)
            base = face['z0'] if base is None or base > face['z0'] + 0.55 else max(base, face['z0'])
            h = rng.uniform(0.18, 0.65)
            if rng.random() < 0.15:
                w *= 0.3
                h = rng.uniform(1.2, 2.6)
            h = min(h, face['z1'] - base - 0.05)
            if h > 0.05:
                nx, nz = 5, max(3, int(h / 0.10))
                first = len(foot_verts)
                for iz in range(nz + 1):
                    for iy in range(nx + 1):
                        uu = u + w * iy / nx
                        zz = base + h * iz / nz + (0.03 * math.sin(iy * 1.7 + u) + 0.035 * math.sin(iz * 1.3 + u) if iz else 0.0)
                        point = _foot_point(face, uu, out)
                        foot_verts.append((point.x, point.y, zz))
                for iz in range(nz):
                    for iy in range(nx):
                        a = first + iz * (nx + 1) + iy
                        if rng.random() < 0.82:
                            foot_faces.append((a, a + 1, a + nx + 2, a + nx + 1))
                feet += 1
            u += w + rng.uniform(0.1, 1.2)
        number = int(amount * (face['u1'] - face['u0']) / 1.6)
        for j in range(number):
            cu = rng.uniform(face['u0'] + 0.2, face['u1'] - 0.2)
            cz = rng.uniform(face['z0'] + 0.5, face['z1'] - 0.3)
            w = rng.uniform(0.12, 0.65)
            h = rng.uniform(0.24, 1.15)
            if j % 3 == 0:
                w *= 0.42
                h *= 2.2
            nx, nz = 3, 5
            first = len(stain_verts)
            for iz in range(nz + 1):
                for iy in range(nx + 1):
                    uu = cu + w * (iy / nx - 0.5) + 0.012 * math.sin(iz * 2 + j)
                    zz = cz + h * (iz / nz - 0.5)
                    point = _foot_point(face, uu, 0.022)
                    stain_verts.append((point.x, point.y, zz))
            for iz in range(nz):
                for iy in range(nx):
                    a = first + iz * (nx + 1) + iy
                    if rng.random() > 0.16:
                        stain_faces.append((a, a + 1, a + nx + 2, a + nx + 1))
            stains += 1
    if foot_faces:
        _mesh_object(PREFIX + 'damp wall feet and rain runnels', foot_verts, foot_faces, grime, collection, 'grime')
    if stain_faces:
        _mesh_object(PREFIX + 'soot and run-off stains', stain_verts, stain_faces, soot, collection, 'grime')
    return {'damp_feet': feet, 'stains': stains}


def rust_under_iron(scene, feet, faces_list, rust, soot, collection, rng, amount, camera_spot, ground_z):
    """A rust streak on the wall below each standing iron thing near a wall, and a dark ring where it meets the ground."""
    verts, faces = [], []
    ring_verts, ring_faces = [], []
    streaks = rings = 0
    for foot, height in feet:
        if not _near_camera(foot, camera_spot) or rng.random() > amount:
            continue
        nearest, best = None, 0.9
        for face in faces_list:
            d = (foot - face['origin']).dot(face['normal']) - face['front']
            u = (foot - face['origin']).dot(face['along'])
            if -0.05 <= d < best and face['u0'] - 0.2 < u < face['u1'] + 0.2 and face['z0'] <= foot.z + 0.5:
                nearest, best = face, d
        if nearest is not None:
            u = (foot - nearest['origin']).dot(nearest['along']) + rng.uniform(-0.05, 0.05)
            top = min(foot.z + height * rng.uniform(0.3, 0.9), nearest['z1'] - 0.1)
            bottom = max(nearest['z0'] + 0.02, top - rng.uniform(0.4, 1.6))
            w = rng.uniform(0.04, 0.09)
            first = len(verts)
            steps = 6
            for k in range(steps + 1):
                z = bottom + (top - bottom) * k / steps
                wobble = 0.01 * math.sin(k * 1.9 + u)
                for side in (-1, 1):
                    point = _foot_point(nearest, u + side * w / 2 + wobble, 0.028)
                    verts.append((point.x, point.y, z))
            for k in range(steps):
                a = first + 2 * k
                faces.append((a, a + 1, a + 3, a + 2))
            streaks += 1
        base = ground_z(foot.x, foot.y, foot.z + 0.5)
        if base is not None:
            _patch(ring_verts, ring_faces, (foot.x, foot.y), rng.uniform(0.12, 0.22), rng.uniform(0.12, 0.22), base + 0.004, rng)
            rings += 1
    if faces:
        _mesh_object(PREFIX + 'rust streaks under iron', verts, faces, rust, collection, 'rust')
    if ring_faces:
        _mesh_object(PREFIX + 'dark rings at iron feet', ring_verts, ring_faces, soot, collection, 'grime')
    return {'rust_streaks': streaks, 'iron_rings': rings}


def growth(scene, faces_list, kerbs, greens, moss, collection, rng, amount, camera_spot, ground_z):
    """Moss patches and weed tufts where a wall meets the ground and in the gutter along the kerb, in patchy colonies."""
    prototypes = _weed_prototypes(scene, greens, rng)
    points = []
    moss_verts, moss_faces = [], []
    patches = 0
    for face in faces_list:
        if not _near_camera(face['centre'], camera_spot):
            continue
        u = face['u0']
        while u < face['u1']:
            colony = math.sin(u * 0.76 + face['origin'].x) + 0.8 * math.sin(u * 1.97 + 3)
            if colony > -0.4 and rng.random() < 0.6 * amount:
                for _ in range(rng.randint(2, 7)):
                    point = _ground_point(face, u + rng.gauss(0, 0.2), rng.uniform(0.01, 0.16))
                    z = ground_z(point.x, point.y, face['z0'] + 0.6)
                    if z is not None:
                        points.append((point.x, point.y, z + 0.004))
            if rng.random() < 0.35 * amount:
                point = _ground_point(face, u + rng.uniform(-0.2, 0.2), rng.uniform(0.02, 0.12))
                z = ground_z(point.x, point.y, face['z0'] + 0.6)
                if z is not None:
                    rx, ry = rng.uniform(0.025, 0.16), rng.uniform(0.08, 0.35)
                    if abs(face['normal'].x) > abs(face['normal'].y):
                        rx, ry = rx, ry
                    else:
                        rx, ry = ry, rx
                    _patch(moss_verts, moss_faces, (point.x, point.y), rx, ry, z + 0.003, rng)
                    patches += 1
            u += rng.uniform(0.5, 1.4)
    for start_point, end_point, toward, top, gutter in kerbs:
        line = end_point - start_point
        length = line.length
        direction = line.normalized()
        t = 0.0
        while t < length:
            base = start_point + direction * t
            if rng.random() < 0.45 * amount and _near_camera(base, camera_spot):
                for _ in range(rng.randint(1, 5)):
                    point = base + direction * rng.gauss(0, 0.2) + toward * rng.uniform(0.0, 0.06)
                    points.append((point.x, point.y, gutter + 0.003))
            t += rng.uniform(0.6, 1.8)
    if points:
        _instance_randomly(PREFIX + 'weed tufts', points, prototypes, collection, 'weed', 732,
                           scale_range=((0.9, 0.9, 0.8), (2.0, 2.0, 1.8)))
    if moss_faces:
        _mesh_object(PREFIX + 'moss patches', moss_verts, moss_faces, moss, collection, 'moss')
    return {'weed_tufts': len(points), 'moss_patches': patches}


def rubbish(scene, faces_list, kerbs, steps, paper, collection, rng, amount, camera, ground_z, shore=False, sand_objects=()):
    """Where a place's small rubbish collects: thick along gutters, along wall feet and round doorsteps, thinning away from
    each edge; never in the middle of a road or a pavement. A street gets coal, cinders, ash, straw and paper; a shore gets
    shells, coral bits and seaweed, also strewn thinly over the sand near the camera."""
    prototypes = _shore_prototypes(scene, rng) if shore else _rubbish_prototypes(scene, rng, paper)
    points = []
    for obj in sand_objects:
        corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
        x0, x1 = min(c.x for c in corners), max(c.x for c in corners)
        y0, y1 = min(c.y for c in corners), max(c.y for c in corners)
        top = max(c.z for c in corners)
        for _ in range(int(amount * 900)):
            x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
            if _in_view((x, y, top), camera, 16.0):
                z = ground_z(x, y, top + 1.0)
                if z is not None:
                    points.append((x, y, z + 0.002))
    for start_point, end_point, toward, top, gutter in kerbs:
        line = end_point - start_point
        direction = line.normalized()
        for _ in range(int(amount * line.length * 70)):
            t = rng.uniform(0, line.length)
            out = rng.expovariate(1 / 0.07)
            point = start_point + direction * t + toward * min(out, 0.6)
            if _in_view(point, camera, 28.0):
                z = gutter if out < 0.12 else (ground_z(point.x, point.y, top + 0.3) or gutter)
                points.append((point.x, point.y, z + 0.002))
    for face in faces_list:
        span = face['u1'] - face['u0']
        for _ in range(int(amount * span * 35)):
            point = _ground_point(face, rng.uniform(face['u0'], face['u1']), rng.expovariate(1 / 0.06))
            if _in_view(point, camera, 28.0):
                z = ground_z(point.x, point.y, face['z0'] + 0.6)
                if z is not None:
                    points.append((point.x, point.y, z + 0.002))
    for centre, size in steps:
        for _ in range(int(amount * 40)):
            a = rng.uniform(0, math.tau)
            rr = size * 0.5 + rng.expovariate(1 / 0.1)
            point = Vector((centre.x + math.cos(a) * rr, centre.y + math.sin(a) * rr, centre.z))
            if _in_view(point, camera, 28.0):
                z = ground_z(point.x, point.y, centre.z + 0.4)
                if z is not None:
                    points.append((point.x, point.y, z + 0.002))
    if points:
        _instance_randomly(PREFIX + 'rubbish: coal, cinders, ash, straw and paper', points, prototypes, collection, 'grime', 517,
                           scale_range=((0.5, 0.5, 0.4), (1.6, 1.6, 1.3)))
    return {'rubbish_pieces': len(points)}


def door_steps(scene, roles, faces_list):
    """Small pavement-role things standing against a wall: doorsteps. Returns (centre, size) for each."""
    found = []
    for obj in scene.objects:
        if obj.type != 'MESH' or is_added(obj) or roles.get(obj.name) != 'pavement':
            continue
        if max(obj.dimensions.x, obj.dimensions.y) > 2.5:
            continue
        corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
        centre = sum(corners, Vector((0, 0, 0))) / 8
        top = max(c.z for c in corners)
        near = any(abs((centre - f['origin']).dot(f['normal'])) < 0.8 for f in faces_list)
        if near:
            found.append((Vector((centre.x, centre.y, top)), max(obj.dimensions.x, obj.dimensions.y), obj))
    return found


def road_life(scene, kerbs, greens, moss, collection, rng, amount, camera_spot):
    """Weeds and moss rooted in the joints between laid setts, in a few colonies near the camera (where the eye can find
    them), and moss creeping along the gutter at the kerb's foot."""
    prototypes = _weed_prototypes(scene, greens, rng)
    points, moss_verts, moss_faces = [], [], []
    laid = [o for o in scene.objects if o.name.endswith('• laid setts') and o.type == 'MESH']
    rooted = 0
    for obj in laid:
        scales = obj.data.attributes.get('stone_scale')
        if scales is None:
            continue
        positions = [obj.matrix_world @ v.co for v in obj.data.vertices]
        near = [i for i, p in enumerate(positions) if _in_view(p, bpy.context.scene.camera, 18.0)]
        if not near:
            continue
        centres = [positions[rng.choice(near)] for _ in range(max(1, int(7 * amount)))]
        for i in near:
            p = positions[i]
            if not any(((p.x - c.x) / 0.44) ** 2 + ((p.y - c.y) / 0.40) ** 2 < 1 for c in centres) or rng.random() > 0.48:
                continue
            size = scales.data[i].vector
            sy = p.y + size.y * 0.50 + rng.uniform(-0.004, 0.004)
            sx = p.x + rng.uniform(-0.32, 0.32) * size.x
            for _ in range(rng.randint(1, 3)):
                points.append((sx + rng.uniform(-0.045, 0.045), sy + rng.uniform(-0.012, 0.012), p.z + 0.006))
            for _ in range(rng.randint(1, 3)):
                _patch(moss_verts, moss_faces, (sx + rng.uniform(-0.09, 0.09), sy + rng.uniform(-0.018, 0.018)),
                       rng.uniform(0.025, 0.075), rng.uniform(0.007, 0.020), p.z + 0.004, rng, lift=0.001)
            rooted += 1
    edge_patches = 0
    for start_point, end_point, toward, top, gutter in kerbs:
        line = end_point - start_point
        direction = line.normalized()
        t = 0.0
        while t < line.length:
            base = start_point + direction * t
            if _near_camera(base, camera_spot) and rng.random() < 0.55 * amount:
                rx, ry = rng.uniform(0.025, 0.12), rng.uniform(0.08, 0.30)
                if abs(direction.x) > abs(direction.y):
                    rx, ry = ry, rx
                centre = base + toward * rng.uniform(0.01, 0.06)
                _patch(moss_verts, moss_faces, (centre.x, centre.y), rx, ry, gutter + 0.002, rng, lift=0.001)
                edge_patches += 1
            t += rng.uniform(0.3, 1.2)
    if points:
        _instance_randomly(PREFIX + 'weeds in sett joints', points, prototypes, collection, 'weed', 811)
    if moss_faces:
        _mesh_object(PREFIX + 'moss in joints and along the kerb', moss_verts, moss_faces, moss, collection, 'moss')
    return {'sett_joints_rooted': rooted, 'joint_weeds': len(points), 'kerb_moss_patches': edge_patches}


def litter(scene, faces_list, kerbs, leaves, stone, collection, rng, amount, camera_spot, ground_z):
    """Wet leaves and small fragments in the gutters and at wall feet, and fallen stone flakes."""
    verts, faces, indices = [], [], []
    flake_points = []

    def leaf_at(x, y, z):
        rad = rng.uniform(0.015, 0.065)
        length = rad * rng.uniform(1.2, 2.3)
        a = rng.random() * math.tau
        dx, dy = math.cos(a), math.sin(a)
        px, py = -dy, dx
        k = len(verts)
        verts.extend([(x - dx * length, y - dy * length, z), (x + px * rad, y + py * rad, z + 0.002),
                      (x + dx * length, y + dy * length, z + 0.001), (x - px * rad, y - py * rad, z + 0.003), (x, y, z + 0.008)])
        for b in range(4):
            faces.append((k + b, k + (b + 1) % 4, k + 4))
            indices.append(0 if rng.random() < 0.7 else rng.randrange(len(leaves)))

    pieces = 0
    for start_point, end_point, toward, top, gutter in kerbs:
        line = end_point - start_point
        length = line.length
        direction = line.normalized()
        for _ in range(int(amount * length * 4.5)):
            t = rng.uniform(0, length)
            out = abs(rng.gauss(0, 0.12))
            point = start_point + direction * t + toward * out
            if not _near_camera(point, camera_spot):
                continue
            z = gutter if out < 0.1 else (ground_z(point.x, point.y, top + 0.3) or gutter)
            leaf_at(point.x, point.y, z + 0.004)
            pieces += 1
            if rng.random() < 0.25:
                flake_points.append((point.x, point.y, z + 0.006))
    for face in faces_list:
        if not _near_camera(face['centre'], camera_spot):
            continue
        for _ in range(int(amount * (face['u1'] - face['u0']) * 1.2)):
            point = _ground_point(face, rng.uniform(face['u0'], face['u1']), abs(rng.gauss(0, 0.15)) + 0.02)
            z = ground_z(point.x, point.y, face['z0'] + 0.6)
            if z is None:
                continue
            leaf_at(point.x, point.y, z + 0.004)
            pieces += 1
            if face.get('stone') and rng.random() < 0.3:
                flake_points.append((point.x, point.y, z + 0.006))
    if faces:
        obj = _mesh_object(PREFIX + 'wet leaves and fragments', verts, faces, None, collection, 'leaf')
        for leaf in leaves:
            obj.data.materials.append(leaf)
        for polygon, index in zip(obj.data.polygons, indices):
            polygon.material_index = index
    flakes = 0
    if flake_points:
        proto_collection = bpy.data.collections.get(PREFIX + 'flake prototype')
        if proto_collection is None:
            proto_collection = bpy.data.collections.new(PREFIX + 'flake prototype')
            scene.collection.children.link(proto_collection)
        _flake_prototype(scene, stone, proto_collection)
        _instance_randomly(PREFIX + 'fallen stone flakes', flake_points, proto_collection, collection, 'trim', 194,
                           scale_range=((0.025, 0.023, 0.025), (0.14, 0.12, 0.12)))
        flakes = len(flake_points)
    return {'litter_pieces': pieces, 'stone_flakes': flakes}


# ----------------------------------------------------------------------------------------------- the one call

def remove_details(scene):
    for obj in list(scene.objects):
        if obj.name.startswith(PREFIX):
            bpy.data.objects.remove(obj, do_unlink=True)
    for collection in list(bpy.data.collections):
        if collection.name.startswith(PREFIX) and not collection.objects:
            bpy.data.collections.remove(collection)


def lay_details(scene, materials, role_from_name, *, wet=1.0, grime=1.0, growth_amount=1.0, litter_amount=1.0, seed=93711):
    """
    materials: a dictionary with keys water, grime, soot, rust, moss, greens (a list), leaves (a list), stone.
    Returns a report of counts.
    """
    remove_details(scene)
    rng = random.Random(seed)
    collection = _collection(scene)
    roles = {o.name: role_of(o, role_from_name) for o in scene.objects if o.type == 'MESH' and not is_added(o)}
    camera_spot = scene.camera.matrix_world.translation if scene.camera else Vector((0, 0, 1.6))
    ground_z = ground_probe(scene)
    roads = road_footprints(scene, roles)
    road_centre = Vector(((roads[0][0] + roads[0][1]) / 2, (roads[0][2] + roads[0][3]) / 2, 0)) if roads else camera_spot
    faces_list = wall_faces(scene, roles, camera_spot)
    kerbs = kerb_lines(scene, roles, road_centre, ground_z)
    feet = iron_feet(scene, roles)
    report = {'wall_faces': len(faces_list), 'kerb_lines': len(kerbs), 'roads': len(roads), 'iron_things': len(feet)}
    if wet > 0:
        report.update(puddles(scene, roads, kerbs, materials['water'], collection, rng, wet, camera_spot, roles))
    if grime > 0:
        report.update(wall_damp_and_soot(scene, faces_list, materials['grime'], materials['soot'], collection, rng, grime, camera_spot, ground_z))
        report.update(rust_under_iron(scene, feet, faces_list, materials['rust'], materials['soot'], collection, rng, grime, camera_spot, ground_z))
    if growth_amount > 0:
        report.update(growth(scene, faces_list, kerbs, materials['greens'], materials['moss'], collection, rng, growth_amount, camera_spot, ground_z))
        report.update(road_life(scene, kerbs, materials['greens'], materials['moss'], collection, rng, growth_amount, camera_spot))
    if litter_amount > 0:
        report.update(litter(scene, faces_list, kerbs, materials['leaves'], materials['stone'], collection, rng, litter_amount, camera_spot, ground_z))
        steps = door_steps(scene, roles, faces_list)
        sand_objects = [o for o in scene.objects if o.type == 'MESH' and not is_added(o) and roles.get(o.name) == 'sand']
        shore = bool(sand_objects or any(r == 'sea' for r in roles.values())) and not roads
        report.update(rubbish(scene, faces_list, kerbs, [(c, s) for c, s, o in steps], materials['paper'], collection, rng,
                              litter_amount, scene.camera, ground_z, shore=shore, sand_objects=sand_objects if shore else ()))
        report['rubbish_kind'] = 'shore: shells, coral, seaweed' if shore else 'street: coal, cinders, ash, straw, paper'
    if grime > 0:
        whitened = _simple_material(PREFIX + 'whitened worn doorstep', (0.42, 0.40, 0.34), 0.75, (0.62, 0.58, 0.48), scale=9.0)
        for centre, size, obj in door_steps(scene, roles, faces_list):
            if not obj.get('detail_kept_material'):
                obj['detail_kept_material'] = obj.data.materials[0].name if obj.data.materials else ''
                obj.data.materials.clear()
                obj.data.materials.append(whitened)
        report['doorsteps_whitened'] = len(door_steps(scene, roles, faces_list))
        rusted = 0
        for foot, height in feet:
            for obj in scene.objects:
                if obj.type == 'MESH' and roles.get(obj.name) == 'iron' and not is_added(obj) and 'pipe' in obj.name.lower():
                    if not obj.get('detail_kept_material'):
                        obj['detail_kept_material'] = obj.data.materials[0].name if obj.data.materials else ''
                        obj.data.materials.clear()
                        obj.data.materials.append(materials['rust'])
                        rusted += 1
            break
        report['pipes_rusted'] = rusted
    return report
