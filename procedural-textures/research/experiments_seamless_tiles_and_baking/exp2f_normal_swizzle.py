# What this does: experiment 2f. Cycles Bake > Normal has "Swizzle" settings (R, G, B: +X, -X, +Y, -Y, +Z, -Z). Does setting G to -Y give a DirectX normal map directly?
# Also: tangent space versus object space on a flat square. Output: out/bake/swizzle_results.json
# Run: blender -b --disable-autoexec -t 2 --python exp2f_normal_swizzle.py
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import exp_common as ec  # noqa: E402

import bpy  # noqa: E402
import numpy as np  # noqa: E402

bh, rt = ec.bh, ec.rt
SIZE = 128
scene, tile = bh.new_bake_scene(SIZE)
group = rt.make_group_tree('h', [('Vector', 'NodeSocketVector', (0, 0, 0))], [('Height', 'NodeSocketFloat')])
tree, w = group
node = w.add('ShaderNodeGroup', 'n')
node.node_tree = rt.tileable_noise_group()
node.inputs['Scale'].default_value = 6.0
node.inputs['Detail'].default_value = 4.0
w.link('in', 'Vector', 'n', 'Vector')
w.link('n', 'Fac', 'out', 'Height')


def material():
    m = bpy.data.materials.new('m')
    m.use_nodes = True
    t = m.node_tree
    t.nodes.clear()
    ww = rt.NodeWriter(t)
    ww.add('ShaderNodeTexCoord', 'coords')
    ww.add('ShaderNodeGroup', 'recipe')
    ww.nodes['recipe'].node_tree = tree
    ww.link('coords', 'UV', 'recipe', 'Vector')
    ww.add('ShaderNodeBump', 'bump', Strength=1.0, Distance=0.05)
    ww.link('recipe', 'Height', 'bump', 'Height')
    ww.add('ShaderNodeBsdfPrincipled', 'bsdf')
    ww.link('bump', 'Normal', 'bsdf', 'Normal')
    ww.add('ShaderNodeOutputMaterial', 'output')
    ww.link('bsdf', 'BSDF', 'output', 'Surface')
    return m


def bake(space='TANGENT', r='POS_X', g='POS_Y', b='POS_Z'):
    m = material()
    tile.data.materials.clear()
    tile.data.materials.append(m)
    image = bpy.data.images.new('n', SIZE, SIZE, alpha=False, float_buffer=True)
    image.colorspace_settings.name = 'Non-Color'
    n = m.node_tree.nodes.new('ShaderNodeTexImage')
    n.image = image
    m.node_tree.nodes.active = n
    bpy.context.view_layer.objects.active = tile
    tile.select_set(True)
    scene.cycles.bake_type = 'NORMAL'
    scene.cycles.samples = 8
    bpy.ops.object.bake(type='NORMAL', normal_space=space, normal_r=r, normal_g=g, normal_b=b, use_clear=True)
    px = np.empty(SIZE * SIZE * 4, np.float32)
    image.pixels.foreach_get(px)
    return px.reshape(SIZE, SIZE, 4)[::-1, :, :3].astype(np.float64)


default = bake()
neg_y = bake(g='NEG_Y')
object_space = bake(space='OBJECT')
results = {
    'default swizzle (+X +Y +Z): green mean': round(float(default[..., 1].mean()), 4),
    'G = -Y: green equals 1 minus the default green (mean abs difference)': round(float(np.abs(neg_y[..., 1] - (1.0 - default[..., 1])).mean()), 5),
    'G = -Y: red and blue unchanged (mean abs difference)': round(float(np.abs(neg_y[..., [0, 2]] - default[..., [0, 2]]).mean()), 5),
    'object space on a flat square facing +Z: mean colour (red, green, blue)': [round(float(x), 4) for x in object_space.reshape(-1, 3).mean(axis=0)],
    'object space vs tangent space on this square: mean abs difference': round(float(np.abs(object_space - default).mean()), 5),
}
json.dump(results, open(os.path.join(ec.OUT, 'bake', 'swizzle_results.json'), 'w'), indent=1)
print(json.dumps(results, indent=1))
