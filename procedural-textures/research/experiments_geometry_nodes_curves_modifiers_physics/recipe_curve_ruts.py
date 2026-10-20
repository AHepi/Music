# What this does: RECIPE 4 - makes wet mud with wheel RUTS out of CURVES, then photographs it from straight above (height, colour, normal pictures of a
# 1 x 1 seamless tile). The ruts are real curves; the ground is a dense sheet that is pushed down/up by its distance to those curves.
# Chain (read top to bottom in the Geometry Node editor):
#   1. Rut curves: for each track, Mesh Line (one point per step along x) -> Set Position (y = start + slope * x + wiggles of two sine waves) ->
#      Mesh to Curve -> Resample Curve -> Set Position with tileable noise (the wheel path is never perfectly smooth) -> Curve to Mesh (no profile =
#      plain edges). A track is a PAIR: the same curve moved up and down by half the wheel gauge. SLOPE must be a whole number (-1, 0, +1) and the
#      sine waves must have whole numbers of waves, so the path leaves the right edge at exactly the height where it re-enters on the left (a closed
#      loop on the donut-shaped tile). All curves are copied into the 8 neighbouring tiles (Transform Geometry x 9 + Join) so the distance is right at the seam.
#   2. Ground: a dense Grid (0..1) -> Geometry Proximity (target = the rut edges, "Edges") gives every vertex its distance to the nearest rut ->
#      a Float Curve turns distance into a rut profile (deep groove in the middle, raised berm on each side, flat far away) -> Set Position z.
#      + tileable noise for clumps; + puddles: where a big noise is high the ground is flattened to a water level (a flat blue surface).
#   3. Stones: Distribute Points on Faces (Poisson Disk, so stones keep apart) on the ground, only where a cluster noise is high and not in a puddle ->
#      copied into the 8 neighbouring tiles (Duplicate Elements) -> Raycast straight down onto the ground to get each stone's resting height ->
#      Instance on Points (a squashed Ico Sphere shape, random size/rotation) -> Realize.
#   4. Colours are stored as a 'piece_colour' attribute (mud brown from height and noise, dark wet band in the groove, blue puddles, dark stones).
# Run:  blender -b --disable-autoexec -t 2 --python recipe_curve_ruts.py -- OUT_FOLDER [--size 1254] [--ao 0.8] [--wrap 1|0]
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy  # noqa: E402
import gn_tools as gt  # noqa: E402

make_ramp, srgb = gt.make_ramp, gt.srgb
TRACKS = [   # slope (whole number!), start height, wiggle 1 (amplitude, whole number of waves, phase), wiggle 2
    dict(slope=-1, y0=0.15, a1=0.075, k1=2, p1=0.3, a2=0.02, k2=5, p2=1.0),
    dict(slope=-1, y0=0.62, a1=0.060, k1=3, p1=1.7, a2=0.02, k2=4, p2=0.2),
    dict(slope=1, y0=0.85, a1=0.080, k1=1, p1=2.4, a2=0.025, k2=3, p2=2.2),
]
DEFAULTS = dict(gauge=0.075, rut_width=0.05, rut_depth=0.014, berm=0.007, clump=0.005, puddle_level=-0.010, grid=400, seed=2, stone_density=45.0, stone_min_distance=0.028, wrap=True)


def rut_curve_nodes(g, tag, track, p, noise_group):
    """Builds one rut path and returns (node_name, socket) of its edge mesh, still inside the tile (not yet copied)."""
    g.node('GeometryNodeMeshLine', f'{tag} line', {'Count': 200, 'Offset': (1.0 / 200, 0.0, 0.0)}, mode='OFFSET')
    g.node('GeometryNodeInputPosition', f'{tag} pos')
    g.node('ShaderNodeSeparateXYZ', f'{tag} xyz', {'Vector': (f'{tag} pos', 'Position')})
    tau = 2 * math.pi
    g.math(f'{tag} w1', 'MULTIPLY', ('{} xyz'.format(tag), 'X'), tau * track['k1'])
    g.math(f'{tag} w1 phase', 'ADD', (f'{tag} w1', 0), track['p1'])
    g.math(f'{tag} s1', 'SINE', (f'{tag} w1 phase', 0))
    g.math(f'{tag} s1 amp', 'MULTIPLY', (f'{tag} s1', 0), track['a1'])
    g.math(f'{tag} w2', 'MULTIPLY', (f'{tag} xyz', 'X'), tau * track['k2'])
    g.math(f'{tag} w2 phase', 'ADD', (f'{tag} w2', 0), track['p2'])
    g.math(f'{tag} s2', 'SINE', (f'{tag} w2 phase', 0))
    g.math(f'{tag} s2 amp', 'MULTIPLY', (f'{tag} s2', 0), track['a2'])
    g.math(f'{tag} slope part', 'MULTIPLY', (f'{tag} xyz', 'X'), float(track['slope']))
    g.math(f'{tag} y sum 1', 'ADD', (f'{tag} slope part', 0), (f'{tag} s1 amp', 0))
    g.math(f'{tag} y sum 2', 'ADD', (f'{tag} y sum 1', 0), (f'{tag} s2 amp', 0))
    g.math(f'{tag} y', 'ADD', (f'{tag} y sum 2', 0), track['y0'])
    g.node('ShaderNodeCombineXYZ', f'{tag} point', {'X': (f'{tag} xyz', 'X'), 'Y': (f'{tag} y', 0), 'Z': 0.0})
    g.node('GeometryNodeSetPosition', f'{tag} placed', {'Geometry': (f'{tag} line', 'Mesh'), 'Position': (f'{tag} point', 'Vector')})
    g.node('GeometryNodeMeshToCurve', f'{tag} curve', {'Mesh': (f'{tag} placed', 'Geometry')})
    g.node('GeometryNodeResampleCurve', f'{tag} resample', {'Curve': (f'{tag} curve', 'Curve'), 'Mode': 'Count', 'Count': 240})
    # a little irregular wobble of the wheel path (tileable noise of x only, so it still wraps)
    g.node('GeometryNodeInputPosition', f'{tag} pos2')
    g.node('ShaderNodeSeparateXYZ', f'{tag} xyz2', {'Vector': (f'{tag} pos2', 'Position')})
    g.node('ShaderNodeCombineXYZ', f'{tag} noise at', {'X': (f'{tag} xyz2', 'X'), 'Y': 0.37, 'Z': 0.0})
    g.group(f'{tag} wobble noise', noise_group, {'Position': (f'{tag} noise at', 'Vector'), 'Scale': 9.0, 'Detail': 3.0, 'Roughness': 0.5, 'Seed': float(track['y0'] * 10)})
    g.node('ShaderNodeMapRange', f'{tag} wobble', {'Value': (f'{tag} wobble noise', 'Fac'), 'From Min': 0.3, 'From Max': 0.7, 'To Min': -0.012, 'To Max': 0.012})
    g.node('ShaderNodeCombineXYZ', f'{tag} wobble move', {'Y': (f'{tag} wobble', 'Result')})
    g.node('GeometryNodeSetPosition', f'{tag} wobbly', {'Geometry': (f'{tag} resample', 'Curve'), 'Offset': (f'{tag} wobble move', 'Vector')})
    g.node('GeometryNodeCurveToMesh', f'{tag} edges', {'Curve': (f'{tag} wobbly', 'Geometry')})
    return f'{tag} edges', 'Mesh'


def build_mud_group(p):
    tree, g = gt.make_geometry_group('Mud with ruts', [('Geometry', 'NodeSocketGeometry', None)])
    noise_group = gt.tileable_noise_geo_group()
    # ---------------------------------------------------------------- 1. all rut curves (pairs), then copies for the wrap
    pieces = []
    for index, track in enumerate(TRACKS):
        tag = f'track{index}'
        node, socket = rut_curve_nodes(g, tag, track, p, noise_group)
        for side, sign in (('a', -1), ('b', 1)):
            g.node('GeometryNodeTransform', f'{tag}{side}', {'Geometry': (node, socket), 'Translation': (0.0, sign * p['gauge'] / 2, 0.0)})
            pieces.append(f'{tag}{side}')
    g.node('GeometryNodeJoinGeometry', 'all ruts', {})
    for piece in pieces:
        g.link(piece, 'Geometry', 'all ruts', 'Geometry')
    copies = []
    shifts = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)] if p['wrap'] else [(0, 0)]
    for dx, dy in shifts:
        name = f'ruts copy {dx} {dy}'
        g.node('GeometryNodeTransform', name, {'Geometry': ('all ruts', 'Geometry'), 'Translation': (float(dx), float(dy), 0.0)})
        copies.append(name)
    g.node('GeometryNodeJoinGeometry', 'ruts and copies', {})
    for name in copies:
        g.link(name, 'Geometry', 'ruts and copies', 'Geometry')
    # ---------------------------------------------------------------- 2. the ground
    g.node('GeometryNodeMeshGrid', 'grid', {'Size X': 1.0, 'Size Y': 1.0, 'Vertices X': p['grid'], 'Vertices Y': p['grid']})
    g.node('GeometryNodeTransform', 'grid move', {'Geometry': ('grid', 'Mesh'), 'Translation': (0.5, 0.5, 0.0)})
    g.node('GeometryNodeInputPosition', 'position')
    g.node('GeometryNodeProximity', 'distance to ruts', {'Geometry': ('ruts and copies', 'Geometry'), 'Sample Position': ('position', 'Position')}, target_element='EDGES')
    g.math('distance scaled', 'DIVIDE', ('distance to ruts', 'Distance'), p['rut_width'])
    curve_node = g.node('ShaderNodeFloatCurve', 'rut profile', {'Factor': 1.0, 'Value': ('distance scaled', 0)})
    curve = curve_node.mapping.curves[0]
    # a Float Curve lives in a 0..1 box: 0.5 means "flat ground", below = groove, above = berm
    wanted = [(0.0, 0.02), (0.18, 0.05), (0.40, 0.30), (0.52, 0.52), (0.68, 0.92), (0.85, 0.62), (1.0, 0.5)]
    while len(curve.points) > 2:
        curve.points.remove(curve.points[-1])
    curve.points[0].location = wanted[0]
    curve.points[1].location = wanted[-1]
    for x, y in wanted[1:-1]:
        curve.points.new(x, y)
    for point in curve.points:
        point.handle_type = 'AUTO'
    curve_node.mapping.extend = 'HORIZONTAL'
    curve_node.mapping.update()
    g.node('ShaderNodeMapRange', 'profile to height', {'Value': ('rut profile', 0), 'From Min': 0.02, 'From Max': 0.92, 'To Min': -p['rut_depth'], 'To Max': p['berm']})
    g.group('clump noise', noise_group, {'Position': ('position', 'Position'), 'Scale': 26.0, 'Detail': 5.0, 'Roughness': 0.65, 'Seed': 2.0})
    g.node('ShaderNodeMapRange', 'clump centred', {'Value': ('clump noise', 'Fac'), 'From Min': 0.3, 'From Max': 0.7, 'To Min': -1.0, 'To Max': 1.0})
    g.math('clump height', 'MULTIPLY', ('clump centred', 'Result'), p['clump'])
    g.group('fine noise', noise_group, {'Position': ('position', 'Position'), 'Scale': 120.0, 'Detail': 3.0, 'Roughness': 0.5, 'Seed': 8.0})
    g.node('ShaderNodeMapRange', 'fine centred', {'Value': ('fine noise', 'Fac'), 'From Min': 0.3, 'From Max': 0.7, 'To Min': -1.0, 'To Max': 1.0})
    g.math('fine height', 'MULTIPLY', ('fine centred', 'Result'), p['clump'] * 0.25)
    g.math('mud 1', 'ADD', ('profile to height', 'Result'), ('clump height', 0))
    g.math('mud height', 'ADD', ('mud 1', 0), ('fine height', 0))
    # puddles: a big, slow noise; where it is high the ground is flattened down to the water level (sharp edge = a shore)
    g.group('puddle noise', noise_group, {'Position': ('position', 'Position'), 'Scale': 3.2, 'Detail': 4.0, 'Roughness': 0.55, 'Seed': 13.0})
    g.node('ShaderNodeMapRange', 'puddle edge', {'Value': ('puddle noise', 'Fac'), 'From Min': 0.575, 'From Max': 0.585, 'To Min': 0.0, 'To Max': 1.0})
    g.node('ShaderNodeMix', 'with puddles', {'Factor': ('puddle edge', 'Result'), 'A': ('mud height', 0), 'B': p['puddle_level']}, data_type='FLOAT')
    g.node('ShaderNodeCombineXYZ', 'ground z', {'Z': ('with puddles', 'Result')})
    g.node('GeometryNodeSetPosition', 'ground', {'Geometry': ('grid move', 'Geometry'), 'Offset': ('ground z', 'Vector')})
    # ---------------------------------------------------------------- ground colour
    g.group('colour noise', noise_group, {'Position': ('position', 'Position'), 'Scale': 14.0, 'Detail': 5.0, 'Roughness': 0.6, 'Seed': 21.0})
    g.math('height light', 'MULTIPLY_ADD', ('mud height', 0), 30.0, 0.5)
    g.math('tone', 'ADD', ('colour noise', 'Fac'), ('height light', 0))
    g.math('tone half', 'MULTIPLY', ('tone', 0), 0.55, clamp=True)
    make_ramp(g, 'mud palette', [(0.0, (46, 32, 28)), (0.30, (78, 50, 38)), (0.55, (112, 72, 50)), (0.80, (140, 92, 62)), (1.0, (150, 112, 84))], {'Fac': ('tone half', 0)})
    g.group('water noise', noise_group, {'Position': ('position', 'Position'), 'Scale': 22.0, 'Detail': 4.0, 'Roughness': 0.55, 'Seed': 31.0})
    make_ramp(g, 'water palette', [(0.3, (64, 66, 72)), (0.55, (86, 94, 104)), (0.8, (108, 118, 124))], {'Fac': ('water noise', 'Fac')})
    g.node('ShaderNodeMix', 'mud or water', {'Factor': ('puddle edge', 'Result'), 'A': ('mud palette', 'Color'), 'B': ('water palette', 'Color')}, data_type='RGBA')
    g.node('ShaderNodeMapRange', 'wet band', {'Value': ('rut profile', 0), 'From Min': 0.30, 'From Max': 0.05, 'To Min': 0.0, 'To Max': 0.8})   # darker where the groove is deepest
    g.node('ShaderNodeMix', 'with wet groove', {'Factor': ('wet band', 'Result'), 'A': ('mud or water', 'Result'), 'B': srgb(38, 28, 26)}, data_type='RGBA')
    g.node('GeometryNodeStoreNamedAttribute', 'ground colour', {'Geometry': ('ground', 'Geometry'), 'Name': 'piece_colour', 'Value': ('with wet groove', 'Result')}, data_type='FLOAT_COLOR', domain='POINT')
    # ---------------------------------------------------------------- 3. stones
    g.group('cluster noise', noise_group, {'Position': ('position', 'Position'), 'Scale': 3.0, 'Detail': 3.0, 'Roughness': 0.5, 'Seed': 44.0})
    g.node('ShaderNodeMapRange', 'cluster', {'Value': ('cluster noise', 'Fac'), 'From Min': 0.46, 'From Max': 0.60, 'To Min': 0.05, 'To Max': 1.0})
    g.math('not puddle', 'SUBTRACT', 1.0, ('puddle edge', 'Result'))
    g.math('stone chance', 'MULTIPLY', ('cluster', 'Result'), ('not puddle', 0))
    g.node('GeometryNodeDistributePointsOnFaces', 'stone points', {'Mesh': ('grid move', 'Geometry'), 'Distance Min': p['stone_min_distance'], 'Density Max': p['stone_density'] * 22,
                                                                    'Density Factor': ('stone chance', 0), 'Seed': p['seed']}, distribute_method='POISSON')
    copies = []
    for dx, dy in shifts:
        name = f'stone copy {dx} {dy}'
        g.node('GeometryNodeTransform', name, {'Geometry': ('stone points', 'Points'), 'Translation': (float(dx), float(dy), 0.0)})
        copies.append(name)
    g.node('GeometryNodeJoinGeometry', 'stone points all', {})
    for name in copies:
        g.link(name, 'Geometry', 'stone points all', 'Geometry')
    # keep only the copies that can reach into the tile (centre within 0.12 of it); the others would just cost time
    g.node('GeometryNodeInputPosition', 'copy pos')
    g.node('ShaderNodeSeparateXYZ', 'copy xyz', {'Vector': ('copy pos', 'Position')})
    outside = []
    for label, coordinate, op, limit in (('x low', 'X', 'LESS_THAN', -0.12), ('x high', 'X', 'GREATER_THAN', 1.12), ('y low', 'Y', 'LESS_THAN', -0.12), ('y high', 'Y', 'GREATER_THAN', 1.12)):
        g.node('FunctionNodeCompare', f'out {label}', {'A': ('copy xyz', coordinate), 'B': limit}, data_type='FLOAT', operation=op)
        outside.append(f'out {label}')
    g.node('FunctionNodeBooleanMath', 'out x', {0: ('out x low', 'Result'), 1: ('out x high', 'Result')}, operation='OR')
    g.node('FunctionNodeBooleanMath', 'out y', {0: ('out y low', 'Result'), 1: ('out y high', 'Result')}, operation='OR')
    g.node('FunctionNodeBooleanMath', 'out any', {0: ('out x', 'Boolean'), 1: ('out y', 'Boolean')}, operation='OR')
    g.node('GeometryNodeDeleteGeometry', 'near copies', {'Geometry': ('stone points all', 'Geometry'), 'Selection': ('out any', 'Boolean')}, domain='POINT')
    # rest each stone on the ground: shoot a ray straight down from above each point at the ground sheet
    g.node('GeometryNodeInputPosition', 'stone pos')
    g.node('ShaderNodeSeparateXYZ', 'stone xyz', {'Vector': ('stone pos', 'Position')})
    # a stone in a neighbouring-tile copy sits at x < 0 or > 1, where there is no ground sheet: look the ground up at the WRAPPED place (the ground repeats)
    g.math('x wrapped', 'WRAP', ('stone xyz', 'X'), 1.0, 0.0)
    g.math('y wrapped', 'WRAP', ('stone xyz', 'Y'), 1.0, 0.0)
    g.node('ShaderNodeCombineXYZ', 'ray start', {'X': ('x wrapped', 0), 'Y': ('y wrapped', 0), 'Z': 1.0})
    g.node('GeometryNodeRaycast', 'find ground', {'Target Geometry': ('ground', 'Geometry'), 'Source Position': ('ray start', 'Vector'), 'Ray Direction': (0.0, 0.0, -1.0), 'Ray Length': 3.0})
    g.node('ShaderNodeSeparateXYZ', 'hit xyz', {'Vector': ('find ground', 'Hit Position')})
    g.node('ShaderNodeCombineXYZ', 'rest place', {'X': ('stone xyz', 'X'), 'Y': ('stone xyz', 'Y'), 'Z': ('hit xyz', 'Z')})
    g.node('GeometryNodeSetPosition', 'stones on ground', {'Geometry': ('near copies', 'Geometry'), 'Position': ('rest place', 'Vector')})
    # random size: many small, few big (cube of a random number); random turn; flatter than tall
    g.node('FunctionNodeRandomValue', 'size random', {'Min': 0.0, 'Max': 1.0, 'Seed': 5}, data_type='FLOAT')
    g.math('size cubed', 'POWER', ('size random', 'Value'), 2.6)
    g.math('size', 'MULTIPLY_ADD', ('size cubed', 0), 0.085, 0.016)
    g.node('FunctionNodeRandomValue', 'height factor', {'Min': 0.55, 'Max': 0.9, 'Seed': 6}, data_type='FLOAT')
    g.math('stone height', 'MULTIPLY', ('size', 0), ('height factor', 'Value'))
    g.node('ShaderNodeCombineXYZ', 'stone scale', {'X': ('size', 0), 'Y': ('size', 0), 'Z': ('stone height', 0)})
    g.node('FunctionNodeRandomValue', 'turn', {'Min': (0.0, 0.0, 0.0), 'Max': (0.35, 0.35, 6.283), 'Seed': 7}, data_type='FLOAT_VECTOR')
    g.node('FunctionNodeEulerToRotation', 'turn rotation', {'Euler': ('turn', 'Value')})
    g.node('GeometryNodeMeshIcoSphere', 'stone ball', {'Radius': 0.5, 'Subdivisions': 1})
    g.node('GeometryNodeInputPosition', 'ball pos')
    g.node('FunctionNodeRandomValue', 'ball jitter', {'Min': (-0.16, -0.16, -0.16), 'Max': (0.16, 0.16, 0.16), 'Seed': 9}, data_type='FLOAT_VECTOR')
    g.node('GeometryNodeSetPosition', 'ball angular', {'Geometry': ('stone ball', 'Mesh'), 'Offset': ('ball jitter', 'Value')})
    g.node('GeometryNodeSetShadeSmooth', 'ball flat', {'Mesh': ('ball angular', 'Geometry'), 'Shade Smooth': False})
    g.node('GeometryNodeInstanceOnPoints', 'stones', {'Points': ('stones on ground', 'Geometry'), 'Instance': ('ball flat', 'Mesh'), 'Rotation': ('turn rotation', 'Rotation'), 'Scale': ('stone scale', 'Vector')})
    g.node('FunctionNodeRandomValue', 'stone tone', {'Seed': 12}, data_type='FLOAT')
    g.node('GeometryNodeStoreNamedAttribute', 'store stone tone', {'Geometry': ('stones', 'Instances'), 'Name': 'stone_tone', 'Value': ('stone tone', 'Value')}, data_type='FLOAT', domain='INSTANCE')
    g.node('GeometryNodeRealizeInstances', 'stones real', {'Geometry': ('store stone tone', 'Geometry')})
    g.node('GeometryNodeInputNamedAttribute', 'stone tone read', {'Name': 'stone_tone'}, data_type='FLOAT')
    g.node('GeometryNodeInputNormal', 'stone normal')
    g.node('ShaderNodeSeparateXYZ', 'stone normal xyz', {'Vector': ('stone normal', 'Normal')})
    g.math('stone light', 'MULTIPLY_ADD', ('stone normal xyz', 'Z'), 0.35, 0.65)
    g.math('stone value', 'MULTIPLY', ('stone tone read', 'Attribute'), ('stone light', 0))
    make_ramp(g, 'stone palette', [(0.0, (22, 22, 26)), (0.25, (36, 40, 48)), (0.5, (56, 64, 76)), (0.8, (96, 100, 108)), (1.0, (138, 100, 70))], {'Fac': ('stone value', 0)})
    g.node('GeometryNodeStoreNamedAttribute', 'stone colour', {'Geometry': ('stones real', 'Geometry'), 'Name': 'piece_colour', 'Value': ('stone palette', 'Color')}, data_type='FLOAT_COLOR', domain='POINT')
    g.node('GeometryNodeJoinGeometry', 'join', {})
    g.link('ground colour', 'Geometry', 'join', 'Geometry')
    g.link('stone colour', 'Geometry', 'join', 'Geometry')
    gt.finish_with_material_slot(g, 'join')
    return tree


def run(out_folder, size=1254, params=None, ambient_occlusion=0.8, quiet=False):
    p = {**DEFAULTS, **(params or {})}
    started = time.time()
    gt.new_scene(size)
    tree = build_mud_group(p)
    obj, modifier = gt.add_geometry_object('mud', tree)
    info = gt.photograph_geometry(obj, out_folder, size=size, normal_reference='mud', ambient_occlusion=ambient_occlusion, occlusion_distance=0.02,
                                  colour_samples=16 if ambient_occlusion else 4, quiet=quiet)
    info['total_seconds'] = round(time.time() - started, 1)
    info['parameters'] = p
    with open(os.path.join(out_folder, 'photo.json'), 'w') as handle:
        json.dump(info, handle, indent=1)
    return info


if __name__ == '__main__':
    arguments = sys.argv[sys.argv.index('--') + 1:]
    option = lambda name, default=None: arguments[arguments.index(name) + 1] if name in arguments else default
    run(arguments[0], size=int(option('--size', 1254)), params={'wrap': option('--wrap', '1') == '1', 'grid': int(option('--grid', DEFAULTS['grid']))},
        ambient_occlusion=float(option('--ao', 0.8)))
