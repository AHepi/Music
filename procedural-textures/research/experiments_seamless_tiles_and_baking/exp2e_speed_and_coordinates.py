# What this does: experiment 2e. Two practical questions about "photographing" a recipe:
#   S  How long does a full-size (1254 x 1254) photograph take at 4, 16, 32 and 64 samples, for a plain 3D noise and for the seamless 4D "donut" noise
#      (Detail 8)? And how much does 4D cost compared with 3D?
#   C  Which texture coordinate should a recipe use? The same raw 3D noise is photographed with UV, Generated and Object coordinates on (1) a 1 x 1 square
#      and (2) the same square stretched to 2 x 1 by the object's scale. Pictures are compared with the UV picture of the 1 x 1 square.
# Output: out/speed/results.json
# Run:  blender -b --disable-autoexec -t 2 --python exp2e_speed_and_coordinates.py
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import exp_common as ec  # noqa: E402

import bpy  # noqa: E402
import numpy as np  # noqa: E402

bh, rt = ec.bh, ec.rt
folder = os.path.join(ec.OUT, 'speed')
os.makedirs(folder, exist_ok=True)
results = {}


def noise_recipe(kind, detail):
    tree, w = rt.make_group_tree(f'speed {kind} {detail}', [('Vector', 'NodeSocketVector', (0, 0, 0))], [('Height', 'NodeSocketFloat')])
    if kind == '3D':
        w.add('ShaderNodeTexNoise', 'n', noise_dimensions='3D', noise_type='FBM', normalize=True, Scale=6.0, Detail=detail)
        w.link('in', 'Vector', 'n', 'Vector')
        w.link('n', 'Fac', 'out', 'Height')
    else:
        node = w.add('ShaderNodeGroup', 'n')
        node.node_tree = rt.tileable_noise_group()
        node.inputs['Scale'].default_value = 6.0
        node.inputs['Detail'].default_value = detail
        w.link('in', 'Vector', 'n', 'Vector')
        w.link('n', 'Fac', 'out', 'Height')
    return tree


# ------------------------------------------------------------------ S: seconds per photograph at 1254 px
size = 1254
scene, tile = bh.new_bake_scene(size)
table = {}
for kind in ('3D', '4D donut'):
    group = noise_recipe(kind, 8.0)
    tile.data.materials.clear()
    tile.data.materials.append(bh.show_channel_material(group, 'Height'))
    for samples in (4, 16, 64):
        scene.cycles.samples = samples
        started = time.time()
        bh.render_to(scene, os.path.join(folder, 'speed_test.png'), True, True)
        table[f'{kind} noise, Detail 8, {samples} samples'] = round(time.time() - started, 1)
results['S_seconds_per_1254px_photograph (2 threads)'] = table

# ------------------------------------------------------------------ C: which coordinate?
size = 256
scene, tile = bh.new_bake_scene(size)
scene.cycles.samples = 16


def coordinate_material(source):
    material = bpy.data.materials.new('coord ' + source)
    material.use_nodes = True
    tree = material.node_tree
    tree.nodes.clear()
    w = rt.NodeWriter(tree)
    w.add('ShaderNodeTexCoord', 'coords', x=0)
    w.add('ShaderNodeTexNoise', 'n', x=1, noise_dimensions='3D', noise_type='FBM', normalize=True, Scale=6.0, Detail=4.0)
    w.link('coords', source, 'n', 'Vector')
    w.add('ShaderNodeCombineColor', 'grey', x=2)
    for socket in ('Red', 'Green', 'Blue'):
        w.link('n', 'Fac', 'grey', socket)
    w.add('ShaderNodeEmission', 'emit', x=3)
    w.link('grey', 'Color', 'emit', 'Color')
    w.add('ShaderNodeOutputMaterial', 'output', x=4)
    w.link('emit', 'Emission', 'output', 'Surface')
    return material


pictures = {}
for stretch in (1.0, 2.0):
    tile.scale = (stretch, 1.0, 1.0)
    # the camera is fixed at 1 x 1, so a 2 x 1 square would be cut off: widen the camera for the stretched case and compare the left half only
    scene.camera.data.ortho_scale = 1.0 * stretch
    scene.camera.location = (0.5 * stretch, 0.5, 5.0)
    for source in ('UV', 'Generated', 'Object'):
        tile.data.materials.clear()
        tile.data.materials.append(coordinate_material(source))
        path = os.path.join(folder, f'coords_{source}_stretch{stretch}.png')
        bh.render_to(scene, path, True, False)
        pictures[(source, stretch)] = bh.load_png_as_array(path)[..., 0]
reference = pictures[('UV', 1.0)]
table = {}
for (source, stretch), picture in pictures.items():
    if stretch == 1.0:
        table[f'{source} on a 1 x 1 square: mean abs difference from the UV picture'] = round(float(np.abs(picture - reference).mean()), 4)
    else:
        # the camera now covers 2 x 2 units of which the square fills the middle strip; compare the whole-camera picture with a 1 x 1 picture squeezed to 2 wide
        table[f'{source} on a square stretched to 2 x 1 (object scale 2): the picture looks the same as the unstretched one? mean abs difference of the left half'] = None
    results['C_coordinate_source'] = table
# simple check of "does stretching the object change the pattern": compare the picture of the stretched square, resampled to 1:1, with the unstretched one
for source in ('UV', 'Generated', 'Object'):
    stretched = pictures[(source, 2.0)]
    rows, columns = stretched.shape
    # the camera ortho is 2 wide, the square occupies the middle 256 rows (a 2 x 1 strip); take them and squeeze 2:1 horizontally to compare with the 1 x 1 picture
    strip = stretched[rows // 4: 3 * rows // 4, :]
    small_reference = reference.reshape(reference.shape[0] // 2, 2, reference.shape[1]).mean(axis=1)      # the 1 x 1 picture squeezed 2:1 vertically
    results['C_coordinate_source'][f'{source}: picture of the square stretched to 2 x 1, compared with the unstretched picture squeezed to the same shape: mean abs difference'] = round(float(np.abs(strip - small_reference).mean()), 4)
results['C_coordinate_source'] = {k: v for k, v in results['C_coordinate_source'].items() if v is not None}

with open(os.path.join(folder, 'results.json'), 'w') as handle:
    json.dump(results, handle, indent=1)
print(json.dumps(results, indent=1))
