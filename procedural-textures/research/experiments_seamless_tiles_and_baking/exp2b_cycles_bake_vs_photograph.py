# What this does: experiment 2b. It compares the two ways of turning a procedural material into pictures:
#   ROUTE A "photograph"   an emission shader shows one channel and a flat orthographic camera renders it (what lib/bake_harness.py does)
#   ROUTE B "Cycles Bake"  Blender's own Bake button (bpy.ops.object.bake) writing into an Image Texture node's picture
# on one test material (a Principled BSDF with tileable noise for colour, roughness, metallic and a Bump node) and answers:
#   Q1  Does Bake > Diffuse (colour only) give the base colour? (and what happens where the surface is metallic?)
#   Q2  Does the "emission trick" (colour into an Emission shader, bake Emit) fix it, and does it equal the photograph?
#   Q3  Does Bake > Roughness give the roughness?   Q4 Does Bake > Normal give the same normal map as the photographed Bump node?
#   Q5  What does Bake > Ambient Occlusion give on a flat square with only a Bump node?
#   Q6  How does the image's colour space (sRGB versus Non-Color) and byte versus float buffer change what a bake writes?
#   Q7  How does the sample count / pixel filter change a hard edge in a bake?   Q8 What does Margin do when the UV island does not fill the picture?
# Output: out/bake/*.png and out/bake/results.json (numbers are errors against the photographed picture, 0..1 scale)
# Run:  blender -b --disable-autoexec -t 2 --python exp2b_cycles_bake_vs_photograph.py -- [size]
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import exp_common as ec  # noqa: E402

import bpy  # noqa: E402
import numpy as np  # noqa: E402

bh, rt = ec.bh, ec.rt
SIZE = int(sys.argv[sys.argv.index('--') + 1]) if '--' in sys.argv and len(sys.argv) > sys.argv.index('--') + 1 else 256
folder = os.path.join(ec.OUT, 'bake')
os.makedirs(folder, exist_ok=True)
results = {'size': SIZE}


# ---------------------------------------------------------------------------------- the test recipe
def build_recipe():
    tree, w = rt.make_group_tree('bake test recipe', [('Vector', 'NodeSocketVector', (0, 0, 0))],
                                 [('Colour', 'NodeSocketColor'), ('Roughness', 'NodeSocketFloat'), ('Metallic', 'NodeSocketFloat'), ('Height', 'NodeSocketFloat')])
    tn = rt.tileable_noise_group()

    def noise(name, scale, detail, seed):
        node = w.add('ShaderNodeGroup', name)
        node.node_tree = tn
        w.link('in', 'Vector', name, 'Vector')
        node.inputs['Scale'].default_value = scale
        node.inputs['Detail'].default_value = detail
        node.inputs['Seed'].default_value = seed
        return name

    noise('height noise', 6.0, 5.0, 0.0)
    noise('colour noise', 4.0, 3.0, 11.0)
    noise('rough noise', 5.0, 3.0, 23.0)
    noise('metal noise', 3.0, 1.0, 37.0)
    w.add('ShaderNodeValToRGB', 'colour ramp')
    ramp = w.nodes['colour ramp'].color_ramp
    ramp.elements[0].position, ramp.elements[0].color = 0.35, (0.55, 0.12, 0.05, 1.0)
    ramp.elements[1].position, ramp.elements[1].color = 0.65, (0.15, 0.30, 0.75, 1.0)
    w.link('colour noise', 'Fac', 'colour ramp', 'Fac')
    w.link('colour ramp', 'Color', 'out', 'Colour')
    w.math('rough map', 'MULTIPLY_ADD', None, 0.6)
    w.nodes['rough map'].inputs[2].default_value = 0.2
    w.link('rough noise', 'Fac', 'rough map', 0)
    w.link('rough map', 0, 'out', 'Roughness')
    w.math('metal cut', 'GREATER_THAN', None, 0.5)       # 0 or 1: metal where the noise is above one half
    w.link('metal noise', 'Fac', 'metal cut', 0)
    w.link('metal cut', 0, 'out', 'Metallic')
    w.link('height noise', 'Fac', 'out', 'Height')
    return tree


def principled_material(group, bump_distance=0.02):
    material = bpy.data.materials.new('principled test')
    material.use_nodes = True
    tree = material.node_tree
    tree.nodes.clear()
    w = rt.NodeWriter(tree)
    w.add('ShaderNodeTexCoord', 'coords', x=0)
    w.add('ShaderNodeGroup', 'recipe', x=1)
    w.nodes['recipe'].node_tree = group
    w.link('coords', 'UV', 'recipe', 'Vector')
    w.add('ShaderNodeBump', 'bump', x=2, Strength=1.0, Distance=bump_distance)
    w.link('recipe', 'Height', 'bump', 'Height')
    w.add('ShaderNodeBsdfPrincipled', 'bsdf', x=3)
    w.link('recipe', 'Colour', 'bsdf', 'Base Color')
    w.link('recipe', 'Roughness', 'bsdf', 'Roughness')
    w.link('recipe', 'Metallic', 'bsdf', 'Metallic')
    w.link('bump', 'Normal', 'bsdf', 'Normal')
    w.add('ShaderNodeOutputMaterial', 'output', x=4)
    w.link('bsdf', 'BSDF', 'output', 'Surface')
    return material


def emission_material(group, channel):
    """The same recipe as an Emission shader showing one channel (used for the emission trick and the photograph route)."""
    return bh.show_channel_material(group, channel)


# ---------------------------------------------------------------------------------- bake helpers
def new_target(name, size, space, float_buffer):
    image = bpy.data.images.new(name, size, size, alpha=False, float_buffer=float_buffer)
    image.colorspace_settings.name = space
    return image


def bake(scene, tile, material, bake_type, image, **options):
    """Bakes `bake_type` of `material` into `image` (through an Image Texture node that is made the active node)."""
    tile.data.materials.clear()
    tile.data.materials.append(material)
    tree = material.node_tree
    node = tree.nodes.new('ShaderNodeTexImage')
    node.image = image
    for other in tree.nodes:
        other.select = False
    node.select = True
    tree.nodes.active = node
    bpy.context.view_layer.objects.active = tile
    tile.select_set(True)
    scene.cycles.bake_type = bake_type
    bake_settings = scene.render.bake
    bake_settings.use_pass_direct = False
    bake_settings.use_pass_indirect = False
    bake_settings.use_pass_color = True
    bake_settings.use_pass_emit = False
    bpy.ops.object.bake(type=bake_type, use_clear=True, **options)
    tree.nodes.remove(node)


def image_to_array(image):
    w, h = image.size
    pixels = np.empty(w * h * 4, dtype=np.float32)
    image.pixels.foreach_get(pixels)
    return pixels.reshape(h, w, 4)[::-1, :, :3].astype(np.float64)       # rows top to bottom


def save_data_png(array, path, bits=16):
    bh.save_array_png(np.clip(array, 0, 1), path, sixteen_bit=(bits == 16))


def photograph(scene, tile, group, channel, path, samples=16):
    scene.cycles.samples = samples
    tile.data.materials.clear()
    tile.data.materials.append(emission_material(group, channel))
    linear = channel != 'Colour'
    bh.render_to(scene, path, linear, sixteen_bit=linear)
    return bh.load_png_as_array(path) if linear else bh.load_png_as_array(path)     # raw numbers back (sRGB encoded for colour)


def srgb_encode(linear):
    return np.where(linear <= 0.0031308, linear * 12.92, 1.055 * np.power(np.maximum(linear, 0), 1 / 2.4) - 0.055)


scene, tile = bh.new_bake_scene(SIZE)
group = build_recipe()
scene.cycles.samples = 16
photo = {}
for channel in ('Colour', 'Roughness', 'Metallic', 'Height'):
    photo[channel] = photograph(scene, tile, group, channel, os.path.join(folder, f'photo_{channel.lower()}.png'))
principled = principled_material(group, bump_distance=0.02)

# ---------------------------------------------------------------------------------- Q1 / Q2 base colour: Diffuse versus the emission trick
metal_fraction = float((photo['Metallic'][..., 0] > 0.5).mean())
results['metal_fraction_of_the_surface'] = round(metal_fraction, 3)
scene.cycles.samples = 16
image = new_target('diffuse_srgb_byte', SIZE, 'sRGB', False)
bake(scene, tile, principled, 'DIFFUSE', image)
diffuse = image_to_array(image)
metal_mask = photo['Metallic'][..., 0] > 0.5
results['Q1_diffuse_bake'] = {
    'mean_error_vs_photograph_where_NOT_metal': round(float(np.abs(diffuse - photo['Colour'])[~metal_mask].mean()), 4),
    'mean_brightness_of_the_bake_where_metal': round(float(diffuse[metal_mask].mean()), 4),
    'mean_brightness_of_the_photograph_where_metal': round(float(photo['Colour'][metal_mask].mean()), 4)}
save_data_png(diffuse, os.path.join(folder, 'bake_diffuse_color_only.png'), 8)

emit_colour_material = emission_material(group, 'Colour')
image = new_target('emit_colour_srgb_byte', SIZE, 'sRGB', False)
bake(scene, tile, emit_colour_material, 'EMIT', image)
emit_colour = image_to_array(image)
results['Q2_emit_trick_colour'] = {'mean_error_vs_photograph': round(float(np.abs(emit_colour - photo['Colour']).mean()), 4),
                                    'max_error_vs_photograph': round(float(np.abs(emit_colour - photo['Colour']).max()), 4)}
save_data_png(emit_colour, os.path.join(folder, 'bake_emit_colour.png'), 8)

# ---------------------------------------------------------------------------------- Q3 roughness
rough_image = new_target('rough_nc_float', SIZE, 'Non-Color', True)
bake(scene, tile, principled, 'ROUGHNESS', rough_image)
rough_bake = image_to_array(rough_image)
results['Q3_roughness_bake'] = {'mean_error_vs_photograph': round(float(np.abs(rough_bake[..., 0] - photo['Roughness'][..., 0]).mean()), 5)}
save_data_png(rough_bake, os.path.join(folder, 'bake_roughness.png'), 16)

# ---------------------------------------------------------------------------------- Q4 normal
normal_image = new_target('normal_nc_float', SIZE, 'Non-Color', True)
bake(scene, tile, principled, 'NORMAL', normal_image)
normal_bake = image_to_array(normal_image)
save_data_png(normal_bake, os.path.join(folder, 'bake_normal.png'), 16)
bump_distance = 0.02
bump_material = bh.show_channel_material(group, 'NormalBump', normal_distance=bump_distance)
tile.data.materials.clear()
tile.data.materials.append(bump_material)
scene.cycles.samples = 16
bh.render_to(scene, os.path.join(folder, 'photo_normal_bumpnode.png'), True, True)
normal_photo = bh.load_png_as_array(os.path.join(folder, 'photo_normal_bumpnode.png'))
height = photo['Height'][..., 0]
sobel = bh.sobel_normal(height, bump_distance * SIZE) * 0.5 + 0.5
results['Q4_normal'] = {
    'cycles_bake_vs_bump_node_photograph_mean_abs_error': round(float(np.abs(normal_bake - normal_photo).mean()), 5),
    'cycles_bake_vs_numpy_sobel_mean_abs_error': round(float(np.abs(normal_bake - sobel).mean()), 5),
    'bump_node_photograph_vs_numpy_sobel_mean_abs_error': round(float(np.abs(normal_photo - sobel).mean()), 5),
    'bake_green_mean': round(float(normal_bake[..., 1].mean()), 4), 'bake_blue_mean': round(float(normal_bake[..., 2].mean()), 4),
}
# how the bump node's strength relates to a Sobel strength: fit s in  n = normalize(-s * grad(height), 1)  to the baked normal
def fit_strength(normal_map, height):
    lo, hi = 0.01, 500.0
    for _ in range(40):
        mid = math.sqrt(lo * hi)
        candidate = bh.sobel_normal(height, mid) * 0.5 + 0.5
        error = np.abs(candidate[..., :2] - normal_map[..., :2]).mean()
        candidate_hi = bh.sobel_normal(height, mid * 1.05) * 0.5 + 0.5
        error_hi = np.abs(candidate_hi[..., :2] - normal_map[..., :2]).mean()
        if error_hi < error:
            lo = mid
        else:
            hi = mid
    return math.sqrt(lo * hi)


results['Q4_normal']['sobel_strength_that_matches_the_cycles_bake'] = round(fit_strength(normal_bake, height), 2)
results['Q4_normal']['predicted_by_distance_times_size'] = round(bump_distance * SIZE, 2)

# ---------------------------------------------------------------------------------- Q5 ambient occlusion on a flat square with only a bump node
ao_image = new_target('ao_nc_float', SIZE, 'Non-Color', True)
scene.cycles.samples = 16
bake(scene, tile, principled, 'AO', ao_image)
ao = image_to_array(ao_image)
results['Q5_ao_of_flat_square_with_bump'] = {'min': round(float(ao.min()), 4), 'max': round(float(ao.max()), 4), 'mean': round(float(ao.mean()), 4)}

# ---------------------------------------------------------------------------------- Q6 colour space and buffer type of the target picture
q6 = {}
for buffer_name, is_float in (('byte', False), ('float', True)):
    for space in ('sRGB', 'Non-Color'):
        image = new_target(f'rough_{buffer_name}_{space}', SIZE, space, is_float)
        bake(scene, tile, principled, 'ROUGHNESS', image)
        in_memory = image_to_array(image)[..., 0]
        path = os.path.join(folder, f'q6_roughness_{buffer_name}_{space.lower()}.png')
        image.filepath_raw = path
        image.file_format = 'PNG'
        scene.render.image_settings.color_depth = '16'
        image.save()
        saved = bh.load_png_as_array(path)[..., 0]
        truth = photo['Roughness'][..., 0]
        q6[f'{buffer_name} buffer, {space}'] = {'roughness_in_memory_error': round(float(np.abs(in_memory - truth).mean()), 4),
                                               'saved_png_error': round(float(np.abs(saved - truth).mean()), 4),
                                               'mean_in_memory': round(float(in_memory.mean()), 4), 'mean_truth': round(float(truth.mean()), 4)}
    for space in ('sRGB',):
        image = new_target(f'colour_{buffer_name}_{space}', SIZE, space, is_float)
        bake(scene, tile, emit_colour_material, 'EMIT', image)
        in_memory = image_to_array(image)
        path = os.path.join(folder, f'q6_colour_{buffer_name}_{space.lower()}.png')
        image.filepath_raw = path
        image.file_format = 'PNG'
        image.save()
        saved = bh.load_png_as_array(path)
        q6[f'COLOUR {buffer_name} buffer, {space}'] = {'in_memory_error': round(float(np.abs(in_memory - photo['Colour']).mean()), 4),
                                                       'saved_png_error': round(float(np.abs(saved - photo['Colour']).mean()), 4)}
        image = new_target(f'colour_{buffer_name}_nc', SIZE, 'Non-Color', is_float)
        bake(scene, tile, emit_colour_material, 'EMIT', image)
        path = os.path.join(folder, f'q6_colour_{buffer_name}_non-color.png')
        image.filepath_raw = path
        image.file_format = 'PNG'
        image.save()
        saved = bh.load_png_as_array(path)
        q6[f'COLOUR {buffer_name} buffer, Non-Color'] = {'saved_png_error': round(float(np.abs(saved - photo['Colour']).mean()), 4)}
results['Q6_colour_space_of_the_target_picture'] = q6

# ---------------------------------------------------------------------------------- Q7 hard edge: samples and pixel filter in a bake
def edge_group():
    tree, w = rt.make_group_tree('edge', [('Vector', 'NodeSocketVector', (0, 0, 0))], [('Colour', 'NodeSocketColor'), ('Height', 'NodeSocketFloat')])
    w.add('ShaderNodeSeparateXYZ', 'sep')
    w.link('in', 'Vector', 'sep', 'Vector')
    w.math('sum', 'ADD')
    w.link('sep', 'X', 'sum', 0)
    w.link('sep', 'Y', 'sum', 1)
    w.math('cut', 'GREATER_THAN', None, 1.0)
    w.link('sum', 0, 'cut', 0)
    w.link('cut', 0, 'out', 'Height')
    w.add('ShaderNodeCombineColor', 'col')
    for socket in ('Red', 'Green', 'Blue'):
        w.link('cut', 0, 'col', socket)
    w.link('col', 'Color', 'out', 'Colour')
    return tree


N_EDGE = 64
scene_e, tile_e = bh.new_bake_scene(N_EDGE)
edge = edge_group()
edge_material = bh.show_channel_material(edge, 'Height')
sub = 32
coordinate = (np.arange(N_EDGE * sub) + 0.5) / (N_EDGE * sub)
exact = (((coordinate[None, :] + coordinate[::-1][:, None]) > 1.0).astype(np.float64)).reshape(N_EDGE, sub, N_EDGE, sub).mean(axis=(1, 3))
edge_px = (exact > 0) & (exact < 1)
q7 = {}
for label, kind, width, samples in (('box1_s1', 'BOX', 1.0, 1), ('box1_s4', 'BOX', 1.0, 4), ('box1_s16', 'BOX', 1.0, 16), ('box1_s64', 'BOX', 1.0, 64),
                                    ('blackmanharris1p5_s16', 'BLACKMAN_HARRIS', 1.5, 16)):
    scene_e.cycles.pixel_filter_type = kind
    scene_e.cycles.filter_width = width
    scene_e.cycles.samples = samples
    image = new_target('edge', N_EDGE, 'Non-Color', True)
    bake(scene_e, tile_e, edge_material, 'EMIT', image)
    value = image_to_array(image)[..., 0]
    q7[label] = {'mean_error_on_edge_pixels': round(float(np.abs(value - exact)[edge_px].mean()), 4),
                 'pixels_changed_away_from_edge': int(((np.abs(value - exact) > 0.01) & ~edge_px).sum())}
results['Q7_bake_hard_edge_vs_exact_coverage'] = q7

# ---------------------------------------------------------------------------------- Q8 margin when the UV island does not fill the picture
scene_m, tile_m = bh.new_bake_scene(SIZE)
group_m = build_recipe()
uv = tile_m.data.uv_layers['UVMap']
for loop, (u, v) in zip(tile_m.data.loops, [(0.25, 0.25), (0.75, 0.25), (0.75, 0.75), (0.25, 0.75)]):
    uv.data[loop.index].uv = (u, v)
emit_m = emission_material(group_m, 'Colour')
scene_m.cycles.samples = 4
q8 = {}
for margin, kind in ((0, 'EXTEND'), (8, 'EXTEND'), (32, 'EXTEND'), (8, 'ADJACENT_FACES')):
    image = new_target('margin', SIZE, 'sRGB', False)
    bake(scene_m, tile_m, emit_m, 'EMIT', image, margin=margin, margin_type=kind)
    array = image_to_array(image)
    filled = (array.sum(axis=-1) > 0)
    inner = SIZE // 4
    q8[f'margin {margin} {kind}'] = {'filled_pixels_percent': round(float(filled.mean()) * 100, 1),
                                    'island_only_percent': 25.0, 'first_filled_column_from_left': int(np.argmax(filled[SIZE // 2, :]))}
    save_data_png(array, os.path.join(folder, f'q8_margin_{margin}_{kind.lower()}.png'), 8)
results['Q8_margin_with_island_covering_the_middle_half'] = q8

with open(os.path.join(folder, 'results.json'), 'w') as handle:
    json.dump(results, handle, indent=1)
print(json.dumps(results, indent=1))
