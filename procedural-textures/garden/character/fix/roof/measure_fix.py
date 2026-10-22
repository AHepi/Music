"""measure_fix.py - runs on the card inside Blender (blender -b --python measure_fix.py -- JOB.json). Plain words: measures the fixed roof stage's finals against the
integrated finals (the 'previous final'): brightness percentiles, saturation, detail energy of the seven boxes, flat windows, palette, the squint test (blurred
luminance similarity) for the whole picture AND for the boxes of my elements (roof, wall, rock, lantern), and writes small JPGs. Same maths as finish_character.py."""
import sys, os, json
import numpy as np
import bpy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
job = json.load(open(sys.argv[sys.argv.index('--') + 1]))
BOXES = {"roof": (700, 300, 1500, 500), "bridge": (0, 1250, 900, 1500), "grass fg": (1500, 1350, 2400, 1600), "maple": (100, 300, 800, 700),
         "sand": (1700, 900, 2300, 1300), "wall": (1500, 580, 2300, 800), "rock": (200, 840, 420, 1050)}
MINE = {'roof': (600, 250, 1700, 620), 'wall': (1500, 480, 2400, 900), 'rocks': (150, 780, 1100, 1100), 'lantern': (1380, 700, 1650, 1080)}


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


def sat_hue(a):
    mx, mn = a.max(-1), a.min(-1)
    sat = (mx - mn) / np.maximum(mx, 1e-4)
    d = np.maximum(mx - mn, 1e-6)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60.0
    return sat, h


def measures(a, boxes=True):
    lum = lum_of(a); l8 = np.round(lum * 255); hf = np.abs(l8 - gblur(l8, 2.0)); sat, hue = sat_hue(a)
    H, W = lum.shape
    out = {'percentiles': {str(p): round(float(np.percentile(lum, p)), 4) for p in (1, 5, 25, 50, 75, 95, 99)}, 'mean_lum': round(float(lum.mean()), 4),
           'mean_saturation': round(float(sat.mean()), 4)}
    if boxes and W == 2400:
        out['detail_energy'] = {k: round(float(hf[y0:y1, x0:x1].mean()), 2) for k, (x0, y0, x1, y1) in BOXES.items()}
        out['detail_energy_mine'] = {k: round(float(hf[y0:y1, x0:x1].mean()), 2) for k, (x0, y0, x1, y1) in MINE.items()}
    y_start = int(0.38 * H); n = f1 = f2 = 0
    for y in range(y_start, H - 96 + 1, 48):
        for x in range(0, W - 96 + 1, 48):
            s = float(lum[y:y + 96, x:x + 96].std()); n += 1; f1 += s < 0.010; f2 += s < 0.014
    out['flat_windows_below_sky'] = {'windows': n, 'std_below_0.010': int(f1), 'share_below_0.014': round(f2 / max(n, 1), 4)}
    mask_out = np.ones((H, W), bool); mask_out[:int(0.55 * H), :int(0.40 * W)] = False
    out['share_sat_above_0.70_outside_maple'] = round(float((sat[mask_out] > 0.70).mean()), 5)
    below = np.zeros((H, W), bool); below[y_start:, :] = True
    out['share_turquoise_below_sky'] = round(float(((hue >= 160) & (hue <= 210) & (sat > 0.35))[below].mean()), 5)
    # share of olive-green (moss) pixels inside the roof box: hue 60-110, sat > 0.25
    x0, y0, x1, y1 = MINE['roof']
    sub_s, sub_h = sat[y0:y1, x0:x1], hue[y0:y1, x0:x1]
    out['roof_box_olive_share'] = round(float(((sub_h >= 55) & (sub_h <= 115) & (sub_s > 0.25)).mean()), 4)
    return out


def ssim_blur(la, lb, sigma_blur=12.0, sigma_win=6.0):
    A, B = gblur(la, sigma_blur), gblur(lb, sigma_blur)
    mu_a, mu_b = gblur(A, sigma_win), gblur(B, sigma_win)
    va = gblur(A * A, sigma_win) - mu_a ** 2; vb = gblur(B * B, sigma_win) - mu_b ** 2; cab = gblur(A * B, sigma_win) - mu_a * mu_b
    c1, c2 = 0.01 ** 2, 0.03 ** 2
    s = ((2 * mu_a * mu_b + c1) * (2 * cab + c2)) / ((mu_a ** 2 + mu_b ** 2 + c1) * (va + vb + c2))
    return s, float(np.corrcoef(A.ravel(), B.ravel())[0, 1])


def save_jpg(arr, path, q):
    h, w = arr.shape[:2]
    img = bpy.data.images.new('tmp_jpg', w, h, alpha=False)
    img.colorspace_settings.name = 'Non-Color'
    rgba = np.concatenate([arr[::-1], np.ones((h, w, 1), np.float32)], axis=2)
    img.pixels.foreach_set(rgba.ravel())
    bpy.context.scene.render.image_settings.file_format = 'JPEG'
    bpy.context.scene.render.image_settings.quality = q
    img.file_format = 'JPEG'; img.filepath_raw = path; img.save(); bpy.data.images.remove(img)


def downscale(a, w):
    h0, w0 = a.shape[:2]
    f = max(1, int(w0 // w))
    if f > 1:
        hh, ww = (h0 // f) * f, (w0 // f) * f
        a = a[:hh, :ww].reshape(hh // f, f, ww // f, f, 3).mean(axis=(1, 3))
    h1, w1 = a.shape[:2]
    if w1 != w:
        nh = int(round(h1 * w / w1)); xs = np.linspace(0, w1 - 1, w); ys = np.linspace(0, h1 - 1, nh)
        x0 = np.floor(xs).astype(int); x1 = np.minimum(x0 + 1, w1 - 1); fx = (xs - x0)[None, :, None]
        y0 = np.floor(ys).astype(int); y1 = np.minimum(y0 + 1, h1 - 1); fy = (ys - y0)[:, None, None]
        top = a[y0][:, x0] * (1 - fx) + a[y0][:, x1] * fx; bot = a[y1][:, x0] * (1 - fx) + a[y1][:, x1] * fx
        a = top * (1 - fy) + bot * fy
    return a


results = {}
for it in job['items']:
    a = load_rgb(it['png'])
    m = measures(a)
    b = load_rgb(it['before'])
    mb = measures(b)
    m['before'] = mb
    la, lb = lum_of(a), lum_of(b)
    s, corr = ssim_blur(la, lb)
    m['ssim_blur12_whole'] = round(float(s.mean()), 4)
    m['corr_blur12_whole'] = round(corr, 4)
    m['ssim_blur12_regions'] = {k: round(float(s[y0:y1, x0:x1].mean()), 4) for k, (x0, y0, x1, y1) in MINE.items()}
    m['ssim_blur12_below_sky_median_window'] = round(float(np.median(s[int(0.2 * s.shape[0]):, :])), 4)
    m['abs_diff_mean'] = round(float(np.abs(a - b).mean()), 4)
    m['abs_diff_in_my_boxes'] = {k: round(float(np.abs(a - b)[y0:y1, x0:x1].mean()), 4) for k, (x0, y0, x1, y1) in MINE.items()}
    # how much of the picture changed at all (more than 0.03 in any channel)
    m['share_pixels_changed_over_0.03'] = round(float((np.abs(a - b).max(-1) > 0.03).mean()), 4)
    results[it['name']] = m
    print('FIX_METRICS', it['name'], json.dumps(m), flush=True)
    od = it['outdir']; os.makedirs(od, exist_ok=True)
    save_jpg(downscale(a, 1200), os.path.join(od, it['name'] + '_1200.jpg'), 88)
    for cn, x0, y0, x1, y1 in it.get('crops', []):
        save_jpg(a[y0:y1, x0:x1], os.path.join(od, '%s_crop_%s.jpg' % (it['name'], cn)), 86)
        save_jpg(b[y0:y1, x0:x1], os.path.join(od, '%s_crop_%s_before.jpg' % (it['name'], cn)), 86)
json.dump(results, open(job['metrics_json'], 'w'), indent=1)
print('MEASURE_DONE')
