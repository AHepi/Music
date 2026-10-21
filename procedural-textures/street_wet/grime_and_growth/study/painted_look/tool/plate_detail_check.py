#!/usr/bin/env python3
"""plate_detail_check.py  -  "will the painter keep it?"  (plain words: a measuring script for plates; it needs no Blender and no network)

WHAT IT DOES
  Takes a plate (the picture drawn in Blender that the painter repaints) and, optionally, the mask picture of ONE weathering layer (white = where the layer's
  marks are: cracks, stains, moss, weeds, chips ...). For every separate mark it measures
     * width in plate pixels at 1536 wide (the size all the targets are written for),
     * contrast: how much brighter or darker the mark is than the ring of surface around it (picture brightness 0..1, Rec.709 weights),
     * the brightness of the surround (so a dark mark on an already dark surface is flagged: the film's brightness curve crushes it),
  and says how likely the painter is to draw it again (GOOD 80 % or more, RISKY 50 to 80 %, LOST under 50 %), using the fit made from the lined-up plate and
  painting pairs of the street (study 12 'Painted look - what survives the painter'). Without a mask it scans the whole plate for dark and bright marks the same way.
  It writes a JSON report and an overlay picture (green = good, amber = risky, red = lost, blue outline = on a surround darker than 0.12).

USE
  python3 -I plate_detail_check.py PLATE.png [--mask MASK.png] [--painter-scale 0.5] [--surfaces SURFACES.png] [--out report.json] [--overlay overlay.jpg] [--label "cracks"]

  --painter-scale   how big the plate is when it is sent (0.527 was used for the wet tests; 1.0 for the old dry paintings). Under 0.5 the answer is an extrapolation.
  --surfaces        optional mask (white) of ONE surface, e.g. all the wall pixels: the report then adds the share of that surface that is darker than 0.10 and 0.12.
  Needs: python3, numpy, opencv (cv2). Written for plates of any size (they are shrunk or enlarged to 1536 wide for measuring; the aspect is kept).

LIMITS (said once)
  The fit comes from natural marks of the street plates (cracks, stains, specks, joints, rubbish) and 5 plate/painting pairs; it does not know the painter's mood on
  a given day (one draw each), it does not look at colour, and it measures brightness only. Treat GOOD/RISKY/LOST as a guide for sizes, not a promise.
"""
import argparse, json, os, sys
import numpy as np
import cv2

HERE = os.path.dirname(os.path.abspath(__file__))
FIT = json.load(open(os.path.join(HERE, 'painter_survival_fit.json')))
W_STD = 1536

def lum(rgb):  # rgb float 0..1 (R, G, B)
    return 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]

def load_plate(path):
    im = cv2.imread(path, cv2.IMREAD_COLOR)
    if im is None: sys.exit("cannot read " + path)
    k = W_STD / im.shape[1]
    if abs(k - 1) > 1e-3:
        im = cv2.resize(im, (W_STD, int(round(im.shape[0] * k))), interpolation=cv2.INTER_AREA if k < 1 else cv2.INTER_CUBIC)
    return cv2.cvtColor(im, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0, k

def load_mask(path, shape):
    m = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if m is None: sys.exit("cannot read " + path)
    if m.ndim == 3: m = m[..., :3].max(axis=2) if m.shape[2] >= 3 else m[..., 0]
    m = cv2.resize(m, (shape[1], shape[0]), interpolation=cv2.INTER_NEAREST)
    return m > 127

def disc(k): return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))

def retention(width, scale):
    """share of a mark's contrast left in the shrunk picture the painter receives (measured on the round 2 plate: width classes 2.5, 4.5, 8 px)."""
    pts_w = [1.5, 3.5, 6.0, 12.0]
    tab = {0.527: [0.71, 0.82, 0.91, 0.945], 0.45: [0.62, 0.74, 0.885, 0.925], 0.40: [0.555, 0.71, 0.87, 0.92], 0.30: [0.36, 0.545, 0.775, 0.865]}
    xs = sorted(tab)
    def at(s): return np.interp(width, pts_w, tab[s])
    if scale >= xs[-1]: return float(at(xs[-1]) + (1 - at(xs[-1])) * min(1, (scale - xs[-1]) / (1 - xs[-1])))
    if scale <= xs[0]: return float(at(xs[0]))
    lo = max(s for s in xs if s <= scale); hi = min(s for s in xs if s >= scale)
    if lo == hi: return float(at(lo))
    t = (scale - lo) / (hi - lo); return float((1 - t) * at(lo) + t * at(hi))

def p_back(kind, width, contrast, scale):
    """probability that the painting has the mark again. kind: 'speck' or 'line'. width in plate px (1536 wide), contrast 0..1."""
    c = max(contrast, 1e-3); w = max(width, 1.0)
    def logistic(fit, cc):
        b = fit['b']; z = b[0] + b[1] * np.log(w) + b[2] * np.log(cc); return 1 / (1 + np.exp(-z))
    small, full = FIT[f'small|{kind}'], FIT[f'full|{kind}']
    if scale >= 0.99: return float(logistic(full, c))
    if scale >= 0.527:
        t = (scale - 0.527) / (1 - 0.527)
        ls = np.log(logistic(small, c) / (1 - logistic(small, c) + 1e-9) + 1e-9); lf = np.log(logistic(full, c) / (1 - logistic(full, c) + 1e-9) + 1e-9)
        z = (1 - t) * ls + t * lf; return float(1 / (1 + np.exp(-z)))
    # smaller than the wet tests: the contrast that reaches the painter is lower
    return float(logistic(small, c * retention(w, scale) / retention(w, 0.527)))

def find_marks(A, mask=None, region=None, kmax=17, thr=0.03, dark=True, maxarea=4000):
    if mask is not None:
        m = mask.astype(np.uint8)
    else:
        f = (cv2.morphologyEx(A, cv2.MORPH_CLOSE, disc(kmax)) - A) if dark else (A - cv2.morphologyEx(A, cv2.MORPH_OPEN, disc(kmax)))
        m = (f > thr).astype(np.uint8)
        if region is not None: m &= region.astype(np.uint8)
    n, lab, stats, cent = cv2.connectedComponentsWithStats(m, connectivity=8)
    out = []
    for i in range(1, n):
        x, y, w, h, area = stats[i]
        if area < 5: continue
        if mask is None and (area > maxarea or w > 150 or h > 150): continue
        out.append((i, x, y, w, h, area))
    return lab, out, m

def measure(A, lab, items, allmask, margin=14):
    H, W = A.shape; rows = []
    for (i, x, y, w, h, area) in items:
        x0, y0, x1, y1 = max(0, x - margin), max(0, y - margin), min(W, x + w + margin), min(H, y + h + margin)
        comp = (lab[y0:y1, x0:x1] == i)
        cu = comp.astype(np.uint8)
        dt = cv2.distanceTransform(np.pad(cu, 1), cv2.DIST_L2, 3); width = 2 * float(dt.max())
        pts = cv2.findNonZero(cu); (cx, cy), (rw, rh), ang = cv2.minAreaRect(pts); length = max(rw, rh); thick = max(1.0, min(rw, rh))
        rr = max(11, int(round(width * 0.6)) | 1)
        ring = (cv2.dilate(cu, disc(rr)) > 0) & ~(cv2.dilate(cu, disc(3)) > 0) & ~allmask[y0:y1, x0:x1]
        if ring.sum() < 8: continue
        core = comp
        a = A[y0:y1, x0:x1]
        c_core = float(a[core].mean()); c_ring = float(a[ring].mean())
        elong = length / thick
        kind = 'line' if elong >= 4 else 'speck'
        rows.append(dict(x=int(x), y=int(y), w=int(w), h=int(h), width_px=round(width, 1), length_px=round(float(length), 1), elong=round(float(elong), 1),
                         kind=kind, sign='dark' if c_core < c_ring else 'bright', contrast=round(abs(c_ring - c_core), 4), surround=round(c_ring, 3), core=round(c_core, 3)))
    return rows

def verdict(p): return 'GOOD' if p >= 0.8 else ('RISKY' if p >= 0.5 else 'LOST')

def main():
    ap = argparse.ArgumentParser(description="will the painter keep it? (see the top of this file)")
    ap.add_argument('plate'); ap.add_argument('--mask'); ap.add_argument('--surfaces'); ap.add_argument('--painter-scale', type=float, default=0.5)
    ap.add_argument('--out', default='plate_detail_report.json'); ap.add_argument('--overlay', default=None); ap.add_argument('--label', default='marks')
    a = ap.parse_args()
    rgb, k = load_plate(a.plate); A = lum(rgb); H, W = A.shape
    surf = load_mask(a.surfaces, A.shape) if a.surfaces else None
    report = dict(plate=a.plate, label=a.label, painter_scale=a.painter_scale, scaled_to_width=W_STD, plate_scale_factor=round(k, 4), note="widths are plate pixels at 1536 wide")
    if a.painter_scale < 0.5: report['warning'] = "painter scale under 0.5: extrapolated from the 0.53 tests with the measured loss of contrast on shrinking"
    allrows = []
    if a.mask:
        mask = load_mask(a.mask, A.shape)
        lab, items, m = find_marks(A, mask=mask)
        rows = measure(A, lab, items, mask)
        for r in rows: r['source'] = 'mask'
        allrows += rows
    else:
        for dark in (True, False):
            lab, items, m = find_marks(A, region=surf, dark=dark)
            rows = measure(A, lab, items, m > 0)
            for r in rows: r['source'] = 'scan dark' if dark else 'scan bright'
            allrows += rows
    for r in allrows:
        r['p_back'] = round(p_back(r['kind'], r['width_px'], r['contrast'], a.painter_scale), 2)
        r['verdict'] = verdict(r['p_back'])
        r['dark_surround'] = bool(r['surround'] < 0.12 and r['sign'] == 'dark')
    n = len(allrows)
    summ = {v: sum(1 for r in allrows if r['verdict'] == v) for v in ('GOOD', 'RISKY', 'LOST')}
    summ['dark_mark_on_dark_surround'] = sum(1 for r in allrows if r['dark_surround'])
    report['marks'] = n; report['summary'] = summ
    if n:
        report['share_good'] = round(summ['GOOD'] / n, 3); report['share_lost'] = round(summ['LOST'] / n, 3)
        wd = np.array([r['width_px'] for r in allrows]); cn = np.array([r['contrast'] for r in allrows])
        report['width_px_median_p10_p90'] = [round(float(np.median(wd)), 1), round(float(np.percentile(wd, 10)), 1), round(float(np.percentile(wd, 90)), 1)]
        report['contrast_median_p10_p90'] = [round(float(np.median(cn)), 3), round(float(np.percentile(cn, 10)), 3), round(float(np.percentile(cn, 90)), 3)]
    if surf is not None:
        report['surface_share_darker_than'] = {'0.08': round(float((A[surf] < 0.08).mean()), 3), '0.10': round(float((A[surf] < 0.10).mean()), 3), '0.12': round(float((A[surf] < 0.12).mean()), 3),
                                               'note': "0.10 = black on the film; 0.12 = about 0.05 on the film (study 12, section 6)"}
    report['details'] = allrows[:2000]
    json.dump(report, open(a.out, 'w'), indent=1)
    print(json.dumps({k_: v for k_, v in report.items() if k_ != 'details'}, indent=1))
    if a.overlay:
        base = (np.clip(rgb * 0.55, 0, 1) * 255).astype(np.uint8)
        ov = cv2.cvtColor(base, cv2.COLOR_RGB2BGR)
        col = {'GOOD': (60, 200, 60), 'RISKY': (40, 170, 240), 'LOST': (50, 50, 230)}
        for r in allrows:
            x, y, w, h = r['x'], r['y'], r['w'], r['h']
            cv2.rectangle(ov, (x - 2, y - 2), (x + w + 2, y + h + 2), col[r['verdict']], 1)
            if r['dark_surround']: cv2.rectangle(ov, (x - 4, y - 4), (x + w + 4, y + h + 4), (230, 120, 30), 1)
        s = 1200 / ov.shape[1]
        if s < 1: ov = cv2.resize(ov, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
        cv2.imwrite(a.overlay, ov, [cv2.IMWRITE_JPEG_QUALITY, 85])
if __name__ == '__main__':
    main()
