

# ------------------------------------------------------------------ cottage D
def outline_points(cx, cy, hx, hy, R, n_e, n_n, n_arc=8):
    """A rounded rectangle, counter-clockwise from the start of the east straight: sections east, north-east arc, north, north-west arc, west, south-west arc, south, south-east arc.
    Returns (points (N, 2), section starts [list of 8 indices], outward unit normals (N, 2))."""
    pts, nor, starts = [], [], []

    def straight(p0, p1, n, normal):
        for k in range(n):
            t = k / n
            pts.append((p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t))
            nor.append(normal)

    def arc(c, a0, n):
        for k in range(n):
            a = math.radians(a0 + 90.0 * k / n)
            pts.append((c[0] + R * math.cos(a), c[1] + R * math.sin(a)))
            nor.append((math.cos(a), math.sin(a)))
    starts.append(len(pts)); straight((cx + hx, cy - hy + R), (cx + hx, cy + hy - R), n_e, (1.0, 0.0))
    starts.append(len(pts)); arc((cx + hx - R, cy + hy - R), 0, n_arc)
    starts.append(len(pts)); straight((cx + hx - R, cy + hy), (cx - hx + R, cy + hy), n_n, (0.0, 1.0))
    starts.append(len(pts)); arc((cx - hx + R, cy + hy - R), 90, n_arc)
    starts.append(len(pts)); straight((cx - hx, cy + hy - R), (cx - hx, cy - hy + R), n_e, (-1.0, 0.0))
    starts.append(len(pts)); arc((cx - hx + R, cy - hy + R), 180, n_arc)
    starts.append(len(pts)); straight((cx - hx + R, cy - hy), (cx + hx - R, cy - hy), n_n, (0.0, -1.0))
    starts.append(len(pts)); arc((cx + hx - R, cy - hy + R), 270, n_arc)
    return np.array(pts, float), starts, np.array(nor, float)


def cob_piece(Pout, Pin, Nrm, i0, i1, zbot, ztop_fn, noise, rows, bulge, lump, ring_total):
    """One piece of the cob wall ring (columns i0..i1 inclusive, counter-clockwise): outer face, inner face, top, bottom and two end caps, as ONE closed solid. ztop_fn(x, y) gives the
    top height of a column; the top row is exact (no lumps) so that a plate or a roof can lie on it; the walls bulge a little and are lumpy."""
    idx = [(i % ring_total) for i in range(i0, i1 + 1)]
    n = len(idx)
    O = np.zeros((n, rows + 1, 3))
    I = np.zeros((n, rows + 1, 3))
    for c, i in enumerate(idx):
        po, pi_, nn = Pout[i], Pin[i], Nrm[i]
        zt = max(ztop_fn(po[0], po[1]), zbot + 0.2)
        zt_in = max(ztop_fn(pi_[0], pi_[1]), zbot + 0.2)
        for j in range(rows + 1):
            t = j / rows
            w = (1 - smoothstep(0.80, 1.0, t)) * smoothstep(0.0, 0.06, t)
            for (P, zz, side, store) in ((po, zt, 1.0, O), (pi_, zt_in, -1.0, I)):
                z = zbot + t * (zz - zbot)
                d = (bulge * math.sin(math.pi * t) ** 0.8 + lump * float(noise.value(P[0] * 1.9, P[1] * 1.9, z * 1.9))) * w
                if side < 0:
                    d *= 0.55
                store[c, j] = (P[0] + side * nn[0] * d, P[1] + side * nn[1] * d, z)
    F = []
    for c in range(n - 1):
        for j in range(rows):
            F.append((tuple_idx(c, j, rows, n, 0), tuple_idx(c + 1, j, rows, n, 0), tuple_idx(c + 1, j + 1, rows, n, 0), tuple_idx(c, j + 1, rows, n, 0)))
            F.append((tuple_idx(c, j, rows, n, 1), tuple_idx(c, j + 1, rows, n, 1), tuple_idx(c + 1, j + 1, rows, n, 1), tuple_idx(c + 1, j, rows, n, 1)))
        F.append((tuple_idx(c, rows, rows, n, 0), tuple_idx(c + 1, rows, rows, n, 0), tuple_idx(c + 1, rows, rows, n, 1), tuple_idx(c, rows, rows, n, 1)))
        F.append((tuple_idx(c + 1, 0, rows, n, 0), tuple_idx(c, 0, rows, n, 0), tuple_idx(c, 0, rows, n, 1), tuple_idx(c + 1, 0, rows, n, 1)))
    for j in range(rows):
        F.append((tuple_idx(0, j, rows, n, 0), tuple_idx(0, j + 1, rows, n, 0), tuple_idx(0, j + 1, rows, n, 1), tuple_idx(0, j, rows, n, 1)))
        F.append((tuple_idx(n - 1, j, rows, n, 0), tuple_idx(n - 1, j, rows, n, 1), tuple_idx(n - 1, j + 1, rows, n, 1), tuple_idx(n - 1, j + 1, rows, n, 0)))
    V = np.vstack([O.reshape(-1, 3), I.reshape(-1, 3)])
    return V, F


def tuple_idx(c, j, rows, n, side):
    return side * n * (rows + 1) + c * (rows + 1) + j


def boolean_cut(V, F, cutters):
    """Cuts boxes (x0, x1, y0, y1, z0, z1) out of a closed solid with Blender's exact boolean, using temporary objects that are removed again. Returns (V, F)."""
    mesh = bpy.data.meshes.new('cs_tmp_cob')
    mesh.from_pydata([tuple(v) for v in V], [], [tuple(f) for f in F])
    mesh.update()
    obj = bpy.data.objects.new('cs_tmp_cob', mesh)
    bpy.context.scene.collection.objects.link(obj)
    temps = [obj]
    meshes = [mesh]
    for k, c in enumerate(cutters):
        cV, cF = box(*c)
        cm = bpy.data.meshes.new(f'cs_tmp_cut{k}')
        cm.from_pydata([tuple(v) for v in cV], [], cF)
        cm.update()
        co = bpy.data.objects.new(f'cs_tmp_cut{k}', cm)
        bpy.context.scene.collection.objects.link(co)
        temps.append(co)
        meshes.append(cm)
        mod = obj.modifiers.new(f'cut{k}', 'BOOLEAN')
        mod.operation = 'DIFFERENCE'
        mod.solver = 'EXACT'
        mod.object = co
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    m2 = bpy.data.meshes.new_from_object(ev)
    n = len(m2.vertices)
    flat = np.empty(n * 3)
    m2.vertices.foreach_get('co', flat)
    V2 = flat.reshape(-1, 3)
    F2 = [tuple(p.vertices) for p in m2.polygons]
    for t in temps:
        bpy.data.objects.remove(t, do_unlink=True)
    for m in meshes + [m2]:
        bpy.data.meshes.remove(m)
    return V2, F2


def build_D(parts, o):
    """Cottage D: the smallest, pale cob walls with rounded corners and no frame, silver shingles at 42 degrees, one low plank door in the north gable end."""
    rng = np.random.default_rng(o['seed'] + 202)
    noise = Noise(o['seed'] + 17)
    noise2 = Noise(o['seed'] + 18, scales=(1.1, 0.5, 0.25))
    X0, X1, Y0, Y1 = 2.15, 5.85, -10.2, -5.8
    cx, cy = 4.0, -8.0
    tw = 0.5
    xw0, xw1, yw0, yw1 = X0 + tw / 2, X1 - tw / 2, Y0 + tw / 2, Y1 - tw / 2
    hp = 1.6
    g, g_low = ground_top(X0 - 0.3, X1 + 0.3, Y0 - 0.3, Y1 + 0.3)
    zp = g + 0.30
    zc = g + 1.92
    zpb = zc + 0.001
    ZS = g + 2.04
    TAN, COS, SIN = math.tan(math.radians(42)), math.cos(math.radians(42)), math.sin(math.radians(42))
    WNd = Wall((xw0, yw1), (1, 0), (0, 1), xw1 - xw0)
    WEd = Wall((xw1, yw0), (0, 1), (1, 0), yw1 - yw0)
    COB = tone3(hexl(o['cob_hex']), hexl('#A39170'), hexl('#CFBF9C'), o['cob_tone'])
    SPL = hexl('#6E6050')
    WEATHER, FRESH = hexl('#6B5E4C'), hexl('#8A6A45')
    IRON = hexl('#2A2826')
    STONE = hexl('#7C7A73')
    facts = dict(g=g, g_low=g_low)

    # ---- plinth: rubble stones 0.5 wide, flat on top 0.3 m above the pad, none under the door
    foot = parts.acc('footD', 'Cottage D plinth', 'stone.footing', seat=0.03)

    def fill(start, end):
        pos, out = start, []
        while end - pos > 0.05:
            L = rng.uniform(0.45, 0.8)
            if end - pos - L < 0.36:
                L = end - pos
            out.append((pos + L / 2, L - 0.02))
            pos += L
        return out
    runs = []
    for (a, b) in ((xw0 - 0.25, 3.50), (4.50, xw1 + 0.25)):
        for c, L in fill(a, b):
            runs.append((c, yw1, L, 0.0))
    for c, L in fill(xw0 - 0.25, xw1 + 0.25):
        runs.append((c, yw0, L, 0.0))
    for c, L in fill(yw0 + 0.25 + 0.015, yw1 - 0.25 - 0.015):
        runs.append((xw0, c, L, math.pi / 2))
        runs.append((xw1, c, L, math.pi / 2))
    for (sx, sy, L, rot) in runs:
        sx, sy = (sx, sy + rng.uniform(-0.01, 0.01)) if rot == 0.0 else (sx + rng.uniform(-0.01, 0.01), sy)
        width = rng.uniform(0.445, 0.465)
        corner = (L > 0.5 and (abs(sx - xw0) < 0.45 or abs(sx - xw1) < 0.45) and rot == 0.0) 
        zb = pk.ground_height_at(sx, sy) - 0.03
        V, F = stone_solid(sx, sy, L, width, rot, zb, zp, rng, chamfer=(0.12, 0.2) if corner else (0.05, 0.10))
        foot.add(V, F, col=stone_colour(STONE, g, rng.uniform(0.82, 1.12)))

    # ---- the cob walls: four pieces (east, north gable, west, south gable) of a ring with rounded corners, cut for the door and the window
    def zU_plane(h, sag=0.0):
        return ZS + (hp - h) * TAN - sag * (1 - h / hp)

    def gable_top(x, y):
        h = abs(x - cx)
        hU = h - 0.07 * SIN
        return float(ZS + (hp - hU) * TAN + 0.07 * COS) - 0.001
    Pout, starts, Nrm = outline_points(cx, cy, 1.85, 2.2, 0.45, 22, 20)
    Pin, _, _ = outline_points(cx, cy, 1.35, 1.7, 0.06, 22, 20)
    N = len(Pout)
    s = starts + [N]
    flat_top = lambda x, y: zc  # noqa: E731
    gab_top = lambda x, y: max(zc, gable_top(x, y))  # noqa: E731
    pieces = [('E', s[0], s[1], flat_top), ('N', s[1], s[4], gab_top), ('W', s[4], s[5], flat_top), ('S', s[5], s[8], gab_top)]
    cob = parts.acc('cobD', 'Cottage D cob walls', 'wall.cob', smooth=True)
    cut_door = [(3.52, 4.48, yw1 - 0.60, yw1 + 0.45, zp - 0.4, g + 1.77), (3.32, 4.68, yw1 - 0.60, yw1 + 0.45, g + 1.77, g + 1.90)]
    cut_window = [(xw1 - 0.4, xw1 + 0.6, -8.25, -7.75, g + 1.05, g + 1.50), (xw1 - 0.4, xw1 + 0.6, -8.37, -7.63, g + 1.50, g + 1.62), (xw1 - 0.4, xw1 + 0.6, -8.37, -7.63, g + 0.93, g + 1.05)]
    for name, i0, i1, topfn in pieces:
        V, F = cob_piece(Pout, Pin, Nrm, i0, i1, zp + 0.0005, topfn, noise, 14, 0.03 * (0.6 + 0.4 * o['cob_lump']), 0.018 * o['cob_lump'], N)
        if name == 'N':
            V, F = boolean_cut(V, F, cut_door)
        elif name == 'E':
            V, F = boolean_cut(V, F, cut_window)
        P = V
        macro = 1 + 0.06 * noise.value(P[:, 0] * 1.2, P[:, 1] * 1.2, P[:, 2] * 1.2) + 0.03 * noise2.value(P[:, 0] * 3.1, P[:, 1] * 3.1, P[:, 2] * 3.1)
        c = shade(np.tile(COB, (len(P), 1)), macro * rng.uniform(0.97, 1.03))
        c = mixc(c, SPL, smoothstep(g + 0.85, g + 0.30, P[:, 2]) * 0.55)
        c = shade(c, 1 - 0.12 * smoothstep(zc - 0.4, zc, P[:, 2]) * (1 - smoothstep(zc, zc + 0.5, P[:, 2])))
        cob.add(V, F, col=c)
    facts['cob_tris'] = cob.tris

    # ---- the door frame, lintel, doorstep, leaf and hinges
    step_top = g + 0.15
    dposts = parts.acc('doorpostsD', 'Cottage D door posts', 'timber.post')
    for xs_, w_ in ((3.52, 0.08), (4.40, 0.08)):
        a = rng.uniform(0.0, 0.0)
        V, F = post_solid(WNd, (xs_ + w_ / 2) - xw0, 0.18, w_ / 2, 0.07, step_top + 0.001, g + 1.769, lean=lean_for(rng, o['lean'] * 0.5), twist=rng.uniform(-0.02, 0.02))
        dposts.add(V, F, col=oak(rng, WEATHER))
    beams = parts.acc('beamsD', 'Cottage D lintels and cill', 'timber.beam')
    V, F = box(3.325, 4.675, yw1 - 0.235, yw1 + 0.235, g + 1.771, g + 1.895)
    beams.add(V, F, col=oak(rng, WEATHER))
    V, F = box(xw1 - 0.245, xw1 + 0.245, -8.365, -7.635, g + 0.931, g + 1.05)
    beams.add(V, F, col=oak(rng, WEATHER))
    V, F = box(xw1 - 0.245, xw1 + 0.245, -8.365, -7.635, g + 1.501, g + 1.619)
    beams.add(V, F, col=oak(rng, WEATHER))
    step = parts.acc('stepD', 'Cottage D doorstep', 'stone.step', seat=0.06)
    V, F = stone_solid(4.0, -5.865, 1.15, 1.07, 0.0, g - 0.06, step_top, rng, chamfer=(0.09, 0.14))
    step.add(V, F, col=stone_colour(hexl('#8B8880'), g, 1.0, 0.0))
    door = parts.acc('doorD', 'Cottage D door leaf', 'timber.door')
    leaf_u0, leaf_u1 = 3.604 - xw0, 4.396 - xw0
    leaf_z0, leaf_z1 = step_top + 0.001, step_top + 0.001 + 1.6
    widths = rng.uniform(0.15, 0.22, size=5)
    V, F, cols = plank_leaf(WNd, leaf_u0, leaf_u1, 0.115, 0.040, leaf_z0, leaf_z1, widths, rng, WEATHER, FRESH, replaced={1}, bow=0.005, ledges=((0.22, 0.34), (1.18, 1.30)))
    door.add(V, F, col=cols)
    hinges = parts.acc('hingesD', 'Cottage D hinges', 'iron.fitting')
    hinge_set(hinges, WNd, leaf_u0, +1, 0.155, [leaf_z0 + 0.28, leaf_z0 + 1.24], 0.5, wback=0.115, col=IRON)
    V, F = wbox(WNd, leaf_u1 - 0.20, leaf_u1 - 0.04, 0.155, 0.166, leaf_z0 + 0.82, leaf_z0 + 0.85)
    hinges.add(V, F, col=IRON)

    # ---- the window in the east wall: two posts on the cill, a shutter leaf on the outside, ajar
    wposts = parts.acc('wpostsD', 'Cottage D window posts', 'timber.post')
    for (ya, yb) in ((-8.25, -8.20), (-7.80, -7.75)):
        u = 0.5 * (ya + yb) - yw0
        V, F = post_solid(WEd, u, 0.19, 0.025, 0.07, g + 1.051, g + 1.499, lean=lean_for(rng, o['lean'] * 0.3))
        wposts.add(V, F, col=oak(rng, WEATHER))
    shutters = parts.acc('shuttersD', 'Cottage D shutter', 'timber.shutter')
    sh_hinges = parts.acc('shhingesD', 'Cottage D shutter hinges', 'iron.fitting')
    u_a, u_b = -8.26 - yw0, -7.74 - yw0
    wf = 0.25 + 0.003
    zb, zt_ = g + 1.04, g + 1.52
    V, F, cols = plank_leaf(WEd, u_a, u_b, wf, 0.025, zb, zt_, rng.uniform(0.9, 1.15, size=3), rng, hexl('#5A4E40'), FRESH, replaced={2}, bow=0.003)
    pivot = WEd.P(u_a, wf, 0.0)[:2]
    dv = WEd.eu[:2]
    cross = dv[0] * WEd.ew[1] - dv[1] * WEd.ew[0]
    ang = math.radians(66) * (1 if cross > 0 else -1)
    shutters.add(rot_z(V, ang, pivot), F, col=cols)
    for zrel in (0.14, zt_ - zb - 0.14):
        zz = zb + zrel
        strap = wbox(WEd, u_a, u_a + 0.22, wf + 0.025, wf + 0.036, zz - 0.02, zz + 0.02)
        pin = wbox(WEd, u_a - 0.03, u_a + 0.012, wf - 0.004, wf + 0.040, zz - 0.03, zz + 0.03)
        sh_hinges.add(rot_z(strap[0], ang, pivot), strap[1], col=IRON)
        sh_hinges.add(*pin, col=IRON)

    # ---- floor.earth
    floor = parts.acc('floorD', 'Cottage D earth floor', 'floor.earth', smooth=True, seat=0.08)
    xs = np.linspace(2.66, 5.34, 15)
    ys = np.linspace(-9.69, -6.42, 18)
    XX, YY = np.meshgrid(xs, ys, indexing='ij')
    ZZ = g + 0.05 + 0.007 * noise.value(XX * 1.7, YY * 1.7, 0.5)
    T = np.stack([XX, YY, ZZ], axis=-1)
    Bb = np.array([[(x, ys[0], g - 0.08), (x, ys[-1], g - 0.08)] for x in xs])
    V, F, nt = grid_slab(T, Bb)
    earth = hexl('#4F3F2E')
    floor.add(V, F, col=lambda P: shade(np.tile(earth, (len(P), 1)), 1 + 0.12 * noise.value(P[:, 0] * 2, P[:, 1] * 2, 0.0)))

    # ---- the roof frame: wall plates on the cob, rafters on the plates and the purlins, ridge piece
    yA, yB = -9.7, -6.3
    SAGD = rng.uniform(0.018, 0.026) * o['sag']

    def sag_fn(y):
        y = np.asarray(y, float)
        out = np.zeros_like(y)
        m = (y >= yA) & (y <= yB)
        out[m] = SAGD * np.sin(np.pi * (y[m] - yA) / (yB - yA))
        return out

    def zU(y, h):
        return ZS + (hp - h) * TAN - sag_fn(y) * (1 - h / hp)

    def slope(y):
        return -TAN + sag_fn(y) / hp

    def nvec(y, s_):
        m = float(slope(y))
        n = np.array([s_ * (-m), 0.0, 1.0])
        return n / np.linalg.norm(n)
    plate = parts.acc('plateD', 'Cottage D wall plate', 'timber.beam')
    for s_ in (1, -1):
        rings = []
        for y in np.linspace(-9.69, -6.31, 6):
            hi, ho = hp - 0.10, hp + 0.10
            pts = [(cx + s_ * hi, zpb), (cx + s_ * ho, zpb), (cx + s_ * ho, float(zU(y, ho))), (cx + s_ * hi, float(zU(y, hi)))]
            rings.append(np.array([(p[0], y, p[1]) for p in pts]))
        V, F = loft(rings)
        plate.add(V, F, col=oak(rng, WEATHER))
    rafters = parts.acc('raftersD', 'Cottage D rafters', 'timber.beam')

    def roof_beam(y, s_, ha, hb, width, d_lo, d_hi):
        n = nvec(y, s_)
        ey = np.array([0.0, 1.0, 0.0])
        rings = []
        for h in (ha, hb):
            L = np.array([cx + s_ * h, y, float(zU(y, h))])
            rings.append(np.array([L - ey * width / 2 + n * d_lo, L + ey * width / 2 + n * d_lo, L + ey * width / 2 + n * d_hi, L - ey * width / 2 + n * d_hi]))
        return loft(rings)
    h_edge = hp + 0.25 + 0.30
    for k in range(6):
        y = -9.45 + k * 0.58 + rng.uniform(-0.02, 0.02)
        for s_ in (1, -1):
            V, F = roof_beam(y + rng.uniform(-0.008, 0.008), s_, h_edge, 0.03, rng.uniform(0.07, 0.085), 0.0, 0.07)
            rafters.add(V, F, col=oak(rng, WEATHER, 0.12))
    purlins = parts.acc('purlinD', 'Cottage D purlin', 'timber.beam')
    hpur = 0.85
    for s_ in (1, -1):
        rings = []
        for y in np.linspace(-10.05, -5.95, 11):
            n = nvec(y, s_)
            dh = 0.05 * math.cos(math.atan(abs(float(slope(y)))))
            o1 = np.array([cx + s_ * (hpur - dh), y, float(zU(y, hpur - dh))])
            o2 = np.array([cx + s_ * (hpur + dh), y, float(zU(y, hpur + dh))])
            rings.append(np.array([o1, o2, o2 - n * 0.10, o1 - n * 0.10]))
        V, F = loft(rings)
        purlins.add(V, F, col=oak(rng, WEATHER, 0.1))
    # ---- the shingles: two slabs of courses, each shingle a little different, a few slipped and a few missing
    De = h_edge + 0.07 * SIN
    ys_t = np.linspace(-10.35, -5.65, 68)
    n_rows = 64
    Ds = np.linspace(0.0, De, n_rows)
    YYt, DDt = np.meshgrid(ys_t, Ds, indexing='ij')
    sgt = sag_fn(YYt)
    mm = -TAN + sgt / hp
    cosf = 1 / np.sqrt(1 + mm * mm)
    sinf = -mm * cosf

    def zT_of(y, D):
        sgx = sag_fn(y)
        m = -TAN + sgx / hp
        cf = 1 / np.sqrt(1 + m * m)
        sf = -m * cf
        hU = D - 0.07 * sf
        return ZS + (hp - hU) * TAN - sgx * (1 - hU / hp) + 0.07 * cf
    zT = zT_of(YYt, DDt)
    # the ridge piece: flat underneath, its top cut to the slope of the shingle slabs (a few mm under them, and under the cob gable tops where its ends are sunk into them)
    ridge = parts.acc('ridgeD', 'Cottage D ridge piece', 'timber.beam')
    rings = []
    for y in np.linspace(-10.0, -6.0, 9):
        zr = float(zU(y, 0.0))
        rings.append(np.array([(cx - 0.08, y, zr - 0.08), (cx + 0.08, y, zr - 0.08), (cx + 0.08, y, float(zT_of(y, 0.08)) - 0.0035), (cx, y, float(zT_of(y, 0.0)) - 0.0035),
                               (cx - 0.08, y, float(zT_of(y, 0.08)) - 0.0035)]))
    V, F = loft(rings)
    ridge.add(V, F, col=oak(rng, WEATHER, 0.1))

    exposure = 0.141
    sl_total = De / COS
    sl = DDt / COS
    r_ = (sl_total - sl) / exposure
    kk = np.floor(r_).astype(int)
    fr = r_ - kk                                           # 0 at the butt (lower edge), up to 1 at the upper edge
    f_butt = 1 - fr
    n_courses = int(kk.max()) + 1
    n_cols = len(ys_t)
    tone = {}
    lift_off = {}
    tilt = {}
    state = {}
    block_of = np.zeros((n_courses, n_cols), int)
    joint = np.zeros((n_courses, n_cols), bool)
    for k in range(n_courses):
        pos = -int(rng.integers(0, 3)) - (k % 2)
        bid = 0
        c = 0
        starts_k = []
        while pos < n_cols + 3:
            w = int(rng.choice([2, 2, 2, 3]))
            starts_k.append(pos)
            for c in range(max(pos, 0), min(pos + w, n_cols)):
                block_of[k, c] = bid
            joint[k, max(min(pos, n_cols - 1), 0)] = True if pos >= 0 else joint[k, 0]
            tone[(k, bid)] = max(0.45, 1.0 + rng.uniform(-0.30, 0.12) * o['shingle_mix'])
            lift_off[(k, bid)] = rng.uniform(-0.004, 0.004)
            tilt[(k, bid)] = rng.uniform(-0.004, 0.004)
            state[(k, bid)] = 'ok'
            bid += 1
            pos += w
    keys = [kb for kb in tone if kb[0] > 2]
    for kb in rng.permutation(len(keys))[:6]:
        state[keys[int(kb)]] = 'missing'
    for kb in rng.permutation(len(keys))[:9]:
        if state[keys[int(kb)]] == 'ok':
            state[keys[int(kb)]] = 'slipped'
    SH = hexl(o['shingle_hex'])
    UNDER = hexl('#3E3730')
    slabs = {}
    for s_, key, nm in ((1, 'shingleE', 'Cottage D shingles east'), (-1, 'shingleW', 'Cottage D shingles west')):
        xw = cx + s_ * DDt
        lift = np.zeros_like(DDt)
        colr = np.zeros(DDt.shape + (4,))
        for i in range(n_cols):
            for j in range(n_rows):
                k = int(kk[i, j])
                f = float(f_butt[i, j])
                if DDt[i, j] < 0.34:                      # the two courses at the ridge are laid flat under the cap
                    lift[i, j] = 0.022
                    colr[i, j] = shade(SH, 0.9)
                    continue
                kb = (k, int(block_of[k, i]))
                st = state[kb]
                base = 0.010 + 0.012 * f + lift_off[kb] + tilt[kb] * ((i % 3) - 1) + 0.003 * float(noise2.value(ys_t[i] * 3, Ds[j] * 3, s_))
                tn = tone[kb]
                if st == 'missing':
                    base = -0.009
                    c = shade(UNDER, rng.uniform(0.9, 1.1))
                else:
                    if st == 'slipped':
                        base += 0.018 * f * f + 0.012
                        tn *= 0.85
                    c = shade(SH, tn)
                    warm = hexl('#B3A794') if (kb[0] + kb[1]) % 3 == 0 else hexl('#9DA29E')
                    c = mixc(c, shade(warm, tn), 0.35)
                    c = shade(c, 1 - 0.18 * smoothstep(0.30, 0.0, 1 - f_butt[i, j]) * 0)            # kept neutral
                    if fr[i, j] < 0.20:                         # the shadow under the butt of the course above
                        c = shade(c, 0.78 + 0.22 * fr[i, j] / 0.20)
                    if joint[k, i]:
                        c = shade(c, 0.78)
                    if s_ == -1 and Ds[j] > De - 0.7:
                        c = mixc(c, hexl('#7C8466'), 0.18)
                lift[i, j] = base
                colr[i, j] = c
        Ptop = np.stack([YYt * 0 + xw, YYt, zT + 0.016 + lift], axis=-1)
        Bb = np.array([[(cx, y, float(zT_of(y, 0.0)) + 0.0005), (cx + s_ * De, y, float(zT_of(y, De)) + 0.0005)] for y in ys_t])
        V, F, nt = grid_slab(Ptop, Bb)
        col = np.zeros((len(V), 4))
        col[:Ptop.shape[0] * Ptop.shape[1]] = colr.reshape(-1, 4)
        col[Ptop.shape[0] * Ptop.shape[1]:] = shade(UNDER, 0.8)
        flags = np.zeros(len(F), bool)
        flags[:nt] = True
        parts.acc(key, nm, 'roof.shingle', smooth=True).add(V, F, col=col, smooth=flags)
        slabs[key] = Ptop
    # the ridge boards: one inverted V of boards lying on the two slabs along the ridge
    cap = parts.acc('shinglecapD', 'Cottage D shingle ridge', 'roof.shingle')
    rings = []
    ytop = np.linspace(-10.35, -5.65, 13)
    for y in ytop:
        Dp = [-0.30, -0.15, 0.0, 0.15, 0.30]
        def ztop_at(D):
            return float(zT_of(y, abs(D))) + 0.016 + 0.022 + 0.001
        low = [(cx + d_, ztop_at(d_)) for d_ in Dp]
        jit = rng.uniform(-0.004, 0.004)
        top = [(cx + d_ + jit * (1 if d_ > 0 else -1), ztop_at(d_) + 0.034 + 0.004 * float(noise2.value(y * 3, d_ * 3, 1.0))) for d_ in Dp[::-1]]
        rings.append(np.array([(p[0], y, p[1]) for p in low + top]))
    V, F = loft(rings)
    cap.add(V, F, col=shade(np.tile(SH, (len(V), 1)), 0.82))
    facts['ridge_len'] = 4.0
    facts['ridge_height_above_ground'] = float(zU(-8.0, 0.0)) + 0.016 + 0.022 + 0.04 - g
    facts['sag_cm'] = round(SAGD * 100, 1)
    return facts
