"""What this file does (plain words): tries possible brightness fixes on the Python copy of the stage's finishing step (finish_model.py), quickly, before any picture is drawn, so only the promising ones are drawn by the real stage.
For each possible fix (a change of the finishing look values and/or of the filmic curve) it lists, for the NEW WET front painting at the plate's view:
  - how bright the road arrives compared with the painting (whole road, and its far, middle and near thirds); the aim is at least 0.90
  - how bright the road's DARK parts arrive (painted brightness 0.08 to 0.22: the dark stones and joints of the wet road); 1.00 = as painted
  - how much of the road's fine detail (joints, stones, rubbish: the picture minus its own blur) survives, as a share of the painted detail
  - how much the film's own DRY lockout painting would change if the same fix were used on it (mean brightness difference over the picture and over its road): the fix must not change the film's existing dry look
It also lists the options that are only in the Python copy (a "toe" protection of the filmic curve) so they can be compared. Writes numbers/fix_candidates_model.json. Run: python3 -I tools/choose_fix.py
"""
import json, os, sys
import cv2, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'tools'))
import finish_model as fm
from finish_model import lum, W, H, srgb_to_lin, lin_to_srgb, aces, smoothstep, vignette_factor
from stage_common import central, central_mask, masks, er, load01, TEST1, FILM
P = lambda *a: os.path.join(HERE, *a)

M = masks(TEST1 + 'alignment/facts_surfaces/')
road = er(central_mask(M['road']))
rows = np.where(road.any(axis=1))[0]
thirds = [(rows[0], rows[int(len(rows) / 3)]), (rows[int(len(rows) / 3)], rows[int(2 * len(rows) / 3)]), (rows[int(2 * len(rows) / 3)], rows[-1] + 1)]
bands = []
for a, b in thirds:
    m = np.zeros_like(road); m[a:b] = road[a:b]; bands.append(m)       # far, middle, near

wet = central(load01(P('../paint/front_painting_final.png')))
dry = central(load01(FILM + 'lockout-painted.jpg'))
pl_w, pl_d = lum(wet), lum(dry)


def toe_finish(img, look, protect, knee):
    """the finishing step with a protected toe: below the knee (in light terms) the filmic curve is blended back toward "no curve" by `protect` (0 = the film's curve, 1 = no curve there)."""
    L = dict(fm.LOCKOUT_LOOK); L.update(look)
    c = srgb_to_lin(img) * L['exposure']
    a = aces(c)
    w = protect * (1.0 - smoothstep(0.0, knee, c))
    c = a * (1 - w) + c * w
    luma = c @ np.array([0.2126, 0.7152, 0.0722])
    c = luma[..., None] + (c - luma[..., None]) * L['saturation']
    c = (c - 0.5) * L['contrast'] + 0.5
    t = L['shadowTint'] + (np.array(L['highlightTint']) - np.array(L['shadowTint'])) * smoothstep(0.05, 0.75, luma)[..., None]
    c = (1 - L['tintAmount']) * c + L['tintAmount'] * (c * t * 2.0)
    c = c + L['lift'] * (1.0 - c)
    out = lin_to_srgb(np.clip(c, 0, 1)) * vignette_factor(img.shape[0], img.shape[1], L['vignette'])[..., None]
    n = np.random.RandomState(0).rand(*out.shape[:2]) - 0.5
    return np.clip(out + (n * L['grain'])[..., None] * (1 - 0.6 * out), 0, 1)


def hp(L):
    return L - cv2.GaussianBlur(L, (0, 0), 2.0)


base_w = fm.finish(wet, with_grain=True)
base_d = fm.finish(dry, with_grain=True)
dark = road & (pl_w > 0.08) & (pl_w < 0.22)


def evaluate(fn):
    ow, od = fn(wet), fn(dry)
    lw, ld = lum(ow), lum(od)
    r = {'road_arrives': float(lw[road].mean() / pl_w[road].mean()),
         'far_third': float(lw[bands[0]].mean() / pl_w[bands[0]].mean()), 'middle_third': float(lw[bands[1]].mean() / pl_w[bands[1]].mean()), 'near_third': float(lw[bands[2]].mean() / pl_w[bands[2]].mean()),
         'dark_road_parts_arrive': float(lw[dark].mean() / pl_w[dark].mean()),
         'road_detail_kept': float(np.std(hp(lw)[road]) / np.std(hp(pl_w)[road])),
         'dry_lockout_change_mean_abs_whole_picture': float(np.abs(ld - lum(base_d)).mean()),
         'dry_lockout_change_mean_abs_road': float(np.abs(ld - lum(base_d))[road].mean()),
         'dry_lockout_road_arrives': float(ld[road].mean() / pl_d[road].mean())}
    return r


cands = {
    'now (the film as it is)': lambda im: fm.finish(im),
    'vignette 0.30 -> 0.20': lambda im: fm.finish(im, dict(vignette=0.20)),
    'vignette 0.30 -> 0.15': lambda im: fm.finish(im, dict(vignette=0.15)),
    'vignette 0.30 -> 0.10': lambda im: fm.finish(im, dict(vignette=0.10)),
    'vignette 0': lambda im: fm.finish(im, dict(vignette=0.0)),
    'contrast 1.04 -> 1.0 (lift stays)': lambda im: fm.finish(im, dict(contrast=1.0)),
    'exposure 1.0 -> 1.10': lambda im: fm.finish(im, dict(exposure=1.10)),
    'exposure 1.0 -> 1.15': lambda im: fm.finish(im, dict(exposure=1.15)),
    'filmic curve off': lambda im: fm.finish(im, dict(filmic=0.0)),
    'filmic off, contrast 1.0, lift 0': lambda im: fm.finish(im, dict(filmic=0.0, contrast=1.0, lift=0.0)),
    'filmic off, contrast 1.0, lift 0, vignette 0.15': lambda im: fm.finish(im, dict(filmic=0.0, contrast=1.0, lift=0.0, vignette=0.15)),
    'filmic off, contrast 1.0, lift 0, vignette 0.20': lambda im: fm.finish(im, dict(filmic=0.0, contrast=1.0, lift=0.0, vignette=0.20)),
    'filmic off, contrast 1.0, lift 0, vignette 0.10': lambda im: fm.finish(im, dict(filmic=0.0, contrast=1.0, lift=0.0, vignette=0.10)),
    'filmic off, contrast 1.0, lift 0, tint off, vignette 0.10': lambda im: fm.finish(im, dict(filmic=0.0, contrast=1.0, lift=0.0, tintAmount=0.0, vignette=0.10)),
    'toe: curve may lift but never crush; contrast/lift/vignette as now': lambda im: fm.finish(im, dict(toe=1.0)),
    'toe, contrast 1.0, lift 0': lambda im: fm.finish(im, dict(toe=1.0, contrast=1.0, lift=0.0)),
    'toe, vignette 0.25': lambda im: fm.finish(im, dict(toe=1.0, vignette=0.25)),
    'toe, vignette 0.20': lambda im: fm.finish(im, dict(toe=1.0, vignette=0.20)),
    'toe, vignette 0.15': lambda im: fm.finish(im, dict(toe=1.0, vignette=0.15)),
    'toe, contrast 1.0, lift 0, vignette 0.25': lambda im: fm.finish(im, dict(toe=1.0, contrast=1.0, lift=0.0, vignette=0.25)),
    'toe, contrast 1.0, lift 0, vignette 0.20': lambda im: fm.finish(im, dict(toe=1.0, contrast=1.0, lift=0.0, vignette=0.20)),
    'toe, lift 0, vignette 0.20': lambda im: fm.finish(im, dict(toe=1.0, lift=0.0, vignette=0.20)),
    'toe, contrast 1.0, vignette 0.20': lambda im: fm.finish(im, dict(toe=1.0, contrast=1.0, vignette=0.20)),
    'toe + exposure 1.05, vignette 0.25': lambda im: fm.finish(im, dict(toe=1.0, exposure=1.05, vignette=0.25)),
}
res = {}
print(f"{'candidate':66s} road far mid near | dark | detail | dry change (picture / road) | dry road arrives")
for name, fn in cands.items():
    r = evaluate(fn); res[name] = r
    print(f"{name:66s} {r['road_arrives']:.3f} {r['far_third']:.2f} {r['middle_third']:.2f} {r['near_third']:.2f} | {r['dark_road_parts_arrive']:.2f} | {r['road_detail_kept']:.2f} | {r['dry_lockout_change_mean_abs_whole_picture']:.4f} / {r['dry_lockout_change_mean_abs_road']:.4f} | {r['dry_lockout_road_arrives']:.3f}")
json.dump(res, open(P('numbers/fix_candidates_model.json'), 'w'), indent=1)
