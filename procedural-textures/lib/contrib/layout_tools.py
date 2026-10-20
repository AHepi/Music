# What this does: builds the reusable "row layout" Geometry Nodes group that the brick, slate, plank and plate recipes all share.
# It answers: "where does each piece of a tiled wall/roof/floor go?" and outputs one POINT per piece (a point cloud, in tile
# coordinates where the tile is x 0..1, y 0..1) carrying these named attributes:
#     piece_id  (int)    a number that is the SAME for a piece and its wrap-around copies (use it for random colours/heights)
#     piece_w   (float)  width of the piece in tile units (already minus the gap)
#     piece_h   (float)  height of the piece in tile units (row pitch x Height factor, minus the gap)
#     piece_centre (vector) the piece's centre (x, y, 0), including the wrap shift for copies
#     row       (int)    which row the piece is in
#     is_copy   (bool)   True for the wrap-around copies (the ones that sit outside the 0..1 square and complete a piece that
#                        crosses the tile edge)
# How: Mesh Line (one point per piece) -> row = floor(index / pieces per row) -> a random weight per piece -> Accumulate Field
# per row turns the weights into piece edges that always add up to exactly 1.0 (so the row repeats exactly) -> a row shift (half
# brick bond with some randomness) -> Wrap -> Duplicate Elements (9 copies shifted by -1, 0, +1 in x and y) -> delete the copies that
# do not touch the 0..1 square.
# Use (inside Blender):  import layout_tools as lt ;  tree = lt.row_layout_group()
import bpy

import gn_tools as gt


def row_layout_group(name='Row layout points'):
    existing = bpy.data.node_groups.get(name)
    if existing:
        return existing
    tree, g = gt.make_geometry_group(name, [
        ('Rows', 'NodeSocketInt', 12, 1, 64), ('Per row', 'NodeSocketInt', 4, 1, 64),
        ('Width jitter', 'NodeSocketFloat', 0.25, 0.0, 0.95), ('Row shift randomness', 'NodeSocketFloat', 0.5, 0.0, 1.0),
        ('Gap', 'NodeSocketFloat', 0.02, 0.0, 0.3), ('Height factor', 'NodeSocketFloat', 1.0, 0.1, 3.0),
        ('Seed', 'NodeSocketInt', 0, -1000, 100000), ('Wrap', 'NodeSocketBool', True)])
    i = 'in'
    # one point per piece
    g.math('count', 'MULTIPLY', (i, 'Rows'), (i, 'Per row'))
    g.node('GeometryNodeMeshLine', 'line', {'Count': ('count', 0), 'Offset': (0.0, 0.0, 0.0)}, mode='OFFSET')
    g.node('GeometryNodeMeshToPoints', 'points', {'Mesh': ('line', 'Mesh')})
    g.node('GeometryNodeInputIndex', 'index')
    # row and random weights
    g.math('index over per row', 'DIVIDE', ('index', 'Index'), (i, 'Per row'))
    g.math('row', 'FLOOR', ('index over per row', 0))
    g.node('FunctionNodeRandomValue', 'weight', {'ID': ('index', 'Index'), 'Seed': (i, 'Seed')}, data_type='FLOAT')
    g.math('weight min', 'SUBTRACT', 1.0, (i, 'Width jitter'))
    g.math('weight max', 'ADD', 1.0, (i, 'Width jitter'))
    g.link('weight min', 0, 'weight', 'Min')
    g.link('weight max', 0, 'weight', 'Max')
    g.node('GeometryNodeAccumulateField', 'accumulate', {'Value': ('weight', 'Value'), 'Group ID': ('row', 0)}, data_type='FLOAT', domain='POINT')
    g.math('x start', 'DIVIDE', ('accumulate', 'Trailing'), ('accumulate', 'Total'))   # Trailing = running total BEFORE this piece (starts at 0); Leading includes this piece
    g.math('width', 'DIVIDE', ('weight', 'Value'), ('accumulate', 'Total'))
    # row shift: half-brick bond (0, 0.5, 0, 0.5...) blended with a random shift per row
    g.math('seed plus', 'ADD', (i, 'Seed'), 101)
    g.node('FunctionNodeRandomValue', 'row random', {'ID': ('row', 0), 'Seed': ('seed plus', 0)}, data_type='FLOAT')
    g.math('row odd', 'MODULO', ('row', 0), 2.0)
    g.math('bond', 'MULTIPLY', ('row odd', 0), 0.5)
    g.math('one minus randomness', 'SUBTRACT', 1.0, (i, 'Row shift randomness'))
    g.math('bond part', 'MULTIPLY', ('bond', 0), ('one minus randomness', 0))
    g.math('random part', 'MULTIPLY', ('row random', 'Value'), (i, 'Row shift randomness'))
    g.math('shift', 'ADD', ('bond part', 0), ('random part', 0))
    g.math('half width', 'MULTIPLY', ('width', 0), 0.5)
    g.math('centre unwrapped', 'ADD', ('x start', 0), ('half width', 0))
    g.math('centre shifted', 'ADD', ('centre unwrapped', 0), ('shift', 0))
    g.math('centre x', 'WRAP', ('centre shifted', 0), 1.0, 0.0)
    g.math('row plus half', 'ADD', ('row', 0), 0.5)
    g.math('pitch', 'DIVIDE', 1.0, (i, 'Rows'))
    g.math('centre y', 'MULTIPLY', ('row plus half', 0), ('pitch', 0))
    g.node('ShaderNodeCombineXYZ', 'centre', {'X': ('centre x', 0), 'Y': ('centre y', 0), 'Z': 0.0})
    g.math('piece w', 'SUBTRACT', ('width', 0), (i, 'Gap'))
    g.math('tall', 'MULTIPLY', ('pitch', 0), (i, 'Height factor'))
    g.math('piece h', 'SUBTRACT', ('tall', 0), (i, 'Gap'))
    # place the points and write the attributes
    g.node('GeometryNodeSetPosition', 'place', {'Geometry': ('points', 'Points'), 'Position': ('centre', 'Vector')})
    previous = ('place', 'Geometry')
    for name_, kind, value in (('piece_id', 'INT', ('index', 'Index')), ('piece_w', 'FLOAT', ('piece w', 0)),
                               ('piece_h', 'FLOAT', ('piece h', 0)), ('row', 'INT', ('row', 0))):
        node = f'store {name_}'
        g.node('GeometryNodeStoreNamedAttribute', node, {'Geometry': previous, 'Name': name_, 'Value': value}, data_type=kind, domain='POINT')
        previous = (node, 'Geometry')
    # nine copies, shifted by -1, 0, +1 in x and y. The original is copy number 4 (the middle one).
    g.node('GeometryNodeDuplicateElements', 'copies', {'Geometry': previous, 'Amount': 9}, domain='POINT')
    g.math('copy x index', 'MODULO', ('copies', 'Duplicate Index'), 3.0)
    g.math('copy x', 'SUBTRACT', ('copy x index', 0), 1.0)
    g.math('copy over 3', 'DIVIDE', ('copies', 'Duplicate Index'), 3.0)
    g.math('copy y index', 'FLOOR', ('copy over 3', 0))
    g.math('copy y', 'SUBTRACT', ('copy y index', 0), 1.0)
    g.node('ShaderNodeCombineXYZ', 'copy shift', {'X': ('copy x', 0), 'Y': ('copy y', 0), 'Z': 0.0})
    g.node('GeometryNodeSetPosition', 'shift copies', {'Geometry': ('copies', 'Geometry'), 'Offset': ('copy shift', 'Vector')})
    # which copies are needed: the piece (centre +- half size, with a margin) must touch the 0..1 square
    g.node('GeometryNodeInputPosition', 'where')
    g.node('ShaderNodeSeparateXYZ', 'where xyz', {'Vector': ('where', 'Position')})
    g.node('GeometryNodeStoreNamedAttribute', 'store centre', {'Geometry': ('shift copies', 'Geometry'), 'Name': 'piece_centre', 'Value': ('where', 'Position')},
           data_type='FLOAT_VECTOR', domain='POINT')
    g.node('GeometryNodeInputNamedAttribute', 'w attr', {'Name': 'piece_w'}, data_type='FLOAT')
    g.node('GeometryNodeInputNamedAttribute', 'h attr', {'Name': 'piece_h'}, data_type='FLOAT')
    g.math('half w', 'MULTIPLY', ('w attr', 'Attribute'), 0.55)
    g.math('half h', 'MULTIPLY', ('h attr', 'Attribute'), 0.55)
    tests = []
    for label, coordinate, half, op in (('left', 'X', 'half w', 'ADD'), ('right', 'X', 'half w', 'SUBTRACT'),
                                        ('below', 'Y', 'half h', 'ADD'), ('above', 'Y', 'half h', 'SUBTRACT')):
        g.math(f'edge {label}', op, ('where xyz', coordinate), (half, 0))
        if op == 'ADD':
            g.node('FunctionNodeCompare', f'ok {label}', {'A': (f'edge {label}', 0), 'B': 0.0}, data_type='FLOAT', operation='GREATER_THAN')
        else:
            g.node('FunctionNodeCompare', f'ok {label}', {'A': (f'edge {label}', 0), 'B': 1.0}, data_type='FLOAT', operation='LESS_THAN')
        tests.append(f'ok {label}')
    g.node('FunctionNodeBooleanMath', 'ok x', {0: ('ok left', 'Result'), 1: ('ok right', 'Result')}, operation='AND')
    g.node('FunctionNodeBooleanMath', 'ok y', {0: ('ok below', 'Result'), 1: ('ok above', 'Result')}, operation='AND')
    g.node('FunctionNodeBooleanMath', 'touches', {0: ('ok x', 'Boolean'), 1: ('ok y', 'Boolean')}, operation='AND')
    g.node('FunctionNodeCompare', 'is original', {'A': ('copies', 'Duplicate Index'), 'B': 4}, data_type='INT', operation='EQUAL')
    g.node('FunctionNodeBooleanMath', 'is copy', {0: ('is original', 'Result')}, operation='NOT')
    g.node('FunctionNodeBooleanMath', 'not needed', {0: ('touches', 'Boolean')}, operation='NOT')
    g.node('FunctionNodeBooleanMath', 'no wrap', {0: (i, 'Wrap')}, operation='NOT')
    g.node('FunctionNodeBooleanMath', 'copy useless', {0: ('not needed', 'Boolean'), 1: ('no wrap', 'Boolean')}, operation='OR')
    g.node('FunctionNodeBooleanMath', 'delete copy', {0: ('is copy', 'Boolean'), 1: ('copy useless', 'Boolean')}, operation='AND')
    g.node('GeometryNodeDeleteGeometry', 'remove', {'Geometry': ('store centre', 'Geometry'), 'Selection': ('delete copy', 'Boolean')}, domain='POINT', mode='ALL')
    g.node('GeometryNodeStoreNamedAttribute', 'store is_copy', {'Geometry': ('remove', 'Geometry'), 'Name': 'is_copy', 'Value': ('is copy', 'Boolean')},
           data_type='BOOLEAN', domain='POINT')
    g.link('store is_copy', 'Geometry', 'out', 'Geometry')
    return tree


def debug_object(tree, name='layout debug', **inputs):
    """An object that shows the layout group's points as plain vertices, so Python can read them back and check the numbers."""
    wrapper, g = gt.make_geometry_group(name + ' wrapper', [('Geometry', 'NodeSocketGeometry', None)])
    g.node('GeometryNodeGroup', 'layout')
    g.nodes['layout'].node_tree = tree
    for key, value in inputs.items():
        g.nodes['layout'].inputs[key.replace('_', ' ')].default_value = value
    g.node('GeometryNodePointsToVertices', 'to mesh', {'Points': ('layout', 'Geometry')})
    g.link('to mesh', 'Mesh', 'out', 'Geometry')
    obj, modifier = gt.add_geometry_object(name, wrapper)
    return obj
