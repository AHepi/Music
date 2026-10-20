# What this does: RECIPE 6 - weathered wooden planks built from real geometry with Geometry Nodes, photographed from straight above
# (height, colour, normal pictures of a 1 x 1 seamless tile). It uses CURVES three ways:
#   * grain: bundles of thin curves (one family of long wiggly lines per plank, 3 different bundles picked at random with Pick Instance),
#            swept with Curve to Mesh into little raised ridges (the plank surface itself stays smooth)
#   * cracks: random wiggly curves -> distance from every plank vertex to the nearest crack (Geometry Proximity, Edges) -> a V-shaped groove
#   * knots: points -> distance to the nearest knot (Proximity, Points) -> rings (cosine of distance) with a dome in the middle
# The plank layout is the shared Row layout group (6 rows, 2 planks per row, random lengths, random row shift, wrap-around copies).
# Run:  blender -b --disable-autoexec -t 2 --python recipe_wood_planks.py -- OUT_FOLDER [--size 1254] [--ao 0.8]
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy  # noqa: E402
import numpy as np  # noqa: E402
import gn_tools as gt  # noqa: E402
import layout_tools as lt  # noqa: E402

make_ramp, srgb = gt.make_ramp, gt.srgb
DEFAULTS = dict(rows=6, per_row=2, width_jitter=0.55, gap=0.012, seed=4, base_z=0.03, crack_count=14, crack_depth=0.014, crack_width=0.0045, knots=3, grain_lines=9,
                grain_radius=0.0016, subdiv=2, wrap=True)


def crack_and_knot_data(p):
    """Random crack and knot positions made in Python (so the same numbers are used by the height AND the colour node chains)."""
    rng = np.random.default_rng(p['seed'] + 100)
    pitch = 1.0 / p['rows']
    cracks = []
    for _ in range(p['crack_count']):
        row = int(rng.integers(0, p['rows']))
        cracks.append(dict(x0=float(rng.uniform(0, 1)), y0=float((row + 0.5) * pitch + rng.uniform(-0.3, 0.3) * pitch), length=float(rng.uniform(0.12, 0.45)),
                           slope=float(rng.uniform(-0.04, 0.04)), amp=float(rng.uniform(0.002, 0.006)), waves=int(rng.integers(2, 6)), phase=float(rng.uniform(0, 6.28))))
    knots = [(float(rng.uniform(0, 1)), float((int(rng.integers(0, p['rows'])) + 0.5) * pitch + rng.uniform(-0.2, 0.2) * pitch)) for _ in range(p['knots'])]
    return cracks, knots


def crack_lines(g, cracks, shifts):
    """Crack curves -> one mesh of edges (with wrap-around copies). Returns (node, socket)."""
    parts = []
    for i, c in enumerate(cracks):
        tag = f'crack{i}'
        g.node('GeometryNodeMeshLine', f'{tag} line', {'Count': 48, 'Start Location': (c['x0'], 0.0, 0.0), 'Offset': (c['length'] / 47, 0.0, 0.0)}, mode='OFFSET')
        g.node('GeometryNodeInputPosition', f'{tag} pos')
        g.node('ShaderNodeSeparateXYZ', f'{tag} xyz', {'Vector': (f'{tag} pos', 'Position')})
        g.math(f'{tag} t', 'SUBTRACT', (f'{tag} xyz', 'X'), c['x0'])
        g.math(f'{tag} wave arg', 'MULTIPLY_ADD', (f'{tag} t', 0), 2 * math.pi * c['waves'] / c['length'], c['phase'])
        g.math(f'{tag} wave', 'SINE', (f'{tag} wave arg', 0))
        g.math(f'{tag} wave y', 'MULTIPLY', (f'{tag} wave', 0), c['amp'])
        g.math(f'{tag} slope y', 'MULTIPLY', (f'{tag} t', 0), c['slope'])
        g.math(f'{tag} y1', 'ADD', (f'{tag} wave y', 0), (f'{tag} slope y', 0))
        g.math(f'{tag} y', 'ADD', (f'{tag} y1', 0), c['y0'])
        g.node('ShaderNodeCombineXYZ', f'{tag} point', {'X': (f'{tag} xyz', 'X'), 'Y': (f'{tag} y', 0), 'Z': 0.0})
        g.node('GeometryNodeSetPosition', f'{tag} placed', {'Geometry': (f'{tag} line', 'Mesh'), 'Position': (f'{tag} point', 'Vector')})
        parts.append(f'{tag} placed')
    g.node('GeometryNodeJoinGeometry', 'cracks join', {})
    for part in parts:
        g.link(part, 'Geometry', 'cracks join', 'Geometry')
    copies = []
    for dx, dy in shifts:
        g.node('GeometryNodeTransform', f'cracks copy {dx} {dy}', {'Geometry': ('cracks join', 'Geometry'), 'Translation': (float(dx), float(dy), 0.0)})
        copies.append(f'cracks copy {dx} {dy}')
    g.node('GeometryNodeJoinGeometry', 'cracks all', {})
    for name in copies:
        g.link(name, 'Geometry', 'cracks all', 'Geometry')
    return 'cracks all', 'Geometry'


def knot_points(g, knots, shifts):
    parts = []
    for i, (x, y) in enumerate(knots):
        g.node('GeometryNodePoints', f'knot{i}', {'Count': 1, 'Position': (x, y, 0.0)})
        parts.append(f'knot{i}')
    g.node('GeometryNodeJoinGeometry', 'knots join', {})
    for part in parts:
        g.link(part, 'Geometry', 'knots join', 'Geometry')
    copies = []
    for dx, dy in shifts:
        g.node('GeometryNodeTransform', f'knots copy {dx} {dy}', {'Geometry': ('knots join', 'Geometry'), 'Translation': (float(dx), float(dy), 0.0)})
        copies.append(f'knots copy {dx} {dy}')
    g.node('GeometryNodeJoinGeometry', 'knots all', {})
    for name in copies:
        g.link(name, 'Geometry', 'knots all', 'Geometry')
    return 'knots all', 'Geometry'


def grain_bundle(g, index, p, noise):
    """One bundle of long thin curves in unit coordinates (x from -0.5 to 0.5, y from -0.5 to 0.5); returns (node, socket) of its Instances."""
    tag = f'bundle{index}'
    g.node('GeometryNodeMeshLine', f'{tag} rows', {'Count': p['grain_lines'], 'Start Location': (0.0, -0.44, 0.0), 'Offset': (0.0, 0.88 / (p['grain_lines'] - 1), 0.0)}, mode='OFFSET')
    g.node('GeometryNodeMeshToPoints', f'{tag} points', {'Mesh': (f'{tag} rows', 'Mesh')})
    g.node('FunctionNodeRandomValue', f'{tag} jitter', {'Min': -0.035, 'Max': 0.035, 'Seed': 50 + index}, data_type='FLOAT')
    g.node('ShaderNodeCombineXYZ', f'{tag} jitter v', {'Y': (f'{tag} jitter', 'Value')})
    g.node('GeometryNodeSetPosition', f'{tag} jittered', {'Geometry': (f'{tag} points', 'Points'), 'Offset': (f'{tag} jitter v', 'Vector')})
    g.node('GeometryNodeCurvePrimitiveLine', f'{tag} line', {'Start': (-0.5, 0.0, 0.0), 'End': (0.5, 0.0, 0.0)}, mode='POINTS')
    g.node('GeometryNodeResampleCurve', f'{tag} resample', {'Curve': (f'{tag} line', 'Curve'), 'Mode': 'Count', 'Count': 64})
    g.node('GeometryNodeInstanceOnPoints', f'{tag} lines', {'Points': (f'{tag} jittered', 'Geometry'), 'Instance': (f'{tag} resample', 'Curve')})
    g.node('GeometryNodeRealizeInstances', f'{tag} real', {'Geometry': (f'{tag} lines', 'Instances')})
    g.node('GeometryNodeInputPosition', f'{tag} pos')
    g.group(f'{tag} wobble', noise, {'Position': (f'{tag} pos', 'Position'), 'Scale': 2.0, 'Detail': 3.0, 'Roughness': 0.5, 'Seed': 3.0 + index * 7.0})
    g.node('ShaderNodeMapRange', f'{tag} wobble centred', {'Value': (f'{tag} wobble', 'Fac'), 'From Min': 0.3, 'From Max': 0.7, 'To Min': -0.06, 'To Max': 0.06})
    g.node('ShaderNodeCombineXYZ', f'{tag} wobble v', {'Y': (f'{tag} wobble centred', 'Result')})
    g.node('GeometryNodeSetPosition', f'{tag} wiggly', {'Geometry': (f'{tag} real', 'Geometry'), 'Offset': (f'{tag} wobble v', 'Vector')})
    g.node('GeometryNodeGeometryToInstance', f'{tag} instance', {'Geometry': (f'{tag} wiggly', 'Geometry')})
    return f'{tag} instance', 'Instances'


def build_wood_group(p):
    tree, g = gt.make_geometry_group('Wood planks', [('Geometry', 'NodeSocketGeometry', None)])
    noise = gt.tileable_noise_geo_group()
    stretched = gt.tileable_noise_stretched_group()
    cracks, knots = crack_and_knot_data(p)
    shifts = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)] if p['wrap'] else [(0, 0)]
    g.group('layout', lt.row_layout_group(), {'Rows': p['rows'], 'Per row': p['per_row'], 'Width jitter': p['width_jitter'], 'Row shift randomness': 1.0, 'Gap': p['gap'],
                                              'Height factor': 1.0, 'Seed': p['seed'], 'Wrap': p['wrap']})
    g.node('GeometryNodeInputNamedAttribute', 'id', {'Name': 'piece_id'}, data_type='INT')
    g.node('GeometryNodeInputNamedAttribute', 'w', {'Name': 'piece_w'}, data_type='FLOAT')
    g.node('GeometryNodeInputNamedAttribute', 'h', {'Name': 'piece_h'}, data_type='FLOAT')
    # each plank sits a little higher or lower than its neighbours
    g.node('FunctionNodeRandomValue', 'plank z random', {'ID': ('id', 'Attribute'), 'Seed': 8, 'Min': -0.004, 'Max': 0.004}, data_type='FLOAT')
    g.math('plank z', 'ADD', ('plank z random', 'Value'), p['base_z'])
    g.node('ShaderNodeCombineXYZ', 'raise v', {'Z': ('plank z', 0)})
    g.node('GeometryNodeInputPosition', 'layout pos')
    g.vmath('layout raised', 'ADD', ('layout pos', 'Position'), ('raise v', 'Vector'))
    g.node('GeometryNodeSetPosition', 'planks at height', {'Geometry': ('layout', 'Geometry'), 'Position': ('layout raised', 0)})
    # ---------------------------------------------------------------- the plank surfaces: one grid per plank
    g.node('GeometryNodeMeshGrid', 'plank grid', {'Size X': 1.0, 'Size Y': 1.0, 'Vertices X': 36, 'Vertices Y': 12})
    g.node('ShaderNodeCombineXYZ', 'plank scale', {'X': ('w', 'Attribute'), 'Y': ('h', 'Attribute'), 'Z': 1.0})
    g.node('GeometryNodeInstanceOnPoints', 'planks', {'Points': ('planks at height', 'Geometry'), 'Instance': ('plank grid', 'Mesh'), 'Scale': ('plank scale', 'Vector')})
    g.node('GeometryNodeRealizeInstances', 'planks real', {'Geometry': ('planks', 'Instances')})
    g.node('GeometryNodeSubdivideMesh', 'planks fine', {'Mesh': ('planks real', 'Geometry'), 'Level': p['subdiv']})
    # ---------------------------------------------------------------- cracks and knots as distance fields
    node, socket = crack_lines(g, cracks, shifts)
    knot_node, knot_socket = knot_points(g, knots, shifts)
    g.node('GeometryNodeInputPosition', 'pos')
    g.node('ShaderNodeSeparateXYZ', 'pos xyz', {'Vector': ('pos', 'Position')})
    g.node('ShaderNodeCombineXYZ', 'flat pos', {'X': ('pos xyz', 'X'), 'Y': ('pos xyz', 'Y'), 'Z': 0.0})
    g.node('GeometryNodeProximity', 'crack distance', {'Geometry': (node, socket), 'Sample Position': ('flat pos', 'Vector')}, target_element='EDGES')
    g.node('GeometryNodeProximity', 'knot distance', {'Geometry': (knot_node, knot_socket), 'Sample Position': ('flat pos', 'Vector')}, target_element='POINTS')
    g.node('ShaderNodeMapRange', 'crack groove', {'Value': ('crack distance', 'Distance'), 'From Min': 0.0, 'From Max': p['crack_width'], 'To Min': -p['crack_depth'], 'To Max': 0.0})
    # knot rings: cos(distance / ring spacing) fading away from the middle, plus a dome
    g.math('knot rings arg', 'MULTIPLY', ('knot distance', 'Distance'), 2 * math.pi / 0.0075)
    g.math('knot rings cos', 'COSINE', ('knot rings arg', 0))
    g.math('knot fade arg', 'DIVIDE', ('knot distance', 'Distance'), 0.06)
    g.math('knot fade sq', 'POWER', ('knot fade arg', 0), 2.0)
    g.math('knot fade neg', 'MULTIPLY', ('knot fade sq', 0), -1.0)
    g.math('knot fade', 'EXPONENT', ('knot fade neg', 0))
    g.math('knot height', 'MULTIPLY', ('knot rings cos', 0), ('knot fade', 0))
    g.math('knot z', 'MULTIPLY', ('knot height', 0), 0.0028)
    # surface relief: fibres (stretched tileable noise: 6 features along x, 140 across) and a slow wear
    g.group('fibres', stretched, {'Position': ('pos', 'Position'), 'Scale X': 7.0, 'Scale Y': 150.0, 'Detail': 3.0, 'Roughness': 0.5, 'Seed': 2.0})
    g.node('ShaderNodeMapRange', 'fibres centred', {'Value': ('fibres', 'Fac'), 'From Min': 0.3, 'From Max': 0.7, 'To Min': -1.0, 'To Max': 1.0})
    g.math('fibres z', 'MULTIPLY', ('fibres centred', 'Result'), 0.0012)
    g.group('wear', noise, {'Position': ('pos', 'Position'), 'Scale': 10.0, 'Detail': 4.0, 'Roughness': 0.55, 'Seed': 6.0})
    g.node('ShaderNodeMapRange', 'wear centred', {'Value': ('wear', 'Fac'), 'From Min': 0.3, 'From Max': 0.7, 'To Min': -1.0, 'To Max': 1.0})
    g.math('wear z', 'MULTIPLY', ('wear centred', 'Result'), 0.0025)
    g.math('z sum 1', 'ADD', ('crack groove', 'Result'), ('knot z', 0))
    g.math('z sum 2', 'ADD', ('z sum 1', 0), ('fibres z', 0))
    g.math('z sum', 'ADD', ('z sum 2', 0), ('wear z', 0))
    g.node('ShaderNodeCombineXYZ', 'z offset', {'Z': ('z sum', 0)})
    g.node('GeometryNodeSetPosition', 'planks shaped', {'Geometry': ('planks fine', 'Mesh'), 'Offset': ('z offset', 'Vector')})
    g.node('GeometryNodeSetShadeSmooth', 'planks smooth', {'Mesh': ('planks shaped', 'Geometry'), 'Shade Smooth': True})
    # ---------------------------------------------------------------- plank colour: tone per plank + fibres streaks + dark rot patches + dark cracks
    g.node('FunctionNodeRandomValue', 'tone random', {'ID': ('id', 'Attribute'), 'Seed': 5}, data_type='FLOAT')
    g.node('GeometryNodeInputNamedAttribute', 'id v', {'Name': 'piece_id'}, data_type='INT')
    g.node('FunctionNodeRandomValue', 'tone v', {'ID': ('id v', 'Attribute'), 'Seed': 5}, data_type='FLOAT')
    g.group('streaks', stretched, {'Position': ('pos', 'Position'), 'Scale X': 3.0, 'Scale Y': 60.0, 'Detail': 4.0, 'Roughness': 0.6, 'Seed': 12.0})
    g.group('rot', noise, {'Position': ('pos', 'Position'), 'Scale': 7.0, 'Detail': 5.0, 'Roughness': 0.65, 'Seed': 17.0})
    g.node('ShaderNodeMapRange', 'rot patch', {'Value': ('rot', 'Fac'), 'From Min': 0.56, 'From Max': 0.60, 'To Min': 0.0, 'To Max': 1.0})
    g.math('tone a', 'MULTIPLY', ('tone v', 'Value'), 0.35)
    g.math('tone b', 'MULTIPLY', ('streaks', 'Fac'), 0.55)
    g.math('tone c', 'ADD', ('tone a', 0), ('tone b', 0))
    g.math('tone', 'ADD', ('tone c', 0), 0.05, clamp=True)
    make_ramp(g, 'wood palette', [(0.0, (34, 24, 20)), (0.25, (58, 42, 34)), (0.5, (84, 63, 51)), (0.75, (110, 80, 58)), (1.0, (146, 106, 76))], {'Fac': ('tone', 0)})
    g.node('ShaderNodeMix', 'with rot', {'Factor': ('rot patch', 'Result'), 'A': ('wood palette', 'Color'), 'B': srgb(48, 34, 28)}, data_type='RGBA')
    g.node('ShaderNodeMapRange', 'crack dark', {'Value': ('crack distance', 'Distance'), 'From Min': 0.0, 'From Max': p['crack_width'] * 1.6, 'To Min': 1.0, 'To Max': 0.0})
    g.node('ShaderNodeMix', 'with cracks', {'Factor': ('crack dark', 'Result'), 'A': ('with rot', 'Result'), 'B': srgb(14, 10, 9)}, data_type='RGBA')
    g.node('ShaderNodeMapRange', 'knot dark', {'Value': ('knot rings cos', 0), 'From Min': -1.0, 'From Max': 0.2, 'To Min': 0.55, 'To Max': 0.0})
    g.node('ShaderNodeMapRange', 'knot near', {'Value': ('knot distance', 'Distance'), 'From Min': 0.045, 'From Max': 0.012, 'To Min': 0.0, 'To Max': 1.0})
    g.math('knot amount', 'MULTIPLY', ('knot dark', 'Result'), ('knot near', 'Result'))
    g.node('ShaderNodeMix', 'with knots', {'Factor': ('knot amount', 0), 'A': ('with cracks', 'Result'), 'B': srgb(30, 20, 16)}, data_type='RGBA')
    g.node('GeometryNodeStoreNamedAttribute', 'planks colour', {'Geometry': ('planks smooth', 'Geometry'), 'Name': 'piece_colour', 'Value': ('with knots', 'Result')}, data_type='FLOAT_COLOR', domain='POINT')
    # ---------------------------------------------------------------- grain ridges: bundles of curves -> instance on the planks -> Curve to Mesh
    bundles = [grain_bundle(g, i, p, noise) for i in range(3)]
    g.node('GeometryNodeJoinGeometry', 'bundles', {})
    for node_, socket_ in bundles:
        g.link(node_, socket_, 'bundles', 'Geometry')
    g.node('FunctionNodeRandomValue', 'bundle pick', {'ID': ('id', 'Attribute'), 'Min': 0, 'Max': 2, 'Seed': 21}, data_type='INT')
    g.node('GeometryNodeInstanceOnPoints', 'grain on planks', {'Points': ('planks at height', 'Geometry'), 'Instance': ('bundles', 'Geometry'), 'Pick Instance': True,
                                                              'Instance Index': ('bundle pick', 'Value'), 'Scale': ('plank scale', 'Vector')})
    g.node('GeometryNodeRealizeInstances', 'grain real', {'Geometry': ('grain on planks', 'Instances')})
    g.node('GeometryNodeCurvePrimitiveCircle', 'ridge profile', {'Resolution': 3, 'Radius': p['grain_radius']}, mode='RADIUS')
    g.node('GeometryNodeCurveToMesh', 'ridges', {'Curve': ('grain real', 'Geometry'), 'Profile Curve': ('ridge profile', 'Curve')})
    g.node('GeometryNodeTransform', 'ridges up', {'Geometry': ('ridges', 'Mesh'), 'Translation': (0.0, 0.0, 0.0006)})
    g.node('GeometryNodeStoreNamedAttribute', 'ridge colour', {'Geometry': ('ridges up', 'Geometry'), 'Name': 'piece_colour', 'Value': srgb(150, 112, 82)}, data_type='FLOAT_COLOR', domain='POINT')
    # ---------------------------------------------------------------- the dark underlay shows in the gaps
    g.node('GeometryNodeMeshGrid', 'under grid', {'Size X': 1.0, 'Size Y': 1.0, 'Vertices X': 32, 'Vertices Y': 32})
    g.node('GeometryNodeTransform', 'under move', {'Geometry': ('under grid', 'Mesh'), 'Translation': (0.5, 0.5, 0.0)})
    g.node('GeometryNodeStoreNamedAttribute', 'under colour', {'Geometry': ('under move', 'Geometry'), 'Name': 'piece_colour', 'Value': srgb(18, 14, 12)}, data_type='FLOAT_COLOR', domain='POINT')
    g.node('GeometryNodeJoinGeometry', 'join', {})
    for node_ in ('planks colour', 'ridge colour', 'under colour'):
        g.link(node_, 'Geometry', 'join', 'Geometry')
    gt.finish_with_material_slot(g, 'join')
    return tree


def run(out_folder, size=1254, params=None, ambient_occlusion=0.8, quiet=False):
    p = {**DEFAULTS, **(params or {})}
    started = time.time()
    gt.new_scene(size)
    tree = build_wood_group(p)
    obj, modifier = gt.add_geometry_object('wood planks', tree)
    info = gt.photograph_geometry(obj, out_folder, size=size, normal_reference='wood', ambient_occlusion=ambient_occlusion, occlusion_distance=0.02,
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
