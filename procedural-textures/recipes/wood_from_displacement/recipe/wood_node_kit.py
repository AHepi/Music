# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------
# A small helper for the wood-from-maps recipe. It lets the recipe write its arithmetic as ordinary Python sums, for example
#       board_number = floor(x / board_length)
# and quietly builds the matching Blender shader nodes (Math, Separate/Combine, White Noise, Noise, Image Texture, Color Ramp).
# Every number in the recipe is an object of class S that remembers which node output it comes from. Plain Python numbers that
# are mixed in are folded away (they become settings of the nodes, or disappear when two plain numbers meet).
#
# Two things this helper adds on top of the research version (research/tests/nodekit.py):
#   * FRAMES: kit.begin('1 ROWS') starts a labelled frame; every node made until the next begin() sits inside it, so a person who opens the
#     recipe in the Shader editor sees titled boxes (rows, boards, window, joints, stains, masks, colour, height) instead of one big heap.
#   * TABLES: kit.table(index, [[...], [...]]) is a small look-up table made from ONE Color Ramp node (constant steps), up to 4 columns
#     (red, green, blue, alpha). This replaces long chains of compare-and-mix nodes. Values are stored divided by a scale so they stay
#     between 0 and 1.
# Words: a "dot" is one dot of the 1254 x 1254 source picture (one pixel); a "socket" is a plug on a node.
# Use (inside Blender):  import wood_node_kit as nk ; kit = nk.Kit(group_tree) ; a = kit.floor(x / 5.0) ; ...
import math

import bpy


class S:
    """One number inside the node tree (an output socket) with Python arithmetic."""
    __slots__ = ('k', 'sock')

    def __init__(self, kit, sock):
        self.k, self.sock = kit, sock

    def _bin(self, op, other, swap=False):
        a, b = (other, self) if swap else (self, other)
        return self.k.math(op, a, b)

    def __add__(self, o): return self._bin('ADD', o)
    def __radd__(self, o): return self._bin('ADD', o, True)
    def __sub__(self, o): return self._bin('SUBTRACT', o)
    def __rsub__(self, o): return self._bin('SUBTRACT', o, True)
    def __mul__(self, o): return self._bin('MULTIPLY', o)
    def __rmul__(self, o): return self._bin('MULTIPLY', o, True)
    def __truediv__(self, o): return self._bin('DIVIDE', o)
    def __rtruediv__(self, o): return self._bin('DIVIDE', o, True)
    def __mod__(self, o): return self._bin('FLOORED_MODULO', o)
    def __neg__(self): return self.k.math('MULTIPLY', self, -1.0)
    def __lt__(self, o): return self._bin('LESS_THAN', o)
    def __gt__(self, o): return self._bin('GREATER_THAN', o)


def _isnum(x):
    return isinstance(x, (int, float))


class Kit:
    def __init__(self, tree):
        self.tree = tree
        self.count = 0
        self.images = {}
        self.frame = None
        self.frame_row = 0
        self.frame_y = 0.0
        self.frames = []
        self._in_frame = 0
        self._pending_frame_height = 0

    # ---------------------------------------------------------------- frames and nodes
    def begin(self, title):
        """Start a new labelled frame; every node made after this sits inside it (until the next begin())."""
        self._close_frame()
        frame = self.tree.nodes.new('NodeFrame')
        frame.label = title
        frame.label_size = 30
        frame.use_custom_color = True
        frame.color = (0.15, 0.22, 0.30)
        frame.location = (0, 0)
        self.frame = frame
        self.frames.append(frame)
        self._in_frame = 0
        return frame

    def _close_frame(self):
        if self.frame is not None:
            rows = (self._in_frame + 11) // 12
            self.frame_y -= (rows * 140 + 260)
        self.frame = None

    def finish(self):
        self._close_frame()

    def _node(self, idname, **settings):
        node = self.tree.nodes.new(idname)
        if self.frame is not None:
            node.parent = self.frame
            column, row = self._in_frame % 12, self._in_frame // 12
            node.location = (column * 190, self.frame_y - row * 140 - 120)
            self._in_frame += 1
        else:
            node.location = ((self.count % 40) * 180, -(self.count // 40) * 200 + 400)
        self.count += 1
        for key, value in settings.items():
            setattr(node, key, value)
        return node

    def label(self, value, text):
        """Give the node that made this number a readable name (shown in the Shader editor)."""
        if isinstance(value, S):
            value.sock.node.label = text
        return value

    def _feed(self, socket, value):
        if value is None:
            return
        if isinstance(value, S):
            self.tree.links.new(value.sock, socket)
        else:
            socket.default_value = float(value)

    # ---------------------------------------------------------------- arithmetic
    def math(self, op, a, b=None, c=None, clamp=False):
        if _isnum(a) and (b is None or _isnum(b)) and (c is None or _isnum(c)) and not clamp:
            return _py(op, a, b, c)
        node = self._node('ShaderNodeMath', operation=op, use_clamp=clamp)
        for index, value in enumerate((a, b, c)):
            self._feed(node.inputs[index], value)
        return S(self, node.outputs[0])

    def floor(self, a): return self.math('FLOOR', a)
    def fract(self, a): return self.math('FRACT', a)
    def sin(self, a): return self.math('SINE', a)
    def cos(self, a): return self.math('COSINE', a)
    def sqrt(self, a): return self.math('SQRT', a)
    def exp(self, a): return self.math('EXPONENT', a)
    def absolute(self, a): return self.math('ABSOLUTE', a)
    def minimum(self, a, b): return self.math('MINIMUM', a, b)
    def maximum(self, a, b): return self.math('MAXIMUM', a, b)
    def saturate(self, a): return self.math('ADD', a, 0.0, clamp=True)          # clamp to 0..1 with one node
    def clamp(self, a, lo, hi): return self.minimum(self.maximum(a, lo), hi)
    def pingpong(self, a, scale): return self.math('PINGPONG', a, scale)
    def multiply_add(self, a, b, c): return self.math('MULTIPLY_ADD', a, b, c)
    def less(self, a, b): return self.math('LESS_THAN', a, b)
    def greater(self, a, b): return self.math('GREATER_THAN', a, b)

    def lerp(self, a, b, t):
        """a when t = 0, b when t = 1."""
        return self.multiply_add(b - a, t, a)

    def where(self, condition, a, b):
        """a where condition (0 or 1) is 1, else b."""
        return self.multiply_add(a - b, condition, b)

    def smoothstep(self, lo, hi, x):
        t = self.saturate((x - lo) / (hi - lo))
        return t * t * (3.0 - 2.0 * t)

    # ---------------------------------------------------------------- tables made from one Color Ramp node
    def _make_ramp(self, node, positions, colours, interpolation):
        """Fill the Color Ramp node with stops at the given (increasing) positions."""
        ramp = node.color_ramp
        ramp.interpolation = interpolation
        n = len(positions)
        # a new ramp has two stops (at 0 and 1): move the second one next to the first, then add the others in increasing order
        if n >= 2:
            ramp.elements[1].position = positions[1]
        for position in positions[2:]:
            ramp.elements.new(position)
        for element, position, colour in zip(ramp.elements, positions, colours):
            element.position = position
            element.color = colour

    def table(self, index, columns, scale=1.0):
        """Look-up table. index: a whole number 0 .. n-1 (a node number). columns: 1 to 4 lists of n numbers each.
        Returns one number per column. One Color Ramp node with constant steps holds up to 4 columns (red, green, blue, alpha).
        Numbers are stored divided by 'scale' (the ramp keeps values best between 0 and 1) and multiplied back after."""
        n = len(columns[0])
        assert 1 <= len(columns) <= 4 and all(len(c) == n for c in columns) and 2 <= n <= 32
        node = self._node('ShaderNodeValToRGB')
        positions = [i / float(n) for i in range(n)]
        colours = []
        for i in range(n):
            values = [columns[c][i] / scale if c < len(columns) else 0.0 for c in range(4)]
            colours.append((values[0], values[1], values[2], values[3] if len(columns) > 3 else 1.0))
        self._make_ramp(node, positions, colours, 'CONSTANT')
        # constant steps: step i is active from position i/n; ask in the middle of the step
        self._feed(node.inputs['Fac'], (index + 0.5) / float(n))
        sep = self._node('ShaderNodeSeparateColor')
        self.tree.links.new(node.outputs['Color'], sep.inputs[0])
        out = []
        for c in range(len(columns)):
            sock = node.outputs['Alpha'] if c == 3 else sep.outputs[c]
            value = S(self, sock)
            out.append(value * scale if scale != 1.0 else value)
        return out if len(out) > 1 else out[0]

    def ramp(self, fac, stops, interpolation='LINEAR'):
        """A smooth colour curve: stops = [(position 0..1, (r, g, b) linear), ...] up to 32. Returns (r, g, b) numbers."""
        node = self._node('ShaderNodeValToRGB')
        self._make_ramp(node, [p for p, _ in stops], [(c[0], c[1], c[2], 1.0) for _, c in stops], interpolation)
        self._feed(node.inputs['Fac'], fac)
        sep = self._node('ShaderNodeSeparateColor')
        self.tree.links.new(node.outputs['Color'], sep.inputs[0])
        return S(self, sep.outputs[0]), S(self, sep.outputs[1]), S(self, sep.outputs[2])

    # ---------------------------------------------------------------- random numbers
    def rand(self, a, b=0.0, c=0.0, w=0.0):
        """Three random numbers 0..1 that depend only on the four inputs (a, b, c, w). Uses the White Noise 4D node."""
        node = self._node('ShaderNodeTexWhiteNoise', noise_dimensions='4D')
        vec = self._node('ShaderNodeCombineXYZ')
        for name, value in zip(('X', 'Y', 'Z'), (a, b, c)):
            self._feed(vec.inputs[name], value)
        self.tree.links.new(vec.outputs[0], node.inputs['Vector'])
        self._feed(node.inputs['W'], w)
        sep = self._node('ShaderNodeSeparateColor')
        self.tree.links.new(node.outputs['Color'], sep.inputs[0])
        return S(self, sep.outputs[0]), S(self, sep.outputs[1]), S(self, sep.outputs[2])

    def rand1(self, a, b=0.0, c=0.0, w=0.0):
        return self.rand(a, b, c, w)[0]

    # ---------------------------------------------------------------- noise (soft cloud patterns)
    def noise3(self, x, y, z, scale, detail=2.0, roughness=0.5):
        """Plain Blender noise, stretched to about 0..1. Does NOT repeat seamlessly."""
        vec = self._node('ShaderNodeCombineXYZ')
        for name, value in zip(('X', 'Y', 'Z'), (x, y, z)):
            self._feed(vec.inputs[name], value)
        node = self._node('ShaderNodeTexNoise', noise_dimensions='3D')
        self.tree.links.new(vec.outputs[0], node.inputs['Vector'])
        node.inputs['Scale'].default_value = scale
        node.inputs['Detail'].default_value = detail
        node.inputs['Roughness'].default_value = roughness
        fac = S(self, node.outputs['Fac'])
        return self.saturate((fac - 0.28) / 0.44)

    def noise4(self, x, y, z, w, scale, detail=2.0, roughness=0.5):
        """4D noise stretched to about 0..1. With (cos u, sin u, cos v, sin v) in the four slots it repeats exactly (a 'donut')."""
        vec = self._node('ShaderNodeCombineXYZ')
        for name, value in zip(('X', 'Y', 'Z'), (x, y, z)):
            self._feed(vec.inputs[name], value)
        node = self._node('ShaderNodeTexNoise', noise_dimensions='4D')
        self.tree.links.new(vec.outputs[0], node.inputs['Vector'])
        self._feed(node.inputs['W'], w)
        node.inputs['Scale'].default_value = scale
        node.inputs['Detail'].default_value = detail
        node.inputs['Roughness'].default_value = roughness
        return self.saturate((S(self, node.outputs['Fac']) - 0.28) / 0.44)

    def cells(self, x, y, scale):
        """Distance to the nearest of many random points (a Voronoi cell pattern, 2D); 'scale' cells per dot. 0 at a point, about 0.5 at the cell edge."""
        vec = self._node('ShaderNodeCombineXYZ')
        self._feed(vec.inputs['X'], x)
        self._feed(vec.inputs['Y'], y)
        node = self._node('ShaderNodeTexVoronoi', voronoi_dimensions='2D', feature='F1')
        self.tree.links.new(vec.outputs[0], node.inputs['Vector'])
        node.inputs['Scale'].default_value = scale
        node.inputs['Randomness'].default_value = 1.0
        return S(self, node.outputs['Distance'])

    def cells4(self, x, y, z, w, scale=1.0):
        """The same cell pattern in 4D: with (cos u, sin u, cos v, sin v) in the four slots it repeats exactly (a 'donut')."""
        vec = self._node('ShaderNodeCombineXYZ')
        for name, value in zip(('X', 'Y', 'Z'), (x, y, z)):
            self._feed(vec.inputs[name], value)
        node = self._node('ShaderNodeTexVoronoi', voronoi_dimensions='4D', feature='F1')
        self.tree.links.new(vec.outputs[0], node.inputs['Vector'])
        self._feed(node.inputs['W'], w)
        node.inputs['Scale'].default_value = scale
        node.inputs['Randomness'].default_value = 1.0
        return S(self, node.outputs['Distance'])

    # ---------------------------------------------------------------- pictures
    def load(self, path, colour=False):
        key = (path, colour)
        if key not in self.images:
            # one Blender image per (file, colour or data): the same file read as colour and as data must be two separate images
            image = bpy.data.images.load(path, check_existing=False)
            image.colorspace_settings.name = 'sRGB' if colour else 'Non-Color'
            self.images[key] = image
        return self.images[key]

    def image(self, path, x_dots, y_dots_down, colour=False, size=1254.0, interpolation='Linear'):
        """Read a picture at a place given in picture dots (x to the right 0..size, y DOWN from the top 0..size).
        Returns (r, g, b) numbers (for a grey picture the three are the same). The picture is read at the dot centre when
        x = i + 0.5 for the dot i."""
        node = self._node('ShaderNodeTexImage', interpolation=interpolation, extension='EXTEND')
        node.image = self.load(path, colour)
        vec = self._node('ShaderNodeCombineXYZ')
        self._feed(vec.inputs['X'], x_dots / float(size))
        self._feed(vec.inputs['Y'], 1.0 - y_dots_down / float(size))      # Blender's picture space has y going UP
        self.tree.links.new(vec.outputs[0], node.inputs['Vector'])
        sep = self._node('ShaderNodeSeparateColor')
        self.tree.links.new(node.outputs['Color'], sep.inputs[0])
        return S(self, sep.outputs[0]), S(self, sep.outputs[1]), S(self, sep.outputs[2])

    def combine_colour(self, r, g, b, socket):
        comb = self._node('ShaderNodeCombineColor')
        for name, value in zip(('Red', 'Green', 'Blue'), (r, g, b)):
            self._feed(comb.inputs[name], value)
        self.tree.links.new(comb.outputs[0], socket)

    def to_socket(self, value, socket):
        if isinstance(value, S):
            self.tree.links.new(value.sock, socket)
        else:
            socket.default_value = float(value)


def _py(op, a, b, c):
    f = {'ADD': lambda: a + b, 'SUBTRACT': lambda: a - b, 'MULTIPLY': lambda: a * b, 'DIVIDE': lambda: a / b if b else 0.0,
         'FLOORED_MODULO': lambda: a - math.floor(a / b) * b if b else 0.0, 'POWER': lambda: a ** b, 'FLOOR': lambda: math.floor(a),
         'FRACT': lambda: a - math.floor(a), 'SINE': lambda: math.sin(a), 'COSINE': lambda: math.cos(a), 'SQRT': lambda: math.sqrt(max(a, 0)),
         'EXPONENT': lambda: math.exp(a), 'ABSOLUTE': lambda: abs(a), 'MINIMUM': lambda: min(a, b), 'MAXIMUM': lambda: max(a, b),
         'LESS_THAN': lambda: 1.0 if a < b else 0.0, 'GREATER_THAN': lambda: 1.0 if a > b else 0.0,
         'MULTIPLY_ADD': lambda: a * b + c,
         'PINGPONG': lambda: abs(((a - b) % (2 * b)) - b) if b else 0.0}
    return float(f[op]())
