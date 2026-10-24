

def make_door(B, rng, mat, hinge_mat, iron_col, wall_y_front, x_left, width, height, thick, z_bottom, direction, fresh, tone, hinge_side='left', hinge_z=(0.35, 1.42), name_prefix='door'):
    """A door leaf (one piece: boards of unequal width with grooves, two battens on the back, one board a fresher replacement) and its two iron strap hinges. direction -1: the door faces south
    (outward is -y), +1: faces north. Returns (leaf acc, hinge acc)."""
    widths = [0.16 + 0.04 * rng.random() for _ in range(5)]
    field = BoardField(int(rng.integers(1, 10 ** 6)), width, height, widths, tone, fresh, fresh_index=int(rng.integers(1, 4)), batten_rows=[(0.28, 0.37), (height - 0.40, height - 0.31)])
    us, vs = subdivide_lines([0, width], 0.03), subdivide_lines([0, height], 0.1)
    if direction < 0:
        orig, e_u, e_n = (x_left, wall_y_front + thick, z_bottom), (1, 0, 0), (0, -1, 0)
    else:
        orig, e_u, e_n = (x_left + width, wall_y_front - thick, z_bottom), (-1, 0, 0), (0, 1, 0)
    V, F, C = relief_slab(orig, e_u, e_n, us, vs, thick, field.relief, field.back, colour_fn=field.colour, back_colour=shade(tone, 0.8), edge_colour=shade(tone, 0.7))
    leaf = Acc()
    leaf.add(V, F, C)
    hinges = Acc()
    for zc in hinge_z:
        length = 0.52 + 0.06 * rng.random()
        if direction < 0:
            xa, xb = (x_left - 0.01, x_left + length) if hinge_side == 'left' else (x_left + width - length, x_left + width + 0.01)
            ya, yb = wall_y_front - 0.011, wall_y_front + 0.002
        else:
            xa, xb = (x_left + width - length, x_left + width + 0.01) if hinge_side == 'left' else (x_left - 0.01, x_left + length)
            ya, yb = wall_y_front - 0.002, wall_y_front + 0.011
        zl = z_bottom + zc
        V, F = box(xa, xb, ya, yb, zl, zl + 0.07)
        hinges.add(V, F, vary(iron_col, rng, 0.2))
    return leaf, hinges


def make_shutters(B, rng, mat, iron_col, wx, face_y, direction, ajar, z0, z1, leaf_w, tone, fresh, name):
    """Two shutter leaves of a window (no glass): each a board slab with a batten on the back and two strap hinges; one can stand ajar. face_y: the plane of the studs' outer face. direction -1: south wall."""
    leaves, hinges = Acc(), Acc()
    thick = 0.028
    for side in (-1, 1):                                       # -1: the west leaf (hinged at the west stud), +1: the east leaf
        xa = wx - leaf_w if side < 0 else wx
        field = BoardField(int(rng.integers(1, 10 ** 6)), leaf_w, z1 - z0, [0.5 + 0.2 * rng.random(), 0.5 + 0.2 * rng.random()], tone, fresh, fresh_index=(int(rng.integers(0, 2)) if rng.random() < 0.3 else None),
                           batten_rows=[((z1 - z0) * 0.55, (z1 - z0) * 0.55 + 0.07)])
        us, vs = subdivide_lines([0, leaf_w], 0.04), subdivide_lines([0, z1 - z0], 0.1)
        yb = face_y + direction * -0.004                        # back plane of the leaf, 4 mm off the studs
        yb = face_y - 0.004 if direction < 0 else face_y + 0.004
        if direction < 0:
            orig, e_u, e_n = (xa, yb, z0), (1, 0, 0), (0, -1, 0)
        else:
            orig, e_u, e_n = (xa + leaf_w, yb, z0), (-1, 0, 0), (0, 1, 0)
        V, F, C = relief_slab(orig, e_u, e_n, us, vs, thick, field.relief, field.back, colour_fn=field.colour, back_colour=shade(tone, 0.8), edge_colour=shade(tone, 0.7))
        hv = []
        for zc in (z0 + 0.12, z1 - 0.18):
            xs0, xs1 = (xa - 0.012, xa + 0.19) if side < 0 else (xa + leaf_w - 0.19, xa + leaf_w + 0.012)
            if direction < 0:
                hv.append(box(xs0, xs1, yb - thick - 0.006 + 0.002, yb - thick + 0.002, zc, zc + 0.03))
            else:
                hv.append(box(xs0, xs1, yb + thick - 0.002, yb + thick + 0.006 - 0.002, zc, zc + 0.03))
        if ajar and side > 0:
            pivot = (xa + leaf_w, yb)
            ang = math.radians(72.0) * (1 if direction < 0 else -1)
            V = rot_z(V, ang, pivot)
            hv = [(rot_z(hh[0], ang, pivot), hh[1]) for hh in hv]
        leaves.add(V, F, C)
        for hh in hv:
            hinges.add(hh[0], hh[1], vary(iron_col, rng, 0.2))
    return leaves, hinges
