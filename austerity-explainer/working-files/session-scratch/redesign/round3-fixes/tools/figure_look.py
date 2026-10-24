# What this does (scratch check): imports figure .glb files and draws each one whole, from behind, three-quarter
# behind (from its left) and the side, lit like the people test: a cool dusk sky, a warm low fire in front of each
# figure and a pale street lamp high behind the camera. About 300 pixels a metre (a plate at about 7 m), or more
# with --scale. One picture per figure, NAME.png.
# Run: DISPLAY=:96 blender -b --python figure_look.py -- FIGURES_FOLDER OUT_FOLDER [--scale 2] NAME ...
import math
import os
import sys

import bpy
from mathutils import Vector

arguments = sys.argv[sys.argv.index('--') + 1:]
pixels_per_metre = 300
if '--scale' in arguments:
    at = arguments.index('--scale')
    pixels_per_metre *= float(arguments[at + 1])
    del arguments[at:at + 2]
folder, out_folder, names = arguments[0], arguments[1], arguments[2:]
os.makedirs(out_folder, exist_ok=True)
views = [('back', 0), ('three-quarter back from its left', -45), ('three-quarter back from its right', 45), ('side', 90)]
spacing = 1.1
for name in names:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    world = bpy.data.worlds.new('dusk')
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.10, 0.13, 0.19, 1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value = 1.96
    bpy.ops.mesh.primitive_plane_add(size=60)
    ground = bpy.context.active_object
    material = bpy.data.materials.new('ground')
    material.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.08, 0.08, 0.085, 1)
    ground.data.materials.append(material)
    top = 0
    for j, (label, angle) in enumerate(views):
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=os.path.join(folder, name + '.glb'))
        root = next(o for o in bpy.data.objects if o not in before and o.parent is None)
        root.location = (j * spacing, 0, 0)
        root.rotation_mode = 'XYZ'
        root.rotation_euler.z = math.radians(angle)
        bpy.context.view_layer.update()
        top = max([top] + [(o.matrix_world @ Vector(c)).z for o in root.children_recursive if o.type == 'MESH' for c in o.bound_box])
        facing = root.matrix_world.to_quaternion() @ Vector((0, 1, 0))
        bpy.ops.object.light_add(type='POINT', location=root.location + facing * 0.7 + Vector((0, 0, 0.95)))
        light = bpy.context.active_object
        light.data.energy, light.data.color, light.data.shadow_soft_size = 60, (1.0, 0.55, 0.25), 0.2
    bpy.ops.object.light_add(type='POINT', location=((len(views) - 1) * spacing / 2, -5.0, 4.0))
    lamp = bpy.context.active_object
    lamp.data.energy, lamp.data.color = 400, (1.0, 0.85, 0.65)
    bpy.ops.object.light_add(type='SUN')
    sun = bpy.context.active_object
    sun.data.energy = 0.5
    sun.rotation_euler = (math.radians(-40), 0, math.radians(15))
    scene.render.engine = 'BLENDER_EEVEE'
    scene.eevee.taa_render_samples = 24
    scene.view_settings.view_transform = 'AgX'
    bpy.ops.object.camera_add()
    camera = bpy.context.active_object
    scene.camera = camera
    camera.data.type = 'ORTHO'
    width = len(views) * spacing
    height = top + 0.15
    camera.data.ortho_scale = max(width, height)
    camera.location = ((len(views) - 1) * spacing / 2, -8, height / 2)
    camera.rotation_euler = (math.radians(90), 0, 0)
    scene.render.resolution_x = int(width * pixels_per_metre)
    scene.render.resolution_y = int(height * pixels_per_metre)
    scene.render.filepath = os.path.join(out_folder, name + '.png')
    bpy.ops.render.render(write_still=True)
print('figure_look: done')
