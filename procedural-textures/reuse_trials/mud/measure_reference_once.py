# What this does (plain words): measures a few GENERAL numbers of the mud reference ONCE, as a guide for the settings of the mud trial.
# Nothing here is traced or stored dot by dot; only a handful of summary numbers are written to reference_measures.json.
#   1. SHARES BY KIND: every dot of the reference colour picture is given the nearest of the 16 stored mud palette colours (the palette comes from
#      recipes/mud/generator/fitted_distributions_mud.json, key stats.palette_rgb, which also says which colours are earth, stone or water).
#      The share of dots in each kind, and the average colour of each kind, are the numbers.
#   2. HOW DARK THE EARTH IS: percentiles (the brightness that 5, 25, 50, 75 and 95 percent of the earth dots stay under).
#   3. HOW THE REFERENCE HEIGHT PICTURE FOLLOWS ITS COLOUR: a straight line "height = slope x (grey - grey_at_zero) / 255", cut to 0..1, is fitted
#      ONCE to the reference's own height.png against the grey of its colour.png (grey = 0.299 R + 0.587 G + 0.114 B of the screen numbers).
#      This is the one place where a reference MAP (not the colour picture) is read; it is used only for the height rule at the end of the recipe.
#   4. SIZE OF THE BIG SOFT PATCHES: how far you can slide the "wet earth" (darker than 30 of 255 brightness, small specks removed) before it matches
#      itself only half as well. A guide for the size of the big dry and wet areas (COLOUR AND FADE's big patches).
# Use: python3 -I measure_reference_once.py   (writes reference_measures.json next to this file)
import json
import os

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..'))
colour = cv2.imread(os.path.join(PROC, 'reference', 'mud', 'colour.png'))[..., ::-1].astype(np.float64)
height = cv2.imread(os.path.join(PROC, 'reference', 'mud', 'height.png'), cv2.IMREAD_UNCHANGED).astype(np.float64)
height = height / (65535.0 if height.max() > 255 else 255.0)
with open(os.path.join(PROC, 'recipes', 'mud', 'generator', 'fitted_distributions_mud.json')) as handle:
    stats = json.load(handle)['stats']
palette = np.array(stats['palette_rgb'], dtype=np.float64)
kinds = np.array(stats['palette_kinds'])
grey = 0.299 * colour[..., 0] + 0.587 * colour[..., 1] + 0.114 * colour[..., 2]

# 1. shares by kind
distance = ((colour[:, :, None, :] - palette[None, None, :, :]) ** 2).sum(axis=-1)
label = distance.argmin(axis=-1)
kind_of_dot = kinds[label]
shares = {k: round(float((kind_of_dot == k).mean()), 4) for k in ('earth', 'stone', 'water')}
average = {k: [round(float(c), 1) for c in colour[kind_of_dot == k].mean(axis=0)] for k in ('earth', 'stone', 'water')}
# 2. earth brightness percentiles
earth_grey = grey[kind_of_dot == 'earth']
percentiles = {str(p): round(float(np.percentile(earth_grey, p)), 1) for p in (5, 25, 50, 75, 95)}
# the share of EARTH dots that is very dark (the ruts and the deep shade): under 40 of 255
dark_earth_share = round(float((earth_grey < 40).mean()), 4)
# 3. height against grey: grid search for slope and grey_at_zero (a straight line, cut to 0..1)
best = None
sample = np.random.RandomState(0).choice(grey.size, 200000, replace=False)
g, h = grey.ravel()[sample], height.ravel()[sample]
for zero in np.arange(0, 60, 2.0):
    for slope in np.arange(1.5, 3.6, 0.05):
        error = np.abs(np.clip(slope * (g - zero) / 255.0, 0, 1) - h).mean()
        if best is None or error < best[0]:
            best = (error, zero, slope)
# 4. wet-earth patch size
wet = (grey < 30).astype(np.uint8)
kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
wet = cv2.morphologyEx(np.pad(wet, 8, mode='wrap'), cv2.MORPH_OPEN, kernel)[8:-8, 8:-8]


def half_length(mask, level=0.5):
    centred = mask.astype(np.float64) - mask.mean()
    auto = np.fft.ifft2(np.abs(np.fft.fft2(centred)) ** 2).real
    auto /= auto[0, 0]
    out = []
    for line in (auto[0, :mask.shape[1] // 2], auto[:mask.shape[0] // 2, 0]):
        below = np.where(line < level)[0]
        out.append(int(below[0]) if len(below) else mask.shape[0] // 2)
    return out


result = {
    'share_of_dots_by_kind (nearest of the 16 stored palette colours)': shares,
    'average_colour_by_kind (r, g, b of 255)': average,
    'earth_brightness_percentiles (of 255)': percentiles,
    'dark_earth_share (earth dots with brightness under 40)': dark_earth_share,
    'overall_brightness_mean (of 255)': round(float(grey.mean()), 1),
    'reference_height_rule_fit (height = clip(slope x (grey - grey_at_zero) / 255, 0, 1))': {
        'grey_at_zero': float(best[1]), 'slope': round(float(best[2]), 3), 'mean_error_of_1': round(float(best[0]), 4),
        'note': 'the earlier mud recipe found (grey - 20) / 108 = slope 2.36, grey_at_zero 20 (04 Recipe - mud, section 2)'},
    'dark_patch_share (brightness under 30, 5-dot opening)': round(float(wet.mean()), 4),
    'dark_patch_half_length_dots [across, up-down]': half_length(wet),
    'from the stored mud numbers (read, not measured here)': [
        'clod area median 39 dots, long side 1.9 x short side (04 Recipe - mud, 3.5)',
        'puddles: 8 per tile, area 3000 to 31600 dots (fitted_distributions_mud.json)',
        'stones: 830 per tile, area median 83 dots, 90th percentile 709, biggest 10548 (fitted_distributions_mud.json)',
        'ruts: 34 long bands about 20 dots wide (04 Recipe - mud, 3.4)'],
}
with open(os.path.join(HERE, 'reference_measures.json'), 'w') as handle:
    json.dump(result, handle, indent=1)
print(json.dumps(result, indent=1))
