

# ------------------------------------------------------------------ shared builders for both cottages
def ground_top(x0, x1, y0, y1):
    """The highest ground under a rectangle (read on a grid of 5 x 5 points) and the lowest."""
    hs = [pk.ground_height_at(x, y) for x in np.linspace(x0, x1, 5) for y in np.linspace(y0, y1, 5)]
    return max(hs), min(hs)


def stone_solid(cx, cy, L, Wd, rot, zb, zt, rng, chamfer=(0.05, 0.10)):
    """A rubble stone: four rings of a chamfered rectangle (bulging a little in the middle, jittered), flat on top at height zt so a sill can lie on it."""
    hx, hy = L / 2, Wd / 2
    c = rng.uniform(*chamfer)
    base = np.array([(hx, -hy + c), (hx, hy - c), (hx - c, hy), (-hx + c, hy), (-hx, hy - c), (-hx, -hy + c), (-hx + c, -hy), (hx - c, -hy)])
    zs = [zb, zb + 0.30 * (zt - zb), zb + 0.72 * (zt - zb), zt]
    scales = [0.90, 1.03, 1.00, 0.95]
    rings = []
    for z, s in zip(zs, scales):
        pts = base * s + rng.uniform(-0.012, 0.012, size=base.shape)
        ring = np.c_[pts[:, 0] + cx, pts[:, 1] + cy, np.full(8, z)]
        rings.append(rot_z(ring, rot, (cx, cy)))
    return loft(rings)


def stone_colour(base, g, factor, moss=0.0):
    moss_c = hexl('#5E7040')

    def fn(V):
        c = shade(np.tile(base, (len(V), 1)), factor)
        low = smoothstep(g + 0.16, g - 0.02, V[:, 2]) * (0.22 + moss)
        return mixc(c, moss_c, low)
    return fn


def bar_solid(wall, u0, u1, wc, hwid, z0, z1, bow=0.003, taper=1.0, stations=3, twist=0.0):
    """A straight timber lying along a wall (u from u0 to u1) with a flat top and bottom (z0, z1), a slight bow in plan, centred across at wc with half width hwid."""
    rings = []
    for k in range(stations):
        t = k / (stations - 1)
        u = u0 + (u1 - u0) * t
        cw = wc + bow * math.sin(math.pi * t)
        h = hwid * (1.0 + (taper - 1.0) * t)
        rings.append(np.array([wall.P(u, cw - h, z0), wall.P(u, cw + h, z0), wall.P(u, cw + h, z1), wall.P(u, cw - h, z1)]))
    return loft(rings)


def oak(rng, base, spread=0.16):
    return shade(base, rng.uniform(1 - spread, 1 + spread * 0.7))


def daub_panel(wall, uL, uR, z0, z1, rng, noise, colours, chip=None, wf0=0.050, wb=-0.050, cell=0.11):
    """A daub panel between two studs, as ONE closed solid: a flat back (w = wb) and a front surface (w about wf0) with soft lumps, a recess at the borders, and, where `chip` says
    (u centre, z centre, u radius, z radius), a ragged chip where the render has fallen off and only the core is left. uL and uR are functions of z (the stud faces, pushed 1.5 cm
    into the studs); z1 may be a number or a function of u. Returns (V, F, colour array, chip mask of the front vertices)."""
    zmid = z0 + 0.5 * ((z1(0.5 * (uL(z0) + uR(z0))) if callable(z1) else z1) - z0)
    width = float(uR(zmid) - uL(zmid))
    top_mid = z1(0.5 * (uL(zmid) + uR(zmid))) if callable(z1) else z1
    nu = max(2, int(round(width / cell)))
    nz = max(2, int(round((top_mid - z0) / (cell * 1.2))))
    Fg = np.zeros((nu + 1, nz + 1, 3))
    Bg = np.zeros((nu + 1, nz + 1, 3))
    col_f = np.zeros((nu + 1, nz + 1, 4))
    mask = np.zeros((nu + 1, nz + 1))
    uLn, uRn = uL(zmid), uR(zmid)
    for j in range(nz + 1):
        tj = j / nz
        for i in range(nu + 1):
            si = i / nu
            un = uLn + si * (uRn - uLn)
            top = z1(un) if callable(z1) else z1
            z = z0 + tj * (top - z0)
            u = uL(z) + si * (uR(z) - uL(z))
            edge = min(si * width, (1 - si) * width, (z - z0), (top - z)) if (top - z0) > 0.0 else 0.0
            wf = wf0 + 0.007 * noise.value(u * 2.1, z * 2.1, 0.3) - 0.014 * (1 - smoothstep(0.0, 0.07, edge))
            if chip is not None:
                uc, zc, ru, rz = chip
                r = math.hypot((u - uc) / ru, (z - zc) / rz) * (1 + 0.28 * noise.value(u * 5.3, z * 5.3, 1.7))
                m = float(smoothstep(1.0, 0.72, r))
                mask[i, j] = m
                wf = wf * (1 - m) + (0.004 + 0.006 * noise.value(u * 7, z * 7, 2.2)) * m
            Fg[i, j] = wall.P(u, wf, z)
            Bg[i, j] = wall.P(u, wb, z)
    return Fg, Bg, mask


def lean_for(rng, scale, big=False):
    mag = (rng.uniform(0.010, 0.019) if big else rng.uniform(0.002, 0.010)) * scale
    ang = rng.uniform(0, 2 * math.pi)
    return (mag * math.cos(ang), mag * math.sin(ang))


def plank_leaf(wall, u0, u1, wback, thick, z0, z1, widths, rng, base, fresh, replaced, bow=0.004, ledges=(), ledge_thick=0.022, groove=0.010):
    """A plank leaf (door or shutter) as ONE closed solid: vertical planks of the given widths with a groove between them, a bow, and ledges on the back (z ranges relative to z0).
    replaced: plank numbers in a fresher colour. Returns (V, F, colours)."""
    n = len(widths)
    ws = np.array(widths, float)
    ws = ws / ws.sum() * (u1 - u0)
    edges = u0 + np.concatenate([[0.0], np.cumsum(ws)])
    wf = [wback + thick + rng.uniform(-0.002, 0.002) + (0.003 if k in replaced else 0.0) for k in range(n)]
    plank_col = []
    for k in range(n):
        c = fresh if k in replaced else base
        plank_col.append(shade(c, rng.uniform(0.86, 1.1)))
    # the profile loop: back left, back right, then the front from right to left
    prof, pcol = [], []
    back_col = shade(base, 0.8)
    prof.append((edges[0], 0.0, -1))
    prof.append((edges[-1], 0.0, -1))
    for k in range(n - 1, -1, -1):
        prof.append((edges[k + 1] - 0.004, wf[k] - wback, k))
        prof.append((edges[k] + 0.004, wf[k] - wback, k))
        if k > 0:
            prof.append((edges[k], min(wf[k], wf[k - 1]) - wback - groove, k))
    levels = [(0.0, 0.0)]
    for a, b in ledges:
        levels += [(a, 0.0), (a, ledge_thick), (b, ledge_thick), (b, 0.0)]
    levels.append((z1 - z0, 0.0))
    rings, cols = [], []
    for zrel, led in levels:
        t = zrel / (z1 - z0)
        shift = bow * math.sin(math.pi * t)
        pts = []
        for (u, w, k) in prof:
            w_here = wback + w + shift - (led if k == -1 else 0.0)
            pts.append(wall.P(u, w_here, z0 + zrel))
        rings.append(np.array(pts))
        cols.append(np.array([back_col if k == -1 else plank_col[k] for (_, _, k) in prof]))
    V, F = loft(rings)
    return V, F, np.vstack(cols)


def hinge_set(acc, wall, u_hinge, direction, wf_top, z_list, length, thick=0.012, pin_in=0.022, wback=0.0, col=None):
    """Iron hinges: for each height a strap lying on the front of the leaf (from the hinge edge `length` along `direction`) and a pintle block straddling the gap between the leaf edge and the post."""
    for z in z_list:
        strap = wbox(wall, min(u_hinge, u_hinge + direction * length), max(u_hinge, u_hinge + direction * length), wf_top, wf_top + thick - 0.001, z - 0.022, z + 0.022)
        acc.add(*strap, col=col)
        pa, pb = u_hinge - direction * 0.035, u_hinge + direction * 0.012
        pin = wbox(wall, min(pa, pb), max(pa, pb), wback, wf_top + thick + 0.003, z - 0.03, z + 0.03)
        acc.add(*pin, col=col)
