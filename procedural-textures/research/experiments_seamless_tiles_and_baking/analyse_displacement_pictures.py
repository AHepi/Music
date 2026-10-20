# What this does: reads the pictures made by exp4_displacement.py and (1) measures how "stair-stepped" the displaced edge of an 8-bit height ramp is compared with the
# 16-bit ramp (root-mean-square distance of the edge from a perfectly straight line, in pixels), and (2) builds labelled comparison sheets for the guide:
# 4b = Bump / Displacement / Both, 4c = static mesh fineness and adaptive subdivision, 4d = bump normal maps from float / 16-bit / 8-bit linear / 8-bit cubic / 8-bit closest.
# Run (plain Python):  python3 -I analyse_displacement_pictures.py
import json
import os

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
folder = os.path.join(HERE, 'out', 'displacement')


def top_edge(picture):
    edge = np.full(picture.shape[1], np.nan)
    for c in range(picture.shape[1]):
        lit = np.where(picture[:, c] > 0.02)[0]
        if len(lit):
            edge[c] = lit[0] + (1.0 - min(picture[lit[0], c], 1.0))
    return edge


report = {}
for bits in (8, 16):
    image = cv2.imread(os.path.join(folder, f'4d_displaced_ramp_{bits}bit.png'))[..., 0].astype(np.float64) / 255.0
    edge = top_edge(image)[150:430]
    x = np.arange(len(edge))
    fit = np.polyval(np.polyfit(x, edge, 4), x)
    report[f'{bits}-bit ramp, true displacement: edge distance from a smooth curve (rms pixels; stair steps show as this number)'] = round(float(np.sqrt(np.mean((edge - fit) ** 2))), 3)
json.dump(report, open(os.path.join(folder, 'ramp_stairs.json'), 'w'), indent=1)
print(json.dumps(report, indent=1))


def label(image, text):
    banner = np.full((26, image.shape[1], 3), 245, np.uint8)
    cv2.putText(banner, text, (4, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (20, 20, 20), 1, cv2.LINE_AA)
    return np.vstack([banner, image])


def sheet(names, labels, out, scale=1.0, columns=None, crop=None):
    tiles = []
    for name, text in zip(names, labels):
        image = cv2.imread(os.path.join(folder, name))
        if crop:
            y0, y1, x0, x1 = crop
            image = image[y0:y1, x0:x1]
        if scale != 1.0:
            image = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        tiles.append(label(image, text))
    columns = columns or len(tiles)
    while len(tiles) % columns:
        tiles.append(np.full_like(tiles[0], 255))
    rows = [np.hstack(tiles[i:i + columns]) for i in range(0, len(tiles), columns)]
    cv2.imwrite(os.path.join(folder, out), np.vstack(rows))


sheet(['4b_method_BUMP.png', '4b_method_DISPLACEMENT.png', '4b_method_BOTH.png'], ['Bump only (silhouette stays straight)', 'Displacement only (silhouette moves)', 'Displacement and Bump'],
      '4b_methods_sheet.png', 0.8, columns=1)
sheet([f'4c_static_{n}.png' for n in (16, 64, 256, 1024)] + [f'4c_adaptive_dicing{d}.png' for d in (8.0, 2.0, 1.0, 0.5)],
      [f'static grid {n} x {n}' for n in (16, 64, 256, 1024)] + [f'adaptive, dicing rate {d}' for d in (8.0, 2.0, 1.0, 0.5)], '4c_fineness_sheet.png', 0.55, columns=2, crop=(60, 280, 100, 560))
sheet(['4d_bump_float_image_Linear.png', '4d_bump_16-bit_image_Linear.png', '4d_bump_8-bit_image_Linear.png', '4d_bump_8-bit_image_Cubic.png', '4d_bump_8-bit_image_Closest.png'],
      ['float image', '16-bit Linear', '8-bit Linear', '8-bit Cubic', '8-bit Closest'], '4d_bump_bit_depth_sheet.png', 1.0, columns=3, crop=(60, 190, 60, 190))
