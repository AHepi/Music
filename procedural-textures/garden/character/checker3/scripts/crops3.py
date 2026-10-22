# Checker's own crops and metrics for the re-check (runs inside Blender, numpy only). blender -b --python crops3.py
import bpy, json, os, sys, colorsys
import numpy as np
G = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/garden/'
OUT = G + 'character/checker3/out/crops/'
os.makedirs(OUT, exist_ok=True)
NEW = {'hero': G + 'character/fix/final/out/finals/final_hero.png', 'veranda': G + 'character/fix/final/out/finals/final_veranda.png'}
FIRST = {'hero': G + 'character/final/out/finals/final_hero.png', 'veranda': G + 'character/final/out/finals/final_veranda.png'}
OLD = {'hero': G + 'fix/out/final/real_hero.png', 'veranda': G + 'fix/out/final/real_veranda.png'}
def load(path):
    img = bpy.data.images.load(path); img.colorspace_settings.name = 'Non-Color'
    w, h = img.size; a = np.empty(w * h * 4, np.float32); img.pixels.foreach_get(a)
    bpy.data.images.remove(img)
    return a.reshape(h, w, 4)[::-1, :, :3].copy()
def save_jpg(arr, path, q=82):
    h, w = arr.shape[:2]
    img = bpy.data.images.new('t', w, h, alpha=False); img.colorspace_settings.name = 'Non-Color'
    img.pixels.foreach_set(np.concatenate([np.clip(arr[::-1], 0, 1), np.ones((h, w, 1), np.float32)], axis=2).ravel())
    bpy.context.scene.render.image_settings.file_format = 'JPEG'; bpy.context.scene.render.image_settings.quality = q
    img.file_format = 'JPEG'; img.filepath_raw = path; img.save(); bpy.data.images.remove(img)
def gblur(a, sigma):
    r = int(3 * sigma + 1); x = np.arange(-r, r + 1); k = np.exp(-x * x / (2 * sigma * sigma)); k /= k.sum()
    p = np.pad(a, ((r, r), (0, 0)), mode='reflect'); a = sum(k[i] * p[i:i + a.shape[0]] for i in range(2 * r + 1))
    p = np.pad(a, ((0, 0), (r, r)), mode='reflect'); return sum(k[i] * p[:, i:i + a.shape[1]] for i in range(2 * r + 1))
def boxmean(a, k):
    c = np.cumsum(np.cumsum(np.pad(a, ((1, 0), (1, 0))), 0), 1)
    return (c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k]) / (k * k)
lum = lambda a: 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
def ssim_box(la, lb, blur=12.0, k=31):
    # different formula from the builders': box window 31 px on a 12 px blur, standard SSIM constants
    A, B = gblur(la, blur), gblur(lb, blur)
    ma, mb = boxmean(A, k), boxmean(B, k)
    va = boxmean(A * A, k) - ma ** 2; vb = boxmean(B * B, k) - mb ** 2; cab = boxmean(A * B, k) - ma * mb
    c1, c2 = 0.01 ** 2, 0.03 ** 2
    s = ((2 * ma * mb + c1) * (2 * cab + c2)) / ((ma ** 2 + mb ** 2 + c1) * (va + vb + c2))
    return s
def ssim_gauss(la, lb, blur=12.0, sw=6.0):
    A, B = gblur(la, blur), gblur(lb, blur)
    ma, mb = gblur(A, sw), gblur(B, sw)
    va = gblur(A * A, sw) - ma ** 2; vb = gblur(B * B, sw) - mb ** 2; cab = gblur(A * B, sw) - ma * mb
    c1, c2 = 0.01 ** 2, 0.03 ** 2
    return ((2 * ma * mb + c1) * (2 * cab + c2)) / ((ma ** 2 + mb ** 2 + c1) * (va + vb + c2))
CR = {'hero': [('bridge_left', 0, 1100, 800, 1600), ('bridge_mid', 700, 1000, 1500, 1450), ('roof', 700, 300, 1450, 620), ('lawn_lr', 1500, 1250, 2400, 1600),
               ('pond_rocks', 250, 850, 1100, 1250), ('maple', 0, 150, 900, 800), ('pine_wall', 1550, 250, 2400, 900), ('lantern_rocks', 1100, 750, 1800, 1150), ('hero_pond_centre', 450, 950, 1350, 1300)],
      'veranda': [('deck', 1500, 800, 2400, 1600), ('lantern', 250, 300, 950, 1200), ('far_bridge_pond', 600, 550, 1500, 1050), ('maple', 1250, 80, 2250, 700),
                  ('moss_bank', 1150, 950, 1800, 1350), ('lawn_path', 0, 1000, 800, 1600)]}
BOXES = {"roof": (700, 300, 1500, 500), "bridge": (0, 1250, 900, 1500), "grass fg": (1500, 1350, 2400, 1600), "maple": (100, 300, 800, 700), "sand": (1700, 900, 2300, 1300), "wall": (1500, 580, 2300, 800), "rock": (200, 840, 420, 1050)}
REG = {'hero': {'maple': (0, 0, 950, 850), 'pond': (250, 880, 1400, 1380)}, 'veranda': {'maple': (1050, 50, 2000, 560)}}
M = {}
for pic in ('hero', 'veranda'):
    n, f, o = load(NEW[pic]), load(FIRST[pic]), load(OLD[pic])
    for name, x0, y0, x1, y1 in CR[pic]:
        parts = []
        sep = np.ones((y1 - y0, 8, 3), np.float32)
        if name in ('maple',): parts = [o[y0:y1, x0:x1], sep, f[y0:y1, x0:x1], sep, n[y0:y1, x0:x1]]
        else: parts = [f[y0:y1, x0:x1], sep, n[y0:y1, x0:x1]]
        arr = np.concatenate(parts, axis=1)
        if arr.shape[1] > 2000: arr = arr[:, ::1][:, :2000]
        save_jpg(arr, OUT + '%s_%s.jpg' % (pic, name), 80)
        save_jpg(n[y0:y1, x0:x1], OUT + '%s_%s_new.jpg' % (pic, name), 86)
    Ln, Lf, Lo = lum(n), lum(f), lum(o)
    H, W = Ln.shape
    res = {}
    for tag, a, L in (('new', n, Ln), ('first', f, Lf), ('old', o, Lo)):
        l8 = np.round(L * 255); hf = np.abs(l8 - gblur(l8, 2.0))
        mx, mn = a.max(-1), a.min(-1); sat = (mx - mn) / np.maximum(mx, 1e-4)
        d = {'pct': {str(p): round(float(np.percentile(L, p)), 3) for p in (1, 5, 25, 50, 75, 95, 99)}, 'sat_mean': round(float(sat.mean()), 3)}
        d['energy'] = {k: round(float(hf[y0:y1, x0:x1].mean()), 2) for k, (x0, y0, x1, y1) in BOXES.items()}
        # hot saturated share outside maple region, below the sky
        mask = np.ones((H, W), bool)
        mx0, my0, mx1, my1 = REG[pic]['maple']; mask[my0:my1, mx0:mx1] = False
        if pic == 'hero': mask[:int(0.35 * H)] = False
        d['sat_gt_0.70_outside_maple_pct'] = round(float(100 * (sat[mask] > 0.70).mean()), 3)
        # turquoise below sky and hills (lower 45 %)
        low = np.zeros((H, W), bool); low[int(0.55 * H):] = True
        r, g, b = a[..., 0], a[..., 1], a[..., 2]
        hue = np.zeros((H, W), np.float32)
        d_ = np.maximum(mx - mn, 1e-6)
        hh = np.where(mx == r, ((g - b) / d_) % 6, np.where(mx == g, (b - r) / d_ + 2, (r - g) / d_ + 4)) * 60
        turq = (hh >= 160) & (hh <= 210) & (sat > 0.35)
        d['turquoise_lower45_pct'] = round(float(100 * turq[low].mean()), 3)
        # flat windows (hero: below 38 %)
        ys = int(0.38 * H); nn = ff = 0
        for y in range(ys, H - 96 + 1, 48):
            for x in range(0, W - 96 + 1, 48):
                s = float(L[y:y + 96, x:x + 96].std()); nn += 1; ff += s < 0.010
        d['flat_windows'] = [ff, nn]
        res[tag] = d
    # squint scores
    sq = {}
    for tag, (A, B) in {'new_vs_old': (Ln, Lo), 'first_vs_old': (Lf, Lo), 'new_vs_first': (Ln, Lf)}.items():
        sg = ssim_gauss(B if tag != 'new_vs_first' else B, A) if False else ssim_gauss(A, B)
        sb = ssim_box(A, B)
        sq[tag] = {'gauss6': round(float(sg.mean()), 4), 'box31': round(float(sb.mean()), 4), 'corr': round(float(np.corrcoef(gblur(A, 12).ravel(), gblur(B, 12).ravel())[0, 1]), 4)}
        if tag == 'new_vs_old':
            # share of missing score by region, then "score outside maple and pond"
            miss = 1 - sg
            tot = float(miss.sum())
            reg = {}
            used = np.zeros((H, W), bool)
            for rn, (x0, y0, x1, y1) in REG[pic].items():
                m = np.zeros((H, W), bool); m[y0:y1, x0:x1] = True; m &= ~used; used |= m
                reg[rn] = {'mean_score_inside': round(float(sg[m].mean()), 3), 'share_of_missing': round(float(miss[m].sum() / tot), 3)}
            rest = ~used
            reg['rest'] = {'mean_score_inside': round(float(sg[rest].mean()), 3), 'share_of_missing': round(float(miss[rest].sum() / tot), 3)}
            sq['regions_new_vs_old'] = reg
            # score if maple and pond areas were identical
            s2 = sg.copy(); s2[used] = 1.0
            sq['gauss6_if_maple_and_pond_identical'] = round(float(s2.mean()), 4)
    res['squint'] = sq
    # plank colours in the bridge region (hero): olive/green share
    if pic == 'hero':
        for nm, (x0, y0, x1, y1) in {'bridge_left_run': (0, 1100, 800, 1500), 'bridge_right_run': (700, 1000, 1500, 1450)}.items():
            for tag, a in (('new', n), ('first', f), ('old', o)):
                c = a[y0:y1, x0:x1]
                mx, mn = c.max(-1), c.min(-1); sat = (mx - mn) / np.maximum(mx, 1e-4)
                r, g, b = c[..., 0], c[..., 1], c[..., 2]
                d_ = np.maximum(mx - mn, 1e-6)
                hh = np.where(mx == r, ((g - b) / d_) % 6, np.where(mx == g, (b - r) / d_ + 2, (r - g) / d_ + 4)) * 60
                green = (hh >= 55) & (hh <= 130) & (sat > 0.22) & (mx > 0.12)
                res.setdefault('plank_green_pct', {})[nm + '_' + tag] = round(float(100 * green.mean()), 2)
                res.setdefault('plank_mean_lum_sat', {})[nm + '_' + tag] = [round(float(lum(c).mean()), 3), round(float(sat.mean()), 3)]
    M[pic] = res
    print(pic, json.dumps(res)[:1500], flush=True)
json.dump(M, open(OUT + 'crops3.json', 'w'), indent=1)
print('CROPS3 DONE')
