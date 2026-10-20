# What this does: small helpers for writing Blender shader-node recipes in Python, so a recipe reads like a list of
# steps instead of a pile of socket plumbing. It gives you (1) NodeWriter: add a node with its settings and inputs in one
# line and link nodes by name, (2) make_group_tree: make a reusable node group with named inputs and outputs, and (3) ready-made
# SEAMLESS building blocks: tileable_noise_group and tileable_voronoi_group (Blender's own noise is not seamless; these
# sample a 4-dimensional noise on a donut shape so the left edge continues into the right edge and the top into the bottom).
# Use: import recipe_tools as rt   (inside Blender)
import math

import bpy


class NodeWriter:
    """Adds and links nodes in one node tree. Nodes are remembered by the short name you give them."""

    def __init__(self, tree):
        self.tree = tree
        self.nodes = {}
        self._column = 0

    def add(self, kind, name, x=None, y=0, **settings):
        """kind: a node type such as 'ShaderNodeTexNoise'. settings: node settings (like noise_dimensions='4D') and input
        values (like Scale=5.0 or Color=(1, 0, 0, 1)) in one go. Names with spaces: use double underscore (Detail, Distortion
        are fine; 'Base Color' becomes Base__Color)."""
        node = self.tree.nodes.new(kind)
        node.name = name
        node.label = name
        node.location = (self._column * 220 if x is None else x * 220, y * 160)
        self._column += 1 if x is None else 0
        for key, value in settings.items():
            self.set(node, key, value)
        self.nodes[name] = node
        return node

    def set(self, node, key, value):
        pretty = key.replace('__', ' ')
        if key in node.bl_rna.properties and key not in ('name', 'label', 'location'):
            setattr(node, key, value)
        elif pretty in node.inputs:
            node.inputs[pretty].default_value = value
        else:
            raise KeyError(f'{node.bl_idname} has neither a setting nor an input called {key!r}; inputs are {[s.name for s in node.inputs]}')

    def link(self, from_name, from_socket, to_name, to_socket):
        """Link output socket (name or index) of one remembered node to an input socket of another."""
        source = self.nodes[from_name] if isinstance(from_name, str) else from_name
        target = self.nodes[to_name] if isinstance(to_name, str) else to_name
        out_socket = source.outputs[from_socket]
        in_socket = target.inputs[to_socket]
        self.tree.links.new(out_socket, in_socket)

    def math(self, name, operation, a=None, b=None, c=None, clamp=False, x=None, y=0):
        node = self.add('ShaderNodeMath', name, x=x, y=y, operation=operation, use_clamp=clamp)
        for index, value in enumerate((a, b, c)):
            if value is not None:
                node.inputs[index].default_value = value
        return node

    def vector_math(self, name, operation, x=None, y=0, **values):
        node = self.add('ShaderNodeVectorMath', name, x=x, y=y, operation=operation)
        for key, value in values.items():
            node.inputs[key.replace('__', ' ')].default_value = value
        return node


def make_group_tree(name, inputs, outputs):
    """A new shader node group. inputs: list of (name, socket_type, default) with socket_type 'NodeSocketFloat',
    'NodeSocketVector', 'NodeSocketColor' or 'NodeSocketInt'; outputs: list of (name, socket_type).
    Returns (tree, writer); the writer already knows 'Group Input' and 'Group Output' as 'in' and 'out'."""
    tree = bpy.data.node_groups.new(name, 'ShaderNodeTree')
    for socket_name, socket_type, default in inputs:
        socket = tree.interface.new_socket(socket_name, in_out='INPUT', socket_type=socket_type)
        if default is not None:
            socket.default_value = default
    for socket_name, socket_type in outputs:
        tree.interface.new_socket(socket_name, in_out='OUTPUT', socket_type=socket_type)
    writer = NodeWriter(tree)
    writer.nodes['in'] = tree.nodes.new('NodeGroupInput')
    writer.nodes['in'].location = (-900, 0)
    writer.nodes['out'] = tree.nodes.new('NodeGroupOutput')
    writer.nodes['out'].location = (1800, 0)
    return tree, writer


# ----------------------------------------------------------------------------------------------------- seamless blocks
def _donut_coordinates(writer, source_node, source_socket):
    """Turn a flat (u, v) tile coordinate into 4 numbers that go round in circles, so anything built from them repeats
    exactly every 1.0 in u and in v. Returns (name_of_vector_node, name_of_w_math_node)."""
    writer.add('ShaderNodeSeparateXYZ', 'split uv', x=-3, y=0)
    writer.link(source_node, source_socket, 'split uv', 'Vector')
    for axis, label in (('X', 'u'), ('Y', 'v')):
        writer.math(f'turns {label}', 'MULTIPLY', None, 2 * math.pi, x=-2, y=0 if label == 'u' else -2)
        writer.link('split uv', axis, f'turns {label}', 0)
        writer.math(f'cos {label}', 'COSINE', x=-1, y=1 if label == 'u' else -1)
        writer.link(f'turns {label}', 0, f'cos {label}', 0)
        writer.math(f'sin {label}', 'SINE', x=-1, y=0 if label == 'u' else -2)
        writer.link(f'turns {label}', 0, f'sin {label}', 0)
    writer.add('ShaderNodeCombineXYZ', 'donut xyz', x=0, y=0)
    writer.link('cos u', 0, 'donut xyz', 'X')
    writer.link('sin u', 0, 'donut xyz', 'Y')
    writer.link('cos v', 0, 'donut xyz', 'Z')
    return 'donut xyz', 'sin v'


def tileable_noise_group(name='Tileable Noise'):
    """Seamless fractal noise. Inputs: Vector (the tile coordinate, 0..1), Scale (how many noise features fit across one tile),
    Detail, Roughness, Lacunarity, Distortion, Seed (any number; changes the pattern). Outputs: Fac (0..1 grey), Color."""
    existing = bpy.data.node_groups.get(name)
    if existing:
        return existing
    tree, w = make_group_tree(name, [
        ('Vector', 'NodeSocketVector', (0, 0, 0)), ('Scale', 'NodeSocketFloat', 4.0), ('Detail', 'NodeSocketFloat', 4.0),
        ('Roughness', 'NodeSocketFloat', 0.5), ('Lacunarity', 'NodeSocketFloat', 2.0), ('Distortion', 'NodeSocketFloat', 0.0),
        ('Seed', 'NodeSocketFloat', 0.0)], [('Fac', 'NodeSocketFloat'), ('Color', 'NodeSocketColor')])
    donut, sin_v = _donut_coordinates(w, 'in', 'Vector')
    # radius so that one trip round the donut is one tile long, scaled by the requested number of features per tile
    w.math('radius', 'DIVIDE', None, 2 * math.pi, x=-2, y=3)
    w.link('in', 'Scale', 'radius', 0)
    w.vector_math('scaled xyz', 'SCALE', x=1, y=0)
    w.link(donut, 0, 'scaled xyz', 0)
    w.link('radius', 0, 'scaled xyz', 'Scale')
    w.math('scaled w', 'MULTIPLY', x=1, y=-2)
    w.link(sin_v, 0, 'scaled w', 0)
    w.link('radius', 0, 'scaled w', 1)
    w.math('seed w', 'ADD', x=2, y=-2)
    w.link('scaled w', 0, 'seed w', 0)
    w.link('in', 'Seed', 'seed w', 1)
    w.add('ShaderNodeTexNoise', 'noise', x=3, y=0, noise_dimensions='4D', noise_type='FBM', normalize=True, Scale=1.0)
    w.link('scaled xyz', 0, 'noise', 'Vector')
    w.link('seed w', 0, 'noise', 'W')
    for socket in ('Detail', 'Roughness', 'Lacunarity', 'Distortion'):
        w.link('in', socket, 'noise', socket)
    w.link('noise', 'Fac', 'out', 'Fac')
    w.link('noise', 'Color', 'out', 'Color')
    return tree


def tileable_voronoi_group(name='Tileable Voronoi'):
    """Seamless cell pattern (stones, cracks, cells). Inputs: Vector (tile coordinate 0..1), Scale (cells across one tile),
    Randomness (0 = regular grid of cells, 1 = fully random), Seed. Outputs: Distance (to the nearest cell centre),
    Color (random colour per cell), Position (4D position of the nearest centre, as a vector)."""
    existing = bpy.data.node_groups.get(name)
    if existing:
        return existing
    tree, w = make_group_tree(name, [
        ('Vector', 'NodeSocketVector', (0, 0, 0)), ('Scale', 'NodeSocketFloat', 6.0), ('Randomness', 'NodeSocketFloat', 1.0),
        ('Seed', 'NodeSocketFloat', 0.0)], [('Distance', 'NodeSocketFloat'), ('Color', 'NodeSocketColor'), ('Position', 'NodeSocketVector')])
    donut, sin_v = _donut_coordinates(w, 'in', 'Vector')
    w.math('radius', 'DIVIDE', None, 2 * math.pi, x=-2, y=3)
    w.link('in', 'Scale', 'radius', 0)
    w.vector_math('scaled xyz', 'SCALE', x=1, y=0)
    w.link(donut, 0, 'scaled xyz', 0)
    w.link('radius', 0, 'scaled xyz', 'Scale')
    w.math('scaled w', 'MULTIPLY', x=1, y=-2)
    w.link(sin_v, 0, 'scaled w', 0)
    w.link('radius', 0, 'scaled w', 1)
    w.math('seed w', 'ADD', x=2, y=-2)
    w.link('scaled w', 0, 'seed w', 0)
    w.link('in', 'Seed', 'seed w', 1)
    w.add('ShaderNodeTexVoronoi', 'voronoi', x=3, y=0, voronoi_dimensions='4D', feature='F1', distance='EUCLIDEAN', Scale=1.0)
    w.link('scaled xyz', 0, 'voronoi', 'Vector')
    w.link('seed w', 0, 'voronoi', 'W')
    w.link('in', 'Randomness', 'voronoi', 'Randomness')
    w.link('voronoi', 'Distance', 'out', 'Distance')
    w.link('voronoi', 'Color', 'out', 'Color')
    w.link('voronoi', 'Position', 'out', 'Position')
    return tree


def srgb_hex_to_linear(hex_text, alpha=1.0):
    """A colour typed as a web hex code ('#c0502a') as the linear (r, g, b, a) Blender wants in a colour input or a Color Ramp stop.
    Blender's colour inputs are linear; hex codes and picture pixels are sRGB. Typing the raw numbers makes everything about 73/255 too bright."""
    text = hex_text.lstrip('#')
    channels = [int(text[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return (linear[0], linear[1], linear[2], alpha)
