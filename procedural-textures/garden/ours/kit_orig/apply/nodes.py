# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# A small helper for building node groups in code (the kit's own copy of the habit the earlier layers used). Net makes nodes inside one group and chains them: every helper
# returns an OUTPUT SOCKET, so a result can be passed straight on as the next input; a plain number given as an input becomes that node's own number.
#   n = Net(tree);  y = n.math('MULTIPLY', n.attr('wk_seed'), 3.0);  c = n.mix_colour(fac, colour_a, colour_b)
# new_group(name, inputs, outputs) makes an empty node group with named sockets and returns (tree, group_in, group_out).
# Habits (cookbook 06): Linear image interpolation only; no Bevel, Ambient Occlusion or Pointiness nodes (they fail or differ in EEVEE); at most about 150 nodes and three noise
# or Voronoi nodes per layer; every mix factor that carries a layer's Amount is exactly 0 at Amount 0 and cannot become NaN (NaN times 0 is NaN): clamp before you divide.
import bpy


class Net:
    def __init__(self, tree):
        self.tree = tree
        self.count = 0

    def _place(self, node):
        node.location = ((self.count % 14) * 200, -(self.count // 14) * 180)
        self.count += 1
        return node

    def _feed(self, node, index, value):
        if value is None:
            return
        if isinstance(value, bpy.types.NodeSocket):
            self.tree.links.new(value, node.inputs[index])
        else:
            node.inputs[index].default_value = value

    def new(self, idname):
        return self._place(self.tree.nodes.new(idname))

    def math(self, operation, a, b=None, c=None, clamp=False):
        node = self.new('ShaderNodeMath')
        node.operation = operation
        node.use_clamp = clamp
        for index, value in enumerate((a, b, c)):
            self._feed(node, index, value)
        return node.outputs[0]

    def map_range(self, value, from_min, from_max, to_min=0.0, to_max=1.0, smooth=False, clamp=True):
        node = self.new('ShaderNodeMapRange')
        node.data_type = 'FLOAT'
        node.interpolation_type = 'SMOOTHSTEP' if smooth else 'LINEAR'
        node.clamp = clamp
        for index, item in enumerate((value, from_min, from_max, to_min, to_max)):
            self._feed(node, index, item)
        return node.outputs[0]

    def mix(self, fac, a, b):
        node = self.new('ShaderNodeMix')
        node.data_type = 'FLOAT'
        node.clamp_factor = True
        self._feed(node, 0, fac)
        self._feed(node, 2, a)
        self._feed(node, 3, b)
        return node.outputs[0]

    def mix_colour(self, fac, a, b, blend='MIX'):
        node = self.new('ShaderNodeMix')
        node.data_type = 'RGBA'
        node.blend_type = blend
        node.clamp_factor = True
        self._feed(node, 0, fac)
        self._feed(node, 6, a)
        self._feed(node, 7, b)
        return node.outputs[2]

    def mix_vector(self, fac, a, b):
        node = self.new('ShaderNodeMix')
        node.data_type = 'VECTOR'
        node.clamp_factor = True
        self._feed(node, 0, fac)
        self._feed(node, 4, a)
        self._feed(node, 5, b)
        return node.outputs[1]

    def vector_math(self, operation, a, b=None, c=None):
        node = self.new('ShaderNodeVectorMath')
        node.operation = operation
        for index, value in enumerate((a, b, c)):
            if value is not None:
                self._feed(node, index, value)
        if operation in ('DOT_PRODUCT', 'LENGTH', 'DISTANCE'):
            return node.outputs['Value']                 # these give a number, not a vector
        return node.outputs[0]

    def combine(self, x, y, z):
        node = self.new('ShaderNodeCombineXYZ')
        for index, value in enumerate((x, y, z)):
            self._feed(node, index, value)
        return node.outputs[0]

    def separate(self, vector):
        node = self.new('ShaderNodeSeparateXYZ')
        self.tree.links.new(vector, node.inputs[0])
        return node.outputs[0], node.outputs[1], node.outputs[2]

    def noise(self, vector, scale=1.0, detail=3.0, roughness=0.5):
        node = self.new('ShaderNodeTexNoise')
        node.noise_dimensions = '3D'
        node.noise_type = 'FBM'
        node.normalize = True
        self.tree.links.new(vector, node.inputs['Vector'])
        node.inputs['Scale'].default_value = scale
        node.inputs['Detail'].default_value = detail
        node.inputs['Roughness'].default_value = roughness
        return node.outputs['Fac']

    def geometry(self):
        return self.new('ShaderNodeNewGeometry')

    def attr(self, name):
        """An OBJECT custom property by name (a number; 0 when the object has none)."""
        node = self.new('ShaderNodeAttribute')
        node.attribute_type = 'OBJECT'
        node.attribute_name = name
        return node.outputs['Fac']

    def image(self, image, vector=None, colour_space='Non-Color'):
        """An image look-up, Linear interpolation, repeating; returns the Color output. vector=None uses the active UV map."""
        node = self.new('ShaderNodeTexImage')
        node.image = image
        image.colorspace_settings.name = colour_space
        node.interpolation = 'Linear'
        node.extension = 'REPEAT'
        if vector is not None:
            self.tree.links.new(vector, node.inputs['Vector'])
        return node.outputs['Color']

    def sep_rgb(self, colour):
        node = self.new('ShaderNodeSeparateColor')
        self.tree.links.new(colour, node.inputs['Color'])
        return node.outputs['Red'], node.outputs['Green'], node.outputs['Blue']

    def comb_rgb(self, r, g, b):
        node = self.new('ShaderNodeCombineColor')
        for name, value in (('Red', r), ('Green', g), ('Blue', b)):
            if isinstance(value, bpy.types.NodeSocket):
                self.tree.links.new(value, node.inputs[name])
            else:
                node.inputs[name].default_value = value
        return node.outputs['Color']

    def clamp01(self, value):
        return self.math('MAXIMUM', 0.0, self.math('MINIMUM', 1.0, value))

    def smoothstep(self, value, edge0, edge1):
        return self.map_range(value, edge0, edge1, 0.0, 1.0, smooth=True)

    def one_minus(self, value):
        return self.math('SUBTRACT', 1.0, value)


def new_group(name, inputs, outputs):
    """An empty shader node group. inputs: [(name, socket type, default)]; outputs: [(name, socket type)]. Returns (tree, group_input_node, group_output_node).
    Socket types: 'NodeSocketFloat', 'NodeSocketColor', 'NodeSocketVector'. A group of that name is replaced only if it has no users."""
    existing = bpy.data.node_groups.get(name)
    if existing is not None:
        if existing.users == 0:
            bpy.data.node_groups.remove(existing)
        else:
            raise ValueError(f'a node group called {name!r} is already in use')
    tree = bpy.data.node_groups.new(name, 'ShaderNodeTree')
    for socket_name, kind, default in inputs:
        socket = tree.interface.new_socket(socket_name, in_out='INPUT', socket_type=kind)
        if default is not None:
            socket.default_value = default
        if kind == 'NodeSocketVector' and socket_name in ('Normal', 'Wet Normal', 'Position', 'Surface Up'):
            socket.hide_value = True
    for socket_name, kind in outputs:
        tree.interface.new_socket(socket_name, in_out='OUTPUT', socket_type=kind)
    group_in = tree.nodes.new('NodeGroupInput')
    group_out = tree.nodes.new('NodeGroupOutput')
    group_in.location = (-400, 0)
    group_out.location = (3200, 0)
    return tree, group_in, group_out


def group_or_none(name):
    return bpy.data.node_groups.get(name)
