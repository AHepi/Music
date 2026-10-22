# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# The shared helpers of the WALLS layers (soot, runoff, foot, steps, wallgrowth, wallcracks, paint). Nothing here names a place, an object or a number of a set:
# a layer reads the kit's standard masks by name and the dials of its own table, and works on any material (the hook puts it in before the Principled BSDF).
#
# WallLayer is the kit's LayerBase (apply/layer_template.py) plus the small tools every walls layer needs:
#   * a surface frame made from the world position and the surface normal: `along` (a metre count that runs ALONG the wall, whatever way the wall faces) and `up` (world z).
#     Streaks, mottling and bands are laid out in these two numbers, so one recipe works on a house front, a gable, a plaster wall or a post.
#   * noise in that frame with a different stretch along and up (soot clouds are taller than wide, streaks much taller), each object and each Seed dial moving it;
#   * sizes in PLATE DOTS: width_dots() turns "at least this many plate dots" into metres through the kit's WK MARK WIDTH helper, using Dot Along for a width measured ALONG a
#     wall (a wall seen from the side is squashed, so a streak must be drawn wider than real to stay N dots wide) or Dot Across for a width measured up the wall;
#   * colour tools: gain (multiply a colour), tint, grey pull, luma;
#   * the per-role multiplier of a dial (the set may name one, apply.<layer>.role_dials; an object without one gives 1);
#   * extra outputs for debug views ("Part <name>") that show one named part of a layer.
# Every effect strength a layer makes goes through self.amount (the master dial times the object's role amount): at Amount 0 every mix factor is exactly 0 and the outputs equal
# the inputs. Nothing divides by a number that can be 0 (clamp before dividing).
import math

import bpy

from apply import dials as dials_module, layer_template, nodes
from masks import scale as scale_module

# constants of the BUS (documented in masks/CONTRACT.md): how far a scaled distance picture reaches
DRIP_REACH_M = 1.5          # drip_dist = metres below the source / 1.5
CORNER_REACH_M = 0.4        # corner = distance to an edge / 0.4
STEP_REACH_M = 0.25         # step_edge = distance in from the tread edge / 0.25
EDGE_REACH_M = 0.3          # edge_dist = distance to a sharp edge / 0.3
KIND_ITEMS = dict(ledge=0.2, pipe_joint=0.4, pipe_foot=0.6, eave=0.8, cap=1.0)   # drip_kind values (CONTRACT)
OBJECT_CLASS_ATTR = 'wk_walls_class'   # written by apply_walls: 0 wall, 1 chimney stack, 2 roof (by the role's own name)


def ensure_dials(layer_key, rows):
    """Adds finer dials of a layer to the kit's table (the same style as the table's own rows; the common names are never redefined). Safe to call twice."""
    from apply import dials as dials_module
    have = dials_module.TABLE.layers.get(layer_key)
    new = [dict(r) for r in rows if have is None or have.row(r['name']) is None]
    if new:
        dials_module.register_layer(layer_key, new)


class WallLayer(layer_template.LayerBase):
    """LayerBase plus the walls tools. Build a layer like:
        L = WallLayer('soot', 'WK SOOT', masks=['sheltered', ...])
        ... L.noise(...), L.width_dots(...), L.gain(...) ...
        L.finish_layer(colour=..., roughness=..., mask=..., parts={'washed': socket})
    """

    def __init__(self, key, group_name, masks=(), parts=(), role_handled=(), **kw):
        masks = list(masks)
        self._role_handled = set(role_handled)         # dials this layer multiplies by role_mult itself (soot's film_mult and sheltered_mult): dial() must not do it twice
        self._role_scaled = {}
        super().__init__(key, group_name, masks=masks, **kw)
        # extra debug outputs, one per named part (a view of one part of the layer: apply_walls.show_mask(kit, 'soot.washed')); the sockets are made in finish_layer
        self.part_names = list(parts)
        self._frame = None
        self._seed3 = None

    # ------------------------------------------------------------------ small numeric helpers (all return sockets)
    def mx(self, a, b):
        return self.n.math('MAXIMUM', a, b)

    def mn(self, a, b):
        return self.n.math('MINIMUM', a, b)

    def mul(self, a, b):
        return self.n.math('MULTIPLY', a, b)

    def add(self, a, b):
        return self.n.math('ADD', a, b)

    def sub(self, a, b):
        return self.n.math('SUBTRACT', a, b)

    def lerp(self, t, a, b):
        return self.n.mix(t, a, b)

    def sstep(self, v, lo, hi):
        """smoothstep of v between lo and hi (each a number or a socket)."""
        return self.n.map_range(v, lo, hi, 0.0, 1.0, smooth=True)

    def lin(self, v, lo, hi):
        return self.n.map_range(v, lo, hi, 0.0, 1.0, smooth=False)

    def c01(self, v):
        return self.n.clamp01(v)

    def one_minus(self, v):
        return self.n.one_minus(v)

    def absv(self, v):
        return self.n.math('ABSOLUTE', v)

    def gt(self, v, t):
        return self.n.math('GREATER_THAN', v, t)

    def lt(self, v, t):
        return self.n.math('LESS_THAN', v, t)

    def pw(self, v, e):
        return self.n.math('POWER', self.mx(v, 0.0), e)

    def frac(self, v):
        return self.n.math('FRACT', v)

    def inv(self, v):
        """1 / v for a v that is known to be positive (a width from the mark helper, a dial with a positive range)."""
        return self.n.math('DIVIDE', 1.0, v)

    def mad(self, a, b, c):
        """a * b + c in one node."""
        return self.n.math('MULTIPLY_ADD', a, b, c)

    def div_safe(self, a, b, floor=1e-5):
        return self.n.math('DIVIDE', a, self.mx(b, floor))

    # ------------------------------------------------------------------ surface frame
    def frame(self):
        """(position, normal, along, up): along = position . normalize(cross(normal, z)), up = z. For a wall facing the viewer along is the metre count down its length."""
        if self._frame is None:
            n = self.n
            geo = n.geometry()
            pos, nrm = geo.outputs['Position'], geo.outputs['Normal']
            cross = n.vector_math('CROSS_PRODUCT', nrm, (0.0, 0.0, 1.0))
            tangent = n.vector_math('NORMALIZE', cross)
            along = n.vector_math('DOT_PRODUCT', pos, tangent)
            _, _, z = n.separate(pos)
            self._frame = (pos, nrm, along, z)
        return self._frame

    @property
    def along(self):
        return self.frame()[2]

    @property
    def up(self):
        return self.frame()[3]

    @property
    def position(self):
        return self.frame()[0]

    @property
    def normal_world(self):
        return self.frame()[1]

    def local_frame(self):
        """(along, up) in the OBJECT's own frame: metres along the front from the object's origin and metres above it (a house's own front, whatever its place in the row). The
        along direction is made from the normal in the object's frame, as `frame` does in the world."""
        if getattr(self, '_local', None) is None:
            n = self.n
            coord = n.new('ShaderNodeTexCoord')
            xf = n.new('ShaderNodeVectorTransform')
            xf.vector_type = 'NORMAL'
            xf.convert_from = 'WORLD'
            xf.convert_to = 'OBJECT'
            self.tree.links.new(self.normal_world, xf.inputs['Vector'])
            tangent = n.vector_math('NORMALIZE', n.vector_math('CROSS_PRODUCT', xf.outputs['Vector'], (0.0, 0.0, 1.0)))
            along = n.vector_math('DOT_PRODUCT', coord.outputs['Object'], tangent)
            _, _, z = n.separate(coord.outputs['Object'])
            self._local = (along, z)
        return self._local

    def seed_obj(self):
        if not hasattr(self, '_seed_obj'):
            self._seed_obj = self.n.attr('wk_seed')
        return self._seed_obj

    def seed3(self):
        """A number that moves every noise: per object (wk_seed) and by the layer's Seed dial. Different for every house."""
        if self._seed3 is None:
            self._seed3 = self.add(self.mul(self.seed_obj(), 131.7), self.mul(self.dial('seed'), 17.3))
        return self._seed3

    def house_rand(self, salt=0.0):
        """A random number 0..1 that is the same everywhere on one object and differs between objects and with the Seed dial (for 'this house has it, that one has not')."""
        return self.frac(self.add(self.mul(self.add(self.seed_obj(), self.mul(self.dial('seed'), 0.0137)), 9301.0 + 17.0 * salt), 0.5 + salt))

    def coord(self, sx, sz, shift=0.0):
        """A noise coordinate: (along * sx, up * sz, per-object slice [+ shift]). sx, sz are frequencies (1/metres, numbers or sockets); a zero sz makes a noise that depends on the
        sideways position only."""
        n = self.n
        a = n.math('MULTIPLY', self.along, sx)
        u = 0.0 if (isinstance(sz, (int, float)) and sz == 0.0) else n.math('MULTIPLY', self.up, sz)
        w = self.seed3() if not shift else self.add(self.seed3(), shift)
        return n.combine(a, u, w)

    def noise(self, sx, sz, shift=0.0, detail=3.0, roughness=0.5):
        """Noise 0..1 (roughly 0.5 +- 0.12) in the surface frame."""
        return self.n.noise(self.coord(sx, sz, shift), 1.0, detail, roughness)

    def stretch(self, v, k=3.2):
        """Spread a noise value (about 0.5 +- 0.12) over 0..1 (one clamped map-range node)."""
        return self.n.map_range(v, 0.5 - 0.5 / k, 0.5 + 0.5 / k, 0.0, 1.0, smooth=False)

    # ------------------------------------------------------------------ sizes in plate dots
    def width_dots(self, real_m, min_dots, along=True):
        """(width in metres, fade). width = max(real, min_dots x one dot) where one dot is Dot Along (a width measured ALONG a wall: a side-on wall is squashed) or Dot Across
        (a width measured UP a wall or across the view). fade = 1 while the widening is inside Inflate Limit, falling to 0 by twice that (then the mark gives way to the layer's
        average tone, never to clean)."""
        group = self.n.new('ShaderNodeGroup')
        group.node_tree = scale_module.build_mark_width_group()
        for name, value in (('Real Width', real_m), ('Min Dots', min_dots), ('Dot Size', self.g('Dot Along') if along else self.g('Dot Across')), ('Inflate Limit', self.g('Inflate Limit'))):
            if isinstance(value, bpy.types.NodeSocket):
                self.tree.links.new(value, group.inputs[name])
            else:
                group.inputs[name].default_value = float(value)
        return group.outputs['Width'], group.outputs['Fade']

    # ------------------------------------------------------------------ per-role multiplier of a dial
    def dial(self, dial):
        """The group input of one dial. A dial the set varies by role (apply.<layer>.role_dials, noted by Kit.apply in dials.ROLE_DIAL_NAMES) comes multiplied by the object's role
        value (wk_<layer>_<dial>; 1 where the role names none), so EVERY walls layer can differ between plaster, stone and wood by settings alone. Dials the set does not vary cost no
        node; dials a layer multiplies itself (role_handled) are left as they are."""
        socket = super().dial(dial)
        if dial == 'amount' or dial in self._role_handled or dial not in dials_module.ROLE_DIAL_NAMES.get(self.key, ()):
            return socket
        scaled = self._role_scaled.get(dial)
        if scaled is None:
            scaled = self.mul(socket, self.role_mult(dial))
            self._role_scaled[dial] = scaled
        return scaled

    def role_mult(self, dial):
        """The role's multiplier of a dial: the object's value wk_<layer>_<dial> where the set names one, 1 where it does not (a missing value reads 0 -> 1)."""
        attr = self.n.attr(f'wk_{self.key}_{dial}')
        present = self.gt(attr, 0.001)
        return self.lerp(present, 1.0, attr)

    def object_class(self):
        """0 wall, 1 chimney stack, 2 roof: the object's own class value (apply_walls writes it from the role's own name). Returns (is_stack, is_roof) as 0/1 sockets."""
        cls = self.n.attr(OBJECT_CLASS_ATTR)
        is_stack = self.mul(self.gt(cls, 0.5), self.lt(cls, 1.5))
        is_roof = self.gt(cls, 1.5)
        return is_stack, is_roof

    # ------------------------------------------------------------------ colour tools
    def luma(self, colour):
        r, g, b = self.n.sep_rgb(colour)
        return self.add(self.add(self.mul(r, 0.2126), self.mul(g, 0.7152)), self.mul(b, 0.0722))

    def grey_of(self, colour):
        lm = self.luma(colour)
        return self.n.comb_rgb(lm, lm, lm)

    def gain(self, colour, factor):
        """colour x factor (a number or socket): one vector-scale node."""
        node = self.n.new('ShaderNodeVectorMath')
        node.operation = 'SCALE'
        self.tree.links.new(colour, node.inputs[0])
        if isinstance(factor, bpy.types.NodeSocket):
            self.tree.links.new(factor, node.inputs['Scale'])
        else:
            node.inputs['Scale'].default_value = float(factor)
        return node.outputs[0]

    def lift_to(self, colour, rgb, fac):
        """Pale-first: each colour channel at least rgb x fac (a pale target scaled by fac). Where the surface is already paler than the target nothing changes, so a dark wall gets a visible
        pale patch and a pale wall is left alone."""
        scaled = self.n.new('ShaderNodeVectorMath')
        scaled.operation = 'SCALE'
        if isinstance(rgb, bpy.types.NodeSocket):
            self.tree.links.new(rgb, scaled.inputs[0])
        else:
            scaled.inputs[0].default_value = (rgb[0], rgb[1], rgb[2])
        self.tree.links.new(fac, scaled.inputs['Scale'])
        return self.n.vector_math('MAXIMUM', colour, scaled.outputs[0])

    def height_eff(self, m_height, frame_valid):
        """Metres above the ground. The bus' height is trusted where a wall sheet applies; elsewhere it is the larger of the bus' height and the metres above the object's own lowest
        point (an object outside the ground picture reads height 0 from the bus, which would make a whole chimney 'the foot of a wall')."""
        own = self.sub(self.up, self.n.attr('wk_zmin'))
        return self.lerp(frame_valid, self.mx(m_height, own), m_height)

    def tint(self, colour, rgb, fac):
        """mix(colour, rgb, fac); rgb a 3-tuple or a socket."""
        value = (rgb[0], rgb[1], rgb[2], 1.0) if not isinstance(rgb, bpy.types.NodeSocket) else rgb
        return self.n.mix_colour(fac, colour, value)

    def grey_pull(self, colour, fac):
        return self.n.mix_colour(fac, colour, self.grey_of(colour))

    def hsv_colour(self, hue, sat, val):
        """A colour from numbers or sockets (hue 0..1, saturation, value): Hue/Saturation/Value of a flat colour is not needed, a combine node does it."""
        node = self.n.new('ShaderNodeCombineColor')
        node.mode = 'HSV'
        for name, v in (('Red', hue), ('Green', sat), ('Blue', val)):
            if isinstance(v, bpy.types.NodeSocket):
                self.tree.links.new(v, node.inputs[name])
            else:
                node.inputs[name].default_value = float(v)
        return node.outputs['Color']

    def bump(self, height_m, fac, normal=None, distance=1.0):
        """The incoming Normal tilted by a relief of `height_m` metres (positive = proud), blended by fac (0 gives the incoming normal back exactly)."""
        node = self.n.new('ShaderNodeBump')
        self.tree.links.new(height_m, node.inputs['Height'])
        node.inputs['Distance'].default_value = distance
        node.inputs['Strength'].default_value = 1.0
        self.tree.links.new(normal if normal is not None else self.g('Normal'), node.inputs['Normal'])
        return self.n.mix_vector(fac, normal if normal is not None else self.g('Normal'), node.outputs['Normal'])

    # ------------------------------------------------------------------ the master dial: blend the full-strength result with the input
    def blend_colour(self, colour_in, colour_effect):
        """colour_in + Amount x (colour_effect - colour_in): Amount 0 returns colour_in exactly, 1 the effect, 2 doubles it (kept inside 0..1)."""
        node = self.n.new('ShaderNodeMix')
        node.data_type = 'RGBA'
        node.blend_type = 'MIX'
        node.clamp_factor = False
        node.clamp_result = True
        self.tree.links.new(self.amount, node.inputs[0])
        self.tree.links.new(colour_in, node.inputs[6])
        self.tree.links.new(colour_effect, node.inputs[7])
        return node.outputs[2]

    def blend_float(self, value_in, value_effect):
        node = self.n.new('ShaderNodeMix')
        node.data_type = 'FLOAT'
        node.clamp_factor = False
        self.tree.links.new(self.amount, node.inputs[0])
        self.tree.links.new(value_in, node.inputs[2])
        if isinstance(value_effect, bpy.types.NodeSocket):
            self.tree.links.new(value_effect, node.inputs[3])
        else:
            node.inputs[3].default_value = float(value_effect)
        return node.outputs[0]

    def blend_normal(self, normal_in, normal_effect, fac=None):
        """The normal blended by Amount (and by `fac`, for example the distance fade)."""
        f = self.amount if fac is None else self.mul(self.amount, fac)
        node = self.n.new('ShaderNodeMix')
        node.data_type = 'VECTOR'
        node.clamp_factor = False
        self.tree.links.new(f, node.inputs[0])
        self.tree.links.new(normal_in, node.inputs[4])
        self.tree.links.new(normal_effect, node.inputs[5])
        return node.outputs[1]

    def bump_raw(self, height_m, normal=None, distance=1.0):
        """The incoming Normal tilted by a relief of height_m metres (positive = proud), full strength (blend it with blend_normal)."""
        node = self.n.new('ShaderNodeBump')
        self.tree.links.new(height_m, node.inputs['Height'])
        node.inputs['Distance'].default_value = distance
        node.inputs['Strength'].default_value = 1.0
        self.tree.links.new(normal if normal is not None else self.g('Normal'), node.inputs['Normal'])
        return node.outputs['Normal']

    # ------------------------------------------------------------------ finishing
    def finish_layer(self, mask=None, parts=None, **outputs):
        tree = self.finish(mask=mask, **outputs)
        for part in self.part_names:
            name = 'Part ' + part.replace('_', ' ').title()
            self.tree.interface.new_socket(name, in_out='OUTPUT', socket_type='NodeSocketFloat')
            socket = self.gout.inputs[name]
            value = (parts or {}).get(part)
            if value is not None:
                self.tree.links.new(value, socket)
            else:
                socket.default_value = 0.0
        return tree


def count_nodes(tree):
    """(nodes, noise-or-voronoi nodes) of a layer group, nested groups not counted (the kit's cost rule: about 150 nodes, at most three noise or Voronoi)."""
    total = len(tree.nodes)
    heavy = sum(1 for node in tree.nodes if node.bl_idname in ('ShaderNodeTexNoise', 'ShaderNodeTexVoronoi', 'ShaderNodeTexWhiteNoise'))
    return total, heavy


def forbidden_nodes(tree):
    """Names of nodes the kit forbids in a layer (Bevel, Ambient Occlusion, Pointiness through Geometry is an output not a node, so only the first two)."""
    return [n.bl_idname for n in tree.nodes if n.bl_idname in ('ShaderNodeBevel', 'ShaderNodeAmbientOcclusion')]
