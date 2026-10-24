# What this does (plain words): copy of the round 1 look checker's own measuring script (not the tuner's), run again in round 2 on the reference, the BEFORE tile and the AFTER tile. Original: verify_look_after_fixes/round_1/my_measures.py, unchanged except this note.
# What this does (plain words): my own, independent look measures for the slate tiles (reference, before the fixes, after the fixes).
# It does NOT use the tuner's measure_look.py. It measures the paint (how crisp and how stripy), the moss (how many pieces and how big),
# the chips (tan pieces), how plain each slate is inside, the slate shapes (lower edge wobble, corner rounding), moss next to side joints,
# and the relief (from the normal map). It only describes general character; nothing is copied from the reference.
# Use: python3 -I my_measures.py  (prints a table and writes my_measures.json next to this file)
import json
import os
import cv2
import numpy as np

P = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/'
SETS = {
    'reference': P + 'reference/slate/colour.png',
    'before': P + 'recipes/slate_layers/outputs/default_before_look_fixes/colour.png',
    'after': P + 'recipes/slate_layers/outputs/default/colour.png',
}
NORMALS = {
    'reference': P + 'reference/slate/normal.png',
    'before': P + 'recipes/slate_layers/outputs/default_before_look_fixes/normal.png',
    'after': P + 'recipes/slate_layers/outputs/default/normal.png',
}


def components(mask, min_area=1):
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), connectivity=8)
    return count, labels, stats


def slate_labels(grey):
    """slates = lighter than 12/100 after a small shrink, pieces bigger than 5000 dots (a different threshold route than the tuner's: grey, not Lab)."""
    mask = cv2.erode((grey > 30).astype(np.uint8), np.ones((3, 3), np.uint8))   # grey 0..255, 30 is about the same as Lab L 12
    count, labels, stats = components(mask)
    keep = [i for i in range(1, count) if stats[i, cv2.CC_STAT_AREA] > 5000]
    return labels, stats, keep


def measure(name):
    bgr = cv2.imread(SETS[name])
    grey = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY).astype(np.float64)
    out = {}
    # ---- paint: crispness and stripiness with Scharr slopes of plain grey at the native size (the tuner used Lab lightness, Sobel, 900 dots)
    sx = cv2.Scharr(grey, cv2.CV_64F, 1, 0) / 16.0
    sy = cv2.Scharr(grey, cv2.CV_64F, 0, 1) / 16.0
    mag = np.hypot(sx, sy)
    labels, stats, keep = slate_labels(grey)
    inside = np.isin(labels, keep)
    inside = cv2.erode(inside.astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool)   # stay away from the slate rims and joints
    m = mag[inside]
    out['paint_median_slope'] = float(np.median(m))
    out['paint_mean_slope'] = float(m.mean())
    out['paint_flat_share_%'] = float((m < 0.6).mean() * 100)           # dots with almost no slope: flat paint
    out['paint_hard_edge_share_%'] = float((m > 8).mean() * 100)        # dots on a hard step
    out['paint_mid_slope_share_%'] = float(((m >= 0.6) & (m <= 8)).mean() * 100)   # soft blends, ripple, grain
    out['paint_side_over_updown'] = float((sx[inside] ** 2).sum() / (sy[inside] ** 2).sum())
    # edge direction: share of the steep slope energy that comes from edges running within 25 degrees of upright
    angle = np.degrees(np.arctan2(np.abs(sy[inside]), np.abs(sx[inside])))   # 0 = slope points sideways = upright edge
    strong = m > 4
    out['upright_edge_share_%'] = float((angle[strong] < 25).mean() * 100)
    # grain: noise level = median absolute difference of the grey from its 5x5 median-blurred copy, inside slates
    blurred = cv2.medianBlur(grey.astype(np.uint8), 5).astype(np.float64)
    out['fine_grain_noise'] = float(np.median(np.abs(grey - blurred)[inside]))
    # ---- how plain a slate is inside: spread of grey inside each slate (mean over slates) and the share of nearly flat slates
    spreads = []
    means = []
    for i in keep:
        ys, xs = np.where(labels == i)
        shrunk = cv2.erode((labels == i).astype(np.uint8), np.ones((15, 15), np.uint8)).astype(bool)
        if shrunk.sum() < 2000:
            continue
        values = grey[shrunk]
        spreads.append(values.std())
        means.append(values.mean())
    spreads = np.array(spreads)
    means = np.array(means)
    out['slate_inner_spread_mean'] = float(spreads.mean())
    out['slate_inner_spread_min'] = float(spreads.min())
    out['slate_count'] = int(len(spreads))
    out['slate_mean_grey_std'] = float(means.std())
    out['slate_mean_grey_range'] = [float(means.min()), float(means.max())]
    # ---- moss: yellow-green hue from HSV (hue 30..90 in OpenCV's 0..180 means 60..180 degrees? no: OpenCV hue is half degrees; 20..45 = 40..90 degrees)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    hue, sat, val = hsv[..., 0].astype(int), hsv[..., 1].astype(int), hsv[..., 2].astype(int)
    moss = (hue >= 22) & (hue <= 45) & (sat >= 45) & (val >= 40) & (val <= 150)
    moss &= inside | cv2.dilate(inside.astype(np.uint8), np.ones((19, 19), np.uint8)).astype(bool)
    out['moss_share_%'] = float(moss.mean() * 100)
    mm = cv2.morphologyEx(moss.astype(np.uint8), cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    count, lab, st = components(mm)
    areas = st[1:, cv2.CC_STAT_AREA]
    areas = areas[areas >= 12]
    out['moss_pieces'] = int(len(areas))
    out['moss_median_piece'] = float(np.median(areas)) if len(areas) else 0
    big = areas[areas >= 1500]
    out['moss_big_pieces_(>=1500)'] = int(len(big))
    out['moss_share_in_big_pieces_%'] = float(big.sum() / max(1, areas.sum()) * 100)
    out['moss_share_in_small_pieces_(<150)_%'] = float(areas[areas < 150].sum() / max(1, areas.sum()) * 100)
    # thin-ness of moss: mean "thickness" = area / (half the perimeter) is bigger for clouds; use distance transform max per piece
    dist = cv2.distanceTransform(mm, cv2.DIST_L2, 3)
    thick = []
    for i in range(1, count):
        if st[i, cv2.CC_STAT_AREA] >= 60:
            thick.append(dist[lab == i].max())
    out['moss_piece_max_thickness_median'] = float(np.median(thick)) if thick else 0
    out['moss_piece_max_thickness_p90'] = float(np.percentile(thick, 90)) if thick else 0
    # moss next to side joints: share of moss dots that are within 14 dots left or right of a joint (a dark dot at the same height)
    joint = (grey < 30).astype(np.uint8)
    side_reach = cv2.dilate(joint, np.ones((1, 29), np.uint8))   # +-14 dots sideways
    vert_reach = cv2.dilate(joint, np.ones((29, 1), np.uint8))   # +-14 dots up and down
    side_only = (side_reach > 0) & ~(vert_reach > 0)
    out['moss_near_side_joint_%'] = float((moss & side_only).sum() / max(1, moss.sum()) * 100)
    out['moss_near_any_joint_%'] = float((moss & (cv2.dilate(joint, np.ones((29, 29), np.uint8)) > 0)).sum() / max(1, moss.sum()) * 100)
    # ---- chips: warm tan/pink/cream dots (hue 5..22 in OpenCV units = 10..44 degrees), saturation 40..140, bright enough
    tan = (hue >= 5) & (hue <= 22) & (sat >= 35) & (sat <= 160) & (val >= 85)
    out['tan_share_%'] = float(tan.mean() * 100)
    tt = cv2.morphologyEx(tan.astype(np.uint8), cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    count, lab, st = components(tt)
    areas = st[1:, cv2.CC_STAT_AREA]
    out['tan_pieces_(>=10)'] = int((areas >= 10).sum())
    out['tan_largest_piece'] = int(areas.max()) if len(areas) else 0
    out['tan_median_piece'] = float(np.median(areas[areas >= 10])) if (areas >= 10).any() else 0
    out['tan_share_in_pieces_>=300_%'] = float(areas[areas >= 300].sum() / max(1, areas.sum()) * 100)
    # ---- lichen discs: small round pale/warm dots inside slates (area 15..160, roundness > 0.8)
    disc = 0
    for i in range(1, count):
        a = st[i, cv2.CC_STAT_AREA]
        if 15 <= a <= 160:
            w, h = st[i, cv2.CC_STAT_WIDTH], st[i, cv2.CC_STAT_HEIGHT]
            if 0.75 < w / h < 1.33 and a / (w * h) > 0.68:
                cx, cy = st[i, cv2.CC_STAT_LEFT] + w // 2, st[i, cv2.CC_STAT_TOP] + h // 2
                if inside[cy, cx]:
                    disc += 1
    out['round_tan_dots_inside_slates'] = disc
    # ---- slate shape: lower edge wobble and corner rounding for each slate (bottom boundary per column of the slate)
    wob, drop, fill = [], [], []
    for i in keep:
        ys, xs = np.where(labels == i)
        x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
        if (x1 - x0) < 80 or x0 <= 2 or x1 >= grey.shape[1] - 3 or y0 <= 2 or y1 >= grey.shape[0] - 3:
            continue
        sub = labels[y0:y1 + 1, x0:x1 + 1] == i
        bottoms = np.array([np.where(sub[:, c])[0].max() if sub[:, c].any() else np.nan for c in range(sub.shape[1])])
        cols = np.arange(sub.shape[1])
        ok = ~np.isnan(bottoms)
        if ok.sum() < 60:
            continue
        mid = slice(int(len(cols) * 0.15), int(len(cols) * 0.85))
        coef = np.polyfit(cols[mid][ok[mid]], bottoms[mid][ok[mid]], 1)
        resid = bottoms[mid][ok[mid]] - np.polyval(coef, cols[mid][ok[mid]])
        wob.append(resid.std())
        base = np.median(bottoms[mid][ok[mid]])
        edge = np.r_[bottoms[:8], bottoms[-8:]]
        drop.append(float(np.nanmean(base - edge)))        # how much higher the last 8 columns at each side sit than the middle: rounded corners
        fill.append(sub.sum() / sub.size)
    out['slate_lower_edge_wobble'] = float(np.mean(wob))
    out['slate_corner_rise_(rounding)'] = float(np.mean(drop))
    out['slate_fill_of_box'] = float(np.mean(fill))
    out['slates_measured_for_shape'] = len(wob)
    # ---- overall colour
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB).astype(float)
    out['mean_lab'] = [float(lab[..., 0].mean() * 100 / 255), float(lab[..., 1].mean() - 128), float(lab[..., 2].mean() - 128)]
    out['dark_share_(grey<30)_%'] = float((grey < 30).mean() * 100)
    # ---- relief from the normal map (only for the three full tiles; test tiles are colour-only)
    if name not in NORMALS:
        return out
    n = cv2.imread(NORMALS[name])[..., ::-1].astype(float) - 127.5
    out['relief_tilt_p99'] = float(np.percentile(np.hypot(n[..., 0], n[..., 1]), 99))
    out['relief_up_down'] = float(np.abs(n[..., 1]).mean())
    out['relief_side'] = float(np.abs(n[..., 0]).mean())
    out['relief_mean_tilt'] = float(np.hypot(n[..., 0], n[..., 1]).mean())
    return out


if __name__ == '__main__':
    import sys
    for extra in sys.argv[1:]:                      # optional: name=path/to/colour.png for colour-only test tiles
        k, v = extra.split('=', 1)
        SETS[k] = v
    results = {k: measure(k) for k in SETS}
    json_name = 'my_measures.json' if len(sys.argv) == 1 else 'my_measures_with_tests.json'
    keys = [k for k in results['reference'].keys() if all(k in r for r in results.values())]
    print('measure'.ljust(40) + ''.join(k.rjust(14) for k in results))
    for key in keys:
        row = key.ljust(40)
        for k in results:
            v = results[k][key]
            row += (('%.2f' % v) if isinstance(v, float) else (str(v) if not isinstance(v, list) else str([round(x, 1) for x in v]))).rjust(14)
        print(row)
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), json_name), 'w') as handle:
        json.dump(results, handle, indent=1)
