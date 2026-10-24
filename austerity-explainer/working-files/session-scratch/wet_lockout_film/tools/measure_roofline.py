"""What this file does (plain words): checks the sky and roof line for a halo or a misfit (the wet street test's checker saw a possible 2-dot misfit at the roofs). In a picture drawn from the plate's own camera
(a frame of the clip before the move starts, or the 'projector' still), takes Blender's exact sky outline (the wet street test's sky mask, read only), and for every dot within 8 dots of that outline on either side
averages the brightness by its signed distance from the outline (negative = sky side, positive = roof/house side). The painting cut to the film's 40-degree lens gives the same profile; a halo or a misfit shows as a difference
between the two profiles right at the outline. Also reports the best extra shift (in dots) that would make the picture's edge sit on the outline.
Run: python3 -I measure_roofline.py PAINTING.jpg LABEL=PICTURE.jpg ...
"""
import json, os, sys
import cv2, numpy as np
sys.path.insert(0, '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/painter_round_2/stage/tools')
from stage_common import central, central_mask, load01
SKY = '/tmp/claude-0/-home-user-Music/02fc5154-76f5-5aac-a505-860164e7e921/scratchpad/proc-work/street_wet/painter_round_2/paint/work/sky/sky_coverage_1536x2730.png'
cov = cv2.imread(SKY, cv2.IMREAD_UNCHANGED).astype(np.float32)
cov = cov / (65535.0 if cov.max() > 255 else 255.0)
sky = central_mask(cov > 0.5)
d_in = cv2.distanceTransform(sky.astype(np.uint8), cv2.DIST_L2, 5)          # inside the sky: distance to the outline
d_out = cv2.distanceTransform((~sky).astype(np.uint8), cv2.DIST_L2, 5)
signed = np.where(sky, -d_in, d_out)                                       # sky side negative
def lum(rgb): return (0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]).astype(np.float32)
def profile(L):
    r = {}
    for lo in range(-8, 8, 1):
        m = (signed >= lo) & (signed < lo + 1)
        r[lo] = float(L[m].mean())
    return r
def crossing(pr):
    # where (signed distance, dots) the profile, scaled from the roof side level (0) to the sky side level (1), crosses one half
    xs = [k + 0.5 for k in range(-8, 8)]; ys = [pr[k] for k in range(-8, 8)]
    sky_level = np.nanmean([pr[k] for k in range(-8, -4)]); roof_level = np.nanmean([pr[k] for k in range(4, 8)])
    n = [(y - roof_level) / (sky_level - roof_level) for y in ys]
    pts = [(x, v) for x, v in zip(xs, n) if not np.isnan(v)]
    for (x0, v0), (x1, v1) in zip(pts, pts[1:]):
        if v0 >= 0.5 >= v1: return x0 + (v0 - 0.5) / (v0 - v1) * (x1 - x0)
    return float('nan')
painting = lum(central(load01(sys.argv[1])))
pp = profile(painting)
out = {'painting': pp}
print('signed distance (dots) | painting | ' + ' | '.join(a.split('=')[0] for a in sys.argv[2:]))
profs = {}
for a in sys.argv[2:]:
    label, path = a.split('=', 1)
    im = cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2RGB).astype(np.float64) / 255
    profs[label] = profile(lum(im))
    # the best extra shift: which (dx, dy) in -3..3 makes the picture's edge strength under the outline largest
    g = cv2.GaussianBlur(lum(im), (0, 0), 1.0); gx = cv2.Sobel(g, cv2.CV_32F, 1, 0); gy = cv2.Sobel(g, cv2.CV_32F, 0, 1); mag = np.hypot(gx, gy)
    edge = (signed >= -1.5) & (signed <= 1.5)
    best = max(((float(np.roll(np.roll(mag, dy, 0), dx, 1)[edge].mean()), dx, dy) for dx in range(-3, 4) for dy in range(-3, 4)))
    out[label] = {'profile': profs[label], 'best_extra_shift_dx_dy_(dots)': [best[1], best[2]], 'edge_strength_at_best_vs_unmoved': [best[0], float(mag[edge].mean())]}
for lo in range(-8, 8):
    print(f'{lo:4d}..{lo + 1:<3d} | {pp[lo]:.3f} | ' + ' | '.join(f'{profs[k][lo]:.3f}' for k in profs))
print('where the profile crosses one half (dots from the outline; + = on the roof side): painting %.2f' % crossing(pp) + ''.join(f'  {k} %.2f' % crossing(profs[k]) for k in profs))
out['crossing_half'] = {'painting': crossing(pp), **{k: crossing(profs[k]) for k in profs}}
for k in profs: print(k, 'best extra shift (dx, dy):', out[k]['best_extra_shift_dx_dy_(dots)'], 'edge strength at best / unmoved: %.3f / %.3f' % tuple(out[k]['edge_strength_at_best_vs_unmoved']))
json.dump(out, open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'numbers', 'roofline.json'), 'w'), indent=1)
