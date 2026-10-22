"""measure_ground.py - runs on the card inside Blender (pictures stay on the store). Measures the ground builder's guard numbers on full-size pictures.
   blender -b -P measure_ground.py -- JOB.json   JOB = {"out": ".../metrics.json", "items": [{"name": "hero", "png": "...", "base": "<previous final png>", "integrated": "<integrated final png>",
                                                    "cam": "hero"|"veranda"}]}"""
import sys, os, json
import numpy as np
import bpy
job = json.load(open(sys.argv[sys.argv.index('--') + 1]))
BOXES = {"roof": (700, 300, 1500, 500), "bridge": (0, 1250, 900, 1500), "grass fg": (1500, 1350, 2400, 1600), "maple": (100, 300, 800, 700),
         "sand": (1700, 900, 2300, 1300), "wall": (1500, 580, 2300, 800), "rock": (200, 840, 420, 1050)}
VBOX = (0, 1152, 1200, 1600)          # veranda foreground (0..0.5 across, 0.72..1.0 down)
def load_rgb(path):
    img = bpy.data.images.load(path)
    img.colorspace_settings.name = 'Non-Color'
    w, h = img.size
    a = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(a)
    bpy.data.images.remove(img)
    return a.reshape(h, w, 4)[::-1, :, :3].copy()
def gblur(a, sigma):
    r = int(3 * sigma + 1)
    x = np.arange(-r, r + 1)
    k = np.exp(-x * x / (2 * sigma * sigma)); k /= k.sum()
    p = np.pad(a, ((r, r), (0, 0)), mode='reflect')
    a = sum(k[i] * p[i:i + a.shape[0]] for i in range(2 * r + 1))
    p = np.pad(a, ((0, 0), (r, r)), mode='reflect')
    return sum(k[i] * p[:, i:i + a.shape[1]] for i in range(2 * r + 1))
def lum_of(a):
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
def sat_of(a):
    mx, mn = a.max(-1), a.min(-1)
    return (mx - mn) / np.maximum(mx, 1e-4)
def hue_of(rgb):
    import colorsys
    h, s, v = colorsys.rgb_to_hsv(*[float(x) for x in rgb]); return h * 360.0
def ssim_blur(la, lb, sigma_blur=12.0, sigma_win=6.0):
    A, B = gblur(la, sigma_blur), gblur(lb, sigma_blur)
    mu_a, mu_b = gblur(A, sigma_win), gblur(B, sigma_win)
    va = gblur(A * A, sigma_win) - mu_a ** 2; vb = gblur(B * B, sigma_win) - mu_b ** 2; cab = gblur(A * B, sigma_win) - mu_a * mu_b
    c1, c2 = 0.01 ** 2, 0.03 ** 2
    s = ((2 * mu_a * mu_b + c1) * (2 * cab + c2)) / ((mu_a ** 2 + mu_b ** 2 + c1) * (va + vb + c2))
    return s
def measures(a):
    lum = lum_of(a); l8 = np.round(lum * 255); hf = np.abs(l8 - gblur(l8, 2.0)); sat = sat_of(a)
    out = {'pct': [round(float(np.percentile(lum, p)), 4) for p in (1, 5, 25, 50, 75, 95, 99)], 'mean_sat': round(float(sat.mean()), 4)}
    out['energy'] = {k: round(float(hf[y0:y1, x0:x1].mean()), 2) for k, (x0, y0, x1, y1) in BOXES.items()}
    x0, y0, x1, y1 = BOXES['grass fg']
    m = a[y0:y1, x0:x1].reshape(-1, 3); sel = lum[y0:y1, x0:x1].reshape(-1) < 0.55
    out['lawn_box'] = {'lum': round(float(lum[y0:y1, x0:x1].reshape(-1)[sel].mean()), 4), 'hue': round(hue_of(m[sel].mean(0)), 1), 'sat': round(float(sat[y0:y1, x0:x1].mean()), 4),
                       'energy': out['energy']['grass fg']}
    x0, y0, x1, y1 = VBOX
    m = a[y0:y1, x0:x1].reshape(-1, 3); sel = lum[y0:y1, x0:x1].reshape(-1) < 0.55
    out['ver_fg_box'] = {'lum': round(float(lum[y0:y1, x0:x1].reshape(-1)[sel].mean()), 4), 'hue': round(hue_of(m[sel].mean(0)), 1), 'energy': round(float(hf[y0:y1, x0:x1].mean()), 2)}
    return out, lum, sat
res = {}
for it in job['items']:
    a = load_rgb(it['png'])
    m, lum, sat = measures(a)
    H, W = lum.shape
    for key in ('base', 'integrated'):
        if it.get(key) and os.path.exists(it[key]):
            b = load_rgb(it[key])
            mb, lb, sb = measures(b)
            m[key] = mb
            s = ssim_blur(lum, lb)
            m['ssim_blur12_vs_' + key] = round(float(s.mean()), 4)
            x0, y0, x1, y1 = BOXES['grass fg']
            m['ssim_lawn_box_vs_' + key] = round(float(s[y0:y1, x0:x1].mean()), 4)
            x0, y0, x1, y1 = (1320, 1152, 2400, 1600)
            m['ssim_hero_lower_right_vs_' + key] = round(float(s[y0:y1, x0:x1].mean()), 4)
            x0, y0, x1, y1 = VBOX
            m['ssim_ver_fg_vs_' + key] = round(float(s[y0:y1, x0:x1].mean()), 4)
    # palette outside the maple corner: share of pixels with saturation above 0.70
    mask = np.ones((H, W), bool); mask[:int(0.55 * H), :int(0.40 * W)] = False
    m['share_sat_above_0.70_outside_maple'] = round(float((sat[mask] > 0.70).mean()), 5)
    res[it['name']] = m
    print('GROUND_METRICS', it['name'], json.dumps(m), flush=True)
json.dump(res, open(job['out'], 'w'), indent=1)
print('MEASURE_DONE')
