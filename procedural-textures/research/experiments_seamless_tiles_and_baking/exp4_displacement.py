# What this does: experiment 4 on Cycles displacement, measured on real renders:
#   4a  What do Midlevel and Scale on the Displacement node mean? A step-shaped height is displaced and the top edge of the slab is measured from the side.
#       Also Space = Object versus World when the object is stretched.
#   4b  Displacement method Bump versus Displacement versus Both (default is Bump!) on a noisy surface seen at a low angle: how bumpy is the far edge?
#   4c  How fine must the mesh be? Static grids of 16, 64, 256, 1024 divisions versus Adaptive Subdivision (and its dicing settings): detail kept and render time.
#   4d  8-bit height images: terraces in true displacement; and is Cubic interpolation really better than Linear for Bump (the manual says so)?
# Output: out/displacement/*.png and out/displacement/results.json
# Run:  blender -b --disable-autoexec -t 2 --python exp4_displacement.py -- [parts, for example 4a4b]
import json
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import exp_common as ec  # noqa: E402

import bpy  # noqa: E402
import numpy as np  # noqa: E402

bh, rt = ec.bh, ec.rt
folder = os.path.join(ec.OUT, 'displacement')
os.makedirs(folder, exist_ok=True)
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
PARTS = args[0] if args else '4a4b4c4d'
results = {}


def fresh_scene(width, height, samples=16):
    bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = samples
    scene.cycles.use_adaptive_sampling = False
    scene.cycles.use_denoising = False
    scene.cycles.max_bounces = 2
    scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = width, height, 100
    scene.view_settings.view_transform = 'Raw'
    scene.view_settings.look = 'None'
    world = bpy.data.worlds.new('w')
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs['Color'].default_value = (0, 0, 0, 1)
    scene.world = world
    return scene


def add_camera(scene, location, rotation, ortho_scale):
    data = bpy.data.cameras.new('cam')
    data.type = 'ORTHO'
    data.ortho_scale = ortho_scale
    data.clip_start, data.clip_end = 0.01, 100
    camera = bpy.data.objects.new('cam', data)
    camera.location = location
    camera.rotation_euler = rotation
    scene.collection.objects.link(camera)
    scene.camera = camera
    return camera


def grid_object(scene, x_div, y_div, name='slab', thickness=None):
    """A 1 x 1 grid in the XY plane (UV 0..1), optionally given thickness downward so a side view shows a solid slab."""
    mesh = bpy.data.meshes.new(name)
    xs = np.linspace(-0.5, 0.5, x_div + 1)
    ys = np.linspace(-0.5, 0.5, y_div + 1)
    GX, GY = np.meshgrid(xs, ys)
    verts = np.stack([GX.ravel(), GY.ravel(), np.zeros(GX.size)], axis=-1)
    index = np.arange((x_div + 1) * (y_div + 1)).reshape(y_div + 1, x_div + 1)
    quads = np.stack([index[:-1, :-1].ravel(), index[:-1, 1:].ravel(), index[1:, 1:].ravel(), index[1:, :-1].ravel()], axis=-1)
    mesh.from_pydata(verts.tolist(), [], quads.tolist())
    uv = mesh.uv_layers.new(name='UVMap')
    loop_vertices = np.array([loop.vertex_index for loop in mesh.loops])
    uv.data.foreach_set('uv', np.stack([verts[loop_vertices, 0] + 0.5, verts[loop_vertices, 1] + 0.5], axis=-1).astype(np.float32).ravel())
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    if thickness:
        solid = obj.modifiers.new('solid', 'SOLIDIFY')
        solid.thickness = thickness
        solid.offset = -1.0
    return obj


def displacement_material(height_builder, midlevel=0.5, scale=0.1, method='DISPLACEMENT', surface='emission', space='OBJECT', bump=None):
    """A material with a Displacement node. height_builder(writer) adds nodes and returns (node, socket) giving the height 0..1.
    surface: 'emission' (white, so a silhouette is easy to measure) or 'diffuse'."""
    material = bpy.data.materials.new('disp')
    material.use_nodes = True
    material.displacement_method = method
    tree = material.node_tree
    tree.nodes.clear()
    w = rt.NodeWriter(tree)
    w.add('ShaderNodeTexCoord', 'coords', x=0)
    node, socket = height_builder(w)
    w.add('ShaderNodeDisplacement', 'disp', x=3, space=space, Midlevel=midlevel, Scale=scale)
    w.link(node, socket, 'disp', 'Height')
    if surface == 'emission':
        w.add('ShaderNodeEmission', 'surf', x=4, Color=(1, 1, 1, 1), Strength=1.0)
        w.add('ShaderNodeOutputMaterial', 'output', x=5)
        w.link('surf', 'Emission', 'output', 'Surface')
    else:
        w.add('ShaderNodeBsdfDiffuse', 'surf', x=4)
        w.nodes['surf'].inputs['Color'].default_value = (0.6, 0.6, 0.6, 1.0)
        w.add('ShaderNodeOutputMaterial', 'output', x=5)
        w.link('surf', 'BSDF', 'output', 'Surface')
    w.link('disp', 'Displacement', 'output', 'Displacement')
    return material


def step_height(w):
    w.add('ShaderNodeSeparateXYZ', 'sep', x=1)
    w.link('coords', 'UV', 'sep', 'Vector')
    w.math('step', 'GREATER_THAN', None, 0.5, x=2)
    w.link('sep', 'X', 'step', 0)
    return 'step', 0


def noise_height(scale=6.0, detail=5.0):
    def build(w):
        node = w.add('ShaderNodeGroup', 'n', x=1)
        node.node_tree = rt.tileable_noise_group()
        w.link('coords', 'UV', 'n', 'Vector')
        node.inputs['Scale'].default_value = scale
        node.inputs['Detail'].default_value = detail
        return 'n', 'Fac'
    return build


def render_gray(scene, path):
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.image_settings.color_depth = '8'
    scene.render.filepath = path
    started = time.time()
    bpy.ops.render.render(write_still=True)
    seconds = time.time() - started
    return bh.load_png_as_array(path)[..., 0], seconds


def top_edge_rows(picture):
    """For each column the (sub-pixel) row where the lit slab starts; rows run top to bottom."""
    rows, columns = picture.shape
    edge = np.full(columns, np.nan)
    for column in range(columns):
        lit = np.where(picture[:, column] > 0.02)[0]
        if len(lit):
            first = lit[0]
            edge[column] = first + (1.0 - min(picture[first, column], 1.0))
    return edge


# ---------------------------------------------------------------------------------- 4a  midlevel, scale, space (side view of a step)
if '4a' in PARTS:
    N = 480
    ortho = 1.2
    pixels_per_unit = N / ortho
    elevation = math.radians(2.0)                 # nearly edge-on: the far edge of a flat sheet shows the displaced profile; no walls to bend the normals
    table = {}
    for midlevel, scale, space, stretch in ((0.5, 0.1, 'OBJECT', 1.0), (0.0, 0.1, 'OBJECT', 1.0), (1.0, 0.1, 'OBJECT', 1.0), (0.5, 0.2, 'OBJECT', 1.0),
                                            (0.5, 0.1, 'OBJECT', 2.0), (0.5, 0.1, 'WORLD', 2.0)):
        scene = fresh_scene(N, N, samples=8)
        add_camera(scene, (0.0, -3.0 * math.cos(elevation), 3.0 * math.sin(elevation)), (math.pi / 2 - elevation, 0, 0), ortho)
        slab = grid_object(scene, 480, 4)
        slab.scale = (1.0, 1.0, stretch)
        slab.data.materials.append(displacement_material(step_height, midlevel, scale, 'DISPLACEMENT', 'emission', space))
        picture, seconds = render_gray(scene, os.path.join(folder, f'4a_mid{midlevel}_scale{scale}_{space}_stretch{stretch}.png'))
        edge = top_edge_rows(picture)
        def height_at(columns):
            screen_up = (N / 2 - float(np.nanmean(edge[columns]))) / pixels_per_unit
            return (screen_up - 0.5 * math.sin(elevation)) / math.cos(elevation)
        left = height_at(slice(N // 2 - 160, N // 2 - 80))      # the sheet spans columns 40..440; left of the centre is u < 0.5
        right = height_at(slice(N // 2 + 80, N // 2 + 160))
        factor = stretch if space == 'OBJECT' else 1.0
        table[f'Midlevel {midlevel}, Scale {scale}, Space {space}, object stretched x{stretch} in z'] = {
            'measured_displacement_where_height_0': round(left, 4), 'expected_(0-mid)*scale': round((0.0 - midlevel) * scale * factor, 4),
            'measured_displacement_where_height_1': round(right, 4), 'expected_(1-mid)*scale': round((1.0 - midlevel) * scale * factor, 4)}
    results['4a_midlevel_scale_space'] = table

# ---------------------------------------------------------------------------------- 4b  method comparison
def low_angle_scene(width=640, height=320, samples=16):
    scene = fresh_scene(width, height, samples)
    elevation = math.radians(20.0)
    camera = add_camera(scene, (0.0, -3.0 * math.cos(elevation), 3.0 * math.sin(elevation)), (math.pi / 2 - elevation, 0, 0), 1.2)
    sun = bpy.data.lights.new('sun', 'SUN')
    sun.energy = 4.0
    sun.angle = 0.02
    sun_obj = bpy.data.objects.new('sun', sun)
    sun_obj.rotation_euler = (math.radians(55), 0, math.radians(-50))
    scene.collection.objects.link(sun_obj)
    return scene


if '4b' in PARTS:
    table = {}
    for method in ('BUMP', 'DISPLACEMENT', 'BOTH'):
        scene = low_angle_scene()
        slab = grid_object(scene, 512, 512)
        slab.data.materials.append(displacement_material(noise_height(6.0, 6.0), 0.5, 0.08, method, 'diffuse'))
        picture, seconds = render_gray(scene, os.path.join(folder, f'4b_method_{method}.png'))
        far_edge = top_edge_rows(picture)
        valid = ~np.isnan(far_edge)
        table[method] = {'far_edge_wobble_in_pixels (std of the top edge)': round(float(np.nanstd(far_edge)), 2), 'brightness_spread_inside': round(float(picture[100:250, 120:520].std()), 4),
                         'seconds_to_render': round(seconds, 1)}
    results['4b_displacement_method'] = table

# ---------------------------------------------------------------------------------- 4c  mesh fineness and adaptive subdivision
if '4c' in PARTS:
    table = {}
    for divisions in (16, 64, 256, 1024):
        scene = low_angle_scene()
        slab = grid_object(scene, divisions, divisions)
        slab.data.materials.append(displacement_material(noise_height(40.0, 6.0), 0.5, 0.05, 'DISPLACEMENT', 'diffuse'))
        picture, seconds = render_gray(scene, os.path.join(folder, f'4c_static_{divisions}.png'))
        far_edge = top_edge_rows(picture)
        table[f'static grid {divisions} x {divisions}'] = {'far_edge_wobble_px': round(float(np.nanstd(far_edge)), 2), 'brightness_spread_inside': round(float(picture[100:250, 120:520].std()), 4),
                                                          'seconds_to_render': round(seconds, 1), 'faces': divisions * divisions}
    for dicing in (8.0, 2.0, 1.0, 0.5):
        scene = low_angle_scene()
        slab = grid_object(scene, 2, 2)
        modifier = slab.modifiers.new('adaptive', 'SUBSURF')
        modifier.subdivision_type = 'SIMPLE'
        modifier.use_adaptive_subdivision = True
        modifier.adaptive_space = 'PIXEL'
        modifier.adaptive_pixel_size = 1.0
        scene.cycles.dicing_rate = dicing
        scene.cycles.max_subdivisions = 12
        slab.data.materials.append(displacement_material(noise_height(40.0, 6.0), 0.5, 0.05, 'DISPLACEMENT', 'diffuse'))
        try:
            picture, seconds = render_gray(scene, os.path.join(folder, f'4c_adaptive_dicing{dicing}.png'))
            far_edge = top_edge_rows(picture)
            table[f'adaptive subdivision, Dicing Rate {dicing} (Pixel Size 1.0)'] = {'far_edge_wobble_px': round(float(np.nanstd(far_edge)), 2),
                                                                                   'brightness_spread_inside': round(float(picture[100:250, 120:520].std()), 4), 'seconds_to_render': round(seconds, 1)}
        except Exception as error:
            table[f'adaptive subdivision, Dicing Rate {dicing}'] = 'FAILED: ' + repr(error)[:200]
    results['4c_mesh_fineness'] = table

# ---------------------------------------------------------------------------------- 4d  8-bit height images
if '4d' in PARTS:
    N = 480
    table = {}
    # a gentle ramp that only uses 40..60 percent of the grey range, stored as 8-bit and as 16-bit
    ramp = np.tile(0.4 + 0.2 * (np.arange(1024) + 0.5) / 1024.0, (64, 1))
    for bits in (8, 16):
        scene = fresh_scene(64, 64)
        bh.save_array_png(np.repeat(ramp[..., None], 3, axis=2), os.path.join(folder, f'4d_ramp_{bits}bit.png'), sixteen_bit=(bits == 16))   # NOTE: bake_harness.save_array_png writes only the RED channel for a 2-D array, so give it height x width x 3

    def image_height(path, interpolation='Linear'):
        def build(w):
            image = bpy.data.images.load(path, check_existing=False)
            image.colorspace_settings.name = 'Non-Color'
            node = w.add('ShaderNodeTexImage', 'img', x=1, interpolation=interpolation, extension='EXTEND')
            node.image = image
            w.link('coords', 'UV', 'img', 'Vector')
            w.add('ShaderNodeRGBToBW', 'bw', x=2)
            w.link('img', 'Color', 'bw', 'Color')
            return 'bw', 'Val'
        return build

    for bits in (8, 16):
        scene = fresh_scene(N, N, samples=4)
        add_camera(scene, (0.0, -3.0, 0.0), (math.pi / 2, 0, 0), 1.2)
        slab = grid_object(scene, 960, 4, thickness=0.25)
        slab.data.materials.append(displacement_material(image_height(os.path.join(folder, f'4d_ramp_{bits}bit.png')), 0.5, 2.0, 'DISPLACEMENT', 'emission'))
        picture, seconds = render_gray(scene, os.path.join(folder, f'4d_displaced_ramp_{bits}bit.png'))
        edge = top_edge_rows(picture)[40:440]
        steps = int((np.abs(np.diff(edge)) > 0.5).sum())
        flat_columns = int((np.abs(np.diff(edge)) < 0.02).sum())
        table[f'{bits}-bit ramp 0.40..0.60, Scale 2.0: true displacement'] = {'top_edge_jumps_bigger_than_half_a_pixel': steps, 'columns_where_the_edge_does_not_move': flat_columns, 'of_columns': len(edge) - 1}
    # bump with linear versus cubic interpolation on an 8-bit smooth noise picture (manual says cubic avoids stepping)
    scene = fresh_scene(256, 256)
    scene_tile = bh.new_bake_scene(256)
    scene, tile = scene_tile
    group = rt.make_group_tree('smooth height', [('Vector', 'NodeSocketVector', (0, 0, 0))], [('Height', 'NodeSocketFloat')])
    tree, w = group
    node = w.add('ShaderNodeGroup', 'n')
    node.node_tree = rt.tileable_noise_group()
    node.inputs['Scale'].default_value = 3.0
    node.inputs['Detail'].default_value = 2.0
    w.link('in', 'Vector', 'n', 'Vector')
    w.math('low contrast', 'MULTIPLY_ADD', None, 0.15)
    w.nodes['low contrast'].inputs[2].default_value = 0.42
    w.link('n', 'Fac', 'low contrast', 0)
    w.link('low contrast', 0, 'out', 'Height')
    tile.data.materials.append(bh.show_channel_material(tree, 'Height'))
    scene.cycles.samples = 16
    bh.render_to(scene, os.path.join(folder, '4d_smooth_noise_16bit.png'), True, True)
    smooth = bh.load_png_as_array(os.path.join(folder, '4d_smooth_noise_16bit.png'))[..., 0]
    bh.save_array_png(np.repeat((np.round(smooth * 255) / 255.0)[..., None], 3, axis=2), os.path.join(folder, '4d_smooth_noise_8bit.png'), sixteen_bit=False)
    float_path = os.path.join(folder, '4d_smooth_noise_float.exr')
    image = bpy.data.images.new('exr', 256, 256, alpha=False, float_buffer=True)
    rgba = np.ones((256, 256, 4), np.float32)
    rgba[..., :3] = smooth[::-1, :, None]
    image.pixels.foreach_set(rgba.ravel())
    image.filepath_raw = float_path
    image.file_format = 'OPEN_EXR'
    image.save()
    normals = {}
    for label, path, interpolation in (('float image, Linear', float_path, 'Linear'), ('8-bit image, Linear', os.path.join(folder, '4d_smooth_noise_8bit.png'), 'Linear'),
                                      ('8-bit image, Cubic', os.path.join(folder, '4d_smooth_noise_8bit.png'), 'Cubic'),
                                      ('8-bit image, Closest', os.path.join(folder, '4d_smooth_noise_8bit.png'), 'Closest'),
                                      ('16-bit image, Linear', os.path.join(folder, '4d_smooth_noise_16bit.png'), 'Linear')):
        tree, w = rt.make_group_tree('image height', [('Vector', 'NodeSocketVector', (0, 0, 0))], [('Height', 'NodeSocketFloat')])
        loaded = bpy.data.images.load(path, check_existing=False)
        loaded.colorspace_settings.name = 'Non-Color'
        img_node = w.add('ShaderNodeTexImage', 'img', interpolation=interpolation, extension='REPEAT')
        img_node.image = loaded
        w.link('in', 'Vector', 'img', 'Vector')
        w.add('ShaderNodeRGBToBW', 'bw')
        w.link('img', 'Color', 'bw', 'Color')
        w.link('bw', 'Val', 'out', 'Height')
        tile.data.materials.clear()
        tile.data.materials.append(bh.show_channel_material(tree, 'NormalBump', normal_distance=0.2))
        name = label.replace(' ', '_').replace(',', '')
        bh.render_to(scene, os.path.join(folder, f'4d_bump_{name}.png'), True, True)
        normals[label] = bh.load_png_as_array(os.path.join(folder, f'4d_bump_{name}.png'))
    truth = normals['float image, Linear']
    for label, picture in normals.items():
        tilt = picture[..., :2] - 0.5
        table[f'Bump normal map from: {label}'] = {'mean_abs_error_vs_float_image': round(float(np.abs(picture - truth).mean()), 5),
                                                  'pixels_with_exactly_flat_x_tilt_percent': round(float((np.abs(tilt[..., 0]) < 2e-4).mean() * 100), 1)}
    results['4d_8bit_heights'] = table

with open(os.path.join(folder, f'results_{PARTS}.json'), 'w') as handle:
    json.dump(results, handle, indent=1)
print(json.dumps(results, indent=1))
