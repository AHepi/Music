# What this does (plain words): measures TWO general numbers of the brick reference picture ONCE, as a guide for the GRIME layer's soot
# settings. Nothing here is traced or stored dot by dot; only a few summary numbers are written.
#   1. how much of the picture is soot-dark OUTSIDE the thin dark ring around the bricks: dark dots (brightness under 70 of 255) are found,
#      then every dark line thinner than about 7 dots (the ring) is removed by an "opening" (shrink the dark areas by 3 dots, grow them back:
#      thin lines vanish, clouds stay). The share left is the soot-cloud share.
#   2. how big a soot cloud is: how far you can slide that soot mask sideways (and up-down) before it matches itself only half as well.
# It also reads the already-measured summaries (palette_k16.npy, element_stats.json, the sampler's soot and spall numbers) and prints them.
# Use: python3 -I measure_reference_once.py   (writes reference_measures.json next to this file)
import json
import os

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..'))
colour = cv2.imread(os.path.join(PROC, 'reference', 'brick', 'colour.png'))[..., ::-1].astype(np.float64)
brightness = 0.299 * colour[..., 0] + 0.587 * colour[..., 1] + 0.114 * colour[..., 2]
dark = (brightness < 70).astype(np.uint8)
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
padded = np.pad(dark, 8, mode='wrap')                    # the tile repeats, so the edges wrap
opened = cv2.morphologyEx(padded, cv2.MORPH_OPEN, kernel)[8:-8, 8:-8]


def half_length(mask, level=0.5):
    """Slide distance (dots) at which the mask matches itself `level` times as well as unslid (0.5 = half), along x and along y."""
    centred = mask.astype(np.float64) - mask.mean()
    power = np.abs(np.fft.fft2(centred)) ** 2
    auto = np.fft.ifft2(power).real
    auto /= auto[0, 0]
    result = []
    for line in (auto[0, :mask.shape[1] // 2], auto[:mask.shape[0] // 2, 0]):
        below = np.where(line < level)[0]
        result.append(int(below[0]) if len(below) else mask.shape[0] // 2)
    return result


with open(os.path.join(PROC, 'recipes', 'brick', 'analysis', 'element_stats.json')) as handle:
    stats = json.load(handle)
with open(os.path.join(PROC, 'recipes', 'brick', 'generator', 'sampler_model_brick.json')) as handle:
    sampler = json.load(handle)
result = {
    'dark_share_all (brightness under 70)': round(float(dark.mean()), 4),
    'soot_cloud_share (dark, thin ring removed by a 7-dot opening)': round(float(opened.mean()), 4),
    'thin_dark_lines_share (ring and specks)': round(float(dark.mean() - opened.mean()), 4),
    'soot_cloud_half_length_dots [across, up-down]': half_length(opened),
    'dark_mask_half_length_dots [across, up-down]': half_length(dark),
    'soot_cloud_fifth_length_dots [across, up-down] (where it matches itself only 0.2 as well: the size of the whole cloud)': half_length(opened, 0.2),
    'soot_envelope_half_length_dots [across, up-down] (the soot mask blurred over about 31 dots first, so mortar bands do not cut it)':
        half_length(cv2.GaussianBlur(np.pad(opened.astype(np.float64), 64, mode='wrap'), (0, 0), 8)[64:-64, 64:-64]),
    'mortar_share (element_stats)': stats['mortar_share'],
    'patch_area_percentiles_dots (element_stats)': stats['patch_area_percentiles_dots'],
    'sampler_layout': sampler['layout'],
    'sampler_accents (soot and spall, some chosen by eye)': sampler['accents'],
    'height_rule (sampler curve: colour brightness -> height)': {'x': sampler['maps']['curve_x'], 'y': sampler['maps']['curve_y'],
                                                                 'normal_strength': sampler['maps']['normal_strength']},
}
with open(os.path.join(HERE, 'reference_measures.json'), 'w') as handle:
    json.dump(result, handle, indent=1)
print(json.dumps(result, indent=1))
