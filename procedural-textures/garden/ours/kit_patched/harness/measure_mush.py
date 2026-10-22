# What this file does (plain words)
# ---------------------------------------------------------------------------------------------------------------------------------------------
# P5 (the set is not turned into one dark mush). On a plate picture, per surface class (the set's test_set.classes: walls, trims, road, pavement, kerb and gutter, iron,
# roofs ...), against the baseline plate of the same camera:
#   M1  share of the class's dots darkened by a third or more (kit brightness <= 2/3 of base brightness, on dots the base holds at least 0.03)      at most 25 %
#   M2  share of the class under plate brightness 0.10: rise in points (road and pavement 8, walls and trims 3)
#   M3  class mean brightness drop (at most 12 %), the whole plate's (at most 8 %)
#   M4  spread inside the class (90th over 10th percentile of brightness, 10th floored at 0.01) kept at 85 % or more of base's
#   M5  distance bands 5 to 10, 10 to 20, 20 to 40 m: kit / base mean brightness of the class in each band between 0.80 and 1.00, bands differing by at most 0.08
# The class picture and the depth picture (see testset.py) are drawn once for the baseline and stored small (class as a role number per dot, depth in 0.25 m steps) so that a
# later picture is cut up by exactly the same dots. stats(...) gives the numbers of ONE plate (what the baseline freezes); compare(...) is the pass test.
# Use:   python3 -I measure_mush.py SET_ID KIT_FOLDER BASE_FOLDER PLATE_NAME [--maps MAPS_DIR]      (plate name e.g. plate_main_A_wet)
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import measure_common as mc  # noqa: E402

BANDS = [(5, 10), (10, 20), (20, 40)]
LIMITS = dict(m1_share=0.25, m2_points={'road': 0.08, 'pavement': 0.08, 'walls': 0.03, 'trims': 0.03}, m2_default=0.08, m3_class=0.12, m3_plate=0.08, m4_keep=0.85, m5_low=0.80, m5_high=1.00, m5_step=0.08)


def save_maps(class_png, depth_png, dest_dir, name):
    """Stores the class picture as a role number per dot (8 bit PNG) and the depth picture as metres * 4 (8 bit, up to 63.75 m)."""
    os.makedirs(dest_dir, exist_ok=True)
    cmap = mc.read_class(class_png).astype(np.uint8)
    depth = np.clip(np.rint(mc.read_depth(depth_png) * 4.0), 0, 255).astype(np.uint8)
    cv2.imwrite(os.path.join(dest_dir, f'class_{name}.png'), cmap, [cv2.IMWRITE_PNG_COMPRESSION, 9])
    cv2.imwrite(os.path.join(dest_dir, f'depth_{name}.png'), depth, [cv2.IMWRITE_PNG_COMPRESSION, 9])


def load_maps(dest_dir, name):
    cmap = cv2.imread(os.path.join(dest_dir, f'class_{name}.png'), cv2.IMREAD_UNCHANGED).astype(np.int16)
    depth = cv2.imread(os.path.join(dest_dir, f'depth_{name}.png'), cv2.IMREAD_UNCHANGED).astype(np.float32) / 4.0
    return cmap, depth


def stats(L, cmap, depth, classes):
    """The numbers of one plate for each class: dots, mean, share under 0.10, 10th and 90th percentile, mean in each distance band; and the whole plate's mean."""
    out = {'plate_mean': round(float(L.mean()), 5), 'classes': {}}
    for cname, ids in classes.items():
        m = mc.class_mask(cmap, ids)
        if m.sum() < 50:
            continue
        v = L[m]
        entry = dict(dots=int(m.sum()), mean=round(float(v.mean()), 5), share_under_010=round(float((v < 0.10).mean()), 5), p10=round(float(np.percentile(v, 10)), 5), p90=round(float(np.percentile(v, 90)), 5), bands={})
        for lo, hi in BANDS:
            b = m & (depth >= lo) & (depth < hi)
            entry['bands'][f'{lo}-{hi}'] = dict(dots=int(b.sum()), mean=round(float(L[b].mean()), 5) if b.sum() >= 50 else None)
        out['classes'][cname] = entry
    return out


def compare(L_kit, L_base, cmap, depth, classes):
    """M1 to M5 of the kit plate against the base plate (same dots). Returns dict(per class numbers, 'ok', 'failures')."""
    s_kit, s_base = stats(L_kit, cmap, depth, classes), stats(L_base, cmap, depth, classes)
    result = {'classes': {}, 'failures': [], 'plate_mean_ratio': round(s_kit['plate_mean'] / max(1e-6, s_base['plate_mean']), 4)}
    if result['plate_mean_ratio'] < 1 - LIMITS['m3_plate']:
        result['failures'].append(f'M3 whole plate brightness ratio {result["plate_mean_ratio"]:.3f} below {1 - LIMITS["m3_plate"]:.2f}')
    for cname, b in s_base['classes'].items():
        k = s_kit['classes'][cname]
        m = mc.class_mask(cmap, classes[cname])
        dark = m & (L_base > 0.03)
        m1 = float((L_kit[dark] <= (2.0 / 3.0) * L_base[dark]).mean()) if dark.any() else 0.0
        m2 = k['share_under_010'] - b['share_under_010']
        m3 = k['mean'] / max(1e-6, b['mean'])
        spread = lambda e: e['p90'] / max(0.01, e['p10'])   # noqa: E731
        m4 = spread(k) / max(1e-6, spread(b))
        ratios = {}
        for band, kb in k['bands'].items():
            bb = b['bands'][band]
            ratios[band] = round(kb['mean'] / bb['mean'], 4) if kb['mean'] is not None and bb['mean'] else None
        entry = dict(m1_darkened_third=round(m1, 4), m2_under_010_rise=round(m2, 4), m3_mean_ratio=round(m3, 4), m4_spread_ratio=round(m4, 4), m5_band_ratios=ratios, base=b, kit=k)
        fails = []
        if m1 > LIMITS['m1_share']:
            fails.append(f'M1 {cname}: {m1:.1%} of dots darkened by a third (limit 25 %)')
        limit2 = LIMITS['m2_points'].get(cname, LIMITS['m2_default'])
        if m2 > limit2:
            fails.append(f'M2 {cname}: share under 0.10 rose {m2 * 100:.1f} points (limit {limit2 * 100:.0f})')
        if m3 < 1 - LIMITS['m3_class']:
            fails.append(f'M3 {cname}: mean brightness ratio {m3:.3f} (limit {1 - LIMITS["m3_class"]:.2f})')
        if m4 < LIMITS['m4_keep']:
            fails.append(f'M4 {cname}: spread kept {m4:.2f} (limit {LIMITS["m4_keep"]})')
        vals = [v for v in ratios.values() if v is not None]
        if any(v < LIMITS['m5_low'] or v > LIMITS['m5_high'] + 1e-6 for v in vals):
            fails.append(f'M5 {cname}: band ratios {ratios} outside 0.80 to 1.00')
        if len(vals) > 1 and max(abs(a - b2) for a, b2 in zip(vals, vals[1:])) > LIMITS['m5_step']:
            fails.append(f'M5 {cname}: band ratios {ratios} differ by more than 0.08 from band to band')
        entry['failures'] = fails
        result['failures'] += fails
        result['classes'][cname] = entry
    result['ok'] = not result['failures']
    return result


def plate_stats_from_folder(settings, folder, plate_name, maps_dir=None):
    """Stats of a drawn plate (folder holds <plate_name>.png and class_/depth_ pictures of its camera and size), or from stored maps."""
    camera = next(c for c, light, state, scene_id, w_, h_ in mc.plate_list(settings) if f'plate_{c}_{light}_{state}' == plate_name)
    cam_info = mc.info(folder, plate_name)
    w, h = cam_info['size'][:2]
    L = mc.read_lum(mc.pic(folder, plate_name))
    cp, dp = mc.pic(folder, f'class_{camera}_{w}x{h}'), mc.pic(folder, f'depth_{camera}_{w}x{h}')
    if cp and dp:
        cmap, depth = mc.read_class(cp), mc.read_depth(dp)
    else:
        cmap, depth = load_maps(maps_dir, f'{camera}_{w}x{h}')
    return stats(L, cmap, depth, mc.classes(settings)), (L, cmap, depth)


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    settings = mc.load_set(args[0])
    kit_folder, base_folder, plate = args[1], args[2], args[3]
    maps_dir = sys.argv[sys.argv.index('--maps') + 1] if '--maps' in sys.argv else None
    if maps_dir and maps_dir in args:
        args.remove(maps_dir)
    kit_stats, (Lk, cmap, depth) = plate_stats_from_folder(settings, kit_folder, plate, maps_dir)
    base_stats, (Lb, _, _) = plate_stats_from_folder(settings, base_folder, plate, maps_dir)
    result = compare(Lk, Lb, cmap, depth, mc.classes(settings))
    print(mc.json.dumps({k: v for k, v in result.items() if k != 'classes'}, indent=1))
