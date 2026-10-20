# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------
# METAL HEIGHT RULE: a tiny NEW box that can sit AFTER COMBINE. It makes the finished height from the finished colour by the metal
# reference's own rule, instead of COMBINE's built-in rule (written for slate; no setting changes it). It is the same idea as the brick
# trial's BRICK HEIGHT RULE (reuse_trials/brick/height_rule.py), written again here because metal's rule is a curve, not a straight line.
# The rule (measured once by the earlier metal analysis, stored in recipes/metal/description/maps_rule.json and quoted in the metal 04 Recipe,
# section 3.1): grey = 0.299 R + 0.587 G + 0.114 B of the screen colour (0..255); height = a 12-point tone curve of that grey (straight lines
# between the points; flat beyond the first and last). The curve is steep: grey 50 to 72 becomes height 100 to 171 of 255.
# The colour arrives from COMBINE as linear light; it is turned into screen values with the exact sRGB rule (1.055 x c^(1/2.4) - 0.055), the
# same rule Blender uses when it saves colour.png, so the grey here is the grey of the saved picture.
# It cannot do the reference rule's slight blur (0.7 dots): a shader sees one dot at a time.
# Settings: 'metal_height_rule.blend' (1 = this rule only; 0 = COMBINE's height unchanged). The curve points are fixed numbers below (they
# describe how the reference maps were made, not where anything is).
import sys

sys.dont_write_bytecode = True
import layer_interface as li  # noqa: E402  (from the frozen snapshot; the recipe puts the snapshot first on the search path)
from layer_interface import Control  # noqa: E402

LAYER_KEY = 'metal_height_rule'
GROUP_NAME = 'METAL HEIGHT RULE'
CURVE_GREY = [16.1, 37.8, 45.5, 50.0, 52.7, 55.1, 56.9, 59.1, 61.9, 65.8, 72.1, 104.1]
CURVE_HEIGHT = [4.9, 64.1, 86.8, 101.0, 109.3, 116.4, 122.2, 129.1, 137.8, 150.4, 171.5, 243.3]
CONTROLS = [
    Control('blend', 'Blend', 1.0, 0.0, 1.0, 'how much of the finished height comes from this rule (1 = all of it; 0 = COMBINE\'s height unchanged)'),
]


def build_group(parameters):
    values = li.resolve(LAYER_KEY, CONTROLS, parameters)
    inputs = [('Colour', 'colour', (0.5, 0.5, 0.5, 1.0), None, None, 'the finished colour from COMBINE'),
              ('Height', 'float', 0.5, None, None, 'the finished height from COMBINE')]
    inputs += [(c.label, c.kind, values[c.key], c.low, c.high, c.text) for c in CONTROLS]
    tree, b = li.make_plain_group(GROUP_NAME, inputs, [('Height', 'float', 'the finished height (0..1)')])
    S = b.input
    screen = []
    for channel in b.channels(S('Colour')):
        screen.append(b.math('MULTIPLY_ADD', b.power(b.mx(channel, 0.0), 1.0 / 2.4), 1.055, -0.055))
    grey = b.add(b.add(b.mul(screen[0], 0.299), b.mul(screen[1], 0.587)), b.mul(screen[2], 0.114))
    curve_node = b.node('ShaderNodeFloatCurve')
    curve = curve_node.mapping.curves[0]
    points = [(x / 255.0, y / 255.0) for x, y in zip(CURVE_GREY, CURVE_HEIGHT)]
    curve.points[0].location = points[0]
    curve.points[1].location = points[1]
    for point in points[2:]:
        curve.points.new(*point)
    for point in curve.points:
        point.handle_type = 'VECTOR'                    # straight lines between the points
    curve_node.mapping.update()
    b._put(curve_node, 'Factor', 1.0)
    b._put(curve_node, 'Value', grey)
    rule = curve_node.outputs['Value']
    b.output('Height', b.mixf(S('Height'), rule, S('Blend')))
    return tree
