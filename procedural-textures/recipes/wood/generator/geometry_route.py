# What this does (plain words): the REAL-GEOMETRY ROUTE experiment for the wood. The normal generator draws everything as flat polygons made in numpy. This script draws the same
# sampled description's cracks and splatters with Blender's own geometry tools instead, and compares the two pictures:
#   - CRACKS as Blender CURVE objects: each crack is a poly curve whose points carry a radius (the tapering width); Blender's "bevel" turns it into a ribbon (the curve is
#     flattened, because only the view from above matters). This is the tool people use for cables and roots.
#   - SPLATTER BLOBS with GEOMETRY NODES: a cloud of points (one per blob, with a radius and a colour on each point) is turned into round blobs by "Instance on Points" with a
#     circle, then "Realize Instances" (a node tree built from Python).
# The planks stay as polygons (a plank is a flat band; a curve or a node tree adds nothing). Both routes are photographed from above in the same way.
# It writes outputs/geometry_route/{polygon_route,geometry_route}/colour.png, difference picture and geometry_route_report.json (time, SSIM, mean difference).
# Use: blender -b --disable-autoexec -t 2 --python geometry_route.py -- OUT_FOLDER [seed]
import json
import os
import sys
import time

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import wood_generator as wg  # noqa: E402  (also puts the project's lib folder on the path)
import bake_harness as bh  # noqa: E402
import sampler  # noqa: E402
import wood_layers as wl  # noqa: E402

arguments = sys.argv[sys.argv.index('--') + 1:]
out_root = arguments[0]
seed = int(arguments[1]) if len(arguments) > 1 else 5
os.makedirs(out_root, exist_ok=True)
SIZE = 1254

full = sampler.sample_description(seed)
keep = ('plank_rows', 'blobs', 'crack_field', 'gap_ribbons')
description = dict(full, layers=[l for l in full['layers'] if l['type'] in keep])
description['maps'] = {'height': {'grey_low': 12.0, 'grey_high': 128.0, 'blur': 0.5, 'mode': 'from_colour'}, 'normal': {'strength': 8}}
tile = float(description['tile'])

# ---------------------------------------------------------------------------------------------- route 1: flat polygons (what the generator does)
t0 = time.time()
wg.bake_description(description, os.path.join(out_root, 'polygon_route'), size=SIZE, samples=16, quiet=True, with_ao=False)
polygon_seconds = round(time.time() - t0, 1)

# ---------------------------------------------------------------------------------------------- route 2: planks as polygons, cracks as curves, blobs by geometry nodes
t0 = time.time()
scene, plane = bh.new_bake_scene(SIZE)
bpy.data.objects.remove(plane)
linear, grey, rough, metal = wg.palette_attributes(description)
palette = description['palette']
rows = layers_rows = wl.board_rows_of(description['layers'], tile)
gaps = wl.gap_geometry(description['layers'], tile)


def emission_material(name, rgb255):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    tree = material.node_tree
    tree.nodes.clear()
    emit = tree.nodes.new('ShaderNodeEmission')
    emit.inputs['Color'].default_value = (*wg.srgb_to_linear(np.array(rgb255) / 255.0), 1.0)
    out = tree.nodes.new('ShaderNodeOutputMaterial')
    tree.links.new(emit.outputs['Emission'], out.inputs['Surface'])
    return material


# planks (polygons) at z = 0 .. small
shapes = []
for layer in description['layers']:
    if layer['type'] == 'plank_rows':
        shapes += wl.expand_boards(layer, tile, None) if layer.get('boards') else wl.expand_plank_rows(layer, tile, None)
mesh, count, faces = wg.build_tile_mesh([(polys, idx) for polys, idx in shapes], dict(description), (0.0, 0.0))
plank_object = bpy.data.objects.new('planks', mesh)
scene.collection.objects.link(plank_object)
plank_object.data.materials.append(wg.channel_material('Colour', description))
plank_object.location.z = 0.0

# cracks and gap ribbons as curves, one object per line, all drawn above the planks
crack_layer = next(l for l in description['layers'] if l['type'] == 'crack_field')
lines = wl.crack_polylines(crack_layer, tile, gaps, rows)
gap_layer = next(l for l in description['layers'] if l['type'] == 'gap_ribbons')
for g in gaps:
    lines.append([[float(x), float(y), float(w) * gap_layer.get('width_scale', 1.0)] for x, y, w in zip(g['x'], g['y'], g['w'])])
dark = emission_material('crack colour', palette[int(crack_layer['colour'])])
curve_count = 0
for line in lines:
    curve = bpy.data.curves.new('crack', 'CURVE')
    curve.dimensions = '3D'
    curve.bevel_depth = 1.0               # the radius of every point is the half width in tile units: width = 2 x bevel depth x point radius
    curve.bevel_resolution = 0
    curve.use_fill_caps = False
    spline = curve.splines.new('POLY')
    spline.points.add(len(line) - 1)
    for point, (x, y, w) in zip(spline.points, line):
        point.co = (x / tile, 1.0 - y / tile, 0.0, 1.0)
        point.radius = max(w, 1.0) / 2.0 / tile
    obj = bpy.data.objects.new('crack', curve)
    obj.scale.z = 1e-4                    # flatten: only the view from above matters
    obj.location.z = 0.01
    obj.data.materials.append(dark)
    scene.collection.objects.link(obj)
    curve_count += 1

# splatter blobs by geometry nodes: points with a radius and a colour -> circles
blobs = wl.blob_list(next(l for l in description['layers'] if l['type'] == 'blobs'), tile, np.random.default_rng(1))
blob_mesh = bpy.data.meshes.new('blob points')
blob_mesh.from_pydata([(x / tile, 1.0 - y / tile, 0.0) for _, x, y, r in blobs], [], [])
radius_attribute = blob_mesh.attributes.new('radius', 'FLOAT', 'POINT')
radius_attribute.data.foreach_set('value', np.array([r / tile for _, x, y, r in blobs], np.float32))
colour_attribute = blob_mesh.attributes.new('piece_colour', 'FLOAT_COLOR', 'POINT')
rgba = np.ones((len(blobs), 4), np.float32)
rgba[:, :3] = linear[[c for c, _, _, _ in blobs]]
colour_attribute.data.foreach_set('color', rgba.ravel())
blob_object = bpy.data.objects.new('blobs', blob_mesh)
blob_object.location.z = 0.005
scene.collection.objects.link(blob_object)
tree = bpy.data.node_groups.new('Blob circles', 'GeometryNodeTree')
tree.interface.new_socket('Geometry', in_out='INPUT', socket_type='NodeSocketGeometry')
tree.interface.new_socket('Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
nodes, links = tree.nodes, tree.links
group_in, group_out = nodes.new('NodeGroupInput'), nodes.new('NodeGroupOutput')
circle = nodes.new('GeometryNodeMeshCircle')
circle.fill_type = 'NGON'
circle.inputs['Vertices'].default_value = 12
instance = nodes.new('GeometryNodeInstanceOnPoints')
radius_in = nodes.new('GeometryNodeInputNamedAttribute')
radius_in.data_type = 'FLOAT'
radius_in.inputs['Name'].default_value = 'radius'
combine = nodes.new('ShaderNodeCombineXYZ')
combine.inputs['Z'].default_value = 1.0
realize = nodes.new('GeometryNodeRealizeInstances')
set_material = nodes.new('GeometryNodeSetMaterial')
blob_material = wg.channel_material('Colour', description)
set_material.inputs['Material'].default_value = blob_material
links.new(circle.outputs['Mesh'], instance.inputs['Instance'])
links.new(group_in.outputs['Geometry'], instance.inputs['Points'])
links.new(radius_in.outputs['Attribute'], combine.inputs['X'])
links.new(radius_in.outputs['Attribute'], combine.inputs['Y'])
links.new(combine.outputs['Vector'], instance.inputs['Scale'])
links.new(instance.outputs['Instances'], realize.inputs['Geometry'])
links.new(realize.outputs['Geometry'], set_material.inputs['Geometry'])
links.new(set_material.outputs['Geometry'], group_out.inputs['Geometry'])
modifier = blob_object.modifiers.new('blobs', 'NODES')
modifier.node_group = tree
# the colour of each blob is read from the point attribute piece_colour (propagated by the nodes onto the realised circles)
scene.camera.location.z = 5.0
timings = {}
wg.photograph(scene, plank_object, wg.channel_material('Colour', description), os.path.join(out_root, 'geometry_route_colour.png'), False, False, 16)
for obj in (blob_object,):
    obj.data.materials.clear()
geometry_seconds = round(time.time() - t0, 1)
os.makedirs(os.path.join(out_root, 'geometry_route'), exist_ok=True)
os.replace(os.path.join(out_root, 'geometry_route_colour.png'), os.path.join(out_root, 'geometry_route', 'colour.png'))

# ---------------------------------------------------------------------------------------------- compare the two pictures
a = bh.load_png_as_array(os.path.join(out_root, 'polygon_route', 'colour.png'))
b = bh.load_png_as_array(os.path.join(out_root, 'geometry_route', 'colour.png'))
difference = np.abs(a - b).mean(axis=-1) * 255.0
report = {'seed': seed, 'polygon_route_seconds_total': polygon_seconds, 'geometry_route_seconds_total': geometry_seconds, 'curves': curve_count, 'blobs': len(blobs),
          'mean_difference_levels': round(float(difference.mean()), 3), 'share_of_dots_differing_over_40': round(float((difference > 40).mean()), 4)}
bh.save_array_png(np.clip(difference / 128.0, 0, 1), os.path.join(out_root, 'difference.png'))
json.dump(report, open(os.path.join(out_root, 'geometry_route_report.json'), 'w'), indent=1)
print('[geometry route]', json.dumps(report))
