# What this does: RECIPE 2 - builds a roof of overlapping slates out of REAL slate plates with Geometry Nodes, then photographs it from straight
# above to get height, colour and normal pictures of a 1 x 1 seamless tile.
# What is different from the brick recipe: the rows OVERLAP. Every slate is taller than its row (Height factor 1.3) and is TILTED a little
# (its lower edge is lifted), so the lower edge of each slate lies on top of the upper part of the slate below it. The overhead camera
# then sees exactly what a roof looks like from above: the real overlap, the step at each lower edge and the dark shadow line under it,
# with no height trick at all - the geometry does the depth sorting. The wrap needs copies in y as well as x, because the top row spills
# over the top edge of the tile (the shared Row layout group makes 3 x 3 copies and keeps only the ones that touch the tile).
# Chain: Row layout points -> Instance on Points (thin box, tilted about X by atan(lift / height)) -> Store Named Attribute (INSTANCE:
# slate tone) -> Realize Instances -> Mesh Bevel (sharp edges) -> Subdivide Mesh -> Set Position with tileable noise: ragged lower edge
# (weighted by 'how far below the slate's centre', using the piece_centre attribute), wobbly outline -> colour from tone + moss patches near
# the top of each slate + pale chipped lower edge -> Join with a dark underlay sheet that shows through the joints.
# Run:  blender -b --disable-autoexec -t 2 --python recipe_slate_layout.py -- OUT_FOLDER [--size 1254] [--ao 0.8]
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy  # noqa: E402
import gn_tools as gt  # noqa: E402
import layout_tools as lt  # noqa: E402

make_ramp = gt.make_ramp
DEFAULTS = dict(rows=8, per_row=6, width_jitter=0.22, gap=0.010, height_factor=1.32, thickness=0.010, lift=0.020, bevel=0.0022, row_shift=0.7, seed=11,
                base_z=0.030, edge_wobble=0.0022, chip=0.012, wrap=True, subdiv=3)


def build_roof_group(p):
    tree, g = gt.make_geometry_group('Slate roof', [('Geometry', 'NodeSocketGeometry', None)])
    noise_group = gt.tileable_noise_geo_group()
    g.group('layout', lt.row_layout_group(), {'Rows': p['rows'], 'Per row': p['per_row'], 'Width jitter': p['width_jitter'], 'Row shift randomness': p['row_shift'],
                                              'Gap': p['gap'], 'Height factor': p['height_factor'], 'Seed': p['seed'], 'Wrap': p['wrap']})
    g.node('GeometryNodeMeshCube', 'cube', {'Size': (1.0, 1.0, 1.0), 'Vertices X': 2, 'Vertices Y': 2, 'Vertices Z': 2})
    g.node('GeometryNodeInputNamedAttribute', 'id', {'Name': 'piece_id'}, data_type='INT')
    g.node('GeometryNodeInputNamedAttribute', 'w', {'Name': 'piece_w'}, data_type='FLOAT')
    g.node('GeometryNodeInputNamedAttribute', 'h', {'Name': 'piece_h'}, data_type='FLOAT')
    g.node('FunctionNodeRandomValue', 'thick random', {'ID': ('id', 'Attribute'), 'Seed': 17, 'Min': 0.8, 'Max': 1.3}, data_type='FLOAT')
    g.math('thickness', 'MULTIPLY', ('thick random', 'Value'), p['thickness'])
    g.node('ShaderNodeCombineXYZ', 'scale', {'X': ('w', 'Attribute'), 'Y': ('h', 'Attribute'), 'Z': ('thickness', 0)})
    # tilt: lower edge lifted by 'lift' (random per slate) over the slate's height -> angle = atan2(lift, height); negative = lower (-y) edge goes UP
    g.node('FunctionNodeRandomValue', 'lift random', {'ID': ('id', 'Attribute'), 'Seed': 41, 'Min': 0.7, 'Max': 1.3}, data_type='FLOAT')
    g.math('lift', 'MULTIPLY', ('lift random', 'Value'), p['lift'])
    g.math('tilt angle', 'ARCTAN2', ('lift', 0), ('h', 'Attribute'))
    g.math('tilt', 'MULTIPLY', ('tilt angle', 0), -1.0)
    g.node('FunctionNodeRandomValue', 'twist random', {'ID': ('id', 'Attribute'), 'Seed': 29, 'Min': -0.03, 'Max': 0.03}, data_type='FLOAT')
    g.node('ShaderNodeCombineXYZ', 'euler', {'X': ('tilt', 0), 'Z': ('twist random', 'Value')})
    g.node('FunctionNodeEulerToRotation', 'rotation', {'Euler': ('euler', 'Vector')})
    g.node('GeometryNodeInstanceOnPoints', 'slates', {'Points': ('layout', 'Geometry'), 'Instance': ('cube', 'Mesh'), 'Rotation': ('rotation', 'Rotation'), 'Scale': ('scale', 'Vector')})
    g.node('FunctionNodeRandomValue', 'tone random', {'ID': ('id', 'Attribute'), 'Seed': 3}, data_type='FLOAT')
    g.node('GeometryNodeStoreNamedAttribute', 'store tone', {'Geometry': ('slates', 'Instances'), 'Name': 'slate_tone', 'Value': ('tone random', 'Value')}, data_type='FLOAT', domain='INSTANCE')
    g.node('GeometryNodeRealizeInstances', 'realize', {'Geometry': ('store tone', 'Geometry')})
    g.node('GeometryNodeInputMeshEdgeAngle', 'edge angle')
    g.node('FunctionNodeCompare', 'sharp edges', {'A': ('edge angle', 'Unsigned Angle'), 'B': 0.6}, data_type='FLOAT', operation='GREATER_THAN')
    g.node('GeometryNodeMeshBevel', 'bevel', {'Mesh': ('realize', 'Geometry'), 'Selection': ('sharp edges', 'Result'), 'Start Left Offset': p['bevel'], 'Start Right Offset': p['bevel'],
                                                'End Left Offset': p['bevel'], 'End Right Offset': p['bevel'], 'Segments': 1})
    g.node('GeometryNodeSubdivideMesh', 'subdivide', {'Mesh': ('bevel', 'Mesh'), 'Level': p['subdiv']})
    # ---- where on the slate is this vertex? local y = vertex y - the slate's centre y (valid for the wrap copies too)
    g.node('GeometryNodeInputPosition', 'position')
    g.node('ShaderNodeSeparateXYZ', 'position xyz', {'Vector': ('position', 'Position')})
    g.node('GeometryNodeInputNamedAttribute', 'centre', {'Name': 'piece_centre'}, data_type='FLOAT_VECTOR')
    g.node('ShaderNodeSeparateXYZ', 'centre xyz', {'Vector': ('centre', 'Attribute')})
    g.math('local y', 'SUBTRACT', ('position xyz', 'Y'), ('centre xyz', 'Y'))
    g.node('GeometryNodeInputNamedAttribute', 'h v', {'Name': 'piece_h'}, data_type='FLOAT')
    g.math('local y relative', 'DIVIDE', ('local y', 0), ('h v', 'Attribute'))          # -0.5 = lower edge, +0.5 = upper edge
    g.node('ShaderNodeMapRange', 'lower edge weight', {'Value': ('local y relative', 0), 'From Min': -0.5, 'From Max': -0.30, 'To Min': 1.0, 'To Max': 0.0})   # 1 at the very bottom edge
    g.node('ShaderNodeMapRange', 'upper weight', {'Value': ('local y relative', 0), 'From Min': -0.1, 'From Max': 0.5, 'To Min': 0.0, 'To Max': 1.0})          # 1 near the top
    g.node('GeometryNodeInputNamedAttribute', 'id v', {'Name': 'piece_id'}, data_type='INT')
    g.math('seed per slate', 'MULTIPLY', ('id v', 'Attribute'), 7.3)
    g.group('chip noise', noise_group, {'Position': ('position', 'Position'), 'Scale': 45.0, 'Detail': 4.0, 'Roughness': 0.6, 'Seed': ('seed per slate', 0)})
    g.group('wobble noise x', noise_group, {'Position': ('position', 'Position'), 'Scale': 26.0, 'Detail': 3.0, 'Roughness': 0.5, 'Seed': ('seed per slate', 0)})
    g.math('seed y', 'ADD', ('seed per slate', 0), 31.0)
    g.group('wobble noise y', noise_group, {'Position': ('position', 'Position'), 'Scale': 26.0, 'Detail': 3.0, 'Roughness': 0.5, 'Seed': ('seed y', 0)})
    for name_, source in (('chip centred', 'chip noise'), ('wobble x', 'wobble noise x'), ('wobble y', 'wobble noise y')):
        g.node('ShaderNodeMapRange', name_, {'Value': (source, 'Fac'), 'From Min': 0.3, 'From Max': 0.7, 'To Min': -1.0, 'To Max': 1.0})
    g.math('chip 0..1', 'MULTIPLY_ADD', ('chip centred', 'Result'), 0.5, 0.5)
    # ragged lower edge: pull the lowest strip of vertices UP the slate by chip noise, only where the weight is high
    g.math('chip amount', 'MULTIPLY', ('chip 0..1', 0), ('lower edge weight', 'Result'))
    g.math('chip up', 'MULTIPLY', ('chip amount', 0), p['chip'])
    g.math('wobble amount x', 'MULTIPLY', ('wobble x', 'Result'), p['edge_wobble'])
    g.math('wobble amount y', 'MULTIPLY', ('wobble y', 'Result'), p['edge_wobble'])
    g.math('y move', 'ADD', ('chip up', 0), ('wobble amount y', 0))
    g.node('ShaderNodeCombineXYZ', 'outline move', {'X': ('wobble amount x', 0), 'Y': ('y move', 0), 'Z': 0.0})
    g.node('GeometryNodeSetPosition', 'ragged', {'Geometry': ('subdivide', 'Mesh'), 'Offset': ('outline move', 'Vector')})
    g.node('GeometryNodeTransform', 'raise slates', {'Geometry': ('ragged', 'Geometry'), 'Translation': (0.0, 0.0, p['base_z'])})
    g.node('GeometryNodeSetShadeSmooth', 'smooth', {'Mesh': ('raise slates', 'Geometry'), 'Shade Smooth': True})
    # ---- colour: tone (dark blue-grey .. light grey-green) + moss near the top + pale chipped lower edge
    g.node('GeometryNodeInputNamedAttribute', 'tone', {'Name': 'slate_tone'}, data_type='FLOAT')
    g.group('moss noise', noise_group, {'Position': ('position', 'Position'), 'Scale': 8.0, 'Detail': 5.0, 'Roughness': 0.6, 'Seed': ('seed per slate', 0)})
    g.node('ShaderNodeMapRange', 'moss patch', {'Value': ('moss noise', 'Fac'), 'From Min': 0.50, 'From Max': 0.58, 'To Min': 0.0, 'To Max': 1.0})
    g.math('moss amount', 'MULTIPLY', ('moss patch', 'Result'), ('upper weight', 'Result'))
    g.math('tone mix', 'MULTIPLY_ADD', ('tone', 'Attribute'), 0.6, 0.0)
    g.math('fine part', 'MULTIPLY', ('chip centred', 'Result'), 0.10)
    g.math('tone sum 1', 'ADD', ('tone mix', 0), ('fine part', 0))
    g.math('tone sum', 'ADD', ('tone sum 1', 0), 0.2, clamp=True)
    make_ramp(g, 'slate palette', [(0.00, (20, 21, 23)), (0.25, (40, 44, 46)), (0.55, (62, 70, 72)), (0.85, (84, 94, 94)), (1.0, (110, 112, 108))], {'Fac': ('tone sum', 0)})
    g.node('ShaderNodeMix', 'with moss', {'Factor': ('moss amount', 0), 'A': ('slate palette', 'Color'), 'B': gt.srgb(86, 92, 48)}, data_type='RGBA', blend_type='MIX')
    g.math('pale edge', 'MULTIPLY', ('lower edge weight', 'Result'), ('chip 0..1', 0))
    g.node('ShaderNodeMix', 'with pale edge', {'Factor': ('pale edge', 0), 'A': ('with moss', 'Result'), 'B': gt.srgb(150, 130, 112)}, data_type='RGBA', blend_type='MIX')
    g.node('GeometryNodeStoreNamedAttribute', 'store colour', {'Geometry': ('smooth', 'Mesh'), 'Name': 'piece_colour', 'Value': ('with pale edge', 'Result')}, data_type='FLOAT_COLOR', domain='POINT')
    # ---- the dark underlay that shows through the joints
    g.node('GeometryNodeMeshGrid', 'under grid', {'Size X': 1.0, 'Size Y': 1.0, 'Vertices X': 64, 'Vertices Y': 64})
    g.node('GeometryNodeTransform', 'under move', {'Geometry': ('under grid', 'Mesh'), 'Translation': (0.5, 0.5, 0.0)})
    g.node('GeometryNodeStoreNamedAttribute', 'under colour', {'Geometry': ('under move', 'Geometry'), 'Name': 'piece_colour', 'Value': gt.srgb(10, 10, 12)}, data_type='FLOAT_COLOR', domain='POINT')
    g.node('GeometryNodeJoinGeometry', 'join', {})
    g.link('store colour', 'Geometry', 'join', 'Geometry')
    g.link('under colour', 'Geometry', 'join', 'Geometry')
    gt.finish_with_material_slot(g, 'join')
    return tree


def run(out_folder, size=1254, params=None, ambient_occlusion=0.8, quiet=False):
    p = {**DEFAULTS, **(params or {})}
    started = time.time()
    gt.new_scene(size)
    tree = build_roof_group(p)
    obj, modifier = gt.add_geometry_object('slate roof', tree)
    info = gt.photograph_geometry(obj, out_folder, size=size, normal_reference='slate', ambient_occlusion=ambient_occlusion, occlusion_distance=0.03,
                                  colour_samples=16 if ambient_occlusion else 4, quiet=quiet)
    info['total_seconds'] = round(time.time() - started, 1)
    info['parameters'] = p
    with open(os.path.join(out_folder, 'photo.json'), 'w') as handle:
        json.dump(info, handle, indent=1)
    return info


if __name__ == '__main__':
    arguments = sys.argv[sys.argv.index('--') + 1:]
    option = lambda name, default=None: arguments[arguments.index(name) + 1] if name in arguments else default
    run(arguments[0], size=int(option('--size', 1254)), params={'wrap': option('--wrap', '1') == '1'}, ambient_occlusion=float(option('--ao', 0.8)))
