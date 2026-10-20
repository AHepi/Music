# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------
# STONES is a NEW paint layer for the mud trial: dark, angular stones with a lit face (light from the upper left). No shared layer can draw an
# angular stone with a lit side (MOSS's lichen discs and DAMAGE's pits are round and flat), so this layer exists. It has exactly the same sockets as
# every shared layer (Vector, Tile Count, the eleven layout numbers, Seed, Amount, then its own controls; outputs Mask, Colour, Height, Roughness).
#
# It does NOT invent the stone shapes: it calls the project's existing stone maker, stone_tools.polygon_stones in lib/contrib/stone_tools.py, UNCHANGED.
# That helper cuts the picture into a grid of whole cells (so the tile repeats), puts at most one stone in each cell, and makes the stone the part
# of the cell inside five straight edges (a random five-sided polygon), with a flat face per edge. It hands back: where the stone is (mask), a thin ring
# just inside its edge (outline), how much the flat face under this dot faces the light (face), and random numbers that are the same over one stone.
# This layer calls it three times (a fine grid of small stones, a grid of medium stones and a coarse grid of a few big stones) and only adds the PAINT:
#   * every stone gets a base grey from a small palette of stone greys (a random pick per stone, and a few warm tan stones),
#   * each flat face is painted one to two palette steps lighter if it faces the light, so a stone has a lit side and a shadow side,
#   * the thin ring just inside the edge is the second darkest grey,
#   * the stone raises the surface and is a little rougher,
#   * the small and medium stones GATHER: a slow seamless noise, read at the middle of each stone's own cell, switches whole stones off in some
#     regions, so stones come in groups with bare ground between (the reference has stones gathered round the big ones).
# What it reads: Vector, Tile Count and its own controls. The stone helper needs plain numbers (not sockets) for its seed and sizes, so the
# seed and every count and size are read when the box is built (they are "build" settings; changing one means building the box again, which the
# settings do anyway). The colours are ordinary sockets. It reads no other layer. Amount 0 switches it off (the shared finish_layer guarantees it).
import os
import sys

sys.dont_write_bytecode = True
import layer_interface as li  # noqa: E402  (from the frozen snapshot)
from layer_interface import Control  # noqa: E402

PROC = li.PROC
CONTRIB = os.path.join(PROC, 'lib', 'contrib')
if CONTRIB not in sys.path:
    sys.path.insert(0, CONTRIB)
import stone_tools  # noqa: E402  (the project's own helper, used unchanged)

LAYER_KEY = 'stones'
GROUP_NAME = 'STONES'
DEFAULT_SEED = 61.0
PALETTE_NAMES = ['Stone Tone 1 (darkest)', 'Stone Tone 2', 'Stone Tone 3', 'Stone Tone 4', 'Stone Tone 5', 'Stone Tone 6 (lightest)']
PALETTE_DEFAULTS = ['#151112', '#26272b', '#40424a', '#60524d', '#726d69', '#8d8782']

CLASSES = ['small', 'medium', 'big']          # three grids of stones, smallest first (a bigger stone is painted over a smaller one)
CONTROLS = [
    Control('small_cells', 'Small Stone Cells', 44, 4, 96, 'how many grid cells across one base tile for the small stones (44 = a cell about 28 dots)', build_time=True),
    Control('small_presence', 'Small Stone Presence', 0.4, 0.0, 1.0, 'share of those cells that hold a small stone', build_time=True),
    Control('small_radius_low', 'Small Radius Low', 0.17, 0.05, 0.5, 'smallest small stone, as a share of its cell (0.5 would touch the cell border)', build_time=True),
    Control('small_radius_high', 'Small Radius High', 0.33, 0.05, 0.5, 'biggest small stone, as a share of its cell', build_time=True),
    Control('medium_cells', 'Medium Stone Cells', 22, 4, 64, 'how many grid cells across one base tile for the medium stones (22 = a cell about 57 dots)', build_time=True),
    Control('medium_presence', 'Medium Stone Presence', 0.3, 0.0, 1.0, 'share of those cells that hold a medium stone', build_time=True),
    Control('medium_radius_low', 'Medium Radius Low', 0.17, 0.05, 0.5, 'smallest medium stone, as a share of its cell', build_time=True),
    Control('medium_radius_high', 'Medium Radius High', 0.35, 0.05, 0.5, 'biggest medium stone, as a share of its cell', build_time=True),
    Control('big_cells', 'Big Stone Cells', 8, 2, 32, 'how many grid cells across one base tile for the few big stones (8 = a cell about 157 dots)', build_time=True),
    Control('big_presence', 'Big Stone Presence', 0.15, 0.0, 1.0, 'share of those cells that hold a big stone', build_time=True),
    Control('big_radius_low', 'Big Radius Low', 0.1, 0.05, 0.5, 'smallest big stone, as a share of its cell', build_time=True),
    Control('big_radius_high', 'Big Radius High', 0.26, 0.05, 0.5, 'biggest big stone, as a share of its cell', build_time=True),
    Control('gather', 'Gather', 0.6, 0.0, 1.0, 'how much the small and medium stones gather into groups with bare ground between (0 = spread evenly, 1 = only in a few groups); the big stones are not gathered', build_time=True),
    Control('gather_features', 'Gather Features', 6.0, 1.0, 30.0, 'how many groups (noise features) fit across one base tile', build_time=True),
    Control('warp', 'Warp', 0.4, 0.0, 1.0, 'how far (in cells) a slow wobble bends the grid so stones do not sit in rows', build_time=True),
    Control('outline_width', 'Outline Width', 0.0028, 0.0, 0.02, 'width of the dark ring just inside the stone edge, in tile units (0.0028 = 3.5 dots)', build_time=True),
    Control('tone_bias', 'Tone Bias', 0.8, 0.0, 2.0, 'which greys the stones start at: a stone gets palette grey floor(2 x its random number + this) (0 = the two darkest, 0.8 = mostly the middle ones, 1.5 = the lighter ones), then 0 to 2 more on a lit face', build_time=True),
    Control('warm_share', 'Warm Share', 0.05, 0.0, 0.5, 'share of stones that are warm tan (lit earth-coloured stones) instead of grey', build_time=True),
    Control('warm_colour', 'Warm Stone Colour', '#8c6246', kind='colour', text='the colour of a warm tan stone on its lit face (darker faces are dimmed)'),
    Control('raise', 'Raise', 0.15, 0.0, 0.5, 'how far a stone stands above the ground (0..1 relief scale)'),
] + [Control(f'tone_{i + 1}', PALETTE_NAMES[i], PALETTE_DEFAULTS[i], kind='colour', text='stone grey number %d of 6 (darkest to lightest)' % (i + 1)) for i in range(6)]
DECLARED_LINKS = []          # STONES reads no other layer


def build_group(parameters):
    values = li.resolve(LAYER_KEY, li.common_controls(DEFAULT_SEED) + list(CONTROLS), parameters)          # the shared Seed and Amount come first
    tree, b = li.make_layer_group(GROUP_NAME, LAYER_KEY, CONTROLS, parameters, DEFAULT_SEED, DECLARED_LINKS)
    S = b.input
    tiles = int(parameters.get('recipe.tiles_across', 1))
    seed_number = float(values['seed'])
    palette = [S(name) for name in PALETTE_NAMES]
    gather = float(values['gather'])

    def palette_pick(index):
        """The palette colour for a whole-number index 0..5: start with the darkest, switch up once the index is above each line."""
        colour = palette[0]
        for step in range(1, len(palette)):
            colour = b.mix(colour, palette[step], b.gt(index, step - 0.5))
        return colour

    def gather_gate(cells, stone_seed, warp):
        """1 for every cell inside a 'group' of stones, 0 outside, the same over a whole cell (so a stone is never cut in half). It repeats the stone helper's
        own bend of the grid (the same noise with the same numbers, so the same values) to find the middle of the cell the dot is in."""
        u, v = b.uv_xy()
        wobble_u, wobble_v, _unused = b.channels(b.tnoise_vector(2.5, 2.5, detail=2.0, roughness=0.5, seed=stone_seed * 1.7 + 3.0))
        bent_u = b.add(u, b.mul(b.sub(wobble_u, 0.5), 2.0 * warp / cells))
        bent_v = b.add(v, b.mul(b.sub(wobble_v, 0.5), 2.0 * warp / cells))
        middle_u = b.div(b.add(b.floor(b.mul(bent_u, cells)), 0.5), cells)
        middle_v = b.div(b.add(b.floor(b.mul(bent_v, cells)), 0.5), cells)
        field = b.tileable_noise(b.vec(middle_u, middle_v, 0.0), float(values['gather_features']) * tiles, 2.0, 0.5, seed_number * 0.7 + 5.0)
        line = 0.25 + 0.3 * gather
        return b.smoothstep(field, line - 0.01, line + 0.01)

    mask_all, colour_all = None, None
    for number, prefix in enumerate(CLASSES):
        cells = float(int(values[f'{prefix}_cells']) * tiles)
        stone_seed = seed_number + 7.0 * number
        warp = float(values['warp'])
        stones = stone_tools.polygon_stones(b, cells, stone_seed, presence=float(values[f'{prefix}_presence']),
                                            radius_low=float(values[f'{prefix}_radius_low']), radius_high=float(values[f'{prefix}_radius_high']), sides=5,
                                            warp=warp, jitter=0.10, light=(-0.6, 0.8), outline_width=float(values['outline_width']) * float(int(values[f'{prefix}_cells'])))     # the helper wants cell units
        mask = stones['mask']
        if gather > 0.0 and prefix != 'big':
            mask = b.mul(mask, gather_gate(cells, stone_seed, warp))
        base = b.floor(b.math('MULTIPLY_ADD', stones['random_tone'], 2.0, float(values['tone_bias'])))     # this stone's grey: 0, 1 or 2 (mostly 1)
        light_step = b.add(b.gt(stones['face'], -0.1), b.gt(stones['face'], 0.5))                  # 0 shadow face, 1 side face, 2 lit face
        colour = palette_pick(b.add(base, light_step))
        warm = b.gt(stones['bch'], 1.0 - float(values['warm_share']))
        dimmed = b.vmath('SCALE', S('Warm Stone Colour'), None, b.math('MULTIPLY_ADD', light_step, 0.25, 0.5))
        colour = b.mix(colour, dimmed, warm)
        colour = b.mix(colour, palette[1], stones['outline'])
        if mask_all is None:
            mask_all, colour_all = mask, colour
        else:                                                                                      # a bigger stone is painted over a smaller one
            colour_all = b.mix(colour_all, colour, mask)
            mask_all = b.mx(mask_all, mask)
    height = b.mul(mask_all, S('Raise'))
    roughness = b.mul(mask_all, 0.1)
    b.finish_layer(mask=mask_all, colour=colour_all, height=height, roughness=roughness)
    return tree
