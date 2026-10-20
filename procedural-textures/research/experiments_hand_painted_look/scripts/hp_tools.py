# What this does: shared helper functions for the hand-painted-look experiments (not part of lib/; lib/ is read-only for us).
# It adds on top of lib/bake_harness.py and lib/recipe_tools.py:
#   * photograph_group(): turn any shader node group (input 'Vector', one output) into a picture, optionally 3 x 3 times wider so
#     that a filter has real neighbours at the edges (padding) and cropping the middle tile out afterwards;
#   * run_compositor(): push a picture through compositor nodes in Blender 5.2 (compositing node group + Group Output) and save the result;
#   * stylising building blocks as node groups that keep a tile seamless: anisotropic (streaky) noise and cells, warped coordinates,
#     a "same pattern a few pixels away" outline maker.
# Use (inside Blender):  sys.path.insert(0, '<this folder>'); import hp_tools as hp
import json
import math
import os
import sys

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
LIB = os.path.join(PROC, 'lib')
sys.path.insert(0, LIB)
import bake_harness as bh  # noqa: E402
import recipe_tools as rt  # noqa: E402

OUT = os.path.abspath(os.path.join(HERE, '..'))

# Samples per pixel for every bake made through bake_harness. 4 = the harness default (smooth anti-aliased edges). 1 = no anti-aliasing at all, so a flat
# patch has exactly its own value up to the last pixel (needed when counting how many different levels a picture contains).
SAMPLES = 4
_original_new_bake_scene = bh.new_bake_scene


def _new_bake_scene_with_samples(size):
    scene, tile = _original_new_bake_scene(size)
    scene.cycles.samples = SAMPLES
    scene.render.dither_intensity = 0.0      # no random +-1/255 noise in 8-bit pictures, so flat levels stay exactly flat
    return scene, tile


bh.new_bake_scene = _new_bake_scene_with_samples


# ------------------------------------------------------------------------------------------------ small helpers
def new_group(name, inputs, outputs):
    """Same as rt.make_group_tree but always starts from a fresh group of that name."""
    old = bpy.data.node_groups.get(name)
    if old:
        bpy.data.node_groups.remove(old)
    return rt.make_group_tree(name, inputs, outputs)


def instance(tree_writer, group, name, x=None, y=0, **values):
    """Put a node-group instance into a writer's tree; values set the named inputs."""
    node = tree_writer.add('ShaderNodeGroup', name, x=x, y=y)
    node.node_tree = group
    for key, value in values.items():
        node.inputs[key.replace('__', ' ')].default_value = value
    return node


def srgb_hex_to_linear(hex_text):
    hex_text = hex_text.lstrip('#')
    rgb = [int(hex_text[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    return [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]


def linear_to_srgb(value):
    return 12.92 * value if value <= 0.0031308 else 1.055 * value ** (1 / 2.4) - 0.055


def wrap_for_padding(group, output_name, scale=3.0, offset=-1.0, name='padded'):
    """A wrapper group whose Vector input is stretched so that a render of the 1 x 1 square shows the tile domain from `offset` to
    `offset + scale` (default -1 to 2): the tile in the middle with a full tile of true neighbours all round."""
    inputs = [('Vector', 'NodeSocketVector', (0, 0, 0))]
    outputs = [(output_name, 'NodeSocketColor' if output_name == 'Colour' else 'NodeSocketFloat')]
    tree, w = new_group(name, inputs, outputs)
    w.vector_math('scale uv', 'SCALE', x=0)
    w.link('in', 'Vector', 'scale uv', 0)
    w.nodes['scale uv'].inputs['Scale'].default_value = scale
    w.vector_math('shift uv', 'ADD', x=1)
    w.link('scale uv', 0, 'shift uv', 0)
    w.nodes['shift uv'].inputs[1].default_value = (offset, offset, 0)
    w.add('ShaderNodeGroup', 'inner', x=2)
    w.nodes['inner'].node_tree = group
    w.link('shift uv', 0, 'inner', 'Vector')
    w.link('inner', output_name, 'out', output_name)
    return tree


def photograph_group(build, channel, path, size, linear=None, sixteen=False, pad=False):
    """Render one output ('Colour' or any float output such as 'Height') of a group to a PNG, straight from above, no lighting.
    build: a function with no arguments that returns the shader node group (it is called AFTER the scene is reset, because resetting
    the scene deletes every node group made before).
    pad=True renders a 3 x 3 times larger picture (domain -1..2) and saves only the middle tile to `path` (the padded picture is
    saved next to it with '_padded' in the name)."""
    if linear is None:
        linear = channel != 'Colour'
    scene, tile = bh.new_bake_scene(size * (3 if pad else 1))
    group = build()
    if pad:
        group = wrap_for_padding(group, channel)
    material = bh.show_channel_material(group, channel)
    tile.data.materials.clear()
    tile.data.materials.append(material)
    target = path if not pad else path.replace('.png', '_padded.png')
    bh.render_to(scene, target, linear, sixteen)
    if pad:
        full = bh.load_png_as_array(target)
        middle = full[size:2 * size, size:2 * size]
        bh.save_array_png(middle, path, sixteen)
    return path


def load(path):
    """Picture as float array 0..1 rows top to bottom, no colour conversion (what is in the file)."""
    return bh.load_png_as_array(path)


def save(array, path, sixteen=False):
    """Write an array 0..1 as PNG. A one-channel (2-D) array is written as grey in all three channels (the lib function would otherwise fill only red)."""
    array = np.clip(array, 0, 1)
    if array.ndim == 2:
        array = np.stack([array] * 3, axis=-1)
    bh.save_array_png(array, path, sixteen)


# ------------------------------------------------------------------------------------------------ the compositor in Blender 5.2
def run_compositor(in_path, out_path, build, input_linear=False, output_linear=False, extra_images=None, sixteen=False, canvas=None):
    """Load a PNG into the compositor, let build(tree, image_node, extras) wire nodes and return the output socket, and save the result.
    input_linear=True reads the PNG numbers as they are (data pictures: height, masks); False reads it as an sRGB colour picture.
    Blender 5.x: the compositor is a node group stored on the scene (scene.compositing_node_group) and ends in a Group Output node."""
    source = bpy.data.images.load(in_path, check_existing=False)
    width, height = source.size
    source.colorspace_settings.name = 'Non-Color' if input_linear else 'sRGB'
    bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)
    scene = bpy.context.scene
    source = bpy.data.images.load(in_path, check_existing=False)
    source.colorspace_settings.name = 'Non-Color' if input_linear else 'sRGB'
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 1
    scene.cycles.use_denoising = False
    scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = (canvas or (width, height))[0], (canvas or (width, height))[1], 100
    scene.view_settings.view_transform = 'Raw' if output_linear else 'Standard'
    scene.view_settings.look = 'None'
    scene.display_settings.display_device = 'sRGB'
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    scene.render.image_settings.color_depth = '16' if sixteen else '8'
    scene.render.dither_intensity = 0.0
    camera_data = bpy.data.cameras.new('cam')
    camera = bpy.data.objects.new('cam', camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    scene.render.use_compositing = True
    scene.render.compositor_device = 'CPU'          # the GPU compositor needs a graphics card (libEGL); not available on this machine
    scene.render.compositor_precision = 'FULL'
    tree = bpy.data.node_groups.new('stylise', 'CompositorNodeTree')
    scene.compositing_node_group = tree
    tree.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
    image_node = tree.nodes.new('CompositorNodeImage')
    image_node.image = source
    extras = {}
    for key, path in (extra_images or {}).items():
        extra = bpy.data.images.load(path, check_existing=False)
        extra.colorspace_settings.name = 'Non-Color'
        node = tree.nodes.new('CompositorNodeImage')
        node.image = extra
        extras[key] = node
    result_socket = build(tree, image_node, extras)
    group_output = tree.nodes.new('NodeGroupOutput')
    tree.links.new(result_socket, group_output.inputs[0])
    scene.render.filepath = out_path
    bpy.ops.render.render(write_still=True)
    return out_path


def set_menu(node, socket_name, option):
    """Menu sockets (Type, Falloff, ...) take the option's name as text."""
    node.inputs[socket_name].default_value = option


# ------------------------------------------------------------------------------------------------ seamless stylising building blocks
def anisotropic_noise_group(name='Streaky Noise', cells=False, feature='F1', distance='EUCLIDEAN', exponent=None):
    """SEAMLESS noise (or, with cells=True, Voronoi cells) that can be stretched. Inputs: Vector (tile coordinate 0..1),
    Scale U (features across the tile left to right), Scale V (features across the tile bottom to top), Detail, Roughness, Distortion, Seed, Randomness.
    Scale U = 40 and Scale V = 4 gives streaks that run up the picture (long in v). Outputs: Fac, Distance (cells), Color, Position.
    How it works: u goes round a circle of circumference Scale U and v round a circle of circumference Scale V; the 4D noise is read
    at the four numbers (cos u, sin u, cos v, sin v), so it repeats every tile and each direction has its own feature size."""
    tree, w = new_group(name, [
        ('Vector', 'NodeSocketVector', (0, 0, 0)), ('Scale U', 'NodeSocketFloat', 8.0), ('Scale V', 'NodeSocketFloat', 8.0),
        ('Detail', 'NodeSocketFloat', 2.0), ('Roughness', 'NodeSocketFloat', 0.5), ('Distortion', 'NodeSocketFloat', 0.0),
        ('Seed', 'NodeSocketFloat', 0.0), ('Randomness', 'NodeSocketFloat', 1.0)],
        [('Fac', 'NodeSocketFloat'), ('Distance', 'NodeSocketFloat'), ('Color', 'NodeSocketColor'), ('Position', 'NodeSocketVector')])
    w.add('ShaderNodeSeparateXYZ', 'split uv', x=-3)
    w.link('in', 'Vector', 'split uv', 'Vector')
    pieces = {}
    for axis, label, scale_name in (('X', 'u', 'Scale U'), ('Y', 'v', 'Scale V')):
        row = 0 if label == 'u' else -3
        w.math(f'turns {label}', 'MULTIPLY', None, 2 * math.pi, x=-2, y=row)
        w.link('split uv', axis, f'turns {label}', 0)
        w.math(f'radius {label}', 'DIVIDE', None, 2 * math.pi, x=-2, y=row + 1)
        w.link('in', scale_name, f'radius {label}', 0)
        for trig, fn in (('cos', 'COSINE'), ('sin', 'SINE')):
            w.math(f'{trig} {label}', fn, x=-1, y=row)
            w.link(f'turns {label}', 0, f'{trig} {label}', 0)
            w.math(f'{trig} {label} r', 'MULTIPLY', x=0, y=row)
            w.link(f'{trig} {label}', 0, f'{trig} {label} r', 0)
            w.link(f'radius {label}', 0, f'{trig} {label} r', 1)
    w.add('ShaderNodeCombineXYZ', 'xyz', x=1)
    w.link('cos u r', 0, 'xyz', 'X')
    w.link('sin u r', 0, 'xyz', 'Y')
    w.link('cos v r', 0, 'xyz', 'Z')
    w.math('w seed', 'ADD', x=1, y=-3)
    w.link('sin v r', 0, 'w seed', 0)
    w.link('in', 'Seed', 'w seed', 1)
    w.add('ShaderNodeTexNoise', 'noise', x=2, noise_dimensions='4D', noise_type='FBM', normalize=True, Scale=1.0)
    w.link('xyz', 0, 'noise', 'Vector')
    w.link('w seed', 0, 'noise', 'W')
    for socket in ('Detail', 'Roughness', 'Distortion'):
        w.link('in', socket, 'noise', socket)
    w.add('ShaderNodeTexVoronoi', 'cells', x=2, y=-2, voronoi_dimensions='4D', feature=feature, distance=distance, Scale=1.0)
    if exponent is not None:
        w.nodes['cells'].inputs['Exponent'].default_value = exponent
    w.link('xyz', 0, 'cells', 'Vector')
    w.link('w seed', 0, 'cells', 'W')
    w.link('in', 'Randomness', 'cells', 'Randomness')
    w.link('noise', 'Fac', 'out', 'Fac')
    enabled = {socket.name for socket in w.nodes['cells'].outputs if socket.enabled}
    for socket_name in ('Distance', 'Color', 'Position'):
        if socket_name in enabled:                       # Distance To Edge only has the Distance output
            w.link('cells', socket_name, 'out', socket_name)
    return tree


def seam_ratio_of(array):
    grey = array if array.ndim == 2 else array.mean(axis=2)
    inner = (np.abs(np.diff(grey, axis=1)).mean() + np.abs(np.diff(grey, axis=0)).mean()) / 2.0
    wrap = (np.abs(grey[:, 0] - grey[:, -1]).mean() + np.abs(grey[0, :] - grey[-1, :]).mean()) / 2.0
    return float(wrap / max(inner, 1e-9))


# ------------------------------------------------------------------------------------------------ sweeps (a row of pictures: one setting, several values)
def sweep(build_for_value, values, folder, labels=None, channel='Colour', size=256, columns=None, title=None, cell=256):
    """Render one small picture per value (build_for_value(value) must return a shader node group with input 'Vector' and output `channel`),
    join them into a labelled strip folder/strip.png, and return the pictures as arrays (for counting levels, seams, etc.)."""
    import subprocess
    import sweep_tools as st
    os.makedirs(folder, exist_ok=True)
    labels = labels or [str(v) for v in values]
    files = st.render_sweep(build_for_value, values, folder, channel, size, labels)
    out = os.path.join(folder, 'strip.png')
    subprocess.run(['python3', '-I', os.path.join(LIB, 'make_strip.py'), folder, out, '--columns', str(columns or len(values)),
                    '--title', title or os.path.basename(folder.rstrip('/')), '--cell', str(cell)], check=True, capture_output=True)
    return [load(os.path.join(folder, f)) for f in files]


def levels(array, decimals=3, min_share=0.004):
    """How many different grey values a picture really uses: values that cover at least min_share of the pixels (this ignores the few
    in-between pixels that anti-aliasing makes on the edge of every flat patch). Returns (count, [(value, share), ...] biggest first, max 24)."""
    grey = array if array.ndim == 2 else array.mean(axis=2)
    values, counts = np.unique(np.round(grey, decimals), return_counts=True)
    shares = counts / grey.size
    keep = shares >= min_share
    order = np.argsort(values[keep])
    return int(keep.sum()), [(float(values[keep][i]), round(float(shares[keep][i]), 3)) for i in order][:24]


# ------------------------------------------------------------------------------------------------ palette and per-cell randomness
BRICK_PALETTE = [('#3a2d27', 9.2), ('#513c31', 12.3), ('#633b2e', 10.4), ('#773f2e', 15.5), ('#8b442d', 18.1), ('#775e49', 13.5), ('#a34d2d', 14.5), ('#9a7b5f', 6.6)]
SLATE_PALETTE = [('#0e0f11', 8.0), ('#1e2022', 9.8), ('#2d3133', 15.9), ('#3a3c31', 7.4), ('#3a4045', 28.7), ('#4f4e40', 5.8), ('#4a5254', 20.7), ('#6d6c67', 3.8)]


def luminance_of_hex(hex_text):
    r, g, b = srgb_hex_to_linear(hex_text)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def palette_ramp(w, name, palette, x=None, y=0, by_lightness=True):
    """A Color Ramp with Constant interpolation holding a painted palette. palette = [(hex, share_in_percent), ...]. Colours are sorted dark to light
    (so a smooth input 0..1 reads as dark to light) and each colour gets a stretch of the 0..1 input as long as its share. A uniform random number
    in gives each colour as often as its share. Hex colours are converted to the linear numbers the ramp wants."""
    colours = sorted(palette, key=lambda p: luminance_of_hex(p[0])) if by_lightness else list(palette)
    total = sum(share for _, share in colours)
    node = w.add('ShaderNodeValToRGB', name, x=x, y=y)
    ramp = node.color_ramp
    ramp.interpolation = 'CONSTANT'
    while len(ramp.elements) < len(colours):
        ramp.elements.new(0.5)
    start = 0.0
    for element, (hex_text, share) in zip(ramp.elements, colours):
        element.position = start
        element.color = (*srgb_hex_to_linear(hex_text), 1.0)
        start += share / total
    return node


def cell_random(w, name, source_node, source_socket, seed=0.0, x=None, y=0):
    """One random number 0..1 per cell: White Noise (4D) of the cell's centre position. Different seed = a different independent random number."""
    node = w.add('ShaderNodeTexWhiteNoise', name, x=x, y=y, noise_dimensions='4D')
    w.link(source_node, source_socket, name, 'Vector')
    node.inputs['W'].default_value = seed
    return node


def warp_vector_group(name='Warp Coordinates'):
    """Pushes the tile coordinate around with seamless noise before another pattern reads it ('domain warping'). Inputs: Vector, Amount (about the biggest
    push, as a fraction of the tile: 0.05 = 5 percent of the tile width), Scale (features of the warp noise across one tile), Seed.
    Output: Vector. Because the push itself repeats every tile, anything seamless that reads the warped coordinate stays seamless."""
    tree, w = new_group(name, [('Vector', 'NodeSocketVector', (0, 0, 0)), ('Amount', 'NodeSocketFloat', 0.05), ('Scale', 'NodeSocketFloat', 3.0),
                               ('Seed', 'NodeSocketFloat', 0.0)], [('Vector', 'NodeSocketVector')])
    w.add('ShaderNodeGroup', 'warp noise', x=0)
    w.nodes['warp noise'].node_tree = rt.tileable_noise_group()
    w.link('in', 'Vector', 'warp noise', 'Vector')
    w.link('in', 'Scale', 'warp noise', 'Scale')
    w.link('in', 'Seed', 'warp noise', 'Seed')
    w.nodes['warp noise'].inputs['Detail'].default_value = 2.0
    w.add('ShaderNodeSeparateColor', 'rgb', x=1)
    w.link('warp noise', 'Color', 'rgb', 'Color')
    w.add('ShaderNodeSeparateXYZ', 'uv', x=1, y=-2)
    w.link('in', 'Vector', 'uv', 'Vector')
    for label, channel, axis, row in (('u', 'Red', 'X', 0), ('v', 'Green', 'Y', -1)):
        w.add('ShaderNodeMapRange', f'centre {label}', x=2, y=row, clamp=False)
        w.nodes[f'centre {label}'].inputs['From Min'].default_value = 0.25
        w.nodes[f'centre {label}'].inputs['From Max'].default_value = 0.75
        w.nodes[f'centre {label}'].inputs['To Min'].default_value = -1.0
        w.nodes[f'centre {label}'].inputs['To Max'].default_value = 1.0
        w.link('rgb', channel, f'centre {label}', 'Value')
        w.math(f'push {label}', 'MULTIPLY', x=3, y=row)
        w.link(f'centre {label}', 'Result', f'push {label}', 0)
        w.link('in', 'Amount', f'push {label}', 1)
        w.math(f'new {label}', 'ADD', x=4, y=row)
        w.link('uv', axis, f'new {label}', 0)
        w.link(f'push {label}', 0, f'new {label}', 1)
    w.add('ShaderNodeCombineXYZ', 'warped', x=5)
    w.link('new u', 0, 'warped', 'X')
    w.link('new v', 0, 'warped', 'Y')
    w.link('warped', 'Vector', 'out', 'Vector')
    return tree


# ------------------------------------------------------------------------------------------------ does the pattern really repeat?
def periodicity_check(build, channel, size=256, threshold=0.03):
    """The strictest seamless test: render the pattern over 2 x 2 tiles (domain 0..2) and compare the tile at 0..1 with the tile at 1..2 (to the right),
    and again with the one above. A truly repeating pattern gives the same picture. Returns the share of pixels that differ by more than `threshold` and the
    mean absolute difference (both for left/right and for bottom/top, worst of the two)."""
    scene, tile = bh.new_bake_scene(size * 2)
    group = wrap_for_padding(build(), channel, scale=2.0, offset=0.0, name='periodicity probe')
    material = bh.show_channel_material(group, channel)
    tile.data.materials.clear()
    tile.data.materials.append(material)
    path = os.path.join(bpy.app.tempdir or '/tmp', 'periodicity_probe.png')
    bh.render_to(scene, path, channel != 'Colour', False)
    full = bh.load_png_as_array(path)
    first, right, above = full[size:2 * size, :size], full[size:2 * size, size:], full[:size, :size]   # rows are top to bottom: lower half = v in 0..1
    worst_share, worst_mean = 0.0, 0.0
    for other in (right, above):
        diff = np.abs(first - other).mean(axis=2)
        worst_share = max(worst_share, float((diff > threshold).mean()))
        worst_mean = max(worst_mean, float(diff.mean()))
    return {'share_of_pixels_that_differ': worst_share, 'mean_abs_difference': worst_mean}


def photograph_padded(build, channel, path, size, pad_px, linear=None, sixteen=False):
    """Like photograph_group(pad=True) but with a margin of only `pad_px` pixels on every side: renders size + 2 x pad_px pixels over the tile domain
    -pad/size .. 1 + pad/size, saves the padded picture (name + '_padded') and the middle `size` x `size` tile (the tile itself)."""
    if linear is None:
        linear = channel != 'Colour'
    total = size + 2 * pad_px
    scene, tile = bh.new_bake_scene(total)
    group = wrap_for_padding(build(), channel, scale=total / size, offset=-pad_px / size, name='padded margin')
    material = bh.show_channel_material(group, channel)
    tile.data.materials.clear()
    tile.data.materials.append(material)
    target = path.replace('.png', '_padded.png')
    bh.render_to(scene, target, linear, sixteen)
    full = bh.load_png_as_array(target)
    bh.save_array_png(full[pad_px:pad_px + size, pad_px:pad_px + size], path, sixteen)
    return target
