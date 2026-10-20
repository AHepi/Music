# What this does (plain words): a FAST stand-in for the Blender photo-shoot, used while fitting: it paints the shape stack (see metal_shapes.py)
# with OpenCV (flat colour per shape, hard edges, no smoothing) and turns the colour picture into the height and normal pictures with the
# same rule the reference used (derive_maps.py). It also writes a folder the two comparison tools can read, and runs them.
# It is not the generator: the Blender generator makes the real pictures; this just lets the fitting scripts try thousands of ideas in seconds.
import json
import os
import subprocess
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, HERE)
import derive_maps as dm  # noqa: E402

SHIFT = 4


def paint_stack(stack, size=1254, tile=1254.0, background=(0, 0, 0)):
    """Colour picture (size x size x 3, uint8 RGB) of a stack, painted in order. Shapes are scaled from tile dots to `size` dots."""
    scale = size / tile
    canvas = np.zeros((size, size, 3), np.uint8)
    canvas[:] = background
    one = 1 << SHIFT
    for s in stack:
        raw = s['points'][1:] if s.get('fan') else s['points']
        pts = np.round((raw * scale - 0.5) * one).astype(np.int32)      # a pixel's centre is its whole number here, so the picture edge x = 0 sits half a dot to the left
        col = tuple(int(round(v)) for v in (s['colours'][1:] if s.get('fan') else s['colours']).mean(axis=0))
        cv2.fillPoly(canvas, [pts.reshape(-1, 1, 2)], col, lineType=cv2.LINE_8, shift=SHIFT)
    return canvas


def write_map_set(colour_rgb, folder, maps, name_reference=None):
    """colour_rgb uint8 -> folder/colour.png, height.png (16-bit), normal.png (OpenGL)."""
    os.makedirs(folder, exist_ok=True)
    cv2.imwrite(os.path.join(folder, 'colour.png'), colour_rgb[..., ::-1])
    height = dm.height_from_colour(colour_rgb.astype(np.float64), maps)
    cv2.imwrite(os.path.join(folder, 'height.png'), np.round(height * 65535).astype(np.uint16))
    normal = dm.normal_from_height(height, maps['normal_strength'])
    cv2.imwrite(os.path.join(folder, 'normal.png'), np.round(normal * 255).astype(np.uint8)[..., ::-1])
    return height, normal


def compare(folder, reference='metal', sheet=True, texture=True, tag=''):
    """Run pixel_compare (and texture_compare) on a map-set folder; returns the pixel dictionary (and the texture one)."""
    py = ['python3', '-I']
    pj = os.path.join(folder, f'pixel{tag}.json')
    cmd = py + [os.path.join(PROC, 'lib', 'pixel_compare.py'), reference, folder, '--json', pj]
    if sheet:
        cmd += ['--sheet', os.path.join(folder, f'diff{tag}.png')]
    subprocess.run(cmd, check=True, capture_output=True)
    pixel = json.load(open(pj))
    tex = None
    if texture:
        tj = os.path.join(folder, f'texture{tag}.json')
        subprocess.run(py + [os.path.join(PROC, 'lib', 'texture_compare.py'), reference, folder, '--json', tj], check=True, capture_output=True)
        tex = json.load(open(tj))
    return pixel, tex


def summary_line(pixel, tex=None):
    keys = ['tier_reached', 'colour_ssim', 'colour_mean_delta_e', 'edge_skill_2px', 'height_mae_best_fit_levels', 'normal_mean_angle_degrees']
    parts = []
    for k in keys:
        v = pixel.get(k)
        if v is None:
            for sub in pixel.values():
                if isinstance(sub, dict) and k in sub:
                    v = sub[k]
        parts.append(f'{k.replace("_levels", "").replace("colour_", "").replace("_degrees", "")}={v if isinstance(v, str) else round(v, 3) if v is not None else None}')
    if tex:
        parts.append('texture=' + str(round(tex.get('overall', -1), 3)))
    return ' | '.join(parts)
