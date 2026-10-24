"""What this does: small MEASURING scripts the place kit's Blender tests run inside Blender. Each one opens a scene, measures one thing straight from Blender's own data (not from the
kit's audit), and writes the numbers as JSON for the test to judge. Nothing here is a verdict: the test file decides.
Run: blender -b --disable-autoexec SCENE.blend --python probe_place.py -- NAME OUT.json [options]
Probes:
  facts          every visible mesh: its role, its materials, whether each material has a normal map wired to the shader's Normal (with a Non-Color picture), a displacement node with its
                 method, varying roughness and colour, which wear layers are in, the per-object layer amounts; bevel and weighted-normal modifiers; counts of scatter objects
  directions     for every normal map the kit made: the correlation of its pixels with the height it came from, and the same for a copy with the green channel flipped
  renders        tiny Cycles pictures (no denoise, a fixed seed) of the open scene from the camera named in --camera: with the wear as it is, with the master at 0, with every layer
                 removed, and again as it is (for determinism), and with only one layer left in at a time; writes the picture differences
  uvs            the UV extent of every wall-like object compared with its size in metres (the texture is in metres)
  roads          the shape of the ground around a road: depth of each rut, the gauge, and how many kit plants stand on a wheel track, in a puddle or on a keep-clear spot
  construction   runs the construction check on the open scene and lists its findings by name
  roads          the lane measured from the real ground by rays (depth of each rut, the gauge between them) and every kit plant and litter root counted against the lane's own
                 geometry (not against the kit's masks): in a wheel rut, in the centre strip, near the lane, elsewhere
  damage         for every role with several objects: how many of them have a different shape from the others once the damage modifiers are applied; how far the objects still stand
                 from the ground; the strength of each damage modifier
  images         a fingerprint of every picture the kit made (name, size, colour space and a hash of its pixels): same inputs, same pictures
  constructions  builds small scenes of boxes (a seated box, a floating plank, a beam on two posts, a beam 3 cm above its posts, a rail joined into posts, a rail that barely overlaps, an
                 inside-out box, two boxes with the same top plane, a door above a gap, a lamp inside a solid, a plank spanning too far) and runs the construction check on each
  lowangle       the displacement-and-normal-map test of design decision D7: a dense flat plane under a low sun, drawn with the kit's own surface material in three ways (the normal map alone,
                 the displacement alone, both with the normal strength at 0.6) and the relief contrast (the spread of the light and dark) of each; needs no scene (open any file)
Options: --camera NAME, --size W H, --samples N
"""
import json
import os
import sys

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
for folder in (os.path.join(KIT, 'place-kit'), os.path.join(KIT, 'calculators')):
    if folder not in sys.path:
        sys.path.insert(0, folder)

arguments = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
if len(arguments) < 2:
    print('usage: blender -b SCENE.blend --python probe_place.py -- NAME OUT.json [--camera NAME] [--size W H] [--samples N]')
    sys.exit(2)
probe_name, out_path = arguments[0], arguments[1]
options = {'camera': None, 'size': (96, 64), 'samples': 8}
if '--camera' in arguments:
    options['camera'] = arguments[arguments.index('--camera') + 1]
if '--size' in arguments:
    index = arguments.index('--size')
    options['size'] = (int(arguments[index + 1]), int(arguments[index + 2]))
if '--samples' in arguments:
    options['samples'] = int(arguments[arguments.index('--samples') + 1])

from place_kit import names, scene_read  # noqa: E402
from place_kit.checks import material_inspect, normals_test  # noqa: E402
from place_kit.surfaces import normals as normal_tools  # noqa: E402


def upstream_has(socket, node_type):
    seen, stack = set(), [socket]
    while stack:
        current = stack.pop()
        for link in current.links:
            node = link.from_node
            if node.type == node_type:
                return True
            if node.name in seen:
                continue
            seen.add(node.name)
            stack.extend(node.inputs)
    return False


def principled(material):
    return next((n for n in material.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'), None) if material.node_tree else None


def raw_material_facts(material):
    """Straight from the nodes: is a Normal Map node fed by a picture and wired to the shader's Normal; is the picture Non-Color; is there a Displacement node on the output."""
    tree = material.node_tree
    shader = principled(material)
    facts = {'name': material.name, 'normal_map_wired': False, 'normal_picture_colourspace': None, 'displacement_node': False, 'displacement_method': getattr(material, 'displacement_method', None),
             'roughness_varies': False, 'colour_varies': False, 'wear_groups': []}
    if tree is None or shader is None:
        return facts
    for node in tree.nodes:
        if node.type == 'NORMAL_MAP' and shader.inputs['Normal'].links:
            wired = False
            stack, seen = [shader.inputs['Normal']], set()
            while stack:
                for link in stack.pop().links:
                    if link.from_node == node:
                        wired = True
                    elif link.from_node.name not in seen:
                        seen.add(link.from_node.name)
                        stack.extend(link.from_node.inputs)
            images = []
            stack, seen = [node.inputs['Color']], set()
            while stack:
                for link in stack.pop().links:
                    if link.from_node.type == 'TEX_IMAGE' and link.from_node.image is not None:
                        images.append(link.from_node.image)
                    elif link.from_node.name not in seen:
                        seen.add(link.from_node.name)
                        stack.extend(link.from_node.inputs)
            if wired and images:
                facts['normal_map_wired'] = True
                facts['normal_picture_colourspace'] = images[0].colorspace_settings.name
    for output in [n for n in tree.nodes if n.type == 'OUTPUT_MATERIAL']:
        for link in output.inputs['Displacement'].links:
            if link.from_node.type == 'DISPLACEMENT':
                facts['displacement_node'] = True
    facts['roughness_varies'] = upstream_has(shader.inputs['Roughness'], 'TEX_NOISE') or upstream_has(shader.inputs['Roughness'], 'TEX_IMAGE')
    facts['colour_varies'] = upstream_has(shader.inputs['Base Color'], 'TEX_NOISE') or upstream_has(shader.inputs['Base Color'], 'VALTORGB') or upstream_has(shader.inputs['Base Color'], 'HUE_SAT')
    facts['wear_groups'] = sorted({n.node_tree.name for n in tree.nodes if n.type == 'GROUP' and n.node_tree is not None and n.node_tree.name.startswith('PK ') and n.node_tree.name != 'PK Plan'})
    return facts


def probe_facts():
    objects = []
    for obj in scene_read.mesh_objects(only_visible=True):
        amounts = {key[3:-7]: round(float(obj[key]), 4) for key in obj.keys() if key.startswith('pk_') and key.endswith('_amount')}
        objects.append({'name': obj.name, 'role': obj.get(names.ROLE), 'scatter': scene_read.is_scatter(obj), 'faces': len(obj.data.polygons),
                        'modifiers': [[m.type, m.name] for m in obj.modifiers], 'amounts': amounts, 'materials': [raw_material_facts(s.material) for s in obj.material_slots if s.material],
                        'inspected': [material_inspect.inspect_material(s.material) for s in obj.material_slots if s.material and s.material.node_tree]})
    images = []
    for name, image in normals_test.unique_normal_images().items():
        images.append({'name': name, 'colourspace': image.colorspace_settings.name, 'size': list(image.size), 'made_by_kit': bool(image.get('pk_made'))})
    return {'objects': objects, 'normal_images': images, 'fake_users': sorted(m.name for m in bpy.data.materials if m.use_fake_user)[:50], 'scatter_objects': sum(1 for o in bpy.data.objects if o.get('pk_scatter'))}


def probe_directions():
    results = []
    for name, image in normals_test.unique_normal_images().items():
        height_image = normals_test.height_partner(image)
        if height_image is None or tuple(height_image.size) != tuple(image.size):
            results.append({'name': name, 'partner': False})
            continue
        rgb = normal_tools.image_to_array(image)[..., :3]
        height = normal_tools.image_to_array(height_image)[..., 0]
        flipped = rgb.copy()
        flipped[..., 1] = 1.0 - flipped[..., 1]
        results.append({'name': name, 'partner': True, 'true': normal_tools.direction_correlation(rgb, height), 'green_flipped': normal_tools.direction_correlation(flipped, height)})
    return {'images': results}


def draw(path, camera, size, samples):
    scene = bpy.context.scene
    scene.camera = camera
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = samples
    scene.cycles.use_denoising = False
    scene.cycles.seed = 7
    scene.cycles.use_animated_seed = False
    scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = size[0], size[1], 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_depth = '16'
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    image = bpy.data.images.load(path + '.png' if not path.endswith('.png') else path, check_existing=False)
    pixels = np.empty(image.size[0] * image.size[1] * 4, dtype=np.float32)
    image.pixels.foreach_get(pixels)
    bpy.data.images.remove(image)
    return pixels.reshape(-1, 4)[:, :3].copy()


def probe_renders():
    from place_kit import commands
    from place_kit.wear import door
    from mathutils import Vector
    scene = bpy.context.scene
    camera = bpy.data.objects.get(options['camera']) if options['camera'] else scene.camera
    if camera is None:                      # a scene with no camera: look at the middle of everything from a corner
        lows, highs = [], []
        for obj in scene_read.mesh_objects(only_visible=True):
            if not scene_read.is_scatter(obj):
                low, high = scene_read.world_bounds(obj)
                lows.append(low)
                highs.append(high)
        middle = (np.min(lows, axis=0) + np.max(highs, axis=0)) / 2
        data = bpy.data.cameras.new('probe camera')
        data.lens = 35
        camera = bpy.data.objects.new('probe camera', data)
        scene.collection.objects.link(camera)
        camera.location = (middle[0] + 7.0, middle[1] - 8.0, middle[2] + 4.5)
        camera.rotation_euler = (Vector((middle[0], middle[1], 1.2)) - Vector(camera.location)).to_track_quat('-Z', 'Y').to_euler()
        scene.camera = camera
    folder = os.path.dirname(os.path.abspath(out_path))
    size, samples = options['size'], options['samples']
    settings_file = os.path.join(os.path.dirname(bpy.data.filepath), 'place-settings.json')
    settings = commands.read_settings(settings_file if os.path.exists(settings_file) else None)
    commands.tag_roles(settings, write=False, fallback=True)
    from place_kit import run_record
    record = run_record.read()               # the look and state the place was finished with
    look, state = record.get('look'), record.get('state')
    wear = door.age_place(settings, look=look, state=state)          # puts the same layers back in (the scene is open from the saved file)
    layers = sorted({k for ls in wear.materials.values() for k in ls})
    as_it_is = draw(os.path.join(folder, 'r_as_it_is.png'), camera, size, samples)
    again = draw(os.path.join(folder, 'r_again.png'), camera, size, samples)
    wear.set_master(0.0)
    master_zero = draw(os.path.join(folder, 'r_master_zero.png'), camera, size, samples)
    wear.set_master(1.0)
    wear.remove()
    removed = draw(os.path.join(folder, 'r_removed.png'), camera, size, samples)
    only = {}
    for layer in layers:
        wear = door.age_place(settings, look=look, state=state, layers=[layer])
        only[layer] = float(np.abs(draw(os.path.join(folder, f'r_only_{layer}.png'), camera, size, samples) - removed).mean())
        wear.remove()
    return {'layers': layers, 'size': list(size), 'samples': samples, 'mean_difference_as_it_is_vs_removed': float(np.abs(as_it_is - removed).mean()),
            'max_difference_master_zero_vs_removed': float(np.abs(master_zero - removed).max()), 'mean_difference_master_zero_vs_removed': float(np.abs(master_zero - removed).mean()),
            'max_difference_as_it_is_vs_again': float(np.abs(as_it_is - again).max()), 'mean_difference_only_one_layer_vs_removed': only,
            'mean_brightness_as_it_is': float(as_it_is.mean()), 'mean_brightness_removed': float(removed.mean())}


def probe_uvs():
    rows = []
    for obj in scene_read.mesh_objects(only_visible=True):
        if scene_read.is_scatter(obj) or not obj.data.uv_layers.active:
            continue
        layer = obj.data.uv_layers.active
        uv = np.empty(len(obj.data.loops) * 2, dtype=np.float32)
        layer.uv.foreach_get('vector', uv)
        uv = uv.reshape(-1, 2)
        low, high = scene_read.world_bounds(obj)
        size = [float(h - l) for l, h in zip(low, high)]
        rows.append({'name': obj.name, 'role': obj.get(names.ROLE), 'uv_extent': [float(np.ptp(uv[:, 0])), float(np.ptp(uv[:, 1]))], 'size_metres': size})
    return {'objects': rows}


def probe_construction():
    from place_kit import commands
    from place_kit.checks import construction
    settings = commands.read_settings(None)
    commands.tag_roles(settings, write=False, fallback=True)
    report = construction.check_construction(settings)
    return {'findings': report if isinstance(report, (list, dict)) else str(report)}


def probe_lowangle():
    import math
    from place_kit import settings_file
    from place_kit.surfaces import materials as surface_materials
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    folder = os.path.dirname(os.path.abspath(out_path))
    size = options['size']
    surface_id, role = (arguments[arguments.index('--surface') + 1] if '--surface' in arguments else 'packed_earth'), 'ground.earth'
    spec = settings_file.surface(surface_id)
    tile = float(settings_file.number(spec['tile_metres']))
    cells = 120
    mesh = bpy.data.meshes.new('lowangle plane')
    side = tile * 0.8
    xs = np.linspace(-side / 2, side / 2, cells + 1)
    vertices = [(x, y, 0.0) for y in xs for x in xs]
    faces = [(r * (cells + 1) + c, r * (cells + 1) + c + 1, (r + 1) * (cells + 1) + c + 1, (r + 1) * (cells + 1) + c) for r in range(cells) for c in range(cells)]
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new('lowangle plane', mesh)
    scene.collection.objects.link(obj)
    mesh.uv_layers.new(name='UVMap')
    uv = mesh.uv_layers.active
    for polygon in mesh.polygons:
        for loop_index in polygon.loop_indices:
            point = mesh.vertices[mesh.loops[loop_index].vertex_index].co
            uv.data[loop_index].uv = (point.x, point.y)         # UVs in metres, like the kit's own
    world = bpy.data.worlds.new('w')
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.02, 0.02, 0.02, 1)
    scene.world = world
    sun = bpy.data.lights.new('low sun', 'SUN')
    sun.energy = 4.0
    sun_object = bpy.data.objects.new('low sun', sun)
    sun_object.rotation_euler = (math.radians(80.0), 0.0, math.radians(30.0))       # 10 degrees above the plane
    scene.collection.objects.link(sun_object)
    camera_data = bpy.data.cameras.new('cam')
    camera_data.type = 'ORTHO'
    camera_data.ortho_scale = side
    camera = bpy.data.objects.new('cam', camera_data)
    camera.location = (0, 0, 3)
    scene.collection.objects.link(camera)
    scene.view_settings.view_transform = 'Standard'
    results = {}
    variants = {'normal_map_alone': (False, None), 'displacement_alone': (True, 0.0), 'both_normal_at_0_6': (True, None), 'both_normal_at_full': (True, 'full')}
    for name, (displace, forced_strength) in variants.items():
        material = surface_materials.build_surface_material(role, surface_id, spec, 512, displace, quick=False)
        material.name = 'lowangle ' + name
        for node in material.node_tree.nodes:
            if node.type == 'NORMAL_MAP' and forced_strength == 'full':
                node.inputs['Strength'].default_value = float(settings_file.number(spec['normal_strength']))
            elif node.type == 'NORMAL_MAP' and forced_strength is not None:
                node.inputs['Strength'].default_value = forced_strength
        strength = next(n for n in material.node_tree.nodes if n.type == 'NORMAL_MAP').inputs['Strength'].default_value
        flat = material.node_tree.nodes['Principled BSDF'] if 'Principled BSDF' in material.node_tree.nodes else principled(material)
        mesh.materials.clear()
        mesh.materials.append(material)
        pixels = draw(os.path.join(folder, f'low_{name}.png'), camera, size, options['samples'])
        luminance = 0.2126 * pixels[:, 0] + 0.7152 * pixels[:, 1] + 0.0722 * pixels[:, 2]
        results[name] = {'relief_contrast': float(luminance.std() / max(luminance.mean(), 1e-6)), 'mean': float(luminance.mean()), 'normal_strength': float(strength), 'displacement_method': material.displacement_method}
    both, normal, displaced = (results[k]['relief_contrast'] for k in ('both_normal_at_0_6', 'normal_map_alone', 'displacement_alone'))
    results['ratio_both_to_larger_single'] = both / max(normal, displaced)
    results['ratio_both_full_normal_to_normal_alone'] = results['both_normal_at_full']['relief_contrast'] / max(normal, 1e-9)
    results['ratio_both_to_sum_of_singles'] = both / (normal + displaced)
    results['surface'] = surface_id
    return results


def segment_distance(point, line):
    """(distance, signed distance, along) of a point from a polyline, by plain geometry (the left of the direction of travel is positive)."""
    best = (1e9, 0.0, 0.0)
    travelled = 0.0
    for a, b in zip(line[:-1], line[1:]):
        a, b = np.asarray(a, float), np.asarray(b, float)
        direction = b - a
        length = float(np.hypot(*direction))
        if length < 1e-9:
            continue
        unit = direction / length
        t = float(np.clip(np.dot(point - a, unit), 0.0, length))
        nearest = a + unit * t
        distance = float(np.hypot(*(point - nearest)))
        side = float(unit[0] * (point[1] - nearest[1]) - unit[1] * (point[0] - nearest[0]))
        if distance < best[0]:
            best = (distance, distance if side >= 0 else -distance, travelled + t)
        travelled += length
    return best


def probe_roads():
    from place_kit import commands, parts
    from place_kit.growth import keepout
    folder = os.path.dirname(bpy.data.filepath)
    settings_path = os.path.join(folder, 'place-settings.json')
    settings = commands.read_settings(settings_path)
    parts.refresh_ground()
    out = {'roads': [], 'plants': {}}
    scatter = {}
    for obj in keepout.scatter_objects():
        scatter.setdefault(obj.get('pk_scatter_group') or 'plant', []).append(keepout.roots_of(obj))
    for road in settings.roads:
        line = np.asarray(road['polyline'], float)
        gauge, width = float(road.get('gauge', 1.3)), float(road.get('width', 3.0))
        rut_width = float(road.get('rut_width', 0.18))
        length = float(np.hypot(*np.diff(line, axis=0).T).sum())
        depths, gauges, shoulders = [], [], []
        for fraction in np.linspace(0.1, 0.9, 12):
            target = fraction * length
            travelled, point, direction = 0.0, line[0], np.array([1.0, 0.0])
            for a, b in zip(line[:-1], line[1:]):
                step = float(np.hypot(*(b - a)))
                if travelled + step >= target:
                    direction = (b - a) / step
                    point = a + direction * (target - travelled)
                    break
                travelled += step
            normal = np.array([-direction[1], direction[0]])
            offsets = np.arange(-2.6, 2.6001, 0.02)
            ground = np.array([parts.ground_height_at(*(point + normal * o)) for o in offsets])
            reference = float(np.median(ground[np.abs(offsets) > 2.2]))
            for side in (-1, 1):
                window = (offsets * side > gauge / 2 - 0.35) & (offsets * side < gauge / 2 + 0.35)
                depths.append(reference - float(ground[window].min()))
            left = offsets < -0.1
            right = offsets > 0.1
            gauges.append(float(offsets[right][np.argmin(ground[right])] - offsets[left][np.argmin(ground[left])]))
            shoulders.append(float(ground[np.abs(offsets) < 0.1].mean() - reference))
        entry = {'name': road.get('name'), 'depth_median_m': float(np.median(depths)), 'depth_min_m': float(min(depths)), 'depth_max_m': float(max(depths)), 'gauge_median_m': float(np.median(gauges)),
                 'gauge_in_settings_m': gauge, 'centre_above_reference_m': float(np.median(shoulders)), 'rut_depth_in_settings_m': float(road.get('rut_depth', 0.08))}
        counts = {'in_rut_core': 0, 'in_rut_band': 0, 'in_centre_strip': 0, 'within_lane': 0, 'near_lane_outside': 0, 'elsewhere': 0, 'total': 0}
        nearest_to_rut = 9.0
        for group, blocks in scatter.items():
            for roots in blocks:
                for root in roots:
                    distance, signed, along = segment_distance(root[:2].astype(float), line)
                    counts['total'] += 1
                    offset = abs(abs(signed) - gauge / 2)
                    if distance <= width / 2 + 0.5:
                        nearest_to_rut = min(nearest_to_rut, offset)
                    if distance <= width / 2 + 0.5 and offset < rut_width / 2 - 0.05:
                        counts['in_rut_core'] += 1
                    if distance <= width / 2 + 0.5 and offset < rut_width / 2 + 0.02:
                        counts['in_rut_band'] += 1
                    if abs(signed) <= 0.4 and 0 < along < length:
                        counts['in_centre_strip'] += 1
                    if distance <= width / 2:
                        counts['within_lane'] += 1
                    elif distance <= width / 2 + 2.0:
                        counts['near_lane_outside'] += 1
                    else:
                        counts['elsewhere'] += 1
        entry['roots'] = counts
        entry['nearest_root_to_a_rut_line_m'] = nearest_to_rut
        out['roads'].append(entry)
    out['groups'] = {group: int(sum(len(r) for r in blocks)) for group, blocks in scatter.items()}
    return out


def probe_damage():
    from place_kit import commands
    from place_kit.checks import fingerprint
    import hashlib
    settings = commands.read_settings(None)
    commands.tag_roles(settings, write=False, fallback=True)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    by_role = {}
    for obj in scene_read.mesh_objects(only_visible=True):
        role = obj.get(names.ROLE) or ''
        if scene_read.is_scatter(obj) or role.startswith('ground.') or role.startswith('never.'):
            continue
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        coordinates = np.empty(len(mesh.vertices) * 3, dtype=np.float64)
        mesh.vertices.foreach_get('co', coordinates)
        world = np.array(evaluated.matrix_world)
        points = coordinates.reshape(-1, 3) @ world[:3, :3].T + world[:3, 3]
        lowest = float(points[:, 2].min()) if len(points) else 0.0
        # the shape on its own (relative to the object's own box) so two copies standing in different places still compare
        shape = hashlib.md5(np.round(coordinates, 3).tobytes()).hexdigest()
        evaluated.to_mesh_clear()
        damage = next((m for m in obj.modifiers if m.name == names.DAMAGE_MODIFIER), None)
        by_role.setdefault(role, []).append({'name': obj.name, 'shape': shape, 'lowest_z': lowest, 'zmin_recorded': float(obj.get(names.BOTTOM_Z, 0.0)), 'damage_strength_m': float(damage.strength) if damage else None,
                                             'faces': len(mesh.polygons) if False else len(obj.data.polygons)})
    result = {}
    for role, items in by_role.items():
        result[role] = {'count': len(items), 'distinct_shapes': len({i['shape'] for i in items}), 'max_lowest_z_error_m': max(abs(i['lowest_z'] - i['zmin_recorded']) for i in items),
                        'with_damage': sum(1 for i in items if i['damage_strength_m']), 'strengths_m': sorted({round(i['damage_strength_m'], 4) for i in items if i['damage_strength_m']})[:4]}
    return {'roles': result}


def probe_images():
    import hashlib
    result = {}
    for image in bpy.data.images:
        if image.name.startswith('pk_'):
            pixels = np.empty(image.size[0] * image.size[1] * image.channels, dtype=np.float32)
            image.pixels.foreach_get(pixels)
            result[image.name] = {'size': list(image.size), 'colourspace': image.colorspace_settings.name, 'hash': hashlib.md5(np.round(pixels, 3).tobytes()).hexdigest()}
    return {'images': result}


def probe_constructions():
    import bmesh
    from place_kit import commands
    from place_kit.checks import construction

    def reset():
        for obj in list(bpy.data.objects):
            bpy.data.objects.remove(obj)
        for mesh in list(bpy.data.meshes):
            bpy.data.meshes.remove(mesh)
        for light in list(bpy.data.lights):
            bpy.data.lights.remove(light)
        mesh = bpy.data.meshes.new('Ground')
        mesh.from_pydata([(-8, -8, 0), (8, -8, 0), (8, 8, 0), (-8, 8, 0)], [], [(0, 1, 2, 3)])
        obj = bpy.data.objects.new('Ground', mesh)
        bpy.context.scene.collection.objects.link(obj)

    def box(name, size, location):
        mesh = bpy.data.meshes.new(name)
        builder = bmesh.new()
        bmesh.ops.create_cube(builder, size=1.0)
        for vertex in builder.verts:
            vertex.co.x *= size[0]
            vertex.co.y *= size[1]
            vertex.co.z *= size[2]
        builder.to_mesh(mesh)
        builder.free()
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.scene.collection.objects.link(obj)
        obj.location = location
        return obj

    def run(roles_by_name):
        bpy.context.view_layer.update()
        settings = commands.read_settings(None)
        settings.data['roles'] = [{'role': role, 'match': {'names': ['^' + name + '$']}} for name, role in roles_by_name.items()]
        settings.data['roles'].append({'role': 'ground.earth', 'match': {'names': ['^Ground$']}})
        return construction.check_construction(settings)['objects']

    cases = {}
    reset()
    box('wall A', (2.0, 0.3, 2.0), (0, 0, 1.0))
    cases['a seated box'] = run({'wall A': 'wall.plaster'})
    reset()
    box('plank float', (1.0, 0.2, 0.04), (0, 0, 0.08))
    cases['a plank 6 cm above the ground'] = run({'plank float': 'timber.plank'})
    reset()
    box('plank low', (1.0, 0.2, 0.04), (0, 0, 0.023))
    cases['a plank 3 mm above the ground'] = run({'plank low': 'timber.plank'})
    reset()
    box('post 1', (0.12, 0.12, 1.0), (-1.0, 0, 0.5))
    box('post 2', (0.12, 0.12, 1.0), (1.0, 0, 0.5))
    box('beam 1', (2.4, 0.1, 0.1), (0, 0, 1.05))
    cases['a beam resting on two posts'] = run({'post 1': 'timber.post', 'post 2': 'timber.post', 'beam 1': 'timber.beam'})
    reset()
    box('post 1', (0.12, 0.12, 1.0), (-1.0, 0, 0.5))
    box('post 2', (0.12, 0.12, 1.0), (1.0, 0, 0.5))
    box('beam 1', (2.4, 0.1, 0.1), (0, 0, 1.08))
    cases['a beam 3 cm above two posts'] = run({'post 1': 'timber.post', 'post 2': 'timber.post', 'beam 1': 'timber.beam'})
    reset()
    box('post 1', (0.12, 0.12, 1.0), (-1.0, 0, 0.5))
    box('post 2', (0.12, 0.12, 1.0), (1.0, 0, 0.5))
    box('rail 1', (2.12, 0.05, 0.1), (0, 0, 0.5))
    cases['a fence rail joined 6 cm into two posts'] = run({'post 1': 'timber.post', 'post 2': 'timber.post', 'rail 1': 'timber.fence'})
    reset()
    box('post 1', (0.12, 0.12, 1.0), (-1.0, 0, 0.5))
    box('post 2', (0.12, 0.12, 1.0), (1.0, 0, 0.5))
    box('beam 1', (2.12, 0.05, 0.1), (0, 0, 0.5))
    cases['a beam (which may not hang) joined into two posts'] = run({'post 1': 'timber.post', 'post 2': 'timber.post', 'beam 1': 'timber.beam'})
    reset()
    box('post 1', (0.12, 0.12, 1.0), (-1.0, 0, 0.5))
    box('rail 1', (0.76, 0.05, 0.1), (-0.58, 0, 0.5))                  # only 2 cm of the rail is inside the post (its end at x = -0.96, the post's face at -0.94)
    cases['a rail with only 2 cm inside its post'] = run({'post 1': 'timber.post', 'rail 1': 'timber.fence'})
    reset()
    inside_out = box('box out', (1.0, 1.0, 1.0), (0, 0, 0.5))
    builder = bmesh.new()
    builder.from_mesh(inside_out.data)
    bmesh.ops.reverse_faces(builder, faces=builder.faces)
    builder.to_mesh(inside_out.data)
    builder.free()
    cases['a closed box turned inside out'] = run({'box out': 'wall.plaster'})
    reset()
    box('plank A', (1.0, 0.2, 0.04), (0, 0, 0.02))
    box('plank B', (1.0, 0.2, 0.04), (0.5, 0, 0.02))
    cases['two planks with the same top plane'] = run({'plank A': 'timber.plank', 'plank B': 'timber.plank'})
    reset()
    box('door 1', (0.9, 0.06, 1.9), (0, 0, 1.55))
    cases['a door whose sill is 60 cm above the ground'] = run({'door 1': 'timber.door'})
    reset()
    box('block 1', (0.3, 0.3, 0.3), (-1.4, 0, 0.15))
    box('block 2', (0.3, 0.3, 0.3), (1.4, 0, 0.15))
    box('plank long', (3.2, 0.2, 0.04), (0, 0, 0.32))
    cases['a plank spanning 2.5 m between two blocks'] = run({'block 1': 'stone.footing', 'block 2': 'stone.footing', 'plank long': 'timber.plank'})
    reset()
    box('wall A', (2.0, 2.0, 2.0), (0, 0, 1.0))
    lamp = bpy.data.lights.new('Lamp', 'POINT')
    lamp_object = bpy.data.objects.new('Lamp', lamp)
    bpy.context.scene.collection.objects.link(lamp_object)
    lamp_object.location = (0, 0, 1.0)
    cases['a lamp inside a solid'] = run({'wall A': 'wall.plaster'})
    return {'cases': cases}


PROBES = {'roads': probe_roads, 'damage': probe_damage, 'images': probe_images, 'constructions': probe_constructions, 'lowangle': probe_lowangle, 'facts': probe_facts, 'directions': probe_directions, 'renders': probe_renders, 'uvs': probe_uvs, 'construction': probe_construction}
if probe_name not in PROBES:
    print('unknown probe', probe_name, 'choose one of', ', '.join(PROBES))
    sys.exit(2)
result = PROBES[probe_name]()
os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
with open(out_path, 'w', encoding='utf-8') as handle:
    json.dump(result, handle, indent=1, default=str)
print('PROBE DONE', probe_name, out_path)
