"""wood_maps.py - height pictures (numpy) for the wood builder's normal maps. White = high. Rows from the TOP of the picture = +V.
All pictures are soft and large-scale (clean grooves, round knots, a few thin checks), never pores or scan noise (style note section 0).
Seamless: grooves use periodic functions; noise is made in Fourier space so it wraps.
"""
import numpy as np
import math


def _rng(seed):
    return np.random.default_rng(seed)


def periodic_noise(h, w, seed, cutoff=6.0, power=2.0):
    """Smooth periodic noise in [-1, 1]; cutoff = number of cycles across the shorter side that are still present."""
    r = _rng(seed)
    f = r.normal(size=(h, w)) + 1j * r.normal(size=(h, w))
    fy = np.fft.fftfreq(h)[:, None] * h
    fx = np.fft.fftfreq(w)[None, :] * w * (h / w)
    k = np.sqrt(fx * fx + fy * fy) / cutoff
    f *= np.exp(-(k ** power))
    f[0, 0] = 0
    a = np.real(np.fft.ifft2(f))
    return a / (np.abs(a).max() + 1e-9)


def _wrapd(a, b, period):
    d = np.abs(a - b)
    return np.minimum(d, period - d)


def calibrate_height(h, p99_tilt_deg=34.0):
    """Scale a height picture so that the steepest 1 percent of its slope tilts the normal by about p99_tilt_deg when converted with
    normal_tools.height_to_normal(h, strength=1.0) (k = W / 8 there)."""
    h = np.asarray(h, np.float32)
    gy, gx = np.gradient(h)
    g = np.sqrt(gx * gx + gy * gy)
    p = float(np.percentile(g, 99.0)) + 1e-9
    k = h.shape[1] / 8.0
    want = math.tan(math.radians(p99_tilt_deg))
    return h * (want / (p * k))


def plank_top_height(W=2048, H=512, seed=3, tile=(1.0, 0.25), knots=False):
    """Grain grooves along u (the long side), 3 soft knots, 2 thin checks, soft board unevenness. Tile = 1.0 m x 0.25 m."""
    r = _rng(seed)
    x = (np.arange(W) + 0.5) / W
    y = (np.arange(H) + 0.5) / H
    X, Y = np.meshgrid(x, y)
    h = np.zeros((H, W), np.float32)
    # --- grain grooves: ~12 wavy lines across 0.25 m, each fades in and out (integer cycles over the tile so it wraps)
    nl = 17
    sig = 0.0014 / tile[1]
    for k in range(nl):
        y0 = (k + r.uniform(0.1, 0.9)) / nl
        amp = r.uniform(0.004, 0.012) / tile[1]
        c1 = int(r.integers(1, 3))
        c2 = int(r.integers(2, 5))
        ph1, ph2 = r.uniform(0, 2 * math.pi, 2)
        yc = y0 + amp * np.sin(2 * math.pi * c1 * X + ph1) + 0.3 * amp * np.sin(2 * math.pi * c2 * X + ph2)
        d = _wrapd(Y, yc, 1.0)
        cn = int(r.integers(1, 4))
        vis = np.clip(0.5 + 0.9 * np.sin(2 * math.pi * cn * X + r.uniform(0, 6.28)), 0, 1) ** 1.4
        dep = r.uniform(0.5, 1.0)
        h -= (dep * vis * np.exp(-(d / sig) ** 2)).astype(np.float32)
    # --- soft raised late-wood ribs between the grooves (wide, gentle)
    for k in range(nl):
        y0 = (k + r.uniform(0.2, 0.8)) / nl
        amp = r.uniform(0.003, 0.01) / tile[1]
        yc = y0 + amp * np.sin(2 * math.pi * int(r.integers(1, 3)) * X + r.uniform(0, 6.28))
        d = _wrapd(Y, yc, 1.0)
        h += (0.32 * np.exp(-(d / (0.011 / tile[1])) ** 2)).astype(np.float32)
    # --- knots: round, with two or three soft rings
    for k in range(2):
        cx, cy = r.uniform(0.1, 0.9), r.uniform(0.2, 0.8)
        R = r.uniform(0.014, 0.03)
        if not knots:        # FIX ROUND: the knots are now separate decals (knot_atlas), one per plank, so the main tile has none
            continue
        dx = _wrapd(X, cx, 1.0) * tile[0]
        dy = _wrapd(Y, cy, 1.0) * tile[1]
        rr = np.sqrt((dx / 1.4) ** 2 + dy ** 2)
        env = np.exp(-(rr / R) ** 2)
        h += (0.9 * env * (0.55 + 0.45 * np.cos(2 * math.pi * rr / (R * 0.55)))).astype(np.float32)
        h -= (0.7 * np.exp(-((rr - R * 1.25) / (R * 0.22)) ** 2)).astype(np.float32)
    # --- two thin checks (long clean grooves) with a ragged start and end
    for k in range(2):
        y0 = r.uniform(0.15, 0.85)
        x0 = r.uniform(0.0, 1.0)
        ln = r.uniform(0.18, 0.42)
        dxs = (X - x0) % 1.0
        along = np.clip(dxs / ln, 0, 1)
        inside = (dxs < ln).astype(np.float32)
        yc = y0 + 0.004 * np.sin(2 * math.pi * 2 * X + r.uniform(0, 6.28))
        d = _wrapd(Y, yc, 1.0) * tile[1]
        wdt = 0.0011 * (1 - 0.6 * along)
        h -= (1.25 * inside * np.exp(-(d / wdt) ** 2) * np.sin(math.pi * np.clip(along, 0.02, 0.98)) ** 0.5).astype(np.float32)
    # --- board unevenness
    h += 0.45 * periodic_noise(H, W, seed + 11, cutoff=3.0)
    h = h - h.mean()
    return h.astype(np.float32)


def plank_cavity(h):
    """0 in the grooves .. 1 on the flat: a colour multiplier picture derived from the height (grooves darker)."""
    hh = np.asarray(h, np.float32)
    c = np.clip(1.0 + hh * 2.2 / (np.abs(hh).max() + 1e-6) * 0.5, 0.0, 1.0)
    c = np.minimum(c, 1.0)
    return c


def end_grain_height(N=1024, seed=5, tile=0.25):
    """Growth rings round an off-centre pith, three thin radial checks, soft relief. Tile 0.25 m."""
    r = _rng(seed)
    x = (np.arange(N) + 0.5) / N
    X, Y = np.meshgrid(x, x)
    cx, cy = 0.47, 0.52
    dx, dy = (X - cx), (Y - cy)
    wob = periodic_noise(N, N, seed + 1, cutoff=3.0) * 0.045
    rr = np.sqrt((dx / 1.0) ** 2 + (dy / 0.78) ** 2) + wob
    h = 0.5 * np.sin(2 * math.pi * rr / 0.052) * np.exp(-(rr / 0.9) ** 2)
    ang = np.arctan2(dy, dx)
    for k in range(3):
        a0 = r.uniform(-math.pi, math.pi)
        da = np.abs(((ang - a0 + math.pi) % (2 * math.pi)) - math.pi)
        len_ = r.uniform(0.18, 0.38)
        h -= 1.2 * np.exp(-(da * rr / 0.0042) ** 2) * (rr < len_) * (rr > 0.02)
    h += 0.35 * periodic_noise(N, N, seed + 2, cutoff=2.5)
    return (h - h.mean()).astype(np.float32)


def post_timber_height(W=1024, H=2048, seed=9, tile=(0.28, 0.56)):
    """Vertical grain (u across 0.28 m, v along 0.56 m): wavy grooves, two long drying checks, one knot, soft bulges."""
    r = _rng(seed)
    x = (np.arange(W) + 0.5) / W
    y = (np.arange(H) + 0.5) / H
    X, Y = np.meshgrid(x, y)
    h = np.zeros((H, W), np.float32)
    nl = 11
    sig = 0.0018 / tile[0]
    for k in range(nl):
        x0 = (k + r.uniform(0.1, 0.9)) / nl
        amp = r.uniform(0.002, 0.007) / tile[0]
        xc = x0 + amp * np.sin(2 * math.pi * int(r.integers(1, 3)) * Y + r.uniform(0, 6.28)) + 0.3 * amp * np.sin(2 * math.pi * int(r.integers(2, 5)) * Y + r.uniform(0, 6.28))
        d = _wrapd(X, xc, 1.0)
        vis = np.clip(0.55 + 0.9 * np.sin(2 * math.pi * int(r.integers(1, 3)) * Y + r.uniform(0, 6.28)), 0, 1) ** 1.3
        h -= (r.uniform(0.5, 1.0) * vis * np.exp(-(d / sig) ** 2)).astype(np.float32)
    for k in range(nl):
        x0 = (k + r.uniform(0.2, 0.8)) / nl
        xc = x0 + 0.004 * np.sin(2 * math.pi * int(r.integers(1, 3)) * Y + r.uniform(0, 6.28))
        h += (0.3 * np.exp(-(_wrapd(X, xc, 1.0) / (0.016 / tile[0] * 0.5)) ** 2)).astype(np.float32)
    # two drying checks: long clean grooves, ragged ends
    for k in range(2):
        x0 = r.uniform(0.2, 0.8)
        y0 = r.uniform(0.0, 1.0)
        ln = r.uniform(0.35, 0.6)
        dys = (Y - y0) % 1.0
        along = np.clip(dys / ln, 0, 1)
        inside = (dys < ln).astype(np.float32)
        xc = x0 + 0.003 * np.sin(2 * math.pi * 3 * Y + r.uniform(0, 6.28))
        d = _wrapd(X, xc, 1.0) * tile[0]
        h -= (1.4 * inside * np.exp(-(d / (0.0016 * (1 - 0.5 * along))) ** 2) * np.sin(math.pi * np.clip(along, 0.02, 0.98)) ** 0.4).astype(np.float32)
    cx, cy = r.uniform(0.3, 0.7), r.uniform(0.3, 0.7)
    dx = _wrapd(X, cx, 1.0) * tile[0]
    dy = _wrapd(Y, cy, 1.0) * tile[1]
    rr = np.sqrt(dx ** 2 + (dy / 1.5) ** 2)
    R = 0.018
    h += (0.9 * np.exp(-(rr / R) ** 2) * (0.55 + 0.45 * np.cos(2 * math.pi * rr / (R * 0.55)))).astype(np.float32)
    h += 0.4 * periodic_noise(H, W, seed + 5, cutoff=3.0)
    return (h - h.mean()).astype(np.float32)


def stone_height_from(disp, blur_px=4):
    """Soft stone relief from a scan height picture (2D array 0..1): blurred (soft, large relief only), tile-safe (wrap)."""
    d = np.asarray(disp, np.float32)
    if d.ndim == 3:
        d = d[..., :3].mean(axis=2)
    d = d - d.mean()
    F = np.fft.fft2(d)
    H_, W_ = d.shape
    fy = np.fft.fftfreq(H_)[:, None]
    fx = np.fft.fftfreq(W_)[None, :]
    g = np.exp(-(fx ** 2 + fy ** 2) * (2 * math.pi ** 2) * (blur_px ** 2))
    out = np.real(np.fft.ifft2(F * g))
    return out.astype(np.float32)


def soft_stone_height(N=1024, seed=21):
    """Procedural fallback: big rounded facets with a few clean cracks."""
    r = _rng(seed)
    h = 1.0 * periodic_noise(N, N, seed, cutoff=3.5) + 0.5 * periodic_noise(N, N, seed + 1, cutoff=7.0)
    x = (np.arange(N) + 0.5) / N
    X, Y = np.meshgrid(x, x)
    for k in range(2):
        a = r.uniform(0, math.pi)
        c = r.uniform(0.2, 0.8)
        d = np.abs((X - 0.5) * math.sin(a) - (Y - 0.5) * math.cos(a) - (c - 0.5)) * 1.0
        h -= 0.5 * np.exp(-(d / 0.004) ** 2) * (periodic_noise(N, N, seed + 7 + k, cutoff=6.0) > -0.1)
    return h.astype(np.float32)


def _smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def knot_atlas(N=1024, seed=31):
    """FIX ROUND (wood): a 2 x 2 atlas of four clean, designed knots, one per cell (cell = N/2 px). Each knot is an oval boss along the grain (u) with
    a small dark pit, two or three soft rings and two grain lines that bend round it. The borders of every cell are flat, so the shader can place one
    knot per plank at any size and position. Returns (height, darkness); both N x N, row 0 = top (+V)."""
    r = _rng(seed)
    cell = N // 2
    ys, xs = (np.mgrid[0:cell, 0:cell] + 0.5) / cell - 0.5          # q in -0.5..0.5, xs along u, ys down the picture
    ys = -ys                                                          # +V up
    H = np.zeros((N, N), np.float32)
    D = np.zeros((N, N), np.float32)
    specs = [dict(a=0.30, b=0.17, rings=2, ramp=0.20, tilt=0.0, check=False, pit=0.9),
             dict(a=0.26, b=0.20, rings=1, ramp=0.14, tilt=14.0, check=False, pit=0.7),
             dict(a=0.34, b=0.15, rings=2, ramp=0.18, tilt=-9.0, check=True, pit=1.0),
             dict(a=0.20, b=0.15, rings=0, ramp=0.0, tilt=-4.0, check=False, pit=0.8)]
    for k, sp in enumerate(specs):
        c, sn = math.cos(math.radians(sp['tilt'])), math.sin(math.radians(sp['tilt']))
        x = xs * c + ys * sn
        y = -xs * sn + ys * c
        rr = np.sqrt((x / sp['a']) ** 2 + (y / sp['b']) ** 2)
        win = (1.0 - _smooth(0.34, 0.47, np.maximum(np.abs(xs), np.abs(ys))))
        boss = 0.55 * np.exp(-(rr / 0.95) ** 3)
        pit = -sp['pit'] * np.exp(-(rr / 0.24) ** 2)
        rings = sp['ramp'] * np.cos(2 * math.pi * rr * max(sp['rings'], 1) / 1.0 + 0.6) * _smooth(0.28, 0.45, rr) * (1 - _smooth(0.9, 1.25, rr))
        # two grain lines that bend round the knot (above and below), fading out along the grain
        lines = np.zeros_like(x)
        for sgn in (-1, 1):
            yl = sgn * sp['b'] * (1.38 + 0.18 * np.cos(math.pi * np.clip(x / (sp['a'] * 1.8), -1, 1)))
            lines -= 0.42 * np.exp(-((y - yl) / 0.012) ** 2) * np.exp(-(x / (sp['a'] * 1.55)) ** 2)
        chk = 0.0
        if sp['check']:
            chk = -0.75 * np.exp(-(((y - 0.012 * np.sin(9 * x)) / 0.0085) ** 2)) * (np.abs(x) < sp['a'] * 1.25) * (1 - _smooth(0.5, 1.25, np.abs(x) / sp['a']))
        h = (boss + pit + rings + lines + chk) * win
        d = (0.95 * np.exp(-(rr / 0.30) ** 2) * sp['pit'] + 0.22 * np.exp(-(rr / 0.7) ** 2) + 0.28 * (lines < -0.1) + (0.7 * (chk < -0.2) if sp['check'] else 0.0)) * win
        col, row = k % 2, k // 2
        H[row * cell:(row + 1) * cell, col * cell:(col + 1) * cell] = h
        D[row * cell:(row + 1) * cell, col * cell:(col + 1) * cell] = np.clip(d, 0, 1)
    # a little blur so that no line is thinner than about 3 px
    k = np.exp(-np.arange(-4, 5) ** 2 / (2 * 1.2 ** 2)); k /= k.sum()
    for arr in (H, D):
        for ax in (0, 1):
            arr[:] = np.apply_along_axis(lambda v: np.convolve(v, k, mode='same'), ax, arr)
    return H.astype(np.float32), D.astype(np.float32)


def mirror_extend_normal(rgb):
    """FIX ROUND (wood): a 2 x 2 mirror tile [[A, flip-u(A)], [flip-v(A), both]] of a tangent-space normal picture (values 0..1, rows from the top = +V).
    Mirrored copies get the matching sign flip of the red (u) / green (v) channel, so the lighting stays right and the whole picture still tiles without a seam.
    A plank that takes a random window from this tile shows the grain mirrored and/or turned round, as if the picture were four different boards."""
    A = np.asarray(rgb, np.float32)
    Fu = A[:, ::-1].copy(); Fu[..., 0] = 1.0 - Fu[..., 0]
    Fv = A[::-1, :].copy(); Fv[..., 1] = 1.0 - Fv[..., 1]
    Fuv = A[::-1, ::-1].copy(); Fuv[..., 0] = 1.0 - Fuv[..., 0]; Fuv[..., 1] = 1.0 - Fuv[..., 1]
    return np.concatenate([np.concatenate([A, Fu], axis=1), np.concatenate([Fv, Fuv], axis=1)], axis=0)


def mirror_extend_scalar(a):
    A = np.asarray(a, np.float32)
    return np.concatenate([np.concatenate([A, A[:, ::-1]], axis=1), np.concatenate([A[::-1, :], A[::-1, ::-1]], axis=1)], axis=0)


def save_knot_atlas_16bit(path, N=1024):
    """Writes knot_atlas.png as a 16-bit RGB PNG through Blender: R = knot height (0.5 = flat), G = knot darkness, B = 0.5. 8 bits are too few for a height
    picture used with a Bump node (the knots would show contour rings)."""
    import bpy
    hk, dk = knot_atlas(N)
    hn = 0.5 + 0.5 * hk / (np.abs(hk).max() + 1e-6)
    rgba = np.stack([hn, dk, np.full_like(hn, 0.5), np.ones_like(hn)], axis=-1)[::-1].astype(np.float32)
    img = bpy.data.images.new('_tmp_knots16', N, N, alpha=False, float_buffer=True)
    img.colorspace_settings.name = 'Non-Color'
    img.pixels.foreach_set(rgba.ravel())
    sc = bpy.context.scene
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_mode = 'RGB'
    sc.render.image_settings.color_depth = '16'
    img.save_render(path, scene=sc)
    bpy.data.images.remove(img)
