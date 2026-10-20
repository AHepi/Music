# What this does: RECIPE 7 - the Geometry-Nodes-only version of gravel: no physics. Random points (a few big, more medium, many small, very many tiny, each with a 'radius'
# attribute) -> a Repeat zone pushes overlapping points apart the wrap-around way (relax_tools.py) -> Instance on Points with Pick Instance chooses one of 8 angular stone
# shapes (Convex Hull of a jittered cube) per point, with random size, flatness, turn and tilt -> Realize -> flat colour per facet (stone-type palette x a pretend light) ->
# Join with an earth sheet. The whole thing evaluates in a few seconds (the rigid-body version takes minutes) but the stones never stack or lean on each other.
# Run:  blender -b --disable-autoexec -t 2 --python recipe_gravel_scatter_gn.py -- OUT_FOLDER [--size 1254] [--ao 0.8]
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy  # noqa: E402
import gn_tools as gt  # noqa: E402
import relax_tools as rx  # noqa: E402
import recipe_gravel_rigidbody as rg  # noqa: E402  (only for its earth sheet)

make_ramp, srgb = gt.make_ramp, gt.srgb
DEFAULTS = dict(big=22, medium=110, small=520, tiny=1500, iterations=60, tightness=0.95, seed=3, variants=8)
CLASSES = [('big', 0.045, 0.066), ('medium', 0.022, 0.040), ('small', 0.011, 0.020), ('tiny', 0.0055, 0.0095)]   # radius ranges in tile units


def stone_variant(g, index):
    """A unit-size angular stone: the Convex Hull of a cube with 26 surface points, each jittered a little. Returns (node, socket)."""
    tag = f'variant{index}'
    g.node('GeometryNodeMeshCube', f'{tag} cube', {'Size': (1.0, 0.8, 0.55), 'Vertices X': 3, 'Vertices Y': 3, 'Vertices Z': 3})
    g.node('FunctionNodeRandomValue', f'{tag} jitter', {'Min': (-0.14, -0.14, -0.2), 'Max': (0.14, 0.14, 0.2), 'Seed': 30 + index}, data_type='FLOAT_VECTOR')
    g.node('GeometryNodeSetPosition', f'{tag} jittered', {'Geometry': (f'{tag} cube', 'Mesh'), 'Offset': (f'{tag} jitter', 'Value')})
    g.node('GeometryNodeConvexHull', f'{tag} hull', {'Geometry': (f'{tag} jittered', 'Geometry')})
    g.node('GeometryNodeSetShadeSmooth', f'{tag} flat', {'Mesh': (f'{tag} hull', 'Convex Hull'), 'Shade Smooth': False})
    g.node('GeometryNodeGeometryToInstance', f'{tag} instance', {'Geometry': (f'{tag} flat', 'Mesh')})
    return f'{tag} instance', 'Instances'


def build_group(p):
    tree, g = gt.make_geometry_group('Gravel scatter', [('Geometry', 'NodeSocketGeometry', None)])
    relax = rx.relax_group_with_radius()
    # ---------------------------------------------------------------- points per class, each with a radius, then joined
    g.node('GeometryNodeMeshGrid', 'grid', {'Size X': 1.0, 'Size Y': 1.0, 'Vertices X': 2, 'Vertices Y': 2})
    g.node('GeometryNodeTransform', 'grid move', {'Geometry': ('grid', 'Mesh'), 'Translation': (0.5, 0.5, 0.0)})
    classes = []
    for number, (name, low, high) in enumerate(CLASSES):
        count = p[name]
        g.node('GeometryNodeDistributePointsOnFaces', f'{name} points', {'Mesh': ('grid move', 'Geometry'), 'Density': float(count), 'Seed': p['seed'] + number}, distribute_method='RANDOM')
        g.node('FunctionNodeRandomValue', f'{name} radius', {'Min': low, 'Max': high, 'Seed': 60 + number}, data_type='FLOAT')
        g.node('GeometryNodeStoreNamedAttribute', f'{name} radius stored', {'Geometry': (f'{name} points', 'Points'), 'Name': 'radius', 'Value': (f'{name} radius', 'Value')}, data_type='FLOAT', domain='POINT')
        classes.append(f'{name} radius stored')
    g.node('GeometryNodeJoinGeometry', 'all points', {})
    for node in classes:
        g.link(node, 'Geometry', 'all points', 'Geometry')
    g.group('relax', relax, {'Points': ('all points', 'Geometry'), 'Iterations': p['iterations'], 'Tightness': p['tightness']})
    # ---------------------------------------------------------------- copies for the wrap, keeping only those that reach into the tile
    copies = []
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            g.node('GeometryNodeTransform', f'relaxed copy {dx} {dy}', {'Geometry': ('relax', 'Points'), 'Translation': (float(dx), float(dy), 0.0)})
            copies.append(f'relaxed copy {dx} {dy}')
    g.node('GeometryNodeJoinGeometry', 'relaxed all', {})
    for node in copies:
        g.link(node, 'Geometry', 'relaxed all', 'Geometry')
    g.node('GeometryNodeInputPosition', 'copy pos')
    g.node('ShaderNodeSeparateXYZ', 'copy xyz', {'Vector': ('copy pos', 'Position')})
    g.node('GeometryNodeInputNamedAttribute', 'radius read', {'Name': 'radius'}, data_type='FLOAT')
    g.math('margin low', 'SUBTRACT', 0.0, ('radius read', 'Attribute'))
    g.math('margin high', 'ADD', 1.0, ('radius read', 'Attribute'))
    outside = []
    for label, coordinate, op, limit in (('x low', 'X', 'LESS_THAN', 'margin low'), ('x high', 'X', 'GREATER_THAN', 'margin high'), ('y low', 'Y', 'LESS_THAN', 'margin low'), ('y high', 'Y', 'GREATER_THAN', 'margin high')):
        g.node('FunctionNodeCompare', f'out {label}', {'A': ('copy xyz', coordinate), 'B': (limit, 0)}, data_type='FLOAT', operation=op)
        outside.append(f'out {label}')
    g.node('FunctionNodeBooleanMath', 'out x', {0: ('out x low', 'Result'), 1: ('out x high', 'Result')}, operation='OR')
    g.node('FunctionNodeBooleanMath', 'out y', {0: ('out y low', 'Result'), 1: ('out y high', 'Result')}, operation='OR')
    g.node('FunctionNodeBooleanMath', 'out any', {0: ('out x', 'Boolean'), 1: ('out y', 'Boolean')}, operation='OR')
    g.node('GeometryNodeDeleteGeometry', 'near copies', {'Geometry': ('relaxed all', 'Geometry'), 'Selection': ('out any', 'Boolean')}, domain='POINT')
    # ---------------------------------------------------------------- stones: pick a shape, random size/flatness/turn/tilt; smaller stones sit a little higher
    variants = [stone_variant(g, i) for i in range(p['variants'])]
    g.node('GeometryNodeJoinGeometry', 'variants', {})
    for node, socket in variants:
        g.link(node, socket, 'variants', 'Geometry')
    g.node('GeometryNodeInputNamedAttribute', 'r', {'Name': 'radius'}, data_type='FLOAT')
    g.node('FunctionNodeRandomValue', 'pick', {'Min': 0, 'Max': p['variants'] - 1, 'Seed': 3}, data_type='INT')
    g.math('size', 'MULTIPLY', ('r', 'Attribute'), 1.7)        # a random turn of the shape fits in a circle of about 0.6 x its size, so size = 1.7 x the radius it asked for
    g.node('FunctionNodeRandomValue', 'flat', {'Min': 0.7, 'Max': 1.1, 'Seed': 4}, data_type='FLOAT')
    g.math('size y', 'MULTIPLY', ('size', 0), ('flat', 'Value'))
    g.node('FunctionNodeRandomValue', 'thick', {'Min': 0.8, 'Max': 1.3, 'Seed': 5}, data_type='FLOAT')
    g.math('size z', 'MULTIPLY', ('size', 0), ('thick', 'Value'))
    g.node('ShaderNodeCombineXYZ', 'scale', {'X': ('size', 0), 'Y': ('size y', 0), 'Z': ('size z', 0)})
    g.node('FunctionNodeRandomValue', 'turn', {'Min': (-0.4, -0.4, 0.0), 'Max': (0.4, 0.4, 6.283), 'Seed': 6}, data_type='FLOAT_VECTOR')
    g.node('FunctionNodeEulerToRotation', 'turn rotation', {'Euler': ('turn', 'Value')})
    g.math('lift', 'MULTIPLY', ('size z', 0), 0.28)
    g.node('GeometryNodeInputPosition', 'stone pos')
    g.node('ShaderNodeCombineXYZ', 'lift v', {'Z': ('lift', 0)})
    g.vmath('stone place', 'ADD', ('stone pos', 'Position'), ('lift v', 'Vector'))
    g.node('GeometryNodeSetPosition', 'stones lifted', {'Geometry': ('near copies', 'Geometry'), 'Position': ('stone place', 0)})
    g.node('GeometryNodeInstanceOnPoints', 'stones', {'Points': ('stones lifted', 'Geometry'), 'Instance': ('variants', 'Geometry'), 'Pick Instance': True, 'Instance Index': ('pick', 'Value'),
                                                      'Rotation': ('turn rotation', 'Rotation'), 'Scale': ('scale', 'Vector')})
    g.node('FunctionNodeRandomValue', 'type random', {'Seed': 8}, data_type='FLOAT')
    g.node('GeometryNodeStoreNamedAttribute', 'store tone', {'Geometry': ('stones', 'Instances'), 'Name': 'stone_tone', 'Value': ('type random', 'Value')}, data_type='FLOAT', domain='INSTANCE')
    g.node('GeometryNodeRealizeInstances', 'real instances', {'Geometry': ('store tone', 'Geometry')})
    g.node('GeometryNodeSplitEdges', 'real', {'Mesh': ('real instances', 'Geometry')})      # every facet gets its own vertices, so each facet can have its own colour
    g.node('GeometryNodeInputNamedAttribute', 'tone', {'Name': 'stone_tone'}, data_type='FLOAT')
    g.node('GeometryNodeInputNormal', 'normal')
    g.node('ShaderNodeSeparateXYZ', 'normal xyz', {'Vector': ('normal', 'Normal')})
    # a pretend light from the upper left: facets turned toward it are lighter
    g.math('lit a', 'MULTIPLY', ('normal xyz', 'X'), -0.4)
    g.math('lit b', 'MULTIPLY', ('normal xyz', 'Y'), 0.55)
    g.math('lit c', 'MULTIPLY', ('normal xyz', 'Z'), 0.75)
    g.math('lit ab', 'ADD', ('lit a', 0), ('lit b', 0))
    g.math('lit', 'ADD', ('lit ab', 0), ('lit c', 0))
    g.math('facet light', 'MULTIPLY_ADD', ('lit', 0), 0.62, 0.62, clamp=False)
    g.node('GeometryNodeInputPosition', 'vpos')
    g.group('facet noise', gt.tileable_noise_geo_group(), {'Position': ('vpos', 'Position'), 'Scale': 60.0, 'Detail': 2.0})
    g.math('noise small', 'MULTIPLY', ('facet noise', 'Fac'), 0.5)
    g.math('light with noise', 'ADD', ('facet light', 0), ('noise small', 0))
    g.math('light final', 'SUBTRACT', ('light with noise', 0), 0.25)
    # stone-type palette by tone: 0-0.33 blue-grey, 0.33-0.66 black, 0.66-0.86 rust, 0.86-1 tan
    make_ramp(g, 'stone light colour', [(0.0, (96, 106, 114)), (0.40, (50, 52, 58)), (0.80, (150, 92, 60)), (0.94, (150, 120, 92))], {'Fac': ('tone', 'Attribute')}, interpolation='CONSTANT')
    g.node('ShaderNodeMix', 'shaded', {'Factor': 1.0, 'A': ('stone light colour', 'Color'), 'B': (1.0, 1.0, 1.0, 1.0)}, data_type='RGBA', blend_type='MULTIPLY')
    g.node('FunctionNodeCombineColor', 'light grey', {'Red': ('light final', 0), 'Green': ('light final', 0), 'Blue': ('light final', 0), 'Alpha': 1.0})
    g.link('light grey', 'Color', 'shaded', 'B')
    g.node('GeometryNodeStoreNamedAttribute', 'stone colour', {'Geometry': ('real', 'Mesh'), 'Name': 'piece_colour', 'Value': ('shaded', 'Result')}, data_type='FLOAT_COLOR', domain='POINT')
    gt.finish_with_material_slot(g, 'stone colour')
    return tree


def run(out_folder, size=1254, params=None, ambient_occlusion=0.8, quiet=False):
    p = {**DEFAULTS, **(params or {})}
    started = time.time()
    gt.new_scene(size)
    tree = build_group(p)
    stones, _ = gt.add_geometry_object('gravel stones', tree)
    earth = rg.earth_object()
    info = gt.photograph_geometry([stones, earth], out_folder, size=size, normal_reference='gravel', ambient_occlusion=ambient_occlusion, occlusion_distance=0.02,
                                  colour_samples=16 if ambient_occlusion else 4, quiet=quiet, z_percentiles=(0.0, 99.99))
    info['total_seconds'] = round(time.time() - started, 1)
    info['parameters'] = p
    with open(os.path.join(out_folder, 'photo.json'), 'w') as handle:
        json.dump(info, handle, indent=1)
    return info


if __name__ == '__main__':
    arguments = sys.argv[sys.argv.index('--') + 1:]
    option = lambda name, default=None: arguments[arguments.index(name) + 1] if name in arguments else default
    run(arguments[0], size=int(option('--size', 1254)), ambient_occlusion=float(option('--ao', 0.8)))
