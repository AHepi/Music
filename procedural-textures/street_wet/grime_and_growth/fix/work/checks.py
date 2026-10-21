# Fix round: the three checks the two checkers asked to be run again (mush per class, plant brightness and puddle share, joint contrast) plus the walls' colour and the steps' colour.
# They work on the full-size plate pictures (PNG or JPG), kit against the earlier layers alone ('base'), exactly as the checkers did (check/meas_A..E.py), so the numbers can be put next to theirs.
#   python3 -I checks.py AFTER_PLATE_DIR [--before-kit integrated|DIR] [--ext png|jpg]
import json
import os
import sys

K = 'proc-work/'
KIT = K + 'kits/weathering'
sys.path.insert(0, KIT)
sys.path.insert(0, KIT + '/harness')
sys.dont_write_bytecode = True
import cv2  # noqa: E402
import numpy as np  # noqa: E402
import measure_common as mc  # noqa: E402

B = KIT + '/harness/baseline/maps/'
INTEGRATED = K + 'street_wet/grime_and_growth/integrated/plates/'
SETTINGS = mc.load_set('pit_village_street')
CLASSES = mc.classes(SETTINGS)
BASE_EXT = 'png'     # the extension of the 'base' pictures: png for the final PNG round; jpg when after and before are JPGs (the runner's JPGs are tone-mapped a second time, so they must only be compared with JPGs)
PLATES = [('street', 'main', 'final_main_A_dry', 'dry'), ('street', 'main', 'final_main_A_wet', 'wet'),
          ('lockout', 'lockout', 'final_lockout_B_dry', 'dry'), ('lockout', 'lockout', 'final_lockout_B_wet', 'wet')]


def have(root, scene, name, ext):
    return os.path.exists(pic(root, scene, name, 'kit', ext))


def rgb(path, size=None):
    a = mc.read_rgb(path)
    return a if size is None else cv2.resize(a, size, interpolation=cv2.INTER_AREA)


def pic(root, scene, name, kind, ext):
    p = os.path.join(root, scene, f'{name}_{kind}.{ext}')
    if not os.path.exists(p):
        alt = 'jpg' if ext == 'png' else 'png'
        p = os.path.join(root, scene, f'{name}_{kind}.{alt}')
    return p


def mush(after_root, ext, before_root=INTEGRATED, before_ext='png'):
    """Per surface class: kit/base mean brightness, share darkened by a third, share under 0.10 (base, before-the-fix kit, after-the-fix kit); 540 x 960 pictures."""
    out = {}
    for scene, camera, name, state in PLATES:
        if not have(after_root, scene, name, ext):
            continue
        cmap = mc.read_class(B + f'class_{camera}_540x960.png')
        base = mc.lum(rgb(pic(INTEGRATED, scene, name, 'base', BASE_EXT), (540, 960)))
        old = mc.lum(rgb(pic(before_root, scene, name, 'kit', before_ext), (540, 960)))
        new = mc.lum(rgb(pic(after_root, scene, name, 'kit', ext), (540, 960)))
        res = {'plate_mean_ratio_before': round(float(old.mean() / base.mean()), 4), 'plate_mean_ratio_after': round(float(new.mean() / base.mean()), 4)}
        for c, ids in CLASSES.items():
            m = mc.class_mask(cmap, ids)
            if m.sum() < 200:
                continue
            b, o, n = base[m], old[m], new[m]
            sel = b >= 0.03
            res[c] = dict(n=int(m.sum()), mean_ratio_before=round(float(o.mean() / b.mean()), 3), mean_ratio_after=round(float(n.mean() / b.mean()), 3),
                          darkened_third_before=round(float(((o <= 2 / 3 * b) & sel).sum() / max(1, sel.sum())), 3), darkened_third_after=round(float(((n <= 2 / 3 * b) & sel).sum() / max(1, sel.sum())), 3),
                          under010_base=round(float((b < 0.10).mean()), 3), under010_before=round(float((o < 0.10).mean()), 3), under010_after=round(float((n < 0.10).mean()), 3))
        out[f'{scene}_{state}'] = res
    return out


def plants(after_root, ext, before_root=INTEGRATED, before_ext='png'):
    """Green plant dots (green clearly over red and blue, saturated, changed against base) in the ground part of the plate: brightness of the plant against the ring round it."""
    out = {}
    for scene, camera, name, state in PLATES:
        if not have(after_root, scene, name, ext):
            continue
        base = rgb(pic(INTEGRATED, scene, name, 'base', BASE_EXT))
        row = {}
        for tag, root, e in (('before', before_root, before_ext), ('after', after_root, ext)):
            k = rgb(pic(root, scene, name, 'kit', e))
            hsv = cv2.cvtColor((k * 255).astype(np.uint8), cv2.COLOR_RGB2HSV_FULL).astype(np.float32)
            H, S, V = hsv[..., 0] / 255 * 360, hsv[..., 1] / 255, hsv[..., 2] / 255
            d = np.abs(k - base).max(axis=2)
            green = (k[..., 1] > k[..., 0] * 1.08) & (k[..., 1] > k[..., 2] * 1.15) & (S > 0.3) & (d > 0.04) & (H > 60) & (H < 170)
            h = k.shape[0]
            ground = np.zeros_like(green)
            ground[int(h * 0.55):] = True
            g = green & ground
            r = dict(green_dots=int(g.sum()))
            if g.sum() > 50:
                Lk = mc.lum(k)
                Lb = mc.lum(base)
                m = g.astype(np.uint8)
                ring = cv2.dilate(m, np.ones((15, 15), np.uint8)) - cv2.dilate(m, np.ones((5, 5), np.uint8))
                r.update(H_med=round(float(np.median(H[g])), 1), S_med=round(float(np.median(S[g])), 3), V_med=round(float(np.median(V[g])), 3), V_p90=round(float(np.percentile(V[g], 0.9 * 100)), 3),
                         plant_lum_med=round(float(np.median(Lk[g])), 3), ring_lum_med=round(float(np.median(Lb[ring > 0])), 3), plant_over_ring=round(float(np.median(Lk[g]) / np.median(Lb[ring > 0])), 2),
                         share_V_over_045=round(float((V[g] > 0.45).mean()), 3), share_S_over_06=round(float((S[g] > 0.6).mean()), 3))
            row[tag] = r
        out[f'{scene}_{state}'] = row
    return out


def puddle_share(after_root, ext, before_root=INTEGRATED, before_ext='png'):
    """Share of plant blobs (green blobs of 25 dots or more) whose centre lies inside a puddle of the earlier water layer (the puddle picture drawn with the base look), wet plates."""
    out = {}
    for scene, camera, name, state in PLATES:
        if not have(after_root, scene, name, ext):
            continue
        if state != 'wet':
            continue
        label = 'main' if scene == 'street' else 'lockout'
        row = {}
        for tag, root, e in (('before', before_root, before_ext), ('after', after_root, ext)):
            base = rgb(pic(INTEGRATED, scene, name, 'base', BASE_EXT))
            k = rgb(pic(root, scene, name, 'kit', e))
            h, w = k.shape[:2]
            hsv = cv2.cvtColor((k * 255).astype(np.uint8), cv2.COLOR_RGB2HSV_FULL).astype(np.float32)
            H, S = hsv[..., 0] / 255 * 360, hsv[..., 1] / 255
            d = np.abs(k - base).max(axis=2)
            green = (k[..., 1] > k[..., 0] * 1.08) & (k[..., 1] > k[..., 2] * 1.15) & (S > 0.3) & (d > 0.04) & (H > 60) & (H < 170)
            green[:int(h * 0.55)] = False
            pud = cv2.imread(B + f'puddle_{label}_wet.png', cv2.IMREAD_UNCHANGED)[..., 2] > 32768
            pud = cv2.resize(pud.astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST) > 0
            n, lab, stats, cent = cv2.connectedComponentsWithStats(green.astype(np.uint8), connectivity=8)
            blobs = [(stats[i, 4], cent[i]) for i in range(1, n) if stats[i, 4] >= 25]
            inside = sum(1 for a, c in blobs if pud[min(h - 1, int(c[1])), min(w - 1, int(c[0]))])
            ground = np.zeros((h, w), bool)
            ground[int(h * 0.55):] = True
            row[tag] = dict(plants=len(blobs), in_puddle=inside, share=round(inside / max(len(blobs), 1), 3), green_dots_in_puddle=round(float((green & pud).sum() / max(green.sum(), 1)), 3),
                            puddle_share_of_ground=round(float(pud[ground].mean()), 3))
        out[f'{scene}_{state}'] = row
    return out


def joints(after_root, ext, before_root=INTEGRATED, before_ext='png'):
    """Joint contrast (1 - joint / sett mean luminance) in three bands of the main plate at 540 x 960, puddle dots left out in the wet picture (the checker's meas_D)."""
    W, H = 540, 960
    jm = cv2.imread(B + 'jmask_main_540x960.png', cv2.IMREAD_UNCHANGED).astype(np.float32) / 65535
    pud = cv2.imread(B + 'puddle_main_wet.png', cv2.IMREAD_UNCHANGED)[..., 2] > 32768
    joint = jm[..., 2] > 0.5
    sett = (jm[..., 1] > 0.5) & ~joint
    res = {}
    for st in ('dry', 'wet'):
        name = f'final_main_A_{st}'
        Lb = mc.lum(rgb(pic(INTEGRATED, 'street', name, 'base', BASE_EXT), (W, H)))
        Lo = mc.lum(rgb(pic(before_root, 'street', name, 'kit', before_ext), (W, H)))
        Ln = mc.lum(rgb(pic(after_root, 'street', name, 'kit', ext), (W, H)))
        ok = ~pud if st == 'wet' else np.ones_like(pud)
        for band, (y0, y1) in {'near rows 800-960': (800, 960), 'mid rows 700-800': (700, 800), 'far rows 600-700': (600, 700)}.items():
            mm = np.zeros_like(ok)
            mm[y0:y1] = True
            j, s = joint & mm & ok, sett & mm & ok
            if j.sum() < 30 or s.sum() < 30:
                continue
            cb = 1 - Lb[j].mean() / Lb[s].mean()
            co = 1 - Lo[j].mean() / Lo[s].mean()
            cn = 1 - Ln[j].mean() / Ln[s].mean()
            res[f'{st} {band}'] = dict(base=round(float(cb), 3), before=round(float(co), 3), after=round(float(cn), 3), after_over_base=round(float(cn / cb), 3))
    return res


def walls_colour(after_root, ext, before_root=INTEGRATED, before_ext='png'):
    """Red-to-blue ratio of the wall class on the left half and the right half of the plate (base, before, after), the share of wall dots lifted more than 1.6 times above base
    (pale panels) and the share darkened by a third; 540 x 960 pictures."""
    out = {}
    for scene, camera, name, state in PLATES:
        if not have(after_root, scene, name, ext):
            continue
        cmap = mc.read_class(B + f'class_{camera}_540x960.png')
        base = rgb(pic(INTEGRATED, scene, name, 'base', BASE_EXT), (540, 960))
        old = rgb(pic(before_root, scene, name, 'kit', before_ext), (540, 960))
        new = rgb(pic(after_root, scene, name, 'kit', ext), (540, 960))
        res = {}
        for cname in ('walls', 'trims'):
            m = mc.class_mask(cmap, CLASSES[cname])
            for side, sl in (('left', slice(0, 270)), ('right', slice(270, 540))):
                mm = np.zeros_like(m)
                mm[:, sl] = m[:, sl]
                mm[:int(960 * 0.12)] = False
                if mm.sum() < 300:
                    continue

                def rb(a):
                    return float(a[..., 0][mm].mean() / max(a[..., 2][mm].mean(), 1e-4))
                Lb, Lo, Ln = mc.lum(base), mc.lum(old), mc.lum(new)
                res[f'{cname}_{side}'] = dict(n=int(mm.sum()), r_over_b_base=round(rb(base), 3), r_over_b_before=round(rb(old), 3), r_over_b_after=round(rb(new), 3),
                                             pale_before=round(float(((Lo > 1.6 * Lb + 0.01) & mm).sum() / mm.sum()), 3), pale_after=round(float(((Ln > 1.6 * Lb + 0.01) & mm).sum() / mm.sum()), 3),
                                             lum_ratio_before=round(float(Lo[mm].mean() / Lb[mm].mean()), 3), lum_ratio_after=round(float(Ln[mm].mean() / Lb[mm].mean()), 3))
        out[f'{scene}_{state}'] = res
    return out


def run(after_root, ext='png', before_root=INTEGRATED, before_ext='png', only=None):
    global BASE_EXT
    BASE_EXT = ext if ext == before_ext else ('jpg' if 'jpg' in (ext, before_ext) else 'png')
    out = {}
    for name, fn in (('mush', mush), ('plants', plants), ('puddles', puddle_share), ('joints', joints), ('walls_colour', walls_colour)):
        if only and name not in only:
            continue
        try:
            out[name] = fn(after_root, ext, before_root, before_ext)
        except FileNotFoundError as e:
            out[name] = dict(missing=str(e))
    return out


if __name__ == '__main__':
    after = sys.argv[1]
    ext = sys.argv[sys.argv.index('--ext') + 1] if '--ext' in sys.argv else 'png'
    res = run(after, ext, before_ext=ext, only=(sys.argv[sys.argv.index('--only') + 1].split(',') if '--only' in sys.argv else None))
    print(json.dumps(res, indent=1))
