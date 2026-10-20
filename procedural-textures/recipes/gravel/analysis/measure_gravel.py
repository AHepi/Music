# What this does (plain words): ANALYSIS script (reads the reference picture; the generator never does). It measures the gravel picture in the
# ways the sampler needs: (1) which dots are soil and which are stone (by colour); (2) the SIZE of the lumps: for stone dots and for soil dots,
# how much of the area sits in lumps whose widest round fit has radius 2, 3, 4, 6, 8, 12, 16, 24, 32, 48 dots ("granulometry": open the mask with
# bigger and bigger discs and see how much survives); (3) the palette of stone and of soil (k-means) and, per size class, the share of each stone colour;
# (4) the dark rim: how dark the dots are right at a stone/soil border compared with the stone's inside; (5) which way the big stones point.
# Output: ../scores/measurements.json and printed tables.
import json, os, sys
import cv2
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import trace_tools as tt

TILE = 1254
bgr = tt.load_reference_colour()
lab = cv2.cvtColor(bgr.astype(np.float32) / 255.0, cv2.COLOR_BGR2Lab)
L, a, b = lab[..., 0], lab[..., 1], lab[..., 2]
chroma = np.hypot(a, b)
soil = ((b > 5.0) & (a > 2.0) & (chroma > 6.5)).astype(np.uint8) * 255
soil = cv2.medianBlur(soil, 5) > 0
stone = ~soil
out = {'soil_share': float(soil.mean()), 'stone_share': float(stone.mean())}
radii = [1, 2, 3, 4, 6, 8, 12, 16, 24, 32, 48]
PAD = 60
def wrap_open(mask, r):
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
    m = np.pad(mask.astype(np.uint8), PAD, mode='wrap')
    o = cv2.morphologyEx(m, cv2.MORPH_OPEN, k)
    return o[PAD:-PAD, PAD:-PAD] > 0
gran = {}
for name, mask in (('stone', stone), ('soil', soil)):
    surv = [float(mask.mean())] + [float(wrap_open(mask, r).mean()) for r in radii]
    gran[name] = surv
    print(name, 'share surviving opening radius', dict(zip([0] + radii, np.round(surv, 3))))
out['granulometry_radii'] = [0] + radii
out['granulometry'] = gran
# size class of each stone dot = largest opening radius that still contains the dot
size_class = np.zeros(stone.shape, np.int8)
for i, r in enumerate(radii):
    size_class[wrap_open(stone, r)] = i + 1
# stone palette
sample_idx = np.flatnonzero(stone.ravel())
rng = np.random.default_rng(2)
pick = rng.choice(sample_idx, 200000, replace=False)
lab_flat = lab.reshape(-1, 3)
crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 60, 0.01)
_, lab_labels, stone_centres = cv2.kmeans(lab_flat[pick].astype(np.float32), 8, None, crit, 3, cv2.KMEANS_PP_CENTERS)
stone_rgb = (np.clip(cv2.cvtColor(stone_centres.reshape(1, -1, 3), cv2.COLOR_Lab2RGB)[0], 0, 1) * 255).round().astype(int)
order = np.argsort(stone_centres[:, 0])
stone_centres, stone_rgb = stone_centres[order], stone_rgb[order]
def assign(centres, idx):
    d = ((lab_flat[idx][:, None, :] - centres[None]) ** 2).sum(-1)
    return d.argmin(1)
stone_lab_idx = np.flatnonzero(stone.ravel())
stone_assign = assign(stone_centres, stone_lab_idx)
print('stone palette (dark to light):')
for k in range(8):
    print('  ', stone_rgb[k].tolist(), 'share of stone dots', round(float((stone_assign == k).mean()), 3))
out['stone_palette_rgb'] = stone_rgb.tolist()
out['stone_palette_share'] = [float((stone_assign == k).mean()) for k in range(8)]
sc_flat = size_class.ravel()[stone_lab_idx]
mix = []
for i in range(len(radii) + 1):
    sel = sc_flat == i
    if sel.sum() == 0:
        mix.append([0] * 8); continue
    mix.append([float((stone_assign[sel] == k).mean()) for k in range(8)])
    print(f'  size class {i} (opening radius {([0] + radii)[i]:>2}): {sel.mean()*100:5.1f}% of stone dots; colour mix', np.round(mix[-1], 2))
out['stone_colour_mix_by_size_class'] = mix
out['stone_area_share_by_size_class'] = [float((sc_flat == i).mean()) for i in range(len(radii) + 1)]
# soil palette
soil_idx = np.flatnonzero(soil.ravel())
pick = rng.choice(soil_idx, min(200000, len(soil_idx)), replace=False)
_, _, soil_centres = cv2.kmeans(lab_flat[pick].astype(np.float32), 8, None, crit, 3, cv2.KMEANS_PP_CENTERS)
soil_rgb = (np.clip(cv2.cvtColor(soil_centres.reshape(1, -1, 3), cv2.COLOR_Lab2RGB)[0], 0, 1) * 255).round().astype(int)
order = np.argsort(soil_centres[:, 0]); soil_centres, soil_rgb = soil_centres[order], soil_rgb[order]
soil_assign = assign(soil_centres, soil_idx)
print('soil palette (dark to light):')
for k in range(8):
    print('  ', soil_rgb[k].tolist(), 'share of soil dots', round(float((soil_assign == k).mean()), 3))
out['soil_palette_rgb'] = soil_rgb.tolist()
out['soil_palette_share'] = [float((soil_assign == k).mean()) for k in range(8)]
# stone vs soil border: darkness profile across the border (distance inside the stone / inside the soil, 1..8 dots)
d_in = cv2.distanceTransform(stone.astype(np.uint8), cv2.DIST_L2, 3)
d_out = cv2.distanceTransform((~stone).astype(np.uint8), cv2.DIST_L2, 3)
profile = {}
for name, d, m in (('inside_stone', d_in, stone), ('inside_soil', d_out, soil)):
    vals = []
    for k in range(1, 9):
        sel = m & (d > k - 0.5) & (d <= k + 0.5)
        vals.append(float(L[sel].mean()))
    profile[name] = vals
    print(name, 'mean lightness at 1..8 dots from the border:', np.round(vals, 1))
out['border_lightness_profile'] = profile
# big stones: direction. structure tensor of the big-stone mask boundaries (opening radius >= 12)
big = wrap_open(stone, 12)
gx = cv2.Sobel(big.astype(np.float32), cv2.CV_32F, 1, 0, ksize=3); gy = cv2.Sobel(big.astype(np.float32), cv2.CV_32F, 0, 1, ksize=3)
jxx, jyy, jxy = (gx * gx).sum(), (gy * gy).sum(), (gx * gy).sum()
theta = 0.5 * np.degrees(np.arctan2(2 * jxy, jxx - jyy))
coherence = float(np.hypot(jxx - jyy, 2 * jxy) / (jxx + jyy))
print('big stone edge direction (degrees from x axis, y down) and coherence:', round(theta, 1), round(coherence, 3))
out['big_edge_theta_degrees'] = float(theta); out['big_edge_coherence'] = coherence
# light direction: mean brightness gradient inside big stones
Lb = cv2.GaussianBlur(L, (0, 0), 2.0)
dLx = cv2.Sobel(Lb, cv2.CV_32F, 1, 0, ksize=3) / 8; dLy = cv2.Sobel(Lb, cv2.CV_32F, 0, 1, ksize=3) / 8
inner = wrap_open(stone, 10)
out['mean_dL_dx_in_big_stones'] = float(dLx[inner].mean()); out['mean_dL_dy_in_big_stones'] = float(dLy[inner].mean())
print('mean brightness slope inside big stones (per dot): dx', out['mean_dL_dx_in_big_stones'], 'dy', out['mean_dL_dy_in_big_stones'], '(negative = brighter to the left/top)')
json.dump(out, open(os.path.join(HERE, '..', 'scores', 'measurements.json'), 'w'), indent=1)
