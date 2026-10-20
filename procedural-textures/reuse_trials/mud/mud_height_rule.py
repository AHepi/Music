# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------
# MUD HEIGHT RULE: a tiny NEW box that sits AFTER COMBINE and makes the finished height from the finished colour by the MUD reference's own rule.
# It is the same 13-node idea as the brick trial's BRICK HEIGHT RULE (reuse_trials/brick/height_rule.py, written there; this is a copy with the mud
# numbers as defaults, so this folder does not depend on the other trial). It is only needed if COMBINE's built-in rule (written for slate, no setting
# changes it) does not fit mud: COMBINE makes height = 2.5 x (brightness - 9.5 of 255), cut to 0..1.
# The mud reference's height picture follows its colour: a straight line fitted ONCE to the reference height against the grey of the reference colour
# (reference_measures.json in this folder) gives height = 2.45 x (grey - 22) / 255, cut to 0..1 (the earlier mud recipe's own analysis found
# (grey - 20) / 108, which is slope 2.36 and zero point 20: the same line within the fit error).
# What it does: grey = 0.299 R + 0.587 G + 0.114 B of the screen colour (the colour turned from linear to screen values the same way COMBINE
# does it: Gamma 0.4545); height = Slope x (grey - Grey At Zero) / 255, cut to 0..1; then mixed with COMBINE's own height by Blend
# (1 = this rule only; 0 = COMBINE's height unchanged). It cannot do the reference rule's slight blur (a shader sees one dot at a time).
# Settings: 'mud_height_rule.blend', 'mud_height_rule.grey_at_zero', 'mud_height_rule.slope'. It reads nothing but the two sockets Colour and Height.
import sys

sys.dont_write_bytecode = True
import layer_interface as li  # noqa: E402  (from the frozen snapshot; the recipe puts the snapshot first on the search path)
from layer_interface import Control  # noqa: E402

LAYER_KEY = 'mud_height_rule'
GROUP_NAME = 'MUD HEIGHT RULE'
CONTROLS = [
    Control('blend', 'Blend', 1.0, 0.0, 1.0, 'how much of the finished height comes from this rule (1 = all of it; 0 = COMBINE\'s height unchanged)'),
    Control('grey_at_zero', 'Grey At Zero', 22.0, 0.0, 255.0, 'the grey (of 255) that becomes height 0; darker dots are cut to 0'),
    Control('slope', 'Slope', 2.45, 0.0, 10.0, 'how many height steps (of 255) one step of grey adds'),
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
    grey = b.add(b.add(b.mul(red, 0.299), b.mul(green, 0.587)), b.mul(blue, 0.114))
    rule = b.math('MULTIPLY', b.sub(grey, b.div(S('Grey At Zero'), 255.0)), S('Slope'), clamp=True)
    b.output('Height', b.mixf(S('Height'), rule, S('Blend')))
    return tree
