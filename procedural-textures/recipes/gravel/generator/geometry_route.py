# What this does (plain words): the REAL-GEOMETRY ROUTE for gravel, kept next to the flat painter to compare them honestly. It reads the same gravel description,
# takes the stone list the painter would use (positions, sizes, turns, colours; made by gravel_layers.make_stone_list), and builds the stones as REAL 3D blocks
# with a Blender Geometry Nodes group: one point per stone -> "Instance on Points" puts a faceted block (a short 4-, 5- or 6-sided column whose top is
# shrunk, i.e. a chunky pebble with a flat-ish top) on every point, turned, squashed and sized from the point's own numbers -> "Realize Instances" ->
# "Set Material". An overhead camera then photographs height (true height of the blocks), colour (one flat colour per block), and the normal.
# Then (plain numpy) a HYBRID height is made: half true geometry height, half the height derived from the painter's colour picture (the research found that
# this 50/50 mix helps gravel), and a normal map from it. Everything is written into the output folder for scoring.
# Use (inside Blender): blender -b --disable-autoexec -t 2 --python geometry_route.py -- DESCRIPTION.json PAINTER_FOLDER OUT_FOLDER [--size 1254]
#   PAINTER_FOLDER = a folder baked by gravel_generator.py from the same description (its colour.png and height.png are used for the hybrid).
import json
import math
import os
import sys
import time

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(PROC, 'lib'))
sys.path.insert(0, os.path.join(PROC, 'lib', 'contrib'))
sys.path.insert(0, HERE)
import bake_harness as bh  # noqa: E402
import gn_tools as gt  # noqa: E402
import gravel_layers as layers  # noqa: E402


def srgb_to_linear(v):
    v = np.asarray(v, np.float64)
    return np.where(v <= 0.04045, v / 12.92, ((v + 0.055) / 1.055) ** 2.4)


def points_mesh(description, tile):
    """One Blender point (a vertex) per stone, with the stone's numbers stored on it. Stones near the tile edge are added again one tile over so the tile wraps."""
    block = description['stones']
    rng = np.random.default_rng(block.get('seed', 1))
    stones = layers.make_stone_list(block, tile, rng)
    rust_tones = block.get('rust_tones', [[96, 63, 42], [118, 81, 54]])
    verts, radius, aspect, angle, variant, colour = [], [], [], [], [], []
    for s in stones:
        rgb = np.asarray(rust_tones[int(rng.integers(len(rust_tones)))] if s['rusty'] else block['tones'][s['tone']], np.float64)
        for ox in (-1, 0, 1):
            for oy in (-1, 0, 1):
                x, y, r = s['x'] + ox * tile, s['y'] + oy * tile, s['radius']
                if x + r < 0 or x - r > tile or y + r < 0 or y - r > tile:
                    continue
                verts.append((x / tile, 1.0 - y / tile, 0.0))
                radius.append(r / tile)
                aspect.append(s['aspect'])
                angle.append(-s['angle'])                       # the picture's y points down, the tile's v points up
                variant.append(int(s['sides']) % 3)
                colour.append(srgb_to_linear(rgb / 255.0))
    mesh = bpy.data.meshes.new('stone points')
    mesh.from_pydata(verts, [], [])
    for name, kind, values in (('stone_radius', 'FLOAT', radius), ('stone_aspect', 'FLOAT', aspect), ('stone_angle', 'FLOAT', angle), ('stone_variant', 'INT', variant)):
        attribute = mesh.attributes.new(name, kind, 'POINT')
        attribute.data.foreach_set('value', np.asarray(values, np.float32 if kind == 'FLOAT' else np.int32))
    col = np.ones((len(verts), 4), np.float32)
    col[:, :3] = np.asarray(colour, np.float32)
    attribute = mesh.attributes.new('piece_colour', 'FLOAT_COLOR', 'POINT')
    attribute.data.foreach_set('color', col.ravel())
    return mesh, len(stones), len(verts)


def build_group(height_ratio, top_shrink):
    """The Geometry Nodes group: points in -> stones out. Settings: height_ratio = stone height / stone radius; top_shrink = how much the flat top is smaller than the base."""
    tree, g = gt.make_geometry_group('gravel stones from points', [('Geometry', 'NodeSocketGeometry', None)])
    blocks = []
    for index, sides in enumerate((4, 5, 6)):
        g.node('GeometryNodeMeshCylinder', f'column{sides}', {'Vertices': sides, 'Radius': 1.0, 'Depth': 1.0})
        # shrink the top face: select the faces whose normal points up and scale them in toward their middle
        g.node('GeometryNodeInputNormal', f'normal{sides}')
        g.node('ShaderNodeVectorMath', f'up{sides}', {0: (f'normal{sides}', 'Normal'), 1: (0.0, 0.0, 1.0)}, operation='DOT_PRODUCT')
        g.node('ShaderNodeMath', f'is_top{sides}', {0: (f'up{sides}', 'Value'), 1: 0.5}, operation='GREATER_THAN')
        g.node('GeometryNodeScaleElements', f'shrink{sides}', {'Geometry': (f'column{sides}', 'Mesh'), 'Selection': (f'is_top{sides}', 'Value'), 'Scale': top_shrink}, domain='FACE')
        g.node('GeometryNodeTransform', f'lift{sides}', {'Geometry': (f'shrink{sides}', 'Geometry'), 'Translation': (0.0, 0.0, 0.5)})     # sit on the ground plane
        g.node('GeometryNodeGeometryToInstance', f'inst{sides}', {'Geometry': (f'lift{sides}', 'Geometry')})
        blocks.append(f'inst{sides}')
    g.node('GeometryNodeJoinGeometry', 'variants')
    for name in blocks:
        g.link(name, 'Instances', 'variants', 'Geometry')
    for key, kind in (('stone_radius', 'FLOAT'), ('stone_aspect', 'FLOAT'), ('stone_angle', 'FLOAT'), ('stone_variant', 'INT')):
        g.add('GeometryNodeInputNamedAttribute', key, data_type=kind)
        g.nodes[key].inputs['Name'].default_value = key
    g.node('ShaderNodeCombineXYZ', 'scale', {'X': ('stone_radius', 'Attribute'), 'Y': ('stone_aspect', 'Attribute'), 'Z': ('stone_radius', 'Attribute')})
    g.node('ShaderNodeMath', 'scale_y', {0: ('stone_radius', 'Attribute'), 1: ('stone_aspect', 'Attribute')}, operation='MULTIPLY')
    g.node('ShaderNodeMath', 'scale_z', {0: ('stone_radius', 'Attribute'), 1: height_ratio}, operation='MULTIPLY')
    g.link('scale_y', 0, 'scale', 'Y')
    g.link('scale_z', 0, 'scale', 'Z')
    g.node('ShaderNodeCombineXYZ', 'turn', {'Z': ('stone_angle', 'Attribute')})
    g.node('GeometryNodeInstanceOnPoints', 'instance', {'Points': ('in', 'Geometry'), 'Instance': ('variants', 'Geometry'), 'Pick Instance': True,
                                                           'Instance Index': ('stone_variant', 'Attribute'), 'Rotation': ('turn', 'Vector'), 'Scale': ('scale', 'Vector')})
    g.node('GeometryNodeRealizeInstances', 'realize', {'Geometry': ('instance', 'Instances')})
    gt.finish_with_material_slot(g, 'realize', 'Geometry')
    return tree


def main():
    arguments = sys.argv[sys.argv.index('--') + 1:]
    description = json.load(open(arguments[0]))
    painter_folder, out_folder = arguments[1], arguments[2]
    size = int(arguments[arguments.index('--size') + 1]) if '--size' in arguments else 1254
    tile = float(description['tile'])
    os.makedirs(out_folder, exist_ok=True)
    timings = {}
    started = time.time()
    scene = gt.new_scene(size)
    mesh, n_stones, n_points = points_mesh(description, tile)
    tree = build_group(height_ratio=0.5, top_shrink=0.75)
    obj, modifier = gt.add_geometry_object('stones', tree, base_mesh=mesh)
    timings['build_s'] = round(time.time() - started, 2)
    timings['stones'] = n_stones
    timings['points_with_wrap_copies'] = n_points
    # the ground plane: a flat square under the stones so the camera sees "soil" at height zero (its colour is the soil ground colour)
    ground = bpy.data.meshes.new('ground')
    ground.from_pydata([(0, 0, -0.001), (1, 0, -0.001), (1, 1, -0.001), (0, 1, -0.001)], [], [(0, 1, 2, 3)])
    ground_colour = np.ones((1, 4), np.float32)
    ground_colour[0, :3] = srgb_to_linear(np.asarray(description.get('ground', [79, 52, 34])) / 255.0)
    attribute = ground.attributes.new('piece_colour', 'FLOAT_COLOR', 'FACE')
    attribute.data.foreach_set('color', ground_colour.ravel())
    ground_object = bpy.data.objects.new('ground', ground)
    scene.collection.objects.link(ground_object)
    info = gt.photograph_geometry([obj, ground_object], out_folder, size=size, normal_reference='gravel', colour_samples=8, with_geometry_normal=False, z_low=-0.001)
    timings.update({k: v for k, v in info.items() if k.endswith('_s')})
    # hybrid height: half true geometry, half derived from the painter's colour (numpy)
    painter_height = bh.load_png_as_array(os.path.join(painter_folder, 'height.png'))[..., 0]
    geometry_height = bh.load_png_as_array(os.path.join(out_folder, 'height.png'))[..., 0]
    g = (geometry_height - geometry_height.mean()) / (geometry_height.std() + 1e-9) * painter_height.std() + painter_height.mean()
    hybrid = np.clip(0.5 * painter_height + 0.5 * g, 0, 1)
    bh.save_array_png(np.stack([hybrid] * 3, axis=-1), os.path.join(out_folder, 'height_hybrid.png'), True)
    strength = 10.0
    h8 = np.round(hybrid * 255.0)
    hx = (np.roll(h8, -1, axis=1) - np.roll(h8, 1, axis=1)) / 2.0
    hy = (np.roll(h8, -1, axis=0) - np.roll(h8, 1, axis=0)) / 2.0
    nx, ny, nz = -strength * hx / 255.0, strength * hy / 255.0, np.ones_like(h8)
    length = np.sqrt(nx * nx + ny * ny + nz * nz)
    bh.save_array_png(np.stack([nx / length, ny / length, nz / length], axis=-1) * 0.5 + 0.5, os.path.join(out_folder, 'normal_hybrid.png'))
    json.dump(timings, open(os.path.join(out_folder, 'geometry_route.json'), 'w'), indent=1)
    print('[geometry route]', json.dumps(timings))


if __name__ == '__main__':
    main()
