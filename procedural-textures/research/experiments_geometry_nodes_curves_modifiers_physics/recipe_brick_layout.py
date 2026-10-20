# What this does: RECIPE 1 - builds a brick wall out of REAL bricks with Geometry Nodes, then photographs it from straight above to get a
# height picture, a colour picture and normal pictures of a 1 x 1 seamless tile. Nothing here uses a picture as input.
# Chain (read it top to bottom in the Geometry Node editor):
#   Row layout points (shared group, layout_tools.py): one point per brick, rows with random brick widths that always add up to 1.0,
#       a half-brick bond blended with a random row shift, plus wrap-around copies of the bricks that cross the tile edge
#   -> Instance on Points: a cube per point, scaled to that brick's width x height, with a small random height and a small twist
#   -> Store Named Attribute (INSTANCE domain): 'brick_colour' from a random number through a Color Ramp (red / orange / dark soot)
#   -> Realize Instances (turns the instances into one real mesh; the instance attributes become vertex attributes)
#   -> Mesh Bevel (only the sharp 90 degree edges, found with Edge Angle) -> Subdivide Mesh -> Set Position with tileable noise
#       (rough brick faces and ragged outlines; every brick gets its own noise through the Seed input, so the wrap copies match)
#   -> Store Named Attribute 'piece_colour' = brick colour x mottling noise
#   + a mortar sheet (a dense Grid, also displaced with tileable noise) + Join Geometry
# Run:  blender -b --disable-autoexec -t 2 --python recipe_brick_layout.py -- OUT_FOLDER [--size 1254] [--wrap 1|0] [--ao 0.8]
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy  # noqa: E402
import gn_tools as gt  # noqa: E402
import layout_tools as lt  # noqa: E402

DEFAULTS = dict(rows=12, per_row=4, width_jitter=0.2, gap=0.022, brick_z=0.035, mortar_z=-0.006, bevel=0.0035, row_shift=0.8, seed=5,
                rough=0.002, patch_z=0.004, edge_wobble=0.0026, wrap=True, subdiv=3)


srgb, make_ramp = gt.srgb, gt.make_ramp


def build_wall_group(p):
    tree, g = gt.make_geometry_group('Brick wall', [('Geometry', 'NodeSocketGeometry', None)])
    layout = lt.row_layout_group()
    noise_group = gt.tileable_noise_geo_group()
    g.node('GeometryNodeGroup', 'layout')
    g.nodes['layout'].node_tree = layout
    for key, value in (('Rows', p['rows']), ('Per row', p['per_row']), ('Width jitter', p['width_jitter']), ('Row shift randomness', p['row_shift']),
                       ('Gap', p['gap']), ('Height factor', 1.0), ('Seed', p['seed']), ('Wrap', p['wrap'])):
        g.nodes['layout'].inputs[key].default_value = value
    # ---- one cube per brick
    g.node('GeometryNodeMeshCube', 'cube', {'Size': (1.0, 1.0, 1.0), 'Vertices X': 2, 'Vertices Y': 2, 'Vertices Z': 2})
    g.node('GeometryNodeTransform', 'cube up', {'Geometry': ('cube', 'Mesh'), 'Translation': (0.0, 0.0, 0.5)})
    g.node('GeometryNodeInputNamedAttribute', 'id', {'Name': 'piece_id'}, data_type='INT')
    g.node('GeometryNodeInputNamedAttribute', 'w', {'Name': 'piece_w'}, data_type='FLOAT')
    g.node('GeometryNodeInputNamedAttribute', 'h', {'Name': 'piece_h'}, data_type='FLOAT')
    g.node('FunctionNodeRandomValue', 'height random', {'ID': ('id', 'Attribute'), 'Seed': 17, 'Min': 0.75, 'Max': 1.1}, data_type='FLOAT')
    g.math('brick z', 'MULTIPLY', ('height random', 'Value'), p['brick_z'])
    g.node('ShaderNodeCombineXYZ', 'scale', {'X': ('w', 'Attribute'), 'Y': ('h', 'Attribute'), 'Z': ('brick z', 0)})
    g.node('FunctionNodeRandomValue', 'twist random', {'ID': ('id', 'Attribute'), 'Seed': 29, 'Min': -0.02, 'Max': 0.02}, data_type='FLOAT')
    g.node('ShaderNodeCombineXYZ', 'twist', {'Z': ('twist random', 'Value')})
    g.node('FunctionNodeEulerToRotation', 'twist rotation', {'Euler': ('twist', 'Vector')})
    g.node('GeometryNodeInstanceOnPoints', 'bricks', {'Points': ('layout', 'Geometry'), 'Instance': ('cube up', 'Geometry'),
                                                      'Rotation': ('twist rotation', 'Rotation'), 'Scale': ('scale', 'Vector')})
    # ---- one random "tone" per brick (0 dark soot .. 1 light orange), stored on the INSTANCE domain
    g.node('FunctionNodeRandomValue', 'tone random', {'ID': ('id', 'Attribute'), 'Seed': 3}, data_type='FLOAT')
    g.node('GeometryNodeStoreNamedAttribute', 'store brick tone', {'Geometry': ('bricks', 'Instances'), 'Name': 'brick_tone', 'Value': ('tone random', 'Value')},
           data_type='FLOAT', domain='INSTANCE')
    g.node('GeometryNodeRealizeInstances', 'realize', {'Geometry': ('store brick tone', 'Geometry')})
    # ---- soften the sharp edges, then add vertices to displace
    g.node('GeometryNodeInputMeshEdgeAngle', 'edge angle')
    g.node('FunctionNodeCompare', 'sharp edges', {'A': ('edge angle', 'Unsigned Angle'), 'B': 0.6}, data_type='FLOAT', operation='GREATER_THAN')
    g.node('GeometryNodeMeshBevel', 'bevel', {'Mesh': ('realize', 'Geometry'), 'Selection': ('sharp edges', 'Result'), 'Start Left Offset': p['bevel'], 'Start Right Offset': p['bevel'],
                                                'End Left Offset': p['bevel'], 'End Right Offset': p['bevel'], 'Segments': 2})
    g.node('GeometryNodeSubdivideMesh', 'subdivide', {'Mesh': ('bevel', 'Mesh'), 'Level': p['subdiv']})
    # ---- rough faces and ragged outlines: tileable noise, a different pattern per brick (Seed = piece id)
    g.node('GeometryNodeInputPosition', 'position')
    g.node('ShaderNodeSeparateXYZ', 'position xyz', {'Vector': ('position', 'Position')})
    g.node('GeometryNodeInputNamedAttribute', 'id v', {'Name': 'piece_id'}, data_type='INT')
    g.math('seed per brick', 'MULTIPLY', ('id v', 'Attribute'), 7.3)
    g.group('rough noise', noise_group, {'Position': ('position', 'Position'), 'Scale': 60.0, 'Detail': 5.0, 'Roughness': 0.6, 'Seed': ('seed per brick', 0)})
    g.group('edge noise x', noise_group, {'Position': ('position', 'Position'), 'Scale': 28.0, 'Detail': 3.0, 'Roughness': 0.5, 'Seed': ('seed per brick', 0)})
    g.math('seed y', 'ADD', ('seed per brick', 0), 31.0)
    g.group('edge noise y', noise_group, {'Position': ('position', 'Position'), 'Scale': 28.0, 'Detail': 3.0, 'Roughness': 0.5, 'Seed': ('seed y', 0)})
    g.group('patch noise', noise_group, {'Position': ('position', 'Position'), 'Scale': 14.0, 'Detail': 5.0, 'Roughness': 0.62, 'Seed': ('seed per brick', 0)})
    g.node('ShaderNodeMapRange', 'patch', {'Value': ('patch noise', 'Fac'), 'From Min': 0.40, 'From Max': 0.60, 'To Min': 0.0, 'To Max': 1.0})   # steep = hard-edged painted-looking patches
    g.node('ShaderNodeMapRange', 'rough centred', {'Value': ('rough noise', 'Fac'), 'From Min': 0.3, 'From Max': 0.7, 'To Min': -1.0, 'To Max': 1.0})
    g.node('ShaderNodeMapRange', 'wobble x', {'Value': ('edge noise x', 'Fac'), 'From Min': 0.3, 'From Max': 0.7, 'To Min': -1.0, 'To Max': 1.0})
    g.node('ShaderNodeMapRange', 'wobble y', {'Value': ('edge noise y', 'Fac'), 'From Min': 0.3, 'From Max': 0.7, 'To Min': -1.0, 'To Max': 1.0})
    # only move vertices that are above the brick's base (the base stays flat on the mortar)
    g.math('base level', 'ADD', 0.0, 0.0005)
    g.node('FunctionNodeCompare', 'above base', {'A': ('position xyz', 'Z'), 'B': ('base level', 0)}, data_type='FLOAT', operation='GREATER_THAN')
    g.node('GeometryNodeInputNormal', 'normal')
    g.node('ShaderNodeSeparateXYZ', 'normal xyz', {'Vector': ('normal', 'Normal')})
    g.node('FunctionNodeCompare', 'faces up', {'A': ('normal xyz', 'Z'), 'B': 0.5}, data_type='FLOAT', operation='GREATER_THAN')
    g.node('FunctionNodeBooleanMath', 'top only', {0: ('above base', 'Result'), 1: ('faces up', 'Result')}, operation='AND')
    g.math('rough z fine', 'MULTIPLY', ('rough centred', 'Result'), p['rough'])
    g.math('patch z', 'MULTIPLY', ('patch', 'Result'), p['patch_z'])
    g.math('rough z', 'ADD', ('rough z fine', 0), ('patch z', 0))
    g.math('wobble amount x', 'MULTIPLY', ('wobble x', 'Result'), p['edge_wobble'])
    g.math('wobble amount y', 'MULTIPLY', ('wobble y', 'Result'), p['edge_wobble'])
    g.node('ShaderNodeCombineXYZ', 'offset all', {'X': ('wobble amount x', 0), 'Y': ('wobble amount y', 0), 'Z': 0.0})
    g.node('ShaderNodeCombineXYZ', 'offset top', {'X': 0.0, 'Y': 0.0, 'Z': ('rough z', 0)})
    g.node('GeometryNodeSetPosition', 'displace outline', {'Geometry': ('subdivide', 'Mesh'), 'Selection': ('above base', 'Result'), 'Offset': ('offset all', 'Vector')})
    g.node('GeometryNodeSetPosition', 'displace top', {'Geometry': ('displace outline', 'Geometry'), 'Selection': ('top only', 'Boolean'), 'Offset': ('offset top', 'Vector')})
    g.node('GeometryNodeTransform', 'lower bricks', {'Geometry': ('displace top', 'Geometry'), 'Translation': (0.0, 0.0, p['mortar_z'] - 0.008)})
    g.node('GeometryNodeSetShadeSmooth', 'smooth bricks', {'Mesh': ('lower bricks', 'Geometry'), 'Shade Smooth': True})
    # ---- colour of every brick vertex: brick tone + the SAME patch noise that lifted the surface (so lighter = higher, like painted maps)
    g.node('GeometryNodeInputNamedAttribute', 'brick tone', {'Name': 'brick_tone'}, data_type='FLOAT')
    g.math('tone part', 'MULTIPLY', ('brick tone', 'Attribute'), 0.45)
    g.math('patch part', 'MULTIPLY', ('patch', 'Result'), 0.55)
    g.math('fine part', 'MULTIPLY', ('rough centred', 'Result'), 0.12)
    g.math('tone sum 1', 'ADD', ('tone part', 0), ('patch part', 0))
    g.math('tone sum', 'ADD', ('tone sum 1', 0), ('fine part', 0), clamp=True)
    make_ramp(g, 'brick palette', [(0.00, (36, 28, 27)), (0.22, (80, 50, 42)), (0.45, (126, 62, 43)), (0.72, (162, 76, 45)), (0.90, (186, 100, 58)), (1.0, (150, 112, 84))],
              {'Fac': ('tone sum', 0)})
    g.node('GeometryNodeStoreNamedAttribute', 'store piece colour', {'Geometry': ('smooth bricks', 'Mesh'), 'Name': 'piece_colour', 'Value': ('brick palette', 'Color')},
           data_type='FLOAT_COLOR', domain='POINT')
    # ---- the mortar sheet: a dense grid (0..1) with tileable noise heights and colours
    g.node('GeometryNodeMeshGrid', 'mortar grid', {'Size X': 1.0, 'Size Y': 1.0, 'Vertices X': 256, 'Vertices Y': 256})
    g.node('GeometryNodeTransform', 'mortar move', {'Geometry': ('mortar grid', 'Mesh'), 'Translation': (0.5, 0.5, p['mortar_z'])})
    g.group('mortar noise a', noise_group, {'Position': ('position', 'Position'), 'Scale': 10.0, 'Detail': 4.0, 'Roughness': 0.6, 'Seed': 5.0})
    g.group('mortar noise b', noise_group, {'Position': ('position', 'Position'), 'Scale': 70.0, 'Detail': 3.0, 'Roughness': 0.5, 'Seed': 9.0})
    g.node('ShaderNodeMapRange', 'mortar a', {'Value': ('mortar noise a', 'Fac'), 'From Min': 0.3, 'From Max': 0.7, 'To Min': -1.0, 'To Max': 1.0})
    g.node('ShaderNodeMapRange', 'mortar b', {'Value': ('mortar noise b', 'Fac'), 'From Min': 0.3, 'From Max': 0.7, 'To Min': -1.0, 'To Max': 1.0})
    g.math('mortar a z', 'MULTIPLY', ('mortar a', 'Result'), 0.004)
    g.math('mortar b z', 'MULTIPLY', ('mortar b', 'Result'), 0.0025)
    g.math('mortar z sum', 'ADD', ('mortar a z', 0), ('mortar b z', 0))
    g.node('ShaderNodeCombineXYZ', 'mortar offset', {'Z': ('mortar z sum', 0)})
    g.node('GeometryNodeSetPosition', 'mortar bumpy', {'Geometry': ('mortar move', 'Geometry'), 'Offset': ('mortar offset', 'Vector')})
    mortar = make_ramp(g, 'mortar palette', [(0.30, (92, 76, 58)), (0.55, (125, 103, 78)), (0.80, (150, 120, 90))], {'Fac': ('mortar noise a', 'Fac')})
    g.node('GeometryNodeStoreNamedAttribute', 'store mortar colour', {'Geometry': ('mortar bumpy', 'Geometry'), 'Name': 'piece_colour', 'Value': ('mortar palette', 'Color')},
           data_type='FLOAT_COLOR', domain='POINT')
    g.node('GeometryNodeJoinGeometry', 'join', {})
    g.link('store piece colour', 'Geometry', 'join', 'Geometry')
    g.link('store mortar colour', 'Geometry', 'join', 'Geometry')
    gt.finish_with_material_slot(g, 'join')
    return tree


def run(out_folder, size=1254, params=None, ambient_occlusion=0.8, quiet=False):
    p = {**DEFAULTS, **(params or {})}
    started = time.time()
    scene = gt.new_scene(size)
    tree = build_wall_group(p)
    obj, modifier = gt.add_geometry_object('brick wall', tree)
    info = gt.photograph_geometry(obj, out_folder, size=size, normal_reference='brick', ambient_occlusion=ambient_occlusion, occlusion_distance=0.03,
                                  colour_samples=16 if ambient_occlusion else 4, quiet=quiet)
    info['total_seconds'] = round(time.time() - started, 1)
    info['parameters'] = {k: (v if not isinstance(v, float) else round(v, 5)) for k, v in p.items()}
    import json
    with open(os.path.join(out_folder, 'photo.json'), 'w') as handle:
        json.dump(info, handle, indent=1)
    return info


if __name__ == '__main__':
    arguments = sys.argv[sys.argv.index('--') + 1:]
    option = lambda name, default=None: arguments[arguments.index(name) + 1] if name in arguments else default
    run(arguments[0], size=int(option('--size', 1254)), params={'wrap': option('--wrap', '1') == '1'}, ambient_occlusion=float(option('--ao', 0.8)))
