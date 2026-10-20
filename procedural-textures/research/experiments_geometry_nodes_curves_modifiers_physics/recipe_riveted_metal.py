# What this does: RECIPE 5 - riveted steel plates with straps, diagonal braces and domed rivets, built from real geometry with Geometry Nodes, then photographed
# from straight above (height, colour, normal pictures of a 1 x 1 seamless tile).
# Chain:
#   plate: a dense Grid (0..1) with fine tileable noise (rust pits)
#   straps: Cube nodes (one per strap, scaled, tilted for the diagonal braces) -> Join -> Mesh Bevel (sharp edges) -> Set Position with noise
#       two vertical straps and one horizontal strap run the whole tile (so they wrap by themselves), the braces sit inside their panels
#   rivets: for every strap a Curve Line along its centre -> Resample Curve (Count) -> Instance on Points (an 8-sided Cone dome) ->
#       the points at both ends of a full-length strap are the SAME place on the donut, so a rivet on the seam appears as two halves that meet when tiled
#   colour: steel (blue-grey ramp) + rust patches (tileable noise, hard edge) + dark crevices from the Ambient Occlusion node in the colour picture
# Run:  blender -b --disable-autoexec -t 2 --python recipe_riveted_metal.py -- OUT_FOLDER [--size 1254] [--ao 0.8]
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
DEFAULTS = dict(strap_width=0.10, strap_height=0.012, plate_z=0.0, rivet_radius=0.021, rivet_height=0.016, rivet_count=8, seed=1, grid=320)
# (name, centre x, centre y, length in x, length in y, angle in degrees); the first three are full-length straps (they wrap)
STRAPS = [
    ('vertical a', 0.06, 0.5, 0.10, 1.0, 0.0),
    ('vertical b', 0.58, 0.5, 0.10, 1.0, 0.0),
    ('horizontal', 0.5, 0.55, 1.0, 0.075, 0.0),
    ('brace a', 0.325, 0.785, 0.56, 0.075, -43.5),
    ('brace b', 0.82, 0.275, 0.60, 0.075, -51.3),
]


def build_metal_group(p):
    tree, g = gt.make_geometry_group('Riveted metal', [('Geometry', 'NodeSocketGeometry', None)])
    noise = gt.tileable_noise_geo_group()
    # ---------------------------------------------------------------- the plate
    g.node('GeometryNodeMeshGrid', 'plate grid', {'Size X': 1.0, 'Size Y': 1.0, 'Vertices X': p['grid'], 'Vertices Y': p['grid']})
    g.node('GeometryNodeTransform', 'plate move', {'Geometry': ('plate grid', 'Mesh'), 'Translation': (0.5, 0.5, p['plate_z'])})
    # ---------------------------------------------------------------- straps and braces
    pieces = []
    for number, (name, cx, cy, lx, ly, angle) in enumerate(STRAPS):
        tag = f'strap{number}'
        resolution_x, resolution_y = max(2, int(lx / 0.012) + 1), max(2, int(ly / 0.012) + 1)
        g.node('GeometryNodeMeshCube', f'{tag} cube', {'Size': (lx, ly, p['strap_height']), 'Vertices X': min(resolution_x, 120), 'Vertices Y': min(resolution_y, 120), 'Vertices Z': 2})
        g.node('GeometryNodeTransform', f'{tag} place', {'Geometry': (f'{tag} cube', 'Mesh'), 'Translation': (cx, cy, p['plate_z'] + p['strap_height'] / 2 - 0.002),
                                                         'Rotation': (0.0, 0.0, math.radians(angle))})
        pieces.append(f'{tag} place')
    g.node('GeometryNodeJoinGeometry', 'straps join', {})
    for name_ in pieces:
        g.link(name_, 'Geometry', 'straps join', 'Geometry')
    g.node('GeometryNodeInputMeshEdgeAngle', 'edge angle')
    g.node('FunctionNodeCompare', 'sharp', {'A': ('edge angle', 'Unsigned Angle'), 'B': 0.6}, data_type='FLOAT', operation='GREATER_THAN')
    g.node('GeometryNodeMeshBevel', 'strap bevel', {'Mesh': ('straps join', 'Geometry'), 'Selection': ('sharp', 'Result'), 'Start Left Offset': 0.0025, 'Start Right Offset': 0.0025,
                                                      'End Left Offset': 0.0025, 'End Right Offset': 0.0025, 'Segments': 2})
    # ---------------------------------------------------------------- rivets: curve -> resample -> instance on points
    rivet_sources = []
    for number, (name, cx, cy, lx, ly, angle) in enumerate(STRAPS):
        tag = f'rivets{number}'
        long_x = lx >= ly
        full = (lx >= 0.99 and long_x) or (ly >= 0.99 and not long_x)
        count = p['rivet_count'] + 1 if full else 4
        length = (lx if long_x else ly) * (1.0 if full else 0.8)
        half = length / 2
        a = math.radians(angle) if long_x else math.radians(angle) + math.pi / 2
        start = (cx - half * math.cos(a), cy - half * math.sin(a), 0.0)
        end = (cx + half * math.cos(a), cy + half * math.sin(a), 0.0)
        g.node('GeometryNodeCurvePrimitiveLine', f'{tag} line', {'Start': start, 'End': end}, mode='POINTS')
        g.node('GeometryNodeResampleCurve', f'{tag} resample', {'Curve': (f'{tag} line', 'Curve'), 'Mode': 'Count', 'Count': count})
        rivet_sources.append(f'{tag} resample')
    g.node('GeometryNodeJoinGeometry', 'rivet curves', {})
    for name_ in rivet_sources:
        g.link(name_, 'Curve', 'rivet curves', 'Geometry')
    g.node('GeometryNodeCurveToPoints', 'rivet points', {'Curve': ('rivet curves', 'Geometry')}, mode='EVALUATED')
    g.node('GeometryNodeMeshCone', 'dome', {'Vertices': 8, 'Radius Top': 0.004, 'Radius Bottom': p['rivet_radius'], 'Depth': p['rivet_height']})
    g.node('GeometryNodeTransform', 'dome up', {'Geometry': ('dome', 'Mesh'), 'Translation': (0.0, 0.0, p['rivet_height'] / 2)})
    g.node('GeometryNodeInstanceOnPoints', 'rivets', {'Points': ('rivet points', 'Points'), 'Instance': ('dome up', 'Geometry')})
    g.node('GeometryNodeRealizeInstances', 'rivets real', {'Geometry': ('rivets', 'Instances')})
    g.node('GeometryNodeTransform', 'rivets raised', {'Geometry': ('rivets real', 'Geometry'), 'Translation': (0.0, 0.0, p['plate_z'] + p['strap_height'] - 0.002)})
    # ---------------------------------------------------------------- weathering: tileable noise displaces plate + straps (rust pits and dents)
    g.node('GeometryNodeInputPosition', 'position')
    g.group('pit noise', noise, {'Position': ('position', 'Position'), 'Scale': 90.0, 'Detail': 4.0, 'Roughness': 0.6, 'Seed': 3.0})
    g.group('dent noise', noise, {'Position': ('position', 'Position'), 'Scale': 7.0, 'Detail': 3.0, 'Roughness': 0.5, 'Seed': 11.0})
    g.node('ShaderNodeMapRange', 'pit centred', {'Value': ('pit noise', 'Fac'), 'From Min': 0.3, 'From Max': 0.7, 'To Min': -1.0, 'To Max': 1.0})
    g.node('ShaderNodeMapRange', 'dent centred', {'Value': ('dent noise', 'Fac'), 'From Min': 0.3, 'From Max': 0.7, 'To Min': -1.0, 'To Max': 1.0})
    g.math('pit z', 'MULTIPLY', ('pit centred', 'Result'), 0.0012)
    g.math('dent z', 'MULTIPLY', ('dent centred', 'Result'), 0.0018)
    g.math('weather z', 'ADD', ('pit z', 0), ('dent z', 0))
    g.node('ShaderNodeCombineXYZ', 'weather offset', {'Z': ('weather z', 0)})
    g.node('GeometryNodeJoinGeometry', 'metal join', {})
    g.link('plate move', 'Geometry', 'metal join', 'Geometry')
    g.link('strap bevel', 'Mesh', 'metal join', 'Geometry')
    g.link('rivets raised', 'Geometry', 'metal join', 'Geometry')
    g.node('GeometryNodeSubdivideMesh', 'extra detail', {'Mesh': ('metal join', 'Geometry'), 'Level': 1})
    g.node('GeometryNodeSetPosition', 'weathered', {'Geometry': ('extra detail', 'Mesh'), 'Offset': ('weather offset', 'Vector')})
    g.node('GeometryNodeSetShadeSmooth', 'smooth', {'Mesh': ('weathered', 'Geometry'), 'Shade Smooth': True})
    # ---------------------------------------------------------------- colour: steel + rust
    g.node('GeometryNodeInputPosition', 'position c')
    g.group('rust big', noise, {'Position': ('position c', 'Position'), 'Scale': 6.0, 'Detail': 5.0, 'Roughness': 0.65, 'Seed': 21.0})
    g.group('rust small', noise, {'Position': ('position c', 'Position'), 'Scale': 22.0, 'Detail': 5.0, 'Roughness': 0.6, 'Seed': 29.0})
    g.math('rust mix', 'MULTIPLY', ('rust small', 'Fac'), 0.4)
    g.math('rust value', 'MULTIPLY', ('rust big', 'Fac'), 0.6)
    g.math('rust sum', 'ADD', ('rust mix', 0), ('rust value', 0))
    g.node('ShaderNodeMapRange', 'rust edge', {'Value': ('rust sum', 0), 'From Min': 0.50, 'From Max': 0.56, 'To Min': 0.0, 'To Max': 1.0})
    g.group('steel noise', noise, {'Position': ('position c', 'Position'), 'Scale': 35.0, 'Detail': 4.0, 'Roughness': 0.6, 'Seed': 41.0})
    make_ramp(g, 'steel', [(0.2, (31, 32, 34)), (0.5, (52, 54, 56)), (0.8, (84, 88, 88))], {'Fac': ('steel noise', 'Fac')})
    make_ramp(g, 'rust colour', [(0.2, (74, 38, 26)), (0.55, (112, 62, 34)), (0.9, (150, 90, 48))], {'Fac': ('rust small', 'Fac')})
    g.node('ShaderNodeMix', 'steel or rust', {'Factor': ('rust edge', 'Result'), 'A': ('steel', 'Color'), 'B': ('rust colour', 'Color')}, data_type='RGBA')
    g.node('GeometryNodeStoreNamedAttribute', 'colour', {'Geometry': ('smooth', 'Mesh'), 'Name': 'piece_colour', 'Value': ('steel or rust', 'Result')}, data_type='FLOAT_COLOR', domain='POINT')
    gt.finish_with_material_slot(g, 'colour')
    return tree


def run(out_folder, size=1254, params=None, ambient_occlusion=0.8, quiet=False):
    p = {**DEFAULTS, **(params or {})}
    started = time.time()
    gt.new_scene(size)
    tree = build_metal_group(p)
    obj, modifier = gt.add_geometry_object('riveted metal', tree)
    info = gt.photograph_geometry(obj, out_folder, size=size, normal_reference='metal', ambient_occlusion=ambient_occlusion, occlusion_distance=0.025,
                                  colour_samples=16 if ambient_occlusion else 4, edge_wear=0.55, edge_colour=srgb(120, 114, 106), quiet=quiet)
    info['total_seconds'] = round(time.time() - started, 1)
    info['parameters'] = p
    with open(os.path.join(out_folder, 'photo.json'), 'w') as handle:
        json.dump(info, handle, indent=1)
    return info


if __name__ == '__main__':
    arguments = sys.argv[sys.argv.index('--') + 1:]
    option = lambda name, default=None: arguments[arguments.index(name) + 1] if name in arguments else default
    run(arguments[0], size=int(option('--size', 1254)), params={'grid': int(option('--grid', DEFAULTS['grid']))}, ambient_occlusion=float(option('--ao', 0.8)))
