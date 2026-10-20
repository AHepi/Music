# What this does (plain words): a small LOOK CHECK for the inventory, not a trial. It puts the FROZEN shared layers (colour and fade, damage, moss,
# outline and shadow, combine; imported unchanged from reuse_trials/shared_layers_snapshot/layers) on two quick layouts written here:
#   * WOOD BOARDS: 5 boards across the tile, each board cut into 2 lengths with a narrow butt joint. Two ways of handing the boards to the layers:
#       'wood_plain'  - the bundle as for slate: local_y runs DOWN the board (across the grain);
#       'wood_turned' - the bundle TURNED a quarter: local_y runs ALONG the board (with the grain), local_x across it, piece_height = board length.
#     The question: does turning the bundle make the shared layers lay their tall streaks, patches and cracks along the grain, with no layer change?
#   * BRICK: 12 courses of 4 bricks (the brick reference has about 4 per course; the earlier reuse test used 6), mortar 6.5 % of a brick sideways and
#     18 % up-down (measured once in recipes/brick: joints 20.4 dots of a 313.5-dot pitch, mortar band 18.6 of a 101.9-dot course).
#     'b1' = the earlier reuse test's settings round 2, b1 (copied below); 'flat' = b1 plus three paint settings that, by reading
#     colour_and_fade.py, should remove the pointed tongues (fade_direction 0) and make the mottling patches round (fade_length = streak_width, tallness 1).
# Parameters: 'layout' ('wood_plain', 'wood_turned', 'brick'), 'style' ('b1' or 'flat', brick only), 'only' (a layer name: show that layer's Colour alone),
# and any 'layer.setting'. Settings here were chosen in minutes by hand; nothing is fitted to a reference.
# Use: through look_check_run.py next to this file (one Blender run, colour pictures only).
import os
import sys

sys.dont_write_bytecode = True          # importing must not write a cache folder into the frozen snapshot
HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..'))
SNAPSHOT = os.path.join(PROC, 'reuse_trials', 'shared_layers_snapshot', 'layers')
if SNAPSHOT not in sys.path:
    sys.path.insert(0, SNAPSHOT)
import layer_interface as li  # noqa: E402
import colour_and_fade, damage, moss, outline_and_shadow, combine  # noqa: E401,E402

MODULES = {'colour_and_fade': colour_and_fade, 'damage': damage, 'moss': moss, 'outline_and_shadow': outline_and_shadow}
STACK = ['colour_and_fade', 'moss', 'damage', 'outline_and_shadow']

# copied from recipes/slate_layers/reuse/brick_layers_recipe.py (BRICK_SETTINGS) and reuse/settings_round_2/views.json (b1); data only
BRICK_B1 = {
    'colour_and_fade.tone_1': '#3a2018', 'colour_and_fade.tone_2': '#4a271c', 'colour_and_fade.tone_3': '#5c2e20', 'colour_and_fade.tone_4': '#6c3524',
    'colour_and_fade.tone_5': '#7a3c28', 'colour_and_fade.tone_6': '#8a452d', 'colour_and_fade.tone_7': '#9a5033', 'colour_and_fade.tone_8': '#a85d3c',
    'colour_and_fade.tone_9': '#b8714c', 'colour_and_fade.green_tint': '#6a5d3d', 'colour_and_fade.warm_tint': '#7a4a30',
    'colour_and_fade.tone_centre': 4.0, 'colour_and_fade.tone_spread': 1.1, 'colour_and_fade.fade_length': 0.04, 'colour_and_fade.streak_width': 0.016,
    'colour_and_fade.fade_direction': 0.5, 'colour_and_fade.top_darkening': 0.2, 'colour_and_fade.mottle_tallness': 1.0, 'colour_and_fade.speck_size': 0.008,
    'damage.chip_depth': 0.01, 'damage.chip_frequency': 140, 'damage.side_share': 0.7, 'damage.crack_length': 0.04, 'damage.crack_amount': 0.15,
    'damage.notch_depth': 0.005, 'damage.corner_break_size': 0.012, 'damage.corner_break_amount': 0.1, 'damage.pit_size': 0.0022, 'damage.scratch_length': 0.02,
    'damage.break_colour': '#a07a55', 'damage.break_colour_light': '#c9a981', 'damage.break_colour_dark': '#6e4a33',
    'moss.drip_length': 0.045, 'moss.drip_width': 0.03, 'moss.cluster_size': 0.03, 'moss.coverage': 0.2, 'moss.joint_preference': 0.8,
    'moss.drip_preference': 0.3, 'moss.lower_preference': 0.5, 'moss.flow_wobble': 0.006, 'moss.fringe_width': 0.005, 'moss.tone_patch_size': 0.012,
    'moss.lichen_size': 0.0025,
    'outline_and_shadow.joint_colour': '#9a8a74', 'outline_and_shadow.outline_colour': '#5a4a3e', 'outline_and_shadow.shadow_colour': '#2a1e18',
    'outline_and_shadow.shadow_width': 0.012, 'outline_and_shadow.shadow_darkness': 0.35, 'outline_and_shadow.band_width': 0.0,
    'outline_and_shadow.joint_width': 0.0012, 'outline_and_shadow.lip_colour': '#b09a80', 'outline_and_shadow.lip_width': 0.0015,
    'outline_and_shadow.black_drips': 0.0,
}
BRICK_FLAT = dict(BRICK_B1, **{'colour_and_fade.fade_direction': 0.0, 'colour_and_fade.fade_length': 0.03, 'colour_and_fade.streak_width': 0.03,
                                'colour_and_fade.mottle_tallness': 1.0})

# wood: nine browns picked by eye from the wood S1 description's 16-colour palette (recipes/wood/description/S1_layout_paint_grain.json), dark to light
WOOD = {
    'colour_and_fade.tone_1': '#191311', 'colour_and_fade.tone_2': '#2f211b', 'colour_and_fade.tone_3': '#3f281b', 'colour_and_fade.tone_4': '#43322a',
    'colour_and_fade.tone_5': '#513726', 'colour_and_fade.tone_6': '#533f35', 'colour_and_fade.tone_7': '#62432f', 'colour_and_fade.tone_8': '#705341',
    'colour_and_fade.tone_9': '#836652', 'colour_and_fade.green_tint': '#4f5458', 'colour_and_fade.warm_tint': '#7a4a30',
    'colour_and_fade.tone_centre': 4.0, 'colour_and_fade.tone_spread': 0.6, 'colour_and_fade.fade_direction': 0.0, 'colour_and_fade.top_darkening': 0.0,
    'colour_and_fade.streak_width': 0.012, 'colour_and_fade.fade_length': 0.03, 'colour_and_fade.mottle_tallness': 2.0, 'colour_and_fade.streak_contrast': 1.4,
    'colour_and_fade.speck_size': 0.006, 'colour_and_fade.speck_cover': 0.2, 'colour_and_fade.bleach_cover': 0.15, 'colour_and_fade.stain_cover': 0.15,
    'colour_and_fade.patch_size': 0.3, 'colour_and_fade.edge_ragged': 0.002, 'colour_and_fade.streak_bend': 0.004,
    # moss off; its lichen discs in rust browns as the reference's rust splatter clouds
    'moss.coverage': 0.0, 'moss.lichen_amount': 0.4, 'moss.lichen_clustering': 0.85, 'moss.lichen_size': 0.004,
    'moss.lichen_colour': '#6b3a22', 'moss.lichen_light': '#8a4b2a', 'moss.lichen_dark': '#4a2616',
    # damage: long dark cracks that run "down the piece" (= along the grain when turned), a few chips on the long edges, no corner breaks
    'damage.crack_amount': 0.6, 'damage.crack_length': 0.08, 'damage.crack_width': 0.003, 'damage.crack_across_share': 0.0, 'damage.crack_slots': 2,
    'damage.chip_amount': 0.3, 'damage.chip_depth': 0.008, 'damage.side_share': 0.8, 'damage.notch_amount': 0.0, 'damage.corner_break_amount': 0.0,
    'damage.pit_amount': 0.03, 'damage.scratch_amount': 0.1,
    'damage.break_colour': '#8a6a4f', 'damage.break_colour_light': '#a88a6a', 'damage.break_colour_dark': '#4a3426', 'damage.hole_colour': '#120d0b',
    # outline: dark gaps, thin side line, no shadow band or lip (boards lie side by side, none overlaps the next)
    'outline_and_shadow.joint_colour': '#120d0b', 'outline_and_shadow.shadow_width': 0.0, 'outline_and_shadow.shadow_darkness': 0.0,
    'outline_and_shadow.lip_brightness': 0.0, 'outline_and_shadow.side_outline_width': 0.0015, 'outline_and_shadow.black_drips': 0.0,
}


def board_bundle(b, vector, rows, lengths, gap_y, gap_x, turned):
    """Eleven layout numbers for horizontal boards (rows counted from the bottom of the picture); every board row's butt joints slid by its own
    random amount. turned = True: local_y runs along the board, local_x across it (the bundle is turned a quarter)."""
    u, v, _ = b.xyz(vector)
    v_rows = b.mul(v, float(rows))
    row_id = b.floor(v_rows)
    up = b.frac(v_rows)                                                     # 0 at the bottom of the board row, 1 at its top
    wrapped_row = b.mod(row_id, float(rows))
    slide = b.hash4(b.vec(wrapped_row, 3.1, 0.0), 7.0).outputs['Value']
    u_lengths = b.add(b.mul(u, float(lengths)), slide)
    column_id = b.floor(u_lengths)
    along = b.frac(u_lengths)
    long_, high = 1.0 / lengths, 1.0 / rows
    left, right = b.mul(b.sub(along, gap_x / 2.0), long_), b.mul(b.sub(b.sub(1.0, along), gap_x / 2.0), long_)
    top, bottom = b.mul(b.sub(b.sub(1.0, up), gap_y / 2.0), high), b.mul(b.sub(up, gap_y / 2.0), high)
    inside = b.mn(b.mn(left, right), b.mn(top, bottom))
    on_piece = b.gt(inside, 0.0)
    wrapped_column = b.mod(column_id, float(lengths))
    across_01 = b.maprange(up, 1.0 - gap_y / 2.0, gap_y / 2.0, 0.0, 1.0, True)          # 0 at the top of the board, 1 at its bottom
    along_01 = b.maprange(along, gap_x / 2.0, 1.0 - gap_x / 2.0, 0.0, 1.0, True)        # 0 at the left end, 1 at the right end
    board_height, board_length = (1.0 - gap_y) * high, (1.0 - gap_x) * long_
    bundle = {
        'piece_id': b.hash4(b.vec(wrapped_column, wrapped_row, 0.9), 0.4).outputs['Value'],
        'row': b.div(wrapped_row, float(rows)),
        'edge_distance': b.mul(b.mx(inside, 0.0), on_piece),
        'gap_mask': b.sub(1.0, on_piece), 'piece_mask': on_piece,
        'base_height': b.add(0.08, b.mul(on_piece, 0.42)),
    }
    if turned:
        bundle.update({'local_x': across_01, 'local_y': along_01, 'piece_width': board_height, 'piece_height': board_length,
                       'top_edge_distance': b.mul(b.mx(left, 0.0), on_piece)})
    else:
        bundle.update({'local_x': along_01, 'local_y': across_01, 'piece_width': board_length, 'piece_height': board_height,
                       'top_edge_distance': b.mul(b.mx(top, 0.0), on_piece)})
    return bundle


def brick_bundle(b, vector, columns, rows, mx, my):
    """The earlier reuse test's brick layout (recipes/slate_layers/reuse/brick_layers_recipe.py), with the counts and mortar shares as arguments."""
    u, v, _ = b.xyz(vector)
    v_rows = b.mul(v, float(rows))
    row_id = b.floor(v_rows)
    up = b.frac(v_rows)
    odd = b.mod(row_id, 2.0)
    u_bricks = b.add(b.mul(u, float(columns)), b.mul(odd, 0.5))
    column_id = b.floor(u_bricks)
    across = b.frac(u_bricks)
    wide, high = 1.0 / columns, 1.0 / rows
    left, right = b.mul(b.sub(across, mx / 2.0), wide), b.mul(b.sub(b.sub(1.0, across), mx / 2.0), wide)
    top, bottom = b.mul(b.sub(b.sub(1.0, up), my / 2.0), high), b.mul(b.sub(up, my / 2.0), high)
    inside = b.mn(b.mn(left, right), b.mn(top, bottom))
    on_brick = b.gt(inside, 0.0)
    wrapped_column, wrapped_row = b.mod(column_id, float(columns)), b.mod(row_id, float(rows))
    return {
        'piece_id': b.hash4(b.vec(wrapped_column, wrapped_row, 0.7), 0.3).outputs['Value'],
        'row': b.div(wrapped_row, float(rows)),
        'local_x': b.maprange(across, mx / 2.0, 1.0 - mx / 2.0, 0.0, 1.0, True),
        'local_y': b.maprange(up, 1.0 - my / 2.0, my / 2.0, 0.0, 1.0, True),
        'piece_width': (1.0 - mx) * wide, 'piece_height': (1.0 - my) * high,
        'edge_distance': b.mul(b.mx(inside, 0.0), on_brick),
        'top_edge_distance': b.mul(b.mx(top, 0.0), on_brick),
        'gap_mask': b.sub(1.0, on_brick), 'piece_mask': on_brick,
        'base_height': b.add(0.08, b.mul(on_brick, 0.42)),
    }


def build_node_group(parameters):
    parameters = dict(parameters or {})
    which = parameters.get('layout', 'wood_turned')
    if which == 'brick':
        settings = dict(BRICK_FLAT if parameters.get('style') == 'flat' else BRICK_B1)
    else:
        settings = dict(WOOD)
    settings.update({k: v for k, v in parameters.items() if '.' in k})
    tree, b = li.make_plain_group('LOOK CHECK', [('Vector', 'vector', (0.0, 0.0, 0.0), None, None, '')],
                                  [('Colour', 'colour', ''), ('Roughness', 'float', ''), ('Metallic', 'float', ''), ('Height', 'float', '')])
    vector = b.input('Vector')
    if which == 'brick':
        bundle = brick_bundle(b, vector, 4, 12, 0.065, 0.18)
    else:
        bundle = board_bundle(b, vector, 5, 2, 0.028, 0.004, which == 'wood_turned')
    layer_nodes = {}
    for name in STACK:
        node = b.node('ShaderNodeGroup')
        node.node_tree = MODULES[name].build_group(settings)
        node.label = MODULES[name].GROUP_NAME
        layer_nodes[name] = node
        b.tree.links.new(vector, node.inputs['Vector'])
        node.inputs['Tile Count'].default_value = 1.0
        for bundle_name in li.BUNDLE_NAMES:
            value = bundle[bundle_name]
            if isinstance(value, (int, float)):
                node.inputs[bundle_name].default_value = float(value)
            else:
                b.tree.links.new(value, node.inputs[bundle_name])
    for name, node in layer_nodes.items():                                  # the declared link moss <- damage, as in the slate recipe
        for link in MODULES[name].DECLARED_LINKS:
            b.tree.links.new(layer_nodes[link[4][0]].outputs[link[4][1]], node.inputs[link[0]])
    combine_node = b.node('ShaderNodeGroup')
    combine_node.node_tree = combine.build_group(settings)
    b.tree.links.new(bundle['base_height'], combine_node.inputs['base_height'])
    for name, node in layer_nodes.items():
        for output in li.OUTPUT_NAMES:
            b.tree.links.new(node.outputs[output], combine_node.inputs[f'{name} {output}'])
    only = parameters.get('only')
    colour = combine_node.outputs['Colour'] if not only else layer_nodes[only].outputs['Colour']
    b.tree.links.new(colour, b.w.nodes['out'].inputs['Colour'])
    for output in ('Roughness', 'Metallic', 'Height'):
        b.tree.links.new(combine_node.outputs[output], b.w.nodes['out'].inputs[output])
    return tree
