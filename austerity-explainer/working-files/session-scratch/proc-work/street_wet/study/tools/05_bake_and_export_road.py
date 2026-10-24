# What this does: a test of the "maps to bake for the glb" part of the plan, on the road of the pit village street (street.blend is opened and never saved):
#   1. puts the WETNESS draft on the road and draws the close view of the setts LIVE (the node group working out the wet look at every dot);
#   2. "photographs" the group's outputs from straight above (the same trick lib/bake_harness.py uses for the texture recipes) into flat pictures, one dot per
#      centimetre: wet colour, roughness, clear-coat strength, clear-coat roughness, a flattened-puddle normal map and the puddle mask;
#   3. gives the road a second set of texture coordinates (UV2: across the road and along it, once, so nothing repeats), builds a plain material that wears only those
#      pictures, and draws the same close view with it (the BAKED look);
#   4. writes the road alone, wearing the baked material, as a .glb, so the .glb can be opened and checked (which extensions the exporter wrote, which pictures).
# It measures how far the baked picture is from the live one. Only the stretch of road from y = 8 m to y = 40 m is baked (the test, not the whole street).
# Run: blender -b --disable-autoexec -t 2 street.blend --python 05_bake_and_export_road.py -- OUT_FOLDER
import json
import math
import os
import sys
import time

import bpy
from mathutils import Vector

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wetness_group as wg  # noqa: E402

out_folder = sys.argv[sys.argv.index('--') + 1]
os.makedirs(out_folder, exist_ok=True)
TEX = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/study/work/polyhaven_maps/'
Y0, Y1, X_HALF = 8.0, 40.0, 2.2            # the baked stretch of road: 32 m long, 4.4 m wide
PIXELS_PER_METRE = 100                     # one dot per centimetre
SLOPE = math.atan(0.0699)                  # the street rises 4 degrees along +y
scene = bpy.context.scene
report = {'times_seconds': {}}

road = bpy.data.objects['street_setts']
material = bpy.data.materials['street_setts']

# ---- the close camera (the same as 03_wet_street_test.py "close_road")
data = bpy.data.cameras.new('close')
close = bpy.data.objects.new('close', data)
scene.collection.objects.link(close)
data.sensor_fit = 'VERTICAL'
data.angle_y = math.radians(38)
close.location = Vector((0.5, 6.0, 1.0))
close.rotation_euler = (Vector((0.0, 11.0, 0.45)) - close.location).to_track_quat('-Z', 'Y').to_euler()


def settings_for_pictures(width, height):
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 48
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = 0.03
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = 'OPENIMAGEDENOISE'
    scene.cycles.max_bounces = 6
    scene.cycles.glossy_bounces = 4
    scene.cycles.sample_clamp_indirect = 8.0
    scene.cycles.pixel_filter_type = 'BLACKMAN_HARRIS'
    scene.cycles.filter_width = 1.5
    scene.render.dither_intensity = 1.0
    scene.render.resolution_x, scene.render.resolution_y = width, height
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'


def draw(path):
    started = time.time()
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return round(time.time() - started, 1)


# ---- 1. the live wet road
lowness_tree = material.node_tree
geometry = lowness_tree.nodes.new('ShaderNodeNewGeometry')
split = lowness_tree.nodes.new('ShaderNodeSeparateXYZ')
lowness_tree.links.new(geometry.outputs['Position'], split.inputs[0])
absolute = lowness_tree.nodes.new('ShaderNodeMath'); absolute.operation = 'ABSOLUTE'
lowness_tree.links.new(split.outputs['X'], absolute.inputs[0])
ramp = lowness_tree.nodes.new('ShaderNodeMapRange'); ramp.interpolation_type = 'SMOOTHSTEP'
ramp.inputs['From Min'].default_value = 0.6; ramp.inputs['From Max'].default_value = 2.1
lowness_tree.links.new(absolute.outputs[0], ramp.inputs['Value'])
group_node = wg.add_wetness_to_material(
    material, {'wetness': 0.85, 'puddles': 0.55},
    rough_image=bpy.data.images.load(TEX + 'square_cobblestone_rough.jpg', check_existing=True),
    height_image=bpy.data.images.load(TEX + 'square_cobblestone_displacement.jpg', check_existing=True),
    lowness=ramp.outputs['Result'], porosity=0.6, seed=3.0)
scene.camera = close
settings_for_pictures(480, 360)
report['times_seconds']['live_close'] = draw(os.path.join(out_folder, 'close_live.png'))
print('DRAWN live', report['times_seconds']['live_close'])

# ---- 2. photograph the group's outputs from above
originally_hidden = {obj.name: obj.hide_render for obj in scene.objects}
for obj in scene.objects:
    obj.hide_render = obj.name != 'street_setts'
cam_data = bpy.data.cameras.new('overhead')
cam_data.type = 'ORTHO'
cam_data.ortho_scale = Y1 - Y0
cam_data.clip_start, cam_data.clip_end = 0.1, 200.0
overhead = bpy.data.objects.new('overhead', cam_data)
scene.collection.objects.link(overhead)
overhead.location = (0.0, (Y0 + Y1) / 2, 60.0)
overhead.rotation_euler = (0, 0, 0)
scene.camera = overhead
width, height = int(2 * X_HALF * PIXELS_PER_METRE), int((Y1 - Y0) * PIXELS_PER_METRE)
scene.render.resolution_x, scene.render.resolution_y = width, height
scene.cycles.samples = 1
scene.cycles.use_adaptive_sampling = False
scene.cycles.use_denoising = False
scene.cycles.pixel_filter_type = 'BOX'
scene.cycles.filter_width = 1.0
scene.render.dither_intensity = 0.0
scene.view_settings.look = 'None'
scene.view_settings.exposure = 0.0
scene.view_settings.gamma = 1.0
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.0
tree = material.node_tree
output = next(n for n in tree.nodes if n.type == 'OUTPUT_MATERIAL')
emission = tree.nodes.new('ShaderNodeEmission')
tree.links.new(emission.outputs['Emission'], output.inputs['Surface'])


def show(socket_name, grey=True, scale=1.0, offset=0.0):
    """Wire one output of the group into the emission, as plain light (grey: the same value in red, green and blue)."""
    combine = tree.nodes.new('ShaderNodeCombineColor')
    source = group_node.outputs[socket_name]
    if scale != 1.0 or offset != 0.0:
        math_node = tree.nodes.new('ShaderNodeMath'); math_node.operation = 'MULTIPLY_ADD'
        tree.links.new(source, math_node.inputs[0]); math_node.inputs[1].default_value = scale; math_node.inputs[2].default_value = offset
        source = math_node.outputs[0]
    for channel in ('Red', 'Green', 'Blue'):
        tree.links.new(source, combine.inputs[channel])
    tree.links.new(combine.outputs['Color'], emission.inputs['Color'])


def photograph(name, linear):
    scene.view_settings.view_transform = 'Raw' if linear else 'Standard'
    report['times_seconds'][name] = draw(os.path.join(out_folder, f'{name}.png'))
    print('PHOTOGRAPHED', name, report['times_seconds'][name])


# wet colour: the group's colour output straight into the emission (sRGB picture)
tree.links.new(group_node.outputs['Colour'], emission.inputs['Color'])
photograph('wet_colour', linear=False)
show('Roughness'); photograph('wet_roughness', linear=True)
show('Coat Weight'); photograph('wet_coat', linear=True)
show('Coat Roughness'); photograph('wet_coat_roughness', linear=True)
show('Puddle Mask'); photograph('wet_puddle_mask', linear=True)
# the normal: turn the world normal into the road's own tangent frame (x across, y along the slope, z out of the road), then 0..1
separate = tree.nodes.new('ShaderNodeSeparateXYZ')
tree.links.new(group_node.outputs['Normal'], separate.inputs[0])
def maths(operation, a, b, c=None):
    node = tree.nodes.new('ShaderNodeMath'); node.operation = operation
    for index, value in enumerate((a, b, c)):
        if value is None: continue
        if isinstance(value, bpy.types.NodeSocket): tree.links.new(value, node.inputs[index])
        else: node.inputs[index].default_value = value
    return node.outputs[0]
tx = separate.outputs['X']
ty = maths('ADD', maths('MULTIPLY', separate.outputs['Y'], math.cos(SLOPE)), maths('MULTIPLY', separate.outputs['Z'], math.sin(SLOPE)))
tz = maths('ADD', maths('MULTIPLY', separate.outputs['Y'], -math.sin(SLOPE)), maths('MULTIPLY', separate.outputs['Z'], math.cos(SLOPE)))
combine = tree.nodes.new('ShaderNodeCombineColor')
for channel, value in (('Red', tx), ('Green', ty), ('Blue', tz)):
    tree.links.new(maths('MULTIPLY_ADD', value, 0.5, 0.5), combine.inputs[channel])
tree.links.new(combine.outputs['Color'], emission.inputs['Color'])
photograph('wet_normal', linear=True)

# ---- 3. the second set of texture coordinates and the plain material that wears only the pictures
mesh = road.data
uv2 = mesh.uv_layers.new(name='UV2')
for polygon in mesh.polygons:
    for loop_index in polygon.loop_indices:
        co = mesh.vertices[mesh.loops[loop_index].vertex_index].co
        uv2.data[loop_index].uv = ((co.x + X_HALF) / (2 * X_HALF), (co.y - Y0) / (Y1 - Y0))
baked = bpy.data.materials.new('road_wet_baked')
baked.use_nodes = True
bt = baked.node_tree
principled = next(n for n in bt.nodes if n.type == 'BSDF_PRINCIPLED')
uv_node = bt.nodes.new('ShaderNodeUVMap'); uv_node.uv_map = 'UV2'


def picture(name, colour):
    node = bt.nodes.new('ShaderNodeTexImage')
    node.image = bpy.data.images.load(os.path.join(out_folder, f'{name}.png'))
    node.image.colorspace_settings.name = 'sRGB' if colour else 'Non-Color'
    node.extension = 'EXTEND'
    bt.links.new(uv_node.outputs['UV'], node.inputs['Vector'])
    return node


bt.links.new(picture('wet_colour', True).outputs['Color'], principled.inputs['Base Color'])
bt.links.new(picture('wet_roughness', False).outputs['Color'], principled.inputs['Roughness'])
bt.links.new(picture('wet_coat', False).outputs['Color'], principled.inputs['Coat Weight'])
bt.links.new(picture('wet_coat_roughness', False).outputs['Color'], principled.inputs['Coat Roughness'])
normal_map = bt.nodes.new('ShaderNodeNormalMap'); normal_map.uv_map = 'UV2'
bt.links.new(picture('wet_normal', False).outputs['Color'], normal_map.inputs['Color'])
bt.links.new(normal_map.outputs['Normal'], principled.inputs['Normal'])
principled.inputs['Coat IOR'].default_value = 1.33
principled.inputs['Specular IOR Level'].default_value = 0.5     # glTF cannot go above the normal specular with a picture (see the study); the film is the coat
road.data.materials[0] = baked

# ---- 4. draw the close view again with the baked road, then write the .glb of the road alone
for obj in scene.objects:
    obj.hide_render = originally_hidden.get(obj.name, False)
settings_for_pictures(480, 360)
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - Medium High Contrast'
scene.view_settings.exposure = 0.6
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 1.4
scene.camera = close
report['times_seconds']['baked_close'] = draw(os.path.join(out_folder, 'close_baked.png'))
print('DRAWN baked', report['times_seconds']['baked_close'])
bpy.ops.object.select_all(action='DESELECT')
road.select_set(True)
bpy.context.view_layer.objects.active = road
glb_path = os.path.join(out_folder, 'road_wet_test.glb')
bpy.ops.export_scene.gltf(filepath=glb_path, export_format='GLB', use_selection=True, export_yup=True, export_apply=True, export_cameras=False, export_lights=False,
                          export_materials='EXPORT', export_image_format='AUTO')
report['glb_bytes'] = os.path.getsize(glb_path)
report['picture_size'] = [width, height]
with open(os.path.join(out_folder, 'bake_report.json'), 'w') as handle:
    json.dump(report, handle, indent=1)
print('REPORT', report)
