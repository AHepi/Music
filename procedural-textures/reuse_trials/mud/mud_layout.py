# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------
# MUD LAYOUT: the small box that answers "which ground patch am I on, and where on it?" for every dot, and hands the shared layers the same
# eleven numbers the slate LAYOUT gives them (the "bundle": piece_id, row, local_x, local_y, piece_width, piece_height, edge_distance,
# top_edge_distance, gap_mask, piece_mask, base_height; their meaning is in recipes/slate_layers/interface/interface.md). It paints nothing.
#
# Mud has no bricks or slates, so a "piece" here is a PATCH OF GROUND: a seamless mosaic of irregular cells (about 80 dots across at the
# default). The shared paint layers then draw the real clods INSIDE each patch (COLOUR AND FADE's little tall flat colour cells).
#   1. PATCHES. The picture is cut into a grid of 16 x 16 places. Every place holds one point, moved at random inside its place (Jitter).
#      A dot belongs to the nearest point. Each dot looks at the 9 places around it (its own and its 8 neighbours); the place numbers are
#      wrapped (place 16 is place 0 again), so the tile repeats exactly. A slow seamless wobble (Warp) bends the patch borders so they are
#      not straight lines.
#   2. WHERE ON THE PATCH. local_x / local_y say where the dot is on its patch, over a box two patch widths wide (an irregular patch reaches well
#      beyond one patch width from its point; with a tighter box the numbers froze at the box edge and the clods inside the patch came out as straight
#      blocks: found in round 7), measured in a frame that is turned (Lean) so that the long way of
#      the mud clods runs along the wheel ruts. local_y runs "down" the patch toward the upper left (the side the light comes from), so the
#      top edge of a patch (local_y = 0) is its shadow side, as the shared layers expect. edge_distance is the distance to the patch border
#      (second-nearest point minus nearest point, halved). There are no gaps: gap_mask is 0 and piece_mask is 1 everywhere.
#   3. BARE RELIEF (base_height). Mostly flat ground with a tiny random lift per patch, and BASINS: a slow seamless noise cut at a line;
#      where it is above the line the ground sinks (a puddle basin, rough edge from the noise's fine detail). MOSS reads this low relief as
#      "water gathers here" (its damp-spot rule), so the puddles follow the basins.
# Settings are named 'mud_layout.<name>'. The number of cells changes the number of nodes, so it is read when the box is built;
# everything else is a socket in the Shader editor. Sizes are TILE units (1.0 = the whole base tile; at 1254 dots 0.008 = 10 dots).
import math
import sys

sys.dont_write_bytecode = True
import layer_interface as li  # noqa: E402  (from the frozen snapshot; the recipe puts the snapshot first on the search path)
from layer_interface import Control  # noqa: E402

LAYER_KEY = 'mud_layout'
GROUP_NAME = 'MUD LAYOUT'

CONTROLS = [
    Control('cells_across', 'Cells Across Per Tile', 16, 2, 64, 'how many ground patches fit across one base tile (16 = a patch about 78 dots across)', build_time=True),
    Control('seed', 'Seed', 1.0, 0.0, 1000.0, 'random seed of the layout: changes where the patches and the puddle basins are, nothing else'),
    Control('jitter', 'Jitter', 0.9, 0.0, 1.0, 'how far each patch point moves from its place in the grid (0 = a regular grid, 1 = anywhere in its place)'),
    Control('warp', 'Warp', 0.3, 0.0, 1.0, 'how far a slow wobble bends the patch borders, in patch widths (0 = straight borders)'),
    Control('lean', 'Lean', 20.0, -90.0, 90.0, 'how many degrees the long way of the clods leans from straight up-down, toward the upper left at the top (the wheel ruts of the reference run steeply down to the right)'),
    Control('ground_level', 'Ground Level', 0.62, 0.0, 1.0, 'base relief height of dry ground (0..1); MOSS counts anything below about 0.56 as damp'),
    Control('patch_lift', 'Patch Lift', 0.02, 0.0, 0.2, 'how much each patch of ground is higher or lower than the others (plus and minus this much)'),
    Control('basin_features', 'Basin Features', 5.0, 1.0, 30.0, 'how many puddle basins (noise features) fit across one base tile'),
    Control('basin_edge', 'Basin Edge', 0.575, 0.3, 0.8, 'the line the basin noise is cut at: the noise (about 0.3 to 0.7) must be above this for ground to sink; higher = fewer, smaller basins'),
    Control('basin_soft', 'Basin Soft', 0.04, 0.001, 0.2, 'how gradually the ground sinks past the line (in noise units)'),
    Control('basin_depth', 'Basin Depth', 0.34, 0.0, 0.6, 'how far a basin sinks below the ground (0..1 relief scale)'),
    Control('basin_detail', 'Basin Detail', 5.0, 0.0, 8.0, 'how many finer noise layers are added to the basin outline (0 = smooth blobs, 5 = scalloped, ragged edge)'),
    Control('basin_roughness', 'Basin Roughness', 0.58, 0.1, 0.9, 'how strong the finer noise layers are compared with the coarse one'),
]
OUTPUTS = [(name, 'float', li.BUNDLE_TEXT[name]) for name in li.BUNDLE_NAMES]


def build_group(parameters):
    """Make the MUD LAYOUT node group. Reads 'mud_layout.*' settings and 'recipe.tiles_across'."""
    values = li.resolve(LAYER_KEY, CONTROLS, parameters)
    tiles = int(parameters.get('recipe.tiles_across', 1))
    cells = int(values['cells_across']) * tiles               # patches across the whole picture
    n = float(cells)
    inputs = [('Vector', 'vector', (0.0, 0.0, 0.0), None, None, 'the tile coordinate: x = 0..1 left to right, y = 0..1 BOTTOM to top of the picture')]
    for control in CONTROLS:
        if not control.build_time:
            inputs.append((control.label, control.kind, values[control.key], control.low, control.high, control.text))
    tree, b = li.make_plain_group(GROUP_NAME, inputs, OUTPUTS)
    S = b.input
    seed = S('Seed')
    u, v, _ = b.xyz(S('Vector'))

    # ---------------------------------------------------------------------------------------------- 1. PATCHES (nearest of the jittered points)
    wobble = b.tnoise_vector(2.5 * tiles, 2.5 * tiles, detail=2.0, roughness=0.5, seed=b.mul(seed, 3.1))      # slow seamless wobble, three numbers about 0.3..0.7
    wobble_u, wobble_v, _unused = b.channels(wobble)
    bend = b.mul(b.mul(S('Warp'), 2.0), 1.0 / n)
    grid_u = b.mul(b.add(u, b.mul(b.sub(wobble_u, 0.5), bend)), n)         # position in patch-grid units (0 .. n)
    grid_v = b.mul(b.add(v, b.mul(b.sub(wobble_v, 0.5), bend)), n)
    base_i, base_j = b.floor(grid_u), b.floor(grid_v)
    best_d2 = best_dx = best_dy = best_id = None
    second_d2 = 100.0
    for dj in (-1, 0, 1):
        for di in (-1, 0, 1):
            place_i, place_j = b.add(base_i, float(di)), b.add(base_j, float(dj))
            wrapped_i, wrapped_j = b.mod(place_i, n), b.mod(place_j, n)
            roll = b.hash4(b.vec(wrapped_i, wrapped_j, seed), 0.37)
            random_x, random_y, _spare = b.channels(roll.outputs['Color'])
            point_u = b.add(place_i, b.math('MULTIPLY_ADD', b.sub(random_x, 0.5), S('Jitter'), 0.5))
            point_v = b.add(place_j, b.math('MULTIPLY_ADD', b.sub(random_y, 0.5), S('Jitter'), 0.5))
            dx, dy = b.sub(grid_u, point_u), b.sub(grid_v, point_v)
            d2 = b.add(b.mul(dx, dx), b.mul(dy, dy))
            if best_d2 is None:
                best_d2, best_dx, best_dy, best_id = d2, dx, dy, roll.outputs['Value']
                continue
            nearer = b.lt(d2, best_d2)
            second_d2 = b.mixf(b.mn(second_d2, d2), best_d2, nearer)          # the old nearest becomes the second nearest if this point is nearer
            best_dx, best_dy = b.mixf(best_dx, dx, nearer), b.mixf(best_dy, dy, nearer)
            best_id = b.mixf(best_id, roll.outputs['Value'], nearer)
            best_d2 = b.mn(best_d2, d2)

    # ---------------------------------------------------------------------------------------------- 2. WHERE ON THE PATCH (a frame turned by Lean)
    border = b.div(b.mul(b.sub(b.sqrt(second_d2), b.sqrt(best_d2)), 0.5), n)             # distance to the patch border, tile units
    angle = b.mul(S('Lean'), math.pi / 180.0)
    sin_a, cos_a = b.math('SINE', angle), b.math('COSINE', angle)
    off_u, off_v = b.div(best_dx, n), b.div(best_dy, n)                                  # offset from the patch point, tile units (u right, v up)
    down = b.add(b.mul(off_u, b.mul(sin_a, -1.0)), b.mul(off_v, cos_a))                  # along the long way, toward the upper left (the lit side)
    across = b.add(b.mul(off_u, cos_a), b.mul(off_v, sin_a))
    size = 2.0 / n                                                                       # the 'box' of a patch: two average patch widths, so that even the far parts of an irregular patch are inside it
    local_y = b.maprange(down, -0.5 * size, 0.5 * size, 0.0, 1.0, True)
    local_x = b.maprange(across, -0.5 * size, 0.5 * size, 0.0, 1.0, True)

    # ---------------------------------------------------------------------------------------------- 3. BARE RELIEF: level ground, tiny lift per patch, puddle basins
    basin_noise = b.tnoise(S('Basin Features') if tiles == 1 else b.mul(S('Basin Features'), float(tiles)), None, S('Basin Detail'), S('Basin Roughness'), 0.0, b.add(b.mul(seed, 2.3), 5.0))
    basin = b.smoothstep(basin_noise, S('Basin Edge'), b.add(S('Basin Edge'), S('Basin Soft')))
    lift = b.mul(b.sub(b.mul(best_id, 2.0), 1.0), S('Patch Lift'))
    base_height = b.add(b.add(S('Ground Level'), lift), b.mul(basin, b.mul(S('Basin Depth'), -1.0)))

    bundle = {'piece_id': best_id, 'row': 0.0, 'local_x': local_x, 'local_y': local_y, 'piece_width': size, 'piece_height': size,
              'edge_distance': border, 'top_edge_distance': b.mul(local_y, size), 'gap_mask': 0.0, 'piece_mask': 1.0, 'base_height': base_height}
    for name in li.BUNDLE_NAMES:
        b.output(name, bundle[name])
    return tree
