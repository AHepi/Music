# What this does (plain words): the REAL-GEOMETRY route, for an honest comparison with the flat "painter" route. It reads the SAME description (the
# layout block: rows, joints, slate heights, tones) and builds the roof as real 3D slate plates with Geometry Nodes:
#   * a small cloud of points, one per slate (and one per wrap-around copy), made from the description with the plate size and tone as point attributes;
#   * Geometry Nodes: Instance on Points (a thin box scaled to each slate, tilted so its lower edge lifts, so lower rows lie ON TOP of the slate
#     below) -> Realize Instances -> Mesh Bevel (rounded edges) -> Subdivide Mesh -> Set Position with seamless noise (ragged lower edge, wobbly outline)
#     -> colour from the slate's tone, moss near the top and a pale chipped lower edge -> Join with a dark underlay sheet that shows through the joints;
#   * the overhead "photo booth" (lib/contrib/gn_tools.photograph_geometry) takes height (true geometry), colour (with ambient occlusion: the crevices
#     go dark by themselves) and the geometry's own normal.
# Adapted from research/experiments_geometry_nodes_curves_modifiers_physics/recipe_slate_layout.py (copied and changed; the original is not edited).
# Use: blender -b --disable-autoexec -t 2 --python geometry_route_slabs.py -- DESCRIPTION.json OUT_FOLDER [--size 1254] [--ao 0.8]
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(PROC, 'lib')); sys.path.insert(0, os.path.join(PROC, 'lib', 'contrib')); sys.path.insert(0, HERE)
import bpy  # noqa: E402
import gn_tools as gt  # noqa: E402
import slate_layers as layers  # noqa: E402

make_ramp = gt.make_ramp
DEFAULTS = dict(height_factor=1.32, thickness=0.010, lift=0.020, bevel=0.0022, base_z=0.030, edge_wobble=0.0022, chip=0.012, subdiv=3)


def parameter_points(description):
    """One point per slate (plus wrap copies) with the attributes the Geometry Nodes group reads: piece_id, piece_w, piece_h, piece_centre, tone0."""
    tile = float(description['tile'])
    layout = description['layout']
    gap_v = 10.6
    points, ids, widths, heights, tones = [], [], [], [], []
    palette = np.array(description['palette'], float)
    grey = palette @ [0.299, 0.587, 0.114]
    n = 0
    for row in layout['rows']:
        for slate in layers.row_slates(row, tile):
            x0, x1 = slate[0], slate[1]
            top, bottom = row['top'] + slate[4], row['bottom'] + slate[5]
            h_slab = (bottom - top) * DEFAULTS['height_factor']
            centre = np.array([0.5 * (x0 + x1), bottom - 0.5 * h_slab])             # the lower edge stays where the slate's visible lower edge is
            tone0 = float(np.clip((grey[slate[6]] - 40.0) / 60.0, 0, 1))
            for ox in (-1, 0, 1):
                for oy in (-1, 0, 1):
                    cx, cy = centre[0] + ox * tile, centre[1] + oy * tile
                    if cx + (x1 - x0) / 2 < 0 or cx - (x1 - x0) / 2 > tile or cy + h_slab / 2 < 0 or cy - h_slab / 2 > tile:
                        continue
                    points.append((cx / tile, 1.0 - cy / tile, 0.0)); ids.append(n); widths.append((x1 - x0) / tile); heights.append(h_slab / tile); tones.append(tone0)
            n += 1
    return np.array(points), np.array(ids), np.array(widths), np.array(heights), np.array(tones)


def build_roof_group(p):
    tree, g = gt.make_geometry_group('Slate roof from description', [('Geometry', 'NodeSocketGeometry', None)])
    noise_group = gt.tileable_noise_geo_group()
    g.node('GeometryNodeMeshCube', 'cube', {'Size': (1.0, 1.0, 1.0), 'Vertices X': 2, 'Vertices Y': 2, 'Vertices Z': 2})
    g.node('GeometryNodeInputNamedAttribute', 'id', {'Name': 'piece_id'}, data_type='INT')
    g.node('GeometryNodeInputNamedAttribute', 'w', {'Name': 'piece_w'}, data_type='FLOAT')
    g.node('GeometryNodeInputNamedAttribute', 'h', {'Name': 'piece_h'}, data_type='FLOAT')
    g.node('FunctionNodeRandomValue', 'thick random', {'ID': ('id', 'Attribute'), 'Seed': 17, 'Min': 0.8, 'Max': 1.3}, data_type='FLOAT')
    g.math('thickness', 'MULTIPLY', ('thick random', 'Value'), p['thickness'])
    g.node('ShaderNodeCombineXYZ', 'scale', {'X': ('w', 'Attribute'), 'Y': ('h', 'Attribute'), 'Z': ('thickness', 0)})
    g.node('FunctionNodeRandomValue', 'lift random', {'ID': ('id', 'Attribute'), 'Seed': 41, 'Min': 0.7, 'Max': 1.3}, data_type='FLOAT')
    g.math('lift', 'MULTIPLY', ('lift random', 'Value'), p['lift'])
    g.math('tilt angle', 'ARCTAN2', ('lift', 0), ('h', 'Attribute'))
    g.math('tilt', 'MULTIPLY', ('tilt angle', 0), -1.0)
    g.node('FunctionNodeRandomValue', 'twist random', {'ID': ('id', 'Attribute'), 'Seed': 29, 'Min': -0.03, 'Max': 0.03}, data_type='FLOAT')
    g.node('ShaderNodeCombineXYZ', 'euler', {'X': ('tilt', 0), 'Z': ('twist random', 'Value')})
    g.node('FunctionNodeEulerToRotation', 'rotation', {'Euler': ('euler', 'Vector')})
    g.node('GeometryNodeInstanceOnPoints', 'slates', {'Points': ('in', 'Geometry'), 'Instance': ('cube', 'Mesh'), 'Rotation': ('rotation', 'Rotation'), 'Scale': ('scale', 'Vector')})
    g.node('GeometryNodeInputNamedAttribute', 'tone0', {'Name': 'tone0'}, data_type='FLOAT')
    g.node('GeometryNodeStoreNamedAttribute', 'store tone', {'Geometry': ('slates', 'Instances'), 'Name': 'slate_tone', 'Value': ('tone0', 'Attribute')}, data_type='FLOAT', domain='INSTANCE')
    g.node('GeometryNodeRealizeInstances', 'realize', {'Geometry': ('store tone', 'Geometry')})
    g.node('GeometryNodeInputMeshEdgeAngle', 'edge angle')
    g.node('FunctionNodeCompare', 'sharp edges', {'A': ('edge angle', 'Unsigned Angle'), 'B': 0.6}, data_type='FLOAT', operation='GREATER_THAN')
    g.node('GeometryNodeMeshBevel', 'bevel', {'Mesh': ('realize', 'Geometry'), 'Selection': ('sharp edges', 'Result'), 'Start Left Offset': p['bevel'], 'Start Right Offset': p['bevel'],
                                                'End Left Offset': p['bevel'], 'End Right Offset': p['bevel'], 'Segments': 1})
    g.node('GeometryNodeSubdivideMesh', 'subdivide', {'Mesh': ('bevel', 'Mesh'), 'Level': p['subdiv']})
    g.node('GeometryNodeInputPosition', 'position')
    g.node('ShaderNodeSeparateXYZ', 'position xyz', {'Vector': ('position', 'Position')})
    g.node('GeometryNodeInputNamedAttribute', 'centre', {'Name': 'piece_centre'}, data_type='FLOAT_VECTOR')
    g.node('ShaderNodeSeparateXYZ', 'centre xyz', {'Vector': ('centre', 'Attribute')})
    g.math('local y', 'SUBTRACT', ('position xyz', 'Y'), ('centre xyz', 'Y'))
    g.node('GeometryNodeInputNamedAttribute', 'h v', {'Name': 'piece_h'}, data_type='FLOAT')
    g.math('local y relative', 'DIVIDE', ('local y', 0), ('h v', 'Attribute'))
    g.node('ShaderNodeMapRange', 'lower edge weight', {'Value': ('local y relative', 0), 'From Min': -0.5, 'From Max': -0.30, 'To Min': 1.0, 'To Max': 0.0})
    g.node('ShaderNodeMapRange', 'upper weight', {'Value': ('local y relative', 0), 'From Min': -0.1, 'From Max': 0.5, 'To Min': 0.0, 'To Max': 1.0})
    g.node('GeometryNodeInputNamedAttribute', 'id v', {'Name': 'piece_id'}, data_type='INT')
    g.math('seed per slate', 'MULTIPLY', ('id v', 'Attribute'), 7.3)
    g.group('chip noise', noise_group, {'Position': ('position', 'Position'), 'Scale': 45.0, 'Detail': 4.0, 'Roughness': 0.6, 'Seed': ('seed per slate', 0)})
    g.group('wobble noise x', noise_group, {'Position': ('position', 'Position'), 'Scale': 26.0, 'Detail': 3.0, 'Roughness': 0.5, 'Seed': ('seed per slate', 0)})
    g.math('seed y', 'ADD', ('seed per slate', 0), 31.0)
    g.group('wobble noise y', noise_group, {'Position': ('position', 'Position'), 'Scale': 26.0, 'Detail': 3.0, 'Roughness': 0.5, 'Seed': ('seed y', 0)})
    for name_, source in (('chip centred', 'chip noise'), ('wobble x', 'wobble noise x'), ('wobble y', 'wobble noise y')):
        g.node('ShaderNodeMapRange', name_, {'Value': (source, 'Fac'), 'From Min': 0.3, 'From Max': 0.7, 'To Min': -1.0, 'To Max': 1.0})
    g.math('chip 0..1', 'MULTIPLY_ADD', ('chip centred', 'Result'), 0.5, 0.5)
    g.math('chip amount', 'MULTIPLY', ('chip 0..1', 0), ('lower edge weight', 'Result'))
    g.math('chip up', 'MULTIPLY', ('chip amount', 0), p['chip'])
    g.math('wobble amount x', 'MULTIPLY', ('wobble x', 'Result'), p['edge_wobble'])
    g.math('wobble amount y', 'MULTIPLY', ('wobble y', 'Result'), p['edge_wobble'])
    g.math('y move', 'ADD', ('chip up', 0), ('wobble amount y', 0))
    g.node('ShaderNodeCombineXYZ', 'outline move', {'X': ('wobble amount x', 0), 'Y': ('y move', 0), 'Z': 0.0})
    g.node('GeometryNodeSetPosition', 'ragged', {'Geometry': ('subdivide', 'Mesh'), 'Offset': ('outline move', 'Vector')})
    g.node('GeometryNodeTransform', 'raise slates', {'Geometry': ('ragged', 'Geometry'), 'Translation': (0.0, 0.0, p['base_z'])})
    g.node('GeometryNodeSetShadeSmooth', 'smooth', {'Mesh': ('raise slates', 'Geometry'), 'Shade Smooth': True})
    g.node('GeometryNodeInputNamedAttribute', 'tone', {'Name': 'slate_tone'}, data_type='FLOAT')
    g.group('moss noise', noise_group, {'Position': ('position', 'Position'), 'Scale': 8.0, 'Detail': 5.0, 'Roughness': 0.6, 'Seed': ('seed per slate', 0)})
    g.node('ShaderNodeMapRange', 'moss patch', {'Value': ('moss noise', 'Fac'), 'From Min': 0.50, 'From Max': 0.58, 'To Min': 0.0, 'To Max': 1.0})
    g.math('moss amount', 'MULTIPLY', ('moss patch', 'Result'), ('upper weight', 'Result'))
    g.math('tone mix', 'MULTIPLY_ADD', ('tone', 'Attribute'), 0.8, 0.0)
    g.math('fine part', 'MULTIPLY', ('chip centred', 'Result'), 0.10)
    g.math('tone sum 1', 'ADD', ('tone mix', 0), ('fine part', 0))
    g.math('tone sum', 'ADD', ('tone sum 1', 0), 0.12, clamp=True)
    make_ramp(g, 'slate palette', [(0.00, (20, 21, 23)), (0.25, (40, 44, 46)), (0.55, (62, 70, 72)), (0.85, (84, 94, 94)), (1.0, (110, 112, 108))], {'Fac': ('tone sum', 0)})
    g.node('ShaderNodeMix', 'with moss', {'Factor': ('moss amount', 0), 'A': ('slate palette', 'Color'), 'B': gt.srgb(86, 92, 48)}, data_type='RGBA', blend_type='MIX')
    g.math('pale edge', 'MULTIPLY', ('lower edge weight', 'Result'), ('chip 0..1', 0))
    g.node('ShaderNodeMix', 'with pale edge', {'Factor': ('pale edge', 0), 'A': ('with moss', 'Result'), 'B': gt.srgb(150, 130, 112)}, data_type='RGBA', blend_type='MIX')
    g.node('GeometryNodeStoreNamedAttribute', 'store colour', {'Geometry': ('smooth', 'Mesh'), 'Name': 'piece_colour', 'Value': ('with pale edge', 'Result')}, data_type='FLOAT_COLOR', domain='POINT')
    g.node('GeometryNodeMeshGrid', 'under grid', {'Size X': 1.0, 'Size Y': 1.0, 'Vertices X': 64, 'Vertices Y': 64})
    g.node('GeometryNodeTransform', 'under move', {'Geometry': ('under grid', 'Mesh'), 'Translation': (0.5, 0.5, 0.0)})
    g.node('GeometryNodeStoreNamedAttribute', 'under colour', {'Geometry': ('under move', 'Geometry'), 'Name': 'piece_colour', 'Value': gt.srgb(10, 10, 12)}, data_type='FLOAT_COLOR', domain='POINT')
    g.node('GeometryNodeJoinGeometry', 'join', {})
    g.link('store colour', 'Geometry', 'join', 'Geometry')
    g.link('under colour', 'Geometry', 'join', 'Geometry')
    gt.finish_with_material_slot(g, 'join')
    return tree


def run(description, out_folder, size=1254, ambient_occlusion=0.8, quiet=False):
    started = time.time()
    p = dict(DEFAULTS)
    gt.new_scene(size)
    pts, ids, widths, heights, tones = parameter_points(description)
    mesh = bpy.data.meshes.new('slate points')
    mesh.from_pydata([tuple(v) for v in pts], [], [])
    for name, kind, values in (('piece_id', 'INT', ids), ('piece_w', 'FLOAT', widths), ('piece_h', 'FLOAT', heights), ('tone0', 'FLOAT', tones)):
        a = mesh.attributes.new(name, kind, 'POINT')
        a.data.foreach_set('value', values.astype(np.int32 if kind == 'INT' else np.float32))
    a = mesh.attributes.new('piece_centre', 'FLOAT_VECTOR', 'POINT')
    a.data.foreach_set('vector', pts.astype(np.float32).ravel())
    tree = build_roof_group(p)
    obj, modifier = gt.add_geometry_object('slate roof', tree, base_mesh=mesh)
    info = gt.photograph_geometry(obj, out_folder, size=size, normal_reference=None, ambient_occlusion=ambient_occlusion, occlusion_distance=0.03,
                                  colour_samples=16 if ambient_occlusion else 4, quiet=quiet)
    info['total_seconds'] = round(time.time() - started, 1)
    info['slates_and_copies'] = int(len(pts))
    json.dump(info, open(os.path.join(out_folder, 'photo.json'), 'w'), indent=1)
    return info


if __name__ == '__main__':
    arguments = sys.argv[sys.argv.index('--') + 1:]
    option = lambda name, default=None: arguments[arguments.index(name) + 1] if name in arguments else default
    run(json.load(open(arguments[0])), arguments[1], size=int(option('--size', 1254)), ambient_occlusion=float(option('--ao', 0.8)))
