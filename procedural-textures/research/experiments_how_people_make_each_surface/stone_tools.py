# What this does: one reusable building block for the mud and gravel recipes: a "stone layer". It cuts the tile into random polygon
# cells (a seamless Voronoi), keeps only some of the cells, shrinks each kept cell by a random margin so that a rounded-off random
# POLYGON is left (that is what gives the angular stones of the references), and works out for every pixel: whether it is on a stone,
# whether it is on the dark outline just inside the stone edge, a random number that is the same all over one stone (for its tone),
# and how much that spot of the stone faces the light (top-left), so a stone can have a light face and a dark face.
# Use (inside Blender, after making a Builder b):  import stone_tools as st ;  layer = st.stone_layer(b, scale=9, seed=3, density=0.25, ...)
#   layer is a dict of node outputs: mask, outline, lit, r, g, bch, edge_distance
import bpy


def stone_layer(b, scale, seed, density, margin_low=0.08, margin_high=0.26, outline_width=0.045, coords=None):
    """scale = cells across the tile; density = share of cells that hold a stone (0..1); margin_low..margin_high = how far each stone is
    pulled in from its cell border (in cell units; the bigger the margin the smaller the stone: 0.05 = nearly the whole cell)."""
    first = b.tvoronoi(scale, scale, seed, feature='F1', coords=coords)
    donut_vector, donut_w = b.last_donut
    cos_u, sin_u, cos_v, sin_v = b.last_trig
    edge = b.tvoronoi(scale, scale, seed, feature='DISTANCE_TO_EDGE', coords=coords)
    r, g, bch = b.channels(first.outputs['Color'])                              # three random numbers per cell
    margin = b.add(margin_low, b.mul(r, margin_high - margin_low))
    edge_distance = edge.outputs['Distance']
    present = b.window(g, 1.0 - density, 1.0 - density + 0.002)
    inside = b.invert(b.window(b.sub(margin, edge_distance), 0.0, 0.0))        # 1 where the pixel is farther from the cell border than the margin
    mask = b.mul(present, inside)
    outline_edge = b.add(margin, outline_width)
    outline = b.mul(mask, b.invert(b.window(edge_distance, outline_edge, outline_edge)))
    # how much this spot faces the top-left light: pixel offset from the cell's own point, rotated into picture directions
    offset = b.vmath('SUBTRACT', donut_vector, first.outputs['Position'])
    ox, oy, oz = b.xyz(offset)
    ow = b.sub(donut_w, first.outputs['W'])
    across = b.add(b.mul(ox, b.mul(sin_u, -1.0)), b.mul(oy, cos_u))               # picture-right part of the offset
    upward = b.add(b.mul(oz, b.mul(sin_v, -1.0)), b.mul(ow, cos_v))               # picture-up part of the offset
    lit = b.add(b.mul(across, -0.6), b.mul(upward, 0.8))                        # + when the spot is toward the top-left of the stone
    return {'mask': mask, 'outline': outline, 'lit': lit, 'r': r, 'g': g, 'bch': bch, 'edge_distance': edge_distance, 'present': present}


# ======================================================================================================================
# The second, better stone maker: one random irregular polygon per grid cell (no Voronoi at all).
# Why: the shrunk-Voronoi stones above come out as thin daggers and slivers (a flat slice through 4-dimensional cells has very uneven
# cell sizes). A grid of whole cells tiles exactly by itself (cell number wrapped with "modulo"), and each cell can hold one stone that is
# a convex polygon: it is the part of the cell where ALL of a few straight-edge tests are true ("distance along direction k is less than
# radius k"), with a random turn, random radius per edge and a random offset. Each flat face can also get its own brightness from the
# direction it faces, which gives the chunky faceted stones of the references.
import math


def hash3(b, cell_x, cell_y, seed):
    """Three random numbers (0..1) for a pair of whole numbers: the White Noise node's Color output (red, green, blue)."""
    vector = b.vec(cell_x, cell_y, seed)
    node = b.white(vector, '3D')
    return b.channels(node.outputs['Color'])


def polygon_stones(b, cells, seed, presence=0.7, radius_low=0.18, radius_high=0.42, sides=5, warp=0.6, jitter=0.10,
                   light=(-0.6, 0.8), outline_width=0.05):
    """cells = whole number of grid cells across the tile (the tile repeats exactly). presence = share of cells holding a stone.
    radius_low..radius_high = stone size in cell units (0.5 = touches the cell border). warp = how far (in cells) a slow noise bends the grid so it
    does not look like a grid. Returns a dict of node outputs: mask (1 on the stone), outline (1 on the dark ring just inside the edge),
    face (0..1 brightness of the flat face under this pixel from the light direction), r / g / bch (three random numbers, the same over one stone),
    inside_distance (how deep inside the stone: negative number, 0 at the edge)."""
    u, v = b.uv_xy()
    if warp > 0.0:
        warp_vector = b.tnoise_vector(2.5, 2.5, detail=2, roughness=0.5, seed=seed * 1.7 + 3.0)
        wx, wy, _ = b.channels(warp_vector)
        u = b.add(u, b.mul(b.sub(wx, 0.5), 2.0 * warp / cells))
        v = b.add(v, b.mul(b.sub(wy, 0.5), 2.0 * warp / cells))
    gx = b.mul(u, cells)
    gy = b.mul(v, cells)
    cell_x = b.floor(gx)
    cell_y = b.floor(gy)
    cx = b.mod(cell_x, cells)
    cy = b.mod(cell_y, cells)
    local_x = b.sub(b.frac(gx), 0.5)
    local_y = b.sub(b.frac(gy), 0.5)
    r1, r2, r3 = hash3(b, cx, cy, seed)                       # presence, size, rotation
    r4, r5, r6 = hash3(b, cx, cy, seed + 11.0)                # offset x, offset y, palette number
    r7, r8, r9 = hash3(b, cx, cy, seed + 23.0)                # extra randoms for the faces
    px = b.sub(local_x, b.mul(b.sub(r4, 0.5), 2.0 * jitter))
    py = b.sub(local_y, b.mul(b.sub(r5, 0.5), 2.0 * jitter))
    radius = b.add(radius_low, b.mul(r2, radius_high - radius_low))
    present = b.window(r1, 1.0 - presence, 1.0 - presence + 0.002)
    # face directions and radii
    face_randoms = []
    for k in range(sides):
        fa, fb, fc = hash3(b, cx, cy, seed + 40.0 + k)
        face_randoms.append((fa, fb))
    best_distance = None
    best_brightness = None
    for k, (angle_random, radius_random) in enumerate(face_randoms):
        angle = b.add(b.mul(r3, 2 * math.pi), b.add(2 * math.pi * k / sides, b.mul(b.sub(angle_random, 0.5), 0.9)))
        nx = b.math('COSINE', angle)
        ny = b.math('SINE', angle)
        along = b.add(b.mul(px, nx), b.mul(py, ny))
        face_radius = b.mul(radius, b.add(0.78, b.mul(radius_random, 0.44)))
        distance = b.sub(along, face_radius)                  # negative inside this face's half-plane
        brightness = b.add(b.mul(nx, light[0]), b.mul(ny, light[1]))     # -1..1: +1 when this face looks at the light
        if best_distance is None:
            best_distance, best_brightness = distance, brightness
        else:
            better = b.gt(distance, best_distance)
            best_brightness = b.mixf(best_brightness, brightness, better)
            best_distance = b.mx(best_distance, distance)
    inside = b.invert(b.window(best_distance, 0.0, 0.0))
    mask = b.mul(present, inside)
    outline = b.mul(mask, b.window(best_distance, -outline_width, -outline_width))
    return {'mask': mask, 'outline': outline, 'face': best_brightness, 'r': r2, 'g': r6, 'bch': r8, 'inside_distance': best_distance,
            'present': present, 'random_tone': r9}
