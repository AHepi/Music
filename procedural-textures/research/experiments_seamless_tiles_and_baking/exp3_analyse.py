# What this does: measures the pictures made by exp3_height_to_normal.py and the project's reference maps.
#   Part A  Bump node: Distance versus the Sobel strength that reproduces it, at three picture sizes (is it resolution independent?)
#   Part B  Bump node Filter Width on a hard-edged height (how soft do the edges get?)
#   Part C  Strength versus Distance, Invert
#   Part D  the compositor normal map versus numpy
#   Part R  the six reference surfaces: which convention each normal map has, and which Sobel strength reproduces it from its height
#   Part Q  8-bit versus 16-bit height: how much worse is a normal map made from 8-bit height?
# Run (plain Python):  python3 -I exp3_analyse.py
import json
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import normal_map_tools as nm  # noqa: E402

REFERENCE = os.path.join(HERE, '..', '..', 'reference')
folder = os.path.join(HERE, 'out', 'normal')
report = {}


def grey(path):
    picture, bits = nm.load_unit_picture(path)
    return picture if picture.ndim == 2 else picture[..., 0]


# ---------------------------------------------------------------------------------- A
a = {}
for size in (128, 256, 512):
    height = grey(os.path.join(folder, f'A_height_{size}.png'))
    for d in (0.01, 0.02, 0.04):
        picture, _ = nm.load_unit_picture(os.path.join(folder, f'A_bump_d{d}_{size}.png'))
        s_red, s_green, c_red, c_green = nm.sobel_strength_that_matches(picture, height)
        a[f'size {size}, Distance {d}'] = {'sobel_strength_fit': round((s_red + s_green) / 2, 3), 'distance_times_size': round(d * size, 3),
                                           'ratio_fit_to_distance_times_size': round((s_red + s_green) / 2 / (d * size), 3),
                                           'agreement_with_height_slope_(1=perfect)': round((-c_red + c_green) / 2, 3),
                                           'convention_from_map_alone': nm.convention_from_the_map_alone(picture)[0], 'score': round(nm.convention_from_the_map_alone(picture)[1], 2)}
report['A_bump_distance_vs_sobel_strength'] = a
# resolution dependence: shrink the 512 normal map to 128 and compare with the 128 render
big, _ = nm.load_unit_picture(os.path.join(folder, 'A_bump_d0.02_512.png'))
small, _ = nm.load_unit_picture(os.path.join(folder, 'A_bump_d0.02_128.png'))
shrunk = cv2.resize(big, (128, 128), interpolation=cv2.INTER_AREA)
report['A_normal_map_made_at_512_then_shrunk_vs_made_at_128'] = {'mean_abs_difference': round(float(np.abs(shrunk - small).mean()), 4),
                                                                'tilt_spread_512': round(float(big[..., :2].std()), 4), 'tilt_spread_128': round(float(small[..., :2].std()), 4)}

# ---------------------------------------------------------------------------------- B
b = {}
height = grey(os.path.join(folder, 'B_height_bricks.png'))
for width in (0.1, 1.0, 2.0):
    picture, _ = nm.load_unit_picture(os.path.join(folder, f'B_bump_filter{width}.png'))
    n = nm.decode_normal(picture)
    tilt = np.degrees(np.arccos(np.clip(n[..., 2], -1, 1)))
    row = tilt[40, :]                          # one row through the bricks
    edge_width = int((row > 1.0).sum())
    b[f'filter width {width}'] = {'steepest_tilt_degrees': round(float(tilt.max()), 1), 'pixels_per_row_with_tilt_above_1_degree': edge_width,
                                  'mean_tilt_degrees': round(float(tilt.mean()), 2)}
report['B_filter_width_on_hard_edges'] = b

# ---------------------------------------------------------------------------------- C
def get(name):
    return nm.load_unit_picture(os.path.join(folder, f'C_{name}.png'))[0]


c = {}
base = get('d0.02_s1')
c['Distance 0.04 Strength 1 versus Distance 0.02 Strength 2: mean abs difference'] = round(float(np.abs(get('d0.04_s1') - get('d0.02_s2')).mean()), 4)
c['Distance 0.04 Strength 0.5 versus Distance 0.02 Strength 1: mean abs difference'] = round(float(np.abs(get('d0.04_s0.5') - base).mean()), 4)
c['Distance 0.1 Strength 1 versus Distance 0.02 Strength 5: mean abs difference'] = round(float(np.abs(get('d0.1_s1') - get('d0.02_s5')).mean()), 4)
c['Invert on: mean of (picture + inverted picture) in red and green (1.0 = exact mirror about 0.5)'] = [round(float((base + get('d0.02_s1_invert'))[..., k].mean()), 4) for k in (0, 1)]
height = grey(os.path.join(folder, 'A_height_256.png'))
tilt_spread = {}
for name in ('d0.02_s1', 'd0.02_s2', 'd0.02_s5', 'd0.04_s1', 'd0.1_s1', 'd0.04_s0.5'):
    picture = get(name)
    s_red, s_green, _, _ = nm.sobel_strength_that_matches(picture, height)
    tilt_spread[name] = round((s_red + s_green) / 2, 2)
c['fitted_sobel_strength_for_each_setting (size 256)'] = tilt_spread
report['C_strength_distance_invert'] = c

# ---------------------------------------------------------------------------------- D
d = {}
height = grey(os.path.join(folder, 'D_height.png'))
compositor, _ = nm.load_unit_picture(os.path.join(folder, 'D_normal_compositor.png'))
reference_numpy = nm.sobel_normal(height, 5.33)
for sign_x in (1, -1):
    for sign_y in (1, -1):
        variant = reference_numpy.copy()
        if sign_x < 0:
            variant[..., 0] = 1.0 - variant[..., 0]
        if sign_y < 0:
            variant[..., 1] = 1.0 - variant[..., 1]
        d[f'compositor_vs_numpy_sobel_5.33 with red {"kept" if sign_x > 0 else "flipped"} and green {"kept" if sign_y > 0 else "flipped"}: mean abs error'] = round(float(np.abs(compositor - variant).mean()), 5)
d['convention_of_the_compositor_map'] = nm.convention_from_the_map_alone(compositor)
report['D_compositor_normal'] = d

# ---------------------------------------------------------------------------------- R
r = {}
for name in ('brick', 'slate', 'wood', 'metal', 'mud', 'gravel'):
    entry = {}
    gl, _ = nm.load_unit_picture(os.path.join(REFERENCE, name, 'normal.png'))
    dx_, _ = nm.load_unit_picture(os.path.join(REFERENCE, name, 'normal_as_uploaded_directx.png'))
    h16, bits16 = nm.load_unit_picture(os.path.join(REFERENCE, name, 'height.png'))
    h8, bits8 = nm.load_unit_picture(os.path.join(REFERENCE, name, 'height_as_uploaded.png'))
    h16 = h16 if h16.ndim == 2 else h16[..., 0]
    h8 = h8 if h8.ndim == 2 else h8[..., 0]
    entry['normal.png verdict from the map alone'] = [nm.convention_from_the_map_alone(gl)[0], round(nm.convention_from_the_map_alone(gl)[1], 2)]
    entry['normal_as_uploaded_directx.png verdict from the map alone'] = [nm.convention_from_the_map_alone(dx_)[0], round(nm.convention_from_the_map_alone(dx_)[1], 2)]
    entry['normal.png verdict from the height'] = [nm.convention_from_height(gl, h16)[0], round(nm.convention_from_height(gl, h16)[1], 2)]
    entry['normal_as_uploaded_directx.png verdict from the height'] = [nm.convention_from_height(dx_, h16)[0], round(nm.convention_from_height(dx_, h16)[1], 2)]
    s_red, s_green, c_red, c_green = nm.sobel_strength_that_matches(gl, h16)
    entry['sobel_strength_that_reproduces_normal_png_from_height_png (16-bit smoothed)'] = [round(s_red, 2), round(s_green, 2), round((-c_red + c_green) / 2, 3)]
    s_red8, s_green8, c_red8, c_green8 = nm.sobel_strength_that_matches(gl, h8)
    entry['same_from_the_8-bit_uploaded_height'] = [round(s_red8, 2), round(s_green8, 2), round((-c_red8 + c_green8) / 2, 3)]
    entry['file_bit_depths (height.png, height_as_uploaded.png)'] = [bits16, bits8]
    entry['different_grey_levels (height.png, height_as_uploaded.png)'] = [int(len(np.unique(np.round(h16 * 65535)))), int(len(np.unique(np.round(h8 * 255))))]
    r[name] = entry
report['R_reference_maps'] = r

# ---------------------------------------------------------------------------------- Q  8-bit versus 16-bit heights
q = {}
size = 512
float_height = grey(os.path.join(folder, 'A_height_512.png'))                  # 16-bit render of a smooth noise
for bits in (8, 16, 'float'):
    if bits == 8:
        quantised = np.round(float_height * 255) / 255.0
    elif bits == 16:
        quantised = np.round(float_height * 65535) / 65535.0
    else:
        quantised = float_height
    for label, strength in (('strength 5', 5.0), ('strength 30', 30.0)):
        exact = nm.sobel_normal(float_height, strength)
        made = nm.sobel_normal(quantised, strength)
        flat_fraction = float(((np.roll(quantised, -1, 1) == np.roll(quantised, 1, 1))).mean())
        q[f'{bits}-bit height, {label}'] = {'normal_mean_abs_error_vs_float_height': round(float(np.abs(made - exact).mean()), 5),
                                           'pixels_with_zero_horizontal_slope_percent': round(flat_fraction * 100, 1)}
report['Q_height_bit_depth_and_the_normal_map'] = q
cv2.imwrite(os.path.join(folder, 'Q_normal_from_8bit_height.png'), (nm.sobel_normal(np.round(float_height * 255) / 255.0, 30.0)[..., ::-1] * 255).astype(np.uint8))
cv2.imwrite(os.path.join(folder, 'Q_normal_from_16bit_height.png'), (nm.sobel_normal(np.round(float_height * 65535) / 65535.0, 30.0)[..., ::-1] * 255).astype(np.uint8))

json.dump(report, open(os.path.join(folder, 'analysis.json'), 'w'), indent=1)
print(json.dumps(report, indent=1))
