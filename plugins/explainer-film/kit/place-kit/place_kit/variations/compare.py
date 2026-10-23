"""What this does: MEASURES the pictures a variations batch drew and checks, AFTER drawing, that they really differ. Plain Python with numpy and Pillow (the same as
calculators/picture_measures.py, which it uses for the numbers); no Blender needed.

For every picture of every variation, and against the baseline picture drawn through the same camera:
    value range         the 5th and 95th percentile of luminance and their gap (a flat picture has a small gap)
    detail energy       fine contrast (picture_measures.detail_energy) and how far it moved from the baseline's
    colour shift        how far the picture's average colour moved from the baseline's, in Lab units (0 = the same; about 2 is the least a person sees)
    saturation shift    the change in average saturation (colourfulness) against the baseline
    squint score        the similarity (1.0 = the same) of the two pictures' 12-pixel-blurred luminance: do the big shapes and the light hold (the house target is place_measures.squint_target)
The numbers shown for a variation are the average over its cameras; the full list for each camera is in the result file.

AFTER drawing, every pair of variations (the baseline too) is compared pixel by pixel: the mean absolute difference (0 to 255) and the share of pixels that moved by more than
place_variations.picture_pixel_step. A pair whose pictures came out nearly the same through EVERY camera (mean under place_variations.picture_mean_difference_min and fewer than
place_variations.picture_changed_share_min of the pixels changed) is flagged. A variation nearly the same as the baseline is flagged "does not show in these cameras": its settings may be right
but the change cannot be seen from where the cameras are (or the setting changed nothing in this scene).

A free scout (`variations scout`: 240 x 160, 8 samples, drawn here) uses its own limits, place_variations.scout_picture_mean_difference_min (0.75) and scout_picture_changed_share_min
(0.3 percent): tiny low-sample pictures differ more, and with these limits two scouts called exactly the same pairs nearly the same as the two real rented-card batches did.

A concrete example: two pictures of a wall with moss cover 0.50 and 0.55 differ by a mean of 0.2 in 255 and 0.1 percent of pixels: flagged as nearly the same.

MEASURABLY IS NOT ALWAYS VISIBLY. A pair that is not nearly the same only because of its MEAN (in every camera fewer than the changed-share limit of pixels moved by more than the
pixel step) differs by a faint, even shift: a dial that tints a whole surface a little (dirt film), or noise. It is flagged "may not be visible" (pair_differences 'faint'), not dropped:
the person looks at the sheet. Example (a tiny wall, 23 October 2026, scout 240 x 160): one variation against the saved scene had a mean difference of 0.68 and 0.97 in the two cameras
but only 0.02 and 0.05 percent of its pixels changed; by eye the two pictures look the same. Why the rule for "nearly the same" was NOT changed to the share alone: on the two real card
batches it would have called 7 more moss pairs nearly the same, and the scout would then have missed one of them, so the measured agreement (22 of 22 pairs) would have broken.
"""
import itertools
import os

import numpy as np

from .. import house_numbers as numbers


def _picture_measures():
    import picture_measures    # the calculators folder is on sys.path (house_numbers puts it there)
    return picture_measures


def mean_lab(rgb):
    """The Lab colour (D65) of a picture's mean colour, mean taken in linear light. rgb: float array 0..1, shape (rows, columns, 3)."""
    linear = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4).reshape(-1, 3).mean(axis=0)
    matrix = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750], [0.0193339, 0.1191920, 0.9503041]])
    xyz = matrix @ linear / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 216 / 24389, np.cbrt(xyz), (24389 / 27 * xyz + 16) / 116)
    return np.array([116 * f[1] - 16, 500 * (f[0] - f[1]), 200 * (f[1] - f[2])])


def colour_shift(rgb_a, rgb_b):
    return float(np.linalg.norm(mean_lab(rgb_a) - mean_lab(rgb_b)))


def measure_variations(results, baseline_name='baseline'):
    """Adds 'measures' to each result: {camera: {...}} and 'average': {...}. results: the per-variation dictionaries with pictures that carry an absolute 'path'. Returns the list."""
    pm = _picture_measures()
    settings = numbers.table()
    baseline = next((r for r in results if r['name'] == baseline_name), None)
    base_paths = {p['camera']: p['path'] for p in (baseline or {}).get('pictures', []) if p.get('ok') and p.get('path')}
    for result in sorted(results, key=lambda r: r['name'] != baseline_name):      # the baseline first: every other measure is against it
        result['measures'] = {}
        for picture in result.get('pictures', []):
            if not picture.get('ok') or not picture.get('path'):
                continue
            base_path = base_paths.get(picture['camera'])
            previous = base_path if base_path and base_path != picture['path'] else None
            measured = pm.measure_picture(picture['path'], settings, None, previous)
            percentiles = measured['percentiles']
            row = {'p5': percentiles['5'], 'p95': percentiles['95'], 'range': percentiles['95'] - percentiles['5'], 'median': percentiles['50'], 'detail': measured['detail_energy']['all'],
                   'mean_saturation': measured['mean_saturation'], 'squint': measured['squint']['similarity'] if previous else 1.0, 'flat_windows': measured['flat_windows']['flat']}
            if previous:
                rgb, base_rgb = pm.load_picture(picture['path']), pm.load_picture(previous)
                base_row = next(r for r in results if r['name'] == baseline_name)['measures'].get(picture['camera'])
                row['colour_shift'] = colour_shift(rgb, base_rgb)
                row['saturation_shift'] = row['mean_saturation'] - base_row['mean_saturation'] if base_row else 0.0
                row['detail_change'] = row['detail'] - base_row['detail'] if base_row else 0.0
            else:
                row.update({'colour_shift': 0.0, 'saturation_shift': 0.0, 'detail_change': 0.0})
            result['measures'][picture['camera']] = row
        rows = list(result['measures'].values())
        result['average'] = {key: float(np.mean([row[key] for row in rows])) for key in rows[0]} if rows else {}
    return results


def _load_uint8(path):
    from PIL import Image
    with Image.open(path) as picture:
        return np.asarray(picture.convert('RGB'), dtype=np.int16)


def pair_differences(results, scout=False):
    """The pairs that came out nearly the same. Returns {'pairs': [{'a', 'b', 'mean_difference', 'changed_share', 'nearly_the_same', 'faint', 'per_camera': {...}}], 'nearly_same': [(a, b)],
    'invisible': [names nearly the same as the baseline], 'faint': [(a, b)], 'faint_against_baseline': [names]} over every pair of drawn variations. scout=True uses the scout's own
    limits (tiny low-sample pictures differ more: see place_variations.scout_picture_mean_difference_min).
    'faint' pairs are measurably but maybe not visibly different: not nearly the same, yet in EVERY camera fewer than the changed-share limit of pixels moved by more than the pixel step
    (only the mean is over its limit: an even tint or noise). They are kept, with a note to look at the sheet."""
    prefix = 'place_variations.scout_' if scout else 'place_variations.'
    need_mean = float(numbers.value(prefix + 'picture_mean_difference_min'))
    need_share = float(numbers.value(prefix + 'picture_changed_share_min'))
    step = int(numbers.value('place_variations.picture_pixel_step'))
    drawn = [r for r in results if r.get('ok') and r.get('pictures')]
    cache = {}
    for result in drawn:
        for picture in result['pictures']:
            if picture.get('ok') and picture.get('path'):
                cache[(result['name'], picture['camera'])] = _load_uint8(picture['path'])
    pairs, nearly, invisible, faint, faint_against_baseline = [], [], [], [], []
    for first, second in itertools.combinations(drawn, 2):
        per_camera = {}
        for camera in {c for (n, c) in cache if n == first['name']} & {c for (n, c) in cache if n == second['name']}:
            a, b = cache[(first['name'], camera)], cache[(second['name'], camera)]
            if a.shape != b.shape:
                continue
            difference = np.abs(a - b)
            per_camera[camera] = {'mean_difference': float(difference.mean()), 'changed_share': float((difference.max(axis=2) > step).mean())}
        if not per_camera:
            continue
        same = all(v['mean_difference'] < need_mean and v['changed_share'] < need_share for v in per_camera.values())
        only_the_mean = not same and all(v['changed_share'] < need_share for v in per_camera.values())
        mean_all = float(np.mean([v['mean_difference'] for v in per_camera.values()]))
        share_all = float(np.mean([v['changed_share'] for v in per_camera.values()]))
        pairs.append({'a': first['name'], 'b': second['name'], 'mean_difference': mean_all, 'changed_share': share_all, 'nearly_the_same': same, 'faint': only_the_mean,
                      'per_camera': per_camera})
        other = second['name'] if first['name'] == 'baseline' else first['name']
        if same:
            nearly.append((first['name'], second['name']))
            if 'baseline' in (first['name'], second['name']):
                invisible.append(other)
        elif only_the_mean:
            faint.append((first['name'], second['name']))
            if 'baseline' in (first['name'], second['name']):
                faint_against_baseline.append(other)
    return {'pairs': pairs, 'nearly_same': nearly, 'invisible': invisible, 'faint': faint, 'faint_against_baseline': faint_against_baseline,
            'changed_share_limit': need_share, 'pixel_step': step}


def reset_drift(baseline_path, check_path):
    """How far the picture drawn again after all the variations differs from the first baseline picture (mean difference in 255; 0 = the reset was exact)."""
    if not (baseline_path and check_path and os.path.exists(baseline_path) and os.path.exists(check_path)):
        return None
    a, b = _load_uint8(baseline_path), _load_uint8(check_path)
    return float(np.abs(a - b).mean()) if a.shape == b.shape else None
