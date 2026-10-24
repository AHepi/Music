# What this does: the shared steps for dressing the pit village street (street.blend) for a shot,
# used by assemble_lockout.py (log 29) and assemble_notice_corner.py (log 31): finding the ground under
# a spot, standing a prop from the props library there, timber posts, glowing materials, the brazier's
# fire, and drawing a picture with EEVEE. Run inside Blender (import it from an assemble script).
# Units are metres; Blender is z-up, the street runs along +y and rises 4 degrees.

import json
import math
import os
import random

import bpy
from mathutils import Quaternion, Vector

KIT_FOLDER = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))   # the kit's top folder
SET_FOLDER = os.path.join(KIT_FOLDER, 'assets/models/pit-village')
PROPS_FOLDER = os.path.join(SET_FOLDER, 'props')


def ground_height(x, y, start=60.0):
    """The height of whatever surface is under (x, y), found by casting a ray straight down from
    `start` (start below a prop to find the ground under it rather than the prop's top)."""
    depsgraph = bpy.context.evaluated_depsgraph_get()
    hit, location, normal, index, hit_object, matrix = bpy.context.scene.ray_cast(depsgraph, Vector((x, y, start)), Vector((0, 0, -1)))
    return location.z if hit else min(y, 76) * math.tan(math.radians(4))


def place_prop(file_name, x, y, turn_degrees=0.0, name=None, lift=0.0, collection='props', scale=1.0, start=60.0):
    """Imports a prop from the library and stands it on the surface at (x, y), turned about z: on
    the first surface a ray going straight down from `start` meets (so a prop can stand on another)."""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(PROPS_FOLDER, file_name))
    imported = [o for o in bpy.data.objects if o not in before]
    roots = [o for o in imported if o.parent is None]
    holder = bpy.data.objects.new(name or file_name.replace('.glb', ''), None)
    target = bpy.data.collections.get(collection) or bpy.data.collections.new(collection)
    if target.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(target)
    target.objects.link(holder)
    for o in imported:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        target.objects.link(o)
    for root in roots:
        root.parent = holder
    holder.location = (x, y, ground_height(x, y, start) + lift)
    holder.rotation_euler = (0, 0, math.radians(turn_degrees))
    holder.scale = (scale, scale, scale)
    return holder


def wooden_post(x, y, height, collection='signs', start=60.0, material=None, turn_degrees=0.0, name=None):
    """A square timber post standing on the ground at (x, y). With `material` (for example the
    notice board's own timber) it wears that, its picture repeating once a metre."""
    ground = ground_height(x, y, start)
    bpy.ops.mesh.primitive_cube_add(size=1)
    post = bpy.context.active_object
    if name:   # a name the film and the shot checker can find (otherwise Blender calls it "Cube")
        post.name = name
    post.scale = (0.09, 0.09, height)
    post.location = (x, y, ground + height / 2)
    post.rotation_euler = (0, 0, math.radians(turn_degrees))
    if material is None:
        material = bpy.data.materials.get('weathered post') or bpy.data.materials.new('weathered post')
        material.use_nodes = True
        material.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.11, 0.08, 0.06, 1)
        material.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.9
    post.data.materials.append(material)
    for c in list(post.users_collection):
        c.objects.unlink(post)
    bpy.data.collections[collection].objects.link(post)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.cube_project(cube_size=1.0)
    bpy.ops.object.mode_set(mode='OBJECT')
    return post


def glow_material(name, colour, strength):
    """A material that only glows: a black base, so a lamp just above can't light it white."""
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    principled = material.node_tree.nodes['Principled BSDF']
    principled.inputs['Base Color'].default_value = (0.0, 0.0, 0.0, 1)
    principled.inputs['Specular IOR Level'].default_value = 0.0
    principled.inputs['Roughness'].default_value = 1.0
    principled.inputs['Emission Color'].default_value = (*colour, 1)
    principled.inputs['Emission Strength'].default_value = strength
    return material


def make_glow(material, colour, strength):
    """Makes an existing material glow (a lamp's glass or bulb), keeping its own colour and texture."""
    principled = material.node_tree.nodes.get('Principled BSDF') if material.use_nodes else None
    if principled:
        principled.inputs['Emission Color'].default_value = (*colour, 1)
        principled.inputs['Emission Strength'].default_value = strength


def brazier_fire(x, y, light_above_coals=0.6, coal_top=0.80, dark_every=4, glow=1.0, energy=900, shadow_soft=0.25, colour=(1.0, 0.55, 0.25)):
    """A heaped bed of coals in the brazier drum, glowing orange with some dark lumps among them,
    and the warm light it throws. The flames themselves are drawn live in the film (lockout-test.js):
    flame shapes in the plate looked like paper cut-outs once painted. coal_top is the bed's height
    above the ground (the drum is 0.86 m tall); dark_every=4 makes every fourth lump dark, dark_every=1.33
    about three in four (a bed that has burnt down, glowing between the lumps). energy is the light's strength
    in watts and shadow_soft its size in metres (a bigger light casts softer shadow edges)."""
    top = ground_height(x, y) + coal_top
    glowing = glow_material('brazier coals', (1.0, 0.16, 0.015), glow)
    dark = bpy.data.materials.new('brazier dark coal')
    dark.use_nodes = True
    dark.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.02, 0.018, 0.016, 1)
    dark.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.5 if dark_every >= 4 else 0.9
    rng = random.Random(7)
    for i in range(22):
        angle, reach = rng.uniform(0, 2 * math.pi), 0.2 * math.sqrt(rng.random())
        size = rng.uniform(0.035, 0.06)
        heap = 0.06 * (1 - reach / 0.2)   # heaped a little in the middle
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=size,
                                              location=(x + reach * math.cos(angle), y + reach * math.sin(angle), top - 0.01 + heap + rng.uniform(0, 0.02)))
        lump = bpy.context.active_object
        lump.name = f'brazier_coal_{i}'
        lump.scale = (1.0, rng.uniform(0.7, 1.1), rng.uniform(0.6, 0.9))
        lump.rotation_euler = (rng.uniform(0, 3), rng.uniform(0, 3), rng.uniform(0, 3))
        lump.data.materials.append(dark if (i % 4 == 3 if dark_every >= 4 else (i * 0.37) % 1.0 < 1 - 1 / dark_every) else glowing)
    bpy.ops.object.light_add(type='POINT', location=(x, y, top + light_above_coals))
    light = bpy.context.active_object
    light.name = 'brazier_light'
    light.data.color = colour
    light.data.energy = energy
    light.data.shadow_soft_size = shadow_soft
    return light


def light_reaches(light, objects, only=True):
    """Chooses which objects a light reaches (Blender's light linking). only=True: the light reaches these
    objects and nothing else; only=False: it reaches everything except these."""
    receivers = bpy.data.collections.new(f'{light.name} reaches')
    for o in objects:
        if o.type == 'MESH':
            receivers.objects.link(o)
    light.light_linking.receiver_collection = receivers
    for item in receivers.collection_objects:
        item.light_linking.link_state = 'INCLUDE' if only else 'EXCLUDE'
    return receivers


def see_through(material, alpha):
    """Makes a material part see-through. An imported glTF glass takes its see-through value from its picture,
    which has none, so a number set on the input was ignored (log 32): the picture is unhooked first."""
    socket = material.node_tree.nodes['Principled BSDF'].inputs['Alpha']
    for link in list(socket.links):
        material.node_tree.links.remove(link)
    socket.default_value = alpha
    return socket


def tint(objects, colour):
    """Darkens and colours every material of these objects by multiplying their base colour (a clean
    white chair made grubby cream). The materials are copied first, so other props keep theirs."""
    for o in objects:
        if o.type != 'MESH':
            continue
        for slot in o.material_slots:
            if not slot.material or not slot.material.use_nodes:
                continue
            material = slot.material.copy()
            slot.material = material
            nodes, links = material.node_tree.nodes, material.node_tree.links
            principled = nodes.get('Principled BSDF')
            if not principled:
                continue
            multiply = nodes.new('ShaderNodeMix')
            multiply.data_type = 'RGBA'
            multiply.blend_type = 'MULTIPLY'
            multiply.inputs['Factor'].default_value = 1.0
            multiply.inputs['B'].default_value = (*colour, 1)
            base = principled.inputs['Base Color']
            if base.is_linked:
                links.new(base.links[0].from_socket, multiply.inputs['A'])
            else:
                multiply.inputs['A'].default_value = base.default_value
            links.new(multiply.outputs['Result'], base)


def render(path, width, height, samples):
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE' if 'BLENDER_EEVEE' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE_NEXT'
    scene.eevee.taa_render_samples = samples
    if hasattr(scene.eevee, 'shadow_pool_size'):
        # the default shadow memory overflows here and draws false hard shadows ("Shadow buffer full"); '1024' still
        # overflowed on the 1536-wide plate, and '2048' can't be set up on this machine ("Could not allocate shadow
        # atlas"), so pictures wider than 1080 get shadows drawn at a lower resolution instead (log 31)
        scene.eevee.shadow_pool_size = '1024'
        scene.eevee.shadow_resolution_scale = min(1.0, 1080 / width)
    scene.render.resolution_x, scene.render.resolution_y = width, height
    scene.render.resolution_percentage = 100
    scene.render.filepath = path
    scene.render.image_settings.file_format = 'PNG'
    bpy.ops.render.render(write_still=True)


def export_for_film(camera, name, fov_degrees, script_name):
    """Writes the dressed set for the film engine: NAME-set.glb (everything the painting is shone onto),
    NAME-signs.glb (the 'signs' collection: boards and notices, which keep their own lettering) and
    NAME-camera.json (the plate camera, as the projector for projected-set.js)."""
    def select_collection(names):
        bpy.ops.object.select_all(action='DESELECT')
        for o in bpy.context.scene.objects:
            in_wanted = any(c.name in names for c in o.users_collection)
            if in_wanted and o.type in ('MESH', 'EMPTY'):
                o.select_set(True)
    sign_names = {'signs'}
    bpy.ops.object.select_all(action='DESELECT')
    for o in bpy.context.scene.objects:
        if o.type in ('MESH', 'EMPTY') and not any(c.name in sign_names for c in o.users_collection) and not any(c.name in ('cameras', 'preview_lights') for c in o.users_collection):
            o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(SET_FOLDER, f'{name}-set.glb'), export_format='GLB', use_selection=True, export_yup=True, export_cameras=False, export_lights=False, export_apply=True)
    select_collection(sign_names)
    bpy.ops.export_scene.gltf(filepath=os.path.join(SET_FOLDER, f'{name}-signs.glb'), export_format='GLB', use_selection=True, export_yup=True, export_cameras=False, export_lights=False, export_apply=True)
    # the projector: the plate camera in three.js space
    q_blender = camera.matrix_world.to_quaternion()
    turn = Quaternion((1, 0, 0), math.radians(-90))
    q_three = turn @ q_blender
    location = camera.matrix_world.translation
    settings = {
        'about': f'The plate camera of the {name} scene ({script_name}), as the projector for projected-set.js. three.js space (y-up): position (x, z, -y) of Blender; quaternion = rotation(-90 deg about x) * Blender quaternion.',
        'position': [round(location.x, 5), round(location.z, 5), round(-location.y, 5)],
        'quaternion': [round(q_three.x, 6), round(q_three.y, 6), round(q_three.z, 6), round(q_three.w, 6)],
        'fov': fov_degrees, 'aspect': 1080 / 1920, 'near': 0.1, 'far': 1500,
        'blender': {'location': [round(v, 5) for v in location], 'rotation_quaternion_wxyz': [round(v, 6) for v in q_blender]},
    }
    with open(os.path.join(SET_FOLDER, f'{name}-camera.json'), 'w') as handle:
        json.dump(settings, handle, indent=1)
