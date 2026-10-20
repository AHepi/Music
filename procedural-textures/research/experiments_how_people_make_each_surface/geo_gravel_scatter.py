# What this does: TEST of the geometry-nodes way of making gravel that many Blender artists describe (Distribute Points on Faces with the
# Poisson Disk method, then Instance on Points with a random scale and rotation of a lumpy stone) and photographs it from straight above as
# colour and height. It also tests two claims from the web: (1) "Object Info > Random gives only a handful of different values" (a forum post
# said "only 10") and (2) "scattered stones wrap seamlessly" (they do not unless you add copies).
# Run: blender -b --disable-autoexec -t 2 --python geo_gravel_scatter.py -- OUT_FOLDER [--size 512] [--method poisson|random] [--distance 0.04] [--ghosts]
import json
import os
import sys

import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import geo_helpers as gh  # noqa: E402
import bake_harness as bh  # noqa: E402

args = sys.argv[sys.argv.index('--') + 1:]
out = args[0]
option = lambda name, default=None: args[args.index(name) + 1] if name in args else default
size = int(option('--size', 512))
method = option('--method', 'poisson')
distance = float(option('--distance', 0.04))
ghosts = '--ghosts' in args
os.makedirs(out, exist_ok=True)

scene = gh.new_overhead_scene(size)
g = gh.GeoBuilder('scatter stones')
# one lumpy stone: an ico sphere whose vertices are each pushed about by a random amount, then flattened a little
ico = g.make('GeometryNodeMeshIcoSphere', 'Mesh', Radius=0.5, Subdivisions=1)
lumps = g.random_vector((-0.16, -0.16, -0.16), (0.16, 0.16, 0.16), seed=3)
lumpy = g.make('GeometryNodeSetPosition', 'Geometry', Geometry=ico, Offset=lumps)
stone_shape = g.make('GeometryNodeTransform', 'Geometry', Geometry=lumpy, Scale=(1.0, 1.0, 0.7))
stone = g.make('GeometryNodeSetMaterial', 'Geometry', Geometry=stone_shape)
# the ground plane to scatter on (a 1 x 1 grid moved to x 0..1, y 0..1)
grid = g.make('GeometryNodeMeshGrid', 'Mesh', Size__X=1.0, Size__Y=1.0, Vertices__X=2, Vertices__Y=2)
ground = g.make('GeometryNodeTransform', 'Geometry', Geometry=grid, Translation=(0.5, 0.5, 0.0))
points_node = g.make('GeometryNodeDistributePointsOnFaces', 'Points', settings={'distribute_method': 'POISSON' if method == 'poisson' else 'RANDOM'}, Mesh=ground, Seed=4)
node = points_node.node
if method == 'poisson':
    node.inputs['Distance Min'].default_value = distance
    node.inputs['Density Max'].default_value = 4000.0
    node.inputs['Density Factor'].default_value = 1.0
else:
    node.inputs['Density'].default_value = 500.0 if 'Density' in node.inputs else 0
points = points_node
if ghosts:
    # copies of the points moved by one tile in every direction, so stones near an edge also appear on the opposite side
    pieces = []
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            pieces.append(g.make('GeometryNodeTransform', 'Geometry', Geometry=points_node, Translation=(float(dx), float(dy), 0.0)))
    join = g.node('GeometryNodeJoinGeometry')
    for piece in pieces:
        g.tree.links.new(piece, join.inputs['Geometry'])
    points = join.outputs['Geometry']
rotation = g.make('FunctionNodeEulerToRotation', 'Rotation', Euler=g.random_vector((0, 0, 0), (6.283, 6.283, 6.283), seed=5))
scale = g.random_vector((0.030, 0.026, 0.02), (0.070, 0.060, 0.04), seed=6)
instances = g.make('GeometryNodeInstanceOnPoints', 'Instances', Points=points, Instance=stone, Rotation=rotation, Scale=scale)
tree = g.finish(instances)
obj, modifier = gh.add_object_with_tree('stones', tree)
# a flat ground so the picture is not black between the stones
plane_mesh = bpy.data.meshes.new('ground')
plane_mesh.from_pydata([(-1, -1, 0), (2, -1, 0), (2, 2, 0), (-1, 2, 0)], [], [(0, 1, 2, 3)])
plane = bpy.data.objects.new('ground', plane_mesh)
scene.collection.objects.link(plane)

stone_colours = [(0.0, '#16181c'), (0.2, '#1f2228'), (0.4, '#2a2f38'), (0.55, '#38414e'), (0.7, '#4b5967'), (0.85, '#5e7080'), (0.93, '#7d5a3d')]
soil = gh.constant_colour_material('soil', (0.1, 0.045, 0.02, 1.0))
height_ground = gh.height_material(0.0, 0.05)
facts = {'method': method, 'distance': distance, 'ghosts': ghosts, 'size': size}

# colour picture
gh.use_material(stone, gh.instancer_random_colour_material(stone_colours))
gh.set_material(plane, soil)
gh.render_picture(scene, os.path.join(out, 'colour.png'))
# height picture (16 bit, raw)
gh.use_material(stone, gh.height_material(0.0, 0.05))
gh.set_material(plane, gh.height_material(0.0, 0.05))
gh.render_picture(scene, os.path.join(out, 'height.png'), sixteen_bit=True, linear=True)
depsgraph = bpy.context.evaluated_depsgraph_get()
# distances between neighbouring stone centres (poisson claim): distances between instance origins
centres = np.array([inst.matrix_world.translation[:2] for inst in depsgraph.object_instances if inst.is_instance and inst.parent and inst.parent.name == 'stones'])
facts['instances_counted'] = int(len(centres))
if len(centres) > 1:
    inside = centres[(centres[:, 0] >= 0) & (centres[:, 0] <= 1) & (centres[:, 1] >= 0) & (centres[:, 1] <= 1)]
    facts['instances_inside_tile'] = int(len(inside))
    diff = inside[:, None, :] - inside[None, :, :]
    d = np.sqrt((diff ** 2).sum(-1)) + np.eye(len(inside)) * 9
    facts['nearest_neighbour_distance_min'] = float(d.min())
    facts['nearest_neighbour_distance_mean'] = float(d.min(axis=1).mean())
    # across the seam (wrap distance)
    wrap = np.abs(diff)
    wrap = np.minimum(wrap, 1 - wrap)
    dw = np.sqrt((wrap ** 2).sum(-1)) + np.eye(len(inside)) * 9
    facts['nearest_neighbour_distance_min_with_wrap'] = float(dw.min())
json.dump(facts, open(os.path.join(out, 'facts.json'), 'w'), indent=1)
print('FACTS', json.dumps(facts))
