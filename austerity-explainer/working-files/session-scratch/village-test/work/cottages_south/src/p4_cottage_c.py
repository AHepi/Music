

# ------------------------------------------------------------------ cottage C
def build_C(parts, o):
    """Cottage C: timber frame with red-ochre daub, pale thatch at 50 degrees, a tall door in the north wall. Returns a dict of facts (sizes, counts) for the report."""
    rng = np.random.default_rng(o['seed'] + 101)
    noise = Noise(o['seed'] + 7)
    noise2 = Noise(o['seed'] + 8, scales=(1.3, 0.6, 0.3))
    X0, X1, Y0, Y1 = -29.7, -22.3, -12.8, -8.2
    hw = 0.07
    xw0, xw1, yw0, yw1 = X0 + hw, X1 - hw, Y0 + hw, Y1 - hw
    xm, yc = -26.0, -10.5
    LX, LY = xw1 - xw0, yw1 - yw0
    hp = yw1 - yc
    g, g_low = ground_top(X0 - 0.3, X1 + 0.3, Y0 - 0.3, Y1 + 0.3)
    ztf = g + 0.32
    zsb = ztf + 0.001
    zst = zsb + 0.15
    zpb = g + 2.06
    zpt = g + 2.2
    ZS = g + 2.2
    TAN, COS, SIN = math.tan(math.radians(50)), math.cos(math.radians(50)), math.sin(math.radians(50))
    WN = Wall((xw0, yw1), (1, 0), (0, 1), LX)
    WS = Wall((xw0, yw0), (1, 0), (0, -1), LX)
    WW = Wall((xw0, yw0), (0, 1), (-1, 0), LY)
    WE = Wall((xw1, yw0), (0, 1), (1, 0), LY)
    OAK = hexl('#33281F')
    DAUB = shade(tone3(hexl(o['daub_hex']), hexl('#8A4A3A'), hexl('#A5603E'), o['daub_tone']), o['daub_value'])
    MUD, CLAY = hexl('#5A3D2C'), hexl('#8C7050')
    WEATHER, FRESH = hexl('#5A4C40'), hexl('#8A6A45')
    IRON = hexl('#2A2826')
    STONE = hexl('#7C7A73')
    WATTLE = hexl('#5E4A33')
    facts = dict(g=g, g_low=g_low)

    # ---- footing: rubble stones, flat on top at one height, sunk into the pad, left out under the door
    foot = parts.acc('footC', 'Cottage C footing', 'stone.footing', seat=0.03)

    def fill(start, end):
        pos, out = start, []
        while end - pos > 0.05:
            L = rng.uniform(0.45, 0.85)
            if end - pos - L < 0.38:
                L = end - pos
            out.append((pos + L / 2, L - 0.02))
            pos += L
        return out
    door_u0, door_u1 = -26.5, -25.5
    runs = []
    for (a, b) in ((xw0 - 0.21, door_u0), (door_u1, xw1 + 0.21)):
        for c, L in fill(a, b):
            runs.append((c, yw1, L, 0.0))
    for c, L in fill(xw0 - 0.21, xw1 + 0.21):
        runs.append((c, yw0, L, 0.0))
    for c, L in fill(yw0 + 0.21 + 0.015, yw1 - 0.21 - 0.015):
        runs.append((xw0, c, L, math.pi / 2))
        runs.append((xw1, c, L, math.pi / 2))
    for (cx, cy, L, rot) in runs:
        if rot == 0.0:
            cx, cy = cx, cy + rng.uniform(-0.012, 0.012)
        else:
            cx, cy = cx + rng.uniform(-0.012, 0.012), cy
        width = rng.uniform(0.38, 0.46)
        zb = pk.ground_height_at(cx, cy) - 0.03
        V, F = stone_solid(cx, cy, L, width, rot, zb, ztf, rng)
        foot.add(V, F, col=stone_colour(STONE, g, rng.uniform(0.80, 1.12)))

    # ---- sill timbers (the north sill is cut at the door; the east and west sills lie between the north and south ones)
    sill = parts.acc('sillC', 'Cottage C sill', 'timber.beam')
    sill_cols = lambda: oak(rng, OAK)  # noqa: E731
    dl = -26.45 - xw0
    dr = -25.55 - xw0
    for wall, u0, u1 in ((WN, -0.075, dl), (WN, dr, LX + 0.075), (WS, -0.075, LX / 2 - 0.0075), (WS, LX / 2 + 0.0075, LX + 0.075), (WW, 0.078, LY - 0.078), (WE, 0.078, LY - 0.078)):
        hwid = 0.075 + rng.uniform(-0.004, 0.004)
        V, F = bar_solid(wall, u0, u1, 0.0, hwid, zsb, zst, bow=rng.uniform(-0.004, 0.004), taper=rng.uniform(0.97, 1.0))
        sill.add(V, F, col=sill_cols())

    # ---- the corner posts (four objects: the kit leans a post about its own foot, so each stands alone)
    corner_info = {}
    for tag, wall, u in (('NW', WN, 0.0), ('NE', WN, LX), ('SW', WS, 0.0), ('SE', WS, LX)):
        a = rng.uniform(0.072, 0.082)
        b = rng.uniform(0.072, 0.080)
        lean = lean_for(rng, o['lean'], big=True)
        acc = parts.acc('postC' + tag, 'Cottage C post ' + tag, 'timber.post')
        V, F = post_solid(wall, u, 0.0, a, b, zst + 0.001, zpb - 0.001, lean=lean, bow=(rng.uniform(-0.004, 0.004), rng.uniform(-0.004, 0.004)),
                          twist=rng.uniform(-0.03, 0.03), taper=rng.uniform(0.94, 0.99))
        acc.add(V, F, col=oak(rng, OAK))
        corner_info[tag] = dict(a=a, b=b, lw=lean[0] * wall.eu[:2] + lean[1] * wall.ew[:2])

    def corner_rec(tag, wall, u):
        ci = corner_info[tag]
        aa, bb = (ci['a'], ci['b']) if wall in (WN, WS) else (ci['b'], ci['a'])
        lean = (float(ci['lw'] @ wall.eu[:2]), float(ci['lw'] @ wall.ew[:2]))
        return dict(u=u, w=0.0, a=aa, b=bb, kind='corner', lean=lean, win=None, z0=zst + 0.001, z1=zpb - 0.001)

    # ---- the wall frames
    studs = parts.acc('studsC', 'Cottage C studs', 'timber.beam')
    rails = parts.acc('railsC', 'Cottage C rails', 'timber.beam')
    door_posts = parts.acc('doorpostsC', 'Cottage C door posts', 'timber.post')
    win_acc = {1: parts.acc('wpostsC1', 'Cottage C window posts 1', 'timber.post'), 2: parts.acc('wpostsC2', 'Cottage C window posts 2', 'timber.post'),
               3: parts.acc('wpostsC3', 'Cottage C loft window studs', 'timber.beam')}
    panel_specs = []
    window_info = {}

    def make_rec(u, kind, win=None, z0=zst + 0.001, z1=zpb - 0.001, topz=None, a=None, big=False):
        a_ = a if a is not None else (rng.uniform(0.052, 0.060) if kind == 'stud' else 0.055 if kind == 'jamb' else 0.052)
        b_ = rng.uniform(0.068, 0.074)
        lean = lean_for(rng, o['lean'] * (0.5 if kind in ('wpost', 'jamb') else 1.0), big=big)
        rec = dict(u=u, w=0.0, a=a_, b=b_, kind=kind, lean=lean, win=win, z0=z0, z1=z1, topz=topz)
        V, F = post_solid(WALLS_CUR[0], u, 0.0, a_, b_, z0, z1, lean=lean, bow=(0, 0), twist=0.0, taper=1.0, topz=topz)
        if kind == 'stud':
            studs.add(V, F, col=oak(rng, OAK))
        elif kind == 'jamb':
            door_posts.add(V, F, col=oak(rng, OAK))
        else:
            win_acc[win].add(V, F, col=oak(rng, OAK))
        return rec
    WALLS_CUR = [None]

    def frame_wall(wall, name, recs, rail_fn, ztop_fn=None, zbot=zst + 0.003, ztop_const=None, door=None):
        """recs: vertical records from one end to the other (the first and last are corner or edge records). rail_fn(bay_kind, left, right) gives the rail levels [(z0, z1, opening_after)]."""
        for i in range(len(recs) - 1):
            left, right = recs[i], recs[i + 1]
            kind = 'door' if (left['kind'] == 'jamb' and right['kind'] == 'jamb') else 'window' if (left.get('win') and left.get('win') == right.get('win')) else 'plain'
            if kind == 'door':
                zl0, zl1 = g + 1.985, zpb - 0.001
                zm = 0.5 * (zl0 + zl1)
                ul = stud_at(left, zm)[0] + left['a'] - 0.085
                ur = stud_at(right, zm)[0] - right['a'] + 0.085
                V, F = wbox(wall, ul, ur, -0.06, 0.06, zl0, zl1)
                rails.add(V, F, col=oak(rng, OAK))
                window_info.setdefault(name + 'door', dict(u0=stud_at(left, zm)[0] + left['a'], u1=stud_at(right, zm)[0] - right['a'], zlintel=zl0))
                continue
            levels = rail_fn(kind, left, right)
            pen = 0.075 if kind == 'window' else 0.043
            for (rz0, rz1, opening) in levels:
                zm = 0.5 * (rz0 + rz1)
                ul = stud_at(left, zm)[0] + left['a'] - pen
                ur = stud_at(right, zm)[0] - right['a'] + pen
                V, F = wbox(wall, ul, ur, -0.06, 0.06, rz0, rz1)
                rails.add(V, F, col=oak(rng, OAK))
            # panels are the spaces between the rails, except the opening of a window
            spans = []
            cur = zbot
            skip_next = False
            for (rz0, rz1, opening) in levels:
                if not skip_next:
                    spans.append((cur, rz0 - 0.003))
                cur = rz1 + 0.003
                skip_next = opening
            spans.append((cur, None))
            for (zb, zt_) in spans:
                top = zt_ if zt_ is not None else (ztop_fn if ztop_fn is not None else ztop_const)
                if not callable(top) and top - zb < 0.08:
                    continue
                panel_specs.append(dict(wall=wall, left=left, right=right, z0=zb, z1=top, name=name, kind=kind))

    # south, west and east walls: plain bays with one mid rail
    mid_rail = lambda kind, l, r: [(g + 1.25, g + 1.35, False)]  # noqa: E731

    def plain_recs(wall, length, bays, c0, c1, base_u):
        recs = [c0]
        us = [length * k / bays for k in range(1, bays)]
        for u in us:
            WALLS_CUR[0] = wall
            recs.append(make_rec(u + rng.uniform(-0.03, 0.03), 'stud'))
        recs.append(c1)
        return recs

    WALLS_CUR[0] = WS
    recs = plain_recs(WS, LX, 9, corner_rec('SW', WS, 0.0), corner_rec('SE', WS, LX), 0)
    frame_wall(WS, 'S', recs, mid_rail, ztop_const=zpb - 0.003)
    WALLS_CUR[0] = WW
    recs = plain_recs(WW, LY, 6, corner_rec('SW', WW, 0.0), corner_rec('NW', WW, LY), 0)
    frame_wall(WW, 'W', recs, mid_rail, ztop_const=zpb - 0.003)
    WALLS_CUR[0] = WE
    recs = plain_recs(WE, LY, 6, corner_rec('SE', WE, 0.0), corner_rec('NE', WE, LY), 0)
    frame_wall(WE, 'E', recs, mid_rail, ztop_const=zpb - 0.003)

    # north wall: two windows and the door
    WALLS_CUR[0] = WN
    win_x = {1: -28.2, 2: -23.8}
    xs_n = [(-29.05, 'stud', None), (win_x[1] - 0.277, 'wpost', 1), (win_x[1] + 0.277, 'wpost', 1), (-27.25, 'stud', None), (-26.505, 'jamb', None),
            (-25.495, 'jamb', None), (-24.85, 'stud', None), (win_x[2] - 0.277, 'wpost', 2), (win_x[2] + 0.277, 'wpost', 2), (-22.9, 'stud', None)]
    recs = [corner_rec('NW', WN, 0.0)]
    for x, kind, win in xs_n:
        jitter = rng.uniform(-0.02, 0.02) if kind == 'stud' else 0.0
        recs.append(make_rec(x - xw0 + jitter, kind, win=win))
    recs.append(corner_rec('NE', WN, LX))

    def north_rails(kind, l, r):
        if kind == 'window':
            return [(g + 0.90, g + 1.00, True), (g + 1.60, g + 1.70, False)]
        return [(g + 1.25, g + 1.35, False)]
    frame_wall(WN, 'N', recs, north_rails, ztop_const=zpb - 0.003)
    for w in (1, 2):
        window_info[w] = dict(u=win_x[w] - xw0, z0=g + 1.00, z1=g + 1.60, wall=WN)

    # ---- gable walls above the gable plates: studs, rails, panels up to the principal rafters
    def zin(x, y):
        h = abs(y - yc)
        return ZS + (hp - h) * TAN - 0.16 / COS - 0.002

    def gable(wall, name, rels, loft_window=False):
        top_u = lambda u: max(zin(0.0, yw0 + u) - 0.003, zpt + 0.03)  # noqa: E731
        WALLS_CUR[0] = wall
        edge_l = dict(u=(yc - 2.09) - yw0, w=0.0, a=0.0, b=0.0, kind='edge', lean=(0.0, 0.0), win=None, z0=zpt, z1=zpt + 1.0)
        edge_r = dict(u=(yc + 2.09) - yw0, w=0.0, a=0.0, b=0.0, kind='edge', lean=(0.0, 0.0), win=None, z0=zpt, z1=zpt + 1.0)
        recs_g = [edge_l]
        for rel, kind, win in rels:
            u = yc + rel - yw0
            topz = lambda x, y: zin(x, y)  # noqa: E731
            rec = make_rec(u + (rng.uniform(-0.02, 0.02) if kind == 'stud' else 0.0), kind, win=win, z0=zpt + 0.001, z1=zin(0, yc + rel), topz=topz)
            recs_g.append(rec)
        recs_g.append(edge_r)

        def gable_rails(kind, l, r):
            ztops = [min(top_u(stud_at(l, zpt)[0] + l['a']), top_u(stud_at(r, zpt)[0] - r['a']))]
            if kind == 'window':
                return [(g + 2.95, g + 3.05, True), (g + 3.55, g + 3.65, False)]
            if ztops[0] > g + 3.10:
                return [(g + 2.95, g + 3.05, False)]
            return []
        frame_wall(wall, name, recs_g, gable_rails, ztop_fn=top_u, zbot=zpt + 0.003)
        return recs_g

    gw_rels = [(-1.5, 'stud', None), (-0.9, 'stud', None), (-0.3, 'stud', None), (0.3, 'stud', None), (0.9, 'stud', None), (1.5, 'stud', None)]
    ge_rels = [(-1.65, 'stud', None), (-0.95, 'stud', None), (-0.277, 'wpost', 3), (0.277, 'wpost', 3), (0.95, 'stud', None), (1.65, 'stud', None)]
    gable(WW, 'GW', gw_rels)
    gable(WE, 'GE', ge_rels, loft_window=True)
    window_info[3] = dict(u=(yc - yw0), z0=g + 3.05, z1=g + 3.55, wall=WE)

    # ---- gable plates (flat, between the long plates) and the long wall plates (wedge seat cut to the roof slope)
    plate = parts.acc('plateC', 'Cottage C wall plate', 'timber.beam')
    for wall in (WW, WE):
        V, F = wbox(wall, 0.083, LY - 0.083, -0.07, 0.07, zpb, zpt)
        plate.add(V, F, col=oak(rng, OAK))

    SAG = [rng.uniform(0.026, 0.034) * o['sag'], rng.uniform(0.032, 0.040) * o['sag']]
    xt = [xw0, xm, xw1]

    def sag_fn(x):
        x = np.asarray(x, float)
        out = np.zeros_like(x)
        for k in range(2):
            m = (x >= xt[k]) & (x <= xt[k + 1])
            out[m] = SAG[k] * np.sin(np.pi * (x[m] - xt[k]) / (xt[k + 1] - xt[k]))
        return out

    def zU(x, h):
        return ZS + (hp - h) * TAN - sag_fn(x) * (1 - h / hp)

    def slope(x):
        return -TAN + sag_fn(x) / hp

    def nvec(x, s):
        m = float(slope(x))
        n = np.array([0.0, s * (-m), 1.0])
        return n / np.linalg.norm(n)

    for s in (1, -1):
        for (xa, xb) in ((X0, xm - 0.008), (xm + 0.008, X1)):
            rings = []
            for x in np.linspace(xa, xb, 7):
                hi, ho = hp - 0.08, hp + 0.08
                pts = [(yc + s * hi, zpb), (yc + s * ho, zpb), (yc + s * ho, float(zU(x, ho))), (yc + s * hi, float(zU(x, hi)))]
                rings.append(np.array([(x, p[0], p[1]) for p in pts]))
            V, F = loft(rings)
            plate.add(V, F, col=oak(rng, OAK))

    # ---- rafters: common rafters on the plate, the purlin and the ridge; principal rafters at the three truss lines
    rafters = parts.acc('raftersC', 'Cottage C rafters', 'timber.beam')
    principals = parts.acc('principalsC', 'Cottage C principal rafters', 'timber.beam')

    def roof_beam(x, s, ha, hb, width, d_lo, d_hi):
        n = nvec(x, s)
        ex = np.array([1.0, 0.0, 0.0])
        rings = []
        for h in (ha, hb):
            L = np.array([x, yc + s * h, float(zU(x, h))])
            rings.append(np.array([L - ex * width / 2 + n * d_lo, L + ex * width / 2 + n * d_lo, L + ex * width / 2 + n * d_hi, L - ex * width / 2 + n * d_hi]))
        return loft(rings)
    h_edge = hp + hw + 0.5
    rafter_x = []
    for k in range(2):
        for i in range(1, 6):
            rafter_x.append(xt[k] + (xt[k + 1] - xt[k]) * i / 6 + rng.uniform(-0.025, 0.025))
    for x in rafter_x:
        for s in (1, -1):
            V, F = roof_beam(x + rng.uniform(-0.01, 0.01), s, h_edge, 0.03, rng.uniform(0.082, 0.098), 0.0, 0.09)
            rafters.add(V, F, col=oak(rng, WEATHER, 0.12))
    for x in xt:
        for s in (1, -1):
            V, F = roof_beam(x, s, hp, 0.03, 0.14, -0.16, 0.004)
            principals.add(V, F, col=oak(rng, WEATHER, 0.1))

    # purlins: one on each slope, butted between the principal rafters (a bay each)
    purlins = parts.acc('purlinsC', 'Cottage C purlins', 'timber.beam')
    hpur = 1.15
    for s in (1, -1):
        for k in range(2):
            xa, xb = xt[k] + 0.02, xt[k + 1] - 0.02
            rings = []
            for x in np.linspace(xa, xb, 9):
                n = nvec(x, s)
                dh = 0.06 * math.cos(math.atan(abs(float(slope(x)))))
                o1 = np.array([x, yc + s * (hpur - dh), float(zU(x, hpur - dh))])
                o2 = np.array([x, yc + s * (hpur + dh), float(zU(x, hpur + dh))])
                rings.append(np.array([o1, o2, o2 - n * 0.12, o1 - n * 0.12]))
            V, F = loft(rings)
            purlins.add(V, F, col=oak(rng, WEATHER, 0.1))

    # collars at the three truss lines (between the principals, up near the ridge)
    collars = parts.acc('collarsC', 'Cottage C collars', 'timber.beam')
    hc = 0.85
    zc_mid = float(zU(0.0, hc)) - 0.078 / COS
    zc0, zc1 = zc_mid - 0.06, zc_mid + 0.06

    def h_range(z):
        return hp - (z + 0.16 / COS - ZS) / TAN, hp - (z - 0.004 / COS - ZS) / TAN
    lo_top = h_range(zc1)
    lo_bot = h_range(zc0)
    half = max(lo_top[0], lo_bot[0]) + 0.03
    facts['collar_embed'] = round(half - max(lo_top[0], lo_bot[0]), 3)
    for k_, x in enumerate(xt):
        V, F = box(x - 0.06, x + 0.06, yc - half, yc + half, zc0, zc1)
        collars.add(V, F, col=oak(rng, WEATHER, 0.1))
        # a king post stands on the collar and carries the ridge piece (one object each, so that the kit leans each about its own foot)
        kp = parts.acc('kingC%d' % (k_ + 1), 'Cottage C king post %d' % (k_ + 1), 'timber.post')
        zr_here = float(ZS + hp * TAN) - 0.09
        kw = 0.052 + 0.003 * k_
        V, F = box(x - kw - 0.002, x + kw + 0.002, yc - kw, yc + kw, zc1 + 0.001, zr_here - 0.001)
        kp.add(V, F, col=oak(rng, WEATHER, 0.1))

    # ---- door leaf, hinges, doorstep, lintel already built; the leaf rests on the doorstep
    step_top = g + 0.17
    dinfo = window_info['Ndoor']
    leaf_u0, leaf_u1 = dinfo['u0'] + 0.004, dinfo['u1'] - 0.004
    leaf_z0, leaf_z1 = step_top + 0.001, step_top + 0.001 + 1.8
    door = parts.acc('doorC', 'Cottage C door leaf', 'timber.door')
    widths = rng.uniform(0.11, 0.145, size=7)
    V, F, cols = plank_leaf(WN, leaf_u0, leaf_u1, 0.010, 0.045, leaf_z0, leaf_z1, widths, rng, WEATHER, FRESH, replaced={3}, bow=0.005,
                            ledges=((0.25, 0.38), (1.42, 1.55)))
    door.add(V, F, col=cols)
    hinges = parts.acc('hingesC', 'Cottage C hinges', 'iron.fitting')
    hinge_set(hinges, WN, leaf_u0, +1, 0.055, [leaf_z0 + 0.315, leaf_z0 + 1.485], 0.62, wback=0.010, col=shade(IRON, 1.0))
    # a latch bar and a ring (iron) on the door
    V, F = wbox(WN, leaf_u1 - 0.22, leaf_u1 - 0.04, 0.055, 0.067, leaf_z0 + 0.93, leaf_z0 + 0.96)
    hinges.add(V, F, col=IRON)
    V, F = wbox(WN, leaf_u1 - 0.065, leaf_u1 - 0.035, 0.055, 0.070, leaf_z0 + 0.90, leaf_z0 + 0.99)
    hinges.add(V, F, col=IRON)
    step = parts.acc('stepC', 'Cottage C doorstep', 'stone.step', seat=0.06)
    V, F = stone_solid(xm, -8.075, 1.12, 0.76, 0.0, g - 0.06, step_top, rng, chamfer=(0.09, 0.13))
    step.add(V, F, col=stone_colour(hexl('#8B8880'), g, 1.0, 0.0))

    # ---- floor.earth inside the footing
    floor = parts.acc('floorC', 'Cottage C earth floor', 'floor.earth', smooth=True, seat=0.08)
    xs = np.linspace(-29.40, -22.60, 35)
    ys = np.linspace(-12.52, -8.48, 21)
    XX, YY = np.meshgrid(xs, ys, indexing='ij')
    ZZ = g + 0.05 + 0.007 * noise.value(XX * 1.7, YY * 1.7, 0.5)
    T = np.stack([XX, YY, ZZ], axis=-1)
    Bb = np.array([[(x, ys[0], g - 0.08), (x, ys[-1], g - 0.08)] for x in xs])
    V, F, nt = grid_slab(T, Bb)
    earth = hexl('#4B3B2B')
    floor.add(V, F, col=lambda P: shade(np.tile(earth, (len(P), 1)), 1 + 0.12 * noise.value(P[:, 0] * 2, P[:, 1] * 2, 0.0)))

    # ---- daub panels (with chips), wattle in the chips
    wattle = parts.acc('wattleC', 'Cottage C wattle', 'timber.generic')
    panels = parts.acc('panelsC', 'Cottage C daub panels', 'wall.timber_frame', smooth=True)
    chip_wanted = {('N', 0), ('N', 3), ('E', 1), ('E', 4), ('S', 2), ('W', 3), ('GE', 2)}
    count_by_wall = {}
    chipped = 0
    for spec in panel_specs:
        wall, left, right, name = spec['wall'], spec['left'], spec['right'], spec['name']
        k = count_by_wall.get(name, 0)
        count_by_wall[name] = k + 1
        uL = lambda z, r=left: stud_at(r, z)[0] + r['a'] - 0.015  # noqa: E731
        uR = lambda z, r=right: stud_at(r, z)[0] - r['a'] + 0.015  # noqa: E731
        z1 = spec['z1']
        chip = None
        if (name, k) in chip_wanted:
            zt_mid = z1(0.5 * (uL(spec['z0']) + uR(spec['z0']))) if callable(z1) else z1
            zc = spec['z0'] + (zt_mid - spec['z0']) * rng.uniform(0.35, 0.6)
            width = uR(zc) - uL(zc)
            ru = min(width * 0.36, 0.26) * o['chip']
            rz = min((zt_mid - spec['z0']) * 0.32, 0.30) * o['chip']
            uc = uL(zc) + width * rng.uniform(0.40, 0.60)
            chip = (uc, zc, ru, rz)
            chipped += 1
        Fg, Bg, mask = daub_panel(wall, uL, uR, spec['z0'], z1, rng, noise2, None, chip=chip)
        V, F = slab_between(Fg, Bg)
        tint = rng.uniform(0.94, 1.06)
        nF = Fg.shape[0] * Fg.shape[1]
        col = np.zeros((len(V), 4))
        P = V
        macro = 1 + 0.07 * noise.value(P[:, 0] * 1.1, P[:, 1] * 1.1, P[:, 2] * 1.1)
        c = shade(np.tile(DAUB, (len(P), 1)), macro * tint)
        c = mixc(c, MUD, smoothstep(g + 1.05, g + 0.55, P[:, 2]) * 0.55)
        c = shade(c, 1 - 0.16 * smoothstep(zpb - 0.35, zpb, P[:, 2]))
        m_full = np.zeros(len(V))
        m_full[:nF] = mask.reshape(-1)
        c = mixc(c, CLAY, m_full)
        panels.add(V, F, col=c)
        if chip is not None:
            uc, zc, ru, rz = chip
            n = 3 if ru > 0.19 else 2
            zb0 = spec['z0'] - 0.0025
            zt0 = (z1(uc) if callable(z1) else z1) - 0.004
            su = [uc + (i - (n - 1) / 2) * 0.25 for i in range(n)]
            for u_ in su:
                V, F = wbox(wall, u_ - 0.025, u_ + 0.025, -0.015, 0.035, zb0, min(zt0, zb0 + 1.3))
                wattle.add(V, F, col=shade(WATTLE, rng.uniform(0.85, 1.12)))
            for i in range(n - 1):
                for zf in (0.30, 0.62):
                    zz = zb0 + (min(zt0, zb0 + 1.3) - zb0) * zf
                    V, F = wbox(wall, su[i] - 0.02, su[i + 1] + 0.02, -0.012, 0.040, zz - 0.025, zz + 0.025)
                    wattle.add(V, F, col=shade(WATTLE, rng.uniform(0.9, 1.15)))
    facts['chipped_panels'] = chipped
    facts['panels'] = len(panel_specs)

    # ---- windows: opening 0.45 x 0.6, shutter leaves (no glass), one ajar
    shutters = parts.acc('shuttersC', 'Cottage C shutters', 'timber.shutter')
    sh_hinges = parts.acc('shhingesC', 'Cottage C shutter hinges', 'iron.fitting')

    def shutter_pair(w, which, ajar_leaf=None):
        info = window_info[w]
        wall = info['wall']
        uc = info['u']
        zb, zt_ = info['z0'] - 0.005, info['z1'] + 0.015
        wf = 0.073
        leaves = [(uc - 0.255, uc - 0.004, 'L'), (uc + 0.004, uc + 0.255, 'R')] if which == 'pair' else [(uc - 0.255, uc + 0.255, 'R')]
        for (a, b, tag) in leaves:
            u_h = a if tag == 'L' else b
            d = +1 if u_h == a else -1
            widths = rng.uniform(0.9, 1.15, size=2 if which == 'pair' else 4)
            replaced = {int(rng.integers(0, len(widths)))} if rng.random() < 0.55 else set()
            V, F, cols = plank_leaf(wall, a, b, wf, 0.025, zb, zt_, widths, rng, hexl('#4F4337'), FRESH, replaced=replaced, bow=0.003)
            is_ajar = (ajar_leaf is not None and tag == ajar_leaf)
            pivot, ang = None, 0.0
            if is_ajar:
                pivot = wall.P(u_h, wf, 0.0)[:2]
                dv = wall.eu[:2] * d
                cross = dv[0] * wall.ew[1] - dv[1] * wall.ew[0]
                ang = math.radians(64) * (1 if cross > 0 else -1)
                V = rot_z(V, ang, pivot)
            shutters.add(V, F, col=cols)
            for zrel in (0.20, zt_ - zb - 0.20):
                zz = zb + zrel
                length = 0.2
                strap = wbox(wall, min(u_h, u_h + d * length), max(u_h, u_h + d * length), wf + 0.025, wf + 0.036, zz - 0.02, zz + 0.02)
                pin = wbox(wall, min(u_h - d * 0.035, u_h + d * 0.012), max(u_h - d * 0.035, u_h + d * 0.012), wf - 0.065, wf + 0.040, zz - 0.03, zz + 0.03)
                sV = rot_z(strap[0], ang, pivot) if is_ajar else strap[0]
                sh_hinges.add(sV, strap[1], col=IRON)
                sh_hinges.add(*pin, col=IRON)
    shutter_pair(1, 'pair')
    shutter_pair(2, 'pair', ajar_leaf=+1)
    shutter_pair(3, 'single')

    # ---- the thatch: two slabs resting on the rafters, and a rolled ridge cap
    thatch_col = tone3(hexl(o['thatch_hex']), hexl('#9C8A64'), hexl('#CBB07A'), o['thatch_tone'])
    cap_col = hexl('#8E7442')
    De = h_edge + 0.07
    xs_t = np.linspace(X0 - 0.30, X1 + 0.30, 81)
    Ds = np.linspace(0.0, De, 29)
    XXt, DDt = np.meshgrid(xs_t, Ds, indexing='ij')
    sg = sag_fn(XXt)
    mm = -TAN + sg / hp
    cosf = 1 / np.sqrt(1 + mm * mm)
    sinf = -mm * cosf

    def zT_of(x, D):
        sgx = sag_fn(x)
        m = -TAN + sgx / hp
        cf = 1 / np.sqrt(1 + m * m)
        sf = -m * cf
        hU = D - 0.09 * sf
        return ZS + (hp - hU) * TAN - sgx * (1 - hU / hp) + 0.09 * cf
    zT = zT_of(XXt, DDt)
    tv0 = 0.35 / cosf
    slabs = {}
    for s, key, nm in ((1, 'thatchN', 'Cottage C thatch north'), (-1, 'thatchS', 'Cottage C thatch south')):
        yw = yc + s * DDt
        damp = smoothstep(0.0, 0.45, DDt)
        lump = (0.10 * noise.value(XXt * 1.15, yw * 1.15, 0.0) + 0.045 * noise2.value(XXt * 2.3, yw * 2.3, 1.0)) * o['thatch_lump'] * damp
        course = 0.012 * np.sin(DDt * 2 * np.pi / 0.40)
        ee = np.minimum.reduce([De - DDt, XXt - xs_t[0], xs_t[-1] - XXt])
        roll = 0.07 * o['thatch_roll'] * np.exp(-((De - DDt - 0.30) / 0.15) ** 2)
        tv = tv0 * (1 + lump + roll) + course * damp
        tv = tv * (1 - 0.40 * smoothstep(0.17, 0.0, ee))
        Ptop = np.stack([XXt, yw, zT + tv], axis=-1)
        Bb = np.array([[(x, yc, float(zT_of(x, 0.0)) + 0.0005), (x, yc + s * De, float(zT_of(x, De)) + 0.0005)] for x in xs_t])
        V, F, nt = grid_slab(Ptop, Bb)
        col = np.zeros((len(V), 4))
        nTop = Ptop.shape[0] * Ptop.shape[1]
        P = V
        straw = shade(np.tile(thatch_col, (len(P), 1)), 1 + 0.10 * noise.value(P[:, 0] * 0.8, P[:, 1] * 0.8, 0.0) + 0.05 * np.sin(P[:, 1] * 2 * np.pi / 0.40 * 0.5))
        edge_dark = smoothstep(0.35, 0.0, np.minimum(De - np.abs(P[:, 1] - yc), 0.35))
        straw = mixc(straw, hexl('#7C6238'), edge_dark * 0.45)
        under = np.zeros(len(P))
        under[nTop:] = 1.0
        straw = mixc(straw, hexl('#3F3224'), under * 0.8)
        flags = np.zeros(len(F), bool)
        flags[:nt] = True
        parts.acc(key, nm, 'roof.thatch', smooth=True).add(V, F, col=straw, smooth=flags)

    # ridge piece (two lengths, one in each bay): flat underneath, its top cut to the slope of the thatch so that the thatch rests on it
    ridge = parts.acc('ridgeC', 'Cottage C ridge piece', 'timber.beam')
    for (xa, xb) in ((X0, xm - 0.008), (xm + 0.008, X1)):
        rings = []
        for x in np.linspace(xa, xb, 9):
            zr = float(zU(x, 0.0))
            rings.append(np.array([(x, yc - 0.085, zr - 0.09), (x, yc + 0.085, zr - 0.09), (x, yc + 0.085, float(zT_of(x, 0.085)) - 0.001), (x, yc, float(zT_of(x, 0.0)) - 0.001),
                                   (x, yc - 0.085, float(zT_of(x, 0.085)) - 0.001)]))
        V, F = loft(rings)
        ridge.add(V, F, col=oak(rng, WEATHER, 0.1))

    # ridge cap: a rolled ridge along the ridge line
    cap = parts.acc('thatchcapC', 'Cottage C thatch ridge cap', 'roof.thatch', smooth=True)
    rings = []
    for x in np.linspace(X0 - 0.30, X1 + 0.30, 33):
        z_a = float(zT_of(x, 0.0)) + float(0.35 / (1 / math.sqrt(1 + float(slope(x)) ** 2)))
        tanp = abs(float(slope(x)))
        bulge = 0.20 + 0.03 * float(noise.value(x * 1.3, 0.0, 0.5))
        Dp = [-0.46, -0.30, -0.15, 0.0, 0.15, 0.30, 0.46]
        low = [(yc + d_, z_a - abs(d_) * tanp - 0.06) for d_ in Dp]
        top = [(yc + d_, z_a - abs(d_) * tanp + bulge * (1 - (d_ / 0.52) ** 2) ** 0.8 * (1 + 0.1 * float(noise2.value(x * 3, d_ * 3, 0.0)))) for d_ in Dp[::-1]]
        rings.append(np.array([(x, p[0], p[1]) for p in low + top]))
    V, F = loft(rings)
    capc = np.tile(cap_col, (len(V), 1))
    capc = shade(capc, 1 + 0.08 * noise.value(V[:, 0] * 0.9, V[:, 1], 0.0))
    cap.add(V, F, col=capc)
    facts['zU_ridge_mid'] = float(zU(xm, 0.0))
    facts['sag_cm'] = [round(s_ * 100, 1) for s_ in SAG]
    facts['H_ridge_top'] = float(zU(xm, 0.0)) + 0.35 / COS + 0.2 - g
    return facts
