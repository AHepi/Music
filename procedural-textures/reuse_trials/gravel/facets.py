# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------
# FACETS is the second NEW paint layer of the gravel trial. A real broken stone has flat faces, and with the light coming from the top the
# faces that look up are lighter and the faces that look down are darker. No shared layer can paint that: COLOUR AND FADE paints flat patches
# but they know nothing about which way a face looks. (The surveyor's plan said "FACETS only if needed"; the first look at the gravel in
# round 1 showed stones that are flat grey blocks, so it was needed.)
# How: every stone gets a few straight CUT LINES across it (two by default), each with its own random direction and place, made from the
# stone's piece_id. A cut line splits the stone into a part on one side and a part on the other: two flat faces. A face that looks UP
# (the line's direction points upwards on the picture) is painted lighter on its far side and darker on its near side, and the other way round
# for a line that points down. Where two cut lines cross there are four faces and the brightness adds up. Faces are painted as flat patches
# with a hard edge: a pale blue-grey over the lit faces, a near-black over the shaded ones, each covering the stone paint only partly (Facet
# Strength) so that every stone keeps its own tone underneath. Stones too small to show a facet get none (Smallest Stone).
# What it reads: piece_id, local_x, local_y, piece_width, piece_height, piece_mask and its own controls and Seed. It never looks at another
# layer (no declared links). The cut lines are made in the stone's own coordinates, so they are the same wherever the stone sits and the tile
# still repeats exactly.
# Sockets: exactly the shared layer interface (layer_interface.make_layer_group). Amount 0 = Mask, Height and Roughness exactly 0.
# Sizes are TILE units (1.0 = the whole base tile; at 1254 dots per tile 0.008 = 10 dots).
import math
import sys

sys.dont_write_bytecode = True
import layer_interface as li  # noqa: E402  (from the frozen snapshot; the recipe puts the snapshot first on the search path)
from layer_interface import Control  # noqa: E402

LAYER_KEY = 'facets'
GROUP_NAME = 'FACETS'
DEFAULT_SEED = 61.0

CONTROLS = [
    Control('cuts', 'Cuts', 2, 1, 4, 'how many straight cut lines every stone gets (each one splits it into two faces)', build_time=True),
    Control('facet_strength', 'Facet Strength', 0.4, 0.0, 1.0, 'how strongly the facet colour covers the stone paint on the strongest faces (0 = no facets)'),
    Control('facet_contrast', 'Facet Contrast', 0.9, 0.0, 3.0, 'how different neighbouring faces are: the brightness step across a cut line, as a multiple of the usual'),
    Control('cut_spread', 'Cut Spread', 0.6, 0.0, 1.0, 'how far from the middle of the stone a cut line may lie, as a share of the stone radius (0 = all cuts through the middle)'),
    Control('ragged_cuts', 'Ragged Cuts', 0.25, 0.0, 1.0, 'how far a fine noise pushes the cut lines about, as a share of the stone radius (0 = ruler-straight facet edges)'),
    Control('smallest_stone', 'Smallest Stone', 0.012, 0.0, 0.1, 'stones narrower than this (tile units; 0.012 = 15 dots) get no facets'),
    Control('light_colour', 'Light Colour', '#7f929c', kind='colour', text='the pale blue-grey of a face that looks up at the light'),
    Control('dark_colour', 'Dark Colour', '#0c0d0f', kind='colour', text='the near-black of a face that looks away from the light'),
    Control('height_step', 'Height Step', 0.02, 0.0, 0.2, 'how much a lit face stands up and a shaded face sinks (height scale 0..1)'),
]
DECLARED_LINKS = []          # FACETS reads no other layer

SOFT = 0.0006                # soft width of a facet edge, in tile units (0.75 dot): painted look = hard edges, one dot of anti-aliasing


def build_group(parameters):
    values = li.resolve(LAYER_KEY, CONTROLS, parameters)
    cuts = int(values['cuts'])
    tree, b = li.make_layer_group(GROUP_NAME, LAYER_KEY, CONTROLS, parameters, DEFAULT_SEED, DECLARED_LINKS)
    S = b.input
    g = b.bundle()
    seed, piece_mask = S('Seed'), g['piece_mask']
    radius = b.mul(g['piece_width'], 0.5 / 1.1)                                  # the nominal stone radius (the layout gives 2.2 radii)
    wobble = b.mul(b.sub(b.tileable_noise(S('Vector'), b.mul(S('Tile Count'), 120.0), 2.0, 0.5, b.add(b.mul(seed, 2.3), 5.0)), 0.5), 5.0)    # -1 .. +1
    across = b.mul(b.sub(g['local_x'], 0.5), g['piece_width'])                   # where the dot is on the stone, tile units, from its middle
    down = b.mul(b.sub(g['local_y'], 0.5), g['piece_height'])                    # (down = towards the bottom of the picture)
    shade = None
    for cut in range(cuts):
        random = b.hash4(b.vec(g['piece_id'], seed, float(cut) + 0.5), 0.2)
        r_turn, r_place, r_amount = b.channels(random.outputs['Color'])
        angle = b.mul(r_turn, 2.0 * math.pi)
        direction_x, direction_y = b.math('COSINE', angle), b.math('SINE', angle)           # the way the cut line "looks" (its normal), y down
        place = b.mul(b.mul(b.sub(r_place, 0.5), 2.0), b.mul(radius, S('Cut Spread')))
        distance = b.sub(b.add(b.add(b.mul(across, direction_x), b.mul(down, direction_y)), b.mul(wobble, b.mul(radius, S('Ragged Cuts')))), place)    # + on the side the normal points to
        side = b.smoothstep(distance, -SOFT, SOFT)                                           # 1 on the normal's side, 0 on the other
        looks_up = b.mul(direction_y, -1.0)                                                  # +1 when the normal points UP the picture (y is down)
        step = b.mul(b.mul(b.sub(b.mul(side, 2.0), 1.0), looks_up), b.add(0.5, r_amount))   # + lighter, - darker
        shade = step if shade is None else b.add(shade, step)
    shade = b.mul(shade, S('Facet Contrast'))
    big_enough = b.smoothstep(g['piece_width'], S('Smallest Stone'), b.mul(S('Smallest Stone'), 1.4))
    where = b.mul(piece_mask, big_enough)
    lit = b.smoothstep(shade, 0.1, 0.9)                                                      # 0..1: how lit
    shaded = b.smoothstep(b.mul(shade, -1.0), 0.1, 0.9)
    colour = b.mix(S('Dark Colour'), S('Light Colour'), b.gt(shade, 0.0))
    mask = b.mul(b.mul(b.mx(lit, shaded), S('Facet Strength')), where)
    height = b.mul(b.mul(b.sub(lit, shaded), S('Height Step')), where)
    b.finish_layer(mask=mask, colour=colour, height=height, roughness=b.mul(mask, 0.0))
    return tree
