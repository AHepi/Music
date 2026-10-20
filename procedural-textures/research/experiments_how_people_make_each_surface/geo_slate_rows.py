# What this does: TEST of the geometry-nodes way of making slate/roof tiles that commercial add-ons and forum threads describe: a grid of points,
# one instanced slab per point, each row slid by a random amount, every slab with its own random width, tilt and height so that upper rows
# lie over lower rows; photographed from straight above as colour (random blue-grey per slab through Object Info > Random) and height.
# Copies of the slabs one tile away in every direction (ghosts) make it repeat.
# Run: blender -b --disable-autoexec -t 2 --python geo_slate_rows.py -- OUT_FOLDER [--size 512]
import json
import math
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import geo_helpers as gh  # noqa: E402

args = sys.argv[sys.argv.index('--') + 1:]
out = args[0]
size = int(args[args.index('--size') + 1]) if '--size' in args else 512
os.makedirs(out, exist_ok=True)
scene = gh.new_overhead_scene(size)
columns, rows = 7, 8
g = gh.GeoBuilder('slate rows')
slab_mesh = g.make('GeometryNodeMeshCube', 'Mesh', Size=(1.0, 1.0, 1.0))                   # scaled per instance below
slab = g.make('GeometryNodeSetMaterial', 'Geometry', Geometry=slab_mesh)
grid = g.make('GeometryNodeMeshGrid', 'Mesh', Size__X=(columns - 1) / columns, Size__Y=(rows - 1) / rows, Vertices__X=columns, Vertices__Y=rows)
centred = g.make('GeometryNodeTransform', 'Geometry', Geometry=grid, Translation=(0.5, 0.5, 0.0))
position = g.make('GeometryNodeInputPosition', 'Position')
px = g.make('ShaderNodeSeparateXYZ', 0, Vector=position, settings=None)
split = px.node
row_number = g.math('FLOOR', g.math('MULTIPLY', split.outputs['Y'], float(rows)))
row_slide = g.random_float(0.0, 1.0 / columns, seed=11, id_value=row_number)           # one random slide per row (same ID -> same number)
offset = g.combine(row_slide, 0.0, g.math('MULTIPLY', row_number, 0.004))               # upper rows are a little higher: they lie over the lower ones
slid = g.make('GeometryNodeSetPosition', 'Geometry', Geometry=centred, Offset=offset)
points = g.make('GeometryNodeMeshToPoints', 'Points', Mesh=slid, Radius=0.01)
# ghosts: copies of the points one tile away in every direction
join = g.node('GeometryNodeJoinGeometry')
for dx in (-1, 0, 1):
    for dy in (-1, 0, 1):
        piece = g.make('GeometryNodeTransform', 'Geometry', Geometry=points, Translation=(float(dx), float(dy), 0.0))
        g.tree.links.new(piece, join.inputs['Geometry'])
# per-slab random width, height of the slab, tilt
scale = g.combine(g.random_float(0.84 / columns, 0.97 / columns, seed=12), 1.0 / rows * 1.32, 0.006)
rotation = g.make('FunctionNodeEulerToRotation', 'Rotation', Euler=g.combine(g.random_float(-0.035, 0.035, seed=13), g.random_float(-0.02, 0.02, seed=14), g.random_float(-0.03, 0.03, seed=15)))
instances = g.make('GeometryNodeInstanceOnPoints', 'Instances', Points=join.outputs['Geometry'], Instance=slab, Rotation=rotation, Scale=scale)
tree = g.finish(instances)
obj, modifier = gh.add_object_with_tree('slates', tree)
plane_mesh = bpy.data.meshes.new('ground')
plane_mesh.from_pydata([(-1, -1, -0.01), (2, -1, -0.01), (2, 2, -0.01), (-1, 2, -0.01)], [], [(0, 1, 2, 3)])
plane = bpy.data.objects.new('ground', plane_mesh)
scene.collection.objects.link(plane)
gh.set_material(plane, gh.constant_colour_material('dark gap', (0.002, 0.002, 0.003, 1)))
colours = [(0.0, '#2c3236'), (0.2, '#353d42'), (0.4, '#414c52'), (0.6, '#4d5b62'), (0.8, '#5c6d73'), (0.92, '#6b7d85')]
gh.use_material(slab, gh.instancer_random_colour_material(colours))
gh.render_picture(scene, os.path.join(out, 'colour.png'))
gh.use_material(slab, gh.height_material(-0.01, 0.045))
gh.set_material(plane, gh.height_material(-0.01, 0.045))
gh.render_picture(scene, os.path.join(out, 'height.png'), True, True)
json.dump({'columns': columns, 'rows': rows, 'note': 'ghost copies in 3 x 3 tiles'}, open(os.path.join(out, 'facts.json'), 'w'))
print('FACTS ok')
