# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------
# The slate recipe is made of separate parts ("layers"): LAYOUT, COLOUR AND FADE, DAMAGE, MOSS, OUTLINE AND SHADOW and COMBINE. Every
# layer is a Blender "node group": a small box in the Shader editor with named sockets on the left (inputs) and the right (outputs).
# For the parts to fit together, every layer must have the SAME sockets. This file is the one place that says which sockets those are
# and builds the empty box for a layer, so each layer's own file only has to say what happens INSIDE the box.
#
# What a layer group looks like from outside (the "fixed interface"; it is written out in plain words in ../interface/interface.md):
#   inputs : Vector, Tile Count, the eleven LAYOUT BUNDLE sockets (piece_id, row, local_x, local_y, piece_width, piece_height,
#            edge_distance, top_edge_distance, gap_mask, piece_mask, base_height), Seed, Amount, then the layer's own controls,
#            then (only if the layer declares any) the DECLARED LINKS from other layers.
#   outputs: Mask (0..1: where the layer paints), Colour (what it paints), Height (a small change of the surface height, 0 = no change),
#            Roughness (a change of roughness, 0 = no change).
#
# What is in this file
#   Control            one setting of a layer: its name, its socket label, default, range and a plain sentence.
#   resolve()          reads a layer's settings: the default written in the layer's file, overridden by the recipe's settings.
#   make_layer_group() makes the empty layer box with the fixed sockets and returns a LayerBuilder to put nodes inside it.
#   make_plain_group() the same for a box with its own sockets (used by LAYOUT and COMBINE).
#   LayerBuilder       "write nodes like a list of sums": b.add(a, b), b.mul(...), b.maprange(...), b.tileable_noise(...), b.hash4(...).
#                      It sits on top of lib/contrib/builder.py (copied idea, not edited).
# Use (inside Blender):  import layer_interface as li
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = 'proc-work'
for folder in (os.path.join(PROC, 'lib'), os.path.join(PROC, 'lib', 'contrib')):
    if folder not in sys.path:
        sys.path.insert(0, folder)
import recipe_tools as rt  # noqa: E402
import builder as bd  # noqa: E402

# ------------------------------------------------------------------------------------------------------------------------------
# The fixed names. Layer builders may rely on these exact spellings.
BUNDLE_NAMES = ['piece_id', 'row', 'local_x', 'local_y', 'piece_width', 'piece_height', 'edge_distance', 'top_edge_distance',
                'gap_mask', 'piece_mask', 'base_height']
BUNDLE_TEXT = {
    'piece_id': 'a random number 0..1, the same for every dot of one slate, different for each slate',
    'row': 'which row the slate is in, as row number / number of rows (0..1)',
    'local_x': '0..1 from the left edge of the slate to its right edge',
    'local_y': '0..1 from the top edge of the slate down to its bottom edge (0 = top)',
    'piece_width': 'width of this slate in tile units (the same for every dot of the slate)',
    'piece_height': 'height of this slate in tile units (the same for every dot of the slate)',
    'edge_distance': 'distance from the nearest slate edge, in tile units (0 at the edge and in the joint, grows inwards)',
    'top_edge_distance': 'distance below the slate\'s upper edge, in tile units (0 at the top edge)',
    'gap_mask': '1 in the dark joint between slates, 0 on the slate (soft over about half a dot at the edge)',
    'piece_mask': '1 on the slate, 0 in the joint (= 1 - gap_mask)',
    'base_height': 'the relief of the bare slates before any layer adds to it (0..1; joints low, slates high, bevelled edges)',
}
OUTPUT_NAMES = ['Mask', 'Colour', 'Height', 'Roughness']
OUTPUT_TEXT = {
    'Mask': 'where the layer paints (0..1)',
    'Colour': 'the colour the layer paints where its Mask is 1',
    'Height': 'the change the layer makes to the surface height (0 = no change; small plus and minus numbers)',
    'Roughness': 'the change the layer makes to roughness (0 = no change; minus = smoother, plus = rougher)',
}


class Control:
    """One setting of one layer. key = the name in settings.json after the 'layer.' prefix; label = the socket name shown in
    Blender; default/low/high = number (or a '#rrggbb' text for kind='colour'); text = one plain sentence; build_time = True for a
    setting that changes how many nodes the layer has (it is read while building, it is not a socket)."""

    def __init__(self, key, label, default, low=None, high=None, text='', kind='float', build_time=False):
        self.key, self.label, self.default, self.low, self.high = key, label, default, low, high
        self.text, self.kind, self.build_time = text, kind, build_time


def setting_name(layer_key, key):
    return f'{layer_key}.{key}'


def resolve(layer_key, controls, parameters):
    """{key: value} for every control: the setting 'layer.key' if the recipe's settings hold it, else the default in the layer file."""
    return {c.key: parameters.get(setting_name(layer_key, c.key), c.default) for c in controls}


COMMON_CONTROLS_TEXT = {
    'seed': 'the layer\'s own random seed: change it and ONLY this layer\'s pattern changes',
    'amount': 'overall strength of the layer: 0 switches the layer off (Mask, Height and Roughness all become 0)',
}


def common_controls(default_seed):
    return [Control('seed', 'Seed', float(default_seed), 0.0, 1000.0, COMMON_CONTROLS_TEXT['seed']),
            Control('amount', 'Amount', 1.0, 0.0, 1.0, COMMON_CONTROLS_TEXT['amount'])]


def unique_name(name):
    """A node group name that does not clash with an earlier build in the same Blender session."""
    if name not in bpy.data.node_groups:
        return name
    count = 1
    while f'{name}.{count:03d}' in bpy.data.node_groups:
        count += 1
    return f'{name}.{count:03d}'


def _make_tree(name, inputs, outputs):
    """inputs: list of (label, kind, default, low, high, text) ; outputs: list of (label, kind, text). kind: 'float', 'vector', 'colour'."""
    tree = bpy.data.node_groups.new(unique_name(name), 'ShaderNodeTree')
    kinds = {'float': 'NodeSocketFloat', 'vector': 'NodeSocketVector', 'colour': 'NodeSocketColor'}
    for label, kind, default, low, high, text in inputs:
        socket = tree.interface.new_socket(label, in_out='INPUT', socket_type=kinds[kind])
        if text:
            socket.description = text
        if kind == 'float':
            if low is not None:
                socket.min_value = low
            if high is not None:
                socket.max_value = high
            socket.default_value = float(default)
        elif kind == 'colour':
            socket.default_value = rt.srgb_hex_to_linear(default) if isinstance(default, str) else tuple(default)
        elif default is not None:
            socket.default_value = default
    for label, kind, text in outputs:
        socket = tree.interface.new_socket(label, in_out='OUTPUT', socket_type=kinds[kind])
        if text:
            socket.description = text
    writer = rt.NodeWriter(tree)
    writer.nodes['in'] = tree.nodes.new('NodeGroupInput')
    writer.nodes['in'].location = (-1400, 0)
    writer.nodes['out'] = tree.nodes.new('NodeGroupOutput')
    writer.nodes['out'].location = (4200, 0)
    return tree, writer


class LayerBuilder(bd.Builder):
    """lib/contrib/builder.py's Builder (add, mul, maprange, ramp, mix ...), but working inside a node group that already exists."""

    def __init__(self, tree, writer):          # not calling Builder.__init__: it would make its own group
        self.tree, self.w = tree, writer
        self.count = 0
        self._uv = None
        self.shift = (0.0, 0.0)

    # ---- reading the group's own sockets
    def input(self, label):
        """The output of the group-input box for the socket called `label` (use it like any number)."""
        return self.w.nodes['in'].outputs[label]

    def bundle(self):
        """dict name -> socket for the eleven layout bundle inputs."""
        return {name: self.input(name) for name in BUNDLE_NAMES}

    def output(self, label, value):
        """Put a number or a node output on the group's output socket `label`."""
        self._put_out(self.w.nodes['out'], label, value)

    def label_last(self, text):
        """Give the node made last a readable name in the Shader editor."""
        last = list(self.tree.nodes)[-1]
        last.label = text
        return last

    # ---- random numbers and seamless noise
    def hash4(self, vector, w=0.0):
        """White Noise in 4D: the same inputs always give the same random numbers. Outputs 'Value' (one number 0..1) and 'Color' (three)."""
        node = self.node('ShaderNodeTexWhiteNoise', noise_dimensions='4D')
        self._put(node, 'Vector', vector)
        self._put(node, 'W', w)
        return node

    def gauss_like(self, colour_socket):
        """A number with mean 0 and spread 1 made from the three random numbers of a hash colour (sum of three, bell-shaped)."""
        red, green, blue = self.channels(colour_socket)
        return self.mul(self.sub(self.add(self.add(red, green), blue), 1.5), 2.0)

    def tileable_noise(self, vector, scale, detail=3.0, roughness=0.5, seed=0.0, distortion=0.0, lacunarity=2.0):
        """Seamless noise from lib/recipe_tools.tileable_noise_group (one box in the editor). vector = the 0..1 tile coordinate,
        scale = how many noise features fit across the WHOLE picture (use features_per_tile * Tile Count). Returns Fac (about 0.3..0.7)."""
        node = self.node('ShaderNodeGroup')
        node.node_tree = rt.tileable_noise_group()
        node.label = 'seamless noise'
        self._put(node, 'Vector', vector)
        self._put(node, 'Scale', scale)
        self._put(node, 'Detail', detail)
        self._put(node, 'Roughness', roughness)
        self._put(node, 'Lacunarity', lacunarity)
        self._put(node, 'Distortion', distortion)
        self._put(node, 'Seed', seed)
        return node.outputs['Fac']

    def noise01(self, vector, scale, detail=3.0, roughness=0.5, seed=0.0, distortion=0.0, low=0.3, high=0.7):
        """tileable_noise stretched so the usual 0.3..0.7 range becomes 0..1 (clamped)."""
        fac = self.tileable_noise(vector, scale, detail, roughness, seed, distortion)
        return self.maprange(fac, low, high, 0.0, 1.0, True)

    def sqrt(self, a):
        return self.math('SQRT', a)

    def exp(self, a):
        return self.math('EXPONENT', a)

    def power(self, a, b):
        return self.math('POWER', a, b)

    def smoothstep(self, value, low, high):
        return self.maprange(value, low, high, 0.0, 1.0, True, 'SMOOTHSTEP')

    def sum_of(self, sockets):
        total = sockets[0]
        for item in sockets[1:]:
            total = self.add(total, item)
        return total

    def finish_layer(self, mask, colour, height, roughness, apply_amount=True):
        """Connect the four outputs. The off-switch is guaranteed here: with Amount = 0, Mask, Height and Roughness are all 0.
        With apply_amount True (the default) they are also scaled by Amount (0..1). A layer that uses Amount in a smarter way
        (for example as 'how much of the slate is covered') passes apply_amount=False and still gets the off-switch."""
        amount = self.input('Amount')
        switch = self.gt(amount, 0.0)
        factor = self.mul(switch, self.mn(amount, 1.0)) if apply_amount else switch
        self.output('Mask', self.mul(mask, factor))
        self.output('Colour', colour)
        self.output('Height', self.mul(height, factor))
        self.output('Roughness', self.mul(roughness, factor))


def make_plain_group(group_name, inputs, outputs):
    """A node group with its own sockets (LAYOUT and COMBINE use this). Returns (tree, LayerBuilder)."""
    tree, writer = _make_tree(group_name, inputs, outputs)
    return tree, LayerBuilder(tree, writer)


def make_layer_group(group_name, layer_key, controls, parameters, default_seed, declared_links=()):
    """The empty box of a layer with the fixed interface.
    controls: the layer's own Control list (NOT including Seed and Amount, which every layer has).
    declared_links: list of (label, kind, default, text) for inputs that come from OTHER layers (for example MOSS reads 'Damage Mask').
    Returns (tree, LayerBuilder). The settings are read here: the socket defaults come from resolve()."""
    values = resolve(layer_key, common_controls(default_seed) + list(controls), parameters)
    inputs = [('Vector', 'vector', (0.0, 0.0, 0.0), None, None, 'the tile coordinate: x = 0..1 left to right, y = 0..1 BOTTOM to top of the picture'),
              ('Tile Count', 'float', 1.0, 1.0, 64.0, 'how many base tiles fit across the picture (1 = one tile; 2 = a 2 x 2 area of new content)')]
    for name in BUNDLE_NAMES:
        inputs.append((name, 'float', 0.0, None, None, 'layout bundle: ' + BUNDLE_TEXT[name]))
    for control in common_controls(default_seed) + list(controls):
        if control.build_time:
            continue
        inputs.append((control.label, control.kind, values[control.key], control.low, control.high, control.text))
    for link in declared_links:
        label, kind, default, text = link[:4]          # (a 5th entry, the source layer and output, is only read by the recipe)
        inputs.append((label, kind, default, None, None, 'declared link from another layer: ' + text))
    outputs = [(name, 'colour' if name == 'Colour' else 'float', OUTPUT_TEXT[name]) for name in OUTPUT_NAMES]
    tree, writer = _make_tree(group_name, inputs, outputs)
    return tree, LayerBuilder(tree, writer)


def controls_table_rows(layer_key, controls, with_common=True, default_seed=0):
    """Rows (setting name, socket label, default, low, high, text) for the one-page controls table."""
    rows = []
    for control in (common_controls(default_seed) if with_common else []) + list(controls):
        rows.append((setting_name(layer_key, control.key), control.label, control.default, control.low, control.high, control.text,
                     'build' if control.build_time else 'socket'))
    return rows
