# What this does: a small "write a shader recipe like a list of sums" helper for the six surface recipes in this folder.
# Instead of adding every node and every link by hand, you call one short function per step (b.math('ADD', x, 0.5), b.noise(...),
# b.ramp(...)) and each call adds the node, wires its inputs and gives you back the output, ready to be the input of the next step.
# A number can stand in for any input; a node output can stand in for any input as well. It sits on top of the project's own
# recipe_tools.py (lib/) and adds: seamless (tile-wrapping) noise and cells that can be stretched along one direction,
# a "which brick / which tile am I on" helper, and a sRGB-hex colour converter (colours typed in Blender are linear, hex codes are not).
# Use (inside Blender):  import builder as bd ;  b = bd.Builder('my recipe') ;  u, v = b.uv_xy() ; ... ; b.finish(colour=..., height=...)
import math
import os
import sys

import bpy

LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'lib')
sys.path.insert(0, os.path.abspath(LIB))
import recipe_tools as rt  # noqa: E402


def srgb_hex_to_linear(code):
    """'#b5553a' (what a colour picker or a reference picture shows) -> (r, g, b, 1) in the linear numbers Blender wants."""
    code = code.lstrip('#')
    values = [int(code[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    linear = [(c / 12.92) if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in values]
    return (linear[0], linear[1], linear[2], 1.0)


def as_colour(value):
    if isinstance(value, str):
        return srgb_hex_to_linear(value)
    if len(value) == 3:
        return (value[0], value[1], value[2], 1.0)
    return tuple(value)


class Builder:
    """One shader node group (input 'Vector' = the tile coordinate, outputs Colour, Roughness, Metallic, Height)."""

    def __init__(self, name, shift=(0.0, 0.0)):
        self.tree, self.w = rt.make_group_tree(name, [('Vector', 'NodeSocketVector', (0, 0, 0))],
                                                [('Colour', 'NodeSocketColor'), ('Roughness', 'NodeSocketFloat'),
                                                 ('Metallic', 'NodeSocketFloat'), ('Height', 'NodeSocketFloat')])
        self.count = 0
        self._uv = None
        self.shift = tuple(shift)      # slide the whole pattern by (u, v): used only by the periodicity test (shift 0.5, 0.5 must equal the picture rolled by half)

    # ------------------------------------------------------------------ plumbing
    def _place(self, node):
        self.count += 1
        node.location = ((self.count % 14) * 220, -(self.count // 14) * 260)
        return node

    def _put(self, node, key, value):
        """value: None (leave), a node output (link), or a number / tuple (set the default)."""
        if value is None:
            return
        socket = node.inputs[key]
        if isinstance(value, bpy.types.NodeSocket):
            self.tree.links.new(value, socket)
        else:
            socket.default_value = value

    def node(self, kind, **settings):
        node = self._place(self.tree.nodes.new(kind))
        for key, value in settings.items():
            setattr(node, key, value)
        return node

    # ------------------------------------------------------------------ coordinates
    def uv(self):
        return self.w.nodes['in'].outputs['Vector']

    def uv_xy(self):
        if self._uv is None:
            x, y, z = self.xyz(self.uv())
            if self.shift[0] != 0.0:
                x = self.add(x, self.shift[0])
            if self.shift[1] != 0.0:
                y = self.add(y, self.shift[1])
            self._uv = (x, y, z)
        return self._uv[0], self._uv[1]

    def xyz(self, vector):
        node = self.node('ShaderNodeSeparateXYZ')
        self._put(node, 0, vector)
        return node.outputs[0], node.outputs[1], node.outputs[2]

    def vec(self, x=0.0, y=0.0, z=0.0):
        node = self.node('ShaderNodeCombineXYZ')
        self._put(node, 'X', x)
        self._put(node, 'Y', y)
        self._put(node, 'Z', z)
        return node.outputs[0]

    # ------------------------------------------------------------------ arithmetic
    def math(self, operation, a=None, b=None, c=None, clamp=False):
        node = self.node('ShaderNodeMath', operation=operation, use_clamp=clamp)
        for index, value in enumerate((a, b, c)):
            self._put(node, index, value)
        return node.outputs[0]

    def add(self, a, b):
        return self.math('ADD', a, b)

    def sub(self, a, b):
        return self.math('SUBTRACT', a, b)

    def mul(self, a, b):
        return self.math('MULTIPLY', a, b)

    def div(self, a, b):
        return self.math('DIVIDE', a, b)

    def lt(self, a, b):
        return self.math('LESS_THAN', a, b)

    def gt(self, a, b):
        return self.math('GREATER_THAN', a, b)

    def mn(self, a, b):
        return self.math('MINIMUM', a, b)

    def mx(self, a, b):
        return self.math('MAXIMUM', a, b)

    def floor(self, a):
        return self.math('FLOOR', a)

    def frac(self, a):
        return self.math('FRACT', a)

    def mod(self, a, b):
        return self.math('FLOORED_MODULO', a, b)

    def absolute(self, a):
        return self.math('ABSOLUTE', a)

    def clamp01(self, a):
        return self.math('ADD', a, 0.0, clamp=True)

    def invert(self, a):
        return self.math('SUBTRACT', 1.0, a)

    def vmath(self, operation, a=None, b=None, scale=None):
        node = self.node('ShaderNodeVectorMath', operation=operation)
        self._put(node, 0, a)
        self._put(node, 1, b)
        if scale is not None:
            self._put(node, 'Scale', scale)
        if operation in ('LENGTH', 'DISTANCE', 'DOT_PRODUCT'):
            return node.outputs['Value']
        return node.outputs['Vector']

    def maprange(self, value, from_min, from_max, to_min=0.0, to_max=1.0, clamp=True, interpolation='LINEAR'):
        node = self.node('ShaderNodeMapRange', data_type='FLOAT', interpolation_type=interpolation, clamp=clamp)
        for index, v in enumerate((value, from_min, from_max, to_min, to_max)):
            self._put(node, index, v)
        return node.outputs[0]

    def window(self, value, low, high, soft=False):
        """0 below low, 1 above high; a hard step when low == high (nudged apart by a hair)."""
        if isinstance(low, bpy.types.NodeSocket) or isinstance(high, bpy.types.NodeSocket):
            if high is low or not isinstance(high, bpy.types.NodeSocket) and not isinstance(low, bpy.types.NodeSocket) and high <= low:
                high = self.add(low, 1e-4)
        elif high <= low:
            high = low + 1e-4
        return self.maprange(value, low, high, 0.0, 1.0, True, 'SMOOTHSTEP' if soft else 'LINEAR')

    # ------------------------------------------------------------------ colour
    def ramp(self, fac, stops, interpolation='LINEAR'):
        """stops: list of (position, colour) with colour a '#hex' string or an (r, g, b) linear tuple. Returns the colour output."""
        node = self.node('ShaderNodeValToRGB')
        ramp = node.color_ramp
        ramp.interpolation = interpolation
        while len(ramp.elements) > 1:
            ramp.elements.remove(ramp.elements[-1])
        ramp.elements[0].position = stops[0][0]
        ramp.elements[0].color = as_colour(stops[0][1])
        for position, colour in stops[1:]:
            element = ramp.elements.new(position)
            element.color = as_colour(colour)
        self._put(node, 'Fac', fac)
        return node.outputs['Color']

    def ramp_value(self, fac, stops, interpolation='LINEAR'):
        """Same as ramp but the stops are plain numbers (a grey ramp) and the output is a single value."""
        colour = self.ramp(fac, [(p, (v, v, v)) for p, v in stops], interpolation)
        node = self.node('ShaderNodeSeparateColor')
        self._put(node, 0, colour)
        return node.outputs[0]

    def mix(self, a, b, fac, blend='MIX'):
        node = self.node('ShaderNodeMix', data_type='RGBA', blend_type=blend, clamp_factor=True, clamp_result=False)
        self._put(node, 0, fac)
        self._put(node, 6, as_colour(a) if isinstance(a, (str, tuple, list)) else a)
        self._put(node, 7, as_colour(b) if isinstance(b, (str, tuple, list)) else b)
        return node.outputs[2]

    def mixf(self, a, b, fac):
        node = self.node('ShaderNodeMix', data_type='FLOAT', clamp_factor=True)
        self._put(node, 0, fac)
        self._put(node, 2, a)
        self._put(node, 3, b)
        return node.outputs[0]

    def grey_to_colour(self, value):
        node = self.node('ShaderNodeCombineColor')
        for socket in ('Red', 'Green', 'Blue'):
            self._put(node, socket, value)
        return node.outputs[0]

    def brightness(self, colour):
        node = self.node('ShaderNodeRGBToBW')
        self._put(node, 0, colour)
        return node.outputs[0]

    def channels(self, colour):
        node = self.node('ShaderNodeSeparateColor')
        self._put(node, 0, colour)
        return node.outputs[0], node.outputs[1], node.outputs[2]

    # ------------------------------------------------------------------ patterns (plain Blender nodes)
    def noise(self, vector=None, scale=5.0, detail=2.0, roughness=0.5, distortion=0.0, w=None, dimensions='3D',
              noise_type='FBM', lacunarity=2.0, normalize=True):
        node = self.node('ShaderNodeTexNoise', noise_dimensions=dimensions, noise_type=noise_type, normalize=normalize)
        self._put(node, 'Vector', vector)
        if w is not None:
            self._put(node, 'W', w)
        self._put(node, 'Scale', scale)
        self._put(node, 'Detail', detail)
        self._put(node, 'Roughness', roughness)
        self._put(node, 'Lacunarity', lacunarity)
        self._put(node, 'Distortion', distortion)
        return node

    def white(self, vector, dimensions='3D'):
        node = self.node('ShaderNodeTexWhiteNoise', noise_dimensions=dimensions)
        self._put(node, 'Vector', vector)
        return node

    # ------------------------------------------------------------------ seamless patterns that can be stretched
    def donut(self, scale_u, scale_v, seed=0.0, shift_u=0.0, shift_v=0.0, coords=None):
        """Turn the tile coordinate into 4 numbers that run in circles, so any pattern read from them repeats every 1.0 in u and v.
        scale_u / scale_v = how many pattern features fit across the tile left-right / up-down (different numbers stretch the
        pattern; scale_u 2 and scale_v 30 = long thin horizontal streaks). shift_u / shift_v slide the pattern along (still seamless).
        coords = (a, b): use these two node outputs (each must repeat every 1.0, for example a = u + v) instead of u and v, which lets
        the stretch run along a diagonal or along a bending line. Returns (vector_xyz, w)."""
        if coords is None:
            u, v = self.uv_xy()
        else:
            u, v = coords
        if shift_u != 0.0:
            u = self.add(u, shift_u)
        if shift_v != 0.0:
            v = self.add(v, shift_v)
        turns_u = self.mul(u, 2 * math.pi)
        turns_v = self.mul(v, 2 * math.pi)
        radius_u = self.mul(scale_u, 1 / (2 * math.pi)) if isinstance(scale_u, bpy.types.NodeSocket) else scale_u / (2 * math.pi)
        radius_v = self.mul(scale_v, 1 / (2 * math.pi)) if isinstance(scale_v, bpy.types.NodeSocket) else scale_v / (2 * math.pi)
        cos_u, sin_u = self.math('COSINE', turns_u), self.math('SINE', turns_u)
        cos_v, sin_v = self.math('COSINE', turns_v), self.math('SINE', turns_v)
        self.last_trig = (cos_u, sin_u, cos_v, sin_v)
        x = self.mul(cos_u, radius_u)
        y = self.mul(sin_u, radius_u)
        z = self.mul(cos_v, radius_v)
        w = self.add(self.mul(sin_v, radius_v), seed)
        return self.vec(x, y, z), w

    def tnoise(self, scale_u, scale_v=None, detail=4.0, roughness=0.5, distortion=0.0, seed=0.0, lacunarity=2.0,
               noise_type='FBM', shift_u=0.0, shift_v=0.0, coords=None):
        """Seamless noise (value 0..1, mostly 0.25..0.75: stretch it with maprange). Returns the Fac output."""
        scale_v = scale_u if scale_v is None else scale_v
        vector, w = self.donut(scale_u, scale_v, seed, shift_u, shift_v, coords)
        node = self.noise(vector, 1.0, detail, roughness, distortion, w, '4D', noise_type, lacunarity)
        return node.outputs['Factor']

    def tnoise_vector(self, scale_u, scale_v=None, detail=2.0, roughness=0.5, seed=0.0):
        """Seamless noise as a random direction (Color output, three separate noises, each about 0..1)."""
        scale_v = scale_u if scale_v is None else scale_v
        vector, w = self.donut(scale_u, scale_v, seed)
        node = self.noise(vector, 1.0, detail, roughness, 0.0, w, '4D')
        return node.outputs['Color']

    def tvoronoi(self, scale_u, scale_v=None, seed=0.0, feature='F1', metric='EUCLIDEAN', randomness=1.0, exponent=None, coords=None):
        """Seamless cells. Returns the Voronoi node (outputs: Distance, Color, Position, W, Radius)."""
        scale_v = scale_u if scale_v is None else scale_v
        vector, w = self.donut(scale_u, scale_v, seed, 0.0, 0.0, coords)
        self.last_donut = (vector, w)
        node = self.node('ShaderNodeTexVoronoi', voronoi_dimensions='4D', feature=feature, distance=metric, normalize=False)
        self._put(node, 'Vector', vector)
        self._put(node, 'W', w)
        self._put(node, 'Scale', 1.0)
        self._put(node, 'Randomness', randomness)
        if exponent is not None:
            self._put(node, 'Exponent', exponent)
        return node

    # ------------------------------------------------------------------ "which brick am I on"
    def rows_and_columns(self, columns, rows, shift_rows=0.5, u_extra=None, v_extra=None):
        """Brick / tile layout that tiles exactly (columns whole, rows EVEN when shift_rows is used).
        Returns a dict: column_id, row_id (whole numbers, wrapped so the tile repeats), fx (0..1 along the brick),
        fy (0..1 up the brick), u_bricks / v_bricks (continuous brick coordinates)."""
        u, v = self.uv_xy()
        if u_extra is not None:
            u = self.add(u, u_extra)
        if v_extra is not None:
            v = self.add(v, v_extra)
        v_rows = self.mul(v, rows)
        row_id = self.floor(v_rows)
        fy = self.frac(v_rows)
        odd = self.mod(row_id, 2.0)
        u_bricks = self.add(self.mul(u, columns), self.mul(odd, shift_rows))
        column_raw = self.floor(u_bricks)
        fx = self.frac(u_bricks)
        column_id = self.mod(column_raw, columns)
        return {'column_id': column_id, 'row_id': self.mod(row_id, rows), 'fx': fx, 'fy': fy, 'u_bricks': u_bricks,
                'v_bricks': v_rows, 'row_raw': row_id, 'column_raw': column_raw}

    def hash2(self, a, b, seed=0.0):
        """One random number 0..1 for the pair of whole numbers (a, b)."""
        vector = self.vec(a, b, seed)
        return self.white(vector, '3D').outputs['Value']

    # ------------------------------------------------------------------ finishing
    def finish(self, colour, height, roughness=0.8, metallic=0.0):
        out = self.w.nodes['out']
        self._put_out(out, 'Colour', colour)
        self._put_out(out, 'Height', height)
        self._put_out(out, 'Roughness', roughness)
        self._put_out(out, 'Metallic', metallic)
        return self.tree

    def _put_out(self, out, key, value):
        socket = out.inputs[key]
        if isinstance(value, bpy.types.NodeSocket):
            self.tree.links.new(value, socket)
        else:
            socket.default_value = value

    def height_from_colour(self, colour, gamma=0.4545):
        """The references' heights follow colour brightness. Screen brightness of the colour = height."""
        node = self.node('ShaderNodeGamma')
        self._put(node, 'Color', colour)
        self._put(node, 'Gamma', gamma)
        return self.brightness(node.outputs[0])
