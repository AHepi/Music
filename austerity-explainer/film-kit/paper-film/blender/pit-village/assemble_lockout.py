# What this does: puts together the "lockout" scene for the plan 3 test (log 29): the pit village
# street (street.blend) with props from the props library placed in it, in 1926 during the miners'
# lockout, at dusk:
#   - a handcart with coal sacks in the street near the camera (coal picked from the tips)
#   - a brazier burning on the right, with a lit glow, beside a notice board on posts carrying the
#     colliery's lock-out notice
#   - dustbins, a barrel, pails and a coal pile by the doorways further up
#   - the colliery's iron gates shut across the top of the street, with its name board
# Then, when asked:
#   --plate FILE    renders the plate (the picture the repaint starts from) from the main camera
#   --preview FILE  renders a quick small version of the same view
#   --export        writes the scene for the film engine: lockout-set.glb (everything the painting is
#                   shone onto) and lockout-signs.glb (the name board and the notice, which keep their
#                   own lettering), and lockout-camera.json (the plate camera, for the projector)
# Run (EEVEE needs a virtual screen):
#   Xvfb :96 -screen 0 1920x1080x24 &
#   DISPLAY=:96 blender -b assets/models/pit-village/street.blend --python paper-film/blender/pit-village/assemble_lockout.py -- --preview out.png
# Units are metres; Blender is z-up, the street runs along +y and rises 4 degrees.

import json
import math
import random
import os
import sys

import bpy
from mathutils import Euler, Quaternion, Vector

KIT_FOLDER = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))   # the kit's top folder
SET_FOLDER = os.path.join(KIT_FOLDER, 'assets/models/pit-village')
PROPS_FOLDER = os.path.join(SET_FOLDER, 'props')

arguments = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
def option(name, default=None):
    return arguments[arguments.index(name) + 1] if name in arguments else default

# the plate camera: a little left of the street's middle, eye height, looking up the street and a
# little to the right, so the right-hand cottages, the brazier and the notice are in view and the
# pithead rises above the roofs. The plate is drawn a little wider than the film frame (44 against
# 40 degrees), so the camera can move without running off the painting.
CAMERA_POSITION = Vector((-1.0, 1.2, 0.0))
CAMERA_EYE_HEIGHT = 1.55
CAMERA_YAW_DEGREES = -6.0          # turn to the right (negative about z)
CAMERA_PITCH_DEGREES = 8.0         # look up a little
PLATE_FOV_DEGREES = 44.0


def ground_height(x, y, start=60.0):
    """The height of whatever surface is under (x, y), found by casting a ray straight down from
    `start` (start below a prop to find the ground under it rather than the prop's top)."""
    depsgraph = bpy.context.evaluated_depsgraph_get()
    hit, location, normal, index, hit_object, matrix = bpy.context.scene.ray_cast(depsgraph, Vector((x, y, start)), Vector((0, 0, -1)))
    return location.z if hit else min(y, 76) * math.tan(math.radians(4))


def place_prop(file_name, x, y, turn_degrees=0.0, name=None, lift=0.0, collection='props', scale=1.0):
    """Imports a prop from the library and stands it on the surface at (x, y), turned about z."""
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
    holder.location = (x, y, ground_height(x, y) + lift)
    holder.rotation_euler = (0, 0, math.radians(turn_degrees))
    holder.scale = (scale, scale, scale)
    return holder


def wooden_post(x, y, height, collection='signs', start=60.0, material=None, turn_degrees=0.0):
    """A square timber post standing on the ground at (x, y). With `material` (for example the
    notice board's own timber) it wears that, its picture repeating once a metre."""
    ground = ground_height(x, y, start)
    bpy.ops.mesh.primitive_cube_add(size=1)
    post = bpy.context.active_object
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


def brazier_fire(x, y):
    """A heaped bed of coals in the brazier drum, glowing orange with some dark lumps among them,
    and the warm light it throws. The flames themselves are drawn live in the film (lockout-test.js):
    flame shapes in the plate looked like paper cut-outs once painted."""
    top = ground_height(x, y) + 0.80
    glowing = glow_material('brazier coals', (1.0, 0.16, 0.015), 1.0)
    dark = bpy.data.materials.new('brazier dark coal')
    dark.use_nodes = True
    dark.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.02, 0.018, 0.016, 1)
    dark.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 0.5
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
        lump.data.materials.append(dark if i % 4 == 3 else glowing)
    bpy.ops.object.light_add(type='POINT', location=(x, y, top + 0.6))
    light = bpy.context.active_object
    light.name = 'brazier_light'
    light.data.color = (1.0, 0.55, 0.25)
    light.data.energy = 900
    light.data.shadow_soft_size = 0.25
    return light


def build_scene():
    for name in ('props', 'signs'):
        if name not in bpy.data.collections:
            collection = bpy.data.collections.new(name)
            bpy.context.scene.collection.children.link(collection)
    # near the camera: the handcart with coal sacks, and a few lumps of coal in the road
    # (the sacks go down first, so they stand on the road, not on the cart)
    sacks = place_prop('coal-sacks.glb', -0.2, 8.4, turn_degrees=18)
    for o in list(sacks.children_recursive):   # the two standing sacks read as clay jars once painted
        if o.name.startswith('sack-standing'):
            bpy.data.objects.remove(o, do_unlink=True)
    place_prop('handcart.glb', -1.75, 9.6, turn_degrees=-70)
    place_prop('coal-pile.glb', 0.75, 8.0, turn_degrees=-20, scale=0.25)   # a few picked lumps: coal was scarce
    place_prop('wooden-pail.glb', 1.75, 9.0, turn_degrees=40)
    place_prop('hurricane-lantern.glb', -0.55, 10.1, turn_degrees=10)
    place_prop('spade.glb', -1.15, 8.9, turn_degrees=70)
    # the brazier with its fire, and the notice board on two posts beside it
    place_prop('brazier-drum.glb', 0.95, 10.4)
    brazier_fire(0.95, 10.4)
    board = place_prop('notice-on-board.glb', 2.25, 13.6, turn_degrees=-17, lift=1.05, collection='signs')
    bpy.context.view_layer.update()   # so the board's matrix_world holds its new place
    board_timber = next((m for o in board.children_recursive if o.type == 'MESH' for m in o.data.materials
                         if m and m.name.startswith('grey-timber')), None)
    for dx in (-0.36, 0.36):
        corner = board.matrix_world @ Vector((dx, 0.06, 0))
        # the ray starts under the board, so it finds the road, not the board's own top
        wooden_post(corner.x, corner.y, 2.2, start=board.location.z - 0.02, material=board_timber, turn_degrees=-17)
    # by the doorways further up the street
    place_prop('dustbins.glb', 3.55, 14.2, turn_degrees=90)
    place_prop('wooden-barrel.glb', -3.6, 15.5)
    place_prop('wooden-pail.glb', 3.6, 19.3)
    place_prop('wooden-wash-tub.glb', -3.55, 22.0)
    place_prop('coal-pile.glb', 3.2, 24.5, turn_degrees=30, scale=0.35)
    place_prop('step-ladder.glb', -3.7, 28.0, turn_degrees=90)
    # the colliery gates shut across the top of the street, with the name board beside them
    place_prop('iron-gates-pair.glb', -1.5, 71.5)
    place_prop('iron-gates-pair.glb', 1.5, 71.5)
    place_prop('colliery-name-board.glb', 0.0, 72.4, collection='signs', scale=1.35)   # big enough to read from the street
    place_prop('coal-tub-on-track.glb', -1.0, 76.5, turn_degrees=90)


def set_camera():
    camera = bpy.data.objects.get('main_camera')
    position = CAMERA_POSITION.copy()
    position.z = ground_height(position.x, position.y) + CAMERA_EYE_HEIGHT
    camera.location = position
    camera.rotation_mode = 'XYZ'
    camera.rotation_euler = Euler((math.radians(90 + CAMERA_PITCH_DEGREES), 0, math.radians(CAMERA_YAW_DEGREES)), 'XYZ')
    camera.data.sensor_fit = 'VERTICAL'
    camera.data.angle_y = math.radians(PLATE_FOV_DEGREES)
    camera.data.clip_start = 0.1
    camera.data.clip_end = 1500
    bpy.context.scene.camera = camera
    return camera


def render(path, width, height, samples):
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE' if 'BLENDER_EEVEE' in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE_NEXT'
    scene.eevee.taa_render_samples = samples
    scene.render.resolution_x, scene.render.resolution_y = width, height
    scene.render.resolution_percentage = 100
    scene.render.filepath = path
    scene.render.image_settings.file_format = 'PNG'
    bpy.ops.render.render(write_still=True)


def export(camera):
    # the signs keep their own lettering, so they go in their own file
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
    bpy.ops.export_scene.gltf(filepath=os.path.join(SET_FOLDER, 'lockout-set.glb'), export_format='GLB', use_selection=True, export_yup=True, export_cameras=False, export_lights=False, export_apply=True)
    select_collection(sign_names)
    bpy.ops.export_scene.gltf(filepath=os.path.join(SET_FOLDER, 'lockout-signs.glb'), export_format='GLB', use_selection=True, export_yup=True, export_cameras=False, export_lights=False, export_apply=True)
    # the projector: the plate camera in three.js space
    q_blender = camera.matrix_world.to_quaternion()
    turn = Quaternion((1, 0, 0), math.radians(-90))
    q_three = turn @ q_blender
    location = camera.matrix_world.translation
    settings = {
        'about': 'The plate camera of the lockout scene (assemble_lockout.py), as the projector for projected-set.js. three.js space (y-up): position (x, z, -y) of Blender; quaternion = rotation(-90 deg about x) * Blender quaternion.',
        'position': [round(location.x, 5), round(location.z, 5), round(-location.y, 5)],
        'quaternion': [round(q_three.x, 6), round(q_three.y, 6), round(q_three.z, 6), round(q_three.w, 6)],
        'fov': PLATE_FOV_DEGREES, 'aspect': 1080 / 1920, 'near': 0.1, 'far': 1500,
        'blender': {'location': [round(v, 5) for v in location], 'rotation_quaternion_wxyz': [round(v, 6) for v in q_blender]},
    }
    with open(os.path.join(SET_FOLDER, 'lockout-camera.json'), 'w') as handle:
        json.dump(settings, handle, indent=1)


build_scene()
camera = set_camera()
if option('--preview'):
    render(option('--preview'), 540, 960, 16)
if option('--plate'):
    render(option('--plate'), 1536, 2730, int(option('--samples', '48')))
if '--export' in arguments:
    export(camera)
if option('--save'):
    bpy.ops.wm.save_as_mainfile(filepath=option('--save'), relative_remap=True)
print('assemble_lockout: done')
