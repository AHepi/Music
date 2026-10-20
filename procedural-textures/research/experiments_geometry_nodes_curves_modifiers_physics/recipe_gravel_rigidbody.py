# What this does: RECIPE 3 - makes gravel by DROPPING real stones with Blender's Rigid Body physics, letting them settle into a pile, and then
# photographing the pile from straight above (height, colour, normal pictures of a 1 x 1 tile). The pile is made to WRAP (seamless) with a trick:
# every stone has 8 "ghost" copies (one tile to the left, right, up, down and the four diagonals). The ghosts are kinematic bodies that this script
# moves to follow their real stone after every physics step, so a stone near the tile edge sits against the stones on the other side of the seam.
# Steps:
#   1. make a few angular stone shapes: convex hull of random points on a squashed sphere (bmesh), merged into flat facets
#   2. choose stone sizes (a few big, more medium, many small), place them at random heights over the tile without overlapping (distances measured the
#      wrap-around way)
#   3. Rigid Body: stones ACTIVE (convex hull shape, small margin, friction 0.9), a PASSIVE floor, ghosts PASSIVE + animated. The physics world is 10 times
#      bigger than the tile (tile = 10 x 10 units) because Bullet is happier with objects that are not tiny.
#   4. step the physics from Python (scene.frame_set) and after every step move the ghosts to follow the stones
#   5. read the final positions, copy each stone (and its wrap-around copies that touch the tile) into ONE mesh with a flat colour per facet
#      (stone type colour x a pretend light on the facet's direction -> the painted look of the references), add an earth sheet made with Geometry Nodes
#   6. photograph it with gn_tools.photograph_geometry
# Run:  blender -b --disable-autoexec -t 2 --python recipe_gravel_rigidbody.py -- OUT_FOLDER [--size 1254] [--ghosts 1|0] [--big 14 --medium 55 --small 170] [--frames 150]
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bmesh  # noqa: E402
import bpy  # noqa: E402
import numpy as np  # noqa: E402
import gn_tools as gt  # noqa: E402

L = 10.0   # size of the tile in the physics world
DEFAULTS = dict(seed=3, big=34, medium=140, small=360, tiny=300, frames=190, ghosts=False, ghost_tiny=False, rounds=3, later_frames=90, variants=10, time_scale=1.0, linear_damping=0.7, angular_damping=0.4, substeps=10, ghost_scale=1.0, solver_iterations=30, max_drop_height=14.0)


# ----------------------------------------------------------------------------------------------------- 1. stone shapes
def make_stone_shapes(rng, count):
    """count different angular stones, each a (vertices, triangles) pair with the largest distance from the centre = 0.5 (so size = width)."""
    shapes = []
    for _ in range(count):
        # blocky stone: points scattered over the surface of a box with random proportions (so the hull has big flat faces and cut corners)
        dims = np.array([1.0, rng.uniform(0.6, 0.95), rng.uniform(0.35, 0.7)])
        n = int(rng.integers(12, 20))
        face = rng.integers(0, 3, size=n)
        points = rng.uniform(-0.5, 0.5, size=(n, 3)) * dims
        sign = rng.choice([-1.0, 1.0], size=n)
        for k in range(n):
            points[k, face[k]] = sign[k] * 0.5 * dims[face[k]]
        points += rng.normal(0, 0.035, size=points.shape)
        bm = bmesh.new()
        for point in points:
            bm.verts.new(point)
        bmesh.ops.convex_hull(bm, input=bm.verts)
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
        bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(9), verts=bm.verts, edges=bm.edges)
        centre = np.mean([v.co[:] for v in bm.verts], axis=0)
        for v in bm.verts:
            v.co = (np.array(v.co[:]) - centre).tolist()
        scale = 0.5 / max(v.co.length for v in bm.verts)
        for v in bm.verts:
            v.co = v.co * scale
        mesh = bpy.data.meshes.new('stone shape')
        bm.to_mesh(mesh)
        bm.free()
        for polygon in mesh.polygons:
            polygon.use_smooth = False
        vertices = np.array([v.co[:] for v in mesh.vertices])
        triangles = []
        for polygon in mesh.polygons:
            indices = list(polygon.vertices)
            for k in range(1, len(indices) - 1):
                triangles.append((indices[0], indices[k], indices[k + 1]))
        shapes.append({'mesh': mesh, 'vertices': vertices, 'triangles': np.array(triangles),
                       'planes': [(np.array(p.normal[:]), float(np.dot(p.normal, mesh.vertices[p.vertices[0]].co))) for p in mesh.polygons]})
    return shapes


# ----------------------------------------------------------------------------------------------------- 2. sizes and starting places
def stone_list(rng, p):
    stones = []
    for kind, count, low, high in (('big', p['big'], 0.9, 1.35), ('medium', p['medium'], 0.45, 0.8), ('small', p['small'], 0.2, 0.4), ('tiny', p['tiny'], 0.09, 0.2)):
        for _ in range(count):
            stones.append({'kind': kind, 'size': float(rng.uniform(low, high))})
    return stones


def place_without_overlap(rng, stones, height=14.0):
    """Random start positions, biggest first, so no two stones overlap (distance between centres measured with wrap-around in x and y)."""
    placed = np.zeros((0, 4))
    for stone in stones:
        radius = stone['size'] * 0.5 * 1.15
        for attempt in range(2000):
            if attempt and attempt % 100 == 0:
                height *= 1.15          # the column is getting crowded: allow a taller one
            candidate = np.array([rng.uniform(0, L), rng.uniform(0, L), rng.uniform(radius + 0.3, height)])
            if len(placed):
                delta = np.abs(placed[:, :3] - candidate)
                delta[:, 0] = np.minimum(delta[:, 0], L - delta[:, 0])
                delta[:, 1] = np.minimum(delta[:, 1], L - delta[:, 1])
                if np.any(np.linalg.norm(delta, axis=1) < placed[:, 3] + radius):
                    continue
            break
        placed = np.vstack([placed, [*candidate, radius]])
        stone['start'] = candidate
        q = rng.normal(size=4)
        stone['rotation'] = q / np.linalg.norm(q)


# ----------------------------------------------------------------------------------------------------- 3 + 4. physics
def run_physics(p, rng, shapes, stones, log, keep_shapes=False):
    scene = bpy.context.scene
    started = time.time()
    collection = bpy.data.collections.new('stones')
    scene.collection.children.link(collection)
    objects = []
    for index, stone in enumerate(stones):
        if 'shape' not in stone:
            stone['shape'] = int(rng.integers(0, len(shapes)))
        obj = bpy.data.objects.new(f'stone{index}', shapes[stone['shape']]['mesh'])
        obj.rotation_mode = 'QUATERNION'
        obj.scale = (stone['size'],) * 3
        obj.location = stone['start']
        obj.rotation_quaternion = stone['rotation']
        collection.objects.link(obj)
        objects.append(obj)
    floor_mesh = bpy.data.meshes.new('floor')
    floor_mesh.from_pydata([(-L, -L, 0), (2 * L, -L, 0), (2 * L, 2 * L, 0), (-L, 2 * L, 0), (-L, -L, -1), (2 * L, -L, -1), (2 * L, 2 * L, -1), (-L, 2 * L, -1)], [],
                           [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)])
    floor = bpy.data.objects.new('floor', floor_mesh)
    collection.objects.link(floor)
    ghosts = []
    offsets = [(dx * L, dy * L) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx, dy) != (0, 0)]
    if p['ghosts']:
        for obj, stone in zip(objects, stones):
            if stone['kind'] == 'tiny' and not p['ghost_tiny']:
                continue
            for offset in offsets:
                ghost = bpy.data.objects.new(obj.name + ' ghost', obj.data)
                ghost.rotation_mode = 'QUATERNION'
                ghost.scale = tuple(c * p['ghost_scale'] for c in obj.scale)
                ghost.location = (obj.location.x + offset[0], obj.location.y + offset[1], obj.location.z)
                ghost.rotation_quaternion = obj.rotation_quaternion
                collection.objects.link(ghost)
                ghosts.append((obj, offset, ghost))
    log['objects_created_s'] = round(time.time() - started, 2)

    def add_bodies(items, body_type):
        for item in bpy.context.view_layer.objects:
            item.select_set(False)
        for item in items:
            item.select_set(True)
        bpy.context.view_layer.objects.active = items[0]
        bpy.ops.rigidbody.objects_add(type=body_type)

    started = time.time()
    bpy.ops.rigidbody.world_add()
    add_bodies([floor], 'PASSIVE')
    add_bodies(objects, 'ACTIVE')
    if ghosts:
        add_bodies([g for _, _, g in ghosts], 'PASSIVE')
    world = scene.rigidbody_world
    world.solver_iterations = p['solver_iterations']
    world.substeps_per_frame = p['substeps']
    world.time_scale = p['time_scale']
    world.point_cache.frame_start, world.point_cache.frame_end = 1, p['frames'] + 2
    scene.frame_start, scene.frame_end = 1, p['frames'] + 2
    floor.rigid_body.friction = 1.0
    floor.rigid_body.restitution = 0.0
    floor.rigid_body.collision_shape = 'BOX'
    for obj, stone in zip(objects, stones):
        rb = obj.rigid_body
        rb.mass = max(0.05, stone['size'] ** 3 * 2.5)
        rb.friction = 0.9
        rb.restitution = 0.05
        rb.collision_shape = 'CONVEX_HULL'
        rb.use_margin = True
        rb.collision_margin = 0.002
        rb.linear_damping = p['linear_damping']
        rb.angular_damping = p['angular_damping']
    for _, _, ghost in ghosts:
        rb = ghost.rigid_body
        rb.kinematic = True
        rb.friction = 0.9
        rb.collision_shape = 'CONVEX_HULL'
        rb.use_margin = True
        rb.collision_margin = 0.002
    log['rigid_body_setup_s'] = round(time.time() - started, 2)
    started = time.time()
    scene.frame_set(1)
    for frame in range(2, p['frames'] + 1):
        scene.frame_set(frame)
        bpy.context.view_layer.update()
        if ghosts:
            for obj, offset, ghost in ghosts:
                translation = obj.matrix_world.translation
                ghost.location = (translation.x + offset[0], translation.y + offset[1], translation.z)
                ghost.rotation_quaternion = obj.matrix_world.to_quaternion()
    log['physics_s'] = round(time.time() - started, 2)
    log['frames'] = p['frames']
    for obj, stone in zip(objects, stones):
        stone['final_location'] = np.array(obj.matrix_world.translation[:])
        stone['final_quaternion'] = np.array(obj.matrix_world.to_quaternion()[:])
    return objects


def clear_physics():
    """Remove the rigid body world and every stone/ghost/floor object (the stone SHAPE meshes stay), so a new round can start clean."""
    if bpy.context.scene.rigidbody_world:
        bpy.ops.rigidbody.world_remove()
    for collection in list(bpy.data.collections):
        for item in list(collection.objects):
            bpy.data.objects.remove(item)
        bpy.data.collections.remove(collection)


def shift_for_next_round(stones):
    """Next round starts from the settled pile, moved by half a tile in x and y (wrapping round), so the old seam is now in the middle of the
    physics area where stones really do push each other apart. A tiny lift keeps stones from starting inside the floor."""
    for stone in stones:
        location = stone['final_location']
        stone['start'] = np.array([(location[0] + L / 2) % L, (location[1] + L / 2) % L, location[2] + 0.01])
        stone['rotation'] = stone['final_quaternion']


# ----------------------------------------------------------------------------------------------------- 5. one mesh with painted facets
def quaternion_to_matrix(q):
    w, x, y, z = q / np.linalg.norm(q)
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


STONE_TYPES = {   # name: (chance for big/medium stones, light colour, dark colour)  sRGB 0-255, picked from the reference with analyse_reference_palettes.py
    'blue-grey': (0.42, (112, 122, 128), (52, 58, 66)),
    'black': (0.33, (52, 53, 58), (22, 22, 25)),
    'rusty': (0.12, (150, 95, 62), (96, 62, 44)),
    'tan': (0.05, (150, 120, 92), (100, 78, 60)),
    'green-grey': (0.08, (96, 106, 104), (56, 64, 62)),
}
SMALL_TYPES = {'brown': (0.45, (130, 92, 66), (82, 56, 40)), 'blue-grey': (0.25, (100, 108, 114), (50, 56, 62)), 'black': (0.2, (46, 46, 50), (22, 22, 25)),
               'rusty': (0.1, (160, 100, 62), (100, 64, 44))}


def build_pile_mesh(rng, stones, shapes, name='gravel pile'):
    light = np.array([-0.4, 0.55, 0.75])
    light /= np.linalg.norm(light)
    positions, colours, faces = [], [], []
    inside_count = 0
    for stone in stones:
        shape = shapes[stone['shape']]
        rotation = quaternion_to_matrix(stone['final_quaternion'])
        world = (shape['vertices'] * stone['size']) @ rotation.T + stone['final_location']
        table = STONE_TYPES if stone['kind'] in ('big', 'medium') else SMALL_TYPES
        names = list(table)
        chances = np.array([table[n][0] for n in names])
        type_name = names[int(rng.choice(len(names), p=chances / chances.sum()))]
        light_c, dark_c = (np.array(table[type_name][1]) / 255.0, np.array(table[type_name][2]) / 255.0)
        tone = rng.uniform(0.0, 1.0)
        base = dark_c + (light_c - dark_c) * tone
        stone['type'] = type_name
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                shifted = world + np.array([dx * L, dy * L, 0.0])
                if shifted[:, 0].max() < 0 or shifted[:, 0].min() > L or shifted[:, 1].max() < 0 or shifted[:, 1].min() > L:
                    continue
                inside_count += 1
                for triangle in shape['triangles']:
                    a, b, c = shifted[triangle[0]], shifted[triangle[1]], shifted[triangle[2]]
                    normal = np.cross(b - a, c - a)
                    length = np.linalg.norm(normal)
                    if length < 1e-12:
                        continue
                    normal /= length
                    shade = 0.62 + 0.62 * max(0.0, float(np.dot(normal, light))) + rng.normal(0, 0.035)
                    colour = np.clip(base * shade, 0, 1)
                    start = len(positions)
                    positions.extend([a / L, b / L, c / L])
                    colours.extend([(*colour, 1.0)] * 3)
                    faces.append((start, start + 1, start + 2))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([tuple(v) for v in positions], [], faces)
    attribute = mesh.attributes.new('piece_colour', 'FLOAT_COLOR', 'POINT')
    flat = np.array(colours, dtype=np.float32)
    # the colours above are sRGB-looking numbers; the attribute is read as linear light, so convert
    linear = np.where(flat[:, :3] > 0.04045, ((flat[:, :3] + 0.055) / 1.055) ** 2.4, flat[:, :3] / 12.92)
    flat[:, :3] = linear
    attribute.data.foreach_set('color', flat.ravel())
    for polygon in mesh.polygons:
        polygon.use_smooth = False
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj, inside_count


def count_overlaps(stones, shapes):
    """How many stone pairs push into each other after settling (measured with wrap-around). For each pair that is near, count the corners of one
    stone that lie deeper than 1% of its size inside the other stone (convex shapes: inside = behind all of that stone's face planes)."""
    transforms = []
    for stone in stones:
        shape = shapes[stone['shape']]
        rotation = quaternion_to_matrix(stone['final_quaternion'])
        world_vertices = (shape['vertices'] * stone['size']) @ rotation.T + stone['final_location']
        planes = [((rotation @ n), d * stone['size'] + float(np.dot(rotation @ n, stone['final_location']))) for n, d in shape['planes']]
        transforms.append((world_vertices, planes, stone['size']))
    count, deep = 0, 0
    for i in range(len(stones)):
        for j in range(len(stones)):
            if i == j:
                continue
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    offset = np.array([dx * L, dy * L, 0.0])
                    ci = stones[i]['final_location']
                    cj = stones[j]['final_location'] + offset
                    if np.linalg.norm(ci - cj) > (stones[i]['size'] + stones[j]['size']) * 0.62:
                        continue
                    vertices_i = transforms[i][0]
                    depth = np.full(len(vertices_i), np.inf)
                    for n, d in transforms[j][1]:
                        depth = np.minimum(depth, d - (vertices_i - offset) @ n + 0 * 0)   # vertices of i, expressed in j's frame
                    # depth>0 for every plane means inside; depth is the distance to the nearest face from inside
                    inside = depth > 0.01 * stones[i]['size']
                    if inside.any():
                        count += 1
                        if inside.sum() >= 2:
                            deep += 1
    return {'overlapping_pairs': count // 1, 'deep_overlaps_two_or_more_corners': deep}


# ----------------------------------------------------------------------------------------------------- the earth under the stones (Geometry Nodes)
def earth_object():
    tree, g = gt.make_geometry_group('Earth sheet', [('Geometry', 'NodeSocketGeometry', None)])
    noise = gt.tileable_noise_geo_group()
    g.node('GeometryNodeMeshGrid', 'grid', {'Size X': 1.0, 'Size Y': 1.0, 'Vertices X': 200, 'Vertices Y': 200})
    g.node('GeometryNodeTransform', 'move', {'Geometry': ('grid', 'Mesh'), 'Translation': (0.5, 0.5, 0.0)})
    g.node('GeometryNodeInputPosition', 'position')
    g.group('clumps', noise, {'Position': ('position', 'Position'), 'Scale': 38.0, 'Detail': 4.0, 'Roughness': 0.65, 'Seed': 4.0})
    g.node('ShaderNodeMapRange', 'clumps centred', {'Value': ('clumps', 'Fac'), 'From Min': 0.3, 'From Max': 0.7, 'To Min': -1.0, 'To Max': 1.0})
    g.math('bump', 'MULTIPLY', ('clumps centred', 'Result'), 0.003)
    g.node('ShaderNodeCombineXYZ', 'lift', {'Z': ('bump', 0)})
    g.node('GeometryNodeSetPosition', 'bumpy', {'Geometry': ('move', 'Geometry'), 'Offset': ('lift', 'Vector')})
    gt.make_ramp(g, 'earth', [(0.2, (62, 42, 30)), (0.5, (92, 62, 44)), (0.8, (128, 90, 62))], {'Fac': ('clumps', 'Fac')})
    g.node('GeometryNodeStoreNamedAttribute', 'colour', {'Geometry': ('bumpy', 'Geometry'), 'Name': 'piece_colour', 'Value': ('earth', 'Color')}, data_type='FLOAT_COLOR', domain='POINT')
    gt.finish_with_material_slot(g, 'colour')
    obj, _ = gt.add_geometry_object('earth', tree)
    return obj


def run(out_folder, size=1254, params=None, ambient_occlusion=0.8, quiet=False):
    p = {**DEFAULTS, **(params or {})}
    log = {'parameters': p}
    total = time.time()
    scene = gt.new_scene(size)
    # the scene helper above deletes everything; rigid body needs a world, which run_physics creates
    rng = np.random.default_rng(p['seed'])
    started = time.time()
    shapes = make_stone_shapes(rng, p['variants'])
    stones = stone_list(rng, p)
    place_without_overlap(rng, stones, p['max_drop_height'])
    log['shapes_and_placement_s'] = round(time.time() - started, 2)
    log['stones'] = len(stones)
    log['rounds'] = []
    for round_number in range(1, p['rounds'] + 1):
        if round_number > 1:
            shift_for_next_round(stones)
            clear_physics()
        round_log = {}
        run_physics({**p, 'frames': p['frames'] if round_number == 1 else p['later_frames']}, rng, shapes, stones, round_log, keep_shapes=True)
        # a stone that tunnelled through the floor (only with ghosts) is removed
        round_log['overlaps'] = count_overlaps(stones, shapes)
        log['rounds'].append(round_log)
        stones = [s_ for s_ in stones if s_['final_location'][2] > -0.3]
    zs = sorted(((s_['final_location'][2], s_['kind'], round(s_['size'], 2)) for s_ in stones), reverse=True)[:5]
    log['five_highest_stone_centres_(z, kind, size)'] = [(round(float(a), 2), b, c) for a, b, c in zs]
    log['overlaps_after_settling'] = log['rounds'][-1]['overlaps']
    log['stones_left'] = len(stones)
    started = time.time()
    pile, copies_inside = build_pile_mesh(rng, stones, shapes)
    earth = earth_object()
    log['pile_mesh_s'] = round(time.time() - started, 2)
    log['stone_copies_in_tile'] = copies_inside
    # hide the physics objects from the photograph
    for item in list(bpy.data.collections['stones'].objects):
        item.hide_render = True
        item.hide_viewport = True
    info = gt.photograph_geometry([pile, earth], out_folder, size=size, normal_reference='gravel', ambient_occlusion=ambient_occlusion, occlusion_distance=0.02,
                                  colour_samples=16 if ambient_occlusion else 4, quiet=True)
    log['photo'] = info
    log['total_seconds'] = round(time.time() - total, 1)
    os.makedirs(out_folder, exist_ok=True)
    with open(os.path.join(out_folder, 'photo.json'), 'w') as handle:
        json.dump(log, handle, indent=1, default=float)
    if not quiet:
        print('[gravel]', json.dumps(log, default=float))
    return log


if __name__ == '__main__':
    arguments = sys.argv[sys.argv.index('--') + 1:]
    option = lambda name, default=None: arguments[arguments.index(name) + 1] if name in arguments else default
    params = {'ghosts': option('--ghosts', '0') == '1', 'rounds': int(option('--rounds', DEFAULTS['rounds'])), 'big': int(option('--big', DEFAULTS['big'])), 'medium': int(option('--medium', DEFAULTS['medium'])),
              'small': int(option('--small', DEFAULTS['small'])), 'tiny': int(option('--tiny', DEFAULTS['tiny'])), 'frames': int(option('--frames', DEFAULTS['frames'])), 'seed': int(option('--seed', DEFAULTS['seed']))}
    run(arguments[0], size=int(option('--size', 1254)), params=params, ambient_occlusion=float(option('--ao', 0.8)))
