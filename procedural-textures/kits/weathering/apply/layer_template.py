# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# THE LAYER TEMPLATE: a documented layer that does NOTHING at its default (and a little, on request), showing every habit a real layer must have. Copy it to start a layer.
# A layer is one NODE GROUP (a packaged recipe of node boxes) that sits in a material's chain (chain.py). Read this file top to bottom once.
#
# 1. THE SOCKETS (the group's interface; LayerBase makes them for you)
#    in  : the bundle  Colour, Roughness, Specular IOR Level, Coat Weight, Normal, Metallic and Wet Normal (the smoothed normal of the water layer; change it the same way
#          as Normal or leave it out and the chain goes around you);
#          masks by NAME: 'M Sheltered', 'M Drip' ... (names.py; the bus wires them; a mask you do not declare costs nothing; a mask the set has not made reads its default);
#          from the earlier layers: 'Wet Mask', 'Puddle Mask' (only a layer AFTER the water layer gets them; slot A reads 0);
#          from the scale helper WK SCALE: 'Dot Across', 'Dot Along', 'Fade Near', 'Far Blend' (metres per plate dot and distance fades, scale.py);
#          the dials, one input each named in Title Case ('Amount', 'Seed', 'Inflate Limit', 'Fade Start', 'Fade End', 'Wet Follow', then the layer's own).
#    out : the same bundle (an output you leave unconnected passes its input through) and 'Mask' (the layer's own mask, raw, for debug views: kit.show_mask).
# 2. THE MASTER DIAL. The effect strength is multiplied by 'Amount' and by the object's own role amount (object value wk_<layer>_amount: 1 on the roles the set names, 0 on
#    everything else, so a material shared by two kinds of object is only weathered where the set says). Amount 0 must give EXACTLY the input: every mix factor is a product
#    that contains the amount, and nothing can become NaN (NaN times 0 is NaN: clamp before dividing).
# 3. SCALE. All marks are sized in PLATE DOTS (one dot of the plate picture). 'Dot Across' is metres per plate dot at this point; a mark of 3 dots is 3 x Dot Across wide;
#    never thinner than the layer's minimum, never wider than 'Inflate Limit' times its real size (beyond that it fades into the layer's average tone, not into clean).
# 4. FADE. Fine detail fades with 'Fade Near' to the layer's AVERAGE tone (never to the clean surface); relief (a Bump on the incoming Normal) fades with it too.
# 5. SEEDS. Random numbers come from the object's wk_seed (an Attribute node) and the layer's own 'Seed' dial, and from position: never from the name of the object.
# 6. TAGS. The chain tags the node it puts in (node['wk'] = the layer's key, node['wk_slot'] = 'A', 'B' or 'C'); put your own helper nodes inside the group, not in the material.
# 7. COST. At most about 150 nodes, at most three noise or Voronoi nodes, Linear image look-ups only, no Bevel, Ambient Occlusion or Pointiness nodes.
# Register the layer with the kit:   kit.register_layer('mylayer', build_group, slot='A')   (build_group(key) returns this file's group tree).
import bpy

from . import dials as dials_module
from . import nodes

try:
    from masks import names as mask_names
except ImportError:                                                    # the masks package is optional for the core
    mask_names = None

BUNDLE_SOCKETS = [('Colour', 'NodeSocketColor', (0.5, 0.5, 0.5, 1.0)), ('Roughness', 'NodeSocketFloat', 0.5), ('Specular IOR Level', 'NodeSocketFloat', 0.5),
                  ('Coat Weight', 'NodeSocketFloat', 0.0), ('Normal', 'NodeSocketVector', (0.0, 0.0, 1.0)), ('Metallic', 'NodeSocketFloat', 0.0),
                  ('Wet Normal', 'NodeSocketVector', (0.0, 0.0, 1.0))]
SCALE_SOCKETS = [('Dot Across', 'NodeSocketFloat', 0.003), ('Dot Along', 'NodeSocketFloat', 0.003), ('Fade Near', 'NodeSocketFloat', 1.0), ('Far Blend', 'NodeSocketFloat', 0.0)]
WET_SOCKETS = [('Wet Mask', 'NodeSocketFloat', 0.0), ('Puddle Mask', 'NodeSocketFloat', 0.0)]


def socket_name(dial):
    """The group input for a dial: 'film_mult' -> 'Film Mult'."""
    return ' '.join(w.capitalize() for w in dial.split('_'))


def mask_default(name):
    return mask_names.default_of(name) if mask_names is not None and name in mask_names.BY_NAME else 0.0


class LayerBase:
    """Makes a layer's node group with the standard interface and gives the builder the pieces it needs.
        layer = LayerBase('soot', 'WK SOOT', masks=['sheltered', 'drip'])
        n, g = layer.n, layer.g                       # n = Net (node maker), g(name) = a group input by socket name ('Amount', 'M Drip', 'Dot Across' ...)
        layer.amount                                  # the effective amount: Amount x the object's role amount (a socket)
        ... build with n.math / n.mix_colour ...
        layer.finish(colour=new_colour, mask=my_mask)  # links the outputs you give; every other output passes its input through
        tree = layer.tree
    """

    def __init__(self, key, group_name, masks=(), dial_names=None, wet_normal=True, wet_masks=True, scale=True):
        self.key = key
        table = dials_module.TABLE.layers.get(key)
        names = list(dial_names) if dial_names is not None else (table.names() if table else [r['name'] for r in dials_module.TABLE.common])
        inputs = [s for s in BUNDLE_SOCKETS if wet_normal or s[0] != 'Wet Normal']
        for mask in masks:
            inputs.append((mask_names.mask_socket(mask) if mask_names else 'M ' + mask.title(), 'NodeSocketFloat', mask_default(mask)))
        if wet_masks:
            inputs += WET_SOCKETS
        if scale:
            inputs += SCALE_SOCKETS
        for dial in names:
            default = table.row(dial)['default'] if table and table.row(dial) else dials_module.TABLE.common[0]['default']
            inputs.append((socket_name(dial), 'NodeSocketFloat', float(default)))
        outputs = [(s[0], s[1]) for s in BUNDLE_SOCKETS if wet_normal or s[0] != 'Wet Normal'] + [('Mask', 'NodeSocketFloat')]
        self.tree, self.gin, self.gout = nodes.new_group(group_name, inputs, outputs)
        self.n = nodes.Net(self.tree)
        self.dial_names = names
        role_amount = self.n.attr(dials_module.object_attribute_name(key, 'amount'))
        self.amount = self.n.math('MULTIPLY', self.n.math('MAXIMUM', self.g('Amount'), 0.0), role_amount)

    def g(self, name):
        return self.gin.outputs[name]

    def dial(self, dial):
        """The group input of one dial."""
        return self.g(socket_name(dial))

    def finish(self, mask=None, **outputs):
        """Links the outputs given by their lower-case names (colour, roughness, specular, coat, normal, metallic, wet_normal); passes the others through."""
        mapping = {'colour': 'Colour', 'roughness': 'Roughness', 'specular': 'Specular IOR Level', 'coat': 'Coat Weight', 'normal': 'Normal', 'metallic': 'Metallic',
                   'wet_normal': 'Wet Normal'}
        links = self.tree.links
        for socket in self.gout.inputs:
            if socket.name == 'Mask':
                if mask is not None:
                    links.new(mask, socket)
                else:
                    socket.default_value = 0.0
                continue
            given = None
            for short, long_name in mapping.items():
                if long_name == socket.name and outputs.get(short) is not None:
                    given = outputs[short]
            links.new(given if given is not None else self.gin.outputs[socket.name], socket)
        return self.tree


def build_template(key='template', demo_tint=(0.8, 0.5, 0.2, 1.0)):
    """The do-nothing layer. With the dial 'Demo' at 0 the outputs equal the inputs exactly; raise Demo and Amount and it tints Colour (on the roles the set names) so a test
    can see that the layer is in the material. Shows the mask inputs by name ('M Sheltered', 'M Height'), the scale inputs, the master amount and the role amount."""
    if 'template' not in dials_module.TABLE.layers or dials_module.TABLE.layers['template'].row('demo') is None:
        dials_module.register_layer('template', [dict(name='demo', lo=0.0, hi=1.0, unit='', default=0.0, doc='Template only: how strongly the layer tints Colour (0 = does nothing).')])
    if key != 'template' and key not in dials_module.TABLE.layers:
        dials_module.register_layer(key, [dict(name='demo', lo=0.0, hi=1.0, unit='', default=0.0, doc='Template only: how strongly the layer tints Colour (0 = does nothing).')])
    layer = LayerBase(key, f'WK TEMPLATE {key}', masks=['sheltered', 'height'])
    n = layer.n
    demo = n.math('MAXIMUM', layer.dial('demo'), 0.0)
    # the effect's strength: master amount x role amount x the demo dial x a mask (here: more under shelter and low down, to show two masks being read by name)
    mask = n.math('MULTIPLY', n.math('MAXIMUM', layer.g('M Sheltered'), n.one_minus(n.smoothstep(layer.g('M Height'), 0.0, 1.0))), 1.0)
    fac = n.math('MULTIPLY', n.math('MULTIPLY', layer.amount, demo), n.math('MAXIMUM', mask, 0.25), clamp=True)
    tinted = n.mix_colour(fac, layer.g('Colour'), demo_tint)
    return layer.finish(colour=tinted, mask=fac)
