# What this does: a fresh checker's own measure of a finished village, made from the scene's real geometry and never from the kit's plan masks.
# It opens nothing and saves nothing: run it inside Blender on an open scene. It writes one JSON file with:
#   1. where every small plant, litter piece and stone stands: at a wall foot (within 0.35 m of a building's wall, footing, post or door), along a road
#      edge or on a verge (within 0.6 m of a road's edge, or on a verge ground), on a seam (within 0.35 m of the line where two other grounds meet),
#      at the foot of a fence, post, prop, rock or tree trunk (within 0.35 m), on the road away from its edges, or in open ground; counted for the
#      pieces the four view cameras can frame (within 60 m and 30 m), and for all; plus the share of the framed GROUND AREA each place takes, so a
#      share of pieces can be compared with a share of area (an even spread gives the same share of pieces as of area);
#   2. each material's surface facts read from its nodes: normal map nodes and their pictures, displacement, the wear nodes found by name, coat and roughness;
#   3. the ground meshes' vertex spacing and the road material's repeat size and displacement settings;
#   4. the shape of every puddle (length, width), the leaf angle of the fern pieces, the stone sizes;
#   5. what a camera sees at chosen pixels (object and material), to name the things seen in the pictures.
# Use: blender -b FILE.blend --python measure_village.py -- OUT.json
import base64
import json
import math
import sys
import time

import bpy
import mathutils
import numpy as np
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

started = time.time()
output_path = sys.argv[sys.argv.index('--') + 1]
scene = bpy.context.scene
depsgraph = bpy.context.evaluated_depsgraph_get()
BUILDING_OWNERS = {'cottages_north', 'cottages_south', 'stable'}
VIEW_CAMERAS = ['View wide', 'View road_eye', 'View stable_close', 'View cottage_close']
WALL_FOOT_METRES = 0.35
ROAD_EDGE_METRES = 0.6
SEAM_METRES = 0.35
STANDING_METRES = 0.35
RNG = np.random.default_rng(7)


def role_of(obj):
    return str(obj.get('place_role') or '')


def world_mesh(obj):
    """(vertices (n,3) world, triangles (m,3)) of an object's evaluated mesh."""
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    mesh.calc_loop_triangles()
    count = len(mesh.vertices)
    vertices = np.empty(count * 3, dtype=np.float64)
    mesh.vertices.foreach_get('co', vertices)
    vertices = vertices.reshape(-1, 3)
    triangles = np.empty(len(mesh.loop_triangles) * 3, dtype=np.int64)
    mesh.loop_triangles.foreach_get('vertices', triangles)
    triangles = triangles.reshape(-1, 3)
    matrix = np.array(obj.matrix_world)
    vertices = vertices @ matrix[:3, :3].T + matrix[:3, 3]
    evaluated.to_mesh_clear()
    return vertices, triangles


def bvh_of(objects):
    """One BVH of many objects, and for each triangle the index of its object."""
    all_vertices, all_triangles, owner = [], [], []
    offset = 0
    for index, obj in enumerate(objects):
        vertices, triangles = world_mesh(obj)
        if len(triangles) == 0:
            continue
        all_vertices.append(vertices)
        all_triangles.append(triangles + offset)
        owner.append(np.full(len(triangles), index))
        offset += len(vertices)
    if not all_vertices:
        return None, np.zeros(0, dtype=np.int64)
    vertices = np.concatenate(all_vertices)
    triangles = np.concatenate(all_triangles)
    tree = BVHTree.FromPolygons(vertices.tolist(), triangles.tolist())
    return tree, np.concatenate(owner)


def boundary_points(obj, spacing=0.05):
    """Points every `spacing` metres along the open (boundary) edges of a mesh object, in world XY, with their Z."""
    mesh = obj.data
    edge_count = np.zeros(len(mesh.edges), dtype=np.int64)
    loop_edges = np.empty(len(mesh.loops), dtype=np.int64)
    mesh.loops.foreach_get('edge_index', loop_edges)
    np.add.at(edge_count, loop_edges, 1)
    edge_vertices = np.empty(len(mesh.edges) * 2, dtype=np.int64)
    mesh.edges.foreach_get('vertices', edge_vertices)
    edge_vertices = edge_vertices.reshape(-1, 2)[edge_count == 1]
    coords = np.empty(len(mesh.vertices) * 3)
    mesh.vertices.foreach_get('co', coords)
    coords = coords.reshape(-1, 3)
    matrix = np.array(obj.matrix_world)
    coords = coords @ matrix[:3, :3].T + matrix[:3, 3]
    points = []
    for a, b in edge_vertices:
        p, q = coords[a], coords[b]
        steps = max(1, int(math.ceil(np.linalg.norm(q[:2] - p[:2]) / spacing)))
        t = np.linspace(0.0, 1.0, steps + 1)[:, None]
        points.append(p + (q - p) * t)
    return np.concatenate(points) if points else np.zeros((0, 3))


def kd_of(points):
    tree = KDTree(len(points))
    for i, p in enumerate(points):
        tree.insert((float(p[0]), float(p[1]), 0.0), i)
    tree.balance()
    return tree


def mean_edge_length(obj):
    mesh = obj.data
    coords = np.empty(len(mesh.vertices) * 3)
    mesh.vertices.foreach_get('co', coords)
    coords = coords.reshape(-1, 3) * np.array(obj.matrix_world.to_scale())
    edges = np.empty(len(mesh.edges) * 2, dtype=np.int64)
    mesh.edges.foreach_get('vertices', edges)
    edges = edges.reshape(-1, 2)
    lengths = np.linalg.norm(coords[edges[:, 0]] - coords[edges[:, 1]], axis=1)
    return float(np.median(lengths)), float(lengths.mean())


# ------------------------------------------------------------------ the scene's parts
objects = [o for o in scene.objects if o.type == 'MESH' and o.visible_get()]
grounds = [o for o in objects if role_of(o).startswith('ground.')]
roads = [o for o in grounds if role_of(o) == 'ground.dirt_road']
verges = [o for o in grounds if 'verge' in o.name.lower()]
others = [o for o in grounds if o not in roads and o not in verges]
building_parts = [o for o in objects if o.get('place_owner') in BUILDING_OWNERS and not role_of(o).startswith(('roof.', 'prop.', 'never.', 'floor.', 'iron.'))]
standing = [o for o in objects if o.get('place_owner') not in BUILDING_OWNERS and (role_of(o).startswith(('timber.fence', 'timber.post', 'timber.generic', 'prop.', 'stone.rock', 'stone.well', 'tree.bark')))]
roofs = [o for o in objects if role_of(o).startswith('roof.')]
scatter = [o for o in scene.objects if o.type == 'MESH' and o.get('pk_scatter')]

ground_tree, ground_owner = bvh_of(grounds)
wall_tree, _ = bvh_of(building_parts)
standing_tree, _ = bvh_of(standing)
roof_tree, _ = bvh_of(roofs)
road_edge = np.concatenate([boundary_points(o) for o in roads])
seam = np.concatenate([boundary_points(o) for o in others + verges])
seam = seam[np.maximum(np.abs(seam[:, 0]), np.abs(seam[:, 1])) < 185.0]            # not the outer rim of the whole place
road_kd = kd_of(road_edge)
seam_kd = kd_of(seam) if len(seam) else None
timing = {'parts_seconds': round(time.time() - started, 1)}


def ground_under(x, y, z_hint=None):
    hit = ground_tree.ray_cast(mathutils.Vector((x, y, 80.0)), mathutils.Vector((0.0, 0.0, -1.0)), 200.0)
    if hit[0] is None:
        return None, None
    return hit[0].z, grounds[int(ground_owner[hit[2]])]


def classify(x, y, z):
    """The place a point on the ground belongs to (the first that fits, in this order)."""
    base = mathutils.Vector((x, y, z + 0.10))
    if wall_tree is not None and wall_tree.find_nearest(base, WALL_FOOT_METRES)[0] is not None:
        return 'wall_foot'
    _, ground_obj = ground_under(x, y)
    road_distance = road_kd.find((x, y, 0.0))[2]
    if road_distance <= ROAD_EDGE_METRES or (ground_obj is not None and ground_obj in verges):
        return 'road_edge_or_verge'
    if seam_kd is not None and seam_kd.find((x, y, 0.0))[2] <= SEAM_METRES:
        return 'seam'
    if standing_tree is not None and standing_tree.find_nearest(base, STANDING_METRES)[0] is not None:
        return 'foot_of_fence_post_prop_rock_or_tree'
    if ground_obj is not None and ground_obj in roads:
        return 'on_road_away_from_edges'
    return 'open_ground'


PLACES = ['wall_foot', 'road_edge_or_verge', 'seam', 'foot_of_fence_post_prop_rock_or_tree', 'on_road_away_from_edges', 'open_ground']


# ------------------------------------------------------------------ what the four view cameras frame
def camera_frames():
    frames = []
    for name in VIEW_CAMERAS:
        camera = scene.objects.get(name)
        if camera is None:
            continue
        corners = camera.data.view_frame(scene=scene)
        half_x = max(abs(c.x / -c.z) for c in corners)
        half_y = max(abs(c.y / -c.z) for c in corners)
        inverse = np.array(camera.matrix_world.inverted())
        frames.append((name, inverse, half_x, half_y, np.array(camera.matrix_world.translation)))
    return frames


FRAMES = camera_frames()


def framed(points, reach):
    """Boolean per point: inside at least one view camera's frame and within `reach` metres of it (no hiding behind things is counted)."""
    inside = np.zeros(len(points), dtype=bool)
    for _, inverse, half_x, half_y, _origin in FRAMES:
        local = points @ inverse[:3, :3].T + inverse[:3, 3]
        depth = -local[:, 2]
        ok = (depth > 0.1) & (depth <= reach)
        ok &= np.abs(local[:, 0]) <= half_x * np.maximum(depth, 1e-6)
        ok &= np.abs(local[:, 1]) <= half_y * np.maximum(depth, 1e-6)
        inside |= ok
    return inside


# ------------------------------------------------------------------ 1. where the pieces stand
pieces = []
for obj in scatter:
    block = bpy.data.texts.get('pk_roots_' + obj.name)
    if block is None:
        continue
    roots = np.frombuffer(base64.b64decode(block.as_string().encode('ascii')), dtype=np.float32).reshape(-1, 3).astype(np.float64)
    for root in roots:
        pieces.append((obj.get('pk_scatter_group'), obj.get('pk_scatter_kind'), root))
roots = np.array([p[2] for p in pieces]) if pieces else np.zeros((0, 3))
in_60 = framed(roots, 60.0)
in_30 = framed(roots, 30.0)
place_of = []
under_roof = 0
for group, kind, root in pieces:
    place_of.append(classify(root[0], root[1], root[2]))
    if roof_tree is not None and roof_tree.ray_cast(mathutils.Vector((root[0], root[1], root[2] + 0.05)), mathutils.Vector((0, 0, 1)), 15.0)[0] is not None:
        under_roof += 1
timing['pieces_seconds'] = round(time.time() - started, 1)


def tally(mask):
    result = {}
    for group in ('plant', 'litter', 'stone'):
        chosen = [place_of[i] for i in range(len(pieces)) if mask[i] and pieces[i][0] == group]
        total = len(chosen)
        counts = {place: chosen.count(place) for place in PLACES}
        result[group] = {'count': total, 'by_place': counts, 'shares': {place: (round(counts[place] / total, 4) if total else None) for place in PLACES}}
    return result


every = np.ones(len(pieces), dtype=bool)
piece_facts = {'framed_within_60m': tally(in_60), 'framed_within_30m': tally(in_30), 'all': tally(every), 'under_a_roof': under_roof,
               'kinds': {kind: int(sum(1 for p in pieces if p[1] == kind)) for kind in sorted({p[1] for p in pieces})}}

# the share of the framed ground area each place takes: random points on the ground the cameras frame
area_facts = {}
for reach in (60.0, 30.0):
    origins = np.array([f[4] for f in FRAMES])
    low = origins[:, :2].min(axis=0) - reach
    high = origins[:, :2].max(axis=0) + reach
    samples = []
    tries = 0
    while len(samples) < 30000 and tries < 60:
        tries += 1
        xy = RNG.uniform(low, high, size=(20000, 2))
        candidates = []
        for x, y in xy:
            z, ground_obj = ground_under(float(x), float(y))
            if z is not None:
                candidates.append((x, y, z))
        candidates = np.array(candidates)
        if len(candidates) == 0:
            continue
        keep = framed(candidates, reach)
        samples.extend(candidates[keep].tolist())
    samples = samples[:30000]
    places = [classify(x, y, z) for x, y, z in samples]
    area_facts[f'framed_within_{int(reach)}m'] = {'samples': len(samples), 'shares': {place: round(places.count(place) / max(len(places), 1), 4) for place in PLACES}}
timing['area_seconds'] = round(time.time() - started, 1)

# ------------------------------------------------------------------ 2. the surfaces, read from each material's nodes
WEAR_WORDS = ('dirt', 'grime', 'weather', 'crack', 'chip', 'edge', 'moss', 'algae', 'wet', 'rust', 'rubbish', 'damage', 'stain', 'puddle', 'seam', 'blend')


def upstream(node, seen=None):
    seen = seen if seen is not None else set()
    if node in seen:
        return seen
    seen.add(node)
    for socket in node.inputs:
        for link in socket.links:
            upstream(link.from_node, seen)
    return seen


def node_words(tree, depth=0):
    words = []
    for node in tree.nodes:
        words.append((node.name + ' ' + node.label).lower())
        if node.type == 'GROUP' and node.node_tree is not None and depth < 3:
            words.append(node.node_tree.name.lower())
            words.extend(node_words(node.node_tree, depth + 1))
    return words


used_materials = {}
for obj in objects:
    if obj.get('pk_scatter'):
        continue
    for slot in obj.material_slots:
        if slot.material is not None:
            used_materials.setdefault(slot.material.name, []).append(obj.name)
material_facts = {}
for name, users in sorted(used_materials.items()):
    material = bpy.data.materials[name]
    entry = {'users': len(users), 'role': role_of(scene.objects[users[0]])}
    if not material.use_nodes or material.node_tree is None:
        entry['nodes'] = False
        material_facts[name] = entry
        continue
    tree = material.node_tree
    output = next((n for n in tree.nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output), None) or next((n for n in tree.nodes if n.type == 'OUTPUT_MATERIAL'), None)
    surface_nodes = upstream(output.inputs['Surface'].links[0].from_node) if output and output.inputs['Surface'].is_linked else set()
    normal_maps = [n for n in surface_nodes if n.type == 'NORMAL_MAP']
    bumps = [n for n in surface_nodes if n.type == 'BUMP']
    images = sorted({n.image.name for n in tree.nodes if n.type == 'TEX_IMAGE' and n.image is not None})
    normal_images = sorted({m.image.name for nm in normal_maps for m in upstream(nm) if m.type == 'TEX_IMAGE' and m.image is not None})
    bsdfs = [n for n in surface_nodes if n.type == 'BSDF_PRINCIPLED']
    reaches = any(b.inputs['Normal'].is_linked for b in bsdfs)
    displacement_linked = bool(output and output.inputs['Displacement'].is_linked)
    displacement_images = []
    displacement_scale = None
    if displacement_linked:
        displacement_nodes = upstream(output.inputs['Displacement'].links[0].from_node)
        displacement_images = sorted({m.image.name for m in displacement_nodes if m.type == 'TEX_IMAGE' and m.image is not None})
        for m in displacement_nodes:
            if m.type == 'DISPLACEMENT':
                displacement_scale = None if m.inputs['Scale'].is_linked else round(float(m.inputs['Scale'].default_value), 4)
    words = ' | '.join(node_words(tree))
    wet_dials = {}
    for node in tree.nodes:
        if node.type == 'GROUP':
            for socket in node.inputs:
                if any(word in socket.name.lower() for word in ('coat', 'wet', 'puddle', 'darken')) and not socket.is_linked and hasattr(socket, 'default_value'):
                    try:
                        wet_dials[f'{node.name}: {socket.name}'] = round(float(socket.default_value), 3)
                    except TypeError:
                        pass
    entry['wet_dials'] = wet_dials
    coat = [(round(float(b.inputs['Coat Weight'].default_value), 3), b.inputs['Coat Weight'].is_linked) for b in bsdfs if 'Coat Weight' in b.inputs]
    roughness = [(round(float(b.inputs['Roughness'].default_value), 3), b.inputs['Roughness'].is_linked) for b in bsdfs]
    entry.update({'nodes': len(tree.nodes), 'images': images, 'normal_map_nodes': len(normal_maps), 'normal_map_images': normal_images, 'bump_nodes': len(bumps),
                  'normal_reaches_bsdf': reaches, 'displacement_linked': displacement_linked, 'displacement_method': getattr(material, 'displacement_method', None),
                  'displacement_images': displacement_images, 'displacement_scale': displacement_scale,
                  'wear_words': {w: words.count(w) for w in WEAR_WORDS if words.count(w)}, 'coat': coat, 'roughness': roughness})
    material_facts[name] = entry
timing['materials_seconds'] = round(time.time() - started, 1)

# ------------------------------------------------------------------ 3. ground meshes and the road material's repeat size
ground_facts = {}
for obj in grounds:
    median_edge, mean_edge = mean_edge_length(obj)
    ground_facts[obj.name] = {'role': role_of(obj), 'vertices': len(obj.data.vertices), 'median_edge_metres': round(median_edge, 4), 'mean_edge_metres': round(mean_edge, 4),
                              'modifiers': [(m.type, m.name) for m in obj.modifiers], 'materials': [m.name for m in obj.data.materials if m]}
road_material_facts = {}
for material in {m for o in roads for m in o.data.materials if m}:
    found = {'mapping_scales': [], 'images': []}
    for node in material.node_tree.nodes:
        if node.type == 'MAPPING':
            found['mapping_scales'].append([round(float(v), 4) for v in node.inputs['Scale'].default_value])
        if node.type == 'TEX_IMAGE' and node.image is not None:
            found['images'].append({'name': node.image.name, 'size': list(node.image.size), 'packed': node.image.packed_file is not None, 'file': bpy.path.basename(node.image.filepath)})
        if node.type == 'DISPLACEMENT':
            found['displacement'] = {'scale': float(node.inputs['Scale'].default_value), 'midlevel': float(node.inputs['Midlevel'].default_value), 'scale_linked': node.inputs['Scale'].is_linked}
        if node.type == 'VALUE' and node.label:
            found.setdefault('values', {})[node.label] = round(float(node.outputs[0].default_value), 4)
    found['custom'] = {k: (v if isinstance(v, (int, float, str)) else str(v)) for k, v in material.items()}
    road_material_facts[material.name] = found


# ------------------------------------------------------------------ 4. puddles, fern leaves, stones
def islands(obj):
    """Vertex groups of connected pieces of a mesh (union-find over edges), as world coordinates."""
    mesh = obj.data
    count = len(mesh.vertices)
    parent = np.arange(count)

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    edges = np.empty(len(mesh.edges) * 2, dtype=np.int64)
    mesh.edges.foreach_get('vertices', edges)
    for a, b in edges.reshape(-1, 2):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    roots = np.array([find(i) for i in range(count)])
    coords = np.empty(count * 3)
    mesh.vertices.foreach_get('co', coords)
    coords = coords.reshape(-1, 3)
    matrix = np.array(obj.matrix_world)
    coords = coords @ matrix[:3, :3].T + matrix[:3, 3]
    order = np.argsort(roots)
    split = np.split(order, np.flatnonzero(np.diff(roots[order])) + 1)
    return [coords[s] for s in split]


puddle_facts = {}
puddle_object = scene.objects.get('PK puddles')
if puddle_object is not None:
    shapes = []
    for points in islands(puddle_object):
        xy = points[:, :2] - points[:, :2].mean(axis=0)
        if len(xy) < 3:
            continue
        _, _, axes = np.linalg.svd(xy, full_matrices=False)
        along = xy @ axes[0]
        across = xy @ axes[1]
        shapes.append((float(along.max() - along.min()), float(across.max() - across.min()), points[:, :2].mean(axis=0).tolist()))
    lengths = np.array([s[0] for s in shapes])
    widths = np.array([max(s[1], 1e-3) for s in shapes])
    ratio = lengths / widths
    puddle_facts = {'pieces': len(shapes), 'length_median_m': round(float(np.median(lengths)), 3), 'length_max_m': round(float(lengths.max()), 3),
                    'width_median_m': round(float(np.median(widths)), 3), 'length_over_width_median': round(float(np.median(ratio)), 2),
                    'share_longer_than_2m': round(float((lengths > 2.0).mean()), 3), 'share_ratio_over_4': round(float((ratio > 4).mean()), 3),
                    'longest_five': sorted([(round(s[0], 2), round(s[1], 2)) for s in shapes], reverse=True)[:5],
                    'within_15m_of_road_eye': int(sum(1 for s in shapes if math.dist(s[2], (-62.0, -3.7)) < 15.0))}


def leaf_angles(kind):
    chosen = [o for o in scatter if o.get('pk_scatter_kind') == kind]
    upright_area, total_area, nz_sum = 0.0, 0.0, 0.0
    for obj in chosen:
        mesh = obj.data
        normals = np.empty(len(mesh.polygons) * 3)
        mesh.polygons.foreach_get('normal', normals)
        areas = np.empty(len(mesh.polygons))
        mesh.polygons.foreach_get('area', areas)
        nz = np.abs(normals.reshape(-1, 3)[:, 2])
        upright_area += float(areas[nz < 0.5].sum())
        total_area += float(areas.sum())
        nz_sum += float((nz * areas).sum())
    if total_area == 0:
        return None
    return {'share_of_leaf_area_steeper_than_60_degrees': round(upright_area / total_area, 3), 'mean_abs_normal_z': round(nz_sum / total_area, 3)}


leaf_facts = {kind: leaf_angles(kind) for kind in ('fern', 'bramble', 'nettle', 'clover', 'tuft', 'moss_cushion')}
stone_facts = {}
for kind in ('pebble', 'cobble'):
    sizes = []
    for obj in [o for o in scatter if o.get('pk_scatter_kind') == kind]:
        for points in islands(obj):
            extent = points.max(axis=0) - points.min(axis=0)
            sizes.append(float(extent[:2].max()))
    if sizes:
        sizes = np.array(sizes) * 1000.0
        stone_facts[kind] = {'pieces': len(sizes), 'largest_side_mm_p5': round(float(np.percentile(sizes, 5)), 1), 'median_mm': round(float(np.median(sizes)), 1),
                             'p95_mm': round(float(np.percentile(sizes, 95)), 1)}
timing['shapes_seconds'] = round(time.time() - started, 1)

# ------------------------------------------------------------------ 5. what a camera sees at chosen pixels (1200 x 800 pictures)
PROBES = {'View road_eye': [(60, 600), (150, 640), (200, 570), (1000, 600), (1100, 640), (1150, 700), (440, 512), (693, 506), (593, 580), (232, 690), (300, 560), (900, 560)],
          'View cottage_close': [(100, 600), (195, 600), (215, 600), (60, 450)],
          'View wide': [(230, 470), (720, 560), (100, 330), (300, 650)]}
probe_facts = {}
for name, pixels in PROBES.items():
    camera = scene.objects.get(name)
    if camera is None:
        continue
    frame = camera.data.view_frame(scene=scene)            # top-right, bottom-right, bottom-left, top-left in camera space
    top_right, bottom_right, bottom_left, top_left = frame
    origin = camera.matrix_world.translation
    rows = []
    for px, py in pixels:
        u, v = (px + 0.5) / 1200.0, (py + 0.5) / 800.0
        top = top_left.lerp(top_right, u)
        bottom = bottom_left.lerp(bottom_right, u)
        local = top.lerp(bottom, v)
        direction = (camera.matrix_world.to_3x3() @ local).normalized()
        hit, location, normal, index, hit_object, _ = scene.ray_cast(depsgraph, origin, direction)
        material = None
        if hit and hit_object.type == 'MESH':
            evaluated = hit_object.evaluated_get(depsgraph)
            data = evaluated.data
            if 0 <= index < len(data.polygons) and data.materials:
                slot = data.polygons[index].material_index
                material = data.materials[slot].name if slot < len(data.materials) and data.materials[slot] else None
        rows.append({'pixel': [px, py], 'object': hit_object.name if hit else None, 'material': material, 'distance_m': round((location - origin).length, 2) if hit else None})
    probe_facts[name] = rows

result = {'scene': bpy.data.filepath, 'timing': timing, 'thresholds_metres': {'wall_foot': WALL_FOOT_METRES, 'road_edge': ROAD_EDGE_METRES, 'seam': SEAM_METRES, 'standing_things': STANDING_METRES},
          'parts': {'grounds': [o.name for o in grounds], 'roads': [o.name for o in roads], 'verges': [o.name for o in verges], 'building_parts': len(building_parts),
                    'standing_things': len(standing), 'road_edge_points': len(road_edge), 'seam_points': len(seam), 'scatter_objects': len(scatter), 'pieces': len(pieces)},
          'pieces': piece_facts, 'area': area_facts, 'materials': material_facts, 'grounds': ground_facts, 'road_material': road_material_facts,
          'puddles': puddle_facts, 'leaves': leaf_facts, 'stones': stone_facts, 'probes': probe_facts}
result['timing']['total_seconds'] = round(time.time() - started, 1)
with open(output_path, 'w') as handle:
    json.dump(result, handle, indent=1)
print('MEASURED', output_path, result['timing'])
