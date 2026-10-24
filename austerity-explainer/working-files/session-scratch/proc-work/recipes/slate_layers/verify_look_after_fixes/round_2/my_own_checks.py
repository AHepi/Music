# What this does (plain words): my own second set of measurements for round 2, written fresh (not the tuner's script and not the round 1
# checker's script), on the reference, the BEFORE tile and the AFTER tile. It uses other colour rules (Lab and Rec.709 grey instead of HSV
# and Rec.601 grey) and other ways of finding slates and joints, so it is a real cross-check:
#   1  slate-to-slate spread of lightness (median per slate) and number of far-off slates   -> problem 7 (pale/dark outliers)
#   2  moss dots near the side joints                                                      -> problem 11
#   3  where the moss sits from the top to the bottom of its slate (hanging from the top?)  -> problem 2
#   4  chips: tan pieces, their width (chunky or thin), and how much of the chip colour sits on the lower rim -> problem 3
#   5  lower rim colour (pale grey lip or orange-pink line) and fine-scale roughness of the lower edge       -> problems 3, 4
# Use: python3 -I my_own_checks.py   (prints a table and writes my_own_checks.json next to this file)
import json
import os
import cv2
import numpy as np

P = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/'
SETS = {'reference': P + 'reference/slate/colour.png',
        'before': P + 'recipes/slate_layers/outputs/default_before_look_fixes/colour.png',
        'after': P + 'recipes/slate_layers/outputs/default/colour.png'}


def lab_planes(rgb):
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float64)
    return lab[..., 0] * 100.0 / 255.0, lab[..., 1] - 128.0, lab[..., 2] - 128.0


def slates_of(light):
    """slate faces: lighter than L 9, opened by a 7-dot square, pieces over 4000 dots"""
    mask = (light > 9).astype(np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask, connectivity=4)
    keep = [i for i in range(1, count) if stats[i, cv2.CC_STAT_AREA] > 4000]
    return labels, stats, keep


def measure(name):
    rgb = cv2.cvtColor(cv2.imread(SETS[name]), cv2.COLOR_BGR2RGB)
    rgbf = rgb.astype(np.float64)
    luma = 0.2126 * rgbf[..., 0] + 0.7152 * rgbf[..., 1] + 0.0722 * rgbf[..., 2]   # Rec.709 grey, 0..255
    light, a, b = lab_planes(rgb)
    labels, stats, keep = slates_of(light)
    out = {}
    # ---- 1: slate-to-slate spread
    medians, ids = [], []
    for i in keep:
        face = cv2.erode((labels == i).astype(np.uint8), np.ones((17, 17), np.uint8)).astype(bool)
        if face.sum() < 1500:
            continue
        medians.append(np.median(luma[face]))
        ids.append(i)
    medians = np.array(medians)
    centre = np.median(medians)
    out['slates_found'] = len(medians)
    out['slate_median_luma_spread_std'] = float(medians.std())
    out['slate_median_luma_range'] = [float(medians.min()), float(medians.max())]
    out['slates_more_than_12_off_middle'] = int((np.abs(medians - centre) > 12).sum())
    out['slates_more_than_8_off_middle'] = int((np.abs(medians - centre) > 8).sum())
    out['slates_pale_(more_than_10_above)'] = int((medians - centre > 10).sum())
    # ---- joints: vertical joints = dark dots (luma < 22) that sit in a vertical dark run of 40+ dots
    dark = (luma < 22).astype(np.uint8)
    run = cv2.morphologyEx(dark, cv2.MORPH_OPEN, np.ones((40, 1), np.uint8))
    side_joint = cv2.dilate(run, np.ones((1, 29), np.uint8)) > 0      # within 14 dots left or right of a vertical dark run
    # ---- 2 and 3: moss by Lab rule (yellow-olive: b* above 5, a* below 2, lightness 10..45), on slate faces only
    slate_any = np.isin(labels, keep)
    moss = (b > 5) & (a < 2) & (light > 10) & (light < 45) & slate_any
    moss &= (cv2.erode(slate_any.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0)
    out['moss_share_%_of_slate_dots'] = float(moss.sum() / slate_any.sum() * 100)
    out['moss_dots_within_14_of_a_side_joint_%'] = float((moss & side_joint).sum() / max(1, moss.sum()) * 100)
    out['all_slate_dots_within_14_of_a_side_joint_%'] = float((slate_any & side_joint).sum() / slate_any.sum() * 100)
    # height of the moss within its slate: 0 = top edge, 1 = bottom edge; share of moss in the top 25 % and bottom 25 %
    top25 = bot25 = total = 0
    hist = np.zeros(10)
    for i in ids:
        ys, xs = np.where(labels == i)
        y0, y1 = ys.min(), ys.max()
        if y1 - y0 < 60:
            continue
        sel = moss[y0:y1 + 1, xs.min():xs.max() + 1] & (labels[y0:y1 + 1, xs.min():xs.max() + 1] == i)
        rows = sel.sum(axis=1).astype(float)
        frac = (np.arange(len(rows)) / max(1, len(rows) - 1))
        for k in range(10):
            hist[k] += rows[(frac >= k / 10) & (frac < (k + 1) / 10 + (1e-9 if k == 9 else 0))].sum()
    hist = hist / max(1, hist.sum()) * 100
    out['moss_by_height_tenths_top_to_bottom_%'] = [round(float(h), 1) for h in hist]
    out['moss_in_top_third_%'] = float(hist[:3].sum())
    # ---- 4: chips = warm pale dots: a* above 1.5, b* above 7, lightness above 38 (cream, tan, pink)
    chip = (a > 1.5) & (b > 7) & (light > 38)
    chip = cv2.morphologyEx(chip.astype(np.uint8), cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    count, lab_c, st, _ = cv2.connectedComponentsWithStats(chip, connectivity=8)
    areas = st[1:, cv2.CC_STAT_AREA]
    out['chip_share_%'] = float(chip.mean() * 100)
    out['chip_pieces_(area>=8)'] = int((areas >= 8).sum())
    dist = cv2.distanceTransform(chip, cv2.DIST_L2, 3)
    widths = []
    for k in range(1, count):
        if st[k, cv2.CC_STAT_AREA] >= 8:
            widths.append(2 * dist[lab_c == k].max())
    widths = np.array(widths)
    out['chip_piece_width_median'] = float(np.median(widths))
    out['chip_pieces_with_width>=7_%_of_pieces'] = float((widths >= 7).mean() * 100)
    big_area = sum(st[k, cv2.CC_STAT_AREA] for k in range(1, count) if st[k, cv2.CC_STAT_AREA] >= 8 and 2 * dist[lab_c == k].max() >= 7)
    out['chip_area_in_chunky_pieces_(width>=7)_%'] = float(big_area / max(1, areas[areas >= 8].sum()) * 100)
    # ---- 5: the lower rim of each slate: take, per column, the lowest slate dot, and the 6 dots above it
    rim_l, rim_a, rim_b, rim_chip = [], [], [], []
    rough_fine, rough_mid, corner = [], [], []
    for i in ids:
        ys, xs = np.where(labels == i)
        x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
        if (x1 - x0) < 100 or x0 <= 2 or x1 >= rgb.shape[1] - 3 or y0 <= 2 or y1 >= rgb.shape[0] - 3:
            continue
        sub = labels[y0:y1 + 1, x0:x1 + 1] == i
        bottoms = np.array([np.where(sub[:, c])[0].max() if sub[:, c].any() else -1 for c in range(sub.shape[1])])
        if (bottoms < 0).any():
            continue
        cols = np.arange(sub.shape[1])
        for c in range(int(len(cols) * 0.15), int(len(cols) * 0.85)):
            yb = y0 + bottoms[c]
            for d in range(1, 7):
                yy = yb - d
                rim_l.append(light[yy, x0 + c]); rim_a.append(a[yy, x0 + c]); rim_b.append(b[yy, x0 + c])
                rim_chip.append(bool(chip[yy, x0 + c]))
        # fine roughness: bottom edge minus its 15-dot running median; mid: the 15-dot running median minus the straight-line fit
        mid_cols = slice(int(len(cols) * 0.15), int(len(cols) * 0.85))
        b_f = bottoms.astype(float)
        run_med = np.array([np.median(b_f[max(0, c - 7):c + 8]) for c in range(len(b_f))])
        rough_fine.append(float(np.std((b_f - run_med)[mid_cols])))
        coef = np.polyfit(cols[mid_cols], run_med[mid_cols], 1)
        rough_mid.append(float(np.std(run_med[mid_cols] - np.polyval(coef, cols[mid_cols]))))
        corner.append(float(np.median(b_f[mid_cols]) - np.mean(np.r_[b_f[:8], b_f[-8:]])))
    out['lower_rim_mean_lightness'] = float(np.mean(rim_l))
    out['lower_rim_mean_a*_b*'] = [float(np.mean(rim_a)), float(np.mean(rim_b))]
    out['lower_rim_share_chip_coloured_%'] = float(np.mean(rim_chip) * 100)
    out['lower_edge_fine_roughness_(under 15 dots)'] = float(np.mean(rough_fine))
    out['lower_edge_mid_wobble_(15+ dots)'] = float(np.mean(rough_mid))
    out['corner_rise_(own)'] = float(np.mean(corner))
    out['slates_measured_for_shape'] = len(rough_fine)
    return out


if __name__ == '__main__':
    results = {k: measure(k) for k in SETS}
    keys = list(results['reference'].keys())
    print('measure'.ljust(50) + ''.join(k.rjust(26) for k in results))
    for key in keys:
        row = key.ljust(50)
        for k in results:
            v = results[k][key]
            if isinstance(v, list):
                s = str([round(x, 1) for x in v])
            elif isinstance(v, float):
                s = '%.2f' % v
            else:
                s = str(v)
            row += s.rjust(26)
        print(row)
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'my_own_checks.json'), 'w') as handle:
        json.dump(results, handle, indent=1)
