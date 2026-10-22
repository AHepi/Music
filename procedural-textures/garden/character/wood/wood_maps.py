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


def plank_top_height(W=2048, H=512, seed=3, tile=(1.0, 0.25)):
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
