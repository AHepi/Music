"""squint_regions.py - WHERE the squint test loses its points (runs on the card inside Blender, numpy only).
   blender -b --factory-startup --python squint_regions.py -- JOB.json
JOB.json = {"json": "/abs/out.json", "items": [{"name": "hero", "png": "new picture", "before": "picture to compare with", "heat": "/abs/heat.jpg" (optional),
            "regions": {"maple": [x0, y0, x1, y1], ...} (optional, drawn first-come-first-served, the rest is 'rest')}]}
Same maths as finish_character.py: luminance, 12 px Gaussian blur, structural similarity with a 6 px window; per picture it prints the mean score, and for
every region the mean score inside it and its SHARE of the total missing score (sum of 1 - score), and for a 4 x 6 grid the same. The heat picture shows
(1 - score) as red over the new picture."""
import sys
import os
import json
import numpy as np
import bpy

job = json.load(open(sys.argv[sys.argv.index('--') + 1]))


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


def ssim_map(la, lb, sigma_blur=12.0, sigma_win=6.0):
    A, B = gblur(la, sigma_blur), gblur(lb, sigma_blur)
    mu_a, mu_b = gblur(A, sigma_win), gblur(B, sigma_win)
    va = gblur(A * A, sigma_win) - mu_a ** 2
    vb = gblur(B * B, sigma_win) - mu_b ** 2
    cab = gblur(A * B, sigma_win) - mu_a * mu_b
    c1, c2 = 0.01 ** 2, 0.03 ** 2
    s = ((2 * mu_a * mu_b + c1) * (2 * cab + c2)) / ((mu_a ** 2 + mu_b ** 2 + c1) * (va + vb + c2))
    return s, A, B


def save_jpg(arr, path, q=84):
    h, w = arr.shape[:2]
    img = bpy.data.images.new('tmp_jpg', w, h, alpha=False)
    img.colorspace_settings.name = 'Non-Color'
    rgba = np.concatenate([np.clip(arr[::-1], 0, 1), np.ones((h, w, 1), np.float32)], axis=2).astype(np.float32)
    img.pixels.foreach_set(rgba.ravel())
    sc = bpy.context.scene
    sc.render.image_settings.file_format = 'JPEG'
    sc.render.image_settings.quality = q
    img.file_format = 'JPEG'
    img.filepath_raw = path
    img.save()
    bpy.data.images.remove(img)


res = {}
for it in job['items']:
    a, b = load_rgb(it['png']), load_rgb(it['before'])
    H, W = a.shape[:2]
    s, A, B = ssim_map(lum_of(a), lum_of(b))
    loss = 1.0 - s
    extra = {}
    for sg in it.get('extra_sigmas', []):
        s2, _, _ = ssim_map(lum_of(a), lum_of(b), sigma_blur=float(sg), sigma_win=float(sg) / 2.0)
        extra[str(sg)] = round(float(s2.mean()), 4)
    tot = float(loss.sum())
    out = {'mean_score': round(float(s.mean()), 4), 'mean_score_other_blur_sigmas': extra, 'size': [W, H], 'mean_blurred_lum_new_minus_before': round(float(A.mean() - B.mean()), 4)}
    taken = np.zeros((H, W), bool)
    regs = {}
    for k, (x0, y0, x1, y1) in it.get('regions', {}).items():
        m = np.zeros((H, W), bool)
        m[y0:y1, x0:x1] = True
        m &= ~taken
        taken |= m
        regs[k] = {'pixels_share': round(float(m.mean()), 4), 'mean_score_inside': round(float(s[m].mean()), 4), 'share_of_missing_score': round(float(loss[m].sum() / tot), 4),
                   'mean_blurred_diff': round(float((A - B)[m].mean()), 4)}
    m = ~taken
    regs['rest'] = {'pixels_share': round(float(m.mean()), 4), 'mean_score_inside': round(float(s[m].mean()), 4), 'share_of_missing_score': round(float(loss[m].sum() / tot), 4),
                    'mean_blurred_diff': round(float((A - B)[m].mean()), 4)}
    out['regions'] = regs
    grid = []
    for gy in range(4):
        row = []
        for gx in range(6):
            sub = loss[gy * H // 4:(gy + 1) * H // 4, gx * W // 6:(gx + 1) * W // 6]
            row.append(round(float(sub.sum() / tot), 3))
        grid.append(row)
    out['grid_share_of_missing_score_4x6'] = grid
    # what would the score be if a region were left exactly as before (the best case for that stage)
    out['score_if_region_unchanged'] = {}
    for k in list(regs):
        if k == 'rest':
            continue
        x0, y0, x1, y1 = it['regions'][k]
        keep = np.ones((H, W), bool)
        keep[y0:y1, x0:x1] = False
        out['score_if_region_unchanged'][k] = round(float(1.0 - loss[keep].sum() / (H * W)), 4)
    res[it['name']] = out
    print('SQUINT_REGIONS', it['name'], json.dumps(out), flush=True)
    if it.get('heat'):
        hm = np.clip(loss / 0.5, 0, 1)[..., None]
        base = np.repeat(lum_of(a)[..., None], 3, axis=2) * 0.6
        heat = base * (1 - hm) + np.array([1.0, 0.1, 0.1], np.float32) * hm
        step = max(1, W // 1000)
        save_jpg(heat[::step, ::step], it['heat'])
os.makedirs(os.path.dirname(job['json']), exist_ok=True)
json.dump(res, open(job['json'], 'w'), indent=1)
print('SQUINT_DONE')
