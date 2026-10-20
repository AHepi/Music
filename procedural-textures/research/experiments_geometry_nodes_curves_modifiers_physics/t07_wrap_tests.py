# What this does: proves (or disproves) that the geometry recipes wrap. For each recipe it bakes the HEIGHT picture twice, with the wrap-around copies ON and OFF
# (the recipes have a 'wrap' setting), and also tests displacing a plane with Blender's plain Noise node versus the tileable noise group.
# Afterwards  measure_wrap.py  measures the seam of every picture and draws the pictures shifted by half a tile (a seam shows up as a cross in the middle).
# Run: blender -b --disable-autoexec -t 2 --python t07_wrap_tests.py
import json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import bpy, numpy as np
import gn_tools as gt
import recipe_brick_layout as rb, recipe_slate_layout as rs, recipe_curve_ruts as rr
OUT = os.path.join(HERE, 'out', 't07_wrap'); os.makedirs(OUT, exist_ok=True)
SIZE = 512
def only_height(obj, name):
    scene = bpy.context.scene
    low, high, _ = gt.z_range(obj)
    gt.render_with(scene, obj, gt.height_material(low, high), os.path.join(OUT, name + '.png'), True, True)
for wrap in (True, False):
    tag = 'wrap' if wrap else 'nowrap'
    gt.new_scene(SIZE); obj, _ = gt.add_geometry_object('brick', rb.build_wall_group({**rb.DEFAULTS, 'wrap': wrap, 'subdiv': 2})); only_height(obj, f'brick_{tag}')
    gt.new_scene(SIZE); obj, _ = gt.add_geometry_object('slate', rs.build_roof_group({**rs.DEFAULTS, 'wrap': wrap, 'subdiv': 2})); only_height(obj, f'slate_{tag}')
    gt.new_scene(SIZE); obj, _ = gt.add_geometry_object('ruts', rr.build_mud_group({**rr.DEFAULTS, 'wrap': wrap, 'grid': 256})); only_height(obj, f'ruts_{tag}')
# plain noise vs tileable noise on a plane
for kind in ('plain Blender noise', 'tileable noise group'):
    gt.new_scene(SIZE)
    tree, g = gt.make_geometry_group('noise plane', [('Geometry', 'NodeSocketGeometry', None)])
    g.node('GeometryNodeMeshGrid', 'grid', {'Size X': 1.0, 'Size Y': 1.0, 'Vertices X': 256, 'Vertices Y': 256})
    g.node('GeometryNodeTransform', 'move', {'Geometry': ('grid', 'Mesh'), 'Translation': (0.5, 0.5, 0.0)})
    g.node('GeometryNodeInputPosition', 'pos')
    if kind.startswith('plain'):
        g.node('ShaderNodeTexNoise', 'noise', {'Vector': ('pos', 'Position'), 'Scale': 6.0, 'Detail': 4.0}, noise_dimensions='3D', normalize=True)
        value = ('noise', 'Fac')
    else:
        g.group('noise', gt.tileable_noise_geo_group(), {'Position': ('pos', 'Position'), 'Scale': 6.0, 'Detail': 4.0})
        value = ('noise', 'Fac')
    g.math('z', 'MULTIPLY', value, 0.1)
    g.node('ShaderNodeCombineXYZ', 'lift', {'Z': ('z', 0)})
    g.node('GeometryNodeSetPosition', 'bumpy', {'Geometry': ('move', 'Geometry'), 'Offset': ('lift', 'Vector')})
    gt.finish_with_material_slot(g, 'bumpy')
    obj, _ = gt.add_geometry_object('plane', tree)
    only_height(obj, 'noise_plain' if kind.startswith('plain') else 'noise_tileable')
print('done')
