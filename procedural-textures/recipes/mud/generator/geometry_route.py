# What this does (plain words): the REAL-GEOMETRY ROUTE experiment for the mud. The normal generator draws everything as flat coloured polygons. This script draws the same
# things with Blender's own geometry tools and compares the pictures:
#   - STONES as real little rocks made by GEOMETRY NODES: one point per stone (position, radius, colour) -> "Instance on Points" puts a low-poly ball (an ico sphere) on every
#     point, turned a random way and flattened -> "Set Position" pushes every corner in or out by noise (so each stone is an irregular faceted lump) -> flat shading. A sun from the
#     upper left lights them, so every stone gets a lit face and a shaded face for free (the flat-polygon route has to invent those faces).
#   - WHEEL RUTS as Blender CURVE objects: each rut is a curve through its points; "bevel depth" gives it width (a tube seen from above is a ribbon).
# Both are photographed from straight above and set beside the polygon route for the SAME description. It writes outputs/geometry_route/<name>/colour.png, report.json (time per
# route) and the sheets. Use: blender -b --disable-autoexec -t 2 --python geometry_route.py -- DESCRIPTION.json OUT_FOLDER [size]
import json
import math
import os
import sys
import time

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(PROC, 'lib')); sys.path.insert(0, os.path.join(PROC, 'lib', 'contrib')); sys.path.insert(0, HERE)
import bake_harness as bh  # noqa: E402
import gn_tools as gt  # noqa: E402
import mud_generator as mg  # noqa: E402
import mud_layers as ml  # noqa: E402

arguments = sys.argv[sys.argv.index('--') + 1:]
description = json.load(open(arguments[0]))
out_root = arguments[1]
SIZE = int(arguments[2]) if len(arguments) > 2 else 1254
os.makedirs(out_root, exist_ok=True)
tile = float(description['tile'])
palette = np.array(description['palette'], np.float64) / 255.0
linear = mg.srgb_to_linear(palette)
report = {}


def emission_material(name, rgb_linear):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    tree = material.node_tree
    tree.nodes.clear()
    emit = tree.nodes.new('ShaderNodeEmission')
    emit.inputs['Color'].default_value = (*rgb_linear, 1.0)
    out = tree.nodes.new('ShaderNodeOutputMaterial')
    tree.links.new(emit.outputs['Emission'], out.inputs['Surface'])
    return material


def polygon_area(p):
    x, y = p[:, 0], p[:, 1]
    return 0.5 * abs(float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))))


# ------------------------------------------------------------------------------------------------ stones: the data every route uses
stones_layer = next(l for l in description['layers'] if l['type'] == 'stones')
stone_data = []
for base, outline, faces in stones_layer['items']:
    pts = ml.decode(outline).astype(np.float64)
    stone_data.append((pts.mean(axis=0), math.sqrt(polygon_area(pts) / math.pi), int(base)))
ground_colour = int(description['ground']['colour'])


def new_ground_scene():
    scene = gt.new_scene(SIZE)
    ground_mesh = bpy.data.meshes.new('ground')
    ground_mesh.from_pydata([(0, 0, -0.001), (1, 0, -0.001), (1, 1, -0.001), (0, 1, -0.001)], [], [(0, 1, 2, 3)])
    ground = bpy.data.objects.new('ground', ground_mesh)
    ground_mesh.materials.append(emission_material('ground colour', linear[ground_colour]))
    scene.collection.objects.link(ground)
    return scene


# ------------------------------------------------------------------------------------------------ route A: flat polygons (what the generator does)
started = time.time()
scene = new_ground_scene()
stone_only = {'tile': description['tile'], 'palette': description['palette'], 'ground': description['ground'], 'layers': [stones_layer], 'maps': description['maps']}
mesh, count, faces = mg.build_tile_mesh(ml.make_shape_list(stone_only)[1:], stone_only)
obj = bpy.data.objects.new('stones polygons', mesh)
scene.collection.objects.link(obj)
scene.camera.location.z = count * mg.Z_STEP + 2.0
scene.camera.data.clip_end = count * mg.Z_STEP + 10.0
mg.photograph(scene, obj, mg.channel_material('Colour'), os.path.join(out_root, 'stones_polygons.png'), False, False, 8)
report['stones_polygon_route_seconds'] = round(time.time() - started, 1)
report['stones_polygon_route_shapes'] = count

# ------------------------------------------------------------------------------------------------ route B: geometry nodes rocks lit by a sun
started = time.time()
scene = new_ground_scene()
points = bpy.data.meshes.new('stone points')
points.from_pydata([(c[0] / tile, 1.0 - c[1] / tile, 0.0) for c, r, b in stone_data], [], [])
radius_attr = points.attributes.new('stone_size', 'FLOAT', 'POINT')
radius_attr.data.foreach_set('value', np.array([r / tile for c, r, b in stone_data], np.float32))
tone_attr = points.attributes.new('tone', 'FLOAT_COLOR', 'POINT')
colours = np.ones((len(stone_data), 4), np.float32)
colours[:, :3] = np.array([linear[b] for c, r, b in stone_data], np.float32)
tone_attr.data.foreach_set('color', colours.ravel())
tree, g = gt.make_geometry_group('Mud stones', [('Geometry', 'NodeSocketGeometry', None), ('Lump', 'NodeSocketFloat', 0.9), ('Squash', 'NodeSocketFloat', 0.55)])
g.node('GeometryNodeMeshToPoints', 'to points', {'Mesh': ('in', 'Geometry')}, mode='VERTICES')
g.node('GeometryNodeMeshIcoSphere', 'ball', {'Radius': 1.0, 'Subdivisions': 1})
g.node('GeometryNodeInputNamedAttribute', 'radius in', {'Name': 'stone_size'}, data_type='FLOAT')
g.node('ShaderNodeCombineXYZ', 'size xyz', {'X': ('radius in', 'Attribute'), 'Y': ('radius in', 'Attribute')})
g.node('ShaderNodeMath', 'height', {0: ('radius in', 'Attribute'), 1: ('in', 'Squash')}, operation='MULTIPLY')
g.link('height', 0, 'size xyz', 'Z')
g.node('FunctionNodeRandomValue', 'turn', {'Min': (0.0, 0.0, 0.0), 'Max': (0.0, 0.0, 6.283)}, data_type='FLOAT_VECTOR')
g.node('GeometryNodeInstanceOnPoints', 'rocks', {'Points': ('to points', 'Points'), 'Instance': ('ball', 'Mesh'), 'Rotation': ('turn', 'Value'), 'Scale': ('size xyz', 'Vector')})
g.node('GeometryNodeRealizeInstances', 'realize', {'Geometry': ('rocks', 'Instances')})
g.node('GeometryNodeInputPosition', 'where')
g.node('ShaderNodeTexNoise', 'lump noise', {'Scale': 2.2, 'Detail': 0.0, 'Vector': ('where', 'Position')}, noise_dimensions='3D')
g.node('ShaderNodeVectorMath', 'centred', {0: ('lump noise', 'Color'), 1: (0.5, 0.5, 0.5)}, operation='SUBTRACT')
g.node('FunctionNodeRandomValue', 'per corner', {'Min': -0.5, 'Max': 0.5, 'ID': ('where', 'Position')}, data_type='FLOAT')
g.node('GeometryNodeInputNamedAttribute', 'radius out', {'Name': 'stone_size'}, data_type='FLOAT')
g.node('ShaderNodeMath', 'push size', {0: ('radius out', 'Attribute'), 1: ('in', 'Lump')}, operation='MULTIPLY')
g.node('ShaderNodeVectorMath', 'pushed', {0: ('centred', 'Vector'), 'Scale': ('push size', 0)}, operation='SCALE')
g.node('GeometryNodeSetPosition', 'lumpy', {'Geometry': ('realize', 'Geometry'), 'Offset': ('pushed', 'Vector')})
g.node('GeometryNodeSetShadeSmooth', 'flat', {'Geometry': ('lumpy', 'Geometry'), 'Shade Smooth': False})
gt.finish_with_material_slot(g, 'flat')
points_object, modifier = gt.add_geometry_object('stones geometry nodes', tree, points)
# the rocks need a lit material: diffuse colour from the point attribute, a sun from the upper left, a little sky light
material = bpy.data.materials.new('rock paint')
material.use_nodes = True
mt = material.node_tree
mt.nodes.clear()
attr = mt.nodes.new('ShaderNodeAttribute'); attr.attribute_name = 'tone'; attr.attribute_type = 'GEOMETRY'
diffuse = mt.nodes.new('ShaderNodeBsdfDiffuse')
out = mt.nodes.new('ShaderNodeOutputMaterial')
mt.links.new(attr.outputs['Color'], diffuse.inputs['Color']); mt.links.new(diffuse.outputs['BSDF'], out.inputs['Surface'])
points_object.modifiers[0].node_group.nodes['show material'].inputs['Material'].default_value = material
sun = bpy.data.lights.new('sun', 'SUN'); sun.energy = math.pi * 0.95; sun.angle = 0.02
sun_object = bpy.data.objects.new('sun', sun)
sun_object.rotation_euler = (math.radians(42), math.radians(-30), math.radians(-45))       # light comes from the upper left of the picture
scene.collection.objects.link(sun_object)
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.5, 0.5, 0.55, 1.0)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.5
scene.cycles.samples = 16
bh.render_to(scene, os.path.join(out_root, 'stones_geometry_nodes.png'), False, False)
report['stones_geometry_nodes_seconds'] = round(time.time() - started, 1)
report['stones_geometry_nodes_vertices'] = len(gt.evaluated_vertices(points_object))

# ------------------------------------------------------------------------------------------------ ruts: polygons vs curve objects
ruts_layer = next((l for l in description['layers'] if l['type'] == 'ruts'), None)
if ruts_layer:
    started = time.time()
    scene = new_ground_scene()
    rut_only = {'tile': description['tile'], 'palette': description['palette'], 'ground': description['ground'], 'layers': [dict(ruts_layer, wobble=0.0)], 'maps': description['maps'], 'seed': 1}
    mesh, count, faces = mg.build_tile_mesh(ml.make_shape_list(rut_only)[1:], rut_only)
    obj = bpy.data.objects.new('ruts polygons', mesh)
    scene.collection.objects.link(obj)
    mg.photograph(scene, obj, mg.channel_material('Colour'), os.path.join(out_root, 'ruts_polygons.png'), False, False, 8)
    report['ruts_polygon_route_seconds'] = round(time.time() - started, 1)
    started = time.time()
    scene = new_ground_scene()
    z = 0.0
    for item in ruts_layer['items']:
        for key, width_key in (('band', 'w'), ('groove', 'gw')):
            if item.get(key, -1) < 0:
                continue
            z += 1e-5
            curve = bpy.data.curves.new('rut', 'CURVE')
            curve.dimensions = '3D'
            curve.bevel_depth = float(item[width_key]) / 2.0 / tile
            curve.bevel_resolution = 1
            curve.use_fill_caps = True
            spline = curve.splines.new('POLY')
            pts = ml.chaikin(np.asarray(item['p'], np.float64), 2)
            spline.points.add(len(pts) - 1)
            for point, (x, y) in zip(spline.points, pts):
                point.co = (x / tile, 1.0 - y / tile, z, 1.0)
            curve_object = bpy.data.objects.new('rut', curve)
            curve_object.scale = (1, 1, 0.02)
            curve.materials.append(emission_material('rut ' + key, linear[item[key]]))
            scene.collection.objects.link(curve_object)
    scene.cycles.samples = 8
    bh.render_to(scene, os.path.join(out_root, 'ruts_curve_objects.png'), False, False)
    report['ruts_curve_route_seconds'] = round(time.time() - started, 1)
json.dump(report, open(os.path.join(out_root, 'report.json'), 'w'), indent=1)
print('[geometry route]', json.dumps(report))
