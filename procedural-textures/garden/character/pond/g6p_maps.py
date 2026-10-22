# POND BUILDER: makes the five normal maps (swell, ripple spots, pebbles, maple bark, pine bark) as PNG files in maps/.
# Plain words: the garden had no normal maps. These are soft, large-scale relief pictures (OpenGL convention: green = up the picture = +V),
# turned from height pictures with the same sign convention as normal_tools.height_to_normal (checked by test_pond.py with the test light).
# Run (anywhere, numpy only, a few seconds):  blender -b --factory-startup --python g6p_maps.py -- [outdir]
import bpy
import sys
import os
import math
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import normal_tools as nt      # noqa: E402

SCANS = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/surfaces/maps'
POND_BBOX = (-5.65, -1.25, 0.20, 3.10)
# ripple spots: (x, y, rings, spacing_m, story). One story per spot (the stage puts a lily stem, a falling leaf or nothing at each).
RIPPLE_SPOTS = [
    (-3.55, 1.72, 6, 0.080, 'lily stems'),
    (-2.55, 2.45, 4, 0.060, 'falling leaf'),
    (-2.35, -0.30, 7, 0.090, 'open water'),
    (-1.15, 1.75, 5, 0.070, 'lily pad'),
]


def gauss_blur(h, sigma):
    """Periodic gaussian blur by FFT (keeps tiling maps seamless)."""
    if sigma <= 0:
        return h
    H, W = h.shape
    fy = np.fft.fftfreq(H)[:, None]
    fx = np.fft.fftfreq(W)[None, :]
    g = np.exp(-2 * (math.pi ** 2) * (sigma ** 2) * (fx ** 2 + fy ** 2))
    return np.real(np.fft.ifft2(np.fft.fft2(h) * g)).astype(np.float32)


def stretch01(h, lo=2, hi=98):
    a, b = np.percentile(h, lo), np.percentile(h, hi)
    return np.clip((h - a) / max(b - a, 1e-6), 0, 1).astype(np.float32)


def normals_from_height_m(h_m, px_x, px_y, tile=True):
    """h_m: height in metres (rows from the TOP of the picture), px_x/px_y: metres per pixel. Same convention as normal_tools.height_to_normal."""
    if tile:
        dx = (np.roll(h_m, -1, axis=1) - np.roll(h_m, 1, axis=1)) * 0.5 / px_x
        dr = (np.roll(h_m, -1, axis=0) - np.roll(h_m, 1, axis=0)) * 0.5 / px_y
    else:
        dx = np.gradient(h_m, axis=1) / px_x
        dr = np.gradient(h_m, axis=0) / px_y
    nx, ny, nz = -dx, +dr, np.ones_like(dx)
    ln = np.sqrt(nx * nx + ny * ny + nz * nz)
    return np.stack([nx / ln, ny / ln, nz / ln], axis=-1).astype(np.float32)


def swell_height(N=2048, tile_m=3.0, seed=11):
    """A soft broad swell: ~16 waves with whole numbers of wavelengths across the 3 m tile (so it tiles), wavelengths 0.5 to 3 m."""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float64) / N
    h = np.zeros((N, N))
    comps = []
    for _ in range(16):
        kx, ky = int(rng.integers(-4, 5)), int(rng.integers(0, 5))
        if kx == 0 and ky == 0:
            continue
        k = math.hypot(kx, ky)
        amp = 1.0 / (k ** 1.1)
        ph = rng.uniform(0, math.tau)
        h += amp * np.sin(math.tau * (kx * xx + ky * yy) + ph)
        comps.append((kx, ky, amp))
    # scale so that the RMS slope is 0.035 (2 degrees): slope = dh/dx_m
    px = tile_m / N
    gx = (np.roll(h, -1, axis=1) - np.roll(h, 1, axis=1)) * 0.5 / px
    gy = (np.roll(h, -1, axis=0) - np.roll(h, 1, axis=0)) * 0.5 / px
    rms = math.sqrt(float((gx ** 2 + gy ** 2).mean()))
    h_m = h * (0.012 / rms)
    return h_m.astype(np.float32), px


def ripple_height(N=2048, bbox=POND_BBOX, spots=RIPPLE_SPOTS, crest_slope=0.085):
    """Concentric ring patterns (4 to 7 rings, 6 to 9 cm apart, Gaussian fade) at the spots, in metres; everything else flat."""
    x0, y0, x1, y1 = bbox
    W_m, H_m = x1 - x0, y1 - y0
    px_x, px_y = W_m / N, H_m / N
    cols = x0 + (np.arange(N) + 0.5) * px_x
    rows = y1 - (np.arange(N) + 0.5) * px_y                # row 0 is the top = largest y (+V up)
    X, Y = np.meshgrid(cols, rows)
    h = np.zeros((N, N))
    for (cx, cy, nrings, lam, story) in spots:
        r = np.hypot(X - cx, Y - cy)
        R = nrings * lam
        env = np.exp(-(r / (0.62 * R)) ** 2) * (r < 1.25 * R)
        env *= np.clip(r / (0.9 * lam), 0, 1) ** 2         # soft start in the middle so the first ring is round and clean
        amp = crest_slope * lam / math.tau
        h += amp * np.sin(math.tau * r / lam - 0.9) * env
    return h.astype(np.float32), px_x, px_y


def strength_for_rms_slope(h, target):
    """normal_tools.height_to_normal strength that gives a root-mean-square slope of `target` (0.3 = about 17 degrees) for a 0..1 height picture."""
    dx = (np.roll(h, -1, axis=1) - np.roll(h, 1, axis=1)) * 0.5
    dy = (np.roll(h, -1, axis=0) - np.roll(h, 1, axis=0)) * 0.5
    rms = math.sqrt(float((dx ** 2 + dy ** 2).mean()))
    return target / (rms * h.shape[1] / 8.0)


def load_scan(name):
    img = bpy.data.images.load(os.path.join(SCANS, name))
    img.colorspace_settings.name = 'Non-Color'
    w, h = img.size
    a = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)[..., :3].mean(axis=2)
    a = a[::-1]                                           # rows from the top
    bpy.data.images.remove(img)
    return a


def save(name, n, outdir):
    path = os.path.join(outdir, name)
    nt.save_normal_png(path, n)
    return path


def stats(n):
    rgb = nt.to_rgb(n)
    return rgb[..., 0].mean(), rgb[..., 1].mean(), rgb[..., 2].mean()


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    outdir = argv[0] if argv else os.path.join(HERE, 'maps')
    os.makedirs(outdir, exist_ok=True)
    out = {}
    # 1 swell 2048 (tile 3 m)
    h, px = swell_height(2048)
    n = normals_from_height_m(h, px, px, tile=True)
    out['swell_normal.png'] = (save('swell_normal.png', n, outdir), stats(n))
    # 2 ripples 2048 over the pond box
    h, pxx, pxy = ripple_height(2048)
    n = normals_from_height_m(h, pxx, pxy, tile=False)
    out['ripple_normal.png'] = (save('ripple_normal.png', n, outdir), stats(n))
    # 3 pebbles 1024 from the blurred clean_pebbles_disp scan (soft lumps ~2 cm at 1 unit = 1 m)
    s = load_scan('clean_pebbles_disp_1k.jpg')
    hp = stretch01(gauss_blur(s, 5.0))
    n = nt.height_to_normal(hp, strength=strength_for_rms_slope(hp, 0.26), tile=True)
    out['pebble_normal.png'] = (save('pebble_normal.png', n, outdir), stats(n))
    # 4 maple bark 1024 (plated ridges, soft)
    s = load_scan('trident_maple_bark_disp_1k.jpg')
    hb = stretch01(gauss_blur(s, 2.2))
    n = nt.height_to_normal(hb, strength=strength_for_rms_slope(hb, 0.30), tile=True)
    out['maple_bark_normal.png'] = (save('maple_bark_normal.png', n, outdir), stats(n))
    # 5 pine bark 1024 (chunky plates)
    s = load_scan('pine_bark_disp_1k.jpg')
    hq = stretch01(gauss_blur(s, 2.6))
    n = nt.height_to_normal(hq, strength=strength_for_rms_slope(hq, 0.30), tile=True)
    out['pine_bark_normal.png'] = (save('pine_bark_normal.png', n, outdir), stats(n))
    for k, (p, st) in out.items():
        print('MAP', k, 'mean rgb %.3f %.3f %.3f' % st, 'bytes', os.path.getsize(p))


if __name__ == '__main__':
    main()
