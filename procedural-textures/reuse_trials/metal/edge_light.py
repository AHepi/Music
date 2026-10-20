# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------
# EDGE LIGHT: a NEW paint layer with exactly the same sockets as the shared layers (built with the shared layer_interface.py, unchanged).
# The reference steel is drawn as if lit from the upper left. The shared OUTLINE AND SHADOW layer draws a shadow under the UPPER edge of
# every piece (with the METAL LAYOUT that is the long soft shadow on the plate under a lying bar), but it knows nothing of light from the
# left and it treats a bar and the plate alike. This layer adds the three things that are missing:
#   1. THE LIT LINE. A thin bright line just inside the edge of a bar that faces the light: the UPPER edge of a lying bar and the LEFT edge
#      of an upright bar (the reference: about 2 to 6 dots in from the dark crease, very bright).
#   2. THE DARK WALL. A dark band just inside the edge of a bar that faces away: the LOWER edge of a lying bar and the RIGHT edge of an
#      upright bar (the reference: about 8 dots of dark next to the crease).
#   3. THE CAST SHADOW RIGHT OF AN UPRIGHT BAR. A soft shadow on whatever lies just right of an upright bar (a panel, or the end of a lying
#      bar that passes under it), fading over Shadow Width in flat steps (the reference: about 20 dots).
# How it knows a bar: a bar is a long thin piece (its length is more than Bar Aspect times its width); upright when taller than wide. (The
# METAL LAYOUT also makes bars higher than the plate, but next to an edge the bare relief slopes down, so the shape is the safer test.)
# A panel's left edge always borders an upright bar in the METAL LAYOUT, and so does the left end of a lying bar stretch: both get the shadow.
# Outputs (the fixed interface): Mask, Colour, Height (lit line slightly up, dark wall slightly down), Roughness (lit line smoother).
# It reads only the layout bundle (local_x, local_y, piece_width, piece_height, piece_mask) and Vector (for a seamless wobble), its own controls
# and Seed. Amount scales it; 0 switches it off exactly (finish_layer). Sizes are TILE units (at 1254 dots per tile 0.004 = 5 dots).
import math
import sys

sys.dont_write_bytecode = True
import layer_interface as li  # noqa: E402  (from the frozen snapshot; the recipe puts the snapshot first on the search path)
from layer_interface import Control  # noqa: E402

LAYER_KEY = 'edge_light'
GROUP_NAME = 'EDGE LIGHT'
DEFAULT_SEED = 71.0

CONTROLS = [
    Control('bar_aspect', 'Bar Aspect', 3.0, 1.0, 20.0, 'a piece counts as a bar when its length is more than this many times its width'),
    Control('line_offset', 'Line Offset', 0.0018, 0.0, 0.02, 'where the lit line starts, in tile units from the piece edge (0.0018 = 2.3 dots: just past the dark crease)'),
    Control('line_width', 'Line Width', 0.003, 0.0, 0.02, 'width of the lit line, in tile units (0.003 = 3.8 dots)'),
    Control('line_strength', 'Line Strength', 0.8, 0.0, 1.0, 'how strongly the lit colour covers the paint on the line (0 = no line)'),
    Control('line_breakup', 'Line Breakup', 0.25, 0.0, 1.0, 'how broken the lit line is (0 = unbroken, 1 = only short pieces)'),
    Control('line_colour', 'Line Colour', '#77726f', kind='colour', text='the bright grey of the lit edge'),
    Control('wall_width', 'Wall Width', 0.0065, 0.0, 0.03, 'width of the dark band inside the shaded edge of a bar, in tile units (0.0065 = 8 dots)'),
    Control('wall_strength', 'Wall Strength', 0.55, 0.0, 1.0, 'how strongly the dark colour covers the paint in that band'),
    Control('shadow_width', 'Shadow Width', 0.016, 0.0, 0.06, 'how far the shadow right of an upright bar reaches, in tile units (0.016 = 20 dots)'),
    Control('shadow_darkness', 'Shadow Darkness', 0.6, 0.0, 1.0, 'how strongly the shadow colour covers the paint right next to the bar (weaker further out)'),
    Control('shadow_tiers', 'Shadow Tiers', 3.0, 0.0, 8.0, 'how many flat steps the shadow is cut into (0 = smooth)'),
    Control('dark_colour', 'Dark Colour', '#100c0a', kind='colour', text='the colour of the dark wall and of the cast shadow'),
    Control('wobble', 'Wobble', 0.4, 0.0, 1.0, 'how hand-drawn the line, wall and shadow edges are (0 = ruler straight)'),
    Control('wobble_scale', 'Wobble Scale', 70.0, 5.0, 400.0, 'how many wobbles fit across one base tile'),
    Control('line_height', 'Line Height', 0.02, 0.0, 0.2, 'how much the lit line is raised (height scale 0..1)'),
    Control('wall_height', 'Wall Height', 0.03, 0.0, 0.2, 'how much the dark wall is lowered (height scale 0..1)'),
]
DECLARED_LINKS = []          # EDGE LIGHT reads no other layer
SOFT = 0.0006                # soft width of every painted edge, in tile units (0.75 dot at 1254)


def build_group(parameters):
    tree, b = li.make_layer_group(GROUP_NAME, LAYER_KEY, CONTROLS, parameters, DEFAULT_SEED, DECLARED_LINKS)
    S = b.input
    g = b.bundle()
    seed, tiles = S('Seed'), S('Tile Count')
    width, height = g['piece_width'], g['piece_height']

    def hard(value):
        return b.smoothstep(value, 0.0, SOFT)

    def lay_over(under_colour, under_strength, colour, strength):
        total = b.sub(1.0, b.mul(b.sub(1.0, under_strength), b.sub(1.0, strength)))
        share = b.div(strength, b.mx(total, 1e-6))
        return b.mix(under_colour, colour, share), total

    # ---- what kind of piece, and distances to its four edges (tile units)
    upright = b.gt(height, width)
    long_side, short_side = b.mx(width, height), b.mn(width, height)
    bar = b.gt(long_side, b.mul(short_side, S('Bar Aspect')))
    lying_bar, upright_bar = b.mul(bar, b.sub(1.0, upright)), b.mul(bar, upright)
    from_left, from_top = b.mul(g['local_x'], width), b.mul(g['local_y'], height)
    from_right, from_bottom = b.sub(width, from_left), b.sub(height, from_top)
    lit_distance = b.mixf(from_top, from_left, upright)                  # lying bar: from its upper edge; upright bar: from its left edge
    shade_distance = b.mixf(from_bottom, from_right, upright)

    # ---- seamless wobble (two noises on the tile coordinate)
    per_tile = b.mul(tiles, S('Wobble Scale'))
    wobble = b.mul(b.sub(b.noise01(S('Vector'), per_tile, 2.0, 0.55, b.add(b.mul(seed, 3.1), 1.0)), 0.5), b.mul(S('Wobble'), 2.0))    # about -1..1 x Wobble
    breaker = b.noise01(S('Vector'), b.mul(per_tile, 0.5), 2.0, 0.5, b.add(b.mul(seed, 3.1), 9.0))

    # ---- 1. lit line
    line_from = b.mul(S('Line Offset'), b.add(1.0, b.mul(wobble, 0.5)))
    line_to = b.add(line_from, b.mul(S('Line Width'), b.add(1.0, wobble)))
    on_line = b.mul(hard(b.sub(lit_distance, line_from)), hard(b.sub(line_to, lit_distance)))
    unbroken = b.smoothstep(breaker, b.sub(b.mul(S('Line Breakup'), 0.8), 0.1), b.add(b.mul(S('Line Breakup'), 0.8), 0.0))
    line = b.mul(b.mul(on_line, unbroken), bar)
    line_strength = b.mul(line, S('Line Strength'))

    # ---- 2. dark wall inside the shaded edge of a bar
    wall_reach = b.mul(S('Wall Width'), b.add(1.0, b.mul(wobble, 0.5)))
    wall = b.mul(hard(b.sub(wall_reach, shade_distance)), bar)
    wall_strength = b.mul(wall, S('Wall Strength'))

    # ---- 3. cast shadow right of an upright bar (on panels and on the left ends of lying bars)
    reach = b.mx(b.mul(S('Shadow Width'), b.add(1.0, b.mul(wobble, 0.4))), 1e-5)
    depth = b.maprange(b.div(from_left, reach), 0.0, 1.0, 1.0, 0.0, True)
    tiers = S('Shadow Tiers')
    stepped = b.div(b.floor(b.add(b.mul(depth, tiers), 0.9999)), b.mx(tiers, 1e-5))
    shape = b.mixf(depth, stepped, b.gt(tiers, 0.5))
    shadow_strength = b.mul(b.mul(shape, S('Shadow Darkness')), b.sub(1.0, upright_bar))

    # ---- stack: shadow, wall, line (later on top); only on the piece (the crease keeps its own dark from OUTLINE AND SHADOW)
    colour, strength = S('Dark Colour'), shadow_strength
    colour, strength = lay_over(colour, strength, S('Dark Colour'), wall_strength)
    colour, strength = lay_over(colour, strength, S('Line Colour'), line_strength)
    mask = b.mul(strength, g['piece_mask'])
    height_change = b.mul(b.sub(b.mul(line, S('Line Height')), b.mul(wall, S('Wall Height'))), g['piece_mask'])
    roughness = b.mul(b.mul(line, -0.1), g['piece_mask'])
    b.finish_layer(mask=mask, colour=colour, height=height_change, roughness=roughness)
    return tree
