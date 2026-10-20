# What this does: experiment 3. It tests the ways of turning a height picture into a normal map:
#   A  Blender's Bump node (photographed): how does the Distance setting relate to the picture size, and does the result change with resolution?
#   B  the Bump node's Filter Width on a hard-edged height (bricks): what does a larger width do to the edges?
#   C  Strength versus Distance (are they the same knob?) and Invert
#   D  the compositor route: Translate nodes (shift the picture by one pixel with wrap-around) and Math nodes, no Python image maths
# The pictures are written to out/normal/ and compared with numpy's Sobel by exp3_analyse.py (plain Python).
# Run:  blender -b --disable-autoexec -t 2 --python exp3_height_to_normal.py
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import exp_common as ec  # noqa: E402

import bpy  # noqa: E402
import numpy as np  # noqa: E402

bh, rt = ec.bh, ec.rt
folder = os.path.join(ec.OUT, 'normal')
os.makedirs(folder, exist_ok=True)
log = {}
PARTS = [a[6:] for a in sys.argv if a.startswith('parts=')]
PARTS = PARTS[0] if PARTS else 'ABCD'


def noise_height_group(name='height recipe'):
    tree, w = rt.make_group_tree(name, [('Vector', 'NodeSocketVector', (0, 0, 0))], [('Height', 'NodeSocketFloat')])
    node = w.add('ShaderNodeGroup', 'n')
    node.node_tree = rt.tileable_noise_group()
    w.link('in', 'Vector', 'n', 'Vector')
    node.inputs['Scale'].default_value = 6.0
    node.inputs['Detail'].default_value = 5.0
    w.link('n', 'Fac', 'out', 'Height')
    return tree


def brick_height_group(name='brick height'):
    tree, w = rt.make_group_tree(name, [('Vector', 'NodeSocketVector', (0, 0, 0))], [('Height', 'NodeSocketFloat')])
    w.add('ShaderNodeTexBrick', 'brick', offset=0.5, offset_frequency=2, squash=1.0, squash_frequency=2, Scale=4.0, Mortar__Size=0.03, Mortar__Smooth=0.0,
          Bias=0.0, Brick__Width=0.5, Row__Height=0.25, Color1=(1, 1, 1, 1), Color2=(1, 1, 1, 1), Mortar=(0, 0, 0, 1))
    w.link('in', 'Vector', 'brick', 'Vector')
    w.link('brick', 'Factor', 'out', 'Height')      # Factor is 1 in the mortar, 0 on bricks: mortar is "high" here, which is fine for an edge test
    return tree


def bump_material(group, distance, strength=1.0, filter_width=0.1, invert=False):
    material = bpy.data.materials.new('bump normal')
    material.use_nodes = True
    tree = material.node_tree
    tree.nodes.clear()
    w = rt.NodeWriter(tree)
    w.add('ShaderNodeTexCoord', 'coords', x=0)
    w.add('ShaderNodeGroup', 'recipe', x=1)
    w.nodes['recipe'].node_tree = group
    w.link('coords', 'UV', 'recipe', 'Vector')
    w.add('ShaderNodeBump', 'bump', x=2, invert=invert, Strength=strength, Distance=distance, Filter__Width=filter_width)
    w.link('recipe', 'Height', 'bump', 'Height')
    w.add('ShaderNodeVectorMath', 'half', x=3, operation='MULTIPLY_ADD')
    w.nodes['half'].inputs[1].default_value = (0.5, 0.5, 0.5)
    w.nodes['half'].inputs[2].default_value = (0.5, 0.5, 0.5)
    w.link('bump', 'Normal', 'half', 0)
    w.add('ShaderNodeEmission', 'emit', x=4)
    w.link('half', 0, 'emit', 'Color')
    w.add('ShaderNodeOutputMaterial', 'output', x=5)
    w.link('emit', 'Emission', 'output', 'Surface')
    return material


def render_material(scene, tile, material, path, samples=16):
    tile.data.materials.clear()
    tile.data.materials.append(material)
    scene.cycles.samples = samples
    bh.render_to(scene, path, True, True)


# ---------------------------------------------------------------------------------- A  distance and resolution
for size in ((128, 256, 512) if 'A' in PARTS else ()):
    scene, tile = bh.new_bake_scene(size)
    group = noise_height_group()
    tile.data.materials.append(bh.show_channel_material(group, 'Height'))
    scene.cycles.samples = 16
    bh.render_to(scene, os.path.join(folder, f'A_height_{size}.png'), True, True)
    for distance in (0.01, 0.02, 0.04):
        render_material(scene, tile, bump_material(group, distance), os.path.join(folder, f'A_bump_d{distance}_{size}.png'))

# ---------------------------------------------------------------------------------- B  filter width on a hard-edged height
size = 256
scene, tile = bh.new_bake_scene(size)
group = brick_height_group()
tile.data.materials.append(bh.show_channel_material(group, 'Height'))
scene.cycles.samples = 16
if 'B' in PARTS:
    bh.render_to(scene, os.path.join(folder, 'B_height_bricks.png'), True, True)
for width in ((0.1, 1.0, 2.0) if 'B' in PARTS else ()):
    render_material(scene, tile, bump_material(group, 0.02, filter_width=width), os.path.join(folder, f'B_bump_filter{width}.png'))

# ---------------------------------------------------------------------------------- C  strength versus distance, and invert
if 'C' in PARTS:
    size = 256
    scene, tile = bh.new_bake_scene(size)
    group = noise_height_group()
    for label, d, s, inv in (('d0.02_s1', 0.02, 1.0, False), ('d0.04_s1', 0.04, 1.0, False), ('d0.02_s2', 0.02, 2.0, False), ('d0.04_s0.5', 0.04, 0.5, False),
                             ('d0.02_s1_invert', 0.02, 1.0, True), ('d0.1_s1', 0.1, 1.0, False), ('d0.02_s5', 0.02, 5.0, False)):
        render_material(scene, tile, bump_material(group, d, s, 0.1, inv), os.path.join(folder, f'C_{label}.png'))

# ---------------------------------------------------------------------------------- D  the compositor route
size = 256
scene, tile = bh.new_bake_scene(size)
group = noise_height_group()
tile.data.materials.append(bh.show_channel_material(group, 'Height'))
scene.cycles.samples = 16
height_path = os.path.join(folder, 'D_height.png')
bh.render_to(scene, height_path, True, True)

report = {'compositor': {}}
scene.render.compositor_device = 'CPU'           # the default is GPU, which crashes a machine without a graphics card (libEGL error)
scene.render.compositor_precision = 'FULL'       # AUTO may use half-float precision; data maps should use full 32-bit
if 'D' not in PARTS:
    raise SystemExit
try:
    tree = bpy.data.node_groups.new('normal from height', 'CompositorNodeTree')
    scene.compositing_node_group = tree
    tree.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
    out_node = tree.nodes.new('NodeGroupOutput')
    image_node = tree.nodes.new('CompositorNodeImage')
    image_node.image = bpy.data.images.load(height_path)
    image_node.image.colorspace_settings.name = 'Non-Color'

    def shifted(x, y, name):
        node = tree.nodes.new('CompositorNodeTranslate')
        node.name = name
        # in Blender 5.2 these are menu SOCKETS (not node properties) and take the names shown in the interface
        node.inputs['Interpolation'].default_value = 'Nearest'
        for socket in ('Extension X', 'Extension Y'):
            for candidate in ('Repeat', 'Wrap', 'Mirror', 'Extend'):
                try:
                    node.inputs[socket].default_value = candidate
                    break
                except TypeError:
                    continue
            report['compositor'][socket] = node.inputs[socket].default_value
        node.inputs['X'].default_value = float(x)
        node.inputs['Y'].default_value = float(y)
        tree.links.new(image_node.outputs['Image'], node.inputs['Image'])
        sep = tree.nodes.new('CompositorNodeSeparateColor')
        tree.links.new(node.outputs['Image'], sep.inputs['Image'])
        return sep.outputs['Red']

    def math(op, a, b=None, name=None):
        node = tree.nodes.new('ShaderNodeMath')
        node.operation = op
        for index, value in enumerate((a, b)):
            if value is None:
                continue
            if isinstance(value, (int, float)):
                node.inputs[index].default_value = float(value)
            else:
                tree.links.new(value, node.inputs[index])
        return node.outputs[0]

    strength = 5.33                                              # per-pixel slope strength (same meaning as the numpy Sobel strength)
    # TRAP found by testing: the Translate node moves the PICTURE, so Translate X=+1 puts each pixel's LEFT neighbour under it, and Y=+1 (up) puts the neighbour BELOW
    # under it. So: shifted(+1, 0) = left neighbour, shifted(-1, 0) = right neighbour, shifted(0, +1) = neighbour below, shifted(0, -1) = neighbour above.
    left_neighbour = shifted(+1, 0, 'left_neighbour')
    right_neighbour = shifted(-1, 0, 'right_neighbour')
    neighbour_below = shifted(0, +1, 'neighbour_below')
    neighbour_above = shifted(0, -1, 'neighbour_above')
    nx = math('MULTIPLY', math('SUBTRACT', left_neighbour, right_neighbour), strength / 2.0)       # = -s * (right - left) / 2
    ny = math('MULTIPLY', math('SUBTRACT', neighbour_below, neighbour_above), strength / 2.0)      # = +s * (below - above) / 2   (OpenGL: green up the picture)
    length = math('SQRT', math('ADD', math('ADD', math('MULTIPLY', nx, nx), math('MULTIPLY', ny, ny)), 1.0))
    def encode(value):
        return math('MULTIPLY_ADD', math('DIVIDE', value, length), 0.5)
    combine = tree.nodes.new('CompositorNodeCombineColor')
    for socket, value in (('Red', nx), ('Green', ny), ('Blue', 1.0)):
        node = math('MULTIPLY', math('DIVIDE', value, length) if not isinstance(value, float) else math('DIVIDE', value, length) , 0.5)
        node = math('ADD', node, 0.5)
        tree.links.new(node, combine.inputs[socket])
    tree.links.new(combine.outputs['Image'], out_node.inputs['Image'])
    scene.render.use_compositing = True
    bh.render_to(scene, os.path.join(folder, 'D_normal_compositor.png'), True, True)
    report['compositor']['status'] = 'rendered'
except Exception as error:                                       # record failures: they are part of the guide
    report['compositor']['status'] = 'FAILED: ' + repr(error)[:300]

with open(os.path.join(folder, 'log.json'), 'w') as handle:
    json.dump(report, handle, indent=1)
print(json.dumps(report, indent=1))
