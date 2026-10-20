# What this does: asks "does real geometry give the SAME kind of height map as the reference pictures?". The reference height maps were made from the colour
# picture (height follows brightness, correlation 0.94-0.99), but a photographed geometry height is the TRUE depth (mortar is LOW, so it is dark). This script
# takes a finished geometry bake (colour.png, height.png, normal_geometry.png in a folder) and builds four alternative picture sets, scores each against the reference
# with lib/texture_compare.py, and writes a table:
#   A geometry   : height = photographed depth, normal = Sobel of that height (what the bake writes)
#   B geo-normal : same height, but the normal map is the TRUE surface normal photographed from the geometry (normal_geometry.png)
#   C hybrid     : height = half photographed depth + half brightness of the colour picture; normal = Sobel of that
#   D colour     : height = brightness of the colour picture only (the references' own recipe); normal = Sobel of that
# Run (plain Python): python3 -I hybrid_height_experiment.py REFERENCE_NAME GEOMETRY_BAKE_FOLDER OUT_FOLDER
import json
import os
import subprocess
import sys

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.abspath(os.path.join(HERE, '..', '..'))
REFERENCE = os.path.join(PROC, 'reference')
LIB = os.path.join(PROC, 'lib')


def read(path, grey=False):
    image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if image.ndim == 3:
        image = image[..., :3][..., ::-1]
    image = image.astype(np.float64) / (65535.0 if image.dtype == np.uint16 else 255.0)
    if grey and image.ndim == 3:
        image = image.mean(axis=-1)
    return image


def write(path, array, sixteen=False):
    if array.ndim == 3:
        array = array[..., ::-1]
    scale = 65535.0 if sixteen else 255.0
    cv2.imwrite(path, np.clip(np.round(array * scale), 0, scale).astype(np.uint16 if sixteen else np.uint8))


def sobel_normal(height, strength):
    hx = (np.roll(height, -1, axis=1) - np.roll(height, 1, axis=1)) / 2.0
    hy = (np.roll(height, -1, axis=0) - np.roll(height, 1, axis=0)) / 2.0
    nx, ny, nz = -strength * hx, strength * hy, np.ones_like(height)
    length = np.sqrt(nx * nx + ny * ny + nz * nz)
    return np.stack([nx / length, ny / length, nz / length], axis=-1)


def fit_strength(height, target):
    low, high = 0.01, 600.0
    for _ in range(40):
        middle = np.sqrt(low * high)
        n = sobel_normal(height, middle)
        spread = (n[..., 0].std() + n[..., 1].std()) / 2
        low, high = (middle, high) if spread < target else (low, middle)
    return float(np.sqrt(low * high))


def score(reference, folder):
    out_json = os.path.join(folder, 'score.json')
    subprocess.run([sys.executable, '-I', os.path.join(LIB, 'texture_compare.py'), reference, folder, '--json', out_json], capture_output=True, check=True)
    result = json.load(open(out_json))
    return {'overall': result['overall'], **result['groups'], 'height_colour_corr': result['facts']['height_colour_corr_candidate']}


def main():
    reference, source, out_root = sys.argv[1:4]
    colour = read(os.path.join(source, 'colour.png'))
    height_geo = read(os.path.join(source, 'height.png'), grey=True)
    normal_geo = read(os.path.join(source, 'normal_geometry.png'))
    ref_normal = read(os.path.join(REFERENCE, reference, 'normal.png')) * 2 - 1
    target_spread = (ref_normal[..., 0].std() + ref_normal[..., 1].std()) / 2
    ref_height = read(os.path.join(REFERENCE, reference, 'height.png'), grey=True)
    luminance = colour @ np.array([0.2126, 0.7152, 0.0722])
    padded = np.pad(luminance, 8, mode='wrap')
    luminance = cv2.GaussianBlur(padded, (0, 0), 0.8)[8:-8, 8:-8]        # blur with wrap-around so the tile edge stays seamless
    luminance = (luminance - luminance.mean()) / (luminance.std() + 1e-9) * ref_height.std() + ref_height.mean()       # same brightness spread as the reference height maps
    geo = (height_geo - height_geo.mean()) / (height_geo.std() + 1e-9) * ref_height.std() + ref_height.mean()
    variants = {
        'A_geometry': (geo, None),
        'B_geo_normal': (geo, normal_geo),
        'C_hybrid_half_geometry_half_colour': (0.5 * geo + 0.5 * luminance, None),
        'D_colour_brightness_only': (luminance, None),
    }
    table = {}
    for name, (height, normal) in variants.items():
        folder = os.path.join(out_root, name)
        os.makedirs(folder, exist_ok=True)
        height = np.clip(height, 0, 1)
        write(os.path.join(folder, 'colour.png'), colour)
        write(os.path.join(folder, 'height.png'), height, sixteen=True)
        if normal is None:
            normal = sobel_normal(height, fit_strength(height, target_spread)) * 0.5 + 0.5
        write(os.path.join(folder, 'normal.png'), normal)
        table[name] = score(reference, folder)
        print(name, table[name])
    json.dump(table, open(os.path.join(out_root, 'hybrid_results.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
