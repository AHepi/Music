# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------
# COMBINE stacks the layers and makes the four finished maps. It is the only place where layers meet.
#   * COLOUR: start with the bottom layer's Colour everywhere (COLOUR AND FADE). Then, layer by layer in the stack order, paint the
#     next layer's Colour over it wherever that layer's Mask is: colour = mix(colour so far, layer Colour, layer Mask).
#   * HEIGHT: the layout's base_height PLUS every layer's Height (each already 0 where the layer does nothing). Cut to 0..1. Then (setting
#     tone_blend, added in the integration round) a share of it is replaced by the brightness of the finished colour, the way the reference maps were made.
#   * ROUGHNESS: a base roughness PLUS every layer's Roughness change. Cut to 0..1.
#   * METALLIC: one number for the whole surface (slate is not metal: 0).
# The stack order is a build setting 'recipe.stack_order' (names separated by commas, bottom first). The default is
# colour_and_fade, moss, damage, outline_and_shadow: moss grows on the slate, damage breaks through the moss, the dark outline is drawn
# last. The order only decides who paints over whom; heights and roughness are plain sums.
# Sockets of this group: inputs 'base_height' and, for every layer name, '<name> Mask', '<name> Colour', '<name> Height',
# '<name> Roughness' (for example 'moss Mask'); controls 'Base Roughness', 'Metallic'; outputs 'Colour', 'Roughness', 'Metallic', 'Height'.
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import layer_interface as li  # noqa: E402
from layer_interface import Control  # noqa: E402

LAYER_KEY = 'combine'
GROUP_NAME = 'COMBINE'
DEFAULT_STACK = ['colour_and_fade', 'moss', 'damage', 'outline_and_shadow']
CONTROLS = [
    Control('base_roughness', 'Base Roughness', 0.80, 0.0, 1.0, 'roughness of the bare slate before any layer changes it (0 = mirror, 1 = completely matt)'),
    Control('metallic', 'Metallic', 0.0, 0.0, 1.0, 'metallic for the whole surface (slate: 0)'),
    Control('tone_blend', 'Tone Blend', 0.0, 0.0, 1.0, 'how much of the finished height is taken from the paint brightness instead of from the real relief (0 = real relief only: chips sunk, moss raised; 1 = the finished height is the brightness of the finished colour, the way the reference maps were made; 0.4 = in between) - added in the integration round'),
    Control('height_gain', 'Height Gain', 1.0, 0.0, 10.0, 'multiplies the layers\' heights before they are added to base_height (1 = as the layers wrote them)'),
]


def build_group(parameters):
    values = li.resolve(LAYER_KEY, CONTROLS, parameters)
    stack = [name.strip() for name in str(parameters.get('recipe.stack_order', ','.join(DEFAULT_STACK))).split(',') if name.strip()]
    inputs = [('base_height', 'float', 0.5, None, None, 'the layout\'s bare relief (0..1)')]
    for name in stack:
        inputs += [(f'{name} Mask', 'float', 0.0, None, None, f'where {name} paints (0..1)'),
                   (f'{name} Colour', 'colour', (0.5, 0.5, 0.5, 1.0), None, None, f'the colour {name} paints'),
                   (f'{name} Height', 'float', 0.0, None, None, f'the height change {name} makes (0 = none)'),
                   (f'{name} Roughness', 'float', 0.0, None, None, f'the roughness change {name} makes (0 = none)')]
    for control in CONTROLS:
        inputs.append((control.label, control.kind, values[control.key], control.low, control.high, control.text))
    outputs = [('Colour', 'colour', 'the finished colour'), ('Roughness', 'float', 'the finished roughness (0..1)'),
               ('Metallic', 'float', 'the finished metallic (0..1)'), ('Height', 'float', 'the finished height (0..1)')]
    tree, b = li.make_plain_group(GROUP_NAME, inputs, outputs)

    colour = b.input(f'{stack[0]} Colour')                       # the bottom layer paints everywhere
    for name in stack[1:]:
        colour = b.mix(colour, b.input(f'{name} Colour'), b.input(f'{name} Mask'))
    layer_heights = b.sum_of([b.input(f'{name} Height') for name in stack])
    height = b.math('MULTIPLY_ADD', layer_heights, b.input('Height Gain'), b.input('base_height'), clamp=True)
    # tone blend: the reference's height maps were made from the colour (height = 2.5 x (brightness - 9.5), cut to 0..255). Mix that into the real relief.
    brightness = b.height_from_colour(colour)
    derived = b.math('MULTIPLY', b.sub(brightness, 9.5 / 255.0), 2.5, clamp=True)
    height = b.mixf(height, derived, b.input('Tone Blend'))
    layer_roughness = b.sum_of([b.input(f'{name} Roughness') for name in stack])
    roughness = b.add(b.input('Base Roughness'), layer_roughness)
    roughness = b.math('ADD', roughness, 0.0, clamp=True)
    b.output('Colour', colour)
    b.output('Height', height)
    b.output('Roughness', roughness)
    b.output('Metallic', b.input('Metallic'))
    return tree
