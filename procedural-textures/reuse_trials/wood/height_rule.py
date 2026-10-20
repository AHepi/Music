# COPY NOTE (wood trial): copied from reuse_trials/brick/height_rule.py (a new box of the brick trial, not a shared layer). One line changed:
# GROUP_NAME 'BRICK HEIGHT RULE' -> 'WOOD HEIGHT RULE'. The wood values (grey at zero 12, slope 255/116 = 2.198, the wood reference's straight
# stretch of grey 12..128, recipes/wood/analysis/derivation_ceiling.json) are SETTINGS in settings.json; the text below is the brick original.
# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------
# BRICK HEIGHT RULE: a tiny NEW box that sits AFTER COMBINE. It makes the finished height from the finished colour by the brick reference's
# own rule, instead of COMBINE's built-in rule (which was written for slate and cannot be changed by a setting).
# Why it is needed: COMBINE's "tone blend" makes height = 2.5 x (brightness - 9.5 of 255), cut to 0..1: the slate reference's rule. The brick
# reference's height was made by a different rule (measured once by the earlier brick analysis and stored in
# recipes/brick/generator/sampler_model_brick.json as a 12-point tone curve on the grey of the colour). A straight line fitted to those 12
# points is height = 2.533 x (grey - 38.7 of 255) / 255 (worst miss 6.3 of 255). With slate's rule, every brick dot brighter than about 111 of
# 255 is cut off at the top (6.9 percent of the trial tile, against 0.1 percent in the reference), which flattens the height map.
# What it does: grey = 0.299 R + 0.587 G + 0.114 B of the screen colour (the colour turned from linear to screen values the same way COMBINE
# does it: Gamma 0.4545); height = Slope x (grey - Grey At Zero), cut to 0..1; then mixed with COMBINE's own height by Blend
# (1 = this rule only; 0 = COMBINE's height unchanged). It cannot do the reference rule's slight blur (a shader sees one dot at a time).
# Settings: 'height_rule.blend', 'height_rule.grey_at_zero', 'height_rule.slope'. It reads nothing but the two sockets Colour and Height.
import sys

sys.dont_write_bytecode = True
import layer_interface as li  # noqa: E402  (from the frozen snapshot; the recipe puts the snapshot first on the search path)
from layer_interface import Control  # noqa: E402

LAYER_KEY = 'height_rule'
GROUP_NAME = 'WOOD HEIGHT RULE'
CONTROLS = [
    Control('blend', 'Blend', 1.0, 0.0, 1.0, 'how much of the finished height comes from this rule (1 = all of it; 0 = COMBINE\'s height unchanged)'),
    Control('grey_at_zero', 'Grey At Zero', 38.7, 0.0, 255.0, 'the grey (of 255) that becomes height 0; darker dots are cut to 0'),
    Control('slope', 'Slope', 2.533, 0.0, 10.0, 'how many height steps (of 255) one step of grey adds'),
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
