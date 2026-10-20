# What this does: builds the six surface recipes as shader node groups and saves them in ONE Blender file with a small demo scene (six planes in a row, each with a material
# that uses its recipe through a Principled BSDF, plus a Bump node made from the recipe's Height), so you can open it in Blender and look at the nodes.
# The node groups are also kept (fake user) so you can use them in your own materials: Add > Group > "Recipe brick" and so on. Their input 'Vector' is the UV coordinate.
# Run: blender -b --disable-autoexec --python save_recipes_blend.py -- recipes/six_surface_recipes.blend
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, 'recipes'))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, '..', '..', 'lib')))
import importlib

out_path = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_homefile(use_empty=True, use_factory_startup=True)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
x = 0.0
for index, name in enumerate(['brick', 'slate', 'wood', 'metal', 'mud', 'gravel']):
    module = importlib.import_module('recipe_' + name)
    group = module.build_node_group({})
    group.name = 'Recipe ' + name
    group.use_fake_user = True
    material = bpy.data.materials.new('Surface ' + name)
    tree = material.node_tree
    tree.nodes.clear()
    coords = tree.nodes.new('ShaderNodeTexCoord')
    node = tree.nodes.new('ShaderNodeGroup')
    node.node_tree = group
    bump = tree.nodes.new('ShaderNodeBump')
    bump.inputs['Distance'].default_value = 0.02
    bsdf = tree.nodes.new('ShaderNodeBsdfPrincipled')
    output = tree.nodes.new('ShaderNodeOutputMaterial')
    for i, n in enumerate((coords, node, bump, bsdf, output)):
        n.location = (i * 260, 0)
    tree.links.new(coords.outputs['UV'], node.inputs['Vector'])
    tree.links.new(node.outputs['Colour'], bsdf.inputs['Base Color'])
    tree.links.new(node.outputs['Roughness'], bsdf.inputs['Roughness'])
    tree.links.new(node.outputs['Metallic'], bsdf.inputs['Metallic'])
    tree.links.new(node.outputs['Height'], bump.inputs['Height'])
    tree.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    mesh = bpy.data.meshes.new('plane ' + name)
    mesh.from_pydata([(x, 0, 0), (x + 1, 0, 0), (x + 1, 1, 0), (x, 1, 0)], [], [(0, 1, 2, 3)])
    uv = mesh.uv_layers.new(name='UVMap')
    for loop, coord in zip(mesh.loops, [(0, 0), (1, 0), (1, 1), (0, 1)]):
        uv.data[loop.index].uv = coord
    mesh.materials.append(material)
    obj = bpy.data.objects.new('Surface ' + name, mesh)
    scene.collection.objects.link(obj)
    x += 1.1
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out_path))
print('SAVED', out_path)
