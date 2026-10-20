# Plain note: runs INSIDE Blender (blender -b --disable-autoexec --python blender_preview.py -- MAPS_FOLDER OUT.png).
# Loads colour.png, normal.png (OpenGL), roughness.png and height.png from a folder of maps made by Material Maker (after finish_maps.py), puts them on
# one flat square with an ordinary Principled material (Image Texture -> Principled, Normal Map node, small Displacement via bump) and
# photographs it from above with a low sun so the bumps show. Proves the Material Maker maps load and look right in Blender.
import sys, os
import bpy
args = sys.argv[sys.argv.index('--') + 1:]
folder, out = args[0], args[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 24
scene.cycles.use_denoising = False
scene.render.resolution_x = scene.render.resolution_y = 600
scene.render.filepath = out
scene.view_settings.view_transform = 'Standard'
bpy.ops.mesh.primitive_plane_add(size=2)
plane = bpy.context.active_object
mat = bpy.data.materials.new('MM_maps')
mat.use_nodes = True
nt = mat.node_tree
for n in list(nt.nodes):
    nt.nodes.remove(n)
out_n = nt.nodes.new('ShaderNodeOutputMaterial')
bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
nt.links.new(bsdf.outputs['BSDF'], out_n.inputs['Surface'])


def image_node(name, colourspace):
    img = bpy.data.images.load(os.path.join(folder, name))
    img.colorspace_settings.name = colourspace
    node = nt.nodes.new('ShaderNodeTexImage')
    node.image = img
    return node


col = image_node('colour.png', 'sRGB')
nt.links.new(col.outputs['Color'], bsdf.inputs['Base Color'])
if os.path.exists(os.path.join(folder, 'roughness.png')):
    rough = image_node('roughness.png', 'Non-Color')
    nt.links.new(rough.outputs['Color'], bsdf.inputs['Roughness'])
nrm = image_node('normal.png', 'Non-Color')
nmap = nt.nodes.new('ShaderNodeNormalMap')
nmap.inputs['Strength'].default_value = 1.0
nt.links.new(nrm.outputs['Color'], nmap.inputs['Color'])
nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
plane.data.materials.append(mat)
cam_data = bpy.data.cameras.new('cam'); cam_data.type = 'ORTHO'; cam_data.ortho_scale = 2.0
cam = bpy.data.objects.new('cam', cam_data); scene.collection.objects.link(cam); cam.location = (0, 0, 3); scene.camera = cam
sun_data = bpy.data.lights.new('sun', 'SUN'); sun_data.energy = 4.0; sun_data.angle = 0.05
sun = bpy.data.objects.new('sun', sun_data); scene.collection.objects.link(sun); sun.rotation_euler = (0.75, 0.0, 0.6)
bpy.ops.render.render(write_still=True)
print('rendered', out)
