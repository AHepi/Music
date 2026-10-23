"""What this does: the common base every wear layer is built on. A layer is ONE node group (a packaged recipe of node boxes) that sits in a material's chain. Its interface
is fixed so the chain can wire any layer into any material: the six bundle inputs (Colour, Roughness, Specular IOR Level, Coat Weight, Normal, Metallic), the masks it
asks for by name ("M Footfall", "M Dampness" ...; the chain wires them from the material's Plan node), "Amount" (the master amount), "Seed", "Dot Metres" (how big one
picture dot is in metres, so marks are sized in picture dots), and one input per dial; its outputs are the same bundle and "Mask" (the layer's own mask, for checking).
Habits every layer keeps (each one is tested): AMOUNT 0 gives EXACTLY the input (every effect is mixed in by a factor that contains the amount, and a mix at 0 is exact); the
effect is also multiplied by the object's own property pk_<layer>_amount, which is 0 on any object that has none (an Attribute node on an object without the property
reads 0 in every renderer: a missing amount silently switches the layer off, which is why the audit checks it); random numbers come from the object's seed, the layer's Seed
and the position, never a name; at most about 150 nodes and three noise or Voronoi nodes; no Bevel, Ambient Occlusion or Pointiness node. It needs Blender (bpy).
A concrete example: layer = LayerBase('dirt', masks=['footfall']); fac = layer.multiply(layer.amount, layer.mask('Footfall')); layer.finish(colour=layer.mix_colour(fac, layer.group_input('Colour'), soil)).
"""
import bpy

from .. import names
from . import dials as dials_module
from .nodes import Net, new_group

GROUP_VERSION = 5
BUNDLE_SOCKETS = [('Colour', 'NodeSocketColor', (0.5, 0.5, 0.5, 1.0)), ('Roughness', 'NodeSocketFloat', 0.5), ('Specular IOR Level', 'NodeSocketFloat', 0.5),
                  ('Coat Weight', 'NodeSocketFloat', 0.0), ('Normal', 'NodeSocketVector', (0.0, 0.0, 1.0)), ('Metallic', 'NodeSocketFloat', 0.0)]
SHORT_TO_SOCKET = {'colour': 'Colour', 'roughness': 'Roughness', 'specular': 'Specular IOR Level', 'coat': 'Coat Weight', 'normal': 'Normal', 'metallic': 'Metallic'}
MASK_DEFAULTS = {'Above Water': 1.0, 'Wall Dist': 4.0, 'Prop Dist': 4.0, 'Litter Dist': 1.0, 'Edge Dist': 1.0, 'Up': 0.5, 'Verge Dist': 2.0, 'Joint Dist': 1.0}


def mask_socket(mask):
    return 'M ' + mask


class LayerBase:
    """Makes a layer's node group with the standard interface and gives the builder the pieces it needs (see the note at the top)."""

    def __init__(self, key, masks=()):
        self.key = key
        table, _ = dials_module.table_defaults(key)
        self.dial_names = [d for d in table if d not in ('amount', 'seed')]
        inputs = list(BUNDLE_SOCKETS)
        for mask in masks:
            inputs.append((mask_socket(mask), 'NodeSocketFloat', MASK_DEFAULTS.get(mask, 0.0)))
        inputs += [('Amount', 'NodeSocketFloat', 1.0), ('Seed', 'NodeSocketFloat', 0.0), ('Dot Metres', 'NodeSocketFloat', 0.01)]
        for dial in self.dial_names:
            inputs.append((dials_module.socket_name(dial), 'NodeSocketFloat', float(table[dial])))
        outputs = [(name, kind) for name, kind, _ in BUNDLE_SOCKETS] + [('Mask', 'NodeSocketFloat')]
        existing = bpy.data.node_groups.get(names.layer_group_name(key))
        if existing is not None:
            existing.name = existing.name + ' (old)'
            if existing.users == 0:
                bpy.data.node_groups.remove(existing)
        self.tree, self.gin, self.gout = new_group(names.layer_group_name(key), inputs, outputs)
        self.tree['pk_version'] = GROUP_VERSION
        self.net = Net(self.tree)
        self.masks = list(masks)
        self.position = self.net.geometry().outputs['Position']
        role_amount = self.net.attr(names.layer_amount_name(key))
        self.amount = self.net.math('MULTIPLY', self.net.math('MAXIMUM', self.group_input('Amount'), 0.0), self.net.math('MAXIMUM', role_amount, 0.0))
        self.object_seed = self.net.attr(names.SEED)

    # ---- inputs
    def group_input(self, name):
        return self.gin.outputs[name]

    def mask(self, name):
        return self.group_input(mask_socket(name))

    def dial(self, name):
        """A dial's input by its name, written either way: 'foot_height_metres' or 'Foot Height Metres'."""
        return self.group_input(dials_module.socket_name(name.lower().replace(' ', '_')))

    # ---- small helpers (each returns an output socket)
    def multiply(self, a, b):
        return self.net.math('MULTIPLY', a, b)

    def add(self, a, b):
        return self.net.math('ADD', a, b)

    def sub(self, a, b):
        return self.net.math('SUBTRACT', a, b)

    def maximum(self, a, b):
        return self.net.math('MAXIMUM', a, b)

    def minimum(self, a, b):
        return self.net.math('MINIMUM', a, b)

    def clamp(self, a):
        return self.net.clamp01(a)

    def smooth_between(self, value, low, high):
        return self.net.smoothstep(value, low, high)

    def one_minus(self, a):
        return self.net.one_minus(a)

    def mix_colour(self, fac, a, b):
        return self.net.mix_colour(fac, a, b)

    def mix(self, fac, a, b):
        return self.net.mix(fac, a, b)

    def noise(self, per_metre, detail=3.0, stretch=(1.0, 1.0, 1.0), shift=0.0):
        """A fractal noise (about 0.5 on average) whose features are about 1/per_metre metres across, different for every object and every Seed.
        per_metre is a plain number or a socket. stretch lengthens features along an axis (x, y, z): (1, 1, 0.15) makes streaks that run down a wall
        (plain numbers only)."""
        net = self.net
        shift_vector = net.combine(self.add(self.multiply(self.object_seed, 31.7 + shift), self.multiply(self.group_input('Seed'), 0.37)), self.multiply(self.object_seed, 17.1), self.add(self.multiply(self.group_input('Seed'), 0.91), self.multiply(self.object_seed, 5.3)))
        if isinstance(per_metre, bpy.types.NodeSocket):
            scaled = net.scale_vector(self.position, per_metre)
        else:
            scaled = net.vector_math('MULTIPLY', self.position, net.combine(per_metre * stretch[0], per_metre * stretch[1], per_metre * stretch[2]))
        moved = net.vector_math('ADD', scaled, shift_vector)
        return net.noise(moved, scale=1.0, detail=detail, roughness=0.55)

    def floor_size(self, metres):
        """At least three picture dots wide (never thinner than the picture can show): the larger of the asked size and 3 x Dot Metres."""
        return self.maximum(metres, self.multiply(self.group_input('Dot Metres'), 3.0))

    def lighten(self, colour, value=1.4, saturation=0.85):
        return self.net.hue_saturation_value(colour, saturation=saturation, value=value)

    def darken(self, colour, share):
        return self.net.hue_saturation_value(colour, value=self.sub(1.0, share))

    # ---- outputs
    def finish(self, mask=None, **outputs):
        """Links the outputs given by their lower-case names (colour, roughness, specular, coat, normal, metallic); every other output passes its input through."""
        links = self.tree.links
        given = {SHORT_TO_SOCKET[k]: v for k, v in outputs.items() if v is not None}
        for socket in self.gout.inputs:
            if socket.name == 'Mask':
                if mask is not None:
                    links.new(mask, socket)
                continue
            links.new(given.get(socket.name, self.gin.outputs[socket.name]), socket)
        return self.tree


def linear(r, g, b):
    """A colour written in sRGB 0..255 as the linear RGBA the nodes want."""
    def channel(v):
        v = v / 255.0
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    return (channel(r), channel(g), channel(b), 1.0)
