# ------------------------------------------------------------------ COTTAGE A
def _footing_acc(strips, rng, x_lo, x_hi, y_lo, y_hi, height, colours, outer):
    """Rough rubble strips: flat top and bottom, the outer long edge pushed out by a different amount every half metre; the strips butt (they never overlap)."""
    acc = Acc()
    for (xa, xb), (ya, yb), axis in strips:
        if axis == 'x_long':
            n = max(1, int((xb - xa) / 0.5))
            if outer == 'south':
                poly = [(xa, ya)] + [(xa + (xb - xa) * j / n, ya - 0.03 * rng.random()) for j in range(1, n)] + [(xb, ya), (xb, yb), (xa, yb)]
            else:
                poly = [(xa, ya), (xb, ya), (xb, yb)] + [(xb - (xb - xa) * j / n, yb + 0.03 * rng.random()) for j in range(1, n)] + [(xa, yb)]
        else:
            n = max(1, int((yb - ya) / 0.5))
            if outer == 'west':
                poly = [(xa, ya), (xb, ya), (xb, yb), (xa, yb)] + [(xa - 0.03 * rng.random(), yb - (yb - ya) * j / n) for j in range(1, n)]
            else:
                poly = [(xa, ya), (xb, ya)] + [(xb + 0.03 * rng.random(), ya + (yb - ya) * j / n) for j in range(1, n)] + [(xb, yb), (xa, yb)]
        V, F = extrude_z(poly, 0.0, height)
        acc.add(V, F, vary(colours[int(rng.integers(0, len(colours)))], rng, 0.08))
    return acc


def _wall_panels(B, rng, wall, mem, wins, x0, x1, y0, y1, SILL_TOP, PL_BOT, base, chips_n, chip_scale, mats, splash_band=0.24):
    """The studs and the cream panels of one wall. mem: sorted members (centre, half width, kind). Returns (studs, panels, frames) accumulators."""
    OAK = mats['OAK']
    studs, panels = Acc(), Acc()
    for ctr, hw_, kind in mem:
        if kind not in ('stud', 'win'):
            continue
        lean = ((rng.random() - 0.5) * 0.01, (rng.random() - 0.5) * 0.01)
        if wall in ('south', 'north'):
            yy = y0 + 0.07 if wall == 'south' else y1 - 0.07
            V, F = lofted_post(ctr, yy, SILL_TOP, PL_BOT, 0.07, 0.12, lean=lean, twist=(rng.random() - 0.5) * 0.05, taper=0.96 + 0.04 * rng.random())
        else:
            xx = x0 + 0.07 if wall == 'west' else x1 - 0.07
            V, F = lofted_post(xx, ctr, SILL_TOP, PL_BOT, 0.12, 0.07, lean=lean, twist=(rng.random() - 0.5) * 0.05, taper=0.96 + 0.04 * rng.random())
        studs.add(V, F, vary(OAK, rng, 0.2))
    pan = []
    for (a, ha, ka), (b, hb, kb) in zip(mem[:-1], mem[1:]):
        if ka == 'door' and kb == 'door':
            continue
        lo, hi = a + ha + 0.003, b - hb - 0.003
        if hi - lo < 0.05:
            continue
        is_window = (ka == 'win' and kb == 'win') and any(abs((a + b) / 2 - wx) < 0.01 for wx in wins)
        for z0_, z1_ in ([(SILL_TOP, 0.90), (1.61, PL_BOT - 0.01)] if is_window else [(SILL_TOP, PL_BOT - 0.01)]):
            pan.append((lo, hi, z0_, z1_, is_window))
    eligible = [i for i, p in enumerate(pan) if (p[1] - p[0]) > 0.55 and not p[4]]
    chosen = set(rng.choice(eligible, size=min(chips_n, len(eligible)), replace=False).tolist()) if eligible and chips_n else set()
    for i, (lo, hi, z0_, z1_, is_window) in enumerate(pan):
        W, Hh = hi - lo, z1_ - z0_
        chips = 1 if i in chosen else 0
        field = PlasterField(int(rng.integers(1, 10 ** 6)), W, Hh, vary(base, rng, 0.04), mats['splash'], mats['hi'], mats['lo'], mats['rim'], chips=chips, chip_scale=chip_scale,
                             band=splash_band if z0_ == SILL_TOP else 0.0)
        step = 0.05 if chips else 0.075
        us, vs = subdivide_lines([0, W], step), subdivide_lines([0, Hh], step)
        if wall == 'south':
            orig, e_u, e_n = (lo, y0 + 0.12, z0_), (1, 0, 0), (0, -1, 0)
        elif wall == 'north':
            orig, e_u, e_n = (hi, y1 - 0.12, z0_), (-1, 0, 0), (0, 1, 0)
        elif wall == 'west':
            orig, e_u, e_n = (x0 + 0.12, hi, z0_), (0, -1, 0), (-1, 0, 0)
        else:
            orig, e_u, e_n = (x1 - 0.12, lo, z0_), (0, 1, 0), (1, 0, 0)
        V, F, C = relief_slab(orig, e_u, e_n, us, vs, 0.10, field.relief, None, colour_fn=field.colour, back_colour=mats['back'], edge_colour=mats['edge'])
        panels.add(V, F, C)
    return studs, panels


def build_cottage_A(opts):
    seed = int(opts.get('seed', 17))
    rng = np.random.default_rng(seed * 7 + 1)
    chip_scale = float(opts.get('chip_amount', 1.0))
    x0, x1, y0, y1 = -37.55, -26.45, 7.6, 12.4
    yc = 10.0
    g = ground_level(-40.1, x1, y0 - 0.5, y1)
    B = Builder('A', g)
    OAK, CREAM = hexl('#3E3128'), hexl('#CDBE9A')
    mats = dict(OAK=OAK, splash=hexl('#8C7B5C'), hi=hexl('#8A6A45'), lo=hexl('#4F3E2C'), rim=hexl('#E2D6B4'), back=hexl('#B5A583'), edge=hexl('#D8CBA6'))
    M = dict(oak=make_material('Cottage A oak frame', 0.8), lime=make_material('Cottage A limewash', 0.9), thatch=make_material('Cottage A thatch', 0.95),
             stone=make_material('Cottage A footing stone', 0.85), boards=make_material('Cottage A boards', 0.8), iron=make_material('Cottage A iron', 0.6),
             earth=make_material('Cottage A earth', 0.95), shingle=make_material('Cottage A shingles', 0.85), shutter=make_material('Cottage A shutter wood', 0.8))
    IRON = hexl('#2E2E30')
    xt = [x0 + 0.07, x0 + 3.70, x0 + 7.40, x1 - 0.07]
    FOOT_H, SILL_TOP, PL_BOT, PL_TOP = 0.28, 0.40, 1.88, 2.0
    DOOR_X, DOOR_POSTS = -32.0, (-32.55, -31.45)
    c = Cot(x0=x0, x1=x1, y0=y0, y1=y1, Zp=PL_TOP, d_b=2.4, bw=0.14, r_d=0.10, xt=xt, sag_max=0.03 * float(opts.get('sag_cm', 1.0)), collar_z=4.0, collar_x=[xt[1], xt[2]], d_p=1.25,
            px0=x0 + 0.03, px1=x1 - 0.03, rx0=x0 + 0.05, rx1=x1 - 0.05, tx0=x0 - 0.25, tx1=x1 + 0.25, t_n=0.30, overhang=0.45, rafter_x=[])
    for k in range(3):
        a, b = xt[k], xt[k + 1]
        n = int(round((b - a) / 0.6))
        for j in range(n):
            c.rafter_x.append((a + (b - a) * j / n, j == 0))
    c.rafter_x.append((xt[-1], True))
    stone_cols = [hexl('#7C7A73'), hexl('#6F6D66'), hexl('#85827A'), hexl('#6A6962')]

    # ---- footing: rubble strips that butt (no overlap), the doorway left open
    acc = Acc()
    acc.V, acc.F, acc.C, acc.n = [], [], [], 0
    parts = [(_footing_acc([((x0 - 0.02, -32.70), (y0 - 0.02, y0 + 0.40), 'x_long'), ((-31.30, x1 + 0.02), (y0 - 0.02, y0 + 0.40), 'x_long')], rng, x0, x1, y0, y1, FOOT_H, stone_cols, 'south')),
             (_footing_acc([((x0 - 0.02, x1 + 0.02), (y1 - 0.40, y1 + 0.02), 'x_long')], rng, x0, x1, y0, y1, FOOT_H, stone_cols, 'north')),
             (_footing_acc([((x0 - 0.02, x0 + 0.40), (y0 + 0.40, y1 - 0.40), 'y_long')], rng, x0, x1, y0, y1, FOOT_H, stone_cols, 'west')),
             (_footing_acc([((x1 - 0.40, x1 + 0.02), (y0 + 0.40, y1 - 0.40), 'y_long')], rng, x0, x1, y0, y1, FOOT_H, stone_cols, 'east'))]
    for p in parts:
        for V in p.V:
            pass
        acc.V.extend(p.V)
        acc.F.extend([tuple(i + acc.n for i in f) for f in p.F])
        acc.C.extend(p.C)
        acc.n += p.n
    foot = B.emit(acc, 'footing', 'stone.footing', M['stone'])
    shift = pk.seat_on_ground(foot)
    B.g += shift                                                                   # everything else of this cottage is built from the footing's own seat
    for o in B.objects:
        pass

    # ---- sill timbers on the footing (flat tops and bottoms; bowed a little in plan)
    acc = Acc()
    sills = [(x0, xt[1] - 0.005, y0 + 0.08), (xt[1] + 0.005, -32.62, y0 + 0.08), (-31.38, xt[2] - 0.005, y0 + 0.08), (xt[2] + 0.005, x1, y0 + 0.08),
             (x0, xt[1] - 0.005, y1 - 0.08), (xt[1] + 0.005, xt[2] - 0.005, y1 - 0.08), (xt[2] + 0.005, x1, y1 - 0.08)]
    for xa, xb, yy in sills:
        V, F = bowed_bar_x(xa, xb, yy, 0.16, FOOT_H, SILL_TOP, (rng.random() - 0.5) * 0.014, ybow_phase=rng.random())
        acc.add(V, F, vary(OAK, rng, 0.15))
    for xx in (x0 + 0.08, x1 - 0.08):
        V, F = extrude_y([(xx - 0.08, FOOT_H), (xx + 0.08, FOOT_H), (xx + 0.08, SILL_TOP), (xx - 0.08, SILL_TOP)], y0 + 0.16, y1 - 0.16)
        acc.add(V, F, vary(OAK, rng, 0.15))
    B.emit(acc, 'sill timbers', 'timber.beam', M['oak'])

    # ---- posts: each its own object (so each leans differently); truss posts stand on the sill, the door posts on the ground
    corner = {(0, 0): 'south west corner', (0, 1): 'north west corner', (3, 0): 'south east corner', (3, 1): 'north east corner'}
    posts = []
    for k, x in enumerate(xt):
        for side, yy in ((0, y0 + 0.07), (1, y1 - 0.07)):
            posts.append((corner.get((k, side), f'truss {k + 1} {"south" if side == 0 else "north"}'), x, yy, SILL_TOP, 0.14, 0.14))
    for xdp in DOOR_POSTS:
        posts.append((f'door post {"west" if xdp < DOOR_X else "east"}', xdp, y0 + 0.07, 0.0, 0.12, 0.14))
    for nm, x, yy, zb, sx, sy in posts:
        acc = Acc()
        lean = ((rng.random() - 0.5) * 0.024, (rng.random() - 0.5) * 0.024)
        V, F = lofted_post(x, yy, zb, PL_BOT, sx, sy, lean=lean, twist=(rng.random() - 0.5) * 0.08, taper=0.92 + 0.07 * rng.random())
        acc.add(V, F, vary(OAK, rng, 0.2))
        o = B.emit(acc, f'post {nm}', 'timber.post', M['oak'])
        if zb == 0.0:
            pk.seat_on_ground(o)

    # ---- the four walls: studs, cream panels, window sills and heads
    south = [(xt[k], 0.07, 'post') for k in range(4)] + [(DOOR_POSTS[0], 0.06, 'door'), (DOOR_POSTS[1], 0.06, 'door')] + [(wx + s * 0.26, 0.035, 'win') for wx in (-35.0, -29.0) for s in (-1, 1)]
    north = [(xt[k], 0.07, 'post') for k in range(4)] + [(-32.0 + s * 0.26, 0.035, 'win') for s in (-1, 1)]
    end = [(y0 + 0.07, 0.07, 'post'), (y1 - 0.07, 0.07, 'post')]
    spec = {'south': (members_along(south), [-35.0, -29.0], 2), 'north': (members_along(north), [-32.0], 2), 'west': (members_along(end), [], 0), 'east': (members_along(end), [], 1)}
    for wall in ('south', 'north', 'west', 'east'):
        mem, wins, chips_n = spec[wall]
        studs, panels = _wall_panels(B, rng, wall, mem, wins, x0, x1, y0, y1, SILL_TOP, PL_BOT, CREAM, chips_n, chip_scale, mats)
        frames = Acc()
        for wx in wins:
            yy0 = y0 + 0.02 if wall == 'south' else y1 - 0.12
            for z0_, z1_ in ((0.90, 0.96), (1.55, 1.61)):
                V, F = box(wx - 0.275, wx + 0.275, yy0, yy0 + 0.10, z0_, z1_)
                frames.add(V, F, vary(OAK, rng, 0.15))
        B.emit(studs, f'{wall} wall studs', 'timber.beam', M['oak'])
        B.emit(panels, f'{wall} wall panels', 'wall.timber_frame', M['lime'])
        if not frames.empty():
            B.emit(frames, f'{wall} window sills and heads', 'timber.beam', M['oak'])

    # ---- wall plates: three sections on each long wall, one across each end
    acc = Acc()
    for xa, xb in ((x0, xt[1] - 0.005), (xt[1] + 0.005, xt[2] - 0.005), (xt[2] + 0.005, x1)):
        for yy in (y0 + 0.08, y1 - 0.08):
            V, F = bowed_bar_x(xa, xb, yy, 0.16, PL_BOT, PL_TOP, (rng.random() - 0.5) * 0.016, ybow_phase=rng.random())
            acc.add(V, F, vary(OAK, rng, 0.15))
    B.emit(acc, 'wall plates', 'timber.beam', M['oak'])
    acc = Acc()
    for xx in (x0 + 0.08, x1 - 0.08):
        V, F = extrude_y([(xx - 0.08, PL_BOT), (xx + 0.08, PL_BOT), (xx + 0.08, PL_TOP), (xx - 0.08, PL_TOP)], y0 + 0.16, y1 - 0.16)
        acc.add(V, F, vary(OAK, rng, 0.15))
    B.emit(acc, 'end wall plates', 'timber.beam', M['oak'])

    # ---- gable ends: five gable studs and six panels over each end plate, up to the underside of the end rafters
    gable_y = [yc + k * 0.8 for k in (-2, -1, 0, 1, 2)]
    for wall, xx in (('west', x0 + 0.07), ('east', x1 - 0.07)):
        gs, gp = Acc(), Acc()
        for yy in gable_y:
            V, F = lofted_post(xx, yy, PL_TOP, c.U(abs(yy - yc)), 0.12, 0.07, lean=(0, (rng.random() - 0.5) * 0.006), top_z_fn=lambda x, y: c.U(abs(y - yc)) - 0.003)
            gs.add(V, F, vary(OAK, rng, 0.2))
        edges = [y0 + 0.16] + sum([[y - 0.038, y + 0.038] for y in gable_y], []) + [y1 - 0.16]
        for a, b in zip(edges[0::2], edges[1::2]):
            W = b - a
            field = PlasterField(int(rng.integers(1, 10 ** 6)), W, 3.0, vary(CREAM, rng, 0.04), mats['splash'], mats['hi'], mats['lo'], mats['rim'], chips=0, band=0.0)
            us, vs = subdivide_lines([0, W], 0.08), subdivide_lines([PL_TOP, PL_TOP + 1.0], 0.1)
            if wall == 'west':
                orig, e_u, e_n = (x0 + 0.12, b, 0.0), (0, -1, 0), (-1, 0, 0)
                yco = (lambda u, b=b: b - u)
            else:
                orig, e_u, e_n = (x1 - 0.12, a, 0.0), (0, 1, 0), (1, 0, 0)
                yco = (lambda u, a=a: a + u)
            V, F, C = relief_slab(orig, e_u, e_n, us, vs, 0.10, lambda U, V, f=field: f.relief(U, V - PL_TOP), None, colour_fn=lambda U, V, R, f=field: f.colour(U, V - PL_TOP, R),
                                  back_colour=mats['back'], edge_colour=mats['edge'], top_fn=lambda u, yco=yco: c.U(abs(yco(u) - yc)) - 0.006)
            gp.add(V, F, C)
        B.emit(gs, f'{wall} gable studs', 'timber.beam', M['oak'])
        B.emit(gp, f'{wall} gable panels', 'wall.timber_frame', M['lime'])
    return B, c, dict(rng=rng, M=M, OAK=OAK, IRON=IRON, x0=x0, x1=x1, y0=y0, y1=y1, yc=yc, xt=xt, DOOR_X=DOOR_X, DOOR_POSTS=DOOR_POSTS, FOOT_H=FOOT_H, PL_TOP=PL_TOP, PL_BOT=PL_BOT,
                      SILL_TOP=SILL_TOP, opts=opts, seed=seed, mats=mats)
