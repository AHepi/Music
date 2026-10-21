"""What this file does (plain words): two small checks on the plate-view stage pictures. (1) COLOUR: with nothing of the stage's finish left, does the painting's colour come through unchanged (blue minus red, and the three colour channels, on the road)? That rules out
a colour-handling fault as the cause of the darkening. (2) SKY: does the fix change the sky? Brightness of the sky in the painting (middle part, Blender's sky mask) against the stage before and after the fix. Writes numbers/sky_and_colour.json.
Run: python3 -I tools/measure_sky_and_colour.py"""
import json, os, sys
import cv2, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'tools'))
from stage_common import central, central_mask, masks, er, load01, TEST1, P
M = masks(TEST1 + 'alignment/facts_surfaces/'); road = er(central_mask(M['road']))
paint = central(load01(P('../paint/front_painting_final.png')))
def st(folder, name): return cv2.cvtColor(cv2.imread(P('stills', folder, name, 'still-6.00.jpg')), cv2.COLOR_BGR2RGB).astype(np.float64) / 255
lum = lambda im: 0.2126 * im[..., 0] + 0.7152 * im[..., 1] + 0.0722 * im[..., 2]
res = {'colour_on_the_road': {}, 'sky': {}}
for name, im in (('painting', paint), ('stage, nothing of the finish left', st('diagnosis', 'off_all')), ('stage before the fix', st('before', 'wet_projector')), ('stage after the fix', st('after', 'wet_projector'))):
    res['colour_on_the_road'][name] = {'red': float(im[..., 0][road].mean()), 'green': float(im[..., 1][road].mean()), 'blue': float(im[..., 2][road].mean()), 'blue_minus_red': float((im[..., 2] - im[..., 0])[road].mean())}
cov = cv2.imread(P('../paint/work/sky/sky_coverage_1536x2730.png'), cv2.IMREAD_UNCHANGED).astype(np.float32) / 255
cov_c = central(cov.astype(np.float32)) if cov.ndim == 2 else central(cov[..., 0])
sky = (cov_c > 0.999) & (np.arange(1920)[:, None] < 0.4 * 1920)
sky = cv2.erode(sky.astype(np.uint8), np.ones((15, 15), np.uint8)) > 0
for name, im in (('painting', paint), ('stage, nothing of the finish left', st('diagnosis', 'off_all')), ('stage before the fix', st('before', 'wet_projector')), ('stage after the fix', st('after', 'wet_projector'))):
    res['sky'][name] = {'mean_brightness': float(lum(im)[sky].mean()), 'sky_dots': int(sky.sum())}
json.dump(res, open(P('numbers/sky_and_colour.json'), 'w'), indent=1); print(json.dumps(res, indent=1))
