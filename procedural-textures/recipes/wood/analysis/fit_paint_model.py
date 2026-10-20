# What this does (plain words): ANALYSIS (reads the reference picture). Measures how the wood is PAINTED so that a sampler can invent new paint of the same kind.
# The picture is painted in two scales: big slowly-changing "zones" (warm brown, grey-blue, dark) and, on top of them, many horizontal strips whose
# colour is close to the zone beneath them. So the model has:
#   - a 16-colour palette (k-means of the average colours of the 8000 traced patches, weighted by area);
#   - the strips by size class: how many per megapixel, how long, how thin (measured as the equal-area rectangle of each patch: length and thickness from its spread);
#   - the ZONE colours: the average colour and spread (a 3 x 3 covariance in the Lab colour space) of the biggest strips, and how fast they change along and across the planks;
#   - for the smaller strips: how their colour differs from the colour beneath them (mean and spread of the Lab difference to the traced patch that holds them
#     one size step up), per size group;
#   - the target "visible area share" of every size class, used to calibrate the stamp counts (stamps overlap, so counting them is not enough).
# Output: analysis/paint_model.json and analysis/palette16.json. Run: python3 -I fit_paint_model.py     Plain Python.
import json
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, HERE)
import describe_tools as dt  # noqa: E402
import merge_trace as mt  # noqa: E402
import trace_tools as tt  # noqa: E402

REGIONS = 8000
PARENT_REGIONS = {1: 1500, 0: 4000}                 # the coarser traced picture used as "the colour beneath" for size groups 1 and 0
CLASS_EDGES = [3, 6, 12, 24, 48, 96, 192, 400, 1300]
GROUP_OF_CLASS = [0, 0, 0, 1, 1, 2, 2, 2]
MEGAPIXELS = 1254 * 1254 / 1e6

bgr = dt.load_reference()
comp, lab, tree = dt.load_merge_state(bgr)
labels, count = mt.labels_at(comp, tree, REGIONS)
means, area = mt.region_colours(labels, lab, count)
centres, index = mt.squeeze_palette(means, area, 16, seed=2)
order = np.argsort(centres[:, 0])
rank = np.empty(16, int)
rank[order] = np.arange(16)
index = rank[index]
centres = centres[order]
palette_rgb = []
for c in centres:
    b = cv2.cvtColor(np.array([[c]], np.float32), cv2.COLOR_Lab2BGR)[0, 0]
    palette_rgb.append([int(round(float(np.clip(v, 0, 1)) * 255)) for v in b[::-1]])
json.dump({'palette_rgb': palette_rgb, 'palette_lab': [[round(float(v), 2) for v in c] for c in centres]}, open(os.path.join(HERE, 'palette16.json'), 'w'))
print('palette16 (rgb):', palette_rgb)

# ---- region geometry: centre, equal-area rectangle (length, thickness) from the second moments
H, W = labels.shape
flat = labels.ravel()
ys, xs = np.divmod(np.arange(flat.size), W)
cx = np.bincount(flat, weights=xs, minlength=count) / area
cy = np.bincount(flat, weights=ys, minlength=count) / area
vxx = np.bincount(flat, weights=xs.astype(np.float64) ** 2, minlength=count) / area - cx ** 2 + 1 / 12.0
vyy = np.bincount(flat, weights=ys.astype(np.float64) ** 2, minlength=count) / area - cy ** 2 + 1 / 12.0
vxy = np.bincount(flat, weights=xs.astype(np.float64) * ys, minlength=count) / area - cx * cy
half_trace, root = (vxx + vyy) / 2, np.sqrt(((vxx - vyy) / 2) ** 2 + vxy ** 2)
lam1, lam2 = half_trace + root, np.maximum(half_trace - root, 1 / 12.0)
length = np.sqrt(12 * lam1)
thick = np.sqrt(12 * lam2)
angle = 0.5 * np.arctan2(2 * vxy, vxx - vyy)
horizontal = np.abs(np.degrees(angle)) < 25
print('share of patches whose long axis is within 25 degrees of horizontal:', round(float(horizontal[area > 20].mean()), 3))
rust_like = np.array([(12 <= centres[k][0] <= 30 and centres[k][2] > 11 and np.hypot(centres[k][1], centres[k][2]) > 14) for k in range(16)])[index]
fill = area / (length * thick)
blobby = rust_like & (length / np.maximum(thick, 1) < 2.2) & (area < 1500)
black = index <= 1
stamp = ~black & ~blobby
print('regions', count, '; black-family', int(black.sum()), '; blob-like rust', int(blobby.sum()))

# ---- classes by length
class_of = np.digitize(length, CLASS_EDGES) - 1
classes, shares = [], []
for ci in range(len(CLASS_EDGES) - 1):
    sel = stamp & (class_of == ci)
    if sel.sum() < 3:
        classes.append({'per_megapixel': 0.0, 'length': [CLASS_EDGES[ci], 0.3], 'aspect': [2.0, 0.3], 'taper': 0.6})
        shares.append(0.0)
        continue
    aspect = np.maximum(length[sel] / thick[sel], 1.0)
    classes.append({'per_megapixel': round(float(sel.sum() / MEGAPIXELS), 1), 'length': [round(float(np.exp(np.log(length[sel]).mean())), 1), round(float(np.log(length[sel]).std()), 3)],
                    'aspect': [round(float(np.exp(np.log(aspect).mean())), 2), round(float(np.log(aspect).std()), 3)], 'taper': 0.6})
    shares.append(round(float(area[sel].sum() / (H * W)), 4))
    print(f'class {ci} length {CLASS_EDGES[ci]}-{CLASS_EDGES[ci + 1]}: {int(sel.sum())} patches, {classes[-1]["per_megapixel"]} per Mpx, length median {classes[-1]["length"][0]}, aspect median {classes[-1]["aspect"][0]}, area share {shares[-1]}')

# ---- zone layer: the coarse traced picture (1500 patches): their colours (area-weighted Lab mean and covariance), their equal-area rectangles (row height and length)
ZONE_REGIONS = 1500
z_labels, z_count = mt.labels_at(comp, tree, ZONE_REGIONS)
z_means, z_area = mt.region_colours(z_labels, lab, z_count)
zf = z_labels.ravel()
zcx = np.bincount(zf, weights=xs, minlength=z_count) / z_area
zcy = np.bincount(zf, weights=ys, minlength=z_count) / z_area
zvxx = np.bincount(zf, weights=xs.astype(np.float64) ** 2, minlength=z_count) / z_area - zcx ** 2 + 1 / 12.0
zvyy = np.bincount(zf, weights=ys.astype(np.float64) ** 2, minlength=z_count) / z_area - zcy ** 2 + 1 / 12.0
zvxy = np.bincount(zf, weights=xs.astype(np.float64) * ys, minlength=z_count) / z_area - zcx * zcy
zh, zr = (zvxx + zvyy) / 2, np.sqrt(((zvxx - zvyy) / 2) ** 2 + zvxy ** 2)
z_len, z_thick = np.sqrt(12 * (zh + zr)), np.sqrt(12 * np.maximum(zh - zr, 1 / 12.0))
w = z_area / z_area.sum()
zone_mean = (z_means * w[:, None]).sum(axis=0)
zone_cov = ((z_means - zone_mean).T * w) @ (z_means - zone_mean)
zone_chol = np.linalg.cholesky(zone_cov + 1e-6 * np.eye(3))
big_enough = z_area > 400
zone_len = [round(float(np.exp(np.average(np.log(z_len[big_enough]), weights=z_area[big_enough]))), 1), round(float(np.log(z_len[big_enough]).std()), 3)]
zone_row = [round(float(np.exp(np.average(np.log(z_thick[big_enough]), weights=z_area[big_enough]))), 1), round(float(np.log(z_thick[big_enough]).std()), 3)]
print('zone Lab mean', zone_mean.round(1), ' spread (std of L, a, b)', np.sqrt(np.diag(zone_cov)).round(2), ' strip length (median, log-spread)', zone_len, ' row height', zone_row)
field = cv2.GaussianBlur(np.pad(lab[..., 2].astype(np.float64), 80, mode='wrap'), (0, 0), sigmaX=40, sigmaY=14)[80:-80, 80:-80]
f = (field - field.mean()) / field.std()


def e_fold(acf):
    below = np.nonzero(acf < 1 / np.e)[0]
    return int(below[0]) if len(below) else len(acf)


acf2 = np.real(np.fft.ifft2(np.abs(np.fft.fft2(f)) ** 2))
acf2 /= acf2[0, 0]
lengths = {'along_the_planks': e_fold(acf2[0, :W // 2]), 'across_the_planks': e_fold(acf2[:H // 2, 0])}
print('field correlation (1/e) lengths in dots:', lengths)

# ---- child colours relative to the colour of the coarser traced patch beneath them
children = {}
for g, parent_count in PARENT_REGIONS.items():
    p_labels, p_count = mt.labels_at(comp, tree, parent_count)
    p_means, p_area = mt.region_colours(p_labels, lab, p_count)
    sel = stamp & (np.array(GROUP_OF_CLASS)[np.clip(class_of, 0, 7)] == g) & (class_of >= 0)
    parent = p_means[p_labels[np.clip(cy[sel].astype(int), 0, H - 1), np.clip(cx[sel].astype(int), 0, W - 1)]]
    diff = means[sel] - parent
    ww = area[sel] / area[sel].sum()
    mean = (diff * ww[:, None]).sum(axis=0)
    cov = ((diff - mean).T * ww) @ (diff - mean)
    children[g] = {'mean': [round(float(v), 2) for v in mean], 'chol': np.linalg.cholesky(cov + 1e-6 * np.eye(3)).round(3).tolist()}
    print(f'group {g} children differ from the colour beneath by Lab mean {mean.round(2)}, spread {np.sqrt(np.diag(cov)).round(2)}')

# ---- fine speckle: how many tiny areas (12 dots or fewer) and how long; their colours as shares of the 16 palette entries
raw_centres = tt.make_palette(bgr, 24)
raw_labels = tt.assign_labels(bgr, raw_centres)
speck_widths, speck_colour_share = [], np.zeros(16)
for k in range(24):
    nn, cc, st, ce = cv2.connectedComponentsWithStats((raw_labels == k).astype(np.uint8), connectivity=4)
    small = np.nonzero((st[1:, cv2.CC_STAT_AREA] <= 12))[0] + 1
    speck_widths.extend(st[small, cv2.CC_STAT_WIDTH].tolist())
    speck_colour_share[int(np.argmin(((centres - raw_centres[k]) ** 2).sum(axis=1)))] += len(small)
speck_widths = np.array(speck_widths, np.float64)
speckle = {'per_megapixel': round(float(len(speck_widths) / MEGAPIXELS), 0), 'length': [round(float(np.exp(np.log(speck_widths).mean())), 2), round(float(np.log(speck_widths).std()), 3)],
           'aspect': [1.8], 'colour_weights': [round(float(v), 4) for v in speck_colour_share / speck_colour_share.sum()]}

model = {'classes': classes, 'class_group': GROUP_OF_CLASS, 'child_classes': [0, 1, 2, 3, 4],
         'zone': {'lab_mean': [round(float(v), 2) for v in zone_mean], 'chol': zone_chol.round(3).tolist(), 'scale': [lengths['along_the_planks'] * 2.5, lengths['across_the_planks'] * 2.5],
                  'strip_length': zone_len, 'row_height': zone_row},
         'child': {str(g): v for g, v in children.items()}, 'fields': {'scale': [lengths['along_the_planks'] * 2.5, lengths['across_the_planks'] * 2.5]},
         'target_area_share': shares, 'class_edges': CLASS_EDGES, 'speckle': speckle, 'regions_used_for_fit': REGIONS}
json.dump(model, open(os.path.join(HERE, 'paint_model.json'), 'w'), indent=1)
print('wrote paint_model.json; target area share by class', shares, 'sum', round(sum(shares), 3))
