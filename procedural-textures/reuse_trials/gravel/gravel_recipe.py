# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------
# THE GRAVEL REUSE TRIAL RECIPE: the one file the bake harness loads (lib/bake_harness.py asks for build_node_group(parameters)). It makes one
# node group "GRAVEL" with input 'Vector' (tile coordinate) and outputs 'Colour', 'Roughness', 'Metallic', 'Height'. Inside it, in the Shader editor:
#
#     a GRAVEL LAYOUT box ---- the eleven-number bundle ----+--> COLOUR AND FADE --+
#       (new: three grids of angular stones, soil between) +--> MOSS (+ Damage Mask; used as RUST) --+
#                                                           +--> DAMAGE -----------------+--> COMBINE --> Colour, Roughness, Metallic, Height
#                                                           +--> OUTLINE AND SHADOW -----+          then (optional) GRAVEL HEIGHT RULE (new) --> Height
#                                                           +--> SOIL (new), FACETS (new) -+
#
# The four paint layers and COMBINE are imported UNCHANGED from the frozen snapshot reuse_trials/shared_layers_snapshot/layers (put first on the
# search path; a check below refuses to run if any of them came from anywhere else). Only their SETTINGS differ from slate. GRAVEL LAYOUT
# (gravel_layout.py), SOIL (soil.py), FACETS (facets.py) and GRAVEL HEIGHT RULE (gravel_height_rule.py) are the new code, in this folder.
# The wiring is a copy of the brick trial's recipe, which is a copy of recipes/slate_layers/recipe/slate_recipe.py (same special parameters, so copies of
# the slate tests run here):
#     shift         [u, v]  slides the whole pattern (half-tile test only)
#     debug_view    'bundle.<name>', 'bundle.piece_colour', '<layer>.mask' / '.colour' / '.height' / '.roughness' (one thing alone)
#     settings_file another settings file instead of settings.json next to this file
# Settings: settings.json next to this file, overridden by the parameters the caller passes in. Recipe settings:
#     recipe.tiles_across  1, 2 ... base tiles across the picture (whole numbers)
#     recipe.stack_order   bottom-first layer names for COMBINE (default colour_and_fade, facets, moss, damage, outline_and_shadow, soil)
#     recipe.height_rule   'gravel' (the new GRAVEL HEIGHT RULE box after COMBINE, default) or 'combine' (COMBINE's own height)
import json
import os
import sys

sys.dont_write_bytecode = True                      # importing must not write a cache folder into the frozen snapshot
HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..'))
SNAPSHOT = os.path.join(PROC, 'reuse_trials', 'shared_layers_snapshot', 'layers')
while SNAPSHOT in sys.path:
    sys.path.remove(SNAPSHOT)
sys.path.insert(0, SNAPSHOT)                        # the shared layers come ONLY from the frozen snapshot
import layer_interface as li  # noqa: E402
import colour_and_fade  # noqa: E402
import damage  # noqa: E402
import moss  # noqa: E402
import outline_and_shadow  # noqa: E402
import combine  # noqa: E402
for _shared in (li, colour_and_fade, damage, moss, outline_and_shadow, combine):
    if os.path.dirname(os.path.abspath(_shared.__file__)) != SNAPSHOT:
        raise ImportError(f'{_shared.__name__} was not imported from the frozen snapshot but from {_shared.__file__}')
if HERE not in sys.path:
    sys.path.append(HERE)
import gravel_layout  # noqa: E402       (new: this folder)
import soil  # noqa: E402                 (new: this folder)
import facets  # noqa: E402               (new: this folder)
import gravel_height_rule as height_rule  # noqa: E402    (new: this folder)

LAYER_MODULES = {'colour_and_fade': colour_and_fade, 'damage': damage, 'moss': moss, 'outline_and_shadow': outline_and_shadow, 'soil': soil, 'facets': facets}
DEFAULT_STACK = ['colour_and_fade', 'facets', 'moss', 'damage', 'outline_and_shadow', 'soil']
SETTINGS_FILE = os.path.join(HERE, 'settings.json')
SPECIAL = ('shift', 'debug_view', 'debug_scale', 'settings_file')
DEFAULT_SCALE = {'edge_distance': 25.0, 'top_edge_distance': 8.0, 'piece_width': 3.0, 'piece_height': 8.0, 'height': 5.0, 'roughness': 2.0}


def load_settings(path=None):
    path = path or SETTINGS_FILE
    if os.path.exists(path):
        with open(path) as handle:
            return {k: v for k, v in json.load(handle).items() if not k.startswith('_')}     # keys starting with _ are notes
    return {}


def effective_settings(parameters):
    merged = load_settings(parameters.get('settings_file'))
    merged.update({k: v for k, v in parameters.items() if k not in SPECIAL})
    return merged


def build_node_group(parameters):
    parameters = dict(parameters or {})
    settings = effective_settings(parameters)
    tiles = int(settings.get('recipe.tiles_across', 1))
    settings['recipe.tiles_across'] = tiles
    stack = [n.strip() for n in str(settings.get('recipe.stack_order', ','.join(DEFAULT_STACK))).split(',') if n.strip()]
    settings['recipe.stack_order'] = ','.join(stack)
    shift = parameters.get('shift') or (0.0, 0.0)

    tree, b = li.make_plain_group('GRAVEL', [('Vector', 'vector', (0.0, 0.0, 0.0), None, None, 'the tile coordinate: x = 0..1, y = 0..1 (up)')],
                                  [('Colour', 'colour', ''), ('Roughness', 'float', ''), ('Metallic', 'float', ''), ('Height', 'float', '')])
    vector = b.input('Vector')
    if shift[0] or shift[1]:
        vector = b.vmath('ADD', vector, (float(shift[0]), float(shift[1]), 0.0))

    # ---- LAYOUT (the new gravel layout)
    layout_module = gravel_layout
    layout_node = b.node('ShaderNodeGroup')
    layout_node.node_tree = layout_module.build_group(settings)
    layout_node.label = layout_module.GROUP_NAME
    b.tree.links.new(vector, layout_node.inputs['Vector'])

    # ---- the layers (same wiring as the slate recipe)
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
    for name, node in layer_nodes.items():          # declared links (only MOSS <- DAMAGE's Mask exists)
        for link in LAYER_MODULES[name].DECLARED_LINKS:
            label, source = link[0], link[4]
            if source[0] in layer_nodes:
                b.tree.links.new(layer_nodes[source[0]].outputs[source[1]], node.inputs[label])

    # ---- COMBINE (unchanged; it makes one set of inputs per name in recipe.stack_order, so SOIL needs no change there)
    combine_node = b.node('ShaderNodeGroup')
    combine_node.node_tree = combine.build_group(settings)
    combine_node.label = 'COMBINE'
    b.tree.links.new(layout_node.outputs['base_height'], combine_node.inputs['base_height'])
    for name, node in layer_nodes.items():
        for output in li.OUTPUT_NAMES:
            b.tree.links.new(node.outputs[output], combine_node.inputs[f'{name} {output}'])
    for output in ('Colour', 'Roughness', 'Metallic', 'Height'):
        b.tree.links.new(combine_node.outputs[output], b.w.nodes['out'].inputs[output])

    # ---- GRAVEL HEIGHT RULE (new, optional): the finished height from the finished colour by the gravel reference's rule, after COMBINE
    if str(settings.get('recipe.height_rule', 'gravel')) == 'gravel':
        rule_node = b.node('ShaderNodeGroup')
        rule_node.node_tree = height_rule.build_group(settings)
        rule_node.label = height_rule.GROUP_NAME
        b.tree.links.new(combine_node.outputs['Colour'], rule_node.inputs['Colour'])
        b.tree.links.new(combine_node.outputs['Height'], rule_node.inputs['Height'])
        b.tree.links.new(rule_node.outputs['Height'], b.w.nodes['out'].inputs['Height'])

    view = parameters.get('debug_view')
    if view and view != 'none':
        _debug_view(b, view, parameters.get('debug_scale'), layout_node, layer_nodes)
    return tree


def _debug_view(b, view, scale, layout_node, layer_nodes):
    """Show ONE thing instead of the finished colour: numbers as grey in Colour and exactly in Height (copied from the slate recipe through the brick trial)."""
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
        b._put(gamma, 'Gamma', 2.2)
        colour = gamma.outputs[0]
    b.tree.links.new(colour, b.w.nodes['out'].inputs['Colour'])
    b.tree.links.new(value, b.w.nodes['out'].inputs['Height'])
