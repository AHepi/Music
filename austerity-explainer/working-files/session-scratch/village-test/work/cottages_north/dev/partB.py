

# ------------------------------------------------------------------ COTTAGE B
def window_lining(rng, wood, centre_across, z0, z1, width_open, facing, origin, depth=0.20, proud=0.045):
    """A timber lining for a small window in a stone wall (no glass): a sill, two jambs and a head. Built facing south with the window centre at x = 0, the nominal outer plane at y = 0 and the
    frame standing `proud` outside it (so the shutters lie on flat faces), then placed on the wall. Returns an accumulator."""
    acc = Acc()
    wo = width_open / 2
    t = 0.05
    for (xa, xb, za, zb) in ((-wo - t, wo + t, z0, z0 + t), (-wo - t, -wo, z0 + t, z1 - t), (wo, wo + t, z0 + t, z1 - t), (-wo - t, wo + t, z1 - t, z1)):
        V, F = box(xa, xb, -proud, depth, za, zb)
        acc.add(place_xy(V, facing, origin), F, vary(wood, rng, 0.15))
    return acc


def build_chimney(rng, x_c, y_c, top, base_w=(1.04, 0.84), shaft=(0.90, 0.70), colour=None):
    """The stone chimney stack: a splayed base, a shaft of courses that each jut a little differently, a corbelled cap with a flue hollow. One closed piece from the ground to `top`."""
    courses = []
    z = 0.0
    courses.append((0.0, 0.34, base_w))
    z = 0.34
    k = 0
    while z < top - 0.45:
        h = 0.26 + 0.18 * rng.random()
        h = min(h, top - 0.45 - z)
        taper = 1.0 - 0.07 * (z / top)
        courses.append((z, z + h, (shaft[0] * taper, shaft[1] * taper)))
        z += h
    courses.append((z, top - 0.12, (shaft[0] * 0.93, shaft[1] * 0.93)))
    courses.append((top - 0.12, top, (shaft[0] + 0.12, shaft[1] + 0.12)))
    rings = []
    for (za, zb, (sy, sx)) in courses:
        ring_a = ring_stone_course(x_c, y_c, za, zb, sx, sy, rng, jut=0.025)
        ring_b = [(px + (rng.random() - 0.5) * 0.008, py + (rng.random() - 0.5) * 0.008) for px, py in ring_a]
        rings.append([(px, py, za) for px, py in ring_a])
        rings.append([(px, py, zb) for px, py in ring_b])
    # the flue: an inner rim at the top and a hollow going down
    fx, fy = 0.30, 0.40
    rings.append([(x_c - fx / 2, y_c - fy / 2, top), (x_c + fx / 2, y_c - fy / 2, top), (x_c + fx / 2, y_c + fy / 2, top), (x_c - fx / 2, y_c + fy / 2, top)])
    rings.append([(x_c - fx / 2, y_c - fy / 2, top - 0.3), (x_c + fx / 2, y_c - fy / 2, top - 0.3), (x_c + fx / 2, y_c + fy / 2, top - 0.3), (x_c - fx / 2, y_c + fy / 2, top - 0.3)])
    V, F = loft_rings(rings)
    cols = []
    n_q = 4
    for m in range(len(rings) - 1):
        for k_ in range(n_q):
            base = vary(colour, rng, 0.07) if (m % 2 == 0) else colour
            cols.append(shade(base, 0.82) if m >= len(rings) - 3 else base)
    cols.append(colour)
    cols.append(shade(colour, 0.5))
    return V, F, cols


def build_cottage_B(opts):
    seed = int(opts.get('seed', 17))
    rng = np.random.default_rng(seed * 11 + 5)
    x0, x1, y0, y1 = -9.2, -2.8, 7.2, 11.8
    yc = 9.5
    g = ground_level(x0 - 0.2, -1.9, y0 - 0.6, y1 + 0.2)
    B = Builder('B', g)
    TIM, STONE_PAL = hexl('#5A4C40'), [hexl('#7C7A73'), hexl('#6E6C66'), hexl('#8A8880'), hexl('#5F5E58'), hexl('#74726B')]
    MOSS = hexl('#5E8236')
    M = dict(timber=make_material('Cottage B timber', 0.8), wall=make_material('Cottage B rubble', 0.9), thatch=make_material('Cottage B thatch', 0.95), footing=make_material('Cottage B footing stone', 0.85),
             boards=make_material('Cottage B boards', 0.8), iron=make_material('Cottage B iron', 0.6), earth=make_material('Cottage B earth', 0.95), shutter=make_material('Cottage B shutter wood', 0.8),
             chimney=make_material('Cottage B chimney stone', 0.9))
    IRON = hexl('#2E2E30')
    FOOT_H, WALL_TOP, WALL_T = 0.30, 2.10, 0.50
    PLATE_H = 0.12
    xt = [x0 + 0.62, -6.0, x1 - 0.62]
    c = Cot(x0=x0, x1=x1, y0=y0, y1=y1, Zp=WALL_TOP + PLATE_H, d_b=2.15, bw=0.14, r_d=0.10, xt=xt, sag_max=0.035 * float(opts.get('sag_cm', 1.0)), collar_z=4.05, collar_x=[xt[1]], d_p=1.15,
            px0=x0 + 0.52, px1=x1 - 0.52, rx0=x0 + 0.55, rx1=x1 - 0.55, tx0=x0, tx1=x1, t_n=0.35, overhang=0.40, rafter_x=[])
    for k in range(2):
        a, b = xt[k], xt[k + 1]
        n = int(round((b - a) / 0.62))
        for j in range(n):
            c.rafter_x.append((a + (b - a) * j / n, j == 0))
    c.rafter_x.append((xt[-1], True))

    # ---- footing: rubble strips under the walls (0.48 wide), the doorway left open
    acc = Acc()
    gap_lo, gap_hi = -6.62, -5.38
    fw = 0.48
    inset = (WALL_T - fw) / 2
    parts = [_footing_acc([((x0 + inset, gap_lo), (y0 + inset, y0 + inset + fw), 'x_long'), ((gap_hi, x1 - inset), (y0 + inset, y0 + inset + fw), 'x_long')], rng, x0, x1, y0, y1, FOOT_H, STONE_PAL, 'south'),
             _footing_acc([((x0 + inset, x1 - inset), (y1 - inset - fw, y1 - inset), 'x_long')], rng, x0, x1, y0, y1, FOOT_H, STONE_PAL, 'north'),
             _footing_acc([((x0 + inset, x0 + inset + fw), (y0 + inset + fw, y1 - inset - fw), 'y_long')], rng, x0, x1, y0, y1, FOOT_H, STONE_PAL, 'west'),
             _footing_acc([((x1 - inset - fw, x1 - inset), (y0 + inset + fw, y1 - inset - fw), 'y_long')], rng, x0, x1, y0, y1, FOOT_H, STONE_PAL, 'east')]
    for p in parts:
        merge_acc(acc, p)
    foot = B.emit(acc, 'footing', 'stone.footing', M['footing'])
    B.g += pk.seat_on_ground(foot)

    # ---- the rubble walls: big uneven blocks standing out of the face; the south wall has the doorway (with a rebate for the lintel) and a small window
    fields = {}
    wall_specs = [
        ('south', (x0, y0 + WALL_T, FOOT_H), (1, 0, 0), (0, -1, 0), x1 - x0, [(2.35, 2.65, 1.50, 1.66), (3.75, 4.05, 1.50, 1.66)], [(2.65, 3.75, 0.0, 1.50), (2.35, 4.05, 1.50, 1.66), (0.95, 1.45, 0.70, 1.30)]),
        ('north', (x1, y1 - WALL_T, FOOT_H), (-1, 0, 0), (0, 1, 0), x1 - x0, [], []),
        ('west', (x0 + WALL_T, y1 - WALL_T, FOOT_H), (0, -1, 0), (-1, 0, 0), (y1 - y0) - 2 * WALL_T, [], []),
        ('east', (x1 - WALL_T, y0 + WALL_T, FOOT_H), (0, 1, 0), (1, 0, 0), (y1 - y0) - 2 * WALL_T, [], []),
    ]
    H = WALL_TOP - FOOT_H
    for name, orig, e_u, e_n, W, _unused, holes in wall_specs:
        if name == 'east':
            holes = [(2.8, 3.3, 0.70, 1.30)]
        sf = StoneField(int(rng.integers(1, 10 ** 6)), W, H, STONE_PAL, MOSS, big=1.0, amp=0.032)
        inner = StoneField(int(rng.integers(1, 10 ** 6)), W, H, STONE_PAL, MOSS, big=1.1, amp=0.012, moss_amount=0.0)
        must_u = [0.0, W] + [h for hh in holes for h in (hh[0], hh[1])]
        must_v = [0.0, H] + [h for hh in holes for h in (hh[2], hh[3])]
        us, vs = subdivide_lines(must_u, 0.06), subdivide_lines(must_v, 0.06)
        V, F, C = relief_slab(orig, e_u, e_n, us, vs, WALL_T, sf.relief, lambda U, V_, f=inner: 0.5 * f.relief(U, V_) + 0.01, holes=holes, colour_fn=sf.colour, back_colour=hexl('#6E6C66'), edge_colour=hexl('#5F5E58'))
        acc = Acc()
        acc.add(V, F, C)
        B.emit(acc, f'{name} wall', 'wall.stone', M['wall'], smooth=True)
    # ---- the two gables above the eaves: stone up to the underside of the thatch (a sloping top)
    for name, xo, e_u, e_n, y_start in (('west', x0, (0, 1, 0), (-1, 0, 0), y0), ('east', x1 - WALL_T, (0, 1, 0), (1, 0, 0), y0)):
        W = y1 - y0
        sf = StoneField(int(rng.integers(1, 10 ** 6)), W, 3.4, STONE_PAL, MOSS, big=1.0, amp=0.032)
        us = subdivide_lines([0.0, W], 0.07)
        vs = subdivide_lines([WALL_TOP, WALL_TOP + 3.0], 0.1)
        if name == 'west':
            orig, e_u_, e_n_ = (x0 + WALL_T, y1, 0.0), (0, -1, 0), (-1, 0, 0)
            yco = (lambda u: y1 - u)
        else:
            orig, e_u_, e_n_ = (x1 - WALL_T, y0, 0.0), (0, 1, 0), (1, 0, 0)
            yco = (lambda u: y0 + u)
        V, F, C = relief_slab(orig, e_u_, e_n_, us, vs, WALL_T, lambda U, V_, f=sf: f.relief(U, V_ - FOOT_H), lambda U, V_: 0.006 + 0.0 * U, colour_fn=lambda U, V_, R, f=sf: f.colour(U, V_ - FOOT_H, R),
                              back_colour=hexl('#6E6C66'), edge_colour=hexl('#5F5E58'), top_fn=lambda u: c.T(abs(yco(u) - yc)) - 0.003)
        acc = Acc()
        acc.add(V, F, C)
        B.emit(acc, f'{name} gable', 'wall.stone', M['wall'], smooth=True)
    # ---- quoin stones at the four corners: stacked blocks, long and short faces turn about
    acc = Acc()
    corners = [(x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)]
    for cx, cy, sx, sy in corners:
        z = FOOT_H
        flip = int(rng.integers(0, 2))
        row = 0
        while z < WALL_TOP - 0.05:
            h = 0.25 + 0.09 * rng.random()
            h = min(h, WALL_TOP - z)
            if WALL_TOP - (z + h) < 0.18:
                h = WALL_TOP - z
            L, S = 0.44 + 0.2 * rng.random(), 0.30 + 0.06 * rng.random()
            along_x = ((row + flip) % 2 == 0)
            ax, ay = (L, S) if along_x else (S, L)
            xa, xb = (cx - 0.03, cx - 0.03 + ax) if sx > 0 else (cx + 0.03 - ax, cx + 0.03)
            ya, yb = (cy - 0.03, cy - 0.03 + ay) if sy > 0 else (cy + 0.03 - ay, cy + 0.03)
            V, F = stone_blob((xa + xb) / 2, (ya + yb) / 2, z, z + h, xb - xa, yb - ya, rng, wobble=0.05)
            acc.add(V, F, vary(hexl('#8E8B82'), rng, 0.08))
            z += h
            row += 1
    B.emit(acc, 'quoin stones', 'wall.stone', M['wall'])
    return B, c, dict(rng=rng, M=M, TIM=TIM, IRON=IRON, x0=x0, x1=x1, y0=y0, y1=y1, yc=yc, xt=xt, FOOT_H=FOOT_H, WALL_TOP=WALL_TOP, WALL_T=WALL_T, PLATE_H=PLATE_H, opts=opts, seed=seed, MOSS=MOSS)


def complete_cottage_B(B, c, ctx):
    rng, M, TIM, IRON = ctx['rng'], ctx['M'], ctx['TIM'], ctx['IRON']
    x0, x1, y0, y1, yc = ctx['x0'], ctx['x1'], ctx['y0'], ctx['y1'], ctx['yc']
    FOOT_H, WALL_TOP, WALL_T, PLATE_H = ctx['FOOT_H'], ctx['WALL_TOP'], ctx['WALL_T'], ctx['PLATE_H']
    opts = ctx['opts']
    DX = -6.0
    # ---- earth floor inside the walls
    acc = Acc()
    V, F = extrude_z([(x0 + WALL_T, y0 + WALL_T), (x1 - WALL_T, y0 + WALL_T), (x1 - WALL_T, y1 - WALL_T), (x0 + WALL_T, y1 - WALL_T)], 0.0, 0.05)
    for i in range(4):
        V[4 + i, 2] += 0.003 * (rng.random() - 0.5)
    acc.add(V, F, vary(hexl('#5E4E3A'), rng, 0.06))
    floor = B.emit(acc, 'earth floor', 'floor.earth', M['earth'])
    pk.seat_on_ground(floor)
    # ---- doorstep: an apron of flat stone in front, a neck through the doorway
    acc = Acc()
    ya = y0 - 0.5
    poly = [(DX - 0.92, ya), (DX + 0.92, ya), (DX + 0.92, y0), (DX + 0.432, y0), (DX + 0.432, y0 + WALL_T), (DX - 0.432, y0 + WALL_T), (DX - 0.432, y0), (DX - 0.92, y0)]
    poly[0] = (poly[0][0] + 0.03 * rng.random(), poly[0][1] - 0.02 * rng.random())
    poly[1] = (poly[1][0] - 0.03 * rng.random(), poly[1][1] - 0.02 * rng.random())
    V, F = extrude_z(poly, 0.0, 0.16)
    acc.add(V, F, vary(hexl('#8A867C'), rng, 0.06))
    step = B.emit(acc, 'doorstep', 'stone.step', M['footing'])
    pk.seat_on_ground(step)
    # ---- jamb posts (on the ground), lintel (resting on the rebate), door and hinges
    for sgn in (-1, 1):
        acc = Acc()
        xc = DX + sgn * 0.4925
        V, F = lofted_post(xc, y0 + 0.225, 0.0, 1.80, 0.115, 0.15, lean=((rng.random() - 0.5) * 0.012, 0.0), twist=(rng.random() - 0.5) * 0.04, taper=0.96)
        acc.add(V, F, vary(TIM, rng, 0.18))
        o = B.emit(acc, f'door post {"west" if sgn < 0 else "east"}', 'timber.post', M['timber'])
        pk.seat_on_ground(o)
    acc = Acc()
    V, F = box(DX - 0.85, DX + 0.85, y0 + 0.02, y0 + WALL_T - 0.02, 1.80, 1.96)
    acc.add(V, F, vary(TIM, rng, 0.12))
    B.emit(acc, 'lintel', 'timber.beam', M['timber'])
    leaf, hinges = make_door(B, rng, M['boards'], M['iron'], IRON, y0 + 0.20, DX - 0.425, 0.85, 1.65, 0.05, 0.16 + 0.004, -1, hexl('#7C6040'), hexl('#5E4B38'), hinge_z=(0.30, 1.30))
    B.emit(leaf, 'door leaf', 'timber.door', M['boards'])
    B.emit(hinges, 'door hinges', 'iron.fitting', M['iron'])
    # ---- the two small shuttered windows (0.4 x 0.5 clear), lined with timber so the shutters lie on flat faces
    shut_tone, fresh = hexl('#4F4236'), hexl('#7C6040')
    allh = Acc()
    for name, facing, origin, ajar in (('south', 'S', (-8.0, y0), True), ('east', 'E', (x1, 10.75), False)):
        lining = window_lining(rng, TIM, 0.0, 1.0, 1.6, 0.40, facing, origin)
        B.emit(lining, f'{name} window sill, jambs and head', 'timber.beam', M['timber'])
        leaves, hinges = make_shutters(rng, IRON, ajar, 1.02, 1.58, 0.215, shut_tone, fresh, facing, origin, plane=-0.045)
        B.emit(leaves, f'shutters {name} window', 'timber.shutter', M['shutter'])
        merge_acc(allh, hinges)
    B.emit(allh, 'shutter hinges', 'iron.fitting', M['iron'])
    # ---- wall plates on the stone tops (two sections each), the roof frame, the thatch
    acc = Acc()
    for xa, xb in ((x0 + WALL_T, -6.005), (-5.995, x1 - WALL_T)):
        for dd in (-1, 1):
            yy = yc + dd * 2.05
            V, F = bowed_bar_x(xa, xb, yy, 0.20, WALL_TOP, WALL_TOP + PLATE_H, (rng.random() - 0.5) * 0.014, ybow_phase=rng.random())
            acc.add(V, F, vary(TIM, rng, 0.15))
    B.emit(acc, 'wall plates', 'timber.beam', M['timber'])
    frame = build_roof_frame(c, rng, TIM, None)
    B.emit(frame['rafters'], 'rafters', 'timber.beam', M['timber'])
    B.emit(frame['collars'], 'collar beam', 'timber.beam', M['timber'])
    B.emit(frame['purlin_s'], 'purlin south', 'timber.beam', M['timber'])
    B.emit(frame['purlin_n'], 'purlin north', 'timber.beam', M['timber'])
    B.emit(frame['ridge'], 'ridge piece', 'timber.beam', M['timber'])
    colour = thatch_colour_fn(int(ctx['seed']) + 31, hexl('#6A6B50'), hexl('#5C5F45'), hexl('#46483A'), hexl('#6F8A3A'), hexl('#3A402C'), hexl('#2F2A20'), hexl('#8D8A68'), moss_amount=1.0, north_moss=0.6)
    V, F, C = build_thatch(c, rng, colour, roll=float(opts.get('thatch_roll', 1.0)), amp=0.034, seed=ctx['seed'] + 5)
    acc = Acc()
    acc.add(V, F, C)
    B.emit(acc, 'thatch', 'roof.thatch', M['thatch'], smooth=True)
    # ---- the chimney: from the ground, through the east gable, 1.2 m above the ridge
    ridge_top = float(c.T(0.0) + c.t_n / COS + 0.11)
    V, F, cols = build_chimney(rng, x1 - 0.30, yc, ridge_top + 1.2, colour=hexl('#76736B'))
    acc = Acc()
    acc.add(V, F, cols)
    chim = B.emit(acc, 'chimney', 'stone.chimney', M['chimney'])
    pk.seat_on_ground(chim)
