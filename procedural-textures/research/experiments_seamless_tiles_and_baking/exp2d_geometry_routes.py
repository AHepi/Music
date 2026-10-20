# What this does: experiment 2d. When a texture is made from real geometry (a bumpy grid made by Geometry Nodes, a sculpt, displaced stones) there
# are three ways to get its maps. All three are tried on one bumpy surface whose exact height and exact normal are known (a sum of waves, so it tiles),
# and each result is compared with the exact answer:
#   Route 1  photograph the geometry from straight above with an emission shader showing the surface normal (and the height, from Position Z)
#   Route 2  Cycles Bake > Normal, selected-to-active: from the bumpy "high" mesh onto a flat "low" square with a UV map
#   Route 3  the same bumpy surface made by a Geometry Nodes modifier instead of a Python-made mesh, photographed like route 1
# Also tested: how many vertices per pixel route 1 needs; whether the mesh must reach past the tile edge (the normals at a mesh edge are wrong);
# and Cycles Bake > Ambient Occlusion on the bumpy geometry (a flat square with a Bump node gave a plain white picture in exp2b).
# Output: out/geometry/*.png and out/geometry/results.json
# Run:  blender -b --disable-autoexec -t 2 --python exp2d_geometry_routes.py -- [size]
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
N = int(sys.argv[sys.argv.index('--') + 1]) if '--' in sys.argv and len(sys.argv) > sys.argv.index('--') + 1 else 256
folder = os.path.join(ec.OUT, 'geometry')
os.makedirs(folder, exist_ok=True)
results = {'picture_size': N}

A1, A2 = 0.02, 0.008
FA, FB, FC, FD = 2 * math.pi * 3, 2 * math.pi * 2, 2 * math.pi * 7, 2 * math.pi * 5
P1, P2 = 1.0, 2.0


def height_function(x, y):
    return A1 * np.sin(FA * x) * np.cos(FB * y) + A2 * np.sin(FC * x + P1) * np.sin(FD * y + P2)


def exact_normal(x, y):
    hx = A1 * FA * np.cos(FA * x) * np.cos(FB * y) + A2 * FC * np.cos(FC * x + P1) * np.sin(FD * y + P2)
    hy = -A1 * FB * np.sin(FA * x) * np.sin(FB * y) + A2 * FD * np.sin(FC * x + P1) * np.cos(FD * y + P2)
    n = np.stack([-hx, -hy, np.ones_like(hx)], axis=-1)
    return n / np.linalg.norm(n, axis=-1, keepdims=True)


xs = (np.arange(N) + 0.5) / N
ys = 1.0 - (np.arange(N) + 0.5) / N                      # picture rows run top to bottom, so v runs down from 1 to 0
X, Y = np.meshgrid(xs, ys)
exact_n = exact_normal(X, Y) * 0.5 + 0.5
exact_h = height_function(X, Y)
border = np.zeros((N, N), bool)
border[:2, :] = border[-2:, :] = border[:, :2] = border[:, -2:] = True


def mesh_from_height(vertices_per_side, margin, name):
    """A grid mesh over [-margin, 1+margin]^2 with z = height_function. vertices_per_side counts the vertices across 0..1 (so pixel-sized steps if = N)."""
    step = 1.0 / vertices_per_side
    count = vertices_per_side + 1 + 2 * int(round(margin / step))
    start = -int(round(margin / step)) * step
    gx = start + np.arange(count) * step
    GX, GY = np.meshgrid(gx, gx)
    GZ = height_function(GX, GY)
    verts = np.stack([GX.ravel(), GY.ravel(), GZ.ravel()], axis=-1)
    index = np.arange(count * count).reshape(count, count)
    quads = np.stack([index[:-1, :-1].ravel(), index[:-1, 1:].ravel(), index[1:, 1:].ravel(), index[1:, :-1].ravel()], axis=-1)
    mesh = bpy.data.meshes.new(name)
    mesh.vertices.add(len(verts))
    mesh.vertices.foreach_set('co', verts.astype(np.float32).ravel())
    mesh.loops.add(len(quads) * 4)
    mesh.loops.foreach_set('vertex_index', quads.ravel().astype(np.int32))
    mesh.polygons.add(len(quads))
    mesh.polygons.foreach_set('loop_start', (np.arange(len(quads)) * 4).astype(np.int32))
    mesh.polygons.foreach_set('loop_total', np.full(len(quads), 4, np.int32)) if 'loop_total' in mesh.polygons[0].bl_rna.properties else None
    mesh.update(calc_edges=True)
    mesh.shade_smooth()
    uv = mesh.uv_layers.new(name='UVMap')
    loop_vertices = quads.ravel()
    uv_values = np.stack([verts[loop_vertices, 0], verts[loop_vertices, 1]], axis=-1).astype(np.float32)
    uv.data.foreach_set('uv', uv_values.ravel())
    return mesh


def emission_material(kind):
    material = bpy.data.materials.new('geometry ' + kind)
    material.use_nodes = True
    tree = material.node_tree
    tree.nodes.clear()
    w = rt.NodeWriter(tree)
    w.add('ShaderNodeNewGeometry', 'geo', x=0)
    w.add('ShaderNodeEmission', 'emit', x=4, Strength=1.0)
    w.add('ShaderNodeOutputMaterial', 'output', x=5)
    w.link('emit', 'Emission', 'output', 'Surface')
    if kind == 'normal':
        w.vector_math('half', 'MULTIPLY_ADD', x=1)
        w.nodes['half'].inputs[1].default_value = (0.5, 0.5, 0.5)
        w.nodes['half'].inputs[2].default_value = (0.5, 0.5, 0.5)
        w.link('geo', 'Normal', 'half', 0)
        w.link('half', 0, 'emit', 'Color')
    else:                                                  # height: z of the position, 0.5 = flat, +-0.05 fills the range
        w.add('ShaderNodeSeparateXYZ', 'sep', x=1)
        w.link('geo', 'Position', 'sep', 'Vector')
        w.math('scale', 'MULTIPLY_ADD', None, 10.0, x=2)
        w.nodes['scale'].inputs[2].default_value = 0.5
        w.link('sep', 'Z', 'scale', 0)
        w.add('ShaderNodeCombineColor', 'grey', x=3)
        for socket in ('Red', 'Green', 'Blue'):
            w.link('scale', 0, 'grey', socket)
        w.link('grey', 'Color', 'emit', 'Color')
    return material


def photograph(scene, path):
    scene.cycles.samples = 8
    bh.render_to(scene, path, True, True)
    return bh.load_png_as_array(path)


def normal_error(picture, mask=None):
    difference = np.abs(picture - exact_n)
    if mask is not None:
        return float(difference[mask].mean())
    return float(difference.mean())


def fresh_scene():
    scene, tile = bh.new_bake_scene(N)
    bpy.data.objects.remove(tile)
    return scene


# ---------------------------------------------------------------------------------- Route 1: photograph the geometry; vertices per pixel and edge margin
route1 = {}
for vertices, margin in ((64, 0.0), (128, 0.0), (256, 0.0), (256, 0.0625), (512, 0.0625)):
    scene = fresh_scene()
    mesh = mesh_from_height(vertices, margin, f'hf{vertices}')
    obj = bpy.data.objects.new('hf', mesh)
    scene.collection.objects.link(obj)
    obj.data.materials.append(emission_material('normal'))
    started = time.time()
    picture = photograph(scene, os.path.join(folder, f'route1_normal_v{vertices}_margin{margin}.png'))
    seconds = time.time() - started
    route1[f'{vertices} vertices across, mesh margin {margin}'] = {
        'normal_mean_abs_error_all': round(normal_error(picture), 5), 'normal_mean_abs_error_two_pixel_border': round(normal_error(picture, border), 5),
        'normal_mean_abs_error_inside': round(normal_error(picture, ~border), 5), 'seconds_to_photograph': round(seconds, 1)}
    if vertices == 256 and margin > 0:
        obj.data.materials.clear()
        obj.data.materials.append(emission_material('height'))
        picture_h = photograph(scene, os.path.join(folder, 'route1_height_v256.png'))
        height_back = (picture_h[..., 0] - 0.5) / 10.0
        route1['height from Position Z (256 vertices, margin)'] = {'mean_abs_error_in_units_of_the_total_height_range': round(float(np.abs(height_back - exact_h).mean() / (exact_h.max() - exact_h.min())), 5)}
results['route1_photograph_geometry'] = route1

# ---------------------------------------------------------------------------------- Route 2: Cycles bake, selected to active (high mesh onto a flat low square)
scene = fresh_scene()
high_mesh = mesh_from_height(256, 0.0625, 'high')
high = bpy.data.objects.new('high', high_mesh)
scene.collection.objects.link(high)
low_mesh = bpy.data.meshes.new('low')
low_mesh.from_pydata([(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)], [], [(0, 1, 2, 3)])
low_uv = low_mesh.uv_layers.new(name='UVMap')
for loop, uvv in zip(low_mesh.loops, [(0, 0), (1, 0), (1, 1), (0, 1)]):
    low_uv.data[loop.index].uv = uvv
low = bpy.data.objects.new('low', low_mesh)
scene.collection.objects.link(low)
material = bpy.data.materials.new('low material')
material.use_nodes = True
image = bpy.data.images.new('normal_bake', N, N, alpha=False, float_buffer=True)
image.colorspace_settings.name = 'Non-Color'
node = material.node_tree.nodes.new('ShaderNodeTexImage')
node.image = image
material.node_tree.nodes.active = node
low.data.materials.append(material)
scene.cycles.bake_type = 'NORMAL'
scene.cycles.samples = 8
bpy.ops.object.select_all(action='DESELECT')
high.select_set(True)
low.select_set(True)
bpy.context.view_layer.objects.active = low
started = time.time()
bpy.ops.object.bake(type='NORMAL', use_selected_to_active=True, cage_extrusion=0.1, max_ray_distance=0.0, margin=0, normal_space='TANGENT', use_clear=True)
route2_seconds = time.time() - started
pixels = np.empty(N * N * 4, np.float32)
image.pixels.foreach_get(pixels)
baked = pixels.reshape(N, N, 4)[::-1, :, :3].astype(np.float64)
bh.save_array_png(np.clip(baked, 0, 1), os.path.join(folder, 'route2_normal_selected_to_active.png'), sixteen_bit=True)
# what happens when the extrusion (how far above the low mesh the rays start) or the max ray distance is wrong
variants = {}
for extrusion, max_distance in ((0.0, 0.0), (0.01, 0.0), (0.1, 0.0), (0.1, 0.01), (0.1, 0.05)):
    bpy.ops.object.bake(type='NORMAL', use_selected_to_active=True, cage_extrusion=extrusion, max_ray_distance=max_distance, margin=0, normal_space='TANGENT', use_clear=True)
    image.pixels.foreach_get(pixels)
    attempt = pixels.reshape(N, N, 4)[::-1, :, :3].astype(np.float64)
    variants[f'extrusion {extrusion}, max ray distance {max_distance}'] = {'normal_mean_abs_error': round(normal_error(attempt), 5),
                                                                          'pixels_left_empty_or_flat_percent': round(float((np.abs(attempt - np.array([0.5, 0.5, 1.0])).max(axis=-1) < 1e-4).mean() * 100), 1)}
results['route2_variants_of_extrusion_and_ray_distance'] = variants
results['route2_cycles_bake_selected_to_active'] = {'normal_mean_abs_error_all': round(normal_error(baked), 5),
                                                    'normal_mean_abs_error_inside': round(normal_error(baked, ~border), 5), 'seconds': round(route2_seconds, 1),
                                                    'green_mean': round(float(baked[..., 1].mean()), 4)}

# ---------------------------------------------------------------------------------- Ambient occlusion baked on the bumpy geometry itself (it has a UV map)
scene = fresh_scene()
mesh = mesh_from_height(256, 0.0, 'ao_mesh')
obj = bpy.data.objects.new('ao_mesh', mesh)
scene.collection.objects.link(obj)
material = bpy.data.materials.new('ao material')
material.use_nodes = True
image = bpy.data.images.new('ao', N, N, alpha=False, float_buffer=True)
image.colorspace_settings.name = 'Non-Color'
node = material.node_tree.nodes.new('ShaderNodeTexImage')
node.image = image
material.node_tree.nodes.active = node
obj.data.materials.append(material)
scene.world.light_settings.distance = 0.05
scene.cycles.samples = 32
scene.cycles.bake_type = 'AO'
bpy.ops.object.select_all(action='DESELECT')
obj.select_set(True)
bpy.context.view_layer.objects.active = obj
started = time.time()
bpy.ops.object.bake(type='AO', margin=0, use_clear=True)
ao_seconds = time.time() - started
image.pixels.foreach_get(pixels)
ao = pixels.reshape(N, N, 4)[::-1, :, 0].astype(np.float64)
bh.save_array_png(np.clip(ao, 0, 1), os.path.join(folder, 'ao_on_bumpy_geometry.png'), sixteen_bit=False)
results['ao_bake_on_bumpy_geometry'] = {'min': round(float(ao.min()), 3), 'max': round(float(ao.max()), 3), 'mean': round(float(ao.mean()), 3),
                                        'correlation_with_height': round(float(np.corrcoef(ao.ravel(), exact_h.ravel())[0, 1]), 3), 'seconds': round(ao_seconds, 1),
                                        'world_ao_distance_used': 0.05}

# ---------------------------------------------------------------------------------- Route 3: the same surface made by Geometry Nodes
scene = fresh_scene()
gn = bpy.data.node_groups.new('heightfield', 'GeometryNodeTree')
gn.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
gn.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
nodes, links = gn.nodes, gn.links
group_in = nodes.new('NodeGroupInput')
group_out = nodes.new('NodeGroupOutput')
grid = nodes.new('GeometryNodeMeshGrid')
margin = 0.0625
side = 1.0 + 2 * margin
grid.inputs['Size X'].default_value = side
grid.inputs['Size Y'].default_value = side
grid.inputs['Vertices X'].default_value = int(round(side * 256)) + 1
grid.inputs['Vertices Y'].default_value = int(round(side * 256)) + 1
position = nodes.new('GeometryNodeInputPosition')
separate = nodes.new('ShaderNodeSeparateXYZ')
links.new(position.outputs['Position'], separate.inputs['Vector'])


def math(operation, a=None, b=None, c=None):
    node = nodes.new('ShaderNodeMath')
    node.operation = operation
    for index, value in enumerate((a, b, c)):
        if value is None:
            continue
        if isinstance(value, (int, float)):
            node.inputs[index].default_value = float(value)
        else:
            links.new(value, node.inputs[index])
    return node.outputs[0]


x = math('ADD', separate.outputs['X'], 0.5)                 # the grid is centred on the origin; move to 0..1
y = math('ADD', separate.outputs['Y'], 0.5)
term1 = math('MULTIPLY', math('SINE', math('MULTIPLY', x, FA)), math('COSINE', math('MULTIPLY', y, FB)))
term2 = math('MULTIPLY', math('SINE', math('MULTIPLY_ADD', x, FC, P1)), math('SINE', math('MULTIPLY_ADD', y, FD, P2)))
z = math('ADD', math('MULTIPLY', term1, A1), math('MULTIPLY', term2, A2))
combine = nodes.new('ShaderNodeCombineXYZ')
links.new(z, combine.inputs['Z'])
set_position = nodes.new('GeometryNodeSetPosition')
smooth = nodes.new('GeometryNodeSetShadeSmooth')
transform = nodes.new('GeometryNodeTransform')
transform.inputs['Translation'].default_value = (0.5, 0.5, 0.0)
links.new(grid.outputs['Mesh'], set_position.inputs['Geometry'])
links.new(combine.outputs['Vector'], set_position.inputs['Offset'])
links.new(set_position.outputs['Geometry'], smooth.inputs['Geometry'])
links.new(smooth.outputs['Geometry'], transform.inputs['Geometry'])
links.new(transform.outputs['Geometry'], group_out.inputs['Geometry'])
def photograph_gn(variant):
    mesh = bpy.data.meshes.new('gn host')
    obj = bpy.data.objects.new('gn host', mesh)
    scene.collection.objects.link(obj)
    modifier = obj.modifiers.new('heightfield', 'NODES')
    modifier.node_group = gn
    material = emission_material('normal')
    if variant == 'material in the data slot (the usual way)':
        obj.data.materials.append(material)
    elif variant == 'material slot linked to the object':
        obj.data.materials.append(None)
        obj.material_slots[0].link = 'OBJECT'
        obj.material_slots[0].material = material
    else:                                                        # a Set Material node inside the node group
        set_material = nodes.new('GeometryNodeSetMaterial')
        set_material.inputs['Material'].default_value = material
        links.new(transform.outputs['Geometry'], set_material.inputs['Geometry'])
        links.new(set_material.outputs['Geometry'], group_out.inputs['Geometry'])
    started = time.time()
    picture = photograph(scene, os.path.join(folder, 'route3_gn_' + variant.split(' ')[0] + '_' + variant.split(' ')[1] + '.png'))
    result = {'normal_mean_abs_error_all': round(normal_error(picture), 5), 'normal_mean_abs_error_two_pixel_border': round(normal_error(picture, border), 5),
              'seconds_including_modifier': round(time.time() - started, 1)}
    bpy.data.objects.remove(obj)
    return result


route3 = {}
for variant in ('material in the data slot (the usual way)', 'material slot linked to the object', 'Set Material node inside the node group'):
    route3[variant] = photograph_gn(variant)
results['route3_geometry_nodes_photograph'] = route3
bh.save_array_png(exact_n, os.path.join(folder, 'exact_normal.png'), sixteen_bit=True)

with open(os.path.join(folder, 'results.json'), 'w') as handle:
    json.dump(results, handle, indent=1)
print(json.dumps(results, indent=1))
