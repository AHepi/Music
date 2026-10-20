# What this does: TEST of "how do I give every instance its own random colour in Blender 5.2?". 200 instanced cubes are scattered in a Geometry Nodes
# object; three ways of reading a per-instance random number in the material are rendered as grey pictures and the number of different grey values
# on the cubes is counted:  (A) Object Info > Random,  (B) Object Info > Location through a White Noise texture (the forum trick),
# (C) a Store Named Attribute on the INSTANCE domain read back with the Attribute node set to 'Instancer'.
# Run: blender -b --disable-autoexec -t 2 --python geo_instance_random_test.py -- OUT_FOLDER
import json
import os
import sys

import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import geo_helpers as gh  # noqa: E402

out = sys.argv[sys.argv.index('--') + 1]
os.makedirs(out, exist_ok=True)
scene = gh.new_overhead_scene(384)
g = gh.GeoBuilder('instances test')
cube_mesh = g.make('GeometryNodeMeshCube', 'Mesh', Size=(0.05, 0.05, 0.02))
cube = g.make('GeometryNodeSetMaterial', 'Geometry', Geometry=cube_mesh)
grid = g.make('GeometryNodeMeshGrid', 'Mesh', Size__X=0.95, Size__Y=0.95, Vertices__X=14, Vertices__Y=14)
moved = g.make('GeometryNodeTransform', 'Geometry', Geometry=grid, Translation=(0.5, 0.5, 0.0))
points = g.make('GeometryNodeMeshToPoints', 'Points', Mesh=moved, Radius=0.01)
instances = g.make('GeometryNodeInstanceOnPoints', 'Instances', Points=points, Instance=cube)
store_node = g.node('GeometryNodeStoreNamedAttribute', data_type='FLOAT', domain='INSTANCE')
g.tree.links.new(instances, store_node.inputs['Geometry'])
store_node.inputs['Name'].default_value = 'rnd'
g.put(store_node, 'Value', g.random_float(0.0, 1.0, seed=2))
tree = g.finish(store_node.outputs['Geometry'])
obj, modifier = gh.add_object_with_tree('cubes', tree)
facts = {'instances': 14 * 14}


def count(path):
    image = bpy.data.images.load(path, check_existing=False)
    image.colorspace_settings.name = 'Non-Color'
    pixels = np.empty(image.size[0] * image.size[1] * 4, dtype=np.float32)
    image.pixels.foreach_get(pixels)
    red = pixels.reshape(image.size[1], image.size[0], 4)[..., 0]
    values = np.round(red[red > 0] * 65535).astype(int)
    unique, counts = np.unique(values, return_counts=True)
    big = counts >= 30
    return {'distinct_values_on_at_least_30_pixels': int(big.sum()), 'min': float(unique[big].min() / 65535) if big.any() else None,
            'max': float(unique[big].max() / 65535) if big.any() else None}


# A: Object Info > Random
gh.use_material(cube, gh.random_grey_material())
gh.render_picture(scene, os.path.join(out, 'A_object_info_random.png'), True, True)
facts['A_object_info_random'] = count(os.path.join(out, 'A_object_info_random.png'))


# B: Object Info > Location -> White Noise
def build_b(tree):
    info = tree.nodes.new('ShaderNodeObjectInfo')
    noise = tree.nodes.new('ShaderNodeTexWhiteNoise')
    noise.noise_dimensions = '3D'
    tree.links.new(info.outputs['Location'], noise.inputs['Vector'])
    grey = tree.nodes.new('ShaderNodeCombineColor')
    for socket in ('Red', 'Green', 'Blue'):
        tree.links.new(noise.outputs['Value'], grey.inputs[socket])
    return grey.outputs[0]


gh.use_material(cube, gh.emission_material('location noise', build_b))
gh.render_picture(scene, os.path.join(out, 'B_location_white_noise.png'), True, True)
facts['B_location_white_noise'] = count(os.path.join(out, 'B_location_white_noise.png'))


# C: Attribute node, type Instancer, name rnd
def build_c(tree):
    attribute = tree.nodes.new('ShaderNodeAttribute')
    attribute.attribute_type = 'INSTANCER'
    attribute.attribute_name = 'rnd'
    grey = tree.nodes.new('ShaderNodeCombineColor')
    for socket in ('Red', 'Green', 'Blue'):
        tree.links.new(attribute.outputs['Fac'], grey.inputs[socket])
    return grey.outputs[0]


gh.use_material(cube, gh.emission_material('instancer attribute', build_c))
gh.render_picture(scene, os.path.join(out, 'C_instancer_attribute.png'), True, True)
facts['C_instancer_attribute'] = count(os.path.join(out, 'C_instancer_attribute.png'))
json.dump(facts, open(os.path.join(out, 'facts.json'), 'w'), indent=1)
print('FACTS', json.dumps(facts))
