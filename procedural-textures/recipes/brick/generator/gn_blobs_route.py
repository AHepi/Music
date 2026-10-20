# What this does (plain words): a SECOND way to make the paint patches (the "blobs" layer): with Blender's Geometry Nodes instead of building the
# patch outlines in Python. A cloud of points (one per patch, each carrying its radii, turn, colour, raggedness and seed as named numbers) goes into a
# Geometry Nodes tree that (1) puts a little circle at every point, stretched to the patch's two radii and turned, (2) pushes every point of every circle
# in or out with a noise (the ragged edge), (3) hands the patch's colour on to the mesh. The bricks and the outline ring are still made by the normal
# route, so the two pictures can be compared (time to build the geometry, and look). Colour picture only.
# Use:  blender -b --disable-autoexec -t 2 --python gn_blobs_route.py -- DESCRIPTION.json OUT_FOLDER [size]
import json
import math
import os
import sys
import time

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(PROC, 'lib'))
import bake_harness as bh  # noqa: E402
import brick_generator as bg  # noqa: E402
import shape_stack as ss  # noqa: E402


def build_blob_tree(circle_points=28):
    tree = bpy.data.node_groups.new('Paint patches', 'GeometryNodeTree')
    tree.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
    tree.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
    n = tree.nodes
    l = tree.links
    group_in = n.new('NodeGroupInput')
    group_out = n.new('NodeGroupOutput')

    def named(name, data_type):
        node = n.new('GeometryNodeInputNamedAttribute')
        node.data_type = data_type
        node.inputs['Name'].default_value = name
        return node
    rx, ry, ang, col, rag, seed = named('rx', 'FLOAT'), named('ry', 'FLOAT'), named('angle', 'FLOAT'), named('colour', 'FLOAT_COLOR'), named('ragged', 'FLOAT'), named('seed', 'FLOAT')
    cx, cy = named('cx', 'FLOAT'), named('cy', 'FLOAT')
    circle = n.new('GeometryNodeMeshCircle')
    circle.fill_type = 'NGON'
    circle.inputs['Vertices'].default_value = circle_points
    circle.inputs['Radius'].default_value = 1.0
    scale = n.new('ShaderNodeCombineXYZ')
    scale.inputs['Z'].default_value = 1.0
    l.new(rx.outputs['Attribute'], scale.inputs['X'])
    l.new(ry.outputs['Attribute'], scale.inputs['Y'])
    rotation = n.new('ShaderNodeCombineXYZ')
    l.new(ang.outputs['Attribute'], rotation.inputs['Z'])
    instance = n.new('GeometryNodeInstanceOnPoints')
    l.new(group_in.outputs['Geometry'], instance.inputs['Points'])
    l.new(circle.outputs['Mesh'], instance.inputs['Instance'])
    l.new(scale.outputs['Vector'], instance.inputs['Scale'])
    l.new(rotation.outputs['Vector'], instance.inputs['Rotation'])
    realize = n.new('GeometryNodeRealizeInstances')
    l.new(instance.outputs['Instances'], realize.inputs['Geometry'])
    # ragged edge: push each vertex away from / toward its patch centre by a noise (read at the vertex, with the patch's seed as the 4th coordinate)
    position = n.new('GeometryNodeInputPosition')
    noise = n.new('ShaderNodeTexNoise')
    noise.noise_dimensions = '4D'
    noise.inputs['Scale'].default_value = 1254 / 6.0                  # a lump about every 6 dots (the tile is 1 unit wide, so 1254 dots per unit)
    noise.inputs['Detail'].default_value = 2.0
    l.new(position.outputs['Position'], noise.inputs['Vector'])
    l.new(seed.outputs['Attribute'], noise.inputs['W'])
    centre = n.new('ShaderNodeCombineXYZ')
    l.new(cx.outputs['Attribute'], centre.inputs['X'])
    l.new(cy.outputs['Attribute'], centre.inputs['Y'])
    offset_from_centre = n.new('ShaderNodeVectorMath')
    offset_from_centre.operation = 'SUBTRACT'
    l.new(position.outputs['Position'], offset_from_centre.inputs[0])
    l.new(centre.outputs['Vector'], offset_from_centre.inputs[1])
    centre_z_fix = n.new('ShaderNodeVectorMath')
    centre_z_fix.operation = 'MULTIPLY'
    centre_z_fix.inputs[1].default_value = (1.0, 1.0, 0.0)             # radial push only in the picture plane
    l.new(offset_from_centre.outputs['Vector'], centre_z_fix.inputs[0])
    centred_noise = n.new('ShaderNodeMath')
    centred_noise.operation = 'SUBTRACT'
    l.new(noise.outputs['Fac'], centred_noise.inputs[0])
    centred_noise.inputs[1].default_value = 0.5
    strength = n.new('ShaderNodeMath')
    strength.operation = 'MULTIPLY'
    strength.inputs[1].default_value = 2.4
    l.new(centred_noise.outputs['Value'], strength.inputs[0])
    by_ragged = n.new('ShaderNodeMath')
    by_ragged.operation = 'MULTIPLY'
    l.new(strength.outputs['Value'], by_ragged.inputs[0])
    l.new(rag.outputs['Attribute'], by_ragged.inputs[1])
    push = n.new('ShaderNodeVectorMath')
    push.operation = 'SCALE'
    l.new(centre_z_fix.outputs['Vector'], push.inputs[0])
    l.new(by_ragged.outputs['Value'], push.inputs['Scale'])
    set_position = n.new('GeometryNodeSetPosition')
    l.new(realize.outputs['Geometry'], set_position.inputs['Geometry'])
    l.new(push.outputs['Vector'], set_position.inputs['Offset'])
    store = n.new('GeometryNodeStoreNamedAttribute')
    store.data_type = 'FLOAT_COLOR'
    store.domain = 'POINT'
    store.inputs['Name'].default_value = 'Col'
    l.new(set_position.outputs['Geometry'], store.inputs['Geometry'])
    l.new(col.outputs['Attribute'], store.inputs['Value'])
    l.new(store.outputs['Geometry'], group_out.inputs['Geometry'])
    return tree


def main():
    arguments = sys.argv[sys.argv.index('--') + 1:]
    description = json.load(open(arguments[0]))
    out = arguments[1]
    size = int(arguments[2]) if len(arguments) > 2 else 1254
    os.makedirs(out, exist_ok=True)
    started = time.time()
    tile = float(description.get('tile', ss.TILE))
    palette_rgb, palette_rough = ss.palette_info(description)
    linear = bg.srgb_to_linear(palette_rgb / 255.0)
    # parts: everything before the blobs layer (backdrop + bricks), the blobs (GN), and everything after (outline ring)
    layers = description['layers']
    blob_layer = [l for l in layers if l['type'] == 'blobs'][0]
    index = layers.index(blob_layer)
    before = dict(description, layers=layers[:index])
    after = dict(description, layers=layers[index + 1:])
    stack_before = ss.build_shape_stack(before)
    stack_after = ss.build_shape_stack(after)[1:]                  # drop the second backdrop
    scene, tile_object = bh.new_bake_scene(size)
    bpy.data.objects.remove(tile_object)
    scene.cycles.samples = 8
    obj_before, z_before = bg.build_mesh(stack_before, palette_rgb, palette_rough, size, tile=tile)
    # the ring goes above everything: shift its z by building it with a bigger index offset
    items = np.array(blob_layer['items'], float)
    count = len(items)
    t_geo = time.time()
    mesh = bpy.data.meshes.new('patch points')
    z0 = z_before + 1e-4
    mesh.vertices.add(count)
    positions = np.column_stack([items[:, 0] / tile, 1.0 - items[:, 1] / tile, z0 + np.arange(count) * 2e-5])
    mesh.vertices.foreach_set('co', positions.astype(np.float32).ravel())
    def add_float(name, values):
        attribute = mesh.attributes.new(name, 'FLOAT', 'POINT')
        attribute.data.foreach_set('value', np.asarray(values, np.float32))
    add_float('rx', items[:, 2] / tile)
    add_float('ry', items[:, 3] / tile)
    add_float('angle', -np.radians(items[:, 4]))                   # the picture's y goes down, Blender's up: the turn flips
    add_float('ragged', items[:, 6])
    add_float('seed', items[:, 7])
    add_float('cx', items[:, 0] / tile)
    add_float('cy', 1.0 - items[:, 1] / tile)
    colour_attribute = mesh.color_attributes.new('colour', 'FLOAT_COLOR', 'POINT')
    colour_attribute.data.foreach_set('color', np.concatenate([linear[items[:, 5].astype(int)], np.ones((count, 1))], axis=1).astype(np.float32).ravel())
    obj = bpy.data.objects.new('patch points', mesh)
    scene.collection.objects.link(obj)
    modifier = obj.modifiers.new('patches', 'NODES')
    modifier.node_group = build_blob_tree()
    material = bg.channel_material('show colour', 'Col', True)
    # Set Material node so the generated mesh renders (Blender 5.2 needs it)
    tree = modifier.node_group
    set_material = tree.nodes.new('GeometryNodeSetMaterial')
    set_material.inputs['Material'].default_value = material
    last = [lk for lk in tree.links if lk.to_node.bl_idname == 'NodeGroupOutput'][0]
    tree.links.new(last.from_socket, set_material.inputs['Geometry'])
    tree.links.new(set_material.outputs['Geometry'], last.to_socket)
    obj_before.data.materials.append(material)
    # ring (outline) mesh above the patches
    obj_after, z_after = bg.build_mesh([{**s} for s in stack_after], palette_rgb, palette_rough, size, tile=tile)
    for v in obj_after.data.vertices:
        v.co.z += z0 + count * 2e-5 + 1e-4
    obj_after.data.materials.append(material)
    scene.camera.location = (0.5, 0.5, z0 + count * 2e-5 + 1.0)
    scene.camera.data.clip_start = 0.3
    scene.camera.data.clip_end = z0 + count * 2e-5 + 5.0
    bpy.context.view_layer.update()
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh_eval = evaluated.to_mesh()
    geometry_seconds = time.time() - t_geo
    triangles = len(mesh_eval.polygons)
    evaluated.to_mesh_clear()
    bh.render_to(scene, os.path.join(out, 'colour.png'), linear_data=False)
    result = {'patches': count, 'geometry_nodes_seconds_to_build_and_evaluate': round(geometry_seconds, 2), 'faces_from_geometry_nodes': triangles, 'total_seconds': round(time.time() - started, 1)}
    json.dump(result, open(os.path.join(out, 'gn_route.json'), 'w'), indent=1)
    print('[gn route]', json.dumps(result))


if __name__ == '__main__':
    main()
