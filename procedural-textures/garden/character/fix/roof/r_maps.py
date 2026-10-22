"""Height pictures and normal maps of the roof builder (22 October). numpy only.
Plain words: draws soft, large-scale relief pictures (tile glaze, plaster, stone, moss pillows) as numpy arrays, and turns them into
tangent-space normal maps with normal_tools.height_to_normal (OpenGL, green = up the picture). Everything tiles (periodic)."""
import os
import sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import normal_tools   # noqa: E402


def blur(a, sigma):
    """periodic gaussian blur by FFT (sigma in pixels)"""
    h, w = a.shape[:2]
    fy = np.fft.fftfreq(h)[:, None]
    fx = np.fft.fftfreq(w)[None, :]
    g = np.exp(-2.0 * (np.pi * sigma) ** 2 * (fx ** 2 + fy ** 2))
    if a.ndim == 3:
        return np.stack([np.fft.ifft2(np.fft.fft2(a[..., c]) * g).real for c in range(a.shape[2])], axis=-1).astype(np.float32)
    return np.fft.ifft2(np.fft.fft2(a) * g).real.astype(np.float32)


def noise(h, w, sigma, rng):
    n = blur(rng.standard_normal((h, w)).astype(np.float32), sigma)
    return n / (n.std() + 1e-9)


def mean_slope(hmap, n_strength_unit=1.0):
    """mean slope magnitude at strength 1 as normal_tools computes it (height_to_normal: k = strength * w / 8)"""
    dx = (np.roll(hmap, -1, axis=1) - np.roll(hmap, 1, axis=1)) * 0.5
    dy = (np.roll(hmap, -1, axis=0) - np.roll(hmap, 1, axis=0)) * 0.5
    k = hmap.shape[1] / 8.0
    return float(np.sqrt(dx * dx + dy * dy).mean() * k)


def to_normal(hmap, target_slope):
    """strength chosen so the mean slope (tan of tilt) is target_slope (0.1 = 6 degrees: soft, painterly)"""
    s = target_slope / max(mean_slope(hmap), 1e-9)
    return normal_tools.height_to_normal(hmap, strength=s, tile=True), s


def _stroke(h, pts, width_px, amp):
    """add a soft line (gaussian cross-section) through pts [(row, col) ...] (periodic wrap ignored)"""
    H, W = h.shape
    for (r0, c0), (r1, c1) in zip(pts[:-1], pts[1:]):
        n = int(max(abs(r1 - r0), abs(c1 - c0)) + 1)
        rr = np.linspace(r0, r1, n)
        cc = np.linspace(c0, c1, n)
        r_lo = int(max(min(rr.min(), rr.max()) - 4 * width_px, 0))
        r_hi = int(min(max(rr) + 4 * width_px + 1, H))
        c_lo = int(max(min(cc) - 4 * width_px, 0))
        c_hi = int(min(max(cc) + 4 * width_px + 1, W))
        if r_hi <= r_lo or c_hi <= c_lo:
            continue
        yy, xx = np.mgrid[r_lo:r_hi, c_lo:c_hi].astype(np.float32)
        d2 = np.full(yy.shape, 1e9, np.float32)
        for r, c in zip(rr[::max(1, int(width_px // 2))], cc[::max(1, int(width_px // 2))]):
            d2 = np.minimum(d2, (yy - r) ** 2 + (xx - c) ** 2)
        h[r_lo:r_hi, c_lo:c_hi] += amp * np.exp(-d2 / (2 * width_px ** 2))


# --------------------------------------------------------------------------------- the four tiling normal maps
def glaze_height(n=1024, seed=11):
    """Roof tile glaze (FIX ROUND: calmer). Soft undulation (6 to 10 cm), THREE faint wide crazing arcs, four shallow soft dents.
    The first version had 14 craze lines and 8 dents per tile, which read as a crumpled sheet at 100 percent. 1 px = 0.65 mm."""
    rng = np.random.default_rng(seed)
    h = 0.55 * noise(n, n, 90, rng) + 0.16 * noise(n, n, 34, rng)
    for _ in range(3):
        r, c = rng.uniform(0, n, 2)
        ang = rng.uniform(0, np.pi)
        pts = [(r, c)]
        for _k in range(int(rng.integers(3, 5))):
            ang += rng.uniform(-0.45, 0.45)
            L = rng.uniform(60, 110)
            r, c = r + np.sin(ang) * L, c + np.cos(ang) * L
            pts.append((r, c))
        _stroke(h, pts, 6.5, -0.28)
    for _ in range(4):
        r, c = rng.uniform(60, n - 60, 2)
        rad = rng.uniform(26, 44)
        yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
        d2 = (yy - r) ** 2 + (xx - c) ** 2
        h -= 0.45 * np.exp(-d2 / (2 * (rad * 0.6) ** 2))
    h = blur(h, 4.0)
    return h


def plaster_height(n=2048, seed=21):
    """Plaster: soft trowel blotches 20 to 60 cm plus 6 to 12 cm undulation, nothing finer than 1.5 cm. 1 px = 1.2 mm (tile 2.5 m)."""
    rng = np.random.default_rng(seed)
    h = 0.9 * noise(n, n, 150, rng) + 0.5 * noise(n, n, 55, rng) + 0.22 * noise(n, n, 20, rng)
    return h


def stone_height(n=1024, seed=31):
    """Stone: the scan's rock_08_disp_1k.jpg, blurred 3 px so only big planes and shallow pits are left (tile 1 m)."""
    path = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/surfaces/maps/rock_08_disp_1k.jpg'
    try:
        import bpy
        img = bpy.data.images.load(path, check_existing=False)
        img.colorspace_settings.name = 'Non-Color'
        w, h_ = img.size
        px = np.empty(w * h_ * 4, np.float32)
        img.pixels.foreach_get(px)
        bpy.data.images.remove(img)
        a = px.reshape(h_, w, 4)[::-1, :, :3].mean(axis=2)
        if a.shape[0] != n:
            idx = (np.arange(n) * a.shape[0] / n).astype(int)
            a = a[idx][:, idx]
        a = (a - a.mean()) / (a.std() + 1e-9)
        # one blur of 3 px (soft), plus a slow undulation so no tile edge reads as a seam
        rng = np.random.default_rng(seed)
        return blur(a, 3.0) + 0.5 * noise(n, n, 60, rng)
    except Exception as e:      # fallback keeps the stage alive when the scan is missing
        print('[roof] stone_height fallback:', e)
        rng = np.random.default_rng(seed)
        return noise(n, n, 5, rng) + 0.6 * noise(n, n, 40, rng)


def moss_height(n=1024, seed=41, cells=7):
    """Moss cap pillows: soft rounded cells (tile 0.6 m, 7 cells across = 8.5 cm), low contrast so the cap reads as one soft shape, not scales, each a soft dome, valleys between."""
    rng = np.random.default_rng(seed)
    gx, gy = np.meshgrid(np.arange(cells), np.arange(cells))
    jit = rng.uniform(0.15, 0.85, (cells, cells, 2)).astype(np.float32)
    px = (np.arange(n) + 0.5) / n * cells
    X, Y = np.meshgrid(px, px)
    f1 = np.full((n, n), 9.0, np.float32)
    f2 = np.full((n, n), 9.0, np.float32)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            cx = (np.floor(X).astype(int) + dx)
            cy = (np.floor(Y).astype(int) + dy)
            jx = jit[cy % cells, cx % cells, 0]
            jy = jit[cy % cells, cx % cells, 1]
            d = np.sqrt((X - (cx + jx)) ** 2 + (Y - (cy + jy)) ** 2)
            new_f2 = np.where(d < f1, f1, np.minimum(f2, d))
            f1 = np.minimum(f1, d)
            f2 = new_f2
    edge = np.clip((f2 - f1) / 0.55, 0, 1)
    dome = (1 - np.clip(f1 / 0.8, 0, 1) ** 2)
    h = (0.55 * dome + 0.30 * edge ** 0.7).astype(np.float32)
    h += 0.25 * noise(n, n, 60, rng)
    return blur(h, 6.0)


def plaster_blotch(sw_path, n=1024):
    """Colour factor from sw_plaster.jpg (it tiles): soft large blotches only. Cracks and the four brown loss patches are painted out
    (they would repeat every 2.5 m), then the picture is blurred and divided by its mean. Returns (n, n, 3) around 1.0."""
    import bpy
    img = bpy.data.images.load(sw_path, check_existing=False)
    img.colorspace_settings.name = 'sRGB'
    w, h_ = img.size
    px = np.empty(w * h_ * 4, np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    a = px.reshape(h_, w, 4)[::-1, :, :3]              # linear light values
    step = max(1, a.shape[0] // 512)
    a = a[::step, ::step]                               # 512 px
    lum = a.mean(axis=2)
    brown = ((a[..., 0] - a[..., 2]) > 0.55 * lum.mean()) & (lum < np.percentile(lum, 55))
    brown = blur(brown.astype(np.float32), 3.0) > 0.12
    wgt = (~brown).astype(np.float32)
    num = blur(a * wgt[..., None], 8.0)
    den = blur(wgt, 8.0)[..., None] + 1e-4
    filled = np.where(brown[..., None], num / den, a)
    soft = blur(filled, 3.0)
    soft = soft / soft.mean(axis=(0, 1), keepdims=True)
    if n != soft.shape[0]:
        idx = (np.arange(n) * soft.shape[0] / n).astype(int)
        soft = soft[idx][:, idx]
    return np.clip(soft, 0.2, 2.5).astype(np.float32)


def all_normals(sizes=None, seed_shift=0):
    sizes = sizes or {}
    out = {}
    out['glaze'] = to_normal(glaze_height(sizes.get('glaze', 1024), 11 + seed_shift), 0.065)
    out['plaster'] = to_normal(plaster_height(sizes.get('plaster', 2048), 21 + seed_shift), 0.045)
    out['stone'] = to_normal(stone_height(sizes.get('stone', 1024), 31 + seed_shift), 0.11)
    out['moss'] = to_normal(moss_height(sizes.get('moss', 1024), 41 + seed_shift), 0.28)
    return out
