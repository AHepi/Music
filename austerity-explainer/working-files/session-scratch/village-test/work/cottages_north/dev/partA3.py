

def jittered_slab_poly(pts, rng, amount):
    """Soften a polygon: each corner pulled in/out a little so a stone slab is not a ruler rectangle."""
    return [(x + (rng.random() - 0.5) * amount, y + (rng.random() - 0.5) * amount) for x, y in pts]


def complete_cottage_A(B, c, ctx):
    rng, M, OAK, IRON = ctx['rng'], ctx['M'], ctx['OAK'], ctx['IRON']
    x0, x1, y0, y1, yc = ctx['x0'], ctx['x1'], ctx['y0'], ctx['y1'], ctx['yc']
    xt, DOOR_X, DOOR_POSTS = ctx['xt'], ctx['DOOR_X'], ctx['DOOR_POSTS']
    SILL_TOP, PL_BOT, PL_TOP, FOOT_H = ctx['SILL_TOP'], ctx['PL_BOT'], ctx['PL_TOP'], ctx['FOOT_H']
    opts = ctx['opts']

    # ---- earth floor inside the footing (top 5 cm above the ground), with a tongue out to the threshold
    acc = Acc()
    ex0, ex1, ey0, ey1 = x0 + 0.40, x1 - 0.40, y0 + 0.40, y1 - 0.40
    poly = [(ex0, ey0), (-32.487, ey0), (-32.487, y0 + 0.16), (-31.513, y0 + 0.16), (-31.513, ey0), (ex1, ey0), (ex1, ey1), (ex0, ey1)]
    V, F = extrude_z(poly, 0.0, 0.05)
    # a little unevenness in the top: 3 mm lumps on the interior vertices (the top ring only)
    n = len(poly)
    for i in range(n):
        V[n + i, 2] += 0.003 * (rng.random() - 0.5)
    acc.add(V, F, vary(hexl('#695842'), rng, 0.06))
    floor = B.emit(acc, 'earth floor', 'floor.earth', M['earth'])
    pk.seat_on_ground(floor)

    # ---- the doorstep: a flat stone, 14 cm high, between the door posts and a wider apron in front
    acc = Acc()
    ya = y0 - 0.45
    poly = [(-32.66, ya), (-31.34, ya), (-31.34, y0), (-31.513, y0), (-31.513, y0 + 0.16), (-32.487, y0 + 0.16), (-32.487, y0), (-32.66, y0)]
    poly = jittered_slab_poly(poly, rng, 0.0) if False else poly
    # roughen only the outer corners
    poly[0] = (poly[0][0] + 0.02 * rng.random(), poly[0][1] - 0.02 * rng.random())
    poly[1] = (poly[1][0] - 0.02 * rng.random(), poly[1][1] - 0.02 * rng.random())
    V, F = extrude_z(poly, 0.0, 0.14)
    acc.add(V, F, vary(hexl('#8A867C'), rng, 0.06))
    step = B.emit(acc, 'doorstep', 'stone.step', M['stone'])
    pk.seat_on_ground(step)
    step_top = 0.14

    # ---- the door and its hinges
    leaf, hinges = make_door(B, rng, M['boards'], M['iron'], IRON, y0 + 0.05, DOOR_X - 0.425, 0.85, 1.70, 0.05, step_top + 0.004, -1, hexl('#8A6A45'), hexl('#6B5239'))
    B.emit(leaf, 'door leaf', 'timber.door', M['boards'])
    B.emit(hinges, 'door hinges', 'iron.fitting', M['iron'])

    # ---- the shuttered windows (two leaves each; one leaf of the second south window stands ajar)
    shut_tone, fresh = hexl('#5C4A36'), hexl('#8A6A45')
    allh = Acc()
    for wx, wall, ajar in ((-35.0, 'south', False), (-29.0, 'south', True), (-32.0, 'north', False)):
        direction = -1 if wall == 'south' else 1
        face_y = (y0 + 0.01) if wall == 'south' else (y1 - 0.01)
        leaves, hinges = make_shutters(B, rng, M['shutter'], IRON, wx, face_y, direction, ajar, 0.95, 1.57, 0.255, shut_tone, fresh, f'{wall} {wx}')
        B.emit(leaves, f'shutters {wall} window {"1" if wx < -33 else "2"}', 'timber.shutter', M['shutter'])
        allh.V.extend(hinges.V)
        allh.F.extend([tuple(i + allh.n for i in f) for f in hinges.F])
        allh.C.extend(hinges.C)
        allh.n += hinges.n
    B.emit(allh, 'shutter hinges', 'iron.fitting', M['iron'])

    # ---- the roof frame: rafters, collars, purlins, ridge piece
    frame = build_roof_frame(c, rng, OAK, None)
    B.emit(frame['rafters'], 'rafters', 'timber.beam', M['oak'])
    B.emit(frame['collars'], 'collar beams', 'timber.beam', M['oak'])
    B.emit(frame['purlin_s'], 'purlin south', 'timber.beam', M['oak'])
    B.emit(frame['purlin_n'], 'purlin north', 'timber.beam', M['oak'])
    B.emit(frame['ridge'], 'ridge piece', 'timber.beam', M['oak'])
    # ---- the thatch: golden, thick, rolled at the eave, a darker ridge cap
    colour = thatch_colour_fn(int(ctx['seed']) + 21, hexl('#9C7A3F'), hexl('#B08C4A'), hexl('#7A5E30'), hexl('#6F8A3A'), hexl('#4F3F22'), hexl('#3E3222'), hexl('#C2A265'))
    V, F, C = build_thatch(c, rng, colour, roll=float(opts.get('thatch_roll', 1.0)), amp=0.028, seed=ctx['seed'] + 3)
    acc = Acc()
    acc.add(V, F, C)
    B.emit(acc, 'thatch', 'roof.thatch', M['thatch'], smooth=True)

    build_lean_to(B, c, ctx)


def build_lean_to(B, c, ctx):
    """The log store on the west end: three posts on the ground carrying a plate, five rafters from the plate to a ledger let into the gable studs, a purlin, a shingle roof at 32 degrees, boards on
    the north side. Open to the south and to the west; EMPTY (the props part stacks the woodpile outside)."""
    rng, M, OAK, IRON = ctx['rng'], ctx['M'], ctx['OAK'], ctx['IRON']
    x0, y_s, y_n = ctx['x0'], 8.1, 11.5
    th = math.radians(32.0)
    tn, cs = math.tan(th), math.cos(th)
    z_p = 1.30                                              # top of the front plate
    d_b, d_a, r_d = 2.5, 2.36, 0.09
    rv = r_d / cs
    x_ref = x0                                              # d = distance west of the gable's outer plane

    def Ul(d):
        return z_p + tn * (d_b - d)

    def Tl(d):
        return Ul(d) + rv

    def xd(d):
        return x_ref - d
    # posts (on the ground), each its own object
    for k, yy in enumerate((y_s + 0.07, (y_s + y_n) / 2, y_n - 0.07)):
        acc = Acc()
        V, F = lofted_post(xd(2.43), yy, 0.0, z_p - 0.12, 0.14, 0.14, lean=((rng.random() - 0.5) * 0.03, (rng.random() - 0.5) * 0.03), twist=(rng.random() - 0.5) * 0.1, taper=0.9 + 0.08 * rng.random())
        acc.add(V, F, vary(OAK, rng, 0.2))
        o = B.emit(acc, f'lean-to post {("south", "middle", "north")[k]}', 'timber.post', M['oak'])
        pk.seat_on_ground(o)
    # plate (two sections, each between two posts)
    acc = Acc()
    mid = (y_s + y_n) / 2
    for ya, yb in ((y_s, mid - 0.005), (mid + 0.005, y_n)):
        poly = [(xd(d_b), z_p - 0.12), (xd(d_a - 0.02), z_p - 0.12), (xd(d_a - 0.02), z_p), (xd(d_b), z_p)]
        V, F = extrude_y(poly, ya, yb)
        acc.add(V, F, vary(OAK, rng, 0.15))
    B.emit(acc, 'lean-to plate', 'timber.beam', M['oak'])
    # ledger let into the gable studs, its top cut to the rafters' underside
    acc = Acc()
    poly = [(xd(0.075), Ul(0.075) - 0.14), (xd(-0.06), Ul(-0.06) - 0.14), (xd(-0.06), Ul(-0.06)), (xd(0.075), Ul(0.075))]
    V, F = extrude_y(poly, y_s, y_n)
    acc.add(V, F, vary(OAK, rng, 0.15))
    B.emit(acc, 'lean-to ledger', 'timber.beam', M['oak'])
    # rafters
    acc = Acc()
    ys = [8.25, 9.0, 9.8, 10.6, 11.35]
    for yy in ys:
        w = 0.065 + 0.02 * rng.random()
        d_max = d_b + 0.22 + 0.1 * rng.random()
        poly = [(xd(0.0), Ul(0.0)), (xd(0.0), Tl(0.0)), (xd(d_max), Tl(d_max)), (xd(d_max), Ul(d_max)), (xd(d_b), z_p), (xd(d_a), z_p), (xd(d_a), Ul(d_a))]
        V, F = extrude_y(poly, yy - w / 2, yy + w / 2)
        acc.add(V, F, vary(OAK, rng, 0.15))
    B.emit(acc, 'lean-to rafters', 'timber.beam', M['oak'])
    # purlin let into the rafters 4.5 cm
    acc = Acc()
    pen, ph, pw = 0.045, 0.12, 0.10
    s_vec, n_vec = np.array([cs, -tn * cs]), np.array([tn * cs, cs])        # along the slope (outward and down), normal to it
    dpu = 1.35
    base = np.array([dpu, Ul(dpu)])
    pts = []
    for a, b in ((-pw / 2, -(ph - pen)), (pw / 2, -(ph - pen)), (pw / 2, pen), (-pw / 2, pen)):
        p = base + a * s_vec + b * n_vec
        pts.append((xd(p[0]), p[1]))
    V, F = extrude_y(pts, y_s + 0.05, y_n - 0.05)
    acc.add(V, F, vary(OAK, rng, 0.12))
    B.emit(acc, 'lean-to purlin', 'timber.beam', M['oak'])
    # shingle roof: a slab lying on the rafter tops (its back on the plane through the tops)
    W, L = (y_n - y_s) + 0.2, (d_b + 0.3) / cs
    field = ShingleField(int(ctx['seed']) + 77, W, L, [hexl('#6B5D4A'), hexl('#7A6B55'), hexl('#5F5547'), hexl('#85785F')], hexl('#2E261C'), hexl('#6F8A3A'))
    us, vs = subdivide_lines([0, W], 0.07), subdivide_lines([0, L], 0.07)
    e_n = np.array([-math.sin(th), 0.0, cs])
    e_u = np.array([0.0, 1.0, 0.0])
    e_v = np.cross(e_n, e_u)
    orig = np.array([xd(0.0), y_s - 0.1, Tl(0.0)])
    V, F, C = relief_slab(orig, e_u, e_n, us, vs, 0.045, field.relief, None, colour_fn=field.colour, back_colour=hexl('#3A2F22'), edge_colour=hexl('#4B3E2F'), e_v=e_v)
    acc = Acc()
    acc.add(V, F, C)
    B.emit(acc, 'lean-to shingle roof', 'roof.shingle', M['shingle'])
    # boards on the north side: upright boards on the ground, their tops cut to the underside of the roof slab
    acc = Acc()
    x_a, x_b = xd(d_b + 0.0), xd(0.02)
    xs = [x_a]
    while xs[-1] < x_b - 0.05:
        xs.append(xs[-1] + 0.15 + 0.03 * rng.random() + 0.004)
    xs[-1] = min(xs[-1], x_b)
    yb = y_n - 0.07 + 0.0
    fresh_i = int(rng.integers(2, len(xs) - 2))
    cols = []
    for i in range(len(xs) - 1):
        xa, xb = xs[i], xs[i + 1] - 0.004
        wdt = xb - xa
        top = lambda x, y: Tl(max(x_ref - x, 0.0)) - 0.003 - 0.0  # noqa: E731
        V, F = lofted_post((xa + xb) / 2, yb, 0.0, 1.0, wdt, 0.03, lean=(0, 0), twist=0.0, taper=1.0, top_z_fn=top)
        acc.add(V, F, vary(hexl('#6B5239') if i != fresh_i else hexl('#8A6A45'), rng, 0.15))
    B.emit(acc, 'lean-to boards', 'timber.plank', M['boards'])
