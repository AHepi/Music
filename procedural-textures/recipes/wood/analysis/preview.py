# What this does (plain words): a quick numpy "painter" for wood descriptions: reads a description, makes the same back-to-front list of flat shapes the Blender
# generator uses (wood_layers.make_shape_list), paints it with OpenCV (4 times sharper, then shrunk), and writes colour.png / height.png / normal.png (made
# the way the reference maps were made) into a folder, so a change to a description can be seen and scored in seconds without starting Blender.
# The Blender bake gives practically the same picture (checked: SSIM 0.7101 in Blender against 0.7140 here for the same description).
# Use:  python3 -I preview.py DESCRIPTION.json OUT_FOLDER [--scale 2] [--score]
import json
import os
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'generator'))
import score_tools as st  # noqa: E402
import wood_layers as wl  # noqa: E402


def paint(description, scale=2, shift=(0.0, 0.0)):
    tile = int(description['tile'])
    size = tile * scale
    palette = np.array(description['palette'], np.float64)
    canvas = np.zeros((size, size, 3), np.uint8)
    shapes = wl.make_shape_list(description)
    sx, sy = shift
    for polygons, index in shapes:
        colour = tuple(int(v) for v in palette[index][::-1])           # BGR
        for points in polygons:
            pts = np.asarray(points, np.float64)
            if len(pts) < 3:
                continue
            pts = pts - tile * np.floor(pts.mean(axis=0) / tile)
            pts = pts + [sx * tile, sy * tile]
            pts = pts - tile * np.floor(pts.mean(axis=0) / tile)
            for ox, oy in wl.wrap_copy_count(pts, tile):
                q = (pts + [ox * tile, oy * tile]) * scale
                cv2.fillPoly(canvas, [q.round().astype(np.int32)], colour, lineType=cv2.LINE_8)
    if scale != 1:
        canvas = cv2.resize(canvas, (tile, tile), interpolation=cv2.INTER_AREA)
    return canvas, len(shapes)


def run(description_path, out_folder, scale=2, score=False):
    description = json.load(open(description_path))
    picture, count = paint(description, scale)
    maps = description['maps']
    st.write_folder(picture, out_folder, grey_low=maps['height']['grey_low'], grey_high=maps['height']['grey_high'], blur=maps['height'].get('blur', 0.5),
                    strength=maps['normal']['strength'])
    if score:
        return st.score_folder(out_folder, texture=True)
    return None


if __name__ == '__main__':
    arguments = sys.argv[1:]
    scale = int(arguments[arguments.index('--scale') + 1]) if '--scale' in arguments else 2
    report = run(arguments[0], arguments[1], scale, '--score' in arguments)
    if report:
        keys = ['colour_ssim', 'colour_mean_delta_e', 'edge_skill_2px', 'height_mae_best_fit_levels', 'normal_mean_angle_degrees', 'tier_reached', 'texture_compare_overall']
        print(json.dumps({k: report.get(k) for k in keys}))
