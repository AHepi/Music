"""
What this file does:
Gives any Blender scene the look of the street bundle "Rain on the Old Curve", without touching the
scene's shapes or materials. The look is the half of that bundle that does not depend on the street:

  - a blue-hour sky painted from noise (no sky picture, no repeating environment map),
  - a real amber light at every warm glowing patch in the scene (windows, lamps), found automatically,
  - broad blue sky light from above and from behind the scene, a soft one in front, and one warm
    off-frame reflection beside the camera,
  - a cool, thin haze filling the scene,
  - Cycles with the AgX view, "Medium High Contrast", exposure 0.5,
  - a restrained painterly finish: fog glow, then an anisotropic Kuwahara filter mixed in at 28 percent,
  - optionally fine slanted rain, and optionally the camera set like a standing person (32 mm, eye 1.65 m).

Everything it adds is named "LOOK • ..." so it can be found and removed. The scene's own lights are
muted (not deleted) unless keep_scene_lights=True.

Use inside Blender's Python or the bpy module:
    import look_stage
    look_stage.apply_look(bpy.context.scene)                  # defaults
    look_stage.apply_look(bpy.context.scene, rain=True, camera_like_a_person=True, samples=64)

The numbers come from the street bundle's build_scene.py and were not re-tuned here; where a number
had to be made scene-independent (light sizes and powers), it is scaled from the scene's size so the
light per square metre stays the same as in the street.
"""

import math
import random

import bpy
import bmesh
from mathutils import Vector

LOOK_PREFIX = 'LOOK • '

# colours and strengths lifted from the street bundle
SKY_DARK = (0.008, 0.025, 0.05, 1)
SKY_LIGHT = (0.055, 0.19, 0.29, 1)
SKY_STRENGTH = 0.27
AMBER_LIGHT = (1.0, 0.49, 0.16)
AMBER_WASH = (1.0, 0.54, 0.22)
BLUE_SKY = (0.20, 0.48, 1.0)
BLUE_VEIL = (0.20, 0.56, 1.0)
BLUE_FRONT = (0.22, 0.52, 0.8)
HAZE_COLOUR = (0.28, 0.41, 0.51, 1)
HAZE_DENSITY = 0.004

# watts per square metre of light surface, so a bigger scene gets a bigger light of the same brightness
BLUE_SKY_WATTS_PER_M2 = 1050 / (math.pi * 9 ** 2)
BLUE_VEIL_WATTS_PER_M2 = 1200 / (math.pi * 6.5 ** 2)
BLUE_FRONT_WATTS_PER_M2 = 500 / (math.pi * 5 ** 2)


def _looks_like_sky_or_ground_backdrop(obj, limit=400.0):
    """Hills and sky domes hundreds of metres wide are not part of the place; leave them out of the bounds."""
    return max(obj.dimensions) > limit


def scene_bounds(scene):
    """Lowest and highest corner of everything that counts as the place (metres, world space)."""
    low = Vector((1e9, 1e9, 1e9))
    high = Vector((-1e9, -1e9, -1e9))
    for obj in scene.objects:
        if obj.type != 'MESH' or obj.hide_render or _looks_like_sky_or_ground_backdrop(obj):
            continue
        for corner in obj.bound_box:
            world = obj.matrix_world @ Vector(corner)
            low = Vector((min(low.x, world.x), min(low.y, world.y), min(low.z, world.z)))
            high = Vector((max(high.x, world.x), max(high.y, world.y), max(high.z, world.z)))
    return low, high


def _is_warm(colour):
    red, green, blue = colour[0], colour[1], colour[2]
    return red > blue * 1.6 and red > 0.5


def warm_glowing_patches(scene, minimum_area=0.02):
    """
    Every separate patch of warm glowing surface: (centre, outward normal, area, emission strength, material name).
    A patch is a run of connected faces that share one glowing material, for example one window pane or one lamp head.
    """
    patches = []
    for obj in scene.objects:
        if obj.type != 'MESH' or obj.hide_render:
            continue
        glowing_slots = {}
        for index, material in enumerate(obj.data.materials):
            if material is None or not material.use_nodes:
                continue
            for node in material.node_tree.nodes:
                strength, colour = 0.0, None
                if node.type == 'BSDF_PRINCIPLED':
                    strength = node.inputs['Emission Strength'].default_value
                    colour = node.inputs['Emission Color'].default_value
                elif node.type == 'EMISSION':
                    strength = node.inputs['Strength'].default_value
                    colour = node.inputs['Color'].default_value
                if strength > 0 and colour is not None and _is_warm(colour):
                    glowing_slots[index] = (strength, material.name)
        if not glowing_slots:
            continue
        mesh = bmesh.new()
        mesh.from_mesh(obj.data)
        mesh.faces.ensure_lookup_table()
        seen = set()
        matrix = obj.matrix_world
        normal_matrix = matrix.to_3x3().inverted_safe().transposed()
        for face in mesh.faces:
            if face.index in seen or face.material_index not in glowing_slots:
                continue
            # grow the patch over connected faces of the same material
            stack = [face]
            seen.add(face.index)
            area = 0.0
            centre = Vector((0, 0, 0))
            normal = Vector((0, 0, 0))
            while stack:
                current = stack.pop()
                face_area = current.calc_area()
                area += face_area
                centre += current.calc_center_median() * face_area
                normal += current.normal * face_area
                for edge in current.edges:
                    for neighbour in edge.link_faces:
                        if neighbour.index not in seen and neighbour.material_index == current.material_index:
                            seen.add(neighbour.index)
                            stack.append(neighbour)
            if area < minimum_area or area <= 0:
                continue
            strength, material_name = glowing_slots[face.material_index]
            world_centre = matrix @ (centre / area)
            world_normal = (normal_matrix @ normal).normalized() if normal.length > 0 else Vector((0, 0, 1))
            scale = matrix.to_scale()
            world_area = area * abs(scale.x * scale.y)  # good enough for roughly uniform scales
            patches.append((world_centre, world_normal, world_area, strength, material_name))
        mesh.free()
    return patches


def _link(obj, collection):
    for existing in list(obj.users_collection):
        existing.objects.unlink(obj)
    collection.objects.link(obj)


def _light(name, kind, location, colour, power, collection, size=0.25, aim_at=None):
    data = bpy.data.lights.new(LOOK_PREFIX + name, kind)
    data.energy = power
    data.color = colour
    if kind == 'POINT':
        data.shadow_soft_size = size
    elif kind == 'AREA':
        data.shape = 'DISK'
        data.size = size
    obj = bpy.data.objects.new(LOOK_PREFIX + name, data)
    collection.objects.link(obj)
    obj.location = location
    if aim_at is not None:
        obj.rotation_euler = (Vector(aim_at) - Vector(location)).to_track_quat('-Z', 'Y').to_euler()
    return obj


def remove_look(scene):
    """Take out everything a previous apply_look added and un-mute the scene's own lights."""
    for obj in list(scene.objects):
        if obj.name.startswith(LOOK_PREFIX):
            bpy.data.objects.remove(obj, do_unlink=True)
        elif obj.type == 'LIGHT' and obj.get('look_muted'):
            obj.hide_render = False
            del obj['look_muted']
    for collection in list(bpy.data.collections):
        if collection.name.startswith(LOOK_PREFIX) and not collection.objects:
            bpy.data.collections.remove(collection)


def apply_look(scene, *, keep_scene_lights=False, replace_world=True, haze=True, rain=False,
               camera_like_a_person=False, samples=64, resolution=(1080, 1920), glow_lights=True,
               max_glow_lights=40, painterly_mix=0.28, exposure=0.5, seed=714035, window_light_scale=1.0):
    """Apply the look. Returns a short report dictionary of what was added."""
    report = {}
    remove_look(scene)
    collection = bpy.data.collections.new(LOOK_PREFIX + 'lights, sky and haze')
    scene.collection.children.link(collection)
    low, high = scene_bounds(scene)
    centre = (low + high) / 2
    size = high - low
    footprint = max(size.x, size.y, 10.0)
    report['bounds'] = (tuple(round(v, 1) for v in low), tuple(round(v, 1) for v in high))

    # 1. the scene's own lights: muted, remembered
    if not keep_scene_lights:
        muted = 0
        for obj in scene.objects:
            if obj.type == 'LIGHT' and not obj.hide_render:
                obj.hide_render = True
                obj['look_muted'] = True
                muted += 1
        report['scene_lights_muted'] = muted

    # 2. a real light at every warm glowing patch
    if glow_lights:
        patches = warm_glowing_patches(scene)
        # every lamp gets a light; windows nearest the camera first, up to the cap
        camera_spot = scene.camera.matrix_world.translation if scene.camera else centre
        lamp_words = ('lamp', 'lantern', 'bulb', 'flame', 'mantle')
        lamps = [p for p in patches if any(word in p[4].lower() for word in lamp_words)]
        windows = [p for p in patches if p not in lamps]
        windows.sort(key=lambda p: (p[0] - camera_spot).length)
        chosen = lamps + windows[:max(0, max_glow_lights - len(lamps))]
        added = 0
        for patch_centre, normal, area, strength, material_name in chosen:
            is_lamp = any(word in material_name.lower() for word in ('lamp', 'lantern', 'bulb', 'flame', 'mantle'))
            if is_lamp:
                # like the street's gas mantle plus its pavement wash
                _light('glow lamp ' + material_name, 'POINT', patch_centre + normal * 0.05, AMBER_LIGHT, 460, collection, size=0.19)
                _light('glow lamp wash ' + material_name, 'AREA', patch_centre + Vector((0, 0, -0.15)), AMBER_WASH, 350, collection,
                       size=1.2, aim_at=patch_centre + normal * 2 + Vector((0, 0, -3)))
                added += 2
            else:
                # a window: light spills out through the glass, a little in front of it
                power = window_light_scale * max(40.0, min(400.0, 110.0 * area * strength / 3.0))
                _light('glow window ' + material_name, 'POINT', patch_centre + normal * 0.35, AMBER_LIGHT, power, collection, size=0.3)
                added += 1
        report['glow_patches_found'] = len(patches)
        report['glow_lights_added'] = added

    # 3. the sky rig, scaled from the place's size
    top = high.z
    sky_size = 0.22 * footprint
    _light('broad blue sky bounce', 'AREA', (centre.x - 0.05 * footprint, centre.y + 0.15 * footprint, top + 0.8 * footprint * 0.35),
           BLUE_SKY, BLUE_SKY_WATTS_PER_M2 * math.pi * (sky_size / 2) ** 2, collection, size=sky_size, aim_at=(centre.x, centre.y, low.z))
    veil_size = 0.16 * footprint
    _light('far blue veil', 'AREA', (centre.x + 0.1 * footprint, centre.y + 0.45 * footprint, top + 0.5 * footprint * 0.35),
           BLUE_VEIL, BLUE_VEIL_WATTS_PER_M2 * math.pi * (veil_size / 2) ** 2, collection, size=veil_size, aim_at=(centre.x, centre.y, low.z + 2))
    camera = scene.camera
    if camera is not None:
        cam = camera.matrix_world.translation
        forward = (camera.matrix_world.to_quaternion() @ Vector((0, 0, -1))).normalized()
        left = (camera.matrix_world.to_quaternion() @ Vector((-1, 0, 0))).normalized()
        front_size = 0.12 * footprint
        _light('soft foreground sky reflection', 'AREA', cam + forward * 3 + Vector((0, 0, 0.12 * footprint)),
               BLUE_FRONT, BLUE_FRONT_WATTS_PER_M2 * math.pi * (front_size / 2) ** 2, collection, size=front_size,
               aim_at=cam + forward * 6 + Vector((0, 0, -2)))
        _light('off-frame amber reflection', 'AREA', cam + left * 3 + forward * 2 + Vector((0, 0, 1.5)), (1, 0.44, 0.13), 430, collection,
               size=1.8, aim_at=cam + forward * 8)

    # 4. the painted blue-hour sky
    if replace_world:
        world = bpy.data.worlds.new(LOOK_PREFIX + 'cobalt clouded evening')
        world.use_nodes = True
        nodes = world.node_tree.nodes
        links = world.node_tree.links
        nodes.clear()
        output = nodes.new('ShaderNodeOutputWorld')
        background = nodes.new('ShaderNodeBackground')
        background.inputs['Strength'].default_value = SKY_STRENGTH
        coordinates = nodes.new('ShaderNodeTexCoord')
        noise = nodes.new('ShaderNodeTexNoise')
        noise.inputs['Scale'].default_value = 3.1
        noise.inputs['Detail'].default_value = 4.5
        noise.inputs['Roughness'].default_value = 0.72
        links.new(coordinates.outputs['Normal'], noise.inputs['Vector'])
        ramp = nodes.new('ShaderNodeValToRGB')
        ramp.color_ramp.elements[0].position = 0.26
        ramp.color_ramp.elements[0].color = SKY_DARK
        ramp.color_ramp.elements[1].position = 0.75
        ramp.color_ramp.elements[1].color = SKY_LIGHT
        links.new(noise.outputs['Fac'], ramp.inputs[0])
        links.new(ramp.outputs[0], background.inputs['Color'])
        links.new(background.outputs[0], output.inputs['Surface'])
        scene['look_previous_world'] = scene.world.name if scene.world else ''
        scene.world = world

    # 5. the haze
    if haze:
        fog = bpy.data.materials.new(LOOK_PREFIX + 'fine cool haze')
        fog.use_nodes = True
        tree = fog.node_tree
        tree.nodes.clear()
        volume = tree.nodes.new('ShaderNodeVolumePrincipled')
        volume.inputs['Density'].default_value = HAZE_DENSITY
        volume.inputs['Color'].default_value = HAZE_COLOUR
        volume.inputs['Anisotropy'].default_value = 0.12
        out = tree.nodes.new('ShaderNodeOutputMaterial')
        tree.links.new(volume.outputs['Volume'], out.inputs['Volume'])
        bpy.ops.mesh.primitive_cube_add(size=1, location=(centre.x, centre.y, low.z + 0.35 * footprint))
        box = bpy.context.object
        box.name = LOOK_PREFIX + 'haze volume'
        box.scale = (size.x * 1.4 + 20, size.y * 1.4 + 20, 0.7 * footprint)
        box.data.materials.append(fog)
        box.display_type = 'WIRE'
        _link(box, collection)

    # 6. rain, optional
    if rain:
        rain_material = bpy.data.materials.new(LOOK_PREFIX + 'rain glint')
        rain_material.use_nodes = True
        principled = rain_material.node_tree.nodes.get('Principled BSDF')
        principled.inputs['Base Color'].default_value = (0.18, 0.35, 0.45, 1)
        principled.inputs['Roughness'].default_value = 0.12
        principled.inputs['Transmission Weight'].default_value = 0.7
        rng = random.Random(seed)
        verts, faces = [], []
        count = int(200 + 10 * footprint)
        for _ in range(count):
            x = rng.uniform(low.x, high.x)
            y = rng.uniform(low.y, high.y)
            z = rng.uniform(low.z + 0.4, low.z + 0.3 * footprint)
            h = rng.uniform(0.09, 0.24)
            w = rng.uniform(0.0005, 0.0018)
            dx = rng.uniform(0.008, 0.027)
            i = len(verts)
            verts.extend([(x - w, y, z), (x + w, y, z), (x + w - dx, y, z + h), (x - w - dx, y, z + h)])
            faces.append((i, i + 1, i + 2, i + 3))
        mesh = bpy.data.meshes.new(LOOK_PREFIX + 'rain streaks')
        mesh.from_pydata(verts, [], faces)
        mesh.update()
        mesh.materials.append(rain_material)
        streaks = bpy.data.objects.new(LOOK_PREFIX + 'rain streaks', mesh)
        collection.objects.link(streaks)
        report['rain_streaks'] = count

    # 7. the camera like a standing person, optional
    if camera_like_a_person and scene.camera is not None:
        cam = scene.camera
        cam.data.lens = 32
        cam.data.sensor_width = 36
        ground_under_camera = low.z
        cam.location.z = ground_under_camera + 1.65
        report['camera'] = 'lens 32 mm, eye 1.65 m above the place floor; aim left as it was'

    # 8. render settings
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 7
    scene.cycles.diffuse_bounces = 3
    scene.cycles.glossy_bounces = 4
    scene.cycles.transmission_bounces = 4
    scene.cycles.volume_bounces = 1
    scene.cycles.adaptive_threshold = 0.045
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.film_transparent = False
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Medium High Contrast'
    scene.view_settings.exposure = exposure

    # 9. the restrained painterly finish
    scene.use_nodes = True
    tree = bpy.data.node_groups.new(LOOK_PREFIX + 'painterly evening compositor', 'CompositorNodeTree')
    scene.compositing_node_group = tree
    nodes, links = tree.nodes, tree.links
    render_layers = nodes.new('CompositorNodeRLayers')
    glare = nodes.new('CompositorNodeGlare')
    glare.inputs['Type'].default_value = 'Fog Glow'
    glare.inputs['Quality'].default_value = 'High'
    glare.inputs['Threshold'].default_value = 1.5
    glare.inputs['Size'].default_value = 0.25
    glare.inputs['Strength'].default_value = 0.15
    links.new(render_layers.outputs['Image'], glare.inputs['Image'])
    kuwahara = nodes.new('CompositorNodeKuwahara')
    kuwahara.inputs['Type'].default_value = 'Anisotropic'
    kuwahara.inputs['Size'].default_value = 3
    links.new(glare.outputs['Image'], kuwahara.inputs['Image'])
    mix = nodes.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    mix.blend_type = 'MIX'
    mix.inputs[0].default_value = painterly_mix
    links.new(glare.outputs['Image'], mix.inputs[6])
    links.new(kuwahara.outputs['Image'], mix.inputs[7])
    output = nodes.new('NodeGroupOutput')
    tree.interface.new_socket(name='Image', in_out='OUTPUT', socket_type='NodeSocketColor')
    links.new(mix.outputs[2], output.inputs['Image'])

    report['added_objects'] = [o.name for o in collection.objects]
    return report
