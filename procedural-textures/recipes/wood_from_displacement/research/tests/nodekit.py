# What this does: a small helper for the research tests in this folder. It lets a test write number sums in plain Python
# (for example  row = floor(v * 5.0)  or  x = (u + shift) % 1.0 ) and quietly builds the matching Blender shader nodes
# (Math, Separate/Combine XYZ, White Noise, Image Texture). Every number is an object of class S that remembers which node
# output it comes from. Plain Python numbers mixed in are turned into node settings. Nothing here is a finished recipe.
# Use (inside Blender):  import nodekit as nk ; kit = nk.Kit(material_node_tree) ; u, v = kit.uv() ; ...
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
    def __pow__(self, o): return self._bin('POWER', o)
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

    # ---------------------------------------------------------------- basics
    def _node(self, idname, **settings):
        node = self.tree.nodes.new(idname)
        node.location = ((self.count % 40) * 180, -(self.count // 40) * 200)
        self.count += 1
        for key, value in settings.items():
            setattr(node, key, value)
        return node

    def _feed(self, socket, value):
        if value is None:
            return
        if isinstance(value, S):
            self.tree.links.new(value.sock, socket)
        else:
            socket.default_value = float(value)

    def math(self, op, a, b=None, c=None, clamp=False):
        # two plain numbers: just compute it in Python (no node needed)
        if _isnum(a) and (b is None or _isnum(b)) and (c is None or _isnum(c)):
            return _py(op, a, b, c)
        node = self._node('ShaderNodeMath', operation=op, use_clamp=clamp)
        for index, value in enumerate((a, b, c)):
            self._feed(node.inputs[index], value)
        return S(self, node.outputs[0])

    def const(self, x):
        return float(x)

    # ---------------------------------------------------------------- functions
    def floor(self, a): return self.math('FLOOR', a)
    def fract(self, a): return self.math('FRACT', a)
    def sin(self, a): return self.math('SINE', a)
    def cos(self, a): return self.math('COSINE', a)
    def sqrt(self, a): return self.math('SQRT', a)
    def exp(self, a): return self.math('EXPONENT', a)
    def log(self, a): return self.math('LOGARITHM', a, math.e)
    def absolute(self, a): return self.math('ABSOLUTE', a)
    def minimum(self, a, b): return self.math('MINIMUM', a, b)
    def maximum(self, a, b): return self.math('MAXIMUM', a, b)
    def clamp(self, a, lo=0.0, hi=1.0): return self.minimum(self.maximum(a, lo), hi)
    def pingpong(self, a, scale): return self.math('PINGPONG', a, scale)
    def power(self, a, b): return self.math('POWER', a, b)
    def multiply_add(self, a, b, c): return self.math('MULTIPLY_ADD', a, b, c)
    def less(self, a, b): return self.math('LESS_THAN', a, b)
    def greater(self, a, b): return self.math('GREATER_THAN', a, b)

    def lerp(self, a, b, t):
        """a when t = 0, b when t = 1"""
        return a + (b - a) * t

    def where(self, condition, a, b):
        """a where condition (0 or 1) is 1, else b"""
        return b + (a - b) * condition

    def smoothstep(self, lo, hi, x):
        t = self.clamp((x - lo) / (hi - lo))
        return t * t * (3.0 - 2.0 * t)

    def pick(self, index, values):
        """Pick values[index] (index a whole number held in a node number). Nodes: one compare per entry."""
        out = values[0]
        for i in range(1, len(values)):
            out = self.where(self.math('COMPARE', index, float(i), 0.01), values[i], out)
        return out

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

    # ---------------------------------------------------------------- coordinates
    def uv(self):
        """(u, v) of the flat test square, both 0..1 over one tile; v counts UP the picture."""
        coord = self._node('ShaderNodeTexCoord')
        sep = self._node('ShaderNodeSeparateXYZ')
        self.tree.links.new(coord.outputs['UV'], sep.inputs[0])
        return S(self, sep.outputs[0]), S(self, sep.outputs[1])

    def noise(self, x, y, z, scale, detail=2.0, roughness=0.5):
        """Plain Blender noise 0..1 (it sits in 0.25 .. 0.75; stretched here to about 0..1). Does NOT repeat seamlessly."""
        vec = self._node('ShaderNodeCombineXYZ')
        for name, value in zip(('X', 'Y', 'Z'), (x, y, z)):
            self._feed(vec.inputs[name], value)
        node = self._node('ShaderNodeTexNoise', noise_dimensions='3D')
        self.tree.links.new(vec.outputs[0], node.inputs['Vector'])
        node.inputs['Scale'].default_value = scale
        node.inputs['Detail'].default_value = detail
        node.inputs['Roughness'].default_value = roughness
        fac = S(self, node.outputs['Fac'])
        return self.clamp((fac - 0.28) / 0.44)

    def noise4d(self, x, y, z, w, scale, detail=2.0, roughness=0.5):
        """Plain Blender 4D noise stretched to about 0..1. With (cos u, sin u, cos v, sin v) in the four slots it repeats seamlessly (a donut)."""
        vec = self._node('ShaderNodeCombineXYZ')
        for name, value in zip(('X', 'Y', 'Z'), (x, y, z)):
            self._feed(vec.inputs[name], value)
        node = self._node('ShaderNodeTexNoise', noise_dimensions='4D')
        self.tree.links.new(vec.outputs[0], node.inputs['Vector'])
        self._feed(node.inputs['W'], w)
        node.inputs['Scale'].default_value = scale
        node.inputs['Detail'].default_value = detail
        node.inputs['Roughness'].default_value = roughness
        return self.clamp((S(self, node.outputs['Fac']) - 0.28) / 0.44)

    # ---------------------------------------------------------------- pictures
    def load(self, path, colour=False):
        key = (path, colour)
        if key not in self.images:
            image = bpy.data.images.load(path, check_existing=True)
            image.colorspace_settings.name = 'sRGB' if colour else 'Non-Color'
            self.images[key] = image
        return self.images[key]

    def image(self, path, x_dots, y_dots_down, colour=False, extension='EXTEND', interpolation='Linear', size=1254):
        """Read a picture at a place given in picture dots: x to the right (0..size), y DOWN from the top (0..size).
        Returns (r, g, b) numbers. For a grey height picture take the first one."""
        node = self._node('ShaderNodeTexImage', interpolation=interpolation, extension=extension)
        node.image = self.load(path, colour)
        vec = self._node('ShaderNodeCombineXYZ')
        self._feed(vec.inputs['X'], x_dots / float(size))
        self._feed(vec.inputs['Y'], 1.0 - y_dots_down / float(size))      # Blender's picture space has y going UP
        self.tree.links.new(vec.outputs[0], node.inputs['Vector'])
        sep = self._node('ShaderNodeSeparateColor')
        self.tree.links.new(node.outputs['Color'], sep.inputs[0])
        return S(self, sep.outputs[0]), S(self, sep.outputs[1]), S(self, sep.outputs[2])

    # ---------------------------------------------------------------- output
    def emit_grey(self, value):
        """Wire a grey emission output for the render. Returns nothing."""
        self._emit(value, value, value)

    def emit_rgb(self, r, g, b):
        self._emit(r, g, b)

    def _emit(self, r, g, b):
        comb = self._node('ShaderNodeCombineColor')
        for name, value in zip(('Red', 'Green', 'Blue'), (r, g, b)):
            self._feed(comb.inputs[name], value)
        emit = self._node('ShaderNodeEmission')
        self.tree.links.new(comb.outputs[0], emit.inputs['Color'])
        out = self._node('ShaderNodeOutputMaterial')
        self.tree.links.new(emit.outputs[0], out.inputs['Surface'])


def _py(op, a, b, c):
    f = {'ADD': lambda: a + b, 'SUBTRACT': lambda: a - b, 'MULTIPLY': lambda: a * b, 'DIVIDE': lambda: a / b if b else 0.0,
         'FLOORED_MODULO': lambda: a - math.floor(a / b) * b if b else 0.0, 'POWER': lambda: a ** b, 'FLOOR': lambda: math.floor(a),
         'FRACT': lambda: a - math.floor(a), 'SINE': lambda: math.sin(a), 'COSINE': lambda: math.cos(a), 'SQRT': lambda: math.sqrt(max(a, 0)),
         'EXPONENT': lambda: math.exp(a), 'ABSOLUTE': lambda: abs(a), 'MINIMUM': lambda: min(a, b), 'MAXIMUM': lambda: max(a, b),
         'LESS_THAN': lambda: 1.0 if a < b else 0.0, 'GREATER_THAN': lambda: 1.0 if a > b else 0.0,
         'MULTIPLY_ADD': lambda: a * b + c, 'LOGARITHM': lambda: math.log(a) / math.log(b) if a > 0 else 0.0,
         'COMPARE': lambda: 1.0 if abs(a - b) <= c else 0.0,
         'PINGPONG': lambda: abs(((a - b) % (2 * b)) - b) if b else 0.0}
    return float(f[op]())
