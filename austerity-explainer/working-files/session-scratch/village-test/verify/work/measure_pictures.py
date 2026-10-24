# What this does: a fresh checker's measures on the pictures (plain Python with Pillow, numpy and OpenCV; no Blender).
#   1. Ground detail: same-size crops (540 x 360 pixels) of the first village's road close-up, the rebuilt village's road close-up and the coal mine's
#      ground, and the same road patch in the road_eye view before and after. For each crop: contrast (spread of brightness over its mean), fine detail
#      (what a 1.5-pixel blur takes away), middle detail (what lies between a 1.5- and a 6-pixel blur), sharp-edge share (pixels whose brightness changes
#      by more than a tenth of the mean from one pixel to the next) and colour spread (mean distance from the crop's own mean colour, in Lab units).
#      All brightness numbers are divided by the crop's mean brightness, so a darker dusk picture is not marked down for being dark.
#   2. Thatch sparkles: tiny pixels on the thatch roofs much brighter than the 7 x 7 pixels round them, before and after.
#   Also for each ground crop: coarse detail (what lies between a 6- and a 24-pixel blur: lumps, stones, hollows) and the number of separate lumps
#   (regions of 60 to 6000 pixels at least 35% brighter or darker than the 24-pixel blur round them: stones, clods, holes, puddles).
# Use: python3 measure_pictures.py OUT.json
import json
import sys

import cv2
import numpy as np
from PIL import Image

BASE = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/village-test/'
MINE = '/home/user/Music/mine-scene/01 Coal mine - dusk photo 1080x1920.png'
BEFORE = BASE + 'main-session-look/out/View_'
AFTER = BASE + 'rebuild/'
CLOSE_BEFORE = BASE + 'verify/work/before-closeup/ground_ruts_preview.jpg'
CLOSE_AFTER = BASE + 'rebuild/ground_closeup.jpg'
CROPS = {
    'road close-up, first village': (CLOSE_BEFORE, (330, 440, 870, 800)),
    'road close-up, rebuilt village': (CLOSE_AFTER, (330, 440, 870, 800)),
    "coal mine's ground": (MINE, (0, 1520, 540, 1880)),
    "coal mine's ground with the puddle": (MINE, (440, 1560, 980, 1920)),
    'road in road_eye view, first village': (BEFORE + 'road_eye.jpg', (330, 600, 870, 800)),
    'road in road_eye view, rebuilt village': (AFTER + 'road_eye.jpg', (330, 600, 870, 800)),
}


def load(path):
    return np.asarray(Image.open(path).convert('RGB')).astype(np.float64) / 255.0


def linear(rgb):
    return np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)


def lab(rgb):
    return cv2.cvtColor(rgb.astype(np.float32), cv2.COLOR_RGB2LAB)


def detail(rgb):
    lum = (linear(rgb) @ np.array([0.2126, 0.7152, 0.0722]))
    mean = lum.mean()
    fine = lum - cv2.GaussianBlur(lum, (0, 0), 1.5)
    middle = cv2.GaussianBlur(lum, (0, 0), 1.5) - cv2.GaussianBlur(lum, (0, 0), 6.0)
    step = np.hypot(np.diff(lum, axis=1)[:-1, :], np.diff(lum, axis=0)[:, :-1])
    colours = lab(rgb).reshape(-1, 3)
    coarse = cv2.GaussianBlur(lum, (0, 0), 6.0) - cv2.GaussianBlur(lum, (0, 0), 24.0)
    local = cv2.GaussianBlur(lum, (0, 0), 24.0)
    lumps = 0
    for mask in ((lum > local * 1.35), (lum < local * 0.65)):
        count, _labels, stats, _centres = cv2.connectedComponentsWithStats(cv2.morphologyEx(mask.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)))
        lumps += int(((stats[1:, cv2.CC_STAT_AREA] >= 60) & (stats[1:, cv2.CC_STAT_AREA] <= 6000)).sum())
    return {'coarse_detail': round(float(coarse.std() / mean), 4), 'lumps': lumps, 'mean_brightness': round(float(mean), 4), 'contrast': round(float(lum.std() / mean), 3), 'fine_detail': round(float(fine.std() / mean), 4),
            'middle_detail': round(float(middle.std() / mean), 4), 'sharp_edge_share': round(float((step > 0.1 * mean).mean()), 4),
            'colour_spread_lab': round(float(np.linalg.norm(colours - colours.mean(axis=0), axis=1).mean()), 2)}


result = {'crops': {}, 'crop_boxes': {k: v[1] for k, v in CROPS.items()}}
for name, (path, box) in CROPS.items():
    image = load(path)
    x0, y0, x1, y1 = box
    result['crops'][name] = detail(image[y0:y1, x0:x1])

# thatch sparkles: a pixel 0.18 brighter than the median of the 7 x 7 pixels round it, inside the roof boxes
ROOFS = {'wide': [(100, 410, 390, 550), (600, 470, 840, 660)], 'cottage_close': [(490, 100, 1020, 380)], 'road_eye': [(10, 220, 370, 390), (840, 250, 1080, 400)]}
sparkles = {}
for view, boxes in ROOFS.items():
    for label, path in (('first village', BEFORE + view + '.jpg'), ('rebuilt village', AFTER + view + '.jpg')):
        image = load(path)
        lum = image @ np.array([0.2126, 0.7152, 0.0722])
        median = cv2.medianBlur((lum * 255).astype(np.uint8), 7).astype(np.float64) / 255.0
        count = 0
        for x0, y0, x1, y1 in boxes:
            spots = (lum[y0:y1, x0:x1] - median[y0:y1, x0:x1]) > 0.18
            count += int(cv2.connectedComponents(spots.astype(np.uint8))[0] - 1)
        sparkles.setdefault(view, {})[label] = count
result['thatch_sparkles'] = sparkles


with open(sys.argv[1], 'w') as handle:
    json.dump(result, handle, indent=1)
print(json.dumps(result, indent=1))
