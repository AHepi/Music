# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------
# GRAIN (new, small layer for the wood trial): the fine dry-brush streaks and hair-thin dark lines that run along wood. The shared paint layers
# make flat patches and specks, but not long thin streaks or hairlines; this layer adds them. It has exactly the same sockets as the shared layers
# (made by layer_interface.make_layer_group from the frozen snapshot), so COMBINE and the recipe treat it like any other layer.
#
# It does not invent the streak maker. It BORROWS, unchanged, the earlier wood build's "Wood Grain Gain" box (recipes/wood/generator/wood_shaders.py:
# seamless stretched noise cut at two levels for light and dark streaks, and the contour lines of another stretched noise for hairlines; 39 nodes).
# That box makes ONE number per dot, a brightness factor: 1 = leave alone, above 1 = lighter streak, below 1 = darker streak or line.
# A paint layer cannot multiply the colour below it (every layer works on its own and COMBINE paints over), so this layer turns the factor into paint:
#     factor below 1  -> paint the near-black Dark Colour with a mask of (1 - factor) x Dark Strength   (a near-black paint of that share
#                        darkens the colour below almost exactly as multiplying by the factor would)
#     factor above 1  -> paint the pale Light Colour with a mask of (factor - 1) x Light Strength
# and only on the board (piece_mask), never in the gaps.
#
# What it reads: Vector and Tile Count (the streaks are laid on the picture, not on each board: they run left to right, which is along the boards),
# piece_mask, its own controls and Seed. No other layer. Seed does not make new random numbers inside the borrowed box (its seeds are fixed in the
# box); it slides the whole streak pattern by a random amount, so another Seed gives the same kind of grain in other places.
# Outputs: Mask, Colour, Height (dark streaks a little low, light ones a little high), Roughness (0). Amount 0 switches the layer off (finish_layer).
# With more than one tile across (Tile Count above 1) the grain repeats once per base tile; the other layers do not.
# The numbers that shape the streaks (the "build" controls) are read when the box is built; they are the numbers written in the earlier wood
# build's description file S1_layout_paint_grain.json (maps.grain): 45 streaks across and 420 up (about 28 dots long and 3 tall), cuts 0.58 and
# 0.38, gains 1.8 and 0.55, hairlines 5 across and 150 up, thickness 0.012, gain 0.45. None of them comes from the reference pictures.
import importlib.util
import os
import sys

sys.dont_write_bytecode = True
import layer_interface as li  # noqa: E402  (from the frozen snapshot; the recipe puts the snapshot first on the search path)
from layer_interface import Control  # noqa: E402

LAYER_KEY = 'grain'
GROUP_NAME = 'GRAIN'
DEFAULT_SEED = 81.0
WOOD_SHADERS = os.path.join(li.PROC, 'recipes', 'wood', 'generator', 'wood_shaders.py')

CONTROLS = [
    Control('streaks_across', 'Streaks Across', 45.0, 1.0, 400.0, 'build setting: how many streak features fit across the tile left to right (45 = about 28 dots long)', build_time=True),
    Control('streaks_up', 'Streaks Up', 420.0, 10.0, 1500.0, 'build setting: how many streak features fit up the tile (420 = about 3 dots tall)', build_time=True),
    Control('streak_detail', 'Streak Detail', 1.5, 0.0, 8.0, 'build setting: more = more ragged streak edges', build_time=True),
    Control('light_cut', 'Light Cut', 0.58, 0.3, 0.9, 'build setting: the noise level above which a light streak starts (higher = fewer light streaks)', build_time=True),
    Control('dark_cut', 'Dark Cut', 0.38, 0.1, 0.7, 'build setting: the noise level below which a dark streak starts (lower = fewer dark streaks)', build_time=True),
    Control('light_gain', 'Light Gain', 1.8, 1.0, 3.0, 'build setting: how many times lighter a light streak is than the paint below', build_time=True),
    Control('dark_gain', 'Dark Gain', 0.55, 0.0, 1.0, 'build setting: how much of its brightness a dark streak keeps (0.55 = 45 percent darker)', build_time=True),
    Control('hair_across', 'Hairlines Across', 5.0, 1.0, 100.0, 'build setting: hairline noise features across the tile', build_time=True),
    Control('hair_up', 'Hairlines Up', 150.0, 10.0, 600.0, 'build setting: hairline noise features up the tile (more = more, closer lines)', build_time=True),
    Control('hair_thickness', 'Hairline Thickness', 0.012, 0.001, 0.1, 'build setting: how far from the noise\'s middle level a hairline reaches (bigger = thicker lines)', build_time=True),
    Control('hair_gain', 'Hairline Gain', 0.45, 0.0, 1.0, 'build setting: how much of its brightness a hairline keeps (0.45 = 55 percent darker)', build_time=True),
    Control('dark_strength', 'Dark Strength', 1.0, 0.0, 1.0, 'how strongly the dark streaks and hairlines cover the paint below (1 = as the factor says)'),
    Control('light_strength', 'Light Strength', 0.6, 0.0, 1.0, 'how strongly the light streaks cover the paint below'),
    Control('dark_colour', 'Dark Colour', '#120d0b', kind='colour', text='the near-black paint of dark streaks and hairlines'),
    Control('light_colour', 'Light Colour', '#b08a62', kind='colour', text='the pale paint of light streaks'),
    Control('dark_sink', 'Dark Sink', 0.01, 0.0, 0.1, 'how much a fully dark streak sinks the surface (height scale 0..1)'),
    Control('light_raise', 'Light Raise', 0.01, 0.0, 0.1, 'how much a fully light streak raises the surface (height scale 0..1)'),
]
DECLARED_LINKS = []          # GRAIN reads no other layer


def _borrowed_shaders():
    """The earlier wood build's shader file, loaded from where it lies and left untouched."""
    spec = importlib.util.spec_from_file_location('wood_shaders_borrowed', WOOD_SHADERS)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_group(parameters):
    values = li.resolve(LAYER_KEY, CONTROLS, parameters)
    grain = {'hatch': {'u': values['streaks_across'], 'v': values['streaks_up'], 'detail': values['streak_detail'], 'seed': 3.0,
                       'light_cut': values['light_cut'], 'dark_cut': values['dark_cut'], 'light_gain': values['light_gain'], 'dark_gain': values['dark_gain']},
             'hair': {'u': values['hair_across'], 'v': values['hair_up'], 'seed': 5.0, 'thickness': values['hair_thickness'], 'gain': values['hair_gain']}}
    tree, b = li.make_layer_group(GROUP_NAME, LAYER_KEY, CONTROLS, parameters, DEFAULT_SEED, DECLARED_LINKS)
    S = b.input
    g = b.bundle()

    # ---- the borrowed streak box, fed the picture coordinate (once per base tile) slid by a random amount that depends on Seed
    slide = b.channels(b.hash4(b.vec(S('Seed'), 0.5, 0.5), 3.0).outputs['Color'])
    position = b.vmath('ADD', b.vmath('SCALE', S('Vector'), None, scale=S('Tile Count')), b.vec(slide[0], slide[1], 0.0))
    gain_node = b.node('ShaderNodeGroup')
    gain_node.node_tree = _borrowed_shaders().grain_gain_group(grain, name=li.unique_name('Wood Grain Gain'))
    gain_node.label = 'Wood Grain Gain (borrowed, unchanged)'
    b._put(gain_node, 'Vector', position)
    factor = gain_node.outputs['Gain']

    # ---- the factor turned into paint
    dark = b.clamp01(b.sub(1.0, factor))
    light = b.clamp01(b.sub(factor, 1.0))
    share_dark = b.div(dark, b.mx(b.add(dark, light), 1e-4))
    mask = b.mul(b.add(b.mul(dark, S('Dark Strength')), b.mul(light, S('Light Strength'))), g['piece_mask'])
    colour = b.mix(S('Light Colour'), S('Dark Colour'), share_dark)
    height = b.mul(b.sub(b.mul(light, S('Light Raise')), b.mul(dark, S('Dark Sink'))), g['piece_mask'])
    b.finish_layer(mask=mask, colour=colour, height=height, roughness=0.0)
    return tree
