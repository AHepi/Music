"""region_metrics.py - inside Blender: numbers for the wood elements' boxes, three versions of a picture (original real, integrated final, this fix).
   blender -b --python region_metrics.py -- JOB.json   JOB = {out, hero: {orig, integ, mine}, veranda: {...}, mask_mine, mask_orig}"""
import sys, json
import numpy as np, bpy
job = json.load(open(sys.argv[sys.argv.index('--') + 1]))

def load_rgb(path, alpha=False):
    img = bpy.data.images.load(path); img.colorspace_settings.name = 'Non-Color'
    w, h = img.size; a = np.empty(w * h * 4, np.float32); img.pixels.foreach_get(a); bpy.data.images.remove(img)
    a = a.reshape(h, w, 4)[::-1]
    return a if alpha else a[..., :3].copy()

def gblur(a, sigma):
    r = int(3 * sigma + 1); x = np.arange(-r, r + 1); k = np.exp(-x * x / (2 * sigma * sigma)); k /= k.sum()
    p = np.pad(a, ((r, r), (0, 0)), mode='reflect'); a = sum(k[i] * p[i:i + a.shape[0]] for i in range(2 * r + 1))
    p = np.pad(a, ((0, 0), (r, r)), mode='reflect'); return sum(k[i] * p[:, i:i + a.shape[1]] for i in range(2 * r + 1))

def lum(a): return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]

def hsv(a):
    mx, mn = a.max(-1), a.min(-1); s = (mx - mn) / np.maximum(mx, 1e-4); d = np.maximum(mx - mn, 1e-6)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60.0
    return h, s, mx

def box_stats(a, box, mask=None):
    x0, y0, x1, y1 = box
    c = a[y0:y1, x0:x1]; L = lum(c); l8 = np.round(L * 255); hf = np.abs(l8 - gblur(l8, 2.0))
    h, s, v = hsv(c)
    m = np.ones(L.shape, bool) if mask is None else mask[y0:y1, x0:x1]
    olive = (h >= 55) & (h <= 125) & (s > 0.22) & (v < 0.85) & (L < 0.6)
    greenish = (c[..., 1] >= 0.92 * c[..., 0]) & (c[..., 1] > 1.12 * c[..., 2]) & (s > 0.18) & (L < 0.65)      # green is not weaker than red: moss and algae, not wood
    return dict(mean_lum=round(float(L[m].mean()), 4), std_lum=round(float(L[m].std()), 4), mean_sat=round(float(s[m].mean()), 4), detail_energy=round(float(hf[m].mean()), 2),
                olive_share=round(float((olive & m).sum() / max(m.sum(), 1)), 4), greenish_share=round(float((greenish & m).sum() / max(m.sum(), 1)), 4), pixels=int(m.sum()))

res = {}
mm = load_rgb(job['mask_mine'], alpha=True)[..., 3] > 0.5 if job.get('mask_mine') else None
mo = load_rgb(job['mask_orig'], alpha=True)[..., 3] > 0.5 if job.get('mask_orig') else None
for pic, boxes in (('hero', {'bridge_left_run': (0, 1250, 900, 1500), 'bridge_crop': (0, 1050, 1560, 1580), 'bridge_box_energy': (0, 1250, 900, 1500)}),
                   ('veranda', {'deck_box': (1450, 700, 2350, 1500)})):
    if pic not in job: continue
    res[pic] = {}
    for ver, path in job[pic].items():
        a = load_rgb(path)
        d = {}
        for bn, box in boxes.items():
            d[bn] = box_stats(a, box, (mo if ver == 'orig' else mm) if (pic == 'hero' and bn != 'bridge_box_energy') else None)
        if pic == 'hero':
            d['bridge_planks_only'] = box_stats(a, (0, 1050, 1560, 1580), mo if ver == 'orig' else mm) if mm is not None else None
        res[pic][ver] = d
# blurred-luminance difference between mine and integrated inside the bridge crop and over the maple box
if 'hero' in job:
    A, B = load_rgb(job['hero']['mine']), load_rgb(job['hero']['integ'])
    la, lb = gblur(lum(A), 12.0), gblur(lum(B), 12.0)
    for nm, (x0, y0, x1, y1) in (('bridge_crop', (0, 1050, 1560, 1580)), ('maple', (100, 300, 800, 700)), ('whole', (0, 0, 2400, 1600))):
        res['hero'].setdefault('blur12_mean_abs_diff_mine_vs_integrated', {})[nm] = round(float(np.abs(la[y0:y1, x0:x1] - lb[y0:y1, x0:x1]).mean()), 4)
if job.get('mask_debug') and 'hero' in job:
    D = load_rgb(job['mask_debug'], alpha=True)
    vis = D[..., 3] > 0.5
    walk = vis & (D[..., 2] > 0.5)
    off = vis & ~walk
    moss = vis & (D[..., 0] > 0.6)
    res['hero']['walking_line'] = {}
    for ver in ('orig', 'integ', 'mine'):
        L = lum(load_rgb(job['hero'][ver]))
        res['hero']['walking_line'][ver] = dict(walk_mean_lum=round(float(L[walk].mean()), 4), off_mean_lum=round(float(L[off & ~moss].mean()), 4), plank_mean_lum=round(float(L[vis].mean()), 4),
                                                walk_minus_plank_average=round(float(L[walk].mean() - L[vis].mean()), 4))
json.dump(res, open(job['out'], 'w'), indent=1)
print('REGION_METRICS', json.dumps(res))
