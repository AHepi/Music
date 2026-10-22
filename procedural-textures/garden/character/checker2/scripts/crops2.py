import bpy, json, sys, os
import numpy as np
G = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/'
OUT = G + 'character/checker2/out/crops/'
os.makedirs(OUT, exist_ok=True)
def load(path):
    img = bpy.data.images.load(path); img.colorspace_settings.name = 'Non-Color'
    w, h = img.size; a = np.empty(w * h * 4, np.float32); img.pixels.foreach_get(a)
    bpy.data.images.remove(img)
    return a.reshape(h, w, 4)[::-1, :, :3].copy()
def save_jpg(arr, path, q=82):
    h, w = arr.shape[:2]
    img = bpy.data.images.new('t', w, h, alpha=False); img.colorspace_settings.name = 'Non-Color'
    img.pixels.foreach_set(np.concatenate([arr[::-1], np.ones((h, w, 1), np.float32)], axis=2).ravel())
    img.file_format = 'JPEG'; bpy.context.scene.render.image_settings.quality = q
    img.filepath_raw = path; img.save(); bpy.data.images.remove(img)
def gblur(a, sigma):
    r = int(3 * sigma + 1); x = np.arange(-r, r + 1); k = np.exp(-x * x / (2 * sigma * sigma)); k /= k.sum()
    p = np.pad(a, ((r, r), (0, 0)), mode='reflect'); a = sum(k[i] * p[i:i + a.shape[0]] for i in range(2 * r + 1))
    p = np.pad(a, ((0, 0), (r, r)), mode='reflect'); return sum(k[i] * p[:, i:i + a.shape[1]] for i in range(2 * r + 1))
lum = lambda a: 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
NEW = {'hero': G + 'character/final/out/finals/final_hero.png', 'veranda': G + 'character/final/out/finals/final_veranda.png'}
OLD = {'hero': G + 'fix/out/final/real_hero.png', 'veranda': G + 'fix/out/final/real_veranda.png'}
cache = {}
def get(d, k):
    key = d[k]
    if key not in cache: cache[key] = load(key)
    return cache[key]
C = [('bridge_west_arm', 'hero', 0, 1080, 800, 1600), ('bridge_middle', 'hero', 700, 1000, 1500, 1450), ('roof_tiles', 'hero', 700, 300, 1450, 620), ('pond_rocks', 'hero', 250, 850, 1100, 1250),
     ('lawn_lower_right', 'hero', 1500, 1250, 2400, 1600), ('maple_hero', 'hero', 0, 150, 900, 800), ('pine_wall', 'hero', 1550, 250, 2400, 900),
     ('deck_foreground', 'veranda', 1500, 800, 2400, 1600), ('far_bridge_pond', 'veranda', 600, 550, 1500, 1050), ('lantern_veranda', 'veranda', 250, 300, 950, 1200), ('maple_veranda', 'veranda', 1250, 80, 2250, 700)]
for name, pic, x0, y0, x1, y1 in C:
    n = get(NEW, pic)[y0:y1, x0:x1]; o = get(OLD, pic)[y0:y1, x0:x1]
    sep = np.ones((n.shape[0], 8, 3), np.float32)
    save_jpg(np.concatenate([o, sep, n], axis=1), OUT + 'ba_%s.jpg' % name)
# metrics (own formulas)
BOXES = {"roof": (700, 300, 1500, 500), "bridge": (0, 1250, 900, 1500), "grass": (1500, 1350, 2400, 1600), "maple": (100, 300, 800, 700), "sand": (1700, 900, 2300, 1300), "wall": (1500, 580, 2300, 800), "rock": (200, 840, 420, 1050), "sky": (900, 0, 1500, 150), "hills": (1700, 100, 2400, 260)}
M = {}
for pic in ('hero', 'veranda'):
    for tag, d in (('old', OLD), ('new', NEW)):
        a = get(d, pic); L = lum(a); l8 = np.round(L * 255); hf = np.abs(l8 - gblur(l8, 2.0))
        mx, mn = a.max(-1), a.min(-1); sat = (mx - mn) / np.maximum(mx, 1e-4)
        m = {'pct': {str(p): round(float(np.percentile(L, p)), 3) for p in (1, 5, 25, 50, 75, 95, 99)}, 'sat_mean': round(float(sat.mean()), 3), 'sat_gt_0.70_share': round(float((sat > 0.70).mean()), 4)}
        m['energy'] = {k: round(float(hf[y0:y1, x0:x1].mean()), 2) for k, (x0, y0, x1, y1) in BOXES.items()}
        H, W = L.shape; y_start = int(0.38 * H); n = f = f2 = 0
        for y in range(y_start, H - 96 + 1, 48):
            for x in range(0, W - 96 + 1, 48):
                s = float(L[y:y + 96, x:x + 96].std()); n += 1; f += s < 0.010; f2 += s < 0.014
        m['flat_windows_lt_0.010_and_lt_0.014_of_n'] = [f, f2, n]
        M[pic + '_' + tag] = m
    A, B = gblur(lum(get(OLD, pic)), 12.0), gblur(lum(get(NEW, pic)), 12.0)
    # SSIM-like on blurred luminance (global means, variances, covariance) and windowed version 
    def ssim(a, b, win=24):
        c1, c2 = 0.01 ** 2, 0.03 ** 2
        mu_a, mu_b = gblur(a, win / 3), gblur(b, win / 3)
        va = gblur(a * a, win / 3) - mu_a ** 2; vb = gblur(b * b, win / 3) - mu_b ** 2; cab = gblur(a * b, win / 3) - mu_a * mu_b
        s = ((2 * mu_a * mu_b + c1) * (2 * cab + c2)) / ((mu_a ** 2 + mu_b ** 2 + c1) * (va + vb + c2))
        return float(s.mean())
    M[pic + '_ssim_blur12_windowed'] = round(ssim(A, B), 4)
    M[pic + '_blur12_corr'] = round(float(np.corrcoef(A.ravel(), B.ravel())[0, 1]), 4)
    h, w = A.shape; g = np.abs(A - B)
    M[pic + '_diff_grid_8x6'] = [[round(float(g[int(r * h / 6):int((r + 1) * h / 6), int(c * w / 8):int((c + 1) * w / 8)].mean()), 3) for c in range(8)] for r in range(6)]
json.dump(M, open(OUT + 'metrics2.json', 'w'), indent=1)
print('CROPS2 DONE')
