# (Look checker round 2 copy, my own, light direction and strength set per job.)
# What this does (plain words): draws LIT pictures: a flat square with a baked tile (colour + normal map + optionally roughness) lit by a low "raking"
# sun from the upper left so that the relief shows, seen from straight above. It does several pictures in one Blender run. Adapted from
# recipes/slate_layers/verify_look/lit_preview.py (not changed there). Used to look at the reference and the new wood under the same light.
# Use: blender -b --disable-autoexec -t 2 --python tools/lit_preview_multi.py -- JOBS.json
# JOBS.json: a list of {"out": "pic.png", "colour": "colour.png", "normal": "normal.png", "rough": "roughness.png" or "none", "window": 1.0, "cx": 0.5, "cy": 0.5, "pixels": 900}
#   window = how much of the 1 x 1 tile is in the picture (1.0 = all of it, 0.3 = a close-up), cx and cy = the centre of the picture on the tile (0..1, y up).
import json
import math
import sys

import bpy

jobs = [j for j in json.load(open(sys.argv[sys.argv.index('--') + 1])) if 'out' in j]


def render_one(job):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 16
    try:
        scene.cycles.use_denoising = True
    except Exception:
        pass
    scene.render.resolution_x = scene.render.resolution_y = int(job.get('pixels', 900))
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
    mat = bpy.data.materials.new('m')
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes['Principled BSDF']

    def img(path, non_colour):
        node = nt.nodes.new('ShaderNodeTexImage')
        node.image = bpy.data.images.load(path)
        if non_colour:
            node.image.colorspace_settings.name = 'Non-Color'
        node.interpolation = 'Cubic'
        return node
    nt.links.new(img(job['colour'], False).outputs['Color'], bsdf.inputs['Base Color'])
    nm = nt.nodes.new('ShaderNodeNormalMap')
    nm.inputs['Strength'].default_value = 1.0
    nt.links.new(img(job['normal'], True).outputs['Color'], nm.inputs['Color'])
    nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    if job.get('rough', 'none') != 'none':
        sep = nt.nodes.new('ShaderNodeSeparateColor')
        nt.links.new(img(job['rough'], True).outputs['Color'], sep.inputs['Color'])
        nt.links.new(sep.outputs['Red'], bsdf.inputs['Roughness'])
    else:
        bsdf.inputs['Roughness'].default_value = 0.8
    plane.data.materials.append(mat)
    cam_data = bpy.data.cameras.new('c')
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = float(job.get('window', 1.0))
    cam = bpy.data.objects.new('c', cam_data)
    scene.collection.objects.link(cam)
    cam.location = (float(job.get('cx', 0.5)), float(job.get('cy', 0.5)), 3.0)
    scene.camera = cam
    sun_data = bpy.data.lights.new('s', 'SUN')
    sun_data.energy = float(job.get('energy', 4.0))
    sun_data.angle = math.radians(1.0)
    sun = bpy.data.objects.new('s', sun_data)
    scene.collection.objects.link(sun)
    r = job.get('sun', [-70, 0, 35])
    sun.rotation_euler = (math.radians(r[0]), math.radians(r[1]), math.radians(r[2]))
    scene.render.filepath = job['out']
    bpy.ops.render.render(write_still=True)


for job in jobs:
    render_one(job)
