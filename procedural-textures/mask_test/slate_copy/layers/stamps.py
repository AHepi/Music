# What this file does (plain words)
# ------------------------------------------------------------------------------------------------------------------------------
# STAMPS lets a layer use a picture of separate shapes as the "where" of its paint. This file is part of the mask test copy of the slate
# recipe (it is NOT in the original recipe folder).
#
# A "stamp" is one shape (one moss clump, one chip) cut out of a picture the image generator painted. The shapes sit in a grid picture
# called the ATLAS (equal cells, one stamp per cell; made by ../../tools/make_stamps.py). In the atlas picture: red = the mask (white = shape),
# green = how deep inside the shape a dot is (0 at the rim, 1 well inside).
#
# What "placing a stamp" means, in a concrete example (moss on one slate):
#   1. The slate has its own random numbers (from piece_id and the layer's Seed). They say: is stamp slot 1 used on this slate (a chance),
#      where along the slate's upper edge, how big, how far turned, mirrored or not, and WHICH cell of the atlas.
#   2. At every dot of the slate we work out where that dot lies inside the stamp: take the dot's place on the slate (x across the slate,
#      y down from the upper edge, both in tile units), subtract the stamp's centre, turn by the stamp's turn, divide by the stamp's size.
#      That gives u and v from 0 to 1 across the stamp (outside 0..1 = outside the stamp).
#   3. Read the atlas picture at (cell + u, cell + v). The red value is the stamp's mask at this dot, the green value its depth.
#   4. A layer uses several slots (for example two on the upper edge, one on a side joint, one low down) and takes the largest value.
# Because the dot's place is measured ON ITS OWN SLATE (the same numbers wherever the slate is wrapped round the tile edge), a stamp that
# lies on a slate crossing the tile edge is cut by the same slate edge on both sides and the tile still repeats exactly.
import json
import os

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))


class Atlas:
    """The atlas picture and what is known about it (read from the JSON file that make_stamps.py wrote next to it)."""

    def __init__(self, json_path):
        with open(json_path) as handle:
            info = json.load(handle)
        self.json_path = json_path
        self.columns, self.rows = int(info['columns']), int(info['rows'])
        self.count = int(info['stamp_count'])
        self.aspect = float(info['cell_aspect_height_over_width'])           # height of a stamp / width of a stamp
        path = os.path.join(os.path.dirname(json_path), info['atlas_file'])
        self.image = bpy.data.images.load(path, check_existing=True)
        self.image.colorspace_settings.name = 'Non-Color'                    # the numbers in the picture are data, not colours
        try:
            self.image.alpha_mode = 'NONE'
        except (TypeError, AttributeError):
            pass


def load_atlas(json_path):
    return Atlas(json_path)


def slot_randoms(b, piece_id, seed, slot):
    """Eight random numbers 0..1 for one stamp slot of one slate (the same on every dot of the slate; new with the layer's Seed)."""
    first = b.hash4(b.vec(piece_id, seed, float(slot)), 0.13)
    second = b.hash4(b.vec(piece_id, seed, float(slot) + 0.5), 0.57)
    a, c, d = b.channels(first.outputs['Color'])
    e, f, h = b.channels(second.outputs['Color'])
    return {'chance': a, 'along': c, 'pick': d, 'size': first.outputs['Value'], 'turn': e, 'mirror': f, 'extra': h, 'extra2': second.outputs['Value']}


def place(b, atlas, x_dot, y_dot, centre_x, centre_y, width, turn, mirror, pick, active):
    """One stamp slot. x_dot, y_dot = this dot's place in the frame of the slate (tile units; y grows towards the INSIDE of the stamp's picture,
    that is 'down' in the stamp). centre_x, centre_y = the stamp's centre in the same frame. width = the stamp's width (tile units); its height
    is width x the cell's aspect. turn = angle in radians. mirror = +1 or -1. pick = random 0..1 that chooses the atlas cell. active = 0 or 1.
    Returns (mask, depth), both 0..1."""
    height = b.mul(width, atlas.aspect)
    dx, dy = b.sub(x_dot, centre_x), b.sub(y_dot, centre_y)
    cos_a, sin_a = b.math('COSINE', turn), b.math('SINE', turn)
    along = b.add(b.mul(dx, cos_a), b.mul(dy, sin_a))
    across = b.add(b.mul(b.sub(0.0, dx), sin_a), b.mul(dy, cos_a))
    u = b.add(0.5, b.mul(b.div(along, width), mirror))
    v = b.add(0.5, b.div(across, height))
    inside = b.mul(b.mul(b.gt(u, 0.0), b.lt(u, 1.0)), b.mul(b.gt(v, 0.0), b.lt(v, 1.0)))
    index = b.floor(b.mn(b.mul(pick, float(atlas.count)), float(atlas.count) - 0.01))
    column = b.mod(index, float(atlas.columns))
    row = b.floor(b.div(index, float(atlas.columns)))
    u_in = b.maprange(u, 0.0, 1.0, 0.004, 0.996, True)                       # stay a hair inside the cell (the cell has black padding)
    v_in = b.maprange(v, 0.0, 1.0, 0.004, 0.996, True)
    atlas_u = b.div(b.add(column, u_in), float(atlas.columns))
    atlas_v = b.sub(1.0, b.div(b.add(row, v_in), float(atlas.rows)))          # Blender's picture row 0 is at the bottom
    texture = b.node('ShaderNodeTexImage', interpolation='Linear', extension='EXTEND')
    texture.image = atlas.image
    b._put(texture, 'Vector', b.vec(atlas_u, atlas_v, 0.0))
    red, green, _blue = b.channels(texture.outputs['Color'])
    keep = b.mul(inside, active)
    return b.mul(red, keep), b.mul(green, keep)


def harden(b, mask, softness):
    """Turn the stamp's grey mask into a mask with an edge of the wanted softness: 0 below 0.5 - softness, 1 above 0.5 + softness."""
    return b.smoothstep(mask, b.sub(0.5, softness), b.add(0.5, softness))
