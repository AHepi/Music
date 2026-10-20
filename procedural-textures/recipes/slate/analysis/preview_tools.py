# What this does (plain words): a QUICK preview of a slate description using plain Python (numpy + OpenCV, no Blender): it draws the flat shapes
# back to front, derives height and normal from the colour the same way the generator does, writes the three pictures into a folder and
# (optionally) runs both comparison tools. It takes seconds instead of a minute, so many settings can be tried; the real pictures always come
# from Blender (generator/slate_generator.py) and are checked against this preview. Use:
#   python3 -I preview_tools.py DESCRIPTION.json OUT_FOLDER [--score] [--size 1254]
import json
import os
import subprocess
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SLATE = os.path.abspath(os.path.join(HERE, '..'))
PROC = os.path.abspath(os.path.join(SLATE, '..', '..'))
sys.path.insert(0, os.path.join(SLATE, 'generator'))
import slate_layers as sl  # noqa: E402


def draw(description, size=1254, scale=3, shift=(0.0, 0.0)):
    shapes = sl.make_shape_list(description)
    palette = np.array(description['palette'], np.uint8)[:, ::-1]
    tile = float(description['tile'])
    factor = size * scale / tile
    canvas = np.zeros((size * scale, size * scale, 3), np.uint8)
    for points, index in shapes:
        pts = np.asarray(points, np.float64)
        pts = pts - tile * np.floor(pts.mean(axis=0) / tile)
        pts = pts + [shift[0] * tile, shift[1] * tile]
        pts = pts - tile * np.floor(pts.mean(axis=0) / tile)
        low, high = pts.min(0), pts.max(0)
        for ox in (-tile, 0, tile):
            if high[0] + ox < 0 or low[0] + ox >= tile:
                continue
            for oy in (-tile, 0, tile):
                if high[1] + oy < 0 or low[1] + oy >= tile:
                    continue
                cv2.fillPoly(canvas, [((pts + [ox, oy] + 0.5) * factor).round().astype(np.int32)], tuple(int(v) for v in palette[index]), lineType=cv2.LINE_8)
    return cv2.resize(canvas, (size, size), interpolation=cv2.INTER_AREA)


def derive_maps(bgr, description):
    h = description['maps']['height']
    grey = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY).astype(np.float64)
    height = np.clip((grey - h['grey_low']) / (h['grey_high'] - h['grey_low']), 0, 1)
    if h.get('blur', 0) > 0:
        height = cv2.GaussianBlur(np.pad(height, 12, mode='wrap'), (0, 0), h['blur'])[12:-12, 12:-12]
    h8 = np.round(height * 255)
    strength = description['maps']['normal']['strength']
    hx = (np.roll(h8, -1, 1) - np.roll(h8, 1, 1)) / 2
    hy = (np.roll(h8, -1, 0) - np.roll(h8, 1, 0)) / 2
    nx, ny, nz = -strength * hx / 255, strength * hy / 255, np.ones_like(h8)
    length = np.sqrt(nx ** 2 + ny ** 2 + nz ** 2)
    normal = np.stack([nx / length, ny / length, nz / length], -1) * 0.5 + 0.5
    return (np.clip(height, 0, 1) * 65535).astype(np.uint16), (np.clip(normal[..., ::-1], 0, 1) * 255).round().astype(np.uint8)


def write_preview(description, folder, size=1254):
    os.makedirs(folder, exist_ok=True)
    bgr = draw(description, size)
    height, normal_bgr = derive_maps(bgr, description)
    cv2.imwrite(os.path.join(folder, 'colour.png'), bgr)
    cv2.imwrite(os.path.join(folder, 'height.png'), height)
    cv2.imwrite(os.path.join(folder, 'normal.png'), normal_bgr)
    return bgr


def score(folder, name='slate'):
    out = {}
    for tool in ('pixel_compare', 'texture_compare'):
        result = subprocess.run([sys.executable, '-I', os.path.join(PROC, 'lib', tool + '.py'), name, folder, '--json', os.path.join(folder, tool + '.json')], capture_output=True, text=True)
        out[tool] = json.load(open(os.path.join(folder, tool + '.json')))
    return out


if __name__ == '__main__':
    description = json.load(open(sys.argv[1]))
    folder = sys.argv[2]
    size = int(sys.argv[sys.argv.index('--size') + 1]) if '--size' in sys.argv else 1254
    write_preview(description, folder, size)
    if '--score' in sys.argv:
        scores = score(folder)
        p, t = scores['pixel_compare'], scores['texture_compare']
        print({k: p[k] for k in ('colour_ssim', 'colour_mean_delta_e', 'edge_skill_2px', 'height_mae_best_fit_levels', 'normal_mean_angle_degrees', 'tier_reached')})
        print({k: t[k] for k in t if k in ('overall', 'colour', 'height', 'normal', 'tiling')} if isinstance(t, dict) else t)
