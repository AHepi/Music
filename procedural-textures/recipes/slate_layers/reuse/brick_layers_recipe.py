# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------
# THE REUSE TEST. The claim of the layered recipe is: "any surface that can make the same eleven layout numbers (the layout bundle) can use the
# same COLOUR AND FADE, DAMAGE, MOSS and OUTLINE AND SHADOW boxes". This recipe tests it on a surface that is NOT slate: a BRICK WALL.
#   * A small BRICK LAYOUT (written here, about 40 lines of nodes, not slate's 300) cuts the picture into rows and columns of bricks (every second
#     row slid by half a brick) with mortar between, and gives the eleven numbers: piece_id, row, local_x, local_y, piece_width, piece_height,
#     edge_distance, top_edge_distance, gap_mask, piece_mask, base_height. (local_y is 0 at the TOP of the brick, as the interface demands.)
#   * The four layer boxes are the UNCHANGED files in ../layers/ (colour_and_fade.py, damage.py, moss.py, outline_and_shadow.py) and so is COMBINE.
#   * The only things changed are SETTINGS (BRICK_SETTINGS below): brick reds instead of blue-greys, shorter drips because a brick is shorter than a
#     slate, damage and moss sized to a brick, a mortar-coloured joint instead of near-black. Everything the person has to change is that dictionary.
# Wiring (which box feeds which, and the declared link moss <- damage) is the same as in ../recipe/slate_recipe.py.
# Run with the harness:  blender -b --python lib/bake_harness.py -- THIS_FILE OUT_FOLDER --size 1254
# Parameters (all optional): 'columns', 'rows' (whole numbers; 6 and 12), 'only' (a layer name: show that layer's Colour alone), 'mask_of' (a layer name: show
# that layer's Mask as grey), any
# 'layer.setting' overrides BRICK_SETTINGS, 'bundle_view': name of a bundle number to show as grey.
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LAYERS = os.path.abspath(os.path.join(HERE, '..', 'layers'))
if LAYERS not in sys.path:
    sys.path.insert(0, LAYERS)
import layer_interface as li  # noqa: E402
import colour_and_fade, damage, moss, outline_and_shadow, combine  # noqa: E402

MODULES = {'colour_and_fade': colour_and_fade, 'damage': damage, 'moss': moss, 'outline_and_shadow': outline_and_shadow}
STACK = ['colour_and_fade', 'moss', 'damage', 'outline_and_shadow']

# every setting that differs from slate. Nothing else (no node, no line of any layer file) was touched.
BRICK_SETTINGS = {
    # COLOUR AND FADE: nine brick colours, darkest (burnt brown) to lightest (sun-bleached sandy brick)
    'colour_and_fade.tone_1': '#2b1a14', 'colour_and_fade.tone_2': '#3a2219', 'colour_and_fade.tone_3': '#4b2a1d', 'colour_and_fade.tone_4': '#5e3322',
    'colour_and_fade.tone_5': '#74402a', 'colour_and_fade.tone_6': '#8a4d31', 'colour_and_fade.tone_7': '#a05e3b', 'colour_and_fade.tone_8': '#b57a52',
    'colour_and_fade.tone_9': '#c69a78', 'colour_and_fade.green_tint': '#6a5d3d', 'colour_and_fade.warm_tint': '#7a4a30',
    'colour_and_fade.tone_centre': 4.0, 'colour_and_fade.tone_spread': 1.1, 'colour_and_fade.fade_length': 0.04, 'colour_and_fade.streak_width': 0.016,
    'colour_and_fade.fade_direction': 0.5, 'colour_and_fade.top_darkening': 0.2, 'colour_and_fade.mottle_tallness': 1.0, 'colour_and_fade.speck_size': 0.008,
    # DAMAGE: a brick is shorter than a slate, so flakes are smaller; chips on all edges; paler sandy breaks
    'damage.chip_depth': 0.01, 'damage.chip_frequency': 140, 'damage.side_share': 0.7, 'damage.crack_length': 0.04, 'damage.crack_amount': 0.15,
    'damage.notch_depth': 0.005, 'damage.corner_break_size': 0.012, 'damage.corner_break_amount': 0.1, 'damage.pit_size': 0.0022, 'damage.scratch_length': 0.02,
    'damage.break_colour': '#a07a55', 'damage.break_colour_light': '#c9a981', 'damage.break_colour_dark': '#6e4a33',
    # MOSS: shorter and narrower drips, mostly in the lower courses and along the joints
    'moss.drip_length': 0.045, 'moss.drip_width': 0.03, 'moss.cluster_size': 0.03, 'moss.coverage': 0.2, 'moss.joint_preference': 0.8,
    'moss.drip_preference': 0.3, 'moss.lower_preference': 0.5, 'moss.flow_wobble': 0.006, 'moss.fringe_width': 0.005, 'moss.tone_patch_size': 0.012,
    'moss.lichen_size': 0.0025,
    # OUTLINE AND SHADOW: mortar grey instead of near-black joints, a thinner shadow
    'outline_and_shadow.joint_colour': '#4a443c', 'outline_and_shadow.outline_colour': '#3a352f', 'outline_and_shadow.shadow_colour': '#2a2622',
    'outline_and_shadow.shadow_width': 0.012, 'outline_and_shadow.shadow_darkness': 0.4, 'outline_and_shadow.band_width': 0.0, 'outline_and_shadow.joint_width': 0.0012,
    'outline_and_shadow.lip_colour': '#b3a58d', 'outline_and_shadow.lip_width': 0.0015, 'outline_and_shadow.black_drips': 0.0,
}
MORTAR_SHARE_X, MORTAR_SHARE_Y = 0.07, 0.14        # mortar share of a brick, sideways and up-down


def brick_bundle(b, vector, columns, rows):
    """The eleven layout numbers for a brick wall (about 40 nodes). Rows are counted from the BOTTOM of the picture; every second row is slid by half a brick."""
    u, v, _ = b.xyz(vector)
    v_rows = b.mul(v, float(rows))
    row_id = b.floor(v_rows)
    up = b.frac(v_rows)                                                     # 0 at the bottom of the brick row, 1 at its top
    odd = b.mod(row_id, 2.0)
    u_bricks = b.add(b.mul(u, float(columns)), b.mul(odd, 0.5))
    column_id = b.floor(u_bricks)
    across = b.frac(u_bricks)
    wide, high = 1.0 / columns, 1.0 / rows                                  # the brick pitch in tile units
    mx, my = MORTAR_SHARE_X, MORTAR_SHARE_Y
    left, right = b.mul(b.sub(across, mx / 2.0), wide), b.mul(b.sub(b.sub(1.0, across), mx / 2.0), wide)
    top, bottom = b.mul(b.sub(b.sub(1.0, up), my / 2.0), high), b.mul(b.sub(up, my / 2.0), high)
    inside = b.mn(b.mn(left, right), b.mn(top, bottom))                     # distance to the nearest edge, negative in the mortar
    on_brick = b.gt(inside, 0.0)
    wrapped_column, wrapped_row = b.mod(column_id, float(columns)), b.mod(row_id, float(rows))
    return {
        'piece_id': b.hash4(b.vec(wrapped_column, wrapped_row, 0.7), 0.3).outputs['Value'],
        'row': b.div(wrapped_row, float(rows)),
        'local_x': b.maprange(across, mx / 2.0, 1.0 - mx / 2.0, 0.0, 1.0, True),
        'local_y': b.maprange(up, 1.0 - my / 2.0, my / 2.0, 0.0, 1.0, True),          # 0 at the TOP of the brick
        'piece_width': (1.0 - mx) * wide, 'piece_height': (1.0 - my) * high,
        'edge_distance': b.mul(b.mx(inside, 0.0), on_brick),
        'top_edge_distance': b.mul(b.mx(top, 0.0), on_brick),
        'gap_mask': b.sub(1.0, on_brick), 'piece_mask': on_brick,
        'base_height': b.add(0.08, b.mul(on_brick, 0.42)),
    }


def build_node_group(parameters):
    parameters = dict(parameters or {})
    settings = dict(BRICK_SETTINGS)
    settings.update({k: v for k, v in parameters.items() if '.' in k})
    columns, rows = int(parameters.get('columns', 6)), int(parameters.get('rows', 12))
    tree, b = li.make_plain_group('BRICK reuse test', [('Vector', 'vector', (0.0, 0.0, 0.0), None, None, '')],
                                  [('Colour', 'colour', ''), ('Roughness', 'float', ''), ('Metallic', 'float', ''), ('Height', 'float', '')])
    vector = b.input('Vector')
    bundle = brick_bundle(b, vector, columns, rows)

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
    for name, node in layer_nodes.items():                                  # the declared links, exactly as in slate_recipe.py
        for link in MODULES[name].DECLARED_LINKS:
            b.tree.links.new(layer_nodes[link[4][0]].outputs[link[4][1]], node.inputs[link[0]])
    combine_node = b.node('ShaderNodeGroup')
    combine_node.node_tree = combine.build_group(settings)
    combine_node.label = 'COMBINE'
    base = bundle['base_height']
    b.tree.links.new(base, combine_node.inputs['base_height'])
    for name, node in layer_nodes.items():
        for output in li.OUTPUT_NAMES:
            b.tree.links.new(node.outputs[output], combine_node.inputs[f'{name} {output}'])
    only = parameters.get('only')
    colour = combine_node.outputs['Colour'] if not only else layer_nodes[only].outputs['Colour']
    mask_of = parameters.get('mask_of')                          # show one layer's Mask as a grey picture (the debug view of a layer on bricks)
    if mask_of:
        grey = b.grey_to_colour(layer_nodes[mask_of].outputs['Mask'])
        gamma = b.node('ShaderNodeGamma')
        b._put(gamma, 'Color', grey)
        b._put(gamma, 'Gamma', 2.2)
        colour = gamma.outputs[0]
    b.tree.links.new(colour, b.w.nodes['out'].inputs['Colour'])
    for output in ('Roughness', 'Metallic', 'Height'):
        b.tree.links.new(combine_node.outputs[output], b.w.nodes['out'].inputs[output])
    return tree
