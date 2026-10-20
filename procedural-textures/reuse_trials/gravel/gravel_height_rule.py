# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------
# GRAVEL HEIGHT RULE: a tiny NEW box that sits AFTER COMBINE (the same idea as the brick trial's height box, written again here with the gravel
# numbers). It makes the finished height from the finished colour by the gravel reference's own rule, instead of COMBINE's built-in rule, which
# was written for slate and cannot be changed by a setting (a lesson of the brick trial).
# The rule: the gravel reference's height picture was made from its colour picture as a mix of the three colour numbers. The earlier gravel
# build found the best mix once from the reference maps (recipes/gravel/description/S_v4.json, "maps"/"height"; recipes/gravel/analysis/
# derivation_ceiling.py): height (of 255) = (267.15 x red + 91.48 x green + 210.5 x blue) / 255 - 17.7, with red, green and blue as the usual
# screen numbers 0..255. Those are the defaults below, so the only numbers taken from the reference maps here are those four, and they are
# taken because height-from-colour is how the reference maps were made (so a colour that is right brings a height that is right).
# What it does: turns the finished colour from linear to screen values (Gamma 0.4545, the way COMBINE does it), applies the mix, cuts to 0..1,
# then mixes the result with COMBINE's own height by Blend (1 = this rule only; 0 = COMBINE's height unchanged, which keeps the layout's dips and
# domes). It cannot do the reference rule's slight blur (a shader sees one dot at a time).
# Settings: 'height_rule.blend', 'height_rule.red_weight', 'height_rule.green_weight', 'height_rule.blue_weight', 'height_rule.offset'.
import sys

sys.dont_write_bytecode = True
import layer_interface as li  # noqa: E402  (from the frozen snapshot; the recipe puts the snapshot first on the search path)
from layer_interface import Control  # noqa: E402

LAYER_KEY = 'height_rule'
GROUP_NAME = 'GRAVEL HEIGHT RULE'
CONTROLS = [
    Control('blend', 'Blend', 1.0, 0.0, 1.0, 'how much of the finished height comes from this rule (1 = all of it; 0 = COMBINE\'s height unchanged)'),
    Control('red_weight', 'Red Weight', 267.15, 0.0, 600.0, 'how many height steps (of 255) the full red number adds'),
    Control('green_weight', 'Green Weight', 91.48, 0.0, 600.0, 'how many height steps (of 255) the full green number adds'),
    Control('blue_weight', 'Blue Weight', 210.5, 0.0, 600.0, 'how many height steps (of 255) the full blue number adds'),
    Control('offset', 'Offset', -17.7, -255.0, 255.0, 'height steps (of 255) added after the mix; the height is then cut to 0..1'),
]


def build_group(parameters):
    values = li.resolve(LAYER_KEY, CONTROLS, parameters)
    inputs = [('Colour', 'colour', (0.5, 0.5, 0.5, 1.0), None, None, 'the finished colour from COMBINE'),
              ('Height', 'float', 0.5, None, None, 'the finished height from COMBINE')]
    inputs += [(c.label, c.kind, values[c.key], c.low, c.high, c.text) for c in CONTROLS]
    tree, b = li.make_plain_group(GROUP_NAME, inputs, [('Height', 'float', 'the finished height (0..1)')])
    S = b.input
    gamma = b.node('ShaderNodeGamma')
    b._put(gamma, 'Color', S('Colour'))
    b._put(gamma, 'Gamma', 0.4545)
    red, green, blue = b.channels(gamma.outputs[0])
    mix = b.add(b.add(b.mul(red, S('Red Weight')), b.mul(green, S('Green Weight'))), b.mul(blue, S('Blue Weight')))
    rule = b.math('MULTIPLY', b.add(mix, S('Offset')), 1.0 / 255.0, clamp=True)
    b.output('Height', b.mixf(S('Height'), rule, S('Blend')))
    return tree
