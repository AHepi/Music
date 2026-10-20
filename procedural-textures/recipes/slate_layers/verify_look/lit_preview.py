# What this does (plain words): the look critic's lit check. Puts a baked tile (colour + normal + roughness) on a flat square,
# lights it with a low "raking" sun so the relief shows, and renders it from straight above. Used on the reference and on the default tile.
# Use: blender -b --disable-autoexec -t 2 --python lit_preview.py -- OUT.png COLOUR.png NORMAL.png ROUGHNESS.png|none WINDOW CX CY PIXELS
import math
import sys

import bpy

args = sys.argv[sys.argv.index('--') + 1:]
out, colour, normal, rough = args[0], args[1], args[2], args[3]
window, cx, cy, pixels = float(args[4]), float(args[5]), float(args[6]), int(args[7])

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


c = img(colour, False)
nt.links.new(c.outputs['Color'], bsdf.inputs['Base Color'])
n = img(normal, True)
nm = nt.nodes.new('ShaderNodeNormalMap')
nm.inputs['Strength'].default_value = 1.0
nt.links.new(n.outputs['Color'], nm.inputs['Color'])
nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
if rough != 'none':
    r = img(rough, True)
    sep = nt.nodes.new('ShaderNodeSeparateColor')
    nt.links.new(r.outputs['Color'], sep.inputs['Color'])
    nt.links.new(sep.outputs['Red'], bsdf.inputs['Roughness'])
else:
    bsdf.inputs['Roughness'].default_value = 0.8
plane.data.materials.append(mat)

cam_data = bpy.data.cameras.new('c')
cam_data.type = 'ORTHO'
cam_data.ortho_scale = window
cam = bpy.data.objects.new('c', cam_data)
scene.collection.objects.link(cam)
cam.location = (cx, cy, 3.0)
scene.camera = cam

sun_data = bpy.data.lights.new('s', 'SUN')
sun_data.energy = 4.0
sun_data.angle = math.radians(1.0)
sun = bpy.data.objects.new('s', sun_data)
scene.collection.objects.link(sun)
# light comes from the upper-left of the picture, 20 degrees above the surface (raking)
sun.rotation_euler = (math.radians(-70), 0, math.radians(35))

scene.render.filepath = out
bpy.ops.render.render(write_still=True)
