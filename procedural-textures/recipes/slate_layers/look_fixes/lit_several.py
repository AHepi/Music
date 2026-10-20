# What this does (plain words): the look checker's lit check (verify_look/lit_preview.py) for SEVERAL tiles in one Blender run. Each tile
# (colour + normal + roughness) is laid on a flat square, lit by a low "raking" sun 20 degrees above the surface from the upper left, and
# photographed from straight above. The scene, light, camera and sample count are copied unchanged from verify_look/lit_preview.py, so the
# pictures can be put next to the checker's own.
# Use: blender -b --disable-autoexec -t 2 --python lit_several.py -- 'JSON [[OUT.png, COLOUR.png, NORMAL.png, ROUGHNESS.png or "none", WINDOW, CX, CY, PIXELS], ...]'
import json
import math
import sys

import bpy


def render_one(out, colour, normal, rough, window, cx, cy, pixels):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 24
    try:
        scene.cycles.use_denoising = True
    except Exception:
        pass
    scene.render.resolution_x = pixels
    scene.render.resolution_y = pixels
    scene.render.film_transparent = False
    scene.view_settings.view_transform = 'Standard'
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 2
    world = bpy.data.worlds.new('w')
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.55, 0.6, 0.7, 1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.25
    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0.5, 0.5, 0))
    plane = bpy.context.active_object
    material = bpy.data.materials.new('m')
    material.use_nodes = True
    tree = material.node_tree
    shader = tree.nodes['Principled BSDF']

    def picture(path, non_colour):
        node = tree.nodes.new('ShaderNodeTexImage')
        node.image = bpy.data.images.load(path)
        if non_colour:
            node.image.colorspace_settings.name = 'Non-Color'
        node.interpolation = 'Cubic'
        return node

    colour_node = picture(colour, False)
    tree.links.new(colour_node.outputs['Color'], shader.inputs['Base Color'])
    normal_node = picture(normal, True)
    normal_map = tree.nodes.new('ShaderNodeNormalMap')
    normal_map.inputs['Strength'].default_value = 1.0
    tree.links.new(normal_node.outputs['Color'], normal_map.inputs['Color'])
    tree.links.new(normal_map.outputs['Normal'], shader.inputs['Normal'])
    if rough != 'none':
        rough_node = picture(rough, True)
        separate = tree.nodes.new('ShaderNodeSeparateColor')
        tree.links.new(rough_node.outputs['Color'], separate.inputs['Color'])
        tree.links.new(separate.outputs['Red'], shader.inputs['Roughness'])
    else:
        shader.inputs['Roughness'].default_value = 0.8
    plane.data.materials.append(material)
    camera_data = bpy.data.cameras.new('c')
    camera_data.type = 'ORTHO'
    camera_data.ortho_scale = window
    camera = bpy.data.objects.new('c', camera_data)
    scene.collection.objects.link(camera)
    camera.location = (cx, cy, 3.0)
    scene.camera = camera
    sun_data = bpy.data.lights.new('s', 'SUN')
    sun_data.energy = 4.0
    sun_data.angle = math.radians(1.0)
    sun = bpy.data.objects.new('s', sun_data)
    scene.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(-70), 0, math.radians(35))
    scene.render.filepath = out
    bpy.ops.render.render(write_still=True)


jobs = json.loads(sys.argv[sys.argv.index('--') + 1:][0])
if isinstance(jobs, dict):           # a job file with a plain note: {"_note": "...", "jobs": [...]}
    jobs = jobs['jobs']
for job in jobs:
    out, colour, normal, rough = job[0], job[1], job[2], job[3]
    render_one(out, colour, normal, rough, float(job[4]), float(job[5]), float(job[6]), int(job[7]))
    print('[lit] done', out, flush=True)
