# What this does (plain words): measures the "look" numbers the look checker used (verify_look/LOOK_VERDICT.md), so the look fixes can be
# judged the same way before and after. It only MEASURES the general character of a picture; it copies nothing from the reference.
#
# For each folder (a bake with colour.png and height.png, and/or normal.png) or the word "reference", it prints:
#   colour, at 900 dots (the picture is shrunk to 900 x 900 if it is bigger):
#     gradient      median colour gradient: how busy the fine texture is (lightness 0..100, 3 x 3 Sobel slope, median over all dots)
#     stripiness    side-to-side over up-down gradient energy: above 1 = more upright stripes than level edges
#     olive %       share of olive (moss-like) dots: Lab b* above 6 and a* below 1
#     tan %         share of tan (chip-like) dots: Lab b* above 6, a* above 0, lightness above 30
#     moss spread   lightness spread (standard deviation) inside the olive dots: low = a flat khaki stain, high = mottled moss
#   at 1254 dots (the picture is scaled to 1254 if it is another size):
#     moss clump    the largest olive clump in dots (olive dots closed with a 5 x 5 round brush, joined to their 8 neighbours)
#     brightest slate   mean lightness of the lightest slate (slates = dots lighter than 12, shrunk by one dot, pieces over 5000 dots)
#     slate spread      the spread of the slate mean lightnesses
#   relief (from the normal map; when the folder has a height.png the normal is made from it the reference's way, Sobel strength 7, with the
#   strength scaled by size / 1254 so a smaller bake reads in the same units):
#     tilt p99      99th percentile of the normal's tilt, in steps of 255 (how steep the steepest 1 % of the surface is)
#     up-down slope   average |green - 128|: slopes that face up or down the picture (level edges: rims, lips, row bands)
#     side slope      average |red - 128|: slopes that face left or right (upright edges: streak outlines, side joints)
#
# Calibration (run 20 October): see "notes - look fixes round 15.md". Use:
#   python3 -I measure_look.py reference FOLDER [FOLDER ...] [--json OUT.json] [--normal-file normal.png]
#   "reference@900" = the reference with its relief measured the way a 900-dot bake is (height shrunk to 900, normal made from it).
import json
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(HERE, '..', 'integration'))
import make_normal  # noqa: E402

REFERENCE = os.path.join(PROC, 'reference', 'slate')


def lab_of(picture):
    lab = cv2.cvtColor(picture, cv2.COLOR_BGR2LAB).astype(np.float64)
    return lab[..., 0] * 100.0 / 255.0, lab[..., 1] - 128.0, lab[..., 2] - 128.0


def resized(picture, size, smooth=True):
    if picture.shape[0] == size:
        return picture
    shrink = picture.shape[0] > size
    return cv2.resize(picture, (size, size), interpolation=cv2.INTER_AREA if shrink else cv2.INTER_LINEAR)


def colour_measures(colour):
    out = {}
    small = resized(colour, 900)
    light, a_star, b_star = lab_of(small)
    slope_x = cv2.Sobel(light, cv2.CV_64F, 1, 0, ksize=3)
    slope_y = cv2.Sobel(light, cv2.CV_64F, 0, 1, ksize=3)
    out['gradient'] = float(np.median(np.hypot(slope_x, slope_y)))
    out['stripiness'] = float((slope_x ** 2).sum() / (slope_y ** 2).sum())
    olive = (b_star > 6) & (a_star < 1)
    tan = (b_star > 6) & (a_star > 0) & (light > 30)
    out['olive_percent'] = float(olive.mean() * 100)
    out['tan_percent'] = float(tan.mean() * 100)
    out['moss_spread'] = float(light[olive].std()) if olive.any() else 0.0
    big = resized(colour, 1254)
    light, a_star, b_star = lab_of(big)
    olive = ((b_star > 6) & (a_star < 1)).astype(np.uint8)
    closed = cv2.morphologyEx(olive, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    count, _, stats, _ = cv2.connectedComponentsWithStats(closed, connectivity=8)
    out['moss_clump'] = int(stats[1:, cv2.CC_STAT_AREA].max()) if count > 1 else 0
    slates = cv2.erode((light > 12).astype(np.uint8), np.ones((3, 3), np.uint8))
    count, labels, stats, _ = cv2.connectedComponentsWithStats(slates, connectivity=4)
    keep = [i for i in range(1, count) if stats[i, cv2.CC_STAT_AREA] > 5000]
    sums = np.bincount(labels.ravel(), weights=light.ravel(), minlength=count)
    means = np.array([sums[i] / stats[i, cv2.CC_STAT_AREA] for i in keep])
    out['brightest_slate'] = float(means.max())
    out['slate_spread'] = float(means.std())
    out['mean_lab'] = [round(float(v.mean()), 1) for v in lab_of(big)]
    return out


def relief_measures(normal_rgb):
    x = normal_rgb[..., 0].astype(np.float64) - 127.5
    y = normal_rgb[..., 1].astype(np.float64) - 127.5
    return {'tilt_p99': float(np.percentile(np.hypot(x, y), 99)), 'up_down_slope': float(np.abs(y).mean()),
            'side_slope': float(np.abs(x).mean())}


def measure(folder, normal_file=None):
    if folder.startswith('reference@'):                     # the reference shrunk to a bake size, relief made from its height like a bake
        size = int(folder.split('@')[1])
        result = colour_measures(cv2.imread(os.path.join(REFERENCE, 'colour.png')))
        height = cv2.resize(cv2.imread(os.path.join(REFERENCE, 'height.png'), cv2.IMREAD_UNCHANGED).astype(np.float32), (size, size),
                            interpolation=cv2.INTER_AREA).round().astype(np.uint16)
        normal = ((make_normal.sobel_normal_from_height(height, 7.0 * size / 1254.0) * 0.5 + 0.5) * 255).round().astype(np.uint8)
        result.update(relief_measures(normal))
        result['relief_size'] = size
        return result
    if folder == 'reference':
        colour = cv2.imread(os.path.join(REFERENCE, 'colour.png'))
        result = colour_measures(colour)
        result.update(relief_measures(cv2.imread(os.path.join(REFERENCE, 'normal.png'))[..., ::-1]))
        result['relief_size'] = 1254
        return result
    colour = cv2.imread(os.path.join(folder, 'colour.png'))
    result = colour_measures(colour) if colour is not None else {}
    height_path = os.path.join(folder, 'height.png')
    if normal_file:
        normal = cv2.imread(os.path.join(folder, normal_file))[..., ::-1]
    elif os.path.exists(height_path):
        height = cv2.imread(height_path, cv2.IMREAD_UNCHANGED)
        height = height[..., 0] if height.ndim == 3 else height
        if height.dtype != np.uint16:
            height = height.astype(np.uint16) * 257
        strength = 7.0 * height.shape[0] / 1254.0
        normal = ((make_normal.sobel_normal_from_height(height, strength) * 0.5 + 0.5) * 255).round().astype(np.uint8)
    else:
        normal = None
    if normal is not None:
        result.update(relief_measures(normal))
        result['relief_size'] = int(normal.shape[0])
    return result


ORDER = [('gradient', '%.2f'), ('stripiness', '%.3f'), ('olive_percent', '%.1f'), ('tan_percent', '%.2f'), ('moss_spread', '%.2f'),
         ('moss_clump', '%d'), ('brightest_slate', '%.1f'), ('slate_spread', '%.2f'), ('tilt_p99', '%.1f'), ('up_down_slope', '%.2f'),
         ('side_slope', '%.2f'), ('relief_size', '%d')]


def main():
    arguments = sys.argv[1:]
    json_out = None
    normal_file = None
    if '--json' in arguments:
        json_out = arguments[arguments.index('--json') + 1]
        del arguments[arguments.index('--json'):arguments.index('--json') + 2]
    if '--normal-file' in arguments:
        normal_file = arguments[arguments.index('--normal-file') + 1]
        del arguments[arguments.index('--normal-file'):arguments.index('--normal-file') + 2]
    results = {}
    print('name'.ljust(34) + ''.join(name[:11].rjust(12) for name, _ in ORDER))
    for folder in arguments:
        result = measure(folder, normal_file)
        results[folder] = result
        label = folder if folder.startswith('reference') else os.path.basename(os.path.normpath(folder))
        print(label[:33].ljust(34) + ''.join(((fmt % result[name]) if name in result else '-').rjust(12) for name, fmt in ORDER), flush=True)
    if json_out:
        with open(json_out, 'w') as handle:
            note = 'measure_look.py numbers (see the top of measure_look.py for what each one means)'
            json.dump(dict({'_note': note}, **results), handle, indent=1)


if __name__ == '__main__':
    main()
