# What this does: turns a procedural material recipe into flat texture pictures (colour, height, roughness, metallic, normal) that can be
# compared with the reference pictures and used anywhere. It "photographs" a flat 1 x 1 square from straight above with a
# 1 x 1 sized camera, once per picture, using a shader that shows exactly one channel of the recipe, so every pixel is exact data.
# Normal maps come two ways: from the height with Blender's own Bump node (normal_bumpnode.png) and from the height with a Sobel
# filter in numpy (normal.png), whose strength can be fitted to a reference normal map.
# A recipe is a Python file with:  build_node_group(parameters) -> a shader node group whose input 'Vector' is the tile
# coordinate (0..1 in u and v) and whose outputs are 'Colour' (colour), 'Roughness', 'Metallic', 'Height' (0..1, 0.5 = flat)
# Use (inside Blender):  import bake_harness as bh ;  bh.bake_recipe(recipe_module, parameters, out_folder, size=1254)
#   or from the command line:
#   blender -b --python bake_harness.py -- RECIPE_FILE.py OUT_FOLDER [--size 1254] [--params '{"seed": 3}'] [--normal-reference REFERENCE_NAME]
import importlib.util
import json
import math
import os
import sys
import time

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import recipe_tools as rt  # noqa: E402

REFERENCE_FOLDER = os.path.join(os.path.dirname(HERE), 'reference')


# ----------------------------------------------------------------------------------------------------- scene
def new_bake_scene(size):
    """Empty scene with a flat 1 x 1 square (u = x, v = y), a straight-down 1 x 1 camera, and plain data-friendly render settings."""
    bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 4
    scene.cycles.use_adaptive_sampling = False
    scene.cycles.use_denoising = False
    scene.cycles.max_bounces = 0
    scene.cycles.pixel_filter_type = 'BOX'
    scene.cycles.filter_width = 1.0
    scene.render.resolution_x = scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'None'
    scene.view_settings.exposure = 0.0
    scene.view_settings.gamma = 1.0
    scene.display_settings.display_device = 'sRGB'
    scene.sequencer_colorspace_settings.name = 'sRGB'
    world = bpy.data.worlds.new('black')
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs['Color'].default_value = (0, 0, 0, 1)
    scene.world = world
    mesh = bpy.data.meshes.new('tile')
    mesh.from_pydata([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)], [], [(0, 1, 2, 3)])
    uv_layer = mesh.uv_layers.new(name='UVMap')
    for loop, uv in zip(mesh.loops, [(0, 0), (1, 0), (1, 1), (0, 1)]):
        uv_layer.data[loop.index].uv = uv
    tile = bpy.data.objects.new('tile', mesh)
    scene.collection.objects.link(tile)
    camera_data = bpy.data.cameras.new('overhead')
    camera_data.type = 'ORTHO'
    camera_data.ortho_scale = 1.0
    camera_data.clip_start = 0.01
    camera_data.clip_end = 100.0
    camera = bpy.data.objects.new('overhead', camera_data)
    camera.location = (0.5, 0.5, 5.0)
    scene.collection.objects.link(camera)
    scene.camera = camera
    return scene, tile


def load_recipe(path):
    spec = importlib.util.spec_from_file_location(os.path.splitext(os.path.basename(path))[0], path)
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, os.path.dirname(path))
    spec.loader.exec_module(module)
    return module


# ----------------------------------------------------------------------------------------------------- shading and rendering
def show_channel_material(group_tree, channel, normal_distance=None):
    """A material that shows one output of the recipe group as plain emitted light (no lighting at all).
    channel: 'Colour', 'Roughness', 'Metallic', 'Height', 'AO', or 'NormalBump' (the Bump-node normal made from Height)."""
    material = bpy.data.materials.new(f'show {channel}')
    material.use_nodes = True
    tree = material.node_tree
    tree.nodes.clear()
    writer = rt.NodeWriter(tree)
    writer.add('ShaderNodeTexCoord', 'coords', x=0)
    writer.add('ShaderNodeGroup', 'recipe', x=1)
    writer.nodes['recipe'].node_tree = group_tree
    writer.link('coords', 'UV', 'recipe', 'Vector')
    writer.add('ShaderNodeEmission', 'emit', x=4, Strength=1.0)
    writer.add('ShaderNodeOutputMaterial', 'output', x=5)
    writer.link('emit', 'Emission', 'output', 'Surface')
    if channel == 'NormalBump':
        writer.add('ShaderNodeBump', 'bump', x=2, invert=False, Strength=1.0, Distance=normal_distance or 0.02)
        writer.link('recipe', 'Height', 'bump', 'Height')
        writer.add('ShaderNodeVectorMath', 'half', x=3, operation='MULTIPLY_ADD')
        writer.nodes['half'].inputs[1].default_value = (0.5, 0.5, 0.5)
        writer.nodes['half'].inputs[2].default_value = (0.5, 0.5, 0.5)
        writer.link('bump', 'Normal', 'half', 0)
        writer.link('half', 0, 'emit', 'Color')
    elif channel == 'Colour':
        writer.link('recipe', 'Colour', 'emit', 'Color')
    else:
        writer.add('ShaderNodeCombineColor', 'grey', x=3)
        for socket in ('Red', 'Green', 'Blue'):
            writer.link('recipe', channel, 'grey', socket)
        writer.link('grey', 'Color', 'emit', 'Color')
    return material


def render_to(scene, path, linear_data, sixteen_bit=False):
    scene.view_settings.view_transform = 'Raw' if linear_data else 'Standard'
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.image_settings.color_depth = '16' if sixteen_bit else '8'
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def sobel_normal(height, strength):
    """Normal map (OpenGL: x to the right, y up the picture, z out) from a height picture; strength = how steep the slopes look."""
    hx = (np.roll(height, -1, axis=1) - np.roll(height, 1, axis=1)) / 2.0
    hy_down = (np.roll(height, -1, axis=0) - np.roll(height, 1, axis=0)) / 2.0   # per pixel step down the picture
    nx, ny, nz = -strength * hx, strength * hy_down, np.ones_like(height)      # up the picture = minus the downward slope
    length = np.sqrt(nx * nx + ny * ny + nz * nz)
    return np.stack([nx / length, ny / length, nz / length], axis=-1)


def load_png_as_array(path):
    image = bpy.data.images.load(path, check_existing=False)
    image.colorspace_settings.name = 'Non-Color'
    width, height = image.size
    pixels = np.empty(width * height * 4, dtype=np.float32)
    image.pixels.foreach_get(pixels)
    array = pixels.reshape(height, width, 4)[::-1]      # Blender stores rows bottom to top
    bpy.data.images.remove(image)
    return array[..., :3].astype(np.float64)


def save_array_png(array, path, sixteen_bit=False):
    """Write an array 0..1 (rows top to bottom) as PNG without any colour conversion."""
    height, width = array.shape[:2]
    channels = 1 if array.ndim == 2 else array.shape[2]
    rgba = np.ones((height, width, 4), dtype=np.float32)
    if channels >= 3:
        rgba[..., :3] = array[..., :3]
    else:                                   # a grey picture: the same value in red, green and blue
        grey = array if array.ndim == 2 else array[..., 0]
        rgba[..., :3] = grey[..., None]
    image = bpy.data.images.new('save', width, height, alpha=False, float_buffer=True)
    image.colorspace_settings.name = 'Non-Color'
    image.pixels.foreach_set(rgba[::-1].ravel())
    image.filepath_raw = path
    image.file_format = 'PNG'
    scene = bpy.context.scene
    settings = scene.render.image_settings
    settings.file_format, settings.color_mode, settings.color_depth = 'PNG', 'RGB', ('16' if sixteen_bit else '8')
    image.save_render(path, scene=scene)
    bpy.data.images.remove(image)


def reference_normal_slope_spread(reference_name):
    """Spread (standard deviation) of the x and y parts of the reference normal map, read in Blender."""
    normal = load_png_as_array(os.path.join(REFERENCE_FOLDER, reference_name, 'normal.png')) * 2.0 - 1.0
    return float(normal[..., 0].std()), float(normal[..., 1].std())


def fit_sobel_strength(height, target_spread):
    """Binary-search the strength so the Sobel normal map's spread of nx and ny matches target_spread (a pair)."""
    target = sum(target_spread) / 2.0
    low, high = 0.01, 400.0
    for _ in range(40):
        middle = math.sqrt(low * high)
        normal = sobel_normal(height, middle)
        spread = (normal[..., 0].std() + normal[..., 1].std()) / 2.0
        if spread < target:
            low = middle
        else:
            high = middle
    return math.sqrt(low * high)


# ----------------------------------------------------------------------------------------------------- the whole bake
def bake_recipe(recipe, parameters, out_folder, size=1254, normal_reference=None, bump_distance=None, quiet=False):
    """Bake colour.png, height.png (16-bit), roughness.png, metallic.png, normal.png and normal_bumpnode.png into out_folder."""
    os.makedirs(out_folder, exist_ok=True)
    started = time.time()
    scene, tile = new_bake_scene(size)
    group = recipe.build_node_group(dict(parameters or {}))
    results = {'size': size, 'parameters': parameters or {}}
    for channel, name, linear, sixteen in (('Colour', 'colour', False, False), ('Height', 'height', True, True),
                                           ('Roughness', 'roughness', True, False), ('Metallic', 'metallic', True, False)):
        if channel not in [s.name for s in group.interface.items_tree if s.item_type == 'SOCKET' and s.in_out == 'OUTPUT']:
            continue
        material = show_channel_material(group, channel)
        tile.data.materials.clear()
        tile.data.materials.append(material)
        render_to(scene, os.path.join(out_folder, name + '.png'), linear, sixteen)
    # the normal map from the height with Sobel, fitted to a reference's slope spread when one is named
    height = load_png_as_array(os.path.join(out_folder, 'height.png'))[..., 0]
    if normal_reference:
        strength = fit_sobel_strength(height, reference_normal_slope_spread(normal_reference))
    else:
        strength = 8.0
    results['sobel_strength'] = strength
    save_array_png(sobel_normal(height, strength) * 0.5 + 0.5, os.path.join(out_folder, 'normal.png'))
    # the same normal map the way a Blender material makes it (Bump node), for comparison
    bump_distance = bump_distance or max(strength / size, 1e-4)
    material = show_channel_material(group, 'NormalBump', normal_distance=bump_distance)
    tile.data.materials.clear()
    tile.data.materials.append(material)
    render_to(scene, os.path.join(out_folder, 'normal_bumpnode.png'), True, False)
    results['bump_node_distance'] = bump_distance
    results['seconds'] = round(time.time() - started, 1)
    with open(os.path.join(out_folder, 'bake.json'), 'w') as handle:
        json.dump(results, handle, indent=1)
    if not quiet:
        print('[bake]', json.dumps(results))
    return results


def main():
    arguments = sys.argv[sys.argv.index('--') + 1:]
    recipe_path, out_folder = arguments[0], arguments[1]
    option = lambda name, default=None: arguments[arguments.index(name) + 1] if name in arguments else default
    recipe = load_recipe(recipe_path)
    parameters = json.loads(option('--params', '{}'))
    bake_recipe(recipe, parameters, out_folder, size=int(option('--size', 1254)), normal_reference=option('--normal-reference'))


if __name__ == '__main__':
    main()
