# What this does: makes the NEW "what does this setting do?" pictures for "06 Guide - geometry nodes, curves, modifiers and physics.md",
# for the geometry tools that had no strip yet. Everything is real Blender 5.2 geometry, photographed from straight above by the
# project's overhead camera (lib/bake_harness.py), 256 x 256 dots per square. Four strips:
#   1. relax_steps     : 220 points that each need room of radius 0.032. Poisson Disk, then plain random points relaxed 0, 5, 15, 40 times
#                        in a Repeat zone (lib/contrib/relax_tools.py). Discs are drawn round every point; a RED disc has a neighbour closer
#                        than 0.9 x the room two discs need (measured the wrap-around way). The picture is slid by half a tile, so the
#                        tile's own edge (the seam) is the thin blue cross in the middle.
#   2. groove_width    : three wavy curves (Curve Line -> Resample Curve -> Set Position) -> Curve to Mesh with no profile (plain edges)
#                        -> 9 wrap copies -> Geometry Proximity (Edges) from every vertex of a 257 x 257 Grid -> Map Range = a V-shaped groove.
#                        The setting is the groove's half-width in tile units. Height picture (white = high).
#   3. ridge_radius    : the same curves -> Curve to Mesh WITH a Curve Circle profile (8 sides) = a raised ridge; the setting is the circle's
#                        radius. The first square has no profile: plain edges, which have no surface for the camera to see.
#   4. set_material    : the same ridges, coloured, photographed twice: material put on the object's own slot (no Set Material node),
#                        and Set Material as the last node of the group. Shows the "black picture" trap.
# Numbers (distances, shares, times, mean brightness) go to numbers_geometry.json next to this file. The squares go to work/<strip>/.
# Run: blender -b --disable-autoexec -t 2 --python make_geometry_strips.py
import json
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(PROC, 'lib'))
sys.path.insert(0, os.path.join(PROC, 'lib', 'contrib'))

import bpy  # noqa: E402
import numpy as np  # noqa: E402

import bake_harness as bh  # noqa: E402
import gn_tools as gt  # noqa: E402
import relax_tools as rx  # noqa: E402

SIZE = 256
WORK = os.path.join(HERE, 'work')
NUMBERS = {}


def write_sweep(folder, files, labels):
    with open(os.path.join(folder, 'sweep.json'), 'w') as handle:
        json.dump({'files': files, 'labels': labels}, handle, indent=1)


def flat_colour_material(name='show face colour'):
    """Emission of the face colour attribute 'col' (no lighting at all), for meshes built straight from Python."""
    material = bpy.data.materials.new(name)
    tree = material.node_tree
    tree.nodes.clear()
    attribute = tree.nodes.new('ShaderNodeAttribute')
    attribute.attribute_name = 'col'
    emit = tree.nodes.new('ShaderNodeEmission')
    out = tree.nodes.new('ShaderNodeOutputMaterial')
    tree.links.new(attribute.outputs['Color'], emit.inputs['Color'])
    tree.links.new(emit.outputs['Emission'], out.inputs['Surface'])
    return material


def linear(rgb):
    return tuple(((c / 255.0) / 12.92 if c / 255.0 <= 0.04045 else ((c / 255.0 + 0.055) / 1.055) ** 2.4) for c in rgb)


# ----------------------------------------------------------------------------------------------------- 1. relaxation steps
RADIUS = 0.032          # room each point needs (the same numbers as research t06_relax_repeat_zone.py)
COUNT = 220


def point_source(g, poisson):
    g.node('GeometryNodeMeshGrid', 'grid', {'Size X': 1.0, 'Size Y': 1.0, 'Vertices X': 2, 'Vertices Y': 2})
    g.node('GeometryNodeTransform', 'grid move', {'Geometry': ('grid', 'Mesh'), 'Translation': (0.5, 0.5, 0.0)})
    if poisson:
        g.node('GeometryNodeDistributePointsOnFaces', 'points', {'Mesh': ('grid move', 'Geometry'), 'Distance Min': 2 * RADIUS, 'Density Max': 4000.0,
                                                                 'Density Factor': 1.0, 'Seed': 3}, distribute_method='POISSON')
    else:
        g.node('GeometryNodeDistributePointsOnFaces', 'points', {'Mesh': ('grid move', 'Geometry'), 'Density': float(COUNT), 'Seed': 3},
               distribute_method='RANDOM')
    g.node('GeometryNodeStoreNamedAttribute', 'room', {'Geometry': ('points', 'Points'), 'Name': 'radius', 'Value': RADIUS}, data_type='FLOAT', domain='POINT')
    return 'room', 'Geometry'


def relaxed_points(poisson, iterations):
    tree, g = gt.make_geometry_group(f'relax test {poisson} {iterations}', [('Geometry', 'NodeSocketGeometry', None)])
    node, socket = point_source(g, poisson)
    if not poisson:
        g.group('relax', rx.relax_group_with_radius(), {'Points': (node, socket), 'Iterations': iterations, 'Tightness': 1.0})
        node, socket = 'relax', 'Points'
    g.node('GeometryNodePointsToVertices', 'to vertices', {'Points': (node, socket)})
    g.link('to vertices', 'Mesh', 'out', 'Geometry')
    obj, _ = gt.add_geometry_object(f'relax object {poisson} {iterations}', tree)
    started = time.time()
    points = gt.evaluated_vertices(obj)[:, :2].astype(np.float64)
    seconds = time.time() - started
    bpy.data.objects.remove(obj)
    return points, seconds


def wrap_stats(points):
    delta = np.abs(points[:, None, :] - points[None, :, :])
    delta = np.minimum(delta, 1.0 - delta)
    distance = np.sqrt((delta ** 2).sum(-1))
    np.fill_diagonal(distance, 9.0)
    nearest = distance.min(axis=1)
    return nearest, {'points': int(len(points)), 'smallest_wrap_distance': round(float(distance.min()), 4),
                     'share_with_a_neighbour_closer_than_0.9_x_2r': round(float((nearest < 0.9 * 2 * RADIUS).mean()), 3)}


def disc_mesh(points, crowded):
    """One flat mesh: a 24-sided disc (radius RADIUS) round every point and its wrap copies, slid by half a tile; grey or red; plus a blue seam cross."""
    vertices, faces, colours = [], [], []
    grey, red, blue, ground = linear((200, 200, 196)), linear((215, 40, 30)), linear((40, 90, 230)), linear((28, 28, 30))

    def add_polygon(corners, colour, z):
        start = len(vertices)
        vertices.extend((x, y, z) for x, y in corners)
        faces.append(tuple(range(start, start + len(corners))))
        colours.append(colour)

    add_polygon([(0, 0), (1, 0), (1, 1), (0, 1)], ground, 0.0)
    angles = np.linspace(0, 2 * math.pi, 24, endpoint=False)
    order = np.argsort(crowded)          # red discs last, so they lie on top
    for index in order:
        x0, y0 = (points[index] + 0.5) % 1.0
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                x, y = x0 + dx, y0 + dy
                if -RADIUS <= x <= 1 + RADIUS and -RADIUS <= y <= 1 + RADIUS:
                    corners = [(x + RADIUS * math.cos(a), y + RADIUS * math.sin(a)) for a in angles]
                    add_polygon(corners, red if crowded[index] else grey, 0.001 + 0.001 * bool(crowded[index]))
    line = 1.5 / SIZE
    add_polygon([(0.5 - line, 0), (0.5 + line, 0), (0.5 + line, 1), (0.5 - line, 1)], blue, 0.01)
    add_polygon([(0, 0.5 - line), (1, 0.5 - line), (1, 0.5 + line), (0, 0.5 + line)], blue, 0.01)
    mesh = bpy.data.meshes.new('discs')
    mesh.from_pydata(vertices, [], faces)
    attribute = mesh.attributes.new('col', 'FLOAT_COLOR', 'FACE')
    attribute.data.foreach_set('color', np.array([c + (1.0,) for c in colours], dtype=np.float32).ravel())
    obj = bpy.data.objects.new('discs', mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(flat_colour_material())
    return obj


def strip_relax():
    folder = os.path.join(WORK, 'relax_steps')
    os.makedirs(folder, exist_ok=True)
    scene = gt.new_scene(SIZE)
    cases = [('Poisson Disk', True, 0), ('random, relax 0', False, 0), ('relax 5 steps', False, 5), ('relax 15 steps', False, 15), ('relax 40 steps', False, 40)]
    files, labels, numbers = [], [], {}
    for index, (label, poisson, iterations) in enumerate(cases):
        points, seconds = relaxed_points(poisson, iterations)
        nearest, stats = wrap_stats(points)
        stats['evaluate_seconds'] = round(seconds, 3)
        crowded = nearest < 0.9 * 2 * RADIUS
        obj = disc_mesh(points, crowded)
        path = os.path.join(folder, f'tile_{index:02d}.png')
        bh.render_to(scene, path, False)
        bpy.data.objects.remove(obj)
        files.append(os.path.basename(path))
        labels.append(f'{label}: {int(crowded.sum())} red')
        numbers[label] = stats
    write_sweep(folder, files, labels)
    NUMBERS['relax_steps'] = {'radius': RADIUS, 'asked_points': COUNT, 'tightness': 1.0, 'seed': 3, 'cases': numbers}


# ----------------------------------------------------------------------------------------------------- curves shared by strips 2-4
TRACKS = [  # y0, slope (whole number so the curve closes on the tile), wave height, whole number of waves, phase
    (0.22, 0.0, 0.035, 2, 0.0),
    (0.55, 1.0, 0.030, 1, 1.3),
    (0.10, -1.0, 0.045, 3, 2.1),
]


def add_tracks(g):
    """Three closed wavy curves on the tile, each made of real curve nodes. Returns the node names of the curves."""
    names = []
    for k, (y0, slope, height, waves, phase) in enumerate(TRACKS):
        tag = f'track {k}'
        g.node('GeometryNodeCurvePrimitiveLine', f'{tag} line', {'Start': (0.0, y0, 0.0), 'End': (1.0, y0, 0.0)}, mode='POINTS')
        g.node('GeometryNodeResampleCurve', f'{tag} resample', {'Curve': (f'{tag} line', 'Curve'), 'Mode': 'Count', 'Count': 240})
        g.node('GeometryNodeInputPosition', f'{tag} pos')
        g.node('ShaderNodeSeparateXYZ', f'{tag} xyz', {'Vector': (f'{tag} pos', 'Position')})
        g.math(f'{tag} turns', 'MULTIPLY', (f'{tag} xyz', 'X'), 2 * math.pi * waves)
        g.math(f'{tag} turns+', 'ADD', (f'{tag} turns', 0), phase)
        g.math(f'{tag} sine', 'SINE', (f'{tag} turns+', 0))
        g.math(f'{tag} wave', 'MULTIPLY', (f'{tag} sine', 0), height)
        g.math(f'{tag} tilt', 'MULTIPLY', (f'{tag} xyz', 'X'), slope)
        g.math(f'{tag} dy', 'ADD', (f'{tag} wave', 0), (f'{tag} tilt', 0))
        g.node('ShaderNodeCombineXYZ', f'{tag} offset', {'Y': (f'{tag} dy', 0)})
        g.node('GeometryNodeSetPosition', f'{tag} placed', {'Geometry': (f'{tag} resample', 'Curve'), 'Offset': (f'{tag} offset', 'Vector')})
        names.append(f'{tag} placed')
    return names


def nine_copies(g, tag, source):
    """Join 9 copies of source shifted by -1, 0, +1 tile in x and y (the wrap copies)."""
    g.node('GeometryNodeJoinGeometry', f'{tag} all', {})
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            name = f'{tag} copy {dx} {dy}'
            g.node('GeometryNodeTransform', name, {'Geometry': source, 'Translation': (float(dx), float(dy), 0.0)})
            g.link(name, 'Geometry', f'{tag} all', 'Geometry')
    return f'{tag} all', 'Geometry'


def ground_grid(g, vertices=257):
    g.node('GeometryNodeMeshGrid', 'ground', {'Size X': 1.0, 'Size Y': 1.0, 'Vertices X': vertices, 'Vertices Y': vertices})
    g.node('GeometryNodeTransform', 'ground move', {'Geometry': ('ground', 'Mesh'), 'Translation': (0.5, 0.5, 0.0)})
    return 'ground move', 'Geometry'


# ----------------------------------------------------------------------------------------------------- 2. groove width
def groove_object(half_width, depth=0.01):
    tree, g = gt.make_geometry_group(f'groove {half_width}', [('Geometry', 'NodeSocketGeometry', None)])
    tracks = add_tracks(g)
    g.node('GeometryNodeJoinGeometry', 'tracks', {})
    for name in tracks:
        g.node('GeometryNodeCurveToMesh', f'{name} edges', {'Curve': (name, 'Geometry')})
        g.link(f'{name} edges', 'Mesh', 'tracks', 'Geometry')
    copies = nine_copies(g, 'tracks', ('tracks', 'Geometry'))
    ground = ground_grid(g)
    g.node('GeometryNodeInputPosition', 'ground pos')
    g.node('GeometryNodeProximity', 'distance', {'Geometry': copies, 'Sample Position': ('ground pos', 'Position')}, target_element='EDGES')
    g.node('ShaderNodeMapRange', 'groove', {'Value': ('distance', 'Distance'), 'From Min': 0.0, 'From Max': half_width, 'To Min': -depth, 'To Max': 0.0}, clamp=True)
    g.node('ShaderNodeCombineXYZ', 'down', {'Z': ('groove', 'Result')})
    g.node('GeometryNodeSetPosition', 'dug', {'Geometry': ground, 'Offset': ('down', 'Vector')})
    gt.finish_with_material_slot(g, 'dug')
    return gt.add_geometry_object(f'groove object {half_width}', tree)[0]


def strip_groove():
    folder = os.path.join(WORK, 'groove_width')
    os.makedirs(folder, exist_ok=True)
    scene = gt.new_scene(SIZE)
    widths = [0.005, 0.01, 0.02, 0.04]
    files, labels, numbers = [], [], {}
    for index, width in enumerate(widths):
        started = time.time()
        obj = groove_object(width)
        low, high, count = gt.z_range(obj)
        path = os.path.join(folder, f'tile_{index:02d}.png')
        gt.render_with(scene, obj, gt.height_material(-0.01, 0.0), path, True)
        numbers[str(width)] = {'groove_half_width_tile_units': width, 'in_dots_of_a_1254_tile': round(width * 1254, 1), 'lowest_z': round(low, 5),
                               'vertices': count, 'seconds_build_and_render': round(time.time() - started, 2)}
        bpy.data.objects.remove(obj)
        files.append(os.path.basename(path))
        labels.append(f'half-width {width} (= {width * 1254:.0f} dots)')
    write_sweep(folder, files, labels)
    NUMBERS['groove_width'] = {'depth_tile_units': 0.01, 'grid_vertices': '257 x 257', 'cases': numbers}


# ----------------------------------------------------------------------------------------------------- 3. ridge radius and 4. Set Material
def ridge_object(radius, set_material=True, colour=None):
    tree, g = gt.make_geometry_group(f'ridge {radius} {set_material}', [('Geometry', 'NodeSocketGeometry', None)])
    tracks = add_tracks(g)
    g.node('GeometryNodeJoinGeometry', 'tracks', {})
    if radius > 0:
        g.node('GeometryNodeCurvePrimitiveCircle', 'profile', {'Resolution': 8, 'Radius': radius}, mode='RADIUS')
    for name in tracks:
        inputs = {'Curve': (name, 'Geometry')}
        if radius > 0:
            inputs['Profile Curve'] = ('profile', 'Curve')
        g.node('GeometryNodeCurveToMesh', f'{name} swept', inputs)
        g.link(f'{name} swept', 'Mesh', 'tracks', 'Geometry')
    copies = nine_copies(g, 'tracks', ('tracks', 'Geometry'))
    g.node('GeometryNodeMeshGrid', 'floor', {'Size X': 1.0, 'Size Y': 1.0, 'Vertices X': 2, 'Vertices Y': 2})
    g.node('GeometryNodeTransform', 'floor move', {'Geometry': ('floor', 'Mesh'), 'Translation': (0.5, 0.5, 0.0)})
    g.node('GeometryNodeJoinGeometry', 'scene', {})
    g.link('floor move', 'Geometry', 'scene', 'Geometry')
    g.link(copies[0], copies[1], 'scene', 'Geometry')
    if colour is not None:
        g.node('GeometryNodeInputPosition', 'height pos')
        g.node('ShaderNodeSeparateXYZ', 'height xyz', {'Vector': ('height pos', 'Position')})
        g.node('ShaderNodeMapRange', 'height share', {'Value': ('height xyz', 'Z'), 'From Min': 0.0, 'From Max': 0.012}, clamp=True)
        g.node('ShaderNodeMix', 'paint', {'Factor': ('height share', 'Result'), 'A': colour[0] + (1.0,), 'B': colour[1] + (1.0,)}, data_type='RGBA')
        g.node('GeometryNodeStoreNamedAttribute', 'store colour', {'Geometry': ('scene', 'Geometry'), 'Name': 'piece_colour', 'Value': ('paint', 'Result')},
               data_type='FLOAT_COLOR', domain='POINT')
        last = 'store colour'
    else:
        last = 'scene'
    if set_material:
        gt.finish_with_material_slot(g, last)
    else:
        g.link(last, 'Geometry', 'out', 'Geometry')
    return gt.add_geometry_object(f'ridge object {radius} {set_material}', tree)[0]


def strip_ridge():
    folder = os.path.join(WORK, 'ridge_radius')
    os.makedirs(folder, exist_ok=True)
    scene = gt.new_scene(SIZE)
    radii = [0.0, 0.003, 0.006, 0.012, 0.024]
    files, labels, numbers = [], [], {}
    for index, radius in enumerate(radii):
        started = time.time()
        obj = ridge_object(radius)
        low, high, count = gt.z_range(obj)
        path = os.path.join(folder, f'tile_{index:02d}.png')
        gt.render_with(scene, obj, gt.height_material(0.0, 0.024), path, True)
        numbers[str(radius)] = {'profile_radius_tile_units': radius, 'highest_z': round(high, 5), 'vertices': count,
                                'seconds_build_and_render': round(time.time() - started, 2)}
        bpy.data.objects.remove(obj)
        files.append(os.path.basename(path))
        labels.append('no profile (edges only)' if radius == 0 else f'profile radius {radius}')
    write_sweep(folder, files, labels)
    NUMBERS['ridge_radius'] = {'profile': 'Curve Circle, Resolution 8', 'height_picture_range': [0.0, 0.024], 'cases': numbers}


def strip_set_material():
    folder = os.path.join(WORK, 'set_material')
    os.makedirs(folder, exist_ok=True)
    scene = gt.new_scene(SIZE)
    colours = (linear((120, 72, 44)), linear((235, 200, 150)))
    material = gt.colour_material('piece_colour')
    files, labels, numbers = [], [], {}
    for index, (label, use_node) in enumerate([('material on the object slot', False), ('Set Material node at the end', True)]):
        obj = ridge_object(0.008, set_material=use_node, colour=colours)
        path = os.path.join(folder, f'tile_{index:02d}.png')
        gt.render_with(scene, obj, material, path, False)
        evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
        slots = [m.name if m else None for m in evaluated.data.materials]
        picture = bh.load_png_as_array(path)
        numbers[label] = {'mean_brightness_0_to_1': round(float(picture[..., :3].mean()), 4), 'materials_on_the_evaluated_mesh': slots,
                          'materials_on_the_object_own_mesh': [m.name for m in obj.data.materials]}
        bpy.data.objects.remove(obj)
        files.append(os.path.basename(path))
        labels.append(label)
    write_sweep(folder, files, labels)
    NUMBERS['set_material'] = numbers


if __name__ == '__main__':
    started = time.time()
    for job in (strip_relax, strip_groove, strip_ridge, strip_set_material):
        job_started = time.time()
        job()
        NUMBERS.setdefault('seconds', {})[job.__name__] = round(time.time() - job_started, 1)
    NUMBERS['seconds']['total'] = round(time.time() - started, 1)
    NUMBERS['blender'] = bpy.app.version_string
    with open(os.path.join(HERE, 'numbers_geometry.json'), 'w') as handle:
        json.dump(NUMBERS, handle, indent=1)
    print(json.dumps(NUMBERS, indent=1))
