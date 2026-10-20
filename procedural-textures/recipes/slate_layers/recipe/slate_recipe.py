# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------
# This is THE SLATE RECIPE: the one file the bake harness loads (lib/bake_harness.py asks for build_node_group(parameters)). It makes one
# Blender node group called "SLATE" whose input is 'Vector' (the tile coordinate, 0..1 in both directions) and whose outputs are
# 'Colour', 'Roughness', 'Metallic', 'Height' (what the harness photographs). Inside it you see, in the Shader editor, these boxes:
#
#     LAYOUT ------------------------------------------------------------- the slates: rows, widths, joints, chipped edges
#       |  (the eleven-number "layout bundle": piece_id, row, local_x, local_y, piece_width, piece_height,
#       |   edge_distance, top_edge_distance, gap_mask, piece_mask, base_height)
#       +--> COLOUR AND FADE ---+
#       +--> MOSS (also reads DAMAGE's Mask: declared link)
#       +--> DAMAGE  -----------+--> COMBINE --> Colour, Roughness, Metallic, Height
#       +--> OUTLINE AND SHADOW +
#
# Settings: a flat list of numbers and words in settings.json next to this file, named 'layer.control' (for example 'moss.amount').
# Order of strength: the default written in each layer's own file  <  settings.json  <  the parameters the caller passes in
# (for example the harness option --params '{"moss.amount": 0.5}'). Special parameters (not settings):
#     shift          [u, v]  slides the whole pattern by that much of the picture; used only by the half-tile-shift test.
#     debug_view     shows one thing instead of the finished colour, so a layer can be baked ALONE:
#                      'bundle.<name>'            any of the eleven layout numbers, e.g. 'bundle.edge_distance'
#                      'bundle.piece_colour'      a random colour per slate (shows what piece_id is)
#                      '<layer>.mask' / '.colour' / '.height' / '.roughness'   one layer's output, e.g. 'damage.mask'
#                    A number is shown as grey in the Colour output AND exactly (16 bit) in the Height output; debug_scale (default
#                    depends on the quantity) stretches it.
#     settings_file  another settings file to use instead of settings.json.
# Settings of the recipe itself:
#     recipe.tiles_across  1, 2, 4 ...  how many base tiles fit across the picture. 1 = one tile that repeats exactly. 2 = a 2 x 2 area
#                          of NEW, non-repeating content with the same look per dot (bake 2 x 1254 dots). Whole numbers only.
#     recipe.stack_order   bottom-first layer names for COMBINE, separated by commas.
#
# Layers are connected ONLY through the layout bundle and through the declared links each layer file lists in DECLARED_LINKS.
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LAYERS = os.path.abspath(os.path.join(HERE, '..', 'layers'))
if LAYERS not in sys.path:
    sys.path.insert(0, LAYERS)
import layer_interface as li  # noqa: E402
import layout  # noqa: E402
import colour_and_fade  # noqa: E402
import damage  # noqa: E402
import moss  # noqa: E402
import outline_and_shadow  # noqa: E402
import combine  # noqa: E402

LAYER_MODULES = {'colour_and_fade': colour_and_fade, 'damage': damage, 'moss': moss, 'outline_and_shadow': outline_and_shadow}
SETTINGS_FILE = os.path.join(HERE, 'settings.json')
DEFAULT_SCALE = {'edge_distance': 25.0, 'top_edge_distance': 8.0, 'piece_width': 5.0, 'piece_height': 8.0, 'height': 5.0, 'roughness': 2.0}


def load_settings(path=None):
    """The settings.json dict (empty if the file is missing)."""
    path = path or SETTINGS_FILE
    if os.path.exists(path):
        with open(path) as handle:
            return json.load(handle)
    return {}


def effective_settings(parameters):
    """settings.json overridden by the caller's parameters."""
    merged = load_settings(parameters.get('settings_file'))
    merged.update({k: v for k, v in parameters.items() if k not in ('shift', 'debug_view', 'debug_scale', 'settings_file')})
    return merged


def _check_no_cycles(links):
    """links: {layer: set of layers it reads from}. Raises if layers read from each other in a circle."""
    done, active = set(), set()

    def visit(name):
        if name in done:
            return
        if name in active:
            raise ValueError(f'declared links form a circle through {name!r}')
        active.add(name)
        for source in links.get(name, ()):
            visit(source)
        active.discard(name)
        done.add(name)
    for name in links:
        visit(name)


def build_node_group(parameters):
    parameters = dict(parameters or {})
    settings = effective_settings(parameters)
    tiles = int(settings.get('recipe.tiles_across', 1))
    settings['recipe.tiles_across'] = tiles
    stack = [n.strip() for n in str(settings.get('recipe.stack_order', ','.join(combine.DEFAULT_STACK))).split(',') if n.strip()]
    shift = parameters.get('shift') or (0.0, 0.0)

    tree, b = li.make_plain_group('SLATE', [('Vector', 'vector', (0.0, 0.0, 0.0), None, None, 'the tile coordinate: x = 0..1, y = 0..1 (up)')],
                                  [('Colour', 'colour', ''), ('Roughness', 'float', ''), ('Metallic', 'float', ''), ('Height', 'float', '')])
    vector = b.input('Vector')
    if shift[0] or shift[1]:
        vector = b.vmath('ADD', vector, (float(shift[0]), float(shift[1]), 0.0))

    # ---- LAYOUT
    layout_node = b.node('ShaderNodeGroup')
    layout_node.node_tree = layout.build_group(settings)
    layout_node.label = 'LAYOUT'
    b.tree.links.new(vector, layout_node.inputs['Vector'])

    # ---- the layers
    layer_nodes = {}
    for name in stack:
        module = LAYER_MODULES[name]
        node = b.node('ShaderNodeGroup')
        node.node_tree = module.build_group(settings)
        node.label = module.GROUP_NAME
        layer_nodes[name] = node
        b.tree.links.new(vector, node.inputs['Vector'])
        node.inputs['Tile Count'].default_value = float(tiles)
        for bundle_name in li.BUNDLE_NAMES:
            b.tree.links.new(layout_node.outputs[bundle_name], node.inputs[bundle_name])
    # ---- declared links between layers (only those written in the layer files)
    dependencies = {name: set() for name in layer_nodes}
    for name, node in layer_nodes.items():
        for link in LAYER_MODULES[name].DECLARED_LINKS:
            label, source = link[0], link[4]
            if source[0] not in layer_nodes:
                continue                                  # the source layer is not in this stack: the socket keeps its default
            dependencies[name].add(source[0])
            b.tree.links.new(layer_nodes[source[0]].outputs[source[1]], node.inputs[label])
    _check_no_cycles(dependencies)

    # ---- COMBINE
    combine_node = b.node('ShaderNodeGroup')
    combine_node.node_tree = combine.build_group(settings)
    combine_node.label = 'COMBINE'
    b.tree.links.new(layout_node.outputs['base_height'], combine_node.inputs['base_height'])
    for name, node in layer_nodes.items():
        for output in li.OUTPUT_NAMES:
            b.tree.links.new(node.outputs[output], combine_node.inputs[f'{name} {output}'])
    for output in ('Colour', 'Roughness', 'Metallic', 'Height'):
        b.tree.links.new(combine_node.outputs[output], b.w.nodes['out'].inputs[output])

    view = parameters.get('debug_view')
    if view and view != 'none':
        _debug_view(b, view, parameters.get('debug_scale'), layout_node, layer_nodes)
    return tree


def _debug_view(b, view, scale, layout_node, layer_nodes):
    """Replace the Colour output (and Height) so that ONE thing is shown. Numbers go to Colour as grey and exactly to Height."""
    group, _, what = view.partition('.')
    colour, value, offset = None, None, 0.0
    if group == 'bundle':
        if what == 'piece_colour':
            colour = b.hash4(b.vec(layout_node.outputs['piece_id'], 0.5, 0.5), 2.5).outputs['Color']
            value = layout_node.outputs['piece_id']
        elif what == 'joints':
            colour = b.mix((0.02, 0.02, 0.025, 1.0), (0.25, 0.28, 0.30, 1.0), layout_node.outputs['piece_mask'])
            value = layout_node.outputs['piece_mask']
        else:
            value = layout_node.outputs[what]
            scale = scale or DEFAULT_SCALE.get(what, 1.0)
    else:
        node = layer_nodes[group]
        if what == 'colour':
            colour = node.outputs['Colour']
            value = b.brightness(colour)
        elif what == 'mask':
            value = node.outputs['Mask']
        elif what in ('height', 'roughness'):
            offset = 0.5
            scale = scale or DEFAULT_SCALE[what]
            value = node.outputs[what.capitalize()]
        else:
            raise KeyError(f'unknown debug view {view!r}')
    if scale and scale != 1.0:
        value = b.mul(value, float(scale))
    if offset:
        value = b.add(value, offset)
    if colour is None:
        grey = b.grey_to_colour(value)
        gamma = b.node('ShaderNodeGamma')
        b._put(gamma, 'Color', grey)
        b._put(gamma, 'Gamma', 2.2)                      # so that the picture shows the number itself (the harness writes sRGB)
        colour = gamma.outputs[0]
    b.tree.links.new(colour, b.w.nodes['out'].inputs['Colour'])
    b.tree.links.new(value, b.w.nodes['out'].inputs['Height'])
