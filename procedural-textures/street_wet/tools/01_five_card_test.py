# What this does: the "any material" test of the WETNESS layer. Five flat cards, each wearing a different kind of surface (the street's photo brick, the
# street's photo cobblestone, and the finished texture-recipe tiles of slate, mud and wood from the earlier trials), each drawn dry, damp and soaked
# with the SAME layer settings (only the porosity changes per card: brick 0.7, cobble 0.6, slate 0.3, mud 0.7, wood 0.3). Nothing is changed in the layer for any card.
# Run: blender -b --disable-autoexec -t 2 --python tools/01_five_card_test.py -- OUT_FOLDER
# Writes OUT_FOLDER/five_cards.png, five_cards_report.json (average brightness of each card, dry against wet).
import json
import math
import os
import sys
import time

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True
import wetness_layer as wl  # noqa: E402

out_folder = sys.argv[sys.argv.index('--') + 1]
os.makedirs(out_folder, exist_ok=True)
ROOT = os.path.abspath(os.path.join(HERE, '..'))
PROC = os.path.abspath(os.path.join(ROOT, '..'))
TEXTURES = os.path.join(ROOT, 'set_copy', 'textures') + os.sep
MAPS = os.path.join(ROOT, 'set_copy', 'polyhaven_maps') + os.sep
slate = os.path.join(PROC, 'recipes/slate_layers/outputs/default') + os.sep
mud = os.path.join(PROC, 'reuse_trials/mud/final/seeds_1') + os.sep
wood = os.path.join(PROC, 'reuse_trials/wood/final/seeds_1') + os.sep

bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)
scene = bpy.context.scene
world = bpy.data.worlds.new('dusk')
world.use_nodes = True
world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.35, 0.45, 0.62, 1)
world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.9
scene.world = world
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - Medium High Contrast'
scene.view_settings.exposure = 0.0


def picture(path, colour):
    image = bpy.data.images.load(path, check_existing=True)
    image.colorspace_settings.name = 'sRGB' if colour else 'Non-Color'
    return image


CARDS = [  # label, colour, normal, rough, height, uv span, porosity
    ('photo brick', TEXTURES + 'red_brick_colour.jpg', TEXTURES + 'red_brick_normal.jpg', MAPS + 'red_brick_rough.jpg', MAPS + 'red_brick_displacement.jpg', 0.7, 0.7),
    ('photo cobblestone', TEXTURES + 'square_cobblestone_colour.jpg', TEXTURES + 'square_cobblestone_normal.jpg', MAPS + 'square_cobblestone_rough.jpg',
     MAPS + 'square_cobblestone_displacement.jpg', 0.5, 0.6),
    ('our slate tile', slate + 'colour.png', slate + 'normal.png', slate + 'roughness.png', slate + 'height.png', 1.0, 0.3),
    ('our mud tile', mud + 'colour.png', mud + 'normal.png', mud + 'roughness.png', mud + 'height.png', 1.0, 0.7),
    ('our wood tile', wood + 'colour.png', wood + 'normal.png', wood + 'roughness.png', wood + 'height.png', 1.0, 0.3),
]
STATES = [('dry', 0.0, 0.0), ('damp', 0.5, 0.2), ('soaked', 1.0, 0.6)]
TINT = {'photo brick': (0.62, 0.5, 0.46), 'photo cobblestone': (0.62, 0.62, 0.64)}
SPACING, CARD = 1.15, 1.0
cards = []
for column, (label, colour, normal, rough, height, span, porosity) in enumerate(CARDS):
    for row, (state_label, wetness, puddles) in enumerate(STATES):
        material = bpy.data.materials.new(f'{label} {state_label}')
        material.use_nodes = True
        tree = material.node_tree
        principled = tree.nodes['Principled BSDF']
        colour_node = tree.nodes.new('ShaderNodeTexImage')
        colour_node.image = picture(colour, True)
        tint = TINT.get(label)
        if tint:
            multiply = tree.nodes.new('ShaderNodeMix')
            multiply.data_type, multiply.blend_type = 'RGBA', 'MULTIPLY'
            multiply.inputs['Factor'].default_value = 1.0
            multiply.inputs[7].default_value = (*tint, 1)
            tree.links.new(colour_node.outputs['Color'], multiply.inputs[6])
            tree.links.new(multiply.outputs[2], principled.inputs['Base Color'])
        else:
            tree.links.new(colour_node.outputs['Color'], principled.inputs['Base Color'])
        normal_node = tree.nodes.new('ShaderNodeTexImage')
        normal_node.image = picture(normal, False)
        normal_map = tree.nodes.new('ShaderNodeNormalMap')
        tree.links.new(normal_node.outputs['Color'], normal_map.inputs['Color'])
        tree.links.new(normal_map.outputs['Normal'], principled.inputs['Normal'])
        principled.inputs['Roughness'].default_value = 0.85
        node = wl.add_wetness_to_material(material, wetness=wetness, puddles=puddles, rough_image=picture(rough, False), height_image=picture(height, False),
                                          porosity=porosity, wet_roughness=0.3, seed=1.0 + column)
        mesh = bpy.data.meshes.new(f'card {label} {state_label}')
        mesh.from_pydata([(0, 0, 0), (CARD, 0, 0), (CARD, CARD, 0), (0, CARD, 0)], [], [(0, 1, 2, 3)])
        uv = mesh.uv_layers.new(name='UVMap')
        for loop, corner in zip(mesh.loops, [(0, 0), (span, 0), (span, span), (0, span)]):
            uv.data[loop.index].uv = corner
        mesh.materials.append(material)
        obj = bpy.data.objects.new(mesh.name, mesh)
        obj.location = ((column - 2) * SPACING - CARD / 2, (1 - row) * SPACING - CARD / 2, 0)
        scene.collection.objects.link(obj)
        cards.append((label, state_label, obj))
# lights: a low warm lamp behind the cards (so wet surfaces throw its shine toward the camera) and a weak cool fill
lamp = bpy.data.objects.new('lamp', bpy.data.lights.new('lamp', 'AREA'))      # a long low warm strip behind the cards, so every card meets its shine
lamp.data.energy, lamp.data.color = 650.0, (1.0, 0.7, 0.42)
lamp.data.shape, lamp.data.size, lamp.data.size_y = 'RECTANGLE', 8.0, 1.0
lamp.location = (0.0, 5.5, 1.3)
lamp.rotation_euler = (math.radians(90) + math.radians(8), 0, math.radians(180))   # facing the cards (-y), tilted a little down
scene.collection.objects.link(lamp)
fill = bpy.data.objects.new('fill', bpy.data.lights.new('fill', 'SUN'))
fill.data.energy, fill.data.color = 0.8, (0.62, 0.72, 0.9)
fill.rotation_euler = (math.radians(35), 0, math.radians(200))
scene.collection.objects.link(fill)
camera_data = bpy.data.cameras.new('cam')
camera_data.sensor_fit = 'HORIZONTAL'
camera_data.angle_x = math.radians(52)
camera = bpy.data.objects.new('cam', camera_data)
camera.location = Vector((0, -4.4, 3.9))
camera.rotation_euler = (Vector((0, 0.15, 0)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
scene.collection.objects.link(camera)
scene.camera = camera
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 40
scene.cycles.use_denoising = True
scene.cycles.denoiser = 'OPENIMAGEDENOISE'
scene.cycles.max_bounces = 6
scene.render.resolution_x, scene.render.resolution_y = 1300, 800
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = os.path.join(out_folder, 'five_cards.png')
started = time.time()
bpy.ops.render.render(write_still=True)
seconds = round(time.time() - started, 1)
# a second picture of the same cards lit by flat light only (colour darkening alone, no reflections): the world is white, no lamps, every surface matte
print('DRAWN five cards', seconds, 's')
from bpy_extras.object_utils import world_to_camera_view
boxes = []
for label, state, obj in cards:      # where each card is in the picture (pixels, y down), so the average brightness of each card can be measured afterwards
    corners = [world_to_camera_view(scene, camera, obj.matrix_world @ Vector(c)) for c in ((0, 0, 0), (CARD, 0, 0), (CARD, CARD, 0), (0, CARD, 0))]
    boxes.append({'label': label, 'state': state, 'corners_px': [[round(c.x * scene.render.resolution_x, 1), round((1 - c.y) * scene.render.resolution_y, 1)] for c in corners]})
with open(os.path.join(out_folder, 'five_cards_report.json'), 'w') as handle:
    json.dump({'seconds': seconds, 'cards': boxes}, handle, indent=1)
