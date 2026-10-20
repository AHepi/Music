# What this does: the "relax points on a wrapping tile" building block, as a reusable Geometry Nodes group (tested in t06_relax_repeat_zone.py).
# It takes points that carry a float attribute 'radius' (the room each point needs) and pushes overlapping points apart, many times in a Repeat zone, measuring distances
# the wrap-around way, so the result repeats perfectly when the tile is repeated.
# One step: store central = True -> 9 copies of the points (shifted by -1, 0, +1 in x and y; copies get central = False) -> every point asks Index of Nearest for its nearest
# OTHER point -> the pair is pushed apart by 0.45 of the overlap ((own radius + neighbour radius) x tightness - distance) -> copies are deleted -> positions are wrapped back into 0..1.
# Use (inside Blender):  import relax_tools as rx ;  group = rx.relax_group_with_radius()   inputs: Points, Iterations, Tightness   output: Points
import bpy

import gn_tools as gt


def add_relax_step(g, source, tightness_source):
    """Adds one relaxation step to writer g. source = (node, socket) of points with a 'radius' attribute; tightness_source = (node, socket) of a float
    (1.0 = stones may just touch as circles; 0.85 = they may overlap by 15% of their radii, which suits angular stones). Returns (node, socket) of the result."""
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
    g.node('GeometryNodeInputNamedAttribute', 'own radius', {'Name': 'radius'}, data_type='FLOAT')
    g.node('GeometryNodeIndexOfNearest', 'nearest', {'Position': ('pos', 'Position')})
    g.node('GeometryNodeSampleIndex', 'neighbour pos', {'Geometry': ('all copies', 'Geometry'), 'Value': ('pos', 'Position'), 'Index': ('nearest', 'Index')}, domain='POINT', data_type='FLOAT_VECTOR')
    g.node('GeometryNodeSampleIndex', 'neighbour radius', {'Geometry': ('all copies', 'Geometry'), 'Value': ('own radius', 'Attribute'), 'Index': ('nearest', 'Index')}, domain='POINT', data_type='FLOAT')
    g.vmath('away', 'SUBTRACT', ('pos', 'Position'), ('neighbour pos', 'Value'))
    g.vmath('gap', 'LENGTH', ('away', 0))
    g.vmath('direction', 'NORMALIZE', ('away', 0))
    g.math('radii sum', 'ADD', ('own radius', 'Attribute'), ('neighbour radius', 'Value'))
    g.math('needed', 'MULTIPLY', ('radii sum', 0), tightness_source)
    g.math('overlap', 'SUBTRACT', ('needed', 0), ('gap', 'Value'))
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


def relax_group_with_radius(name='Relax points with radius (wrap)'):
    existing = bpy.data.node_groups.get(name)
    if existing:
        return existing
    tree, g = gt.make_geometry_group(name, [('Points', 'NodeSocketGeometry', None), ('Iterations', 'NodeSocketInt', 40, 0, 500), ('Tightness', 'NodeSocketFloat', 0.9, 0.3, 1.5)],
                                     [('Points', 'NodeSocketGeometry')])
    g.node('GeometryNodeRepeatInput', 'repeat in', {'Iterations': ('in', 'Iterations')})
    g.node('GeometryNodeRepeatOutput', 'repeat out')
    g.nodes['repeat in'].pair_with_output(g.nodes['repeat out'])
    g.link('in', 'Points', 'repeat in', 'Geometry')
    node, socket = add_relax_step(g, ('repeat in', 'Geometry'), ('in', 'Tightness'))
    g.link(node, socket, 'repeat out', 'Geometry')
    g.link('repeat out', 'Geometry', 'out', 'Points')
    return tree
