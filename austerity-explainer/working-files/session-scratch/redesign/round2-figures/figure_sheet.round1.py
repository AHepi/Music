# What this does: draws contact sheets of the figures built by build_figures.py, to check them by eye
# before they go into a shot. It loads every figure's .glb (so it checks what was saved, not what was
# built), stands them in a row a little apart and draws the row from behind, from the side and from the
# front, lit like the pit village at dusk (a cool sky, a warm fire low in front of them, a pale lamp-lit
# wall beyond them), and once more from behind as black shapes on the lit wall (their silhouettes).
# The camera is 7 m from the row (the distance of the waiting men in the plan) with a narrow lens, so each
# figure is drawn about as many pixels tall as it is in a plate at 7 m.
# Writes sheet-back.png, sheet-side.png, sheet-front.png and sheet-silhouettes.png into OUT_FOLDER.
# Run (EEVEE needs a virtual screen):
#   DISPLAY=:96 blender -b --python figure_sheet.py -- OUT_FOLDER [NAME ...]

import json
import math
import os
import sys

import bpy

FIGURES_FOLDER = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..',
                                              'assets', 'models', 'inflation-chapter-2-newcomers', 'figures'))
SPACING = 1.25            # metres between figures in the row
CAMERA_DISTANCE = 7.0
PIXELS_PER_METRE = 290    # about a plate at 7 m (1536 x 2730, 64.4 degrees top to bottom)

arguments = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
out_folder = arguments[0]
os.makedirs(out_folder, exist_ok=True)
with open(os.path.join(FIGURES_FOLDER, 'index.json')) as handle:
    names = [entry['file'][:-4] for entry in json.load(handle)]
names = arguments[1:] or names

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

figures = []
for i, name in enumerate(names):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(FIGURES_FOLDER, f'{name}.glb'))
    root = next(o for o in bpy.data.objects if o not in before and o.parent is None)
    root.location = ((i - (len(names) - 1) / 2) * SPACING, 0, 0)
    root.rotation_mode = 'XYZ'   # the glTF importer leaves it on quaternions, and the sheet turns figures round
    figures.append(root)
width = len(names) * SPACING + 0.4


def plane(name, size, location, rotation, colour, glow=0.0):
    bpy.ops.mesh.primitive_plane_add(size=1, location=location, rotation=rotation)
    obj = bpy.context.active_object
    obj.name = name
    obj.scale = (*size, 1)
    material = bpy.data.materials.new(name)
    shader = material.node_tree.nodes['Principled BSDF']
    shader.inputs['Base Color'].default_value = (*colour, 1)
    shader.inputs['Roughness'].default_value = 0.9
    if glow:
        shader.inputs['Emission Color'].default_value = (*colour, 1)
        shader.inputs['Emission Strength'].default_value = glow
    obj.data.materials.append(material)
    return obj


plane('ground', (width + 20, 40), (0, 0, 0), (0, 0, 0), (0.07, 0.07, 0.075))
wall = plane('lamp-lit wall', (width + 20, 8), (0, 6, 4), (math.radians(90), 0, 0), (0.30, 0.27, 0.22), glow=0.5)

world = bpy.data.worlds.new('dusk')
scene.world = world
world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.10, 0.13, 0.19, 1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value = 1.2

# a warm strip low in front of the row (a brazier for each), and a pale lamp high beyond them
bpy.ops.object.light_add(type='AREA', location=(0, 1.1, 0.95))
fire = bpy.context.active_object
fire.data.shape = 'RECTANGLE'
fire.data.size, fire.data.size_y = width, 0.3
fire.data.color = (1.0, 0.5, 0.2)
fire.data.energy = 60 * len(names)
fire.rotation_euler = (math.radians(-90), 0, 0)   # facing -y, toward the figures' fronts
bpy.ops.object.light_add(type='SUN', location=(0, 0, 10))
lamp = bpy.context.active_object
lamp.data.energy = 0.6
lamp.data.color = (0.95, 0.92, 0.85)
lamp.rotation_euler = (math.radians(-35), 0, math.radians(10))   # from beyond the row, a little to one side

bpy.ops.object.camera_add()
camera = bpy.context.active_object
scene.camera = camera
camera.data.type = 'PERSP'
camera.data.sensor_fit = 'VERTICAL'
frame_height = 2.3
camera.data.angle_y = 2 * math.atan(frame_height / 2 / CAMERA_DISTANCE)
camera.data.lens_unit = 'FOV'
scene.render.engine = 'BLENDER_EEVEE'
scene.eevee.taa_render_samples = 24
scene.render.resolution_y = int(frame_height * PIXELS_PER_METRE)
scene.render.resolution_x = int(scene.render.resolution_y * width / frame_height * 1.0)
scene.render.film_transparent = False
scene.view_settings.view_transform = 'AgX'


def shoot(file_name, location, rotation):
    # square on (orthographic): a wide perspective turned the figures at the ends of the row half round
    camera.location = location
    camera.rotation_euler = rotation
    camera.data.type = 'ORTHO'
    camera.data.sensor_fit = 'HORIZONTAL'
    camera.data.ortho_scale = width
    scene.render.filepath = os.path.join(out_folder, file_name)
    bpy.ops.render.render(write_still=True)


eye = 1.0   # the middle of the frame (square-on drawing: the height only frames the row)
look_down = 0.0   # square on
shoot('sheet-back.png', (0, -CAMERA_DISTANCE, eye), (math.radians(90 - look_down), 0, 0))
# from the side, each figure turned a quarter round on its own spot
for root in figures:
    root.rotation_euler.z = math.radians(90)
shoot('sheet-side.png', (0, -CAMERA_DISTANCE, eye), (math.radians(90 - look_down), 0, 0))
for root in figures:
    root.rotation_euler.z = math.radians(180)
shoot('sheet-front.png', (0, -CAMERA_DISTANCE, eye), (math.radians(90 - look_down), 0, 0))
# silhouettes: the figures black, from behind, on the lit wall
black = bpy.data.materials.new('silhouette')
black.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0, 0, 0, 1)
black.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 1
for root in figures:
    root.rotation_euler.z = 0
    for o in root.children_recursive:
        if o.type == 'MESH':
            for slot in o.material_slots:
                slot.material = black
wall.data.materials[0].node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = 3.0
shoot('sheet-silhouettes.png', (0, -CAMERA_DISTANCE, eye), (math.radians(90 - look_down), 0, 0))
print('figure_sheet: done')
