# What this does: tests "iterative relaxation" in Geometry Nodes 5.2 and compares four ways of spacing points on a 1 x 1 tile that must wrap:
#   A. plain random points                                     (the baseline: points land on top of each other)
#   B. Distribute Points on Faces, Poisson Disk, Distance Min  (spacing, but it knows nothing about the other side of the tile edge)
#   C. random points + a REPEAT ZONE that pushes overlapping points apart, measuring distances the wrap-around way (this file builds that group)
#   D. the same relaxation written with a SIMULATION ZONE, stepped one frame at a time (should equal C)
# Also tests the BAKE node: bake the relaxed points, then change the upstream setting and see the result stay frozen.
# The relaxation group: inside the zone, make 9 copies of the points (shifted by -1, 0, +1 in x and y), ask "Index of Nearest" for each point's nearest OTHER point,
# push the pair apart by half of the overlap, delete the copies, wrap the positions back into 0..1, repeat.
# Run: blender -b --disable-autoexec -t 2 --python t06_relax_repeat_zone.py
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy  # noqa: E402
import numpy as np  # noqa: E402
import gn_tools as gt  # noqa: E402

OUT = os.path.join(HERE, 'out', 't06_relax')
os.makedirs(OUT, exist_ok=True)
N_POINTS, RADIUS = 220, 0.032      # 220 points; each needs 2 * RADIUS = 0.064 of free room (a packing density of about 0.71 of the maximum)


def add_relax_step(g, source):
    """Adds the nodes of ONE relaxation step to writer g and returns (node, socket) of the relaxed points. source = (node, socket) of the points.
    The points are copied into the 8 neighbouring tiles (every copy remembers 'central = False'), each point finds its nearest OTHER point with
    Index of Nearest, overlapping pairs are pushed apart, the copies are deleted and the positions are wrapped back into 0..1."""
    g.node('GeometryNodeStoreNamedAttribute', 'mark central', {'Geometry': source, 'Name': 'central', 'Value': True}, data_type='BOOLEAN', domain='POINT')
    pieces = []
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            node = f'copy {dx} {dy}'
            g.node('GeometryNodeTransform', node, {'Geometry': ('mark central', 'Geometry'), 'Translation': (float(dx), float(dy), 0.0)})
            if (dx, dy) != (0, 0):
                g.node('GeometryNodeStoreNamedAttribute', node + ' ghost', {'Geometry': (node, 'Geometry'), 'Name': 'central', 'Value': False}, data_type='BOOLEAN', domain='POINT')
                pieces.append(node + ' ghost')
            else:
                pieces.append(node)
    g.node('GeometryNodeJoinGeometry', 'all copies', {})
    for node in pieces:
        g.link(node, 'Geometry', 'all copies', 'Geometry')
    g.node('GeometryNodeInputPosition', 'pos')
    g.node('GeometryNodeIndexOfNearest', 'nearest', {'Position': ('pos', 'Position')})
    g.node('GeometryNodeSampleIndex', 'neighbour pos', {'Geometry': ('all copies', 'Geometry'), 'Value': ('pos', 'Position'), 'Index': ('nearest', 'Index')}, domain='POINT', data_type='FLOAT_VECTOR')
    g.vmath('away', 'SUBTRACT', ('pos', 'Position'), ('neighbour pos', 'Value'))
    g.vmath('gap', 'LENGTH', ('away', 0))
    g.vmath('direction', 'NORMALIZE', ('away', 0))
    g.math('overlap', 'SUBTRACT', 2.0 * RADIUS, ('gap', 'Value'))
    g.math('half overlap', 'MULTIPLY', ('overlap', 0), 0.45)
    g.math('push', 'MAXIMUM', ('half overlap', 0), 0.0)
    g.vmath('move', 'SCALE', ('direction', 0))
    g.link('push', 0, 'move', 'Scale')
    g.node('GeometryNodeSetPosition', 'pushed', {'Geometry': ('all copies', 'Geometry'), 'Offset': ('move', 0)})
    g.node('GeometryNodeInputNamedAttribute', 'central read', {'Name': 'central'}, data_type='BOOLEAN')
    g.node('FunctionNodeBooleanMath', 'is ghost', {0: ('central read', 'Attribute')}, operation='NOT')
    g.node('GeometryNodeDeleteGeometry', 'drop ghosts', {'Geometry': ('pushed', 'Geometry'), 'Selection': ('is ghost', 'Boolean')}, domain='POINT')
    g.node('GeometryNodeInputPosition', 'pos2')
    g.node('ShaderNodeSeparateXYZ', 'xyz2', {'Vector': ('pos2', 'Position')})
    g.math('wrap x', 'WRAP', ('xyz2', 'X'), 1.0, 0.0)
    g.math('wrap y', 'WRAP', ('xyz2', 'Y'), 1.0, 0.0)
    g.node('ShaderNodeCombineXYZ', 'wrapped', {'X': ('wrap x', 0), 'Y': ('wrap y', 0), 'Z': 0.0})
    g.node('GeometryNodeSetPosition', 'wrap back', {'Geometry': ('drop ghosts', 'Geometry'), 'Position': ('wrapped', 'Vector')})
    return 'wrap back', 'Geometry'


def relax_group(name='Relax points (wrap)'):
    """Group: Points, Iterations -> relaxed Points (a Repeat zone around one relaxation step)."""
    existing = bpy.data.node_groups.get(name)
    if existing:
        return existing
    tree, g = gt.make_geometry_group(name, [('Points', 'NodeSocketGeometry', None), ('Iterations', 'NodeSocketInt', 30, 0, 500)], [('Points', 'NodeSocketGeometry')])
    g.node('GeometryNodeRepeatInput', 'repeat in', {'Iterations': ('in', 'Iterations')})
    g.node('GeometryNodeRepeatOutput', 'repeat out')
    g.nodes['repeat in'].pair_with_output(g.nodes['repeat out'])
    g.link('in', 'Points', 'repeat in', 'Geometry')
    node, socket = add_relax_step(g, ('repeat in', 'Geometry'))
    g.link(node, socket, 'repeat out', 'Geometry')
    g.link('repeat out', 'Geometry', 'out', 'Points')
    return tree


def starting_points_node(g, name, count, seed):
    """Random points inside 0..1 (a flat grid with Distribute Points on Faces, random mode)."""
    g.node('GeometryNodeMeshGrid', f'{name} grid', {'Size X': 1.0, 'Size Y': 1.0, 'Vertices X': 2, 'Vertices Y': 2})
    g.node('GeometryNodeTransform', f'{name} grid move', {'Geometry': (f'{name} grid', 'Mesh'), 'Translation': (0.5, 0.5, 0.0)})
    g.node('GeometryNodeDistributePointsOnFaces', name, {'Mesh': (f'{name} grid move', 'Geometry'), 'Density': float(count), 'Seed': seed}, distribute_method='RANDOM')
    return name, 'Points'


def positions_of(obj):
    return gt.evaluated_vertices(obj)[:, :2]


def periodic_stats(points, radius_sum):
    """Smallest wrap-around distance between any two points, and the share of points that have a neighbour closer than 90% of radius_sum."""
    delta = np.abs(points[:, None, :] - points[None, :, :])
    delta = np.minimum(delta, 1.0 - delta)
    distance = np.sqrt((delta ** 2).sum(-1))
    np.fill_diagonal(distance, 9.0)
    nearest = distance.min(axis=1)
    return {'min_distance': round(float(distance.min()), 4), 'median_nearest': round(float(np.median(nearest)), 4),
            'share_touching_(closer_than_0.9x_2r)': round(float((nearest < 0.9 * radius_sum).mean()), 3), 'points': len(points)}


def wrapper_object(name, build):
    tree, g = gt.make_geometry_group(name, [('Geometry', 'NodeSocketGeometry', None)])
    source = build(g)
    g.node('GeometryNodePointsToVertices', 'to vertices', {'Points': source})
    g.link('to vertices', 'Mesh', 'out', 'Geometry')
    return gt.add_geometry_object(name, tree)


def main():
    gt.new_scene(64)
    results = {'radius': RADIUS}
    relax = relax_group()
    # A: random
    obj_a, _ = wrapper_object('A random', lambda g: starting_points_node(g, 'a', N_POINTS, 3))
    points_a = positions_of(obj_a)
    results['A_random'] = periodic_stats(points_a, 2 * RADIUS)
    # B: Poisson disk
    def build_b(g):
        g.node('GeometryNodeMeshGrid', 'b grid', {'Size X': 1.0, 'Size Y': 1.0, 'Vertices X': 2, 'Vertices Y': 2})
        g.node('GeometryNodeTransform', 'b move', {'Geometry': ('b grid', 'Mesh'), 'Translation': (0.5, 0.5, 0.0)})
        g.node('GeometryNodeDistributePointsOnFaces', 'b', {'Mesh': ('b move', 'Geometry'), 'Distance Min': 2 * RADIUS, 'Density Max': 4000.0, 'Density Factor': 1.0, 'Seed': 3}, distribute_method='POISSON')
        return 'b', 'Points'
    obj_b, _ = wrapper_object('B poisson', build_b)
    points_b = positions_of(obj_b)
    results['B_poisson'] = periodic_stats(points_b, 2 * RADIUS)
    results['B_poisson']['note'] = 'Distance Min 2r; Poisson keeps spacing inside the tile but is unaware of the wrap-around neighbours'
    # C: random + repeat zone relaxation, 5 / 15 / 40 iterations
    for iterations in (5, 15, 40):
        def build_c(g, iterations=iterations):
            node, socket = starting_points_node(g, 'c', N_POINTS, 3)
            g.group('relax', relax, {'Points': (node, socket), 'Iterations': iterations})
            return 'relax', 'Points'
        started = time.time()
        obj_c, _ = wrapper_object(f'C relax {iterations}', build_c)
        points_c = positions_of(obj_c)
        results[f'C_repeat_zone_{iterations}_iterations'] = {**periodic_stats(points_c, 2 * RADIUS), 'seconds': round(time.time() - started, 2)}
        if iterations == 40:
            final_c = points_c
    # D: the same with a simulation zone, one step per frame
    tree, g = gt.make_geometry_group('D sim', [('Geometry', 'NodeSocketGeometry', None)])
    node, socket = starting_points_node(g, 'd', N_POINTS, 3)
    g.node('GeometryNodeSimulationInput', 'sim in')
    g.node('GeometryNodeSimulationOutput', 'sim out')
    g.nodes['sim in'].pair_with_output(g.nodes['sim out'])
    g.link(node, socket, 'sim in', 'Geometry')
    g.group('one step', relax_one_step_group(), {'Points': ('sim in', 'Geometry')})
    g.link('one step', 'Points', 'sim out', 'Geometry')
    g.node('GeometryNodePointsToVertices', 'to vertices', {'Points': ('sim out', 'Geometry')})
    g.link('to vertices', 'Mesh', 'out', 'Geometry')
    obj_d, _ = gt.add_geometry_object('D sim', tree)
    scene = bpy.context.scene
    scene.frame_start, scene.frame_end = 1, 60
    started = time.time()
    for frame in range(1, 42):
        scene.frame_set(frame)
    points_d = positions_of(obj_d)
    results['D_simulation_zone_40_steps'] = {**periodic_stats(points_d, 2 * RADIUS), 'seconds': round(time.time() - started, 2)}
    results['D_equals_C_40?'] = {'max_abs_difference_of_sorted_points': float(np.abs(np.sort(points_d[:, 0]) - np.sort(final_c[:, 0])).max())}
    np.save(os.path.join(OUT, 'points_a.npy'), points_a)
    np.save(os.path.join(OUT, 'points_b.npy'), points_b)
    np.save(os.path.join(OUT, 'points_c40.npy'), final_c)
    with open(os.path.join(OUT, 'results.json'), 'w') as handle:
        json.dump(results, handle, indent=1)
    print(json.dumps(results, indent=1))


def relax_one_step_group():
    """One relaxation step as its own group (for use inside a Simulation zone, where the zone supplies the repetition)."""
    name = 'Relax one step'
    existing = bpy.data.node_groups.get(name)
    if existing:
        return existing
    tree, g = gt.make_geometry_group(name, [('Points', 'NodeSocketGeometry', None)], [('Points', 'NodeSocketGeometry')])
    node, socket = add_relax_step(g, ('in', 'Points'))
    g.link(node, socket, 'out', 'Points')
    return tree


if __name__ == '__main__':
    main()
