"""measure_fix.py (POND FIX ROUND copy of finish_character.py: adds per-region measures: mean colour, blurred-luminance similarity inside a region, detail energy of extra boxes)
finish_character.py - runs on the card inside Blender after the finals (pictures stay on the store; only small JPGs and json are downloaded).
   blender -b --python finish_character.py -- JOB.json
JOB.json = {"items": [{"name": "hero", "png": ".../hero.png", "before": ".../real_hero.png" | null, "outdir": "...", "jpg_width": 1200,
                       "crops": [["name", x0, y0, x1, y1]], "boxes": true}]}
For each picture: the garden's own measures (the same maths as concept/hf_measure_second_helper.py): brightness percentiles, mean saturation, detail
energy of the seven boxes, plus the new acceptance checks (squint match with the previous picture, flat windows, palette) and small JPG previews."""
import sys
import os
import json
import numpy as np
import bpy

job = json.load(open(sys.argv[sys.argv.index('--') + 1]))
BOXES = {"roof": (700, 300, 1500, 500), "bridge": (0, 1250, 900, 1500), "grass fg": (1500, 1350, 2400, 1600), "maple": (100, 300, 800, 700),
         "sand": (1700, 900, 2300, 1300), "wall": (1500, 580, 2300, 800), "rock": (200, 840, 420, 1050)}


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
    k = np.exp(-x * x / (2 * sigma * sigma))
    k /= k.sum()
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


def measures(a, with_boxes):
    lum = lum_of(a)
    l8 = np.round(lum * 255)
    hf = np.abs(l8 - gblur(l8, 2.0))
    sat, hue = sat_hue(a)
    H, W = lum.shape
    out = {'percentiles': {str(p): round(float(np.percentile(lum, p)), 4) for p in (1, 5, 25, 50, 75, 95, 99)}, 'mean_lum': round(float(lum.mean()), 4),
           'mean_saturation': round(float(sat.mean()), 4)}
    if with_boxes and W == 2400:
        out['detail_energy'] = {k: round(float(hf[y0:y1, x0:x1].mean()), 2) for k, (x0, y0, x1, y1) in BOXES.items()}
    # flat windows (96 x 96, step 48) below the sky and hills (y >= 38 percent of the height): std of luminance under 0.010 and under 0.014
    y_start = int(0.38 * H)
    n = f1 = f2 = 0
    for y in range(y_start, H - 96 + 1, 48):
        for x in range(0, W - 96 + 1, 48):
            s = float(lum[y:y + 96, x:x + 96].std())
            n += 1
            f1 += s < 0.010
            f2 += s < 0.014
    out['flat_windows_below_sky'] = {'windows': n, 'std_below_0.010': int(f1), 'share_below_0.014': round(f2 / max(n, 1), 4)}
    # palette: saturation above 0.70 outside the maple (left 40 percent of the picture, top 55 percent), turquoise (hue 160-210, sat above 0.35) below the sky
    mask_out = np.ones((H, W), bool)
    mask_out[:int(0.55 * H), :int(0.40 * W)] = False
    out['share_sat_above_0.70_outside_maple'] = round(float((sat[mask_out] > 0.70).mean()), 5)
    below = np.zeros((H, W), bool)
    below[y_start:, :] = True
    out['share_turquoise_below_sky'] = round(float(((hue >= 160) & (hue <= 210) & (sat > 0.35))[below].mean()), 5)
    return out


def ssim_blur(la, lb, sigma_blur=12.0, sigma_win=6.0):
    A, B = gblur(la, sigma_blur), gblur(lb, sigma_blur)
    mu_a, mu_b = gblur(A, sigma_win), gblur(B, sigma_win)
    va = gblur(A * A, sigma_win) - mu_a ** 2
    vb = gblur(B * B, sigma_win) - mu_b ** 2
    cab = gblur(A * B, sigma_win) - mu_a * mu_b
    c1, c2 = 0.01 ** 2, 0.03 ** 2
    s = ((2 * mu_a * mu_b + c1) * (2 * cab + c2)) / ((mu_a ** 2 + mu_b ** 2 + c1) * (va + vb + c2))
    corr = float(np.corrcoef(A.ravel(), B.ravel())[0, 1])
    return round(float(s.mean()), 4), round(corr, 4)


def save_jpg(arr, path, q):
    h, w = arr.shape[:2]
    img = bpy.data.images.new('tmp_jpg', w, h, alpha=False)
    img.colorspace_settings.name = 'Non-Color'
    rgba = np.concatenate([arr[::-1], np.ones((h, w, 1), np.float32)], axis=2)
    img.pixels.foreach_set(np.ascontiguousarray(rgba, dtype=np.float32).ravel())
    sc = bpy.context.scene
    sc.render.image_settings.file_format = 'JPEG'
    sc.render.image_settings.quality = q
    img.file_format = 'JPEG'
    img.filepath_raw = path
    img.save()
    bpy.data.images.remove(img)


def downscale(a, w):
    """area-average downscale to width w (any ratio) with numpy: first integer box, then linear interpolation"""
    h0, w0 = a.shape[:2]
    f = max(1, int(w0 // w))
    if f > 1:
        hh, ww = (h0 // f) * f, (w0 // f) * f
        a = a[:hh, :ww].reshape(hh // f, f, ww // f, f, 3).mean(axis=(1, 3))
    h1, w1 = a.shape[:2]
    if w1 != w:
        nh = int(round(h1 * w / w1))
        xs = np.linspace(0, w1 - 1, w)
        ys = np.linspace(0, h1 - 1, nh)
        x0 = np.floor(xs).astype(int)
        x1 = np.minimum(x0 + 1, w1 - 1)
        fx = (xs - x0)[None, :, None]
        y0 = np.floor(ys).astype(int)
        y1 = np.minimum(y0 + 1, h1 - 1)
        fy = (ys - y0)[:, None, None]
        top = a[y0][:, x0] * (1 - fx) + a[y0][:, x1] * fx
        bot = a[y1][:, x0] * (1 - fx) + a[y1][:, x1] * fx
        a = top * (1 - fy) + bot * fy
    return a



def region_stats(a, b, reg):
    """per region (x0,y0,x1,y1 in 2400 coords): mean rgb of a and b, mean luminance, saturation, SSIM-blur12 inside the region, detail energy of a and b"""
    out = {}
    la, lb = lum_of(a), lum_of(b)
    A, B = gblur(la, 12.0), gblur(lb, 12.0)
    mu_a, mu_b = gblur(A, 6.0), gblur(B, 6.0)
    va = gblur(A * A, 6.0) - mu_a ** 2
    vb = gblur(B * B, 6.0) - mu_b ** 2
    cab = gblur(A * B, 6.0) - mu_a * mu_b
    c1, c2 = 0.01 ** 2, 0.03 ** 2
    smap = ((2 * mu_a * mu_b + c1) * (2 * cab + c2)) / ((mu_a ** 2 + mu_b ** 2 + c1) * (va + vb + c2))
    l8a, l8b = np.round(la * 255), np.round(lb * 255)
    hfa, hfb = np.abs(l8a - gblur(l8a, 2.0)), np.abs(l8b - gblur(l8b, 2.0))
    sa, _ = sat_hue(a); sb, _ = sat_hue(b)
    for name, (x0, y0, x1, y1) in reg.items():
        sl = (slice(y0, y1), slice(x0, x1))
        out[name] = {'mean_rgb_new': [round(float(a[sl][..., i].mean()), 4) for i in range(3)], 'mean_rgb_before': [round(float(b[sl][..., i].mean()), 4) for i in range(3)],
                     'mean_lum_new': round(float(la[sl].mean()), 4), 'mean_lum_before': round(float(lb[sl].mean()), 4),
                     'sat_new': round(float(sa[sl].mean()), 4), 'sat_before': round(float(sb[sl].mean()), 4),
                     'ssim_blur12': round(float(smap[sl].mean()), 4), 'detail_new': round(float(hfa[sl].mean()), 2), 'detail_before': round(float(hfb[sl].mean()), 2)}
    return out


results = {}
for it in job['items']:
    if not os.path.exists(it['png']):
        print('missing', it['png'])
        continue
    a = load_rgb(it['png'])
    m = measures(a, it.get('boxes', True))
    if it.get('before') and os.path.exists(it['before']):
        b = load_rgb(it['before'])
        mb = measures(b, True)
        m['before'] = mb
        m['ssim_blur12_vs_before'], m['corr_blur12_vs_before'] = ssim_blur(lum_of(a), lum_of(b))
        m['abs_diff_mean'] = round(float(np.abs(a - b).mean()), 4)
        if it.get('regions'):
            m['regions'] = region_stats(a, b, {k: tuple(v) for k, v in it['regions'].items()})
    results[it['name']] = m
    print('CHARACTER_METRICS', it['name'], json.dumps(m), flush=True)
    od = it['outdir']
    os.makedirs(od, exist_ok=True)
    if it.get('no_jpg'):
        continue
    save_jpg(downscale(a, it.get('jpg_width', 1200)), os.path.join(od, it['name'] + '_%d.jpg' % it.get('jpg_width', 1200)), it.get('quality', 86))
    for cn, x0, y0, x1, y1 in it.get('crops', []):
        save_jpg(a[y0:y1, x0:x1], os.path.join(od, '%s_crop_%s.jpg' % (it['name'], cn)), 84)
    if it.get('before') and it.get('crops') and os.path.exists(it['before']):
        for cn, x0, y0, x1, y1 in it['crops']:
            save_jpg(b[y0:y1, x0:x1], os.path.join(od, '%s_crop_%s_before.jpg' % (it['name'], cn)), 84)
json.dump(results, open(job['metrics_json'], 'w'), indent=1)
print('FINISH_DONE')
