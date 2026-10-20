# What this does: measures the uploaded wood height map and colour map once, and writes the numbers into
#   research/measurements_wood_source_map.json  (plus two small pictures in research/pictures/).
# It answers: where the 5 board rows run, how wide the dark gaps are, whether the map wraps around without a seam, where the
# knots and stains sit, and how the colour picture relates to the height picture.
# Run with:  python3 -I measure_wood_source_map.py        (needs numpy, PIL and cv2; no Blender)
# Joints and knots were first read by eye from labelled crops (the crops are in research/tests/probe_R1..R5.png) and then
# the numbers below were checked by the program (dark-line detector, black-dot detector). Stains are found by the program.
import json
import numpy as np
import cv2
from PIL import Image

BASE = 'proc-work/'
REF = BASE + 'reference/wood/'
OUT = BASE + 'recipes/wood_from_displacement/research/'

h8 = np.asarray(Image.open(REF + 'height_as_uploaded.png'))
h = h8.astype(np.float32) / 255.0
col8 = np.asarray(Image.open(REF + 'colour.png'))
col = col8.astype(np.float32) / 255.0
H, W = h.shape
result = {'what_this_is': 'Measurements of the uploaded wood height map (height_as_uploaded.png) and colour map (colour.png), 1254 x 1254. '
                          'Coordinates are in dots: x to the right (0..1253), y DOWN the picture (0 = top row of the picture).'}

# ------------------------------------------------------------------ 1. the grey levels
hist = np.bincount(h8.ravel(), minlength=256)
result['height_levels'] = {
    'min': int(h8.min()), 'max': int(h8.max()), 'mean': round(float(h8.mean()), 2),
    'percentiles_1_5_25_50_75_95_99': [float(v) for v in np.percentile(h8, [1, 5, 25, 50, 75, 95, 99])],
    'note': 'The percentiles are almost evenly spaced, so the grey levels are spread nearly evenly from 3 to 250 (the map was probably '
            'contrast-equalised). This is why blending two copies of it flattens contrast and why re-stretching the result back to an even spread helps.'}

# ------------------------------------------------------------------ 2. does it wrap (seam test)
def seam(a, axis):
    if axis == 1:
        inner = float(np.abs(a[:, 1:] - a[:, :-1]).mean()); wrap = float(np.abs(a[:, 0] - a[:, -1]).mean())
    else:
        inner = float(np.abs(a[1:] - a[:-1]).mean()); wrap = float(np.abs(a[0] - a[-1]).mean())
    return {'jump_across_the_wrap_edge': round(wrap, 4), 'normal_jump_between_neighbouring_lines': round(inner, 4), 'ratio_wrap_over_normal': round(wrap / inner, 2)}
result['wraps_seamlessly'] = {
    'left_to_right': seam(h, 1), 'top_to_bottom': seam(h, 0),
    'verdict': 'NO. A seamless picture would give a ratio near 1.0. Left-right gives about 4.0 and top-bottom about 2.8. '
               'A straight vertical seam line and a horizontal seam line are visible in a plain 2 x 2 repeat (research/pictures/source_seam_crop.jpg). '
               'So windows read from this map must not cross its edges (use only 0..1253 inside the picture), or the seam has to be hidden.'}

# ------------------------------------------------------------------ 3. rows and gaps
dark_fraction = (h8 < 51).mean(1)         # share of each line that is darker than 20 per cent grey
smooth = np.convolve(np.pad(dark_fraction, (1, 1), mode='wrap'), np.ones(3) / 3, 'valid')
gap_lines = [(183, 192), (460, 474), (700, 712), (971, 983)]
gaps = []
hb = cv2.GaussianBlur(h, (0, 0), 3)
for index, (a, b) in enumerate(gap_lines):
    centre = a + int(np.argmax(smooth[a:b + 1]))
    # rows where more than half of the line is dark = the gap proper
    core = [y for y in range(a - 6, b + 7) if smooth[y] > 0.5]
    wobble = []
    for x0 in range(0, W, 100):
        column = hb[centre - 30:centre + 31, x0:x0 + 100].mean(1)
        wobble.append(centre - 30 + int(np.argmin(column)))
    gaps.append({'between_rows': f'R{index + 1} and R{index + 2}', 'dark_lines_from_y': a, 'to_y': b, 'darkest_line_y': centre,
                 'width_where_over_half_dark': (core[-1] - core[0] + 1) if core else None,
                 'share_of_darkest_line_that_is_dark': round(float(smooth[centre]), 2),
                 'mean_grey_inside_gap_0_to_255': round(float(h8[core[0]:core[-1] + 1].mean()), 1) if core else None,
                 'centre_line_y_every_100_dots_across': wobble,
                 'how_much_the_centre_line_wanders_dots': int(max(wobble) - min(wobble))})
result['gaps_between_rows'] = {
    'list': gaps,
    'note': 'Four clear dark gaps. Each is 10 to 15 dots wide where more than 30 per cent of the line is dark, and 6 to 7 dots wide where more than half of the line is dark. Their centre lines wander by 6 to 16 dots across the picture '
            '(gap 4 dips by about 15 dots near x = 200 to 300), so they are not ruler-straight. In the picture the gap is filled with small dark pebble shapes (dirt in the gap); that was seen by eye, not measured.',
    'wrap_gap': 'The fifth gap (between the bottom row R5 and the top row R1) is not a clean straight gap: it is a ragged, partly open crack at about y = 18 to 30 '
                'across the left 400 and right 250 dots, with a thin 18-dot sliver of R5 above it at the very top of the picture. Only 8 to 14 per cent of those lines are dark.'}
bands = {'R1': (28, 182), 'R2': (193, 459), 'R3': (475, 699), 'R4': (713, 970), 'R5': (984, 1253)}
rows = []
for name, (a, b) in bands.items():
    rows.append({'row': name, 'top_y': a, 'bottom_y': b, 'height_in_dots': b - a + 1,
                 'mean_grey': round(float(h8[a:b + 1].mean()), 1), 'share_darker_than_20_percent': round(float((h8[a:b + 1] < 51).mean()), 3)})
result['rows'] = {
    'list': rows,
    'note': 'Row tops and bottoms are the first and last lines after the gap. R1 is the shortest (155 dots) because the picture ends in the middle of the wood: the top 28 dots hold '
            'the end of row R5 (a 18-dot sliver) plus the ragged crack. R5 therefore runs from y = 984 to the bottom edge. Typical row height is 226 to 270 dots (about 18 to 22 per cent of the picture).'}

# ------------------------------------------------------------------ 4. joints (read by eye from labelled crops, see probe_R*.png)
result['butt_joints'] = {
    'what_they_are': 'Places where a board ends and the next begins inside a row: a crack that runs across the row, usually only part of the row height, often stepped and with a '
                     'notch. They are NOT clean full-height lines. Each row has two of them (R1 two small ones).',
    'list_x_range_and_y_range': [
        {'row': 'R1', 'x': [690, 700], 'y': [85, 105], 'kind': 'short plank end (a loose board tip), not full height'},
        {'row': 'R1', 'x': [1185, 1200], 'y': [140, 183], 'kind': 'notched step near the row edge'},
        {'row': 'R2', 'x': [734, 750], 'y': [300, 350], 'kind': 'vertical crack in the upper half, joins a long horizontal crack'},
        {'row': 'R2', 'x': [920, 950], 'y': [360, 462], 'kind': 'full lower-half step, board end with notch (clearest joint in R2)'},
        {'row': 'R3', 'x': [508, 520], 'y': [476, 505], 'kind': 'short vertical crack at the top of the row'},
        {'row': 'R3', 'x': [1075, 1095], 'y': [545, 645], 'kind': 'stacked broken board end (clearest joint in R3)'},
        {'row': 'R4', 'x': [585, 605], 'y': [748, 840], 'kind': 'board end with raised notch (clearest joint in R4)'},
        {'row': 'R4', 'x': [818, 840], 'y': [840, 965], 'kind': 'vertical crack through the lower half, runs through the knot K4'},
        {'row': 'R5', 'x': [905, 925], 'y': [992, 1060], 'kind': 'board end with a white splinter, upper half'},
        {'row': 'R5', 'x': [585, 615], 'y': [1190, 1250], 'kind': 'stepped crack in the lower half'}],
    'how_checked': 'A program looked for dark vertical runs at least 30 dots tall inside the row interiors; every joint above had a match within about 15 dots (see the detector output in tests/measure_wood_source_map.py). '
                   'The detector also fires on knot centres, so the list was cleaned by eye. Positions are good to about plus or minus 10 dots.'}

# ------------------------------------------------------------------ 5. knots
knots = [{'name': 'K1', 'row': 'R1', 'centre_xy': [988, 104], 'ring_radius_dots_about': 42, 'note': 'full knot with growth rings and a black centre dot, near the right end of R1'},
         {'name': 'K2', 'row': 'R2', 'centre_xy': [350, 378], 'ring_radius_dots_about': 58, 'note': 'biggest knot, wavy grain flows around it, dot area about 125 dots'},
         {'name': 'K3', 'row': 'R4', 'centre_xy': [170, 806], 'ring_radius_dots_about': 50, 'note': 'full knot with rings, left end of R4'},
         {'name': 'K4', 'row': 'R4', 'centre_xy': [832, 893], 'ring_radius_dots_about': 50, 'note': 'partial knot (rings visible, split by a vertical crack, no clean black dot), sits on the R4 joint at x about 830'}]
result['knots'] = {'list': knots, 'how_checked': 'Black centre dots (grey below 14 per cent, area 125 to 240 dots) were found by a program within 6 to 22 dots of the centres read by eye (K1, K2, K3). K4 has no clean dot.',
                   'note': 'Four knots in the whole map. Windows that contain a knot will show the same knot every time; windows that avoid all four knots are the "plain wood" windows. '
                           'Knots are about 100 dots wide and sit between 8 and 14 per cent of the picture from the left or right edge, which is why a texture that repeats them is easy to spot.'}

# ------------------------------------------------------------------ 6. stains (found by program)
body = h8.copy()
mask_stain = ((body >= 30) & (body <= 110)).astype(np.uint8)
opened = cv2.morphologyEx(mask_stain, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))   # drops thin grain lines
for a_, b_ in gap_lines:
    opened[max(a_ - 4, 0):b_ + 5] = 0                                                                              # the dark gaps are not stains
closed = cv2.dilate(opened, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))                               # joins neighbouring dots (closer than about 15 dots) into clusters
n, lab, st, cen = cv2.connectedComponentsWithStats(closed)
clusters = []
for i in range(1, n):
    x, y, w, hh, a = st[i]
    if a >= 1500:
        clusters.append({'centre_xy': [int(cen[i][0]), int(cen[i][1])], 'box_x_y_w_h': [int(x), int(y), int(w), int(hh)], 'area_dots': int(a)})
clusters.sort(key=lambda c: -c['area_dots'])
n2, lab2, st2, cen2 = cv2.connectedComponentsWithStats(opened)
blob_sizes = sorted([int(st2[i, 4]) for i in range(1, n2) if st2[i, 4] >= 30], reverse=True)
result['stains'] = {
    'what_they_are': 'dark round splotches, flat grey 30 to 110 (wood is 120 to 250), built from many small round dots 4 to 20 dots across, grouped in clusters 80 to 250 dots wide',
    'share_of_picture_covered_by_stain_dots': round(float(opened.mean()), 3),
    'number_of_stain_clusters_over_1500_dots_after_joining_dots_closer_than_15': len(clusters), 'clusters_largest_first': clusters[:14],
    'number_of_separate_round_dots_over_30_dots_area': len(blob_sizes), 'biggest_single_dot_areas': blob_sizes[:8],
    'note': 'The program is rough: it also catches some dark grain and crack shade, so read the numbers as an upper limit and the overlay picture as the check. The clusters are spread over all five rows. They are the second thing (after the knots) that a viewer remembers, so a texture that repeats whole windows repeats them visibly. '
            'Stains are separate from the grain: they are a flat dark cut-out on top of it.'}
vis = cv2.cvtColor(h8, cv2.COLOR_GRAY2BGR)
for a_, b_ in gap_lines:
    cv2.line(vis, (0, (a_ + b_) // 2), (W - 1, (a_ + b_) // 2), (0, 255, 255), 1)
for name_, (a_, b_) in bands.items():
    cv2.putText(vis, name_, (6, (a_ + b_) // 2), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
for k in knots:
    cv2.circle(vis, tuple(k['centre_xy']), k['ring_radius_dots_about'], (0, 0, 255), 2)
for jt in result['butt_joints']['list_x_range_and_y_range']:
    cv2.rectangle(vis, (jt['x'][0], jt['y'][0]), (jt['x'][1], jt['y'][1]), (255, 128, 0), 2)
for c in clusters:
    x, y, w, hh = c['box_x_y_w_h']
    cv2.rectangle(vis, (x, y), (x + w, y + hh), (0, 200, 0), 1)
cv2.imwrite(OUT + 'pictures/source_map_measured_overlay.jpg', vis, [cv2.IMWRITE_JPEG_QUALITY, 88])

# ------------------------------------------------------------------ 7. colour against height
rgb = col
luma_srgb = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]      # brightness of the sRGB numbers
def lin(c): return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
luma_lin = 0.2126 * lin(rgb[..., 0]) + 0.7152 * lin(rgb[..., 1]) + 0.0722 * lin(rgb[..., 2])
def corr(a, b): return float(np.corrcoef(a.ravel(), b.ravel())[0, 1])
corrs = {'sRGB_luma': corr(luma_srgb, h), 'linear_luma': corr(luma_lin, h), 'red': corr(rgb[..., 0], h), 'green': corr(rgb[..., 1], h), 'blue': corr(rgb[..., 2], h),
         'mean_of_rgb': corr(rgb.mean(-1), h), 'maximum_of_rgb': corr(rgb.max(-1), h)}
blur_scan = {}
for sigma in (0.0, 0.5, 0.8, 1.0, 1.5):
    lb = luma_srgb if sigma == 0 else cv2.GaussianBlur(luma_srgb, (0, 0), sigma)
    blur_scan[str(sigma)] = round(corr(lb, h), 4)
# fitted tone curve: bin colour luma into 64 equal-count bins and see the mean height
bins = np.quantile(luma_srgb, np.linspace(0, 1, 65))
idx = np.clip(np.searchsorted(bins, luma_srgb, side='right') - 1, 0, 63)
curve = np.array([h[idx == i].mean() for i in range(64)])
fitted = curve[idx]
r2_curve = 1 - float(((h - fitted) ** 2).sum() / ((h - h.mean()) ** 2).sum())
# per row correlation
per_row = {}
for name_, (a_, b_) in bands.items():
    per_row[name_] = round(corr(luma_srgb[a_:b_ + 1], h[a_:b_ + 1]), 4)
# the other way round: colour predicted from height. 32 equal-count height bins, mean colour per bin, error in Lab
hb_edges = np.quantile(h8, np.linspace(0, 1, 33))
hi = np.clip(np.searchsorted(hb_edges, h8, side='right') - 1, 0, 31)
palette = np.array([col[hi == i].mean(0) for i in range(32)])
pred = palette[hi]
def to_lab(img): return cv2.cvtColor((np.clip(img, 0, 1) * 255).astype(np.uint8)[..., ::-1], cv2.COLOR_BGR2LAB).astype(np.float32) * np.array([100 / 255, 1, 1], np.float32) - np.array([0, 128, 128], np.float32)
lab_true, lab_pred = to_lab(col), to_lab(pred)
de = np.sqrt(((lab_true - lab_pred) ** 2).sum(-1))
# the same with one palette per row band (so the row tone is allowed to differ)
pred_row = np.zeros_like(col)
for name_, (a_, b_) in bands.items():
    sub = hi[a_:b_ + 1]; pal = np.array([col[a_:b_ + 1][sub == i].mean(0) if (sub == i).any() else palette[i] for i in range(32)]); pred_row[a_:b_ + 1] = pal[sub]
pred_row[:bands['R1'][0]] = pred[:bands['R1'][0]]
for a_, b_ in gap_lines:
    pred_row[a_ - 0:b_ + 1] = pred[a_:b_ + 1]
de_row = np.sqrt(((lab_true - to_lab(pred_row)) ** 2).sum(-1))
result['colour_versus_height'] = {
    'correlation_with_height': {k: round(v, 4) for k, v in corrs.items()},
    'correlation_of_srgb_luma_after_blur_sigma_dots': blur_scan,
    'correlation_of_srgb_luma_with_height_per_row': per_row,
    'share_of_height_explained_by_a_fitted_tone_curve_of_colour_brightness_R2': round(r2_curve, 4),
    'palette_from_height_32_bins_srgb_0_to_255': [[int(round(v * 255)) for v in p] for p in palette],
    'palette_bin_height_edges_0_to_255': [round(float(v), 1) for v in hb_edges],
    'colour_error_if_colour_is_made_from_height_by_one_palette_DeltaE_mean_and_95th_percent': [round(float(de.mean()), 2), round(float(np.percentile(de, 95)), 2)],
    'colour_error_if_each_row_gets_its_own_palette_DeltaE_mean_and_95th_percent': [round(float(de_row.mean()), 2), round(float(np.percentile(de_row, 95)), 2)],
    'note': 'Correlation (Pearson) of the colour picture brightness with the height map. A value of 1.0 would mean the height is nothing but the colour brightness. '
            'DeltaE is a standard colour-difference number: about 1 is just noticeable, 2 to 5 is a small difference to the eye, over 10 is clearly another colour. '
            'The palette error says how wrong the "colour from height" comparison version will be, on average, if it uses the best possible single palette for the whole map.'}
for ch in ('R', 'G', 'B'):
    pass
result['colour_map_facts'] = {'mean_srgb_0_to_255': [round(float(v) * 255, 1) for v in col.reshape(-1, 3).mean(0)],
                              'darkest_gap_colour_0_to_255': [round(float(v) * 255, 1) for v in col[183:192].reshape(-1, 3).mean(0)],
                              'note': 'Colour hues are brown/orange in bright (weathered bare wood) areas and blue-grey in dull areas and stains; a palette from height alone cannot reproduce the orange-versus-blue-grey split where brightness is the same.'}

# ------------------------------------------------------------------ 8. normal check: is the uploaded normal map the slope of the height at strength 8?
def sobel_normal(height, strength):
    hx = (np.roll(height, -1, axis=1) - np.roll(height, 1, axis=1)) / 2.0
    hy_down = (np.roll(height, -1, axis=0) - np.roll(height, 1, axis=0)) / 2.0
    nx, ny, nz = -strength * hx, strength * hy_down, np.ones_like(height)
    length = np.sqrt(nx * nx + ny * ny + nz * nz)
    return np.stack([nx / length, ny / length, nz / length], -1)
nref = np.asarray(Image.open(REF + 'normal.png')).astype(np.float32) / 255 * 2 - 1
results_normal = {}
for s in (6, 8, 10):
    mine = sobel_normal(h, s)
    results_normal[str(s)] = {'mean_abs_difference_in_x_y_z': [round(float(np.abs(mine[..., i] - nref[..., i]).mean()), 4) for i in range(3)]}
result['normal_check'] = {'sobel_strength_scan_against_reference_normal_png': results_normal,
                          'note': 'Strength 8 gives the smallest difference if the first number of its pair is lowest here; the notes say wood uses strength 8. The reference normal.png here is the OpenGL one (green up).'}

# ------------------------------------------------------------------ 9. ready-made numbers for the builder
slices = [('R2', 180, 277), ('R3', 457, 240), ('R4', 697, 270), ('R5', 967, 287)]
result['numbers_for_the_builder'] = {
    'what_this_is': 'Source slices that each start 3 dots above a dark gap and run to just above the next gap (so every slice is one gap on top plus one board row). '
                    'They follow each other without overlap from y = 180 to the bottom of the map, so they can be laid one after another or in any order.',
    'slices_y_start_and_length_in_dots': [{'row': n, 'start_y': a, 'length': b, 'scale_to_fit_a_row_of_250.8_dots': round(b / 250.8, 3)} for n, a, b in slices],
    'row_R1_not_used_because': 'it is only 155 dots tall (165 with its lower gap) and would need a 1.5 times zoom to fill a row of 250.8 dots',
    'knot_free_stretches_in_x_for_each_slice': {'R2': [470, 1253], 'R3': [0, 1253], 'R4': [290, 710], 'R5': [0, 1253]},
    'knots_x_in_each_slice': {'R2': [350], 'R4': [170, 832]},
    'note': 'Knot-free stretch = x range where a window does not touch a knot disc (radius about 58 plus 60 dots of margin). Row R4 has two knots, so only 420 dots of it are knot-free; '
            'R2 has 784. R3 and R5 have none.'}
with open(OUT + 'measurements_wood_source_map.json', 'w') as handle:
    json.dump(result, handle, indent=1)
print('written', OUT + 'measurements_wood_source_map.json')
print(json.dumps({k: result[k] for k in ('colour_versus_height', 'normal_check')}, indent=1)[:5000])
