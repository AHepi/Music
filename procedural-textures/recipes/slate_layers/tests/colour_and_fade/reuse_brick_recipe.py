# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------
# The REUSE test of COLOUR AND FADE: the same layer box, on a surface that is NOT slate. This recipe makes a quick BRICK WALL layout
# (columns and rows of bricks, every second row slid by half a brick, mortar between) with the stock helper lib/contrib/builder.py, turns
# it into the same eleven numbers LAYOUT gives (the "layout bundle": piece_id, row, local_x, local_y, piece_width, piece_height,
# edge_distance, top_edge_distance, gap_mask, piece_mask, base_height) and plugs them into the UNCHANGED colour_and_fade.py. The only
# things changed are SETTINGS (the nine palette colours become brick reds and browns, the fade is shorter), written in BRICK_SETTINGS below.
# What the test shows: the layer only needs the bundle's names and ranges; it does not care whether the pieces are slates or bricks.
# Run with the harness:  blender -b --python lib/bake_harness.py -- THIS_FILE OUT --size 1254   (or tests/bake_tools.py with views)
# Parameters (all optional): any 'colour_and_fade.*' setting overrides BRICK_SETTINGS; 'columns', 'rows' (whole numbers, default 6 and 12).
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LAYERS = os.path.abspath(os.path.join(HERE, '..', '..', 'layers'))
if LAYERS not in sys.path:
    sys.path.insert(0, LAYERS)
import layer_interface as li  # noqa: E402
import colour_and_fade  # noqa: E402

BRICK_SETTINGS = {
    # nine brick colours, darkest to lightest (burnt brown to pale sandy mortar-dust)
    'colour_and_fade.tone_1': '#2b1a14', 'colour_and_fade.tone_2': '#3a2219', 'colour_and_fade.tone_3': '#4b2a1d', 'colour_and_fade.tone_4': '#5e3322',
    'colour_and_fade.tone_5': '#74402a', 'colour_and_fade.tone_6': '#8a4d31', 'colour_and_fade.tone_7': '#a05e3b', 'colour_and_fade.tone_8': '#b57a52',
    'colour_and_fade.tone_9': '#c69a78',
    'colour_and_fade.green_tint': '#6a5d3d', 'colour_and_fade.warm_tint': '#7a4a30',
    'colour_and_fade.tone_centre': 4.0, 'colour_and_fade.fade_length': 0.045, 'colour_and_fade.streak_width': 0.02,
    'colour_and_fade.fade_direction': 0.6, 'colour_and_fade.top_darkening': 0.3,
}


def build_node_group(parameters):
    parameters = dict(parameters or {})
    settings = dict(BRICK_SETTINGS)
    settings.update({k: v for k, v in parameters.items() if k.startswith('colour_and_fade.') or k.startswith('recipe.')})
    columns, rows = int(parameters.get('columns', 6)), int(parameters.get('rows', 12))
    tree, b = li.make_plain_group('BRICK reuse test', [('Vector', 'vector', (0.0, 0.0, 0.0), None, None, '')],
                                  [('Colour', 'colour', ''), ('Roughness', 'float', ''), ('Metallic', 'float', ''), ('Height', 'float', '')])
    u, v, _ = b.xyz(b.input('Vector'))
    # brick layout: rows counted from the BOTTOM (v up); every second row slid by half a brick; whole numbers so that the tile repeats
    v_rows = b.mul(v, float(rows))
    row_id = b.floor(v_rows)
    up_the_brick = b.frac(v_rows)                                               # 0 at the bottom of the brick row, 1 at the top
    odd = b.mod(row_id, 2.0)
    u_bricks = b.add(b.mul(u, float(columns)), b.mul(odd, 0.5))
    column_id = b.floor(u_bricks)
    across = b.frac(u_bricks)                                                    # 0..1 along the brick
    mortar_x, mortar_y = 0.06, 0.12                                              # mortar share of a brick, sideways and up-down
    inside_x = b.mn(across, b.sub(1.0, across))                                   # distance from the nearest side, in brick widths
    inside_y = b.mn(up_the_brick, b.sub(1.0, up_the_brick))
    on_brick = b.mul(b.gt(inside_x, mortar_x * 0.5), b.gt(inside_y, mortar_y * 0.5))
    local_x = b.maprange(across, mortar_x * 0.5, 1.0 - mortar_x * 0.5, 0.0, 1.0, True)
    local_y = b.maprange(up_the_brick, 1.0 - mortar_y * 0.5, mortar_y * 0.5, 0.0, 1.0, True)    # 0 at the TOP of the brick (the bundle's rule)
    piece_width, piece_height = (1.0 - mortar_x) / columns, (1.0 - mortar_y) / rows
    wrapped_column = b.mod(column_id, float(columns))
    wrapped_row = b.mod(row_id, float(rows))
    piece_id = b.hash4(b.vec(wrapped_column, wrapped_row, 0.7), 0.3).outputs['Value']
    edge = b.mn(b.mul(inside_x, piece_width * columns / columns), b.mul(inside_y, piece_height))
    bundle = {'piece_id': piece_id, 'row': b.div(wrapped_row, float(rows)), 'local_x': local_x, 'local_y': local_y, 'piece_width': piece_width,
              'piece_height': piece_height, 'edge_distance': b.mul(edge, on_brick), 'top_edge_distance': b.mul(b.mx(b.sub(1.0, local_y), 0.0), 0.0),
              'gap_mask': b.sub(1.0, on_brick), 'piece_mask': on_brick, 'base_height': b.add(0.1, b.mul(on_brick, 0.4))}
    layer = b.node('ShaderNodeGroup')
    layer.node_tree = colour_and_fade.build_group(settings)
    layer.label = 'COLOUR AND FADE (unchanged code)'
    b.tree.links.new(b.input('Vector'), layer.inputs['Vector'])
    layer.inputs['Tile Count'].default_value = 1.0
    for name in li.BUNDLE_NAMES:
        value = bundle[name]
        if isinstance(value, (int, float)):
            layer.inputs[name].default_value = float(value)
        else:
            b.tree.links.new(value, layer.inputs[name])
    mortar = b.mix('#6d655a', '#4a443c', b.hash4(b.vec(wrapped_column, wrapped_row, 3.3), 1.1).outputs['Value'])
    colour = b.mix(mortar, layer.outputs['Colour'], on_brick)
    b.output('Colour', colour)
    b.output('Height', b.math('ADD', bundle['base_height'], layer.outputs['Height'], clamp=True))
    b.output('Roughness', b.add(0.8, layer.outputs['Roughness']))
    b.output('Metallic', 0.0)
    return tree
