# What this does: experiment 2a. It answers four "does the number I save equal the number I meant?" questions about getting texture data out of Blender:
#   Q1  Which way of saving a float picture (image.save, image.save_render with the Standard, Raw or AgX view transform) keeps a data value of 0.5 as 0.5?
#       And what do the image's own colour-space setting (sRGB or Non-Color) and the picture's file bit depth change?
#   Q2  When a flat square is photographed with an emission shader, which view transform returns the exact input value (a smooth 0..1 ramp) in an 8-bit
#       and in a 16-bit PNG?  (Standard / Raw / AgX / Filmic)
#   Q3  Is a "16-bit" PNG from Blender really 16-bit, and how many different grey levels does an 8-bit versus a 16-bit height map hold?
#   Q4  How does the pixel filter (default Blackman-Harris 1.5 px versus Box 1.0 px) change a hard edge?
# Output: out/colour_space/*.png and out/colour_space/results.json
# Run:  blender -b --disable-autoexec -t 2 --python exp2a_colour_space_and_bit_depth.py
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import exp_common as ec  # noqa: E402

import bpy  # noqa: E402
import numpy as np  # noqa: E402

bh, rt = ec.bh, ec.rt
folder = os.path.join(ec.OUT, 'colour_space')
os.makedirs(folder, exist_ok=True)
results = {}


def read_png_values(path):
    """Read a PNG back as raw numbers 0..1 with no colour conversion (Non-Color), as the first pixel row's mean for each channel."""
    image = bpy.data.images.load(path, check_existing=False)
    image.colorspace_settings.name = 'Non-Color'
    w, h = image.size
    pixels = np.empty(w * h * 4, dtype=np.float32)
    image.pixels.foreach_get(pixels)
    array = pixels.reshape(h, w, 4)
    bpy.data.images.remove(image)
    return array[..., :3]


scene, tile = bh.new_bake_scene(64)

# ---------------------------------------------------------------------------------- Q1 saving a float picture with a data value 0.5
q1 = {}
for space in ('sRGB', 'Non-Color'):
    for depth in ('8', '16'):
        for how in ('save', 'save_render_standard', 'save_render_raw', 'save_render_agx'):
            image = bpy.data.images.new('q1', 16, 16, alpha=False, float_buffer=True)
            image.colorspace_settings.name = space
            image.pixels.foreach_set(np.full(16 * 16 * 4, 0.5, dtype=np.float32))
            path = os.path.join(folder, f'q1_{space}_{depth}bit_{how}.png')
            settings = scene.render.image_settings
            settings.file_format, settings.color_mode, settings.color_depth = 'PNG', 'RGB', depth
            if how == 'save':
                image.filepath_raw = path
                image.file_format = 'PNG'
                image.save()
            else:
                scene.view_settings.view_transform = {'save_render_standard': 'Standard', 'save_render_raw': 'Raw', 'save_render_agx': 'AgX'}[how]
                image.save_render(path, scene=scene)
            bpy.data.images.remove(image)
            value = float(read_png_values(path)[0, 0, 0])
            q1[f'{space} | {depth}-bit | {how}'] = round(value, 4)
results['Q1_saved_value_for_data_0.5'] = q1

# ---------------------------------------------------------------------------------- Q2 photographing a ramp with different view transforms
def ramp_group():
    tree, w = rt.make_group_tree('ramp', [('Vector', 'NodeSocketVector', (0, 0, 0))], [('Height', 'NodeSocketFloat')])
    w.add('ShaderNodeSeparateXYZ', 'sep')
    w.link('in', 'Vector', 'sep', 'Vector')
    w.link('sep', 'X', 'out', 'Height')
    return tree


q2 = {}
group = ramp_group()
material = bh.show_channel_material(group, 'Height')
tile.data.materials.clear()
tile.data.materials.append(material)
scene.render.resolution_x = scene.render.resolution_y = 256
for transform in ('Standard', 'Raw', 'AgX', 'Filmic'):
    for depth in ('8', '16'):
        try:
            scene.view_settings.view_transform = transform
        except TypeError as error:
            q2[f'{transform} {depth}-bit'] = 'not available: ' + str(error)[:60]
            continue
        scene.render.image_settings.file_format = 'PNG'
        scene.render.image_settings.color_mode = 'RGB'
        scene.render.image_settings.color_depth = depth
        path = os.path.join(folder, f'q2_ramp_{transform}_{depth}bit.png')
        scene.render.filepath = path
        bpy.ops.render.render(write_still=True)
        values = read_png_values(path)[128, :, 0]
        expected = (np.arange(256) + 0.5) / 256.0
        q2[f'{transform} {depth}-bit'] = {'max_error_vs_input': round(float(np.abs(values - expected).max()), 4),
                                         'value_at_u_0.5': round(float(values[127:129].mean()), 4)}
results['Q2_photographed_ramp_error'] = q2
# the default view transform of a brand new scene (what you get if you do not set it yourself)
fresh = bpy.data.scenes.new('fresh')
results['Q2_default_view_transform_of_a_new_scene'] = fresh.view_settings.view_transform
results['Q2_default_look_of_a_new_scene'] = fresh.view_settings.look
results['Q2_default_pixel_filter_of_a_new_scene'] = [fresh.cycles.pixel_filter_type, fresh.cycles.filter_width]
bpy.data.scenes.remove(fresh)

# ---------------------------------------------------------------------------------- Q3 gentle height ramp 0.40 .. 0.60 in 8 and 16 bit (counted later by analyse_pngs)
def gentle_ramp_group():
    tree, w = rt.make_group_tree('gentle', [('Vector', 'NodeSocketVector', (0, 0, 0))], [('Height', 'NodeSocketFloat')])
    w.add('ShaderNodeSeparateXYZ', 'sep')
    w.link('in', 'Vector', 'sep', 'Vector')
    w.math('scale', 'MULTIPLY_ADD', None, 0.2)
    w.nodes['scale'].inputs[2].default_value = 0.4
    w.link('sep', 'X', 'scale', 0)
    w.link('scale', 0, 'out', 'Height')
    return tree


scene.render.resolution_x = scene.render.resolution_y = 512
material = bh.show_channel_material(gentle_ramp_group(), 'Height')
tile.data.materials.clear()
tile.data.materials.append(material)
for depth in ('8', '16'):
    bh.render_to(scene, os.path.join(folder, f'q3_gentle_ramp_{depth}bit.png'), True, depth == '16')

# ---------------------------------------------------------------------------------- Q4 a hard diagonal edge with different pixel filters and sample counts
def edge_group():
    tree, w = rt.make_group_tree('edge', [('Vector', 'NodeSocketVector', (0, 0, 0))], [('Height', 'NodeSocketFloat')])
    w.add('ShaderNodeSeparateXYZ', 'sep')
    w.link('in', 'Vector', 'sep', 'Vector')
    w.math('sum', 'ADD')
    w.link('sep', 'X', 'sum', 0)
    w.link('sep', 'Y', 'sum', 1)
    w.math('cut', 'GREATER_THAN', None, 1.0)
    w.link('sum', 0, 'cut', 0)
    w.link('cut', 0, 'out', 'Height')
    return tree


scene.render.resolution_x = scene.render.resolution_y = 64
material = bh.show_channel_material(edge_group(), 'Height')
tile.data.materials.clear()
tile.data.materials.append(material)
cases = [('blackmanharris1p5_s4', 'BLACKMAN_HARRIS', 1.5, 4), ('box1p0_s1', 'BOX', 1.0, 1), ('box1p0_s4', 'BOX', 1.0, 4), ('box1p0_s16', 'BOX', 1.0, 16),
         ('box1p0_s64', 'BOX', 1.0, 64), ('gaussian1p5_s64', 'GAUSSIAN', 1.5, 64)]
for name, kind, width, samples in cases:
    scene.cycles.pixel_filter_type = kind
    scene.cycles.filter_width = width
    scene.cycles.samples = samples
    bh.render_to(scene, os.path.join(folder, f'q4_edge_{name}.png'), True, True)
with open(os.path.join(folder, 'results.json'), 'w') as handle:
    json.dump(results, handle, indent=1)
print(json.dumps(results, indent=1))
